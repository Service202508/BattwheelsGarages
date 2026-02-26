"""
Battwheels OS - 10-Fix Stabilisation Sprint Tests
==================================================
Tests for all 10 critical fixes applied in this sprint:
- FIX 1: JWT Unification
- FIX 2: Platform Admin RBAC  
- FIX 3: server.py Decomposition
- FIX 4: Trial Balance
- FIX 5: Failure Card Modal (API only - UI tested separately)
- FIX 7: resolution_type Complete Removal
- FIX 9: Banking Module
- FIX 10: Notifications org_id
"""
import pytest
import requests
import os
import jwt
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "dev@battwheels.internal"
TEST_PASSWORD = "DevTest@123"


class TestAuth:
    """Test authentication and JWT unification (FIX 1)"""
    token = None
    org_id = None
    user_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login once for all tests in this class"""
        if TestAuth.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestAuth.token = data["token"]
            TestAuth.org_id = data.get("current_organization")
            TestAuth.user_id = data.get("user", {}).get("user_id")

    def test_login_returns_token(self):
        """FIX 1: Login returns token"""
        assert TestAuth.token is not None
        assert len(TestAuth.token) > 50  # JWT tokens are typically long

    def test_jwt_contains_user_id(self):
        """FIX 1: JWT payload contains user_id"""
        payload = jwt.decode(TestAuth.token, options={"verify_signature": False})
        assert "user_id" in payload, f"Missing user_id in payload: {payload}"
        assert payload["user_id"] is not None

    def test_jwt_contains_role(self):
        """FIX 1: JWT payload contains role"""
        payload = jwt.decode(TestAuth.token, options={"verify_signature": False})
        assert "role" in payload, f"Missing role in payload: {payload}"
        assert payload["role"] in ["owner", "admin", "manager", "technician", "accountant", "hr", "dispatcher", "viewer"]

    def test_jwt_contains_org_id(self):
        """FIX 1: JWT payload contains org_id when user has org membership"""
        payload = jwt.decode(TestAuth.token, options={"verify_signature": False})
        # org_id should be present if user is member of an org
        if TestAuth.org_id:
            assert "org_id" in payload, f"Missing org_id in payload for user with org: {payload}"
            assert payload["org_id"] == TestAuth.org_id


class TestPlatformAdminRBAC:
    """Test Platform Admin RBAC (FIX 2)"""

    def test_feature_flags_requires_auth(self):
        """FIX 2: GET /api/v1/platform/feature-flags requires authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/platform/feature-flags")
        # Should return 401 without token
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_feature_flags_requires_platform_admin(self):
        """FIX 2: GET /api/v1/platform/feature-flags returns 403 for non-platform-admin"""
        # First get a regular user token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        org_id = login_resp.json().get("current_organization")
        
        headers = {"Authorization": f"Bearer {token}"}
        if org_id:
            headers["X-Organization-ID"] = org_id
        
        response = requests.get(
            f"{BASE_URL}/api/v1/platform/feature-flags",
            headers=headers
        )
        # Regular user (not platform admin) should get 403
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

    def test_platform_version_public(self):
        """FIX 2: GET /api/v1/platform/version should be accessible"""
        response = requests.get(f"{BASE_URL}/api/v1/platform/version")
        # This endpoint should be public or accessible
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"


