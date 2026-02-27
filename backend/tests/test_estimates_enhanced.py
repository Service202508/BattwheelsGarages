"""
Estimates Enhanced Module Tests
Tests for CRUD operations, status workflow, line items management, 
GST calculations, conversions, and reporting endpoints.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://platform-hardening-1.preview.emergentagent.com')

# Test data storage
test_data = {
    "estimate_id": None,
    "estimate_number": None,
    "customer_id": None,
    "line_item_id": None
}


class TestEstimatesSettings:
    """Test estimate settings endpoints"""
    
    def test_get_settings(self):
        """GET /api/estimates-enhanced/settings - Returns module settings"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "settings" in data
        assert "numbering" in data["settings"]
        assert "defaults" in data["settings"]
        # Verify numbering settings
        numbering = data["settings"]["numbering"]
        assert "prefix" in numbering
        assert "next_number" in numbering
        print(f"✓ Settings retrieved: prefix={numbering.get('prefix')}, next_number={numbering.get('next_number')}")


class TestEstimatesSummary:
    """Test summary and reporting endpoints"""
    
    def test_get_summary(self):
        """GET /api/estimates-enhanced/summary - Returns summary statistics"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        assert "total" in summary
        assert "by_status" in summary
        assert "total_value" in summary
        print(f"✓ Summary: total={summary['total']}, total_value=₹{summary['total_value']}")
    
    def test_conversion_funnel_report(self):
        """GET /api/estimates-enhanced/reports/conversion-funnel - Conversion funnel report"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/reports/conversion-funnel")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "funnel" in data
        funnel = data["funnel"]
        assert "total_created" in funnel
        assert "sent_to_customer" in funnel
        assert "accepted" in funnel
        assert "converted" in funnel
        print(f"✓ Funnel: created={funnel['total_created']}, sent={funnel['sent_to_customer']}, accepted={funnel['accepted']}, converted={funnel['converted']}")
    
    def test_report_by_status(self):
        """GET /api/estimates-enhanced/reports/by-status - Report by status"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/reports/by-status")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        print(f"✓ Status report: {len(data['report'])} status groups")
    
    def test_report_by_customer(self):
        """GET /api/estimates-enhanced/reports/by-customer - Report by customer"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/reports/by-customer?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        print(f"✓ Customer report: {len(data['report'])} customers")


