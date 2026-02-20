"""
Battwheels Knowledge Brain - Feature Flags Service
Tenant-level feature flag management for AI capabilities
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import motor.motor_asyncio
from functools import wraps
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


# ==================== DEFAULT FEATURE FLAGS ====================

DEFAULT_AI_CONFIG = {
    # Core AI features
    "ai_assist_enabled": True,
    "rag_enabled": True,
    "citations_enabled": True,
    
    # Escalation features
    "expert_queue_enabled": True,
    "zendesk_enabled": False,  # Always false - using internal queue
    
    # EFI Guidance Layer (Hinglish mode)
    "efi_guidance_layer_enabled": True,
    "hinglish_mode_enabled": True,
    "visual_diagrams_enabled": True,
    "ask_back_enabled": True,
    
    # EFI Intelligence Engine (Phase 2)
    "efi_intelligence_engine_enabled": True,
    "model_aware_ranking_enabled": True,
    "continuous_learning_enabled": True,
    "pattern_detection_enabled": True,
    
    # Knowledge management
    "knowledge_ingestion_enabled": True,
    "knowledge_approval_required": True,
    "auto_knowledge_capture": True,
    
    # UI features
    "contextual_suggestions_enabled": True,
    "estimate_suggestions_enabled": True,
    "quick_diagnose_enabled": True,
    
    # Limits
    "daily_query_limit": 1000,
    "max_sources_per_query": 5,
    "max_escalations_per_day": 50,
    
    # Model configuration
    "llm_provider": "gemini",
    "llm_model": "gemini-3-flash-preview",
}


class FeatureFlagService:
    """
    Service for managing tenant-level feature flags.
    
    Features:
    - Get/set tenant AI configuration
    - Check if feature is enabled for tenant
    - Default fallback for unconfigured tenants
    - Rate limiting support
    """
    
    def __init__(self, db: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = db
        self.config_collection = db.tenant_ai_config
        self._cache: Dict[str, Dict] = {}  # Simple in-memory cache
    
    async def get_tenant_config(
        self,
        organization_id: str,
        use_cache: bool = True
    ) -> Dict:
        """
        Get AI configuration for a tenant.
        Returns default config if tenant has no custom config.
        """
        # Check cache first
        if use_cache and organization_id in self._cache:
            return self._cache[organization_id]
        
        config = await self.config_collection.find_one(
            {"organization_id": organization_id},
            {"_id": 0}
        )
        
        if config:
            # Merge with defaults for any missing keys
            merged = {**DEFAULT_AI_CONFIG, **config}
            self._cache[organization_id] = merged
            return merged
        
        # Return defaults
        return {**DEFAULT_AI_CONFIG, "organization_id": organization_id}
    
    async def update_tenant_config(
        self,
        organization_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> Dict:
        """Update tenant AI configuration"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Only allow updating known flags
        allowed_keys = set(DEFAULT_AI_CONFIG.keys())
        filtered_updates = {
            k: v for k, v in updates.items() 
            if k in allowed_keys
        }
        
        filtered_updates["updated_at"] = now
        filtered_updates["updated_by"] = updated_by
        
        await self.config_collection.update_one(
            {"organization_id": organization_id},
            {
                "$set": filtered_updates,
                "$setOnInsert": {
                    "organization_id": organization_id,
                    "created_at": now
                }
            },
            upsert=True
        )
        
        # Clear cache
        if organization_id in self._cache:
            del self._cache[organization_id]
        
        return await self.get_tenant_config(organization_id, use_cache=False)
    
    async def is_feature_enabled(
        self,
        organization_id: str,
        feature_key: str
    ) -> bool:
        """Check if a specific feature is enabled for tenant"""
        config = await self.get_tenant_config(organization_id)
        return config.get(feature_key, DEFAULT_AI_CONFIG.get(feature_key, False))
    
    async def check_rate_limit(
        self,
        organization_id: str,
        limit_key: str = "daily_query_limit"
    ) -> Dict:
        """
        Check if tenant is within rate limits.
        Returns remaining quota and limit status.
        """
        config = await self.get_tenant_config(organization_id)
        limit = config.get(limit_key, DEFAULT_AI_CONFIG.get(limit_key, 1000))
        
        # Get today's usage
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        usage_doc = await self.db.ai_usage.find_one({
            "organization_id": organization_id,
            "date": today
        })
        
        current_usage = usage_doc.get("count", 0) if usage_doc else 0
        remaining = max(0, limit - current_usage)
        
        return {
            "limit": limit,
            "used": current_usage,
            "remaining": remaining,
            "exceeded": remaining <= 0
        }
    
    async def increment_usage(
        self,
        organization_id: str,
        usage_type: str = "query"
    ) -> Dict:
        """Increment usage counter for rate limiting"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        await self.db.ai_usage.update_one(
            {
                "organization_id": organization_id,
                "date": today
            },
            {
                "$inc": {"count": 1, f"{usage_type}_count": 1},
                "$setOnInsert": {
                    "organization_id": organization_id,
                    "date": today,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        return await self.check_rate_limit(organization_id)
    
    async def get_llm_config(self, organization_id: str) -> Dict:
        """Get LLM provider configuration for tenant"""
        config = await self.get_tenant_config(organization_id)
        
        return {
            "provider": config.get("llm_provider", "gemini"),
            "model": config.get("llm_model", "gemini-3-flash-preview"),
            "enabled": config.get("ai_assist_enabled", True)
        }
    
    def clear_cache(self, organization_id: Optional[str] = None):
        """Clear config cache"""
        if organization_id:
            self._cache.pop(organization_id, None)
        else:
            self._cache.clear()


# ==================== MIDDLEWARE / DECORATORS ====================

async def get_feature_flags(request: Request) -> FeatureFlagService:
    """Dependency to get feature flag service"""
    from server import db
    return FeatureFlagService(db)


async def require_ai_enabled(request: Request) -> Dict:
    """
    Dependency that checks if AI is enabled for the organization.
    Raises 403 if AI is disabled.
    """
    from server import db
    
    org_id = request.headers.get("X-Organization-ID", "global")
    service = FeatureFlagService(db)
    
    config = await service.get_tenant_config(org_id)
    
    if not config.get("ai_assist_enabled", True):
        raise HTTPException(
            status_code=403,
            detail="AI assistance is not enabled for your organization."
        )
    
    # Check rate limit
    rate_status = await service.check_rate_limit(org_id)
    if rate_status["exceeded"]:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI query limit ({rate_status['limit']}) exceeded. Please try again tomorrow."
        )
    
    return config


def require_feature(feature_key: str):
    """
    Decorator to require a specific feature flag.
    Usage:
        @require_feature("expert_queue_enabled")
        async def my_endpoint(...):
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            if request is None:
                # Try to find request in args/kwargs
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                from server import db
                org_id = request.headers.get("X-Organization-ID", "global")
                service = FeatureFlagService(db)
                
                if not await service.is_feature_enabled(org_id, feature_key):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Feature '{feature_key}' is not enabled for your organization."
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ==================== GLOBAL FEATURE CHECKS ====================

async def check_ai_available(db: motor.motor_asyncio.AsyncIOMotorDatabase) -> Dict:
    """Check overall AI service availability"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    return {
        "ai_available": bool(api_key),
        "provider": "gemini",
        "model": "gemini-3-flash-preview",
        "features": {
            "rag": True,
            "citations": True,
            "expert_queue": True,
            "knowledge_capture": True
        }
    }
