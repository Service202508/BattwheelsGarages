# Battwheels OS — Product Requirements Document

## Original Problem Statement
Battwheels OS is a multi-tenant SaaS ERP platform for EV service businesses. The platform manages tickets, invoices, contacts, inventory, estimates, HR, banking, GST compliance, and more across three environments (dev/staging/production).

## Core Architecture
- **Backend:** FastAPI + MongoDB (motor) with multi-tenant isolation via `organization_id`
- **Frontend:** React with Shadcn/UI components
- **Databases:** battwheels_dev (development), battwheels_staging (staging), battwheels (production)
- **Auth:** JWT-based with role-based access control (RBAC)

## Key Documents
- `/app/ENVIRONMENT_SOP.md` — Three-environment discipline rules
- `/app/CODING_STANDARDS.md` — Multi-tenancy & data integrity rules (Pattern A/B/C)

## What's Been Implemented

### Production Reset & Verification (2026-02-27)
- Production and staging databases wiped clean (only platform-admin user + seed data)
- Password sanitization bug fixed (bleach.clean corrupting special characters)
- Login response password field leak patched
- `scripts/verify_prod_org.py` updated for SaaS architecture (0 orgs = PASS)
- Full test suite verified: 322 passed, 0 failed, 51 skipped

### H-01/H-02 Hard Cap Sprint (2026-02-27)
- **H-01:** All 11 completely unbounded queries (`.to_list(None)`) capped to 1000
  - services/fault_tree_import.py (1 query)
  - services/embedding_service.py (2 queries)
  - services/efi_embedding_service.py (4 queries)
  - services/data_sanitization_service.py (4 queries)
- **H-02:** 10 Tier 1 customer-facing queries capped from 10000 to 500
  - routes/contact_integration.py (3 queries)
  - routes/items_enhanced.py (7 queries)
- Export endpoints deliberately NOT touched (per instructions)

### Pattern A Remediation — items_enhanced.py (2026-02-27)
- **66 total violations fixed** across all 70 endpoints in items_enhanced.py
- Original 30 READ violations + 36 additional WRITE/CRUD violations discovered
- Every endpoint now includes `request: Request` param + `org_id = extract_org_id(request)`
- All queries include `"organization_id": org_id` in filters
- All inserts include `"organization_id": org_id` in documents
- 2 body param renames (BulkItemPriceSet, BulkActionRequest) to avoid Request naming conflict
- Automated scan confirms ZERO remaining violations
- Test suite: 322 passed, 0 failed, 51 skipped (no regressions)
- Production verified: ALL GREEN (6/6 PASS)

**Known gap:** `log_item_history` helper inserts history without org_id (requires signature change across callers)

### Full Codebase Audit — COMPLETED (2026-02-28)
- Comprehensive A-through-N audit completed with file:line citations
- Output: `/app/docs/REMEDIATION_AUDIT_2026.md` (1464 lines, 59 file citations, 641 table rows)
- Findings: 8 P0, 22 P1, 19 P2 items cataloged
- Key discoveries:
  - P0: 20 route files bypass RBAC (all `-enhanced` routes unmapped in ROUTE_PERMISSIONS)
  - P0: 5 services with ZERO tenant isolation (efi_decision_engine, efi_embedding_service, embedding_service, event_processor, scheduler)
  - P0: 11 EFI collections missing from TenantGuard TENANT_COLLECTIONS
  - P0: Professional Tax hardcoded flat ₹200 for all states
  - P1: Workflow chain broken at Steps 4→5 and 5→6

### RBAC Bypass Fix — P0-01 RESOLVED (2026-02-28)
- Added 20 missing route patterns to ROUTE_PERMISSIONS in middleware/rbac.py
- Changed fallthrough logic from "allow all authenticated" to 403 Forbidden deny-by-default
- Fixed regex patterns from `/.*$` to `(/.*)?$` to cover root-level paths (e.g., `/api/tickets`)
- Added 3 missing auth-related routes: change-password, switch-organization, employees
- Added technician to inventory roles (business requirement validated by test)
- Total patterns in RBAC map: 93 (up from 70)
- Verification: RBAC script ALL PASS, Core tests 322 passed / 51 skipped / 0 failed, Production ALL GREEN

