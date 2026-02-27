"""
Test Items, Price Lists, and Inventory Adjustments APIs
Tests for the new Catalog & Inventory module features
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://trial-ready.preview.emergentagent.com').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "DevTest@123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")

@pytest.fixture
def api_client(auth_token):
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestItemsAPI:
    """Items CRUD API tests"""
    
    def test_list_items(self, api_client):
        """Test listing items"""
        response = api_client.get(f"{BASE_URL}/api/zoho/items?per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"SUCCESS: Listed {len(data['items'])} items")
    
    def test_list_items_filter_by_type(self, api_client):
        """Test filtering items by type"""
        # Test goods filter
        response = api_client.get(f"{BASE_URL}/api/zoho/items?item_type=goods&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"SUCCESS: Listed {len(data['items'])} goods items")
        
        # Test service filter
        response = api_client.get(f"{BASE_URL}/api/zoho/items?item_type=service&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"SUCCESS: Listed {len(data['items'])} service items")
    
    def test_search_items(self, api_client):
        """Test searching items"""
        response = api_client.get(f"{BASE_URL}/api/zoho/items?search_text=battery&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"SUCCESS: Search returned {len(data['items'])} items")
    
    def test_create_item(self, api_client):
        """Test creating a new item"""
        test_item = {
            "name": f"TEST_Item_{uuid.uuid4().hex[:8]}",
            "sku": f"TEST-SKU-{uuid.uuid4().hex[:6]}",
            "description": "Test item for automated testing",
            "item_type": "goods",
            "rate": 1500.00,
            "purchase_rate": 1000.00,
            "tax_percentage": 18,
            "hsn_or_sac": "998745",
            "unit": "pcs",
            "stock_on_hand": 100,
            "reorder_level": 10,
            "is_taxable": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/zoho/items", json=test_item)
        assert response.status_code == 200, f"Create item failed: {response.text}"
        data = response.json()
        assert "item" in data or "item_id" in data or data.get("code") == 0
        print(f"SUCCESS: Created item")
        
        # Return item_id for cleanup
        return data.get("item", {}).get("item_id") or data.get("item_id")


class TestPriceListsAPI:
    """Price Lists CRUD API tests"""
    
    def test_list_price_lists(self, api_client):
        """Test listing price lists"""
        response = api_client.get(f"{BASE_URL}/api/zoho/price-lists")
        assert response.status_code == 200
        data = response.json()
        assert "price_lists" in data
        assert isinstance(data["price_lists"], list)
        print(f"SUCCESS: Listed {len(data['price_lists'])} price lists")
    
    def test_create_price_list(self, api_client):
        """Test creating a new price list"""
        test_price_list = {
            "price_list_name": f"TEST_PriceList_{uuid.uuid4().hex[:8]}",
            "description": "Test price list for automated testing",
            "currency_code": "INR",
            "price_type": "sales",
            "is_default": False,
            "round_off_to": "never"
        }
        
        response = api_client.post(f"{BASE_URL}/api/zoho/price-lists", json=test_price_list)
        assert response.status_code == 200, f"Create price list failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "price_list" in data
        
        price_list_id = data["price_list"]["price_list_id"]
        print(f"SUCCESS: Created price list with ID: {price_list_id}")
        
        return price_list_id
    
    def test_add_item_to_price_list(self, api_client):
        """Test adding an item to a price list"""
        # First create a price list
        test_price_list = {
            "price_list_name": f"TEST_PL_AddItem_{uuid.uuid4().hex[:8]}",
            "description": "Test price list for adding items",
            "currency_code": "INR",
            "price_type": "sales",
            "is_default": False,
            "round_off_to": "never"
        }
        
        response = api_client.post(f"{BASE_URL}/api/zoho/price-lists", json=test_price_list)
        assert response.status_code == 200
        price_list_id = response.json()["price_list"]["price_list_id"]
        
        # Get an existing item
        items_response = api_client.get(f"{BASE_URL}/api/zoho/items?per_page=1")
        assert items_response.status_code == 200
        items = items_response.json().get("items", [])
        
        if items:
            item_id = items[0].get("item_id")
            custom_rate = 999.99
            
            # Add item to price list
            add_response = api_client.post(
                f"{BASE_URL}/api/zoho/price-lists/{price_list_id}/items?item_id={item_id}&custom_rate={custom_rate}"
            )
            assert add_response.status_code == 200
            assert add_response.json().get("code") == 0
            print(f"SUCCESS: Added item {item_id} to price list {price_list_id}")
        else:
            print("WARNING: No items available to add to price list")


class TestInventoryAdjustmentsAPI:
    """Inventory Adjustments CRUD API tests"""
    
    def test_list_inventory_adjustments(self, api_client):
        """Test listing inventory adjustments"""
        response = api_client.get(f"{BASE_URL}/api/zoho/inventory-adjustments")
        assert response.status_code == 200
        data = response.json()
        assert "inventory_adjustments" in data
        assert isinstance(data["inventory_adjustments"], list)
        print(f"SUCCESS: Listed {len(data['inventory_adjustments'])} inventory adjustments")
    
    def test_create_inventory_adjustment(self, api_client):
        """Test creating a new inventory adjustment"""
        # Get an existing goods item
        items_response = api_client.get(f"{BASE_URL}/api/zoho/items?item_type=goods&per_page=1")
        assert items_response.status_code == 200
        items = items_response.json().get("items", [])
        
        if items:
            item = items[0]
            item_id = item.get("item_id")
            item_name = item.get("name")
            current_stock = item.get("stock_on_hand", 0)
            
            test_adjustment = {
                "adjustment_type": "quantity",
                "reason": "damaged",
                "description": "Test adjustment for automated testing",
                "reference_number": f"TEST-ADJ-{uuid.uuid4().hex[:6]}",
                "line_items": [
                    {
                        "item_id": item_id,
                        "item_name": item_name,
                        "quantity_adjusted": -5,
                        "new_quantity": max(0, current_stock - 5)
                    }
                ]
            }
            
            response = api_client.post(f"{BASE_URL}/api/zoho/inventory-adjustments", json=test_adjustment)
            assert response.status_code == 200, f"Create adjustment failed: {response.text}"
            data = response.json()
            assert data.get("code") == 0
            assert "adjustment" in data
            
            adjustment_id = data["adjustment"]["adjustment_id"]
            print(f"SUCCESS: Created inventory adjustment with ID: {adjustment_id}")
            
            return adjustment_id
        else:
            print("WARNING: No goods items available for inventory adjustment test")
            pytest.skip("No goods items available")
    
    def test_list_adjustments_by_reason(self, api_client):
        """Test filtering adjustments by reason"""
        response = api_client.get(f"{BASE_URL}/api/zoho/inventory-adjustments?reason=damaged")
        assert response.status_code == 200
        data = response.json()
        assert "inventory_adjustments" in data
        print(f"SUCCESS: Listed {len(data['inventory_adjustments'])} damaged adjustments")


class TestNavigationAndIntegration:
    """Test navigation links and page integration"""
    
    def test_items_endpoint_exists(self, api_client):
        """Verify items endpoint is accessible"""
        response = api_client.get(f"{BASE_URL}/api/zoho/items?per_page=1")
        assert response.status_code == 200
        print("SUCCESS: Items endpoint accessible")
    
    def test_price_lists_endpoint_exists(self, api_client):
        """Verify price lists endpoint is accessible"""
        response = api_client.get(f"{BASE_URL}/api/zoho/price-lists")
        assert response.status_code == 200
        print("SUCCESS: Price Lists endpoint accessible")
    
    def test_inventory_adjustments_endpoint_exists(self, api_client):
        """Verify inventory adjustments endpoint is accessible"""
        response = api_client.get(f"{BASE_URL}/api/zoho/inventory-adjustments")
        assert response.status_code == 200
        print("SUCCESS: Inventory Adjustments endpoint accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
