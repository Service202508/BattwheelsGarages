"""
Sales Orders Enhanced Module Tests
Tests for the Sales Orders module including CRUD, line items, status workflow, fulfillment, and conversions.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://beta-ready-1.preview.emergentagent.com')

# Test data
TEST_CUSTOMER_ID = "CON-235065AEEC94"  # Rahul Sharma - customer
TEST_ITEM_ID = "I-DDC36534C55C"  # EV Battery Service

class TestSalesOrdersEnhancedSettings:
    """Test settings and summary endpoints"""
    
    def test_get_settings(self):
        """GET /api/sales-orders-enhanced/settings - Returns module settings"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "settings" in data
        assert "numbering" in data["settings"]
        assert "defaults" in data["settings"]
        assert data["settings"]["numbering"]["prefix"] == "SO-"
        print(f"✓ Settings retrieved: prefix={data['settings']['numbering']['prefix']}")
    
    def test_get_summary(self):
        """GET /api/sales-orders-enhanced/summary - Returns summary statistics"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        assert "total" in data["summary"]
        assert "by_status" in data["summary"]
        assert "by_fulfillment" in data["summary"]
        print(f"✓ Summary retrieved: total={data['summary']['total']}")


class TestSalesOrdersEnhancedReports:
    """Test reporting endpoints"""
    
    def test_report_by_status(self):
        """GET /api/sales-orders-enhanced/reports/by-status - Status report"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/reports/by-status")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        print(f"✓ Status report retrieved: {len(data['report'])} status groups")
    
    def test_report_by_customer(self):
        """GET /api/sales-orders-enhanced/reports/by-customer - Customer report"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/reports/by-customer")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        print(f"✓ Customer report retrieved: {len(data['report'])} customers")
    
    def test_fulfillment_summary(self):
        """GET /api/sales-orders-enhanced/reports/fulfillment-summary - Fulfillment report"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/reports/fulfillment-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        assert "total_orders" in data["summary"]
        assert "unfulfilled" in data["summary"]
        assert "fulfilled" in data["summary"]
        print(f"✓ Fulfillment summary: total={data['summary']['total_orders']}, fulfilled={data['summary']['fulfilled']}")


