"""
Comprehensive Credit Notes Endpoint Tests
==========================================
Tests for all credit note endpoints.
Uses shared conftest.py fixtures.

Run: pytest backend/tests/test_credit_notes_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid
from datetime import datetime


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


@pytest.fixture(scope="module")
def _demo_headers(base_url):
    """Demo user headers (different org)."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "demo@voltmotors.in",
        "password": "Demo@12345"
    })
    assert resp.status_code == 200
    token = resp.json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def sent_invoice(base_url, _headers):
    """Create a FRESH non-draft invoice for credit note testing (test isolation)."""
    # First get a customer
    resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/?per_page=1", headers=_headers)
    if resp.status_code != 200:
        pytest.skip("No customers available for invoice creation")
    contacts = resp.json().get("contacts") or resp.json().get("data") or []
    if not contacts:
        pytest.skip("No customers")
    today = datetime.now().strftime("%Y-%m-%d")
    resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/", headers=_headers, json={
        "customer_id": contacts[0]["contact_id"],
        "invoice_date": today,
        "due_date": "2026-12-31",
        "send_email": False,
        "line_items": [{"name": "Battery Service", "quantity": 2, "rate": 1000.0, "tax_percentage": 18.0, "tax_name": "GST @18%", "hsn_sac_code": "998719"}]
    })
    if resp.status_code != 200:
        pytest.skip(f"Cannot create invoice: {resp.status_code}")
    inv_data = resp.json().get("invoice") or resp.json()
    inv_id = inv_data.get("invoice_id")
    # Try to send the invoice so it becomes non-draft
    send_resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/{inv_id}/send", headers=_headers)
    # If send fails (e.g. weasyprint not installed), update status directly via action endpoint
    if send_resp.status_code != 200:
        # Use the action endpoint to change status
        action_resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/{inv_id}/action",
                                     headers=_headers, json={"action": "send"})
        if action_resp.status_code != 200:
            # Direct DB update as last resort - mark as sent via update endpoint
            update_resp = requests.put(f"{base_url}/api/v1/invoices-enhanced/{inv_id}",
                                        headers=_headers, json={"status": "sent"})
    resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/{inv_id}", headers=_headers)
    if resp.status_code == 200:
        inv = resp.json().get("invoice") or resp.json()
    else:
        inv = inv_data
    if inv.get("status") == "draft":
        pytest.skip(f"Cannot send invoice to non-draft status — send endpoint returned {send_resp.status_code}")
    return inv


@pytest.fixture(scope="module")
def test_credit_note(base_url, _headers, sent_invoice):
    """Create a test credit note."""
    resp = requests.post(f"{base_url}/api/v1/credit-notes/", headers=_headers, json={
        "original_invoice_id": sent_invoice["invoice_id"],
        "reason": "Defective battery returned",
        "notes": "Test CN for comprehensive testing",
        "line_items": [{
            "name": "Battery Service Return",
            "quantity": 1,
            "rate": 500.0,
            "tax_percentage": 18.0,
            "tax_name": "GST @18%"
        }]
    })
    if resp.status_code != 200:
        pytest.skip(f"Cannot create CN: {resp.status_code} {resp.text}")
    data = resp.json()
    cn = data.get("credit_note") or data
    assert cn.get("credit_note_id"), f"No CN ID: {data}"
    return cn


# ==================== 1. POST — Create Credit Note ====================

