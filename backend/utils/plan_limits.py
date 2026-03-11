"""
Plan Record Limit Enforcement
==============================
Utility to check record limits based on the organization's subscription plan.
Called from route handlers before creating new records.
"""
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Record limits by plan — only free_trial has limits
FREE_TRIAL_LIMITS = {
    "tickets": 20,
    "contacts": 10,
    "estimates": 10,
    "invoices": 10,
    "items": 20,
}

PLAN_HIERARCHY = {
    "free": 0,
    "free_trial": 0,
    "starter": 1,
    "professional": 2,
    "enterprise": 3,
}

_db = None

def init_record_limits(db):
    global _db
    _db = db

async def check_record_limit(org_id: str, resource: str):
    """
    Check if the organization has reached its record limit for a resource.
    Only enforces limits for free_trial plan. All other plans have unlimited.
    Raises HTTPException(403) if limit reached.
    """
    if _db is None or not org_id:
        return

    try:
        org = await _db.organizations.find_one(
            {"organization_id": org_id},
            {"_id": 0, "plan_type": 1}
        )
        plan_type = (org.get("plan_type", "free_trial") if org else "free_trial").lower()
    except Exception:
        return

    # Only free_trial has record limits
    if plan_type not in ("free", "free_trial"):
        return

    limit = FREE_TRIAL_LIMITS.get(resource)
    if not limit:
        return

    # Map resource to collection name
    collection_map = {
        "tickets": "tickets",
        "contacts": "contacts",
        "estimates": "estimates",
        "invoices": "invoices",
        "items": "items",
    }

    collection_name = collection_map.get(resource)
    if not collection_name:
        return

    try:
        collection = _db[collection_name]
        count = await collection.count_documents({"organization_id": org_id})

        if count >= limit:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "record_limit_reached",
                    "message": f"Free trial is limited to {limit} {resource}. Upgrade to create more.",
                    "current_count": count,
                    "limit": limit,
                    "resource": resource,
                    "upgrade_url": "/subscription",
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Record limit check failed for {resource}: {e}")