class TestSalesOrdersCRUD:
    """Test CRUD operations for sales orders"""
    
    created_order_id = None
    created_order_number = None
    
    def test_01_create_sales_order(self):
        """POST /api/sales-orders-enhanced/ - Create sales order with customer and line items"""
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "reference_number": "TEST-PO-001",
            "date": "2026-02-17",
            "expected_shipment_date": "2026-02-24",
            "salesperson_name": "Test Salesperson",
            "terms_and_conditions": "Test terms",
            "notes": "Test sales order for automated testing",
            "discount_type": "percent",
            "discount_value": 5,
            "shipping_charge": 100,
            "adjustment": 0,
            "delivery_method": "delivery",
            "line_items": [
                {
                    "item_id": TEST_ITEM_ID,
                    "name": "TEST EV Battery Service",
                    "description": "Test service item",
                    "quantity": 2,
                    "unit": "service",
                    "rate": 2500,
                    "discount_percent": 0,
                    "tax_percentage": 18,
                    "hsn_code": "998719"
                },
                {
                    "name": "TEST Custom Item",
                    "description": "Custom line item for testing",
                    "quantity": 1,
                    "unit": "pcs",
                    "rate": 1000,
                    "discount_percent": 10,
                    "tax_percentage": 18,
                    "hsn_code": "999999"
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "salesorder" in data
        assert data["salesorder"]["status"] == "draft"
        assert data["salesorder"]["customer_id"] == TEST_CUSTOMER_ID
        assert len(data["salesorder"]["line_items"]) == 2
        
        # Store for later tests
        TestSalesOrdersCRUD.created_order_id = data["salesorder"]["salesorder_id"]
        TestSalesOrdersCRUD.created_order_number = data["salesorder"]["salesorder_number"]
        
        print(f"✓ Sales Order created: {data['salesorder']['salesorder_number']} (ID: {data['salesorder']['salesorder_id']})")
        print(f"  Grand Total: ₹{data['salesorder']['grand_total']}")
    
    def test_02_list_sales_orders(self):
        """GET /api/sales-orders-enhanced/ - List sales orders with filters"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "salesorders" in data
        assert "page_context" in data
        print(f"✓ Listed {len(data['salesorders'])} sales orders")
    
    def test_03_list_with_status_filter(self):
        """GET /api/sales-orders-enhanced/?status=draft - Filter by status"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/?status=draft")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for order in data["salesorders"]:
            assert order["status"] == "draft"
        print(f"✓ Filtered by status=draft: {len(data['salesorders'])} orders")
    
    def test_04_get_sales_order_detail(self):
        """GET /api/sales-orders-enhanced/{id} - Get sales order details with line items, fulfillments, history"""
        assert TestSalesOrdersCRUD.created_order_id is not None
        
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersCRUD.created_order_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "salesorder" in data
        assert "line_items" in data["salesorder"]
        assert "history" in data["salesorder"]
        assert "fulfillments" in data["salesorder"]
        assert data["salesorder"]["salesorder_id"] == TestSalesOrdersCRUD.created_order_id
        print(f"✓ Retrieved order detail: {data['salesorder']['salesorder_number']}")
        print(f"  Line items: {len(data['salesorder']['line_items'])}")
        print(f"  History entries: {len(data['salesorder']['history'])}")
    
    def test_05_update_draft_sales_order(self):
        """PUT /api/sales-orders-enhanced/{id} - Update draft sales order"""
        assert TestSalesOrdersCRUD.created_order_id is not None
        
        payload = {
            "reference_number": "TEST-PO-001-UPDATED",
            "notes": "Updated notes for testing",
            "shipping_charge": 150
        }
        
        response = requests.put(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersCRUD.created_order_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["salesorder"]["reference_number"] == "TEST-PO-001-UPDATED"
        assert data["salesorder"]["shipping_charge"] == 150
        print(f"✓ Updated sales order: reference={data['salesorder']['reference_number']}")


class TestSalesOrdersLineItems:
    """Test line item operations"""
    
    added_line_item_id = None
    
    def test_01_add_line_item(self):
        """POST /api/sales-orders-enhanced/{id}/line-items - Add line item"""
        assert TestSalesOrdersCRUD.created_order_id is not None
        
        payload = {
            "name": "TEST Additional Item",
            "description": "Added via API test",
            "quantity": 3,
            "unit": "pcs",
            "rate": 500,
            "discount_percent": 5,
            "tax_percentage": 18,
            "hsn_code": "888888"
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersCRUD.created_order_id}/line-items", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "line_item" in data
        assert data["line_item"]["name"] == "TEST Additional Item"
        
        TestSalesOrdersLineItems.added_line_item_id = data["line_item"]["line_item_id"]
        print(f"✓ Added line item: {data['line_item']['name']} (ID: {data['line_item']['line_item_id']})")
    
    def test_02_update_line_item(self):
        """PUT /api/sales-orders-enhanced/{id}/line-items/{line_id} - Update line item"""
        assert TestSalesOrdersCRUD.created_order_id is not None
        assert TestSalesOrdersLineItems.added_line_item_id is not None
        
        payload = {
            "quantity": 5,
            "rate": 600
        }
        
        response = requests.put(
            f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersCRUD.created_order_id}/line-items/{TestSalesOrdersLineItems.added_line_item_id}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["line_item"]["quantity"] == 5
        assert data["line_item"]["rate"] == 600
        print(f"✓ Updated line item: qty={data['line_item']['quantity']}, rate={data['line_item']['rate']}")
    
    def test_03_delete_line_item(self):
        """DELETE /api/sales-orders-enhanced/{id}/line-items/{line_id} - Delete line item"""
        assert TestSalesOrdersCRUD.created_order_id is not None
        assert TestSalesOrdersLineItems.added_line_item_id is not None
        
        response = requests.delete(
            f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersCRUD.created_order_id}/line-items/{TestSalesOrdersLineItems.added_line_item_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Deleted line item: {TestSalesOrdersLineItems.added_line_item_id}")


class TestSalesOrdersWorkflow:
    """Test status workflow: confirm, fulfill, convert, void"""
    
    confirmed_order_id = None
    confirmed_order_number = None
    
    def test_01_create_order_for_workflow(self):
        """Create a new order for workflow testing"""
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "reference_number": "TEST-WORKFLOW-001",
            "date": "2026-02-17",
            "expected_shipment_date": "2026-02-24",
            "notes": "Order for workflow testing",
            "line_items": [
                {
                    "name": "TEST Workflow Item 1",
                    "quantity": 5,
                    "unit": "pcs",
                    "rate": 1000,
                    "tax_percentage": 18
                },
                {
                    "name": "TEST Workflow Item 2",
                    "quantity": 3,
                    "unit": "pcs",
                    "rate": 500,
                    "tax_percentage": 18
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        TestSalesOrdersWorkflow.confirmed_order_id = data["salesorder"]["salesorder_id"]
        TestSalesOrdersWorkflow.confirmed_order_number = data["salesorder"]["salesorder_number"]
        print(f"✓ Created workflow test order: {data['salesorder']['salesorder_number']}")
    
    def test_02_confirm_order(self):
        """POST /api/sales-orders-enhanced/{id}/confirm - Confirm order and reserve stock"""
        assert TestSalesOrdersWorkflow.confirmed_order_id is not None
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}/confirm")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status changed
        detail_response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}")
        detail_data = detail_response.json()
        assert detail_data["salesorder"]["status"] == "confirmed"
        print(f"✓ Order confirmed: {TestSalesOrdersWorkflow.confirmed_order_number}")
    
    def test_03_create_fulfillment(self):
        """POST /api/sales-orders-enhanced/{id}/fulfill - Create fulfillment/shipment"""
        assert TestSalesOrdersWorkflow.confirmed_order_id is not None
        
        # Get line items first
        detail_response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}")
        detail_data = detail_response.json()
        line_items = detail_data["salesorder"]["line_items"]
        
        # Fulfill partial quantities
        fulfillment_items = [
            {
                "line_item_id": line_items[0]["line_item_id"],
                "quantity_to_fulfill": 3  # Partial fulfillment
            },
            {
                "line_item_id": line_items[1]["line_item_id"],
                "quantity_to_fulfill": 2  # Partial fulfillment
            }
        ]
        
        payload = {
            "line_items": fulfillment_items,
            "shipment_date": "2026-02-17",
            "tracking_number": "TEST-TRACK-001",
            "carrier": "Test Carrier",
            "notes": "Test fulfillment"
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}/fulfill", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "fulfillment" in data
        print(f"✓ Fulfillment created: {data['fulfillment']['fulfillment_id']}")
        
        # Verify fulfillment status
        detail_response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}")
        detail_data = detail_response.json()
        # Should be partially_fulfilled or open since we didn't fulfill all
        assert detail_data["salesorder"]["fulfillment_status"] in ["partially_fulfilled", "unfulfilled"]
        print(f"  Fulfillment status: {detail_data['salesorder']['fulfillment_status']}")
    
    def test_04_get_fulfillments(self):
        """GET /api/sales-orders-enhanced/{id}/fulfillments - Get all fulfillments"""
        assert TestSalesOrdersWorkflow.confirmed_order_id is not None
        
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}/fulfillments")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "fulfillments" in data
        assert len(data["fulfillments"]) >= 1
        print(f"✓ Retrieved {len(data['fulfillments'])} fulfillments")
    
    def test_05_convert_to_invoice(self):
        """POST /api/sales-orders-enhanced/{id}/convert-to-invoice - Convert to invoice"""
        assert TestSalesOrdersWorkflow.confirmed_order_id is not None
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}/convert-to-invoice")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "invoice_id" in data
        assert "invoice_number" in data
        print(f"✓ Converted to Invoice: {data['invoice_number']}")
        
        # Verify converted_to is set
        detail_response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}")
        detail_data = detail_response.json()
        assert detail_data["salesorder"]["converted_to"] is not None
        print(f"  Converted to: {detail_data['salesorder']['converted_to']}")


