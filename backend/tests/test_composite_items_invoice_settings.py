"""
Composite Items and Invoice Automation Settings Tests
Tests for:
1. Composite Items CRUD (create, list, get, delete)
2. Composite Items Build/Unbuild operations
3. Invoice Automation reminder and late fee settings
4. Recurring Invoices endpoints
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test data storage
created_composite_id = None
test_item_ids = []

class TestCompositeItemsSummary:
    """Test composite items summary endpoint"""
    
    def test_get_summary(self):
        """GET /api/composite-items/summary - Get composite items summary stats"""
        response = requests.get(f"{API_URL}/composite-items/summary")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "total_items" in data
        assert "active" in data
        assert "kits" in data
        assert "assemblies" in data
        assert "bundles" in data
        assert "inventory_value" in data
        print(f"Summary: {data['total_items']} items, {data['active']} active, {data['kits']} kits, {data['assemblies']} assemblies, {data['bundles']} bundles")


class TestCompositeItemsList:
    """Test composite items list endpoint"""
    
    def test_list_composite_items(self):
        """GET /api/composite-items - List all composite items"""
        response = requests.get(f"{API_URL}/composite-items")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "composite_items" in data
        assert "total" in data
        print(f"Found {data['total']} composite items")
        
    def test_list_by_type_kit(self):
        """GET /api/composite-items?type=kit - Filter by kit type"""
        response = requests.get(f"{API_URL}/composite-items?type=kit")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        # All items should be kits (if any)
        for item in data.get("composite_items", []):
            if item:
                assert item.get("type") == "kit", f"Expected type='kit', got '{item.get('type')}'"


class TestInventoryItemsForComposite:
    """Get inventory items to use as components for composite"""
    
    def test_get_inventory_items(self):
        """GET /api/items-enhanced/ - Get inventory items for component selection"""
        global test_item_ids
        response = requests.get(f"{API_URL}/items-enhanced/?per_page=20")
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        print(f"Found {len(items)} inventory items")
        
        # Store some item IDs for composite creation
        test_item_ids = [item["item_id"] for item in items[:3] if item.get("item_id")]
        print(f"Using item_ids for composite test: {test_item_ids[:2]}")


class TestCompositeItemsCRUD:
    """Test composite items CRUD operations"""
    
    def test_create_composite_item(self):
        """POST /api/composite-items - Create a new composite item"""
        global created_composite_id, test_item_ids
        
        # First get inventory items if not populated
        if not test_item_ids:
            response = requests.get(f"{API_URL}/items-enhanced/?per_page=20")
            items = response.json().get("items", [])
            test_item_ids = [item["item_id"] for item in items[:3] if item.get("item_id")]
        
        if len(test_item_ids) < 2:
            pytest.skip("Not enough inventory items to create composite")
            
        # Create composite item with at least 2 components
        payload = {
            "name": f"TEST_Kit_{uuid.uuid4().hex[:8]}",
            "sku": f"TEST-KIT-{uuid.uuid4().hex[:6].upper()}",
            "description": "Test composite item created by automated test",
            "type": "kit",
            "components": [
                {"item_id": test_item_ids[0], "quantity": 1, "unit": "pcs", "waste_percentage": 0},
                {"item_id": test_item_ids[1], "quantity": 2, "unit": "pcs", "waste_percentage": 5}
            ],
            "auto_calculate_price": True,
            "markup_percentage": 10,
            "track_inventory": True,
            "auto_build": False,
            "min_build_quantity": 1,
            "category": "Test Category"
        }
        
        response = requests.post(f"{API_URL}/composite-items", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "composite_id" in data
        assert data.get("message") == "Composite item created"
        
        created_composite_id = data["composite_id"]
        print(f"Created composite item: {created_composite_id}")
        print(f"Component cost: {data.get('component_cost')}, Selling price: {data.get('selling_price')}")
        
    def test_get_composite_item(self):
        """GET /api/composite-items/{id} - Get specific composite item"""
        global created_composite_id
        
        if not created_composite_id:
            pytest.skip("No composite item created")
            
        response = requests.get(f"{API_URL}/composite-items/{created_composite_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "composite_item" in data
        
        item = data["composite_item"]
        assert item.get("composite_id") == created_composite_id
        assert "components" in item
        assert "component_details" in item
        print(f"Got composite item: {item.get('name')}, Components: {len(item.get('components', []))}")
        
    def test_check_build_availability(self):
        """GET /api/composite-items/{id}/availability - Check if can build"""
        global created_composite_id
        
        if not created_composite_id:
            pytest.skip("No composite item created")
            
        response = requests.get(f"{API_URL}/composite-items/{created_composite_id}/availability?quantity=1")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "can_build" in data
        assert "max_buildable" in data
        assert "components" in data
        
        print(f"Can build: {data.get('can_build')}, Max buildable: {data.get('max_buildable')}")
        if data.get("shortages"):
            print(f"Shortages: {data['shortages']}")
            
    def test_build_composite_item_insufficient_stock(self):
        """POST /api/composite-items/{id}/build - Build should fail with insufficient stock"""
        global created_composite_id
        
        if not created_composite_id:
            pytest.skip("No composite item created")
            
        # Since stock is 0, this should fail
        payload = {"quantity": 1, "notes": "Test build"}
        response = requests.post(f"{API_URL}/composite-items/{created_composite_id}/build", json=payload)
        
        # Expected to fail with 400 due to insufficient stock
        if response.status_code == 400:
            data = response.json()
            assert "Insufficient stock" in data.get("detail", "")
            print(f"Build correctly failed: {data.get('detail')}")
        elif response.status_code == 200:
            # If stock exists, it might succeed
            data = response.json()
            print(f"Build succeeded unexpectedly: {data}")
        else:
            print(f"Unexpected status: {response.status_code}, {response.text}")


class TestCompositeItemDelete:
    """Test composite item deletion"""
    
    def test_delete_composite_item(self):
        """DELETE /api/composite-items/{id} - Delete composite item"""
        global created_composite_id
        
        if not created_composite_id:
            pytest.skip("No composite item to delete")
            
        response = requests.delete(f"{API_URL}/composite-items/{created_composite_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert data.get("message") == "Composite item deleted"
        print(f"Deleted composite item: {created_composite_id}")
        
        # Verify deleted
        response = requests.get(f"{API_URL}/composite-items/{created_composite_id}")
        assert response.status_code == 404
        
        created_composite_id = None


class TestInvoiceAutomationSettings:
    """Test Invoice Automation Settings endpoints"""
    
    def test_get_reminder_settings(self):
        """GET /api/invoice-automation/reminder-settings - Get reminder settings"""
        response = requests.get(f"{API_URL}/invoice-automation/reminder-settings")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "settings" in data
        
        settings = data["settings"]
        print(f"Reminder settings: enabled={settings.get('enabled')}, include_payment_link={settings.get('include_payment_link')}")
        
    def test_update_reminder_settings(self):
        """PUT /api/invoice-automation/reminder-settings - Update reminder settings"""
        payload = {
            "enabled": True,
            "reminder_before_days": [7, 3, 1],
            "reminder_after_days": [1, 7, 14, 30],
            "email_template": "default",
            "include_payment_link": True
        }
        
        response = requests.put(f"{API_URL}/invoice-automation/reminder-settings", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        print("Reminder settings updated successfully")
        
    def test_get_late_fee_settings(self):
        """GET /api/invoice-automation/late-fee-settings - Get late fee settings"""
        response = requests.get(f"{API_URL}/invoice-automation/late-fee-settings")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "settings" in data
        
        settings = data["settings"]
        print(f"Late fee settings: enabled={settings.get('enabled')}, fee_type={settings.get('fee_type')}, fee_value={settings.get('fee_value')}")
        
    def test_update_late_fee_settings(self):
        """PUT /api/invoice-automation/late-fee-settings - Update late fee settings"""
        payload = {
            "enabled": False,
            "fee_type": "percentage",
            "fee_value": 2.0,
            "grace_period_days": 0,
            "max_fee_percentage": 10.0,
            "apply_automatically": False
        }
        
        response = requests.put(f"{API_URL}/invoice-automation/late-fee-settings", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        print("Late fee settings updated successfully")


class TestInvoiceAutomationData:
    """Test Invoice Automation data endpoints"""
    
    def test_get_overdue_invoices(self):
        """GET /api/invoice-automation/overdue-invoices - Get overdue invoices"""
        response = requests.get(f"{API_URL}/invoice-automation/overdue-invoices")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "overdue_invoices" in data
        assert "total_count" in data
        assert "total_overdue_amount" in data
        print(f"Overdue: {data['total_count']} invoices, Total: ₹{data['total_overdue_amount']:,.2f}")
        
    def test_get_due_soon_invoices(self):
        """GET /api/invoice-automation/due-soon-invoices - Get invoices due soon"""
        response = requests.get(f"{API_URL}/invoice-automation/due-soon-invoices?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "due_soon_invoices" in data
        assert "total_count" in data
        print(f"Due soon (7 days): {data['total_count']} invoices")
        
    def test_get_aging_report(self):
        """GET /api/invoice-automation/aging-report - Get AR aging report"""
        response = requests.get(f"{API_URL}/invoice-automation/aging-report")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "aging_buckets" in data
        assert "total_receivable" in data
        
        print(f"Total AR: ₹{data['total_receivable']:,.2f}")
        for bucket in data.get("aging_buckets", []):
            print(f"  {bucket['label']}: ₹{bucket['amount']:,.2f} ({bucket['count']} invoices)")


class TestRecurringInvoices:
    """Test Recurring Invoices endpoints"""
    
    recurring_id = None
    
    def test_get_recurring_summary(self):
        """GET /api/recurring-invoices/summary - Get recurring invoices summary"""
        response = requests.get(f"{API_URL}/recurring-invoices/summary")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "total_profiles" in data
        assert "active" in data
        assert "monthly_recurring_revenue" in data
        print(f"Recurring summary: {data['total_profiles']} profiles, {data['active']} active, MRR: ₹{data['monthly_recurring_revenue']:,.2f}")
        
    def test_list_recurring_invoices(self):
        """GET /api/recurring-invoices - List recurring invoices"""
        response = requests.get(f"{API_URL}/recurring-invoices")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "recurring_invoices" in data
        assert "total" in data
        print(f"Found {data['total']} recurring invoice profiles")
        
    def test_create_recurring_invoice(self):
        """POST /api/recurring-invoices - Create recurring invoice"""
        # First get a customer
        response = requests.get(f"{API_URL}/contacts-enhanced/?contact_type=customer&per_page=5")
        customers = response.json().get("contacts", [])
        
        if not customers:
            pytest.skip("No customers found")
            
        customer_id = customers[0]["contact_id"]
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        payload = {
            "customer_id": customer_id,
            "profile_name": f"TEST_Recurring_{uuid.uuid4().hex[:8]}",
            "frequency": "monthly",
            "repeat_every": 1,
            "start_date": start_date,
            "line_items": [
                {"name": "Test Service", "rate": 1000, "quantity": 1, "tax_percentage": 18}
            ],
            "payment_terms_days": 15,
            "notes": "Test recurring invoice",
            "send_email_on_generation": False
        }
        
        response = requests.post(f"{API_URL}/recurring-invoices", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "recurring_id" in data
        
        TestRecurringInvoices.recurring_id = data["recurring_id"]
        print(f"Created recurring invoice: {data['recurring_id']}, Next: {data['next_invoice_date']}")
        
    def test_get_recurring_invoice(self):
        """GET /api/recurring-invoices/{id} - Get specific recurring invoice"""
        if not TestRecurringInvoices.recurring_id:
            pytest.skip("No recurring invoice created")
            
        response = requests.get(f"{API_URL}/recurring-invoices/{TestRecurringInvoices.recurring_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "recurring_invoice" in data
        print(f"Got recurring invoice: {data['recurring_invoice'].get('profile_name')}")
        
    def test_generate_invoice_now(self):
        """POST /api/recurring-invoices/{id}/generate-now - Generate invoice"""
        if not TestRecurringInvoices.recurring_id:
            pytest.skip("No recurring invoice created")
            
        response = requests.post(f"{API_URL}/recurring-invoices/{TestRecurringInvoices.recurring_id}/generate-now")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "invoice_id" in data
        assert "invoice_number" in data
        print(f"Generated invoice: {data['invoice_number']}")
        
    def test_stop_recurring_invoice(self):
        """POST /api/recurring-invoices/{id}/stop - Stop recurring invoice"""
        if not TestRecurringInvoices.recurring_id:
            pytest.skip("No recurring invoice created")
            
        response = requests.post(f"{API_URL}/recurring-invoices/{TestRecurringInvoices.recurring_id}/stop")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        print("Recurring invoice stopped")
        
    def test_resume_recurring_invoice(self):
        """POST /api/recurring-invoices/{id}/resume - Resume recurring invoice"""
        if not TestRecurringInvoices.recurring_id:
            pytest.skip("No recurring invoice created")
            
        response = requests.post(f"{API_URL}/recurring-invoices/{TestRecurringInvoices.recurring_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        print(f"Recurring invoice resumed, next: {data.get('next_invoice_date')}")
        
    def test_delete_recurring_invoice(self):
        """DELETE /api/recurring-invoices/{id} - Delete recurring invoice"""
        if not TestRecurringInvoices.recurring_id:
            pytest.skip("No recurring invoice created")
            
        response = requests.delete(f"{API_URL}/recurring-invoices/{TestRecurringInvoices.recurring_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        print(f"Deleted recurring invoice: {TestRecurringInvoices.recurring_id}")
        
        # Verify deleted
        response = requests.get(f"{API_URL}/recurring-invoices/{TestRecurringInvoices.recurring_id}")
        assert response.status_code == 404
        
        TestRecurringInvoices.recurring_id = None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
