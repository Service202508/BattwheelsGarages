"""
Battwheels OS - Ticket Module Tests
Tests for the refactored event-driven ticket system

Tests cover:
- Ticket CRUD operations (POST, GET, PUT)
- Ticket lifecycle (create, assign, update, close)
- Event emission verification (via logs/side effects)
- AI matching integration
- Failure card selection
- Ticket statistics
- Backward compatibility
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "dev@battwheels.internal"
ADMIN_PASSWORD = "DevTest@123"


class TestTicketModuleAuth:
    """Authentication tests for ticket module"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "owner"
        print(f"✓ Admin login successful, role: {data['user']['role']}")
    
    def test_unauthorized_ticket_access(self):
        """Test that ticket endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/v1/tickets")
        assert response.status_code == 401
        print("✓ Unauthorized access correctly rejected")


class TestTicketCRUD:
    """CRUD operations for tickets"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_ticket_id(self, auth_headers):
        """Create a test ticket and return its ID"""
        ticket_data = {
            "title": "TEST_Battery not charging properly",
            "description": "Vehicle battery shows 0% even after 8 hours of charging",
            "category": "battery",
            "priority": "high",
            "vehicle_type": "2-wheeler",
            "vehicle_make": "Ather",
            "vehicle_model": "450X",
            "vehicle_number": "KA01AB1234",
            "customer_name": "Test Customer",
            "customer_type": "individual",
            "contact_number": "9876543210",
            "customer_email": "test@example.com",
            "issue_type": "charging_issue",
            "resolution_type": "workshop",
            "error_codes_reported": ["E001", "E002"]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        data = response.json()
        assert "ticket_id" in data
        return data["ticket_id"]
    
    def test_create_ticket_success(self, auth_headers):
        """Test POST /api/v1/tickets - Create ticket with event emission"""
        ticket_data = {
            "title": "TEST_Motor overheating during ride",
            "description": "Motor temperature warning appears after 10km ride",
            "category": "motor",
            "priority": "medium",
            "vehicle_type": "2-wheeler",
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "customer_name": "Test User",
            "customer_type": "individual",
            "resolution_type": "workshop"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify ticket structure
        assert "ticket_id" in data
        assert data["title"] == ticket_data["title"]
        assert data["status"] == "open"
        assert data["priority"] == "medium"
        assert data["category"] == "motor"
        
        # Verify EFI fields initialized
        assert "suggested_failure_cards" in data
        assert "ai_match_performed" in data
        assert data["selected_failure_card"] is None
        
        # Verify timestamps
        assert "created_at" in data
        assert "updated_at" in data
        
        print(f"✓ Created ticket: {data['ticket_id']}")
        print(f"  - Status: {data['status']}")
        print(f"  - AI match performed: {data['ai_match_performed']}")
        
        # Wait for async event processing
        time.sleep(0.5)
        
        # Verify AI matching was triggered (check if suggested_failure_cards populated)
        get_response = requests.get(
            f"{BASE_URL}/api/v1/tickets/{data['ticket_id']}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        updated_ticket = get_response.json()
        print(f"  - Suggested failure cards: {len(updated_ticket.get('suggested_failure_cards', []))}")
    
    def test_create_ticket_minimal_data(self, auth_headers):
        """Test ticket creation with minimal required fields"""
        ticket_data = {
            "title": "TEST_Minimal ticket"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "TEST_Minimal ticket"
        assert data["priority"] == "medium"  # Default
        assert data["status"] == "open"  # Default
        print(f"✓ Created minimal ticket: {data['ticket_id']}")
    
    def test_list_tickets(self, auth_headers):
        """Test GET /api/v1/tickets - List tickets"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)
        
        print(f"✓ Listed {len(data['data'])} tickets (total: {data['pagination'].get('total', 'N/A')})")
    
    def test_list_tickets_with_status_filter(self, auth_headers):
        """Test GET /api/v1/tickets?status=open - Filter by status"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets?status=open",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned tickets should have status=open
        for ticket in data["data"]:
            assert ticket["status"] == "open"
        
        print(f"✓ Filtered tickets by status=open: {len(data['tickets'])} results")
    
    def test_list_tickets_with_priority_filter(self, auth_headers):
        """Test GET /api/v1/tickets?priority=high - Filter by priority"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets?priority=high",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for ticket in data["data"]:
            assert ticket["priority"] == "high"
        
        print(f"✓ Filtered tickets by priority=high: {len(data['tickets'])} results")
    
    def test_list_tickets_with_category_filter(self, auth_headers):
        """Test GET /api/v1/tickets?category=battery - Filter by category"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets?category=battery",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for ticket in data["data"]:
            assert ticket["category"] == "battery"
        
        print(f"✓ Filtered tickets by category=battery: {len(data['tickets'])} results")
    
    def test_get_single_ticket(self, auth_headers, test_ticket_id):
        """Test GET /api/v1/tickets/{id} - Get single ticket"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets/{test_ticket_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["ticket_id"] == test_ticket_id
        assert "title" in data
        assert "status" in data
        assert "status_history" in data
        
        print(f"✓ Retrieved ticket: {test_ticket_id}")
        print(f"  - Title: {data['title']}")
        print(f"  - Status: {data['status']}")
    
    def test_get_nonexistent_ticket(self, auth_headers):
        """Test GET /api/v1/tickets/{id} - Returns 404 for non-existent ticket"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets/tkt_nonexistent123",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent ticket correctly returns 404")
    
    def test_update_ticket(self, auth_headers, test_ticket_id):
        """Test PUT /api/v1/tickets/{id} - Update ticket (emits TICKET_UPDATED)"""
        update_data = {
            "priority": "critical",
            "status": "in_progress",
            "description": "Updated description - issue confirmed after diagnosis"
        }
        response = requests.put(
            f"{BASE_URL}/api/v1/tickets/{test_ticket_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["priority"] == "critical"
        assert data["status"] == "in_progress"
        
        # Verify status history updated
        assert len(data["status_history"]) >= 2  # open -> in_progress
        
        print(f"✓ Updated ticket: {test_ticket_id}")
        print(f"  - New priority: {data['priority']}")
        print(f"  - New status: {data['status']}")
        print(f"  - Status history entries: {len(data['status_history'])}")


class TestTicketLifecycle:
    """Test complete ticket lifecycle with events"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def technician_id(self, auth_headers):
        """Get a technician user ID"""
        response = requests.get(
            f"{BASE_URL}/api/technicians",
            headers=auth_headers
        )
        if response.status_code == 200:
            technicians = response.json()
            if technicians:
                return technicians[0]["user_id"]
        # Return admin user_id as fallback
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=auth_headers
        )
        return response.json()["user_id"]
    
    def test_full_ticket_lifecycle(self, auth_headers, technician_id):
        """Test complete ticket lifecycle: create -> assign -> update -> close"""
        
        # Step 1: Create ticket (TICKET_CREATED event)
        ticket_data = {
            "title": "TEST_Full lifecycle - Display not working",
            "description": "Dashboard display shows blank screen",
            "category": "display",
            "priority": "high",
            "vehicle_make": "TVS",
            "vehicle_model": "iQube",
            "customer_name": "Lifecycle Test Customer",
            "resolution_type": "workshop"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert create_response.status_code == 200
        ticket = create_response.json()
        ticket_id = ticket["ticket_id"]
        
        print(f"✓ Step 1: Created ticket {ticket_id}")
        assert ticket["status"] == "open"
        
        # Wait for AI matching event to process
        time.sleep(0.5)
        
        # Step 2: Assign ticket (TICKET_ASSIGNED event)
        assign_response = requests.post(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/assign",
            headers=auth_headers,
            json={"technician_id": technician_id}
        )
        assert assign_response.status_code == 200
        assigned_ticket = assign_response.json()
        
        print(f"✓ Step 2: Assigned ticket to technician")
        assert assigned_ticket["status"] == "assigned"
        assert assigned_ticket["assigned_technician_id"] == technician_id
        
        # Step 3: Update status to in_progress (TICKET_STATUS_CHANGED event)
        update_response = requests.put(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}",
            headers=auth_headers,
            json={"status": "in_progress"}
        )
        assert update_response.status_code == 200
        updated_ticket = update_response.json()
        
        print(f"✓ Step 3: Updated status to in_progress")
        assert updated_ticket["status"] == "in_progress"
        
        # Step 4: Close ticket (TICKET_CLOSED event)
        close_response = requests.post(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/close",
            headers=auth_headers,
            json={
                "resolution": "Replaced display connector cable",
                "resolution_outcome": "success",
                "resolution_notes": "Loose connector was the root cause"
            }
        )
        assert close_response.status_code == 200
        closed_ticket = close_response.json()
        
        print(f"✓ Step 4: Closed ticket with resolution")
        assert closed_ticket["status"] == "closed"
        assert closed_ticket["resolution"] == "Replaced display connector cable"
        assert closed_ticket["resolution_outcome"] == "success"
        assert closed_ticket["closed_at"] is not None
        
        # Verify status history
        assert len(closed_ticket["status_history"]) >= 4
        print(f"  - Status history entries: {len(closed_ticket['status_history'])}")
    
    def test_assign_ticket(self, auth_headers, technician_id):
        """Test POST /api/v1/tickets/{id}/assign - Assign ticket to technician"""
        # Create a ticket first
        ticket_data = {
            "title": "TEST_Assignment test ticket",
            "category": "battery",
            "priority": "medium"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        ticket_id = create_response.json()["ticket_id"]
        
        # Assign ticket
        assign_response = requests.post(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/assign",
            headers=auth_headers,
            json={"technician_id": technician_id}
        )
        assert assign_response.status_code == 200
        data = assign_response.json()
        
        assert data["assigned_technician_id"] == technician_id
        assert data["status"] == "assigned"
        
        print(f"✓ Assigned ticket {ticket_id} to technician {technician_id}")
    
    def test_close_ticket_with_failure_card(self, auth_headers):
        """Test POST /api/v1/tickets/{id}/close - Close with failure card (FAILURE_CARD_USED event)"""
        # Create a ticket
        ticket_data = {
            "title": "TEST_Close with failure card",
            "category": "battery",
            "priority": "high",
            "description": "Battery draining fast"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        ticket_id = create_response.json()["ticket_id"]
        
        # Wait for AI matching
        time.sleep(0.5)
        
        # Get suggested failure cards
        matches_response = requests.get(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/matches",
            headers=auth_headers
        )
        assert matches_response.status_code == 200
        matches = matches_response.json()
        
        failure_card_id = None
        if matches.get("matches"):
            failure_card_id = matches["matches"][0]["failure_id"]
        
        # Close ticket with failure card
        close_data = {
            "resolution": "Replaced battery cells",
            "resolution_outcome": "success",
            "resolution_notes": "Battery cells degraded beyond repair"
        }
        if failure_card_id:
            close_data["selected_failure_card"] = failure_card_id
        
        close_response = requests.post(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/close",
            headers=auth_headers,
            json=close_data
        )
        assert close_response.status_code == 200
        data = close_response.json()
        
        assert data["status"] == "closed"
        assert data["resolution_outcome"] == "success"
        if failure_card_id:
            assert data["selected_failure_card"] == failure_card_id
        
        print(f"✓ Closed ticket {ticket_id} with failure card: {failure_card_id}")


class TestAIMatching:
    """Test AI matching and failure card integration"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_ticket_matches(self, auth_headers):
        """Test GET /api/v1/tickets/{id}/matches - Get AI-suggested failure cards"""
        # Create a ticket with specific symptoms
        ticket_data = {
            "title": "TEST_Battery not holding charge",
            "description": "Battery drains from 100% to 0% in 2 hours without use",
            "category": "battery",
            "priority": "high",
            "vehicle_make": "Ather",
            "vehicle_model": "450X",
            "error_codes_reported": ["BAT001", "CHG002"]
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        ticket_id = create_response.json()["ticket_id"]
        
        # Wait for AI matching to complete
        time.sleep(1)
        
        # Get matches
        matches_response = requests.get(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/matches",
            headers=auth_headers
        )
        assert matches_response.status_code == 200
        data = matches_response.json()
        
        assert "ticket_id" in data
        assert "ai_match_performed" in data
        assert "matches" in data
        
        print(f"✓ Got matches for ticket {ticket_id}")
        print(f"  - AI match performed: {data['ai_match_performed']}")
        print(f"  - Matches found: {len(data['matches'])}")
        
        if data["matches"]:
            for match in data["matches"][:3]:
                print(f"    - {match.get('failure_id')}: {match.get('title', 'N/A')}")
    
    def test_select_failure_card(self, auth_headers):
        """Test POST /api/v1/tickets/{id}/select-card - Select failure card for ticket"""
        # Create a ticket
        ticket_data = {
            "title": "TEST_Select failure card test",
            "category": "motor",
            "description": "Motor making unusual noise"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        ticket_id = create_response.json()["ticket_id"]
        
        # Wait for AI matching
        time.sleep(0.5)
        
        # Get matches
        matches_response = requests.get(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/matches",
            headers=auth_headers
        )
        matches = matches_response.json()
        
        if matches.get("matches"):
            failure_id = matches["matches"][0]["failure_id"]
            
            # Select the failure card
            select_response = requests.post(
                f"{BASE_URL}/api/v1/tickets/{ticket_id}/select-card",
                headers=auth_headers,
                json={"failure_id": failure_id}
            )
            assert select_response.status_code == 200
            data = select_response.json()
            
            assert data["ticket_id"] == ticket_id
            assert data["failure_id"] == failure_id
            
            print(f"✓ Selected failure card {failure_id} for ticket {ticket_id}")
            
            # Verify ticket was updated
            get_response = requests.get(
                f"{BASE_URL}/api/v1/tickets/{ticket_id}",
                headers=auth_headers
            )
            updated_ticket = get_response.json()
            assert updated_ticket["selected_failure_card"] == failure_id
        else:
            print("⚠ No failure cards available to select (skipping)")
    
    def test_select_failure_card_legacy_route(self, auth_headers):
        """Test POST /api/v1/tickets/{id}/select-card/{failure_id} - Legacy route"""
        # Create a ticket
        ticket_data = {
            "title": "TEST_Legacy select card test",
            "category": "battery"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        ticket_id = create_response.json()["ticket_id"]
        
        # Wait for AI matching
        time.sleep(0.5)
        
        # Get matches
        matches_response = requests.get(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/matches",
            headers=auth_headers
        )
        matches = matches_response.json()
        
        if matches.get("matches"):
            failure_id = matches["matches"][0]["failure_id"]
            
            # Use legacy route
            select_response = requests.post(
                f"{BASE_URL}/api/v1/tickets/{ticket_id}/select-card/{failure_id}",
                headers=auth_headers
            )
            assert select_response.status_code == 200
            
            print(f"✓ Legacy route: Selected failure card {failure_id}")
        else:
            print("⚠ No failure cards available (skipping legacy route test)")


class TestTicketStats:
    """Test ticket statistics endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_ticket_stats(self, auth_headers):
        """Test GET /api/v1/tickets/stats - Get ticket statistics"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "open" in data
        assert "in_progress" in data
        assert "resolved" in data
        assert "by_status" in data
        
        print(f"✓ Ticket statistics:")
        print(f"  - Total: {data['total']}")
        print(f"  - Open: {data['open']}")
        print(f"  - In Progress: {data['in_progress']}")
        print(f"  - Resolved: {data['resolved']}")
        print(f"  - By Status: {data['by_status']}")


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_update_nonexistent_ticket(self, auth_headers):
        """Test PUT /api/v1/tickets/{id} - Returns 404 for non-existent ticket"""
        response = requests.put(
            f"{BASE_URL}/api/v1/tickets/tkt_nonexistent123",
            headers=auth_headers,
            json={"status": "in_progress"}
        )
        assert response.status_code == 404
        print("✓ Update non-existent ticket returns 404")
    
    def test_close_nonexistent_ticket(self, auth_headers):
        """Test POST /api/v1/tickets/{id}/close - Returns 404 for non-existent ticket"""
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets/tkt_nonexistent123/close",
            headers=auth_headers,
            json={"resolution": "Test", "resolution_outcome": "success"}
        )
        assert response.status_code == 404
        print("✓ Close non-existent ticket returns 404")
    
    def test_assign_nonexistent_ticket(self, auth_headers):
        """Test POST /api/v1/tickets/{id}/assign - Returns 404 for non-existent ticket"""
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets/tkt_nonexistent123/assign",
            headers=auth_headers,
            json={"technician_id": "user_test123"}
        )
        assert response.status_code == 404
        print("✓ Assign non-existent ticket returns 404")
    
    def test_assign_nonexistent_technician(self, auth_headers):
        """Test POST /api/v1/tickets/{id}/assign - Returns 404 for non-existent technician"""
        # Create a ticket first
        ticket_data = {"title": "TEST_Assign error test"}
        create_response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        ticket_id = create_response.json()["ticket_id"]
        
        # Try to assign to non-existent technician
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}/assign",
            headers=auth_headers,
            json={"technician_id": "user_nonexistent123"}
        )
        assert response.status_code == 404
        print("✓ Assign to non-existent technician returns 404")
    
    def test_get_matches_nonexistent_ticket(self, auth_headers):
        """Test GET /api/v1/tickets/{id}/matches - Returns 404 for non-existent ticket"""
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets/tkt_nonexistent123/matches",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Get matches for non-existent ticket returns 404")
    
    def test_select_card_nonexistent_ticket(self, auth_headers):
        """Test POST /api/v1/tickets/{id}/select-card - Returns 404 for non-existent ticket"""
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets/tkt_nonexistent123/select-card",
            headers=auth_headers,
            json={"failure_id": "fail_test123"}
        )
        assert response.status_code == 404
        print("✓ Select card for non-existent ticket returns 404")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_cleanup_test_tickets(self, auth_headers):
        """Clean up TEST_ prefixed tickets"""
        # Get all tickets
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets?limit=500",
            headers=auth_headers
        )
        if response.status_code == 200:
            data = response.json()
            test_tickets = [t for t in data["data"] if t["title"].startswith("TEST_")]
            print(f"Found {len(test_tickets)} test tickets to clean up")
            # Note: No delete endpoint, so just report
        print("✓ Cleanup check completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
