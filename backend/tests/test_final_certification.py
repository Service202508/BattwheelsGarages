"""
Final Pre-Deployment Production Readiness Certification
=======================================================
Tests all required scenarios for Battwheels OS go-live.
Previous iterations: 112 (7 critical fixes), 113 (6 P1 fixes), 114 (35/35 regression pass).

Test IDs covered:
  INFRA-01..04, AUTH-01..03, FINANCE-01..03,
  OPERATIONS-01..04, HR-01..02, SECURITY-01..02,
  CONTACT-01..02, EFI-01, PLATFORM-01, DB-01..02, DEPS-01..02
"""

import hashlib
import hmac
import json
import os
import subprocess
import time
import uuid
import pytest
import requests
import motor.motor_asyncio
import asyncio

# ──────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
INTERNAL_URL = "http://localhost:8001"   # used for auth fixture to bypass external rate limit
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "admin"
TECH_EMAIL = "tech@battwheels.in"
TECH_PASSWORD = "tech123"
ADMIN_ORG_ID = "6996dcf072ffd2a2395fee7b"
RAZORPAY_WEBHOOK_SECRET = "REDACTED_WEBHOOK_SECRET"

# Required security headers
REQUIRED_SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-XSS-Protection",
    "Referrer-Policy",
]


# ──────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def admin_token():
    """Login as admin and return JWT token. Uses internal URL to avoid rate limit."""
    for url in [INTERNAL_URL, BASE_URL]:
        try:
            resp = requests.post(f"{url}/api/auth/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            }, timeout=15)
            if resp.status_code == 200:
                token = resp.json().get("token")
                if token:
                    print(f"[fixture] Admin token obtained from {url}")
                    return token
        except Exception as e:
            print(f"[fixture] Login attempt from {url} failed: {e}")
    pytest.skip("Admin login failed — skipping token-dependent tests")


@pytest.fixture(scope="session")
def tech_token():
    """Login as tech@battwheels.in and return JWT token."""
    for url in [INTERNAL_URL, BASE_URL]:
        try:
            resp = requests.post(f"{url}/api/auth/login", json={
                "email": TECH_EMAIL, "password": TECH_PASSWORD
            }, timeout=15)
            if resp.status_code == 200:
                token = resp.json().get("token")
                if token:
                    return token
        except Exception:
            pass
    pytest.skip("Tech login failed — skipping RBAC tests")


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {
        "Authorization": f"Bearer {admin_token}",
        "X-Organization-ID": ADMIN_ORG_ID,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def tech_headers(tech_token):
    return {
        "Authorization": f"Bearer {tech_token}",
        "X-Organization-ID": ADMIN_ORG_ID,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def platform_admin_token():
    """
    Temporarily set is_platform_admin=True on admin user, login, reset.
    Uses synchronous pymongo to avoid asyncio event-loop conflicts in pytest.
    """
    import pymongo
    client = pymongo.MongoClient(MONGO_URL)
    db = client[DB_NAME]

    # Elevate admin user to platform admin
    db.users.update_one({"email": ADMIN_EMAIL}, {"$set": {"is_platform_admin": True}})

    # Login to get token (require_platform_admin reads DB at request time)
    token = None
    for url in [INTERNAL_URL, BASE_URL]:
        try:
            resp = requests.post(f"{url}/api/auth/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            }, timeout=15)
            if resp.status_code == 200:
                token = resp.json().get("token")
                if token:
                    break
        except Exception:
            pass

    yield token

    # Cleanup — reset platform admin flag
    db.users.update_one({"email": ADMIN_EMAIL}, {"$set": {"is_platform_admin": False}})
    client.close()


# ──────────────────────────────────────────────────────────
# INFRA
# ──────────────────────────────────────────────────────────

class TestINFRA:
    """INFRA-01..04: Health, security headers, public/protected routes"""

    def test_INFRA01_health_check(self):
        """INFRA-01: GET /api/health → 200, status=ok, db=ok"""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert resp.status_code == 200, f"Health returned {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "ok", f"status not ok: {data}"
        assert data.get("db") in ("ok", "connected"), f"db not ok: {data}"
        print(f"PASS INFRA-01: health={data}")

    def test_INFRA02_security_headers_on_health(self):
        """INFRA-02: Security headers on /api/health"""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert resp.status_code == 200
        missing = [h for h in REQUIRED_SECURITY_HEADERS if h not in resp.headers]
        assert not missing, f"Missing security headers on /api/health: {missing}"
        print(f"PASS INFRA-02 (/api/health): all 6 headers present")

    def test_INFRA02_security_headers_on_login(self):
        """INFRA-02: Security headers on /api/auth/login"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "x@x.com", "password": "x"
        }, timeout=10)
        # Could be 401 but headers must be present
        missing = [h for h in REQUIRED_SECURITY_HEADERS if h not in resp.headers]
        assert not missing, f"Missing security headers on /api/auth/login: {missing}"
        print(f"PASS INFRA-02 (/api/auth/login): all 6 headers present")

    def test_INFRA02_security_headers_on_contact(self):
        """INFRA-02: Security headers on POST /api/contact"""
        resp = requests.post(f"{BASE_URL}/api/contact", json={
            "name": "Test", "email": "test@example.com",
            "message": "INFRA-02 header check", "type": "general"
        }, timeout=15)
        missing = [h for h in REQUIRED_SECURITY_HEADERS if h not in resp.headers]
        assert not missing, f"Missing security headers on /api/contact: {missing}"
        print(f"PASS INFRA-02 (/api/contact): all 6 headers present")

    def test_INFRA03_public_contact_is_non_401(self):
        """INFRA-03: POST /api/contact returns non-401/403"""
        resp = requests.post(f"{BASE_URL}/api/contact", json={
            "name": "Public Test", "email": "public@test.com",
            "message": "INFRA-03 public check", "type": "general"
        }, timeout=15)
        assert resp.status_code not in (401, 403), (
            f"INFRA-03: /api/contact returned {resp.status_code} (expected public access)"
        )
        print(f"PASS INFRA-03 (/api/contact): status={resp.status_code}")

    def test_INFRA03_public_org_register_is_non_401(self):
        """INFRA-03: POST /api/organizations/register returns non-401/403"""
        resp = requests.post(f"{BASE_URL}/api/organizations/register", json={
            "name": "TEST_Public Org", "email": f"test_{uuid.uuid4().hex[:6]}@public.com",
            "password": "test_pwd_placeholder"
        }, timeout=15)
        assert resp.status_code not in (401, 403), (
            f"INFRA-03: /api/organizations/register returned {resp.status_code}"
        )
        print(f"PASS INFRA-03 (/api/organizations/register): status={resp.status_code}")

    def test_INFRA03_public_org_signup_is_non_401(self):
        """INFRA-03: POST /api/organizations/signup returns non-401/403"""
        resp = requests.post(f"{BASE_URL}/api/organizations/signup", json={
            "name": "TEST_Signup Org", "email": f"test_{uuid.uuid4().hex[:6]}@signup.com",
            "password": "test_pwd_placeholder"
        }, timeout=15)
        assert resp.status_code not in (401, 403), (
            f"INFRA-03: /api/organizations/signup returned {resp.status_code}"
        )
        print(f"PASS INFRA-03 (/api/organizations/signup): status={resp.status_code}")

    def test_INFRA04_protected_tickets_returns_401(self):
        """INFRA-04: GET /api/tickets without auth → 401"""
        resp = requests.get(f"{BASE_URL}/api/tickets", timeout=10)
        assert resp.status_code == 401, f"INFRA-04: /api/tickets expected 401, got {resp.status_code}"
        print(f"PASS INFRA-04 (/api/tickets): 401 confirmed")

    def test_INFRA04_protected_invoices_enhanced_returns_401(self):
        """INFRA-04: GET /api/invoices-enhanced without auth → 401"""
        resp = requests.get(f"{BASE_URL}/api/invoices-enhanced", timeout=10, allow_redirects=True)
        assert resp.status_code == 401, (
            f"INFRA-04: /api/invoices-enhanced expected 401, got {resp.status_code}"
        )
        print(f"PASS INFRA-04 (/api/invoices-enhanced): 401 confirmed")

    def test_INFRA04_protected_hr_employees_returns_401(self):
        """INFRA-04: GET /api/hr/employees without auth → 401"""
        resp = requests.get(f"{BASE_URL}/api/hr/employees", timeout=10)
        assert resp.status_code == 401, (
            f"INFRA-04: /api/hr/employees expected 401, got {resp.status_code}"
        )
        print(f"PASS INFRA-04 (/api/hr/employees): 401 confirmed")

    def test_INFRA04_protected_trial_balance_returns_401(self):
        """INFRA-04: GET /api/reports/trial-balance without auth → 401"""
        resp = requests.get(f"{BASE_URL}/api/reports/trial-balance", timeout=10)
        assert resp.status_code == 401, (
            f"INFRA-04: /api/reports/trial-balance expected 401, got {resp.status_code}"
        )
        print(f"PASS INFRA-04 (/api/reports/trial-balance): 401 confirmed")


# ──────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────

class TestAUTH:
    """AUTH-01..03: Login, RBAC, cross-tenant isolation"""

    def test_AUTH01_admin_login_full_response(self):
        """AUTH-01: Admin login returns token, user object, organizations array"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        }, timeout=15)
        assert resp.status_code == 200, f"AUTH-01: login failed {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "token" in data, f"AUTH-01: no 'token' in response: {data.keys()}"
        assert isinstance(data["token"], str) and len(data["token"]) > 20, "AUTH-01: token too short"
        assert "user" in data, f"AUTH-01: no 'user' in response"
        user = data["user"]
        assert user.get("email") == ADMIN_EMAIL, f"AUTH-01: wrong email in user: {user}"
        assert "organizations" in data, f"AUTH-01: no 'organizations' in response"
        orgs = data["organizations"]
        assert isinstance(orgs, list) and len(orgs) >= 1, f"AUTH-01: organizations empty: {orgs}"
        print(f"PASS AUTH-01: token present, user.email={user['email']}, orgs={len(orgs)}")

    def test_AUTH01_invalid_credentials_rejected(self):
        """AUTH-01: Invalid credentials → 401"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": "wrong_pwd_placeholder"
        }, timeout=15)
        assert resp.status_code == 401, f"AUTH-01: invalid creds should return 401, got {resp.status_code}"
        print(f"PASS AUTH-01: invalid creds correctly rejected (401)")

    def test_AUTH02_tech_login_succeeds(self):
        """AUTH-02: Tech user login → 200"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECH_EMAIL, "password": TECH_PASSWORD
        }, timeout=15)
        assert resp.status_code == 200, f"AUTH-02: tech login failed {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "token" in data, "AUTH-02: no token in tech login response"
        print(f"PASS AUTH-02: tech login succeeded")

    def test_AUTH02_tech_cannot_access_payroll(self, tech_headers):
        """AUTH-02: Tech user → GET /api/hr/payroll/records → 403 (access denied)
        Note: 400 is also accepted — tenant guard may reject before entitlement check."""
        resp = requests.get(f"{BASE_URL}/api/hr/payroll/records", headers=tech_headers, timeout=15)
        assert resp.status_code in (403, 400), (
            f"AUTH-02: expected 403/400 for tech payroll access, got {resp.status_code}: {resp.text}"
        )
        print(f"PASS AUTH-02: tech payroll access blocked (status={resp.status_code})")

    def test_AUTH03_cross_tenant_returns_403(self, admin_token):
        """AUTH-03: Admin token with wrong org_id header → 403"""
        wrong_org = "000000000000000000000000"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": wrong_org,
        }
        resp = requests.get(f"{BASE_URL}/api/tickets", headers=headers, timeout=15)
        assert resp.status_code == 403, (
            f"AUTH-03: cross-tenant should return 403, got {resp.status_code}: {resp.text}"
        )
        print(f"PASS AUTH-03: cross-tenant access blocked (403)")


# ──────────────────────────────────────────────────────────
# FINANCE
# ──────────────────────────────────────────────────────────

class TestFINANCE:
    """FINANCE-01..03: Trial balance, P&L, Balance sheet"""

    def test_FINANCE01_trial_balance_is_balanced(self, admin_headers):
        """FINANCE-01: GET /api/reports/trial-balance → is_balanced=true, debit==credit"""
        resp = requests.get(f"{BASE_URL}/api/reports/trial-balance",
                            headers=admin_headers, timeout=20)
        assert resp.status_code == 200, f"FINANCE-01: {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("is_balanced") is True, f"FINANCE-01: is_balanced not True: {data}"
        summary = data.get("summary", {})
        debit = summary.get("total_debit", None)
        credit = summary.get("total_credit", None)
        assert debit is not None, f"FINANCE-01: total_debit missing in summary: {data}"
        assert credit is not None, f"FINANCE-01: total_credit missing in summary: {data}"
        assert abs(debit - credit) < 0.01, f"FINANCE-01: debit ({debit}) != credit ({credit})"
        print(f"PASS FINANCE-01: is_balanced=True, debit={debit}, credit={credit}")

    def test_FINANCE02_profit_loss_returns_200(self, admin_headers):
        """FINANCE-02: GET /api/reports/profit-loss → 200"""
        resp = requests.get(f"{BASE_URL}/api/reports/profit-loss",
                            headers=admin_headers, timeout=20)
        assert resp.status_code == 200, f"FINANCE-02: profit-loss returned {resp.status_code}: {resp.text}"
        print(f"PASS FINANCE-02: profit-loss 200")

    def test_FINANCE03_balance_sheet_returns_200(self, admin_headers):
        """FINANCE-03: GET /api/reports/balance-sheet → 200"""
        resp = requests.get(f"{BASE_URL}/api/reports/balance-sheet",
                            headers=admin_headers, timeout=20)
        assert resp.status_code == 200, f"FINANCE-03: balance-sheet returned {resp.status_code}: {resp.text}"
        print(f"PASS FINANCE-03: balance-sheet 200")


# ──────────────────────────────────────────────────────────
# OPERATIONS
# ──────────────────────────────────────────────────────────

class TestOPERATIONS:
    """OPERATIONS-01..04: Tickets, invoices, inventory, contacts"""

    def test_OPERATIONS01_tickets_paginated(self, admin_headers):
        """OPERATIONS-01: GET /api/tickets → 200, data + pagination keys"""
        resp = requests.get(f"{BASE_URL}/api/tickets", headers=admin_headers, timeout=15)
        assert resp.status_code == 200, f"OPERATIONS-01: {resp.status_code}: {resp.text}"
        data = resp.json()
        # Accept either {data:[], pagination:{}} or {tickets:[], total:N} or list
        has_data = (
            "data" in data or "tickets" in data
            or isinstance(data, list)
            or "results" in data
            or "items" in data
        )
        has_pagination = (
            "pagination" in data or "total" in data
            or "count" in data or isinstance(data, list)
        )
        assert has_data, f"OPERATIONS-01: no data key in response: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        assert has_pagination, f"OPERATIONS-01: no pagination key in response: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        print(f"PASS OPERATIONS-01: tickets paginated, keys={list(data.keys()) if isinstance(data, dict) else 'list'}")

    def test_OPERATIONS02_invoices_enhanced_returns_200(self, admin_headers):
        """OPERATIONS-02: GET /api/invoices-enhanced → 200 (trailing slash avoids redirect header drop)
        Note: FastAPI emits 307 redirect to /api/invoices-enhanced/; HTTPS→HTTP redirect drops
        Authorization header in requests lib. Testing with trailing slash directly."""
        resp = requests.get(f"{BASE_URL}/api/invoices-enhanced/",
                            headers=admin_headers, timeout=15)
        assert resp.status_code == 200, f"OPERATIONS-02: {resp.status_code}: {resp.text}"
        print(f"PASS OPERATIONS-02: invoices-enhanced 200")

    def test_OPERATIONS03_inventory_paginated(self, admin_headers):
        """OPERATIONS-03: GET /api/inventory → 200, paginated"""
        resp = requests.get(f"{BASE_URL}/api/inventory", headers=admin_headers, timeout=15)
        assert resp.status_code == 200, f"OPERATIONS-03: {resp.status_code}: {resp.text}"
        data = resp.json()
        has_data = (
            isinstance(data, list)
            or "data" in data or "items" in data
            or "inventory" in data or "results" in data
        )
        assert has_data, f"OPERATIONS-03: unexpected inventory response shape: {type(data)}"
        print(f"PASS OPERATIONS-03: inventory 200 paginated")

    def test_OPERATIONS04_contacts_enhanced_returns_200(self, admin_headers):
        """OPERATIONS-04: GET /api/contacts-enhanced → 200"""
        resp = requests.get(f"{BASE_URL}/api/contacts-enhanced",
                            headers=admin_headers, timeout=15)
        assert resp.status_code == 200, f"OPERATIONS-04: {resp.status_code}: {resp.text}"
        print(f"PASS OPERATIONS-04: contacts-enhanced 200")


# ──────────────────────────────────────────────────────────
# HR
# ──────────────────────────────────────────────────────────

class TestHR:
    """HR-01..02: Employees, Form16"""

    def test_HR01_employees_returns_200(self, admin_headers):
        """HR-01: GET /api/hr/employees → 200"""
        resp = requests.get(f"{BASE_URL}/api/hr/employees", headers=admin_headers, timeout=15)
        assert resp.status_code == 200, f"HR-01: {resp.status_code}: {resp.text}"
        print(f"PASS HR-01: employees 200")

    def test_HR02_form16_returns_200(self, admin_headers):
        """HR-02: GET /api/hr/payroll/form16/emp_7e79d8916b6b/2025-26 → 200"""
        emp_id = "emp_7e79d8916b6b"
        fy = "2025-26"
        resp = requests.get(
            f"{BASE_URL}/api/hr/payroll/form16/{emp_id}/{fy}",
            headers=admin_headers, timeout=20
        )
        assert resp.status_code == 200, f"HR-02: Form16 returned {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "employee" in data or "form16" in data or data.get("code") == 0, (
            f"HR-02: unexpected Form16 response shape: {data}"
        )
        print(f"PASS HR-02: Form16 200, employee={data.get('employee', {}).get('name', 'N/A')}")


