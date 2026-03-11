"""
GSTR-3B Section 3.1(d) — Reverse Charge Mechanism Tests
========================================================
Seeds 3 bills directly into MongoDB, queries GSTR-3B API,
asserts exact RCM values. Cleans up seed data after tests.

Test data:
  Bill 1: reverse_charge=True, intra-state, taxable=10000, CGST=900, SGST=900
  Bill 2: reverse_charge=False, taxable=5000 (should NOT appear in RCM)
  Bill 3: reverse_charge=True, inter-state, taxable=20000, IGST=3600
"""

import pytest
import requests
import uuid
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_dev")
TEST_MONTH = "2099-01"
RCM_TAG = f"rcm_test_{uuid.uuid4().hex[:8]}"

# The org_id of the demo user — fetched from their auth token
DEMO_ORG_ID = None


def _get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


@pytest.fixture(scope="module")
def auth_headers():
    """Login as demo user and extract org_id from JWT."""
    import jwt
    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "demo@voltmotors.in", "password": "Demo@12345"},
    )
    if resp.status_code != 200:
        pytest.skip(f"Login failed: {resp.status_code}")
    token = resp.json()["token"]
    # Decode JWT to get organization_id
    decoded = jwt.decode(token, options={"verify_signature": False})
    org_id = decoded.get("organization_id", decoded.get("org_id", ""))
    global DEMO_ORG_ID
    DEMO_ORG_ID = org_id
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Organization-ID": org_id,
    }


@pytest.fixture(scope="module", autouse=True)
def seed_and_cleanup(auth_headers):
    """Seed 3 test bills directly into MongoDB, yield, then delete them."""
    loop = _get_event_loop()

    bill_ids = [
        f"BILL-RCM-INTRA-{RCM_TAG}",
        f"BILL-NORMAL-{RCM_TAG}",
        f"BILL-RCM-INTER-{RCM_TAG}",
    ]

    bills = [
        {
            "bill_id": bill_ids[0],
            "bill_number": f"RCM-INTRA-{RCM_TAG}",
            "organization_id": DEMO_ORG_ID,
            "vendor_name": "RCM Intra Vendor",
            "vendor_gstin": "07AADCB2230M1ZT",
            "date": f"{TEST_MONTH}-15",
            "due_date": f"{TEST_MONTH}-28",
            "sub_total": 10000,
            "tax_total": 1800,
            "total": 11800,
            "reverse_charge": True,
            "status": "approved",
        },
        {
            "bill_id": bill_ids[1],
            "bill_number": f"NORMAL-{RCM_TAG}",
            "organization_id": DEMO_ORG_ID,
            "vendor_name": "Normal Vendor",
            "vendor_gstin": "07AADCB2230M1ZT",
            "date": f"{TEST_MONTH}-15",
            "due_date": f"{TEST_MONTH}-28",
            "sub_total": 5000,
            "tax_total": 900,
            "total": 5900,
            "reverse_charge": False,
            "status": "approved",
        },
        {
            "bill_id": bill_ids[2],
            "bill_number": f"RCM-INTER-{RCM_TAG}",
            "organization_id": DEMO_ORG_ID,
            "vendor_name": "RCM Inter Vendor",
            "vendor_gstin": "29AADCB2230M1ZV",
            "date": f"{TEST_MONTH}-15",
            "due_date": f"{TEST_MONTH}-28",
            "sub_total": 20000,
            "tax_total": 3600,
            "total": 23600,
            "reverse_charge": True,
            "status": "approved",
        },
    ]

    async def seed():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        for bill in bills:
            await db.bills.insert_one(bill.copy())
        print(f"  Seeded {len(bills)} test bills with tag {RCM_TAG}")

    async def cleanup():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        result = await db.bills.delete_many({"bill_id": {"$in": bill_ids}})
        print(f"  Cleaned up {result.deleted_count} seed bills")

    loop.run_until_complete(seed())
    yield
    loop.run_until_complete(cleanup())


class TestGSTR3BSection31D:
    """Verify Section 3.1(d) RCM values from seeded bills."""

    def test_section_3_1_d_exists_with_cess(self, auth_headers):
        """section_3_1.d must exist and include cess field."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={TEST_MONTH}",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"GSTR-3B failed: {resp.status_code}"
        data = resp.json()
        s31 = data.get("section_3_1", {})
        assert "d" in s31, f"section_3_1.d missing. Keys: {list(s31.keys())}"
        d = s31["d"]
        assert "cess" in d, f"cess field missing from section_3_1.d: {d}"
        print(f"  section_3_1.d exists with cess field")

    def test_rcm_taxable_value_is_30000(self, auth_headers):
        """Only reverse_charge=True bills should sum: 10000 + 20000 = 30000"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={TEST_MONTH}",
            headers=auth_headers,
        )
        d = resp.json()["section_3_1"]["d"]
        assert d["taxable_value"] == 30000, f"Expected 30000, got {d['taxable_value']}"

    def test_rcm_cgst_is_900(self, auth_headers):
        """Intra-state RCM bill (10000 @ 18%): CGST = 1800/2 = 900"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={TEST_MONTH}",
            headers=auth_headers,
        )
        d = resp.json()["section_3_1"]["d"]
        assert d["cgst"] == 900, f"Expected 900, got {d['cgst']}"

    def test_rcm_sgst_is_900(self, auth_headers):
        """Intra-state RCM bill (10000 @ 18%): SGST = 1800/2 = 900"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={TEST_MONTH}",
            headers=auth_headers,
        )
        d = resp.json()["section_3_1"]["d"]
        assert d["sgst"] == 900, f"Expected 900, got {d['sgst']}"

    def test_rcm_igst_is_3600(self, auth_headers):
        """Inter-state RCM bill (20000 @ 18%): IGST = 3600"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={TEST_MONTH}",
            headers=auth_headers,
        )
        d = resp.json()["section_3_1"]["d"]
        assert d["igst"] == 3600, f"Expected 3600, got {d['igst']}"

    def test_rcm_cess_is_0(self, auth_headers):
        """Cess should be 0 (no cess on RCM supplies in test data)."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={TEST_MONTH}",
            headers=auth_headers,
        )
        d = resp.json()["section_3_1"]["d"]
        assert d["cess"] == 0, f"Expected 0, got {d['cess']}"

    def test_non_rcm_bill_excluded(self, auth_headers):
        """The non-RCM bill (5000) must NOT appear in section_3_1.d."""
        resp = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr3b?month={TEST_MONTH}",
            headers=auth_headers,
        )
        d = resp.json()["section_3_1"]["d"]
        assert d["taxable_value"] == 30000, (
            f"Non-RCM bill leaked into RCM! Expected 30000, got {d['taxable_value']}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
