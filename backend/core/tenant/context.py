"""
Tenant Context Module
====================

The TenantContext is the CENTRAL object that flows through the entire request lifecycle.
Every service, repository, and event emitter receives this context.

Key Design Principles:
1. Context is REQUIRED for all non-public endpoints
2. Context is IMMUTABLE once created
3. Context propagates to all async operations
4. Context contains full RBAC information

Usage:
    @router.get("/items")
    async def get_items(ctx: TenantContext = Depends(tenant_context_required)):
        # ctx.org_id is guaranteed to be valid
        items = await item_service.list(ctx)
        return items
"""

from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from contextvars import ContextVar
from fastapi import Request, HTTPException
from pydantic import BaseModel, Field
import uuid
import logging

from .exceptions import TenantContextMissing, TenantAccessDenied, TenantSuspended

logger = logging.getLogger(__name__)

# Context variable for async propagation
_tenant_context: ContextVar[Optional['TenantContext']] = ContextVar('tenant_context', default=None)


class TenantPlan(str, Enum):
    """Tenant subscription plans with feature limits"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status states"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    TRIAL = "trial"


@dataclass(frozen=True)
class TenantContext:
    """
    Immutable tenant context object.
    
    This object is created once per request and propagated through all layers.
    It contains everything needed to enforce tenant isolation.
    
    Attributes:
        org_id: Organization ID (primary isolation key)
        user_id: Current user ID
        user_role: User's role in this organization
        permissions: Set of permission strings
        plan: Tenant's subscription plan
        status: Tenant's current status
        request_id: Unique request identifier for tracing
        created_at: When this context was created
    """
    org_id: str
    user_id: str
    user_role: str
    permissions: frozenset = field(default_factory=frozenset)
    plan: TenantPlan = TenantPlan.STARTER
    status: TenantStatus = TenantStatus.ACTIVE
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Organization metadata (readonly)
    org_name: str = ""
    org_slug: str = ""
    
    # Feature flags
    features: frozenset = field(default_factory=frozenset)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if "*" in self.permissions:
            return True
        if permission in self.permissions:
            return True
        # Check wildcard (e.g., "tickets:*" covers "tickets:read")
        resource = permission.split(":")[0]
        if f"{resource}:*" in self.permissions:
            return True
        return False
    
    def require_permission(self, permission: str) -> None:
        """Raise exception if permission not granted"""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}"
            )
    
    def has_feature(self, feature: str) -> bool:
        """Check if tenant has access to a feature"""
        return feature in self.features
    
    def scope_query(self, base_query: Dict = None) -> Dict[str, Any]:
        """Create org-scoped MongoDB query"""
        query = {"organization_id": self.org_id}
        if base_query:
            query.update(base_query)
        return query
    
    def scope_document(self, doc: Dict) -> Dict[str, Any]:
        """Add org_id to document before insert"""
        doc["organization_id"] = self.org_id
        return doc
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for logging/serialization)"""
        return {
            "org_id": self.org_id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "permissions": list(self.permissions),
            "plan": self.plan.value,
            "status": self.status.value,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat(),
            "org_name": self.org_name,
            "org_slug": self.org_slug,
            "features": list(self.features)
        }
    
    def to_event_metadata(self) -> Dict[str, Any]:
        """Extract metadata for event emission"""
        return {
            "organization_id": self.org_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "timestamp": self.created_at.isoformat()
        }


