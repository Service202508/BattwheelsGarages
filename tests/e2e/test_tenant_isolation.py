"""
Multi-Tenant Isolation & RBAC E2E Test Suite
=============================================

Tests that the Battwheels OS platform correctly isolates tenant data,
enforces role-based access control, and applies subscription entitlements.

Run with:
    cd /app && REACT_APP_BACKEND_URL=<url> python -m pytest tests/e2e/test_tenant_isolation.py -v

Pre-conditions (seeded once, idempotent):
    Org A  — Battwheels Garages     — admin@battwheels.in / admin         — PROFESSIONAL
    Org B  — Test Workshop B        — admin@testworkshopb.com / adminB123  — STARTER
    Free   — Free Test Org          — freetester@test.com / testpass123    — FREE
    Plat   — Platform Admin         — platform-admin@battwheels.in / admin — (no org)
    Tech   — Technician (Org A)     — deepak@battwheelsgarages.in / tech123

Known seed IDs:
    Org A ticket:   tkt_bc6a640e425b  (ORGA_ISOLATION_TEST_TICKET)
    Org A contact:  CON-29372294A9AB  (ORGA_TEST_CONTACT)
    Org A invoice:  inv_08b1717ea43f
    Org B ticket:   tkt_38b2bf1e6a69  (ORGB_ISOLATION_TEST_TICKET)
    Org B contact:  CON-9309B2F641C2  (ORGB_TEST_CONTACT)
    Org B invoice:  inv_31da406729f1  (INV-202602-0002)
"""

import os
import time
import pytest
import requests

# ── Config ──────────────────────────────────────────────────────────────────
API_URL = os.getenv("REACT_APP_BACKEND_URL", "https://p0-p1-patch.preview.emergentagent.com")
BASE = f"{API_URL}/api"

# ── Org / User constants ─────────────────────────────────────────────────────
ORG_A_ID     = "6996dcf072ffd2a2395fee7b"
ORG_B_ID     = "org_testworkshopb01"
FREE_ORG_ID  = "org_freetestorg01"

ADMIN_A      = {"email": "admin@battwheels.in",          "password": "admin"}
ADMIN_B      = {"email": "admin@testworkshopb.com",      "password": "adminB123"}
ADMIN_FREE   = {"email": "freetester@test.com",          "password": "test_pwd_placeholder"}
PLATFORM_ADMIN = {"email": "platform-admin@battwheels.in", "password": "admin"}
TECHNICIAN_A = {"email": "deepak@battwheelsgarages.in",  "password": "tech123"}

# ── Seed IDs ─────────────────────────────────────────────────────────────────
ORG_A_TICKET   = "tkt_bc6a640e425b"
ORG_A_CONTACT  = "CON-29372294A9AB"
ORG_A_INVOICE  = "inv_08b1717ea43f"
ORG_B_TICKET   = "tkt_38b2bf1e6a69"
ORG_B_CONTACT  = "CON-9309B2F641C2"
ORG_B_INVOICE  = "inv_31da406729f1"

# ── Token cache (module-level, login once per test session) ──────────────────
_token_cache: dict[str, str] = {}


@pytest.fixture(scope="session", autouse=True)
def ensure_clean_state():
    """Ensure Org B is active and on Starter plan before the test suite runs."""
    # Activate Org B (in case a previous run left it suspended)
    try:
        plat_token = _login_with_retry(PLATFORM_ADMIN)
        h = {"Authorization": f"Bearer {plat_token}"}
        requests.post(f"{BASE}/platform/organizations/{ORG_B_ID}/activate", headers=h, timeout=15)
        requests.put(f"{BASE}/platform/organizations/{ORG_B_ID}/plan",
                     headers=h, json={"plan_type": "starter"}, timeout=15)
    except Exception:
        pass  # Non-fatal — tests will surface the issue themselves
    yield


