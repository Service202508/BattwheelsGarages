"""
Payments Received Module - Zoho Books Style
Handles payment recording, multi-invoice splitting, overpayments, retainer payments, and refunds.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import uuid
import csv
import io
import os

# Import double-entry posting hooks
from services.posting_hooks import post_payment_received_journal_entry

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/payments-received", tags=["Payments Received"])

payments_collection = db["payments_received"]
invoices_collection = db["invoices_enhanced"]
contacts_collection = db["contacts_enhanced"]
customer_credits_collection = db["customer_credits"]
payment_settings_collection = db["payment_settings"]
payment_history_collection = db["payment_history"]


# ==================== MODELS ====================

class PaymentAllocation(BaseModel):
    """Allocation of payment to a specific invoice"""
    invoice_id: str
    amount: float = 0
    
class PaymentRecordCreate(BaseModel):
    """Create a new payment record"""
    customer_id: str
    payment_date: str = ""  # YYYY-MM-DD
    amount: float
    payment_mode: str = "cash"  # cash, cheque, bank_transfer, card, upi, online, other
    deposit_to_account: str = "Undeposited Funds"
    reference_number: str = ""
    bank_charges: float = 0
    tax_deducted: bool = False
    tax_account: str = ""
    tax_amount: float = 0
    notes: str = ""
    allocations: List[PaymentAllocation] = []  # Empty = retainer/advance payment
    is_retainer: bool = False
    send_thank_you: bool = False

class PaymentUpdate(BaseModel):
    """Update payment details"""
    payment_date: Optional[str] = None
    payment_mode: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    deposit_to_account: Optional[str] = None

class RefundCreate(BaseModel):
    """Create a refund from overpayment/credit"""
    amount: float
    refund_date: str = ""
    payment_mode: str = "bank_transfer"
    reference_number: str = ""
    notes: str = ""

class BulkActionRequest(BaseModel):
    """Bulk action on multiple payments"""
    payment_ids: List[str]
    action: str  # delete, export


# ==================== HELPER FUNCTIONS ====================

def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix"""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def round_currency(value: float) -> float:
    """Round to 2 decimal places"""
    return round(value, 2)

async def get_next_payment_number() -> str:
    """Generate next payment number"""
    settings = await payment_settings_collection.find_one({"type": "numbering"})
    if not settings:
        settings = {"type": "numbering", "prefix": "PMT", "next_number": 1}
        await payment_settings_collection.insert_one(settings)
    
    prefix = settings.get("prefix", "PMT")
    next_num = settings.get("next_number", 1)
    
    payment_number = f"{prefix}-{next_num:05d}"
    
    await payment_settings_collection.update_one(
        {"type": "numbering"},
        {"$set": {"next_number": next_num + 1}}
    )
    
    return payment_number

