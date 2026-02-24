"""
Battwheels OS — Comprehensive org_id Remap Script
===================================================
Remaps ALL documents with unknown/ghost organization_ids to the known org.
This handles the case where the org was recreated with a new ID.
"""
import asyncio
import os
import argparse
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")

SYSTEM_COLLECTIONS = {
    "organizations", "users", "sequences", "password_reset_tokens",
    "efi_platform_patterns", "plans", "demo_requests", "platform_audit_runs",
    "vehicle_categories", "vehicle_models", "units", "contact_submissions",
    "user_sessions", "system_events"
}


async def remap(db_name: str, dry_run: bool):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[db_name]

    # Get known org
    orgs = await db.organizations.find({}, {"_id": 0, "organization_id": 1, "name": 1}).to_list(None)
    if len(orgs) != 1:
        raise ValueError(f"Expected 1 org, found {len(orgs)}")
    
    known_org = orgs[0]["organization_id"]
    org_name = orgs[0]["name"]
    mode = "DRY RUN" if dry_run else "EXECUTE"

    print(f"\n{'='*70}")
    print(f"  org_id REMAP — {mode}")
    print(f"  Database: {db_name}")
    print(f"  Known org: {org_name} ({known_org})")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}\n")

    # Phase 1: Find all unknown org_ids
    all_cols = sorted(await db.list_collection_names())
    ghost_ids = set()
    
    for col in all_cols:
        if col in SYSTEM_COLLECTIONS:
            continue
        pipeline = [
            {"$match": {"organization_id": {"$exists": True, "$ne": known_org}}},
            {"$group": {"_id": "$organization_id"}}
        ]
        results = await db[col].aggregate(pipeline).to_list(None)
        for r in results:
            if r["_id"] is not None:
                ghost_ids.add(r["_id"])
    
    print(f"  Ghost org_ids found: {len(ghost_ids)}")
    for gid in sorted(ghost_ids):
        print(f"    - {gid}")
    
    if not ghost_ids:
        print("\n  No ghost org_ids found. Nothing to remap.")
        return 0

    # Phase 2: Remap each collection
    print(f"\n  REMAPPING:")
    total_remapped = 0
    
    for col in all_cols:
        if col in SYSTEM_COLLECTIONS:
            continue
        
        count = await db[col].count_documents(
            {"organization_id": {"$in": list(ghost_ids)}}
        )
        if count == 0:
            continue
        
        if dry_run:
            print(f"    [DRY RUN] {col}: {count} documents would be remapped")
            total_remapped += count
        else:
            result = await db[col].update_many(
                {"organization_id": {"$in": list(ghost_ids)}},
                {"$set": {"organization_id": known_org}}
            )
            print(f"    [REMAPPED] {col}: {result.modified_count} documents")
            total_remapped += result.modified_count

    # Phase 3: Also stamp any remaining docs without org_id
    print(f"\n  STAMPING REMAINING (no org_id):")
    total_stamped = 0
    
    for col in all_cols:
        if col in SYSTEM_COLLECTIONS:
            continue
        count = await db[col].count_documents({"organization_id": {"$exists": False}})
        if count == 0:
            continue
        
        if dry_run:
            print(f"    [DRY RUN] {col}: {count} documents would be stamped")
            total_stamped += count
        else:
            result = await db[col].update_many(
                {"organization_id": {"$exists": False}},
                {"$set": {"organization_id": known_org}}
            )
            print(f"    [STAMPED] {col}: {result.modified_count} documents")
            total_stamped += result.modified_count

    print(f"\n{'='*70}")
    print(f"  SUMMARY — {mode}")
    print(f"  Documents {'would be ' if dry_run else ''}remapped: {total_remapped}")
    print(f"  Documents {'would be ' if dry_run else ''}stamped: {total_stamped}")
    print(f"  Total {'would be ' if dry_run else ''}fixed: {total_remapped + total_stamped}")
    print(f"{'='*70}")

    # Phase 4: Post-remap verification
    if not dry_run:
        print(f"\n  POST-REMAP VERIFICATION:")
        issues = 0
        for col in all_cols:
            if col in SYSTEM_COLLECTIONS:
                continue
            count = await db[col].count_documents({})
            if count == 0:
                continue
            
            no_org = await db[col].count_documents({"organization_id": {"$exists": False}})
            unknown = await db[col].count_documents(
                {"organization_id": {"$exists": True, "$ne": known_org}}
            )
            
            if no_org > 0 or unknown > 0:
                print(f"    FAIL: {col} — {no_org} without org_id, {unknown} with unknown org_id")
                issues += 1
        
        if issues == 0:
            print(f"    PASS: ALL tenant documents belong to {org_name}")
        else:
            print(f"    FAIL: {issues} collections still have issues")

        # Trial balance
        entries = await db.journal_entries.find({}).to_list(None)
        if entries:
            total_dr = sum(e.get("debit_amount", 0) for e in entries)
            total_cr = sum(e.get("credit_amount", 0) for e in entries)
            diff = abs(total_dr - total_cr)
            status = "BALANCED" if diff < 0.01 else f"UNBALANCED by {diff:.2f}"
            print(f"    TRIAL BALANCE: {status} (DR: {total_dr:,.2f} / CR: {total_cr:,.2f})")
        else:
            print(f"    TRIAL BALANCE: No journal entries")
    
    return total_remapped + total_stamped


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: Must specify --dry-run or --execute")
        exit(1)

    asyncio.run(remap(args.db, dry_run=args.dry_run))
