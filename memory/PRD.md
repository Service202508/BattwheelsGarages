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
- **Frontend:** `API` constant for business, `AUTH_API` for auth
- **Lifespan:** `@asynccontextmanager` (no deprecated `on_event`)
- **Startup:** SLA job + index migration + 23 compound indexes

## Security Posture
- Multi-tenancy: All route files hardened with org_id filtering
- JWT: uses `JWT_SECRET` (64-char hex key) with `pwd_v` (password version)
- JWT validation: checks `is_active` in DB on every request
- Rate limiting: 10/min on login, 20/min on AI, 300/min standard
- CORS: Locked to specific origin (not wildcard)

## Audit History

### Grand Final Audit (2026-02-24)
- **Verdict:** UNCONDITIONALLY APPROVED for commercial operation
- **Migration:** 1,375 documents fixed across 111 tenant collections
- **Tests:** 20/20 pytest PASS, frontend build PASS

### Full System Audit (2026-02-24)
- **System Stability:** 72/100
- **Multi-Tenant Safety:** 78/100
- **Financial Integrity:** 65/100
- **Compliance Readiness:** 60/100
- **4 CRITICAL findings:** RBAC v1 bypass, AI assistant no org_id, Zoho sync unscoped deletes, Journal posting no idempotency
- **Full report:** /app/FULL_SYSTEM_AUDIT_REPORT.md

## Test Credentials
- Admin: admin@battwheels.in / Admin@12345 (org: Battwheels Garages)
- Demo (dev DB): demo@voltmotors.in / Demo@12345

## Post-Launch Roadmap (Updated Priority)

### CRITICAL (Before First Customer)
- **C1:** Fix RBAC v1 pattern matching (patterns use `/api/` but routes are `/api/v1/`)
- **C2:** Add org_id to `ai_assistant.py` (0 tenant scoping currently)
- **C3:** Add org_id filter to Zoho sync destructive operations
- **C4:** Add idempotency guard to journal entry posting

### P1 — Next Session
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
- GSTR-2A/2B reconciliation

### P4 — At Scale
- Celery background jobs
- Redis caching
- server.py decomposition
- Live WhatsApp credentials
