"""
Test suite for API v1 Versioning and Multi-Tenancy enforcement.
Tests:
1. Auth routes at /api/auth/ (login, register, logout, me, etc.)
2. Auth routes NOT at /api/v1/auth/ (should return 404/error)
3. Business routes at /api/v1/ (tickets, inventory, suppliers, etc.)
4. Health endpoint at /api/health
5. Multi-tenancy: API responses scoped to organization
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "Admin@12345"
ORG_ID = "dev-internal-testing-001"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_endpoint_accessible(self):
        """Health endpoint should be accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "db" in data
        print(f"Health check: {data}")


class TestAuthRoutesAtApiAuth:
    """Auth routes should work at /api/auth/"""
    
    @pytest.fixture
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_login_at_api_auth(self, auth_session):
        """POST /api/auth/login should work"""
        response = auth_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"Login successful: user={data['user']['email']}")
    
    def test_me_at_api_auth(self, auth_session):
        """GET /api/auth/me should return current user"""
        # First login
        login_response = auth_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        token = login_response.json().get("token")
        
        # Then check /me
        response = auth_session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == ADMIN_EMAIL
        print(f"Me endpoint returned: {data.get('email')}")
    
    def test_logout_at_api_auth(self, auth_session):
        """POST /api/auth/logout should work"""
        # First login
        login_response = auth_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        token = login_response.json().get("token")
        
        # Then logout
        response = auth_session.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Logout can return 200 or 204
        assert response.status_code in [200, 204], f"Logout failed: {response.text}"
        print("Logout successful")
    
    def test_session_at_api_auth(self, auth_session):
        """POST /api/auth/session should work (for OAuth callbacks)"""
        # Test that endpoint exists - it may require valid session_token
        response = auth_session.post(
            f"{BASE_URL}/api/auth/session",
            json={"session_token": "invalid_test_token"}
        )
        # Should return 4xx for invalid token, but NOT 404
        assert response.status_code != 404, "Session endpoint should exist at /api/auth/session"
        print(f"Session endpoint exists, returned: {response.status_code}")
    
    def test_forgot_password_at_api_auth(self, auth_session):
        """POST /api/auth/forgot-password should work"""
        response = auth_session.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        # Should return 200 (success or user-not-found silently handled)
        assert response.status_code in [200, 404], f"Forgot password endpoint issue: {response.text}"
        print(f"Forgot password endpoint returned: {response.status_code}")


class TestAuthRoutesNotAtApiV1:
    """Auth routes should NOT exist at /api/v1/auth/"""
    
    def test_login_not_at_v1(self):
        """POST /api/v1/auth/login should return 404 or auth error"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        # Should NOT be 200 - either 404 or 401 (v1 routes require auth)
        assert response.status_code != 200, f"Auth login should NOT work at /api/v1/auth/login"
        print(f"/api/v1/auth/login correctly returns {response.status_code}")
    
    def test_register_not_at_v1(self):
        """POST /api/v1/auth/register should return error"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": "test@test.com", "password": "Test@12345", "name": "Test"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code != 200, f"Auth register should NOT work at /api/v1/auth/register"
        print(f"/api/v1/auth/register correctly returns {response.status_code}")


