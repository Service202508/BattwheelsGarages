"""
Contact Integration Module Tests
Tests for the contact integration service that bridges enhanced contacts with transactions
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://prodready-execution.preview.emergentagent.com')

class TestContactIntegrationModule:
    """Test suite for Contact Integration API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@battwheels.in", "password": "admin123"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Known test contact IDs
        self.test_customer_id = "CON-235065AEEC94"  # Rahul Sharma
        self.test_vendor_id = "CON-3960B309AD78"   # Battery Suppliers Ltd
    
    # ==================== CONTACT SEARCH TESTS ====================
    
    def test_contact_search_all(self):
        """Test unified contact search - all contacts"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/search?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contacts" in data
        assert "count" in data
        assert isinstance(data["contacts"], list)
        print(f"✓ Contact search returned {data['count']} contacts")
    
    def test_contact_search_with_query(self):
        """Test contact search with search query"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/search?q=Rahul&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # Should find Rahul Sharma
        if data["count"] > 0:
            names = [c.get("name", "") for c in data["contacts"]]
            print(f"✓ Search for 'Rahul' found: {names}")
    
    def test_contact_search_by_type_customer(self):
        """Test contact search filtered by customer type"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/search?contact_type=customer&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All results should be customers or both
        for contact in data["contacts"]:
            assert contact.get("contact_type") in ["customer", "both"], f"Expected customer type, got {contact.get('contact_type')}"
        print(f"✓ Customer search returned {data['count']} customers")
    
    def test_contact_search_by_type_vendor(self):
        """Test contact search filtered by vendor type"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/search?contact_type=vendor&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Vendor search returned {data['count']} vendors")
    
    def test_contact_search_includes_source(self):
        """Test that search results include source (enhanced/legacy)"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/search?limit=5")
        assert response.status_code == 200
        data = response.json()
        for contact in data["contacts"]:
            assert "source" in contact, "Contact should have source field"
            assert contact["source"] in ["enhanced", "legacy"], f"Invalid source: {contact['source']}"
        print("✓ All contacts have valid source field")
    
    # ==================== CONTACT FOR TRANSACTION TESTS ====================
    
    def test_get_contact_for_transaction(self):
        """Test getting contact details formatted for transaction"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/{self.test_customer_id}/for-transaction")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contact" in data
        
        contact = data["contact"]
        # Verify required fields for transaction
        assert "contact_id" in contact
        assert "name" in contact
        assert "email" in contact
        assert "phone" in contact
        assert "gstin" in contact
        assert "place_of_supply" in contact
        assert "payment_terms" in contact
        assert "currency_code" in contact
        assert "billing_address" in contact
        assert "shipping_address" in contact
        assert "primary_contact" in contact
        assert "contact_type" in contact
        
        print(f"✓ Contact for transaction: {contact['name']}")
        print(f"  - Billing address: {contact['billing_address'] is not None}")
        print(f"  - Shipping address: {contact['shipping_address'] is not None}")
        print(f"  - Primary contact: {contact['primary_contact'] is not None}")
    
    def test_get_contact_for_transaction_not_found(self):
        """Test getting non-existent contact returns 404"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/INVALID-ID-12345/for-transaction")
        assert response.status_code == 404
        print("✓ Non-existent contact returns 404")
    
    # ==================== TRANSACTION HISTORY TESTS ====================
    
    def test_get_contact_transactions(self):
        """Test getting transaction history for a contact"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/{self.test_customer_id}/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contact_id" in data
        assert "transactions" in data
        assert "summary" in data
        assert "page_context" in data
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_invoiced" in summary
        assert "total_billed" in summary
        assert "total_outstanding" in summary
        assert "transaction_count" in summary
        
        print(f"✓ Transaction history for {self.test_customer_id}")
        print(f"  - Total transactions: {summary['transaction_count']}")
        print(f"  - Total invoiced: ₹{summary['total_invoiced']}")
        print(f"  - Total outstanding: ₹{summary['total_outstanding']}")
    
    def test_get_contact_transactions_filtered_by_type(self):
        """Test filtering transactions by type"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/{self.test_customer_id}/transactions?transaction_type=invoices")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All transactions should be invoices
        for txn in data["transactions"]:
            assert txn.get("type") == "invoice", f"Expected invoice, got {txn.get('type')}"
        print(f"✓ Filtered transactions by type: invoices")
    
    def test_get_contact_transactions_pagination(self):
        """Test transaction history pagination"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/{self.test_customer_id}/transactions?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page_context"]["page"] == 1
        assert data["page_context"]["per_page"] == 5
        print("✓ Transaction pagination works correctly")
    
    # ==================== BALANCE SUMMARY TESTS ====================
    
    def test_get_contact_balance_summary(self):
        """Test getting balance summary for a contact"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/contacts/{self.test_customer_id}/balance-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contact_id" in data
        assert "balance_summary" in data
        
        summary = data["balance_summary"]
        
        # Verify receivable structure
        assert "receivable" in summary
        receivable = summary["receivable"]
        assert "total_invoiced" in receivable
        assert "outstanding" in receivable
        assert "overdue" in receivable
        assert "overdue_count" in receivable
        assert "unused_credits" in receivable
        
        # Verify payable structure
        assert "payable" in summary
        payable = summary["payable"]
        assert "total_billed" in payable
        assert "outstanding" in payable
        assert "overdue" in payable
        assert "overdue_count" in payable
        assert "unused_credits" in payable
        
        # Verify net balance
        assert "net_balance" in summary
        
        print(f"✓ Balance summary for {self.test_customer_id}")
        print(f"  - Receivable outstanding: ₹{receivable['outstanding']}")
        print(f"  - Payable outstanding: ₹{payable['outstanding']}")
        print(f"  - Net balance: ₹{summary['net_balance']}")
    
    # ==================== TRANSACTION ENRICHMENT TESTS ====================
    
    def test_invoices_with_contacts(self):
        """Test listing invoices with enriched contact details"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/invoices/with-contacts?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "invoices" in data
        assert "page_context" in data
        
        # Verify contact enrichment
        for invoice in data["invoices"]:
            assert "contact_details" in invoice, "Invoice should have contact_details"
            assert "contact_name" in invoice, "Invoice should have contact_name"
        
        print(f"✓ Invoices with contacts: {len(data['invoices'])} returned")
    
    def test_bills_with_contacts(self):
        """Test listing bills with enriched contact details"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/bills/with-contacts?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "bills" in data
        
        for bill in data["bills"]:
            assert "contact_details" in bill, "Bill should have contact_details"
            assert "contact_name" in bill, "Bill should have contact_name"
        
        print(f"✓ Bills with contacts: {len(data['bills'])} returned")
    
    def test_estimates_with_contacts(self):
        """Test listing estimates with enriched contact details"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/estimates/with-contacts?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "estimates" in data
        
        for estimate in data["estimates"]:
            assert "contact_details" in estimate, "Estimate should have contact_details"
            assert "contact_name" in estimate, "Estimate should have contact_name"
        
        print(f"✓ Estimates with contacts: {len(data['estimates'])} returned")
    
    def test_purchase_orders_with_contacts(self):
        """Test listing purchase orders with enriched contact details"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/purchase-orders/with-contacts?per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "purchase_orders" in data
        
        print(f"✓ Purchase orders with contacts: {len(data['purchase_orders'])} returned")
    
    # ==================== MIGRATION TESTS ====================
    
    def test_migration_dry_run(self):
        """Test migration dry-run (does not actually migrate)"""
        response = self.session.post(f"{BASE_URL}/api/contact-integration/migrate/contacts-to-enhanced?dry_run=true")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["dry_run"] == True
        assert "migrated_count" in data
        assert "skipped_count" in data
        assert "error_count" in data
        assert "migrated" in data
        assert "skipped" in data
        assert "errors" in data
        
        print(f"✓ Migration dry-run completed")
        print(f"  - Would migrate: {data['migrated_count']} contacts")
        print(f"  - Would skip: {data['skipped_count']} contacts")
        print(f"  - Errors: {data['error_count']}")
    
    def test_link_transactions_dry_run(self):
        """Test linking transactions to enhanced contacts (dry-run)"""
        response = self.session.post(f"{BASE_URL}/api/contact-integration/migrate/link-transactions?dry_run=true")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["dry_run"] == True
        assert "updated_collections" in data
        assert "total_updated" in data
        
        print(f"✓ Link transactions dry-run completed")
        print(f"  - Total would update: {data['total_updated']}")
        for collection, count in data["updated_collections"].items():
            if count > 0:
                print(f"    - {collection}: {count}")
    
    # ==================== REPORTING TESTS ====================
    
    def test_report_customers_by_revenue(self):
        """Test top customers by revenue report"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/reports/customers-by-revenue?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "top_customers" in data
        
        # Verify structure of each customer entry
        for customer in data["top_customers"]:
            assert "contact_id" in customer
            assert "contact_name" in customer
            assert "company_name" in customer
            assert "total_revenue" in customer
            assert "invoice_count" in customer
            assert "avg_invoice" in customer
        
        # Verify sorted by revenue (descending)
        revenues = [c["total_revenue"] for c in data["top_customers"]]
        assert revenues == sorted(revenues, reverse=True), "Should be sorted by revenue descending"
        
        print(f"✓ Top customers by revenue: {len(data['top_customers'])} returned")
        if data["top_customers"]:
            top = data["top_customers"][0]
            print(f"  - Top customer: {top['contact_name']} ({top['company_name']})")
            print(f"  - Revenue: ₹{top['total_revenue']:,.2f}")
    
    def test_report_vendors_by_expense(self):
        """Test top vendors by expense report"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/reports/vendors-by-expense?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "top_vendors" in data
        
        # Verify structure
        for vendor in data["top_vendors"]:
            assert "contact_id" in vendor
            assert "contact_name" in vendor
            assert "total_expense" in vendor
            assert "bill_count" in vendor
            assert "avg_bill" in vendor
        
        print(f"✓ Top vendors by expense: {len(data['top_vendors'])} returned")
    
    def test_report_receivables_aging(self):
        """Test receivables aging report"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/reports/receivables-aging")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "aging_by_customer" in data
        assert "totals" in data
        assert "customer_count" in data
        
        # Verify totals structure
        totals = data["totals"]
        assert "current" in totals
        assert "days_1_30" in totals
        assert "days_31_60" in totals
        assert "days_61_90" in totals
        assert "over_90" in totals
        assert "total" in totals
        
        # Verify customer aging structure
        for customer in data["aging_by_customer"]:
            assert "contact_id" in customer
            assert "contact_name" in customer
            assert "current" in customer
            assert "days_1_30" in customer
            assert "days_31_60" in customer
            assert "days_61_90" in customer
            assert "over_90" in customer
            assert "total" in customer
            assert "invoice_count" in customer
        
        print(f"✓ Receivables aging report")
        print(f"  - Customers with receivables: {data['customer_count']}")
        print(f"  - Total receivables: ₹{totals['total']:,.2f}")
        print(f"  - Current: ₹{totals['current']:,.2f}")
        print(f"  - 1-30 days: ₹{totals['days_1_30']:,.2f}")
        print(f"  - 31-60 days: ₹{totals['days_31_60']:,.2f}")
        print(f"  - 61-90 days: ₹{totals['days_61_90']:,.2f}")
        print(f"  - Over 90 days: ₹{totals['over_90']:,.2f}")
    
    def test_report_payables_aging(self):
        """Test payables aging report"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/reports/payables-aging")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "aging_by_vendor" in data
        assert "totals" in data
        assert "vendor_count" in data
        
        # Verify totals structure
        totals = data["totals"]
        assert "current" in totals
        assert "days_1_30" in totals
        assert "days_31_60" in totals
        assert "days_61_90" in totals
        assert "over_90" in totals
        assert "total" in totals
        
        print(f"✓ Payables aging report")
        print(f"  - Vendors with payables: {data['vendor_count']}")
        print(f"  - Total payables: ₹{totals['total']:,.2f}")
    
    # ==================== FILTER TESTS ====================
    
    def test_invoices_filter_by_status(self):
        """Test filtering invoices by status"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/invoices/with-contacts?status=paid&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for invoice in data["invoices"]:
            assert invoice.get("status") == "paid", f"Expected paid status, got {invoice.get('status')}"
        print(f"✓ Invoice filter by status works")
    
    def test_invoices_filter_by_customer(self):
        """Test filtering invoices by customer_id"""
        response = self.session.get(f"{BASE_URL}/api/contact-integration/invoices/with-contacts?customer_id=C-195F30EC3C88&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for invoice in data["invoices"]:
            assert invoice.get("customer_id") == "C-195F30EC3C88"
        print(f"✓ Invoice filter by customer works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