def _login_with_retry(creds: dict, max_retries: int = 3) -> str:
    """Login with exponential back-off on rate limit."""
    for attempt in range(max_retries):
        r = requests.post(f"{BASE}/auth/login", json=creds, timeout=15)
        if r.status_code == 200:
            return r.json()["token"]
        if r.status_code == 429:
            wait = (attempt + 1) * 20
            time.sleep(wait)
        else:
            pytest.fail(f"Login failed for {creds['email']}: {r.status_code} {r.text[:200]}")
    pytest.fail(f"Login still rate-limited after {max_retries} retries for {creds['email']}")


def get_token(creds: dict) -> str:
    """Return a cached token, logging in lazily."""
    key = creds["email"]
    if key not in _token_cache:
        _token_cache[key] = _login_with_retry(creds)
    return _token_cache[key]


def hdrs(creds: dict, org_id: str = None) -> dict:
    h = {"Authorization": f"Bearer {get_token(creds)}"}
    if org_id:
        h["X-Organization-Id"] = org_id
    return h


def api_get(creds, path, org_id=None):
    return requests.get(f"{BASE}{path}", headers=hdrs(creds, org_id), timeout=15)


def api_post(creds, path, org_id=None, **kwargs):
    return requests.post(f"{BASE}{path}", headers=hdrs(creds, org_id), timeout=15, **kwargs)


# ── Helpers ──────────────────────────────────────────────────────────────────
def ticket_ids(response: requests.Response) -> list[str]:
    data = response.json()
    if isinstance(data, list):
        return [t.get("ticket_id", "") for t in data]
    # Handle both 'tickets' and 'data' keys
    return [t.get("ticket_id", "") for t in
            data.get("tickets", data.get("data", []))]


def invoice_ids(response: requests.Response) -> list[str]:
    data = response.json()
    if isinstance(data, list):
        return [i.get("invoice_id", "") for i in data]
    return [i.get("invoice_id", "") for i in
            data.get("invoices", data.get("data", []))]


def contact_ids(response: requests.Response) -> list[str]:
    data = response.json()
    if isinstance(data, list):
        return [c.get("contact_id", "") for c in data]
    return [c.get("contact_id", "") for c in data.get("data", data.get("contacts", []))]


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 1 — DATA ISOLATION
# ═══════════════════════════════════════════════════════════════════════════

