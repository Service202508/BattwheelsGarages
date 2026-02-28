"""
EFI Embedding Service - Provider-Agnostic Vector Embeddings

This module provides a provider-agnostic interface for generating text embeddings
used in the EV Failure Intelligence system for semantic similarity search.

Architecture:
- BaseEmbeddingService: Abstract interface
- GeminiEmbeddingService: Uses Emergent LLM Key with Gemini for semantic feature extraction
- FallbackEmbeddingService: Hash-based embeddings when API unavailable

Usage:
    service = EmbeddingServiceFactory.create("gemini", api_key="...")
    embedding = await service.embed_text("Battery not charging")
"""

import os
import hashlib
import math
import logging
import asyncio
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import httpx
import json

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResponse:
    """Standard response from embedding service"""
    text: str
    embedding: List[float]
    model: str
    dimensions: int


class BaseEmbeddingService(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available and configured"""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Return the embedding dimensions"""
        pass
    
    @abstractmethod
    async def embed_text(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> EmbeddingResponse:
        """Generate embedding for a single text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str], task_type: str = "SEMANTIC_SIMILARITY") -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts"""
        pass


class GeminiEmbeddingService(BaseEmbeddingService):
    """
    Hybrid embedding service: LLM semantic features + deterministic text features.
    
    Since dedicated embedding models (text-embedding-004, text-embedding-3-small)
    are not available via the Emergent proxy, this uses a two-part approach:
    
    Part 1 (dims 0-7): 8 LLM-rated semantic dimensions via gpt-4o-mini.
        These capture domain-specific meaning: which EV subsystem is involved,
        severity, component affected, urgency.
    
    Part 2 (dims 8-255): 248 deterministic text features.
        Character trigrams + word-level hashing provides text differentiation.
        Different texts produce different vectors; similar texts produce similar vectors.
    
    The LLM dims are weighted 3x to dominate similarity calculations.
    """
    
    SEMANTIC_DIM_COUNT = 8
    SEMANTIC_WEIGHT = 3.0  # Weight LLM dims higher in final vector
    SEMANTIC_DIMS = "battery,motor,controller,severity,cell,BMS,charger,urgency"
    
    def __init__(self, api_key: Optional[str] = None, output_dim: int = 256):
        self.api_key = api_key or os.environ.get("EMERGENT_LLM_KEY")
        self.output_dim = output_dim
        self.model = "gpt-4o-mini"
        self.proxy_url = os.environ.get("INTEGRATION_PROXY_URL", "https://integrations.emergentagent.com")
        self._initialized = False
        self._available = False
        
    def _ensure_initialized(self):
        """Lazy initialization check"""
        if self._initialized:
            return
        self._available = bool(self.api_key)
        self._initialized = True
        if self._available:
            logger.info("Hybrid embedding service initialized (LLM semantic + text features)")
        else:
            logger.warning("Hybrid embedding service: No API key — using text features only")
    
    def is_available(self) -> bool:
        self._ensure_initialized()
        return self._available
    
    def get_dimensions(self) -> int:
        return self.output_dim
    
    def _text_to_features(self, text: str) -> List[float]:
        """Generate deterministic text features using character trigrams and word hashing.
        Produces self.output_dim - SEMANTIC_DIM_COUNT features."""
        text_normalized = text.lower().strip()
        feat_dim = self.output_dim - self.SEMANTIC_DIM_COUNT
        features = [0.0] * feat_dim
        
        # Character trigram hashing
        for i in range(len(text_normalized) - 2):
            trigram = text_normalized[i:i+3]
            h = int(hashlib.md5(trigram.encode()).hexdigest(), 16)
            idx = h % feat_dim
            features[idx] += 1.0
        
        # Word-level hashing
        words = text_normalized.split()
        for w in words:
            h = int(hashlib.sha256(w.encode()).hexdigest(), 16)
            idx = h % feat_dim
            features[idx] += 2.0  # Words weighted more than trigrams
        
        # Normalize to unit vector
        norm = math.sqrt(sum(x*x for x in features))
        if norm > 0:
            features = [x / norm for x in features]
        
        return features
    
    async def _extract_semantic_features(self, text: str) -> Optional[List[float]]:
        """Use LLM to rate text on 8 EV diagnostic dimensions.
        Returns 8 floats between -1 and 1, or None on failure."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                prompt = (
                    f'[0.9,0.1,...] Rate this EV complaint on {self.SEMANTIC_DIM_COUNT} dims '
                    f'({self.SEMANTIC_DIMS}) as floats -1 to 1. '
                    f'Complaint: "{text}". Reply with ONLY the JSON array.'
                )
                response = await client.post(
                    f"{self.proxy_url}/llm/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0,
                        "max_tokens": 200
                    }
                )
                if response.status_code == 200:
                    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    content = content.strip()
                    if "```" in content:
                        content = content.split("```")[1].replace("json", "", 1).strip()
                    
                    import re
                    match = re.search(r'\[[\d\s,.\-eE]+\]', content.replace('\n', ' '))
                    if match:
                        features = json.loads(match.group())
                        if isinstance(features, list) and len(features) >= self.SEMANTIC_DIM_COUNT:
                            return [float(v) for v in features[:self.SEMANTIC_DIM_COUNT]]
                    
                    logger.warning(f"LLM returned unparseable content: {content[:100]}")
                else:
                    logger.warning(f"LLM semantic extraction failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Semantic feature extraction error: {e}")
        return None
    
    async def embed_text(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> EmbeddingResponse:
        """Generate hybrid embedding: 8 LLM semantic dims + 248 text feature dims."""
        self._ensure_initialized()
        model_used = "hybrid-semantic+text"
        
        # Part 2: Deterministic text features (always available, dims 8-255)
        text_features = self._text_to_features(text)
        
        # Part 1: LLM semantic dims (dims 0-7)
        semantic_dims = None
        if self._available:
            semantic_dims = await self._extract_semantic_features(text)
        
        if semantic_dims is None:
            # No LLM available — use zero semantic dims, rely on text features only
            semantic_dims = [0.0] * self.SEMANTIC_DIM_COUNT
            model_used = "text-features-only"
            logger.debug(f"Using text features only for: {text[:50]}...")
        
        # Combine: weight semantic dims higher (they carry meaning)
        weighted_semantic = [v * self.SEMANTIC_WEIGHT for v in semantic_dims]
        embedding = weighted_semantic + text_features
        
        # Normalize to unit vector
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return EmbeddingResponse(
            text=text,
            embedding=embedding[:self.output_dim],
            model=model_used,
            dimensions=self.output_dim
        )
    
    async def embed_batch(self, texts: List[str], task_type: str = "SEMANTIC_SIMILARITY") -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts concurrently"""
        # Process in batches to avoid rate limiting
        batch_size = 5
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            tasks = [self.embed_text(text, task_type) for text in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Small delay between batches
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)
        
        return results


class FallbackEmbeddingService(BaseEmbeddingService):
    """Hash-based fallback embedding service for offline operation"""
    
    def __init__(self, output_dim: int = 256):
        self.output_dim = output_dim
        
    def is_available(self) -> bool:
        return True  # Always available
    
    def get_dimensions(self) -> int:
        return self.output_dim
    
    def _generate_hash_embedding(self, text: str) -> List[float]:
        """Generate deterministic embedding from text hash"""
        # Combine multiple hash functions for better distribution
        text_lower = text.lower().strip()
        
        # SHA-256 for primary hash
        sha_hash = hashlib.sha256(text_lower.encode()).digest()
        
        # MD5 for secondary hash (mixing)
        md5_hash = hashlib.md5(text_lower.encode()).digest()
        
        # Combine hashes
        combined = sha_hash + md5_hash
        
        embedding = []
        for i in range(self.output_dim):
            byte_idx = i % len(combined)
            # Create float from bytes with some variation
            val = combined[byte_idx] / 255.0 * 2 - 1  # Scale to [-1, 1]
            # Add variation based on position
            variation = (i / self.output_dim) * 0.1
            val = val * (1 - variation) + variation * math.sin(i * 0.1)
            embedding.append(val)
        
        # Normalize to unit vector
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    async def embed_text(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> EmbeddingResponse:
        """Generate hash-based embedding"""
        embedding = self._generate_hash_embedding(text)
        
        return EmbeddingResponse(
            text=text,
            embedding=embedding,
            model="hash-fallback",
            dimensions=len(embedding)
        )
    
    async def embed_batch(self, texts: List[str], task_type: str = "SEMANTIC_SIMILARITY") -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts"""
        return [await self.embed_text(text, task_type) for text in texts]


class EmbeddingServiceFactory:
    """Factory for creating embedding service instances"""
    
    _instances: Dict[str, BaseEmbeddingService] = {}
    
    @classmethod
    def create(
        cls, 
        provider: str = "gemini", 
        api_key: Optional[str] = None,
        output_dim: int = 256,
        **kwargs
    ) -> BaseEmbeddingService:
        """
        Create or return cached embedding service instance.
        
        Args:
            provider: "gemini" or "fallback"
            api_key: API key (uses env var if not provided)
            output_dim: Embedding dimensions
            
        Returns:
            Configured embedding service
        """
        cache_key = f"{provider}_{output_dim}"
        
        if cache_key not in cls._instances:
            if provider == "gemini":
                service = GeminiEmbeddingService(api_key=api_key, output_dim=output_dim)
            else:
                service = FallbackEmbeddingService(output_dim=output_dim)
            
            cls._instances[cache_key] = service
            logger.info(f"Created {provider} embedding service with {output_dim} dimensions")
        
        return cls._instances[cache_key]
    
    @classmethod
    def get_default(cls) -> BaseEmbeddingService:
        """Get the default embedding service (Gemini with fallback)"""
        service = cls.create("gemini")
        
        # If Gemini not available, use fallback
        if not service.is_available():
            logger.warning("Gemini not available, using fallback embedding service")
            service = cls.create("fallback")
        
        return service


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions must match: {len(vec1)} vs {len(vec2)}")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Euclidean distance between two vectors"""
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions must match: {len(vec1)} vs {len(vec2)}")
    
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


async def find_similar_embeddings(
    query_embedding: List[float],
    embeddings: List[Dict[str, Any]],
    top_k: int = 5,
    threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Find most similar embeddings to a query embedding.
    
    Args:
        query_embedding: The query vector
        embeddings: List of dicts with 'embedding' and 'id' keys
        top_k: Maximum number of results
        threshold: Minimum similarity score
        
    Returns:
        List of matches with similarity scores
    """
    results = []
    
    for item in embeddings:
        if 'embedding' not in item:
            continue
            
        similarity = cosine_similarity(query_embedding, item['embedding'])
        
        if similarity >= threshold:
            results.append({
                **item,
                'similarity_score': similarity
            })
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return results[:top_k]


# ==================== EFI EMBEDDING MANAGER ====================

class EFIEmbeddingManager:
    """
    Manager for EFI embedding operations - integrates with failure cards database.
    Handles complaint classification, embedding generation, and similarity search.
    """
    
    # Subsystem keywords for classification
    SUBSYSTEM_KEYWORDS = {
        "battery": ["battery", "bms", "charging", "charge", "cell", "voltage", "soc", "swap", "discharge", "capacity", "pack"],
        "motor": ["motor", "hub", "torque", "rpm", "overheating", "noise", "vibration", "hall", "sensor", "shaft"],
        "controller": ["controller", "ecu", "throttle", "firmware", "software", "communication", "can", "error code", "lock"],
        "electrical": ["wiring", "harness", "connector", "fuse", "relay", "dc-dc", "converter", "voltage", "ground", "short"]
    }
    
    def __init__(self, db, embedding_service: Optional[BaseEmbeddingService] = None):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingServiceFactory.get_default()
        logger.info(f"EFI Embedding Manager initialized with {type(self.embedding_service).__name__}")
    
    def classify_subsystem(self, text: str) -> str:
        """Classify complaint text into subsystem category"""
        text_lower = text.lower()
        scores = {}
        
        for subsystem, keywords in self.SUBSYSTEM_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[subsystem] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "unknown"
    
    async def generate_complaint_embedding(self, complaint_text: str) -> Dict[str, Any]:
        """Generate embedding and classify a complaint"""
        # Classify subsystem
        subsystem = self.classify_subsystem(complaint_text)
        
        # Generate embedding
        embedding_response = await self.embedding_service.embed_text(complaint_text)
        
        return {
            "complaint_text": complaint_text,
            "classified_subsystem": subsystem,
            "embedding": embedding_response.embedding,
            "embedding_model": embedding_response.model,
            "dimensions": embedding_response.dimensions
        }
    
    async def find_similar_failure_cards(
        self,
        embedding: List[float],
        subsystem: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.1  # Lowered threshold for hash-based embeddings
    ) -> List[Dict[str, Any]]:
        """Find similar failure cards using embedding similarity"""
        
        # Build query filter
        query = {
            "embedding_vector": {"$exists": True, "$ne": None},
            "excluded_from_efi": {"$ne": True},
        }
        if subsystem and subsystem != "unknown":
            query["subsystem_category"] = subsystem
        
        # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1C
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        cards = await self.db.failure_cards.find(query, {"_id": 0}).to_list(1000)
        
        if not cards:
            # Try without subsystem filter
            # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1C
            # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
            cards = await self.db.failure_cards.find(
                {"embedding_vector": {"$exists": True, "$ne": None}},
                {"_id": 0}
            ).to_list(1000)
        
        if not cards:
            logger.warning("No failure cards with embeddings found")
            return []
        
        # Get all decision tree IDs for boosting
        tree_card_ids = set()
        # TIER 2 SHARED-BRAIN: efi_decision_trees cross-tenant by design — Sprint 1C
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        trees = await self.db.efi_decision_trees.find({}, {"failure_card_id": 1}).to_list(1000)
        for t in trees:
            tree_card_ids.add(t.get("failure_card_id"))
        
        # Calculate similarities
        results = []
        for card in cards:
            card_embedding = card.get("embedding_vector", [])
            if not card_embedding or len(card_embedding) != len(embedding):
                continue
            
            similarity = cosine_similarity(embedding, card_embedding)
            
            # Boost cards that have decision trees
            has_tree = card.get("failure_id") in tree_card_ids
            boosted_score = similarity * (1.5 if has_tree else 1.0)
            
            if boosted_score >= threshold:
                # Determine confidence level
                if boosted_score >= 0.5:
                    confidence = "high"
                elif boosted_score >= 0.25:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                results.append({
                    **card,
                    "similarity_score": round(boosted_score, 4),
                    "raw_similarity": round(similarity, 4),
                    "confidence_level": confidence,
                    "has_decision_tree": has_tree
                })
        
        # Sort by similarity and limit
        results.sort(key=lambda x: (x.get("has_decision_tree", False), x["similarity_score"]), reverse=True)
        return results[:limit]
    
    async def embed_failure_card(self, failure_id: str) -> Dict[str, Any]:
        """Generate and store embedding for a single failure card (uses fast hash-based)"""
        # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1C
        card = await self.db.failure_cards.find_one({"failure_id": failure_id})
        if not card:
            raise ValueError(f"Failure card {failure_id} not found")
        
        # Create text for embedding from card fields
        text_parts = [
            card.get("title", ""),
            card.get("description", ""),
            card.get("symptoms", ""),
            card.get("symptom_text", ""),
            " ".join(card.get("common_causes", [])),
            " ".join(card.get("keywords", []))
        ]
        text = " ".join(filter(None, text_parts))
        
        # Use hash-based embedding for reliability in batch operations
        fallback = FallbackEmbeddingService(self.embedding_service.get_dimensions())
        embedding_response = await fallback.embed_text(text)
        
        # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1C
        await self.db.failure_cards.update_one(
            {"failure_id": failure_id},
            {
                "$set": {
                    "embedding_vector": embedding_response.embedding,
                    "embedding_model": embedding_response.model,
                    "embedding_updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "failure_id": failure_id,
            "embedding_dimensions": len(embedding_response.embedding),
            "model": embedding_response.model,
            "status": "success"
        }
    
    async def embed_all_cards(self) -> Dict[str, Any]:
        """Generate embeddings for all failure cards"""
        # TIER 2 SHARED-BRAIN: failure_cards cross-tenant by design — Sprint 1C
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        cards = await self.db.failure_cards.find({}, {"failure_id": 1, "_id": 0}).to_list(1000)
        
        results = {
            "total": len(cards),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for card in cards:
            try:
                await self.embed_failure_card(card["failure_id"])
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "failure_id": card["failure_id"],
                    "error": str(e)
                })
        
        return results


# ==================== SINGLETON MANAGEMENT ====================

_embedding_manager: Optional[EFIEmbeddingManager] = None


def init_efi_embedding_manager(db) -> EFIEmbeddingManager:
    """Initialize the EFI embedding manager with database"""
    global _embedding_manager
    _embedding_manager = EFIEmbeddingManager(db)
    return _embedding_manager


def get_efi_embedding_manager() -> Optional[EFIEmbeddingManager]:
    """Get the initialized embedding manager"""
    return _embedding_manager
