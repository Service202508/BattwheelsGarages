"""
Test Estimate Bug Fixes (Bugs A, B, C + Chain Fix)
- Bug A: Save Changes error toast while showing "Saved Just now"
- Bug B: Line items not loading in edit modal
- Bug C: Estimates list not loading (data key mismatch)
- Chain Fix: Estimate-to-invoice conversion collection name
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://gst-report-update.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "admin@battwheels.in"
TEST_PASSWORD = "admin"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]

@pytest.fixture(scope="module")
def headers(auth_token):
    """Create headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestBugCFix:
    """Bug C: Estimates list not loading due to data key mismatch
    Frontend was reading data.estimates instead of data.data
    """
    
    def test_estimates_list_returns_data_key(self, headers):
        """GET /api/estimates-enhanced/ returns 'data' key (not just 'estimates')"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=100", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has 'data' key
        assert "data" in data, "Response missing 'data' key - Bug C not fixed"
        assert isinstance(data["data"], list), "'data' should be a list"
        
        # Verify we have estimates
        assert len(data["data"]) >= 1, "No estimates found"
        print(f"✓ Bug C Fixed: Found {len(data['data'])} estimates in data.data")
    
    def test_estimates_list_has_pagination(self, headers):
        """Verify pagination metadata is present"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=100", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "pagination" in data, "Response missing pagination"
        pagination = data["pagination"]
        assert "total_count" in pagination
        print(f"✓ Pagination: total_count={pagination['total_count']}")


