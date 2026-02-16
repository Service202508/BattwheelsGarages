"""
Battwheels OS - Failure Intelligence Routes
Core routes for the EV Failure Intelligence (EFI) Platform

Version 2.0 - Enhanced with:
- Failure signature matching
- Diagnostic tree support
- Confidence history tracking
- Pattern detection endpoints
- Part usage tracking
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import asyncio
import logging
import hashlib

from models.failure_intelligence import (
    FailureCard, FailureCardCreate, FailureCardUpdate, FailureCardStatus,
    SubsystemCategory, ConfidenceLevel, FailureMode, SourceType,
    TechnicianAction, TechnicianActionCreate,
    FailureMatchRequest, FailureMatchResult, FailureMatchResponse,
    Symptom, SymptomCreate,
    KnowledgeRelation, EFIEvent, EFIEventType,
    FailureSignature, ConfidenceChangeEvent,
    PartUsage, PartUsageCreate,
    EmergingPattern
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/efi", tags=["Failure Intelligence"])

# Database and service references
db = None
event_processor = None

def init_router(database, processor=None):
    global db, event_processor
    db = database
    event_processor = processor
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
        return 0.5
    success_rate = success_count / usage_count
    usage_bonus = min(0.1, usage_count / 100)
    return min(1.0, success_rate + usage_bonus)

def compute_signature_hash(signature_data: dict) -> str:
    """Generate deterministic hash for failure signature"""
    components = [
        ",".join(sorted(signature_data.get("primary_symptoms", []))),
        ",".join(sorted(signature_data.get("error_codes", []))),
        str(signature_data.get("subsystem", "")),
        str(signature_data.get("failure_mode", "")),
        signature_data.get("temperature_range", ""),
        signature_data.get("load_condition", "")
    ]
    hash_input = "|".join(components).lower()
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

def extract_keywords(text: str) -> List[str]:
    """Extract symptom keywords from text"""
    symptom_indicators = [
        "not", "no", "fail", "error", "issue", "problem", "slow", "fast",
        "hot", "cold", "noise", "vibration", "charging", "battery", "motor",
        "display", "brake", "smoke", "burn", "leak", "stuck", "loose"
    ]
    words = text.lower().split()
    keywords = []
    for word in words:
        for indicator in symptom_indicators:
            if indicator in word:
                keywords.append(word)
                break
    return list(set(keywords))[:20]

def compute_text_similarity(text1: str, text2: str) -> float:
    """Compute simple text similarity using keyword overlap"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)

async def emit_event(event_type: str, data: dict, priority: int = 5):
    """Emit an EFI event for async processing"""
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "source": "api",
        "priority": priority,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed": False,
        "retry_count": 0,
        "max_retries": 3
    }
    await db.efi_events.insert_one(event)
    return event["event_id"]

# ==================== FAILURE CARD ROUTES ====================

