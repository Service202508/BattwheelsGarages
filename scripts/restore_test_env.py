"""
Restore Test Environment for Battwheels OS Core Test Suite
==========================================================
This script restores all data required by the test suite for
the `dev-internal-testing-001` organization and the `org_9c74befbaa95`
starter test org.

Usage:
    python scripts/restore_test_env.py

SAFETY: Hard-coded to ONLY run against battwheels_dev.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
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
    #    The dev user must ONLY be a member of dev-internal-testing-001
    # ================================================================
    print("\n[1] Cleaning spurious org memberships for dev user...")
    result = await db.organization_users.delete_many({
        "user_id": DEV_USER_ID,
        "organization_id": {"$ne": DEV_ORG_ID}
    })
    print(f"    Removed {result.deleted_count} spurious memberships")

    # Ensure the dev user's membership in dev org has last_active_at set
    await db.organization_users.update_one(
        {"user_id": DEV_USER_ID, "organization_id": DEV_ORG_ID},
        {"$set": {"last_active_at": now}}
    )
    print("    Updated last_active_at for dev user in dev org")

    # ================================================================
    # 2. Fix subscription for dev-internal-testing-001
    #    Must have subscription_id, plan_code, billing_cycle
    # ================================================================
    print("\n[2] Fixing subscription for dev org...")
    await db.subscriptions.delete_many({"organization_id": DEV_ORG_ID})
    dev_sub = {
        "subscription_id": "sub_dev_professional_001",
        "organization_id": DEV_ORG_ID,
        "plan_id": "plan_professional_monthly",
        "plan_code": "professional",
        "plan_name": "Professional",
        "status": "active",
        "billing_cycle": "monthly",
        "current_period_start": "2026-01-01T00:00:00+00:00",
        "current_period_end": "2027-01-01T00:00:00+00:00",
        "trial_start": "2026-01-01T00:00:00+00:00",
        "trial_end": "2027-01-01T00:00:00+00:00",
        "features": [
            "advanced_invoicing", "hr_payroll", "gst_compliance",
            "efi_intelligence", "banking", "inventory", "api_access",
            "accounting_module", "project_management"
        ],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": now,
    }
    await db.subscriptions.insert_one(dev_sub)
    print(f"    Created subscription: {dev_sub['subscription_id']}")

    # Also ensure the org doc has plan=professional
    await db.organizations.update_one(
        {"organization_id": DEV_ORG_ID},
        {"$set": {
            "plan": "professional",
            "plan_type": "professional",
            "subscription_status": "active",
        }}
    )
    print("    Updated org doc with plan=professional")

    # ================================================================
    # 3. Create starter test org (org_9c74befbaa95)
    # ================================================================
    print("\n[3] Creating starter test org...")
    existing_starter_org = await db.organizations.find_one(
        {"organization_id": STARTER_ORG_ID}
    )
    if not existing_starter_org:
        starter_org = {
            "organization_id": STARTER_ORG_ID,
            "name": "TestCompany",
            "slug": "testcompany",
            "industry_type": "ev_garage",
            "plan": "starter",
            "plan_type": "starter",
            "subscription_status": "active",
            "is_active": True,
            "is_onboarded": True,
            "created_at": now,
            "updated_at": now,
            "city": "Test City",
            "country": "India",
            "settings": {
                "currency": "INR",
                "timezone": "Asia/Kolkata",
                "date_format": "DD/MM/YYYY",
                "fiscal_year_start": "April",
            },
            "features": {
                "zoho_sync": False,
                "ai_assistant": True,
                "failure_intelligence": True,
                "multi_warehouse": False,
                "advanced_reports": False,
            },
        }
        await db.organizations.insert_one(starter_org)
        print(f"    Created org: {STARTER_ORG_ID}")
    else:
        print(f"    Org {STARTER_ORG_ID} already exists")

    # ================================================================
    # 4. Update john@testcompany.com user to belong to starter org
    # ================================================================
    print("\n[4] Configuring john@testcompany.com for starter org...")
    john_user = await db.users.find_one({"email": "john@testcompany.com"})
    john_user_id = "user_john_test_001"
    if john_user:
        await db.users.update_one(
            {"email": "john@testcompany.com"},
            {"$set": {
                "organization_id": STARTER_ORG_ID,
                "organizations": [STARTER_ORG_ID],
            }}
        )
        john_user_id = john_user.get("user_id", john_user_id)
        print(f"    Updated john's org to {STARTER_ORG_ID}")
    else:
        import bcrypt
        pw_hash = bcrypt.hashpw("test_pwd_placeholder".encode(), bcrypt.gensalt()).decode()
        john_doc = {
            "user_id": john_user_id,
            "email": "john@testcompany.com",
            "password_hash": pw_hash,
            "name": "John Doe",
            "role": "owner",
            "designation": "Owner",
            "is_active": True,
            "organization_id": STARTER_ORG_ID,
            "organizations": [STARTER_ORG_ID],
            "created_at": now,
            "updated_at": now,
        }
        await db.users.insert_one(john_doc)
        print(f"    Created john user: {john_user_id}")

    # Create/update organization_users for john in starter org
    await db.organization_users.delete_many({"user_id": john_user_id})
    await db.organization_users.insert_one({
        "user_id": john_user_id,
        "organization_id": STARTER_ORG_ID,
        "email": "john@testcompany.com",
        "role": "owner",
        "status": "active",
        "joined_at": now,
        "last_active_at": now,
    })
    print(f"    Created org_users entry for john in {STARTER_ORG_ID}")

    # ================================================================
    # 5. Create starter subscription for org_9c74befbaa95
    # ================================================================
    print("\n[5] Creating starter subscription for starter org...")
    await db.subscriptions.delete_many({"organization_id": STARTER_ORG_ID})
    starter_sub = {
        "subscription_id": "sub_starter_test_001",
        "organization_id": STARTER_ORG_ID,
        "plan_id": "plan_starter_monthly",
        "plan_code": "starter",
        "plan_name": "Starter",
        "status": "active",
        "billing_cycle": "monthly",
        "current_period_start": "2026-01-01T00:00:00+00:00",
        "current_period_end": "2027-01-01T00:00:00+00:00",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": now,
    }
    await db.subscriptions.insert_one(starter_sub)
    print(f"    Created subscription: {starter_sub['subscription_id']}")

    # ================================================================
    # 6. Create test invoices for credit note tests
    # ================================================================
    print("\n[6] Creating test invoices for credit note tests...")
    test_invoices = [
        {
            "invoice_id": "inv_d616af1adb14",
            "invoice_number": "INV-TEST-001",
            "organization_id": DEV_ORG_ID,
            "customer_id": "cust_test_001",
            "customer_name": "Test Customer A",
            "invoice_date": "2026-02-15",
            "due_date": "2026-03-15",
            "status": "sent",
            "items": [
                {"name": "Battery Service", "quantity": 1, "rate": 18000, "tax_rate": 18, "amount": 18000}
            ],
            "subtotal": 18000,
            "tax_amount": 3240.0,
            "cgst_amount": 1620.0,
            "sgst_amount": 1620.0,
            "igst_amount": 0,
            "total_amount": 21240,
            "amount_paid": 0,
            "amount_due": 21240,
            "currency": "INR",
            "place_of_supply": "07",
            "created_at": "2026-02-15T10:00:00+00:00",
            "updated_at": "2026-02-15T10:00:00+00:00",
        },
        {
            "invoice_id": "inv_158dc0a9c5ea",
            "invoice_number": "INV-TEST-002",
            "organization_id": DEV_ORG_ID,
            "customer_id": "cust_test_002",
            "customer_name": "Test Customer B",
            "invoice_date": "2026-02-10",
            "due_date": "2026-03-10",
            "status": "paid",
            "items": [
                {"name": "Motor Replacement", "quantity": 1, "rate": 15000, "tax_rate": 18, "amount": 15000}
            ],
            "subtotal": 15000,
            "tax_amount": 2700.0,
            "cgst_amount": 1350.0,
            "sgst_amount": 1350.0,
            "igst_amount": 0,
            "total_amount": 17700,
            "amount_paid": 17700,
            "amount_due": 0,
            "currency": "INR",
            "place_of_supply": "07",
            "created_at": "2026-02-10T10:00:00+00:00",
            "updated_at": "2026-02-10T10:00:00+00:00",
        },
        {
            "invoice_id": "inv_6ce2fdc798d7",
            "invoice_number": "INV-TEST-003",
            "organization_id": DEV_ORG_ID,
            "customer_id": "cust_test_003",
            "customer_name": "Test Customer C",
            "invoice_date": "2026-02-20",
            "due_date": "2026-03-20",
            "status": "draft",
            "items": [
                {"name": "Diagnostic Service", "quantity": 1, "rate": 8475, "tax_rate": 18, "amount": 8475}
            ],
            "subtotal": 8475,
            "tax_amount": 1525.0,
            "cgst_amount": 762.5,
            "sgst_amount": 762.5,
            "igst_amount": 0,
            "total_amount": 10000,
            "amount_paid": 0,
            "amount_due": 10000,
            "currency": "INR",
            "place_of_supply": "07",
            "created_at": "2026-02-20T10:00:00+00:00",
            "updated_at": "2026-02-20T10:00:00+00:00",
        },
    ]
    for inv in test_invoices:
        await db.invoices_enhanced.delete_many({"invoice_id": inv["invoice_id"]})
        await db.invoices_enhanced.insert_one(inv)
        print(f"    Created invoice: {inv['invoice_id']} ({inv['status']}, total={inv['total_amount']})")

    # ================================================================
    # 7. Create period lock for January 2026
    # ================================================================
    print("\n[7] Creating period lock for January 2026...")
    await db.period_locks.delete_many({
        "org_id": DEV_ORG_ID,
        "period_month": 1,
        "period_year": 2026
    })
    # Also check organization_id variant
    await db.period_locks.delete_many({
        "organization_id": DEV_ORG_ID,
        "period_month": 1,
        "period_year": 2026
    })
    lock_doc = {
        "lock_id": "plock_test_jan2026_001",
        "org_id": DEV_ORG_ID,
        "organization_id": DEV_ORG_ID,
        "period_month": 1,
        "period_year": 2026,
        "locked_at": "2026-02-01T00:00:00+00:00",
        "locked_by": "user-dev-owner-001",
        "locked_by_name": "Dev Admin",
        "lock_reason": "Monthly closing - January 2026",
    }
    await db.period_locks.insert_one(lock_doc)
    print(f"    Created period lock: {lock_doc['lock_id']} (Jan 2026)")

    # ================================================================
    # 8. Ensure contacts/customers exist for multi-tenant scoping tests
    # ================================================================
    print("\n[8] Ensuring contacts exist for dev org...")
    contact_count = await db.contacts.count_documents({"organization_id": DEV_ORG_ID})
    if contact_count == 0:
        test_contacts = [
            {
                "contact_id": f"contact_test_{i:03d}",
                "organization_id": DEV_ORG_ID,
                "name": f"Test Contact {i}",
                "email": f"contact{i}@test.com",
                "phone": f"99000000{i:02d}",
                "contact_type": "customer",
                "created_at": now,
                "updated_at": now,
            }
            for i in range(1, 4)
        ]
        await db.contacts.insert_many(test_contacts)
        print(f"    Created {len(test_contacts)} test contacts")
    else:
        print(f"    Contacts already exist: {contact_count}")

    # ================================================================
    # 9. Ensure items/inventory exist for multi-tenant scoping tests
    # ================================================================
    print("\n[9] Ensuring inventory items exist for dev org...")
    item_count = await db.items.count_documents({"organization_id": DEV_ORG_ID})
    if item_count == 0:
        test_items = [
            {
                "item_id": f"item_test_{i:03d}",
                "organization_id": DEV_ORG_ID,
                "name": f"Test Item {i}",
                "sku": f"SKU-TEST-{i:03d}",
                "unit_price": 1000 * i,
                "quantity": 10,
                "created_at": now,
                "updated_at": now,
            }
            for i in range(1, 4)
        ]
        await db.items.insert_many(test_items)
        print(f"    Created {len(test_items)} test items")
    else:
        print(f"    Items already exist: {item_count}")

    # ================================================================
    # 10. Final verification
    # ================================================================
    print(f"\n{'=' * 60}")
    print("  POST-RESTORE VERIFICATION")
    print(f"{'=' * 60}")

    # Verify dev user's org resolution
    dev_memberships = await db.organization_users.find(
        {"user_id": DEV_USER_ID, "status": "active"},
        {"_id": 0, "organization_id": 1}
    ).to_list(20)
    dev_orgs = [m["organization_id"] for m in dev_memberships]
    print(f"  Dev user orgs: {dev_orgs}")
    assert DEV_ORG_ID in dev_orgs, f"Dev user must be in {DEV_ORG_ID}"
    assert len(dev_orgs) == 1, f"Dev user should only be in 1 org, found: {dev_orgs}"

    # Verify subscriptions
    dev_sub_check = await db.subscriptions.find_one(
        {"organization_id": DEV_ORG_ID, "status": "active"},
        {"_id": 0, "subscription_id": 1, "plan_code": 1}
    )
    print(f"  Dev sub: {dev_sub_check}")
    assert dev_sub_check and dev_sub_check.get("plan_code") == "professional"

    starter_sub_check = await db.subscriptions.find_one(
        {"organization_id": STARTER_ORG_ID, "status": "active"},
        {"_id": 0, "subscription_id": 1, "plan_code": 1}
    )
    print(f"  Starter sub: {starter_sub_check}")
    assert starter_sub_check and starter_sub_check.get("plan_code") == "starter"

    # Verify invoices
    for iid in ["inv_d616af1adb14", "inv_158dc0a9c5ea", "inv_6ce2fdc798d7"]:
        inv = await db.invoices_enhanced.find_one({"invoice_id": iid}, {"_id": 0, "invoice_id": 1, "status": 1})
        print(f"  Invoice {iid}: {inv}")
        assert inv is not None

    # Verify period lock
    lock_check = await db.period_locks.find_one(
        {"org_id": DEV_ORG_ID, "period_month": 1, "period_year": 2026, "unlocked_at": {"$exists": False}},
        {"_id": 0, "lock_id": 1}
    )
    print(f"  Period lock (Jan 2026): {lock_check}")
    assert lock_check is not None

    # Verify john user
    john_check = await db.users.find_one(
        {"email": "john@testcompany.com"},
        {"_id": 0, "user_id": 1, "organization_id": 1}
    )
    print(f"  John user: {john_check}")
    assert john_check and john_check.get("organization_id") == STARTER_ORG_ID

    print(f"\n{'=' * 60}")
    print("  ALL VERIFICATIONS PASSED")
    print(f"{'=' * 60}")

    client.close()


if __name__ == "__main__":
    asyncio.run(restore())
