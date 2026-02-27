"""
Razorpay Integration Tests for Battwheels OS
Tests for:
- /api/payments/config GET endpoint (returns configuration status)
- /api/payments/config POST endpoint (validates and saves credentials)
- Organization Settings Finance tab with Razorpay card
- Invoice page payment buttons when balance_due > 0
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "dev@battwheels.internal"
TEST_PASSWORD = "DevTest@123"

class TestRazorpayConfigAPI:
    """Test Razorpay payment configuration endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token") or data.get("access_token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed with status {login_response.status_code}")
    
    def test_get_payment_config_returns_status(self):
        """Test GET /api/payments/config returns configuration status"""
        response = self.session.get(f"{BASE_URL}/api/v1/payments/config")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "code" in data
        assert "configured" in data
        assert "test_mode" in data
        assert "message" in data
        
        # Default should be not configured (no env vars set)
        print(f"Razorpay configured: {data['configured']}")
        print(f"Test mode: {data['test_mode']}")
        print(f"Message: {data['message']}")
    
    def test_get_payment_config_without_auth(self):
        """Test GET /api/payments/config without authentication"""
        # Create session without auth
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/v1/payments/config")
        
        # Should return 200 (public) or 401 (auth required)
        assert response.status_code in [200, 401], f"Expected 200 or 401, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "configured" in data
            print(f"Without auth - configured: {data['configured']}")
        else:
            print(f"Without auth - endpoint requires authentication (401)")
    
    def test_post_payment_config_validation_invalid_credentials(self):
        """Test POST /api/payments/config validates credentials before saving"""
        # Try with fake credentials - should fail validation
        fake_config = {
            "key_id": "rzp_test_REDACTED",
            "key_secret": "fake_secret_12345678901234",
            "webhook_secret": "",
            "test_mode": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/v1/payments/config", json=fake_config)
        
        # Should fail with 400 because credentials are invalid
        # The API validates against Razorpay before saving
        assert response.status_code == 400, f"Expected 400 for invalid credentials, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data or "error" in data
        print(f"Validation error: {data.get('detail', data.get('error', 'Unknown'))}")
    
    def test_post_payment_config_validation_short_credentials(self):
        """Test POST /api/payments/config validates credential length"""
        # Try with too short credentials
        short_config = {
            "key_id": "rzp_test",  # Too short
            "key_secret": "short",  # Too short
            "webhook_secret": "",
            "test_mode": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/v1/payments/config", json=short_config)
        
        # Should fail with 422 (validation error) or 400
        assert response.status_code in [400, 422], f"Expected 400/422 for short credentials, got {response.status_code}"
        
        print(f"Short credentials validation response: {response.status_code}")
    
    def test_post_payment_config_missing_required_fields(self):
        """Test POST /api/payments/config requires key_id and key_secret"""
        # Missing key_secret
        partial_config = {
            "key_id": "rzp_test_REDACTED",
            "test_mode": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/v1/payments/config", json=partial_config)
        
        # Should fail with 422 (validation error)
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
    
    def test_payment_orders_endpoint_exists(self):
        """Test GET /api/payments/orders endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/v1/payments/orders")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "orders" in data
        print(f"Payment orders: {len(data.get('orders', []))}")
    
    def test_payment_links_endpoint_exists(self):
        """Test GET /api/payments/links endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/v1/payments/links")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "payment_links" in data
        print(f"Payment links: {len(data.get('payment_links', []))}")


class TestInvoicePaymentIntegration:
    """Test invoice-related payment endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token") or data.get("access_token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed with status {login_response.status_code}")
    
    def test_get_invoices_with_balance_due(self):
        """Test fetching invoices with balance_due > 0"""
        response = self.session.get(f"{BASE_URL}/api/v1/invoices-enhanced/")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        invoices = data.get("invoices", [])
        
        # Find invoices with balance due
        invoices_with_balance = [inv for inv in invoices if inv.get("balance_due", 0) > 0]
        print(f"Total invoices: {len(invoices)}")
        print(f"Invoices with balance due: {len(invoices_with_balance)}")
        
        if invoices_with_balance:
            print(f"First invoice with balance: {invoices_with_balance[0].get('invoice_number')} - ₹{invoices_with_balance[0].get('balance_due')}")
    
    def test_create_payment_order_without_razorpay_config(self):
        """Test creating payment order fails gracefully when Razorpay not configured"""
        # First, let's get an invoice with balance
        invoices_response = self.session.get(f"{BASE_URL}/api/v1/invoices-enhanced/")
        
        if invoices_response.status_code != 200:
            pytest.skip("Could not fetch invoices")
        
        invoices = invoices_response.json().get("invoices", [])
        invoices_with_balance = [inv for inv in invoices if inv.get("balance_due", 0) > 0]
        
        if not invoices_with_balance:
            pytest.skip("No invoices with balance due found")
        
        invoice_id = invoices_with_balance[0].get("invoice_id")
        
        # Try to create order
        response = self.session.post(f"{BASE_URL}/api/v1/payments/create-order", json={
            "invoice_id": invoice_id
        })
        
        # Should fail with 400 because Razorpay is not configured
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "not configured" in data.get("detail", "").lower() or "credentials" in data.get("detail", "").lower()
        print(f"Expected error: {data.get('detail')}")
    
    def test_create_payment_link_without_razorpay_config(self):
        """Test creating payment link fails gracefully when Razorpay not configured"""
        # First, get an invoice with balance
        invoices_response = self.session.get(f"{BASE_URL}/api/v1/invoices-enhanced/")
        
        if invoices_response.status_code != 200:
            pytest.skip("Could not fetch invoices")
        
        invoices = invoices_response.json().get("invoices", [])
        invoices_with_balance = [inv for inv in invoices if inv.get("balance_due", 0) > 0]
        
        if not invoices_with_balance:
            pytest.skip("No invoices with balance due found")
        
        invoice_id = invoices_with_balance[0].get("invoice_id")
        
        # Try to create payment link
        response = self.session.post(f"{BASE_URL}/api/v1/payments/create-payment-link/{invoice_id}")
        
        # Should fail with 400 because Razorpay is not configured
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        print(f"Expected error: {data.get('detail')}")


class TestOrganizationSettingsAPI:
    """Test organization settings API for Razorpay configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token") or data.get("access_token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed with status {login_response.status_code}")
    
    def test_get_organization_settings(self):
        """Test GET /api/v1/organizations/settings returns settings"""
        response = self.session.get(f"{BASE_URL}/api/v1/organizations/settings")
        
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Organization settings keys: {list(data.keys())}")
        else:
            print(f"Organization settings endpoint: {response.status_code}")
    
    def test_get_organization_info(self):
        """Test GET /api/v1/organizations returns organization info"""
        response = self.session.get(f"{BASE_URL}/api/v1/organizations")
        
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Organization: {data.get('name')}")
            print(f"Organization ID: {data.get('organization_id')}")
        else:
            print(f"Organization info endpoint: {response.status_code}")


class TestWebhookEndpoint:
    """Test Razorpay webhook endpoint"""
    
    def test_webhook_endpoint_exists(self):
        """Test POST /api/payments/webhook endpoint exists"""
        # Send invalid payload - should get 400 not 404
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/v1/payments/webhook", json={})
        
        # Should return 400 for invalid payload, 200 for success, or 403 for RBAC
        assert response.status_code in [400, 200, 403], f"Expected 400, 200, or 403, got {response.status_code} - webhook endpoint may not exist"
        print(f"Webhook endpoint status: {response.status_code}")
    
    def test_webhook_with_test_payload(self):
        """Test webhook with a simulated payment.captured event"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        test_payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test123",
                        "order_id": "order_test123",
                        "amount": 10000,
                        "status": "captured",
                        "method": "upi",
                        "notes": {
                            "invoice_id": "test_invoice",
                            "organization_id": ""
                        }
                    }
                }
            }
        }
        
        response = session.post(f"{BASE_URL}/api/v1/payments/webhook", json=test_payload)
        
        # Without signature verification, webhook should still process
        # The order_id won't be found, but the endpoint should work
        print(f"Webhook test response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Webhook processed: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
