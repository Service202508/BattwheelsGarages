"""
Test Suite for Subscription & Entitlement API Endpoints
=========================================================

Tests the subscription management and feature entitlement APIs.
Tests: GET /api/subscriptions/plans, /api/subscriptions/plans/compare,
       /api/subscriptions/current, /api/subscriptions/entitlements,
       /api/subscriptions/entitlements/{feature}, /api/subscriptions/limits
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone


BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPublicPlanEndpoints:
    """Tests for public subscription plan endpoints (no auth required)"""
    
    def test_list_plans_returns_all_plans(self):
        """GET /api/subscriptions/plans - List all available plans"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 4, f"Should have at least 4 plans (free, starter, professional, enterprise), got {len(data)}"
        
        # Validate plan structure
        plan_codes = [p["code"] for p in data]
        assert "free" in plan_codes, "Free plan missing"
        assert "starter" in plan_codes, "Starter plan missing"
        assert "professional" in plan_codes, "Professional plan missing"
        assert "enterprise" in plan_codes, "Enterprise plan missing"
        
        # Verify plan structure
        for plan in data:
            assert "plan_id" in plan, "Missing plan_id"
            assert "code" in plan, "Missing code"
            assert "name" in plan, "Missing name"
            assert "price_monthly" in plan, "Missing price_monthly"
            assert "price_annual" in plan, "Missing price_annual"
            assert "features" in plan, "Missing features"
            assert "limits" in plan, "Missing limits"
    
    def test_free_plan_has_correct_pricing(self):
        """Free plan should have 0 price"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans")
        assert response.status_code == 200
        
        data = response.json()
        free_plan = next((p for p in data if p["code"] == "free"), None)
        assert free_plan is not None, "Free plan not found"
        assert free_plan["price_monthly"] == 0, "Free plan monthly price should be 0"
        assert free_plan["price_annual"] == 0, "Free plan annual price should be 0"
    
    def test_enterprise_plan_has_all_features_enabled(self):
        """Enterprise plan should have all features enabled"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans")
        assert response.status_code == 200
        
        data = response.json()
        enterprise = next((p for p in data if p["code"] == "enterprise"), None)
        assert enterprise is not None, "Enterprise plan not found"
        
        # All features should be enabled
        features = enterprise["features"]
        disabled_features = [k for k, v in features.items() if not v.get("enabled", False)]
        assert len(disabled_features) == 0, f"Enterprise should have all features enabled, but these are disabled: {disabled_features}"
        
        # Limits should be unlimited (-1)
        limits = enterprise["limits"]
        assert limits["max_users"] == -1, "Enterprise should have unlimited users"
        assert limits["max_invoices_per_month"] == -1, "Enterprise should have unlimited invoices"
    
    def test_compare_plans_returns_comparison(self):
        """GET /api/subscriptions/plans/compare - Get plan comparison"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans/compare")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 4, "Should have at least 4 plans"
        
        # Verify comparison structure
        for plan in data:
            assert "code" in plan, "Missing code"
            assert "name" in plan, "Missing name"
            assert "price_monthly" in plan, "Missing price_monthly"
            assert "features" in plan, "Missing features"
            assert "limits" in plan, "Missing limits"
            assert "support_level" in plan, "Missing support_level"
    
    def test_get_specific_plan_by_code(self):
        """GET /api/subscriptions/plans/{plan_code} - Get specific plan"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans/starter")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["code"] == "starter", "Should return starter plan"
        assert data["name"] == "Starter", "Starter plan name mismatch"
        assert data["price_monthly"] > 0, "Starter plan should have a price"
    
    def test_invalid_plan_code_returns_404(self):
        """GET /api/subscriptions/plans/{invalid_code} - Should return 404"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans/invalid_plan_xyz")
        
        assert response.status_code == 404, f"Expected 404 for invalid plan, got {response.status_code}"


class TestAuthenticatedSubscriptionEndpoints:
    """Tests for authenticated subscription endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_test_org(self):
        """Create a test organization for each test"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        
        signup_data = {
            "name": f"TEST_Entitlement_API_{timestamp}_{unique_id}",
            "admin_name": "Test Admin",
            "admin_email": f"test_ent_{timestamp}_{unique_id}@test.com",
            "admin_password": "test_pwd_placeholder",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/organizations/signup",
            json=signup_data
        )
        
        if response.status_code != 200:
            pytest.skip(f"Could not create test org: {response.text}")
        
        data = response.json()
        self.token = data.get("token")
        self.org_id = data.get("organization", {}).get("organization_id")
        
        if not self.token or not self.org_id:
            pytest.skip("Missing token or org_id in signup response")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Organization-ID": self.org_id
        }
        
        yield
        
        # Cleanup (optional - test orgs with TEST_ prefix can be cleaned up later)
    
    def test_get_current_subscription(self):
        """GET /api/subscriptions/current - Get current organization subscription"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/current",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify subscription structure
        assert "subscription_id" in data, "Missing subscription_id"
        assert "organization_id" in data, "Missing organization_id"
        assert data["organization_id"] == self.org_id, "Organization ID mismatch"
        
        # Verify plan info
        assert "plan" in data, "Missing plan info"
        plan = data["plan"]
        assert "code" in plan, "Missing plan code"
        assert "name" in plan, "Missing plan name"
        
        # Verify status
        assert "status" in data, "Missing status"
        assert data["status"] in ["trialing", "active", "past_due", "canceled", "suspended", "expired"]
        
        # Verify period info
        assert "current_period_start" in data, "Missing current_period_start"
        assert "current_period_end" in data, "Missing current_period_end"
        
        # Verify usage
        assert "usage" in data, "Missing usage"
        assert "is_active" in data, "Missing is_active"
        assert "is_in_trial" in data, "Missing is_in_trial"
    
    def test_new_org_starts_with_trial(self):
        """New organizations should start with a trial subscription"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/current",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # New orgs should be in trial
        assert data["is_in_trial"] == True, "New org should be in trial"
        assert data["is_active"] == True, "Trial subscription should be active"
        assert data["status"] == "trialing", "Status should be 'trialing'"
    
    def test_get_all_entitlements(self):
        """GET /api/subscriptions/entitlements - Get all feature entitlements"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/entitlements",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "organization_id" in data, "Missing organization_id"
        assert "plan" in data, "Missing plan"
        assert "status" in data, "Missing status"
        assert "features" in data, "Missing features"
        assert "is_active" in data, "Missing is_active"
        assert "is_trial" in data, "Missing is_trial"
        
        # Verify features dictionary
        features = data["features"]
        assert isinstance(features, dict), "Features should be a dictionary"
        
        # Check some expected features exist
        expected_features = [
            "ops_tickets", "ops_vehicles", "finance_invoicing",
            "efi_ai_guidance", "hr_payroll", "advanced_sso"
        ]
        for feature in expected_features:
            assert feature in features, f"Missing feature: {feature}"
            assert isinstance(features[feature], bool), f"Feature {feature} should be boolean"
    
    def test_check_enabled_feature(self):
        """GET /api/subscriptions/entitlements/{feature} - Check enabled feature"""
        # efi_ai_guidance is enabled for starter plan
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/entitlements/efi_ai_guidance",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["feature"] == "efi_ai_guidance", "Feature name mismatch"
        assert data["enabled"] == True, "efi_ai_guidance should be enabled for starter plan"
        assert data["minimum_plan_required"] == "starter", "Minimum plan should be starter"
        assert data["current_plan"] == "starter", "Current plan should be starter"
        
        # Check limit is set
        assert data["limit"] == 100, "efi_ai_guidance should have limit of 100 for starter"
    
    def test_check_disabled_feature_with_upgrade_suggestion(self):
        """GET /api/subscriptions/entitlements/{feature} - Check disabled feature returns upgrade_to"""
        # hr_payroll is enterprise only
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/entitlements/hr_payroll",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["feature"] == "hr_payroll", "Feature name mismatch"
        assert data["enabled"] == False, "hr_payroll should be disabled for starter plan"
        assert data["minimum_plan_required"] == "enterprise", "hr_payroll requires enterprise"
        
        # Should suggest upgrade
        assert "upgrade_to" in data, "Should have upgrade_to suggestion"
        assert data["upgrade_to"] == "Enterprise", "Should suggest Enterprise upgrade"
    
    def test_check_unknown_feature_returns_404(self):
        """GET /api/subscriptions/entitlements/{feature} - Unknown feature returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/entitlements/unknown_feature_xyz",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404 for unknown feature, got {response.status_code}"
    
    def test_get_usage_limits(self):
        """GET /api/subscriptions/limits - Get usage limits and current usage"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/limits",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "organization_id" in data, "Missing organization_id"
        assert "plan" in data, "Missing plan"
        assert "billing_cycle" in data, "Missing billing_cycle"
        assert "period" in data, "Missing period"
        assert "limits" in data, "Missing limits"
        
        # Verify limits structure
        limits = data["limits"]
        expected_limit_keys = ["invoices", "tickets", "vehicles", "ai_calls", "api_calls", "users", "technicians", "storage_gb"]
        for key in expected_limit_keys:
            assert key in limits, f"Missing limit key: {key}"
        
        # Verify invoices limit structure
        invoices = limits["invoices"]
        assert "current" in invoices, "Missing current usage"
        assert "limit" in invoices, "Missing limit"
        assert "percent" in invoices, "Missing percent"
        assert "remaining" in invoices, "Missing remaining"
        
        # New org should have 0 usage
        assert invoices["current"] == 0, "New org should have 0 invoice usage"
    
    def test_starter_plan_limits_match_expected(self):
        """Verify starter plan has correct limits"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/limits",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        limits = data["limits"]
        
        # Starter plan expected limits
        assert limits["invoices"]["limit"] == 500, "Starter should have 500 invoice limit"
        assert limits["tickets"]["limit"] == 500, "Starter should have 500 ticket limit"
        assert limits["vehicles"]["limit"] == 100, "Starter should have 100 vehicle limit"
        assert limits["ai_calls"]["limit"] == 100, "Starter should have 100 AI call limit"
        assert limits["users"]["limit"] == 3, "Starter should have 3 user limit"
        assert limits["technicians"]["limit"] == 2, "Starter should have 2 technician limit"


class TestSubscriptionEndpointsAuth:
    """Test authentication/authorization for subscription endpoints"""
    
    def test_current_subscription_requires_auth(self):
        """GET /api/subscriptions/current - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/current")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_entitlements_requires_auth(self):
        """GET /api/subscriptions/entitlements - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/entitlements")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_entitlement_check_requires_auth(self):
        """GET /api/subscriptions/entitlements/{feature} - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/entitlements/efi_ai_guidance")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_limits_requires_auth(self):
        """GET /api/subscriptions/limits - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/limits")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_invalid_org_id_returns_403(self):
        """Invalid X-Organization-ID should return 403"""
        # First create a valid org and get token
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        
        signup_data = {
            "name": f"TEST_Auth_Test_{timestamp}_{unique_id}",
            "admin_name": "Test Admin",
            "admin_email": f"test_auth_{timestamp}_{unique_id}@test.com",
            "admin_password": "test_pwd_placeholder",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        signup_response = requests.post(
            f"{BASE_URL}/api/v1/organizations/signup",
            json=signup_data
        )
        
        if signup_response.status_code != 200:
            pytest.skip("Could not create test org")
        
        token = signup_response.json().get("token")
        
        # Try with invalid org ID
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/current",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": "org_invalid_123456"
            }
        )
        
        assert response.status_code == 403, f"Expected 403 for invalid org ID, got {response.status_code}"


class TestPlanFeatureEntitlement:
    """Test specific feature entitlements across plans"""
    
    def test_free_plan_features(self):
        """Verify free plan has correct feature entitlements"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans/free")
        assert response.status_code == 200
        
        data = response.json()
        features = data["features"]
        
        # Free plan enabled features
        assert features["ops_tickets"]["enabled"] == True
        assert features["ops_vehicles"]["enabled"] == True
        assert features["finance_invoicing"]["enabled"] == True
        assert features["finance_payments"]["enabled"] == True
        assert features["portal_technician"]["enabled"] == True
        
        # Free plan disabled features
        assert features["ops_amc"]["enabled"] == False
        assert features["finance_recurring_invoices"]["enabled"] == False
        assert features["inventory_tracking"]["enabled"] == False
        assert features["hr_payroll"]["enabled"] == False
        assert features["advanced_sso"]["enabled"] == False
    
    def test_starter_plan_features(self):
        """Verify starter plan has correct feature entitlements"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans/starter")
        assert response.status_code == 200
        
        data = response.json()
        features = data["features"]
        
        # Starter plan enabled features (in addition to free)
        assert features["ops_amc"]["enabled"] == True
        assert features["finance_recurring_invoices"]["enabled"] == True
        assert features["inventory_tracking"]["enabled"] == True
        assert features["efi_failure_intelligence"]["enabled"] == True
        assert features["efi_ai_guidance"]["enabled"] == True
        assert features["portal_customer"]["enabled"] == True
        
        # Starter plan disabled features
        assert features["finance_bills"]["enabled"] == False
        assert features["hr_payroll"]["enabled"] == False
        assert features["integrations_webhooks"]["enabled"] == False
    
    def test_professional_plan_features(self):
        """Verify professional plan has correct feature entitlements"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans/professional")
        assert response.status_code == 200
        
        data = response.json()
        features = data["features"]
        
        # Professional plan enabled features
        assert features["finance_bills"]["enabled"] == True
        assert features["finance_expenses"]["enabled"] == True
        assert features["finance_banking"]["enabled"] == True
        assert features["inventory_serial_batch"]["enabled"] == True
        assert features["hr_employees"]["enabled"] == True
        assert features["efi_knowledge_brain"]["enabled"] == True
        assert features["integrations_zoho_sync"]["enabled"] == True
        assert features["integrations_api_access"]["enabled"] == True
        assert features["advanced_reports"]["enabled"] == True
        
        # Professional plan disabled features (enterprise only)
        assert features["hr_payroll"]["enabled"] == False
        assert features["advanced_workflow_automation"]["enabled"] == False
        assert features["advanced_sso"]["enabled"] == False
    
    def test_enterprise_all_features_enabled(self):
        """Verify enterprise plan has ALL features enabled"""
        response = requests.get(f"{BASE_URL}/api/v1/subscriptions/plans/enterprise")
        assert response.status_code == 200
        
        data = response.json()
        features = data["features"]
        
        # ALL features should be enabled
        for feature_key, feature_data in features.items():
            assert feature_data["enabled"] == True, f"Enterprise should have {feature_key} enabled"
        
        # Enterprise-only features specifically
        assert features["hr_payroll"]["enabled"] == True
        assert features["efi_expert_escalation"]["enabled"] == True
        assert features["integrations_webhooks"]["enabled"] == True
        assert features["advanced_workflow_automation"]["enabled"] == True
        assert features["advanced_white_label"]["enabled"] == True
        assert features["advanced_sso"]["enabled"] == True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
