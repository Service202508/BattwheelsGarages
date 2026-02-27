# BATTWHEELS OS — GRAND AUDIT REPORT
**Date:** 2026-02-27
**Auditor:** Emergent Agent
**Method:** File inspection + live API tests + database queries

---

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Overall Score** | **62/100** |
| Critical Issues | 5 |
| High Issues | 8 |
| Medium Issues | 6 |
| Low Issues | 5 |

---

## AREA SCORES

| Area | Score | Notes |
|------|-------|-------|
| Codebase Structure | 7/10 | Well-decomposed routes, but 80 route files is high; dead code present |
| Database State | 5/10 | Duplicate collections, staging empty, production has 223 collections |
| Security Layers | 5/10 | TenantGuard + RBAC active, but NO CSRF, NO input sanitization middleware |
| Tenant Isolation | 3/10 | CRITICAL: contact_integration.py 33 unscoped queries; many routes use Optional org_id |
| Financial Engine | 7/10 | Double-entry works, period locking active, trial balance functional |
| GST Compliance | 6/10 | GSTR-1/3B exist, HSN present, but reverse charge 3.1(d) incomplete; credit notes don't create journal entries |
| Integrations | 6/10 | Razorpay live (now test keys), Resend live, Sentry configured, WhatsApp real code (not mocked), Gemini real |
| Frontend Completeness | 7/10 | 119 pages, dark theme applied, DataInsights functional, AIAssistant is a thin wrapper |
| Test Coverage | 4/10 | 122 test files but 798 failures / 308 passing — most tests are broken or stale |
| Tech Debt | 5/10 | 124 Zoho lines in routes, dead hr_payroll_api.py (1148 lines), 435 unbounded queries |

---

## AREA 1: CODEBASE STRUCTURE

| Category | Count |
|----------|-------|
| Backend route files | 80 |
| Frontend page files | 119 |
| Test files | 132 (122 test_*.py) |
| Root documentation files | 33 .md files |

**Critical file existence:**

| File | Status |
|------|--------|
| ENVIRONMENT_SOP.md | FOUND |
| CODING_STANDARDS.md | FOUND |
| PRE_DEPLOYMENT_AUDIT.md | FOUND |
| BATTWHEELS_OS_HANDOFF.md | FOUND |
| docs/INCIDENTS.md | **MISSING** |
| docs/PERIOD_LOCKING_DESIGN.md | FOUND |

---

## AREA 2: DATABASE STATE

### battwheels_dev (62 collections)

| Collection | Count |
|------------|-------|
| organizations | 12 |
| users | 15 |
| tickets | 31 |
| invoices | 8 |
| invoices_enhanced | 0 |
| journal_entries | 16 |
| audit_log | 7 |
| audit_logs | 0 |
| period_locks | 4 |
| credit_notes | 0 |
| contacts | 12 |
| vehicles | 8 |
| items | 0 |
| subscription_orders | 3 |
| subscription_payments | 2 |
| razorpay_plans | 2 |

### battwheels_staging (0 collections)
**EMPTY** — never been used. Staging environment is not set up.

### battwheels (production) (223 collections)
1 organization, 13 users, 10 tickets, 15 contacts, 12 items. Production data intact.

**Anomalies:**
- **Duplicate collections:** `audit_log` (7) vs `audit_logs` (0) in dev; both exist in prod (1 vs 31)
- **Duplicate collections:** `invoices` (8) vs `invoices_enhanced` (0) in dev; both in prod (2 vs 3)
- **Duplicate collections:** `contacts` (12) vs `contacts_enhanced` (0) in dev
- **Empty collections that should have data:** `items` (0), `invoices_enhanced` (0), `audit_logs` (0), `credit_notes` (0) in dev
- **Staging completely empty** — no QA gate exists

---

## AREA 3: SECURITY LAYERS

