# Battwheels OS — Product Requirements Document

## Overview
Full-stack SaaS platform for EV service workshops. React + FastAPI + MongoDB.
Multi-tenant architecture with organization-level data isolation.

## Core Modules (16)
1. Tickets/Job Cards  2. Invoices  3. Contacts/CRM  4. Inventory  5. Estimates
6. HR/Payroll  7. Accounting/Journal  8. EFI (Failure Intelligence)  9. Reports
10. WhatsApp (awaiting credentials)  11. SLA  12. Surveys  13. Tally Export  14. GST
15. Razorpay Payments  16. Organization/Admin

## Architecture
- **Auth routes:** `/api/auth/...` (non-versioned)
- **Business routes:** `/api/v1/...` (versioned)
- **Public routes:** `/api/public/...` (non-versioned, no auth required)
- **Frontend:** `API` constant = `BACKEND_URL/api/v1`, `AUTH_API` = `BACKEND_URL/api`
- **Lifespan:** `@asynccontextmanager` (no deprecated `on_event`)
- **Startup:** SLA job + index migration + 23 compound indexes

## Audit & Remediation History

### Grand Final Audit (2026-02-24)
- org_id migration: 1,375 documents fixed
- Verdict: APPROVED for single-tenant commercial operation

### Full System Audit (2026-02-24)
- Scores: Stability 72/100, Multi-Tenant 78/100, Financial 65/100, Compliance 60/100
- 4 CRITICAL, 7 HIGH, 6 STRUCTURAL findings

### Remediation Blueprint (2026-02-24)
- 4 CRITICAL fixes planned: RBAC v1 bypass, Zoho sync destructive ops, Journal idempotency, AI org scoping
- Total: ~43 lines across 5 files, ~70 min implementation
- Full report: `/app/CRITICAL_REMEDIATION_BLUEPRINT.md`

## Immediate Roadmap (Priority Order)

### CRITICAL — Fix Now (~70 min total)
1. **RBAC v1 Bypass** — Add path normalization in `middleware/rbac.py` `get_allowed_roles()` (~3 lines)
2. **Zoho Sync Destructive Ops** — Add org_id filter to `delete_many({})` in `zoho_sync.py` (~15 lines)
3. **Journal Idempotency** — Add `source_document_id` check + unique index in `double_entry_service.py` (~20 lines)
4. **AI Assistant Org Scoping** — Add org_id extraction in `ai_assistant.py` (~5 lines)

### P1 — Next Development Session
- **Credit Notes** (GST compliance)
- **Period Locking** (prevent posting to closed periods)
- **Audit log wiring** (13 remaining action types)

### P2 — Month 1
- Refactor EstimatesEnhanced.jsx (2,966 lines)
- Consolidate 5 auth middleware files → 1
- Attendance-Payroll integration (LOP deduction)
- State-variable Professional Tax

### P3 — Month 2-3
- Deferred revenue recognition
- ITC eligibility validation
- Feature gate enforcement on routes
- server.py decomposition

### P4 — At Scale
- Celery background jobs
- Redis caching
- Live WhatsApp credentials

## Test Credentials
- Admin: admin@battwheels.in / Admin@12345 (org: Battwheels Garages)
- Demo (dev DB): demo@voltmotors.in / Demo@12345
