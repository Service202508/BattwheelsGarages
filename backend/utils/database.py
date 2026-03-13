"""
Battwheels OS - Database Configuration
Centralized database connection and utilities
"""
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

from config.environments import MONGO_URL, DB_NAME

# Create client and database
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def extract_org_id(request) -> Optional[str]:
    """Extract organization_id from request state (set by TenantGuardMiddleware).
    Returns None if no org context — use ONLY in public/auth/platform routes
    where None is a valid outcome.
    
    For tenant-scoped routes, use require_org_id() instead."""
    return getattr(getattr(request, "state", None), "tenant_org_id", None)


def require_org_id(request) -> str:
    """Extract and VALIDATE organization_id from request state.
    Raises HTTP 403 if org context is missing — use in ALL tenant-scoped routes.
    
    This is the mandatory guard for Pattern A multi-tenancy compliance.
    Every tenant-scoped DB query MUST use this instead of extract_org_id()."""
    from fastapi import HTTPException
    org_id = getattr(getattr(request, "state", None), "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    return org_id


def org_query(org_id: str, extra: dict = None) -> dict:
    """Build a MongoDB query dict with organization_id guard.
    Raises ValueError if org_id is falsy — prevents unscoped global queries."""
    if not org_id:
        raise ValueError(
            "org_query called with None org_id — "
            "this would produce an unscoped global query. "
            "Ensure extract_org_id() is called before org_query()."
        )
    q = {"organization_id": org_id}
    if extra:
        q.update(extra)
    return q


async def get_database():
    """Get database instance for dependency injection"""
    return db

async def close_database():
    """Close database connection"""
    client.close()
