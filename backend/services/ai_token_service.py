"""
AI Diagnostic Token Service
============================
Manages per-org monthly AI diagnostic token allocations.
One token = one new EFI diagnostic session started.
Viewing past results does NOT consume tokens.

Token Allocations:
  Free Trial (14 days): 10 tokens total (not monthly)
  Starter 2,999/mo:     25 tokens/month
  Professional 5,999/mo: 100 tokens/month
  Enterprise:            Unlimited (no limit enforced)
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_db = None


def init_ai_token_service(db):
    global _db
    _db = db


PLAN_TOKEN_LIMITS = {
    "free_trial": 10,
    "free": 10,
    "starter": 25,
    "professional": 100,
    "enterprise": -1,  # unlimited
}


def get_plan_token_limit(plan_name: str) -> int:
    """Return the token limit for a plan. -1 means unlimited."""
    return PLAN_TOKEN_LIMITS.get(plan_name, 0)


async def _get_org_plan(org_id: str) -> dict:
    """Fetch org document and return plan + created_at."""
    org = await _db.organizations.find_one(
        {"organization_id": org_id},
        {"_id": 0, "plan": 1, "plan_type": 1, "created_at": 1}
    )
    if not org:
        return {"plan": "free", "created_at": None}
    plan = org.get("plan") or org.get("plan_type") or "free"
    return {"plan": plan, "created_at": org.get("created_at")}


def _is_free_trial_expired(created_at) -> bool:
    """Check if free trial (14 days) has expired."""
    if not created_at:
        return True
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created_at > timedelta(days=14)


async def get_token_status(org_id: str) -> dict:
    """
    Get current token status for an org.
    Performs lazy monthly reset when stored month != current month.
    """
    org_info = await _get_org_plan(org_id)
    plan = org_info["plan"]
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")

    limit = get_plan_token_limit(plan)

    # Free trial: check expiry
    if plan in ("free_trial", "free"):
        if _is_free_trial_expired(org_info["created_at"]):
            limit = 0

    # Enterprise: unlimited
    if limit == -1:
        usage = await _db.ai_usage.find_one(
            {"organization_id": org_id, "month": current_month},
            {"_id": 0}
        )
        tokens_used = usage["tokens_used"] if usage else 0
        return {
            "tokens_used": tokens_used,
            "tokens_limit": -1,
            "tokens_remaining": -1,
            "plan": plan,
            "unlimited": True,
            "month": current_month,
        }

    # Find or create usage doc
    usage = await _db.ai_usage.find_one(
        {"organization_id": org_id, "month": current_month},
        {"_id": 0}
    )

    if not usage:
        # Lazy reset: create new month doc
        usage = {
            "organization_id": org_id,
            "month": current_month,
            "tokens_used": 0,
            "tokens_limit": limit,
            "plan": plan,
            "sessions": [],
        }
        await _db.ai_usage.insert_one(usage)
        usage.pop("_id", None)
    elif usage.get("month") != current_month:
        # Should not happen since we query by month, but safety
        usage["tokens_used"] = 0
        usage["month"] = current_month
        usage["tokens_limit"] = limit

    # Always sync limit from plan (plan could have changed)
    usage["tokens_limit"] = limit

    remaining = max(0, limit - usage["tokens_used"])

    return {
        "tokens_used": usage["tokens_used"],
        "tokens_limit": limit,
        "tokens_remaining": remaining,
        "plan": plan,
        "unlimited": False,
        "month": current_month,
    }


async def consume_token(org_id: str, session_id: str, ticket_id: str) -> dict:
    """
    Consume one AI diagnostic token.
    Returns {success: True, tokens_remaining} or {success: False, error: ...}
    """
    status = await get_token_status(org_id)

    # Enterprise: unlimited, always allow
    if status.get("unlimited"):
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        await _db.ai_usage.update_one(
            {"organization_id": org_id, "month": current_month},
            {
                "$inc": {"tokens_used": 1},
                "$push": {"sessions": {
                    "session_id": session_id,
                    "ticket_id": ticket_id,
                    "used_at": datetime.now(timezone.utc).isoformat(),
                }},
                "$setOnInsert": {
                    "organization_id": org_id,
                    "month": current_month,
                    "tokens_limit": -1,
                    "plan": status["plan"],
                },
            },
            upsert=True,
        )
        return {"success": True, "tokens_remaining": -1, "unlimited": True}

    # Check if tokens remain
    if status["tokens_remaining"] <= 0:
        return {
            "success": False,
            "error": "Monthly diagnostic limit reached",
            "tokens_used": status["tokens_used"],
            "tokens_limit": status["tokens_limit"],
        }

    current_month = status["month"]

    await _db.ai_usage.update_one(
        {"organization_id": org_id, "month": current_month},
        {
            "$inc": {"tokens_used": 1},
            "$push": {"sessions": {
                "session_id": session_id,
                "ticket_id": ticket_id,
                "used_at": datetime.now(timezone.utc).isoformat(),
            }},
        },
    )

    new_remaining = status["tokens_remaining"] - 1
    return {"success": True, "tokens_remaining": new_remaining}
