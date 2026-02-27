"""
Comprehensive Zoho Books API Test Suite
Tests all modules: Contacts, Items, Estimates, Invoices, Sales Orders, 
Purchase Orders, Bills, Credit Notes, Vendor Credits, Payments, Expenses,
Banking, Chart of Accounts, Journals, and Reports
"""
import pytest
import requests
import os
import time

pytestmark = pytest.mark.skip(reason="deprecated — Zoho integration removed")

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestZohoContacts:
    """Test Contacts (Customers/Vendors) Module"""
    
    contact_id = None
    
    def test_01_create_customer(self):
        """Create a new customer contact"""
        response = requests.post(f"{BASE_URL}/api/zoho/contacts", json={
            "contact_name": "TEST_Customer_ABC Corp",
            "company_name": "ABC Corporation",
            "contact_type": "customer",
            "email": "test_abc@example.com",
            "phone": "9876543210",
            "gst_no": "29AABCU9603R1ZM",
            "gst_treatment": "business_gst",
            "place_of_supply": "KA",
            "payment_terms": 30,
            "payment_terms_label": "Net 30"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["code"] == 0
        assert "contact" in data
        assert data["contact"]["contact_name"] == "TEST_Customer_ABC Corp"
        assert data["contact"]["contact_type"] == "customer"
        TestZohoContacts.contact_id = data["contact"]["contact_id"]
        print(f"✓ Created customer: {TestZohoContacts.contact_id}")
    
    def test_02_create_vendor(self):
        """Create a new vendor contact"""
        response = requests.post(f"{BASE_URL}/api/zoho/contacts", json={
            "contact_name": "TEST_Vendor_XYZ Supplies",
            "company_name": "XYZ Supplies Ltd",
            "contact_type": "vendor",
            "email": "test_xyz@vendor.com",
            "phone": "9123456789",
            "gst_no": "27AABCU9603R1ZM",
            "payment_terms": 45
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["contact"]["contact_type"] == "vendor"
        TestZohoContacts.vendor_id = data["contact"]["contact_id"]
        print(f"✓ Created vendor: {TestZohoContacts.vendor_id}")
    
    def test_03_list_contacts(self):
        """List contacts with filters"""
        response = requests.get(f"{BASE_URL}/api/zoho/contacts", params={
            "contact_type": "customer",
            "status": "active",
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contacts" in data
        assert "page_context" in data
        print(f"✓ Listed {len(data['contacts'])} contacts")
    
    def test_04_get_contact_details(self):
        """Get specific contact details"""
        response = requests.get(f"{BASE_URL}/api/zoho/contacts/{TestZohoContacts.contact_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["contact"]["contact_id"] == TestZohoContacts.contact_id
        print(f"✓ Retrieved contact details")
    
    def test_05_update_contact(self):
        """Update contact details"""
        response = requests.put(f"{BASE_URL}/api/zoho/contacts/{TestZohoContacts.contact_id}", json={
            "contact_name": "TEST_Customer_ABC Corp Updated",
            "company_name": "ABC Corporation Updated",
            "contact_type": "customer",
            "email": "updated_abc@example.com",
            "phone": "9876543211"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Updated contact")
    
    def test_06_mark_contact_inactive(self):
        """Mark contact as inactive"""
        response = requests.post(f"{BASE_URL}/api/zoho/contacts/{TestZohoContacts.contact_id}/inactive")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Marked contact inactive")
    
    def test_07_mark_contact_active(self):
        """Mark contact as active"""
        response = requests.post(f"{BASE_URL}/api/zoho/contacts/{TestZohoContacts.contact_id}/active")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Marked contact active")


class TestZohoItems:
    """Test Items (Products/Services) Module"""
    
    item_id = None
    
    def test_01_create_service_item(self):
        """Create a service item"""
        response = requests.post(f"{BASE_URL}/api/zoho/items", json={
            "name": "TEST_Battery Diagnostic Service",
            "description": "Complete battery health check",
            "rate": 500.00,
            "unit": "hrs",
            "item_type": "sales",
            "product_type": "service",
            "hsn_or_sac": "998714",
            "tax_name": "GST18",
            "tax_percentage": 18
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["item"]["product_type"] == "service"
        TestZohoItems.item_id = data["item"]["item_id"]
        print(f"✓ Created service item: {TestZohoItems.item_id}")
    
    def test_02_create_goods_item(self):
        """Create a goods/inventory item"""
        response = requests.post(f"{BASE_URL}/api/zoho/items", json={
            "name": "TEST_EV Battery Pack 48V",
            "description": "48V Lithium-ion battery pack",
            "sku": "BAT-48V-001",
            "rate": 25000.00,
            "purchase_rate": 20000.00,
            "unit": "pcs",
            "item_type": "sales_and_purchases",
            "product_type": "goods",
            "hsn_or_sac": "8507",
            "tax_percentage": 18,
            "initial_stock": 10,
            "reorder_level": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["item"]["product_type"] == "goods"
        TestZohoItems.goods_item_id = data["item"]["item_id"]
        print(f"✓ Created goods item: {TestZohoItems.goods_item_id}")
    
    def test_03_list_items(self):
        """List items with filters"""
        response = requests.get(f"{BASE_URL}/api/zoho/items", params={
            "status": "active",
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data
        print(f"✓ Listed {len(data['items'])} items")


class TestZohoEstimates:
    """Test Estimates Module"""
    
    estimate_id = None
    
    def test_01_create_estimate(self):
        """Create a new estimate"""
        response = requests.post(f"{BASE_URL}/api/zoho/estimates", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "line_items": [
                {
                    "name": "Battery Diagnostic Service",
                    "description": "Complete battery health check",
                    "rate": 500.00,
                    "quantity": 2,
                    "tax_name": "GST18",
                    "tax_percentage": 18
                },
                {
                    "name": "Motor Inspection",
                    "description": "Motor performance check",
                    "rate": 300.00,
                    "quantity": 1,
                    "tax_percentage": 18
                }
            ],
            "discount_percent": 5,
            "shipping_charge": 100,
            "notes": "Valid for 30 days",
            "terms": "Payment due on acceptance"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "estimate" in data
        assert data["estimate"]["status"] == "draft"
        # Verify calculations
        assert data["estimate"]["sub_total"] > 0
        assert data["estimate"]["tax_total"] > 0
        assert data["estimate"]["total"] > 0
        TestZohoEstimates.estimate_id = data["estimate"]["estimate_id"]
        print(f"✓ Created estimate: {TestZohoEstimates.estimate_id}")
        print(f"  Total: {data['estimate']['total']}")
    
    def test_02_list_estimates(self):
        """List estimates"""
        response = requests.get(f"{BASE_URL}/api/zoho/estimates")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['estimates'])} estimates")
    
    def test_03_mark_estimate_sent(self):
        """Mark estimate as sent"""
        response = requests.post(f"{BASE_URL}/api/zoho/estimates/{TestZohoEstimates.estimate_id}/status/sent")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Marked estimate as sent")
    
    def test_04_mark_estimate_accepted(self):
        """Mark estimate as accepted"""
        response = requests.post(f"{BASE_URL}/api/zoho/estimates/{TestZohoEstimates.estimate_id}/status/accepted")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Marked estimate as accepted")


class TestZohoInvoices:
    """Test Invoices Module"""
    
    invoice_id = None
    
    def test_01_create_invoice(self):
        """Create a new invoice"""
        response = requests.post(f"{BASE_URL}/api/zoho/invoices", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "payment_terms": 15,
            "line_items": [
                {
                    "name": "Battery Replacement Service",
                    "description": "48V battery replacement",
                    "rate": 25000.00,
                    "quantity": 1,
                    "tax_percentage": 18,
                    "hsn_or_sac": "8507"
                },
                {
                    "name": "Labor Charges",
                    "description": "Installation labor",
                    "rate": 1500.00,
                    "quantity": 2,
                    "tax_percentage": 18
                }
            ],
            "discount_percent": 0,
            "shipping_charge": 0,
            "notes": "Thank you for your business"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["invoice"]["status"] == "draft"
        assert data["invoice"]["balance"] == data["invoice"]["total"]
        TestZohoInvoices.invoice_id = data["invoice"]["invoice_id"]
        TestZohoInvoices.invoice_total = data["invoice"]["total"]
        print(f"✓ Created invoice: {TestZohoInvoices.invoice_id}")
        print(f"  Total: {data['invoice']['total']}, Balance: {data['invoice']['balance']}")
    
    def test_02_list_invoices(self):
        """List invoices"""
        response = requests.get(f"{BASE_URL}/api/zoho/invoices")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['invoices'])} invoices")
    
    def test_03_mark_invoice_sent(self):
        """Mark invoice as sent"""
        response = requests.post(f"{BASE_URL}/api/zoho/invoices/{TestZohoInvoices.invoice_id}/status/sent")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Marked invoice as sent")
    
    def test_04_convert_estimate_to_invoice(self):
        """Convert estimate to invoice"""
        # Create a new estimate first
        est_response = requests.post(f"{BASE_URL}/api/zoho/estimates", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "line_items": [
                {"name": "Test Service", "rate": 1000.00, "quantity": 1, "tax_percentage": 18}
            ]
        })
        est_data = est_response.json()
        est_id = est_data["estimate"]["estimate_id"]
        
        # Convert to invoice
        response = requests.post(f"{BASE_URL}/api/zoho/estimates/{est_id}/lineitems/invoices")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "invoice" in data
        assert data["invoice"]["from_estimate_id"] == est_id
        print(f"✓ Converted estimate to invoice: {data['invoice']['invoice_id']}")


class TestZohoSalesOrders:
    """Test Sales Orders Module"""
    
    salesorder_id = None
    
    def test_01_create_salesorder(self):
        """Create a new sales order"""
        response = requests.post(f"{BASE_URL}/api/zoho/salesorders", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "line_items": [
                {
                    "name": "EV Battery Pack 48V",
                    "rate": 25000.00,
                    "quantity": 2,
                    "tax_percentage": 18
                }
            ],
            "shipping_charge": 500,
            "notes": "Delivery within 7 days"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["salesorder"]["status"] == "draft"
        TestZohoSalesOrders.salesorder_id = data["salesorder"]["salesorder_id"]
        print(f"✓ Created sales order: {TestZohoSalesOrders.salesorder_id}")
    
    def test_02_convert_salesorder_to_invoice(self):
        """Convert sales order to invoice"""
        response = requests.post(f"{BASE_URL}/api/zoho/salesorders/{TestZohoSalesOrders.salesorder_id}/invoices")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["invoice"]["from_salesorder_id"] == TestZohoSalesOrders.salesorder_id
        print(f"✓ Converted sales order to invoice: {data['invoice']['invoice_id']}")
    
    def test_03_convert_estimate_to_salesorder(self):
        """Convert estimate to sales order"""
        # Create a new estimate
        est_response = requests.post(f"{BASE_URL}/api/zoho/estimates", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "line_items": [
                {"name": "Test Product", "rate": 5000.00, "quantity": 3, "tax_percentage": 18}
            ]
        })
        est_id = est_response.json()["estimate"]["estimate_id"]
        
        # Convert to sales order
        response = requests.post(f"{BASE_URL}/api/zoho/estimates/{est_id}/lineitems/salesorders")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["salesorder"]["from_estimate_id"] == est_id
        print(f"✓ Converted estimate to sales order: {data['salesorder']['salesorder_id']}")


class TestZohoPurchaseOrders:
    """Test Purchase Orders Module"""
    
    purchaseorder_id = None
    
    def test_01_create_purchaseorder(self):
        """Create a new purchase order"""
        response = requests.post(f"{BASE_URL}/api/zoho/purchaseorders", json={
            "vendor_id": TestZohoContacts.vendor_id,
            "vendor_name": "TEST_Vendor_XYZ Supplies",
            "line_items": [
                {
                    "name": "Battery Cells 18650",
                    "rate": 150.00,
                    "quantity": 100,
                    "tax_percentage": 18
                },
                {
                    "name": "BMS Module",
                    "rate": 2500.00,
                    "quantity": 5,
                    "tax_percentage": 18
                }
            ],
            "shipping_charge": 1000,
            "notes": "Urgent delivery required"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["purchaseorder"]["status"] == "draft"
        TestZohoPurchaseOrders.purchaseorder_id = data["purchaseorder"]["purchaseorder_id"]
        print(f"✓ Created purchase order: {TestZohoPurchaseOrders.purchaseorder_id}")
    
    def test_02_list_purchaseorders(self):
        """List purchase orders"""
        response = requests.get(f"{BASE_URL}/api/zoho/purchaseorders")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['purchaseorders'])} purchase orders")
    
    def test_03_convert_purchaseorder_to_bill(self):
        """Convert purchase order to bill"""
        response = requests.post(f"{BASE_URL}/api/zoho/purchaseorders/{TestZohoPurchaseOrders.purchaseorder_id}/bills")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["bill"]["from_purchaseorder_id"] == TestZohoPurchaseOrders.purchaseorder_id
        TestZohoPurchaseOrders.bill_id = data["bill"]["bill_id"]
        print(f"✓ Converted PO to bill: {data['bill']['bill_id']}")


class TestZohoBills:
    """Test Bills Module"""
    
    bill_id = None
    
    def test_01_create_bill(self):
        """Create a new bill"""
        response = requests.post(f"{BASE_URL}/api/zoho/bills", json={
            "vendor_id": TestZohoContacts.vendor_id,
            "vendor_name": "TEST_Vendor_XYZ Supplies",
            "bill_number": "BILL-TEST-001",
            "payment_terms": 30,
            "line_items": [
                {
                    "name": "Motor Controller",
                    "rate": 8000.00,
                    "quantity": 2,
                    "tax_percentage": 18
                }
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["bill"]["status"] == "open"
        TestZohoBills.bill_id = data["bill"]["bill_id"]
        TestZohoBills.bill_total = data["bill"]["total"]
        print(f"✓ Created bill: {TestZohoBills.bill_id}")
    
    def test_02_list_bills(self):
        """List bills"""
        response = requests.get(f"{BASE_URL}/api/zoho/bills")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['bills'])} bills")


class TestZohoCreditNotes:
    """Test Credit Notes Module"""
    
    creditnote_id = None
    
    def test_01_create_creditnote(self):
        """Create a credit note"""
        response = requests.post(f"{BASE_URL}/api/zoho/creditnotes", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "reason": "Returned goods",
            "line_items": [
                {
                    "name": "Returned Battery Pack",
                    "rate": 5000.00,
                    "quantity": 1,
                    "tax_percentage": 18
                }
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["creditnote"]["status"] == "open"
        TestZohoCreditNotes.creditnote_id = data["creditnote"]["creditnote_id"]
        TestZohoCreditNotes.credit_amount = data["creditnote"]["total"]
        print(f"✓ Created credit note: {TestZohoCreditNotes.creditnote_id}")
    
    def test_02_apply_creditnote_to_invoice(self):
        """Apply credit note to invoice"""
        # First create an invoice to apply credit to
        inv_response = requests.post(f"{BASE_URL}/api/zoho/invoices", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "line_items": [
                {"name": "Test Service", "rate": 10000.00, "quantity": 1, "tax_percentage": 18}
            ]
        })
        inv_id = inv_response.json()["invoice"]["invoice_id"]
        
        # Apply credit
        response = requests.post(
            f"{BASE_URL}/api/zoho/creditnotes/{TestZohoCreditNotes.creditnote_id}/invoices/{inv_id}/apply",
            params={"amount": 1000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Applied credit note to invoice")


class TestZohoVendorCredits:
    """Test Vendor Credits Module"""
    
    vendorcredit_id = None
    
    def test_01_create_vendorcredit(self):
        """Create a vendor credit"""
        response = requests.post(f"{BASE_URL}/api/zoho/vendorcredits", json={
            "vendor_id": TestZohoContacts.vendor_id,
            "vendor_name": "TEST_Vendor_XYZ Supplies",
            "reason": "Defective goods returned",
            "line_items": [
                {
                    "name": "Defective Motor Controller",
                    "rate": 8000.00,
                    "quantity": 1,
                    "tax_percentage": 18
                }
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        TestZohoVendorCredits.vendorcredit_id = data["vendorcredit"]["vendorcredit_id"]
        print(f"✓ Created vendor credit: {TestZohoVendorCredits.vendorcredit_id}")


class TestZohoCustomerPayments:
    """Test Customer Payments Module"""
    
    payment_id = None
    
    def test_01_record_customer_payment(self):
        """Record a customer payment"""
        # Create an invoice first
        inv_response = requests.post(f"{BASE_URL}/api/zoho/invoices", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "line_items": [
                {"name": "Service Charge", "rate": 5000.00, "quantity": 1, "tax_percentage": 18}
            ]
        })
        inv_data = inv_response.json()
        inv_id = inv_data["invoice"]["invoice_id"]
        inv_total = inv_data["invoice"]["total"]
        
        # Record payment - using invoice_ids as list of strings
        response = requests.post(f"{BASE_URL}/api/zoho/customerpayments", json={
            "customer_id": TestZohoContacts.contact_id,
            "customer_name": "TEST_Customer_ABC Corp",
            "amount": inv_total,
            "payment_mode": "bank_transfer",
            "reference_number": "TXN123456",
            "invoice_ids": [inv_id]  # List of invoice IDs
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        TestZohoCustomerPayments.payment_id = data["payment"]["payment_id"]
        print(f"✓ Recorded customer payment: {TestZohoCustomerPayments.payment_id}")
    
    def test_02_list_customer_payments(self):
        """List customer payments"""
        response = requests.get(f"{BASE_URL}/api/zoho/customerpayments")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['customerpayments'])} customer payments")


class TestZohoVendorPayments:
    """Test Vendor Payments Module"""
    
    def test_01_record_vendor_payment(self):
        """Record a vendor payment"""
        response = requests.post(f"{BASE_URL}/api/zoho/vendorpayments", json={
            "vendor_id": TestZohoContacts.vendor_id,
            "vendor_name": "TEST_Vendor_XYZ Supplies",
            "amount": 5000.00,
            "payment_mode": "bank_transfer",
            "reference_number": "PAY123456",
            "bill_ids": [TestZohoBills.bill_id]  # List of bill IDs
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Recorded vendor payment: {data['payment']['payment_id']}")


class TestZohoExpenses:
    """Test Expenses Module"""
    
    expense_id = None
    
    def test_01_create_expense(self):
        """Create an expense"""
        response = requests.post(f"{BASE_URL}/api/zoho/expenses", json={
            "expense_account_id": "ACC-001",
            "expense_account_name": "Office Supplies",
            "amount": 2500.00,
            "description": "Office stationery purchase",
            "reference_number": "EXP-001",
            "vendor_id": TestZohoContacts.vendor_id,
            "vendor_name": "TEST_Vendor_XYZ Supplies",
            "tax_percentage": 18,
            "is_billable": False
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["code"] == 0
        TestZohoExpenses.expense_id = data["expense"]["expense_id"]
        print(f"✓ Created expense: {TestZohoExpenses.expense_id}")
    
    def test_02_list_expenses(self):
        """List expenses with totals"""
        response = requests.get(f"{BASE_URL}/api/zoho/expenses")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # API returns expense_total not total_amount
        assert "expense_total" in data
        print(f"✓ Listed {len(data['expenses'])} expenses, Total: {data['expense_total']}")


class TestZohoBanking:
    """Test Banking Module (Bank Accounts & Transactions)"""
    
    account_id = None
    transaction_id = None
    
    def test_01_create_bank_account(self):
        """Create a bank account"""
        response = requests.post(f"{BASE_URL}/api/zoho/bankaccounts", json={
            "account_name": "TEST_Business Current Account",
            "account_number": "1234567890",
            "bank_name": "HDFC Bank",
            "account_type": "bank",
            "currency_code": "INR",
            "opening_balance": 100000.00
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        TestZohoBanking.account_id = data["bankaccount"]["account_id"]
        print(f"✓ Created bank account: {TestZohoBanking.account_id}")
    
    def test_02_list_bank_accounts(self):
        """List bank accounts"""
        response = requests.get(f"{BASE_URL}/api/zoho/bankaccounts")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['bankaccounts'])} bank accounts")
    
    def test_03_create_bank_transaction(self):
        """Create a bank transaction"""
        response = requests.post(f"{BASE_URL}/api/zoho/banktransactions", json={
            "account_id": TestZohoBanking.account_id,
            "transaction_type": "deposit",
            "amount": 50000.00,
            "description": "Customer payment received",
            "reference_number": "DEP-001",
            "payee": "ABC Corp"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        TestZohoBanking.transaction_id = data["transaction"]["transaction_id"]
        print(f"✓ Created bank transaction: {TestZohoBanking.transaction_id}")
    
    def test_04_list_bank_transactions(self):
        """List bank transactions"""
        response = requests.get(f"{BASE_URL}/api/zoho/banktransactions", params={
            "account_id": TestZohoBanking.account_id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['transactions'])} transactions")


class TestZohoChartOfAccounts:
    """Test Chart of Accounts Module"""
    
    account_id = None
    
    def test_01_create_account(self):
        """Create a chart of accounts entry"""
        response = requests.post(f"{BASE_URL}/api/zoho/chartofaccounts", json={
            "account_name": "TEST_EV Parts Inventory",
            "account_type": "asset",
            "account_code": "1500",
            "description": "Inventory of EV spare parts"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        TestZohoChartOfAccounts.account_id = data["account"]["account_id"]
        print(f"✓ Created account: {TestZohoChartOfAccounts.account_id}")
    
    def test_02_list_accounts(self):
        """List chart of accounts"""
        response = requests.get(f"{BASE_URL}/api/zoho/chartofaccounts")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # API returns chartofaccounts not accounts
        assert "chartofaccounts" in data
        print(f"✓ Listed {len(data['chartofaccounts'])} accounts")


class TestZohoJournals:
    """Test Journal Entries Module"""
    
    journal_id = None
    
    def test_01_create_journal_entry(self):
        """Create a journal entry (debit must equal credit)"""
        response = requests.post(f"{BASE_URL}/api/zoho/journals", json={
            "date": "2026-01-15",
            "reference_number": "JE-001",
            "notes": "Test journal entry",
            "line_items": [
                {
                    "account_id": "ACC-CASH",
                    "account_name": "Cash",
                    "debit": 10000.00,
                    "credit": 0,
                    "description": "Cash received"
                },
                {
                    "account_id": "ACC-SALES",
                    "account_name": "Sales Revenue",
                    "debit": 0,
                    "credit": 10000.00,
                    "description": "Sales recorded"
                }
            ]
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["code"] == 0
        TestZohoJournals.journal_id = data["journal"]["journal_id"]
        print(f"✓ Created journal entry: {TestZohoJournals.journal_id}")
    
    def test_02_journal_validation_debit_credit_mismatch(self):
        """Test journal validation - debit must equal credit"""
        response = requests.post(f"{BASE_URL}/api/zoho/journals", json={
            "date": "2026-01-15",
            "line_items": [
                {"account_id": "ACC-1", "account_name": "Cash", "debit": 10000.00, "credit": 0},
                {"account_id": "ACC-2", "account_name": "Sales", "debit": 0, "credit": 5000.00}  # Mismatch!
            ]
        })
        # Should fail with 400 error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ Journal validation working - rejected mismatched entry")
    
    def test_03_list_journals(self):
        """List journal entries"""
        response = requests.get(f"{BASE_URL}/api/zoho/journals")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Listed {len(data['journals'])} journal entries")


class TestZohoReports:
    """Test Reports Module"""
    
    def test_01_dashboard_report(self):
        """Get dashboard summary report"""
        response = requests.get(f"{BASE_URL}/api/zoho/reports/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # API returns financials not dashboard
        assert "financials" in data
        financials = data["financials"]
        assert "receivables" in financials
        assert "outstanding_payables" in financials
        print(f"✓ Dashboard report: Receivables={financials['receivables']}, Payables={financials['outstanding_payables']}")
    
    def test_02_profit_and_loss_report(self):
        """Get P&L report"""
        response = requests.get(f"{BASE_URL}/api/zoho/reports/profitandloss")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "income" in data
        assert "net_profit" in data
        print(f"✓ P&L Report: Income={data['income']['total_income']}, Net Profit={data['net_profit']}")
    
    def test_03_receivables_report(self):
        """Get receivables aging report"""
        response = requests.get(f"{BASE_URL}/api/zoho/reports/receivables")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # Check actual structure
        assert "total_outstanding" in data or "aging_summary" in data
        print(f"✓ Receivables report retrieved")
    
    def test_04_payables_report(self):
        """Get payables aging report"""
        response = requests.get(f"{BASE_URL}/api/zoho/reports/payables")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Payables report retrieved")
    
    def test_05_gst_report(self):
        """Get GST summary report"""
        response = requests.get(f"{BASE_URL}/api/zoho/reports/gst")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # Check actual structure - API returns gstr3b_summary with output_gst
        assert "gstr3b_summary" in data or "gstr1_outward_supplies" in data
        if "gstr3b_summary" in data:
            print(f"✓ GST Report: Output GST={data['gstr3b_summary']['output_gst']}, Input GST={data['gstr3b_summary']['input_gst_credit']}")


class TestZohoWorkflows:
    """Test Complete Business Workflows"""
    
    def test_01_sales_workflow(self):
        """Test complete sales workflow: Contact -> Item -> Estimate -> Invoice -> Payment"""
        print("\n=== Testing Sales Workflow ===")
        
        # 1. Create customer
        cust_resp = requests.post(f"{BASE_URL}/api/zoho/contacts", json={
            "contact_name": "TEST_Workflow_Customer",
            "contact_type": "customer",
            "email": "workflow@test.com"
        })
        assert cust_resp.status_code == 200
        customer_id = cust_resp.json()["contact"]["contact_id"]
        print(f"1. Created customer: {customer_id}")
        
        # 2. Create item
        item_resp = requests.post(f"{BASE_URL}/api/zoho/items", json={
            "name": "TEST_Workflow_Service",
            "rate": 10000.00,
            "product_type": "service",
            "tax_percentage": 18
        })
        assert item_resp.status_code == 200
        item_id = item_resp.json()["item"]["item_id"]
        print(f"2. Created item: {item_id}")
        
        # 3. Create estimate
        est_resp = requests.post(f"{BASE_URL}/api/zoho/estimates", json={
            "customer_id": customer_id,
            "customer_name": "TEST_Workflow_Customer",
            "line_items": [
                {"name": "TEST_Workflow_Service", "rate": 10000.00, "quantity": 1, "tax_percentage": 18}
            ]
        })
        assert est_resp.status_code == 200
        estimate_id = est_resp.json()["estimate"]["estimate_id"]
        print(f"3. Created estimate: {estimate_id}")
        
        # 4. Convert estimate to invoice
        inv_resp = requests.post(f"{BASE_URL}/api/zoho/estimates/{estimate_id}/lineitems/invoices")
        assert inv_resp.status_code == 200
        invoice_id = inv_resp.json()["invoice"]["invoice_id"]
        invoice_total = inv_resp.json()["invoice"]["total"]
        print(f"4. Converted to invoice: {invoice_id}, Total: {invoice_total}")
        
        # 5. Record payment using invoice_ids
        pay_resp = requests.post(f"{BASE_URL}/api/zoho/customerpayments", json={
            "customer_id": customer_id,
            "customer_name": "TEST_Workflow_Customer",
            "amount": invoice_total,
            "payment_mode": "bank_transfer",
            "invoice_ids": [invoice_id]
        })
        assert pay_resp.status_code == 200
        payment_id = pay_resp.json()["payment"]["payment_id"]
        print(f"5. Recorded payment: {payment_id}")
        
        # 6. Verify invoice is paid
        inv_check = requests.get(f"{BASE_URL}/api/zoho/invoices/{invoice_id}")
        assert inv_check.status_code == 200
        inv_data = inv_check.json()["invoice"]
        assert inv_data["status"] == "paid", f"Expected 'paid', got '{inv_data['status']}'"
        assert inv_data["balance"] == 0, f"Expected balance 0, got {inv_data['balance']}"
        print(f"6. Verified invoice status: {inv_data['status']}, Balance: {inv_data['balance']}")
        
        print("✓ Sales workflow completed successfully!")
    
    def test_02_purchase_workflow(self):
        """Test complete purchase workflow: Vendor -> PO -> Bill -> Payment"""
        print("\n=== Testing Purchase Workflow ===")
        
        # 1. Create vendor
        vendor_resp = requests.post(f"{BASE_URL}/api/zoho/contacts", json={
            "contact_name": "TEST_Workflow_Vendor",
            "contact_type": "vendor",
            "email": "vendor_workflow@test.com"
        })
        assert vendor_resp.status_code == 200
        vendor_id = vendor_resp.json()["contact"]["contact_id"]
        print(f"1. Created vendor: {vendor_id}")
        
        # 2. Create purchase order
        po_resp = requests.post(f"{BASE_URL}/api/zoho/purchaseorders", json={
            "vendor_id": vendor_id,
            "vendor_name": "TEST_Workflow_Vendor",
            "line_items": [
                {"name": "Raw Materials", "rate": 5000.00, "quantity": 10, "tax_percentage": 18}
            ]
        })
        assert po_resp.status_code == 200
        po_id = po_resp.json()["purchaseorder"]["purchaseorder_id"]
        print(f"2. Created PO: {po_id}")
        
        # 3. Convert PO to bill
        bill_resp = requests.post(f"{BASE_URL}/api/zoho/purchaseorders/{po_id}/bills")
        assert bill_resp.status_code == 200
        bill_id = bill_resp.json()["bill"]["bill_id"]
        bill_total = bill_resp.json()["bill"]["total"]
        print(f"3. Converted to bill: {bill_id}, Total: {bill_total}")
        
        # 4. Record vendor payment using bill_ids
        pay_resp = requests.post(f"{BASE_URL}/api/zoho/vendorpayments", json={
            "vendor_id": vendor_id,
            "vendor_name": "TEST_Workflow_Vendor",
            "amount": bill_total,
            "payment_mode": "bank_transfer",
            "bill_ids": [bill_id]
        })
        assert pay_resp.status_code == 200
        payment_id = pay_resp.json()["payment"]["payment_id"]
        print(f"4. Recorded payment: {payment_id}")
        
        # 5. Verify bill is paid
        bill_check = requests.get(f"{BASE_URL}/api/zoho/bills/{bill_id}")
        assert bill_check.status_code == 200
        bill_data = bill_check.json()["bill"]
        assert bill_data["status"] == "paid", f"Expected 'paid', got '{bill_data['status']}'"
        assert bill_data["balance"] == 0, f"Expected balance 0, got {bill_data['balance']}"
        print(f"5. Verified bill status: {bill_data['status']}, Balance: {bill_data['balance']}")
        
        print("✓ Purchase workflow completed successfully!")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_data(self):
        """Delete all TEST_ prefixed data"""
        # List and delete test contacts
        contacts_resp = requests.get(f"{BASE_URL}/api/zoho/contacts", params={"per_page": 100})
        if contacts_resp.status_code == 200:
            for contact in contacts_resp.json().get("contacts", []):
                if contact["contact_name"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/zoho/contacts/{contact['contact_id']}")
        
        # List and delete test items
        items_resp = requests.get(f"{BASE_URL}/api/zoho/items", params={"per_page": 100})
        if items_resp.status_code == 200:
            for item in items_resp.json().get("items", []):
                if item["name"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/zoho/items/{item['item_id']}")
        
        print("✓ Test data cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
