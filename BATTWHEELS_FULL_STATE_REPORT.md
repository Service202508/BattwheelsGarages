# BATTWHEELS OS - FULL STATE REPORT
**Date:** 2026-02-26
**Post-Sprint:** Architectural Evolution v2.5.0
**Environment:** battwheels_dev (development)

---

## SECTION 1 - Project Structure

| Metric | Count |
|--------|-------|
| Backend Python files | ~155 |
| Backend route files | 78 |
| Backend service files | 48 |
| Backend middleware files | 3 (rbac.py, tenant.py, rate_limit.py) |
| Frontend page components | 93 |
| Frontend custom components | ~24 |
| Frontend UI (Shadcn) components | ~60 |
| Test files | 118 |

### Files Over 500 Lines (Backend Routes)
| File | Lines |
|------|-------|
| estimates_enhanced.py | 3,007 |
| items_enhanced.py | 3,305 |
| zoho_api.py | 3,671 |
| zoho_extended.py | 2,983 |
| contacts_enhanced.py | 2,240 |
| invoices_enhanced.py | 2,392 |
| inventory_enhanced.py | 1,734 |
| sales_orders_enhanced.py | 1,557 |
| payments_received.py | 1,371 |
| hr.py | 1,906 (per ls -la ~75KB) |
| bills_enhanced.py | 961 |
| banking_module.py | 923 |
| amc.py | 843 |
| serial_batch_tracking.py | 814 |
| contact_integration.py | 783 |
| **server.py** | **6,727** |

### Files Over 500 Lines (Backend Services)
| File | Lines |
|------|-------|
| double_entry_service.py | 1,649 |
| ticket_estimate_service.py | 1,395 |
| efi_seed_data.py | 1,385 |
| ticket_service.py | 1,211 |
| ai_guidance_service.py | 1,069 |
| einvoice_service.py | 1,107 |
| pdf_service.py | 1,682 |
| failure_intelligence_service.py | 983 |
| fault_tree_import.py | 961 |

### Files Over 500 Lines (Frontend Pages)
| File | Lines |
|------|-------|
| EstimatesEnhanced.jsx | 2,966 |
| InvoicesEnhanced.jsx | 2,768 |
| ItemsEnhanced.jsx | 2,682 |
| OrganizationSettings.jsx | 2,626 |
| AllSettings.jsx | 2,439 |
| JournalEntries.jsx | 1,705 |
| Employees.jsx | 1,472 |
| InventoryAdjustments.jsx | 1,363 |
| InventoryEnhanced.jsx | 1,419 |
| Login.jsx | 1,142 |
| Projects.jsx | 1,150 |
| Reports.jsx | 1,106 |

### Stub/Empty Files
| File | Lines | Status |
|------|-------|--------|
| AIAssistant.jsx | 10 | STUB - essentially empty |
| middleware/tenant.py | 15 | DEPRECATED tombstone (correct) |

---

## SECTION 2 - Database

**Total Collections:** 47

### Collections With Data
| Collection | Documents | Uses organization_id |
|------------|-----------|---------------------|
| accounts | 11 | No (uses organization_id field name but field exists) |
| audit_log | 1 | Yes (org_id) |
| chart_of_accounts | 396 | Yes (organization_id) |
| contact_submissions | 6 | No - public submissions, correct |
| contacts | 8 | Yes (organization_id) |
| efi_platform_patterns | 3 | No - correctly anonymised |
| employees | 3 | Yes (organization_id) |
| event_log | 13 | Yes (organization_id) |
| failure_cards | 3 | Yes (organization_id) |
| inventory | 10 | Yes (organization_id) |
| invoices | 8 | Yes (organization_id) |
| journal_entries | 1 | Yes (organization_id) |
| migrations | 4 | No - platform global |
| notifications | 13 | No - should have org_id |
| organization_users | 2 | Yes (organization_id) |
| organizations | 2 | N/A - self-referencing |
| payroll_runs | 2 | Yes (organization_id) |
| plans | 4 | No - platform global |
| subscriptions | 2 | Yes (organization_id) |
| ticket_estimate_history | 2 | No - missing org isolation |
| ticket_estimate_settings | 1 | Yes (organization_id) |
| ticket_estimates | 2 | Yes (organization_id) |
| tickets | 27 | Yes (organization_id) |
| users | 2 | Yes (organization_id) |
| vehicles | 8 | Yes (organization_id) |

