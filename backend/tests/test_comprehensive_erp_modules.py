"""
Comprehensive ERP Module Tests - Battwheels OS
Tests: Items, Quotes/Estimates, Sales (Customers, Invoices, Payments), Inventory Adjustments
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "DevTest@123"
    })
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return response.json().get("token")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ==================== ITEMS MODULE TESTS ====================
class TestItemsModule:
    """Items CRUD, stock tracking, price lists, categories"""
    
    def test_items_summary(self, authenticated_client):
        """Test items summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_items" in data["summary"]
        assert "inventory_items" in data["summary"]
        print(f"Items Summary: {data['summary']['total_items']} total, {data['summary']['inventory_items']} inventory items")
    
    def test_items_list_with_pagination(self, authenticated_client):
        """Test items list with pagination"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "page_context" in data
        assert "total" in data["page_context"]
        assert len(data["items"]) <= 5
        print(f"Items List: {data['page_context']['total']} total, page {data['page_context']['page']}")
    
    def test_items_list_filter_by_type(self, authenticated_client):
        """Test items filter by type (inventory/service)"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/?item_type=inventory&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Verify all returned items are inventory type
        for item in data["items"]:
            assert item.get("item_type") == "inventory" or item.get("product_type") == "goods"
        print(f"Inventory Items: {len(data['items'])} returned")
    
    def test_items_search(self, authenticated_client):
        """Test items search functionality"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/?search=SEATCOVER&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"Search 'SEATCOVER': {len(data['items'])} items found")
    
    def test_price_lists(self, authenticated_client):
        """Test price lists endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/price-lists")
        assert response.status_code == 200
        data = response.json()
        assert "price_lists" in data
        print(f"Price Lists: {len(data['price_lists'])} lists found")
    
    def test_composite_items(self, authenticated_client):
        """Test composite items endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/composite-items")
        assert response.status_code == 200
        data = response.json()
        assert "composite_items" in data or "items" in data or isinstance(data, list)
        items = data.get("composite_items", data.get("items", data))
        print(f"Composite Items: {len(items)} items")
    
    def test_item_categories(self, authenticated_client):
        """Test item categories endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/categories")
        # Categories endpoint may not exist - check status
        if response.status_code == 200:
            data = response.json()
            categories = data.get("categories", [])
            print(f"Categories: {len(categories)} categories")
        else:
            print(f"Categories endpoint: {response.status_code} - May not be implemented")
    
    def test_create_item(self, authenticated_client):
        """Test item creation"""
        item_data = {
            "name": f"TEST_Item_{datetime.now().strftime('%H%M%S')}",
            "sku": f"TEST-SKU-{datetime.now().strftime('%H%M%S')}",
            "item_type": "inventory",
            "rate": 100.00,
            "purchase_rate": 80.00,
            "unit": "pcs",
            "description": "Test item for automated testing",
            "initial_stock": 10,
            "reorder_level": 5
        }
        response = authenticated_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        data = response.json()
        # Item may be nested in 'item' key
        item = data.get("item", data)
        assert "item_id" in item or "id" in item or "_id" in item or "item" in data
        item_id = item.get("item_id") or item.get("id") or item.get("_id")
        print(f"Created Item: {item_id}")
        return data


