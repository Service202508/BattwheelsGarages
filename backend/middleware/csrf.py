"""
CSRF Protection Middleware — Double Submit Cookie Pattern

How it works:
1. On every response without a CSRF cookie: sets a `csrftoken` cookie
   (HttpOnly=False so JavaScript can read it).
2. On state-changing requests (POST / PUT / DELETE / PATCH):
   - Compares X-CSRF-Token header against the csrftoken cookie.
   - Mismatch or missing → 403.
3. Bypasses:
   - Requests carrying a valid Bearer token (API / JWT clients have no
     CSRF risk because browsers never attach Authorization automatically).
   - Explicitly exempted paths (auth, webhooks, health).
"""

import secrets
import logging
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

_IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development") == "production"

CSRF_EXEMPT_PATHS = (
    "/health",
    "/api/health",
    "/api/v1/health",
    "/api/organizations/signup",
    "/api/organizations/register",
    "/api/v1/organizations/signup",
    "/api/v1/organizations/register",
    "/api/book-demo",
    "/api/v1/book-demo",
    "/api/contact",
    "/api/v1/contact",
    "/api/contact-form",
    "/api/v1/contact-form",
    "/api/demo-request",
    "/api/v1/demo-request",
    "/api/v1/payments/webhook",
    "/api/v1/payments/razorpay/webhook",
)

CSRF_EXEMPT_PREFIXES = (
    "/api/auth/",
    "/api/v1/auth/",
    "/api/webhooks/",
    "/api/v1/webhooks/",
    "/api/public/",
    "/api/v1/public/",
    "/api/customer-portal/",
    "/api/v1/customer-portal/",
    "/api/business-portal/",
    "/api/v1/business-portal/",
    "/api/technician-portal/",
    "/api/v1/technician-portal/",
    "/api/estimates-enhanced/public/",
    "/api/v1/estimates-enhanced/public/",
    "/api/invoices-enhanced/public/",
    "/api/v1/invoices-enhanced/public/",
    "/api/master-data/",
    "/api/v1/master-data/",
    "/api/public-tickets/",
    "/api/v1/public-tickets/",
)

CSRF_COOKIE = "csrftoken"
CSRF_HEADER = "x-csrf-token"


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()

        # Safe methods — skip validation, ensure cookie is set
        if method in SAFE_METHODS:
            response = await call_next(request)
            _ensure_csrf_cookie(request, response)
            return response

        # Bypass: Bearer-token auth (JWT clients, no CSRF risk)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            response = await call_next(request)
            return response

        # Bypass: explicitly exempt paths
        path = request.url.path
        if path in CSRF_EXEMPT_PATHS or any(path.startswith(p) for p in CSRF_EXEMPT_PREFIXES):
            response = await call_next(request)
            return response

        # --- State-changing request without Bearer → validate CSRF ---
        cookie_token = request.cookies.get(CSRF_COOKIE)
        header_token = request.headers.get(CSRF_HEADER)

        if not cookie_token or not header_token:
            logger.warning("CSRF token missing on %s %s", method, path)
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing. Include X-CSRF-Token header matching the csrftoken cookie."},
            )

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning("CSRF token mismatch on %s %s", method, path)
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch. The X-CSRF-Token header does not match the csrftoken cookie."},
            )

        # Valid — proceed
        response = await call_next(request)
        _ensure_csrf_cookie(request, response)
        return response


def _ensure_csrf_cookie(request: Request, response: Response):
    """Set the CSRF cookie if the client doesn't already have one."""
    if not request.cookies.get(CSRF_COOKIE):
        token = secrets.token_hex(32)
        response.set_cookie(
            key=CSRF_COOKIE,
            value=token,
            httponly=False,
            secure=_IS_PRODUCTION,
            samesite="lax",
            path="/",
        )