| Layer | Status | Evidence |
|-------|--------|----------|
| TenantGuardMiddleware | **ACTIVE** | `core/tenant/guard.py:403-472` mounted in `server.py:227` |
| RBAC Middleware | **ACTIVE** | `middleware/rbac.py` mounted in `server.py:226`, role-based checks on all routes |
| JWT Implementation | **ACTIVE** | Single canonical source: `utils/auth.py:18` reads `JWT_SECRET` from env. `business_portal.py:18` and `technician_portal.py:19` have `SECRET_KEY = None` (properly disabled) |
| CSRF Protection | **MISSING** | No CSRF middleware found anywhere in codebase |
| Input Sanitization Middleware | **MISSING** | No bleach middleware mounted. `data_sanitization_service.py` exists but is a batch tool, not request middleware. `ticket_service.py` does per-field sanitization for tickets only. |
| Rate Limiting | **ACTIVE** | `middleware/rate_limit.py` — auth_login: 5/min, auth_register: 3/hour, auth_password_reset: 5/hour |

**Public route bypasses (not requiring auth):**
- `/api/v1/organizations/signup`, `/register`, `/accept-invite`
- `/api/v1/auth/login`, `/register`, `/forgot-password`, `/reset-password`
- `/api/public/*`, `/api/v1/public/*`
- `/api/webhooks/*`, `/api/v1/razorpay/webhook`
- `/api/v1/customer-portal/auth*`
- `/api/v1/subscriptions/plans`, `/plans/compare`

---

## AREA 4: TENANT ISOLATION

**This is the most critical section.**

### contact_integration.py — 33 UNSCOPED QUERIES (CRITICAL)

Every query in this file queries by `contact_id` only, without `organization_id`:
- `contact_integration.py:26` — `find_one({"contact_id": contact_id})`
- `contact_integration.py:31` — `find_one({"contact_id": contact_id})`
- `contact_integration.py:41-57` — address lookups without org_id
- `contact_integration.py:63` — `find_one({"contact_id": ...})`
- `contact_integration.py:120,141` — contact listing without org_id
- `contact_integration.py:173-263` — invoices, bills, estimates, POs all queried without org_id
- `contact_integration.py:289-349` — statement queries without org_id
- `contact_integration.py:391-420` — financial summary without org_id
- `contact_integration.py:455-503` — migration tool (admin context)

### Broader Pattern Analysis

The grep-based scan flagged nearly all route files as having "unscoped" queries. However, deeper analysis reveals **two patterns**:

1. **Files using TenantContext properly:** `tickets.py`, `journal_entries.py`, `period_locks.py` etc. build queries with `ctx.org_id` on separate lines. The scan counts these as "unscoped" because the grep doesn't see `org_id` on the same line as `.find()`.

2. **Files using Optional org_id:** `invoices_enhanced.py`, `estimates_enhanced.py`, etc. use `org_query(org_id, ...)` helper where `org_id` can be `None`. If org_id resolution fails, queries run WITHOUT tenant scope.

### Collections missing org_id:
- `attendance`: 2 records, 0 with org_id
- `ticket_estimate_history`: 2 records, 0 with org_id

---

## AREA 5: FINANCIAL ENGINE

| Subsystem | Status | Evidence |
|-----------|--------|----------|
| Double-entry bookkeeping | **WORKING** | `services/double_entry_service.py` (65KB), imported by `journal_entries.py`, `hr.py` |
| Trial balance | **WORKING** | `GET /api/v1/banking/reports/trial-balance` returns 42 accounts |
| Period locking | **WORKING** | `routes/period_locks.py`, integrated into `journal_entries.py:177-178` and `invoices_enhanced.py:721-723`. Dev org has 4 active locks. |
| Credit notes | **PARTIAL** | Routes exist (`credit_notes.py`, 551 lines), but **no journal entries created** on CN issuance |
| Payroll → Accounting | **PARTIAL** | TDS deposit creates journal entries (`hr.py:969`), but **payroll run itself does NOT** create DR Salary Expense / CR payables entries |
| Inventory → COGS | **NOT FOUND** | No evidence of stock_movement creating COGS journal entries in route files |

---

## AREA 6: GST COMPLIANCE

