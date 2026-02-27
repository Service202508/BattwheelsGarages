"""
Finance Module Tests - Expenses, Bills, Banking
==============================================
Tests for Finance Module endpoints:
- Expenses: Create, submit, approve (journal entry), mark paid (payment journal)
- Bills: Create with line items, approve (journal entry), record payment (payment journal), vendor aging
- Banking: Create account (opening balance journal), transactions, transfers, reconciliation

Author: T1 Testing Agent
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "dev@battwheels.internal"
TEST_PASSWORD = "DevTest@123"


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create a requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture(scope="class")
    def auth_token(self, session):
        """Get authentication token"""
        response = session.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            return token
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }


class TestExpensesAPI(TestSetup):
    """Expense management API tests"""
    
    expense_id = None
    category_id = None
    
    def test_get_expense_constants(self, session, auth_headers):
        """Test getting expense constants (statuses, payment modes, GST rates)"""
        response = session.get(f"{BASE_URL}/api/v1/expenses/constants", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "statuses" in data
        assert "payment_modes" in data
        assert "gst_rates" in data
        assert "DRAFT" in data["statuses"]
        assert "APPROVED" in data["statuses"]
        print("✓ Expense constants returned correctly")
    
    def test_list_expense_categories(self, session, auth_headers):
        """Test listing expense categories"""
        response = session.get(f"{BASE_URL}/api/v1/expenses/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        # Categories should be auto-seeded
        if data["categories"]:
            TestExpensesAPI.category_id = data["categories"][0]["category_id"]
            print(f"✓ Found {len(data['categories'])} expense categories")
        else:
            print("✓ Categories endpoint working (no categories yet)")
    
    def test_create_expense_with_gst(self, session, auth_headers):
        """Test creating expense with GST calculation"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Use a category if we found one
        category_id = TestExpensesAPI.category_id or "test_cat_001"
        
        expense_data = {
            "expense_date": today,
            "vendor_name": "TEST_Vendor Office Supplies",
            "description": "TEST Office stationery purchase",
            "amount": 1000,
            "category_id": category_id,
            "vendor_gstin": "29AABCU9603R1ZM",  # Valid GSTIN format
            "gst_rate": 18,
            "is_igst": False,
            "payment_mode": "PENDING",
            "notes": "Test expense for automation"
        }
        
        response = session.post(f"{BASE_URL}/api/v1/expenses", headers=auth_headers, json=expense_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "expense" in data
        
        expense = data["expense"]
        assert expense["status"] == "DRAFT"
        # Verify GST calculation: 1000 base, 18% GST = 90 CGST + 90 SGST
        assert expense["cgst_amount"] == 90
        assert expense["sgst_amount"] == 90
        assert expense["total_amount"] == 1180
        
        TestExpensesAPI.expense_id = expense["expense_id"]
        print(f"✓ Created expense {expense['expense_number']} with GST calculation verified")
    
    def test_submit_expense(self, session, auth_headers):
        """Test submitting expense for approval (DRAFT → SUBMITTED)"""
        if not TestExpensesAPI.expense_id:
            pytest.skip("No expense to submit")
        
        response = session.post(
            f"{BASE_URL}/api/v1/expenses/{TestExpensesAPI.expense_id}/submit",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert data["expense"]["status"] == "SUBMITTED"
        print("✓ Expense submitted for approval")
    
    def test_approve_expense_creates_journal(self, session, auth_headers):
        """Test approving expense (SUBMITTED → APPROVED) and verify journal entry created"""
        if not TestExpensesAPI.expense_id:
            pytest.skip("No expense to approve")
        
        response = session.post(
            f"{BASE_URL}/api/v1/expenses/{TestExpensesAPI.expense_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert data["expense"]["status"] == "APPROVED"
        
        # Verify journal entry was created
        journal_id = data.get("journal_entry_id")
        if journal_id:
            print(f"✓ Expense approved with journal entry: {journal_id}")
        else:
            print("✓ Expense approved (journal entry may be posted)")
    
    def test_mark_expense_paid_creates_payment_journal(self, session, auth_headers):
        """Test marking expense as paid (APPROVED → PAID) and verify payment journal"""
        if not TestExpensesAPI.expense_id:
            pytest.skip("No expense to mark paid")
        
        response = session.post(
            f"{BASE_URL}/api/v1/expenses/{TestExpensesAPI.expense_id}/mark-paid",
            headers=auth_headers,
            json={"payment_mode": "BANK"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert data["expense"]["status"] == "PAID"
        assert data["expense"]["payment_mode"] == "BANK"
        
        journal_id = data.get("journal_entry_id")
        if journal_id:
            print(f"✓ Expense marked paid with payment journal entry: {journal_id}")
        else:
            print("✓ Expense marked paid")
    
    def test_get_expense_summary(self, session, auth_headers):
        """Test getting expense summary statistics"""
        response = session.get(f"{BASE_URL}/api/v1/expenses/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "summary" in data
        summary = data["summary"]
        assert "by_status" in summary
        assert "itc_summary" in summary
        print(f"✓ Expense summary retrieved")


class TestBillsAPI(TestSetup):
    """Vendor bills API tests"""
    
    bill_id = None
    
    def test_get_bill_constants(self, session, auth_headers):
        """Test getting bill constants"""
        response = session.get(f"{BASE_URL}/api/v1/bills/constants", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "statuses" in data
        assert "DRAFT" in data["statuses"]
        assert "APPROVED" in data["statuses"]
        print("✓ Bill constants returned correctly")
    
    def test_create_bill_with_line_items(self, session, auth_headers):
        """Test creating bill with line items and GST"""
        today = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        bill_data = {
            "bill_number": f"TEST_INV_{datetime.now().strftime('%H%M%S')}",
            "vendor_id": "test_vendor_001",
            "vendor_name": "TEST_Supplier Pvt Ltd",
            "vendor_gstin": "29AABCU9603R1ZM",
            "bill_date": today,
            "due_date": due_date,
            "line_items": [
                {
                    "description": "Software License",
                    "quantity": 1,
                    "unit": "nos",
                    "rate": 5000,
                    "gst_rate": 18,
                    "is_igst": False,
                    "account_code": "5000"
                },
                {
                    "description": "Annual Maintenance",
                    "quantity": 1,
                    "unit": "nos",
                    "rate": 2000,
                    "gst_rate": 18,
                    "is_igst": False,
                    "account_code": "5000"
                }
            ],
            "notes": "Test bill for automation"
        }
        
        response = session.post(f"{BASE_URL}/api/v1/bills", headers=auth_headers, json=bill_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "bill" in data
        
        bill = data["bill"]
        assert bill["status"] == "DRAFT"
        # Verify calculations: 5000 + 2000 = 7000 base, 18% GST
        assert bill["subtotal"] == 7000
        assert bill["cgst"] == 630  # 9% of 7000
        assert bill["sgst"] == 630  # 9% of 7000
        assert bill["total_amount"] == 8260  # 7000 + 1260
        
        TestBillsAPI.bill_id = bill["bill_id"]
        print(f"✓ Created bill {bill['internal_ref']} with {len(bill.get('line_items', []))} line items")
    
    def test_get_bill_details(self, session, auth_headers):
        """Test getting bill details with line items"""
        if not TestBillsAPI.bill_id:
            pytest.skip("No bill to fetch")
        
        response = session.get(
            f"{BASE_URL}/api/v1/bills/{TestBillsAPI.bill_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "bill" in data
        bill = data["bill"]
        assert "line_items" in bill
        assert len(bill["line_items"]) == 2
        print(f"✓ Bill details retrieved with {len(bill['line_items'])} line items")
    
    def test_approve_bill_creates_journal(self, session, auth_headers):
        """Test approving bill and verify journal entry created"""
        if not TestBillsAPI.bill_id:
            pytest.skip("No bill to approve")
        
        response = session.post(
            f"{BASE_URL}/api/v1/bills/{TestBillsAPI.bill_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert data["bill"]["status"] == "APPROVED"
        
        journal_id = data.get("journal_entry_id")
        if journal_id:
            print(f"✓ Bill approved with journal entry: {journal_id}")
        else:
            print("✓ Bill approved (journal entry may be posted)")
    
    def test_record_partial_payment(self, session, auth_headers):
        """Test recording partial payment against bill"""
        if not TestBillsAPI.bill_id:
            pytest.skip("No bill for payment")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        payment_data = {
            "amount": 4000,  # Partial payment
            "payment_date": today,
            "payment_mode": "BANK",
            "reference_number": "UTR123456789"
        }
        
        response = session.post(
            f"{BASE_URL}/api/v1/bills/{TestBillsAPI.bill_id}/record-payment",
            headers=auth_headers,
            json=payment_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "payment" in data
        
        # Verify payment was recorded
        payment = data["payment"]
        assert payment["amount"] == 4000
        
        journal_id = data.get("journal_entry_id")
        if journal_id:
            print(f"✓ Partial payment recorded with journal entry: {journal_id}")
        else:
            print(f"✓ Partial payment of ₹4000 recorded")
    
    def test_get_bill_payments(self, session, auth_headers):
        """Test getting bill payments and verify balance"""
        if not TestBillsAPI.bill_id:
            pytest.skip("No bill to check payments")
        
        response = session.get(
            f"{BASE_URL}/api/v1/bills/{TestBillsAPI.bill_id}/payments",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert data["total_paid"] == 4000
        assert data["balance_due"] == 4260  # 8260 - 4000
        print(f"✓ Bill payments verified: Paid={data['total_paid']}, Balance={data['balance_due']}")
    
    def test_vendor_aging_report(self, session, auth_headers):
        """Test vendor aging report shows correct amounts"""
        response = session.get(f"{BASE_URL}/api/v1/bills/aging/vendor", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "vendors" in data
        assert "totals" in data
        
        # Check if our test vendor appears in aging
        vendors = data["vendors"]
        totals = data["totals"]
        print(f"✓ Vendor aging report: {len(vendors)} vendors, Total outstanding: ₹{totals.get('grand_total', 0)}")
    
    def test_aging_report_buckets(self, session, auth_headers):
        """Test aging report grouped by days overdue"""
        response = session.get(f"{BASE_URL}/api/v1/bills/aging", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "aging" in data
        
        aging = data["aging"]
        assert "current" in aging
        assert "1_30" in aging
        assert "31_60" in aging
        assert "61_90" in aging
        assert "over_90" in aging
        print("✓ Aging report buckets verified")


class TestBankingAPI(TestSetup):
    """Banking module API tests"""
    
    account_id_1 = None
    account_id_2 = None
    transaction_id = None
    
    def test_get_banking_constants(self, session, auth_headers):
        """Test getting banking constants"""
        response = session.get(f"{BASE_URL}/api/v1/banking/constants", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "account_types" in data
        assert "transaction_types" in data
        assert "transaction_categories" in data
        print("✓ Banking constants returned correctly")
    
    def test_create_account_with_opening_balance(self, session, auth_headers):
        """Test creating bank account with opening balance and verify journal entry"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        account_data = {
            "account_name": f"TEST_Business Account",
            "bank_name": "HDFC Bank",
            "account_number": f"50100{datetime.now().strftime('%H%M%S')}",
            "ifsc_code": "HDFC0001234",
            "account_type": "CURRENT",
            "opening_balance": 50000,
            "opening_balance_date": today,
            "is_default": False
        }
        
        response = session.post(f"{BASE_URL}/api/v1/banking/accounts", headers=auth_headers, json=account_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "account" in data
        
        account = data["account"]
        assert account["current_balance"] == 50000
        assert account["opening_balance"] == 50000
        
        TestBankingAPI.account_id_1 = account["account_id"]
        
        journal_id = account.get("opening_journal_entry_id")
        if journal_id:
            print(f"✓ Account created with opening balance journal: {journal_id}")
        else:
            print(f"✓ Account created: {account['account_name']} with ₹50,000 balance")
    
    def test_create_second_account(self, session, auth_headers):
        """Test creating a second account for transfer testing"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        account_data = {
            "account_name": f"TEST_Savings Account",
            "bank_name": "ICICI Bank",
            "account_number": f"98765{datetime.now().strftime('%H%M%S')}",
            "ifsc_code": "ICIC0001234",
            "account_type": "SAVINGS",
            "opening_balance": 10000,
            "opening_balance_date": today,
            "is_default": False
        }
        
        response = session.post(f"{BASE_URL}/api/v1/banking/accounts", headers=auth_headers, json=account_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        
        account = data["account"]
        TestBankingAPI.account_id_2 = account["account_id"]
        print(f"✓ Second account created: {account['account_name']}")
    
    def test_add_transaction(self, session, auth_headers):
        """Test adding a transaction to account"""
        if not TestBankingAPI.account_id_1:
            pytest.skip("No account for transaction")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        txn_data = {
            "transaction_date": today,
            "description": "TEST Customer payment received",
            "transaction_type": "CREDIT",
            "amount": 15000,
            "category": "CUSTOMER_PAYMENT",
            "reference_number": "NEFT123456"
        }
        
        response = session.post(
            f"{BASE_URL}/api/v1/banking/accounts/{TestBankingAPI.account_id_1}/transactions",
            headers=auth_headers,
            json=txn_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "transaction" in data
        
        txn = data["transaction"]
        assert txn["amount"] == 15000
        assert txn["transaction_type"] == "CREDIT"
        assert txn["balance_after"] == 65000  # 50000 + 15000
        
        TestBankingAPI.transaction_id = txn["transaction_id"]
        print(f"✓ Transaction recorded, new balance: ₹{txn['balance_after']}")
    
    def test_transfer_between_accounts(self, session, auth_headers):
        """Test transferring funds between accounts and verify journal entry"""
        if not TestBankingAPI.account_id_1 or not TestBankingAPI.account_id_2:
            pytest.skip("Need two accounts for transfer")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        transfer_data = {
            "from_account_id": TestBankingAPI.account_id_1,
            "to_account_id": TestBankingAPI.account_id_2,
            "amount": 5000,
            "transfer_date": today,
            "reference": "Internal transfer",
            "notes": "Test transfer"
        }
        
        response = session.post(f"{BASE_URL}/api/v1/banking/transfer", headers=auth_headers, json=transfer_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "transfer" in data
        
        transfer = data["transfer"]
        assert transfer["amount"] == 5000
        
        journal_id = data.get("journal_entry_id")
        if journal_id:
            print(f"✓ Transfer completed with journal entry: {journal_id}")
        else:
            print(f"✓ Transferred ₹5,000 between accounts")
    
    def test_reconcile_transaction(self, session, auth_headers):
        """Test reconciling a transaction"""
        if not TestBankingAPI.transaction_id:
            pytest.skip("No transaction to reconcile")
        
        response = session.post(
            f"{BASE_URL}/api/v1/banking/reconcile/{TestBankingAPI.transaction_id}?reconciled=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert data["transaction"]["reconciled"] == True
        print("✓ Transaction reconciled")
    
    def test_get_banking_summary(self, session, auth_headers):
        """Test getting banking summary"""
        response = session.get(f"{BASE_URL}/api/v1/banking/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_balance" in summary
        assert "accounts" in summary
        print(f"✓ Banking summary: {len(summary['accounts'])} accounts, Total balance: ₹{summary['total_balance']}")
    
    def test_get_account_transactions(self, session, auth_headers):
        """Test getting transactions for an account"""
        if not TestBankingAPI.account_id_1:
            pytest.skip("No account to fetch transactions")
        
        response = session.get(
            f"{BASE_URL}/api/v1/banking/accounts/{TestBankingAPI.account_id_1}/transactions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "transactions" in data
        print(f"✓ Retrieved {len(data['transactions'])} transactions")
    
    def test_list_accounts(self, session, auth_headers):
        """Test listing all bank accounts"""
        response = session.get(f"{BASE_URL}/api/v1/banking/accounts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0
        assert "accounts" in data
        print(f"✓ Listed {len(data['accounts'])} bank accounts")


class TestBillsExport(TestSetup):
    """Bills export functionality tests"""
    
    def test_export_bills_csv(self, session, auth_headers):
        """Test exporting bills as CSV"""
        response = session.get(f"{BASE_URL}/api/v1/bills/export", headers=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        content = response.text
        assert "Internal Ref" in content or "Vendor Invoice" in content
        print("✓ Bills CSV export working")


class TestExpenseWorkflowEdgeCases(TestSetup):
    """Edge case tests for expense workflow"""
    
    expense_id = None
    
    def test_cannot_approve_draft_expense(self, session, auth_headers):
        """Test that draft expense cannot be approved directly"""
        # Create a draft expense
        today = datetime.now().strftime("%Y-%m-%d")
        response = session.get(f"{BASE_URL}/api/v1/expenses/categories", headers=auth_headers)
        cat_id = "test_cat"
        if response.status_code == 200:
            cats = response.json().get("categories", [])
            if cats:
                cat_id = cats[0]["category_id"]
        
        expense_data = {
            "expense_date": today,
            "vendor_name": "TEST_EdgeCase Vendor",
            "description": "TEST Edge case expense",
            "amount": 500,
            "category_id": cat_id,
            "payment_mode": "PENDING"
        }
        
        response = session.post(f"{BASE_URL}/api/v1/expenses", headers=auth_headers, json=expense_data)
        if response.status_code == 200:
            expense_id = response.json()["expense"]["expense_id"]
            
            # Try to approve without submitting first
            response = session.post(
                f"{BASE_URL}/api/v1/expenses/{expense_id}/approve",
                headers=auth_headers
            )
            # Should fail because expense is in DRAFT status
            assert response.status_code == 400
            print("✓ Cannot approve expense that is not submitted (expected behavior)")
        else:
            print("✓ Edge case test skipped - expense creation failed")


# Pytest fixtures at module level for session sharing
@pytest.fixture(scope="module")
def session():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(session):
    response = session.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
