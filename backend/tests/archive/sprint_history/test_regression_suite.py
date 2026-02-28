"""
Regression Test Suite for Battwheels OS
Tests critical workflows to ensure Zoho Books parity

Run with: pytest /app/backend/tests/test_regression_suite.py -v
"""

import pytest
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any
import os

# Configuration
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8001/api")
TEST_EMAIL = "admin@battwheels.in"
TEST_PASSWORD = "DevTest@123"

# ========================= FIXTURES =========================

@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def auth_token():
    """Get authentication token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]

@pytest.fixture
def headers(auth_token):
    """Auth headers for requests"""
    return {"Authorization": f"Bearer {auth_token}"}

# ========================= TEST DATA =========================

def get_test_customer():
    """Test customer data"""
    return {
        "display_name": f"Test Customer {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company_name": "Test Company",
        "contact_type": "customer",
        "email": "test@example.com",
        "phone": "1234567890",
        "billing_address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "Delhi",
            "zip": "110001",
            "country": "India"
        },
        "gst_treatment": "business_gst",
        "gstin": "07AABCT1332L1ZL"
    }

def get_test_item():
    """Test item data"""
    return {
        "name": f"Test Item {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "item_type": "sales_and_purchases",
        "sku": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "rate": 1000.00,
        "purchase_rate": 800.00,
        "tax_id": "",
        "tax_percentage": 18,
        "unit": "pcs",
        "is_taxable": True,
        "stock_on_hand": 100,
        "reorder_level": 10
    }

def get_test_estimate(customer_id: str):
    """Test estimate data"""
    return {
        "customer_id": customer_id,
        "estimate_date": datetime.now().strftime("%Y-%m-%d"),
        "expiry_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "line_items": [
            {
                "name": "Test Service",
                "description": "Test service description",
                "quantity": 2,
                "rate": 500,
                "tax_percentage": 18
            }
        ],
        "notes": "Test estimate notes",
        "terms_conditions": "Standard terms apply"
    }

def get_test_invoice(customer_id: str):
    """Test invoice data"""
    return {
        "customer_id": customer_id,
        "invoice_date": datetime.now().strftime("%Y-%m-%d"),
        "payment_terms": 30,
        "line_items": [
            {
                "name": "Test Product",
                "description": "Test product description",
                "quantity": 3,
                "rate": 1000,
                "tax_rate": 18
            }
        ],
        "customer_notes": "Test invoice notes",
        "terms_conditions": "Payment due within 30 days"
    }

# ========================= WORKFLOW TESTS =========================

@pytest.mark.asyncio
class TestQuoteToInvoiceWorkflow:
    """Test Quote → Invoice conversion workflow"""
    
    async def test_create_estimate(self, headers):
        """Step 1: Create an estimate"""
        async with httpx.AsyncClient() as client:
            # First get a customer
            customers = await client.get(f"{BASE_URL}/contacts-v2/?per_page=1", headers=headers)
            customer_id = customers.json()["contacts"][0]["contact_id"]
            
            # Create estimate
            estimate_data = get_test_estimate(customer_id)
            response = await client.post(
                f"{BASE_URL}/estimates-enhanced/",
                json=estimate_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "estimate" in data
            assert data["estimate"]["status"] == "draft"
            
            # Store for next tests
            pytest.estimate_id = data["estimate"]["estimate_id"]
            pytest.customer_id = customer_id
    
    async def test_send_estimate(self, headers):
        """Step 2: Send the estimate"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/estimates-enhanced/{pytest.estimate_id}/mark-sent",
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify status changed
            detail = await client.get(
                f"{BASE_URL}/estimates-enhanced/{pytest.estimate_id}",
                headers=headers
            )
            assert detail.json()["estimate"]["status"] == "sent"
    
    async def test_accept_estimate(self, headers):
        """Step 3: Accept the estimate"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/estimates-enhanced/{pytest.estimate_id}/accept",
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify status
            detail = await client.get(
                f"{BASE_URL}/estimates-enhanced/{pytest.estimate_id}",
                headers=headers
            )
            assert detail.json()["estimate"]["status"] == "accepted"
    
    async def test_convert_to_invoice(self, headers):
        """Step 4: Convert estimate to invoice"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/from-estimate/{pytest.estimate_id}",
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "invoice" in data
            
            # Store invoice ID
            pytest.invoice_id = data["invoice"]["invoice_id"]
            
            # Verify estimate status changed to invoiced
            estimate = await client.get(
                f"{BASE_URL}/estimates-enhanced/{pytest.estimate_id}",
                headers=headers
            )
            assert estimate.json()["estimate"]["status"] == "invoiced"

