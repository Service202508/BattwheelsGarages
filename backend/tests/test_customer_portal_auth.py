"""
Customer Portal Authentication Tests
=====================================
Tests for customer portal authentication that accepts tokens from both:
1. X-Portal-Session header
2. session_token query parameter

Endpoints tested:
- POST /api/customer-portal/login - Login with portal token
- GET /api/customer-portal/dashboard - Dashboard with session token
- GET /api/customer-portal/invoices - Invoices list
- GET /api/customer-portal/estimates - Estimates list  
- GET /api/customer-portal/profile - Customer profile
- GET /api/customer-portal/statement - Account statement
- POST /api/contacts-enhanced/{contact_id}/enable-portal - Enable portal for contact
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "DevTest@123"
TEST_CONTACT_ID = "1837096000000463081"

# Helper function to get a fresh portal token
def get_fresh_portal_token():
    """Enable portal for the contact and get a fresh token"""
    # Login as admin first
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if login_resp.status_code != 200:
        return None
    
    admin_token = login_resp.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Enable portal for contact
    enable_resp = requests.post(
        f"{BASE_URL}/api/contacts-enhanced/{TEST_CONTACT_ID}/enable-portal",
        headers=admin_headers
    )
    if enable_resp.status_code == 200:
        return enable_resp.json().get("token")
    return None


class TestPortalLogin:
    """Test customer portal login with portal token"""
    
    def test_portal_login_success(self):
        """Test successful portal login with valid token"""
        # Get a fresh portal token
        portal_token = get_fresh_portal_token()
        if not portal_token:
            pytest.skip("Could not get portal token - admin login or enable-portal failed")
        
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": portal_token
        })
        
        print(f"Portal login response status: {response.status_code}")
        print(f"Portal login response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Portal login failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "session_token" in data, "session_token not returned"
        assert "contact" in data, "contact not returned"
        assert data["session_token"].startswith("PS-"), f"Session token should start with PS-, got {data['session_token'][:10]}"
        
        print(f"SUCCESS: Portal login - session_token: {data['session_token'][:20]}...")
    
    def test_portal_login_invalid_token(self):
        """Test portal login with invalid token"""
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": "invalid-token-12345678"
        })
        
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("SUCCESS: Invalid portal token correctly rejected")
    
    def test_portal_login_short_token(self):
        """Test portal login with token that's too short"""
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": "short"
        })
        
        assert response.status_code in [401, 422], f"Expected 401/422 for short token, got {response.status_code}"
        print("SUCCESS: Short token correctly rejected")


