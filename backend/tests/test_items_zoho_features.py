"""
Test suite for Items Module Phase 1 - Zoho Books Style Features
Tests: Search, Sort, Filter, Bulk Actions, Export/Import, Custom Fields, Price Lists with Type
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://audit-fixes-5.preview.emergentagent.com').rstrip('/')


class TestSearchSortFilter:
    """Test search, sort, and filter functionality"""
    
    def test_search_items_by_name(self):
        """Test searching items by name"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?search=Battery")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data
        print(f"✓ Search by name: Found {len(data['items'])} items matching 'Battery'")
    
    def test_search_items_by_sku(self):
        """Test searching items by SKU"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?search=SKU")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Search by SKU: Found {len(data['items'])} items")
    
    def test_sort_by_name_asc(self):
        """Test sorting items by name ascending"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?sort_by=name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        items = data["items"]
        if len(items) >= 2:
            assert items[0]["name"].lower() <= items[1]["name"].lower()
        print(f"✓ Sort by name ASC: First item is '{items[0]['name'] if items else 'N/A'}'")
    
    def test_sort_by_sales_rate_desc(self):
        """Test sorting items by sales rate descending"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?sort_by=sales_rate&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        items = data["items"]
        if len(items) >= 2:
            assert items[0].get("sales_rate", 0) >= items[1].get("sales_rate", 0)
        print(f"✓ Sort by sales_rate DESC: Highest rate is ₹{items[0].get('sales_rate', 0) if items else 0}")
    
    def test_sort_by_stock(self):
        """Test sorting items by stock"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?sort_by=stock_on_hand&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Sort by stock: {len(data['items'])} items returned")
    
    def test_filter_by_inventory_type(self):
        """Test filtering items by inventory type"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?item_type=inventory")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for item in data["items"]:
            assert item["item_type"] == "inventory"
        print(f"✓ Filter by inventory type: {len(data['items'])} inventory items")
    
    def test_filter_by_service_type(self):
        """Test filtering items by service type"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?item_type=service")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for item in data["items"]:
            assert item["item_type"] == "service"
        print(f"✓ Filter by service type: {len(data['items'])} service items")
    
    def test_filter_by_active_status(self):
        """Test filtering items by active status"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Filter by active status: {len(data['items'])} active items")


class TestBulkActions:
    """Test bulk action functionality"""
    
    @pytest.fixture
    def test_item_id(self):
        """Create a test item for bulk actions"""
        unique_name = f"TEST_BulkItem_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0,
            "initial_stock": 10
        })
        return response.json()["item"]["item_id"]
    
    def test_bulk_clone(self, test_item_id):
        """Test bulk clone action"""
        response = requests.post(f"{BASE_URL}/api/items-enhanced/bulk-action", json={
            "item_ids": [test_item_id],
            "action": "clone"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["results"]["success"] >= 1
        print(f"✓ Bulk clone: {data['results']['success']} items cloned")
    
    def test_bulk_deactivate(self, test_item_id):
        """Test bulk deactivate action"""
        response = requests.post(f"{BASE_URL}/api/items-enhanced/bulk-action", json={
            "item_ids": [test_item_id],
            "action": "deactivate"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["results"]["success"] >= 1
        print(f"✓ Bulk deactivate: {data['results']['success']} items deactivated")
    
    def test_bulk_activate(self, test_item_id):
        """Test bulk activate action"""
        # First deactivate
        requests.post(f"{BASE_URL}/api/items-enhanced/bulk-action", json={
            "item_ids": [test_item_id],
            "action": "deactivate"
        })
        # Then activate
        response = requests.post(f"{BASE_URL}/api/items-enhanced/bulk-action", json={
            "item_ids": [test_item_id],
            "action": "activate"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["results"]["success"] >= 1
        print(f"✓ Bulk activate: {data['results']['success']} items activated")
    
    def test_bulk_delete(self):
        """Test bulk delete action (creates new item to delete)"""
        # Create item specifically for deletion
        unique_name = f"TEST_DeleteItem_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 100.0
        })
        item_id = create_response.json()["item"]["item_id"]
        
        response = requests.post(f"{BASE_URL}/api/items-enhanced/bulk-action", json={
            "item_ids": [item_id],
            "action": "delete"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Bulk delete: {data['results']['success']} items deleted")
    
    def test_bulk_action_empty_list(self):
        """Test bulk action with empty item list"""
        response = requests.post(f"{BASE_URL}/api/items-enhanced/bulk-action", json={
            "item_ids": [],
            "action": "activate"
        })
        assert response.status_code == 400
        print("✓ Bulk action with empty list correctly rejected")


class TestExportImport:
    """Test export and import functionality"""
    
    def test_export_csv(self):
        """Test exporting items to CSV"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        content = response.text
        assert "item_id" in content or "name" in content
        lines = content.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one item
        print(f"✓ Export CSV: {len(lines)-1} items exported")
    
    def test_import_template_download(self):
        """Test downloading import template"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/export/template")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        content = response.text
        # Check required columns
        assert "name" in content
        assert "sku" in content
        assert "item_type" in content
        assert "sales_rate" in content
        print("✓ Import template downloaded with correct columns")


class TestCustomFields:
    """Test custom fields functionality"""
    
    def test_list_custom_fields(self):
        """Test listing custom fields"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/custom-fields")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "custom_fields" in data
        print(f"✓ Listed {len(data['custom_fields'])} custom fields")
    
    def test_create_text_custom_field(self):
        """Test creating a text custom field"""
        unique_name = f"TEST_Field_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/items-enhanced/custom-fields", json={
            "field_name": unique_name,
            "field_type": "text",
            "is_required": False,
            "show_in_list": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["field"]["field_name"] == unique_name
        print(f"✓ Created text custom field: {unique_name}")
    
    def test_create_dropdown_custom_field(self):
        """Test creating a dropdown custom field"""
        unique_name = f"TEST_Dropdown_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/items-enhanced/custom-fields", json={
            "field_name": unique_name,
            "field_type": "dropdown",
            "is_required": False,
            "dropdown_options": ["Option A", "Option B", "Option C"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["field"]["field_type"] == "dropdown"
        print(f"✓ Created dropdown custom field: {unique_name}")


class TestPriceListsEnhanced:
    """Test enhanced price lists with type"""
    
    def test_create_sales_price_list(self):
        """Test creating a sales price list"""
        unique_name = f"TEST_SalesPL_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/items-enhanced/price-lists", json={
            "name": unique_name,
            "description": "Sales price list",
            "discount_percentage": 10,
            "markup_percentage": 0,
            "is_active": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["price_list"]["name"] == unique_name
        print(f"✓ Created sales price list: {unique_name}")
    
    def test_create_purchase_price_list(self):
        """Test creating a purchase price list"""
        unique_name = f"TEST_PurchasePL_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/items-enhanced/price-lists", json={
            "name": unique_name,
            "description": "Purchase price list",
            "discount_percentage": 5,
            "markup_percentage": 0,
            "is_active": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Created purchase price list: {unique_name}")


class TestItemHistory:
    """Test item history tracking"""
    
    def test_get_all_history(self):
        """Test getting all item history"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/history")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "history" in data
        print(f"✓ Retrieved {len(data['history'])} history entries")
    
    def test_get_item_specific_history(self):
        """Test getting history for a specific item"""
        # Create an item first
        unique_name = f"TEST_HistItem_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0
        })
        item_id = create_response.json()["item"]["item_id"]
        
        # Get history for this item
        response = requests.get(f"{BASE_URL}/api/items-enhanced/history?item_id={item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # Should have at least the "created" entry
        assert len(data["history"]) >= 1
        print(f"✓ Retrieved {len(data['history'])} history entries for item {item_id}")


class TestInventoryAdjustmentsEnhanced:
    """Test enhanced inventory adjustments"""
    
    @pytest.fixture
    def inventory_item_and_warehouse(self):
        """Create test item and get warehouse"""
        # Create item
        unique_name = f"TEST_AdjEnhItem_{uuid.uuid4().hex[:6]}"
        item_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0,
            "initial_stock": 100
        })
        item_id = item_response.json()["item"]["item_id"]
        
        # Get warehouse
        wh_response = requests.get(f"{BASE_URL}/api/items-enhanced/warehouses")
        warehouse_id = wh_response.json()["warehouses"][0]["warehouse_id"]
        
        return item_id, warehouse_id
    
    def test_add_stock_adjustment(self, inventory_item_and_warehouse):
        """Test adding stock via adjustment"""
        item_id, warehouse_id = inventory_item_and_warehouse
        response = requests.post(f"{BASE_URL}/api/items-enhanced/adjustments", json={
            "item_id": item_id,
            "warehouse_id": warehouse_id,
            "adjustment_type": "add",
            "quantity": 50,
            "reason": "purchase",
            "notes": "Test stock addition"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["adjustment"]["quantity"] == 50
        assert data["adjustment"]["adjustment_type"] == "add"
        print(f"✓ Added 50 units to stock")
    
    def test_subtract_stock_adjustment(self, inventory_item_and_warehouse):
        """Test subtracting stock via adjustment"""
        item_id, warehouse_id = inventory_item_and_warehouse
        response = requests.post(f"{BASE_URL}/api/items-enhanced/adjustments", json={
            "item_id": item_id,
            "warehouse_id": warehouse_id,
            "adjustment_type": "subtract",
            "quantity": 10,
            "reason": "damage",
            "notes": "Test stock subtraction"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["adjustment"]["adjustment_type"] == "subtract"
        print(f"✓ Subtracted 10 units from stock")


class TestItemCRUDEnhanced:
    """Test enhanced item CRUD operations"""
    
    def test_create_item_with_all_fields(self):
        """Test creating item with all Zoho-style fields"""
        unique_name = f"TEST_FullItem_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "sku": f"SKU-{uuid.uuid4().hex[:6]}",
            "description": "Full featured test item",
            "item_type": "inventory",
            "sales_rate": 1500.0,
            "sales_description": "Sales description",
            "purchase_rate": 1000.0,
            "purchase_description": "Purchase description",
            "unit": "pcs",
            "tax_preference": "taxable",
            "tax_percentage": 18,
            "intra_state_tax_rate": 18,
            "inter_state_tax_rate": 18,
            "hsn_code": "85071000",
            "initial_stock": 100,
            "reorder_level": 20,
            "track_inventory": True,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/items-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        item = data["item"]
        assert item["name"] == unique_name
        assert item["hsn_code"] == "85071000"
        assert item["tax_preference"] == "taxable"
        print(f"✓ Created item with all fields: {unique_name}")
    
    def test_update_item(self):
        """Test updating an item"""
        # Create item first
        unique_name = f"TEST_UpdateItem_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0
        })
        item_id = create_response.json()["item"]["item_id"]
        
        # Update it
        response = requests.put(f"{BASE_URL}/api/items-enhanced/{item_id}", json={
            "name": f"{unique_name}_Updated",
            "sales_rate": 600.0,
            "hsn_code": "12345678"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify update
        get_response = requests.get(f"{BASE_URL}/api/items-enhanced/{item_id}")
        updated_item = get_response.json()["item"]
        assert updated_item["sales_rate"] == 600.0
        print(f"✓ Updated item: {item_id}")
    
    def test_delete_item_no_transactions(self):
        """Test deleting item with no transactions"""
        # Create item
        unique_name = f"TEST_DeleteItem_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 100.0
        })
        item_id = create_response.json()["item"]["item_id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/items-enhanced/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/items-enhanced/{item_id}")
        assert get_response.status_code == 404
        print(f"✓ Deleted item: {item_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
