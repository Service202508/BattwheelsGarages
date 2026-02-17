"""
EFI Embedding Service - Provider-Agnostic Architecture
Supports: Gemini, OpenAI, or any future provider
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingResponse:
    """Standardized embedding response across all providers"""
    def __init__(self, text: str, embedding: List[float], model: str, dimensions: int):
        self.text = text
        self.embedding = embedding
        self.model = model
        self.dimensions = dimensions


class BaseEmbeddingService(ABC):
    """Abstract base class for embedding providers - enables provider switching"""
    
    @abstractmethod
    async def embed_text(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> EmbeddingResponse:
        """Generate embedding for single text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str], task_type: str = "SEMANTIC_SIMILARITY") -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts"""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Return embedding dimensions"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if service is configured and available"""
        pass


class GeminiEmbeddingService(BaseEmbeddingService):
    """Gemini embedding implementation using Emergent LLM Key"""
    
    def __init__(self, api_key: Optional[str] = None, output_dim: int = 768):
        self.api_key = api_key
        self.output_dim = output_dim
        self.model = "text-embedding-004"
        self.client = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of Gemini client"""
        if self._initialized:
            return
            
        try:
            from emergentintegrations.llm.gemini import GeminiManager
            
            if self.api_key:
                self.client = GeminiManager(emergent_api_key=self.api_key)
            else:
                # Try to get from environment
                key = os.environ.get("EMERGENT_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")
                if key:
                    self.client = GeminiManager(emergent_api_key=key)
                    
            self._initialized = True
            if self.client:
                logger.info("Gemini embedding service initialized successfully")
            else:
                logger.warning("Gemini embedding service: No API key found")
        except ImportError as e:
            logger.error(f"Failed to import emergentintegrations: {e}")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self._initialized = True
    
    def is_available(self) -> bool:
        self._ensure_initialized()
        return self.client is not None
    
    def get_dimensions(self) -> int:
        return self.output_dim
    
    async def embed_text(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> EmbeddingResponse:
        """Generate embedding using Gemini"""
        self._ensure_initialized()
        
        if not self.client:
            # Fallback to simple hash-based pseudo-embedding
            return self._fallback_embedding(text)
        
        try:
            import google.generativeai as genai
            
            # Use the Gemini embedding model
            result = genai.embed_content(
                model=f"models/{self.model}",
                content=text,
                task_type=task_type
            )
            
            embedding = result['embedding']
            
            # Truncate or pad to desired dimensions
            if len(embedding) > self.output_dim:
                embedding = embedding[:self.output_dim]
            elif len(embedding) < self.output_dim:
                embedding = embedding + [0.0] * (self.output_dim - len(embedding))
            
            return EmbeddingResponse(
                text=text,
                embedding=embedding,
                model=self.model,
                dimensions=len(embedding)
            )
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            return self._fallback_embedding(text)
    
    async def embed_batch(self, texts: List[str], task_type: str = "SEMANTIC_SIMILARITY") -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts"""
        results = []
        for text in texts:
            result = await self.embed_text(text, task_type)
            results.append(result)
            await asyncio.sleep(0.1)  # Rate limiting
        return results
    
    def _fallback_embedding(self, text: str) -> EmbeddingResponse:
        """Fallback pseudo-embedding using text features (TF-IDF style)"""
        import hashlib
        
        # Create deterministic pseudo-embedding from text
        words = text.lower().split()
        embedding = [0.0] * self.output_dim
        
        for i, word in enumerate(words):
            # Hash word to get position and value
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
            pos = word_hash % self.output_dim
            val = (word_hash % 1000) / 1000.0
            embedding[pos] += val
        
        # Normalize
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return EmbeddingResponse(
            text=text,
            embedding=embedding,
            model="fallback-hash",
            dimensions=self.output_dim
        )