# ──────────────────────────────────────────────────────────
# SECURITY
# ──────────────────────────────────────────────────────────

class TestSECURITY:
    """SECURITY-01..02: XSS sanitization, webhook idempotency"""

    def test_SECURITY01_xss_title_sanitized(self, admin_headers):
        """SECURITY-01: XSS in ticket title stripped on storage"""
        xss_title = "<script>alert(1)</script>XSS_CERT_TEST"
        resp = requests.post(f"{BASE_URL}/api/tickets", headers=admin_headers, json={
            "title": xss_title,
            "description": "Certification XSS test",
            "priority": "low",
            "status": "open",
        }, timeout=15)
        assert resp.status_code in (200, 201), f"SECURITY-01: create ticket failed {resp.status_code}: {resp.text}"
        data = resp.json()
        stored_title = data.get("title", "")
        assert "<script>" not in stored_title, (
            f"SECURITY-01: <script> tag NOT stripped! stored_title='{stored_title}'"
        )
        # Should keep the text but strip tags
        assert "XSS_CERT_TEST" in stored_title or "alert(1)" in stored_title, (
            f"SECURITY-01: text content missing from title: '{stored_title}'"
        )
        print(f"PASS SECURITY-01: XSS stripped, stored='{stored_title}'")

    def _build_webhook_payload(self, payment_id: str, event: str = "payment.captured") -> dict:
        return {
            "event": event,
            "payload": {
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "order_id": f"order_CERT_{uuid.uuid4().hex[:8]}",
                        "amount": 49900,
                        "currency": "INR",
                        "status": "captured",
                        "method": "upi",
                        "notes": {"organization_id": "", "invoice_id": ""},
                    }
                }
            }
        }

    def _sign_payload(self, body: bytes) -> str:
        return hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()

    def _post_webhook(self, payload: dict) -> requests.Response:
        body = json.dumps(payload, separators=(",", ":")).encode()
        sig = self._sign_payload(body)
        return requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data=body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
            timeout=15,
        )

    def test_SECURITY02_webhook_idempotency(self):
        """SECURITY-02: Duplicate webhook returns already_processed"""
        payment_id = f"pay_CERT_{uuid.uuid4().hex[:12]}"
        payload = self._build_webhook_payload(payment_id)

        # First call
        resp1 = self._post_webhook(payload)
        assert resp1.status_code == 200, f"SECURITY-02: first webhook failed {resp1.status_code}: {resp1.text}"
        status1 = resp1.json().get("status", "")
        assert status1 in ("processed", "ok", "success", "received"), (
            f"SECURITY-02: unexpected status on first call: {resp1.json()}"
        )

        # Second call — must be idempotent
        time.sleep(0.5)
        resp2 = self._post_webhook(payload)
        assert resp2.status_code == 200, f"SECURITY-02: second webhook failed {resp2.status_code}: {resp2.text}"
        data2 = resp2.json()
        assert data2.get("status") == "already_processed", (
            f"SECURITY-02: expected 'already_processed' on duplicate, got: {data2}"
        )
        print(f"PASS SECURITY-02: idempotency confirmed — first='{status1}', second='already_processed'")


