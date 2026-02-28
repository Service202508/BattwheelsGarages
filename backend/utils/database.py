"""
Battwheels OS - Database Configuration
Centralized database connection and utilities
"""
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_os")

# Create client and database
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def extract_org_id(request) -> Optional[str]:
    """Extract organization_id from request headers.
    This is the canonical way to get org context in route handlers.
    Every DB query on tenant data MUST use this."""
    org_id = request.headers.get("X-Organization-ID") or request.headers.get("x-organization-id")
    if not org_id:
        # Fallback: check request state (set by tenant middleware)
        org_id = getattr(getattr(request, "state", None), "tenant_org_id", None)
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
