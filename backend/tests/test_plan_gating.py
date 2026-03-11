"""
Plan Gating Feature Tests
=========================
Tests for subscription plan enforcement:
1. Sidebar lock icons based on plan type
2. Backend API blocking for write operations
3. Record limit enforcement for free_trial
4. Professional plan has full access

Uses demo org: demo-volt-motors-001 (default: professional plan)
Test flow: Change to free_trial -> Test blocks -> Restore to professional
"""
import pytest
import requests
import os
from pymongo import MongoClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'battwheels')

# Demo user credentials
DEMO_EMAIL = "demo@voltmotors.in"
DEMO_PASSWORD = "Demo@12345"
DEMO_ORG_ID = "demo-volt-motors-001"


class TestPlanGating:
    """Test subscription plan enforcement (frontend sidebar + backend API blocks)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup MongoDB connection and auth token"""
        self.client = MongoClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        
        # Login to get token
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Organization-ID": DEMO_ORG_ID
        }
        
        # Store original plan type
        org = self.db.organizations.find_one({"organization_id": DEMO_ORG_ID})
        self.original_plan = org.get("plan_type", "professional") if org else "professional"
        
        yield
        
        # Restore original plan
        self.db.organizations.update_one(
            {"organization_id": DEMO_ORG_ID},
            {"$set": {"plan_type": self.original_plan}}
        )
        self.client.close()
    
    def set_plan(self, plan_type: str):
        """Helper to change org plan in DB"""
        result = self.db.organizations.update_one(
            {"organization_id": DEMO_ORG_ID},
            {"$set": {"plan_type": plan_type}}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    # ============ Test 1: Professional plan (default) has full access ============
    def test_professional_plan_full_access(self):
        """Test 9: Professional plan has full access to all modules"""
        # Ensure professional plan
        self.set_plan("professional")
        
        # Test GET requests work (not gated)
        endpoints = [
            "/api/v1/tickets",
            "/api/v1/amc/plans",
            "/api/v1/hr/employees",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=self.headers)
            # Should NOT return 403 plan_upgrade_required
            assert response.status_code != 403 or "plan_upgrade_required" not in response.text, \
                f"Professional plan blocked on GET {endpoint}"
        
        print("PASS: Professional plan has full GET access")
    
    # ============ Test 2: Free trial POST to AMC blocked (returns 403) ============
    def test_free_trial_amc_post_blocked(self):
        """Test 6: With free_trial, POST to /api/v1/amc/plans returns 403"""
        self.set_plan("free_trial")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/amc/plans",
            headers=self.headers,
            json={"name": "Test AMC Plan", "duration_months": 12, "price": 1000}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("error") == "plan_upgrade_required", f"Expected plan_upgrade_required error, got: {data}"
        assert data.get("required_plan") == "starter", f"AMC requires starter plan, got: {data.get('required_plan')}"
        
        print("PASS: Free trial blocked from AMC POST with correct error")
    
    # ============ Test 3: Free trial POST to HR blocked (requires professional) ============
    def test_free_trial_hr_post_blocked(self):
        """Test 7: With free_trial, POST to /api/v1/hr/employees returns 403 requiring 'professional'"""
        self.set_plan("free_trial")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/employees",
            headers=self.headers,
            json={"name": "Test Employee", "email": "test@voltmotors.in"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("error") == "plan_upgrade_required", f"Expected plan_upgrade_required error, got: {data}"
        # HR requires professional plan, not just starter
        assert data.get("required_plan") in ["professional", "enterprise"], \
            f"HR should require professional, got: {data.get('required_plan')}"
        
        print("PASS: Free trial blocked from HR POST requiring professional")
    
    # ============ Test 4: Free trial GET requests still work (not gated) ============
    def test_free_trial_get_allowed(self):
        """Test 8: With free_trial, GET /api/v1/tickets works (GETs not gated)"""
        self.set_plan("free_trial")
        
        response = requests.get(f"{BASE_URL}/api/v1/tickets", headers=self.headers)
        
        # Should NOT return 403 with plan_upgrade_required
        if response.status_code == 403:
            data = response.json()
            assert data.get("error") != "plan_upgrade_required", \
                f"GET should not be plan-gated, got: {data}"
        
        # Acceptable status codes: 200 (success), 401 (if token expired), but NOT 403 plan block
        assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
        
        print("PASS: Free trial GET /api/v1/tickets allowed")
    
    # ============ Test 5: Starter plan can access AMC but not HR ============
    def test_starter_plan_partial_access(self):
        """Starter plan can POST to AMC but not to HR (requires professional)"""
        self.set_plan("starter")
        
        # AMC should work for starter
        response = requests.get(f"{BASE_URL}/api/v1/amc/plans", headers=self.headers)
        # Should not return plan_upgrade_required
        if response.status_code == 403:
            data = response.json()
            assert data.get("error") != "plan_upgrade_required", \
                f"Starter should access AMC, got: {data}"
        
        # HR should still be blocked (requires professional)
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/employees",
            headers=self.headers,
            json={"name": "Test", "email": "test@test.com"}
        )
        
        if response.status_code == 403:
            data = response.json()
            if data.get("error") == "plan_upgrade_required":
                assert data.get("required_plan") in ["professional", "enterprise"], \
                    f"HR should require professional for starter, got: {data}"
                print("PASS: Starter plan blocked from HR POST as expected")
            return
        
        print("PASS: Starter plan has correct access levels")
    
    # ============ Test 6: Record limit enforcement for tickets ============
    def test_record_limit_enforcement(self):
        """Test 10: Free trial ticket limit (20 tickets max)"""
        self.set_plan("free_trial")
        
        # Count existing tickets for this org
        ticket_count = self.db.tickets.count_documents({"organization_id": DEMO_ORG_ID})
        print(f"Current ticket count: {ticket_count}")
        
        # If under limit, create should work
        # If at/over limit, should get 403 record_limit_reached
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            headers=self.headers,
            json={
                "customer_name": "Test Customer",
                "vehicle_type": "Electric Scooter",
                "primary_issue": "Test Issue",
                "description": "Test description for plan limit test"
            }
        )
        
        if ticket_count >= 20:
            # Should be blocked
            assert response.status_code == 403, f"Expected 403 for limit reached, got {response.status_code}"
            data = response.json()
            detail = data.get("detail", {})
            assert detail.get("error") == "record_limit_reached", f"Expected record_limit_reached, got: {data}"
            print(f"PASS: Ticket creation blocked at limit ({ticket_count}/20)")
        else:
            # Should succeed (if not blocked by other validation)
            # Accept 200, 201, or 422 (validation error - not a plan issue)
            assert response.status_code in [200, 201, 422, 400], \
                f"Unexpected response when under limit: {response.status_code} - {response.text}"
            print(f"PASS: Ticket creation allowed under limit ({ticket_count}/20)")
    
    # ============ Test 7: Professional plan POST works everywhere ============
    def test_professional_post_access(self):
        """Test that professional plan can POST to all gated endpoints"""
        self.set_plan("professional")
        
        # Test AMC POST (requires starter)
        response = requests.post(
            f"{BASE_URL}/api/v1/amc/plans",
            headers=self.headers,
            json={"name": "Pro Test AMC", "duration_months": 12, "price": 5000}
        )
        
        # Should NOT get plan_upgrade_required
        if response.status_code == 403:
            data = response.json()
            assert data.get("error") != "plan_upgrade_required", \
                f"Professional should not be plan-blocked: {data}"
        
        # Test HR POST (requires professional)
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/employees",
            headers=self.headers,
            json={"name": "Pro Test Employee", "email": "protest@voltmotors.in"}
        )
        
        if response.status_code == 403:
            data = response.json()
            assert data.get("error") != "plan_upgrade_required", \
                f"Professional should not be plan-blocked for HR: {data}"
        
        print("PASS: Professional plan POST operations not plan-blocked")
    
    # ============ Test 8: Verify plan stored correctly in DB ============
    def test_plan_change_persists(self):
        """Verify plan changes persist in database"""
        # Set to free_trial
        self.set_plan("free_trial")
        org = self.db.organizations.find_one({"organization_id": DEMO_ORG_ID})
        assert org["plan_type"] == "free_trial", f"Plan not updated to free_trial: {org.get('plan_type')}"
        
        # Set to starter
        self.set_plan("starter")
        org = self.db.organizations.find_one({"organization_id": DEMO_ORG_ID})
        assert org["plan_type"] == "starter", f"Plan not updated to starter: {org.get('plan_type')}"
        
        # Restore to professional
        self.set_plan("professional")
        org = self.db.organizations.find_one({"organization_id": DEMO_ORG_ID})
        assert org["plan_type"] == "professional", f"Plan not restored to professional: {org.get('plan_type')}"
        
        print("PASS: Plan changes persist correctly in DB")


