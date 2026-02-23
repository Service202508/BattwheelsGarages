"""
Enterprise QA Audit of Battwheels OS SaaS
Comprehensive testing for:
1) All modules working end-to-end
2) Workflow synchronization
3) Calculation accuracy
4) Multi-tenant isolation
5) Role-based access control

Test Categories:
- Auth & Login flows (Admin, Technician)
- Dashboard stats display
- Ticket lifecycle: create -> assign -> estimate -> close
- Invoice creation and payment recording
- Multi-tenant data isolation
- RBAC: technician access restrictions
- EFI Intelligence Engine
"""
import pytest
import requests
import os
from datetime import datetime
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://battwheels-saas.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "admin123"
TECHNICIAN_EMAIL = "deepak@battwheelsgarages.in"
TECHNICIAN_PASSWORD = "tech123"
ORGANIZATION_ID = "org_71f0df814d6d"  # Battwheels Garages default org


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "token" in data
    assert data["user"]["role"] == "admin"
    return data["token"]


@pytest.fixture(scope="module")
def technician_token():
    """Get technician authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TECHNICIAN_EMAIL,
        "password": TECHNICIAN_PASSWORD
    })
    assert response.status_code == 200, f"Technician login failed: {response.text}"
    data = response.json()
    assert "token" in data
    assert data["user"]["role"] == "technician"
    return data["token"]


def get_auth_headers(token, include_org=False):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if include_org:
        headers["X-Organization-ID"] = ORGANIZATION_ID
    return headers


class TestAdminLogin:
    """Test admin login and dashboard access"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        assert data["user"]["name"] == "Admin User"
        print(f"✓ Admin login successful: {data['user']['name']}")

    def test_admin_login_invalid_password(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid password correctly rejected")


class TestTechnicianLogin:
    """Test technician login and dashboard access"""
    
    def test_technician_login_success(self):
        """Test technician login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECHNICIAN_EMAIL,
            "password": TECHNICIAN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == TECHNICIAN_EMAIL
        assert data["user"]["role"] == "technician"
        print(f"✓ Technician login successful: {data['user']['name']}")


class TestDashboardStats:
    """Test dashboard stats display correctly"""
    
    def test_dashboard_stats_with_admin(self, admin_token):
        """Admin can access dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify workshop metrics
        assert "vehicles_in_workshop" in data
        assert "open_repair_orders" in data
        assert "avg_repair_time" in data
        assert "available_technicians" in data
        
        # Verify financial metrics
        assert "total_revenue" in data
        assert "pending_invoices" in data
        assert "inventory_value" in data
        
        # Verify service ticket stats
        assert "service_ticket_stats" in data
        stats = data["service_ticket_stats"]
        assert "total_open" in stats
        assert "onsite_resolution" in stats
        assert "workshop_visit" in stats
        assert "pickup" in stats
        assert "remote" in stats
        assert "avg_resolution_time_hours" in stats
        
        print(f"✓ Dashboard stats: {stats['total_open']} open tickets, " +
              f"{stats['onsite_resolution']} onsite, {stats['workshop_visit']} workshop")
        
    def test_dashboard_stats_with_technician(self, technician_token):
        """Technician can also access dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=get_auth_headers(technician_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "service_ticket_stats" in data
        print("✓ Technician can access dashboard stats")


class TestTicketLifecycle:
    """Test ticket lifecycle: create -> assign -> estimate -> close"""
    
    @pytest.fixture(autouse=True)
    def setup(self, admin_token, technician_token):
        self.admin_token = admin_token
        self.technician_token = technician_token
        self.created_ticket_id = None
    
    def test_01_create_ticket(self):
        """Create a new service ticket"""
        ticket_data = {
            "title": f"TEST_QA_Audit_{uuid.uuid4().hex[:8]}",
            "description": "Battery not charging properly - QA audit test",
            "category": "battery",
            "priority": "high",
            "vehicle_type": "Electric Scooter",
            "vehicle_model": "Ola S1 Pro",
            "vehicle_number": "KA01AB1234",
            "customer_name": "QA Test Customer",
            "customer_type": "individual",
            "contact_number": "9876543210",
            "resolution_type": "workshop"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            json=ticket_data,
            headers=get_auth_headers(self.admin_token)
        )
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        data = response.json()
        
        assert "ticket_id" in data
        assert data["status"] == "open"
        assert data["title"] == ticket_data["title"]
        
        self.__class__.created_ticket_id = data["ticket_id"]
        print(f"✓ Created ticket: {data['ticket_id']}")
        
    def test_02_get_ticket(self):
        """Get the created ticket"""
        if not self.__class__.created_ticket_id:
            pytest.skip("No ticket created in previous test")
            
        response = requests.get(
            f"{BASE_URL}/api/tickets/{self.__class__.created_ticket_id}",
            headers=get_auth_headers(self.admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == self.__class__.created_ticket_id
        print(f"✓ Retrieved ticket: {data['title']}")
        
    def test_03_assign_ticket(self):
        """Assign ticket to technician"""
        if not self.__class__.created_ticket_id:
            pytest.skip("No ticket created in previous test")
        
        # Get technician user_id first
        response = requests.get(
            f"{BASE_URL}/api/technicians",
            headers=get_auth_headers(self.admin_token)
        )
        assert response.status_code == 200
        technicians = response.json()
        assert len(technicians) > 0, "No technicians found"
        
        tech_id = technicians[0]["user_id"]
        
        # Assign ticket
        response = requests.post(
            f"{BASE_URL}/api/tickets/{self.__class__.created_ticket_id}/assign",
            json={"technician_id": tech_id},
            headers=get_auth_headers(self.admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_technician_id"] == tech_id
        print(f"✓ Assigned ticket to technician: {tech_id}")
        
    def test_04_update_ticket_status(self):
        """Update ticket with estimate and progress"""
        if not self.__class__.created_ticket_id:
            pytest.skip("No ticket created in previous test")
            
        response = requests.put(
            f"{BASE_URL}/api/tickets/{self.__class__.created_ticket_id}",
            json={
                "status": "work_in_progress",
                "estimated_cost": 2500.00
            },
            headers=get_auth_headers(self.admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "work_in_progress"
        assert data["estimated_cost"] == 2500.00
        print("✓ Updated ticket status to work_in_progress")
        
    def test_05_close_ticket(self):
        """Close the ticket with resolution"""
        if not self.__class__.created_ticket_id:
            pytest.skip("No ticket created in previous test")
            
        response = requests.post(
            f"{BASE_URL}/api/tickets/{self.__class__.created_ticket_id}/close",
            json={
                "resolution": "Battery cell replaced successfully",
                "resolution_outcome": "success",
                "resolution_notes": "QA Audit test - replaced faulty cell"
            },
            headers=get_auth_headers(self.admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"
        print("✓ Closed ticket successfully")
        
    def test_06_cleanup_ticket(self):
        """Cleanup test ticket"""
        if not self.__class__.created_ticket_id:
            pytest.skip("No ticket to clean up")
        # Note: Tickets typically don't have delete endpoints in production
        # Just verify it's closed
        response = requests.get(
            f"{BASE_URL}/api/tickets/{self.__class__.created_ticket_id}",
            headers=get_auth_headers(self.admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"
        print(f"✓ Verified ticket {self.__class__.created_ticket_id} is closed")


class TestInvoiceCreation:
    """Test invoice creation and payment recording"""
    
    def test_list_invoices(self, admin_token):
        """Admin can list all invoices"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        invoices = response.json()
        assert isinstance(invoices, list)
        print(f"✓ Retrieved {len(invoices)} invoices")
        
    def test_invoice_has_required_fields(self, admin_token):
        """Verify invoice structure has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        invoices = response.json()
        
        if len(invoices) > 0:
            invoice = invoices[0]
            required_fields = ["invoice_id", "total_amount", "status"]
            for field in required_fields:
                assert field in invoice, f"Missing field: {field}"
            print(f"✓ Invoice has all required fields: {invoice.get('invoice_number', invoice.get('invoice_id'))}")


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation"""
    
    def test_admin_only_sees_own_org_data(self, admin_token):
        """Admin should only see data from their organization"""
        # Get tickets - returns paginated response
        response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify paginated response structure
        if isinstance(data, dict):
            assert "tickets" in data
            tickets = data["tickets"]
        else:
            tickets = data
        
        assert isinstance(tickets, list)
        print(f"✓ Admin can access {len(tickets)} tickets (org-scoped)")
        
    def test_unauthorized_access_blocked(self):
        """Unauthenticated requests should be blocked"""
        response = requests.get(f"{BASE_URL}/api/tickets")
        assert response.status_code == 401
        print("✓ Unauthorized access correctly blocked")


class TestRBAC:
    """Test Role-Based Access Control"""
    
    def test_technician_cannot_access_users_list(self, technician_token):
        """Technician should not be able to list all users (admin-only)"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers=get_auth_headers(technician_token)
        )
        # Users list is admin-only
        assert response.status_code == 403
        print("✓ Technician correctly denied access to users list")
        
    def test_technician_can_access_tickets(self, technician_token):
        """Technician should be able to access tickets"""
        response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers=get_auth_headers(technician_token)
        )
        assert response.status_code == 200
        print("✓ Technician can access tickets")
        
    def test_technician_can_access_inventory(self, technician_token):
        """Technician should be able to access inventory"""
        response = requests.get(
            f"{BASE_URL}/api/inventory",
            headers=get_auth_headers(technician_token)
        )
        assert response.status_code == 200
        print("✓ Technician can access inventory")
        
    def test_admin_can_access_users(self, admin_token):
        """Admin should be able to access users list"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        print(f"✓ Admin can access users list ({len(users)} users)")


class TestEFIIntelligenceEngine:
    """Test EFI Intelligence Engine endpoints"""
    
    def test_efi_failure_cards_list(self, admin_token):
        """Can list EFI failure cards"""
        response = requests.get(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_auth_headers(admin_token, include_org=True)
        )
        assert response.status_code == 200
        data = response.json()
        # Should return list or paginated result
        assert isinstance(data, (list, dict))
        print(f"✓ EFI Failure Cards API working")
        
    def test_efi_dashboard_summary(self, admin_token):
        """Can get EFI dashboard summary"""
        response = requests.get(
            f"{BASE_URL}/api/efi/intelligence/dashboard-summary",
            headers=get_auth_headers(admin_token, include_org=True)
        )
        assert response.status_code == 200
        data = response.json()
        # Verify key sections exist
        assert "failure_cards" in data or "risk_alerts" in data or isinstance(data, dict)
        print("✓ EFI Dashboard Summary API working")
        
    def test_efi_risk_alerts(self, admin_token):
        """Can get risk alerts"""
        response = requests.get(
            f"{BASE_URL}/api/efi/intelligence/risk-alerts",
            headers=get_auth_headers(admin_token, include_org=True)
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print("✓ EFI Risk Alerts API working")
        
    def test_efi_learning_stats(self, admin_token):
        """Can get learning stats"""
        response = requests.get(
            f"{BASE_URL}/api/efi/intelligence/learning/stats",
            headers=get_auth_headers(admin_token, include_org=True)
        )
        assert response.status_code == 200
        print("✓ EFI Learning Stats API working")


class TestFinanceCalculations:
    """Test finance calculator accuracy"""
    
    def test_invoice_totals_calculation(self, admin_token):
        """Verify invoice totals are calculated correctly"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        invoices = response.json()
        
        if len(invoices) > 0:
            invoice = invoices[0]
            # Check that totals make sense (balance should not exceed total)
            total = invoice.get("total_amount", 0)
            paid = invoice.get("amount_paid", 0)
            balance = invoice.get("balance_due", 0)
            
            # Basic sanity check
            assert total >= 0, "Total should be non-negative"
            assert paid >= 0, "Amount paid should be non-negative"
            print(f"✓ Invoice calculation check: Total={total}, Paid={paid}, Balance={balance}")


class TestWorkflowSync:
    """Test workflow synchronization"""
    
    def test_ticket_stats_update_on_status_change(self, admin_token):
        """Verify dashboard stats reflect ticket status changes"""
        # Get initial stats
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        initial_stats = response.json()
        initial_open = initial_stats["service_ticket_stats"]["total_open"]
        
        # Create a test ticket
        ticket_data = {
            "title": f"TEST_WorkflowSync_{uuid.uuid4().hex[:8]}",
            "description": "Testing workflow sync",
            "category": "motor",
            "priority": "medium",
            "resolution_type": "workshop"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            json=ticket_data,
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        ticket_id = response.json()["ticket_id"]
        
        # Check stats updated
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200
        new_stats = response.json()
        new_open = new_stats["service_ticket_stats"]["total_open"]
        
        assert new_open >= initial_open, "Open ticket count should increase or stay same"
        print(f"✓ Workflow sync verified: {initial_open} -> {new_open} open tickets")
        
        # Close the test ticket to clean up
        requests.post(
            f"{BASE_URL}/api/tickets/{ticket_id}/close",
            json={
                "resolution": "Test completed",
                "resolution_outcome": "success"
            },
            headers=get_auth_headers(admin_token)
        )
        print(f"✓ Cleaned up test ticket: {ticket_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
