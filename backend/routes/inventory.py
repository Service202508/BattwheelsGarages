"""
Battwheels OS - Inventory Routes
Thin controller layer for inventory management
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import logging

from services.inventory_service import (
    InventoryService,
    get_inventory_service,
    init_inventory_service
)
from core.subscriptions.entitlement import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

_service: Optional[InventoryService] = None


def init_router(database):
    global _service
    _service = init_inventory_service(database)
    logger.info("Inventory router initialized")
    return router


def get_service() -> InventoryService:
    if _service is None:
        raise HTTPException(status_code=500, detail="Inventory service not initialized")
    return _service


# Request models
class InventoryCreateRequest(BaseModel):
    name: str
    sku: str
    category: str
    quantity: int
    unit_price: float
    reorder_level: int = 10


class InventoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    reorder_level: Optional[int] = None
    status: Optional[str] = None


class AllocationRequest(BaseModel):
    ticket_id: str
    item_id: str
    quantity: int


class UseAllocationRequest(BaseModel):
    quantity_used: int


class ReturnAllocationRequest(BaseModel):
    quantity_returned: int


# Helper
async def get_current_user(request: Request, db) -> dict:
    """Get current authenticated user - supports both session tokens and JWT"""
    # Try session token from cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user
    
    # Try Bearer token from header (JWT)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        import jwt
        import os
        try:
            JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
        except Exception:
            pass
    
    raise HTTPException(status_code=401, detail="Not authenticated")


# Routes
@router.post("")
async def create_inventory_item(data: InventoryCreateRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    return await service.create_item(
        name=data.name,
        sku=data.sku,
        category=data.category,
        quantity=data.quantity,
        unit_price=data.unit_price,
        reorder_level=data.reorder_level,
        user_id=user.get("user_id")
    )


@router.get("")
async def list_inventory(
    request: Request,
    category: Optional[str] = None,
    low_stock: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1)
):
    """List inventory items with standardized pagination"""
    import math
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100 per page")

    service = get_service()

    query = {}
    if category:
        query["category"] = category
    if low_stock:
        query["$expr"] = {"$lte": ["$quantity", "$reorder_level"]}

    total = await service.db.inventory.count_documents(query)
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    items = await service.db.inventory.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

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


@router.get("/{item_id}")
async def get_inventory_item(item_id: str, request: Request):
    service = get_service()
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}")
async def update_inventory_item(item_id: str, data: InventoryUpdateRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    return await service.update_item(item_id, updates, user.get("user_id"))


@router.delete("/{item_id}")
async def delete_inventory_item(item_id: str, request: Request):
    service = get_service()
    await service.db.inventory.delete_one({"item_id": item_id})
    return {"message": "Item deleted"}


# Allocations
@router.post("/allocations")
async def create_allocation(data: AllocationRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    try:
        return await service.allocate_for_ticket(
            ticket_id=data.ticket_id,
            item_id=data.item_id,
            quantity=data.quantity,
            technician_id=user.get("user_id")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/allocations/list")
async def list_allocations(request: Request, ticket_id: Optional[str] = None):
    service = get_service()
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    return await service.db.allocations.find(query, {"_id": 0}).to_list(100)


@router.put("/allocations/{allocation_id}/use")
async def use_allocation(allocation_id: str, data: UseAllocationRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    # Get org_id from tenant context (set by TenantGuardMiddleware)
    org_id = getattr(request.state, "tenant_org_id", None)
    
    try:
        return await service.use_allocation(
            allocation_id, 
            data.quantity_used, 
            user.get("user_id"),
            organization_id=org_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/allocations/{allocation_id}/return")
async def return_allocation(allocation_id: str, data: ReturnAllocationRequest, request: Request):
    service = get_service()
    user = await get_current_user(request, service.db)
    
    try:
        return await service.return_allocation(allocation_id, data.quantity_returned, user.get("user_id"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
