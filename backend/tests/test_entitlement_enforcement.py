"""
Feature Entitlement Enforcement Tests
======================================
Tests all 8 specified scenarios for plan-based feature access control.

Credentials:
- Admin (PROFESSIONAL): admin@battwheels.in / admin
- Platform Admin: platform-admin@battwheels.in / admin
- Starter Test User: john@testcompany.com / testpass123, org: org_9c74befbaa95
"""

import pytest
import requests
import os

# Use localhost:8001 for backend tests as specified by review_request
BASE_URL = "http://localhost:8001"

STARTER_EMAIL = "john@testcompany.com"
STARTER_PASSWORD = "test_pwd_placeholder"
STARTER_ORG = "org_9c74befbaa95"

PROFESSIONAL_EMAIL = "dev@battwheels.internal"
PROFESSIONAL_PASSWORD = "DevTest@123"

PLATFORM_ADMIN_EMAIL = "platform-admin@battwheels.in"
PLATFORM_ADMIN_PASSWORD = "DevTest@123"


# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def starter_token():
    """Get JWT token for starter org user"""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": STARTER_EMAIL,
        "password": STARTER_PASSWORD
    })
    if resp.status_code != 200:
        pytest.skip(f"Starter login failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.skip(f"No token in starter login response: {data}")
    return token


@pytest.fixture(scope="module")
def professional_token():
    """Get JWT token for professional org user"""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": PROFESSIONAL_EMAIL,
        "password": PROFESSIONAL_PASSWORD
    })
    if resp.status_code != 200:
        pytest.skip(f"Professional login failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.skip(f"No token in professional login response: {data}")
    return token


@pytest.fixture(scope="module")
def platform_admin_token():
    """Get JWT token for platform admin"""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": PLATFORM_ADMIN_EMAIL,
        "password": PLATFORM_ADMIN_PASSWORD
    })
    if resp.status_code != 200:
        pytest.skip(f"Platform admin login failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.skip(f"No token in platform admin login response: {data}")
    return token


def make_headers(token, org_id=None):
    """Build auth headers with optional org context"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if org_id:
        headers["X-Organization-ID"] = org_id
    return headers


# ==================== TEST 1: Starter blocked from Payroll ====================

class TestStarterPayrollBlocked:
    """Test 1: Starter org cannot access payroll endpoints"""

    def test_starter_payroll_records_returns_403(self, starter_token):
        """GET /api/hr/payroll/records with starter plan should return 403"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}: {resp.text[:300]}"

    def test_starter_payroll_403_has_correct_error_structure(self, starter_token):
        """Response must have detail.error='feature_not_available'"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        assert resp.status_code == 403
        data = resp.json()
        print(f"  Response JSON: {data}")
        detail = data.get("detail")
        assert detail is not None, "Response must have 'detail' field"
        assert isinstance(detail, dict), f"detail must be dict, got {type(detail)}: {detail}"
        assert detail.get("error") == "feature_not_available", f"Expected error=feature_not_available, got: {detail}"

    def test_starter_payroll_403_has_feature_field(self, starter_token):
        """detail must contain feature='Payroll'"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        detail = resp.json().get("detail", {})
        feature = detail.get("feature")
        print(f"  feature field: {feature}")
        assert feature == "Payroll", f"Expected feature='Payroll', got: {feature}"

    def test_starter_payroll_403_has_current_plan_starter(self, starter_token):
        """detail must contain current_plan='starter'"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        detail = resp.json().get("detail", {})
        current_plan = detail.get("current_plan")
        print(f"  current_plan: {current_plan}")
        assert current_plan == "starter", f"Expected current_plan='starter', got: {current_plan}"

    def test_starter_payroll_403_has_required_plan_professional(self, starter_token):
        """detail must contain required_plan='professional'"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        detail = resp.json().get("detail", {})
        required_plan = detail.get("required_plan")
        print(f"  required_plan: {required_plan}")
        assert required_plan == "professional", f"Expected required_plan='professional', got: {required_plan}"


# ==================== TEST 2: Professional can access Payroll ====================

class TestProfessionalPayrollAllowed:
    """Test 2: Professional org can access payroll endpoints"""

    def test_professional_payroll_records_returns_200(self, professional_token):
        """GET /api/hr/payroll/records with professional plan should return 200"""
        headers = make_headers(professional_token)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}: {resp.text[:300]}"

    def test_professional_payroll_200_has_data_field(self, professional_token):
        """Response should have 'data' field (pagination response)"""
        headers = make_headers(professional_token)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        print(f"  Response keys: {list(data.keys())}")
        assert "data" in data, f"Expected 'data' field in response, got: {list(data.keys())}"
        assert "pagination" in data, f"Expected 'pagination' field in response, got: {list(data.keys())}"


# ==================== TEST 3: Frontend UpgradeModal (code review) ====================

