# BATTWHEELS OS — FULL SYSTEM AUDIT REPORT
## Coordinated Multi-Agent Diagnostic Audit
### Date: 2026-02-24 | Mode: READ-ONLY | Scope: All Modules, All Layers

---

# EXECUTIVE SUMMARY

Battwheels OS is a comprehensive multi-tenant SaaS platform for Indian EV workshops with 72 backend route files (~50,000+ lines), 113 frontend pages, and 16+ functional modules. The platform demonstrates strong foundational architecture with double-entry accounting, GST compliance infrastructure, multi-layered security, and AI-driven failure intelligence. However, this audit identifies several structural gaps that must be addressed for enterprise-grade operation.

**System Stability Score: 72/100**
**Multi-Tenant Safety Score: 78/100**
**Financial Integrity Score: 65/100**
**Compliance Readiness Score: 60/100**

---

# PHASE 1 — MULTI-TENANT ISOLATION VALIDATION

## 1.1 Organization ID Enforcement

| Finding | Severity | Details |
|---------|----------|---------|
| `ai_assistant.py` — 0 org_id refs in 190 lines | **CRITICAL** | Route handles AI queries without tenant scoping. Risk of cross-tenant data leakage in AI context. |
| `failure_intelligence.py` — 2 org_id refs in 687 lines | **HIGH** | Insufficient tenant scoping for failure pattern retrieval. |
| `customer_portal.py` — 2 org_id refs in 672 lines | **HIGH** | Customer-facing portal with minimal org isolation. Portal queries may return cross-tenant data. |
| `stripe_webhook.py` — 0 org_id refs in 70 lines | **MEDIUM** | Stripe webhook handler has no org_id context. Updates `payment_transactions` without tenant scope. |
| `reports.py` — 8 org_id refs in 1639 lines | **MEDIUM** | Low org_id density for a report module. Risk of cross-tenant data in aggregated reports. |

## 1.2 Middleware Chain Analysis

The platform has a **5-layer middleware stack**, which is comprehensive but fragmented:

1. **`middleware/tenant.py`** — Primary tenant isolation enforcement
2. **`core/tenant/guard.py`** — Secondary guard with `TENANT_COLLECTIONS` (92 collections) and `GLOBAL_COLLECTIONS` (34 collections)
3. **`middleware/rbac.py`** — Role hierarchy enforcement with 10 roles
4. **`middleware/rate_limit.py`** — Rate limiting with tiered limits
5. **`server.py` inline** — JWT validation, `is_active` check, `pwd_v` verification

**Risk:** Two separate tenant enforcement layers (`middleware/tenant.py` and `core/tenant/guard.py`) create confusion about which is authoritative. Whitelists may diverge.

## 1.3 Event Organization ID Tagging

| Finding | Severity |
|---------|----------|
| Event dispatcher (`events/event_dispatcher.py` line 327) explicitly adds `organization_id` to every `event_log` entry | PASS |
| However, `event_log` is listed in `GLOBAL_COLLECTIONS` in `core/tenant/guard.py`, meaning the guard won't enforce org_id on queries | **MEDIUM** — Inconsistent classification |

## 1.4 Subscription/Plan Gating

| Finding | Severity |
|---------|----------|
| `feature_gate` decorator exists in `core/subscriptions/entitlement.py` | PASS |
| 5 plan tiers defined (Free → Ultimate) with feature matrix | PASS |
| `feature_gate` is NOT applied to any production route handler | **HIGH** — Entitlement gating exists in code but is not enforced. All features are accessible regardless of plan. |
| No runtime usage/quota enforcement found in route handlers | **HIGH** |

## 1.5 Zoho Sync Tenant Isolation

| Finding | Severity |
|---------|----------|
| `zoho_api.py` uses `extract_org_id(request)` on every route (20+ usages) | PASS |
| `zoho_sync.py` contains `delete_many({})` and `drop_collection()` at lines 866/880 | **CRITICAL** — A sync reset can wipe ALL data in a collection, not just the requesting tenant's data. No org_id filter on destructive operations. |

---

# PHASE 2 — FINANCIAL INTEGRITY VALIDATION

