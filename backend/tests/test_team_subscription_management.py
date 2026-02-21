"""
Team & Subscription Management API Tests
=========================================

Tests for:
- Subscription Management endpoints (current, entitlements, limits)
- Team Management endpoints (members, invite, cancel invite, update role)
- Organization Switcher data endpoints

Test account: test403debug@example.com / testpass123
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestAuthentication:
    """Test authentication and setup for Team & Subscription tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Shared requests session"""
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        return s
    
    @pytest.fixture(scope="class")
    def auth_data(self, session):
        """Get auth token and org_id from login"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test403debug@example.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code == 200:
            data = response.json()
            return {
                "token": data.get("token"),
                "user_id": data.get("user", {}).get("user_id"),
                "org_id": data.get("organization", {}).get("organization_id")
            }
        pytest.skip(f"Login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_data):
        """Headers with auth token and org ID"""
        return {
            "Authorization": f"Bearer {auth_data['token']}",
            "X-Organization-ID": auth_data["org_id"],
            "Content-Type": "application/json"
        }


class TestSubscriptionManagement(TestAuthentication):
    """Test Subscription Management API endpoints"""
    
    def test_get_current_subscription(self, session, auth_headers):
        """Test GET /api/subscriptions/current - Returns current subscription"""
        response = session.get(f"{BASE_URL}/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "subscription_id" in data
        assert "plan" in data
        assert "status" in data
        assert data["plan"].get("code") in ["free", "starter", "professional", "enterprise"]
        print(f"Current plan: {data['plan']['code']}, status: {data['status']}")
    
    def test_get_subscription_entitlements(self, session, auth_headers):
        """Test GET /api/subscriptions/entitlements - Returns feature entitlements"""
        response = session.get(f"{BASE_URL}/api/subscriptions/entitlements", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "features" in data
        assert "plan" in data
        assert "is_active" in data
        
        features = data["features"]
        assert isinstance(features, dict)
        # Basic features should exist
        assert "ops_tickets" in features or len(features) > 0
        print(f"Plan: {data['plan']}, Active: {data['is_active']}, Features count: {len(features)}")
    
    def test_get_subscription_limits(self, session, auth_headers):
        """Test GET /api/subscriptions/limits - Returns usage limits"""
        response = session.get(f"{BASE_URL}/api/subscriptions/limits", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "limits" in data
        assert "plan" in data
        assert "billing_cycle" in data
        
        limits = data["limits"]
        # Check limit structure
        for key in ["invoices", "tickets", "vehicles", "ai_calls"]:
            if key in limits:
                limit_data = limits[key]
                assert "current" in limit_data or "limit" in limit_data
        print(f"Limits retrieved for plan: {data['plan']}")
    
    def test_subscription_requires_auth(self, session):
        """Test subscription endpoints require authentication"""
        # Without auth
        response = session.get(f"{BASE_URL}/api/subscriptions/current")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_compare_plans_public(self, session):
        """Test GET /api/subscriptions/plans/compare - Public endpoint"""
        response = session.get(f"{BASE_URL}/api/subscriptions/plans/compare")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check plan structure
        for plan in data:
            assert "code" in plan or "name" in plan
        print(f"Found {len(data)} plans in comparison")


class TestTeamManagement(TestAuthentication):
    """Test Team Management API endpoints"""
    
    def test_list_members(self, session, auth_headers):
        """Test GET /api/organizations/me/members - List team members"""
        response = session.get(f"{BASE_URL}/api/organizations/me/members", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "members" in data
        assert "total" in data
        
        members = data["members"]
        assert isinstance(members, list)
        
        if len(members) > 0:
            member = members[0]
            assert "user_id" in member
            assert "role" in member
            assert "email" in member or "name" in member
        print(f"Found {len(members)} team members")
    
    def test_list_invitations(self, session, auth_headers):
        """Test GET /api/organizations/me/invites - List invitations"""
        response = session.get(f"{BASE_URL}/api/organizations/me/invites", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "invites" in data
        
        invites = data["invites"]
        assert isinstance(invites, list)
        print(f"Found {len(invites)} invitations")
    
    def test_invite_user(self, session, auth_headers):
        """Test POST /api/organizations/me/invite - Send invitation"""
        test_email = f"TEST_invite_{uuid.uuid4().hex[:8]}@example.com"
        
        response = session.post(
            f"{BASE_URL}/api/organizations/me/invite",
            headers=auth_headers,
            json={
                "name": "Test Invite User",
                "email": test_email,
                "role": "technician"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "invite_id" in data
        assert "invite_link" in data
        
        # Store for cancel test
        pytest.invite_id = data["invite_id"]
        print(f"Created invitation: {data['invite_id']}")
    
    def test_invite_user_duplicate(self, session, auth_headers):
        """Test duplicate invitation returns 400"""
        # First create an invite
        test_email = f"TEST_dup_{uuid.uuid4().hex[:8]}@example.com"
        
        response1 = session.post(
            f"{BASE_URL}/api/organizations/me/invite",
            headers=auth_headers,
            json={
                "name": "Test Dup User",
                "email": test_email,
                "role": "technician"
            }
        )
        assert response1.status_code == 200
        
        # Try duplicate
        response2 = session.post(
            f"{BASE_URL}/api/organizations/me/invite",
            headers=auth_headers,
            json={
                "name": "Test Dup User",
                "email": test_email,
                "role": "technician"
            }
        )
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}"
        print("Duplicate invite correctly rejected")
    
    def test_invite_user_invalid_role(self, session, auth_headers):
        """Test invalid role returns 422/400"""
        test_email = f"TEST_invalid_{uuid.uuid4().hex[:8]}@example.com"
        
        response = session.post(
            f"{BASE_URL}/api/organizations/me/invite",
            headers=auth_headers,
            json={
                "name": "Test User",
                "email": test_email,
                "role": "superadmin"  # Invalid role
            }
        )
        assert response.status_code in [400, 422], f"Expected 400/422 for invalid role, got {response.status_code}"
        print("Invalid role correctly rejected")
    
    def test_cancel_invitation(self, session, auth_headers):
        """Test DELETE /api/organizations/me/invites/{invite_id} - Cancel invitation"""
        # Create a new invite to cancel
        test_email = f"TEST_cancel_{uuid.uuid4().hex[:8]}@example.com"
        
        create_response = session.post(
            f"{BASE_URL}/api/organizations/me/invite",
            headers=auth_headers,
            json={
                "name": "Test Cancel User",
                "email": test_email,
                "role": "technician"
            }
        )
        assert create_response.status_code == 200
        invite_id = create_response.json()["invite_id"]
        
        # Cancel the invite
        response = session.delete(
            f"{BASE_URL}/api/organizations/me/invites/{invite_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print(f"Cancelled invitation: {invite_id}")
    
    def test_cancel_nonexistent_invitation(self, session, auth_headers):
        """Test cancelling non-existent invitation returns 404"""
        response = session.delete(
            f"{BASE_URL}/api/organizations/me/invites/inv_nonexistent123",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Non-existent invite cancel correctly returns 404")
    
    def test_update_member_role(self, session, auth_headers, auth_data):
        """Test PATCH /api/organizations/me/members/{user_id}/role - Update role"""
        # First get members
        members_response = session.get(
            f"{BASE_URL}/api/organizations/me/members",
            headers=auth_headers
        )
        assert members_response.status_code == 200
        
        members = members_response.json().get("members", [])
        
        # Find a non-owner member to update
        target_member = None
        for m in members:
            if m.get("role") not in ["owner"] and m.get("user_id") != auth_data["user_id"]:
                target_member = m
                break
        
        if target_member is None:
            pytest.skip("No non-owner members available to test role update")
        
        # Update role
        response = session.patch(
            f"{BASE_URL}/api/organizations/me/members/{target_member['user_id']}/role",
            headers=auth_headers,
            json={"role": "manager"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print(f"Updated member {target_member['user_id']} role to manager")
    
    def test_update_role_invalid(self, session, auth_headers):
        """Test invalid role update returns 400"""
        response = session.patch(
            f"{BASE_URL}/api/organizations/me/members/some_user_id/role",
            headers=auth_headers,
            json={"role": "superadmin"}  # Invalid role
        )
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print("Invalid role update correctly rejected")
    
    def test_team_endpoints_require_auth(self, session):
        """Test team endpoints require authentication"""
        endpoints = [
            ("GET", f"{BASE_URL}/api/organizations/me/members"),
            ("GET", f"{BASE_URL}/api/organizations/me/invites"),
            ("POST", f"{BASE_URL}/api/organizations/me/invite"),
        ]
        
        for method, url in endpoints:
            if method == "GET":
                response = session.get(url)
            else:
                response = session.post(url, json={})
            assert response.status_code in [401, 403, 422], f"{method} {url} should require auth, got {response.status_code}"
        print("Team endpoints correctly require authentication")


class TestOrganizationSwitcher(TestAuthentication):
    """Test Organization Switcher related endpoints"""
    
    def test_get_my_organizations(self, session, auth_headers):
        """Test GET /api/organizations/my-organizations - Get user's orgs"""
        response = session.get(
            f"{BASE_URL}/api/organizations/my-organizations",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "organizations" in data
        assert "total" in data
        
        orgs = data["organizations"]
        assert isinstance(orgs, list)
        assert len(orgs) >= 1, "User should belong to at least one org"
        
        # Check org structure
        org = orgs[0]
        assert "organization_id" in org
        assert "name" in org
        assert "role" in org
        print(f"User belongs to {len(orgs)} organization(s)")
    
    def test_get_current_organization(self, session, auth_headers):
        """Test GET /api/organizations/me - Get current org details"""
        response = session.get(
            f"{BASE_URL}/api/organizations/me",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "organization_id" in data
        assert "name" in data
        assert "plan_type" in data
        print(f"Current org: {data['name']}, plan: {data['plan_type']}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_invites(self):
        """Clean up TEST_ prefixed invites created during tests"""
        # This would be done via database cleanup in production
        # For now, we just log that cleanup should happen
        print("Note: TEST_ prefixed invitations should be cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
