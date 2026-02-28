"""
Battwheels OS - EFI Event Processor Service
Handles all event-driven workflows for the Failure Intelligence system

Workflows:
1. Ticket Created → AI Similarity Matching
2. Technician Marks Undocumented Issue → Auto-Create Draft Card
3. Ticket Closure → Update Confidence Score
4. Emerging Pattern Detection (Scheduled)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
import hashlib

from models.failure_intelligence import (
    EFIEvent, EFIEventType, FailureCard, FailureCardStatus,
    ConfidenceLevel, ConfidenceChangeEvent, SourceType,
    FailureSignature, FailureMatchRequest, EmergingPattern,
    SubsystemCategory
)

logger = logging.getLogger(__name__)


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
    
    success_rate = success_count / usage_count
    usage_bonus = min(0.1, usage_count / 100)
    
    return min(1.0, success_rate + usage_bonus)


class EFIEventProcessor:
    """
    Central event processor for EFI workflows
    AI assists ranking. Human-approved FAILURE_CARD remains source of truth.
    """
    
    def __init__(self, db, ai_matcher=None):
        self.db = db
        self.ai_matcher = ai_matcher
        
        self.handlers = {
            EFIEventType.TICKET_CREATED.value: self.handle_ticket_created,
            EFIEventType.TICKET_RESOLVED.value: self.handle_ticket_resolved,
            EFIEventType.ACTION_COMPLETED.value: self.handle_action_completed,
            EFIEventType.NEW_FAILURE_DISCOVERED.value: self.handle_new_failure_discovered,
            EFIEventType.CARD_APPROVED.value: self.handle_card_approved,
            EFIEventType.CARD_USED.value: self.handle_card_used,
            EFIEventType.PATTERN_DETECTED.value: self.handle_pattern_detected,
        }
    
    async def process_event(self, event: dict) -> Dict[str, Any]:
        """Route event to appropriate handler"""
        event_type = event.get("event_type")
        handler = self.handlers.get(event_type)
        
        if not handler:
            logger.warning(f"No handler for event type: {event_type}")
            return {"status": "skipped", "reason": "no_handler"}
        
        try:
            result = await handler(event)
            await self.mark_processed(event, result)
            return result
        except Exception as e:
            logger.error(f"Error processing event {event.get('event_id')}: {e}")
            await self.mark_error(event, str(e))
            return {"status": "error", "error": str(e)}
    
    async def mark_processed(self, event: dict, result: dict):
        """Mark event as successfully processed"""
        filter_q = {"event_id": event["event_id"]}
        if event.get("organization_id"):
            filter_q["organization_id"] = event["organization_id"]  # TIER 1: org-scoped — Sprint 1C
        await self.db.efi_events.update_one(
            filter_q,
            {"$set": {
                "processed": True,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "processing_result": result
            }}
        )
    
    async def mark_error(self, event: dict, error: str):
        """Mark event as failed"""
        retry_count = event.get("retry_count", 0) + 1
        filter_q = {"event_id": event["event_id"]}
        if event.get("organization_id"):
            filter_q["organization_id"] = event["organization_id"]  # TIER 1: org-scoped — Sprint 1C
        await self.db.efi_events.update_one(
            filter_q,
            {"$set": {
                "error_message": error,
                "retry_count": retry_count,
                "processed": retry_count >= event.get("max_retries", 3)
            }}
        )
    
    # =====================================================================
    # WORKFLOW 1: Ticket Created → Trigger AI Similarity Matching
    # =====================================================================
    
    async def handle_ticket_created(self, event: dict) -> Dict[str, Any]:
        """
        When a ticket is created:
        1. Extract symptoms, error codes, vehicle info
        2. Build failure signature
        3. Run 4-stage AI matching pipeline
        4. Update ticket with suggested_failure_cards
        """
        ticket_id = event["data"].get("ticket_id")
        if not ticket_id:
            return {"status": "error", "reason": "no_ticket_id"}
        
        # TIER 1: Extract org_id from event — Sprint 1C
        org_id = event.get("organization_id") or event["data"].get("organization_id")
        
        ticket_query = {"ticket_id": ticket_id}
        if org_id:
            ticket_query["organization_id"] = org_id
        ticket = await self.db.tickets.find_one(ticket_query, {"_id": 0})
        if not ticket:
            return {"status": "error", "reason": "ticket_not_found"}
        
        # Build failure signature for matching
        signature = self._build_failure_signature(ticket)
        signature_hash = self._compute_signature_hash(signature)
        
        # Stage 1: Signature match (fastest, highest confidence)
        matches = await self._match_by_signature(signature_hash)
        
        if not matches or matches[0].get("match_score", 0) < 0.95:
            # Stage 2: Subsystem + Vehicle filtering
            stage2_matches = await self._match_by_subsystem_vehicle(ticket)
            matches = self._merge_matches(matches, stage2_matches)
        
        if not matches or matches[0].get("match_score", 0) < 0.8:
            # Stage 3: Semantic similarity
            stage3_matches = await self._match_by_semantic(ticket)
            matches = self._merge_matches(matches, stage3_matches)
        
        if not matches or matches[0].get("match_score", 0) < 0.5:
            # Stage 4: Keyword fallback
            stage4_matches = await self._match_by_keyword(ticket)
            matches = self._merge_matches(matches, stage4_matches)
        
        # Sort by score and take top 5
        matches.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        top_matches = matches[:5]
        
        # Update ticket with suggestions (TIER 1: org-scoped — Sprint 1C)
        ticket_update_filter = {"ticket_id": ticket_id}
        if org_id:
            ticket_update_filter["organization_id"] = org_id
        await self.db.tickets.update_one(
            ticket_update_filter,
            {"$set": {
                "suggested_failure_cards": [m["failure_id"] for m in top_matches],
                "ai_match_performed": True,
                "ai_match_timestamp": datetime.now(timezone.utc).isoformat(),
                "ai_match_signature_hash": signature_hash
            }}
        )
        
        # Emit match completed event (TIER 1: org-scoped — Sprint 1C)
        await self._emit_event(
            EFIEventType.MATCH_COMPLETED.value,
            {
                "ticket_id": ticket_id,
                "matches_found": len(top_matches),
                "top_match_score": top_matches[0]["match_score"] if top_matches else 0
            },
            org_id=org_id
        )
        
        return {
            "status": "success",
            "matches_found": len(top_matches),
            "signature_hash": signature_hash
        }
    
    def _build_failure_signature(self, ticket: dict) -> dict:
        """Build failure signature from ticket data"""
        return {
            "primary_symptoms": self._extract_symptoms(ticket.get("description", "")),
            "error_codes": ticket.get("error_codes_reported", []),
            "subsystem": ticket.get("category", "other"),
            "failure_mode": "unknown",
            "vehicle_make": ticket.get("vehicle_make"),
            "vehicle_model": ticket.get("vehicle_model"),
        }
    
    def _compute_signature_hash(self, signature: dict) -> str:
        """Generate deterministic hash for signature matching"""
        components = [
            ",".join(sorted(signature.get("primary_symptoms", []))),
            ",".join(sorted(signature.get("error_codes", []))),
            signature.get("subsystem", ""),
            signature.get("failure_mode", ""),
        ]
        hash_input = "|".join(components).lower()
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Extract symptom keywords from text"""
        # Simple keyword extraction - would use NLP in production
        keywords = []
        symptom_indicators = [
            "not", "no", "fail", "error", "issue", "problem",
            "slow", "fast", "hot", "cold", "noise", "vibration",
            "charging", "battery", "motor", "display", "brake"
        ]
        words = text.lower().split()
        for word in words:
            for indicator in symptom_indicators:
                if indicator in word:
                    keywords.append(word)
                    break
        return list(set(keywords))[:10]
    
    async def _match_by_signature(self, signature_hash: str) -> List[dict]:
        """Stage 1: Direct signature hash match"""
        cards = await self.db.failure_cards.find(
            {"signature_hash": signature_hash, "status": "approved"},
            {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, "effectiveness_score": 1}
        ).to_list(5)
        
        return [{
            "failure_id": c["failure_id"],
            "title": c["title"],
            "match_score": 0.95,
            "match_type": "signature",
            "match_stage": 1,
            "confidence_level": calculate_confidence_level(c.get("confidence_score", 0.5)).value,
            "effectiveness_score": c.get("effectiveness_score", 0)
        } for c in cards]
    
    async def _match_by_subsystem_vehicle(self, ticket: dict) -> List[dict]:
        """Stage 2: Subsystem + vehicle filtering"""
        query = {"status": {"$in": ["approved", "draft"]}}
        
        if ticket.get("category"):
            query["subsystem_category"] = ticket["category"]
        
        cards = await self.db.failure_cards.find(
            query,
            {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, 
             "effectiveness_score": 1, "vehicle_models": 1, "subsystem_category": 1}
        ).limit(20).to_list(20)
        
        matches = []
        for card in cards:
            score = 0.5  # Base score
            
            # Boost for vehicle match
            if ticket.get("vehicle_make"):
                for vm in card.get("vehicle_models", []):
                    if vm.get("make", "").lower() == ticket["vehicle_make"].lower():
                        score += 0.2
                        if ticket.get("vehicle_model") and vm.get("model", "").lower() == ticket["vehicle_model"].lower():
                            score += 0.1
                        break
            
            matches.append({
                "failure_id": card["failure_id"],
                "title": card["title"],
                "match_score": min(0.8, score),
                "match_type": "subsystem_vehicle",
                "match_stage": 2,
                "confidence_level": calculate_confidence_level(card.get("confidence_score", 0.5)).value,
                "effectiveness_score": card.get("effectiveness_score", 0)
            })
        
        return matches
    
    async def _match_by_semantic(self, ticket: dict) -> List[dict]:
        """Stage 3: Semantic similarity (simplified - would use embeddings)"""
        query_text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
        keywords = self._extract_symptoms(query_text)
        
        if not keywords:
            return []
        
        cards = await self.db.failure_cards.find(
            {
                "status": {"$in": ["approved", "draft"]},
                "$or": [
                    {"keywords": {"$in": keywords}},
                    {"symptom_text": {"$regex": "|".join(keywords), "$options": "i"}}
                ]
            },
            {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1,
             "effectiveness_score": 1, "keywords": 1, "symptom_text": 1}
        ).limit(10).to_list(10)
        
        matches = []
        for card in cards:
            # Calculate keyword overlap
            card_keywords = set(card.get("keywords", []))
            query_keywords = set(keywords)
            overlap = len(card_keywords & query_keywords)
            score = min(0.7, 0.3 + (overlap * 0.1))
            
            matches.append({
                "failure_id": card["failure_id"],
                "title": card["title"],
                "match_score": score,
                "match_type": "semantic",
                "match_stage": 3,
                "confidence_level": calculate_confidence_level(card.get("confidence_score", 0.5)).value,
                "effectiveness_score": card.get("effectiveness_score", 0)
            })
        
        return matches
    
    async def _match_by_keyword(self, ticket: dict) -> List[dict]:
        """Stage 4: Keyword fallback"""
        query_text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
        
        cards = await self.db.failure_cards.find(
            {
                "status": {"$in": ["approved", "draft"]},
                "$text": {"$search": query_text}
            },
            {"_id": 0, "failure_id": 1, "title": 1, "confidence_score": 1, 
             "effectiveness_score": 1, "score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(5).to_list(5)
        
        return [{
            "failure_id": c["failure_id"],
            "title": c["title"],
            "match_score": min(0.5, c.get("score", 0) / 10),
            "match_type": "keyword",
            "match_stage": 4,
            "confidence_level": calculate_confidence_level(c.get("confidence_score", 0.5)).value,
            "effectiveness_score": c.get("effectiveness_score", 0)
        } for c in cards]
    
    def _merge_matches(self, existing: List[dict], new: List[dict]) -> List[dict]:
        """Merge match lists, keeping highest score per card"""
        seen_ids = {m["failure_id"]: m for m in existing}
        
        for match in new:
            fid = match["failure_id"]
            if fid not in seen_ids or seen_ids[fid]["match_score"] < match["match_score"]:
                seen_ids[fid] = match
        
        return list(seen_ids.values())
    
    # =====================================================================
    # WORKFLOW 2: Technician Marks Undocumented Issue → Auto-Create Draft Card
    # =====================================================================
    
    async def handle_new_failure_discovered(self, event: dict) -> Dict[str, Any]:
        """
        When technician marks new_failure_discovered = true:
        1. Extract observations from TechnicianAction
        2. Extract vehicle/symptom info from Ticket
        3. Create DRAFT FailureCard (status=draft, confidence=0.3)
        4. Queue for expert review
        """
        action_id = event["data"].get("action_id")
        ticket_id = event["data"].get("ticket_id")
        
        if not action_id or not ticket_id:
            return {"status": "error", "reason": "missing_ids"}
        
        action = await self.db.technician_actions.find_one({"action_id": action_id}, {"_id": 0})
        ticket = await self.db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
        
        if not action or not ticket:
            return {"status": "error", "reason": "records_not_found"}
        
        # Build draft card from action and ticket data
        import uuid
        failure_id = f"fc_{uuid.uuid4().hex[:12]}"
        
        # Infer subsystem from ticket category
        subsystem = self._infer_subsystem(ticket.get("category", "other"))
        
        # Build failure signature
        signature = FailureSignature(
            primary_symptoms=self._extract_symptoms(action.get("new_failure_description", "")),
            error_codes=ticket.get("error_codes_reported", []),
            subsystem=subsystem,
            failure_mode="unknown"
        )
        signature_hash = signature.compute_hash()
        
        draft_card = {
            "failure_id": failure_id,
            "title": f"[DRAFT] {action.get('new_failure_description', 'New Undocumented Issue')[:100]}",
            "description": "\n".join(action.get("observations", [])),
            "subsystem_category": subsystem.value,
            "failure_mode": "unknown",
            
            # Signature
            "failure_signature": signature.model_dump(),
            "signature_hash": signature_hash,
            
            # Symptoms
            "symptom_text": action.get("new_failure_description"),
            "symptom_codes": [],
            "error_codes": ticket.get("error_codes_reported", []),
            
            # Root cause
            "root_cause": action.get("new_failure_root_cause", "Under Investigation"),
            "root_cause_details": action.get("technician_notes"),
            
            # Resolution
            "resolution_steps": [{
                "step_number": 1,
                "action": action.get("new_failure_resolution", "Resolution pending expert review"),
                "duration_minutes": 30
            }],
            "resolution_summary": action.get("new_failure_resolution"),
            
            # Parts
            "required_parts": action.get("parts_used", []),
            
            # Vehicle
            "vehicle_models": [{
                "make": ticket.get("vehicle_make", "Unknown"),
                "model": ticket.get("vehicle_model", "Unknown"),
                "variants": []
            }] if ticket.get("vehicle_make") else [],
            
            # Intelligence
            "confidence_score": 0.3,  # Low initial confidence
            "confidence_level": ConfidenceLevel.LOW.value,
            "confidence_history": [{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_score": 0.0,
                "new_score": 0.3,
                "change_reason": "initial_creation",
                "ticket_id": ticket_id,
                "technician_id": action.get("technician_id")
            }],
            
            # Keywords
            "keywords": self._extract_symptoms(
                f"{action.get('new_failure_description', '')} {ticket.get('description', '')}"
            ),
            
            # Provenance
            "source_type": SourceType.FIELD_DISCOVERY.value,
            "source_ticket_id": ticket_id,
            "source_garage_id": ticket.get("garage_id"),
            "created_by": action.get("technician_id"),
            
            # Status
            "status": FailureCardStatus.DRAFT.value,
            "version": 1,
            
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "first_detected_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.db.failure_cards.insert_one(draft_card)
        
        # Emit card created event
        await self._emit_event(
            EFIEventType.CARD_CREATED.value,
            {
                "failure_id": failure_id,
                "status": "draft",
                "source_ticket_id": ticket_id,
                "needs_expert_review": True
            },
            priority=3  # Higher priority for expert review queue
        )
        
        logger.info(f"Created draft failure card {failure_id} from ticket {ticket_id}")
        
        return {
            "status": "success",
            "draft_card_created": failure_id,
            "queued_for_review": True
        }
    
    def _infer_subsystem(self, category: str) -> SubsystemCategory:
        """Infer subsystem category from ticket category"""
        mapping = {
            "battery": SubsystemCategory.BATTERY,
            "motor": SubsystemCategory.MOTOR,
            "charging": SubsystemCategory.CHARGER,
            "electrical": SubsystemCategory.WIRING,
            "display": SubsystemCategory.DISPLAY,
            "brakes": SubsystemCategory.BRAKES,
            "software": SubsystemCategory.SOFTWARE,
        }
        return mapping.get(category.lower(), SubsystemCategory.OTHER)
    
    # =====================================================================
    # WORKFLOW 3: Ticket Closure → Update Failure Intelligence Confidence Score
    # =====================================================================
    
    async def handle_ticket_resolved(self, event: dict) -> Dict[str, Any]:
        """
        When ticket is resolved:
        1. Get linked TechnicianAction
        2. Determine success/failure
        3. Update FailureCard metrics
        4. Record in confidence_history
        """
        ticket_id = event["data"].get("ticket_id")
        if not ticket_id:
            return {"status": "error", "reason": "no_ticket_id"}
        
        # Get the technician action for this ticket
        action = await self.db.technician_actions.find_one(
            {"ticket_id": ticket_id},
            {"_id": 0}
        )
        
        if not action:
            return {"status": "skipped", "reason": "no_technician_action"}
        
        failure_card_id = action.get("failure_card_used")
        if not failure_card_id:
            return {"status": "skipped", "reason": "no_card_used"}
        
        # Get current card
        card = await self.db.failure_cards.find_one(
            {"failure_id": failure_card_id},
            {"_id": 0}
        )
        
        if not card:
            return {"status": "error", "reason": "card_not_found"}
        
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
        effectiveness = calculate_effectiveness(success_count, failure_count, usage_count)
        confidence_level = calculate_confidence_level(new_confidence)
        
        # Build confidence history entry
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
        await self.db.failure_cards.update_one(
            {"failure_id": failure_card_id},
            {
                "$set": {
                    "usage_count": usage_count,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "effectiveness_score": effectiveness,
                    "confidence_score": new_confidence,
                    "confidence_level": confidence_level.value,
                    "last_used_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$push": {
                    "confidence_history": history_entry
                }
            }
        )
        
        # Emit confidence updated event
        await self._emit_event(
            EFIEventType.CONFIDENCE_UPDATED.value,
            {
                "failure_id": failure_card_id,
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "change_reason": change_reason,
                "effectiveness": effectiveness
            }
        )
        
        logger.info(
            f"Updated card {failure_card_id}: confidence {old_confidence:.2f} → {new_confidence:.2f}"
        )
        
        return {
            "status": "success",
            "card_updated": failure_card_id,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "effectiveness": effectiveness
        }
    
    async def handle_action_completed(self, event: dict) -> Dict[str, Any]:
        """Handle technician action completion - update usage stats"""
        action_id = event["data"].get("action_id")
        # Additional processing for action completion
        return {"status": "success", "action_id": action_id}
    
    async def handle_card_used(self, event: dict) -> Dict[str, Any]:
        """Track when a card is used (viewed/selected by technician)"""
        failure_id = event["data"].get("failure_id")
        
        await self.db.failure_cards.update_one(
            {"failure_id": failure_id},
            {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"status": "success", "failure_id": failure_id}
    
    async def handle_card_approved(self, event: dict) -> Dict[str, Any]:
        """Handle card approval - trigger network sync"""
        failure_id = event["data"].get("failure_id")
        
        # Update card status
        await self.db.failure_cards.update_one(
            {"failure_id": failure_id},
            {"$set": {
                "status": FailureCardStatus.APPROVED.value,
                "approved_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Trigger sync event
        await self._emit_event(
            EFIEventType.SYNC_REQUESTED.value,
            {"failure_id": failure_id, "sync_type": "card_approved"}
        )
        
        return {"status": "success", "failure_id": failure_id}
    
    # =====================================================================
    # WORKFLOW 4: Emerging Pattern Detection (Scheduled)
    # =====================================================================
    
    async def detect_emerging_patterns(
        self,
        min_occurrences: int = 3,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Scheduled job: Detect emerging patterns that need expert review
        
        1. Find repeating symptoms without linked failure_card
        2. Find abnormal part replacement patterns
        3. Auto-flag for expert review
        """
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
        patterns_detected = []
        
        # Pattern 1: Repeating symptoms without linked failure card
        symptom_patterns = await self._detect_unlinked_symptom_clusters(
            cutoff_date, min_occurrences
        )
        patterns_detected.extend(symptom_patterns)
        
        # Pattern 2: Abnormal part replacement patterns
        part_patterns = await self._detect_part_anomalies(cutoff_date)
        patterns_detected.extend(part_patterns)
        
        # Store detected patterns
        for pattern in patterns_detected:
            await self.db.emerging_patterns.insert_one(pattern)
            
            # Emit event
            await self._emit_event(
                EFIEventType.PATTERN_DETECTED.value,
                {
                    "pattern_id": pattern["pattern_id"],
                    "pattern_type": pattern["pattern_type"],
                    "occurrence_count": pattern["occurrence_count"]
                },
                priority=4
            )
        
        logger.info(f"Pattern detection complete: {len(patterns_detected)} patterns found")
        return patterns_detected
    
    async def _detect_unlinked_symptom_clusters(
        self,
        cutoff_date: str,
        min_occurrences: int
    ) -> List[dict]:
        """Find tickets with similar symptoms but no linked failure card"""
        import uuid
        
        # Aggregate tickets without failure card suggestions
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": cutoff_date},
                    "$or": [
                        {"suggested_failure_cards": {"$exists": False}},
                        {"suggested_failure_cards": {"$size": 0}}
                    ]
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "tickets": {"$push": {
                        "ticket_id": "$ticket_id",
                        "description": "$description",
                        "vehicle_make": "$vehicle_make",
                        "vehicle_model": "$vehicle_model"
                    }}
                }
            },
            {"$match": {"count": {"$gte": min_occurrences}}}
        ]
        
        clusters = await self.db.tickets.aggregate(pipeline).to_list(50)
        
        patterns = []
        for cluster in clusters:
            pattern_id = f"pat_{uuid.uuid4().hex[:12]}"
            
            # Extract common symptoms
            descriptions = [t.get("description", "") for t in cluster["tickets"]]
            common_symptoms = self._find_common_keywords(descriptions)
            
            # Group by vehicle
            vehicle_counts = {}
            for t in cluster["tickets"]:
                key = f"{t.get('vehicle_make', 'Unknown')} {t.get('vehicle_model', 'Unknown')}"
                vehicle_counts[key] = vehicle_counts.get(key, 0) + 1
            
            patterns.append({
                "pattern_id": pattern_id,
                "pattern_type": "symptom_cluster",
                "description": f"Repeating {cluster['_id']} issues without documented solution",
                "detected_symptoms": common_symptoms,
                "affected_vehicles": [
                    {"make_model": k, "count": v}
                    for k, v in vehicle_counts.items()
                ],
                "occurrence_count": cluster["count"],
                "first_occurrence": cutoff_date,
                "last_occurrence": datetime.now(timezone.utc).isoformat(),
                "has_linked_failure_card": False,
                "confidence_score": min(0.9, cluster["count"] / 10),
                "status": "detected",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        return patterns
    
    async def _detect_part_anomalies(self, cutoff_date: str) -> List[dict]:
        """Find abnormal part replacement patterns"""
        import uuid
        
        # Find parts with unexpected_vs_actual = False
        pipeline = [
            {
                "$match": {
                    "allocated_at": {"$gte": cutoff_date},
                    "expected_vs_actual": False
                }
            },
            {
                "$group": {
                    "_id": "$part_id",
                    "count": {"$sum": 1},
                    "part_name": {"$first": "$part_name"},
                    "failure_cards": {"$addToSet": "$failure_card_id"},
                    "notes": {"$push": "$expectation_notes"}
                }
            },
            {"$match": {"count": {"$gte": 2}}}
        ]
        
        anomalies = await self.db.part_usage.aggregate(pipeline).to_list(50)
        
        patterns = []
        for anomaly in anomalies:
            pattern_id = f"pat_{uuid.uuid4().hex[:12]}"
            
            patterns.append({
                "pattern_id": pattern_id,
                "pattern_type": "part_anomaly",
                "description": f"Part '{anomaly.get('part_name')}' not matching expectations",
                "affected_parts": [{
                    "part_id": anomaly["_id"],
                    "name": anomaly.get("part_name"),
                    "anomaly_type": "expectation_mismatch",
                    "count": anomaly["count"]
                }],
                "detected_symptoms": [],
                "occurrence_count": anomaly["count"],
                "has_linked_failure_card": bool(anomaly.get("failure_cards")),
                "linked_failure_card_ids": [fc for fc in anomaly.get("failure_cards", []) if fc],
                "confidence_score": min(0.8, anomaly["count"] / 5),
                "status": "detected",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        return patterns
    
    def _find_common_keywords(self, texts: List[str]) -> List[str]:
        """Find keywords common across multiple texts"""
        from collections import Counter
        
        all_keywords = []
        for text in texts:
            keywords = self._extract_symptoms(text)
            all_keywords.extend(keywords)
        
        # Find keywords appearing in at least 50% of texts
        counter = Counter(all_keywords)
        threshold = len(texts) * 0.5
        
        return [kw for kw, count in counter.items() if count >= threshold]
    
    async def handle_pattern_detected(self, event: dict) -> Dict[str, Any]:
        """Handle pattern detection event"""
        pattern_id = event["data"].get("pattern_id")
        # Could trigger notifications to experts
        return {"status": "success", "pattern_id": pattern_id}
    
    # =====================================================================
    # HELPER METHODS
    # =====================================================================
    
    async def _emit_event(
        self,
        event_type: str,
        data: dict,
        priority: int = 5,
        org_id: str = None
    ):
        """Emit a new EFI event"""
        import uuid
        
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": event_type,
            "source": "event_processor",
            "priority": priority,
            "data": data,
            "organization_id": org_id,  # TIER 1: org-scoped — Sprint 1C
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processed": False,
            "retry_count": 0,
            "max_retries": 3
        }
        
        await self.db.efi_events.insert_one(event)
    
    async def process_pending_events(self, limit: int = 100) -> Dict[str, Any]:
        """Process all pending events"""
        events = await self.db.efi_events.find(
            {"processed": False}
        ).sort([("priority", 1), ("timestamp", 1)]).limit(limit).to_list(limit)
        
        results = {"processed": 0, "errors": 0, "skipped": 0}
        
        for event in events:
            result = await self.process_event(event)
            if result.get("status") == "success":
                results["processed"] += 1
            elif result.get("status") == "error":
                results["errors"] += 1
            else:
                results["skipped"] += 1
        
        return results