### Sprint 1B — Tenant Isolation & Fail-Fast Fixes (2026-02-28)
- **P1-02 RESOLVED:** org_query() in utils/database.py now raises ValueError on None org_id instead of silently returning unscoped {}
- **P0-08 RESOLVED:** Added 11 missing EFI collections to TenantGuard TENANT_COLLECTIONS (efi_decision_trees, efi_sessions, learning_queue, embedding_cache, efi_events, emerging_patterns, symptoms, knowledge_relations, ai_queries, ai_escalations, notification_logs)
- **P0-06 RESOLVED:** All 4 scheduler jobs (overdue marking, recurring invoices, recurring expenses, payment reminders) now scope every DB operation by org_id extracted from source records
- **P1-03 RESOLVED:** All 4 notification_service.py DB operations now include org_id (log insert, ticket lookup, log query, stats aggregate)
- Verification: Core tests 322/0/51, Production ALL GREEN

### Sprint 1C — EFI Tenant Isolation (2026-02-28)
- **P0-02 RESOLVED:** efi_decision_engine.py — 8 functions updated with org_id parameter (efi_sessions, learning_queue, technician_action_logs all scoped)
- **P0-03/04 RESOLVED:** embedding_service.py — 4 embedding_cache operations scoped by org_id. failure_cards left untouched (Tier 2 shared brain)
- **P0-05 RESOLVED:** event_processor.py — efi_events, tickets, technician_actions all scoped. failure_cards marked SHARED-BRAIN. emerging_patterns now per-org via aggregation grouping
- **P1-01 RESOLVED:** items_enhanced.py — log_item_history now includes org_id in all 8 call sites
- Tier 2 (failure_cards, efi_decision_trees, knowledge_articles) intentionally left cross-tenant per architectural rule
- Verification: Core tests 322/0/51, Production ALL GREEN

### Sprint 2A — Indian Statutory Compliance (2026-02-28)
- State-wise Professional Tax slab calculations in services/hr_service.py
- Period lock enforcement on all journal entry postings in services/posting_hooks.py
- Indian fiscal year awareness in accounting reports (services/double_entry_service.py)
- Immutable audit trail for journal entry creation and reversals

### Sprint 2B — GST Compliance Fixes (2026-02-28)
- **P2-18 RESOLVED:** GSTIN checksum validation (Luhn mod-36 algorithm) in `compute_gstin_checksum()`, enforced by `validate_gstin()`
- **P1-09 RESOLVED:** GSTR-1 enhancements: B2CL/B2CS segregation, CDNR split (registered/unregistered), HSN summary by code+rate, credit note adjustments
- **P1-10 RESOLVED:** GSTR-3B enhancements: Table 3.2 (inter/intra-state B2C split), Table 4 (ITC categorization: imports, RCM, ISD, all other, reversed, ineligible)
- **UNBOUNDED RESOLVED:** All 8 `.to_list(10000)` queries in gst.py capped to `.to_list(5000)`
- Verification: Core tests 322/0/51, Production ALL GREEN

### Sprint 2C — Indian Payroll Statutory Compliance (2026-02-28)
- **P1-06/P1-07 RESOLVED:** PF wage ceiling at 15000, EPS/EPF split (8.33%/3.67%), employee PF uncapped at 12% of full basic
- **P1-08 RESOLVED:** PF admin charges (0.5%) and EDLI (0.5%) on capped pf_wages added to employer cost and CTC
- **Section I.4 VERIFIED:** ESI employer rate 3.25% was already correct; refactored with ESI_WAGE_CEILING=21000 constant
- **H.3 Carry-forward RESOLVED:** HSN summary endpoint org_id scoping added (routes/gst.py:1283)
- Constants added: PF_WAGE_CEILING=15000, ESI_WAGE_CEILING=21000 at module level
- Backward-compatible keys retained: pf_deduction, pf_employer
- Verification: Core tests 322/0/51, Production ALL GREEN

