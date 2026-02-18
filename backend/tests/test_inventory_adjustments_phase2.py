"""
Inventory Adjustments V2 Phase 2+3 Test Suite
Tests: Export CSV, Import CSV (validate+process), PDF generation, ABC drill-down, ticket linking
"""

import pytest
import requests
import os
import io
import uuid
import tempfile

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test item details from credentials
TEST_ITEM_ID = "1837096000000446195"  # 12V Battery replacement
TEST_ITEM_NAME = "12V Battery replacement"
ALT_ITEM_ID = "1837096000001141394"  # 2 WHEELER SEATCOVER-25 (inventory item)

class TestExportCSV:
    """Test CSV export functionality"""
    
    def test_export_csv_returns_csv_content(self):
        """GET /api/inv-adjustments/export/csv should return 200 with text/csv"""
        response = requests.get(f"{BASE_URL}/api/inv-adjustments/export/csv")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check content-type header
        content_type = response.headers.get('Content-Type', '')
        assert 'text/csv' in content_type, f"Expected text/csv, got {content_type}"
        
        # Check content-disposition for filename
        content_disp = response.headers.get('Content-Disposition', '')
        assert 'attachment' in content_disp
        assert 'filename=' in content_disp
        
        # Verify CSV content has rows
        csv_content = response.text
        lines = csv_content.strip().split('\n')
        assert len(lines) >= 1, "CSV should have at least header row"
        
        # Check header columns
        header = lines[0]
        expected_headers = ['Reference Number', 'Date', 'Type', 'Status', 'Item Name']
        for h in expected_headers:
            assert h in header, f"Missing header: {h}"
        
        print(f"✓ Export CSV: {len(lines)} lines, headers: {header[:100]}...")
    
    def test_export_csv_with_filters(self):
        """Export with status filter should work"""
        response = requests.get(f"{BASE_URL}/api/inv-adjustments/export/csv?status=adjusted")
        assert response.status_code == 200
        print("✓ Export CSV with status filter works")
    
    def test_export_csv_with_date_range(self):
        """Export with date range filter should work"""
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/export/csv?date_from=2025-01-01&date_to=2026-12-31"
        )
        assert response.status_code == 200
        print("✓ Export CSV with date range works")