class TestEstimatesCRUD:
    """Test CRUD operations for estimates"""
    
    @pytest.fixture(autouse=True)
    def setup_customer(self):
        """Get a customer for testing"""
        response = requests.get(f"{BASE_URL}/api/contact-integration/contacts/search?q=test&contact_type=customer&limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("contacts") and len(data["contacts"]) > 0:
                test_data["customer_id"] = data["contacts"][0]["contact_id"]
                print(f"Using customer: {data['contacts'][0].get('contact_name', data['contacts'][0].get('name'))}")
    
    def test_01_create_estimate(self):
        """POST /api/estimates-enhanced/ - Create estimate with customer and line items"""
        if not test_data["customer_id"]:
            pytest.skip("No customer available for testing")
        
        payload = {
            "customer_id": test_data["customer_id"],
            "reference_number": "TEST-REF-001",
            "subject": "Test Estimate for Automation",
            "salesperson_name": "Test Salesperson",
            "terms_and_conditions": "Test terms and conditions",
            "notes": "Test notes for estimate",
            "discount_type": "percent",
            "discount_value": 5,
            "shipping_charge": 100,
            "adjustment": -50,
            "adjustment_description": "Rounding adjustment",
            "line_items": [
                {
                    "name": "Test Product 1",
                    "description": "Test product description",
                    "hsn_code": "8471",
                    "quantity": 2,
                    "unit": "pcs",
                    "rate": 1000,
                    "discount_percent": 10,
                    "tax_percentage": 18
                },
                {
                    "name": "Test Service",
                    "description": "Test service description",
                    "hsn_code": "9983",
                    "quantity": 1,
                    "unit": "hrs",
                    "rate": 500,
                    "discount_percent": 0,
                    "tax_percentage": 18
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "estimate" in data
        
        estimate = data["estimate"]
        test_data["estimate_id"] = estimate["estimate_id"]
        test_data["estimate_number"] = estimate["estimate_number"]
        
        # Verify estimate data
        assert estimate["status"] == "draft"
        assert estimate["customer_id"] == test_data["customer_id"]
        assert estimate["reference_number"] == "TEST-REF-001"
        assert estimate["subject"] == "Test Estimate for Automation"
        assert estimate["line_items_count"] == 2
        assert estimate["discount_type"] == "percent"
        assert estimate["discount_value"] == 5
        assert estimate["shipping_charge"] == 100
        assert estimate["adjustment"] == -50
        
        # Verify GST calculations
        assert "subtotal" in estimate
        assert "total_tax" in estimate
        assert "grand_total" in estimate
        assert estimate["grand_total"] > 0
        
        print(f"✓ Created estimate: {estimate['estimate_number']}, grand_total=₹{estimate['grand_total']}")
    
    def test_02_list_estimates(self):
        """GET /api/estimates-enhanced/ - List estimates with filters"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "estimates" in data
        assert "page_context" in data
        print(f"✓ Listed {len(data['estimates'])} estimates, total={data['page_context']['total']}")
    
    def test_03_list_estimates_with_status_filter(self):
        """GET /api/estimates-enhanced/?status=draft - Filter by status"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?status=draft")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for est in data.get("estimates", []):
            assert est["status"] == "draft"
        print(f"✓ Filtered by status=draft: {len(data['estimates'])} estimates")
    
    def test_04_list_estimates_with_search(self):
        """GET /api/estimates-enhanced/?search=TEST - Search estimates"""
        if not test_data["estimate_number"]:
            pytest.skip("No estimate created yet")
        
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?search=TEST")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Search results: {len(data['estimates'])} estimates")
    
    def test_05_get_estimate_detail(self):
        """GET /api/estimates-enhanced/{id} - Get estimate details with line items and history"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "estimate" in data
        
        estimate = data["estimate"]
        assert estimate["estimate_id"] == test_data["estimate_id"]
        assert "line_items" in estimate
        assert "history" in estimate
        assert "customer_details" in estimate
        assert len(estimate["line_items"]) == 2
        
        # Store line item ID for later tests
        if estimate["line_items"]:
            test_data["line_item_id"] = estimate["line_items"][0]["line_item_id"]
        
        print(f"✓ Got estimate detail: {estimate['estimate_number']}, {len(estimate['line_items'])} line items, {len(estimate['history'])} history entries")
    
    def test_06_update_estimate(self):
        """PUT /api/estimates-enhanced/{id} - Update draft estimate"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        payload = {
            "subject": "Updated Test Estimate",
            "notes": "Updated notes",
            "shipping_charge": 150
        }
        
        response = requests.put(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["estimate"]["subject"] == "Updated Test Estimate"
        assert data["estimate"]["shipping_charge"] == 150
        print(f"✓ Updated estimate: subject='{data['estimate']['subject']}'")
    
    def test_07_get_estimate_not_found(self):
        """GET /api/estimates-enhanced/{id} - 404 for non-existent estimate"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/EST-NONEXISTENT123")
        assert response.status_code == 404
        print("✓ Correctly returns 404 for non-existent estimate")


class TestLineItems:
    """Test line items management"""
    
    def test_01_add_line_item(self):
        """POST /api/estimates-enhanced/{id}/line-items - Add line item to estimate"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        payload = {
            "name": "Additional Item",
            "description": "Added via API test",
            "quantity": 3,
            "unit": "pcs",
            "rate": 250,
            "discount_percent": 5,
            "tax_percentage": 12,
            "hsn_code": "8542"
        }
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/line-items", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "line_item" in data
        
        line_item = data["line_item"]
        assert line_item["name"] == "Additional Item"
        assert line_item["quantity"] == 3
        assert "total" in line_item
        
        test_data["new_line_item_id"] = line_item["line_item_id"]
        print(f"✓ Added line item: {line_item['name']}, total=₹{line_item['total']}")
    
    def test_02_update_line_item(self):
        """PUT /api/estimates-enhanced/{id}/line-items/{line_id} - Update line item"""
        if not test_data["estimate_id"] or not test_data.get("new_line_item_id"):
            pytest.skip("No line item available")
        
        payload = {
            "quantity": 5,
            "rate": 300
        }
        
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/line-items/{test_data['new_line_item_id']}", 
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["line_item"]["quantity"] == 5
        assert data["line_item"]["rate"] == 300
        print(f"✓ Updated line item: qty={data['line_item']['quantity']}, rate=₹{data['line_item']['rate']}")
    
    def test_03_delete_line_item(self):
        """DELETE /api/estimates-enhanced/{id}/line-items/{line_id} - Delete line item"""
        if not test_data["estimate_id"] or not test_data.get("new_line_item_id"):
            pytest.skip("No line item available")
        
        response = requests.delete(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/line-items/{test_data['new_line_item_id']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("✓ Deleted line item successfully")


class TestStatusWorkflow:
    """Test status workflow: draft → sent → accepted/declined → converted"""
    
    def test_01_send_estimate(self):
        """POST /api/estimates-enhanced/{id}/send - Send estimate email (mocked)"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.post(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/send?email_to=test@example.com&message=Test%20message"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "sent" in data["message"].lower()
        print(f"✓ Sent estimate (mocked): {data['message']}")
    
    def test_02_verify_sent_status(self):
        """Verify estimate status changed to 'sent'"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["estimate"]["status"] == "sent"
        print("✓ Estimate status is now 'sent'")
    
    def test_03_mark_accepted(self):
        """POST /api/estimates-enhanced/{id}/mark-accepted - Accept estimate"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/mark-accepted")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("✓ Marked estimate as accepted")
    
    def test_04_verify_accepted_status(self):
        """Verify estimate status changed to 'accepted'"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["estimate"]["status"] == "accepted"
        assert "accepted_date" in data["estimate"]
        print(f"✓ Estimate status is 'accepted', accepted_date={data['estimate']['accepted_date']}")


class TestConversions:
    """Test conversion to Invoice and Sales Order"""
    
    def test_01_convert_to_invoice(self):
        """POST /api/estimates-enhanced/{id}/convert-to-invoice - Convert accepted estimate to invoice"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/convert-to-invoice")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "invoice_id" in data
        assert "invoice_number" in data
        print(f"✓ Converted to Invoice: {data['invoice_number']}")
    
    def test_02_verify_converted_status(self):
        """Verify estimate status changed to 'converted'"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["estimate"]["status"] == "converted"
        assert data["estimate"]["converted_to"] is not None
        assert "invoice:" in data["estimate"]["converted_to"]
        print(f"✓ Estimate converted: {data['estimate']['converted_to']}")


class TestCloneAndDelete:
    """Test clone and delete operations"""
    
    def test_01_clone_estimate(self):
        """POST /api/estimates-enhanced/{id}/clone - Clone estimate"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/clone")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "estimate_id" in data
        assert "estimate_number" in data
        
        test_data["cloned_estimate_id"] = data["estimate_id"]
        print(f"✓ Cloned estimate: {data['estimate_number']}")
    
    def test_02_delete_cloned_estimate(self):
        """DELETE /api/estimates-enhanced/{id} - Delete draft estimate only"""
        if not test_data.get("cloned_estimate_id"):
            pytest.skip("No cloned estimate available")
        
        response = requests.delete(f"{BASE_URL}/api/estimates-enhanced/{test_data['cloned_estimate_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("✓ Deleted cloned estimate successfully")
    
    def test_03_cannot_delete_non_draft(self):
        """DELETE /api/estimates-enhanced/{id} - Cannot delete non-draft estimate"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate created yet")
        
        # The original estimate is now 'converted', should not be deletable
        response = requests.delete(f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}")
        assert response.status_code == 400
        print("✓ Correctly prevents deletion of non-draft estimate")


class TestSalesOrderConversion:
    """Test conversion to Sales Order (separate flow)"""
    
    def test_01_create_and_accept_for_so(self):
        """Create a new estimate and accept it for SO conversion"""
        # Get customer
        response = requests.get(f"{BASE_URL}/api/contact-integration/contacts/search?q=test&contact_type=customer&limit=1")
        if response.status_code != 200 or not response.json().get("contacts"):
            pytest.skip("No customer available")
        
        customer_id = response.json()["contacts"][0]["contact_id"]
        
        # Create estimate
        payload = {
            "customer_id": customer_id,
            "subject": "Test for Sales Order Conversion",
            "line_items": [
                {"name": "SO Test Item", "quantity": 1, "rate": 1000, "tax_percentage": 18}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/", json=payload)
        assert response.status_code == 200
        estimate_id = response.json()["estimate"]["estimate_id"]
        
        # Send
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}/send?email_to=test@example.com")
        assert response.status_code == 200
        
        # Accept
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}/mark-accepted")
        assert response.status_code == 200
        
        test_data["so_estimate_id"] = estimate_id
        print(f"✓ Created and accepted estimate for SO conversion")
    
    def test_02_convert_to_sales_order(self):
        """POST /api/estimates-enhanced/{id}/convert-to-sales-order - Convert to sales order"""
        if not test_data.get("so_estimate_id"):
            pytest.skip("No estimate available for SO conversion")
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{test_data['so_estimate_id']}/convert-to-sales-order")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "salesorder_id" in data
        assert "salesorder_number" in data
        print(f"✓ Converted to Sales Order: {data['salesorder_number']}")


class TestDeclineFlow:
    """Test decline and resend flow"""
    
    def test_01_create_and_send_for_decline(self):
        """Create and send estimate for decline test"""
        response = requests.get(f"{BASE_URL}/api/contact-integration/contacts/search?q=test&contact_type=customer&limit=1")
        if response.status_code != 200 or not response.json().get("contacts"):
            pytest.skip("No customer available")
        
        customer_id = response.json()["contacts"][0]["contact_id"]
        
        payload = {
            "customer_id": customer_id,
            "subject": "Test for Decline Flow",
            "line_items": [
                {"name": "Decline Test Item", "quantity": 1, "rate": 500, "tax_percentage": 18}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/", json=payload)
        assert response.status_code == 200
        estimate_id = response.json()["estimate"]["estimate_id"]
        
        # Send
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}/send?email_to=test@example.com")
        assert response.status_code == 200
        
        test_data["decline_estimate_id"] = estimate_id
        print("✓ Created and sent estimate for decline test")
    
    def test_02_mark_declined(self):
        """POST /api/estimates-enhanced/{id}/mark-declined - Decline estimate"""
        if not test_data.get("decline_estimate_id"):
            pytest.skip("No estimate available for decline")
        
        response = requests.post(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['decline_estimate_id']}/mark-declined?reason=Price%20too%20high"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("✓ Marked estimate as declined")
    
    def test_03_verify_declined_status(self):
        """Verify estimate status is 'declined'"""
        if not test_data.get("decline_estimate_id"):
            pytest.skip("No estimate available")
        
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/{test_data['decline_estimate_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["estimate"]["status"] == "declined"
        print("✓ Estimate status is 'declined'")
    
    def test_04_resend_declined_estimate(self):
        """POST /api/estimates-enhanced/{id}/send - Resend declined estimate"""
        if not test_data.get("decline_estimate_id"):
            pytest.skip("No estimate available")
        
        response = requests.post(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['decline_estimate_id']}/send?email_to=test@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("✓ Resent declined estimate")


class TestStatusValidation:
    """Test status transition validation"""
    
    def test_invalid_status_transition(self):
        """PUT /api/estimates-enhanced/{id}/status - Invalid transition should fail"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate available")
        
        # Try to change converted estimate to draft (invalid)
        payload = {"status": "draft"}
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/status",
            json=payload
        )
        assert response.status_code == 400
        print("✓ Correctly rejects invalid status transition")


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_create_without_customer(self):
        """POST /api/estimates-enhanced/ - Should fail without customer"""
        payload = {
            "subject": "No Customer Test",
            "line_items": [{"name": "Test", "quantity": 1, "rate": 100}]
        }
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/", json=payload)
        assert response.status_code == 422  # Validation error
        print("✓ Correctly rejects estimate without customer")
    
    def test_create_with_invalid_customer(self):
        """POST /api/estimates-enhanced/ - Should fail with invalid customer"""
        payload = {
            "customer_id": "INVALID-CUSTOMER-ID",
            "line_items": [{"name": "Test", "quantity": 1, "rate": 100}]
        }
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/", json=payload)
        assert response.status_code == 404
        print("✓ Correctly rejects estimate with invalid customer")
    
    def test_update_non_draft_estimate(self):
        """PUT /api/estimates-enhanced/{id} - Should fail for non-draft"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate available")
        
        payload = {"subject": "Try to update converted"}
        response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}",
            json=payload
        )
        assert response.status_code == 400
        print("✓ Correctly rejects update of non-draft estimate")
    
    def test_add_line_item_to_non_draft(self):
        """POST /api/estimates-enhanced/{id}/line-items - Should fail for non-draft"""
        if not test_data["estimate_id"]:
            pytest.skip("No estimate available")
        
        payload = {"name": "New Item", "quantity": 1, "rate": 100}
        response = requests.post(
            f"{BASE_URL}/api/estimates-enhanced/{test_data['estimate_id']}/line-items",
            json=payload
        )
        assert response.status_code == 400
        print("✓ Correctly rejects adding line item to non-draft estimate")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
