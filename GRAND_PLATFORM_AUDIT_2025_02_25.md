# BATTWHEELS OS — GRAND AUDIT REPORT
## Read-Only SaaS Platform Audit
**Date:** 2026-02-25 | **Scope:** All 10 audit domains | **Mode:** Read-only, no changes

---

# A. EXECUTIVE SUMMARY

Battwheels OS is a multi-tenant EV SaaS platform with 222 MongoDB collections, 70+ route modules, and integrations with Razorpay, Zoho, Resend, Sentry, and Gemini AI. The P0 security fixes (RBAC, Zoho, AI scoping, Journal idempotency) and P1 Credit Notes were recently implemented and are verified working.

**Critical findings:** 22 routes with DB access lack explicit org_id scoping (rely on middleware propagation — must be verified per-route). Dual JWT secrets remain across `server.py` (JWT_SECRET) and `routes/auth.py` (SECRET_KEY). No period locking exists. No deferred revenue support. 96 collections with zero documents have no org_id field validation. Sentry lacks org context tagging.

**Production verdict: NOT READY FOR GA. Ready for limited beta with a defined set of known-trusted orgs, provided the 6 critical findings are remediated first.**

---

# B. READINESS SCORECARD

| Domain | Score | Status |
|--------|-------|--------|
| System Stability | 7/10 | Functional, hot reload stable |
| Multi-Tenant Safety | 6/10 | Middleware enforced but 22 routes lack explicit scoping |
| Security | 5/10 | RBAC fixed but dual JWT secrets remain; no rate limit on sensitive ops |
| Financial Integrity | 7/10 | Double-entry balanced, idempotency fixed, but no period lock |
| Compliance Readiness | 5/10 | GSTR-1/3B present, CN built, but no credit note GST reversal in GSTR, no ITC recon |
| Operations Readiness | 7/10 | Ticket lifecycle works, estimates→invoice chain exists |
| Integration Readiness | 6/10 | Razorpay verified, Zoho scoped, WhatsApp mocked |
| EFI Safety | 7/10 | AI org-scoped, session isolated, no RAG currently |
| UX Readiness | 6/10 | Dark theme consistent, but EstimatesEnhanced known broken |

---

# C. FINDINGS TABLE

## CRITICAL

| # | Finding | Module | Evidence | Impact | Remediation | Tests |
|---|---------|--------|----------|--------|-------------|-------|
| C-01 | **Dual JWT Secret** | Auth | `server.py:89` uses `JWT_SECRET` env var; `routes/auth.py:16` uses `SECRET_KEY` env var with different default. Tokens signed by one cannot be decoded by the other. | Auth bypass or lockout depending on which path is hit | Unify to single JWT_SECRET across all files | Token round-trip test: sign with server.py, decode in auth.py |
| C-02 | **22 Route Files Lack Explicit Org Scoping** | Multi-Tenant | `amc.py`, `business_portal.py`, `gst.py`, `notifications.py`, `organizations.py`, `permissions.py`, `platform_admin.py`, `productivity.py`, `technician_portal.py`, `zoho_api.py`, `zoho_extended.py`, `efi_guided.py`, `einvoice.py`, `export.py`, `fault_tree_import.py`, `master_data.py`, `seed_utility.py`, `tally_export.py`, `data_integrity.py`, `banking_module.py`, `uploads.py`, `auth.py` — all have DB calls but no `tenant_org_id`/`organization_id` from `request.state` | Cross-tenant data leakage if middleware doesn't propagate or if route reads from body/header | Audit each route: if it reads org_id from body/header/JWT rather than request.state, it's vulnerable | Per-route cross-tenant test with 2 orgs |
| C-03 | **No Period Locking** | Accounting | Zero results for `period_lock` / `close_period` / `lock_period` across entire codebase | Journal entries can be back-posted to closed financial periods; auditors cannot rely on closed-month integrity | Implement period lock with `locked_periods` collection + pre-insert check in double_entry_service | Post JE to locked period → expect 403 |
| C-04 | **`middleware/tenant.py` is DEAD CODE** | Architecture | `server.py:6632` mounts only `TenantGuardMiddleware` from `core/tenant/guard.py`. The `TenantIsolationMiddleware` class in `middleware/tenant.py` is never mounted. | Misleading during audits; developers may assume tenant isolation is active when it's not | Delete file or add deprecation notice | Static analysis: verify no import references |
| C-05 | **No Audit Logging on Financial Mutations** | Compliance | `invoices_enhanced.py`, `credit_notes.py`, `journal_entries.py` — zero calls to `audit_log`/`log_activity`/`event_log` for create/update/delete operations on financial documents | No forensic trail for invoice changes, CN issuance, or journal modifications; GST audit failure risk | Add `event_log` insert for every CUD operation on financial documents | Verify audit_logs collection has entry for each financial mutation |
| C-06 | **GSTR Reports Don't Include Credit Notes** | GST Compliance | `routes/gst.py:326-547` queries `invoices_enhanced` only for GSTR-1 report. No credit note inclusion (Section 9A of GSTR-1 requires CN reporting) | Under-reporting of tax adjustments to government; potential demand notice | Add credit_notes query to GSTR-1 and GSTR-3B report generators | Generate GSTR-1 for month with CNs → verify CN appears in Section 9A |

