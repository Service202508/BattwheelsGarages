# Battwheels OS — Changelog

## Feb 24, 2026 — Regression Fix (Session 3b)
- Fixed invoices-enhanced 307 redirect stripping auth headers (added `@router.get("")` route)
- Bumped login rate limit from 5/min to 10/min (still blocks brute force, allows test flows)
- Result: **20/20 tests passing — 100% regression**

## Feb 24, 2026 — Hardening Sprint (Session 3)
All 14 items implemented and verified:

### Multi-Tenancy (Item 1)
- Fixed org_id stamps in master_data.py, invoice_payments.py, invoices_enhanced.py
- 0 unscoped queries remaining in routes/

### Security
- **S5:** Password version in JWT (`pwd_v` field) — sessions invalidated on password change
- **S2:** `is_active` DB check on every JWT validation — deactivated users blocked immediately
- **S4:** Rate limiting: 10/min on login endpoint (SlowAPI)
- **S3:** PIL-based MIME validation added to file upload service
- **S1:** Password reset tokens using SHA-256 hash + 1h TTL (verified)

### Data Integrity
- **D1:** Atomic inventory deduction via `find_one_and_update` with `$gte` floor check
- **D3:** Unique compound index on `payroll_runs(organization_id, period)` — prevents duplicate runs
- **Section 5:** Razorpay webhook atomicity — critical block pattern, notifications fail silently

### Operational
- **O1:** Structured audit logging (`utils/audit.py`) wired to: ticket close, password change, payroll run, user removal, Razorpay payment (6+ endpoints)
- **O2:** Enhanced health check — MongoDB ping + env var verification
- **O3:** Bounded cursor iteration in tally_export, data_migration, platform_admin

### Architecture
- **Section 7:** 17+ compound indexes auto-created on startup via `utils/indexes.py`
- **Section 8:** Lifespan refactor — replaced all `@app.on_event` with `@asynccontextmanager`
- **B1:** Indian FY (April-March) date defaults in BusinessReports.jsx + backend/frontend utilities

## Feb 24, 2026 — Session 2
- API v1 versioning: auth at /api/auth/, business at /api/v1/
- EFI feedback loop UI: Shadcn Dialog in JobCard.jsx
- MongoDB schema validators on 7 collections

## Feb 24, 2026 — Session 1
- Master audit of 16 modules
- Multi-tenancy hardening: 22 route files patched
- Legacy data cleanup
- Environment separation: dev/staging/prod
- Password security reset