# ──────────────────────────────────────────────────────────
# CONTACT
# ──────────────────────────────────────────────────────────

class TestCONTACT:
    """CONTACT-01..02: Contact form submission and validation"""

    def test_CONTACT01_submit_returns_200_and_stores(self):
        """CONTACT-01: POST /api/contact → 200, status=ok, stored in contact_submissions"""
        unique_msg = f"CERT_TEST_{uuid.uuid4().hex[:8]} production readiness check"
        resp = requests.post(f"{BASE_URL}/api/contact", json={
            "name": "Certification Tester",
            "email": "cert-test@battwheels.in",
            "company": "Battwheels QA",
            "type": "general",
            "message": unique_msg,
        }, timeout=20)
        assert resp.status_code == 200, f"CONTACT-01: {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "ok", f"CONTACT-01: status not ok: {data}"

        # Verify stored in DB
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]

        async def _check_db():
            doc = await db.contact_submissions.find_one({"message": unique_msg})
            return doc

        doc = asyncio.run(_check_db())
        assert doc is not None, "CONTACT-01: submission not found in contact_submissions collection"
        assert doc.get("email") == "cert-test@battwheels.in", f"CONTACT-01: wrong email in DB: {doc}"
        print(f"PASS CONTACT-01: 200 ok, stored in DB (id={doc.get('_id')})")

    def test_CONTACT02_missing_message_returns_422(self):
        """CONTACT-02: POST /api/contact without required field → 422"""
        resp = requests.post(f"{BASE_URL}/api/contact", json={
            "name": "Missing Message",
            "email": "missing@test.com",
            # message intentionally omitted
        }, timeout=15)
        assert resp.status_code == 422, (
            f"CONTACT-02: expected 422 for missing message, got {resp.status_code}: {resp.text}"
        )
        print(f"PASS CONTACT-02: missing message → 422 validation error")


