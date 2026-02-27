"""
Battwheels OS - Financial Dashboard, Time Tracking & Documents API Tests
Testing new Zoho-style modules
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ORG_ID = "org_71f0df814d6d"

class TestAuthSetup:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping tests")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth and org"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "X-Organization-ID": ORG_ID
        }
    
    def test_login_works(self):
        """Verify login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print(f"✓ Login successful, token obtained")


# ==================== FINANCIAL DASHBOARD API TESTS ====================

class TestFinancialDashboardAPIs:
    """Financial Dashboard endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        token = response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Organization-ID": ORG_ID
        }
    
    def test_financial_summary(self, auth_headers):
        """GET /api/dashboard/financial/summary - returns receivables and payables"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/summary", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got: {data}"
        assert "summary" in data
        
        summary = data["summary"]
        assert "receivables" in summary
        assert "payables" in summary
        
        # Verify receivables structure
        receivables = summary["receivables"]
        assert "total" in receivables
        assert "current" in receivables
        assert "overdue" in receivables
        
        # Verify payables structure  
        payables = summary["payables"]
        assert "total" in payables
        
        print(f"✓ Financial summary: Receivables={receivables['total']}, Payables={payables['total']}")
    
    def test_cash_flow(self, auth_headers):
        """GET /api/dashboard/financial/cash-flow - returns monthly cash flow"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/cash-flow", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "cash_flow" in data
        
        cash_flow = data["cash_flow"]
        assert "monthly_data" in cash_flow
        assert "total_incoming" in cash_flow
        assert "total_outgoing" in cash_flow
        assert "closing_balance" in cash_flow
        
        print(f"✓ Cash flow: Incoming={cash_flow['total_incoming']}, Outgoing={cash_flow['total_outgoing']}")
    
    def test_cash_flow_with_period(self, auth_headers):
        """GET /api/dashboard/financial/cash-flow with different periods"""
        periods = ["fiscal_year", "last_12_months", "last_6_months"]
        for period in periods:
            response = requests.get(
                f"{BASE_URL}/api/dashboard/financial/cash-flow?period={period}", 
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("code") == 0
            assert data["cash_flow"]["period"] == period
        print(f"✓ Cash flow periods tested: {periods}")
    
    def test_income_expense(self, auth_headers):
        """GET /api/dashboard/financial/income-expense - returns income/expense breakdown"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/income-expense", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "income_expense" in data
        
        income_expense = data["income_expense"]
        assert "total_income" in income_expense
        assert "total_expense" in income_expense
        assert "net_profit" in income_expense
        assert "monthly_data" in income_expense
        
        print(f"✓ Income/Expense: Income={income_expense['total_income']}, Expense={income_expense['total_expense']}")
    
    def test_income_expense_methods(self, auth_headers):
        """GET /api/dashboard/financial/income-expense with accrual and cash methods"""
        methods = ["accrual", "cash"]
        for method in methods:
            response = requests.get(
                f"{BASE_URL}/api/dashboard/financial/income-expense?method={method}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("code") == 0
            assert data["income_expense"]["method"] == method
        print(f"✓ Income/Expense methods tested: {methods}")
    
    def test_top_expenses(self, auth_headers):
        """GET /api/dashboard/financial/top-expenses - returns expense categories"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/top-expenses", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "top_expenses" in data
        
        top_expenses = data["top_expenses"]
        assert "total" in top_expenses
        assert "categories" in top_expenses
        
        # Categories should be a list
        assert isinstance(top_expenses["categories"], list)
        
        print(f"✓ Top expenses: Total={top_expenses['total']}, Categories={len(top_expenses['categories'])}")
    
    def test_bank_accounts(self, auth_headers):
        """GET /api/dashboard/financial/bank-accounts - returns bank account info"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/bank-accounts", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "bank_accounts" in data
        
        bank_accounts = data["bank_accounts"]
        assert "accounts" in bank_accounts
        assert "total_balance" in bank_accounts
        
        print(f"✓ Bank accounts: Count={len(bank_accounts['accounts'])}, Balance={bank_accounts['total_balance']}")
    
    def test_projects_watchlist(self, auth_headers):
        """GET /api/dashboard/financial/projects-watchlist - returns active projects"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/projects-watchlist", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "projects" in data
        
        print(f"✓ Projects watchlist: Count={len(data['projects'])}")
    
    def test_quick_stats(self, auth_headers):
        """GET /api/dashboard/financial/quick-stats - returns dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/quick-stats", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "quick_stats" in data
        
        stats = data["quick_stats"]
        assert "active_customers" in stats
        assert "total_items" in stats
        
        print(f"✓ Quick stats: Customers={stats['active_customers']}, Items={stats['total_items']}")
    
    def test_financial_summary_requires_org_id(self):
        """Financial summary requires X-Organization-ID header"""
        # Get auth token first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        token = response.json().get("token")
        
        # Call without org ID
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.get(f"{BASE_URL}/api/dashboard/financial/summary", headers=headers)
        assert response.status_code == 400
        print(f"✓ Financial summary correctly requires X-Organization-ID header")


# ==================== TIME TRACKING API TESTS ====================

class TestTimeTrackingAPIs:
    """Time Tracking endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        token = response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Organization-ID": ORG_ID
        }
    
    def test_list_time_entries(self, auth_headers):
        """GET /api/time-tracking/entries - returns time entries list"""
        response = requests.get(f"{BASE_URL}/api/time-tracking/entries", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "entries" in data
        assert "page_context" in data
        
        print(f"✓ Time entries list: Count={len(data['entries'])}")
    
    def test_create_time_entry(self, auth_headers):
        """POST /api/time-tracking/entries - creates new time entry"""
        entry_data = {
            "user_id": "test_user",
            "user_name": "Test Technician",
            "date": "2026-02-19",
            "hours": 2.5,
            "description": "Test time entry for API testing",
            "task_type": "service",
            "billable": True,
            "hourly_rate": 500
        }
        
        response = requests.post(
            f"{BASE_URL}/api/time-tracking/entries",
            json=entry_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "entry" in data
        
        entry = data["entry"]
        assert entry["hours"] == 2.5
        assert entry["task_type"] == "service"
        assert entry["amount"] == 1250  # 2.5 * 500
        
        # Store entry_id for cleanup
        TestTimeTrackingAPIs.created_entry_id = entry["entry_id"]
        
        print(f"✓ Time entry created: ID={entry['entry_id']}, Amount={entry['amount']}")
    
    def test_get_time_entry(self, auth_headers):
        """GET /api/time-tracking/entries/{entry_id} - get specific entry"""
        if not hasattr(TestTimeTrackingAPIs, 'created_entry_id'):
            pytest.skip("No entry created to test")
        
        entry_id = TestTimeTrackingAPIs.created_entry_id
        response = requests.get(f"{BASE_URL}/api/time-tracking/entries/{entry_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert data["entry"]["entry_id"] == entry_id
        
        print(f"✓ Time entry retrieved: ID={entry_id}")
    
    def test_update_time_entry(self, auth_headers):
        """PUT /api/time-tracking/entries/{entry_id} - update time entry"""
        if not hasattr(TestTimeTrackingAPIs, 'created_entry_id'):
            pytest.skip("No entry created to test")
        
        entry_id = TestTimeTrackingAPIs.created_entry_id
        update_data = {
            "hours": 3.0,
            "description": "Updated description"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/time-tracking/entries/{entry_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert data["entry"]["hours"] == 3.0
        
        print(f"✓ Time entry updated: Hours={data['entry']['hours']}")
    
    def test_start_timer(self, auth_headers):
        """POST /api/time-tracking/timer/start - starts a timer"""
        timer_data = {
            "user_id": "test_user",
            "user_name": "Test Technician",
            "description": "Test timer",
            "task_type": "repair",
            "billable": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/time-tracking/timer/start",
            json=timer_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "timer" in data
        assert data["timer"]["status"] == "running"
        
        # Store timer_id for stop test
        TestTimeTrackingAPIs.active_timer_id = data["timer"]["timer_id"]
        
        print(f"✓ Timer started: ID={data['timer']['timer_id']}")
    
    def test_get_active_timers(self, auth_headers):
        """GET /api/time-tracking/timer/active - get active timers"""
        response = requests.get(f"{BASE_URL}/api/time-tracking/timer/active", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "timers" in data
        
        # Should have at least our created timer
        timers = data["timers"]
        print(f"✓ Active timers: Count={len(timers)}")
    
    def test_stop_timer(self, auth_headers):
        """POST /api/time-tracking/timer/stop/{timer_id} - stops timer"""
        if not hasattr(TestTimeTrackingAPIs, 'active_timer_id'):
            pytest.skip("No timer created to test")
        
        timer_id = TestTimeTrackingAPIs.active_timer_id
        response = requests.post(
            f"{BASE_URL}/api/time-tracking/timer/stop/{timer_id}?hourly_rate=500",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "entry" in data
        assert "hours" in data
        
        print(f"✓ Timer stopped: Hours={data['hours']}")
    
    def test_get_unbilled_hours(self, auth_headers):
        """GET /api/time-tracking/unbilled - get unbilled summary"""
        response = requests.get(f"{BASE_URL}/api/time-tracking/unbilled", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "unbilled" in data
        
        unbilled = data["unbilled"]
        assert "total_hours" in unbilled
        assert "total_amount" in unbilled
        
        print(f"✓ Unbilled hours: Total={unbilled['total_hours']}, Amount={unbilled['total_amount']}")
    
    def test_time_summary_report(self, auth_headers):
        """GET /api/time-tracking/reports/summary - get time summary report"""
        response = requests.get(f"{BASE_URL}/api/time-tracking/reports/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "report" in data
        
        report = data["report"]
        assert "totals" in report
        
        print(f"✓ Time summary report: Total hours={report['totals']['total_hours']}")
    
    def test_delete_time_entry(self, auth_headers):
        """DELETE /api/time-tracking/entries/{entry_id} - cleanup test entry"""
        if not hasattr(TestTimeTrackingAPIs, 'created_entry_id'):
            pytest.skip("No entry created to test")
        
        entry_id = TestTimeTrackingAPIs.created_entry_id
        response = requests.delete(f"{BASE_URL}/api/time-tracking/entries/{entry_id}", headers=auth_headers)
        assert response.status_code == 200
        
        print(f"✓ Time entry deleted: ID={entry_id}")


# ==================== DOCUMENTS API TESTS ====================

class TestDocumentsAPIs:
    """Documents Management endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        token = response.json().get("token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Organization-ID": ORG_ID
        }
    
    def test_list_documents(self, auth_headers):
        """GET /api/documents/ - returns documents list"""
        response = requests.get(f"{BASE_URL}/api/documents/", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "documents" in data
        assert "page_context" in data
        
        print(f"✓ Documents list: Count={len(data['documents'])}")
    
    def test_list_folders(self, auth_headers):
        """GET /api/documents/folders - returns folders list"""
        response = requests.get(f"{BASE_URL}/api/documents/folders", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "folders" in data
        
        print(f"✓ Folders list: Count={len(data['folders'])}")
    
    def test_create_folder(self, auth_headers):
        """POST /api/documents/folders - creates new folder"""
        folder_data = {
            "name": "TEST_Folder_API",
            "color": "#10B981"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/documents/folders",
            json=folder_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "folder" in data
        assert data["folder"]["name"] == "TEST_Folder_API"
        
        # Store folder_id for cleanup
        TestDocumentsAPIs.created_folder_id = data["folder"]["folder_id"]
        
        print(f"✓ Folder created: ID={data['folder']['folder_id']}")
    
    def test_document_stats_summary(self, auth_headers):
        """GET /api/documents/stats/summary - returns document stats"""
        response = requests.get(f"{BASE_URL}/api/documents/stats/summary", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "stats" in data
        
        stats = data["stats"]
        assert "total_documents" in stats
        assert "total_folders" in stats
        assert "total_size_mb" in stats
        
        print(f"✓ Document stats: Docs={stats['total_documents']}, Folders={stats['total_folders']}, Size={stats['total_size_mb']}MB")
    
    def test_create_document(self, auth_headers):
        """POST /api/documents/ - creates new document"""
        doc_data = {
            "name": "TEST_Document_API",
            "description": "Test document created via API",
            "document_type": "receipt",
            "tags": ["test", "api"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/documents/",
            json=doc_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "document" in data
        assert data["document"]["name"] == "TEST_Document_API"
        
        # Store document_id for cleanup
        TestDocumentsAPIs.created_doc_id = data["document"]["document_id"]
        
        print(f"✓ Document created: ID={data['document']['document_id']}")
    
    def test_get_document(self, auth_headers):
        """GET /api/documents/{document_id} - get specific document"""
        if not hasattr(TestDocumentsAPIs, 'created_doc_id'):
            pytest.skip("No document created to test")
        
        doc_id = TestDocumentsAPIs.created_doc_id
        response = requests.get(f"{BASE_URL}/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert data["document"]["document_id"] == doc_id
        
        print(f"✓ Document retrieved: ID={doc_id}")
    
    def test_update_document(self, auth_headers):
        """PUT /api/documents/{document_id} - update document"""
        if not hasattr(TestDocumentsAPIs, 'created_doc_id'):
            pytest.skip("No document created to test")
        
        doc_id = TestDocumentsAPIs.created_doc_id
        update_data = {
            "description": "Updated description via API",
            "tags": ["test", "api", "updated"]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/documents/{doc_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "Updated" in data["document"]["description"]
        
        print(f"✓ Document updated: ID={doc_id}")
    
    def test_list_tags(self, auth_headers):
        """GET /api/documents/tags/all - returns all tags"""
        response = requests.get(f"{BASE_URL}/api/documents/tags/all", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "tags" in data
        
        print(f"✓ Tags list: Count={len(data['tags'])}")
    
    def test_delete_document(self, auth_headers):
        """DELETE /api/documents/{document_id} - cleanup test document"""
        if not hasattr(TestDocumentsAPIs, 'created_doc_id'):
            pytest.skip("No document created to test")
        
        doc_id = TestDocumentsAPIs.created_doc_id
        response = requests.delete(f"{BASE_URL}/api/documents/{doc_id}", headers=auth_headers)
        assert response.status_code == 200
        
        print(f"✓ Document deleted: ID={doc_id}")
    
    def test_delete_folder(self, auth_headers):
        """DELETE /api/documents/folders/{folder_id} - cleanup test folder"""
        if not hasattr(TestDocumentsAPIs, 'created_folder_id'):
            pytest.skip("No folder created to test")
        
        folder_id = TestDocumentsAPIs.created_folder_id
        response = requests.delete(f"{BASE_URL}/api/documents/folders/{folder_id}", headers=auth_headers)
        assert response.status_code == 200
        
        print(f"✓ Folder deleted: ID={folder_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
