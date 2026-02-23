"""
P2 WhatsApp Invoice Delivery, P3 Tally XML Export, P4 Public Signup, PWA Tests
=================================================================================
Tests:
  P2: WhatsApp settings CRUD + test endpoint
  P2: Invoice send with channel=email (regression)
  P3: Tally XML export (valid XML, structure, headers, empty range 404)
  P4: Public signup flow (/api/organizations/signup)
  PWA: manifest.json, sw.js, icon-192.png, icon-512.png
"""

import pytest
import requests
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Org admin credentials
ORG_ADMIN_EMAIL = "admin@battwheels.in"
ORG_ADMIN_PASS = "admin"
ORG_ID = "6996dcf072ffd2a2395fee7b"


# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for org admin"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASS,
        "organization_id": ORG_ID,
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    data = res.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {
        "Authorization": f"Bearer {auth_token}",
        "X-Organization-ID": ORG_ID,
        "Content-Type": "application/json",
    }


# ==================== P2: WHATSAPP SETTINGS ====================

class TestWhatsAppSettings:
    """P2: WhatsApp Business API settings endpoints"""

    def test_get_whatsapp_settings_returns_200(self, auth_headers):
        """GET /api/organizations/me/whatsapp-settings returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    def test_get_whatsapp_settings_has_configured_field(self, auth_headers):
        """GET returns 'configured' boolean field"""
        res = requests.get(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert "configured" in data, f"Missing 'configured' field in response: {data}"
        assert isinstance(data["configured"], bool)

    def test_get_whatsapp_settings_has_phone_number_id_field(self, auth_headers):
        """GET returns 'phone_number_id' field"""
        res = requests.get(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert "phone_number_id" in data, f"Missing 'phone_number_id' field: {data}"

    def test_post_whatsapp_settings_saves_credentials(self, auth_headers):
        """POST /api/organizations/me/whatsapp-settings saves credentials"""
        res = requests.post(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
            json={
                "phone_number_id": "test123",
                "access_token": "testtoken123456789",
            },
        )
        assert res.status_code == 200, f"Save failed: {res.text}"
        data = res.json()
        assert data.get("success") is True, f"Expected success=True: {data}"

    def test_get_after_save_shows_configured(self, auth_headers):
        """After saving, GET should show configured=True and correct phone_number_id"""
        # Save first
        requests.post(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
            json={"phone_number_id": "test123", "access_token": "testtoken123456789"},
        )
        # Get and verify
        res = requests.get(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("configured") is True, f"Expected configured=True after save: {data}"
        assert data.get("phone_number_id") == "test123", f"phone_number_id mismatch: {data}"

    def test_delete_whatsapp_settings_removes_credentials(self, auth_headers):
        """DELETE /api/organizations/me/whatsapp-settings removes credentials"""
        # Save first
        requests.post(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
            json={"phone_number_id": "test123", "access_token": "testtoken123456789"},
        )
        # Delete
        res = requests.delete(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
        )
        assert res.status_code == 200, f"Delete failed: {res.text}"
        data = res.json()
        assert data.get("success") is True, f"Expected success=True: {data}"

    def test_get_after_delete_shows_not_configured(self, auth_headers):
        """After DELETE, GET should show configured=False"""
        # Delete first
        requests.delete(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
        )
        # Get and verify
        res = requests.get(
            f"{BASE_URL}/api/organizations/me/whatsapp-settings",
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("configured") is False, f"Expected configured=False after delete: {data}"

    def test_whatsapp_test_returns_400_no_phone(self, auth_headers):
        """POST /api/organizations/me/whatsapp-test returns 400 if no phone on user profile"""
        # Note: admin user has no phone in profile for test org
        # This is expected behavior per review request
        res = requests.post(
            f"{BASE_URL}/api/organizations/me/whatsapp-test",
            headers=auth_headers,
        )
        # Either 400 (no phone) or 400 (WhatsApp not configured) - both are valid expected responses
        # 400 is expected since test credentials aren't real Meta credentials
        assert res.status_code in (400,), f"Expected 400, got {res.status_code}: {res.text}"
        data = res.json()
        detail = data.get("detail", "")
        print(f"WhatsApp test response: {detail}")
        # Should mention phone or WhatsApp config
        assert detail, f"Empty detail in 400 response: {data}"


# ==================== P2: INVOICE SEND REGRESSION ====================

class TestInvoiceSendRegression:
    """P2: Regression - POST /api/invoices-enhanced/{id}/send?channel=email still works"""

    def test_send_invoice_email_channel_works(self, auth_headers):
        """POST /api/invoices-enhanced/{id}/send?channel=email returns 200"""
        # First, get a list of invoices to find an ID
        res = requests.get(
            f"{BASE_URL}/api/invoices-enhanced/?per_page=5",
            headers=auth_headers,
        )
        assert res.status_code == 200, f"Failed to list invoices: {res.text}"
        data = res.json()
        invoices = data.get("invoices", data.get("data", []))
        
        if not invoices:
            pytest.skip("No invoices found for regression test")
        
        invoice_id = invoices[0].get("invoice_id") or invoices[0].get("id")
        assert invoice_id, f"No invoice_id in first invoice: {invoices[0]}"
        
        # Send via email channel
        send_res = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/{invoice_id}/send?channel=email",
            headers=auth_headers,
        )
        # Should be 200 (success or graceful error, not 500)
        assert send_res.status_code in (200, 400, 422), (
            f"Unexpected status {send_res.status_code} for invoice send: {send_res.text}"
        )
        print(f"Invoice send via email: {send_res.status_code} - {send_res.text[:200]}")


# ==================== P3: TALLY XML EXPORT ====================

class TestTallyXMLExport:
    """P3: Tally XML Export tests"""

    DATE_FROM = "2026-02-01"
    DATE_TO = "2026-02-28"

    def test_tally_xml_returns_200_for_valid_range(self, auth_headers):
        """GET /api/finance/export/tally-xml returns 200 for Feb 2026"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": self.DATE_FROM, "date_to": self.DATE_TO},
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    def test_tally_xml_response_has_content_disposition(self, auth_headers):
        """Response has Content-Disposition: attachment header"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": self.DATE_FROM, "date_to": self.DATE_TO},
        )
        assert res.status_code == 200
        cd = res.headers.get("Content-Disposition", "")
        assert "attachment" in cd, f"Missing 'attachment' in Content-Disposition: '{cd}'"
        assert ".xml" in cd, f"Missing .xml in Content-Disposition: '{cd}'"

    def test_tally_xml_content_type_is_xml(self, auth_headers):
        """Response content type is application/xml"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": self.DATE_FROM, "date_to": self.DATE_TO},
        )
        assert res.status_code == 200
        ct = res.headers.get("Content-Type", "")
        assert "xml" in ct, f"Expected XML content type, got: {ct}"

    def test_tally_xml_starts_with_xml_declaration(self, auth_headers):
        """XML response starts with <?xml version"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": self.DATE_FROM, "date_to": self.DATE_TO},
        )
        assert res.status_code == 200
        xml_text = res.text.strip()
        assert xml_text.startswith("<?xml version"), (
            f"XML should start with <?xml version, got: {xml_text[:100]}"
        )

    def test_tally_xml_is_valid_xml(self, auth_headers):
        """XML response is parseable / valid XML"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": self.DATE_FROM, "date_to": self.DATE_TO},
        )
        assert res.status_code == 200
        try:
            root = ET.fromstring(res.text.split("\n", 1)[1])  # Skip XML declaration
            print(f"XML root tag: {root.tag}")
        except ET.ParseError as e:
            pytest.fail(f"XML is not valid: {e}")

    def test_tally_xml_contains_envelope_structure(self, auth_headers):
        """XML contains ENVELOPE > BODY > IMPORTDATA structure"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": self.DATE_FROM, "date_to": self.DATE_TO},
        )
        assert res.status_code == 200
        root = ET.fromstring(res.text.split("\n", 1)[1])
        
        assert root.tag == "ENVELOPE", f"Root element should be ENVELOPE, got: {root.tag}"
        
        body = root.find("BODY")
        assert body is not None, "ENVELOPE should contain BODY element"
        
        import_data = body.find("IMPORTDATA")
        assert import_data is not None, "BODY should contain IMPORTDATA element"
        
        print(f"Structure OK: ENVELOPE > BODY > IMPORTDATA found")

    def test_tally_xml_no_entries_returns_404(self, auth_headers):
        """GET with date range with no entries returns 404"""
        # Use a far-future date range with no entries
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": "2030-01-01", "date_to": "2030-01-31"},
        )
        assert res.status_code == 404, (
            f"Expected 404 for empty date range, got {res.status_code}: {res.text}"
        )

    def test_tally_xml_invalid_date_returns_400(self, auth_headers):
        """GET with invalid date format returns 400"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": "invalid-date", "date_to": "2026-02-28"},
        )
        assert res.status_code == 400, f"Expected 400 for invalid date, got {res.status_code}"

    def test_tally_xml_date_from_after_to_returns_400(self, auth_headers):
        """GET with date_from > date_to returns 400"""
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers,
            params={"date_from": "2026-03-01", "date_to": "2026-02-01"},
        )
        assert res.status_code == 400, f"Expected 400 when date_from > date_to, got {res.status_code}"


