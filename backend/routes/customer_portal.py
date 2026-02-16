"""
Customer Portal Routes
======================
Read-only views + simple actions for customers.
Strict RBAC: customer sees only their own data.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
import os
import uuid

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

router = APIRouter(prefix="/customer", tags=["Customer Portal"])

# ==================== MODELS ====================

class AMCPlan(BaseModel):
    """AMC Plan template (admin-configurable)"""
    plan_id: str = Field(default_factory=lambda: f"amc_plan_{uuid.uuid4().hex[:8]}")
    name: str
    description: Optional[str] = None
    tier: str = "basic"  # basic, plus, premium (stored as data, not constants)
    duration_months: int = 12
    price: float
    services_included: List[dict] = []  # [{service_id, service_name, quantity}]
    max_service_visits: int = 4
    includes_parts: bool = False
    parts_discount_percent: float = 0.0
    priority_support: bool = False
    roadside_assistance: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AMCSubscription(BaseModel):
    """Customer's AMC subscription"""
    subscription_id: str = Field(default_factory=lambda: f"amc_sub_{uuid.uuid4().hex[:12]}")
    plan_id: str
    plan_name: str
    customer_id: str
    customer_name: str
    vehicle_id: str
    vehicle_number: str
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    services_used: int = 0
    max_services: int = 4
    status: str = "active"  # active, expiring, expired, cancelled
    amount_paid: float = 0.0
    payment_status: str = "pending"  # pending, paid, partial
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    renewed_from: Optional[str] = None  # Previous subscription_id if renewed

class ServiceHistoryItem(BaseModel):
    """Service history view model"""
    ticket_id: str
    vehicle_number: str
    vehicle_model: Optional[str] = None
    title: str
    status: str
    priority: str
    created_at: str
    resolved_at: Optional[str] = None
    technician_name: Optional[str] = None
    total_cost: float = 0.0
    invoice_id: Optional[str] = None

class PaymentDue(BaseModel):
    """Outstanding payment view model"""
    invoice_id: str
    invoice_number: str
    ticket_id: Optional[str] = None
    vehicle_number: Optional[str] = None
    amount: float
    amount_paid: float = 0.0
    balance_due: float
    due_date: Optional[str] = None
    status: str
    created_at: str

# ==================== AUTH HELPERS ====================

async def get_current_user_from_request(request: Request):
    """Extract current user from request (reuse main auth)"""
    import jwt
    JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
    
    # Try session token first
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            if user:
                return user
    
    # Try JWT token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
        except:
            pass
    return None

async def require_customer(request: Request):
    """Require authenticated customer (not admin/technician for customer portal)"""
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Customer portal is for customers, but admins can also view for support
    if user.get("role") not in ["customer", "admin"]:
        raise HTTPException(status_code=403, detail="Customer portal access required")
    return user

async def require_any_authenticated(request: Request):
    """Require any authenticated user"""
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ==================== CUSTOMER DASHBOARD ====================

