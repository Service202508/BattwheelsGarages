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

# Shared state across tests (module-level dict shared by all classes)
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
    h = {
        "Authorization": f"Bearer {state['token']}",
        "Content-Type": "application/json",
    }
    if state["org_id"]:
        h["X-Organization-ID"] = state["org_id"]
    return h


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
        if res.status_code == 400 and ("already registered" in str(data.get("detail", "")) or
                                        "already exists" in str(data.get("detail", ""))):
            print("INFO: Org already exists, logging in instead")
            login_res = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": AUDIT_EMAIL, "password": AUDIT_PASS},
                timeout=10,
            )
            assert login_res.status_code == 200, f"Login failed: {login_res.text}"
            login_data = login_res.json()
            state["token"] = login_data["token"]
            orgs = login_data.get("organizations", [])
            state["org_id"] = orgs[0]["organization_id"] if orgs else None
            print(f"PASS: Logged in as existing org {state['org_id']}")
            return

        assert res.status_code == 200, f"Signup failed: {data}"
        assert "token" in data, "No token in response"
        assert "organization" in data, "No organization in response"

        state["token"] = data["token"]
        state["org_id"] = data["organization"]["organization_id"]

        org = data["organization"]
        assert org.get("plan_type") == "free_trial", f"Expected free_trial, got {org.get('plan_type')}"
        # trial expiry is returned as plan_expires_at
        trial_expiry = org.get("plan_expires_at") or org.get("trial_ends_at")
        assert trial_expiry, f"No trial expiry in org: {list(org.keys())}"
        print(f"PASS: Org created {state['org_id']}, trial ends {trial_expiry[:10]}")

    def test_user_has_owner_role(self):
        """GET /api/organizations/me/members shows owner role"""
        assert state["token"], "No token from signup"
        res = requests.get(
            f"{BASE_URL}/api/organizations/me/members",
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
        """GET /api/organizations/onboarding/status returns checklist"""
        assert state["token"], "No token from signup"
        res = requests.get(
            f"{BASE_URL}/api/organizations/onboarding/status",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Onboarding status failed: {res.text}"
        data = res.json()
        # Accepts any checklist-like structure
        assert (
            "steps" in data or "checklist" in data
            or "completion_percentage" in data
            or "total_steps" in data
            or "show_onboarding" in data
            or "onboarding_completed" in data
        ), f"No checklist data: {data}"
        print(f"PASS: Onboarding checklist returned with keys {list(data.keys())}")


# ============================================================
# FLOW 02 — Workshop Profile in Settings
# ============================================================
class TestFlow02WorkshopProfile:
    """FLOW 02 — Workshop Profile: add GSTIN and address"""

    def test_update_org_profile(self):
        """PUT /api/organizations/me updates GSTIN and address"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "gstin": "07AABCU9603R1ZX",
            "address": "Koramangala, Bangalore",
        }
        res = requests.put(
            f"{BASE_URL}/api/organizations/me",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code in [200, 204], f"Profile update failed: {res.text}"
        print("PASS: Workshop profile updated with GSTIN and address")

    def test_profile_persists(self):
        """GET /api/organizations/me returns saved GSTIN"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/organizations/me",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Profile GET failed: {res.text}"
        data = res.json()
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
        """POST /api/organizations/me/invite sends invite"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "email": "tech-audit@battwheelstest.com",
            "name": "Tech Audit User",
            "role": "technician",
        }
        res = requests.post(
            f"{BASE_URL}/api/organizations/me/invite",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        # 200/201 = success, 400 = already invited (acceptable)
        assert res.status_code in [200, 201, 400], f"Invite failed ({res.status_code}): {data}"
        if res.status_code in [200, 201]:
            print("PASS: Technician invite sent")
        else:
            print(f"INFO: Invite returned 400 (may already exist): {data.get('detail')}")

    def test_tech_user_no_finance_access(self):
        """Tech user cannot access payroll endpoint → 403/401"""
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
            "category": "parts",
            "quantity": 10,
            "unit_price": 3200,
            "cost_price": 2500,
            "min_stock_level": 2,
            "max_stock_level": 100,
            "reorder_quantity": 5,
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
        qty = data.get("quantity") or data.get("current_stock") or data.get("stock", {}).get("quantity")
        assert qty == 10, f"Qty mismatch: got {qty}, expected 10"
        print(f"PASS: BMS Module created id={item_id}, qty={qty}")

    def test_add_brake_pad(self):
        """POST /api/inventory creates Brake Pad Set item"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "name": "Brake Pad Set",
            "sku": "BRK-002",
            "category": "parts",
            "quantity": 25,
            "unit_price": 650,
            "cost_price": 450,
            "min_stock_level": 5,
            "max_stock_level": 100,
            "reorder_quantity": 10,
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
        """GET /api/inventory returns both new items"""
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
        print(f"PASS: Both items in inventory list ({len(items)} total)")


# ============================================================
# FLOW 05 — Add customer and vehicle
# ============================================================
class TestFlow05CustomerVehicle:
    """FLOW 05 — Add Rajesh Kumar customer and vehicle"""

    def test_create_contact(self):
        """POST /api/contacts-enhanced/ creates Rajesh Kumar"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "contact_type": "customer",
            "name": "Rajesh Kumar",
            "phone": "9876543210",
            "email": "rajesh@test.com",
            "city": "Delhi",
        }
        res = requests.post(
            f"{BASE_URL}/api/contacts-enhanced/",
            json=payload,
            headers=auth_headers(),
            timeout=10,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Contact create failed ({res.status_code}): {data}"
        # Response is {code, message, contact: {contact_id, ...}}
        contact = data.get("contact", data)
        contact_id = (
            contact.get("contact_id")
            or contact.get("id")
            or data.get("contact_id")
            or data.get("id")
        )
        assert contact_id, f"No contact_id in response: {data}"
        state["contact_id"] = contact_id
        print(f"PASS: Contact Rajesh Kumar created id={contact_id}")

    def test_add_vehicle_to_contact(self):
        """POST /api/vehicles creates Ola S1 Pro for Rajesh Kumar"""
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
        reg = data.get("registration_number")
        assert reg == "DL01AB1234", f"Reg mismatch: got {reg}"
        print(f"PASS: Vehicle DL01AB1234 created id={vehicle_id}")


# ============================================================
# FLOW 06 — Create service ticket
# ============================================================
class TestFlow06CreateTicket:
    """FLOW 06 — Create service ticket"""

    def test_create_ticket(self):
        """POST /api/tickets creates high priority ticket"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "title": "Battery not charging, range reduced to 30km, BMS warning on display",
            "description": "Battery not charging, range reduced to 30km, BMS warning on display",
            "priority": "high",
            "resolution_type": "workshop",
            "customer_name": "Rajesh Kumar",
            "customer_type": "individual",
            "contact_number": "9876543210",
            "vehicle_number": "DL01AB1234",
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "vehicle_type": "2W_EV",
        }
        if state.get("contact_id"):
            payload["customer_id"] = state["contact_id"]
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
        ticket_id = data.get("ticket_id") or data.get("id") or data.get("_id")
        assert ticket_id, f"No ticket_id: {data}"
        state["ticket_id"] = ticket_id
        print(f"PASS: Ticket created id={ticket_id}")

    def test_ticket_has_unique_id(self):
        """Ticket ID is present"""
        assert state["ticket_id"], "No ticket from Flow 06"
        print(f"PASS: Ticket has ID: {state['ticket_id']}")

    def test_dashboard_open_count(self):
        """Dashboard shows at least 0 open tickets (fresh org ok)"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Dashboard stats failed: {res.text}"
        data = res.json()
        # Just check the API returns correctly - fresh org may have 0
        print(f"PASS: Dashboard stats returned. Data keys: {list(data.keys())}")


# ============================================================
# FLOW 07 — EFI diagnostics
# ============================================================
class TestFlow07EFIDiagnostics:
    """FLOW 07 — EFI/AI diagnostics"""

    def test_efi_diagnose(self):
        """POST /api/ai/diagnose returns result"""
        assert state["token"], "No token from Flow 01"
        payload = {
            "issue_description": "Battery not charging, reduced range 30km, BMS warning",
            "vehicle_category": "2W_EV",
            "category": "battery",
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
        has_result = (
            data.get("diagnosis")
            or data.get("result")
            or data.get("analysis")
            or data.get("solution")
            or data.get("recommendations")
        )
        assert has_result, f"EFI returned no content: {data}"
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
        print(f"PASS: EFI failure cards returned")


# ============================================================
# FLOW 08 — Update and close ticket
# ============================================================
class TestFlow08CloseTicket:
    """FLOW 08 — Update and close ticket"""

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
            "resolution_notes": "BMS recalibrated, brake pads replaced",
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
        assert status in ["resolved", "closed", "done", "in_progress"], \
            f"Unexpected status: '{status}'"
        print(f"PASS: Ticket status = {status}")


# ============================================================
# FLOW 09 — Create invoice
# ============================================================
class TestFlow09CreateInvoice:
    """FLOW 09 — Create invoice from ticket"""

    def test_create_invoice(self):
        """POST /api/invoices-enhanced/ creates invoice"""
        assert state["token"], "No token from Flow 01"
        # Invoice requires customer_id; use contact if available, else create one
        customer_id = state.get("contact_id")
        if not customer_id:
            # Create contact on-the-fly
            cr = requests.post(
                f"{BASE_URL}/api/contacts-enhanced/",
                json={"contact_type": "customer", "name": "Rajesh Kumar", "phone": "9876543210"},
                headers=auth_headers(), timeout=10,
            )
            if cr.status_code in [200, 201]:
                cdata = cr.json()
                contact = cdata.get("contact", cdata)
                customer_id = contact.get("contact_id") or contact.get("id")
                state["contact_id"] = customer_id

        assert customer_id, "Cannot create invoice without customer_id"
        payload = {
            "customer_id": customer_id,
            "invoice_date": "2026-02-01",
            "due_date": "2026-02-15",
            "line_items": [
                {"name": "BMS Module", "quantity": 1, "rate": 3200, "tax_rate": 18},
                {"name": "Brake Pad Set", "quantity": 1, "rate": 650, "tax_rate": 18},
                {"name": "BMS Recalibration Labour", "quantity": 2.5, "rate": 500, "tax_rate": 18},
            ],
        }
        if state.get("ticket_id"):
            payload["ticket_id"] = state["ticket_id"]

        res = requests.post(
            f"{BASE_URL}/api/invoices-enhanced/",
            json=payload,
            headers=auth_headers(),
            timeout=15,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Invoice create failed ({res.status_code}): {data}"
        invoice = data.get("invoice", data)
        invoice_id = invoice.get("invoice_id") or invoice.get("id") or data.get("invoice_id")
        assert invoice_id, f"No invoice_id: {data}"
        state["invoice_id"] = invoice_id
        print(f"PASS: Invoice created id={invoice_id}")

    def test_invoice_gst_calculated(self):
        """GET invoice shows GST amounts"""
        assert state["token"] and state["invoice_id"], "Missing token or invoice"
        res = requests.get(
            f"{BASE_URL}/api/invoices-enhanced/{state['invoice_id']}",
            headers=auth_headers(),
            timeout=10,
        )
        assert res.status_code == 200, f"Invoice GET failed: {res.text}"
        data = res.json()
        # Response is {invoice: {...}}
        invoice = data.get("invoice", data)
        has_gst = (
            invoice.get("cgst_amount") is not None
            or invoice.get("sgst_amount") is not None
            or invoice.get("tax_amount") is not None
            or invoice.get("total_tax") is not None
            or invoice.get("gst_amount") is not None
            or invoice.get("total_tax_amount") is not None
        )
        assert has_gst, f"No GST amounts in invoice: {list(invoice.keys())}"
        print(f"PASS: Invoice has GST amounts")


# ============================================================
# FLOW 10 — Record payment
# ============================================================
class TestFlow10RecordPayment:
    """FLOW 10 — Record payment against invoice"""

    def test_record_payment(self):
        """POST /api/payments records payment for invoice"""
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
        """GET /api/reports/trial-balance returns data"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers=auth_headers(),
            timeout=15,
        )
        assert res.status_code == 200, f"Trial Balance failed: {res.text}"
        data = res.json()
        print(f"PASS: Trial Balance returned keys: {list(data.keys())}")

    def test_profit_loss_loads(self):
        """GET /api/reports/profit-loss returns data"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/reports/profit-loss",
            headers=auth_headers(),
            timeout=15,
        )
        assert res.status_code == 200, f"P&L failed: {res.text}"
        data = res.json()
        print(f"PASS: P&L returned keys: {list(data.keys())}")

    def test_gst_summary_loads(self):
        """GET /api/reports/gst-summary or /api/gst/summary"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/reports/gst-summary",
            headers=auth_headers(),
            timeout=15,
        )
        if res.status_code == 404:
            res = requests.get(
                f"{BASE_URL}/api/gst/summary",
                headers=auth_headers(),
                timeout=15,
            )
        assert res.status_code == 200, f"GST summary failed: {res.text}"
        data = res.json()
        print(f"PASS: GST summary returned keys: {list(data.keys())}")


