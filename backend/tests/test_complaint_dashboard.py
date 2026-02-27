"""
Test suite for Complaint Dashboard and Job Card features
Tests: KPI cards, ticket filtering, search, Job Card dialog, technician assignment
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "DevTest@123"
TECH_EMAIL = "deepak@battwheelsgarages.in"
TECH_PASSWORD = "DevTest@123"


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login returns token and user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["role"] == "admin", "User role should be admin"
        print(f"✓ Admin login successful - user: {data['user']['name']}")
    
    def test_technician_login(self):
        """Test technician login returns token and user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECH_EMAIL,
            "password": TECH_PASSWORD
        })
        assert response.status_code == 200, f"Technician login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert data["user"]["role"] == "technician", "User role should be technician"
        print(f"✓ Technician login successful - user: {data['user']['name']}")


@pytest.fixture
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture
def tech_token():
    """Get technician authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TECH_EMAIL,
        "password": TECH_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Technician authentication failed")


class TestTicketsAPI:
    """Tests for GET /api/tickets endpoint"""
    
    def test_get_all_tickets(self, admin_token):
        """Test fetching all tickets"""
        response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to get tickets: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/tickets - returned {len(data)} tickets")
        
        # Verify ticket structure if tickets exist
        if len(data) > 0:
            ticket = data[0]
            required_fields = ["ticket_id", "title", "status", "priority"]
            for field in required_fields:
                assert field in ticket, f"Missing field: {field}"
            print(f"✓ Ticket structure verified - has required fields")
    
    def test_get_tickets_by_status_open(self, admin_token):
        """Test filtering tickets by status=open"""
        response = requests.get(
            f"{BASE_URL}/api/tickets?status=open",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to filter tickets: {response.text}"
        data = response.json()
        
        # All returned tickets should have status=open
        for ticket in data:
            assert ticket["status"] == "open", f"Ticket {ticket['ticket_id']} has status {ticket['status']}, expected 'open'"
        print(f"✓ GET /api/tickets?status=open - returned {len(data)} open tickets")
    
    def test_get_tickets_by_status_technician_assigned(self, admin_token):
        """Test filtering tickets by status=technician_assigned"""
        response = requests.get(
            f"{BASE_URL}/api/tickets?status=technician_assigned",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to filter tickets: {response.text}"
        data = response.json()
        
        for ticket in data:
            assert ticket["status"] == "technician_assigned", f"Ticket status mismatch"
        print(f"✓ GET /api/tickets?status=technician_assigned - returned {len(data)} tickets")
    
    def test_get_tickets_by_status_in_progress(self, admin_token):
        """Test filtering tickets by status=in_progress"""
        response = requests.get(
            f"{BASE_URL}/api/tickets?status=in_progress",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to filter tickets: {response.text}"
        data = response.json()
        
        for ticket in data:
            assert ticket["status"] == "in_progress", f"Ticket status mismatch"
        print(f"✓ GET /api/tickets?status=in_progress - returned {len(data)} tickets")
    
    def test_get_tickets_by_status_resolved(self, admin_token):
        """Test filtering tickets by status=resolved"""
        response = requests.get(
            f"{BASE_URL}/api/tickets?status=resolved",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to filter tickets: {response.text}"
        data = response.json()
        
        for ticket in data:
            assert ticket["status"] == "resolved", f"Ticket status mismatch"
        print(f"✓ GET /api/tickets?status=resolved - returned {len(data)} tickets")
    
    def test_unauthorized_access(self):
        """Test that unauthorized access returns 401"""
        response = requests.get(f"{BASE_URL}/api/tickets")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthorized access returns 401")


class TestTicketDetails:
    """Tests for GET /api/tickets/{ticket_id} endpoint"""
    
    def test_get_ticket_by_id(self, admin_token):
        """Test fetching a specific ticket by ID"""
        # First get list of tickets
        list_response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert list_response.status_code == 200
        tickets = list_response.json()
        
        if len(tickets) == 0:
            pytest.skip("No tickets available to test")
        
        ticket_id = tickets[0]["ticket_id"]
        
        # Get specific ticket
        response = requests.get(
            f"{BASE_URL}/api/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to get ticket: {response.text}"
        data = response.json()
        
        assert data["ticket_id"] == ticket_id, "Ticket ID mismatch"
        
        # Verify essential Job Card fields (some may be null but should exist in schema)
        essential_fields = ["ticket_id", "title", "priority", "status", "created_at"]
        for field in essential_fields:
            assert field in data, f"Missing essential field: {field}"
        
        # Optional fields that may or may not be present depending on ticket data
        optional_fields = [
            "customer_name", "customer_email", "contact_number",
            "vehicle_number", "vehicle_type", "vehicle_model",
            "assigned_technician_name", "description"
        ]
        present_optional = [f for f in optional_fields if f in data and data[f] is not None]
        print(f"  - Optional fields present: {present_optional}")
        
        print(f"✓ GET /api/tickets/{ticket_id} - ticket details retrieved")
        print(f"  - Customer: {data.get('customer_name', 'N/A')}")
        print(f"  - Vehicle: {data.get('vehicle_number', 'N/A')}")
        print(f"  - Status: {data.get('status', 'N/A')}")
    
    def test_get_nonexistent_ticket(self, admin_token):
        """Test fetching a non-existent ticket returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/tickets/nonexistent_ticket_id",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent ticket returns 404")


