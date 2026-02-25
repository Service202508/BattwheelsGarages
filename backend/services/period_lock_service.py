"""
Period Lock Service
===================
Core business logic for financial period locking.
Enforces that no financial mutations occur in locked accounting periods.

Design doc: /app/docs/PERIOD_LOCKING_DESIGN.md
Audit writes to: audit_logs (pre-existing collection, NOT audit_log)
"""
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import motor.motor_asyncio
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
_db = _client[DB_NAME]

# Collections
period_locks_col = _db["period_locks"]
audit_logs_col = _db["audit_logs"]  # Pre-existing collection — NOT audit_log

# Default unlock window: 72 hours
DEFAULT_UNLOCK_WINDOW_HOURS = 72
MAX_EXTENSIONS = 2
MAX_TOTAL_UNLOCK_DAYS = 7


def _extract_period(date_str: str) -> str:
    """Extract YYYY-MM from a date string. Handles YYYY-MM-DD and ISO datetime."""
    if not date_str:
        raise ValueError("Date string is empty")
    return date_str[:7]


def _generate_lock_id() -> str:
    return f"lock_{uuid.uuid4().hex[:12]}"


async def check_period_lock(org_id: str, date_str: str) -> None:
    """
    Raises HTTP 409 if the month containing `date_str` is locked for `org_id`.
    Called at the top of every financial write endpoint.

    Parameters:
        org_id:   Organization ID from tenant context
        date_str: The effective financial date (YYYY-MM-DD or ISO datetime)

    Raises:
        HTTPException(409) with code PERIOD_LOCKED if the period is locked.
    """
    if not org_id or not date_str:
        return  # Skip check if context is missing

    period = _extract_period(date_str)

    lock = await period_locks_col.find_one(
        {
            "organization_id": org_id,
            "period": period,
            "status": "locked",
        },
        {"_id": 0, "locked_by": 1, "locked_at": 1},
    )

    if lock:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Period {period} is locked for this organization. Unlock the period or use a date in an open period.",
                "code": "PERIOD_LOCKED",
                "locked_period": period,
                "locked_by": lock.get("locked_by", ""),
                "locked_at": lock.get("locked_at", ""),
            },
        )


async def get_period_locks(org_id: str, year: Optional[int] = None) -> list:
    """Get all period locks for an organization, optionally filtered by year."""
    query = {"organization_id": org_id}
    if year:
        query["period"] = {"$regex": f"^{year}-"}

    locks = await period_locks_col.find(
        query, {"_id": 0}
    ).sort("period", -1).to_list(None)
    return locks


async def get_period_lock(org_id: str, period: str) -> Optional[dict]:
    """Get a single period lock record."""
    return await period_locks_col.find_one(
        {"organization_id": org_id, "period": period},
        {"_id": 0},
    )


