"""One-time script: purge all test orgs and add missing slug index."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os, pymongo
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

TEST_ORG_IDS = [
    'org_test_onboarding1', 'org_a7752faa402d', 'org_bf635c8cc4ee',
    'org_9560cdd65ee0', 'org_564b587b6860', 'org_ba945034b8a9',
    'org_5f2e219b0a67', 'org_15747fed0f6d', 'org_5f4370a33f71',
    'org_7343e5271e81', 'org_ba4b511ee9ee', 'org_0e3cc3e9283d',
    'org_a731b059acfa', 'org_81ced3ae394b',
]

COLLECTIONS = [
    'tickets', 'invoices', 'contacts_enhanced', 'vehicles', 'inventory_items',
    'journal_entries', 'accounts', 'employees', 'payroll_records',
    'efi_failures', 'efi_diagnoses', 'subscriptions', 'payments',
    'estimates', 'bills', 'expenses', 'ticket_payments', 'ticket_estimates',
    'ticket_activities', 'efi_platform_patterns', 'sequences',
    'sla_configurations', 'pdf_templates', 'whatsapp_logs',
    'email_logs', 'audit_logs', 'survey_responses', 'knowledge_entries',
    'items_enhanced', 'contacts', 'sales_orders', 'purchase_orders',
    'project_tasks', 'projects', 'time_tracking',
]

async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    total = 0

    print("=== PURGING TEST ORGS ===")
    for org_id in TEST_ORG_IDS:
        org = await db.organizations.find_one({'organization_id': org_id}, {'_id': 0, 'name': 1})
        name = org.get('name', 'NOT FOUND') if org else 'NOT FOUND'
        print(f'\n  {org_id} ({name})')
        for col in COLLECTIONS:
            r = await db[col].delete_many({'organization_id': org_id})
            if r.deleted_count:
                print(f'    {col}: -{r.deleted_count}')
                total += r.deleted_count
        await db.organizations.delete_one({'organization_id': org_id})
        ur = await db.users.delete_many({'organization_id': org_id})
        print(f'    org deleted, users deleted: {ur.deleted_count}')

    print(f'\nTotal data records deleted: {total}')

    # Fix slug for production org (battwheels-default → battwheels-garages)
    print("\n=== FIXING PRODUCTION ORG SLUG ===")
    result = await db.organizations.update_one(
        {'organization_id': '6996dcf072ffd2a2395fee7b'},
        {'$set': {'slug': 'battwheels-garages'}}
    )
    print(f'  Slug updated: {result.modified_count} document(s)')

    # Add missing slug index on organizations
    print("\n=== ADDING MISSING SLUG INDEX ===")
    try:
        await db.organizations.create_index(
            [('slug', pymongo.ASCENDING)], unique=True, name='idx_organizations_slug'
        )
        print('  organizations.slug: index created')
    except Exception as e:
        print(f'  organizations.slug: {e}')

    # Final state
    print("\n=== FINAL STATE ===")
    orgs = await db.organizations.find(
        {}, {'_id': 0, 'organization_id': 1, 'name': 1, 'slug': 1}
    ).to_list(None)
    print(f'Remaining orgs ({len(orgs)}):')
    for o in orgs:
        print(f'  {o}')

    users = await db.users.find(
        {}, {'_id': 0, 'email': 1, 'role': 1, 'organization_id': 1}
    ).to_list(None)
    print(f'\nRemaining users ({len(users)}):')
    for u in users:
        print(f'  {u}')

    # Orphan check
    org_ids = [o['organization_id'] for o in orgs]
    orphan_tickets = await db.tickets.count_documents({'organization_id': {'$nin': org_ids}})
    orphan_invoices = await db.invoices.count_documents({'organization_id': {'$nin': org_ids}})
    print(f'\nOrphaned tickets: {orphan_tickets}')
    print(f'Orphaned invoices: {orphan_invoices}')

asyncio.run(main())
