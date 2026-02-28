# Battwheels OS — Product Requirements Document

## Original Problem Statement
Full-stack workshop management platform (FastAPI + React + MongoDB) for Indian automotive workshops. Multi-tenant SaaS with GST compliance, HR/payroll, ticket management, inventory, invoicing, and more.

## Current Sprint: PHASE 0 — SURGICAL CLEANUP SPRINT (Completed 2026-02-28)

### Items Completed

**ITEM 1: Fix Broken Employee Endpoint (P0)** ✅
- **Problem**: `test_admin_can_reset_employee_password` skipped due to 404.
- **Root cause**: (a) Test URLs used wrong paths (`/api/employees/...` instead of `/api/v1/employees/...` and `/api/v1/hr/employees`). (b) Endpoint looked up `users.user_id` directly with `employee_id` instead of first resolving employee → user mapping.
- **Fix**: Updated `auth_main.py` endpoint to look up employee record first, then find linked user via `user_id`, `work_email`, or `email`. Fixed test URLs.
- **Files changed**: `routes/auth_main.py`, `tests/test_password_management.py`
- **Test result**: 14/14 passed (3 previously skipped now passing)

**ITEM 2: CSRF Protection Middleware (P1)** ✅
- **Status**: Already implemented at `middleware/csrf.py` using double-submit cookie pattern.
- **Verification**: Mounted in `server.py` line 230. Bypasses Bearer token auth, auth endpoints, webhooks.
- **Tests added**: `tests/test_csrf_middleware.py` — 6/6 passed

**ITEM 3: GSTR-3B RCM Handling (P1)** ✅
- **Status**: Already implemented in `routes/gst.py`.
- **Coverage**: Section 3.1(d) inward RCM supplies, Table 4A(3) ITC from RCM, RCM added to net tax liability.
- **Tests added**: `tests/test_gstr3b_rcm.py` — 4/4 passed

**ITEM 4: Bleach Input Sanitization Middleware (P1)** ✅
- **Problem**: Password fields were NOT exempted from bleach sanitization, risking credential corruption.
- **Fix**: Added `PASSWORD_FIELDS` frozenset and `key` parameter to `_sanitize_value()` to skip password/token/secret fields.
- **Files changed**: `middleware/sanitization.py`
- **Tests added**: `tests/test_sanitization_middleware.py` — 8/8 passed (including E2E password preservation test)

**ITEM 5: Remove Duplicate TechnicianProductivity.jsx (P2)** ✅
- **Finding**: Two components with same name but different purposes (admin dashboard vs technician self-view).
- **Fix**: Renamed root `pages/TechnicianProductivity.jsx` → `pages/ProductivityDashboard.jsx`. Updated App.js import.
- **Files changed**: `pages/TechnicianProductivity.jsx` (renamed), `App.js` (import updated)

**ITEM 6: Remove Vestigial Stripe Configuration (P2)** ✅
- **Removed**: `STRIPE_API_KEY=REDACTED_STRIPE_KEY` from `.env`
- **Removed**: `routes.invoice_payments` from V1_ROUTES in `server.py`
- **Removed**: Stripe RBAC pattern from `middleware/rbac.py`
- **Removed**: Stripe webhook bypass from `core/tenant/guard.py`

### Final Verification
- **New tests**: 32/32 passed
- **Production health check**: ALL GREEN (6/6 checks)
- **Backend**: healthy, MongoDB connected

## Architecture
- **Backend**: FastAPI on port 8001, supervisor-managed
- **Frontend**: React on port 3000, supervisor-managed
- **Database**: MongoDB (`battwheels_dev` for dev, `battwheels` for prod)
- **Auth**: JWT-based with session cookie support
- **Middleware stack**: CORS → Security Headers → TenantGuard → RBAC → CSRF → Sanitization → RateLimit

## Known Pre-existing Issues
- `test_gstr3b_credit_notes.py`: Missing `REACT_APP_BACKEND_URL` env var causes URL failures
- `test_gst_accounting_flow.py`: Uses wrong credentials
- Pattern A Violations: Queries without `org_id` in `knowledge_brain.py`, `double_entry_service.py`
- UI/UX: Hardcoded off-theme colors, inline styles
- Module stubs: `BalanceSheet.jsx`, `einvoice_service.py`, `expert_queue_service.py`
- 12 tests skipped (webhooks, Form16, Razorpay infrastructure)

## 3rd Party Integrations
- Razorpay (test keys)
- Resend (API key present)
- Sentry (DSN present)
- Zoho (credentials present)
- Emergent LLM Key (gpt-4o-mini, gemini-2.5-flash)
