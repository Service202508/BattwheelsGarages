"""
Login Rate Limiter — Per-email brute-force protection
=====================================================
Max 5 failed login attempts per email per 15 minutes.
6th attempt returns 429. Successful login clears counter.
Uses MongoDB login_attempts collection with TTL index.
"""

import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_db: AsyncIOMotorDatabase = None
_ttl_index_created = False


def init_rate_limiter_sync(db: AsyncIOMotorDatabase):
    """Initialize rate limiter with DB reference (sync, TTL index created lazily)."""
    global _db
    _db = db
    logger.info("Login rate limiter initialized (TTL index deferred)")


async def _ensure_ttl_index():
    """Create TTL index on first use (async)."""
    global _ttl_index_created
    if not _ttl_index_created and _db:
        await _db.login_attempts.create_index("created_at", expireAfterSeconds=900)
        _ttl_index_created = True


async def check_login_rate_limit(email: str) -> tuple:
    """
    Check if email is rate-limited.
    Returns (is_allowed: bool, retry_after: int).
    """
    if not _db:
        return True, 0

    await _ensure_ttl_index()
    count = await _db.login_attempts.count_documents({"email": email})
    if count >= 5:
        return False, 900
    return True, 0


async def record_failed_attempt(email: str):
    """Record a failed login attempt."""
    if not _db:
        return
    await _ensure_ttl_index()
    await _db.login_attempts.insert_one({
        "email": email,
        "created_at": datetime.now(timezone.utc)
    })


async def clear_attempts(email: str):
    """Clear all recorded attempts for an email (on successful login)."""
    if not _db:
        return
    await _db.login_attempts.delete_many({"email": email})
