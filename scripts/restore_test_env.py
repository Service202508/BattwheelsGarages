"""
Restore Test Environment for Battwheels OS Core Test Suite
==========================================================
Restores all data required by the test suite (428 tests).

Protects and rebuilds:
  - dev-internal-testing-001 (core test infrastructure org)
  - org_9c74befbaa95 (starter entitlement test org)

Usage:
    python scripts/restore_test_env.py

SAFETY: Hard-coded to ONLY run against battwheels_dev.
"""

import asyncio
import os
import bcrypt
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

DEV_ORG_ID = "dev-internal-testing-001"
STARTER_ORG_ID = "org_9c74befbaa95"
DEV_USER_ID = "user_f52257c9b53c"


async def restore():
    db_name = os.environ.get("DB_NAME", "battwheels_dev")
    if db_name != "battwheels_dev":
        raise Exception(f"SAFETY: This script ONLY runs against battwheels_dev. Got: {db_name}")

    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[db_name]
    now = datetime.now(timezone.utc).isoformat()

    print("=" * 60)
    print("  Restore Test Environment")
    print(f"  Database: {db_name}")
    print(f"  Timestamp: {now}")
    print("=" * 60)

    # ================================================================
    # 1. Clean up spurious organization_users for the dev user
    # ================================================================
    print("\n[1] Cleaning spurious org memberships for dev user...")
    result = await db.organization_users.delete_many({
        "user_id": DEV_USER_ID,
        "organization_id": {"$ne": DEV_ORG_ID}
    })
    print(f"    Removed {result.deleted_count} spurious memberships")
    await db.organization_users.update_one(
        {"user_id": DEV_USER_ID, "organization_id": DEV_ORG_ID},
        {"$set": {"last_active_at": now}}
    )

    # ================================================================
    # 2. Fix subscription for dev-internal-testing-001
    # ================================================================
    print("\n[2] Fixing subscription for dev org...")
    await db.subscriptions.delete_many({"organization_id": DEV_ORG_ID})
    await db.subscriptions.insert_one({
        "subscription_id": "sub_dev_professional_001",
        "organization_id": DEV_ORG_ID,
        "plan_id": "plan_professional_monthly",
        "plan_code": "professional",
        "plan_name": "Professional",
        "status": "active",
        "billing_cycle": "monthly",
        "current_period_start": "2026-01-01T00:00:00+00:00",
        "current_period_end": "2027-01-01T00:00:00+00:00",
        "features": [
            "advanced_invoicing", "hr_payroll", "gst_compliance",
            "efi_intelligence", "banking", "inventory", "api_access",
            "accounting_module", "project_management"
        ],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": now,
    })
    await db.organizations.update_one(
        {"organization_id": DEV_ORG_ID},
        {"$set": {"plan": "professional", "plan_type": "professional", "subscription_status": "active"}}
    )
    print("    Done")

    # ================================================================
    # 3. Create starter test org
    # ================================================================
    print("\n[3] Ensuring starter test org exists...")
    if not await db.organizations.find_one({"organization_id": STARTER_ORG_ID}):
        await db.organizations.insert_one({
            "organization_id": STARTER_ORG_ID,
            "name": "TestCompany", "slug": "testcompany",
            "industry_type": "ev_garage", "plan": "starter", "plan_type": "starter",
            "subscription_status": "active", "is_active": True, "is_onboarded": True,
            "created_at": now, "updated_at": now, "city": "Test City", "country": "India",
            "settings": {"currency": "INR", "timezone": "Asia/Kolkata",
                         "date_format": "DD/MM/YYYY", "fiscal_year_start": "April"},
        })
    print("    Done")

    # ================================================================
    # 4. john@testcompany.com user for starter org
    # ================================================================
    print("\n[4] Configuring john@testcompany.com...")
    john = await db.users.find_one({"email": "john@testcompany.com"})
    john_uid = john["user_id"] if john else "user_john_test_001"
    if john:
        await db.users.update_one(
            {"email": "john@testcompany.com"},
            {"$set": {"organization_id": STARTER_ORG_ID, "organizations": [STARTER_ORG_ID]}}
        )
    else:
        pw = bcrypt.hashpw("test_pwd_placeholder".encode(), bcrypt.gensalt()).decode()
        await db.users.insert_one({
            "user_id": john_uid, "email": "john@testcompany.com", "password_hash": pw,
            "name": "John Doe", "role": "owner", "is_active": True,
            "organization_id": STARTER_ORG_ID, "organizations": [STARTER_ORG_ID],
            "created_at": now, "updated_at": now,
        })
    await db.organization_users.delete_many({"user_id": john_uid})
    await db.organization_users.insert_one({
        "user_id": john_uid, "organization_id": STARTER_ORG_ID,
        "email": "john@testcompany.com", "role": "owner",
        "status": "active", "joined_at": now, "last_active_at": now,
    })
    print("    Done")

    # ================================================================
    # 5. Starter subscription
    # ================================================================
    print("\n[5] Creating starter subscription...")
    await db.subscriptions.delete_many({"organization_id": STARTER_ORG_ID})
    await db.subscriptions.insert_one({
        "subscription_id": "sub_starter_test_001",
        "organization_id": STARTER_ORG_ID,
        "plan_id": "plan_starter_monthly", "plan_code": "starter",
        "plan_name": "Starter", "status": "active", "billing_cycle": "monthly",
        "current_period_start": "2026-01-01T00:00:00+00:00",
        "current_period_end": "2027-01-01T00:00:00+00:00",
        "created_at": "2026-01-01T00:00:00+00:00", "updated_at": now,
    })
    print("    Done")

    # ================================================================
    # 6. Test invoices for credit note tests
    # ================================================================
    print("\n[6] Creating test invoices...")
    test_invoices = [
        {"invoice_id": "inv_d616af1adb14", "invoice_number": "INV-TEST-001",
         "customer_id": "cust_test_001", "customer_name": "Test Customer A",
         "invoice_date": "2026-02-15", "due_date": "2026-03-15", "status": "sent",
         "items": [{"name": "Battery Service", "quantity": 1, "rate": 18000, "tax_rate": 18, "amount": 18000}],
         "subtotal": 18000, "tax_amount": 3240.0, "total_amount": 21240, "total": 21240, "grand_total": 21240,
         "amount_paid": 0, "amount_due": 21240, "balance_due": 21240,
         "cgst_amount": 1620.0, "sgst_amount": 1620.0, "igst_amount": 0, "currency": "INR", "place_of_supply": "07"},
        {"invoice_id": "inv_158dc0a9c5ea", "invoice_number": "INV-TEST-002",
         "customer_id": "cust_test_002", "customer_name": "Test Customer B",
         "invoice_date": "2026-02-10", "due_date": "2026-03-10", "status": "paid",
         "items": [{"name": "Motor Replacement", "quantity": 1, "rate": 15000, "tax_rate": 18, "amount": 15000}],
         "subtotal": 15000, "tax_amount": 2700.0, "total_amount": 17700, "total": 17700, "grand_total": 17700,
         "amount_paid": 17700, "amount_due": 0, "balance_due": 0,
         "cgst_amount": 1350.0, "sgst_amount": 1350.0, "igst_amount": 0, "currency": "INR", "place_of_supply": "07"},
        {"invoice_id": "inv_6ce2fdc798d7", "invoice_number": "INV-TEST-003",
         "customer_id": "cust_test_003", "customer_name": "Test Customer C",
         "invoice_date": "2026-02-20", "due_date": "2026-03-20", "status": "draft",
         "items": [{"name": "Diagnostic Service", "quantity": 1, "rate": 8475, "tax_rate": 18, "amount": 8475}],
         "subtotal": 8475, "tax_amount": 1525.0, "total_amount": 10000, "total": 10000, "grand_total": 10000,
         "amount_paid": 0, "amount_due": 10000, "balance_due": 10000,
         "cgst_amount": 762.5, "sgst_amount": 762.5, "igst_amount": 0, "currency": "INR", "place_of_supply": "07"},
    ]
    for inv in test_invoices:
        inv["organization_id"] = DEV_ORG_ID
        inv["created_at"] = "2026-02-15T10:00:00+00:00"
        inv["updated_at"] = "2026-02-15T10:00:00+00:00"
        await db.invoices_enhanced.delete_many({"invoice_id": inv["invoice_id"]})
        await db.invoices_enhanced.insert_one(inv)
    # Clean stale credit notes for these invoices
    r = await db.credit_notes.delete_many({"original_invoice_id": {"$in": [i["invoice_id"] for i in test_invoices]}})
    if r.deleted_count:
        print(f"    Cleaned {r.deleted_count} stale credit notes")
    await db.journal_entries.delete_many({"organization_id": DEV_ORG_ID, "source_document_type": "credit_note"})
    await db.sequences.delete_many({"organization_id": DEV_ORG_ID, "sequence_type": "credit_note"})
    print("    Done")

    # ================================================================
    # 7. Period lock for January 2026
    # ================================================================
    print("\n[7] Creating period lock...")
    await db.period_locks.delete_many({"org_id": DEV_ORG_ID, "period_month": 1, "period_year": 2026})
    await db.period_locks.delete_many({"organization_id": DEV_ORG_ID, "period_month": 1, "period_year": 2026})
    await db.period_locks.insert_one({
        "lock_id": "plock_test_jan2026_001", "org_id": DEV_ORG_ID, "organization_id": DEV_ORG_ID,
        "period_month": 1, "period_year": 2026,
        "locked_at": "2026-02-01T00:00:00+00:00", "locked_by": "user-dev-owner-001",
        "locked_by_name": "Dev Admin", "lock_reason": "Monthly closing - January 2026",
    })
    print("    Done")

    # ================================================================
    # 8. Contacts (customer + vendor)
    # ================================================================
    print("\n[8] Ensuring contacts...")
    await db.contacts.update_one(
        {"contact_id": "contact_customer_alpha_001"},
        {"$set": {"contact_id": "contact_customer_alpha_001", "organization_id": DEV_ORG_ID,
                  "name": "Alpha Motors Pvt Ltd", "email": "alpha-motors@test.in",
                  "phone": "9800000010", "contact_type": "customer", "is_active": True,
                  "created_at": now, "updated_at": now}},
        upsert=True
    )
    for i, (name, email) in enumerate([("EV Parts Supplier", "supplier@evparts.in"),
                                        ("Battery Wholesale Inc", "orders@batterywholesale.in")], 1):
        await db.contacts.update_one(
            {"contact_id": f"contact_vendor_{i:03d}"},
            {"$set": {"contact_id": f"contact_vendor_{i:03d}", "organization_id": DEV_ORG_ID,
                      "name": name, "email": email, "contact_type": "vendor",
                      "is_active": True, "created_at": now, "updated_at": now}},
            upsert=True
        )
    print("    Done")

    # ================================================================
    # 9. Employees
    # ================================================================
    print("\n[9] Ensuring employees...")
    for i, (name, email) in enumerate([("Deepak Kumar", "deepak@battwheelsgarages.in"),
                                        ("Rahul Singh", "rahul@battwheels.internal")], 1):
        await db.employees.update_one(
            {"employee_id": f"emp_test_{i:03d}"},
            {"$set": {"employee_id": f"emp_test_{i:03d}", "organization_id": DEV_ORG_ID,
                      "name": name, "email": email, "work_email": f"{name.split()[0].lower()}.work@battwheels.internal",
                      "designation": "Technician", "department": "Service", "status": "active",
                      "date_of_joining": "2025-06-01", "basic_salary": 25000 - (i-1)*5000,
                      "created_at": now, "updated_at": now}},
            upsert=True
        )
    print("    Done")

    # ================================================================
    # 10. P0 security test users
    # ================================================================
    print("\n[10] Creating P0 security test users...")
    for email, role, uid in [
        ("admin@battwheels.in", "admin", "user_p0_admin_001"),
        ("tech@battwheels.in", "technician", "user_p0_tech_001"),
    ]:
        pw = bcrypt.hashpw("TestPass@123".encode(), bcrypt.gensalt()).decode()
        await db.users.update_one(
            {"email": email},
            {"$set": {"user_id": uid, "email": email, "password_hash": pw,
                      "name": f"{role.title()} User", "role": role, "is_active": True,
                      "organization_id": DEV_ORG_ID, "organizations": [DEV_ORG_ID],
                      "created_at": now, "updated_at": now}},
            upsert=True
        )
        await db.organization_users.update_one(
            {"user_id": uid, "organization_id": DEV_ORG_ID},
            {"$set": {"user_id": uid, "organization_id": DEV_ORG_ID, "email": email,
                      "role": role, "status": "active", "joined_at": now, "last_active_at": now}},
            upsert=True
        )
        print(f"    Created {email} ({role})")

    # ================================================================
    # Verification
    # ================================================================
    print(f"\n{'=' * 60}")
    print("  VERIFICATION")
    print(f"{'=' * 60}")

    checks = [
        ("Dev user single org",
         await db.organization_users.count_documents({"user_id": DEV_USER_ID}) == 1),
        ("Dev sub professional",
         (await db.subscriptions.find_one({"organization_id": DEV_ORG_ID, "status": "active"}, {"_id": 0})) is not None),
        ("Starter org exists",
         (await db.organizations.find_one({"organization_id": STARTER_ORG_ID})) is not None),
        ("Starter sub exists",
         (await db.subscriptions.find_one({"organization_id": STARTER_ORG_ID, "status": "active"})) is not None),
        ("Test invoices exist",
         await db.invoices_enhanced.count_documents({"invoice_id": {"$in": ["inv_d616af1adb14", "inv_158dc0a9c5ea", "inv_6ce2fdc798d7"]}}) == 3),
        ("Period lock Jan 2026",
         (await db.period_locks.find_one({"org_id": DEV_ORG_ID, "period_month": 1, "period_year": 2026, "unlocked_at": {"$exists": False}})) is not None),
        ("Vendor contacts",
         await db.contacts.count_documents({"organization_id": DEV_ORG_ID, "contact_type": "vendor"}) >= 2),
        ("Employees",
         await db.employees.count_documents({"organization_id": DEV_ORG_ID}) >= 2),
        ("P0 admin user",
         (await db.users.find_one({"email": "admin@battwheels.in"})) is not None),
        ("P0 tech user",
         (await db.users.find_one({"email": "tech@battwheels.in"})) is not None),
    ]
    all_ok = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_ok = False
        print(f"  [{status}] {name}")

    print(f"\n{'=' * 60}")
    print(f"  {'ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED'}")
    print(f"{'=' * 60}")
    client.close()


if __name__ == "__main__":
    asyncio.run(restore())