### Empty Collections (28 total)
attendance, audit_logs, bills, contact_history, counters, credit_notes, estimate_history, estimates, expenses, invoices_enhanced, items, leave_balances, ledger, password_reset_tokens, payment_modes, payments, sequences, taxes, ticket_activities

### Key Observations
- Field naming: System uses `organization_id` (not `org_id`) consistently across collections
- `notifications` collection (13 docs) has NO org_id - potential cross-tenant leak
- `ticket_estimate_history` has no org_id
- `accounts` collection (11 docs) uses `organization_id` field name
- `efi_platform_patterns` correctly has no org/tenant identifiers (anonymised)

---

## SECTION 3 - JWT/Auth

### JWT Implementations Found: **4** (CRITICAL)

| # | Location | Function | Secret Used | Payload Fields | Expiry |
|---|----------|----------|-------------|----------------|--------|
| 1 | `server.py:1166` | `create_token()` | `JWT_SECRET` | user_id, email, role, org_id, pwd_v, exp | 7 days |
| 2 | `routes/auth.py:52` | `create_access_token()` | `JWT_SECRET` | user_id, role, exp | 7 days |
| 3 | `utils/auth.py:47` | `create_access_token()` | `JWT_SECRET` | (pass-through dict + exp) | 7 days |
| 4 | `core/org/utils.py:41` | (inline decode) | **`SECRET_KEY`** (DIFFERENT!) | N/A | N/A |

### Critical JWT Issues

1. **`routes/auth.py` creates tokens WITHOUT `org_id`**: When the frontend uses `/api/auth/login` (which delegates to `auth.py`), the resulting token has NO `org_id`. This means TenantGuard cannot extract org context from these tokens.

2. **`core/org/utils.py` uses a DIFFERENT secret**: Uses `SECRET_KEY` env var (default: `battwheels_secret_key`) instead of `JWT_SECRET`. Any code that validates tokens through this path will fail for tokens created by other paths (and vice versa).

3. **`server.py` login vs `auth.py` login**: Both `/api/auth/login` exists. The actual endpoint called depends on which router is registered last. Investigation shows `auth.py` login is the one mounted (via `auth_router`), which creates tokens WITHOUT org_id.

   **However:** Looking at the actual login flow in `routes/auth.py`, after creating the initial token, the response also returns `organizations` and `current_organization`. The frontend then likely uses the server.py `/api/auth/switch-organization` to get a proper token WITH org_id.

### Token Validation Paths
| Component | Import Source |
|-----------|--------------|
| TenantGuardMiddleware | `core/tenant/guard.py` - uses `JWT_SECRET` |
| RBAC Middleware | Reads from `request.state.tenant_user_role` (set by TenantGuard) |
| `routes/auth.py /me` | Uses own `jwt.decode` with `JWT_SECRET` |
| `routes/hr.py` | Uses own inline `jwt.decode` with `JWT_SECRET` |
| `routes/failure_intelligence.py` | Uses own inline `jwt.decode` with `JWT_SECRET` |
| `core/org/utils.py` | Uses **`SECRET_KEY`** - DIFFERENT |

### RISK: HIGH
- Tokens created by `routes/auth.py` lack `org_id` -> TenantGuard may not enforce tenant isolation for these sessions until org switch
- `core/org/utils.py` uses different secret entirely -> any code path through there will reject valid tokens

---

## SECTION 4 - Tenant Isolation

### How org_id Enters the Request
1. TenantGuardMiddleware (`core/tenant/guard.py`) extracts `org_id` from JWT payload
2. Sets it on `request.state.tenant_org_id` (and `tenant_user_id`, `tenant_user_role`)
3. Many route handlers also get org_id via:
   - `TenantContext` dependency (`ctx.org_id`)
   - `request.state.org_id` or `request.state.organization_id` (inconsistent naming)
   - Direct DB lookup from user record

### Queries Without org_id Filter
Most route files use `organization_id` filters correctly. However:
- `contact_integration.py`: Multiple find queries use projection but some inline queries may not filter
- `reports_advanced.py`: Some aggregation pipelines
- `failure_intelligence.py`: Uses `service.db` directly
- Some endpoints in `server.py` inline routes get org_id from the JWT but need verification

### X-Organization-ID Header Usage
- `services/feature_flags.py` reads org_id from `X-Organization-ID` header (line 239, 280)
- Multiple test files send it as a header
- TenantGuard does NOT appear to validate header against JWT claim

