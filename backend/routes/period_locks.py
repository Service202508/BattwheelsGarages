"""
Period Locks API Routes — Financial Compliance
===============================================
Manage locked financial periods per organization.
- GET  /period-locks       — list locked periods
- POST /period-locks       — lock a period (admin/owner only)
- DELETE /period-locks/:id — unlock (platform super-admin ONLY)
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance/period-locks", tags=["Period Locks"])

_db = None


def set_db(db):
    global _db
    _db = db


def get_db():
    if _db is None:
        from server import db
        return db
    return _db


# ==================== MODELS ====================

class PeriodLockCreate(BaseModel):
    period_month: int = Field(..., ge=1, le=12)
    period_year: int = Field(..., ge=2020, le=2100)
    lock_reason: str = ""


# ==================== HELPERS ====================

async def _get_user_from_request(request: Request) -> dict:
    from utils.auth import get_current_user_from_request
    return await get_current_user_from_request(request)


async def _get_org_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and user.get("org_id"):
        return user["org_id"]
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        return org_id
    from utils.auth import decode_token_safe
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = decode_token_safe(auth_header.split(" ")[1])
        if payload and payload.get("org_id"):
            return payload["org_id"]
    raise HTTPException(status_code=400, detail="Organization context required")


# ==================== ROUTES ====================

@router.get("")
@router.get("/")
async def list_period_locks(request: Request):
    """List all locked periods for the current organization."""
    user = await _get_user_from_request(request)
    org_id = await _get_org_id(request)
    db = get_db()

    locks = await db.period_locks.find(
        {"org_id": org_id}, {"_id": 0}
    ).sort([("period_year", -1), ("period_month", -1)]).to_list(120)

    return {"code": 0, "data": locks}


@router.post("")
@router.post("/")
async def lock_period(request: Request, data: PeriodLockCreate):
    """Lock a financial period. Only admin/owner roles can lock."""
    user = await _get_user_from_request(request)
    org_id = await _get_org_id(request)
    db = get_db()

    role = user.get("role", "")
    if role not in ("admin", "owner", "org_admin"):
        raise HTTPException(status_code=403, detail="Only admin or owner can lock financial periods")

    existing = await db.period_locks.find_one({
        "org_id": org_id,
        "period_month": data.period_month,
        "period_year": data.period_year,
        "unlocked_at": None
    })
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Period {data.period_month}/{data.period_year} is already locked"
        )

    lock_id = f"plock_{uuid.uuid4().hex[:12]}"
    lock_doc = {
        "lock_id": lock_id,
        "org_id": org_id,
        "period_month": data.period_month,
        "period_year": data.period_year,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "locked_by": user.get("user_id", ""),
        "locked_by_name": user.get("name", user.get("email", "")),
        "lock_reason": data.lock_reason,
        "unlocked_at": None,
        "unlocked_by": None,
    }
    await db.period_locks.insert_one(lock_doc)

    await db.period_locks.create_index(
        [("org_id", 1), ("period_month", 1), ("period_year", 1)],
        unique=False
    )

    lock_doc.pop("_id", None)
    logger.info(f"Period locked: {data.period_month}/{data.period_year} by {user.get('user_id')} in org {org_id}")
    return {"code": 0, "message": f"Period {data.period_month}/{data.period_year} locked", "lock": lock_doc}


@router.delete("/{lock_id}")
async def unlock_period(request: Request, lock_id: str):
    """Unlock a period. Only platform_admin or super_admin can unlock."""
    user = await _get_user_from_request(request)
    db = get_db()

    role = user.get("role", "")
    if role not in ("platform_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Only platform super-admin can unlock financial periods")

    lock = await db.period_locks.find_one({"lock_id": lock_id}, {"_id": 0})
    if not lock:
        raise HTTPException(status_code=404, detail="Lock not found")
    if lock.get("unlocked_at"):
        raise HTTPException(status_code=409, detail="Period is already unlocked")

    await db.period_locks.update_one(
        {"lock_id": lock_id},
        {"$set": {
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
            "unlocked_by": user.get("user_id", ""),
        }}
    )

    logger.info(f"Period unlocked: {lock_id} by {user.get('user_id')}")
    return {"code": 0, "message": "Period unlocked"}
