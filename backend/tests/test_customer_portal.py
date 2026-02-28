"""
Customer Portal API Tests
=========================
Tests for customer portal read-only APIs and AMC management.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCustomerAuth:
    """Test customer authentication and role-based access"""
    
    def test_customer_login_success(self):
        """Test customer can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        assert response.status_code == 200, f"Customer login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not returned"
        assert "user" in data, "User data not returned"
        assert data["user"]["role"] == "customer", f"Expected customer role, got {data['user']['role']}"
        assert data["user"]["email"] == "customer@demo.com"
        print(f"SUCCESS: Customer login - user_id: {data['user']['user_id']}")
        return data["token"]
    
    def test_admin_login_success(self):
        """Test admin can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not returned"
        assert "user" in data, "User data not returned"
        assert data["user"]["role"] == "admin", f"Expected admin role, got {data['user']['role']}"
        print(f"SUCCESS: Admin login - user_id: {data['user']['user_id']}")
        return data["token"]
    
    def test_invalid_login(self):
        """Test login fails with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrong_pwd_placeholder"
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print("SUCCESS: Invalid login correctly rejected")


class TestCustomerDashboard:
    """Test customer dashboard API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get customer token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code != 200:
            pytest.skip("Customer login failed - skipping dashboard tests")
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_dashboard(self):
        """Test customer dashboard returns correct stats"""
        response = requests.get(f"{BASE_URL}/api/customer/dashboard", headers=self.headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        # Verify all expected fields are present
        assert "vehicles_count" in data, "vehicles_count missing"
        assert "active_tickets" in data, "active_tickets missing"
        assert "total_services" in data, "total_services missing"
        assert "pending_amount" in data, "pending_amount missing"
        assert "active_amc_plans" in data, "active_amc_plans missing"
        
        # Verify data types
        assert isinstance(data["vehicles_count"], int), "vehicles_count should be int"
        assert isinstance(data["pending_amount"], (int, float)), "pending_amount should be numeric"
        
        print(f"SUCCESS: Dashboard - vehicles: {data['vehicles_count']}, services: {data['total_services']}, pending: ₹{data['pending_amount']}, AMC: {data['active_amc_plans']}")
    
    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/customer/dashboard")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Dashboard correctly requires authentication")


class TestCustomerVehicles:
    """Test customer vehicles API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get customer token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code != 200:
            pytest.skip("Customer login failed - skipping vehicles tests")
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_vehicles(self):
        """Test customer can get their vehicles"""
        response = requests.get(f"{BASE_URL}/api/customer/vehicles", headers=self.headers)
        assert response.status_code == 200, f"Vehicles API failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of vehicles"
        
        if len(data) > 0:
            vehicle = data[0]
            # Verify vehicle structure
            assert "vehicle_id" in vehicle or "registration_number" in vehicle, "Vehicle ID or registration missing"
            print(f"SUCCESS: Found {len(data)} vehicles")
            for v in data:
                print(f"  - {v.get('registration_number', 'N/A')}: {v.get('make', '')} {v.get('model', '')}")
        else:
            print("INFO: No vehicles found for customer")
    
    def test_vehicles_requires_auth(self):
        """Test vehicles API requires authentication"""
        response = requests.get(f"{BASE_URL}/api/customer/vehicles")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Vehicles API correctly requires authentication")


class TestCustomerServiceHistory:
    """Test customer service history API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get customer token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code != 200:
            pytest.skip("Customer login failed - skipping service history tests")
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_service_history(self):
        """Test customer can get their service history"""
        response = requests.get(f"{BASE_URL}/api/customer/service-history", headers=self.headers)
        assert response.status_code == 200, f"Service history failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of services"
        
        if len(data) > 0:
            service = data[0]
            # Verify service structure
            assert "ticket_id" in service, "ticket_id missing"
            assert "status" in service, "status missing"
            assert "title" in service, "title missing"
            print(f"SUCCESS: Found {len(data)} service records")
            for s in data[:3]:  # Show first 3
                print(f"  - {s.get('ticket_id', 'N/A')}: {s.get('title', 'N/A')} [{s.get('status', 'N/A')}]")
        else:
            print("INFO: No service history found for customer")
    
    def test_service_history_with_status_filter(self):
        """Test service history with status filter"""
        response = requests.get(f"{BASE_URL}/api/customer/service-history?status=resolved", headers=self.headers)
        assert response.status_code == 200, f"Filtered service history failed: {response.text}"
        
        data = response.json()
        # All returned items should have resolved status
        for service in data:
            assert service.get("status") == "resolved", f"Expected resolved status, got {service.get('status')}"
        print(f"SUCCESS: Status filter works - found {len(data)} resolved services")
    
    def test_service_history_with_limit(self):
        """Test service history with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/customer/service-history?limit=3", headers=self.headers)
        assert response.status_code == 200, f"Limited service history failed: {response.text}"
        
        data = response.json()
        assert len(data) <= 3, f"Expected max 3 items, got {len(data)}"
        print(f"SUCCESS: Limit parameter works - returned {len(data)} items")


