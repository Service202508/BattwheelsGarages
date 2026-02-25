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
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

# Real org for ORG_A (admin user already has membership)
ORG_A = "6996dcf072ffd2a2395fee7b"
# Synthetic org for ORG_B
ORG_B = "test_org_gstr3b_beta_001"
ORG_B_USER_ID = "test_user_orgb_gstr3b"
ORG_B_EMAIL = "gstr3b_testuser_orgb@test.internal"
ORG_B_PASSWORD = "TestOrgB@12345"

# Test months — far future to avoid collision
MONTH_1 = "2099-06"
MONTH_2 = "2099-07"

# === Deterministic figures ===
# Invoice A1: taxable ₹10,000, 18% intra-state → CGST ₹900, SGST ₹900, total ₹11,800
INV_SUBTOTAL = 10000.0
INV_TAX_TOTAL = 1800.0
INV_CGST = 900.0
INV_SGST = 900.0
INV_TOTAL = 11800.0

# CN1 (partial, month 1): taxable ₹2,000, CGST ₹180, SGST ₹180, total ₹2,360
CN1_SUBTOTAL = 2000.0
CN1_CGST = 180.0
CN1_SGST = 180.0
CN1_IGST = 0.0
CN1_GST = 360.0
CN1_TOTAL = 2360.0

# CN2 (partial, month 1, same invoice): taxable ₹1,000, CGST ₹90, SGST ₹90, total ₹1,180
CN2_SUBTOTAL = 1000.0
CN2_CGST = 90.0
CN2_SGST = 90.0
CN2_IGST = 0.0
CN2_GST = 180.0
CN2_TOTAL = 1180.0

# CN3 (cross-period, in month 2): taxable ₹500, IGST ₹90, total ₹590
CN3_SUBTOTAL = 500.0
CN3_CGST = 0.0
CN3_SGST = 0.0
CN3_IGST = 90.0
CN3_GST = 90.0
CN3_TOTAL = 590.0

# Org B invoice: taxable ₹5,000, CGST ₹450, SGST ₹450, total ₹5,900
ORGB_INV_SUBTOTAL = 5000.0
ORGB_INV_TAX_TOTAL = 900.0
ORGB_INV_TOTAL = 5900.0

# Auth
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "Admin@12345"
TOKEN_A = None
TOKEN_B = None


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def get_token_a():
    global TOKEN_A
    if TOKEN_A:
        return TOKEN_A
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
    })
    TOKEN_A = resp.json().get("token", "")
    return TOKEN_A


def get_token_b():
    global TOKEN_B
    if TOKEN_B:
        return TOKEN_B
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_B_EMAIL, "password": ORG_B_PASSWORD
    })
    TOKEN_B = resp.json().get("token", "")
    return TOKEN_B


def headers_a():
    return {"Authorization": f"Bearer {get_token_a()}", "X-Organization-ID": ORG_A}

def headers_b():
    return {"Authorization": f"Bearer {get_token_b()}", "X-Organization-ID": ORG_B}