async def lock_period(
    org_id: str,
    period: str,
    user_id: str,
    user_role: str,
    reason: str = "",
    request: Optional[Request] = None,
) -> dict:
    """
    Lock a financial period.

    Allowed roles: admin, owner, accountant
    """
    if user_role not in ("admin", "owner", "accountant"):
        raise HTTPException(status_code=403, detail="Only admin, owner, or accountant can lock periods")

    # Validate period format
    if not _is_valid_period(period):
        raise HTTPException(status_code=400, detail="Invalid period format. Use YYYY-MM.")

    now = datetime.now(timezone.utc)

    # Check if already locked
    existing = await period_locks_col.find_one(
        {"organization_id": org_id, "period": period},
        {"_id": 0},
    )

    if existing and existing.get("status") == "locked":
        raise HTTPException(status_code=409, detail=f"Period {period} is already locked")

    if existing:
        # Re-lock an unlocked period
        before = dict(existing)
        await period_locks_col.update_one(
            {"organization_id": org_id, "period": period},
            {
                "$set": {
                    "status": "locked",
                    "locked_by": user_id,
                    "locked_at": now.isoformat(),
                    "lock_reason": reason,
                    "unlocked_by": None,
                    "unlocked_at": None,
                    "unlock_reason": None,
                    "unlock_expires_at": None,
                    "unlock_extension_count": 0,
                    "updated_at": now.isoformat(),
                },
            },
        )
        lock_doc = await period_locks_col.find_one(
            {"organization_id": org_id, "period": period}, {"_id": 0}
        )
        await _write_audit(org_id, user_id, user_role, "LOCK_PERIOD", "period_lock", period, before, lock_doc, request)
    else:
        # Create new lock record
        lock_doc = {
            "lock_id": _generate_lock_id(),
            "organization_id": org_id,
            "period": period,
            "status": "locked",
            "locked_by": user_id,
            "locked_at": now.isoformat(),
            "lock_reason": reason,
            "unlocked_by": None,
            "unlocked_at": None,
            "unlock_reason": None,
            "unlock_expires_at": None,
            "unlock_extension_count": 0,
            "platform_override": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        await period_locks_col.insert_one(lock_doc)
        lock_doc.pop("_id", None)
        await _write_audit(org_id, user_id, user_role, "LOCK_PERIOD", "period_lock", period, None, lock_doc, request)

    return lock_doc


async def unlock_period(
    org_id: str,
    period: str,
    user_id: str,
    user_role: str,
    reason: str,
    window_hours: int = DEFAULT_UNLOCK_WINDOW_HOURS,
    request: Optional[Request] = None,
) -> dict:
    """
    Unlock a financial period with mandatory reason and time window.

    Allowed roles: admin, owner (accountants cannot unlock)
    """
    if user_role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only admin or owner can unlock periods")

    if not reason or len(reason.strip()) < 10:
        raise HTTPException(status_code=400, detail="Unlock reason must be at least 10 characters")

    existing = await period_locks_col.find_one(
        {"organization_id": org_id, "period": period},
        {"_id": 0},
    )

    if not existing:
        raise HTTPException(status_code=404, detail=f"No lock record found for period {period}")

    if existing.get("status") != "locked":
        raise HTTPException(status_code=409, detail=f"Period {period} is not currently locked (status: {existing.get('status')})")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=window_hours)
    before = dict(existing)

    await period_locks_col.update_one(
        {"organization_id": org_id, "period": period},
        {
            "$set": {
                "status": "unlocked_amendment",
                "unlocked_by": user_id,
                "unlocked_at": now.isoformat(),
                "unlock_reason": reason.strip(),
                "unlock_expires_at": expires_at.isoformat(),
                "unlock_extension_count": 0,
                "updated_at": now.isoformat(),
            },
        },
    )

    lock_doc = await period_locks_col.find_one(
        {"organization_id": org_id, "period": period}, {"_id": 0}
    )

    await _write_audit(org_id, user_id, user_role, "UNLOCK_PERIOD", "period_lock", period, before, lock_doc, request)

    return lock_doc


async def extend_unlock(
    org_id: str,
    period: str,
    user_id: str,
    user_role: str,
    additional_hours: int = DEFAULT_UNLOCK_WINDOW_HOURS,
    request: Optional[Request] = None,
) -> dict:
    """
    Extend the unlock window. Max 2 extensions, total max 7 days.
    """
    if user_role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only admin or owner can extend unlock windows")

    existing = await period_locks_col.find_one(
        {"organization_id": org_id, "period": period},
        {"_id": 0},
    )

    if not existing:
        raise HTTPException(status_code=404, detail=f"No lock record found for period {period}")

    if existing.get("status") != "unlocked_amendment":
        raise HTTPException(status_code=409, detail=f"Period {period} is not in amendment window (status: {existing.get('status')})")

    ext_count = existing.get("unlock_extension_count", 0)
    if ext_count >= MAX_EXTENSIONS:
        raise HTTPException(status_code=409, detail=f"Maximum extensions ({MAX_EXTENSIONS}) reached for period {period}")

    # Calculate new expiry
    current_expires = existing.get("unlock_expires_at", "")
    if current_expires:
        current_dt = datetime.fromisoformat(current_expires)
    else:
        current_dt = datetime.now(timezone.utc)

    new_expires = current_dt + timedelta(hours=additional_hours)

    # Enforce max total unlock duration (7 days from original unlock)
    unlocked_at = existing.get("unlocked_at", "")
    if unlocked_at:
        original_unlock = datetime.fromisoformat(unlocked_at)
        max_allowed = original_unlock + timedelta(days=MAX_TOTAL_UNLOCK_DAYS)
        if new_expires > max_allowed:
            new_expires = max_allowed

    now = datetime.now(timezone.utc)
    before = dict(existing)

    await period_locks_col.update_one(
        {"organization_id": org_id, "period": period},
        {
            "$set": {
                "unlock_expires_at": new_expires.isoformat(),
                "unlock_extension_count": ext_count + 1,
                "updated_at": now.isoformat(),
            },
        },
    )

    lock_doc = await period_locks_col.find_one(
        {"organization_id": org_id, "period": period}, {"_id": 0}
    )

    await _write_audit(org_id, user_id, user_role, "EXTEND_UNLOCK", "period_lock", period, before, lock_doc, request)

    return lock_doc