class TestPortalSessionTokenMethods:
    """Test that session tokens can be passed via header or query parameter"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get a valid session token for testing"""
        # Get a fresh portal token
        portal_token = get_fresh_portal_token()
        if not portal_token:
            pytest.skip("Could not get portal token - admin login or enable-portal failed")
        
        # Login to portal
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": portal_token
        })
        
        if response.status_code == 200:
            self.session_token = response.json()["session_token"]
            self.contact_id = response.json()["contact"]["contact_id"]
        else:
            pytest.skip("Could not get a valid portal session token")
    
    def test_dashboard_with_header(self):
        """Test dashboard access with X-Portal-Session header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/dashboard",
            headers={"X-Portal-Session": self.session_token}
        )
        
        print(f"Dashboard (header) status: {response.status_code}")
        assert response.status_code == 200, f"Dashboard with header failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "dashboard" in data, "dashboard not in response"
        print(f"SUCCESS: Dashboard via header - receivable: {data['dashboard'].get('summary', {}).get('total_receivable', 'N/A')}")
    
    def test_dashboard_with_query_param(self):
        """Test dashboard access with session_token query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/dashboard?session_token={self.session_token}"
        )
        
        print(f"Dashboard (query) status: {response.status_code}")
        assert response.status_code == 200, f"Dashboard with query param failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "dashboard" in data, "dashboard not in response"
        print(f"SUCCESS: Dashboard via query param - outstanding: {data['dashboard'].get('summary', {}).get('total_outstanding', 'N/A')}")
    
    def test_invoices_with_header(self):
        """Test invoices access with X-Portal-Session header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/invoices",
            headers={"X-Portal-Session": self.session_token}
        )
        
        print(f"Invoices (header) status: {response.status_code}")
        assert response.status_code == 200, f"Invoices with header failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "invoices" in data, "invoices not in response"
        print(f"SUCCESS: Invoices via header - count: {len(data.get('invoices', []))}")
    
    def test_invoices_with_query_param(self):
        """Test invoices access with session_token query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/invoices?session_token={self.session_token}"
        )
        
        print(f"Invoices (query) status: {response.status_code}")
        assert response.status_code == 200, f"Invoices with query param failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "invoices" in data, "invoices not in response"
        print(f"SUCCESS: Invoices via query param - count: {len(data.get('invoices', []))}")
    
    def test_estimates_with_header(self):
        """Test estimates access with X-Portal-Session header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/estimates",
            headers={"X-Portal-Session": self.session_token}
        )
        
        print(f"Estimates (header) status: {response.status_code}")
        assert response.status_code == 200, f"Estimates with header failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "estimates" in data, "estimates not in response"
        print(f"SUCCESS: Estimates via header - count: {len(data.get('estimates', []))}")
    
    def test_estimates_with_query_param(self):
        """Test estimates access with session_token query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/estimates?session_token={self.session_token}"
        )
        
        print(f"Estimates (query) status: {response.status_code}")
        assert response.status_code == 200, f"Estimates with query param failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "estimates" in data, "estimates not in response"
        print(f"SUCCESS: Estimates via query param - count: {len(data.get('estimates', []))}")
    
    def test_profile_with_header(self):
        """Test profile access with X-Portal-Session header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/profile",
            headers={"X-Portal-Session": self.session_token}
        )
        
        print(f"Profile (header) status: {response.status_code}")
        assert response.status_code == 200, f"Profile with header failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "profile" in data, "profile not in response"
        print(f"SUCCESS: Profile via header - name: {data['profile'].get('name', 'N/A')}")
    
    def test_profile_with_query_param(self):
        """Test profile access with session_token query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/profile?session_token={self.session_token}"
        )
        
        print(f"Profile (query) status: {response.status_code}")
        assert response.status_code == 200, f"Profile with query param failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "profile" in data, "profile not in response"
        print(f"SUCCESS: Profile via query param - email: {data['profile'].get('email', 'N/A')}")
    
    def test_statement_with_header(self):
        """Test statement access with X-Portal-Session header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/statement",
            headers={"X-Portal-Session": self.session_token}
        )
        
        print(f"Statement (header) status: {response.status_code}")
        assert response.status_code == 200, f"Statement with header failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "statement" in data, "statement not in response"
        print(f"SUCCESS: Statement via header - balance: {data['statement'].get('summary', {}).get('balance_due', 'N/A')}")
    
    def test_statement_with_query_param(self):
        """Test statement access with session_token query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/statement?session_token={self.session_token}"
        )
        
        print(f"Statement (query) status: {response.status_code}")
        assert response.status_code == 200, f"Statement with query param failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "statement" in data, "statement not in response"
        print(f"SUCCESS: Statement via query param - invoices: {len(data['statement'].get('invoices', []))}")


class TestPortalSessionValidation:
    """Test session token validation edge cases"""
    
    def test_missing_session_token(self):
        """Test endpoint fails with missing session token"""
        response = requests.get(f"{BASE_URL}/api/customer-portal/dashboard")
        
        assert response.status_code == 401, f"Expected 401 for missing token, got {response.status_code}"
        print("SUCCESS: Missing session token correctly rejected")
    
    def test_invalid_session_token_header(self):
        """Test endpoint fails with invalid session token in header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/dashboard",
            headers={"X-Portal-Session": "invalid-session-token"}
        )
        
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("SUCCESS: Invalid session token in header correctly rejected")
    
    def test_invalid_session_token_query(self):
        """Test endpoint fails with invalid session token in query"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/dashboard?session_token=invalid-session-token"
        )
        
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("SUCCESS: Invalid session token in query correctly rejected")


