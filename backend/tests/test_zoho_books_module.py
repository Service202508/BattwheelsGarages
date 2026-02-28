"""
Test Suite for Zoho Books Module - Battwheels OS
Tests: Customers, Services, Parts, Invoices, Analytics
"""
import pytest
import requests
import os

pytestmark = pytest.mark.skip(reason="deprecated — Zoho integration removed")

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "dev@battwheels.internal"
        assert data["user"]["role"] == "admin"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrong_pwd_placeholder"
        })
        assert response.status_code == 401


class TestCustomers:
    """Customer CRUD tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json().get("token")
    
    def test_list_customers(self, auth_token):
        """Test listing customers - should have at least 50 imported from Zoho Books"""
        response = requests.get(
            f"{BASE_URL}/api/books/customers?limit=100",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "customers" in data
        assert "total" in data
        assert data["total"] >= 50, f"Expected at least 50 customers, got {data['total']}"
        assert len(data["customers"]) >= 50
    
    def test_customer_search(self, auth_token):
        """Test customer search functionality"""
        response = requests.get(
            f"{BASE_URL}/api/books/customers?search=Bluwheelz&limit=100",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "customers" in data
        # Should find Bluwheelz Mobility
        assert len(data["customers"]) >= 1
        assert any("Bluwheelz" in c.get("display_name", "") for c in data["customers"])
    
    def test_customer_has_required_fields(self, auth_token):
        """Test that customers have all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/books/customers?limit=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        customer = data["customers"][0]
        
        # Check required fields
        required_fields = ["customer_id", "display_name", "outstanding_balance", "payment_terms"]
        for field in required_fields:
            assert field in customer, f"Missing field: {field}"
    
    def test_create_customer(self, auth_token):
        """Test creating a new customer"""
        new_customer = {
            "display_name": "TEST_Customer_ZohoBooks",
            "company_name": "Test Company",
            "phone": "9999999999",
            "email": "test@example.com",
            "gstin": "07AAAAA0000A1Z5",
            "billing_city": "Delhi",
            "billing_state": "Delhi",
            "payment_terms": 30
        }
        response = requests.post(
            f"{BASE_URL}/api/books/customers",
            json=new_customer,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == new_customer["display_name"]
        assert "customer_id" in data
        assert data["outstanding_balance"] == 0


class TestServices:
    """Service items tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json().get("token")
    
    def test_list_services(self, auth_token):
        """Test listing services - should have 100 imported from Zoho Books"""
        response = requests.get(
            f"{BASE_URL}/api/books/services?limit=200",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 100, f"Expected 100 services, got {data['total']}"
    
    def test_service_has_hsn_code(self, auth_token):
        """Test that services have HSN/SAC codes"""
        response = requests.get(
            f"{BASE_URL}/api/books/services?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check that services have HSN codes
        for service in data["items"]:
            assert "hsn_sac" in service
            assert "rate" in service
            assert "tax_rate" in service
    
    def test_service_search(self, auth_token):
        """Test service search functionality"""
        response = requests.get(
            f"{BASE_URL}/api/books/services?search=REPAIR&limit=100",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        # All results should contain REPAIR
        for item in data["items"]:
            assert "REPAIR" in item["name"].upper()


class TestParts:
    """Parts/Inventory tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json().get("token")
    
    def test_list_parts(self, auth_token):
        """Test listing parts - should have 200 imported from Zoho Books"""
        response = requests.get(
            f"{BASE_URL}/api/books/parts?limit=300",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 200, f"Expected 200 parts, got {data['total']}"
    
    def test_part_has_stock_info(self, auth_token):
        """Test that parts have stock information"""
        response = requests.get(
            f"{BASE_URL}/api/books/parts?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        for part in data["items"]:
            assert "stock_quantity" in part
            assert "reorder_level" in part
            assert "hsn_sac" in part
            assert "rate" in part


class TestInvoices:
    """Invoice tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json().get("token")
    
    def test_list_invoices(self, auth_token):
        """Test listing invoices"""
        response = requests.get(
            f"{BASE_URL}/api/books/invoices?limit=50",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        assert "total" in data
    
    def test_invoice_has_gst_calculation(self, auth_token):
        """Test that invoices have proper GST calculation"""
        response = requests.get(
            f"{BASE_URL}/api/books/invoices?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["invoices"]:
            invoice = data["invoices"][0]
            assert "subtotal" in invoice
            assert "tax_total" in invoice
            assert "total" in invoice
            # Verify GST calculation: total = subtotal + tax_total
            assert abs(invoice["total"] - (invoice["subtotal"] + invoice["tax_total"])) < 0.01
    
    def test_create_invoice_with_gst(self, auth_token):
        """Test creating an invoice with GST calculation"""
        # First get a customer
        cust_response = requests.get(
            f"{BASE_URL}/api/books/customers?limit=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        customer = cust_response.json()["customers"][0]
        
        # Get a service
        svc_response = requests.get(
            f"{BASE_URL}/api/books/services?limit=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        service = svc_response.json()["items"][0]
        
        # Create invoice
        invoice_data = {
            "customer_id": customer["customer_id"],
            "customer_name": customer["display_name"],
            "line_items": [{
                "item_id": service["item_id"],
                "item_name": service["name"],
                "quantity": 2,
                "rate": service["rate"],
                "discount_percent": 0,
                "tax_rate": 18.0
            }],
            "place_of_supply": "DL",
            "gst_treatment": "business_gst"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/books/invoices",
            json=invoice_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify GST calculation (18%)
        expected_subtotal = 2 * service["rate"]
        expected_tax = expected_subtotal * 0.18
        expected_total = expected_subtotal + expected_tax
        
        assert abs(data["subtotal"] - expected_subtotal) < 0.01
        assert abs(data["tax_total"] - expected_tax) < 0.01
        assert abs(data["total"] - expected_total) < 0.01
        assert data["status"] == "draft"


class TestAnalytics:
    """Analytics endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json().get("token")
    
    def test_analytics_summary(self, auth_token):
        """Test analytics summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/books/analytics/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "invoices" in data
        assert "revenue" in data
        assert "counts" in data
        
        # Check invoice stats
        assert "total" in data["invoices"]
        assert "paid" in data["invoices"]
        assert "pending" in data["invoices"]
        
        # Check revenue stats
        assert "total" in data["revenue"]
        assert "collected" in data["revenue"]
        assert "outstanding" in data["revenue"]
        
        # Check counts - verify Zoho Books import (at least the imported amounts)
        assert data["counts"]["customers"] >= 50
        assert data["counts"]["services"] >= 100
        assert data["counts"]["parts"] >= 200


class TestVendors:
    """Vendor tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json().get("token")
    
    def test_list_vendors(self, auth_token):
        """Test listing vendors - should have 50 imported from Zoho Books"""
        response = requests.get(
            f"{BASE_URL}/api/books/vendors?limit=100",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "vendors" in data
        assert "total" in data
        assert data["total"] == 50, f"Expected 50 vendors, got {data['total']}"


class TestChartOfAccounts:
    """Chart of Accounts tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        return response.json().get("token")
    
    def test_list_accounts(self, auth_token):
        """Test listing chart of accounts"""
        response = requests.get(
            f"{BASE_URL}/api/books/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total" in data
        # Should have 109 accounts imported
        assert data["total"] >= 100, f"Expected ~109 accounts, got {data['total']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
