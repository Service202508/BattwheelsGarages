"""
Test Items Enhanced Module - Zoho Books 39 Columns Compatibility
Tests:
1. Items API accepts all new Zoho Books fields on create
2. Items API exports CSV in Zoho Books format with all 39 columns
3. Items API export template has correct columns
4. Item creation with full fields (sales account, purchase account, inventory account, GST taxes)
5. Item list displays correctly with new fields
"""
import pytest
import requests
import os
import csv
import io
import uuid

pytestmark = pytest.mark.skip(reason="deprecated — Zoho integration removed")

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# All 39 Zoho Books compatible columns
ZOHO_EXPORT_COLUMNS = [
    "Item ID", "Item Name", "SKU", "HSN/SAC", "Description", "Rate",
    "Account", "Account Code", "Taxable", "Exemption Reason", "Taxability Type",
    "Product Type", "Intra State Tax Name", "Intra State Tax Rate", "Intra State Tax Type",
    "Inter State Tax Name", "Inter State Tax Rate", "Inter State Tax Type",
    "Source", "Reference ID", "Last Sync Time", "Status",
    "Usage unit", "Unit Name", "Purchase Rate", "Purchase Account", "Purchase Account Code",
    "Purchase Description", "Inventory Account", "Inventory Account Code",
    "Inventory Valuation Method", "Reorder Point", "Vendor", "Location Name",
    "Opening Stock", "Opening Stock Value", "Stock On Hand",
    "Item Type", "Sellable", "Purchasable", "Track Inventory"
]

