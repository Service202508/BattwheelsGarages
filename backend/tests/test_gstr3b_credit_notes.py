"""
Day 3 — C-06: GSTR-3B Credit Note Inclusion Tests
===================================================
Validates that credit notes correctly reduce GSTR-3B outward supplies
and net GST liability. Tests cover:
- Same-period CN: invoice + CN both in the same filing month
- Cross-period CN: CN in month 2 referencing invoice from month 1
- Tenant scoping: two orgs see only their own data
- Partial CN: only CN amount deducted, not full invoice
- Multiple CNs against the same invoice
- CGST/SGST/IGST adjusted separately
"""
import pytest
import requests
import os
import asyncio
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

# Two test orgs
ORG_A = "test_org_gstr3b_a"
ORG_B = "test_org_gstr3b_b"

# Test months
MONTH_1 = "2099-06"  # far future to avoid collision with real data
MONTH_2 = "2099-07"

# Deterministic invoice/CN values
# Invoice: taxable ₹10,000, CGST ₹900, SGST ₹900, total ₹11,800 (18% intra-state)
INV_SUBTOTAL = 10000.0
INV_TAX_RATE = 18
INV_TAX_TOTAL = 1800.0  # 18% of 10000
INV_CGST = 900.0
INV_SGST = 900.0
INV_IGST = 0.0
INV_TOTAL = 11800.0

# Partial CN: taxable ₹2,000, CGST ₹180, SGST ₹180, total ₹2,360
CN1_SUBTOTAL = 2000.0
CN1_CGST = 180.0
CN1_SGST = 180.0
CN1_IGST = 0.0
CN1_GST = 360.0
CN1_TOTAL = 2360.0

# Second CN against same invoice: taxable ₹1,000, CGST ₹90, SGST ₹90, total ₹1,180
CN2_SUBTOTAL = 1000.0
CN2_CGST = 90.0
CN2_SGST = 90.0
CN2_IGST = 0.0
CN2_GST = 180.0
CN2_TOTAL = 1180.0

# Cross-period CN (in MONTH_2, ref invoice from MONTH_1): taxable ₹500, IGST ₹90, total ₹590
CN3_SUBTOTAL = 500.0
CN3_CGST = 0.0
CN3_SGST = 0.0
CN3_IGST = 90.0
CN3_GST = 90.0
CN3_TOTAL = 590.0

# Org B invoice: taxable ₹5,000, CGST ₹450, SGST ₹450
ORGB_INV_SUBTOTAL = 5000.0
ORGB_INV_TAX_TOTAL = 900.0
ORGB_INV_TOTAL = 5900.0

# Auth token
TOKEN = None
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "Admin@12345"


def get_token():
    global TOKEN
    if TOKEN:
        return TOKEN
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
    })
    TOKEN = resp.json().get("token", "")
    return TOKEN