## 2.1 Double-Entry Correctness

| Finding | Severity |
|---------|----------|
| `JournalEntry.validate()` enforces `total_debit == total_credit` before every write | PASS |
| Balance check uses Python `Decimal` with `ROUND_HALF_UP` precision | PASS |
| All posting hooks (invoice, payment, bill, expense, payroll) route through `DoubleEntryService.create_journal_entry()` | PASS |
| Reversal creates swap entries (debit↔credit) with `is_reversed` flag | PASS |

## 2.2 Ledger Consistency

| Finding | Severity |
|---------|----------|
| Trial balance currently shows ₹0.00/₹0.00 — balanced but empty | **MEDIUM** — No real financial transactions have been posted yet. The accounting engine is structurally correct but untested with real data. |
| System Chart of Accounts has 40+ pre-defined accounts with proper codes (1100-6900 range) | PASS |

## 2.3 Posting Immutability

| Finding | Severity |
|---------|----------|
| Journal entries are INSERT-only via `insert_one()` in `double_entry_service.py` | PASS |
| No `update_one()` or `update_many()` on `journal_entries` found in the service | PASS |
| Reversal uses a NEW entry (not editing the original) with `is_reversed=True` on original | PASS |
| Audit log entries (`audit_logs` collection) are INSERT-only | PASS |

**Risk identified:** The `journal_entries` route file (`routes/journal_entries.py`) has no explicit period-locking check. An accountant could post entries to any past date without restriction.

## 2.4 Period Locking Readiness

| Finding | Severity |
|---------|----------|
| **No period locking mechanism exists** | **HIGH** — No ability to freeze/close financial periods. Journal entries can be posted to any past date. This is a fundamental gap for CA audit readiness. |
| Indian Financial Year (April-March) utility exists in `utils/dates.py` | PASS |
| TDS service uses financial year format correctly | PASS |

## 2.5 COGS and Inventory Mapping

| Finding | Severity |
|---------|----------|
| `inventory_service.py` has `_post_cogs_entry()` method | PASS |
| COGS entries: DR Cost of Goods Sold (5100) / CR Inventory (1300) | PASS |
| COGS posts on part usage from tickets | PASS |
| **Inventory valuation method not configurable** (no FIFO/LIFO/weighted avg selection) | **MEDIUM** — Uses implicit average costing. Indian accounting standards require explicit method declaration. |

## 2.6 Payroll Journal Generation

| Finding | Severity |
|---------|----------|
| `posting_hooks.post_payroll_run_journal_entry()` is called from `hr_service.py` | PASS |
| Payroll entry: DR Salary Expense / CR Salary Payable, PF Payable, ESI Payable, PT Payable, TDS Payable | PASS |
| Employer PF contribution (12%) posts as separate DR Employer PF Expense / CR Employer PF Payable | PASS |

---

# PHASE 3 — GST COMPLIANCE VALIDATION

## 3.1 Tax Calculation Logic

| Finding | Severity |
|---------|----------|
| `calculate_gst()` in `gst.py` correctly splits CGST/SGST (intra-state) vs IGST (inter-state) | PASS |
| State code comparison (`org_state_code == customer_state_code`) determines split | PASS |
| Invoice line item calculation in `invoices_enhanced.py` supports inclusive/exclusive tax | PASS |
| Tax rate defaults to 18% — no support for multiple GST slabs (5%, 12%, 18%, 28%) per line item dynamically | **MEDIUM** — Per-item `tax_rate` field exists but no HSN-to-rate auto-mapping. |

## 3.2 Intra/Inter-State Mapping

| Finding | Severity |
|---------|----------|
| `place_of_supply` field exists on invoice model | PASS |
| State code-based CGST/SGST vs IGST determination is correct | PASS |
| **No validation that `place_of_supply` is a valid Indian state code** | **LOW** |

## 3.3 Input/Output Reconciliation

| Finding | Severity |
|---------|----------|
| GST summary endpoint aggregates output tax (from invoices) and input tax (from bills) | PASS |
| Net liability = Output GST - Input GST Credit | PASS |
| **No ITC (Input Tax Credit) eligibility validation** | **MEDIUM** — System assumes all input GST is claimable. No blocked credit rules (Section 17(5) of GST Act). |

