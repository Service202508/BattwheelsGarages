"""
P0 Security Test: Cross-Tenant Isolation
==========================================
Verifies that an authenticated user CANNOT access another organization's data
by forging the X-Organization-ID header. The TenantGuardMiddleware must validate
the header value against the user's org membership and reject unauthorized access.
"""
import pytest
import httpx
import os

API_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://evfi-hardening.preview.emergentagent.com")

# Test credentials
DEMO_EMAIL = "demo@voltmotors.in"
DEMO_PASSWORD = "Demo@12345"

# Org IDs from the database
VOLT_MOTORS_ORG = "demo-volt-motors-001"
OTHER_ORG = "dev-internal-testing-001"  # Demo user is NOT a member


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate as demo user and return JWT token"""
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{API_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        token = data.get("token") or data.get("access_token")
        assert token, f"No token in response: {data}"
        return token


class TestCrossTenantIsolation:
    """Authenticated user cannot access another org's data by forging headers"""

    def test_forged_header_returns_403(self, auth_token):
        """
        Send GET /api/v1/tickets with X-Organization-ID set to an org
        the demo user is NOT a member of. Expect 403.
        """
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{API_URL}/api/v1/tickets",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "X-Organization-ID": OTHER_ORG,
                },
            )
            assert resp.status_code == 403, (
                f"Expected 403 for cross-tenant access, got {resp.status_code}. "
                f"Response: {resp.text[:500]}"
            )

    def test_forged_header_invoices_returns_403(self, auth_token):
        """
        Send GET /api/v1/invoices-enhanced/summary with forged org header.
        """
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{API_URL}/api/v1/invoices-enhanced/summary",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "X-Organization-ID": OTHER_ORG,
                },
            )
            assert resp.status_code == 403, (
                f"Expected 403 for cross-tenant invoice access, got {resp.status_code}. "
                f"Response: {resp.text[:500]}"
            )

    def test_forged_header_dashboard_returns_403(self, auth_token):
        """
        Financial dashboard with forged header.
        """
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{API_URL}/api/v1/dashboard/financial/summary",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "X-Organization-ID": OTHER_ORG,
                },
            )
            assert resp.status_code == 403, (
                f"Expected 403 for cross-tenant dashboard access, got {resp.status_code}. "
                f"Response: {resp.text[:500]}"
            )

    def test_forged_nonexistent_org_returns_403(self, auth_token):
        """
        Completely fabricated org_id must also be rejected.
        """
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{API_URL}/api/v1/tickets",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "X-Organization-ID": "fake-org-does-not-exist",
                },
            )
            assert resp.status_code == 403, (
                f"Expected 403 for fabricated org_id, got {resp.status_code}. "
                f"Response: {resp.text[:500]}"
            )


class TestNormalFlowPreserved:
    """Normal authenticated flow must still work correctly"""

    def test_own_org_tickets_accessible(self, auth_token):
        """
        GET /api/v1/tickets with own org header returns 200 with data.
        """
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{API_URL}/api/v1/tickets",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "X-Organization-ID": VOLT_MOTORS_ORG,
                },
            )
            assert resp.status_code == 200, (
                f"Expected 200 for own org, got {resp.status_code}. "
                f"Response: {resp.text[:500]}"
            )

    def test_no_org_header_uses_default(self, auth_token):
        """
        GET /api/v1/tickets WITHOUT any X-Organization-ID header
        should use user's default org (Volt Motors) and return data.
        """
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{API_URL}/api/v1/tickets",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                },
            )
            assert resp.status_code == 200, (
                f"Expected 200 with default org, got {resp.status_code}. "
                f"Response: {resp.text[:500]}"
            )

    def test_invoices_summary_accessible(self, auth_token):
        """Own org invoices-enhanced summary should return data"""
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{API_URL}/api/v1/invoices-enhanced/summary",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "X-Organization-ID": VOLT_MOTORS_ORG,
                },
            )
            assert resp.status_code == 200, (
                f"Expected 200 for own org invoices, got {resp.status_code}. "
                f"Response: {resp.text[:500]}"
            )
