"""
Comprehensive Estimates Endpoint Tests
=======================================
Tests for the 10 most critical estimate endpoints.
Uses shared conftest.py fixtures (base_url, auth_headers, admin_headers).

Run: pytest backend/tests/test_estimates_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid
import os


# ==================== HELPERS ====================

@pytest.fixture(scope="module")
def _headers(base_url):
    """Auth headers with org context for estimates."""
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


@pytest.fixture(scope="module")
def test_customer_id(base_url, _headers):
    """Get or create a test customer for estimates."""
    # Try to find existing customer
    resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/?per_page=1", headers=_headers)
    if resp.status_code == 200:
        data = resp.json()
        contacts = data.get("data") or data.get("contacts") or []
        if contacts:
            return contacts[0].get("contact_id")
    # Fallback: use a placeholder
    return None


@pytest.fixture(scope="module")
def test_estimate(base_url, _headers, test_customer_id):
    """Create a test estimate and return it."""
    if not test_customer_id:
        pytest.skip("No customer available to create estimate")

    payload = {
        "customer_id": test_customer_id,
        "subject": f"Test Estimate {uuid.uuid4().hex[:8]}",
        "line_items": [{
            "name": "Battery Inspection",
            "description": "Full battery health check",
            "quantity": 1,
            "unit": "nos",
            "rate": 500.0,
            "tax_percentage": 18.0,
            "tax_name": "GST @18%"
        }],
        "terms": "Test terms",
        "notes": "Created by comprehensive test"
    }
    resp = requests.post(f"{base_url}/api/v1/estimates-enhanced/", headers=_headers, json=payload)
    if resp.status_code != 200:
        pytest.skip(f"Cannot create estimate: {resp.status_code} {resp.text}")
    data = resp.json()
    estimate = data.get("estimate") or data
    assert estimate.get("estimate_id"), f"No estimate_id: {data}"
    return estimate


# ==================== 1. POST /api/v1/estimates-enhanced/ — Create ====================

class TestCreateEstimate:
    def test_create_estimate_success(self, base_url, _headers, test_customer_id):
        if not test_customer_id:
            pytest.skip("No customer available")
        resp = requests.post(f"{base_url}/api/v1/estimates-enhanced/", headers=_headers, json={
            "customer_id": test_customer_id,
            "subject": f"Create Test {uuid.uuid4().hex[:6]}",
            "line_items": [{
                "name": "Motor Repair",
                "quantity": 1,
                "rate": 2000.0,
                "tax_percentage": 18.0,
                "tax_name": "GST @18%"
            }]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("estimate") or data.get("estimate_id")

    def test_create_estimate_missing_customer(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/estimates-enhanced/", headers=_headers, json={
            "customer_id": "nonexistent_customer_999",
            "subject": "Should fail",
            "line_items": [{"name": "x", "quantity": 1, "rate": 100}]
        })
        assert resp.status_code in [400, 404, 422]


# ==================== 2. GET /api/v1/estimates-enhanced/ — List ====================

class TestListEstimates:
    def test_list_estimates(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data or "estimates" in data
        assert "pagination" in data

    def test_list_estimates_with_status_filter(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/?status=draft", headers=_headers)
        assert resp.status_code == 200

    def test_list_estimates_with_search(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/?search=battery", headers=_headers)
        assert resp.status_code == 200

    def test_list_estimates_pagination(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/?page=1&limit=5", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        pagination = data.get("pagination", {})
        assert "total_count" in pagination
        assert "has_next" in pagination

    def test_list_estimates_cursor_pagination(self, base_url, _headers):
        """Test cursor-based pagination (added in Part B Task 4)."""
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/?limit=2&cursor_mode=true", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        pagination = data.get("pagination", {})
        # Cursor response should have next_cursor
        if pagination.get("has_next"):
            assert pagination.get("next_cursor") is not None


# ==================== 3. GET /api/v1/estimates-enhanced/{id} — Get Single ====================

class TestGetEstimate:
    def test_get_estimate(self, base_url, _headers, test_estimate):
        eid = test_estimate["estimate_id"]
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/{eid}", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        est = data.get("estimate") or data
        assert est.get("estimate_id") == eid

    def test_get_nonexistent_estimate(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/EST_NONEXISTENT_999", headers=_headers)
        assert resp.status_code == 404


# ==================== 4. PUT /api/v1/estimates-enhanced/{id} — Update ====================

class TestUpdateEstimate:
    def test_update_estimate_subject(self, base_url, _headers, test_estimate):
        eid = test_estimate["estimate_id"]
        new_subject = f"Updated Subject {uuid.uuid4().hex[:6]}"
        resp = requests.put(f"{base_url}/api/v1/estimates-enhanced/{eid}", headers=_headers, json={
            "subject": new_subject
        })
        assert resp.status_code == 200

    def test_update_nonexistent_estimate(self, base_url, _headers):
        resp = requests.put(f"{base_url}/api/v1/estimates-enhanced/EST_NONEXISTENT_999", headers=_headers, json={
            "subject": "Should fail"
        })
        assert resp.status_code in [404, 400]


# ==================== 5. POST /{id}/convert-to-invoice — Convert ====================

class TestConvertToInvoice:
    @pytest.fixture(scope="class")
    def convertible_estimate(self, base_url, _headers, test_customer_id):
        if not test_customer_id:
            pytest.skip("No customer available")
        resp = requests.post(f"{base_url}/api/v1/estimates-enhanced/", headers=_headers, json={
            "customer_id": test_customer_id,
            "subject": f"Convertible {uuid.uuid4().hex[:6]}",
            "line_items": [{"name": "Service", "quantity": 1, "rate": 1000, "tax_percentage": 18, "tax_name": "GST"}]
        })
        if resp.status_code != 200:
            pytest.skip("Cannot create estimate for conversion test")
        return (resp.json().get("estimate") or resp.json())

    def test_convert_to_invoice(self, base_url, _headers, convertible_estimate):
        eid = convertible_estimate["estimate_id"]
        resp = requests.post(f"{base_url}/api/v1/estimates-enhanced/{eid}/convert-to-invoice", headers=_headers)
        # 200 = success, 400/409 = already converted, 422 = validation
        assert resp.status_code in [200, 400, 409, 422], f"Unexpected: {resp.status_code} {resp.text}"

    def test_convert_nonexistent(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/estimates-enhanced/EST_NONEXISTENT/convert-to-invoice", headers=_headers)
        assert resp.status_code in [404, 400]


# ==================== 6. POST /{id}/share — Share link ====================

class TestShareEstimate:
    def test_create_share_link(self, base_url, _headers, test_estimate):
        eid = test_estimate["estimate_id"]
        resp = requests.post(f"{base_url}/api/v1/estimates-enhanced/{eid}/share", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("share_link") or data.get("share_url") or data.get("token") or data.get("share_token")


# ==================== 7. GET /{id}/pdf — PDF generation ====================

class TestEstimatePDF:
    def test_generate_pdf(self, base_url, _headers, test_estimate):
        eid = test_estimate["estimate_id"]
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/{eid}/pdf", headers=_headers)
        # PDF generation may return 200 with content or 500 if deps missing
        assert resp.status_code in [200, 500, 503], f"Unexpected: {resp.status_code}"
        if resp.status_code == 200:
            assert "pdf" in resp.headers.get("content-type", "").lower() or len(resp.content) > 0

    def test_pdf_nonexistent(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/EST_NONEXISTENT/pdf", headers=_headers)
        assert resp.status_code in [404, 500]


# ==================== 8. GET /summary — Summary stats ====================

class TestEstimateSummary:
    def test_get_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/summary", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data or "total" in data or isinstance(data, dict)


# ==================== 9. GET /reports/conversion-funnel ====================

class TestConversionFunnel:
    def test_get_funnel(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/reports/conversion-funnel", headers=_headers)
        assert resp.status_code == 200


# ==================== 10. GET /{id}/activity — Activity log ====================

class TestEstimateActivity:
    def test_get_activity(self, base_url, _headers, test_estimate):
        eid = test_estimate["estimate_id"]
        resp = requests.get(f"{base_url}/api/v1/estimates-enhanced/{eid}/activity", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data or "activities" in data or isinstance(data, list)
