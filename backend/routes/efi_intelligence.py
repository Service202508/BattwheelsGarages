"""
Battwheels OS - EFI Intelligence Engine Routes

API endpoints for:
- Model Risk Alerts (Part E - Pattern Detection)
- Failure Card Management
- Learning Stats
- Admin/Supervisor Dashboard Data

Note: Technicians see simplified guidance.
Complex analytics visible only to Supervisor/Admin.
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from core.subscriptions.entitlement import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/efi/intelligence", tags=["EFI Intelligence Engine"])


def get_db():
    from server import db
    return db


def get_continuous_learning_service():
    from services.continuous_learning_service import ContinuousLearningService
    db = get_db()
    return ContinuousLearningService(db)


def get_ranking_service():
    from services.model_aware_ranking_service import ModelAwareRankingService, RankingContext
    db = get_db()
    return ModelAwareRankingService(db)


# ==================== REQUEST MODELS ====================

class TicketClosureData(BaseModel):
    actual_root_cause: Optional[str] = None
    parts_replaced: List[str] = []
    repair_actions: List[str] = []
    ai_was_correct: Optional[bool] = None
    subsystem: Optional[str] = None
    unsafe_incident: bool = False


class AlertAcknowledgeRequest(BaseModel):
    resolution_notes: Optional[str] = None


class FailureCardCreate(BaseModel):
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    vehicle_category: str = "2W"
    subsystem: str
    symptom_cluster: List[str] = []
    dtc_codes: List[str] = []
    probable_root_cause: str
    verified_fix: str
    fix_steps: List[str] = []
    parts_required: List[str] = []
    estimated_repair_time_minutes: int = 60


class FailureCardUpdate(BaseModel):
    status: Optional[str] = None
    probable_root_cause: Optional[str] = None
    verified_fix: Optional[str] = None
    fix_steps: Optional[List[str]] = None
    parts_required: Optional[List[str]] = None


# ==================== FEATURE FLAG CHECK ====================

async def check_intelligence_enabled(org_id: str):
    """Check if EFI Intelligence Engine is enabled"""
    from services.feature_flags import FeatureFlagService
    db = get_db()
    flags = FeatureFlagService(db)
    config = await flags.get_tenant_config(org_id)
    
    if not config.get("efi_intelligence_engine_enabled", True):
        raise HTTPException(
            status_code=403,
            detail="EFI Intelligence Engine is not enabled for your organization"
        )


# ==================== MODEL RISK ALERTS (Part E) ====================

@router.get("/risk-alerts")
async def get_risk_alerts(
    http_request: Request,
    status: str = Query("active", description="Filter by status: active, acknowledged, resolved, all")
):
    """
    Get Model Risk Alerts for supervisor dashboard.
    Shows patterns: ≥3 similar failures in 30 days.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    await check_intelligence_enabled(org_id)
    
    db = get_db()
    
    query = {"organization_id": org_id}
    if status != "all":
        query["status"] = status
    
    alerts = await db.efi_model_risk_alerts.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "active_count": sum(1 for a in alerts if a.get("status") == "active")
    }


@router.get("/risk-alerts/{alert_id}")
async def get_risk_alert(alert_id: str, http_request: Request):
    """Get details of a specific risk alert"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    alert = await db.efi_model_risk_alerts.find_one(
        {"alert_id": alert_id, "organization_id": org_id},
        {"_id": 0}
    )
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert


@router.put("/risk-alerts/{alert_id}/acknowledge")
async def acknowledge_risk_alert(
    alert_id: str,
    data: AlertAcknowledgeRequest,
    http_request: Request
):
    """Acknowledge a risk alert (supervisor action)"""
    org_id = http_request.headers.get("X-Organization-ID")
    user_id = http_request.headers.get("X-User-ID", "unknown")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    result = await db.efi_model_risk_alerts.update_one(
        {"alert_id": alert_id, "organization_id": org_id},
        {
            "$set": {
                "status": "acknowledged",
                "acknowledged_by": user_id,
                "acknowledged_at": datetime.now(timezone.utc).isoformat(),
                "resolution_notes": data.resolution_notes
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"success": True, "message": "Alert acknowledged"}


@router.put("/risk-alerts/{alert_id}/resolve")
async def resolve_risk_alert(
    alert_id: str,
    data: AlertAcknowledgeRequest,
    http_request: Request
):
    """Resolve a risk alert"""
    org_id = http_request.headers.get("X-Organization-ID")
    user_id = http_request.headers.get("X-User-ID", "unknown")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    result = await db.efi_model_risk_alerts.update_one(
        {"alert_id": alert_id, "organization_id": org_id},
        {
            "$set": {
                "status": "resolved",
                "resolved_by": user_id,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "resolution_notes": data.resolution_notes
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"success": True, "message": "Alert resolved"}


# ==================== FAILURE CARDS ====================

@router.get("/failure-cards")
async def get_failure_cards(
    http_request: Request,
    status: str = Query("all", description="Filter: draft, pending_review, approved, all"),
    subsystem: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    """Get failure cards for knowledge management"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    await check_intelligence_enabled(org_id)
    
    db = get_db()
    
    query = {
        "$or": [
            {"organization_id": org_id},
            {"scope": "global"},
            {"organization_id": None}
        ]
    }
    
    if status != "all":
        query["status"] = status
    if subsystem:
        query["subsystem"] = {"$regex": subsystem, "$options": "i"}
    if vehicle_model:
        query["vehicle_model"] = {"$regex": vehicle_model, "$options": "i"}
    
    cards = await db.efi_failure_cards.find(
        query,
        {"_id": 0}
    ).sort("historical_success_rate", -1).limit(limit).to_list(limit)
    
    return {
        "failure_cards": cards,
        "total": len(cards)
    }