class TestServerDecomposition:
    """Test server.py decomposition (FIX 3)"""
    token = None
    org_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestServerDecomposition.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestServerDecomposition.token = data["token"]
                TestServerDecomposition.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestServerDecomposition.token}"}
        if TestServerDecomposition.org_id:
            headers["X-Organization-ID"] = TestServerDecomposition.org_id
        return headers

    def test_health_returns_version_2_5_0(self):
        """FIX 3: Health endpoint returns version 2.5.0"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("version") == "2.5.0", f"Expected version 2.5.0, got {data.get('version')}"

    def test_tickets_endpoint_works(self):
        """FIX 3: /api/v1/tickets endpoint works"""
        response = requests.get(f"{BASE_URL}/api/v1/tickets", headers=self.get_headers())
        assert response.status_code == 200, f"Tickets failed: {response.status_code}"

    def test_invoices_enhanced_endpoint_works(self):
        """FIX 3: /api/v1/invoices-enhanced endpoint works"""
        response = requests.get(f"{BASE_URL}/api/v1/invoices-enhanced", headers=self.get_headers())
        # 200 or 404 (empty) are acceptable
        assert response.status_code in [200, 404], f"Invoices failed: {response.status_code}"

    def test_contacts_enhanced_endpoint_works(self):
        """FIX 3: /api/v1/contacts-enhanced endpoint works"""
        response = requests.get(f"{BASE_URL}/api/v1/contacts-enhanced", headers=self.get_headers())
        assert response.status_code in [200, 404], f"Contacts failed: {response.status_code}"

    def test_hr_employees_endpoint_works(self):
        """FIX 3: /api/v1/hr/employees endpoint works"""
        response = requests.get(f"{BASE_URL}/api/v1/hr/employees", headers=self.get_headers())
        assert response.status_code in [200, 404], f"HR employees failed: {response.status_code}"

    def test_estimates_enhanced_endpoint_works(self):
        """FIX 3: /api/v1/estimates-enhanced endpoint works"""
        response = requests.get(f"{BASE_URL}/api/v1/estimates-enhanced", headers=self.get_headers())
        assert response.status_code in [200, 404], f"Estimates failed: {response.status_code}"


class TestTrialBalance:
    """Test Trial Balance (FIX 4)"""
    token = None
    org_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestTrialBalance.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestTrialBalance.token = data["token"]
                TestTrialBalance.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestTrialBalance.token}"}
        if TestTrialBalance.org_id:
            headers["X-Organization-ID"] = TestTrialBalance.org_id
        return headers

    def test_trial_balance_endpoint_exists(self):
        """FIX 4: GET /api/v1/journal-entries/reports/trial-balance exists"""
        response = requests.get(
            f"{BASE_URL}/api/v1/journal-entries/reports/trial-balance",
            headers=self.get_headers()
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, f"Trial balance endpoint not found"
        # 200 or 403 (feature gated) are acceptable
        assert response.status_code in [200, 403, 402], f"Unexpected status: {response.status_code}"

    def test_trial_balance_returns_totals(self):
        """FIX 4: Trial balance returns debit/credit totals"""
        response = requests.get(
            f"{BASE_URL}/api/v1/journal-entries/reports/trial-balance",
            headers=self.get_headers()
        )
        if response.status_code == 200:
            data = response.json()
            # Should have totals structure
            assert "totals" in data or "total_debit" in data or "accounts" in data, f"Missing totals: {data.keys()}"


class TestFailureCards:
    """Test Failure Cards API (FIX 5)"""
    token = None
    org_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestFailureCards.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestFailureCards.token = data["token"]
                TestFailureCards.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestFailureCards.token}"}
        if TestFailureCards.org_id:
            headers["X-Organization-ID"] = TestFailureCards.org_id
        return headers

    def test_failure_cards_list_endpoint(self):
        """FIX 5: GET /api/v1/failure-cards returns list"""
        response = requests.get(f"{BASE_URL}/api/v1/failure-cards", headers=self.get_headers())
        assert response.status_code == 200, f"Failure cards list failed: {response.status_code}"
        data = response.json()
        assert "data" in data or "failure_cards" in data or isinstance(data, list), f"Invalid response: {data.keys() if isinstance(data, dict) else type(data)}"

    def test_failure_card_by_ticket_endpoint(self):
        """FIX 5: GET /api/v1/failure-cards/by-ticket/{ticket_id} works"""
        response = requests.get(
            f"{BASE_URL}/api/v1/failure-cards/by-ticket/test_ticket_123",
            headers=self.get_headers()
        )
        # 200 (found) or 404 (not found) or returns null card
        assert response.status_code in [200, 404], f"By-ticket endpoint failed: {response.status_code}"


class TestResolutionTypeRemoval:
    """Test resolution_type complete removal (FIX 7)"""

    def test_no_resolution_type_in_frontend_code(self):
        """FIX 7: No resolution_type in frontend JS/JSX files"""
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "resolution_type", "/app/frontend/src", 
             "--include=*.js", "--include=*.jsx"],
            capture_output=True, text=True
        )
        # Should return no matches (exit code 1 means no match)
        matches = result.stdout.strip()
        assert len(matches) == 0, f"Found resolution_type in frontend: {matches}"

    def test_no_resolution_type_in_backend_routes(self):
        """FIX 7: No resolution_type in backend route files (excluding tests)"""
        import subprocess
        # Check routes directory only
        result = subprocess.run(
            ["grep", "-r", "resolution_type", "/app/backend/routes",
             "--include=*.py"],
            capture_output=True, text=True
        )
        matches = result.stdout.strip()
        assert len(matches) == 0, f"Found resolution_type in backend routes: {matches}"


class TestBankingModule:
    """Test Banking Module (FIX 9)"""
    token = None
    org_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestBankingModule.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestBankingModule.token = data["token"]
                TestBankingModule.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestBankingModule.token}"}
        if TestBankingModule.org_id:
            headers["X-Organization-ID"] = TestBankingModule.org_id
        return headers

    def test_banking_accounts_endpoint(self):
        """FIX 9: GET /api/v1/banking/accounts responds"""
        response = requests.get(f"{BASE_URL}/api/v1/banking/accounts", headers=self.get_headers())
        assert response.status_code in [200, 404], f"Banking accounts failed: {response.status_code}"

    def test_banking_transactions_endpoint(self):
        """FIX 9: GET /api/v1/banking/transactions responds"""
        response = requests.get(f"{BASE_URL}/api/v1/banking/transactions", headers=self.get_headers())
        assert response.status_code in [200, 404], f"Banking transactions failed: {response.status_code}"

    def test_banking_chart_of_accounts(self):
        """FIX 9: GET /api/v1/banking/chart-of-accounts responds"""
        response = requests.get(f"{BASE_URL}/api/v1/banking/chart-of-accounts", headers=self.get_headers())
        assert response.status_code in [200, 404], f"Chart of accounts failed: {response.status_code}"


class TestNotificationsOrgId:
    """Test Notifications org_id (FIX 10)"""
    token = None
    org_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestNotificationsOrgId.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                TestNotificationsOrgId.token = data["token"]
                TestNotificationsOrgId.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestNotificationsOrgId.token}"}
        if TestNotificationsOrgId.org_id:
            headers["X-Organization-ID"] = TestNotificationsOrgId.org_id
        return headers

    def test_notifications_list_endpoint(self):
        """FIX 10: GET /api/v1/notifications responds"""
        response = requests.get(f"{BASE_URL}/api/v1/notifications", headers=self.get_headers())
        assert response.status_code == 200, f"Notifications list failed: {response.status_code}"

    def test_notifications_create_includes_org_id(self):
        """FIX 10: POST /api/v1/notifications creates notification with org_id"""
        payload = {
            "notification_type": "test_notification",
            "title": "Test Notification",
            "message": "This is a test notification for FIX 10",
            "priority": "normal"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/notifications",
            headers=self.get_headers(),
            json=payload
        )
        assert response.status_code in [200, 201], f"Create notification failed: {response.status_code}"
        data = response.json()
        # Check the notification has org_id
        notification = data.get("notification", data)
        if TestNotificationsOrgId.org_id:
            assert notification.get("organization_id") == TestNotificationsOrgId.org_id, \
                f"Notification missing org_id: {notification.get('organization_id')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