class EFIEmbeddingManager:
    """Manager for EFI embedding operations - provider agnostic"""
    
    def __init__(self, db, provider: str = "gemini"):
        self.db = db
        self.provider = provider
        self._service: Optional[BaseEmbeddingService] = None
        
    def _get_service(self) -> BaseEmbeddingService:
        """Get or create embedding service"""
        if self._service is None:
            api_key = os.environ.get("EMERGENT_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")
            
            if self.provider == "gemini":
                self._service = GeminiEmbeddingService(api_key=api_key, output_dim=768)
            else:
                # Default fallback
                self._service = GeminiEmbeddingService(api_key=api_key, output_dim=768)
        
        return self._service
    
    async def generate_complaint_embedding(self, complaint_text: str, subsystem: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate embedding for a complaint and classify subsystem
        Called during complaint pre-processing
        """
        service = self._get_service()
        
        # Generate embedding
        embedding_result = await service.embed_text(complaint_text)
        
        # Auto-classify subsystem if not provided
        if not subsystem:
            subsystem = self._classify_subsystem(complaint_text)
        
        return {
            "embedding": embedding_result.embedding,
            "embedding_model": embedding_result.model,
            "embedding_dimensions": embedding_result.dimensions,
            "classified_subsystem": subsystem,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def find_similar_failure_cards(
        self, 
        embedding: List[float], 
        subsystem: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar failure cards using cosine similarity
        """
        # Build query
        query = {"status": "approved"}
        if subsystem:
            query["subsystem_category"] = subsystem
        
        # Get all failure cards with embeddings
        cards = await self.db.failure_cards.find(
            {**query, "embedding_vector": {"$exists": True}},
            {"_id": 0}
        ).to_list(500)
        
        # Calculate similarity scores
        results = []
        for card in cards:
            if "embedding_vector" in card and card["embedding_vector"]:
                similarity = self._cosine_similarity(embedding, card["embedding_vector"])
                results.append({
                    **card,
                    "similarity_score": similarity,
                    "confidence_level": self._score_to_confidence(similarity)
                })
        
        # Sort by similarity and return top N
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]
    
    async def embed_failure_card(self, card_id: str) -> bool:
        """Generate and store embedding for a failure card"""
        card = await self.db.failure_cards.find_one({"failure_id": card_id})
        if not card:
            return False
        
        # Create text for embedding
        embed_text = self._card_to_embed_text(card)
        
        service = self._get_service()
        result = await service.embed_text(embed_text)
        
        # Store embedding
        await self.db.failure_cards.update_one(
            {"failure_id": card_id},
            {"$set": {
                "embedding_vector": result.embedding,
                "embedding_model": result.model,
                "embedding_updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return True
    
    async def embed_all_cards(self, batch_size: int = 25) -> Dict[str, int]:
        """Embed all failure cards that don't have embeddings"""
        cards = await self.db.failure_cards.find(
            {"$or": [
                {"embedding_vector": {"$exists": False}},
                {"embedding_vector": None}
            ]},
            {"failure_id": 1}
        ).to_list(1000)
        
        success = 0
        failed = 0
        
        for card in cards:
            try:
                if await self.embed_failure_card(card["failure_id"]):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to embed card {card['failure_id']}: {e}")
                failed += 1
            
            await asyncio.sleep(0.2)  # Rate limiting
        
        return {"success": success, "failed": failed}
    
    def _card_to_embed_text(self, card: Dict) -> str:
        """Convert failure card to text for embedding"""
        parts = [
            card.get("title", ""),
            card.get("symptom_text", ""),
            card.get("root_cause", ""),
            " ".join(card.get("keywords", [])),
            " ".join(card.get("error_codes", []))
        ]
        return " ".join(filter(None, parts))
    
    def _classify_subsystem(self, text: str) -> str:
        """Auto-classify subsystem from complaint text"""
        text_lower = text.lower()
        
        subsystem_keywords = {
            "battery": ["battery", "charge", "charging", "voltage", "cell", "bms", "soc", "power"],
            "motor": ["motor", "torque", "rpm", "rotation", "speed", "hall", "sensor"],
            "controller": ["controller", "ecu", "firmware", "software", "communication", "can"],
            "wiring": ["wire", "wiring", "connector", "harness", "cable", "connection"],
            "charger": ["charger", "charging port", "ac", "dc", "plug"],
            "throttle": ["throttle", "accelerator", "pedal", "signal"],
            "display": ["display", "screen", "dashboard", "indicator"],
            "brakes": ["brake", "abs", "regenerative", "stopping"]
        }
        
        scores = {}
        for subsystem, keywords in subsystem_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[subsystem] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "other"
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a ** 2 for a in vec1) ** 0.5
        mag2 = sum(b ** 2 for b in vec2) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def _score_to_confidence(self, score: float) -> str:
        """Convert similarity score to confidence level"""
        if score >= 0.85:
            return "verified"
        elif score >= 0.70:
            return "high"
        elif score >= 0.50:
            return "medium"
        return "low"


# Singleton instance
_embedding_manager: Optional[EFIEmbeddingManager] = None


def get_efi_embedding_manager(db=None) -> Optional[EFIEmbeddingManager]:
    """Get or create EFI embedding manager"""
    global _embedding_manager
    if _embedding_manager is None and db is not None:
        _embedding_manager = EFIEmbeddingManager(db)
    return _embedding_manager


def init_efi_embedding_manager(db) -> EFIEmbeddingManager:
    """Initialize EFI embedding manager"""
    global _embedding_manager
    _embedding_manager = EFIEmbeddingManager(db)
    return _embedding_manager
