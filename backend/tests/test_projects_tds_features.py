"""
Battwheels OS - Projects & TDS Features Test Suite
Testing the 4 major features:
1. TDS Calculation Engine with Mark TDS Deposited modal, Form 16 API, CSV export
2. Projects Module Backend with invoice generation, expense approval
3. Projects Module - time log marking as invoiced
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test IDs from agent context
TEST_PROJECT_ID = "proj_060e595d2008"
TEST_EMPLOYEE_ID = "emp_7e79d8916b6b"

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_login_success(self):
        """Test login with admin credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data, "No token in response"
        print(f"Login successful, token received")
        return data.get("token") or data.get("access_token")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "admin"
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("token") or data.get("access_token")
        print(f"Auth token obtained successfully")
        return token
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_session(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


# ==================== TDS MODULE TESTS ====================

class TestTDSModule:
    """TDS Calculation Engine tests"""
    
    def test_tds_summary_endpoint(self, authenticated_session):
        """Test TDS summary endpoint - GET /api/hr/payroll/tds-summary"""
        response = authenticated_session.get(f"{BASE_URL}/api/hr/payroll/tds-summary", params={
            "month": 12,
            "year": 2025
        })
        assert response.status_code == 200, f"TDS summary failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"TDS summary error: {data}"
        assert "employees" in data, "Missing employees in TDS summary"
        assert "total_tds_this_month" in data, "Missing total_tds_this_month"
        assert "financial_year" in data, "Missing financial_year"
        print(f"TDS Summary: {len(data['employees'])} employees, total TDS: ₹{data['total_tds_this_month']}")
    
    def test_tds_calculate_for_employee(self, authenticated_session):
        """Test TDS calculation for specific employee"""
        response = authenticated_session.get(f"{BASE_URL}/api/hr/tds/calculate/{TEST_EMPLOYEE_ID}", params={
            "month": 12,
            "year": 2025
        })
        # May fail if employee not found, but endpoint should work
        if response.status_code == 404:
            pytest.skip(f"Employee {TEST_EMPLOYEE_ID} not found, skipping")
        assert response.status_code == 200, f"TDS calc failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"TDS calc error: {data}"
        assert "monthly_tds" in data or "annual_tax_liability" in data, "Missing TDS data"
        print(f"TDS calculated for employee: {data.get('employee_name', TEST_EMPLOYEE_ID)}")
    
    def test_tds_export_csv(self, authenticated_session):
        """Test TDS CSV export - GET /api/hr/payroll/tds/export"""
        response = authenticated_session.get(f"{BASE_URL}/api/hr/payroll/tds/export", params={
            "month": 12,
            "year": 2025
        })
        assert response.status_code == 200, f"TDS export failed: {response.text}"
        # Check it's a CSV response
        content_type = response.headers.get("Content-Type", "")
        assert "text/csv" in content_type, f"Expected CSV, got: {content_type}"
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition, "Missing attachment header"
        # Verify CSV content has data
        csv_content = response.text
        assert "Employee Name" in csv_content, "CSV missing header row"
        lines = csv_content.strip().split("\n")
        assert len(lines) >= 1, "CSV has no data rows"
        print(f"TDS CSV export successful, {len(lines)} lines")
    
    def test_mark_tds_deposited(self, authenticated_session):
        """Test Mark TDS Deposited - POST /api/hr/payroll/tds/mark-deposited"""
        import uuid
        test_challan = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        
        payload = {
            "month": 12,
            "year": 2025,
            "challan_number": test_challan,
            "bsr_code": "0012345",
            "deposit_date": "2025-01-07",
            "amount": 5000.00,
            "payment_mode": "net_banking"
        }
        
        response = authenticated_session.post(f"{BASE_URL}/api/hr/payroll/tds/mark-deposited", json=payload)
        assert response.status_code == 200, f"Mark TDS deposited failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Mark TDS error: {data}"
        assert "challan" in data, "Missing challan in response"
        assert "tds_summary" in data, "Missing tds_summary in response"
        
        # Verify challan was created
        assert data["challan"]["challan_number"] == test_challan
        assert data["challan"]["status"] == "DEPOSITED"
        print(f"TDS marked as deposited: Challan {test_challan}")
    
    def test_mark_tds_deposited_duplicate_challan(self, authenticated_session):
        """Test duplicate challan validation"""
        # First create a challan
        import uuid
        test_challan = f"DUP_{uuid.uuid4().hex[:8].upper()}"
        
        payload = {
            "month": 11,
            "year": 2025,
            "challan_number": test_challan,
            "bsr_code": "0012345",
            "deposit_date": "2025-01-05",
            "amount": 3000.00,
            "payment_mode": "net_banking"
        }
        
        # First request should succeed
        response1 = authenticated_session.post(f"{BASE_URL}/api/hr/payroll/tds/mark-deposited", json=payload)
        assert response1.status_code == 200, f"First challan failed: {response1.text}"
        
        # Second request with same challan should fail
        response2 = authenticated_session.post(f"{BASE_URL}/api/hr/payroll/tds/mark-deposited", json=payload)
        assert response2.status_code == 400, f"Duplicate challan should fail: {response2.text}"
        error_data = response2.json()
        assert "duplicate" in error_data.get("detail", "").lower() or "already exists" in error_data.get("detail", "").lower()
        print(f"Duplicate challan validation working correctly")
    
    def test_list_tds_challans(self, authenticated_session):
        """Test list TDS challans endpoint"""
        response = authenticated_session.get(f"{BASE_URL}/api/hr/tds/challans")
        assert response.status_code == 200, f"List challans failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"List challans error: {data}"
        assert "challans" in data, "Missing challans in response"
        print(f"Found {len(data['challans'])} TDS challans")
    
    def test_form16_api(self, authenticated_session):
        """Test Form 16 API - GET /api/hr/payroll/form16/{employee_id}/{fy}"""
        # Test with known employee
        response = authenticated_session.get(f"{BASE_URL}/api/hr/payroll/form16/{TEST_EMPLOYEE_ID}/2025-26")
        
        # May fail if no payroll data, that's ok
        if response.status_code == 404:
            pytest.skip(f"Employee or FY data not found for Form 16")
        
        if response.status_code == 400:
            # Check if it's just "no payroll records"
            data = response.json()
            if "no payroll" in data.get("detail", "").lower():
                pytest.skip("No payroll records for this FY")
        
        assert response.status_code == 200, f"Form 16 failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0 or "employee" in data, f"Form 16 error: {data}"
        print(f"Form 16 data retrieved successfully")


# ==================== PROJECTS MODULE TESTS ====================

class TestProjectsModule:
    """Projects Module tests"""
    
    def test_list_projects(self, authenticated_session):
        """Test list projects endpoint"""
        response = authenticated_session.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200, f"List projects failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"List projects error: {data}"
        assert "projects" in data, "Missing projects in response"
        print(f"Found {len(data['projects'])} projects")
    
    def test_get_project_detail(self, authenticated_session):
        """Test get project detail - GET /api/projects/{project_id}"""
        response = authenticated_session.get(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Get project failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Get project error: {data}"
        assert "project" in data, "Missing project in response"
        
        project = data["project"]
        assert project.get("project_id") == TEST_PROJECT_ID
        print(f"Project: {project.get('name')}, Status: {project.get('status')}")
    
    def test_project_tasks(self, authenticated_session):
        """Test project tasks endpoint"""
        response = authenticated_session.get(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/tasks")
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Get tasks failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Get tasks error: {data}"
        assert "tasks" in data, "Missing tasks in response"
        print(f"Found {len(data['tasks'])} tasks")
    
    def test_project_time_logs(self, authenticated_session):
        """Test project time logs endpoint"""
        response = authenticated_session.get(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/time-logs")
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Get time logs failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Get time logs error: {data}"
        assert "time_logs" in data, "Missing time_logs in response"
        assert "total_hours" in data, "Missing total_hours in response"
        print(f"Found {len(data['time_logs'])} time logs, {data['total_hours']} total hours")
    
    def test_project_expenses(self, authenticated_session):
        """Test project expenses endpoint"""
        response = authenticated_session.get(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/expenses")
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Get expenses failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Get expenses error: {data}"
        assert "expenses" in data, "Missing expenses in response"
        print(f"Found {len(data['expenses'])} expenses, total: ₹{data.get('total_amount', 0)}")
    
    def test_project_profitability(self, authenticated_session):
        """Test project profitability endpoint"""
        response = authenticated_session.get(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/profitability")
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Get profitability failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Get profitability error: {data}"
        assert "profitability" in data, "Missing profitability in response"
        
        profit = data["profitability"]
        assert "revenue" in profit, "Missing revenue"
        assert "gross_profit" in profit, "Missing gross_profit"
        print(f"Project Revenue: ₹{profit['revenue']}, Profit: ₹{profit['gross_profit']}, Margin: {profit.get('margin_pct', 0)}%")
    
    def test_project_dashboard_stats(self, authenticated_session):
        """Test project dashboard stats"""
        response = authenticated_session.get(f"{BASE_URL}/api/projects/stats/dashboard")
        assert response.status_code == 200, f"Get dashboard stats failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Dashboard stats error: {data}"
        assert "stats" in data, "Missing stats in response"
        
        stats = data["stats"]
        print(f"Dashboard: {stats.get('total_projects', 0)} total, {stats.get('active_projects', 0)} active")


class TestProjectExpenseApproval:
    """Test expense approval workflow"""
    
    def test_add_expense_to_project(self, authenticated_session):
        """Test adding expense to project (pending status)"""
        import uuid
        
        payload = {
            "amount": 1500.00,
            "description": f"TEST_Expense_{uuid.uuid4().hex[:6]}",
            "expense_date": "2025-01-10",
            "category": "materials"
        }
        
        response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/expenses", json=payload)
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Add expense failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Add expense error: {data}"
        assert "expense" in data, "Missing expense in response"
        
        expense = data["expense"]
        assert expense.get("status") == "PENDING", f"Expense should be PENDING, got: {expense.get('status')}"
        print(f"Created expense: {expense.get('project_expense_id')}, status: PENDING")
        return expense.get("project_expense_id")
    
    def test_approve_expense(self, authenticated_session):
        """Test expense approval - POST /api/projects/{id}/expenses/{expense_id}/approve"""
        import uuid
        
        # First create an expense
        payload = {
            "amount": 2000.00,
            "description": f"TEST_Approve_{uuid.uuid4().hex[:6]}",
            "expense_date": "2025-01-10",
            "category": "equipment"
        }
        
        create_response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/expenses", json=payload)
        
        if create_response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert create_response.status_code == 200, f"Create expense failed: {create_response.text}"
        expense_id = create_response.json()["expense"]["project_expense_id"]
        
        # Now approve it
        approve_response = authenticated_session.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/expenses/{expense_id}/approve",
            json={"approved": True}
        )
        
        assert approve_response.status_code == 200, f"Approve expense failed: {approve_response.text}"
        data = approve_response.json()
        assert data.get("code") == 0, f"Approve error: {data}"
        assert data["expense"]["status"] == "APPROVED", f"Expense not approved: {data['expense']['status']}"
        print(f"Expense {expense_id} approved successfully")
    
    def test_reject_expense(self, authenticated_session):
        """Test expense rejection"""
        import uuid
        
        # First create an expense
        payload = {
            "amount": 500.00,
            "description": f"TEST_Reject_{uuid.uuid4().hex[:6]}",
            "expense_date": "2025-01-10",
            "category": "travel"
        }
        
        create_response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/expenses", json=payload)
        
        if create_response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert create_response.status_code == 200
        expense_id = create_response.json()["expense"]["project_expense_id"]
        
        # Now reject it
        reject_response = authenticated_session.post(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/expenses/{expense_id}/approve",
            json={"approved": False}
        )
        
        assert reject_response.status_code == 200, f"Reject expense failed: {reject_response.text}"
        data = reject_response.json()
        assert data["expense"]["status"] == "REJECTED"
        print(f"Expense {expense_id} rejected successfully")


class TestProjectInvoiceGeneration:
    """Test project invoice generation"""
    
    def test_generate_invoice_from_project(self, authenticated_session):
        """Test invoice generation - POST /api/projects/{id}/invoice"""
        payload = {
            "billing_period_from": "2025-01-01",
            "billing_period_to": "2025-01-31",
            "include_expenses": True,
            "line_item_grouping": "BY_TASK",
            "notes": "Test invoice generation"
        }
        
        response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/invoice", json=payload)
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        if response.status_code == 400:
            data = response.json()
            # If no time logs, that's expected
            if "no uninvoiced" in data.get("detail", "").lower() or "no time logs" in data.get("detail", "").lower():
                print("No uninvoiced time logs in period - expected behavior")
                return
        
        assert response.status_code == 200, f"Generate invoice failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Generate invoice error: {data}"
        
        if data.get("invoice_id"):
            print(f"Invoice created: {data['invoice_number']}, Total: ₹{data['sub_total']}")
            assert "line_items" in data, "Missing line_items"
            assert "billing_period" in data, "Missing billing_period"
        else:
            print("Invoice data generated but no invoice created (may have no line items)")
    
    def test_invoice_grouping_by_employee(self, authenticated_session):
        """Test invoice generation grouped by employee"""
        payload = {
            "billing_period_from": "2024-12-01",
            "billing_period_to": "2024-12-31",
            "include_expenses": False,
            "line_item_grouping": "BY_EMPLOYEE",
            "notes": "Test - grouped by employee"
        }
        
        response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/invoice", json=payload)
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        # Even if 400 (no logs), endpoint should respond correctly
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"Invoice BY_EMPLOYEE grouping: {response.status_code}")
    
    def test_invoice_grouping_by_date(self, authenticated_session):
        """Test invoice generation grouped by date"""
        payload = {
            "billing_period_from": "2024-11-01",
            "billing_period_to": "2024-11-30",
            "include_expenses": True,
            "line_item_grouping": "BY_DATE",
            "notes": "Test - grouped by date"
        }
        
        response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/invoice", json=payload)
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"Invoice BY_DATE grouping: {response.status_code}")


class TestProjectTaskManagement:
    """Test project task management"""
    
    def test_create_task(self, authenticated_session):
        """Test creating a task for a project"""
        import uuid
        
        payload = {
            "title": f"TEST_Task_{uuid.uuid4().hex[:6]}",
            "description": "Automated test task",
            "status": "TODO",
            "priority": "MEDIUM",
            "estimated_hours": 4.0
        }
        
        response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/tasks", json=payload)
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Create task failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Create task error: {data}"
        assert "task" in data, "Missing task in response"
        print(f"Created task: {data['task']['task_id']}")
        return data["task"]["task_id"]
    
    def test_update_task_status(self, authenticated_session):
        """Test updating task status"""
        import uuid
        
        # Create a task first
        create_payload = {
            "title": f"TEST_Update_{uuid.uuid4().hex[:6]}",
            "description": "Task to update",
            "status": "TODO",
            "priority": "HIGH"
        }
        
        create_response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/tasks", json=create_payload)
        
        if create_response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert create_response.status_code == 200
        task_id = create_response.json()["task"]["task_id"]
        
        # Update status
        update_response = authenticated_session.put(
            f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/tasks/{task_id}",
            json={"status": "IN_PROGRESS"}
        )
        
        assert update_response.status_code == 200, f"Update task failed: {update_response.text}"
        data = update_response.json()
        assert data["task"]["status"] == "IN_PROGRESS"
        print(f"Task {task_id} status updated to IN_PROGRESS")


class TestTimeLogging:
    """Test time logging functionality"""
    
    def test_log_time(self, authenticated_session):
        """Test logging time against a project"""
        import uuid
        
        payload = {
            "hours_logged": 2.5,
            "description": f"TEST_TimeLog_{uuid.uuid4().hex[:6]}",
            "log_date": "2025-01-10"
        }
        
        response = authenticated_session.post(f"{BASE_URL}/api/projects/{TEST_PROJECT_ID}/time-log", json=payload)
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Log time failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Log time error: {data}"
        assert "time_log" in data, "Missing time_log in response"
        print(f"Logged {data['time_log']['hours_logged']} hours")


class TestEmployeeTaxConfig:
    """Test employee tax configuration"""
    
    def test_get_employee_tax_config(self, authenticated_session):
        """Test getting employee tax config"""
        response = authenticated_session.get(f"{BASE_URL}/api/hr/employees/{TEST_EMPLOYEE_ID}/tax-config")
        
        if response.status_code == 404:
            pytest.skip(f"Employee {TEST_EMPLOYEE_ID} not found")
        
        assert response.status_code == 200, f"Get tax config failed: {response.text}"
        data = response.json()
        assert "tax_config" in data, "Missing tax_config"
        print(f"Tax regime: {data['tax_config'].get('tax_regime', 'new')}")
    
    def test_update_employee_tax_config(self, authenticated_session):
        """Test updating employee tax config with PAN validation"""
        payload = {
            "pan_number": "ABCDE1234F",
            "tax_regime": "new",
            "declarations": {}
        }
        
        response = authenticated_session.put(
            f"{BASE_URL}/api/hr/employees/{TEST_EMPLOYEE_ID}/tax-config",
            json=payload
        )
        
        if response.status_code == 404:
            pytest.skip(f"Employee {TEST_EMPLOYEE_ID} not found")
        
        assert response.status_code == 200, f"Update tax config failed: {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Update error: {data}"
        print("Tax config updated successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
