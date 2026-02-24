"""
Invoice Automation - Payment Reminders, Late Fees, Auto Credit Application
Phase 2 & 3 Automation Features
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio
import os
from fastapi import Request
from utils.database import extract_org_id, org_query


MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/invoice-automation", tags=["Invoice Automation"])

invoices_collection = db["invoices_enhanced"]
contacts_collection = db["contacts_enhanced"]
customer_credits_collection = db["customer_credits"]
reminder_settings_collection = db["reminder_settings"]
reminder_history_collection = db["reminder_history"]
late_fee_settings_collection = db["late_fee_settings"]


# ==================== MODELS ====================

class ReminderSettings(BaseModel):
    """Payment reminder settings"""
    enabled: bool = True
    reminder_before_days: List[int] = [7, 3, 1]  # Days before due date
    reminder_after_days: List[int] = [1, 7, 14, 30]  # Days after due date
    email_template: str = "default"
    include_payment_link: bool = True

class LateFeeSettings(BaseModel):
    """Late fee calculation settings"""
    enabled: bool = False
    fee_type: str = "percentage"  # percentage, fixed
    fee_value: float = 2.0  # 2% or fixed amount
    grace_period_days: int = 0
    max_fee_percentage: float = 10.0  # Cap at 10%
    apply_automatically: bool = False

class AutoCreditSettings(BaseModel):
    """Auto credit application settings"""
    enabled: bool = True
    apply_on_invoice_creation: bool = True
    apply_on_invoice_send: bool = False


# ==================== SETTINGS ENDPOINTS ====================

@router.get("/reminder-settings")
async def get_reminder_settings(request: Request):
    org_id = extract_org_id(request)
    """Get payment reminder settings"""
    settings = await reminder_settings_collection.find_one({"type": "reminder"}, {"_id": 0})
    if not settings:
        settings = ReminderSettings().dict()
    return {"code": 0, "settings": settings}

@router.put("/reminder-settings")
async def update_reminder_settings(settings: ReminderSettings, request: Request):
    org_id = extract_org_id(request)
    """Update payment reminder settings"""
    await reminder_settings_collection.update_one(
        {"type": "reminder"},
        {"$set": {**settings.dict(), "type": "reminder", "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"code": 0, "message": "Reminder settings updated"}

@router.get("/late-fee-settings")
async def get_late_fee_settings(request: Request):
    org_id = extract_org_id(request)
    """Get late fee settings"""
    settings = await late_fee_settings_collection.find_one({"type": "late_fee"}, {"_id": 0})
    if not settings:
        settings = LateFeeSettings().dict()
    return {"code": 0, "settings": settings}

@router.put("/late-fee-settings")
async def update_late_fee_settings(settings: LateFeeSettings, request: Request):
    org_id = extract_org_id(request)
    """Update late fee settings"""
    await late_fee_settings_collection.update_one(
        {"type": "late_fee"},
        {"$set": {**settings.dict(), "type": "late_fee", "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"code": 0, "message": "Late fee settings updated"}


# ==================== REMINDER FUNCTIONS ====================

@router.get("/overdue-invoices")
async def get_overdue_invoices(request: Request):
    org_id = extract_org_id(request)
    """Get all overdue invoices"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    invoices = await invoices_collection.find({
        "status": {"$in": ["sent", "partially_paid"]},
        "due_date": {"$lt": today},
        "balance_due": {"$gt": 0}
    }, {"_id": 0}).to_list(1000)
    
    # Calculate days overdue
    for inv in invoices:
        due_date = datetime.strptime(inv.get("due_date", today), "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        inv["days_overdue"] = (today_dt - due_date).days
    
    return {
        "code": 0,
        "overdue_invoices": invoices,
        "total_count": len(invoices),
        "total_overdue_amount": sum(inv.get("balance_due", 0) for inv in invoices)
    }

@router.get("/due-soon-invoices")
async def get_due_soon_invoices(days: int = 7, request: Request):
    org_id = extract_org_id(request)
    """Get invoices due within specified days"""
    today = datetime.now(timezone.utc)
    future_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    
    invoices = await invoices_collection.find({
        "status": {"$in": ["sent", "partially_paid"]},
        "due_date": {"$gte": today_str, "$lte": future_date},
        "balance_due": {"$gt": 0}
    }, {"_id": 0}).to_list(1000)
    
    # Calculate days until due
    for inv in invoices:
        due_date = datetime.strptime(inv.get("due_date", today_str), "%Y-%m-%d")
        today_dt = datetime.strptime(today_str, "%Y-%m-%d")
        inv["days_until_due"] = (due_date - today_dt).days
    
    return {
        "code": 0,
        "due_soon_invoices": invoices,
        "total_count": len(invoices),
        "total_amount": sum(inv.get("balance_due", 0) for inv in invoices)
    }

@router.post("/send-reminder/{invoice_id}")
async def send_payment_reminder(invoice_id: str, background_tasks: BackgroundTasks, request: Request):
    org_id = extract_org_id(request)
    """Send payment reminder for a specific invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("balance_due", 0) <= 0:
        raise HTTPException(status_code=400, detail="Invoice has no balance due")
    
    # Get customer email
    customer = await contacts_collection.find_one({"contact_id": invoice.get("customer_id")})
    email = customer.get("email") if customer else invoice.get("customer_email")
    
    if not email:
        raise HTTPException(status_code=400, detail="No email address found for customer")
    
    # Log reminder (mocked email)
    reminder_doc = {
        "invoice_id": invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "customer_id": invoice.get("customer_id"),
        "customer_name": invoice.get("customer_name"),
        "email": email,
        "amount_due": invoice.get("balance_due"),
        "due_date": invoice.get("due_date"),
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "reminder_type": "manual"
    }
    
    await reminder_history_collection.insert_one(reminder_doc)
    
    # Update invoice
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "last_reminder_sent": datetime.now(timezone.utc).isoformat(),
            "reminder_count": (invoice.get("reminder_count", 0) or 0) + 1
        }}
    )
    
    # Mock email sending
    print(f"[MOCK EMAIL] Payment Reminder to {email}")
    print(f"  Subject: Payment Reminder - Invoice {invoice.get('invoice_number')}")
    print(f"  Amount Due: ₹{invoice.get('balance_due'):,.2f}")
    print(f"  Due Date: {invoice.get('due_date')}")
    
    return {
        "code": 0,
        "message": f"Payment reminder sent to {email}",
        "invoice_number": invoice.get("invoice_number")
    }

@router.post("/send-bulk-reminders")
async def send_bulk_reminders(invoice_ids: List[str], background_tasks: BackgroundTasks, request: Request):
    org_id = extract_org_id(request)
    """Send payment reminders for multiple invoices"""
    sent = 0
    failed = 0
    errors = []
    
    for invoice_id in invoice_ids:
        try:
            invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
            if not invoice or invoice.get("balance_due", 0) <= 0:
                continue
            
            customer = await contacts_collection.find_one({"contact_id": invoice.get("customer_id")})
            email = customer.get("email") if customer else invoice.get("customer_email")
            
            if not email:
                errors.append(f"{invoice.get('invoice_number')}: No email")
                failed += 1
                continue
            
            # Log reminder
            reminder_doc = {
                "invoice_id": invoice_id,
                "invoice_number": invoice.get("invoice_number"),
                "customer_id": invoice.get("customer_id"),
                "email": email,
                "amount_due": invoice.get("balance_due"),
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "reminder_type": "bulk"
            }
            await reminder_history_collection.insert_one(reminder_doc)
            
            # Update invoice
            await invoices_collection.update_one(
                {"invoice_id": invoice_id},
                {"$set": {
                    "last_reminder_sent": datetime.now(timezone.utc).isoformat(),
                    "reminder_count": (invoice.get("reminder_count", 0) or 0) + 1
                }}
            )
            
            sent += 1
            
        except Exception as e:
            failed += 1
            errors.append(str(e))
    
    return {
        "code": 0,
        "message": f"Sent {sent} reminders, {failed} failed",
        "sent": sent,
        "failed": failed,
        "errors": errors[:5]
    }

@router.get("/reminder-history")
async def get_reminder_history(invoice_id: str = "", customer_id: str = "", limit: int = 50, request: Request):
    org_id = extract_org_id(request)
    """Get reminder history"""
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if customer_id:
        query["customer_id"] = customer_id
    
    history = await reminder_history_collection.find(query, {"_id": 0}).sort("sent_at", -1).limit(limit).to_list(limit)
    
    return {"code": 0, "history": history}


# ==================== LATE FEE FUNCTIONS ====================

@router.get("/calculate-late-fee/{invoice_id}")
async def calculate_late_fee(invoice_id: str, request: Request):
    org_id = extract_org_id(request)
    """Calculate late fee for an invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    settings = await late_fee_settings_collection.find_one({"type": "late_fee"})
    if not settings or not settings.get("enabled"):
        return {"code": 0, "late_fee": 0, "message": "Late fees not enabled"}
    
    # Check if overdue
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_date = invoice.get("due_date", today)
    
    if due_date >= today:
        return {"code": 0, "late_fee": 0, "message": "Invoice not overdue"}
    
    # Calculate days overdue (minus grace period)
    due_dt = datetime.strptime(due_date, "%Y-%m-%d")
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    days_overdue = (today_dt - due_dt).days - settings.get("grace_period_days", 0)
    
    if days_overdue <= 0:
        return {"code": 0, "late_fee": 0, "message": "Within grace period"}
    
    balance_due = invoice.get("balance_due", 0)
    
    if settings.get("fee_type") == "percentage":
        fee_rate = settings.get("fee_value", 0)
        late_fee = balance_due * (fee_rate / 100)
        
        # Cap at max percentage
        max_fee = balance_due * (settings.get("max_fee_percentage", 10) / 100)
        late_fee = min(late_fee, max_fee)
    else:
        late_fee = settings.get("fee_value", 0)
    
    return {
        "code": 0,
        "late_fee": round(late_fee, 2),
        "days_overdue": days_overdue,
        "balance_due": balance_due,
        "fee_type": settings.get("fee_type"),
        "fee_rate": settings.get("fee_value")
    }

@router.post("/apply-late-fee/{invoice_id}")
async def apply_late_fee(invoice_id: str, request: Request):
    org_id = extract_org_id(request)
    """Apply late fee to an invoice"""
    # Calculate fee
    fee_result = await calculate_late_fee(invoice_id)
    late_fee = fee_result.get("late_fee", 0)
    
    if late_fee <= 0:
        return {"code": 0, "message": "No late fee to apply"}
    
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    
    # Update invoice with late fee
    current_fees = invoice.get("late_fees_applied", 0)
    new_balance = invoice.get("balance_due", 0) + late_fee
    
    await invoices_collection.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "late_fees_applied": round(current_fees + late_fee, 2),
            "balance_due": round(new_balance, 2),
            "grand_total": round(invoice.get("grand_total", 0) + late_fee, 2),
            "late_fee_applied_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "code": 0,
        "message": f"Late fee of ₹{late_fee:,.2f} applied",
        "late_fee": late_fee,
        "new_balance": new_balance
    }


