"""
Input Sanitization Middleware — bleach-based HTML stripping

Intercepts ALL JSON request bodies. For every string field:
strips HTML tags using bleach.clean() with no allowed tags.

Handles Starlette body caching: reads body once, sanitizes,
caches the sanitized version for route handlers.
"""

import json
import logging
import bleach
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Endpoints that may legitimately contain HTML (e.g., rich-text editors)
SANITIZE_BYPASS_PREFIXES = (
    "/docs",
    "/openapi.json",
    "/redoc",
)


def _sanitize_value(value):
    """Recursively sanitize all strings in a JSON structure."""
    if isinstance(value, str):
        cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)
        return cleaned
    elif isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


class SanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Only sanitize requests with JSON bodies
        content_type = request.headers.get("content-type", "")
        path = request.url.path

        if any(path.startswith(prefix) for prefix in SANITIZE_BYPASS_PREFIXES):
            return await call_next(request)

        if "application/json" in content_type and request.method in ("POST", "PUT", "PATCH"):
            try:
                # Read the raw body once
                raw_body = await request.body()
                if raw_body:
                    data = json.loads(raw_body)
                    sanitized = _sanitize_value(data)
                    sanitized_bytes = json.dumps(sanitized).encode("utf-8")

                    # Starlette body caching fix: override BOTH the receive callable
                    # AND the cached _body so route handlers read sanitized content
                    async def receive():
                        return {"type": "http.request", "body": sanitized_bytes}

                    request._receive = receive
                    # Clear the cached body so next .body() call re-reads from _receive
                    request._body = sanitized_bytes
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not valid JSON — pass through unmodified
                pass
            except Exception as e:
                logger.warning(f"Sanitization error on {path}: {e}")

        response = await call_next(request)
        return response
