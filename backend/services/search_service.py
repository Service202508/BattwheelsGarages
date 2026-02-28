"""
Battwheels OS - Advanced Search Service
Production-grade search combining multiple strategies

Features:
- Text search with fuzzy matching
- Vector semantic search
- Hybrid ranking (BM25 + Vector)
- Query expansion
- Result caching
"""
import re
import math
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from collections import Counter

from services.embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


# EV-specific synonyms for query expansion
EV_SYNONYMS = {
    "battery": ["bms", "cell", "pack", "soc", "voltage", "charge"],
    "motor": ["hub", "bldc", "controller", "drive", "torque"],
    "charger": ["charging", "adapter", "connector", "port"],
    "display": ["dashboard", "screen", "lcd", "meter", "speedometer"],
    "brake": ["braking", "regen", "abs", "disc"],
    "controller": ["ecu", "mcu", "inverter", "driver"],
    "wiring": ["harness", "connector", "fuse", "relay", "wire"],
    "throttle": ["accelerator", "speed", "pedal"],
    "noise": ["sound", "vibration", "rattle", "hum"],
    "heat": ["hot", "temperature", "thermal", "overheat"],
    "error": ["fault", "code", "warning", "alert"],
    "not working": ["failed", "dead", "stuck", "broken", "malfunction"],
}

# Stopwords to filter from search
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
    "because", "until", "while", "this", "that", "these", "those", "it",
    "its", "ev", "electric", "vehicle", "scooter", "bike"
}


