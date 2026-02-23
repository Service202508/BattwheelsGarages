"""
Test Suite for Bills Enhanced and Inventory Enhanced Modules
Tests: Bills CRUD, Bill Payments, Purchase Orders, PO Status Transitions
       Warehouses, Variants, Bundles, Serial/Batch, Stock Adjustments, Reports
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://production-hardening-1.preview.emergentagent.com')

# Test data tracking
created_ids = {
    "bills": [],
    "purchase_orders": [],
    "warehouses": [],
    "variants": [],
    "bundles": [],
    "serial_batches": [],
    "adjustments": [],
    "contacts": [],
    "items": []
}

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ==================== BILLS ENHANCED MODULE ====================

class TestBillsEnhancedSummary:
    """Bills summary endpoint tests"""
    
    def test_get_bills_summary(self, api_client):
        """Test bills summary endpoint"""
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        assert "total_bills" in summary
        assert "draft" in summary
        assert "open" in summary
        assert "overdue" in summary
        assert "total_payable" in summary
        assert "total_paid" in summary
        print(f"✓ Bills summary: {summary['total_bills']} total, {summary['draft']} draft, {summary['open']} open")


class TestBillsEnhancedCRUD:
    """Bills CRUD operations tests"""
    
    @pytest.fixture(autouse=True)
    def setup_vendor(self, api_client):
        """Create a test vendor for bill creation"""
        # First check if we have existing vendors
        response = api_client.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=vendor&per_page=10")
        if response.status_code == 200:
            data = response.json()
            if data.get("contacts") and len(data["contacts"]) > 0:
                self.vendor_id = data["contacts"][0]["contact_id"]
                self.vendor_name = data["contacts"][0]["name"]
                print(f"Using existing vendor: {self.vendor_name}")
                return
        
        # Create a test vendor
        vendor_data = {
            "name": f"TEST_Vendor_{uuid.uuid4().hex[:6]}",
            "contact_type": "vendor",
            "email": f"test_vendor_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "9876543210",
            "gstin": "29AABCU9603R1ZM",
            "gst_treatment": "registered",
            "payment_terms": 30
        }
        response = api_client.post(f"{BASE_URL}/api/contacts-enhanced/", json=vendor_data)
        if response.status_code in [200, 201]:
            data = response.json()
            self.vendor_id = data["contact"]["contact_id"]
            self.vendor_name = data["contact"]["name"]
            created_ids["contacts"].append(self.vendor_id)
            print(f"Created test vendor: {self.vendor_name}")
        else:
            pytest.skip("Could not create or find vendor for bill testing")
    
    def test_create_bill(self, api_client):
        """Test creating a new bill"""
        bill_data = {
            "vendor_id": self.vendor_id,
            "reference_number": f"TEST_REF_{uuid.uuid4().hex[:6]}",
            "bill_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_terms": 30,
            "line_items": [
                {
                    "name": "Test Item 1",
                    "description": "Test description",
                    "quantity": 2,
                    "unit": "pcs",
                    "rate": 500,
                    "tax_rate": 18
                },
                {
                    "name": "Test Item 2",
                    "quantity": 1,
                    "rate": 1000,
                    "tax_rate": 18
                }
            ],
            "discount_type": "percentage",
            "discount_value": 0,
            "vendor_notes": "Test bill created by automated tests"
        }
        
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/", json=bill_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bill" in data
        bill = data["bill"]
        assert "bill_id" in bill
        assert "bill_number" in bill
        assert bill["status"] == "draft"
        assert bill["vendor_id"] == self.vendor_id
        assert len(bill.get("line_items", [])) == 2
        
        # Verify totals are calculated
        assert bill["grand_total"] > 0
        assert bill["balance_due"] == bill["grand_total"]
        
        created_ids["bills"].append(bill["bill_id"])
        print(f"✓ Created bill: {bill['bill_number']} with total ₹{bill['grand_total']}")
    
    def test_list_bills(self, api_client):
        """Test listing bills"""
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bills" in data
        assert "page_context" in data
        print(f"✓ Listed {len(data['bills'])} bills")
    
    def test_get_bill_detail(self, api_client):
        """Test getting bill details"""
        if not created_ids["bills"]:
            pytest.skip("No bills created to test")
        
        bill_id = created_ids["bills"][0]
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/{bill_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bill" in data
        bill = data["bill"]
        assert "line_items" in bill
        assert "payments" in bill
        assert "history" in bill
        print(f"✓ Got bill detail: {bill['bill_number']}")
    
    def test_open_bill(self, api_client):
        """Test opening a draft bill"""
        if not created_ids["bills"]:
            pytest.skip("No bills created to test")
        
        bill_id = created_ids["bills"][0]
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/{bill_id}/open")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status changed
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/{bill_id}")
        bill = response.json()["bill"]
        assert bill["status"] == "open"
        print(f"✓ Opened bill: {bill['bill_number']}")


class TestBillPayments:
    """Bill payment operations tests"""
    
    def test_record_payment(self, api_client):
        """Test recording a payment on a bill"""
        if not created_ids["bills"]:
            pytest.skip("No bills created to test")
        
        bill_id = created_ids["bills"][0]
        
        # Get bill to check balance
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/{bill_id}")
        bill = response.json()["bill"]
        
        if bill["status"] == "draft":
            # Open the bill first
            api_client.post(f"{BASE_URL}/api/bills-enhanced/{bill_id}/open")
            response = api_client.get(f"{BASE_URL}/api/bills-enhanced/{bill_id}")
            bill = response.json()["bill"]
        
        if bill["balance_due"] <= 0:
            pytest.skip("Bill already paid")
        
        # Record partial payment
        payment_amount = min(500, bill["balance_due"])
        payment_data = {
            "amount": payment_amount,
            "payment_mode": "bank_transfer",
            "reference_number": f"TEST_PAY_{uuid.uuid4().hex[:6]}",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Test payment"
        }
        
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/{bill_id}/payments", json=payment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "payment" in data
        assert data["payment"]["amount"] == payment_amount
        print(f"✓ Recorded payment of ₹{payment_amount}")
    
    def test_get_bill_payments(self, api_client):
        """Test getting payments for a bill"""
        if not created_ids["bills"]:
            pytest.skip("No bills created to test")
        
        bill_id = created_ids["bills"][0]
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/{bill_id}/payments")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "payments" in data
        print(f"✓ Got {len(data['payments'])} payments for bill")


class TestBillActions:
    """Bill action operations tests"""
    
    def test_clone_bill(self, api_client):
        """Test cloning a bill"""
        if not created_ids["bills"]:
            pytest.skip("No bills created to test")
        
        bill_id = created_ids["bills"][0]
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/{bill_id}/clone")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bill" in data
        cloned_bill = data["bill"]
        assert cloned_bill["status"] == "draft"
        assert cloned_bill["bill_id"] != bill_id
        created_ids["bills"].append(cloned_bill["bill_id"])
        print(f"✓ Cloned bill to: {cloned_bill['bill_number']}")


# ==================== PURCHASE ORDERS MODULE ====================

class TestPurchaseOrdersSummary:
    """Purchase Orders summary tests"""
    
    def test_get_po_summary(self, api_client):
        """Test PO summary endpoint"""
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/purchase-orders/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        assert "total_orders" in summary
        assert "draft" in summary
        assert "issued" in summary
        assert "received" in summary
        assert "billed" in summary
        print(f"✓ PO summary: {summary['total_orders']} total, {summary['draft']} draft")


class TestPurchaseOrdersCRUD:
    """Purchase Orders CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup_vendor(self, api_client):
        """Get or create vendor for PO"""
        response = api_client.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=vendor&per_page=10")
        if response.status_code == 200:
            data = response.json()
            if data.get("contacts") and len(data["contacts"]) > 0:
                self.vendor_id = data["contacts"][0]["contact_id"]
                return
        pytest.skip("No vendor available for PO testing")
    
    def test_create_purchase_order(self, api_client):
        """Test creating a purchase order"""
        po_data = {
            "vendor_id": self.vendor_id,
            "reference_number": f"TEST_PO_REF_{uuid.uuid4().hex[:6]}",
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "expected_delivery_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "delivery_address": "Test Delivery Address, Delhi",
            "line_items": [
                {
                    "name": "PO Test Item",
                    "quantity": 5,
                    "rate": 200,
                    "tax_rate": 18
                }
            ],
            "vendor_notes": "Test PO created by automated tests"
        }
        
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/purchase-orders", json=po_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "purchase_order" in data
        po = data["purchase_order"]
        assert "po_id" in po
        assert "po_number" in po
        assert po["status"] == "draft"
        created_ids["purchase_orders"].append(po["po_id"])
        print(f"✓ Created PO: {po['po_number']} with total ₹{po['grand_total']}")
    
    def test_list_purchase_orders(self, api_client):
        """Test listing purchase orders"""
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/purchase-orders")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "purchase_orders" in data
        print(f"✓ Listed {len(data['purchase_orders'])} purchase orders")
    
    def test_get_purchase_order_detail(self, api_client):
        """Test getting PO details"""
        if not created_ids["purchase_orders"]:
            pytest.skip("No POs created to test")
        
        po_id = created_ids["purchase_orders"][0]
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/purchase-orders/{po_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "purchase_order" in data
        po = data["purchase_order"]
        assert "line_items" in po
        print(f"✓ Got PO detail: {po['po_number']}")


class TestPurchaseOrderStatusTransitions:
    """PO status transition tests: draft -> issued -> received -> billed"""
    
    def test_issue_purchase_order(self, api_client):
        """Test issuing a draft PO"""
        if not created_ids["purchase_orders"]:
            pytest.skip("No POs created to test")
        
        po_id = created_ids["purchase_orders"][0]
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/purchase-orders/{po_id}/issue")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/purchase-orders/{po_id}")
        po = response.json()["purchase_order"]
        assert po["status"] == "issued"
        print(f"✓ Issued PO: {po['po_number']}")
    
    def test_receive_purchase_order(self, api_client):
        """Test marking PO as received"""
        if not created_ids["purchase_orders"]:
            pytest.skip("No POs created to test")
        
        po_id = created_ids["purchase_orders"][0]
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/purchase-orders/{po_id}/receive")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/purchase-orders/{po_id}")
        po = response.json()["purchase_order"]
        assert po["status"] == "received"
        print(f"✓ Received PO: {po['po_number']}")
    
    def test_convert_po_to_bill(self, api_client):
        """Test converting PO to bill"""
        if not created_ids["purchase_orders"]:
            pytest.skip("No POs created to test")
        
        po_id = created_ids["purchase_orders"][0]
        response = api_client.post(f"{BASE_URL}/api/bills-enhanced/purchase-orders/{po_id}/convert-to-bill")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bill" in data
        bill = data["bill"]
        created_ids["bills"].append(bill["bill_id"])
        
        # Verify PO status changed to billed
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/purchase-orders/{po_id}")
        po = response.json()["purchase_order"]
        assert po["status"] == "billed"
        print(f"✓ Converted PO to bill: {bill['bill_number']}")


