"""
Battwheels Knowledge Brain - AI Assistant Routes
Centralized AI assistance API for all portals
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import uuid
import logging

from models.knowledge_brain import (
    AIQueryRequest, AIQueryResponse, AIFeedback, EscalationRequest,
    KnowledgeType, KnowledgeScope, ApprovalStatus
)
from services.ai_assist_service import AIAssistService
from services.knowledge_store_service import KnowledgeStoreService
from utils.database import extract_org_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Assistant - Knowledge Brain"])


def get_db():
    from server import db
    return db


def get_ai_service():
    db = get_db()
    return AIAssistService(db)


def get_knowledge_store():
    db = get_db()
    return KnowledgeStoreService(db)


# ==================== AI QUERY ENDPOINTS ====================

@router.post("/assist/query", response_model=AIQueryResponse)
async def ai_assist_query(
    request: AIQueryRequest,
    http_request: Request
):
    """
    Main AI assistance query endpoint.
    Implements RAG pipeline with source citations.
    
    Use for:
    - Fault diagnosis queries
    - Repair procedure lookups
    - Error code interpretation
    - Technical documentation search
    """
    # Get organization from header
    org_id = http_request.headers.get("X-Organization-ID")
    if org_id:
        request.organization_id = org_id
    
    # Get user from token if available
    user_id = http_request.headers.get("X-User-ID")
    if user_id:
        request.user_id = user_id
    
    service = get_ai_service()
    response = await service.process_query(request)
    
    return response


@router.post("/assist/ticket/{ticket_id}")
async def get_ticket_ai_suggestions(
    ticket_id: str,
    http_request: Request
):
    """
    Get AI-powered suggestions for a specific ticket.
    Returns diagnostic steps, probable causes, and estimate suggestions.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    service = get_ai_service()
    suggestions = await service.get_ticket_suggestions(ticket_id, org_id)
    
    return suggestions


class QuickDiagnoseRequest(BaseModel):
    """Quick diagnosis request for category-based queries"""
    category: str = "general"
    symptoms: List[str] = []
    dtc_codes: List[str] = []
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    description: Optional[str] = None


@router.post("/assist/quick-diagnose")
async def quick_diagnose(
    data: QuickDiagnoseRequest,
    http_request: Request
):
    """
    Quick diagnosis endpoint for category-based symptom lookup.
    Returns matching failure cards and diagnostic suggestions.
    """
    org_id = http_request.headers.get("X-Organization-ID", "global")
    
    store = get_knowledge_store()
    
    # Get failure cards matching symptoms
    failure_cards = await store.get_failure_cards_for_symptoms(
        symptoms=data.symptoms,
        organization_id=org_id,
        vehicle_make=data.vehicle_make,
        limit=5
    )
    
    # Get error code info
    error_info = []
    for code in data.dtc_codes[:5]:
        info = await store.get_error_code_info(code, org_id)
        if info:
            error_info.append(info)
    
    return {
        "failure_cards": failure_cards,
        "error_codes": error_info,
        "category": data.category,
        "suggestions_count": len(failure_cards) + len(error_info)
    }


# ==================== FEEDBACK & ESCALATION ====================

@router.post("/assist/feedback")
async def submit_feedback(
    feedback: AIFeedback,
    http_request: Request
):
    """
    Submit feedback on AI response quality.
    Used to improve the knowledge base and AI accuracy.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if org_id:
        feedback.organization_id = org_id
    
    if not feedback.created_at:
        feedback.created_at = datetime.now(timezone.utc).isoformat()
    
    service = get_ai_service()
    await service.record_feedback(feedback)
    
    return {"status": "recorded", "query_id": feedback.query_id}


@router.post("/assist/escalate")
async def escalate_to_expert(
    escalation: EscalationRequest,
    http_request: Request
):
    """
    Escalate a query to human expert review.
    Creates an internal expert queue ticket or Zendesk ticket if configured.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    if org_id:
        escalation.organization_id = org_id
    
    service = get_ai_service()
    result = await service.create_escalation(escalation)
    
    return result


# ==================== KNOWLEDGE MANAGEMENT ====================

class KnowledgeUploadRequest(BaseModel):
    """Request model for uploading new knowledge"""
    knowledge_type: str = "repair_procedure"
    title: str
    content: str
    summary: Optional[str] = None
    symptoms: List[str] = []
    dtc_codes: List[str] = []
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    subsystem: Optional[str] = None
    tags: List[str] = []
    severity: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None


