"""
Battwheels OS - Business Customer Portal API Routes
Fleet management, bulk operations, and organization-level access
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import jwt
import os
import uuid

def get_db():
    from server import db
    return db

router = APIRouter(prefix="/business", tags=["Business Portal"])

SECRET_KEY = os.environ.get("JWT_SECRET", "battwheels-secret")
ALGORITHM = "HS256"


async def get_business_customer(request: Request):
    """Extract business customer info from token"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        # Allow both business_customer and customer roles with business type
        if role not in ["business_customer", "customer"]:
            raise HTTPException(status_code=403, detail="Business customer access required")
        
        db = get_db()
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Get business/organization info
        business = await db.business_customers.find_one(
            {"$or": [{"user_id": user_id}, {"admin_user_id": user_id}]},
            {"_id": 0}
        )
        
        return user, business
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==================== REGISTRATION ====================

class BusinessRegistration(BaseModel):
    business_name: str
    business_type: str  # fleet, oem, dealer, corporate
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str
    contact_name: str
    contact_email: str
    contact_phone: str
    fleet_size: Optional[int] = None
    vehicle_categories: List[str] = []

@router.post("/register")
async def register_business(data: BusinessRegistration):
    """Register a new business customer"""
    db = get_db()
    
    # Check if business already exists
    existing = await db.business_customers.find_one({"gst_number": data.gst_number})
    if existing:
        raise HTTPException(status_code=400, detail="Business with this GST number already registered")
    
    now = datetime.now(timezone.utc)
    business_id = f"biz_{uuid.uuid4().hex[:12]}"
    
    # Create user account for business admin
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    # Check if user email exists
    existing_user = await db.users.find_one({"email": data.contact_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered. Please login.")
    
    business_doc = {
        "business_id": business_id,
        "business_name": data.business_name,
        "business_type": data.business_type,
        "gst_number": data.gst_number,
        "pan_number": data.pan_number,
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "pincode": data.pincode,
        "contact_name": data.contact_name,
        "contact_email": data.contact_email,
        "contact_phone": data.contact_phone,
        "fleet_size": data.fleet_size,
        "vehicle_categories": data.vehicle_categories,
        "admin_user_id": user_id,
        "status": "pending_verification",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.business_customers.insert_one(business_doc)
    
    # Create associated customer record
    customer_doc = {
        "customer_id": business_id,
        "name": data.business_name,
        "type": "business",
        "business_type": data.business_type,
        "gst_number": data.gst_number,
        "contact_name": data.contact_name,
        "email": data.contact_email,
        "phone": data.contact_phone,
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "pincode": data.pincode,
        "business_id": business_id,
        "is_active": True,
        "created_at": now.isoformat()
    }
    await db.customers.insert_one(customer_doc)
    
    return {
        "message": "Business registration submitted for verification",
        "business_id": business_id,
        "status": "pending_verification"
    }


# ==================== DASHBOARD ====================

@router.get("/dashboard")
async def get_business_dashboard(request: Request):
    """Get business customer dashboard data"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    business_id = business["business_id"]
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get all vehicles in fleet
    fleet_count = await db.vehicles.count_documents({"business_id": business_id})
    
    # Get ticket stats
    ticket_filter = {"business_id": business_id}
    
    open_tickets = await db.tickets.count_documents({**ticket_filter, "status": {"$in": ["open", "assigned", "technician_assigned"]}})
    in_progress = await db.tickets.count_documents({**ticket_filter, "status": "work_in_progress"})
    pending_estimate = await db.tickets.count_documents({**ticket_filter, "status": {"$in": ["estimate_sent"]}})
    resolved_month = await db.tickets.count_documents({
        **ticket_filter,
        "status": {"$in": ["resolved", "closed", "work_completed"]},
        "updated_at": {"$gte": month_start.isoformat()}
    })
    total_tickets = await db.tickets.count_documents(ticket_filter)
    
    # Calculate average resolution TAT
    resolved_tickets = await db.tickets.find(
        {
            **ticket_filter,
            "status": {"$in": ["resolved", "closed", "work_completed"]},
            "resolved_at": {"$exists": True}
        },
        {"_id": 0, "created_at": 1, "resolved_at": 1}
    ).sort("resolved_at", -1).limit(50).to_list(50)
    
    avg_tat_hours = 0
    if resolved_tickets:
        total_hours = 0
        for t in resolved_tickets:
            try:
                created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(t["resolved_at"].replace("Z", "+00:00"))
                total_hours += (resolved - created).total_seconds() / 3600
            except:
                pass
        avg_tat_hours = round(total_hours / len(resolved_tickets), 1)
    
    # Invoice stats
    total_invoiced = 0
    total_paid = 0
    total_pending = 0
    
    invoices = await db.invoices.find(
        {"customer_id": business_id},
        {"_id": 0, "total": 1, "balance": 1, "status": 1}
    ).to_list(1000)
    
    for inv in invoices:
        total_invoiced += inv.get("total", 0)
        if inv.get("status") == "paid":
            total_paid += inv.get("total", 0)
        else:
            total_pending += inv.get("balance", 0)
    
    # AMC stats
    active_amcs = await db.amc_contracts.count_documents({
        "customer_id": business_id,
        "status": "active"
    })
    
    return {
        "business": {
            "business_id": business_id,
            "name": business.get("business_name"),
            "type": business.get("business_type"),
            "status": business.get("status")
        },
        "fleet": {
            "total_vehicles": fleet_count,
            "active_services": open_tickets + in_progress
        },
        "tickets": {
            "open": open_tickets,
            "in_progress": in_progress,
            "pending_estimate_approval": pending_estimate,
            "resolved_this_month": resolved_month,
            "total": total_tickets
        },
        "resolution_tat_hours": avg_tat_hours,
        "financials": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "pending_payment": total_pending
        },
        "amc": {
            "active_contracts": active_amcs
        }
    }


# ==================== FLEET MANAGEMENT ====================

@router.get("/fleet")
async def get_fleet(request: Request, status: Optional[str] = None):
    """Get all vehicles in the fleet"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    query = {"business_id": business["business_id"]}
    if status:
        query["status"] = status
    
    vehicles = await db.vehicles.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with service status
    for vehicle in vehicles:
        active_ticket = await db.tickets.find_one(
            {
                "vehicle_number": vehicle.get("vehicle_number"),
                "status": {"$nin": ["closed", "resolved", "work_completed"]}
            },
            {"_id": 0, "ticket_id": 1, "status": 1, "title": 1}
        )
        vehicle["active_service"] = active_ticket
    
    return {"vehicles": vehicles, "total": len(vehicles)}

class FleetVehicleAdd(BaseModel):
    vehicle_number: str
    vehicle_category: str
    vehicle_model_id: Optional[str] = None
    vehicle_model_name: str
    vehicle_oem: str
    year_of_manufacture: Optional[int] = None
    chassis_number: Optional[str] = None
    battery_serial: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None

@router.post("/fleet")
async def add_fleet_vehicle(request: Request, data: FleetVehicleAdd):
    """Add a vehicle to the fleet"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    now = datetime.now(timezone.utc)
    
    # Check if vehicle already exists
    existing = await db.vehicles.find_one({"vehicle_number": data.vehicle_number.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Vehicle already registered")
    
    vehicle_doc = {
        "vehicle_id": f"veh_{uuid.uuid4().hex[:12]}",
        "vehicle_number": data.vehicle_number.upper(),
        "vehicle_category": data.vehicle_category,
        "vehicle_model_id": data.vehicle_model_id,
        "vehicle_model": data.vehicle_model_name,
        "vehicle_oem": data.vehicle_oem,
        "year_of_manufacture": data.year_of_manufacture,
        "chassis_number": data.chassis_number,
        "battery_serial": data.battery_serial,
        "driver_name": data.driver_name,
        "driver_phone": data.driver_phone,
        "business_id": business["business_id"],
        "customer_id": business["business_id"],
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.vehicles.insert_one(vehicle_doc)
    del vehicle_doc["_id"]
    
    # Update fleet size
    await db.business_customers.update_one(
        {"business_id": business["business_id"]},
        {"$inc": {"fleet_size": 1}}
    )
    
    return vehicle_doc

@router.delete("/fleet/{vehicle_id}")
async def remove_fleet_vehicle(request: Request, vehicle_id: str):
    """Remove a vehicle from the fleet"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    result = await db.vehicles.delete_one({
        "vehicle_id": vehicle_id,
        "business_id": business["business_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Update fleet size
    await db.business_customers.update_one(
        {"business_id": business["business_id"]},
        {"$inc": {"fleet_size": -1}}
    )
    
    return {"message": "Vehicle removed from fleet"}


# ==================== TICKETS ====================

@router.get("/tickets")
async def get_business_tickets(request: Request, status: Optional[str] = None, vehicle_number: Optional[str] = None, limit: int = 50, skip: int = 0):
    """Get all tickets for the business"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    query = {"business_id": business["business_id"]}
    
    if status:
        if status == "active":
            query["status"] = {"$in": ["open", "assigned", "technician_assigned", "work_in_progress", "estimate_sent"]}
        elif status == "completed":
            query["status"] = {"$in": ["work_completed", "closed", "resolved"]}
        else:
            query["status"] = status
    
    if vehicle_number:
        query["vehicle_number"] = {"$regex": vehicle_number, "$options": "i"}
    
    tickets = await db.tickets.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.tickets.count_documents(query)
    
    return {"tickets": tickets, "total": total}

class BusinessTicketCreate(BaseModel):
    vehicle_number: str
    title: str
    description: str
    issue_type: str
    priority: str = "medium"
    resolution_type: str = "workshop"
    incident_location: Optional[str] = None

@router.post("/tickets")
async def create_business_ticket(request: Request, data: BusinessTicketCreate):
    """Create a service ticket for a fleet vehicle"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    # Verify vehicle belongs to fleet
    vehicle = await db.vehicles.find_one({
        "vehicle_number": data.vehicle_number.upper(),
        "business_id": business["business_id"]
    }, {"_id": 0})
    
    if not vehicle:
        raise HTTPException(status_code=400, detail="Vehicle not found in your fleet")
    
    # Get organization_id from business or default org
    organization_id = business.get("organization_id")
    if not organization_id:
        default_org = await db.organizations.find_one(
            {"$or": [{"is_default": True}, {"slug": "battwheels-default"}]},
            {"_id": 0, "organization_id": 1}
        )
        organization_id = default_org.get("organization_id") if default_org else None
    
    now = datetime.now(timezone.utc)
    ticket_id = f"tkt_{uuid.uuid4().hex[:12]}"
    
    ticket_doc = {
        "ticket_id": ticket_id,
        "organization_id": organization_id,  # Link to organization
        "title": data.title,
        "description": data.description,
        "category": data.issue_type,
        "issue_type": data.issue_type,
        "priority": data.priority,
        "status": "open",
        "vehicle_number": data.vehicle_number.upper(),
        "vehicle_category": vehicle.get("vehicle_category"),
        "vehicle_model": vehicle.get("vehicle_model"),
        "vehicle_oem": vehicle.get("vehicle_oem"),
        "customer_type": "business",
        "customer_id": business["business_id"],
        "customer_name": business["business_name"],
        "business_id": business["business_id"],
        "resolution_type": data.resolution_type,
        "incident_location": data.incident_location,
        "source": "business_portal",
        "created_by": user["user_id"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "status_history": [{
            "status": "open",
            "timestamp": now.isoformat(),
            "notes": "Ticket created via business portal"
        }]
    }
    
    await db.tickets.insert_one(ticket_doc)
    del ticket_doc["_id"]
    
    return ticket_doc


# ==================== INVOICES & PAYMENTS ====================

@router.get("/invoices")
async def get_business_invoices(request: Request, status: Optional[str] = None, limit: int = 50, skip: int = 0):
    """Get all invoices for the business"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    query = {"customer_id": business["business_id"]}
    if status:
        query["status"] = status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.invoices.count_documents(query)
    
    # Calculate totals
    all_invoices = await db.invoices.find(
        {"customer_id": business["business_id"]},
        {"_id": 0, "total": 1, "balance": 1, "status": 1}
    ).to_list(1000)
    
    total_amount = sum(inv.get("total", 0) for inv in all_invoices)
    pending_amount = sum(inv.get("balance", 0) for inv in all_invoices if inv.get("status") != "paid")
    
    return {
        "invoices": invoices,
        "total_count": total,
        "summary": {
            "total_invoiced": total_amount,
            "pending_payment": pending_amount
        }
    }

class BulkPaymentRequest(BaseModel):
    invoice_ids: List[str]
    payment_method: str = "razorpay"

@router.post("/invoices/bulk-payment")
async def initiate_bulk_payment(request: Request, data: BulkPaymentRequest):
    """Initiate bulk payment for multiple invoices"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    # Get all invoices
    invoices = await db.invoices.find(
        {
            "invoice_id": {"$in": data.invoice_ids},
            "customer_id": business["business_id"],
            "status": {"$ne": "paid"}
        },
        {"_id": 0}
    ).to_list(100)
    
    if len(invoices) != len(data.invoice_ids):
        raise HTTPException(status_code=400, detail="Some invoices not found or already paid")
    
    total_amount = sum(inv.get("balance", 0) for inv in invoices)
    
    # Create Razorpay order
    from services.razorpay_service import create_razorpay_order
    
    receipt = f"BULK-{business['business_id'][-6:]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    order = await create_razorpay_order(
        amount_inr=total_amount,
        receipt=receipt,
        notes={
            "business_id": business["business_id"],
            "invoice_ids": ",".join(data.invoice_ids),
            "payment_type": "bulk"
        }
    )
    
    return {
        "order_id": order["id"],
        "amount": total_amount,
        "amount_paise": int(total_amount * 100),
        "currency": "INR",
        "invoice_count": len(invoices),
        "invoices": [{"invoice_id": inv["invoice_id"], "amount": inv.get("balance", 0)} for inv in invoices],
        "is_mock": order.get("_mock", False)
    }


# ==================== AMC ====================

@router.get("/amc")
async def get_business_amc(request: Request):
    """Get AMC contracts for the business"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    contracts = await db.amc_contracts.find(
        {"customer_id": business["business_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Get available plans
    plans = await db.amc_plans.find({"is_active": True}, {"_id": 0}).to_list(20)
    
    return {"contracts": contracts, "available_plans": plans}


# ==================== REPORTS ====================

@router.get("/reports/summary")
async def get_business_report_summary(request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get summary report for the business"""
    user, business = await get_business_customer(request)
    db = get_db()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    # Default to current month
    now = datetime.now(timezone.utc)
    if not start_date:
        start_date = now.replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")
    
    business_id = business["business_id"]
    
    # Ticket stats
    tickets = await db.tickets.find(
        {
            "business_id": business_id,
            "created_at": {"$gte": f"{start_date}T00:00:00", "$lte": f"{end_date}T23:59:59"}
        },
        {"_id": 0, "status": 1, "priority": 1, "vehicle_number": 1, "created_at": 1, "resolved_at": 1}
    ).to_list(1000)
    
    # Group by status
    status_breakdown = {}
    priority_breakdown = {}
    vehicle_breakdown = {}
    
    for t in tickets:
        status = t.get("status", "unknown")
        priority = t.get("priority", "medium")
        vehicle = t.get("vehicle_number", "unknown")
        
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
        priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
        vehicle_breakdown[vehicle] = vehicle_breakdown.get(vehicle, 0) + 1
    
    # Invoice stats
    invoices = await db.invoices.find(
        {
            "customer_id": business_id,
            "date": {"$gte": start_date, "$lte": end_date}
        },
        {"_id": 0, "total": 1, "balance": 1, "status": 1}
    ).to_list(1000)
    
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_paid = sum(inv.get("total", 0) - inv.get("balance", 0) for inv in invoices)
    
    return {
        "period": {"start": start_date, "end": end_date},
        "tickets": {
            "total": len(tickets),
            "by_status": status_breakdown,
            "by_priority": priority_breakdown,
            "by_vehicle": dict(sorted(vehicle_breakdown.items(), key=lambda x: x[1], reverse=True)[:10])
        },
        "financials": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "outstanding": total_invoiced - total_paid
        }
    }
