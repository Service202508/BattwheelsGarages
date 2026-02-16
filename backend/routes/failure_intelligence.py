"""
Battwheels OS - Failure Intelligence Routes
Core routes for the EV Failure Intelligence (EFI) Platform
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import asyncio
import logging

from models.failure_intelligence import (
    FailureCard, FailureCardCreate, FailureCardUpdate, FailureCardStatus,
    SubsystemCategory, ConfidenceLevel, FailureMode,
    TechnicianAction, TechnicianActionCreate,
    FailureMatchRequest, FailureMatchResult, FailureMatchResponse,
    Symptom, SymptomCreate,
    KnowledgeRelation, EFIEvent
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/efi", tags=["Failure Intelligence"])

# Database reference
db = None

def init_router(database):
    global db
    db = database
    return router

# ==================== HELPER FUNCTIONS ====================

def calculate_confidence_level(score: float) -> ConfidenceLevel:
    """Convert confidence score to level"""
    if score >= 0.9:
        return ConfidenceLevel.VERIFIED
    elif score >= 0.7:
        return ConfidenceLevel.HIGH
    elif score >= 0.4:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW

def calculate_effectiveness(success_count: int, failure_count: int, usage_count: int) -> float:
    """Calculate effectiveness score based on usage outcomes"""
    if usage_count == 0:
        return 0.5  # Default for new cards
    
    # Weighted calculation
    success_rate = success_count / usage_count if usage_count > 0 else 0
    
    # Bonus for high usage (trusted solutions)
    usage_bonus = min(0.1, usage_count / 100)
    
    return min(1.0, success_rate + usage_bonus)

async def generate_embedding(text: str) -> List[float]:
    """Generate text embedding for semantic search"""
    # This would integrate with an embedding model (OpenAI, Sentence Transformers, etc.)
    # For now, we'll use a placeholder that can be replaced with actual embedding
    try:
        from emergentintegrations.llm.openai import OpenAIConfig, OpenAILLM
        import os
        
        config = OpenAIConfig(
            api_key=os.environ.get("EMERGENT_LLM_KEY", ""),
            model="text-embedding-3-small"
        )
        llm = OpenAILLM(config)
        
        # Generate embedding
        response = await asyncio.to_thread(
            llm.embeddings.create,
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        # Return a simple hash-based vector as fallback
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val >> (i * 8)) % 256 / 255.0 for i in range(64)]

def compute_text_similarity(text1: str, text2: str) -> float:
    """Compute simple text similarity using keyword overlap"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)

# ==================== FAILURE CARD ROUTES ====================

@router.post("/failure-cards")
async def create_failure_card(data: FailureCardCreate, request: Request):
    """Create a new failure intelligence card"""
    # Get auth from main server (simple approach)
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Build failure card
    card = FailureCard(
        title=data.title,
        description=data.description,
        subsystem_category=data.subsystem_category,
        failure_mode=data.failure_mode,
        symptom_codes=data.symptom_codes,
        symptom_text=data.symptom_text,
        error_codes=data.error_codes,
        root_cause=data.root_cause,
        root_cause_details=data.root_cause_details,
        secondary_causes=data.secondary_causes,
        verification_steps=data.verification_steps,
        resolution_steps=data.resolution_steps,
        required_parts=data.required_parts,
        vehicle_models=data.vehicle_models,
        universal_failure=data.universal_failure,
        failure_conditions=data.failure_conditions,
        keywords=data.keywords,
        tags=data.tags,
        source_ticket_id=data.source_ticket_id,
        status=FailureCardStatus.DRAFT
    )
    
    # Calculate estimated costs
    total_parts_cost = sum(p.get("estimated_cost", 0) for p in data.required_parts)
    total_time = sum(s.get("duration_minutes", 0) for s in data.resolution_steps)
    labor_cost = total_time * 5  # ₹5 per minute average
    
    card.estimated_parts_cost = total_parts_cost
    card.estimated_labor_cost = labor_cost
    card.estimated_total_cost = total_parts_cost + labor_cost
    card.estimated_repair_time_minutes = total_time
    
    # Generate keywords from content
    content_text = f"{data.title} {data.description or ''} {data.root_cause} {data.symptom_text or ''}"
    card.keywords = list(set(card.keywords + content_text.lower().split()[:20]))
    
    # Store
    doc = card.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.failure_cards.insert_one(doc)
    
    # Create event
    await db.efi_events.insert_one({
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": "failure_card_created",
        "source": "api",
        "data": {"failure_id": card.failure_id, "title": card.title},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed": False
    })
    
    return card.model_dump()