async def process_auto_relocks() -> int:
    """
    Auto-relock periods where the amendment window has expired.
    Called by a background task/cron.
    Returns the number of periods relocked.
    """
    now = datetime.now(timezone.utc)

    expired = await period_locks_col.find(
        {
            "status": "unlocked_amendment",
            "unlock_expires_at": {"$lte": now.isoformat()},
        },
        {"_id": 0},
    ).to_list(None)

    relocked = 0
    for lock in expired:
        before = dict(lock)
        await period_locks_col.update_one(
            {
                "organization_id": lock["organization_id"],
                "period": lock["period"],
            },
            {
                "$set": {
                    "status": "locked",
                    "locked_by": "system_auto_relock",
                    "locked_at": now.isoformat(),
                    "lock_reason": "Auto-relocked after amendment window expired",
                    "updated_at": now.isoformat(),
                },
            },
        )

        after = await period_locks_col.find_one(
            {"organization_id": lock["organization_id"], "period": lock["period"]},
            {"_id": 0},
        )

        await _write_audit(
            lock["organization_id"],
            "system_auto_relock", "system",
            "AUTO_RELOCK_PERIOD", "period_lock",
            lock["period"], before, after,
        )
        relocked += 1

    if relocked:
        logger.info(f"Auto-relocked {relocked} expired amendment windows")

    return relocked


async def lock_fiscal_year(
    org_id: str,
    year: int,
    user_id: str,
    user_role: str,
    fiscal_year_start_month: int = 4,
    request: Optional[Request] = None,
) -> list:
    """Lock all 12 months of a fiscal year (e.g., Apr 2025 to Mar 2026)."""
    results = []
    for i in range(12):
        month = fiscal_year_start_month + i
        y = year if month <= 12 else year + 1
        m = month if month <= 12 else month - 12
        period = f"{y}-{m:02d}"
        try:
            result = await lock_period(org_id, period, user_id, user_role, f"Fiscal year {year}-{year+1} close", request)
            results.append({"period": period, "status": "locked"})
        except HTTPException as e:
            results.append({"period": period, "status": "skipped", "reason": str(e.detail)})
    return results


def _is_valid_period(period: str) -> bool:
    """Validate YYYY-MM format."""
    if len(period) != 7 or period[4] != "-":
        return False
    try:
        y, m = period.split("-")
        return 2000 <= int(y) <= 2099 and 1 <= int(m) <= 12
    except (ValueError, IndexError):
        return False


async def _write_audit(
    org_id: str,
    user_id: str,
    user_role: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before_snapshot: Optional[dict] = None,
    after_snapshot: Optional[dict] = None,
    request: Optional[Request] = None,
):
    """Write audit entry to audit_logs collection (pre-existing, NOT audit_log)."""
    ip_address = ""
    if request:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif hasattr(request, "client") and request.client:
            ip_address = request.client.host or ""

    entry = {
        "organization_id": org_id,
        "user_id": user_id,
        "user_role": user_role,
        "action": action,
        "resource_type": entity_type,
        "resource_id": entity_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address,
        "before_snapshot": before_snapshot,
        "after_snapshot": after_snapshot,
    }

    try:
        await audit_logs_col.insert_one(entry)
        logger.info(f"AUDIT: {action} {entity_type} {entity_id} by {user_id} in org {org_id}")
    except Exception as e:
        logger.error(f"AUDIT LOG FAILED: {action} {entity_type} {entity_id} — {e}")