### Potential Cross-Tenant Risks
1. `notifications` collection has no `organization_id` field at all
2. `ticket_estimate_history` has no `organization_id`
3. Feature flags service accepts org_id from HTTP header (user-controllable)

### RISK: MEDIUM
Core business routes use `organization_id` filtering. The risks are in edge collections and header-based org_id injection.

---

## SECTION 5 - RBAC

### Roles Defined
| Role | Inherits |
|------|----------|
| owner | All roles |
| admin | All roles |
| org_admin | org_admin, manager, accountant, technician, dispatcher, viewer |
| manager | manager, technician, dispatcher, viewer |
| hr | hr, viewer |
| accountant | accountant, viewer |
| technician | technician, viewer |
| dispatcher | dispatcher, viewer |
| customer | customer |
| fleet_customer | fleet_customer, customer |
| viewer | viewer |

### Route Protection Stats
- **Total @router decorators:** 1,325
- **With inline role checks (Depends/require_role):** 0
- **All RBAC enforcement via middleware pattern matching:** YES
- **Routes in ROUTE_PERMISSIONS map:** ~60 patterns covering all major modules

### CRITICAL RBAC ISSUES

1. **Platform Admin routes bypass RBAC entirely:**
   ```python
   PUBLIC_PATTERNS = [
       ...
       r"^/api/platform/.*",  # <-- ALL platform routes are PUBLIC
   ]
   ```
   Any authenticated user (even a viewer or technician) can access platform admin functionality.

2. **No inline role checks:** All 1,325 route handlers rely entirely on middleware pattern matching. If a route path doesn't match any pattern, it's allowed for ANY authenticated user.

3. **Routes not in permissions map are allowed:** The middleware explicitly says "Route not in permissions map - allow authenticated users" (line ~285 in rbac.py).

### HR Role: PROPERLY CONFIGURED
- HR can access: employees, attendance, leave, payroll, productivity
- HR blocked from: tickets, finance, invoicing, inventory
- Attendance/leave open to: technician, accountant (self-service)

### Employee Data Isolation: PARTIAL
- `get_current_user()` is called in HR routes
- But actual filtering of data to "own records only" for technicians is NOT visible in the route handlers
- A technician calling `/api/v1/hr/attendance/all` may see all employee attendance

---

## SECTION 6 - Ticket System (Phase 1)

| Feature | Status |
|---------|--------|
| `ticket_type` field | WORKING - auto-set by backend |
| Auto-detection logic | WORKING - onsite if customer_id present, workshop otherwise |
| Public form sets onsite | WORKING |
| Internal form sets workshop | WORKING |
| Filter tabs (All/Onsite/Workshop) | WORKING on Tickets.jsx |
| Type badges on ticket rows | WORKING |

### `resolution_type` Removal: **INCOMPLETE**

Still present in:
- `frontend/src/pages/TrackTicket.jsx` (line 394)
- `frontend/src/pages/business/BusinessTickets.jsx` (lines 55, 126, 311, 313, 432, 433, 447)
- `frontend/src/pages/PublicTicketForm.jsx` (line 92)
- `frontend/src/pages/technician/TechnicianTickets.jsx` (lines 286, 288, 290)
- `frontend/src/components/JobCard.jsx` (line 585)
- `backend/routes/business_portal.py` (lines 404, 454)
- `backend/routes/public_tickets.py` (line 569)

---

## SECTION 7 - Public Form (Phase 3)

| Feature | Status |
|---------|--------|
| Customer auto-detection by phone | WORKING - `/customer-lookup` endpoint |
| Contact auto-creation on new customer | WORKING |
| `resolution_type` removed from form | PARTIAL - still in initial state (line 92) |
| Subdomain routing for org resolution | CODE EXISTS but untestable in preview env |
| Dark + Volt design | YES |

---

## SECTION 8 - Estimate in Ticket (Phase 4)

| Feature | Status |
|---------|--------|
| `ticket_id` on estimates | WORKING - via `ticket_estimates` collection |
| Estimate panel on TicketDetail | WORKING - fetch + create buttons |
| Create estimate from ticket page | WORKING - `/ticket-estimates/tickets/{id}/estimate/ensure` |
| Line items CRUD | WORKING - add, update, delete endpoints |
| Standalone estimates still work | YES - `estimates_enhanced.py` is independent |
| Code duplication | NO - uses `ticket_estimate_service.py` (separate service) |

