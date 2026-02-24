"""
Invoice Payment Gateway Integration - Stripe
Enables online payments for invoices, card-on-file, and payment links.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime, timezone
import motor.motor_asyncio
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

from emergentintegrations.payments.stripe.checkout import (
from utils.database import extract_org_id, org_query

    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/invoice-payments", tags=["Invoice Payments"])

# Collections - Use main collections with Zoho-synced data
payment_transactions_collection = db["payment_transactions"]
invoices_collection = db["invoices"]
payments_received_collection = db["customerpayments"]
customer_credits_collection = db["customer_credits"]
contacts_collection = db["contacts"]


# ==================== MODELS ====================

class CreatePaymentLinkRequest(BaseModel):
    """Request to create a payment link for an invoice"""
    invoice_id: str
    origin_url: str  # Frontend origin for success/cancel URLs

class PaymentStatusRequest(BaseModel):
    """Request to check payment status"""
    session_id: str


# ==================== HELPER FUNCTIONS ====================

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

async def get_next_payment_number() -> str:
    """Generate next payment number for payments received"""
    settings = await db["payment_settings"].find_one({"type": "numbering"})
    if not settings:
        settings = {"type": "numbering", "prefix": "PMT", "next_number": 1}
        await db["payment_settings"].insert_one(settings)
    
    prefix = settings.get("prefix", "PMT")
    next_num = settings.get("next_number", 1)
    
    payment_number = f"{prefix}-{next_num:05d}"
    
    await db["payment_settings"].update_one(
        {"type": "numbering"},
        {"$set": {"next_number": next_num + 1}}
    )
    
    return payment_number


# ==================== ENDPOINTS ====================

@router.post("/create-payment-link")
async def create_payment_link(request: CreatePaymentLinkRequest, http_request: Request)::
    org_id = extract_org_id(request)
    """
    Create a Stripe checkout session for an invoice payment.
    Returns a payment link URL that the customer can use to pay.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    # Get invoice
    invoice = await invoices_collection.find_one({"invoice_id": request.invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice can be paid
    if invoice.get("status") in ["paid", "void", "draft"]:
        raise HTTPException(status_code=400, detail=f"Invoice cannot be paid (status: {invoice.get('status')})")
    
    balance_due = invoice.get("balance_due", 0)
    if balance_due <= 0:
        raise HTTPException(status_code=400, detail="Invoice has no balance due")
    
    # Build success and cancel URLs
    success_url = f"{request.origin_url}/invoices?payment_success=true&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/invoices?payment_cancelled=true&invoice_id={request.invoice_id}"
    
    # Initialize Stripe checkout
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=float(balance_due),
        currency="inr",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "invoice_id": request.invoice_id,
            "invoice_number": invoice.get("invoice_number", ""),
            "customer_id": invoice.get("customer_id", ""),
            "customer_name": invoice.get("customer_name", ""),
            "payment_type": "invoice_payment"
        }
    )
    
    try:
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")
    
    # Create payment transaction record
    transaction_id = generate_id("TXN")
    transaction_doc = {
        "transaction_id": transaction_id,
        "session_id": session.session_id,
        "invoice_id": request.invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "customer_id": invoice.get("customer_id"),
        "customer_name": invoice.get("customer_name"),
        "amount": float(balance_due),
        "currency": "INR",
        "payment_method": "stripe",
        "payment_status": "pending",
        "checkout_url": session.url,
        "metadata": checkout_request.metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await payment_transactions_collection.insert_one(transaction_doc)
    
    # Update invoice with payment link
    await invoices_collection.update_one(
        {"invoice_id": request.invoice_id},
        {"$set": {
            "payment_link": session.url,
            "payment_session_id": session.session_id,
            "payment_link_created_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "code": 0,
        "payment_url": session.url,
        "session_id": session.session_id,
        "amount": balance_due,
        "transaction_id": transaction_id
    }


@router.get("/status/{session_id}")
async def get_payment_status(session_id: str, http_request: Request)::
    org_id = extract_org_id(request)
    """
    Check the status of a Stripe checkout session.
    Used for polling after redirect from Stripe.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    # Get transaction record
    transaction = await payment_transactions_collection.find_one({"session_id": session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already processed, return stored status
    if transaction.get("payment_status") in ["paid", "completed"]:
        return {
            "code": 0,
            "status": "complete",
            "payment_status": "paid",
            "amount": transaction.get("amount"),
            "invoice_id": transaction.get("invoice_id"),
            "already_processed": True
        }
    
    # Initialize Stripe checkout
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check payment status: {str(e)}")
    
    # Update transaction status
    await payment_transactions_collection.update_one(
        {"session_id": session_id},
        {"$set": {
            "payment_status": status.payment_status,
            "stripe_status": status.status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # If payment is successful, create payment record
    if status.payment_status == "paid":
        # Check if already processed (prevent duplicate processing)
        existing = await payments_received_collection.find_one({
            "stripe_session_id": session_id,
            "status": "recorded"
        })
        
        if not existing:
            await process_successful_payment(transaction, session_id)
    
    return {
        "code": 0,
        "status": status.status,
        "payment_status": status.payment_status,
        "amount": status.amount_total / 100,  # Convert from cents
        "currency": status.currency,
        "invoice_id": transaction.get("invoice_id"),
        "already_processed": False
    }


async def process_successful_payment(transaction: dict, session_id: str):
    """Process a successful Stripe payment - create payment record and update invoice"""
    invoice_id = transaction.get("invoice_id")
    amount = transaction.get("amount", 0)
    customer_id = transaction.get("customer_id")
    
    # Get customer details
    customer = await contacts_collection.find_one({"contact_id": customer_id})
    customer_name = customer.get("name", "") if customer else transaction.get("customer_name", "")
    
    # Create payment record in payments_received
    payment_id = generate_id("PAY")
    payment_number = await get_next_payment_number()
    
    payment_doc = {
        "payment_id": payment_id,
        "payment_number": payment_number,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "amount": amount,
        "payment_mode": "online",
        "deposit_to_account": "Stripe",
        "reference_number": session_id,
        "bank_charges": 0,
        "notes": f"Online payment via Stripe for invoice {transaction.get('invoice_number', '')}",
        "allocations": [{"invoice_id": invoice_id, "amount": amount}],
        "amount_allocated": amount,
        "overpayment_amount": 0,
        "is_retainer": False,
        "status": "recorded",
        "stripe_session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await payments_received_collection.insert_one(payment_doc)
    
    # Update invoice
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if invoice:
        current_paid = invoice.get("amount_paid", 0)
        current_balance = invoice.get("balance_due", 0)
        
        new_paid = current_paid + amount
        new_balance = max(0, current_balance - amount)
        new_status = "paid" if new_balance <= 0 else "partially_paid"
        
        await invoices_collection.update_one(
            {"invoice_id": invoice_id},
            {"$set": {
                "amount_paid": new_paid,
                "balance_due": new_balance,
                "status": new_status,
                "last_payment_date": datetime.now(timezone.utc).isoformat(),
                "online_payment_completed": True
            }}
        )
    
    # Update transaction as completed
    await payment_transactions_collection.update_one(
        {"session_id": session_id},
        {"$set": {
            "payment_status": "completed",
            "payment_id": payment_id,
            "payment_number": payment_number,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update customer balance
    await update_customer_balance(customer_id)


async def update_customer_balance(customer_id: str):
    """Update customer's receivable balance"""
    invoices = await invoices_collection.find({
        "customer_id": customer_id,
        "status": {"$nin": ["void", "draft"]}
    }).to_list(1000)
    
    total_receivable = sum(inv.get("balance_due", 0) for inv in invoices)
    
    credits = await customer_credits_collection.find({
        "customer_id": customer_id,
        "status": "available"
    }).to_list(1000)
    
    total_credits = sum(c.get("amount", 0) for c in credits)
    
    await contacts_collection.update_one(
        {"contact_id": customer_id},
        {"$set": {
            "receivable_balance": round(total_receivable, 2),
            "unused_credits": round(total_credits, 2),
            "balance_updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )


@router.get("/invoice/{invoice_id}/payment-link")
async def get_invoice_payment_link(invoice_id: str, request: Request)::
    org_id = extract_org_id(request)
    """Get existing payment link for an invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment_link = invoice.get("payment_link")
    session_id = invoice.get("payment_session_id")
    
    if not payment_link:
        return {"code": 0, "has_payment_link": False}
    
    return {
        "code": 0,
        "has_payment_link": True,
        "payment_link": payment_link,
        "session_id": session_id,
        "created_at": invoice.get("payment_link_created_at")
    }


@router.get("/transactions")
async def list_payment_transactions(
    invoice_id: str = "",
    customer_id: str = "",
    status: str = "",
    page: int = 1,
    per_page: int = 50, request: Request)::
    org_id = extract_org_id(request)
    """List payment transactions"""
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["payment_status"] = status
    
    total = await payment_transactions_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    transactions = await payment_transactions_collection.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "transactions": transactions,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/summary")
async def get_online_payments_summary(request: Request)::
    org_id = extract_org_id(request)
    """Get summary of online payments"""
    # Total online payments
    pipeline = [
        {"$match": {"payment_status": "completed"}},
        {"$group": {
            "_id": None,
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    result = await payment_transactions_collection.aggregate(pipeline).to_list(1)
    
    # Pending payments
    pending = await payment_transactions_collection.count_documents({"payment_status": "pending"})
    
    # Failed payments
    failed = await payment_transactions_collection.count_documents({"payment_status": {"$in": ["expired", "failed"]}})
    
    stats = result[0] if result else {"total_amount": 0, "count": 0}
    
    return {
        "code": 0,
        "summary": {
            "completed_amount": stats.get("total_amount", 0),
            "completed_count": stats.get("count", 0),
            "pending_count": pending,
            "failed_count": failed
        }
    }
