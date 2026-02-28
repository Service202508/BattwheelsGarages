# Sprint 6D-02: Clean dev database
# Removes test data accumulation while preserving demo org and legitimate data.
#
# Usage:
#   python scripts/clean_dev_database.py --dry-run   # preview deletions
#   python scripts/clean_dev_database.py              # execute deletions
#
# SAFETY: Hard-coded to ONLY run against battwheels_dev.

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

PROTECTED_ORG_IDS = {
    "demo-volt-motors-001",  # Demo org (Volt Motors)
}

PROTECTED_USERS = {
    "platform-admin@battwheels.in",
    "demo@voltmotors.in",
}

TEST_TICKET_PATTERNS = [
    {"title": {"$regex": "^TEST_"}},
    {"title": {"$regex": "^Tech-Other-"}},
    {"title": {"$regex": "^Tech-Own-"}},
    {"title": {"$regex": "^CrossTenant-"}},
    {"title": {"$regex": "^Smoke Test"}},
    {"title": {"$regex": "^Tenant Context Test"}},
    {"title": {"$regex": "^SE4\\.05 XSS"}},
    {"title": {"$regex": "^alert\\("}},
    {"title": {"$regex": "^&lt;alert"}},
    {"title": {"$regex": "^<script"}},
    {"title": {"$regex": "^Normal Battery Overheating"}},
]

# Collections to clean by org_id (delete all docs not in protected orgs)
ORG_SCOPED_COLLECTIONS = [
    "contacts", "items", "estimates", "estimates_enhanced",
    "sales_orders", "purchase_orders", "payments", "expenses",
    "attendance", "leave_requests", "payroll_runs", "payroll_slips",
    "bank_accounts", "bank_transactions", "reconciliation_sessions",
    "efi_learning_queue", "efi_sessions",
    "period_locks", "organization_settings", "chart_of_accounts",
    "notifications", "time_entries",
]


async def clean(dry_run: bool):
    db_name = os.environ.get("DB_NAME", "battwheels_dev")
    if db_name != "battwheels_dev":
        raise Exception(f"SAFETY: This script ONLY runs against battwheels_dev. Got: {db_name}")

    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[db_name]

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"{'='*60}")
    print(f"  Dev Database Cleanup [{mode}]")
    print(f"  Database: {db_name}")
    print(f"  Protected orgs: {PROTECTED_ORG_IDS}")
    print(f"{'='*60}")

    # 1. Identify test organizations (all except protected)
    all_orgs = await db.organizations.find(
        {"organization_id": {"$nin": list(PROTECTED_ORG_IDS)}},
        {"_id": 0, "organization_id": 1, "name": 1}
    ).to_list(5000)
    test_org_ids = [o["organization_id"] for o in all_orgs]
    print(f"\n[1] Test organizations to delete: {len(test_org_ids)}")
    for o in all_orgs[:5]:
        print(f"    {o['organization_id']}: {o.get('name','')}")
    if len(all_orgs) > 5:
        print(f"    ... and {len(all_orgs) - 5} more")

    # 2. Delete test tickets (by pattern + by test org)
    test_ticket_filter = {"$or": TEST_TICKET_PATTERNS}
    pattern_count = await db.tickets.count_documents(test_ticket_filter)

    org_ticket_filter = {"organization_id": {"$in": test_org_ids}}
    org_ticket_count = await db.tickets.count_documents(org_ticket_filter)

    combined_filter = {"$or": [test_ticket_filter, org_ticket_filter]}
    total_ticket_del = await db.tickets.count_documents(combined_filter)

    print(f"\n[2] Tickets to delete: {total_ticket_del}")
    print(f"    By pattern: {pattern_count}")
    print(f"    By test org: {org_ticket_count}")

    if not dry_run:
        r = await db.tickets.delete_many(combined_filter)
        print(f"    Deleted: {r.deleted_count}")

    # 3. Delete invoices in test orgs
    inv_count = await db.invoices_enhanced.count_documents({"organization_id": {"$in": test_org_ids}})
    print(f"\n[3] Invoices to delete (test orgs): {inv_count}")
    if not dry_run and inv_count > 0:
        r = await db.invoices_enhanced.delete_many({"organization_id": {"$in": test_org_ids}})
        print(f"    Deleted: {r.deleted_count}")

    # 4. Delete employees in test orgs
    emp_count = await db.employees.count_documents({"organization_id": {"$in": test_org_ids}})
    print(f"\n[4] Employees to delete (test orgs): {emp_count}")
    if not dry_run and emp_count > 0:
        r = await db.employees.delete_many({"organization_id": {"$in": test_org_ids}})
        print(f"    Deleted: {r.deleted_count}")

    # 5. Delete users in test orgs (except protected)
    user_filter = {
        "email": {"$nin": list(PROTECTED_USERS)},
        "is_platform_admin": {"$ne": True},
        "$or": [
            {"organization_id": {"$in": test_org_ids}},
            {"organizations": {"$elemMatch": {"$in": test_org_ids}}},
        ]
    }
    user_count = await db.users.count_documents(user_filter)
    print(f"\n[5] Users to delete (test orgs, non-protected): {user_count}")
    if not dry_run and user_count > 0:
        r = await db.users.delete_many(user_filter)
        print(f"    Deleted: {r.deleted_count}")

    # Also delete orphan users not in any protected org
    orphan_filter = {
        "email": {"$nin": list(PROTECTED_USERS)},
        "is_platform_admin": {"$ne": True},
        "organization_id": {"$nin": list(PROTECTED_ORG_IDS)},
    }

    # 6. Delete org-scoped collection data for test orgs
    print(f"\n[6] Org-scoped collections cleanup:")
    for coll_name in ORG_SCOPED_COLLECTIONS:
        count = await db[coll_name].count_documents({"organization_id": {"$in": test_org_ids}})
        if count > 0:
            print(f"    {coll_name}: {count} docs to delete")
            if not dry_run:
                r = await db[coll_name].delete_many({"organization_id": {"$in": test_org_ids}})
                print(f"      Deleted: {r.deleted_count}")

    # 7. Delete the test organizations themselves
    print(f"\n[7] Organizations to delete: {len(test_org_ids)}")
    if not dry_run:
        r = await db.organizations.delete_many({"organization_id": {"$in": test_org_ids}})
        print(f"    Deleted: {r.deleted_count}")

    # 8. Delete subscriptions for test orgs
    sub_count = await db.subscriptions.count_documents({"organization_id": {"$in": test_org_ids}})
    print(f"\n[8] Subscriptions to delete: {sub_count}")
    if not dry_run and sub_count > 0:
        r = await db.subscriptions.delete_many({"organization_id": {"$in": test_org_ids}})
        print(f"    Deleted: {r.deleted_count}")

    # 9. Final counts
    print(f"\n{'='*60}")
    print(f"  POST-CLEANUP COUNTS")
    print(f"{'='*60}")
    for coll_name in ["tickets", "invoices_enhanced", "employees", "failure_cards",
                       "knowledge_articles", "users", "organizations"]:
        count = await db[coll_name].count_documents({})
        print(f"  {coll_name}: {count}")

    client.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(clean(dry_run))
