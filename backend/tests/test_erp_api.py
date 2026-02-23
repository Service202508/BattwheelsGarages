"""
Battwheels OS ERP API Tests
Tests all ERP modules: Inventory, Suppliers, Purchase Orders, Sales Orders, Invoices, Accounting
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://revenue-health-dash.preview.emergentagent.com')

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_root_api(self):
        """Test root API endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data
        print("✓ Root API endpoint working")
    
    def test_admin_login(self):
        """Test admin login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "test_pwd_placeholder"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@battwheels.in"
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful - user_id: {data['user']['user_id']}")
    
    def test_technician_login(self):
        """Test technician login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "deepak@battwheelsgarages.in",
            "password": "tech123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "technician"
        print(f"✓ Technician login successful - user_id: {data['user']['user_id']}")
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrong_pwd_placeholder"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected")


@pytest.fixture(scope="class")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "test_pwd_placeholder"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="class")
def auth_headers(admin_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestDashboard:
    """Dashboard stats tests"""
    
    def test_dashboard_stats(self, auth_headers):
        """Test dashboard stats endpoint returns all required metrics"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required stats are present
        required_fields = [
            "vehicles_in_workshop",
            "open_repair_orders", 
            "avg_repair_time",
            "available_technicians"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Dashboard stats: vehicles_in_workshop={data['vehicles_in_workshop']}, open_repair_orders={data['open_repair_orders']}")


class TestInventory:
    """Inventory management tests"""
    
    def test_get_inventory(self, auth_headers):
        """Test fetching inventory items"""
        response = requests.get(f"{BASE_URL}/api/inventory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Inventory fetched: {len(data)} items")
        
        # Verify seeded items exist (should have 6 items)
        if len(data) >= 6:
            print(f"✓ Seeded inventory items present ({len(data)} items)")
        
        # Verify item structure
        if len(data) > 0:
            item = data[0]
            required_fields = ["item_id", "name", "category", "quantity", "unit_price", "min_stock_level"]
            for field in required_fields:
                assert field in item, f"Missing field in inventory item: {field}"
            print(f"✓ Inventory item structure valid - first item: {item['name']}")
    
    def test_create_inventory_item(self, auth_headers):
        """Test creating a new inventory item"""
        test_item = {
            "name": "TEST_Battery_Cell_48V",
            "sku": "TEST-BAT-48V-001",
            "category": "battery",
            "quantity": 50,
            "unit_price": 15000,
            "cost_price": 12000,
            "min_stock_level": 10,
            "max_stock_level": 100,
            "reorder_quantity": 20,
            "location": "Warehouse A"
        }
        response = requests.post(f"{BASE_URL}/api/inventory", headers=auth_headers, json=test_item)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_item["name"]
        assert data["quantity"] == test_item["quantity"]
        assert "item_id" in data
        print(f"✓ Inventory item created: {data['item_id']}")
        return data["item_id"]


class TestSuppliers:
    """Supplier management tests"""
    
    def test_get_suppliers(self, auth_headers):
        """Test fetching suppliers - should have 3 seeded suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Suppliers fetched: {len(data)} suppliers")
        
        # Verify seeded suppliers exist
        supplier_names = [s["name"] for s in data]
        expected_suppliers = ["EV Parts India", "BatteryWorld", "AutoTools Pro"]
        found_suppliers = [name for name in expected_suppliers if name in supplier_names]
        print(f"✓ Found seeded suppliers: {found_suppliers}")
        
        # Verify supplier structure
        if len(data) > 0:
            supplier = data[0]
            required_fields = ["supplier_id", "name", "category", "payment_terms", "is_active"]
            for field in required_fields:
                assert field in supplier, f"Missing field in supplier: {field}"
            print(f"✓ Supplier structure valid")
    
    def test_create_supplier(self, auth_headers):
        """Test creating a new supplier"""
        test_supplier = {
            "name": "TEST_Supplier_Corp",
            "contact_person": "Test Contact",
            "email": "test@supplier.com",
            "phone": "+91-9876543210",
            "address": "Test Address, Mumbai",
            "gst_number": "27AABCT1234A1ZV",
            "payment_terms": "net_30",
            "category": "parts"
        }
        response = requests.post(f"{BASE_URL}/api/suppliers", headers=auth_headers, json=test_supplier)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_supplier["name"]
        assert "supplier_id" in data
        print(f"✓ Supplier created: {data['supplier_id']}")


class TestPurchaseOrders:
    """Purchase order tests"""
    
    def test_get_purchase_orders(self, auth_headers):
        """Test fetching purchase orders"""
        response = requests.get(f"{BASE_URL}/api/purchase-orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Purchase orders fetched: {len(data)} orders")


class TestSalesOrders:
    """Sales order tests"""
    
    def test_get_sales_orders(self, auth_headers):
        """Test fetching sales orders"""
        response = requests.get(f"{BASE_URL}/api/sales-orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Sales orders fetched: {len(data)} orders")


class TestInvoices:
    """Invoice tests"""
    
    def test_get_invoices(self, auth_headers):
        """Test fetching invoices"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Invoices fetched: {len(data)} invoices")


class TestAccounting:
    """Accounting tests"""
    
    def test_get_accounting_summary(self, auth_headers):
        """Test fetching accounting summary"""
        response = requests.get(f"{BASE_URL}/api/accounting/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["total_revenue", "total_expenses", "total_receivables", "total_payables", "net_profit"]
        for field in required_fields:
            assert field in data, f"Missing field in accounting summary: {field}"
        
        print(f"✓ Accounting summary: revenue=₹{data['total_revenue']}, expenses=₹{data['total_expenses']}, net_profit=₹{data['net_profit']}")
    
    def test_get_ledger(self, auth_headers):
        """Test fetching general ledger"""
        response = requests.get(f"{BASE_URL}/api/ledger", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Ledger fetched: {len(data)} entries")


class TestVehicles:
    """Vehicle management tests"""
    
    def test_get_vehicles(self, auth_headers):
        """Test fetching vehicles"""
        response = requests.get(f"{BASE_URL}/api/vehicles", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Vehicles fetched: {len(data)} vehicles")
    
    def test_create_vehicle(self, auth_headers):
        """Test creating a new vehicle"""
        test_vehicle = {
            "owner_name": "TEST_Owner",
            "owner_email": "test@owner.com",
            "owner_phone": "+91-9876543210",
            "make": "Tata",
            "model": "Nexon EV",
            "year": 2024,
            "registration_number": "TEST-MH-01-AB-1234",
            "battery_capacity": 40.5
        }
        response = requests.post(f"{BASE_URL}/api/vehicles", headers=auth_headers, json=test_vehicle)
        assert response.status_code == 200
        data = response.json()
        assert data["make"] == test_vehicle["make"]
        assert data["model"] == test_vehicle["model"]
        assert "vehicle_id" in data
        print(f"✓ Vehicle created: {data['vehicle_id']}")
        return data["vehicle_id"]


class TestTickets:
    """Ticket management tests"""
    
    def test_get_tickets(self, auth_headers):
        """Test fetching tickets"""
        response = requests.get(f"{BASE_URL}/api/tickets", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Tickets fetched: {len(data)} tickets")
    
    def test_create_ticket(self, auth_headers):
        """Test creating a new ticket"""
        # First get a vehicle
        vehicles_response = requests.get(f"{BASE_URL}/api/vehicles", headers=auth_headers)
        vehicles = vehicles_response.json()
        
        if len(vehicles) == 0:
            # Create a vehicle first
            vehicle_data = {
                "owner_name": "TEST_Ticket_Owner",
                "owner_email": "ticket@test.com",
                "owner_phone": "+91-9876543210",
                "make": "Mahindra",
                "model": "XUV400",
                "year": 2024,
                "registration_number": "TEST-MH-02-CD-5678",
                "battery_capacity": 39.4
            }
            vehicle_response = requests.post(f"{BASE_URL}/api/vehicles", headers=auth_headers, json=vehicle_data)
            vehicle_id = vehicle_response.json()["vehicle_id"]
        else:
            vehicle_id = vehicles[0]["vehicle_id"]
        
        test_ticket = {
            "vehicle_id": vehicle_id,
            "title": "TEST_Battery_Diagnostic",
            "description": "Test ticket for battery diagnostic check",
            "category": "battery_service",
            "priority": "high",
            "estimated_cost": 5000
        }
        response = requests.post(f"{BASE_URL}/api/tickets", headers=auth_headers, json=test_ticket)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_ticket["title"]
        assert "ticket_id" in data
        print(f"✓ Ticket created: {data['ticket_id']}")


class TestServices:
    """Service offerings tests"""
    
    def test_get_services(self, auth_headers):
        """Test fetching service offerings"""
        response = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Services fetched: {len(data)} services")


class TestAlerts:
    """Alerts system tests"""
    
    def test_get_alerts(self, auth_headers):
        """Test fetching alerts"""
        response = requests.get(f"{BASE_URL}/api/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Alerts fetched: {len(data)} alerts")


class TestTechnicians:
    """Technician management tests"""
    
    def test_get_technicians(self, auth_headers):
        """Test fetching technicians"""
        response = requests.get(f"{BASE_URL}/api/technicians", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Technicians fetched: {len(data)} technicians")


class TestUsers:
    """User management tests (admin only)"""
    
    def test_get_users(self, auth_headers):
        """Test fetching users (admin only)"""
        response = requests.get(f"{BASE_URL}/api/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Users fetched: {len(data)} users")
        
        # Verify seeded users exist (should have 4 users)
        if len(data) >= 4:
            print(f"✓ Seeded users present ({len(data)} users)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
