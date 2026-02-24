"""
Recurring Invoices Module - Zoho-Style Automated Invoice Generation
Creates invoices on a schedule (daily, weekly, monthly, yearly)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import motor.motor_asyncio
import os
import uuid
import logging
from fastapi import Request
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

router = APIRouter(prefix="/recurring-invoices", tags=["Recurring Invoices"])

# Collections - Use main collections with Zoho-synced data
recurring_collection = db["recurring_invoices"]
invoices_collection = db["invoices"]
contacts_collection = db["contacts"]


# ==================== MODELS ====================

class LineItem(BaseModel):
    """Line item for recurring invoice"""
    item_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    quantity: float = 1
    rate: float
    tax_percentage: float = 18.0
    hsn_code: Optional[str] = None


class RecurringInvoiceCreate(BaseModel):
    """Create recurring invoice profile"""
    customer_id: str
    profile_name: str
    frequency: str = "monthly"  # daily, weekly, monthly, yearly, custom
    repeat_every: int = 1  # Every X periods
    start_date: str  # YYYY-MM-DD
    end_date: Optional[str] = None  # None = never expires
    line_items: List[LineItem]
    payment_terms_days: int = 15
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    send_email_on_generation: bool = True
    auto_charge: bool = False


class RecurringInvoiceUpdate(BaseModel):
    """Update recurring invoice profile"""
    profile_name: Optional[str] = None
    frequency: Optional[str] = None
    repeat_every: Optional[int] = None
    end_date: Optional[str] = None
    line_items: Optional[List[LineItem]] = None
    payment_terms_days: Optional[int] = None
    notes: Optional[str] = None
    send_email_on_generation: Optional[bool] = None
    status: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

def calculate_next_date(current_date: datetime, frequency: str, repeat_every: int) -> datetime:
    """Calculate next occurrence date based on frequency"""
    if frequency == "daily":
        return current_date + timedelta(days=repeat_every)
    elif frequency == "weekly":
        return current_date + timedelta(weeks=repeat_every)
    elif frequency == "monthly":
        return current_date + relativedelta(months=repeat_every)
    elif frequency == "yearly":
        return current_date + relativedelta(years=repeat_every)
    else:
        return current_date + relativedelta(months=repeat_every)


async def generate_invoice_number():
    """Generate sequential invoice number"""
    count = await invoices_collection.count_documents(org_query(org_id))
    return f"INV-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"


async def create_invoice_from_recurring(recurring: dict) -> dict:
    """Generate an invoice from recurring profile"""
    customer = await contacts_collection.find_one(
        {"contact_id": recurring["customer_id"]}, {"_id": 0}
    )
    if not customer:
        raise ValueError(f"Customer {recurring['customer_id']} not found")

    # Calculate totals
    line_items = recurring.get("line_items", [])
    subtotal = sum(item["quantity"] * item["rate"] for item in line_items)
    tax_amount = sum(
        item["quantity"] * item["rate"] * (item.get("tax_percentage", 18) / 100)
        for item in line_items
    )
    grand_total = subtotal + tax_amount

    # Calculate due date
    invoice_date = datetime.now(timezone.utc)
    due_date = invoice_date + timedelta(days=recurring.get("payment_terms_days", 15))

    invoice_number = await generate_invoice_number()

    invoice = {
        "invoice_id": f"INV-{uuid.uuid4().hex[:12].upper()}",
        "invoice_number": invoice_number,
        "recurring_invoice_id": recurring["recurring_id"],
        "customer_id": recurring["customer_id"],
        "customer_name": customer.get("display_name", customer.get("contact_name", "")),
        "customer_email": customer.get("email"),
        "invoice_date": invoice_date.strftime("%Y-%m-%d"),
        "due_date": due_date.strftime("%Y-%m-%d"),
        "line_items": line_items,
        "subtotal": round(subtotal, 2),
        "tax_amount": round(tax_amount, 2),
        "grand_total": round(grand_total, 2),
        "balance_due": round(grand_total, 2),
        "amount_paid": 0,
        "status": "draft",
        "notes": recurring.get("notes"),
        "terms_conditions": recurring.get("terms_conditions"),
        "source": "recurring",
        "created_at": invoice_date.isoformat(),
        "updated_at": invoice_date.isoformat()
    }

    await invoices_collection.insert_one(invoice)
    return invoice


# ==================== API ENDPOINTS ====================

@router.post("")
async def create_recurring_invoice(data: RecurringInvoiceCreate, request: Request):
    org_id = extract_org_id(request)
    """Create a new recurring invoice profile"""
    # Validate customer exists
    customer = await contacts_collection.find_one(
        {"contact_id": data.customer_id}, {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Validate start date format
    try:
        datetime.strptime(data.start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid start_date format (use YYYY-MM-DD)")

    recurring = {
        "recurring_id": f"RI-{uuid.uuid4().hex[:12].upper()}",
        "customer_id": data.customer_id,
        "customer_name": customer.get("display_name", customer.get("contact_name", "")),
        "profile_name": data.profile_name,
        "frequency": data.frequency,
        "repeat_every": data.repeat_every,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "next_invoice_date": data.start_date,
        "line_items": [item.dict() for item in data.line_items],
        "payment_terms_days": data.payment_terms_days,
        "notes": data.notes,
        "terms_conditions": data.terms_conditions,
        "send_email_on_generation": data.send_email_on_generation,
        "auto_charge": data.auto_charge,
        "status": "active",
        "total_generated": 0,
        "last_generated": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    # Calculate totals for display
    subtotal = sum(item.quantity * item.rate for item in data.line_items)
    tax = sum(item.quantity * item.rate * (item.tax_percentage / 100) for item in data.line_items)
    recurring["subtotal"] = round(subtotal, 2)
    recurring["tax_amount"] = round(tax, 2)
    recurring["grand_total"] = round(subtotal + tax, 2)

    await recurring_collection.insert_one(recurring)

    return {
        "code": 0,
        "message": "Recurring invoice created",
        "recurring_id": recurring["recurring_id"],
        "next_invoice_date": recurring["next_invoice_date"]
    }


@router.get("")
async def list_recurring_invoices(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50, request: Request):
    org_id = extract_org_id(request)
    """List all recurring invoice profiles"""
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id

    total = await recurring_collection.count_documents(query)
    profiles = await recurring_collection.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)

    return {
        "code": 0,
        "recurring_invoices": profiles,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }


@router.get("/summary")
async def get_recurring_summary(request: Request):
    org_id = extract_org_id(request)
    """Get summary statistics for recurring invoices"""
    total = await recurring_collection.count_documents(org_query(org_id))
    active = await recurring_collection.count_documents({"status": "active"})
    stopped = await recurring_collection.count_documents({"status": "stopped"})
    expired = await recurring_collection.count_documents({"status": "expired"})

    # Calculate total recurring revenue
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]
    result = await recurring_collection.aggregate(pipeline).to_list(1)
    monthly_revenue = result[0]["total"] if result else 0

    # Get profiles due today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_today = await recurring_collection.count_documents({
        "status": "active",
        "next_invoice_date": today
    })

    return {
        "code": 0,
        "total_profiles": total,
        "active": active,
        "stopped": stopped,
        "expired": expired,
        "monthly_recurring_revenue": monthly_revenue,
        "due_today": due_today
    }


@router.get("/{recurring_id}")
async def get_recurring_invoice(recurring_id: str, request: Request):
    org_id = extract_org_id(request)
    """Get a specific recurring invoice profile"""
    profile = await recurring_collection.find_one(
        {"recurring_id": recurring_id}, {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    # Get generated invoices
    invoices = await invoices_collection.find(
        {"recurring_invoice_id": recurring_id}, {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)

    return {
        "code": 0,
        "recurring_invoice": profile,
        "generated_invoices": invoices
    }


@router.put("/{recurring_id}")
async def update_recurring_invoice(recurring_id: str, data: RecurringInvoiceUpdate, request: Request):
    org_id = extract_org_id(request)
    """Update a recurring invoice profile"""
    profile = await recurring_collection.find_one({"recurring_id": recurring_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    update_dict = {k: v for k, v in data.dict().items() if v is not None}
    if "line_items" in update_dict:
        update_dict["line_items"] = [item.dict() if hasattr(item, 'dict') else item for item in update_dict["line_items"]]
        # Recalculate totals
        subtotal = sum(item["quantity"] * item["rate"] for item in update_dict["line_items"])
        tax = sum(item["quantity"] * item["rate"] * (item.get("tax_percentage", 18) / 100) for item in update_dict["line_items"])
        update_dict["subtotal"] = round(subtotal, 2)
        update_dict["tax_amount"] = round(tax, 2)
        update_dict["grand_total"] = round(subtotal + tax, 2)

    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

    await recurring_collection.update_one(
        {"recurring_id": recurring_id},
        {"$set": update_dict}
    )

    return {"code": 0, "message": "Recurring invoice updated"}


@router.post("/{recurring_id}/stop")
async def stop_recurring_invoice(recurring_id: str, request: Request):
    org_id = extract_org_id(request)
    """Stop a recurring invoice profile"""
    result = await recurring_collection.update_one(
        {"recurring_id": recurring_id},
        {"$set": {"status": "stopped", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    return {"code": 0, "message": "Recurring invoice stopped"}


@router.post("/{recurring_id}/resume")
async def resume_recurring_invoice(recurring_id: str, request: Request):
    org_id = extract_org_id(request)
    """Resume a stopped recurring invoice profile"""
    profile = await recurring_collection.find_one({"recurring_id": recurring_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    # Check if not expired
    if profile.get("end_date"):
        end_date = datetime.strptime(profile["end_date"], "%Y-%m-%d")
        if end_date < datetime.now():
            raise HTTPException(status_code=400, detail="Cannot resume expired profile")

    # Calculate next invoice date from today
    next_date = datetime.now(timezone.utc)
    next_date_str = next_date.strftime("%Y-%m-%d")

    await recurring_collection.update_one(
        {"recurring_id": recurring_id},
        {"$set": {
            "status": "active",
            "next_invoice_date": next_date_str,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    return {"code": 0, "message": "Recurring invoice resumed", "next_invoice_date": next_date_str}


@router.post("/{recurring_id}/generate-now")
async def generate_invoice_now(recurring_id: str, background_tasks: BackgroundTasks, request: Request):
    org_id = extract_org_id(request)
    """Manually generate an invoice from recurring profile"""
    profile = await recurring_collection.find_one(
        {"recurring_id": recurring_id}, {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    try:
        invoice = await create_invoice_from_recurring(profile)

        # Update recurring profile
        next_date = calculate_next_date(
            datetime.now(timezone.utc),
            profile["frequency"],
            profile["repeat_every"]
        )

        await recurring_collection.update_one(
            {"recurring_id": recurring_id},
            {"$set": {
                "next_invoice_date": next_date.strftime("%Y-%m-%d"),
                "last_generated": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$inc": {"total_generated": 1}}
        )

        return {
            "code": 0,
            "message": "Invoice generated successfully",
            "invoice_id": invoice["invoice_id"],
            "invoice_number": invoice["invoice_number"],
            "next_invoice_date": next_date.strftime("%Y-%m-%d")
        }

    except Exception as e:
        logger.error(f"Failed to generate invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-due")
async def process_due_recurring_invoices(background_tasks: BackgroundTasks, request: Request):
    org_id = extract_org_id(request)
    """Process all recurring invoices due today (scheduled job)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    due_profiles = await recurring_collection.find({
        "status": "active",
        "next_invoice_date": {"$lte": today}
    }, {"_id": 0}).to_list(100)

    results = {
        "processed": 0,
        "failed": 0,
        "invoices_generated": []
    }

    for profile in due_profiles:
        try:
            # Check if expired
            if profile.get("end_date"):
                end_date = datetime.strptime(profile["end_date"], "%Y-%m-%d")
                if end_date < datetime.now():
                    await recurring_collection.update_one(
                        {"recurring_id": profile["recurring_id"]},
                        {"$set": {"status": "expired"}}
                    )
                    continue

            invoice = await create_invoice_from_recurring(profile)

            # Calculate next invoice date
            next_date = calculate_next_date(
                datetime.strptime(profile["next_invoice_date"], "%Y-%m-%d"),
                profile["frequency"],
                profile["repeat_every"]
            )

            await recurring_collection.update_one(
                {"recurring_id": profile["recurring_id"]},
                {"$set": {
                    "next_invoice_date": next_date.strftime("%Y-%m-%d"),
                    "last_generated": datetime.now(timezone.utc).isoformat()
                },
                "$inc": {"total_generated": 1}}
            )

            results["processed"] += 1
            results["invoices_generated"].append({
                "recurring_id": profile["recurring_id"],
                "invoice_id": invoice["invoice_id"],
                "customer": profile["customer_name"]
            })

        except Exception as e:
            logger.error(f"Failed to process {profile['recurring_id']}: {str(e)}")
            results["failed"] += 1

    return {
        "code": 0,
        "message": f"Processed {results['processed']} recurring invoices",
        **results
    }


@router.delete("/{recurring_id}")
async def delete_recurring_invoice(recurring_id: str, request: Request):
    org_id = extract_org_id(request)
    """Delete a recurring invoice profile"""
    result = await recurring_collection.delete_one({"recurring_id": recurring_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    return {"code": 0, "message": "Recurring invoice deleted"}