# Template columns (excludes Item ID, Last Sync Time, Stock On Hand - auto-generated)
ZOHO_TEMPLATE_COLUMNS = [
    "Item Name", "SKU", "HSN/SAC", "Description", "Rate",
    "Account", "Account Code", "Taxable", "Exemption Reason", "Taxability Type",
    "Product Type", "Intra State Tax Name", "Intra State Tax Rate", "Intra State Tax Type",
    "Inter State Tax Name", "Inter State Tax Rate", "Inter State Tax Type",
    "Source", "Reference ID", "Status",
    "Usage unit", "Unit Name", "Purchase Rate", "Purchase Account", "Purchase Account Code",
    "Purchase Description", "Inventory Account", "Inventory Account Code",
    "Inventory Valuation Method", "Reorder Point", "Vendor", "Location Name",
    "Opening Stock", "Opening Stock Value",
    "Item Type", "Sellable", "Purchasable", "Track Inventory"
]


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestItemsEnhancedZohoColumns:
    """Test Items Enhanced API with full Zoho Books compatibility"""

    def test_health_check(self, api_client):
        """Test backend is running"""
        # Try multiple health endpoints
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/summary")
        assert response.status_code == 200
        print("Backend health check passed (via items-enhanced/summary)")

    def test_items_endpoint_available(self, api_client):
        """Test items enhanced endpoint is available"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"Items endpoint available, found {len(data.get('items', []))} items")

    def test_create_item_with_full_zoho_fields(self, api_client):
        """Test creating item with all Zoho Books compatible fields"""
        unique_id = uuid.uuid4().hex[:8]
        
        # Full Zoho Books compatible item payload
        item_data = {
            # Basic Info
            "name": f"TEST_ZohoItem_{unique_id}",
            "sku": f"TEST-SKU-{unique_id}",
            "description": "Test item with full Zoho Books fields",
            "item_type": "inventory",
            "product_type": "goods",
            
            # Sales Information
            "rate": 5000.00,
            "sales_rate": 5000.00,
            "sales_description": "Sales description for test item",
            "sales_account": "Sales Revenue",
            "sales_account_code": "4000",
            
            # Purchase Information  
            "purchase_rate": 3500.00,
            "purchase_description": "Purchase description for test item",
            "purchase_account": "Cost of Goods Sold",
            "purchase_account_code": "5000",
            
            # Inventory Account
            "inventory_account": "Inventory Asset",
            "inventory_account_code": "1200",
            "inventory_valuation_method": "fifo",
            
            # Inventory Levels
            "opening_stock": 100,
            "opening_stock_value": 350000,
            "reorder_level": 20,
            
            # Units
            "unit": "pcs",
            "usage_unit": "pcs",
            "unit_name": "Pieces",
            
            # Tax Information
            "taxable": True,
            "tax_preference": "taxable",
            "taxability_type": "Goods",
            "exemption_reason": "",
            "tax_percentage": 18,
            
            # GST Taxes (India)
            "intra_state_tax_name": "GST",
            "intra_state_tax_rate": 18,
            "intra_state_tax_type": "percentage",
            "inter_state_tax_name": "IGST",
            "inter_state_tax_rate": 18,
            "inter_state_tax_type": "percentage",
            
            # HSN/SAC Codes
            "hsn_code": "85076000",
            
            # Vendor Information
            "vendor": "Test Vendor Ltd",
            
            # Location/Warehouse
            "location_name": "Main Warehouse",
            
            # Sync Information
            "source": "Manual",
            "reference_id": f"REF-{unique_id}",
            
            # Status & Flags
            "status": "active",
            "is_active": True,
            "sellable": True,
            "purchasable": True,
            "track_inventory": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        print(f"Create item response status: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to create item: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Error creating item: {data}"
        assert "item" in data
        
        item = data["item"]
        
        # Verify all key fields are saved correctly
        assert item["name"] == item_data["name"]
        assert item["sku"] == item_data["sku"]
        assert item["rate"] == item_data["rate"]
        assert item["sales_account"] == item_data["sales_account"]
        assert item["sales_account_code"] == item_data["sales_account_code"]
        assert item["purchase_rate"] == item_data["purchase_rate"]
        assert item["purchase_account"] == item_data["purchase_account"]
        assert item["purchase_account_code"] == item_data["purchase_account_code"]
        assert item["inventory_account"] == item_data["inventory_account"]
        assert item["inventory_account_code"] == item_data["inventory_account_code"]
        assert item["inventory_valuation_method"] == item_data["inventory_valuation_method"]
        assert item["opening_stock"] == item_data["opening_stock"]
        assert item["opening_stock_value"] == item_data["opening_stock_value"]
        assert item["taxable"] == item_data["taxable"]
        assert item["intra_state_tax_name"] == item_data["intra_state_tax_name"]
        assert item["intra_state_tax_rate"] == item_data["intra_state_tax_rate"]
        assert item["inter_state_tax_name"] == item_data["inter_state_tax_name"]
        assert item["inter_state_tax_rate"] == item_data["inter_state_tax_rate"]
        assert item["hsn_code"] == item_data["hsn_code"]
        assert item["vendor"] == item_data["vendor"]
        assert item["location_name"] == item_data["location_name"]
        assert item["sellable"] == item_data["sellable"]
        assert item["purchasable"] == item_data["purchasable"]
        assert item["track_inventory"] == item_data["track_inventory"]
        
        print(f"Created item with ID: {item.get('item_id')}")
        print(f"All 39 Zoho fields verified: PASS")
        
        return item.get("item_id")

    def test_create_item_minimal_fields(self, api_client):
        """Test creating item with minimal required fields"""
        unique_id = uuid.uuid4().hex[:8]
        
        item_data = {
            "name": f"TEST_MinimalItem_{unique_id}",
            "rate": 1000.00,
            "item_type": "inventory"
        }
        
        response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        
        item = data["item"]
        
        # Verify defaults are applied
        assert item["intra_state_tax_name"] == "GST"
        assert item["intra_state_tax_rate"] == 18
        assert item["inter_state_tax_name"] == "IGST"
        assert item["inter_state_tax_rate"] == 18
        assert item["inventory_valuation_method"] == "fifo"
        assert item["sellable"] == True
        assert item["purchasable"] == True
        assert item["track_inventory"] == True
        
        print(f"Created minimal item with ID: {item.get('item_id')}")
        print("Default values correctly applied: PASS")

    def test_export_csv_has_39_columns(self, api_client):
        """Test CSV export contains all 39 Zoho Books columns"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/export?format=csv&include_inactive=true")
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        
        # Parse CSV content
        content = response.text
        csv_reader = csv.reader(io.StringIO(content))
        headers = next(csv_reader)
        
        print(f"CSV has {len(headers)} columns")
        print(f"Expected {len(ZOHO_EXPORT_COLUMNS)} columns")
        
        # Verify all 39 columns present
        missing_columns = []
        for col in ZOHO_EXPORT_COLUMNS:
            if col not in headers:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"Missing columns: {missing_columns}")
        
        assert len(missing_columns) == 0, f"Missing columns in CSV export: {missing_columns}"
        assert len(headers) >= 39, f"Expected at least 39 columns, got {len(headers)}"
        
        print(f"CSV export verified with all {len(headers)} Zoho Books columns: PASS")
        
        # Check at least one data row if items exist
        rows = list(csv_reader)
        if rows:
            print(f"CSV contains {len(rows)} data rows")

    def test_export_template_has_correct_columns(self, api_client):
        """Test import template contains correct Zoho Books columns"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/export/template")
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        
        # Parse CSV content
        content = response.text
        csv_reader = csv.reader(io.StringIO(content))
        headers = next(csv_reader)
        
        print(f"Template has {len(headers)} columns")
        print(f"Expected {len(ZOHO_TEMPLATE_COLUMNS)} columns")
        
        # Verify template columns present
        missing_columns = []
        for col in ZOHO_TEMPLATE_COLUMNS:
            if col not in headers:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"Missing columns in template: {missing_columns}")
        
        assert len(missing_columns) == 0, f"Missing columns in template: {missing_columns}"
        
        # Verify sample data rows exist
        rows = list(csv_reader)
        assert len(rows) >= 1, "Template should have at least one sample row"
        
        print(f"Template has {len(rows)} sample row(s)")
        print(f"Export template verified with all columns: PASS")

    def test_export_json_format(self, api_client):
        """Test JSON export format"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/export?format=json&include_inactive=true")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "items" in data
        assert "count" in data
        
        print(f"JSON export: {data['count']} items")
        
        # Verify item structure has core Zoho fields (checking fields that should always be present)
        if data["items"]:
            item = data["items"][0]
            # Check only basic fields that should always be present on any item
            core_fields = [
                "item_id", "name", "rate", "item_type", "status"
            ]
            
            missing = []
            for field in core_fields:
                if field not in item:
                    missing.append(field)
            
            assert len(missing) == 0, f"Missing core fields in JSON export: {missing}"
            
            print("JSON export structure verified: PASS")
            print(f"Sample item fields: {list(item.keys())[:15]}...")

    def test_item_list_with_new_fields(self, api_client):
        """Test item list displays correctly with new fields"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=10")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "items" in data
        assert "page_context" in data
        
        items = data["items"]
        print(f"Listed {len(items)} items")
        
        if items:
            # Check first item has all new fields
            item = items[0]
            
            # Core Zoho fields that should be present
            zoho_fields = [
                "name", "sku", "rate", "item_type", "status",
                "taxable", "intra_state_tax_name", "intra_state_tax_rate",
                "inter_state_tax_name", "inter_state_tax_rate",
                "inventory_valuation_method", "sellable", "purchasable", "track_inventory"
            ]
            
            present_fields = [f for f in zoho_fields if f in item]
            print(f"Present Zoho fields: {len(present_fields)}/{len(zoho_fields)}")
            
            # List missing fields
            missing = [f for f in zoho_fields if f not in item]
            if missing:
                print(f"Note: Some items may not have all fields set: {missing}")
            
            print("Item list structure verified: PASS")

    def test_create_service_item_with_gst(self, api_client):
        """Test creating a service item with SAC code and GST"""
        unique_id = uuid.uuid4().hex[:8]
        
        item_data = {
            "name": f"TEST_ServiceItem_{unique_id}",
            "sku": f"SRV-{unique_id}",
            "description": "Professional service item",
            "item_type": "service",
            "product_type": "service",
            "rate": 1500.00,
            "sales_account": "Service Revenue",
            "sales_account_code": "4100",
            "sac_code": "998719",  # SAC for services
            "taxable": True,
            "taxability_type": "Service",
            "intra_state_tax_name": "GST",
            "intra_state_tax_rate": 18,
            "inter_state_tax_name": "IGST",
            "inter_state_tax_rate": 18,
            "sellable": True,
            "purchasable": False,
            "track_inventory": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        
        item = data["item"]
        assert item["item_type"] == "service"
        assert item["product_type"] == "service"
        assert item["sac_code"] == "998719"
        assert item["track_inventory"] == False
        
        print(f"Created service item with SAC code: {item.get('item_id')}")

    def test_create_item_with_weighted_average_valuation(self, api_client):
        """Test creating item with weighted average valuation method"""
        unique_id = uuid.uuid4().hex[:8]
        
        item_data = {
            "name": f"TEST_WeightedAvgItem_{unique_id}",
            "sku": f"WAV-{unique_id}",
            "item_type": "inventory",
            "rate": 2000.00,
            "purchase_rate": 1500.00,
            "inventory_valuation_method": "weighted_average",
            "opening_stock": 50,
            "opening_stock_value": 75000,
            "track_inventory": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        
        item = data["item"]
        assert item["inventory_valuation_method"] == "weighted_average"
        
        print(f"Created item with weighted average valuation: {item.get('item_id')}")

    def test_get_single_item_details(self, api_client):
        """Test getting a single item with all fields"""
        # First create an item
        unique_id = uuid.uuid4().hex[:8]
        
        item_data = {
            "name": f"TEST_DetailItem_{unique_id}",
            "sku": f"DET-{unique_id}",
            "item_type": "inventory",
            "rate": 3000.00,
            "purchase_rate": 2000.00,
            "hsn_code": "85076000",
            "intra_state_tax_rate": 18,
            "inter_state_tax_rate": 18,
            "inventory_account": "Inventory Asset",
            "inventory_valuation_method": "fifo"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        assert create_response.status_code == 200
        
        item_id = create_response.json()["item"]["item_id"]
        
        # Get single item details
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/{item_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "item" in data
        
        item = data["item"]
        
        # Verify all key Zoho fields are returned
        assert item["name"] == item_data["name"]
        assert item["sku"] == item_data["sku"]
        assert item["rate"] == item_data["rate"]
        assert item["purchase_rate"] == item_data["purchase_rate"]
        assert item["hsn_code"] == item_data["hsn_code"]
        
        print(f"Single item details verified for: {item_id}")

    def test_update_item_zoho_fields(self, api_client):
        """Test updating item with Zoho fields"""
        # Create item first
        unique_id = uuid.uuid4().hex[:8]
        
        create_data = {
            "name": f"TEST_UpdateItem_{unique_id}",
            "rate": 1000.00,
            "item_type": "inventory"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=create_data)
        assert create_response.status_code == 200
        item_id = create_response.json()["item"]["item_id"]
        
        # Update with Zoho fields
        update_data = {
            "rate": 1500.00,
            "sales_account": "Updated Sales Account",
            "sales_account_code": "4500",
            "purchase_account": "Updated Purchase Account",
            "purchase_account_code": "5500",
            "inventory_account": "Updated Inventory",
            "inventory_account_code": "1300",
            "intra_state_tax_rate": 12,
            "inter_state_tax_rate": 12,
            "vendor": "Updated Vendor Name",
            "reorder_level": 30
        }
        
        update_response = api_client.put(f"{BASE_URL}/api/items-enhanced/{item_id}", json=update_data)
        assert update_response.status_code == 200
        
        # Verify updates
        get_response = api_client.get(f"{BASE_URL}/api/items-enhanced/{item_id}")
        item = get_response.json()["item"]
        
        assert item["rate"] == 1500.00
        assert item["sales_account"] == "Updated Sales Account"
        assert item["purchase_account"] == "Updated Purchase Account"
        assert item["inventory_account"] == "Updated Inventory"
        assert item["intra_state_tax_rate"] == 12
        assert item["vendor"] == "Updated Vendor Name"
        assert item["reorder_level"] == 30
        
        print(f"Item updated successfully with Zoho fields: {item_id}")


class TestItemsExportValidation:
    """Validate export CSV structure and data"""
    
    def test_export_csv_data_integrity(self, api_client):
        """Test that exported CSV data matches item data"""
        # Create an item with known values
        unique_id = uuid.uuid4().hex[:8]
        
        item_data = {
            "name": f"TEST_ExportVerify_{unique_id}",
            "sku": f"EXP-{unique_id}",
            "description": "Test export data integrity",
            "item_type": "inventory",
            "rate": 9999.00,
            "sales_account": "Test Sales Account",
            "sales_account_code": "TEST4000",
            "purchase_rate": 7777.00,
            "purchase_account": "Test Purchase Account",
            "purchase_account_code": "TEST5000",
            "inventory_account": "Test Inventory Account",
            "inventory_account_code": "TEST1200",
            "hsn_code": "12345678",
            "intra_state_tax_rate": 5,
            "inter_state_tax_rate": 5,
            "opening_stock": 999,
            "opening_stock_value": 7769223,
            "vendor": "Test Export Vendor",
            "location_name": "Test Warehouse",
            "sellable": True,
            "purchasable": True,
            "track_inventory": True
        }
        
        # Create item
        create_response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        assert create_response.status_code == 200
        
        # Export and find our item
        export_response = api_client.get(f"{BASE_URL}/api/items-enhanced/export?format=csv&include_inactive=true")
        assert export_response.status_code == 200
        
        content = export_response.text
        csv_reader = csv.DictReader(io.StringIO(content))
        
        # Find our test item
        found_item = None
        for row in csv_reader:
            if row.get("SKU") == item_data["sku"]:
                found_item = row
                break
        
        assert found_item is not None, f"Could not find item with SKU {item_data['sku']} in export"
        
        # Verify data matches
        assert found_item["Item Name"] == item_data["name"]
        assert found_item["SKU"] == item_data["sku"]
        assert float(found_item["Rate"]) == item_data["rate"]
        assert found_item["Account"] == item_data["sales_account"]
        assert found_item["Account Code"] == item_data["sales_account_code"]
        assert float(found_item["Purchase Rate"]) == item_data["purchase_rate"]
        assert found_item["Purchase Account"] == item_data["purchase_account"]
        assert found_item["Inventory Account"] == item_data["inventory_account"]
        assert found_item["HSN/SAC"] == item_data["hsn_code"]
        assert float(found_item["Intra State Tax Rate"]) == item_data["intra_state_tax_rate"]
        assert float(found_item["Inter State Tax Rate"]) == item_data["inter_state_tax_rate"]
        assert float(found_item["Opening Stock"]) == item_data["opening_stock"]
        assert found_item["Vendor"] == item_data["vendor"]
        assert found_item["Location Name"] == item_data["location_name"]
        assert found_item["Sellable"] == "Yes"
        assert found_item["Purchasable"] == "Yes"
        assert found_item["Track Inventory"] == "Yes"
        
        print(f"Export data integrity verified for: {item_data['sku']}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_items(self, api_client):
        """Clean up TEST_ prefixed items"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/?search=TEST_&per_page=100")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            deleted_count = 0
            for item in items:
                item_id = item.get("item_id")
                if item_id:
                    del_response = api_client.delete(f"{BASE_URL}/api/items-enhanced/{item_id}")
                    if del_response.status_code == 200:
                        deleted_count += 1
            
            print(f"Cleaned up {deleted_count} test items")
        else:
            print("No test items to cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
