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
- `/app/docs/SPRINT_6D_FINAL_REPORT.md` — Sprint 6D (Pre-Launch Readiness) final report

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

### Phase 6 — Bug Fixes, Knowledge Pipeline, Pagination & Readiness
- **Sprint 6A: COMPLETE** — GST settings fix, org_state fix, embeddings, Rule 42/43
- **Sprint 6B: COMPLETE** — Knowledge Pipeline: auto-generate articles from learning events
- **Sprint 6C: COMPLETE** — Cursor-based pagination on 5 endpoints (backward compatible)
- **Sprint 6D: COMPLETE** (2026-02-28) — Pre-launch readiness:
  - 6D-01: 8 compound MongoDB indexes for paginated collections
  - 6D-02: Database cleanup script (safe, preserves 3 protected orgs)
  - 6D-03: Volt Motors demo account seeded with realistic data
  - 6D-04: Final readiness audit — Score: 93/100
  - 6D-05: Dead code cleanup (stripe_webhook.py, fault_tree_import.py, efi_failure_cards)
  - Test environment restoration script (`scripts/restore_test_env.py`)

## Prioritized Backlog

### P1 — High Priority
- Frontend upgrade to use server-side cursor pagination
- Razorpay LIVE keys (user must provide)
- Address remaining 13 skipped tests

### P2 — Medium Priority
- Background task runner for long-running jobs (embedding regeneration)
- Migrate hybrid embeddings to true embedding model
- Purge stale sessions/tenant_roles data
- WhatsApp notification integration (currently mocked)

## Credentials
- **Demo:** demo@voltmotors.in / Demo@12345
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / DevTest@123
- **P0 Admin:** admin@battwheels.in / TestPass@123
- **P0 Tech:** tech@battwheels.in / TestPass@123

## 3rd Party Integrations
- Razorpay (test keys), Resend, bleach, bcrypt
- Emergent LLM Key (gpt-4o-mini for hybrid embeddings)
- WhatsApp remains MOCKED

## Test Baseline (Post Sprint 6D)
- Core suite: 428 passed, 0 failed, 13 skipped
- Sprint readiness score: 93/100
- Protected orgs: demo-volt-motors-001, dev-internal-testing-001, org_9c74befbaa95

## Scripts
- `scripts/restore_test_env.py` — Restores test infrastructure (repeatable)
- `scripts/clean_dev_database.py` — Removes test data (supports --dry-run)
- `scripts/add_pagination_indexes.py` — Creates compound indexes
- `scripts/seed_demo_data.py` / `scripts/seed_demo_org.py` — Seeds demo org