@router.post("/failure-cards")
async def create_failure_card(data: FailureCardCreate, request: Request, background_tasks: BackgroundTasks):
    """Create a new failure intelligence card"""
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Build failure signature
    signature_data = data.failure_signature or {}
    if not signature_data:
        signature_data = {
            "primary_symptoms": extract_keywords(f"{data.title} {data.symptom_text or ''}"),
            "error_codes": data.error_codes,
            "subsystem": data.subsystem_category.value,
            "failure_mode": data.failure_mode.value if data.failure_mode else "unknown"
        }
    signature_hash = compute_signature_hash(signature_data)
    
    # Initial confidence history entry
    initial_confidence = 0.5 if data.source_type == SourceType.FIELD_DISCOVERY else 0.7
    confidence_history = [{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_score": 0.0,
        "new_score": initial_confidence,
        "change_reason": "initial_creation",
        "notes": f"Created via {data.source_type.value if data.source_type else 'field_discovery'}"
    }]
    
    # Build failure card with all new fields
    card = FailureCard(
        title=data.title,
        description=data.description,
        subsystem_category=data.subsystem_category,
        failure_mode=data.failure_mode,
        
        # Failure signature
        failure_signature=FailureSignature(**signature_data) if signature_data else None,
        signature_hash=signature_hash,
        
        # Symptoms
        symptom_codes=data.symptom_codes,
        symptom_text=data.symptom_text,
        error_codes=data.error_codes,
        
        # Root cause
        root_cause=data.root_cause,
        root_cause_details=data.root_cause_details,
        secondary_causes=data.secondary_causes,
        
        # Diagnostic tree
        diagnostic_tree=data.diagnostic_tree,
        
        # Steps
        verification_steps=data.verification_steps,
        resolution_steps=data.resolution_steps,
        required_parts=data.required_parts,
        
        # Vehicle
        vehicle_models=data.vehicle_models,
        universal_failure=data.universal_failure,
        failure_conditions=data.failure_conditions,
        
        # Keywords
        keywords=data.keywords,
        tags=data.tags,
        
        # Provenance
        source_type=data.source_type or SourceType.FIELD_DISCOVERY,
        source_ticket_id=data.source_ticket_id,
        
        # Intelligence
        confidence_score=initial_confidence,
        confidence_level=calculate_confidence_level(initial_confidence),
        confidence_history=confidence_history,
        
        # Status
        status=FailureCardStatus.DRAFT,
        
        # Timestamps
        first_detected_at=datetime.now(timezone.utc)
    )
    
    # Calculate estimated costs
    total_parts_cost = sum(p.get("estimated_cost", 0) for p in data.required_parts)
    total_time = sum(s.get("duration_minutes", 0) for s in data.resolution_steps)
    labor_cost = total_time * 5
    
    card.estimated_parts_cost = total_parts_cost
    card.estimated_labor_cost = labor_cost
    card.estimated_total_cost = total_parts_cost + labor_cost
    card.estimated_repair_time_minutes = total_time
    
    # Generate keywords from content
    content_text = f"{data.title} {data.description or ''} {data.root_cause} {data.symptom_text or ''}"
    card.keywords = list(set(card.keywords + extract_keywords(content_text)))
    
    # Store
    doc = card.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('first_detected_at'):
        doc['first_detected_at'] = doc['first_detected_at'].isoformat()
    if doc.get('failure_signature'):
        # Ensure signature is serializable
        pass
    if doc.get('confidence_history'):
        for entry in doc['confidence_history']:
            if isinstance(entry.get('timestamp'), datetime):
                entry['timestamp'] = entry['timestamp'].isoformat()
    
    await db.failure_cards.insert_one(doc)
    
    # Emit event
    await emit_event(
        EFIEventType.CARD_CREATED.value,
        {"failure_id": card.failure_id, "title": card.title, "status": "draft"},
        priority=5
    )
    
    return card.model_dump()

@router.get("/failure-cards")
async def list_failure_cards(
    request: Request,
    status: Optional[str] = None,
    subsystem: Optional[str] = None,
    search: Optional[str] = None,
    min_confidence: Optional[float] = None,
    min_effectiveness: Optional[float] = None,
    source_type: Optional[str] = None,
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
    if min_effectiveness:
        query["effectiveness_score"] = {"$gte": min_effectiveness}
    if source_type:
        query["source_type"] = source_type
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"root_cause": {"$regex": search, "$options": "i"}},
            {"keywords": {"$in": [search.lower()]}},
            {"error_codes": {"$in": [search.upper()]}},
            {"signature_hash": search}
        ]
    
    cards = await db.failure_cards.find(
        query, 
        {"_id": 0, "embedding_vector": 0}
    ).sort([("confidence_score", -1), ("effectiveness_score", -1)]).skip(skip).limit(limit).to_list(limit)
    
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

@router.get("/failure-cards/{failure_id}/confidence-history")
async def get_confidence_history(failure_id: str, request: Request):
    """Get confidence score history for a failure card"""
    card = await db.failure_cards.find_one(
        {"failure_id": failure_id},
        {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, "confidence_history": 1}
    )
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    return {
        "failure_id": card["failure_id"],
        "title": card["title"],
        "current_confidence": card.get("confidence_score", 0.5),
        "history": card.get("confidence_history", [])
    }

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
    
    # Recompute signature hash if signature changed
    if data.failure_signature:
        update_dict["signature_hash"] = compute_signature_hash(data.failure_signature)
    
    # Track confidence change in history
    if data.confidence_score and data.confidence_score != existing.get("confidence_score"):
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_score": existing.get("confidence_score", 0.5),
            "new_score": data.confidence_score,
            "change_reason": "manual_update",
            "notes": "Updated via API"
        }
        await db.failure_cards.update_one(
            {"failure_id": failure_id},
            {"$push": {"confidence_history": history_entry}}
        )
        update_dict["confidence_level"] = calculate_confidence_level(data.confidence_score).value
    
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
    
    # Emit update event
    await emit_event(
        EFIEventType.CARD_UPDATED.value,
        {"failure_id": failure_id, "changes": list(update_dict.keys())}
    )
    
    updated = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0, "embedding_vector": 0})
    return updated

