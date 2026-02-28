"""
Battwheels OS - Failure Intelligence Routes (Refactored)
Thin controller layer - all business logic delegated to EFIService

Routes are thin:
- Parse request
- Call service
- Return response

All events are emitted from the service layer, not routes.
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query, Depends
from typing import Optional, List
from datetime import datetime, timezone
import logging

from models.failure_intelligence import (
    FailureCardCreate, FailureCardUpdate,
    TechnicianActionCreate,
    FailureMatchRequest,
    SymptomCreate,
    PartUsageCreate,
    Symptom, KnowledgeRelation
)
from services.failure_intelligence_service import (
    EFIService,
    get_efi_service,
    init_efi_service
)
from core.subscriptions.entitlement import require_feature
from utils.database import extract_org_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/efi",
    tags=["Failure Intelligence"],
    dependencies=[Depends(require_feature("efi_failure_intelligence"))]
)

# Service reference
_service: Optional[EFIService] = None
_event_processor = None


def init_router(database, processor=None):
    """Initialize router with database and event processor"""
    global _service, _event_processor
    _event_processor = processor
    _service = init_efi_service(database, processor)
    logger.info("EFI router initialized with service")
    return router


def get_service() -> EFIService:
    """Get the EFI service instance"""
    if _service is None:
        raise HTTPException(status_code=500, detail="EFI service not initialized")
    return _service


# ==================== HELPER FUNCTIONS ====================

async def get_current_user(request: Request, db) -> dict:
    """Get current authenticated user"""
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user
    
    # Try JWT token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        from utils.auth import decode_token_safe
        payload = decode_token_safe(token)
        if payload and payload.get("user_id"):
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
    
    raise HTTPException(status_code=401, detail="Not authenticated")


# ==================== FAILURE CARD ROUTES ====================

@router.post("/failure-cards")
async def create_failure_card(request: Request, data: FailureCardCreate):
    """Create a new failure intelligence card"""
    service = get_service()
    org_id = extract_org_id(request)
    user = await get_current_user(request, service.db)
    
    result = await service.create_failure_card(
        data=data,
        user_id=user.get("user_id")
    )
    return result


@router.get("/failure-cards")
async def list_failure_cards(request: Request, status: Optional[str] = None, subsystem: Optional[str] = None, search: Optional[str] = None, min_confidence: Optional[float] = None, min_effectiveness: Optional[float] = None, source_type: Optional[str] = None, limit: int = Query(50, le=500),
    skip: int = Query(0, ge=0)
):
    """List failure cards with filtering"""
    service = get_service()
    org_id = extract_org_id(request)
    
    return await service.list_failure_cards(
        status=status,
        subsystem=subsystem,
        search=search,
        min_confidence=min_confidence,
        min_effectiveness=min_effectiveness,
        source_type=source_type,
        limit=limit,
        skip=skip,
        organization_id=org_id
    )


@router.get("/failure-cards/{failure_id}")
async def get_failure_card(request: Request, failure_id: str):
    """Get a single failure card by ID"""
    service = get_service()
    org_id = extract_org_id(request)
    
    card = await service.get_failure_card(failure_id)
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    return card


@router.get("/failure-cards/{failure_id}/confidence-history")
async def get_confidence_history(request: Request, failure_id: str):
    """Get confidence score history for a failure card"""
    service = get_service()
    org_id = extract_org_id(request)
    
    try:
        return await service.get_confidence_history(failure_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/failure-cards/{failure_id}")
async def update_failure_card(request: Request, failure_id: str, data: FailureCardUpdate):
    """Update a failure card"""
    service = get_service()
    org_id = extract_org_id(request)
    user = await get_current_user(request, service.db)
    
    try:
        return await service.update_failure_card(
            failure_id=failure_id,
            data=data,
            user_id=user.get("user_id")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/failure-cards/{failure_id}/approve")
async def approve_failure_card(request: Request, failure_id: str, approved_by: Optional[str] = None):
    """Approve a failure card for network distribution"""
    service = get_service()
    org_id = extract_org_id(request)
    user = await get_current_user(request, service.db)
    
    try:
        return await service.approve_failure_card(
            failure_id=failure_id,
            approved_by=approved_by or user.get("name", "System"),
            user_id=user.get("user_id")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/failure-cards/{failure_id}/deprecate")
async def deprecate_failure_card(request: Request, failure_id: str, reason: str):
    """Deprecate a failure card"""
    service = get_service()
    org_id = extract_org_id(request)
    user = await get_current_user(request, service.db)
    
    try:
        return await service.deprecate_failure_card(
            failure_id=failure_id,
            reason=reason,
            user_id=user.get("user_id")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== AI MATCHING ROUTES ====================

@router.post("/match")
async def match_failure(request: Request, data: FailureMatchRequest):
    """AI-powered failure matching - 4-stage pipeline"""
    service = get_service()
    org_id = extract_org_id(request)
    
    response = await service.match_failure(data)
    return response


@router.post("/match-ticket/{ticket_id}")
async def match_ticket_to_failures(request: Request, ticket_id: str):
    """Match an existing ticket to failure cards"""
    service = get_service()
    org_id = extract_org_id(request)
    
    try:
        return await service.match_ticket_to_failures(ticket_id, org_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== TECHNICIAN ACTION ROUTES ====================

@router.post("/technician-actions")
async def record_technician_action(request: Request, data: TechnicianActionCreate):
    """Record technician diagnostic and repair actions"""
    service = get_service()
    org_id = extract_org_id(request)
    user = await get_current_user(request, service.db)
    
    try:
        return await service.record_technician_action(
            data=data,
            technician_id=user.get("user_id"),
            technician_name=user.get("name")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/technician-actions")
async def list_technician_actions(request: Request, ticket_id: Optional[str] = None, technician_id: Optional[str] = None, include_hypotheses: bool = False, limit: int = 50):
    """List technician actions"""
    service = get_service()
    org_id = extract_org_id(request)
    
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    if technician_id:
        query["technician_id"] = technician_id
    
    projection = {"_id": 0}
    if not include_hypotheses:
        projection["rejected_hypotheses"] = 0
        projection["attempted_diagnostics"] = 0
    
    actions = await service.db.technician_actions.find(
        query, projection
    ).sort("completed_at", -1).limit(limit).to_list(limit)
    
    return actions


# ==================== PART USAGE ROUTES ====================

@router.post("/part-usage")
async def record_part_usage(request: Request, data: PartUsageCreate):
    """Record part usage with failure card linkage"""
    service = get_service()
    org_id = extract_org_id(request)
    await get_current_user(request, service.db)  # Auth check
    
    try:
        return await service.record_part_usage(data, org_id=org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/part-usage")
async def list_part_usage(request: Request, ticket_id: Optional[str] = None, failure_card_id: Optional[str] = None, unexpected_only: bool = False, limit: int = 100):
    """List part usage records"""
    service = get_service()
    org_id = extract_org_id(request)
    
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    if failure_card_id:
        query["failure_card_id"] = failure_card_id
    if unexpected_only:
        query["expected_vs_actual"] = False
    
    usage = await service.db.part_usage.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return usage


# ==================== PATTERN DETECTION ROUTES ====================

@router.get("/patterns")
async def list_emerging_patterns(request: Request, status: Optional[str] = None, pattern_type: Optional[str] = None, limit: int = 50):
    """List detected emerging patterns"""
    service = get_service()
    org_id = extract_org_id(request)
    
    query = {}
    if status:
        query["status"] = status
    if pattern_type:
        query["pattern_type"] = pattern_type
    
    patterns = await service.db.emerging_patterns.find(
        query, {"_id": 0}
    ).sort("occurrence_count", -1).limit(limit).to_list(limit)
    
    return patterns


@router.post("/patterns/{pattern_id}/review")
async def review_pattern(request: Request, pattern_id: str, action: str, notes: Optional[str] = None):
    """Review and action an emerging pattern"""
    service = get_service()
    org_id = extract_org_id(request)
    
    pattern = await service.db.emerging_patterns.find_one({"pattern_id": pattern_id}, {"_id": 0})
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    update = {
        "status": "reviewed" if action == "confirm" else ("dismissed" if action == "dismiss" else "actioned"),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "review_notes": notes,
        "action_taken": action
    }
    
    await service.db.emerging_patterns.update_one(
        {"pattern_id": pattern_id},
        {"$set": update}
    )
    
    return {"message": f"Pattern {action}ed", "pattern_id": pattern_id}


@router.post("/patterns/detect")
async def trigger_pattern_detection(request: Request, background_tasks: BackgroundTasks):
    """Manually trigger pattern detection job"""
    if _event_processor:
        background_tasks.add_task(
            _event_processor.detect_emerging_patterns,
            min_occurrences=3,
            lookback_days=30
        )
        return {"message": "Pattern detection triggered", "status": "queued"}
    else:
        return {"message": "Event processor not configured", "status": "skipped"}


# ==================== SYMPTOM LIBRARY ROUTES ====================

@router.post("/symptoms")
async def create_symptom(request: Request, data: SymptomCreate):
    """Create a new symptom in the library"""
    service = get_service()
    
    symptom = Symptom(
        code=data.code,
        category=data.category,
        description=data.description,
        severity=data.severity,
        keywords=data.keywords
    )
    
    doc = symptom.model_dump()
    await service.db.symptoms.insert_one(doc)
    
    return symptom.model_dump()


@router.get("/symptoms")
async def list_symptoms(request: Request, category: Optional[str] = None, search: Optional[str] = None):
    """List symptoms from library"""
    service = get_service()
    
    query = {}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"keywords": {"$in": [search.lower()]}}
        ]
    
    symptoms = await service.db.symptoms.find(query, {"_id": 0}).to_list(100)
    return symptoms


# ==================== KNOWLEDGE GRAPH ROUTES ====================

@router.post("/relations")
async def create_knowledge_relation(request: Request, data: dict):
    """Create a relationship in the knowledge graph"""
    service = get_service()
    
    relation = KnowledgeRelation(
        source_type=data["source_type"],
        source_id=data["source_id"],
        source_label=data.get("source_label"),
        relation_type=data["relation_type"],
        target_type=data["target_type"],
        target_id=data["target_id"],
        target_label=data.get("target_label"),
        weight=data.get("weight", 1.0),
        confidence=data.get("confidence", 0.5),
        bidirectional=data.get("bidirectional", False),
        metadata=data.get("metadata", {})
    )
    
    doc = relation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await service.db.knowledge_relations.insert_one(doc)
    
    return relation.model_dump()


@router.get("/relations")
async def get_knowledge_relations(request: Request, source_id: Optional[str] = None, target_id: Optional[str] = None, relation_type: Optional[str] = None):
    """Get relationships from knowledge graph"""
    service = get_service()
    
    query = {}
    if source_id:
        query["source_id"] = source_id
    if target_id:
        query["target_id"] = target_id
    if relation_type:
        query["relation_type"] = relation_type
    
    relations = await service.db.knowledge_relations.find(query, {"_id": 0}).to_list(100)
    return relations


@router.get("/graph/{entity_type}/{entity_id}")
async def get_entity_graph(request: Request, entity_type: str, entity_id: str, depth: int = 2):
    """Get knowledge graph around an entity"""
    service = get_service()
    
    relations = await service.db.knowledge_relations.find({
        "$or": [
            {"source_type": entity_type, "source_id": entity_id},
            {"target_type": entity_type, "target_id": entity_id}
        ]
    }, {"_id": 0}).to_list(100)
    
    nodes = [{"id": entity_id, "type": entity_type, "label": entity_id}]
    edges = []
    seen = {entity_id}
    
    for rel in relations:
        if rel["source_id"] != entity_id and rel["source_id"] not in seen:
            nodes.append({
                "id": rel["source_id"],
                "type": rel["source_type"],
                "label": rel.get("source_label", rel["source_id"])
            })
            seen.add(rel["source_id"])
        
        if rel["target_id"] != entity_id and rel["target_id"] not in seen:
            nodes.append({
                "id": rel["target_id"],
                "type": rel["target_type"],
                "label": rel.get("target_label", rel["target_id"])
            })
            seen.add(rel["target_id"])
        
        edges.append({
            "source": rel["source_id"],
            "target": rel["target_id"],
            "type": rel["relation_type"],
            "weight": rel["weight"]
        })
    
    return {"nodes": nodes, "edges": edges, "center": entity_id}


# ==================== ANALYTICS ROUTES ====================

@router.get("/analytics/overview")
async def get_efi_analytics(request: Request):
    """Get EFI system analytics"""
    service = get_service()
    return await service.get_analytics_overview()


@router.get("/analytics/effectiveness")
async def get_effectiveness_report(request: Request):
    """Get effectiveness report for failure cards"""
    service = get_service()
    
    pipeline = [
        {"$match": {"status": "approved", "usage_count": {"$gt": 0}}},
        {"$project": {
            "_id": 0,
            "failure_id": 1,
            "title": 1,
            "subsystem_category": 1,
            "source_type": 1,
            "usage_count": 1,
            "success_count": 1,
            "failure_count": 1,
            "effectiveness_score": 1,
            "confidence_score": 1,
            "first_detected_at": 1,
            "last_used_at": 1,
            "success_rate": {
                "$cond": [
                    {"$gt": ["$usage_count", 0]},
                    {"$divide": ["$success_count", "$usage_count"]},
                    0
                ]
            }
        }},
        {"$sort": {"effectiveness_score": -1}}
    ]
    
    report = await service.db.failure_cards.aggregate(pipeline).to_list(50)
    
    return {
        "report": report,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/analytics/part-anomalies")
async def get_part_anomaly_report(request: Request):
    """Get report of unexpected part usage"""
    service = get_service()
    
    pipeline = [
        {"$match": {"expected_vs_actual": False}},
        {"$group": {
            "_id": "$part_id",
            "part_name": {"$first": "$part_name"},
            "occurrence_count": {"$sum": 1},
            "failure_cards": {"$addToSet": "$failure_card_id"},
            "notes": {"$push": "$expectation_notes"}
        }},
        {"$sort": {"occurrence_count": -1}},
        {"$limit": 20}
    ]
    
    anomalies = await service.db.part_usage.aggregate(pipeline).to_list(20)
    
    return {
        "anomalies": anomalies,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# ==================== EVENT PROCESSING ====================

@router.get("/events")
async def list_events(request: Request, event_type: Optional[str] = None, processed: Optional[bool] = None, limit: int = 50):
    """List EFI system events"""
    service = get_service()
    
    query = {}
    if event_type:
        query["event_type"] = event_type
    if processed is not None:
        query["processed"] = processed
    
    events = await service.db.efi_events.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return events


@router.post("/events/process")
async def process_pending_events(request: Request, background_tasks: BackgroundTasks):
    """Process pending EFI events"""
    service = get_service()
    
    pending = await service.db.efi_events.count_documents({"processed": False})
    
    if _event_processor:
        background_tasks.add_task(_event_processor.process_pending_events, limit=100)
        return {"message": f"Processing {pending} pending events", "queued": True}
    else:
        # Fallback simple processing
        async def simple_process():
            events = await service.db.efi_events.find({"processed": False}).limit(100).to_list(100)
            for event in events:
                await service.db.efi_events.update_one(
                    {"event_id": event["event_id"]},
                    {"$set": {"processed": True, "processed_at": datetime.now(timezone.utc).isoformat()}}
                )
        
        background_tasks.add_task(simple_process)
        return {"message": f"Processing {pending} pending events (simple mode)", "queued": True}



# ==================== EMBEDDING MANAGEMENT ====================

@router.post("/embeddings/generate")
async def generate_embeddings(request: Request, background_tasks: BackgroundTasks):
    """
    Generate vector embeddings for all failure cards.
    This enables semantic search in the AI matching pipeline.
    
    Note: Requires OPENAI_API_KEY in environment. Emergent LLM key does not support embeddings.
    """
    try:
        from services.embedding_service import get_card_embedder, get_embedding_service
        
        embedding_service = get_embedding_service()
        
        # Check if embeddings are available
        if embedding_service.client is None:
            return {
                "message": "Embedding service not available",
                "reason": "OPENAI_API_KEY not configured. Emergent LLM key does not support embeddings.",
                "alternative": "The system will use keyword-based matching (BM25) which is still effective.",
                "status": "disabled"
            }
        
        embedder = get_card_embedder()
        
        # Run in background to not block
        async def run_embedding():
            return await embedder.embed_all_cards(batch_size=25)
        
        background_tasks.add_task(run_embedding)
        
        # Get count of cards without embeddings
        service = get_service()
        total_cards = await service.db.failure_cards.count_documents({})
        cards_without_embeddings = await service.db.failure_cards.count_documents({
            "$or": [
                {"embedding_vector": {"$exists": False}},
                {"embedding_vector": None}
            ]
        })
        
        return {
            "message": "Embedding generation started in background",
            "total_cards": total_cards,
            "cards_needing_embeddings": cards_without_embeddings,
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Failed to start embedding generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embeddings/status")
async def get_embedding_status(request: Request):
    """Check embedding generation status for failure cards."""
    service = get_service()
    
    # Check if embedding service is available
    try:
        from services.embedding_service import get_embedding_service
        embedding_service = get_embedding_service()
        embeddings_enabled = embedding_service.client is not None
    except:
        embeddings_enabled = False
    
    total_cards = await service.db.failure_cards.count_documents({})
    cards_with_embeddings = await service.db.failure_cards.count_documents({
        "embedding_vector": {"$exists": True, "$ne": None}
    })
    cards_without_embeddings = total_cards - cards_with_embeddings
    
    # Check cache stats
    cache_count = await service.db.embedding_cache.count_documents({})
    
    return {
        "embeddings_enabled": embeddings_enabled,
        "note": "Requires OPENAI_API_KEY (Emergent LLM key does not support embeddings)" if not embeddings_enabled else None,
        "total_cards": total_cards,
        "cards_with_embeddings": cards_with_embeddings,
        "cards_without_embeddings": cards_without_embeddings,
        "embedding_coverage_percent": round((cards_with_embeddings / total_cards * 100), 2) if total_cards > 0 else 0,
        "cache_entries": cache_count,
        "embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 1536
    }