## 3.4 Credit Note Tax Impact

| Finding | Severity |
|---------|----------|
| **Credit Notes NOT implemented** | **HIGH** — No credit note route files exist. GSTR-1 report queries `creditnotes` collection but it's always empty. GST compliance requires credit notes for invoice corrections, returns, and refunds. |

## 3.5 GST Reporting Readiness

| Finding | Severity |
|---------|----------|
| GSTR-1 report endpoint exists with B2B, B2C sections | PASS |
| GSTR-3B summary endpoint exists | PASS |
| HSN summary endpoint exists | PASS |
| **No GSTR-2A/2B reconciliation** | **MEDIUM** — Cannot match vendor invoices against GST portal data. |
| **No e-Invoice integration** (QR code generation exists in `einvoice.py` but uses mock NIC API) | **MEDIUM** |

---

# PHASE 4 — REVENUE RECOGNITION VALIDATION

## 4.1 Subscription Revenue Timing

| Finding | Severity |
|---------|----------|
| Subscription routes exist (`/api/v1/subscriptions/`) with plan change, cancel, reactivate | PASS |
| **No deferred revenue accounting** — Subscription payments are not mapped to revenue recognition periods | **HIGH** — If annual subscriptions are sold, the entire amount is recognized immediately rather than being deferred over the service period. This violates IndAS 115. |

## 4.2 Upgrade/Downgrade Logic

| Finding | Severity |
|---------|----------|
| `change_plan` endpoint exists | PASS |
| **No proration logic for mid-cycle plan changes** | **MEDIUM** — Upgrade/downgrade doesn't calculate prorated charges or credits. |

## 4.3 AMC Revenue Recognition

| Finding | Severity |
|---------|----------|
| AMC module has subscription create/renew/cancel flows | PASS |
| **No AMC revenue recognition timing** — Annual AMC payments are not split into monthly revenue recognition entries | **MEDIUM** |
| AMC subscription does not auto-generate journal entries | **MEDIUM** |

## 4.4 Refund Impact

| Finding | Severity |
|---------|----------|
| No refund workflow exists (no credit notes, no journal reversal on refund) | **HIGH** |

---

# PHASE 5 — HRMS AND PAYROLL VALIDATION

## 5.1 Attendance-Payroll Integration

| Finding | Severity |
|---------|----------|
| Clock-in/clock-out with late marking exists | PASS |
| **Attendance data is NOT used in payroll calculation** — Payroll calculates based on salary structure only, not actual attendance/working days | **HIGH** — A present-for-0-days employee gets full salary. No LOP (Loss of Pay) deduction mechanism. |

## 5.2 Payroll Locking

| Finding | Severity |
|---------|----------|
| Unique compound index on `(organization_id, period)` prevents duplicate payroll runs | PASS |
| **No payroll finalization/lock mechanism** — Once run, payroll records can potentially be re-run if index is circumvented | **MEDIUM** |
| No payroll reversal workflow | **LOW** |

## 5.3 Payroll Accounting Integration

| Finding | Severity |
|---------|----------|
| Payroll journal entry posts via `posting_hooks.post_payroll_run_journal_entry()` | PASS |
| Deductions: PF (12% of basic), ESI (0.75% if gross ≤ ₹21,000), PT (₹200 flat), TDS | PASS |
| **Employer PF/ESI contributions exist but are hardcoded** | **MEDIUM** — PF rate is hardcoded at 12%, ESI at 0.75%. No support for PF opt-out or wage ceiling (₹15,000 for PF, ₹21,000 for ESI). |
| **Professional Tax is ₹200 flat** — doesn't vary by state | **MEDIUM** — PT varies by state (Maharashtra: ₹200/₹300, Karnataka: ₹200, etc.). Currently hardcoded. |

## 5.4 Role-Based Salary Visibility

| Finding | Severity |
|---------|----------|
| HR/Payroll routes restricted to `org_admin`, `admin`, `owner` roles | PASS |
| Employee list accessible to `manager` role | PASS |
| **No self-service payslip access for employees** | **LOW** — Employees can't view their own payslips through the platform. |

