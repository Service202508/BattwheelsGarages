"""
Test Employee Creation - Bug fix verification for field mismatch
Frontend was sending 'email' and 'date_of_joining' but backend expected 'work_email' and 'joining_date'
This test verifies the fix is working correctly.
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmployeeCreation:
    """Test employee creation flow after bug fix"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        return data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not returned"
        assert data.get("user", {}).get("email") == "admin@battwheels.in"
        print(f"✓ Admin login successful - role: {data.get('user', {}).get('role')}")
    
    def test_create_employee_with_correct_fields(self, auth_headers):
        """Test creating employee with work_email and joining_date (fixed fields)"""
        unique_id = uuid.uuid4().hex[:8]
        test_email = f"test_emp_{unique_id}@battwheels.in"
        
        employee_data = {
            "first_name": "Test",
            "last_name": f"Employee_{unique_id}",
            "work_email": test_email,  # This is the correct field name
            "department": "operations",
            "designation": "Test Technician",
            "joining_date": "2025-01-15",  # This is the correct field name
            "system_role": "technician",
            "password": "test_pwd_placeholder",
            "employment_type": "full_time",
            "basic_salary": 25000,
            "hra": 5000,
            "da": 2000,
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200 or response.status_code == 201, \
            f"Employee creation failed: {response.text}"
        
        data = response.json()
        assert "employee_id" in data, "employee_id not returned"
        assert data.get("work_email") == test_email, "work_email mismatch"
        assert data.get("first_name") == "Test", "first_name mismatch"
        assert data.get("joining_date") == "2025-01-15", "joining_date mismatch"
        
        print(f"✓ Employee created successfully with ID: {data.get('employee_id')}")
        return data
    
    def test_get_employees_list(self, auth_headers):
        """Test getting employees list"""
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get employees failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Got {len(data)} employees in list")
        return data
    
    def test_new_employee_can_login(self, auth_headers):
        """Test that newly created employee can login with their credentials"""
        unique_id = uuid.uuid4().hex[:8]
        test_email = f"login_test_{unique_id}@battwheels.in"
        test_password = "test_pwd_placeholder"
        
        # Create employee
        employee_data = {
            "first_name": "Login",
            "last_name": f"Test_{unique_id}",
            "work_email": test_email,
            "department": "service",
            "designation": "Service Engineer",
            "joining_date": "2025-01-20",
            "system_role": "technician",
            "password": test_password,
            "employment_type": "full_time"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        
        assert create_response.status_code in [200, 201], \
            f"Employee creation failed: {create_response.text}"
        
        created = create_response.json()
        print(f"✓ Employee created: {created.get('employee_id')}")
        
        # Try to login with the new employee's credentials
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        
        assert login_response.status_code == 200, \
            f"New employee login failed: {login_response.text}"
        
        login_data = login_response.json()
        assert "token" in login_data, "Token not returned for new employee"
        assert login_data.get("user", {}).get("email") == test_email
        
        print(f"✓ New employee can login successfully with email: {test_email}")
        return login_data
    
    def test_create_employee_with_all_fields(self, auth_headers):
        """Test creating employee with all fields including salary and bank details"""
        unique_id = uuid.uuid4().hex[:8]
        test_email = f"full_emp_{unique_id}@battwheels.in"
        
        employee_data = {
            # Personal
            "first_name": "Full",
            "last_name": f"Employee_{unique_id}",
            "date_of_birth": "1990-05-15",
            "gender": "male",
            "phone": "9876543210",
            "personal_email": f"personal_{unique_id}@gmail.com",
            "current_address": "123 Test Street",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            # Employment
            "work_email": test_email,
            "department": "finance",
            "designation": "Senior Accountant",
            "employment_type": "full_time",
            "joining_date": "2025-01-25",
            "probation_period_months": 3,
            "work_location": "office",
            "shift": "general",
            # Role & Access
            "system_role": "accountant",
            "password": "accountant123",
            # Salary
            "basic_salary": 50000,
            "hra": 15000,
            "da": 5000,
            "conveyance": 2000,
            "medical_allowance": 1500,
            "special_allowance": 5000,
            "other_allowances": 1000,
            # Bank
            "bank_name": "HDFC Bank",
            "account_number": "12345678901234",
            "ifsc_code": "HDFC0001234",
            "branch_name": "MG Road",
            "account_type": "savings",
            # Compliance
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "1234 5678 9012",
            "pf_enrolled": True,
            "esi_enrolled": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        
        print(f"Full employee creation - Status: {response.status_code}")
        
        assert response.status_code in [200, 201], \
            f"Full employee creation failed: {response.text}"
        
        data = response.json()
        assert data.get("work_email") == test_email
        assert data.get("department") == "finance"
        assert data.get("system_role") == "accountant"
        
        # Check salary structure
        salary = data.get("salary", {})
        assert salary.get("basic_salary") == 50000
        assert salary.get("hra") == 15000
        
        # Check bank details
        bank = data.get("bank_details", {})
        assert bank.get("bank_name") == "HDFC Bank"
        
        print(f"✓ Full employee created with all fields - ID: {data.get('employee_id')}")
        return data


class TestEmployeeValidation:
    """Test employee creation validation"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_create_employee_missing_required_fields(self, auth_headers):
        """Test that creating employee without required fields fails"""
        # Missing work_email
        employee_data = {
            "first_name": "Test",
            "last_name": "Missing",
            "designation": "Test",
            "joining_date": "2025-01-15",
            "system_role": "technician",
            "password": "test123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422, \
            f"Expected validation error (422), got {response.status_code}: {response.text}"
        print("✓ Missing work_email validation works")
    
    def test_create_employee_duplicate_email(self, auth_headers):
        """Test that creating employee with duplicate email fails"""
        unique_id = uuid.uuid4().hex[:8]
        test_email = f"dup_test_{unique_id}@battwheels.in"
        
        employee_data = {
            "first_name": "Duplicate",
            "last_name": "Test1",
            "work_email": test_email,
            "designation": "Test",
            "joining_date": "2025-01-15",
            "system_role": "technician",
            "password": "test123",
            "department": "operations"
        }
        
        # Create first employee
        response1 = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        assert response1.status_code in [200, 201], f"First employee creation failed: {response1.text}"
        print(f"✓ First employee created with email: {test_email}")
        
        # Try to create second employee with same email
        employee_data["last_name"] = "Test2"
        response2 = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        
        # Should fail with duplicate email error
        assert response2.status_code == 400, \
            f"Expected duplicate email error (400), got {response2.status_code}: {response2.text}"
        print("✓ Duplicate email validation works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