@router.post("/failure-cards/{failure_id}/approve")
async def approve_failure_card(failure_id: str, request: Request, approved_by: Optional[str] = None):
    """Approve a failure card for network distribution"""
    card = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    if card.get("status") == FailureCardStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Card already approved")
    
    # Boost confidence on approval
    old_confidence = card.get("confidence_score", 0.5)
    new_confidence = min(1.0, old_confidence + 0.2)  # Approval adds confidence
    
    history_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_score": old_confidence,
        "new_score": new_confidence,
        "change_reason": "expert_approval",
        "notes": f"Approved by {approved_by or 'expert'}"
    }
    
    await db.failure_cards.update_one(
        {"failure_id": failure_id},
        {
            "$set": {
                "status": FailureCardStatus.APPROVED.value,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": approved_by,
                "confidence_score": new_confidence,
                "confidence_level": calculate_confidence_level(new_confidence).value
            },
            "$push": {"confidence_history": history_entry}
        }
    )
    
    # Emit approval event
    await emit_event(
        EFIEventType.CARD_APPROVED.value,
        {"failure_id": failure_id, "approved_by": approved_by},
        priority=3
    )
    
    return {"message": "Failure card approved", "failure_id": failure_id, "new_confidence": new_confidence}

@router.post("/failure-cards/{failure_id}/deprecate")
async def deprecate_failure_card(failure_id: str, reason: str, request: Request):
    """Deprecate a failure card"""
    card = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    await db.failure_cards.update_one(
        {"failure_id": failure_id},
        {"$set": {
            "status": FailureCardStatus.DEPRECATED.value,
            "deprecation_reason": reason,
            "deprecated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await emit_event(
        EFIEventType.CARD_DEPRECATED.value,
        {"failure_id": failure_id, "reason": reason}
    )
    
    return {"message": "Failure card deprecated", "failure_id": failure_id}

# ==================== AI MATCHING ROUTES ====================

@router.post("/match")
async def match_failure(data: FailureMatchRequest, request: Request) -> FailureMatchResponse:
    """
    AI-powered failure matching - 4-stage pipeline
    
    Priority order (per architecture):
    1. Failure signature match (fastest, highest confidence)
    2. Subsystem + vehicle filtering
    3. Semantic similarity
    4. Keyword fallback
    """
    import time
    start_time = time.time()
    
    query_text = data.symptom_text
    if data.error_codes:
        query_text += " " + " ".join(data.error_codes)
    
    # Build signature for matching
    signature_data = {
        "primary_symptoms": extract_keywords(data.symptom_text),
        "error_codes": data.error_codes,
        "subsystem": data.subsystem_hint.value if data.subsystem_hint else "",
        "failure_mode": data.failure_mode_hint.value if data.failure_mode_hint else "",
        "temperature_range": data.temperature_range or "",
        "load_condition": data.load_condition or ""
    }
    signature_hash = compute_signature_hash(signature_data)
    
    all_matches = []
    stages_used = []
    
    # Stage 1: Signature match (fastest, highest confidence)
    signature_matches = await db.failure_cards.find(
        {"signature_hash": signature_hash, "status": {"$in": ["approved", "draft"]}},
        {"_id": 0, "embedding_vector": 0}
    ).limit(5).to_list(5)
    
    if signature_matches:
        stages_used.append("signature")
        for card in signature_matches:
            all_matches.append(FailureMatchResult(
                failure_id=card["failure_id"],
                title=card["title"],
                match_score=0.95,
                match_type="signature",
                match_stage=1,
                matched_error_codes=list(set(card.get("error_codes", [])) & set(data.error_codes)),
                confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                effectiveness_score=card.get("effectiveness_score", 0)
            ))
    
    # Stage 2: Subsystem + Vehicle filtering
    if not all_matches or all_matches[0].match_score < 0.9:
        stages_used.append("subsystem_vehicle")
        
        stage2_query = {"status": {"$in": ["approved", "draft"]}}
        if data.subsystem_hint:
            stage2_query["subsystem_category"] = data.subsystem_hint.value
        
        stage2_cards = await db.failure_cards.find(
            stage2_query,
            {"_id": 0, "embedding_vector": 0}
        ).limit(20).to_list(20)
        
        for card in stage2_cards:
            if card["failure_id"] in [m.failure_id for m in all_matches]:
                continue
            
            score = 0.5
            matched_symptoms = []
            
            # Vehicle match bonus
            if data.vehicle_make:
                for vm in card.get("vehicle_models", []):
                    if vm.get("make", "").lower() == data.vehicle_make.lower():
                        score += 0.15
                        if data.vehicle_model and vm.get("model", "").lower() == data.vehicle_model.lower():
                            score += 0.1
                        break
            
            # Error code overlap
            card_codes = set(card.get("error_codes", []))
            query_codes = set(data.error_codes)
            if card_codes & query_codes:
                score += 0.2 * (len(card_codes & query_codes) / max(len(query_codes), 1))
            
            if score > 0.4:
                all_matches.append(FailureMatchResult(
                    failure_id=card["failure_id"],
                    title=card["title"],
                    match_score=min(0.85, score),
                    match_type="subsystem_vehicle",
                    match_stage=2,
                    matched_symptoms=matched_symptoms,
                    matched_error_codes=list(card_codes & query_codes),
                    confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                    effectiveness_score=card.get("effectiveness_score", 0)
                ))
    
    # Stage 3: Semantic similarity
    if not all_matches or all_matches[0].match_score < 0.7:
        stages_used.append("semantic")
        
        keywords = extract_keywords(query_text)
        if keywords:
            stage3_cards = await db.failure_cards.find(
                {
                    "status": {"$in": ["approved", "draft"]},
                    "$or": [
                        {"keywords": {"$in": keywords}},
                        {"symptom_text": {"$regex": "|".join(keywords[:5]), "$options": "i"}}
                    ]
                },
                {"_id": 0, "embedding_vector": 0}
            ).limit(10).to_list(10)
            
            for card in stage3_cards:
                if card["failure_id"] in [m.failure_id for m in all_matches]:
                    continue
                
                # Calculate keyword overlap
                card_keywords = set(card.get("keywords", []))
                query_keywords = set(keywords)
                overlap = len(card_keywords & query_keywords)
                score = min(0.7, 0.3 + (overlap * 0.08))
                
                # Text similarity boost
                if card.get("symptom_text"):
                    text_sim = compute_text_similarity(query_text, card["symptom_text"])
                    score = max(score, text_sim * 0.75)
                
                if score > 0.35:
                    all_matches.append(FailureMatchResult(
                        failure_id=card["failure_id"],
                        title=card["title"],
                        match_score=score,
                        match_type="semantic",
                        match_stage=3,
                        matched_symptoms=list(card_keywords & query_keywords)[:5],
                        confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                        effectiveness_score=card.get("effectiveness_score", 0)
                    ))
    
    # Stage 4: Keyword fallback
    if not all_matches or all_matches[0].match_score < 0.5:
        stages_used.append("keyword")
        
        try:
            stage4_cards = await db.failure_cards.find(
                {
                    "status": {"$in": ["approved", "draft"]},
                    "$text": {"$search": query_text}
                },
                {"_id": 0, "embedding_vector": 0, "score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(5).to_list(5)
            
            for card in stage4_cards:
                if card["failure_id"] in [m.failure_id for m in all_matches]:
                    continue
                
                all_matches.append(FailureMatchResult(
                    failure_id=card["failure_id"],
                    title=card["title"],
                    match_score=min(0.5, card.get("score", 0) / 10),
                    match_type="keyword",
                    match_stage=4,
                    confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                    effectiveness_score=card.get("effectiveness_score", 0)
                ))
        except Exception as e:
            logger.warning(f"Text search failed: {e}")
    
    # Sort by score, then effectiveness
    all_matches.sort(key=lambda x: (x.match_score, x.effectiveness_score), reverse=True)
    
    # Log matching event
    await emit_event(
        EFIEventType.MATCH_COMPLETED.value,
        {
            "query": query_text[:200],
            "signature_hash": signature_hash,
            "matches_found": len(all_matches),
            "stages_used": stages_used,
            "top_match": all_matches[0].failure_id if all_matches else None,
            "top_score": all_matches[0].match_score if all_matches else 0
        }
    )
    
    processing_time = (time.time() - start_time) * 1000
    
    return FailureMatchResponse(
        query_text=query_text,
        signature_hash=signature_hash,
        matches=[m for m in all_matches[:data.limit]],
        processing_time_ms=processing_time,
        model_used="hybrid_4stage_pipeline",
        matching_stages_used=stages_used
    )

@router.post("/match-ticket/{ticket_id}")
async def match_ticket_to_failures(ticket_id: str, request: Request, background_tasks: BackgroundTasks):
    """Match an existing ticket to failure cards and suggest solutions"""
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Build match request from ticket
    match_request = FailureMatchRequest(
        symptom_text=f"{ticket.get('title', '')} {ticket.get('description', '')}",
        error_codes=ticket.get("error_codes_reported", []),
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
            {"$set": {
                "suggested_failure_cards": suggested_ids,
                "ai_match_performed": True,
                "ai_match_timestamp": datetime.now(timezone.utc).isoformat(),
                "ai_match_signature_hash": response.signature_hash
            }}
        )
    
    return {
        "ticket_id": ticket_id,
        "matches": [m.model_dump() for m in response.matches],
        "processing_time_ms": response.processing_time_ms,
        "signature_hash": response.signature_hash
    }

# ==================== TECHNICIAN ACTION ROUTES ====================

@router.post("/technician-actions")
async def record_technician_action(data: TechnicianActionCreate, request: Request, background_tasks: BackgroundTasks):
    """
    Record technician diagnostic and repair actions
    
    Enhanced v2.0:
    - Records attempted_diagnostics and rejected_hypotheses
    - Triggers confidence updates
    - Auto-creates draft cards for new failures
    """
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    
    # Verify ticket exists
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get technician info
    technician_id = ""
    technician_name = None
    if token:
        session = await db.user_sessions.find_one({"session_token": token})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]})
            if user:
                technician_id = user["user_id"]
                technician_name = user.get("name")
    
    action = TechnicianAction(
        ticket_id=data.ticket_id,
        technician_id=technician_id,
        technician_name=technician_name,
        diagnostic_steps_performed=data.diagnostic_steps_performed,
        attempted_diagnostics=data.attempted_diagnostics,
        rejected_hypotheses=data.rejected_hypotheses,
        observations=data.observations,
        measurements=data.measurements,
        parts_used=data.parts_used,
        resolution_outcome=data.resolution_outcome,
        failure_card_used=data.failure_card_used,
        failure_card_helpful=data.failure_card_helpful,
        failure_card_accuracy_rating=data.failure_card_accuracy_rating,
        failure_card_modifications=data.failure_card_modifications,
        new_failure_discovered=data.new_failure_discovered,
        new_failure_description=data.new_failure_description,
        new_failure_root_cause=data.new_failure_root_cause,
        new_failure_resolution=data.new_failure_resolution,
        suggest_new_card=data.suggest_new_card,
        technician_notes=data.technician_notes,
        difficulty_rating=data.difficulty_rating,
        documentation_quality_rating=data.documentation_quality_rating,
        time_spent_minutes=data.time_spent_minutes,
        completed_at=datetime.now(timezone.utc)
    )
    
    doc = action.model_dump()
    doc['started_at'] = doc['started_at'].isoformat()
    doc['completed_at'] = doc['completed_at'].isoformat()
    
    # Serialize nested objects
    for diag in doc.get('attempted_diagnostics', []):
        if isinstance(diag.get('timestamp'), datetime):
            diag['timestamp'] = diag['timestamp'].isoformat()
    for hyp in doc.get('rejected_hypotheses', []):
        if isinstance(hyp.get('ruled_out_at'), datetime):
            hyp['ruled_out_at'] = hyp['ruled_out_at'].isoformat()
    
    await db.technician_actions.insert_one(doc)
    
    # Emit action completed event
    await emit_event(
        EFIEventType.ACTION_COMPLETED.value,
        {
            "action_id": action.action_id,
            "ticket_id": data.ticket_id,
            "outcome": data.resolution_outcome,
            "card_used": data.failure_card_used
        }
    )
    
    # If failure card was used, update its metrics
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
        
        # Emit card used event for confidence update
        await emit_event(
            EFIEventType.CARD_USED.value,
            {
                "failure_id": data.failure_card_used,
                "ticket_id": data.ticket_id,
                "outcome": data.resolution_outcome,
                "helpful": data.failure_card_helpful,
                "rating": data.failure_card_accuracy_rating
            },
            priority=4
        )
    
    # If new failure discovered, emit event for draft card creation
    if data.new_failure_discovered:
        await emit_event(
            EFIEventType.NEW_FAILURE_DISCOVERED.value,
            {
                "action_id": action.action_id,
                "ticket_id": data.ticket_id,
                "description": data.new_failure_description,
                "root_cause": data.new_failure_root_cause,
                "resolution": data.new_failure_resolution,
                "technician_id": technician_id
            },
            priority=3
        )
    
    return action.model_dump()

@router.get("/technician-actions")
async def list_technician_actions(
    request: Request,
    ticket_id: Optional[str] = None,
    technician_id: Optional[str] = None,
    include_hypotheses: bool = False,
    limit: int = 50
):
    """List technician actions"""
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    if technician_id:
        query["technician_id"] = technician_id
    
    projection = {"_id": 0}
    if not include_hypotheses:
        projection["rejected_hypotheses"] = 0
        projection["attempted_diagnostics"] = 0
    
    actions = await db.technician_actions.find(
        query, projection
    ).sort("completed_at", -1).limit(limit).to_list(limit)
    
    return actions

# ==================== PART USAGE ROUTES ====================

@router.post("/part-usage")
async def record_part_usage(data: PartUsageCreate, request: Request):
    """
    Record part usage with failure card linkage
    Tracks expected_vs_actual for pattern detection
    """
    # Verify ticket exists
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get part info
    part = await db.inventory.find_one({"item_id": data.part_id}, {"_id": 0})
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    usage = PartUsage(
        ticket_id=data.ticket_id,
        action_id=data.action_id,
        part_id=data.part_id,
        part_name=part.get("name", "Unknown"),
        part_number=part.get("sku"),
        category=part.get("category"),
        quantity_used=data.quantity_used,
        unit_cost=part.get("unit_price", 0),
        total_cost=data.quantity_used * part.get("unit_price", 0),
        failure_card_id=data.failure_card_id,
        was_recommended=data.was_recommended,
        is_substitute=data.is_substitute,
        substitute_for=data.substitute_for,
        expected_vs_actual=data.expected_vs_actual,
        expectation_notes=data.expectation_notes,
        status="used"
    )
    
    doc = usage.model_dump()
    doc['allocated_at'] = doc['allocated_at'].isoformat()
    doc['used_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.part_usage.insert_one(doc)
    
    # Update inventory
    await db.inventory.update_one(
        {"item_id": data.part_id},
        {"$inc": {"quantity": -data.quantity_used}}
    )
    
    return usage.model_dump()

@router.get("/part-usage")
async def list_part_usage(
    request: Request,
    ticket_id: Optional[str] = None,
    failure_card_id: Optional[str] = None,
    unexpected_only: bool = False,
    limit: int = 100
):
    """List part usage records"""
    query = {}
    if ticket_id:
        query["ticket_id"] = ticket_id
    if failure_card_id:
        query["failure_card_id"] = failure_card_id
    if unexpected_only:
        query["expected_vs_actual"] = False
    
    usage = await db.part_usage.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return usage

# ==================== PATTERN DETECTION ROUTES ====================

@router.get("/patterns")
async def list_emerging_patterns(
    request: Request,
    status: Optional[str] = None,
    pattern_type: Optional[str] = None,
    limit: int = 50
):
    """List detected emerging patterns"""
    query = {}
    if status:
        query["status"] = status
    if pattern_type:
        query["pattern_type"] = pattern_type
    
    patterns = await db.emerging_patterns.find(
        query, {"_id": 0}
    ).sort("occurrence_count", -1).limit(limit).to_list(limit)
    
    return patterns

@router.post("/patterns/{pattern_id}/review")
async def review_pattern(
    pattern_id: str,
    action: str,  # confirm, dismiss, create_card
    notes: Optional[str] = None,
    request: Request = None
):
    """Review and action an emerging pattern"""
    pattern = await db.emerging_patterns.find_one({"pattern_id": pattern_id}, {"_id": 0})
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    update = {
        "status": "reviewed" if action == "confirm" else ("dismissed" if action == "dismiss" else "actioned"),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "review_notes": notes,
        "action_taken": action
    }
    
    await db.emerging_patterns.update_one(
        {"pattern_id": pattern_id},
        {"$set": update}
    )
    
    # If creating card, emit event
    if action == "create_card":
        await emit_event(
            EFIEventType.PATTERN_ACTIONED.value,
            {"pattern_id": pattern_id, "action": "create_card"},
            priority=4
        )
    
    return {"message": f"Pattern {action}ed", "pattern_id": pattern_id}

@router.post("/patterns/detect")
async def trigger_pattern_detection(request: Request, background_tasks: BackgroundTasks):
    """Manually trigger pattern detection job"""
    if event_processor:
        background_tasks.add_task(
            event_processor.detect_emerging_patterns,
            min_occurrences=3,
            lookback_days=30
        )
        return {"message": "Pattern detection triggered", "status": "queued"}
    else:
        return {"message": "Event processor not configured", "status": "skipped"}

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
async def get_entity_graph(entity_type: str, entity_id: str, request: Request, depth: int = 2):
    """Get knowledge graph around an entity"""
    relations = await db.knowledge_relations.find({
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
    total_cards = await db.failure_cards.count_documents({})
    approved_cards = await db.failure_cards.count_documents({"status": "approved"})
    draft_cards = await db.failure_cards.count_documents({"status": "draft"})
    
    # Top performing cards
    top_cards = await db.failure_cards.find(
        {"status": "approved", "usage_count": {"$gt": 0}},
        {"_id": 0, "failure_id": 1, "title": 1, "effectiveness_score": 1, "usage_count": 1, "confidence_score": 1}
    ).sort("effectiveness_score", -1).limit(5).to_list(5)
    
    # By subsystem
    subsystem_pipeline = [
        {"$group": {"_id": "$subsystem_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_subsystem = await db.failure_cards.aggregate(subsystem_pipeline).to_list(20)
    
    # By source type
    source_pipeline = [
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_source = await db.failure_cards.aggregate(source_pipeline).to_list(10)
    
    # Total matches performed
    total_matches = await db.efi_events.count_documents({"event_type": "match.completed"})
    
    # Pending patterns
    pending_patterns = await db.emerging_patterns.count_documents({"status": "detected"})
    
    # Recent events
    recent_events = await db.efi_events.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)
    
    return {
        "total_failure_cards": total_cards,
        "approved_cards": approved_cards,
        "draft_cards": draft_cards,
        "top_performing_cards": top_cards,
        "by_subsystem": by_subsystem,
        "by_source_type": by_source,
        "total_matches_performed": total_matches,
        "pending_patterns": pending_patterns,
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
    
    report = await db.failure_cards.aggregate(pipeline).to_list(50)
    
    return {
        "report": report,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@router.get("/analytics/part-anomalies")
async def get_part_anomaly_report(request: Request):
    """Get report of unexpected part usage"""
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
    
    anomalies = await db.part_usage.aggregate(pipeline).to_list(20)
    
    return {
        "anomalies": anomalies,
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
    """Process pending EFI events"""
    pending = await db.efi_events.count_documents({"processed": False})
    
    if event_processor:
        background_tasks.add_task(event_processor.process_pending_events, limit=100)
        return {"message": f"Processing {pending} pending events", "queued": True}
    else:
        # Fallback simple processing
        async def simple_process():
            events = await db.efi_events.find({"processed": False}).limit(100).to_list(100)
            for event in events:
                await db.efi_events.update_one(
                    {"event_id": event["event_id"]},
                    {"$set": {"processed": True, "processed_at": datetime.now(timezone.utc).isoformat()}}
                )
        
        background_tasks.add_task(simple_process)
        return {"message": f"Processing {pending} pending events (simple mode)", "queued": True}