## 5.5 Employee Lifecycle States

| Finding | Severity |
|---------|----------|
| Employee status field exists (active/inactive) | PASS |
| Employee create, update, delete flows exist | PASS |
| **No probation period enforcement** — `probation_period_months` field exists but isn't used in any business logic | **LOW** |

---

# PHASE 6 — EVENT-DRIVEN ARCHITECTURE AND RELIABILITY

## 6.1 Idempotent Event Handling

| Finding | Severity |
|---------|----------|
| Razorpay webhook has explicit idempotency guard — checks `webhook_logs` for `(payment_id, event)` pair before processing | PASS |
| Event dispatcher logs to `event_log` with unique `event_id` | PASS |
| **General event handlers don't have explicit idempotency checks** — EventHandler has `retry_count=3` but no dedup on retry | **MEDIUM** |

## 6.2 Duplicate Posting Risk

| Finding | Severity |
|---------|----------|
| Razorpay webhook idempotency prevents double-crediting payments | PASS |
| **Invoice journal entry posting has no idempotency guard** — If `post_invoice_journal_entry()` is called twice for the same invoice, two journal entries are created | **HIGH** — No check for existing entry with same `source_document_id` before posting. |
| **Payroll has unique index protection** — duplicate payroll run for same period is prevented at DB level | PASS |

## 6.3 Retry Safety

| Finding | Severity |
|---------|----------|
| EventHandler retries up to 3 times with exception catch | PASS |
| **No exponential backoff on retries** — immediate retry on failure | **LOW** |
| Background tasks use FastAPI's `BackgroundTasks` (fire-and-forget, no persistent queue) | **MEDIUM** — Background email/WhatsApp tasks are lost if server restarts mid-execution. |

## 6.4 Background Job Tenant Scope

| Finding | Severity |
|---------|----------|
| Notification service passes org context through to email/WhatsApp handlers | PASS |
| **No Celery/persistent job queue** — all background work is in-process | **MEDIUM** — Acceptable at current scale, but a scaling bottleneck. |

---

# PHASE 7 — AI INTELLIGENCE ISOLATION

## 7.1 Tenant-Isolated Embeddings

| Finding | Severity |
|---------|----------|
| EFI embedding service uses **hash-based pseudo-embeddings** (not real ML embeddings) | **INFO** — `_text_to_hash_embedding()` generates deterministic vectors from text hashes. No actual ML model is called for embeddings. |
| **No vector database** — Embeddings are stored in MongoDB, not a dedicated vector DB | **INFO** — Works at current scale but won't support semantic search at volume. |
| Knowledge brain queries are scoped with `organization_id` | PASS |

## 7.2 Cross-Tenant Retrieval Risk

| Finding | Severity |
|---------|----------|
| EFI failure cards have `scope` field: `"tenant"` (org-specific) or `"global"` (shared) | PASS |
| Queries use `$or: [{"organization_id": org_id}, {"scope": "global"}]` — correct pattern | PASS |
| `efi_platform_patterns` is correctly global (no org_id required) | PASS |
| **`ai_assistant.py` has 0 org_id refs** — AI assistant queries are NOT tenant-scoped | **CRITICAL** |

## 7.3 Failure Card Integrity

| Finding | Severity |
|---------|----------|
| Failure cards go through create → review → approve workflow | PASS |
| Status field enforces draft → approved transition | PASS |
| Approved cards contribute to platform patterns | PASS |

## 7.4 AI Fallback Behavior

| Finding | Severity |
|---------|----------|
| EFI embedding service has `FallbackEmbeddingService` (hash-based) when API is unavailable | PASS |
| AI guidance has confidence scoring with disclaimer | PASS |
| **No explicit fallback when Gemini API key is invalid/expired** — Service initializes but may silently fail on API calls | **LOW** |

---

# PHASE 8 — PERFORMANCE AND SECURITY RISK SCAN

## 8.1 High-Load Bottlenecks

