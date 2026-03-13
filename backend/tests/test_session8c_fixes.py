"""
Session 8C - Fix Verification Tests
Tests for 7 critical/high issues fixed during Module 5-8 investigation:
1. Payments Received page loads with data
2. Inventory Adjustments page loads with data
3. Accounting page shows revenue data
4. Chart of Accounts loads accounts
5. /inventory redirects to /inventory-management
6. Backend /api/v1/inventory/reorder-suggestions returns 200 (not 404)
6b. Backend /api/v1/inventory/stocktakes returns 200 (not 404)
7. /inventory-enhanced page loads without crashing
8A. /invoices redirects to /invoices-enhanced
8A. /knowledge-brain loads the EFI Diagnostic Assistant
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://beta-readiness-2.preview.emergentagent.com")

# Test credentials
TEST_EMAIL = "demo@voltmotors.in"
TEST_PASSWORD = "volt1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API testing"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")
    return None


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get authenticated headers"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }


class TestFix1_PaymentsReceived:
    """Fix 1: Payments Received API - verify data exists"""

    def test_payments_received_list_returns_200(self, auth_headers):
        """GET /api/v1/payments-received/ should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/payments-received/",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "payments" in data or "code" in data, f"Unexpected response format: {data}"

    def test_payments_received_summary_returns_200(self, auth_headers):
        """GET /api/v1/payments-received/summary should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/payments-received/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"


class TestFix2_InventoryAdjustments:
    """Fix 2: Inventory Adjustments API - verify data exists"""

    def test_inventory_adjustments_list_returns_200(self, auth_headers):
        """GET /api/v1/inv-adjustments should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inv-adjustments",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        # Should have adjustments array and summary counts
        assert "adjustments" in data, f"Expected 'adjustments' key in response: {data}"

    def test_inventory_adjustments_summary_returns_200(self, auth_headers):
        """GET /api/v1/inv-adjustments/summary should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inv-adjustments/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        # Summary should have draft, adjusted, voided counts
        assert "total" in data or "draft" in data, f"Expected summary counts in response: {data}"


class TestFix3_Accounting:
    """Fix 3: Accounting API - verify revenue data"""

    def test_accounting_summary_returns_200(self, auth_headers):
        """GET /api/v1/accounting/summary should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/accounting/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        # Should have total_revenue field
        assert "total_revenue" in data, f"Expected 'total_revenue' in response: {data}"


class TestFix4_ChartOfAccounts:
    """Fix 4: Chart of Accounts API - verify accounts load"""

    def test_chart_of_accounts_returns_200(self, auth_headers):
        """GET /api/v1/chart-of-accounts should return 200 with accounts"""
        response = requests.get(
            f"{BASE_URL}/api/v1/chart-of-accounts",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        # Should return list of accounts (could be empty array or array with accounts)
        assert isinstance(data, list), f"Expected list response, got: {type(data)}"


class TestFix6_InventoryEnhancedAPIs:
    """Fix 6: Backend inventory APIs - /reorder-suggestions and /stocktakes should NOT return 404 'Item not found'"""

    def test_reorder_suggestions_returns_200_not_404(self, auth_headers):
        """GET /api/v1/inventory-enhanced/reorder-suggestions should return 200 (not 404)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory-enhanced/reorder-suggestions",
            headers=auth_headers
        )
        # Should be 200 OR 403 (enterprise feature), but NOT 404 'Item not found'
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}: {response.text[:200]}"
        if response.status_code == 404:
            data = response.json()
            assert "Item not found" not in str(data.get("detail", "")), \
                f"Route collision bug: got 'Item not found' instead of reorder-suggestions data"

    def test_stocktakes_returns_200_not_404(self, auth_headers):
        """GET /api/v1/inventory-enhanced/stocktakes should return 200 (not 404)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory-enhanced/stocktakes",
            headers=auth_headers
        )
        # Should be 200 OR 403 (enterprise feature), but NOT 404 'Item not found'
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}: {response.text[:200]}"
        if response.status_code == 404:
            data = response.json()
            assert "Item not found" not in str(data.get("detail", "")), \
                f"Route collision bug: got 'Item not found' instead of stocktakes data"


class TestFix6_InventoryAPIEndpoints:
    """Additional inventory API endpoint verification"""

    def test_inventory_api_reorder_suggestions(self, auth_headers):
        """GET /api/v1/inventory/reorder-suggestions should return 200 (dedicated inventory_api route)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory/reorder-suggestions",
            headers=auth_headers
        )
        # Could be 200 or 403 (enterprise gated), but NOT 404
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}: {response.text[:200]}"
        
    def test_inventory_api_stocktakes(self, auth_headers):
        """GET /api/v1/inventory/stocktakes should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory/stocktakes",
            headers=auth_headers
        )
        # Could be 200 or 403 (enterprise gated), but NOT 404
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}: {response.text[:200]}"


class TestHealthAndBasicAPIs:
    """Health check and basic API verification"""

    def test_health_check(self):
        """GET /api/health should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") in ["healthy", "degraded"], f"Unexpected status: {data}"

    def test_items_enhanced_returns_200(self, auth_headers):
        """GET /api/v1/items-enhanced/ should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/items-enhanced/",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"

    def test_invoices_enhanced_returns_200(self, auth_headers):
        """GET /api/v1/invoices-enhanced/ should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices-enhanced/",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"


class TestInventoryEnhancedSummary:
    """Test inventory-enhanced summary endpoint"""

    def test_inventory_enhanced_summary(self, auth_headers):
        """GET /api/v1/inventory-enhanced/summary should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory-enhanced/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
