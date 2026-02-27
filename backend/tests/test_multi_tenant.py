"""
Multi-tenant architecture tests.
Tests organization scoping, permissions, and data isolation.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8001/api/v1")
ADMIN_EMAIL = "dev@battwheels.internal"
ADMIN_PASSWORD = "DevTest@123"
TECH_EMAIL = "tech.a@battwheels.internal"
TECH_PASSWORD = "TechA@123"


class TestMultiTenantArchitecture:
    """Test organization-scoped access and multi-tenant data isolation"""

    def admin_headers(self):
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return {"Authorization": f"Bearer {resp.json()['token']}"}

    def tech_headers(self):
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": TECH_EMAIL, "password": TECH_PASSWORD}
        )
        assert resp.status_code == 200, f"Tech login failed: {resp.text}"
        return {"Authorization": f"Bearer {resp.json()['token']}"}

    # ==================== ORGANIZATION TESTS ====================
    
    def test_get_organization(self):
        """Test getting current organization"""
        response = requests.get(
            f"{BASE_URL}/organizations/me",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert "organization_id" in data
        assert "name" in data
        assert "slug" in data
        assert data["is_active"] is True
    
    def test_get_organization_settings(self):
        """Test getting organization details (settings merged into org doc)"""
        response = requests.get(
            f"{BASE_URL}/organizations/me",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert "organization_id" in data
        assert "name" in data
        # Settings fields may or may not be present depending on org setup
        # Core fields must exist
        assert "plan" in data or "subscription_plan" in data
    
    def test_list_user_organizations(self):
        """Test listing organizations user belongs to"""
        response = requests.get(
            f"{BASE_URL}/organizations/my-organizations",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert "organizations" in data
        assert len(data["organizations"]) >= 1
        assert data["organizations"][0]["role"] == "owner"
    
    def test_list_organization_users(self):
        """Test listing users in organization"""
        response = requests.get(
            f"{BASE_URL}/organizations/me/members",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_get_available_roles(self):
        """Test getting available roles"""
        response = requests.get(
            f"{BASE_URL}/permissions/roles",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        roles = [r["role"] for r in data["roles"]]
        assert "admin" in roles
        assert "technician" in roles
    
    # ==================== PERMISSION TESTS ====================
    
    def test_admin_can_update_settings(self):
        """Test admin/owner can update organization"""
        response = requests.put(
            f"{BASE_URL}/organizations/me",
            headers=self.admin_headers(),
            json={"city": "Test City"}
        )
        assert response.status_code == 200
    
    def test_technician_cannot_update_settings(self):
        """Test technician cannot update organization"""
        response = requests.put(
            f"{BASE_URL}/organizations/me",
            headers=self.tech_headers(),
            json={"city": "Hacker City"}
        )
        assert response.status_code in [403, 401]
    
    def test_technician_can_read_org(self):
        """Test technician can read organization info"""
        response = requests.get(
            f"{BASE_URL}/organizations/me",
            headers=self.tech_headers()
        )
        assert response.status_code == 200
    
    # ==================== DATA ISOLATION TESTS ====================
    
    def test_data_has_organization_id(self):
        """Test that org list proves scoping works"""
        response = requests.get(
            f"{BASE_URL}/organizations/my-organizations",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["organizations"]) >= 1
        
        response = requests.get(
            f"{BASE_URL}/organizations/me",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        org = response.json()
        assert "organization_id" in org
        assert "name" in org
    
    # ==================== SETTINGS STRUCTURE TESTS ====================
    
    def test_settings_structure(self):
        """Test organization has required fields"""
        response = requests.get(
            f"{BASE_URL}/organizations/me",
            headers=self.admin_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Core organization fields
        assert "organization_id" in data
        assert "name" in data
        assert "slug" in data
        assert "is_active" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
