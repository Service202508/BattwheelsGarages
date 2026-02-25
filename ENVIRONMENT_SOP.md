# BATTWHEELS OS — ENVIRONMENT SOP
## Standing Operating Procedure: Three-Environment Discipline
## This file is LAW. Every agent, every session, every change must follow it.

---

## THE THREE ENVIRONMENTS

| Environment | Database | Purpose | Who touches it |
|---|---|---|---|
| **Development** | `battwheels_dev` | All new code, all experiments, all testing | Emergent agent |
| **Staging** | `battwheels_staging` | Pre-release QA gate — mirrors production | Manual promotion only |
| **Production** | `battwheels` | Live data. Real customers. Real money. | Manual promotion only, with sign-off |

---

## RULE 1 — WHERE ALL DEVELOPMENT HAPPENS

**Every single code change, feature, fix, test, and experiment happens in `battwheels_dev` ONLY.**

Before touching any code in any session, the agent MUST verify the active environment:

```bash
python3 -c "
import os
db = os.environ.get('DB_NAME', 'NOT SET')
print(f'Active DB: {db}')
if db != 'battwheels_dev':
    print('⛔ WRONG ENVIRONMENT. Stop. Do not write code. Fix .env first.')
else:
    print('✅ Correct. Development environment confirmed. Safe to proceed.')
"
```

If DB_NAME is anything other than `battwheels_dev` — **STOP. Fix it. Then proceed.**

---

## RULE 2 — THE PROMOTION LADDER

Code only moves UP. Never sideways. Never down.

```
[1] DEVELOPMENT (battwheels_dev)
     All new work done here.
     Agent writes code, runs tests, verifies features.
     PASS condition: All tests pass + feature manually verified in Emergent preview.
          ↓
     HUMAN SIGN-OFF REQUIRED before moving to step 2.
     D must review and explicitly say "promote to staging".

[2] STAGING (battwheels_staging)
     Agent runs DB_NAME=battwheels_staging — same code, staging data.
     Full regression test suite runs against staging DB.
     PASS condition: All tests pass + D does manual QA walkthrough.
          ↓
     HUMAN SIGN-OFF REQUIRED before moving to step 3.
     D must explicitly say "promote to production".

[3] PRODUCTION (battwheels)
     Deployment with DB_NAME=battwheels.
     Read verify_prod_org.py health check after every deployment.
     PASS condition: Health check clean + production org data intact.
```

**The agent NEVER skips a step. NEVER promotes without explicit human instruction.**

---

## RULE 3 — PRODUCTION IS READ-ONLY FOR THE AGENT

The agent may NEVER:
- Write, update, or delete documents in the `battwheels` (production) database
- Run migrations directly against production without explicit sign-off
- Reset, seed, or modify production data
- Run destructive scripts against production

The ONLY script allowed to run against production without explicit permission is:
```bash
python scripts/verify_prod_org.py  # READ-ONLY health check
```

**If the agent needs to fix a production data issue, it must:**
1. State the problem clearly
2. Write the migration/fix script
3. Test it against `battwheels_dev` first
4. Present it to D for review
5. Wait for explicit "run this on production" instruction

---

## RULE 4 — CODE IS ENVIRONMENT-AGNOSTIC, DATA IS NOT

**Code:** One codebase. Same Python files, same JSX files run in all three environments. The `DB_NAME` environment variable is the only thing that changes.

**Data:** Never migrates upward automatically. Each environment has its own independent data:
- `battwheels_dev` — Volt Motors demo org + development test data
- `battwheels_staging` — Staging test org (mirrors production structure)
- `battwheels` — Battwheels Garages real data. Sacred. Never touched carelessly.

**Schema migrations** (adding indexes, renaming fields, etc.) must be:
1. Written as scripts in `/app/scripts/migrations/`
2. Tested on `battwheels_dev`
3. Run on `battwheels_staging` and verified
4. Then and only then run on `battwheels` with explicit sign-off

---

## RULE 5 — SESSION START PROTOCOL

At the start of EVERY development session, before writing a single line of code:

