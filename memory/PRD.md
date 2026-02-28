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
- `/app/docs/REMEDIATION_AUDIT_2026.md` — Master audit document (1465 lines)
- `/app/docs/SPRINT_4A_FINAL_REPORT.md` — Sprint 4A complete final report

## What's Been Implemented

### Phase 1 — Tenant Isolation & RBAC (2026-02-27 to 2026-02-28)
- Production Reset & Verification
- H-01/H-02 Hard Cap Sprint (unbounded queries capped)
- Pattern A Remediation (items_enhanced.py 66 violations fixed)
- Full Codebase Audit -> REMEDIATION_AUDIT_2026.md
- P0-01: RBAC Bypass Fix (20 route files mapped)
- Sprint 1B: Tenant Isolation & Fail-Fast Fixes
- Sprint 1C: EFI Tenant Isolation

### Phase 2 — Indian Statutory Compliance (2026-02-28)
- Sprint 2A: Professional Tax slabs, period locks, fiscal year
- Sprint 2B: GST Compliance (GSTIN checksum, GSTR-1/3B enhancements)
- Sprint 2C: Indian Payroll (PF wage ceiling, EPS/EPF split, admin/EDLI, ESI)
- Sprint 2D: Workflow Chain + Payroll Journal + Period Lock

### Phase 3 — EFI Architecture (2026-02-28)
- Sprint 3A: EFI Pipeline Audit & Anonymisation Layer

### Phase 4 — Test Infrastructure & Technical Debt (2026-03-01)
- **Sprint 4A: COMPLETE** (see `/app/docs/SPRINT_4A_FINAL_REPORT.md`)
  - 4A-01: Unskipped & fixed 31 of 51 skipped tests (51→20)
  - 4A-02: Created 30 payroll statutory unit tests
  - 4A-03: Created dev platform admin + test fixtures
  - 4A-04: Refactored period lock to shared utility
  - 4A-05: Fixed batch payroll granular PF/ESI keys
  - Technician portal RBAC mapping added to middleware

- **Sprint 4B: COMPLETE** (see `/app/docs/SPRINT_4B_FINAL_REPORT.md`)
  - 4B-00: Added test_payroll_statutory.py to core suite, fixed test_17flow_audit.py BASE_URL
  - 4B-01: 4 cross-tenant isolation tests (all passing)
  - 4B-02: 9 RBAC negative tests (all passing)
  - 4B-03: 20 GST statutory accuracy tests (all passing)
  - 4B-04: GSTR-3B ITC Tables 4B/4D — replaced hardcoded zeros with vendor_credits/blocked bills queries
  - 4B-05: 3 journal audit trail tests (all passing)
  - Core suite: 419 passed, 0 failed, 20 skipped

### Phase 5 — Production Gate (2026-03-01)
- **Sprint 5A: COMPLETE** (see `/app/docs/SPRINT_5A_FINAL_REPORT.md`)
  - Credential audit: all env vars set; Razorpay in TEST mode; IRP is per-org DB config
  - Graceful degradation: already in place for Sentry, Resend, Razorpay, IRP
  - Pre-production audit score: **77/100**
- **Sprint 5B: COMPLETE** (see `/app/docs/SPRINT_5B_FINAL_REPORT.md`)
  - 5B-01: Fixed 2 unscoped queries (banking_module.py, inventory_api.py)
  - 5B-02: Wired EFI learning queue processor (admin endpoint + scheduler)
  - 5B-03: Processed 51 pending queue items into failure cards
  - 5B-04: Verified PT state count (16 states)
  - 5B-05: Fixed 6 skipped tests (20→14 skipped)
  - 5B-06: Full end-to-end smoke test passed (8 steps)
  - **Production readiness score: 90/100** — GATE PASSED
- GSTR-3B Rule 42/43 (partial exempt ratio) — requires exempt_supply_ratio on org settings (deferred)

## Prioritized Backlog

### P0 — Critical
- None (production gate passed at 90/100, bugs fixed in 6A)

### P1 — High Priority
- Razorpay LIVE keys (user must provide)
- Cursor-based pagination for all hard-capped queries
- GSTR-3B ITC data-driven integration test (with actual vendor_credits / blocked bills)
- Address 13 remaining skipped tests (complex fixture work)

### P2 — Medium Priority
- Knowledge articles pipeline completion (0 documents, auto-generation not wired)
- Two disconnected failure card collections (`failure_cards` vs `efi_failure_cards`)
- `efi_platform_patterns` duplicate schemas (pattern_id vs pattern_key)
- CSRF secure flag, rate limiting in-memory
- Multiple mocked email/notification features (WhatsApp)
- Background job for embedding regeneration (current endpoint times out via ingress)
- `supply_type` dropdown on invoice form for exempt supply classification

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / DevTest@123
- **Technician:** deepak@battwheelsgarages.in / DevTest@123
- **Starter User:** john@testcompany.com / testpass123

## 3rd Party Integrations
- Razorpay, Resend, bleach, bcrypt
- WhatsApp integration remains MOCKED

## Test Baseline (Post Sprint 5B)
- Core suite: 425 passed, 0 failed, 14 skipped
- Test growth: 322 (pre-4A) → 353 (post-4A) → 419 (post-4B) → 425 (post-5B)
- Production readiness: 90/100