class TestTechniciansAPI:
    """Tests for GET /api/technicians endpoint"""
    
    def test_get_technicians(self, admin_token):
        """Test fetching list of technicians"""
        response = requests.get(
            f"{BASE_URL}/api/technicians",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to get technicians: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify technician structure
        if len(data) > 0:
            tech = data[0]
            assert "user_id" in tech, "Missing user_id"
            assert "name" in tech, "Missing name"
            assert tech.get("role") == "technician", "Role should be technician"
        
        print(f"✓ GET /api/technicians - returned {len(data)} technicians")
        for tech in data:
            print(f"  - {tech.get('name', 'N/A')} ({tech.get('email', 'N/A')})")


class TestTicketUpdate:
    """Tests for PUT /api/tickets/{ticket_id} endpoint"""
    
    def test_assign_technician_to_ticket(self, admin_token):
        """Test assigning a technician to an open ticket"""
        # Get list of tickets
        tickets_response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        tickets = tickets_response.json()
        
        # Find an open ticket
        open_ticket = None
        for t in tickets:
            if t["status"] == "open":
                open_ticket = t
                break
        
        if not open_ticket:
            pytest.skip("No open tickets available to test assignment")
        
        # Get technicians
        tech_response = requests.get(
            f"{BASE_URL}/api/technicians",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        technicians = tech_response.json()
        
        if len(technicians) == 0:
            pytest.skip("No technicians available")
        
        tech = technicians[0]
        
        # Assign technician
        response = requests.put(
            f"{BASE_URL}/api/tickets/{open_ticket['ticket_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "status": "technician_assigned",
                "assigned_technician_id": tech["user_id"]
            }
        )
        assert response.status_code == 200, f"Failed to assign technician: {response.text}"
        data = response.json()
        
        assert data["status"] == "technician_assigned", "Status should be technician_assigned"
        assert data["assigned_technician_id"] == tech["user_id"], "Technician ID mismatch"
        assert data.get("assigned_technician_name") is not None, "Technician name should be set"
        
        print(f"✓ Assigned technician {tech['name']} to ticket {open_ticket['ticket_id']}")
        print(f"  - New status: {data['status']}")
    
    def test_update_ticket_status_to_in_progress(self, admin_token):
        """Test updating ticket status to in_progress"""
        # Get tickets with technician_assigned status
        tickets_response = requests.get(
            f"{BASE_URL}/api/tickets?status=technician_assigned",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        tickets = tickets_response.json()
        
        if len(tickets) == 0:
            pytest.skip("No technician_assigned tickets available")
        
        ticket = tickets[0]
        
        # Update to in_progress
        response = requests.put(
            f"{BASE_URL}/api/tickets/{ticket['ticket_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "in_progress"}
        )
        assert response.status_code == 200, f"Failed to update status: {response.text}"
        data = response.json()
        
        assert data["status"] == "in_progress", "Status should be in_progress"
        print(f"✓ Updated ticket {ticket['ticket_id']} to in_progress")
    
    def test_update_ticket_with_estimated_items(self, admin_token):
        """Test updating ticket with estimated items"""
        # Get any ticket
        tickets_response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        tickets = tickets_response.json()
        
        if len(tickets) == 0:
            pytest.skip("No tickets available")
        
        ticket = tickets[0]
        
        # Update with estimated items
        estimated_items = {
            "parts": [
                {"item_id": "test_part_1", "name": "Battery Cell", "quantity": 2, "unit_price": 5000, "gst_rate": 18}
            ],
            "services": [
                {"service_id": "test_service_1", "name": "Battery Diagnostic", "quantity": 1, "unit_price": 1500, "gst_rate": 18}
            ]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/tickets/{ticket['ticket_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"estimated_items": estimated_items}
        )
        assert response.status_code == 200, f"Failed to update estimated items: {response.text}"
        data = response.json()
        
        # Verify estimated_items were saved
        if "estimated_items" in data:
            assert data["estimated_items"] == estimated_items, "Estimated items mismatch"
            print(f"✓ Updated ticket {ticket['ticket_id']} with estimated items")
        else:
            print(f"✓ Ticket update successful (estimated_items may not be returned)")


class TestInventoryAPI:
    """Tests for GET /api/inventory endpoint (used in Job Card)"""
    
    def test_get_inventory(self, admin_token):
        """Test fetching inventory items"""
        response = requests.get(
            f"{BASE_URL}/api/inventory",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to get inventory: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/inventory - returned {len(data)} items")
        if len(data) > 0:
            item = data[0]
            print(f"  - Sample item: {item.get('name', 'N/A')} (₹{item.get('unit_price', 0)})")


class TestServicesAPI:
    """Tests for GET /api/services endpoint (used in Job Card)"""
    
    def test_get_services(self, admin_token):
        """Test fetching service offerings"""
        response = requests.get(
            f"{BASE_URL}/api/services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to get services: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/services - returned {len(data)} services")
        if len(data) > 0:
            service = data[0]
            print(f"  - Sample service: {service.get('name', 'N/A')} (₹{service.get('base_price', 0)})")


class TestKPIData:
    """Tests for KPI card data calculation"""
    
    def test_kpi_counts(self, admin_token):
        """Test that KPI counts can be calculated from tickets"""
        response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        tickets = response.json()
        
        # Calculate KPI counts
        open_count = len([t for t in tickets if t["status"] == "open"])
        tech_assigned_count = len([t for t in tickets if t["status"] == "technician_assigned"])
        estimate_shared_count = len([t for t in tickets if t["status"] == "estimate_shared"])
        in_progress_count = len([t for t in tickets if t["status"] == "in_progress"])
        
        # Calculate resolved this week
        one_week_ago = datetime.now() - timedelta(days=7)
        resolved_this_week = 0
        for t in tickets:
            if t["status"] == "resolved" and t.get("updated_at"):
                try:
                    updated = datetime.fromisoformat(t["updated_at"].replace("Z", "+00:00"))
                    if updated.replace(tzinfo=None) >= one_week_ago:
                        resolved_this_week += 1
                except:
                    pass
        
        print(f"✓ KPI Data calculated from {len(tickets)} tickets:")
        print(f"  - Open: {open_count}")
        print(f"  - Technician Assigned: {tech_assigned_count}")
        print(f"  - Awaiting Approval (Estimate Shared): {estimate_shared_count}")
        print(f"  - Work In Progress: {in_progress_count}")
        print(f"  - Resolved This Week: {resolved_this_week}")


class TestTicketCreation:
    """Tests for POST /api/tickets endpoint"""
    
    def test_create_ticket(self, admin_token):
        """Test creating a new ticket"""
        ticket_data = {
            "title": "TEST_Battery not charging properly",
            "description": "Customer reports battery not holding charge after overnight charging",
            "priority": "high",
            "category": "battery",
            "vehicle_type": "two_wheeler",
            "vehicle_model": "Ather 450X",
            "vehicle_number": "KA01AB1234",
            "customer_name": "TEST_John Doe",
            "customer_email": "test.john@example.com",
            "contact_number": "9876543210",
            "customer_type": "individual",
            "resolution_type": "workshop",
            "issue_type": "battery"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=ticket_data
        )
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        data = response.json()
        
        assert "ticket_id" in data, "ticket_id not in response"
        assert data["title"] == ticket_data["title"], "Title mismatch"
        assert data["status"] == "open", "New ticket should have status 'open'"
        assert data["customer_name"] == ticket_data["customer_name"], "Customer name mismatch"
        
        # Verify status_history is initialized
        if "status_history" in data:
            assert len(data["status_history"]) > 0, "Status history should have initial entry"
            assert data["status_history"][0]["status"] == "open", "First status should be 'open'"
        
        print(f"✓ Created ticket: {data['ticket_id']}")
        print(f"  - Title: {data['title']}")
        print(f"  - Status: {data['status']}")
        
        return data["ticket_id"]


class TestInvoiceGeneration:
    """Tests for POST /api/invoices endpoint (used in Job Card)"""
    
    def test_invoice_endpoint_exists(self, admin_token):
        """Test that invoice endpoint is accessible"""
        # Just verify the endpoint exists and requires proper data
        response = requests.post(
            f"{BASE_URL}/api/invoices",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={}  # Empty body to test validation
        )
        # Should return 422 (validation error) or 404 (ticket not found), not 500
        assert response.status_code in [400, 404, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ POST /api/invoices endpoint accessible (returns {response.status_code} for invalid data)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
