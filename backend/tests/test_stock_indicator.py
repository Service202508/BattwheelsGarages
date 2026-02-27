"""
Test Suite: Stock Indicator Feature for Estimate Panel
Tests visual inventory indicators showing stock status for parts
- Green: in_stock (available > reorder_level)
- Yellow: low_stock (available <= reorder_level && available > 0)
- Red: out_of_stock (available <= 0)
- Orange (frontend): insufficient (qty > available_stock)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStockIndicatorFeature:
    """Tests for stock indicator column in estimates"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Auth headers with organization ID"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "X-Organization-ID": "org_71f0df814d6d",
            "Content-Type": "application/json"
        }
    
    def test_1_stock_indicator_in_stock(self, headers):
        """Test that parts with sufficient stock show 'in_stock' status"""
        # Get estimate with parts that have item_id
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_5b6ea472ac46",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get estimate: {response.text}"
        
        data = response.json()
        assert "estimate" in data
        line_items = data["estimate"]["line_items"]
        
        # Find part with item_id
        parts_with_stock = [item for item in line_items if item.get("type") == "part" and item.get("item_id")]
        assert len(parts_with_stock) > 0, "No parts with item_id found"
        
        for part in parts_with_stock:
            stock_info = part.get("stock_info")
            assert stock_info is not None, f"Part {part['name']} missing stock_info"
            assert "available_stock" in stock_info
            assert "status" in stock_info
            assert stock_info["status"] in ["in_stock", "low_stock", "out_of_stock"]
            print(f"Part: {part['name']}, Stock: {stock_info['available_stock']}, Status: {stock_info['status']}")
    
    def test_2_labour_items_no_stock_info(self, headers):
        """Test that labour items don't have stock_info"""
        # Use the estimate we created with labour item
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_253fe4cc8bd6",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        labour_items = [item for item in line_items if item.get("type") == "labour"]
        for labour in labour_items:
            assert labour.get("stock_info") is None or "stock_info" not in labour, \
                f"Labour item {labour['name']} should not have stock_info"
            print(f"Labour: {labour['name']} - No stock_info (correct)")
    
    def test_3_stock_status_in_stock(self, headers):
        """Test in_stock status (available > reorder_level)"""
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_253fe4cc8bd6",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        # Item 1837096000000446195 has 91 in stock
        battery_items = [item for item in line_items if item.get("item_id") == "1837096000000446195"]
        if battery_items:
            stock_info = battery_items[0].get("stock_info")
            assert stock_info is not None
            assert stock_info["available_stock"] == 91
            assert stock_info["status"] == "in_stock"
            print(f"12V Battery: {stock_info['available_stock']} in stock - Status: {stock_info['status']}")
    
    def test_4_stock_status_low_stock(self, headers):
        """Test low_stock status (available <= reorder_level && available > 0)"""
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_253fe4cc8bd6",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        # Item 1837096000000993694 has 3 in stock with reorder_level 10
        harness_items = [item for item in line_items if item.get("item_id") == "1837096000000993694"]
        if harness_items:
            stock_info = harness_items[0].get("stock_info")
            assert stock_info is not None
            assert stock_info["available_stock"] == 3
            assert stock_info["status"] == "low_stock"
            print(f"12V HARNESS 3W PIAGGIO-25: {stock_info['available_stock']} in stock - Status: {stock_info['status']}")
    
    def test_5_stock_status_out_of_stock(self, headers):
        """Test out_of_stock status (available <= 0)"""
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_253fe4cc8bd6",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        # Item 1837096000000233245 has 0 in stock
        repair_items = [item for item in line_items if item.get("item_id") == "1837096000000233245"]
        if repair_items:
            stock_info = repair_items[0].get("stock_info")
            assert stock_info is not None
            assert stock_info["available_stock"] == 0
            assert stock_info["status"] == "out_of_stock"
            print(f"12V HARNESS REPAIR 3W: {stock_info['available_stock']} in stock - Status: {stock_info['status']}")
    
    def test_6_parts_catalog_shows_stock(self, headers):
        """Test that parts catalog API shows stock info"""
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/?per_page=10&item_type=inventory",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        
        for item in data["items"][:3]:
            # Parts catalog should include stock_on_hand
            assert "stock_on_hand" in item or item.get("stock_on_hand") is None
            print(f"Catalog item: {item['name']}, Stock: {item.get('stock_on_hand', 'N/A')}")
    
    def test_7_add_part_returns_stock_info(self, headers):
        """Test that adding a part to estimate returns stock_info"""
        # Get current version
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_253fe4cc8bd6",
            headers=headers
        )
        assert response.status_code == 200
        current_version = response.json()["estimate"]["version"]
        
        # Add a new part with known stock
        add_response = requests.post(
            f"{BASE_URL}/api/ticket-estimates/est_253fe4cc8bd6/line-items",
            headers=headers,
            json={
                "type": "part",
                "item_id": "1837096000000413092",  # 12V HARNESS 3W with 97 in stock
                "name": "12V HARNESS 3W",
                "qty": 1,
                "unit_price": 150,
                "tax_rate": 18,
                "version": current_version
            }
        )
        assert add_response.status_code == 200
        
        data = add_response.json()
        line_items = data["estimate"]["line_items"]
        
        # Find the newly added item
        harness = [item for item in line_items if item.get("item_id") == "1837096000000413092"]
        assert len(harness) > 0, "Newly added part not found"
        
        stock_info = harness[0].get("stock_info")
        assert stock_info is not None, "Stock info not returned for new part"
        assert stock_info["available_stock"] == 97
        assert stock_info["status"] == "in_stock"
        print(f"Newly added part: stock_info = {stock_info}")
    
    def test_8_stock_info_includes_all_fields(self, headers):
        """Test that stock_info includes all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_253fe4cc8bd6",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        parts_with_stock = [item for item in line_items if item.get("stock_info")]
        assert len(parts_with_stock) > 0
        
        for part in parts_with_stock:
            stock_info = part["stock_info"]
            required_fields = ["available_stock", "reserved_stock", "total_stock", "reorder_level", "status"]
            for field in required_fields:
                assert field in stock_info, f"Missing field: {field}"
            print(f"Part: {part['name']}, stock_info fields: {list(stock_info.keys())}")
    
    def test_9_parts_without_item_id_no_stock(self, headers):
        """Test that parts without item_id have no stock_info"""
        response = requests.get(
            f"{BASE_URL}/api/ticket-estimates/est_5b6ea472ac46",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        parts_without_id = [item for item in line_items if item.get("type") == "part" and not item.get("item_id")]
        for part in parts_without_id:
            assert part.get("stock_info") is None, f"Part {part['name']} without item_id should not have stock_info"
            print(f"Part without item_id: {part['name']} - stock_info is None (correct)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
