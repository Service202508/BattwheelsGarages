"""
Battwheels Knowledge Brain - AI Guidance Service
Technician-grade EFI guidance with Hinglish output and visual specs
"""

import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import motor.motor_asyncio
from dataclasses import dataclass
from enum import Enum

from services.llm_provider import LLMProviderFactory, LLMProviderType
from services.knowledge_store_service import KnowledgeStoreService
from services.feature_flags import FeatureFlagService

logger = logging.getLogger(__name__)


class GuidanceMode(str, Enum):
    QUICK = "quick"  # 60-90 seconds read
    DEEP = "deep"    # Full decision-tree


class GuidanceConfidence(str, Enum):
    HIGH = "high"      # 3+ matching sources
    MEDIUM = "medium"  # 1-2 matching sources
    LOW = "low"        # No matching sources - requires ask-back


@dataclass
class GuidanceContext:
    """Context extracted from Job Card for guidance generation"""
    ticket_id: str
    organization_id: str
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    symptoms: List[str] = None
    dtc_codes: List[str] = None
    category: str = "general"
    description: str = ""
    last_repair_notes: Optional[str] = None
    battery_soc: Optional[float] = None
    odometer: Optional[int] = None
    technician_notes: Optional[str] = None
    ask_back_answers: Dict[str, Any] = None


# ==================== HINGLISH PROMPT TEMPLATES ====================

HINGLISH_SYSTEM_PROMPT = """You are an expert EV Service Technician AI Assistant for Battwheels, India's leading EV service company.

**OUTPUT LANGUAGE**: Write in Hinglish (Hindi-English mix) that Indian shop-floor technicians understand.
- Use short sentences
- Use common terms: "connector loose", "wiring check karo", "multimeter se measure karo", "SOC", "BMS", "MCU"
- Mix Hindi + English naturally: "Pehle HV isolation karo, phir connector seating check karo"
- Explain DTC meaning in 1 line max
- Use bullet points and numbered steps

**SAFETY RULES** (NEVER skip these):
1. ALWAYS start with HV isolation steps for battery/motor/charger issues
2. List required PPE (safety gloves, insulated tools, etc.)
3. If high voltage involved, add ⚠️ WARNING clearly

**CONFIDENCE RULES**:
- If you have matching Failure Cards/sources: provide confident diagnosis
- If sources are weak/missing: say "Insufficient sources - safe checklist below" and provide basic checks + ask-back questions
- NEVER guess without evidence

**OUTPUT FORMAT** (follow exactly):
## 🛡️ Safety First
[PPE + isolation steps in Hinglish]

## 🔍 Symptom Summary  
[Summarize reported symptoms]

## 📋 Step-by-Step Guide
1. [Step with expected value/result]
2. [Step with expected value/result]
...

## 🎯 Probable Causes
[Ranked list with confidence %]

## 🛠️ Recommended Fix
[Parts/labour suggestions]

## 📚 Sources Used
[List of Failure Card IDs/manual refs]
"""

QUICK_MODE_INSTRUCTIONS = """
**MODE: QUICK (60-90 second read)**
- Maximum 5-7 diagnostic steps
- Each step: action + expected value + pass/fail
- No lengthy explanations
- Bullet points only
"""

DEEP_MODE_INSTRUCTIONS = """
**MODE: DEEP (Full decision tree)**
- Include branching logic: "Agar X hai, toh Y karo. Agar nahi, toh Z check karo"
- Provide measurement values and tolerances
- Include test point locations
- Add troubleshooting flowchart logic
"""

ASK_BACK_PROMPT = """Based on the limited information provided, I need more details to give accurate guidance.

**Required Information:**
{questions}

Please answer these questions so I can provide precise diagnostic steps.

**In the meantime, follow this SAFE CHECKLIST:**
1. ⚠️ HV system isolation confirm karo
2. Visual inspection: loose connectors, damaged wires, burn marks
3. 12V auxiliary battery voltage check karo (should be 12.4V+)
4. Any error codes/warning lights note karo
5. Last service date aur work done verify karo

**Note:** Ye general checklist hai. Specific guidance ke liye upar ke questions answer karo.
"""


