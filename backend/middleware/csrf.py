"""
CSRF Protection Middleware — Double Submit Cookie Pattern

How it works:
1. On every response: sets a csrf_token cookie (HttpOnly=False so JS can read it)
2. On state-changing requests (POST/PUT/PATCH/DELETE):
   - Compares X-CSRF-Token header value against the csrf_token cookie value
   - If they don't match → 403
3. Bypasses:
   - Bearer token auth (API clients use JWT, not cookies — no CSRF risk)
   - Webhook endpoints (external callbacks have no cookies)
   - Public endpoints (signup, login, etc.)
"""

import secrets
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

CSRF_BYPASS_PREFIXES = (
    "/api/v1/razorpay/webhook",
    "/api/webhooks/",
    "/api/public/",
    "/api/v1/public/",
    "/docs",
    "/openapi.json",
    "/redoc",
)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()

        # Safe methods — skip validation, but set cookie on response
        if method in SAFE_METHODS:
            response = await call_next(request)
            self._ensure_csrf_cookie(request, response)
            return response

        # Bypass 1: Bearer token auth → API client, no CSRF risk
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            response = await call_next(request)
            return response

        # Bypass 2: Webhook/public endpoints
        path = request.url.path
        if any(path.startswith(prefix) for prefix in CSRF_BYPASS_PREFIXES):
            response = await call_next(request)
            return response

        # State-changing request without Bearer token → validate CSRF
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            logger.warning(f"CSRF: Missing token on {method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing", "code": "CSRF_MISSING"}
            )

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(f"CSRF: Token mismatch on {method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch", "code": "CSRF_INVALID"}
            )

        # Valid CSRF — proceed
        response = await call_next(request)
        self._ensure_csrf_cookie(request, response)
        return response

    def _ensure_csrf_cookie(self, request: Request, response: Response):
        """Set CSRF cookie if not already present."""
        existing = request.cookies.get(CSRF_COOKIE_NAME)
        if not existing:
            token = secrets.token_hex(32)
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=token,
                httponly=False,      # JS must be able to read this
                samesite="lax",
                secure=False,        # Set True in production behind HTTPS
                max_age=86400,       # 24 hours
                path="/",
            )
