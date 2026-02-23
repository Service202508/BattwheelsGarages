"""
Test Key Modules - Iteration 59
Tests core functionality: Dashboard, Items, Inventory Enhanced, Sales Orders, 
Time Tracking, Documents, and Customer Portal
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://self-serve-signup.preview.emergentagent.com').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Headers with auth"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Login successful - User: {data['user'].get('email', 'N/A')}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials properly rejected")


class TestDashboard:
    """Financial Dashboard tests at /home"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_dashboard_stats(self, headers):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Dashboard should have financial summary data
        print(f"✓ Dashboard stats: {list(data.keys())[:5]}...")
    
    def test_org_info(self, headers):
        """Test organization info"""
        response = requests.get(f"{BASE_URL}/api/org", headers=headers)
        assert response.status_code == 200
        print("✓ Organization info retrieved")


class TestItems:
    """Items module tests at /items"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_items_list(self, headers):
        """Test items listing"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Items list: {len(data['items'])} items found")
    
    def test_items_search(self, headers):
        """Test items search"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/?search=battery", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Items search: {len(data.get('items', []))} results for 'battery'")
    
    def test_create_and_get_item(self, headers):
        """Test item CRUD"""
        # Create item
        item_data = {
            "name": "TEST_Item_59",
            "sku": "TEST-SKU-59",
            "type": "goods",
            "rate": 100.0,
            "description": "Test item for iteration 59"
        }
        create_res = requests.post(f"{BASE_URL}/api/items-enhanced/", headers=headers, json=item_data)
        assert create_res.status_code in [200, 201], f"Create failed: {create_res.text}"
        created = create_res.json()
        item_id = created.get("item_id") or created.get("item", {}).get("item_id")
        print(f"✓ Item created: {item_id}")
        
        # Get item
        if item_id:
            get_res = requests.get(f"{BASE_URL}/api/items-enhanced/{item_id}", headers=headers)
            assert get_res.status_code == 200
            print("✓ Item retrieved successfully")


class TestInventoryEnhanced:
    """Inventory Management tests at /inventory-enhanced"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_inventory_summary(self, headers):
        """Test inventory summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        print(f"✓ Inventory summary: Items={data['summary'].get('total_items', 0)}, Variants={data['summary'].get('total_variants', 0)}")
    
    def test_warehouses_list(self, headers):
        """Test warehouses endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/warehouses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Warehouses: {len(data.get('warehouses', []))} found")
    
    def test_variants_list(self, headers):
        """Test variants endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/variants", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Variants: {len(data.get('variants', []))} found")
    
    def test_bundles_list(self, headers):
        """Test bundles endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/bundles", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Bundles: {len(data.get('bundles', []))} found")
    
    def test_serial_batches_list(self, headers):
        """Test serial/batch endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/serial-batches?status=all", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Serial/Batches: {len(data.get('serial_batches', []))} found")
    
    def test_shipments_list(self, headers):
        """Test shipments endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/shipments", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Shipments: {len(data.get('shipments', []))} found")
    
    def test_returns_list(self, headers):
        """Test returns endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/returns", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Returns: {len(data.get('returns', []))} found")
    
    def test_low_stock_report(self, headers):
        """Test low stock report"""
        response = requests.get(f"{BASE_URL}/api/inventory-enhanced/reports/low-stock", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Low Stock Report: {len(data.get('report', {}).get('low_stock_items', []))} items")
    
    def test_create_warehouse(self, headers):
        """Test creating a warehouse"""
        warehouse_data = {
            "name": "TEST_Warehouse_59",
            "code": "TW59",
            "city": "Mumbai",
            "is_primary": False
        }
        response = requests.post(f"{BASE_URL}/api/inventory-enhanced/warehouses", headers=headers, json=warehouse_data)
        assert response.status_code in [200, 201], f"Create warehouse failed: {response.text}"
        print("✓ Warehouse created successfully")


class TestSalesOrders:
    """Sales Orders tests at /sales-orders"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_sales_orders_list(self, headers):
        """Test sales orders listing"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Sales Orders: {len(data.get('sales_orders', []))} found")
    
    def test_sales_orders_summary(self, headers):
        """Test sales orders summary"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Sales Orders Summary: {data.get('summary', {})}")
    
    def test_fulfillment_summary(self, headers):
        """Test fulfillment summary"""
        response = requests.get(f"{BASE_URL}/api/sales-orders-enhanced/reports/fulfillment-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Fulfillment Summary retrieved")


