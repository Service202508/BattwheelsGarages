"""
Items Module Phase 2 Enhancement Tests
Testing: Contact Price Lists, Line Item Pricing, Bulk Price Setting, Barcode/QR, Advanced Reports
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestContactPriceLists:
    """Test contact price list assignment feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get existing contacts
        response = self.session.get(f"{BASE_URL}/api/contacts-enhanced/")
        if response.status_code == 200:
            contacts = response.json().get("contacts", [])
            if contacts:
                self.test_contact_id = contacts[0].get("contact_id")
            else:
                self.test_contact_id = None
        else:
            self.test_contact_id = None
            
        # Get existing price lists
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/price-lists")
        if response.status_code == 200:
            price_lists = response.json().get("price_lists", [])
            if price_lists:
                self.test_price_list_id = price_lists[0].get("pricelist_id")
            else:
                self.test_price_list_id = None
        else:
            self.test_price_list_id = None
    
    def test_assign_price_list_to_contact(self):
        """Test POST /api/items-enhanced/contact-price-lists"""
        if not self.test_contact_id or not self.test_price_list_id:
            pytest.skip("No test contact or price list available")
        
        payload = {
            "contact_id": self.test_contact_id,
            "sales_price_list_id": self.test_price_list_id
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/contact-price-lists",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "message" in data
        print(f"✓ Assigned price list {self.test_price_list_id} to contact {self.test_contact_id}")
    
    def test_get_contact_price_lists(self):
        """Test GET /api/items-enhanced/contact-price-lists/{contact_id}"""
        if not self.test_contact_id:
            pytest.skip("No test contact available")
        
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/contact-price-lists/{self.test_contact_id}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "contact_price_lists" in data
        
        contact_pl = data["contact_price_lists"]
        assert "contact_id" in contact_pl
        assert "contact_name" in contact_pl
        print(f"✓ Retrieved price lists for contact: {contact_pl.get('contact_name')}")
    
    def test_get_contact_price_lists_not_found(self):
        """Test GET /api/items-enhanced/contact-price-lists/{contact_id} with invalid ID"""
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/contact-price-lists/INVALID-CONTACT-ID"
        )
        
        assert response.status_code == 404
        print("✓ Returns 404 for invalid contact ID")