class TestFrontendUpgradeModal:
    """Test 3: Verify frontend files exist and have correct implementation"""

    def test_upgrade_modal_file_exists(self):
        """UpgradeModal.jsx should exist"""
        import os
        path = "/app/frontend/src/components/UpgradeModal.jsx"
        assert os.path.exists(path), f"UpgradeModal.jsx not found at {path}"

    def test_upgrade_modal_listens_to_feature_not_available_event(self):
        """UpgradeModal must listen for 'feature_not_available' custom event"""
        with open("/app/frontend/src/components/UpgradeModal.jsx") as f:
            content = f.read()
        assert 'feature_not_available' in content, "UpgradeModal must listen for 'feature_not_available' event"
        assert 'window.addEventListener' in content, "UpgradeModal must use window.addEventListener"

    def test_api_js_file_exists(self):
        """api.js should exist"""
        import os
        path = "/app/frontend/src/utils/api.js"
        assert os.path.exists(path), f"api.js not found at {path}"

    def test_api_js_dispatches_custom_event_on_403(self):
        """apiFetch in api.js must dispatch CustomEvent 'feature_not_available' on 403"""
        with open("/app/frontend/src/utils/api.js") as f:
            content = f.read()
        assert 'response.status === 403' in content or 'status === 403' in content, \
            "api.js must check for 403 status"
        assert 'dispatchEvent' in content, "api.js must call dispatchEvent"
        assert 'CustomEvent' in content, "api.js must dispatch CustomEvent"
        assert 'feature_not_available' in content, "api.js must dispatch 'feature_not_available' event"
        assert 'detail.error === "feature_not_available"' in content or \
               "detail.error === 'feature_not_available'" in content or \
               'detail?.error' in content, "api.js must check detail.error before dispatching"

    def test_upgrade_modal_has_testid_attributes(self):
        """UpgradeModal must have data-testid attributes"""
        with open("/app/frontend/src/components/UpgradeModal.jsx") as f:
            content = f.read()
        assert 'data-testid="upgrade-modal"' in content or "data-testid='upgrade-modal'" in content, \
            "UpgradeModal must have data-testid='upgrade-modal'"
        assert 'data-testid="upgrade-modal-close"' in content or "data-testid='upgrade-modal-close'" in content, \
            "UpgradeModal must have data-testid='upgrade-modal-close'"


# ==================== TEST 4: Platform Admin Plan Change ====================

class TestPlatformAdminPlanChange:
    """Test 4: Platform admin can list orgs and change org plan"""

    def test_platform_admin_can_list_organizations(self, platform_admin_token):
        """GET /api/platform/organizations should return list"""
        headers = make_headers(platform_admin_token)
        resp = requests.get(f"{BASE_URL}/api/v1/platform/organizations", headers=headers)
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}: {resp.text[:300]}"
        data = resp.json()
        assert "organizations" in data, f"Expected 'organizations' key, got: {list(data.keys())}"
        assert isinstance(data["organizations"], list), "organizations must be a list"
        print(f"  Found {len(data['organizations'])} organizations")

    def test_platform_admin_can_upgrade_org_to_professional(self, platform_admin_token, starter_token):
        """PUT /api/platform/organizations/org_9c74befbaa95/plan to professional should succeed"""
        headers = make_headers(platform_admin_token)
        resp = requests.put(
            f"{BASE_URL}/api/v1/platform/organizations/{STARTER_ORG}/plan",
            json={"plan_type": "professional"},
            headers=headers
        )
        print(f"  Upgrade status: {resp.status_code}")
        print(f"  Upgrade body: {resp.text[:300]}")
        assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}: {resp.text[:300]}"
        data = resp.json()
        assert data.get("success") is True, f"Expected success=True, got: {data}"

    def test_upgraded_org_can_access_payroll(self, platform_admin_token, starter_token):
        """After upgrading to professional, payroll should be accessible"""
        # First upgrade
        platform_headers = make_headers(platform_admin_token)
        requests.put(
            f"{BASE_URL}/api/v1/platform/organizations/{STARTER_ORG}/plan",
            json={"plan_type": "professional"},
            headers=platform_headers
        )
        
        # Now test payroll access
        starter_headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=starter_headers)
        print(f"  Payroll status after upgrade: {resp.status_code}")
        print(f"  Payroll body: {resp.text[:300]}")
        assert resp.status_code == 200, f"Expected 200 after plan upgrade, got {resp.status_code}: {resp.text[:300]}"

    def test_revert_org_to_starter_after_test(self, platform_admin_token, starter_token):
        """CLEANUP: Revert org_9c74befbaa95 back to starter plan"""
        platform_headers = make_headers(platform_admin_token)
        resp = requests.put(
            f"{BASE_URL}/api/v1/platform/organizations/{STARTER_ORG}/plan",
            json={"plan_type": "starter"},
            headers=platform_headers
        )
        print(f"  Revert to starter status: {resp.status_code}")
        print(f"  Revert body: {resp.text[:300]}")
        assert resp.status_code == 200, f"Failed to revert to starter: {resp.text[:300]}"
        # Verify it's back to starter (payroll should be blocked again)
        starter_headers = make_headers(starter_token, STARTER_ORG)
        payroll_resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=starter_headers)
        print(f"  Payroll after revert: {payroll_resp.status_code}")
        assert payroll_resp.status_code == 403, f"Expected 403 after reverting to starter, got {payroll_resp.status_code}"