class AdvancedSearchService:
    """
    Production-grade search service for failure cards.
    
    Combines multiple search strategies:
    1. Exact match (signature hash)
    2. Text search (tokenized, fuzzy)
    3. Vector semantic search
    4. Hybrid ranking
    """
    
    def __init__(self, db, embedding_service: EmbeddingService = None):
        self.db = db
        self.embedding_service = embedding_service
        logger.info("AdvancedSearchService initialized")
    
    # ==================== TEXT PROCESSING ====================
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize and clean text for search."""
        if not text:
            return []
        
        # Lowercase and split
        text = text.lower()
        
        # Replace special chars with spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Split into tokens
        tokens = text.split()
        
        # Remove stopwords and short tokens
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
        
        return tokens
    
    def expand_query(self, tokens: List[str]) -> List[str]:
        """Expand query with EV-specific synonyms."""
        expanded = set(tokens)
        
        for token in tokens:
            # Check for synonym matches
            for key, synonyms in EV_SYNONYMS.items():
                if token == key or token in synonyms:
                    expanded.add(key)
                    expanded.update(synonyms[:3])  # Add top 3 synonyms
        
        return list(expanded)
    
    def compute_bm25_score(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        avg_doc_length: float = 50,
        k1: float = 1.5,
        b: float = 0.75
    ) -> float:
        """
        Compute BM25 relevance score.
        
        BM25 is a probabilistic ranking function used by search engines.
        """
        if not query_tokens or not doc_tokens:
            return 0.0
        
        doc_length = len(doc_tokens)
        doc_freq = Counter(doc_tokens)
        
        score = 0.0
        
        for token in query_tokens:
            if token in doc_freq:
                tf = doc_freq[token]
                
                # BM25 term frequency component
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
                
                # IDF approximation (simplified)
                idf = math.log(2.0)  # Simplified; would use corpus stats in production
                
                score += idf * (numerator / denominator)
        
        return score
    
    def fuzzy_match(self, token: str, target: str, threshold: float = 0.7) -> bool:
        """Check if token fuzzy-matches target using Levenshtein ratio."""
        if not token or not target:
            return False
        
        # Exact match
        if token == target:
            return True
        
        # Prefix match
        if target.startswith(token) or token.startswith(target):
            return True
        
        # Levenshtein distance
        len1, len2 = len(token), len(target)
        if abs(len1 - len2) > 3:
            return False
        
        # Simple edit distance
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if token[i - 1] == target[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
        
        distance = dp[len1][len2]
        max_len = max(len1, len2)
        similarity = 1 - (distance / max_len)
        
        return similarity >= threshold
    
    # ==================== SEARCH METHODS ====================
    
    async def text_search(
        self,
        query: str,
        filter_query: Dict[str, Any] = None,
        limit: int = 20,
        fuzzy: bool = True,
        org_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Perform text-based search on failure cards.
        
        Uses tokenization, BM25 scoring, and optional fuzzy matching.
        """
        filter_query = filter_query or {"status": {"$in": ["approved", "draft"]}}
        
        # Tokenize and expand query
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []
        
        expanded_tokens = self.expand_query(query_tokens)
        
        # Build MongoDB query - use $or with $regex for each field
        or_conditions = []
        for token in expanded_tokens:
            if fuzzy:
                pattern = f".*{token}.*"
            else:
                pattern = f"\\b{token}\\b"
            
            or_conditions.extend([
                {"title": {"$regex": pattern, "$options": "i"}},
                {"description": {"$regex": pattern, "$options": "i"}},
                {"symptom_text": {"$regex": pattern, "$options": "i"}},
                {"root_cause": {"$regex": pattern, "$options": "i"}}
            ])
        
        # Add keyword matches
        or_conditions.append({"keywords": {"$in": expanded_tokens}})
        
        mongo_query = {
            **filter_query,
            "$or": or_conditions
        }
        
        # Fallback to simpler query if regex fails
        try:
            # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1D
            candidates = await self.db.failure_cards.find(
                mongo_query,
                {"_id": 0, "embedding_vector": 0}
            ).limit(limit * 3).to_list(limit * 3)
        except Exception as e:
            logger.warning(f"Complex query failed, using simple: {e}")
            # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1D
            # Simple keyword search
            candidates = await self.db.failure_cards.find(
                {**filter_query, "keywords": {"$in": expanded_tokens}},
                {"_id": 0, "embedding_vector": 0}
            ).limit(limit * 3).to_list(limit * 3)
        
        if not candidates:
            return []
        
        # Score candidates using BM25
        scored_results = []
        
        for card in candidates:
            # Build document tokens
            doc_text = f"{card.get('title', '')} {card.get('description', '')} {card.get('symptom_text', '')} {card.get('root_cause', '')} {' '.join(card.get('keywords', []))}"
            doc_tokens = self.tokenize(doc_text)
            
            # Compute BM25 score
            bm25_score = self.compute_bm25_score(expanded_tokens, doc_tokens)
            
            # Bonus for exact keyword matches
            keyword_matches = len(set(expanded_tokens) & set(card.get("keywords", [])))
            keyword_bonus = keyword_matches * 0.1
            
            # Bonus for title match
            title_tokens = self.tokenize(card.get("title", ""))
            title_matches = len(set(query_tokens) & set(title_tokens))
            title_bonus = title_matches * 0.2
            
            # Confidence and effectiveness boost
            confidence_boost = card.get("confidence_score", 0.5) * 0.1
            effectiveness_boost = card.get("effectiveness_score", 0) * 0.1
            
            total_score = bm25_score + keyword_bonus + title_bonus + confidence_boost + effectiveness_boost
            
            card["text_score"] = round(total_score, 4)
            scored_results.append(card)
        
        # Sort by score
        scored_results.sort(key=lambda x: x["text_score"], reverse=True)
        
        return scored_results[:limit]
    
    async def vector_search(
        self,
        query: str,
        filter_query: Dict[str, Any] = None,
        limit: int = 20,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform vector semantic search using embeddings.
        """
        if not self.embedding_service:
            logger.warning("Embedding service not available for vector search")
            return []
        
        filter_query = filter_query or {"status": {"$in": ["approved", "draft"]}}
        
        # Generate query embedding
        query_embedding = await self.embedding_service.get_embedding(query)
        
        if not query_embedding:
            logger.warning("Failed to generate query embedding")
            return []
        
        # Perform vector similarity search
        results = await self.embedding_service.find_similar(
            query_embedding=query_embedding,
            collection="failure_cards",
            embedding_field="embedding_vector",
            filter_query=filter_query,
            limit=limit,
            min_score=min_score
        )
        
        # Rename score field
        for r in results:
            if "score" in r:
                r["vector_score"] = r.pop("score")
        
        return results
    
    async def hybrid_search(
        self,
        query: str,
        error_codes: List[str] = None,
        subsystem: str = None,
        vehicle_make: str = None,
        vehicle_model: str = None,
        limit: int = 10,
        text_weight: float = 0.4,
        vector_weight: float = 0.6,
        org_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining text and vector approaches.
        
        This is the main search method for production use.
        """
        # Build filter
        filter_query = {"status": {"$in": ["approved", "draft"]}}
        
        if subsystem:
            filter_query["subsystem_category"] = subsystem
        
        # Enrich query with context
        enriched_query = query
        if error_codes:
            enriched_query += f" error codes: {', '.join(error_codes)}"
        if vehicle_make:
            enriched_query += f" {vehicle_make}"
        if vehicle_model:
            enriched_query += f" {vehicle_model}"
        
        # Run both searches in parallel
        text_results, vector_results = await asyncio.gather(
            self.text_search(enriched_query, filter_query, limit * 2),
            self.vector_search(enriched_query, filter_query, limit * 2, min_score=0.4),
            return_exceptions=True
        )
        
        # Handle errors
        if isinstance(text_results, Exception):
            logger.error(f"Text search failed: {text_results}")
            text_results = []
        
        if isinstance(vector_results, Exception):
            logger.error(f"Vector search failed: {vector_results}")
            vector_results = []
        
        # Merge and re-rank results
        merged = {}
        
        # Add text results
        for card in text_results:
            fid = card["failure_id"]
            merged[fid] = {
                **card,
                "text_score": card.get("text_score", 0),
                "vector_score": 0
            }
        
        # Merge vector results
        for card in vector_results:
            fid = card["failure_id"]
            if fid in merged:
                merged[fid]["vector_score"] = card.get("vector_score", 0)
            else:
                merged[fid] = {
                    **card,
                    "text_score": 0,
                    "vector_score": card.get("vector_score", 0)
                }
        
        # Compute hybrid scores
        results = []
        for fid, card in merged.items():
            # Normalize scores
            text_score = min(1.0, card["text_score"] / 3.0) if card["text_score"] > 0 else 0
            vector_score = card["vector_score"]
            
            # Weighted combination
            hybrid_score = (text_weight * text_score) + (vector_weight * vector_score)
            
            # Bonus for error code matches
            if error_codes and card.get("error_codes"):
                code_matches = len(set(error_codes) & set(card["error_codes"]))
                hybrid_score += code_matches * 0.1
            
            # Bonus for vehicle match
            if vehicle_make and card.get("vehicle_models"):
                for vm in card["vehicle_models"]:
                    if vm.get("make", "").lower() == vehicle_make.lower():
                        hybrid_score += 0.1
                        if vehicle_model and vm.get("model", "").lower() == vehicle_model.lower():
                            hybrid_score += 0.05
                        break
            
            card["hybrid_score"] = round(hybrid_score, 4)
            card["match_type"] = "hybrid"
            results.append(card)
        
        # Sort by hybrid score
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return results[:limit]


# Service factory
_search_service: Optional[AdvancedSearchService] = None


def get_search_service() -> AdvancedSearchService:
    if _search_service is None:
        raise ValueError("AdvancedSearchService not initialized")
    return _search_service


def init_search_service(db, embedding_service: EmbeddingService = None) -> AdvancedSearchService:
    """Initialize search service."""
    global _search_service
    _search_service = AdvancedSearchService(db, embedding_service)
    return _search_service
