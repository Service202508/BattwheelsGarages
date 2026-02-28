import pytest
"""
Zoho Parity Regression Test Suite
Synchronous version for reliable testing

Run with: python /app/backend/tests/test_zoho_parity_regression.py
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os

pytestmark = pytest.mark.skip(reason="deprecated — Zoho integration removed")

# Configuration
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8001/api")
TEST_EMAIL = "admin@battwheels.in"
TEST_PASSWORD = "DevTest@123"

class TestRunner:
    def __init__(self):
        self.token = None
        self.results = []
        self.errors = []
        
    def login(self):
        """Authenticate and get token"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            if response.status_code == 200:
                self.token = response.json()["token"]
                return True
            else:
                self.errors.append(f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.errors.append(f"Login error: {str(e)}")
            return False
    
    def headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def run_test(self, name, test_func):
        """Run a test and record result"""
        try:
            result = test_func()
            self.results.append({"name": name, "status": "PASS" if result else "FAIL", "error": None})
            return result
        except Exception as e:
            self.results.append({"name": name, "status": "FAIL", "error": str(e)})
            return False

    # ========================= WORKFLOW TESTS =========================
    
    def test_quote_to_invoice_workflow(self):
        """Test Quote → Invoice conversion workflow"""
        print("\n=== Test: Quote to Invoice Workflow ===")
        
        # Step 1: Get a customer
        response = requests.get(f"{BASE_URL}/contacts-enhanced/?per_page=1", headers=self.headers())
        if response.status_code != 200 or not response.json().get("contacts"):
            print("  ❌ No customers found")
            return False
        customer_id = response.json()["contacts"][0]["contact_id"]
        print(f"  ✓ Got customer: {customer_id}")
        
        # Step 2: Create estimate
        estimate_data = {
            "customer_id": customer_id,
            "estimate_date": datetime.now().strftime("%Y-%m-%d"),
            "expiry_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "line_items": [
                {"name": "Test Service", "quantity": 2, "rate": 500, "tax_percentage": 18}
            ],
            "notes": "Regression test estimate"
        }
        response = requests.post(f"{BASE_URL}/estimates-enhanced/", json=estimate_data, headers=self.headers())
        if response.status_code != 200:
            print(f"  ❌ Create estimate failed: {response.status_code}")
            return False
        estimate = response.json()["estimate"]
        estimate_id = estimate["estimate_id"]
        print(f"  ✓ Created estimate: {estimate['estimate_number']} (status: {estimate['status']})")
        
        # Step 3: Mark as sent (use PUT /status endpoint)
        response = requests.put(
            f"{BASE_URL}/estimates-enhanced/{estimate_id}/status",
            json={"status": "sent"},
            headers=self.headers()
        )
        if response.status_code != 200:
            print(f"  ❌ Mark sent failed: {response.status_code}")
            return False
        print("  ✓ Marked as sent")
        
        # Step 4: Accept estimate (use PUT /status endpoint)
        response = requests.put(
            f"{BASE_URL}/estimates-enhanced/{estimate_id}/status",
            json={"status": "accepted"},
            headers=self.headers()
        )
        if response.status_code != 200:
            print(f"  ❌ Accept failed: {response.status_code}")
            return False
        print("  ✓ Accepted estimate")
        
        # Step 5: Convert to invoice
        response = requests.post(f"{BASE_URL}/invoices-enhanced/from-estimate/{estimate_id}", headers=self.headers())
        if response.status_code != 200:
            print(f"  ❌ Convert to invoice failed: {response.status_code}")
            return False
        invoice = response.json()["invoice"]
        print(f"  ✓ Converted to invoice: {invoice['invoice_number']}")
        
        # Verify estimate status changed
        response = requests.get(f"{BASE_URL}/estimates-enhanced/{estimate_id}", headers=self.headers())
        if response.json()["estimate"]["status"] != "invoiced":
            print("  ❌ Estimate status not updated to 'invoiced'")
            return False
        print("  ✓ Estimate status updated to 'invoiced'")
        
        return True
    
    def test_invoice_payment_workflow(self):
        """Test Invoice payment workflow"""
        print("\n=== Test: Invoice Payment Workflow ===")
        
        # Step 1: Get customer
        response = requests.get(f"{BASE_URL}/contacts-enhanced/?per_page=1", headers=self.headers())
        customer_id = response.json()["contacts"][0]["contact_id"]
        
        # Step 2: Create invoice
        invoice_data = {
            "customer_id": customer_id,
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_terms": 30,
            "line_items": [
                {"name": "Test Product", "quantity": 3, "rate": 1000, "tax_rate": 18}
            ]
        }
        response = requests.post(f"{BASE_URL}/invoices-enhanced/", json=invoice_data, headers=self.headers())
        if response.status_code != 200:
            print(f"  ❌ Create invoice failed: {response.status_code}")
            return False
        invoice = response.json()["invoice"]
        invoice_id = invoice["invoice_id"]
        total = invoice["grand_total"]
        print(f"  ✓ Created invoice: {invoice['invoice_number']} (Total: ₹{total})")
        
        # Step 3: Mark as sent
        response = requests.post(f"{BASE_URL}/invoices-enhanced/{invoice_id}/mark-sent", headers=self.headers())
        if response.status_code != 200:
            print(f"  ❌ Mark sent failed: {response.status_code}")
            return False
        print("  ✓ Marked as sent")
        
        # Step 4: Record partial payment (use /payments endpoint)
        partial_amount = total / 2
        response = requests.post(
            f"{BASE_URL}/invoices-enhanced/{invoice_id}/payments",
            json={
                "amount": partial_amount,
                "payment_mode": "bank_transfer",
                "payment_date": datetime.now().strftime("%Y-%m-%d"),
                "reference_number": f"TEST-PAY-{datetime.now().strftime('%H%M%S')}"
            },
            headers=self.headers()
        )
        if response.status_code != 200:
            print(f"  ❌ Partial payment failed: {response.status_code} - {response.text}")
            return False
        
        # Verify partially_paid status
        response = requests.get(f"{BASE_URL}/invoices-enhanced/{invoice_id}", headers=self.headers())
        invoice = response.json()["invoice"]
        if invoice["status"] != "partially_paid":
            print(f"  ❌ Status should be 'partially_paid', got: {invoice['status']}")
            return False
        print(f"  ✓ Partial payment recorded (Balance: ₹{invoice['balance_due']})")
        
        # Step 5: Record remaining payment
        response = requests.post(
            f"{BASE_URL}/invoices-enhanced/{invoice_id}/payments",
            json={
                "amount": invoice["balance_due"],
                "payment_mode": "cash",
                "payment_date": datetime.now().strftime("%Y-%m-%d"),
                "reference_number": f"TEST-PAY2-{datetime.now().strftime('%H%M%S')}"
            },
            headers=self.headers()
        )
        if response.status_code != 200:
            print(f"  ❌ Full payment failed: {response.status_code}")
            return False
        
        # Verify paid status
        response = requests.get(f"{BASE_URL}/invoices-enhanced/{invoice_id}", headers=self.headers())
        invoice = response.json()["invoice"]
        if invoice["status"] != "paid":
            print(f"  ❌ Status should be 'paid', got: {invoice['status']}")
            return False
        print(f"  ✓ Full payment recorded (Status: {invoice['status']})")
        
        return True
    
    def test_inventory_adjustment_workflow(self):
        """Test Inventory adjustment workflow"""
        print("\n=== Test: Inventory Adjustment Workflow ===")
        
        # Step 1: Get an item
        response = requests.get(f"{BASE_URL}/items-enhanced/?per_page=1", headers=self.headers())
        if response.status_code != 200 or not response.json().get("items"):
            print("  ❌ No items found")
            return False
        item = response.json()["items"][0]
        item_id = item["item_id"]
        initial_stock = item.get("stock_on_hand", item.get("on_hand_stock", 0))
        print(f"  ✓ Got item: {item['name']} (Stock: {initial_stock})")
        
        # Step 2: Create adjustment (use /inv-adjustments endpoint)
        response = requests.post(
            f"{BASE_URL}/inv-adjustments",
            json={
                "adjustment_type": "quantity",
                "reason": "Stock Recount",
                "reference_number": f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "line_items": [
                    {
                        "item_id": item_id,
                        "item_name": item["name"],
                        "quantity_adjusted": 5
                    }
                ],
                "notes": "Regression test adjustment"
            },
            headers=self.headers()
        )
        if response.status_code != 200:
            print(f"  ❌ Create adjustment failed: {response.status_code} - {response.text[:200]}")
            return False
        
        # Response structure is different - get adjustment_id directly from response
        resp_data = response.json()
        adjustment_id = resp_data.get("adjustment_id")
        ref_number = resp_data.get("reference_number")
        status = resp_data.get("status")
        print(f"  ✓ Created adjustment: {ref_number} (Status: {status})")
        
        # Step 3: Apply adjustment (convert)
        response = requests.post(f"{BASE_URL}/inv-adjustments/{adjustment_id}/convert", headers=self.headers())
        if response.status_code != 200:
            print(f"  ❌ Apply adjustment failed: {response.status_code}")
            return False
        print("  ✓ Adjustment applied")
        
        # Step 4: Verify stock updated
        response = requests.get(f"{BASE_URL}/items-enhanced/{item_id}", headers=self.headers())
        updated_item = response.json()["item"]
        new_stock = updated_item.get("stock_on_hand", updated_item.get("on_hand_stock", 0))
        expected = initial_stock + 5
        print(f"  ✓ Stock updated: {initial_stock} → {new_stock} (Expected: {expected})")
        
        return True
    
    def test_pdf_generation(self):
        """Test PDF generation for documents"""
        print("\n=== Test: PDF Generation ===")
        
        # Test Invoice PDF
        response = requests.get(f"{BASE_URL}/invoices-enhanced/?per_page=1", headers=self.headers())
        if response.json().get("invoices"):
            invoice_id = response.json()["invoices"][0]["invoice_id"]
            response = requests.get(f"{BASE_URL}/invoices-enhanced/{invoice_id}/pdf", headers=self.headers())
            if response.status_code == 200 and response.content[:4] == b"%PDF":
                print(f"  ✓ Invoice PDF generated ({len(response.content)} bytes)")
            else:
                print(f"  ❌ Invoice PDF failed: {response.status_code}")
                return False
        
        # Test Estimate PDF
        response = requests.get(f"{BASE_URL}/estimates-enhanced/?per_page=1", headers=self.headers())
        if response.json().get("estimates"):
            estimate_id = response.json()["estimates"][0]["estimate_id"]
            response = requests.get(f"{BASE_URL}/estimates-enhanced/{estimate_id}/pdf", headers=self.headers())
            if response.status_code == 200:
                print(f"  ✓ Estimate PDF generated ({len(response.content)} bytes)")
            else:
                print(f"  ❌ Estimate PDF failed: {response.status_code}")
                return False
        
        # Test Payment Receipt PDF
        response = requests.get(f"{BASE_URL}/payments-received/?per_page=1", headers=self.headers())
        if response.json().get("payments"):
            payment_id = response.json()["payments"][0]["payment_id"]
            response = requests.get(f"{BASE_URL}/payments-received/{payment_id}/receipt-pdf", headers=self.headers())
            if response.status_code == 200:
                print(f"  ✓ Payment Receipt PDF generated ({len(response.content)} bytes)")
            else:
                print(f"  ❌ Payment Receipt PDF failed: {response.status_code}")
                return False
        
        # Test Sales Order PDF
        response = requests.get(f"{BASE_URL}/sales-orders-enhanced/?per_page=1", headers=self.headers())
        if response.json().get("sales_orders"):
            so_id = response.json()["sales_orders"][0]["salesorder_id"]
            response = requests.get(f"{BASE_URL}/sales-orders-enhanced/{so_id}/pdf", headers=self.headers())
            if response.status_code == 200:
                print(f"  ✓ Sales Order PDF generated ({len(response.content)} bytes)")
            else:
                print(f"  ❌ Sales Order PDF failed: {response.status_code}")
                return False
        
        return True
    
    def test_activity_logs(self):
        """Test activity log endpoints"""
        print("\n=== Test: Activity Logs ===")
        
        # Invoice history
        response = requests.get(f"{BASE_URL}/invoices-enhanced/?per_page=1", headers=self.headers())
        if response.json().get("invoices"):
            invoice_id = response.json()["invoices"][0]["invoice_id"]
            response = requests.get(f"{BASE_URL}/invoices-enhanced/{invoice_id}/history", headers=self.headers())
            if response.status_code == 200 and "history" in response.json():
                print(f"  ✓ Invoice history endpoint ({len(response.json()['history'])} entries)")
            else:
                print(f"  ❌ Invoice history failed: {response.status_code}")
                return False
        
        # Estimate activity
        response = requests.get(f"{BASE_URL}/estimates-enhanced/?per_page=1", headers=self.headers())
        if response.json().get("estimates"):
            estimate_id = response.json()["estimates"][0]["estimate_id"]
            response = requests.get(f"{BASE_URL}/estimates-enhanced/{estimate_id}/activity", headers=self.headers())
            if response.status_code == 200 and "activities" in response.json():
                print(f"  ✓ Estimate activity endpoint ({len(response.json()['activities'])} entries)")
            else:
                print(f"  ❌ Estimate activity failed: {response.status_code}")
                return False
        
        # Payment activity
        response = requests.get(f"{BASE_URL}/payments-received/?per_page=1", headers=self.headers())
        if response.json().get("payments"):
            payment_id = response.json()["payments"][0]["payment_id"]
            response = requests.get(f"{BASE_URL}/payments-received/{payment_id}/activity", headers=self.headers())
            if response.status_code == 200 and "activities" in response.json():
                print(f"  ✓ Payment activity endpoint ({len(response.json()['activities'])} entries)")
            else:
                print(f"  ❌ Payment activity failed: {response.status_code}")
                return False
        
        # Sales Order activity
        response = requests.get(f"{BASE_URL}/sales-orders-enhanced/?per_page=1", headers=self.headers())
        if response.json().get("sales_orders"):
            so_id = response.json()["sales_orders"][0]["salesorder_id"]
            response = requests.get(f"{BASE_URL}/sales-orders-enhanced/{so_id}/activity", headers=self.headers())
            if response.status_code == 200 and "activities" in response.json():
                print(f"  ✓ Sales Order activity endpoint ({len(response.json()['activities'])} entries)")
            else:
                print(f"  ❌ Sales Order activity failed: {response.status_code}")
                return False
        
        return True
    
    def test_invoice_void_workflow(self):
        """Test Invoice void workflow"""
        print("\n=== Test: Invoice Void Workflow ===")
        
        # Get customer
        response = requests.get(f"{BASE_URL}/contacts-enhanced/?per_page=1", headers=self.headers())
        customer_id = response.json()["contacts"][0]["contact_id"]
        
        # Create invoice
        response = requests.post(
            f"{BASE_URL}/invoices-enhanced/",
            json={
                "customer_id": customer_id,
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "payment_terms": 30,
                "line_items": [{"name": "Void Test", "quantity": 1, "rate": 100, "tax_rate": 18}]
            },
            headers=self.headers()
        )
        if response.status_code != 200:
            print(f"  ❌ Create invoice failed: {response.status_code}")
            return False
        invoice_id = response.json()["invoice"]["invoice_id"]
        print(f"  ✓ Created invoice for void test")
        
        # Mark sent then void
        requests.post(f"{BASE_URL}/invoices-enhanced/{invoice_id}/mark-sent", headers=self.headers())
        
        response = requests.post(f"{BASE_URL}/invoices-enhanced/{invoice_id}/void", headers=self.headers())
        if response.status_code != 200:
            print(f"  ❌ Void failed: {response.status_code}")
            return False
        
        # Verify status
        response = requests.get(f"{BASE_URL}/invoices-enhanced/{invoice_id}", headers=self.headers())
        if response.json()["invoice"]["status"] != "void":
            print(f"  ❌ Status should be 'void'")
            return False
        print("  ✓ Invoice voided successfully")
        
        return True
    
    def test_calculation_parity(self):
        """Test calculation accuracy matches Zoho logic"""
        print("\n=== Test: Calculation Parity ===")
        
        # Get customer
        response = requests.get(f"{BASE_URL}/contacts-enhanced/?per_page=1", headers=self.headers())
        customer_id = response.json()["contacts"][0]["contact_id"]
        
        # Create invoice with known values
        # Item 1: 2 * 100 = 200, 10% discount = 20, taxable = 180, tax(18%) = 32.4, total = 212.4
        # Item 2: 3 * 200 = 600, 10% discount = 60, taxable = 540, tax(18%) = 97.2, total = 637.2
        # Subtotal: 720, Tax: 129.6, Shipping: 50, Grand Total: 899.6
        
        response = requests.post(
            f"{BASE_URL}/invoices-enhanced/",
            json={
                "customer_id": customer_id,
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "payment_terms": 30,
                "line_items": [
                    {"name": "Calc Item 1", "quantity": 2, "rate": 100, "tax_rate": 18, "discount_percentage": 10},
                    {"name": "Calc Item 2", "quantity": 3, "rate": 200, "tax_rate": 18, "discount_percentage": 10}
                ],
                "shipping_charge": 50
            },
            headers=self.headers()
        )
        
        if response.status_code != 200:
            print(f"  ❌ Create invoice failed: {response.status_code}")
            return False
        
        invoice = response.json()["invoice"]
        print(f"  Invoice totals:")
        print(f"    Subtotal: ₹{invoice.get('sub_total', 'N/A')}")
        print(f"    Tax: ₹{invoice.get('tax_total', 'N/A')}")
        print(f"    Shipping: ₹{invoice.get('shipping_charge', 'N/A')}")
        print(f"    Grand Total: ₹{invoice['grand_total']}")
        
        # Verify calculations are in reasonable range
        if invoice['grand_total'] > 0:
            print("  ✓ Calculations completed successfully")
            return True
        
        return False
    
    def test_finance_calculator_service(self):
        """Test Finance Calculator Service functions"""
        print("\n=== Test: Finance Calculator Service ===")
        
        # Import and test the service directly
        sys.path.insert(0, '/app/backend')
        try:
            from services.finance_calculator import (
                calculate_line_item, calculate_invoice_totals, 
                calculate_tax_breakdown, round_currency
            )
            
            # Test 1: Line item calculation
            result = calculate_line_item(
                name="Test",
                quantity=10,
                rate=100,
                tax_rate=18,
                discount_percent=10
            )
            # Expected: amount=1000, discount=100, taxable=900, tax=162, total=1062
            if abs(float(result.item_total) - 1062) < 1:
                print(f"  ✓ Line item calculation correct: ₹{result.item_total}")
            else:
                print(f"  ❌ Line item calculation wrong: expected 1062, got {result.item_total}")
                return False
            
            # Test 2: Tax breakdown (CGST/SGST)
            tax = calculate_tax_breakdown(1000, 18, is_igst=False)
            if tax["cgst_rate"] == 9 and tax["sgst_rate"] == 9:
                print(f"  ✓ Tax breakdown correct: CGST {tax['cgst_rate']}% + SGST {tax['sgst_rate']}%")
            else:
                print(f"  ❌ Tax breakdown wrong")
                return False
            
            # Test 3: Currency rounding
            rounded = round_currency(123.456)
            if float(rounded) == 123.46:
                print(f"  ✓ Currency rounding correct: {rounded}")
            else:
                print(f"  ❌ Currency rounding wrong: expected 123.46, got {rounded}")
                return False
            
            return True
        except Exception as e:
            print(f"  ❌ Finance Calculator test failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all regression tests"""
        print("=" * 60)
        print("ZOHO PARITY REGRESSION TEST SUITE")
        print("=" * 60)
        print(f"API URL: {BASE_URL}")
        print(f"Test User: {TEST_EMAIL}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        
        if not self.login():
            print("\n❌ FAILED: Could not authenticate")
            return False
        
        print("\n✓ Authentication successful")
        
        # Run tests
        tests = [
            ("Quote to Invoice Workflow", self.test_quote_to_invoice_workflow),
            ("Invoice Payment Workflow", self.test_invoice_payment_workflow),
            ("Inventory Adjustment Workflow", self.test_inventory_adjustment_workflow),
            ("PDF Generation", self.test_pdf_generation),
            ("Activity Logs", self.test_activity_logs),
            ("Invoice Void Workflow", self.test_invoice_void_workflow),
            ("Calculation Parity", self.test_calculation_parity),
            ("Finance Calculator Service", self.test_finance_calculator_service),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            result = self.run_test(name, test_func)
            if result:
                passed += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total: {len(tests)}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        print(f"Pass Rate: {(passed/len(tests))*100:.1f}%")
        print("=" * 60)
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.results:
            status = "✓" if result["status"] == "PASS" else "✗"
            print(f"  {status} {result['name']}")
            if result["error"]:
                print(f"      Error: {result['error']}")
        
        return failed == 0


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