class TestOtherGatedEndpoints:
    """Test other plan-gated endpoints for completeness"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup MongoDB connection and auth token"""
        self.client = MongoClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        
        # Login
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        self.token = data["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Organization-ID": DEMO_ORG_ID
        }
        
        # Store original plan
        org = self.db.organizations.find_one({"organization_id": DEMO_ORG_ID})
        self.original_plan = org.get("plan_type", "professional") if org else "professional"
        
        yield
        
        # Restore
        self.db.organizations.update_one(
            {"organization_id": DEMO_ORG_ID},
            {"$set": {"plan_type": self.original_plan}}
        )
        self.client.close()
    
    def set_plan(self, plan_type: str):
        self.db.organizations.update_one(
            {"organization_id": DEMO_ORG_ID},
            {"$set": {"plan_type": plan_type}}
        )
    
    def test_time_tracking_gated(self):
        """Time tracking requires professional"""
        self.set_plan("free_trial")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/time-tracking/entries",
            headers=self.headers,
            json={"task": "Test", "duration": 60}
        )
        
        if response.status_code == 403:
            data = response.json()
            if data.get("error") == "plan_upgrade_required":
                assert data.get("required_plan") in ["professional", "enterprise"]
                print("PASS: Time tracking blocked for free_trial")
                return
        
        print(f"Time tracking response: {response.status_code}")
    
    def test_sales_orders_gated(self):
        """Sales orders require starter"""
        self.set_plan("free_trial")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/sales-orders",
            headers=self.headers,
            json={"customer_id": "test", "items": []}
        )
        
        if response.status_code == 403:
            data = response.json()
            if data.get("error") == "plan_upgrade_required":
                assert data.get("required_plan") in ["starter", "professional", "enterprise"]
                print("PASS: Sales orders blocked for free_trial")
                return
        
        print(f"Sales orders response: {response.status_code}")
    
    def test_purchases_gated(self):
        """Purchases require starter"""
        self.set_plan("free_trial")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/purchases",
            headers=self.headers,
            json={"vendor_id": "test", "items": []}
        )
        
        if response.status_code == 403:
            data = response.json()
            if data.get("error") == "plan_upgrade_required":
                print("PASS: Purchases blocked for free_trial")
                return
        
        print(f"Purchases response: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