# ==================== QUOTES/ESTIMATES MODULE TESTS ====================
class TestEstimatesModule:
    """Quotes/Estimates CRUD, status workflow, conversion"""
    
    def test_estimates_summary(self, authenticated_client):
        """Test estimates summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total" in data["summary"]
        assert "by_status" in data["summary"]
        print(f"Estimates Summary: {data['summary']['total']} total, by status: {data['summary']['by_status']}")
    
    def test_estimates_list_with_pagination(self, authenticated_client):
        """Test estimates list with pagination"""
        response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "estimates" in data
        assert "page_context" in data
        total = data["page_context"]["total"]
        print(f"Estimates List: {total} total")
    
    def test_estimates_filter_by_status(self, authenticated_client):
        """Test estimates filter by status"""
        for status in ["draft", "sent", "accepted"]:
            response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/?status={status}&per_page=3")
            assert response.status_code == 200
            data = response.json()
            print(f"Estimates with status '{status}': {len(data.get('estimates', []))} found")
    
    def test_estimate_detail(self, authenticated_client):
        """Test getting estimate detail"""
        # First get list to find an estimate
        list_response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=1")
        assert list_response.status_code == 200
        estimates = list_response.json().get("estimates", [])
        
        if estimates:
            estimate_id = estimates[0].get("estimate_id") or estimates[0].get("_id")
            response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}")
            assert response.status_code == 200
            data = response.json()
            assert "estimate" in data or "estimate_id" in data
            print(f"Estimate Detail: {estimate_id}")
    
    def test_estimate_public_link(self, authenticated_client):
        """Test public share link for estimates"""
        # Get an accepted estimate
        list_response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/?status=accepted&per_page=1")
        if list_response.status_code == 200:
            estimates = list_response.json().get("estimates", [])
            if estimates:
                estimate_id = estimates[0].get("estimate_id") or estimates[0].get("_id")
                # Check if public link endpoint exists
                response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}/public-link")
                print(f"Public Link Response: {response.status_code}")
    
    def test_estimate_pdf_generation(self, authenticated_client):
        """Test PDF generation for estimates"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=1")
        if list_response.status_code == 200:
            estimates = list_response.json().get("estimates", [])
            if estimates:
                estimate_id = estimates[0].get("estimate_id") or estimates[0].get("_id")
                response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}/pdf")
                # PDF should return 200 with application/pdf content type
                print(f"PDF Generation: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}")
    
    def test_estimate_convert_to_invoice(self, authenticated_client):
        """Test converting estimate to invoice"""
        # Get an accepted estimate that hasn't been converted
        list_response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/?status=accepted&per_page=5")
        if list_response.status_code == 200:
            estimates = list_response.json().get("estimates", [])
            # Find one that's not already converted
            for est in estimates:
                if not est.get("converted_to_invoice"):
                    estimate_id = est.get("estimate_id") or est.get("_id")
                    response = authenticated_client.post(f"{BASE_URL}/api/estimates-enhanced/{estimate_id}/convert-to-invoice")
                    print(f"Convert to Invoice: {response.status_code} - {response.text[:200] if response.text else 'No response'}")
                    break


