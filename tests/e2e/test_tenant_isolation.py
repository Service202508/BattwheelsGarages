"""
Multi-Tenant Isolation & RBAC E2E Test Suite
=============================================

Tests that the Battwheels OS platform correctly isolates tenant data,
enforces role-based access control, and applies subscription entitlements.

Run with:
    cd /app && python -m pytest tests/e2e/test_tenant_isolation.py -v

Pre-conditions (seeded once, idempotent):
    Org A  — Battwheels Garages     — admin@battwheels.in / admin         — PROFESSIONAL
    Org B  — Test Workshop B        — admin@testworkshopb.com / adminB123  — STARTER
    Free   — Free Test Org          — freetester@test.com / testpass123    — FREE
    Plat   — Platform Admin         — platform-admin@battwheels.in / admin — (no org)
    Tech   — Technician (Org A)     — deepak@battwheelsgarages.in / tech123
    Cust   — Customer portal user   — customer@demo.com / (any)

Known seed data:
    Org A ticket:   tkt_bc6a640e425b  (ORGA_ISOLATION_TEST_TICKET)
    Org A contact:  CON-29372294A9AB  (ORGA_TEST_CONTACT)
    Org A invoice:  inv_08b1717ea43f
    Org B ticket:   tkt_38b2bf1e6a69  (ORGB_ISOLATION_TEST_TICKET)
    Org B contact:  CON-9309B2F641C2  (ORGB_TEST_CONTACT)
    Org B invoice:  inv_31da406729f1  (INV-202602-0002)
"""

import os
import pytest
import requests

# ── Config ──────────────────────────────────────────────────────────────────
API_URL = os.getenv("REACT_APP_BACKEND_URL", "https://feature-gating-4.preview.emergentagent.com")
BASE = f"{API_URL}/api"

# ── Org / User constants ─────────────────────────────────────────────────────
ORG_A_ID      = "6996dcf072ffd2a2395fee7b"
ORG_B_ID      = "org_testworkshopb01"
FREE_ORG_ID   = "org_freetestorg01"

ADMIN_A       = {"email": "admin@battwheels.in",      "password": "admin"}
ADMIN_B       = {"email": "admin@testworkshopb.com",  "password": "adminB123"}
ADMIN_FREE    = {"email": "freetester@test.com",      "password": "test_pwd_placeholder"}
PLATFORM_ADMIN = {"email": "platform-admin@battwheels.in", "password": "admin"}
TECHNICIAN_A  = {"email": "deepak@battwheelsgarages.in", "password": "tech123"}
CUSTOMER_A    = {"email": "customer@demo.com",        "password": ""}

# ── Seed IDs ─────────────────────────────────────────────────────────────────
ORG_A_TICKET  = "tkt_bc6a640e425b"
ORG_A_CONTACT = "CON-29372294A9AB"
ORG_A_INVOICE = "inv_08b1717ea43f"

ORG_B_TICKET  = "tkt_38b2bf1e6a69"
ORG_B_CONTACT = "CON-9309B2F641C2"
ORG_B_INVOICE = "inv_31da406729f1"


