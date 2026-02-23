"""
Razorpay Payment Integration Routes
====================================
Full Razorpay integration with:
- Organization-specific credentials (multi-tenant)
- Payment link generation for invoices
- Webhook handling with signature verification
- Payment status tracking
- Refund processing
- Journal entry auto-posting on payment

All mocked responses replaced with real Razorpay API calls.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import razorpay
import hmac
import hashlib
import os
import uuid
import logging
import json

# Import double-entry posting hooks
from services.posting_hooks import post_payment_received_journal_entry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/razorpay", tags=["Razorpay Payments"])

# Database connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
organizations_collection = db.organizations
invoices_collection = db.invoices_enhanced
payments_collection = db.razorpay_payments
refunds_collection = db.razorpay_refunds

# Global fallback keys (for orgs without custom keys)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')


# ==================== REQUEST MODELS ====================

class RazorpayConfig(BaseModel):
    """Razorpay configuration for an organization"""
    key_id: str = Field(..., min_length=10, description="Razorpay Key ID")
    key_secret: str = Field(..., min_length=10, description="Razorpay Key Secret")
    webhook_secret: str = Field(default="", description="Webhook secret for signature verification")
    test_mode: bool = Field(default=True, description="True for test mode, False for live")


class CreatePaymentLinkRequest(BaseModel):
    """Request to create a payment link for an invoice"""
    invoice_id: str
    expire_hours: int = Field(default=72, ge=1, le=720, description="Link expiry in hours")
    send_notification: bool = Field(default=True, description="Send SMS/Email notification")
    callback_url: Optional[str] = None


class RefundRequest(BaseModel):
    """Request to initiate a refund"""
    payment_id: str
    amount: Optional[float] = Field(default=None, description="Amount to refund in INR (None for full)")
    reason: str = Field(default="", description="Reason for refund")


# ==================== HELPER FUNCTIONS ====================

async def get_org_razorpay_config(org_id: str) -> Dict:
    """Get Razorpay configuration for an organization (uses credential_service for encryption)"""
    from services.credential_service import get_razorpay_credentials
    return await get_razorpay_credentials(org_id)


def get_razorpay_client(config: Dict):
    """Create Razorpay client from config"""
    key_id = config.get("key_id", "")
    key_secret = config.get("key_secret", "")
    
    if not key_id or not key_secret:
        return None
    
    return razorpay.Client(auth=(key_id, key_secret))


async def get_org_id_from_request(request: Request) -> str:
    """Extract organization ID from request"""
    org_id = request.headers.get("X-Organization-ID")
    if not org_id:
        # Try to get from session
        session_token = request.cookies.get("session_token")
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    membership = await db.organization_users.find_one(
                        {"user_id": user["user_id"], "status": "active"},
                        {"organization_id": 1}
                    )
                    if membership:
                        org_id = membership["organization_id"]
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    return org_id


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify Razorpay webhook signature"""
    if not secret:
        logger.warning("Webhook secret not configured, skipping verification")
        return True
    
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


# ==================== CONFIGURATION ENDPOINTS ====================

@router.get("/config")
async def get_razorpay_config(request: Request):
    """Get current Razorpay configuration status (keys masked)"""
    org_id = await get_org_id_from_request(request)
    config = await get_org_razorpay_config(org_id)
    
    key_id = config.get("key_id", "")
    has_secret = bool(config.get("key_secret"))
    has_webhook = bool(config.get("webhook_secret"))
    
    return {
        "code": 0,
        "configured": bool(key_id and has_secret),
        "key_id_masked": f"{key_id[:8]}...{key_id[-4:]}" if len(key_id) > 12 else key_id[:4] + "***" if key_id else None,
        "has_key_secret": has_secret,
        "has_webhook_secret": has_webhook,
        "test_mode": config.get("test_mode", True),
        "using_global_keys": not (await organizations_collection.find_one(
            {"organization_id": org_id, "razorpay_config": {"$exists": True}}
        ))
    }


@router.post("/config")
async def save_razorpay_config(config: RazorpayConfig, request: Request):
    """Save Razorpay configuration for the organization"""
    org_id = await get_org_id_from_request(request)
    
    # Validate keys by making a test API call
    test_client = razorpay.Client(auth=(config.key_id, config.key_secret))
    
    try:
        # Try to fetch account details to validate keys
        test_client.order.all({"count": 1})
    except razorpay.errors.BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Razorpay credentials: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to validate credentials: {str(e)}")
    
    # Save using credential_service (encrypted)
    from services.credential_service import save_credentials, RAZORPAY
    await save_credentials(org_id, RAZORPAY, {
        "key_id": config.key_id,
        "key_secret": config.key_secret,
        "webhook_secret": config.webhook_secret,
        "test_mode": config.test_mode,
    })
    
    return {
        "code": 0,
        "message": "Razorpay configuration saved successfully",
        "test_mode": config.test_mode
    }