@router.get("/failure-cards")
async def list_failure_cards(
    request: Request,
    status: Optional[str] = None,
    subsystem: Optional[str] = None,
    search: Optional[str] = None,
    min_confidence: Optional[float] = None,
    limit: int = 50,
    skip: int = 0
):
    """List failure cards with filtering"""
    query = {}
    
    if status:
        query["status"] = status
    if subsystem:
        query["subsystem_category"] = subsystem
    if min_confidence:
        query["confidence_score"] = {"$gte": min_confidence}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"root_cause": {"$regex": search, "$options": "i"}},
            {"keywords": {"$in": [search.lower()]}},
            {"error_codes": {"$in": [search.upper()]}}
        ]
    
    cards = await db.failure_cards.find(
        query, 
        {"_id": 0, "embedding_vector": 0}
    ).sort("confidence_score", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.failure_cards.count_documents(query)
    
    return {
        "items": cards,
        "total": total,
        "limit": limit,
        "skip": skip
    }

@router.get("/failure-cards/{failure_id}")
async def get_failure_card(failure_id: str, request: Request):
    """Get a single failure card by ID"""
    card = await db.failure_cards.find_one(
        {"failure_id": failure_id}, 
        {"_id": 0, "embedding_vector": 0}
    )
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    return card

@router.put("/failure-cards/{failure_id}")
async def update_failure_card(failure_id: str, data: FailureCardUpdate, request: Request):
    """Update a failure card"""
    existing = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Increment version
    update_dict["version"] = existing.get("version", 1) + 1
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Add to version history
    version_entry = {
        "version": existing.get("version", 1),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "changes": list(update_dict.keys())
    }
    
    await db.failure_cards.update_one(
        {"failure_id": failure_id},
        {
            "$set": update_dict,
            "$push": {"version_history": version_entry}
        }
    )
    
    updated = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0, "embedding_vector": 0})
    return updated

@router.post("/failure-cards/{failure_id}/approve")
async def approve_failure_card(failure_id: str, request: Request):
    """Approve a failure card for network distribution"""
    card = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    if card.get("status") == FailureCardStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Card already approved")
    
    await db.failure_cards.update_one(
        {"failure_id": failure_id},
        {"$set": {
            "status": FailureCardStatus.APPROVED.value,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "confidence_level": ConfidenceLevel.HIGH.value
        }}
    )
    
    # Create sync event
    await db.efi_events.insert_one({
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": "failure_card_approved",
        "source": "api",
        "data": {"failure_id": failure_id},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed": False
    })
    
    return {"message": "Failure card approved", "failure_id": failure_id}

