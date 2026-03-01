# BATTWHEELS OS — Product Requirements Document

## Original Problem Statement
Multi-phase project to improve application stability, maintainability, feature set, and security. Phase 2 Cluster 3 Part 1 covers operational module investigation (HR, Projects, Contacts) plus critical security investigations.

## Architecture
- **Frontend:** React/CRACO
- **Backend:** FastAPI (Python)
- **Database:** MongoDB (battwheels_dev)
- **3rd Party:** Razorpay (test keys), Resend, Sentry, Zoho (config-only), Emergent LLM (GPT-4o-mini, Gemini-2.5-flash)

## Completed Work

### Cluster 3 Part 1 (2026-03-01)
- **Task 1 (Zoho):** Investigated — CONFIG-READY, NOT ACTIVE. Zero HTTP calls to Zoho APIs. Documented in FEATURE_GAPS.md
- **Task 2 (WhatsApp):** Fixed deceptive behavior — `/send-whatsapp` now returns `{"status": "mocked", "delivered": false}` instead of `{"status": "queued"}` when Twilio not configured
- **Task 3 (Projects):** Investigated — FULLY ACTIVE with 17+ backend endpoints and 3 frontend components
- **Task 4 (Orphans):** Investigated — SalesOrders and TimeTracking are BOTH actively routed, not orphaned
- **Task 5 (Skipped Test):** Fixed `test_upgraded_org_can_access_payroll` — root cause was password scrubbing breaking test user login. Removed skip, now passes
- **Task 6 (HR/Payroll):** Created `test_hr_payroll_comprehensive.py` (27 tests), all passing. Fixed `organization_id` bug in `hr_service.py:create_employee`
- **Bug fixes:** Credit notes collection mismatch (invoices vs invoices_enhanced), 17 test files with empty BASE_URL, test user password restoration

### Previous Clusters
- Git history secret scrubbing (3 passes + gitleaks deep scan)
- Security: CORS hardening, brute-force protection
- Frontend: Cursor pagination modernization
- Testing: 693+ passing tests

## Current Status
- **906 passed, 13 skipped, 0 failed** (core tests — target 900+ achieved)
- All services healthy: backend, frontend, MongoDB
- Phase 2 Cluster 4 Part 2 — COMPLETE. Platform ready for founder QA.

## Completed Work — Cluster 4 Part 2 (2026-03-01)
- **Task 0 (AMC RBAC Fix):** Added "owner" role to AMC require_admin — org owners can now access AMC endpoints.
- **Task 1 (Customer Portal):** `test_customer_portal_comprehensive.py` — 18 passed. Fixed CSRF middleware + Tenant Guard exemptions for portal routes.
- **Task 2 (Tech Portal):** `test_tech_portal_comprehensive.py` — 17 passed. Tested dashboard, tickets, attendance, leave, payroll, productivity, AI assist, RBAC.
- **Task 3 (Skipped Tests):** Reduced skips from 19→13. Fixed 6 P0 tests (wrong credentials, wrong login path, wrong BASE_URL in test_p0_security_fixes.py).
- **Task 4 (Coverage Report):** 1,181 total endpoints, 906 tests passing, 18 modules with comprehensive tests.
- **Task 5 (Pre-QA Verification):** Full verification suite passed. Created docs/QA_TESTING_GUIDE.md.

## Completed Work — Cluster 4 Part 1 (2026-03-01)
- **Task 1 (Platform Admin):** `test_platform_admin_comprehensive.py` — 33 passed. Mapped 26 endpoints.
- **Task 2 (AMC):** `test_amc_comprehensive.py` — 17 passed. Plans CRUD + Subscriptions lifecycle + analytics.
- **Task 3 (Reports):** `test_reports_comprehensive.py` — 24 passed. Financial reports (8 endpoints) + Advanced reports (13 endpoints).
- **Task 4 (Sales Orders):** `test_sales_orders_comprehensive.py` — 18 passed. Full CRUD + status + clone + reports. Fixed `extract_org_id` bug in `sales_orders_enhanced.py`.
- **Task 5 (Time Tracking):** `test_time_tracking_comprehensive.py` — 16 passed. Entries CRUD + timer start/stop + unbilled hours + summary.

## Completed Work — Cluster 3 Part 2 (2026-03-01)
- **Task 1 (Inventory Tests):** `test_inventory_comprehensive.py` verified — 22 passed, 1 skipped
- **Task 2 (Contacts Tests):** `test_contacts_comprehensive.py` verified — 24 passed
- **Task 3 (Projects Tests):** `test_projects_comprehensive.py` fixed (payload keys: `name`→`title`, `hours`→`hours_logged`) — 17 passed
- **Task 4 (Frontend JWT Expiry):** Global fetch wrapper in `App.js` intercepts 401s, clears session, redirects to `/login`
- **Task 5 (Final Verification):** Full core suite: **763 passed, 13 skipped, 0 failures**
- **Infra fixes:** Rate limiter TESTING bypass (middleware), session-scoped login_attempts cleanup in conftest.py, added 3 missing comprehensive suites to `run_core_tests.sh`

## Prioritized Backlog

### P0
- Founder manual QA testing (using docs/QA_TESTING_GUIDE.md)

### P1
- Decompose "God-Files" (Tickets, Estimates, EFI modules)
- Remediate Test Debt (26 test files per TEST_DEBT_REGISTER.md)
- Unskip remaining 41 tests where possible

### P2
- Backend Task Runner (Celery)
- Zendesk Integration (replace stub)
- Banking Cursor Pagination (backend + frontend)
- Frontend Test Suite (Jest/RTL or Cypress)
- Zoho API Integration (Phase 4)
- Twilio WhatsApp configuration

## Known Issues
- 13 tests skipped (4 Razorpay webhooks, 5 Form16 unimplemented, 2 test data, 1 entitlement-gated, 1 test data)
- test_hr_module.py has 4 failures + 12 errors (pre-existing, older fixture pattern)
- AMC RBAC now accepts "owner" role (fixed in Cluster 4 Part 2)
- Reports Advanced: gated by entitlements, 200 path data structure not verified
- Banking frontend not migrated to cursor pagination
- Razorpay uses test/disabled keys
- expert_queue_service.py uses stub ZendeskBridge

## Credentials
- Dev Admin: dev@battwheels.internal / DevTest@123
- Platform Admin: platform-admin@battwheels.in / DevTest@123
- Demo User: demo@voltmotors.in / Demo@12345
- AMC Admin: admin@battwheels.in / DevTest@123
- Technician: tech.a@battwheels.internal / TechA@123
