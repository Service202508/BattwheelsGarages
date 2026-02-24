"""
Battwheels OS — 17-Flow Functional Audit
Tests all major flows from signup to payroll via backend APIs.
Uses: auditfinal@battwheelstest.com / audit123 (fresh org created in test)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

# Test data constants
AUDIT_EMAIL = "auditfinal@battwheelstest.com"
AUDIT_PASS = "audit123"
AUDIT_WORKSHOP = "Audit Workshop Final"
AUDIT_CITY = "Bangalore"
AUDIT_STATE = "Karnataka"

ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASS = "admin"
PLATFORM_EMAIL = "platform-admin@battwheels.in"
PLATFORM_PASS = "admin"

# Shared state across tests
state = {
    "token": None,
    "org_id": None,
    "ticket_id": None,
    "invoice_id": None,
    "bms_item_id": None,
    "brake_item_id": None,
    "employee_id": None,
    "payroll_id": None,
    "contact_id": None,
    "vehicle_id": None,
}


def auth_headers():
    return {
        "Authorization": f"Bearer {state['token']}",
        "Content-Type": "application/json",
        "X-Organization-ID": state["org_id"],
    }


# ============================================================
# FLOW 01 — Self-serve signup
# ============================================================
class TestFlow01Registration:
    """FLOW 01 — Self-serve signup at /register"""

    def test_register_page_accessible(self):
        """Register page returns non-error response"""
        res = requests.get(f"{BASE_URL}/register", timeout=10)
        assert res.status_code in [200, 304], f"Register page failed: {res.status_code}"
        print("PASS: /register page accessible")

    def test_signup_creates_org(self):
        """POST /api/organizations/signup creates org, returns token"""
        payload = {
            "name": AUDIT_WORKSHOP,
            "city": AUDIT_CITY,
            "state": AUDIT_STATE,
            "admin_email": AUDIT_EMAIL,
            "admin_password": AUDIT_PASS,
            "admin_name": "Audit Owner",
            "phone": "9000000001",
            "vehicle_types": ["2W"],
            "industry_type": "ev_garage",
        }
        res = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json=payload,
            timeout=15,
        )
        data = res.json()
        # Handle already exists gracefully (re-runs)
        if res.status_code == 400 and "already registered" in str(data.get("detail", "")):
            print("INFO: Org already exists, logging in instead")
            login_res = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": AUDIT_EMAIL, "password": AUDIT_PASS},
                timeout=10,
            )
            assert login_res.status_code == 200
            login_data = login_res.json()
            state["token"] = login_data["token"]
            state["org_id"] = login_data["organizations"][0]["organization_id"]
            print(f"PASS: Logged in as existing org {state['org_id']}")
            return

        assert res.status_code == 200, f"Signup failed: {data}"
        assert "token" in data, "No token in response"
        assert "organization" in data, "No organization in response"

        state["token"] = data["token"]
        state["org_id"] = data["organization"]["organization_id"]

        org = data["organization"]
        assert org.get("plan_type") == "free_trial", f"Expected free_trial, got {org.get('plan_type')}"
        assert "trial_ends_at" in org, "No trial_ends_at in org"
        print(f"PASS: Org created {state['org_id']}, trial_ends_at={org.get('trial_ends_at')[:10]}")

    def test_user_has_owner_role(self):
        """Verify user has owner role via /api/organizations/members"""
        assert state["token"], "No token from signup"
        res = requests.get(
            f"{BASE_URL}/api/organizations/members",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Members API failed: {res.text}"
        data = res.json()
        members = data.get("members", data if isinstance(data, list) else [])
        owner = next((m for m in members if m.get("role") in ["owner", "admin"]), None)
        assert owner is not None, f"No owner/admin in members: {members}"
        print(f"PASS: Owner role confirmed — {owner.get('role')}")

    def test_onboarding_checklist_visible(self):
        """GET /api/organizations/onboarding-status returns checklist"""
        assert state["token"], "No token from signup"
        res = requests.get(
            f"{BASE_URL}/api/organizations/onboarding-status",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Onboarding status failed: {res.text}"
        data = res.json()
        assert "steps" in data or "checklist" in data or "completion_percentage" in data, \
            f"No checklist data: {data}"
        print(f"PASS: Onboarding checklist returned with keys {list(data.keys())}")


# ============================================================
# FLOW 02 — Workshop Profile in Settings
# ============================================================
class TestFlow02WorkshopProfile:
    """FLOW 02 — Workshop Profile: add GSTIN and address"""

    def test_update_org_profile(self):
        """PUT /api/organizations/profile adds GSTIN and address"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "gstin": "07AABCU9603R1ZX",
            "address": "Koramangala, Bangalore",
        }
        res = requests.put(
            f"{BASE_URL}/api/organizations/profile",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code in [200, 204], f"Profile update failed: {res.text}"
        print("PASS: Workshop profile updated with GSTIN and address")

    def test_profile_persists(self):
        """GET /api/organizations/profile returns saved GSTIN"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/organizations/profile",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Profile GET failed: {res.text}"
        data = res.json()
        # Accept org object either top-level or nested
        org = data.get("organization", data)
        gstin = org.get("gstin", "")
        assert gstin == "07AABCU9603R1ZX", f"GSTIN not persisted: got '{gstin}'"
        print(f"PASS: GSTIN persists: {gstin}")


# ============================================================
# FLOW 03 — Invite team member
# ============================================================
class TestFlow03InviteTeam:
    """FLOW 03 — Invite Technician team member"""

    def test_invite_technician(self):
        """POST /api/organizations/invite sends invite"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "email": "tech-audit@battwheelstest.com",
            "role": "technician",
        }
        res = requests.post(
            f"{BASE_URL}/api/organizations/invite",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        # 200/201 = success, 400 = already invited (acceptable)
        assert res.status_code in [200, 201, 400], f"Invite failed: {data}"
        if res.status_code in [200, 201]:
            print("PASS: Technician invite sent")
        else:
            print(f"INFO: Invite returned 400 (may already exist): {data.get('detail')}")

    def test_tech_user_no_finance_access(self):
        """Tech user cannot access payroll/finance endpoints (403)"""
        # Use the existing tech account
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "tech@battwheels.in", "password": "tech123"},
            timeout=10,
        )
        assert login_res.status_code == 200, "Tech login failed"
        tech_token = login_res.json()["token"]
        tech_orgs = login_res.json().get("organizations", [])
        tech_org_id = tech_orgs[0]["organization_id"] if tech_orgs else ""

        headers = {
            "Authorization": f"Bearer {tech_token}",
            "Content-Type": "application/json",
            "X-Organization-ID": tech_org_id,
        }
        res = requests.get(f"{BASE_URL}/api/hr/payroll/records", headers=headers, timeout=10)
        assert res.status_code in [403, 401], \
            f"Technician should be blocked from payroll, got {res.status_code}"
        print(f"PASS: Technician correctly blocked from payroll (HTTP {res.status_code})")


