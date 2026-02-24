"""
Read-only verification that production org data is intact.
Run before and after every deployment.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

PROD_ORG_SLUG = "battwheels-garages"


async def verify():
    url = os.environ.get("MONGO_URL")
    if not url:
        print("ERROR: MONGO_URL environment variable not set.")
        return

    db_name = os.environ.get("DB_NAME", "battwheels")
    client = AsyncIOMotorClient(url)
    db = client[db_name]

    org = await db.organizations.find_one(
        {"slug": PROD_ORG_SLUG},
        {"_id": 0}
    )

    if not org:
        print("CRITICAL: Production org 'battwheels-garages' NOT FOUND")
        client.close()
        return

    org_id = org["organization_id"]

    checks = {
        "tickets": await db.tickets.count_documents({"organization_id": org_id}),
        "invoices": await db.invoices.count_documents({"organization_id": org_id}),
        "journal_entries": await db.journal_entries.count_documents({"organization_id": org_id}),
        "users": await db.users.count_documents({"organization_id": org_id}),
        "contacts": await db.contacts.count_documents({"organization_id": org_id}),
    }

    # Check for test data contamination
    test_tickets = await db.tickets.count_documents({
        "organization_id": org_id,
        "$or": [
            {"customer_name": {"$regex": "test|demo|dummy", "$options": "i"}},
            {"complaint": {"$regex": "test|audit|dummy", "$options": "i"}},
        ]
    })

    demo_orgs = await db.organizations.count_documents({
        "$or": [
            {"is_demo": True},
            {"is_dev": True},
        ]
    })

    print(f"\n{'='*54}")
    print(f" PRODUCTION ORG HEALTH CHECK")
    print(f" {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*54}")
    print(f" Database: {db_name}")
    print(f" Org:  {org.get('name')} | Slug: {org.get('slug')}")
    print(f"\n Record counts:")
    for col, count in checks.items():
        print(f"   {col}: {count}")
    contamination = "INVESTIGATE" if test_tickets > 0 else "Clean"
    print(f"\n Test data contamination: {test_tickets} suspicious records — {contamination}")
    print(f" Demo/Dev orgs in prod DB: {demo_orgs} {'— WARNING: should be 0' if demo_orgs > 0 else '— Clean'}")
    print(f"{'='*54}\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(verify())
