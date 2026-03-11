"""
Input Sanitization Middleware — bleach-based HTML stripping
===========================================================

Intercepts ALL incoming POST/PUT/PATCH requests with JSON bodies.
Recursively sanitizes every string field using bleach.clean().

Two sanitization modes:
  1. STRICT (default): strip ALL HTML tags  (ALLOWED_TAGS = [])
  2. SAFE:  preserve a safe subset of HTML  (for rich-text fields)

Exempt paths skip sanitization entirely.
Allowed-HTML fields get the SAFE mode instead of STRICT.

Starlette body caching: after sanitizing, the body is re-cached
so downstream route handlers read the sanitized version.
"""

import json
import logging
from typing import Any

import bleach
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Paths completely exempt from sanitization (prefix match).
EXEMPT_PATHS = (
    "/api/auth/login",
    "/api/auth/signup",
    "/api/auth/refresh",
    "/api/webhooks/",
    "/api/v1/webhooks/",
    "/api/health",
    "/api/public/",
    "/api/v1/public/",
    "/api/customer-portal/",
    "/api/v1/customer-portal/",
    "/api/business-portal/",
    "/api/v1/business-portal/",
    # Framework docs / schema endpoints
    "/docs",
    "/openapi.json",
    "/redoc",
)

# Fields whose values must NEVER be touched (passwords, tokens, secrets).
SKIP_FIELDS = frozenset({
    "password", "new_password", "current_password", "old_password",
    "password_hash", "confirm_password", "temporary_password",
    "token", "refresh_token", "secret", "api_key",
})

# Fields that legitimately contain rich-text HTML.
# These get the SAFE tag-set instead of full stripping.
ALLOWED_HTML_FIELDS = frozenset({
    "email_body",
    "html_content",
    "template_html",
    "description",
})

# Tags / attributes allowed inside ALLOWED_HTML_FIELDS.
SAFE_TAGS = [
    "p", "br", "strong", "em", "ul", "ol", "li", "a",
    "h1", "h2", "h3", "h4", "span", "div",
]
SAFE_ATTRS = {
    "a": ["href", "title"],
    "span": ["class"],
    "div": ["class"],
}

# ---------------------------------------------------------------------------
# Recursive sanitizer
# ---------------------------------------------------------------------------

def _sanitize_value(value: Any, key: str | None = None) -> Any:
    """Recursively sanitize every string in a JSON-compatible structure.

    Returns the sanitized structure and the number of fields that were cleaned.
    """
    if key and key.lower() in SKIP_FIELDS:
        return value, 0

    if isinstance(value, str):
        if key and key.lower() in ALLOWED_HTML_FIELDS:
            cleaned = bleach.clean(
                value, tags=SAFE_TAGS, attributes=SAFE_ATTRS, strip=True,
            )
        else:
            cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)
        changed = 1 if cleaned != value else 0
        return cleaned, changed

    if isinstance(value, dict):
        total = 0
        out = {}
        for k, v in value.items():
            sanitized, count = _sanitize_value(v, key=k)
            out[k] = sanitized
            total += count
        return out, total

    if isinstance(value, list):
        total = 0
        out = []
        for item in value:
            sanitized, count = _sanitize_value(item)
            out.append(sanitized)
            total += count
        return out, total

    return value, 0

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class SanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Exempt paths — pass through untouched
        if any(path.startswith(prefix) for prefix in EXEMPT_PATHS):
            return await call_next(request)

        content_type = request.headers.get("content-type", "")

        if (
            request.method in ("POST", "PUT", "PATCH")
            and "application/json" in content_type
        ):
            try:
                raw_body = await request.body()
                if raw_body:
                    data = json.loads(raw_body)
                    sanitized, fields_cleaned = _sanitize_value(data)
                    sanitized_bytes = json.dumps(sanitized).encode("utf-8")

                    if fields_cleaned:
                        logger.debug(
                            "Sanitized %d field(s) on %s %s",
                            fields_cleaned, request.method, path,
                        )

                    # Starlette body-caching fix: override receive + cached body
                    async def receive():
                        return {"type": "http.request", "body": sanitized_bytes}

                    request._receive = receive
                    request._body = sanitized_bytes

            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            except Exception as e:
                logger.warning("Sanitization error on %s: %s", path, e)

        return await call_next(request)