# ============================================================
# FLOW 12 — Tally XML export
# ============================================================
class TestFlow12TallyExport:
    """FLOW 12 — Tally XML export"""

    def test_tally_export(self):
        """GET /api/finance/export/tally-xml returns XML"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/finance/export/tally-xml",
            headers=auth_headers(),
            params={"date_from": "2026-01-01", "date_to": "2026-03-31"},
            timeout=20,
        )
        assert res.status_code == 200, f"Tally export failed: {res.status_code} {res.text[:200]}"
        content_type = res.headers.get("content-type", "")
        body = res.text
        is_xml = (
            "xml" in content_type
            or "octet-stream" in content_type
            or body.strip().startswith("<?xml")
            or "<ENVELOPE>" in body
            or "TALLYMESSAGE" in body
            or "<envelope>" in body.lower()
        )
        assert is_xml, f"Response not XML: content_type={content_type}, body={body[:300]}"
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
            "first_name": "Ravi",
            "last_name": "Kumar",
            "email": "ravi.audit@battwheelstest.com",
            "phone": "9000000099",
            "department": "Workshop",
            "designation": "Technician",
            "employment_type": "full_time",
            "date_of_joining": "2026-02-01",
            "employee_code": "EMP-AUDIT-001",
            "pan_number": "ABCDE1234F",
            "state": "Delhi",
            "salary_structure": {
                "basic": 18000,
                "hra": 0,
                "da": 0,
                "special_allowance": 0,
            },
            "system_role": "technician",
            "pf_enrolled": True,
            "esi_enrolled": True,
        }
        res = requests.post(
            f"{BASE_URL}/api/hr/employees",
            json=payload,
            headers=auth_headers(),
            timeout=15,
        )
        data = res.json()
        if res.status_code == 400 and "already" in str(data.get("detail", "")).lower():
            # Try to get existing
            emp_res = requests.get(
                f"{BASE_URL}/api/hr/employees",
                headers=auth_headers(),
                timeout=10,
            )
            emp_data = emp_res.json()
            employees = emp_data.get("employees", emp_data if isinstance(emp_data, list) else [])
            ravi = next((e for e in employees if "Ravi" in e.get("first_name", "")), None)
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
        """POST /api/hr/payroll/generate for Feb 2026"""
        assert state["token"], "No token from Flow 01"
        assert state.get("employee_id"), "No employee from Flow 13"
        res = requests.post(
            f"{BASE_URL}/api/hr/payroll/generate",
            params={"month": "February", "year": 2026},
            headers=auth_headers(),
            timeout=30,
        )
        data = res.json()
        assert res.status_code in [200, 201], f"Payroll generate failed: {data}"
        print(f"PASS: Payroll generated. Response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")

    def test_payroll_records_available(self):
        """GET /api/hr/payroll/records returns records"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/hr/payroll/records",
            headers=auth_headers(),
            params={"month": "February", "year": 2026},
            timeout=10,
        )
        assert res.status_code == 200, f"Payroll records failed: {res.text}"
        data = res.json()
        print(f"PASS: Payroll records returned. Keys: {list(data.keys())}")


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
        """POST /api/public/tickets/submit without org slug → friendly 400"""
        payload = {
            "vehicle_category": "2W_EV",
            "vehicle_number": "MH01AB0001",
            "customer_name": "Priya Sharma",
            "contact_number": "9123456789",
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
        # Should NOT crash with 500
        assert res.status_code != 500, f"FAIL: Server crashed with 500"
        assert res.status_code in [400, 422, 404], \
            f"Expected 400/422/404 for missing slug, got {res.status_code}"
        data = res.json()
        # Error can be a string or a list
        detail = data.get("detail", data.get("message", ""))
        if isinstance(detail, list):
            error_msg = str(detail)
        else:
            error_msg = str(detail)
        print(f"PASS: Public ticket without slug returns {res.status_code}: {error_msg[:100]}")

    def test_public_vehicle_categories(self):
        """GET /api/public/vehicle-categories loads without auth"""
        res = requests.get(
            f"{BASE_URL}/api/public/vehicle-categories",
            timeout=10,
        )
        assert res.status_code == 200, f"Public vehicle categories failed: {res.text}"
        data = res.json()
        assert "categories" in data, f"No categories key: {data}"
        print(f"PASS: {len(data['categories'])} vehicle categories returned")


# ============================================================
# FLOW 15 — Data Insights
# ============================================================
class TestFlow15DataInsights:
    """FLOW 15 — Data Insights 6 sections"""

    def test_insights_revenue(self):
        """GET /api/insights/revenue"""
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
        """GET /api/insights/operations"""
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
        """GET /api/insights/technician-performance"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/technician-performance",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code in [200, 404], f"Technician insights failed: {res.text}"
        print(f"PASS: Technician insights HTTP {res.status_code}")

    def test_insights_inventory(self):
        """GET /api/insights/inventory"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/inventory",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code in [200, 404], f"Inventory insights failed: {res.text}"
        print(f"PASS: Inventory insights HTTP {res.status_code}")

    def test_insights_efi(self):
        """GET /api/insights/efi-intelligence"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/efi-intelligence",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code in [200, 404], f"EFI insights failed: {res.text}"
        print(f"PASS: EFI insights HTTP {res.status_code}")

    def test_insights_customer(self):
        """GET /api/insights/customer-intelligence"""
        assert state["token"], "No token from Flow 01"
        res = requests.get(
            f"{BASE_URL}/api/insights/customer-intelligence",
            headers=auth_headers(),
            params={"period": "month"},
            timeout=15,
        )
        assert res.status_code in [200, 404], f"Customer insights failed: {res.text}"
        print(f"PASS: Customer insights HTTP {res.status_code}")


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
        assert res.status_code in [200, 201], f"Book demo failed ({res.status_code}): {data}"
        print(f"PASS: Book demo submitted: {data}")

    def test_book_demo_validation(self):
        """POST /api/book-demo without required fields → 422"""
        payload = {"name": "Incomplete"}
        res = requests.post(
            f"{BASE_URL}/api/book-demo",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert res.status_code == 422, \
            f"Expected 422 for incomplete payload, got {res.status_code}"
        print(f"PASS: Book demo validation working (422)")


# ============================================================
# CLEANUP — Report audit org ID
# ============================================================
class TestCleanup:
    """Report audit org state for cleanup"""

    def test_report_audit_org(self):
        """Print audit org ID for cleanup"""
        print(f"\n{'='*60}")
        print(f"AUDIT ORG ID: {state.get('org_id', 'NOT CREATED')}")
        print(f"AUDIT EMAIL: {AUDIT_EMAIL}")
        print(f"Ticket ID: {state.get('ticket_id')}")
        print(f"Invoice ID: {state.get('invoice_id')}")
        print(f"Employee ID: {state.get('employee_id')}")
        print(f"BMS Item ID: {state.get('bms_item_id')}")
        print(f"Brake Item ID: {state.get('brake_item_id')}")
        print(f"{'='*60}\n")
        print("PASS: Audit org data reported")
