"""
Battwheels OS - Tenant Isolation Middleware
============================================

CRITICAL SECURITY COMPONENT

This middleware intercepts ALL requests and enforces tenant isolation.
It runs BEFORE any route handler executes.

Security Principles:
1. NEVER trust organization_id from request body or URL params alone
2. ALWAYS validate org_id against JWT claim
3. ALWAYS verify user membership in the organization
4. BLOCK cross-tenant data access at the middleware level
"""

import os
import re
import jwt
import logging
from typing import Optional, List, Callable
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
JWT_ALGORITHM = "HS256"

# Routes that do NOT require tenant context (public/auth routes)
PUBLIC_ROUTES: List[str] = [
    # Authentication
    r"^/api/auth/login$",
    r"^/api/auth/register$",
    r"^/api/auth/logout$",
    r"^/api/auth/google$",
    r"^/api/auth/session$",
    r"^/api/auth/me$",
    r"^/api/auth/forgot-password$",
    r"^/api/auth/reset-password$",
    
    # Health checks
    r"^/api/health$",
    r"^/api/$",
    r"^/$",
    r"^/docs$",
    r"^/openapi.json$",
    r"^/redoc$",
    
    # Public ticket tracking (customer-facing)
    r"^/api/public/tickets/.*$",
    r"^/api/public/track$",
    r"^/api/public/estimate.*$",
    r"^/api/v1/public-tickets/.*$",
    
    # Public invoice/estimate view
    r"^/api/invoices/public/.*$",
    r"^/api/estimates/public/.*$",
    r"^/api/quotes/public/.*$",
    
    # Customer portal auth
    r"^/api/customer-portal/auth.*$",
    r"^/api/business-portal/register$",
    
    # Public self-serve signup (no auth needed)
    r"^/api/organizations/signup$",
    r"^/api/organizations/register$",
    r"^/api/contact$",
    r"^/api/book-demo$",
    r"^/api/organizations/accept-invite$",
    
    # Webhook endpoints (use different auth — signature verified inside handler)
    r"^/api/webhooks/.*$",
    r"^/api/razorpay/webhook$",
    r"^/api/payments/webhook$",
    r"^/api/stripe/webhook$",
    
    # Platform admin routes (cross-tenant, use own auth check)
    r"^/api/platform/.*$",
    
    # Static files
    r"^/static/.*$",
    r"^/favicon.ico$",
]

# Compiled regex patterns for performance
_PUBLIC_PATTERNS = [re.compile(pattern) for pattern in PUBLIC_ROUTES]


