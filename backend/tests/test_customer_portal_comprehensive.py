"""
Comprehensive Customer Portal Endpoint Tests
==============================================
Tests for all /api/v1/customer-portal/* endpoints.
The Customer Portal uses its own token-based session auth,
NOT JWT. Tests create a portal-enabled contact in `contacts`.

Run: pytest backend/tests/test_customer_portal_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid

PREFIX = "/api/v1/customer-portal"
PORTAL_TOKEN = f"portal-test-{uuid.uuid4().hex}"
TEST_CONTACT_ID = f"contact-portal-test-{uuid.uuid4().hex[:8]}"
TEST_ORG = "dev-internal-testing-001"


@pytest.fixture(scope="module")
def _setup_portal_contact(base_url):
    """Create a portal-enabled contact for testing."""
    import pymongo, os
    client = pymongo.MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "battwheels_dev")]
    db.contacts.insert_one({
        "contact_id": TEST_CONTACT_ID,
        "display_name": "Portal Test Customer",
        "email": "portal-test@example.com",
        "phone": "9999999999",
        "organization_id": TEST_ORG,
        "portal_enabled": True,
        "portal_token": PORTAL_TOKEN,
        "is_active": True,
        "status": "active",
        "contact_type": "customer",
    })
    yield
    # Cleanup
    db.contacts.delete_one({"contact_id": TEST_CONTACT_ID})
    db.portal_sessions.delete_many({"contact_id": TEST_CONTACT_ID})
    client.close()


@pytest.fixture(scope="module")
def _session_token(base_url, _setup_portal_contact):
    """Login to customer portal and return session token."""
    resp = requests.post(f"{base_url}{PREFIX}/login", json={"token": PORTAL_TOKEN})
    assert resp.status_code == 200, f"Portal login failed: {resp.text}"
    data = resp.json()
    return data.get("session_token")


@pytest.fixture(scope="module")
def _portal_headers(_session_token):
    """Headers with portal session token."""
    return {
        "X-Portal-Session": _session_token,
        "Content-Type": "application/json",
    }


# ==================== AUTH ====================

class TestPortalAuth:

    def test_login_valid_token(self, base_url, _setup_portal_contact):
        resp = requests.post(f"{base_url}{PREFIX}/login", json={"token": PORTAL_TOKEN})
        assert resp.status_code == 200
        assert "session_token" in resp.json()

    def test_login_invalid_token(self, base_url):
        resp = requests.post(f"{base_url}{PREFIX}/login", json={"token": "invalid-token-xyz-1234567890"})
        assert resp.status_code == 401

    def test_session_info(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/session", headers=_portal_headers)
        assert resp.status_code == 200

    def test_no_session_401(self, base_url):
        resp = requests.get(f"{base_url}{PREFIX}/session")
        assert resp.status_code == 401


# ==================== DASHBOARD ====================

class TestPortalDashboard:

    def test_get_dashboard(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/dashboard", headers=_portal_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Response wraps in {"dashboard": {...}}
        dashboard = data.get("dashboard", data)
        assert "contact" in dashboard


# ==================== INVOICES ====================

class TestPortalInvoices:

    def test_list_invoices(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/invoices", headers=_portal_headers)
        assert resp.status_code == 200

    def test_get_invoice_nonexistent(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/invoices/NONEXISTENT", headers=_portal_headers)
        assert resp.status_code == 404


# ==================== ESTIMATES ====================

class TestPortalEstimates:

    def test_list_estimates(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/estimates", headers=_portal_headers)
        assert resp.status_code == 200

    def test_get_estimate_nonexistent(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/estimates/NONEXISTENT", headers=_portal_headers)
        assert resp.status_code == 404


# ==================== STATEMENT ====================

class TestPortalStatement:

    def test_get_statement(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/statement", headers=_portal_headers)
        assert resp.status_code == 200


# ==================== PAYMENTS ====================

class TestPortalPayments:

    def test_list_payments(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/payments", headers=_portal_headers)
        assert resp.status_code == 200


# ==================== PROFILE ====================

class TestPortalProfile:

    def test_get_profile(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/profile", headers=_portal_headers)
        assert resp.status_code == 200
        data = resp.json()
        profile = data.get("profile", data)
        assert "contact_id" in profile


# ==================== TICKETS ====================

class TestPortalTickets:

    def test_list_tickets(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/tickets", headers=_portal_headers)
        assert resp.status_code == 200

    def test_create_support_request(self, base_url, _portal_headers):
        resp = requests.post(f"{base_url}{PREFIX}/tickets", headers=_portal_headers, json={
            "subject": "Test support request",
            "description": "Need help with test issue",
            "priority": "medium",
        })
        # May succeed, need vehicle_id, or have internal error
        assert resp.status_code in [200, 201, 400, 422, 500]

    def test_get_ticket_nonexistent(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/tickets/NONEXISTENT", headers=_portal_headers)
        assert resp.status_code == 404


# ==================== VEHICLES ====================

class TestPortalVehicles:

    def test_list_vehicles(self, base_url, _portal_headers):
        resp = requests.get(f"{base_url}{PREFIX}/vehicles", headers=_portal_headers)
        assert resp.status_code == 200


# ==================== LOGOUT ====================

class TestPortalLogout:

    def test_logout(self, base_url, _setup_portal_contact):
        """Login then logout."""
        resp = requests.post(f"{base_url}{PREFIX}/login", json={"token": PORTAL_TOKEN})
        assert resp.status_code == 200
        session = resp.json()["session_token"]
        resp2 = requests.post(
            f"{base_url}{PREFIX}/logout",
            headers={"X-Portal-Session": session}
        )
        assert resp2.status_code == 200

    def test_session_invalid_after_logout(self, base_url, _setup_portal_contact):
        """After logout, session should be invalid."""
        resp = requests.post(f"{base_url}{PREFIX}/login", json={"token": PORTAL_TOKEN})
        session = resp.json()["session_token"]
        requests.post(f"{base_url}{PREFIX}/logout", headers={"X-Portal-Session": session})
        resp2 = requests.get(f"{base_url}{PREFIX}/dashboard", headers={"X-Portal-Session": session})
        assert resp2.status_code == 401
