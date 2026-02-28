"""
Battwheels Knowledge Brain - AI Assist Service
RAG-based AI assistance with source citations and structured responses
"""

import os
import uuid
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import motor.motor_asyncio

from models.knowledge_brain import (
    AIQueryRequest, AIQueryResponse, AISource, AIFeedback,
    EscalationRequest, Severity
)
from services.knowledge_store_service import KnowledgeStoreService

logger = logging.getLogger(__name__)


class AIAssistService:
    """
    AI Assistance service with RAG (Retrieval-Augmented Generation)
    Provides technician-grade diagnostic assistance with source citations
    """
    
    def __init__(self, db: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.knowledge_store = KnowledgeStoreService(db)
        self.queries_collection = db.ai_queries
        self.feedback_collection = db.ai_feedback
        self.escalations_collection = db.ai_escalations
        self.config_collection = db.tenant_ai_config
    
    async def get_tenant_config(self, organization_id: str) -> Dict:
        """Get tenant AI configuration"""
        config = await self.config_collection.find_one(
            {"organization_id": organization_id},
            {"_id": 0}
        )
        
        if not config:
            # Default config
            config = {
                "organization_id": organization_id,
                "ai_assist_enabled": True,
                "zendesk_enabled": False,
                "knowledge_ingestion_enabled": True,
                "auto_suggest_enabled": True,
                "daily_query_limit": 1000,
                "queries_today": 0
            }
        
        return config
    
    async def process_query(
        self,
        request: AIQueryRequest
    ) -> AIQueryResponse:
        """
        Main entry point for AI assistance queries.
        Implements RAG pipeline: Retrieve → Augment → Generate
        """
        start_time = time.time()
        query_id = f"AIQ-{uuid.uuid4().hex[:12].upper()}"
        
        organization_id = request.organization_id
        if not organization_id:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="Organization context required for AI assistance"
            )
        
        # Check tenant config and limits
        config = await self.get_tenant_config(organization_id)
        if not config.get("ai_assist_enabled", True):
            return AIQueryResponse(
                response="AI assistance is not enabled for your organization.",
                ai_enabled=False,
                query_id=query_id,
                category=request.category
            )
        
        try:
            # Step 1: Retrieve relevant knowledge
            retrieved_docs, sources = await self._retrieve_knowledge(request)
            
            # Step 2: Build context-aware prompt
            prompt, system_message = await self._build_rag_prompt(
                request, retrieved_docs
            )
            
            # Step 3: Generate response with LLM (using swappable provider)
            response_text = await self._generate_response(
                prompt, system_message, request.category, organization_id
            )
            
            # Step 4: Parse and structure response
            structured_response = self._parse_response(response_text, sources)
            
            # Step 5: Log query for analytics
            await self._log_query(query_id, request, structured_response)
            
            response_time = int((time.time() - start_time) * 1000)
            
            return AIQueryResponse(
                response=response_text,
                ai_enabled=True,
                category=request.category,
                sources=sources,
                sources_used=len(sources),
                diagnosis_summary=structured_response.get("diagnosis_summary"),
                confidence_level=structured_response.get("confidence_level", "medium"),
                safety_warnings=structured_response.get("safety_warnings", []),
                diagnostic_steps=structured_response.get("diagnostic_steps", []),
                probable_causes=structured_response.get("probable_causes", []),
                recommended_parts=structured_response.get("recommended_parts", []),
                escalation_recommended=structured_response.get("escalation_recommended", False),
                escalation_reason=structured_response.get("escalation_reason"),
                estimate_suggestions=structured_response.get("estimate_suggestions", []),
                query_id=query_id,
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"AI assist error: {e}")
            return AIQueryResponse(
                response="I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support.",
                ai_enabled=False,
                query_id=query_id,
                category=request.category,
                escalation_recommended=True,
                escalation_reason="System error - manual review recommended"
            )
    
    async def _retrieve_knowledge(
        self,
        request: AIQueryRequest
    ) -> tuple[List[Dict], List[AISource]]:
        """Retrieve relevant knowledge from the knowledge base"""
        organization_id = request.organization_id
        if not organization_id:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="Organization context required for AI assistance"
            )
        
        # Search knowledge base
        results = await self.knowledge_store.search_knowledge(
            query=request.query,
            organization_id=organization_id,
            category=request.category,
            vehicle_make=request.vehicle_make,
            vehicle_model=request.vehicle_model,
            dtc_codes=request.dtc_codes,
            symptoms=request.symptoms,
            limit=5
        )
        
        # Get failure cards if symptoms provided
        if request.symptoms:
            failure_cards = await self.knowledge_store.get_failure_cards_for_symptoms(
                symptoms=request.symptoms,
                organization_id=organization_id,
                vehicle_make=request.vehicle_make,
                limit=3
            )
            for card in failure_cards:
                if card not in [r[0] for r in results]:
                    results.append((card, 0.8))
        
        # Get error code info if DTC codes provided
        for dtc in request.dtc_codes[:3]:  # Limit to 3 codes
            code_info = await self.knowledge_store.get_error_code_info(
                dtc, organization_id
            )
            if code_info:
                results.append((code_info, 0.9))
        
        # Format sources for citation
        sources = await self.knowledge_store.format_sources(results)
        
        return [r[0] for r in results], sources
    
    async def _build_rag_prompt(
        self,
        request: AIQueryRequest,
        retrieved_docs: List[Dict]
    ) -> tuple[str, str]:
        """Build the RAG prompt with retrieved context"""
        
        # Category-specific focus
        category_prompts = {
            "battery": "Focus on battery system issues: BMS errors, cell degradation, charging problems, thermal management, and state of charge issues.",
            "motor": "Focus on motor and drivetrain issues: BLDC/PMSM motors, motor controllers, inverters, regenerative braking, and torque delivery problems.",
            "electrical": "Focus on electrical system issues: wiring faults, connector problems, fuse failures, relay issues, and high-voltage safety.",
            "diagnosis": "Focus on systematic fault diagnosis: symptom analysis, error code interpretation, test procedures, and root cause analysis.",
            "charger": "Focus on charging system issues: onboard chargers, DC fast charging, CCS/CHAdeMO protocols, and charge port problems.",
            "general": "Provide comprehensive EV service guidance covering all systems."
        }
        
        category_focus = category_prompts.get(request.category, category_prompts["general"])
        
        # Build system message
        system_message = f"""You are an expert EV Service Technician AI Assistant for Battwheels, India's leading EV service company.

**Your Role**: Provide technician-grade diagnostic assistance with actionable, step-by-step guidance.

**Your Expertise**:
- Electric 2-wheelers: Ola S1, Ather 450X, TVS iQube, Hero Electric, Bajaj Chetak
- Electric 3-wheelers: Mahindra Treo, Piaggio Ape E-City, Euler HiLoad
- Electric 4-wheelers: Tata Nexon EV, MG ZS EV, Hyundai Kona Electric
- Battery Systems: Li-ion (NMC, LFP), BMS diagnostics, thermal management
- Motor Systems: BLDC, PMSM, controllers, inverters
- Charging: AC/DC chargers, CCS, CHAdeMO, Type 2

**Current Focus**: {category_focus}

**CRITICAL RULES**:
1. Always prioritize SAFETY - include high-voltage warnings when relevant
2. Provide STEP-BY-STEP procedures with specific measurements and expected values
3. CITE your sources - reference the knowledge base articles provided
4. Include TOOLS and PPE required for each procedure
5. Specify ESCALATION criteria - when the issue needs expert intervention
6. Never guess - if uncertain, recommend further diagnosis or escalation

**Response Structure** (use this format):
## Diagnosis Summary
[Brief hypothesis with confidence level]

## Safety Precautions
[Required PPE and safety checks]

## Diagnostic Steps
[Numbered step-by-step procedure]

## Probable Causes
[Ranked list with likelihood]

## Recommended Fix
[Solution steps with parts/tools]

## Sources
[Reference the knowledge articles used]"""

        # Build user prompt with context
        context_parts = []
        
        # Add retrieved knowledge context
        if retrieved_docs:
            context_parts.append("### KNOWLEDGE BASE CONTEXT ###")
            for i, doc in enumerate(retrieved_docs[:5], 1):
                doc_type = doc.get("knowledge_type", doc.get("failure_card_id", "Article"))
                title = doc.get("title", doc.get("problem_title", "Unknown"))
                content = doc.get("content", doc.get("problem_description", ""))[:500]
                source_id = doc.get("knowledge_id", doc.get("failure_card_id", f"source_{i}"))
                
                context_parts.append(f"""
**Source [{source_id}]**: {title}
Type: {doc_type}
{content}
---""")
        
        # Add vehicle context
        if request.vehicle_make or request.vehicle_model:
            context_parts.append("\n### VEHICLE INFO ###")
            if request.vehicle_make:
                context_parts.append(f"Make: {request.vehicle_make}")
            if request.vehicle_model:
                context_parts.append(f"Model: {request.vehicle_model}")
        
        # Add DTC codes
        if request.dtc_codes:
            context_parts.append("\n### ERROR CODES ###")
            context_parts.append(f"DTC Codes: {', '.join(request.dtc_codes)}")
        
        # Add symptoms
        if request.symptoms:
            context_parts.append("\n### REPORTED SYMPTOMS ###")
            context_parts.append(f"Symptoms: {', '.join(request.symptoms)}")
        
        # Build final prompt
        prompt = "\n".join(context_parts)
        prompt += f"\n\n### TECHNICIAN QUERY ###\n{request.query}"
        
        if not retrieved_docs:
            prompt += "\n\n**Note**: No relevant knowledge base articles found. Provide guidance based on general EV service expertise, and recommend creating a Failure Card if this is a new issue pattern."
        
        return prompt, system_message
    
    async def _generate_response(
        self,
        prompt: str,
        system_message: str,
        category: str,
        organization_id: str = "global"
    ) -> str:
        """
        Generate response using LLM via provider interface.
        Uses swappable LLMProvider for model flexibility.
        """
        from services.llm_provider import LLMProviderFactory, LLMProviderType
        from services.feature_flags import FeatureFlagService
        
        # Get LLM config for tenant (allows per-tenant model selection)
        flag_service = FeatureFlagService(self.db)
        llm_config = await flag_service.get_llm_config(organization_id)
        
        # Get appropriate provider
        provider_map = {
            "gemini": LLMProviderType.GEMINI,
            "openai": LLMProviderType.OPENAI,
            "anthropic": LLMProviderType.ANTHROPIC,
        }
        provider_type = provider_map.get(llm_config["provider"], LLMProviderType.GEMINI)
        
        provider = LLMProviderFactory.get_provider(
            provider_type=provider_type,
            model=llm_config.get("model")
        )
        
        if not provider.is_available():
            raise Exception("LLM service unavailable - API key not configured")
        
        # Generate response
        response = await provider.generate(
            prompt=prompt,
            system_message=system_message,
            session_id=f"kb_rag_{uuid.uuid4().hex[:8]}"
        )
        
        if response.error:
            logger.error(f"LLM generation error: {response.error}")
            raise Exception(f"LLM generation failed: {response.error}")
        
        return response.content
    
    def _parse_response(
        self,
        response_text: str,
        sources: List[AISource]
    ) -> Dict[str, Any]:
        """Parse the LLM response into structured components"""
        result = {
            "diagnosis_summary": None,
            "confidence_level": "medium",
            "safety_warnings": [],
            "diagnostic_steps": [],
            "probable_causes": [],
            "recommended_parts": [],
            "escalation_recommended": False,
            "escalation_reason": None,
            "estimate_suggestions": []
        }
        
        # Extract diagnosis summary
        if "## Diagnosis Summary" in response_text:
            start = response_text.find("## Diagnosis Summary")
            end = response_text.find("##", start + 20)
            if end == -1:
                end = len(response_text)
            result["diagnosis_summary"] = response_text[start+20:end].strip()
        
        # Check for safety warnings
        safety_keywords = ["warning", "caution", "danger", "high voltage", "ppe", "safety"]
        for keyword in safety_keywords:
            if keyword.lower() in response_text.lower():
                # Extract safety lines
                for line in response_text.split('\n'):
                    if keyword.lower() in line.lower() and line.strip():
                        result["safety_warnings"].append(line.strip())
                break
        
        # Check for escalation triggers
        escalation_keywords = ["escalate", "expert required", "specialist", "further diagnosis needed", "unable to determine"]
        for keyword in escalation_keywords:
            if keyword.lower() in response_text.lower():
                result["escalation_recommended"] = True
                result["escalation_reason"] = f"AI detected: {keyword}"
                break
        
        # Determine confidence level
        if sources and len(sources) >= 2:
            avg_relevance = sum(s.relevance_score for s in sources) / len(sources)
            if avg_relevance > 0.85:
                result["confidence_level"] = "high"
            elif avg_relevance > 0.6:
                result["confidence_level"] = "medium"
            else:
                result["confidence_level"] = "low"
        else:
            result["confidence_level"] = "low"
        
        return result
    
    async def _log_query(
        self,
        query_id: str,
        request: AIQueryRequest,
        response_data: Dict
    ):
        """Log query for analytics and improvement"""
        log_entry = {
            "query_id": query_id,
            "organization_id": request.organization_id,
            "user_id": request.user_id,
            "portal_type": request.portal_type,
            "query": request.query,
            "category": request.category,
            "vehicle_make": request.vehicle_make,
            "vehicle_model": request.vehicle_model,
            "dtc_codes": request.dtc_codes,
            "symptoms": request.symptoms,
            "ticket_id": request.ticket_id,
            "confidence_level": response_data.get("confidence_level"),
            "escalation_recommended": response_data.get("escalation_recommended"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.queries_collection.insert_one(log_entry)
    
    async def record_feedback(
        self,
        feedback: AIFeedback
    ) -> bool:
        """Record user feedback on AI response"""
        feedback_doc = {
            "query_id": feedback.query_id,
            "feedback_type": feedback.feedback_type,
            "reason": feedback.reason,
            "missing_info": feedback.missing_info,
            "correct_answer": feedback.correct_answer,
            "user_id": feedback.user_id,
            "organization_id": feedback.organization_id,
            "created_at": feedback.created_at
        }
        
        await self.feedback_collection.insert_one(feedback_doc)
        
        # Update knowledge confidence based on feedback
        query = await self.queries_collection.find_one({"query_id": feedback.query_id})
        if query:
            # Adjust future recommendations based on feedback patterns
            pass
        
        logger.info(f"Recorded feedback for query {feedback.query_id}: {feedback.feedback_type}")
        return True
    
    async def create_escalation(
        self,
        escalation: EscalationRequest
    ) -> Dict:
        """
        Create an escalation for human expert review.
        Uses internal Expert Queue (Zendesk is stubbed).
        """
        from services.expert_queue_service import ExpertQueueService
        
        expert_queue = ExpertQueueService(self.db)
        
        # Create escalation in Expert Queue
        result = await expert_queue.create_escalation(
            query_id=escalation.query_id,
            ticket_id=escalation.ticket_id,
            organization_id=escalation.organization_id,
            original_query=escalation.original_query,
            ai_response=escalation.ai_response,
            sources_checked=escalation.sources_checked,
            vehicle_info=escalation.vehicle_info,
            symptoms=escalation.symptoms,
            dtc_codes=escalation.dtc_codes,
            images=escalation.images,
            documents=escalation.documents,
            urgency=escalation.urgency,
            reason=escalation.reason,
            user_id=escalation.user_id,
            user_name=escalation.user_name
        )
        
        logger.info(f"Created expert queue escalation: {result['escalation_id']}")
        
        return result
    
    async def get_ticket_suggestions(
        self,
        ticket_id: str,
        organization_id: str
    ) -> Dict:
        """Get AI suggestions for a specific ticket"""
        # Get ticket details
        ticket = await self.db.tickets.find_one(
            {"ticket_id": ticket_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not ticket:
            return {"suggestions": [], "error": "Ticket not found"}
        
        # Build query from ticket
        request = AIQueryRequest(
            query=ticket.get("description", ticket.get("subject", "")),
            category=ticket.get("category", "general"),
            ticket_id=ticket_id,
            vehicle_make=ticket.get("vehicle_make"),
            vehicle_model=ticket.get("vehicle_model"),
            dtc_codes=ticket.get("dtc_codes", []),
            symptoms=ticket.get("symptoms", []),
            organization_id=organization_id,
            portal_type="ticket"
        )
        
        response = await self.process_query(request)
        
        return {
            "ticket_id": ticket_id,
            "diagnosis_summary": response.diagnosis_summary,
            "diagnostic_steps": response.diagnostic_steps,
            "probable_causes": response.probable_causes,
            "estimate_suggestions": response.estimate_suggestions,
            "safety_warnings": response.safety_warnings,
            "sources": [s.model_dump() for s in response.sources],
            "confidence_level": response.confidence_level
        }