| Item | Status | Evidence |
|------|--------|----------|
| GSTR-1 generation | **IMPLEMENTED** | `gst.py:330` — full B2B/B2C/CDN/HSN breakdown |
| GSTR-3B generation | **IMPLEMENTED** | `gst.py:688` — Section 3.1, 4, 6 |
| Credit note in GSTR-3B | **IMPLEMENTED** | `gst.py:455-488` — credit notes fetched and netted |
| Reverse charge 3.1(d) | **PARTIAL** | Section 3.1 exists (`gst.py:890`) but no separate 3.1(d) reverse charge subsection |
| E-Invoice/IRN | **PARTIAL** | `einvoice.py` exists (14KB), config management present, but no actual NIC API integration |
| HSN code handling | **IMPLEMENTED** | `gst.py:1013` — HSN summary endpoint |
| CGST/SGST/IGST split | **IMPLEMENTED** | `gst.py:136-149` — inter/intra state logic |

---

## AREA 7: INTEGRATIONS

| Integration | Status | Evidence |
|-------------|--------|----------|
| Razorpay | **CONFIGURED** (test keys) | Webhook handler with idempotency (`razorpay.py:580`), subscription flow, refund handling. Keys now `rzp_test_disabled` |
| Resend | **LIVE** | `email_service.py` uses `RESEND_API_KEY` from env, sending working |
| WhatsApp | **REAL CODE, NOT MOCKED** | `whatsapp_service.py` uses Meta Graph API v18.0. Requires per-org credentials via `credential_service`. Not a mock/stub — just needs config. |
| Sentry | **CONFIGURED** | DSN set in `.env`, `server.py:38-40` initializes with FastAPI integration, 10% trace sampling |
| Gemini AI (EFI) | **LIVE** | `ai_assistant.py:173` uses `gemini-3-flash-preview` via `emergentintegrations` |

---

## AREA 8: FRONTEND COMPLETENESS

| Module | Status | Notes |
|--------|--------|-------|
| Dashboard | Working | Dark volt theme |
| Data Insights | Working | Full chart implementation, no redirect issue |
| Platform Admin | Present | `PlatformAdmin.jsx` exists |
| Technician portal | Present | 7 pages under `technician/` |
| Customer portal | Present | 6 pages under `customer/` |
| Business portal | Present | 6 pages under `business/` |
| AI Assistant | **Stub** | 10-line wrapper delegating to `AIDiagnosticAssistant` component |
| Estimates | Present | `EstimatesEnhanced.jsx` |
| Subscription Management | Present | `SubscriptionManagement.jsx` with Razorpay.js integration |

**Total:** 119 JSX pages. Dark volt theme is globally applied.

---

## AREA 9: TEST COVERAGE

| Metric | Value |
|--------|-------|
| Total test files | 122 (test_*.py) |
| Tests passing | 308 |
| Tests failing | 798 |
| Tests skipped | 765 |
| Tests erroring | 642 |
| **Pass rate** | **~16%** |

**Critical paths WITH tests:** Multi-tenant isolation, RBAC, subscription entitlements, stabilization fixes, onboarding, subscription safety.

**Critical paths WITHOUT tests:** Period lock enforcement (integration test), credit note journal entries, payroll journal entries, GSTR-3B accuracy, inventory COGS flow.

**Note:** Many test failures appear to be from stale test credentials, missing test data, or tests written against deprecated APIs. The 24 stabilization tests previously reported as passing were via a separate testing method.

---

## AREA 10: DEAD CODE & TECH DEBT

| Item | Count/Status |
|------|-------------|
| Zoho references in routes | 124 lines across 29 files |
| hr_payroll_api.py (dead) | **EXISTS** — 1,148 lines of unused code |
| server.py size | 248 lines (good — was 6,727) |
| TODO/FIXME/HACK | 8 occurrences |
| Unbounded .find() queries | ~435 |
| Large .to_list() calls | 85 (to_list(1000) or similar) |
| Duplicate route files | `razorpay.py` + `razorpay_routes.py`, `banking.py` + `banking_module.py` |

---

## AREA 11: OPEN ITEMS FROM LAST SESSION

