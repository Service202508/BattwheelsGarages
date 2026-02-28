"""
Test suite for Enhanced Items Module
Tests: Item Groups, Warehouses, Price Lists, Items, Adjustments, Reports
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://security-fixes-4.preview.emergentagent.com').rstrip('/')

class TestItemGroups:
    """Test Item Groups CRUD operations"""
    
    def test_list_item_groups(self):
        """Test listing item groups"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/groups")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "groups" in data
        assert isinstance(data["groups"], list)
        print(f"✓ Listed {len(data['groups'])} item groups")
    
    def test_create_item_group(self):
        """Test creating an item group"""
        unique_name = f"TEST_Group_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "description": "Test group for automated testing",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/items-enhanced/groups", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "group" in data
        assert data["group"]["name"] == unique_name
        print(f"✓ Created item group: {unique_name}")
        return data["group"]["group_id"]
    
    def test_get_item_group(self):
        """Test getting a specific item group"""
        # First create a group
        unique_name = f"TEST_GetGroup_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/groups", json={
            "name": unique_name,
            "description": "Test group"
        })
        group_id = create_response.json()["group"]["group_id"]
        
        # Then get it
        response = requests.get(f"{BASE_URL}/api/items-enhanced/groups/{group_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["group"]["name"] == unique_name
        print(f"✓ Retrieved item group: {group_id}")


class TestWarehouses:
    """Test Warehouses CRUD operations"""
    
    def test_list_warehouses(self):
        """Test listing warehouses"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/warehouses")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "warehouses" in data
        assert isinstance(data["warehouses"], list)
        print(f"✓ Listed {len(data['warehouses'])} warehouses")
    
    def test_create_warehouse(self):
        """Test creating a warehouse"""
        unique_name = f"TEST_Warehouse_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "location": "Test Location",
            "is_primary": False,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/items-enhanced/warehouses", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "warehouse" in data
        assert data["warehouse"]["name"] == unique_name
        print(f"✓ Created warehouse: {unique_name}")
        return data["warehouse"]["warehouse_id"]
    
    def test_get_warehouse(self):
        """Test getting a specific warehouse"""
        # First create a warehouse
        unique_name = f"TEST_GetWH_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/warehouses", json={
            "name": unique_name,
            "location": "Test Location"
        })
        warehouse_id = create_response.json()["warehouse"]["warehouse_id"]
        
        # Then get it
        response = requests.get(f"{BASE_URL}/api/items-enhanced/warehouses/{warehouse_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["warehouse"]["name"] == unique_name
        print(f"✓ Retrieved warehouse: {warehouse_id}")


class TestPriceLists:
    """Test Price Lists CRUD operations"""
    
    def test_list_price_lists(self):
        """Test listing price lists"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/price-lists")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "price_lists" in data
        assert isinstance(data["price_lists"], list)
        print(f"✓ Listed {len(data['price_lists'])} price lists")
    
    def test_create_price_list(self):
        """Test creating a price list"""
        unique_name = f"TEST_PriceList_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "description": "Test price list",
            "discount_percentage": 10.0,
            "markup_percentage": 0,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/items-enhanced/price-lists", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "price_list" in data
        assert data["price_list"]["name"] == unique_name
        print(f"✓ Created price list: {unique_name}")
        return data["price_list"]["pricelist_id"]
    
    def test_get_price_list(self):
        """Test getting a specific price list"""
        # First create a price list
        unique_name = f"TEST_GetPL_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/price-lists", json={
            "name": unique_name,
            "description": "Test"
        })
        pricelist_id = create_response.json()["price_list"]["pricelist_id"]
        
        # Then get it
        response = requests.get(f"{BASE_URL}/api/items-enhanced/price-lists/{pricelist_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["price_list"]["name"] == unique_name
        print(f"✓ Retrieved price list: {pricelist_id}")


class TestEnhancedItems:
    """Test Enhanced Items CRUD operations"""
    
    def test_list_items(self):
        """Test listing items"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"✓ Listed {len(data['items'])} items")
    
    def test_create_inventory_item(self):
        """Test creating an inventory item"""
        unique_name = f"TEST_Item_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "sku": f"SKU-{uuid.uuid4().hex[:6]}",
            "description": "Test inventory item",
            "item_type": "inventory",
            "sales_rate": 1000.0,
            "purchase_rate": 800.0,
            "unit": "pcs",
            "tax_percentage": 18,
            "hsn_code": "8507",
            "initial_stock": 50,
            "reorder_level": 10,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/items-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "item" in data
        assert data["item"]["name"] == unique_name
        assert data["item"]["item_type"] == "inventory"
        print(f"✓ Created inventory item: {unique_name}")
        return data["item"]["item_id"]
    
    def test_get_item(self):
        """Test getting a specific item"""
        # First create an item
        unique_name = f"TEST_GetItem_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0
        })
        item_id = create_response.json()["item"]["item_id"]
        
        # Then get it
        response = requests.get(f"{BASE_URL}/api/items-enhanced/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["item"]["name"] == unique_name
        print(f"✓ Retrieved item: {item_id}")
    
    def test_low_stock_items(self):
        """Test getting low stock items"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "low_stock_items" in data
        print(f"✓ Found {len(data['low_stock_items'])} low stock items")


class TestInventoryAdjustments:
    """Test Inventory Adjustments operations"""
    
    def test_list_adjustments(self):
        """Test listing adjustments"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/adjustments")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustments" in data
        assert isinstance(data["adjustments"], list)
        print(f"✓ Listed {len(data['adjustments'])} adjustments")
    
    def test_create_adjustment(self):
        """Test creating an inventory adjustment"""
        # First create an inventory item
        unique_name = f"TEST_AdjItem_{uuid.uuid4().hex[:6]}"
        item_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0,
            "initial_stock": 100
        })
        item_id = item_response.json()["item"]["item_id"]
        
        # Get a warehouse
        wh_response = requests.get(f"{BASE_URL}/api/items-enhanced/warehouses")
        warehouses = wh_response.json()["warehouses"]
        if not warehouses:
            # Create one if none exists
            wh_create = requests.post(f"{BASE_URL}/api/items-enhanced/warehouses", json={
                "name": f"TEST_WH_{uuid.uuid4().hex[:6]}",
                "location": "Test"
            })
            warehouse_id = wh_create.json()["warehouse"]["warehouse_id"]
        else:
            warehouse_id = warehouses[0]["warehouse_id"]
        
        # Create adjustment
        payload = {
            "item_id": item_id,
            "warehouse_id": warehouse_id,
            "adjustment_type": "add",
            "quantity": 25,
            "reason": "purchase",
            "notes": "Test adjustment"
        }
        response = requests.post(f"{BASE_URL}/api/items-enhanced/adjustments", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustment" in data
        assert data["adjustment"]["quantity"] == 25
        print(f"✓ Created adjustment for item: {item_id}")


class TestInventoryReports:
    """Test Inventory Reports"""
    
    def test_stock_summary(self):
        """Test stock summary report"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/reports/stock-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "stock_summary" in data
        summary = data["stock_summary"]
        assert "total_items" in summary
        assert "total_stock_value" in summary
        assert "low_stock_count" in summary
        assert "out_of_stock_count" in summary
        print(f"✓ Stock Summary: {summary['total_items']} items, ₹{summary['total_stock_value']:,.2f} value")
    
    def test_inventory_valuation(self):
        """Test inventory valuation report"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/reports/valuation")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "valuation" in data
        valuation = data["valuation"]
        assert "total_items" in valuation
        assert "total_purchase_value" in valuation
        assert "total_sales_value" in valuation
        print(f"✓ Inventory Valuation: {valuation['total_items']} items")


class TestStockLocations:
    """Test Stock Locations operations"""
    
    def test_create_stock_location(self):
        """Test creating a stock location"""
        # First create an item
        unique_name = f"TEST_SLItem_{uuid.uuid4().hex[:6]}"
        item_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0
        })
        item_id = item_response.json()["item"]["item_id"]
        
        # Get a warehouse
        wh_response = requests.get(f"{BASE_URL}/api/items-enhanced/warehouses")
        warehouses = wh_response.json()["warehouses"]
        warehouse_id = warehouses[0]["warehouse_id"] if warehouses else None
        
        if warehouse_id:
            payload = {
                "item_id": item_id,
                "warehouse_id": warehouse_id,
                "stock": 100
            }
            response = requests.post(f"{BASE_URL}/api/items-enhanced/stock-locations", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            print(f"✓ Created stock location for item: {item_id}")
    
    def test_get_item_stock_locations(self):
        """Test getting stock locations for an item"""
        # First create an item
        unique_name = f"TEST_GetSL_{uuid.uuid4().hex[:6]}"
        item_response = requests.post(f"{BASE_URL}/api/items-enhanced/", json={
            "name": unique_name,
            "item_type": "inventory",
            "sales_rate": 500.0,
            "initial_stock": 50
        })
        item_id = item_response.json()["item"]["item_id"]
        
        # Get stock locations
        response = requests.get(f"{BASE_URL}/api/items-enhanced/{item_id}/stock-locations")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "stock_locations" in data
        print(f"✓ Retrieved stock locations for item: {item_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