@router.get("/failure-cards/{card_id}")
async def get_failure_card(card_id: str, http_request: Request):
    """Get a specific failure card"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    card = await db.efi_failure_cards.find_one(
        {"failure_card_id": card_id},
        {"_id": 0}
    )
    
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    return card


@router.post("/failure-cards")
async def create_failure_card(
    data: FailureCardCreate,
    http_request: Request
):
    """Create a new failure card (requires approval)"""
    org_id = http_request.headers.get("X-Organization-ID")
    user_id = http_request.headers.get("X-User-ID", "unknown")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    await check_intelligence_enabled(org_id)
    
    db = get_db()
    
    import uuid
    card_id = f"FC-{uuid.uuid4().hex[:12].upper()}"
    
    card = {
        "failure_card_id": card_id,
        "organization_id": org_id,
        "scope": "tenant",
        
        # Vehicle
        "vehicle_make": data.vehicle_make,
        "vehicle_model": data.vehicle_model,
        "vehicle_variant": data.vehicle_variant,
        "vehicle_category": data.vehicle_category,
        
        # Issue
        "subsystem": data.subsystem,
        "symptom_cluster": data.symptom_cluster,
        "dtc_codes": data.dtc_codes,
        "dtc_code": data.dtc_codes[0] if data.dtc_codes else None,
        
        # Resolution
        "probable_root_cause": data.probable_root_cause,
        "verified_fix": data.verified_fix,
        "fix_steps": data.fix_steps,
        "parts_required": data.parts_required,
        "estimated_repair_time_minutes": data.estimated_repair_time_minutes,
        
        # Metrics
        "historical_success_rate": 0.5,
        "recurrence_counter": 0,
        "usage_count": 0,
        "positive_feedback_count": 0,
        "negative_feedback_count": 0,
        "confidence_score": 0.5,
        
        # Status
        "status": "draft",
        "source_type": "manual_entry",
        
        # Timestamps
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id
    }
    
    await db.efi_failure_cards.insert_one(card)
    
    return {"success": True, "failure_card_id": card_id}


@router.put("/failure-cards/{card_id}")
async def update_failure_card(
    card_id: str,
    data: FailureCardUpdate,
    http_request: Request
):
    """Update a failure card"""
    org_id = http_request.headers.get("X-Organization-ID")
    # user_id available for audit but not currently used
    _ = http_request.headers.get("X-User-ID", "unknown")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.efi_failure_cards.update_one(
        {"failure_card_id": card_id, "organization_id": org_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    return {"success": True}


@router.put("/failure-cards/{card_id}/approve")
async def approve_failure_card(card_id: str, http_request: Request):
    """Approve a draft failure card (supervisor action)"""
    org_id = http_request.headers.get("X-Organization-ID")
    user_id = http_request.headers.get("X-User-ID", "unknown")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    result = await db.efi_failure_cards.update_one(
        {"failure_card_id": card_id, "organization_id": org_id, "status": "draft"},
        {
            "$set": {
                "status": "approved",
                "approved_by": user_id,
                "approved_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Failure card not found or already approved")
    
    return {"success": True, "message": "Failure card approved"}


# ==================== LEARNING & RANKING ====================

@router.post("/learning/capture-closure/{ticket_id}")
async def capture_ticket_closure(
    ticket_id: str,
    data: TicketClosureData,
    http_request: Request
):
    """
    Capture learning data when ticket is closed.
    Called automatically by ticket closure flow.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_continuous_learning_service()
    
    event_id = await service.capture_ticket_closure(
        ticket_id=ticket_id,
        organization_id=org_id,
        closure_data=data.model_dump()
    )
    
    return {
        "success": True,
        "event_id": event_id,
        "message": "Learning data captured"
    }


