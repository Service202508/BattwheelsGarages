"""
Battwheels Knowledge Brain - AI Guidance Routes
API endpoints for EVFI Guidance Layer
"""

from fastapi import APIRouter, HTTPException, Request, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from services.ai_guidance_service import (
    AIGuidanceService, GuidanceContext, GuidanceMode,
    inject_safety_warning, classify_efi_response,
    EFI_DAILY_LIMITS, sanitize_efi_response, inject_watermark,
)
from services.visual_spec_service import VisualSpecService, EVDiagnosticTemplates
from services.feature_flags import FeatureFlagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/guidance", tags=["AI Guidance - Technician EVFI Layer"])


def get_db():
    from server import db
    return db


def get_guidance_service():
    db = get_db()
    return AIGuidanceService(db)


# ==================== REQUEST MODELS ====================

class GenerateGuidanceRequest(BaseModel):
    ticket_id: str
    mode: str = "quick"  # quick or deep
    force_regenerate: bool = False
    # Optional overrides
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    symptoms: Optional[List[str]] = None
    dtc_codes: Optional[List[str]] = None
    description: Optional[str] = None
    battery_soc: Optional[float] = None
    technician_notes: Optional[str] = None


class AskBackAnswersRequest(BaseModel):
    ticket_id: str
    answers: Dict[str, Any]


class GuidanceFeedbackRequest(BaseModel):
    guidance_id: str
    ticket_id: str
    helped: bool
    unsafe: bool = False
    step_failed: Optional[int] = None
    comment: Optional[str] = None


class AddToEstimateRequest(BaseModel):
    ticket_id: str
    estimate_id: Optional[str] = None
    items: List[Dict[str, Any]]


# ==================== GUIDANCE ENDPOINTS ====================

