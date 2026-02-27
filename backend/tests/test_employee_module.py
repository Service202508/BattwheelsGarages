"""
Employee Management Module Tests
Tests for Employee CRUD operations, salary calculations, and India compliance
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmployeeModule:
    """Employee Management API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.admin_email = "admin@battwheels.in"
        self.admin_password = "DevTest@123"
        self.test_employee_email = "test.employee@battwheels.in"
        self.test_employee_password = "test123"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json().get("token")
    
    # ==================== AUTH TESTS ====================
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['email']}")
    
    def test_employee_login(self):
        """Test existing employee can login with work_email and password"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_employee_email,
            "password": self.test_employee_password
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == self.test_employee_email
        assert data["user"]["role"] == "technician"
        print(f"✓ Employee login successful: {data['user']['email']}")
    
    # ==================== GET EMPLOYEES TESTS ====================
    
    def test_get_employees_list(self):
        """Test GET /api/employees returns list of employees"""
        token = self.get_admin_token()
        response = self.session.get(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/employees returned {len(data)} employees")
        
        # Verify employee structure
        if len(data) > 0:
            emp = data[0]
            assert "employee_id" in emp
            assert "full_name" in emp
            assert "employee_code" in emp
            assert "department" in emp
            assert "designation" in emp
            assert "system_role" in emp
            assert "status" in emp
            assert "salary" in emp
            assert "compliance" in emp
            assert "bank_details" in emp
            print(f"✓ Employee structure validated: {emp['full_name']}")
    
    def test_get_employees_filter_by_department(self):
        """Test GET /api/employees with department filter"""
        token = self.get_admin_token()
        response = self.session.get(
            f"{BASE_URL}/api/employees?department=service",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for emp in data:
            assert emp["department"] == "service"
        print(f"✓ Department filter working: {len(data)} employees in service")
    
    def test_get_employees_filter_by_status(self):
        """Test GET /api/employees with status filter"""
        token = self.get_admin_token()
        response = self.session.get(
            f"{BASE_URL}/api/employees?status=active",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for emp in data:
            assert emp["status"] == "active"
        print(f"✓ Status filter working: {len(data)} active employees")
    
    def test_get_single_employee(self):
        """Test GET /api/employees/{id} returns single employee details"""
        token = self.get_admin_token()
        
        # First get list to find an employee ID
        list_response = self.session.get(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"}
        )
        employees = list_response.json()
        assert len(employees) > 0, "No employees found"
        
        employee_id = employees[0]["employee_id"]
        
        # Get single employee
        response = self.session.get(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        emp = response.json()
        assert emp["employee_id"] == employee_id
        print(f"✓ GET /api/employees/{employee_id} returned: {emp['full_name']}")
    
    def test_get_nonexistent_employee(self):
        """Test GET /api/employees/{id} returns 404 for non-existent employee"""
        token = self.get_admin_token()
        response = self.session.get(
            f"{BASE_URL}/api/employees/emp_nonexistent123",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        print("✓ Non-existent employee returns 404")
    
    # ==================== MANAGERS & ROLES TESTS ====================
    
    def test_get_managers_list(self):
        """Test GET /api/employees/managers/list returns managers"""
        token = self.get_admin_token()
        response = self.session.get(
            f"{BASE_URL}/api/employees/managers/list",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Managers should have admin or manager role
        for mgr in data:
            assert mgr.get("employee_id") is not None
        print(f"✓ GET /api/employees/managers/list returned {len(data)} managers")
    
    def test_get_roles_list(self):
        """Test GET /api/employees/roles/list returns available roles"""
        token = self.get_admin_token()
        response = self.session.get(
            f"{BASE_URL}/api/employees/roles/list",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5  # admin, manager, technician, accountant, customer_support
        
        role_values = [r["value"] for r in data]
        assert "admin" in role_values
        assert "manager" in role_values
        assert "technician" in role_values
        assert "accountant" in role_values
        assert "customer_support" in role_values
        print(f"✓ GET /api/employees/roles/list returned {len(data)} roles")
    
    # ==================== CREATE EMPLOYEE TESTS ====================
    
    def test_create_employee_full(self):
        """Test POST /api/employees creates employee with user account and calculated deductions"""
        token = self.get_admin_token()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_email = f"TEST_emp_{timestamp}@battwheels.in"
        
        employee_data = {
            # Personal
            "first_name": "TEST_John",
            "last_name": "Doe",
            "date_of_birth": "1990-05-15",
            "gender": "male",
            "personal_email": f"john.personal_{timestamp}@email.com",
            "phone": "+91 98765 43210",
            "current_address": "123 Test Street",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+91 98765 43211",
            "emergency_contact_relation": "Spouse",
            # Employment
            "work_email": test_email,
            "department": "operations",
            "designation": "Senior Technician",
            "employment_type": "full_time",
            "joining_date": "2026-02-16",
            "shift": "general",
            # Role & Access
            "system_role": "technician",
            "password": "test_pwd_placeholder",
            # Salary
            "basic_salary": 25000,
            "hra": 10000,
            "da": 0,
            "conveyance": 0,
            "medical_allowance": 0,
            "special_allowance": 0,
            "other_allowances": 0,
            # Compliance
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "1234 5678 9012",
            "pf_enrolled": True,
            "esi_enrolled": False,
            # Bank
            "bank_name": "State Bank of India",
            "account_number": "1234567890123",
            "ifsc_code": "SBIN0001234",
            "branch_name": "MG Road Branch",
            "account_type": "savings"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"},
            json=employee_data
        )
        
        assert response.status_code == 200, f"Create employee failed: {response.text}"
        emp = response.json()
        
        # Verify employee created
        assert emp["first_name"] == "TEST_John"
        assert emp["last_name"] == "Doe"
        assert emp["full_name"] == "TEST_John Doe"
        assert emp["work_email"] == test_email
        assert emp["department"] == "operations"
        assert emp["designation"] == "Senior Technician"
        assert emp["system_role"] == "technician"
        assert emp["status"] == "active"
        assert emp["employee_code"].startswith("EMP")
        
        # Verify salary calculations
        salary = emp["salary"]
        assert salary["basic_salary"] == 25000
        assert salary["hra"] == 10000
        assert salary["gross_salary"] == 35000  # 25000 + 10000
        
        # Verify PF deduction (12% of basic)
        assert salary["pf_deduction"] == 3000  # 25000 * 0.12
        
        # Verify Professional Tax (gross > 15000)
        assert salary["professional_tax"] == 200
        
        # Verify net salary calculation
        expected_net = 35000 - 3000 - 200 - salary["tds"]
        assert abs(salary["net_salary"] - expected_net) < 1
        
        # Verify compliance
        assert emp["compliance"]["pan_number"] == "ABCDE1234F"
        assert emp["compliance"]["pf_enrolled"] == True
        
        # Verify bank details
        assert emp["bank_details"]["bank_name"] == "State Bank of India"
        
        print(f"✓ Employee created: {emp['employee_code']} - {emp['full_name']}")
        print(f"  Gross: ₹{salary['gross_salary']}, PF: ₹{salary['pf_deduction']}, Net: ₹{salary['net_salary']}")
        
        # Verify new employee can login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "test_pwd_placeholder"
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["user"]["email"] == test_email
        assert login_data["user"]["role"] == "technician"
        print(f"✓ New employee can login with work_email and password")
        
        # Store for cleanup
        self.created_employee_id = emp["employee_id"]
        return emp
    
    def test_create_employee_duplicate_email(self):
        """Test POST /api/employees rejects duplicate email"""
        token = self.get_admin_token()
        
        employee_data = {
            "first_name": "Duplicate",
            "last_name": "Test",
            "work_email": self.test_employee_email,  # Already exists
            "department": "operations",
            "designation": "Test",
            "joining_date": "2026-02-16",
            "system_role": "technician",
            "password": "test123"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"},
            json=employee_data
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
        print("✓ Duplicate email rejected correctly")
    
    # ==================== UPDATE EMPLOYEE TESTS ====================
    
    def test_update_employee(self):
        """Test PUT /api/employees/{id} updates employee details"""
        token = self.get_admin_token()
        
        # Get existing employee
        list_response = self.session.get(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"}
        )
        employees = list_response.json()
        assert len(employees) > 0
        
        employee_id = employees[0]["employee_id"]
        original_designation = employees[0]["designation"]
        
        # Update designation
        update_data = {
            "designation": "Updated Designation"
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["designation"] == "Updated Designation"
        print(f"✓ Employee updated: {updated['full_name']} - designation changed")
        
        # Revert change
        self.session.put(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"designation": original_designation}
        )
    
    def test_update_employee_salary_recalculates_deductions(self):
        """Test updating salary recalculates deductions correctly"""
        token = self.get_admin_token()
        
        # Get existing employee
        list_response = self.session.get(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"}
        )
        employees = list_response.json()
        assert len(employees) > 0
        
        employee_id = employees[0]["employee_id"]
        original_salary = employees[0]["salary"]
        
        # Update basic salary
        update_data = {
            "basic_salary": 30000,
            "hra": 12000
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        updated = response.json()
        salary = updated["salary"]
        
        # Verify recalculations
        assert salary["basic_salary"] == 30000
        assert salary["hra"] == 12000
        assert salary["gross_salary"] == 42000  # 30000 + 12000
        
        # PF should be 12% of new basic
        expected_pf = 30000 * 0.12
        assert salary["pf_deduction"] == expected_pf
        
        print(f"✓ Salary updated and deductions recalculated")
        print(f"  New Gross: ₹{salary['gross_salary']}, PF: ₹{salary['pf_deduction']}")
        
        # Revert changes
        self.session.put(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "basic_salary": original_salary["basic_salary"],
                "hra": original_salary["hra"]
            }
        )
    
    # ==================== DELETE EMPLOYEE TESTS ====================
    
    def test_delete_employee_soft_delete(self):
        """Test DELETE /api/employees/{id} performs soft delete (deactivates)"""
        token = self.get_admin_token()
        
        # Create a test employee to delete
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_email = f"TEST_delete_{timestamp}@battwheels.in"
        
        create_response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "TEST_Delete",
                "last_name": "Me",
                "work_email": test_email,
                "department": "operations",
                "designation": "Test",
                "joining_date": "2026-02-16",
                "system_role": "technician",
                "password": "test123"
            }
        )
        
        assert create_response.status_code == 200
        emp = create_response.json()
        employee_id = emp["employee_id"]
        
        # Delete (soft delete)
        delete_response = self.session.delete(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert delete_response.status_code == 200
        assert "deactivated" in delete_response.json().get("message", "").lower()
        
        # Verify employee is now terminated
        get_response = self.session.get(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert get_response.status_code == 200
        deleted_emp = get_response.json()
        assert deleted_emp["status"] == "terminated"
        assert deleted_emp["termination_date"] is not None
        
        # Verify user account is deactivated
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "test123"
        })
        assert login_response.status_code == 401
        
        print(f"✓ Employee soft deleted: {employee_id}")
        print(f"  Status: {deleted_emp['status']}, User login disabled")
    
    # ==================== SALARY DEDUCTION TESTS ====================
    
    def test_pf_deduction_calculation(self):
        """Test PF deduction is 12% of basic salary when enrolled"""
        token = self.get_admin_token()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_email = f"TEST_pf_{timestamp}@battwheels.in"
        
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "TEST_PF",
                "last_name": "Test",
                "work_email": test_email,
                "department": "operations",
                "designation": "Test",
                "joining_date": "2026-02-16",
                "system_role": "technician",
                "password": "test123",
                "basic_salary": 50000,
                "pf_enrolled": True
            }
        )
        
        assert response.status_code == 200
        emp = response.json()
        
        # PF should be 12% of basic
        expected_pf = 50000 * 0.12
        assert emp["salary"]["pf_deduction"] == expected_pf
        print(f"✓ PF deduction correct: ₹{emp['salary']['pf_deduction']} (12% of ₹50000)")
    
    def test_esi_deduction_calculation(self):
        """Test ESI deduction is 0.75% when gross <= 21000 and enrolled"""
        token = self.get_admin_token()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_email = f"TEST_esi_{timestamp}@battwheels.in"
        
        # Create employee with gross <= 21000
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "TEST_ESI",
                "last_name": "Test",
                "work_email": test_email,
                "department": "operations",
                "designation": "Test",
                "joining_date": "2026-02-16",
                "system_role": "technician",
                "password": "test123",
                "basic_salary": 15000,
                "hra": 5000,  # Gross = 20000
                "pf_enrolled": False,
                "esi_enrolled": True
            }
        )
        
        assert response.status_code == 200
        emp = response.json()
        
        # ESI should be 0.75% of gross (20000)
        expected_esi = round(20000 * 0.0075, 2)
        assert emp["salary"]["esi_deduction"] == expected_esi
        print(f"✓ ESI deduction correct: ₹{emp['salary']['esi_deduction']} (0.75% of ₹20000)")
    
    def test_esi_not_applied_above_threshold(self):
        """Test ESI deduction is 0 when gross > 21000"""
        token = self.get_admin_token()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_email = f"TEST_esi_high_{timestamp}@battwheels.in"
        
        # Create employee with gross > 21000
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "TEST_ESI_High",
                "last_name": "Test",
                "work_email": test_email,
                "department": "operations",
                "designation": "Test",
                "joining_date": "2026-02-16",
                "system_role": "technician",
                "password": "test123",
                "basic_salary": 25000,
                "hra": 10000,  # Gross = 35000 > 21000
                "pf_enrolled": False,
                "esi_enrolled": True
            }
        )
        
        assert response.status_code == 200
        emp = response.json()
        
        # ESI should be 0 since gross > 21000
        assert emp["salary"]["esi_deduction"] == 0
        print(f"✓ ESI not applied for gross > 21000: ₹{emp['salary']['esi_deduction']}")
    
    def test_professional_tax_calculation(self):
        """Test Professional Tax calculation based on gross salary"""
        token = self.get_admin_token()
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_email = f"TEST_pt_{timestamp}@battwheels.in"
        
        # Create employee with gross > 15000
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "TEST_PT",
                "last_name": "Test",
                "work_email": test_email,
                "department": "operations",
                "designation": "Test",
                "joining_date": "2026-02-16",
                "system_role": "technician",
                "password": "test123",
                "basic_salary": 20000,  # Gross > 15000
                "pf_enrolled": False,
                "esi_enrolled": False
            }
        )
        
        assert response.status_code == 200
        emp = response.json()
        
        # Professional Tax should be 200 for gross > 15000
        assert emp["salary"]["professional_tax"] == 200
        print(f"✓ Professional Tax correct: ₹{emp['salary']['professional_tax']}")
    
    # ==================== AUTHORIZATION TESTS ====================
    
    def test_unauthorized_access(self):
        """Test endpoints require authentication"""
        response = self.session.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 401
        print("✓ Unauthorized access returns 401")
    
    def test_non_admin_cannot_create_employee(self):
        """Test non-admin users cannot create employees"""
        # Login as technician
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_employee_email,
            "password": self.test_employee_password
        })
        tech_token = login_response.json().get("token")
        
        response = self.session.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {tech_token}"},
            json={
                "first_name": "Unauthorized",
                "last_name": "Test",
                "work_email": "unauthorized@test.com",
                "department": "operations",
                "designation": "Test",
                "joining_date": "2026-02-16",
                "system_role": "technician",
                "password": "test123"
            }
        )
        
        assert response.status_code == 403
        print("✓ Non-admin cannot create employees (403)")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_employees(self):
        """Clean up TEST_ prefixed employees"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        token = login_response.json().get("token")
        
        # Get all employees
        response = session.get(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {token}"}
        )
        employees = response.json()
        
        # Delete TEST_ prefixed employees
        deleted_count = 0
        for emp in employees:
            if emp.get("first_name", "").startswith("TEST_"):
                session.delete(
                    f"{BASE_URL}/api/employees/{emp['employee_id']}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} test employees")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