class TestBugBFix:
    """Bug B: Line items not loading in edit modal
    handleOpenEdit was not normalizing field names between estimate types
    """
    
    def test_estimate_detail_has_line_items(self, headers):
        """GET /api/estimates-enhanced/{id} returns line_items array"""
        # First get an estimate ID
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10", headers=headers)
        estimates = response.json().get("data", [])
        assert len(estimates) > 0, "No estimates to test"
        
        # Get one with line items (EST-00002 has 2 items)
        estimate_id = None
        for est in estimates:
            if est.get("line_items_count", 0) >= 2:
                estimate_id = est["estimate_id"]
                break
        
        if not estimate_id:
            estimate_id = estimates[0]["estimate_id"]
        
        # Fetch detail
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "estimate" in data
        estimate = data["estimate"]
        assert "line_items" in estimate, "Bug B not fixed: estimate detail missing line_items"
        print(f"✓ Bug B Fixed: Estimate {estimate_id} has {len(estimate['line_items'])} line items")
    
    def test_line_items_have_required_fields(self, headers):
        """Verify line items have all required fields for edit modal"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10", headers=headers)
        estimates = response.json().get("data", [])
        
        # Find estimate with line items
        for est in estimates:
            if est.get("line_items_count", 0) >= 1:
                response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{est['estimate_id']}", headers=headers)
                estimate = response.json()["estimate"]
                
                for item in estimate.get("line_items", []):
                    # Check required fields exist
                    assert "name" in item, f"Line item missing 'name'"
                    assert "quantity" in item, f"Line item missing 'quantity'"
                    assert "rate" in item, f"Line item missing 'rate'"
                    assert "tax_percentage" in item, f"Line item missing 'tax_percentage'"
                    print(f"  ✓ Line item '{item['name']}': qty={item['quantity']}, rate={item['rate']}, tax={item['tax_percentage']}%")
                break


class TestBugAFix:
    """Bug A: Error updating estimate toast while "Saved Just now" shows
    Frontend was sending wrong field names + backend not handling line_items in PUT
    """
    
    def test_update_estimate_with_line_items(self, headers):
        """PUT /api/estimates-enhanced/{id} accepts line_items and recalculates totals"""
        # Find a draft estimate
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10&status=draft", headers=headers)
        estimates = response.json().get("data", [])
        draft_estimates = [e for e in estimates if e.get("status") == "draft"]
        
        if not draft_estimates:
            pytest.skip("No draft estimates available for update test")
        
        estimate_id = draft_estimates[0]["estimate_id"]
        original_total = draft_estimates[0].get("grand_total", 0)
        
        # Update with modified line items
        update_payload = {
            "notes": "Updated by pytest test",
            "terms_and_conditions": "Net 30 - pytest",
            "line_items": [
                {"name": "Test Item 1", "quantity": 2, "rate": 500, "tax_percentage": 18, "unit": "pcs", "discount_percent": 0},
                {"name": "Test Item 2", "quantity": 1, "rate": 1000, "tax_percentage": 18, "unit": "pcs", "discount_percent": 0}
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json=update_payload
        )
        
        assert response.status_code == 200, f"Bug A not fixed: Update failed with {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("code") == 0, f"Update failed: {data}"
        assert "estimate" in data, "Response missing estimate"
        
        estimate = data["estimate"]
        # Verify totals recalculated: (2*500 + 1*1000) * 1.18 = 2360
        assert estimate.get("subtotal") == 2000, f"Subtotal mismatch: {estimate.get('subtotal')}"
        assert estimate.get("grand_total") == 2360, f"Grand total mismatch: {estimate.get('grand_total')}"
        
        print(f"✓ Bug A Fixed: Update succeeded, totals recalculated correctly")
        print(f"  - Subtotal: ₹{estimate['subtotal']}")
        print(f"  - Tax: ₹{estimate['total_tax']}")
        print(f"  - Grand Total: ₹{estimate['grand_total']}")
    
    def test_update_estimate_returns_line_items(self, headers):
        """Verify PUT response includes updated line_items"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10&status=draft", headers=headers)
        estimates = response.json().get("data", [])
        draft_estimates = [e for e in estimates if e.get("status") == "draft"]
        
        if not draft_estimates:
            pytest.skip("No draft estimates available")
        
        estimate_id = draft_estimates[0]["estimate_id"]
        
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json={
                "line_items": [
                    {"name": "Single Item", "quantity": 1, "rate": 1180, "tax_percentage": 18, "unit": "pcs"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        estimate = data["estimate"]
        
        assert "line_items" in estimate, "PUT response missing line_items"
        assert len(estimate["line_items"]) == 1, "Line items count mismatch"
        assert estimate["line_items"][0]["name"] == "Single Item"
        print(f"✓ PUT response includes {len(estimate['line_items'])} line items")


class TestChainFix:
    """Chain Fix: Estimate-to-invoice conversion endpoint was querying wrong collection
    Was using db['estimates_enhanced'] instead of db['estimates']
    """
    
    def test_estimate_to_invoice_finds_estimate(self, headers):
        """POST /api/invoices-enhanced/from-estimate/{id} finds estimate (not 404)"""
        # Get a draft estimate
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10&status=draft", headers=headers)
        estimates = response.json().get("data", [])
        draft_estimates = [e for e in estimates if e.get("status") == "draft"]
        
        if not draft_estimates:
            pytest.skip("No draft estimates available")
        
        estimate_id = draft_estimates[0]["estimate_id"]
        
        # Try to convert - should fail with 400 (not accepted), NOT 404 (not found)
        response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/from-estimate/{estimate_id}",
            headers=headers
        )
        
        # Should be 400 (business rule violation), not 404 (not found)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Only accepted estimates" in response.json().get("detail", ""), \
            f"Wrong error: {response.json()}"
        
        print(f"✓ Chain Fix verified: Estimate {estimate_id} found (got 400, not 404)")
    
    def test_converted_estimate_cannot_convert_again(self, headers):
        """Already converted estimates should not be convertible again"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10", headers=headers)
        estimates = response.json().get("data", [])
        converted = [e for e in estimates if e.get("status") == "converted"]
        
        if not converted:
            pytest.skip("No converted estimates available")
        
        estimate_id = converted[0]["estimate_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/from-estimate/{estimate_id}",
            headers=headers
        )
        
        assert response.status_code == 400
        print(f"✓ Converted estimate {estimate_id} correctly rejected for re-conversion")


class TestTicketEstimates:
    """Test ticket-linked estimates functionality"""
    
    def test_ticket_estimates_list(self, headers):
        """GET /api/ticket-estimates returns estimates list"""
        response = requests.get(f"{BASE_URL}/api/ticket-estimates?per_page=100", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("code") == 0
        assert "estimates" in data
        print(f"✓ Found {len(data['estimates'])} ticket estimates")


class TestDiscountTypeOptions:
    """Verify discount type options are correct: none/percent/amount"""
    
    def test_estimate_accepts_none_discount(self, headers):
        """PUT with discount_type='none' should work"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10&status=draft", headers=headers)
        estimates = response.json().get("data", [])
        draft_estimates = [e for e in estimates if e.get("status") == "draft"]
        
        if not draft_estimates:
            pytest.skip("No draft estimates available")
        
        estimate_id = draft_estimates[0]["estimate_id"]
        
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json={"discount_type": "none", "discount_value": 0}
        )
        
        assert response.status_code == 200
        print("✓ discount_type='none' accepted")
    
    def test_estimate_accepts_percent_discount(self, headers):
        """PUT with discount_type='percent' should work"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10&status=draft", headers=headers)
        estimates = response.json().get("data", [])
        draft_estimates = [e for e in estimates if e.get("status") == "draft"]
        
        if not draft_estimates:
            pytest.skip("No draft estimates available")
        
        estimate_id = draft_estimates[0]["estimate_id"]
        
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json={"discount_type": "percent", "discount_value": 5}
        )
        
        assert response.status_code == 200
        print("✓ discount_type='percent' accepted")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
