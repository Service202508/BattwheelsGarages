"""
Migration: Add organization_id indexes to 38 collections missing them.
Run: python -m migrations.add_org_id_indexes

These indexes are critical for:
- Multi-tenant query performance (all queries filter by organization_id)
- Preventing full-collection scans on per-org data
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# Collections missing org_id index (from pre-deployment audit, Feb 2026)
# Excludes global/platform tables: user_sessions, plans, platform_audit_runs
ORG_SCOPED_COLLECTIONS = [
    "composite_items",
    "contact_statements",
    "custom_test_vehicle_tracking",
    "customer_addresses",
    "customer_persons",
    "document_folders",
    "documents",
    "expense_categories",
    "export_data",
    "export_jobs",
    "invoice_comments",
    "invoice_share_links",
    "org_members",
    "organization_invites",
    "payment_modes",
    "project_expenses",
    "project_time_logs",
    "razorpay_configs",
    "razorpay_refunds",
    "recurring_bills",
    "sanitization_audit_log",
    "sanitization_jobs",
    "stocktakes",
    "subscriptions",
    "sync_events",
    "sync_jobs",
    "sync_status",
    "tds_challans",
    "tenant_roles",
    "ticket_reviews",
    "token_vault",
    "units",
    "vehicle_categories",
    "vehicle_models",
    "webhook_logs",
]

# webhook_logs also needs a unique index on razorpay payment_id for idempotency (PY9.03)
UNIQUE_INDEXES = [
    ("webhook_logs", [("payment_id", 1), ("event", 1)], {
        "name": "idx_webhook_logs_payment_event_unique",
        "unique": True,
        # partialFilterExpression: only enforce uniqueness where payment_id exists and is non-null
        # (non-payment events don't have a payment_id so they're excluded from the constraint)
        "partialFilterExpression": {"payment_id": {"$exists": True, "$type": "string"}}
    }),
]


async def run():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    existing_collections = set(await db.list_collection_names())
    created = 0
    skipped = 0
    errors = 0

    print(f"Adding organization_id indexes to {len(ORG_SCOPED_COLLECTIONS)} collections...")

    for coll_name in ORG_SCOPED_COLLECTIONS:
        if coll_name not in existing_collections:
            print(f"  [SKIP] {coll_name} — collection does not exist yet")
            skipped += 1
            continue

        try:
            # Check if org_id index already exists
            indexes = await db[coll_name].index_information()
            has_org_idx = any(
                'organization_id' in str(idx.get('key', {}))
                for idx in indexes.values()
            )
            if has_org_idx:
                print(f"  [SKIP] {coll_name} — index already exists")
                skipped += 1
                continue

            await db[coll_name].create_index(
                [("organization_id", 1)],
                name=f"idx_{coll_name}_org_id",
                background=True
            )
            print(f"  [OK]   {coll_name} — created idx_{coll_name}_org_id")
            created += 1
        except Exception as e:
            print(f"  [ERR]  {coll_name} — {e}")
            errors += 1

    print(f"\nAdding unique idempotency indexes ({len(UNIQUE_INDEXES)} indexes)...")
    for coll_name, keys, opts in UNIQUE_INDEXES:
        if coll_name not in existing_collections:
            print(f"  [SKIP] {coll_name} — does not exist")
            continue
        try:
            await db[coll_name].create_index(keys, **opts)
            print(f"  [OK]   {coll_name} — created {opts['name']}")
            created += 1
        except Exception as e:
            # Index may already exist
            if "already exists" in str(e) or "IndexOptionsConflict" in str(e):
                print(f"  [SKIP] {coll_name} — {opts['name']} already exists")
                skipped += 1
            else:
                print(f"  [ERR]  {coll_name} — {e}")
                errors += 1

    print(f"\nDone. Created: {created}, Skipped: {skipped}, Errors: {errors}")
    client.close()


if __name__ == "__main__":
    asyncio.run(run())
