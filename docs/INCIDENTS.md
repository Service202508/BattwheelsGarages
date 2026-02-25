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

### INC-004 — Drop empty audit_log collection (production)
- **Date:** 2026-02-25 12:19 UTC
- **Performed by:** Agent (with explicit human approval)
- **Environment:** production
- **Affected org:** All (collection-level change)
- **Action taken:**
  - Dropped the empty `audit_log` collection (0 documents) from `battwheels` database
  - The correct collection `audit_logs` (31 records) was verified intact before and after
- **Reason:** `audit_log` (without 's') was a Week 2 artifact. All code writes to `audit_logs`. Empty collection caused confusion.
- **Approved by:** D (script code reviewed line-by-line before execution)
- **Verification:**
  - Pre-check confirmed 0 documents in `audit_log`
  - Post-check assertion confirmed collection no longer exists
  - `audit_logs` (31 records) unaffected
  - verify_prod_org.py: CLEAN
- **Rollback plan:** Collection was empty — no data to restore

### INC-005 — Migrate invoices to invoices_enhanced (production)
- **Date:** 2026-02-25 12:19 UTC
- **Performed by:** Agent (with explicit human approval)
- **Environment:** production
- **Affected org:** battwheels-garages
- **Action taken:**
  - Migrated 1 record (INV-00001, Rajesh Kumar, grand_total=18880.0) from `invoices` to `invoices_enhanced`
  - Line items fetched from `invoice_line_items` collection (2 items)
  - `payment_status` derived as "paid" (balance_due=0, amount_paid=18880)
  - Original `created_at` preserved from `created_time` field
  - All GST fields preserved (total_igst=2880.0, place_of_supply=MH)
  - Additional fields preserved: customer_email, estimate_id, estimate_number, shipping_charge, adjustment, paid_date, payment_count
- **Reason:** Consolidate legacy `invoices` collection into the enhanced schema used by all current code.
- **Approved by:** D (raw production document reviewed, dry-run preview approved, transform function updated with 4 fixes before execution)
- **Verification:**
  - Dry-run preview of INV-00001 reviewed and approved before execution
  - Post-migration verification: all 7 critical fields confirmed correct
  - verify_prod_org.py: CLEAN
- **Rollback plan:** Delete migrated record from `invoices_enhanced` where `migrated_from: "invoices"`

### INC-005a — invoices collection preservation decision
- **Date:** 2026-02-25 12:19 UTC
- **Decision by:** D
- **Environment:** production
- **Status:** PENDING — Original `invoices` collection (1 record, INV-00001) intentionally preserved
- **Reason:** Migration to `invoices_enhanced` is complete and verified, but the original collection is kept as a safety net until D explicitly approves dropping it.
- **Action required:** When ready, run `db.invoices.drop()` on production and log as INC-006.
- **No expiry** — this is a manual decision, not a timed cleanup.
