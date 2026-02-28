"""
Battwheels OS - Continuous Learning Service

Part D of Phase 2 - Continuous Learning (Invisible to Technician)

Handles:
- On ticket closure: capture actual root cause, parts replaced, AI correctness
- Update historical_success_rate and recurrence_counter on failure cards
- Background job for processing learning events
- Pattern detection trigger (Part E)

This runs in background - NO UI impact for technicians.

DEPRECATED_COLLECTIONS:
  efi_failure_cards — consolidated into failure_cards in Sprint 3B-01.
  All reads and writes now use failure_cards as the single canonical
  collection. The efi_failure_cards collection is no longer referenced.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class ContinuousLearningService:
    """
    Continuous Learning Engine for EFI Intelligence.
    
    Captures outcomes from ticket closures and guidance feedback,
    then updates success rates and recurrence counters on failure cards.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.learning_queue = db.efi_learning_queue
        self.failure_cards = db.failure_cards  # Sprint 3B-01: consolidated from efi_failure_cards
        self.guidance_snapshots = db.ai_guidance_snapshots
        self.tickets = db.tickets
        self.model_risk_alerts = db.efi_model_risk_alerts
    
    async def capture_ticket_closure(
        self,
        ticket_id: str,
        organization_id: str,
        closure_data: Dict[str, Any]
    ) -> str:
        """
        Capture learning data when a ticket is closed.
        
        Captures:
        - Actual root cause
        - Parts replaced
        - AI correctness (was AI guidance used and helpful?)
        - Time to resolve
        """
        event_id = f"LE-{uuid.uuid4().hex[:12].upper()}"
        
        # Get the ticket
        ticket = await self.tickets.find_one(
            {"ticket_id": ticket_id},
            {"_id": 0}
        )
        
        if not ticket:
            logger.warning(f"Ticket {ticket_id} not found for learning capture")
            return event_id
        
        # Get any guidance that was generated for this ticket
        guidance = await self.guidance_snapshots.find_one(
            {"ticket_id": ticket_id, "status": "active"},
            {"_id": 0}
        )
        
        # Calculate resolution time
        created_at = ticket.get("created_at")
        closed_at = closure_data.get("closed_at") or datetime.now(timezone.utc).isoformat()
        
        resolution_time_minutes = None
        if created_at:
            try:
                start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                end = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                resolution_time_minutes = int((end - start).total_seconds() / 60)
            except Exception as e:
                logger.warning(f"Could not calculate resolution time: {e}")
        
        # Create learning event
        learning_event = {
            "event_id": event_id,
            "event_type": "ticket_closure",
            "ticket_id": ticket_id,
            "organization_id": organization_id,
            
            # Vehicle info (for model-aware learning)
            "vehicle_make": ticket.get("vehicle_info", {}).get("make") or ticket.get("vehicle_oem"),
            "vehicle_model": ticket.get("vehicle_info", {}).get("model") or ticket.get("vehicle_model"),
            "vehicle_variant": ticket.get("vehicle_info", {}).get("variant"),
            "vehicle_category": ticket.get("vehicle_category", "2W"),
            
            # Issue context
            "category": ticket.get("category"),
            "subsystem": closure_data.get("subsystem") or ticket.get("category"),
            "symptoms": ticket.get("symptoms", []),
            "dtc_codes": ticket.get("dtc_codes", []),
            
            # Resolution data
            "actual_root_cause": closure_data.get("actual_root_cause") or closure_data.get("resolution"),
            "parts_replaced": closure_data.get("parts_replaced", []),
            "repair_actions": closure_data.get("repair_actions", []),
            "resolution_time_minutes": resolution_time_minutes,
            
            # AI correctness
            "guidance_id": guidance.get("guidance_id") if guidance else None,
            "ai_guidance_used": guidance is not None,
            "ai_was_correct": closure_data.get("ai_was_correct"),
            "ai_suggested_cause": guidance.get("probable_causes", [{}])[0].get("cause") if guidance else None,
            
            # Processing status
            "status": "pending",
            "processed_at": None,
            "processing_result": None,
            
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.learning_queue.insert_one(learning_event)
        logger.info(f"Captured learning event {event_id} for ticket {ticket_id}")
        
        # EFI-PIPELINE-GAP: No automated call to knowledge_store_service here.
        # The learning event is written to efi_learning_queue and updates
        # failure_cards on processing, but NEVER creates or updates
        # knowledge_articles or knowledge_embeddings.
        # The knowledge_store_service.create_failure_card_from_ticket() method
        # exists but is only reachable via manual API (routes/knowledge_brain.py).
        # Sprint 3A documents this gap; Sprint 3B should bridge it with an
        # anonymised write to knowledge_articles after learning event processing.
        
        # Trigger immediate processing for high-value events
        if closure_data.get("ai_was_correct") is False or closure_data.get("unsafe_incident"):
            await self.process_learning_event(event_id)
        
        return event_id
    
    async def process_learning_event(self, event_id: str) -> Dict[str, Any]:
        """
        Process a single learning event.
        
        Updates:
        - Failure card success rates
        - Recurrence counters
        - Triggers pattern detection if needed
        """
        event = await self.learning_queue.find_one(
            {"event_id": event_id},
            {"_id": 0}
        )
        
        if not event:
            return {"success": False, "error": "Event not found"}
        
        if event.get("status") == "processed":
            return {"success": True, "already_processed": True}
        
        result = {
            "success": True,
            "event_id": event_id,
            "actions_taken": []
        }
        
        try:
            # 1. Find or create matching failure card
            failure_card = await self._find_matching_failure_card(event)
            
            if failure_card:
                # Update existing card
                update_ops = {
                    "$inc": {"usage_count": 1, "recurrence_counter": 1},
                    "$set": {
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "last_used_at": datetime.now(timezone.utc).isoformat()
                    }
                }
                
                # Update success rate based on AI correctness
                if event.get("ai_was_correct") is not None:
                    if event["ai_was_correct"]:
                        update_ops["$inc"]["positive_feedback_count"] = 1
                    else:
                        update_ops["$inc"]["negative_feedback_count"] = 1
                    
                    # Recalculate success rate
                    pos = failure_card.get("positive_feedback_count", 0) + (1 if event["ai_was_correct"] else 0)
                    neg = failure_card.get("negative_feedback_count", 0) + (0 if event["ai_was_correct"] else 1)
                    total = pos + neg
                    if total > 0:
                        new_rate = round(pos / total, 3)
                        update_ops["$set"]["historical_success_rate"] = new_rate
                        update_ops["$set"]["last_confidence_update"] = datetime.now(timezone.utc).isoformat()
                
                # Sprint 3B-01: handle different ID field names across card sources
                card_id_field = None
                card_id_value = None
                for id_field in ("card_id", "failure_id", "failure_card_id"):
                    if failure_card.get(id_field):
                        card_id_field = id_field
                        card_id_value = failure_card[id_field]
                        break
                
                if card_id_field:
                    await self.failure_cards.update_one(
                        {card_id_field: card_id_value},
                        update_ops
                    )
                result["actions_taken"].append({
                    "action": "updated_failure_card",
                    "failure_card_id": card_id_value
                })
            else:
                # Create draft failure card for unknown issue
                if event.get("actual_root_cause"):
                    new_card_id = await self._create_draft_failure_card(event)
                    result["actions_taken"].append({
                        "action": "created_draft_failure_card",
                        "failure_card_id": new_card_id
                    })
            
            # 2. Check for patterns (Part E - Pattern Detection)
            pattern_result = await self._check_for_patterns(event)
            if pattern_result:
                result["actions_taken"].append({
                    "action": "triggered_pattern_alert",
                    **pattern_result
                })
            
            # 3. Mark event as processed
            await self.learning_queue.update_one(
                {"event_id": event_id},
                {
                    "$set": {
                        "status": "processed",
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                        "processing_result": result
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing learning event {event_id}: {e}")
            await self.learning_queue.update_one(
                {"event_id": event_id},
                {"$set": {"status": "error", "error_message": str(e)}}
            )
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    async def _find_matching_failure_card(self, event: Dict) -> Optional[Dict]:
        """
        Find a failure card that matches the event context.
        
        Matching criteria:
        - Same vehicle model (or global card)
        - Same subsystem
        - Similar symptoms or DTC codes
        """
        # Build query — handle both legacy field names (Sprint 3B-01)
        subsystem_val = event.get("subsystem") or event.get("category")
        query = {
            "status": {"$in": ["approved", "draft"]},
        }
        
        # Use $and to combine filters without clobbering $or
        and_conditions = []
        
        # failure_cards uses fault_category or subsystem or subsystem_category
        if subsystem_val:
            and_conditions.append({
                "$or": [
                    {"subsystem": subsystem_val},
                    {"fault_category": subsystem_val},
                    {"subsystem_category": subsystem_val},
                ]
            })
        
        # Try model-specific or global cards
        if event.get("vehicle_model"):
            and_conditions.append({
                "$or": [
                    {"vehicle_model": event["vehicle_model"]},
                    {"vehicle_model": None},
                    {"scope": "global"},
                    {"organization_id": None},  # Seed cards have no org
                ]
            })
        
        # Add DTC code matching if available
        if event.get("dtc_codes"):
            and_conditions.append({
                "$or": [
                    {"dtc_codes": {"$in": event["dtc_codes"]}},
                    {"dtc_code": {"$in": event["dtc_codes"]}},
                    {"error_codes": {"$in": event["dtc_codes"]}},
                ]
            })
        
        if and_conditions:
            query["$and"] = and_conditions
        
        # Find best matching card
        cards = await self.failure_cards.find(
            query,
            {"_id": 0}
        ).sort("historical_success_rate", -1).limit(5).to_list(5)
        
        if not cards:
            return None
        
        # Score and select best match
        best_match = None
        best_score = 0
        
        for card in cards:
            score = 0
            
            # Model match bonus
            if card.get("vehicle_model") == event.get("vehicle_model"):
                score += 30
            
            # DTC match bonus
            card_dtcs = set(card.get("dtc_codes", []))
            event_dtcs = set(event.get("dtc_codes", []))
            if card_dtcs & event_dtcs:
                score += 25
            
            # Symptom overlap bonus
            card_symptoms = set(card.get("symptom_cluster", []))
            event_symptoms = set(event.get("symptoms", []))
            if card_symptoms & event_symptoms:
                score += 20
            
            # Success rate bonus
            score += card.get("historical_success_rate", 0.5) * 15
            
            # Recency bonus
            if card.get("last_used_at"):
                try:
                    last_used = datetime.fromisoformat(card["last_used_at"].replace("Z", "+00:00"))
                    days_ago = (datetime.now(timezone.utc) - last_used).days
                    if days_ago < 7:
                        score += 10
                    elif days_ago < 30:
                        score += 5
                except Exception:
                    pass
            
            if score > best_score:
                best_score = score
                best_match = card
        
        return best_match
    
    async def _create_draft_failure_card(self, event: Dict) -> str:
        """
        Create or update a failure card from the learning event.
        Uses upsert by ticket_id + organization_id to avoid duplicates
        with auto-created cards from routes/tickets.py (Sprint 3B-01).
        """
        card_id = f"fc_{uuid.uuid4().hex[:12]}"
        ticket_id = event.get("ticket_id")
        org_id = event.get("organization_id")
        
        learning_data = {
            # Vehicle classification
            "vehicle_make": event.get("vehicle_make"),
            "vehicle_model": event.get("vehicle_model"),
            "vehicle_variant": event.get("vehicle_variant"),
            "vehicle_category": event.get("vehicle_category", "2W"),
            
            # Issue details — write to both field names for compatibility
            "subsystem": event.get("subsystem") or event.get("category"),
            "fault_category": event.get("subsystem") or event.get("category"),
            "symptom_cluster": event.get("symptoms", []),
            "dtc_code": event["dtc_codes"][0] if event.get("dtc_codes") else None,
            "dtc_codes": event.get("dtc_codes", []),
            
            # Root cause and fix
            "probable_root_cause": event.get("actual_root_cause"),
            "root_cause": event.get("actual_root_cause"),
            "verified_fix": event.get("actual_root_cause"),
            "parts_required": event.get("parts_replaced", []),
            "estimated_repair_time_minutes": event.get("resolution_time_minutes") or 60,
            
            # Metrics
            "historical_success_rate": 0.5,
            "confidence_score": 0.3,
            
            # Status
            "status": "draft",
            "source_type": "field_discovery",
            
            # Timestamps
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "last_used_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Sprint 3B-01: upsert by ticket_id + organization_id
        result = await self.failure_cards.update_one(
            {"ticket_id": ticket_id, "organization_id": org_id},
            {
                "$set": learning_data,
                "$inc": {"recurrence_counter": 1, "usage_count": 1},
                "$setOnInsert": {
                    "card_id": card_id,
                    "ticket_id": ticket_id,
                    "organization_id": org_id,
                    "scope": "tenant",
                    "positive_feedback_count": 0,
                    "negative_feedback_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "first_detected_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        action = "upserted" if result.upserted_id else "updated"
        logger.info(f"{action} failure card for ticket {ticket_id} (card_id={card_id})")
        
        # Sprint 3B-03: Auto-generate embedding after upsert
        try:
            from services.efi_embedding_service import EFIEmbeddingManager
            efi_emb = EFIEmbeddingManager(self.db)
            card_text = " ".join(filter(None, [
                event.get("actual_root_cause", ""),
                event.get("subsystem", ""),
                event.get("category", ""),
                " ".join(event.get("symptoms", [])),
            ])).strip()
            if card_text:
                emb_result = await efi_emb.generate_complaint_embedding(card_text)
                if emb_result and emb_result.get("embedding"):
                    await self.failure_cards.update_one(
                        {"ticket_id": ticket_id, "organization_id": org_id},
                        {"$set": {
                            "embedding_vector": emb_result["embedding"],
                            "subsystem_category": emb_result.get("classified_subsystem"),
                            "embedding_generated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
        except Exception as emb_err:
            logger.warning(f"Embedding generation failed for learning card {ticket_id}: {emb_err}")
        
        return card_id
    
    async def _check_for_patterns(self, event: Dict) -> Optional[Dict]:
        """
        Part E - Lean Pattern Detection
        
        If ≥3 similar failures in 30 days (same model + subsystem):
        Trigger "Model Risk Alert" for supervisor dashboard.
        """
        # Only check if we have model info
        if not event.get("vehicle_model") or not event.get("subsystem"):
            return None
        
        # Count similar events in last 30 days
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        similar_count = await self.learning_queue.count_documents({
            "vehicle_model": event["vehicle_model"],
            "subsystem": event["subsystem"],
            "created_at": {"$gte": thirty_days_ago},
            "event_type": "ticket_closure"
        })
        
        # Trigger alert if ≥3 similar failures
        if similar_count >= 3:
            # Check if alert already exists
            existing_alert = await self.model_risk_alerts.find_one({
                "vehicle_model": event["vehicle_model"],
                "subsystem": event["subsystem"],
                "status": "active"
            })
            
            if existing_alert:
                # Update existing alert
                await self.model_risk_alerts.update_one(
                    {"alert_id": existing_alert["alert_id"]},
                    {
                        "$inc": {"occurrence_count": 1},
                        "$set": {"last_occurrence": datetime.now(timezone.utc).isoformat()},
                        "$push": {"affected_ticket_ids": event.get("ticket_id")}
                    }
                )
                return {
                    "alert_id": existing_alert["alert_id"],
                    "action": "updated_existing",
                    "occurrence_count": existing_alert["occurrence_count"] + 1
                }
            else:
                # Create new alert
                alert_id = f"MRA-{uuid.uuid4().hex[:8].upper()}"
                
                # Get affected ticket IDs
                affected_tickets = await self.learning_queue.find(
                    {
                        "vehicle_model": event["vehicle_model"],
                        "subsystem": event["subsystem"],
                        "created_at": {"$gte": thirty_days_ago}
                    },
                    {"ticket_id": 1}
                ).to_list(20)
                
                alert = {
                    "alert_id": alert_id,
                    "organization_id": event.get("organization_id"),
                    
                    "vehicle_make": event.get("vehicle_make"),
                    "vehicle_model": event["vehicle_model"],
                    "subsystem": event["subsystem"],
                    
                    "occurrence_count": similar_count,
                    "first_occurrence": thirty_days_ago,
                    "last_occurrence": datetime.now(timezone.utc).isoformat(),
                    "affected_ticket_ids": [t.get("ticket_id") for t in affected_tickets if t.get("ticket_id")],
                    
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.model_risk_alerts.insert_one(alert)
                logger.warning(f"Created Model Risk Alert {alert_id}: {event['vehicle_model']} - {event['subsystem']} ({similar_count} occurrences)")
                
                return {
                    "alert_id": alert_id,
                    "action": "created_new",
                    "occurrence_count": similar_count
                }
        
        return None
    
    async def process_pending_events(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Process pending learning events in batch.
        Run this as a background job.
        """
        pending = await self.learning_queue.find(
            {"status": "pending"},
            {"event_id": 1, "_id": 0}
        ).sort("created_at", 1).limit(batch_size).to_list(batch_size)
        
        results = {
            "processed": 0,
            "errors": 0,
            "event_ids": []
        }
        
        for event_doc in pending:
            event_id = event_doc.get("event_id")
            try:
                await self.process_learning_event(event_id)
                results["processed"] += 1
                results["event_ids"].append(event_id)
            except Exception as e:
                logger.error(f"Batch processing error for {event_id}: {e}")
                results["errors"] += 1
        
        return results
    
    async def get_learning_stats(self, organization_id: str) -> Dict[str, Any]:
        """Get learning stats for supervisor dashboard"""
        pipeline = [
            {"$match": {"organization_id": organization_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        status_counts = await self.learning_queue.aggregate(pipeline).to_list(10)
        
        # Get active alerts
        active_alerts = await self.model_risk_alerts.count_documents({
            "organization_id": organization_id,
            "status": "active"
        })
        
        # Get failure card stats
        failure_card_stats = await self.failure_cards.aggregate([
            {"$match": {"organization_id": organization_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]).to_list(10)
        
        return {
            "learning_events": {
                status["_id"]: status["count"] for status in status_counts
            },
            "active_risk_alerts": active_alerts,
            "failure_cards": {
                status["_id"]: status["count"] for status in failure_card_stats
            }
        }
