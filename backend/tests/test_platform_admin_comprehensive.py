"""
Comprehensive Platform Admin Endpoint Tests
=============================================
Tests for all /api/v1/platform/* endpoints.
Uses shared conftest.py fixtures.
Platform admin tests use admin_headers (platform-admin@battwheels.in).

Run: pytest backend/tests/test_platform_admin_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid


# ==================== HELPERS ====================

@pytest.fixture(scope="module")
def _admin_h(base_url, admin_token):
    """Admin headers for platform admin endpoints."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def _demo_h(base_url, demo_token):
    """Demo user headers (non-admin, for 403 tests)."""
    return {
        "Authorization": f"Bearer {demo_token}",
        "Content-Type": "application/json",
    }


PREFIX = "/api/v1/platform"


# ==================== 1. LIST ORGANIZATIONS ====================

class TestListOrganizations:

    def test_list_orgs_as_admin(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/organizations", headers=_admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "organizations" in data
        assert "total" in data
        assert isinstance(data["organizations"], list)

    def test_list_orgs_pagination(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/organizations?page=1&limit=5", headers=_admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 5
        assert "total_pages" in data

    def test_list_orgs_search(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/organizations?search=volt", headers=_admin_h)
        assert resp.status_code == 200

    def test_list_orgs_filter_by_plan(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/organizations?plan=free", headers=_admin_h)
        assert resp.status_code == 200

    def test_list_orgs_regular_user_403(self, base_url, _demo_h):
        resp = requests.get(f"{base_url}{PREFIX}/organizations", headers=_demo_h)
        assert resp.status_code == 403

    def test_list_orgs_no_auth_401(self, base_url):
        resp = requests.get(f"{base_url}{PREFIX}/organizations")
        assert resp.status_code in [401, 403]


# ==================== 2. GET ORGANIZATION DETAIL ====================

class TestGetOrganizationDetail:

    def test_get_org_detail(self, base_url, _admin_h):
        # First get an org id
        resp = requests.get(f"{base_url}{PREFIX}/organizations?limit=1", headers=_admin_h)
        assert resp.status_code == 200
        orgs = resp.json().get("organizations", [])
        if not orgs:
            pytest.skip("No organizations to test detail view")
        org_id = orgs[0]["organization_id"]
        resp2 = requests.get(f"{base_url}{PREFIX}/organizations/{org_id}", headers=_admin_h)
        assert resp2.status_code == 200
        detail = resp2.json()
        assert "member_count" in detail
        assert "members" in detail
        assert "status" in detail

    def test_get_org_nonexistent_404(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/organizations/nonexistent-org-xyz", headers=_admin_h)
        assert resp.status_code == 404


# ==================== 3. SUSPEND / ACTIVATE ORG ====================

class TestSuspendActivateOrg:

    @pytest.fixture(scope="class")
    def _test_org_id(self, base_url, _admin_h):
        """Find a non-production org to suspend/activate."""
        resp = requests.get(f"{base_url}{PREFIX}/organizations?search=volt&limit=1", headers=_admin_h)
        orgs = resp.json().get("organizations", [])
        if not orgs:
            pytest.skip("No org found for suspend/activate test")
        return orgs[0]["organization_id"]

    def test_suspend_org(self, base_url, _admin_h, _test_org_id):
        resp = requests.post(f"{base_url}{PREFIX}/organizations/{_test_org_id}/suspend", headers=_admin_h)
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_activate_org(self, base_url, _admin_h, _test_org_id):
        resp = requests.post(f"{base_url}{PREFIX}/organizations/{_test_org_id}/activate", headers=_admin_h)
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_suspend_nonexistent_404(self, base_url, _admin_h):
        resp = requests.post(f"{base_url}{PREFIX}/organizations/nonexistent-xyz/suspend", headers=_admin_h)
        assert resp.status_code == 404


# ==================== 4. CHANGE ORG PLAN ====================

class TestChangeOrgPlan:

    @pytest.fixture(scope="class")
    def _test_org_id(self, base_url, _admin_h):
        """Use dev-internal-testing-001 for plan tests (not demo org)."""
        return "dev-internal-testing-001"

    @pytest.fixture(scope="class")
    def _original_plan(self, base_url, _admin_h, _test_org_id):
        """Capture the original plan to restore after test."""
        resp = requests.get(f"{base_url}{PREFIX}/organizations/{_test_org_id}", headers=_admin_h)
        if resp.status_code == 200:
            return resp.json().get("subscription", {}).get("plan_code", "professional")
        return "professional"

    def test_change_plan(self, base_url, _admin_h, _test_org_id):
        resp = requests.put(
            f"{base_url}{PREFIX}/organizations/{_test_org_id}/plan",
            headers=_admin_h,
            json={"plan_type": "enterprise"}
        )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_change_plan_invalid(self, base_url, _admin_h, _test_org_id):
        resp = requests.put(
            f"{base_url}{PREFIX}/organizations/{_test_org_id}/plan",
            headers=_admin_h,
            json={"plan_type": "invalid_plan"}
        )
        assert resp.status_code == 400

    def test_change_plan_nonexistent_org(self, base_url, _admin_h):
        resp = requests.put(
            f"{base_url}{PREFIX}/organizations/nonexistent-xyz/plan",
            headers=_admin_h,
            json={"plan_type": "free"}
        )
        assert resp.status_code == 404

    def test_change_plan_restore(self, base_url, _admin_h, _test_org_id, _original_plan):
        """Restore plan after test."""
        resp = requests.put(
            f"{base_url}{PREFIX}/organizations/{_test_org_id}/plan",
            headers=_admin_h,
            json={"plan_type": _original_plan}
        )
        assert resp.status_code == 200


# ==================== 5. PLATFORM METRICS ====================

class TestPlatformMetrics:

    def test_get_metrics(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/metrics", headers=_admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_organizations" in data
        assert "active_organizations" in data
        assert "total_users" in data
        assert "organizations_by_plan" in data
        assert "monthly_signups" in data

    def test_metrics_requires_admin(self, base_url, _demo_h):
        resp = requests.get(f"{base_url}{PREFIX}/metrics", headers=_demo_h)
        assert resp.status_code == 403


# ==================== 6. REVENUE HEALTH ====================

class TestRevenueHealth:

    def test_get_revenue_health(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/revenue-health", headers=_admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_mrr" in data
        assert "mrr_by_plan" in data
        assert "trial_pipeline" in data
        assert "churn_risk" in data
        assert "recent_signups" in data


# ==================== 7. ACTIVITY & AUDIT ====================

class TestActivityAndAudit:

    def test_get_activity(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/activity", headers=_admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "runs" in data

    def test_get_audit_status(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/audit-status", headers=_admin_h)
        assert resp.status_code == 200


# ==================== 8. ENVIRONMENT ====================

class TestEnvironment:

    def test_get_environment(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/environment", headers=_admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "environment" in data
        assert data["environment"] in ["development", "staging", "production"]


# ==================== 9. LEADS ====================

class TestLeads:

    def test_list_leads(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/leads", headers=_admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "leads" in data
        assert "summary" in data
        assert "total" in data["summary"]

    def test_list_leads_filter_status(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/leads?status=new", headers=_admin_h)
        assert resp.status_code == 200

    def test_update_lead_status_nonexistent(self, base_url, _admin_h):
        resp = requests.patch(
            f"{base_url}{PREFIX}/leads/nonexistent-lead/status",
            headers=_admin_h,
            json={"status": "called"}
        )
        assert resp.status_code == 404

    def test_update_lead_notes_nonexistent(self, base_url, _admin_h):
        resp = requests.patch(
            f"{base_url}{PREFIX}/leads/nonexistent-lead/notes",
            headers=_admin_h,
            json={"notes": "Test notes"}
        )
        assert resp.status_code == 404


# ==================== 10. FEATURE FLAGS ====================

class TestFeatureFlags:

    UNIQUE_KEY = f"test_flag_{uuid.uuid4().hex[:8]}"

    def test_list_feature_flags(self, base_url, _admin_h):
        resp = requests.get(f"{base_url}{PREFIX}/feature-flags", headers=_admin_h)
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_create_feature_flag(self, base_url, _admin_h):
        resp = requests.post(
            f"{base_url}{PREFIX}/feature-flags",
            headers=_admin_h,
            json={
                "feature_key": self.UNIQUE_KEY,
                "name": "Test Flag",
                "description": "Created by test",
                "status": "off",
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature_key"] == self.UNIQUE_KEY

    def test_create_duplicate_feature_flag_409(self, base_url, _admin_h):
        resp = requests.post(
            f"{base_url}{PREFIX}/feature-flags",
            headers=_admin_h,
            json={
                "feature_key": self.UNIQUE_KEY,
                "name": "Dup Flag",
            }
        )
        assert resp.status_code == 409

    def test_update_feature_flag(self, base_url, _admin_h):
        resp = requests.put(
            f"{base_url}{PREFIX}/feature-flags/{self.UNIQUE_KEY}",
            headers=_admin_h,
            json={"status": "on", "name": "Updated Flag"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "on"

    def test_update_nonexistent_flag_404(self, base_url, _admin_h):
        resp = requests.put(
            f"{base_url}{PREFIX}/feature-flags/nonexistent_key",
            headers=_admin_h,
            json={"status": "on"}
        )
        assert resp.status_code == 404

    def test_delete_feature_flag(self, base_url, _admin_h):
        resp = requests.delete(
            f"{base_url}{PREFIX}/feature-flags/{self.UNIQUE_KEY}",
            headers=_admin_h,
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] == self.UNIQUE_KEY

    def test_delete_nonexistent_flag_404(self, base_url, _admin_h):
        resp = requests.delete(
            f"{base_url}{PREFIX}/feature-flags/nonexistent_key",
            headers=_admin_h,
        )
        assert resp.status_code == 404


# ==================== 11. VERSION (PUBLIC) ====================

class TestVersion:

    def test_get_version(self, base_url):
        """Version endpoint is public — no auth required."""
        resp = requests.get(f"{base_url}{PREFIX}/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