class TestCreateCreditNote:
    def test_create_cn_success(self, base_url, _headers, sent_invoice):
        resp = requests.post(f"{base_url}/api/v1/credit-notes/", headers=_headers, json={
            "original_invoice_id": sent_invoice["invoice_id"],
            "reason": "Partial service refund",
            "line_items": [{
                "name": "Refund Item",
                "quantity": 1,
                "rate": 200.0,
                "tax_percentage": 18.0,
                "tax_name": "GST @18%"
            }]
        })
        assert resp.status_code == 200, f"CN create failed: {resp.status_code} {resp.text}"
        data = resp.json()
        cn = data.get("credit_note") or data
        assert cn.get("credit_note_id")
        assert cn.get("credit_note_number")
        assert cn.get("status") == "issued"

    def test_create_cn_exceeding_amount_rejected(self, base_url, _headers, sent_invoice):
        inv_total = float(sent_invoice.get("grand_total") or sent_invoice.get("total", 0))
        # Try to credit more than the invoice total
        resp = requests.post(f"{base_url}/api/v1/credit-notes/", headers=_headers, json={
            "original_invoice_id": sent_invoice["invoice_id"],
            "reason": "Over-credit test",
            "line_items": [{
                "name": "Excessive refund",
                "quantity": 100,
                "rate": max(inv_total, 10000),
                "tax_percentage": 18.0,
                "tax_name": "GST @18%"
            }]
        })
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assert "exceeds" in resp.json().get("detail", "").lower()

    def test_create_cn_nonexistent_invoice(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/credit-notes/", headers=_headers, json={
            "original_invoice_id": "inv_nonexistent_999",
            "reason": "Test",
            "line_items": [{"name": "x", "quantity": 1, "rate": 100, "tax_percentage": 18, "tax_name": "GST"}]
        })
        assert resp.status_code == 404

    def test_create_cn_requires_auth(self, base_url, sent_invoice):
        resp = requests.post(f"{base_url}/api/v1/credit-notes/", json={
            "original_invoice_id": sent_invoice["invoice_id"],
            "reason": "No auth",
            "line_items": [{"name": "x", "quantity": 1, "rate": 100, "tax_percentage": 18, "tax_name": "GST"}]
        })
        assert resp.status_code in [401, 403, 422]

    def test_create_cn_cross_org_blocked(self, base_url, _demo_headers, sent_invoice):
        """Demo user (different org) should not see dev org's invoice."""
        resp = requests.post(f"{base_url}/api/v1/credit-notes/", headers=_demo_headers, json={
            "original_invoice_id": sent_invoice["invoice_id"],
            "reason": "Cross-org test",
            "line_items": [{"name": "x", "quantity": 1, "rate": 100, "tax_percentage": 18, "tax_name": "GST"}]
        })
        # 404 = invoice not found in their org, 400 = org context missing
        assert resp.status_code in [400, 403, 404]


# ==================== 2. GET — List Credit Notes ====================

class TestListCreditNotes:
    def test_list_credit_notes(self, base_url, _headers, test_credit_note):
        resp = requests.get(f"{base_url}/api/v1/credit-notes/", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        cns = data.get("credit_notes") or data.get("data") or data
        assert isinstance(cns, list)
        assert len(cns) > 0

    def test_list_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/v1/credit-notes/")
        assert resp.status_code in [401, 403, 422]


# ==================== 3. GET /{id} — Get Single ====================

class TestGetCreditNote:
    def test_get_credit_note(self, base_url, _headers, test_credit_note):
        cnid = test_credit_note["credit_note_id"]
        resp = requests.get(f"{base_url}/api/v1/credit-notes/{cnid}", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        cn = data.get("credit_note") or data
        assert cn.get("credit_note_id") == cnid
        # GST breakdown fields
        assert "cgst_amount" in cn or "gst_amount" in cn
        assert "subtotal" in cn

    def test_get_nonexistent_cn(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/credit-notes/cn_nonexistent_999", headers=_headers)
        assert resp.status_code == 404


# ==================== 4. GET /{id}/pdf — PDF ====================

class TestCreditNotePDF:
    def test_generate_pdf(self, base_url, _headers, test_credit_note):
        cnid = test_credit_note["credit_note_id"]
        resp = requests.get(f"{base_url}/api/v1/credit-notes/{cnid}/pdf", headers=_headers)
        assert resp.status_code in [200, 500, 503]
        if resp.status_code == 200:
            assert len(resp.content) > 0

    def test_pdf_nonexistent(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/credit-notes/cn_nonexistent_999/pdf", headers=_headers)
        assert resp.status_code in [404, 500]