---

## SECTION 9 - Failure Cards (Phase 5)

| Feature | Status |
|---------|--------|
| Auto-creation on ticket close | WORKING - in `tickets.py:close_ticket()` |
| Failure card CRUD API | WORKING - `failure_cards.py` |
| Anonymisation function | WORKING - `ticket_service.py:_update_efi_platform_patterns()` |
| efi_platform_patterns has org_id | NO - correctly anonymised |
| Failure card visible on ticket detail | **NO** - zero references to failure cards in TicketDetail.jsx |
| Completion modal for technician | **MISSING** - not implemented |
| Brain feed on card update | WORKING - feeds to `efi_platform_patterns` |

---

## SECTION 10 - Feature Flags + Version + Migrations (Phase 6)

| Feature | Status |
|---------|--------|
| Feature flag utility | WORKING - `utils/feature_flags.py` (off/on/canary/percentage) |
| Feature flags configured | NONE - collection is empty (0 documents) |
| `/api/health` returns version | YES - "version": "2.5.0" |
| Version in frontend | **NOT DISPLAYED** |
| Migration system | WORKING - `runner.py` runs on startup |
| Migrations executed | 4/4 (all completed) |
| Feature flags service (AI) | EXISTS - `services/feature_flags.py` (default AI config) |

---

## SECTION 11 - Financial Engine

| Feature | Status |
|---------|--------|
| Double-entry system | REAL - `DoubleEntryService` (1,649 lines) |
| Invoice -> journal entry | YES - via `posting_hooks.py` |
| Bill -> journal entry | YES - via `posting_hooks.py` |
| Expense -> journal entry | YES - via `double_entry_service` |
| Payment -> journal entry | YES - via `posting_hooks.py` |
| COGS on parts consumption | YES - via `ticket_estimate_service.py` |
| GST calculation (CGST/SGST/IGST) | WORKING - `finance_calculator.py` |
| TDS calculation | WORKING - `tds_service.py` (TDSCalculator, Form16Generator) |

### Trial Balance: RETURNS 0/0 - ROOT CAUSE IDENTIFIED

**Three separate trial balance endpoints exist:**
1. `/api/v1/journal-entries/reports/trial-balance` - Uses `DoubleEntryService.get_trial_balance()` -> returns 0/0
2. `/api/v1/reports/trial-balance` - Uses inline aggregation on chart_of_accounts -> returns 0/0
3. `/api/v1/banking/reports/trial-balance` - **COMMENTED OUT** in server.py

**Root Cause:** The test journal entry was seeded into org `demo-volt-motors-001`, but the dev user `dev@battwheels.internal` belongs to org `dev-internal-testing-001`. The data exists but is in the wrong org scope.

**Banking module is completely commented out** in server.py (line 5894-5895).

---

## SECTION 12 - Sales/Purchases/Inventory

| Module | Status | Details |
|--------|--------|---------|
| Estimates (Enhanced) | FUNCTIONAL | 3,007 lines, full CRUD, convert to invoice/SO |
| Invoices (Enhanced) | FUNCTIONAL | 2,392 lines, full CRUD, journal posting |
| Sales Orders | FUNCTIONAL | 1,557 lines, full lifecycle |
| Payments Received | FUNCTIONAL | 1,371 lines, CRUD + allocation |
| Credit Notes | FUNCTIONAL | 546 lines, create + PDF |
| Bills (Enhanced) | FUNCTIONAL | 961 lines, CRUD + PO inside |
| Items (Enhanced) | FUNCTIONAL | 3,305 lines, full CRUD |
| Inventory (Enhanced) | FUNCTIONAL | 1,734 lines, stock management |
| Composite Items | FUNCTIONAL | 557 lines, BOM build/unbuild |
| Recurring Invoices | FUNCTIONAL | 475 lines, create/stop/resume |
| Serial/Batch Tracking | FUNCTIONAL | 814 lines |
| Stock Transfers | FUNCTIONAL | 508 lines |
| Delivery Challans | **MISSING** backend route (frontend exists at 291 lines) |
| Purchase Orders | **INSIDE** bills_enhanced.py (not standalone) |
| Vendor Credits | **MISSING** backend route (frontend exists at 238 lines) |
| Estimate-to-Invoice | WORKING | Both auto-convert and manual endpoint |

