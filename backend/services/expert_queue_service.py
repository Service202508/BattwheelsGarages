"""
Battwheels Knowledge Brain - Expert Queue Service
Internal escalation system for human expert review.

STATUS: PRODUCTION-READY (internal queue). ZendeskBridge is STUBBED.

The ExpertQueueService class is fully functional using MongoDB as its
backend. It handles escalation creation, assignment, resolution, and
knowledge capture internally.

The ZendeskBridge class is a STUB that returns mock responses. If
Zendesk integration is needed in the future, implement the bridge
methods to call the Zendesk API. See docs/FEATURE_GAPS.md for details.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import motor.motor_asyncio

logger = logging.getLogger(__name__)


# ==================== EXPERT QUEUE STATUS ====================

class ExpertQueueStatus:
    """Status values for expert queue items"""
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ExpertQueuePriority:
    """Priority levels for expert queue"""
    CRITICAL = "critical"  # Safety issue - respond within 1 hour
    HIGH = "high"          # Customer blocked - respond within 4 hours
    MEDIUM = "medium"      # Standard - respond within 24 hours
    LOW = "low"            # Can wait - respond within 48 hours


# ==================== ZENDESK BRIDGE INTERFACE ====================

class ZendeskBridge:
    """
    STUB: Abstract interface for Zendesk integration.
    Currently returns mock responses — the internal ExpertQueueService
    handles all escalation logic via MongoDB.
    
    To implement real Zendesk integration:
    - Obtain Zendesk subdomain, API token, and agent email
    - Implement create_ticket() to POST to /api/v2/tickets.json
    - Implement update_ticket() to PUT to /api/v2/tickets/{id}.json
    - Implement add_comment() to POST to /api/v2/tickets/{id}.json
    - Set _enabled = True when credentials are configured
    
    See: https://developer.zendesk.com/api-reference/
    """
    
    def __init__(self, subdomain: str = None, api_token: str = None, email: str = None):
        self.subdomain = subdomain
        self.api_token = api_token
        self.email = email
        self._enabled = False  # Zendesk is disabled, using internal queue
    
    @property
    def is_enabled(self) -> bool:
        """Check if Zendesk integration is configured and enabled"""
        return self._enabled and all([self.subdomain, self.api_token, self.email])
    
    async def create_ticket(
        self,
        subject: str,
        description: str,
        requester_name: str,
        requester_email: str,
        priority: str = "normal",
        tags: List[str] = None,
        custom_fields: Dict[str, Any] = None
    ) -> Dict:
        """
        Create a Zendesk ticket.
        STUB: Returns mock response - actual implementation would call Zendesk API.
        """
        logger.info(f"[ZendeskBridge STUB] Would create ticket: {subject}")
        
        return {
            "status": "stub",
            "message": "Zendesk integration not enabled. Using internal Expert Queue.",
            "ticket_id": None,
            "zendesk_enabled": False
        }
    
    async def update_ticket(self, ticket_id: str, **updates) -> Dict:
        """Update a Zendesk ticket. STUB."""
        return {"status": "stub", "message": "Zendesk not enabled"}
    
    async def add_comment(self, ticket_id: str, comment: str, public: bool = True) -> Dict:
        """Add comment to Zendesk ticket. STUB."""
        return {"status": "stub", "message": "Zendesk not enabled"}


# ==================== EXPERT QUEUE SERVICE ====================

class ExpertQueueService:
    """
    Internal Expert Queue system for Battwheels OS.
    Replaces Zendesk for escalation handling.
    
    Features:
    - Create escalation tickets from AI queries
    - Assign to expert technicians/supervisors
    - Track resolution in ticket timeline
    - Knowledge capture from resolutions
    """
    
    def __init__(self, db: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.queue_collection = db.expert_queue
        self.experts_collection = db.expert_roster
        self.zendesk_bridge = ZendeskBridge()  # Stubbed
    
    async def initialize_indexes(self):
        """Create necessary indexes"""
        await self.queue_collection.create_index([
            ("organization_id", 1), ("status", 1)
        ])
        await self.queue_collection.create_index([
            ("assigned_expert_id", 1), ("status", 1)
        ])
        await self.queue_collection.create_index([
            ("priority", 1), ("created_at", -1)
        ])
        await self.queue_collection.create_index([
            ("ticket_id", 1)
        ])
        logger.info("Expert Queue indexes initialized")
    
    async def create_escalation(
        self,
        query_id: str,
        ticket_id: Optional[str],
        organization_id: str,
        original_query: str,
        ai_response: str,
        sources_checked: List[str],
        vehicle_info: Optional[Dict] = None,
        symptoms: List[str] = None,
        dtc_codes: List[str] = None,
        images: List[str] = None,
        documents: List[str] = None,
        urgency: str = "medium",
        reason: str = "",
        user_id: str = "",
        user_name: str = ""
    ) -> Dict:
        """
        Create a new expert queue escalation.
        
        This is the main entry point for escalating from AI assistant.
        Returns escalation details for tracking.
        """
        now = datetime.now(timezone.utc).isoformat()
        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        
        # Map urgency to priority
        priority_map = {
            "low": ExpertQueuePriority.LOW,
            "normal": ExpertQueuePriority.MEDIUM,
            "medium": ExpertQueuePriority.MEDIUM,
            "high": ExpertQueuePriority.HIGH,
            "critical": ExpertQueuePriority.CRITICAL,
        }
        priority = priority_map.get(urgency, ExpertQueuePriority.MEDIUM)
        
        # Determine category from symptoms/vehicle info
        category = self._determine_category(symptoms or [], vehicle_info)
        
        escalation_doc = {
            "escalation_id": escalation_id,
            "query_id": query_id,
            "ticket_id": ticket_id,
            "organization_id": organization_id,
            
            # Query context
            "original_query": original_query,
            "ai_response": ai_response,
            "sources_checked": sources_checked or [],
            
            # Vehicle & issue context
            "vehicle_info": vehicle_info or {},
            "symptoms": symptoms or [],
            "dtc_codes": dtc_codes or [],
            "category": category,
            
            # Attachments
            "images": images or [],
            "documents": documents or [],
            
            # Priority & status
            "priority": priority,
            "urgency": urgency,
            "reason": reason,
            "status": ExpertQueueStatus.OPEN,
            
            # Assignment (initially unassigned)
            "assigned_expert_id": None,
            "assigned_expert_name": None,
            "assigned_at": None,
            
            # Resolution
            "expert_response": None,
            "resolution_notes": None,
            "resolved_at": None,
            "resolution_duration_minutes": None,
            
            # Knowledge capture flag
            "knowledge_captured": False,
            "knowledge_id": None,
            
            # Requester
            "requester_id": user_id,
            "requester_name": user_name,
            
            # Timeline/audit trail
            "timeline": [
                {
                    "event": "created",
                    "timestamp": now,
                    "user_id": user_id,
                    "user_name": user_name,
                    "details": f"Escalation created: {reason}"
                }
            ],
            
            # Timestamps
            "created_at": now,
            "updated_at": now
        }
        
        await self.queue_collection.insert_one(escalation_doc)
        
        # Also add to ticket timeline if ticket_id provided
        if ticket_id:
            await self._add_to_ticket_timeline(
                ticket_id, 
                escalation_id, 
                "escalated",
                user_name,
                reason
            )
        
        logger.info(f"Created expert queue escalation: {escalation_id}")
        
        return {
            "escalation_id": escalation_id,
            "status": ExpertQueueStatus.OPEN,
            "priority": priority,
            "message": "Escalation created and added to Expert Queue.",
            "zendesk_enabled": self.zendesk_bridge.is_enabled
        }
    
    async def assign_expert(
        self,
        escalation_id: str,
        expert_id: str,
        expert_name: str,
        assigned_by: str
    ) -> Dict:
        """Assign an expert to handle the escalation"""
        now = datetime.now(timezone.utc).isoformat()
        
        result = await self.queue_collection.update_one(
            {"escalation_id": escalation_id},
            {
                "$set": {
                    "assigned_expert_id": expert_id,
                    "assigned_expert_name": expert_name,
                    "assigned_at": now,
                    "status": ExpertQueueStatus.ASSIGNED,
                    "updated_at": now
                },
                "$push": {
                    "timeline": {
                        "event": "assigned",
                        "timestamp": now,
                        "user_id": assigned_by,
                        "details": f"Assigned to expert: {expert_name}"
                    }
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Assigned {escalation_id} to expert {expert_name}")
            return {"status": "assigned", "expert_name": expert_name}
        
        return {"status": "failed", "message": "Escalation not found"}
    
    async def start_work(
        self,
        escalation_id: str,
        expert_id: str
    ) -> Dict:
        """Mark escalation as in-progress"""
        now = datetime.now(timezone.utc).isoformat()
        
        result = await self.queue_collection.update_one(
            {"escalation_id": escalation_id, "assigned_expert_id": expert_id},
            {
                "$set": {
                    "status": ExpertQueueStatus.IN_PROGRESS,
                    "work_started_at": now,
                    "updated_at": now
                },
                "$push": {
                    "timeline": {
                        "event": "work_started",
                        "timestamp": now,
                        "user_id": expert_id,
                        "details": "Expert started working on this issue"
                    }
                }
            }
        )
        
        return {"status": "in_progress" if result.modified_count > 0 else "failed"}
    
    async def resolve_escalation(
        self,
        escalation_id: str,
        expert_id: str,
        expert_name: str,
        response: str,
        resolution_notes: str,
        capture_knowledge: bool = True
    ) -> Dict:
        """
        Resolve an escalation with expert response.
        Optionally captures resolution as new knowledge.
        """
        now = datetime.now(timezone.utc).isoformat()
        
        # Get escalation for duration calculation
        escalation = await self.queue_collection.find_one(
            {"escalation_id": escalation_id},
            {"_id": 0}
        )
        
        if not escalation:
            return {"status": "failed", "message": "Escalation not found"}
        
        # Calculate resolution time
        created_at = datetime.fromisoformat(escalation["created_at"].replace('Z', '+00:00'))
        duration_minutes = int((datetime.now(timezone.utc) - created_at).total_seconds() / 60)
        
        update_data = {
            "status": ExpertQueueStatus.RESOLVED,
            "expert_response": response,
            "resolution_notes": resolution_notes,
            "resolved_at": now,
            "resolution_duration_minutes": duration_minutes,
            "updated_at": now
        }
        
        # Capture knowledge if requested
        knowledge_id = None
        if capture_knowledge:
            knowledge_id = await self._capture_knowledge(escalation, response, resolution_notes, expert_id)
            if knowledge_id:
                update_data["knowledge_captured"] = True
                update_data["knowledge_id"] = knowledge_id
        
        await self.queue_collection.update_one(
            {"escalation_id": escalation_id},
            {
                "$set": update_data,
                "$push": {
                    "timeline": {
                        "event": "resolved",
                        "timestamp": now,
                        "user_id": expert_id,
                        "user_name": expert_name,
                        "details": f"Resolved by {expert_name}. Resolution time: {duration_minutes} minutes"
                    }
                }
            }
        )
        
        # Update original ticket if exists
        if escalation.get("ticket_id"):
            await self._add_to_ticket_timeline(
                escalation["ticket_id"],
                escalation_id,
                "expert_resolved",
                expert_name,
                response[:200]  # First 200 chars
            )
        
        logger.info(f"Resolved escalation {escalation_id} by {expert_name}")
        
        return {
            "status": "resolved",
            "escalation_id": escalation_id,
            "resolution_duration_minutes": duration_minutes,
            "knowledge_captured": knowledge_id is not None,
            "knowledge_id": knowledge_id
        }
    
    async def add_comment(
        self,
        escalation_id: str,
        user_id: str,
        user_name: str,
        comment: str,
        is_internal: bool = False
    ) -> Dict:
        """Add a comment to the escalation timeline"""
        now = datetime.now(timezone.utc).isoformat()
        
        result = await self.queue_collection.update_one(
            {"escalation_id": escalation_id},
            {
                "$push": {
                    "timeline": {
                        "event": "comment_internal" if is_internal else "comment",
                        "timestamp": now,
                        "user_id": user_id,
                        "user_name": user_name,
                        "details": comment,
                        "is_internal": is_internal
                    }
                },
                "$set": {"updated_at": now}
            }
        )
        
        return {"status": "added" if result.modified_count > 0 else "failed"}
    
    async def request_info(
        self,
        escalation_id: str,
        expert_id: str,
        expert_name: str,
        request_details: str
    ) -> Dict:
        """Request additional information from requester"""
        now = datetime.now(timezone.utc).isoformat()
        
        result = await self.queue_collection.update_one(
            {"escalation_id": escalation_id},
            {
                "$set": {
                    "status": ExpertQueueStatus.PENDING_INFO,
                    "updated_at": now
                },
                "$push": {
                    "timeline": {
                        "event": "info_requested",
                        "timestamp": now,
                        "user_id": expert_id,
                        "user_name": expert_name,
                        "details": request_details
                    }
                }
            }
        )
        
        return {"status": "pending_info" if result.modified_count > 0 else "failed"}
    
    async def get_escalation(self, escalation_id: str) -> Optional[Dict]:
        """Get escalation by ID"""
        return await self.queue_collection.find_one(
            {"escalation_id": escalation_id},
            {"_id": 0}
        )
    
    async def list_escalations(
        self,
        organization_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """List escalations with filters"""
        query = {"organization_id": organization_id}
        
        if status:
            query["status"] = status
        if assigned_to:
            query["assigned_expert_id"] = assigned_to
        if priority:
            query["priority"] = priority
        
        escalations = await self.queue_collection.find(
            query, {"_id": 0}
        ).sort([
            ("priority", 1),  # Critical first
            ("created_at", -1)
        ]).skip(offset).limit(limit).to_list(limit)
        
        total = await self.queue_collection.count_documents(query)
        
        return {
            "escalations": escalations,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_expert_workload(self, organization_id: str) -> List[Dict]:
        """Get workload summary per expert"""
        pipeline = [
            {"$match": {
                "organization_id": organization_id,
                "status": {"$in": [ExpertQueueStatus.ASSIGNED, ExpertQueueStatus.IN_PROGRESS]}
            }},
            {"$group": {
                "_id": {
                    "expert_id": "$assigned_expert_id",
                    "expert_name": "$assigned_expert_name"
                },
                "total": {"$sum": 1},
                "critical": {"$sum": {"$cond": [{"$eq": ["$priority", "critical"]}, 1, 0]}},
                "high": {"$sum": {"$cond": [{"$eq": ["$priority", "high"]}, 1, 0]}},
            }},
            {"$project": {
                "_id": 0,
                "expert_id": "$_id.expert_id",
                "expert_name": "$_id.expert_name",
                "total_assigned": "$total",
                "critical_count": "$critical",
                "high_count": "$high"
            }}
        ]
        
        return await self.queue_collection.aggregate(pipeline).to_list(100)
    
    async def get_queue_stats(self, organization_id: str) -> Dict:
        """Get expert queue statistics"""
        base_query = {"organization_id": organization_id}
        
        total = await self.queue_collection.count_documents(base_query)
        open_count = await self.queue_collection.count_documents({**base_query, "status": ExpertQueueStatus.OPEN})
        assigned = await self.queue_collection.count_documents({**base_query, "status": ExpertQueueStatus.ASSIGNED})
        in_progress = await self.queue_collection.count_documents({**base_query, "status": ExpertQueueStatus.IN_PROGRESS})
        resolved = await self.queue_collection.count_documents({**base_query, "status": ExpertQueueStatus.RESOLVED})
        
        # Average resolution time
        pipeline = [
            {"$match": {**base_query, "status": ExpertQueueStatus.RESOLVED}},
            {"$group": {
                "_id": None,
                "avg_resolution_minutes": {"$avg": "$resolution_duration_minutes"}
            }}
        ]
        avg_result = await self.queue_collection.aggregate(pipeline).to_list(1)
        avg_resolution = avg_result[0]["avg_resolution_minutes"] if avg_result else 0
        
        return {
            "total": total,
            "open": open_count,
            "assigned": assigned,
            "in_progress": in_progress,
            "resolved": resolved,
            "avg_resolution_minutes": round(avg_resolution, 1) if avg_resolution else 0
        }
    
    # ==================== HELPER METHODS ====================
    
    def _determine_category(self, symptoms: List[str], vehicle_info: Optional[Dict]) -> str:
        """Determine category from symptoms and vehicle info"""
        symptom_text = " ".join(symptoms).lower()
        
        if any(kw in symptom_text for kw in ["battery", "charge", "soc", "bms"]):
            return "battery"
        elif any(kw in symptom_text for kw in ["motor", "drive", "torque", "hall"]):
            return "motor"
        elif any(kw in symptom_text for kw in ["charger", "charging", "ccs", "type2"]):
            return "charger"
        elif any(kw in symptom_text for kw in ["wire", "fuse", "relay", "voltage"]):
            return "electrical"
        
        return "general"
    
    async def _add_to_ticket_timeline(
        self,
        ticket_id: str,
        escalation_id: str,
        event: str,
        user_name: str,
        details: str
    ):
        """Add escalation event to ticket timeline"""
        now = datetime.now(timezone.utc).isoformat()
        
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {
                "$push": {
                    "status_history": {
                        "event": f"expert_queue_{event}",
                        "escalation_id": escalation_id,
                        "timestamp": now,
                        "user": user_name,
                        "details": details
                    }
                },
                "$set": {"updated_at": now}
            }
        )
    
    async def _capture_knowledge(
        self,
        escalation: Dict,
        response: str,
        resolution_notes: str,
        expert_id: str
    ) -> Optional[str]:
        """Capture resolution as draft knowledge article"""
        try:
            from services.knowledge_store_service import KnowledgeStoreService
            
            store = KnowledgeStoreService(self.db)
            
            # Create a failure card draft from the resolution
            data = {
                "problem_title": f"Expert Resolution: {escalation['original_query'][:100]}",
                "problem_description": escalation['original_query'],
                "symptoms": escalation.get('symptoms', []),
                "dtc_codes": escalation.get('dtc_codes', []),
                "vehicle_make": escalation.get('vehicle_info', {}).get('make'),
                "vehicle_model": escalation.get('vehicle_info', {}).get('model'),
                "subsystem": escalation.get('category'),
                "fix_procedures": [
                    {"step": 1, "description": response},
                    {"step": 2, "description": resolution_notes}
                ],
                "expert_notes": f"Resolved by expert. Escalation ID: {escalation['escalation_id']}",
                "source_type": "expert_resolution",
                "source_id": escalation['escalation_id']
            }
            
            card = await store.create_failure_card(
                data=data,
                organization_id=escalation['organization_id'],
                created_by=expert_id
            )
            
            logger.info(f"Captured knowledge from escalation {escalation['escalation_id']}: {card['knowledge_id']}")
            return card['knowledge_id']
            
        except Exception as e:
            logger.error(f"Failed to capture knowledge: {e}")
            return None
