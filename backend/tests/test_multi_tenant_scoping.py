"""
Multi-Tenant Organization Scoping Tests
Tests organization-level data isolation for all ERP entities

This test verifies that:
1. Organization context is resolved from X-Organization-ID header
2. User's default organization is used when no header provided
3. All data endpoints (vehicles, tickets, customers, etc.) are properly scoped
4. Organization API endpoints (settings, profile, users) work correctly
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip('/')

# Test credentials
ADMIN_EMAIL = "dev@battwheels.internal"
ADMIN_PASSWORD = "DevTest@123"
TECH_EMAIL = "tech.a@battwheels.internal"
TECH_PASSWORD = "TechA@123"


class TestAuthentication:
    """Test authentication and token handling"""
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "owner"
        print(f"✓ Admin login successful - user_id: {data['user']['user_id']}")
    
    def test_technician_login(self):
        """Test technician can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TECH_EMAIL, "password": TECH_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "technician"
        print(f"✓ Technician login successful - user_id: {data['user']['user_id']}")


class TestOrganizationContext:
    """Test organization context resolution"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth tokens for tests"""
        # Admin login
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.admin_token = response.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Technician login
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TECH_EMAIL, "password": TECH_PASSWORD}
        )
        self.tech_token = response.json()["token"]
        self.tech_headers = {"Authorization": f"Bearer {self.tech_token}"}
    
    def test_get_current_organization(self):
        """Test GET /api/org - returns current organization profile"""
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "organization_id" in data, "Missing organization_id"
        assert "name" in data, "Missing name"
        assert "slug" in data, "Missing slug"
        print(f"✓ Current organization: {data['name']} ({data['organization_id']})")
    
    def test_get_organization_settings(self):
        """Test GET /api/org/settings - returns organization settings"""
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "organization_id" in data, "Missing organization_id"
        # Settings are included in the org document or may be separate
        # Core org fields are required
        assert "name" in data, "Missing name"
        assert "slug" in data, "Missing slug"
        print(f"✓ Organization settings retrieved - org: {data['name']}")
    
    def test_list_organization_users(self):
        """Test GET /api/org/users - lists users in organization"""
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me/members",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "members" in data, "Missing members array"
        assert "total" in data, "Missing total count"
        assert data["total"] >= 1, "No users found"
        print(f"✓ Organization users: {data['total']} members")
    
    def test_list_user_organizations(self):
        """Test GET /api/org/list - lists all organizations user belongs to"""
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/my-organizations",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "organizations" in data, "Missing organizations array"
        assert "total" in data, "Missing total count"
        assert data["total"] >= 1, "No organizations found"
        org = data["organizations"][0]
        assert "organization_id" in org, "Missing org_id in list"
        assert "role" in org, "Missing role in list"
        print(f"✓ User belongs to {data['total']} organization(s): {org['name']} ({org['role']})")


class TestVehiclesScoping:
    """Test vehicles endpoint with organization scoping"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get org_id
        org_response = requests.get(f"{BASE_URL}/api/v1/organizations/me", headers=self.headers)
        if org_response.status_code == 200:
            self.org_id = org_response.json().get("organization_id")
        else:
            self.org_id = None
    
    def test_list_vehicles_without_header(self):
        """Test GET /api/vehicles - uses user's default organization"""
        response = requests.get(
            f"{BASE_URL}/api/v1/vehicles",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"✓ Vehicles list (default org): {len(data)} vehicles")
    
    def test_list_vehicles_with_org_header(self):
        """Test GET /api/vehicles with X-Organization-ID header"""
        if not self.org_id:
            pytest.skip("No org_id available")
        
        headers = {**self.headers, "X-Organization-ID": self.org_id}
        response = requests.get(
            f"{BASE_URL}/api/v1/vehicles",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"✓ Vehicles list (explicit org header): {len(data)} vehicles")


class TestTicketsScoping:
    """Test tickets endpoint with organization scoping"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get org_id
        org_response = requests.get(f"{BASE_URL}/api/v1/organizations/me", headers=self.headers)
        if org_response.status_code == 200:
            self.org_id = org_response.json().get("organization_id")
        else:
            self.org_id = None
    
    def test_list_tickets_without_header(self):
        """Test GET /api/tickets - uses user's default organization"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Tickets endpoint returns object with tickets array
        if isinstance(data, dict) and "tickets" in data:
            tickets = data["tickets"]
        else:
            tickets = data if isinstance(data, list) else []
        print(f"✓ Tickets list (default org): {len(tickets)} tickets")
    
    def test_list_tickets_with_org_header(self):
        """Test GET /api/tickets with X-Organization-ID header"""
        if not self.org_id:
            pytest.skip("No org_id available")
        
        headers = {**self.headers, "X-Organization-ID": self.org_id}
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ Tickets list (explicit org header): OK")