```bash
# Step 1: Confirm environment
echo "Active DB: $DB_NAME"
echo "Mongo URL: $MONGO_URL" | sed 's/:.*@/:***@/'

# Step 2: Confirm dev org is healthy
python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
async def check():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME', 'battwheels_dev')]
    org = await db.organizations.find_one({'slug': 'volt-motors-demo'})
    if org:
        print(f'✅ Dev org intact: {org[\"name\"]}')
    else:
        print('⚠️  Demo org not found — may need re-seeding: make seed-demo')
asyncio.run(check())
"

# Step 3: Quick test suite
cd /app && python -m pytest backend/tests/ -q 2>&1 | tail -3
```

All three checks must be green before any new work begins.

---

## RULE 6 — WEEK / SPRINT COMPLETION PROTOCOL

Before declaring any sprint or week complete:

1. Run full test suite — all tests must pass
2. Run `python scripts/verify_prod_org.py` — production must be untouched
3. List every file modified in this session
4. Confirm all changes are in `battwheels_dev` / codebase only
5. State explicitly: "Development phase complete. Ready for staging promotion when D approves."

The agent NEVER declares "done" and NEVER promotes without this checklist complete.

---

## RULE 7 — IF SOMETHING GOES WRONG

**In development:** Fix it. That's what dev is for.

**In staging:** Fix in dev first. Re-promote to staging. Never patch staging directly.

**In production:** 
1. STOP all new development immediately
2. Assess: can it be fixed with a data patch or does it need a code fix?
3. Write fix in dev, test in staging
4. Present to D with exact steps
5. Get explicit approval
6. Run fix on production
7. Run `verify_prod_org.py` immediately after
8. Document what happened in `/app/docs/INCIDENTS.md`

---

## RULE 8 — CUSTOMERS ARE SACROSANCT

Battwheels Garages and every future customer organisation are independent tenants
of Battwheels OS. Their data belongs to them. The platform owner has technical
access but no right to manipulate customer data directly under any normal circumstance.

**The agent must NEVER:**
- Run scripts that write, update, or delete records in a customer org's data
- Seed, reset, or manipulate a customer org's records directly via DB
- Use a customer org as a development or testing environment
- Apply data migrations that alter customer content
  (structure-only schema changes are permitted during deployment)

**New features reach customers exclusively through code deployment:**
1. Code written and tested in battwheels_dev (Volt Motors demo org)
2. Code verified in battwheels_staging
3. Code deployed to production
4. All customer orgs (including Battwheels Garages) receive the update on next login
5. No one touches their database directly at any point in this process

**Operational tasks for customer orgs must use the application layer only:**
- Password resets → use the forgot-password flow (/forgot-password)
- Data corrections → use the Platform Admin panel (/platform-admin)
- Support issues → the customer uses the UI; never bypass via direct DB

**The ONLY org in production the agent may interact with directly is:**
- Name: Battwheels OS Internal
- Slug: battwheels-internal
- Purpose: Platform-level production testing, without touching any customer data
- All other production orgs are customer-owned and untouchable by the agent

**If a task requires touching a customer org's data directly:**
- Stop immediately
- Explain what needs to happen and why
- Wait for explicit written approval from D
- Document the action in /app/docs/INCIDENTS.md before and after

---

## ENVIRONMENT REFERENCE CARD

```
╔══════════════════════════════════════════════════════╗
║           BATTWHEELS OS ENVIRONMENTS                 ║
╠══════════════════════════════════════════════════════╣
║  DEV        DB_NAME=battwheels_dev                   ║
║             Volt Motors demo org                     ║
║             Safe to break. Made to be tested.        ║
╠══════════════════════════════════════════════════════╣
║  STAGING    DB_NAME=battwheels_staging               ║
║             QA gate. Must match production structure.║
║             Promote from dev only. Sign-off needed.  ║
╠══════════════════════════════════════════════════════╣
║  PRODUCTION DB_NAME=battwheels                       ║
║             Battwheels Garages. Real customers.      ║
║  ⚠️  NEVER write here without explicit approval. ⚠️  ║
╚══════════════════════════════════════════════════════╝
```

---

## ACKNOWLEDGEMENT

Every agent session working on Battwheels OS must read this file at the start.
This SOP was established on 2026-02-25 and applies to all future development.
Violations of this SOP risk real customer data and platform integrity.