def is_public_route(path: str) -> bool:
    """Check if route is in the public whitelist"""
    for pattern in _PUBLIC_PATTERNS:
        if pattern.match(path):
            return True
    return False


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces tenant isolation on ALL requests.
    
    Every non-public request must have:
    1. Valid JWT token
    2. Valid organization_id (from token or header)
    3. User must be member of the organization
    
    The middleware sets request.state.tenant_org_id and request.state.tenant_user_id
    which are used by all downstream handlers for data scoping.
    """
    
    def __init__(self, app, db=None):
        super().__init__(app)
        self.db = db
        logger.info("TenantIsolationMiddleware initialized")
    
    def set_db(self, db):
        """Set database reference (called after app startup)"""
        self.db = db
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process every request through tenant isolation.
        """
        path = request.url.path
        method = request.method
        
        # Skip OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            return await call_next(request)
        
        # Skip public routes
        if is_public_route(path):
            logger.debug(f"Public route, skipping tenant check: {path}")
            return await call_next(request)
        
        # All other routes require tenant context
        try:
            # Extract and validate JWT
            user_id, token_org_id, user_role = await self._extract_jwt_claims(request)
            
            if not user_id:
                logger.warning(f"No valid JWT for protected route: {path}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required", "code": "AUTH_REQUIRED"}
                )
            
            # Resolve organization_id
            org_id = await self._resolve_org_id(request, user_id, token_org_id)
            
            if not org_id:
                logger.warning(f"No organization context for user {user_id} on {path}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Organization context required. Use X-Organization-ID header.",
                        "code": "ORG_CONTEXT_MISSING"
                    }
                )
            
            # Validate membership (CRITICAL - prevents cross-tenant access)
            is_member = await self._validate_membership(user_id, org_id)
            
            if not is_member:
                logger.error(
                    f"SECURITY: Cross-tenant access attempt blocked. "
                    f"User {user_id} tried to access org {org_id}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Access denied. You are not a member of this organization.",
                        "code": "TENANT_ACCESS_DENIED"
                    }
                )
            
            # Set tenant context on request state for downstream use
            request.state.tenant_org_id = org_id
            request.state.tenant_user_id = user_id
            request.state.tenant_user_role = user_role or "viewer"
            
            logger.debug(f"Tenant context set: org={org_id}, user={user_id}, path={path}")
            
            # Continue to route handler
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            logger.exception(f"Tenant middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during tenant validation"}
            )
    
    async def _extract_jwt_claims(self, request: Request) -> tuple:
        """
        Extract user_id, org_id, and role from JWT token.
        Returns (user_id, org_id, role) or (None, None, None) if invalid.
        """
        token = None
        
        # Try Authorization header first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        # Fallback to session cookie
        if not token:
            token = request.cookies.get("session_token")
        
        if not token:
            return None, None, None
        
        try:
            # Decode JWT
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("user_id")
            org_id = payload.get("org_id")  # May be None if not selected
            role = payload.get("role")
            return user_id, org_id, role
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            return None, None, None
    
    async def _resolve_org_id(
        self, 
        request: Request, 
        user_id: str, 
        token_org_id: Optional[str]
    ) -> Optional[str]:
        """
        Resolve organization_id from multiple sources.
        
        Priority:
        1. org_id from JWT token (most trusted)
        2. X-Organization-ID header
        3. org_id query parameter
        4. User's default organization
        
        SECURITY: Even if org_id comes from header/param, we ALWAYS
        validate membership before allowing access.
        """
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
        if self.db and user_id:
            membership = await self.db.organization_users.find_one({
                "user_id": user_id,
                "status": "active"
            }, {"organization_id": 1})
            
            if membership:
                return membership.get("organization_id")
        
        return None
    
    async def _validate_membership(self, user_id: str, org_id: str) -> bool:
        """
        CRITICAL: Validate that user is an active member of the organization.
        This is the core security check that prevents cross-tenant access.
        """
        if not self.db:
            logger.error("Database not initialized in tenant middleware")
            return False
        
        membership = await self.db.organization_users.find_one({
            "user_id": user_id,
            "organization_id": org_id,
            "status": "active"
        })
        
        return membership is not None


# Helper functions for route handlers to use

def get_tenant_org_id(request: Request) -> str:
    """
    Get validated tenant org_id from request.
    Only call this after TenantIsolationMiddleware has processed the request.
    
    Usage:
        @router.get("/items")
        async def list_items(request: Request):
            org_id = get_tenant_org_id(request)
            items = await db.items.find({"organization_id": org_id}).to_list()
    """
    if not hasattr(request.state, "tenant_org_id"):
        raise HTTPException(
            status_code=500,
            detail="Tenant context not available. Check middleware configuration."
        )
    return request.state.tenant_org_id


def get_tenant_user_id(request: Request) -> str:
    """Get validated user_id from request"""
    if not hasattr(request.state, "tenant_user_id"):
        raise HTTPException(
            status_code=500,
            detail="User context not available. Check middleware configuration."
        )
    return request.state.tenant_user_id


def get_tenant_user_role(request: Request) -> str:
    """Get user role from request"""
    return getattr(request.state, "tenant_user_role", "viewer")


def scope_query(request: Request, base_query: dict = None) -> dict:
    """
    Create organization-scoped MongoDB query.
    
    Usage:
        @router.get("/tickets")
        async def list_tickets(request: Request):
            query = scope_query(request, {"status": "open"})
            # Returns: {"organization_id": "org_xxx", "status": "open"}
            tickets = await db.tickets.find(query).to_list()
    """
    org_id = get_tenant_org_id(request)
    query = {"organization_id": org_id}
    if base_query:
        query.update(base_query)
    return query


def scope_document(request: Request, doc: dict) -> dict:
    """
    Add organization_id to document before insert.
    
    Usage:
        @router.post("/tickets")
        async def create_ticket(request: Request, data: TicketCreate):
            doc = scope_document(request, data.dict())
            # Automatically adds organization_id
            await db.tickets.insert_one(doc)
    """
    org_id = get_tenant_org_id(request)
    doc["organization_id"] = org_id
    return doc
