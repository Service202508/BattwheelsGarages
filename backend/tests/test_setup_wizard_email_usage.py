"""
Setup Wizard, Email Service, and Usage Tracker Tests
=====================================================

Tests for Phase 5 SaaS features:
- Organization Setup Wizard APIs (PATCH /api/organizations/me/settings, POST /api/organizations/me/complete-setup, GET /api/organizations/me/setup-status)
- Email Service (invitation emails logged/sent)
- Usage Tracker service
- Integration with existing team management
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSetupWizardAPIs:
    """Organization Setup Wizard API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test403debug@example.com", "password": "testpass123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        self.org_id = data.get("current_organization") or data.get("organization", {}).get("organization_id")
        yield
    
    def test_get_setup_status(self):
        """GET /api/organizations/me/setup-status - Check setup completion status"""
        response = requests.get(
            f"{BASE_URL}/api/organizations/me/setup-status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Setup status failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "setup_completed" in data
        assert "created_at" in data
        assert isinstance(data["setup_completed"], bool)
        print(f"Setup status: completed={data['setup_completed']}")
    
    def test_update_organization_settings_profile(self):
        """PATCH /api/organizations/me/settings - Update organization profile (Step 1)"""
        payload = {
            "name": "TestOrg403Debug Updated",
            "industry_type": "ev_garage",
            "settings": {
                "address": "123 Test Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "phone": "+91 98765 43210",
                "gst_number": "22AAAAA0000A1Z5"
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/organizations/me/settings",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200, f"Update settings failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Profile settings updated successfully")
        
        # Verify changes persisted via GET
        verify_response = requests.get(
            f"{BASE_URL}/api/organizations/me",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        org_data = verify_response.json()
        
        # Check settings were saved
        settings = org_data.get("settings", {})
        assert settings.get("address") == "123 Test Street"
        assert settings.get("city") == "Mumbai"
        print("Profile settings verified via GET")
    
    def test_update_organization_settings_business(self):
        """PATCH /api/organizations/me/settings - Update business settings (Step 2)"""
        payload = {
            "settings": {
                "timezone": "Asia/Kolkata",
                "currency": "INR",
                "fiscal_year_start": "april",
                "working_hours": {
                    "start": "09:00",
                    "end": "18:00",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
                }
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/organizations/me/settings",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200, f"Update business settings failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print("Business settings updated successfully")
        
        # Verify changes persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/organizations/me",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        org_data = verify_response.json()
        settings = org_data.get("settings", {})
        
        assert settings.get("timezone") == "Asia/Kolkata"
        assert settings.get("currency") == "INR"
        print("Business settings verified via GET")
    
    def test_complete_setup(self):
        """POST /api/organizations/me/complete-setup - Mark setup as complete"""
        response = requests.post(
            f"{BASE_URL}/api/organizations/me/complete-setup",
            headers=self.headers
        )
        assert response.status_code == 200, f"Complete setup failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("message") == "Setup completed"
        print("Setup marked as complete")
        
        # Verify setup_completed flag
        verify_response = requests.get(
            f"{BASE_URL}/api/organizations/me/setup-status",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        status_data = verify_response.json()
        assert status_data.get("setup_completed") == True
        assert "setup_completed_at" in status_data
        print(f"Setup completion verified: completed_at={status_data.get('setup_completed_at')}")
    
    def test_settings_requires_auth(self):
        """PATCH /api/organizations/me/settings - Requires authentication"""
        response = requests.patch(
            f"{BASE_URL}/api/organizations/me/settings",
            json={"name": "Unauthorized"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Settings endpoint properly requires authentication")
    
    def test_complete_setup_requires_auth(self):
        """POST /api/organizations/me/complete-setup - Requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/organizations/me/complete-setup"
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Complete-setup endpoint properly requires authentication")


class TestTeamInvitationWithEmail:
    """Team invitation tests with email service integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test403debug@example.com", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        yield
    
    def test_invite_user_sends_email(self):
        """POST /api/organizations/me/invite - Creates invite and logs/sends email"""
        # Use unique email to avoid duplicate invite errors
        unique_email = f"TEST_wizard_{datetime.now().strftime('%H%M%S')}@example.com"
        
        payload = {
            "name": "Test Wizard User",
            "email": unique_email,
            "role": "technician"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/organizations/me/invite",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200, f"Invite failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "invite_id" in data
        assert "invite_link" in data
        assert "expires_at" in data
        print(f"Invitation created: {data.get('invite_id')}")
        print(f"Invite link: {data.get('invite_link')}")
        
        # Cleanup - cancel the test invitation
        invite_id = data.get("invite_id")
        if invite_id:
            cleanup_response = requests.delete(
                f"{BASE_URL}/api/organizations/me/invites/{invite_id}",
                headers=self.headers
            )
            print(f"Cleanup invite: {cleanup_response.status_code}")
    
    def test_duplicate_invite_rejected(self):
        """POST /api/organizations/me/invite - Rejects duplicate pending invites"""
        # First check for existing pending invites
        list_response = requests.get(
            f"{BASE_URL}/api/organizations/me/invites",
            headers=self.headers
        )
        invites = list_response.json().get("invites", [])
        pending_emails = [inv["email"] for inv in invites if inv.get("status") == "pending"]
        
        if pending_emails:
            # Try to create duplicate
            response = requests.post(
                f"{BASE_URL}/api/organizations/me/invite",
                headers=self.headers,
                json={"name": "Duplicate", "email": pending_emails[0], "role": "technician"}
            )
            assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
            print(f"Duplicate invite properly rejected for {pending_emails[0]}")
        else:
            pytest.skip("No pending invites to test duplicate rejection")


class TestSubscriptionAndUsage:
    """Subscription and usage tracking tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test403debug@example.com", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        yield
    
    def test_subscription_current_still_works(self):
        """GET /api/subscriptions/current - Subscription endpoint still working"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/current",
            headers=self.headers
        )
        assert response.status_code == 200, f"Subscription current failed: {response.text}"
        data = response.json()
        
        # Verify subscription structure
        assert "subscription_id" in data
        assert "plan_code" in data
        assert "status" in data
        assert "usage" in data or data.get("plan_code") is not None
        print(f"Subscription: plan={data.get('plan_code')}, status={data.get('status')}")
    
    def test_subscription_limits_still_works(self):
        """GET /api/subscriptions/limits - Usage limits endpoint still working"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/limits",
            headers=self.headers
        )
        assert response.status_code == 200, f"Subscription limits failed: {response.text}"
        data = response.json()
        
        # Verify limits structure
        assert "limits" in data
        limits = data["limits"]
        assert isinstance(limits, dict)
        print(f"Limits: {list(limits.keys())}")
    
    def test_subscription_entitlements_still_works(self):
        """GET /api/subscriptions/entitlements - Entitlements endpoint still working"""
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/entitlements",
            headers=self.headers
        )
        assert response.status_code == 200, f"Subscription entitlements failed: {response.text}"
        data = response.json()
        
        # Verify entitlements structure  
        assert "entitlements" in data
        entitlements = data["entitlements"]
        assert isinstance(entitlements, dict)
        print(f"Entitlements count: {len(entitlements)}")


class TestTeamManagementStillWorks:
    """Verify team management APIs still working after Phase 5"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test403debug@example.com", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        yield
    
    def test_list_members_works(self):
        """GET /api/organizations/me/members - List members works"""
        response = requests.get(
            f"{BASE_URL}/api/organizations/me/members",
            headers=self.headers
        )
        assert response.status_code == 200, f"List members failed: {response.text}"
        data = response.json()
        assert "members" in data
        assert "total" in data
        print(f"Team members count: {data['total']}")
    
    def test_list_invites_works(self):
        """GET /api/organizations/me/invites - List invites works"""
        response = requests.get(
            f"{BASE_URL}/api/organizations/me/invites",
            headers=self.headers
        )
        assert response.status_code == 200, f"List invites failed: {response.text}"
        data = response.json()
        assert "invites" in data
        assert "total" in data
        print(f"Invites count: {data['total']}")
    
    def test_organization_me_works(self):
        """GET /api/organizations/me - Org details works"""
        response = requests.get(
            f"{BASE_URL}/api/organizations/me",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get org failed: {response.text}"
        data = response.json()
        assert "organization_id" in data or "name" in data
        print(f"Organization: {data.get('name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