class TestCustomerInvoices:
    """Test customer invoices API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get customer token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code != 200:
            pytest.skip("Customer login failed - skipping invoices tests")
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_invoices(self):
        """Test customer can get their invoices"""
        response = requests.get(f"{BASE_URL}/api/customer/invoices", headers=self.headers)
        assert response.status_code == 200, f"Invoices API failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of invoices"
        
        if len(data) > 0:
            invoice = data[0]
            # Verify invoice structure
            assert "invoice_id" in invoice or "invoice_number" in invoice, "Invoice ID missing"
            print(f"SUCCESS: Found {len(data)} invoices")
            for inv in data[:3]:
                print(f"  - {inv.get('invoice_number', inv.get('invoice_id', 'N/A'))}: ₹{inv.get('total_amount', 0)} [{inv.get('payment_status', 'N/A')}]")
        else:
            print("INFO: No invoices found for customer")


class TestCustomerPaymentsDue:
    """Test customer payments due API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get customer token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code != 200:
            pytest.skip("Customer login failed - skipping payments tests")
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_payments_due(self):
        """Test customer can get their payments due"""
        response = requests.get(f"{BASE_URL}/api/customer/payments-due", headers=self.headers)
        assert response.status_code == 200, f"Payments due API failed: {response.text}"
        
        data = response.json()
        # Verify structure
        assert "payments" in data, "payments field missing"
        assert "total_due" in data, "total_due field missing"
        assert isinstance(data["payments"], list), "payments should be a list"
        assert isinstance(data["total_due"], (int, float)), "total_due should be numeric"
        
        print(f"SUCCESS: Payments due - total: ₹{data['total_due']}, count: {len(data['payments'])}")


class TestCustomerAMC:
    """Test customer AMC subscriptions API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get customer token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code != 200:
            pytest.skip("Customer login failed - skipping AMC tests")
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_amc_subscriptions(self):
        """Test customer can get their AMC subscriptions"""
        response = requests.get(f"{BASE_URL}/api/customer/amc", headers=self.headers)
        assert response.status_code == 200, f"AMC subscriptions API failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of subscriptions"
        
        if len(data) > 0:
            sub = data[0]
            # Verify subscription structure
            assert "subscription_id" in sub, "subscription_id missing"
            assert "plan_name" in sub, "plan_name missing"
            assert "status" in sub, "status missing"
            print(f"SUCCESS: Found {len(data)} AMC subscriptions")
            for s in data:
                print(f"  - {s.get('plan_name', 'N/A')}: {s.get('status', 'N/A')} (services used: {s.get('services_used', 0)}/{s.get('max_services', 0)})")
        else:
            print("INFO: No AMC subscriptions found for customer")
    
    def test_get_available_amc_plans(self):
        """Test customer can view available AMC plans"""
        response = requests.get(f"{BASE_URL}/api/customer/amc-plans", headers=self.headers)
        assert response.status_code == 200, f"AMC plans API failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of plans"
        
        if len(data) > 0:
            plan = data[0]
            # Verify plan structure
            assert "plan_id" in plan, "plan_id missing"
            assert "name" in plan, "name missing"
            assert "price" in plan, "price missing"
            print(f"SUCCESS: Found {len(data)} available AMC plans")
            for p in data:
                print(f"  - {p.get('name', 'N/A')}: ₹{p.get('price', 0)} ({p.get('tier', 'N/A')} tier)")
        else:
            print("INFO: No AMC plans available")


class TestAdminAMCManagement:
    """Test admin AMC management APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping admin AMC tests")
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_get_amc_plans(self):
        """Test admin can get all AMC plans"""
        response = requests.get(f"{BASE_URL}/api/amc/plans", headers=self.headers)
        assert response.status_code == 200, f"Admin AMC plans API failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of plans"
        print(f"SUCCESS: Admin can view {len(data)} AMC plans")
    
    def test_admin_get_amc_subscriptions(self):
        """Test admin can get all AMC subscriptions"""
        response = requests.get(f"{BASE_URL}/api/amc/subscriptions", headers=self.headers)
        assert response.status_code == 200, f"Admin AMC subscriptions API failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of subscriptions"
        print(f"SUCCESS: Admin can view {len(data)} AMC subscriptions")
    
    def test_admin_get_amc_analytics(self):
        """Test admin can get AMC analytics"""
        response = requests.get(f"{BASE_URL}/api/amc/analytics", headers=self.headers)
        assert response.status_code == 200, f"AMC analytics API failed: {response.text}"
        
        data = response.json()
        # Verify analytics structure
        assert "total_active" in data, "total_active missing"
        assert "expiring_soon" in data, "expiring_soon missing"
        assert "total_revenue" in data, "total_revenue missing"
        print(f"SUCCESS: AMC Analytics - active: {data['total_active']}, expiring: {data['expiring_soon']}, revenue: ₹{data['total_revenue']}")


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_customer_cannot_access_admin_amc_routes(self):
        """Test customer cannot access admin AMC management routes"""
        # Login as customer
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "customer@demo.com",
            "password": "test_pwd_placeholder"
        })
        if response.status_code != 200:
            pytest.skip("Customer login failed")
        
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin AMC routes
        response = requests.get(f"{BASE_URL}/api/amc/plans", headers=headers)
        assert response.status_code == 403, f"Expected 403 for customer accessing admin route, got {response.status_code}"
        print("SUCCESS: Customer correctly blocked from admin AMC routes")
    
    def test_admin_can_access_customer_portal(self):
        """Test admin can access customer portal routes (for support)"""
        # Login as admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Admin should be able to access customer portal routes
        response = requests.get(f"{BASE_URL}/api/customer/dashboard", headers=headers)
        assert response.status_code == 200, f"Admin should be able to access customer dashboard, got {response.status_code}"
        print("SUCCESS: Admin can access customer portal routes for support")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