class AIGuidanceService:
    """
    AI Guidance service for technician-grade diagnostic assistance.
    Generates Hinglish output with visual specs and estimate suggestions.
    """
    
    def __init__(self, db: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.knowledge_store = KnowledgeStoreService(db)
        self.feature_flags = FeatureFlagService(db)
        self.guidance_collection = db.ai_guidance_snapshots
        self.feedback_collection = db.ai_guidance_feedback
    
    async def is_enabled(self, organization_id: str) -> bool:
        """Check if EFI Guidance Layer is enabled for tenant"""
        return await self.feature_flags.is_feature_enabled(
            organization_id, "efi_guidance_layer_enabled"
        )
    
    async def generate_guidance(
        self,
        context: GuidanceContext,
        mode: GuidanceMode = GuidanceMode.QUICK,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate EFI guidance for a Job Card/Ticket.
        
        Returns structured guidance with:
        - guidance_text (Hinglish)
        - diagram_spec (Mermaid or JSON)
        - charts_spec (JSON for micro-charts)
        - estimate_suggestions
        - sources
        - confidence
        - ask_back_questions (if insufficient data)
        """
        # Check feature flag
        if not await self.is_enabled(context.organization_id):
            return {
                "enabled": False,
                "message": "EFI Guidance Layer is not enabled for your organization."
            }
        
        # Generate context hash for caching
        context_hash = self._generate_context_hash(context)
        
        # Check for cached guidance (unless force regenerate)
        if not force_regenerate:
            cached = await self._get_cached_guidance(
                context.ticket_id, context_hash, mode
            )
            if cached:
                return cached
        
        # Retrieve relevant knowledge
        retrieved_docs, sources = await self._retrieve_knowledge(context)
        
        # Determine confidence level
        confidence = self._determine_confidence(sources)
        
        # Check if we need ask-back
        missing_info = self._check_missing_info(context)
        needs_ask_back = confidence == GuidanceConfidence.LOW or len(missing_info) > 2
        
        # Generate guidance
        if needs_ask_back and not context.ask_back_answers:
            # Generate ask-back response with safe checklist
            guidance_result = await self._generate_ask_back_response(
                context, missing_info
            )
        else:
            # Generate full guidance
            guidance_result = await self._generate_full_guidance(
                context, mode, retrieved_docs, sources, confidence
            )
        
        # Generate visual specs
        diagram_spec = await self._generate_diagram_spec(context, guidance_result)
        charts_spec = await self._generate_charts_spec(context, guidance_result, sources)
        
        # Generate estimate suggestions
        estimate_suggestions = await self._generate_estimate_suggestions(
            context, guidance_result
        )
        
        # Build response
        response = {
            "enabled": True,
            "guidance_id": f"GD-{uuid.uuid4().hex[:8].upper()}",
            "ticket_id": context.ticket_id,
            "mode": mode.value,
            "confidence": confidence.value,
            "guidance_text": guidance_result.get("text", ""),
            "safety_block": guidance_result.get("safety_block", ""),
            "symptom_summary": guidance_result.get("symptom_summary", ""),
            "diagnostic_steps": guidance_result.get("diagnostic_steps", []),
            "probable_causes": guidance_result.get("probable_causes", []),
            "recommended_fix": guidance_result.get("recommended_fix", ""),
            "diagram_spec": diagram_spec,
            "charts_spec": charts_spec,
            "estimate_suggestions": estimate_suggestions,
            "sources": [s.model_dump() if hasattr(s, 'model_dump') else s for s in sources],
            "needs_ask_back": needs_ask_back,
            "ask_back_questions": missing_info if needs_ask_back else [],
            "context_hash": context_hash,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache the guidance
        await self._cache_guidance(response)
        
        return response
    
    async def _retrieve_knowledge(
        self,
        context: GuidanceContext
    ) -> Tuple[List[Dict], List]:
        """Retrieve relevant knowledge from the knowledge base"""
        # Build search query from context
        query_parts = []
        if context.description:
            query_parts.append(context.description)
        if context.symptoms:
            query_parts.extend(context.symptoms)
        if context.technician_notes:
            query_parts.append(context.technician_notes)
        
        query = " ".join(query_parts) if query_parts else "general EV diagnostic"
        
        # Search knowledge base
        results = await self.knowledge_store.search_knowledge(
            query=query,
            organization_id=context.organization_id,
            category=context.category,
            vehicle_make=context.vehicle_make,
            vehicle_model=context.vehicle_model,
            dtc_codes=context.dtc_codes or [],
            symptoms=context.symptoms or [],
            limit=5
        )
        
        # Get failure cards for symptoms
        if context.symptoms:
            failure_cards = await self.knowledge_store.get_failure_cards_for_symptoms(
                symptoms=context.symptoms,
                organization_id=context.organization_id,
                vehicle_make=context.vehicle_make,
                limit=3
            )
            for card in failure_cards:
                if card not in [r[0] for r in results]:
                    results.append((card, 0.8))
        
        # Get DTC info
        if context.dtc_codes:
            for dtc in context.dtc_codes[:3]:
                code_info = await self.knowledge_store.get_error_code_info(
                    dtc, context.organization_id
                )
                if code_info:
                    results.append((code_info, 0.9))
        
        # Format sources
        sources = await self.knowledge_store.format_sources(results)
        
        return [r[0] for r in results], sources
    
    def _determine_confidence(self, sources: List) -> GuidanceConfidence:
        """Determine confidence level based on sources"""
        if len(sources) >= 3:
            avg_relevance = sum(s.relevance_score for s in sources) / len(sources)
            if avg_relevance > 0.7:
                return GuidanceConfidence.HIGH
            return GuidanceConfidence.MEDIUM
        elif len(sources) >= 1:
            return GuidanceConfidence.MEDIUM
        return GuidanceConfidence.LOW
    
    def _check_missing_info(self, context: GuidanceContext) -> List[Dict]:
        """Check what information is missing and generate ask-back questions"""
        questions = []
        
        if not context.vehicle_model:
            questions.append({
                "id": "vehicle_model",
                "question": "Vehicle model kya hai?",
                "question_en": "What is the vehicle model?",
                "type": "select",
                "options": [
                    "Ola S1 Pro", "Ola S1 Air", "Ather 450X", "Ather 450 Plus",
                    "TVS iQube", "Bajaj Chetak", "Hero Electric", "Other"
                ]
            })
        
        if not context.dtc_codes:
            questions.append({
                "id": "dtc_codes",
                "question": "Koi error code dikh raha hai dashboard pe?",
                "question_en": "Any error codes on dashboard?",
                "type": "text",
                "placeholder": "e.g., P0A1F, U0100"
            })
        
        if not context.symptoms or len(context.symptoms) == 0:
            questions.append({
                "id": "symptoms",
                "question": "Main problem kya hai? (multiple select karo)",
                "question_en": "What are the main symptoms?",
                "type": "multi_select",
                "options": [
                    "Vehicle start nahi ho raha",
                    "Battery charge nahi ho rahi",
                    "Motor noise / vibration",
                    "Range kam ho gaya hai",
                    "Warning light on",
                    "Charger connect nahi ho raha",
                    "Display blank / error",
                    "Brake issue",
                    "Other"
                ]
            })
        
        if context.battery_soc is None:
            questions.append({
                "id": "battery_soc",
                "question": "Current battery SOC (%) kitna hai?",
                "question_en": "What is the current battery SOC?",
                "type": "number",
                "min": 0,
                "max": 100
            })
        
        if not context.last_repair_notes:
            questions.append({
                "id": "last_repair",
                "question": "Last service mein kya kaam hua tha?",
                "question_en": "What was done in last service?",
                "type": "text",
                "placeholder": "e.g., battery replaced, firmware update"
            })
        
        return questions[:5]  # Max 5 questions
    
    async def _generate_ask_back_response(
        self,
        context: GuidanceContext,
        missing_info: List[Dict]
    ) -> Dict:
        """Generate ask-back response with safe checklist"""
        questions_text = "\n".join([
            f"- {q['question']}" for q in missing_info
        ])
        
        return {
            "text": ASK_BACK_PROMPT.format(questions=questions_text),
            "safety_block": """⚠️ **SAFETY FIRST - Pehle ye karo:**
1. HV system OFF karo aur isolate karo
2. Safety gloves aur insulated tools use karo
3. 5 minute wait karo capacitor discharge ke liye""",
            "symptom_summary": context.description or "Details pending",
            "diagnostic_steps": [
                {"step": 1, "action": "HV system isolation", "expected": "Isolation confirmed", "hinglish": "HV system isolate karo"},
                {"step": 2, "action": "Visual inspection", "expected": "No visible damage", "hinglish": "Dekho koi damage ya loose connection hai"},
                {"step": 3, "action": "12V battery check", "expected": "12.4V+", "hinglish": "12V battery voltage check karo"},
                {"step": 4, "action": "Note error codes", "expected": "Record all DTCs", "hinglish": "Saare error codes note karo"},
                {"step": 5, "action": "Service history check", "expected": "Review recent work", "hinglish": "Last service details check karo"}
            ],
            "probable_causes": [],
            "recommended_fix": "Specific fix ke liye upar ke questions answer karo."
        }
    
    async def _generate_full_guidance(
        self,
        context: GuidanceContext,
        mode: GuidanceMode,
        retrieved_docs: List[Dict],
        sources: List,
        confidence: GuidanceConfidence
    ) -> Dict:
        """Generate full Hinglish guidance using LLM"""
        # Build context for LLM
        knowledge_context = self._format_knowledge_context(retrieved_docs)
        
        # Build system prompt
        system_prompt = HINGLISH_SYSTEM_PROMPT
        if mode == GuidanceMode.QUICK:
            system_prompt += "\n\n" + QUICK_MODE_INSTRUCTIONS
        else:
            system_prompt += "\n\n" + DEEP_MODE_INSTRUCTIONS
        
        # Build user prompt
        user_prompt = f"""
### JOB CARD CONTEXT ###
Vehicle: {context.vehicle_make or 'Unknown'} {context.vehicle_model or 'Unknown'}
Category: {context.category}
Description: {context.description or 'Not provided'}
Symptoms: {', '.join(context.symptoms) if context.symptoms else 'Not specified'}
DTC Codes: {', '.join(context.dtc_codes) if context.dtc_codes else 'None'}
Battery SOC: {context.battery_soc}% if {context.battery_soc is not None} else 'Unknown'
Technician Notes: {context.technician_notes or 'None'}

### KNOWLEDGE BASE CONTEXT ###
{knowledge_context}

### CONFIDENCE LEVEL ###
{confidence.value} ({len(sources)} sources found)

### TASK ###
Generate diagnostic guidance in Hinglish for the technician.
{"Insufficient sources - provide safe checklist + ask-back questions." if confidence == GuidanceConfidence.LOW else ""}
"""
        
        # Get LLM provider
        llm_config = await self.feature_flags.get_llm_config(context.organization_id)
        provider = LLMProviderFactory.get_provider(
            provider_type=LLMProviderType.GEMINI,
            model=llm_config.get("model")
        )
        
        # Generate response
        response = await provider.generate(
            prompt=user_prompt,
            system_message=system_prompt,
            session_id=f"guidance_{context.ticket_id}_{uuid.uuid4().hex[:6]}"
        )
        
        # Parse the response
        return self._parse_guidance_response(response.content, context)
    
    def _format_knowledge_context(self, docs: List[Dict]) -> str:
        """Format retrieved documents for LLM context"""
        if not docs:
            return "No relevant knowledge base articles found."
        
        context_parts = []
        for i, doc in enumerate(docs[:5], 1):
            doc_type = doc.get("knowledge_type", doc.get("failure_card_id", "Article"))
            title = doc.get("title", doc.get("problem_title", "Unknown"))
            content = doc.get("content", doc.get("problem_description", ""))[:400]
            source_id = doc.get("knowledge_id", doc.get("failure_card_id", f"source_{i}"))
            
            context_parts.append(f"""
**Source [{source_id}]**: {title}
Type: {doc_type}
{content}
---""")
        
        return "\n".join(context_parts)
    
    def _parse_guidance_response(
        self,
        response_text: str,
        context: GuidanceContext
    ) -> Dict:
        """Parse LLM response into structured format"""
        result = {
            "text": response_text,
            "safety_block": "",
            "symptom_summary": context.description or "",
            "diagnostic_steps": [],
            "probable_causes": [],
            "recommended_fix": ""
        }
        
        # Extract Safety First block
        if "## 🛡️ Safety First" in response_text:
            start = response_text.find("## 🛡️ Safety First")
            end = response_text.find("##", start + 20)
            if end == -1:
                end = len(response_text)
            result["safety_block"] = response_text[start:end].strip()
        
        # Extract Symptom Summary
        if "## 🔍 Symptom Summary" in response_text:
            start = response_text.find("## 🔍 Symptom Summary")
            end = response_text.find("##", start + 20)
            if end == -1:
                end = len(response_text)
            result["symptom_summary"] = response_text[start:end].replace("## 🔍 Symptom Summary", "").strip()
        
        # Extract Step-by-Step Guide
        if "## 📋 Step-by-Step Guide" in response_text:
            start = response_text.find("## 📋 Step-by-Step Guide")
            end = response_text.find("##", start + 20)
            if end == -1:
                end = len(response_text)
            steps_text = response_text[start:end]
            
            # Parse numbered steps
            import re
            step_pattern = r'(\d+)\.\s*(.+?)(?=\d+\.|$)'
            matches = re.findall(step_pattern, steps_text, re.DOTALL)
            for num, step_text in matches:
                result["diagnostic_steps"].append({
                    "step": int(num),
                    "action": step_text.strip()[:200],
                    "hinglish": step_text.strip()[:200]
                })
        
        # Extract Probable Causes
        if "## 🎯 Probable Causes" in response_text:
            start = response_text.find("## 🎯 Probable Causes")
            end = response_text.find("##", start + 20)
            if end == -1:
                end = len(response_text)
            causes_text = response_text[start:end]
            
            # Parse causes (simple extraction)
            lines = causes_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    # Try to extract percentage
                    import re
                    match = re.search(r'(\d+)%', line)
                    confidence = int(match.group(1)) if match else 50
                    cause = re.sub(r'\d+%', '', line).strip(' -•')
                    if cause:
                        result["probable_causes"].append({
                            "cause": cause,
                            "confidence": confidence
                        })
        
        # Extract Recommended Fix
        if "## 🛠️ Recommended Fix" in response_text:
            start = response_text.find("## 🛠️ Recommended Fix")
            end = response_text.find("##", start + 20)
            if end == -1:
                end = len(response_text)
            result["recommended_fix"] = response_text[start:end].replace("## 🛠️ Recommended Fix", "").strip()
        
        return result
    
    async def _generate_diagram_spec(
        self,
        context: GuidanceContext,
        guidance_result: Dict
    ) -> Dict:
        """Generate Mermaid diagram specification"""
        steps = guidance_result.get("diagnostic_steps", [])
        
        if not steps or len(steps) < 2:
            return None
        
        # Build simple flowchart
        mermaid_lines = ["graph TD"]
        
        for i, step in enumerate(steps[:7]):  # Max 7 nodes
            node_id = f"S{i+1}"
            action = step.get("action", step.get("hinglish", ""))[:40]
            
            if i == 0:
                mermaid_lines.append(f'    START([Start]) --> {node_id}["{action}"]')
            else:
                prev_id = f"S{i}"
                mermaid_lines.append(f'    {prev_id} --> {node_id}["{action}"]')
        
        # Add end node
        if steps:
            last_id = f"S{min(len(steps), 7)}"
            mermaid_lines.append(f'    {last_id} --> END([Complete])')
        
        # Add styling
        mermaid_lines.extend([
            "    classDef default fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#fff",
            "    classDef start fill:#10b981,stroke:#10b981,color:#fff",
            "    classDef end fill:#10b981,stroke:#10b981,color:#fff"
        ])
        
        return {
            "type": "mermaid",
            "code": "\n".join(mermaid_lines),
            "title": "Diagnostic Flow"
        }
    
    async def _generate_charts_spec(
        self,
        context: GuidanceContext,
        guidance_result: Dict,
        sources: List
    ) -> Dict:
        """Generate chart specifications for micro-visualizations"""
        charts = {}
        
        # SOC Gauge (if SOC available)
        if context.battery_soc is not None:
            soc = context.battery_soc
            color = "#10b981" if soc > 30 else "#f59e0b" if soc > 10 else "#ef4444"
            charts["soc_gauge"] = {
                "type": "gauge",
                "title": "Battery SOC",
                "value": soc,
                "max": 100,
                "unit": "%",
                "color": color,
                "zones": [
                    {"min": 0, "max": 10, "color": "#ef4444"},
                    {"min": 10, "max": 30, "color": "#f59e0b"},
                    {"min": 30, "max": 100, "color": "#10b981"}
                ]
            }
        
        # Probable Causes Bar Chart
        causes = guidance_result.get("probable_causes", [])
        if causes:
            charts["causes_chart"] = {
                "type": "horizontal_bar",
                "title": "Probable Causes",
                "data": [
                    {"label": c["cause"][:30], "value": c["confidence"]}
                    for c in causes[:5]
                ],
                "max": 100,
                "unit": "%"
            }
        
        # Time to Check (estimated)
        steps = guidance_result.get("diagnostic_steps", [])
        if steps:
            # Estimate 2-5 minutes per step
            total_minutes = len(steps) * 3
            charts["time_estimate"] = {
                "type": "info",
                "title": "Estimated Time",
                "value": total_minutes,
                "unit": "min",
                "steps_count": len(steps)
            }
        
        # Source confidence
        if sources:
            avg_relevance = sum(s.relevance_score for s in sources) / len(sources) * 100
            charts["confidence_indicator"] = {
                "type": "confidence",
                "title": "Source Confidence",
                "value": round(avg_relevance),
                "sources_count": len(sources),
                "unit": "%"
            }
        
        return charts if charts else None
    
    async def _generate_estimate_suggestions(
        self,
        context: GuidanceContext,
        guidance_result: Dict
    ) -> List[Dict]:
        """Generate parts/labour suggestions for estimate"""
        suggestions = []
        
        # Extract parts from guidance
        fix_text = guidance_result.get("recommended_fix", "")
        text_lower = fix_text.lower()
        
        # Common parts mapping (simplified)
        parts_keywords = {
            "battery": {"name": "Battery Pack", "category": "battery", "estimated_cost": 15000},
            "bms": {"name": "BMS Module", "category": "battery", "estimated_cost": 8000},
            "charger": {"name": "Onboard Charger", "category": "charger", "estimated_cost": 5000},
            "connector": {"name": "HV Connector", "category": "electrical", "estimated_cost": 500},
            "fuse": {"name": "HV Fuse", "category": "electrical", "estimated_cost": 200},
            "motor controller": {"name": "Motor Controller", "category": "motor", "estimated_cost": 12000},
            "dc-dc": {"name": "DC-DC Converter", "category": "electrical", "estimated_cost": 3000},
            "throttle": {"name": "Throttle Sensor", "category": "electrical", "estimated_cost": 800},
            "display": {"name": "Dashboard Display", "category": "electrical", "estimated_cost": 2500},
        }
        
        for keyword, part_info in parts_keywords.items():
            if keyword in text_lower:
                suggestions.append({
                    "type": "part",
                    "name": part_info["name"],
                    "category": part_info["category"],
                    "quantity": 1,
                    "estimated_cost": part_info["estimated_cost"],
                    "confidence": "medium"
                })
        
        # Add labour based on category
        labour_mapping = {
            "battery": {"name": "Battery System Diagnosis", "hours": 1, "rate": 500},
            "motor": {"name": "Motor/Controller Repair", "hours": 2, "rate": 500},
            "electrical": {"name": "Electrical Diagnosis", "hours": 1, "rate": 500},
            "charger": {"name": "Charger System Service", "hours": 1.5, "rate": 500},
        }
        
        if context.category in labour_mapping:
            labour = labour_mapping[context.category]
            suggestions.append({
                "type": "labour",
                "name": labour["name"],
                "hours": labour["hours"],
                "rate": labour["rate"],
                "estimated_cost": labour["hours"] * labour["rate"]
            })
        
        return suggestions[:10]  # Max 10 suggestions
    
    def _generate_context_hash(self, context: GuidanceContext) -> str:
        """
        Generate deterministic hash for idempotency.
        Same input context = same hash = can reuse existing snapshot.
        """
        components = [
            context.ticket_id,
            context.vehicle_make or "",
            context.vehicle_model or "",
            context.vehicle_variant or "",
            context.category,
            context.description[:200] if context.description else "",
            ",".join(sorted(context.symptoms or [])),
            ",".join(sorted(context.dtc_codes or [])),
            str(context.ask_back_answers) if context.ask_back_answers else ""
        ]
        hash_input = "|".join(components).lower().strip()
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    async def _get_cached_guidance(
        self,
        ticket_id: str,
        context_hash: str,
        mode: GuidanceMode
    ) -> Optional[Dict]:
        """
        Get cached guidance snapshot if available.
        Implements idempotency - reuse if context unchanged.
        """
        cached = await self.guidance_collection.find_one({
            "ticket_id": ticket_id,
            "input_context_hash": context_hash,
            "mode": mode.value,
            "status": "active"  # Only return active snapshots
        }, {"_id": 0})
        
        if cached:
            # Update view count
            await self.guidance_collection.update_one(
                {"snapshot_id": cached.get("snapshot_id", cached.get("guidance_id"))},
                {
                    "$inc": {"view_count": 1},
                    "$set": {"last_viewed_at": datetime.now(timezone.utc).isoformat()}
                }
            )
            logger.info(f"Reusing cached guidance snapshot for ticket {ticket_id}")
        
        return cached
    
    async def _cache_guidance(self, guidance: Dict, context: GuidanceContext):
        """
        Cache generated guidance as a versioned snapshot.
        Supersedes any existing active snapshot for same ticket/mode.
        """
        snapshot_id = f"GS-{uuid.uuid4().hex[:12].upper()}"
        
        # Mark existing active snapshots as superseded
        await self.guidance_collection.update_many(
            {
                "ticket_id": guidance["ticket_id"],
                "mode": guidance["mode"],
                "status": "active"
            },
            {
                "$set": {
                    "status": "superseded",
                    "superseded_by": snapshot_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Get version number
        version_count = await self.guidance_collection.count_documents({
            "ticket_id": guidance["ticket_id"],
            "mode": guidance["mode"]
        })
        
        # Create snapshot document
        snapshot_doc = {
            **guidance,
            "snapshot_id": snapshot_id,
            "input_context_hash": guidance.get("context_hash"),
            "version": version_count + 1,
            "status": "active",
            "organization_id": context.organization_id,
            "vehicle_make": context.vehicle_make,
            "vehicle_model": context.vehicle_model,
            "vehicle_variant": context.vehicle_variant,
            "symptoms": context.symptoms or [],
            "dtc_codes": context.dtc_codes or [],
            "category": context.category,
            "description": context.description,
            "feedback_count": 0,
            "helpful_count": 0,
            "not_helpful_count": 0,
            "unsafe_count": 0,
            "view_count": 1,
            "regenerated_count": 0
        }
        
        await self.guidance_collection.insert_one(snapshot_doc)
        logger.info(f"Created guidance snapshot {snapshot_id} v{version_count + 1} for ticket {guidance['ticket_id']}")
    
    async def get_snapshot_info(self, ticket_id: str, mode: str = "quick") -> Optional[Dict]:
        """
        Get snapshot info to determine if regeneration is needed.
        Used by frontend to show "Regenerate" button only when context changed.
        """
        snapshot = await self.guidance_collection.find_one(
            {
                "ticket_id": ticket_id,
                "mode": mode,
                "status": "active"
            },
            {
                "_id": 0,
                "snapshot_id": 1,
                "guidance_id": 1,
                "input_context_hash": 1,
                "version": 1,
                "created_at": 1,
                "feedback_count": 1,
                "helpful_count": 1
            }
        )
        return snapshot
    
    async def check_context_changed(self, context: GuidanceContext, mode: str = "quick") -> Dict:
        """
        Check if context has changed since last snapshot.
        Returns whether regeneration is needed.
        """
        current_hash = self._generate_context_hash(context)
        
        existing = await self.guidance_collection.find_one(
            {
                "ticket_id": context.ticket_id,
                "mode": mode,
                "status": "active"
            },
            {"_id": 0, "input_context_hash": 1, "version": 1, "created_at": 1}
        )
        
        if not existing:
            return {"needs_regeneration": True, "reason": "no_existing_snapshot"}
        
        if existing.get("input_context_hash") != current_hash:
            return {
                "needs_regeneration": True,
                "reason": "context_changed",
                "existing_version": existing.get("version", 1)
            }
        
        return {
            "needs_regeneration": False,
            "reason": "context_unchanged",
            "existing_version": existing.get("version", 1),
            "snapshot_created_at": existing.get("created_at")
        }
    
    async def submit_feedback(
        self,
        guidance_id: str,
        ticket_id: str,
        organization_id: str,
        user_id: str,
        helped: bool,
        unsafe: bool = False,
        step_failed: Optional[int] = None,
        comment: Optional[str] = None,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        correct_diagnosis: Optional[str] = None,
        actual_fix: Optional[str] = None,
        rating: Optional[int] = None
    ) -> bool:
        """
        Submit feedback on guidance quality.
        Feeds into continuous learning loop (Part D).
        """
        feedback_doc = {
            "feedback_id": f"GF-{uuid.uuid4().hex[:12].upper()}",
            "guidance_id": guidance_id,
            "ticket_id": ticket_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "feedback_type": "helpful" if helped else ("unsafe" if unsafe else "not_helpful"),
            "helped": helped,
            "rating": rating,
            "unsafe": unsafe,
            "incorrect": not helped and not unsafe,
            "step_failed": step_failed,
            "comment": comment,
            "correct_diagnosis": correct_diagnosis,
            "actual_fix": actual_fix,
            "processed_for_learning": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.feedback_collection.insert_one(feedback_doc)
        
        # Update guidance snapshot stats
        update_ops = {
            "$inc": {
                "feedback_count": 1,
                "helpful_count": 1 if helped else 0,
                "not_helpful_count": 0 if helped else 1,
                "unsafe_count": 1 if unsafe else 0
            }
        }
        
        # Recalculate average rating if rating provided
        if rating:
            snapshot = await self.guidance_collection.find_one(
                {"guidance_id": guidance_id},
                {"_id": 0, "feedback_count": 1, "avg_rating": 1}
            )
            if snapshot:
                old_avg = snapshot.get("avg_rating", 0)
                old_count = snapshot.get("feedback_count", 0)
                new_avg = ((old_avg * old_count) + rating) / (old_count + 1)
                update_ops["$set"] = {"avg_rating": round(new_avg, 2)}
        
        await self.guidance_collection.update_one(
            {"guidance_id": guidance_id},
            update_ops
        )
        
        # Trigger learning pipeline for negative/unsafe feedback
        if not helped or unsafe:
            await self._queue_for_learning(feedback_doc)
        
        logger.info(f"Recorded guidance feedback: {feedback_doc['feedback_id']} (helped={helped})")
        return True
    
    async def _queue_for_learning(self, feedback: Dict):
        """
        Queue feedback for continuous learning processing.
        Part D - Background learning loop.
        """
        learning_event = {
            "event_id": f"LE-{uuid.uuid4().hex[:8].upper()}",
            "event_type": "guidance_feedback",
            "feedback_id": feedback["feedback_id"],
            "guidance_id": feedback["guidance_id"],
            "ticket_id": feedback["ticket_id"],
            "organization_id": feedback["organization_id"],
            "helped": feedback["helped"],
            "unsafe": feedback["unsafe"],
            "correct_diagnosis": feedback.get("correct_diagnosis"),
            "actual_fix": feedback.get("actual_fix"),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.efi_learning_queue.insert_one(learning_event)
        logger.info(f"Queued feedback for learning: {learning_event['event_id']}")
    
    async def update_context_with_answers(
        self,
        ticket_id: str,
        answers: Dict[str, Any]
    ) -> bool:
        """Update ticket context with ask-back answers"""
        # Store answers in ticket
        update_data = {"ask_back_answers": answers}
        
        # Map specific fields
        if "vehicle_model" in answers:
            update_data["vehicle_model"] = answers["vehicle_model"]
        if "dtc_codes" in answers:
            update_data["dtc_codes"] = answers["dtc_codes"].split(",") if isinstance(answers["dtc_codes"], str) else answers["dtc_codes"]
        if "symptoms" in answers:
            update_data["symptoms"] = answers["symptoms"]
        if "battery_soc" in answers:
            update_data["battery_soc"] = float(answers["battery_soc"])
        
        await self.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": update_data}
        )
        
        return True
    
    async def get_feedback_summary(self, guidance_id: str) -> Dict:
        """Get feedback summary for a guidance snapshot"""
        pipeline = [
            {"$match": {"guidance_id": guidance_id}},
            {"$group": {
                "_id": None,
                "total_feedback": {"$sum": 1},
                "helpful_count": {"$sum": {"$cond": ["$helped", 1, 0]}},
                "unsafe_count": {"$sum": {"$cond": ["$unsafe", 1, 0]}},
                "avg_rating": {"$avg": "$rating"}
            }}
        ]
        
        result = await self.feedback_collection.aggregate(pipeline).to_list(1)
        
        if result:
            data = result[0]
            return {
                "total_feedback": data.get("total_feedback", 0),
                "helpful_rate": round(
                    data.get("helpful_count", 0) / max(data.get("total_feedback", 1), 1) * 100, 1
                ),
                "unsafe_count": data.get("unsafe_count", 0),
                "avg_rating": round(data.get("avg_rating") or 0, 1)
            }
        
        return {"total_feedback": 0, "helpful_rate": 0, "unsafe_count": 0, "avg_rating": 0}
