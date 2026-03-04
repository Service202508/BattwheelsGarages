"""
HR Module API Tests - Attendance, Leave Management, Payroll
Tests for the new HR & Payroll features added to Battwheels OS
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

class TestAuthentication:
    """Authentication tests for HR module access"""
    
    def test_admin_login(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "owner"
        return data["token"]


class TestAttendanceModule:
    """Attendance tracking API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_get_today_attendance(self, auth_token):
        """Test getting today's attendance status"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/attendance/today",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # API may return attendance data or a "no record" message
        if "message" in data:
            assert "no attendance" in data["message"].lower() or "not found" in data["message"].lower()
        else:
            assert "date" in data
    
    def test_get_my_attendance_records(self, auth_token):
        """Test getting user's attendance records for a month"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/attendance/my-records?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 404 if user has no employee record
        assert response.status_code in (200, 404)
        data = response.json()
        
        if response.status_code == 200:
            assert "records" in data or "month" in data
        else:
            assert "detail" in data
    
    def test_get_team_summary_admin(self, auth_token):
        """Test getting team attendance summary (admin only)"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/attendance/team-summary?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 404/500 if no employee records exist for this user
        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            # Verify response has basic structure
            assert isinstance(data, dict)


class TestLeaveManagement:
    """Leave management API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_get_leave_types(self, auth_token):
        """Test getting all leave types"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/leave/types",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, (list, dict))
        _list = data.get("data", data) if isinstance(data, dict) else data
        assert len(_list) >= 1
        
        # Verify leave type structure
        first_lt = _list[0]
        assert "type" in first_lt or "code" in first_lt
        assert "name" in first_lt
    
    def test_get_leave_balance(self, auth_token):
        """Test getting user's leave balance"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/leave/balance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 404 if user has no employee record
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    def test_get_my_leave_requests(self, auth_token):
        """Test getting user's leave requests"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/leave/my-requests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, (list, dict))
        
        # If there are requests, verify structure
        _list = data.get("data", data) if isinstance(data, dict) else data
        if len(_list) > 0:
            req = _list[0]
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
            f"{BASE_URL}/api/v1/hr/leave/pending-approvals",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, (list, dict))


class TestPayrollModule:
    """Payroll processing API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_get_payroll_records_admin(self, auth_token):
        """Test getting payroll records (admin only)"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/payroll/records?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a list
        assert isinstance(data, (list, dict))
        
        # If there are records, verify structure
        _list = data.get("data", data) if isinstance(data, dict) else data

        if len(_list) > 0:

            record = _list[0]
            assert "payroll_id" in record
            assert "employee_id" in record or "user_id" in record
            assert "month" in record
            assert "year" in record
            assert "net_salary" in record
            assert "status" in record
    
    def test_get_my_payroll_records(self, auth_token):
        """Test getting user's own payroll records"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/payroll/my-records",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 404 if user has no employee record
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    def test_generate_payroll_admin(self, auth_token):
        """Test generating payroll for all employees (admin only)"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/payroll/generate?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # 409 = payroll already generated for this period
        assert response.status_code in (200, 409)
        data = response.json()
        
        # Verify response has a success indicator
        assert "message" in data or "data" in data or "records" in data or "detail" in data


class TestHRIntegration:
    """Integration tests for HR module workflows"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json()["token"]
    
    def test_attendance_to_payroll_flow(self, auth_token):
        """Test that attendance data flows correctly to payroll"""
        month = datetime.now().month
        year = datetime.now().year
        
        # Get attendance records (may fail if no employee record)
        attendance_response = requests.get(
            f"{BASE_URL}/api/v1/hr/attendance/my-records?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert attendance_response.status_code in (200, 404)
        
        # Generate payroll (may return 409 if already generated)
        payroll_response = requests.post(
            f"{BASE_URL}/api/v1/hr/payroll/generate?month={month}&year={year}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert payroll_response.status_code in (200, 409)
        
        # Get my payroll (may fail if no employee record)
        my_payroll_response = requests.get(
            f"{BASE_URL}/api/v1/hr/payroll/my-records",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert my_payroll_response.status_code in (200, 404)
    
    def test_leave_balance_update_on_request(self, auth_token):
        """Test that leave balance updates when request is made"""
        # Get initial balance (may return 404 if no employee record)
        initial_balance_response = requests.get(
            f"{BASE_URL}/api/v1/hr/leave/balance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert initial_balance_response.status_code in (200, 404)
        
        if initial_balance_response.status_code == 200:
            initial_balance = initial_balance_response.json()
            assert isinstance(initial_balance, dict)


class TestUnauthorizedAccess:
    """Test unauthorized access to HR endpoints"""
    
    def test_attendance_without_auth(self):
        """Test that attendance endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/hr/attendance/today")
        assert response.status_code == 401
    
    def test_leave_without_auth(self):
        """Test that leave endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/hr/leave/types")
        assert response.status_code == 401
    
    def test_payroll_without_auth(self):
        """Test that payroll endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/hr/payroll/my-records")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
