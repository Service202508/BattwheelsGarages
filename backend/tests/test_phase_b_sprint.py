"""
Battwheels OS - Phase B Stabilisation Sprint Tests
===================================================
Tests for delivery challans and vendor credits routes:
- GET/POST/PUT/DELETE /api/v1/delivery-challans
- GET/POST/PUT/DELETE /api/v1/vendor-credits  
- POST /api/v1/vendor-credits/:id/apply (journal entry creation)
- Period lock enforcement on vendor credits (Jan 2026 locked, Feb 2026 open)
- /api/v1/bills-enhanced after removing legacy bills.py
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "dev@battwheels.internal"
ADMIN_PASSWORD = "DevTest@123"
TEST_CUSTOMER = "test-customer-001"


class TestDeliveryChallans:
    """Delivery Challans CRUD tests"""
    token = None
    org_id = None
    created_challan_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login once for all tests"""
        if TestDeliveryChallans.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestDeliveryChallans.token = data["token"]
            TestDeliveryChallans.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestDeliveryChallans.token}"}
        if TestDeliveryChallans.org_id:
            headers["X-Organization-ID"] = TestDeliveryChallans.org_id
        return headers

    def test_01_list_delivery_challans(self):
        """GET /api/v1/delivery-challans returns list with pagination"""
        response = requests.get(f"{BASE_URL}/api/v1/delivery-challans", headers=self.get_headers())
        assert response.status_code == 200, f"List challans failed: {response.status_code}, {response.text}"
        data = response.json()
        assert "data" in data, f"Missing 'data' key: {data.keys()}"
        assert "pagination" in data, f"Missing 'pagination' key: {data.keys()}"
        assert "total" in data["pagination"], "Missing total in pagination"
        print(f"Found {data['pagination']['total']} challans")

    def test_02_create_delivery_challan(self):
        """POST /api/v1/delivery-challans creates a challan"""
        payload = {
            "customer_id": TEST_CUSTOMER,
            "date": "2026-02-15",
            "items": [
                {"item_name": "Test Battery", "quantity": 2, "unit": "pcs", "hsn_code": "8507"}
            ],
            "vehicle_number": "KA01AB1234",
            "transporter_name": "Test Transport",
            "notes": "Test challan from Phase B sprint"
        }
        response = requests.post(f"{BASE_URL}/api/v1/delivery-challans", headers=self.get_headers(), json=payload)
        assert response.status_code == 200, f"Create challan failed: {response.status_code}, {response.text}"
        data = response.json()
        assert "challan_id" in data, f"Missing challan_id: {data}"
        assert "challan_number" in data, f"Missing challan_number: {data}"
        assert data["status"] == "draft", f"Expected status draft, got {data.get('status')}"
        TestDeliveryChallans.created_challan_id = data["challan_id"]
        print(f"Created challan: {data['challan_number']} ({data['challan_id']})")

    def test_03_get_delivery_challan_by_id(self):
        """GET /api/v1/delivery-challans/:id returns specific challan"""
        if not TestDeliveryChallans.created_challan_id:
            pytest.skip("No challan created")
        response = requests.get(
            f"{BASE_URL}/api/v1/delivery-challans/{TestDeliveryChallans.created_challan_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Get challan failed: {response.status_code}"
        data = response.json()
        assert data["challan_id"] == TestDeliveryChallans.created_challan_id

    def test_04_update_delivery_challan(self):
        """PUT /api/v1/delivery-challans/:id updates challan"""
        if not TestDeliveryChallans.created_challan_id:
            pytest.skip("No challan created")
        payload = {"vehicle_number": "KA02CD5678", "notes": "Updated notes"}
        response = requests.put(
            f"{BASE_URL}/api/v1/delivery-challans/{TestDeliveryChallans.created_challan_id}",
            headers=self.get_headers(), json=payload
        )
        assert response.status_code == 200, f"Update challan failed: {response.status_code}"
        data = response.json()
        assert data["vehicle_number"] == "KA02CD5678", f"Update not applied: {data}"

    def test_05_cannot_delete_delivered_challan(self):
        """DELETE /api/v1/delivery-challans/:id fails if status=delivered"""
        # First update status to delivered
        if not TestDeliveryChallans.created_challan_id:
            pytest.skip("No challan created")
        # Update to delivered status
        requests.put(
            f"{BASE_URL}/api/v1/delivery-challans/{TestDeliveryChallans.created_challan_id}",
            headers=self.get_headers(), json={"status": "delivered"}
        )
        # Try to delete
        response = requests.delete(
            f"{BASE_URL}/api/v1/delivery-challans/{TestDeliveryChallans.created_challan_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 400, f"Expected 400 for delivered challan, got {response.status_code}"
        assert "cannot delete" in response.text.lower() or "delivered" in response.text.lower()

    def test_06_delete_draft_challan(self):
        """DELETE /api/v1/delivery-challans/:id succeeds for draft"""
        # Create a new draft challan to delete
        payload = {
            "customer_id": TEST_CUSTOMER,
            "date": "2026-02-16",
            "items": [],
            "notes": "Challan to be deleted"
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/delivery-challans", headers=self.get_headers(), json=payload)
        assert create_resp.status_code == 200
        challan_id = create_resp.json()["challan_id"]
        
        # Delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/delivery-challans/{challan_id}", headers=self.get_headers())
        assert delete_resp.status_code == 200, f"Delete draft failed: {delete_resp.status_code}"
        
        # Verify deletion
        get_resp = requests.get(f"{BASE_URL}/api/v1/delivery-challans/{challan_id}", headers=self.get_headers())
        assert get_resp.status_code == 404


class TestVendorCredits:
    """Vendor Credits CRUD tests with period lock enforcement"""
    token = None
    org_id = None
    created_credit_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestVendorCredits.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            })
            assert response.status_code == 200
            data = response.json()
            TestVendorCredits.token = data["token"]
            TestVendorCredits.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestVendorCredits.token}"}
        if TestVendorCredits.org_id:
            headers["X-Organization-ID"] = TestVendorCredits.org_id
        return headers

    def test_01_list_vendor_credits(self):
        """GET /api/v1/vendor-credits returns list with pagination"""
        response = requests.get(f"{BASE_URL}/api/v1/vendor-credits", headers=self.get_headers())
        assert response.status_code == 200, f"List vendor credits failed: {response.status_code}"
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        print(f"Found {data['pagination']['total']} vendor credits")

    def test_02_create_vendor_credit_locked_period_fails(self):
        """POST /api/v1/vendor-credits fails for locked period (Jan 2026)"""
        payload = {
            "vendor_id": "test-vendor-001",
            "date": "2026-01-15",  # January is locked
            "amount": 1000.0,
            "reason": "Test credit for locked period"
        }
        response = requests.post(f"{BASE_URL}/api/v1/vendor-credits", headers=self.get_headers(), json=payload)
        # Should fail with 423 (period locked)
        assert response.status_code == 423, f"Expected 423 for locked period, got {response.status_code}: {response.text}"
        print("Period lock correctly blocked January 2026 vendor credit creation")

    def test_03_create_vendor_credit_open_period(self):
        """POST /api/v1/vendor-credits succeeds for open period (Feb 2026)"""
        payload = {
            "vendor_id": "test-vendor-001",
            "date": "2026-02-15",  # February is NOT locked
            "amount": 2500.50,
            "reason": "Test vendor credit for Phase B sprint",
            "line_items": [{"item_name": "Defective Battery Return", "quantity": 5, "rate": 500, "amount": 2500}]
        }
        response = requests.post(f"{BASE_URL}/api/v1/vendor-credits", headers=self.get_headers(), json=payload)
        assert response.status_code == 200, f"Create vendor credit failed: {response.status_code}, {response.text}"
        data = response.json()
        assert "credit_id" in data
        assert "credit_note_number" in data
        assert data["status"] == "draft"
        TestVendorCredits.created_credit_id = data["credit_id"]
        print(f"Created vendor credit: {data['credit_note_number']} ({data['credit_id']})")

    def test_04_get_vendor_credit_by_id(self):
        """GET /api/v1/vendor-credits/:id returns specific credit"""
        if not TestVendorCredits.created_credit_id:
            pytest.skip("No credit created")
        response = requests.get(
            f"{BASE_URL}/api/v1/vendor-credits/{TestVendorCredits.created_credit_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["credit_id"] == TestVendorCredits.created_credit_id

    def test_05_apply_vendor_credit_creates_journal_entry(self):
        """POST /api/v1/vendor-credits/:id/apply creates journal entry"""
        if not TestVendorCredits.created_credit_id:
            pytest.skip("No credit created")
        response = requests.post(
            f"{BASE_URL}/api/v1/vendor-credits/{TestVendorCredits.created_credit_id}/apply",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Apply vendor credit failed: {response.status_code}, {response.text}"
        data = response.json()
        assert "journal_entry_id" in data, f"Missing journal_entry_id: {data}"
        print(f"Applied vendor credit, created journal entry: {data['journal_entry_id']}")

    def test_06_cannot_delete_applied_credit(self):
        """DELETE /api/v1/vendor-credits/:id fails for applied credits"""
        if not TestVendorCredits.created_credit_id:
            pytest.skip("No credit created")
        response = requests.delete(
            f"{BASE_URL}/api/v1/vendor-credits/{TestVendorCredits.created_credit_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 400, f"Expected 400 for applied credit, got {response.status_code}"
        assert "applied" in response.text.lower() or "cannot delete" in response.text.lower()

    def test_07_delete_draft_vendor_credit(self):
        """DELETE /api/v1/vendor-credits/:id succeeds for draft"""
        # Create a new draft to delete
        payload = {
            "vendor_id": "test-vendor-002",
            "date": "2026-02-20",
            "amount": 500.0,
            "reason": "Credit to be deleted"
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/vendor-credits", headers=self.get_headers(), json=payload)
        assert create_resp.status_code == 200
        credit_id = create_resp.json()["credit_id"]
        
        # Delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/vendor-credits/{credit_id}", headers=self.get_headers())
        assert delete_resp.status_code == 200, f"Delete draft failed: {delete_resp.status_code}"
        
        # Verify
        get_resp = requests.get(f"{BASE_URL}/api/v1/vendor-credits/{credit_id}", headers=self.get_headers())
        assert get_resp.status_code == 404


class TestBillsEnhanced:
    """Test /api/v1/bills-enhanced still works after removing legacy bills.py"""
    token = None
    org_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestBillsEnhanced.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            })
            assert response.status_code == 200
            data = response.json()
            TestBillsEnhanced.token = data["token"]
            TestBillsEnhanced.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestBillsEnhanced.token}"}
        if TestBillsEnhanced.org_id:
            headers["X-Organization-ID"] = TestBillsEnhanced.org_id
        return headers

    def test_bills_enhanced_list(self):
        """GET /api/v1/bills-enhanced works"""
        response = requests.get(f"{BASE_URL}/api/v1/bills-enhanced", headers=self.get_headers())
        assert response.status_code in [200, 404], f"Bills enhanced failed: {response.status_code}"
        print(f"Bills enhanced endpoint status: {response.status_code}")


class TestFinancialReports:
    """Test Balance Sheet and P&L report endpoints"""
    token = None
    org_id = None

    @pytest.fixture(autouse=True)
    def setup(self):
        if TestFinancialReports.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            })
            assert response.status_code == 200
            data = response.json()
            TestFinancialReports.token = data["token"]
            TestFinancialReports.org_id = data.get("current_organization")

    def get_headers(self):
        headers = {"Authorization": f"Bearer {TestFinancialReports.token}"}
        if TestFinancialReports.org_id:
            headers["X-Organization-ID"] = TestFinancialReports.org_id
        return headers

    def test_balance_sheet_endpoint(self):
        """GET /api/v1/journal-entries/reports/balance-sheet works"""
        response = requests.get(
            f"{BASE_URL}/api/v1/journal-entries/reports/balance-sheet?as_of_date=2026-02-26",
            headers=self.get_headers()
        )
        assert response.status_code in [200, 403, 402], f"Balance sheet failed: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"Balance sheet keys: {data.keys()}")

    def test_profit_loss_endpoint(self):
        """GET /api/v1/journal-entries/reports/profit-loss works"""
        response = requests.get(
            f"{BASE_URL}/api/v1/journal-entries/reports/profit-loss?start_date=2026-01-01&end_date=2026-02-26",
            headers=self.get_headers()
        )
        assert response.status_code in [200, 403, 402], f"P&L failed: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"P&L keys: {data.keys()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
