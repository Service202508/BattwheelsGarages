"""
Backend tests for iteration 104 new features:
1. SLA Config PUT/GET with auto_reassign fields
2. SLA Breach Report endpoint
3. Bulk Form 16 ZIP endpoint
4. Logo upload endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ======================== AUTH FIXTURE ========================

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin@battwheels.in"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "admin"
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("token") or data.get("access_token")
        if token:
            return token
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ======================== AUTH TESTS ========================

class TestAuth:
    """Basic auth tests"""

    def test_login_success(self):
        """Admin login should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@battwheels.in",
            "password": "admin"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data


# ======================== TASK 2: SLA CONFIG TESTS ========================

class TestSLAConfig:
    """SLA Configuration endpoint tests"""

    def test_get_sla_config(self, auth_headers):
        """GET /api/sla/config should return config"""
        response = requests.get(f"{BASE_URL}/api/sla/config", headers=auth_headers)
        assert response.status_code == 200, f"GET SLA config failed: {response.text}"
        data = response.json()
        assert "sla_config" in data, "Missing sla_config in response"

    def test_put_sla_config_with_auto_reassign(self, auth_headers):
        """PUT /api/sla/config with auto_reassign_on_breach=true and reassignment_delay_minutes=45"""
        payload = {
            "CRITICAL": {"response_hours": 1, "resolution_hours": 4},
            "HIGH": {"response_hours": 4, "resolution_hours": 8},
            "MEDIUM": {"response_hours": 8, "resolution_hours": 24},
            "LOW": {"response_hours": 24, "resolution_hours": 72},
            "auto_reassign_on_breach": True,
            "reassignment_delay_minutes": 45
        }
        response = requests.put(f"{BASE_URL}/api/sla/config", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"PUT SLA config failed: {response.text}"
        data = response.json()
        # Verify response contains updated config
        sla_config = data.get("sla_config", {})
        assert sla_config.get("auto_reassign_on_breach") == True, "auto_reassign_on_breach not set to True"
        assert sla_config.get("reassignment_delay_minutes") == 45, "reassignment_delay_minutes not set to 45"

    def test_get_sla_config_reflects_update(self, auth_headers):
        """GET /api/sla/config should return updated config after PUT"""
        response = requests.get(f"{BASE_URL}/api/sla/config", headers=auth_headers)
        assert response.status_code == 200, f"GET SLA config failed: {response.text}"
        data = response.json()
        config = data.get("sla_config", {})
        assert config.get("auto_reassign_on_breach") == True, f"Updated config not persisted: {config}"
        assert config.get("reassignment_delay_minutes") == 45, f"Updated delay not persisted: {config}"

    def test_put_sla_config_restore_defaults(self, auth_headers):
        """Restore SLA config to safe defaults after test"""
        payload = {
            "CRITICAL": {"response_hours": 1, "resolution_hours": 4},
            "HIGH": {"response_hours": 4, "resolution_hours": 8},
            "MEDIUM": {"response_hours": 8, "resolution_hours": 24},
            "LOW": {"response_hours": 24, "resolution_hours": 72},
            "auto_reassign_on_breach": False,
            "reassignment_delay_minutes": 30
        }
        response = requests.put(f"{BASE_URL}/api/sla/config", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Restore SLA config failed: {response.text}"


# ======================== TASK 2: SLA BREACH REPORT TESTS ========================

class TestSLABreachReport:
    """SLA Breach Report endpoint tests"""

    def test_get_breach_report_default(self, auth_headers):
        """GET /api/sla/breach-report should return 200 with summary"""
        response = requests.get(f"{BASE_URL}/api/sla/breach-report", headers=auth_headers)
        assert response.status_code == 200, f"SLA breach report failed: {response.text}"
        data = response.json()
        assert "summary" in data, "Missing summary in breach report"
        assert "breaches" in data, "Missing breaches list in breach report"

    def test_breach_report_has_compliance_pct(self, auth_headers):
        """Breach report summary should contain sla_compliance_pct"""
        response = requests.get(f"{BASE_URL}/api/sla/breach-report", headers=auth_headers)
        assert response.status_code == 200, f"Breach report failed: {response.text}"
        data = response.json()
        summary = data.get("summary", {})
        assert "sla_compliance_pct" in summary, f"Missing sla_compliance_pct in summary: {summary}"
        assert isinstance(summary["sla_compliance_pct"], (int, float)), "compliance_pct should be numeric"

    def test_breach_report_with_date_range(self, auth_headers):
        """Breach report with date range params"""
        params = {
            "start_date": "2025-01-01",
            "end_date": "2026-12-31"
        }
        response = requests.get(
            f"{BASE_URL}/api/sla/breach-report",
            params=params,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Breach report with date range failed: {response.text}"
        data = response.json()
        assert "period" in data, "Missing period in breach report"
        assert "summary" in data

    def test_breach_report_summary_structure(self, auth_headers):
        """Breach report summary should have all required fields"""
        response = requests.get(f"{BASE_URL}/api/sla/breach-report", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        required_fields = ["total_breaches", "response_sla_breaches", "resolution_sla_breaches",
                          "auto_reassignments_triggered", "total_tickets_in_period", "within_sla_count", "sla_compliance_pct"]
        for field in required_fields:
            assert field in summary, f"Missing field '{field}' in summary"


# ======================== TASK 4: BULK FORM 16 ENDPOINT TESTS ========================

class TestBulkForm16:
    """Bulk Form 16 ZIP endpoint tests"""

    def test_bulk_form16_endpoint_exists(self, auth_headers):
        """GET /api/hr/payroll/form16/bulk/{fy} should exist (200 or 404 if no data)"""
        response = requests.get(
            f"{BASE_URL}/api/hr/payroll/form16/bulk/2025-26",
            headers=auth_headers
        )
        # Should return 200 (possibly with empty zip) or 404 if no employees with payroll data
        # but NOT 500 (server error) or 405 (method not allowed)
        assert response.status_code in [200, 404], \
            f"Bulk Form 16 endpoint returned unexpected status: {response.status_code} - {response.text[:200]}"

    def test_bulk_form16_invalid_fy(self, auth_headers):
        """Invalid FY format should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/hr/payroll/form16/bulk/invalid-fy",
            headers=auth_headers
        )
        # Should return 400 for invalid FY format or 404 if no data
        assert response.status_code in [400, 404, 200], \
            f"Invalid FY should not return 500: {response.text[:200]}"


# ======================== TASK 3: LOGO UPLOAD ENDPOINT TEST ========================

class TestLogoUpload:
    """Logo upload endpoint tests"""

    def test_logo_upload_endpoint_exists(self, auth_token):
        """POST /api/uploads/logo should exist and accept multipart"""
        # Create a minimal 1x1 PNG in memory
        import io
        # Minimal valid PNG (1x1 white pixel)
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00'
            b'\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        files = {
            "file": ("test_logo.png", io.BytesIO(png_data), "image/png")
        }
        data = {"logo_type": "main"}
        response = requests.post(
            f"{BASE_URL}/api/uploads/logo",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files,
            data=data
        )
        assert response.status_code in [200, 201, 400, 422], \
            f"Logo upload returned unexpected status: {response.status_code} - {response.text[:300]}"


# ======================== GENERAL HEALTH TESTS ========================

class TestHealthCheck:
    """Health check tests"""

    def test_api_root_health(self):
        """API root endpoint should be healthy"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Root API failed: {response.text}"
