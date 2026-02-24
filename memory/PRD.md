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
- **Startup:** SLA job + index migration + 23 compound indexes (auto on every deployment)

## Security Posture
- Multi-tenancy: All route files hardened with org_id filtering
- JWT: uses `JWT_SECRET` (64-char hex key) with `pwd_v` (password version)
- JWT validation: checks `is_active` in DB on every request
- Password reset tokens: SHA-256 hashed, single-use, 1h TTL
- Rate limiting: 10/min on login, 20/min on AI, 300/min standard
- File uploads: python-magic MIME validation + size limits
- CORS: Locked to specific origin (not wildcard)

## Data Integrity
- Atomic inventory deduction via `find_one_and_update` (prevents negative stock)
- Payroll duplicate prevention: unique compound index on (org_id, period)
- Razorpay webhook atomicity: payment-first, notification-after pattern
- 23 compound indexes on critical query patterns (incl. estimates, items, bills, expenses)

## Operational
- Structured audit logging: `utils/audit.py` wired to 6+ critical endpoints
- Health check: MongoDB ping + env var verification
- Indian FY (April-March) defaults in financial reports

## Grand Final Audit (2026-02-24)
- **Verdict:** CONDITIONAL — Approved for single-tenant commercial operation
- **Bugs Fixed:** Public ticket routing (404→working), JWT secret inconsistency (unified)
- **Added:** 6 compound indexes on estimates, items, bills, expenses
- **Open:** 374 legacy docs without org_id need migration before multi-tenant

## Test Credentials
- Admin: admin@battwheels.in / Admin@12345 (org: Battwheels Garages)
- Demo (dev DB): demo@voltmotors.in / Demo@12345

## Backlog (Priority Order)
- **P0:** org_id migration for 374 legacy production documents
- **P1:** Credit Notes (GST compliance)
- **P2:** Refactor EstimatesEnhanced.jsx (2,966 lines)
- **P3:** Consolidate auth middleware (5 files → 1)
- **P4:** E2E Playwright tests
- **P5:** Live WhatsApp credentials
- **P6:** Logo swap
- **P7:** Remove orphaned routes/auth.py
- **P8:** Celery for background jobs