## HIGH

| # | Finding | Module | Evidence | Impact | Remediation | Tests |
|---|---------|--------|----------|--------|-------------|-------|
| H-01 | **Sentry Missing Org Context** | Observability | `server.py:58-71` initializes Sentry but never calls `set_tag("organization_id", ...)` or `set_context(...)` | Cannot triage production errors by tenant; all errors appear as one stream | Add `set_tag` in TenantGuardMiddleware after org validation | Trigger error → verify Sentry event has org_id tag |
| H-02 | **No Index on invoices_enhanced** | Performance | `invoices_enhanced` has only `_id` index (1 index total). No compound on `(organization_id, status, created_at)` | Full collection scans on every invoice list/filter query | Add compound index | Explain plan before/after |
| H-03 | **No Index on chart_of_accounts** | Performance | Only `_id` index. Account lookups by `(organization_id, account_code)` do full scans | Slow journal posting (multiple account lookups per entry) | Add `(organization_id, account_code)` unique index | Query explain before/after |
| H-04 | **WhatsApp Mock Safety** | Integration | `whatsapp_service.py` has no explicit mock flag. No grep results for `mock`/`MOCK`/`test_mode`. Need to verify it doesn't make real API calls | If WABA credentials are accidentally set, mock could send real messages | Add explicit `WHATSAPP_MODE=mock|live` env check | Set WABA creds + mock flag → verify no API call |
| H-05 | **Estimates Module Known Broken Chain** | Operations | `estimates_enhanced.py:2190` has convert-to-invoice but estimate edit/save has known bugs. Full chain: Estimate → Accept → Convert-to-Invoice → Send → Journal Post — need to verify each link | Revenue recognition chain is unreliable | Fix estimate edit bug first, then validate full chain | Create estimate → accept → convert → verify invoice has line items |
| H-06 | **Payroll PF/ESI Hardcoded Rates** | HR/Compliance | `hr_service.py:460-468`: PF rate 12%+1%, ESI 0.75%, PT ₹200 — all hardcoded. No config collection or rate table | Rate changes (ESI was updated in 2024) require code deployment; compliance risk | Create `statutory_rates` collection with effective dates | Change rate in DB → verify next payroll uses new rate |
| H-07 | **No Deferred Revenue Support** | Accounting | Zero results for `deferred_revenue`/`DEFERRED`/`unearned` in entire codebase | AMC subscriptions and advance payments cannot be correctly recognized over time; revenue over-statement risk | Implement deferred revenue account + recognition scheduler | Post AMC → verify revenue recognized over period |
| H-08 | **Credit Note Idempotency Gap at Application Layer** | Accounting | `credit_notes.py` creates the CN document before posting the journal entry. If journal posting fails (e.g., missing account), CN exists without a journal entry. No transaction wrapper. | Orphaned credit notes that reduce apparent outstanding but don't touch the books | Wrap CN creation + journal posting in a logical transaction (check journal success before committing CN) | Create CN with missing account → verify CN is not persisted |
| H-09 | **Subscription Gating Not Enforced on Routes** | SaaS | `core/subscriptions/entitlement.py` has `feature_gate` but no route uses `@feature_gate` decorator on financial routes. Only `efi_ai_guidance` is checked. | Free-tier orgs can access all features including invoicing, payroll, reports | Add `feature_gate` checks to key route handlers | Login as free-tier org → verify premium features return 403 |