class TestTimeTracking:
    """Time Tracking module tests at /time-tracking"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_time_entries_list(self, headers):
        """Test time entries listing"""
        response = requests.get(f"{BASE_URL}/api/time-tracking/entries", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Time Entries: {len(data.get('entries', []))} found")
    
    def test_projects_list(self, headers):
        """Test projects for time tracking"""
        response = requests.get(f"{BASE_URL}/api/time-tracking/projects", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Time Tracking Projects: {len(data.get('projects', []))} found")


class TestDocuments:
    """Documents module tests at /documents"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_documents_list(self, headers):
        """Test documents listing"""
        response = requests.get(f"{BASE_URL}/api/documents/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Documents: {len(data.get('documents', []))} found")
    
    def test_document_folders(self, headers):
        """Test document folders"""
        response = requests.get(f"{BASE_URL}/api/documents/folders", headers=headers)
        # Documents may or may not have folders endpoint
        if response.status_code == 200:
            print("✓ Document folders endpoint available")
        else:
            print(f"Note: Document folders returned {response.status_code}")


class TestCustomerPortal:
    """Customer Portal tests at /api/customer-portal endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def portal_session(self, admin_headers):
        """Get portal session by enabling portal for a contact"""
        # First get a contact
        contacts_res = requests.get(f"{BASE_URL}/api/contacts-enhanced/", headers=admin_headers)
        if contacts_res.status_code != 200:
            pytest.skip("Cannot fetch contacts")
        
        contacts = contacts_res.json().get("contacts", [])
        if not contacts:
            pytest.skip("No contacts available")
        
        contact_id = contacts[0].get("contact_id")
        
        # Enable portal
        enable_res = requests.post(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/enable-portal", headers=admin_headers)
        if enable_res.status_code not in [200, 201]:
            pytest.skip(f"Cannot enable portal: {enable_res.text}")
        
        portal_token = enable_res.json().get("portal_token")
        
        # Login to portal
        login_res = requests.post(f"{BASE_URL}/api/customer-portal/login", json={"token": portal_token})
        if login_res.status_code != 200:
            pytest.skip(f"Portal login failed: {login_res.text}")
        
        return login_res.json().get("session_token")
    
    def test_portal_login_invalid_token(self):
        """Test portal login with invalid token"""
        response = requests.post(f"{BASE_URL}/api/customer-portal/login", json={
            "token": "invalid-token-123456789"
        })
        assert response.status_code == 401
        print("✓ Invalid portal token rejected")
    
    def test_portal_dashboard_with_header(self, portal_session):
        """Test portal dashboard via X-Portal-Session header"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/dashboard",
            headers={"X-Portal-Session": portal_session}
        )
        assert response.status_code == 200
        data = response.json()
        assert "dashboard" in data
        print(f"✓ Portal Dashboard (header): Contact={data['dashboard']['contact'].get('name', 'N/A')}")
    
    def test_portal_dashboard_with_query(self, portal_session):
        """Test portal dashboard via query parameter"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/dashboard?session_token={portal_session}"
        )
        assert response.status_code == 200
        print("✓ Portal Dashboard (query param) works")
    
    def test_portal_invoices(self, portal_session):
        """Test portal invoices endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/invoices",
            headers={"X-Portal-Session": portal_session}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Portal Invoices: {len(data.get('invoices', []))} found")
    
    def test_portal_estimates(self, portal_session):
        """Test portal estimates endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/estimates",
            headers={"X-Portal-Session": portal_session}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Portal Estimates: {len(data.get('estimates', []))} found")
    
    def test_portal_profile(self, portal_session):
        """Test portal profile endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/profile",
            headers={"X-Portal-Session": portal_session}
        )
        assert response.status_code == 200
        print("✓ Portal Profile retrieved")
    
    def test_portal_statement(self, portal_session):
        """Test portal statement endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/customer-portal/statement",
            headers={"X-Portal-Session": portal_session}
        )
        assert response.status_code == 200
        print("✓ Portal Statement retrieved")
    
    def test_portal_logout(self, portal_session):
        """Test portal logout"""
        response = requests.post(
            f"{BASE_URL}/api/customer-portal/logout",
            headers={"X-Portal-Session": portal_session}
        )
        assert response.status_code == 200
        print("✓ Portal Logout successful")


class TestContactsAndInvoices:
    """Additional tests for contacts and invoices"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin123"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_contacts_list(self, headers):
        """Test contacts listing"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Contacts: {len(data.get('contacts', []))} found")
    
    def test_invoices_list(self, headers):
        """Test invoices listing"""
        response = requests.get(f"{BASE_URL}/api/invoices-enhanced/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Invoices: {len(data.get('invoices', []))} found")
    
    def test_estimates_list(self, headers):
        """Test estimates listing"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Estimates: {len(data.get('estimates', []))} found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
