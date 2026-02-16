"""
Battwheels OS - Failure Intelligence Event Handlers
Handles EFI-specific events for failure card lifecycle

Event Flow:
NEW_FAILURE_DETECTED -> Auto-create draft failure card
FAILURE_CARD_APPROVED -> Sync to network, boost confidence
FAILURE_CARD_USED -> Track usage, update last_used_at
"""
from typing import Dict, Any
from datetime import datetime, timezone
import uuid
import logging

from events.event_dispatcher import (
    EventType, EventPriority, Event,
    get_dispatcher, EventDispatcher
)

logger = logging.getLogger(__name__)


def register_failure_handlers(dispatcher: EventDispatcher, db):
    """
    Register all failure intelligence event handlers
    """
    
    @dispatcher.on(EventType.NEW_FAILURE_DETECTED, priority=EventPriority.HIGH)
    async def handle_new_failure_detected(event: Event):
        """
        When technician marks undocumented issue:
        1. Extract observations from TechnicianAction
        2. Extract vehicle/symptom info from Ticket
        3. Create DRAFT FailureCard
        4. Queue for expert review
        """
        action_id = event.data.get("action_id")
        ticket_id = event.data.get("ticket_id")
        description = event.data.get("description")
        root_cause = event.data.get("root_cause")
        resolution = event.data.get("resolution")
        technician_id = event.data.get("technician_id")
        
        if not ticket_id:
            logger.warning("NEW_FAILURE_DETECTED missing ticket_id")
            return {"skipped": "missing_ticket_id"}
        
        logger.info(f"Creating draft failure card from ticket {ticket_id}")
        
        # Get ticket details
        ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
        if not ticket:
            return {"skipped": "ticket_not_found"}
        
        # Get action if available
        action = None
        if action_id:
            action = await db.technician_actions.find_one({"action_id": action_id}, {"_id": 0})
        
        # Build draft card
        failure_id = f"fc_{uuid.uuid4().hex[:12]}"
        
        # Infer subsystem
        subsystem = infer_subsystem(ticket.get("category", "other"))
        
        # Extract keywords
        keywords = extract_keywords(
            f"{description or ''} {ticket.get('description', '')} {root_cause or ''}"
        )
        
        # Build failure signature
        signature = {
            "primary_symptoms": keywords[:5],
            "error_codes": ticket.get("error_codes_reported", []),
            "subsystem": subsystem,
            "failure_mode": "unknown"
        }
        signature_hash = compute_signature_hash(signature)
        
        draft_card = {
            "failure_id": failure_id,
            "title": f"[DRAFT] {description or 'New Undocumented Issue'}"[:150],
            "description": action.get("observations", [])[:500] if action else description,
            "subsystem_category": subsystem,
            "failure_mode": "unknown",
            
            # Signature
            "failure_signature": signature,
            "signature_hash": signature_hash,
            
            # Symptoms
            "symptom_text": description or ticket.get("description"),
            "symptom_codes": [],
            "error_codes": ticket.get("error_codes_reported", []),
            
            # Root cause
            "root_cause": root_cause or "Under Investigation",
            "root_cause_details": action.get("technician_notes") if action else None,
            "secondary_causes": [],
            
            # Resolution
            "resolution_steps": [{
                "step_number": 1,
                "action": resolution or "Resolution pending expert review",
                "duration_minutes": 30
            }] if resolution else [],
            "resolution_summary": resolution,
            
            # Parts used (from action)
            "required_parts": action.get("parts_used", []) if action else [],
            
            # Vehicle
            "vehicle_models": [{
                "make": ticket.get("vehicle_make", "Unknown"),
                "model": ticket.get("vehicle_model", "Unknown"),
                "variants": []
            }] if ticket.get("vehicle_make") else [],
            
            # Keywords
            "keywords": keywords,
            "tags": ["auto-generated", "needs-review"],
            
            # Intelligence metrics - low initial confidence
            "confidence_score": 0.3,
            "confidence_level": "low",
            "confidence_history": [{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_score": 0.0,
                "new_score": 0.3,
                "change_reason": "auto_creation",
                "ticket_id": ticket_id,
                "technician_id": technician_id,
                "notes": "Auto-generated from NEW_FAILURE_DETECTED event"
            }],
            
            # Provenance
            "source_type": "field_discovery",
            "source_ticket_id": ticket_id,
            "source_garage_id": ticket.get("garage_id"),
            "created_by": technician_id,
            
            # Status
            "status": "draft",
            "version": 1,
            
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "first_detected_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Insert card
        await db.failure_cards.insert_one(draft_card)
        
        logger.info(f"Created draft failure card {failure_id} from ticket {ticket_id}")
        
        # Emit card created event
        await dispatcher.emit(
            EventType.FAILURE_CARD_CREATED,
            {
                "failure_id": failure_id,
                "status": "draft",
                "source_ticket_id": ticket_id,
                "needs_expert_review": True,
                "auto_generated": True
            },
            source="failure_events",
            correlation_id=event.correlation_id
        )
        
        return {"draft_card_created": failure_id}
    
    @dispatcher.on(EventType.FAILURE_CARD_APPROVED, priority=EventPriority.NORMAL)
    async def handle_failure_card_approved(event: Event):
        """
        When failure card is approved:
        1. Boost confidence score
        2. Update status and timestamps
        3. Trigger network sync
        """
        failure_id = event.data.get("failure_id")
        approved_by = event.data.get("approved_by")
        
        if not failure_id:
            return {"skipped": "missing_failure_id"}
        
        logger.info(f"Processing approval for failure card {failure_id}")
        
        # Get current card
        card = await db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
        if not card:
            return {"skipped": "card_not_found"}
        
        # Boost confidence on approval
        old_confidence = card.get("confidence_score", 0.5)
        new_confidence = min(1.0, old_confidence + 0.2)
        
        # Update confidence level
        if new_confidence >= 0.9:
            confidence_level = "verified"
        elif new_confidence >= 0.7:
            confidence_level = "high"
        else:
            confidence_level = "medium"
        
        # Build history entry
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_score": old_confidence,
            "new_score": new_confidence,
            "change_reason": "expert_approval",
            "notes": f"Approved by {approved_by or 'expert'}"
        }
        
        # Update card
        await db.failure_cards.update_one(
            {"failure_id": failure_id},
            {
                "$set": {
                    "status": "approved",
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "approved_by": approved_by,
                    "confidence_score": new_confidence,
                    "confidence_level": confidence_level,
                    "synced_to_network": True,
                    "last_sync_at": datetime.now(timezone.utc).isoformat()
                },
                "$push": {
                    "confidence_history": history_entry
                }
            }
        )
        
        logger.info(f"Approved card {failure_id}: confidence {old_confidence:.2f} -> {new_confidence:.2f}")
        
        # Emit confidence updated
        await dispatcher.emit(
            EventType.CONFIDENCE_UPDATED,
            {
                "failure_id": failure_id,
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "change_reason": "expert_approval"
            },
            source="failure_events",
            correlation_id=event.correlation_id
        )
        
        return {"approved": True, "new_confidence": new_confidence}
    
    @dispatcher.on(EventType.FAILURE_CARD_USED, priority=EventPriority.LOW)
    async def handle_failure_card_used(event: Event):
        """
        When failure card is used by technician:
        1. Update last_used_at
        2. Optionally increment view count
        """
        failure_id = event.data.get("failure_id")
        ticket_id = event.data.get("ticket_id")
        
        if not failure_id:
            return {"skipped": "missing_failure_id"}
        
        await db.failure_cards.update_one(
            {"failure_id": failure_id},
            {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"tracked": True}
    
    @dispatcher.on(EventType.FAILURE_CARD_CREATED, priority=EventPriority.NORMAL)
    async def handle_failure_card_created_notification(event: Event):
        """
        When new failure card is created:
        1. If draft, add to expert review queue
        2. Log creation
        """
        failure_id = event.data.get("failure_id")
        needs_review = event.data.get("needs_expert_review", False)
        
        if needs_review:
            logger.info(f"New draft card {failure_id} added to expert review queue")
            # Could trigger notification to experts here
        
        return {"logged": True}
    
    logger.info("Failure event handlers registered")


# ==================== HELPER FUNCTIONS ====================

def infer_subsystem(category: str) -> str:
    """Infer subsystem category from ticket category"""
    mapping = {
        "battery": "battery",
        "motor": "motor",
        "charging": "charger",
        "electrical": "wiring",
        "display": "display",
        "brakes": "brakes",
        "software": "software",
        "controller": "controller",
        "bms": "bms",
    }
    return mapping.get(category.lower(), "other")


def extract_keywords(text: str) -> list:
    """Extract keywords from text"""
    if not text:
        return []
    
    import re
    
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall',
        'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
        'by', 'from', 'as', 'into', 'through', 'and', 'or', 'but'
    }
    
    words = re.findall(r'[a-z]+', text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in stopwords]
    
    return list(dict.fromkeys(keywords))[:20]


def compute_signature_hash(signature: dict) -> str:
    """Compute signature hash"""
    import hashlib
    
    components = [
        ",".join(sorted(signature.get("primary_symptoms", []))),
        ",".join(sorted(signature.get("error_codes", []))),
        signature.get("subsystem", ""),
        signature.get("failure_mode", "")
    ]
    hash_input = "|".join(components).lower()
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
