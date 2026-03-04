"""
RBAC Negative Tests (Sprint 4B-02)
====================================
Verify that roles CANNOT access endpoints they should be denied.
"""
import pytest
import requests

BASE_URL = "http://localhost:8001"

OWNER_EMAIL = "dev@battwheels.internal"
OWNER_PASSWORD = "DevTest@123"
OWNER_ORG = "dev-internal-testing-001"

TECH_EMAIL = "deepak@battwheelsgarages.in"
TECH_PASSWORD = "DevTest@123"
TECH_ORG = "dev-internal-testing-001"


def server_is_running():
    try:
        return requests.get(f"{BASE_URL}/api/health", timeout=3).status_code == 200
    except Exception:
        return False


def login(email, password):
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data.get("token") or data.get("access_token")


def make_headers(token, org_id=None):
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if org_id:
        h["X-Organization-ID"] = org_id
    return h


@pytest.fixture(scope="module")
def owner_token():
    token = login(OWNER_EMAIL, OWNER_PASSWORD)
    if not token:
        pytest.skip("Owner login failed")
    return token


@pytest.fixture(scope="module")
def tech_token():
    token = login(TECH_EMAIL, TECH_PASSWORD)
    if not token:
        pytest.skip("Technician login failed")
    return token


# ==================== TECHNICIAN DENIED ENDPOINTS ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestTechnicianDenied:

    def test_technician_cannot_access_invoices(self, tech_token):
        """Technician role must be denied access to invoices-enhanced."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/invoices-enhanced",
            headers=make_headers(tech_token, TECH_ORG),
        )
        assert resp.status_code == 403, \
            f"Expected 403 for technician on invoices, got {resp.status_code}"

    def test_technician_cannot_access_accounting(self, tech_token):
        """Technician role must be denied access to journal entries."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/journal-entries",
            headers=make_headers(tech_token, TECH_ORG),
        )
        assert resp.status_code == 403, \
            f"Expected 403 for technician on journal entries, got {resp.status_code}"

    def test_technician_cannot_access_settings(self, tech_token):
        """Technician role must be denied access to settings."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/settings",
            headers=make_headers(tech_token, TECH_ORG),
        )
        assert resp.status_code == 403, \
            f"Expected 403 for technician on settings, got {resp.status_code}"

    def test_technician_cannot_access_users(self, tech_token):
        """Technician role must be denied access to user management."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/users",
            headers=make_headers(tech_token, TECH_ORG),
        )
        assert resp.status_code == 403, \
            f"Expected 403 for technician on users, got {resp.status_code}"


# ==================== TECHNICIAN ALLOWED ENDPOINT ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestTechnicianAllowed:

    def test_technician_can_access_technician_portal(self, tech_token):
        """Technician role CAN access technician portal (Sprint 4A fix)."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/technician/tickets",
            headers=make_headers(tech_token, TECH_ORG),
        )
        assert resp.status_code == 200, \
            f"Expected 200 for technician on portal, got {resp.status_code}"


# ==================== UNAUTHENTICATED ACCESS ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestUnauthenticatedAccess:

    def test_unauthenticated_cannot_access_tickets(self):
        """No Authorization header → 401."""
        resp = requests.get(f"{BASE_URL}/api/v1/tickets")
        assert resp.status_code == 401, \
            f"Expected 401 for unauthenticated tickets, got {resp.status_code}"

    def test_unauthenticated_cannot_access_invoices(self):
        """No Authorization header → 401."""
        resp = requests.get(f"{BASE_URL}/api/v1/invoices-enhanced")
        assert resp.status_code == 401, \
            f"Expected 401 for unauthenticated invoices, got {resp.status_code}"

    def test_unauthenticated_cannot_access_hr(self):
        """No Authorization header → 401."""
        resp = requests.get(f"{BASE_URL}/api/v1/hr/employees")
        assert resp.status_code == 401, \
            f"Expected 401 for unauthenticated HR, got {resp.status_code}"


# ==================== ORG SPOOFING ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestOrgSpoofing:

    def test_wrong_org_token_denied(self, owner_token):
        """Token for org_A but X-Organization-ID claiming org_B → 401 or 403."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers=make_headers(owner_token, "demo-volt-motors-001"),
        )
        # The tenant guard should reject: user is member of dev-internal-testing-001,
        # not demo-volt-motors-001
        assert resp.status_code in (401, 403), \
            f"Expected 401/403 for org spoofing, got {resp.status_code}"