async def seed_test_data():
    """Insert deterministic test invoices and credit notes for both orgs."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Clean previous test runs (scoped to test data only)
    await db.invoices_enhanced.delete_many({
        "organization_id": {"$in": [ORG_A, ORG_B]},
        "invoice_number": {"$regex": "^TEST-"}
    })
    await db.credit_notes.delete_many({
        "organization_id": {"$in": [ORG_A, ORG_B]},
        "credit_note_number": {"$regex": "^TEST-"}
    })
    await db.invoices_enhanced.delete_many({
        "organization_id": ORG_B,
        "invoice_number": {"$regex": "^ORGB-"}
    })

    # Create Org B user + membership (idempotent)
    pw_hash = bcrypt.hashpw(ORG_B_PASSWORD.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one(
        {"user_id": ORG_B_USER_ID},
        {"$set": {
            "user_id": ORG_B_USER_ID,
            "email": ORG_B_EMAIL,
            "name": "GSTR3B Test User B",
            "password_hash": pw_hash,
            "role": "admin",
            "organization_id": ORG_B,
            "is_active": True,
        }},
        upsert=True
    )
    await db.organizations.update_one(
        {"organization_id": ORG_B},
        {"$set": {
            "organization_id": ORG_B,
            "name": "GSTR3B Test Org Beta",
            "is_active": True,
        }},
        upsert=True
    )
    await db.organization_users.update_one(
        {"user_id": ORG_B_USER_ID, "organization_id": ORG_B},
        {"$set": {
            "user_id": ORG_B_USER_ID,
            "organization_id": ORG_B,
            "role": "admin",
            "status": "active",
        }},
        upsert=True
    )

    inv_a1_id = "inv_test_gstr3b_a1"

    # === ORG A: MONTH_1 invoice (intra-state, CGST+SGST) ===
    await db.invoices_enhanced.insert_one({
        "invoice_id": inv_a1_id,
        "invoice_number": "TEST-INV-001",
        "organization_id": ORG_A,
        "invoice_date": f"{MONTH_1}-15",
        "status": "sent",
        "customer_name": "Test Customer Alpha",
        "customer_gstin": "07AABCU1234A1ZB",
        "sub_total": INV_SUBTOTAL,
        "tax_total": INV_TAX_TOTAL,
        "total": INV_TOTAL,
        "cgst_amount": INV_CGST,
        "sgst_amount": INV_SGST,
        "igst_amount": 0,
    })

    # === ORG A: MONTH_1 partial CN #1 ===
    await db.credit_notes.insert_one({
        "credit_note_id": "cn_test_gstr3b_01",
        "credit_note_number": "TEST-CN-001",
        "organization_id": ORG_A,
        "original_invoice_id": inv_a1_id,
        "original_invoice_number": "TEST-INV-001",
        "customer_name": "Test Customer Alpha",
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

    # === ORG A: MONTH_1 partial CN #2 (multiple CNs against same invoice) ===
    await db.credit_notes.insert_one({
        "credit_note_id": "cn_test_gstr3b_02",
        "credit_note_number": "TEST-CN-002",
        "organization_id": ORG_A,
        "original_invoice_id": inv_a1_id,
        "original_invoice_number": "TEST-INV-001",
        "customer_name": "Test Customer Alpha",
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

    # === ORG A: MONTH_2 cross-period CN ===
    await db.credit_notes.insert_one({
        "credit_note_id": "cn_test_gstr3b_03",
        "credit_note_number": "TEST-CN-003",
        "organization_id": ORG_A,
        "original_invoice_id": inv_a1_id,
        "original_invoice_number": "TEST-INV-001",
        "customer_name": "Test Customer Alpha",
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

    # === ORG B: MONTH_1 invoice (different org, same month, no CNs) ===
    await db.invoices_enhanced.insert_one({
        "invoice_id": "inv_test_gstr3b_b1",
        "invoice_number": "ORGB-INV-001",
        "organization_id": ORG_B,
        "invoice_date": f"{MONTH_1}-10",
        "status": "paid",
        "customer_name": "Org B Customer",
        "customer_gstin": "07XYZAB5678C1D2",
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
    await db.invoices_enhanced.delete_many({
        "organization_id": {"$in": [ORG_A, ORG_B]},
        "invoice_number": {"$regex": "^(TEST-|ORGB-)"}
    })
    await db.credit_notes.delete_many({
        "organization_id": {"$in": [ORG_A, ORG_B]},
        "credit_note_number": {"$regex": "^TEST-"}
    })
    # Clean up Org B test user/org
    await db.users.delete_one({"user_id": ORG_B_USER_ID})
    await db.organizations.delete_one({"organization_id": ORG_B})
    await db.organization_users.delete_one({"user_id": ORG_B_USER_ID, "organization_id": ORG_B})
    client.close()


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    run_async(seed_test_data())
    yield
    run_async(cleanup_test_data())


# ============= SAME PERIOD TESTS =============

class TestGSTR3B_SamePeriod:
    """Invoice and 2 CNs all in the same filing period (MONTH_1)."""

    def _get_month1(self):
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=headers_a()
        )
        assert resp.status_code == 200, f"GSTR-3B failed: {resp.text}"
        return resp.json()

    def test_net_taxable_value(self):
        """net taxable = invoice subtotal - CN1 - CN2 = 10000 - 2000 - 1000 = 7000"""
        data = self._get_month1()
        assert data["section_3_1"]["taxable_value"] == 7000.0

    def test_cgst_reduced(self):
        """CGST = 900 - 180 - 90 = 630"""
        data = self._get_month1()
        assert data["section_3_1"]["cgst"] == 630.0

    def test_sgst_reduced(self):
        """SGST = 900 - 180 - 90 = 630"""
        data = self._get_month1()
        assert data["section_3_1"]["sgst"] == 630.0

    def test_igst_unchanged(self):
        """IGST = 0 (intra-state only, no IGST CNs in month 1)"""
        data = self._get_month1()
        assert data["section_3_1"]["igst"] == 0

    def test_adjustments_count_and_values(self):
        """adjustments shows exactly 2 CNs with correct totals"""
        data = self._get_month1()
        adj = data["adjustments"]["credit_notes"]
        assert adj["count"] == 2
        assert adj["taxable_value"] == 3000.0  # 2000+1000
        assert adj["cgst"] == 270.0  # 180+90
        assert adj["sgst"] == 270.0  # 180+90

    def test_gross_outward_preserved(self):
        """gross_outward = full invoice subtotal before CN deduction"""
        data = self._get_month1()
        assert data["section_3_1"]["gross_outward"] == 10000.0


# ============= CROSS PERIOD TESTS =============

class TestGSTR3B_CrossPeriod:
    """CN3 created in MONTH_2 referencing an invoice from MONTH_1."""

    def test_month1_excludes_month2_cn(self):
        """Month 1 must NOT include CN3"""
        data = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=headers_a()
        ).json()
        assert data["adjustments"]["credit_notes"]["count"] == 2

    def test_month2_includes_cross_period_cn(self):
        """Month 2 MUST include CN3 (IGST credit note)"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_2}", headers=headers_a()
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        adj = data["adjustments"]["credit_notes"]
        assert adj["count"] == 1
        assert adj["taxable_value"] == 500.0
        assert adj["igst"] == 90.0

    def test_month2_negative_net_taxable(self):
        """Month 2 has no invoices, only CN3 → negative taxable"""
        data = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_2}", headers=headers_a()
        ).json()
        assert data["section_3_1"]["taxable_value"] == -500.0
        assert data["section_3_1"]["igst"] == -90.0


