"""
Tenant Guard Module
==================

The TenantGuard is the ENFORCEMENT layer that prevents cross-tenant access.

Key Responsibilities:
1. Validate org_id on every query
2. Block queries without org_id on tenant tables
3. Detect and log boundary violations
4. Provide middleware for automatic enforcement

This is the SECURITY CORE - all database operations must pass through guards.
"""

from typing import Optional, Dict, Any, List, Set, Callable
from datetime import datetime, timezone
from functools import wraps
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
import re
import os

from .context import TenantContext, get_tenant_context
from .exceptions import (
    TenantBoundaryViolation,
    TenantDataLeakAttempt,
    TenantContextMissing
)

logger = logging.getLogger(__name__)


# Collections that MUST have organization_id
TENANT_COLLECTIONS = {
    # Core business data
    "tickets", "vehicles", "invoices", "estimates", "payments",
    "contacts", "customers", "items", "inventory", "suppliers",
    "purchase_orders", "sales_orders", "expenses", "bills",
    "credit_notes", "vendor_credits", "recurring_invoices",
    "delivery_challans", "salesorders", "purchaseorders",
    
    # Operations
    "amc_plans", "amc_subscriptions", "time_entries",
    "documents", "document_folders", "allocations",
    
    # HR & Payroll
    "employees", "attendance", "leave_requests", "payroll_records",
    
    # EFI Intelligence
    "failure_cards", "technician_actions", "part_usage",
    "ai_guidance_snapshots", "ai_guidance_feedback",
    "model_risk_alerts", "structured_failure_cards",
    "expert_escalations", "learning_events",
    
    # Knowledge
    "knowledge_articles", "knowledge_embeddings",
    "error_code_definitions", "fault_trees",
    
    # Settings & Config
    "organization_settings", "custom_fields", "workflow_rules",
    "pdf_templates", "notification_preferences",
    
    # Financial
    "ledger", "journal_entries", "bank_accounts",
    "bank_transactions", "reconciliations", "chart_of_accounts",
    
    # Stock
    "stock", "stock_transfers", "warehouses",
    "serial_numbers", "batch_numbers",
    
    # Enhanced modules
    "items_enhanced", "contacts_enhanced", "invoices_enhanced",
    "estimates_enhanced", "bills_enhanced",
    
    # Ticket estimates
    "ticket_estimates", "ticket_estimate_line_items", "ticket_estimate_history",
    
    # Zoho sync
    "zoho_sync_mappings",
}

# Collections that are GLOBAL (no org_id required)
GLOBAL_COLLECTIONS = {
    "users", "user_sessions", "organizations", "organization_users",
    "audit_logs", "event_log", "sync_jobs", "sync_status", "sync_events",
    "webhook_logs", "realtime_events", "ai_usage", "tenant_ai_config",
    "role_permissions", "system_settings", "feature_flags",
    "master_vehicle_categories", "master_vehicle_models", "master_issue_types",
    "taxes", "currencies", "countries", "states",
}

# Collections that need special handling
MIXED_SCOPE_COLLECTIONS = {
    # These have both global and tenant-scoped records
    "failure_cards": "scope",  # scope field: "global" or "tenant"
    "knowledge_articles": "scope",
}


