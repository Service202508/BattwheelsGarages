# Battwheels OS — Product Requirements Document

## Original Problem Statement
Enterprise garage management platform (SaaS) covering:
- Multi-tenant ticket/job management
- Estimates, invoicing, credit notes
- GST compliance (GSTR-1, GSTR-3B, RCM, E-Invoice)
- Inventory and stock management
- Employee/HR management
- Customer portal
- Razorpay payment integration
- Subscription/entitlement management

## What's Been Implemented (Cumulative)

### Phase 0/0.5 — Setup & Emergency Fix (2026-02-27)
- Environment checks completed
- Live Razorpay keys replaced with test placeholders

### Phase 1 — Grand Audit (2026-02-27)
- Comprehensive 11-area audit conducted
- Report: `/app/GRAND_AUDIT_2026_02_27.md`
- Production readiness score: 68/100

### Phase 2 — Stabilization Sprint (2026-02-27)
All 9 fixes implemented and verified:

| Fix | Category | Status |
|---|---|---|
| Fix 1-3 | Tenant Isolation (CRITICAL) | DONE |
| Fix 4 | RBAC owner role (HIGH) | DONE |
| Fix 5 | CSRF middleware rebuild (CRITICAL) | DONE |
| Fix 6 | Input sanitization middleware (HIGH) | DONE |
| Fix 7 | GSTR-3B RCM rebuild (HIGH) | DONE |
| Fix 8 | Test suite triage (HIGH) | DONE |
| Fix 9 | Dead code cleanup (MEDIUM) | DONE |

**Final Score: 80/100** (up from 68/100)
**Report:** `/app/STABILIZATION_FINAL_2026_02_27.md`

### Additional Bugs Fixed During Sprint
- `entity_crud.py` dict attribute access error (caused 500 on vehicle listing)
- Ticket RBAC missing "owner" role (caused 403 for org owners)

## Architecture

```
/app
├── backend/
│   ├── middleware/
│   │   ├── csrf.py
│   │   ├── sanitization.py
│   │   ├── rbac.py
│   │   ├── rate_limit.py
│   │   └── tenant_guard.py
│   ├── routes/ (70+ route modules)
│   ├── services/
│   ├── schemas/
│   ├── tests/ (122 test files)
│   └── server.py
├── frontend/
│   └── src/
└── scripts/
    ├── run_core_tests.sh
    └── verify_prod_org.py
```

## Prioritized Backlog

### P0 — Beta Launch Blockers
- Await Phase 3 instructions from user

### P1 — High Priority
- H-01/H-02: Implement pagination for 435+ unbounded `.find()` queries
- H-07: Seed staging database with representative data for QA
- Rewrite 72 stale test assertions to match current API (path + response format)

### P2 — Medium Priority
- AIAssistant.jsx page build-out
- Failure Card Insights Dashboard
- Real E-Invoice NIC API implementation
- INCIDENTS.md documentation
- Zoho comment cleanup across route files

### P3 — Low Priority / Nice-to-have
- Estimate-to-Ticket conversion flow enhancement
- Category B/C test file cleanup/deletion
- Load testing suite

## Key Test Credentials
- Admin: `dev@battwheels.internal` / `DevTest@123`
- Technician: `tech.a@battwheels.internal` / `TechA@123`
- Dev org: `dev-internal-testing-001`

## Core Test Suite
Run: `bash /app/scripts/run_core_tests.sh`
Current pass rate: 235/373 (63%)