class TestBusinessRoutesAtApiV1:
    """Business routes should work at /api/v1/"""
    
    @pytest.fixture
    def authenticated_session(self):
        """Get authenticated session with token and org_id"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Login failed - cannot test authenticated routes")
        
        data = response.json()
        token = data.get("token")
        org_id = data.get("current_organization") or ORG_ID
        
        session.headers.update({
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": org_id
        })
        return session, org_id
    
    def test_tickets_at_v1(self, authenticated_session):
        """GET /api/v1/tickets should return tickets"""
        session, org_id = authenticated_session
        response = session.get(f"{BASE_URL}/api/v1/tickets")
        assert response.status_code == 200, f"Tickets endpoint failed: {response.text}"
        data = response.json()
        assert "data" in data, "Response should have 'data' field"
        assert "pagination" in data, "Response should have 'pagination' field"
        print(f"Tickets returned: {len(data['data'])} items")
        
        # Verify organization_id in returned data
        for ticket in data["data"]:
            assert ticket.get("organization_id") == org_id, f"Ticket {ticket.get('ticket_id')} has wrong org_id"
    
    def test_inventory_at_v1(self, authenticated_session):
        """GET /api/v1/inventory should return inventory"""
        session, org_id = authenticated_session
        response = session.get(f"{BASE_URL}/api/v1/inventory")
        assert response.status_code == 200, f"Inventory endpoint failed: {response.text}"
        data = response.json()
        assert "data" in data
        print(f"Inventory returned: {len(data['data'])} items")
        
        # Verify organization_id
        for item in data["data"]:
            assert item.get("organization_id") == org_id, f"Inventory item has wrong org_id"
    
    def test_suppliers_at_v1(self, authenticated_session):
        """GET /api/v1/suppliers should return suppliers"""
        session, org_id = authenticated_session
        response = session.get(f"{BASE_URL}/api/v1/suppliers")
        assert response.status_code == 200, f"Suppliers endpoint failed: {response.text}"
        print(f"Suppliers endpoint returned: {response.status_code}")
    
    def test_users_at_v1(self, authenticated_session):
        """GET /api/v1/users should return users"""
        session, org_id = authenticated_session
        response = session.get(f"{BASE_URL}/api/v1/users")
        assert response.status_code == 200, f"Users endpoint failed: {response.text}"
        print(f"Users endpoint returned: {response.status_code}")
    
    def test_invoices_at_v1(self, authenticated_session):
        """GET /api/v1/invoices should return invoices"""
        session, org_id = authenticated_session
        response = session.get(f"{BASE_URL}/api/v1/invoices")
        assert response.status_code == 200, f"Invoices endpoint failed: {response.text}"
        print(f"Invoices endpoint returned: {response.status_code}")
    
    def test_dashboard_stats_at_v1(self, authenticated_session):
        """GET /api/v1/dashboard/stats should return dashboard stats"""
        session, org_id = authenticated_session
        response = session.get(f"{BASE_URL}/api/v1/dashboard/stats")
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        print(f"Dashboard stats returned: {list(data.keys())[:5]}...")


class TestMultiTenancyEnforcement:
    """Multi-tenancy: API responses should be scoped to organization"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Login failed")
        
        data = response.json()
        token = data.get("token")
        org_id = data.get("current_organization")
        
        session.headers.update({
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": org_id
        })
        return session, org_id, token
    
    def test_tickets_scoped_to_org(self, admin_session):
        """All tickets should belong to the logged-in user's org"""
        session, org_id, _ = admin_session
        response = session.get(f"{BASE_URL}/api/v1/tickets")
        assert response.status_code == 200
        
        data = response.json()
        tickets = data.get("data", [])
        
        for ticket in tickets:
            assert ticket.get("organization_id") == org_id, \
                f"TENANT LEAK: Ticket {ticket.get('ticket_id')} belongs to org {ticket.get('organization_id')}, not {org_id}"
        
        print(f"All {len(tickets)} tickets correctly scoped to org {org_id}")
    
    def test_inventory_scoped_to_org(self, admin_session):
        """All inventory should belong to the logged-in user's org"""
        session, org_id, _ = admin_session
        response = session.get(f"{BASE_URL}/api/v1/inventory")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("data", [])
        
        for item in items:
            assert item.get("organization_id") == org_id, \
                f"TENANT LEAK: Inventory {item.get('item_id')} belongs to org {item.get('organization_id')}, not {org_id}"
        
        print(f"All {len(items)} inventory items correctly scoped to org {org_id}")
    
    def test_x_org_header_required(self, admin_session):
        """Requests without X-Organization-ID should handle gracefully"""
        session, org_id, token = admin_session
        
        # Remove org header
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
            # No X-Organization-ID
        }
        
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers=headers
        )
        
        # Should either use org from JWT or return error
        # It should NOT return all orgs' data
        if response.status_code == 200:
            data = response.json()
            tickets = data.get("data", [])
            # Even without header, should still be scoped
            for ticket in tickets:
                assert ticket.get("organization_id") == org_id, \
                    "TENANT LEAK: Without org header, returned data from other org"
        
        print(f"Without X-Org header: status={response.status_code}")


class TestTicketCloseEndpoint:
    """Test ticket close endpoint accepts confirmed_fault field"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Login failed")
        
        data = response.json()
        token = data.get("token")
        org_id = data.get("current_organization")
        
        session.headers.update({
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": org_id
        })
        return session, org_id
    
    def test_close_ticket_endpoint_exists(self, admin_session):
        """POST /api/v1/tickets/{id}/close should exist"""
        session, org_id = admin_session
        
        # Get a ticket first
        tickets_response = session.get(f"{BASE_URL}/api/v1/tickets")
        if tickets_response.status_code != 200:
            pytest.skip("Cannot get tickets")
        
        tickets = tickets_response.json().get("data", [])
        if not tickets:
            pytest.skip("No tickets available to test close")
        
        # Try to close any ticket (may fail if not in right status)
        ticket_id = tickets[0]["ticket_id"]
        close_response = session.post(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/close",
            json={
                "resolution": "Test resolution",
                "resolution_outcome": "success",
                "confirmed_fault": "Test confirmed fault for EFI"
            }
        )
        
        # Either works (200) or fails due to status (400) - but NOT 404
        assert close_response.status_code != 404, \
            "Close ticket endpoint should exist at /api/v1/tickets/{id}/close"
        print(f"Close ticket endpoint returned: {close_response.status_code}")
        
        if close_response.status_code == 200:
            print("Ticket closed successfully with confirmed_fault field")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
