"""
Battwheels OS - Time Tracking API Routes
Zoho Books-style time tracking for technicians and work orders
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
import os
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/time-tracking", tags=["Time Tracking"])

# Database connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def get_org_id(request: Request) -> Optional[str]:
    """Get organization ID from request header"""
    return request.headers.get("X-Organization-ID")


# ==================== MODELS ====================

class TimeEntryCreate(BaseModel):
    ticket_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: str
    user_name: str
    date: str  # YYYY-MM-DD
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None  # HH:MM
    hours: float = Field(..., gt=0, le=24)
    description: str = ""
    task_type: str = "service"  # service, repair, inspection, admin
    billable: bool = True
    hourly_rate: float = 0
    notes: str = ""

class TimeEntryUpdate(BaseModel):
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    hours: Optional[float] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    billable: Optional[bool] = None
    hourly_rate: Optional[float] = None
    notes: Optional[str] = None
    billed: Optional[bool] = None
    invoice_id: Optional[str] = None

class TimerStart(BaseModel):
    ticket_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: str
    user_name: str
    description: str = ""
    task_type: str = "service"
    billable: bool = True


# ==================== TIME ENTRIES ====================

@router.get("/entries")
async def list_time_entries(request: Request, user_id: str = "", ticket_id: str = "", project_id: str = "", billable: str = "", billed: str = "", start_date: str = "", end_date: str = "", page: int = 1, per_page: int = 50):
    """List time entries with filters"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    query = {"organization_id": org_id}
    
    if user_id:
        query["user_id"] = user_id
    if ticket_id:
        query["ticket_id"] = ticket_id
    if project_id:
        query["project_id"] = project_id
    if billable:
        query["billable"] = billable.lower() == "true"
    if billed:
        query["billed"] = billed.lower() == "true"
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
    
    skip = (page - 1) * per_page
    entries = await db.time_entries.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(per_page).to_list(per_page)
    total = await db.time_entries.count_documents(query)
    
    return {
        "code": 0,
        "entries": entries,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }


@router.post("/entries")
async def create_time_entry(request: Request, entry: TimeEntryCreate):
    """Create a new time entry"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    entry_id = f"TE-{uuid.uuid4().hex[:12].upper()}"
    
    entry_doc = {
        "entry_id": entry_id,
        "organization_id": org_id,
        "ticket_id": entry.ticket_id,
        "project_id": entry.project_id,
        "user_id": entry.user_id,
        "user_name": entry.user_name,
        "date": entry.date,
        "start_time": entry.start_time,
        "end_time": entry.end_time,
        "hours": entry.hours,
        "description": entry.description,
        "task_type": entry.task_type,
        "billable": entry.billable,
        "hourly_rate": entry.hourly_rate,
        "amount": round(entry.hours * entry.hourly_rate, 2),
        "notes": entry.notes,
        "billed": False,
        "invoice_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.time_entries.insert_one(entry_doc)
    
    # Update ticket if linked
    if entry.ticket_id:
        await db.tickets.update_one(
            {"ticket_id": entry.ticket_id},
            {
                "$inc": {"total_hours": entry.hours},
                "$push": {"time_entries": entry_id}
            }
        )
    
    entry_doc.pop("_id", None)
    return {"code": 0, "entry": entry_doc, "message": "Time entry created"}


@router.get("/entries/{entry_id}")
async def get_time_entry(request: Request, entry_id: str):
    """Get a specific time entry"""
    org_id = await get_org_id(request)
    
    entry = await db.time_entries.find_one(
        {"entry_id": entry_id, "organization_id": org_id},
        {"_id": 0}
    )
    
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    return {"code": 0, "entry": entry}


@router.put("/entries/{entry_id}")
async def update_time_entry(request: Request, entry_id: str, update: TimeEntryUpdate):
    """Update a time entry"""
    org_id = await get_org_id(request)
    
    existing = await db.time_entries.find_one(
        {"entry_id": entry_id, "organization_id": org_id}
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    if existing.get("billed"):
        raise HTTPException(status_code=400, detail="Cannot edit billed time entry")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Recalculate amount if hours or rate changed
    if "hours" in update_data or "hourly_rate" in update_data:
        hours = update_data.get("hours", existing.get("hours", 0))
        rate = update_data.get("hourly_rate", existing.get("hourly_rate", 0))
        update_data["amount"] = round(hours * rate, 2)
    
    await db.time_entries.update_one(
        {"entry_id": entry_id},
        {"$set": update_data}
    )
    
    updated = await db.time_entries.find_one({"entry_id": entry_id}, {"_id": 0})
    return {"code": 0, "entry": updated, "message": "Time entry updated"}


@router.delete("/entries/{entry_id}")
async def delete_time_entry(request: Request, entry_id: str):
    """Delete a time entry"""
    org_id = await get_org_id(request)
    
    existing = await db.time_entries.find_one(
        {"entry_id": entry_id, "organization_id": org_id}
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    if existing.get("billed"):
        raise HTTPException(status_code=400, detail="Cannot delete billed time entry")
    
    # Update ticket if linked
    if existing.get("ticket_id"):
        await db.tickets.update_one(
            {"ticket_id": existing["ticket_id"]},
            {
                "$inc": {"total_hours": -existing.get("hours", 0)},
                "$pull": {"time_entries": entry_id}
            }
        )
    
    await db.time_entries.delete_one({"entry_id": entry_id})
    
    return {"code": 0, "message": "Time entry deleted"}


# ==================== TIMER ====================

@router.post("/timer/start")
async def start_timer(request: Request, timer: TimerStart):
    """Start a timer for live time tracking"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    # Check for existing running timer
    existing = await db.active_timers.find_one({
        "user_id": timer.user_id,
        "organization_id": org_id,
        "status": "running"
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Timer already running. Stop it first.")
    
    timer_id = f"TMR-{uuid.uuid4().hex[:12].upper()}"
    
    timer_doc = {
        "timer_id": timer_id,
        "organization_id": org_id,
        "ticket_id": timer.ticket_id,
        "project_id": timer.project_id,
        "user_id": timer.user_id,
        "user_name": timer.user_name,
        "description": timer.description,
        "task_type": timer.task_type,
        "billable": timer.billable,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.active_timers.insert_one(timer_doc)
    timer_doc.pop("_id", None)
    
    return {"code": 0, "timer": timer_doc, "message": "Timer started"}


@router.post("/timer/stop/{timer_id}")
async def stop_timer(request: Request, timer_id: str, hourly_rate: float = 0):
    """Stop a running timer and create time entry"""
    org_id = await get_org_id(request)
    
    timer = await db.active_timers.find_one({
        "timer_id": timer_id,
        "organization_id": org_id,
        "status": "running"
    })
    
    if not timer:
        raise HTTPException(status_code=404, detail="Running timer not found")
    
    end_time = datetime.now(timezone.utc)
    start_time = datetime.fromisoformat(timer["start_time"].replace("Z", "+00:00"))
    
    # Calculate hours
    duration = end_time - start_time
    hours = round(duration.total_seconds() / 3600, 2)
    
    # Create time entry
    entry_id = f"TE-{uuid.uuid4().hex[:12].upper()}"
    
    entry_doc = {
        "entry_id": entry_id,
        "organization_id": org_id,
        "ticket_id": timer.get("ticket_id"),
        "project_id": timer.get("project_id"),
        "user_id": timer["user_id"],
        "user_name": timer["user_name"],
        "date": start_time.strftime("%Y-%m-%d"),
        "start_time": start_time.strftime("%H:%M"),
        "end_time": end_time.strftime("%H:%M"),
        "hours": hours,
        "description": timer.get("description", ""),
        "task_type": timer.get("task_type", "service"),
        "billable": timer.get("billable", True),
        "hourly_rate": hourly_rate,
        "amount": round(hours * hourly_rate, 2),
        "notes": f"Auto-generated from timer {timer_id}",
        "billed": False,
        "invoice_id": None,
        "timer_id": timer_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.time_entries.insert_one(entry_doc)
    
    # Update timer status
    await db.active_timers.update_one(
        {"timer_id": timer_id},
        {"$set": {
            "status": "stopped",
            "end_time": end_time.isoformat(),
            "hours": hours,
            "entry_id": entry_id
        }}
    )
    
    # Update ticket if linked
    if timer.get("ticket_id"):
        await db.tickets.update_one(
            {"ticket_id": timer["ticket_id"]},
            {
                "$inc": {"total_hours": hours},
                "$push": {"time_entries": entry_id}
            }
        )
    
    entry_doc.pop("_id", None)
    return {"code": 0, "entry": entry_doc, "hours": hours, "message": "Timer stopped and entry created"}


@router.get("/timer/active")
async def get_active_timers(request: Request, user_id: str = ""):
    """Get active running timers"""
    org_id = await get_org_id(request)
    
    query = {"organization_id": org_id, "status": "running"}
    if user_id:
        query["user_id"] = user_id
    
    timers = await db.active_timers.find(query, {"_id": 0}).to_list(100)
    
    # Calculate elapsed time for each timer
    now = datetime.now(timezone.utc)
    for timer in timers:
        start = datetime.fromisoformat(timer["start_time"].replace("Z", "+00:00"))
        elapsed = now - start
        timer["elapsed_seconds"] = int(elapsed.total_seconds())
        timer["elapsed_hours"] = round(elapsed.total_seconds() / 3600, 2)
    
    return {"code": 0, "timers": timers}


# ==================== UNBILLED HOURS ====================

@router.get("/unbilled")
async def get_unbilled_hours(request: Request, user_id: str = "", ticket_id: str = ""):
    """Get unbilled time entries summary"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    query = {
        "organization_id": org_id,
        "billable": True,
        "billed": False
    }
    
    if user_id:
        query["user_id"] = user_id
    if ticket_id:
        query["ticket_id"] = ticket_id
    
    entries = await db.time_entries.find(query, {"_id": 0}).to_list(1000)
    
    # Group by ticket/project
    grouped = {}
    for entry in entries:
        key = entry.get("ticket_id") or entry.get("project_id") or "unassigned"
        if key not in grouped:
            grouped[key] = {
                "ticket_id": entry.get("ticket_id"),
                "project_id": entry.get("project_id"),
                "entries": [],
                "total_hours": 0,
                "total_amount": 0
            }
        grouped[key]["entries"].append(entry)
        grouped[key]["total_hours"] += entry.get("hours", 0)
        grouped[key]["total_amount"] += entry.get("amount", 0)
    
    # Round values
    for key in grouped:
        grouped[key]["total_hours"] = round(grouped[key]["total_hours"], 2)
        grouped[key]["total_amount"] = round(grouped[key]["total_amount"], 2)
    
    total_hours = sum(g["total_hours"] for g in grouped.values())
    total_amount = sum(g["total_amount"] for g in grouped.values())
    
    return {
        "code": 0,
        "unbilled": {
            "groups": list(grouped.values()),
            "total_hours": round(total_hours, 2),
            "total_amount": round(total_amount, 2),
            "entry_count": len(entries)
        }
    }


@router.post("/convert-to-invoice")
async def convert_to_invoice(request: Request, entry_ids: List[str], customer_id: str):
    """Convert unbilled time entries to an invoice"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    # Get entries
    entries = await db.time_entries.find({
        "entry_id": {"$in": entry_ids},
        "organization_id": org_id,
        "billed": False
    }, {"_id": 0}).to_list(len(entry_ids))
    
    if not entries:
        raise HTTPException(status_code=404, detail="No unbilled entries found")
    
    # Get customer info
    customer = await db.contacts.find_one(
        {"contact_id": customer_id, "organization_id": org_id},
        {"_id": 0}
    )
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Create invoice
    invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    
    line_items = []
    total = 0
    
    for entry in entries:
        item = {
            "item_id": entry["entry_id"],
            "name": f"Time: {entry.get('description', entry.get('task_type', 'Service'))}",
            "description": f"{entry.get('hours', 0)} hours on {entry.get('date', '')}",
            "quantity": entry.get("hours", 0),
            "rate": entry.get("hourly_rate", 0),
            "amount": entry.get("amount", 0),
            "time_entry_id": entry["entry_id"]
        }
        line_items.append(item)
        total += entry.get("amount", 0)
    
    invoice_doc = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "organization_id": org_id,
        "customer_id": customer_id,
        "customer_name": customer.get("contact_name") or customer.get("company_name"),
        "invoice_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "line_items": line_items,
        "sub_total": round(total, 2),
        "total": round(total, 2),
        "balance": round(total, 2),
        "status": "draft",
        "source": "time_tracking",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(invoice_doc)
    
    # Mark entries as billed
    await db.time_entries.update_many(
        {"entry_id": {"$in": entry_ids}},
        {"$set": {"billed": True, "invoice_id": invoice_id}}
    )
    
    invoice_doc.pop("_id", None)
    return {
        "code": 0,
        "invoice": invoice_doc,
        "message": f"Invoice {invoice_number} created from {len(entries)} time entries"
    }


# ==================== REPORTS ====================

@router.get("/reports/summary")
async def get_time_summary(request: Request, start_date: str = "", end_date: str = "", group_by: str = "user"  # user, ticket, task_type, date):
    """Get time tracking summary report"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    # Default to current month
    if not start_date:
        start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    query = {
        "organization_id": org_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    entries = await db.time_entries.find(query, {"_id": 0}).to_list(10000)
    
    # Group data
    grouped = {}
    for entry in entries:
        if group_by == "user":
            key = entry.get("user_name", "Unknown")
        elif group_by == "ticket":
            key = entry.get("ticket_id", "Unassigned")
        elif group_by == "task_type":
            key = entry.get("task_type", "Other")
        elif group_by == "date":
            key = entry.get("date", "Unknown")
        else:
            key = "All"
        
        if key not in grouped:
            grouped[key] = {
                "key": key,
                "total_hours": 0,
                "billable_hours": 0,
                "non_billable_hours": 0,
                "billed_hours": 0,
                "unbilled_hours": 0,
                "total_amount": 0,
                "billed_amount": 0,
                "unbilled_amount": 0,
                "entry_count": 0
            }
        
        hours = entry.get("hours", 0)
        amount = entry.get("amount", 0)
        
        grouped[key]["total_hours"] += hours
        grouped[key]["entry_count"] += 1
        grouped[key]["total_amount"] += amount
        
        if entry.get("billable"):
            grouped[key]["billable_hours"] += hours
            if entry.get("billed"):
                grouped[key]["billed_hours"] += hours
                grouped[key]["billed_amount"] += amount
            else:
                grouped[key]["unbilled_hours"] += hours
                grouped[key]["unbilled_amount"] += amount
        else:
            grouped[key]["non_billable_hours"] += hours
    
    # Round values
    for key in grouped:
        for field in grouped[key]:
            if isinstance(grouped[key][field], float):
                grouped[key][field] = round(grouped[key][field], 2)
    
    summary = list(grouped.values())
    summary.sort(key=lambda x: x["total_hours"], reverse=True)
    
    return {
        "code": 0,
        "report": {
            "period": {"start": start_date, "end": end_date},
            "group_by": group_by,
            "summary": summary,
            "totals": {
                "total_hours": round(sum(g["total_hours"] for g in summary), 2),
                "billable_hours": round(sum(g["billable_hours"] for g in summary), 2),
                "unbilled_hours": round(sum(g["unbilled_hours"] for g in summary), 2),
                "total_amount": round(sum(g["total_amount"] for g in summary), 2)
            }
        }
    }