@router.delete("/config")
async def remove_razorpay_config(request: Request):
    """Remove organization-specific Razorpay config (falls back to global)"""
    org_id = await get_org_id_from_request(request)
    
    from services.credential_service import delete_credentials, RAZORPAY
    await delete_credentials(org_id, RAZORPAY)
    # Also clear legacy plaintext config from org document
    await organizations_collection.update_one(
        {"organization_id": org_id},
        {"$unset": {"razorpay_config": ""}}
    )
    
    return {"code": 0, "message": "Razorpay configuration removed, using global keys"}


# ==================== ORDER & PAYMENT LINK ENDPOINTS ====================

@router.post("/create-order")
async def create_razorpay_order(request: Request, invoice_id: str):
    """
    Create a Razorpay order for an invoice.
    Returns order_id that can be used with Razorpay Checkout.
    """
    org_id = await get_org_id_from_request(request)
    config = await get_org_razorpay_config(org_id)
    
    # Verify invoice exists
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id, "organization_id": org_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if already paid
    if invoice.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Invoice is already paid")
    
    # Get client
    rp_client = get_razorpay_client(config)
    if not rp_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured. Please add credentials in settings.")
    
    # Calculate amount due
    total = float(invoice.get("grand_total", invoice.get("total", 0)))
    paid = float(invoice.get("amount_paid", 0))
    due = total - paid
    
    if due <= 0:
        raise HTTPException(status_code=400, detail="No amount due on this invoice")
    
    # Create Razorpay order
    try:
        order_data = {
            "amount": int(due * 100),  # Convert to paise
            "currency": "INR",
            "receipt": invoice.get("invoice_number", invoice_id),
            "payment_capture": 1,  # Auto-capture
            "notes": {
                "invoice_id": invoice_id,
                "invoice_number": invoice.get("invoice_number", ""),
                "customer_id": invoice.get("customer_id", ""),
                "organization_id": org_id
            }
        }
        
        order = rp_client.order.create(order_data)
        
        # Store order reference
        await invoices_collection.update_one(
            {"invoice_id": invoice_id},
            {"$set": {
                "razorpay_order_id": order["id"],
                "razorpay_order_created_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Store in payments collection
        payment_record = {
            "payment_id": f"rp_{uuid.uuid4().hex[:12]}",
            "razorpay_order_id": order["id"],
            "invoice_id": invoice_id,
            "organization_id": org_id,
            "amount": due,
            "amount_paise": int(due * 100),
            "currency": "INR",
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await payments_collection.insert_one(payment_record)
        
        return {
            "code": 0,
            "order_id": order["id"],
            "amount": due,
            "amount_paise": int(due * 100),
            "currency": "INR",
            "key_id": config["key_id"],
            "invoice_number": invoice.get("invoice_number"),
            "customer_name": invoice.get("customer_name"),
            "customer_email": invoice.get("customer_email"),
            "customer_phone": invoice.get("customer_phone", "")
        }
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create order: {str(e)}")


@router.post("/payment-link")
async def create_payment_link(req: CreatePaymentLinkRequest, request: Request):
    """
    Create a Razorpay payment link for an invoice.
    Returns a shareable payment URL.
    """
    org_id = await get_org_id_from_request(request)
    config = await get_org_razorpay_config(org_id)
    
    # Verify invoice
    invoice = await invoices_collection.find_one({"invoice_id": req.invoice_id, "organization_id": org_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Invoice is already paid")
    
    rp_client = get_razorpay_client(config)
    if not rp_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    # Calculate amount
    total = float(invoice.get("grand_total", invoice.get("total", 0)))
    paid = float(invoice.get("amount_paid", 0))
    due = total - paid
    
    if due <= 0:
        raise HTTPException(status_code=400, detail="No amount due")
    
    # Build payment link
    try:
        expire_timestamp = int((datetime.now(timezone.utc) + timedelta(hours=req.expire_hours)).timestamp())
        
        link_data = {
            "amount": int(due * 100),
            "currency": "INR",
            "accept_partial": False,
            "description": f"Payment for Invoice {invoice.get('invoice_number', '')}",
            "customer": {
                "name": invoice.get("customer_name", "Customer"),
                "email": invoice.get("customer_email", ""),
                "contact": invoice.get("customer_phone", "")
            },
            "notify": {
                "sms": req.send_notification and bool(invoice.get("customer_phone")),
                "email": req.send_notification and bool(invoice.get("customer_email"))
            },
            "reference_id": req.invoice_id,
            "expire_by": expire_timestamp,
            "notes": {
                "invoice_id": req.invoice_id,
                "invoice_number": invoice.get("invoice_number", ""),
                "organization_id": org_id
            }
        }
        
        if req.callback_url:
            link_data["callback_url"] = req.callback_url
            link_data["callback_method"] = "get"
        
        payment_link = rp_client.payment_link.create(link_data)
        
        # Update invoice with payment link
        await invoices_collection.update_one(
            {"invoice_id": req.invoice_id},
            {"$set": {
                "razorpay_payment_link_id": payment_link["id"],
                "razorpay_payment_link_url": payment_link["short_url"],
                "razorpay_payment_link_created_at": datetime.now(timezone.utc).isoformat(),
                "razorpay_payment_link_expires_at": datetime.fromtimestamp(expire_timestamp, timezone.utc).isoformat()
            }}
        )
        
        return {
            "code": 0,
            "payment_link_id": payment_link["id"],
            "payment_link_url": payment_link["short_url"],
            "amount": due,
            "expires_at": datetime.fromtimestamp(expire_timestamp, timezone.utc).isoformat(),
            "notification_sent": req.send_notification
        }
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Payment link creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create payment link: {str(e)}")


@router.get("/invoice/{invoice_id}/payment-status")
async def get_invoice_payment_status(invoice_id: str, request: Request):
    """
    Get detailed payment status for an invoice.
    Shows Razorpay transaction details when paid.
    """
    org_id = await get_org_id_from_request(request)
    
    invoice = await invoices_collection.find_one(
        {"invoice_id": invoice_id, "organization_id": org_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get payment records
    payments = await payments_collection.find(
        {"invoice_id": invoice_id, "status": "captured"},
        {"_id": 0}
    ).to_list(100)
    
    total = float(invoice.get("grand_total", invoice.get("total", 0)))
    paid = float(invoice.get("amount_paid", 0))
    due = total - paid
    
    # Determine status
    if due <= 0:
        payment_status = "paid"
    elif paid > 0:
        payment_status = "partial"
    else:
        payment_status = "pending"
    
    return {
        "code": 0,
        "invoice_id": invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "payment_status": payment_status,
        "total_amount": total,
        "amount_paid": paid,
        "amount_due": max(0, due),
        "razorpay_order_id": invoice.get("razorpay_order_id"),
        "razorpay_payment_link_url": invoice.get("razorpay_payment_link_url"),
        "razorpay_payment_link_expires_at": invoice.get("razorpay_payment_link_expires_at"),
        "payments": [
            {
                "payment_id": p.get("razorpay_payment_id"),
                "amount": p.get("amount"),
                "payment_method": p.get("payment_method"),
                "payment_date": p.get("payment_date"),
                "transaction_id": p.get("razorpay_payment_id")
            }
            for p in payments
        ]
    }


# ==================== WEBHOOK ENDPOINT ====================

@router.post("/webhook")
async def handle_razorpay_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Razorpay webhook events.
    
    Verifies signature and processes:
    - payment.captured: Mark invoice as paid, post journal entry
    - payment.failed: Log failure
    - refund.processed: Update refund status
    """
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = payload.get("event")
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    
    # Extract org_id from notes
    notes = entity.get("notes", {})
    org_id = notes.get("organization_id", "")
    invoice_id = notes.get("invoice_id", "")
    
    # Get org-specific webhook secret
    if org_id:
        config = await get_org_razorpay_config(org_id)
        webhook_secret = config.get("webhook_secret", RAZORPAY_WEBHOOK_SECRET)
    else:
        webhook_secret = RAZORPAY_WEBHOOK_SECRET
    
    # Verify signature
    if not verify_webhook_signature(body, signature, webhook_secret):
        logger.warning(f"Invalid webhook signature for event {event_type}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    logger.info(f"[RAZORPAY WEBHOOK] Event: {event_type}, Payment ID: {entity.get('id')}")
    
    # Process event
    if event_type == "payment.captured":
        await process_payment_captured(entity, org_id, invoice_id, background_tasks)
    
    elif event_type == "payment.failed":
        await process_payment_failed(entity, org_id, invoice_id)
    
    elif event_type == "refund.processed":
        refund_entity = payload.get("payload", {}).get("refund", {}).get("entity", {})
        await process_refund_completed(refund_entity, org_id)
    
    return {"status": "ok", "event": event_type}


async def process_payment_captured(payment: Dict, org_id: str, invoice_id: str, background_tasks: BackgroundTasks):
    """Process payment.captured webhook event"""
    payment_id = payment.get("id")
    amount_paise = payment.get("amount", 0)
    amount_inr = amount_paise / 100
    
    logger.info(f"Processing captured payment: {payment_id} for ₹{amount_inr}")
    
    # Update payment record
    await payments_collection.update_one(
        {"razorpay_order_id": payment.get("order_id")},
        {"$set": {
            "razorpay_payment_id": payment_id,
            "status": "captured",
            "amount": amount_inr,
            "payment_method": payment.get("method"),
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "card_last4": payment.get("card", {}).get("last4"),
            "bank": payment.get("bank"),
            "wallet": payment.get("wallet"),
            "vpa": payment.get("vpa"),  # UPI ID
            "email": payment.get("email"),
            "contact": payment.get("contact"),
            "captured_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update invoice
    if invoice_id:
        invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
        if invoice:
            current_paid = float(invoice.get("amount_paid", 0))
            new_paid = current_paid + amount_inr
            total = float(invoice.get("grand_total", invoice.get("total", 0)))
            
            new_status = "paid" if new_paid >= total else "partially_paid"
            
            await invoices_collection.update_one(
                {"invoice_id": invoice_id},
                {"$set": {
                    "status": new_status,
                    "amount_paid": new_paid,
                    "balance_due": max(0, total - new_paid),
                    "razorpay_payment_id": payment_id,
                    "razorpay_payment_method": payment.get("method"),
                    "razorpay_payment_date": datetime.now(timezone.utc).isoformat(),
                    "payment_received_at": datetime.now(timezone.utc).isoformat(),
                    "updated_time": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Post journal entry for double-entry bookkeeping
            try:
                await post_payment_received_journal_entry(
                    organization_id=org_id,
                    payment={
                        "payment_id": payment_id,
                        "amount": amount_inr,
                        "payment_mode": payment.get("method", "online"),
                        "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "customer_name": invoice.get("customer_name", ""),
                        "invoice_number": invoice.get("invoice_number", ""),
                        "reference_number": payment_id
                    }
                )
                logger.info(f"Posted journal entry for Razorpay payment {payment_id}")
            except Exception as e:
                logger.error(f"Failed to post journal entry for payment {payment_id}: {e}")
            
            # TODO: Send payment confirmation email in background
            # background_tasks.add_task(send_payment_confirmation, invoice, payment)
    
    logger.info(f"Payment {payment_id} processed successfully")


async def process_payment_failed(payment: Dict, org_id: str, invoice_id: str):
    """Process payment.failed webhook event"""
    payment_id = payment.get("id")
    error_code = payment.get("error_code")
    error_description = payment.get("error_description")
    
    logger.warning(f"Payment failed: {payment_id} - {error_code}: {error_description}")
    
    # Update payment record
    await payments_collection.update_one(
        {"razorpay_order_id": payment.get("order_id")},
        {"$set": {
            "razorpay_payment_id": payment_id,
            "status": "failed",
            "error_code": error_code,
            "error_description": error_description,
            "failed_at": datetime.now(timezone.utc).isoformat()
        }}
    )


async def process_refund_completed(refund: Dict, org_id: str):
    """Process refund.processed webhook event"""
    refund_id = refund.get("id")
    payment_id = refund.get("payment_id")
    amount_paise = refund.get("amount", 0)
    
    logger.info(f"Processing refund: {refund_id} for payment {payment_id}")
    
    await refunds_collection.update_one(
        {"razorpay_refund_id": refund_id},
        {"$set": {
            "status": "processed",
            "processed_at": datetime.now(timezone.utc).isoformat()
        }}
    )


# ==================== REFUND ENDPOINTS ====================

@router.post("/refund")
async def initiate_refund(req: RefundRequest, request: Request):
    """
    Initiate a refund for a payment.
    Can be full refund or partial refund.
    """
    org_id = await get_org_id_from_request(request)
    config = await get_org_razorpay_config(org_id)
    
    rp_client = get_razorpay_client(config)
    if not rp_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    # Fetch original payment
    payment_record = await payments_collection.find_one({
        "razorpay_payment_id": req.payment_id,
        "organization_id": org_id,
        "status": "captured"
    })
    
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment not found or not captured")
    
    try:
        refund_data = {
            "notes": {
                "reason": req.reason,
                "organization_id": org_id
            }
        }
        
        if req.amount:
            refund_data["amount"] = int(req.amount * 100)  # Convert to paise
        
        refund = rp_client.payment.refund(req.payment_id, refund_data)
        
        # Store refund record
        refund_record = {
            "refund_id": f"rfnd_{uuid.uuid4().hex[:12]}",
            "razorpay_refund_id": refund["id"],
            "razorpay_payment_id": req.payment_id,
            "invoice_id": payment_record.get("invoice_id"),
            "organization_id": org_id,
            "amount": req.amount or payment_record.get("amount"),
            "reason": req.reason,
            "status": refund.get("status", "pending"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await refunds_collection.insert_one(refund_record)
        
        return {
            "code": 0,
            "refund_id": refund["id"],
            "amount": refund.get("amount", 0) / 100,
            "status": refund.get("status"),
            "message": "Refund initiated successfully"
        }
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Refund failed: {e}")
        raise HTTPException(status_code=400, detail=f"Refund failed: {str(e)}")


@router.get("/refunds")
async def list_refunds(
    request: Request,
    invoice_id: str = None,
    payment_id: str = None,
    limit: int = 50
):
    """List refunds for the organization"""
    org_id = await get_org_id_from_request(request)
    
    query = {"organization_id": org_id}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if payment_id:
        query["razorpay_payment_id"] = payment_id
    
    refunds = await refunds_collection.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"code": 0, "refunds": refunds, "count": len(refunds)}


@router.get("/refund/{refund_id}/status")
async def get_refund_status(refund_id: str, request: Request):
    """Get status of a specific refund"""
    org_id = await get_org_id_from_request(request)
    config = await get_org_razorpay_config(org_id)
    
    rp_client = get_razorpay_client(config)
    if not rp_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    # Get local record
    local_refund = await refunds_collection.find_one({
        "razorpay_refund_id": refund_id,
        "organization_id": org_id
    }, {"_id": 0})
    
    if not local_refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    # Fetch latest status from Razorpay
    try:
        rp_refund = rp_client.refund.fetch(refund_id)
        
        # Update local status
        await refunds_collection.update_one(
            {"razorpay_refund_id": refund_id},
            {"$set": {"status": rp_refund.get("status")}}
        )
        
        return {
            "code": 0,
            "refund_id": refund_id,
            "status": rp_refund.get("status"),
            "amount": rp_refund.get("amount", 0) / 100,
            "payment_id": rp_refund.get("payment_id"),
            "created_at": local_refund.get("created_at")
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch refund status: {e}")
        return {
            "code": 0,
            "refund_id": refund_id,
            "status": local_refund.get("status"),
            "amount": local_refund.get("amount"),
            "message": "Using cached status"
        }


# ==================== VERIFICATION ENDPOINTS ====================

@router.post("/verify-payment")
async def verify_payment_signature(request: Request):
    """
    Verify payment signature after checkout completion.
    Called by frontend after Razorpay Checkout.
    """
    data = await request.json()
    
    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")
    
    if not all([order_id, payment_id, signature]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Get org from order
    payment_record = await payments_collection.find_one({"razorpay_order_id": order_id})
    if not payment_record:
        raise HTTPException(status_code=404, detail="Order not found")
    
    org_id = payment_record.get("organization_id")
    config = await get_org_razorpay_config(org_id)
    
    rp_client = get_razorpay_client(config)
    if not rp_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    
    try:
        rp_client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        
        return {"code": 0, "verified": True, "message": "Payment signature verified"}
        
    except razorpay.errors.SignatureVerificationError:
        return {"code": 1, "verified": False, "message": "Invalid signature"}


# ==================== PAYMENT HISTORY ====================

@router.get("/payments")
async def list_payments(
    request: Request,
    invoice_id: str = None,
    status: str = None,
    limit: int = 50
):
    """List payments for the organization"""
    org_id = await get_org_id_from_request(request)
    
    query = {"organization_id": org_id}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if status:
        query["status"] = status
    
    payments = await payments_collection.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"code": 0, "payments": payments, "count": len(payments)}
