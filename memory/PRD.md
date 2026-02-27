# Battwheels OS — Product Requirements Document

## Original Problem Statement
Battwheels OS is a multi-tenant SaaS platform for automotive workshop management. The platform includes features for ticket management, invoicing, GST compliance, credit notes, banking, HR/payroll, RBAC, subscription management, and more.

## Current Phase
**Phase 2.5: Beta Launch Gate Sprint — COMPLETED**

## Phase 2.5 Results (Feb 27, 2026)
- **Task 1 (Signup Flow):** FIXED — role assignment bug (admin→owner), UserContext auth wrapper
- **Task 2 (GSTR-3B CN Tests):** FIXED — 15/15 passing
- **Task 3 (Test Rewrites):** COMPLETED — 30 tests fixed, 63%→86.1% pass rate (321/373)
- **Overall Score:** 78-80/100 → **86/100** — BETA GATE PASSED

## Key Fixes Applied
1. Fixed role assignment in organizations.py (admin→owner for new signups)
2. Introduced UserContext wrapper in auth middleware for consistent auth access
3. Fixed entity_crud.py NameError for require_technician_or_admin
4. Fixed period-lock date issues in test_credit_notes_p1.py
5. Updated stale test endpoints from /api/v1/bills/* to /api/v1/bills-enhanced/*
6. Fixed password validation assertions in test_password_management.py
7. Fixed role leakage ("DevTest@123"→"admin") in test_rbac_portals.py
8. Fixed endpoint paths in test_razorpay_integration.py
9. Fixed pagination response handling in test_tenant_isolation.py
10. Updated plan feature assertions in test_subscription_entitlements_api.py

## Prioritized Backlog

### P0 — Phase 3 (Pending User Approval)
- Await reviewer approval of Beta Gate Sprint report

### P1 — High Priority
- H-01/H-02: Implement pagination for 435+ unbounded database queries
- H-07: Seed staging database for proper QA environment

### P2 — Medium Priority
- Address remaining Medium/Low audit items
- Fix 52 skipped tests that need fixture data

## Architecture
- Backend: FastAPI + MongoDB
- Frontend: React
- Auth: JWT-based with UserContext wrapper
- Multi-tenant: Organization-scoped with X-Organization-ID header
- Integrations: Razorpay (payments), Resend (email), bleach (XSS sanitization)

## Test Status
- Core suite: 321 passed, 0 failed, 52 skipped (86.1%)
- Signup: 15/15, GSTR-3B: 15/15, Credit Notes: 16/16