# ==================== TEST 5: Starter blocked from Projects ====================

class TestStarterProjectsBlocked:
    """Test 5: Starter org cannot access Projects module"""

    def test_starter_projects_returns_403(self, starter_token):
        """GET /api/projects with starter plan should return 403"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/projects", headers=headers)
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}: {resp.text[:300]}"

    def test_starter_projects_403_has_feature_not_available(self, starter_token):
        """Projects 403 must have feature_not_available error"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/projects", headers=headers)
        assert resp.status_code == 403
        data = resp.json()
        detail = data.get("detail", {})
        print(f"  detail: {detail}")
        assert isinstance(detail, dict), f"detail must be dict, got: {detail}"
        assert detail.get("error") == "feature_not_available", f"Expected feature_not_available, got: {detail}"

    def test_starter_projects_blocked_feature_is_project_management(self, starter_token):
        """Projects 403 must indicate project_management feature key"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/v1/projects", headers=headers)
        detail = resp.json().get("detail", {})
        feature_key = detail.get("feature_key")
        print(f"  feature_key: {feature_key}")
        assert feature_key == "project_management", f"Expected feature_key='project_management', got: {feature_key}"


# ==================== TEST 6: EFI allowed on Starter ====================

class TestStarterEFIAllowed:
    """Test 6: EFI Intelligence is allowed on Starter plan"""

    def test_starter_efi_failure_cards_not_403(self, starter_token):
        """GET /api/efi/failure-cards with starter plan should NOT return 403"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/efi/failure-cards", headers=headers)
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        assert resp.status_code != 403, \
            f"Starter should be allowed EFI access but got 403: {resp.text[:300]}"

    def test_starter_efi_failure_cards_returns_2xx_or_404(self, starter_token):
        """GET /api/efi/failure-cards should return 200 (or 404 if empty)"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/efi/failure-cards", headers=headers)
        # Accept 200 (success) or 404 (no data) but not 403 (blocked)
        assert resp.status_code in [200, 201, 404], \
            f"Expected 200/404 for EFI on starter, got {resp.status_code}: {resp.text[:300]}"
        print(f"  EFI allowed, returned {resp.status_code}")


# ==================== TEST 7: Advanced Reports allowed on Starter ====================

class TestStarterAdvancedReportsAllowed:
    """Test 7: Advanced Reports is allowed on Starter plan"""

    def test_starter_profit_loss_report_not_403(self, starter_token):
        """GET /api/reports/profit-loss with starter plan should NOT return 403"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/reports/profit-loss", headers=headers)
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        assert resp.status_code != 403, \
            f"Starter should be allowed Advanced Reports but got 403: {resp.text[:300]}"

    def test_starter_profit_loss_returns_200_or_other_non_403(self, starter_token):
        """GET /api/reports/profit-loss should return 200 (or other non-403)"""
        headers = make_headers(starter_token, STARTER_ORG)
        resp = requests.get(f"{BASE_URL}/api/reports/profit-loss", headers=headers)
        # Accept 200, 201, 400 (bad params), 404 (no data), 500 - just not 403
        assert resp.status_code in [200, 201, 400, 404, 500], \
            f"Expected non-403 for Advanced Reports on starter, got {resp.status_code}: {resp.text[:300]}"
        print(f"  Advanced Reports allowed, returned {resp.status_code}")


# ==================== TEST 8: Battwheels Garages Professional - All Access ====================

class TestBattwheelsGaragesProfessionalAllAccess:
    """Test 8: admin@battwheels.in (Professional) can access all features"""

    def test_professional_payroll_accessible(self, professional_token):
        """Payroll should return 200 for professional org"""
        headers = make_headers(professional_token)
        resp = requests.get(f"{BASE_URL}/api/v1/hr/payroll/records", headers=headers)
        print(f"  Payroll status: {resp.status_code}")
        assert resp.status_code == 200, f"Expected 200 for payroll, got {resp.status_code}: {resp.text[:300]}"

    def test_professional_projects_accessible(self, professional_token):
        """Projects should NOT return 403 for professional org"""
        headers = make_headers(professional_token)
        resp = requests.get(f"{BASE_URL}/api/v1/projects", headers=headers)
        print(f"  Projects status: {resp.status_code}")
        assert resp.status_code != 403, \
            f"Professional should access projects but got 403: {resp.text[:300]}"

    def test_professional_advanced_reports_accessible(self, professional_token):
        """Advanced Reports should NOT return 403 for professional org"""
        headers = make_headers(professional_token)
        resp = requests.get(f"{BASE_URL}/api/reports/profit-loss", headers=headers)
        print(f"  Advanced Reports status: {resp.status_code}")
        assert resp.status_code != 403, \
            f"Professional should access advanced reports but got 403: {resp.text[:300]}"

    def test_professional_efi_accessible(self, professional_token):
        """EFI should NOT return 403 for professional org"""
        headers = make_headers(professional_token)
        resp = requests.get(f"{BASE_URL}/api/efi/failure-cards", headers=headers)
        print(f"  EFI status: {resp.status_code}")
        assert resp.status_code != 403, \
            f"Professional should access EFI but got 403: {resp.text[:300]}"