@router.post("/knowledge/upload")
async def upload_knowledge(
    data: KnowledgeUploadRequest,
    http_request: Request
):
    """
    Upload new knowledge article to the tenant knowledge base.
    Article goes to 'draft' status until approved.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    user_id = http_request.headers.get("X-User-ID", "system")
    
    store = get_knowledge_store()
    
    article = await store.create_knowledge_article(
        data=data.model_dump(),
        organization_id=org_id,
        created_by=user_id
    )
    
    return {
        "status": "created",
        "knowledge_id": article["knowledge_id"],
        "approval_status": article["approval_status"]
    }


class FailureCardUploadRequest(BaseModel):
    """Request model for creating a failure card"""
    problem_title: str
    problem_description: str
    symptoms: List[str] = []
    dtc_codes: List[str] = []
    error_messages: List[str] = []
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    subsystem: Optional[str] = None
    component: Optional[str] = None
    preliminary_checks: List[str] = []
    diagnostic_steps: List[Dict[str, Any]] = []
    probable_causes: List[Dict[str, Any]] = []
    fix_procedures: List[Dict[str, Any]] = []
    parts_required: List[Dict[str, Any]] = []
    tools_required: List[str] = []
    safety_warnings: List[str] = []
    high_voltage_involved: bool = False


@router.post("/knowledge/failure-card")
async def create_failure_card(
    data: FailureCardUploadRequest,
    http_request: Request
):
    """
    Create a new failure card in the knowledge base.
    Failure cards provide structured diagnostic and repair procedures.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    user_id = http_request.headers.get("X-User-ID", "system")
    
    store = get_knowledge_store()
    
    card = await store.create_failure_card(
        data=data.model_dump(),
        organization_id=org_id,
        created_by=user_id
    )
    
    return {
        "status": "created",
        "failure_card_id": card["failure_card_id"],
        "knowledge_id": card["knowledge_id"],
        "approval_status": card["approval_status"]
    }


@router.post("/knowledge/from-ticket/{ticket_id}")
async def create_knowledge_from_ticket(
    ticket_id: str,
    resolution_notes: str = Body(..., embed=True),
    http_request: Request = None
):
    """
    Create a failure card draft from a resolved ticket.
    Converts successful resolutions into reusable knowledge.
    """
    org_id = http_request.headers.get("X-Organization-ID") if http_request else None
    user_id = http_request.headers.get("X-User-ID", "system") if http_request else "system"
    
    db = get_db()
    
    # Get ticket
    ticket = await db.tickets.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    store = get_knowledge_store()
    
    card = await store.create_failure_card_from_ticket(
        ticket=ticket,
        resolution_notes=resolution_notes,
        organization_id=org_id or ticket.get("organization_id"),
        created_by=user_id
    )
    
    return {
        "status": "created",
        "failure_card_id": card["failure_card_id"],
        "knowledge_id": card["knowledge_id"],
        "message": "Failure card draft created. Awaiting supervisor approval."
    }


class ApprovalRequest(BaseModel):
    """Request model for knowledge approval"""
    action: str  # "approve" or "reject"
    reason: Optional[str] = None


@router.post("/knowledge/approve/{knowledge_id}")
async def approve_knowledge(
    knowledge_id: str,
    data: ApprovalRequest,
    http_request: Request
):
    """
    Approve or reject a knowledge article.
    Requires supervisor/admin role.
    """
    org_id = http_request.headers.get("X-Organization-ID")
    user_id = http_request.headers.get("X-User-ID", "system")
    
    store = get_knowledge_store()
    
    if data.action == "approve":
        success = await store.approve_knowledge(knowledge_id, user_id, org_id)
        status = "approved" if success else "failed"
    elif data.action == "reject":
        if not data.reason:
            raise HTTPException(status_code=400, detail="Rejection reason required")
        success = await store.reject_knowledge(knowledge_id, user_id, data.reason, org_id)
        status = "rejected" if success else "failed"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return {"knowledge_id": knowledge_id, "status": status}