class TenantGuard:
    """
    Central guard for tenant isolation enforcement.
    
    This class provides methods to validate queries and operations
    against tenant boundaries.
    """
    
    def __init__(self, db):
        self.db = db
        self._violation_count = 0
        self._last_violations: List[Dict] = []  # Keep last 100
    
    def validate_query(
        self,
        collection: str,
        query: Dict[str, Any],
        ctx: TenantContext,
        operation: str = "read"
    ) -> Dict[str, Any]:
        """
        Validate and augment a query with tenant isolation.
        
        Args:
            collection: MongoDB collection name
            query: The query dict
            ctx: Current tenant context
            operation: Type of operation (read/write/delete)
        
        Returns:
            Modified query with org_id filter
        
        Raises:
            TenantBoundaryViolation: If query violates tenant boundaries
        """
        # Global collections don't need org_id
        if collection in GLOBAL_COLLECTIONS:
            return query
        
        # Tenant collections MUST have org_id
        if collection in TENANT_COLLECTIONS:
            if "organization_id" not in query:
                # Auto-inject org_id from context
                query["organization_id"] = ctx.org_id
                logger.debug(f"Auto-injected org_id={ctx.org_id} for {collection}")
            elif query["organization_id"] != ctx.org_id:
                # CRITICAL: Attempt to access other tenant's data
                self._record_violation(
                    operation=operation,
                    collection=collection,
                    current_org=ctx.org_id,
                    attempted_org=query["organization_id"],
                    user_id=ctx.user_id
                )
                raise TenantBoundaryViolation(
                    operation=operation,
                    collection=collection,
                    current_org_id=ctx.org_id,
                    violation_type="cross_tenant_query",
                    query={"attempted_org": query["organization_id"]}
                )
        
        # Mixed scope collections
        if collection in MIXED_SCOPE_COLLECTIONS:
            scope_field = MIXED_SCOPE_COLLECTIONS[collection]
            # Allow global scope OR matching org_id
            query["$or"] = query.get("$or", [])
            query["$or"].extend([
                {scope_field: "global"},
                {"organization_id": ctx.org_id}
            ])
        
        return query
    
    def validate_document(
        self,
        collection: str,
        document: Dict[str, Any],
        ctx: TenantContext,
        operation: str = "insert"
    ) -> Dict[str, Any]:
        """
        Validate and augment a document with org_id before insert.
        
        Args:
            collection: Target collection
            document: Document to insert
            ctx: Tenant context
            operation: insert/update/upsert
        
        Returns:
            Document with org_id added
        
        Raises:
            TenantBoundaryViolation: If document has wrong org_id
        """
        if collection in GLOBAL_COLLECTIONS:
            return document
        
        if collection in TENANT_COLLECTIONS:
            if "organization_id" not in document:
                document["organization_id"] = ctx.org_id
            elif document["organization_id"] != ctx.org_id:
                self._record_violation(
                    operation=operation,
                    collection=collection,
                    current_org=ctx.org_id,
                    attempted_org=document["organization_id"],
                    user_id=ctx.user_id
                )
                raise TenantBoundaryViolation(
                    operation=operation,
                    collection=collection,
                    current_org_id=ctx.org_id,
                    violation_type="cross_tenant_insert",
                    query={"document_org": document["organization_id"]}
                )
        
        return document
    
    def validate_aggregation(
        self,
        collection: str,
        pipeline: List[Dict],
        ctx: TenantContext
    ) -> List[Dict]:
        """
        Validate aggregation pipeline starts with org_id filter.
        
        CRITICAL: Aggregations MUST start with $match on organization_id
        to prevent cross-tenant data leakage.
        """
        if collection in GLOBAL_COLLECTIONS:
            return pipeline
        
        if collection not in TENANT_COLLECTIONS:
            return pipeline
        
        # Check if first stage is $match with org_id
        if not pipeline:
            # Empty pipeline - add match
            return [{"$match": {"organization_id": ctx.org_id}}] + pipeline
        
        first_stage = pipeline[0]
        if "$match" not in first_stage:
            # First stage is not $match - inject one
            pipeline.insert(0, {"$match": {"organization_id": ctx.org_id}})
        else:
            # Verify $match includes org_id
            match_stage = first_stage["$match"]
            if "organization_id" not in match_stage:
                match_stage["organization_id"] = ctx.org_id
            elif match_stage["organization_id"] != ctx.org_id:
                raise TenantDataLeakAttempt(
                    operation="aggregation",
                    source_org_id=ctx.org_id,
                    potential_leak_reason="aggregation_pipeline_wrong_org",
                    affected_collections=[collection]
                )
        
        # Check for $lookup stages that might cross tenants
        for i, stage in enumerate(pipeline):
            if "$lookup" in stage:
                lookup = stage["$lookup"]
                from_collection = lookup.get("from", "")
                
                if from_collection in TENANT_COLLECTIONS:
                    # Ensure lookup has org_id filter in pipeline
                    lookup_pipeline = lookup.get("pipeline", [])
                    if not lookup_pipeline or "$match" not in lookup_pipeline[0]:
                        logger.warning(
                            f"$lookup on tenant collection {from_collection} "
                            f"missing org_id filter in pipeline"
                        )
        
        return pipeline
    
    def validate_update(
        self,
        collection: str,
        filter_query: Dict[str, Any],
        update_doc: Dict[str, Any],
        ctx: TenantContext
    ) -> tuple:
        """
        Validate update operation.
        
        Returns:
            Tuple of (validated_filter, validated_update)
        """
        # Validate filter has org_id
        filter_query = self.validate_query(collection, filter_query, ctx, "update")
        
        # Prevent changing organization_id
        if "$set" in update_doc and "organization_id" in update_doc["$set"]:
            if update_doc["$set"]["organization_id"] != ctx.org_id:
                raise TenantBoundaryViolation(
                    operation="update",
                    collection=collection,
                    current_org_id=ctx.org_id,
                    violation_type="org_id_modification_attempt",
                    query={"attempted_new_org": update_doc["$set"]["organization_id"]}
                )
        
        return filter_query, update_doc
    
    def validate_delete(
        self,
        collection: str,
        filter_query: Dict[str, Any],
        ctx: TenantContext
    ) -> Dict[str, Any]:
        """Validate delete operation has org_id"""
        return self.validate_query(collection, filter_query, ctx, "delete")
    
    def _record_violation(
        self,
        operation: str,
        collection: str,
        current_org: str,
        attempted_org: str,
        user_id: str
    ):
        """Record a violation for security auditing"""
        self._violation_count += 1
        
        violation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "collection": collection,
            "current_org": current_org,
            "attempted_org": attempted_org,
            "user_id": user_id
        }
        
        self._last_violations.append(violation)
        if len(self._last_violations) > 100:
            self._last_violations = self._last_violations[-100:]
        
        # Log as security warning
        logger.warning(
            f"TENANT BOUNDARY VIOLATION: {operation} on {collection} "
            f"by user {user_id} (org: {current_org} → attempted: {attempted_org})"
        )
    
    def get_violation_stats(self) -> Dict[str, Any]:
        """Get violation statistics for monitoring"""
        return {
            "total_violations": self._violation_count,
            "recent_violations": self._last_violations[-10:],
        }


