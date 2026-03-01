"""
Comprehensive AMC (Annual Maintenance Contracts) Endpoint Tests
================================================================
Tests for all /api/v1/amc/* endpoints.
Uses shared conftest.py fixtures (base_url, dev_headers).

Run: pytest backend/tests/test_amc_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid


@pytest.fixture(scope="module")
def _headers(base_url):
    """Auth headers with org context for AMC (requires role=admin)."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "DevTest@123",
    })
    assert resp.status_code == 200, f"AMC admin login failed: {resp.text}"
    token = resp.json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "dev-internal-testing-001",
        "Content-Type": "application/json",
    }


PREFIX = "/api/v1/amc"


# ==================== 1. AMC PLANS - CRUD ====================

class TestAMCPlanCreate:

    PLAN_NAME = f"Test Plan {uuid.uuid4().hex[:6]}"

    @pytest.fixture(scope="class")
    def created_plan(self, base_url, _headers):
        resp = requests.post(f"{base_url}{PREFIX}/plans", headers=_headers, json={
            "name": self.PLAN_NAME,
            "description": "Comprehensive test plan",
            "tier": "starter",
            "vehicle_category": "2W",
            "billing_frequency": "monthly",
            "duration_months": 12,
            "price": 999.0,
            "max_service_visits": 4,
        })
        assert resp.status_code == 200, f"Plan creation failed: {resp.text}"
        return resp.json()

    def test_create_plan_returns_id(self, created_plan):
        assert "plan_id" in created_plan or "id" in created_plan

    def test_create_plan_has_name(self, created_plan):
        assert created_plan.get("name") == self.PLAN_NAME


class TestAMCPlanList:

    def test_list_plans(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/plans", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        plans = data if isinstance(data, list) else data.get("plans", data.get("data", []))
        assert isinstance(plans, list)

    def test_list_plans_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}{PREFIX}/plans")
        assert resp.status_code in [401, 403]


class TestAMCPlanGetUpdate:

    @pytest.fixture(scope="class")
    def _plan_id(self, base_url, _headers):
        """Create a plan and return its ID."""
        resp = requests.post(f"{base_url}{PREFIX}/plans", headers=_headers, json={
            "name": f"Detail Plan {uuid.uuid4().hex[:6]}",
            "tier": "fleet_essential",
            "vehicle_category": "3W",
            "billing_frequency": "annual",
            "duration_months": 12,
            "price": 5999.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        return data.get("plan_id") or data.get("id")

    def test_get_plan(self, base_url, _headers, _plan_id):
        resp = requests.get(f"{base_url}{PREFIX}/plans/{_plan_id}", headers=_headers)
        assert resp.status_code == 200

    def test_get_nonexistent_plan_404(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/plans/nonexistent-plan-xyz", headers=_headers)
        assert resp.status_code == 404

    def test_update_plan(self, base_url, _headers, _plan_id):
        resp = requests.put(f"{base_url}{PREFIX}/plans/{_plan_id}", headers=_headers, json={
            "price": 6999.0,
            "description": "Updated by test"
        })
        assert resp.status_code == 200

    def test_deactivate_plan(self, base_url, _headers, _plan_id):
        resp = requests.delete(f"{base_url}{PREFIX}/plans/{_plan_id}", headers=_headers)
        assert resp.status_code == 200


# ==================== 2. AMC SUBSCRIPTIONS ====================

class TestAMCSubscriptions:

    @pytest.fixture(scope="class")
    def _plan_id(self, base_url, _headers):
        resp = requests.post(f"{base_url}{PREFIX}/plans", headers=_headers, json={
            "name": f"Sub Plan {uuid.uuid4().hex[:6]}",
            "tier": "starter",
            "vehicle_category": "2W",
            "price": 499.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        return data.get("plan_id") or data.get("id")

    @pytest.fixture(scope="class")
    def created_sub(self, base_url, _headers, _plan_id):
        resp = requests.post(f"{base_url}{PREFIX}/subscriptions", headers=_headers, json={
            "plan_id": _plan_id,
            "customer_id": "user_aea4696a9fa8",
            "vehicle_id": "veh_30c1bd83046a",
            "amount_paid": 499.0,
            "payment_status": "paid",
        })
        assert resp.status_code == 200, f"Sub creation failed: {resp.text}"
        return resp.json()

    def test_create_subscription(self, created_sub):
        assert "subscription_id" in created_sub or "id" in created_sub

    def test_list_subscriptions(self, base_url, _headers, created_sub):
        resp = requests.get(f"{base_url}{PREFIX}/subscriptions", headers=_headers)
        assert resp.status_code == 200

    def test_get_subscription(self, base_url, _headers, created_sub):
        sub_id = created_sub.get("subscription_id") or created_sub.get("id")
        resp = requests.get(f"{base_url}{PREFIX}/subscriptions/{sub_id}", headers=_headers)
        assert resp.status_code == 200

    def test_get_nonexistent_subscription_404(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/subscriptions/nonexistent-sub-xyz", headers=_headers)
        assert resp.status_code == 404

    def test_record_service_usage(self, base_url, _headers, created_sub):
        sub_id = created_sub.get("subscription_id") or created_sub.get("id")
        resp = requests.put(f"{base_url}{PREFIX}/subscriptions/{sub_id}/use-service", headers=_headers)
        assert resp.status_code == 200

    def test_cancel_subscription(self, base_url, _headers, created_sub):
        sub_id = created_sub.get("subscription_id") or created_sub.get("id")
        resp = requests.put(f"{base_url}{PREFIX}/subscriptions/{sub_id}/cancel", headers=_headers)
        assert resp.status_code == 200


# ==================== 3. AMC ANALYTICS ====================

class TestAMCAnalytics:

    def test_get_analytics(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/analytics", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


# ==================== 4. PLANS BY CATEGORY ====================

class TestPlansByCategory:

    def test_plans_by_category(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/plans-by-category", headers=_headers)
        assert resp.status_code == 200

    def test_plans_by_category_filter(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/plans-by-category?vehicle_category=2W", headers=_headers)
        assert resp.status_code == 200
