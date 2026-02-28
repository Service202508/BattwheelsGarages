"""
P1 Mobile Responsive Technician Flows - Backend Tests
======================================================
Tests:
  - GET /api/platform/audit-status (platform admin endpoint)
  - GET /api/organizations/me/members (was crashing with KeyError: membership_id)
  - POST /api/auth/login for both org_admin and platform_admin
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Credentials
ORG_ADMIN_EMAIL = "admin@battwheels.in"
ORG_ADMIN_PASS = "admin"
ORG_ID = "dev-internal-testing-001"
PLATFORM_ADMIN_EMAIL = "platform-admin@battwheels.in"
PLATFORM_ADMIN_PASS = "admin"


@pytest.fixture(scope="module")
def org_admin_token():
    """Login as org admin and return token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASS
    })
    assert res.status_code == 200, f"Org admin login failed: {res.status_code} - {res.text}"
    data = res.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture(scope="module")
def platform_admin_token():
    """Login as platform admin and return token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": PLATFORM_ADMIN_EMAIL,
        "password": PLATFORM_ADMIN_PASS
    })
    assert res.status_code == 200, f"Platform admin login failed: {res.status_code} - {res.text}"
    data = res.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"No token in response: {data}"
    return token


class TestAuthLogin:
    """Test login endpoints for both user types"""

    def test_org_admin_login(self):
        """Test org admin login returns 200 and token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASS
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        token = data.get("token") or data.get("access_token")
        assert token, "No token returned"
        print(f"PASS: Org admin login succeeded, token: {token[:20]}...")

    def test_platform_admin_login(self):
        """Test platform admin login returns 200 and token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASS
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        token = data.get("token") or data.get("access_token")
        assert token, "No token returned"
        print(f"PASS: Platform admin login succeeded")


class TestPlatformAuditStatus:
    """Test GET /api/platform/audit-status endpoint"""

    def test_audit_status_returns_200(self, platform_admin_token):
        """Verify audit-status returns 200 for platform admin"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        res = requests.get(f"{BASE_URL}/api/platform/audit-status", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print(f"PASS: GET /api/platform/audit-status returned 200")

    def test_audit_status_returns_valid_json(self, platform_admin_token):
        """Verify audit-status returns valid JSON (empty or with timestamp)"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        res = requests.get(f"{BASE_URL}/api/platform/audit-status", headers=headers)
        assert res.status_code == 200
        data = res.json()
        # Can be empty dict or audit result
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        if data:
            # If data exists, validate fields
            if "timestamp" in data:
                assert "passed" in data or "total" in data, f"Missing passed/total in audit data: {data}"
                print(f"PASS: Audit status has data: {data.get('passed')}/{data.get('total')} at {data.get('timestamp')}")
            else:
                print(f"PASS: Audit status returned (no timestamp yet): {list(data.keys())}")
        else:
            print("PASS: Audit status returned empty dict (no audit run yet)")

    def test_audit_status_denied_without_auth(self):
        """Verify audit-status returns 401/403 without auth"""
        res = requests.get(f"{BASE_URL}/api/platform/audit-status")
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"PASS: Unauthenticated request denied with {res.status_code}")

    def test_audit_status_denied_for_org_admin(self, org_admin_token):
        """Verify audit-status returns 403 for non-platform admin"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        res = requests.get(f"{BASE_URL}/api/platform/audit-status", headers=headers)
        assert res.status_code == 403, f"Expected 403 for non-platform-admin, got {res.status_code}: {res.text}"
        print(f"PASS: Org admin properly denied access to audit-status with 403")


class TestOrganizationMembers:
    """Test GET /api/organizations/me/members - was crashing with KeyError: membership_id"""

    def test_members_returns_200(self, org_admin_token):
        """Verify members endpoint returns 200"""
        headers = {"Authorization": f"Bearer {org_admin_token}", "X-Organization-Id": ORG_ID}
        res = requests.get(f"{BASE_URL}/api/organizations/me/members", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print(f"PASS: GET /api/organizations/me/members returned 200")

    def test_members_returns_valid_structure(self, org_admin_token):
        """Verify members endpoint returns members list"""
        headers = {"Authorization": f"Bearer {org_admin_token}", "X-Organization-Id": ORG_ID}
        res = requests.get(f"{BASE_URL}/api/organizations/me/members", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "members" in data, f"Missing 'members' key in response: {data}"
        assert "total" in data, f"Missing 'total' key in response: {data}"
        assert isinstance(data["members"], list), f"Expected list, got {type(data['members'])}"
        print(f"PASS: members endpoint returned {data['total']} members")

    def test_members_have_membership_id(self, org_admin_token):
        """Verify no KeyError on membership_id - each member should have membership_id"""
        headers = {"Authorization": f"Bearer {org_admin_token}", "X-Organization-Id": ORG_ID}
        res = requests.get(f"{BASE_URL}/api/organizations/me/members", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        members = data.get("members", [])
        assert len(members) > 0, "Expected at least one member in Battwheels org"
        
        # Verify each member has membership_id (fix was m.get("membership_id", m.get("_id", "")))
        for member in members:
            assert "membership_id" in member, f"Member missing membership_id: {member}"
            assert member["membership_id"] != "", f"Member has empty membership_id: {member}"
            assert "email" in member, f"Member missing email: {member}"
            assert "role" in member, f"Member missing role: {member}"
        
        print(f"PASS: All {len(members)} members have membership_id field")

    def test_members_no_500_crash(self, org_admin_token):
        """Specifically verify no 500 crash on members (KeyError: membership_id fix)"""
        headers = {"Authorization": f"Bearer {org_admin_token}", "X-Organization-Id": ORG_ID}
        res = requests.get(f"{BASE_URL}/api/organizations/me/members", headers=headers)
        assert res.status_code != 500, f"Server crashed with 500: {res.text}"
        assert res.status_code == 200, f"Unexpected status: {res.status_code}: {res.text}"
        print(f"PASS: No 500 crash on members endpoint - KeyError fix confirmed")


class TestPlatformMetrics:
    """Test GET /api/platform/metrics endpoint"""

    def test_metrics_returns_200(self, platform_admin_token):
        """Verify metrics endpoint returns 200"""
        headers = {"Authorization": f"Bearer {platform_admin_token}"}
        res = requests.get(f"{BASE_URL}/api/platform/metrics", headers=headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "total_organizations" in data, f"Missing total_organizations: {data}"
        print(f"PASS: Platform metrics returned {data['total_organizations']} orgs")
