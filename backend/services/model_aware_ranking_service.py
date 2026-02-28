"""
Battwheels OS - Model-Aware Ranking Service

Part B of Phase 2 - Model-Aware Ranking (Lean)

Enhances RAG ranking with:
- Model match (high weight)
- DTC match
- Subsystem match
- Symptom similarity
- Historical success rate
- Recency bonus

Output: Top 3 ranked root causes only.
If confidence < 60%: Show safe checklist + escalate suggestion.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


# ==================== RANKING WEIGHTS ====================

class RankingWeight:
    """Configurable ranking weights for model-aware scoring"""
    MODEL_MATCH = 35        # Same vehicle model
    MAKE_MATCH = 15         # Same vehicle make
    DTC_MATCH = 25          # Matching DTC code
    SUBSYSTEM_MATCH = 15    # Same subsystem
    SYMPTOM_SIMILARITY = 20 # Overlapping symptoms
    SUCCESS_RATE = 20       # Historical success rate (0-1 scaled)
    RECENCY_BONUS = 10      # Used recently
    USAGE_BONUS = 5         # Frequently used


class ConfidenceLevel(str, Enum):
    HIGH = "high"       # >= 70%
    MEDIUM = "medium"   # 40-70%
    LOW = "low"         # < 40%


@dataclass
class RankingContext:
    """Context for ranking failure cards"""
    organization_id: str
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    vehicle_category: str = "2W"
    subsystem: Optional[str] = None
    symptoms: List[str] = None
    dtc_codes: List[str] = None
    description: str = ""
    
    def __post_init__(self):
        self.symptoms = self.symptoms or []
        self.dtc_codes = self.dtc_codes or []


@dataclass
class RankedCause:
    """A ranked probable cause"""
    cause: str
    confidence: int  # 0-100
    failure_card_id: Optional[str] = None
    evidence: Optional[str] = None
    ranking_score: float = 0.0
    matching_factors: List[str] = None
    
    def __post_init__(self):
        self.matching_factors = self.matching_factors or []


class ModelAwareRankingService:
    """
    Ranks failure cards and knowledge items based on vehicle model
    and context matching.
    
    Key principle: Same model = higher relevance
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.failure_cards = db.failure_cards  # Sprint 3B-01: consolidated from efi_failure_cards
        self.knowledge_items = db.knowledge_items
    
    async def rank_causes(
        self,
        context: RankingContext,
        limit: int = 3
    ) -> Tuple[List[RankedCause], ConfidenceLevel]:
        """
        Rank probable causes based on context.
        
        Returns:
        - Top N ranked causes
        - Overall confidence level
        """
        # Get candidate failure cards
        candidates = await self._get_candidate_cards(context)
        
        if not candidates:
            return [], ConfidenceLevel.LOW
        
        # Score each candidate
        scored_candidates = []
        for card in candidates:
            score, factors = self._calculate_score(card, context)
            scored_candidates.append({
                "card": card,
                "score": score,
                "factors": factors
            })
        
        # Sort by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Take top N
        top_candidates = scored_candidates[:limit]
        
        # Build ranked causes
        ranked_causes = []
        for item in top_candidates:
            card = item["card"]
            score = item["score"]
            factors = item["factors"]
            
            # Normalize score to confidence (0-100)
            max_possible = (
                RankingWeight.MODEL_MATCH +
                RankingWeight.MAKE_MATCH +
                RankingWeight.DTC_MATCH +
                RankingWeight.SUBSYSTEM_MATCH +
                RankingWeight.SYMPTOM_SIMILARITY +
                RankingWeight.SUCCESS_RATE +
                RankingWeight.RECENCY_BONUS +
                RankingWeight.USAGE_BONUS
            )
            confidence = min(100, int((score / max_possible) * 100))
            
            # Build evidence string
            evidence_parts = []
            if "model_match" in factors:
                evidence_parts.append("Same model ({})".format(card.get('vehicle_model')))
            if "dtc_match" in factors:
                evidence_parts.append("DTC match")
            if "high_success_rate" in factors:
                evidence_parts.append("Success rate: {}%".format(int(card.get('historical_success_rate', 0) * 100)))
            
            ranked_causes.append(RankedCause(
                cause=card.get("probable_root_cause", "Unknown cause"),
                confidence=confidence,
                failure_card_id=card.get("failure_card_id"),
                evidence="; ".join(evidence_parts) if evidence_parts else None,
                ranking_score=score,
                matching_factors=factors
            ))
        
        # Determine overall confidence
        if ranked_causes:
            top_confidence = ranked_causes[0].confidence
            if top_confidence >= 70:
                overall_confidence = ConfidenceLevel.HIGH
            elif top_confidence >= 40:
                overall_confidence = ConfidenceLevel.MEDIUM
            else:
                overall_confidence = ConfidenceLevel.LOW
        else:
            overall_confidence = ConfidenceLevel.LOW
        
        return ranked_causes, overall_confidence
    
    async def _get_candidate_cards(
        self,
        context: RankingContext,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get candidate failure cards for ranking.
        Uses broad query to get potential matches.
        """
        # Build base query
        query = {
            "status": {"$in": ["approved", "draft"]}
        }
        
        # TIER 2 SHARED-BRAIN: efi_failure_cards cross-tenant by design — Sprint 1D
        # No org_id filter on failure_cards — shared knowledge base
        
        # Add subsystem filter if available
        if context.subsystem:
            query["$or"] = [
                {"subsystem": context.subsystem},
                {"subsystem": {"$regex": context.subsystem, "$options": "i"}}
            ]
        
        # Fetch candidates
        candidates = await self.failure_cards.find(
            query,
            {"_id": 0}
        ).limit(limit).to_list(limit)
        
        # Also search knowledge items if not enough failure cards
        # TIER 2 SHARED-BRAIN: knowledge_items cross-tenant by design — Sprint 1D
        if len(candidates) < 10:
            knowledge_query = {}
            if context.subsystem:
                knowledge_query["subsystem"] = {"$regex": context.subsystem, "$options": "i"}
            
            knowledge_items = await self.knowledge_items.find(
                knowledge_query,
                {"_id": 0}
            ).limit(20).to_list(20)
            
            # Convert to failure card format
            for item in knowledge_items:
                candidates.append({
                    "failure_card_id": f"KB-{item.get('knowledge_id', 'unknown')}",
                    "probable_root_cause": item.get("solution") or item.get("content", "")[:200],
                    "vehicle_model": item.get("vehicle_model"),
                    "vehicle_make": item.get("vehicle_make"),
                    "subsystem": item.get("subsystem") or item.get("category"),
                    "symptom_cluster": item.get("keywords", []),
                    "dtc_codes": item.get("dtc_codes", []),
                    "historical_success_rate": item.get("effectiveness_score", 0.5),
                    "usage_count": item.get("usage_count", 0),
                    "last_used_at": item.get("last_used_at"),
                    "source_type": "knowledge_base"
                })
        
        return candidates
    
    def _calculate_score(
        self,
        card: Dict,
        context: RankingContext
    ) -> Tuple[float, List[str]]:
        """
        Calculate ranking score for a failure card.
        
        Returns (score, list of matching factors)
        """
        score = 0.0
        factors = []
        
        # 1. Model Match (high weight)
        if context.vehicle_model and card.get("vehicle_model"):
            if context.vehicle_model.lower() == card["vehicle_model"].lower():
                score += RankingWeight.MODEL_MATCH
                factors.append("model_match")
            elif context.vehicle_model.lower() in card["vehicle_model"].lower():
                score += RankingWeight.MODEL_MATCH * 0.5
                factors.append("model_partial_match")
        
        # 2. Make Match
        if context.vehicle_make and card.get("vehicle_make"):
            if context.vehicle_make.lower() == card["vehicle_make"].lower():
                score += RankingWeight.MAKE_MATCH
                factors.append("make_match")
        
        # 3. DTC Match
        if context.dtc_codes and card.get("dtc_codes"):
            context_dtcs = set(dtc.upper() for dtc in context.dtc_codes)
            card_dtcs = set(dtc.upper() for dtc in card["dtc_codes"])
            if context_dtcs & card_dtcs:
                # Proportional to how many match
                match_ratio = len(context_dtcs & card_dtcs) / len(context_dtcs)
                score += RankingWeight.DTC_MATCH * match_ratio
                factors.append("dtc_match")
        
        # Also check single DTC code field
        if context.dtc_codes and card.get("dtc_code"):
            if card["dtc_code"].upper() in [dtc.upper() for dtc in context.dtc_codes]:
                score += RankingWeight.DTC_MATCH * 0.5
                if "dtc_match" not in factors:
                    factors.append("dtc_match")
        
        # 4. Subsystem Match
        if context.subsystem and card.get("subsystem"):
            if context.subsystem.lower() == card["subsystem"].lower():
                score += RankingWeight.SUBSYSTEM_MATCH
                factors.append("subsystem_match")
            elif context.subsystem.lower() in card["subsystem"].lower():
                score += RankingWeight.SUBSYSTEM_MATCH * 0.5
        
        # 5. Symptom Similarity
        if context.symptoms and card.get("symptom_cluster"):
            context_symptoms = set(s.lower() for s in context.symptoms)
            card_symptoms = set(s.lower() for s in card["symptom_cluster"])
            
            if context_symptoms and card_symptoms:
                intersection = context_symptoms & card_symptoms
                union = context_symptoms | card_symptoms
                jaccard = len(intersection) / len(union) if union else 0
                score += RankingWeight.SYMPTOM_SIMILARITY * jaccard
                if jaccard > 0.2:
                    factors.append("symptom_match")
        
        # 6. Historical Success Rate
        success_rate = card.get("historical_success_rate", 0.5)
        score += RankingWeight.SUCCESS_RATE * success_rate
        if success_rate >= 0.7:
            factors.append("high_success_rate")
        
        # 7. Recency Bonus
        if card.get("last_used_at"):
            try:
                last_used = datetime.fromisoformat(card["last_used_at"].replace("Z", "+00:00"))
                days_ago = (datetime.now(timezone.utc) - last_used).days
                
                if days_ago <= 7:
                    score += RankingWeight.RECENCY_BONUS
                    factors.append("recent_use")
                elif days_ago <= 30:
                    score += RankingWeight.RECENCY_BONUS * 0.5
            except Exception:
                pass
        
        # 8. Usage Bonus
        usage_count = card.get("usage_count", 0)
        if usage_count > 10:
            score += RankingWeight.USAGE_BONUS
            factors.append("frequently_used")
        elif usage_count > 5:
            score += RankingWeight.USAGE_BONUS * 0.5
        
        return score, factors
    
    async def get_safe_checklist(
        self,
        context: RankingContext
    ) -> List[Dict]:
        """
        Get safe checklist when confidence < 60%.
        Generic safety steps based on subsystem.
        """
        subsystem = (context.subsystem or "general").lower()
        
        checklists = {
            "battery": [
                {"step": 1, "action": "HV isolation verify karo", "hinglish": "HV isolation verify karo - sabse pehle ye check"},
                {"step": 2, "action": "PPE pehen lo", "hinglish": "PPE gloves aur safety glasses pehen lo"},
                {"step": 3, "action": "12V battery check karo", "hinglish": "12V auxiliary battery voltage check karo", "expected": "12.4V+"}
            ],
            "motor": [
                {"step": 1, "action": "Kill switch check", "hinglish": "Kill switch position check karo"},
                {"step": 2, "action": "Side stand sensor test", "hinglish": "Side stand sensor working hai ya nahi"},
                {"step": 3, "action": "Throttle check", "hinglish": "Throttle position sensor check karo"}
            ],
            "charger": [
                {"step": 1, "action": "Mains supply check", "hinglish": "Mains supply voltage verify karo", "expected": "220-240V"},
                {"step": 2, "action": "Charging port inspect", "hinglish": "Charging port clean hai aur damage nahi hai"},
                {"step": 3, "action": "Charger LED check", "hinglish": "Charger LED status dekho"}
            ],
            "general": [
                {"step": 1, "action": "Safety first", "hinglish": "Pehle safety check - HV components touch mat karo"},
                {"step": 2, "action": "Visual inspection", "hinglish": "Visual inspection karo - koi damage dikhe toh note karo"},
                {"step": 3, "action": "Basic connectivity", "hinglish": "Basic connections tight hain ya nahi check karo"}
            ]
        }
        
        return checklists.get(subsystem, checklists["general"])
    
    async def should_escalate(
        self,
        ranked_causes: List[RankedCause],
        confidence: ConfidenceLevel
    ) -> Tuple[bool, str]:
        """
        Determine if issue should be escalated to expert.
        
        Returns (should_escalate, reason)
        """
        if confidence == ConfidenceLevel.LOW:
            return True, "Low confidence - expert verification recommended"
        
        if not ranked_causes:
            return True, "No matching causes found - needs expert diagnosis"
        
        # Check if top cause has very low confidence
        if ranked_causes[0].confidence < 40:
            return True, "Top cause confidence too low - expert review needed"
        
        # Check for potentially dangerous causes
        dangerous_keywords = ["fire", "smoke", "thermal", "runaway", "explosion", "short circuit"]
        for cause in ranked_causes[:3]:
            cause_lower = cause.cause.lower()
            if any(kw in cause_lower for kw in dangerous_keywords):
                return True, "Potential safety issue detected - expert supervision required"
        
        return False, ""
