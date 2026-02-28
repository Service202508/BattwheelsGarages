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
  - 4A-01: Unskipped & fixed 47 of 51 skipped tests
  - 4A-02: Created 30 payroll statutory unit tests
  - 4A-03: Created dev platform admin + test fixtures
  - 4A-04: Refactored period lock to shared utility
  - 4A-05: Fixed batch payroll granular PF/ESI keys
  - Technician portal RBAC mapping added to middleware

## Prioritized Backlog

### P0 — Critical
- Sprint 4B: Compliance Tests (next sprint)
- GSTR-3B ITC Tables 4B/4D (currently hardcoded to zero)
- Knowledge pipeline incomplete: ticket closure -> knowledge_articles never auto-triggered

### P1 — High Priority
- Cursor-based pagination for all hard-capped queries
- Two disconnected failure card collections (`failure_cards` vs `efi_failure_cards`)
- Data contract gaps: 5 missing ticket fields, dtc_codes name mismatch
- EFI brain has no data (0 embeddings, 0 trees, 0 articles)
- `feed_efi_brain` not auto-triggered after ticket closure
- Fix `test_17flow_audit.py` BASE_URL issue
- Address 3 remaining skipped tests (complex inter-test dependencies)
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

## Test Baseline (Post Sprint 4A)
- Sprint-focused tests: 85 passed, 1 skipped
- Overall suite: 393 passed (pre-existing failures in legacy test files)
