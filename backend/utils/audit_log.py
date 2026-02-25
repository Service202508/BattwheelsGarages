"""
Audit Logging for Financial Mutations
======================================
C-05: Non-repudiable audit trail for all financial events.
Writes to: audit_logs (pre-existing collection, NOT audit_log).
Schema matches pre-existing: organization_id, user_id, user_role, action,
        resource_type, resource_id, timestamp, ip_address, details,
        before_snapshot, after_snapshot.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request
import logging
import os
import motor.motor_asyncio

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
_db = _client[DB_NAME]
audit_collection = _db["audit_logs"]  # Pre-existing collection — NOT audit_log


def _extract_request_context(request: Optional[Request]) -> dict:
    """Extract user_id, user_role, ip_address from a FastAPI Request."""
    if not request:
        return {"user_id": "", "user_role": "", "ip_address": ""}

    user_id = getattr(request.state, "tenant_user_id", "") or ""
    user_role = getattr(request.state, "tenant_user_role", None) or getattr(request.state, "user_role", "unknown")

    # IP from X-Forwarded-For (Kubernetes ingress) or direct client
    ip_address = ""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    elif hasattr(request, "client") and request.client:
        ip_address = request.client.host or ""

    return {"user_id": user_id, "user_role": user_role, "ip_address": ip_address}


async def log_financial_action(
    org_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    request: Optional[Request] = None,
    before_snapshot: Optional[dict] = None,
    after_snapshot: Optional[dict] = None,
    user_id: str = "",
    user_role: str = "",
    details: Optional[dict] = None,
):
    """
    Write one audit log entry to the audit_logs collection.

    Parameters
    ----------
    org_id : str          – Organization ID (tenant scope)
    action : str          – CREATE / UPDATE / VOID / DELETE / APPROVE etc.
    entity_type : str     – invoice / credit_note / journal_entry / payment / ticket / estimate etc.
    entity_id : str       – Primary key of the entity
    request : Request     – FastAPI request (extracts user_id, role, ip)
    before_snapshot : dict – State before mutation (None for CREATE)
    after_snapshot : dict  – State after mutation
    user_id : str         – Override user_id (for service-layer calls without request)
    user_role : str       – Override user_role
    details : dict        – Additional context (matches pre-existing schema)
    """
    ctx = _extract_request_context(request)

    entry = {
        "organization_id": org_id or "",
        "user_id": ctx["user_id"] or user_id,
        "user_role": ctx["user_role"] or user_role,
        "action": action,
        "resource_type": entity_type,
        "resource_id": entity_id,
        "timestamp": datetime.now(timezone.utc),
        "ip_address": ctx["ip_address"],
        "before_snapshot": before_snapshot,
        "after_snapshot": after_snapshot,
        "details": details,
    }

    try:
        await audit_collection.insert_one(entry)
        logger.info(f"AUDIT: {action} {entity_type} {entity_id} by {entry['user_id']} in org {org_id}")
    except Exception as e:
        # Audit log failures must not break the main operation
        logger.error(f"AUDIT LOG FAILED: {action} {entity_type} {entity_id} — {e}")