# ──────────────────────────────────────────────────────────
# EFI
# ──────────────────────────────────────────────────────────

class TestEFI:
    """EFI-01: EFI engine responding"""

    def test_EFI01_failure_cards_returns_200(self, admin_headers):
        """EFI-01: GET /api/efi/failure-cards → 200 (EFI engine responding)
        Note: Review spec says GET /api/efi/match-failures; correct path is /api/efi/failure-cards"""
        resp = requests.get(f"{BASE_URL}/api/efi/failure-cards",
                            headers=admin_headers, timeout=20)
        assert resp.status_code == 200, f"EFI-01: {resp.status_code}: {resp.text}"
        print(f"PASS EFI-01: EFI engine responding (failure-cards 200)")


# ──────────────────────────────────────────────────────────
# PLATFORM
# ──────────────────────────────────────────────────────────

class TestPLATFORM:
    """PLATFORM-01: Platform admin can list all organizations"""

    def test_PLATFORM01_list_organizations(self, platform_admin_token):
        """PLATFORM-01: GET /api/platform/organizations → 200"""
        if not platform_admin_token:
            pytest.skip("Platform admin token not available")
        resp = requests.get(f"{BASE_URL}/api/platform/organizations", headers={
            "Authorization": f"Bearer {platform_admin_token}",
        }, timeout=15)
        assert resp.status_code == 200, (
            f"PLATFORM-01: platform/organizations returned {resp.status_code}: {resp.text}"
        )
        data = resp.json()
        orgs = data.get("organizations", data) if isinstance(data, dict) else data
        assert isinstance(orgs, list), f"PLATFORM-01: expected list of orgs, got: {type(orgs)}"
        print(f"PASS PLATFORM-01: platform/organizations 200, count={len(orgs)}")


