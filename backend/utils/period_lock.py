"""
Period Lock Utility — Financial Compliance
==========================================
Reusable utility to check and enforce period locks on financial write operations.
A locked period prevents any financial transaction from being created, modified,
or deleted with a date falling within that locked period.

Sprint 4A-04: This is the canonical location for period lock checking.
Both posting_hooks.py and double_entry_service.py import from here,
eliminating the circular dependency risk between those modules.

Usage:
    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(db, org_id, transaction_date_str)

    # For posting hooks / double_entry_service:
    from utils.period_lock import check_period_locked
    await check_period_locked(org_id, transaction_date_str)
"""
import os
from datetime import datetime
from fastapi import HTTPException
import motor.motor_asyncio


async def check_period_lock(db, org_id: str, transaction_date: datetime) -> bool:
    """
    Returns True if the period is locked, False if open.
    Call this BEFORE any financial write operation.
    """
    if not org_id:
        return False
    lock = await db.period_locks.find_one({
        "org_id": org_id,
        "period_month": transaction_date.month,
        "period_year": transaction_date.year,
        "unlocked_at": None
    })
    return lock is not None


async def enforce_period_lock(db, org_id: str, transaction_date_str: str):
    """
    Raises HTTP 423 if the period is locked.
    Accepts date as a string (YYYY-MM-DD or ISO format) and parses it.
    Call this in every financial write endpoint.
    """
    if not transaction_date_str or not org_id:
        return
    try:
        dt = datetime.fromisoformat(transaction_date_str[:10])
    except (ValueError, TypeError):
        return
    if await check_period_lock(db, org_id, dt):
        raise HTTPException(
            status_code=423,
            detail=f"Financial period {dt.strftime('%B %Y')} is locked. "
                   f"No transactions can be created or modified in this period."
        )


async def check_period_locked(organization_id: str, transaction_date: str) -> None:
    """
    Check if the period containing transaction_date is locked.
    Raises ValueError if the period is locked.

    Sprint 4A-04: Moved from services/posting_hooks.py.
    This is the standalone version that creates its own DB connection,
    used by posting_hooks.py and double_entry_service.py.

    transaction_date: ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    """
    if not organization_id or not transaction_date:
        return

    try:
        dt = datetime.fromisoformat(transaction_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            dt = datetime.strptime(transaction_date[:10], "%Y-%m-%d")
        except Exception:
            return

    MONGO_URL = os.environ.get("MONGO_URL")
    DB_NAME = os.environ.get("DB_NAME")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    lock = await db.period_locks.find_one({
        "org_id": organization_id,
        "period_month": dt.month,
        "period_year": dt.year,
        "unlocked_at": None
    })

    if lock:
        raise ValueError(
            f"Cannot post journal entry: period {dt.month}/{dt.year} "
            f"is locked for organization {organization_id}"
        )


# Backward-compatible alias for posting_hooks imports
_check_period_lock = check_period_locked
