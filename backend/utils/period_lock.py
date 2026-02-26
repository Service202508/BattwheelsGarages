"""
Period Lock Utility — Financial Compliance
==========================================
Reusable utility to check and enforce period locks on financial write operations.
A locked period prevents any financial transaction from being created, modified,
or deleted with a date falling within that locked period.

Usage:
    from utils.period_lock import enforce_period_lock
    await enforce_period_lock(db, org_id, transaction_date_str)
"""
from datetime import datetime
from fastapi import HTTPException


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
