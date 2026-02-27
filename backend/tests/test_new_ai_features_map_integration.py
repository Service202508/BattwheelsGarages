"""
Test suite for new Battwheels OS features:
1. AI Issue Suggestions (Gemini-powered) for public ticket form
2. Business Portal APIs
3. Technician AI Assistant API
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
BUSINESS_CREDS = {"email": "business@bluwheelz.co.in", "password": "business123"}
TECHNICIAN_CREDS = {"email": "deepak@battwheelsgarages.in", "password": "DevTest@123"}


class TestAIIssueSuggestions:
    """Test AI-powered issue suggestions endpoint"""
    
    def test_ai_suggestions_battery_issue(self):
        """Test AI suggestions for battery-related input"""
        response = requests.post(
            f"{BASE_URL}/api/public/ai/issue-suggestions",
            json={
                "vehicle_category": "2W_EV",
                "vehicle_model": "Ather 450X",
                "vehicle_oem": "Ather",
                "user_input": "battery draining fast not holding charge"
            },
            timeout=30
        )
        print(f"AI Suggestions Response: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        # Should have at least one suggestion
        if data.get("ai_enabled"):
            assert len(data["suggestions"]) >= 1
            # Each suggestion should have required fields
            for suggestion in data["suggestions"]:
                assert "title" in suggestion
                assert "issue_type" in suggestion
                assert "severity" in suggestion
    
    def test_ai_suggestions_motor_issue(self):
        """Test AI suggestions for motor-related input"""
        response = requests.post(
            f"{BASE_URL}/api/public/ai/issue-suggestions",
            json={
                "vehicle_category": "4W_EV",
                "vehicle_model": "Tata Nexon EV",
                "vehicle_oem": "Tata",
                "user_input": "motor making grinding noise when accelerating"
            },
            timeout=30
        )
        print(f"Motor AI Suggestions: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    def test_ai_suggestions_minimal_input(self):
        """Test AI suggestions with minimal input"""
        response = requests.post(
            f"{BASE_URL}/api/public/ai/issue-suggestions",
            json={
                "vehicle_category": "3W_EV",
                "user_input": "not starting"
            },
            timeout=30
        )
        print(f"Minimal input suggestions: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data


class TestBusinessPortalAPIs:
    """Test Business Customer Portal APIs"""
    
    @pytest.fixture
    def business_auth(self):
        """Get business customer auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=BUSINESS_CREDS
        )
        print(f"Business login: {response.status_code}")
        if response.status_code != 200:
            pytest.skip("Business login failed - cannot test business APIs")
        
        data = response.json()
        token = data.get("token")
        cookies = {"session_token": token}
        headers = {"Authorization": f"Bearer {token}"}
        return {"cookies": cookies, "headers": headers}
    
    def test_business_dashboard(self, business_auth):
        """Test business dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/business/dashboard",
            cookies=business_auth["cookies"],
            headers=business_auth["headers"]
        )
        print(f"Business Dashboard: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        # Dashboard should have key sections
        assert "business" in data
        assert "fleet" in data
        assert "tickets" in data
        assert "financials" in data
    
    def test_business_fleet(self, business_auth):
        """Test business fleet endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/business/fleet",
            cookies=business_auth["cookies"],
            headers=business_auth["headers"]
        )
        print(f"Business Fleet: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "vehicles" in data
        assert "total" in data
    
    def test_business_tickets(self, business_auth):
        """Test business tickets endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/business/tickets",
            cookies=business_auth["cookies"],
            headers=business_auth["headers"]
        )
        print(f"Business Tickets: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "total" in data
    
    def test_business_invoices(self, business_auth):
        """Test business invoices endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/business/invoices",
            cookies=business_auth["cookies"],
            headers=business_auth["headers"]
        )
        print(f"Business Invoices: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        assert "summary" in data


class TestTechnicianAIAssistant:
    """Test Technician AI Assistant API"""
    
    @pytest.fixture
    def technician_auth(self):
        """Get technician auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TECHNICIAN_CREDS
        )
        print(f"Technician login: {response.status_code}")
        if response.status_code != 200:
            pytest.skip("Technician login failed - cannot test technician AI API")
        
        data = response.json()
        token = data.get("token")
        cookies = {"session_token": token}
        headers = {"Authorization": f"Bearer {token}"}
        return {"cookies": cookies, "headers": headers, "user": data.get("user", {})}
    
    def test_technician_ai_assist_battery_query(self, technician_auth):
        """Test AI assist for battery diagnosis query"""
        response = requests.post(
            f"{BASE_URL}/api/technician/ai-assist",
            json={
                "query": "How to diagnose BMS communication error on Ather 450X?",
                "category": "battery",
                "context": {
                    "technician_name": technician_auth.get("user", {}).get("name", "Technician"),
                    "role": "technician"
                }
            },
            cookies=technician_auth["cookies"],
            headers=technician_auth["headers"],
            timeout=60
        )
        print(f"AI Assist Battery Query: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Response should be a non-empty string
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 50  # Should have substantial content
    
    def test_technician_ai_assist_motor_query(self, technician_auth):
        """Test AI assist for motor diagnosis query"""
        response = requests.post(
            f"{BASE_URL}/api/technician/ai-assist",
            json={
                "query": "Motor controller overheating troubleshooting steps",
                "category": "motor",
                "context": {
                    "technician_name": "Test Technician",
                    "role": "technician"
                }
            },
            cookies=technician_auth["cookies"],
            headers=technician_auth["headers"],
            timeout=60
        )
        print(f"AI Assist Motor Query: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_technician_ai_assist_general_query(self, technician_auth):
        """Test AI assist for general EV query"""
        response = requests.post(
            f"{BASE_URL}/api/technician/ai-assist",
            json={
                "query": "What are the common causes of range reduction in EVs?",
                "category": "general"
            },
            cookies=technician_auth["cookies"],
            headers=technician_auth["headers"],
            timeout=60
        )
        print(f"AI Assist General Query: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestTechnicianDashboard:
    """Test Technician Portal Dashboard API"""
    
    @pytest.fixture
    def technician_auth(self):
        """Get technician auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TECHNICIAN_CREDS
        )
        if response.status_code != 200:
            pytest.skip("Technician login failed")
        
        data = response.json()
        token = data.get("token")
        cookies = {"session_token": token}
        headers = {"Authorization": f"Bearer {token}"}
        return {"cookies": cookies, "headers": headers}
    
    def test_technician_dashboard(self, technician_auth):
        """Test technician dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/technician/dashboard",
            cookies=technician_auth["cookies"],
            headers=technician_auth["headers"]
        )
        print(f"Technician Dashboard: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "technician" in data
        assert "tickets" in data
        assert "performance" in data
        assert "attendance" in data


class TestPublicTicketForm:
    """Test public ticket form related APIs"""
    
    def test_vehicle_categories(self):
        """Test vehicle categories for public form"""
        response = requests.get(f"{BASE_URL}/api/public/vehicle-categories")
        print(f"Vehicle Categories: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
    
    def test_vehicle_models(self):
        """Test vehicle models for public form"""
        response = requests.get(f"{BASE_URL}/api/public/vehicle-models?category_code=2W_EV")
        print(f"Vehicle Models: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
    
    def test_service_charges(self):
        """Test service charges endpoint"""
        response = requests.get(f"{BASE_URL}/api/public/service-charges")
        print(f"Service Charges: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "visit_fee" in data
        assert "diagnostic_fee" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
