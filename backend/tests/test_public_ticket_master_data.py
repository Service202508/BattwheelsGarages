"""
Battwheels OS - Public Ticket Submission & Master Data Tests
Tests for:
- Vehicle Categories, Models, Issue Suggestions master data APIs
- Public ticket submission flow with Individual/Business customer types
- Payment flow for Individual + OnSite (Razorpay mock mode)
- Public ticket tracking and lookup
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://production-ready-64.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


class TestMasterDataSeed:
    """Test master data seeding endpoint"""
    
    def test_seed_master_data(self):
        """Seed master data - should work or indicate already seeded"""
        response = requests.post(f"{API}/master-data/seed")
        assert response.status_code == 200
        data = response.json()
        # Either returns seeded counts or "already exists" message
        assert "message" in data or "categories" in data


class TestPublicVehicleCategories:
    """Test public vehicle categories API"""
    
    def test_get_vehicle_categories(self):
        """Get all active vehicle categories"""
        response = requests.get(f"{API}/public/vehicle-categories")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert len(data["categories"]) >= 5
        
        # Verify category structure
        for cat in data["categories"]:
            assert "code" in cat
            assert "name" in cat
            assert "category_id" in cat
        
        # Verify expected categories exist
        codes = [c["code"] for c in data["categories"]]
        assert "2W_EV" in codes  # Two Wheeler
        assert "3W_EV" in codes  # Three Wheeler
        assert "4W_EV" in codes  # Four Wheeler


class TestPublicVehicleModels:
    """Test public vehicle models API"""
    
    def test_get_all_models(self):
        """Get all vehicle models"""
        response = requests.get(f"{API}/public/vehicle-models")
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "by_oem" in data
        assert len(data["models"]) >= 10  # Should have ~21 models
    
    def test_get_models_by_category(self):
        """Get models filtered by category"""
        response = requests.get(f"{API}/public/vehicle-models?category_code=2W_EV")
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        # Verify all returned models are 2W_EV
        for model in data["models"]:
            assert model["category_code"] == "2W_EV"
        
        # Should have OEM grouping
        assert "by_oem" in data
        # Verify popular 2W OEMs
        oems = list(data["by_oem"].keys())
        assert "Ola Electric" in oems or "Ather Energy" in oems
    
    def test_model_has_required_fields(self):
        """Verify model data structure"""
        response = requests.get(f"{API}/public/vehicle-models?category_code=2W_EV")
        assert response.status_code == 200
        data = response.json()
        
        for model in data["models"]:
            assert "model_id" in model
            assert "name" in model
            assert "oem" in model
            assert "category_code" in model


class TestPublicIssueSuggestions:
    """Test public issue suggestions API"""
    
    def test_get_issue_suggestions(self):
        """Get issue suggestions for a category"""
        response = requests.get(f"{API}/public/issue-suggestions?category_code=2W_EV")
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert len(data["suggestions"]) >= 5
    
    def test_suggestion_has_required_fields(self):
        """Verify suggestion data structure"""
        response = requests.get(f"{API}/public/issue-suggestions")
        assert response.status_code == 200
        data = response.json()
        
        for suggestion in data["suggestions"]:
            assert "suggestion_id" in suggestion
            assert "title" in suggestion
            assert "issue_type" in suggestion
    
    def test_suggestions_have_common_symptoms(self):
        """Verify suggestions include common symptoms"""
        response = requests.get(f"{API}/public/issue-suggestions?category_code=2W_EV")
        assert response.status_code == 200
        data = response.json()
        
        # At least some suggestions should have symptoms
        has_symptoms = any(s.get("common_symptoms") for s in data["suggestions"])
        assert has_symptoms


class TestServiceCharges:
    """Test service charges endpoint"""
    
    def test_get_service_charges(self):
        """Get current service charge rates"""
        response = requests.get(f"{API}/public/service-charges")
        assert response.status_code == 200
        data = response.json()
        
        assert "visit_fee" in data
        assert "diagnostic_fee" in data
        
        # Verify amounts
        assert data["visit_fee"]["amount"] == 299
        assert data["diagnostic_fee"]["amount"] == 199
        assert data["visit_fee"]["currency"] == "INR"


class TestPublicTicketSubmission:
    """Test public ticket submission flow"""
    
    def test_submit_business_ticket_no_payment(self):
        """Business customer submission should not require payment"""
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "4W_EV",
            "vehicle_model_id": "vmod_tata_nexon_ev",
            "vehicle_number": f"MH12BIZ{unique_id}",
            "customer_type": "business",
            "customer_name": f"TEST_Business_{unique_id}",
            "contact_number": "9800000001",
            "email": f"test_{unique_id}@example.com",
            "business_name": "Test Fleet Co",
            "gst_number": "22AAAAA0000A1Z5",
            "title": "Motor issue",
            "description": "Test description for business ticket",
            "issue_type": "motor",
            "priority": "medium",
            "resolution_type": "workshop"
        }
        
        response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "ticket_id" in data
        assert data["requires_payment"] == False
        assert data["status"] == "open"
        assert "tracking_url" in data
    
    def test_submit_individual_workshop_no_payment(self):
        """Individual customer with workshop visit should not require payment"""
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "2W_EV",
            "vehicle_model_id": "vmod_ather_450x",
            "vehicle_number": f"KA01IND{unique_id}",
            "customer_type": "individual",
            "customer_name": f"TEST_Individual_{unique_id}",
            "contact_number": "9800000002",
            "email": f"test_ind_{unique_id}@example.com",
            "title": "Battery issue",
            "description": "Battery not holding charge",
            "issue_type": "battery",
            "priority": "high",
            "resolution_type": "workshop"  # Workshop - no payment required
        }
        
        response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["requires_payment"] == False
        assert data["status"] == "open"
    
    def test_submit_individual_onsite_requires_payment(self):
        """Individual customer with onsite resolution should require payment"""
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "2W_EV",
            "vehicle_model_id": "vmod_ola_s1_pro",
            "vehicle_number": f"MH12PAY{unique_id}",
            "customer_type": "individual",
            "customer_name": f"TEST_Payment_{unique_id}",
            "contact_number": "9800000003",
            "email": f"test_pay_{unique_id}@example.com",
            "title": "Charging issue",
            "description": "Charger not connecting",
            "issue_type": "charging",
            "priority": "medium",
            "resolution_type": "onsite",  # OnSite - payment required
            "incident_location": "Mumbai, Maharashtra",
            "include_visit_fee": True,
            "include_diagnostic_fee": False
        }
        
        response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["requires_payment"] == True
        assert data["status"] == "pending_payment"
        assert "payment_details" in data
        
        # Verify payment details
        payment = data["payment_details"]
        assert payment["visit_fee"] == 299
        assert payment["amount"] == 299  # Only visit fee since diagnostic not included
        assert payment["currency"] == "INR"
        assert "order_id" in payment
        assert payment["is_mock"] == True  # Mock mode when Razorpay not configured
        
        return data  # Return for use in other tests
    
    def test_submit_individual_onsite_with_diagnostic(self):
        """Individual + OnSite + Diagnostic should have ₹498 total"""
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "2W_EV",
            "vehicle_model_id": "vmod_tvs_iqube",
            "vehicle_number": f"TN01FULL{unique_id}",
            "customer_type": "individual",
            "customer_name": f"TEST_FullPayment_{unique_id}",
            "contact_number": "9800000004",
            "title": "Display not working",
            "description": "Dashboard screen blank",
            "issue_type": "controller",
            "priority": "high",
            "resolution_type": "onsite",
            "incident_location": "Chennai, Tamil Nadu",
            "include_visit_fee": True,
            "include_diagnostic_fee": True  # Both fees
        }
        
        response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["requires_payment"] == True
        payment = data["payment_details"]
        assert payment["visit_fee"] == 299
        assert payment["diagnostic_fee"] == 199
        assert payment["amount"] == 498  # 299 + 199


class TestPaymentVerification:
    """Test payment verification flow"""
    
    def test_verify_mock_payment(self):
        """Verify mock payment completes successfully"""
        # First create a ticket requiring payment
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "2W_EV",
            "vehicle_number": f"MH12VER{unique_id}",
            "customer_type": "individual",
            "customer_name": f"TEST_Verify_{unique_id}",
            "contact_number": "9800000005",
            "title": "Test payment verification",
            "description": "Testing payment flow",
            "issue_type": "general",
            "priority": "low",
            "resolution_type": "onsite",
            "incident_location": "Test Location",
            "include_visit_fee": True
        }
        
        create_response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        
        ticket_id = create_data["ticket_id"]
        order_id = create_data["payment_details"]["order_id"]
        
        # Verify payment
        verify_data = {
            "ticket_id": ticket_id,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": f"pay_mock_{unique_id}",
            "razorpay_signature": "mock_signature"
        }
        
        verify_response = requests.post(f"{API}/public/tickets/verify-payment", json=verify_data)
        assert verify_response.status_code == 200
        verify_result = verify_response.json()
        
        assert verify_result["status"] == "open"
        assert "ticket_id" in verify_result


class TestPublicTicketTracking:
    """Test public ticket tracking functionality"""
    
    def test_lookup_by_ticket_id(self):
        """Lookup ticket by ID"""
        # First create a ticket
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "3W_EV",
            "vehicle_number": f"AP01LOOK{unique_id}",
            "customer_type": "business",
            "customer_name": f"TEST_Lookup_{unique_id}",
            "contact_number": "9800000006",
            "title": "Test lookup",
            "description": "Testing ticket lookup",
            "issue_type": "motor",
            "resolution_type": "workshop"
        }
        
        create_response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        ticket_id = create_response.json()["ticket_id"]
        
        # Lookup by ticket ID
        lookup_response = requests.post(
            f"{API}/public/tickets/lookup",
            json={"ticket_id": ticket_id}
        )
        assert lookup_response.status_code == 200
        data = lookup_response.json()
        
        assert "tickets" in data
        assert len(data["tickets"]) >= 1
        assert data["tickets"][0]["ticket_id"] == ticket_id
    
    def test_lookup_by_phone(self):
        """Lookup tickets by phone number"""
        unique_phone = "9811223344"
        
        # Create a ticket with known phone
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "2W_EV",
            "vehicle_number": f"DL01PHN{unique_id}",
            "customer_type": "individual",
            "customer_name": f"TEST_Phone_{unique_id}",
            "contact_number": unique_phone,
            "title": "Test phone lookup",
            "description": "Testing phone lookup",
            "issue_type": "battery",
            "resolution_type": "workshop"
        }
        
        requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        
        # Lookup by phone
        lookup_response = requests.post(
            f"{API}/public/tickets/lookup",
            json={"contact_number": unique_phone}
        )
        assert lookup_response.status_code == 200
        data = lookup_response.json()
        assert len(data["tickets"]) >= 1
    
    def test_get_ticket_details_with_token(self):
        """Get detailed ticket info with access token"""
        # Create ticket
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "4W_EV",
            "vehicle_model_id": "vmod_mg_zs_ev",
            "vehicle_number": f"GJ01DET{unique_id}",
            "customer_type": "business",
            "customer_name": f"TEST_Details_{unique_id}",
            "contact_number": "9800000007",
            "title": "Test details retrieval",
            "description": "Testing detailed view",
            "issue_type": "charging",
            "resolution_type": "pickup"
        }
        
        create_response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        create_data = create_response.json()
        ticket_id = create_data["ticket_id"]
        token = create_data["tracking_url"].split("token=")[1]
        
        # Get details
        details_response = requests.get(
            f"{API}/public/tickets/{ticket_id}?token={token}"
        )
        assert details_response.status_code == 200
        details = details_response.json()
        
        assert "ticket" in details
        assert details["ticket"]["ticket_id"] == ticket_id
        assert details["ticket"]["vehicle_model"] == "ZS EV"
        assert details["ticket"]["vehicle_oem"] == "MG Motor"
        assert "status_history" in details["ticket"]
    
    def test_get_ticket_without_token_fails(self):
        """Access without proper token should fail"""
        # Create ticket
        unique_id = uuid.uuid4().hex[:8]
        ticket_data = {
            "vehicle_category": "2W_EV",
            "vehicle_number": f"RJ01SEC{unique_id}",
            "customer_type": "individual",
            "customer_name": f"TEST_Security_{unique_id}",
            "contact_number": "9800000008",
            "title": "Test security",
            "description": "Testing access control",
            "issue_type": "general",
            "resolution_type": "remote"
        }
        
        create_response = requests.post(f"{API}/public/tickets/submit", json=ticket_data)
        ticket_id = create_response.json()["ticket_id"]
        
        # Try to access without token
        details_response = requests.get(f"{API}/public/tickets/{ticket_id}")
        assert details_response.status_code == 403


class TestMasterDataInternalAPI:
    """Test authenticated master data API endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth token for internal APIs"""
        login_response = requests.post(
            f"{API}/auth/login",
            json={"email": "admin@battwheels.in", "password": "test_pwd_placeholder"}
        )
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Admin authentication failed")
    
    def test_get_internal_vehicle_categories(self, auth_headers):
        """Internal API for vehicle categories"""
        response = requests.get(
            f"{API}/master-data/vehicle-categories",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data
    
    def test_get_internal_vehicle_models(self, auth_headers):
        """Internal API for vehicle models"""
        response = requests.get(
            f"{API}/master-data/vehicle-models?category_code=4W_EV",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        # Should have 4W EV models like Tata Nexon, MG ZS, etc.
        oems = list(data.get("by_oem", {}).keys())
        assert "Tata Motors" in oems or "MG Motor" in oems
    
    def test_get_internal_issue_suggestions(self, auth_headers):
        """Internal API for issue suggestions"""
        response = requests.get(
            f"{API}/master-data/issue-suggestions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