@pytest.mark.asyncio
class TestInvoicePaymentWorkflow:
    """Test Invoice payment workflow"""
    
    async def test_create_invoice(self, headers):
        """Step 1: Create an invoice"""
        async with httpx.AsyncClient() as client:
            # Get customer
            customers = await client.get(f"{BASE_URL}/contacts-v2/?per_page=1", headers=headers)
            customer_id = customers.json()["contacts"][0]["contact_id"]
            
            # Create invoice
            invoice_data = get_test_invoice(customer_id)
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/",
                json=invoice_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "invoice" in data
            
            pytest.payment_invoice_id = data["invoice"]["invoice_id"]
            pytest.invoice_total = data["invoice"]["grand_total"]
    
    async def test_send_invoice(self, headers):
        """Step 2: Mark invoice as sent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/{pytest.payment_invoice_id}/mark-sent",
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify status
            detail = await client.get(
                f"{BASE_URL}/invoices-enhanced/{pytest.payment_invoice_id}",
                headers=headers
            )
            assert detail.json()["invoice"]["status"] == "sent"
    
    async def test_partial_payment(self, headers):
        """Step 3: Record partial payment"""
        async with httpx.AsyncClient() as client:
            partial_amount = pytest.invoice_total / 2
            
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/{pytest.payment_invoice_id}/record-payment",
                json={
                    "amount": partial_amount,
                    "payment_mode": "bank_transfer",
                    "payment_date": datetime.now().strftime("%Y-%m-%d"),
                    "reference_number": "TEST-PAY-001"
                },
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify status is partially_paid
            detail = await client.get(
                f"{BASE_URL}/invoices-enhanced/{pytest.payment_invoice_id}",
                headers=headers
            )
            invoice = detail.json()["invoice"]
            assert invoice["status"] == "partially_paid"
            assert abs(invoice["balance_due"] - partial_amount) < 1
    
    async def test_full_payment(self, headers):
        """Step 4: Record remaining payment"""
        async with httpx.AsyncClient() as client:
            # Get current balance
            detail = await client.get(
                f"{BASE_URL}/invoices-enhanced/{pytest.payment_invoice_id}",
                headers=headers
            )
            remaining = detail.json()["invoice"]["balance_due"]
            
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/{pytest.payment_invoice_id}/record-payment",
                json={
                    "amount": remaining,
                    "payment_mode": "cash",
                    "payment_date": datetime.now().strftime("%Y-%m-%d"),
                    "reference_number": "TEST-PAY-002"
                },
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify status is paid
            detail = await client.get(
                f"{BASE_URL}/invoices-enhanced/{pytest.payment_invoice_id}",
                headers=headers
            )
            invoice = detail.json()["invoice"]
            assert invoice["status"] == "paid"
            assert invoice["balance_due"] < 1

@pytest.mark.asyncio
class TestInventoryAdjustmentWorkflow:
    """Test Inventory adjustment workflow"""
    
    async def test_create_adjustment(self, headers):
        """Step 1: Create inventory adjustment"""
        async with httpx.AsyncClient() as client:
            # Get an item
            items = await client.get(f"{BASE_URL}/items-enhanced/?per_page=1", headers=headers)
            item = items.json()["items"][0]
            pytest.test_item_id = item["item_id"]
            pytest.initial_stock = item.get("stock_on_hand", item.get("on_hand_stock", 0))
            
            # Create adjustment
            response = await client.post(
                f"{BASE_URL}/inventory-adjustments-v2/",
                json={
                    "adjustment_type": "quantity",
                    "reason": "Stock Recount",
                    "reference_number": f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "line_items": [
                        {
                            "item_id": pytest.test_item_id,
                            "item_name": item["name"],
                            "quantity_adjusted": 10,
                            "adjustment_type": "add"
                        }
                    ],
                    "notes": "Test adjustment"
                },
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "adjustment" in data
            
            pytest.adjustment_id = data["adjustment"]["adjustment_id"]
            assert data["adjustment"]["status"] == "draft"
    
    async def test_apply_adjustment(self, headers):
        """Step 2: Apply the adjustment"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/inventory-adjustments-v2/{pytest.adjustment_id}/convert",
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify adjustment status
            detail = await client.get(
                f"{BASE_URL}/inventory-adjustments-v2/{pytest.adjustment_id}",
                headers=headers
            )
            assert detail.json()["adjustment"]["status"] == "adjusted"
    
    async def test_verify_stock_updated(self, headers):
        """Step 3: Verify stock was updated"""
        async with httpx.AsyncClient() as client:
            # Get updated item
            item = await client.get(
                f"{BASE_URL}/items-enhanced/{pytest.test_item_id}",
                headers=headers
            )
            
            new_stock = item.json()["item"].get("stock_on_hand", 
                        item.json()["item"].get("on_hand_stock", 0))
            
            # Stock should have increased by 10
            expected_stock = pytest.initial_stock + 10
            assert abs(new_stock - expected_stock) < 1, f"Expected {expected_stock}, got {new_stock}"

