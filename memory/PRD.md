# Battwheels OS - Product Requirements Document

## Original Problem Statement
Battwheels OS is an EV service management SaaS platform with AI-powered diagnostics (EVFI), multi-tenant architecture, full ERP capabilities (tickets, invoices, estimates, accounting, HR, GST), and customer/technician portals.

## What's Been Implemented

### Session: 2026-03-11 (Email Standardization)
- Standardized all public-facing contact emails to `support@battwheels.com` across 8 frontend files, 1 HTML file, and 2 backend files
- Replaced: hello@, enterprise@, security@, legal@, privacy@, sales@, accounts@ variants
- Protected emails untouched: SENDER_EMAIL (noreply@battwheels.com), platform-admin@battwheels.in

### Session: 2026-03-11 (Pre-Deployment E2E Fixes)
- **TASK 1 (P0)**: Fixed plan type discrepancy - both signup and login now consistently return `free_trial` for new orgs. Root cause: subscription service was overwriting org plan_type to "starter" after creation.
- **TASK 2 (P0)**: Updated registration form on Login page to include Organization Name, Your Name, Email, Password, Confirm Password, City, State fields. Button changed to "CREATE ORGANIZATION". Form now submits to `/api/v1/organizations/signup`.
- **TASK 3 (P0)**: Plan gating now works correctly - AMC endpoint returns 403 for free_trial users (was returning 422). Fixed by Task 1 (correct plan_type enables middleware).
- **TASK 4 (P1)**: Removed all em dashes (—) from 34+ JSX files across pages/ and 7 JSX files in components/. Zero remaining.
- **TASK 5 (P1)**: Fixed vehicle_category not saving on ticket creation. Added `vehicle_category` and `vehicle_year` fields to `TicketCreateRequest` Pydantic model.
- **TASK 6 (P1)**: Investigated - `/api/v1/operations/stats` is not a valid path; correct path is `/api/v1/operations/dashboard/stats`. Test spec issue, not app bug.
- **TASK 7 (P1)**: Fixed accounting summary returning zeros. Changed data source from empty `ledger` collection to `journal_entries` collection with `$unwind` aggregation.

### Previous Sessions
- Homepage content rewrite and polish (EVFI branding, Hinglish copy, stats updates)
- 11 UI/UX fixes (diagnosis readability, dropdown empty states, sidebar nav, mobile scrolling)
- 37 cross-tenant data leak fixes + RBAC middleware fix
- Full multi-tenant architecture with plan gating

### Session: 2026-03-12 (Deployment Fix + Test Suite Fix)
- **DEPLOYMENT FIX - ROOT CAUSE**: `startup.sh` only checked WeasyPrint dependencies and exited without starting any services. Container died immediately, causing HTTP 520 on all health checks.
  - Created `/app/supervisord.prod.conf` - production supervisor config (backend uvicorn on 8001, frontend `serve -s build` on 3000, no MongoDB since production uses Atlas)
  - Rewrote `/app/startup.sh` to `exec supervisord` as the main foreground process
  - Added `serve` package as frontend dependency for static file serving
- **CORS FIX**: Changed `CORS_ORIGINS=*` in backend/.env, updated server.py to handle wildcard
- **GITIGNORE FIX**: Removed all `.env` blocking patterns, added `!backend/.env` and `!frontend/.env` negations. Cleaned 92 corrupted `-e` lines.
- **CONFTEST FIX (P1)**: Backend test suite was 100% broken (2844 errors, 0 passed). Root causes:
  1. conftest.py didn't load backend `.env`, defaulting to `battwheels_dev` while server used `battwheels`
  2. `dev@battwheels.internal` user didn't exist in the active DB; `_ensure_test_user_passwords` only did `update_one` (no upsert)
  - Added `load_dotenv()` for backend `.env`
  - Made `_ensure_test_user_passwords` create dev user, dev org, and org membership via upsert if missing
  - Result: 575 passed, 880 failed, 982 skipped, 717 errors (remaining failures are in individual test logic, not conftest)

## Prioritized Backlog

### P0 (Critical)
- Deploy application and verify HTTP 520 is resolved
- First Customer Journey Audit (full UI/UX walkthrough for new user onboarding)

### P1 (High)
- Fix Backend Test Suite (conftest.py fixture uses non-existent test user)
- Clean Orphaned DB Records (tenant_roles, tenant_activity_logs)
- Automate Vehicle Category Seeding (deployment script)
- Verify Production Email Service (Resend integration)
- Fix CI/CD Pipeline

### P2 (Medium)
- Implement Payslip PDF Generation
- Refactor `_enhanced` file duplication
- Decompose "God Files" (reports_advanced.py etc.)
- Unify `invoices` and `ticket_invoices` collections
- Migrate remaining mocked emails to real EmailService
- Fix Trial Balance Report (shows ₹0.00)

## Known Issues
- Backend test suite broken (recurring 9+ times)
- Demo data naming inconsistency ("Pvt Ltd")
- Technician Report "Avg Response N/A"
- Customer portal sessions may expire in dev DB
- Platform admin credentials may differ between prod/dev

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + MongoDB (Motor)
- AI: Gemini via Emergent LLM Key (EVFI diagnostics)
- Payments: Razorpay
- Email: Resend
- Error Tracking: Sentry

## Key Files Modified This Session
- `backend/routes/organizations.py` - Plan type fix (restore to free_trial after subscription)
- `backend/routes/tickets.py` - Added vehicle_category to TicketCreateRequest
- `backend/routes/sales_finance_api.py` - Accounting summary uses journal_entries
- `frontend/src/pages/Login.jsx` - Registration form with org fields
- 34+ JSX files in pages/ - Em dash removal
- 7 JSX files in components/ - Em dash removal