### Sprint 2D — Workflow Chain + Payroll Journal + Period Lock (2026-02-28)
- **P1-13A RESOLVED:** Payroll journal entry split into 16 granular lines (6 Dr + 10 Cr). Separate accounts for EPF/EPS/PF Admin/EDLI/ESI Employee/ESI Employer. Debit=Credit balance verified before posting.
- **P1-13B RESOLVED:** Estimate approval includes stock_warnings[] and next_action; ticket completion includes invoice check with next_action/invoice_prompt.
- **P1-13C RESOLVED:** Period lock check added to create_journal_entry in double_entry_service.py (lazy import from posting_hooks).
- **Regression fix:** Credit note journal date corrected from created_at to credit_note_date.
- Verification: Core tests 322/0/51, Production ALL GREEN

## Prioritized Backlog (Updated from Audit)

### P0 — Critical (Must Fix Before Production)
- ~~P0-01: 20 route files bypass RBAC~~ **RESOLVED 2026-02-28**
- ~~P0-06: Scheduler zero tenant isolation~~ **RESOLVED 2026-02-28**
- ~~P0-08: 11 EFI collections missing from TenantGuard~~ **RESOLVED 2026-02-28**
- P0-02 to P0-05: ~~EFI Tenant Isolation~~ **RESOLVED 2026-02-28 (Sprint 1C)**
- P0-02: EFI Decision Engine — zero tenant isolation (services/efi_decision_engine.py, 11 DB ops)
- P0-03: EFI Embedding Service — zero tenant isolation (services/efi_embedding_service.py, 6 DB ops)
- P0-04: Embedding Service — zero tenant isolation (services/embedding_service.py, 10 DB ops)
- P0-05: Event Processor — zero tenant isolation (services/event_processor.py, 21 DB ops)
- P0-06: Scheduler — zero tenant isolation, all jobs global (services/scheduler.py, 13 DB ops)
- P0-07: Professional Tax hardcoded flat ₹200 for all states (services/hr_service.py:462)
- P0-08: 11 EFI collections missing from TenantGuard TENANT_COLLECTIONS (core/tenant/guard.py:37-83)

### P1 — High Priority
- ~~P1-02: org_query silently drops org_id when null~~ **RESOLVED 2026-02-28**
- ~~P1-03: Notification service — no org_id~~ **RESOLVED 2026-02-28**
- ~~P1-01: log_item_history missing org_id~~ **RESOLVED 2026-02-28 (Sprint 1C)**
- P1-04: log_item_history missing org_id in inserted docs (routes/items_enhanced.py:2827)
- P1-04: 32+ queries with .to_list(5000-10000) remaining
- P1-05: No period lock enforcement on journal entry creation
- P1-06: PF ceiling not enforced (₹15,000 basic cap)
- P1-07-08: GSTR-1/3B compliance gaps
- P1-09: No fiscal year concept in accounting
- P1-10: RBAC fallthrough for unmapped routes
- P1-11: Workflow chain broken at Steps 4→5 and 5→6
- P1-12-17: Additional tenant isolation gaps in services

### P2 — Medium Priority / Backlog
- Cursor-based pagination to replace all hard caps
- 51 skipped tests need data fixtures
- CSRF secure flag, rate limiting in-memory
- Multiple mocked email/notification features
- Payroll statutory gaps (HRA exemption, 80C/80D, gratuity, bonus)
- GST gaps (e-Way bill, GSTR-2A/2B, annual return)
- Projects module skeleton needs expansion

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / v4Nx6^3Xh&uPWwxK9HOs

## 3rd Party Integrations
- Razorpay, Resend, bleach, bcrypt
- WhatsApp integration remains MOCKED