| Item | Status |
|------|--------|
| ~33 unscoped queries in contact_integration.py | **STILL PRESENT** |
| attendance collection missing org_id | **CONFIRMED** — 2 records, 0 with org_id |
| ticket_estimate_history missing org_id | **CONFIRMED** — 2 records, 0 with org_id |
| Subscription auto-trial | **WORKING** — verified: signup sets subscription_status=trialing, trial_active=true, trial_start, trial_end |
| Duplicate subscription prevention | **WORKING** — verified: returns 409 Conflict on second subscribe call |

---

## SECTION F — VERIFICATION GAPS

Things I **could not verify** and why:

1. **Razorpay webhook end-to-end** — Keys are now test placeholders (`rzp_test_disabled`), cannot create real subscriptions or trigger real webhook events. Idempotency logic was verified via code inspection only.
2. **Sentry error reporting** — DSN is configured, but I cannot trigger a monitored error and verify it appears in the Sentry dashboard. Verified initialization code only.
3. **WhatsApp message delivery** — No org has WhatsApp credentials configured. Code is real (not mocked) but untestable without Meta Business API credentials.
4. **E-Invoice/IRN generation** — `einvoice.py` has config management but no NIC API integration. Cannot test actual IRN generation.
5. **RBAC permission granularity** — Verified middleware is mounted, but did not exhaustively test every role×route combination. Newly registered admin users get 403 on `org:billing:update` permission, suggesting RBAC role initialization may be incomplete.
6. **Frontend page-by-page rendering** — Did not take screenshots of all 119 pages. Verified key pages (dashboard, data insights, subscription management) are functional via prior testing.
7. **Trial balance accuracy** — Endpoint returns 42 accounts but debit/credit totals were not in the expected response field. Could not confirm `is_balanced`.
8. **Payroll → journal entry integration** — TDS deposit creates journal entries, but could not verify a full payroll run → journal flow end-to-end.
9. **Production Razorpay subscriptions** — 1 active subscription (`sub_SL3uHYrWupJ0zx`) exists in dev `subscription_orders` from when live keys were in use. Cannot verify its state in Razorpay dashboard.

---

## CRITICAL FINDINGS (must fix)

| ID | Description | Location |
|----|-------------|----------|
| **C-01** | **Tenant isolation leak in contact_integration.py** — 33 DB queries lack `organization_id` filter. Any authenticated user could access another org's contacts, invoices, bills, estimates, and purchase orders via contact_id. | `routes/contact_integration.py:26-503` |
| **C-02** | **No CSRF protection** — Entire application has no CSRF middleware. State-changing POST/PUT/DELETE requests are vulnerable to cross-site request forgery. | Missing from `middleware/` and `server.py` |
| **C-03** | **No request-level input sanitization middleware** — Only `ticket_service.py` does field-level sanitization. All other routes accept raw user input into MongoDB. XSS/injection risk. | Missing from `middleware/` |
| **C-04** | **Optional org_id in major routes** — `invoices_enhanced.py`, `estimates_enhanced.py`, `contacts_enhanced.py` use `Optional[str]` for org_id via `get_org_id()` helper. If resolution fails, queries run with no tenant scope. | `routes/invoices_enhanced.py:54-70`, `routes/estimates_enhanced.py`, `routes/contacts_enhanced.py` |
| **C-05** | **attendance and ticket_estimate_history collections have no org_id** — 2 records each, none with organization_id. Data cannot be tenant-scoped. | DB: `attendance`, `ticket_estimate_history` |

## HIGH FINDINGS (fix this sprint)

