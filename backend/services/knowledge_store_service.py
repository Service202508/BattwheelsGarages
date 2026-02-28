"""
Battwheels Knowledge Brain - Knowledge Store Service
Handles knowledge storage, retrieval, and RAG operations
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import motor.motor_asyncio
from models.knowledge_brain import (
    KnowledgeArticle, FailureCard, ErrorCodeDefinition,
    KnowledgeType, KnowledgeScope, ApprovalStatus, Severity,
    AISource
)

logger = logging.getLogger(__name__)


class KnowledgeStoreService:
    """Service for managing the Knowledge Brain storage and retrieval"""
    
    def __init__(self, db: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.knowledge_collection = db.knowledge_articles
        self.failure_cards_collection = db.failure_cards
        self.error_codes_collection = db.error_codes
        self.embeddings_collection = db.knowledge_embeddings
    
    async def initialize_indexes(self):
        """Create necessary indexes for efficient retrieval"""
        # Knowledge articles indexes
        await self.knowledge_collection.create_index([
            ("organization_id", 1), ("scope", 1), ("approval_status", 1)
        ])
        await self.knowledge_collection.create_index([
            ("knowledge_type", 1), ("subsystem", 1)
        ])
        await self.knowledge_collection.create_index([
            ("symptoms", 1)
        ])
        await self.knowledge_collection.create_index([
            ("dtc_codes", 1)
        ])
        await self.knowledge_collection.create_index([
            ("vehicle_make", 1), ("vehicle_model", 1)
        ])
        await self.knowledge_collection.create_index([
            ("tags", 1)
        ])
        
        # Failure cards indexes
        await self.failure_cards_collection.create_index([
            ("organization_id", 1), ("scope", 1), ("approval_status", 1)
        ])
        await self.failure_cards_collection.create_index([
            ("dtc_codes", 1)
        ])
        await self.failure_cards_collection.create_index([
            ("symptoms", 1)
        ])
        await self.failure_cards_collection.create_index([
            ("subsystem", 1), ("vehicle_make", 1)
        ])
        
        # Error codes indexes
        await self.error_codes_collection.create_index([
            ("dtc_code", 1)
        ], unique=True)
        await self.error_codes_collection.create_index([
            ("vehicle_make", 1)
        ])
        
        logger.info("Knowledge Brain indexes initialized")
    
    # ==================== KNOWLEDGE RETRIEVAL ====================
    
    async def search_knowledge(
        self,
        query: str,
        organization_id: str,
        category: str = "general",
        vehicle_make: Optional[str] = None,
        vehicle_model: Optional[str] = None,
        dtc_codes: List[str] = [],
        symptoms: List[str] = [],
        limit: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Search knowledge base using keyword matching and filters.
        Returns list of (document, relevance_score) tuples.
        """
        results = []
        
        # Build search query
        base_query = {
            "approval_status": ApprovalStatus.APPROVED.value,
            "$or": [
                {"scope": KnowledgeScope.GLOBAL.value},
                {"organization_id": organization_id, "scope": KnowledgeScope.TENANT.value}
            ]
        }
        
        # Category to subsystem mapping
        category_subsystem = {
            "battery": ["battery", "bms", "charger"],
            "motor": ["motor", "controller"],
            "electrical": ["electrical", "telematics"],
            "diagnosis": None,  # All subsystems
            "general": None
        }
        
        subsystems = category_subsystem.get(category)
        if subsystems:
            base_query["subsystem"] = {"$in": subsystems}
        
        # Vehicle filters
        if vehicle_make:
            base_query["$or"].append({"vehicle_make": {"$regex": vehicle_make, "$options": "i"}})
            base_query["$or"].append({"vehicle_make": None})  # Include generic
        
        # DTC code search
        if dtc_codes:
            dtc_query = base_query.copy()
            dtc_query["dtc_codes"] = {"$in": dtc_codes}
            
            async for doc in self.knowledge_collection.find(dtc_query, {"_id": 0}).limit(limit):
                # High relevance for DTC match
                results.append((doc, 0.95))
            
            async for doc in self.failure_cards_collection.find(dtc_query, {"_id": 0}).limit(limit):
                results.append((doc, 0.95))
        
        # Symptom search
        if symptoms:
            symptom_query = base_query.copy()
            symptom_query["symptoms"] = {"$in": symptoms}
            
            async for doc in self.knowledge_collection.find(symptom_query, {"_id": 0}).limit(limit):
                if doc not in [r[0] for r in results]:
                    results.append((doc, 0.85))
            
            async for doc in self.failure_cards_collection.find(symptom_query, {"_id": 0}).limit(limit):
                if doc not in [r[0] for r in results]:
                    results.append((doc, 0.85))
        
        # Text search in title and content
        query_words = query.lower().split()
        text_query = base_query.copy()
        text_query["$or"] = [
            {"title": {"$regex": word, "$options": "i"}} for word in query_words[:3]
        ] + [
            {"content": {"$regex": word, "$options": "i"}} for word in query_words[:3]
        ] + [
            {"tags": {"$in": query_words[:5]}}
        ]
        
        async for doc in self.knowledge_collection.find(
            text_query, {"_id": 0}
        ).sort("confidence_score", -1).limit(limit):
            if doc.get("knowledge_id") not in [r[0].get("knowledge_id") for r in results]:
                results.append((doc, 0.7))
        
        # Sort by relevance
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    async def get_failure_cards_for_symptoms(
        self,
        symptoms: List[str],
        organization_id: str,
        vehicle_make: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Get failure cards matching symptoms"""
        query = {
            "approval_status": ApprovalStatus.APPROVED.value,
            "$or": [
                {"scope": KnowledgeScope.GLOBAL.value},
                {"organization_id": organization_id, "scope": KnowledgeScope.TENANT.value}
            ],
            "symptoms": {"$in": symptoms}
        }
        
        if vehicle_make:
            query["$or"].append({"vehicle_make": {"$regex": vehicle_make, "$options": "i"}})
        
        cards = await self.failure_cards_collection.find(
            query, {"_id": 0}
        ).sort("confidence_score", -1).limit(limit).to_list(limit)
        
        return cards
    
    async def get_error_code_info(
        self,
        dtc_code: str,
        organization_id: str
    ) -> Optional[Dict]:
        """Get error code definition"""
        # Try exact match first
        code = await self.error_codes_collection.find_one(
            {"dtc_code": dtc_code.upper()},
            {"_id": 0}
        )
        
        if not code:
            # Try partial match
            code = await self.error_codes_collection.find_one(
                {"dtc_code": {"$regex": f"^{dtc_code}", "$options": "i"}},
                {"_id": 0}
            )
        
        return code
    
    async def format_sources(
        self,
        results: List[Tuple[Dict, float]]
    ) -> List[AISource]:
        """Format search results as AISource citations"""
        sources = []
        
        for doc, score in results:
            source_type = doc.get("knowledge_type", doc.get("failure_card_id", "unknown"))
            source_id = doc.get("knowledge_id", doc.get("failure_card_id", doc.get("code_id", "")))
            
            # Build snippet
            content = doc.get("content", doc.get("problem_description", ""))
            snippet = content[:200] + "..." if len(content) > 200 else content
            
            sources.append(AISource(
                source_id=source_id,
                source_type=str(source_type),
                title=doc.get("title", doc.get("problem_title", "Unknown")),
                relevance_score=score,
                snippet=snippet,
                link=f"/knowledge/{source_id}"
            ))
        
        return sources
    
    # ==================== KNOWLEDGE CREATION ====================
    
    async def create_knowledge_article(
        self,
        data: Dict[str, Any],
        organization_id: Optional[str],
        created_by: str
    ) -> Dict:
        """Create a new knowledge article"""
        now = datetime.now(timezone.utc).isoformat()
        
        article = {
            "knowledge_id": f"KB-{uuid.uuid4().hex[:8].upper()}",
            "organization_id": organization_id,
            "scope": KnowledgeScope.TENANT.value if organization_id else KnowledgeScope.GLOBAL.value,
            "knowledge_type": data.get("knowledge_type", KnowledgeType.REPAIR_PROCEDURE.value),
            "title": data.get("title", ""),
            "summary": data.get("summary", ""),
            "content": data.get("content", ""),
            "symptoms": data.get("symptoms", []),
            "dtc_codes": data.get("dtc_codes", []),
            "vehicle_category": data.get("vehicle_category"),
            "vehicle_make": data.get("vehicle_make"),
            "vehicle_model": data.get("vehicle_model"),
            "subsystem": data.get("subsystem"),
            "tags": data.get("tags", []),
            "severity": data.get("severity"),
            "confidence_score": data.get("confidence_score", 0.7),
            "approval_status": ApprovalStatus.DRAFT.value,
            "created_by": created_by,
            "version": 1,
            "created_at": now,
            "updated_at": now,
            "source_type": data.get("source_type"),
            "source_id": data.get("source_id")
        }
        
        await self.knowledge_collection.insert_one(article)
        
        logger.info(f"Created knowledge article: {article['knowledge_id']}")
        return article
    
    async def create_failure_card(
        self,
        data: Dict[str, Any],
        organization_id: Optional[str],
        created_by: str
    ) -> Dict:
        """Create a new failure card"""
        now = datetime.now(timezone.utc).isoformat()
        
        # First create the knowledge article
        article_data = {
            "knowledge_type": KnowledgeType.FAILURE_CARD.value,
            "title": data.get("problem_title", ""),
            "summary": data.get("problem_description", "")[:200],
            "content": data.get("problem_description", ""),
            "symptoms": data.get("symptoms", []),
            "dtc_codes": data.get("dtc_codes", []),
            "vehicle_make": data.get("vehicle_make"),
            "vehicle_model": data.get("vehicle_model"),
            "subsystem": data.get("subsystem"),
            "source_type": "failure_card"
        }
        
        article = await self.create_knowledge_article(article_data, organization_id, created_by)
        
        # Then create the failure card
        card = {
            "failure_card_id": f"FC-{uuid.uuid4().hex[:8].upper()}",
            "knowledge_id": article["knowledge_id"],
            "organization_id": organization_id,
            "scope": KnowledgeScope.TENANT.value if organization_id else KnowledgeScope.GLOBAL.value,
            "problem_title": data.get("problem_title", ""),
            "problem_description": data.get("problem_description", ""),
            "symptoms": data.get("symptoms", []),
            "dtc_codes": data.get("dtc_codes", []),
            "error_messages": data.get("error_messages", []),
            "vehicle_category": data.get("vehicle_category"),
            "vehicle_make": data.get("vehicle_make"),
            "vehicle_model": data.get("vehicle_model"),
            "subsystem": data.get("subsystem"),
            "component": data.get("component"),
            "preliminary_checks": data.get("preliminary_checks", []),
            "diagnostic_steps": data.get("diagnostic_steps", []),
            "test_points": data.get("test_points", []),
            "probable_causes": data.get("probable_causes", []),
            "fix_procedures": data.get("fix_procedures", []),
            "parts_required": data.get("parts_required", []),
            "tools_required": data.get("tools_required", []),
            "estimated_repair_time": data.get("estimated_repair_time"),
            "safety_warnings": data.get("safety_warnings", []),
            "ppe_required": data.get("ppe_required", []),
            "high_voltage_involved": data.get("high_voltage_involved", False),
            "escalation_triggers": data.get("escalation_triggers", []),
            "expert_notes": data.get("expert_notes"),
            "confidence_score": data.get("confidence_score", 0.7),
            "approval_status": ApprovalStatus.DRAFT.value,
            "created_at": now,
            "updated_at": now
        }
        
        await self.failure_cards_collection.insert_one(card)
        
        logger.info(f"Created failure card: {card['failure_card_id']}")
        return card
    
    async def create_failure_card_from_ticket(
        self,
        ticket: Dict,
        resolution_notes: str,
        organization_id: str,
        created_by: str
    ) -> Dict:
        """Create a failure card draft from a resolved ticket"""
        data = {
            "problem_title": ticket.get("subject", ticket.get("title", "Resolved Issue")),
            "problem_description": ticket.get("description", ""),
            "symptoms": ticket.get("symptoms", []),
            "dtc_codes": ticket.get("dtc_codes") or ticket.get("error_codes_reported", []),
            "vehicle_make": ticket.get("vehicle_make"),
            "vehicle_model": ticket.get("vehicle_model"),
            "subsystem": ticket.get("category"),
            "fix_procedures": [{"step": 1, "description": resolution_notes}],
            "source_type": "resolved_ticket",
            "source_id": ticket.get("ticket_id")
        }
        
        return await self.create_failure_card(data, organization_id, created_by)
    
    # ==================== APPROVAL WORKFLOW ====================
    
    async def approve_knowledge(
        self,
        knowledge_id: str,
        approved_by: str,
        organization_id: Optional[str] = None
    ) -> bool:
        """Approve a knowledge article"""
        now = datetime.now(timezone.utc).isoformat()
        
        query = {"knowledge_id": knowledge_id}
        if organization_id:
            query["organization_id"] = organization_id
        
        result = await self.knowledge_collection.update_one(
            query,
            {"$set": {
                "approval_status": ApprovalStatus.APPROVED.value,
                "approved_by": approved_by,
                "approved_at": now,
                "updated_at": now
            }}
        )
        
        if result.modified_count > 0:
            # Also update linked failure card if exists
            await self.failure_cards_collection.update_one(
                {"knowledge_id": knowledge_id},
                {"$set": {
                    "approval_status": ApprovalStatus.APPROVED.value,
                    "updated_at": now
                }}
            )
            logger.info(f"Approved knowledge: {knowledge_id}")
            return True
        
        return False
    
    async def reject_knowledge(
        self,
        knowledge_id: str,
        rejected_by: str,
        reason: str,
        organization_id: Optional[str] = None
    ) -> bool:
        """Reject a knowledge article"""
        now = datetime.now(timezone.utc).isoformat()
        
        query = {"knowledge_id": knowledge_id}
        if organization_id:
            query["organization_id"] = organization_id
        
        result = await self.knowledge_collection.update_one(
            query,
            {"$set": {
                "approval_status": ApprovalStatus.REJECTED.value,
                "rejection_reason": reason,
                "rejected_by": rejected_by,
                "updated_at": now
            }}
        )
        
        return result.modified_count > 0
    
    # ==================== STATISTICS ====================
    
    async def get_knowledge_stats(
        self,
        organization_id: Optional[str] = None
    ) -> Dict:
        """Get knowledge base statistics"""
        query = {}
        if organization_id:
            query["$or"] = [
                {"scope": KnowledgeScope.GLOBAL.value},
                {"organization_id": organization_id}
            ]
        
        total = await self.knowledge_collection.count_documents(query)
        approved = await self.knowledge_collection.count_documents({**query, "approval_status": ApprovalStatus.APPROVED.value})
        pending = await self.knowledge_collection.count_documents({**query, "approval_status": ApprovalStatus.PENDING.value})
        
        failure_cards = await self.failure_cards_collection.count_documents(query)
        error_codes = await self.error_codes_collection.count_documents({})
        
        return {
            "total_articles": total,
            "approved": approved,
            "pending": pending,
            "failure_cards": failure_cards,
            "error_codes": error_codes
        }