@router.get("/dashboard")
async def get_customer_dashboard(request: Request):
    """Get customer portal dashboard summary"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    # Get customer's vehicles
    vehicles = await db.vehicles.find(
        {"owner_id": customer_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get active tickets
    active_tickets = await db.tickets.count_documents({
        "customer_id": customer_id,
        "status": {"$nin": ["closed", "resolved"]}
    })
    
    # Get total service history
    total_services = await db.tickets.count_documents({
        "customer_id": customer_id
    })
    
    # Get pending payments
    pending_invoices = await db.invoices.find({
        "customer_id": customer_id,
        "payment_status": {"$in": ["pending", "partial"]}
    }, {"_id": 0, "total_amount": 1, "amount_paid": 1}).to_list(100)
    
    total_pending = sum(
        (inv.get("total_amount", 0) - inv.get("amount_paid", 0)) 
        for inv in pending_invoices
    )
    
    # Get active AMC subscriptions
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    active_amc = await db.amc_subscriptions.count_documents({
        "customer_id": customer_id,
        "status": {"$in": ["active", "expiring"]},
        "end_date": {"$gte": today}
    })
    
    return {
        "vehicles_count": len(vehicles),
        "active_tickets": active_tickets,
        "total_services": total_services,
        "pending_amount": total_pending,
        "active_amc_plans": active_amc,
        "customer_name": user.get("name", ""),
        "customer_email": user.get("email", "")
    }

# ==================== MY VEHICLES ====================

@router.get("/vehicles")
async def get_my_vehicles(request: Request):
    """Get customer's registered vehicles"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    vehicles = await db.vehicles.find(
        {"owner_id": customer_id},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with service stats
    for vehicle in vehicles:
        vehicle_id = vehicle.get("vehicle_id")
        
        # Count services
        service_count = await db.tickets.count_documents({"vehicle_id": vehicle_id})
        vehicle["total_services"] = service_count
        
        # Last service date
        last_ticket = await db.tickets.find_one(
            {"vehicle_id": vehicle_id},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", -1)]
        )
        vehicle["last_service_date"] = last_ticket.get("created_at") if last_ticket else None
        
        # Check AMC status
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        amc = await db.amc_subscriptions.find_one({
            "vehicle_id": vehicle_id,
            "status": {"$in": ["active", "expiring"]},
            "end_date": {"$gte": today}
        }, {"_id": 0, "plan_name": 1, "end_date": 1, "status": 1})
        vehicle["amc_plan"] = amc
    
    return vehicles

# ==================== SERVICE HISTORY ====================

