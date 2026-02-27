# Battwheels OS — PRD & Development Status

## Original Problem Statement
Full-stack SaaS platform (React/FastAPI/MongoDB) for automotive service management with EFI AI diagnostics. After a 6-phase "Architectural Evolution Sprint", a full audit revealed 35/100 production readiness. User ordered a 10-fix Stabilisation Sprint followed by deep verification and 3 completion fixes.

## Current State: Subscription Safety Complete (Feb 2026)

### Stabilisation Sprint — COMPLETE
All 10 fixes + 3 completion fixes + 3 cleanups verified and passing.

### Onboarding Critical Fixes (Feb 27, 2026) — COMPLETE

| Fix | Status | Details |
|-----|--------|---------|
| Fix A: Public Pattern /v1/ Mismatch | DONE | Updated RBAC + TenantGuard public patterns to include /api/v1/... paths. Registration, webhooks, login, password reset all unblocked. |
| Fix B: Org Slug Resolution | DONE | Rewrote get_org_from_request() to detect non-production hosts (emergentagent.com, emergentcf.cloud, localhost). Falls back to X-Organization-Slug header or ?org_slug= query param. |
| Fix C: Subscription Payment Flow | DONE | Built complete Razorpay subscription checkout: POST /subscribe creates Razorpay subscription, webhook handles activated/charged/halted/cancelled events, cancel endpoint, payment history, frontend checkout with Razorpay.js |

### Subscription Safety Fixes (Feb 27, 2026) — COMPLETE

| Fix | Status | Details |
|-----|--------|---------|
| Fix 1: Duplicate Subscription Prevention | DONE | Added check in POST /subscribe for existing active/created/authenticated/pending subscriptions in subscription_orders + org document. Returns 409 Conflict. |
| Fix 2: Live Key Safety Warning | DONE | Logs WARNING when rzp_live_* key detected in non-production ENVIRONMENT. ENVIRONMENT=development set in .env. |
| Fix 3: Auto-Trial on Registration | DONE | Signup now sets subscription_status=trialing, trial_active=true, trial_start=now, trial_end=now+14d on org document. |

### Onboarding Flow: 12/12 PASS
1. Register new org → 200 ✅
2. Chart of Accounts → seeds on first journal use
3. Admin invite users → 200 ✅
4. Configure org settings → 200 ✅
5. View subscription plans → 200 (public) ✅
6. Razorpay subscription checkout → real subscription created ✅
7. Webhook processes payment → org activated ✅
8. Welcome email → Resend configured and working ✅
9. Employee login → 200 ✅
10. Public ticket form → org_slug resolution working ✅
11. Customer submits ticket → 200 ✅
12. Ticket in org's All Tickets → visible ✅

### Architecture
```
/app/backend/
├── server.py (248 lines)
├── middleware/ (rbac.py — updated public patterns, tenant_guard.py)
├── core/tenant/guard.py (updated PUBLIC_ENDPOINTS + PUBLIC_PATTERNS)
├── routes/
│   ├── subscriptions.py (subscribe, cancel-razorpay, payment-history endpoints)
│   ├── razorpay.py (webhook handler for subscription.* events)
│   ├── public_tickets.py (updated get_org_from_request for non-production)
│   └── ... (all other routes)
├── utils/ (auth.py, period_lock.py, indexes.py — partial index fix)
└── services/
```

### Key API Endpoints (New)
- `POST /api/v1/subscriptions/subscribe` — Create Razorpay subscription checkout
- `POST /api/v1/subscriptions/cancel-razorpay` — Cancel subscription at period end
- `GET /api/v1/subscriptions/payment-history` — Payment receipts
- Webhook: `subscription.activated`, `subscription.charged`, `subscription.pending`, `subscription.halted`, `subscription.cancelled`

### Key Credentials
- Dev: `dev@battwheels.internal` / `DevTest@123` (owner)
- New: `rajesh.audit@battwheelsgarages.com` / `Garage@2026` (owner, org: org_d357321217cc)
- Tech A: `tech.a@battwheels.internal` / `TechA@123` (technician)

### Testing Status
- Stabilisation: 24/24 PASS
- Onboarding: 12/12 PASS
- Regression: No failures

## P2 — Backlog
- Failure Card Insights Dashboard
- AIAssistant.jsx implementation
- Estimate-to-Ticket conversion flow
- 20+ unbounded DB queries (pagination)
- Finance & RBAC test coverage
- Fix Reverse Charge in GSTR-3B
- Zoho dead code removal (823 references)
- contact_integration.py tenant isolation fix

## 3rd Party Integrations
- Razorpay (Subscription payments — LIVE)
- Gemini (EFI AI) — via Emergent LLM Key
- Resend (Email — LIVE)
- WhatsApp — MOCKED

## Estimated Score: ~80/100
(up from 78 — subscription safety fixes complete: duplicate prevention, live key warning, auto-trial)