class TenantContextManager:
    """
    Manages tenant context resolution and validation.
    
    This is a singleton that handles:
    - Resolving org_id from request (header/param/session)
    - Validating user membership
    - Loading permissions and features
    - Caching frequently accessed data
    """
    
    def __init__(self, db):
        self.db = db
        self._permission_cache: Dict[str, Dict] = {}  # Cache role->permissions
        self._org_cache: Dict[str, Dict] = {}  # Cache org_id->org_data (TTL in production)
    
    async def resolve_context(
        self,
        request: Request,
        user_id: str,
        org_id: Optional[str] = None
    ) -> TenantContext:
        """
        Resolve full tenant context from request.
        
        Resolution order for org_id:
        1. Explicit org_id parameter
        2. X-Organization-ID header
        3. org_id query parameter
        4. User's default (first active) organization
        
        Raises:
            TenantContextMissing: If no org_id can be resolved
            TenantAccessDenied: If user is not a member of the organization
            TenantSuspended: If organization is suspended
        """
        # Step 1: Resolve org_id
        resolved_org_id = org_id
        
        if not resolved_org_id:
            resolved_org_id = request.headers.get("X-Organization-ID")
        
        if not resolved_org_id:
            resolved_org_id = request.query_params.get("org_id")
        
        if not resolved_org_id:
            # Get user's default organization
            membership = await self.db.organization_users.find_one({
                "user_id": user_id,
                "status": "active"
            }, {"organization_id": 1})
            
            if membership:
                resolved_org_id = membership.get("organization_id")
        
        if not resolved_org_id:
            raise TenantContextMissing(
                endpoint=request.url.path,
                user_id=user_id,
                metadata={"method": request.method}
            )
        
        # Step 2: Validate membership
        membership = await self.db.organization_users.find_one({
            "user_id": user_id,
            "organization_id": resolved_org_id,
            "status": "active"
        }, {"_id": 0})
        
        if not membership:
            # Get user's actual orgs for logging
            user_orgs_cursor = self.db.organization_users.find(
                {"user_id": user_id, "status": "active"},
                {"organization_id": 1}
            )
            user_orgs = [m["organization_id"] async for m in user_orgs_cursor]
            
            raise TenantAccessDenied(
                user_id=user_id,
                attempted_org_id=resolved_org_id,
                user_orgs=user_orgs
            )
        
        # Step 3: Load organization data
        org = await self.db.organizations.find_one(
            {"organization_id": resolved_org_id},
            {"_id": 0}
        )
        
        if not org:
            raise TenantContextMissing(
                endpoint=request.url.path,
                user_id=user_id,
                metadata={"reason": "organization_not_found", "org_id": resolved_org_id}
            )
        
        # Step 4: Check organization status
        org_status = org.get("is_active", True)
        if not org_status:
            raise TenantSuspended(
                org_id=resolved_org_id,
                suspension_reason=org.get("suspension_reason")
            )
        
        # Step 5: Load permissions for role
        role = membership.get("role", "viewer")
        permissions = await self._get_role_permissions(role)
        
        # Add custom permissions if any
        custom_perms = membership.get("custom_permissions", [])
        all_permissions = set(permissions) | set(custom_perms)
        
        # Step 6: Load tenant features
        features = await self._get_tenant_features(resolved_org_id, org.get("plan_type", "starter"))
        
        # Step 7: Create immutable context
        context = TenantContext(
            org_id=resolved_org_id,
            user_id=user_id,
            user_role=role,
            permissions=frozenset(all_permissions),
            plan=TenantPlan(org.get("plan_type", "starter")),
            status=TenantStatus.ACTIVE,
            request_id=f"req_{uuid.uuid4().hex[:12]}",
            org_name=org.get("name", ""),
            org_slug=org.get("slug", ""),
            features=frozenset(features)
        )
        
        # Step 8: Store in context var for propagation
        _tenant_context.set(context)
        
        # Step 9: Attach to request state
        request.state.tenant_context = context
        
        logger.debug(
            f"Tenant context resolved: org={resolved_org_id}, "
            f"user={user_id}, role={role}, request={context.request_id}"
        )
        
        return context
    
    async def _get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a role (cached)"""
        if role in self._permission_cache:
            return self._permission_cache[role]
        
        # Load from database or use defaults
        from core.org.models import ROLE_PERMISSIONS, OrgUserRole
        
        try:
            role_enum = OrgUserRole(role)
            permissions = ROLE_PERMISSIONS.get(role_enum, [])
        except ValueError:
            permissions = ROLE_PERMISSIONS.get(OrgUserRole.VIEWER, [])
        
        self._permission_cache[role] = permissions
        return permissions
    
    async def _get_tenant_features(self, org_id: str, plan: str) -> List[str]:
        """Get enabled features for tenant based on plan"""
        # Base features available to all
        features = [
            "tickets", "vehicles", "estimates", "invoices",
            "contacts", "inventory"
        ]
        
        if plan in ["starter", "professional", "enterprise"]:
            features.extend([
                "ai_assist", "efi_guidance", "failure_cards",
                "documents", "time_tracking"
            ])
        
        if plan in ["professional", "enterprise"]:
            features.extend([
                "advanced_reports", "zoho_sync", "customer_portal",
                "bulk_operations", "api_access"
            ])
        
        if plan == "enterprise":
            features.extend([
                "white_label", "sso", "dedicated_support",
                "custom_fields", "audit_logs", "data_export"
            ])
        
        # Check for feature flag overrides
        config = await self.db.tenant_ai_config.find_one(
            {"organization_id": org_id},
            {"_id": 0}
        )
        
        if config:
            if config.get("ai_assist_enabled") is False:
                features = [f for f in features if f not in ["ai_assist", "efi_guidance"]]
        
        return features


# Singleton manager
_context_manager: Optional[TenantContextManager] = None


def init_tenant_context_manager(db) -> TenantContextManager:
    """Initialize the tenant context manager"""
    global _context_manager
    _context_manager = TenantContextManager(db)
    logger.info("TenantContextManager initialized")
    return _context_manager


def get_tenant_context_manager() -> TenantContextManager:
    """Get the singleton context manager"""
    if _context_manager is None:
        raise RuntimeError("TenantContextManager not initialized. Call init_tenant_context_manager first.")
    return _context_manager


def get_tenant_context() -> Optional[TenantContext]:
    """Get current tenant context from context var"""
    return _tenant_context.get()


async def tenant_context_required(request: Request) -> TenantContext:
    """
    FastAPI dependency that REQUIRES tenant context.
    
    Usage:
        @router.get("/items")
        async def get_items(ctx: TenantContext = Depends(tenant_context_required)):
            items = await db.items.find(ctx.scope_query()).to_list()
    """
    # Check if already resolved
    if hasattr(request.state, "tenant_context"):
        ctx = request.state.tenant_context
        if ctx is not None:
            return ctx
    
    # Need to resolve - get user first
    from core.org.dependencies import get_user_id_from_request
    
    user_id = await get_user_id_from_request(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Resolve context
    manager = get_tenant_context_manager()
    ctx = await manager.resolve_context(request, user_id)
    
    return ctx


async def optional_tenant_context(request: Request) -> Optional[TenantContext]:
    """
    FastAPI dependency that optionally returns tenant context.
    
    Use for endpoints that work with or without auth.
    """
    try:
        return await tenant_context_required(request)
    except (HTTPException, Exception):
        return None
