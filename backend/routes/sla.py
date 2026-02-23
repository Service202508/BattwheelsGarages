"""
Battwheels OS - SLA (Service Level Agreement) Routes
=====================================================

SLA configuration, enforcement and breach tracking for service tickets.

SLA Tiers (default):
  CRITICAL: Response 1h | Resolution 4h
  HIGH:     Response 4h | Resolution 8h
  MEDIUM:   Response 8h | Resolution 24h
  LOW:      Response 24h | Resolution 72h
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sla", tags=["SLA"])


def get_db():
    from server import db
    return db


# ==================== DEFAULT SLA CONFIG ====================

DEFAULT_SLA_CONFIG = {
    "CRITICAL": {"response_hours": 1, "resolution_hours": 4},
    "HIGH": {"response_hours": 4, "resolution_hours": 8},
    "MEDIUM": {"response_hours": 8, "resolution_hours": 24},
    "LOW": {"response_hours": 24, "resolution_hours": 72},
}


# ==================== MODELS ====================

class SLATierConfig(BaseModel):
    response_hours: float = Field(..., gt=0, description="Hours to first response")
    resolution_hours: float = Field(..., gt=0, description="Hours to resolution")


class SLAConfig(BaseModel):
    CRITICAL: SLATierConfig = SLATierConfig(response_hours=1, resolution_hours=4)
    HIGH: SLATierConfig = SLATierConfig(response_hours=4, resolution_hours=8)
    MEDIUM: SLATierConfig = SLATierConfig(response_hours=8, resolution_hours=24)
    LOW: SLATierConfig = SLATierConfig(response_hours=24, resolution_hours=72)
    auto_reassign_on_breach: bool = False
    reassignment_delay_minutes: int = 30


# ==================== HELPERS ====================

async def get_org_id_from_request(request: Request) -> str:
    """Extract organization ID from JWT or header"""
    import jwt
    import os
    org_id = request.headers.get("X-Organization-ID")
    if not org_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                payload = jwt.decode(
                    auth_header.split(" ")[1],
                    os.environ.get("JWT_SECRET", "battwheels-secret"),
                    algorithms=["HS256"]
                )
                org_id = payload.get("org_id")
            except Exception:
                pass
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    return org_id


async def get_sla_config_for_org(org_id: str) -> Dict:
    """Get SLA config for an org, falling back to defaults"""
    db = get_db()
    org = await db.organizations.find_one(
        {"organization_id": org_id},
        {"_id": 0, "sla_config": 1}
    )
    if org and org.get("sla_config"):
        return org["sla_config"]
    return DEFAULT_SLA_CONFIG


def calculate_sla_deadlines(created_at: str, priority: str, sla_config: Dict) -> Dict:
    """Calculate SLA deadlines from ticket creation time"""
    priority_upper = priority.upper() if priority else "MEDIUM"
    tier = sla_config.get(priority_upper, DEFAULT_SLA_CONFIG.get("MEDIUM"))

    try:
        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
    except Exception:
        created_dt = datetime.now(timezone.utc)

    response_due = created_dt + timedelta(hours=tier["response_hours"])
    resolution_due = created_dt + timedelta(hours=tier["resolution_hours"])

    return {
        "sla_response_due_at": response_due.isoformat(),
        "sla_resolution_due_at": resolution_due.isoformat(),
        "sla_response_breached": False,
        "sla_resolution_breached": False,
        "sla_response_breached_at": None,
        "sla_resolution_breached_at": None,
        "first_response_at": None,
        "resolved_at": None
    }


# ==================== SLA ENDPOINTS ====================

@router.get("/config")
async def get_sla_config(request: Request):
    """Get SLA configuration for the organization"""
    org_id = await get_org_id_from_request(request)
    config = await get_sla_config_for_org(org_id)
    return {"code": 0, "sla_config": config}


@router.put("/config")
async def update_sla_config(config: SLAConfig, request: Request):
    """Update SLA configuration for the organization"""
    org_id = await get_org_id_from_request(request)
    db = get_db()

    sla_data = {
        "CRITICAL": config.CRITICAL.dict(),
        "HIGH": config.HIGH.dict(),
        "MEDIUM": config.MEDIUM.dict(),
        "LOW": config.LOW.dict()
    }

    await db.organizations.update_one(
        {"organization_id": org_id},
        {"$set": {"sla_config": sla_data, "sla_config_updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"code": 0, "message": "SLA configuration updated", "sla_config": sla_data}


@router.get("/status/{ticket_id}")
async def get_ticket_sla_status(ticket_id: str, request: Request):
    """Get SLA status for a specific ticket"""
    db = get_db()
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    now = datetime.now(timezone.utc)
    response_due = ticket.get("sla_response_due_at")
    resolution_due = ticket.get("sla_resolution_due_at")

    def time_info(due_str, breached, resolved_at):
        if not due_str:
            return {"status": "not_configured"}
        try:
            due_dt = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
            if due_dt.tzinfo is None:
                due_dt = due_dt.replace(tzinfo=timezone.utc)
        except Exception:
            return {"status": "error"}

        if resolved_at:
            return {"status": "MET", "due_at": due_str}
        if breached:
            delta = now - due_dt
            return {"status": "BREACHED", "due_at": due_str, "breached_by_minutes": int(delta.total_seconds() / 60)}
        remaining = due_dt - now
        remaining_minutes = int(remaining.total_seconds() / 60)
        if remaining_minutes <= 120:
            sla_health = "AT_RISK"
        elif remaining_minutes <= 0:
            sla_health = "BREACHED"
        else:
            sla_health = "ON_TRACK"
        return {
            "status": sla_health,
            "due_at": due_str,
            "remaining_minutes": max(0, remaining_minutes),
            "remaining_display": _format_time_remaining(remaining_minutes)
        }

    return {
        "code": 0,
        "ticket_id": ticket_id,
        "priority": ticket.get("priority", "medium"),
        "response_sla": time_info(
            response_due,
            ticket.get("sla_response_breached", False),
            ticket.get("first_response_at")
        ),
        "resolution_sla": time_info(
            resolution_due,
            ticket.get("sla_resolution_breached", False),
            ticket.get("resolved_at")
        )
    }


def _format_time_remaining(minutes: int) -> str:
    """Format minutes into human-readable string"""
    if minutes <= 0:
        return "Overdue"
    if minutes < 60:
        return f"{minutes}m remaining"
    hours = minutes // 60
    mins = minutes % 60
    if hours < 24:
        return f"{hours}h {mins}m remaining" if mins else f"{hours}h remaining"
    days = hours // 24
    hrs = hours % 24
    return f"{days}d {hrs}h remaining"


@router.get("/dashboard")
async def get_sla_dashboard(request: Request):
    """
    SLA dashboard stats: breaches today, at-risk tickets.
    """
    org_id = await get_org_id_from_request(request)
    db = get_db()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    # Breached today
    response_breaches = await db.tickets.count_documents({
        "organization_id": org_id,
        "sla_response_breached": True,
        "sla_response_breached_at": {"$gte": today_start}
    })
    resolution_breaches = await db.tickets.count_documents({
        "organization_id": org_id,
        "sla_resolution_breached": True,
        "sla_resolution_breached_at": {"$gte": today_start}
    })

    # At risk: resolution due within 2 hours and still open
    two_hours_later = (now + timedelta(hours=2)).isoformat()
    at_risk = await db.tickets.count_documents({
        "organization_id": org_id,
        "status": {"$in": ["open", "assigned", "work_in_progress"]},
        "sla_resolution_breached": {"$ne": True},
        "sla_resolution_due_at": {"$lte": two_hours_later, "$gte": now.isoformat()}
    })

    # Open tickets with breached SLA
    total_open_breached = await db.tickets.count_documents({
        "organization_id": org_id,
        "status": {"$in": ["open", "assigned", "work_in_progress"]},
        "$or": [
            {"sla_response_breached": True},
            {"sla_resolution_breached": True}
        ]
    })

    return {
        "code": 0,
        "sla_breaches_today": response_breaches + resolution_breaches,
        "at_risk_tickets": at_risk,
        "open_breached_tickets": total_open_breached,
        "stats": {
            "response_breaches_today": response_breaches,
            "resolution_breaches_today": resolution_breaches
        }
    }


@router.post("/check-breaches")
async def trigger_sla_breach_check(request: Request):
    """
    Manually trigger SLA breach check for the organization.
    Normally this runs as a background job every 5 minutes.
    """
    org_id = await get_org_id_from_request(request)
    result = await run_sla_breach_check(org_id)
    return {"code": 0, **result}


# ==================== SLA BACKGROUND JOB ====================

async def run_sla_breach_check(org_id: str = None) -> Dict:
    """
    Check all open tickets for SLA breaches.
    Called every 5 minutes by the background scheduler.
    If org_id is None, checks all organizations.
    """
    db = get_db()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    response_breaches = 0
    resolution_breaches = 0

    # Build base query
    base_query = {
        "status": {"$in": ["open", "assigned", "work_in_progress"]}
    }
    if org_id:
        base_query["organization_id"] = org_id

    # Check response SLA breaches (first response not given, deadline passed)
    response_breach_query = {
        **base_query,
        "sla_response_breached": {"$ne": True},
        "first_response_at": None,
        "sla_response_due_at": {"$lt": now_iso, "$exists": True}
    }
    response_breached_tickets = await db.tickets.find(
        response_breach_query,
        {"_id": 0, "ticket_id": 1, "title": 1, "priority": 1, "organization_id": 1, "customer_name": 1, "assigned_technician_id": 1}
    ).to_list(500)

    for ticket in response_breached_tickets:
        await db.tickets.update_one(
            {"ticket_id": ticket["ticket_id"]},
            {"$set": {
                "sla_response_breached": True,
                "sla_response_breached_at": now_iso
            }}
        )
        response_breaches += 1
        # Queue escalation notification (fire and forget)
        try:
            await _send_sla_breach_notification(ticket, "response", ticket.get("organization_id", org_id))
        except Exception as e:
            logger.warning(f"SLA notification failed for {ticket['ticket_id']}: {e}")

    # Check resolution SLA breaches (not resolved, deadline passed)
    resolution_breach_query = {
        **base_query,
        "sla_resolution_breached": {"$ne": True},
        "resolved_at": None,
        "sla_resolution_due_at": {"$lt": now_iso, "$exists": True}
    }
    resolution_breached_tickets = await db.tickets.find(
        resolution_breach_query,
        {"_id": 0, "ticket_id": 1, "title": 1, "priority": 1, "organization_id": 1, "customer_name": 1, "assigned_technician_id": 1}
    ).to_list(500)

    for ticket in resolution_breached_tickets:
        await db.tickets.update_one(
            {"ticket_id": ticket["ticket_id"]},
            {"$set": {
                "sla_resolution_breached": True,
                "sla_resolution_breached_at": now_iso
            }}
        )
        resolution_breaches += 1
        try:
            await _send_sla_breach_notification(ticket, "resolution", ticket.get("organization_id", org_id))
        except Exception as e:
            logger.warning(f"SLA notification failed for {ticket['ticket_id']}: {e}")

    logger.info(f"SLA breach check complete: {response_breaches} response, {resolution_breaches} resolution breaches")
    return {
        "response_breaches_found": response_breaches,
        "resolution_breaches_found": resolution_breaches,
        "checked_at": now_iso
    }


async def _send_sla_breach_notification(ticket: Dict, breach_type: str, org_id: str):
    """Send SLA breach email to admins"""
    try:
        from services.email_service import EmailService
        db = get_db()

        # Get admin emails for org
        admin_users = await db.users.find(
            {"organization_id": org_id, "role": {"$in": ["admin", "manager"]}},
            {"_id": 0, "email": 1, "name": 1}
        ).to_list(10)

        if not admin_users:
            return

        breach_label = "Response SLA" if breach_type == "response" else "Resolution SLA"
        subject = f"SLA Breach — Ticket {ticket.get('ticket_id')}: {ticket.get('title', 'No Title')}"
        body = f"""
SLA Breach Alert — {breach_label}

Ticket ID: {ticket.get('ticket_id')}
Title: {ticket.get('title', 'N/A')}
Priority: {ticket.get('priority', 'N/A').upper()}
Customer: {ticket.get('customer_name', 'N/A')}
SLA Breached: {breach_label}

Immediate attention required. Please log in to Battwheels OS to take action.
        """.strip()

        for admin in admin_users:
            if admin.get("email"):
                try:
                    await EmailService.send_generic_email(
                        to_email=admin["email"],
                        subject=subject,
                        body=body
                    )
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"SLA email error: {e}")


# ==================== BACKGROUND SCHEDULER ====================

import asyncio

_sla_task = None


async def sla_background_loop():
    """Background loop: check SLA breaches every 5 minutes"""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            await run_sla_breach_check()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"SLA background job error: {e}")
            await asyncio.sleep(60)  # Back off on error


def start_sla_background_job():
    """Start the SLA background job"""
    global _sla_task
    loop = asyncio.get_event_loop()
    _sla_task = loop.create_task(sla_background_loop())
    logger.info("SLA background job started (5-minute interval)")
