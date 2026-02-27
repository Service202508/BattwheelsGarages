"""
Test file for new features in iteration 64:
1. GET /api/inventory-enhanced/stock - Bug fix for 404 error
2. Organization Settings Export/Import
3. Customer Portal Support Tickets
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestInventoryEnhancedStock:
    """Test the fixed /api/inventory-enhanced/stock endpoint (was 404, now should be 200)"""
    
    def test_stock_endpoint_returns_200(self):
        """Bug fix test: GET /api/inventory-enhanced/stock should return 200 with stock data"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/stock")
        print(f"Stock endpoint status: {response.status_code}")
        print(f"Stock response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "code" in data
        assert data["code"] == 0
        assert "stock" in data
        assert isinstance(data["stock"], list)
        print(f"Stock items count: {len(data['stock'])}")
    
    def test_stock_endpoint_with_warehouse_filter(self):
        """Test stock endpoint with optional warehouse_id filter"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/stock", params={"warehouse_id": "WH-TEST-123"})
        print(f"Stock with warehouse filter status: {response.status_code}")
        
        # Should still return 200 even with non-existent warehouse (empty list)
        assert response.status_code == 200
        data = response.json()
        assert "stock" in data


class TestOrganizationSettingsExportImport:
    """Test organization settings export and import functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        if login_response.status_code == 200:
            return login_response.json().get("token")
        return None
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get authorization headers"""
        if auth_token:
            return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}
    
    def test_export_organization_settings(self, auth_headers):
        """Test GET /api/org/settings/export returns JSON with org and settings data"""
        response = requests.get(f"{BASE_URL}/api/org/settings/export", headers=auth_headers)
        print(f"Export settings status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text[:300]}"
        
        data = response.json()
        
        # Validate export structure
        assert "export_version" in data, "Missing export_version"
        assert "export_date" in data, "Missing export_date"
        assert "organization" in data, "Missing organization section"
        assert "settings" in data, "Missing settings section"
        
        # Validate organization data
        org = data["organization"]
        assert "name" in org
        assert "email" in org or org.get("email") is None  # email can be None
        
        # Validate settings data
        settings = data["settings"]
        assert "currency" in settings
        assert "timezone" in settings
        print(f"Export contains org: {org.get('name')}, currency: {settings.get('currency')}")
    
    def test_import_organization_settings(self, auth_headers):
        """Test POST /api/org/settings/import accepts JSON and updates settings"""
        # First export to get current settings
        export_response = requests.get(f"{BASE_URL}/api/org/settings/export", headers=auth_headers)
        assert export_response.status_code == 200
        export_data = export_response.json()
        
        # Modify a setting for import test
        import_data = {
            "export_version": "1.0",
            "organization": {
                "name": export_data.get("organization", {}).get("name"),
            },
            "settings": {
                "currency": export_data.get("settings", {}).get("currency", "INR"),
                "timezone": export_data.get("settings", {}).get("timezone", "Asia/Kolkata"),
            }
        }
        
        # Import the settings
        response = requests.post(f"{BASE_URL}/api/org/settings/import", 
                                headers=auth_headers, 
                                json=import_data)
        print(f"Import settings status: {response.status_code}")
        print(f"Import response: {response.text[:300]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "message" in data
        assert "imported" in data["message"].lower() or "success" in data["message"].lower()
    
    def test_import_invalid_format_rejected(self, auth_headers):
        """Test that import rejects invalid format"""
        invalid_data = {"invalid": "data", "no_export_version": True}
        
        response = requests.post(f"{BASE_URL}/api/org/settings/import", 
                                headers=auth_headers, 
                                json=invalid_data)
        print(f"Import invalid format status: {response.status_code}")
        
        assert response.status_code == 400, f"Expected 400 for invalid format, got {response.status_code}"


class TestCustomerPortalTickets:
    """Test customer portal support ticket functionality"""
    
    @pytest.fixture
    def portal_contact_setup(self):
        """Setup: Create a test contact with portal access"""
        # Login as admin to create contact with portal access
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        if login_response.status_code != 200:
            pytest.skip("Cannot login as admin")
            return None
        
        admin_token = login_response.json().get("token")
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        # Create a test contact with portal enabled
        import uuid
        test_email = f"test_portal_{uuid.uuid4().hex[:8]}@example.com"
        portal_token = f"PORTAL-{uuid.uuid4().hex[:16].upper()}"
        
        contact_data = {
            "contact_name": "TEST Portal Customer",
            "first_name": "TEST",
            "last_name": "Customer",
            "display_name": "TEST Portal Customer",
            "email": test_email,
            "phone": "+919876543210",
            "contact_type": "customer",
            "company_name": "TEST Company",
            "portal_enabled": True,
            "portal_token": portal_token,
            "status": "active"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/contacts-v2/", 
                                       headers=headers, 
                                       json=contact_data)
        
        if create_response.status_code in [200, 201]:
            contact = create_response.json().get("contact", create_response.json())
            return {
                "contact_id": contact.get("contact_id"),
                "portal_token": portal_token,
                "admin_headers": headers
            }
        
        return None
    
    @pytest.fixture
    def portal_session(self, portal_contact_setup):
        """Login to portal and get session token"""
        if not portal_contact_setup:
            pytest.skip("No portal contact setup")
            return None
        
        login_response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": portal_contact_setup["portal_token"]
        })
        
        if login_response.status_code == 200:
            session = login_response.json()
            return {
                "session_token": session.get("session_token"),
                "contact": session.get("contact"),
                "admin_headers": portal_contact_setup["admin_headers"]
            }
        
        print(f"Portal login failed: {login_response.status_code} - {login_response.text}")
        return None
    
    def test_portal_login(self, portal_contact_setup):
        """Test customer portal login with token"""
        if not portal_contact_setup:
            pytest.skip("No portal contact available")
        
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": portal_contact_setup["portal_token"]
        })
        print(f"Portal login status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "session_token" in data
        assert "contact" in data
        print(f"Portal session created for: {data['contact'].get('name')}")
    
    def test_get_customer_tickets_empty(self, portal_session):
        """Test GET /api/customer-portal/tickets returns list (can be empty)"""
        if not portal_session:
            pytest.skip("No portal session")
        
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/tickets",
            params={"session_token": portal_session["session_token"]}
        )
        print(f"Get tickets status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)
        print(f"Customer tickets count: {len(data['tickets'])}")
    
    def test_create_support_ticket(self, portal_session):
        """Test POST /api/customer-portal/tickets creates new support request"""
        if not portal_session:
            pytest.skip("No portal session")
        
        ticket_data = {
            "subject": "TEST: Battery not charging",
            "description": "My EV battery is not charging properly after the latest software update. Need assistance.",
            "priority": "high",
            "category": "technical"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/customer-portal/tickets",
            params={"session_token": portal_session["session_token"]},
            json=ticket_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Create ticket status: {response.status_code}")
        print(f"Create ticket response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "ticket" in data
        ticket = data["ticket"]
        assert "ticket_id" in ticket
        assert ticket["subject"] == ticket_data["subject"]
        assert ticket["status"] == "open"
        assert ticket["priority"] == "high"
        assert ticket["source"] == "customer_portal"
        
        print(f"Created ticket: {ticket['ticket_id']}")
        return ticket["ticket_id"]
    
    def test_get_ticket_detail(self, portal_session):
        """Test GET /api/customer-portal/tickets/{ticket_id} returns ticket with updates"""
        if not portal_session:
            pytest.skip("No portal session")
        
        # First create a ticket
        ticket_data = {
            "subject": "TEST: Detail test",
            "description": "Testing ticket detail endpoint",
            "priority": "medium",
            "category": "general"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/customer-portal/tickets",
            params={"session_token": portal_session["session_token"]},
            json=ticket_data,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create ticket for detail test")
        
        ticket_id = create_response.json()["ticket"]["ticket_id"]
        
        # Now get the ticket detail
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/tickets/{ticket_id}",
            params={"session_token": portal_session["session_token"]}
        )
        print(f"Get ticket detail status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "ticket" in data
        ticket = data["ticket"]
        assert ticket["ticket_id"] == ticket_id
        assert "updates" in ticket  # Should have updates array (can be empty)
        print(f"Ticket detail retrieved: {ticket_id}, updates: {len(ticket.get('updates', []))}")
    
    def test_add_ticket_comment(self, portal_session):
        """Test POST /api/customer-portal/tickets/{ticket_id}/comment adds comment"""
        if not portal_session:
            pytest.skip("No portal session")
        
        # First create a ticket
        ticket_data = {
            "subject": "TEST: Comment test",
            "description": "Testing comment functionality",
            "priority": "low",
            "category": "service"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/customer-portal/tickets",
            params={"session_token": portal_session["session_token"]},
            json=ticket_data,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create ticket for comment test")
        
        ticket_id = create_response.json()["ticket"]["ticket_id"]
        
        # Add a comment
        comment_text = "TEST: This is a customer comment from the portal"
        response = requests.post(
            f"{BASE_URL}/api/customer-portal/tickets/{ticket_id}/comment",
            params={
                "session_token": portal_session["session_token"],
                "comment": comment_text
            }
        )
        print(f"Add comment status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower() or "added" in data["message"].lower()
        print(f"Comment added to ticket: {ticket_id}")
    
    def test_get_customer_vehicles(self, portal_session):
        """Test GET /api/customer-portal/vehicles returns customer vehicles"""
        if not portal_session:
            pytest.skip("No portal session")
        
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/vehicles",
            params={"session_token": portal_session["session_token"]}
        )
        print(f"Get vehicles status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "vehicles" in data
        assert isinstance(data["vehicles"], list)
        print(f"Customer vehicles count: {len(data['vehicles'])}")


class TestOrganizationSwitcher:
    """Test organization management and switching"""
    
    @pytest.fixture
    def auth_headers(self):
        """Login and get auth headers"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "DevTest@123"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return {}
    
    def test_get_current_organization(self, auth_headers):
        """Test GET /api/org returns current organization"""
        response = requests.get(f"{BASE_URL}/api/org", headers=auth_headers)
        print(f"Get org status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "organization_id" in data or "name" in data
        print(f"Current org: {data.get('name', data.get('organization_id'))}")
    
    def test_list_user_organizations(self, auth_headers):
        """Test GET /api/org/list returns user's organizations"""
        response = requests.get(f"{BASE_URL}/api/org/list", headers=auth_headers)
        print(f"List orgs status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "organizations" in data
        print(f"User has {len(data['organizations'])} organization(s)")
    
    def test_get_organization_settings(self, auth_headers):
        """Test GET /api/org/settings returns settings"""
        response = requests.get(f"{BASE_URL}/api/org/settings", headers=auth_headers)
        print(f"Get settings status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        # Check for common settings fields
        assert "currency" in data or "timezone" in data or "organization_id" in data
    
    def test_get_roles(self, auth_headers):
        """Test GET /api/org/roles returns available roles"""
        response = requests.get(f"{BASE_URL}/api/org/roles", headers=auth_headers)
        print(f"Get roles status: {response.status_code}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "roles" in data
        print(f"Available roles: {[r['role'] for r in data['roles']]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
