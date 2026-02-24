"""
Zoho Books Extended Features
Recurring Transactions, Delivery Challans, Retainer Invoices, Projects, Taxes, etc.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import logging
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/zoho", tags=["zoho-extended"])

def get_db():
    from server import db
    return db

# ============== RECURRING TRANSACTIONS ==============

class RecurringInvoiceCreate(BaseModel):
    customer_id: str
    customer_name: str
    recurrence_name: str
    recurrence_frequency: str = "monthly"  # weekly, monthly, yearly, custom
    repeat_every: int = 1
    start_date: str
    end_date: Optional[str] = None
    never_expires: bool = False
    line_items: List[Dict]
    payment_terms: int = 15
    notes: Optional[str] = ""
    terms: Optional[str] = ""

@router.post("/recurring-invoices")
async def create_recurring_invoice(request: Request, ri: RecurringInvoiceCreate):
    org_id = extract_org_id(request)
    """Create a recurring invoice profile"""
    db = get_db()
    ri_id = f"RI-{uuid.uuid4().hex[:12].upper()}"
    
    # Calculate totals
    sub_total = sum(item.get("quantity", 1) * item.get("rate", 0) for item in ri.line_items)
    tax_total = sum(
        item.get("quantity", 1) * item.get("rate", 0) * (item.get("tax_percentage", 0) / 100)
        for item in ri.line_items
    )
    total = sub_total + tax_total
    
    ri_dict = {
        "recurring_invoice_id": ri_id,
        "customer_id": ri.customer_id,
        "customer_name": ri.customer_name,
        "recurrence_name": ri.recurrence_name,
        "recurrence_frequency": ri.recurrence_frequency,
        "repeat_every": ri.repeat_every,
        "start_date": ri.start_date,
        "end_date": ri.end_date,
        "never_expires": ri.never_expires,
        "next_invoice_date": ri.start_date,
        "line_items": ri.line_items,
        "sub_total": sub_total,
        "tax_total": tax_total,
        "total": total,
        "payment_terms": ri.payment_terms,
        "notes": ri.notes,
        "terms": ri.terms,
        "status": "active",
        "invoices_generated": 0,
        "last_invoice_date": None,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.recurring_invoices.insert_one(ri_dict)
    del ri_dict["_id"]
    return {"code": 0, "message": "Recurring invoice created", "recurring_invoice": ri_dict}

@router.get("/recurring-invoices")
async def list_recurring_invoices(request: Request, status: str = "", customer_id: str = ""):
    org_id = extract_org_id(request)
    """List all recurring invoices"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.recurring_invoices.find(query, {"_id": 0}).sort("created_time", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "recurring_invoices": items}

@router.get("/recurring-invoices/{ri_id}")
async def get_recurring_invoice(request: Request, ri_id: str):
    org_id = extract_org_id(request)
    """Get recurring invoice details"""
    db = get_db()
    ri = await db.recurring_invoices.find_one({"recurring_invoice_id": ri_id}, {"_id": 0})
    if not ri:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")
    return {"code": 0, "recurring_invoice": ri}

