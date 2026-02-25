# BATTWHEELS OS — INCIDENT LOG

All manual interventions on production data are recorded here.
This file is append-only. Never edit or delete existing entries.

---

## Format

```
### INC-[NNN] — [Short Title]
- **Date:** YYYY-MM-DD HH:MM UTC
- **Performed by:** [Agent / Human]
- **Environment:** production / staging
- **Affected org:** [org slug]
- **Action taken:** [Exact description of what was done]
- **Reason:** [Why this was necessary]
- **Approved by:** D
- **Verification:** [How it was verified safe]
- **Rollback plan:** [What to do if something went wrong]
```

---

## Incidents

### INC-001 — Production Contamination Cleanup
- **Date:** 2026-02-25 09:49 UTC
- **Performed by:** Agent (with explicit human approval)
- **Environment:** production
- **Affected org:** battwheels-garages (cleanup only — no real data touched)
- **Action taken:**
  - Deleted 6 test user accounts created during Week 2 development
  - Deleted 3 test invoices from `invoices_enhanced` collection
  - Deleted 1 test invoice (INV-00027, "Audit Customer") from `invoices` collection
  - Deleted 1 test audit_log entry
  - Deleted 2 test business_customer records (TEST_Fleet_Company, BluWheelz)
  - Deleted 1 test contact (audit_customer@test.com)
  - Fixed org=None for 4 real staff users (deepak, rahul, priya, service) — linked to correct org_id
- **Reason:** Week 2 development ran with DB_NAME=battwheels (production) instead of battwheels_dev. Test data was written to production during development and testing.
- **Approved by:** D (line-by-line dry run reviewed and confirmed)
- **Verification:**
  - Dry run output reviewed before any deletion
  - Before/after counts verified
  - INV-00001 (real invoice, Rajesh Kumar) confirmed intact
  - verify_prod_org.py: CLEAN (0 suspicious records, 0 demo/dev orgs)
  - Battwheels Garages core data: tickets=10, invoices=1, journal_entries=18, contacts=14
- **Rollback plan:** N/A — deleted records were confirmed test data with no business value

### INC-002 — Battwheels OS Internal Org Creation
- **Date:** 2026-02-25 09:52 UTC
- **Performed by:** Agent (with explicit human approval)
- **Environment:** production
- **Affected org:** N/A (new org created, no existing data modified)
- **Action taken:**
  - Created new organisation "Battwheels OS Internal" (slug: battwheels-internal)
  - Created admin user internal@battwheels.in with generated password
  - Purpose: Platform-level production testing without touching customer data
- **Reason:** ENVIRONMENT_SOP.md Rule 8 requires a dedicated internal org for production testing. Customer orgs must never be used for testing.
- **Approved by:** D
- **Verification:**
  - Battwheels Garages data unchanged (before/after counts identical)
  - verify_prod_org.py: CLEAN
  - Total orgs: 2 (Battwheels Garages + Battwheels OS Internal)
- **Rollback plan:** Delete the battwheels-internal org and internal@battwheels.in user

### INC-003 — Environment Misconfiguration Fix
- **Date:** 2026-02-25 09:57 UTC
- **Performed by:** Agent
- **Environment:** development (.env file change)
- **Affected org:** N/A
- **Action taken:**
  - Changed DB_NAME from "battwheels" to "battwheels_dev" in /app/backend/.env
  - Changed ENVIRONMENT from "production" to "development" in /app/backend/.env
  - Fixed empty password hashes for dev/demo users in battwheels_dev (seeding bug)
- **Reason:** Development environment was incorrectly pointing at production database since Week 2.
- **Approved by:** D
- **Verification:**
  - Backend restarted successfully
  - demo@voltmotors.in login: SUCCESS
  - dev@battwheels.internal login: SUCCESS
  - Production database not affected (read-only verification)
- **Rollback plan:** Revert .env values (not desired — the fix is correct)
