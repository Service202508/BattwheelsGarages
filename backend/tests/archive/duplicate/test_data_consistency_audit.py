"""
Data Consistency Audit - Backend API Tests
Tests for organization_id handling in financial dashboard and ticket endpoints.
Issue: Inconsistent data across mobile and desktop views (₹0 for receivables/payables).
Root cause: organization_id not being passed correctly in API calls.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test organization ID
ORG_ID = "org_71f0df814d6d"

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "DevTest@123"
TECH_EMAIL = "deepak@battwheelsgarages.in"
TECH_PASSWORD = "DevTest@123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def tech_token():
    """Get technician auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TECH_EMAIL,
        "password": TECH_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Technician authentication failed")


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin auth and org ID"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "X-Organization-ID": ORG_ID,
        "Content-Type": "application/json"
    }


@pytest.fixture
def admin_headers_no_org(admin_token):
    """Headers with admin auth but NO org ID"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def tech_headers(tech_token):
    """Headers with technician auth and org ID"""
    return {
        "Authorization": f"Bearer {tech_token}",
        "X-Organization-ID": ORG_ID,
        "Content-Type": "application/json"
    }


class TestOrganizationContext:
    """Test organization context initialization"""
    
    def test_org_endpoint_returns_org_info(self, admin_token):
        """Test /api/org endpoint returns organization info"""
        response = requests.get(f"{BASE_URL}/api/org", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "organization_id" in data
        assert data["organization_id"] == ORG_ID
        assert data["name"] == "Battwheels Garages"
        print(f"✓ Organization context: {data['organization_id']}")
    
    def test_org_endpoint_for_technician(self, tech_token):
        """Test /api/org endpoint works for technician"""
        response = requests.get(f"{BASE_URL}/api/org", headers={
            "Authorization": f"Bearer {tech_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "organization_id" in data
        print(f"✓ Technician org context: {data['organization_id']}")


class TestFinancialSummaryWithOrgId:
    """Test financial summary endpoint WITH organization_id"""
    
    def test_summary_with_org_returns_data(self, admin_headers):
        """Summary with org_id should return actual financial data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/summary", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        
        # Key assertion: Total receivables should be ~₹33L, not ₹0
        receivables = data["summary"]["receivables"]["total"]
        payables = data["summary"]["payables"]["total"]
        
        assert receivables > 0, f"Receivables should not be ₹0, got: {receivables}"
        assert receivables >= 3300000, f"Receivables should be ~₹33L, got: {receivables}"
        assert payables > 0, f"Payables should not be ₹0, got: {payables}"
        assert payables >= 320000, f"Payables should be ~₹3.2L, got: {payables}"
        
        print(f"✓ Total Receivables: ₹{receivables:,.2f}")
        print(f"✓ Total Payables: ₹{payables:,.2f}")
    
    def test_summary_has_correct_structure(self, admin_headers):
        """Verify summary response structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/summary", headers=admin_headers)
        data = response.json()
        
        # Receivables structure
        recv = data["summary"]["receivables"]
        assert "total" in recv
        assert "current" in recv
        assert "overdue" in recv
        assert "invoice_count" in recv
        
        # Payables structure
        pay = data["summary"]["payables"]
        assert "total" in pay
        assert "current" in pay
        assert "overdue" in pay
        assert "bill_count" in pay
        
        print(f"✓ Summary structure verified")


class TestFinancialSummaryWithoutOrgId:
    """Test financial summary endpoint WITHOUT organization_id - graceful degradation"""
    
    def test_summary_without_org_returns_empty(self, admin_headers_no_org):
        """Summary without org_id should return graceful empty response"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/summary", headers=admin_headers_no_org)
        
        # Should NOT return 400 error - graceful degradation
        assert response.status_code == 200
        data = response.json()
        
        # Should have org_missing flag
        assert data["summary"].get("org_missing") == True
        
        # Should return zeros (not errors)
        assert data["summary"]["receivables"]["total"] == 0
        assert data["summary"]["payables"]["total"] == 0
        
        print(f"✓ Graceful empty response when org missing")


