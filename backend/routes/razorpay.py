"""
Razorpay Payment Routes
Handles payment orders, payment links, and webhooks for invoice payments.
Enhanced with:
- Multi-tenant organization-specific credentials
- Journal entry posting on payment capture
- Better error handling
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
import uuid
import os
import json
import logging
import razorpay

logger = logging.getLogger(__name__)

def get_db():
    from server import db
    return db

# Import double-entry posting hooks
from services.posting_hooks import post_payment_received_journal_entry

router = APIRouter(prefix="/payments", tags=["Payments"])

# Global fallback Razorpay keys
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')


# ==================== MULTI-TENANT HELPERS ====================

async def get_org_razorpay_config(org_id: str) -> Dict:
    """Get Razorpay configuration for an organization"""
    db = get_db()
    org = await db.organizations.find_one(
        {"organization_id": org_id},
        {"razorpay_config": 1, "_id": 0}
    )
    
    if org and org.get("razorpay_config"):
        return org["razorpay_config"]
    
    # Return global fallback
    return {
        "key_id": RAZORPAY_KEY_ID,
        "key_secret": RAZORPAY_KEY_SECRET,
        "webhook_secret": RAZORPAY_WEBHOOK_SECRET,
        "test_mode": True
    }


def get_razorpay_client(config: Dict = None):
    """Create Razorpay client from config or global keys"""
    if config:
        key_id = config.get("key_id", "")
        key_secret = config.get("key_secret", "")
    else:
        key_id = RAZORPAY_KEY_ID
        key_secret = RAZORPAY_KEY_SECRET
    
    if not key_id or not key_secret:
        return None
    
    return razorpay.Client(auth=(key_id, key_secret))


def is_razorpay_configured(config: Dict = None) -> bool:
    """Check if Razorpay is configured"""
    if config:
        return bool(config.get("key_id") and config.get("key_secret"))
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


async def get_org_id_from_request(request: Request) -> str:
    """Extract organization ID from request"""
    org_id = request.headers.get("X-Organization-ID")
    if not org_id:
        db = get_db()
        session_token = request.cookies.get("session_token")
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                membership = await db.organization_users.find_one(
                    {"user_id": session["user_id"], "status": "active"},
                    {"organization_id": 1}
                )
                if membership:
                    org_id = membership["organization_id"]
    return org_id or ""


# ==================== REQUEST/RESPONSE MODELS ====================

class RazorpayConfigUpdate(BaseModel):
    """Razorpay configuration for an organization"""
    key_id: str = Field(..., min_length=10, description="Razorpay Key ID")
    key_secret: str = Field(..., min_length=10, description="Razorpay Key Secret")
    webhook_secret: str = Field(default="", description="Webhook secret")
    test_mode: bool = Field(default=True, description="Test mode flag")


class CreateOrderRequest(BaseModel):
    invoice_id: str
    amount: Optional[float] = None  # If not provided, uses invoice balance


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    invoice_id: str


class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = None  # None for full refund
    reason: Optional[str] = ""


# ==================== CONFIGURATION ENDPOINTS ====================

@router.get("/config")
async def get_payment_config(request: Request):
    """Get Razorpay configuration status"""
    org_id = await get_org_id_from_request(request)
    
    if org_id:
        config = await get_org_razorpay_config(org_id)
        key_id = config.get("key_id", "")
        configured = is_razorpay_configured(config)
    else:
        key_id = RAZORPAY_KEY_ID
        configured = is_razorpay_configured()
    
    return {
        "code": 0,
        "configured": configured,
        "key_id_masked": f"{key_id[:8]}...{key_id[-4:]}" if len(key_id) > 12 else key_id[:4] + "***" if key_id else None,
        "has_webhook_secret": bool(config.get("webhook_secret") if org_id else RAZORPAY_WEBHOOK_SECRET),
        "test_mode": config.get("test_mode", True) if org_id else True,
        "message": "Razorpay is configured" if configured else "Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to backend/.env or configure in settings"
    }


@router.post("/config")
async def save_payment_config(config: RazorpayConfigUpdate, request: Request):
    """Save organization-specific Razorpay configuration"""
    org_id = await get_org_id_from_request(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    # Validate credentials
    try:
        test_client = razorpay.Client(auth=(config.key_id, config.key_secret))
        test_client.order.all({"count": 1})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Razorpay credentials: {str(e)}")
    
    db = get_db()
    config_data = {
        "key_id": config.key_id,
        "key_secret": config.key_secret,
        "webhook_secret": config.webhook_secret,
        "test_mode": config.test_mode,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.organizations.update_one(
        {"organization_id": org_id},
        {"$set": {"razorpay_config": config_data}}
    )
    
    return {"code": 0, "message": "Razorpay configuration saved", "test_mode": config.test_mode}


@router.post("/create-order")
async def create_payment_order(req: CreateOrderRequest, request: Request):
    """Create a Razorpay order for an invoice"""
    db = get_db()
    org_id = await get_org_id_from_request(request)
    
    # Get org-specific config
    config = await get_org_razorpay_config(org_id) if org_id else None
    rp_client = get_razorpay_client(config)
    
    if not rp_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured. Please add credentials in settings.")
    
    # Try enhanced invoices first, then regular invoices
    invoice = await db.invoices_enhanced.find_one({"invoice_id": req.invoice_id}, {"_id": 0})
    if not invoice:
        invoice = await db.invoices.find_one({"invoice_id": req.invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") in ["void", "paid"]:
        raise HTTPException(status_code=400, detail=f"Cannot create payment for {invoice['status']} invoice")
    
    # Calculate amount due
    total = float(invoice.get("grand_total", invoice.get("total", invoice.get("balance", 0))))
    paid = float(invoice.get("amount_paid", 0))
    balance = total - paid
    
    amount = req.amount or balance
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    if amount > balance:
        raise HTTPException(status_code=400, detail="Amount exceeds invoice balance")
    
    # Create Razorpay order
    try:
        order = rp_client.order.create({
            "amount": int(amount * 100),  # Convert to paise
            "currency": "INR",
            "receipt": invoice.get("invoice_number", req.invoice_id),
            "payment_capture": 1,
            "notes": {
                "invoice_id": req.invoice_id,
                "invoice_number": invoice.get("invoice_number"),
                "customer_id": invoice.get("customer_id"),
                "customer_name": invoice.get("customer_name"),
                "organization_id": org_id
            }
        })
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create order: {str(e)}")
    
    # Store order in database
    order_record = {
        "order_id": order["id"],
        "invoice_id": req.invoice_id,
        "organization_id": org_id,
        "customer_id": invoice.get("customer_id"),
        "amount": amount,
        "amount_paise": int(amount * 100),
        "currency": "INR",
        "status": "created",
        "razorpay_order": order,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payment_orders.insert_one(order_record)
    
    # Update invoice with order reference
    collection = db.invoices_enhanced if await db.invoices_enhanced.find_one({"invoice_id": req.invoice_id}) else db.invoices
    await collection.update_one(
        {"invoice_id": req.invoice_id},
        {"$set": {"razorpay_order_id": order["id"]}}
    )
    
    return {
        "code": 0,
        "order": {
            "id": order["id"],
            "amount": order["amount"],
            "currency": order.get("currency", "INR"),
            "receipt": order.get("receipt"),
            "status": order.get("status")
        },
        "invoice": {
            "invoice_id": req.invoice_id,
            "invoice_number": invoice.get("invoice_number"),
            "balance": balance
        },
        "key_id": config.get("key_id", RAZORPAY_KEY_ID) if config else RAZORPAY_KEY_ID,
        "customer_name": invoice.get("customer_name"),
        "customer_email": invoice.get("customer_email"),
        "customer_phone": invoice.get("customer_phone", "")
    }


@router.post("/create-payment-link/{invoice_id}")
async def create_invoice_payment_link(invoice_id: str, request: Request, expire_days: int = 30):
    """Create a shareable payment link for an invoice"""
    db = get_db()
    org_id = await get_org_id_from_request(request)
    
    # Get org-specific config
    config = await get_org_razorpay_config(org_id) if org_id else None
    rp_client = get_razorpay_client(config)
    
    if not rp_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    # Try enhanced invoices first
    invoice = await db.invoices_enhanced.find_one({"invoice_id": invoice_id}, {"_id": 0})
    collection = db.invoices_enhanced
    if not invoice:
        invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
        collection = db.invoices
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Calculate balance
    total = float(invoice.get("grand_total", invoice.get("total", invoice.get("balance", 0))))
    paid = float(invoice.get("amount_paid", 0))
    balance = total - paid
    
    if balance <= 0:
        raise HTTPException(status_code=400, detail="Invoice has no balance due")
    
    # Get customer details
    customer = await db.contacts.find_one({"contact_id": invoice.get("customer_id")}, {"_id": 0})
    
    expire_timestamp = int((datetime.now(timezone.utc) + timedelta(days=expire_days)).timestamp())
    
    try:
        payment_link = rp_client.payment_link.create({
            "amount": int(balance * 100),
            "currency": "INR",
            "accept_partial": False,
            "description": f"Payment for Invoice {invoice.get('invoice_number')}",
            "customer": {
                "name": invoice.get("customer_name", "Customer"),
                "email": customer.get("email", "") if customer else invoice.get("customer_email", ""),
                "contact": customer.get("phone", "") if customer else invoice.get("customer_phone", "")
            },
            "notify": {
                "sms": bool(customer.get("phone") if customer else invoice.get("customer_phone")),
                "email": bool(customer.get("email") if customer else invoice.get("customer_email"))
            },
            "reference_id": invoice_id,
            "expire_by": expire_timestamp,
            "notes": {
                "invoice_id": invoice_id,
                "invoice_number": invoice.get("invoice_number", ""),
                "organization_id": org_id
            }
        })
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Payment link creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create payment link: {str(e)}")
    
    # Store payment link in database
    link_record = {
        "payment_link_id": payment_link["id"],
        "invoice_id": invoice_id,
        "organization_id": org_id,
        "invoice_number": invoice.get("invoice_number"),
        "customer_id": invoice.get("customer_id"),
        "amount": balance,
        "short_url": payment_link.get("short_url"),
        "status": "active",
        "expire_by": expire_timestamp,
        "razorpay_link": payment_link,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.razorpay_payment_links.insert_one(link_record)
    
    # Update invoice with payment link
    await collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "payment_link_id": payment_link["id"],
            "payment_link_url": payment_link.get("short_url"),
            "payment_link_expires_at": datetime.fromtimestamp(expire_timestamp, timezone.utc).isoformat(),
            "has_payment_link": True
        }}
    )
    
    return {
        "code": 0,
        "message": "Payment link created",
        "payment_link": {
            "id": payment_link["id"],
            "short_url": payment_link.get("short_url"),
            "amount": balance,
            "expire_by": expire_timestamp
        }
    }


@router.post("/verify")
async def verify_payment(request: PaymentVerifyRequest):
    """Verify payment and update invoice"""
    db = get_db()
    
    # Verify signature
    is_valid = await verify_payment_signature(
        request.razorpay_order_id,
        request.razorpay_payment_id,
        request.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    # Fetch payment details
    payment = await fetch_payment(request.razorpay_payment_id)
    
    # Get invoice
    invoice = await db.invoices.find_one({"invoice_id": request.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    amount_paid = payment.get("amount", 0) / 100  # Convert paise to rupees
    
    # Create payment record
    payment_id = f"RPAY-{uuid.uuid4().hex[:12].upper()}"
    payment_record = {
        "payment_id": payment_id,
        "razorpay_payment_id": request.razorpay_payment_id,
        "razorpay_order_id": request.razorpay_order_id,
        "invoice_id": request.invoice_id,
        "customer_id": invoice.get("customer_id"),
        "customer_name": invoice.get("customer_name"),
        "amount": amount_paid,
        "payment_mode": "razorpay",
        "method": payment.get("method"),
        "status": payment.get("status"),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.customerpayments.insert_one(payment_record)
    
    # Update invoice
    new_balance = invoice.get("balance", 0) - amount_paid
    new_status = "paid" if new_balance <= 0 else "partial"
    
    await db.invoices.update_one(
        {"invoice_id": request.invoice_id},
        {
            "$set": {
                "balance": max(0, new_balance),
                "status": new_status,
                "last_modified_time": datetime.now(timezone.utc).isoformat()
            },
            "$push": {
                "payments": {
                    "payment_id": payment_id,
                    "razorpay_payment_id": request.razorpay_payment_id,
                    "amount": amount_paid,
                    "date": payment_record["date"]
                }
            }
        }
    )
    
    # Update customer outstanding
    await db.contacts.update_one(
        {"contact_id": invoice.get("customer_id")},
        {"$inc": {"outstanding_receivable_amount": -amount_paid}}
    )
    
    # Update order status
    await db.payment_orders.update_one(
        {"order_id": request.razorpay_order_id},
        {"$set": {"status": "paid", "payment_id": request.razorpay_payment_id}}
    )
    
    return {
        "code": 0,
        "message": "Payment verified and recorded",
        "payment": {
            "payment_id": payment_id,
            "amount": amount_paid,
            "invoice_id": request.invoice_id
        },
        "invoice": {
            "new_balance": max(0, new_balance),
            "status": new_status
        }
    }


@router.post("/webhook")
async def handle_razorpay_webhook(request: Request):
    """
    Handle Razorpay webhooks for payment events.
    Verifies signature and posts journal entries on payment capture.
    """
    body = await request.body()
    signature = request.headers.get('X-Razorpay-Signature', '')
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event = payload.get("event")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    
    # Get org_id from payment notes
    notes = payment_entity.get("notes", {})
    org_id = notes.get("organization_id", "")
    
    # Get org-specific webhook secret
    if org_id:
        config = await get_org_razorpay_config(org_id)
        webhook_secret = config.get("webhook_secret", RAZORPAY_WEBHOOK_SECRET)
    else:
        webhook_secret = RAZORPAY_WEBHOOK_SECRET
    
    # Verify webhook signature
    if webhook_secret:
        import hmac
        import hashlib
        expected_signature = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            logger.warning(f"Invalid webhook signature for event {event}")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    db = get_db()
    
    # Log webhook event
    webhook_log = {
        "webhook_id": f"WH-{uuid.uuid4().hex[:12].upper()}",
        "event": event,
        "payment_id": payment_entity.get("id"),
        "order_id": payment_entity.get("order_id"),
        "amount": payment_entity.get("amount"),
        "status": payment_entity.get("status"),
        "organization_id": org_id,
        "payload": payload,
        "received_at": datetime.now(timezone.utc).isoformat()
    }
    await db.webhook_logs.insert_one(webhook_log)
    
    logger.info(f"[RAZORPAY WEBHOOK] Event: {event}, Payment: {payment_entity.get('id')}")
    
    # Handle specific events
    if event == "payment.captured":
        await process_payment_captured_webhook(payment_entity, org_id, notes.get("invoice_id", ""))
    
    elif event == "payment.failed":
        order_id = payment_entity.get("order_id")
        await db.payment_orders.update_one(
            {"order_id": order_id},
            {"$set": {
                "status": "failed",
                "error_code": payment_entity.get("error_code"),
                "error_reason": payment_entity.get("error_description"),
                "failed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    elif event == "payment_link.paid":
        link_entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        link_id = link_entity.get("id")
        
        await db.razorpay_payment_links.update_one(
            {"payment_link_id": link_id},
            {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    elif event == "refund.processed":
        refund_entity = payload.get("payload", {}).get("refund", {}).get("entity", {})
        await db.refunds.update_one(
            {"razorpay_refund_id": refund_entity.get("id")},
            {"$set": {"status": "processed", "processed_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"status": "processed", "event": event}


async def process_payment_captured_webhook(payment_entity: Dict, org_id: str, invoice_id: str):
    """Process payment.captured webhook - update invoice and post journal entry"""
    db = get_db()
    
    order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")
    amount_paise = payment_entity.get("amount", 0)
    amount_inr = amount_paise / 100
    
    logger.info(f"Processing captured payment: {payment_id} for ₹{amount_inr}")
    
    # Get order to find invoice
    order = await db.payment_orders.find_one({"order_id": order_id}, {"_id": 0})
    if not order:
        logger.warning(f"Order {order_id} not found for payment {payment_id}")
        return
    
    invoice_id = invoice_id or order.get("invoice_id")
    
    # Get invoice (try enhanced first)
    invoice = await db.invoices_enhanced.find_one({"invoice_id": invoice_id}, {"_id": 0})
    collection = db.invoices_enhanced
    if not invoice:
        invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
        collection = db.invoices
    
    if invoice:
        # Calculate new balance
        total = float(invoice.get("grand_total", invoice.get("total", 0)))
        current_paid = float(invoice.get("amount_paid", 0))
        new_paid = current_paid + amount_inr
        new_balance = max(0, total - new_paid)
        new_status = "paid" if new_balance <= 0 else "partially_paid"
        
        # Update invoice
        await collection.update_one(
            {"invoice_id": invoice_id},
            {"$set": {
                "status": new_status,
                "amount_paid": new_paid,
                "balance_due": new_balance,
                "razorpay_payment_id": payment_id,
                "razorpay_payment_method": payment_entity.get("method"),
                "razorpay_payment_date": datetime.now(timezone.utc).isoformat(),
                "last_modified_time": datetime.now(timezone.utc).isoformat()
            },
            "$push": {
                "payments": {
                    "payment_id": payment_id,
                    "razorpay_payment_id": payment_id,
                    "amount": amount_inr,
                    "method": payment_entity.get("method"),
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                }
            }}
        )
        
        # Post journal entry for double-entry bookkeeping
        if org_id:
            try:
                await post_payment_received_journal_entry(
                    organization_id=org_id,
                    payment={
                        "payment_id": payment_id,
                        "amount": amount_inr,
                        "payment_mode": payment_entity.get("method", "razorpay"),
                        "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "customer_name": invoice.get("customer_name", ""),
                        "invoice_number": invoice.get("invoice_number", ""),
                        "reference_number": payment_id
                    }
                )
                logger.info(f"Posted journal entry for Razorpay payment {payment_id}")
            except Exception as e:
                logger.error(f"Failed to post journal entry for payment {payment_id}: {e}")
        
        # Update customer outstanding
        customer_id = invoice.get("customer_id")
        if customer_id:
            await db.contacts.update_one(
                {"contact_id": customer_id},
                {"$inc": {"outstanding_receivable_amount": -amount_inr}}
            )
    
    # Update order status
    await db.payment_orders.update_one(
        {"order_id": order_id},
        {"$set": {
            "status": "captured",
            "razorpay_payment_id": payment_id,
            "payment_method": payment_entity.get("method"),
            "webhook_processed": True,
            "captured_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Create payment record
    payment_record = {
        "payment_id": f"RPAY-{uuid.uuid4().hex[:12].upper()}",
        "razorpay_payment_id": payment_id,
        "razorpay_order_id": order_id,
        "invoice_id": invoice_id,
        "organization_id": org_id,
        "customer_id": invoice.get("customer_id") if invoice else None,
        "customer_name": invoice.get("customer_name") if invoice else None,
        "amount": amount_inr,
        "payment_mode": "razorpay",
        "method": payment_entity.get("method"),
        "card_last4": payment_entity.get("card", {}).get("last4"),
        "bank": payment_entity.get("bank"),
        "wallet": payment_entity.get("wallet"),
        "vpa": payment_entity.get("vpa"),
        "status": "captured",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    await db.customerpayments.insert_one(payment_record)
    
    logger.info(f"Payment {payment_id} processed successfully")


@router.post("/refund")
async def process_refund(request: RefundRequest):
    """Process a refund for a payment"""
    db = get_db()
    
    # Find the payment
    payment = await db.customerpayments.find_one(
        {"$or": [
            {"razorpay_payment_id": request.payment_id},
            {"payment_id": request.payment_id}
        ]},
        {"_id": 0}
    )
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    razorpay_payment_id = payment.get("razorpay_payment_id")
    if not razorpay_payment_id:
        raise HTTPException(status_code=400, detail="Not a Razorpay payment")
    
    amount_paise = int(request.amount * 100) if request.amount else None
    
    refund = await refund_payment(
        razorpay_payment_id,
        amount_paise,
        {"reason": request.reason} if request.reason else None
    )
    
    # Record refund
    refund_record = {
        "refund_id": refund.get("id", f"RFND-{uuid.uuid4().hex[:12].upper()}"),
        "payment_id": payment.get("payment_id"),
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_refund_id": refund.get("id"),
        "invoice_id": payment.get("invoice_id"),
        "amount": request.amount or payment.get("amount"),
        "reason": request.reason,
        "status": refund.get("status", "processed"),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.refunds.insert_one(refund_record)
    
    # Update invoice balance if applicable
    if payment.get("invoice_id"):
        refund_amount = request.amount or payment.get("amount", 0)
        await db.invoices.update_one(
            {"invoice_id": payment.get("invoice_id")},
            {
                "$inc": {"balance": refund_amount},
                "$set": {"status": "partial"}
            }
        )
    
    return {
        "code": 0,
        "message": "Refund processed",
        "refund": refund_record,
        "is_mock": refund.get("_mock", False)
    }


@router.get("/orders")
async def list_payment_orders(invoice_id: str = "", status: str = "", page: int = 1, per_page: int = 25):
    """List payment orders"""
    db = get_db()
    
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if status:
        query["status"] = status
    
    skip = (page - 1) * per_page
    orders = await db.payment_orders.find(query, {"_id": 0}).sort("created_time", -1).skip(skip).limit(per_page).to_list(length=per_page)
    total = await db.payment_orders.count_documents(query)
    
    return {
        "code": 0,
        "orders": orders,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }


@router.get("/links")
async def list_payment_links(invoice_id: str = "", status: str = ""):
    """List payment links"""
    db = get_db()
    
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if status:
        query["status"] = status
    
    links = await db.razorpay_payment_links.find(query, {"_id": 0}).sort("created_time", -1).to_list(length=100)
    
    return {"code": 0, "payment_links": links}
