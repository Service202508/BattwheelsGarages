"""Staging validation for GSTR-3B credit note fix."""
import asyncio
import os
import requests
import bcrypt
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ORG_A = "6996dcf072ffd2a2395fee7b"
ORG_B = "staging_org_beta_gstr3b"
ORG_B_USER_ID = "staging_user_orgb"
ORG_B_EMAIL = "staging_orgb@test.internal"
ORG_B_PASSWORD = "StagingB@12345"
MONTH = "2099-06"


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Cleanup first
    for oid in [ORG_A, ORG_B]:
        await db.invoices_enhanced.delete_many(
            {"organization_id": oid, "invoice_number": {"$regex": "^(STG-|ORGB-STG-)"}}
        )
    await db.credit_notes.delete_many({"credit_note_id": "stg_cn_01"})

    # Org B setup
    pw = bcrypt.hashpw(ORG_B_PASSWORD.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one(
        {"user_id": ORG_B_USER_ID},
        {"$set": {
            "user_id": ORG_B_USER_ID, "email": ORG_B_EMAIL, "name": "Staging B",
            "password_hash": pw, "role": "admin", "organization_id": ORG_B, "is_active": True
        }}, upsert=True
    )
    await db.organizations.update_one(
        {"organization_id": ORG_B},
        {"$set": {"organization_id": ORG_B, "name": "Staging Beta Org", "is_active": True}},
        upsert=True
    )
    await db.organization_users.update_one(
        {"user_id": ORG_B_USER_ID, "organization_id": ORG_B},
        {"$set": {"user_id": ORG_B_USER_ID, "organization_id": ORG_B, "role": "admin", "status": "active"}},
        upsert=True
    )

    # Org A: invoice + CN
    await db.invoices_enhanced.insert_one({
        "invoice_id": "stg_inv_a1", "invoice_number": "STG-INV-001",
        "organization_id": ORG_A, "invoice_date": f"{MONTH}-15", "status": "sent",
        "customer_name": "Staging Customer A", "customer_gstin": "07AABCU1234A1ZB",
        "sub_total": 10000, "tax_total": 1800, "total": 11800,
    })
    await db.credit_notes.insert_one({
        "credit_note_id": "stg_cn_01", "credit_note_number": "STG-CN-001",
        "organization_id": ORG_A, "original_invoice_id": "stg_inv_a1",
        "subtotal": 2000, "cgst_amount": 180, "sgst_amount": 180, "igst_amount": 0,
        "gst_amount": 360, "total": 2360, "status": "issued",
        "created_at": f"{MONTH}-20T10:00:00+00:00",
    })

    # Org B: invoice only, no CNs
    await db.invoices_enhanced.insert_one({
        "invoice_id": "stg_inv_b1", "invoice_number": "ORGB-STG-001",
        "organization_id": ORG_B, "invoice_date": f"{MONTH}-10", "status": "paid",
        "customer_name": "Staging Customer B", "customer_gstin": "07XYZAB5678C1D2",
        "sub_total": 5000, "tax_total": 900, "total": 5900,
    })
    client.close()


async def cleanup():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.invoices_enhanced.delete_many({"invoice_id": {"$in": ["stg_inv_a1", "stg_inv_b1"]}})
    await db.credit_notes.delete_many({"credit_note_id": "stg_cn_01"})
    await db.users.delete_one({"user_id": ORG_B_USER_ID})
    await db.organizations.delete_one({"organization_id": ORG_B})
    await db.organization_users.delete_one({"user_id": ORG_B_USER_ID, "organization_id": ORG_B})
    client.close()


def main():
    asyncio.run(seed())

    tok_a = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in", "password": "Admin@12345"
    }).json()["token"]
    tok_b = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_B_EMAIL, "password": ORG_B_PASSWORD
    }).json()["token"]

    r_a = requests.get(f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH}",
                       headers={"Authorization": f"Bearer {tok_a}", "X-Organization-ID": ORG_A}).json()
    r_b = requests.get(f"{BASE_URL}/api/v1/gst/gstr3b?month={MONTH}",
                       headers={"Authorization": f"Bearer {tok_b}", "X-Organization-ID": ORG_B}).json()

    s31a = r_a["section_3_1"]
    adja = r_a["adjustments"]["credit_notes"]
    s31b = r_b["section_3_1"]
    adjb = r_b["adjustments"]["credit_notes"]

    print("=" * 60)
    print("STAGING VALIDATION REPORT")
    print("=" * 60)
    print()
    print("--- Org A: Battwheels Garages ---")
    print(f"  Gross Outward:  {s31a['gross_outward']}")
    print(f"  CN Adjustment:  {s31a['cn_adjustment']}")
    print(f"  Net Taxable:    {s31a['taxable_value']}")
    print(f"  CGST (net):     {s31a['cgst']}")
    print(f"  SGST (net):     {s31a['sgst']}")
    print(f"  IGST (net):     {s31a['igst']}")
    print(f"  Total Tax:      {s31a['total_tax']}")
    print(f"  CN Count:       {adja['count']}")
    print(f"  Net Liability:  {r_a['section_6']['total_liability']}")
    print()
    print("--- Org B: Staging Beta Org ---")
    print(f"  Gross Outward:  {s31b['gross_outward']}")
    print(f"  CN Adjustment:  {s31b['cn_adjustment']}")
    print(f"  Net Taxable:    {s31b['taxable_value']}")
    print(f"  CGST (net):     {s31b['cgst']}")
    print(f"  SGST (net):     {s31b['sgst']}")
    print(f"  IGST (net):     {s31b['igst']}")
    print(f"  CN Count:       {adjb['count']}")
    print(f"  Net Liability:  {r_b['section_6']['total_liability']}")
    print()
    print("--- Cross-Org Validation ---")
    ok1 = s31a["gross_outward"] == 10000 and s31b["gross_outward"] == 5000
    ok2 = adja["count"] == 1 and adjb["count"] == 0
    ok3 = s31a["gross_outward"] != s31b["gross_outward"]
    print(f"  Figures differ per org:   {'PASS' if ok3 else 'FAIL'} (A={s31a['gross_outward']}, B={s31b['gross_outward']})")
    print(f"  CN scoping correct:       {'PASS' if ok2 else 'FAIL'} (A_cn={adja['count']}, B_cn={adjb['count']})")
    print(f"  No cross-org totals:      {'PASS' if ok1 else 'FAIL'}")
    print()

    asyncio.run(cleanup())
    print("Staging data cleaned up.")


if __name__ == "__main__":
    main()
