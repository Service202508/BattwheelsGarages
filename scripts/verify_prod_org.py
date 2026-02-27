"""
Battwheels OS — Production Health Check (READ-ONLY)

Verifies the production database matches the expected SaaS state:
  - 1 user: platform-admin@battwheels.in (is_platform_admin=True)
  - 0 organizations (customers sign up via the self-serve flow)
  - Platform-level seed data present (plans, migrations)
  - No unexpected data in any other collection

Run before and after every deployment.
Safe to run at any time — makes zero writes.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# Platform-level collections that are expected to have data
EXPECTED_PLATFORM_COLLECTIONS = {"users", "plans", "migrations"}


async def verify():
    url = os.environ.get("MONGO_URL")
    if not url:
        print("FAIL: MONGO_URL environment variable not set.")
        return

    client = AsyncIOMotorClient(url)
    prod = client["battwheels"]

    results = []
    warnings = []

    print(f"\n{'=' * 58}")
    print(f"  PRODUCTION HEALTH CHECK (battwheels)")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  READ-ONLY — no modifications")
    print(f"{'=' * 58}")

    # --- CHECK 1: Platform admin user ---
    print(f"\n  [1] Platform Admin User")
    pa = await prod.users.find_one(
        {"email": "platform-admin@battwheels.in"},
        {"_id": 0, "password_hash": 0}
    )
    user_count = await prod.users.count_documents({})

    if pa and pa.get("is_platform_admin") and user_count == 1:
        print(f"      PASS — platform-admin@battwheels.in exists")
        print(f"      PASS — is_platform_admin: True")
        print(f"      PASS — Total users: {user_count} (expected: 1)")
        results.append("PASS")
    elif pa and user_count > 1:
        print(f"      PASS — platform-admin@battwheels.in exists")
        print(f"      INFO — Total users: {user_count} (customer signups may have occurred)")
        results.append("PASS")
    else:
        if not pa:
            print(f"      FAIL — platform-admin@battwheels.in NOT FOUND")
            results.append("FAIL")
        else:
            if not pa.get("is_platform_admin"):
                print(f"      FAIL — is_platform_admin is NOT True")
                results.append("FAIL")
            print(f"      Total users: {user_count}")

    # --- CHECK 2: Organizations (0 = expected SaaS state) ---
    print(f"\n  [2] Organizations")
    org_count = await prod.organizations.count_documents({})

    if org_count == 0:
        print(f"      PASS — 0 organizations (clean SaaS state, awaiting first signup)")
        results.append("PASS")
    else:
        orgs = await prod.organizations.find(
            {}, {"name": 1, "slug": 1, "organization_id": 1, "_id": 0}
        ).to_list(20)
        print(f"      WARNING — {org_count} organization(s) found (review if expected):")
        for o in orgs:
            print(f"        {o.get('name', '?')} (slug: {o.get('slug', '?')})")
        warnings.append(f"{org_count} unexpected org(s) in production")
        results.append("WARNING")

    # --- CHECK 3: Plans (subscription plan definitions) ---
    print(f"\n  [3] Subscription Plans")
    plans_count = await prod.plans.count_documents({})

    if plans_count >= 1:
        print(f"      PASS — {plans_count} plan(s) present")
        results.append("PASS")
    else:
        print(f"      FAIL — No plans found (signup flow will break)")
        results.append("FAIL")

    # --- CHECK 4: Migrations ---
    print(f"\n  [4] Migrations")
    migrations_count = await prod.migrations.count_documents({})

    if migrations_count >= 1:
        print(f"      PASS — {migrations_count} migration record(s)")
        results.append("PASS")
    else:
        print(f"      WARNING — No migration records (may re-run on next startup)")
        warnings.append("No migration records in production")
        results.append("WARNING")

    # --- CHECK 5: Unexpected data in other collections ---
    print(f"\n  [5] Unexpected Data Scan")
    collections = await prod.list_collection_names()
    unexpected = []

    for coll_name in sorted(collections):
        if coll_name in EXPECTED_PLATFORM_COLLECTIONS:
            continue
        count = await prod[coll_name].count_documents({})
        if count > 0:
            unexpected.append((coll_name, count))

    if not unexpected:
        print(f"      PASS — All non-platform collections are empty")
        results.append("PASS")
    else:
        print(f"      WARNING — {len(unexpected)} collection(s) have unexpected data:")
        for name, count in unexpected:
            print(f"        {name}: {count} document(s)")
        warnings.append(f"{len(unexpected)} collection(s) with unexpected data")
        results.append("WARNING")

    # --- CHECK 6: No demo/test contamination ---
    print(f"\n  [6] Test Data Contamination")
    demo_orgs = await prod.organizations.count_documents({
        "$or": [{"is_demo": True}, {"is_dev": True}]
    })
    test_users = await prod.users.count_documents({
        "email": {"$regex": "test|demo|dummy|example", "$options": "i"},
        "email": {"$ne": "platform-admin@battwheels.in"}
    })

    if demo_orgs == 0 and test_users == 0:
        print(f"      PASS — No demo/test data detected")
        results.append("PASS")
    else:
        if demo_orgs > 0:
            print(f"      WARNING — {demo_orgs} demo/dev org(s) found")
            warnings.append(f"{demo_orgs} demo/dev orgs in production")
        if test_users > 0:
            print(f"      WARNING — {test_users} test-like user(s) found")
            warnings.append(f"{test_users} test users in production")
        results.append("WARNING")

    # --- SUMMARY ---
    fails = results.count("FAIL")
    warns = results.count("WARNING")
    passes = results.count("PASS")

    print(f"\n{'─' * 58}")
    print(f"  SUMMARY")
    print(f"{'─' * 58}")
    print(f"  Checks: {len(results)} total — {passes} PASS, {warns} WARNING, {fails} FAIL")
    print(f"  Users: {user_count}  |  Orgs: {org_count}  |  Plans: {plans_count}  |  Migrations: {migrations_count}")

    if warnings:
        print(f"\n  Warnings:")
        for w in warnings:
            print(f"    - {w}")

    if fails > 0:
        print(f"\n  VERDICT: FAIL — {fails} critical check(s) failed")
    elif warns > 0:
        print(f"\n  VERDICT: WARNING — review {warns} item(s) above")
    else:
        print(f"\n  VERDICT: ALL GREEN — production is healthy")

    print(f"{'=' * 58}\n")
    client.close()


if __name__ == "__main__":
    asyncio.run(verify())
