"""
Battwheels OS - Input Sanitization Middleware
=============================================
Strips dangerous HTML/JS from all incoming JSON string fields
using `bleach`. Prevents stored XSS attacks.

Only processes application/json bodies on unsafe methods.
Does NOT alter file uploads, query params, or path params.
"""

import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    logger.warning("bleach not installed — input sanitization disabled")

# Methods whose JSON bodies should be sanitized
UNSAFE_METHODS = {"POST", "PUT", "PATCH"}

# Paths where sanitization is skipped (e.g. raw HTML template endpoints)
EXEMPT_PREFIXES = (
    "/api/auth/",
    "/api/webhooks/",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)

# bleach.clean defaults — strip ALL tags, keep no attributes
ALLOWED_TAGS: list = []
ALLOWED_ATTRIBUTES: dict = {}


def sanitize_value(value):
    """Recursively sanitize strings in a JSON-compatible structure."""
    if isinstance(value, str):
        return bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


class SanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts JSON bodies on POST/PUT/PATCH and
    strips all HTML tags from string values using bleach.
    """

    def __init__(self, app):
        super().__init__(app)
        logger.info(f"SanitizationMiddleware initialized (bleach={'ON' if BLEACH_AVAILABLE else 'OFF'})")

    def _is_exempt(self, path: str) -> bool:
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        if not BLEACH_AVAILABLE:
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Only process unsafe methods with JSON content
        if method not in UNSAFE_METHODS or self._is_exempt(path):
            return await call_next(request)

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return await call_next(request)

        # Read, sanitize, and replace the body
        try:
            raw_body = await request.body()
            if raw_body:
                data = json.loads(raw_body)
                sanitized = sanitize_value(data)
                sanitized_bytes = json.dumps(sanitized).encode("utf-8")

                # Clear Starlette's cached body and replace the receive callable
                # so downstream middleware/routes see the sanitized version
                request._body = sanitized_bytes

                async def receive():
                    return {"type": "http.request", "body": sanitized_bytes}

                request._receive = receive
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not valid JSON — let the route handle validation errors
            pass
        except Exception as e:
            logger.error(f"Sanitization error on {method} {path}: {e}")

        return await call_next(request)
