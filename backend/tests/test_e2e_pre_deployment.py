"""
Pre-deployment E2E verification tests for Battwheels OS
Tests 13 fixed issues across signup/login, plan gating, vehicle category, accounting summary
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://security-hardening-17.preview.emergentagent.com')

# ==================== TASK 1: Plan Type Consistency ====================
class TestTask1PlanTypeConsistency:
    """Signup and login both return 'free_trial' for new orgs"""
    
    test_email = f"e2e_verify_{uuid.uuid4().hex[:8]}@test.in"
    test_password = "Test@2026"
    
    def test_01_signup_returns_free_trial(self):
        """Signup should return plan_type='free_trial'"""
        response = requests.post(
            f"{BASE_URL}/api/v1/organizations/signup",
            json={
                "name": "E2E Verify Motors",
                "admin_email": self.test_email,
                "admin_password": self.test_password,
                "admin_name": "E2E Verify User",
                "city": "Delhi",
                "state": "DL"
            }
        )
        
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        
        assert "organization" in data, "Response missing organization"
        org = data["organization"]
        assert org.get("plan_type") == "free_trial", f"Expected plan_type='free_trial', got '{org.get('plan_type')}'"
        
        # Store for next test
        TestTask1PlanTypeConsistency.signup_token = data.get("token")
        print(f"PASS: Signup returns plan_type='free_trial'")
    
    def test_02_login_returns_free_trial(self):
        """Login should also show plan_type='free_trial'"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": self.test_email,
                "password": self.test_password
            }
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        orgs = data.get("organizations", [])
        assert len(orgs) >= 1, "No organizations returned on login"
        assert orgs[0].get("plan_type") == "free_trial", f"Expected plan_type='free_trial', got '{orgs[0].get('plan_type')}'"
        
        # Store token for plan gating tests
        TestTask1PlanTypeConsistency.login_token = data.get("token")
        print(f"PASS: Login returns plan_type='free_trial'")


# ==================== TASK 3: Plan Gating ====================
class TestTask3PlanGating:
    """AMC returns 403 for free_trial, tickets returns 200"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get token from previous test"""
        # Login with the test user created in Task 1
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": TestTask1PlanTypeConsistency.test_email,
                "password": TestTask1PlanTypeConsistency.test_password
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            self.token = None
    
    def test_01_amc_returns_403_for_free_trial(self):
        """AMC POST should return 403 for free_trial users"""
        if not self.token:
            pytest.skip("No token available")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/amc/plans",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test AMC Plan",
                "description": "Test",
                "price": 1000
            }
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("error") == "plan_upgrade_required", f"Expected error='plan_upgrade_required', got '{data}'"
        print(f"PASS: AMC returns 403 with plan_upgrade_required")
    
    def test_02_tickets_returns_200_for_free_trial(self):
        """Tickets GET should return 200"""
        if not self.token:
            pytest.skip("No token available")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Tickets returns 200 for free_trial users")


# ==================== TASK 5: Vehicle Category ====================
class TestTask5VehicleCategory:
    """Vehicle category '2W' saves correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": TestTask1PlanTypeConsistency.test_email,
                "password": TestTask1PlanTypeConsistency.test_password
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            self.token = None
    
    def test_vehicle_category_2w_saves(self):
        """POST ticket with vehicle_category='2W' should return same"""
        if not self.token:
            pytest.skip("No token available")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "title": f"Test 2W Ticket - {uuid.uuid4().hex[:8]}",
                "description": "Testing vehicle_category",
                "vehicle_category": "2W",
                "priority": "medium"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("vehicle_category") == "2W", f"Expected vehicle_category='2W', got '{data.get('vehicle_category')}'"
        print(f"PASS: Vehicle category '2W' saved correctly")


# ==================== TASK 7: Accounting Summary ====================
class TestTask7AccountingSummary:
    """Accounting summary returns data for demo org"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login with demo user"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "demo@voltmotors.in",
                "password": "Demo@12345"
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            self.token = None
    
    def test_accounting_summary_returns_data(self):
        """GET accounting summary should return proper structure"""
        if not self.token:
            pytest.skip("Demo login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/v1/accounting/summary",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "total_revenue" in data, "Missing total_revenue"
        assert "total_expenses" in data, "Missing total_expenses"
        assert "gross_profit" in data, "Missing gross_profit"
        print(f"PASS: Accounting summary works. Revenue={data.get('total_revenue')}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