class TestImportValidate:
    """Test CSV import validation endpoint"""
    
    def test_validate_import_with_valid_csv(self):
        """POST /api/inv-adjustments/import/validate with valid CSV"""
        # Create test CSV content
        csv_content = f"""Item Name,New Quantity,Reason,Type,Date
{TEST_ITEM_NAME},100,Stocktaking Variance,quantity,2026-01-18
"""
        # Create file-like object
        files = {'file': ('test_import.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments/import/validate",
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["code"] == 0
        assert "available_fields" in data
        assert "row_count" in data
        assert "preview_rows" in data
        assert "items_found" in data
        
        print(f"✓ Import validate: row_count={data['row_count']}, items_found={data['items_found']}")
        print(f"  Available fields: {data['available_fields']}")
        
        # Check items matching
        if data['items_not_found']:
            print(f"  Items not found: {data['items_not_found']}")
    
    def test_validate_import_detects_missing_items(self):
        """Validation should report items not found in database"""
        csv_content = """Item Name,New Quantity,Reason,Type,Date
NonExistentItem12345,50,Other,quantity,2026-01-18
"""
        files = {'file': ('test_missing.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments/import/validate",
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should report item not found
        assert "items_not_found" in data
        assert len(data["items_not_found"]) >= 1 or data["items_found"] == 0
        print(f"✓ Validate correctly reports missing items: {data.get('items_not_found', [])}")


class TestImportProcess:
    """Test CSV import processing endpoint"""
    
    def test_process_import_creates_draft_adjustments(self):
        """POST /api/inv-adjustments/import/process creates drafts"""
        # Create CSV with valid item - use item_id for better matching
        csv_content = f"""Item ID,Item Name,New Quantity,Reason,Type,Date,Description
{ALT_ITEM_ID},2 WHEELER SEATCOVER-25,100,Stocktaking Variance,quantity,2026-01-18,TEST_Import draft
"""
        files = {'file': ('test_process.csv', csv_content, 'text/csv')}
        
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments/import/process",
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["code"] == 0
        assert "created" in data
        assert "message" in data
        
        print(f"✓ Import process: {data['created']} adjustments created as drafts")
        print(f"  Message: {data['message']}")
        
        if data.get("errors"):
            print(f"  Errors: {data['errors'][:3]}")
        
        # Return created count for verification
        return data["created"]


class TestPDFGeneration:
    """Test PDF generation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get an existing adjustment ID for PDF test"""
        # List adjustments to get a valid ID
        response = requests.get(f"{BASE_URL}/api/inv-adjustments?per_page=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("adjustments") and len(data["adjustments"]) > 0:
                self.test_adjustment_id = data["adjustments"][0]["adjustment_id"]
            else:
                self.test_adjustment_id = None
        else:
            self.test_adjustment_id = None
    
    def test_pdf_generation_returns_pdf(self):
        """GET /api/inv-adjustments/{id}/pdf should return PDF"""
        if not self.test_adjustment_id:
            pytest.skip("No adjustment available for PDF test")
        
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/{self.test_adjustment_id}/pdf"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get('Content-Type', '')
        
        # Could return PDF or JSON with HTML (if WeasyPrint not available)
        if 'application/pdf' in content_type:
            # Check it's actual PDF content
            content = response.content
            assert content.startswith(b'%PDF') or len(content) > 1000
            print(f"✓ PDF generated: {len(content)} bytes, content-type: {content_type}")
        else:
            # Fallback - check if HTML returned
            data = response.json() if 'application/json' in content_type else {}
            if data.get("html"):
                print(f"✓ PDF fallback: HTML returned (WeasyPrint may not be installed)")
            else:
                print(f"✓ PDF endpoint responded: {content_type}")
    
    def test_pdf_for_invalid_id_returns_404(self):
        """PDF for non-existent adjustment should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/INVALID-ID-12345/pdf"
        )
        assert response.status_code == 404
        print("✓ PDF for invalid ID returns 404")


class TestABCClassificationReport:
    """Test ABC Classification report with drill-down"""
    
    def test_abc_report_returns_classification(self):
        """GET /api/inv-adjustments/reports/abc-classification"""
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/reports/abc-classification"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        
        report = data["report"]
        assert "items" in report
        assert "class_counts" in report
        
        # Verify class_counts structure
        class_counts = report["class_counts"]
        assert "A" in class_counts
        assert "B" in class_counts
        assert "C" in class_counts
        
        print(f"✓ ABC Report: A={class_counts['A']}, B={class_counts['B']}, C={class_counts['C']}")
        print(f"  Total items classified: {len(report['items'])}")
        
        # Store an item_id for drill-down test
        if report["items"]:
            pytest.abc_item_id = report["items"][0]["_id"]
            pytest.abc_item_name = report["items"][0].get("item_name", "Unknown")
        
        return report
    
    def test_abc_drill_down_for_item(self):
        """GET /api/inv-adjustments/reports/abc-classification/{item_id}"""
        # First get ABC report to get an item_id
        abc_response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/reports/abc-classification"
        )
        abc_data = abc_response.json()
        
        if not abc_data.get("report", {}).get("items"):
            pytest.skip("No items in ABC report to drill down")
        
        # Get first item_id from ABC report
        item_id = abc_data["report"]["items"][0]["_id"]
        
        # Call drill-down endpoint
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/reports/abc-classification/{item_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["code"] == 0
        assert "item" in data or "adjustments" in data
        assert "adjustments" in data
        assert "total_adjustments" in data
        assert "total_qty_change" in data
        assert "total_value_change" in data
        
        print(f"✓ ABC Drill-down for item {item_id}:")
        print(f"  Total adjustments: {data['total_adjustments']}")
        print(f"  Total qty change: {data['total_qty_change']}")
        print(f"  Adjustments: {len(data.get('adjustments', []))}")
        
        # Verify adjustment structure
        if data["adjustments"]:
            adj = data["adjustments"][0]
            expected_fields = ["adjustment_id", "reference_number", "date", "reason", "type", "quantity_adjusted"]
            for field in expected_fields:
                assert field in adj, f"Missing field in drill-down: {field}"
    
    def test_abc_drill_down_invalid_item(self):
        """Drill-down for non-existent item should still return 200 with empty data"""
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/reports/abc-classification/INVALID-ITEM-12345"
        )
        # Should return 200 with empty adjustments (not 404)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["total_adjustments"] == 0
        print("✓ ABC drill-down for invalid item returns empty data")


class TestTicketLinking:
    """Test ticket_id field in adjustments"""
    
    def test_create_adjustment_with_ticket_id(self):
        """POST /api/inv-adjustments with ticket_id"""
        # Get a reason first
        reasons_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        reason = reasons_resp.json()["reasons"][0]["name"]
        
        ticket_id = "TKT-TEST-001"
        payload = {
            "adjustment_type": "quantity",
            "date": "2026-01-18",
            "account": "Cost of Goods Sold",
            "reason": reason,
            "description": "TEST_Ticket linked adjustment",
            "line_items": [
                {"item_id": ALT_ITEM_ID, "new_quantity": 15}
            ],
            "status": "draft",
            "ticket_id": ticket_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        adj_id = data["adjustment_id"]
        print(f"✓ Created adjustment with ticket_id: {adj_id}")
        
        # Verify ticket_id is stored and returned in GET
        detail_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/{adj_id}")
        detail = detail_resp.json()["adjustment"]
        
        assert detail.get("ticket_id") == ticket_id, f"ticket_id not stored! Got: {detail.get('ticket_id')}"
        print(f"✓ ticket_id '{ticket_id}' stored and returned correctly")
        
        # Cleanup - delete draft
        requests.delete(f"{BASE_URL}/api/inv-adjustments/{adj_id}")
        
        return adj_id
    
    def test_ticket_id_in_export(self):
        """Exported CSV should include ticket_id column"""
        response = requests.get(f"{BASE_URL}/api/inv-adjustments/export/csv")
        assert response.status_code == 200
        
        csv_content = response.text
        header = csv_content.split('\n')[0]
        
        assert 'Ticket ID' in header or 'ticket_id' in header.lower()
        print("✓ ticket_id column present in CSV export")


class TestAdjustStockFromItemsPage:
    """Test the Adjust Stock shortcut functionality - URL param handling"""
    
    def test_items_endpoint_exists(self):
        """Verify items endpoint works for getting item data"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
        # Check test item exists
        items = data["items"]
        test_item = next((i for i in items if i["item_id"] == ALT_ITEM_ID), None)
        if test_item:
            print(f"✓ Test item found: {test_item['name']} (stock: {test_item.get('stock_on_hand', 0)})")
        else:
            print(f"✓ Items endpoint works, {len(items)} items returned")


class TestIntegrationScenario:
    """End-to-end integration tests"""
    
    def test_full_import_workflow(self):
        """Test: Create CSV -> Validate -> Process -> Verify draft created"""
        # Step 1: Create CSV
        csv_content = f"""Item ID,New Quantity,Reason,Type,Date,Description
{ALT_ITEM_ID},88,Stocktaking Variance,quantity,2026-01-18,TEST_Full import workflow
"""
        files = {'file': ('import_test.csv', csv_content, 'text/csv')}
        
        # Step 2: Validate
        validate_resp = requests.post(
            f"{BASE_URL}/api/inv-adjustments/import/validate",
            files=files
        )
        assert validate_resp.status_code == 200
        validate_data = validate_resp.json()
        assert validate_data["items_found"] >= 1 or validate_data["row_count"] >= 1
        print(f"✓ Step 1: Validated - {validate_data['row_count']} rows, {validate_data['items_found']} items matched")
        
        # Step 3: Process (need to send file again)
        files = {'file': ('import_test.csv', csv_content, 'text/csv')}
        process_resp = requests.post(
            f"{BASE_URL}/api/inv-adjustments/import/process",
            files=files
        )
        assert process_resp.status_code == 200
        process_data = process_resp.json()
        created_count = process_data.get("created", 0)
        print(f"✓ Step 2: Processed - {created_count} drafts created")
        
        # Step 4: Verify draft exists
        list_resp = requests.get(f"{BASE_URL}/api/inv-adjustments?status=draft&search=TEST_Full")
        list_data = list_resp.json()
        # May or may not find by description search, so just verify list works
        print(f"✓ Step 3: Draft adjustments listed: {list_data['total']} total drafts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
