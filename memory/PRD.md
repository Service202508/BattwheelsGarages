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
- `/app/docs/SPRINT_6B_FINAL_REPORT.md` — Sprint 6B (Knowledge Pipeline) final report

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
- **Sprint 4A: COMPLETE** — 31 tests unskipped, 30 payroll tests, dev platform admin
- **Sprint 4B: COMPLETE** — Cross-tenant tests, RBAC tests, GST statutory tests, GSTR-3B ITC

### Phase 5 — Production Gate (2026-03-01)
- **Sprint 5A: COMPLETE** — Pre-production audit score: 77/100
- **Sprint 5B: COMPLETE** — Production readiness score: 90/100, GATE PASSED

### Phase 6 — Bug Fixes & Knowledge Pipeline (2026-02-28)
- **Sprint 6A: COMPLETE** — GST settings fix (Pattern A), org_state hardcode removed, EFI embeddings regenerated, Rule 42/43 implemented
- **Sprint 6B: COMPLETE** — Knowledge Pipeline:
  - 6B-01: Auto-generate knowledge articles from learning events
  - 6B-02: Seed 14 knowledge articles from failure cards
  - 6B-03: Fix 8 empty failure cards (populated from source tickets)
  - 6B-04: Wire knowledge articles into EFI suggestion response

## Prioritized Backlog

### P0 — Critical
- None (production gate passed, knowledge pipeline complete)

### P1 — High Priority
- Razorpay LIVE keys (user must provide)
- Cursor-based pagination for all hard-capped queries
- GSTR-3B ITC data-driven integration test
- Address 13 remaining skipped tests

### P2 — Medium Priority
- Knowledge article embeddings (for semantic search on articles)
- Two disconnected failure card collections (`failure_cards` vs `efi_failure_cards`)
- `efi_platform_patterns` duplicate schemas
- CSRF secure flag, rate limiting in-memory
- Multiple mocked email/notification features (WhatsApp)
- Background job for embedding regeneration (endpoint times out via ingress)
- `supply_type` dropdown on invoice form for exempt supply classification

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / DevTest@123
- **Technician:** deepak@battwheelsgarages.in / DevTest@123
- **Starter User:** john@testcompany.com / testpass123

## 3rd Party Integrations
- Razorpay (test keys), Resend, bleach, bcrypt
- Emergent LLM Key (gpt-4o-mini for hybrid embeddings)
- WhatsApp integration remains MOCKED

## Test Baseline (Post Sprint 6B)
- Core suite: 428 passed, 0 failed, 13 skipped
- Sprint 6B tests: 13/13 passed
- Test growth: 322 (pre-4A) → 353 (post-4A) → 419 (post-4B) → 425 (post-5B) → 428 (post-6A/6B)
- Production readiness: 90/100
