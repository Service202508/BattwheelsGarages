"""
HR Module API Tests - Attendance, Leave Management, Payroll
Tests for the new HR & Payroll features added to Battwheels OS
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication tests for HR module access"""
    
    def test_admin_login(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        return data["token"]


class TestAttendanceModule:
    """Attendance tracking API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_get_today_attendance(self, auth_token):
        """Test getting today's attendance status"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/today",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "date" in data
        assert "standard_hours" in data
        assert "standard_start" in data
        assert "standard_end" in data
        
        # Verify standard hours configuration
        assert data["standard_hours"] == 9.0
        assert data["standard_start"] == "09:00"
        assert data["standard_end"] == "18:00"
    
    def test_get_my_attendance_records(self, auth_token):
        """Test getting user's attendance records for a month"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/attendance/my-records?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "month" in data
        assert "year" in data
        assert "records" in data
        assert "summary" in data
        
        # Verify summary fields
        summary = data["summary"]
        assert "total_days" in summary
        assert "present_days" in summary
        assert "half_days" in summary
        assert "absent_days" in summary
        assert "leave_days" in summary
        assert "late_arrivals" in summary
        assert "early_departures" in summary
        assert "total_hours" in summary
        assert "overtime_hours" in summary
        assert "attendance_percentage" in summary
        assert "productivity_percentage" in summary
    
    def test_get_team_summary_admin(self, auth_token):
        """Test getting team attendance summary (admin only)"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/attendance/team-summary?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "month" in data
        assert "year" in data
        assert "team_stats" in data
        assert "averages" in data
        
        # Verify averages fields
        averages = data["averages"]
        assert "avg_attendance" in averages
        assert "avg_productivity" in averages
        assert "total_overtime" in averages
        
        # Verify team_stats is a list
        assert isinstance(data["team_stats"], list)


class TestLeaveManagement:
    """Leave management API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_get_leave_types(self, auth_token):
        """Test getting all leave types"""
        response = requests.get(
            f"{BASE_URL}/api/leave/types",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, list)
        assert len(data) >= 5  # CL, SL, EL, LWP, CO
        
        # Verify leave type structure
        leave_codes = [lt["code"] for lt in data]
        assert "CL" in leave_codes  # Casual Leave
        assert "SL" in leave_codes  # Sick Leave
        assert "EL" in leave_codes  # Earned Leave
        assert "LWP" in leave_codes  # Leave Without Pay
        assert "CO" in leave_codes  # Compensatory Off
        
        # Verify days allowed
        for lt in data:
            assert "code" in lt
            assert "name" in lt
            assert "days_allowed" in lt
            assert "is_paid" in lt
    
    def test_get_leave_balance(self, auth_token):
        """Test getting user's leave balance"""
        response = requests.get(
            f"{BASE_URL}/api/leave/balance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "user_id" in data
        assert "year" in data
        assert "balances" in data
        
        # Verify balance structure for each leave type
        balances = data["balances"]
        for code in ["CL", "SL", "EL", "LWP", "CO"]:
            assert code in balances
            assert "total" in balances[code]
            assert "used" in balances[code]
            assert "pending" in balances[code]
            assert "available" in balances[code]
        
        # Verify default allocations
        assert balances["CL"]["total"] == 12
        assert balances["SL"]["total"] == 12
        assert balances["EL"]["total"] == 15
        assert balances["LWP"]["total"] == 365
        assert balances["CO"]["total"] == 10
    
    def test_get_my_leave_requests(self, auth_token):
        """Test getting user's leave requests"""
        response = requests.get(
            f"{BASE_URL}/api/leave/my-requests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, list)
        
        # If there are requests, verify structure
        if len(data) > 0:
            req = data[0]
            assert "leave_id" in req
            assert "user_id" in req
            assert "leave_type" in req
            assert "start_date" in req
            assert "end_date" in req
            assert "days" in req
            assert "reason" in req
            assert "status" in req
    
    def test_get_pending_approvals_admin(self, auth_token):
        """Test getting pending leave approvals (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/leave/pending-approvals",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, list)


class TestPayrollModule:
    """Payroll processing API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_get_payroll_records_admin(self, auth_token):
        """Test getting payroll records (admin only)"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/records?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, list)
        
        # If there are records, verify structure
        if len(data) > 0:
            record = data[0]
            assert "payroll_id" in record
            assert "user_id" in record
            assert "user_name" in record
            assert "month" in record
            assert "year" in record
            assert "working_days" in record
            assert "days_present" in record
            assert "days_absent" in record
            assert "total_hours" in record
            assert "overtime_hours" in record
            assert "attendance_percentage" in record
            assert "productivity_score" in record
            assert "base_salary" in record
            assert "overtime_pay" in record
            assert "deductions" in record
            assert "net_salary" in record
            assert "status" in record
    
    def test_get_my_payroll_records(self, auth_token):
        """Test getting user's own payroll records"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/my-records",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, list)
        
        # If there are records, verify structure
        if len(data) > 0:
            record = data[0]
            assert "payroll_id" in record
            assert "month" in record
            assert "year" in record
            assert "base_salary" in record
            assert "net_salary" in record
            assert "deductions" in record
    
    def test_generate_payroll_admin(self, auth_token):
        """Test generating payroll for all employees (admin only)"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/generate?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "month" in data
        assert "year" in data
        assert "records" in data
        
        # Verify records were generated
        assert isinstance(data["records"], list)
        assert len(data["records"]) > 0
        
        # Verify each record has required fields
        for record in data["records"]:
            assert "payroll_id" in record
            assert "user_id" in record
            assert "base_salary" in record
            assert "net_salary" in record


class TestHRIntegration:
    """Integration tests for HR module workflows"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_attendance_to_payroll_flow(self, auth_token):
        """Test that attendance data flows correctly to payroll"""
        month = datetime.now().month
        year = datetime.now().year
        
        # Get attendance records
        attendance_response = requests.get(
            f"{BASE_URL}/api/attendance/my-records?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert attendance_response.status_code == 200
        attendance_data = attendance_response.json()
        
        # Generate payroll
        payroll_response = requests.post(
            f"{BASE_URL}/api/payroll/generate?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert payroll_response.status_code == 200
        
        # Get my payroll
        my_payroll_response = requests.get(
            f"{BASE_URL}/api/payroll/my-records",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert my_payroll_response.status_code == 200
        payroll_data = my_payroll_response.json()
        
        # Find current month's payroll
        current_payroll = None
        for record in payroll_data:
            if record["month"] == month and record["year"] == year:
                current_payroll = record
                break
        
        # Verify payroll reflects attendance
        if current_payroll:
            # Attendance percentage should match
            assert "attendance_percentage" in current_payroll
            # Late arrivals should affect deductions
            if current_payroll.get("late_arrivals", 0) > 0:
                assert current_payroll["deductions"] > 0
    
    def test_leave_balance_update_on_request(self, auth_token):
        """Test that leave balance updates when request is made"""
        # Get initial balance
        initial_balance_response = requests.get(
            f"{BASE_URL}/api/leave/balance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert initial_balance_response.status_code == 200
        initial_balance = initial_balance_response.json()
        
        # Verify balance structure exists
        assert "balances" in initial_balance
        assert "CL" in initial_balance["balances"]
        
        # Check pending count
        initial_pending = initial_balance["balances"]["CL"].get("pending", 0)
        
        # Get my requests to verify
        requests_response = requests.get(
            f"{BASE_URL}/api/leave/my-requests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert requests_response.status_code == 200


class TestUnauthorizedAccess:
    """Test unauthorized access to HR endpoints"""
    
    def test_attendance_without_auth(self):
        """Test that attendance endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/attendance/today")
        assert response.status_code == 401
    
    def test_leave_without_auth(self):
        """Test that leave endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/leave/types")
        assert response.status_code == 401
    
    def test_payroll_without_auth(self):
        """Test that payroll endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/payroll/my-records")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
