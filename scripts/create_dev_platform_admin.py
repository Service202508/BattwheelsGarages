"""
Create dev platform admin and test users in battwheels_dev.
Sprint 4A-03: Enables admin endpoint testing in dev environment.

SAFETY: Only touches battwheels_dev. Never battwheels (production).
"""
import asyncio
import os
import sys
import bcrypt
import motor.motor_asyncio
from datetime import datetime, timezone

# Hardcoded to dev DB — NEVER change this
TARGET_DB = "battwheels_dev"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def main():
    mongo_url = os.environ.get("MONGO_URL")
    if not mongo_url:
        print("FAIL: MONGO_URL not set")
        sys.exit(1)

    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    db = client[TARGET_DB]

    # Verify we're NOT in production
    db_name = os.environ.get("DB_NAME", "")
    if db_name == "battwheels":
        print("ABORT: DB_NAME is 'battwheels' (production). This script only runs in dev.")
        sys.exit(1)

    now = datetime.now(timezone.utc).isoformat()

    users_to_create = [
        {
            "user_id": "user-dev-platform-admin",
            "email": "platform-admin@battwheels.in",
            "password_hash": hash_password("DevAdmin@2026!"),
            "name": "Dev Platform Admin",
            "first_name": "Dev",
            "last_name": "Platform Admin",
            "role": "platform_admin",
            "is_platform_admin": True,
            "organizations": [],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": "user-dev-admin-001",
            "email": "admin@battwheels.in",
            "password_hash": hash_password("TestPass@123"),
            "name": "Dev Admin User",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "is_platform_admin": False,
            "organizations": ["dev-internal-testing-001"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": "user-dev-tech-001",
            "email": "tech@battwheels.in",
            "password_hash": hash_password("TestPass@123"),
            "name": "Dev Technician",
            "first_name": "Tech",
            "last_name": "User",
            "role": "technician",
            "is_platform_admin": False,
            "organizations": ["dev-internal-testing-001"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": "user-dev-starter-001",
            "email": "john@testcompany.com",
            "password_hash": hash_password("test_pwd_placeholder"),
            "name": "John Starter",
            "first_name": "John",
            "last_name": "Starter",
            "role": "owner",
            "is_platform_admin": False,
            "organizations": ["org_9c74befbaa95"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": "user-dev-tech-deepak",
            "email": "deepak@battwheelsgarages.in",
            "password_hash": hash_password("DevTest@123"),
            "name": "Deepak Technician",
            "first_name": "Deepak",
            "last_name": "Sharma",
            "role": "technician",
            "is_platform_admin": False,
            "organizations": ["dev-internal-testing-001"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]

    # Ensure orgs exist for user_organizations
    orgs_to_ensure = [
        {
            "organization_id": "dev-internal-testing-001",
            "name": "Dev Testing Org",
            "plan": "professional",
            "created_at": now,
        },
        {
            "organization_id": "org_9c74befbaa95",
            "name": "Test Starter Company",
            "plan": "starter",
            "created_at": now,
        },
    ]

    for org in orgs_to_ensure:
        existing = await db.organizations.find_one({"organization_id": org["organization_id"]})
        if not existing:
            await db.organizations.insert_one(org)
            print(f"  Created org: {org['organization_id']} ({org['name']})")
        else:
            # Ensure plan is set
            if not existing.get("plan"):
                await db.organizations.update_one(
                    {"organization_id": org["organization_id"]},
                    {"$set": {"plan": org["plan"]}}
                )
            print(f"  Org exists: {org['organization_id']}")

    created = 0
    skipped = 0
    for user in users_to_create:
        existing = await db.users.find_one({"email": user["email"]})
        if existing:
            # Update password hash and role in case they changed
            await db.users.update_one(
                {"email": user["email"]},
                {"$set": {
                    "password_hash": user["password_hash"],
                    "role": user["role"],
                    "is_platform_admin": user["is_platform_admin"],
                    "is_active": True,
                    "updated_at": now,
                }}
            )
            print(f"  Updated: {user['email']} (role={user['role']})")
            skipped += 1
        else:
            await db.users.insert_one(user)
            print(f"  Created: {user['email']} (role={user['role']})")
            created += 1

        # Ensure user_organizations membership
        for org_id in user.get("organizations", []):
            existing_membership = await db.user_organizations.find_one({
                "user_id": user["user_id"],
                "organization_id": org_id,
            })
            if not existing_membership:
                await db.user_organizations.insert_one({
                    "user_id": user["user_id"],
                    "organization_id": org_id,
                    "role": user["role"],
                    "joined_at": now,
                })
                print(f"    + membership: {user['email']} → {org_id}")

    print(f"\nDone. Created: {created}, Updated: {skipped}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
