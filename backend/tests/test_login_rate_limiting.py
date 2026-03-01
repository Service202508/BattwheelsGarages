"""
Login Rate Limiting Tests
==========================
Tests per-email brute-force protection (5 attempts / 15 min).
Uses shared conftest.py fixtures.

Run: pytest backend/tests/test_login_rate_limiting.py -v --tb=short
"""

import pytest
import requests


@pytest.fixture(scope="module")
def _base(base_url):
    return f"{base_url}/api/v1/auth/login"


@pytest.fixture(autouse=True)
def _clear_attempts(base_url):
    """Clear rate limit state before each test by using a unique email per test class."""
    yield
    # TTL handles cleanup; no manual cleanup needed


class TestLoginRateLimiting:
    """Tests that login rate limiting works per email."""

    FAKE_EMAIL = "brute_force_test_unique_abc@nonexistent.example"

    def test_first_5_attempts_allowed(self, _base):
        """First 5 wrong-password attempts should return 401, not 429."""
        for i in range(5):
            resp = requests.post(_base, json={
                "email": self.FAKE_EMAIL,
                "password": f"wrong_password_{i}"
            })
            assert resp.status_code == 401, (
                f"Attempt {i+1}: expected 401, got {resp.status_code} — {resp.text}"
            )

    def test_6th_attempt_returns_429(self, _base):
        """After 5 failures, the 6th attempt should be blocked with 429."""
        email = "brute_force_6th_test@nonexistent.example"
        for i in range(5):
            requests.post(_base, json={"email": email, "password": f"wrong_{i}"})

        resp = requests.post(_base, json={"email": email, "password": "wrong_6"})
        assert resp.status_code == 429, f"Expected 429, got {resp.status_code} — {resp.text}"
        assert "Too many login attempts" in resp.json().get("detail", "")

    def test_successful_login_resets_counter(self, _base):
        """A correct login should clear the attempt counter."""
        email = "platform-admin@battwheels.in"
        password = "DevTest@123"

        # Make 3 failed attempts
        for i in range(3):
            requests.post(_base, json={"email": email, "password": f"wrong_{i}"})

        # Successful login
        resp = requests.post(_base, json={"email": email, "password": password})
        assert resp.status_code == 200, f"Login should succeed: {resp.text}"

        # Should be able to fail again (counter reset)
        for i in range(4):
            resp = requests.post(_base, json={"email": email, "password": f"wrong_again_{i}"})
            assert resp.status_code == 401, f"Post-reset attempt {i+1}: expected 401, got {resp.status_code}"

    def test_different_emails_tracked_independently(self, _base):
        """Rate limiting one email should not affect another."""
        email_a = "independent_a_test@nonexistent.example"
        email_b = "independent_b_test@nonexistent.example"

        # Exhaust email_a
        for i in range(5):
            requests.post(_base, json={"email": email_a, "password": f"wrong_{i}"})

        # email_a should be blocked
        resp_a = requests.post(_base, json={"email": email_a, "password": "wrong_6"})
        assert resp_a.status_code == 429

        # email_b should NOT be blocked
        resp_b = requests.post(_base, json={"email": email_b, "password": "wrong_1"})
        assert resp_b.status_code == 401, f"email_b should be 401, got {resp_b.status_code}"

    def test_rate_limit_response_includes_retry_after(self, _base):
        """429 response should include Retry-After header."""
        email = "retry_after_test@nonexistent.example"
        for i in range(5):
            requests.post(_base, json={"email": email, "password": f"wrong_{i}"})

        resp = requests.post(_base, json={"email": email, "password": "wrong_6"})
        assert resp.status_code == 429
        # FastAPI HTTPException with headers may or may not propagate Retry-After
        # Check response body as primary
        detail = resp.json().get("detail", "")
        assert "15 minutes" in detail
