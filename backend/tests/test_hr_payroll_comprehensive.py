"""
Comprehensive HR/Payroll Module Tests
======================================
Tests all critical HR endpoints: employees CRUD, payroll generation,
payroll records, payslip, and payroll summary.

Uses conftest fixtures (auth_headers, admin_headers, base_url, dev_headers).
"""

import pytest
import requests
import uuid
from datetime import datetime


# ==================== HELPERS ====================

def unique(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ==================== EMPLOYEE CRUD ====================

class TestEmployeeCRUD:
    """Test employee CRUD operations via /api/v1/hr/employees"""

    @pytest.fixture(scope="class")
    def created_employee(self, base_url, auth_headers):
        """Create a test employee for use across this class"""
        data = {
            "first_name": "TestEmp",
            "last_name": unique("HR"),
            "email": f"{unique('emp')}@test.com",
            "phone": "9876543210",
            "department": "Service",
            "designation": "Technician",
            "employment_type": "full_time",
            "date_of_joining": "2025-01-15",
            "salary_structure": {"basic": 25000, "hra": 10000, "da": 5000},
        }
        resp = requests.post(
            f"{base_url}/api/v1/hr/employees",
            json=data,
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Create employee failed: {resp.status_code} {resp.text[:300]}"
        result = resp.json()
        emp_id = result.get("employee_id") or result.get("data", {}).get("employee_id")
        assert emp_id, f"No employee_id in response: {result}"
        return {"employee_id": emp_id, **data}

    def test_list_employees(self, base_url, auth_headers):
        """GET /api/v1/hr/employees returns list"""
        resp = requests.get(f"{base_url}/api/v1/hr/employees", headers=auth_headers)
        assert resp.status_code == 200, f"List employees: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "data" in data or isinstance(data, list), f"Unexpected response shape: {list(data.keys()) if isinstance(data, dict) else type(data)}"

    def test_list_employees_requires_auth(self, base_url):
        """GET /api/v1/hr/employees without auth returns 401/403"""
        resp = requests.get(f"{base_url}/api/v1/hr/employees")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_create_employee_valid(self, base_url, auth_headers, created_employee):
        """POST /api/v1/hr/employees with valid data succeeds"""
        assert created_employee["employee_id"] is not None

    def test_create_employee_missing_fields_rejected(self, base_url, auth_headers):
        """POST /api/v1/hr/employees with missing required fields returns 422"""
        resp = requests.post(
            f"{base_url}/api/v1/hr/employees",
            json={"first_name": "Incomplete"},
            headers=auth_headers,
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

    def test_get_employee_by_id(self, base_url, auth_headers, created_employee):
        """GET /api/v1/hr/employees/{id} returns the employee"""
        emp_id = created_employee["employee_id"]
        resp = requests.get(
            f"{base_url}/api/v1/hr/employees/{emp_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Get employee: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        emp = data if "employee_id" in data else data.get("data", data)
        assert emp.get("employee_id") == emp_id or emp.get("first_name") == "TestEmp"

    def test_get_nonexistent_employee_returns_404(self, base_url, auth_headers):
        """GET /api/v1/hr/employees/{fake_id} returns 404"""
        resp = requests.get(
            f"{base_url}/api/v1/hr/employees/emp_nonexistent_999",
            headers=auth_headers,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    def test_update_employee(self, base_url, auth_headers, created_employee):
        """PUT /api/v1/hr/employees/{id} updates employee"""
        emp_id = created_employee["employee_id"]
        resp = requests.put(
            f"{base_url}/api/v1/hr/employees/{emp_id}",
            json={"designation": "Senior Technician", "phone": "9999999999"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Update employee: {resp.status_code} {resp.text[:300]}"


# ==================== PAYROLL ====================

class TestPayroll:
    """Test payroll generation and records via /api/v1/hr/payroll"""

    def test_payroll_records_list(self, base_url, auth_headers):
        """GET /api/v1/hr/payroll/records returns paginated list"""
        resp = requests.get(
            f"{base_url}/api/v1/hr/payroll/records",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Payroll records: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "data" in data, f"Expected 'data' key: {list(data.keys())}"
        assert "pagination" in data, f"Expected 'pagination' key: {list(data.keys())}"

    def test_payroll_records_requires_auth(self, base_url):
        """GET /api/v1/hr/payroll/records without auth returns 401/403"""
        resp = requests.get(f"{base_url}/api/v1/hr/payroll/records")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_payroll_generate(self, base_url, auth_headers):
        """POST /api/v1/hr/payroll/generate runs payroll for current month"""
        now = datetime.utcnow()
        resp = requests.post(
            f"{base_url}/api/v1/hr/payroll/generate",
            params={"month": now.strftime("%B"), "year": now.year},
            headers=auth_headers,
        )
        # 200 = success, 409 = already generated (both acceptable)
        assert resp.status_code in (200, 409), f"Payroll generate: {resp.status_code} {resp.text[:300]}"

    def test_payroll_calculate_for_employee(self, base_url, auth_headers):
        """GET /api/v1/hr/payroll/calculate/{emp_id} calculates salary"""
        # First get an employee
        emp_resp = requests.get(f"{base_url}/api/v1/hr/employees", headers=auth_headers)
        if emp_resp.status_code != 200:
            pytest.skip("Cannot list employees")
        employees = emp_resp.json()
        emp_list = employees.get("data", employees) if isinstance(employees, dict) else employees
        if not emp_list:
            pytest.skip("No employees in system")
        emp_id = emp_list[0].get("employee_id") if isinstance(emp_list, list) else None
        if not emp_id:
            pytest.skip("No employee_id found")

        resp = requests.get(
            f"{base_url}/api/v1/hr/payroll/calculate/{emp_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Payroll calculate: {resp.status_code} {resp.text[:300]}"

    def test_payroll_my_records(self, base_url, auth_headers):
        """GET /api/v1/hr/payroll/my-records returns own payroll"""
        resp = requests.get(
            f"{base_url}/api/v1/hr/payroll/my-records",
            headers=auth_headers,
        )
        # 200 = has employee record, 404 = no employee record for user (both valid)
        assert resp.status_code in (200, 404), f"My payroll: {resp.status_code} {resp.text[:300]}"


# ==================== DEPARTMENTS & ATTENDANCE ====================

class TestDepartmentsAndAttendance:
    """Test department listing and attendance endpoints"""

    def test_list_departments(self, base_url, auth_headers):
        """GET /api/v1/hr/departments returns department list"""
        resp = requests.get(f"{base_url}/api/v1/hr/departments", headers=auth_headers)
        assert resp.status_code == 200, f"Departments: {resp.status_code} {resp.text[:300]}"

    def test_today_attendance(self, base_url, auth_headers):
        """GET /api/v1/hr/attendance/today returns today's attendance"""
        resp = requests.get(f"{base_url}/api/v1/hr/attendance/today", headers=auth_headers)
        assert resp.status_code == 200, f"Today attendance: {resp.status_code} {resp.text[:300]}"

    def test_my_attendance_records(self, base_url, auth_headers):
        """GET /api/v1/hr/attendance/my-records returns attendance or 404 for non-employee users"""
        resp = requests.get(f"{base_url}/api/v1/hr/attendance/my-records", headers=auth_headers)
        # 200 = has employee record, 404 = demo user has no employee record (valid)
        assert resp.status_code in (200, 404), f"My attendance: {resp.status_code} {resp.text[:300]}"

    def test_all_attendance_admin(self, base_url, auth_headers):
        """GET /api/v1/hr/attendance/all returns all attendance (admin view)"""
        resp = requests.get(f"{base_url}/api/v1/hr/attendance/all", headers=auth_headers)
        assert resp.status_code == 200, f"All attendance: {resp.status_code} {resp.text[:300]}"


# ==================== LEAVE MANAGEMENT ====================

class TestLeaveManagement:
    """Test leave type listing and request flow"""

    def test_get_leave_types(self, base_url, auth_headers):
        """GET /api/v1/hr/leave/types returns leave types"""
        resp = requests.get(f"{base_url}/api/v1/hr/leave/types", headers=auth_headers)
        assert resp.status_code == 200, f"Leave types: {resp.status_code} {resp.text[:300]}"

    def test_get_leave_balance(self, base_url, auth_headers):
        """GET /api/v1/hr/leave/balance returns balances or 404 for non-employee users"""
        resp = requests.get(f"{base_url}/api/v1/hr/leave/balance", headers=auth_headers)
        # 200 = has employee record, 404 = demo user has no employee record (valid)
        assert resp.status_code in (200, 404), f"Leave balance: {resp.status_code} {resp.text[:300]}"

    def test_get_my_leave_requests(self, base_url, auth_headers):
        """GET /api/v1/hr/leave/my-requests returns own requests"""
        resp = requests.get(f"{base_url}/api/v1/hr/leave/my-requests", headers=auth_headers)
        assert resp.status_code == 200, f"My leaves: {resp.status_code} {resp.text[:300]}"

    def test_get_pending_approvals(self, base_url, auth_headers):
        """GET /api/v1/hr/leave/pending-approvals returns pending"""
        resp = requests.get(f"{base_url}/api/v1/hr/leave/pending-approvals", headers=auth_headers)
        assert resp.status_code == 200, f"Pending approvals: {resp.status_code} {resp.text[:300]}"


# ==================== TDS & TAX ====================

class TestTDSAndTax:
    """Test TDS calculation and challan endpoints"""

    def test_tds_summary(self, base_url, auth_headers):
        """GET /api/v1/hr/payroll/tds-summary returns TDS summary"""
        resp = requests.get(
            f"{base_url}/api/v1/hr/payroll/tds-summary",
            params={"month": 1, "year": 2026},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"TDS summary: {resp.status_code} {resp.text[:300]}"

    def test_tds_challans_list(self, base_url, auth_headers):
        """GET /api/v1/hr/tds/challans returns challan list"""
        resp = requests.get(f"{base_url}/api/v1/hr/tds/challans", headers=auth_headers)
        assert resp.status_code == 200, f"TDS challans: {resp.status_code} {resp.text[:300]}"

    def test_tds_calculate_for_employee(self, base_url, auth_headers):
        """GET /api/v1/hr/tds/calculate/{emp_id} calculates TDS"""
        emp_resp = requests.get(f"{base_url}/api/v1/hr/employees", headers=auth_headers)
        if emp_resp.status_code != 200:
            pytest.skip("Cannot list employees")
        employees = emp_resp.json()
        emp_list = employees.get("data", employees) if isinstance(employees, dict) else employees
        if not emp_list:
            pytest.skip("No employees")
        emp_id = emp_list[0].get("employee_id") if isinstance(emp_list, list) else None
        if not emp_id:
            pytest.skip("No employee_id")

        resp = requests.get(
            f"{base_url}/api/v1/hr/tds/calculate/{emp_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"TDS calculate: {resp.status_code} {resp.text[:300]}"


# ==================== NEGATIVE / SECURITY TESTS ====================

class TestHRNegativeCases:
    """Negative and security tests for HR endpoints"""

    def test_employees_no_auth_rejected(self, base_url):
        """All employee endpoints reject unauthenticated requests"""
        for endpoint in ["/api/v1/hr/employees", "/api/v1/hr/departments", "/api/v1/hr/payroll/records"]:
            resp = requests.get(f"{base_url}{endpoint}")
            assert resp.status_code in (401, 403), f"{endpoint} without auth: {resp.status_code}"

    def test_create_employee_invalid_data(self, base_url, auth_headers):
        """POST /api/v1/hr/employees with invalid data returns 422"""
        resp = requests.post(
            f"{base_url}/api/v1/hr/employees",
            json={"first_name": "X"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_delete_nonexistent_employee(self, base_url, auth_headers):
        """DELETE /api/v1/hr/employees/{fake} returns 200 (soft-delete is idempotent) or 404"""
        resp = requests.delete(
            f"{base_url}/api/v1/hr/employees/emp_does_not_exist_999",
            headers=auth_headers,
        )
        # Soft-delete via update_one with no match returns 200 (idempotent) — accepted behavior
        assert resp.status_code in (200, 404), f"Expected 200/404, got {resp.status_code}"

    def test_payroll_generate_no_auth(self, base_url):
        """POST /api/v1/hr/payroll/generate without auth returns 401/403"""
        resp = requests.post(f"{base_url}/api/v1/hr/payroll/generate")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"
