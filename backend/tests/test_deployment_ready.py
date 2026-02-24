"""
Deployment Readiness Tests for Battwheels OS
Tests all critical APIs after collection mapping fix
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://audit-fixes-5.preview.emergentagent.com')
ORG_ID = "org_71f0df814d6d"
HEADERS = {
    "Content-Type": "application/json",
    "X-Organization-ID": ORG_ID
}


class TestLoginAPI:
    """Test Login API - admin@battwheels.in / admin123"""
    
    def test_login_success(self):
        """Login with admin credentials should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "test_pwd_placeholder"
        }, headers={"Content-Type": "application/json"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == "admin@battwheels.in"
        print(f"✓ Login successful: {data['user']['email']}")
        
        # Store token for authenticated tests
        self.auth_token = data["token"]
    
    def test_login_invalid_credentials(self):
        """Login with wrong credentials should fail"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrong_pwd_placeholder"
        }, headers={"Content-Type": "application/json"})
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


class TestContactsEnhancedAPI:
    """Test Contacts Enhanced API - GET /api/contacts-enhanced/"""
    
    def test_get_contacts_returns_337_contacts(self):
        """Should return 337 contacts for org_71f0df814d6d"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "contacts" in data, "Response should contain contacts"
        
        total = data.get("page_context", {}).get("total", len(data["contacts"]))
        print(f"✓ Contacts Enhanced: {total} contacts returned")
        
        # Should have approximately 337 contacts (may vary slightly)
        assert total >= 300, f"Expected ~337 contacts, got {total}"
    
    def test_contacts_have_required_fields(self):
        """Contacts should have contact_id field"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/?per_page=5", headers=HEADERS)
        
        assert response.status_code == 200
        data = response.json()
        
        for contact in data.get("contacts", [])[:5]:
            assert "contact_id" in contact or "zoho_contact_id" in contact, "Contact should have contact_id"
            assert "contact_name" in contact or "name" in contact, "Contact should have name"
        print("✓ Contacts have required fields")


class TestInvoicesEnhancedAPI:
    """Test Invoices Enhanced API - GET /api/invoices-enhanced/"""
    
    def test_get_invoices_returns_8000_plus(self):
        """Should return 8000+ invoices"""
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "invoices" in data, "Response should contain invoices"
        
        total = data.get("page_context", {}).get("total", len(data["invoices"]))
        print(f"✓ Invoices Enhanced: {total} invoices returned")
        
        # Should have 8000+ invoices
        assert total >= 8000, f"Expected 8000+ invoices, got {total}"
    
    def test_invoices_have_amounts(self):
        """Invoices should have balance and total fields"""
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/?per_page=5", headers=HEADERS)
        
        assert response.status_code == 200
        data = response.json()
        
        for invoice in data.get("invoices", [])[:5]:
            # Check for amount fields (Zoho format)
            has_amount = "total" in invoice or "grand_total" in invoice or "balance" in invoice
            assert has_amount, f"Invoice should have amount field: {invoice.keys()}"
        print("✓ Invoices have amount fields")


class TestEstimatesEnhancedAPI:
    """Test Estimates Enhanced API - GET /api/estimates-enhanced/"""
    
    def test_get_estimates_returns_3400_plus(self):
        """Should return 3400+ estimates"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "estimates" in data, "Response should contain estimates"
        
        total = data.get("page_context", {}).get("total", len(data["estimates"]))
        print(f"✓ Estimates Enhanced: {total} estimates returned")
        
        # Should have 3400+ estimates
        assert total >= 3400, f"Expected 3400+ estimates, got {total}"


class TestDataManagementAPI:
    """Test Data Management API endpoints"""
    
    def test_data_counts(self):
        """GET /api/data-management/counts should return record counts"""
        response = requests.get(f"{BASE_URL}/api/data-management/counts", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "counts" in data, "Response should contain counts"
        
        counts = data["counts"]
        print(f"✓ Data counts returned for {len(counts)} collections")
        
        # Verify specific counts
        assert counts.get("contacts", {}).get("total", 0) >= 300, "Expected 337 contacts"
        assert counts.get("invoices", {}).get("total", 0) >= 8000, "Expected 8000+ invoices"
        assert counts.get("estimates", {}).get("total", 0) >= 3400, "Expected 3400+ estimates"
        assert counts.get("items", {}).get("total", 0) >= 1300, "Expected 1300+ items"
        
        print(f"  - Contacts: {counts.get('contacts', {}).get('total', 0)}")
        print(f"  - Invoices: {counts.get('invoices', {}).get('total', 0)}")
        print(f"  - Estimates: {counts.get('estimates', {}).get('total', 0)}")
        print(f"  - Items: {counts.get('items', {}).get('total', 0)}")
    
    def test_sync_status_shows_synced(self):
        """GET /api/data-management/sync/status should show synced status"""
        response = requests.get(f"{BASE_URL}/api/data-management/sync/status", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "status" in data, "Response should contain status"
        
        status = data["status"]
        modules = status.get("modules", {})
        
        # Check that key modules are synced
        synced_count = 0
        for module, info in modules.items():
            if info.get("status") == "synced":
                synced_count += 1
        
        print(f"✓ Sync status: {synced_count}/{len(modules)} modules synced")
        assert synced_count > 0, "At least some modules should be synced"


class TestItemsEnhancedAPI:
    """Test Items Enhanced API - GET /api/items-enhanced/"""
    
    def test_get_items_returns_1300_plus(self):
        """Should return 1300+ items"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "items" in data, "Response should contain items"
        
        total = data.get("page_context", {}).get("total", len(data["items"]))
        print(f"✓ Items Enhanced: {total} items returned")
        
        # Should have 1300+ items
        assert total >= 1300, f"Expected 1300+ items, got {total}"
    
    def test_items_have_required_fields(self):
        """Items should have item_id and name fields"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?per_page=5", headers=HEADERS)
        
        assert response.status_code == 200
        data = response.json()
        
        for item in data.get("items", [])[:5]:
            assert "item_id" in item or "zoho_item_id" in item, "Item should have item_id"
            assert "name" in item or "item_name" in item, "Item should have name"
        print("✓ Items have required fields")


class TestTicketsAPI:
    """Test Tickets API - GET /api/tickets"""
    
    @pytest.fixture(autouse=True)
    def get_auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "test_pwd_placeholder"
        })
        if response.status_code == 200:
            self.auth_headers = {
                **HEADERS,
                "Authorization": f"Bearer {response.json()['token']}"
            }
        else:
            pytest.skip("Could not get auth token")
    
    def test_get_tickets(self):
        """Should return tickets"""
        response = requests.get(f"{BASE_URL}/api/tickets", headers=self.auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tickets" in data, "Response should contain tickets"
        
        total = len(data["tickets"])
        print(f"✓ Tickets: {total} tickets returned")


class TestInvoiceSummary:
    """Test Invoice Summary API"""
    
    def test_invoices_summary(self):
        """GET /api/invoices-enhanced/summary should return summary statistics"""
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/summary", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "summary" in data, "Response should contain summary"
        
        summary = data["summary"]
        print(f"✓ Invoice Summary: {summary.get('total_invoices', 0)} total invoices")
        print(f"  - Total invoiced: ₹{summary.get('total_invoiced', 0):,.2f}")
        print(f"  - Total outstanding: ₹{summary.get('total_outstanding', 0):,.2f}")


class TestEstimatesSummary:
    """Test Estimates Summary API"""
    
    def test_estimates_summary(self):
        """GET /api/estimates-enhanced/summary should return summary statistics"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/summary", headers=HEADERS)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0, "Expected code 0"
        assert "summary" in data, "Response should contain summary"
        
        summary = data["summary"]
        print(f"✓ Estimate Summary: {summary.get('total', 0)} total estimates")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