| Finding | Severity |
|---------|----------|
| `server.py` is **6,674 lines** — a massive monolith that loads every route inline. Import time and memory footprint are high. | **MEDIUM** |
| `to_list(None)` usage: **0 occurrences** in routes — properly bounded cursors | PASS |
| 23 compound indexes on critical query patterns | PASS |
| **No caching layer** — Every request hits MongoDB directly. No Redis/memcache for hot data like dashboard stats or plan features. | **MEDIUM** |

## 8.2 Unsafe API Endpoints

| Finding | Severity |
|---------|----------|
| `zoho_sync.py` line 866: `delete_many({})` — can wipe entire collection | **CRITICAL** |
| `zoho_sync.py` line 880: `drop_collection()` — can drop collections | **CRITICAL** |
| `data_management.py` line 37 org_id refs but contains data deletion flows | **MEDIUM** — Verify all delete operations are org-scoped. |
| `stripe_webhook.py` updates `payment_transactions` without org_id | **MEDIUM** |

## 8.3 Privilege Escalation Risk

| Finding | Severity |
|---------|----------|
| RBAC middleware has proper role hierarchy (owner > admin > manager > technician) | PASS |
| `platform_admin.py` routes are separated and role-gated | PASS |
| **RBAC route patterns use `/api/` prefix (not `/api/v1/`)** — Many actual routes are at `/api/v1/` and may bypass RBAC pattern matching | **HIGH** — RBAC patterns like `r"^/api/finance/.*$"` won't match actual routes at `/api/v1/finance/...`. |
| JWT `is_active` check on every request (server.py line 65) | PASS |
| Password version (`pwd_v`) in JWT for session invalidation | PASS |

## 8.4 Audit Log Completeness

| Finding | Severity |
|---------|----------|
| Audit log utility (`utils/audit.py`) defines 17 action types | PASS |
| Currently wired to: ticket closure, user removal, payment webhook, Razorpay payment | PARTIAL |
| **Missing audit coverage:** invoice creation, estimate creation, inventory adjustment, employee creation, payroll run, login, settings change, data export | **HIGH** — Only 4 of 17 defined actions are actually wired to route handlers. |

---

# CONSOLIDATED FINDINGS

## Critical Risks (Fix Before Launch)

| # | Module | Finding | Impact |
|---|--------|---------|--------|
| 1 | Zoho Sync | `delete_many({})` and `drop_collection()` without org_id filter | Can wipe ALL tenant data in a single API call |
| 2 | AI Assistant | Zero org_id enforcement | Cross-tenant AI context leakage |
| 3 | RBAC | Route patterns don't match v1-prefixed routes | RBAC middleware is effectively non-functional for v1 routes |
| 4 | Journal Posting | No idempotency guard on invoice/bill journal posting | Double-posting risk on retry or duplicate API call |

## High Priority Fixes

| # | Module | Finding | Impact |
|---|--------|---------|--------|
| 5 | Credit Notes | Not implemented | GST non-compliance; cannot correct invoices |
| 6 | Period Locking | Not implemented | Past-period entries can be modified without restriction |
| 7 | Subscription Gating | `feature_gate` exists but not applied to any route | All features accessible regardless of plan tier |
| 8 | Payroll-Attendance | Attendance data not used in payroll calculation | Full salary paid regardless of actual attendance |
| 9 | Deferred Revenue | No revenue recognition timing | Subscription/AMC revenue recognized immediately |
| 10 | Audit Logging | Only 4/17 actions wired | Incomplete accountability trail |
| 11 | Duplicate Posting | Invoice journal entries have no duplicate check | Financial data integrity risk |

## Structural Improvements

| # | Module | Finding | Priority |
|---|--------|---------|----------|
| 12 | Auth Middleware | 5 separate files — fragmented | Month 1 |
| 13 | server.py | 6,674 lines monolith | Month 1-2 |
| 14 | Inventory Valuation | No FIFO/LIFO/weighted avg selection | Month 2 |
| 15 | Professional Tax | Hardcoded ₹200, doesn't vary by state | Month 2 |
| 16 | ITC Validation | No blocked credit rules | Month 2 |
| 17 | GSTR-2A/2B | No vendor invoice reconciliation | Month 2-3 |