## MEDIUM

| # | Finding | Module | Evidence | Impact | Remediation | Tests |
|---|---------|--------|----------|--------|-------------|-------|
| M-01 | **96 Empty Collections Without org_id Validation** | Data Integrity | `bills_enhanced`, `employees`, `payroll`, `payroll_runs`, etc. — 96 collections with 0 docs and no org_id field. When data is first inserted, nothing enforces org_id presence. | Future inserts may omit org_id, creating unscoped data | Add MongoDB schema validator requiring org_id on tenant collections | Insert doc without org_id → expect validation error |
| M-02 | **No Backup/Restore Strategy** | Reliability | No `mongodump` cron, no backup collection, no point-in-time recovery config | Data loss risk in production | Implement daily mongodump to S3 + test restore procedure | Backup → drop collection → restore → verify |
| M-03 | **IRN e-Invoice Error Handling** | GST | `einvoice_service.py` and `einvoice.py` have IRN generation but no org scoping in the route grep output (listed as NO_ORG_SCOPE) | IRN generation may not be org-scoped; error responses may leak | Verify org scoping in einvoice route handlers | Generate IRN for Org A → verify Org B cannot see it |
| M-04 | **No ITC Reconciliation** | GST | No code references to Input Tax Credit reconciliation, GSTR-2A/2B matching | Cannot reconcile purchase GST credits; potential ITC loss | Implement ITC tracking from bills/expenses against GSTR-2B | Mark bill as ITC eligible → verify in ITC report |
| M-05 | **Concurrency Safety on Finance Posting** | Accounting | `create_journal_entry` has idempotency via unique index, but `post_credit_note_journal` creates the CN doc first then posts — no optimistic locking on invoice `total_credits_applied` | Two concurrent CN creations could both pass validation before either updates the invoice | Use `findOneAndUpdate` with `$inc` + compare against limit atomically | Concurrent CN creation → verify only valid one succeeds |
| M-06 | **Contact Submissions Not Org-Scoped** | Multi-Tenant | `contact_submissions: 10 docs | org_id_field=NO` | Public submissions stored without org context | Add org derivation from form metadata | Verify submissions queryable by org |

## LOW

| # | Finding | Module | Evidence | Impact | Remediation | Tests |
|---|---------|--------|----------|--------|-------------|-------|
| L-01 | **Units Collection Not Org-Scoped** | Data | `units: 10 docs | org_id_field=NO` | Shared units across tenants (may be intentional for standard units) | Verify design intent — global or tenant-specific | N/A if intentional |
| L-02 | **Vehicle Categories/Models Not Org-Scoped** | Data | `vehicle_categories: 5, vehicle_models: 21` — no org_id | Shared lookup data (likely intentional for EV platform) | Verify design intent | N/A if intentional |
| L-03 | **Plans Collection Not Org-Scoped** | SaaS | `plans: 4 docs | org_id_field=NO` | Subscription plans are global (correct for SaaS) | No action needed — design correct | N/A |
| L-04 | **Demo Requests Not Org-Scoped** | Marketing | `demo_requests: 4 docs | org_id_field=NO` | Pre-signup data, no tenant context yet | Acceptable for marketing funnel | N/A |

---

# D. PRODUCTION VERDICT

## **NOT READY FOR GA**

### Hard Blockers (must fix before any customer-facing deployment):

1. **C-01: Dual JWT Secret** — Auth tokens may be incompatible between routes. Risk of auth failures in production.
2. **C-02: 22 Unscoped Routes** — Must verify each route derives org_id from `request.state.tenant_org_id` (set by TenantGuardMiddleware), not from request body or missing entirely.
3. **C-05: No Audit Logging on Financial Mutations** — GST audit compliance requires immutable trail of all financial document changes.
4. **C-06: GSTR Reports Missing Credit Notes** — Filing GSTR-1 without CN data is a compliance violation under Section 34 of CGST Act.