# ============= TENANT SCOPING TESTS =============

class TestGSTR3B_TenantScoping:
    """Each org sees only its own data — no cross-org contamination."""

    def test_org_a_sees_own_data(self):
        data = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=headers_a()
        ).json()
        assert data["section_3_1"]["gross_outward"] == 10000.0

    def test_org_b_sees_own_data(self):
        data = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=headers_b()
        ).json()
        assert data["section_3_1"]["gross_outward"] == 5000.0
        assert data["adjustments"]["credit_notes"]["count"] == 0

    def test_no_cross_org_leakage(self):
        data_a = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=headers_a()
        ).json()
        data_b = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=headers_b()
        ).json()
        assert data_a["section_3_1"]["gross_outward"] != data_b["section_3_1"]["gross_outward"]


# ============= GSTR-1 ALIGNMENT TESTS =============

class TestGSTR1_CreditNotes:
    """GSTR-1 CDNR section should show credit notes correctly."""

    def test_gstr1_cdnr_count(self):
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month={MONTH_1}", headers=headers_a()
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert data["cdnr"]["summary"]["count"] == 2

    def test_gstr1_grand_total_adjusted(self):
        data = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month={MONTH_1}", headers=headers_a()
        ).json()
        assert data["grand_total"]["taxable_value"] == 7000.0


class TestGSTR1_vs_GSTR3B_Alignment:
    """GSTR-1 net taxable == GSTR-3B section_3_1.taxable_value for same period."""

    def test_alignment(self):
        h = headers_a()
        r1 = requests.get(f"{BASE_URL}/api/v1/gst/gstr1?month={MONTH_1}", headers=h).json()
        r3b = requests.get(f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH_1}", headers=h).json()
        gstr1_net = r1["grand_total"]["taxable_value"]
        gstr3b_net = r3b["section_3_1"]["taxable_value"]
        assert gstr1_net == gstr3b_net, (
            f"GSTR-1 net ({gstr1_net}) != GSTR-3B net ({gstr3b_net})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