@router.post("/failure-cards/{failure_id}/deprecate")
async def deprecate_failure_card(failure_id: str, reason: str, request: Request):
    """Deprecate a failure card"""
    await db.failure_cards.update_one(
        {"failure_id": failure_id},
        {"$set": {
            "status": FailureCardStatus.DEPRECATED.value,
            "deprecation_reason": reason,
            "deprecated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Failure card deprecated", "failure_id": failure_id}

# ==================== AI MATCHING ROUTES ====================

@router.post("/match")
async def match_failure(data: FailureMatchRequest, request: Request) -> FailureMatchResponse:
    """
    AI-powered failure matching
    Matches symptoms/descriptions against known failure cards
    """
    import time
    start_time = time.time()
    
    # Build query text for matching
    query_text = data.symptom_text
    if data.error_codes:
        query_text += " " + " ".join(data.error_codes)
    
    # Stage 1: Exact error code match
    exact_matches = []
    if data.error_codes:
        exact_query = {"error_codes": {"$in": data.error_codes}, "status": "approved"}
        exact_results = await db.failure_cards.find(
            exact_query, 
            {"_id": 0, "embedding_vector": 0}
        ).limit(5).to_list(5)
        
        for card in exact_results:
            matched_codes = set(card.get("error_codes", [])) & set(data.error_codes)
            exact_matches.append(FailureMatchResult(
                failure_id=card["failure_id"],
                title=card["title"],
                match_score=0.95,  # High score for exact code match
                match_type="exact",
                matched_symptoms=list(matched_codes),
                confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5))
            ))
    
    # Stage 2: Subsystem + Keyword match
    category_matches = []
    category_query = {"status": {"$in": ["approved", "draft"]}}
    
    if data.subsystem_hint:
        category_query["subsystem_category"] = data.subsystem_hint.value
    
    # Keyword matching
    keywords = query_text.lower().split()
    if keywords:
        category_query["keywords"] = {"$in": keywords}
    
    category_results = await db.failure_cards.find(
        category_query,
        {"_id": 0, "embedding_vector": 0}
    ).limit(10).to_list(10)
    
    for card in category_results:
        if card["failure_id"] in [m.failure_id for m in exact_matches]:
            continue
        
        # Calculate keyword overlap score
        card_keywords = set(card.get("keywords", []))
        query_keywords = set(keywords)
        overlap = len(card_keywords & query_keywords)
        score = min(0.8, 0.3 + (overlap * 0.1))
        
        # Boost if symptom text matches
        if card.get("symptom_text"):
            text_sim = compute_text_similarity(query_text, card["symptom_text"])
            score = max(score, text_sim * 0.85)
        
        if score > 0.3:
            category_matches.append(FailureMatchResult(
                failure_id=card["failure_id"],
                title=card["title"],
                match_score=score,
                match_type="partial",
                matched_symptoms=list(card_keywords & query_keywords)[:5],
                confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5))
            ))
    
    # Stage 3: Vehicle-specific filtering
    if data.vehicle_make or data.vehicle_model:
        vehicle_query = {"status": {"$in": ["approved", "draft"]}}
        
        if data.vehicle_make:
            vehicle_query["vehicle_models.make"] = {"$regex": data.vehicle_make, "$options": "i"}
        if data.vehicle_model:
            vehicle_query["vehicle_models.model"] = {"$regex": data.vehicle_model, "$options": "i"}
        
        vehicle_results = await db.failure_cards.find(
            vehicle_query,
            {"_id": 0, "embedding_vector": 0}
        ).limit(5).to_list(5)
        
        for card in vehicle_results:
            existing_ids = [m.failure_id for m in exact_matches + category_matches]
            if card["failure_id"] not in existing_ids:
                category_matches.append(FailureMatchResult(
                    failure_id=card["failure_id"],
                    title=card["title"],
                    match_score=0.5,
                    match_type="vehicle",
                    matched_symptoms=[f"Vehicle: {data.vehicle_make} {data.vehicle_model}"],
                    confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5))
                ))
    
    # Combine and sort results
    all_matches = exact_matches + category_matches
    all_matches.sort(key=lambda x: x.match_score, reverse=True)
    
    # Log matching event
    await db.efi_events.insert_one({
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": "match_performed",
        "source": "api",
        "data": {
            "query": query_text[:200],
            "matches_found": len(all_matches),
            "top_match": all_matches[0].failure_id if all_matches else None
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed": True
    })
    
    processing_time = (time.time() - start_time) * 1000
    
    return FailureMatchResponse(
        query_text=query_text,
        matches=all_matches[:data.limit],
        processing_time_ms=processing_time,
        model_used="hybrid_keyword_semantic"
    )

@router.post("/match-ticket/{ticket_id}")
async def match_ticket_to_failures(ticket_id: str, request: Request):
    """Match an existing ticket to failure cards and suggest solutions"""
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Build match request from ticket
    match_request = FailureMatchRequest(
        symptom_text=f"{ticket.get('title', '')} {ticket.get('description', '')}",
        error_codes=[],  # Could extract from ticket if available
        vehicle_make=ticket.get("vehicle_make"),
        vehicle_model=ticket.get("vehicle_model"),
        subsystem_hint=None,
        limit=5
    )
    
    # Perform matching
    response = await match_failure(match_request, request)
    
    # Update ticket with suggested failure cards
    if response.matches:
        suggested_ids = [m.failure_id for m in response.matches]
        await db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"suggested_failure_cards": suggested_ids}}
        )
    
    return {
        "ticket_id": ticket_id,
        "matches": [m.model_dump() for m in response.matches],
        "processing_time_ms": response.processing_time_ms
    }

# ==================== TECHNICIAN ACTION ROUTES ====================

