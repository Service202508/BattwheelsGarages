"""Purge audit org created during final walkthrough testing."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

AUDIT_ORG_ID = "org_545d5b59ccf8"

COLLECTIONS = [
    'tickets', 'invoices', 'contacts_enhanced', 'vehicles', 'inventory_items',
    'journal_entries', 'accounts', 'employees', 'payroll_records',
    'efi_failures', 'efi_diagnoses', 'subscriptions', 'payments',
    'estimates', 'bills', 'expenses', 'ticket_payments', 'ticket_estimates',
    'ticket_activities', 'efi_platform_patterns', 'sequences',
    'sla_configurations', 'pdf_templates', 'items_enhanced',
    'contacts', 'sales_orders', 'purchase_orders', 'project_tasks',
    'projects', 'time_tracking', 'invoice_payments',
]

async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    total = 0
    print(f"Purging audit org: {AUDIT_ORG_ID}")
    for col in COLLECTIONS:
        r = await db[col].delete_many({'organization_id': AUDIT_ORG_ID})
        if r.deleted_count:
            print(f"  {col}: -{r.deleted_count}")
            total += r.deleted_count

    await db.organizations.delete_one({'organization_id': AUDIT_ORG_ID})
    ur = await db.users.delete_many({'organization_id': AUDIT_ORG_ID})
    print(f"  org deleted, users deleted: {ur.deleted_count}")
    print(f"Total records deleted: {total}")

    # Also delete the test Book Demo lead created during Flow 16
    r = await db.demo_requests.delete_many({'phone': '9999999999'})
    print(f"Test demo request deleted: {r.deleted_count}")

    # Final state
    orgs = await db.organizations.find({}, {'_id': 0, 'name': 1, 'organization_id': 1}).to_list(None)
    print(f"\nFinal orgs ({len(orgs)}): {[o['name'] for o in orgs]}")

    # Orphan check
    org_ids = [o['organization_id'] for o in orgs]
    for col in ['tickets', 'invoices', 'journal_entries']:
        orphans = await db[col].count_documents({'organization_id': {'$nin': org_ids}})
        if orphans:
            print(f"WARNING: {col} has {orphans} orphaned records!")
    print("Orphan check complete — no orphans expected")

asyncio.run(main())
