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
- `/app/docs/REMEDIATION_AUDIT_2026.md` — Master audit document
- `/app/docs/SPRINT_6A_FINAL_REPORT.md` — Sprint 6A final report
- `/app/docs/SPRINT_6B_FINAL_REPORT.md` — Sprint 6B (Knowledge Pipeline) final report
- `/app/docs/SPRINT_6C_FINAL_REPORT.md` — Sprint 6C (Cursor Pagination) final report

## What's Been Implemented

### Phase 1 — Tenant Isolation & RBAC
- Production Reset & Verification, H-01/H-02 Hard Cap Sprint
- Pattern A Remediation, Full Codebase Audit
- P0-01: RBAC Bypass Fix, Sprint 1B/1C: Tenant & EFI Isolation

### Phase 2 — Indian Statutory Compliance
- Sprint 2A-2D: Professional Tax, GST, Indian Payroll, Workflow Chain

### Phase 3 — EFI Architecture
- Sprint 3A: EFI Pipeline Audit & Anonymisation Layer

### Phase 4 — Test Infrastructure & Technical Debt
- Sprint 4A/4B: Tests unskipped, payroll/cross-tenant/RBAC tests

### Phase 5 — Production Gate
- Sprint 5A/5B: Pre-production audit, GATE PASSED (90/100)

### Phase 6 — Bug Fixes, Knowledge Pipeline & Pagination
- **Sprint 6A: COMPLETE** — GST settings fix (Pattern A), org_state fix, embeddings, Rule 42/43
- **Sprint 6B: COMPLETE** — Knowledge Pipeline: auto-generate articles from learning events, seed from failure cards, fix empty cards, wire into EFI response. 22 knowledge articles total.
- **Sprint 6C: COMPLETE** — Cursor-based (keyset) pagination on 5 highest-traffic endpoints:
  - GET /api/v1/tickets (1961 items, sort by created_at)
  - GET /api/v1/invoices-enhanced (14 items, sort by invoice_date)
  - GET /api/v1/hr/employees (2 items, sort by created_at)
  - GET /api/v1/failure-intelligence/failure-cards (sort by confidence_score)
  - GET /api/v1/journal-entries (844 items, sort by entry_date)
  - Shared utility: `utils/pagination.py` with `paginate_keyset()`, `encode_cursor()`, `decode_cursor()`
  - Backward compatible: legacy page/limit still works, `next_cursor` included in all responses

## Prioritized Backlog

### P0 — Critical
- None (production gate passed, knowledge pipeline + pagination complete)

### P1 — High Priority
- Razorpay LIVE keys (user must provide)
- Frontend upgrade to use server-side cursor pagination (currently client-side)
- GSTR-3B ITC data-driven integration test
- Address 13 remaining skipped tests
- GST supply_type UI dropdown on invoice form

### P2 — Medium Priority
- Knowledge article embeddings for semantic search
- Compound indexes for cursor pagination fields
- Consolidate failure_cards vs efi_failure_cards collections
- Background job for embedding regeneration (ingress timeout)
- CSRF secure flag, rate limiting improvements
- WhatsApp notification integration (mocked)
- Migrate hybrid embeddings to true embedding model

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / DevTest@123
- **Technician:** deepak@battwheelsgarages.in / DevTest@123

## 3rd Party Integrations
- Razorpay (test keys), Resend, bleach, bcrypt
- Emergent LLM Key (gpt-4o-mini for hybrid embeddings)
- WhatsApp remains MOCKED

## Test Baseline (Post Sprint 6C)
- Core suite: 428 passed, 0 failed, 13 skipped
- Sprint 6B tests: 13/13, Sprint 6C tests: 17/17
- Production readiness: 90/100
