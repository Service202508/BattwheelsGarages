from utils.auth import require_auth, create_token, hash_password
"""
Battwheels OS - Entity CRUD Routes (extracted from server.py)
Users, Technicians, Suppliers, Vehicles, Customers
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from utils.auth import create_access_token, decode_token, hash_password, verify_password
from schemas.models import (
    UserUpdate, Supplier, SupplierCreate, SupplierUpdate,
    Vehicle, VehicleCreate, Customer, CustomerCreate, CustomerUpdate,
)
from core.tenant.context import TenantContext, tenant_context_required

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Entity CRUD"])
db = None

def init_router(database):
    global db
    db = database

@router.get("/users")
async def get_users(request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    await require_admin(request)
    # Return only users who are members of this organisation (not all platform users)
    memberships = await db.organization_users.find(
        {"organization_id": ctx.org_id, "status": "active"},
        {"user_id": 1}
    ).to_list(1000)
    member_ids = [m["user_id"] for m in memberships]
    users = await db.users.find(
        {"user_id": {"$in": member_ids}},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    return users

@router.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    await require_auth(request)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}")
async def update_user(user_id: str, update: UserUpdate, request: Request):
    current_user = await require_auth(request)
    if current_user.get("user_id") != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Cannot update other users")
    if update.role and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_dict:
        await db.users.update_one({"user_id": user_id}, {"$set": update_dict})
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return user

@router.get("/technicians")
async def get_technicians(request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    await require_auth(request)
    # Return technicians belonging to this org only
    memberships = await db.organization_users.find(
        {"organization_id": ctx.org_id, "role": "technician", "status": "active"},
        {"user_id": 1}
    ).to_list(200)
    tech_ids = [m["user_id"] for m in memberships]
    technicians = await db.users.find(
        {"user_id": {"$in": tech_ids}, "is_active": True},
        {"_id": 0, "password_hash": 0}
    ).to_list(200)
    return technicians

# ==================== SUPPLIER ROUTES ====================

@router.post("/suppliers")
async def create_supplier(
    data: SupplierCreate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    user = await require_auth(request)
    if user.get("role") not in ["admin", "owner", "technician", "manager"]:
        raise HTTPException(status_code=403, detail="Technician or Admin access required")
    
    supplier = Supplier(**data.model_dump())
    doc = supplier.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['organization_id'] = ctx.org_id
    await db.suppliers.insert_one(doc)
    return supplier.model_dump()

@router.get("/suppliers")
async def get_suppliers(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"organization_id": ctx.org_id}
    suppliers = await db.suppliers.find(query, {"_id": 0}).to_list(1000)
    return suppliers

@router.get("/suppliers/{supplier_id}")
async def get_supplier(
    supplier_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"supplier_id": supplier_id, "organization_id": ctx.org_id}
    supplier = await db.suppliers.find_one(query, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: str, 
    update: SupplierUpdate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    user = await require_auth(request)
    if user.get("role") not in ["admin", "owner", "technician", "manager"]:
        raise HTTPException(status_code=403, detail="Technician or Admin access required")
    query = {"supplier_id": supplier_id, "organization_id": ctx.org_id}
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.suppliers.update_one(query, {"$set": update_dict})
    supplier = await db.suppliers.find_one(query, {"_id": 0})
    return supplier

# ==================== VEHICLE ROUTES ====================

@router.post("/vehicles")
async def create_vehicle(
    vehicle_data: VehicleCreate, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    user = await require_auth(request)
    
    vehicle = Vehicle(
        owner_id=user.get("user_id"),
        owner_name=vehicle_data.owner_name,
        owner_email=vehicle_data.owner_email,
        owner_phone=vehicle_data.owner_phone,
        make=vehicle_data.make,
        model=vehicle_data.model,
        year=vehicle_data.year,
        registration_number=vehicle_data.registration_number,
        battery_capacity=vehicle_data.battery_capacity
    )
    doc = vehicle.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['organization_id'] = ctx.org_id
    await db.vehicles.insert_one(doc)
    return vehicle.model_dump()

@router.get("/vehicles")
async def get_vehicles(
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    user = await require_auth(request)
    base_query = {"organization_id": ctx.org_id}
    
    if user.get("role") in ["admin", "technician"]:
        vehicles = await db.vehicles.find(base_query, {"_id": 0}).to_list(1000)
    else:
        query = {**base_query, "owner_id": user.get("user_id")}
        vehicles = await db.vehicles.find(query, {"_id": 0}).to_list(100)
    return vehicles

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_auth(request)
    query = {"vehicle_id": vehicle_id, "organization_id": ctx.org_id}
    
    vehicle = await db.vehicles.find_one(query, {"_id": 0})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.put("/vehicles/{vehicle_id}/status")
async def update_vehicle_status(
    vehicle_id: str, 
    status: str, 
    request: Request,
    ctx: TenantContext = Depends(tenant_context_required)
):
    await require_technician_or_admin(request)
    if status not in ["active", "in_workshop", "serviced"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    query = {"vehicle_id": vehicle_id, "organization_id": ctx.org_id}
    await db.vehicles.update_one(query, {"$set": {"current_status": status}})
    return {"message": "Status updated"}

# ==================== TICKET ROUTES (MIGRATED TO /routes/tickets.py) ====================
# Old monolithic ticket routes have been moved to the event-driven tickets module.
# See: /app/backend/routes/tickets.py and /app/backend/services/ticket_service.py
# The new module:
# - Emits events (TICKET_CREATED, TICKET_UPDATED, TICKET_CLOSED)
# - Integrates with EFI AI matching pipeline
# - Triggers confidence engine on ticket closure
# - Auto-creates draft failure cards for undocumented issues

# ==================== INVENTORY ROUTES ====================

@router.post("/customers")
async def create_customer(data: CustomerCreate, request: Request):
    await require_technician_or_admin(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
    except HTTPException:
        org_id = None
    
    customer = Customer(**data.model_dump())
    doc = customer.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if org_id:
        doc['organization_id'] = org_id
    await db.customers.insert_one(doc)
    return customer.model_dump()

@router.get("/customers")
async def get_customers(request: Request, search: Optional[str] = None, status: Optional[str] = None):
    await require_auth(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
        query = {"organization_id": org_id}
    except HTTPException:
        query = {}
    
    if search:
        query["$or"] = [
            {"display_name": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if status:
        query["status"] = status
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    return customers

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, request: Request):
    await require_auth(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
        query = {"customer_id": customer_id, "organization_id": org_id}
    except HTTPException:
        query = {"customer_id": customer_id}
    customer = await db.customers.find_one(query, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, update: CustomerUpdate, request: Request):
    await require_technician_or_admin(request)
    # Get org context for multi-tenant scoping
    from core.org import get_org_id_from_request
    try:
        org_id = await get_org_id_from_request(request)
        query = {"customer_id": customer_id, "organization_id": org_id}
    except HTTPException:
        query = {"customer_id": customer_id}
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.customers.update_one(query, {"$set": update_dict})
    customer = await db.customers.find_one(query, {"_id": 0})
    return customer

# ==================== EXPENSE ROUTES (LEGACY - DEPRECATED) ====================
# These routes have been replaced by /app/backend/routes/expenses.py
# Keeping as reference but disabling to avoid route conflicts