@router.get("/service-history")
async def get_service_history(
    request: Request,
    vehicle_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get customer's service history with status timeline"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    query = {"customer_id": customer_id}
    if vehicle_id:
        query["vehicle_id"] = vehicle_id
    if status:
        query["status"] = status
    
    tickets = await db.tickets.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    history = []
    for ticket in tickets:
        # Get invoice if exists
        invoice = await db.invoices.find_one(
            {"ticket_id": ticket["ticket_id"]},
            {"_id": 0, "invoice_id": 1, "total_amount": 1}
        )
        
        history.append({
            "ticket_id": ticket.get("ticket_id"),
            "vehicle_number": ticket.get("vehicle_number", "N/A"),
            "vehicle_model": ticket.get("vehicle_model"),
            "title": ticket.get("title"),
            "description": ticket.get("description"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at"),
            "resolved_at": ticket.get("resolved_at"),
            "technician_name": ticket.get("assigned_technician_name"),
            "total_cost": ticket.get("final_amount", ticket.get("estimated_cost", 0)),
            "invoice_id": invoice.get("invoice_id") if invoice else None,
            "status_history": ticket.get("status_history", [])
        })
    
    return history

@router.get("/service-history/{ticket_id}")
async def get_service_detail(ticket_id: str, request: Request):
    """Get detailed service ticket view with timeline"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    ticket = await db.tickets.find_one(
        {"ticket_id": ticket_id, "customer_id": customer_id},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")
    
    # Get invoice
    invoice = await db.invoices.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )
    
    # Get status history (timeline)
    status_history = ticket.get("status_history", [])
    
    return {
        **ticket,
        "invoice": invoice,
        "timeline": status_history
    }

# ==================== INVOICES ====================

@router.get("/invoices")
async def get_my_invoices(
    request: Request,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get customer's invoices"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    query = {"customer_id": customer_id}
    if status:
        query["payment_status"] = status
    
    invoices = await db.invoices.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return invoices

@router.get("/invoices/{invoice_id}")
async def get_invoice_detail(invoice_id: str, request: Request):
    """Get invoice detail (for download/view)"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "customer_id": customer_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

# ==================== PAYMENTS DUE ====================

@router.get("/payments-due")
async def get_payments_due(request: Request):
    """Get outstanding payments"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    invoices = await db.invoices.find({
        "customer_id": customer_id,
        "payment_status": {"$in": ["pending", "partial"]}
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    payments_due = []
    for inv in invoices:
        total = inv.get("total_amount", 0)
        paid = inv.get("amount_paid", 0)
        balance = total - paid
        
        if balance > 0:
            payments_due.append({
                "invoice_id": inv.get("invoice_id"),
                "invoice_number": inv.get("invoice_number"),
                "ticket_id": inv.get("ticket_id"),
                "vehicle_number": inv.get("vehicle_number"),
                "amount": total,
                "amount_paid": paid,
                "balance_due": balance,
                "due_date": inv.get("due_date"),
                "status": inv.get("payment_status"),
                "created_at": inv.get("created_at")
            })
    
    return {
        "payments": payments_due,
        "total_due": sum(p["balance_due"] for p in payments_due)
    }

# ==================== AMC SUBSCRIPTIONS ====================

@router.get("/amc")
async def get_my_amc_subscriptions(request: Request):
    """Get customer's AMC subscriptions"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    subscriptions = await db.amc_subscriptions.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Update status based on dates
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for sub in subscriptions:
        end_date = sub.get("end_date", "")
        if end_date:
            if end_date < today:
                sub["status"] = "expired"
            elif end_date <= (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d"):
                sub["status"] = "expiring"
            else:
                sub["status"] = "active" if sub.get("status") != "cancelled" else "cancelled"
    
    return subscriptions

@router.get("/amc/{subscription_id}")
async def get_amc_detail(subscription_id: str, request: Request):
    """Get AMC subscription detail with usage"""
    user = await require_customer(request)
    customer_id = user["user_id"]
    
    subscription = await db.amc_subscriptions.find_one(
        {"subscription_id": subscription_id, "customer_id": customer_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="AMC subscription not found")
    
    # Get the plan details
    plan = await db.amc_plans.find_one(
        {"plan_id": subscription.get("plan_id")},
        {"_id": 0}
    )
    
    # Get services used under this AMC
    services_used = await db.tickets.find({
        "vehicle_id": subscription.get("vehicle_id"),
        "amc_subscription_id": subscription_id
    }, {"_id": 0, "ticket_id": 1, "title": 1, "created_at": 1, "status": 1}).to_list(100)
    
    return {
        **subscription,
        "plan_details": plan,
        "services_history": services_used
    }

@router.get("/amc-plans")
async def get_available_amc_plans(request: Request):
    """Get available AMC plans for purchase"""
    user = await require_customer(request)
    
    plans = await db.amc_plans.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    return plans

# ==================== SIMPLE ACTIONS ====================

@router.post("/request-callback")
async def request_callback(request: Request):
    """Request a callback from service team"""
    user = await require_customer(request)
    body = await request.json()
    
    callback_request = {
        "request_id": f"cb_{uuid.uuid4().hex[:12]}",
        "customer_id": user["user_id"],
        "customer_name": user.get("name"),
        "customer_email": user.get("email"),
        "customer_phone": body.get("phone"),
        "reason": body.get("reason", "General inquiry"),
        "preferred_time": body.get("preferred_time"),
        "vehicle_id": body.get("vehicle_id"),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.callback_requests.insert_one(callback_request)
    
    return {"message": "Callback request submitted", "request_id": callback_request["request_id"]}

@router.post("/request-appointment")
async def request_appointment(request: Request):
    """Request service appointment"""
    user = await require_customer(request)
    body = await request.json()
    
    appointment = {
        "appointment_id": f"apt_{uuid.uuid4().hex[:12]}",
        "customer_id": user["user_id"],
        "customer_name": user.get("name"),
        "vehicle_id": body.get("vehicle_id"),
        "service_type": body.get("service_type"),
        "preferred_date": body.get("preferred_date"),
        "preferred_time": body.get("preferred_time"),
        "notes": body.get("notes"),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment)
    
    return {"message": "Appointment request submitted", "appointment_id": appointment["appointment_id"]}
