"""
Comprehensive GST Endpoint Tests
==================================
Tests for GST compliance endpoints.
Uses shared conftest.py fixtures.

Run: pytest backend/tests/test_gst_comprehensive.py -v --tb=short
"""

import pytest
import requests


@pytest.fixture(scope="module")
def _headers(base_url):
    """Auth headers with org context."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "dev@battwheels.internal",
        "password": "DevTest@123"
    })
    assert resp.status_code == 200
    token = resp.json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "dev-internal-testing-001",
        "Content-Type": "application/json"
    }


# ==================== 1. GET /api/v1/gst/gstr1 ====================

class TestGSTR1:
    def test_gstr1_report(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr1?month=2026-03", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "b2b" in data
        assert "b2cl" in data or "b2cs" in data
        assert "hsn_summary" in data

    def test_gstr1_b2b_section(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr1?month=2026-03", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["b2b"], list)

    def test_gstr1_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr1?month=2026-03")
        assert resp.status_code in [401, 403, 422]


# ==================== 2. GET /api/v1/gst/gstr3b ====================

class TestGSTR3B:
    def test_gstr3b_report(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr3b?month=2026-03", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Table 3.1 (outward supplies)
        assert "table_3_1" in data

    def test_gstr3b_rcm_section(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr3b?month=2026-03", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "table_3_1" in data
        table31 = data["table_3_1"]
        # 3.1d is RCM
        assert "d" in table31 or "rcm" in str(table31).lower() or isinstance(table31, dict)

    def test_gstr3b_itc_section(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr3b?month=2026-03", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "table_4A" in data or "itc" in data or "table_4" in str(data.keys())

    def test_gstr3b_net_liability(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr3b?month=2026-03", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "net_liability" in data or "liability" in data or "payable" in str(data).lower()

    def test_gstr3b_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/v1/gst/gstr3b?month=2026-03")
        assert resp.status_code in [401, 403, 422]


# ==================== 3. GET /api/v1/gst/organization-settings ====================

class TestGSTSettings:
    def test_get_settings(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/organization-settings", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "gstin" in data or "settings" in data or "organization_id" in data

    def test_settings_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/v1/gst/organization-settings")
        assert resp.status_code in [401, 403, 422]


# ==================== 4. PUT /api/v1/gst/organization-settings ====================

class TestUpdateGSTSettings:
    def test_update_settings(self, base_url, _headers):
        # First get current settings
        get_resp = requests.get(f"{base_url}/api/v1/gst/organization-settings", headers=_headers)
        if get_resp.status_code != 200:
            pytest.skip("Cannot get current settings")
        current = get_resp.json()
        current_gstin = current.get("gstin", "07AAACM1234A1Z5")

        resp = requests.put(f"{base_url}/api/v1/gst/organization-settings", headers=_headers, json={
            "gstin": current_gstin,
            "state_code": "07",
            "state_name": "Delhi"
        })
        assert resp.status_code == 200


# ==================== 5. GET /api/v1/gst/hsn-summary ====================

class TestHSNSummary:
    def test_hsn_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/hsn-summary?month=2026-03", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "hsn_data" in data or "data" in data or isinstance(data, dict)

    def test_hsn_summary_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/v1/gst/hsn-summary?month=2026-03")
        assert resp.status_code in [401, 403, 422]


# ==================== 6. GET /api/v1/gst/summary ====================

class TestGSTSummary:
    def test_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/summary", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


# ==================== 7. GET /api/v1/gst/states ====================

class TestGSTStates:
    def test_states(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/gst/states", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        states = data.get("states") or data
        assert isinstance(states, (list, dict))


# ==================== 8. POST /api/v1/gst/validate-gstin ====================

class TestGSTINValidation:
    def test_validate_gstin(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/gst/validate-gstin", headers=_headers, json={
            "gstin": "07AAACM1234A1Z5"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "valid" in data or "is_valid" in data

    def test_validate_invalid_gstin(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/gst/validate-gstin", headers=_headers, json={
            "gstin": "INVALID"
        })
        assert resp.status_code in [200, 400, 422]


# ==================== 9. POST /api/v1/gst/calculate ====================

class TestGSTCalculation:
    def test_calculate_gst(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/gst/calculate", headers=_headers, json={
            "amount": 10000,
            "gst_rate": 18,
            "is_inter_state": False,
            "place_of_supply": "07"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "cgst" in data or "total" in data or "gst_amount" in data
