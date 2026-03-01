"""
Comprehensive Sales Orders Endpoint Tests
===========================================
Tests for all /api/v1/sales-orders-enhanced/* endpoints.
Uses shared conftest.py fixtures (base_url, dev_headers).

Run: pytest backend/tests/test_sales_orders_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid


@pytest.fixture(scope="module")
def _headers(base_url, dev_token):
    """Auth headers with org context for sales orders."""
    return {
        "Authorization": f"Bearer {dev_token}",
        "X-Organization-ID": "dev-internal-testing-001",
        "Content-Type": "application/json",
    }


PREFIX = "/api/v1/sales-orders-enhanced"


# ==================== HELPERS ====================

@pytest.fixture(scope="module")
def created_order(base_url, _headers):
    """Create a sales order for testing."""
    resp = requests.post(f"{base_url}{PREFIX}/", headers=_headers, json={
        "customer_id": "test-customer-001",
        "date": "2026-03-01",
        "expected_shipment_date": "2026-03-15",
        "notes": "Test sales order",
        "line_items": [
            {
                "name": "Test Item",
                "quantity": 2,
                "rate": 500.0,
                "tax_percentage": 18.0,
            }
        ],
    })
    assert resp.status_code in [200, 201], f"Order creation failed: {resp.text}"
    return resp.json()


def _get_order_id(order_data):
    return order_data.get("salesorder_id") or order_data.get("id") or order_data.get("data", {}).get("salesorder_id")


# ==================== 1. SETTINGS ====================

class TestSettings:

    def test_get_settings(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/settings", headers=_headers)
        assert resp.status_code == 200


# ==================== 2. CREATE SALES ORDER ====================

class TestCreateSalesOrder:

    def test_create_order(self, created_order):
        order_id = _get_order_id(created_order)
        assert order_id is not None

    def test_create_order_requires_auth(self, base_url):
        resp = requests.post(f"{base_url}{PREFIX}/", json={
            "customer_id": "test",
            "line_items": [{"name": "x", "quantity": 1, "rate": 100}],
        })
        assert resp.status_code in [401, 403]


# ==================== 3. LIST SALES ORDERS ====================

class TestListSalesOrders:

    def test_list_orders(self, base_url, _headers, created_order):
        resp = requests.get(f"{base_url}{PREFIX}/", headers=_headers)
        assert resp.status_code == 200

    def test_list_orders_with_filters(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/?status=draft", headers=_headers)
        assert resp.status_code == 200


# ==================== 4. GET SINGLE ORDER ====================

class TestGetSalesOrder:

    def test_get_order(self, base_url, _headers, created_order):
        order_id = _get_order_id(created_order)
        resp = requests.get(f"{base_url}{PREFIX}/{order_id}", headers=_headers)
        assert resp.status_code == 200

    def test_get_nonexistent_order(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/SO-NONEXISTENT", headers=_headers)
        assert resp.status_code == 404


# ==================== 5. UPDATE ORDER ====================

class TestUpdateSalesOrder:

    def test_update_order(self, base_url, _headers, created_order):
        order_id = _get_order_id(created_order)
        resp = requests.put(f"{base_url}{PREFIX}/{order_id}", headers=_headers, json={
            "notes": "Updated by test",
            "shipping_charge": 100.0,
        })
        assert resp.status_code == 200


# ==================== 6. SUMMARY ====================

class TestSalesOrderSummary:

    def test_get_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/summary", headers=_headers)
        assert resp.status_code == 200


# ==================== 7. STATUS UPDATES ====================

class TestStatusUpdates:

    @pytest.fixture(scope="class")
    def _order_id(self, base_url, _headers):
        """Create a fresh order for status tests."""
        resp = requests.post(f"{base_url}{PREFIX}/", headers=_headers, json={
            "customer_id": "test-customer-001",
            "date": "2026-03-01",
            "line_items": [{"name": "Status Item", "quantity": 1, "rate": 100.0}],
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        return _get_order_id(data)

    def test_confirm_order(self, base_url, _headers, _order_id):
        resp = requests.post(f"{base_url}{PREFIX}/{_order_id}/confirm", headers=_headers)
        assert resp.status_code == 200

    def test_void_order(self, base_url, _headers):
        """Create and void a separate order."""
        resp = requests.post(f"{base_url}{PREFIX}/", headers=_headers, json={
            "customer_id": "test-customer-001",
            "date": "2026-03-01",
            "line_items": [{"name": "Void Item", "quantity": 1, "rate": 50.0}],
        })
        assert resp.status_code in [200, 201]
        oid = _get_order_id(resp.json())
        resp2 = requests.post(f"{base_url}{PREFIX}/{oid}/void", headers=_headers)
        assert resp2.status_code == 200


# ==================== 8. CLONE ====================

class TestCloneOrder:

    def test_clone_order(self, base_url, _headers, created_order):
        order_id = _get_order_id(created_order)
        resp = requests.post(f"{base_url}{PREFIX}/{order_id}/clone", headers=_headers)
        assert resp.status_code == 200


# ==================== 9. REPORTS ====================

class TestSalesOrderReports:

    def test_report_by_status(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/reports/by-status", headers=_headers)
        assert resp.status_code == 200

    def test_report_by_customer(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/reports/by-customer", headers=_headers)
        assert resp.status_code == 200

    def test_fulfillment_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/reports/fulfillment-summary", headers=_headers)
        assert resp.status_code == 200


# ==================== 10. ACTIVITY ====================

class TestOrderActivity:

    def test_get_activity(self, base_url, _headers, created_order):
        order_id = _get_order_id(created_order)
        resp = requests.get(f"{base_url}{PREFIX}/{order_id}/activity", headers=_headers)
        assert resp.status_code == 200


# ==================== 11. DELETE ====================

class TestDeleteOrder:

    def test_delete_order(self, base_url, _headers):
        """Create and delete a separate order."""
        resp = requests.post(f"{base_url}{PREFIX}/", headers=_headers, json={
            "customer_id": "test-customer-001",
            "date": "2026-03-01",
            "line_items": [{"name": "Del Item", "quantity": 1, "rate": 25.0}],
        })
        assert resp.status_code in [200, 201]
        oid = _get_order_id(resp.json())
        resp2 = requests.delete(f"{base_url}{PREFIX}/{oid}", headers=_headers)
        assert resp2.status_code == 200

    def test_delete_nonexistent_404(self, base_url, _headers):
        resp = requests.delete(f"{base_url}{PREFIX}/SO-NONEXISTENT", headers=_headers)
        assert resp.status_code == 404