async def add_payment_history(payment_id: str, action: str, details: str, user_id: str = ""):
    """Add entry to payment history"""
    await payment_history_collection.insert_one({
        "payment_id": payment_id,
        "action": action,
        "details": details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

async def update_invoice_payment_status(invoice_id: str):
    """Update invoice status based on payments"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        return
    
    total = invoice.get("grand_total", 0)
    
    # Get all payments for this invoice
    payments = await payments_collection.find({
        "allocations.invoice_id": invoice_id,
        "status": {"$ne": "refunded"}
    }).to_list(1000)
    
    amount_paid = 0
    for payment in payments:
        for alloc in payment.get("allocations", []):
            if alloc.get("invoice_id") == invoice_id:
                amount_paid += alloc.get("amount", 0)
    
    # Add legacy payments (from invoices_enhanced)
    legacy_payments = invoice.get("payments", [])
    for p in legacy_payments:
        amount_paid += p.get("amount", 0)
    
    write_off = invoice.get("write_off_amount", 0)
    balance_due = round_currency(total - amount_paid - write_off)
    
    if balance_due <= 0:
        new_status = "paid"
    elif amount_paid > 0:
        new_status = "partially_paid"
    else:
        new_status = invoice.get("status", "sent")
        if new_status in ["paid", "partially_paid"]:
            new_status = "sent"
    
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "amount_paid": round_currency(amount_paid),
            "balance_due": balance_due,
            "status": new_status,
            "last_payment_date": datetime.now(timezone.utc).isoformat() if amount_paid > 0 else None
        }}
    )

async def update_customer_balance(customer_id: str):
    """Update customer's receivable balance"""
    # Get all unpaid invoices
    invoices = await invoices_collection.find({
        "customer_id": customer_id,
        "status": {"$nin": ["void", "draft"]}
    }).to_list(1000)
    
    total_receivable = sum(inv.get("balance_due", 0) for inv in invoices)
    
    # Get customer credits
    credits = await customer_credits_collection.find({
        "customer_id": customer_id,
        "status": "available"
    }).to_list(1000)
    
    total_credits = sum(c.get("amount", 0) for c in credits)
    
    await contacts_collection.update_one(
        {"contact_id": customer_id},
        {"$set": {
            "receivable_balance": round_currency(total_receivable),
            "unused_credits": round_currency(total_credits),
            "balance_updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

async def get_customer_open_invoices(customer_id: str) -> List[dict]:
    """Get all open invoices for a customer"""
    invoices = await invoices_collection.find({
        "customer_id": customer_id,
        "status": {"$in": ["sent", "partially_paid", "overdue"]},
        "balance_due": {"$gt": 0}
    }, {"_id": 0}).sort("date", 1).to_list(1000)
    
    return invoices

async def get_customer_credits(customer_id: str) -> List[dict]:
    """Get available credits for a customer"""
    credits = await customer_credits_collection.find({
        "customer_id": customer_id,
        "status": "available"
    }, {"_id": 0}).to_list(100)
    
    return credits


# ==================== SETTINGS ENDPOINTS ====================

@router.get("/settings")
async def get_payment_settings():
    """Get payment module settings"""
    settings = {}
    
    numbering = await payment_settings_collection.find_one({"type": "numbering"}, {"_id": 0})
    settings["numbering"] = numbering or {"prefix": "PMT", "next_number": 1}
    
    defaults = await payment_settings_collection.find_one({"type": "defaults"}, {"_id": 0})
    settings["defaults"] = defaults or {
        "default_deposit_account": "Undeposited Funds",
        "send_thank_you_default": False,
        "payment_modes": ["cash", "cheque", "bank_transfer", "card", "upi", "online", "other"]
    }
    
    accounts = await payment_settings_collection.find_one({"type": "accounts"}, {"_id": 0})
    settings["accounts"] = accounts or {
        "deposit_accounts": ["Undeposited Funds", "Petty Cash", "Bank Account", "Savings Account"],
        "tax_accounts": ["TDS Receivable", "TCS Payable"]
    }
    
    return {"code": 0, "settings": settings}

@router.put("/settings")
async def update_payment_settings(settings: dict):
    """Update payment settings"""
    for setting_type, values in settings.items():
        await payment_settings_collection.update_one(
            {"type": setting_type},
            {"$set": {**values, "type": setting_type}},
            upsert=True
        )
    
    return {"code": 0, "message": "Settings updated"}


# ==================== SUMMARY & REPORTS ====================

@router.get("/summary")
async def get_payments_summary(period: str = "this_month"):
    """Get payments summary statistics"""
    today = datetime.now(timezone.utc)
    
    if period == "today":
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "this_week":
        start_date = today - timedelta(days=today.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "this_month":
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "this_quarter":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "this_year":
        start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = None
    
    match_filter = {"status": {"$ne": "refunded"}}
    if start_date:
        match_filter["payment_date"] = {"$gte": start_date.isoformat()[:10]}
    
    # Get all payments
    payments = await payments_collection.find(match_filter, {"_id": 0}).to_list(10000)
    
    total_received = sum(p.get("amount", 0) for p in payments)
    invoice_payments = sum(p.get("amount", 0) for p in payments if not p.get("is_retainer"))
    retainer_payments = sum(p.get("amount", 0) for p in payments if p.get("is_retainer"))
    
    # Count by payment mode
    by_mode = {}
    for p in payments:
        mode = p.get("payment_mode", "other")
        by_mode[mode] = by_mode.get(mode, 0) + p.get("amount", 0)
    
    # Get pending credits
    credits = await customer_credits_collection.find({"status": "available"}, {"_id": 0}).to_list(1000)
    total_credits = sum(c.get("amount", 0) for c in credits)
    
    return {
        "code": 0,
        "summary": {
            "total_received": round_currency(total_received),
            "invoice_payments": round_currency(invoice_payments),
            "retainer_payments": round_currency(retainer_payments),
            "payment_count": len(payments),
            "by_payment_mode": by_mode,
            "unused_credits": round_currency(total_credits),
            "period": period
        }
    }

@router.get("/reports/by-customer")
async def get_payments_by_customer(limit: int = 20):
    """Get payments grouped by customer"""
    pipeline = [
        {"$match": {"status": {"$ne": "refunded"}}},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "total_amount": {"$sum": "$amount"},
            "payment_count": {"$sum": 1},
            "last_payment_date": {"$max": "$payment_date"}
        }},
        {"$sort": {"total_amount": -1}},
        {"$limit": limit}
    ]
    
    results = await payments_collection.aggregate(pipeline).to_list(limit)
    
    return {"code": 0, "report": results}

@router.get("/reports/by-mode")
async def get_payments_by_mode(start_date: str = "", end_date: str = ""):
    """Get payments grouped by payment mode"""
    match_filter = {"status": {"$ne": "refunded"}}
    
    if start_date:
        match_filter["payment_date"] = {"$gte": start_date}
    if end_date:
        if "payment_date" in match_filter:
            match_filter["payment_date"]["$lte"] = end_date
        else:
            match_filter["payment_date"] = {"$lte": end_date}
    
    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": "$payment_mode",
            "total_amount": {"$sum": "$amount"},
            "payment_count": {"$sum": 1}
        }},
        {"$sort": {"total_amount": -1}}
    ]
    
    results = await payments_collection.aggregate(pipeline).to_list(100)
    
    return {"code": 0, "report": results}


# ==================== CUSTOMER INVOICES & CREDITS ====================

@router.get("/customer/{customer_id}/open-invoices")
async def get_customer_invoices_for_payment(customer_id: str):
    """Get open invoices for a customer when recording payment"""
    invoices = await get_customer_open_invoices(customer_id)
    credits = await get_customer_credits(customer_id)
    
    # Get customer info
    customer = await contacts_collection.find_one({"contact_id": customer_id}, {"_id": 0})
    
    return {
        "code": 0,
        "customer": {
            "contact_id": customer_id,
            "name": customer.get("name", "") if customer else "",
            "company_name": customer.get("company_name", "") if customer else "",
            "email": customer.get("email", "") if customer else ""
        },
        "open_invoices": invoices,
        "available_credits": credits,
        "total_outstanding": round_currency(sum(inv.get("balance_due", 0) for inv in invoices)),
        "total_credits": round_currency(sum(c.get("amount", 0) for c in credits))
    }


# ==================== CRUD OPERATIONS ====================

@router.post("/")
async def record_payment(payment: PaymentRecordCreate, background_tasks: BackgroundTasks):
    """Record a new payment"""
    # Validate customer
    customer = await contacts_collection.find_one({"contact_id": payment.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Period lock check
    from utils.period_lock import enforce_period_lock
    payment_date_str = payment.payment_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await enforce_period_lock(contacts_collection.database, customer.get("organization_id", ""), payment_date_str)
    
    payment_id = generate_id("PAY")
    payment_number = await get_next_payment_number()
    payment_date = payment.payment_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Calculate allocation totals
    total_allocated = sum(a.amount for a in payment.allocations)
    overpayment_amount = round_currency(payment.amount - total_allocated - payment.bank_charges)
    
    # Validate allocations don't exceed invoice balances
    for alloc in payment.allocations:
        if alloc.amount > 0:
            invoice = await invoices_collection.find_one({"invoice_id": alloc.invoice_id})
            if not invoice:
                raise HTTPException(status_code=400, detail=f"Invoice {alloc.invoice_id} not found")
            if alloc.amount > invoice.get("balance_due", 0) + 0.01:  # Small tolerance
                raise HTTPException(
                    status_code=400, 
                    detail=f"Allocation amount ₹{alloc.amount} exceeds balance due ₹{invoice.get('balance_due', 0)} for invoice {invoice.get('invoice_number')}"
                )
    
    # Build payment document
    payment_doc = {
        "payment_id": payment_id,
        "payment_number": payment_number,
        "customer_id": payment.customer_id,
        "customer_name": customer.get("name", ""),
        "payment_date": payment_date,
        "amount": round_currency(payment.amount),
        "payment_mode": payment.payment_mode,
        "deposit_to_account": payment.deposit_to_account,
        "reference_number": payment.reference_number,
        "bank_charges": round_currency(payment.bank_charges),
        "tax_deducted": payment.tax_deducted,
        "tax_account": payment.tax_account if payment.tax_deducted else "",
        "tax_amount": round_currency(payment.tax_amount) if payment.tax_deducted else 0,
        "notes": payment.notes,
        "allocations": [{"invoice_id": a.invoice_id, "amount": round_currency(a.amount)} for a in payment.allocations if a.amount > 0],
        "amount_allocated": round_currency(total_allocated),
        "overpayment_amount": max(0, overpayment_amount),
        "is_retainer": payment.is_retainer or len(payment.allocations) == 0,
        "status": "recorded",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await payments_collection.insert_one(payment_doc)
    
    # Update invoice statuses
    for alloc in payment.allocations:
        if alloc.amount > 0:
            await update_invoice_payment_status(alloc.invoice_id)
    
    # Create customer credit if overpayment
    if overpayment_amount > 0:
        credit_doc = {
            "credit_id": generate_id("CRD"),
            "customer_id": payment.customer_id,
            "customer_name": customer.get("name", ""),
            "source_type": "overpayment",
            "source_id": payment_id,
            "source_number": payment_number,
            "amount": round_currency(overpayment_amount),
            "original_amount": round_currency(overpayment_amount),
            "status": "available",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Overpayment from {payment_number}"
        }
        await customer_credits_collection.insert_one(credit_doc)
    
    # Handle retainer payment as credit
    if payment.is_retainer and total_allocated == 0:
        credit_doc = {
            "credit_id": generate_id("CRD"),
            "customer_id": payment.customer_id,
            "customer_name": customer.get("name", ""),
            "source_type": "retainer",
            "source_id": payment_id,
            "source_number": payment_number,
            "amount": round_currency(payment.amount - payment.bank_charges),
            "original_amount": round_currency(payment.amount - payment.bank_charges),
            "status": "available",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Retainer/Advance payment {payment_number}"
        }
        await customer_credits_collection.insert_one(credit_doc)
    
    # Update customer balance
    await update_customer_balance(payment.customer_id)
    
    # Add history
    await add_payment_history(payment_id, "created", f"Payment {payment_number} recorded for ₹{payment.amount:,.2f}")
    
    # Post journal entry for double-entry bookkeeping
    # Get org_id from one of the invoices
    org_id = None
    if payment.allocations:
        first_invoice = await invoices_collection.find_one({"invoice_id": payment.allocations[0].invoice_id})
        if first_invoice:
            org_id = first_invoice.get("organization_id")
    
    if org_id:
        try:
            await post_payment_received_journal_entry(
                organization_id=org_id,
                payment={
                    **payment_doc,
                    "customer_name": customer.get("name", ""),
                    "invoice_number": first_invoice.get("invoice_number", "") if payment.allocations else ""
                }
            )
        except Exception as e:
            import logging
            logging.warning(f"Failed to post journal entry for payment {payment_number}: {e}")
    
    # Send thank you email (mocked)
    if payment.send_thank_you:
        background_tasks.add_task(
            send_thank_you_email,
            customer.get("email", ""),
            customer.get("name", ""),
            payment_number,
            payment.amount
        )
    
    # Remove _id for response
    payment_doc.pop("_id", None)
    
    return {
        "code": 0,
        "message": "Payment recorded successfully",
        "payment": payment_doc,
        "overpayment_credited": overpayment_amount if overpayment_amount > 0 else None
    }

@router.get("/")
async def list_payments(
    customer_id: str = "",
    payment_type: str = "",  # invoice, retainer, all
    payment_mode: str = "",
    status: str = "",
    start_date: str = "",
    end_date: str = "",
    search: str = "",
    sort_by: str = "payment_date",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 50
):
    """List all payments with filters"""
    query = {}
    
    if customer_id:
        query["customer_id"] = customer_id
    if payment_type == "invoice":
        query["is_retainer"] = False
    elif payment_type == "retainer":
        query["is_retainer"] = True
    if payment_mode:
        query["payment_mode"] = payment_mode
    if status:
        query["status"] = status
    if start_date:
        query["payment_date"] = {"$gte": start_date}
    if end_date:
        if "payment_date" in query:
            query["payment_date"]["$lte"] = end_date
        else:
            query["payment_date"] = {"$lte": end_date}
    if search:
        query["$or"] = [
            {"payment_number": {"$regex": search, "$options": "i"}},
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"reference_number": {"$regex": search, "$options": "i"}}
        ]
    
    # Sorting
    sort_dir = -1 if sort_order == "desc" else 1
    
    # Count total
    total = await payments_collection.count_documents(query)
    
    # Get payments
    skip = (page - 1) * per_page
    payments = await payments_collection.find(query, {"_id": 0}).sort(sort_by, sort_dir).skip(skip).limit(per_page).to_list(per_page)
    
    # Get invoice numbers for display
    for payment in payments:
        invoice_numbers = []
        for alloc in payment.get("allocations", []):
            inv = await invoices_collection.find_one({"invoice_id": alloc.get("invoice_id")}, {"invoice_number": 1, "_id": 0})
            if inv:
                invoice_numbers.append(inv.get("invoice_number", ""))
        payment["invoice_numbers"] = invoice_numbers
    
    return {
        "code": 0,
        "payments": payments,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


# ==================== CREDITS MANAGEMENT (must be before /{payment_id}) ====================

@router.get("/credits")
async def list_all_credits(
    customer_id: str = "",
    status: str = "",
    page: int = 1,
    per_page: int = 50
):
    """List all customer credits"""
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status
    
    total = await customer_credits_collection.count_documents(query)
    skip = (page - 1) * per_page
    
    credits = await customer_credits_collection.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "code": 0,
        "credits": credits,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/credits/{customer_id}")
async def get_customer_credits_endpoint(customer_id: str):
    """Get all credits for a specific customer"""
    credits = await customer_credits_collection.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    available = [c for c in credits if c.get("status") == "available"]
    used = [c for c in credits if c.get("status") != "available"]
    
    return {
        "code": 0,
        "available_credits": available,
        "used_credits": used,
        "total_available": round_currency(sum(c.get("amount", 0) for c in available))
    }


# ==================== IMPORT/EXPORT (must be before /{payment_id}) ====================

@router.get("/export")
async def export_payments(
    format: str = "csv",
    start_date: str = "",
    end_date: str = "",
    customer_id: str = ""
):
    """Export payments to CSV"""
    query = {}
    if start_date:
        query["payment_date"] = {"$gte": start_date}
    if end_date:
        if "payment_date" in query:
            query["payment_date"]["$lte"] = end_date
        else:
            query["payment_date"] = {"$lte": end_date}
    if customer_id:
        query["customer_id"] = customer_id
    
    payments = await payments_collection.find(query, {"_id": 0}).to_list(10000)
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Payment Number", "Payment Date", "Customer Name", "Amount",
            "Payment Mode", "Reference Number", "Deposit Account", "Notes", "Status"
        ])
        
        # Data
        for p in payments:
            writer.writerow([
                p.get("payment_number", ""),
                p.get("payment_date", ""),
                p.get("customer_name", ""),
                p.get("amount", 0),
                p.get("payment_mode", ""),
                p.get("reference_number", ""),
                p.get("deposit_to_account", ""),
                p.get("notes", ""),
                p.get("status", "")
            ])
        
        return {
            "code": 0,
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"payments_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    
    return {"code": 0, "format": "json", "data": payments}

@router.get("/import/template")
async def get_import_template():
    """Get CSV template for importing payments"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Customer Name", "Payment Date", "Amount", "Payment Mode",
        "Reference Number", "Deposit Account", "Notes"
    ])
    
    # Sample row
    writer.writerow([
        "Sample Customer", "2026-01-15", "5000", "bank_transfer",
        "REF123", "Bank Account", "Sample payment"
    ])
    
    return {
        "code": 0,
        "template": output.getvalue(),
        "filename": "payments_import_template.csv"
    }

@router.post("/import")
async def import_payments(file: UploadFile = File(...)):
    """Import payments from CSV"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    content = await file.read()
    if len(content) > 1024 * 1024:  # 1MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 1MB limit")
    
    try:
        reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        imported = 0
        errors = []
        
        for row in reader:
            try:
                # Find customer
                customer_name = row.get("Customer Name", "").strip()
                customer = await contacts_collection.find_one({
                    "$or": [
                        {"name": {"$regex": f"^{customer_name}$", "$options": "i"}},
                        {"company_name": {"$regex": f"^{customer_name}$", "$options": "i"}}
                    ]
                })
                
                if not customer:
                    errors.append(f"Customer '{customer_name}' not found")
                    continue
                
                payment_id = generate_id("PAY")
                payment_number = await get_next_payment_number()
                
                payment_doc = {
                    "payment_id": payment_id,
                    "payment_number": payment_number,
                    "customer_id": customer.get("contact_id"),
                    "customer_name": customer.get("name", ""),
                    "payment_date": row.get("Payment Date", datetime.now().strftime("%Y-%m-%d")),
                    "amount": float(row.get("Amount", 0)),
                    "payment_mode": row.get("Payment Mode", "other").lower(),
                    "deposit_to_account": row.get("Deposit Account", "Undeposited Funds"),
                    "reference_number": row.get("Reference Number", ""),
                    "notes": row.get("Notes", ""),
                    "allocations": [],
                    "amount_allocated": 0,
                    "is_retainer": True,  # Imported as retainer, can be applied later
                    "status": "recorded",
                    "imported": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await payments_collection.insert_one(payment_doc)
                
                # Create as customer credit
                credit_doc = {
                    "credit_id": generate_id("CRD"),
                    "customer_id": customer.get("contact_id"),
                    "customer_name": customer.get("name", ""),
                    "source_type": "imported",
                    "source_id": payment_id,
                    "source_number": payment_number,
                    "amount": float(row.get("Amount", 0)),
                    "original_amount": float(row.get("Amount", 0)),
                    "status": "available",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await customer_credits_collection.insert_one(credit_doc)
                
                imported += 1
                
            except Exception as e:
                errors.append(f"Row error: {str(e)}")
        
        return {
            "code": 0,
            "message": f"Import completed: {imported} payments imported",
            "imported": imported,
            "errors": errors[:10]  # Return first 10 errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

@router.post("/bulk-action")
async def bulk_payment_action(request: BulkActionRequest):
    """Perform bulk action on payments"""
    if not request.payment_ids:
        raise HTTPException(status_code=400, detail="No payments selected")
    
    if request.action == "delete":
        deleted = 0
        for payment_id in request.payment_ids:
            try:
                payment = await payments_collection.find_one({"payment_id": payment_id})
                if payment:
                    customer_id = payment.get("customer_id")
                    
                    # Delete payment
                    await payments_collection.delete_one({"payment_id": payment_id})
                    
                    # Update invoice statuses
                    for alloc in payment.get("allocations", []):
                        await update_invoice_payment_status(alloc.get("invoice_id"))
                    
                    # Delete credits
                    await customer_credits_collection.delete_many({"source_id": payment_id})
                    
                    # Update customer balance
                    await update_customer_balance(customer_id)
                    
                    deleted += 1
            except Exception:
                pass
        
        return {"code": 0, "message": f"{deleted} payments deleted"}
    
    elif request.action == "export":
        payments = await payments_collection.find(
            {"payment_id": {"$in": request.payment_ids}},
            {"_id": 0}
        ).to_list(len(request.payment_ids))
        
        return {"code": 0, "payments": payments}
    
    raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")


@router.get("/{payment_id}")
async def get_payment(payment_id: str):
    """Get payment details"""
    payment = await payments_collection.find_one({"payment_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get invoice details for allocations
    invoice_details = []
    for alloc in payment.get("allocations", []):
        invoice = await invoices_collection.find_one(
            {"invoice_id": alloc.get("invoice_id")},
            {"_id": 0, "invoice_id": 1, "invoice_number": 1, "date": 1, "grand_total": 1, "balance_due": 1}
        )
        if invoice:
            invoice_details.append({
                **invoice,
                "amount_applied": alloc.get("amount", 0)
            })
    
    # Get payment history
    history = await payment_history_collection.find(
        {"payment_id": payment_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    
    # Get customer details
    customer = await contacts_collection.find_one(
        {"contact_id": payment.get("customer_id")},
        {"_id": 0, "contact_id": 1, "name": 1, "email": 1, "company_name": 1}
    )
    
    return {
        "code": 0,
        "payment": payment,
        "invoice_details": invoice_details,
        "customer": customer,
        "history": history
    }

@router.put("/{payment_id}")
async def update_payment(payment_id: str, update: PaymentUpdate):
    """Update payment details (limited fields)"""
    payment = await payments_collection.find_one({"payment_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await payments_collection.update_one(
        {"payment_id": payment_id},
        {"$set": update_data}
    )
    
    await add_payment_history(payment_id, "updated", "Payment details updated")
    
    updated = await payments_collection.find_one({"payment_id": payment_id}, {"_id": 0})
    
    return {"code": 0, "message": "Payment updated", "payment": updated}

@router.delete("/{payment_id}")
async def delete_payment(payment_id: str):
    """Delete a payment and reverse its effects"""
    payment = await payments_collection.find_one({"payment_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    customer_id = payment.get("customer_id")
    
    # Delete payment
    await payments_collection.delete_one({"payment_id": payment_id})
    
    # Update invoice statuses
    for alloc in payment.get("allocations", []):
        await update_invoice_payment_status(alloc.get("invoice_id"))
    
    # Delete associated credits
    await customer_credits_collection.delete_many({"source_id": payment_id})
    
    # Update customer balance
    await update_customer_balance(customer_id)
    
    # Add history
    await add_payment_history(payment_id, "deleted", f"Payment {payment.get('payment_number')} deleted")
    
    return {"code": 0, "message": "Payment deleted successfully"}


# ==================== REFUNDS ====================

@router.post("/{payment_id}/refund")
async def refund_payment(payment_id: str, refund: RefundCreate):
    """Refund overpayment or credit"""
    payment = await payments_collection.find_one({"payment_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check available credit
    credits = await customer_credits_collection.find({
        "source_id": payment_id,
        "status": "available"
    }).to_list(10)
    
    available_credit = sum(c.get("amount", 0) for c in credits)
    
    if refund.amount > available_credit:
        raise HTTPException(
            status_code=400,
            detail=f"Refund amount ₹{refund.amount} exceeds available credit ₹{available_credit}"
        )
    
    refund_id = generate_id("REF")
    refund_date = refund.refund_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Create refund record
    refund_doc = {
        "refund_id": refund_id,
        "payment_id": payment_id,
        "payment_number": payment.get("payment_number"),
        "customer_id": payment.get("customer_id"),
        "customer_name": payment.get("customer_name"),
        "amount": round_currency(refund.amount),
        "refund_date": refund_date,
        "payment_mode": refund.payment_mode,
        "reference_number": refund.reference_number,
        "notes": refund.notes,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["payment_refunds"].insert_one(refund_doc)
    
    # Reduce credit
    remaining_to_deduct = refund.amount
    for credit in credits:
        if remaining_to_deduct <= 0:
            break
        
        credit_amount = credit.get("amount", 0)
        if credit_amount <= remaining_to_deduct:
            # Use entire credit
            await customer_credits_collection.update_one(
                {"credit_id": credit.get("credit_id")},
                {"$set": {"status": "refunded", "amount": 0}}
            )
            remaining_to_deduct -= credit_amount
        else:
            # Partial use
            await customer_credits_collection.update_one(
                {"credit_id": credit.get("credit_id")},
                {"$set": {"amount": round_currency(credit_amount - remaining_to_deduct)}}
            )
            remaining_to_deduct = 0
    
    # Update payment
    await payments_collection.update_one(
        {"payment_id": payment_id},
        {"$set": {
            "has_refund": True,
            "refund_amount": round_currency(payment.get("refund_amount", 0) + refund.amount)
        }}
    )
    
    # Update customer balance
    await update_customer_balance(payment.get("customer_id"))
    
    await add_payment_history(payment_id, "refunded", f"Refund of ₹{refund.amount:,.2f} processed")
    
    refund_doc.pop("_id", None)
    
    return {"code": 0, "message": "Refund processed", "refund": refund_doc}

@router.get("/{payment_id}/refunds")
async def get_payment_refunds(payment_id: str):
    """Get all refunds for a payment"""
    refunds = await db["payment_refunds"].find(
        {"payment_id": payment_id},
        {"_id": 0}
    ).to_list(100)
    
    return {"code": 0, "refunds": refunds}


# ==================== APPLY CREDIT TO INVOICE ====================

class ApplyCreditRequest(BaseModel):
    """Request to apply credit to invoice"""
    credit_id: str
    invoice_id: str
    amount: float

@router.post("/apply-credit")
async def apply_credit_to_invoice(request: ApplyCreditRequest):
    """Apply customer credit to an invoice"""
    credit_id = request.credit_id
    invoice_id = request.invoice_id
    amount = request.amount
    
    credit = await customer_credits_collection.find_one({"credit_id": credit_id})
    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")
    
    if credit.get("status") != "available":
        raise HTTPException(status_code=400, detail="Credit is not available")
    
    if amount > credit.get("amount", 0):
        raise HTTPException(status_code=400, detail=f"Amount exceeds available credit ₹{credit.get('amount', 0)}")
    
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if amount > invoice.get("balance_due", 0):
        raise HTTPException(status_code=400, detail=f"Amount exceeds invoice balance ₹{invoice.get('balance_due', 0)}")
    
    # Create credit application record
    application_doc = {
        "application_id": generate_id("CRA"),
        "credit_id": credit_id,
        "invoice_id": invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "customer_id": credit.get("customer_id"),
        "amount": round_currency(amount),
        "applied_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["credit_applications"].insert_one(application_doc)
    
    # Update credit
    new_credit_amount = round_currency(credit.get("amount", 0) - amount)
    if new_credit_amount <= 0:
        await customer_credits_collection.update_one(
            {"credit_id": credit_id},
            {"$set": {"status": "applied", "amount": 0}}
        )
    else:
        await customer_credits_collection.update_one(
            {"credit_id": credit_id},
            {"$set": {"amount": new_credit_amount}}
        )
    
    # Update invoice
    new_balance = round_currency(invoice.get("balance_due", 0) - amount)
    new_amount_paid = round_currency(invoice.get("amount_paid", 0) + amount)
    new_status = "paid" if new_balance <= 0 else "partially_paid"
    
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "balance_due": new_balance,
            "amount_paid": new_amount_paid,
            "credits_applied": round_currency(invoice.get("credits_applied", 0) + amount),
            "status": new_status
        }}
    )
    
    # Update customer balance
    await update_customer_balance(credit.get("customer_id"))
    
    return {
        "code": 0,
        "message": f"Credit of ₹{amount:,.2f} applied to invoice {invoice.get('invoice_number')}",
        "new_credit_balance": new_credit_amount,
        "new_invoice_balance": new_balance
    }


# ==================== THANK YOU EMAIL ====================

def send_thank_you_email(email: str, name: str, payment_number: str, amount: float):
    """Send thank you email (mocked)"""
    print(f"[MOCK EMAIL] Thank you email to {email}")
    print(f"  Subject: Thank you for your payment - {payment_number}")
    print(f"  Body: Dear {name}, Thank you for your payment of ₹{amount:,.2f}.")


# ==================== ATTACHMENTS ====================

@router.post("/{payment_id}/attachments")
async def add_payment_attachment(payment_id: str, file: UploadFile = File(...)):
    """Add attachment to payment"""
    payment = await payments_collection.find_one({"payment_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check file size (10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB")
    
    # Check attachment count
    attachments = payment.get("attachments", [])
    if len(attachments) >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 attachments allowed")
    
    import base64
    attachment = {
        "attachment_id": generate_id("ATT"),
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "data": base64.b64encode(content).decode('utf-8'),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await payments_collection.update_one(
        {"payment_id": payment_id},
        {"$push": {"attachments": attachment}}
    )
    
    return {"code": 0, "message": "Attachment added", "attachment_id": attachment["attachment_id"]}

@router.delete("/{payment_id}/attachments/{attachment_id}")
async def delete_payment_attachment(payment_id: str, attachment_id: str):
    """Delete attachment from payment"""
    result = await payments_collection.update_one(
        {"payment_id": payment_id},
        {"$pull": {"attachments": {"attachment_id": attachment_id}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    return {"code": 0, "message": "Attachment deleted"}


# ==================== PAYMENT RECEIPT PDF ====================

@router.get("/{payment_id}/receipt-pdf")
async def get_payment_receipt_pdf(payment_id: str):
    """Generate payment receipt PDF"""
    from io import BytesIO
    
    payment = await payments_collection.find_one({"payment_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get customer details
    customer = await contacts_collection.find_one(
        {"contact_id": payment.get("customer_id")},
        {"_id": 0, "display_name": 1, "company_name": 1, "billing_address": 1, "email": 1}
    ) or {}
    
    # Get organization settings
    org_settings = await db["organization_settings"].find_one({}, {"_id": 0}) or {}
    
    # Generate HTML for receipt
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            .receipt {{ max-width: 800px; margin: 0 auto; border: 1px solid #ddd; padding: 40px; }}
            .header {{ display: flex; justify-content: space-between; margin-bottom: 30px; border-bottom: 3px solid #22EDA9; padding-bottom: 20px; }}
            .company {{ font-size: 24px; font-weight: bold; color: #1a1a1a; }}
            .receipt-title {{ font-size: 28px; color: #22EDA9; text-align: right; }}
            .receipt-number {{ font-size: 14px; color: #666; }}
            .section {{ margin-bottom: 25px; }}
            .label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
            .value {{ font-size: 14px; }}
            .amount-box {{ background: #f8f8f8; padding: 20px; text-align: center; margin-top: 30px; }}
            .amount-label {{ font-size: 14px; color: #666; margin-bottom: 10px; }}
            .amount {{ font-size: 36px; font-weight: bold; color: #22EDA9; }}
            .details-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
            .details-table th {{ background: #f8f9fa; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
            .footer {{ margin-top: 40px; text-align: center; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="receipt">
            <div class="header">
                <div>
                    <div class="company">{org_settings.get('company_name', 'Battwheels OS')}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        {org_settings.get('address', '')}<br>
                        {org_settings.get('phone', '')} | {org_settings.get('email', '')}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="receipt-title">PAYMENT RECEIPT</div>
                    <div class="receipt-number">#{payment.get('payment_number', payment_id)}</div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between;">
                <div class="section">
                    <div class="label">Received From</div>
                    <div class="value" style="font-weight: bold;">{customer.get('display_name', payment.get('customer_name', 'N/A'))}</div>
                    <div class="value" style="font-size: 12px; color: #666;">{customer.get('billing_address', {}).get('street', '')}</div>
                </div>
                <div class="section" style="text-align: right;">
                    <div class="label">Payment Date</div>
                    <div class="value">{payment.get('payment_date', '')}</div>
                    <div class="label" style="margin-top: 15px;">Payment Mode</div>
                    <div class="value">{payment.get('payment_mode', 'N/A').replace('_', ' ').title()}</div>
                </div>
            </div>
            
            <div class="amount-box">
                <div class="amount-label">Amount Received</div>
                <div class="amount">₹{payment.get('amount', 0):,.2f}</div>
            </div>
            
            <table class="details-table">
                <thead>
                    <tr>
                        <th>Invoice #</th>
                        <th style="text-align: right;">Invoice Amount</th>
                        <th style="text-align: right;">Payment Applied</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add invoice allocations
    allocations = payment.get("allocations", [])
    if allocations:
        for alloc in allocations:
            html_content += f"""
                    <tr>
                        <td>{alloc.get('invoice_number', alloc.get('invoice_id', 'N/A'))}</td>
                        <td style="text-align: right;">₹{alloc.get('invoice_amount', 0):,.2f}</td>
                        <td style="text-align: right;">₹{alloc.get('amount', 0):,.2f}</td>
                    </tr>
            """
    else:
        html_content += """
                    <tr>
                        <td colspan="3" style="text-align: center; color: #888;">Unapplied Payment</td>
                    </tr>
        """
    
    html_content += f"""
                </tbody>
            </table>
            
            <div style="margin-top: 20px;">
                <div class="label">Reference Number</div>
                <div class="value">{payment.get('reference_number', 'N/A')}</div>
            </div>
            
            {f'<div style="margin-top: 15px;"><div class="label">Notes</div><div class="value">{payment.get("notes", "")}</div></div>' if payment.get('notes') else ''}
            
            <div class="footer">
                <p>Thank you for your payment!</p>
                <p>Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        from weasyprint import HTML
        from fastapi.responses import StreamingResponse
        
        pdf_buffer = BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Receipt_{payment.get('payment_number', payment_id)}.pdf"
            }
        )
    except Exception as e:
        # Return HTML if WeasyPrint not available
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

# ==================== ACTIVITY LOG ====================

@router.get("/{payment_id}/activity")
async def get_payment_activity(payment_id: str, limit: int = 50):
    """Get activity log for a payment"""
    payment = await payments_collection.find_one({"payment_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get from history collection
    history = await payment_history_collection.find(
        {"payment_id": payment_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # If no history, create basic activity from payment data
    if not history:
        history = [
            {
                "action": "created",
                "details": f"Payment of ₹{payment.get('amount', 0):,.2f} recorded",
                "timestamp": payment.get("created_at", payment.get("payment_date", ""))
            }
        ]
        
        if payment.get("allocations"):
            for alloc in payment.get("allocations", []):
                history.append({
                    "action": "applied",
                    "details": f"₹{alloc.get('amount', 0):,.2f} applied to {alloc.get('invoice_number', 'invoice')}",
                    "timestamp": payment.get("created_at", "")
                })
    
    return {"code": 0, "activities": history}

# ==================== HISTORY HELPER ====================

async def add_payment_history(payment_id: str, action: str, details: str):
    """Add entry to payment history"""
    await payment_history_collection.insert_one({
        "history_id": generate_id("HIST"),
        "payment_id": payment_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