| ID | Description | Location |
|----|-------------|----------|
| **H-01** | **435 unbounded .find() queries** — No pagination. Large datasets will cause memory exhaustion and timeouts. | Across all route files |
| **H-02** | **85 large .to_list() calls** — `to_list(1000)` or `to_list(10000)` will load enormous result sets into memory. | Across all route files |
| **H-03** | **Test suite 84% failure rate** — 798 failed, 642 errors. Tests are unreliable; cannot catch regressions. | `backend/tests/` |
| **H-04** | **Credit notes do not create journal entries** — CN issuance has no accounting integration. Financial reports will be inaccurate. | `routes/credit_notes.py` |
| **H-05** | **Payroll run does not create salary journal entries** — Only TDS deposit creates entries. Core payroll (DR Salary Expense / CR Payables) is missing. | `routes/hr.py` |
| **H-06** | **GSTR-3B reverse charge Section 3.1(d) incomplete** — No separate reverse charge subsection in the 3.1 output. | `routes/gst.py:890` |
| **H-07** | **Staging database empty** — No QA gate between dev and production. The promotion ladder from ENVIRONMENT_SOP.md is not operational. | DB: `battwheels_staging` |
| **H-08** | **RBAC role initialization incomplete for new orgs** — Newly registered admin/owner users get 403 on `org:billing:update`. RBAC initialization may not be granting all expected permissions. | `core/tenant/rbac.py` via `organizations.py:289-294` |

## MEDIUM FINDINGS (fix within 2 weeks)

| ID | Description | Location |
|----|-------------|----------|
| **M-01** | **Duplicate collections** — `audit_log` vs `audit_logs`, `invoices` vs `invoices_enhanced`, `contacts` vs `contacts_enhanced`. Confusing and risks data splits. | DB schema |
| **M-02** | **Dead code: hr_payroll_api.py** — 1,148 lines of unused Zoho-era payroll code. | `routes/hr_payroll_api.py` |
| **M-03** | **124 Zoho reference lines** — Legacy code across 29 route files. | `routes/*.py` |
| **M-04** | **Duplicate route files** — `razorpay.py` + `razorpay_routes.py`, `banking.py` + `banking_module.py`. | `routes/` |
| **M-05** | **docs/INCIDENTS.md missing** — Required by ENVIRONMENT_SOP.md Rule 7 for production incident tracking. | `docs/` |
| **M-06** | **E-Invoice/IRN is config-only** — No actual NIC API integration for IRN generation. | `routes/einvoice.py` |

## LOW FINDINGS (backlog)

| ID | Description | Location |
|----|-------------|----------|
| **L-01** | **8 TODO/FIXME/HACK comments** — Minor but should be tracked. | Various route/service files |
| **L-02** | **Inventory → COGS journal entries not implemented** — Part consumption doesn't create accounting entries. | Missing integration |
| **L-03** | **AIAssistant.jsx is a 10-line stub** — Just wraps AIDiagnosticAssistant component. | `pages/AIAssistant.jsx` |
| **L-04** | **Rate limiting only covers auth endpoints** — No rate limiting on data-heavy endpoints like reports, exports. | `middleware/rate_limit.py` |
| **L-05** | **WhatsApp integration untestable** — Real code exists but no org has credentials configured. | `services/whatsapp_service.py` |

---

## RECOMMENDED FIX ORDER

1. **C-01** — Fix tenant isolation in `contact_integration.py` (33 unscoped queries)
2. **C-04** — Make org_id REQUIRED (not Optional) in `invoices_enhanced.py`, `estimates_enhanced.py`, `contacts_enhanced.py`
3. **C-05** — Add org_id to `attendance` and `ticket_estimate_history` records + queries
4. **H-08** — Fix RBAC role initialization for new organizations (billing permissions)
5. **C-02** — Add CSRF protection middleware
6. **C-03** — Add request-level input sanitization middleware
7. **H-04** — Credit note → journal entry integration
8. **H-05** — Payroll run → salary journal entries
9. **H-06** — Complete GSTR-3B reverse charge section
10. **H-01/H-02** — Implement pagination for unbounded queries (phased, highest-traffic routes first)
11. **H-03** — Fix or remove broken tests; establish reliable regression suite
12. **M-02/M-03** — Remove dead Zoho code and hr_payroll_api.py
13. **M-01/M-04** — Consolidate duplicate collections and route files
14. **H-07** — Seed staging database for QA gate

---

*Report generated from live codebase inspection. No files were modified during this audit.*