def gstr3b_headers(org_id):
    return {
        "Authorization": f"Bearer {get_token()}",
        "X-Organization-ID": org_id
    }


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def seed_test_data():
    """Insert deterministic test invoices and credit notes for both orgs."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Clean up any previous test data
    await db.invoices_enhanced.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.credit_notes.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.invoices.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.bills.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.expenses.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})

    # === ORG A: MONTH_1 invoice (intra-state, CGST+SGST) ===
    inv_a1_id = f"inv_test_{uuid.uuid4().hex[:8]}"
    await db.invoices_enhanced.insert_one({
        "invoice_id": inv_a1_id,
        "invoice_number": "TEST-INV-001",
        "organization_id": ORG_A,
        "invoice_date": f"{MONTH_1}-15",
        "status": "sent",
        "customer_name": "Test Customer A",
        "customer_gstin": "06AABCU1234A1ZB",  # same state as org (06=Haryana)
        "sub_total": INV_SUBTOTAL,
        "tax_total": INV_TAX_TOTAL,
        "total": INV_TOTAL,
        "cgst_amount": INV_CGST,
        "sgst_amount": INV_SGST,
        "igst_amount": INV_IGST,
    })

    # === ORG A: MONTH_1 partial CN #1 (same period as invoice) ===
    await db.credit_notes.insert_one({
        "credit_note_id": f"cn_test_{uuid.uuid4().hex[:8]}",
        "credit_note_number": "TEST-CN-001",
        "organization_id": ORG_A,
        "original_invoice_id": inv_a1_id,
        "original_invoice_number": "TEST-INV-001",
        "customer_name": "Test Customer A",
        "reason": "Partial return",
        "subtotal": CN1_SUBTOTAL,
        "cgst_amount": CN1_CGST,
        "sgst_amount": CN1_SGST,
        "igst_amount": CN1_IGST,
        "gst_amount": CN1_GST,
        "gst_treatment": "cgst_sgst",
        "total": CN1_TOTAL,
        "status": "issued",
        "created_at": f"{MONTH_1}-20T10:00:00+00:00",
    })

    # === ORG A: MONTH_1 partial CN #2 against SAME invoice (multiple CNs test) ===
    await db.credit_notes.insert_one({
        "credit_note_id": f"cn_test_{uuid.uuid4().hex[:8]}",
        "credit_note_number": "TEST-CN-002",
        "organization_id": ORG_A,
        "original_invoice_id": inv_a1_id,
        "original_invoice_number": "TEST-INV-001",
        "customer_name": "Test Customer A",
        "reason": "Quality issue",
        "subtotal": CN2_SUBTOTAL,
        "cgst_amount": CN2_CGST,
        "sgst_amount": CN2_SGST,
        "igst_amount": CN2_IGST,
        "gst_amount": CN2_GST,
        "gst_treatment": "cgst_sgst",
        "total": CN2_TOTAL,
        "status": "issued",
        "created_at": f"{MONTH_1}-25T14:00:00+00:00",
    })

    # === ORG A: MONTH_2 cross-period CN (CN date in month 2, invoice from month 1) ===
    await db.credit_notes.insert_one({
        "credit_note_id": f"cn_test_{uuid.uuid4().hex[:8]}",
        "credit_note_number": "TEST-CN-003",
        "organization_id": ORG_A,
        "original_invoice_id": inv_a1_id,
        "original_invoice_number": "TEST-INV-001",
        "customer_name": "Test Customer A",
        "reason": "Late return - cross period",
        "subtotal": CN3_SUBTOTAL,
        "cgst_amount": CN3_CGST,
        "sgst_amount": CN3_SGST,
        "igst_amount": CN3_IGST,
        "gst_amount": CN3_GST,
        "gst_treatment": "igst",
        "total": CN3_TOTAL,
        "status": "issued",
        "created_at": f"{MONTH_2}-05T09:00:00+00:00",
    })

    # === ORG B: MONTH_1 invoice (different org, same month) ===
    await db.invoices_enhanced.insert_one({
        "invoice_id": f"inv_test_{uuid.uuid4().hex[:8]}",
        "invoice_number": "ORGB-INV-001",
        "organization_id": ORG_B,
        "invoice_date": f"{MONTH_1}-10",
        "status": "paid",
        "customer_name": "Org B Customer",
        "customer_gstin": "06XYZAB5678C1D2",
        "sub_total": ORGB_INV_SUBTOTAL,
        "tax_total": ORGB_INV_TAX_TOTAL,
        "total": ORGB_INV_TOTAL,
        "cgst_amount": 450.0,
        "sgst_amount": 450.0,
        "igst_amount": 0,
    })

    client.close()
    print("Test data seeded successfully")


async def cleanup_test_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.invoices_enhanced.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.credit_notes.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.invoices.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.bills.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    await db.expenses.delete_many({"organization_id": {"$in": [ORG_A, ORG_B]}})
    client.close()


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    run_async(seed_test_data())
    yield
    run_async(cleanup_test_data())


class TestGSTR3B_SamePeriod:
    """Unit test — same period: Invoice and CN both in the same filing period."""

    def test_same_period_net_taxable_value(self):
        """GSTR-3B month 1: net taxable = invoice subtotal - CN1 subtotal - CN2 subtotal"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        s31 = data["section_3_1"]

        expected_taxable = INV_SUBTOTAL - CN1_SUBTOTAL - CN2_SUBTOTAL  # 10000 - 2000 - 1000 = 7000
        assert s31["taxable_value"] == expected_taxable, (
            f"Expected taxable {expected_taxable}, got {s31['taxable_value']}"
        )

    def test_same_period_cgst_reduced(self):
        """CGST correctly reduced by CN1 + CN2 CGST"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        s31 = data["section_3_1"]

        expected_cgst = INV_CGST - CN1_CGST - CN2_CGST  # 900 - 180 - 90 = 630
        assert s31["cgst"] == expected_cgst, (
            f"Expected CGST {expected_cgst}, got {s31['cgst']}"
        )

    def test_same_period_sgst_reduced(self):
        """SGST correctly reduced by CN1 + CN2 SGST"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        s31 = data["section_3_1"]

        expected_sgst = INV_SGST - CN1_SGST - CN2_SGST  # 900 - 180 - 90 = 630
        assert s31["sgst"] == expected_sgst, (
            f"Expected SGST {expected_sgst}, got {s31['sgst']}"
        )

    def test_same_period_igst_unchanged(self):
        """IGST unchanged (intra-state invoice, no IGST CNs in month 1)"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        s31 = data["section_3_1"]

        assert s31["igst"] == 0, f"Expected IGST 0, got {s31['igst']}"

    def test_same_period_adjustments_block(self):
        """adjustments.credit_notes shows 2 CNs with correct totals"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        adj = data["adjustments"]["credit_notes"]

        assert adj["count"] == 2, f"Expected 2 CNs, got {adj['count']}"
        assert adj["taxable_value"] == CN1_SUBTOTAL + CN2_SUBTOTAL  # 3000
        assert adj["cgst"] == CN1_CGST + CN2_CGST  # 270
        assert adj["sgst"] == CN1_SGST + CN2_SGST  # 270

    def test_same_period_gross_outward_preserved(self):
        """gross_outward shows full invoice value before CN deduction"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        s31 = data["section_3_1"]

        assert s31["gross_outward"] == INV_SUBTOTAL  # 10000


class TestGSTR3B_CrossPeriod:
    """Unit test — cross period: CN in Month 2 for invoice from Month 1."""

    def test_month1_excludes_month2_cn(self):
        """Month 1 report must NOT include the cross-period CN (created in month 2)"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        adj = data["adjustments"]["credit_notes"]

        # Only CN1 and CN2 are in month 1; CN3 is in month 2
        assert adj["count"] == 2, f"Month 1 should have 2 CNs, got {adj['count']}"

    def test_month2_includes_cross_period_cn(self):
        """Month 2 report MUST include the cross-period CN and reduce liability"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_2}",
            headers=gstr3b_headers(ORG_A)
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        adj = data["adjustments"]["credit_notes"]

        assert adj["count"] == 1, f"Month 2 should have 1 CN, got {adj['count']}"
        assert adj["taxable_value"] == CN3_SUBTOTAL  # 500
        assert adj["igst"] == CN3_IGST  # 90

    def test_month2_net_values_negative_or_zero(self):
        """Month 2 has no invoices, only a CN — net taxable should be negative"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_2}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        s31 = data["section_3_1"]

        # No invoices in month 2, only CN3
        assert s31["taxable_value"] == -CN3_SUBTOTAL  # -500
        assert s31["igst"] == -CN3_IGST  # -90


