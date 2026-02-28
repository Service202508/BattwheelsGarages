"""
Backend Tests for Banking, Accountant, and Stock Transfers Modules
Tests Zoho Books style features: Bank Reconciliation, P&L, Balance Sheet, Trial Balance, Journal Entries, Stock Transfers
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://invoice-bugs.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "admin@battwheels.in"
TEST_PASSWORD = "DevTest@123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestSeedUtility:
    """Test data seeding utility"""
    
    def test_seed_all_data(self, headers):
        """Test seed all endpoint seeds data correctly"""
        response = requests.post(f"{BASE_URL}/api/seed/all", headers=headers)
        assert response.status_code == 200, f"Seed all failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "results" in data
        results = data["results"]
        # Verify seeding messages
        assert "warehouses" in results
        assert "items" in results
        assert "stock" in results
        assert "bank_accounts" in results
        print(f"PASS: Seed all - {results}")


class TestBankingAccounts:
    """Test banking accounts API"""
    
    def test_list_bank_accounts(self, headers):
        """Test listing bank accounts"""
        response = requests.get(f"{BASE_URL}/api/banking/accounts", headers=headers)
        assert response.status_code == 200, f"List accounts failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "bank_accounts" in data
        accounts = data["bank_accounts"]
        assert isinstance(accounts, list)
        print(f"PASS: List bank accounts - found {len(accounts)} accounts")
        if accounts:
            # Verify account structure
            acc = accounts[0]
            assert "bank_account_id" in acc
            assert "account_name" in acc
            assert "current_balance" in acc
            print(f"  Sample: {acc['account_name']} - Balance: {acc['current_balance']}")
        return accounts
    
    def test_get_single_bank_account(self, headers):
        """Test getting a single bank account"""
        # First get list
        list_res = requests.get(f"{BASE_URL}/api/banking/accounts", headers=headers)
        accounts = list_res.json().get("bank_accounts", [])
        if not accounts:
            pytest.skip("No bank accounts to test")
        
        account_id = accounts[0]["bank_account_id"]
        response = requests.get(f"{BASE_URL}/api/banking/accounts/{account_id}", headers=headers)
        assert response.status_code == 200, f"Get account failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "bank_account" in data
        print(f"PASS: Get bank account {account_id}")


class TestBankingDashboard:
    """Test banking dashboard stats"""
    
    def test_dashboard_stats(self, headers):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/banking/dashboard/stats", headers=headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "stats" in data
        stats = data["stats"]
        # Verify stats structure
        assert "total_bank_balance" in stats
        assert "bank_accounts_count" in stats
        assert "monthly_deposits" in stats
        assert "monthly_withdrawals" in stats
        print(f"PASS: Dashboard stats - Balance: {stats['total_bank_balance']}, Accounts: {stats['bank_accounts_count']}")


class TestChartOfAccounts:
    """Test chart of accounts API"""
    
    def test_list_chart_of_accounts(self, headers):
        """Test listing chart of accounts"""
        response = requests.get(f"{BASE_URL}/api/banking/chart-of-accounts", headers=headers)
        assert response.status_code == 200, f"List CoA failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "chart_of_accounts" in data
        accounts = data["chart_of_accounts"]
        assert isinstance(accounts, list)
        print(f"PASS: List chart of accounts - found {len(accounts)} entries")
        if accounts:
            # Verify account types
            acc = accounts[0]
            assert "account_id" in acc
            assert "account_name" in acc
            assert "account_type" in acc
            print(f"  Sample: {acc['account_code']} - {acc['account_name']} ({acc['account_type']})")
    
    def test_create_chart_account(self, headers):
        """Test creating a chart of accounts entry"""
        test_account = {
            "account_name": f"TEST_Account_{datetime.now().strftime('%H%M%S')}",
            "account_type": "expense",
            "account_sub_type": "operating_expense",
            "description": "Test account for testing"
        }
        response = requests.post(f"{BASE_URL}/api/banking/chart-of-accounts", headers=headers, json=test_account)
        assert response.status_code == 200, f"Create CoA failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "account" in data
        print(f"PASS: Create chart of accounts entry")


class TestTrialBalance:
    """Test trial balance report"""
    
    def test_trial_balance_report(self, headers):
        """Test getting trial balance report"""
        response = requests.get(f"{BASE_URL}/api/banking/reports/trial-balance", headers=headers)
        assert response.status_code == 200, f"Trial balance failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        # Verify trial balance structure
        assert "accounts" in data
        assert "total_debit" in data
        assert "total_credit" in data
        assert "is_balanced" in data
        print(f"PASS: Trial balance - Debit: {data['total_debit']}, Credit: {data['total_credit']}, Balanced: {data['is_balanced']}")


class TestFinancialReports:
    """Test financial reports: P&L, Balance Sheet, Cash Flow"""
    
    def test_profit_loss_report(self, headers):
        """Test profit and loss report"""
        response = requests.get(f"{BASE_URL}/api/banking/reports/profit-loss", headers=headers)
        assert response.status_code == 200, f"P&L report failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "income" in data
        assert "expenses" in data
        assert "net_profit" in data
        print(f"PASS: P&L Report - Net Profit: {data['net_profit']}")
    
    def test_balance_sheet_report(self, headers):
        """Test balance sheet report"""
        response = requests.get(f"{BASE_URL}/api/banking/reports/balance-sheet", headers=headers)
        assert response.status_code == 200, f"Balance sheet failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        print(f"PASS: Balance Sheet - Assets: {data['assets'].get('total')}, Liabilities: {data['liabilities'].get('total')}")
    
    def test_cash_flow_report(self, headers):
        """Test cash flow report"""
        response = requests.get(f"{BASE_URL}/api/banking/reports/cash-flow", headers=headers)
        assert response.status_code == 200, f"Cash flow failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "cash_inflows" in data
        assert "cash_outflows" in data
        assert "net_cash_flow" in data
        print(f"PASS: Cash Flow - Inflows: {data['cash_inflows']}, Outflows: {data['cash_outflows']}")


class TestJournalEntries:
    """Test journal entries API"""
    
    def test_list_journal_entries(self, headers):
        """Test listing journal entries"""
        response = requests.get(f"{BASE_URL}/api/banking/journal-entries", headers=headers)
        assert response.status_code == 200, f"List JE failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "journal_entries" in data
        print(f"PASS: List journal entries - found {len(data['journal_entries'])} entries")
    
    def test_create_journal_entry_balanced(self, headers):
        """Test creating a balanced journal entry"""
        # First get chart of accounts
        coa_res = requests.get(f"{BASE_URL}/api/banking/chart-of-accounts", headers=headers)
        accounts = coa_res.json().get("chart_of_accounts", [])
        if len(accounts) < 2:
            pytest.skip("Need at least 2 accounts for journal entry")
        
        acc1 = accounts[0]
        acc2 = accounts[1]
        
        entry = {
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "reference": "TEST-JE-001",
            "notes": "Test journal entry",
            "lines": [
                {"account_id": acc1["account_id"], "account_name": acc1["account_name"], "debit": 1000, "credit": 0},
                {"account_id": acc2["account_id"], "account_name": acc2["account_name"], "debit": 0, "credit": 1000}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/banking/journal-entries", headers=headers, json=entry)
        assert response.status_code == 200, f"Create JE failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "journal_entry" in data
        print(f"PASS: Create balanced journal entry")
    
    def test_create_journal_entry_unbalanced_fails(self, headers):
        """Test that unbalanced journal entry fails"""
        coa_res = requests.get(f"{BASE_URL}/api/banking/chart-of-accounts", headers=headers)
        accounts = coa_res.json().get("chart_of_accounts", [])
        if len(accounts) < 2:
            pytest.skip("Need at least 2 accounts for journal entry")
        
        acc1 = accounts[0]
        acc2 = accounts[1]
        
        # Unbalanced entry
        entry = {
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "reference": "TEST-JE-UNBALANCED",
            "lines": [
                {"account_id": acc1["account_id"], "debit": 1000, "credit": 0},
                {"account_id": acc2["account_id"], "debit": 0, "credit": 500}  # Unbalanced
            ]
        }
        response = requests.post(f"{BASE_URL}/api/banking/journal-entries", headers=headers, json=entry)
        assert response.status_code == 400, f"Expected 400 for unbalanced JE, got {response.status_code}"
        print(f"PASS: Unbalanced journal entry rejected correctly")


class TestReconciliation:
    """Test bank reconciliation API"""
    
    def test_reconciliation_history(self, headers):
        """Test getting reconciliation history"""
        response = requests.get(f"{BASE_URL}/api/banking/reconciliation/history", headers=headers)
        assert response.status_code == 200, f"Reconciliation history failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "reconciliations" in data
        print(f"PASS: Reconciliation history - found {len(data['reconciliations'])} entries")
    
    def test_start_reconciliation(self, headers):
        """Test starting a reconciliation session"""
        # Get bank accounts
        acc_res = requests.get(f"{BASE_URL}/api/banking/accounts", headers=headers)
        accounts = acc_res.json().get("bank_accounts", [])
        if not accounts:
            pytest.skip("No bank accounts for reconciliation")
        
        recon_data = {
            "bank_account_id": accounts[0]["bank_account_id"],
            "statement_date": datetime.now().strftime("%Y-%m-%d"),
            "statement_balance": accounts[0].get("current_balance", 0)
        }
        response = requests.post(f"{BASE_URL}/api/banking/reconciliation/start", headers=headers, json=recon_data)
        assert response.status_code == 200, f"Start reconciliation failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "reconciliation" in data
        print(f"PASS: Start reconciliation - ID: {data['reconciliation'].get('reconciliation_id')}")


class TestStockTransfers:
    """Test stock transfers API"""
    
    def test_list_stock_transfers(self, headers):
        """Test listing stock transfers"""
        response = requests.get(f"{BASE_URL}/api/stock-transfers/", headers=headers)
        assert response.status_code == 200, f"List transfers failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "transfers" in data
        transfers = data["transfers"]
        print(f"PASS: List stock transfers - found {len(transfers)} transfers")
        if transfers:
            t = transfers[0]
            print(f"  Sample: {t.get('transfer_number')} - {t.get('source_warehouse_name')} -> {t.get('destination_warehouse_name')} [{t.get('status')}]")
        return transfers
    
    def test_stock_transfers_stats(self, headers):
        """Test stock transfers statistics"""
        response = requests.get(f"{BASE_URL}/api/stock-transfers/stats/summary", headers=headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "stats" in data
        stats = data["stats"]
        assert "total_transfers" in stats
        assert "by_status" in stats
        print(f"PASS: Stock transfers stats - Total: {stats['total_transfers']}, By Status: {stats['by_status']}")
    
    def test_stock_transfers_filter_by_status(self, headers):
        """Test filtering transfers by status"""
        response = requests.get(f"{BASE_URL}/api/stock-transfers/?status=received", headers=headers)
        assert response.status_code == 200, f"Filter transfers failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        transfers = data.get("transfers", [])
        # All returned should have status=received
        for t in transfers:
            assert t.get("status") == "received", f"Expected status=received, got {t.get('status')}"
        print(f"PASS: Filter by status=received - found {len(transfers)} transfers")


class TestInventoryEnhanced:
    """Test inventory enhanced for stock management"""
    
    def test_list_warehouses(self, headers):
        """Test listing warehouses"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/warehouses", headers=headers)
        assert response.status_code == 200, f"List warehouses failed: {response.text}"
        data = response.json()
        assert "warehouses" in data
        warehouses = data["warehouses"]
        print(f"PASS: List warehouses - found {len(warehouses)} warehouses")
        if warehouses:
            w = warehouses[0]
            print(f"  Sample: {w.get('name')} ({w.get('location')})")
        return warehouses
    
    def test_list_stock(self, headers):
        """Test listing stock across warehouses"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/stock", headers=headers)
        assert response.status_code == 200, f"List stock failed: {response.text}"
        data = response.json()
        assert "stock" in data
        stock = data["stock"]
        print(f"PASS: List stock - found {len(stock)} stock records")


class TestNavigationIntegration:
    """Test that navigation links work with backend APIs"""
    
    def test_stock_transfers_page_data(self, headers):
        """Test data required for /stock-transfers page"""
        # Stock transfers list
        res1 = requests.get(f"{BASE_URL}/api/stock-transfers/", headers=headers)
        assert res1.status_code == 200, "Stock transfers list failed"
        
        # Stock transfers stats
        res2 = requests.get(f"{BASE_URL}/api/stock-transfers/stats/summary", headers=headers)
        assert res2.status_code == 200, "Stock transfers stats failed"
        
        # Warehouses for dropdown
        res3 = requests.get(f"{BASE_URL}/api/inventory-enhanced/warehouses", headers=headers)
        assert res3.status_code == 200, "Warehouses list failed"
        
        print(f"PASS: Stock transfers page data - All APIs working")
    
    def test_accountant_page_data(self, headers):
        """Test data required for /accountant page"""
        # Banking dashboard stats
        res1 = requests.get(f"{BASE_URL}/api/banking/dashboard/stats", headers=headers)
        assert res1.status_code == 200, "Dashboard stats failed"
        
        # Bank accounts
        res2 = requests.get(f"{BASE_URL}/api/banking/accounts", headers=headers)
        assert res2.status_code == 200, "Bank accounts failed"
        
        # Chart of accounts
        res3 = requests.get(f"{BASE_URL}/api/banking/chart-of-accounts", headers=headers)
        assert res3.status_code == 200, "Chart of accounts failed"
        
        # Trial balance
        res4 = requests.get(f"{BASE_URL}/api/banking/reports/trial-balance", headers=headers)
        assert res4.status_code == 200, "Trial balance failed"
        
        # P&L
        res5 = requests.get(f"{BASE_URL}/api/banking/reports/profit-loss", headers=headers)
        assert res5.status_code == 200, "P&L report failed"
        
        # Balance sheet
        res6 = requests.get(f"{BASE_URL}/api/banking/reports/balance-sheet", headers=headers)
        assert res6.status_code == 200, "Balance sheet failed"
        
        print(f"PASS: Accountant page data - All APIs working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
