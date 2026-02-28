"""
Battwheels OS - EFI Service
Business logic for EV Failure Intelligence Platform

Service responsibilities:
- Failure card CRUD operations
- AI matching pipeline (4-stage)
- Confidence scoring and history
- Technician action processing
- Pattern detection
- Event emission for all operations

Event Flow:
┌─────────────┐     ┌───────────────┐     ┌────────────────────┐
│ Create/     │ --> │ EFI Service   │ --> │ Event Dispatcher   │
│ Update/     │     │ (business     │     │ - Confidence Eng   │
│ Match       │     │  logic)       │     │ - Notifications    │
└─────────────┘     └───────────────┘     │ - Pattern Detect   │
                                          └────────────────────┘
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import logging
import hashlib
import time

from events import get_dispatcher, EventType, EventPriority
from models.failure_intelligence import (
    FailureCard, FailureCardCreate, FailureCardUpdate, FailureCardStatus,
    SubsystemCategory, ConfidenceLevel, FailureMode, SourceType,
    TechnicianAction, TechnicianActionCreate,
    FailureMatchRequest, FailureMatchResult, FailureMatchResponse,
    Symptom, SymptomCreate,
    PartUsage, PartUsageCreate,
    FailureSignature
)

# Optional imports for enhanced search
try:
    from services.embedding_service import get_embedding_service, get_card_embedder
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

try:
    from services.search_service import get_search_service
    ADVANCED_SEARCH_AVAILABLE = True
except ImportError:
    ADVANCED_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)


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


# ==================== EFI SERVICE ====================

class EFIService:
    """
    Core EFI business logic service
    
    All EFI operations flow through this service.
    Service emits events - handlers process them.
    """
    
    def __init__(self, db, event_processor=None):
        self.db = db
        self.event_processor = event_processor
        self.dispatcher = get_dispatcher()
        logger.info("EFIService initialized")
    
    # ==================== FAILURE CARD CREATION ====================
    
    async def create_failure_card(
        self,
        data: FailureCardCreate,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a new failure intelligence card
        
        Steps:
        1. Build failure signature for fast matching
        2. Initialize confidence history
        3. Calculate costs and keywords
        4. Store in database
        5. Emit FAILURE_CARD_CREATED event
        
        Returns:
            Created failure card document
        """
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
        
        # Initial confidence
        initial_confidence = 0.5 if data.source_type == SourceType.FIELD_DISCOVERY else 0.7
        confidence_history = [{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_score": 0.0,
            "new_score": initial_confidence,
            "change_reason": "initial_creation",
            "notes": f"Created via {data.source_type.value if data.source_type else 'field_discovery'}"
        }]
        
        # Build failure card
        card = FailureCard(
            title=data.title,
            description=data.description,
            subsystem_category=data.subsystem_category,
            failure_mode=data.failure_mode,
            failure_signature=FailureSignature(**signature_data) if signature_data else None,
            signature_hash=signature_hash,
            symptom_codes=data.symptom_codes,
            symptom_text=data.symptom_text,
            error_codes=data.error_codes,
            root_cause=data.root_cause,
            root_cause_details=data.root_cause_details,
            secondary_causes=data.secondary_causes,
            diagnostic_tree=data.diagnostic_tree,
            verification_steps=data.verification_steps,
            resolution_steps=data.resolution_steps,
            required_parts=data.required_parts,
            vehicle_models=data.vehicle_models,
            universal_failure=data.universal_failure,
            failure_conditions=data.failure_conditions,
            keywords=data.keywords,
            tags=data.tags,
            source_type=data.source_type or SourceType.FIELD_DISCOVERY,
            source_ticket_id=data.source_ticket_id,
            confidence_score=initial_confidence,
            confidence_level=calculate_confidence_level(initial_confidence),
            confidence_history=confidence_history,
            status=FailureCardStatus.DRAFT,
            first_detected_at=datetime.now(timezone.utc)
        )
        
        # Calculate costs
        total_parts_cost = sum(p.get("estimated_cost", 0) for p in data.required_parts)
        total_time = sum(s.get("duration_minutes", 0) for s in data.resolution_steps)
        labor_cost = total_time * 5
        
        card.estimated_parts_cost = total_parts_cost
        card.estimated_labor_cost = labor_cost
        card.estimated_total_cost = total_parts_cost + labor_cost
        card.estimated_repair_time_minutes = total_time
        
        # Generate keywords
        content_text = f"{data.title} {data.description or ''} {data.root_cause} {data.symptom_text or ''}"
        card.keywords = list(set(card.keywords + extract_keywords(content_text)))
        
        # Serialize and store
        doc = card.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        if doc.get('first_detected_at'):
            doc['first_detected_at'] = doc['first_detected_at'].isoformat()
        if doc.get('confidence_history'):
            for entry in doc['confidence_history']:
                if isinstance(entry.get('timestamp'), datetime):
                    entry['timestamp'] = entry['timestamp'].isoformat()
        
        await self.db.failure_cards.insert_one(doc)
        
        # EMIT FAILURE_CARD_CREATED EVENT
        await self.dispatcher.emit(
            EventType.FAILURE_CARD_CREATED,
            {
                "failure_id": card.failure_id,
                "title": card.title,
                "subsystem": card.subsystem_category.value,
                "status": "draft",
                "created_by": user_id
            },
            source="efi_service",
            user_id=user_id
        )
        
        logger.info(f"Created failure card {card.failure_id}, emitted FAILURE_CARD_CREATED")
        
        # Return without _id
        return await self.db.failure_cards.find_one(
            {"failure_id": card.failure_id},
            {"_id": 0, "embedding_vector": 0}
        )
    
    # ==================== FAILURE CARD QUERIES ====================
    
    async def get_failure_card(self, failure_id: str) -> Optional[Dict[str, Any]]:
        """Get a single failure card by ID"""
        return await self.db.failure_cards.find_one(
            {"failure_id": failure_id},
            {"_id": 0, "embedding_vector": 0}
        )
    
    async def list_failure_cards(
        self,
        status: Optional[str] = None,
        subsystem: Optional[str] = None,
        search: Optional[str] = None,
        min_confidence: Optional[float] = None,
        min_effectiveness: Optional[float] = None,
        source_type: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List failure cards with filtering"""
        query = {}

        # Scope to organisation — failure cards are org-specific knowledge base
        if organization_id:
            query["organization_id"] = organization_id
        
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
        
        cards = await self.db.failure_cards.find(
            query,
            {"_id": 0, "embedding_vector": 0}
        ).sort([("confidence_score", -1), ("effectiveness_score", -1)]).skip(skip).limit(limit).to_list(limit)
        
        total = await self.db.failure_cards.count_documents(query)
        
        return {
            "items": cards,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    
    async def get_confidence_history(self, failure_id: str) -> Dict[str, Any]:
        """Get confidence score history for a failure card"""
        card = await self.db.failure_cards.find_one(
            {"failure_id": failure_id},
            {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, "confidence_history": 1}
        )
        if not card:
            raise ValueError(f"Failure card {failure_id} not found")
        
        return {
            "failure_id": card["failure_id"],
            "title": card["title"],
            "current_confidence": card.get("confidence_score", 0.5),
            "history": card.get("confidence_history", [])
        }
    
    # ==================== FAILURE CARD UPDATE ====================
    
    async def update_failure_card(
        self,
        failure_id: str,
        data: FailureCardUpdate,
        user_id: str
    ) -> Dict[str, Any]:
        """Update a failure card"""
        existing = await self.db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
        if not existing:
            raise ValueError(f"Failure card {failure_id} not found")
        
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        update_dict["version"] = existing.get("version", 1) + 1
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Recompute signature hash if signature changed
        if data.failure_signature:
            update_dict["signature_hash"] = compute_signature_hash(data.failure_signature)
        
        # Track confidence change
        if data.confidence_score and data.confidence_score != existing.get("confidence_score"):
            history_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_score": existing.get("confidence_score", 0.5),
                "new_score": data.confidence_score,
                "change_reason": "manual_update",
                "notes": f"Updated by {user_id}"
            }
            await self.db.failure_cards.update_one(
                {"failure_id": failure_id},
                {"$push": {"confidence_history": history_entry}}
            )
            update_dict["confidence_level"] = calculate_confidence_level(data.confidence_score).value
        
        # Version history
        version_entry = {
            "version": existing.get("version", 1),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "changes": list(update_dict.keys())
        }
        
        await self.db.failure_cards.update_one(
            {"failure_id": failure_id},
            {"$set": update_dict, "$push": {"version_history": version_entry}}
        )
        
        # EMIT FAILURE_CARD_UPDATED EVENT
        await self.dispatcher.emit(
            EventType.FAILURE_CARD_UPDATED,
            {
                "failure_id": failure_id,
                "changes": list(update_dict.keys()),
                "updated_by": user_id
            },
            source="efi_service",
            user_id=user_id
        )
        
        logger.info(f"Updated failure card {failure_id}")
        
        return await self.db.failure_cards.find_one(
            {"failure_id": failure_id},
            {"_id": 0, "embedding_vector": 0}
        )
    
    # ==================== FAILURE CARD APPROVAL ====================
    
    async def approve_failure_card(
        self,
        failure_id: str,
        approved_by: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Approve a failure card for network distribution"""
        card = await self.db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
        if not card:
            raise ValueError(f"Failure card {failure_id} not found")
        
        if card.get("status") == FailureCardStatus.APPROVED.value:
            raise ValueError("Card already approved")
        
        # Boost confidence on approval
        old_confidence = card.get("confidence_score", 0.5)
        new_confidence = min(1.0, old_confidence + 0.2)
        
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_score": old_confidence,
            "new_score": new_confidence,
            "change_reason": "expert_approval",
            "notes": f"Approved by {approved_by}"
        }
        
        await self.db.failure_cards.update_one(
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
        
        # EMIT FAILURE_CARD_APPROVED EVENT
        await self.dispatcher.emit(
            EventType.FAILURE_CARD_APPROVED,
            {
                "failure_id": failure_id,
                "approved_by": approved_by,
                "new_confidence": new_confidence
            },
            source="efi_service",
            user_id=user_id,
            priority=EventPriority.HIGH
        )
        
        logger.info(f"Approved failure card {failure_id}")
        
        return {
            "message": "Failure card approved",
            "failure_id": failure_id,
            "new_confidence": new_confidence
        }
    
    async def deprecate_failure_card(
        self,
        failure_id: str,
        reason: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Deprecate a failure card"""
        card = await self.db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
        if not card:
            raise ValueError(f"Failure card {failure_id} not found")
        
        await self.db.failure_cards.update_one(
            {"failure_id": failure_id},
            {"$set": {
                "status": FailureCardStatus.DEPRECATED.value,
                "deprecation_reason": reason,
                "deprecated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # EMIT FAILURE_CARD_DEPRECATED EVENT
        await self.dispatcher.emit(
            EventType.FAILURE_CARD_DEPRECATED,
            {"failure_id": failure_id, "reason": reason},
            source="efi_service",
            user_id=user_id
        )
        
        return {"message": "Failure card deprecated", "failure_id": failure_id}
    
    # ==================== AI MATCHING ====================
    
    async def match_failure(self, data: FailureMatchRequest) -> FailureMatchResponse:
        """
        AI-powered failure matching - Enhanced 5-stage pipeline
        
        Priority order:
        1. Failure signature match (fastest, highest confidence)
        2. Subsystem + vehicle filtering
        3. Vector semantic search (if embeddings available)
        4. Hybrid text+vector search
        5. Keyword fallback
        """
        start_time = time.time()
        
        query_text = data.symptom_text
        if data.error_codes:
            query_text += " " + " ".join(data.error_codes)
        
        # Build signature
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
        
        # Stage 1: Signature match (exact hash match)
        signature_matches = await self.db.failure_cards.find(
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
            
            stage2_cards = await self.db.failure_cards.find(
                stage2_query, {"_id": 0, "embedding_vector": 0}
            ).limit(20).to_list(20)
            
            for card in stage2_cards:
                if card["failure_id"] in [m.failure_id for m in all_matches]:
                    continue
                
                score = 0.5
                
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
                        matched_error_codes=list(card_codes & query_codes),
                        confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                        effectiveness_score=card.get("effectiveness_score", 0)
                    ))
        
        # Stage 3: Vector Semantic Search (if available)
        if EMBEDDINGS_AVAILABLE and (not all_matches or all_matches[0].match_score < 0.8):
            try:
                embedding_service = get_embedding_service()
                query_embedding = await embedding_service.get_embedding(query_text)
                
                if query_embedding:
                    stages_used.append("vector_semantic")
                    
                    vector_results = await embedding_service.find_similar(
                        query_embedding=query_embedding,
                        collection="failure_cards",
                        embedding_field="embedding_vector",
                        filter_query={"status": {"$in": ["approved", "draft"]}},
                        limit=10,
                        min_score=0.6
                    )
                    
                    for card in vector_results:
                        if card["failure_id"] in [m.failure_id for m in all_matches]:
                            # Update existing match score if vector score is higher
                            for m in all_matches:
                                if m.failure_id == card["failure_id"]:
                                    vector_score = card.get("score", 0) * 0.85
                                    if vector_score > m.match_score:
                                        m.match_score = vector_score
                                        m.match_type = "hybrid"
                            continue
                        
                        all_matches.append(FailureMatchResult(
                            failure_id=card["failure_id"],
                            title=card["title"],
                            match_score=card.get("score", 0.6) * 0.85,
                            match_type="vector_semantic",
                            match_stage=3,
                            matched_symptoms=extract_keywords(card.get("symptom_text", ""))[:5],
                            confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                            effectiveness_score=card.get("effectiveness_score", 0)
                        ))
            except Exception as e:
                logger.warning(f"Vector search failed, continuing with fallback: {e}")
        
        # Stage 4: Hybrid Text+Vector Search (if advanced search available)
        if ADVANCED_SEARCH_AVAILABLE and (not all_matches or all_matches[0].match_score < 0.7):
            try:
                search_service = get_search_service()
                hybrid_results = await search_service.hybrid_search(
                    query=query_text,
                    error_codes=data.error_codes,
                    subsystem=data.subsystem_hint.value if data.subsystem_hint else None,
                    vehicle_make=data.vehicle_make,
                    vehicle_model=data.vehicle_model,
                    limit=10
                )
                
                if hybrid_results:
                    stages_used.append("hybrid")
                    
                    for card in hybrid_results:
                        if card["failure_id"] in [m.failure_id for m in all_matches]:
                            continue
                        
                        all_matches.append(FailureMatchResult(
                            failure_id=card["failure_id"],
                            title=card["title"],
                            match_score=min(0.75, card.get("hybrid_score", 0.5)),
                            match_type="hybrid",
                            match_stage=4,
                            confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                            effectiveness_score=card.get("effectiveness_score", 0)
                        ))
            except Exception as e:
                logger.warning(f"Hybrid search failed: {e}")
        
        # Stage 5: Keyword fallback
        if not all_matches or all_matches[0].match_score < 0.5:
            if "keyword" not in stages_used:
                stages_used.append("keyword")
            
            try:
                stage5_cards = await self.db.failure_cards.find(
                    {
                        "status": {"$in": ["approved", "draft"]},
                        "$text": {"$search": query_text}
                    },
                    {"_id": 0, "embedding_vector": 0, "score": {"$meta": "textScore"}}
                ).sort([("score", {"$meta": "textScore"})]).limit(5).to_list(5)
                
                for card in stage5_cards:
                    if card["failure_id"] in [m.failure_id for m in all_matches]:
                        continue
                    
                    all_matches.append(FailureMatchResult(
                        failure_id=card["failure_id"],
                        title=card["title"],
                        match_score=min(0.5, card.get("score", 0) / 10),
                        match_type="keyword",
                        match_stage=5,
                        confidence_level=calculate_confidence_level(card.get("confidence_score", 0.5)),
                        effectiveness_score=card.get("effectiveness_score", 0)
                    ))
            except Exception as e:
                logger.warning(f"Text search failed: {e}")
        
        # Sort by score
        all_matches.sort(key=lambda x: (x.match_score, x.effectiveness_score), reverse=True)
        
        # EMIT MATCH_COMPLETED EVENT
        await self.dispatcher.emit(
            EventType.MATCH_COMPLETED,
            {
                "query": query_text[:200],
                "signature_hash": signature_hash,
                "matches_found": len(all_matches),
                "stages_used": stages_used,
                "top_match": all_matches[0].failure_id if all_matches else None,
                "top_score": all_matches[0].match_score if all_matches else 0
            },
            source="efi_service"
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
    
    async def match_ticket_to_failures(self, ticket_id: str, org_id: str = None) -> Dict[str, Any]:
        """Match an existing ticket to failure cards"""
        ticket_query = {"ticket_id": ticket_id}
        if org_id:
            ticket_query["organization_id"] = org_id
        ticket = await self.db.tickets.find_one(ticket_query, {"_id": 0})
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        match_request = FailureMatchRequest(
            symptom_text=f"{ticket.get('title', '')} {ticket.get('description', '')}",
            error_codes=ticket.get("error_codes_reported", []),
            vehicle_make=ticket.get("vehicle_make"),
            vehicle_model=ticket.get("vehicle_model"),
            subsystem_hint=None,
            limit=5
        )
        
        response = await self.match_failure(match_request)
        
        # Update ticket
        if response.matches:
            suggested_ids = [m.failure_id for m in response.matches]
            ticket_update_filter = {"ticket_id": ticket_id}
            if org_id:
                ticket_update_filter["organization_id"] = org_id
            await self.db.tickets.update_one(
                ticket_update_filter,
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
    
    # ==================== TECHNICIAN ACTIONS ====================
    
    async def record_technician_action(
        self,
        data: TechnicianActionCreate,
        technician_id: str,
        technician_name: Optional[str],
        org_id: str = None
    ) -> Dict[str, Any]:
        """Record technician diagnostic and repair actions"""
        ticket_query = {"ticket_id": data.ticket_id}
        if org_id:
            ticket_query["organization_id"] = org_id
        ticket = await self.db.tickets.find_one(ticket_query, {"_id": 0})
        if not ticket:
            raise ValueError(f"Ticket {data.ticket_id} not found")
        
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
        if org_id:
            doc['organization_id'] = org_id
        
        for diag in doc.get('attempted_diagnostics', []):
            if isinstance(diag.get('timestamp'), datetime):
                diag['timestamp'] = diag['timestamp'].isoformat()
        for hyp in doc.get('rejected_hypotheses', []):
            if isinstance(hyp.get('ruled_out_at'), datetime):
                hyp['ruled_out_at'] = hyp['ruled_out_at'].isoformat()
        
        await self.db.technician_actions.insert_one(doc)
        doc.pop("_id", None)
        
        # EMIT ACTION_COMPLETED EVENT
        await self.dispatcher.emit(
            EventType.ACTION_COMPLETED,
            {
                "action_id": action.action_id,
                "ticket_id": data.ticket_id,
                "outcome": data.resolution_outcome,
                "card_used": data.failure_card_used
            },
            source="efi_service",
            user_id=technician_id
        )
        
        # Update failure card metrics if used
        if data.failure_card_used:
            update_query = {"$inc": {"usage_count": 1}}
            if data.resolution_outcome == "success":
                update_query["$inc"]["success_count"] = 1
            elif data.resolution_outcome == "failed":
                update_query["$inc"]["failure_count"] = 1
            
            await self.db.failure_cards.update_one(
                {"failure_id": data.failure_card_used},
                update_query
            )
            
            # EMIT FAILURE_CARD_USED EVENT
            await self.dispatcher.emit(
                EventType.FAILURE_CARD_USED,
                {
                    "failure_id": data.failure_card_used,
                    "ticket_id": data.ticket_id,
                    "outcome": data.resolution_outcome,
                    "helpful": data.failure_card_helpful,
                    "rating": data.failure_card_accuracy_rating
                },
                source="efi_service",
                user_id=technician_id
            )
        
        # Handle new failure discovery
        if data.new_failure_discovered:
            await self.dispatcher.emit(
                EventType.NEW_FAILURE_DETECTED,
                {
                    "action_id": action.action_id,
                    "ticket_id": data.ticket_id,
                    "description": data.new_failure_description,
                    "root_cause": data.new_failure_root_cause,
                    "resolution": data.new_failure_resolution,
                    "technician_id": technician_id
                },
                source="efi_service",
                user_id=technician_id,
                priority=EventPriority.HIGH
            )
        
        logger.info(f"Recorded technician action {action.action_id}")
        
        return action.model_dump()
    
    # ==================== PART USAGE ====================
    
    async def record_part_usage(self, data: PartUsageCreate, org_id: str = None) -> Dict[str, Any]:
        """Record part usage with failure card linkage"""
        ticket_query = {"ticket_id": data.ticket_id}
        if org_id:
            ticket_query["organization_id"] = org_id
        ticket = await self.db.tickets.find_one(ticket_query, {"_id": 0})
        if not ticket:
            raise ValueError(f"Ticket {data.ticket_id} not found")
        
        part_query = {"item_id": data.part_id}
        if org_id:
            part_query["organization_id"] = org_id
        part = await self.db.inventory.find_one(part_query, {"_id": 0})
        if not part:
            raise ValueError(f"Part {data.part_id} not found")
        
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
        
        await self.db.part_usage.insert_one(doc)
        
        # Update inventory
        await self.db.inventory.update_one(
            {"item_id": data.part_id},
            {"$inc": {"quantity": -data.quantity_used}}
        )
        
        return usage.model_dump()
    
    # ==================== ANALYTICS ====================
    
    async def get_analytics_overview(self) -> Dict[str, Any]:
        """Get EFI system analytics"""
        # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1D
        total_cards = await self.db.failure_cards.count_documents({})
        approved_cards = await self.db.failure_cards.count_documents({"status": "approved"})
        draft_cards = await self.db.failure_cards.count_documents({"status": "draft"})
        
        top_cards = await self.db.failure_cards.find(
            {"status": "approved", "usage_count": {"$gt": 0}},
            {"_id": 0, "failure_id": 1, "title": 1, "effectiveness_score": 1, "usage_count": 1, "confidence_score": 1}
        ).sort("effectiveness_score", -1).limit(5).to_list(5)
        
        subsystem_pipeline = [
            {"$group": {"_id": "$subsystem_category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_subsystem = await self.db.failure_cards.aggregate(subsystem_pipeline).to_list(20)
        
        source_pipeline = [
            {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_source = await self.db.failure_cards.aggregate(source_pipeline).to_list(10)
        
        total_matches = await self.db.efi_events.count_documents({"event_type": "match.completed"})
        pending_patterns = await self.db.emerging_patterns.count_documents({"status": "detected"})
        
        recent_events = await self.db.efi_events.find(
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


# ==================== SERVICE FACTORY ====================

_efi_service: Optional[EFIService] = None


def get_efi_service() -> EFIService:
    """Get the EFI service singleton"""
    if _efi_service is None:
        raise ValueError("EFI Service not initialized")
    return _efi_service


def init_efi_service(db, event_processor=None) -> EFIService:
    """Initialize the EFI service with database"""
    global _efi_service
    _efi_service = EFIService(db, event_processor)
    return _efi_service
