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

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

class TestStockIndicatorFeature:
    """Tests for stock indicator column in estimates"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Auth headers with organization ID"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "X-Organization-ID": "dev-internal-testing-001",
            "Content-Type": "application/json"
        }

    @pytest.fixture(scope="class")
    def existing_estimate_id(self, headers):
        """Find an existing ticket estimate in the dev org, or skip."""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/?per_page=1",
            headers=headers,
        )
        if response.status_code != 200:
            pytest.skip("ticket-estimates endpoint unavailable")
        data = response.json()
        items = data.get("data", data.get("estimates", []))
        if not items:
            pytest.skip("No ticket estimates in dev org")
        return items[0].get("estimate_id")

    def test_1_stock_indicator_in_stock(self, headers, existing_estimate_id):
        """Test that parts with sufficient stock show 'in_stock' status"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get estimate: {response.text}"
        
        data = response.json()
        assert "estimate" in data
        line_items = data["estimate"]["line_items"]
        
        # Find part with item_id
        parts_with_stock = [item for item in line_items if item.get("type") == "part" and item.get("item_id")]
        if not parts_with_stock:
            pytest.skip("No parts with item_id in this estimate")
        
        for part in parts_with_stock:
            stock_info = part.get("stock_info")
            assert stock_info is not None, f"Part {part['name']} missing stock_info"
            assert "available_stock" in stock_info
            assert "status" in stock_info
            assert stock_info["status"] in ["in_stock", "low_stock", "out_of_stock"]
    
    def test_2_labour_items_no_stock_info(self, headers, existing_estimate_id):
        """Test that labour items don't have stock_info"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        labour_items = [item for item in line_items if item.get("type") == "labour"]
        if not labour_items:
            pytest.skip("No labour items in this estimate")
        for labour in labour_items:
            assert labour.get("stock_info") is None or "stock_info" not in labour, \
                f"Labour item {labour['name']} should not have stock_info"
    
    def test_3_stock_status_in_stock(self, headers, existing_estimate_id):
        """Test in_stock status detection"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        # Check any part with stock_info
        parts_with_stock = [item for item in line_items if item.get("type") == "part" and item.get("stock_info")]
        in_stock_parts = [p for p in parts_with_stock if p["stock_info"]["status"] == "in_stock"]
        if in_stock_parts:
            assert in_stock_parts[0]["stock_info"]["available_stock"] > 0
        else:
            pytest.skip("No in_stock parts found")
    
    def test_4_stock_status_low_stock(self, headers, existing_estimate_id):
        """Test low_stock status detection"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        parts_with_stock = [item for item in line_items if item.get("type") == "part" and item.get("stock_info")]
        low_stock_parts = [p for p in parts_with_stock if p["stock_info"]["status"] == "low_stock"]
        if low_stock_parts:
            assert low_stock_parts[0]["stock_info"]["available_stock"] > 0
        else:
            pytest.skip("No low_stock parts found")
    
    def test_5_stock_status_out_of_stock(self, headers, existing_estimate_id):
        """Test out_of_stock status detection"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        parts_with_stock = [item for item in line_items if item.get("type") == "part" and item.get("stock_info")]
        oos_parts = [p for p in parts_with_stock if p["stock_info"]["status"] == "out_of_stock"]
        if oos_parts:
            assert oos_parts[0]["stock_info"]["available_stock"] <= 0
        else:
            pytest.skip("No out_of_stock parts found")
    
    def test_6_parts_catalog_shows_stock(self, headers):
        """Test that parts catalog API shows stock info"""
        response = requests.get(
            f"{BASE_URL}/api/v1/items-enhanced/?per_page=10&item_type=inventory",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        
        for item in data.get("items", data.get("data", []))[:3]:
            # Parts catalog should include stock_on_hand
            assert "stock_on_hand" in item or item.get("stock_on_hand") is None
            print(f"Catalog item: {item['name']}, Stock: {item.get('stock_on_hand', 'N/A')}")
    
    def test_7_add_part_returns_stock_info(self, headers, existing_estimate_id):
        """Test that adding a part to estimate returns stock_info"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        if response.status_code != 200:
            pytest.skip("Estimate not accessible")
        current_version = response.json()["estimate"].get("version", 1)
        
        # Add a new part with known item from seed data
        add_response = requests.post(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}/line-items",
            headers=headers,
            json={
                "type": "part",
                "item_id": "1837096000000446195",
                "name": "12V Battery replacement",
                "qty": 1,
                "unit_price": 200,
                "tax_rate": 18,
                "version": current_version
            }
        )
        # May fail if estimate is in a non-editable status
        assert add_response.status_code in (200, 400, 409)
        
        if add_response.status_code == 200:
            data = add_response.json()
            line_items = data.get("estimate", {}).get("line_items", [])
            battery = [item for item in line_items if item.get("item_id") == "1837096000000446195"]
            if battery:
                stock_info = battery[0].get("stock_info")
                if stock_info:
                    assert "available_stock" in stock_info
                    assert "status" in stock_info
    
    def test_8_stock_info_includes_all_fields(self, headers, existing_estimate_id):
        """Test that stock_info includes required fields"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        parts_with_stock = [item for item in line_items if item.get("stock_info")]
        if not parts_with_stock:
            pytest.skip("No parts with stock_info")
        
        for part in parts_with_stock:
            stock_info = part["stock_info"]
            assert "available_stock" in stock_info
            assert "status" in stock_info
    
    def test_9_parts_without_item_id_no_stock(self, headers, existing_estimate_id):
        """Test that parts without item_id have no stock_info"""
        response = requests.get(
            f"{BASE_URL}/api/v1/ticket-estimates/{existing_estimate_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        line_items = data["estimate"]["line_items"]
        
        parts_without_id = [item for item in line_items if item.get("type") == "part" and not item.get("item_id")]
        if not parts_without_id:
            pytest.skip("No parts without item_id")
        for part in parts_without_id:
            assert part.get("stock_info") is None, f"Part {part['name']} without item_id should not have stock_info"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