class TestSalesOrdersCloneAndSend:
    """Test clone and send operations"""
    
    def test_01_clone_sales_order(self):
        """POST /api/sales-orders-enhanced/{id}/clone - Clone sales order"""
        assert TestSalesOrdersCRUD.created_order_id is not None
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersCRUD.created_order_id}/clone")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "salesorder_id" in data
        assert "salesorder_number" in data
        print(f"✓ Cloned order: {data['salesorder_number']}")
        
        # Verify cloned order is draft
        detail_response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{data['salesorder_id']}")
        detail_data = detail_response.json()
        assert detail_data["salesorder"]["status"] == "draft"
        print(f"  Cloned order status: {detail_data['salesorder']['status']}")
    
    def test_02_send_sales_order(self):
        """POST /api/sales-orders-enhanced/{id}/send - Send order email (mocked)"""
        assert TestSalesOrdersCRUD.created_order_id is not None
        
        response = requests.post(
            f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersCRUD.created_order_id}/send",
            params={"email_to": "test@example.com", "message": "Test message"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Send order (MOCKED): {data['message']}")


class TestSalesOrdersVoidAndDelete:
    """Test void and delete operations"""
    
    void_order_id = None
    
    def test_01_create_order_for_void(self):
        """Create order for void testing"""
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "reference_number": "TEST-VOID-001",
            "line_items": [
                {"name": "TEST Void Item", "quantity": 1, "rate": 100, "tax_percentage": 18}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        TestSalesOrdersVoidAndDelete.void_order_id = data["salesorder"]["salesorder_id"]
        print(f"✓ Created order for void test: {data['salesorder']['salesorder_number']}")
    
    def test_02_confirm_then_void(self):
        """POST /api/sales-orders-enhanced/{id}/void - Void order and release stock"""
        assert TestSalesOrdersVoidAndDelete.void_order_id is not None
        
        # First confirm
        requests.post(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersVoidAndDelete.void_order_id}/confirm")
        
        # Then void
        response = requests.post(
            f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersVoidAndDelete.void_order_id}/void",
            params={"reason": "Test void reason"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status
        detail_response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersVoidAndDelete.void_order_id}")
        detail_data = detail_response.json()
        assert detail_data["salesorder"]["status"] == "void"
        print(f"✓ Order voided: {detail_data['salesorder']['salesorder_number']}")
    
    def test_03_delete_draft_order(self):
        """DELETE /api/sales-orders-enhanced/{id} - Delete draft sales order only"""
        # Create a new draft order to delete
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "reference_number": "TEST-DELETE-001",
            "line_items": [
                {"name": "TEST Delete Item", "quantity": 1, "rate": 100, "tax_percentage": 18}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/", json=payload)
        assert response.status_code == 200
        delete_order_id = response.json()["salesorder"]["salesorder_id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/sales-orders-enhanced/{delete_order_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Deleted draft order: {delete_order_id}")
    
    def test_04_cannot_delete_confirmed_order(self):
        """Verify confirmed orders cannot be deleted"""
        assert TestSalesOrdersWorkflow.confirmed_order_id is not None
        
        response = requests.delete(f"{BASE_URL}/api/sales-orders-enhanced/{TestSalesOrdersWorkflow.confirmed_order_id}")
        assert response.status_code == 400
        print(f"✓ Correctly rejected deletion of confirmed order")


class TestSalesOrdersEdgeCases:
    """Test edge cases and validation"""
    
    def test_invalid_customer(self):
        """Test creating order with invalid customer"""
        payload = {
            "customer_id": "INVALID-CUSTOMER-ID",
            "line_items": [
                {"name": "Test Item", "quantity": 1, "rate": 100, "tax_percentage": 18}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders-enhanced/", json=payload)
        assert response.status_code == 404
        print(f"✓ Correctly rejected invalid customer")
    
    def test_get_nonexistent_order(self):
        """Test getting non-existent order"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/NONEXISTENT-ORDER-ID")
        assert response.status_code == 404
        print(f"✓ Correctly returned 404 for non-existent order")
    
    def test_search_orders(self):
        """Test search functionality"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/?search=TEST")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Search returned {len(data['salesorders'])} results")


# Cleanup test - run last
class TestZZCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_orders(self):
        """Delete test orders created during testing"""
        # Get all orders with TEST in reference
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/?search=TEST&per_page=100")
        if response.status_code == 200:
            data = response.json()
            deleted = 0
            for order in data.get("salesorders", []):
                if order.get("status") == "draft":
                    del_response = requests.delete(f"{BASE_URL}/api/sales-orders-enhanced/{order['salesorder_id']}")
                    if del_response.status_code == 200:
                        deleted += 1
            print(f"✓ Cleanup: deleted {deleted} test draft orders")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
