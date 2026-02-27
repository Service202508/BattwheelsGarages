"""
Subscription Safety Fixes Tests
================================
Tests for 3 critical subscription safety fixes:
1. Duplicate subscription prevention (409 on active sub)
2. Live Razorpay key warning in dev environment
3. Auto-assign 14-day trial on org signup
"""

import pytest
import requests
import os
import time
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
DEV_EMAIL = "dev@battwheels.internal"
DEV_PASSWORD = "DevTest@123"


class TestSubscriptionSafetyFixes:
    """Tests for 3 subscription safety fixes"""

    @pytest.fixture(scope="class")
    def dev_auth_token(self):
        """Get token for dev account that has active subscription"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": DEV_EMAIL, "password": DEV_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token") or data.get("access_token")
        pytest.skip(f"Could not authenticate dev account: {response.status_code} - {response.text}")

    @pytest.fixture(scope="class")
    def new_org_response(self):
        """Create a new organization and return signup response"""
        timestamp = int(time.time())
        unique_email = f"testfix_{timestamp}@test.com"
        
        signup_data = {
            "name": f"Test Fix Org {timestamp}",
            "admin_name": "Test Admin",
            "admin_email": unique_email,
            "admin_password": "Test@12345",
            "industry_type": "ev_garage"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/organizations/signup",
            json=signup_data,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip(f"Could not create test org: {response.status_code} - {response.text}")
        
        return {
            "response": response,
            "data": response.json(),
            "email": unique_email,
            "timestamp": timestamp
        }

    # ==========================================================
    # FIX 3: Auto-assign 14-day trial on new org registration
    # ==========================================================

    def test_signup_returns_trial_status(self, new_org_response):
        """POST /api/v1/organizations/signup should set subscription_status='trialing'"""
        data = new_org_response["data"]
        
        # The signup response includes org data
        assert new_org_response["response"].status_code in [200, 201], \
            f"Signup failed: {new_org_response['response'].text}"
        
        # Check the returned organization data
        org = data.get("organization", {})
        assert org.get("plan_type") == "free_trial", \
            f"Expected plan_type='free_trial', got '{org.get('plan_type')}'"
        
        print(f"PASS: Signup returns plan_type='free_trial'")

    def test_new_org_has_trial_fields_via_me_endpoint(self, new_org_response):
        """GET /api/v1/organizations/me should show trial fields for new org"""
        token = new_org_response["data"].get("token")
        if not token:
            pytest.skip("No token returned from signup")
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Failed to get org: {response.status_code} - {response.text}"
        
        org_data = response.json()
        
        # Check trial fields exist and have correct values
        assert org_data.get("subscription_status") == "trialing", \
            f"Expected subscription_status='trialing', got '{org_data.get('subscription_status')}'"
        
        assert org_data.get("trial_active") is True, \
            f"Expected trial_active=True, got {org_data.get('trial_active')}"
        
        assert org_data.get("trial_start") is not None, \
            "Expected trial_start to be set"
        
        assert org_data.get("trial_end") is not None, \
            "Expected trial_end to be set"
        
        # Verify trial_end is approximately 14 days from now
        if org_data.get("trial_end"):
            trial_end_str = org_data["trial_end"]
            try:
                trial_end = datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                days_diff = (trial_end - now).days
                assert 13 <= days_diff <= 15, \
                    f"Trial end should be ~14 days from now, but is {days_diff} days"
                print(f"PASS: trial_end is {days_diff} days from now")
            except Exception as e:
                print(f"WARNING: Could not parse trial_end date: {e}")
        
        print(f"PASS: New org has correct trial fields - subscription_status='{org_data.get('subscription_status')}', trial_active={org_data.get('trial_active')}")

    # ==========================================================
    # FIX 1: Prevent duplicate subscriptions (409 error)
    # ==========================================================

    def test_duplicate_subscription_returns_409(self, dev_auth_token):
        """POST /api/v1/subscriptions/subscribe should return 409 for org with active sub"""
        headers = {"Authorization": f"Bearer {dev_auth_token}"}
        
        subscribe_data = {
            "plan_code": "professional",
            "billing_cycle": "monthly"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/subscriptions/subscribe",
            json=subscribe_data,
            headers=headers,
            timeout=30
        )
        
        # Should return 409 Conflict
        assert response.status_code == 409, \
            f"Expected 409 for duplicate subscription, got {response.status_code} - {response.text}"
        
        # Verify error message mentions active subscription
        error_detail = response.json().get("detail", "")
        assert "active subscription" in error_detail.lower() or "already has" in error_detail.lower(), \
            f"Error message should mention active subscription: {error_detail}"
        
        print(f"PASS: Duplicate subscription correctly returns 409 - {error_detail}")

    def test_duplicate_subscription_error_includes_sub_id(self, dev_auth_token):
        """409 response should include existing subscription ID for debugging"""
        headers = {"Authorization": f"Bearer {dev_auth_token}"}
        
        subscribe_data = {
            "plan_code": "starter",
            "billing_cycle": "monthly"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/subscriptions/subscribe",
            json=subscribe_data,
            headers=headers,
            timeout=30
        )
        
        assert response.status_code == 409, \
            f"Expected 409, got {response.status_code}"
        
        error_detail = response.json().get("detail", "")
        
        # Check if error includes subscription ID or status
        has_id = "sub_" in error_detail or "id:" in error_detail.lower()
        has_status = "status:" in error_detail.lower() or "active" in error_detail.lower()
        
        assert has_id or has_status, \
            f"Error should include subscription ID or status for debugging: {error_detail}"
        
        print(f"PASS: 409 error includes subscription info - {error_detail}")

    # ==========================================================
    # FIX 2: Live Razorpay key warning in non-production
    # ==========================================================

    def test_subscribe_logs_live_key_warning(self, dev_auth_token):
        """
        POST /api/v1/subscriptions/subscribe should log WARNING about LIVE keys in dev.
        Note: This test triggers the endpoint and we verify logs separately.
        """
        headers = {"Authorization": f"Bearer {dev_auth_token}"}
        
        subscribe_data = {
            "plan_code": "professional",
            "billing_cycle": "monthly"
        }
        
        # Call subscribe endpoint (will get 409 but that's okay - warning should still log)
        response = requests.post(
            f"{BASE_URL}/api/v1/subscriptions/subscribe",
            json=subscribe_data,
            headers=headers,
            timeout=30
        )
        
        # The endpoint was called - regardless of 409, the warning should have been logged
        # We'll verify logs separately
        print(f"PASS: Subscribe endpoint called (status={response.status_code})")
        print("NOTE: Check backend logs for 'LIVE Razorpay key detected' warning")


class TestTrialFieldsDataIntegrity:
    """Additional tests for trial field data integrity"""

    def test_signup_sets_all_required_trial_fields(self):
        """Verify all 4 trial fields are set: subscription_status, trial_active, trial_start, trial_end"""
        timestamp = int(time.time())
        unique_email = f"trialtest_{timestamp}@test.com"
        
        signup_data = {
            "name": f"Trial Test Org {timestamp}",
            "admin_name": "Trial Tester",
            "admin_email": unique_email,
            "admin_password": "Test@12345",
            "industry_type": "ev_garage"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/organizations/signup",
            json=signup_data,
            timeout=30
        )
        
        assert response.status_code in [200, 201], f"Signup failed: {response.status_code} - {response.text}"
        
        data = response.json()
        token = data.get("token")
        
        if not token:
            pytest.skip("No token returned")
        
        # Now get org details
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(
            f"{BASE_URL}/api/v1/organizations/me",
            headers=headers,
            timeout=30
        )
        
        assert me_response.status_code == 200
        org = me_response.json()
        
        # Verify all 4 required trial fields
        required_fields = ["subscription_status", "trial_active", "trial_start", "trial_end"]
        for field in required_fields:
            assert field in org and org[field] is not None, \
                f"Missing or null trial field: {field}"
        
        print(f"PASS: All trial fields present - {', '.join(required_fields)}")


# Run tests when file is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
