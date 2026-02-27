"""
Battwheels OS - Rate Limiting Middleware
=========================================

Protects against abuse and controls AI costs using slowapi.

Rate limit tiers:
- Auth endpoints: 5/min per IP (login), 3/hour per IP (register)
- AI/EFI endpoints: 20/min per org, 200/hour per org
- Standard API: 300/min per user
- Public endpoints: 60/min per IP
"""

import os
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key based on request type.
    - For authenticated requests: use user_id
    - For org-scoped requests: use org_id
    - For public requests: use IP address
    """
    # Try to get user_id from request state (set by TenantGuardMiddleware)
    user_id = getattr(request.state, "tenant_user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    # Fallback to IP
    return get_remote_address(request)


def get_org_rate_limit_key(request: Request) -> str:
    """Get rate limit key by organization (for AI endpoints)"""
    org_id = getattr(request.state, "tenant_org_id", None)
    if org_id:
        return f"org:{org_id}"
    return get_remote_address(request)


# Create limiters
limiter = Limiter(key_func=get_rate_limit_key)
org_limiter = Limiter(key_func=get_org_rate_limit_key)


# Rate limit configurations
RATE_LIMITS = {
    # Authentication - prevent brute force (relaxed in dev for test suite)
    "auth_login": "500/minute" if os.environ.get("ENVIRONMENT") == "development" else "5/minute",
    "auth_register": "100/hour" if os.environ.get("ENVIRONMENT") == "development" else "3/hour",
    "auth_password_reset": "5/hour",
    
    # AI/EFI - cost control per organization
    "ai_per_minute": "20/minute",
    "ai_per_hour": "200/hour",
    
    # Standard API - per user
    "standard": "300/minute",
    "standard_burst": "50/second",
    
    # Public endpoints - per IP
    "public": "60/minute",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies rate limiting based on route patterns.
    Works with slowapi but provides custom categorization.
    """
    
    # Route patterns and their rate limit categories
    AUTH_PATTERNS = [
        (r"^/api/auth/login$", "auth_login"),
        (r"^/api/auth/register$", "auth_register"),
        (r"^/api/auth/forgot-password$", "auth_password_reset"),
        (r"^/api/auth/reset-password$", "auth_password_reset"),
    ]
    
    AI_PATTERNS = [
        r"^/api/efi/.*$",
        r"^/api/ai/.*$",
        r"^/api/failure-intelligence/.*$",
        r"^/api/knowledge-brain/.*$",
    ]
    
    PUBLIC_PATTERNS = [
        r"^/api/public/.*$",
        r"^/api/webhooks/.*$",
        r"^/api/payments/webhook$",
        r"^/api/organizations/signup$",
        r"^/api/organizations/register$",
        r"^/api/contact$",
        r"^/api/book-demo$",
    ]
    
    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_url = redis_url
        # In-memory rate limit tracking (use Redis in production)
        self._request_counts = {}
        logger.info("RateLimitMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Skip OPTIONS
        if method == "OPTIONS":
            return await call_next(request)
        
        # Skip health checks
        if path in ["/api/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Determine rate limit category
        category = self._get_category(path)
        
        if category:
            # Check rate limit
            is_allowed, retry_after = await self._check_rate_limit(request, category)
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded: {path} - category: {category}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "retry_after": retry_after,
                        "message": "Too many requests. Please wait before retrying."
                    },
                    headers={"Retry-After": str(retry_after)}
                )
        
        return await call_next(request)
    
    def _get_category(self, path: str) -> str:
        """Determine rate limit category for a path"""
        # Check auth patterns
        for pattern, category in self.AUTH_PATTERNS:
            if re.match(pattern, path):
                return category
        
        # Check AI patterns
        for pattern in self.AI_PATTERNS:
            if re.match(pattern, path):
                return "ai"
        
        # Check public patterns
        for pattern in self.PUBLIC_PATTERNS:
            if re.match(pattern, path):
                return "public"
        
        # Default to standard
        return "standard"
    
    async def _check_rate_limit(self, request: Request, category: str) -> tuple:
        """
        Check if request is within rate limits.
        Returns (is_allowed, retry_after_seconds)
        
        Note: This is a simple in-memory implementation.
        For production, use Redis with slowapi.
        """
        import time
        
        # Get appropriate key
        if category in ["auth_login", "auth_register", "auth_password_reset", "public"]:
            key = get_remote_address(request)
        elif category == "ai":
            key = get_org_rate_limit_key(request)
        else:
            key = get_rate_limit_key(request)
        
        # Get limits
        if category == "ai":
            max_per_minute = 20
            window = 60
        elif category == "auth_login":
            max_per_minute = 10
            window = 60
        elif category == "auth_register":
            max_per_minute = 3
            window = 3600  # per hour
        elif category == "public":
            max_per_minute = 60
            window = 60
        else:
            max_per_minute = 300
            window = 60
        
        # Simple rate limiting with sliding window
        now = time.time()
        cache_key = f"{category}:{key}"
        
        if cache_key not in self._request_counts:
            self._request_counts[cache_key] = []
        
        # Clean old entries
        self._request_counts[cache_key] = [
            t for t in self._request_counts[cache_key]
            if now - t < window
        ]
        
        # Check limit
        if len(self._request_counts[cache_key]) >= max_per_minute:
            # Calculate retry_after
            oldest = min(self._request_counts[cache_key])
            retry_after = int(window - (now - oldest)) + 1
            return False, retry_after
        
        # Record this request
        self._request_counts[cache_key].append(now)
        return True, 0


def setup_rate_limiting(app):
    """
    Setup rate limiting on FastAPI app.
    Call this during app startup.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(RateLimitMiddleware)
    logger.info("Rate limiting configured")


# Decorators for route-level rate limiting (for specific endpoints)
def rate_limit_auth_login():
    """Rate limit decorator for login endpoint"""
    return limiter.limit(RATE_LIMITS["auth_login"])


def rate_limit_auth_register():
    """Rate limit decorator for register endpoint"""
    return limiter.limit(RATE_LIMITS["auth_register"])


def rate_limit_ai():
    """Rate limit decorator for AI endpoints"""
    return org_limiter.limit(RATE_LIMITS["ai_per_minute"])


def rate_limit_standard():
    """Rate limit decorator for standard endpoints"""
    return limiter.limit(RATE_LIMITS["standard"])
