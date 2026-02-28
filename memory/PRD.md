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
  - 2 unscoped finds identified: banking_module.py:731, inventory_api.py:577
  - EFI learning queue: 33 pending items, no auto-processor
  - Sprint 5B: SIGNIFICANT WORK needed (+13 to reach 90/100)
- GSTR-3B Rule 42/43 (partial exempt ratio) — requires exempt_supply_ratio on org settings (Sprint 5A)
- Knowledge pipeline incomplete: ticket closure -> knowledge_articles never auto-triggered

### P1 — High Priority
- Cursor-based pagination for all hard-capped queries
- GSTR-3B ITC data-driven integration test (with actual vendor_credits / blocked bills)
- Two disconnected failure card collections (`failure_cards` vs `efi_failure_cards`)
- Data contract gaps: 5 missing ticket fields, dtc_codes name mismatch
- EFI brain has no data (0 embeddings, 0 trees, 0 articles)
- `feed_efi_brain` not auto-triggered after ticket closure
- Address 20 remaining skipped tests (complex inter-test dependencies / fixture infra)
- Subscription cache invalidation for test infrastructure

### P2 — Medium Priority
- `efi_platform_patterns` duplicate schemas (pattern_id vs pattern_key)
- CSRF secure flag, rate limiting in-memory
- Multiple mocked email/notification features

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / DevTest@123
- **Technician:** deepak@battwheelsgarages.in / DevTest@123
- **Starter User:** john@testcompany.com / testpass123

## 3rd Party Integrations
- Razorpay, Resend, bleach, bcrypt
- WhatsApp integration remains MOCKED

## Test Baseline (Post Sprint 4B)
- Core suite: 419 passed, 0 failed, 20 skipped
- New tests in 4B: 36 (cross-tenant: 4, RBAC negative: 9, GST statutory: 20, journal audit: 3)
- Overall suite growth: 322 (pre-4A) → 353 (post-4A) → 419 (post-4B)
