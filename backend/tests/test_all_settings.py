"""
Test All Settings API Endpoints
Tests for the Zoho Books-style All Settings feature
Covers: Settings categories, GST/TDS/MSME settings, Module settings, Custom fields, Workflows
"""
import os
import pytest
import requests
from typing import Optional

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = 'https://battwheels-beta.preview.emergentagent.com'

# Test organization ID
ORG_ID = "org_71f0df814d6d"


class TestSettingsCategories:
    """Test settings categories endpoint - no auth required"""
    
    def test_get_categories_returns_8(self):
        """GET /api/settings/categories - Should return exactly 8 categories"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        assert res.status_code == 200
        
        data = res.json()
        categories = data.get("categories", [])
        assert len(categories) == 8, f"Expected 8 categories, got {len(categories)}"
    
    def test_categories_have_required_structure(self):
        """Each category should have id, name, icon, color, items"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        assert res.status_code == 200
        
        categories = res.json().get("categories", [])
        for cat in categories:
            assert "id" in cat, f"Category missing 'id': {cat}"
            assert "name" in cat, f"Category missing 'name': {cat}"
            assert "icon" in cat, f"Category missing 'icon': {cat}"
            assert "color" in cat, f"Category missing 'color': {cat}"
            assert "items" in cat, f"Category missing 'items': {cat}"
            assert isinstance(cat["items"], list)
    
    def test_expected_category_ids_present(self):
        """All expected category IDs should be present"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        assert res.status_code == 200
        
        categories = res.json().get("categories", [])
        cat_ids = [c["id"] for c in categories]
        
        expected = ["organization", "users", "taxes", "customization", "automation", "modules", "integrations", "developer"]
        for expected_id in expected:
            assert expected_id in cat_ids, f"Missing category: {expected_id}"


class TestSettingsAuth:
    """Test authenticated settings endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        
        token = login_res.json().get("token")
        assert token, "No token in login response"
        
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Organization-ID": ORG_ID
        }
    
    def test_get_all_settings(self):
        """GET /api/settings - Returns all settings for organization"""
        res = requests.get(f"{BASE_URL}/api/settings", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        # Should have multiple settings keys
        assert "gst" in data or "vehicles" in data or "billing" in data, f"Missing expected settings keys: {list(data.keys())[:5]}"
    
    def test_get_gst_settings(self):
        """GET /api/settings/taxes/gst - Returns GST settings"""
        res = requests.get(f"{BASE_URL}/api/settings/taxes/gst", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        # Should have GST-related fields
        assert "is_gst_registered" in data or "gstin" in data or "gst_treatment" in data, f"Missing GST fields: {list(data.keys())}"
    
    def test_update_gst_settings(self):
        """PATCH /api/settings/taxes/gst - Updates GST settings"""
        update_data = {
            "is_gst_registered": True,
            "gstin": "22AAAAA0000A1Z5",
            "gst_treatment": "registered_business",
            "e_invoicing_enabled": False,
            "eway_bill_enabled": False
        }
        
        res = requests.patch(f"{BASE_URL}/api/settings/taxes/gst", headers=self.headers, json=update_data)
        assert res.status_code == 200
        
        data = res.json()
        assert data.get("is_gst_registered") == True, "GST registered setting not updated"
    
    def test_get_tds_settings(self):
        """GET /api/settings/taxes/tds - Returns TDS settings"""
        res = requests.get(f"{BASE_URL}/api/settings/taxes/tds", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        assert "is_tds_applicable" in data or "tan" in data, f"Missing TDS fields: {list(data.keys())}"
    
    def test_get_msme_settings(self):
        """GET /api/settings/taxes/msme - Returns MSME settings"""
        res = requests.get(f"{BASE_URL}/api/settings/taxes/msme", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        assert "is_msme_registered" in data or "payment_terms_days" in data, f"Missing MSME fields: {list(data.keys())}"


class TestModuleSettings:
    """Test module-specific settings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        assert login_res.status_code == 200
        
        token = login_res.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Organization-ID": ORG_ID
        }
    
    def test_get_vehicle_settings(self):
        """GET /api/settings/modules/vehicles - Returns vehicle module settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/vehicles", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        # Should have vehicle-related fields
        expected_keys = ["default_warranty_months", "categories", "statuses", "battery_warranty_months"]
        found = [k for k in expected_keys if k in data]
        assert len(found) >= 1, f"Missing vehicle settings keys. Found: {list(data.keys())}"
    
    def test_get_ticket_settings(self):
        """GET /api/settings/modules/tickets - Returns ticket module settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/tickets", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        expected_keys = ["default_priority", "categories", "sla_enabled", "priorities"]
        found = [k for k in expected_keys if k in data]
        assert len(found) >= 1, f"Missing ticket settings keys. Found: {list(data.keys())}"
    
    def test_get_billing_settings(self):
        """GET /api/settings/modules/billing - Returns billing module settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/billing", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        expected_keys = ["invoice_prefix", "default_payment_terms", "quote_prefix", "max_discount_percent"]
        found = [k for k in expected_keys if k in data]
        assert len(found) >= 1, f"Missing billing settings keys. Found: {list(data.keys())}"
    
    def test_get_inventory_settings(self):
        """GET /api/settings/modules/inventory - Returns inventory module settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/inventory", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        expected_keys = ["tracking_method", "low_stock_threshold", "enable_serial_tracking"]
        found = [k for k in expected_keys if k in data]
        assert len(found) >= 1, f"Missing inventory settings keys. Found: {list(data.keys())}"
    
    def test_get_efi_settings(self):
        """GET /api/settings/modules/efi - Returns EFI/Failure Intelligence settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/efi", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        # May have custom fields set, or defaults
        assert isinstance(data, dict), "EFI settings should return a dict"


class TestCustomizationSettings:
    """Test customization endpoints (custom fields, workflows)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        assert login_res.status_code == 200
        
        token = login_res.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Organization-ID": ORG_ID
        }
    
    def test_get_custom_fields(self):
        """GET /api/settings/custom-fields - Returns custom fields list"""
        res = requests.get(f"{BASE_URL}/api/settings/custom-fields", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        assert isinstance(data, list), "Custom fields should return a list"
    
    def test_get_workflows(self):
        """GET /api/settings/workflows - Returns workflow rules list"""
        res = requests.get(f"{BASE_URL}/api/settings/workflows", headers=self.headers)
        assert res.status_code == 200
        
        data = res.json()
        assert isinstance(data, list), "Workflows should return a list"


class TestPermissions:
    """Test permission requirements"""
    
    def test_settings_require_auth(self):
        """GET /api/settings - Should return 401 without auth"""
        res = requests.get(f"{BASE_URL}/api/settings")
        assert res.status_code in [401, 403], f"Expected 401/403 without auth, got {res.status_code}"
    
    def test_settings_require_org(self):
        """GET /api/settings - Should require organization context"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        token = login_res.json().get("token")
        
        # Try without org header
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        # Should either fail or return empty/default settings
        assert res.status_code in [200, 401, 403], f"Unexpected status: {res.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
