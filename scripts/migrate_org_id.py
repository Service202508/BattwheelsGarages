"""
Battwheels OS — org_id Migration Script
========================================
Stamps all legacy documents missing `organization_id` with the correct org_id.

Usage:
  python3 scripts/migrate_org_id.py --db battwheels_dev --dry-run
  python3 scripts/migrate_org_id.py --db battwheels_dev --execute
  python3 scripts/migrate_org_id.py --db battwheels --execute
"""
import asyncio
import os
import argparse
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")

# Collections that are SYSTEM-level and should NEVER get organization_id
SYSTEM_COLLECTIONS = {
    "organizations",
    "users",                    # Users map to orgs via organization_users
    "sequences",                # Already has organization_id where needed
    "password_reset_tokens",    # User-level, not org-level
    "efi_platform_patterns",    # Intentionally shared across all tenants
    "plans",                    # Platform-level subscription plans
    "demo_requests",            # Public website form submissions
    "platform_audit_runs",      # Platform admin
    "vehicle_categories",       # Shared EV reference data
    "vehicle_models",           # Shared EV reference data
    "units",                    # Shared measurement units
    "contact_submissions",      # Public website form submissions
    "user_sessions",            # User-level, not org-level
    "system_events",            # Platform-level
}

async def get_org_id(db, explicit_org_id=None):
    """Get the organization_id to stamp documents with."""
    orgs = await db.organizations.find({}, {"_id": 0, "organization_id": 1, "name": 1}).to_list(None)
    if len(orgs) == 0:
        raise ValueError("No organizations found in database")
    
    if explicit_org_id:
        match = [o for o in orgs if o["organization_id"] == explicit_org_id]
        if not match:
            raise ValueError(f"org_id '{explicit_org_id}' not found in database")
        return match[0]["organization_id"], match[0]["name"]
    
    if len(orgs) > 1:
        raise ValueError(f"Multiple organizations found ({len(orgs)}). Use --org-id to specify which one.")
    return orgs[0]["organization_id"], orgs[0]["name"]


async def migrate(db_name: str, dry_run: bool, explicit_org_id: str = None):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[db_name]

    org_id, org_name = await get_org_id(db, explicit_org_id)
    mode = "DRY RUN" if dry_run else "EXECUTE"
    
    print(f"\n{'='*70}")
    print(f"  org_id MIGRATION — {mode}")
    print(f"  Database: {db_name}")
    print(f"  Target org: {org_name} ({org_id})")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}\n")

    all_collections = sorted(await db.list_collection_names())
    
    total_stamped = 0
    results = []

    for col_name in all_collections:
        if col_name in SYSTEM_COLLECTIONS:
            continue

        count = await db[col_name].count_documents({})
        if count == 0:
            continue

        missing = await db[col_name].count_documents({"organization_id": {"$exists": False}})
        if missing == 0:
            continue

        # This collection has documents without organization_id
        if dry_run:
            print(f"  [DRY RUN] {col_name}: {missing}/{count} documents would be stamped")
            results.append({"collection": col_name, "stamped": missing, "total": count})
            total_stamped += missing
        else:
            # Execute the migration for this collection
            result = await db[col_name].update_many(
                {"organization_id": {"$exists": False}},
                {"$set": {"organization_id": org_id}}
            )
            actual = result.modified_count
            print(f"  [STAMPED] {col_name}: {actual}/{count} documents stamped with org_id")
            results.append({"collection": col_name, "stamped": actual, "total": count})
            total_stamped += actual

            # Verify: no documents should be missing org_id now
            remaining = await db[col_name].count_documents({"organization_id": {"$exists": False}})
            if remaining > 0:
                print(f"    WARNING: {remaining} documents still missing org_id in {col_name}!")

    print(f"\n{'='*70}")
    print(f"  SUMMARY — {mode}")
    print(f"  Collections processed: {len(results)}")
    print(f"  Total documents {'would be ' if dry_run else ''}stamped: {total_stamped}")
    print(f"{'='*70}")

    # Post-migration verification
    if not dry_run:
        print(f"\n  POST-MIGRATION VERIFICATION:")
        issues = 0
        for col_name in all_collections:
            if col_name in SYSTEM_COLLECTIONS:
                continue
            count = await db[col_name].count_documents({})
            if count == 0:
                continue
            missing = await db[col_name].count_documents({"organization_id": {"$exists": False}})
            if missing > 0:
                print(f"    FAIL: {col_name} still has {missing} documents without org_id")
                issues += 1
        
        if issues == 0:
            print(f"    PASS: All tenant documents have organization_id")
        else:
            print(f"    FAIL: {issues} collections still have issues")

        # Trial balance check
        entries = await db.journal_entries.find({}).to_list(None)
        if entries:
            total_dr = sum(e.get("debit_amount", 0) for e in entries)
            total_cr = sum(e.get("credit_amount", 0) for e in entries)
            diff = abs(total_dr - total_cr)
            if diff < 0.01:
                print(f"    TRIAL BALANCE: BALANCED (DR: {total_dr:,.2f} / CR: {total_cr:,.2f})")
            else:
                print(f"    TRIAL BALANCE: UNBALANCED by {diff:.2f}!")
        else:
            print(f"    TRIAL BALANCE: No journal entries (balanced by default)")

    return total_stamped, results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stamp missing organization_id on legacy documents")
    parser.add_argument("--db", required=True, help="Database name (battwheels or battwheels_dev)")
    parser.add_argument("--dry-run", action="store_true", help="Count only, don't modify")
    parser.add_argument("--execute", action="store_true", help="Actually stamp the documents")
    parser.add_argument("--org-id", type=str, default=None, help="Explicit org_id (required when DB has multiple orgs)")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: Must specify --dry-run or --execute")
        exit(1)
    if args.dry_run and args.execute:
        print("ERROR: Cannot specify both --dry-run and --execute")
        exit(1)

    asyncio.run(migrate(args.db, dry_run=args.dry_run, explicit_org_id=args.org_id))