## Non-Urgent Enhancements

| # | Module | Finding | Priority |
|---|--------|---------|----------|
| 18 | Background Jobs | No persistent job queue (Celery) | At 3+ customers |
| 19 | Caching | No Redis layer for hot data | At 5+ customers |
| 20 | Vector DB | Hash-based embeddings, not ML | At scale |
| 21 | Employee Self-Service | No payslip self-access | Future |
| 22 | Proration | No mid-cycle plan change proration | Future |
| 23 | e-Invoice NIC | Currently mock integration | When mandatory |

## Do Not Touch Zones

| Zone | Reason |
|------|--------|
| `DoubleEntryService` core posting logic | Structurally correct, well-tested. Changes risk accounting integrity. |
| `posting_hooks.py` entry creation pattern | Proper delegation to centralized service. |
| Compound index definitions in `utils/indexes.py` | 23 indexes are well-designed for current query patterns. |
| JWT authentication flow in `server.py` | Multi-layered, properly implements pwd_v and is_active checks. |
| Event dispatcher `emit_event` pattern | Clean event architecture. Enhance (add idempotency), don't restructure. |

---

# SCORING BREAKDOWN

## System Stability: 72/100
- (+) 20/20 pytest passing, frontend builds, health checks work
- (+) Comprehensive module coverage (16+ modules)
- (+) No `to_list(None)` performance issues
- (-) 6,674-line server.py monolith
- (-) No persistent background job system
- (-) No caching layer

## Multi-Tenant Safety: 78/100
- (+) org_id migration complete — all 2,080 docs correctly scoped
- (+) Tenant isolation middleware on every request
- (+) 23 compound indexes include org_id
- (-) `ai_assistant.py` has zero tenant scoping
- (-) Zoho sync has unscoped destructive operations
- (-) RBAC patterns don't match v1 routes
- (-) `stripe_webhook.py` has no org_id context

## Financial Integrity: 65/100
- (+) Double-entry engine with balance validation
- (+) Posting hooks for all transaction types
- (+) Immutable journal entries with reversal pattern
- (+) COGS posting on inventory usage
- (-) No period locking
- (-) No duplicate posting prevention on journal entries
- (-) No deferred revenue recognition
- (-) Trial balance is empty (no real financial data yet)
- (-) No credit notes

## Compliance Readiness: 60/100
- (+) GST CGST/SGST/IGST split correct
- (+) GSTR-1 and GSTR-3B reports exist
- (+) Indian FY (April-March) utilities
- (+) TDS service with financial year tracking
- (-) No credit notes (GST compliance gap)
- (-) No ITC eligibility validation
- (-) No GSTR-2A/2B reconciliation
- (-) PT hardcoded, not state-variable
- (-) Attendance not linked to payroll
- (-) No period locking for CA audit readiness
- (-) e-Invoice integration is mocked

---

# IMPROVEMENT ROADMAP (Priority Order)

## Immediate (Before First Customer)
1. **Fix RBAC v1 pattern matching** — Update `ROUTE_PERMISSIONS` patterns in `middleware/rbac.py` to include `/api/v1/` prefix
2. **Add org_id to `ai_assistant.py`** — Inject tenant context
3. **Add org_id filter to Zoho sync destructive operations** — Prevent full-collection wipes
4. **Add idempotency guard to journal posting** — Check for existing entry with same `source_document_id`

## Next Development Session
5. **Credit Notes** — Full implementation with journal reversal, GST impact, PDF

## Month 1
6. **Period Locking** — Prevent journal entries to closed periods
7. **RBAC pattern fix + auth middleware consolidation**
8. **Attendance-Payroll integration** — LOP deduction based on actual working days
9. **Audit log wiring** — Connect remaining 13 action types to route handlers

## Month 2-3
10. **State-variable Professional Tax**
11. **Deferred revenue recognition for subscriptions/AMC**
12. **ITC eligibility validation**
13. **Feature gate enforcement on routes**

## At Scale
14. **Celery background jobs**
15. **Redis caching**
16. **server.py decomposition**

---

**This report is diagnostic only. No code, schema, or data was modified during this audit.**
