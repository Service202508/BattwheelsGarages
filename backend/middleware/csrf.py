"""
Battwheels OS - CSRF Protection Middleware
==========================================
Double Submit Cookie pattern:
1. Backend sets a `csrf_token` cookie on every response.
2. Frontend reads the cookie and sends it back as `X-CSRF-Token` header.
3. Middleware validates header == cookie for all state-changing methods.

Because a cross-origin attacker cannot read the cookie value (SameSite + CORS),
they cannot forge the header, blocking CSRF attacks.
"""

import secrets
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
TOKEN_LENGTH = 32  # 256-bit entropy

# Methods that mutate state and therefore require CSRF validation
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths that are exempt from CSRF checks (webhooks, public forms, auth endpoints)
EXEMPT_PREFIXES = (
    "/api/auth/",
    "/api/public/",
    "/api/webhooks/",
    "/api/stripe/webhook",
    "/api/razorpay/webhook",
    "/api/health",
    "/api/contact",
    "/api/book-demo",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _generate_token() -> str:
    return secrets.token_hex(TOKEN_LENGTH)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double Submit Cookie CSRF protection.

    - Sets `csrf_token` cookie on every response (HttpOnly=False so JS can read it).
    - Validates X-CSRF-Token header matches the cookie for unsafe methods.
    """

    def __init__(self, app):
        super().__init__(app)
        logger.info("CSRFMiddleware initialized")

    def _is_exempt(self, path: str) -> bool:
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method

        # OPTIONS (CORS preflight) — always pass through
        if method == "OPTIONS":
            return await call_next(request)

        # Exempt routes skip validation entirely
        if self._is_exempt(path):
            response = await call_next(request)
            # Still issue the cookie so the frontend has a token ready
            self._ensure_csrf_cookie(request, response)
            return response

        # Bearer-token authenticated requests are inherently CSRF-safe
        # because attackers cannot forge the Authorization header cross-origin.
        # Only cookie-only sessions need double-submit cookie validation.
        auth_header = request.headers.get("authorization", "")
        has_bearer = auth_header.startswith("Bearer ") and len(auth_header) > 10

        # For unsafe methods WITHOUT bearer token, validate the double-submit
        if method in UNSAFE_METHODS and not has_bearer:
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)

            if not cookie_token or not header_token:
                logger.warning(f"CSRF: missing token on {method} {path}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing", "code": "CSRF_MISSING"},
                )

            if not secrets.compare_digest(cookie_token, header_token):
                logger.warning(f"CSRF: token mismatch on {method} {path}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token invalid", "code": "CSRF_INVALID"},
                )

        # For unsafe methods WITH bearer token, also validate CSRF if the
        # X-CSRF-Token header is provided (defense-in-depth for apiFetch users).
        # But don't block if it's missing — the bearer token itself is sufficient.
        if method in UNSAFE_METHODS and has_bearer:
            header_token = request.headers.get(CSRF_HEADER_NAME)
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            if header_token and cookie_token:
                if not secrets.compare_digest(cookie_token, header_token):
                    logger.warning(f"CSRF: token mismatch (bearer+csrf) on {method} {path}")
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF token invalid", "code": "CSRF_INVALID"},
                    )

        # Proceed with the request
        response = await call_next(request)
        self._ensure_csrf_cookie(request, response)
        return response

    @staticmethod
    def _ensure_csrf_cookie(request: Request, response: Response) -> None:
        """Set or refresh the csrf_token cookie if it is absent."""
        existing = request.cookies.get(CSRF_COOKIE_NAME)
        if not existing:
            token = _generate_token()
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=token,
                httponly=False,  # JS must read this
                secure=True,
                samesite="none",  # Required for cross-origin preview URLs
                path="/",
                max_age=60 * 60 * 24,  # 24 hours
            )
