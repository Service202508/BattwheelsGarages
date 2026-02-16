"""
Razorpay Payment Routes
Handles payment orders, payment links, and webhooks for invoice payments
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import os
import json

from database import get_db
from services.razorpay_service import (
    is_razorpay_configured,
    create_razorpay_order,
    create_payment_link,
    fetch_payment,
    verify_payment_signature,
    verify_webhook_signature,
    refund_payment
)

router = APIRouter(prefix="/payments", tags=["Payments"])


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


@router.get("/config")
async def get_payment_config():
    """Get Razorpay configuration status"""
    return {
        "code": 0,
        "configured": is_razorpay_configured(),
        "key_id": os.environ.get('RAZORPAY_KEY_ID', '')[:10] + '...' if is_razorpay_configured() else None,
        "message": "Razorpay is configured" if is_razorpay_configured() else "Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to backend/.env"
    }


@router.post("/create-order")
async def create_payment_order(request: CreateOrderRequest):
    """Create a Razorpay order for an invoice"""
    db = get_db()
    
    invoice = await db.invoices.find_one({"invoice_id": request.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") in ["void", "paid"]:
        raise HTTPException(status_code=400, detail=f"Cannot create payment for {invoice['status']} invoice")
    
    amount = request.amount or invoice.get("balance", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    if amount > invoice.get("balance", 0):
        raise HTTPException(status_code=400, detail="Amount exceeds invoice balance")
    
    # Create Razorpay order
    order = await create_razorpay_order(
        amount_inr=amount,
        receipt=invoice.get("invoice_number", request.invoice_id),
        notes={
            "invoice_id": request.invoice_id,
            "invoice_number": invoice.get("invoice_number"),
            "customer_id": invoice.get("customer_id"),
            "customer_name": invoice.get("customer_name")
        }
    )
    
    # Store order in database
    order_record = {
        "order_id": order["id"],
        "invoice_id": request.invoice_id,
        "customer_id": invoice.get("customer_id"),
        "amount": amount,
        "amount_paise": int(amount * 100),
        "currency": "INR",
        "status": "created",
        "razorpay_order": order,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payment_orders.insert_one(order_record)
    
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
            "invoice_id": request.invoice_id,
            "invoice_number": invoice.get("invoice_number"),
            "balance": invoice.get("balance")
        },
        "key_id": os.environ.get('RAZORPAY_KEY_ID', ''),
        "is_mock": order.get("_mock", False)
    }


@router.post("/create-payment-link/{invoice_id}")
async def create_invoice_payment_link(invoice_id: str, expire_days: int = 30):
    """Create a shareable payment link for an invoice"""
    db = get_db()
    
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("balance", 0) <= 0:
        raise HTTPException(status_code=400, detail="Invoice has no balance due")
    
    # Get customer details
    customer = await db.contacts.find_one({"contact_id": invoice.get("customer_id")}, {"_id": 0})
    
    expire_timestamp = int((datetime.now(timezone.utc) + timedelta(days=expire_days)).timestamp())
    
    payment_link = await create_payment_link(
        amount_inr=invoice.get("balance", 0),
        description=f"Payment for Invoice {invoice.get('invoice_number')}",
        customer_name=invoice.get("customer_name", "Customer"),
        customer_email=customer.get("email", "") if customer else "",
        customer_phone=customer.get("phone", "") if customer else "",
        reference_id=invoice_id,
        expire_by=expire_timestamp
    )
    
    # Store payment link in database
    link_record = {
        "payment_link_id": payment_link["id"],
        "invoice_id": invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "customer_id": invoice.get("customer_id"),
        "amount": invoice.get("balance"),
        "short_url": payment_link.get("short_url"),
        "status": "active",
        "expire_by": expire_timestamp,
        "razorpay_link": payment_link,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.razorpay_payment_links.insert_one(link_record)
    
    # Update invoice with payment link
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "payment_link_id": payment_link["id"],
            "payment_link_url": payment_link.get("short_url"),
            "has_payment_link": True
        }}
    )
    
    return {
        "code": 0,
        "message": "Payment link created",
        "payment_link": {
            "id": payment_link["id"],
            "short_url": payment_link.get("short_url"),
            "amount": invoice.get("balance"),
            "expire_by": expire_timestamp
        },
        "is_mock": payment_link.get("_mock", False)
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
    """Handle Razorpay webhooks for payment events"""
    body = await request.body()
    signature = request.headers.get('X-Razorpay-Signature', '')
    
    # Verify webhook signature
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event = payload.get("event")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    
    db = get_db()
    
    # Log webhook event
    webhook_log = {
        "webhook_id": f"WH-{uuid.uuid4().hex[:12].upper()}",
        "event": event,
        "payment_id": payment_entity.get("id"),
        "order_id": payment_entity.get("order_id"),
        "amount": payment_entity.get("amount"),
        "status": payment_entity.get("status"),
        "payload": payload,
        "received_at": datetime.now(timezone.utc).isoformat()
    }
    await db.webhook_logs.insert_one(webhook_log)
    
    # Handle specific events
    if event == "payment.captured":
        # Payment successful - update order and invoice
        order_id = payment_entity.get("order_id")
        
        order = await db.payment_orders.find_one({"order_id": order_id}, {"_id": 0})
        if order:
            invoice_id = order.get("invoice_id")
            amount_paid = payment_entity.get("amount", 0) / 100
            
            # Update invoice if not already processed
            invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
            if invoice and invoice.get("balance", 0) > 0:
                new_balance = invoice.get("balance", 0) - amount_paid
                new_status = "paid" if new_balance <= 0 else "partial"
                
                await db.invoices.update_one(
                    {"invoice_id": invoice_id},
                    {"$set": {"balance": max(0, new_balance), "status": new_status}}
                )
            
            await db.payment_orders.update_one(
                {"order_id": order_id},
                {"$set": {"status": "captured", "webhook_processed": True}}
            )
    
    elif event == "payment.failed":
        order_id = payment_entity.get("order_id")
        await db.payment_orders.update_one(
            {"order_id": order_id},
            {"$set": {"status": "failed", "error_reason": payment_entity.get("error_reason")}}
        )
    
    elif event == "payment_link.paid":
        link_entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        link_id = link_entity.get("id")
        
        await db.razorpay_payment_links.update_one(
            {"payment_link_id": link_id},
            {"$set": {"status": "paid"}}
        )
    
    return {"status": "processed", "event": event}


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