class TestLineItemPricing:
    """Test line item pricing calculation feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get existing items
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/?per_page=5")
        if response.status_code == 200:
            items = response.json().get("items", [])
            self.test_items = [item.get("item_id") for item in items[:3] if item.get("item_id")]
        else:
            self.test_items = []
            
        # Get existing contacts
        response = self.session.get(f"{BASE_URL}/api/contacts-enhanced/?per_page=1")
        if response.status_code == 200:
            contacts = response.json().get("contacts", [])
            if contacts:
                self.test_contact_id = contacts[0].get("contact_id")
            else:
                self.test_contact_id = None
        else:
            self.test_contact_id = None
    
    def test_calculate_line_prices_basic(self):
        """Test POST /api/items-enhanced/calculate-line-prices - basic calculation"""
        if not self.test_items:
            pytest.skip("No test items available")
        
        payload = {
            "items": [
                {"item_id": self.test_items[0], "quantity": 2}
            ],
            "transaction_type": "sales"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/calculate-line-prices",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "line_items" in data
        # API returns total_amount, not total
        assert "total_amount" in data or "total" in data
        
        if data["line_items"]:
            line_item = data["line_items"][0]
            assert "item_id" in line_item
            assert "quantity" in line_item
            # Check for rate fields
            assert "final_rate" in line_item or "rate" in line_item
            assert "amount" in line_item
        total = data.get("total_amount") or data.get("total", 0)
        print(f"✓ Calculated line prices, total: {total}")
    
    def test_calculate_line_prices_with_contact(self):
        """Test POST /api/items-enhanced/calculate-line-prices - with contact price list"""
        if not self.test_items or not self.test_contact_id:
            pytest.skip("No test items or contact available")
        
        payload = {
            "items": [
                {"item_id": self.test_items[0], "quantity": 1}
            ],
            "contact_id": self.test_contact_id,
            "transaction_type": "sales"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/calculate-line-prices",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        total = data.get("total_amount") or data.get("total", 0)
        print(f"✓ Calculated line prices with contact, total: {total}")
    
    def test_calculate_line_prices_multiple_items(self):
        """Test POST /api/items-enhanced/calculate-line-prices - multiple items"""
        if len(self.test_items) < 2:
            pytest.skip("Need at least 2 test items")
        
        payload = {
            "items": [
                {"item_id": self.test_items[0], "quantity": 2},
                {"item_id": self.test_items[1], "quantity": 3}
            ],
            "transaction_type": "sales"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/calculate-line-prices",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert len(data.get("line_items", [])) >= 1  # At least one item should be returned
        total = data.get("total_amount") or data.get("total", 0)
        print(f"✓ Calculated prices for multiple items, total: {total}")


class TestBulkPriceSetting:
    """Test bulk price setting for price lists"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Create a test price list
        unique_id = uuid.uuid4().hex[:6]
        payload = {
            "name": f"TEST_BulkPL_{unique_id}",
            "description": "Test price list for bulk pricing",
            "discount_percentage": 0,
            "markup_percentage": 0,
            "is_active": True
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/price-lists",
            json=payload
        )
        
        if response.status_code == 200:
            self.test_price_list_id = response.json().get("price_list", {}).get("pricelist_id")
        else:
            self.test_price_list_id = None
            
        # Get existing items
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/?per_page=5")
        if response.status_code == 200:
            items = response.json().get("items", [])
            self.test_items = [item.get("item_id") for item in items[:3] if item.get("item_id")]
        else:
            self.test_items = []
    
    def test_set_bulk_prices_percentage(self):
        """Test POST /api/items-enhanced/price-lists/{id}/set-prices - percentage method"""
        if not self.test_price_list_id:
            pytest.skip("No test price list available")
        
        payload = {
            "price_list_id": self.test_price_list_id,
            "pricing_method": "percentage",
            "percentage": 10  # 10% markup
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/price-lists/{self.test_price_list_id}/set-prices",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        # API returns results with created/updated counts
        assert "results" in data or "items_updated" in data
        results = data.get("results", {})
        items_updated = results.get("created", 0) + results.get("updated", 0) if results else data.get("items_updated", 0)
        print(f"✓ Set bulk prices with 10% markup, items updated: {items_updated}")
    
    def test_set_bulk_prices_custom(self):
        """Test POST /api/items-enhanced/price-lists/{id}/set-prices - custom method"""
        if not self.test_price_list_id or not self.test_items:
            pytest.skip("No test price list or items available")
        
        payload = {
            "price_list_id": self.test_price_list_id,
            "pricing_method": "custom",
            "items": [
                {"item_id": self.test_items[0], "custom_rate": 999.99}
            ]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/price-lists/{self.test_price_list_id}/set-prices",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        results = data.get("results", {})
        items_updated = results.get("created", 0) + results.get("updated", 0) if results else data.get("items_updated", 0)
        print(f"✓ Set custom prices, items updated: {items_updated}")


class TestBarcodeFeatures:
    """Test barcode/QR code features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get existing items
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/?per_page=5")
        if response.status_code == 200:
            items = response.json().get("items", [])
            if items:
                self.test_item_id = items[0].get("item_id")
                self.test_item_sku = items[0].get("sku")
            else:
                self.test_item_id = None
                self.test_item_sku = None
        else:
            self.test_item_id = None
            self.test_item_sku = None
    
    def test_create_barcode(self):
        """Test POST /api/items-enhanced/barcodes"""
        if not self.test_item_id:
            pytest.skip("No test item available")
        
        unique_barcode = f"BC{uuid.uuid4().hex[:10].upper()}"
        payload = {
            "item_id": self.test_item_id,
            "barcode_type": "CODE128",
            "barcode_value": unique_barcode
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/barcodes",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        print(f"✓ Created barcode: {unique_barcode}")
    
    def test_barcode_lookup(self):
        """Test GET /api/items-enhanced/lookup/barcode/{value}"""
        if not self.test_item_id:
            pytest.skip("No test item available")
        
        # First create a barcode
        unique_barcode = f"BC{uuid.uuid4().hex[:10].upper()}"
        payload = {
            "item_id": self.test_item_id,
            "barcode_type": "CODE128",
            "barcode_value": unique_barcode
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/barcodes",
            json=payload
        )
        assert create_response.status_code == 200
        
        # Now lookup
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/lookup/barcode/{unique_barcode}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "item" in data
        print(f"✓ Barcode lookup successful, found item: {data.get('item', {}).get('name')}")
    
    def test_barcode_lookup_not_found(self):
        """Test GET /api/items-enhanced/lookup/barcode/{value} - not found"""
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/lookup/barcode/NONEXISTENT-BARCODE-12345"
        )
        
        # Should return 404 for non-existent barcode
        assert response.status_code == 404
        print("✓ Returns 404 for non-existent barcode")
    
    def test_batch_barcode_lookup(self):
        """Test POST /api/items-enhanced/lookup/batch"""
        if not self.test_item_id:
            pytest.skip("No test item available")
        
        # Create a barcode first
        unique_barcode = f"BC{uuid.uuid4().hex[:10].upper()}"
        payload = {
            "item_id": self.test_item_id,
            "barcode_type": "CODE128",
            "barcode_value": unique_barcode
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/barcodes",
            json=payload
        )
        assert create_response.status_code == 200
        
        # Batch lookup - API expects a list directly
        batch_payload = [unique_barcode, "NONEXISTENT-123"]
        
        response = self.session.post(
            f"{BASE_URL}/api/items-enhanced/lookup/batch",
            json=batch_payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "results" in data
        print(f"✓ Batch lookup returned {len(data.get('results', []))} results")


class TestAdvancedReports:
    """Test advanced reports: Sales by Item, Purchases by Item, Inventory Valuation, Item Movement"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_sales_by_item_report(self):
        """Test GET /api/items-enhanced/reports/sales-by-item"""
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/reports/sales-by-item"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        # Report data is nested under "report" key
        assert "report" in data
        report = data["report"]
        assert "items" in report
        assert "summary" in report
        
        summary = report.get("summary", {})
        assert "total_revenue" in summary or "total_quantity_sold" in summary
        print(f"✓ Sales by Item report: {len(report.get('items', []))} items, total revenue: {summary.get('total_revenue', 0)}")
    
    def test_sales_by_item_report_with_filters(self):
        """Test GET /api/items-enhanced/reports/sales-by-item with date filters"""
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/reports/sales-by-item",
            params={
                "start_date": "2024-01-01",
                "end_date": "2026-12-31"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        report = data.get("report", {})
        print(f"✓ Sales by Item report with date filter: {len(report.get('items', []))} items")
    
    def test_purchases_by_item_report(self):
        """Test GET /api/items-enhanced/reports/purchases-by-item"""
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/reports/purchases-by-item"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        # Report data is nested under "report" key
        assert "report" in data
        report = data["report"]
        assert "items" in report
        assert "summary" in report
        
        summary = report.get("summary", {})
        print(f"✓ Purchases by Item report: {len(report.get('items', []))} items, total cost: {summary.get('total_cost', 0)}")
    
    def test_inventory_valuation_report(self):
        """Test GET /api/items-enhanced/reports/inventory-valuation"""
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/reports/inventory-valuation"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        # Report data is nested under "report" key
        assert "report" in data
        report = data["report"]
        assert "items" in report
        assert "summary" in report
        
        summary = report.get("summary", {})
        assert "total_stock_value" in summary or "total_items" in summary
        print(f"✓ Inventory Valuation report: {len(report.get('items', []))} items, total value: {summary.get('total_stock_value', 0)}")
    
    def test_item_movement_report(self):
        """Test GET /api/items-enhanced/reports/item-movement - requires item_id"""
        # Get an item first
        items_response = self.session.get(f"{BASE_URL}/api/items-enhanced/?per_page=1")
        if items_response.status_code != 200:
            pytest.skip("Could not get items")
        
        items = items_response.json().get("items", [])
        if not items:
            pytest.skip("No items available")
        
        item_id = items[0].get("item_id")
        
        # Item movement requires item_id parameter
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/reports/item-movement",
            params={"item_id": item_id}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        print(f"✓ Item Movement report retrieved successfully")
    
    def test_item_movement_report_with_date_filter(self):
        """Test GET /api/items-enhanced/reports/item-movement with date filter"""
        # Get an item first
        items_response = self.session.get(f"{BASE_URL}/api/items-enhanced/?per_page=1")
        if items_response.status_code != 200:
            pytest.skip("Could not get items")
        
        items = items_response.json().get("items", [])
        if not items:
            pytest.skip("No items available")
        
        item_id = items[0].get("item_id")
        
        response = self.session.get(
            f"{BASE_URL}/api/items-enhanced/reports/item-movement",
            params={
                "item_id": item_id,
                "start_date": "2024-01-01",
                "end_date": "2026-12-31"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        print(f"✓ Item Movement report with date filter retrieved")


class TestExistingPhase1Features:
    """Verify Phase 1 features still work after Phase 2 additions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_items_list(self):
        """Test GET /api/items-enhanced/ still works"""
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "items" in data
        print(f"✓ Items list: {len(data.get('items', []))} items")
    
    def test_price_lists(self):
        """Test GET /api/items-enhanced/price-lists still works"""
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/price-lists")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "price_lists" in data
        print(f"✓ Price lists: {len(data.get('price_lists', []))} lists")
    
    def test_groups(self):
        """Test GET /api/items-enhanced/groups still works"""
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/groups")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "groups" in data
        print(f"✓ Groups: {len(data.get('groups', []))} groups")
    
    def test_warehouses(self):
        """Test GET /api/items-enhanced/warehouses still works"""
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/warehouses")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "warehouses" in data
        print(f"✓ Warehouses: {len(data.get('warehouses', []))} warehouses")
    
    def test_summary(self):
        """Test GET /api/items-enhanced/summary still works"""
        response = self.session.get(f"{BASE_URL}/api/items-enhanced/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "summary" in data
        print(f"✓ Summary: {data.get('summary', {}).get('total_items', 0)} total items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