@router.post("/learning/process-pending")
async def process_pending_learning(
    http_request: Request,
    batch_size: int = Query(50, le=100)
):
    """Process pending learning events (background job trigger)"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_continuous_learning_service()
    result = await service.process_pending_events(batch_size)
    
    return result


@router.get("/learning/stats")
async def get_learning_stats(http_request: Request):
    """Get learning statistics for supervisor dashboard"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    await check_intelligence_enabled(org_id)
    
    service = get_continuous_learning_service()
    stats = await service.get_learning_stats(org_id)
    
    return stats


@router.post("/ranking/rank-causes")
async def rank_probable_causes(
    http_request: Request,
    vehicle_make: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    subsystem: Optional[str] = None,
    symptoms: Optional[str] = None,  # Comma-separated
    dtc_codes: Optional[str] = None  # Comma-separated
):
    """
    Get ranked probable causes for given context.
    Used by guidance generation.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    from services.model_aware_ranking_service import RankingContext
    
    context = RankingContext(
        vehicle_make=vehicle_make,
        vehicle_model=vehicle_model,
        subsystem=subsystem,
        symptoms=symptoms.split(",") if symptoms else [],
        dtc_codes=dtc_codes.split(",") if dtc_codes else [],
        organization_id=org_id
    )
    
    service = get_ranking_service()
    ranked_causes, confidence = await service.rank_causes(context)
    
    # Check if escalation is recommended
    should_escalate, escalate_reason = await service.should_escalate(ranked_causes, confidence)
    
    # Get safe checklist if low confidence
    safe_checklist = []
    if confidence.value == "low":
        safe_checklist = await service.get_safe_checklist(context)
    
    return {
        "ranked_causes": [
            {
                "cause": c.cause,
                "confidence": c.confidence,
                "failure_card_id": c.failure_card_id,
                "evidence": c.evidence,
                "matching_factors": c.matching_factors
            }
            for c in ranked_causes
        ],
        "overall_confidence": confidence.value,
        "should_escalate": should_escalate,
        "escalate_reason": escalate_reason,
        "safe_checklist": safe_checklist
    }


# ==================== DASHBOARD SUMMARY ====================

@router.get("/dashboard-summary")
async def get_dashboard_summary(http_request: Request):
    """
    Get intelligence engine summary for supervisor dashboard.
    Includes risk alerts, learning stats, and failure card counts.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    await check_intelligence_enabled(org_id)
    
    db = get_db()
    
    # Active risk alerts
    active_alerts = await db.efi_model_risk_alerts.count_documents({
        "organization_id": org_id,
        "status": "active"
    })
    
    # Recent alerts (last 7 days)
    from datetime import timedelta
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_alerts = await db.efi_model_risk_alerts.find(
        {
            "organization_id": org_id,
            "created_at": {"$gte": seven_days_ago}
        },
        {"_id": 0, "alert_id": 1, "vehicle_model": 1, "subsystem": 1, "occurrence_count": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Failure card stats
    draft_cards = await db.efi_failure_cards.count_documents({
        "organization_id": org_id,
        "status": "draft"
    })
    approved_cards = await db.efi_failure_cards.count_documents({
        "$or": [
            {"organization_id": org_id, "status": "approved"},
            {"scope": "global", "status": "approved"}
        ]
    })
    
    # Learning queue
    pending_learning = await db.efi_learning_queue.count_documents({
        "organization_id": org_id,
        "status": "pending"
    })
    
    # Guidance stats
    guidance_count = await db.ai_guidance_snapshots.count_documents({
        "organization_id": org_id
    })
    
    # Feedback stats
    feedback_pipeline = [
        {"$match": {"organization_id": org_id}},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "helpful": {"$sum": {"$cond": ["$helped", 1, 0]}}
        }}
    ]
    feedback_result = await db.ai_guidance_feedback.aggregate(feedback_pipeline).to_list(1)
    feedback_stats = feedback_result[0] if feedback_result else {"total": 0, "helpful": 0}
    
    return {
        "risk_alerts": {
            "active": active_alerts,
            "recent": recent_alerts
        },
        "failure_cards": {
            "draft": draft_cards,
            "approved": approved_cards,
            "total": draft_cards + approved_cards
        },
        "learning": {
            "pending_events": pending_learning
        },
        "guidance": {
            "total_generated": guidance_count,
            "feedback_count": feedback_stats.get("total", 0),
            "helpful_rate": round(
                feedback_stats.get("helpful", 0) / max(feedback_stats.get("total", 1), 1) * 100, 1
            )
        }
    }
