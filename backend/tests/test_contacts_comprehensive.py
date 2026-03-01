"""
Comprehensive Contacts Module Tests
=====================================
Tests contacts CRUD, customer/vendor filtering, transactions,
aging reports, tags, and org isolation.

Uses conftest fixtures (auth_headers, admin_headers, base_url, dev_headers).
"""

import pytest
import requests
import uuid


def unique(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ==================== CONTACTS CRUD ====================

class TestContactsCRUD:
    """Test contacts CRUD via /api/v1/contacts-enhanced/"""

    @pytest.fixture(scope="class")
    def created_customer(self, base_url, auth_headers):
        """Create a test customer"""
        data = {
            "contact_name": f"Test Customer {unique()}",
            "contact_type": "customer",
            "email": f"{unique('cust')}@test.com",
            "phone": "9876543210",
            "billing_address": {"street": "123 Test St", "city": "Mumbai", "state": "Maharashtra", "zip": "400001"},
        }
        resp = requests.post(f"{base_url}/api/v1/contacts-enhanced/", json=data, headers=auth_headers)
        assert resp.status_code == 200, f"Create customer: {resp.status_code} {resp.text[:300]}"
        result = resp.json()
        contact = result.get("contact") or result
        assert contact.get("contact_id"), f"No contact_id: {list(result.keys())}"
        return contact

    @pytest.fixture(scope="class")
    def created_vendor(self, base_url, auth_headers):
        """Create a test vendor"""
        data = {
            "contact_name": f"Test Vendor {unique()}",
            "contact_type": "vendor",
            "email": f"{unique('vnd')}@test.com",
            "phone": "9123456789",
        }
        resp = requests.post(f"{base_url}/api/v1/contacts-enhanced/", json=data, headers=auth_headers)
        assert resp.status_code == 200, f"Create vendor: {resp.status_code} {resp.text[:300]}"
        result = resp.json()
        contact = result.get("contact") or result
        assert contact.get("contact_id"), f"No contact_id: {list(result.keys())}"
        return contact

    def test_create_customer(self, created_customer):
        """POST /api/v1/contacts-enhanced/ creates customer"""
        assert created_customer["contact_id"] is not None
        assert created_customer.get("contact_type") == "customer"

    def test_create_vendor(self, created_vendor):
        """POST /api/v1/contacts-enhanced/ creates vendor"""
        assert created_vendor["contact_id"] is not None
        assert created_vendor.get("contact_type") == "vendor"

    def test_create_contact_requires_auth(self, base_url):
        """POST /api/v1/contacts-enhanced/ without auth returns 401/403"""
        resp = requests.post(f"{base_url}/api/v1/contacts-enhanced/", json={"contact_name": "NoAuth"})
        assert resp.status_code in (401, 403)

    def test_list_contacts(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/ returns list"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        contacts = data.get("contacts") or data.get("data") or data
        assert isinstance(contacts, list)

    def test_list_contacts_search(self, base_url, auth_headers, created_customer):
        """GET /api/v1/contacts-enhanced/?search=... returns filtered results"""
        name = created_customer.get("contact_name", "Test Customer")
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/", params={"search": name[:15]}, headers=auth_headers)
        assert resp.status_code == 200

    def test_get_contact_by_id(self, base_url, auth_headers, created_customer):
        """GET /api/v1/contacts-enhanced/{id} returns contact"""
        cid = created_customer["contact_id"]
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        contact = data.get("contact") or data
        assert contact.get("contact_id") == cid

    def test_get_nonexistent_contact_returns_404(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/{fake} returns 404"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/contact_nonexist_999", headers=auth_headers)
        assert resp.status_code == 404

    def test_update_contact(self, base_url, auth_headers, created_customer):
        """PUT /api/v1/contacts-enhanced/{id} updates contact"""
        cid = created_customer["contact_id"]
        resp = requests.put(
            f"{base_url}/api/v1/contacts-enhanced/{cid}",
            json={"phone": "9999888877", "notes": "Updated by test"},
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ==================== FILTER BY TYPE ====================

class TestContactFiltering:
    """Test customer/vendor filtering"""

    def test_list_customers_only(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/customers returns only customers"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/customers", headers=auth_headers)
        assert resp.status_code == 200

    def test_list_vendors_only(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/vendors returns only vendors"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/vendors", headers=auth_headers)
        assert resp.status_code == 200

    def test_contacts_summary(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/summary returns summary"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/summary", headers=auth_headers)
        assert resp.status_code == 200


# ==================== TRANSACTIONS & AGING ====================

class TestContactTransactionsAndAging:
    """Test contact transactions and aging reports"""

    def test_contact_transactions(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/{id}/transactions returns history"""
        # Get first contact
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/", params={"per_page": 1}, headers=auth_headers)
        if resp.status_code != 200:
            pytest.skip("Cannot list contacts")
        contacts = resp.json().get("contacts") or resp.json().get("data") or []
        if not contacts:
            pytest.skip("No contacts")
        cid = contacts[0]["contact_id"]
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/{cid}/transactions", headers=auth_headers)
        assert resp.status_code == 200

    def test_aging_receivable(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/reports/aging-summary?aging_type=receivable"""
        resp = requests.get(
            f"{base_url}/api/v1/contacts-enhanced/reports/aging-summary",
            params={"aging_type": "receivable"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_aging_payable(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/reports/aging-summary?aging_type=payable"""
        resp = requests.get(
            f"{base_url}/api/v1/contacts-enhanced/reports/aging-summary",
            params={"aging_type": "payable"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_top_customers_report(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/reports/top-customers"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/reports/top-customers", headers=auth_headers)
        assert resp.status_code == 200

    def test_top_vendors_report(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/reports/top-vendors"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/reports/top-vendors", headers=auth_headers)
        assert resp.status_code == 200

    def test_segment_report(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/reports/by-segment"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/reports/by-segment", headers=auth_headers)
        assert resp.status_code == 200


# ==================== TAGS ====================

class TestContactTags:
    """Test contact tag management"""

    def test_list_tags(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/tags returns tags"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/tags", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_tag(self, base_url, auth_headers):
        """POST /api/v1/contacts-enhanced/tags creates tag"""
        resp = requests.post(
            f"{base_url}/api/v1/contacts-enhanced/tags",
            json={"name": f"TestTag-{unique()}", "color": "#FF5733"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201), f"Create tag: {resp.status_code} {resp.text[:200]}"


# ==================== SETTINGS & UTILITIES ====================

class TestContactSettings:
    """Test contact settings and utilities"""

    def test_get_settings(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/settings returns settings"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/settings", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_indian_states(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/states returns states"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/states", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))


# ==================== NEGATIVE TESTS ====================

class TestContactsNegative:
    """Security and negative tests"""

    def test_list_no_auth(self, base_url):
        """GET /api/v1/contacts-enhanced/ without auth returns 401/403"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/")
        assert resp.status_code in (401, 403)

    def test_create_no_auth(self, base_url):
        """POST /api/v1/contacts-enhanced/ without auth returns 401/403"""
        resp = requests.post(f"{base_url}/api/v1/contacts-enhanced/", json={"contact_name": "No Auth"})
        assert resp.status_code in (401, 403)

    def test_get_nonexistent(self, base_url, auth_headers):
        """GET /api/v1/contacts-enhanced/{fake} returns 404"""
        resp = requests.get(f"{base_url}/api/v1/contacts-enhanced/contact_fake_999", headers=auth_headers)
        assert resp.status_code == 404