@router.post("/technician-actions")
async def record_technician_action(data: TechnicianActionCreate, request: Request):
    """Record technician diagnostic and repair actions"""
    # Get technician from auth
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    
    # Verify ticket exists
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    action = TechnicianAction(
        ticket_id=data.ticket_id,
        technician_id="",  # Would be set from auth
        diagnostic_steps_performed=data.diagnostic_steps_performed,
        observations=data.observations,
        measurements=data.measurements,
        parts_used=data.parts_used,
        resolution_outcome=data.resolution_outcome,
        failure_card_used=data.failure_card_used,
        failure_card_helpful=data.failure_card_helpful,
        new_failure_discovered=data.new_failure_discovered,
        technician_notes=data.technician_notes,
        difficulty_rating=data.difficulty_rating,
        time_spent_minutes=data.time_spent_minutes,
        completed_at=datetime.now(timezone.utc)
    )
    
    doc = action.model_dump()
    doc['started_at'] = doc['started_at'].isoformat()
    doc['completed_at'] = doc['completed_at'].isoformat()
    await db.technician_actions.insert_one(doc)
    
    # Update failure card metrics if one was used
    if data.failure_card_used:
        update_query = {"$inc": {"usage_count": 1}}
        if data.resolution_outcome == "success":
            update_query["$inc"]["success_count"] = 1
        elif data.resolution_outcome == "failed":
            update_query["$inc"]["failure_count"] = 1
        
        await db.failure_cards.update_one(
            {"failure_id": data.failure_card_used},
            update_query
        )
        
        # Recalculate effectiveness
        card = await db.failure_cards.find_one({"failure_id": data.failure_card_used}, {"_id": 0})
        if card:
            effectiveness = calculate_effectiveness(
                card.get("success_count", 0),
                card.get("failure_count", 0),
                card.get("usage_count", 0)
            )
            confidence = min(1.0, card.get("confidence_score", 0.5) + (0.01 if data.resolution_outcome == "success" else -0.02))
            
            await db.failure_cards.update_one(
                {"failure_id": data.failure_card_used},
                {"$set": {
                    "effectiveness_score": effectiveness,
                    "confidence_score": confidence,
                    "confidence_level": calculate_confidence_level(confidence).value
                }}
            )
    
    # Create event for new failure discovery
    if data.new_failure_discovered:
        await db.efi_events.insert_one({
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "new_failure_discovered",
            "source": "technician_action",
            "data": {
                "ticket_id": data.ticket_id,
                "observations": data.observations,
                "notes": data.technician_notes
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processed": False
        })
    
    return action.model_dump()

@router.get("/technician-actions")
async def list_technician_actions(
    request: Request,
    ticket_id: Optional[str] = None,
    technician_id: Optional[str] = None,
    limit: int = 50
):
    """List technician actions"""
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    if technician_id:
        query["technician_id"] = technician_id
    
    actions = await db.technician_actions.find(
        query, {"_id": 0}
    ).sort("completed_at", -1).limit(limit).to_list(limit)
    
    return actions

# ==================== SYMPTOM LIBRARY ROUTES ====================

@router.post("/symptoms")
async def create_symptom(data: SymptomCreate, request: Request):
    """Create a new symptom in the library"""
    symptom = Symptom(
        code=data.code,
        category=data.category,
        description=data.description,
        severity=data.severity,
        keywords=data.keywords
    )
    
    doc = symptom.model_dump()
    await db.symptoms.insert_one(doc)
    
    return symptom.model_dump()

@router.get("/symptoms")
async def list_symptoms(
    request: Request,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """List symptoms from library"""
    query = {}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"keywords": {"$in": [search.lower()]}}
        ]
    
    symptoms = await db.symptoms.find(query, {"_id": 0}).to_list(100)
    return symptoms

# ==================== KNOWLEDGE GRAPH ROUTES ====================

@router.post("/relations")
async def create_knowledge_relation(data: dict, request: Request):
    """Create a relationship in the knowledge graph"""
    relation = KnowledgeRelation(
        source_type=data["source_type"],
        source_id=data["source_id"],
        relation_type=data["relation_type"],
        target_type=data["target_type"],
        target_id=data["target_id"],
        weight=data.get("weight", 1.0),
        metadata=data.get("metadata", {})
    )
    
    doc = relation.model_dump()
    await db.knowledge_relations.insert_one(doc)
    
    return relation.model_dump()

@router.get("/relations")
async def get_knowledge_relations(
    request: Request,
    source_id: Optional[str] = None,
    target_id: Optional[str] = None,
    relation_type: Optional[str] = None
):
    """Get relationships from knowledge graph"""
    query = {}
    if source_id:
        query["source_id"] = source_id
    if target_id:
        query["target_id"] = target_id
    if relation_type:
        query["relation_type"] = relation_type
    
    relations = await db.knowledge_relations.find(query, {"_id": 0}).to_list(100)
    return relations