# ==================== AUTO CREDIT APPLICATION ====================

@router.post("/auto-apply-credits/{invoice_id}")
async def auto_apply_credits(invoice_id: str, request: Request):
    org_id = extract_org_id(request)
    """Automatically apply available customer credits to an invoice"""
    invoice = await invoices_collection.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    balance_due = invoice.get("balance_due", 0)
    if balance_due <= 0:
        return {"code": 0, "message": "Invoice has no balance due", "applied": 0}
    
    customer_id = invoice.get("customer_id")
    
    # Get available credits
    credits = await customer_credits_collection.find({
        "customer_id": customer_id,
        "status": "available"
    }).to_list(100)
    
    if not credits:
        return {"code": 0, "message": "No credits available", "applied": 0}
    
    total_applied = 0
    
    for credit in credits:
        if balance_due <= 0:
            break
        
        credit_amount = credit.get("amount", 0)
        apply_amount = min(credit_amount, balance_due)
        
        # Apply credit
        if apply_amount > 0:
            # Update credit
            new_credit_amount = credit_amount - apply_amount
            if new_credit_amount <= 0:
                await customer_credits_collection.update_one(
                    {"credit_id": credit.get("credit_id")},
                    {"$set": {"status": "applied", "amount": 0}}
                )
            else:
                await customer_credits_collection.update_one(
                    {"credit_id": credit.get("credit_id")},
                    {"$set": {"amount": round(new_credit_amount, 2)}}
                )
            
            # Log application
            await db["credit_applications"].insert_one({
                "credit_id": credit.get("credit_id"),
                "invoice_id": invoice_id,
                "amount": apply_amount,
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "auto_applied": True
            })
            
            total_applied += apply_amount
            balance_due -= apply_amount
    
    # Update invoice
    if total_applied > 0:
        new_balance = invoice.get("balance_due", 0) - total_applied
        new_paid = invoice.get("amount_paid", 0) + total_applied
        new_status = "paid" if new_balance <= 0 else "partially_paid"
        
        await invoices_collection.update_one(
            {"invoice_id": invoice_id},
            {"$set": {
                "balance_due": round(new_balance, 2),
                "amount_paid": round(new_paid, 2),
                "credits_applied": round(invoice.get("credits_applied", 0) + total_applied, 2),
                "status": new_status
            }}
        )
    
    return {
        "code": 0,
        "message": f"Applied ₹{total_applied:,.2f} in credits",
        "applied": total_applied,
        "new_balance": round(invoice.get("balance_due", 0) - total_applied, 2)
    }