# ── Helper ───────────────────────────────────────────────────────────────────
def login(creds: dict, org_id: str = None) -> tuple[str, dict]:
    """Login and return (token, org_id_used)."""
    r = requests.post(f"{BASE}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.text[:200]}"
    data = r.json()
    token = data["token"]
    # If org_id not provided, take first org from response
    if org_id is None:
        orgs = data.get("organizations", [])
        org_id = orgs[0]["organization_id"] if orgs else None
    return token, org_id


def auth_headers(token: str, org_id: str = None) -> dict:
    h = {"Authorization": f"Bearer {token}"}
    if org_id:
        h["X-Organization-Id"] = org_id
    return h


def get(token: str, path: str, org_id: str = None, **kwargs):
    return requests.get(f"{BASE}{path}", headers=auth_headers(token, org_id),
                        timeout=15, **kwargs)


def post(token: str, path: str, org_id: str = None, **kwargs):
    return requests.post(f"{BASE}{path}", headers=auth_headers(token, org_id),
                         timeout=15, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 1 — DATA ISOLATION
# ═══════════════════════════════════════════════════════════════════════════

class TestDataIsolation:
    """Verify that each org can only see its own data."""

    def test_org_a_cannot_see_org_b_tickets(self):
        """Org A's ticket list must not contain any Org B tickets."""
        token, oid = login(ADMIN_A, ORG_A_ID)
        r = get(token, "/tickets?per_page=100", oid)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        tickets = r.json()
        # Flatten to list of ticket IDs (handle both list and dict response)
        if isinstance(tickets, list):
            ids = [t.get("ticket_id", "") for t in tickets]
        else:
            ids = [t.get("ticket_id", "") for t in tickets.get("tickets", [])]

        assert ORG_B_TICKET not in ids, (
            f"ISOLATION BREACH: Org B ticket {ORG_B_TICKET} appeared in Org A's response"
        )
        # Org A's own ticket should be visible
        assert ORG_A_TICKET in ids, (
            f"Org A ticket {ORG_A_TICKET} not found in Org A's own list — test data missing"
        )

    def test_org_a_cannot_see_org_b_invoices(self):
        """Org A's invoice list must not contain any Org B invoices."""
        token, oid = login(ADMIN_A, ORG_A_ID)
        r = get(token, "/invoices?per_page=200", oid)
        assert r.status_code == 200

        invs = r.json()
        if isinstance(invs, list):
            ids = [i.get("invoice_id", "") for i in invs]
        else:
            ids = [i.get("invoice_id", "") for i in invs.get("invoices", invs.get("data", []))]

        assert ORG_B_INVOICE not in ids, (
            f"ISOLATION BREACH: Org B invoice {ORG_B_INVOICE} appeared in Org A's response"
        )

    def test_org_a_cannot_see_org_b_contacts(self):
        """Org A's contact list must not include Org B contacts."""
        token, oid = login(ADMIN_A, ORG_A_ID)
        r = get(token, "/contacts-enhanced/?per_page=200", oid)
        assert r.status_code == 200

        body = r.json()
        contacts = body if isinstance(body, list) else body.get("data", body.get("contacts", []))
        contact_ids = [c.get("contact_id", "") for c in contacts]

        assert ORG_B_CONTACT not in contact_ids, (
            f"ISOLATION BREACH: Org B contact {ORG_B_CONTACT} found in Org A's contact list"
        )
        assert ORG_A_CONTACT in contact_ids, (
            f"Org A contact {ORG_A_CONTACT} not found in Org A's list — test data missing"
        )

    def test_org_b_cannot_see_org_a_tickets(self):
        """Symmetry check — Org B cannot see Org A's data."""
        token, oid = login(ADMIN_B, ORG_B_ID)
        r = get(token, "/tickets?per_page=100", oid)
        assert r.status_code == 200

        tickets = r.json()
        ids = [t.get("ticket_id", "") for t in (
            tickets if isinstance(tickets, list) else tickets.get("tickets", [])
        )]

        assert ORG_A_TICKET not in ids, (
            f"ISOLATION BREACH: Org A ticket {ORG_A_TICKET} appeared in Org B's response"
        )

    def test_direct_ticket_id_access_blocked_across_orgs(self):
        """Org A admin cannot fetch Org B's ticket by ID."""
        token, oid = login(ADMIN_A, ORG_A_ID)
        r = get(token, f"/tickets/{ORG_B_TICKET}", oid)
        assert r.status_code in (403, 404), (
            f"ISOLATION BREACH: Org A got {r.status_code} for Org B ticket {ORG_B_TICKET}. "
            f"Body: {r.text[:200]}"
        )
        # Critically: response must NOT contain Org B ticket data
        body = r.json()
        assert body.get("ticket_id") != ORG_B_TICKET, (
            f"ISOLATION BREACH: Org B ticket data was returned to Org A user"
        )

    def test_direct_contact_id_access_blocked_across_orgs(self):
        """Org A admin cannot fetch Org B's contact by ID."""
        token, oid = login(ADMIN_A, ORG_A_ID)
        r = get(token, f"/contacts-enhanced/{ORG_B_CONTACT}", oid)
        # Some implementations return 404 (not found for this org), others 403
        assert r.status_code in (403, 404), (
            f"ISOLATION BREACH: Got {r.status_code} when accessing Org B contact. Body: {r.text[:200]}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 2 — CREDENTIAL ISOLATION (Invoice Numbering)
# ═══════════════════════════════════════════════════════════════════════════

class TestCredentialIsolation:
    """Verify per-org sequential numbering."""

    def test_org_b_invoice_numbering_independent_from_org_a(self):
        """
        Org B's invoices are numbered independently from Org A.
        Org A is at INV-0007x+, Org B's first test invoice must not
        be a continuation of Org A's sequence.
        """
        token_a, oid_a = login(ADMIN_A, ORG_A_ID)
        token_b, oid_b = login(ADMIN_B, ORG_B_ID)

        # Get Org A latest invoice number
        r_a = get(token_a, "/invoices?per_page=1", oid_a)
        assert r_a.status_code == 200
        orga_invs = r_a.json()
        orga_inv_list = orga_invs if isinstance(orga_invs, list) else orga_invs.get("data", orga_invs.get("invoices", []))
        orga_number = orga_inv_list[0]["invoice_number"] if orga_inv_list else "INV-00000"

        # Get Org B invoice
        r_b = get(token_b, f"/invoices/{ORG_B_INVOICE}", oid_b)
        # If not found by ID, list invoices
        if r_b.status_code != 200:
            r_b = get(token_b, "/invoices?per_page=1", oid_b)
            assert r_b.status_code == 200
            orgb_invs = r_b.json()
            orgb_inv_list = orgb_invs if isinstance(orgb_invs, list) else orgb_invs.get("data", orgb_invs.get("invoices", []))
            orgb_number = orgb_inv_list[0]["invoice_number"] if orgb_inv_list else None
        else:
            orgb_number = r_b.json().get("invoice_number")

        assert orgb_number is not None, "Could not retrieve Org B invoice number"
        assert orgb_number != orga_number, (
            f"Invoice numbers are equal across orgs ({orgb_number}) — possible shared sequence"
        )
        # Org B sequence should start fresh, not continue Org A's high numbers
        # INV-202602-0002 vs INV-00074 confirms per-org numbering
        assert orga_number != orgb_number, "NUMBERING BREACH: Same invoice number across orgs"


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 3 — RBAC (Role-Based Access Control)
# ═══════════════════════════════════════════════════════════════════════════

class TestRBAC:
    """Verify that roles restrict access to the correct endpoints."""

    def test_technician_cannot_access_finance_dashboard(self):
        """Technician role must be blocked from finance endpoints."""
        token, oid = login(TECHNICIAN_A, ORG_A_ID)
        r = get(token, "/finance/dashboard", oid)
        assert r.status_code == 403, (
            f"Expected 403 for technician on /finance/dashboard, got {r.status_code}: {r.text[:200]}"
        )

    def test_technician_cannot_access_payroll(self):
        """Technician role must not access payroll records."""
        token, oid = login(TECHNICIAN_A, ORG_A_ID)
        r = get(token, "/hr/payroll/records", oid)
        assert r.status_code in (403, 401), (
            f"Expected 403/401 for technician on /hr/payroll/records, got {r.status_code}"
        )
        body = r.json()
        detail = body.get("detail", "")
        assert "denied" in str(detail).lower() or "role" in str(detail).lower() or r.status_code == 403, (
            f"Expected access-denied message, got: {detail}"
        )

    def test_technician_can_access_tickets(self):
        """Technician must still be able to access tickets (their primary endpoint)."""
        token, oid = login(TECHNICIAN_A, ORG_A_ID)
        r = get(token, "/tickets?per_page=5", oid)
        assert r.status_code == 200, (
            f"Technician should be able to access tickets, got {r.status_code}"
        )

    def test_org_b_admin_cannot_access_org_a_data_with_org_a_id_header(self):
        """Org B admin cannot inject Org A's org ID to access its data."""
        token, _ = login(ADMIN_B, ORG_B_ID)
        # Try to use Org A's org ID in the header while authenticated as Org B
        r = get(token, f"/tickets/{ORG_A_TICKET}", ORG_A_ID)
        assert r.status_code in (403, 401, 404), (
            f"CRITICAL ISOLATION BREACH: Org B user accessed Org A data via header injection. "
            f"Status: {r.status_code}, Body: {r.text[:200]}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 4 — SUBSCRIPTION ENTITLEMENTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEntitlements:
    """Verify subscription plan gating at the API level."""

    def test_free_plan_blocked_from_payroll(self):
        """Free plan org must receive 403 feature_not_available on payroll."""
        token, oid = login(ADMIN_FREE, FREE_ORG_ID)
        r = get(token, "/hr/payroll/records", oid)
        assert r.status_code == 403, (
            f"Expected 403 for free plan on payroll, got {r.status_code}: {r.text[:200]}"
        )
        body = r.json()
        detail = body.get("detail", {})
        assert detail.get("error") == "feature_not_available", (
            f"Expected 'feature_not_available' error, got: {detail}"
        )
        assert detail.get("required_plan") is not None, "required_plan missing from 403 response"
        assert detail.get("current_plan") == "free", (
            f"Expected current_plan='free', got: {detail.get('current_plan')}"
        )

    def test_professional_plan_allowed_payroll(self):
        """Professional plan must access payroll without restriction."""
        token, oid = login(ADMIN_A, ORG_A_ID)
        r = get(token, "/hr/payroll/records", oid)
        assert r.status_code == 200, (
            f"Professional plan should access payroll, got {r.status_code}: {r.text[:200]}"
        )

    def test_starter_plan_blocked_from_payroll(self):
        """Starter plan must also be blocked from payroll (requires Professional)."""
        token, oid = login(ADMIN_B, ORG_B_ID)
        r = get(token, "/hr/payroll/records", oid)
        assert r.status_code == 403, (
            f"Starter plan should be blocked from payroll, got {r.status_code}: {r.text[:200]}"
        )
        detail = r.json().get("detail", {})
        assert detail.get("error") == "feature_not_available"

    def test_starter_plan_allowed_advanced_reports(self):
        """Starter plan should be allowed to access advanced reports (STARTER minimum)."""
        token, oid = login(ADMIN_B, ORG_B_ID)
        r = get(token, "/reports-advanced/summary", oid)
        # 200 or at most a data-not-found 404 is acceptable; 403 is NOT
        assert r.status_code != 403, (
            f"Starter plan should access advanced reports but got 403: {r.text[:200]}"
        )

    def test_free_plan_blocked_from_projects(self):
        """Free plan must be blocked from project management (requires Professional)."""
        token, oid = login(ADMIN_FREE, FREE_ORG_ID)
        r = get(token, "/projects/", oid)
        assert r.status_code == 403, (
            f"Expected 403 for free plan on /projects/, got {r.status_code}: {r.text[:200]}"
        )
        detail = r.json().get("detail", {})
        assert detail.get("error") == "feature_not_available"

    def test_feature_not_available_response_structure(self):
        """403 feature_not_available must include required fields for frontend modal."""
        token, oid = login(ADMIN_FREE, FREE_ORG_ID)
        r = get(token, "/hr/payroll/records", oid)
        assert r.status_code == 403
        detail = r.json().get("detail", {})
        required_fields = ["error", "feature", "feature_key", "current_plan", "required_plan",
                           "message", "upgrade_url"]
        for field in required_fields:
            assert field in detail, (
                f"Missing field '{field}' in 403 response. Got: {list(detail.keys())}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# SUITE 5 — PLATFORM ADMIN
# ═══════════════════════════════════════════════════════════════════════════

class TestPlatformAdmin:
    """Verify platform admin capabilities and isolation."""

    def test_platform_admin_can_list_all_organizations(self):
        """Platform admin must see all registered organizations."""
        token, _ = login(PLATFORM_ADMIN)
        r = get(token, "/platform/organizations?per_page=100")
        assert r.status_code == 200, (
            f"Platform admin /platform/organizations failed: {r.status_code} {r.text[:200]}"
        )
        data = r.json()
        orgs = data.get("organizations", data) if isinstance(data, dict) else data
        org_ids = [o.get("organization_id", "") for o in orgs]
        assert ORG_A_ID in org_ids, f"Org A ({ORG_A_ID}) not found in platform org list"
        assert ORG_B_ID in org_ids, f"Org B ({ORG_B_ID}) not found in platform org list"

    def test_platform_admin_can_change_org_plan(self):
        """Platform admin must be able to change Org B's plan to Professional."""
        token, _ = login(PLATFORM_ADMIN)

        # Upgrade Org B to Professional
        r = post(token, f"/platform/organizations/{ORG_B_ID}/plan",
                 json={"plan_id": "professional"})
        assert r.status_code == 200, (
            f"Plan change failed: {r.status_code} {r.text[:200]}"
        )

        # Verify Org B now has access to payroll
        token_b, oid_b = login(ADMIN_B, ORG_B_ID)
        r2 = get(token_b, "/hr/payroll/records", oid_b)
        assert r2.status_code == 200, (
            f"After upgrade to Professional, Org B should access payroll. Got {r2.status_code}: {r2.text[:200]}"
        )

        # Revert Org B back to Starter
        r3 = post(token, f"/platform/organizations/{ORG_B_ID}/plan",
                  json={"plan_id": "starter"})
        assert r3.status_code == 200, f"Plan revert failed: {r3.status_code}"

    def test_platform_admin_can_suspend_org(self):
        """Platform admin can suspend an org; suspended org logins should fail."""
        token, _ = login(PLATFORM_ADMIN)

        # Suspend Org B
        r = post(token, f"/platform/organizations/{ORG_B_ID}/suspend")
        assert r.status_code == 200, f"Suspend failed: {r.status_code} {r.text[:200]}"

        # Org B admin login should now be blocked (401/403) or have no access
        login_r = requests.post(f"{BASE}/auth/login",
                                json=ADMIN_B, timeout=15)
        # Either login fails or returns a limited token
        if login_r.status_code == 200:
            # If login succeeds, verify tenant access is blocked
            token_b = login_r.json()["token"]
            tickets_r = get(token_b, "/tickets", ORG_B_ID)
            assert tickets_r.status_code in (403, 401, 423), (
                f"Suspended org should not access data. Got {tickets_r.status_code}: {tickets_r.text[:200]}"
            )
        else:
            assert login_r.status_code in (403, 401, 423), (
                f"Expected login blocked for suspended org, got {login_r.status_code}"
            )

        # Re-activate Org B (cleanup)
        r2 = post(token, f"/platform/organizations/{ORG_B_ID}/activate")
        assert r2.status_code == 200, f"Activate failed: {r2.status_code}"

    def test_regular_admin_cannot_access_platform_routes(self):
        """Org admin must NOT be able to access /platform/* routes."""
        token, _ = login(ADMIN_A, ORG_A_ID)
        r = get(token, "/platform/organizations")
        assert r.status_code in (403, 401), (
            f"SECURITY BREACH: Regular org admin accessed platform routes. "
            f"Status: {r.status_code}, Body: {r.text[:200]}"
        )

    def test_platform_admin_org_metrics(self):
        """Platform admin metrics endpoint should return aggregate data."""
        token, _ = login(PLATFORM_ADMIN)
        r = get(token, "/platform/metrics")
        assert r.status_code == 200, f"Platform metrics failed: {r.status_code} {r.text[:200]}"
        data = r.json()
        # Should have org/user counts
        assert any(k in data for k in ["total_organizations", "total_users", "total_orgs"]), (
            f"Metrics response missing org/user counts. Keys: {list(data.keys())}"
        )