class TestDataIsolation:
    """Verify that each org only sees its own data."""

    def test_org_a_cannot_see_org_b_tickets(self):
        """Org A ticket list must NOT contain any Org B ticket IDs."""
        r = api_get(ADMIN_A, "/tickets?per_page=200", ORG_A_ID)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        ids = ticket_ids(r)
        assert ORG_B_TICKET not in ids, (
            f"ISOLATION BREACH: Org B ticket {ORG_B_TICKET} appeared in Org A response"
        )

    def test_org_a_own_ticket_visible(self):
        """Org A's own isolation test ticket must appear in its list."""
        r = api_get(ADMIN_A, "/tickets?per_page=200", ORG_A_ID)
        assert r.status_code == 200
        ids = ticket_ids(r)
        assert ORG_A_TICKET in ids, (
            f"Org A ticket {ORG_A_TICKET} not found — check test data or pagination"
        )

    def test_org_a_cannot_see_org_b_invoices(self):
        """Org A invoice list must NOT contain any Org B invoices."""
        r = api_get(ADMIN_A, "/invoices?per_page=200", ORG_A_ID)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        ids = invoice_ids(r)
        assert ORG_B_INVOICE not in ids, (
            f"ISOLATION BREACH: Org B invoice {ORG_B_INVOICE} appeared in Org A response"
        )

    def test_org_a_cannot_see_org_b_contacts(self):
        """Org A contact list must NOT include Org B contacts."""
        r = api_get(ADMIN_A, "/contacts-enhanced/?per_page=200", ORG_A_ID)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        ids = contact_ids(r)
        assert ORG_B_CONTACT not in ids, (
            f"ISOLATION BREACH: Org B contact {ORG_B_CONTACT} found in Org A contact list"
        )

    def test_org_b_cannot_see_org_a_tickets(self):
        """Symmetry: Org B ticket list must NOT contain Org A tickets."""
        r = api_get(ADMIN_B, "/tickets?per_page=200", ORG_B_ID)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        ids = ticket_ids(r)
        assert ORG_A_TICKET not in ids, (
            f"ISOLATION BREACH: Org A ticket {ORG_A_TICKET} appeared in Org B response"
        )

    def test_direct_ticket_id_blocked_across_orgs(self):
        """Org A admin must not fetch Org B's ticket by ID."""
        r = api_get(ADMIN_A, f"/tickets/{ORG_B_TICKET}", ORG_A_ID)
        assert r.status_code in (403, 404), (
            f"ISOLATION BREACH: Got {r.status_code} for cross-org ticket access. Body: {r.text[:200]}"
        )
        body = r.json()
        assert body.get("ticket_id") != ORG_B_TICKET, "BREACH: Org B ticket data returned to Org A"

    def test_direct_contact_id_blocked_across_orgs(self):
        """Org A admin must not fetch Org B's contact by ID."""
        r = api_get(ADMIN_A, f"/contacts-enhanced/{ORG_B_CONTACT}", ORG_A_ID)
        assert r.status_code in (403, 404), (
            f"ISOLATION BREACH: Got {r.status_code} for cross-org contact. Body: {r.text[:200]}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 2 — CREDENTIAL ISOLATION (Invoice Numbering)
# ═══════════════════════════════════════════════════════════════════════════

class TestCredentialIsolation:
    """Verify per-org sequential numbering is independent."""

    def test_invoice_numbering_independent_across_orgs(self):
        """
        Org B's invoice number must be independent of Org A's sequence.
        Org A is at INV-00074+; Org B's test invoice is INV-202602-0002.
        They must not share numbers.
        """
        r_a = api_get(ADMIN_A, "/invoices?per_page=1", ORG_A_ID)
        assert r_a.status_code == 200
        r_b = api_get(ADMIN_B, f"/invoices/{ORG_B_INVOICE}", ORG_B_ID)
        # Either direct fetch works or list it
        if r_b.status_code == 200:
            orgb_number = r_b.json().get("invoice_number")
        else:
            r_b2 = api_get(ADMIN_B, "/invoices?per_page=1", ORG_B_ID)
            assert r_b2.status_code == 200
            b_list = r_b2.json()
            b_invs = b_list if isinstance(b_list, list) else b_list.get("data", b_list.get("invoices", []))
            orgb_number = b_invs[0]["invoice_number"] if b_invs else None

        assert orgb_number is not None, "Could not retrieve Org B invoice number"
        a_invs = r_a.json()
        a_list = a_invs if isinstance(a_invs, list) else a_invs.get("data", a_invs.get("invoices", []))
        orga_number = a_list[0]["invoice_number"] if a_list else None

        # They must not have the same invoice number
        assert orga_number != orgb_number, (
            f"NUMBERING BREACH: Same invoice number '{orgb_number}' across orgs"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 3 — RBAC (Role-Based Access Control)
# ═══════════════════════════════════════════════════════════════════════════

class TestRBAC:
    """Verify role-based endpoint access."""

    def test_technician_blocked_from_finance_dashboard(self):
        """Technician role must be blocked from finance endpoints."""
        r = api_get(TECHNICIAN_A, "/finance/dashboard", ORG_A_ID)
        assert r.status_code == 403, (
            f"Expected 403 for technician on /finance/dashboard, got {r.status_code}: {r.text[:200]}"
        )

    def test_technician_blocked_from_payroll(self):
        """Technician role must not access payroll records."""
        r = api_get(TECHNICIAN_A, "/hr/payroll/records", ORG_A_ID)
        assert r.status_code in (403, 401), (
            f"Expected 403/401 for technician on payroll, got {r.status_code}: {r.text[:200]}"
        )

    def test_technician_can_access_own_tickets(self):
        """Technician must still access tickets (their primary workflow)."""
        r = api_get(TECHNICIAN_A, "/tickets?per_page=5", ORG_A_ID)
        assert r.status_code == 200, (
            f"Technician should access tickets, got {r.status_code}: {r.text[:200]}"
        )

    def test_org_b_admin_cannot_inject_org_a_header(self):
        """Org B admin using Org A's header must not get Org A data."""
        r = api_get(ADMIN_B, f"/tickets/{ORG_A_TICKET}", ORG_A_ID)
        assert r.status_code in (403, 401, 404), (
            f"CRITICAL ISOLATION BREACH: Org B user accessed Org A data. "
            f"Status: {r.status_code}, Body: {r.text[:200]}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 4 — SUBSCRIPTION ENTITLEMENTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEntitlements:
    """Verify subscription plan gating at the API level."""

    def test_free_plan_blocked_from_payroll(self):
        """Free plan must receive 403 feature_not_available on payroll."""
        r = api_get(ADMIN_FREE, "/hr/payroll/records", FREE_ORG_ID)
        assert r.status_code == 403, (
            f"Expected 403 for free plan on payroll, got {r.status_code}: {r.text[:200]}"
        )
        detail = r.json().get("detail", {})
        assert detail.get("error") == "feature_not_available", (
            f"Expected feature_not_available, got: {detail}"
        )
        assert detail.get("current_plan") == "free"
        assert detail.get("required_plan") is not None

    def test_professional_plan_allowed_payroll(self):
        """Professional plan must access payroll without restriction."""
        r = api_get(ADMIN_A, "/hr/payroll/records", ORG_A_ID)
        assert r.status_code == 200, (
            f"Professional plan should access payroll, got {r.status_code}: {r.text[:200]}"
        )

    def test_starter_plan_blocked_from_payroll(self):
        """Starter plan is blocked from payroll (requires Professional minimum)."""
        r = api_get(ADMIN_B, "/hr/payroll/records", ORG_B_ID)
        assert r.status_code == 403, (
            f"Starter plan should be blocked from payroll, got {r.status_code}: {r.text[:200]}"
        )
        raw_detail = r.json().get("detail", {})
        # detail can be a dict (feature_not_available) or a string (other 403)
        if isinstance(raw_detail, dict):
            assert raw_detail.get("error") == "feature_not_available", (
                f"Expected feature_not_available, got: {raw_detail}"
            )
        else:
            assert "feature" in str(raw_detail).lower() or "plan" in str(raw_detail).lower(), (
                f"Expected plan-related denial message, got: {raw_detail}"
            )

    def test_starter_plan_allowed_advanced_reports(self):
        """Starter plan must access advanced reports (STARTER minimum)."""
        r = api_get(ADMIN_B, "/reports-advanced/summary", ORG_B_ID)
        assert r.status_code != 403, (
            f"Starter should access advanced reports but got 403: {r.text[:200]}"
        )

    def test_free_plan_blocked_from_projects(self):
        """Free plan is blocked from project management (requires Professional)."""
        r = api_get(ADMIN_FREE, "/projects", FREE_ORG_ID)
        assert r.status_code == 403, (
            f"Expected 403 for free plan on /projects, got {r.status_code}: {r.text[:200]}"
        )
        detail = r.json().get("detail", {})
        assert detail.get("error") == "feature_not_available"

    def test_feature_not_available_response_structure(self):
        """403 feature_not_available must include all fields for the frontend modal."""
        r = api_get(ADMIN_FREE, "/hr/payroll/records", FREE_ORG_ID)
        assert r.status_code == 403
        detail = r.json().get("detail", {})
        required = ["error", "feature", "feature_key", "current_plan", "required_plan",
                    "message", "upgrade_url"]
        missing = [f for f in required if f not in detail]
        assert not missing, f"Missing fields in 403 response: {missing}. Got: {list(detail.keys())}"


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 5 — PLATFORM ADMIN
# ═══════════════════════════════════════════════════════════════════════════

class TestPlatformAdmin:
    """Verify platform admin capabilities and isolation."""

    def test_platform_admin_can_list_all_orgs(self):
        """Platform admin sees all registered organizations."""
        r = api_get(PLATFORM_ADMIN, "/platform/organizations?per_page=100")
        assert r.status_code == 200, (
            f"Platform orgs list failed: {r.status_code} {r.text[:200]}"
        )
        data = r.json()
        orgs = data.get("organizations", data) if isinstance(data, dict) else data
        org_ids = [o.get("organization_id", "") for o in orgs]
        assert ORG_A_ID in org_ids, f"Org A not in platform list"
        assert ORG_B_ID in org_ids, f"Org B not in platform list"

    def test_regular_admin_blocked_from_platform_routes(self):
        """Regular org admin must NOT access /platform/* routes.
        Note: admin@battwheels.in has is_platform_admin=True, so we use Org B admin."""
        r = api_get(ADMIN_B, "/platform/organizations", ORG_B_ID)
        assert r.status_code in (403, 401), (
            f"SECURITY BREACH: Regular admin accessed platform routes. "
            f"Status: {r.status_code}, Body: {r.text[:200]}"
        )

    def test_platform_admin_can_change_org_plan(self):
        """Platform admin can upgrade Org B to Professional, then revert."""
        # Upgrade — endpoint is PUT /platform/organizations/{id}/plan with {"plan_type": "..."}
        r = requests.put(f"{BASE}/platform/organizations/{ORG_B_ID}/plan",
                         headers=hdrs(PLATFORM_ADMIN), json={"plan_type": "professional"}, timeout=15)
        assert r.status_code == 200, f"Upgrade failed: {r.status_code} {r.text[:200]}"

        # Verify Org B now passes payroll check — invalidate token cache for fresh token
        if ADMIN_B["email"] in _token_cache:
            del _token_cache[ADMIN_B["email"]]
        r2 = api_get(ADMIN_B, "/hr/payroll/records", ORG_B_ID)
        assert r2.status_code == 200, (
            f"After Professional upgrade, Org B should access payroll. "
            f"Got {r2.status_code}: {r2.text[:200]}"
        )

        # Revert to Starter
        r3 = requests.put(f"{BASE}/platform/organizations/{ORG_B_ID}/plan",
                          headers=hdrs(PLATFORM_ADMIN), json={"plan_type": "starter"}, timeout=15)
        assert r3.status_code == 200, f"Plan revert failed: {r3.status_code}"

    def test_platform_admin_can_suspend_and_reactivate_org(self):
        """Platform admin can suspend Org B; its admin gets blocked; then reactivate."""
        # Suspend
        r = api_post(PLATFORM_ADMIN, f"/platform/organizations/{ORG_B_ID}/suspend")
        assert r.status_code == 200, f"Suspend failed: {r.status_code} {r.text[:200]}"

        # Org B admin should now be blocked
        # Invalidate cached token so we force re-login / re-check
        if ADMIN_B["email"] in _token_cache:
            del _token_cache[ADMIN_B["email"]]

        r2 = api_get(ADMIN_B, "/tickets", ORG_B_ID)
        # Suspended org should get 403/401 on data access, or login should fail
        if r2.status_code == 200:
            # If login somehow succeeds, this is a potential breach — flag it
            pytest.fail(
                f"Suspended org B returned 200 on /tickets. "
                f"Suspension may not be enforced at the API level."
            )
        assert r2.status_code in (401, 403, 423), (
            f"Expected block for suspended org, got {r2.status_code}: {r2.text[:200]}"
        )

        # Re-activate
        r3 = api_post(PLATFORM_ADMIN, f"/platform/organizations/{ORG_B_ID}/activate")
        assert r3.status_code == 200, f"Activate failed: {r3.status_code}"

        # Clear cache so next tests get fresh token
        if ADMIN_B["email"] in _token_cache:
            del _token_cache[ADMIN_B["email"]]

    def test_platform_admin_metrics(self):
        """Platform metrics endpoint returns aggregate data."""
        r = api_get(PLATFORM_ADMIN, "/platform/metrics")
        assert r.status_code == 200, f"Metrics failed: {r.status_code} {r.text[:200]}"
        data = r.json()
        assert any(k in data for k in ["total_organizations", "total_users", "total_orgs"]), (
            f"Metrics missing org/user counts. Keys: {list(data.keys())}"
        )
