"""
Vendor Credits API Routes
=========================
CRUD endpoints for vendor credits with tenant isolation, period lock enforcement,
and journal entry creation on apply.
"""
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendor-credits", tags=["Vendor Credits"])

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

class VendorCreditLineItem(BaseModel):
    item_id: Optional[str] = None
    item_name: str = ""
    description: str = ""
    quantity: float = 0
    rate: float = 0
    amount: float = 0
    account_id: Optional[str] = None
    tax_rate: float = 0


class VendorCreditCreate(BaseModel):
    vendor_id: str
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}")
    amount: float = Field(..., gt=0)
    reason: str = ""
    linked_bill_id: Optional[str] = None
    line_items: List[VendorCreditLineItem] = []


class VendorCreditUpdate(BaseModel):
    date: Optional[str] = None
    amount: Optional[float] = None
    reason: Optional[str] = None
    linked_bill_id: Optional[str] = None
    line_items: Optional[List[VendorCreditLineItem]] = None
    status: Optional[str] = None


# ==================== HELPERS ====================

async def _next_credit_number(db, org_id: str) -> str:
    last = await db.vendor_credits.find_one(
        {"organization_id": org_id}, sort=[("created_at", -1)], projection={"credit_note_number": 1, "_id": 0}
    )
    if last and last.get("credit_note_number"):
        try:
            num = int(last["credit_note_number"].split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"VCR-{num:05d}"


# ==================== ROUTES ====================

@router.get("")
@router.get("/")
async def list_vendor_credits(request: Request, status: Optional[str] = None, vendor_id: Optional[str] = None, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    db = get_db()
    org_id = await _get_org_id(request)
    query = {"organization_id": org_id}
    if status:
        query["status"] = status
    if vendor_id:
        query["vendor_id"] = vendor_id
    total = await db.vendor_credits.count_documents(query)
    credits = await db.vendor_credits.find(query, {"_id": 0}).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    return {"data": credits, "pagination": {"total": total, "page": page, "per_page": per_page}}


@router.get("/{credit_id}")
async def get_vendor_credit(request: Request, credit_id: str):
    db = get_db()
    org_id = await _get_org_id(request)
    credit = await db.vendor_credits.find_one({"credit_id": credit_id, "organization_id": org_id}, {"_id": 0})
    if not credit:
        raise HTTPException(status_code=404, detail="Vendor credit not found")
    return credit


@router.post("")
@router.post("/")
async def create_vendor_credit(request: Request, data: VendorCreditCreate):
    db = get_db()
    org_id = await _get_org_id(request)
    user_id = await _get_user_id(request)

    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(db, org_id, data.date)

    credit_id = f"vcr_{uuid.uuid4().hex[:12]}"
    credit_number = await _next_credit_number(db, org_id)

    doc = {
        "credit_id": credit_id,
        "credit_note_number": credit_number,
        "organization_id": org_id,
        "vendor_id": data.vendor_id,
        "date": data.date,
        "amount": data.amount,
        "reason": data.reason,
        "linked_bill_id": data.linked_bill_id,
        "line_items": [item.dict() for item in data.line_items],
        "status": "draft",
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.vendor_credits.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/{credit_id}")
async def update_vendor_credit(request: Request, credit_id: str, data: VendorCreditUpdate):
    db = get_db()
    org_id = await _get_org_id(request)
    existing = await db.vendor_credits.find_one({"credit_id": credit_id, "organization_id": org_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor credit not found")
    if existing.get("status") == "applied":
        raise HTTPException(status_code=400, detail="Cannot modify an applied vendor credit")

    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(db, org_id, existing.get("date", ""))
    if data.date:
        await enforce_period_lock(db, org_id, data.date)

    updates = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    if "line_items" in updates:
        updates["line_items"] = [item.dict() if hasattr(item, 'dict') else item for item in updates["line_items"]]
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.vendor_credits.update_one({"credit_id": credit_id}, {"$set": updates})
    updated = await db.vendor_credits.find_one({"credit_id": credit_id}, {"_id": 0})
    return updated


@router.post("/{credit_id}/apply")
async def apply_vendor_credit(request: Request, credit_id: str):
    """Apply a vendor credit — creates a journal entry (Vendor Payable Dr / Purchase Returns Cr)."""
    db = get_db()
    org_id = await _get_org_id(request)
    user_id = await _get_user_id(request)

    credit = await db.vendor_credits.find_one({"credit_id": credit_id, "organization_id": org_id})
    if not credit:
        raise HTTPException(status_code=404, detail="Vendor credit not found")
    if credit.get("status") == "applied":
        raise HTTPException(status_code=400, detail="Vendor credit already applied")

    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(db, org_id, credit.get("date", ""))

    je_id = f"je_{uuid.uuid4().hex[:12]}"
    journal_entry = {
        "entry_id": je_id,
        "organization_id": org_id,
        "entry_date": credit["date"],
        "description": f"Vendor Credit {credit.get('credit_note_number', '')} applied",
        "reference": credit_id,
        "source": "vendor_credit",
        "lines": [
            {"account_name": "Vendor Payable", "debit_amount": credit["amount"], "credit_amount": 0},
            {"account_name": "Purchase Returns", "debit_amount": 0, "credit_amount": credit["amount"]},
        ],
        "is_posted": True,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.journal_entries.insert_one(journal_entry)

    await db.vendor_credits.update_one(
        {"credit_id": credit_id},
        {"$set": {"status": "applied", "journal_entry_id": je_id, "applied_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"message": "Vendor credit applied", "journal_entry_id": je_id}


@router.delete("/{credit_id}")
async def delete_vendor_credit(request: Request, credit_id: str):
    db = get_db()
    org_id = await _get_org_id(request)
    existing = await db.vendor_credits.find_one({"credit_id": credit_id, "organization_id": org_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor credit not found")
    if existing.get("status") == "applied":
        raise HTTPException(status_code=400, detail="Cannot delete an applied vendor credit")

    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(db, org_id, existing.get("date", ""))

    await db.vendor_credits.delete_one({"credit_id": credit_id})
    return {"message": "Vendor credit deleted"}
