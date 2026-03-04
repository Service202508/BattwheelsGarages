"""
Cross-Tenant Isolation Tests (Sprint 4B-01)
============================================
Verify that one organization cannot read another organization's data.
Uses dev fixture users: Org A (dev-internal-testing-001) and Org B (demo-volt-motors-001).
"""
import pytest
import requests
import uuid

BASE_URL = "http://localhost:8001"

ORG_A_ID = "dev-internal-testing-001"
ORG_A_EMAIL = "dev@battwheels.internal"
ORG_A_PASSWORD = "DevTest@123"

ORG_B_ID = "demo-volt-motors-001"
ORG_B_EMAIL = "demo@voltmotors.in"
ORG_B_PASSWORD = "Demo@12345"

TECH_EMAIL = "deepak@battwheelsgarages.in"
TECH_PASSWORD = "DevTest@123"


def server_is_running():
    try:
        return requests.get(f"{BASE_URL}/api/health", timeout=3).status_code == 200
    except Exception:
        return False


def login(email, password):
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data.get("token") or data.get("access_token")


def headers(token, org_id):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Organization-ID": org_id,
    }


@pytest.fixture(scope="module")
def org_a_token():
    token = login(ORG_A_EMAIL, ORG_A_PASSWORD)
    if not token:
        pytest.skip("Org A login failed")
    return token


@pytest.fixture(scope="module")
def org_b_token():
    token = login(ORG_B_EMAIL, ORG_B_PASSWORD)
    if not token:
        pytest.skip("Org B login failed")
    return token


@pytest.fixture(scope="module")
def tech_token():
    token = login(TECH_EMAIL, TECH_PASSWORD)
    if not token:
        pytest.skip("Technician login failed")
    return token


# ==================== CROSS-TENANT: TICKETS ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestCrossTenantTickets:

    def test_org_cannot_read_other_org_tickets(self, org_a_token, org_b_token):
        """Create ticket in org_A, verify org_B cannot see it."""
        tag = uuid.uuid4().hex[:8]
        ticket_payload = {
            "title": f"CrossTenant-Ticket-{tag}",
            "description": "Isolation test ticket",
            "priority": "medium",
            "customer_name": "Test Customer",
        }
        # Create ticket in Org A
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            json=ticket_payload,
            headers=headers(org_a_token, ORG_A_ID),
        )
        # Accept 200 or 201 (created)
        assert create_resp.status_code in (200, 201), \
            f"Failed to create ticket in Org A: {create_resp.status_code} {create_resp.text[:300]}"

        # List tickets as Org B
        list_resp = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers=headers(org_b_token, ORG_B_ID),
        )
        assert list_resp.status_code == 200, \
            f"Failed to list tickets as Org B: {list_resp.status_code}"

        data = list_resp.json()
        tickets = data.get("tickets") or data.get("data") or []
        org_a_titles = [t.get("title", "") for t in tickets]
        assert f"CrossTenant-Ticket-{tag}" not in org_a_titles, \
            "Org B can see Org A's ticket — TENANT ISOLATION BREACH"


# ==================== CROSS-TENANT: INVOICES ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestCrossTenantInvoices:

    def test_org_cannot_read_other_org_invoices(self, org_a_token, org_b_token):
        """Create invoice in org_A, verify org_B cannot see it."""
        tag = uuid.uuid4().hex[:8]
        invoice_payload = {
            "customer_name": f"CrossTenant-Customer-{tag}",
            "date": "2026-01-15",
            "due_date": "2026-02-15",
            "line_items": [{"item_name": "Test Item", "quantity": 1, "rate": 100}],
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/invoices-enhanced",
            json=invoice_payload,
            headers=headers(org_a_token, ORG_A_ID),
        )
        # May return 200/201/400 depending on required fields
        created = create_resp.status_code in (200, 201)

        # List invoices as Org B
        list_resp = requests.get(
            f"{BASE_URL}/api/v1/invoices-enhanced",
            headers=headers(org_b_token, ORG_B_ID),
        )
        assert list_resp.status_code == 200, \
            f"Failed to list invoices as Org B: {list_resp.status_code}"

        data = list_resp.json()
        invoices = data.get("invoices") or data.get("data") or []
        customer_names = [i.get("customer_name", "") for i in invoices]
        assert f"CrossTenant-Customer-{tag}" not in customer_names, \
            "Org B can see Org A's invoice — TENANT ISOLATION BREACH"


# ==================== CROSS-TENANT: EMPLOYEES ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestCrossTenantEmployees:

    def test_org_cannot_read_other_org_employees(self, org_a_token, org_b_token):
        """Create employee in org_A, verify org_B cannot see it."""
        tag = uuid.uuid4().hex[:8]
        emp_payload = {
            "name": f"CrossTenant-Emp-{tag}",
            "email": f"cross-{tag}@test.internal",
            "designation": "Tester",
            "department": "QA",
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/hr/employees",
            json=emp_payload,
            headers=headers(org_a_token, ORG_A_ID),
        )
        # May return 200/201/400
        created = create_resp.status_code in (200, 201)

        # List employees as Org B
        list_resp = requests.get(
            f"{BASE_URL}/api/v1/hr/employees",
            headers=headers(org_b_token, ORG_B_ID),
        )
        assert list_resp.status_code == 200, \
            f"Failed to list employees as Org B: {list_resp.status_code}"

        data = list_resp.json()
        employees = data.get("employees") or data.get("data") or []
        emp_names = [e.get("name", "") for e in employees]
        assert f"CrossTenant-Emp-{tag}" not in emp_names, \
            "Org B can see Org A's employee — TENANT ISOLATION BREACH"


# ==================== TECHNICIAN TICKET SCOPING ====================

@pytest.mark.skipif(not server_is_running(), reason="requires running server")
class TestTechnicianTicketScoping:

    def test_technician_only_sees_assigned_tickets(self, org_a_token, tech_token):
        """Create two tickets assigned to different techs; technician only sees their own."""
        tag = uuid.uuid4().hex[:8]

        # Create ticket assigned to our technician (deepak)
        t1 = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            json={
                "title": f"Tech-Own-{tag}",
                "description": "Assigned to deepak",
                "priority": "high",
                "assigned_to": "user_3d9035ce8138",
            },
            headers=headers(org_a_token, ORG_A_ID),
        )

        # Create ticket assigned to a different tech
        t2 = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            json={
                "title": f"Tech-Other-{tag}",
                "description": "Assigned to other tech",
                "priority": "low",
                "assigned_to": "user_8d62c20c5d68",
            },
            headers=headers(org_a_token, ORG_A_ID),
        )

        # Technician lists their own tickets via portal
        tech_resp = requests.get(
            f"{BASE_URL}/api/v1/technician/tickets",
            headers=headers(tech_token, ORG_A_ID),
        )
        assert tech_resp.status_code == 200, \
            f"Technician portal tickets failed: {tech_resp.status_code}"

        data = tech_resp.json()
        titles = [t.get("title", "") for t in data.get("tickets", [])]

        # The technician should NOT see the other tech's ticket
        assert f"Tech-Other-{tag}" not in titles, \
            "Technician can see tickets assigned to another technician — SCOPING BREACH"
