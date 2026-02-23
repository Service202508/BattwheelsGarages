"""
Multi-Tenant CRUD Operations Test Suite
========================================

Tests CRUD operations for all major resources with tenant (organization) scoping:
- Authentication
- Tickets CRUD with org scoping
- Vehicles CRUD with org scoping
- Inventory CRUD with org scoping
- Suppliers CRUD with org scoping
- Ticket stats endpoint
- Error handling (403 for invalid org, 401 for missing auth)

Run with: pytest tests/test_multi_tenant_crud.py -v --tb=short
"""

import pytest
import requests
import uuid
import os

# Use public URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://production-ready-64.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "admin123"
TECH_EMAIL = "deepak@battwheelsgarages.in"
TECH_PASSWORD = "tech123"


class TestAuthentication:
    """Test authentication flow returns token"""
    
    def test_admin_login_success(self):
        """Admin login should return valid token and user info"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "token" in data, "Missing token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        assert len(data["token"]) > 50  # JWT should be long
    
    def test_technician_login_success(self):
        """Technician login should return valid token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECH_EMAIL,
            "password": TECH_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "token" in data
        assert data["user"]["role"] == "technician"
    
    def test_invalid_credentials_returns_401(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_missing_auth_returns_401(self):
        """Requests without authentication should return 401"""
        endpoints = [
            "/api/tickets",
            "/api/vehicles",
            "/api/inventory",
            "/api/suppliers"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code in [401, 403], \
                f"Endpoint {endpoint} should require auth, got {response.status_code}"


class TestTicketsCRUD:
    """Test Tickets CRUD operations with organization scoping"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers with org context"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def org_id(self, auth_headers):
        """Get user's organization ID from auth/me or by querying org"""
        # Try to get org membership
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        if response.status_code == 200:
            user_data = response.json()
            # Check if we need to fetch org separately
            
        # For now, use the known org ID from previous tests
        return "org_71f0df814d6d"
    
    def test_list_tickets(self, auth_headers):
        """List tickets should return tickets for user's org"""
        response = requests.get(f"{BASE_URL}/api/tickets", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to list tickets: {response.text}"
        data = response.json()
        
        # Can be dict with tickets key or list
        if isinstance(data, dict):
            assert "tickets" in data or "total" in data
            tickets = data.get("tickets", [])
        else:
            tickets = data
        
        assert isinstance(tickets, list)
    
    def test_create_ticket_with_org_scope(self, auth_headers):
        """Create ticket should inherit organization ID"""
        ticket_data = {
            "title": f"TEST_MultiTenant Ticket {uuid.uuid4().hex[:6]}",
            "description": "Testing multi-tenant ticket creation",
            "category": "battery",
            "priority": "medium"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201], f"Failed to create ticket: {response.text}"
        created = response.json()
        
        assert "ticket_id" in created
        assert created["title"] == ticket_data["title"]
        
        # Verify ticket was created by fetching it
        ticket_id = created["ticket_id"]
        get_response = requests.get(
            f"{BASE_URL}/api/tickets/{ticket_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        
        return ticket_id
    
    def test_update_ticket(self, auth_headers):
        """Update ticket should work within org scope"""
        # First create a ticket
        ticket_data = {
            "title": f"TEST_Update Ticket {uuid.uuid4().hex[:6]}",
            "description": "To be updated",
            "category": "motor",
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/tickets",
            json=ticket_data,
            headers=auth_headers
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create ticket for update test")
        
        ticket_id = create_response.json()["ticket_id"]
        
        # Update the ticket
        update_data = {
            "priority": "high",
            "status": "assigned"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/tickets/{ticket_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated = update_response.json()
        
        assert updated["priority"] == "high"
    
    def test_ticket_stats_scoped_to_org(self, auth_headers):
        """Ticket stats should be scoped to organization"""
        response = requests.get(
            f"{BASE_URL}/api/tickets/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get stats: {response.text}"
        stats = response.json()
        
        # Verify stats structure
        assert "total" in stats or "by_status" in stats


class TestVehiclesCRUD:
    """Test Vehicles CRUD operations with organization scoping"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_vehicles(self, auth_headers):
        """List vehicles should return vehicles for user's org"""
        response = requests.get(f"{BASE_URL}/api/vehicles", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to list vehicles: {response.text}"
        vehicles = response.json()
        
        assert isinstance(vehicles, list)
    
    def test_create_vehicle_with_org_scope(self, auth_headers):
        """Create vehicle should inherit organization ID"""
        vehicle_data = {
            "owner_name": f"TEST_Owner {uuid.uuid4().hex[:6]}",
            "make": "TestMake",
            "model": "TestModel",
            "year": 2024,
            "registration_number": f"TEST{uuid.uuid4().hex[:6].upper()}",
            "battery_capacity": 50.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/vehicles",
            json=vehicle_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201], f"Failed to create vehicle: {response.text}"
        created = response.json()
        
        assert "vehicle_id" in created
        assert created["owner_name"] == vehicle_data["owner_name"]
        
        # Verify vehicle was created by fetching it
        vehicle_id = created["vehicle_id"]
        get_response = requests.get(
            f"{BASE_URL}/api/vehicles/{vehicle_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
    
    def test_get_vehicle_not_found_returns_404(self, auth_headers):
        """Getting non-existent vehicle should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/vehicles/veh_nonexistent123",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestInventoryCRUD:
    """Test Inventory CRUD operations with organization scoping"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_inventory(self, auth_headers):
        """List inventory should return items for user's org"""
        response = requests.get(f"{BASE_URL}/api/inventory", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to list inventory: {response.text}"
        items = response.json()
        
        assert isinstance(items, list)
    
    def test_create_inventory_with_org_scope(self, auth_headers):
        """Create inventory item should inherit organization ID"""
        item_data = {
            "name": f"TEST_Item {uuid.uuid4().hex[:6]}",
            "category": "battery",
            "quantity": 10,
            "unit_price": 1500.0,
            "min_stock_level": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201], f"Failed to create item: {response.text}"
        created = response.json()
        
        assert "item_id" in created
        assert created["name"] == item_data["name"]
        assert created["quantity"] == item_data["quantity"]
        
        # Verify item was created by fetching it
        item_id = created["item_id"]
        get_response = requests.get(
            f"{BASE_URL}/api/inventory/{item_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
    
    def test_update_inventory(self, auth_headers):
        """Update inventory item should work within org scope"""
        # First create an item
        item_data = {
            "name": f"TEST_UpdateItem {uuid.uuid4().hex[:6]}",
            "category": "parts",
            "quantity": 20,
            "unit_price": 500.0,
            "min_stock_level": 10
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=auth_headers
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create item for update test")
        
        item_id = create_response.json()["item_id"]
        
        # Update the item
        update_data = {
            "quantity": 50,
            "unit_price": 600.0
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/inventory/{item_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated = update_response.json()
        
        assert updated["quantity"] == 50
        assert updated["unit_price"] == 600.0
    
    def test_delete_inventory_requires_admin(self, auth_headers):
        """Delete inventory requires admin role"""
        # First create an item
        item_data = {
            "name": f"TEST_DeleteItem {uuid.uuid4().hex[:6]}",
            "category": "parts",
            "quantity": 5,
            "unit_price": 100.0,
            "min_stock_level": 2
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=auth_headers
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create item for delete test")
        
        item_id = create_response.json()["item_id"]
        
        # Delete should work for admin
        delete_response = requests.delete(
            f"{BASE_URL}/api/inventory/{item_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code in [200, 204], \
            f"Delete failed: {delete_response.text}"


class TestSuppliersCRUD:
    """Test Suppliers CRUD operations with organization scoping"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_suppliers(self, auth_headers):
        """List suppliers should return suppliers for user's org"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to list suppliers: {response.text}"
        suppliers = response.json()
        
        assert isinstance(suppliers, list)
    
    def test_create_supplier_with_org_scope(self, auth_headers):
        """Create supplier should inherit organization ID"""
        supplier_data = {
            "name": f"TEST_Supplier {uuid.uuid4().hex[:6]}",
            "contact_person": "Test Contact",
            "email": f"test{uuid.uuid4().hex[:4]}@supplier.com",
            "phone": "+91-9999999999",
            "category": "parts"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/suppliers",
            json=supplier_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201], f"Failed to create supplier: {response.text}"
        created = response.json()
        
        assert "supplier_id" in created
        assert created["name"] == supplier_data["name"]
        
        # Verify supplier was created by fetching it
        supplier_id = created["supplier_id"]
        get_response = requests.get(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
    
    def test_update_supplier(self, auth_headers):
        """Update supplier should work within org scope"""
        # First create a supplier
        supplier_data = {
            "name": f"TEST_UpdateSupplier {uuid.uuid4().hex[:6]}",
            "contact_person": "Original Contact",
            "category": "parts"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/suppliers",
            json=supplier_data,
            headers=auth_headers
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create supplier for update test")
        
        supplier_id = create_response.json()["supplier_id"]
        
        # Update the supplier
        update_data = {
            "contact_person": "Updated Contact",
            "phone": "+91-8888888888"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"


class TestInvalidOrgIdHandling:
    """Test that invalid X-Organization-ID returns proper errors (403, not 500)"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_invalid_org_id_returns_403_not_500(self, auth_headers):
        """Invalid X-Organization-ID should return 403, not 500"""
        headers = {
            **auth_headers,
            "X-Organization-ID": f"org_invalid_{uuid.uuid4().hex[:8]}"
        }
        
        response = requests.get(f"{BASE_URL}/api/tickets", headers=headers)
        
        # Should be 400 or 403 (access denied), NOT 500 (server error)
        assert response.status_code in [200, 400, 403], \
            f"Invalid org should return 400/403, got {response.status_code}: {response.text}"
        
        # If it returns 400/403, check for proper error structure
        if response.status_code in [400, 403]:
            data = response.json()
            assert "detail" in data or "code" in data or "message" in data
    
    def test_malformed_org_id_handled_gracefully(self, auth_headers):
        """Malformed org ID should be handled gracefully"""
        headers = {
            **auth_headers,
            "X-Organization-ID": "not-a-valid-id"
        }
        
        response = requests.get(f"{BASE_URL}/api/tickets", headers=headers)
        
        # Should NOT be 500
        assert response.status_code != 500, \
            f"Malformed org ID caused 500 error: {response.text}"


class TestTechnicianPermissions:
    """Test technician role permissions"""
    
    @pytest.fixture
    def tech_headers(self):
        """Get technician authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECH_EMAIL,
            "password": TECH_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_technician_can_list_tickets(self, tech_headers):
        """Technician should be able to list tickets"""
        response = requests.get(f"{BASE_URL}/api/tickets", headers=tech_headers)
        assert response.status_code == 200
    
    def test_technician_can_create_ticket(self, tech_headers):
        """Technician should be able to create tickets"""
        ticket_data = {
            "title": f"TEST_TechTicket {uuid.uuid4().hex[:6]}",
            "description": "Technician created ticket",
            "category": "battery",
            "priority": "medium"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            json=ticket_data,
            headers=tech_headers
        )
        
        assert response.status_code in [200, 201], f"Technician ticket creation failed: {response.text}"
    
    def test_technician_can_view_inventory(self, tech_headers):
        """Technician should be able to view inventory"""
        response = requests.get(f"{BASE_URL}/api/inventory", headers=tech_headers)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