# ==================== AGING REPORT ====================

@router.get("/aging-report")
async def get_aging_report(request: Request):
    org_id = extract_org_id(request)
    """Get accounts receivable aging report"""
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")
    
    # Define aging buckets
    buckets = {
        "current": {"label": "Current", "min": 0, "max": 0, "amount": 0, "count": 0},
        "1_30": {"label": "1-30 Days", "min": 1, "max": 30, "amount": 0, "count": 0},
        "31_60": {"label": "31-60 Days", "min": 31, "max": 60, "amount": 0, "count": 0},
        "61_90": {"label": "61-90 Days", "min": 61, "max": 90, "amount": 0, "count": 0},
        "over_90": {"label": "Over 90 Days", "min": 91, "max": 9999, "amount": 0, "count": 0}
    }
    
    # Get all unpaid invoices
    invoices = await invoices_collection.find({
        "status": {"$in": ["sent", "partially_paid", "overdue"]},
        "balance_due": {"$gt": 0}
    }, {"_id": 0}).to_list(10000)
    
    customer_aging = {}
    
    for inv in invoices:
        due_date = inv.get("due_date", today_str)
        balance = inv.get("balance_due", 0)
        customer_id = inv.get("customer_id")
        customer_name = inv.get("customer_name", "")
        
        # Calculate days overdue
        due_dt = datetime.strptime(due_date, "%Y-%m-%d")
        today_dt = datetime.strptime(today_str, "%Y-%m-%d")
        days_overdue = max(0, (today_dt - due_dt).days)
        
        # Assign to bucket
        if days_overdue == 0:
            bucket = "current"
        elif days_overdue <= 30:
            bucket = "1_30"
        elif days_overdue <= 60:
            bucket = "31_60"
        elif days_overdue <= 90:
            bucket = "61_90"
        else:
            bucket = "over_90"
        
        buckets[bucket]["amount"] += balance
        buckets[bucket]["count"] += 1
        
        # Track by customer
        if customer_id not in customer_aging:
            customer_aging[customer_id] = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "total": 0,
                "current": 0,
                "1_30": 0,
                "31_60": 0,
                "61_90": 0,
                "over_90": 0
            }
        
        customer_aging[customer_id]["total"] += balance
        customer_aging[customer_id][bucket] += balance
    
    # Sort customers by total outstanding
    customer_list = sorted(customer_aging.values(), key=lambda x: x["total"], reverse=True)
    
    return {
        "code": 0,
        "aging_buckets": list(buckets.values()),
        "total_receivable": sum(b["amount"] for b in buckets.values()),
        "customer_aging": customer_list[:50],  # Top 50 customers
        "as_of_date": today_str
    }