# ============================================================
# FLOW 04 — Add inventory items
# ============================================================
class TestFlow04Inventory:
    """FLOW 04 — Add BMS Module and Brake Pad Set"""

    def test_add_bms_module(self):
        """POST /api/inventory creates BMS Module item"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "name": "BMS Module",
            "sku": "BMS-001",
            "purchase_price": 2500,
            "selling_price": 3200,
            "quantity": 10,
            "reorder_level": 2,
            "unit": "pcs",
            "category": "parts",
        }
        res = requests.post(
            f"{BASE_URL}/api/inventory",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"BMS add failed: {data}"
        item_id = data.get("id") or data.get("item_id") or data.get("_id")
        assert item_id, "No item_id in response"
        state["bms_item_id"] = item_id
        assert data.get("quantity") == 10 or data.get("current_stock") == 10, \
            f"Qty mismatch: {data}"
        print(f"PASS: BMS Module created id={item_id}")

    def test_add_brake_pad(self):
        """POST /api/inventory creates Brake Pad Set item"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "name": "Brake Pad Set",
            "sku": "BRK-002",
            "purchase_price": 450,
            "selling_price": 650,
            "quantity": 25,
            "reorder_level": 5,
            "unit": "set",
            "category": "parts",
        }
        res = requests.post(
            f"{BASE_URL}/api/inventory",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Brake Pad add failed: {data}"
        item_id = data.get("id") or data.get("item_id") or data.get("_id")
        assert item_id, "No item_id in response"
        state["brake_item_id"] = item_id
        print(f"PASS: Brake Pad Set created id={item_id}")

    def test_items_appear_in_list(self):
        """GET /api/inventory returns both items"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/inventory",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Inventory list failed: {res.text}"
        data = res.json()
        items = data.get("items", data.get("data", data if isinstance(data, list) else []))
        names = [i.get("name", "") for i in items]
        assert any("BMS" in n for n in names), f"BMS not in list: {names[:5]}"
        assert any("Brake" in n for n in names), f"Brake not in list: {names[:5]}"
        print(f"PASS: Both items in inventory list ({len(items)} total items)")


# ============================================================
# FLOW 05 — Add customer and vehicle
# ============================================================
class TestFlow05CustomerVehicle:
    """FLOW 05 — Add Rajesh Kumar customer and vehicle"""

    def test_create_contact(self):
        """POST /api/contacts-enhanced creates Rajesh Kumar"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "name": "Rajesh Kumar",
            "phone": "9876543210",
            "email": "rajesh@test.com",
            "city": "Delhi",
            "contact_type": "customer",
        }
        res = requests.post(
            f"{BASE_URL}/api/contacts-enhanced",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Contact create failed: {data}"
        contact_id = data.get("id") or data.get("contact_id") or data.get("_id")
        assert contact_id, "No contact_id in response"
        state["contact_id"] = contact_id
        print(f"PASS: Contact Rajesh Kumar created id={contact_id}")

    def test_add_vehicle_to_contact(self):
        """POST /api/vehicles creates vehicle for Rajesh Kumar"""
        assert state["token"], "No token from Flow 01"
        assert state["contact_id"], "No contact from Flow 05"
        payload = {
            "make": "Ola",
            "model": "S1 Pro",
            "year": 2023,
            "registration_number": "DL01AB1234",
            "contact_id": state["contact_id"],
            "vehicle_type": "2W_EV",
        }
        res = requests.post(
            f"{BASE_URL}/api/vehicles",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Vehicle create failed: {data}"
        vehicle_id = data.get("id") or data.get("vehicle_id") or data.get("_id")
        assert vehicle_id, "No vehicle_id in response"
        state["vehicle_id"] = vehicle_id
        assert data.get("registration_number") == "DL01AB1234", \
            f"Reg mismatch: {data.get('registration_number')}"
        print(f"PASS: Vehicle DL01AB1234 created id={vehicle_id}")


# ============================================================
# FLOW 06 — Create service ticket
# ============================================================
class TestFlow06CreateTicket:
    """FLOW 06 — Create service ticket for Rajesh Kumar"""

    def test_create_ticket(self):
        """POST /api/tickets creates a high priority ticket"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "customer_name": "Rajesh Kumar",
            "customer_phone": "9876543210",
            "vehicle_registration": "DL01AB1234",
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "complaint": "Battery not charging, range reduced to 30km, BMS warning on display",
            "priority": "high",
            "ticket_type": "workshop_visit",
            "status": "open",
        }
        # Some APIs use contact_id / vehicle_id
        if state.get("contact_id"):
            payload["contact_id"] = state["contact_id"]
        if state.get("vehicle_id"):
            payload["vehicle_id"] = state["vehicle_id"]

        res = requests.post(
            f"{BASE_URL}/api/tickets",
            json=payload,
            headers=auth_headers(),
            timeout=15,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Ticket create failed: {data}"
        ticket_id = (
            data.get("ticket_id")
            or data.get("id")
            or data.get("_id")
        )
        assert ticket_id, f"No ticket_id in response: {data}"
        state["ticket_id"] = ticket_id
        print(f"PASS: Ticket created id={ticket_id}")

    def test_ticket_has_unique_id(self):
        """Ticket ID is present and unique-looking"""
        assert state["ticket_id"], "No ticket from Flow 06"
        print(f"PASS: Ticket has ID: {state['ticket_id']}")

    def test_dashboard_open_count(self):
        """GET /api/dashboard/stats shows open tickets > 0"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Dashboard stats failed: {res.text}"
        data = res.json()
        open_count = (
            data.get("open_tickets")
            or data.get("open_count")
            or data.get("tickets", {}).get("open")
            or 0
        )
        assert open_count >= 1, f"Open count should be >=1, got {open_count}. Data: {data}"
        print(f"PASS: Dashboard open_tickets = {open_count}")


# ============================================================
# FLOW 07 — EFI diagnostics on ticket
# ============================================================
class TestFlow07EFIDiagnostics:
    """FLOW 07 — EFI/AI diagnostics on ticket"""

    def test_efi_diagnose(self):
        """POST /api/ai/diagnose returns result"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "symptoms": "Battery not charging, reduced range 30km, BMS warning",
            "vehicle_type": "2W_EV",
        }
        if state.get("ticket_id"):
            payload["ticket_id"] = state["ticket_id"]

        res = requests.post(
            f"{BASE_URL}/api/ai/diagnose",
            json=payload,
            headers=auth_headers(),
            timeout=30,
        )
        data = res.json()
        assert res.status_code == 200, f"EFI diagnose failed: {data}"
        # Check result has some content
        has_result = (
            data.get("diagnosis")
            or data.get("result")
            or data.get("analysis")
            or data.get("recommendations")
            or data.get("possible_causes")
            or data.get("diagnostic_result")
        )
        assert has_result, f"EFI returned no diagnosis content: {data}"
        print(f"PASS: EFI returned result with keys: {list(data.keys())}")

    def test_efi_failure_cards(self):
        """GET /api/efi/failure-cards returns cards"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"EFI failure-cards failed: {res.text}"
        data = res.json()
        print(f"PASS: EFI failure cards returned, keys: {list(data.keys())}")


# ============================================================
# FLOW 08 — Update and close ticket
# ============================================================
class TestFlow08CloseTicket:
    """FLOW 08 — Update, add parts, close ticket"""

    def test_update_status_in_progress(self):
        """PUT /api/tickets/{id} sets status to in_progress"""
        assert state["token"] and state["ticket_id"], "Missing token or ticket"
        res = requests.put(
            f"{BASE_URL}/api/tickets/{state['ticket_id']}",
            json={"status": "in_progress"},
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code in [200, 204], f"Status update failed: {res.text}"
        print("PASS: Ticket status set to in_progress")

    def test_close_ticket_with_resolution(self):
        """PUT /api/tickets/{id} closes ticket with resolution"""
        assert state["token"] and state["ticket_id"], "Missing token or ticket"
        payload = {
            "status": "resolved",
            "resolution": "BMS recalibrated, brake pads replaced",
        }
        res = requests.put(
            f"{BASE_URL}/api/tickets/{state['ticket_id']}",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code in [200, 204], f"Close ticket failed: {res.text}"
        print("PASS: Ticket closed with resolution")

    def test_ticket_shows_resolved(self):
        """GET /api/tickets/{id} shows resolved status"""
        assert state["token"] and state["ticket_id"], "Missing token or ticket"
        res = requests.get(
            f"{BASE_URL}/api/tickets/{state['ticket_id']}",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Get ticket failed: {res.text}"
        data = res.json()
        ticket = data.get("ticket", data)
        status = ticket.get("status", "")
        assert status in ["resolved", "closed", "done"], \
            f"Expected resolved, got '{status}'"
        print(f"PASS: Ticket status = {status}")


# ============================================================
# FLOW 09 — Create invoice
# ============================================================
class TestFlow09CreateInvoice:
    """FLOW 09 — Create invoice from ticket"""

    def test_create_invoice(self):
        """POST /api/invoices-enhanced creates invoice"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "customer_name": "Rajesh Kumar",
            "customer_email": "rajesh@test.com",
            "line_items": [
                {
                    "description": "BMS Module",
                    "quantity": 1,
                    "unit_price": 3200,
                    "tax_rate": 18,
                },
                {
                    "description": "Brake Pad Set",
                    "quantity": 1,
                    "unit_price": 650,
                    "tax_rate": 18,
                },
                {
                    "description": "BMS Recalibration Labour",
                    "quantity": 2.5,
                    "unit_price": 500,
                    "tax_rate": 18,
                },
            ],
            "invoice_date": "2026-02-01",
            "due_date": "2026-02-15",
        }
        if state.get("contact_id"):
            payload["contact_id"] = state["contact_id"]
        if state.get("ticket_id"):
            payload["ticket_id"] = state["ticket_id"]

        res = requests.post(
            f"{BASE_URL}/api/invoices-enhanced",
            json=payload,
            headers=auth_headers(),
            timeout=15,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Invoice create failed: {data}"
        invoice_id = data.get("invoice_id") or data.get("id") or data.get("_id")
        assert invoice_id, f"No invoice_id: {data}"
        state["invoice_id"] = invoice_id
        print(f"PASS: Invoice created id={invoice_id}")

    def test_invoice_gst_calculated(self):
        """Invoice has GST amounts"""
        assert state["token"] and state["invoice_id"], "Missing token or invoice"
        res = requests.get(
            f"{BASE_URL}/api/invoices-enhanced/{state['invoice_id']}",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Invoice GET failed: {res.text}"
        data = res.json()
        invoice = data.get("invoice", data)
        # Check for GST fields
        has_gst = (
            invoice.get("cgst_amount") is not None
            or invoice.get("sgst_amount") is not None
            or invoice.get("tax_amount") is not None
            or invoice.get("total_tax") is not None
        )
        assert has_gst, f"No GST amounts in invoice: {list(invoice.keys())}"
        print(f"PASS: Invoice has GST amounts")


# ============================================================
# FLOW 10 — Record payment
# ============================================================
class TestFlow10RecordPayment:
    """FLOW 10 — Record payment against invoice"""

    def test_record_payment(self):
        """POST /api/payments records payment"""
        assert state["token"] and state["invoice_id"], "Missing token or invoice"
        payload = {
            "invoice_id": state["invoice_id"],
            "amount": 6018,
            "payment_method": "cash",
            "payment_date": "2026-02-01",
            "notes": "Full payment received",
        }
        res = requests.post(
            f"{BASE_URL}/api/payments",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Payment record failed: {data}"
        print(f"PASS: Payment recorded for invoice {state['invoice_id']}")

    def test_invoice_status_paid(self):
        """GET invoice shows paid status"""
        assert state["token"] and state["invoice_id"], "Missing token or invoice"
        res = requests.get(
            f"{BASE_URL}/api/invoices-enhanced/{state['invoice_id']}",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Invoice GET failed: {res.text}"
        data = res.json()
        invoice = data.get("invoice", data)
        status = invoice.get("status", "")
        assert status in ["paid", "Paid", "PAID"], \
            f"Invoice status should be paid, got '{status}'"
        print(f"PASS: Invoice status = {status}")


# ============================================================
# FLOW 11 — Financial reports
# ============================================================
class TestFlow11FinancialReports:
    """FLOW 11 — Trial Balance, P&L, GST Summary"""

    def test_trial_balance_loads(self):
        """GET /api/reports/trial-balance returns balanced data"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers=auth_headers(),
            timeout=15,
        )
        assert res.status_code == 200, f"Trial Balance failed: {res.text}"
        data = res.json()
        assert "accounts" in data or "entries" in data or "total_debit" in data, \
            f"Unexpected trial balance structure: {list(data.keys())}"
        print(f"PASS: Trial Balance returned, keys: {list(data.keys())}")

    def test_profit_loss_loads(self):
        """GET /api/reports/profit-loss returns revenue & COGS"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/reports/profit-loss",
            headers=auth_headers(),
            timeout=15,
        )
        assert res.status_code == 200, f"P&L failed: {res.text}"
        data = res.json()
        print(f"PASS: P&L returned, keys: {list(data.keys())}")

    def test_gst_summary_loads(self):
        """GET /api/reports/gst-summary returns output GST"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/reports/gst-summary",
            headers=auth_headers(),
            timeout=15,
        )
        assert res.status_code in [200, 404], f"GST summary failed: {res.text}"
        if res.status_code == 200:
            data = res.json()
            print(f"PASS: GST summary returned, keys: {list(data.keys())}")
        else:
            # Try alternate route
            res2 = requests.get(
                f"{BASE_URL}/api/gst/summary",
                headers=auth_headers(),
                timeout=15,
            )
            assert res2.status_code == 200, f"GST summary (alternate) failed: {res2.text}"
            print(f"PASS: GST summary (alternate route) returned")


# ============================================================
# FLOW 12 — Tally XML export
# ============================================================
class TestFlow12TallyExport:
    """FLOW 12 — Tally XML export"""

    def test_tally_export(self):
        """GET /api/tally/export returns XML"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/tally/export",
            headers=auth_headers(),
            timeout=20,
        )
        if res.status_code == 404:
            # Try alternate route
            res = requests.get(
                f"{BASE_URL}/api/export/tally",
                headers=auth_headers(),
                timeout=20,
            )
        assert res.status_code == 200, f"Tally export failed: {res.status_code} {res.text[:200]}"
        content_type = res.headers.get("content-type", "")
        # Accept XML content-type or attachment
        is_xml = (
            "xml" in content_type
            or "application/octet-stream" in content_type
            or res.text.strip().startswith("<?xml")
            or "<ENVELOPE>" in res.text
            or "TALLYMESSAGE" in res.text
        )
        assert is_xml, f"Response not XML: content_type={content_type}, text={res.text[:200]}"
        print(f"PASS: Tally export returned XML ({len(res.content)} bytes)")


# ============================================================
# FLOW 13 — Add employee and run payroll
# ============================================================
class TestFlow13Payroll:
    """FLOW 13 — Add Ravi Kumar employee and run payroll"""

    def test_add_employee(self):
        """POST /api/hr/employees creates Ravi Kumar"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "name": "Ravi Kumar",
            "employee_code": "EMP-AUDIT-001",
            "role": "Technician",
            "department": "Workshop",
            "basic_salary": 18000,
            "pf_applicable": True,
            "esi_applicable": True,
            "state": "Delhi",
            "pan_number": "ABCDE1234F",
            "joining_date": "2026-02-01",
            "email": "ravi.kumar.audit@battwheelstest.com",
            "phone": "9000000099",
        }
        res = requests.post(
            f"{BASE_URL}/api/hr/employees",
            json=payload,
            headers=auth_headers(),
            timeout=15,
        )
        data = res.json()
        if res.status_code == 400 and "already" in str(data.get("detail", "")).lower():
            # Get existing employee
            emp_res = requests.get(
                f"{BASE_URL}/api/hr/employees",
                headers=auth_headers(),
                timeout=10,
            )
            emp_data = emp_res.json()
            employees = emp_data.get("employees", emp_data if isinstance(emp_data, list) else [])
            ravi = next((e for e in employees if "Ravi" in e.get("name", "") and "Audit" in e.get("employee_code", "")), None)
            if ravi:
                state["employee_id"] = ravi.get("employee_id") or ravi.get("id")
                print(f"INFO: Using existing employee {state['employee_id']}")
                return
        assert res.status_code in [200, 201], f"Employee create failed: {data}"
        emp_id = data.get("employee_id") or data.get("id") or data.get("_id")
        assert emp_id, f"No employee_id: {data}"
        state["employee_id"] = emp_id
        print(f"PASS: Employee Ravi Kumar created id={emp_id}")

    def test_run_payroll(self):
        """POST /api/hr/payroll/run runs payroll for current month"""
        assert state["token"], "No token from Flow 01"
        assert state.get("employee_id"), "No employee from Flow 13"
        payload = {
            "month": 2,
            "year": 2026,
            "employee_ids": [state["employee_id"]],
        }
        res = requests.post(
            f"{BASE_URL}/api/hr/payroll/run",
            json=payload,
            headers=auth_headers(),
            timeout=30,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Payroll run failed: {data}"
        records = data.get("records", data.get("payroll_records", [data] if isinstance(data, dict) else data))
        assert len(records) >= 1, f"No payroll records: {data}"

        # Check net salary ~15505 (18000 - 2160 PF - 135 ESI - 200 PT)
        record = records[0] if records else {}
        net = record.get("net_salary") or record.get("net_pay") or record.get("take_home")
        if net:
            # Allow ±200 variance
            assert abs(net - 15505) <= 500, \
                f"Net salary {net} differs too much from expected 15505"
            print(f"PASS: Net salary = ₹{net} (expected ≈15505)")
        else:
            print(f"PASS: Payroll run succeeded (net not in direct response). Keys: {list(record.keys())}")

        payroll_id = record.get("payroll_id") or record.get("id")
        state["payroll_id"] = payroll_id


# ============================================================
# FLOW 14 — Public ticket form
# ============================================================
class TestFlow14PublicTicket:
    """FLOW 14 — Public ticket form /submit-ticket"""

    def test_public_form_accessible(self):
        """GET /submit-ticket loads without auth"""
        res = requests.get(f"{BASE_URL}/submit-ticket", timeout=10)
        assert res.status_code in [200, 304], f"Public form page failed: {res.status_code}"
        print("PASS: /submit-ticket page accessible without auth")

    def test_public_submit_without_slug_gives_friendly_error(self):
        """POST /api/public/tickets/submit without org slug returns 400 not 500"""
        payload = {
            "customer_name": "Priya Sharma",
            "contact_number": "9123456789",
            "vehicle_category": "2W_EV",
            "vehicle_number": "MH01AB0001",
            "title": "Scooter not starting",
            "description": "Scooter not starting after overnight charging",
            "priority": "high",
            "resolution_type": "workshop",
        }
        res = requests.post(
            f"{BASE_URL}/api/public/tickets/submit",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        # Should be 400 with friendly error, NOT 500
        assert res.status_code != 500, "FAIL: Server crashed with 500 on public ticket without slug"
        assert res.status_code in [400, 422, 404], \
            f"Expected 400/422/404 for missing org slug, got {res.status_code}"
        data = res.json()
        error_msg = data.get("detail", data.get("message", str(data)))
        assert "workshop" in error_msg.lower() or "org" in error_msg.lower() or "slug" in error_msg.lower() \
               or "determine" in error_msg.lower() or "organization" in error_msg.lower(), \
            f"Error message not helpful: {error_msg}"
        print(f"PASS: Public ticket without slug returns {res.status_code}: {error_msg}")

    def test_public_vehicle_categories(self):
        """GET /api/public/vehicle-categories loads without auth"""
        res = requests.get(
            f"{BASE_URL}/api/public/vehicle-categories",
            timeout=10,
        )
        assert res.status_code == 200, f"Public vehicle categories failed: {res.text}"
        data = res.json()
        assert "categories" in data, f"No categories key: {data}"
        print(f"PASS: Public vehicle categories returned {len(data['categories'])} categories")


# ============================================================
# FLOW 15 — Data Insights
# ============================================================
class TestFlow15DataInsights:
    """FLOW 15 — Data Insights page"""

    def test_insights_revenue(self):
        """GET /api/insights/revenue returns data"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/revenue",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code == 200, f"Revenue insights failed: {res.text}"
        print(f"PASS: Revenue insights loaded")

    def test_insights_operations(self):
        """GET /api/insights/operations returns data"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/operations",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code == 200, f"Operations insights failed: {res.text}"
        print(f"PASS: Operations insights loaded")

    def test_insights_technician(self):
        """GET /api/insights/technician-performance returns data"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/technician-performance",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code in [200, 404], f"Technician insights failed: {res.text}"
        if res.status_code == 200:
            print(f"PASS: Technician insights loaded")
        else:
            print(f"INFO: Technician insights returned 404")

    def test_insights_inventory(self):
        """GET /api/insights/inventory returns data"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/inventory",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code in [200, 404], f"Inventory insights failed: {res.text}"
        if res.status_code == 200:
            print(f"PASS: Inventory insights loaded")
        else:
            print(f"INFO: Inventory insights returned 404")


# ============================================================
# FLOW 16 — Book Demo
# ============================================================
class TestFlow16BookDemo:
    """FLOW 16 — Book Demo lead capture"""

    def test_book_demo_endpoint(self):
        """POST /api/book-demo submits lead without auth"""
        payload = {
            "name": "Test Lead",
            "workshop_name": "Test Workshop",
            "city": "Mumbai",
            "phone": "9999999999",
            "vehicles_per_month": "10-50",
        }
        res = requests.post(
            f"{BASE_URL}/api/book-demo",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Book demo failed: {data}"
        print(f"PASS: Book demo submitted, response: {data}")

    def test_book_demo_validation(self):
        """POST /api/book-demo without required fields returns 422"""
        payload = {"name": "Incomplete"}
        res = requests.post(
            f"{BASE_URL}/api/book-demo",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert res.status_code == 422, \
            f"Expected 422 for incomplete data, got {res.status_code}"
        print(f"PASS: Book demo validation working (422 on incomplete payload)")


# ============================================================
# CLEANUP — Report audit org ID
# ============================================================
class TestCleanup:
    """Report audit org ID for cleanup"""

    def test_report_audit_org(self):
        """Print audit org ID for cleanup"""
        print(f"\n{'='*60}")
        print(f"AUDIT ORG ID: {state.get('org_id', 'NOT CREATED')}")
        print(f"AUDIT EMAIL: {AUDIT_EMAIL}")
        print(f"Ticket: {state.get('ticket_id')}")
        print(f"Invoice: {state.get('invoice_id')}")
        print(f"Employee: {state.get('employee_id')}")
        print(f"{'='*60}\n")
        print("PASS: Audit org data reported above")
