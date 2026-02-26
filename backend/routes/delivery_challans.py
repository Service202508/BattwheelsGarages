"""
Delivery Challans API Routes
============================
CRUD endpoints for delivery challans with tenant isolation and period lock enforcement.
"""
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/delivery-challans", tags=["Delivery Challans"])

_db = None


def set_db(db):
    global _db
    _db = db


def get_db():
    if _db is None:
        from server import db
        return db
    return _db


async def _get_org_id(request: Request) -> str:
    from utils.auth import decode_token_safe
    org_id = request.headers.get("X-Organization-ID")
    if not org_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token_safe(auth_header.split(" ")[1])
            if payload:
                org_id = payload.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")
    return org_id


async def _get_user_id(request: Request) -> str:
    from utils.auth import decode_token_safe
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = decode_token_safe(auth_header.split(" ")[1])
        if payload:
            return payload.get("user_id", "")
    return ""


# ==================== MODELS ====================

class ChallanLineItem(BaseModel):
    item_id: Optional[str] = None
    item_name: str = ""
    description: str = ""
    quantity: float = 0
    unit: str = "pcs"
    hsn_code: str = ""


class DeliveryChallanCreate(BaseModel):
    customer_id: str
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}")
    items: List[ChallanLineItem] = []
    linked_invoice_id: Optional[str] = None
    linked_sales_order_id: Optional[str] = None
    vehicle_number: str = ""
    transporter_name: str = ""
    notes: str = ""


class DeliveryChallanUpdate(BaseModel):
    date: Optional[str] = None
    items: Optional[List[ChallanLineItem]] = None
    linked_invoice_id: Optional[str] = None
    linked_sales_order_id: Optional[str] = None
    vehicle_number: Optional[str] = None
    transporter_name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


# ==================== HELPERS ====================

async def _next_challan_number(db, org_id: str) -> str:
    last = await db.delivery_challans.find_one(
        {"organization_id": org_id}, sort=[("created_at", -1)], projection={"challan_number": 1, "_id": 0}
    )
    if last and last.get("challan_number"):
        try:
            num = int(last["challan_number"].split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"DC-{num:05d}"


# ==================== ROUTES ====================

@router.get("")
@router.get("/")
async def list_challans(request: Request, status: Optional[str] = None, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    db = get_db()
    org_id = await _get_org_id(request)
    query = {"organization_id": org_id}
    if status:
        query["status"] = status
    total = await db.delivery_challans.count_documents(query)
    challans = await db.delivery_challans.find(query, {"_id": 0}).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    return {"data": challans, "pagination": {"total": total, "page": page, "per_page": per_page}}


@router.get("/{challan_id}")
async def get_challan(request: Request, challan_id: str):
    db = get_db()
    org_id = await _get_org_id(request)
    challan = await db.delivery_challans.find_one({"challan_id": challan_id, "organization_id": org_id}, {"_id": 0})
    if not challan:
        raise HTTPException(status_code=404, detail="Delivery challan not found")
    return challan


@router.post("")
@router.post("/")
async def create_challan(request: Request, data: DeliveryChallanCreate):
    db = get_db()
    org_id = await _get_org_id(request)
    user_id = await _get_user_id(request)

    challan_id = f"dc_{uuid.uuid4().hex[:12]}"
    challan_number = await _next_challan_number(db, org_id)

    doc = {
        "challan_id": challan_id,
        "challan_number": challan_number,
        "organization_id": org_id,
        "customer_id": data.customer_id,
        "date": data.date,
        "items": [item.dict() for item in data.items],
        "linked_invoice_id": data.linked_invoice_id,
        "linked_sales_order_id": data.linked_sales_order_id,
        "vehicle_number": data.vehicle_number,
        "transporter_name": data.transporter_name,
        "notes": data.notes,
        "status": "draft",
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.delivery_challans.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/{challan_id}")
async def update_challan(request: Request, challan_id: str, data: DeliveryChallanUpdate):
    db = get_db()
    org_id = await _get_org_id(request)
    existing = await db.delivery_challans.find_one({"challan_id": challan_id, "organization_id": org_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Delivery challan not found")

    updates = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    if "items" in updates:
        updates["items"] = [item.dict() if hasattr(item, 'dict') else item for item in updates["items"]]
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.delivery_challans.update_one({"challan_id": challan_id}, {"$set": updates})
    updated = await db.delivery_challans.find_one({"challan_id": challan_id}, {"_id": 0})
    return updated


@router.delete("/{challan_id}")
async def delete_challan(request: Request, challan_id: str):
    db = get_db()
    org_id = await _get_org_id(request)
    existing = await db.delivery_challans.find_one({"challan_id": challan_id, "organization_id": org_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Delivery challan not found")
    if existing.get("status") == "delivered":
        raise HTTPException(status_code=400, detail="Cannot delete a delivered challan")
    await db.delivery_challans.delete_one({"challan_id": challan_id})
    return {"message": "Delivery challan deleted"}