class TestBillsReports:
    """Bills reports tests"""
    
    def test_aging_report(self, api_client):
        """Test payables aging report"""
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/reports/aging")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        report = data["report"]
        assert "current" in report
        assert "1_30" in report
        assert "31_60" in report
        print(f"✓ Aging report: Total ₹{data.get('total', 0)}")
    
    def test_vendor_wise_report(self, api_client):
        """Test vendor-wise report"""
        response = api_client.get(f"{BASE_URL}/api/bills-enhanced/reports/vendor-wise")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        print(f"✓ Vendor-wise report: {len(data['report'])} vendors")


# ==================== INVENTORY ENHANCED MODULE ====================

class TestInventorySummary:
    """Inventory summary tests"""
    
    def test_get_inventory_summary(self, api_client):
        """Test inventory summary endpoint"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        assert "total_items" in summary
        assert "total_variants" in summary
        assert "total_bundles" in summary
        assert "total_warehouses" in summary
        assert "total_stock_value" in summary
        assert "low_stock_count" in summary
        print(f"✓ Inventory summary: {summary['total_items']} items, {summary['total_warehouses']} warehouses")


class TestWarehouseManagement:
    """Warehouse CRUD tests"""
    
    def test_list_warehouses(self, api_client):
        """Test listing warehouses"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/warehouses")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "warehouses" in data
        print(f"✓ Listed {len(data['warehouses'])} warehouses")
    
    def test_create_warehouse(self, api_client):
        """Test creating a warehouse"""
        warehouse_data = {
            "name": f"TEST_Warehouse_{uuid.uuid4().hex[:6]}",
            "code": f"WH-{uuid.uuid4().hex[:4].upper()}",
            "address": "Test Address",
            "city": "Delhi",
            "state": "DL",
            "pincode": "110001",
            "is_primary": False,
            "is_active": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-enhanced/warehouses", json=warehouse_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "warehouse" in data
        warehouse = data["warehouse"]
        assert "warehouse_id" in warehouse
        created_ids["warehouses"].append(warehouse["warehouse_id"])
        print(f"✓ Created warehouse: {warehouse['name']}")
    
    def test_get_warehouse_detail(self, api_client):
        """Test getting warehouse details"""
        if not created_ids["warehouses"]:
            # Use existing warehouse
            response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/warehouses")
            warehouses = response.json().get("warehouses", [])
            if not warehouses:
                pytest.skip("No warehouses available")
            warehouse_id = warehouses[0]["warehouse_id"]
        else:
            warehouse_id = created_ids["warehouses"][0]
        
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/warehouses/{warehouse_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "warehouse" in data
        warehouse = data["warehouse"]
        assert "stock_items" in warehouse
        assert "item_count" in warehouse
        print(f"✓ Got warehouse detail: {warehouse['name']} with {warehouse['item_count']} items")


class TestItemVariants:
    """Item variants CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup_item(self, api_client):
        """Get or create an item for variant testing"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=10")
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                self.item_id = data["items"][0]["item_id"]
                self.item_name = data["items"][0]["name"]
                return
        
        # Create a test item
        item_data = {
            "name": f"TEST_Item_{uuid.uuid4().hex[:6]}",
            "sku": f"SKU-{uuid.uuid4().hex[:6].upper()}",
            "item_type": "goods",
            "sales_rate": 1000,
            "purchase_rate": 800,
            "track_inventory": True,
            "reorder_level": 10
        }
        response = api_client.post(f"{BASE_URL}/api/items-enhanced/", json=item_data)
        if response.status_code in [200, 201]:
            data = response.json()
            self.item_id = data["item"]["item_id"]
            self.item_name = data["item"]["name"]
            created_ids["items"].append(self.item_id)
        else:
            pytest.skip("Could not create or find item for variant testing")
    
    def test_create_variant(self, api_client):
        """Test creating an item variant"""
        # Get a warehouse
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/warehouses")
        warehouses = response.json().get("warehouses", [])
        warehouse_id = warehouses[0]["warehouse_id"] if warehouses else ""
        
        variant_data = {
            "item_id": self.item_id,
            "variant_name": f"Large - Red",
            "sku": f"VAR-{uuid.uuid4().hex[:6].upper()}",
            "additional_rate": 100,
            "attributes": {"size": "Large", "color": "Red"},
            "initial_stock": 10,
            "warehouse_id": warehouse_id
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-enhanced/variants", json=variant_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "variant" in data
        variant = data["variant"]
        assert "variant_id" in variant
        assert variant["variant_name"] == "Large - Red"
        created_ids["variants"].append(variant["variant_id"])
        print(f"✓ Created variant: {variant['variant_name']} for {self.item_name}")
    
    def test_list_variants(self, api_client):
        """Test listing variants"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/variants")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "variants" in data
        print(f"✓ Listed {len(data['variants'])} variants")
    
    def test_get_variant_detail(self, api_client):
        """Test getting variant details"""
        if not created_ids["variants"]:
            pytest.skip("No variants created to test")
        
        variant_id = created_ids["variants"][0]
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/variants/{variant_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "variant" in data
        variant = data["variant"]
        assert "stock_locations" in variant
        assert "total_stock" in variant
        print(f"✓ Got variant detail: {variant['variant_name']} with stock {variant['total_stock']}")


class TestBundlesKits:
    """Bundle/Kit CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup_items(self, api_client):
        """Get items for bundle components"""
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=10")
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) >= 2:
                self.items = data["items"][:2]
                return
        pytest.skip("Need at least 2 items for bundle testing")
    
    def test_create_bundle(self, api_client):
        """Test creating a bundle"""
        bundle_data = {
            "name": f"TEST_Bundle_{uuid.uuid4().hex[:6]}",
            "sku": f"BDL-{uuid.uuid4().hex[:6].upper()}",
            "description": "Test bundle with multiple components",
            "rate": 0,
            "components": [
                {"item_id": self.items[0]["item_id"], "quantity": 2},
                {"item_id": self.items[1]["item_id"], "quantity": 1}
            ],
            "auto_calculate_rate": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-enhanced/bundles", json=bundle_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bundle" in data
        bundle = data["bundle"]
        assert "bundle_id" in bundle
        assert bundle["component_count"] == 2
        created_ids["bundles"].append(bundle["bundle_id"])
        print(f"✓ Created bundle: {bundle['name']} with {bundle['component_count']} components")
    
    def test_list_bundles(self, api_client):
        """Test listing bundles"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/bundles")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bundles" in data
        print(f"✓ Listed {len(data['bundles'])} bundles")
    
    def test_get_bundle_detail(self, api_client):
        """Test getting bundle details with components"""
        if not created_ids["bundles"]:
            pytest.skip("No bundles created to test")
        
        bundle_id = created_ids["bundles"][0]
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/bundles/{bundle_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bundle" in data
        bundle = data["bundle"]
        assert "components" in bundle
        assert "max_assemblable" in bundle
        print(f"✓ Got bundle detail: {bundle['name']} - max assemblable: {bundle['max_assemblable']}")


class TestSerialBatchTracking:
    """Serial/Batch tracking tests"""
    
    @pytest.fixture(autouse=True)
    def setup_item_and_warehouse(self, api_client):
        """Get item and warehouse for serial/batch testing"""
        # Get item
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=10")
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                self.item_id = data["items"][0]["item_id"]
        
        # Get warehouse
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/warehouses")
        if response.status_code == 200:
            data = response.json()
            if data.get("warehouses") and len(data["warehouses"]) > 0:
                self.warehouse_id = data["warehouses"][0]["warehouse_id"]
        
        if not hasattr(self, 'item_id') or not hasattr(self, 'warehouse_id'):
            pytest.skip("Need item and warehouse for serial/batch testing")
    
    def test_create_serial_number(self, api_client):
        """Test creating a serial number"""
        serial_data = {
            "item_id": self.item_id,
            "tracking_type": "serial",
            "number": f"SN-{uuid.uuid4().hex[:8].upper()}",
            "warehouse_id": self.warehouse_id,
            "notes": "Test serial number"
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-enhanced/serial-batches", json=serial_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "serial_batch" in data
        serial = data["serial_batch"]
        assert serial["tracking_type"] == "serial"
        assert serial["quantity"] == 1
        created_ids["serial_batches"].append(serial["serial_batch_id"])
        print(f"✓ Created serial number: {serial['number']}")
    
    def test_create_batch(self, api_client):
        """Test creating a batch"""
        batch_data = {
            "item_id": self.item_id,
            "tracking_type": "batch",
            "number": f"BATCH-{uuid.uuid4().hex[:6].upper()}",
            "warehouse_id": self.warehouse_id,
            "quantity": 50,
            "expiry_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "notes": "Test batch"
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-enhanced/serial-batches", json=batch_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "serial_batch" in data
        batch = data["serial_batch"]
        assert batch["tracking_type"] == "batch"
        assert batch["quantity"] == 50
        created_ids["serial_batches"].append(batch["serial_batch_id"])
        print(f"✓ Created batch: {batch['number']} with qty {batch['quantity']}")
    
    def test_list_serial_batches(self, api_client):
        """Test listing serial numbers and batches"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/serial-batches?status=all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "serial_batches" in data
        print(f"✓ Listed {len(data['serial_batches'])} serial/batches")


class TestStockAdjustments:
    """Stock adjustment tests"""
    
    @pytest.fixture(autouse=True)
    def setup_item_and_warehouse(self, api_client):
        """Get item and warehouse for adjustment testing"""
        # Get item
        response = api_client.get(f"{BASE_URL}/api/items-enhanced/?per_page=10")
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                self.item_id = data["items"][0]["item_id"]
                self.item_name = data["items"][0]["name"]
        
        # Get warehouse
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/warehouses")
        if response.status_code == 200:
            data = response.json()
            if data.get("warehouses") and len(data["warehouses"]) > 0:
                self.warehouse_id = data["warehouses"][0]["warehouse_id"]
        
        if not hasattr(self, 'item_id') or not hasattr(self, 'warehouse_id'):
            pytest.skip("Need item and warehouse for adjustment testing")
    
    def test_add_stock_adjustment(self, api_client):
        """Test adding stock via adjustment"""
        adjustment_data = {
            "item_id": self.item_id,
            "warehouse_id": self.warehouse_id,
            "adjustment_type": "add",
            "quantity": 100,
            "reason": "Initial stock from automated test",
            "reference_number": f"ADJ-{uuid.uuid4().hex[:6].upper()}",
            "notes": "Test adjustment"
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-enhanced/adjustments", json=adjustment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustment" in data
        adj = data["adjustment"]
        assert adj["quantity_adjusted"] == 100
        assert adj["stock_after"] >= 100
        created_ids["adjustments"].append(adj["adjustment_id"])
        print(f"✓ Added stock adjustment: +{adj['quantity_adjusted']} for {self.item_name}")
    
    def test_subtract_stock_adjustment(self, api_client):
        """Test subtracting stock via adjustment"""
        adjustment_data = {
            "item_id": self.item_id,
            "warehouse_id": self.warehouse_id,
            "adjustment_type": "subtract",
            "quantity": 10,
            "reason": "Damaged goods - automated test",
            "reference_number": f"ADJ-{uuid.uuid4().hex[:6].upper()}"
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-enhanced/adjustments", json=adjustment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustment" in data
        adj = data["adjustment"]
        assert adj["quantity_adjusted"] == -10
        print(f"✓ Subtracted stock adjustment: {adj['quantity_adjusted']} for {self.item_name}")
    
    def test_list_adjustments(self, api_client):
        """Test listing adjustments"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/adjustments")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "adjustments" in data
        print(f"✓ Listed {len(data['adjustments'])} adjustments")


class TestInventoryReports:
    """Inventory reports tests"""
    
    def test_stock_summary_report(self, api_client):
        """Test stock summary report"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/reports/stock-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        report = data["report"]
        assert "items" in report
        assert "summary" in report
        print(f"✓ Stock summary: {report['summary']['total_items']} items, ₹{report['summary']['total_value']} value")
    
    def test_low_stock_report(self, api_client):
        """Test low stock report"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/reports/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        report = data["report"]
        assert "low_stock_items" in report
        assert "total" in report
        print(f"✓ Low stock report: {report['total']} items below reorder level")
    
    def test_valuation_report(self, api_client):
        """Test inventory valuation report"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/reports/valuation")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        report = data["report"]
        assert "by_type" in report
        assert "totals" in report
        print(f"✓ Valuation report: ₹{report['totals']['total_purchase_value']} purchase value")
    
    def test_movement_report(self, api_client):
        """Test stock movement report"""
        response = api_client.get(f"{BASE_URL}/api/inventory-enhanced/reports/movement?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        report = data["report"]
        assert "movements" in report
        assert "by_action" in report
        print(f"✓ Movement report: {len(report['movements'])} movements in last 30 days")


# ==================== CLEANUP ====================

class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_data(self, api_client):
        """Clean up created test data"""
        cleaned = {"bills": 0, "purchase_orders": 0, "warehouses": 0, "variants": 0, "bundles": 0, "contacts": 0, "items": 0}
        
        # Note: We don't delete bills/POs as they may have payments
        # Just log what was created
        print(f"\n=== Test Data Created ===")
        print(f"Bills: {len(created_ids['bills'])}")
        print(f"Purchase Orders: {len(created_ids['purchase_orders'])}")
        print(f"Warehouses: {len(created_ids['warehouses'])}")
        print(f"Variants: {len(created_ids['variants'])}")
        print(f"Bundles: {len(created_ids['bundles'])}")
        print(f"Serial/Batches: {len(created_ids['serial_batches'])}")
        print(f"Adjustments: {len(created_ids['adjustments'])}")
        
        # Delete test variants
        for variant_id in created_ids["variants"]:
            try:
                api_client.delete(f"{BASE_URL}/api/inventory-enhanced/variants/{variant_id}")
                cleaned["variants"] += 1
            except:
                pass
        
        print(f"✓ Cleanup complete: {cleaned}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
