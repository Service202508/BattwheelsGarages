"""
P0 Bug Fixes Test Suite - Payments Received & User Registration
================================================================
Tests for two critical P0 bugs that were fixed:
1. P0-4: POST /api/v1/payments-received was querying wrong collections
         (contacts_enhanced/invoices_enhanced instead of contacts/invoices)
2. P0-5: POST /api/v1/auth/register only created a bare user without
         organization, membership, or subscription

Test Data:
- Demo org: demo-volt-motors-001
- Demo user: demo@voltmotors.in / Demo@12345
- Invoice: inv-052293f33251 (customer: CON-devfleet-006, total: 41300, balance: 41300)
- Invoice: inv-1a60e27fb6ff (customer: CON-greenride-007, total: 26845)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://evfi-hardening.preview.emergentagent.com").rstrip("/")

# Test data tracking for cleanup
CREATED_TEST_USERS = []
CREATED_TEST_PAYMENTS = []


# ====================== FIXTURES ======================

@pytest.fixture(scope="module")
def demo_auth_headers():
    """Get auth headers for demo user in demo-volt-motors-001 org"""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "demo@voltmotors.in",
        "password": "Demo@12345"
    })
    assert resp.status_code == 200, f"Demo login failed: {resp.text}"
    token = resp.json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "demo-volt-motors-001",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module", autouse=True)
def reset_invoice_balances_before_tests():
    """Reset test invoice balances before running payment tests"""
    import pymongo
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["battwheels_dev"]
    
    # Reset invoice balances to original values
    db.invoices.update_one(
        {"invoice_id": "inv-052293f33251"}, 
        {"$set": {"balance_due": 41300.0, "amount_paid": 0, "status": "sent"}}
    )
    db.invoices.update_one(
        {"invoice_id": "inv-1a60e27fb6ff"}, 
        {"$set": {"balance_due": 26845.0, "amount_paid": 0, "status": "overdue"}}
    )
    
    # Also clean up any test payments from previous runs
    db.payments_received.delete_many({"notes": {"$regex": "^Test payment.*P0"}})
    db.payments_received.delete_many({"notes": {"$regex": "^Advance payment"}})
    db.payments_received.delete_many({"reference_number": {"$regex": "^TEST-"}})
    
    client.close()
    yield


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_tests():
    """Cleanup test data after all tests in this module"""
    yield
    # Cleanup created users
    import pymongo
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["battwheels_dev"]
    
    for email in CREATED_TEST_USERS:
        user = db.users.find_one({"email": email})
        if user:
            user_id = user["user_id"]
            org_id = user.get("organization_id")
            # Delete user, org, membership, subscription
            db.users.delete_one({"user_id": user_id})
            if org_id:
                db.organizations.delete_one({"organization_id": org_id})
                db.organization_users.delete_many({"organization_id": org_id})
                db.subscriptions.delete_many({"organization_id": org_id})
    
    # Cleanup created payments
    for payment_id in CREATED_TEST_PAYMENTS:
        db.payments_received.delete_one({"payment_id": payment_id})
        db.customer_credits.delete_many({"source_id": payment_id})
        db.payment_history.delete_many({"payment_id": payment_id})
    
    client.close()


# ====================== P0-4: PAYMENTS RECEIVED TESTS ======================

class TestPaymentRecordingP0Fix:
    """
    P0-4: Tests for payment recording bug fix
    Bug: Was querying contacts_enhanced/invoices_enhanced instead of contacts/invoices
    Fix: Changed collection references in payments_received.py lines 23-24
    """
    
    def test_record_payment_success_customer_found(self, demo_auth_headers):
        """
        P0-4: POST /api/v1/payments-received should record a payment successfully
        Customer should be found from 'contacts' collection (not contacts_enhanced)
        Payment document should include organization_id
        """
        payment_data = {
            "customer_id": "CON-devfleet-006",  # Known customer in demo org
            "amount": 10000,
            "payment_mode": "bank_transfer",
            "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reference_number": f"TEST-REF-{uuid.uuid4().hex[:8]}",
            "allocations": [
                {"invoice_id": "inv-052293f33251", "amount": 10000}
            ],
            "notes": "Test payment for P0-4 bug fix verification"
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/v1/payments-received",
            json=payment_data,
            headers=demo_auth_headers
        )
        
        # Verify success
        assert resp.status_code == 200, f"Payment recording failed: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0, f"Unexpected response code: {data}"
        assert "payment" in data, "Response should contain payment object"
        
        payment = data["payment"]
        
        # Verify payment document structure
        assert payment.get("payment_id"), "Payment should have payment_id"
        assert payment.get("payment_number"), "Payment should have payment_number"
        assert payment.get("organization_id") == "demo-volt-motors-001", \
            f"Payment should have correct organization_id, got: {payment.get('organization_id')}"
        assert payment.get("customer_id") == "CON-devfleet-006"
        assert payment.get("customer_name") == "Delhi EV Fleet Pvt Ltd"
        assert payment.get("amount") == 10000
        assert payment.get("status") == "recorded"
        
        # Track for cleanup
        CREATED_TEST_PAYMENTS.append(payment["payment_id"])
        
        print(f"SUCCESS: Payment {payment['payment_number']} recorded with org_id={payment['organization_id']}")
    
    def test_record_payment_customer_not_found_404(self, demo_auth_headers):
        """
        P0-4: POST /api/v1/payments-received should return 404 if customer_id
        doesn't exist in the contacts collection
        """
        payment_data = {
            "customer_id": "NON-EXISTENT-CUSTOMER-12345",
            "amount": 5000,
            "payment_mode": "cash",
            "allocations": []
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/v1/payments-received",
            json=payment_data,
            headers=demo_auth_headers
        )
        
        # Should return 404
        assert resp.status_code == 404, f"Expected 404 for non-existent customer, got {resp.status_code}: {resp.text}"
        assert "not found" in resp.text.lower(), "Error should mention customer not found"
        
        print("SUCCESS: Non-existent customer correctly returns 404")
    
    def test_record_payment_wrong_org_customer_404(self, demo_auth_headers):
        """
        P0-4: Payment should fail if customer exists but belongs to different org
        Multi-tenancy: customer lookup now includes org_id filter
        """
        # CON-235065AEEC94 belongs to dev-internal-testing-001, not demo org
        payment_data = {
            "customer_id": "CON-235065AEEC94",
            "amount": 5000,
            "payment_mode": "cash",
            "allocations": []
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/v1/payments-received",
            json=payment_data,
            headers=demo_auth_headers
        )
        
        # Should return 404 because customer is in different org
        assert resp.status_code == 404, \
            f"Expected 404 for customer in different org, got {resp.status_code}: {resp.text}"
        
        print("SUCCESS: Customer from different org correctly returns 404 (multi-tenant isolation)")
    
    def test_list_payments_filtered_by_org(self, demo_auth_headers):
        """
        P0-4: GET /api/v1/payments-received should list payments filtered by organization_id from JWT
        """
        resp = requests.get(
            f"{BASE_URL}/api/v1/payments-received/",  # Note: trailing slash required
            headers=demo_auth_headers
        )
        
        assert resp.status_code == 200, f"List payments failed: {resp.text}"
        data = resp.json()
        assert data.get("code") == 0
        assert "payments" in data
        assert "total" in data
        
        # Verify all returned payments belong to the demo org
        for payment in data["payments"]:
            assert payment.get("organization_id") == "demo-volt-motors-001", \
                f"Payment {payment.get('payment_id')} has wrong org: {payment.get('organization_id')}"
        
        print(f"SUCCESS: Listed {len(data['payments'])} payments for demo org")
    
    def test_record_retainer_payment(self, demo_auth_headers):
        """
        P0-4: Record a retainer/advance payment (no invoice allocation)
        Should create customer credit
        """
        payment_data = {
            "customer_id": "CON-greenride-007",
            "amount": 15000,
            "payment_mode": "upi",
            "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reference_number": f"TEST-RETAINER-{uuid.uuid4().hex[:8]}",
            "allocations": [],  # No allocation = retainer
            "is_retainer": True,
            "notes": "Advance payment for future services"
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/v1/payments-received",
            json=payment_data,
            headers=demo_auth_headers
        )
        
        assert resp.status_code == 200, f"Retainer payment failed: {resp.text}"
        data = resp.json()
        payment = data["payment"]
        
        assert payment.get("is_retainer") == True
        assert payment.get("organization_id") == "demo-volt-motors-001"
        
        CREATED_TEST_PAYMENTS.append(payment["payment_id"])
        
        print(f"SUCCESS: Retainer payment {payment['payment_number']} recorded")


# ====================== P0-5: USER REGISTRATION TESTS ======================

class TestUserRegistrationP0Fix:
    """
    P0-5: Tests for user registration bug fix
    Bug: Registration only created a bare user without organization, membership, or subscription
    Fix: Rewritten register() in auth_main.py to create all 4 documents
    """
    
    def test_register_creates_all_documents(self):
        """
        P0-5: POST /api/v1/auth/register should create:
        1. User (role=owner)
        2. Organization
        3. Organization_users membership
        4. Subscription (plan_code=starter, status=trialing)
        """
        test_email = f"test-agent-{uuid.uuid4().hex[:8]}@test.in"
        CREATED_TEST_USERS.append(test_email)
        
        register_data = {
            "email": test_email,
            "password": "Test@12345",
            "name": "Test Agent User",
            "organization_name": "Test Agent Workshop",
            "phone": "9876543210"
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=register_data
        )
        
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "token" in data, "Response should contain JWT token"
        assert "user_id" in data
        assert "organization_id" in data
        assert "organization_name" in data
        assert data.get("role") == "owner", f"Role should be owner, got: {data.get('role')}"
        
        user_id = data["user_id"]
        org_id = data["organization_id"]
        
        # Verify documents in database
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["battwheels_dev"]
        
        # 1. Check user document
        user = db.users.find_one({"user_id": user_id})
        assert user is not None, "User document not created"
        assert user["email"] == test_email
        assert user["role"] == "owner"
        assert user["organization_id"] == org_id
        assert user.get("is_active") == True
        
        # 2. Check organization document
        org = db.organizations.find_one({"organization_id": org_id})
        assert org is not None, "Organization document not created"
        assert org["name"] == "Test Agent Workshop"
        assert org.get("is_active") == True
        assert org.get("trial_active") == True
        assert "trial_end" in org
        
        # 3. Check organization_users membership
        membership = db.organization_users.find_one({
            "user_id": user_id,
            "organization_id": org_id
        })
        assert membership is not None, "Organization membership not created"
        assert membership["role"] == "owner"
        assert membership["status"] == "active"
        
        # 4. Check subscription
        subscription = db.subscriptions.find_one({"organization_id": org_id})
        assert subscription is not None, "Subscription not created"
        assert subscription["plan_code"] == "starter"
        assert subscription["status"] == "trialing"
        assert "trial_start" in subscription
        assert "trial_end" in subscription
        
        client.close()
        
        print(f"SUCCESS: Registration created all 4 documents for {test_email}")
        print(f"  - User: {user_id}")
        print(f"  - Organization: {org_id}")
        print(f"  - Membership: owner")
        print(f"  - Subscription: starter (trialing)")
    
    def test_register_returns_jwt_with_org_id(self):
        """
        P0-5: POST /api/v1/auth/register should return JWT token containing org_id
        """
        import jwt
        
        test_email = f"test-jwt-{uuid.uuid4().hex[:8]}@test.in"
        CREATED_TEST_USERS.append(test_email)
        
        register_data = {
            "email": test_email,
            "password": "Test@12345",
            "name": "JWT Test User"
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=register_data
        )
        
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        data = resp.json()
        
        token = data["token"]
        
        # Decode JWT (without verification - just to check payload)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert "org_id" in payload, f"JWT should contain org_id, got: {payload.keys()}"
        assert payload["org_id"] == data["organization_id"]
        assert payload.get("user_id") == data["user_id"]
        assert payload.get("role") == "owner"
        
        print(f"SUCCESS: JWT contains org_id={payload['org_id']}")
    
    def test_register_duplicate_email_rejected(self):
        """
        P0-5: POST /api/v1/auth/register should reject duplicate emails with 400
        """
        # First registration
        test_email = f"test-dup-{uuid.uuid4().hex[:8]}@test.in"
        CREATED_TEST_USERS.append(test_email)
        
        register_data = {
            "email": test_email,
            "password": "Test@12345",
            "name": "First User"
        }
        
        resp1 = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        assert resp1.status_code == 200, f"First registration failed: {resp1.text}"
        
        # Second registration with same email
        register_data["name"] = "Second User"
        resp2 = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        
        assert resp2.status_code == 400, \
            f"Duplicate email should return 400, got {resp2.status_code}: {resp2.text}"
        assert "already registered" in resp2.text.lower() or "already exists" in resp2.text.lower(), \
            f"Error should mention duplicate email: {resp2.text}"
        
        print("SUCCESS: Duplicate email correctly rejected with 400")
    
    def test_register_auto_generates_org_name(self):
        """
        P0-5: POST /api/v1/auth/register should auto-generate org name if not provided
        """
        test_email = f"test-auto-{uuid.uuid4().hex[:8]}@test.in"
        CREATED_TEST_USERS.append(test_email)
        
        register_data = {
            "email": test_email,
            "password": "Test@12345",
            "name": "Auto Org User"
            # organization_name NOT provided
        }
        
        resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        data = resp.json()
        
        # Verify org name was auto-generated
        assert data.get("organization_name"), "Organization name should be auto-generated"
        assert "Auto Org User" in data["organization_name"], \
            f"Auto-generated org name should contain user's name, got: {data['organization_name']}"
        
        print(f"SUCCESS: Auto-generated org name: {data['organization_name']}")
    
    def test_new_user_can_login_and_access_modules(self):
        """
        P0-5: New registered user should be able to login and access modules
        Tests: tickets, contacts-enhanced, items-enhanced returning 200
        """
        # Register new user
        test_email = f"test-access-{uuid.uuid4().hex[:8]}@test.in"
        CREATED_TEST_USERS.append(test_email)
        
        register_data = {
            "email": test_email,
            "password": "Test@12345",
            "name": "Access Test User",
            "organization_name": "Access Test Workshop"
        }
        
        resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        
        reg_data = resp.json()
        org_id = reg_data["organization_id"]
        
        # Login with new user
        login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": test_email,
            "password": "Test@12345"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        token = login_resp.json()["token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": org_id,
            "Content-Type": "application/json"
        }
        
        # Test access to key modules
        modules_to_test = [
            ("/api/v1/tickets", "Service Tickets"),
            ("/api/v1/contacts-enhanced", "Contacts Enhanced"),
            ("/api/v1/items-enhanced", "Items Enhanced"),
        ]
        
        for endpoint, module_name in modules_to_test:
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            assert resp.status_code == 200, \
                f"{module_name} ({endpoint}) should return 200, got {resp.status_code}: {resp.text}"
            print(f"  - {module_name}: OK (200)")
        
        print(f"SUCCESS: New user can access all tested modules")


# ====================== ADDITIONAL EDGE CASES ======================

class TestPaymentEdgeCases:
    """Additional edge cases for payment recording"""
    
    def test_payment_with_invoice_allocation(self, demo_auth_headers):
        """Test payment with specific invoice allocation updates invoice status"""
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["battwheels_dev"]
        
        # Get invoice balance before payment
        invoice_before = db.invoices.find_one({"invoice_id": "inv-1a60e27fb6ff"})
        balance_before = invoice_before.get("balance_due", 0)
        
        payment_data = {
            "customer_id": "CON-greenride-007",
            "amount": 5000,
            "payment_mode": "card",
            "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reference_number": f"TEST-ALLOC-{uuid.uuid4().hex[:8]}",
            "allocations": [
                {"invoice_id": "inv-1a60e27fb6ff", "amount": 5000}
            ]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/v1/payments-received",
            json=payment_data,
            headers=demo_auth_headers
        )
        
        assert resp.status_code == 200, f"Payment failed: {resp.text}"
        payment = resp.json()["payment"]
        CREATED_TEST_PAYMENTS.append(payment["payment_id"])
        
        # Verify invoice balance updated
        invoice_after = db.invoices.find_one({"invoice_id": "inv-1a60e27fb6ff"})
        balance_after = invoice_after.get("balance_due", 0)
        
        assert balance_after < balance_before, \
            f"Invoice balance should decrease after payment: before={balance_before}, after={balance_after}"
        
        client.close()
        
        print(f"SUCCESS: Payment allocated to invoice, balance: {balance_before} -> {balance_after}")


class TestRegistrationValidation:
    """Validation tests for registration"""
    
    def test_register_missing_required_fields(self):
        """Registration should fail with missing required fields"""
        # Missing email
        resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
            "password": "Test@12345",
            "name": "Test User"
        })
        assert resp.status_code == 422, f"Missing email should return 422, got {resp.status_code}"
        
        # Missing password
        resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
            "email": "test@test.in",
            "name": "Test User"
        })
        assert resp.status_code == 422, f"Missing password should return 422, got {resp.status_code}"
        
        print("SUCCESS: Missing required fields correctly rejected")
    
    def test_register_invalid_email_format(self):
        """Registration should fail with invalid email format"""
        resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Test@12345",
            "name": "Test User"
        })
        assert resp.status_code == 422, f"Invalid email should return 422, got {resp.status_code}"
        
        print("SUCCESS: Invalid email format correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