@router.post("/recurring-invoices/{ri_id}/stop")
async def stop_recurring_invoice(request: Request, ri_id: str):
    org_id = extract_org_id(request)
    """Stop a recurring invoice"""
    db = get_db()
    result = await db.recurring_invoices.update_one(
        {"recurring_invoice_id": ri_id},
        {"$set": {"status": "stopped"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")
    return {"code": 0, "message": "Recurring invoice stopped"}

@router.post("/recurring-invoices/{ri_id}/resume")
async def resume_recurring_invoice(request: Request, ri_id: str):
    org_id = extract_org_id(request)
    """Resume a stopped recurring invoice"""
    db = get_db()
    result = await db.recurring_invoices.update_one(
        {"recurring_invoice_id": ri_id},
        {"$set": {"status": "active"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")
    return {"code": 0, "message": "Recurring invoice resumed"}

@router.delete("/recurring-invoices/{ri_id}")
async def delete_recurring_invoice(request: Request, ri_id: str):
    org_id = extract_org_id(request)
    """Delete a recurring invoice"""
    db = get_db()
    result = await db.recurring_invoices.delete_one({"recurring_invoice_id": ri_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")
    return {"code": 0, "message": "Recurring invoice deleted"}

@router.post("/recurring-invoices/generate")
async def generate_due_invoices(request: Request):
    org_id = extract_org_id(request)
    """Generate invoices for all due recurring profiles"""
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Find active recurring invoices due today or earlier
    ris = await db.recurring_invoices.find({
        "status": "active",
        "next_invoice_date": {"$lte": today}
    }, {"_id": 0}).to_list(length=1000)
    
    generated = 0
    for ri in ris:
        try:
            # Create invoice
            invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
            counter = await db.counters.find_one_and_update(
                {"_id": "invoices"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            invoice_number = f"INV-{str(counter['seq']).zfill(6)}"
            
            due_date = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=ri.get("payment_terms", 15))).strftime("%Y-%m-%d")
            
            invoice_dict = {
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "customer_id": ri["customer_id"],
                "customer_name": ri["customer_name"],
                "date": today,
                "due_date": due_date,
                "status": "draft",
                "line_items": ri["line_items"],
                "sub_total": ri["sub_total"],
                "tax_total": ri["tax_total"],
                "total": ri["total"],
                "balance": ri["total"],
                "payment_made": 0,
                "from_recurring_invoice_id": ri["recurring_invoice_id"],
                "notes": ri.get("notes", ""),
                "terms": ri.get("terms", ""),
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await db.invoices.insert_one(invoice_dict)
            
            # Calculate next invoice date
            next_date = calculate_next_date(
                ri["next_invoice_date"],
                ri["recurrence_frequency"],
                ri["repeat_every"]
            )
            
            # Check if expired
            new_status = ri["status"]
            if ri.get("end_date") and next_date > ri["end_date"]:
                new_status = "expired"
            
            # Update recurring invoice
            await db.recurring_invoices.update_one(
                {"recurring_invoice_id": ri["recurring_invoice_id"]},
                {"$set": {
                    "next_invoice_date": next_date,
                    "last_invoice_date": today,
                    "status": new_status
                },
                "$inc": {"invoices_generated": 1}}
            )
            
            generated += 1
        except Exception as e:
            logger.error(f"Error generating invoice for {ri['recurring_invoice_id']}: {e}")
    
    return {"code": 0, "message": f"Generated {generated} invoices"}

def calculate_next_date(current_date: str, frequency: str, repeat_every: int) -> str:
    """Calculate next recurring date"""
    dt = datetime.strptime(current_date, "%Y-%m-%d")
    
    if frequency == "daily":
        next_dt = dt + timedelta(days=repeat_every)
    elif frequency == "weekly":
        next_dt = dt + timedelta(weeks=repeat_every)
    elif frequency == "monthly":
        next_dt = dt + relativedelta(months=repeat_every)
    elif frequency == "yearly":
        next_dt = dt + relativedelta(years=repeat_every)
    else:
        next_dt = dt + relativedelta(months=repeat_every)
    
    return next_dt.strftime("%Y-%m-%d")

# ============== DELIVERY CHALLANS ==============

class DeliveryChallanCreate(BaseModel):
    customer_id: str
    customer_name: str
    challan_number: Optional[str] = ""
    reference_number: Optional[str] = ""
    date: Optional[str] = None
    challan_type: str = "delivery"  # delivery, job_work, supply_on_approval
    line_items: List[Dict]
    shipping_address: Optional[Dict] = {}
    notes: Optional[str] = ""

@router.post("/delivery-challans")
async def create_delivery_challan(request: Request, dc: DeliveryChallanCreate):
    org_id = extract_org_id(request)
    """Create a delivery challan"""
    db = get_db()
    dc_id = f"DC-{uuid.uuid4().hex[:12].upper()}"
    
    counter = await db.counters.find_one_and_update(
        {"_id": "delivery_challans"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    dc_number = dc.challan_number or f"DC-{str(counter['seq']).zfill(6)}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Calculate totals
    sub_total = sum(item.get("quantity", 1) * item.get("rate", 0) for item in dc.line_items)
    
    dc_dict = {
        "delivery_challan_id": dc_id,
        "challan_number": dc_number,
        "customer_id": dc.customer_id,
        "customer_name": dc.customer_name,
        "reference_number": dc.reference_number,
        "date": dc.date or today,
        "challan_type": dc.challan_type,
        "line_items": dc.line_items,
        "sub_total": sub_total,
        "shipping_address": dc.shipping_address,
        "notes": dc.notes,
        "status": "draft",
        "is_invoiced": False,
        "invoice_id": None,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.delivery_challans.insert_one(dc_dict)
    del dc_dict["_id"]
    return {"code": 0, "message": "Delivery challan created", "delivery_challan": dc_dict}

@router.get("/delivery-challans")
async def list_delivery_challans(request: Request, status: str = "", customer_id: str = "", page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List delivery challans with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id

    total = await db.delivery_challans.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    items = await db.delivery_challans.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "data": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/delivery-challans/{dc_id}")
async def get_delivery_challan(request: Request, dc_id: str):
    org_id = extract_org_id(request)
    """Get delivery challan details"""
    db = get_db()
    dc = await db.delivery_challans.find_one({"delivery_challan_id": dc_id}, {"_id": 0})
    if not dc:
        raise HTTPException(status_code=404, detail="Delivery challan not found")
    return {"code": 0, "delivery_challan": dc}

@router.post("/delivery-challans/{dc_id}/status/delivered")
async def mark_challan_delivered(request: Request, dc_id: str):
    org_id = extract_org_id(request)
    """Mark delivery challan as delivered"""
    db = get_db()
    result = await db.delivery_challans.update_one(
        {"delivery_challan_id": dc_id},
        {"$set": {"status": "delivered", "delivered_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Delivery challan not found")
    return {"code": 0, "message": "Delivery challan marked as delivered"}

@router.post("/delivery-challans/{dc_id}/convert-to-invoice")
async def convert_challan_to_invoice(request: Request, dc_id: str):
    org_id = extract_org_id(request)
    """Convert delivery challan to invoice"""
    db = get_db()
    dc = await db.delivery_challans.find_one({"delivery_challan_id": dc_id}, {"_id": 0})
    if not dc:
        raise HTTPException(status_code=404, detail="Delivery challan not found")
    
    if dc.get("is_invoiced"):
        raise HTTPException(status_code=400, detail="Challan already invoiced")
    
    # Create invoice
    invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    counter = await db.counters.find_one_and_update(
        {"_id": "invoices"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    invoice_number = f"INV-{str(counter['seq']).zfill(6)}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_date = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d")
    
    # Calculate totals with tax
    sub_total = sum(item.get("quantity", 1) * item.get("rate", 0) for item in dc["line_items"])
    tax_total = sum(
        item.get("quantity", 1) * item.get("rate", 0) * (item.get("tax_percentage", 18) / 100)
        for item in dc["line_items"]
    )
    total = sub_total + tax_total
    
    invoice_dict = {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "customer_id": dc["customer_id"],
        "customer_name": dc["customer_name"],
        "date": today,
        "due_date": due_date,
        "status": "draft",
        "line_items": dc["line_items"],
        "sub_total": sub_total,
        "tax_total": tax_total,
        "total": total,
        "balance": total,
        "payment_made": 0,
        "from_delivery_challan_id": dc_id,
        "from_delivery_challan_number": dc["challan_number"],
        "notes": dc.get("notes", ""),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(invoice_dict)
    
    # Update challan
    await db.delivery_challans.update_one(
        {"delivery_challan_id": dc_id},
        {"$set": {"is_invoiced": True, "invoice_id": invoice_id, "status": "invoiced"}}
    )
    
    del invoice_dict["_id"]
    return {"code": 0, "message": "Invoice created from delivery challan", "invoice": invoice_dict}

# ============== RETAINER INVOICES ==============

class RetainerInvoiceCreate(BaseModel):
    customer_id: str
    customer_name: str
    retainer_number: Optional[str] = ""
    date: Optional[str] = None
    amount: float
    description: Optional[str] = ""
    project_id: Optional[str] = ""
    project_name: Optional[str] = ""

@router.post("/retainer-invoices")
async def create_retainer_invoice(request: Request, ri: RetainerInvoiceCreate):
    org_id = extract_org_id(request)
    """Create a retainer invoice (advance payment)"""
    db = get_db()
    ri_id = f"RET-{uuid.uuid4().hex[:12].upper()}"
    
    counter = await db.counters.find_one_and_update(
        {"_id": "retainer_invoices"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    retainer_number = ri.retainer_number or f"RET-{str(counter['seq']).zfill(6)}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    ri_dict = {
        "retainer_invoice_id": ri_id,
        "retainer_number": retainer_number,
        "customer_id": ri.customer_id,
        "customer_name": ri.customer_name,
        "date": ri.date or today,
        "amount": ri.amount,
        "balance": ri.amount,
        "used_amount": 0,
        "description": ri.description,
        "project_id": ri.project_id,
        "project_name": ri.project_name,
        "status": "draft",
        "applied_invoices": [],
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.retainer_invoices.insert_one(ri_dict)
    del ri_dict["_id"]
    return {"code": 0, "message": "Retainer invoice created", "retainer_invoice": ri_dict}

@router.get("/retainer-invoices")
async def list_retainer_invoices(request: Request, status: str = "", customer_id: str = ""):
    org_id = extract_org_id(request)
    """List all retainer invoices"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.retainer_invoices.find(query, {"_id": 0}).sort("date", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "retainer_invoices": items}

@router.post("/retainer-invoices/{ri_id}/apply/{invoice_id}")
async def apply_retainer_to_invoice(request: Request, ri_id: str, invoice_id: str, amount: float):
    org_id = extract_org_id(request)
    """Apply retainer to an invoice"""
    db = get_db()
    
    retainer = await db.retainer_invoices.find_one({"retainer_invoice_id": ri_id}, {"_id": 0})
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    
    if not retainer:
        raise HTTPException(status_code=404, detail="Retainer invoice not found")
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if amount > retainer["balance"]:
        raise HTTPException(status_code=400, detail="Amount exceeds retainer balance")
    if amount > invoice["balance"]:
        raise HTTPException(status_code=400, detail="Amount exceeds invoice balance")
    
    # Update retainer
    new_balance = retainer["balance"] - amount
    new_status = "closed" if new_balance <= 0 else retainer["status"]
    
    await db.retainer_invoices.update_one(
        {"retainer_invoice_id": ri_id},
        {
            "$set": {"balance": new_balance, "used_amount": retainer["used_amount"] + amount, "status": new_status},
            "$push": {"applied_invoices": {"invoice_id": invoice_id, "amount": amount, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}}
        }
    )
    
    # Update invoice
    new_inv_balance = invoice["balance"] - amount
    inv_status = "paid" if new_inv_balance <= 0 else "partially_paid"
    
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"balance": new_inv_balance, "status": inv_status},
         "$inc": {"payment_made": amount}}
    )
    
    return {"code": 0, "message": f"Applied ₹{amount} from retainer to invoice"}

# ============== PROJECTS & TIME TRACKING ==============

class ProjectCreate(BaseModel):
    project_name: str
    customer_id: str
    customer_name: str
    description: Optional[str] = ""
    billing_type: str = "fixed_cost"  # fixed_cost, based_on_project_hours, based_on_task_hours, based_on_staff_hours
    rate: float = 0
    budget_type: str = "no_budget"  # no_budget, total_project_cost, hours_per_task, hours_per_staff
    budget_amount: float = 0
    budget_hours: float = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@router.post("/projects")
async def create_project(request: Request, project: ProjectCreate):
    org_id = extract_org_id(request)
    """Create a new project"""
    db = get_db()
    project_id = f"PRJ-{uuid.uuid4().hex[:12].upper()}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    project_dict = {
        "project_id": project_id,
        "project_name": project.project_name,
        "customer_id": project.customer_id,
        "customer_name": project.customer_name,
        "description": project.description,
        "billing_type": project.billing_type,
        "rate": project.rate,
        "budget_type": project.budget_type,
        "budget_amount": project.budget_amount,
        "budget_hours": project.budget_hours,
        "start_date": project.start_date or today,
        "end_date": project.end_date,
        "status": "active",
        "total_hours": 0,
        "billed_hours": 0,
        "unbilled_hours": 0,
        "total_cost": 0,
        "billed_amount": 0,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.insert_one(project_dict)
    del project_dict["_id"]
    return {"code": 0, "message": "Project created", "project": project_dict}

@router.get("/projects")
async def list_projects(request: Request, status: str = "", customer_id: str = ""):
    org_id = extract_org_id(request)
    """List all projects"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.projects.find(query, {"_id": 0}).sort("created_time", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "projects": items}

@router.get("/projects/{project_id}")
async def get_project(request: Request, project_id: str):
    org_id = extract_org_id(request)
    """Get project details"""
    db = get_db()
    project = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"code": 0, "project": project}

@router.put("/projects/{project_id}")
async def update_project(request: Request, project_id: str, project: ProjectCreate):
    org_id = extract_org_id(request)
    """Update project"""
    db = get_db()
    result = await db.projects.update_one(
        {"project_id": project_id},
        {"$set": project.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"code": 0, "message": "Project updated"}

@router.post("/projects/{project_id}/status/{status}")
async def update_project_status(request: Request, project_id: str, status: str):
    org_id = extract_org_id(request)
    """Update project status (active, on_hold, completed, cancelled)"""
    db = get_db()
    if status not in ["active", "on_hold", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.projects.update_one(
        {"project_id": project_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"code": 0, "message": f"Project status updated to {status}"}

# Time Entries
class TimeEntryCreate(BaseModel):
    project_id: str
    project_name: str
    user_id: Optional[str] = ""
    user_name: Optional[str] = ""
    task_name: Optional[str] = ""
    date: Optional[str] = None
    hours: float
    is_billable: bool = True
    description: Optional[str] = ""
    rate: float = 0

@router.post("/time-entries")
async def create_time_entry(request: Request, entry: TimeEntryCreate):
    org_id = extract_org_id(request)
    """Log time entry for a project"""
    db = get_db()
    entry_id = f"TE-{uuid.uuid4().hex[:12].upper()}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get project rate if not specified
    project = await db.projects.find_one({"project_id": entry.project_id}, {"_id": 0})
    rate = entry.rate if entry.rate > 0 else (project.get("rate", 0) if project else 0)
    cost = entry.hours * rate
    
    entry_dict = {
        "time_entry_id": entry_id,
        "project_id": entry.project_id,
        "project_name": entry.project_name,
        "user_id": entry.user_id,
        "user_name": entry.user_name,
        "task_name": entry.task_name,
        "date": entry.date or today,
        "hours": entry.hours,
        "is_billable": entry.is_billable,
        "is_billed": False,
        "description": entry.description,
        "rate": rate,
        "cost": cost,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.time_entries.insert_one(entry_dict)
    
    # Update project totals
    if project:
        update_fields = {"$inc": {"total_hours": entry.hours, "total_cost": cost}}
        if entry.is_billable:
            update_fields["$inc"]["unbilled_hours"] = entry.hours
        await db.projects.update_one({"project_id": entry.project_id}, update_fields)
    
    del entry_dict["_id"]
    return {"code": 0, "message": "Time entry logged", "time_entry": entry_dict}

@router.get("/time-entries")
async def list_time_entries(request: Request, project_id: str = "", user_id: str = "", is_billed: str = ""):
    org_id = extract_org_id(request)
    """List time entries"""
    db = get_db()
    query = {}
    if project_id:
        query["project_id"] = project_id
    if user_id:
        query["user_id"] = user_id
    if is_billed:
        query["is_billed"] = is_billed.lower() == "true"
    
    cursor = db.time_entries.find(query, {"_id": 0}).sort("date", -1)
    items = await cursor.to_list(length=500)
    
    total_hours = sum(e.get("hours", 0) for e in items)
    total_cost = sum(e.get("cost", 0) for e in items)
    
    return {"code": 0, "time_entries": items, "total_hours": total_hours, "total_cost": total_cost}

@router.delete("/time-entries/{entry_id}")
async def delete_time_entry(request: Request, entry_id: str):
    org_id = extract_org_id(request)
    """Delete time entry"""
    db = get_db()
    entry = await db.time_entries.find_one({"time_entry_id": entry_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Update project totals
    await db.projects.update_one(
        {"project_id": entry["project_id"]},
        {"$inc": {"total_hours": -entry["hours"], "total_cost": -entry["cost"], "unbilled_hours": -entry["hours"] if entry["is_billable"] and not entry["is_billed"] else 0}}
    )
    
    await db.time_entries.delete_one({"time_entry_id": entry_id})
    return {"code": 0, "message": "Time entry deleted"}

# ============== TAXES CONFIGURATION ==============

class TaxCreate(BaseModel):
    tax_name: str
    tax_percentage: float
    tax_type: str = "tax"  # tax, compound_tax, cess
    is_default: bool = False
    description: Optional[str] = ""

@router.post("/taxes")
async def create_tax(request: Request, tax: TaxCreate):
    org_id = extract_org_id(request)
    """Create a tax rate"""
    db = get_db()
    tax_id = f"TAX-{uuid.uuid4().hex[:12].upper()}"
    
    tax_dict = {
        "tax_id": tax_id,
        **tax.dict(),
        "status": "active",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.taxes.insert_one(tax_dict)
    del tax_dict["_id"]
    return {"code": 0, "message": "Tax created", "tax": tax_dict}

@router.get("/taxes")
async def list_taxes(request: Request):
    org_id = extract_org_id(request)
    """List all taxes"""
    db = get_db()
    cursor = db.taxes.find({"status": "active"}, {"_id": 0})
    items = await cursor.to_list(length=100)
    return {"code": 0, "taxes": items}

@router.put("/taxes/{tax_id}")
async def update_tax(request: Request, tax_id: str, tax: TaxCreate):
    org_id = extract_org_id(request)
    """Update tax"""
    db = get_db()
    result = await db.taxes.update_one({"tax_id": tax_id}, {"$set": tax.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tax not found")
    return {"code": 0, "message": "Tax updated"}

@router.delete("/taxes/{tax_id}")
async def delete_tax(request: Request, tax_id: str):
    org_id = extract_org_id(request)
    """Delete (deactivate) tax"""
    db = get_db()
    result = await db.taxes.update_one({"tax_id": tax_id}, {"$set": {"status": "inactive"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tax not found")
    return {"code": 0, "message": "Tax deleted"}

# Tax Groups
class TaxGroupCreate(BaseModel):
    group_name: str
    tax_ids: List[str]
    description: Optional[str] = ""

@router.post("/tax-groups")
async def create_tax_group(request: Request, group: TaxGroupCreate):
    org_id = extract_org_id(request)
    """Create a tax group"""
    db = get_db()
    group_id = f"TG-{uuid.uuid4().hex[:12].upper()}"
    
    # Calculate combined rate
    taxes = await db.taxes.find({"tax_id": {"$in": group.tax_ids}}, {"_id": 0}).to_list(length=20)
    combined_rate = sum(t.get("tax_percentage", 0) for t in taxes)
    
    group_dict = {
        "tax_group_id": group_id,
        **group.dict(),
        "taxes": taxes,
        "combined_rate": combined_rate,
        "status": "active",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tax_groups.insert_one(group_dict)
    del group_dict["_id"]
    return {"code": 0, "message": "Tax group created", "tax_group": group_dict}

@router.get("/tax-groups")
async def list_tax_groups(request: Request):
    org_id = extract_org_id(request)
    """List all tax groups"""
    db = get_db()
    cursor = db.tax_groups.find({"status": "active"}, {"_id": 0})
    items = await cursor.to_list(length=100)
    return {"code": 0, "tax_groups": items}

# ============== PAYMENT REMINDERS ==============

class PaymentReminderCreate(BaseModel):
    reminder_name: str
    days_before_after: int  # negative = before due, positive = after due
    is_active: bool = True
    email_subject: str
    email_body: str

@router.post("/payment-reminders/templates")
async def create_reminder_template(request: Request, reminder: PaymentReminderCreate):
    org_id = extract_org_id(request)
    """Create a payment reminder template"""
    db = get_db()
    reminder_id = f"RMD-{uuid.uuid4().hex[:12].upper()}"
    
    reminder_dict = {
        "reminder_id": reminder_id,
        **reminder.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payment_reminder_templates.insert_one(reminder_dict)
    del reminder_dict["_id"]
    return {"code": 0, "message": "Reminder template created", "reminder": reminder_dict}

@router.get("/payment-reminders/templates")
async def list_reminder_templates(request: Request):
    org_id = extract_org_id(request)
    """List all reminder templates"""
    db = get_db()
    cursor = db.payment_reminder_templates.find({}, {"_id": 0})
    items = await cursor.to_list(length=50)
    return {"code": 0, "reminder_templates": items}

@router.post("/payment-reminders/send")
async def send_payment_reminders(request: Request):
    org_id = extract_org_id(request)
    """Send payment reminders for due invoices"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    # Get active reminder templates
    templates = await db.payment_reminder_templates.find({"is_active": True}, {"_id": 0}).to_list(length=20)
    
    # Get unpaid invoices
    invoices = await db.invoices.find(
        {"balance": {"$gt": 0}, "status": {"$nin": ["paid", "void"]}},
        {"_id": 0}
    ).to_list(length=10000)
    
    reminders_sent = 0
    
    for inv in invoices:
        try:
            due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_from_due = (today - due_date).days
            
            for template in templates:
                if template["days_before_after"] == days_from_due:
                    # Create reminder record
                    reminder_record = {
                        "reminder_record_id": f"RR-{uuid.uuid4().hex[:12].upper()}",
                        "invoice_id": inv["invoice_id"],
                        "invoice_number": inv["invoice_number"],
                        "customer_id": inv["customer_id"],
                        "customer_name": inv["customer_name"],
                        "reminder_id": template["reminder_id"],
                        "reminder_name": template["reminder_name"],
                        "sent_date": today.strftime("%Y-%m-%d"),
                        "status": "sent",
                        "created_time": today.isoformat()
                    }
                    await db.payment_reminder_records.insert_one(reminder_record)
                    reminders_sent += 1
        except Exception:
            continue
    
    return {"code": 0, "message": f"Sent {reminders_sent} payment reminders"}

@router.get("/payment-reminders/history")
async def get_reminder_history(request: Request, invoice_id: str = "", customer_id: str = ""):
    org_id = extract_org_id(request)
    """Get payment reminder history"""
    db = get_db()
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.payment_reminder_records.find(query, {"_id": 0}).sort("sent_date", -1)
    items = await cursor.to_list(length=500)
    return {"code": 0, "reminder_records": items}

# ============== INVENTORY ADJUSTMENTS ==============

class InventoryAdjustmentCreate(BaseModel):
    adjustment_type: str  # quantity, value
    reason: str  # damaged, stolen, stock_on_fire, expired, written_off, other
    description: Optional[str] = ""
    date: Optional[str] = None
    reference_number: Optional[str] = ""
    line_items: List[Dict]  # [{item_id, item_name, quantity_adjusted, new_quantity}]

@router.post("/inventory-adjustments")
async def create_inventory_adjustment(request: Request, adj: InventoryAdjustmentCreate):
    org_id = extract_org_id(request)
    """Create an inventory adjustment"""
    db = get_db()
    adj_id = f"ADJ-{uuid.uuid4().hex[:12].upper()}"
    
    counter = await db.counters.find_one_and_update(
        {"_id": "inventory_adjustments"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    adj_number = f"ADJ-{str(counter['seq']).zfill(6)}"
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    adj_dict = {
        "adjustment_id": adj_id,
        "adjustment_number": adj_number,
        "adjustment_type": adj.adjustment_type,
        "reason": adj.reason,
        "description": adj.description,
        "date": adj.date or today,
        "reference_number": adj.reference_number,
        "line_items": adj.line_items,
        "status": "adjusted",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    # Update item stock levels
    for item in adj.line_items:
        await db.items.update_one(
            {"item_id": item.get("item_id")},
            {"$set": {"stock_on_hand": item.get("new_quantity", 0)}}
        )
    
    await db.inventory_adjustments.insert_one(adj_dict)
    del adj_dict["_id"]
    return {"code": 0, "message": "Inventory adjustment created", "adjustment": adj_dict}

@router.get("/inventory-adjustments")
async def list_inventory_adjustments(request: Request, reason: str = ""):
    org_id = extract_org_id(request)
    """List all inventory adjustments"""
    db = get_db()
    query = {}
    if reason:
        query["reason"] = reason
    
    cursor = db.inventory_adjustments.find(query, {"_id": 0}).sort("date", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "inventory_adjustments": items}

@router.get("/inventory-adjustments/{adj_id}")
async def get_inventory_adjustment(request: Request, adj_id: str):
    org_id = extract_org_id(request)
    """Get inventory adjustment details"""
    db = get_db()
    adj = await db.inventory_adjustments.find_one({"adjustment_id": adj_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    return {"code": 0, "adjustment": adj}

# ============== PRICE LISTS (ENHANCED - Zoho Books Compatible) ==============

class PriceListCreate(BaseModel):
    price_list_name: str
    description: Optional[str] = ""
    currency_code: str = "INR"
    price_type: str = "sales"  # sales, purchase
    is_default: bool = False
    round_off_to: str = "never"  # never, nearest_1, nearest_5, nearest_10
    percentage_type: Optional[str] = None  # markup_percentage, markdown_percentage
    percentage_value: Optional[float] = 0  # Default percentage for all items

class PriceListItemCreate(BaseModel):
    item_id: str
    pricelist_rate: Optional[float] = None  # Custom rate for this item
    discount: Optional[float] = 0  # Discount percentage (0-100)
    discount_type: str = "percentage"  # percentage, fixed_amount

class PriceListUpdate(BaseModel):
    price_list_name: Optional[str] = None
    description: Optional[str] = None
    currency_code: Optional[str] = None
    price_type: Optional[str] = None
    is_default: Optional[bool] = None
    round_off_to: Optional[str] = None
    percentage_type: Optional[str] = None
    percentage_value: Optional[float] = None
    status: Optional[str] = None

@router.post("/price-lists")
async def create_price_list(request: Request, pl: PriceListCreate):
    org_id = extract_org_id(request)
    """Create a price list"""
    db = get_db()
    pl_id = f"PL-{uuid.uuid4().hex[:12].upper()}"
    
    pl_dict = {
        "price_list_id": pl_id,
        **pl.dict(),
        "items": [],
        "status": "active",
        "item_count": 0,
        "created_time": datetime.now(timezone.utc).isoformat(),
        "updated_time": datetime.now(timezone.utc).isoformat()
    }
    
    # If setting as default, unset other defaults
    if pl.is_default:
        await db.price_lists.update_many(
            {"price_type": pl.price_type, "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    await db.price_lists.insert_one(pl_dict)
    del pl_dict["_id"]
    return {"code": 0, "message": "Price list created", "price_list": pl_dict}


@router.get("/price-lists")
async def list_price_lists(request: Request, price_type: str = "", include_items: bool = True):
    org_id = extract_org_id(request)
    """List all price lists with enriched item data"""
    db = get_db()
    query = {"status": {"$ne": "deleted"}}
    if price_type:
        query["price_type"] = price_type
    
    cursor = db.price_lists.find(query, {"_id": 0}).sort("created_time", -1)
    price_lists = await cursor.to_list(length=100)
    
    if include_items:
        # Enrich items with current item details for real-time sync
        items_cache = {}
        all_item_ids = set()
        for pl in price_lists:
            for item in pl.get("items", []):
                all_item_ids.add(item.get("item_id"))
        
        if all_item_ids:
            items_cursor = db.items.find(
                {"item_id": {"$in": list(all_item_ids)}},
                {"_id": 0, "item_id": 1, "name": 1, "sku": 1, "status": 1, 
                 "is_combo_product": 1, "rate": 1, "item_type": 1, "unit": 1}
            )
            async for item in items_cursor:
                items_cache[item["item_id"]] = item
        
        # Enrich price list items with current item data
        for pl in price_lists:
            enriched_items = []
            for pl_item in pl.get("items", []):
                item_data = items_cache.get(pl_item.get("item_id"), {})
                enriched_item = {
                    **pl_item,
                    "item_name": item_data.get("name", "Unknown"),
                    "sku": item_data.get("sku", ""),
                    "item_status": item_data.get("status", "active"),
                    "is_combo_product": item_data.get("is_combo_product", False),
                    "item_price": item_data.get("rate", 0),
                    "item_type": item_data.get("item_type", "goods"),
                    "unit": item_data.get("unit", "pcs")
                }
                enriched_items.append(enriched_item)
            pl["items"] = enriched_items
            pl["item_count"] = len(enriched_items)
    
    return {"code": 0, "price_lists": price_lists}


@router.get("/price-lists/{pl_id}")
async def get_price_list(request: Request, pl_id: str):
    org_id = extract_org_id(request)
    """Get single price list with enriched item data"""
    db = get_db()
    
    pl = await db.price_lists.find_one({"price_list_id": pl_id}, {"_id": 0})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    # Enrich items with current item details
    items_cache = {}
    item_ids = [item.get("item_id") for item in pl.get("items", [])]
    
    if item_ids:
        items_cursor = db.items.find(
            {"item_id": {"$in": item_ids}},
            {"_id": 0, "item_id": 1, "name": 1, "sku": 1, "status": 1,
             "is_combo_product": 1, "rate": 1, "item_type": 1, "unit": 1}
        )
        async for item in items_cursor:
            items_cache[item["item_id"]] = item
    
    enriched_items = []
    for pl_item in pl.get("items", []):
        item_data = items_cache.get(pl_item.get("item_id"), {})
        enriched_item = {
            **pl_item,
            "item_name": item_data.get("name", "Unknown"),
            "sku": item_data.get("sku", ""),
            "item_status": item_data.get("status", "active"),
            "is_combo_product": item_data.get("is_combo_product", False),
            "item_price": item_data.get("rate", 0),
            "item_type": item_data.get("item_type", "goods"),
            "unit": item_data.get("unit", "pcs")
        }
        enriched_items.append(enriched_item)
    
    pl["items"] = enriched_items
    pl["item_count"] = len(enriched_items)
    
    return {"code": 0, "price_list": pl}


@router.put("/price-lists/{pl_id}")
async def update_price_list(request: Request, pl_id: str, update: PriceListUpdate):
    org_id = extract_org_id(request)
    """Update price list details"""
    db = get_db()
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    # If setting as default, unset other defaults
    if update.is_default:
        pl = await db.price_lists.find_one({"price_list_id": pl_id})
        if pl:
            await db.price_lists.update_many(
                {"price_type": pl.get("price_type"), "is_default": True, "price_list_id": {"$ne": pl_id}},
                {"$set": {"is_default": False}}
            )
    
    result = await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    return {"code": 0, "message": "Price list updated"}


@router.delete("/price-lists/{pl_id}")
async def delete_price_list(request: Request, pl_id: str):
    org_id = extract_org_id(request)
    """Soft delete a price list"""
    db = get_db()
    
    result = await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$set": {"status": "deleted", "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    return {"code": 0, "message": "Price list deleted"}


@router.post("/price-lists/{pl_id}/items")
async def add_item_to_price_list(request: Request, pl_id: str, item_id: str, custom_rate: Optional[float] = None, pricelist_rate: Optional[float] = None, discount: float = 0, discount_type: str = "percentage"):
    org_id = extract_org_id(request)
    """Add item with custom price to price list (Zoho compatible)"""
    db = get_db()
    
    # Use pricelist_rate or custom_rate (backward compatible)
    rate = pricelist_rate if pricelist_rate is not None else custom_rate
    
    # Verify item exists and get its data
    item = await db.items.find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if item already exists in price list
    pl = await db.price_lists.find_one({"price_list_id": pl_id})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    existing_items = pl.get("items", [])
    for i, existing in enumerate(existing_items):
        if existing.get("item_id") == item_id:
            # Update existing item
            existing_items[i] = {
                "item_id": item_id,
                "pricelist_rate": rate,
                "custom_rate": rate,  # Keep for backward compatibility
                "discount": discount,
                "discount_type": discount_type,
                "added_time": existing.get("added_time", datetime.now(timezone.utc).isoformat()),
                "updated_time": datetime.now(timezone.utc).isoformat()
            }
            await db.price_lists.update_one(
                {"price_list_id": pl_id},
                {"$set": {"items": existing_items, "updated_time": datetime.now(timezone.utc).isoformat()}}
            )
            return {"code": 0, "message": "Item updated in price list"}
    
    # Add new item
    new_item = {
        "item_id": item_id,
        "pricelist_rate": rate,
        "custom_rate": rate,  # Keep for backward compatibility
        "discount": discount,
        "discount_type": discount_type,
        "added_time": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {
            "$push": {"items": new_item},
            "$set": {"updated_time": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    return {"code": 0, "message": "Item added to price list"}


@router.put("/price-lists/{pl_id}/items/{item_id}")
async def update_item_in_price_list(request: Request, pl_id: str, item_id: str, pricelist_rate: Optional[float] = None, discount: Optional[float] = None, discount_type: Optional[str] = None):
    org_id = extract_org_id(request)
    """Update item pricing in price list"""
    db = get_db()
    
    pl = await db.price_lists.find_one({"price_list_id": pl_id})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    items = pl.get("items", [])
    item_found = False
    
    for i, item in enumerate(items):
        if item.get("item_id") == item_id:
            if pricelist_rate is not None:
                items[i]["pricelist_rate"] = pricelist_rate
                items[i]["custom_rate"] = pricelist_rate
            if discount is not None:
                items[i]["discount"] = discount
            if discount_type is not None:
                items[i]["discount_type"] = discount_type
            items[i]["updated_time"] = datetime.now(timezone.utc).isoformat()
            item_found = True
            break
    
    if not item_found:
        raise HTTPException(status_code=404, detail="Item not found in price list")
    
    await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$set": {"items": items, "updated_time": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": "Item updated in price list"}

@router.delete("/price-lists/{pl_id}/items/{item_id}")
async def remove_item_from_price_list(request: Request, pl_id: str, item_id: str):
    org_id = extract_org_id(request)
    """Remove item from price list"""
    db = get_db()
    
    result = await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$pull": {"items": {"item_id": item_id}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    return {"code": 0, "message": "Item removed from price list"}

@router.get("/price-lists/{pl_id}/items/{item_id}/rate")
async def get_item_rate_from_price_list(request: Request, pl_id: str, item_id: str):
    org_id = extract_org_id(request)
    """Get item rate from a specific price list"""
    db = get_db()
    
    pl = await db.price_lists.find_one({"price_list_id": pl_id}, {"_id": 0})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    for item in pl.get("items", []):
        if item["item_id"] == item_id:
            return {"code": 0, "rate": item["custom_rate"]}
    
    # Return default item rate
    item = await db.items.find_one({"item_id": item_id}, {"_id": 0})
    if item:
        return {"code": 0, "rate": item.get("rate", 0)}
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.get("/price-lists/{pl_id}/export")
async def export_price_list_csv(request: Request, pl_id: str):
    org_id = extract_org_id(request)
    """Export price list items as CSV (Zoho Books compatible format)"""
    db = get_db()
    
    pl = await db.price_lists.find_one({"price_list_id": pl_id}, {"_id": 0})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    # Get all item details
    item_ids = [item.get("item_id") for item in pl.get("items", [])]
    items_map = {}
    
    if item_ids:
        items_cursor = db.items.find(
            {"item_id": {"$in": item_ids}},
            {"_id": 0}
        )
        async for item in items_cursor:
            items_map[item["item_id"]] = item
    
    # Build CSV - Zoho Books format
    csv_lines = ["Item ID,Item Name,SKU,Status,is_combo_product,Item Price,PriceList Rate,Discount"]
    
    for pl_item in pl.get("items", []):
        item_id = pl_item.get("item_id", "")
        item_data = items_map.get(item_id, {})
        
        row = [
            item_id,
            item_data.get("name", "").replace(",", ";"),  # Escape commas
            item_data.get("sku", ""),
            item_data.get("status", "active"),
            str(item_data.get("is_combo_product", False)).lower(),
            str(item_data.get("rate", 0)),
            str(pl_item.get("pricelist_rate", pl_item.get("custom_rate", 0))),
            str(pl_item.get("discount", 0))
        ]
        csv_lines.append(",".join(row))
    
    csv_content = "\n".join(csv_lines)
    
    headers = {
        "Content-Disposition": f"attachment; filename={pl.get('price_list_name', 'pricelist').replace(' ', '_')}_export.csv",
        "Content-Type": "text/csv"
    }
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers=headers
    )


@router.get("/price-lists/{pl_id}/export/template")
async def get_price_list_import_template(request: Request, pl_id: str):
    org_id = extract_org_id(request)
    """Get CSV template for importing items to price list"""
    
    template = """Item ID,Item Name,SKU,Status,is_combo_product,Item Price,PriceList Rate,Discount
ITEM-001,Sample Product,SKU001,active,false,1000,900,10
ITEM-002,Sample Service,SKU002,active,false,500,450,10"""
    
    headers = {
        "Content-Disposition": "attachment; filename=pricelist_import_template.csv",
        "Content-Type": "text/csv"
    }
    
    return StreamingResponse(
        iter([template]),
        media_type="text/csv",
        headers=headers
    )


@router.post("/price-lists/{pl_id}/import")
async def import_price_list_items(request: Request, pl_id: str):
    org_id = extract_org_id(request)
    """Import items to price list from CSV (Zoho Books compatible format)"""
    db = get_db()
    
    pl = await db.price_lists.find_one({"price_list_id": pl_id})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    body = await request.json()
    csv_data = body.get("csv_data", "")
    
    if not csv_data:
        raise HTTPException(status_code=400, detail="No CSV data provided")
    
    # Parse CSV
    lines = csv_data.strip().split("\n")
    if len(lines) < 2:
        raise HTTPException(status_code=400, detail="CSV must have header and at least one data row")
    
    header = [h.strip().lower().replace(" ", "_") for h in lines[0].split(",")]
    
    # Map header columns
    col_map = {
        "item_id": ["item_id", "item id"],
        "pricelist_rate": ["pricelist_rate", "pricelist rate", "custom_rate", "rate"],
        "discount": ["discount", "discount_percent"]
    }
    
    def get_col_index(field):
        for name in col_map.get(field, [field]):
            if name in header:
                return header.index(name)
        return -1
    
    item_id_idx = get_col_index("item_id")
    rate_idx = get_col_index("pricelist_rate")
    discount_idx = get_col_index("discount")
    
    if item_id_idx == -1:
        raise HTTPException(status_code=400, detail="CSV must have 'Item ID' column")
    
    imported = 0
    errors = []
    
    existing_items = {item.get("item_id"): item for item in pl.get("items", [])}
    
    for i, line in enumerate(lines[1:], start=2):
        try:
            cols = line.split(",")
            item_id = cols[item_id_idx].strip()
            
            if not item_id:
                continue
            
            # Verify item exists
            item = await db.items.find_one({"item_id": item_id})
            if not item:
                errors.append(f"Row {i}: Item {item_id} not found")
                continue
            
            pricelist_rate = float(cols[rate_idx]) if rate_idx >= 0 and len(cols) > rate_idx and cols[rate_idx].strip() else item.get("rate", 0)
            discount = float(cols[discount_idx]) if discount_idx >= 0 and len(cols) > discount_idx and cols[discount_idx].strip() else 0
            
            # Update or add item
            if item_id in existing_items:
                existing_items[item_id]["pricelist_rate"] = pricelist_rate
                existing_items[item_id]["custom_rate"] = pricelist_rate
                existing_items[item_id]["discount"] = discount
                existing_items[item_id]["updated_time"] = datetime.now(timezone.utc).isoformat()
            else:
                existing_items[item_id] = {
                    "item_id": item_id,
                    "pricelist_rate": pricelist_rate,
                    "custom_rate": pricelist_rate,
                    "discount": discount,
                    "discount_type": "percentage",
                    "added_time": datetime.now(timezone.utc).isoformat()
                }
            
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
    
    # Update price list
    await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$set": {
            "items": list(existing_items.values()),
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "code": 0,
        "message": f"Imported {imported} items",
        "imported_count": imported,
        "errors": errors[:10] if errors else []
    }


@router.post("/price-lists/{pl_id}/sync-items")
async def sync_price_list_with_items(request: Request, pl_id: str):
    org_id = extract_org_id(request)
    """Sync price list item data with current Items module data (real-time refresh)"""
    db = get_db()
    
    pl = await db.price_lists.find_one({"price_list_id": pl_id})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    # Get current items for all item_ids in price list
    item_ids = [item.get("item_id") for item in pl.get("items", [])]
    
    if not item_ids:
        return {"code": 0, "message": "No items to sync", "synced_count": 0}
    
    items_map = {}
    items_cursor = db.items.find({"item_id": {"$in": item_ids}}, {"_id": 0})
    async for item in items_cursor:
        items_map[item["item_id"]] = item
    
    # Update price list items with current item data
    updated_items = []
    removed_count = 0
    
    for pl_item in pl.get("items", []):
        item_id = pl_item.get("item_id")
        item_data = items_map.get(item_id)
        
        if not item_data:
            # Item was deleted, remove from price list
            removed_count += 1
            continue
        
        # Keep price list specific data, update synced data
        updated_items.append({
            **pl_item,
            "synced_item_name": item_data.get("name"),
            "synced_sku": item_data.get("sku"),
            "synced_status": item_data.get("status"),
            "synced_item_price": item_data.get("rate"),
            "synced_is_combo": item_data.get("is_combo_product", False),
            "last_synced": datetime.now(timezone.utc).isoformat()
        })
    
    await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$set": {
            "items": updated_items,
            "updated_time": datetime.now(timezone.utc).isoformat(),
            "last_sync_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "code": 0,
        "message": f"Synced {len(updated_items)} items, removed {removed_count} deleted items",
        "synced_count": len(updated_items),
        "removed_count": removed_count
    }


@router.post("/price-lists/{pl_id}/bulk-add")
async def bulk_add_items_to_price_list(request: Request, pl_id: str):
    org_id = extract_org_id(request)
    """Bulk add items to price list with percentage markup/markdown"""
    db = get_db()
    
    pl = await db.price_lists.find_one({"price_list_id": pl_id})
    if not pl:
        raise HTTPException(status_code=404, detail="Price list not found")
    
    body = await request.json()
    item_ids = body.get("item_ids", [])
    percentage_type = body.get("percentage_type", "none")  # markup_percentage, markdown_percentage, none
    percentage_value = body.get("percentage_value", 0)
    
    if not item_ids:
        raise HTTPException(status_code=400, detail="No items provided")
    
    # Get item data
    items_cursor = db.items.find({"item_id": {"$in": item_ids}}, {"_id": 0})
    items_data = {item["item_id"]: item async for item in items_cursor}
    
    existing_items = {item.get("item_id"): item for item in pl.get("items", [])}
    added = 0
    
    for item_id in item_ids:
        item_data = items_data.get(item_id)
        if not item_data:
            continue
        
        base_rate = item_data.get("rate", 0)
        
        # Calculate pricelist rate based on percentage
        if percentage_type == "markup_percentage" and percentage_value > 0:
            pricelist_rate = base_rate * (1 + percentage_value / 100)
        elif percentage_type == "markdown_percentage" and percentage_value > 0:
            pricelist_rate = base_rate * (1 - percentage_value / 100)
        else:
            pricelist_rate = base_rate
        
        if item_id in existing_items:
            existing_items[item_id]["pricelist_rate"] = pricelist_rate
            existing_items[item_id]["custom_rate"] = pricelist_rate
            existing_items[item_id]["updated_time"] = datetime.now(timezone.utc).isoformat()
        else:
            existing_items[item_id] = {
                "item_id": item_id,
                "pricelist_rate": pricelist_rate,
                "custom_rate": pricelist_rate,
                "discount": 0,
                "discount_type": "percentage",
                "added_time": datetime.now(timezone.utc).isoformat()
            }
        added += 1
    
    await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$set": {
            "items": list(existing_items.values()),
            "updated_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"code": 0, "message": f"Added/updated {added} items", "count": added}


# ============== DOCUMENTS/ATTACHMENTS ==============

class DocumentCreate(BaseModel):
    entity_type: str  # invoice, bill, estimate, contact, project, expense
    entity_id: str
    document_name: str
    document_type: str  # pdf, image, doc, xlsx
    file_url: str
    file_size: int = 0
    description: Optional[str] = ""

@router.post("/documents")
async def create_document(request: Request, doc: DocumentCreate):
    org_id = extract_org_id(request)
    """Attach a document to an entity"""
    db = get_db()
    doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
    
    doc_dict = {
        "document_id": doc_id,
        **doc.dict(),
        "uploaded_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(doc_dict)
    del doc_dict["_id"]
    return {"code": 0, "message": "Document attached", "document": doc_dict}

@router.get("/documents")
async def list_documents(request: Request, entity_type: str = "", entity_id: str = ""):
    org_id = extract_org_id(request)
    """List documents"""
    db = get_db()
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    
    cursor = db.documents.find(query, {"_id": 0}).sort("uploaded_time", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "documents": items}

@router.delete("/documents/{doc_id}")
async def delete_document(request: Request, doc_id: str):
    org_id = extract_org_id(request)
    """Delete a document"""
    db = get_db()
    result = await db.documents.delete_one({"document_id": doc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"code": 0, "message": "Document deleted"}

# ============== ORGANIZATION SETTINGS ==============

class OrganizationSettings(BaseModel):
    organization_name: str
    industry_type: Optional[str] = ""
    address: Optional[Dict] = {}
    phone: Optional[str] = ""
    email: Optional[str] = ""
    website: Optional[str] = ""
    fiscal_year_start_month: int = 4  # April
    currency_code: str = "INR"
    time_zone: str = "Asia/Kolkata"
    date_format: str = "dd/MM/yyyy"
    gst_no: Optional[str] = ""
    pan_no: Optional[str] = ""
    tan_no: Optional[str] = ""
    cin: Optional[str] = ""

@router.get("/settings/organization")
async def get_organization_settings(request: Request):
    org_id = extract_org_id(request)
    """Get organization settings"""
    db = get_db()
    settings = await db.organization_settings.find_one({}, {"_id": 0})
    if not settings:
        settings = OrganizationSettings(organization_name="").dict()
    return {"code": 0, "settings": settings}

@router.put("/settings/organization")
async def update_organization_settings(request: Request, settings: OrganizationSettings):
    org_id = extract_org_id(request)
    """Update organization settings"""
    db = get_db()
    await db.organization_settings.update_one(
        {},
        {"$set": settings.dict()},
        upsert=True
    )
    return {"code": 0, "message": "Settings updated"}

# Number Series Settings
class NumberSeriesSettings(BaseModel):
    entity_type: str  # invoice, estimate, salesorder, bill, etc.
    prefix: str
    next_number: int
    suffix: Optional[str] = ""

@router.get("/settings/number-series")
async def get_number_series(request: Request):
    org_id = extract_org_id(request)
    """Get all number series settings"""
    db = get_db()
    cursor = db.number_series.find({}, {"_id": 0})
    items = await cursor.to_list(length=50)
    return {"code": 0, "number_series": items}

@router.put("/settings/number-series/{entity_type}")
async def update_number_series(request: Request, entity_type: str, settings: NumberSeriesSettings):
    org_id = extract_org_id(request)
    """Update number series for an entity type"""
    db = get_db()
    await db.number_series.update_one(
        {"entity_type": entity_type},
        {"$set": settings.dict()},
        upsert=True
    )
    return {"code": 0, "message": "Number series updated"}


# ============== RECURRING EXPENSES ==============

class RecurringExpenseCreate(BaseModel):
    vendor_id: Optional[str] = ""
    vendor_name: Optional[str] = ""
    account_id: str
    account_name: str
    recurrence_name: str
    recurrence_frequency: str = "monthly"
    repeat_every: int = 1
    start_date: str
    end_date: Optional[str] = None
    never_expires: bool = False
    amount: float
    tax_percentage: float = 0
    description: Optional[str] = ""
    is_billable: bool = False
    customer_id: Optional[str] = ""
    project_id: Optional[str] = ""

@router.post("/recurring-expenses")
async def create_recurring_expense(request: Request, re: RecurringExpenseCreate):
    org_id = extract_org_id(request)
    """Create a recurring expense profile"""
    db = get_db()
    re_id = f"RE-{uuid.uuid4().hex[:12].upper()}"
    
    tax_amount = re.amount * (re.tax_percentage / 100)
    total = re.amount + tax_amount
    
    re_dict = {
        "recurring_expense_id": re_id,
        **re.dict(),
        "tax_amount": tax_amount,
        "total": total,
        "next_expense_date": re.start_date,
        "status": "active",
        "expenses_generated": 0,
        "last_expense_date": None,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.recurring_expenses.insert_one(re_dict)
    del re_dict["_id"]
    return {"code": 0, "message": "Recurring expense created", "recurring_expense": re_dict}

@router.get("/recurring-expenses")
async def list_recurring_expenses(request: Request, status: str = "", vendor_id: str = ""):
    org_id = extract_org_id(request)
    """List all recurring expenses"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    cursor = db.recurring_expenses.find(query, {"_id": 0}).sort("created_time", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "recurring_expenses": items}

@router.post("/recurring-expenses/{re_id}/stop")
async def stop_recurring_expense(request: Request, re_id: str):
    org_id = extract_org_id(request)
    """Stop a recurring expense"""
    db = get_db()
    result = await db.recurring_expenses.update_one(
        {"recurring_expense_id": re_id},
        {"$set": {"status": "stopped"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return {"code": 0, "message": "Recurring expense stopped"}

@router.post("/recurring-expenses/{re_id}/resume")
async def resume_recurring_expense(request: Request, re_id: str):
    org_id = extract_org_id(request)
    """Resume a stopped recurring expense"""
    db = get_db()
    result = await db.recurring_expenses.update_one(
        {"recurring_expense_id": re_id},
        {"$set": {"status": "active"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return {"code": 0, "message": "Recurring expense resumed"}

@router.delete("/recurring-expenses/{re_id}")
async def delete_recurring_expense(request: Request, re_id: str):
    org_id = extract_org_id(request)
    """Delete a recurring expense"""
    db = get_db()
    result = await db.recurring_expenses.delete_one({"recurring_expense_id": re_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return {"code": 0, "message": "Recurring expense deleted"}

@router.post("/recurring-expenses/generate")
async def generate_due_expenses(request: Request):
    org_id = extract_org_id(request)
    """Generate expenses for all due recurring profiles"""
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    res = await db.recurring_expenses.find({
        "status": "active",
        "next_expense_date": {"$lte": today}
    }, {"_id": 0}).to_list(length=1000)
    
    generated = 0
    for re in res:
        try:
            expense_id = f"EXP-{uuid.uuid4().hex[:12].upper()}"
            
            expense_dict = {
                "expense_id": expense_id,
                "vendor_id": re.get("vendor_id", ""),
                "vendor_name": re.get("vendor_name", ""),
                "account_id": re["account_id"],
                "account_name": re["account_name"],
                "date": today,
                "amount": re["amount"],
                "tax_percentage": re.get("tax_percentage", 0),
                "tax_amount": re.get("tax_amount", 0),
                "total": re["total"],
                "description": re.get("description", ""),
                "is_billable": re.get("is_billable", False),
                "customer_id": re.get("customer_id", ""),
                "project_id": re.get("project_id", ""),
                "from_recurring_expense_id": re["recurring_expense_id"],
                "status": "unbilled",
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await db.expenses.insert_one(expense_dict)
            
            next_date = calculate_next_date(
                re["next_expense_date"],
                re["recurrence_frequency"],
                re["repeat_every"]
            )
            
            new_status = re["status"]
            if re.get("end_date") and next_date > re["end_date"]:
                new_status = "expired"
            
            await db.recurring_expenses.update_one(
                {"recurring_expense_id": re["recurring_expense_id"]},
                {"$set": {"next_expense_date": next_date, "last_expense_date": today, "status": new_status},
                 "$inc": {"expenses_generated": 1}}
            )
            
            generated += 1
        except Exception as e:
            logger.error(f"Error generating expense for {re['recurring_expense_id']}: {e}")
    
    return {"code": 0, "message": f"Generated {generated} expenses"}

# ============== PROJECT TASKS ==============

class ProjectTaskCreate(BaseModel):
    project_id: str
    task_name: str
    description: Optional[str] = ""
    rate: float = 0
    budget_hours: float = 0
    is_billable: bool = True

@router.post("/projects/{project_id}/tasks")
async def create_project_task(request: Request, project_id: str, task: ProjectTaskCreate):
    org_id = extract_org_id(request)
    """Create a task for a project"""
    db = get_db()
    task_id = f"TSK-{uuid.uuid4().hex[:12].upper()}"
    
    task_dict = {
        "task_id": task_id,
        "project_id": project_id,
        **task.dict(),
        "status": "active",
        "logged_hours": 0,
        "billed_hours": 0,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.project_tasks.insert_one(task_dict)
    del task_dict["_id"]
    return {"code": 0, "message": "Task created", "task": task_dict}

@router.get("/projects/{project_id}/tasks")
async def list_project_tasks(request: Request, project_id: str):
    org_id = extract_org_id(request)
    """List all tasks for a project"""
    db = get_db()
    cursor = db.project_tasks.find({"project_id": project_id}, {"_id": 0})
    items = await cursor.to_list(length=200)
    return {"code": 0, "tasks": items}

@router.put("/projects/{project_id}/tasks/{task_id}")
async def update_project_task(request: Request, project_id: str, task_id: str, task: ProjectTaskCreate):
    org_id = extract_org_id(request)
    """Update a project task"""
    db = get_db()
    result = await db.project_tasks.update_one(
        {"task_id": task_id, "project_id": project_id},
        {"$set": task.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"code": 0, "message": "Task updated"}

@router.delete("/projects/{project_id}/tasks/{task_id}")
async def delete_project_task(request: Request, project_id: str, task_id: str):
    org_id = extract_org_id(request)
    """Delete a project task"""
    db = get_db()
    result = await db.project_tasks.delete_one({"task_id": task_id, "project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"code": 0, "message": "Task deleted"}

# ============== OPENING BALANCES ==============

class OpeningBalanceCreate(BaseModel):
    entity_type: str  # customer, vendor, account
    entity_id: str
    entity_name: str
    opening_balance: float
    as_of_date: str
    notes: Optional[str] = ""

@router.post("/opening-balances")
async def create_opening_balance(request: Request, ob: OpeningBalanceCreate):
    org_id = extract_org_id(request)
    """Set opening balance for a customer, vendor, or account"""
    db = get_db()
    ob_id = f"OB-{uuid.uuid4().hex[:12].upper()}"
    
    ob_dict = {
        "opening_balance_id": ob_id,
        **ob.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.opening_balances.insert_one(ob_dict)
    
    # Update entity's opening balance
    collection_map = {
        "customer": "contacts",
        "vendor": "contacts",
        "account": "chartofaccounts"
    }
    id_field_map = {
        "customer": "contact_id",
        "vendor": "contact_id",
        "account": "account_id"
    }
    
    collection = collection_map.get(ob.entity_type)
    id_field = id_field_map.get(ob.entity_type)
    
    if collection and id_field:
        await db[collection].update_one(
            {id_field: ob.entity_id},
            {"$set": {"opening_balance": ob.opening_balance, "opening_balance_date": ob.as_of_date}}
        )
    
    del ob_dict["_id"]
    return {"code": 0, "message": "Opening balance set", "opening_balance": ob_dict}

@router.get("/opening-balances")
async def list_opening_balances(request: Request, entity_type: str = ""):
    org_id = extract_org_id(request)
    """List all opening balances"""
    db = get_db()
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    
    cursor = db.opening_balances.find(query, {"_id": 0}).sort("as_of_date", -1)
    items = await cursor.to_list(length=500)
    return {"code": 0, "opening_balances": items}

# ============== PAYMENT LINKS ==============

@router.post("/invoices/{invoice_id}/payment-link")
async def generate_payment_link(request: Request, invoice_id: str):
    org_id = extract_org_id(request)
    """Generate a payment link for an invoice"""
    db = get_db()
    
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("balance", 0) <= 0:
        raise HTTPException(status_code=400, detail="Invoice is already paid")
    
    # Generate unique payment token
    payment_token = f"PAY-{uuid.uuid4().hex[:16].upper()}"
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    payment_link_data = {
        "payment_link_id": payment_token,
        "invoice_id": invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "customer_id": invoice.get("customer_id"),
        "customer_name": invoice.get("customer_name"),
        "amount": invoice.get("balance"),
        "currency": "INR",
        "status": "active",
        "expiry_date": expiry_date,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payment_links.insert_one(payment_link_data)
    
    # Update invoice with payment link
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"payment_link_id": payment_token, "has_payment_link": True}}
    )
    
    return {
        "code": 0,
        "message": "Payment link generated",
        "payment_link": {
            "token": payment_token,
            "amount": invoice.get("balance"),
            "expiry_date": expiry_date
        }
    }

@router.get("/payment-links")
async def list_payment_links(request: Request, status: str = "", customer_id: str = ""):
    org_id = extract_org_id(request)
    """List all payment links"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.payment_links.find(query, {"_id": 0}).sort("created_time", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "payment_links": items}

@router.post("/payment-links/{token}/pay")
async def process_payment_link(request: Request, token: str, payment_method: str = "card"):
    org_id = extract_org_id(request)
    """Process payment via payment link (stub for integration)"""
    db = get_db()
    
    link = await db.payment_links.find_one({"payment_link_id": token}, {"_id": 0})
    if not link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    if link.get("status") != "active":
        raise HTTPException(status_code=400, detail="Payment link is not active")
    
    # This is a stub - actual payment processing would integrate with Razorpay/Stripe
    return {
        "code": 0,
        "message": "Payment link is valid. Integrate with payment gateway to process.",
        "invoice_id": link.get("invoice_id"),
        "amount": link.get("amount"),
        "currency": link.get("currency")
    }

# ============== CURRENCY EXCHANGE RATES ==============

class ExchangeRateCreate(BaseModel):
    from_currency: str
    to_currency: str
    rate: float
    effective_date: str

@router.post("/settings/exchange-rates")
async def set_exchange_rate(request: Request, rate: ExchangeRateCreate):
    org_id = extract_org_id(request)
    """Set currency exchange rate"""
    db = get_db()
    rate_id = f"ER-{uuid.uuid4().hex[:8].upper()}"
    
    rate_dict = {
        "exchange_rate_id": rate_id,
        **rate.dict(),
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.exchange_rates.insert_one(rate_dict)
    del rate_dict["_id"]
    return {"code": 0, "message": "Exchange rate set", "exchange_rate": rate_dict}

@router.get("/settings/exchange-rates")
async def list_exchange_rates(request: Request, from_currency: str = "", to_currency: str = ""):
    org_id = extract_org_id(request)
    """List exchange rates"""
    db = get_db()
    query = {}
    if from_currency:
        query["from_currency"] = from_currency
    if to_currency:
        query["to_currency"] = to_currency
    
    cursor = db.exchange_rates.find(query, {"_id": 0}).sort("effective_date", -1)
    items = await cursor.to_list(length=100)
    return {"code": 0, "exchange_rates": items}

# ============== AUDIT TRAIL / ACTIVITY LOG ==============

@router.get("/activity-logs")
async def list_activity_logs(request: Request, entity_type: str = "", entity_id: str = "", user_id: str = "", page: int = 1, per_page: int = 50):
    org_id = extract_org_id(request)
    """List activity logs for audit trail"""
    db = get_db()
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if user_id:
        query["user_id"] = user_id
    
    skip = (page - 1) * per_page
    cursor = db.activity_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(per_page)
    items = await cursor.to_list(length=per_page)
    total = await db.activity_logs.count_documents(query)
    
    return {
        "code": 0,
        "activity_logs": items,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

async def log_activity(db, entity_type: str, entity_id: str, action: str, user_id: str = "", user_name: str = "", details: dict = None):
    """Helper to log activity"""
    log_entry = {
        "log_id": f"LOG-{uuid.uuid4().hex[:12].upper()}",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "user_id": user_id,
        "user_name": user_name,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.activity_logs.insert_one(log_entry)


# ============== SCHEDULED JOBS API ==============

@router.post("/scheduler/run")
async def run_scheduled_jobs(request: Request, background_tasks: BackgroundTasks, job: str = "all"):
    org_id = extract_org_id(request)
    """
    Trigger scheduled jobs manually or via cron.
    Jobs: all, overdue, recurring_invoices, recurring_expenses, reminders
    """
    from services.scheduler import (
        run_all_scheduled_jobs,
        update_overdue_invoices,
        generate_recurring_invoices,
        generate_recurring_expenses,
        send_payment_reminders
    )
    
    async def run_job():
        if job == "all":
            return await run_all_scheduled_jobs()
        elif job == "overdue":
            return await update_overdue_invoices()
        elif job == "recurring_invoices":
            return await generate_recurring_invoices()
        elif job == "recurring_expenses":
            return await generate_recurring_expenses()
        elif job == "reminders":
            return await send_payment_reminders()
        else:
            raise ValueError(f"Unknown job: {job}")
    
    # Run in background for long jobs
    if job == "all":
        background_tasks.add_task(run_job)
        return {"code": 0, "message": "All scheduled jobs started in background"}
    
    # Run immediately for single jobs
    result = await run_job()
    return {"code": 0, "message": f"Job '{job}' completed", "result": result}

@router.get("/scheduler/status")
async def get_scheduler_status(request: Request):
    org_id = extract_org_id(request)
    """Get status of scheduled job executions"""
    db = get_db()
    
    # Get counts of various automated items
    overdue_count = await db.invoices.count_documents({"status": "overdue"})
    active_recurring_invoices = await db.recurring_invoices.count_documents({"status": "active"})
    active_recurring_expenses = await db.recurring_expenses.count_documents({"status": "active"})
    pending_reminders = await db.payment_reminders.count_documents({"status": "queued"})
    
    return {
        "code": 0,
        "status": {
            "overdue_invoices": overdue_count,
            "active_recurring_invoices": active_recurring_invoices,
            "active_recurring_expenses": active_recurring_expenses,
            "pending_payment_reminders": pending_reminders
        },
        "jobs_available": ["all", "overdue", "recurring_invoices", "recurring_expenses", "reminders"],
        "note": "Call POST /api/zoho/scheduler/run?job=<job_name> to trigger"
    }

# ============== RECURRING BILLS ==============

class RecurringBillCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    recurrence_name: str
    recurrence_frequency: str = "monthly"  # weekly, monthly, yearly, custom
    repeat_every: int = 1
    start_date: str
    end_date: Optional[str] = None
    never_expires: bool = False
    line_items: List[Dict]
    payment_terms: int = 30
    notes: Optional[str] = ""

@router.post("/recurring-bills")
async def create_recurring_bill(request: Request, rb: RecurringBillCreate):
    org_id = extract_org_id(request)
    """Create a recurring bill profile"""
    db = get_db()
    rb_id = f"RB-{uuid.uuid4().hex[:12].upper()}"
    
    # Calculate totals
    sub_total = sum(item.get("quantity", 1) * item.get("rate", 0) for item in rb.line_items)
    tax_total = sum(
        item.get("quantity", 1) * item.get("rate", 0) * (item.get("tax_percentage", 0) / 100)
        for item in rb.line_items
    )
    total = sub_total + tax_total
    
    rb_dict = {
        "recurring_bill_id": rb_id,
        "vendor_id": rb.vendor_id,
        "vendor_name": rb.vendor_name,
        "recurrence_name": rb.recurrence_name,
        "recurrence_frequency": rb.recurrence_frequency,
        "repeat_every": rb.repeat_every,
        "start_date": rb.start_date,
        "end_date": rb.end_date,
        "never_expires": rb.never_expires,
        "next_bill_date": rb.start_date,
        "last_bill_date": None,
        "line_items": rb.line_items,
        "sub_total": sub_total,
        "tax_total": tax_total,
        "total": total,
        "payment_terms": rb.payment_terms,
        "notes": rb.notes,
        "status": "active",
        "bills_generated": 0,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.recurring_bills.insert_one(rb_dict)
    return {"code": 0, "message": "Recurring bill created", "recurring_bill": {k: v for k, v in rb_dict.items() if k != "_id"}}

@router.get("/recurring-bills")
async def list_recurring_bills(request: Request, status: str = "", vendor_id: str = ""):
    org_id = extract_org_id(request)
    """List all recurring bills"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    cursor = db.recurring_bills.find(query, {"_id": 0}).sort("created_time", -1)
    items = await cursor.to_list(length=1000)
    return {"code": 0, "recurring_bills": items}

@router.get("/recurring-bills/{rb_id}")
async def get_recurring_bill(request: Request, rb_id: str):
    org_id = extract_org_id(request)
    """Get recurring bill details"""
    db = get_db()
    rb = await db.recurring_bills.find_one({"recurring_bill_id": rb_id}, {"_id": 0})
    if not rb:
        raise HTTPException(status_code=404, detail="Recurring bill not found")
    return {"code": 0, "recurring_bill": rb}

@router.put("/recurring-bills/{rb_id}")
async def update_recurring_bill(request: Request, rb_id: str, update_data: Dict):
    org_id = extract_org_id(request)
    """Update a recurring bill"""
    db = get_db()
    update_data.pop("recurring_bill_id", None)
    update_data.pop("_id", None)
    update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.recurring_bills.update_one(
        {"recurring_bill_id": rb_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring bill not found")
    return {"code": 0, "message": "Recurring bill updated"}

@router.post("/recurring-bills/{rb_id}/stop")
async def stop_recurring_bill(request: Request, rb_id: str):
    org_id = extract_org_id(request)
    """Stop a recurring bill"""
    db = get_db()
    result = await db.recurring_bills.update_one(
        {"recurring_bill_id": rb_id},
        {"$set": {"status": "stopped"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring bill not found")
    return {"code": 0, "message": "Recurring bill stopped"}

@router.post("/recurring-bills/{rb_id}/resume")
async def resume_recurring_bill(request: Request, rb_id: str):
    org_id = extract_org_id(request)
    """Resume a stopped recurring bill"""
    db = get_db()
    result = await db.recurring_bills.update_one(
        {"recurring_bill_id": rb_id},
        {"$set": {"status": "active"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring bill not found")
    return {"code": 0, "message": "Recurring bill resumed"}

@router.delete("/recurring-bills/{rb_id}")
async def delete_recurring_bill(request: Request, rb_id: str):
    org_id = extract_org_id(request)
    """Delete a recurring bill"""
    db = get_db()
    result = await db.recurring_bills.delete_one({"recurring_bill_id": rb_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring bill not found")
    return {"code": 0, "message": "Recurring bill deleted"}

@router.post("/recurring-bills/generate")
async def generate_due_bills(request: Request):
    org_id = extract_org_id(request)
    """Generate bills for all due recurring profiles"""
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    res = await db.recurring_bills.find({
        "status": "active",
        "next_bill_date": {"$lte": today}
    }, {"_id": 0}).to_list(length=1000)
    
    generated = 0
    for rb in res:
        try:
            bill_id = f"BILL-{uuid.uuid4().hex[:12].upper()}"
            
            # Get next bill number
            counter = await db.counters.find_one_and_update(
                {"_id": "bills"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            bill_number = f"BILL-{str(counter['seq']).zfill(6)}"
            
            due_date = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=rb.get("payment_terms", 30))).strftime("%Y-%m-%d")
            
            bill_dict = {
                "bill_id": bill_id,
                "bill_number": bill_number,
                "vendor_id": rb["vendor_id"],
                "vendor_name": rb["vendor_name"],
                "date": today,
                "due_date": due_date,
                "line_items": rb["line_items"],
                "sub_total": rb["sub_total"],
                "tax_total": rb["tax_total"],
                "total": rb["total"],
                "balance_due": rb["total"],
                "status": "open",
                "from_recurring_bill_id": rb["recurring_bill_id"],
                "notes": rb.get("notes", ""),
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await db.bills.insert_one(bill_dict)
            
            next_date = calculate_next_date(
                rb["next_bill_date"],
                rb["recurrence_frequency"],
                rb["repeat_every"]
            )
            
            new_status = rb["status"]
            if rb.get("end_date") and next_date > rb["end_date"]:
                new_status = "expired"
            
            await db.recurring_bills.update_one(
                {"recurring_bill_id": rb["recurring_bill_id"]},
                {"$set": {"next_bill_date": next_date, "last_bill_date": today, "status": new_status},
                 "$inc": {"bills_generated": 1}}
            )
            
            generated += 1
        except Exception as e:
            logger.error(f"Error generating bill for {rb['recurring_bill_id']}: {e}")
    
    return {"code": 0, "message": f"Generated {generated} bills"}

# ============== FIXED ASSETS ==============

ASSET_TYPES = ["furniture", "vehicle", "computer", "equipment", "building", "land", "software", "other"]
DEPRECIATION_METHODS = ["straight_line", "declining_balance", "units_of_production", "sum_of_years"]

class FixedAssetCreate(BaseModel):
    asset_name: str
    asset_type: str = "equipment"
    description: Optional[str] = ""
    purchase_date: str
    purchase_price: float
    useful_life_years: int = 5
    salvage_value: float = 0
    depreciation_method: str = "straight_line"
    asset_account_id: Optional[str] = ""
    depreciation_account_id: Optional[str] = ""
    location: Optional[str] = ""
    serial_number: Optional[str] = ""
    warranty_expiry: Optional[str] = None

@router.post("/fixed-assets")
async def create_fixed_asset(request: Request, asset: FixedAssetCreate):
    org_id = extract_org_id(request)
    """Create a fixed asset"""
    db = get_db()
    asset_id = f"FA-{uuid.uuid4().hex[:12].upper()}"
    
    # Get next asset number
    counter = await db.counters.find_one_and_update(
        {"_id": "fixed_assets"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    asset_number = f"ASSET-{str(counter['seq']).zfill(6)}"
    
    # Calculate annual depreciation (straight line default)
    depreciable_value = asset.purchase_price - asset.salvage_value
    annual_depreciation = depreciable_value / asset.useful_life_years if asset.useful_life_years > 0 else 0
    
    asset_dict = {
        "asset_id": asset_id,
        "asset_number": asset_number,
        "asset_name": asset.asset_name,
        "asset_type": asset.asset_type,
        "description": asset.description,
        "purchase_date": asset.purchase_date,
        "purchase_price": asset.purchase_price,
        "useful_life_years": asset.useful_life_years,
        "salvage_value": asset.salvage_value,
        "depreciation_method": asset.depreciation_method,
        "depreciable_value": depreciable_value,
        "annual_depreciation": annual_depreciation,
        "accumulated_depreciation": 0,
        "book_value": asset.purchase_price,
        "asset_account_id": asset.asset_account_id,
        "depreciation_account_id": asset.depreciation_account_id,
        "location": asset.location,
        "serial_number": asset.serial_number,
        "warranty_expiry": asset.warranty_expiry,
        "status": "active",
        "depreciation_entries": [],
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.fixed_assets.insert_one(asset_dict)
    return {"code": 0, "message": "Fixed asset created", "fixed_asset": {k: v for k, v in asset_dict.items() if k != "_id"}}

@router.get("/fixed-assets")
async def list_fixed_assets(request: Request, status: str = "", asset_type: str = "", page: int = 1, per_page: int = 50):
    org_id = extract_org_id(request)
    """List all fixed assets"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if asset_type:
        query["asset_type"] = asset_type
    
    skip = (page - 1) * per_page
    cursor = db.fixed_assets.find(query, {"_id": 0}).sort("created_time", -1).skip(skip).limit(per_page)
    assets = await cursor.to_list(length=per_page)
    total = await db.fixed_assets.count_documents(query)
    
    return {
        "code": 0,
        "fixed_assets": assets,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/fixed-assets/summary")
async def get_fixed_assets_summary(request: Request):
    org_id = extract_org_id(request)
    """Get summary of fixed assets"""
    db = get_db()
    
    total_count = await db.fixed_assets.count_documents(org_query(org_id))
    active_count = await db.fixed_assets.count_documents({"status": "active"})
    disposed_count = await db.fixed_assets.count_documents({"status": "disposed"})
    
    # Aggregate values
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": None,
            "total_purchase_value": {"$sum": "$purchase_price"},
            "total_book_value": {"$sum": "$book_value"},
            "total_accumulated_depreciation": {"$sum": "$accumulated_depreciation"}
        }}
    ]
    
    result = await db.fixed_assets.aggregate(pipeline).to_list(length=1)
    values = result[0] if result else {
        "total_purchase_value": 0,
        "total_book_value": 0,
        "total_accumulated_depreciation": 0
    }
    
    # By type breakdown
    type_pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": "$asset_type",
            "count": {"$sum": 1},
            "total_value": {"$sum": "$book_value"}
        }}
    ]
    by_type = await db.fixed_assets.aggregate(type_pipeline).to_list(length=100)
    
    return {
        "code": 0,
        "summary": {
            "total_assets": total_count,
            "active_assets": active_count,
            "disposed_assets": disposed_count,
            "total_purchase_value": values.get("total_purchase_value", 0),
            "total_book_value": values.get("total_book_value", 0),
            "total_accumulated_depreciation": values.get("total_accumulated_depreciation", 0),
            "by_type": by_type
        }
    }

@router.get("/fixed-assets/{asset_id}")
async def get_fixed_asset(request: Request, asset_id: str):
    org_id = extract_org_id(request)
    """Get fixed asset details"""
    db = get_db()
    asset = await db.fixed_assets.find_one({"asset_id": asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    return {"code": 0, "fixed_asset": asset}

@router.put("/fixed-assets/{asset_id}")
async def update_fixed_asset(request: Request, asset_id: str, update_data: Dict):
    org_id = extract_org_id(request)
    """Update a fixed asset"""
    db = get_db()
    update_data.pop("asset_id", None)
    update_data.pop("_id", None)
    update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.fixed_assets.update_one(
        {"asset_id": asset_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    return {"code": 0, "message": "Fixed asset updated"}

@router.delete("/fixed-assets/{asset_id}")
async def delete_fixed_asset(request: Request, asset_id: str):
    org_id = extract_org_id(request)
    """Delete a fixed asset"""
    db = get_db()
    result = await db.fixed_assets.delete_one({"asset_id": asset_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    return {"code": 0, "message": "Fixed asset deleted"}

@router.post("/fixed-assets/{asset_id}/depreciate")
async def record_depreciation(request: Request, asset_id: str, period: str = "", amount: Optional[float] = None):
    org_id = extract_org_id(request)
    """Record depreciation for an asset"""
    db = get_db()
    
    asset = await db.fixed_assets.find_one({"asset_id": asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    
    if asset["status"] != "active":
        raise HTTPException(status_code=400, detail="Cannot depreciate non-active asset")
    
    # Use provided amount or calculate based on method
    if amount is None:
        amount = asset["annual_depreciation"] / 12  # Monthly depreciation
    
    # Check if would exceed depreciable value
    new_accumulated = asset["accumulated_depreciation"] + amount
    if new_accumulated > asset["depreciable_value"]:
        amount = asset["depreciable_value"] - asset["accumulated_depreciation"]
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Asset is fully depreciated")
    
    new_book_value = asset["purchase_price"] - new_accumulated
    
    # Create depreciation entry
    entry = {
        "entry_id": f"DEP-{uuid.uuid4().hex[:8].upper()}",
        "period": period or datetime.now(timezone.utc).strftime("%Y-%m"),
        "amount": amount,
        "accumulated_after": new_accumulated,
        "book_value_after": new_book_value,
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    # Check if fully depreciated
    new_status = "active"
    if new_book_value <= asset["salvage_value"]:
        new_status = "fully_depreciated"
    
    await db.fixed_assets.update_one(
        {"asset_id": asset_id},
        {
            "$set": {
                "accumulated_depreciation": new_accumulated,
                "book_value": new_book_value,
                "status": new_status
            },
            "$push": {"depreciation_entries": entry}
        }
    )
    
    return {"code": 0, "message": "Depreciation recorded", "entry": entry}

@router.post("/fixed-assets/{asset_id}/dispose")
async def dispose_asset(request: Request, asset_id: str, disposal_date: str, disposal_amount: float, reason: str = ""):
    org_id = extract_org_id(request)
    """Dispose/sell a fixed asset"""
    db = get_db()
    
    asset = await db.fixed_assets.find_one({"asset_id": asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    
    if asset["status"] in ["disposed", "written_off"]:
        raise HTTPException(status_code=400, detail="Asset already disposed")
    
    gain_loss = disposal_amount - asset["book_value"]
    
    await db.fixed_assets.update_one(
        {"asset_id": asset_id},
        {"$set": {
            "status": "disposed",
            "disposal_date": disposal_date,
            "disposal_amount": disposal_amount,
            "disposal_gain_loss": gain_loss,
            "disposal_reason": reason,
            "disposed_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "code": 0,
        "message": "Asset disposed",
        "disposal": {
            "book_value": asset["book_value"],
            "disposal_amount": disposal_amount,
            "gain_loss": gain_loss
        }
    }

@router.post("/fixed-assets/{asset_id}/write-off")
async def write_off_asset(request: Request, asset_id: str, reason: str = ""):
    org_id = extract_org_id(request)
    """Write off a fixed asset"""
    db = get_db()
    
    asset = await db.fixed_assets.find_one({"asset_id": asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    
    if asset["status"] in ["disposed", "written_off"]:
        raise HTTPException(status_code=400, detail="Asset already disposed/written off")
    
    await db.fixed_assets.update_one(
        {"asset_id": asset_id},
        {"$set": {
            "status": "written_off",
            "write_off_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "write_off_reason": reason,
            "write_off_amount": asset["book_value"],
            "book_value": 0,
            "written_off_time": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "code": 0,
        "message": "Asset written off",
        "write_off_amount": asset["book_value"]
    }

# ============== CUSTOM MODULES ==============

class CustomModuleCreate(BaseModel):
    module_name: str
    module_label: str
    description: Optional[str] = ""
    fields: List[Dict]  # [{name, label, type, required, options}]
    icon: Optional[str] = "folder"

@router.post("/custom-modules")
async def create_custom_module(request: Request, module: CustomModuleCreate):
    org_id = extract_org_id(request)
    """Create a custom module definition"""
    db = get_db()
    module_id = f"CM-{uuid.uuid4().hex[:12].upper()}"
    
    # Validate field types
    valid_types = ["text", "number", "decimal", "date", "datetime", "email", "phone", "url", "textarea", "dropdown", "checkbox", "lookup"]
    for field in module.fields:
        if field.get("type") not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid field type: {field.get('type')}")
    
    module_dict = {
        "module_id": module_id,
        "module_name": module.module_name.lower().replace(" ", "_"),
        "module_label": module.module_label,
        "description": module.description,
        "fields": module.fields,
        "icon": module.icon,
        "is_active": True,
        "records_count": 0,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_modules.insert_one(module_dict)
    return {"code": 0, "message": "Custom module created", "custom_module": {k: v for k, v in module_dict.items() if k != "_id"}}

@router.get("/custom-modules")
async def list_custom_modules(request: Request, is_active: bool = True):
    org_id = extract_org_id(request)
    """List all custom modules"""
    db = get_db()
    query = {"is_active": is_active} if is_active else {}
    cursor = db.custom_modules.find(query, {"_id": 0}).sort("created_time", -1)
    modules = await cursor.to_list(length=100)
    return {"code": 0, "custom_modules": modules}

@router.get("/custom-modules/{module_id}")
async def get_custom_module(request: Request, module_id: str):
    org_id = extract_org_id(request)
    """Get custom module definition"""
    db = get_db()
    module = await db.custom_modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Custom module not found")
    return {"code": 0, "custom_module": module}

@router.put("/custom-modules/{module_id}")
async def update_custom_module(request: Request, module_id: str, update_data: Dict):
    org_id = extract_org_id(request)
    """Update a custom module"""
    db = get_db()
    update_data.pop("module_id", None)
    update_data.pop("_id", None)
    update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.custom_modules.update_one(
        {"module_id": module_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Custom module not found")
    return {"code": 0, "message": "Custom module updated"}

@router.delete("/custom-modules/{module_id}")
async def delete_custom_module(request: Request, module_id: str):
    org_id = extract_org_id(request)
    """Deactivate a custom module (soft delete)"""
    db = get_db()
    result = await db.custom_modules.update_one(
        {"module_id": module_id},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Custom module not found")
    return {"code": 0, "message": "Custom module deactivated"}

@router.post("/custom-modules/{module_id}/records")
async def create_custom_record(request: Request, module_id: str, record_data: Dict):
    org_id = extract_org_id(request)
    """Create a record in a custom module"""
    db = get_db()
    
    module = await db.custom_modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Custom module not found")
    
    # Validate required fields
    for field in module["fields"]:
        if field.get("required") and not record_data.get(field["name"]):
            raise HTTPException(status_code=400, detail=f"Field '{field['name']}' is required")
    
    record_id = f"REC-{uuid.uuid4().hex[:12].upper()}"
    collection_name = f"custom_{module['module_name']}"
    
    record_dict = {
        "record_id": record_id,
        "module_id": module_id,
        **record_data,
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db[collection_name].insert_one(record_dict)
    
    # Update records count
    await db.custom_modules.update_one(
        {"module_id": module_id},
        {"$inc": {"records_count": 1}}
    )
    
    return {"code": 0, "message": "Record created", "record": {k: v for k, v in record_dict.items() if k != "_id"}}

@router.get("/custom-modules/{module_id}/records")
async def list_custom_records(request: Request, module_id: str, page: int = 1, per_page: int = 50, search: str = ""):
    org_id = extract_org_id(request)
    """List records in a custom module"""
    db = get_db()
    
    module = await db.custom_modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Custom module not found")
    
    collection_name = f"custom_{module['module_name']}"
    query = {"module_id": module_id}
    
    if search:
        # Search in text fields
        text_fields = [f["name"] for f in module["fields"] if f.get("type") in ["text", "textarea", "email"]]
        if text_fields:
            query["$or"] = [{f: {"$regex": search, "$options": "i"}} for f in text_fields]
    
    skip = (page - 1) * per_page
    cursor = db[collection_name].find(query, {"_id": 0}).sort("created_time", -1).skip(skip).limit(per_page)
    records = await cursor.to_list(length=per_page)
    total = await db[collection_name].count_documents(query)
    
    return {
        "code": 0,
        "records": records,
        "page_context": {"page": page, "per_page": per_page, "total": total}
    }

@router.get("/custom-modules/{module_id}/records/{record_id}")
async def get_custom_record(request: Request, module_id: str, record_id: str):
    org_id = extract_org_id(request)
    """Get a specific record"""
    db = get_db()
    
    module = await db.custom_modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Custom module not found")
    
    collection_name = f"custom_{module['module_name']}"
    record = await db[collection_name].find_one({"record_id": record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return {"code": 0, "record": record}

@router.put("/custom-modules/{module_id}/records/{record_id}")
async def update_custom_record(request: Request, module_id: str, record_id: str, update_data: Dict):
    org_id = extract_org_id(request)
    """Update a record in a custom module"""
    db = get_db()
    
    module = await db.custom_modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Custom module not found")
    
    collection_name = f"custom_{module['module_name']}"
    update_data.pop("record_id", None)
    update_data.pop("_id", None)
    update_data["updated_time"] = datetime.now(timezone.utc).isoformat()
    
    result = await db[collection_name].update_one(
        {"record_id": record_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return {"code": 0, "message": "Record updated"}

@router.delete("/custom-modules/{module_id}/records/{record_id}")
async def delete_custom_record(request: Request, module_id: str, record_id: str):
    org_id = extract_org_id(request)
    """Delete a record from a custom module"""
    db = get_db()
    
    module = await db.custom_modules.find_one({"module_id": module_id}, {"_id": 0})
    if not module:
        raise HTTPException(status_code=404, detail="Custom module not found")
    
    collection_name = f"custom_{module['module_name']}"
    result = await db[collection_name].delete_one({"record_id": record_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Update records count
    await db.custom_modules.update_one(
        {"module_id": module_id},
        {"$inc": {"records_count": -1}}
    )
    
    return {"code": 0, "message": "Record deleted"}