### Ready for Limited Beta with conditions:
- Fix C-01 (dual JWT) and C-06 (GSTR CN inclusion) first
- Deploy to max 2 known-trusted orgs
- Manual GSTR filing support (don't rely on auto-generated reports)
- Weekly trial balance verification
- No payroll module activation until PF/ESI rates are configurable

---

# E. 30-DAY PRIORITIZED REMEDIATION PLAN

### Week 1 — Security & Auth (Days 1-7)
- [ ] **Day 1-2:** Fix C-01 — Unify JWT secret (server.py + auth.py + utils/auth.py → single JWT_SECRET)
- [ ] **Day 2-3:** Fix C-04 — Delete or deprecate dead `middleware/tenant.py`
- [ ] **Day 3-5:** Fix C-02 — Audit all 22 unscoped routes. For each: verify org_id derivation source. Fix any that read from body/header instead of `request.state`
- [ ] **Day 5-7:** Fix H-01 — Add Sentry org context tagging

### Week 2 — Financial Integrity (Days 8-14)
- [ ] **Day 8-9:** Fix C-05 — Add audit logging to all financial CUD operations (invoices, CNs, journals, payments, expenses, bills)
- [ ] **Day 9-10:** Fix C-03 — Implement period locking (locked_periods collection + pre-insert check)
- [ ] **Day 10-11:** Fix H-08 — Wrap CN creation + journal posting in logical transaction
- [ ] **Day 11-12:** Fix H-02, H-03 — Add missing indexes on invoices_enhanced and chart_of_accounts
- [ ] **Day 12-14:** Fix M-05 — Atomic `total_credits_applied` update with race condition prevention

### Week 3 — Compliance (Days 15-21)
- [ ] **Day 15-16:** Fix C-06 — Add credit notes to GSTR-1 and GSTR-3B reports
- [ ] **Day 16-18:** Fix H-06 — Make PF/ESI/PT rates configurable via statutory_rates collection
- [ ] **Day 18-19:** Fix H-05 — Debug and fix estimates edit/save bug, validate full chain
- [ ] **Day 19-21:** Fix M-03 — Verify and fix e-Invoice IRN org scoping

### Week 4 — Hardening & Testing (Days 22-30)
- [ ] **Day 22-24:** Fix H-09 — Implement subscription feature gating on premium routes
- [ ] **Day 24-26:** Fix M-01 — Add MongoDB schema validators for critical tenant collections
- [ ] **Day 26-28:** Cross-tenant regression suite (2-org negative tests for all critical routes)
- [ ] **Day 28-30:** Staging protocol execution, go/no-go checklist, beta deployment prep

---

# F. VERIFICATION GAPS

**Areas the audit could NOT fully verify due to missing test data or environment constraints:**

| Area | Gap | Reason |
|------|-----|--------|
| Razorpay Webhook Live Flow | Cannot verify signature validation with real webhook events | No live Razorpay events in staging |
| WhatsApp Mock Isolation | Cannot verify mock doesn't leak to real API | No WABA credentials configured; `whatsapp_service.py` had zero grep results for mock/test flags — needs manual code review |
| Sentry Error Tagging | Cannot trigger real Sentry event to verify org context | SENTRY_DSN may not be configured in this environment |
| E-Invoice IRN Generation | Cannot test IRN API connectivity | Requires GSP credentials and sandbox access |
| Multi-Org Cross-Tenant Full Suite | Only 1 org exists with meaningful data | Need Org B with test data to run full cross-tenant negative tests |
| Backup/Restore | Cannot verify backup procedure | No backup cron or S3 config exists |
| Mobile Responsiveness | Not tested in this audit | Requires browser-based responsive testing |
| Concurrent Finance Posting Stress Test | Cannot simulate parallel requests in read-only audit | Requires load testing tool (k6, locust) |
| Subscription Tier Enforcement | Only 1 plan/subscription in DB | Need multiple tiers with feature restrictions to test gating |
| EFI Vector Embedding Isolation | `efi_embedding_service.py` returned zero org_id grep results AND `vector_embeddings: 0 docs` | No embeddings exist to test scoping; service may not be active |

---

# COLLECTION BASELINE

**Total collections in database: 222**
- With org_id field (populated): 126
- Without org_id field: 96 (includes 70+ empty collections, plus intentionally global ones like `plans`, `vehicle_models`, `units`)

This resolves the "23 vs 35" ambiguity from earlier architecture documents. The actual number is **222 collections**, of which approximately **45 are actively used with data**.

---

**END OF AUDIT REPORT**
**Classification:** Internal — Do Not Distribute
**Next Action:** User review → Approve remediation plan → Begin Week 1 fixes
