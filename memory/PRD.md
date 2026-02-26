# Battwheels OS — PRD & Development Status

## Original Problem Statement
Full-stack SaaS platform (React/FastAPI/MongoDB) for automotive service management with EFI AI diagnostics. After a 6-phase "Architectural Evolution Sprint", a full audit revealed 35/100 production readiness. User ordered a 10-fix Stabilisation Sprint followed by deep verification and 3 completion fixes.

## Current State: Post-Completion Fixes (Feb 2026)

### Stabilisation Sprint — 10 Fixes (All Verified)

| Fix | Status |
|-----|--------|
| FIX 1: JWT Unification | DONE |
| FIX 2: Platform Admin RBAC | DONE |
| FIX 3: server.py Decomposition | DONE |
| FIX 4: Trial Balance | DONE |
| FIX 5: Failure Card Modal | DONE |
| FIX 6: Employee Isolation | DONE |
| FIX 7: resolution_type Removal | DONE |
| FIX 8: Zoho Dead Code | DONE |
| FIX 9: Banking Module | DONE |
| FIX 10: Notifications org_id | DONE |

### Completion Fixes A/B/C (All Verified)

| Fix | Status | Details |
|-----|--------|---------|
| FIX A: JWT Migration (remaining 50%) | DONE | 18 files updated. 0 direct jwt imports/calls outside utils/auth.py. TenantGuard uses canonical decode_token. |
| FIX B: HR Routes Unified | DONE | Legacy routes/hr.py is active (with isolation). routes/hr_payroll_api.py removed from router. Isolation verified: Tech A/B see only own records. |
| FIX C: Trailing Slash Fix | DONE | @router.get("") added to contacts_enhanced.py and estimates_enhanced.py. 24/24 tests pass. |

### Architecture
```
/app/backend/
├── server.py (245 lines — app init, middleware, includes only)
├── schemas/models.py (60 Pydantic models)
├── routes/
│   ├── auth.py (login endpoint)
│   ├── auth_main.py (register, password mgmt)
│   ├── hr.py (ACTIVE HR — with employee data isolation)
│   ├── entity_crud.py, inventory_api.py, sales_finance_api.py, operations_api.py
│   └── ... (50+ route files)
├── utils/
│   ├── auth.py (CANONICAL JWT — SINGLE source of truth for encode/decode)
│   └── helpers.py
├── middleware/ (rbac.py, rate_limit.py)
├── core/tenant/guard.py (uses utils.auth.decode_token)
└── services/
```

### Key Credentials
- Dev: `dev@battwheels.internal` / `DevTest@123` (owner, org: dev-internal-testing-001)
- Tech A: `tech.a@battwheels.internal` / `TechA@123` (technician)
- Tech B: `tech.b@battwheels.internal` / `TechB@123` (technician)

### Testing Status
- Test suite: 24/24 PASS (test_stabilisation_sprint_fixes.py)
- JWT grep verification: 0 results (fully migrated)
- Employee isolation: Verified with 2 technician users
- All 13 stabilisation fixes verified

## P1 — Next Sprint (Stabilisation Mode)
- Period Locking (financial write endpoints — deferred since Week 3)
- Missing frontend pages: BalanceSheet, ProfitLoss, ForgotPassword
- Missing backend routes: delivery_challans, vendor_credits
- 33 dark+volt design violations
- Duplicate route files cleanup (bills.py vs bills_enhanced.py)

## P2 — Backlog (Feature Work — ON HOLD)
- Failure Card Insights Dashboard
- AIAssistant.jsx implementation
- Estimate-to-Ticket conversion flow
- 20+ unbounded DB queries (pagination)
- Finance & RBAC test coverage
- Fix Reverse Charge in GSTR-3B

## 3rd Party Integrations
- Gemini (EFI AI) — via Emergent LLM Key
- Resend (Email)
- Razorpay (Payments)
- Stripe (test mode)
- Sentry (Error Monitoring)
- WhatsApp — MOCKED

## Estimated Score: ~70/100
(up from 35/100 — security fixed, architecture clean, JWT unified, isolation verified)
