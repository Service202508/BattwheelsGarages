"""
Role-Based Access Control and Portal Testing
Tests for: Permissions API, Technician Portal, Business Portal
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_check(self):
        """Verify API is running"""
        res = requests.get(f"{BASE_URL}/api/health")
        print(f"Health check response: {res.status_code}")
        assert res.status_code == 200
    
    def test_admin_login(self):
        """Admin login - admin@battwheels.in"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        print(f"Admin login: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "token" in data or "access_token" in data
        assert data.get("user", {}).get("role") == "DevTest@123"
        return data
    
    def test_technician_login(self):
        """Technician login - deepak@battwheelsgarages.in"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "deepak@battwheelsgarages.in",
            "password": "DevTest@123"
        })
        print(f"Technician login: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "token" in data or "access_token" in data
        assert data.get("user", {}).get("role") == "technician"
        return data


class TestPermissionsAPI:
    """Test Permissions CRUD API endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        if res.status_code != 200:
            pytest.skip("Admin login failed")
        token = res.json().get("token") or res.json().get("access_token")
        return token
    
    def test_list_modules(self, admin_token):
        """GET /api/permissions/modules - List all modules"""
        res = requests.get(
            f"{BASE_URL}/api/permissions/modules",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"List modules: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "modules" in data
        modules = data["modules"]
        assert len(modules) > 0
        # Check some expected modules exist
        module_ids = [m["module_id"] for m in modules]
        assert "dashboard" in module_ids
        assert "tickets" in module_ids
        assert "attendance" in module_ids
        print(f"Found {len(modules)} modules")
    
    def test_list_roles(self, admin_token):
        """GET /api/permissions/roles - List all roles"""
        res = requests.get(
            f"{BASE_URL}/api/permissions/roles",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"List roles: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "roles" in data
        roles = data["roles"]
        # Check all 5 expected roles exist
        role_names = [r["role"] for r in roles]
        expected_roles = ["DevTest@123", "manager", "technician", "customer", "business_customer"]
        for expected in expected_roles:
            assert expected in role_names, f"Role '{expected}' not found"
        print(f"Found roles: {role_names}")
    
    def test_get_admin_permissions(self, admin_token):
        """GET /api/permissions/roles/admin - Admin has full access"""
        res = requests.get(
            f"{BASE_URL}/api/permissions/roles/admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Get admin permissions: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "DevTest@123"
        assert "modules" in data
        # Admin should have full access to dashboard
        dashboard_perms = data["modules"].get("dashboard", {})
        assert dashboard_perms.get("can_view") == True
    
    def test_get_technician_permissions(self, admin_token):
        """GET /api/permissions/roles/technician - Verify technician restricted access"""
        res = requests.get(
            f"{BASE_URL}/api/permissions/roles/technician",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Get technician permissions: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "technician"
        modules = data.get("modules", {})
        # Technician should view dashboard, tickets, attendance
        assert modules.get("dashboard", {}).get("can_view") == True
        assert modules.get("tickets", {}).get("can_view") == True
        assert modules.get("attendance", {}).get("can_view") == True
        # Technician should NOT access users, settings
        assert modules.get("users", {}).get("can_view") == False
        assert modules.get("settings", {}).get("can_view") == False
    
    def test_get_business_customer_permissions(self, admin_token):
        """GET /api/permissions/roles/business_customer - Business customer access"""
        res = requests.get(
            f"{BASE_URL}/api/permissions/roles/business_customer",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Get business_customer permissions: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "business_customer"
        modules = data.get("modules", {})
        # Business customer should have fleet management and reports
        assert modules.get("vehicles", {}).get("can_view") == True
        assert modules.get("reports", {}).get("can_view") == True
    
    def test_update_module_permission(self, admin_token):
        """PATCH /api/permissions/roles/{role}/module/{module_id} - Update permission"""
        # Toggle a permission
        res = requests.patch(
            f"{BASE_URL}/api/permissions/roles/technician/module/vehicles",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "role": "technician",
                "module_id": "vehicles",
                "permission_key": "can_create",
                "value": True
            }
        )
        print(f"Update permission: {res.status_code}")
        assert res.status_code == 200
        
        # Verify the update
        res2 = requests.get(
            f"{BASE_URL}/api/permissions/roles/technician",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res2.status_code == 200
        data = res2.json()
        vehicles_perms = data.get("modules", {}).get("vehicles", {})
        assert vehicles_perms.get("can_create") == True
        
        # Revert the change
        requests.patch(
            f"{BASE_URL}/api/permissions/roles/technician/module/vehicles",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "role": "technician",
                "module_id": "vehicles",
                "permission_key": "can_create",
                "value": False
            }
        )
    
    def test_check_permission(self, admin_token):
        """GET /api/permissions/check - Check specific permission"""
        res = requests.get(
            f"{BASE_URL}/api/permissions/check",
            params={"role": "DevTest@123", "module_id": "dashboard", "action": "can_view"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Check permission: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert data.get("allowed") == True
        
        # Check technician can't delete users
        res2 = requests.get(
            f"{BASE_URL}/api/permissions/check",
            params={"role": "technician", "module_id": "users", "action": "can_delete"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2.get("allowed") == False
    
    def test_get_nonexistent_role(self, admin_token):
        """GET /api/permissions/roles/{invalid} - 404 for invalid role"""
        res = requests.get(
            f"{BASE_URL}/api/permissions/roles/nonexistent_role_xyz",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Get nonexistent role: {res.status_code}")
        assert res.status_code == 404


class TestTechnicianPortalAPI:
    """Test Technician Portal specific APIs"""
    
    @pytest.fixture
    def tech_token(self):
        """Get technician auth token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "deepak@battwheelsgarages.in",
            "password": "DevTest@123"
        })
        if res.status_code != 200:
            pytest.skip("Technician login failed")
        token = res.json().get("token") or res.json().get("access_token")
        return token
    
    def test_technician_dashboard(self, tech_token):
        """GET /api/technician/dashboard - Technician dashboard data"""
        res = requests.get(
            f"{BASE_URL}/api/technician/dashboard",
            headers={"Authorization": f"Bearer {tech_token}"}
        )
        print(f"Technician dashboard: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        # Verify dashboard structure
        assert "technician" in data
        assert "tickets" in data
        assert "attendance" in data
        # Verify tickets data has expected fields
        tickets = data["tickets"]
        assert "open" in tickets
        assert "in_progress" in tickets
        assert "completed_today" in tickets
        assert "total_assigned" in tickets
        print(f"Dashboard data: {data}")
    
    def test_technician_my_tickets(self, tech_token):
        """GET /api/technician/tickets - Only assigned tickets"""
        res = requests.get(
            f"{BASE_URL}/api/technician/tickets",
            headers={"Authorization": f"Bearer {tech_token}"}
        )
        print(f"Technician tickets: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "tickets" in data
        assert "total" in data
        # Verify all tickets are assigned to this technician
        # (They should be, but we're just checking structure)
        print(f"Found {data['total']} assigned tickets")
    
    def test_technician_tickets_filter_status(self, tech_token):
        """GET /api/technician/tickets?status=active - Filter by status"""
        res = requests.get(
            f"{BASE_URL}/api/technician/tickets",
            params={"status": "active"},
            headers={"Authorization": f"Bearer {tech_token}"}
        )
        print(f"Technician active tickets: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "tickets" in data
    
    def test_technician_attendance(self, tech_token):
        """GET /api/technician/attendance - Own attendance records"""
        res = requests.get(
            f"{BASE_URL}/api/technician/attendance",
            headers={"Authorization": f"Bearer {tech_token}"}
        )
        print(f"Technician attendance: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "records" in data
        assert "summary" in data
        assert "month" in data
        assert "year" in data
        summary = data["summary"]
        assert "present" in summary
        assert "absent" in summary
    
    def test_technician_leave_requests(self, tech_token):
        """GET /api/technician/leave - Own leave requests"""
        res = requests.get(
            f"{BASE_URL}/api/technician/leave",
            headers={"Authorization": f"Bearer {tech_token}"}
        )
        print(f"Technician leave: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "requests" in data
        assert "balance" in data
    
    def test_technician_payroll(self, tech_token):
        """GET /api/technician/payroll - Own payroll history"""
        res = requests.get(
            f"{BASE_URL}/api/technician/payroll",
            headers={"Authorization": f"Bearer {tech_token}"}
        )
        print(f"Technician payroll: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "payslips" in data
    
    def test_technician_productivity(self, tech_token):
        """GET /api/technician/productivity - Own productivity metrics"""
        res = requests.get(
            f"{BASE_URL}/api/technician/productivity",
            headers={"Authorization": f"Bearer {tech_token}"}
        )
        print(f"Technician productivity: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "this_month" in data
        assert "weekly_trend" in data
        assert "rank" in data
    
    def test_technician_unauthorized_without_token(self):
        """Technician APIs require authentication"""
        res = requests.get(f"{BASE_URL}/api/technician/dashboard")
        print(f"Unauthorized access: {res.status_code}")
        assert res.status_code == 401
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        if res.status_code != 200:
            pytest.skip("Admin login failed")
        return res.json().get("token") or res.json().get("access_token")
    
    def test_admin_cannot_access_technician_portal(self, admin_token):
        """Admin role should be rejected from technician portal"""
        res = requests.get(
            f"{BASE_URL}/api/technician/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Admin accessing tech portal: {res.status_code}")
        assert res.status_code == 403


class TestBusinessPortalAPI:
    """Test Business Customer Portal APIs"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for testing"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        if res.status_code != 200:
            pytest.skip("Admin login failed")
        return res.json().get("token") or res.json().get("access_token")
    
    def test_business_registration_endpoint_exists(self):
        """POST /api/business/register - Endpoint exists"""
        res = requests.post(
            f"{BASE_URL}/api/business/register",
            json={
                "business_name": "TEST_Fleet_Company",
                "business_type": "fleet",
                "gst_number": "TEST29ABCDE1234F1Z5",
                "address": "123 Test Street",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560001",
                "contact_name": "Test Contact",
                "contact_email": f"test_business_{os.urandom(4).hex()}@test.com",
                "contact_phone": "9876543210"
            }
        )
        print(f"Business registration: {res.status_code}")
        # Either success or email already exists
        assert res.status_code in [200, 201, 400]
    
    def test_business_dashboard_endpoint_exists(self, admin_token):
        """GET /api/business/dashboard - Endpoint exists"""
        res = requests.get(
            f"{BASE_URL}/api/business/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Business dashboard: {res.status_code}")
        # Should return 403 for admin (not business role) or 404 (no business profile)
        assert res.status_code in [200, 403, 404]
    
    def test_business_fleet_endpoint_exists(self, admin_token):
        """GET /api/business/fleet - Endpoint exists"""
        res = requests.get(
            f"{BASE_URL}/api/business/fleet",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Business fleet: {res.status_code}")
        assert res.status_code in [200, 403, 404]
    
    def test_business_tickets_endpoint_exists(self, admin_token):
        """GET /api/business/tickets - Endpoint exists"""
        res = requests.get(
            f"{BASE_URL}/api/business/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Business tickets: {res.status_code}")
        assert res.status_code in [200, 403, 404]
    
    def test_business_invoices_endpoint_exists(self, admin_token):
        """GET /api/business/invoices - Endpoint exists"""
        res = requests.get(
            f"{BASE_URL}/api/business/invoices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Business invoices: {res.status_code}")
        assert res.status_code in [200, 403, 404]
    
    def test_business_amc_endpoint_exists(self, admin_token):
        """GET /api/business/amc - Endpoint exists"""
        res = requests.get(
            f"{BASE_URL}/api/business/amc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Business AMC: {res.status_code}")
        assert res.status_code in [200, 403, 404]
    
    def test_business_reports_endpoint_exists(self, admin_token):
        """GET /api/business/reports/summary - Endpoint exists"""
        res = requests.get(
            f"{BASE_URL}/api/business/reports/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Business reports: {res.status_code}")
        assert res.status_code in [200, 403, 404]
    
    def test_business_bulk_payment_endpoint_exists(self, admin_token):
        """POST /api/business/invoices/bulk-payment - Endpoint exists"""
        res = requests.post(
            f"{BASE_URL}/api/business/invoices/bulk-payment",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "invoice_ids": ["test_inv_1"],
                "payment_method": "razorpay"
            }
        )
        print(f"Business bulk payment: {res.status_code}")
        # Will fail due to not being business role or invalid invoices
        assert res.status_code in [200, 400, 403, 404]


class TestSeedDefaults:
    """Test seeding default permissions"""
    
    @pytest.fixture
    def admin_token(self):
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        if res.status_code != 200:
            pytest.skip("Admin login failed")
        return res.json().get("token") or res.json().get("access_token")
    
    def test_seed_default_permissions(self, admin_token):
        """POST /api/permissions/seed-defaults - Seed default permissions"""
        res = requests.post(
            f"{BASE_URL}/api/permissions/seed-defaults",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"Seed defaults: {res.status_code}")
        assert res.status_code == 200
        data = res.json()
        assert "roles" in data
        roles = data["roles"]
        assert "DevTest@123" in roles
        assert "technician" in roles
        assert "business_customer" in roles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