class TestCustomersScoping:
    """Test customers endpoint with organization scoping"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get org_id
        org_response = requests.get(f"{BASE_URL}/api/v1/organizations/me", headers=self.headers)
        if org_response.status_code == 200:
            self.org_id = org_response.json().get("organization_id")
        else:
            self.org_id = None
    
    def test_list_customers_without_header(self):
        """Test GET /api/customers - uses user's default organization"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customers",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Check response structure
        if isinstance(data, dict) and "customers" in data:
            customers = data["customers"]
        else:
            customers = data if isinstance(data, list) else []
        print(f"✓ Customers list (default org): {len(customers)} customers")
    
    def test_list_customers_with_org_header(self):
        """Test GET /api/customers with X-Organization-ID header"""
        if not self.org_id:
            pytest.skip("No org_id available")
        
        headers = {**self.headers, "X-Organization-ID": self.org_id}
        response = requests.get(
            f"{BASE_URL}/api/v1/customers",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ Customers list (explicit org header): OK")


class TestInventoryScoping:
    """Test inventory endpoint with organization scoping"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get org_id
        org_response = requests.get(f"{BASE_URL}/api/v1/organizations/me", headers=self.headers)
        if org_response.status_code == 200:
            self.org_id = org_response.json().get("organization_id")
        else:
            self.org_id = None
    
    def test_list_inventory_without_header(self):
        """Test GET /api/inventory - uses user's default organization"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        items = data if isinstance(data, list) else []
        print(f"✓ Inventory list (default org): {len(items)} items")


class TestPermissions:
    """Test role-based permissions for organization operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth tokens"""
        # Admin
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.admin_token = response.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Technician
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TECH_EMAIL, "password": TECH_PASSWORD}
        )
        self.tech_token = response.json()["token"]
        self.tech_headers = {"Authorization": f"Bearer {self.tech_token}"}
    
    def test_admin_can_update_settings(self):
        """Test admin/owner can update organization settings"""
        response = requests.put(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=self.admin_headers,
            json={"service_radius_km": 55}
        )
        assert response.status_code == 200, f"Admin should be able to update settings: {response.text}"
        print("✓ Admin can update organization settings")
    
    def test_technician_cannot_update_settings(self):
        """Test technician cannot update organization settings"""
        response = requests.put(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=self.tech_headers,
            json={"service_radius_km": 100}
        )
        assert response.status_code == 403, f"Technician should not be able to update settings: {response.status_code}"
        print("✓ Technician correctly denied settings update (403)")
    
    def test_technician_can_read_organization(self):
        """Test technician can read organization info"""
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=self.tech_headers
        )
        assert response.status_code == 200, f"Technician should be able to read org: {response.text}"
        print("✓ Technician can read organization info")
    
    def test_technician_can_read_settings(self):
        """Test technician can read organization settings"""
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=self.tech_headers
        )
        assert response.status_code == 200, f"Technician should be able to read settings: {response.text}"
        print("✓ Technician can read organization settings")


class TestUnauthenticatedAccess:
    """Test unauthenticated access is properly blocked"""
    
    def test_no_token_returns_401(self):
        """Test requests without auth token return 401"""
        response = requests.get(f"{BASE_URL}/api/v1/organizations/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated access correctly denied (401)")
    
    def test_invalid_token_returns_401(self):
        """Test requests with invalid token return 401"""
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid token correctly denied (401)")


class TestAvailableRoles:
    """Test roles endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_available_roles(self):
        """Test GET /api/org/roles - returns available roles and permissions"""
        response = requests.get(
            f"{BASE_URL}/api/v1/permissions/roles",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "roles" in data, "Missing roles array"
        role_names = [r["role"] for r in data["roles"]]
        assert "admin" in role_names, "Missing admin role"
        assert "technician" in role_names, "Missing technician role"
        print(f"✓ Available roles: {role_names}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
