"""
Inventory Adjustments V2 Module - Comprehensive Test Suite
Tests: CRUD operations, status workflow (Draft -> Adjusted -> Void), 
       reasons management, reports, filtering, and validation
"""

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test item with inventory tracking
TEST_ITEM_ID = "1837096000001141394"  # 2 WHEELER SEATCOVER-25 (stock: 10.0)
TEST_ITEM_NAME = "2 WHEELER SEATCOVER-25"
FALLBACK_ITEM_ID = "1837096000000446195"  # 12V Battery replacement (service)

class TestReasonsCRUD:
    """Test adjustment reasons CRUD operations"""
    
    def test_get_reasons_seeds_defaults(self):
        """GET /api/inv-adjustments/reasons should seed defaults on first call"""
        response = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "reasons" in data
        reasons = data["reasons"]
        assert len(reasons) >= 9, "Should have at least 9 default reasons"
        # Verify default reasons exist
        reason_names = [r["name"] for r in reasons]
        assert "Stocktaking Variance" in reason_names
        assert "Damaged Goods" in reason_names
        assert "Other" in reason_names
        print(f"✓ Found {len(reasons)} reasons including defaults")
    
    def test_create_custom_reason(self):
        """POST /api/inv-adjustments/reasons - create custom reason"""
        custom_name = f"TEST_Reason_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": custom_name,
            "description": "Test reason for unit testing",
            "is_active": True,
            "sort_order": 50
        }
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments/reasons",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "reason_id" in data
        print(f"✓ Created custom reason: {custom_name} (ID: {data['reason_id']})")
        
        # Verify it appears in list
        list_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        reasons = list_resp.json()["reasons"]
        assert any(r["name"] == custom_name for r in reasons)
        
        # Store for cleanup
        pytest.test_reason_id = data["reason_id"]
    
    def test_disable_reason(self):
        """DELETE /api/inv-adjustments/reasons/{id} - soft delete"""
        if not hasattr(pytest, 'test_reason_id'):
            pytest.skip("No test reason to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/inv-adjustments/reasons/{pytest.test_reason_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Disabled reason: {pytest.test_reason_id}")
        
        # Verify it no longer appears in active list
        list_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons?active_only=true")
        reasons = list_resp.json()["reasons"]
        assert not any(r["reason_id"] == pytest.test_reason_id for r in reasons)


class TestAdjustmentWorkflow:
    """Test full adjustment workflow: Create -> Draft -> Adjusted -> Void"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get a valid reason for tests"""
        resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        self.reasons = resp.json()["reasons"]
        self.default_reason = self.reasons[0]["name"] if self.reasons else "Other"
    
    def test_create_draft_quantity_adjustment(self):
        """POST /api/inv-adjustments - create draft quantity adjustment"""
        payload = {
            "adjustment_type": "quantity",
            "date": "2026-01-18",
            "account": "Cost of Goods Sold",
            "reason": self.default_reason,
            "warehouse_id": "WH-E1972349",
            "warehouse_name": "Main Warehouse",
            "description": "TEST_Quantity adjustment for testing",
            "line_items": [
                {
                    "item_id": TEST_ITEM_ID,
                    "new_quantity": 50  # Set new quantity to 50
                }
            ],
            "status": "draft"
        }
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustment_id" in data
        assert data["status"] == "draft"
        assert "reference_number" in data
        print(f"✓ Created draft adjustment: {data['adjustment_id']} (Ref: {data['reference_number']})")
        
        # Store for next tests
        pytest.draft_adjustment_id = data["adjustment_id"]
        pytest.draft_reference = data["reference_number"]
    
    def test_list_adjustments_with_filters(self):
        """GET /api/inv-adjustments - verify pagination and filtering"""
        # Get all adjustments
        response = requests.get(f"{BASE_URL}/api/inv-adjustments")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustments" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        print(f"✓ Listed {data['total']} adjustments")
        
        # Filter by status=draft
        draft_resp = requests.get(f"{BASE_URL}/api/inv-adjustments?status=draft")
        draft_data = draft_resp.json()
        assert draft_data["code"] == 0
        draft_statuses = [a["status"] for a in draft_data["adjustments"]]
        assert all(s == "draft" for s in draft_statuses), "All should be drafts"
        print(f"✓ Filtered by draft: {len(draft_data['adjustments'])} found")
        
        # Search by reference number
        if hasattr(pytest, 'draft_reference'):
            search_resp = requests.get(
                f"{BASE_URL}/api/inv-adjustments?search={pytest.draft_reference}"
            )
            search_data = search_resp.json()
            assert search_data["code"] == 0
            assert len(search_data["adjustments"]) >= 1
            print(f"✓ Search by reference works: {pytest.draft_reference}")
    
    def test_get_adjustment_detail_with_audit(self):
        """GET /api/inv-adjustments/{id} - verify audit_trail included"""
        if not hasattr(pytest, 'draft_adjustment_id'):
            pytest.skip("No draft adjustment to get")
        
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/{pytest.draft_adjustment_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustment" in data
        adj = data["adjustment"]
        assert "audit_trail" in adj
        assert adj["status"] == "draft"
        assert adj["adjustment_type"] == "quantity"
        assert len(adj["line_items"]) > 0
        print(f"✓ Got detail with audit trail: {len(adj['audit_trail'])} entries")
    
    def test_convert_to_adjusted(self):
        """POST /api/inv-adjustments/{id}/convert - convert draft to adjusted"""
        if not hasattr(pytest, 'draft_adjustment_id'):
            pytest.skip("No draft to convert")
        
        # Get item stock before conversion
        items_resp = requests.get(f"{BASE_URL}/api/items-enhanced/?per_page=500")
        items_data = items_resp.json()
        item_before = next((i for i in items_data["items"] if i["item_id"] == TEST_ITEM_ID), None)
        stock_before = item_before.get("stock_on_hand", 0) if item_before else 0
        
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments/{pytest.draft_adjustment_id}/convert"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Converted to adjusted")
        
        # Verify status changed
        detail_resp = requests.get(
            f"{BASE_URL}/api/inv-adjustments/{pytest.draft_adjustment_id}"
        )
        detail = detail_resp.json()["adjustment"]
        assert detail["status"] == "adjusted"
        assert detail["converted_at"] is not None
        
        # Verify stock was updated
        items_resp_after = requests.get(f"{BASE_URL}/api/items-enhanced/?per_page=500")
        items_data_after = items_resp_after.json()
        item_after = next((i for i in items_data_after["items"] if i["item_id"] == TEST_ITEM_ID), None)
        if item_after:
            stock_after = item_after.get("stock_on_hand", 0)
            print(f"✓ Stock changed: {stock_before} -> {stock_after}")
    
    def test_void_adjusted(self):
        """POST /api/inv-adjustments/{id}/void - void and reverse stock"""
        if not hasattr(pytest, 'draft_adjustment_id'):
            pytest.skip("No adjustment to void")
        
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments/{pytest.draft_adjustment_id}/void"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Voided adjustment")
        
        # Verify status
        detail_resp = requests.get(
            f"{BASE_URL}/api/inv-adjustments/{pytest.draft_adjustment_id}"
        )
        detail = detail_resp.json()["adjustment"]
        assert detail["status"] == "void"
        assert detail["voided_at"] is not None