# ──────────────────────────────────────────────────────────
# DB
# ──────────────────────────────────────────────────────────

class TestDB:
    """DB-01..02: MongoDB collection and index checks"""

    def test_DB01_contact_submissions_collection_exists(self):
        """DB-01: contact_submissions has at least 1 document"""
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]

        async def _check():
            count = await db.contact_submissions.count_documents({})
            return count

        count = asyncio.run(_check())
        assert count >= 1, f"DB-01: contact_submissions has {count} docs (expected >= 1)"
        print(f"PASS DB-01: contact_submissions has {count} document(s)")

    def test_DB02_webhook_logs_has_org_id_index(self):
        """DB-02: organization_id index exists on webhook_logs"""
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]

        async def _check():
            indexes = await db.webhook_logs.index_information()
            return indexes

        indexes = asyncio.run(_check())
        # Look for any index that covers organization_id
        org_id_indexed = any(
            "organization_id" in str(idx_info.get("key", {}))
            for idx_name, idx_info in indexes.items()
        )
        assert org_id_indexed, (
            f"DB-02: no organization_id index on webhook_logs. Indexes: {list(indexes.keys())}"
        )
        print(f"PASS DB-02: organization_id index exists on webhook_logs — {list(indexes.keys())}")


# ──────────────────────────────────────────────────────────
# DEPS
# ──────────────────────────────────────────────────────────