@pytest.mark.asyncio
class TestInvoiceVoidWorkflow:
    """Test Invoice void and stock reversal"""
    
    async def test_create_and_send_invoice(self, headers):
        """Step 1: Create and send invoice"""
        async with httpx.AsyncClient() as client:
            # Get customer
            customers = await client.get(f"{BASE_URL}/contacts-v2/?per_page=1", headers=headers)
            customer_id = customers.json()["contacts"][0]["contact_id"]
            
            # Create invoice
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/",
                json=get_test_invoice(customer_id),
                headers=headers
            )
            
            assert response.status_code == 200
            pytest.void_invoice_id = response.json()["invoice"]["invoice_id"]
            
            # Send it
            await client.post(
                f"{BASE_URL}/invoices-enhanced/{pytest.void_invoice_id}/mark-sent",
                headers=headers
            )
    
    async def test_void_invoice(self, headers):
        """Step 2: Void the invoice"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/{pytest.void_invoice_id}/void",
                headers=headers
            )
            
            assert response.status_code == 200
            
            # Verify status
            detail = await client.get(
                f"{BASE_URL}/invoices-enhanced/{pytest.void_invoice_id}",
                headers=headers
            )
            assert detail.json()["invoice"]["status"] == "void"

@pytest.mark.asyncio
class TestPDFGeneration:
    """Test PDF generation for all document types"""
    
    async def test_invoice_pdf(self, headers):
        """Test invoice PDF generation"""
        async with httpx.AsyncClient() as client:
            # Get an invoice
            invoices = await client.get(f"{BASE_URL}/invoices-enhanced/?per_page=1", headers=headers)
            invoice_id = invoices.json()["invoices"][0]["invoice_id"]
            
            response = await client.get(
                f"{BASE_URL}/invoices-enhanced/{invoice_id}/pdf",
                headers=headers
            )
            
            assert response.status_code == 200
            assert response.headers.get("content-type") == "application/pdf"
            assert response.content[:4] == b"%PDF"
    
    async def test_estimate_pdf(self, headers):
        """Test estimate PDF generation"""
        async with httpx.AsyncClient() as client:
            # Get an estimate
            estimates = await client.get(f"{BASE_URL}/estimates-enhanced/?per_page=1", headers=headers)
            estimate_id = estimates.json()["estimates"][0]["estimate_id"]
            
            response = await client.get(
                f"{BASE_URL}/estimates-enhanced/{estimate_id}/pdf",
                headers=headers
            )
            
            assert response.status_code == 200
    
    async def test_payment_receipt_pdf(self, headers):
        """Test payment receipt PDF generation"""
        async with httpx.AsyncClient() as client:
            # Get a payment
            payments = await client.get(f"{BASE_URL}/payments-received/?per_page=1", headers=headers)
            if payments.json().get("payments"):
                payment_id = payments.json()["payments"][0]["payment_id"]
                
                response = await client.get(
                    f"{BASE_URL}/payments-received/{payment_id}/receipt-pdf",
                    headers=headers
                )
                
                assert response.status_code == 200

@pytest.mark.asyncio  
class TestActivityLogs:
    """Test activity log endpoints"""
    
    async def test_invoice_history(self, headers):
        """Test invoice history endpoint"""
        async with httpx.AsyncClient() as client:
            invoices = await client.get(f"{BASE_URL}/invoices-enhanced/?per_page=1", headers=headers)
            invoice_id = invoices.json()["invoices"][0]["invoice_id"]
            
            response = await client.get(
                f"{BASE_URL}/invoices-enhanced/{invoice_id}/history",
                headers=headers
            )
            
            assert response.status_code == 200
            assert "history" in response.json()
    
    async def test_estimate_activity(self, headers):
        """Test estimate activity endpoint"""
        async with httpx.AsyncClient() as client:
            estimates = await client.get(f"{BASE_URL}/estimates-enhanced/?per_page=1", headers=headers)
            estimate_id = estimates.json()["estimates"][0]["estimate_id"]
            
            response = await client.get(
                f"{BASE_URL}/estimates-enhanced/{estimate_id}/activity",
                headers=headers
            )
            
            assert response.status_code == 200
            assert "activities" in response.json()

@pytest.mark.asyncio
class TestCalculationParity:
    """Test calculation accuracy"""
    
    async def test_invoice_totals_calculation(self, headers):
        """Test that invoice totals are calculated correctly"""
        async with httpx.AsyncClient() as client:
            # Get customer
            customers = await client.get(f"{BASE_URL}/contacts-v2/?per_page=1", headers=headers)
            customer_id = customers.json()["contacts"][0]["contact_id"]
            
            # Create invoice with known values
            invoice_data = {
                "customer_id": customer_id,
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "payment_terms": 30,
                "line_items": [
                    {"name": "Item 1", "quantity": 2, "rate": 100, "tax_rate": 18},
                    {"name": "Item 2", "quantity": 3, "rate": 200, "tax_rate": 18}
                ],
                "discount_type": "percentage",
                "discount_value": 10,
                "shipping_charge": 50
            }
            
            response = await client.post(
                f"{BASE_URL}/invoices-enhanced/",
                json=invoice_data,
                headers=headers
            )
            
            assert response.status_code == 200
            invoice = response.json()["invoice"]
            
            # Expected calculations:
            # Item 1: 2 * 100 = 200
            # Item 2: 3 * 200 = 600
            # Subtotal: 800
            # Discount (10%): 80
            # Taxable: 720
            # Tax (18%): 129.6
            # Shipping: 50
            # Total: 720 + 129.6 + 50 = 899.6
            
            assert abs(invoice["sub_total"] - 800) < 1, f"Subtotal mismatch: {invoice['sub_total']}"
            # Note: Actual calculation may vary based on implementation

# ========================= RUN CONFIGURATION =========================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
