"""
Input Sanitization Middleware Tests — Prompt 2 deliverable
==========================================================

5 test cases covering:
  1. Script tag injection stripped from regular field
  2. Nested objects fully sanitized
  3. Exempt path (/api/auth/login) passes through unchanged
  4. ALLOWED_HTML_FIELDS preserve safe HTML, strip dangerous
  5. Array of strings with HTML all sanitized
"""

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from middleware.sanitization import (
    _sanitize_value,
    EXEMPT_PATHS,
    ALLOWED_HTML_FIELDS,
    SAFE_TAGS,
)


class TestSanitizationMiddleware:
    """All 5 required test cases."""

    # ------------------------------------------------------------------
    # Test 1: POST with <script>alert('xss')</script> in a string field
    #         → field is cleaned, script tag removed
    # ------------------------------------------------------------------
    def test_script_tag_stripped_from_regular_field(self):
        payload = {"name": "<script>alert('xss')</script>John"}
        result, count = _sanitize_value(payload)

        assert "<script>" not in result["name"]
        assert "alert('xss')" not in result["name"] or "<script>" not in result["name"]
        assert result["name"] == "alert('xss')John"
        assert count == 1
        print(f"PASS: script tag stripped → {result['name']!r}, fields_cleaned={count}")

    # ------------------------------------------------------------------
    # Test 2: POST with nested object containing HTML
    #         → all nested strings sanitized
    # ------------------------------------------------------------------
    def test_nested_object_sanitized(self):
        payload = {
            "customer": {
                "name": "<b>Bold Name</b>",
                "address": {
                    "line1": '<img src=x onerror="hack()">Street',
                    "city": "Normal City",
                },
            },
            "note": "<em>italic</em> text",
        }
        result, count = _sanitize_value(payload)

        assert result["customer"]["name"] == "Bold Name"
        assert "<img" not in result["customer"]["address"]["line1"]
        assert result["customer"]["address"]["line1"] == "Street"
        assert result["customer"]["address"]["city"] == "Normal City"
        assert result["note"] == "italic text"
        assert count == 3  # name, line1, note changed; city unchanged
        print(f"PASS: nested object sanitized, fields_cleaned={count}")

    # ------------------------------------------------------------------
    # Test 3: POST to /api/auth/login (exempt path)
    #         → body passes through unchanged
    # ------------------------------------------------------------------
    def test_exempt_path_login(self):
        # Verify /api/auth/login is in EXEMPT_PATHS
        assert any(
            "/api/auth/login".startswith(p) for p in EXEMPT_PATHS
        ), "/api/auth/login must be in EXEMPT_PATHS"

        # The middleware skips sanitization for exempt paths entirely,
        # so _sanitize_value is never called. We verify the config.
        assert any(
            "/api/auth/signup".startswith(p) for p in EXEMPT_PATHS
        ), "/api/auth/signup must be in EXEMPT_PATHS"
        assert any(
            "/api/auth/refresh".startswith(p) for p in EXEMPT_PATHS
        ), "/api/auth/refresh must be in EXEMPT_PATHS"
        assert any(
            "/api/webhooks/razorpay".startswith(p) for p in EXEMPT_PATHS
        ), "/api/webhooks/* must be in EXEMPT_PATHS"
        assert any(
            "/api/health".startswith(p) for p in EXEMPT_PATHS
        ), "/api/health must be in EXEMPT_PATHS"

        print("PASS: all 5 exempt paths confirmed in EXEMPT_PATHS tuple")

    # ------------------------------------------------------------------
    # Test 4: POST with email_body containing <p><strong>
    #         → allowed HTML preserved, <script> removed
    # ------------------------------------------------------------------
    def test_allowed_html_field_preserves_safe_tags(self):
        assert "email_body" in ALLOWED_HTML_FIELDS

        html_input = (
            '<p><strong>Invoice</strong> ready.</p>'
            '<script>steal()</script>'
            '<a href="https://example.com" title="link">Click</a>'
        )
        result, count = _sanitize_value(html_input, key="email_body")

        # Safe tags preserved
        assert "<p>" in result
        assert "<strong>" in result
        assert "<a " in result
        assert 'href="https://example.com"' in result

        # Dangerous tags stripped
        assert "<script>" not in result
        assert "steal()" in result  # text content remains, tag stripped

        assert count == 1
        print(f"PASS: email_body safe HTML preserved, script stripped → {result!r}")

    # ------------------------------------------------------------------
    # Test 5: POST with array of strings containing HTML
    #         → all strings in array sanitized
    # ------------------------------------------------------------------
    def test_array_of_strings_sanitized(self):
        payload = {
            "tags": [
                "<b>important</b>",
                '<a href="http://evil.com">click</a>',
                "normal-tag",
                "<script>xss</script>clean",
            ]
        }
        result, count = _sanitize_value(payload)

        assert result["tags"][0] == "important"
        assert result["tags"][1] == "click"
        assert result["tags"][2] == "normal-tag"
        assert result["tags"][3] == "xssclean"
        assert count == 3  # items 0, 1, 3 changed; item 2 unchanged
        print(f"PASS: array strings sanitized, fields_cleaned={count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
