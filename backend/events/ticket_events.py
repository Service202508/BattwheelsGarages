"""
Battwheels OS - Ticket Event Handlers
Handles all ticket-related events and triggers EFI workflows

Event Flow:
TICKET_CREATED -> AI Matching -> Populate suggested_failure_cards
TICKET_UPDATED -> Track changes -> Notify if priority changed
TICKET_CLOSED -> Confidence Engine -> Update failure card metrics
"""
from typing import Dict, Any
from datetime import datetime, timezone
import logging

from events.event_dispatcher import (
    EventType, EventPriority, Event, 
    get_dispatcher, EventDispatcher
)

logger = logging.getLogger(__name__)


def register_ticket_handlers(dispatcher: EventDispatcher, db, ai_matcher=None):
    """
    Register all ticket event handlers
    
    Call this during server startup to wire event handlers
    """
    
    @dispatcher.on(EventType.TICKET_CREATED, priority=EventPriority.HIGH)
    async def handle_ticket_created_ai_matching(event: Event):
        """
        When TICKET_CREATED:
        1. Trigger AI matching service
        2. Populate suggested_failure_cards
        3. Emit MATCH_COMPLETED event
        """
        ticket_id = event.data.get("ticket_id")
        if not ticket_id:
            logger.warning("TICKET_CREATED event missing ticket_id")
            return
        
        logger.info(f"Processing TICKET_CREATED for AI matching: {ticket_id}")
        
        # Get ticket details
        ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
        if not ticket:
            logger.error(f"Ticket not found: {ticket_id}")
            return
        
        # Build match request
        symptom_text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
        error_codes = ticket.get("error_codes_reported", [])
        vehicle_make = ticket.get("vehicle_make")
        vehicle_model = ticket.get("vehicle_model")
        
        # Perform AI matching
        matches = await perform_ai_matching(
            db=db,
            symptom_text=symptom_text,
            error_codes=error_codes,
            vehicle_make=vehicle_make,
            vehicle_model=vehicle_model,
            limit=5
        )
        
        # Update ticket with suggestions
        if matches:
            suggested_ids = [m["failure_id"] for m in matches]
            await db.tickets.update_one(
                {"ticket_id": ticket_id},
                {"$set": {
                    "suggested_failure_cards": suggested_ids,
                    "ai_match_performed": True,
                    "ai_match_timestamp": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            logger.info(f"Matched ticket {ticket_id} to {len(matches)} failure cards")
            
            # Emit match completed event
            await dispatcher.emit(
                EventType.MATCH_COMPLETED,
                {
                    "ticket_id": ticket_id,
                    "matches_count": len(matches),
                    "top_match": matches[0]["failure_id"] if matches else None,
                    "top_score": matches[0]["match_score"] if matches else 0
                },
                source="ticket_events",
                correlation_id=event.correlation_id
            )
        
        return {"matches_found": len(matches)}
    
    @dispatcher.on(EventType.TICKET_STATUS_CHANGED, priority=EventPriority.NORMAL)
    async def handle_ticket_status_change(event: Event):
        """
        When ticket status changes:
        1. Log status change
        2. Trigger notifications if needed
        3. If resolved/closed, trigger confidence update
        """
        ticket_id = event.data.get("ticket_id")
        old_status = event.data.get("old_status")
        new_status = event.data.get("new_status")
        
        logger.info(f"Ticket {ticket_id} status changed: {old_status} -> {new_status}")
        
        # If resolved or closed, trigger confidence update
        if new_status in ["resolved", "closed"]:
            await dispatcher.emit(
                EventType.TICKET_CLOSED if new_status == "closed" else EventType.TICKET_RESOLVED,
                {"ticket_id": ticket_id, "status": new_status},
                source="ticket_events",
                correlation_id=event.correlation_id
            )
        
        return {"status_tracked": True}
    
    @dispatcher.on(EventType.TICKET_CLOSED, EventType.TICKET_RESOLVED, priority=EventPriority.NORMAL)
    async def handle_ticket_closed_confidence_update(event: Event):
        """
        When TICKET_CLOSED:
        1. Get linked technician action
        2. Determine success/failure
        3. Update failure card confidence
        4. Update effectiveness metrics
        """
        ticket_id = event.data.get("ticket_id")
        if not ticket_id:
            return
        
        logger.info(f"Processing ticket closure for confidence update: {ticket_id}")
        
        # Get technician action
        action = await db.technician_actions.find_one(
            {"ticket_id": ticket_id},
            {"_id": 0}
        )
        
        if not action:
            logger.debug(f"No technician action for ticket {ticket_id}")
            return {"skipped": "no_action"}
        
        failure_card_id = action.get("failure_card_used")
        if not failure_card_id:
            logger.debug(f"No failure card used in ticket {ticket_id}")
            return {"skipped": "no_card_used"}
        
        # Get current card
        card = await db.failure_cards.find_one(
            {"failure_id": failure_card_id},
            {"_id": 0}
        )
        
        if not card:
            return {"skipped": "card_not_found"}
        
        # Determine success
        is_success = (
            action.get("resolution_outcome") == "success" and
            not action.get("new_failure_discovered", False)
        )
        
        # Calculate new metrics
        old_confidence = card.get("confidence_score", 0.5)
        usage_count = card.get("usage_count", 0) + 1
        success_count = card.get("success_count", 0) + (1 if is_success else 0)
        failure_count = card.get("failure_count", 0) + (0 if is_success else 1)
        
        # Update confidence
        if is_success:
            new_confidence = min(1.0, old_confidence + 0.01)
            change_reason = "success_outcome"
        else:
            new_confidence = max(0.0, old_confidence - 0.02)
            change_reason = "failure_outcome"
        
        # Calculate effectiveness
        effectiveness = (success_count / usage_count) + min(0.1, usage_count / 100)
        
        # Determine confidence level
        if new_confidence >= 0.9:
            confidence_level = "verified"
        elif new_confidence >= 0.7:
            confidence_level = "high"
        elif new_confidence >= 0.4:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Build history entry
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_score": old_confidence,
            "new_score": new_confidence,
            "change_reason": change_reason,
            "ticket_id": ticket_id,
            "technician_id": action.get("technician_id"),
            "notes": f"Usage #{usage_count}, {'Success' if is_success else 'Failure'}"
        }
        
        # Update card
        await db.failure_cards.update_one(
            {"failure_id": failure_card_id},
            {
                "$set": {
                    "usage_count": usage_count,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "effectiveness_score": effectiveness,
                    "confidence_score": new_confidence,
                    "confidence_level": confidence_level,
                    "last_used_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$push": {
                    "confidence_history": history_entry
                }
            }
        )
        
        logger.info(
            f"Updated card {failure_card_id}: confidence {old_confidence:.2f} -> {new_confidence:.2f}"
        )
        
        # Emit confidence updated event
        await dispatcher.emit(
            EventType.CONFIDENCE_UPDATED,
            {
                "failure_id": failure_card_id,
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "change_reason": change_reason,
                "effectiveness": effectiveness
            },
            source="ticket_events",
            correlation_id=event.correlation_id
        )
        
        return {
            "card_updated": failure_card_id,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence
        }
    
    logger.info("Ticket event handlers registered")


async def perform_ai_matching(
    db,
    symptom_text: str,
    error_codes: list = None,
    vehicle_make: str = None,
    vehicle_model: str = None,
    limit: int = 5
) -> list:
    """
    Perform 4-stage AI matching pipeline
    
    Priority order (per EFI architecture):
    1. Failure signature match
    2. Subsystem + vehicle filtering
    3. Semantic similarity
    4. Keyword fallback
    """
    import hashlib
    import re
    
    error_codes = error_codes or []
    all_matches = []
    
    def extract_keywords(text: str) -> list:
        """Extract symptom keywords"""
        if not text:
            return []
        indicators = [
            "not", "no", "fail", "error", "issue", "problem", "slow", "fast",
            "hot", "cold", "noise", "vibration", "charging", "battery", "motor",
            "display", "brake", "smoke", "burn", "leak", "stuck", "loose"
        ]
        words = text.lower().split()
        keywords = []
        for word in words:
            for indicator in indicators:
                if indicator in word:
                    keywords.append(word)
                    break
        return list(set(keywords))[:10]
    
    def compute_signature_hash(symptoms: list, codes: list, subsystem: str = "") -> str:
        """Compute signature hash for fast matching"""
        components = [
            ",".join(sorted(symptoms)),
            ",".join(sorted(codes)),
            subsystem
        ]
        hash_input = "|".join(components).lower()
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    # Extract keywords and compute signature
    keywords = extract_keywords(symptom_text)
    signature_hash = compute_signature_hash(keywords, error_codes)
    
    # Stage 1: Signature match (fastest)
    try:
        sig_matches = await db.failure_cards.find(
            {"signature_hash": signature_hash, "status": {"$in": ["approved", "draft"]}},
            {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, "effectiveness_score": 1}
        ).limit(5).to_list(5)
        
        for card in sig_matches:
            all_matches.append({
                "failure_id": card["failure_id"],
                "title": card["title"],
                "match_score": 0.95,
                "match_type": "signature",
                "confidence_score": card.get("confidence_score", 0.5)
            })
    except Exception as e:
        logger.warning(f"Signature match failed: {e}")
    
    # Stage 2: Subsystem + vehicle filtering
    if not all_matches or all_matches[0].get("match_score", 0) < 0.9:
        try:
            query = {"status": {"$in": ["approved", "draft"]}}
            
            cards = await db.failure_cards.find(
                query,
                {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1,
                 "effectiveness_score": 1, "vehicle_models": 1, "error_codes": 1}
            ).limit(20).to_list(20)
            
            for card in cards:
                if card["failure_id"] in [m["failure_id"] for m in all_matches]:
                    continue
                
                score = 0.5
                
                # Error code match
                card_codes = set(card.get("error_codes", []))
                query_codes = set(error_codes)
                if card_codes & query_codes:
                    score += 0.2 * (len(card_codes & query_codes) / max(len(query_codes), 1))
                
                # Vehicle match
                if vehicle_make:
                    for vm in card.get("vehicle_models", []):
                        if vm.get("make", "").lower() == vehicle_make.lower():
                            score += 0.15
                            if vehicle_model and vm.get("model", "").lower() == vehicle_model.lower():
                                score += 0.1
                            break
                
                if score > 0.4:
                    all_matches.append({
                        "failure_id": card["failure_id"],
                        "title": card["title"],
                        "match_score": min(0.85, score),
                        "match_type": "subsystem_vehicle",
                        "confidence_score": card.get("confidence_score", 0.5)
                    })
        except Exception as e:
            logger.warning(f"Subsystem match failed: {e}")
    
    # Stage 3: Semantic similarity (keyword overlap)
    if not all_matches or all_matches[0].get("match_score", 0) < 0.7:
        try:
            if keywords:
                cards = await db.failure_cards.find(
                    {
                        "status": {"$in": ["approved", "draft"]},
                        "$or": [
                            {"keywords": {"$in": keywords}},
                            {"symptom_text": {"$regex": "|".join(keywords[:5]), "$options": "i"}}
                        ]
                    },
                    {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, "keywords": 1}
                ).limit(10).to_list(10)
                
                for card in cards:
                    if card["failure_id"] in [m["failure_id"] for m in all_matches]:
                        continue
                    
                    card_keywords = set(card.get("keywords", []))
                    query_keywords = set(keywords)
                    overlap = len(card_keywords & query_keywords)
                    score = min(0.7, 0.3 + (overlap * 0.08))
                    
                    if score > 0.35:
                        all_matches.append({
                            "failure_id": card["failure_id"],
                            "title": card["title"],
                            "match_score": score,
                            "match_type": "semantic",
                            "confidence_score": card.get("confidence_score", 0.5)
                        })
        except Exception as e:
            logger.warning(f"Semantic match failed: {e}")
    
    # Stage 4: Text search fallback
    if not all_matches or all_matches[0].get("match_score", 0) < 0.5:
        try:
            cards = await db.failure_cards.find(
                {
                    "status": {"$in": ["approved", "draft"]},
                    "$text": {"$search": symptom_text}
                },
                {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, "score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(5).to_list(5)
            
            for card in cards:
                if card["failure_id"] in [m["failure_id"] for m in all_matches]:
                    continue
                
                all_matches.append({
                    "failure_id": card["failure_id"],
                    "title": card["title"],
                    "match_score": min(0.5, card.get("score", 0) / 10),
                    "match_type": "keyword",
                    "confidence_score": card.get("confidence_score", 0.5)
                })
        except Exception as e:
            logger.debug(f"Text search fallback failed: {e}")
    
    # Sort by score
    all_matches.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    return all_matches[:limit]
