"""
Clean Development Database
==========================
Removes test data accumulated from automated test runs while
PRESERVING the following critical orgs and ALL their data:

  1. demo-volt-motors-001  (demo org for user validation)
  2. dev-internal-testing-001  (core test infrastructure org)
  3. org_9c74befbaa95  (starter entitlement test org)
  4. Platform admin user (platform-admin@battwheels.in)

Usage:
    python scripts/clean_dev_database.py --dry-run   # Preview
    python scripts/clean_dev_database.py              # Execute

SAFETY: Hard-coded to ONLY run against battwheels_dev.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

PROTECTED_ORG_IDS = {
    "demo-volt-motors-001",
    "dev-internal-testing-001",
    "org_9c74befbaa95",
}

PROTECTED_EMAILS = {
    "platform-admin@battwheels.in",
    "dev@battwheels.internal",
    "demo@voltmotors.in",
    "tech.a@battwheels.internal",
    "john@testcompany.com",
    "admin@battwheels.in",
    "tech@battwheels.in",
    "deepak@battwheelsgarages.in",
}

ORG_SCOPED_COLLECTIONS = [
    "tickets", "invoices_enhanced", "estimates", "contacts",
    "items", "employees", "payroll_records", "payslips",
    "journal_entries", "chart_of_accounts", "bank_accounts",
    "bank_transactions", "credit_notes", "bills", "bills_enhanced",
    "failure_cards", "knowledge_articles", "sales_orders",
    "purchase_orders", "time_entries", "projects", "tasks",
    "customer_vehicles", "gst_settings", "organization_settings",
    "period_locks", "sequences", "subscriptions",
    "razorpay_config", "payment_orders", "payment_links",
    "webhook_logs",
]


async def clean(dry_run: bool):
    db_name = os.environ.get("DB_NAME", "battwheels_dev")
    if db_name != "battwheels_dev":
        raise Exception(f"SAFETY: This script ONLY runs against battwheels_dev. Got: {db_name}")

    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[db_name]

    mode = "DRY RUN" if dry_run else "LIVE"
    print("=" * 60)
    print(f"  Clean Development Database [{mode}]")
    print(f"  Database: {db_name}")
    print(f"  Protected orgs: {PROTECTED_ORG_IDS}")
    print("=" * 60)

    total_deleted = 0

    # ================================================================
    # 1. Delete test organizations (not in protected set)
    # ================================================================
    print("\n[1] Cleaning test organizations...")
    all_orgs = await db.organizations.find({}, {"_id": 0, "organization_id": 1, "name": 1}).to_list(500)
    test_orgs = [o for o in all_orgs if o["organization_id"] not in PROTECTED_ORG_IDS]
    test_org_ids = [o["organization_id"] for o in test_orgs]

    print(f"    Protected orgs: {len(all_orgs) - len(test_orgs)}")
    print(f"    Test orgs to delete: {len(test_orgs)}")
    for o in test_orgs[:10]:
        print(f"      - {o['organization_id']}: {o.get('name', 'N/A')}")
    if len(test_orgs) > 10:
        print(f"      ... and {len(test_orgs) - 10} more")

    if not dry_run and test_org_ids:
        r = await db.organizations.delete_many({"organization_id": {"$in": test_org_ids}})
        total_deleted += r.deleted_count
        print(f"    Deleted {r.deleted_count} organizations")

    # ================================================================
    # 2. Delete org-scoped data for test organizations
    # ================================================================
    print("\n[2] Cleaning org-scoped data for test organizations...")
    for coll_name in ORG_SCOPED_COLLECTIONS:
        coll = db[coll_name]
        count = await coll.count_documents({"organization_id": {"$in": test_org_ids}}) if test_org_ids else 0
        if count > 0:
            print(f"    {coll_name}: {count} docs")
            if not dry_run:
                r = await coll.delete_many({"organization_id": {"$in": test_org_ids}})
                total_deleted += r.deleted_count

    # ================================================================
    # 3. Delete test users (not in protected emails, not in protected orgs)
    # ================================================================
    print("\n[3] Cleaning test users...")
    test_users_query = {
        "email": {"$nin": list(PROTECTED_EMAILS)},
        "organization_id": {"$nin": list(PROTECTED_ORG_IDS)},
        "is_platform_admin": {"$ne": True},
    }
    test_users = await db.users.find(test_users_query, {"_id": 0, "user_id": 1, "email": 1}).to_list(1000)
    test_user_ids = [u["user_id"] for u in test_users]

    print(f"    Test users to delete: {len(test_users)}")
    for u in test_users[:5]:
        print(f"      - {u['email']} ({u['user_id']})")
    if len(test_users) > 5:
        print(f"      ... and {len(test_users) - 5} more")

    if not dry_run and test_user_ids:
        r = await db.users.delete_many({"user_id": {"$in": test_user_ids}})
        total_deleted += r.deleted_count
        print(f"    Deleted {r.deleted_count} users")

    # ================================================================
    # 4. Delete organization_users for test users/orgs
    # ================================================================
    print("\n[4] Cleaning organization_users...")
    ou_query = {
        "$or": [
            {"organization_id": {"$in": test_org_ids}},
            {"user_id": {"$in": test_user_ids}},
        ]
    } if (test_org_ids or test_user_ids) else {"_id": None}

    ou_count = await db.organization_users.count_documents(ou_query)
    print(f"    organization_users to delete: {ou_count}")
    if not dry_run and ou_count > 0:
        r = await db.organization_users.delete_many(ou_query)
        total_deleted += r.deleted_count
        print(f"    Deleted {r.deleted_count}")

    # ================================================================
    # 5. Clean password_reset_tokens for test users
    # ================================================================
    print("\n[5] Cleaning password reset tokens...")
    token_count = await db.password_reset_tokens.count_documents(
        {"user_id": {"$in": test_user_ids}}
    ) if test_user_ids else 0
    print(f"    Tokens to delete: {token_count}")
    if not dry_run and token_count > 0:
        r = await db.password_reset_tokens.delete_many({"user_id": {"$in": test_user_ids}})
        total_deleted += r.deleted_count

    # ================================================================
    # Summary
    # ================================================================
    print(f"\n{'=' * 60}")
    if dry_run:
        print("  DRY RUN COMPLETE - No data was deleted")
        print("  Run without --dry-run to execute cleanup")
    else:
        print(f"  CLEANUP COMPLETE - Deleted {total_deleted} documents total")

    # Post-cleanup verification
    remaining_orgs = await db.organizations.find({}, {"_id": 0, "organization_id": 1, "name": 1}).to_list(100)
    print(f"\n  Remaining organizations ({len(remaining_orgs)}):")
    for o in remaining_orgs:
        protected = "PROTECTED" if o["organization_id"] in PROTECTED_ORG_IDS else ""
        print(f"    - {o['organization_id']}: {o.get('name', 'N/A')} {protected}")

    remaining_users = await db.users.count_documents({})
    print(f"\n  Remaining users: {remaining_users}")
    print(f"{'=' * 60}")

    client.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(clean(dry_run))