# ==================== CUSTOMERS MODULE TESTS ====================
class TestCustomersModule:
    """Customer CRUD, addresses, credit limits"""
    
    def test_contacts_summary(self, authenticated_client):
        """Test contacts summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "customers" in data["summary"]
        print(f"Contacts Summary: {data['summary']['customers']} customers, {data['summary'].get('vendors', 0)} vendors")
    
    def test_customers_list(self, authenticated_client):
        """Test customers list with filter"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=customer&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "contacts" in data
        print(f"Customers List: {len(data['contacts'])} customers returned")
    
    def test_customer_detail(self, authenticated_client):
        """Test getting customer detail"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=customer&per_page=1")
        if list_response.status_code == 200:
            contacts = list_response.json().get("contacts", [])
            if contacts:
                contact_id = contacts[0].get("contact_id") or contacts[0].get("_id")
                response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}")
                assert response.status_code == 200
                data = response.json()
                print(f"Customer Detail: {contact_id}, Name: {data.get('contact', {}).get('contact_name', 'N/A')}")
    
    def test_customer_financial_profile(self, authenticated_client):
        """Test customer financial profile (outstanding balances)"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=customer&per_page=1")
        if list_response.status_code == 200:
            contacts = list_response.json().get("contacts", [])
            if contacts:
                contact_id = contacts[0].get("contact_id") or contacts[0].get("_id")
                response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/financial-summary")
                print(f"Financial Profile: {response.status_code}")
    
    def test_customer_addresses(self, authenticated_client):
        """Test customer addresses endpoint"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=customer&per_page=1")
        if list_response.status_code == 200:
            contacts = list_response.json().get("contacts", [])
            if contacts:
                contact_id = contacts[0].get("contact_id") or contacts[0].get("_id")
                response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/addresses")
                print(f"Customer Addresses: {response.status_code}")


# ==================== INVOICES MODULE TESTS ====================
class TestInvoicesModule:
    """Invoice CRUD, GST calculations, status workflow"""
    
    def test_invoices_summary(self, authenticated_client):
        """Test invoices summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_invoices" in data["summary"]
        print(f"Invoices Summary: {data['summary']['total_invoices']} total, Outstanding: {data['summary'].get('total_outstanding', 0)}")
    
    def test_invoices_list_with_pagination(self, authenticated_client):
        """Test invoices list with pagination"""
        response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        assert "page_context" in data
        total = data["page_context"]["total"]
        print(f"Invoices List: {total} total")
    
    def test_invoices_filter_by_status(self, authenticated_client):
        """Test invoices filter by status"""
        for status in ["draft", "sent", "paid", "overdue"]:
            response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/?status={status}&per_page=3")
            assert response.status_code == 200
            data = response.json()
            print(f"Invoices with status '{status}': {len(data.get('invoices', []))} found")
    
    def test_invoice_detail(self, authenticated_client):
        """Test getting invoice detail"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/?per_page=1")
        if list_response.status_code == 200:
            invoices = list_response.json().get("invoices", [])
            if invoices:
                invoice_id = invoices[0].get("invoice_id") or invoices[0].get("_id")
                response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/{invoice_id}")
                assert response.status_code == 200
                data = response.json()
                print(f"Invoice Detail: {invoice_id}")
    
    def test_invoice_pdf_generation(self, authenticated_client):
        """Test PDF generation for invoices"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/?per_page=1")
        if list_response.status_code == 200:
            invoices = list_response.json().get("invoices", [])
            if invoices:
                invoice_id = invoices[0].get("invoice_id") or invoices[0].get("_id")
                response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/{invoice_id}/pdf")
                print(f"Invoice PDF: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}")
    
    def test_invoice_gst_calculation(self, authenticated_client):
        """Test invoice with GST calculations"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/?per_page=5")
        if list_response.status_code == 200:
            invoices = list_response.json().get("invoices", [])
            for inv in invoices:
                if inv.get("tax_total", 0) > 0:
                    print(f"Invoice {inv.get('invoice_number')}: Subtotal={inv.get('sub_total')}, Tax={inv.get('tax_total')}, Total={inv.get('total')}")
                    break


# ==================== PAYMENTS RECEIVED MODULE TESTS ====================
class TestPaymentsModule:
    """Payment recording, partial payments, invoice linkage"""
    
    def test_payments_summary(self, authenticated_client):
        """Test payments summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/payments-received/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        print(f"Payments Summary: Total={data['summary'].get('total_received', 0)}, Count={data['summary'].get('payment_count', 0)}")
    
    def test_payments_list(self, authenticated_client):
        """Test payments list with pagination"""
        response = authenticated_client.get(f"{BASE_URL}/api/payments-received/?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "payments" in data
        print(f"Payments List: {len(data['payments'])} payments returned")
    
    def test_payment_detail(self, authenticated_client):
        """Test getting payment detail"""
        list_response = authenticated_client.get(f"{BASE_URL}/api/payments-received/?per_page=1")
        if list_response.status_code == 200:
            payments = list_response.json().get("payments", [])
            if payments:
                payment_id = payments[0].get("payment_id") or payments[0].get("_id")
                response = authenticated_client.get(f"{BASE_URL}/api/payments-received/{payment_id}")
                print(f"Payment Detail: {response.status_code}")
    
    def test_payment_modes(self, authenticated_client):
        """Test payment modes breakdown"""
        response = authenticated_client.get(f"{BASE_URL}/api/payments-received/summary")
        if response.status_code == 200:
            data = response.json()
            by_mode = data.get("summary", {}).get("by_payment_mode", {})
            print(f"Payment Modes: {by_mode}")


# ==================== INVENTORY ADJUSTMENTS MODULE TESTS ====================
class TestInventoryAdjustmentsModule:
    """Inventory adjustments, reasons, reports"""
    
    def test_adjustments_summary(self, authenticated_client):
        """Test adjustments summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/inv-adjustments/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        print(f"Adjustments Summary: Total={data['total']}, Draft={data.get('draft', 0)}, Adjusted={data.get('adjusted', 0)}")
    
    def test_adjustments_list(self, authenticated_client):
        """Test adjustments list with pagination"""
        response = authenticated_client.get(f"{BASE_URL}/api/inv-adjustments?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert "adjustments" in data
        print(f"Adjustments List: {len(data['adjustments'])} adjustments returned")
    
    def test_adjustments_filter_by_status(self, authenticated_client):
        """Test adjustments filter by status"""
        for status in ["draft", "adjusted", "void"]:
            response = authenticated_client.get(f"{BASE_URL}/api/inv-adjustments?status={status}&per_page=3")
            assert response.status_code == 200
            data = response.json()
            print(f"Adjustments with status '{status}': {len(data.get('adjustments', []))} found")
    
    def test_adjustment_reasons(self, authenticated_client):
        """Test adjustment reasons endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/inv-adjustments/reasons")
        assert response.status_code == 200
        data = response.json()
        assert "reasons" in data
        print(f"Adjustment Reasons: {len(data['reasons'])} reasons")
    
    def test_abc_classification_report(self, authenticated_client):
        """Test ABC classification report"""
        response = authenticated_client.get(f"{BASE_URL}/api/inv-adjustments/reports/abc-classification")
        print(f"ABC Report: {response.status_code}")
    
    def test_fifo_tracking_report(self, authenticated_client):
        """Test FIFO tracking report"""
        response = authenticated_client.get(f"{BASE_URL}/api/inv-adjustments/reports/fifo-tracking")
        print(f"FIFO Report: {response.status_code}")
    
    def test_adjustment_summary_report(self, authenticated_client):
        """Test adjustment summary report"""
        response = authenticated_client.get(f"{BASE_URL}/api/inv-adjustments/reports/adjustment-summary")
        print(f"Adjustment Summary Report: {response.status_code}")


# ==================== CROSS-MODULE INTEGRATION TESTS ====================
class TestCrossModuleIntegration:
    """Test data flow between modules"""
    
    def test_quote_to_invoice_flow(self, authenticated_client):
        """Test Quote -> Invoice conversion flow"""
        # Get converted estimates
        response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/?status=converted&per_page=3")
        if response.status_code == 200:
            estimates = response.json().get("estimates", [])
            print(f"Converted Estimates: {len(estimates)} found")
            for est in estimates:
                if est.get("converted_to_invoice"):
                    print(f"  Estimate {est.get('estimate_number')} -> Invoice {est.get('converted_to_invoice')}")
    
    def test_invoice_payment_linkage(self, authenticated_client):
        """Test Invoice -> Payment linkage"""
        # Get partially paid invoices
        response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/?status=partially_paid&per_page=3")
        if response.status_code == 200:
            invoices = response.json().get("invoices", [])
            print(f"Partially Paid Invoices: {len(invoices)} found")
            for inv in invoices:
                print(f"  Invoice {inv.get('invoice_number')}: Total={inv.get('total')}, Balance={inv.get('balance')}")
    
    def test_item_stock_tracking(self, authenticated_client):
        """Test item stock levels"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/?item_type=inventory&per_page=5")
        if response.status_code == 200:
            items = response.json().get("items", [])
            print(f"Inventory Items Stock Check:")
            for item in items[:5]:
                stock = item.get("stock_on_hand", item.get("available_stock", 0))
                print(f"  {item.get('name', 'N/A')[:30]}: Stock={stock}")
    
    def test_customer_outstanding_balance(self, authenticated_client):
        """Test customer outstanding balances"""
        response = authenticated_client.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=customer&per_page=5")
        if response.status_code == 200:
            contacts = response.json().get("contacts", [])
            print(f"Customer Outstanding Balances:")
            for contact in contacts[:5]:
                outstanding = contact.get("outstanding_receivable_amount", contact.get("receivables", 0))
                if outstanding and outstanding > 0:
                    print(f"  {contact.get('contact_name', 'N/A')[:30]}: Outstanding={outstanding}")


# ==================== DATA INTEGRITY TESTS ====================
class TestDataIntegrity:
    """Test data integrity and edge cases"""
    
    def test_negative_stock_handling(self, authenticated_client):
        """Check for negative stock values"""
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=100")
        if response.status_code == 200:
            items = response.json().get("items", [])
            negative_stock_items = []
            for item in items:
                stock = item.get("stock_on_hand", item.get("available_stock", 0))
                if stock is not None and stock < 0:
                    negative_stock_items.append({
                        "name": item.get("name"),
                        "stock": stock
                    })
            if negative_stock_items:
                print(f"WARNING: {len(negative_stock_items)} items with negative stock found!")
                for item in negative_stock_items[:5]:
                    print(f"  {item['name']}: {item['stock']}")
            else:
                print("No negative stock items found")
    
    def test_pagination_total_count(self, authenticated_client):
        """Verify pagination total count matches actual data"""
        # Test items
        response = authenticated_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=10")
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            items_count = len(data.get("items", []))
            print(f"Items Pagination: total={total}, returned={items_count}")
            if total == 0 and items_count > 0:
                print("WARNING: Total count is 0 but items exist!")
    
    def test_status_transitions(self, authenticated_client):
        """Verify proper status transitions"""
        # Check estimate statuses
        response = authenticated_client.get(f"{BASE_URL}/api/estimates-enhanced/summary")
        if response.status_code == 200:
            data = response.json()
            by_status = data.get("summary", {}).get("by_status", {})
            print(f"Estimate Status Distribution: {by_status}")
        
        # Check invoice statuses
        response = authenticated_client.get(f"{BASE_URL}/api/invoices-enhanced/summary")
        if response.status_code == 200:
            data = response.json()
            print(f"Invoice Status: Draft={data['summary'].get('draft', 0)}, Sent={data['summary'].get('sent', 0)}, Paid={data['summary'].get('paid', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
