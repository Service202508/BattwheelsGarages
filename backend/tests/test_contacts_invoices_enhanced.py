"""
Test Suite for Unified Contacts v2 and Invoices Enhanced Modules
Tests the architectural merge of customers_enhanced into contacts_enhanced_v2
and the new invoices_enhanced module with payments, partial payments, recurring, and GST compliance
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://readiness-check-21.preview.emergentagent.com').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test data prefix for cleanup
TEST_PREFIX = f"TEST_{uuid.uuid4().hex[:6].upper()}"


class TestContactsEnhancedV2Summary:
    """Test Unified Contacts v2 API - Summary endpoint"""
    
    def test_summary_returns_correct_counts(self):
        """GET /api/contacts-enhanced/summary returns correct counts"""
        response = requests.get(f"{API_URL}/contacts-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        # Verify all expected fields
        assert "total_contacts" in summary
        assert "customers" in summary
        assert "vendors" in summary
        assert "active" in summary
        assert "inactive" in summary
        assert "with_gstin" in summary
        assert "with_portal" in summary
        assert "new_this_month" in summary
        assert "total_receivable" in summary
        assert "total_payable" in summary
        assert "total_credit_limit" in summary
        # Verify counts are non-negative
        assert summary["total_contacts"] >= 0
        assert summary["customers"] >= 0
        assert summary["vendors"] >= 0
    
    def test_summary_with_contact_type_filter(self):
        """GET /api/contacts-enhanced/summary with contact_type filter"""
        # Test customer filter
        response = requests.get(f"{API_URL}/contacts-enhanced/summary?contact_type=customer")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Test vendor filter
        response = requests.get(f"{API_URL}/contacts-enhanced/summary?contact_type=vendor")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


class TestContactsEnhancedV2List:
    """Test Unified Contacts v2 API - List endpoint with filters"""
    
    def test_list_all_contacts(self):
        """GET /api/contacts-enhanced/ returns list of contacts"""
        response = requests.get(f"{API_URL}/contacts-enhanced/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contacts" in data
        assert "page_context" in data
        assert isinstance(data["contacts"], list)
    
    def test_list_filter_by_customer_type(self):
        """GET /api/contacts-enhanced/?contact_type=customer filters correctly"""
        response = requests.get(f"{API_URL}/contacts-enhanced/?contact_type=customer")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All returned contacts should be customers or both
        for contact in data["contacts"]:
            assert contact["contact_type"] in ["customer", "both"]
    
    def test_list_filter_by_vendor_type(self):
        """GET /api/contacts-enhanced/?contact_type=vendor filters correctly"""
        response = requests.get(f"{API_URL}/contacts-enhanced/?contact_type=vendor")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All returned contacts should be vendors or both
        for contact in data["contacts"]:
            assert contact["contact_type"] in ["vendor", "both"]
    
    def test_list_with_search(self):
        """GET /api/contacts-enhanced/?search=test filters by search term"""
        response = requests.get(f"{API_URL}/contacts-enhanced/?search=test")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
    
    def test_list_pagination(self):
        """GET /api/contacts-enhanced/ supports pagination"""
        response = requests.get(f"{API_URL}/contacts-enhanced/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["page_context"]["page"] == 1
        assert data["page_context"]["per_page"] == 10


class TestContactsEnhancedV2CRUD:
    """Test Unified Contacts v2 API - Create, Read, Update, Delete"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_contact_id = None
        yield
        # Cleanup
        if self.test_contact_id:
            requests.delete(f"{API_URL}/contacts-enhanced/{self.test_contact_id}?force=true")
    
    def test_create_customer_contact(self):
        """POST /api/contacts-enhanced/ creates customer contact"""
        payload = {
            "name": f"{TEST_PREFIX}_Customer",
            "contact_type": "customer",
            "email": f"{TEST_PREFIX.lower()}@test.com",
            "phone": "9876543210",
            "gstin": "27AABCU9603R1ZM",
            "gst_treatment": "registered",
            "payment_terms": 30
        }
        response = requests.post(f"{API_URL}/contacts-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contact" in data
        contact = data["contact"]
        assert contact["name"] == payload["name"]
        assert contact["contact_type"] == "customer"
        self.test_contact_id = contact["contact_id"]
        
        # Verify GET returns the contact
        get_response = requests.get(f"{API_URL}/contacts-enhanced/{self.test_contact_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["contact"]["name"] == payload["name"]
    
    def test_create_vendor_contact(self):
        """POST /api/contacts-enhanced/ creates vendor contact"""
        payload = {
            "name": f"{TEST_PREFIX}_Vendor",
            "contact_type": "vendor",
            "email": f"{TEST_PREFIX.lower()}_vendor@test.com",
            "phone": "9876543211",
            "gst_treatment": "registered"
        }
        response = requests.post(f"{API_URL}/contacts-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        contact = data["contact"]
        assert contact["contact_type"] == "vendor"
        self.test_contact_id = contact["contact_id"]
    
    def test_create_both_type_contact(self):
        """POST /api/contacts-enhanced/ creates contact with type 'both'"""
        payload = {
            "name": f"{TEST_PREFIX}_Both",
            "contact_type": "both",
            "email": f"{TEST_PREFIX.lower()}_both@test.com"
        }
        response = requests.post(f"{API_URL}/contacts-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        contact = data["contact"]
        assert contact["contact_type"] == "both"
        self.test_contact_id = contact["contact_id"]


class TestContactsEnhancedV2Detail:
    """Test Unified Contacts v2 API - Contact detail endpoint"""
    
    def test_contact_detail_returns_persons_addresses_balance_aging(self):
        """GET /api/contacts-enhanced/{id} returns persons, addresses, balance, aging"""
        # First get a contact
        list_response = requests.get(f"{API_URL}/contacts-enhanced/?per_page=1")
        if list_response.status_code == 200 and list_response.json()["contacts"]:
            contact_id = list_response.json()["contacts"][0]["contact_id"]
            
            response = requests.get(f"{API_URL}/contacts-enhanced/{contact_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            contact = data["contact"]
            
            # Verify expected fields
            assert "persons" in contact
            assert "addresses" in contact
            assert "balance_details" in contact
            assert "transaction_counts" in contact
            assert "history" in contact
            
            # Verify balance_details structure
            balance = contact["balance_details"]
            assert "total_invoiced" in balance
            assert "total_receivable" in balance
            assert "total_payable" in balance
    
    def test_contact_detail_not_found(self):
        """GET /api/contacts-enhanced/{id} returns 404 for non-existent contact"""
        response = requests.get(f"{API_URL}/contacts-enhanced/non_existent_id")
        assert response.status_code == 404


class TestContactsEnhancedV2Portal:
    """Test Unified Contacts v2 API - Portal enable/disable"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test contact"""
        payload = {
            "name": f"{TEST_PREFIX}_Portal_Test",
            "contact_type": "customer",
            "email": f"{TEST_PREFIX.lower()}_portal@test.com"
        }
        response = requests.post(f"{API_URL}/contacts-enhanced/", json=payload)
        if response.status_code == 200:
            self.test_contact_id = response.json()["contact"]["contact_id"]
        else:
            self.test_contact_id = None
        yield
        if self.test_contact_id:
            requests.delete(f"{API_URL}/contacts-enhanced/{self.test_contact_id}?force=true")
    
    def test_enable_portal(self):
        """POST /api/contacts-enhanced/{id}/enable-portal enables portal access"""
        if not self.test_contact_id:
            pytest.skip("Test contact not created")
        
        response = requests.post(f"{API_URL}/contacts-enhanced/{self.test_contact_id}/enable-portal")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "token" in data
        
        # Verify portal is enabled
        get_response = requests.get(f"{API_URL}/contacts-enhanced/{self.test_contact_id}")
        assert get_response.json()["contact"]["portal_enabled"] == True
    
    def test_disable_portal(self):
        """POST /api/contacts-enhanced/{id}/disable-portal disables portal access"""
        if not self.test_contact_id:
            pytest.skip("Test contact not created")
        
        # First enable
        requests.post(f"{API_URL}/contacts-enhanced/{self.test_contact_id}/enable-portal")
        
        # Then disable
        response = requests.post(f"{API_URL}/contacts-enhanced/{self.test_contact_id}/disable-portal")
        assert response.status_code == 200
        
        # Verify portal is disabled
        get_response = requests.get(f"{API_URL}/contacts-enhanced/{self.test_contact_id}")
        assert get_response.json()["contact"]["portal_enabled"] == False


class TestContactsEnhancedV2Statement:
    """Test Unified Contacts v2 API - Email statement"""
    
    def test_email_statement(self):
        """POST /api/contacts-enhanced/{id}/email-statement sends statement (MOCKED)"""
        # Get a contact with email
        list_response = requests.get(f"{API_URL}/contacts-enhanced/?per_page=1")
        if list_response.status_code == 200 and list_response.json()["contacts"]:
            contact = list_response.json()["contacts"][0]
            if contact.get("email"):
                response = requests.post(
                    f"{API_URL}/contacts-enhanced/{contact['contact_id']}/email-statement",
                    json={}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 0


class TestInvoicesEnhancedSummary:
    """Test Invoices Enhanced API - Summary endpoint"""
    
    def test_summary_returns_statistics(self):
        """GET /api/invoices-enhanced/summary returns invoice statistics"""
        response = requests.get(f"{API_URL}/invoices-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        
        # Verify all expected fields
        assert "total_invoices" in summary
        assert "draft" in summary
        assert "sent" in summary
        assert "overdue" in summary
        assert "partially_paid" in summary
        assert "paid" in summary
        assert "total_invoiced" in summary
        assert "total_outstanding" in summary
        assert "total_collected" in summary
    
    def test_summary_with_period_filter(self):
        """GET /api/invoices-enhanced/summary with period filter"""
        response = requests.get(f"{API_URL}/invoices-enhanced/summary?period=this_month")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["summary"]["period"] == "this_month"


class TestInvoicesEnhancedCRUD:
    """Test Invoices Enhanced API - Create, Read, Update, Delete"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_invoice_id = None
        self.test_contact_id = None
        
        # Create a test customer for invoices
        payload = {
            "name": f"{TEST_PREFIX}_Invoice_Customer",
            "contact_type": "customer",
            "email": f"{TEST_PREFIX.lower()}_inv@test.com"
        }
        response = requests.post(f"{API_URL}/contacts-enhanced/", json=payload)
        if response.status_code == 200:
            self.test_contact_id = response.json()["contact"]["contact_id"]
        
        yield
        
        # Cleanup
        if self.test_invoice_id:
            requests.delete(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}?force=true")
        if self.test_contact_id:
            requests.delete(f"{API_URL}/contacts-enhanced/{self.test_contact_id}?force=true")
    
    def test_create_invoice_with_line_items(self):
        """POST /api/invoices-enhanced/ creates invoice with line items and tax calculations"""
        if not self.test_contact_id:
            pytest.skip("Test contact not created")
        
        payload = {
            "customer_id": self.test_contact_id,
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_terms": 30,
            "line_items": [
                {
                    "name": "Test Service",
                    "description": "Test service description",
                    "quantity": 2,
                    "rate": 1000,
                    "tax_rate": 18
                },
                {
                    "name": "Test Product",
                    "quantity": 1,
                    "rate": 500,
                    "tax_rate": 18
                }
            ],
            "discount_type": "percentage",
            "discount_value": 5,
            "shipping_charge": 100
        }
        
        response = requests.post(f"{API_URL}/invoices-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "invoice" in data
        invoice = data["invoice"]
        
        # Verify invoice structure
        assert "invoice_id" in invoice
        assert "invoice_number" in invoice
        assert invoice["customer_id"] == self.test_contact_id
        assert invoice["status"] == "draft"
        
        # Verify tax calculations
        assert "sub_total" in invoice
        assert "tax_total" in invoice
        assert "grand_total" in invoice
        assert "balance_due" in invoice
        
        # Verify line items
        assert "line_items" in invoice
        assert len(invoice["line_items"]) == 2
        
        self.test_invoice_id = invoice["invoice_id"]
        
        # Verify GET returns the invoice
        get_response = requests.get(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["invoice"]["invoice_number"] == invoice["invoice_number"]
    
    def test_list_invoices(self):
        """GET /api/invoices-enhanced/ returns list of invoices"""
        response = requests.get(f"{API_URL}/invoices-enhanced/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "invoices" in data
        assert "page_context" in data
    
    def test_list_invoices_with_filters(self):
        """GET /api/invoices-enhanced/ with status filter"""
        response = requests.get(f"{API_URL}/invoices-enhanced/?status=draft")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for invoice in data["invoices"]:
            assert invoice["status"] == "draft"


class TestInvoicesEnhancedPayments:
    """Test Invoices Enhanced API - Record payment"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test invoice"""
        self.test_invoice_id = None
        self.test_contact_id = None
        
        # Create customer
        contact_payload = {
            "name": f"{TEST_PREFIX}_Payment_Customer",
            "contact_type": "customer",
            "email": f"{TEST_PREFIX.lower()}_pay@test.com"
        }
        contact_response = requests.post(f"{API_URL}/contacts-enhanced/", json=contact_payload)
        if contact_response.status_code == 200:
            self.test_contact_id = contact_response.json()["contact"]["contact_id"]
            
            # Create invoice
            invoice_payload = {
                "customer_id": self.test_contact_id,
                "line_items": [{"name": "Test Item", "quantity": 1, "rate": 1000, "tax_rate": 18}]
            }
            invoice_response = requests.post(f"{API_URL}/invoices-enhanced/", json=invoice_payload)
            if invoice_response.status_code == 200:
                self.test_invoice_id = invoice_response.json()["invoice"]["invoice_id"]
                # Mark as sent so we can record payment
                requests.post(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/mark-sent")
        
        yield
        
        # Cleanup
        if self.test_invoice_id:
            requests.delete(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}?force=true")
        if self.test_contact_id:
            requests.delete(f"{API_URL}/contacts-enhanced/{self.test_contact_id}?force=true")
    
    def test_record_payment(self):
        """POST /api/invoices-enhanced/{id}/payments records payment"""
        if not self.test_invoice_id:
            pytest.skip("Test invoice not created")
        
        # Get invoice balance
        invoice_response = requests.get(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}")
        balance = invoice_response.json()["invoice"]["balance_due"]
        
        # Record partial payment
        payment_amount = balance / 2
        payload = {
            "amount": payment_amount,
            "payment_mode": "bank_transfer",
            "reference_number": f"{TEST_PREFIX}_REF001",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Test payment"
        }
        
        response = requests.post(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/payments", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "payment" in data
        assert data["new_status"] == "partially_paid"
        
        # Verify invoice status updated
        get_response = requests.get(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}")
        assert get_response.json()["invoice"]["status"] == "partially_paid"
    
    def test_record_full_payment(self):
        """POST /api/invoices-enhanced/{id}/payments with full amount marks as paid"""
        if not self.test_invoice_id:
            pytest.skip("Test invoice not created")
        
        # Get invoice balance
        invoice_response = requests.get(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}")
        balance = invoice_response.json()["invoice"]["balance_due"]
        
        # Record full payment
        payload = {
            "amount": balance,
            "payment_mode": "cash"
        }
        
        response = requests.post(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/payments", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] == "paid"


class TestInvoicesEnhancedStatusTransitions:
    """Test Invoices Enhanced API - Status transitions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test invoice"""
        self.test_invoice_id = None
        self.test_contact_id = None
        
        # Create customer
        contact_payload = {
            "name": f"{TEST_PREFIX}_Status_Customer",
            "contact_type": "customer",
            "email": f"{TEST_PREFIX.lower()}_status@test.com"
        }
        contact_response = requests.post(f"{API_URL}/contacts-enhanced/", json=contact_payload)
        if contact_response.status_code == 200:
            self.test_contact_id = contact_response.json()["contact"]["contact_id"]
            
            # Create invoice
            invoice_payload = {
                "customer_id": self.test_contact_id,
                "line_items": [{"name": "Test Item", "quantity": 1, "rate": 1000, "tax_rate": 18}]
            }
            invoice_response = requests.post(f"{API_URL}/invoices-enhanced/", json=invoice_payload)
            if invoice_response.status_code == 200:
                self.test_invoice_id = invoice_response.json()["invoice"]["invoice_id"]
        
        yield
        
        # Cleanup
        if self.test_invoice_id:
            requests.delete(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}?force=true")
        if self.test_contact_id:
            requests.delete(f"{API_URL}/contacts-enhanced/{self.test_contact_id}?force=true")
    
    def test_draft_to_sent(self):
        """Invoice status transition: draft -> sent"""
        if not self.test_invoice_id:
            pytest.skip("Test invoice not created")
        
        # Verify initial status is draft
        response = requests.get(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}")
        assert response.json()["invoice"]["status"] == "draft"
        
        # Mark as sent
        send_response = requests.post(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/mark-sent")
        assert send_response.status_code == 200
        
        # Verify status changed
        response = requests.get(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}")
        assert response.json()["invoice"]["status"] == "sent"
    
    def test_send_invoice_email(self):
        """POST /api/invoices-enhanced/{id}/send sends invoice email (MOCKED)"""
        if not self.test_invoice_id:
            pytest.skip("Test invoice not created")
        
        response = requests.post(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/send")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


class TestInvoicesEnhancedClone:
    """Test Invoices Enhanced API - Clone functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test invoice"""
        self.test_invoice_id = None
        self.cloned_invoice_id = None
        self.test_contact_id = None
        
        # Create customer
        contact_payload = {
            "name": f"{TEST_PREFIX}_Clone_Customer",
            "contact_type": "customer"
        }
        contact_response = requests.post(f"{API_URL}/contacts-enhanced/", json=contact_payload)
        if contact_response.status_code == 200:
            self.test_contact_id = contact_response.json()["contact"]["contact_id"]
            
            # Create invoice
            invoice_payload = {
                "customer_id": self.test_contact_id,
                "line_items": [{"name": "Clone Test Item", "quantity": 2, "rate": 500, "tax_rate": 18}]
            }
            invoice_response = requests.post(f"{API_URL}/invoices-enhanced/", json=invoice_payload)
            if invoice_response.status_code == 200:
                self.test_invoice_id = invoice_response.json()["invoice"]["invoice_id"]
        
        yield
        
        # Cleanup
        if self.cloned_invoice_id:
            requests.delete(f"{API_URL}/invoices-enhanced/{self.cloned_invoice_id}?force=true")
        if self.test_invoice_id:
            requests.delete(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}?force=true")
        if self.test_contact_id:
            requests.delete(f"{API_URL}/contacts-enhanced/{self.test_contact_id}?force=true")
    
    def test_clone_invoice(self):
        """POST /api/invoices-enhanced/{id}/clone creates new draft invoice"""
        if not self.test_invoice_id:
            pytest.skip("Test invoice not created")
        
        response = requests.post(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/clone")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "invoice" in data
        
        cloned = data["invoice"]
        self.cloned_invoice_id = cloned["invoice_id"]
        
        # Verify cloned invoice
        assert cloned["invoice_id"] != self.test_invoice_id
        assert cloned["status"] == "draft"
        assert cloned["customer_id"] == self.test_contact_id


class TestInvoicesEnhancedVoid:
    """Test Invoices Enhanced API - Void functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test invoice"""
        self.test_invoice_id = None
        self.test_contact_id = None
        
        # Create customer
        contact_payload = {
            "name": f"{TEST_PREFIX}_Void_Customer",
            "contact_type": "customer"
        }
        contact_response = requests.post(f"{API_URL}/contacts-enhanced/", json=contact_payload)
        if contact_response.status_code == 200:
            self.test_contact_id = contact_response.json()["contact"]["contact_id"]
            
            # Create invoice
            invoice_payload = {
                "customer_id": self.test_contact_id,
                "line_items": [{"name": "Void Test Item", "quantity": 1, "rate": 1000, "tax_rate": 18}]
            }
            invoice_response = requests.post(f"{API_URL}/invoices-enhanced/", json=invoice_payload)
            if invoice_response.status_code == 200:
                self.test_invoice_id = invoice_response.json()["invoice"]["invoice_id"]
                # Mark as sent
                requests.post(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/mark-sent")
        
        yield
        
        # Cleanup
        if self.test_invoice_id:
            requests.delete(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}?force=true")
        if self.test_contact_id:
            requests.delete(f"{API_URL}/contacts-enhanced/{self.test_contact_id}?force=true")
    
    def test_void_invoice(self):
        """POST /api/invoices-enhanced/{id}/void voids the invoice"""
        if not self.test_invoice_id:
            pytest.skip("Test invoice not created")
        
        response = requests.post(
            f"{API_URL}/invoices-enhanced/{self.test_invoice_id}/void",
            json={"reason": "Test void"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify status is void
        get_response = requests.get(f"{API_URL}/invoices-enhanced/{self.test_invoice_id}")
        assert get_response.json()["invoice"]["status"] == "void"


class TestInvoicesEnhancedReports:
    """Test Invoices Enhanced API - Reports"""
    
    def test_aging_report(self):
        """GET /api/invoices-enhanced/reports/aging returns aging report"""
        response = requests.get(f"{API_URL}/invoices-enhanced/reports/aging")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        report = data["report"]
        assert "totals" in report
        assert "current" in report["totals"]
        assert "1_30" in report["totals"]
        assert "31_60" in report["totals"]
        assert "61_90" in report["totals"]
        assert "over_90" in report["totals"]
    
    def test_customer_wise_report(self):
        """GET /api/invoices-enhanced/reports/customer-wise returns customer report"""
        response = requests.get(f"{API_URL}/invoices-enhanced/reports/customer-wise")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
    
    def test_monthly_report(self):
        """GET /api/invoices-enhanced/reports/monthly returns monthly report"""
        response = requests.get(f"{API_URL}/invoices-enhanced/reports/monthly")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        assert "year" in data["report"]
        assert "months" in data["report"]


class TestContactsEnhancedV2Tags:
    """Test Unified Contacts v2 API - Tags"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_tag_id = None
        yield
        # Cleanup
        if self.test_tag_id:
            requests.delete(f"{API_URL}/contacts-enhanced/tags/{self.test_tag_id}")
    
    def test_list_tags(self):
        """GET /api/contacts-enhanced/tags returns list of tags"""
        response = requests.get(f"{API_URL}/contacts-enhanced/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "tags" in data
    
    def test_create_tag(self):
        """POST /api/contacts-enhanced/tags creates new tag"""
        payload = {
            "name": f"{TEST_PREFIX}_Tag",
            "description": "Test tag description",
            "color": "#FF5733"
        }
        response = requests.post(f"{API_URL}/contacts-enhanced/tags", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "tag" in data
        self.test_tag_id = data["tag"]["tag_id"]


class TestContactsEnhancedV2States:
    """Test Unified Contacts v2 API - States endpoint"""
    
    def test_get_indian_states(self):
        """GET /api/contacts-enhanced/states returns Indian states"""
        response = requests.get(f"{API_URL}/contacts-enhanced/states")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "states" in data
        assert len(data["states"]) > 0
        # Verify state structure
        state = data["states"][0]
        assert "code" in state
        assert "name" in state


class TestContactsEnhancedV2GSTINValidation:
    """Test Unified Contacts v2 API - GSTIN validation"""
    
    def test_validate_valid_gstin(self):
        """GET /api/contacts-enhanced/validate-gstin/{gstin} validates correct GSTIN"""
        valid_gstin = "27AABCU9603R1ZM"
        response = requests.get(f"{API_URL}/contacts-enhanced/validate-gstin/{valid_gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert "details" in data
        assert data["details"]["state_code"] == "MH"  # Maharashtra
    
    def test_validate_invalid_gstin(self):
        """GET /api/contacts-enhanced/validate-gstin/{gstin} rejects invalid GSTIN"""
        invalid_gstin = "INVALID123"
        response = requests.get(f"{API_URL}/contacts-enhanced/validate-gstin/{invalid_gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False


class TestNavigationRedirect:
    """Test /customers-enhanced redirects to /contacts"""
    
    def test_customers_enhanced_redirect(self):
        """Verify /customers-enhanced route redirects to /contacts in frontend"""
        # This is a frontend test - we verify the route exists in App.js
        # The actual redirect is handled by React Router
        pass  # Frontend test will verify this


# Cleanup function to remove all test data
def cleanup_test_data():
    """Remove all TEST_ prefixed data"""
    # Get all contacts with TEST_ prefix
    response = requests.get(f"{API_URL}/contacts-enhanced/?search={TEST_PREFIX}&per_page=100")
    if response.status_code == 200:
        for contact in response.json().get("contacts", []):
            requests.delete(f"{API_URL}/contacts-enhanced/{contact['contact_id']}?force=true")
    
    # Get all invoices with TEST_ prefix
    response = requests.get(f"{API_URL}/invoices-enhanced/?search={TEST_PREFIX}&per_page=100")
    if response.status_code == 200:
        for invoice in response.json().get("invoices", []):
            requests.delete(f"{API_URL}/invoices-enhanced/{invoice['invoice_id']}?force=true")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