@router.get("/graph/{entity_type}/{entity_id}")
async def get_entity_graph(entity_type: str, entity_id: str, depth: int = 2, request: Request):
    """Get knowledge graph around an entity"""
    # Get relations where entity is source or target
    relations = await db.knowledge_relations.find({
        "$or": [
            {"source_type": entity_type, "source_id": entity_id},
            {"target_type": entity_type, "target_id": entity_id}
        ]
    }, {"_id": 0}).to_list(100)
    
    # Build node list
    nodes = [{
        "id": entity_id,
        "type": entity_type,
        "label": entity_id
    }]
    
    edges = []
    for rel in relations:
        # Add connected nodes
        if rel["source_id"] != entity_id:
            nodes.append({
                "id": rel["source_id"],
                "type": rel["source_type"],
                "label": rel["source_id"]
            })
        if rel["target_id"] != entity_id:
            nodes.append({
                "id": rel["target_id"],
                "type": rel["target_type"],
                "label": rel["target_id"]
            })
        
        edges.append({
            "source": rel["source_id"],
            "target": rel["target_id"],
            "type": rel["relation_type"],
            "weight": rel["weight"]
        })
    
    # Deduplicate nodes
    seen = set()
    unique_nodes = []
    for node in nodes:
        if node["id"] not in seen:
            seen.add(node["id"])
            unique_nodes.append(node)
    
    return {
        "nodes": unique_nodes,
        "edges": edges,
        "center": entity_id
    }

# ==================== ANALYTICS ROUTES ====================

@router.get("/analytics/overview")
async def get_efi_analytics(request: Request):
    """Get EFI system analytics"""
    total_cards = await db.failure_cards.count_documents({})
    approved_cards = await db.failure_cards.count_documents({"status": "approved"})
    draft_cards = await db.failure_cards.count_documents({"status": "draft"})
    
    # Top performing cards
    top_cards = await db.failure_cards.find(
        {"status": "approved"},
        {"_id": 0, "failure_id": 1, "title": 1, "effectiveness_score": 1, "usage_count": 1}
    ).sort("effectiveness_score", -1).limit(5).to_list(5)
    
    # By subsystem
    subsystem_pipeline = [
        {"$group": {"_id": "$subsystem_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_subsystem = await db.failure_cards.aggregate(subsystem_pipeline).to_list(20)
    
    # Recent events
    recent_events = await db.efi_events.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)
    
    # Total matches performed
    total_matches = await db.efi_events.count_documents({"event_type": "match_performed"})
    
    return {
        "total_failure_cards": total_cards,
        "approved_cards": approved_cards,
        "draft_cards": draft_cards,
        "top_performing_cards": top_cards,
        "by_subsystem": by_subsystem,
        "total_matches_performed": total_matches,
        "recent_events": recent_events
    }

@router.get("/analytics/effectiveness")
async def get_effectiveness_report(request: Request):
    """Get effectiveness report for failure cards"""
    pipeline = [
        {"$match": {"status": "approved", "usage_count": {"$gt": 0}}},
        {"$project": {
            "_id": 0,
            "failure_id": 1,
            "title": 1,
            "subsystem_category": 1,
            "usage_count": 1,
            "success_count": 1,
            "failure_count": 1,
            "effectiveness_score": 1,
            "confidence_score": 1,
            "success_rate": {
                "$cond": [
                    {"$gt": ["$usage_count", 0]},
                    {"$divide": ["$success_count", "$usage_count"]},
                    0
                ]
            }
        }},
        {"$sort": {"usage_count": -1}}
    ]
    
    report = await db.failure_cards.aggregate(pipeline).to_list(50)
    
    return {
        "report": report,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

# ==================== EVENT PROCESSING ====================

@router.get("/events")
async def list_events(
    request: Request,
    event_type: Optional[str] = None,
    processed: Optional[bool] = None,
    limit: int = 50
):
    """List EFI system events"""
    query = {}
    if event_type:
        query["event_type"] = event_type
    if processed is not None:
        query["processed"] = processed
    
    events = await db.efi_events.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return events

@router.post("/events/process")
async def process_pending_events(request: Request, background_tasks: BackgroundTasks):
    """Process pending EFI events (background job trigger)"""
    pending = await db.efi_events.count_documents({"processed": False})
    
    async def process_events():
        events = await db.efi_events.find({"processed": False}).limit(100).to_list(100)
        
        for event in events:
            try:
                event_type = event.get("event_type")
                
                if event_type == "new_failure_discovered":
                    # Auto-create draft failure card
                    data = event.get("data", {})
                    if data.get("observations"):
                        # Would create draft card here
                        pass
                
                elif event_type == "failure_card_approved":
                    # Trigger network sync
                    pass
                
                # Mark as processed
                await db.efi_events.update_one(
                    {"event_id": event["event_id"]},
                    {"$set": {"processed": True, "processing_result": {"status": "success"}}}
                )
                
            except Exception as e:
                await db.efi_events.update_one(
                    {"event_id": event["event_id"]},
                    {"$set": {"processing_result": {"status": "error", "error": str(e)}}}
                )
    
    background_tasks.add_task(process_events)
    
    return {"message": f"Processing {pending} pending events", "queued": True}
