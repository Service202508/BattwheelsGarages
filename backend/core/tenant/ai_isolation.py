"""
Tenant-Isolated Vector Storage Service (Phase E)
================================================

Provides tenant-isolated vector storage and retrieval for the AI/RAG system.
Each organization's embeddings are namespaced to prevent cross-tenant data leakage.

Architecture:
- Vector namespace: {collection}_{organization_id}
- All similarity searches scoped to organization
- Embedding storage includes organization_id
- Query filtering enforces tenant boundaries

Security:
- Default-deny on missing organization_id
- Audit logging for all vector operations
- No cross-org aggregations allowed
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
import logging
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """A document with vector embedding, scoped to organization"""
    doc_id: str
    organization_id: str
    collection: str  # e.g., "failure_cards", "knowledge_base"
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "organization_id": self.organization_id,
            "collection": self.collection,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @property
    def namespace(self) -> str:
        """Get the tenant-specific namespace"""
        return f"{self.collection}_{self.organization_id}"


@dataclass
class SimilarityResult:
    """Result from similarity search"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    organization_id: str


class TenantVectorStorage:
    """
    Tenant-isolated vector storage using MongoDB.
    
    Each organization's vectors are stored with organization_id and
    all queries are automatically filtered by organization.
    
    This provides a simpler alternative to dedicated vector databases
    while maintaining strict tenant isolation.
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.vector_embeddings
        self._index_created = False
    
    async def ensure_indexes(self):
        """Create necessary indexes for efficient vector queries"""
        if self._index_created:
            return
        
        try:
            # Compound index for tenant-scoped queries
            await self.collection.create_index([
                ("organization_id", 1),
                ("collection", 1)
            ])
            
            # Index for doc_id lookups
            await self.collection.create_index([
                ("doc_id", 1),
                ("organization_id", 1)
            ], unique=True)
            
            self._index_created = True
            logger.info("Vector storage indexes created")
        except Exception as e:
            logger.warning(f"Index creation skipped: {e}")
    
    async def store_vector(
        self,
        doc_id: str,
        organization_id: str,
        collection: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorDocument:
        """
        Store a vector embedding for a document.
        
        Args:
            doc_id: Unique document identifier
            organization_id: Organization ID (required - Phase E security)
            collection: Collection name (e.g., "failure_cards")
            content: Original text content
            embedding: Vector embedding
            metadata: Additional metadata
        
        Returns:
            Created VectorDocument
        """
        if not organization_id:
            raise ValueError("organization_id is required for vector storage")
        
        await self.ensure_indexes()
        
        doc = VectorDocument(
            doc_id=doc_id,
            organization_id=organization_id,
            collection=collection,
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        # Upsert to allow updates
        await self.collection.update_one(
            {"doc_id": doc_id, "organization_id": organization_id},
            {"$set": doc.to_dict()},
            upsert=True
        )
        
        logger.debug(f"Stored vector for {doc_id} in {doc.namespace}")
        return doc
    
    async def delete_vector(
        self,
        doc_id: str,
        organization_id: str
    ) -> bool:
        """Delete a vector by doc_id (scoped to organization)"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        result = await self.collection.delete_one({
            "doc_id": doc_id,
            "organization_id": organization_id
        })
        return result.deleted_count > 0
    
    async def get_vector(
        self,
        doc_id: str,
        organization_id: str
    ) -> Optional[VectorDocument]:
        """Get a vector by doc_id (scoped to organization)"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        doc = await self.collection.find_one(
            {"doc_id": doc_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if doc:
            return VectorDocument(**doc)
        return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        organization_id: str,
        collection: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[SimilarityResult]:
        """
        Find similar documents using cosine similarity.
        
        CRITICAL: Always filtered by organization_id to prevent data leakage.
        
        Args:
            query_embedding: Query vector
            organization_id: Organization ID (REQUIRED - Phase E)
            collection: Optional collection filter
            limit: Max results
            min_score: Minimum similarity score
        
        Returns:
            List of similar documents with scores
        """
        if not organization_id:
            raise ValueError("organization_id is required for similarity search (Phase E security)")
        
        # Build query - ALWAYS include organization_id
        query = {"organization_id": organization_id}
        if collection:
            query["collection"] = collection
        
        # Fetch candidate documents
        docs = await self.collection.find(query, {"_id": 0}).to_list(1000)
        
        # Calculate similarities
        results = []
        for doc in docs:
            score = self._cosine_similarity(query_embedding, doc["embedding"])
            if score >= min_score:
                results.append(SimilarityResult(
                    doc_id=doc["doc_id"],
                    content=doc["content"],
                    score=score,
                    metadata=doc.get("metadata", {}),
                    organization_id=doc["organization_id"]
                ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"Similarity search in org {organization_id}: {len(results)} results")
        return results[:limit]
    
    async def get_collection_stats(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get vector storage statistics for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        pipeline = [
            {"$match": {"organization_id": organization_id}},
            {"$group": {
                "_id": "$collection",
                "count": {"$sum": 1}
            }}
        ]
        
        collection_counts = {}
        async for doc in self.collection.aggregate(pipeline):
            collection_counts[doc["_id"]] = doc["count"]
        
        total = sum(collection_counts.values())
        
        return {
            "organization_id": organization_id,
            "total_vectors": total,
            "by_collection": collection_counts
        }


class TenantAIService:
    """
    Tenant-isolated AI/RAG service for failure intelligence.
    
    Combines embedding generation with tenant-scoped vector storage
    to provide organization-isolated AI features.
    """
    
    def __init__(self, db, embedding_service=None):
        self.db = db
        self.vector_storage = TenantVectorStorage(db)
        self.embedding_service = embedding_service
    
    def set_embedding_service(self, service):
        """Set the embedding service (for late initialization)"""
        self.embedding_service = service
    
    async def index_failure_card(
        self,
        failure_id: str,
        organization_id: str,
        title: str,
        description: str,
        symptoms: List[str],
        resolution_steps: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorDocument:
        """
        Index a failure card for similarity search.
        
        Creates a searchable vector representation of the failure card
        that is isolated to the organization.
        """
        if not organization_id:
            raise ValueError("organization_id is required for indexing")
        
        # Combine fields for embedding
        content = f"{title}\n{description}\nSymptoms: {', '.join(symptoms)}\nResolution: {', '.join(resolution_steps)}"
        
        # Generate embedding
        if self.embedding_service:
            response = await self.embedding_service.embed_text(content)
            embedding = response.embedding
        else:
            # Fallback to hash-based embedding
            embedding = self._hash_embedding(content)
        
        # Store with organization scope
        doc = await self.vector_storage.store_vector(
            doc_id=failure_id,
            organization_id=organization_id,
            collection="failure_cards",
            content=content,
            embedding=embedding,
            metadata={
                "title": title,
                "type": "failure_card",
                **(metadata or {})
            }
        )
        
        logger.info(f"Indexed failure card {failure_id} for org {organization_id}")
        return doc
    
    async def search_similar_failures(
        self,
        query: str,
        organization_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar failure cards based on a query.
        
        Results are strictly isolated to the organization.
        """
        if not organization_id:
            raise ValueError("organization_id is required for search")
        
        # Generate query embedding
        if self.embedding_service:
            response = await self.embedding_service.embed_text(query)
            query_embedding = response.embedding
        else:
            query_embedding = self._hash_embedding(query)
        
        # Search within organization
        results = await self.vector_storage.similarity_search(
            query_embedding=query_embedding,
            organization_id=organization_id,
            collection="failure_cards",
            limit=limit
        )
        
        return [
            {
                "failure_id": r.doc_id,
                "content": r.content,
                "score": r.score,
                "metadata": r.metadata
            }
            for r in results
        ]
    
    def _hash_embedding(self, text: str, dim: int = 256) -> List[float]:
        """Simple hash-based embedding for fallback"""
        import math
        
        text_lower = text.lower().strip()
        hash_bytes = hashlib.sha256(text_lower.encode()).digest()
        
        values = []
        for i in range(dim):
            byte_idx = i % len(hash_bytes)
            values.append((hash_bytes[byte_idx] / 255.0) * 2 - 1)
        
        # Normalize
        norm = math.sqrt(sum(x * x for x in values))
        if norm > 0:
            values = [x / norm for x in values]
        
        return values


# ==================== SERVICE SINGLETON ====================

_tenant_ai_service: Optional[TenantAIService] = None


def init_tenant_ai_service(db, embedding_service=None) -> TenantAIService:
    """Initialize the tenant AI service singleton"""
    global _tenant_ai_service
    _tenant_ai_service = TenantAIService(db, embedding_service)
    logger.info("TenantAIService initialized (Phase E)")
    return _tenant_ai_service


def get_tenant_ai_service() -> TenantAIService:
    """Get the tenant AI service singleton"""
    if _tenant_ai_service is None:
        raise RuntimeError("TenantAIService not initialized")
    return _tenant_ai_service
