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

## What's Been Implemented

### Phase 1 — Tenant Isolation & RBAC (2026-02-27 to 2026-02-28)
- Production Reset & Verification
- H-01/H-02 Hard Cap Sprint (unbounded queries capped)
- Pattern A Remediation (items_enhanced.py 66 violations fixed)
- Full Codebase Audit → REMEDIATION_AUDIT_2026.md
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

#### Sprint 3A — Completed Items
- **3A-01:** Failure card → knowledge pipeline audited. Pipeline is INCOMPLETE (Case C).
  - `feed_efi_brain()` in `routes/failure_cards.py:232-264` correctly anonymises data
  - But pipeline never reaches `knowledge_articles` collection (0 documents)
  - `continuous_learning_service` writes to `efi_learning_queue`/`efi_failure_cards`, never to `knowledge_articles`
  - TODO comment added to `continuous_learning_service.py:126-135`
- **3A-02:** Parameterized collection search constrained. `ALLOWED_SEARCH_COLLECTIONS` guard added to `embedding_service.py:find_similar()`. Only `failure_cards`, `knowledge_articles`, `knowledge_embeddings` allowed.
- **3A-03:** Ticket-EFI data contract verified. 7 mismatches documented (5 missing fields, 1 name mismatch, 1 partial). EFI invocation uses embedding-only matching.
- **3A-04:** EFI response quality: GENERIC. 0 failure cards with embeddings, 0 decision trees, 0 knowledge articles. Data seeding gap.
- **3A-05:** `_update_efi_platform_patterns` org_id fix verified — PASS. org_id in find_one, update_one, and $setOnInsert.

## Prioritized Backlog

### P0 — Critical
- Knowledge pipeline incomplete: ticket closure → knowledge_articles never auto-triggered
- `feed_efi_brain` not auto-triggered after ticket closure
- Two disconnected failure card collections (`failure_cards` vs `efi_failure_cards`)

### P1 — High Priority
- Data contract gaps: 5 missing ticket fields, dtc_codes name mismatch
- EFI brain has no data (0 embeddings, 0 trees, 0 articles)
- GSTR-3B ITC Tables 4B/4D hardcoded to zero
- Batch payroll function still uses old key names
- Payroll unit tests missing
- Cursor-based pagination for all hard-capped queries
- 51 skipped tests

### P2 — Medium Priority
- `efi_platform_patterns` duplicate schemas (pattern_id vs pattern_key)
- Dev user has no org membership for demo org (testing gap)
- CSRF secure flag, rate limiting in-memory
- Multiple mocked email/notification features

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / v4Nx6^3Xh&uPWwxK9HOs

## 3rd Party Integrations
- Razorpay, Resend, bleach, bcrypt
- WhatsApp integration remains MOCKED

## Test Baseline
- Core tests: 322 passed, 0 failed, 51 skipped
- Production: 6/6 PASS, ALL GREEN
