# Serial/Batch Tracking and PDF Templates API Tests
# Tests for P2 features: Serial/Batch Tracking module and PDF Template Customization

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ========================= FIXTURES =========================

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def test_item_id(api_client):
    """Create a test item for serial/batch tracking tests"""
    # First try to create a test item
    item_data = {
        "name": f"TEST_SerialBatch_Item_{uuid.uuid4().hex[:8]}",
        "sku": f"TEST-SB-{uuid.uuid4().hex[:6].upper()}",
        "item_type": "inventory",
        "unit": "pcs",
        "selling_price": 1000,
        "purchase_price": 800,
        "stock_on_hand": 100
    }
    
    response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0 and data.get("item"):
            return data["item"]["item_id"]
    
    # If creation fails, get an existing inventory item
    response = api_client.get(f"{BASE_URL}/api/items-enhanced/summary")
    if response.status_code == 200:
        # Get list of items
        list_response = api_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=10&item_type=inventory")
        if list_response.status_code == 200:
            data = list_response.json()
            items = data.get("items", [])
            if items:
                return items[0].get("item_id")
    
    pytest.skip("Could not create or find test item")

# ========================= SERIAL/BATCH TRACKING TESTS =========================

class TestSerialBatchSummaryReports:
    """Test summary and report endpoints"""
    
    def test_serial_summary_report(self, api_client):
        """Test serial tracking summary endpoint"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/reports/serial-summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_serials" in summary
        assert "available" in summary
        assert "sold" in summary
        assert "returned" in summary
        assert "damaged" in summary
        assert "reserved" in summary
        
        # All counts should be non-negative integers
        for key, value in summary.items():
            assert isinstance(value, int)
            assert value >= 0
    
    def test_batch_summary_report(self, api_client):
        """Test batch tracking summary endpoint"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/reports/batch-summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_batches" in summary
        assert "active_batches" in summary
        assert "depleted_batches" in summary
        assert "expiring_soon" in summary
        assert "expired_with_stock" in summary
    
    def test_expiring_batches_report(self, api_client):
        """Test expiring batches endpoint"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/batches/expiring?days=30")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "expiring_batches" in data
        assert "total" in data
        assert isinstance(data["expiring_batches"], list)
    
    def test_tracking_enabled_items(self, api_client):
        """Test list of items with tracking enabled"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/items/tracking-enabled")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)