---

## SECTION 13 - HR & Payroll

| Feature | Status |
|---------|--------|
| Employee CRUD | WORKING |
| Attendance (clock in/out) | WORKING (endpoints exist) |
| Leave management | WORKING (request, approve, balance) |
| Payroll calculation | WORKING (PF, ESI, Professional Tax present) |
| Payslip PDF | ENDPOINTS EXIST (referenced in tests, PDF generation in pdf_service.py) |
| TDS / Form 16 | WORKING (TDSCalculator class) |
| Employee data isolation | **UI-ONLY** - backend routes call `get_current_user()` but do not filter attendance/payroll data by user_id for non-admin roles |

---

## SECTION 14 - EFI AI

| Feature | Status |
|---------|--------|
| Gemini integration | REAL - via `emergentintegrations` + Emergent LLM Key |
| LLM provider | `services/llm_provider.py` with factory pattern |
| Diagnostic inputs | Vehicle make, model, symptoms, DTC codes, conversation context |
| Diagnostic output | Fault diagnosis, suggested paths, confidence, resolution steps |
| AI Assistant | FUNCTIONAL - `/api/v1/ai-assist/diagnose` endpoint |
| EFI Guided Execution | FUNCTIONAL - decision trees, session tracking, smart estimates |
| Fault tree import | WORKING - endpoint + service exist |
| EFI Intelligence Engine | FUNCTIONAL - risk alerts, failure cards, learning pipeline |
| Model-aware ranking | EXISTS - `model_aware_ranking_service.py` |
| Knowledge Brain | EXISTS - ingestion, articles, embeddings |
| Frontend AIAssistant.jsx | **10-LINE STUB** - essentially empty |

---

## SECTION 15 - Frontend

### Pages Present: 90+ / ~95 expected

### Missing Pages
| Page | Status |
|------|--------|
| BalanceSheet | MISSING (backend exists at `/api/v1/reports/balance-sheet`) |
| ProfitLoss | MISSING (backend exists at `/api/v1/reports/profit-loss`) |
| ForgotPassword | MISSING (backend endpoint exists) |

### Near-Empty Stubs
| Page | Lines | Issue |
|------|-------|-------|
| AIAssistant.jsx | 10 | Essentially a redirect/placeholder |

