"""
Battwheels OS - Vector Embedding Service
Production-grade semantic search using OpenAI embeddings

Features:
- OpenAI text-embedding-3-small (1536 dimensions)
- Batch embedding generation
- Caching for cost optimization
- MongoDB vector search integration

Note: Embeddings require a direct OpenAI API key (OPENAI_API_KEY).
The Emergent LLM key only supports chat completions.
"""
import os
import hashlib
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 100  # OpenAI batch limit
CACHE_TTL_HOURS = 168  # 7 days


class EmbeddingService:
    """
    Production vector embedding service using OpenAI.
    
    Requires direct OpenAI API key (OPENAI_API_KEY env var).
    Implements caching to reduce API costs.
    """
    
    def __init__(self, db=None):
        self.db = db
        # Only use OPENAI_API_KEY for embeddings (Emergent key doesn't support embeddings)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. Vector embeddings disabled - using keyword search only.")
            logger.info("To enable semantic search, add OPENAI_API_KEY to .env file.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("EmbeddingService initialized with OpenAI client")
    
    def _compute_text_hash(self, text: str) -> str:
        """Generate deterministic hash for text caching."""
        return hashlib.sha256(text.encode()).hexdigest()[:32]
    
    async def get_embedding(self, text: str, use_cache: bool = True, org_id: str = None) -> Optional[List[float]]:
        """
        Get embedding for a single text string.
        
        Args:
            text: Text to embed
            use_cache: Whether to check cache first
            org_id: Organization ID for cache scoping (TIER 1)
            
        Returns:
            1536-dimensional embedding vector or None if error
        """
        if not self.client:
            logger.warning("Embedding client not initialized")
            return None
        
        if not text or not text.strip():
            return None
        
        text = text.strip()[:8000]  # Limit to 8000 chars
        text_hash = self._compute_text_hash(text)
        
        # Check cache (TIER 1: org-scoped — Sprint 1C)
        if use_cache and self.db is not None:
            cache_query = {"text_hash": text_hash}
            if org_id:
                cache_query["organization_id"] = org_id
            cached = await self.db.embedding_cache.find_one(
                cache_query,
                {"_id": 0, "embedding": 1}
            )
            if cached:
                logger.debug(f"Cache hit for embedding: {text_hash[:8]}...")
                return cached["embedding"]
        
        try:
            response = await self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result (TIER 1: org-scoped — Sprint 1C)
            if self.db is not None:
                cache_doc = {
                    "text_hash": text_hash,
                    "text_preview": text[:200],
                    "embedding": embedding,
                    "model": EMBEDDING_MODEL,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                if org_id:
                    cache_doc["organization_id"] = org_id
                cache_filter = {"text_hash": text_hash}
                if org_id:
                    cache_filter["organization_id"] = org_id
                await self.db.embedding_cache.update_one(
                    cache_filter,
                    {"$set": cache_doc},
                    upsert=True
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        use_cache: bool = True,
        org_id: str = None
    ) -> List[Optional[List[float]]]:
        """
        Get embeddings for multiple texts in batch.
        
        More efficient than individual calls.
        """
        if not self.client:
            return [None] * len(texts)
        
        results = [None] * len(texts)
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if not text or not text.strip():
                continue
            
            text = text.strip()[:8000]
            text_hash = self._compute_text_hash(text)
            
            if use_cache and self.db is not None:
                cache_query = {"text_hash": text_hash}
                if org_id:
                    cache_query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
                cached = await self.db.embedding_cache.find_one(
                    cache_query,
                    {"_id": 0, "embedding": 1}
                )
                if cached:
                    results[i] = cached["embedding"]
                    continue
            
            texts_to_embed.append(text)
            indices_to_embed.append(i)
        
        # Batch embed uncached texts
        if texts_to_embed:
            try:
                # Process in batches of BATCH_SIZE
                for batch_start in range(0, len(texts_to_embed), BATCH_SIZE):
                    batch_end = min(batch_start + BATCH_SIZE, len(texts_to_embed))
                    batch_texts = texts_to_embed[batch_start:batch_end]
                    batch_indices = indices_to_embed[batch_start:batch_end]
                    
                    response = await self.client.embeddings.create(
                        model=EMBEDDING_MODEL,
                        input=batch_texts,
                        dimensions=EMBEDDING_DIMENSIONS
                    )
                    
                    # Store results and cache
                    for j, embedding_data in enumerate(response.data):
                        original_idx = batch_indices[j]
                        embedding = embedding_data.embedding
                        results[original_idx] = embedding
                        
                        # Cache (TIER 1: org-scoped — Sprint 1C)
                        if self.db is not None:
                            text = batch_texts[j]
                            text_hash = self._compute_text_hash(text)
                            cache_doc = {
                                "text_hash": text_hash,
                                "text_preview": text[:200],
                                "embedding": embedding,
                                "model": EMBEDDING_MODEL,
                                "created_at": datetime.now(timezone.utc).isoformat()
                            }
                            if org_id:
                                cache_doc["organization_id"] = org_id
                            cache_filter = {"text_hash": text_hash}
                            if org_id:
                                cache_filter["organization_id"] = org_id
                            await self.db.embedding_cache.update_one(
                                cache_filter,
                                {"$set": cache_doc},
                                upsert=True
                            )
                    
                    logger.info(f"Generated {len(batch_texts)} embeddings")
                    
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
        
        return results
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        import math
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def find_similar(
        self,
        query_embedding: List[float],
        collection: str,
        embedding_field: str = "embedding_vector",
        filter_query: Dict[str, Any] = None,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find similar documents using vector similarity.
        
        Uses MongoDB $vectorSearch if available, falls back to in-memory.
        """
        if self.db is None or not query_embedding:
            return []
        
        filter_query = filter_query or {}
        
        # Try MongoDB Atlas Vector Search first
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": f"{collection}_vector_index",
                        "path": embedding_field,
                        "queryVector": query_embedding,
                        "numCandidates": limit * 10,
                        "limit": limit,
                        "filter": filter_query
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        embedding_field: 0,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            results = await self.db[collection].aggregate(pipeline).to_list(limit)
            return [r for r in results if r.get("score", 0) >= min_score]
            
        except Exception as e:
            logger.debug(f"Vector search not available: {e}, using fallback")
        
        # Fallback: In-memory similarity search
        documents = await self.db[collection].find(
            {**filter_query, embedding_field: {"$exists": True}},
            {"_id": 0}
        ).limit(500).to_list(500)
        
        scored_docs = []
        for doc in documents:
            doc_embedding = doc.get(embedding_field)
            if doc_embedding:
                score = self.compute_similarity(query_embedding, doc_embedding)
                if score >= min_score:
                    doc["score"] = score
                    doc.pop(embedding_field, None)  # Remove large embedding from result
                    scored_docs.append(doc)
        
        # Sort by score descending
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_docs[:limit]


class FailureCardEmbedder:
    """
    Specialized embedder for failure cards.
    
    Generates optimized embeddings combining multiple fields.
    """
    
    def __init__(self, embedding_service: EmbeddingService, db):
        self.embedding_service = embedding_service
        self.db = db
    
    def _build_embedding_text(self, card: Dict[str, Any]) -> str:
        """
        Build optimized text for embedding from failure card fields.
        
        Combines: title, symptom_text, root_cause, keywords, error_codes
        """
        parts = []
        
        # Title (high weight - repeated)
        if card.get("title"):
            parts.append(card["title"])
            parts.append(card["title"])  # Repeat for emphasis
        
        # Symptom text
        if card.get("symptom_text"):
            parts.append(card["symptom_text"])
        
        # Description
        if card.get("description"):
            parts.append(card["description"][:500])
        
        # Root cause
        if card.get("root_cause"):
            parts.append(f"Root cause: {card['root_cause']}")
        
        # Error codes
        if card.get("error_codes"):
            parts.append(f"Error codes: {', '.join(card['error_codes'])}")
        
        # Keywords
        if card.get("keywords"):
            parts.append(f"Keywords: {', '.join(card['keywords'][:20])}")
        
        # Subsystem
        if card.get("subsystem_category"):
            parts.append(f"Subsystem: {card['subsystem_category']}")
        
        # Vehicle models
        if card.get("vehicle_models"):
            vehicles = [f"{v.get('make', '')} {v.get('model', '')}" for v in card["vehicle_models"][:5]]
            parts.append(f"Vehicles: {', '.join(vehicles)}")
        
        return " | ".join(parts)
    
    async def embed_failure_card(self, card: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for a single failure card.
        """
        text = self._build_embedding_text(card)
        return await self.embedding_service.get_embedding(text)
    
    async def embed_all_cards(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Generate embeddings for all failure cards without embeddings.
        
        Returns statistics about the operation.
        """
        # Find cards without embeddings
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        cards = await self.db.failure_cards.find(
            {"embedding_vector": {"$exists": False}},
            {"_id": 0}
        ).to_list(1000)
        
        if not cards:
            # Also check cards with null embeddings
            # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
            cards = await self.db.failure_cards.find(
                {"embedding_vector": None},
                {"_id": 0}
            ).to_list(1000)
        
        if not cards:
            return {"status": "complete", "processed": 0, "message": "All cards already have embeddings"}
        
        logger.info(f"Generating embeddings for {len(cards)} failure cards")
        
        processed = 0
        errors = 0
        
        # Process in batches
        for i in range(0, len(cards), batch_size):
            batch = cards[i:i + batch_size]
            texts = [self._build_embedding_text(card) for card in batch]
            
            embeddings = await self.embedding_service.get_embeddings_batch(texts)
            
            # Update cards with embeddings
            for card, embedding in zip(batch, embeddings):
                if embedding:
                    await self.db.failure_cards.update_one(
                        {"failure_id": card["failure_id"]},
                        {"$set": {
                            "embedding_vector": embedding,
                            "embedding_updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    processed += 1
                else:
                    errors += 1
            
            logger.info(f"Processed batch {i // batch_size + 1}: {processed} successful, {errors} errors")
        
        return {
            "status": "complete",
            "total_cards": len(cards),
            "processed": processed,
            "errors": errors
        }
    
    async def update_card_embedding(self, failure_id: str) -> bool:
        """
        Update embedding for a specific card (after card update).
        """
        card = await self.db.failure_cards.find_one(
            {"failure_id": failure_id},
            {"_id": 0}
        )
        
        if not card:
            return False
        
        embedding = await self.embed_failure_card(card)
        
        if embedding:
            await self.db.failure_cards.update_one(
                {"failure_id": failure_id},
                {"$set": {
                    "embedding_vector": embedding,
                    "embedding_updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return True
        
        return False


# Service factory
_embedding_service: Optional[EmbeddingService] = None
_card_embedder: Optional[FailureCardEmbedder] = None


def get_embedding_service() -> EmbeddingService:
    if _embedding_service is None:
        raise ValueError("EmbeddingService not initialized")
    return _embedding_service


def get_card_embedder() -> FailureCardEmbedder:
    if _card_embedder is None:
        raise ValueError("FailureCardEmbedder not initialized")
    return _card_embedder


def init_embedding_service(db) -> tuple:
    """Initialize embedding service and card embedder."""
    global _embedding_service, _card_embedder
    _embedding_service = EmbeddingService(db)
    _card_embedder = FailureCardEmbedder(_embedding_service, db)
    logger.info("Embedding services initialized")
    return _embedding_service, _card_embedder
