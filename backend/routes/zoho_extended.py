"""
Zoho Books Extended Features
Recurring Transactions, Delivery Challans, Retainer Invoices, Projects, Taxes, etc.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import logging

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
async def create_recurring_invoice(ri: RecurringInvoiceCreate):
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
async def list_recurring_invoices(status: str = "", customer_id: str = ""):
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
async def get_recurring_invoice(ri_id: str):
    """Get recurring invoice details"""
    db = get_db()
    ri = await db.recurring_invoices.find_one({"recurring_invoice_id": ri_id}, {"_id": 0})
    if not ri:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")
    return {"code": 0, "recurring_invoice": ri}

@router.post("/recurring-invoices/{ri_id}/stop")
async def stop_recurring_invoice(ri_id: str):
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
async def resume_recurring_invoice(ri_id: str):
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
async def delete_recurring_invoice(ri_id: str):
    """Delete a recurring invoice"""
    db = get_db()
    result = await db.recurring_invoices.delete_one({"recurring_invoice_id": ri_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")
    return {"code": 0, "message": "Recurring invoice deleted"}

@router.post("/recurring-invoices/generate")
async def generate_due_invoices():
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
async def create_delivery_challan(dc: DeliveryChallanCreate):
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
async def list_delivery_challans(status: str = "", customer_id: str = ""):
    """List all delivery challans"""
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    
    cursor = db.delivery_challans.find(query, {"_id": 0}).sort("date", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "delivery_challans": items}

@router.get("/delivery-challans/{dc_id}")
async def get_delivery_challan(dc_id: str):
    """Get delivery challan details"""
    db = get_db()
    dc = await db.delivery_challans.find_one({"delivery_challan_id": dc_id}, {"_id": 0})
    if not dc:
        raise HTTPException(status_code=404, detail="Delivery challan not found")
    return {"code": 0, "delivery_challan": dc}

@router.post("/delivery-challans/{dc_id}/status/delivered")
async def mark_challan_delivered(dc_id: str):
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
async def convert_challan_to_invoice(dc_id: str):
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
async def create_retainer_invoice(ri: RetainerInvoiceCreate):
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
async def list_retainer_invoices(status: str = "", customer_id: str = ""):
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
async def apply_retainer_to_invoice(ri_id: str, invoice_id: str, amount: float):
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
async def create_project(project: ProjectCreate):
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
async def list_projects(status: str = "", customer_id: str = ""):
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
async def get_project(project_id: str):
    """Get project details"""
    db = get_db()
    project = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"code": 0, "project": project}

@router.put("/projects/{project_id}")
async def update_project(project_id: str, project: ProjectCreate):
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
async def update_project_status(project_id: str, status: str):
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
async def create_time_entry(entry: TimeEntryCreate):
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
async def list_time_entries(project_id: str = "", user_id: str = "", is_billed: str = ""):
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
async def delete_time_entry(entry_id: str):
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
async def create_tax(tax: TaxCreate):
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
async def list_taxes():
    """List all taxes"""
    db = get_db()
    cursor = db.taxes.find({"status": "active"}, {"_id": 0})
    items = await cursor.to_list(length=100)
    return {"code": 0, "taxes": items}

@router.put("/taxes/{tax_id}")
async def update_tax(tax_id: str, tax: TaxCreate):
    """Update tax"""
    db = get_db()
    result = await db.taxes.update_one({"tax_id": tax_id}, {"$set": tax.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tax not found")
    return {"code": 0, "message": "Tax updated"}

@router.delete("/taxes/{tax_id}")
async def delete_tax(tax_id: str):
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
async def create_tax_group(group: TaxGroupCreate):
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
async def list_tax_groups():
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
async def create_reminder_template(reminder: PaymentReminderCreate):
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
async def list_reminder_templates():
    """List all reminder templates"""
    db = get_db()
    cursor = db.payment_reminder_templates.find({}, {"_id": 0})
    items = await cursor.to_list(length=50)
    return {"code": 0, "reminder_templates": items}

@router.post("/payment-reminders/send")
async def send_payment_reminders():
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
        except:
            continue
    
    return {"code": 0, "message": f"Sent {reminders_sent} payment reminders"}

@router.get("/payment-reminders/history")
async def get_reminder_history(invoice_id: str = "", customer_id: str = ""):
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
async def create_inventory_adjustment(adj: InventoryAdjustmentCreate):
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
async def list_inventory_adjustments(reason: str = ""):
    """List all inventory adjustments"""
    db = get_db()
    query = {}
    if reason:
        query["reason"] = reason
    
    cursor = db.inventory_adjustments.find(query, {"_id": 0}).sort("date", -1)
    items = await cursor.to_list(length=200)
    return {"code": 0, "inventory_adjustments": items}

@router.get("/inventory-adjustments/{adj_id}")
async def get_inventory_adjustment(adj_id: str):
    """Get inventory adjustment details"""
    db = get_db()
    adj = await db.inventory_adjustments.find_one({"adjustment_id": adj_id}, {"_id": 0})
    if not adj:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    return {"code": 0, "adjustment": adj}

# ============== PRICE LISTS ==============

class PriceListCreate(BaseModel):
    price_list_name: str
    description: Optional[str] = ""
    currency_code: str = "INR"
    price_type: str = "sales"  # sales, purchase
    is_default: bool = False
    round_off_to: str = "never"  # never, nearest_1, nearest_5, nearest_10

@router.post("/price-lists")
async def create_price_list(pl: PriceListCreate):
    """Create a price list"""
    db = get_db()
    pl_id = f"PL-{uuid.uuid4().hex[:12].upper()}"
    
    pl_dict = {
        "price_list_id": pl_id,
        **pl.dict(),
        "items": [],
        "status": "active",
        "created_time": datetime.now(timezone.utc).isoformat()
    }
    
    await db.price_lists.insert_one(pl_dict)
    del pl_dict["_id"]
    return {"code": 0, "message": "Price list created", "price_list": pl_dict}

@router.get("/price-lists")
async def list_price_lists(price_type: str = ""):
    """List all price lists"""
    db = get_db()
    query = {"status": "active"}
    if price_type:
        query["price_type"] = price_type
    
    cursor = db.price_lists.find(query, {"_id": 0})
    items = await cursor.to_list(length=100)
    return {"code": 0, "price_lists": items}

@router.post("/price-lists/{pl_id}/items")
async def add_item_to_price_list(pl_id: str, item_id: str, custom_rate: float):
    """Add item with custom price to price list"""
    db = get_db()
    
    result = await db.price_lists.update_one(
        {"price_list_id": pl_id},
        {"$push": {"items": {"item_id": item_id, "custom_rate": custom_rate}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price list not found")
    return {"code": 0, "message": "Item added to price list"}

@router.delete("/price-lists/{pl_id}/items/{item_id}")
async def remove_item_from_price_list(pl_id: str, item_id: str):
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
async def get_item_rate_from_price_list(pl_id: str, item_id: str):
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
async def create_document(doc: DocumentCreate):
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
async def list_documents(entity_type: str = "", entity_id: str = ""):
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
async def delete_document(doc_id: str):
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
async def get_organization_settings():
    """Get organization settings"""
    db = get_db()
    settings = await db.organization_settings.find_one({}, {"_id": 0})
    if not settings:
        settings = OrganizationSettings(organization_name="").dict()
    return {"code": 0, "settings": settings}

@router.put("/settings/organization")
async def update_organization_settings(settings: OrganizationSettings):
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
async def get_number_series():
    """Get all number series settings"""
    db = get_db()
    cursor = db.number_series.find({}, {"_id": 0})
    items = await cursor.to_list(length=50)
    return {"code": 0, "number_series": items}

@router.put("/settings/number-series/{entity_type}")
async def update_number_series(entity_type: str, settings: NumberSeriesSettings):
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
async def create_recurring_expense(re: RecurringExpenseCreate):
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
async def list_recurring_expenses(status: str = "", vendor_id: str = ""):
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
async def stop_recurring_expense(re_id: str):
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
async def resume_recurring_expense(re_id: str):
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
async def delete_recurring_expense(re_id: str):
    """Delete a recurring expense"""
    db = get_db()
    result = await db.recurring_expenses.delete_one({"recurring_expense_id": re_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return {"code": 0, "message": "Recurring expense deleted"}

@router.post("/recurring-expenses/generate")
async def generate_due_expenses():
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
async def create_project_task(project_id: str, task: ProjectTaskCreate):
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
async def list_project_tasks(project_id: str):
    """List all tasks for a project"""
    db = get_db()
    cursor = db.project_tasks.find({"project_id": project_id}, {"_id": 0})
    items = await cursor.to_list(length=200)
    return {"code": 0, "tasks": items}

@router.put("/projects/{project_id}/tasks/{task_id}")
async def update_project_task(project_id: str, task_id: str, task: ProjectTaskCreate):
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
async def delete_project_task(project_id: str, task_id: str):
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
async def create_opening_balance(ob: OpeningBalanceCreate):
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
async def list_opening_balances(entity_type: str = ""):
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
async def generate_payment_link(invoice_id: str):
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
async def list_payment_links(status: str = "", customer_id: str = ""):
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
async def process_payment_link(token: str, payment_method: str = "card"):
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
async def set_exchange_rate(rate: ExchangeRateCreate):
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
async def list_exchange_rates(from_currency: str = "", to_currency: str = ""):
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
async def list_activity_logs(entity_type: str = "", entity_id: str = "", user_id: str = "", page: int = 1, per_page: int = 50):
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