class TestSerialNumberCRUD:
    """Test serial number CRUD operations"""
    
    def test_list_serial_numbers(self, api_client):
        """Test listing serial numbers"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/serials?per_page=50")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "serials" in data
        assert "page_context" in data
        assert isinstance(data["serials"], list)
    
    def test_list_serials_with_status_filter(self, api_client):
        """Test listing serials with status filter"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/serials?status=available")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        # All returned serials should have status=available
        for serial in data.get("serials", []):
            assert serial.get("status") == "available"
    
    def test_create_serial_number(self, api_client, test_item_id):
        """Test creating a serial number"""
        serial_data = {
            "item_id": test_item_id,
            "serial_number": f"TEST-SN-{uuid.uuid4().hex[:8].upper()}",
            "warehouse_id": "",
            "cost_price": 500,
            "warranty_expiry": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "notes": "Test serial number"
        }
        
        response = api_client.post(f"{BASE_URL}/api/serial-batch/serials", json=serial_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "serial" in data
        assert data["serial"]["serial_number"] == serial_data["serial_number"]
        assert data["serial"]["status"] == "available"
        assert "serial_id" in data["serial"]
        
        # Verify by GET
        serial_id = data["serial"]["serial_id"]
        get_response = api_client.get(f"{BASE_URL}/api/serial-batch/serials/{serial_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["code"] == 0
        assert get_data["serial"]["serial_number"] == serial_data["serial_number"]
    
    def test_create_duplicate_serial_fails(self, api_client, test_item_id):
        """Test that duplicate serial numbers are rejected"""
        serial_number = f"TEST-DUP-{uuid.uuid4().hex[:8].upper()}"
        serial_data = {
            "item_id": test_item_id,
            "serial_number": serial_number,
            "cost_price": 500
        }
        
        # Create first serial
        response1 = api_client.post(f"{BASE_URL}/api/serial-batch/serials", json=serial_data)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = api_client.post(f"{BASE_URL}/api/serial-batch/serials", json=serial_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json().get("detail", "").lower()
    
    def test_bulk_create_serials(self, api_client, test_item_id):
        """Test bulk creating serial numbers"""
        bulk_data = {
            "item_id": test_item_id,
            "prefix": f"BULK-{uuid.uuid4().hex[:4].upper()}-",
            "start_number": 1,
            "count": 5,
            "warehouse_id": "",
            "cost_price": 250
        }
        
        response = api_client.post(f"{BASE_URL}/api/serial-batch/serials/bulk", json=bulk_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "created" in data
        assert len(data["created"]) == 5
        assert "errors" in data
        
        # Verify each created serial has expected format
        for serial in data["created"]:
            assert serial["serial_number"].startswith(bulk_data["prefix"])
    
    def test_serial_lookup_by_number(self, api_client, test_item_id):
        """Test looking up serial by serial number"""
        # First create a serial
        serial_number = f"LOOKUP-{uuid.uuid4().hex[:8].upper()}"
        serial_data = {
            "item_id": test_item_id,
            "serial_number": serial_number
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/serial-batch/serials", json=serial_data)
        assert create_response.status_code == 200
        
        # Lookup by serial number
        lookup_response = api_client.get(f"{BASE_URL}/api/serial-batch/serials/lookup/{serial_number}")
        assert lookup_response.status_code == 200
        
        data = lookup_response.json()
        assert data["code"] == 0
        assert data["serial"]["serial_number"] == serial_number
    
    def test_update_serial_status(self, api_client, test_item_id):
        """Test updating serial number status"""
        # Create a serial
        serial_data = {
            "item_id": test_item_id,
            "serial_number": f"STATUS-{uuid.uuid4().hex[:8].upper()}"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/serial-batch/serials", json=serial_data)
        assert create_response.status_code == 200
        serial_id = create_response.json()["serial"]["serial_id"]
        
        # Update status to damaged
        update_response = api_client.put(
            f"{BASE_URL}/api/serial-batch/serials/{serial_id}/status?status=damaged&reason=Testing"
        )
        assert update_response.status_code == 200
        
        # Verify status changed
        get_response = api_client.get(f"{BASE_URL}/api/serial-batch/serials/{serial_id}")
        assert get_response.status_code == 200
        assert get_response.json()["serial"]["status"] == "damaged"


class TestBatchNumberCRUD:
    """Test batch number CRUD operations"""
    
    def test_list_batch_numbers(self, api_client):
        """Test listing batch numbers"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/batches?per_page=50")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "batches" in data
        assert "page_context" in data
        assert isinstance(data["batches"], list)
    
    def test_create_batch_number(self, api_client, test_item_id):
        """Test creating a batch number"""
        batch_data = {
            "item_id": test_item_id,
            "batch_number": f"LOT-{uuid.uuid4().hex[:8].upper()}",
            "warehouse_id": "",
            "quantity": 100,
            "available_quantity": 100,
            "manufacturing_date": datetime.now().strftime("%Y-%m-%d"),
            "expiry_date": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            "cost_price": 50,
            "notes": "Test batch"
        }
        
        response = api_client.post(f"{BASE_URL}/api/serial-batch/batches", json=batch_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "batch" in data
        assert data["batch"]["batch_number"] == batch_data["batch_number"]
        assert data["batch"]["quantity"] == 100
        assert data["batch"]["status"] == "active"
        assert "batch_id" in data["batch"]
        
        # Verify by GET
        batch_id = data["batch"]["batch_id"]
        get_response = api_client.get(f"{BASE_URL}/api/serial-batch/batches/{batch_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["code"] == 0
        assert get_data["batch"]["batch_number"] == batch_data["batch_number"]
    
    def test_create_duplicate_batch_fails(self, api_client, test_item_id):
        """Test that duplicate batch numbers are rejected"""
        batch_number = f"DUP-LOT-{uuid.uuid4().hex[:8].upper()}"
        batch_data = {
            "item_id": test_item_id,
            "batch_number": batch_number,
            "quantity": 50
        }
        
        # Create first batch
        response1 = api_client.post(f"{BASE_URL}/api/serial-batch/batches", json=batch_data)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = api_client.post(f"{BASE_URL}/api/serial-batch/batches", json=batch_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json().get("detail", "").lower()
    
    def test_adjust_batch_quantity(self, api_client, test_item_id):
        """Test adjusting batch quantity"""
        # Create a batch
        batch_data = {
            "item_id": test_item_id,
            "batch_number": f"ADJ-{uuid.uuid4().hex[:8].upper()}",
            "quantity": 100,
            "available_quantity": 100
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/serial-batch/batches", json=batch_data)
        assert create_response.status_code == 200
        batch_id = create_response.json()["batch"]["batch_id"]
        
        # Deduct quantity
        adjust_response = api_client.put(
            f"{BASE_URL}/api/serial-batch/batches/{batch_id}/quantity?quantity_change=-30&reason=Testing"
        )
        assert adjust_response.status_code == 200
        assert adjust_response.json()["new_quantity"] == 70
        
        # Verify quantity changed
        get_response = api_client.get(f"{BASE_URL}/api/serial-batch/batches/{batch_id}")
        assert get_response.status_code == 200
        assert get_response.json()["batch"]["available_quantity"] == 70
    
    def test_batch_depleted_status(self, api_client, test_item_id):
        """Test that batch status changes to depleted when quantity reaches 0"""
        # Create a batch with small quantity
        batch_data = {
            "item_id": test_item_id,
            "batch_number": f"DEPLETE-{uuid.uuid4().hex[:8].upper()}",
            "quantity": 10,
            "available_quantity": 10
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/serial-batch/batches", json=batch_data)
        assert create_response.status_code == 200
        batch_id = create_response.json()["batch"]["batch_id"]
        
        # Deduct all quantity
        adjust_response = api_client.put(
            f"{BASE_URL}/api/serial-batch/batches/{batch_id}/quantity?quantity_change=-10"
        )
        assert adjust_response.status_code == 200
        assert adjust_response.json()["new_quantity"] == 0
        
        # Verify status is depleted
        get_response = api_client.get(f"{BASE_URL}/api/serial-batch/batches/{batch_id}")
        assert get_response.status_code == 200
        assert get_response.json()["batch"]["status"] == "depleted"


class TestItemTrackingConfig:
    """Test item tracking configuration"""
    
    def test_configure_item_tracking(self, api_client, test_item_id):
        """Test configuring tracking for an item"""
        config_data = {
            "item_id": test_item_id,
            "enable_serial": True,
            "enable_batch": True,
            "serial_prefix": "SN-",
            "batch_prefix": "LOT-",
            "require_on_sale": True,
            "require_on_purchase": True,
            "auto_generate_serial": False
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/serial-batch/items/{test_item_id}/configure",
            json=config_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "config" in data
        assert data["config"]["enable_serial_tracking"] == True
        assert data["config"]["enable_batch_tracking"] == True
    
    def test_get_item_tracking_config(self, api_client, test_item_id):
        """Test getting tracking configuration for an item"""
        response = api_client.get(f"{BASE_URL}/api/serial-batch/items/{test_item_id}/config")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "config" in data
        assert "stats" in data
        assert "total_serials" in data["stats"]
        assert "total_batches" in data["stats"]


# ========================= PDF TEMPLATES TESTS =========================

class TestPDFTemplatesList:
    """Test PDF templates listing and retrieval"""
    
    def test_list_all_templates(self, api_client):
        """Test listing all PDF templates"""
        response = api_client.get(f"{BASE_URL}/api/pdf-templates/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "templates" in data
        assert "total" in data
        assert len(data["templates"]) >= 4  # At least 4 default templates
        
        # Verify default templates exist
        template_names = [t["name"] for t in data["templates"]]
        assert "Modern Green" in template_names
        assert "Classic Blue" in template_names
        assert "Minimal Gray" in template_names
        assert "Professional Dark" in template_names
    
    def test_list_templates_by_type(self, api_client):
        """Test filtering templates by type"""
        response = api_client.get(f"{BASE_URL}/api/pdf-templates/?template_type=invoice")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        # All returned templates should be invoice type
        for template in data["templates"]:
            assert template.get("template_type") == "invoice"
    
    def test_list_available_styles(self, api_client):
        """Test listing available template styles"""
        response = api_client.get(f"{BASE_URL}/api/pdf-templates/styles")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "styles" in data
        
        style_ids = [s["id"] for s in data["styles"]]
        assert "modern" in style_ids
        assert "classic" in style_ids
        assert "minimal" in style_ids
        assert "professional" in style_ids
    
    def test_get_template_by_id(self, api_client):
        """Test getting a specific template by ID"""
        response = api_client.get(f"{BASE_URL}/api/pdf-templates/TPL-DEFAULT-MODERN")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "template" in data
        assert data["template"]["template_id"] == "TPL-DEFAULT-MODERN"
        assert data["template"]["name"] == "Modern Green"
        assert data["template"]["is_system"] == True
    
    def test_get_nonexistent_template_returns_404(self, api_client):
        """Test that getting a non-existent template returns 404"""
        response = api_client.get(f"{BASE_URL}/api/pdf-templates/TPL-NONEXISTENT")
        assert response.status_code == 404
    
    def test_get_default_template_for_type(self, api_client):
        """Test getting the default template for a document type"""
        response = api_client.get(f"{BASE_URL}/api/pdf-templates/default/invoice")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "template" in data
        assert data["template"]["template_type"] == "invoice"


class TestPDFTemplatesCRUD:
    """Test PDF templates CRUD operations"""
    
    def test_create_custom_template(self, api_client):
        """Test creating a custom template"""
        template_data = {
            "name": f"TEST_Custom_Template_{uuid.uuid4().hex[:8]}",
            "template_type": "invoice",
            "style": "modern",
            "colors": {
                "primary": "#FF5733",
                "secondary": "#333333",
                "accent": "#FF5733",
                "text": "#000000",
                "muted": "#666666",
                "border": "#e5e7eb",
                "background": "#ffffff"
            },
            "is_default": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/pdf-templates/", json=template_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "template" in data
        assert data["template"]["name"] == template_data["name"]
        assert data["template"]["is_system"] == False
        assert "template_id" in data["template"]
        
        # Verify by GET
        template_id = data["template"]["template_id"]
        get_response = api_client.get(f"{BASE_URL}/api/pdf-templates/{template_id}")
        assert get_response.status_code == 200
        assert get_response.json()["template"]["name"] == template_data["name"]
    
    def test_duplicate_template(self, api_client):
        """Test duplicating a template"""
        # Duplicate the Modern Green template
        response = api_client.post(
            f"{BASE_URL}/api/pdf-templates/TPL-DEFAULT-MODERN/duplicate?new_name=TEST_Duplicated_Template"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "template" in data
        assert data["template"]["name"] == "TEST_Duplicated_Template"
        assert data["template"]["is_system"] == False
        assert data["template"]["template_id"] != "TPL-DEFAULT-MODERN"
    
    def test_update_custom_template(self, api_client):
        """Test updating a custom template"""
        # First create a template
        create_data = {
            "name": f"TEST_Update_Template_{uuid.uuid4().hex[:8]}",
            "template_type": "invoice",
            "style": "modern"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/pdf-templates/", json=create_data)
        assert create_response.status_code == 200
        template_id = create_response.json()["template"]["template_id"]
        
        # Update the template
        update_data = {
            "name": "TEST_Updated_Name",
            "style": "classic"
        }
        
        update_response = api_client.put(
            f"{BASE_URL}/api/pdf-templates/{template_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = api_client.get(f"{BASE_URL}/api/pdf-templates/{template_id}")
        assert get_response.status_code == 200
        assert get_response.json()["template"]["name"] == "TEST_Updated_Name"
        assert get_response.json()["template"]["style"] == "classic"
    
    def test_cannot_update_system_template(self, api_client):
        """Test that system templates cannot be modified"""
        update_data = {"name": "Modified Name"}
        
        response = api_client.put(
            f"{BASE_URL}/api/pdf-templates/TPL-DEFAULT-MODERN",
            json=update_data
        )
        assert response.status_code == 400
        assert "system templates" in response.json().get("detail", "").lower()
    
    def test_delete_custom_template(self, api_client):
        """Test deleting a custom template"""
        # First create a template
        create_data = {
            "name": f"TEST_Delete_Template_{uuid.uuid4().hex[:8]}",
            "template_type": "invoice",
            "style": "minimal"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/pdf-templates/", json=create_data)
        assert create_response.status_code == 200
        template_id = create_response.json()["template"]["template_id"]
        
        # Delete the template
        delete_response = api_client.delete(f"{BASE_URL}/api/pdf-templates/{template_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = api_client.get(f"{BASE_URL}/api/pdf-templates/{template_id}")
        assert get_response.status_code == 404
    
    def test_cannot_delete_system_template(self, api_client):
        """Test that system templates cannot be deleted"""
        response = api_client.delete(f"{BASE_URL}/api/pdf-templates/TPL-DEFAULT-MODERN")
        assert response.status_code == 400
        assert "system templates" in response.json().get("detail", "").lower()
    
    def test_set_default_template(self, api_client):
        """Test setting a template as default"""
        # Create a custom template
        create_data = {
            "name": f"TEST_Default_Template_{uuid.uuid4().hex[:8]}",
            "template_type": "invoice",
            "style": "modern"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/pdf-templates/", json=create_data)
        assert create_response.status_code == 200
        template_id = create_response.json()["template"]["template_id"]
        
        # Set as default
        set_default_response = api_client.post(
            f"{BASE_URL}/api/pdf-templates/{template_id}/set-default"
        )
        assert set_default_response.status_code == 200
        
        # Verify it's now default
        get_response = api_client.get(f"{BASE_URL}/api/pdf-templates/{template_id}")
        assert get_response.status_code == 200
        assert get_response.json()["template"]["is_default"] == True


class TestPDFTemplatePreview:
    """Test PDF template preview functionality"""
    
    def test_preview_template(self, api_client):
        """Test generating a template preview"""
        response = api_client.post(
            f"{BASE_URL}/api/pdf-templates/preview?template_id=TPL-DEFAULT-MODERN"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "preview_html" in data
        assert data["template_id"] == "TPL-DEFAULT-MODERN"
        assert len(data["preview_html"]) > 0
        # Verify HTML contains expected elements
        assert "INVOICE" in data["preview_html"]
    
    def test_preview_with_custom_data(self, api_client):
        """Test preview with custom sample data"""
        sample_data = {
            "invoice_number": "TEST-INV-001",
            "date": "2026-02-19",
            "due_date": "2026-03-05",
            "customer_name": "Test Customer",
            "customer_address": "123 Test Street",
            "line_items": [
                {"name": "Test Product", "quantity": 5, "rate": 100, "item_total": 500}
            ],
            "sub_total": 500,
            "tax_total": 90,
            "total": 590,
            "balance": 590
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/pdf-templates/preview?template_id=TPL-DEFAULT-CLASSIC",
            json=sample_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "preview_html" in data
        # Verify custom data appears in preview
        assert "Test Customer" in data["preview_html"]
        assert "TEST-INV-001" in data["preview_html"]


# ========================= CLEANUP =========================

@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(api_client):
    """Cleanup test data after all tests complete"""
    yield
    # Note: In a production environment, we would clean up TEST_ prefixed data
    # For now, we leave test data for verification purposes
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