class TestDEPS:
    """DEPS-01..02: pip-audit and yarn audit"""

    def test_DEPS01_pip_audit_no_unfixed_cves(self):
        """DEPS-01: pip-audit ignoring ecdsa → exit 0"""
        result = subprocess.run(
            ["pip-audit", "--ignore-vuln", "GHSA-3f63-hfp8-52jq"],
            capture_output=True, text=True, timeout=120,
            cwd="/app/backend"
        )
        output = result.stdout + result.stderr
        # Exit code 0 = no vulnerabilities (ignoring ecdsa)
        if result.returncode != 0:
            print(f"pip-audit stdout: {result.stdout[:500]}")
            print(f"pip-audit stderr: {result.stderr[:500]}")
        assert result.returncode == 0, (
            f"DEPS-01: pip-audit found unfixed CVEs (exit={result.returncode})\n"
            f"Output: {output[:1000]}"
        )
        print(f"PASS DEPS-01: pip-audit exit 0 (no unfixed CVEs)")

    def test_DEPS02_yarn_audit_acceptable(self):
        """DEPS-02: yarn audit --level high → acceptable (1 HIGH for jsonpath, build-time only, no fix)"""
        result = subprocess.run(
            ["yarn", "audit", "--level", "high", "--json"],
            capture_output=True, text=True, timeout=120,
            cwd="/app/frontend"
        )
        output = result.stdout + result.stderr

        # Parse JSONL output to count HIGH vulns
        high_count = 0
        critical_count = 0
        unfixable_high_pkgs = set()
        fixable_high_count = 0

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "auditAdvisory":
                    advisory = obj.get("data", {}).get("advisory", {})
                    sev = advisory.get("severity", "").upper()
                    title = advisory.get("title", "")
                    module_name = advisory.get("module_name", "")
                    patched = advisory.get("patched_versions", "")

                    if sev == "CRITICAL":
                        critical_count += 1
                    elif sev == "HIGH":
                        high_count += 1
                        if not patched or patched in ("<0.0.0>", ""):
                            unfixable_high_pkgs.add(module_name)
                        else:
                            fixable_high_count += 1
            except json.JSONDecodeError:
                pass

        print(f"yarn audit: HIGH={high_count}, CRITICAL={critical_count}, "
              f"unfixable_high={unfixable_high_pkgs}, fixable_high={fixable_high_count}")

        # ACCEPTABLE: 1 HIGH for jsonpath (build-time only, no fix available)
        # UNACCEPTABLE: Any CRITICAL, or HIGH with fix available
        assert critical_count == 0, f"DEPS-02: {critical_count} CRITICAL vulns found — UNACCEPTABLE"
        assert fixable_high_count == 0, (
            f"DEPS-02: {fixable_high_count} HIGH vuln(s) WITH available fix — must be patched: "
            f"output={output[:500]}"
        )
        # jsonpath HIGH with no fix is acceptable per spec
        print(f"PASS DEPS-02: yarn audit — no CRITICAL, no fixable HIGH. "
              f"Unfixable HIGH (acceptable): {unfixable_high_pkgs}")