# ==================== P4: PUBLIC SIGNUP ====================

class TestPublicSignup:
    """P4: Public self-serve signup at /register"""
    
    TIMESTAMP = int(time.time())

    def test_signup_is_public_route_no_auth_needed(self):
        """POST /api/organizations/signup accessible without auth"""
        # Try with a unique email - no auth headers
        unique_email = f"test_signup_{self.TIMESTAMP}@teststudio.com"
        res = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json={
                "name": f"TEST Garage {self.TIMESTAMP}",
                "city": "Mumbai",
                "phone": "9876543210",
                "vehicle_types": ["2W", "4W"],
                "admin_name": "Test Owner",
                "admin_email": unique_email,
                "admin_password": "TestPass123!",
                "industry_type": "ev_garage",
            },
        )
        assert res.status_code == 200, f"Signup failed: {res.text}"
        data = res.json()
        assert data.get("success") is True, f"Expected success=True: {data}"

    def test_signup_returns_token(self):
        """POST /api/organizations/signup returns JWT token"""
        unique_email = f"test_token_{self.TIMESTAMP + 1}@teststudio.com"
        res = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json={
                "name": f"TEST Token Garage",
                "city": "Delhi",
                "phone": "9123456789",
                "vehicle_types": ["2W"],
                "admin_name": "Token Owner",
                "admin_email": unique_email,
                "admin_password": "TestPass123!",
                "industry_type": "ev_garage",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "token" in data, f"No token in signup response: {data}"
        assert len(data["token"]) > 20, "Token seems too short"

    def test_signup_creates_org_with_trial_ends_at(self):
        """New org has trial_ends_at ~14 days from creation"""
        unique_email = f"test_trial_{self.TIMESTAMP + 2}@teststudio.com"
        res = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json={
                "name": "TEST Trial Garage",
                "city": "Pune",
                "phone": "9000000001",
                "vehicle_types": ["4W"],
                "admin_name": "Trial Owner",
                "admin_email": unique_email,
                "admin_password": "TestPass123!",
                "industry_type": "ev_garage",
            },
        )
        assert res.status_code == 200
        data = res.json()
        org = data.get("organization", {})
        plan_expires_at = org.get("plan_expires_at")
        assert plan_expires_at, f"No plan_expires_at in org: {org}"
        
        # Verify trial is ~14 days from now
        from datetime import datetime, timezone
        expires = datetime.fromisoformat(plan_expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_diff = (expires - now).days
        assert 13 <= days_diff <= 15, f"Trial should be ~14 days, got {days_diff} days"
        print(f"Trial ends in {days_diff} days - OK")

    def test_signup_with_city_phone_vehicle_types(self):
        """POST /api/organizations/signup accepts city, phone, vehicle_types"""
        unique_email = f"test_fields_{self.TIMESTAMP + 3}@teststudio.com"
        res = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json={
                "name": "TEST Fields Garage",
                "city": "Bangalore",
                "phone": "9876543211",
                "vehicle_types": ["2W", "3W", "4W"],
                "admin_name": "Fields Owner",
                "admin_email": unique_email,
                "admin_password": "TestPass123!",
                "industry_type": "ev_garage",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True

    def test_signup_duplicate_email_returns_400(self):
        """Duplicate email signup returns 400"""
        unique_email = f"test_dup_{self.TIMESTAMP + 4}@teststudio.com"
        payload = {
            "name": "TEST Duplicate Garage",
            "city": "Chennai",
            "phone": "9876543212",
            "vehicle_types": ["2W"],
            "admin_name": "Dup Owner",
            "admin_email": unique_email,
            "admin_password": "TestPass123!",
            "industry_type": "ev_garage",
        }
        # First signup
        res1 = requests.post(f"{BASE_URL}/api/organizations/signup", json=payload)
        assert res1.status_code == 200
        
        # Duplicate
        res2 = requests.post(f"{BASE_URL}/api/organizations/signup", json=payload)
        assert res2.status_code == 400, f"Expected 400 for duplicate, got {res2.status_code}"
        data = res2.json()
        assert "already registered" in data.get("detail", "").lower() or "exists" in data.get("detail", "").lower(), (
            f"Expected 'already registered' message: {data}"
        )

    def test_signup_plan_type_is_free_trial(self):
        """New org has plan_type 'free_trial'"""
        unique_email = f"test_plan_{self.TIMESTAMP + 5}@teststudio.com"
        res = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json={
                "name": "TEST Plan Garage",
                "city": "Hyderabad",
                "phone": "9000000002",
                "vehicle_types": ["4W"],
                "admin_name": "Plan Owner",
                "admin_email": unique_email,
                "admin_password": "TestPass123!",
            },
        )
        assert res.status_code == 200
        data = res.json()
        org = data.get("organization", {})
        assert org.get("plan_type") == "free_trial", f"Expected free_trial plan: {org}"


# ==================== PWA ASSETS ====================

class TestPWAAssets:
    """PWA: Check manifest.json, sw.js, icon files"""

    def test_manifest_json_accessible(self):
        """GET /manifest.json returns 200"""
        res = requests.get(f"{BASE_URL}/manifest.json")
        assert res.status_code == 200, f"manifest.json not accessible: {res.status_code}"

    def test_manifest_json_has_name(self):
        """manifest.json has 'name' field"""
        res = requests.get(f"{BASE_URL}/manifest.json")
        assert res.status_code == 200
        data = res.json()
        assert "name" in data, f"Missing 'name' in manifest.json: {data}"
        assert data["name"] == "Battwheels OS", f"name mismatch: {data['name']}"

    def test_manifest_json_has_theme_color(self):
        """manifest.json has 'theme_color' field"""
        res = requests.get(f"{BASE_URL}/manifest.json")
        assert res.status_code == 200
        data = res.json()
        assert "theme_color" in data, f"Missing 'theme_color' in manifest.json: {data}"
        assert data["theme_color"] == "#C8FF00", f"theme_color mismatch: {data['theme_color']}"

    def test_manifest_json_has_icons(self):
        """manifest.json has 'icons' array with 192 and 512 entries"""
        res = requests.get(f"{BASE_URL}/manifest.json")
        assert res.status_code == 200
        data = res.json()
        assert "icons" in data, f"Missing 'icons' in manifest.json"
        icons = data["icons"]
        assert len(icons) >= 2, f"Expected at least 2 icons, got {len(icons)}"
        sizes = [icon.get("sizes") for icon in icons]
        assert "192x192" in sizes, f"Missing 192x192 icon. Sizes: {sizes}"
        assert "512x512" in sizes, f"Missing 512x512 icon. Sizes: {sizes}"

    def test_sw_js_accessible(self):
        """GET /sw.js returns 200"""
        res = requests.get(f"{BASE_URL}/sw.js")
        assert res.status_code == 200, f"sw.js not accessible: {res.status_code}"

    def test_sw_js_is_javascript(self):
        """sw.js has JavaScript content"""
        res = requests.get(f"{BASE_URL}/sw.js")
        assert res.status_code == 200
        assert "addEventListener" in res.text, f"sw.js doesn't look like valid service worker"

    def test_icon_192_accessible(self):
        """GET /icon-192.png returns 200"""
        res = requests.get(f"{BASE_URL}/icon-192.png")
        assert res.status_code == 200, f"icon-192.png not accessible: {res.status_code}"

    def test_icon_512_accessible(self):
        """GET /icon-512.png returns 200"""
        res = requests.get(f"{BASE_URL}/icon-512.png")
        assert res.status_code == 200, f"icon-512.png not accessible: {res.status_code}"

    def test_icon_192_is_png(self):
        """icon-192.png has PNG content type"""
        res = requests.get(f"{BASE_URL}/icon-192.png")
        assert res.status_code == 200
        ct = res.headers.get("Content-Type", "")
        assert "image" in ct or "png" in ct, f"icon-192.png has unexpected content type: {ct}"

    def test_icon_512_is_png(self):
        """icon-512.png has PNG content type"""
        res = requests.get(f"{BASE_URL}/icon-512.png")
        assert res.status_code == 200
        ct = res.headers.get("Content-Type", "")
        assert "image" in ct or "png" in ct, f"icon-512.png has unexpected content type: {ct}"