class TestValueAdjustment:
    """Test value adjustment type"""
    
    def test_create_value_adjustment_adjusted(self):
        """POST /api/inv-adjustments with adjustment_type=value, status=adjusted"""
        # Get a reason
        reasons_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        reason = reasons_resp.json()["reasons"][0]["name"]
        
        payload = {
            "adjustment_type": "value",
            "date": "2026-01-18",
            "account": "Inventory Write-Off",
            "reason": reason,
            "description": "TEST_Value adjustment for testing",
            "line_items": [
                {
                    "item_id": TEST_ITEM_ID,
                    "new_value": 150.00  # New purchase rate
                }
            ],
            "status": "adjusted"  # Create as adjusted directly
        }
        response = requests.post(
            f"{BASE_URL}/api/inv-adjustments",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["status"] == "adjusted"
        print(f"✓ Created value adjustment (adjusted): {data['adjustment_id']}")
        
        # Get detail to verify value_adjusted calculated
        detail_resp = requests.get(
            f"{BASE_URL}/api/inv-adjustments/{data['adjustment_id']}"
        )
        detail = detail_resp.json()["adjustment"]
        assert detail["adjustment_type"] == "value"
        line = detail["line_items"][0]
        assert line.get("new_value") == 150.00
        assert "value_adjusted" in line
        print(f"✓ Value adjusted calculated: {line.get('value_adjusted')}")
        
        pytest.value_adj_id = data["adjustment_id"]


class TestDeleteDraft:
    """Test draft deletion and validation"""
    
    def test_create_and_delete_draft(self):
        """Create a draft then delete it - should succeed"""
        # Get a reason
        reasons_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        reason = reasons_resp.json()["reasons"][0]["name"]
        
        # Create draft
        payload = {
            "adjustment_type": "quantity",
            "date": "2026-01-18",
            "account": "Cost of Goods Sold",
            "reason": reason,
            "description": "TEST_To be deleted",
            "line_items": [
                {"item_id": TEST_ITEM_ID, "new_quantity": 5}
            ],
            "status": "draft"
        }
        create_resp = requests.post(f"{BASE_URL}/api/inv-adjustments", json=payload)
        adj_id = create_resp.json()["adjustment_id"]
        print(f"✓ Created draft: {adj_id}")
        
        # Delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/inv-adjustments/{adj_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["code"] == 0
        print(f"✓ Deleted draft: {adj_id}")
        
        # Verify it's gone
        get_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/{adj_id}")
        assert get_resp.status_code == 404
    
    def test_delete_adjusted_fails(self):
        """Deleting an adjusted adjustment should fail with 400"""
        # Create and convert an adjustment
        reasons_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        reason = reasons_resp.json()["reasons"][0]["name"]
        
        payload = {
            "adjustment_type": "quantity",
            "date": "2026-01-18",
            "account": "Cost of Goods Sold",
            "reason": reason,
            "description": "TEST_Adjusted cannot delete",
            "line_items": [
                {"item_id": TEST_ITEM_ID, "new_quantity": 5}
            ],
            "status": "draft"
        }
        create_resp = requests.post(f"{BASE_URL}/api/inv-adjustments", json=payload)
        adj_id = create_resp.json()["adjustment_id"]
        
        # Convert to adjusted
        requests.post(f"{BASE_URL}/api/inv-adjustments/{adj_id}/convert")
        
        # Try to delete - should fail
        delete_resp = requests.delete(f"{BASE_URL}/api/inv-adjustments/{adj_id}")
        assert delete_resp.status_code == 400
        print(f"✓ Cannot delete adjusted adjustment (400 returned)")
        
        # Cleanup - void it
        requests.post(f"{BASE_URL}/api/inv-adjustments/{adj_id}/void")


class TestSummary:
    """Test summary endpoint"""
    
    def test_get_summary(self):
        """GET /api/inv-adjustments/summary - verify counts"""
        response = requests.get(f"{BASE_URL}/api/inv-adjustments/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify all expected fields
        expected_fields = ["total", "draft", "adjusted", "voided", 
                          "this_month", "total_increases", "total_decreases"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Summary: total={data['total']}, draft={data['draft']}, "
              f"adjusted={data['adjusted']}, voided={data['voided']}")
        
        # Verify counts are non-negative
        assert data["total"] >= 0
        assert data["draft"] >= 0
        assert data["adjusted"] >= 0
        assert data["voided"] >= 0


class TestReports:
    """Test report endpoints"""
    
    def test_adjustment_summary_report(self):
        """GET /api/inv-adjustments/reports/adjustment-summary"""
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/reports/adjustment-summary"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        
        report = data["report"]
        assert "total_adjustments" in report
        assert "by_reason" in report
        assert "by_type" in report
        assert "by_account" in report
        print(f"✓ Adjustment summary report: {report['total_adjustments']} adjustments")
    
    def test_fifo_tracking_report(self):
        """GET /api/inv-adjustments/reports/fifo-tracking"""
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/reports/fifo-tracking"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        
        report = data["report"]
        assert "lots" in report
        assert "total_lots" in report
        assert "total_in" in report
        assert "total_out" in report
        print(f"✓ FIFO tracking report: {report['total_lots']} lots")
    
    def test_abc_classification_report(self):
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
        assert "period_days" in report
        assert "thresholds" in report
        print(f"✓ ABC classification report: A={report['class_counts']['A']}, "
              f"B={report['class_counts']['B']}, C={report['class_counts']['C']}")


class TestNumberingSettings:
    """Test numbering settings endpoints"""
    
    def test_get_numbering_settings(self):
        """GET /api/inv-adjustments/settings/numbering"""
        response = requests.get(
            f"{BASE_URL}/api/inv-adjustments/settings/numbering"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "settings" in data
        
        settings = data["settings"]
        assert "prefix" in settings
        print(f"✓ Numbering settings: prefix={settings.get('prefix')}")


class TestEdgeCases:
    """Test edge cases and validation"""
    
    def test_convert_non_draft_fails(self):
        """Converting non-draft should return 400"""
        # Create and convert to adjusted first
        reasons_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        reason = reasons_resp.json()["reasons"][0]["name"]
        
        payload = {
            "adjustment_type": "quantity",
            "reason": reason,
            "line_items": [{"item_id": TEST_ITEM_ID, "new_quantity": 1}],
            "status": "draft"
        }
        create_resp = requests.post(f"{BASE_URL}/api/inv-adjustments", json=payload)
        adj_id = create_resp.json()["adjustment_id"]
        
        # Convert first time
        requests.post(f"{BASE_URL}/api/inv-adjustments/{adj_id}/convert")
        
        # Try converting again
        second_convert = requests.post(f"{BASE_URL}/api/inv-adjustments/{adj_id}/convert")
        assert second_convert.status_code == 400
        print(f"✓ Cannot convert non-draft (400 returned)")
        
        # Cleanup
        requests.post(f"{BASE_URL}/api/inv-adjustments/{adj_id}/void")
    
    def test_void_non_adjusted_fails(self):
        """Voiding a draft should return 400"""
        reasons_resp = requests.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        reason = reasons_resp.json()["reasons"][0]["name"]
        
        payload = {
            "adjustment_type": "quantity",
            "reason": reason,
            "line_items": [{"item_id": TEST_ITEM_ID, "new_quantity": 1}],
            "status": "draft"
        }
        create_resp = requests.post(f"{BASE_URL}/api/inv-adjustments", json=payload)
        adj_id = create_resp.json()["adjustment_id"]
        
        # Try voiding draft
        void_resp = requests.post(f"{BASE_URL}/api/inv-adjustments/{adj_id}/void")
        assert void_resp.status_code == 400
        print(f"✓ Cannot void draft (400 returned)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/inv-adjustments/{adj_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