# Singleton guard
_tenant_guard: Optional[TenantGuard] = None


def init_tenant_guard(db) -> TenantGuard:
    """Initialize the tenant guard"""
    global _tenant_guard
    _tenant_guard = TenantGuard(db)
    logger.info("TenantGuard initialized")
    return _tenant_guard


def get_tenant_guard() -> TenantGuard:
    """Get the singleton guard"""
    if _tenant_guard is None:
        raise RuntimeError("TenantGuard not initialized")
    return _tenant_guard


class TenantGuardMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that ENFORCES tenant context on ALL requests.
    
    CRITICAL SECURITY COMPONENT:
    - Blocks ALL non-public requests without valid tenant context
    - Validates user membership in organization
    - Sets tenant context for downstream handlers
    
    Exceptions (Public routes):
    - Health checks
    - Auth endpoints (login/register)
    - Public ticket/invoice views
    - Webhook endpoints
    """
    
    # Database reference
    _db = None
    _jwt_secret = None
    
    # JWT settings
    JWT_ALGORITHM = "HS256"
    
    @classmethod
    def get_jwt_secret(cls):
        """Get JWT secret lazily to ensure .env is loaded first"""
        if cls._jwt_secret is None:
            cls._jwt_secret = os.environ.get('JWT_SECRET', 'battwheels-secret')
        return cls._jwt_secret
    
    # Endpoints that don't require tenant context
    PUBLIC_ENDPOINTS = {
        # Health
        "/api/health",
        "/api/",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        
        # Auth
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/session",
        "/api/auth/logout",
        "/api/auth/me",
        "/api/auth/google",
        "/api/auth/forgot-password",
        "/api/auth/reset-password",
        
        # Public forms
        "/api/public/tickets/submit",
        "/api/public/tickets/lookup",
        "/api/public/tickets/verify-payment",
        "/api/public/track",
        "/api/track-ticket",
        
        # Master data (read-only public)
        "/api/master-data/vehicle-categories",
        "/api/master-data/vehicle-models",
        "/api/master-data/issue-suggestions",
        "/api/org/roles",
        
        # Portal registration
        "/api/customer-portal/login",
        "/api/customer-portal/auth",
        "/api/business-portal/register",
    }
    
    # Patterns for public endpoints
    PUBLIC_PATTERNS = [
        r"^/api/public/.*",
        r"^/api/webhooks/.*",
        r"^/api/razorpay/webhook$",
        r"^/api/stripe/webhook$",
        r"^/api/invoices/public/.*",
        r"^/api/estimates/public/.*",
        r"^/api/quotes/public/.*",
        r"^/static/.*",
    ]
    
    @classmethod
    def set_db(cls, db):
        """Set database reference"""
        cls._db = db
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Skip OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            return await call_next(request)
        
        # Skip public endpoints
        if self._is_public(path):
            logger.debug(f"Public route, skipping tenant check: {path}")
            return await call_next(request)
        
        # === ENFORCEMENT MODE: All other routes MUST have tenant context ===
        
        try:
            # Extract JWT claims
            user_id, token_org_id, user_role = await self._extract_jwt_claims(request)
            
            if not user_id:
                logger.warning(f"TENANT GUARD: No auth for protected route {path}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required", "code": "AUTH_REQUIRED"}
                )
            
            # Resolve organization_id
            org_id = await self._resolve_org_id(request, user_id, token_org_id)
            
            if not org_id:
                logger.warning(f"TENANT GUARD: No org context for user {user_id} on {path}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Organization context required. Use X-Organization-ID header or select an organization.",
                        "code": "TENANT_CONTEXT_MISSING"
                    }
                )
            
            # CRITICAL: Validate user is member of this organization
            is_member = await self._validate_membership(user_id, org_id)
            
            if not is_member:
                logger.error(
                    f"SECURITY ALERT: Cross-tenant access attempt! "
                    f"User {user_id} tried to access org {org_id} on {path}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Access denied. You are not a member of this organization.",
                        "code": "TENANT_ACCESS_DENIED"
                    }
                )
            
            # Set tenant context on request state for downstream handlers
            request.state.tenant_org_id = org_id
            request.state.tenant_user_id = user_id
            request.state.tenant_user_role = user_role or "viewer"
            
            # Also try to build full TenantContext for routes that use it
            try:
                from .context import TenantContext, TenantPlan, TenantStatus
                from core.org.models import ROLE_PERMISSIONS, OrgUserRole
                
                # Get permissions for role
                try:
                    role_enum = OrgUserRole(user_role) if user_role else OrgUserRole.VIEWER
                    permissions = ROLE_PERMISSIONS.get(role_enum, [])
                except ValueError:
                    permissions = ROLE_PERMISSIONS.get(OrgUserRole.VIEWER, [])
                
                ctx = TenantContext(
                    org_id=org_id,
                    user_id=user_id,
                    user_role=user_role or "viewer",
                    permissions=frozenset(permissions),
                    plan=TenantPlan.STARTER,
                    status=TenantStatus.ACTIVE,
                )
                request.state.tenant_context = ctx
            except Exception as e:
                logger.debug(f"Could not build full TenantContext: {e}")
            
            logger.debug(f"TENANT GUARD: Authorized - org={org_id}, user={user_id}, path={path}")
            
            # Continue to route handler
            response = await call_next(request)
            
            # Add tenant headers for debugging
            response.headers["X-Tenant-ID"] = org_id
            
            return response
            
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            logger.exception(f"TENANT GUARD ERROR: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during tenant validation"}
            )
    
    async def _extract_jwt_claims(self, request: Request) -> tuple:
        """Extract user_id, org_id, role from JWT"""
        import jwt as pyjwt
        
        token = None
        
        # Try Authorization header
        auth_header = request.headers.get("Authorization", "")
        logger.debug(f"Auth header: {auth_header[:50] if auth_header else 'NONE'}...")
        
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            logger.debug(f"Token from header: {token[:50] if token else 'NONE'}...")
        
        # Fallback to session cookie
        if not token:
            token = request.cookies.get("session_token")
            if token:
                logger.debug(f"Token from cookie: {token[:50] if token else 'NONE'}...")
        
        if not token:
            logger.debug("No token found in request")
            return None, None, None
        
        try:
            jwt_secret = self.get_jwt_secret()
            payload = pyjwt.decode(token, jwt_secret, algorithms=[self.JWT_ALGORITHM])
            logger.debug(f"JWT decoded: user_id={payload.get('user_id')}, org_id={payload.get('org_id')}")
            return payload.get("user_id"), payload.get("org_id"), payload.get("role")
        except pyjwt.ExpiredSignatureError:
            logger.warning("JWT expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except pyjwt.InvalidTokenError as e:
            logger.warning(f"JWT invalid: {e}")
            return None, None, None
    
    async def _resolve_org_id(self, request: Request, user_id: str, token_org_id: str) -> str:
        """Resolve org_id from multiple sources"""
        # Priority 1: Token (most secure)
        if token_org_id:
            return token_org_id
        
        # Priority 2: Header
        org_id = request.headers.get("X-Organization-ID")
        if org_id:
            return org_id
        
        # Priority 3: Query param
        org_id = request.query_params.get("org_id")
        if org_id:
            return org_id
        
        # Priority 4: User's default organization
        if self._db and user_id:
            membership = await self._db.organization_users.find_one({
                "user_id": user_id,
                "status": "active"
            }, {"organization_id": 1})
            
            if membership:
                return membership.get("organization_id")
        
        return None
    
    async def _validate_membership(self, user_id: str, org_id: str) -> bool:
        """CRITICAL: Validate user is member of organization"""
        if self._db is None:
            logger.error("Database not initialized in TenantGuardMiddleware")
            return False
        
        membership = await self._db.organization_users.find_one({
            "user_id": user_id,
            "organization_id": org_id,
            "status": "active"
        })
        
        return membership is not None
    
    def _is_public(self, path: str) -> bool:
        """Check if path is public"""
        if path in self.PUBLIC_ENDPOINTS:
            return True
        
        for pattern in self.PUBLIC_PATTERNS:
            if re.match(pattern, path):
                return True
        
        return False


def tenant_boundary_check(collection: str):
    """
    Decorator to enforce tenant boundary on a database operation.
    
    Usage:
        @tenant_boundary_check("tickets")
        async def get_ticket(ticket_id: str, ctx: TenantContext):
            return await db.tickets.find_one(ctx.scope_query({"ticket_id": ticket_id}))
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find tenant context in kwargs
            ctx = kwargs.get("ctx") or kwargs.get("tenant_context")
            
            if ctx is None:
                # Try to find in args (if it's a method)
                for arg in args:
                    if isinstance(arg, TenantContext):
                        ctx = arg
                        break
            
            if ctx is None:
                # Try context var
                ctx = get_tenant_context()
            
            if ctx is None:
                raise TenantContextMissing(
                    endpoint=func.__name__,
                    metadata={"collection": collection}
                )
            
            # Execute with context
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def enforce_tenant_isolation(ctx: TenantContext, query: Dict, collection: str) -> Dict:
    """
    Utility function to enforce tenant isolation on a query.
    
    Usage:
        query = enforce_tenant_isolation(ctx, {"status": "open"}, "tickets")
        # Returns: {"status": "open", "organization_id": "org_xxx"}
    """
    guard = get_tenant_guard()
    return guard.validate_query(collection, query.copy(), ctx)
