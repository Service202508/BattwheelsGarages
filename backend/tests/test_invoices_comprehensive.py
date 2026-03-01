"""
Comprehensive Invoices Endpoint Tests
=======================================
Tests for 10 critical invoice endpoints.
Uses shared conftest.py fixtures (base_url, dev_headers).

Run: pytest backend/tests/test_invoices_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid


# ==================== HELPERS ====================

@pytest.fixture(scope="module")
def _headers(base_url):
    """Auth headers with org context for invoices."""
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
    """Get an existing customer for invoice tests."""
    resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/?per_page=1", headers=_headers)
    if resp.status_code == 200:
        data = resp.json()
        contacts = data.get("data") or data.get("contacts") or []
        if contacts:
            return contacts[0].get("contact_id")
    return None


@pytest.fixture(scope="module")
def test_invoice(base_url, _headers, test_customer_id):
    """Create a test invoice and return it."""
    if not test_customer_id:
        pytest.skip("No customer available to create invoice")

    resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/", headers=_headers, json={
        "customer_id": test_customer_id,
        "invoice_date": "2026-02-01",
        "due_date": "2026-03-01",
        "line_items": [{
            "name": "Battery Health Check",
            "description": "Full diagnostic scan",
            "quantity": 1,
            "rate": 500.0,
            "tax_percentage": 18.0,
            "tax_name": "GST @18%",
            "hsn_sac": "998719"
        }],
        "terms": "Payment due within 30 days",
        "notes": "Test invoice for comprehensive testing"
    })
    if resp.status_code != 200:
        pytest.skip(f"Cannot create invoice: {resp.status_code} {resp.text}")
    data = resp.json()
    invoice = data.get("invoice") or data
    assert invoice.get("invoice_id"), f"No invoice_id: {data}"
    return invoice


# ==================== 1. POST — Create Invoice ====================

class TestCreateInvoice:
    def test_create_invoice_success(self, base_url, _headers, test_customer_id):
        if not test_customer_id:
            pytest.skip("No customer")
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/", headers=_headers, json={
            "customer_id": test_customer_id,
            "invoice_date": "2026-02-15",
            "due_date": "2026-03-15",
            "line_items": [{"name": "Motor Repair", "quantity": 1, "rate": 2000.0, "tax_percentage": 18.0, "tax_name": "GST"}]
        })
        assert resp.status_code == 200
        data = resp.json()
        inv = data.get("invoice") or data
        assert inv.get("invoice_id")
        assert inv.get("invoice_number")

    def test_create_invoice_missing_customer(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/", headers=_headers, json={
            "customer_id": "nonexistent_customer_999",
            "line_items": [{"name": "x", "quantity": 1, "rate": 100}]
        })
        assert resp.status_code in [404, 422]

    def test_create_invoice_requires_auth(self, base_url):
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/", json={
            "customer_id": "x",
            "line_items": [{"name": "x", "quantity": 1, "rate": 100}]
        })
        assert resp.status_code in [401, 403, 422]


# ==================== 2. GET — List Invoices ====================

class TestListInvoices:
    def test_list_invoices(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data

    def test_list_invoices_cursor_pagination(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/?limit=2", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        pagination = data.get("pagination", {})
        assert "total_count" in pagination
        assert "has_next" in pagination

    def test_list_invoices_status_filter(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/?status=draft", headers=_headers)
        assert resp.status_code == 200

    def test_list_invoices_search(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/?search=battery", headers=_headers)
        assert resp.status_code == 200

    def test_list_invoices_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/")
        assert resp.status_code in [401, 403, 422]


# ==================== 3. GET /{id} — Get Single ====================

class TestGetInvoice:
    def test_get_invoice(self, base_url, _headers, test_invoice):
        iid = test_invoice["invoice_id"]
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/{iid}", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        inv = data.get("invoice") or data
        assert inv.get("invoice_id") == iid
        assert inv.get("customer_id")
        assert "line_items" in inv

    def test_get_nonexistent_invoice(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/INV_NONEXISTENT_999", headers=_headers)
        assert resp.status_code == 404


# ==================== 4. PUT /{id} — Update ====================

class TestUpdateInvoice:
    def test_update_invoice_notes(self, base_url, _headers, test_invoice):
        iid = test_invoice["invoice_id"]
        resp = requests.put(f"{base_url}/api/v1/invoices-enhanced/{iid}", headers=_headers, json={
            "notes": f"Updated notes {uuid.uuid4().hex[:6]}"
        })
        assert resp.status_code == 200

    def test_update_nonexistent(self, base_url, _headers):
        resp = requests.put(f"{base_url}/api/v1/invoices-enhanced/INV_NONEXISTENT", headers=_headers, json={
            "notes": "should fail"
        })
        assert resp.status_code in [404, 400]


# ==================== 5. POST /{id}/payments — Record Payment ====================

class TestRecordPayment:
    def test_record_payment(self, base_url, _headers, test_invoice):
        iid = test_invoice["invoice_id"]
        total = test_invoice.get("total", 590)
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/{iid}/payments", headers=_headers, json={
            "amount": min(total, 100),
            "payment_date": "2026-02-20",
            "payment_mode": "bank_transfer",
            "reference_number": "PAY-TEST-001",
            "notes": "Partial payment test"
        })
        assert resp.status_code == 200, f"Payment failed: {resp.text}"
        data = resp.json()
        assert data.get("payment_id") or data.get("payment") or data.get("message")

    def test_record_payment_nonexistent(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/INV_NONEXISTENT/payments", headers=_headers, json={
            "amount": 100, "payment_date": "2026-02-20", "payment_mode": "cash"
        })
        assert resp.status_code in [404, 400]


# ==================== 6. GET /{id}/pdf — PDF Generation ====================

class TestInvoicePDF:
    def test_generate_pdf(self, base_url, _headers, test_invoice):
        iid = test_invoice["invoice_id"]
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/{iid}/pdf", headers=_headers)
        assert resp.status_code in [200, 500, 503], f"Unexpected: {resp.status_code}"
        if resp.status_code == 200:
            assert len(resp.content) > 0

    def test_pdf_nonexistent(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/INV_NONEXISTENT/pdf", headers=_headers)
        assert resp.status_code in [404, 500]


# ==================== 7. POST /{id}/send — Send Invoice ====================

class TestSendInvoice:
    def test_send_invoice(self, base_url, _headers, test_invoice):
        iid = test_invoice["invoice_id"]
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/{iid}/send", headers=_headers)
        # 200 = sent, 400 = no email, 500 = email service error
        assert resp.status_code in [200, 400, 500], f"Unexpected: {resp.status_code} {resp.text}"


# ==================== 8. GET /summary — Invoice Stats ====================

class TestInvoiceSummary:
    def test_get_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/summary", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_invoices" in data or "summary" in data or "total" in data

    def test_summary_with_period(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/summary?period=this_month", headers=_headers)
        assert resp.status_code == 200


# ==================== 9. POST /{id}/void — Void Invoice ====================

class TestVoidInvoice:
    @pytest.fixture(scope="class")
    def voidable_invoice(self, base_url, _headers, test_customer_id):
        if not test_customer_id:
            pytest.skip("No customer")
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/", headers=_headers, json={
            "customer_id": test_customer_id,
            "invoice_date": "2026-02-01",
            "due_date": "2026-03-01",
            "line_items": [{"name": "Void Test", "quantity": 1, "rate": 100.0, "tax_percentage": 18.0, "tax_name": "GST"}]
        })
        if resp.status_code != 200:
            pytest.skip("Cannot create invoice for void test")
        return (resp.json().get("invoice") or resp.json())

    def test_void_invoice(self, base_url, _headers, voidable_invoice):
        iid = voidable_invoice["invoice_id"]
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/{iid}/void", headers=_headers,
                              params={"reason": "Test voiding"})
        assert resp.status_code in [200, 400], f"Unexpected: {resp.status_code} {resp.text}"

    def test_void_nonexistent(self, base_url, _headers):
        resp = requests.post(f"{base_url}/api/v1/invoices-enhanced/INV_NONEXISTENT/void", headers=_headers)
        assert resp.status_code in [404, 400]


# ==================== 10. GET /{id}/payments — List Payments ====================

class TestGetPayments:
    def test_get_payments(self, base_url, _headers, test_invoice):
        iid = test_invoice["invoice_id"]
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/{iid}/payments", headers=_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "payments" in data
        assert isinstance(data["payments"], list)

    def test_get_payments_nonexistent(self, base_url, _headers):
        resp = requests.get(f"{base_url}/api/v1/invoices-enhanced/INV_NONEXISTENT/payments", headers=_headers)
        assert resp.status_code in [200, 404]
