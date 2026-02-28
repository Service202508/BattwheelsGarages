"""
AI Diagnostic Assistant Module Tests
Tests the AI Assistant API endpoints for Admin and Technician portals
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "dev@battwheels.internal"
ADMIN_PASSWORD = "DevTest@123"
TECHNICIAN_EMAIL = "deepak@battwheelsgarages.in"
TECHNICIAN_PASSWORD = "DevTest@123"


class TestAIAssistHealthEndpoint:
    """Test AI Assistant health endpoint"""

    def test_ai_health_endpoint_available(self):
        """Test that AI health endpoint returns available status"""
        response = requests.get(f"{BASE_URL}/api/ai-assist/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "available"
        assert "model" in data
        assert data["model"] == "gemini-3-flash-preview"


class TestAIAssistDiagnoseEndpoint:
    """Test AI Diagnose endpoint with different scenarios"""

    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")

    @pytest.fixture
    def technician_token(self):
        """Get technician authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TECHNICIAN_EMAIL, "password": TECHNICIAN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Technician authentication failed")

    def test_diagnose_battery_issue_admin(self, admin_token):
        """Test AI diagnosis for battery issue from admin portal"""
        payload = {
            "query": "Battery not charging past 80% on Ola S1 Pro",
            "category": "battery",
            "portal_type": "admin",
            "context": {
                "user_name": "Admin User",
                "role": "admin",
                "vehicle_type": "2_wheeler",
                "vehicle_model": "Ola S1 Pro",
                "dtc_codes": "P0A80"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/ai-assist/diagnose",
            json=payload,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data
        assert "ai_enabled" in data
        assert "category" in data
        assert "confidence" in data
        
        # Verify AI response is enabled and has content
        assert data["ai_enabled"] == True
        assert len(data["response"]) > 100  # Should have substantial content
        assert data["category"] == "battery"
        assert data["confidence"] == 0.85

    def test_diagnose_motor_issue_technician(self, technician_token):
        """Test AI diagnosis for motor issue from technician portal"""
        payload = {
            "query": "Motor making grinding noise at high speed. Customer reports reduced power.",
            "category": "motor",
            "portal_type": "technician",
            "context": {
                "user_name": "Deepak Tiwary",
                "role": "technician",
                "vehicle_type": "3_wheeler",
                "vehicle_model": "Mahindra Treo"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/ai-assist/diagnose",
            json=payload,
            headers={
                "Authorization": f"Bearer {technician_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data
        assert "ai_enabled" in data
        assert data["ai_enabled"] == True
        assert len(data["response"]) > 100
        assert data["category"] == "motor"

    def test_diagnose_electrical_issue(self, admin_token):
        """Test AI diagnosis for electrical system issue"""
        payload = {
            "query": "Intermittent power loss while driving. Dashboard shows battery warning.",
            "category": "electrical",
            "portal_type": "admin",
            "context": {
                "user_name": "Admin User",
                "role": "admin",
                "vehicle_type": "car",
                "vehicle_model": "Tata Nexon EV"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/ai-assist/diagnose",
            json=payload,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_enabled"] == True
        assert data["category"] == "electrical"

    def test_diagnose_charging_issue(self, technician_token):
        """Test AI diagnosis for charging system issue"""
        payload = {
            "query": "Scooter not accepting charge from home charger. No lights on charging port.",
            "category": "charging",
            "portal_type": "technician",
            "context": {
                "user_name": "Deepak Tiwary",
                "role": "technician",
                "vehicle_type": "2_wheeler",
                "vehicle_model": "Ather 450X"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/ai-assist/diagnose",
            json=payload,
            headers={
                "Authorization": f"Bearer {technician_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_enabled"] == True
        # Charging may be mapped to battery or general category
        assert data["category"] in ["charging", "battery", "general"]

    def test_diagnose_with_dtc_codes(self, admin_token):
        """Test AI diagnosis with DTC error codes included"""
        payload = {
            "query": "Vehicle Type: 2 Wheeler\nVehicle Model: Ola S1 Pro\nIssue Category: Battery Issues\nDTC Codes: P0A80, U0100\n\nIssue Description:\nBattery not holding charge. Shows 100% but dies within 10km.",
            "category": "battery",
            "portal_type": "admin",
            "context": {
                "user_name": "Admin User",
                "role": "admin",
                "vehicle_type": "2_wheeler",
                "vehicle_model": "Ola S1 Pro",
                "dtc_codes": "P0A80, U0100"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/ai-assist/diagnose",
            json=payload,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_enabled"] == True
        # Response should mention the DTC codes
        assert "P0A80" in data["response"] or "DTC" in data["response"] or "error" in data["response"].lower()

    def test_diagnose_minimal_input(self, admin_token):
        """Test AI diagnosis with minimal input (only query)"""
        payload = {
            "query": "Scooter won't start",
            "category": "general",
            "portal_type": "admin"
        }
        response = requests.post(
            f"{BASE_URL}/api/ai-assist/diagnose",
            json=payload,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_enabled"] == True
        assert len(data["response"]) > 50


class TestAuthenticationEndpoints:
    """Test authentication for AI Assistant access"""

    def test_admin_login_success(self):
        """Test admin login returns valid token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == ADMIN_EMAIL

    def test_technician_login_success(self):
        """Test technician login returns valid token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TECHNICIAN_EMAIL, "password": TECHNICIAN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "technician"
        assert data["user"]["email"] == TECHNICIAN_EMAIL

    def test_invalid_login_rejected(self):
        """Test invalid credentials are rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrong_pwd_placeholder"}
        )
        assert response.status_code == 401
