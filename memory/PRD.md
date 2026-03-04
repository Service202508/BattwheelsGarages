# Battwheels OS — Product Requirements Document

## Original Problem Statement
Battwheels OS is an EV service workshop management SaaS platform. After a stability audit, the codebase was reverted, and a "REBUILD SESSION 1 — P0: EFI + FLOW BLOCKERS" was initiated to restore high-priority features.

## Architecture
- **Frontend**: React + Vite (craco), shadcn/ui, Tailwind CSS
- **Backend**: FastAPI + MongoDB (motor async)
- **DB**: MongoDB (`battwheels_dev` for dev, `battwheels` for production)
- **Auth**: JWT-based, RBAC with roles (platform_admin, owner, technician, etc.)

## Credentials
- Demo User: `demo@voltmotors.in` / `Demo@12345`
- Dev Admin: `platform-admin@battwheels.in` / `DevTest@123`
- Owner User: `dev@battwheels.internal` / `DevTest@123`

## Completed Tasks (Session 1A - 2026-03-04)

### Task 0: Verification Scripts — DONE
- `/app/scripts/verify_platform.sh` — exists, executable
- `/app/scripts/verify_prod_org.py` — exists, valid Python

### Task 1: Vehicle Category Dropdown Fix — DONE
- **Root cause**: 218 duplicate entries in `vehicle_categories` collection (seed script ran multiple times without idempotency)
- **Fix**: Cleaned duplicates (kept 5 unique: 2W_EV, 3W_EV, 4W_EV, COMM_EV, LEV), added unique index on `code`
- Also cleaned 882 duplicate `vehicle_models` (35 unique remain), added unique index on `model_id`
- Made seed function idempotent (uses upsert instead of insert_many)

### Task 2: Platform Admin Fixes — DONE
- **Back arrow**: Added back button (`data-testid="platform-admin-back-btn"`) to PlatformAdmin header using `navigate(-1)`
- **Logout button**: Already existed (`data-testid="platform-admin-logout-btn"`) with `onLogout` prop properly passed from App.js

## Completed Tasks (Session 3A - 2026-03-04)

### Task 1: AI Diagnostic Token System — DONE
- Created `backend/services/ai_token_service.py` with get_token_status, consume_token, lazy monthly reset
- Created `backend/routes/ai_usage.py` with GET /api/v1/ai-usage/status
- Integrated token consumption in `efi_guided.py` /session/start (HTTP 429 on limit)
- Added token badge to EFI panel in TicketDetail.jsx (color-coded: green/amber/red)
- Button disabled when tokens exhausted
- 8 unit tests all passing

### Task 2: Plan Sync — DONE
- Professional price synced to ₹5,999/mo across models.py, platform_admin.py, Docs.jsx, Terms.jsx
- Token allocations: Free Trial 10, Starter 25, Professional 100, Enterprise unlimited

## Completed Tasks (Session - 2026-03-04, Fork)

### Fix reports_advanced.py Collection Names + DB Fallback — DONE
- **Root cause**: `backend/routes/reports_advanced.py` queried `_enhanced` collections (`invoices_enhanced`, `estimates_enhanced`, `salesorders_enhanced`, `contacts_enhanced`) which had 0-3 docs, instead of canonical collections (`invoices`: 1637, `contacts`: 513, `estimates`: 1253, `salesorders`: 667)
- **Fix**: Changed collection references on lines 28-31 to canonical names. Changed DB fallback from `zoho_books_clone` to `battwheels_dev`.
- **Verification**: All 4 advanced report endpoints return non-zero multi-month data. Regression check passed (receivables: 142,177.55, total_invoiced: 573,509.60, cash_flow: 390,208.40, AMC active: 7).

### Audit: Untested Dashboard Endpoints — DONE (Report Only)
- `/dashboard/financial/bank-accounts`: Working (HTTP 200). Returns default placeholder. **Data gap** — no seeded bank accounts.
- `/dashboard/financial/projects-watchlist`: Working (HTTP 200). Returns 5 test projects. Sparse data (unbilled_amount = 0).

## Prioritized Backlog

### P1 — Upcoming
- Seed bank account records for demo org to populate `/bank-accounts` dashboard
- Seed `customerpayments` and `expenses` records for richer cash-flow reporting

### P2 — Future
- Refactor DB connections: centralize into shared utility (currently duplicated per route file)
- Resolve dual-collection architecture: CRUD routes write to `_enhanced` collections, analytics read from canonical collections
- Remove stale `zoho_books_clone` fallback strings from other route files

### P3 — Backlog
- Fix skipped password reset tests (state pollution in `test_password_reset.py`)
- Investigate failed API spot-checks (404s on `items/search`, `efi-guided/failure-cards`)
