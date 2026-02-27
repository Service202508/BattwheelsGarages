"""
Test: Parts Catalog in Add Item to Estimate dialog
Bug Fix: Trailing slash issue in GET /api/items-enhanced/ endpoint

Tests:
1. GET /api/items-enhanced/ returns inventory items (with trailing slash)
2. Items are loaded when popover opens (no search required)
3. Search filters items correctly
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestItemsEnhancedPartsFix:
    """Test the parts dropdown fix for Estimate Items dialog"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for API calls"""
        self.headers = {"Content-Type": "application/json"}
        
        # Login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@battwheels.in", "password": "DevTest@123"},
            headers=self.headers
        )
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.headers["Authorization"] = f"Bearer {token}"
    
    def test_items_enhanced_with_trailing_slash(self):
        """Test: GET /api/items-enhanced/ with trailing slash returns items"""
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/?per_page=20&item_type=inventory",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert len(data["items"]) > 0, "Should return at least one item"
        
        # Verify item structure
        item = data["items"][0]
        assert "name" in item, "Item should have 'name'"
        assert "item_id" in item, "Item should have 'item_id'"
        assert "rate" in item or "selling_price" in item, "Item should have 'rate' or 'selling_price'"
        
        print(f"SUCCESS: GET /api/items-enhanced/ returned {len(data['items'])} items")
    
    def test_items_enhanced_without_search_query(self):
        """Test: Items load without search query (initial load when popover opens)"""
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/?per_page=20&item_type=inventory",
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        items = data["items"]
        
        # Should return items without needing search query
        assert len(items) > 0, "Should return items even without search query"
        
        print(f"SUCCESS: Initial load returned {len(items)} items (no search query)")
    
    def test_items_enhanced_with_search_query(self):
        """Test: Search filters items correctly"""
        search_term = "motor"
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/?per_page=20&item_type=inventory&search={search_term}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        items = data["items"]
        
        # If items returned, verify they match search
        if len(items) > 0:
            # At least one item should contain search term in name or description
            has_match = any(
                search_term.lower() in (item.get("name", "") or "").lower() or
                search_term.lower() in (item.get("description", "") or "").lower() or
                search_term.lower() in (item.get("sku", "") or "").lower()
                for item in items
            )
            assert has_match, f"Items should match search term '{search_term}'"
        
        print(f"SUCCESS: Search for '{search_term}' returned {len(items)} matching items")
    
    def test_items_enhanced_inventory_type_filter(self):
        """Test: item_type=inventory filter works"""
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/?per_page=20&item_type=inventory",
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # All returned items should be inventory type
        for item in items:
            item_type = item.get("item_type", "")
            assert item_type == "inventory", f"Item {item.get('name')} has type '{item_type}', expected 'inventory'"
        
        print(f"SUCCESS: All {len(items)} items have item_type='inventory'")
    
    def test_items_have_required_fields_for_estimate(self):
        """Test: Items have fields needed for estimate line items"""
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/?per_page=5&item_type=inventory",
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        assert len(items) > 0
        
        required_fields = ["item_id", "name"]
        price_fields = ["rate", "selling_price"]
        
        for item in items:
            # Check required fields
            for field in required_fields:
                assert field in item, f"Item missing required field '{field}'"
            
            # Check at least one price field exists
            has_price = any(field in item for field in price_fields)
            assert has_price, f"Item {item.get('name')} missing price field"
        
        # Check for optional but useful fields
        sample_item = items[0]
        useful_fields = ["hsn_code", "tax_percentage", "unit", "sku"]
        available_fields = [f for f in useful_fields if f in sample_item]
        print(f"SUCCESS: Items have required fields. Optional fields available: {available_fields}")


class TestItemsEnhancedPagination:
    """Test pagination for large catalogs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.headers = {"Content-Type": "application/json"}
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@battwheels.in", "password": "DevTest@123"},
            headers=self.headers
        )
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.headers["Authorization"] = f"Bearer {token}"
    
    def test_pagination_context(self):
        """Test: Response includes pagination context"""
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/?per_page=5&page=1&item_type=inventory",
            headers=self.headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "page_context" in data, "Response should include page_context"
        
        page_context = data["page_context"]
        assert "page" in page_context
        assert "per_page" in page_context
        assert "total" in page_context
        
        print(f"SUCCESS: Pagination context - page: {page_context['page']}, per_page: {page_context['per_page']}, total: {page_context['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
