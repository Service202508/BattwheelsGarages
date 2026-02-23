"""
SaaS Onboarding Experience Test Suite
=====================================
Tests for multi-tenant SaaS features:
- Organization signup flow
- Login returns organizations list
- Organization selection for multi-org users
- Switch organization endpoint
- My organizations endpoint
- X-Organization-ID header handling
"""

import pytest
import requests
import os
import uuid

# Get API URL from environment
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://production-hardening-1.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "test_pwd_placeholder"


class TestSaaSLandingAPI:
    """Test basic API health and public endpoints"""
    
    def test_api_accessible(self):
        """Test that API is reachable via any endpoint"""
        # Use the login endpoint to check API is up
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@test.com", "password": "wrong"},
            timeout=10
        )
        # 401 is expected for wrong credentials, but API is responding
        assert response.status_code in [200, 401, 400], f"API not accessible: {response.status_code}"
        print("PASS: API is accessible")
    
    def test_public_saas_landing_assets(self):
        """Test that the SaaS landing page HTML is served at root"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        # Should return HTML content for React SPA
        assert response.status_code == 200, f"Landing page failed: {response.status_code}"
        print("PASS: SaaS landing page is accessible at root /")


class TestOrganizationSignup:
    """Test organization signup flow"""
    
    def test_signup_creates_organization_and_admin(self):
        """Test that signup creates org with admin user and returns token"""
        unique_id = uuid.uuid4().hex[:8]
        signup_data = {
            "name": f"TEST_Org_{unique_id}",
            "admin_name": f"Test Admin {unique_id}",
            "admin_email": f"test_admin_{unique_id}@test.com",
            "admin_password": "test_pwd_placeholder",
            "industry_type": "ev_garage",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json=signup_data,
            timeout=10
        )
        
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "token" in data, "No token returned"
        assert "organization" in data, "No organization returned"
        assert "user" in data, "No user returned"
        
        # Verify organization data
        org = data["organization"]
        assert org["organization_id"].startswith("org_"), f"Invalid org ID: {org.get('organization_id')}"
        assert org["name"] == signup_data["name"], "Org name mismatch"
        assert org["plan_type"] == "free_trial", f"Expected free_trial plan, got {org.get('plan_type')}"
        
        # Verify user data
        user = data["user"]
        assert user["email"] == signup_data["admin_email"], "Email mismatch"
        assert user["role"] == "admin", f"Expected admin role, got {user.get('role')}"
        
        print(f"PASS: Signup creates organization with ID: {org['organization_id']}")
        print(f"PASS: Signup creates admin user with ID: {user['user_id']}")
        print(f"PASS: Signup returns JWT token for immediate login")
    
    def test_signup_rejects_duplicate_email(self):
        """Test that signup rejects already registered email"""
        # Use the existing admin email
        signup_data = {
            "name": "Duplicate Test Org",
            "admin_name": "Admin",
            "admin_email": ADMIN_EMAIL,  # Already exists
            "admin_password": "test_pwd_placeholder",
            "industry_type": "ev_garage"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json=signup_data,
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        data = response.json()
        assert "already registered" in data.get("detail", "").lower() or "already" in data.get("detail", "").lower(), f"Unexpected error: {data}"
        print("PASS: Signup rejects duplicate email with 400")


class TestLoginWithOrganizations:
    """Test login flow with organization support"""
    
    def test_login_returns_organizations_list(self):
        """Test that login returns user's organizations"""
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "token" in data, "No token returned"
        assert "user" in data, "No user returned"
        assert "organizations" in data, "No organizations array returned"
        
        # Verify organizations structure (even if empty)
        orgs = data["organizations"]
        assert isinstance(orgs, list), f"Organizations should be list, got {type(orgs)}"
        
        if len(orgs) > 0:
            org = orgs[0]
            assert "organization_id" in org, "Org missing organization_id"
            assert "name" in org, "Org missing name"
            assert "role" in org, "Org missing role"
            print(f"PASS: Login returns {len(orgs)} organization(s) with user membership info")
        else:
            print("PASS: Login returns empty organizations list (user may not be in any org)")
        
        # If single org, should also return it as 'organization' key
        if len(orgs) == 1:
            assert "organization" in data, "Single org should return 'organization' key"
            print("PASS: Single org user gets organization object for auto-selection")
        
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test that login rejects invalid credentials"""
        login_data = {
            "email": "invalid@test.com",
            "password": "wrong_pwd_placeholder"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("PASS: Login rejects invalid credentials with 401")


class TestMyOrganizations:
    """Test my-organizations endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    def test_my_organizations_returns_user_orgs(self, auth_token):
        """Test that my-organizations returns user's organizations"""
        response = requests.get(
            f"{BASE_URL}/api/organizations/my-organizations",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        
        assert response.status_code == 200, f"My orgs failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "organizations" in data, "Missing organizations array"
        assert "total" in data, "Missing total count"
        
        orgs = data["organizations"]
        assert isinstance(orgs, list), "Organizations should be a list"
        
        if len(orgs) > 0:
            org = orgs[0]
            assert "organization_id" in org, "Missing organization_id"
            assert "name" in org, "Missing name"
            assert "role" in org, "Missing role"
            print(f"PASS: my-organizations returns {len(orgs)} org(s) with role info")
        else:
            print("PASS: my-organizations returns empty list (user not in any org)")
    
    def test_my_organizations_requires_auth(self):
        """Test that my-organizations requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/organizations/my-organizations",
            timeout=10
        )
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("PASS: my-organizations requires authentication")


class TestSwitchOrganization:
    """Test switch-organization endpoint"""
    
    @pytest.fixture
    def auth_and_orgs(self):
        """Get auth token and organizations"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        
        data = response.json()
        token = data.get("token")
        orgs = data.get("organizations", [])
        
        return {"token": token, "organizations": orgs}
    
    def test_switch_organization_returns_new_token(self, auth_and_orgs):
        """Test that switch-organization returns new token with org_id"""
        token = auth_and_orgs["token"]
        orgs = auth_and_orgs["organizations"]
        
        if len(orgs) == 0:
            pytest.skip("User has no organizations to switch to")
        
        target_org_id = orgs[0]["organization_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-organization",
            headers={"Authorization": f"Bearer {token}"},
            json={"organization_id": target_org_id},
            timeout=10
        )
        
        assert response.status_code == 200, f"Switch org failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert "token" in data, "No new token returned"
        assert "organization" in data, "No organization returned"
        
        org = data["organization"]
        assert org["organization_id"] == target_org_id, "Org ID mismatch"
        
        print(f"PASS: switch-organization returns new token for org: {org['name']}")
    
    def test_switch_organization_rejects_invalid_org(self, auth_and_orgs):
        """Test that switch-organization rejects invalid org_id"""
        token = auth_and_orgs["token"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-organization",
            headers={"Authorization": f"Bearer {token}"},
            json={"organization_id": "org_invalid_12345"},
            timeout=10
        )
        
        # Should reject with 403 (not a member) or 404 (not found)
        assert response.status_code in [403, 404], f"Expected 403/404 for invalid org, got {response.status_code}"
        print("PASS: switch-organization rejects invalid org_id")
    
    def test_switch_organization_requires_auth(self):
        """Test that switch-organization requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/switch-organization",
            json={"organization_id": "org_test123"},
            timeout=10
        )
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("PASS: switch-organization requires authentication")


class TestXOrganizationIDHeader:
    """Test X-Organization-ID header handling"""
    
    @pytest.fixture
    def auth_with_org(self):
        """Get auth token with organization"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        
        data = response.json()
        token = data.get("token")
        orgs = data.get("organizations", [])
        org_id = orgs[0]["organization_id"] if orgs else None
        
        return {"token": token, "org_id": org_id}
    
    def test_api_accepts_x_organization_id_header(self, auth_with_org):
        """Test that API accepts X-Organization-ID header"""
        token = auth_with_org["token"]
        org_id = auth_with_org.get("org_id")
        
        if not org_id:
            pytest.skip("No organization available for test")
        
        # Test with tickets endpoint (should be org-scoped)
        response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": org_id
            },
            timeout=10
        )
        
        # Should succeed (200) or at least not fail with "invalid header" error
        assert response.status_code in [200, 403, 404], f"Unexpected status: {response.status_code}"
        print(f"PASS: API accepts X-Organization-ID header, status: {response.status_code}")
    
    def test_invalid_org_header_returns_403(self, auth_with_org):
        """Test that invalid X-Organization-ID returns 403"""
        token = auth_with_org["token"]
        
        # Test with tickets endpoint using invalid org ID
        response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": "org_invalid_notexist"
            },
            timeout=10
        )
        
        # Should return 403 for tenant access denied
        assert response.status_code == 403, f"Expected 403 for invalid org, got {response.status_code}"
        print("PASS: Invalid X-Organization-ID returns 403 TENANT_ACCESS_DENIED")


class TestAuthMe:
    """Test auth/me endpoint"""
    
    def test_auth_me_returns_user_info(self):
        """Test that /auth/me returns current user"""
        # Login first
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        
        assert "user_id" in data, "Missing user_id"
        assert "email" in data, "Missing email"
        assert data["email"] == ADMIN_EMAIL, f"Email mismatch: {data.get('email')}"
        
        print(f"PASS: /auth/me returns user info for {data['email']}")
    
    def test_auth_me_without_token_returns_401(self):
        """Test that /auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("PASS: /auth/me requires authentication")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
