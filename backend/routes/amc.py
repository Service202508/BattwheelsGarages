"""
AMC (Annual Maintenance Contract) Routes
========================================
Admin routes for managing AMC plans and subscriptions.
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

router = APIRouter(prefix="/amc", tags=["AMC Management"])

# ==================== MODELS ====================

class AMCPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tier: str = "basic"
    duration_months: int = 12
    price: float
    services_included: List[dict] = []
    max_service_visits: int = 4
    includes_parts: bool = False
    parts_discount_percent: float = 0.0
    priority_support: bool = False
    roadside_assistance: bool = False

class AMCPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tier: Optional[str] = None
    duration_months: Optional[int] = None
    price: Optional[float] = None
    services_included: Optional[List[dict]] = None
    max_service_visits: Optional[int] = None
    includes_parts: Optional[bool] = None
    parts_discount_percent: Optional[float] = None
    priority_support: Optional[bool] = None
    roadside_assistance: Optional[bool] = None
    is_active: Optional[bool] = None

class AMCSubscriptionCreate(BaseModel):
    plan_id: str
    customer_id: str
    vehicle_id: str
    start_date: Optional[str] = None  # Defaults to today
    amount_paid: float = 0.0
    payment_status: str = "pending"
    notes: Optional[str] = None

# ==================== AUTH HELPERS ====================

async def get_current_user_from_request(request: Request):
    """Extract current user from request"""
    import jwt
    JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
    
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            if user:
                return user
    
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

async def require_admin(request: Request):
    """Require admin access"""
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_admin_or_technician(request: Request):
    """Require admin or technician access"""
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.get("role") not in ["admin", "technician"]:
        raise HTTPException(status_code=403, detail="Admin or technician access required")
    return user

# ==================== AMC PLANS (Admin) ====================

@router.post("/plans")
async def create_amc_plan(plan_data: AMCPlanCreate, request: Request):
    """Create a new AMC plan (admin only)"""
    user = await require_admin(request)
    
    plan = {
        "plan_id": f"amc_plan_{uuid.uuid4().hex[:8]}",
        "name": plan_data.name,
        "description": plan_data.description,
        "tier": plan_data.tier,
        "duration_months": plan_data.duration_months,
        "price": plan_data.price,
        "services_included": plan_data.services_included,
        "max_service_visits": plan_data.max_service_visits,
        "includes_parts": plan_data.includes_parts,
        "parts_discount_percent": plan_data.parts_discount_percent,
        "priority_support": plan_data.priority_support,
        "roadside_assistance": plan_data.roadside_assistance,
        "is_active": True,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.amc_plans.insert_one(plan)
    if "_id" in plan:
        del plan["_id"]
    
    return plan

@router.get("/plans")
async def get_amc_plans(request: Request, include_inactive: bool = False):
    """Get all AMC plans"""
    user = await require_admin_or_technician(request)
    
    query = {} if include_inactive else {"is_active": True}
    plans = await db.amc_plans.find(query, {"_id": 0}).to_list(100)
    
    # Add subscription count for each plan
    for plan in plans:
        plan["active_subscriptions"] = await db.amc_subscriptions.count_documents({
            "plan_id": plan["plan_id"],
            "status": {"$in": ["active", "expiring"]}
        })
    
    return plans

@router.get("/plans/{plan_id}")
async def get_amc_plan(plan_id: str, request: Request):
    """Get AMC plan details"""
    user = await require_admin_or_technician(request)
    
    plan = await db.amc_plans.find_one({"plan_id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="AMC plan not found")
    
    return plan

@router.put("/plans/{plan_id}")
async def update_amc_plan(plan_id: str, update_data: AMCPlanUpdate, request: Request):
    """Update AMC plan (admin only)"""
    user = await require_admin(request)
    
    plan = await db.amc_plans.find_one({"plan_id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="AMC plan not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_dict["updated_by"] = user["user_id"]
    
    await db.amc_plans.update_one(
        {"plan_id": plan_id},
        {"$set": update_dict}
    )
    
    updated_plan = await db.amc_plans.find_one({"plan_id": plan_id}, {"_id": 0})
    return updated_plan

@router.delete("/plans/{plan_id}")
async def deactivate_amc_plan(plan_id: str, request: Request):
    """Deactivate AMC plan (soft delete)"""
    user = await require_admin(request)
    
    result = await db.amc_plans.update_one(
        {"plan_id": plan_id},
        {"$set": {"is_active": False, "deactivated_by": user["user_id"]}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="AMC plan not found")
    
    return {"message": "AMC plan deactivated"}

# ==================== AMC SUBSCRIPTIONS ====================

@router.post("/subscriptions")
async def create_amc_subscription(sub_data: AMCSubscriptionCreate, request: Request):
    """Create a new AMC subscription for a customer"""
    user = await require_admin_or_technician(request)
    
    # Get plan details
    plan = await db.amc_plans.find_one({"plan_id": sub_data.plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="AMC plan not found")
    
    # Get customer details
    customer = await db.users.find_one({"user_id": sub_data.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get vehicle details
    vehicle = await db.vehicles.find_one({"vehicle_id": sub_data.vehicle_id}, {"_id": 0})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Calculate dates
    start_date = sub_data.start_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=plan["duration_months"] * 30)
    end_date = end_dt.strftime("%Y-%m-%d")
    
    subscription = {
        "subscription_id": f"amc_sub_{uuid.uuid4().hex[:12]}",
        "plan_id": plan["plan_id"],
        "plan_name": plan["name"],
        "plan_tier": plan.get("tier", "basic"),
        "customer_id": customer["user_id"],
        "customer_name": customer.get("name", ""),
        "customer_email": customer.get("email", ""),
        "vehicle_id": vehicle["vehicle_id"],
        "vehicle_number": vehicle.get("registration_number", ""),
        "vehicle_model": f"{vehicle.get('make', '')} {vehicle.get('model', '')}",
        "start_date": start_date,
        "end_date": end_date,
        "duration_months": plan["duration_months"],
        "services_used": 0,
        "max_services": plan["max_service_visits"],
        "services_included": plan.get("services_included", []),
        "includes_parts": plan.get("includes_parts", False),
        "parts_discount_percent": plan.get("parts_discount_percent", 0),
        "status": "active",
        "amount": plan["price"],
        "amount_paid": sub_data.amount_paid,
        "payment_status": sub_data.payment_status,
        "notes": sub_data.notes,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.amc_subscriptions.insert_one(subscription)
    del subscription["_id"] if "_id" in subscription else None
    
    return subscription

@router.get("/subscriptions")
async def get_amc_subscriptions(
    request: Request,
    customer_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get AMC subscriptions with filters"""
    user = await require_admin_or_technician(request)
    
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if vehicle_id:
        query["vehicle_id"] = vehicle_id
    if status:
        query["status"] = status
    
    subscriptions = await db.amc_subscriptions.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Update status based on dates
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for sub in subscriptions:
        end_date = sub.get("end_date", "")
        if end_date and sub.get("status") not in ["cancelled"]:
            if end_date < today:
                sub["status"] = "expired"
            elif end_date <= (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d"):
                sub["status"] = "expiring"
    
    return subscriptions

@router.get("/subscriptions/{subscription_id}")
async def get_amc_subscription(subscription_id: str, request: Request):
    """Get AMC subscription details"""
    user = await require_admin_or_technician(request)
    
    subscription = await db.amc_subscriptions.find_one(
        {"subscription_id": subscription_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="AMC subscription not found")
    
    # Get usage history
    services_used = await db.tickets.find({
        "amc_subscription_id": subscription_id
    }, {"_id": 0, "ticket_id": 1, "title": 1, "created_at": 1, "status": 1}).to_list(100)
    
    subscription["usage_history"] = services_used
    
    return subscription

@router.put("/subscriptions/{subscription_id}/use-service")
async def record_amc_service_usage(subscription_id: str, request: Request):
    """Record a service usage against AMC subscription"""
    user = await require_admin_or_technician(request)
    body = await request.json()
    
    subscription = await db.amc_subscriptions.find_one(
        {"subscription_id": subscription_id},
        {"_id": 0}
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="AMC subscription not found")
    
    if subscription.get("status") in ["expired", "cancelled"]:
        raise HTTPException(status_code=400, detail="AMC subscription is no longer active")
    
    if subscription.get("services_used", 0) >= subscription.get("max_services", 0):
        raise HTTPException(status_code=400, detail="All AMC services have been used")
    
    # Increment usage
    await db.amc_subscriptions.update_one(
        {"subscription_id": subscription_id},
        {
            "$inc": {"services_used": 1},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # If ticket_id provided, link it to the AMC
    if body.get("ticket_id"):
        await db.tickets.update_one(
            {"ticket_id": body["ticket_id"]},
            {"$set": {"amc_subscription_id": subscription_id, "amc_covered": True}}
        )
    
    return {"message": "Service usage recorded", "services_used": subscription["services_used"] + 1}

@router.put("/subscriptions/{subscription_id}/cancel")
async def cancel_amc_subscription(subscription_id: str, request: Request):
    """Cancel AMC subscription"""
    user = await require_admin(request)
    body = await request.json()
    
    result = await db.amc_subscriptions.update_one(
        {"subscription_id": subscription_id},
        {
            "$set": {
                "status": "cancelled",
                "cancelled_by": user["user_id"],
                "cancelled_at": datetime.now(timezone.utc).isoformat(),
                "cancellation_reason": body.get("reason", "")
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="AMC subscription not found")
    
    return {"message": "AMC subscription cancelled"}

@router.post("/subscriptions/{subscription_id}/renew")
async def renew_amc_subscription(subscription_id: str, request: Request):
    """Renew an expiring/expired AMC subscription"""
    user = await require_admin_or_technician(request)
    body = await request.json()
    
    old_subscription = await db.amc_subscriptions.find_one(
        {"subscription_id": subscription_id},
        {"_id": 0}
    )
    
    if not old_subscription:
        raise HTTPException(status_code=404, detail="AMC subscription not found")
    
    # Get the plan (might want to use same or different plan)
    plan_id = body.get("plan_id", old_subscription["plan_id"])
    plan = await db.amc_plans.find_one({"plan_id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="AMC plan not found")
    
    # Calculate new dates
    start_date = body.get("start_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=plan["duration_months"] * 30)
    
    new_subscription = {
        "subscription_id": f"amc_sub_{uuid.uuid4().hex[:12]}",
        "plan_id": plan["plan_id"],
        "plan_name": plan["name"],
        "plan_tier": plan.get("tier", "basic"),
        "customer_id": old_subscription["customer_id"],
        "customer_name": old_subscription["customer_name"],
        "customer_email": old_subscription.get("customer_email", ""),
        "vehicle_id": old_subscription["vehicle_id"],
        "vehicle_number": old_subscription["vehicle_number"],
        "vehicle_model": old_subscription.get("vehicle_model", ""),
        "start_date": start_date,
        "end_date": end_dt.strftime("%Y-%m-%d"),
        "duration_months": plan["duration_months"],
        "services_used": 0,
        "max_services": plan["max_service_visits"],
        "services_included": plan.get("services_included", []),
        "includes_parts": plan.get("includes_parts", False),
        "parts_discount_percent": plan.get("parts_discount_percent", 0),
        "status": "active",
        "amount": plan["price"],
        "amount_paid": body.get("amount_paid", 0),
        "payment_status": body.get("payment_status", "pending"),
        "renewed_from": subscription_id,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.amc_subscriptions.insert_one(new_subscription)
    
    # Mark old subscription as renewed
    await db.amc_subscriptions.update_one(
        {"subscription_id": subscription_id},
        {"$set": {"renewed_to": new_subscription["subscription_id"]}}
    )
    
    del new_subscription["_id"] if "_id" in new_subscription else None
    return new_subscription

# ==================== ANALYTICS ====================

@router.get("/analytics")
async def get_amc_analytics(request: Request):
    """Get AMC analytics for admin dashboard"""
    user = await require_admin(request)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expiring_threshold = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d")
    
    # Counts
    total_active = await db.amc_subscriptions.count_documents({
        "status": "active",
        "end_date": {"$gte": today}
    })
    
    expiring_soon = await db.amc_subscriptions.count_documents({
        "end_date": {"$gte": today, "$lte": expiring_threshold}
    })
    
    expired = await db.amc_subscriptions.count_documents({
        "end_date": {"$lt": today}
    })
    
    # Revenue
    pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_paid"}}}
    ]
    revenue_result = await db.amc_subscriptions.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Plan distribution
    plan_pipeline = [
        {"$match": {"status": {"$in": ["active", "expiring"]}}},
        {"$group": {"_id": "$plan_name", "count": {"$sum": 1}}}
    ]
    plan_dist = await db.amc_subscriptions.aggregate(plan_pipeline).to_list(100)
    
    return {
        "total_active": total_active,
        "expiring_soon": expiring_soon,
        "expired": expired,
        "total_revenue": total_revenue,
        "plan_distribution": {p["_id"]: p["count"] for p in plan_dist if p["_id"]}
    }