@router.get("/status")
async def get_guidance_status(http_request: Request):
    """
    Check if EVFI Guidance Layer is enabled for the organization.
    Returns feature flag status and configuration.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    feature_flags = FeatureFlagService(db)
    
    config = await feature_flags.get_tenant_config(org_id)
    
    return {
        "efi_guidance_enabled": config.get("efi_guidance_layer_enabled", False),
        "ai_assist_enabled": config.get("ai_assist_enabled", True),
        "features": {
            "hinglish_mode": True,
            "visual_diagrams": True,
            "ask_back": True,
            "estimate_suggestions": True
        },
        "organization_id": org_id
    }


@router.post("/generate")
async def generate_guidance(
    data: GenerateGuidanceRequest,
    http_request: Request
):
    """
    Generate EVFI guidance for a Job Card/Ticket.
    Rate-limited by plan, audit-logged, watermarked, and sanitized.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    user_id = http_request.headers.get("X-User-ID", "anonymous")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_guidance_service()
    db = get_db()
    
    # Check if enabled
    if not await service.is_enabled(org_id):
        raise HTTPException(
            status_code=403,
            detail="EVFI Guidance Layer is not enabled for your organization."
        )
    
    # ── Rate Limit (per day by plan) ──
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    org_doc = await db.organizations.find_one(
        {"organization_id": org_id}, {"_id": 0, "plan_type": 1}
    )
    plan_code = (org_doc or {}).get("plan_type", "starter")
    daily_limit = EFI_DAILY_LIMITS.get(plan_code, 20)

    if daily_limit != -1:
        usage = await db.ai_usage.find_one(
            {"organization_id": org_id, "date": today}, {"_id": 0, "guidance_count": 1}
        )
        current_count = (usage or {}).get("guidance_count", 0)
        if current_count >= daily_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Daily EVFI limit reached ({daily_limit}/day on {plan_code} plan). Upgrade for more."
            )
    
    # Get ticket context from database
    ticket = await db.tickets.find_one(
        {"ticket_id": data.ticket_id},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Build context (use overrides if provided, else from ticket)
    context = GuidanceContext(
        ticket_id=data.ticket_id,
        organization_id=org_id,
        vehicle_make=data.vehicle_make or ticket.get("vehicle_info", {}).get("make"),
        vehicle_model=data.vehicle_model or ticket.get("vehicle_info", {}).get("model"),
        vehicle_variant=ticket.get("vehicle_info", {}).get("variant"),
        symptoms=data.symptoms or ticket.get("symptoms", []),
        dtc_codes=data.dtc_codes or ticket.get("dtc_codes", []),
        category=ticket.get("category", "general"),
        description=data.description or ticket.get("description", ""),
        last_repair_notes=ticket.get("last_repair_notes"),
        battery_soc=data.battery_soc or ticket.get("battery_soc"),
        odometer=ticket.get("odometer"),
        technician_notes=data.technician_notes or ticket.get("technician_notes"),
        ask_back_answers=ticket.get("ask_back_answers")
    )
    
    # Parse mode
    mode = GuidanceMode.DEEP if data.mode == "deep" else GuidanceMode.QUICK
    
    # Generate guidance
    result = await service.generate_guidance(
        context=context,
        mode=mode,
        force_regenerate=data.force_regenerate
    )
    
    # Track usage
    await db.ai_usage.update_one(
        {"organization_id": org_id, "date": today},
        {
            "$inc": {"guidance_count": 1},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    # ── Audit Log ──
    await db.efi_audit_log.insert_one({
        "user_id": user_id,
        "organization_id": org_id,
        "ticket_id": data.ticket_id,
        "mode": data.mode,
        "query": (data.description or ticket.get("description", ""))[:500],
        "guidance_id": result.get("guidance_id"),
        "from_cache": result.get("from_cache", False),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    # ── Watermark guidance text with org_id ──
    if result.get("guidance_text"):
        result["guidance_text"] = inject_watermark(result["guidance_text"], org_id)
    
    # ── Sanitize: strip internal data before returning ──
    return sanitize_efi_response(result)
    
    return result


@router.post("/ask-back")
async def submit_ask_back_answers(
    data: AskBackAnswersRequest,
    http_request: Request
):
    """
    Submit answers to ask-back questions and regenerate guidance.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_guidance_service()
    
    # Update ticket with answers
    await service.update_context_with_answers(data.ticket_id, data.answers)
    
    # Regenerate guidance with new context
    request = GenerateGuidanceRequest(
        ticket_id=data.ticket_id,
        mode="quick",
        force_regenerate=True
    )
    
    # Add org header for recursive call
    return await generate_guidance(request, http_request)


@router.post("/feedback")
async def submit_guidance_feedback(
    data: GuidanceFeedbackRequest,
    http_request: Request
):
    """
    Submit feedback on guidance quality.
    Used to improve AI guidance over time.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    user_id = http_request.headers.get("X-User-ID", "anonymous")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_guidance_service()
    
    success = await service.submit_feedback(
        guidance_id=data.guidance_id,
        ticket_id=data.ticket_id,
        organization_id=org_id,
        user_id=user_id,
        helped=data.helped,
        unsafe=data.unsafe,
        step_failed=data.step_failed,
        comment=data.comment
    )
    
    return {"success": success, "message": "Feedback recorded. Dhanyavaad!"}


@router.get("/ticket/{ticket_id}")
async def get_guidance_for_ticket(http_request: Request, ticket_id: str, mode: str = "quick"):
    """
    Get existing guidance for a ticket (or generate if not exists).
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    # Check cache first
    db = get_db()
    cached = await db.ai_guidance_snapshots.find_one(
        {"ticket_id": ticket_id, "mode": mode},
        {"_id": 0}
    )
    
    if cached:
        # Ensure efi_classification is present on cached results
        if "efi_classification" not in cached:
            ticket = await db.tickets.find_one(
                {"ticket_id": ticket_id}, {"_id": 0}
            )
            if ticket:
                cached["efi_classification"] = classify_efi_response(ticket)
        return cached
    
    # Generate new guidance
    request = GenerateGuidanceRequest(ticket_id=ticket_id, mode=mode)
    return await generate_guidance(request, http_request)


# ==================== ESTIMATE INTEGRATION ====================

@router.post("/add-to-estimate")
async def add_suggestions_to_estimate(
    data: AddToEstimateRequest,
    http_request: Request
):
    """
    Add suggested parts/labour to the linked estimate.
    One-click integration from guidance panel.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    user_id = http_request.headers.get("X-User-ID", "system")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    # Get ticket to find linked estimate
    ticket = await db.tickets.find_one(
        {"ticket_id": data.ticket_id},
        {"_id": 0, "estimate_id": 1}
    )
    
    estimate_id = data.estimate_id or (ticket.get("estimate_id") if ticket else None)
    
    if not estimate_id:
        # Create new estimate if none exists
        from datetime import datetime
        import uuid
        
        estimate_id = f"EST-{uuid.uuid4().hex[:8].upper()}"
        new_estimate = {
            "estimate_id": estimate_id,
            "ticket_id": data.ticket_id,
            "organization_id": org_id,
            "status": "draft",
            "line_items": [],
            "sub_total": 0,
            "tax_total": 0,
            "grand_total": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id,
            "created_via": "ai_guidance"
        }
        await db.estimates.insert_one(new_estimate)
        
        # Link to ticket
        await db.tickets.update_one(
            {"ticket_id": data.ticket_id},
            {"$set": {"estimate_id": estimate_id}}
        )
    
    # Add items to estimate
    added_items = []
    for item in data.items:
        line_item = {
            "line_item_id": f"LI-{uuid.uuid4().hex[:6].upper()}",
            "type": item.get("type", "part"),
            "name": item.get("name", "Unknown Item"),
            "description": item.get("description", ""),
            "quantity": item.get("quantity", 1),
            "unit_price": item.get("estimated_cost", 0),
            "total": item.get("quantity", 1) * item.get("estimated_cost", 0),
            "added_via": "ai_guidance",
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        added_items.append(line_item)
    
    # Update estimate
    await db.estimates.update_one(
        {"estimate_id": estimate_id},
        {
            "$push": {"line_items": {"$each": added_items}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Recalculate totals
    estimate = await db.estimates.find_one({"estimate_id": estimate_id})
    if estimate:
        sub_total = sum(item.get("total", 0) for item in estimate.get("line_items", []))
        tax_total = sub_total * 0.18  # 18% GST
        grand_total = sub_total + tax_total
        
        await db.estimates.update_one(
            {"estimate_id": estimate_id},
            {"$set": {
                "sub_total": sub_total,
                "tax_total": round(tax_total, 2),
                "grand_total": round(grand_total, 2)
            }}
        )
    
    return {
        "success": True,
        "estimate_id": estimate_id,
        "items_added": len(added_items),
        "message": f"{len(added_items)} items added to estimate"
    }


# ==================== VISUAL TEMPLATES ====================

@router.get("/templates/diagrams")
async def get_diagram_templates():
    """
    Get predefined diagnostic flow templates.
    """
    return {
        "templates": [
            {
                "id": "battery_not_charging",
                "title": "Battery Not Charging",
                "category": "battery",
                "diagram": EVDiagnosticTemplates.battery_not_charging_flow()
            },
            {
                "id": "motor_not_running",
                "title": "Motor Not Running",
                "category": "motor",
                "diagram": EVDiagnosticTemplates.motor_not_running_flow()
            },
            {
                "id": "range_anxiety",
                "title": "Reduced Range",
                "category": "battery",
                "diagram": EVDiagnosticTemplates.range_anxiety_flow()
            }
        ]
    }


@router.get("/templates/checklist/{category}")
async def get_checklist_template(category: str):
    """
    Get diagnostic checklist template for a category.
    """
    checklists = {
        "battery": {
            "title": "Battery Diagnostic Checklist",
            "items": [
                {"title": "HV isolation verified", "severity": "critical"},
                {"title": "PPE worn (gloves, safety glasses)", "severity": "critical"},
                {"title": "12V auxiliary battery voltage checked", "severity": "normal"},
                {"title": "BMS communication active", "severity": "normal"},
                {"title": "Cell voltages balanced (±50mV)", "severity": "normal"},
                {"title": "Pack temperature normal (15-35°C)", "severity": "normal"},
                {"title": "No physical damage or swelling", "severity": "high"},
                {"title": "Connector seating verified", "severity": "normal"}
            ]
        },
        "motor": {
            "title": "Motor Diagnostic Checklist",
            "items": [
                {"title": "HV isolation verified", "severity": "critical"},
                {"title": "Kill switch position checked", "severity": "normal"},
                {"title": "Side stand sensor functional", "severity": "normal"},
                {"title": "Throttle position sensor working", "severity": "normal"},
                {"title": "Motor controller powered", "severity": "normal"},
                {"title": "Hall sensors tested (3 signals)", "severity": "normal"},
                {"title": "Phase wires continuity checked", "severity": "normal"},
                {"title": "Motor free spin test passed", "severity": "normal"}
            ]
        },
        "charger": {
            "title": "Charger Diagnostic Checklist",
            "items": [
                {"title": "Mains supply voltage verified", "severity": "normal"},
                {"title": "Charging port clean and undamaged", "severity": "normal"},
                {"title": "Charger LED status checked", "severity": "normal"},
                {"title": "Charging cable inspected", "severity": "normal"},
                {"title": "Onboard charger output tested", "severity": "normal"},
                {"title": "BMS charge enable signal present", "severity": "normal"}
            ]
        },
        "electrical": {
            "title": "Electrical Diagnostic Checklist",
            "items": [
                {"title": "Fuse box inspection", "severity": "normal"},
                {"title": "Main relay operation tested", "severity": "normal"},
                {"title": "Wiring harness visual inspection", "severity": "normal"},
                {"title": "Ground connections verified", "severity": "normal"},
                {"title": "DC-DC converter output checked", "severity": "normal"},
                {"title": "Contactor operation verified", "severity": "normal"}
            ]
        }
    }
    
    checklist = checklists.get(category, checklists.get("electrical"))
    
    return VisualSpecService.generate_troubleshooting_checklist_spec(
        checklist["items"]
    )


# ==================== SNAPSHOT MANAGEMENT ====================

@router.get("/snapshot/{ticket_id}")
async def get_snapshot_info(http_request: Request, ticket_id: str, mode: str = "quick"):
    """
    Get snapshot info for a ticket.
    Used to show "Regenerate" button only when context changed.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_guidance_service()
    snapshot = await service.get_snapshot_info(ticket_id, mode)
    
    if not snapshot:
        return {
            "exists": False,
            "ticket_id": ticket_id,
            "mode": mode
        }
    
    return {
        "exists": True,
        "ticket_id": ticket_id,
        "mode": mode,
        **snapshot
    }


@router.post("/check-context")
async def check_context_changed(
    data: GenerateGuidanceRequest,
    http_request: Request
):
    """
    Check if context has changed since last snapshot.
    Returns whether regeneration is needed.
    
    Use this before calling generate to determine if
    "Regenerate" button should be shown.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    # Get ticket
    ticket = await db.tickets.find_one(
        {"ticket_id": data.ticket_id},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Build context
    context = GuidanceContext(
        ticket_id=data.ticket_id,
        organization_id=org_id,
        vehicle_make=data.vehicle_make or ticket.get("vehicle_info", {}).get("make"),
        vehicle_model=data.vehicle_model or ticket.get("vehicle_info", {}).get("model"),
        vehicle_variant=ticket.get("vehicle_info", {}).get("variant"),
        symptoms=data.symptoms or ticket.get("symptoms", []),
        dtc_codes=data.dtc_codes or ticket.get("dtc_codes", []),
        category=ticket.get("category", "general"),
        description=data.description or ticket.get("description", ""),
        ask_back_answers=ticket.get("ask_back_answers")
    )
    
    service = get_guidance_service()
    result = await service.check_context_changed(context, data.mode)
    
    return {
        "ticket_id": data.ticket_id,
        "mode": data.mode,
        **result
    }


@router.get("/feedback-summary/{guidance_id}")
async def get_feedback_summary(
    guidance_id: str,
    http_request: Request
):
    """
    Get feedback summary for a guidance snapshot.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_guidance_service()
    return await service.get_feedback_summary(guidance_id)


# ==================== METRICS ====================

@router.get("/metrics")
async def get_guidance_metrics(http_request: Request, days: int = Query(7, le=30)
):
    """
    Get AI guidance usage metrics.
    """
    org_id = getattr(http_request.state, "tenant_org_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    # Get guidance stats (tenant isolated)
    guidance_count = await db.ai_guidance_snapshots.count_documents({
        "organization_id": org_id
    })
    
    # Get active snapshots
    active_snapshots = await db.ai_guidance_snapshots.count_documents({
        "organization_id": org_id,
        "status": "active"
    })
    
    # Get feedback stats
    pipeline = [
        {"$match": {"organization_id": org_id}},
        {"$group": {
            "_id": None,
            "total_feedback": {"$sum": 1},
            "helpful_count": {"$sum": {"$cond": ["$helped", 1, 0]}},
            "unsafe_reports": {"$sum": {"$cond": ["$unsafe", 1, 0]}},
            "avg_rating": {"$avg": "$rating"}
        }}
    ]
    
    feedback_stats = await db.ai_guidance_feedback.aggregate(pipeline).to_list(1)
    feedback = feedback_stats[0] if feedback_stats else {
        "total_feedback": 0,
        "helpful_count": 0,
        "unsafe_reports": 0,
        "avg_rating": 0
    }
    
    # Get estimate integration stats
    estimate_items = await db.estimates.count_documents({
        "organization_id": org_id,
        "line_items.added_via": "ai_guidance"
    })
    
    # Get learning queue stats
    pending_learning = await db.efi_learning_queue.count_documents({
        "organization_id": org_id,
        "status": "pending"
    })
    
    return {
        "organization_id": org_id,
        "metrics": {
            "guidance_generated": guidance_count,
            "active_snapshots": active_snapshots,
            "total_feedback": feedback.get("total_feedback", 0),
            "helpful_rate": round(
                feedback.get("helpful_count", 0) / max(feedback.get("total_feedback", 1), 1) * 100, 1
            ),
            "avg_rating": round(feedback.get("avg_rating") or 0, 1),
            "unsafe_reports": feedback.get("unsafe_reports", 0),
            "estimate_integrations": estimate_items,
            "pending_learning_events": pending_learning
        }
    }