class TestEnablePortalEndpoint:
    """Test enable-portal endpoint for contacts"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        
        self.admin_token = response.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_enable_portal_for_contact(self):
        """Test enabling portal for a contact"""
        response = requests.post(
            f"{BASE_URL}/api/contacts-enhanced/{TEST_CONTACT_ID}/enable-portal",
            headers=self.admin_headers
        )
        
        print(f"Enable portal status: {response.status_code}")
        print(f"Enable portal response: {response.text[:500]}")
        
        if response.status_code == 404:
            print("INFO: Contact not found - may need different contact ID")
            pytest.skip("Test contact not found")
        
        if response.status_code == 400:
            # May already be enabled or no email
            print(f"INFO: Enable portal returned 400 - {response.json().get('detail', 'unknown reason')}")
            return
        
        assert response.status_code == 200, f"Enable portal failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "token" in data, "Portal token not returned"
        
        print(f"SUCCESS: Portal enabled - token: {data['token'][:20]}...")
        return data["token"]
    
    def test_enable_portal_invalid_contact(self):
        """Test enable portal for non-existent contact"""
        response = requests.post(
            f"{BASE_URL}/api/contacts-enhanced/invalid-contact-id/enable-portal",
            headers=self.admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid contact, got {response.status_code}"
        print("SUCCESS: Invalid contact correctly returns 404")


class TestPortalLogout:
    """Test portal logout functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get a valid session token"""
        # Get a fresh portal token
        portal_token = get_fresh_portal_token()
        if not portal_token:
            pytest.skip("Could not get portal token")
        
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": portal_token
        })
        
        if response.status_code != 200:
            pytest.skip("Could not get session token for logout test")
        
        self.session_token = response.json()["session_token"]
    
    def test_logout_with_header(self):
        """Test logout with X-Portal-Session header"""
        response = requests.post(
            f"{BASE_URL}/api/customer-portal/logout",
            headers={"X-Portal-Session": self.session_token}
        )
        
        print(f"Logout (header) status: {response.status_code}")
        assert response.status_code == 200, f"Logout failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        print("SUCCESS: Logout via header works")
        
        # Verify session is invalid after logout
        verify_response = requests.get(
            f"{BASE_URL}/api/customer-portal/dashboard",
            headers={"X-Portal-Session": self.session_token}
        )
        assert verify_response.status_code == 401, f"Session should be invalid after logout, got {verify_response.status_code}"
        print("SUCCESS: Session correctly invalidated after logout")


class TestPortalSessionInfo:
    """Test portal session info endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get a valid session token"""
        # Get a fresh portal token
        portal_token = get_fresh_portal_token()
        if not portal_token:
            pytest.skip("Could not get portal token")
        
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": portal_token
        })
        
        if response.status_code != 200:
            pytest.skip("Could not get session token")
        
        self.session_token = response.json()["session_token"]
    
    def test_session_info_with_header(self):
        """Test getting session info with header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/session",
            headers={"X-Portal-Session": self.session_token}
        )
        
        print(f"Session info (header) status: {response.status_code}")
        assert response.status_code == 200, f"Session info failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "session" in data, "session not in response"
        print(f"SUCCESS: Session info - contact: {data['session'].get('contact_name', 'N/A')}")
    
    def test_session_info_with_query_param(self):
        """Test getting session info with query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/session?session_token={self.session_token}"
        )
        
        print(f"Session info (query) status: {response.status_code}")
        assert response.status_code == 200, f"Session info with query failed: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "session" in data, "session not in response"
        print(f"SUCCESS: Session info via query - expires: {data['session'].get('expires_at', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