class TestGSTR3B_TenantScoping:
    """Confirm each org sees only its own data."""

    def test_org_a_month1(self):
        """Org A sees its invoice + 2 CNs"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        assert data["section_3_1"]["gross_outward"] == INV_SUBTOTAL  # 10000

    def test_org_b_month1(self):
        """Org B sees its own invoice, no CNs"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_B)
        )
        data = resp.json()
        assert data["section_3_1"]["gross_outward"] == ORGB_INV_SUBTOTAL  # 5000
        assert data["adjustments"]["credit_notes"]["count"] == 0

    def test_no_cross_org_contamination(self):
        """Org A and Org B totals must differ — no cross-org leakage"""
        resp_a = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        resp_b = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}",
            headers=gstr3b_headers(ORG_B)
        )
        data_a = resp_a.json()
        data_b = resp_b.json()

        assert data_a["section_3_1"]["gross_outward"] != data_b["section_3_1"]["gross_outward"]
        assert data_a["adjustments"]["credit_notes"]["count"] != data_b["adjustments"]["credit_notes"]["count"]


class TestGSTR1_CreditNotes:
    """Verify GSTR-1 also includes credit notes correctly (Section CDNR)."""

    def test_gstr1_cdnr_section(self):
        """GSTR-1 CDNR section shows 2 credit notes in month 1"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        cdnr = data.get("cdnr", {})
        assert cdnr["summary"]["count"] == 2

    def test_gstr1_grand_total_adjusted(self):
        """GSTR-1 grand total taxable value reduced by CN amounts"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month={MONTH_1}",
            headers=gstr3b_headers(ORG_A)
        )
        data = resp.json()
        gt = data["grand_total"]

        expected_net_taxable = INV_SUBTOTAL - (CN1_SUBTOTAL + CN2_SUBTOTAL)  # 7000
        assert gt["taxable_value"] == expected_net_taxable


class TestGSTR1_vs_GSTR3B_Alignment:
    """GSTR-1 gross minus CN adjustments = GSTR-3B net"""

    def test_alignment(self):
        """GSTR-1 grand_total.taxable_value == GSTR-3B section_3_1.taxable_value for same month"""
        h = gstr3b_headers(ORG_A)
        r1 = requests.get(f"{BASE_URL}/api/v1/gst/gstr1?month={MONTH_1}", headers=h)
        r3b = requests.get(f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=h)

        gstr1_net_taxable = r1.json()["grand_total"]["taxable_value"]
        gstr3b_net_taxable = r3b.json()["section_3_1"]["taxable_value"]

        assert gstr1_net_taxable == gstr3b_net_taxable, (
            f"GSTR-1 net taxable ({gstr1_net_taxable}) != GSTR-3B net taxable ({gstr3b_net_taxable})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
