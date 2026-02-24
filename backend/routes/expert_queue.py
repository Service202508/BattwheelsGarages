"""
Battwheels Knowledge Brain - Expert Queue Routes
API endpoints for internal escalation management
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from services.expert_queue_service import ExpertQueueService, ExpertQueueStatus
from services.feature_flags import require_ai_enabled

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expert-queue", tags=["Expert Queue - Escalation Management"])


def get_db():
    from server import db
    return db


def get_expert_queue_service():
    db = get_db()
    return ExpertQueueService(db)


# ==================== MODELS ====================

class AssignExpertRequest(BaseModel):
    expert_id: str
    expert_name: str


class ResolveEscalationRequest(BaseModel):
    response: str
    resolution_notes: str
    capture_knowledge: bool = True


class AddCommentRequest(BaseModel):
    comment: str
    is_internal: bool = False


class RequestInfoRequest(BaseModel):
    request_details: str


# ==================== ESCALATION ENDPOINTS ====================

@router.get("/escalations")
async def list_escalations(http_request: Request, status: Optional[str] = None, priority: Optional[str] = None, assigned_to: Optional[str] = None, limit: int = Query(50, le=100),
    offset: int = 0
):
    """
    List escalations in the expert queue.
    Filter by status, priority, or assigned expert.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_expert_queue_service()
    result = await service.list_escalations(
        organization_id=org_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset
    )
    
    return result


@router.get("/escalations/{escalation_id}")
async def get_escalation(
    escalation_id: str,
    http_request: Request
):
    """Get details of a specific escalation"""
    service = get_expert_queue_service()
    escalation = await service.get_escalation(escalation_id)
    
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    return escalation


@router.post("/escalations/{escalation_id}/assign")
async def assign_expert(
    escalation_id: str,
    data: AssignExpertRequest,
    http_request: Request
):
    """Assign an expert to handle the escalation"""
    user_id = http_request.headers.get("X-User-ID", "system")
    
    service = get_expert_queue_service()
    result = await service.assign_expert(
        escalation_id=escalation_id,
        expert_id=data.expert_id,
        expert_name=data.expert_name,
        assigned_by=user_id
    )
    
    if result.get("status") == "failed":
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    return result


@router.post("/escalations/{escalation_id}/start")
async def start_work(
    escalation_id: str,
    http_request: Request
):
    """Mark escalation as in-progress (expert started working)"""
    expert_id = http_request.headers.get("X-User-ID")
    if not expert_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    service = get_expert_queue_service()
    result = await service.start_work(escalation_id, expert_id)
    
    if result.get("status") == "failed":
        raise HTTPException(status_code=404, detail="Escalation not found or not assigned to you")
    
    return result


@router.post("/escalations/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: str,
    data: ResolveEscalationRequest,
    http_request: Request
):
    """
    Resolve an escalation with expert response.
    Optionally captures resolution as new knowledge.
    """
    expert_id = http_request.headers.get("X-User-ID")
    expert_name = http_request.headers.get("X-User-Name", "Expert")
    
    if not expert_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    service = get_expert_queue_service()
    result = await service.resolve_escalation(
        escalation_id=escalation_id,
        expert_id=expert_id,
        expert_name=expert_name,
        response=data.response,
        resolution_notes=data.resolution_notes,
        capture_knowledge=data.capture_knowledge
    )
    
    if result.get("status") == "failed":
        raise HTTPException(status_code=404, detail=result.get("message", "Failed to resolve"))
    
    return result


@router.post("/escalations/{escalation_id}/comment")
async def add_comment(
    escalation_id: str,
    data: AddCommentRequest,
    http_request: Request
):
    """Add a comment to the escalation timeline"""
    user_id = http_request.headers.get("X-User-ID", "system")
    user_name = http_request.headers.get("X-User-Name", "User")
    
    service = get_expert_queue_service()
    result = await service.add_comment(
        escalation_id=escalation_id,
        user_id=user_id,
        user_name=user_name,
        comment=data.comment,
        is_internal=data.is_internal
    )
    
    if result.get("status") == "failed":
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    return result


@router.post("/escalations/{escalation_id}/request-info")
async def request_info(
    escalation_id: str,
    data: RequestInfoRequest,
    http_request: Request
):
    """Request additional information from the requester"""
    expert_id = http_request.headers.get("X-User-ID")
    expert_name = http_request.headers.get("X-User-Name", "Expert")
    
    if not expert_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    service = get_expert_queue_service()
    result = await service.request_info(
        escalation_id=escalation_id,
        expert_id=expert_id,
        expert_name=expert_name,
        request_details=data.request_details
    )
    
    if result.get("status") == "failed":
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    return result


# ==================== DASHBOARD / STATS ====================

@router.get("/stats")
async def get_queue_stats(http_request: Request):
    """Get expert queue statistics for the organization"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_expert_queue_service()
    stats = await service.get_queue_stats(org_id)
    
    return stats


@router.get("/workload")
async def get_expert_workload(http_request: Request):
    """Get workload summary per expert"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_expert_queue_service()
    workload = await service.get_expert_workload(org_id)
    
    return {"experts": workload}


@router.get("/my-queue")
async def get_my_queue(http_request: Request, status: Optional[str] = None, limit: int = Query(20, le=100)
):
    """Get escalations assigned to the current expert"""
    org_id = http_request.headers.get("X-Organization-ID")
    expert_id = http_request.headers.get("X-User-ID")
    
    if not org_id or not expert_id:
        raise HTTPException(status_code=400, detail="Organization ID and User ID required")
    
    service = get_expert_queue_service()
    result = await service.list_escalations(
        organization_id=org_id,
        status=status,
        assigned_to=expert_id,
        limit=limit
    )
    
    return result


# ==================== EXPERT ROSTER ====================

class ExpertRosterEntry(BaseModel):
    user_id: str
    user_name: str
    specializations: List[str] = []
    max_concurrent: int = 5
    is_available: bool = True


@router.post("/experts")
async def add_expert_to_roster(
    data: ExpertRosterEntry,
    http_request: Request
):
    """Add an expert to the roster"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    expert_doc = {
        "user_id": data.user_id,
        "user_name": data.user_name,
        "organization_id": org_id,
        "specializations": data.specializations,
        "max_concurrent": data.max_concurrent,
        "is_available": data.is_available,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.expert_roster.update_one(
        {"user_id": data.user_id, "organization_id": org_id},
        {"$set": expert_doc},
        upsert=True
    )
    
    return {"status": "added", "user_id": data.user_id}


@router.get("/experts")
async def list_experts(http_request: Request):
    """List all experts in the roster"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    experts = await db.expert_roster.find(
        {"organization_id": org_id},
        {"_id": 0}
    ).to_list(100)
    
    return {"experts": experts}


@router.delete("/experts/{user_id}")
async def remove_expert_from_roster(
    user_id: str,
    http_request: Request
):
    """Remove an expert from the roster"""
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    db = get_db()
    
    result = await db.expert_roster.delete_one({
        "user_id": user_id,
        "organization_id": org_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expert not found")
    
    return {"status": "removed", "user_id": user_id}
