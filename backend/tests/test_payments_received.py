"""
Payments Received Module - Backend API Tests
Tests for Zoho-style payment recording, multi-invoice allocation, overpayments, credits, and refunds.
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://secure-auth-suite-1.preview.emergentagent.com').rstrip('/')

# Test data
TEST_CUSTOMER_ID = "CUST-93AE14BE3618"  # Full Zoho Test Co
TEST_CUSTOMER_NAME = "Full Zoho Test Co"


class TestPaymentsReceivedSummary:
    """Test GET /api/payments-received/summary - Summary statistics"""
    
    def test_summary_default_period(self):
        """Test summary with default period (this_month)"""
        response = requests.get(f"{BASE_URL}/api/payments-received/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_received" in summary
        assert "invoice_payments" in summary
        assert "retainer_payments" in summary
        assert "payment_count" in summary
        assert "by_payment_mode" in summary
        assert "unused_credits" in summary
        assert summary["period"] == "this_month"
        
        # Verify data types
        assert isinstance(summary["total_received"], (int, float))
        assert isinstance(summary["payment_count"], int)
    
    def test_summary_different_periods(self):
        """Test summary with different time periods"""
        periods = ["today", "this_week", "this_month", "this_quarter", "this_year"]
        
        for period in periods:
            response = requests.get(f"{BASE_URL}/api/payments-received/summary?period={period}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == 0
            assert data["summary"]["period"] == period


class TestPaymentsReceivedList:
    """Test GET /api/payments-received/ - List payments with filters"""
    
    def test_list_all_payments(self):
        """Test listing all payments"""
        response = requests.get(f"{BASE_URL}/api/payments-received/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "payments" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        
        # Verify payment structure
        if data["payments"]:
            payment = data["payments"][0]
            assert "payment_id" in payment
            assert "payment_number" in payment
            assert "customer_id" in payment
            assert "customer_name" in payment
            assert "amount" in payment
            assert "payment_mode" in payment
            assert "payment_date" in payment
    
    def test_list_payments_by_customer(self):
        """Test filtering payments by customer"""
        response = requests.get(f"{BASE_URL}/api/payments-received/?customer_id={TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        # All payments should be for the specified customer
        for payment in data["payments"]:
            assert payment["customer_id"] == TEST_CUSTOMER_ID
    
    def test_list_payments_by_mode(self):
        """Test filtering payments by payment mode"""
        response = requests.get(f"{BASE_URL}/api/payments-received/?payment_mode=bank_transfer")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        for payment in data["payments"]:
            assert payment["payment_mode"] == "bank_transfer"
    
    def test_list_payments_search(self):
        """Test searching payments"""
        response = requests.get(f"{BASE_URL}/api/payments-received/?search=PMT")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
    
    def test_list_payments_pagination(self):
        """Test pagination"""
        response = requests.get(f"{BASE_URL}/api/payments-received/?page=1&per_page=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 10


class TestPaymentDetails:
    """Test GET /api/payments-received/{id} - Get payment details"""
    
    def test_get_existing_payment(self):
        """Test getting details of an existing payment"""
        # First get a payment ID from the list
        list_response = requests.get(f"{BASE_URL}/api/payments-received/")
        assert list_response.status_code == 200
        
        payments = list_response.json()["payments"]
        if not payments:
            pytest.skip("No payments available for testing")
        
        payment_id = payments[0]["payment_id"]
        
        # Get payment details
        response = requests.get(f"{BASE_URL}/api/payments-received/{payment_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "payment" in data
        assert "invoice_details" in data
        assert "customer" in data
        assert "history" in data
        
        # Verify payment data
        payment = data["payment"]
        assert payment["payment_id"] == payment_id
    
    def test_get_nonexistent_payment(self):
        """Test getting a non-existent payment returns 404"""
        response = requests.get(f"{BASE_URL}/api/payments-received/PAY-NONEXISTENT")
        assert response.status_code == 404


class TestCustomerOpenInvoices:
    """Test GET /api/payments-received/customer/{id}/open-invoices"""
    
    def test_get_customer_open_invoices(self):
        """Test getting open invoices for a customer"""
        response = requests.get(f"{BASE_URL}/api/payments-received/customer/{TEST_CUSTOMER_ID}/open-invoices")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "customer" in data
        assert "open_invoices" in data
        assert "available_credits" in data
        assert "total_outstanding" in data
        assert "total_credits" in data
        
        # Verify customer info
        customer = data["customer"]
        assert customer["contact_id"] == TEST_CUSTOMER_ID


class TestCreditsEndpoints:
    """Test credits management endpoints"""
    
    def test_list_all_credits(self):
        """Test GET /api/payments-received/credits - List all credits"""
        response = requests.get(f"{BASE_URL}/api/payments-received/credits")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "credits" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
    
    def test_list_credits_by_status(self):
        """Test filtering credits by status"""
        response = requests.get(f"{BASE_URL}/api/payments-received/credits?status=available")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        for credit in data["credits"]:
            assert credit["status"] == "available"
    
    def test_get_customer_credits(self):
        """Test GET /api/payments-received/credits/{customer_id}"""
        response = requests.get(f"{BASE_URL}/api/payments-received/credits/{TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "available_credits" in data
        assert "used_credits" in data
        assert "total_available" in data
        
        # Verify credit structure
        if data["available_credits"]:
            credit = data["available_credits"][0]
            assert "credit_id" in credit
            assert "customer_id" in credit
            assert "amount" in credit
            assert "status" in credit


class TestRecordPayment:
    """Test POST /api/payments-received/ - Record new payment"""
    
    def test_record_retainer_payment(self):
        """Test recording a retainer/advance payment"""
        payment_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "amount": 500.0,
            "payment_mode": "cash",
            "deposit_to_account": "Petty Cash",
            "reference_number": f"TEST-{uuid.uuid4().hex[:8].upper()}",
            "notes": "Test retainer payment",
            "allocations": [],
            "is_retainer": True
        }
        
        response = requests.post(f"{BASE_URL}/api/payments-received/", json=payment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "payment" in data
        assert data["message"] == "Payment recorded successfully"
        
        payment = data["payment"]
        assert payment["customer_id"] == TEST_CUSTOMER_ID
        assert payment["amount"] == 500.0
        assert payment["is_retainer"] == True
        assert payment["payment_mode"] == "cash"
        
        # Store for cleanup
        TestRecordPayment.created_payment_id = payment["payment_id"]
    
    def test_record_payment_invalid_customer(self):
        """Test recording payment with invalid customer returns error"""
        payment_data = {
            "customer_id": "INVALID-CUSTOMER-ID",
            "amount": 100.0,
            "payment_mode": "cash"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments-received/", json=payment_data)
        assert response.status_code == 404
    
    def test_record_payment_with_bank_charges(self):
        """Test recording payment with bank charges"""
        payment_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "amount": 1000.0,
            "payment_mode": "bank_transfer",
            "bank_charges": 50.0,
            "reference_number": f"TEST-BC-{uuid.uuid4().hex[:8].upper()}",
            "notes": "Test payment with bank charges",
            "allocations": [],
            "is_retainer": True
        }
        
        response = requests.post(f"{BASE_URL}/api/payments-received/", json=payment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        payment = data["payment"]
        assert payment["bank_charges"] == 50.0
        
        # Store for cleanup
        TestRecordPayment.created_payment_with_charges_id = payment["payment_id"]


class TestDeletePayment:
    """Test DELETE /api/payments-received/{id} - Delete payment"""
    
    def test_delete_payment(self):
        """Test deleting a payment"""
        # First create a payment to delete
        payment_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "amount": 100.0,
            "payment_mode": "cash",
            "is_retainer": True,
            "reference_number": f"TEST-DEL-{uuid.uuid4().hex[:8].upper()}"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/payments-received/", json=payment_data)
        assert create_response.status_code == 200
        
        payment_id = create_response.json()["payment"]["payment_id"]
        
        # Delete the payment
        delete_response = requests.delete(f"{BASE_URL}/api/payments-received/{payment_id}")
        assert delete_response.status_code == 200
        
        data = delete_response.json()
        assert data["code"] == 0
        assert data["message"] == "Payment deleted successfully"
        
        # Verify payment is deleted
        get_response = requests.get(f"{BASE_URL}/api/payments-received/{payment_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_payment(self):
        """Test deleting a non-existent payment returns 404"""
        response = requests.delete(f"{BASE_URL}/api/payments-received/PAY-NONEXISTENT")
        assert response.status_code == 404


class TestPaymentSettings:
    """Test payment settings endpoints"""
    
    def test_get_settings(self):
        """Test GET /api/payments-received/settings"""
        response = requests.get(f"{BASE_URL}/api/payments-received/settings")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "settings" in data
        
        settings = data["settings"]
        assert "numbering" in settings
        assert "defaults" in settings
        assert "accounts" in settings


class TestPaymentReports:
    """Test payment reports endpoints"""
    
    def test_report_by_customer(self):
        """Test GET /api/payments-received/reports/by-customer"""
        response = requests.get(f"{BASE_URL}/api/payments-received/reports/by-customer")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
    
    def test_report_by_mode(self):
        """Test GET /api/payments-received/reports/by-mode"""
        response = requests.get(f"{BASE_URL}/api/payments-received/reports/by-mode")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "report" in data


class TestExportImport:
    """Test export/import functionality"""
    
    def test_export_payments(self):
        """Test GET /api/payments-received/export"""
        response = requests.get(f"{BASE_URL}/api/payments-received/export")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "filename" in data
    
    def test_get_import_template(self):
        """Test GET /api/payments-received/import/template"""
        response = requests.get(f"{BASE_URL}/api/payments-received/import/template")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "template" in data
        assert "filename" in data


class TestRefundEndpoint:
    """Test refund functionality"""
    
    def test_refund_requires_available_credit(self):
        """Test that refund fails if no credit available"""
        # Create a payment without overpayment
        payment_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "amount": 100.0,
            "payment_mode": "cash",
            "is_retainer": False,
            "allocations": [],
            "reference_number": f"TEST-REF-{uuid.uuid4().hex[:8].upper()}"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/payments-received/", json=payment_data)
        assert create_response.status_code == 200
        
        payment_id = create_response.json()["payment"]["payment_id"]
        
        # Try to refund more than available
        refund_data = {
            "amount": 1000.0,  # More than available
            "payment_mode": "bank_transfer"
        }
        
        refund_response = requests.post(f"{BASE_URL}/api/payments-received/{payment_id}/refund", json=refund_data)
        assert refund_response.status_code == 400
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payments-received/{payment_id}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_payments(self):
        """Clean up test payments created during tests"""
        # Get all payments
        response = requests.get(f"{BASE_URL}/api/payments-received/?search=TEST-")
        if response.status_code == 200:
            payments = response.json().get("payments", [])
            for payment in payments:
                if "TEST-" in payment.get("reference_number", ""):
                    requests.delete(f"{BASE_URL}/api/payments-received/{payment['payment_id']}")
        
        # Also cleanup specific IDs if stored
        if hasattr(TestRecordPayment, 'created_payment_id'):
            requests.delete(f"{BASE_URL}/api/payments-received/{TestRecordPayment.created_payment_id}")
        if hasattr(TestRecordPayment, 'created_payment_with_charges_id'):
            requests.delete(f"{BASE_URL}/api/payments-received/{TestRecordPayment.created_payment_with_charges_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
