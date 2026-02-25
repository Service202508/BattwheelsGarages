"""
Period Locks Routes
===================
CRUD + management endpoints for financial period locking.

Design doc: /app/docs/PERIOD_LOCKING_DESIGN.md
All audit entries written to audit_logs (NOT audit_log).
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services.period_lock_service import (
    check_period_lock,
    extend_unlock,
    get_period_lock,
    get_period_locks,
    lock_fiscal_year,
    lock_period,
    process_auto_relocks,
    unlock_period,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/period-locks", tags=["Period Locks"])


# --- Request Models ---

class LockPeriodRequest(BaseModel):
    period: str = Field(..., description="Calendar month in YYYY-MM format", pattern=r"^\d{4}-\d{2}$")
    reason: str = Field("", description="Optional reason for locking")


class UnlockPeriodRequest(BaseModel):
    reason: str = Field(..., description="Mandatory reason for unlocking (min 10 chars)", min_length=10)
    window_hours: int = Field(72, description="Hours before auto-relock (default 72)")


class ExtendUnlockRequest(BaseModel):
    additional_hours: int = Field(72, description="Additional hours to extend the window")


class LockFiscalYearRequest(BaseModel):
    year: int = Field(..., description="Fiscal year start year (e.g., 2025 for FY 2025-26)")
    fiscal_year_start_month: int = Field(4, description="Starting month of fiscal year (default April=4)")


class CheckPeriodRequest(BaseModel):
    date: str = Field(..., description="Date to check (YYYY-MM-DD)")


# --- Helper to extract user context ---

async def _get_user_context(request: Request) -> dict:
    user_id = getattr(request.state, "tenant_user_id", "") or getattr(request.state, "user_id", "")
    user_role = getattr(request.state, "tenant_user_role", "") or getattr(request.state, "user_role", "")
    org_id = getattr(request.state, "tenant_org_id", "") or getattr(request.state, "organization_id", "")
    return {"user_id": user_id, "user_role": user_role, "org_id": org_id}


# --- Endpoints ---

@router.get("")
async def list_period_locks(
    request: Request,
    year: Optional[int] = Query(None, description="Filter by year"),
):
    """List all period locks for the current organization."""
    ctx = await _get_user_context(request)
    if not ctx["org_id"]:
        raise HTTPException(status_code=400, detail="Organization context required")
    locks = await get_period_locks(ctx["org_id"], year)
    return {"locks": locks, "count": len(locks)}


@router.get("/{period}")
async def get_single_period_lock(request: Request, period: str):
    """Get lock status for a specific period."""
    ctx = await _get_user_context(request)
    if not ctx["org_id"]:
        raise HTTPException(status_code=400, detail="Organization context required")
    lock = await get_period_lock(ctx["org_id"], period)
    if not lock:
        return {"period": period, "status": "unlocked", "lock": None}
    return {"period": period, "status": lock.get("status", "unknown"), "lock": lock}


@router.post("/check")
async def check_period(request: Request, body: CheckPeriodRequest):
    """Check if a date falls in a locked period. Returns 200 if open, 409 if locked."""
    ctx = await _get_user_context(request)
    if not ctx["org_id"]:
        raise HTTPException(status_code=400, detail="Organization context required")
    await check_period_lock(ctx["org_id"], body.date)
    period = body.date[:7]
    return {"period": period, "status": "open", "message": f"Period {period} is open for modifications"}


@router.post("/lock")
async def lock_period_endpoint(request: Request, body: LockPeriodRequest):
    """Lock a financial period. Requires admin, owner, or accountant role."""
    ctx = await _get_user_context(request)
    if not ctx["org_id"]:
        raise HTTPException(status_code=400, detail="Organization context required")
    lock = await lock_period(
        ctx["org_id"], body.period, ctx["user_id"], ctx["user_role"], body.reason, request
    )
    return {"message": f"Period {body.period} locked successfully", "lock": lock}


@router.post("/unlock")
async def unlock_period_endpoint(request: Request, period: str = Query(...), body: UnlockPeriodRequest = None):
    """Unlock a financial period with mandatory reason. Requires admin or owner role."""
    ctx = await _get_user_context(request)
    if not ctx["org_id"]:
        raise HTTPException(status_code=400, detail="Organization context required")
    lock = await unlock_period(
        ctx["org_id"], period, ctx["user_id"], ctx["user_role"],
        body.reason, body.window_hours, request
    )
    return {"message": f"Period {period} unlocked for amendment", "lock": lock}


@router.post("/extend")
async def extend_unlock_endpoint(request: Request, period: str = Query(...), body: ExtendUnlockRequest = None):
    """Extend an active unlock window. Max 2 extensions."""
    ctx = await _get_user_context(request)
    if not ctx["org_id"]:
        raise HTTPException(status_code=400, detail="Organization context required")
    lock = await extend_unlock(
        ctx["org_id"], period, ctx["user_id"], ctx["user_role"],
        body.additional_hours, request
    )
    return {"message": f"Unlock window extended for period {period}", "lock": lock}


@router.post("/lock-fiscal-year")
async def lock_fiscal_year_endpoint(request: Request, body: LockFiscalYearRequest):
    """Lock all 12 months of a fiscal year."""
    ctx = await _get_user_context(request)
    if not ctx["org_id"]:
        raise HTTPException(status_code=400, detail="Organization context required")
    if ctx["user_role"] not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only admin or owner can lock fiscal years")
    results = await lock_fiscal_year(
        ctx["org_id"], body.year, ctx["user_id"], ctx["user_role"],
        body.fiscal_year_start_month, request
    )
    locked_count = sum(1 for r in results if r["status"] == "locked")
    return {
        "message": f"Fiscal year {body.year}-{body.year+1}: {locked_count}/12 periods locked",
        "results": results,
    }


@router.post("/auto-relock")
async def trigger_auto_relock(request: Request):
    """
    Trigger auto-relock of expired amendment windows.
    In production, this would be called by a cron job.
    """
    ctx = await _get_user_context(request)
    if ctx["user_role"] not in ("admin", "owner", "platform_admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions for auto-relock trigger")
    count = await process_auto_relocks()
    return {"message": f"Auto-relock complete: {count} periods relocked", "relocked_count": count}
