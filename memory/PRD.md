# Battwheels OS - Product Requirements Document

## Original Problem Statement
Battwheels OS is an EV service management SaaS platform with AI-powered diagnostics (EVFI), multi-tenant architecture, full ERP capabilities (tickets, invoices, estimates, accounting, HR, GST), and customer/technician portals.

## What's Been Implemented

### Session: 2026-03-12 (Deployment Fix - Production 520 Resolution)
- **MongoDB Retry with Backoff**: Added `_wait_for_mongodb()` in `server.py` — retries connection up to 30 times (3s timeout + 2s delay per attempt) with per-attempt logging. Prevents silent hang when MongoDB isn't ready at startup. Root cause of 520 errors.
- **load_dotenv override investigation**: Tested `override=True`, reverted — not needed since Emergent secrets are correct.
- **Corrupted .gitignore cleanup**: Removed 80+ duplicate `# Environment files` lines, 16 orphan `-e` sed artifacts, consolidated to 12-line clean file.
- **Production Atlas config**: Updated `backend/.env` with correct Atlas `MONGO_URL` (`mongodb+srv://...customer-apps.ngfrxe.mongodb.net`) and `DB_NAME=new-org-validation-battwheels`.

### Previous Sessions
- Homepage content rewrite and polish (EVFI branding, Hinglish copy, stats updates)
- 11 UI/UX fixes (diagnosis readability, dropdown empty states, sidebar nav, mobile scrolling)
- 37 cross-tenant data leak fixes + RBAC middleware fix
- Full multi-tenant architecture with plan gating
- Email standardization to support@battwheels.com
- Pre-deployment E2E fixes (plan type, registration form, vehicle_category, accounting summary)
- Test suite isolation to battwheels_test DB

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + MongoDB (Motor) — Atlas in production
- AI: Gemini via Emergent LLM Key (EVFI diagnostics)
- Payments: Razorpay
- Email: Resend
- Error Tracking: Sentry

## Prioritized Backlog

### P0 (Critical)
- Deploy and verify 520 is resolved (commits ready, awaiting UI deploy)
- First Customer Journey Audit (full UI/UX walkthrough)

### P1 (High)
- Fix EVFI `/match` endpoint tenant validation error (500 on `/api/v1/evfi/match`)
- Fix `test_multi_tenant_crud.py` setup errors
- Fix `reports/advanced/summary` 404 error
- Investigate rate limiting (429 errors)
- Automate Vehicle Category Seeding
- Verify Production Email Service (Resend)
- Fix CI/CD Pipeline

### P2 (Medium)
- Fix CSRF token missing on payroll POST
- Implement Payslip PDF Generation
- Refactor `_enhanced` file duplication
- Decompose "God Files" (reports_advanced.py)
- Unify `invoices` and `ticket_invoices` collections
- Fix orphaned DB records root cause (operations_api.py tenant isolation)

## Key Commits This Session
- `54129fe5` fix: add MongoDB retry with backoff on startup to prevent deployment 520s
- `0d93ed75` fix: clean corrupted .gitignore
- `609a9f47` revert: remove load_dotenv override=True
- `ec8dc6ee` fix: align backend/.env with production Atlas config and correct DB name
