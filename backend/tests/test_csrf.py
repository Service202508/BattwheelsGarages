"""
Test suite for CSRF Double Submit Cookie middleware.

4 test cases:
  1. POST without CSRF token → 403
  2. POST with valid CSRF token → success (not CSRF-403)
  3. POST with Bearer auth (no CSRF) → success (bypass)
  4. POST to /api/webhooks/ (no CSRF) → success (exempt path)
"""

import requests


def test_post_without_csrf_returns_403(base_url):
    """POST without CSRF token or Bearer auth must be rejected with 403."""
    resp = requests.post(
        f"{base_url}/api/v1/invoices",
        json={"dummy": True},
        # No Authorization header, no CSRF cookie/header
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "CSRF" in body.get("detail", ""), f"Expected CSRF error, got: {body}"


def test_post_with_valid_csrf_succeeds(base_url):
    """POST with matching cookie + header must pass the CSRF gate."""
    session = requests.Session()

    # Step 1: GET to obtain the CSRF cookie
    get_resp = session.get(f"{base_url}/api/health")
    assert get_resp.status_code == 200
    csrf_token = session.cookies.get("csrftoken")
    assert csrf_token, f"Expected csrftoken cookie, got: {dict(session.cookies)}"

    # Step 2: POST with the CSRF token in both cookie (auto via session) and header
    post_resp = session.post(
        f"{base_url}/api/v1/invoices",
        json={"dummy": True},
        headers={"X-CSRF-Token": csrf_token},
    )
    # Must NOT be a CSRF-specific 403. Could be 401 (no auth) or 422, etc.
    if post_resp.status_code == 403:
        body = post_resp.json()
        assert "CSRF" not in body.get("detail", ""), (
            f"CSRF should have passed but got CSRF 403: {body}"
        )


def test_post_with_bearer_bypasses_csrf(base_url, demo_token):
    """POST with Bearer token should bypass CSRF validation entirely."""
    resp = requests.post(
        f"{base_url}/api/v1/invoices",
        json={"dummy": True},
        headers={"Authorization": f"Bearer {demo_token}"},
        # No CSRF cookie or header
    )
    # Should NOT be a CSRF-specific 403
    if resp.status_code == 403:
        body = resp.json()
        assert "CSRF" not in body.get("detail", ""), (
            f"Bearer request should bypass CSRF, got: {body}"
        )


def test_post_to_webhooks_bypasses_csrf(base_url):
    """POST to /api/webhooks/* should bypass CSRF validation."""
    resp = requests.post(
        f"{base_url}/api/webhooks/razorpay",
        json={"event": "payment.captured"},
        # No CSRF, no Bearer
    )
    # Should NOT be a CSRF-specific 403. Could be 404/422 but not CSRF.
    if resp.status_code == 403:
        body = resp.json()
        assert "CSRF" not in body.get("detail", ""), (
            f"Webhook request should bypass CSRF, got: {body}"
        )