class TestCashFlowWithOrgId:
    """Test cash flow endpoint WITH organization_id"""
    
    def test_cash_flow_returns_monthly_data(self, admin_headers):
        """Cash flow should return monthly data with org_id"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/cash-flow?period=fiscal_year", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        cash_flow = data.get("cash_flow", {})
        monthly_data = cash_flow.get("monthly_data", [])
        
        # Should have monthly data for fiscal year
        assert len(monthly_data) > 0, "Monthly data should not be empty"
        
        # Check first month has required fields
        if monthly_data:
            month = monthly_data[0]
            assert "month" in month
            assert "incoming" in month
            assert "outgoing" in month
            assert "running_balance" in month
        
        total_incoming = cash_flow.get("total_incoming", 0)
        total_outgoing = cash_flow.get("total_outgoing", 0)
        
        print(f"✓ Cash Flow: Incoming ₹{total_incoming:,.2f}, Outgoing ₹{total_outgoing:,.2f}")
        print(f"✓ Monthly data points: {len(monthly_data)}")
    
    def test_cash_flow_without_org_returns_empty(self, admin_headers_no_org):
        """Cash flow without org_id should return empty gracefully"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/cash-flow?period=fiscal_year", headers=admin_headers_no_org)
        
        assert response.status_code == 200
        data = response.json()
        
        cash_flow = data.get("cash_flow", {})
        assert cash_flow.get("org_missing") == True
        assert cash_flow.get("total_incoming") == 0
        assert len(cash_flow.get("monthly_data", [])) == 0
        
        print(f"✓ Cash flow graceful empty response")


class TestIncomeExpenseWithOrgId:
    """Test income/expense endpoint"""
    
    def test_income_expense_returns_data(self, admin_headers):
        """Income/expense should return data with org_id"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/income-expense?period=fiscal_year&method=accrual", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        ie = data.get("income_expense", {})
        assert "total_income" in ie
        assert "total_expense" in ie
        assert "monthly_data" in ie
        
        print(f"✓ Income: ₹{ie['total_income']:,.2f}, Expense: ₹{ie['total_expense']:,.2f}")


class TestTopExpensesWithOrgId:
    """Test top expenses endpoint"""
    
    def test_top_expenses_returns_categories(self, admin_headers):
        """Top expenses should return category breakdown"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/top-expenses?period=fiscal_year", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        expenses = data.get("top_expenses", {})
        categories = expenses.get("categories", [])
        
        # Should have categories or be empty if no expenses
        assert isinstance(categories, list)
        
        print(f"✓ Top expense categories: {len(categories)}")


class TestProjectsWatchlistWithOrgId:
    """Test projects watchlist endpoint"""
    
    def test_projects_returns_tickets(self, admin_headers):
        """Projects watchlist should return active tickets"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/projects-watchlist", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        projects = data.get("projects", [])
        
        # Should return list (may be empty if no active tickets)
        assert isinstance(projects, list)
        
        print(f"✓ Active projects/tickets: {len(projects)}")


class TestQuickStatsWithOrgId:
    """Test quick stats endpoint"""
    
    def test_quick_stats_returns_counts(self, admin_headers):
        """Quick stats should return this month's counts"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/quick-stats", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        stats = data.get("quick_stats", {})
        assert "invoices_this_month" in stats
        assert "active_customers" in stats
        assert "month" in stats
        
        print(f"✓ Invoices this month: {stats['invoices_this_month']}")
        print(f"✓ Active customers: {stats['active_customers']}")


class TestTicketsWithOrgId:
    """Test tickets endpoint with organization_id filtering"""
    
    def test_tickets_filtered_by_org(self, admin_headers):
        """Tickets should be filtered by organization_id"""
        response = requests.get(f"{BASE_URL}/api/tickets?limit=10", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        tickets = data.get("tickets", [])
        
        # All tickets should have the correct organization_id
        for ticket in tickets:
            if ticket.get("organization_id"):
                assert ticket["organization_id"] == ORG_ID, f"Ticket {ticket['ticket_id']} has wrong org_id"
        
        print(f"✓ Tickets returned: {len(tickets)}")
    
    def test_technician_sees_tickets(self, tech_headers):
        """Technician should see their assigned tickets"""
        response = requests.get(f"{BASE_URL}/api/tickets?limit=10", headers=tech_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        tickets = data.get("tickets", [])
        print(f"✓ Technician tickets: {len(tickets)}")


class TestBankAccountsWithOrgId:
    """Test bank accounts endpoint"""
    
    def test_bank_accounts_returns_data(self, admin_headers):
        """Bank accounts should return account list"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/bank-accounts", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        accounts = data.get("bank_accounts", {})
        assert "accounts" in accounts
        assert isinstance(accounts["accounts"], list)
        
        print(f"✓ Bank accounts: {len(accounts['accounts'])}")


class TestTicketCreationWithOrgId:
    """Test ticket creation sets organization_id"""
    
    def test_create_ticket_has_org_id(self, admin_headers):
        """Creating a ticket should automatically set organization_id"""
        # Create a test ticket
        ticket_data = {
            "title": "TEST_DataConsistencyAudit - OrgId Test",
            "description": "Testing that tickets get organization_id set",
            "priority": "low",
            "category": "service"
        }
        
        response = requests.post(f"{BASE_URL}/api/tickets", json=ticket_data, headers=admin_headers)
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        # Verify organization_id is set
        assert data.get("organization_id") == ORG_ID, "Ticket should have organization_id set"
        
        print(f"✓ Ticket created with org_id: {data.get('organization_id')}")
        
        return data.get("ticket_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