@router.get("/assist/sources/{source_id}")
async def get_source_details(
    source_id: str,
    http_request: Request
):
    """
    Get full details of a knowledge source.
    Used when user clicks on a citation link.
    """
    org_id = http_request.headers.get("X-Organization-ID", "global")
    db = get_db()
    
    # Try knowledge articles
    article = await db.knowledge_articles.find_one(
        {"knowledge_id": source_id},
        {"_id": 0}
    )
    if article:
        return {"source_type": "knowledge_article", "data": article}
    
    # Try failure cards
    card = await db.failure_cards.find_one(
        {"failure_card_id": source_id},
        {"_id": 0}
    )
    if card:
        return {"source_type": "failure_card", "data": card}
    
    # Try error codes
    code = await db.error_codes.find_one(
        {"code_id": source_id},
        {"_id": 0}
    )
    if code:
        return {"source_type": "error_code", "data": code}
    
    raise HTTPException(status_code=404, detail="Source not found")


# ==================== KNOWLEDGE BROWSING ====================

@router.get("/knowledge/list")
async def list_knowledge(http_request: Request, knowledge_type: Optional[str] = None, subsystem: Optional[str] = None, vehicle_make: Optional[str] = None, status: Optional[str] = None, limit: int = Query(20, le=100),
    offset: int = 0
):
    """
    List knowledge articles with filters.
    """
    org_id = http_request.headers.get("X-Organization-ID", "global")
    db = get_db()
    
    query = {
        "$or": [
            {"scope": "global"},
            {"organization_id": org_id}
        ]
    }
    
    if knowledge_type:
        query["knowledge_type"] = knowledge_type
    if subsystem:
        query["subsystem"] = subsystem
    if vehicle_make:
        query["vehicle_make"] = {"$regex": vehicle_make, "$options": "i"}
    if status:
        query["approval_status"] = status
    
    articles = await db.knowledge_articles.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    total = await db.knowledge_articles.count_documents(query)
    
    return {
        "articles": articles,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/knowledge/failure-cards")
async def list_failure_cards(http_request: Request, subsystem: Optional[str] = None, vehicle_make: Optional[str] = None, status: Optional[str] = "approved", limit: int = Query(20, le=100),
    offset: int = 0
):
    """
    List failure cards with filters.
    """
    org_id = http_request.headers.get("X-Organization-ID", "global")
    db = get_db()
    
    query = {
        "$or": [
            {"scope": "global"},
            {"organization_id": org_id}
        ]
    }
    
    if subsystem:
        query["subsystem"] = subsystem
    if vehicle_make:
        query["vehicle_make"] = {"$regex": vehicle_make, "$options": "i"}
    if status:
        query["approval_status"] = status
    
    cards = await db.failure_cards.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    total = await db.failure_cards.count_documents(query)
    
    return {
        "failure_cards": cards,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ==================== STATS & HEALTH ====================

@router.get("/health")
async def ai_health():
    """Check AI service health and configuration"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    db = get_db()
    store = get_knowledge_store()
    stats = await store.get_knowledge_stats()
    
    return {
        "status": "available" if api_key else "unavailable",
        "model": "gemini-3-flash-preview",
        "knowledge_base": stats,
        "features": {
            "rag_enabled": True,
            "citations_enabled": True,
            "escalation_enabled": True,
            "feedback_enabled": True
        }
    }


@router.get("/stats")
async def get_ai_stats(http_request: Request):
    """Get AI usage statistics for the organization"""
    org_id = http_request.headers.get("X-Organization-ID", "global")
    db = get_db()
    
    # Query stats
    total_queries = await db.ai_queries.count_documents({"organization_id": org_id})
    escalations = await db.ai_escalations.count_documents({"organization_id": org_id})
    
    # Feedback stats
    helpful = await db.ai_feedback.count_documents({
        "organization_id": org_id,
        "feedback_type": "helpful"
    })
    not_helpful = await db.ai_feedback.count_documents({
        "organization_id": org_id,
        "feedback_type": "not_helpful"
    })
    
    # Knowledge stats
    store = get_knowledge_store()
    kb_stats = await store.get_knowledge_stats(org_id)
    
    return {
        "queries": {
            "total": total_queries,
            "escalations": escalations,
            "escalation_rate": (escalations / total_queries * 100) if total_queries > 0 else 0
        },
        "feedback": {
            "helpful": helpful,
            "not_helpful": not_helpful,
            "satisfaction_rate": (helpful / (helpful + not_helpful) * 100) if (helpful + not_helpful) > 0 else 0
        },
        "knowledge_base": kb_stats
    }