### Design System Violations
- **33 instances** of light theme classes (`bg-white`, `bg-gray-50`, `text-gray-900`, etc.) across frontend pages
- These conflict with the Dark + Volt (#080C0F background, #C8FF00 accent) design system

### Role-Based Sidebar
- Sidebar lives in `components/Layout.jsx` (not a separate Sidebar.jsx)
- Role-based filtering IS implemented in the layout component

### Frontend Version Display
- **NOT implemented** - no version number shown anywhere in the UI

---

## SECTION 16 - Tech Debt

### Zoho Dead Code: **8,223 lines**
| File | Lines |
|------|-------|
| zoho_api.py | 3,671 |
| zoho_extended.py | 2,983 |
| zoho_sync.py | 918 |
| zoho_realtime_sync.py (service) | 651 |

### server.py Monolith: **6,727 lines**
| Metric | Count |
|--------|-------|
| Pydantic models inline | 68 |
| Functions | 140 |
| Inline routes (@v1_router / @api_router) | 121 |
| include_router calls | 78 |
| Lines of code | 6,727 |

**What server.py contains that should be extracted:**
- 68 Pydantic models (should be in `models/`)
- 121 inline route handlers for: users, suppliers, vehicles, inventory, job cards, invoices, payments, employees, HR, attendance, leave, payroll (should be in `routes/`)
- Auth login/register/session flows (duplicated with `routes/auth.py`)
- Utility functions (number_to_words, etc.)

### TODO/FIXME/HACK Comments
- Backend: 9 markers (6 are "TODO" as task status, 3 are real TODOs)
- Frontend: 3 markers
- **Low** - code is relatively clean of dangling TODOs

### Duplicate Route Files
- `banking.py` vs `banking_module.py` (banking_module is COMMENTED OUT)
- `bills.py` vs `bills_enhanced.py` (both active)
- `razorpay.py` vs `razorpay_routes.py` (both active)

---

## SECTION 17 - Tests

| Metric | Value |
|--------|-------|
| Test files | 118 |
| Tests collected | 2,456 |
| Collection errors | 1 (missing env var) |

### Module Test Coverage
| Module | Test Functions |
|--------|---------------|
| auth | 608 |
| ticket | 167 |
| invoice | 166 |
| estimate | 126 |
| contact | 82 |
| inventory | 54 |
| failure | 47 |
| payroll | 27 |
| efi | 23 |
| tenant | 13 |
| hr | 10 |
| finance | 3 |
| rbac | 1 |

### Modules with ZERO/Near-Zero Test Coverage
- **RBAC**: Only 1 test function
- **Finance**: Only 3 test functions (critical module!)
- **Period locking**: 0 (not implemented)
- **Feature flags**: 0
- **Banking module**: 0 (commented out)

---

## SECTION 18 - Pagination

| Metric | Count |
|--------|-------|
| Endpoints with pagination params | 257 |
| Unbounded find() queries | 20+ |

### Notable Unbounded Queries
- `contact_integration.py`: 10+ unbounded queries across invoices, bills, estimates, POs, credit notes, payments
- `reports_advanced.py`: Unbounded invoice queries
- `invoice_payments.py`: Unbounded invoice and credit lookups
- `failure_intelligence.py`: Unbounded technician_actions and emerging_patterns

---

## CRITICAL ISSUES (Must Fix Before Any More Features)

| # | Issue | File(s) | Risk |
|---|-------|---------|------|
| 1 | **4x JWT implementations with inconsistent payloads** - auth.py tokens lack org_id, core/org/utils.py uses different secret | server.py, routes/auth.py, utils/auth.py, core/org/utils.py | CRITICAL - security |
| 2 | **Platform Admin routes bypass RBAC** - `r"^/api/platform/.*"` in PUBLIC_PATTERNS | middleware/rbac.py | CRITICAL - security |
| 3 | **Trial Balance returns 0/0** - test data in wrong org | Dev data issue | HIGH - functionality |
| 4 | **121 inline routes in 6,727-line server.py monolith** | server.py | HIGH - maintainability |
| 5 | **Failure Card completion modal MISSING** | TicketDetail.jsx | HIGH - feature incomplete |
| 6 | **Period Locking NOT IMPLEMENTED** | N/A | HIGH - financial integrity |

## HIGH ISSUES (Must Fix Before Beta)

| # | Issue | File(s) | Risk |
|---|-------|---------|------|
| 7 | `resolution_type` remnants in 8+ files | Multiple frontend + 2 backend | MEDIUM |
| 8 | 8,223 lines of Zoho dead code | zoho_*.py | MEDIUM - maintenance |
| 9 | Banking module is commented out | server.py:5894 | MEDIUM |
| 10 | Employee data isolation is UI-only | routes/hr.py | MEDIUM - security |
| 11 | `notifications` collection missing org_id | DB schema | MEDIUM - data leak |
| 12 | No version displayed in frontend | Frontend | LOW |
| 13 | 33 light theme violations | Frontend pages | LOW - design |

## MEDIUM (Fix Within Next Sprint)

| # | Issue | File(s) |
|---|-------|---------|
| 14 | AIAssistant.jsx is 10-line stub | pages/AIAssistant.jsx |
| 15 | Missing backend: delivery_challans, vendor_credits | routes/ |
| 16 | Missing frontend: BalanceSheet, ProfitLoss, ForgotPassword | pages/ |
| 17 | Duplicate route files (banking, bills, razorpay) | routes/ |
| 18 | 20+ unbounded database queries | Various route files |
| 19 | Finance module has only 3 test functions | backend/tests/ |
| 20 | RBAC has only 1 test function | backend/tests/ |

---

## OVERALL ASSESSMENT

| Metric | Score |
|--------|-------|
| **Production Readiness** | **35/100** |
| Aligned with architectural vision | PARTIAL |
| Feature completeness | 65% |
| Security posture | POOR (JWT chaos, RBAC bypass, data isolation gaps) |
| Code quality | MEDIUM (works but monolithic, dead code) |
| Test coverage | LOW for critical paths (finance, RBAC, security) |

**Biggest Risk:** The 4x JWT implementation with the platform admin RBAC bypass means any authenticated user could potentially access admin functions, and tokens may not carry proper tenant context.

**Biggest Strength:** The financial double-entry engine is real and comprehensive. Invoice/bill/expense/payment all create proper journal entries. GST and TDS calculations are implemented. The EFI AI system is genuinely connected to Gemini and functional.
