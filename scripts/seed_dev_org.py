"""
Seeds a minimal Dev org for internal testing.
Run: python scripts/seed_dev_org.py --env development
"""
import asyncio
import argparse
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

DEV_ORG_ID = "dev-internal-testing-001"
DEV_ORG_SLUG = "battwheels-dev"


async def seed_dev(db):
    # Purge and recreate
    for col in ["organizations", "users", "tickets", "invoices", "contacts",
                "inventory", "journal_entries", "accounts", "employees"]:
        await db[col].delete_many({"organization_id": DEV_ORG_ID})

    hashed = bcrypt.hashpw(b"DevTest@123", bcrypt.gensalt()).decode()

    await db.organizations.insert_one({
        "organization_id": DEV_ORG_ID,
        "name": "Battwheels Dev",
        "slug": DEV_ORG_SLUG,
        "is_active": True,
        "is_dev": True,
        "city": "Delhi",
        "state": "Delhi",
        "plan": "professional",
        "created_at": datetime.utcnow(),
    })

    await db.users.insert_one({
        "user_id": "user-dev-owner-001",
        "organization_id": DEV_ORG_ID,
        "name": "Dev Admin",
        "email": "dev@battwheels.internal",
        "password": hashed,
        "role": "owner",
        "is_active": True,
        "created_at": datetime.utcnow(),
    })

    print("Dev org created: dev@battwheels.internal / DevTest@123")
    print(f"   Slug: {DEV_ORG_SLUG} | DB: battwheels_dev")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True, choices=["development"])
    parser.add_argument("--yes", action="store_true",
                        help="Skip confirmation prompt.")
    args = parser.parse_args()

    if not args.yes:
        confirm = input(f"\nAbout to seed DEV data into development database.\n   Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

    url = os.environ.get("MONGO_URL")
    if not url:
        print("ERROR: MONGO_URL environment variable not set.")
        sys.exit(1)

    client = AsyncIOMotorClient(url)
    db = client["battwheels_dev"]
    await seed_dev(db)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
