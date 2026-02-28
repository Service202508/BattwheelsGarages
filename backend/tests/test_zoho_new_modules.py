"""
Test Suite for New Zoho Books Modules:
- Recurring Bills API
- Fixed Assets API  
- Custom Modules API
- Contacts Enhanced (renamed from contacts_enhanced_v2)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

pytestmark = pytest.mark.skip(reason="deprecated — Zoho integration removed")

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://rbac-bypass-fix.preview.emergentagent.com')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "DevTest@123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ============== RECURRING BILLS TESTS ==============

class TestRecurringBills:
    """Test Recurring Bills CRUD and operations"""
    
    created_bill_id = None
    
    def test_list_recurring_bills(self, authenticated_client):
        """Test listing recurring bills"""
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/recurring-bills")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "recurring_bills" in data
        print(f"Found {len(data['recurring_bills'])} recurring bills")
    
    def test_create_recurring_bill(self, authenticated_client):
        """Test creating a recurring bill"""
        today = datetime.now().strftime("%Y-%m-%d")
        payload = {
            "vendor_id": "TEST-VENDOR-001",
            "vendor_name": "Test Vendor for Recurring Bill",
            "recurrence_name": "TEST Monthly Office Rent",
            "recurrence_frequency": "monthly",
            "repeat_every": 1,
            "start_date": today,
            "end_date": "",
            "never_expires": True,
            "line_items": [
                {
                    "name": "Office Rent",
                    "description": "Monthly rent payment",
                    "quantity": 1,
                    "rate": 50000,
                    "tax_percentage": 18
                }
            ],
            "payment_terms": 30,
            "notes": "Test recurring bill"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/zoho/recurring-bills", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "recurring_bill" in data
        assert data["recurring_bill"]["recurrence_name"] == "TEST Monthly Office Rent"
        assert data["recurring_bill"]["total"] == 59000  # 50000 + 18% tax
        
        TestRecurringBills.created_bill_id = data["recurring_bill"]["recurring_bill_id"]
        print(f"Created recurring bill: {TestRecurringBills.created_bill_id}")
    
    def test_get_recurring_bill(self, authenticated_client):
        """Test getting a specific recurring bill"""
        if not TestRecurringBills.created_bill_id:
            pytest.skip("No recurring bill created")
        
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/recurring-bills/{TestRecurringBills.created_bill_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["recurring_bill"]["recurring_bill_id"] == TestRecurringBills.created_bill_id
        print(f"Retrieved recurring bill: {data['recurring_bill']['recurrence_name']}")
    
    def test_stop_recurring_bill(self, authenticated_client):
        """Test stopping a recurring bill"""
        if not TestRecurringBills.created_bill_id:
            pytest.skip("No recurring bill created")
        
        response = authenticated_client.post(f"{BASE_URL}/api/zoho/recurring-bills/{TestRecurringBills.created_bill_id}/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status changed
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/recurring-bills/{TestRecurringBills.created_bill_id}")
        assert get_response.json()["recurring_bill"]["status"] == "stopped"
        print("Recurring bill stopped successfully")
    
    def test_resume_recurring_bill(self, authenticated_client):
        """Test resuming a stopped recurring bill"""
        if not TestRecurringBills.created_bill_id:
            pytest.skip("No recurring bill created")
        
        response = authenticated_client.post(f"{BASE_URL}/api/zoho/recurring-bills/{TestRecurringBills.created_bill_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status changed
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/recurring-bills/{TestRecurringBills.created_bill_id}")
        assert get_response.json()["recurring_bill"]["status"] == "active"
        print("Recurring bill resumed successfully")
    
    def test_generate_due_bills(self, authenticated_client):
        """Test generating due bills from recurring profiles"""
        response = authenticated_client.post(f"{BASE_URL}/api/zoho/recurring-bills/generate")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "message" in data
        print(f"Generate due bills result: {data['message']}")
    
    def test_delete_recurring_bill(self, authenticated_client):
        """Test deleting a recurring bill"""
        if not TestRecurringBills.created_bill_id:
            pytest.skip("No recurring bill created")
        
        response = authenticated_client.delete(f"{BASE_URL}/api/zoho/recurring-bills/{TestRecurringBills.created_bill_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify deletion
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/recurring-bills/{TestRecurringBills.created_bill_id}")
        assert get_response.status_code == 404
        print("Recurring bill deleted successfully")


# ============== FIXED ASSETS TESTS ==============

class TestFixedAssets:
    """Test Fixed Assets CRUD and operations"""
    
    created_asset_id = None
    
    def test_get_fixed_assets_summary(self, authenticated_client):
        """Test getting fixed assets summary"""
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/fixed-assets/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        assert "total_assets" in data["summary"]
        assert "total_purchase_value" in data["summary"]
        assert "total_book_value" in data["summary"]
        print(f"Fixed Assets Summary: {data['summary']['total_assets']} assets, Book Value: {data['summary']['total_book_value']}")
    
    def test_list_fixed_assets(self, authenticated_client):
        """Test listing fixed assets"""
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/fixed-assets")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "fixed_assets" in data
        print(f"Found {len(data['fixed_assets'])} fixed assets")
    
    def test_create_fixed_asset(self, authenticated_client):
        """Test creating a fixed asset"""
        today = datetime.now().strftime("%Y-%m-%d")
        payload = {
            "asset_name": "TEST Office Furniture Set",
            "asset_type": "furniture",
            "description": "Test furniture for testing",
            "purchase_date": today,
            "purchase_price": 100000,
            "useful_life_years": 10,
            "salvage_value": 10000,
            "depreciation_method": "straight_line",
            "location": "Test Office",
            "serial_number": "TEST-FURN-001"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/zoho/fixed-assets", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "fixed_asset" in data
        assert data["fixed_asset"]["asset_name"] == "TEST Office Furniture Set"
        assert data["fixed_asset"]["annual_depreciation"] == 9000  # (100000 - 10000) / 10
        assert data["fixed_asset"]["book_value"] == 100000
        
        TestFixedAssets.created_asset_id = data["fixed_asset"]["asset_id"]
        print(f"Created fixed asset: {TestFixedAssets.created_asset_id}")
    
    def test_get_fixed_asset(self, authenticated_client):
        """Test getting a specific fixed asset"""
        if not TestFixedAssets.created_asset_id:
            pytest.skip("No fixed asset created")
        
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/fixed-assets/{TestFixedAssets.created_asset_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["fixed_asset"]["asset_id"] == TestFixedAssets.created_asset_id
        print(f"Retrieved fixed asset: {data['fixed_asset']['asset_name']}")
    
    def test_record_depreciation(self, authenticated_client):
        """Test recording depreciation for an asset"""
        if not TestFixedAssets.created_asset_id:
            pytest.skip("No fixed asset created")
        
        period = datetime.now().strftime("%Y-%m")
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/fixed-assets/{TestFixedAssets.created_asset_id}/depreciate",
            params={"period": period}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "entry" in data
        assert data["entry"]["amount"] == 750  # 9000 / 12 = 750 monthly
        print(f"Recorded depreciation: {data['entry']['amount']} for period {period}")
        
        # Verify book value updated
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/fixed-assets/{TestFixedAssets.created_asset_id}")
        asset = get_response.json()["fixed_asset"]
        assert asset["accumulated_depreciation"] == 750
        assert asset["book_value"] == 99250  # 100000 - 750
    
    def test_dispose_asset(self, authenticated_client):
        """Test disposing/selling a fixed asset"""
        if not TestFixedAssets.created_asset_id:
            pytest.skip("No fixed asset created")
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/fixed-assets/{TestFixedAssets.created_asset_id}/dispose",
            params={
                "disposal_date": today,
                "disposal_amount": 95000,
                "reason": "Test disposal"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "disposal" in data
        # Book value was 99250, selling for 95000 = loss of 4250
        assert data["disposal"]["gain_loss"] == -4250
        print(f"Asset disposed with gain/loss: {data['disposal']['gain_loss']}")
        
        # Verify status changed
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/fixed-assets/{TestFixedAssets.created_asset_id}")
        assert get_response.json()["fixed_asset"]["status"] == "disposed"
    
    def test_create_and_write_off_asset(self, authenticated_client):
        """Test creating and writing off a fixed asset"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create a new asset for write-off test
        payload = {
            "asset_name": "TEST Damaged Equipment",
            "asset_type": "equipment",
            "purchase_date": today,
            "purchase_price": 50000,
            "useful_life_years": 5,
            "salvage_value": 5000
        }
        
        create_response = authenticated_client.post(f"{BASE_URL}/api/zoho/fixed-assets", json=payload)
        assert create_response.status_code == 200
        asset_id = create_response.json()["fixed_asset"]["asset_id"]
        
        # Write off the asset
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/fixed-assets/{asset_id}/write-off",
            params={"reason": "Damaged beyond repair"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["write_off_amount"] == 50000
        print(f"Asset written off: {data['write_off_amount']}")
        
        # Verify status
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/fixed-assets/{asset_id}")
        asset = get_response.json()["fixed_asset"]
        assert asset["status"] == "written_off"
        assert asset["book_value"] == 0
        
        # Cleanup
        authenticated_client.delete(f"{BASE_URL}/api/zoho/fixed-assets/{asset_id}")
    
    def test_delete_fixed_asset(self, authenticated_client):
        """Test deleting a fixed asset"""
        if not TestFixedAssets.created_asset_id:
            pytest.skip("No fixed asset created")
        
        response = authenticated_client.delete(f"{BASE_URL}/api/zoho/fixed-assets/{TestFixedAssets.created_asset_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify deletion
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/fixed-assets/{TestFixedAssets.created_asset_id}")
        assert get_response.status_code == 404
        print("Fixed asset deleted successfully")


# ============== CUSTOM MODULES TESTS ==============

class TestCustomModules:
    """Test Custom Modules CRUD and record operations"""
    
    created_module_id = None
    created_record_id = None
    
    def test_list_custom_modules(self, authenticated_client):
        """Test listing custom modules"""
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/custom-modules")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "custom_modules" in data
        print(f"Found {len(data['custom_modules'])} custom modules")
    
    def test_create_custom_module(self, authenticated_client):
        """Test creating a custom module with various field types"""
        payload = {
            "module_name": "test_vehicle_tracking",
            "module_label": "TEST Vehicle Tracking",
            "description": "Track company vehicles for testing",
            "fields": [
                {"name": "vehicle_number", "label": "Vehicle Number", "type": "text", "required": True},
                {"name": "driver_name", "label": "Driver Name", "type": "text", "required": True},
                {"name": "last_service_date", "label": "Last Service Date", "type": "date", "required": False},
                {"name": "mileage", "label": "Current Mileage", "type": "number", "required": False},
                {"name": "fuel_cost", "label": "Monthly Fuel Cost", "type": "decimal", "required": False},
                {"name": "vehicle_status", "label": "Status", "type": "dropdown", "required": True, "options": ["Active", "In Service", "Retired"]},
                {"name": "is_insured", "label": "Insurance Valid", "type": "checkbox", "required": False}
            ],
            "icon": "car"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/zoho/custom-modules", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "custom_module" in data
        assert data["custom_module"]["module_label"] == "TEST Vehicle Tracking"
        assert len(data["custom_module"]["fields"]) == 7
        
        TestCustomModules.created_module_id = data["custom_module"]["module_id"]
        print(f"Created custom module: {TestCustomModules.created_module_id}")
    
    def test_get_custom_module(self, authenticated_client):
        """Test getting a specific custom module"""
        if not TestCustomModules.created_module_id:
            pytest.skip("No custom module created")
        
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["custom_module"]["module_id"] == TestCustomModules.created_module_id
        print(f"Retrieved custom module: {data['custom_module']['module_label']}")
    
    def test_create_custom_record(self, authenticated_client):
        """Test creating a record in a custom module"""
        if not TestCustomModules.created_module_id:
            pytest.skip("No custom module created")
        
        payload = {
            "vehicle_number": "KA-01-AB-1234",
            "driver_name": "Test Driver",
            "last_service_date": "2024-01-15",
            "mileage": 45000,
            "fuel_cost": 15000.50,
            "vehicle_status": "Active",
            "is_insured": True
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "record" in data
        assert data["record"]["vehicle_number"] == "KA-01-AB-1234"
        
        TestCustomModules.created_record_id = data["record"]["record_id"]
        print(f"Created custom record: {TestCustomModules.created_record_id}")
    
    def test_list_custom_records(self, authenticated_client):
        """Test listing records in a custom module"""
        if not TestCustomModules.created_module_id:
            pytest.skip("No custom module created")
        
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "records" in data
        assert len(data["records"]) >= 1
        print(f"Found {len(data['records'])} records in custom module")
    
    def test_get_custom_record(self, authenticated_client):
        """Test getting a specific record"""
        if not TestCustomModules.created_module_id or not TestCustomModules.created_record_id:
            pytest.skip("No custom module or record created")
        
        response = authenticated_client.get(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records/{TestCustomModules.created_record_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["record"]["record_id"] == TestCustomModules.created_record_id
        print(f"Retrieved custom record: {data['record']['vehicle_number']}")
    
    def test_update_custom_record(self, authenticated_client):
        """Test updating a record in a custom module"""
        if not TestCustomModules.created_module_id or not TestCustomModules.created_record_id:
            pytest.skip("No custom module or record created")
        
        payload = {
            "mileage": 50000,
            "vehicle_status": "In Service"
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records/{TestCustomModules.created_record_id}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify update
        get_response = authenticated_client.get(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records/{TestCustomModules.created_record_id}"
        )
        record = get_response.json()["record"]
        assert record["mileage"] == 50000
        assert record["vehicle_status"] == "In Service"
        print("Custom record updated successfully")
    
    def test_search_custom_records(self, authenticated_client):
        """Test searching records in a custom module"""
        if not TestCustomModules.created_module_id:
            pytest.skip("No custom module created")
        
        response = authenticated_client.get(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records",
            params={"search": "Test Driver"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"Search returned {len(data['records'])} records")
    
    def test_validate_required_fields(self, authenticated_client):
        """Test that required fields are validated"""
        if not TestCustomModules.created_module_id:
            pytest.skip("No custom module created")
        
        # Missing required field
        payload = {
            "vehicle_number": "KA-02-CD-5678"
            # Missing driver_name and vehicle_status which are required
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records",
            json=payload
        )
        assert response.status_code == 400
        print("Required field validation working correctly")
    
    def test_delete_custom_record(self, authenticated_client):
        """Test deleting a record from a custom module"""
        if not TestCustomModules.created_module_id or not TestCustomModules.created_record_id:
            pytest.skip("No custom module or record created")
        
        response = authenticated_client.delete(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records/{TestCustomModules.created_record_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify deletion
        get_response = authenticated_client.get(
            f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}/records/{TestCustomModules.created_record_id}"
        )
        assert get_response.status_code == 404
        print("Custom record deleted successfully")
    
    def test_deactivate_custom_module(self, authenticated_client):
        """Test deactivating (soft delete) a custom module"""
        if not TestCustomModules.created_module_id:
            pytest.skip("No custom module created")
        
        response = authenticated_client.delete(f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify deactivation (module still exists but is_active=False)
        get_response = authenticated_client.get(f"{BASE_URL}/api/zoho/custom-modules/{TestCustomModules.created_module_id}")
        assert get_response.status_code == 200
        assert get_response.json()["custom_module"]["is_active"] == False
        print("Custom module deactivated successfully")


# ============== CONTACTS ENHANCED TESTS (Renamed from contacts_enhanced_v2) ==============

class TestContactsEnhanced:
    """Test Contacts Enhanced API (renamed from contacts_enhanced_v2)"""
    
    def test_list_contacts(self, authenticated_client):
        """Test listing contacts"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/", params={"per_page": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contacts" in data
        assert "page_context" in data
        print(f"Found {data['page_context']['total']} contacts")
    
    def test_contacts_summary(self, authenticated_client):
        """Test contacts summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        assert "total_contacts" in data["summary"]
        assert "customers" in data["summary"]
        assert "vendors" in data["summary"]
        print(f"Contacts Summary: {data['summary']['total_contacts']} total, {data['summary']['customers']} customers, {data['summary']['vendors']} vendors")
    
    def test_filter_customers(self, authenticated_client):
        """Test filtering by contact type - customers"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/", params={"contact_type": "customer", "per_page": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All returned contacts should be customers or both
        for contact in data["contacts"]:
            assert contact["contact_type"] in ["customer", "both"]
        print(f"Customer filter returned {len(data['contacts'])} contacts")
    
    def test_filter_vendors(self, authenticated_client):
        """Test filtering by contact type - vendors"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/", params={"contact_type": "vendor", "per_page": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All returned contacts should be vendors or both
        for contact in data["contacts"]:
            assert contact["contact_type"] in ["vendor", "both"]
        print(f"Vendor filter returned {len(data['contacts'])} contacts")
    
    def test_validate_gstin(self, authenticated_client):
        """Test GSTIN validation endpoint"""
        # Valid GSTIN format
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/validate-gstin/27AABCU9603R1ZM")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["result"]["state_code"] == "MH"  # Maharashtra
        print(f"GSTIN validation: {data['result']['state_name']}")
    
    def test_get_indian_states(self, authenticated_client):
        """Test getting list of Indian states"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/states")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "states" in data
        assert len(data["states"]) > 30  # India has 28 states + UTs
        print(f"Found {len(data['states'])} Indian states/UTs")
    
    def test_contact_tags(self, authenticated_client):
        """Test contact tags endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "tags" in data
        print(f"Found {len(data['tags'])} contact tags")
    
    def test_check_sync(self, authenticated_client):
        """Test contacts sync/audit endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/check-sync")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "sync_report" in data
        assert "summary" in data["sync_report"]
        print(f"Sync report: {data['sync_report']['summary']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
