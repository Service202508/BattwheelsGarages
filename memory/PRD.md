# Battwheels OS — Product Requirements Document

## Overview
Full-stack SaaS platform for EV service workshops. React + FastAPI + MongoDB.
Multi-tenant architecture with organization-level data isolation.

## Core Modules (16)
1. Tickets/Job Cards  2. Invoices  3. Contacts/CRM  4. Inventory  5. Estimates
6. HR/Payroll  7. Accounting/Journal  8. EFI (Failure Intelligence)  9. Reports
10. WhatsApp (mocked)  11. SLA  12. Surveys  13. Tally Export  14. GST
15. Razorpay Payments  16. Organization/Admin

## Architecture
- **Auth routes:** `/api/auth/...` (non-versioned)
- **Business routes:** `/api/v1/...` (versioned)
- **Frontend:** `API` constant for business, `AUTH_API` for auth
- **Lifespan:** `@asynccontextmanager` (no deprecated `on_event`)
- **Startup:** SLA job + index migration + compound indexes (auto on every deployment)

## Security Posture
- Multi-tenancy: 22 route files hardened with org_id filtering
- JWT: includes `pwd_v` (password version) — invalidates sessions on password change
- JWT validation: checks `is_active` in DB on every request
- Password reset tokens: SHA-256 hashed, single-use, 1h TTL
- Rate limiting: 5/min on login, 20/min on AI, 300/min standard
- File uploads: PIL-based MIME validation + size limits

## Data Integrity
- Atomic inventory deduction via `find_one_and_update` (prevents negative stock)
- Payroll duplicate prevention: unique compound index on (org_id, period)
- Razorpay webhook atomicity: payment-first, notification-after pattern
- 17+ compound indexes on critical query patterns

## Operational
- Structured audit logging: `utils/audit.py` wired to 6+ critical endpoints
- Health check: MongoDB ping + env var verification
- Indian FY (April-March) defaults in financial reports

## Mocked Services
- WhatsApp integration (`whatsapp_service.py`) — awaiting live credentials

## Test Credentials
- Admin: admin@battwheels.in / Admin@12345 (org: Battwheels Garages)
- Demo (dev DB): demo@voltmotors.in / Demo@12345

## Backlog
- **P0:** Credit Notes (GST compliance) — deferred to dedicated session
- **P1:** Production deployment guide
- **P2:** Refactor EstimatesEnhanced.jsx
- **P3:** E2E Playwright tests
- **P4:** Live WhatsApp credentials
- **P5:** Logo swap
- **P6:** Consolidate auth middleware files
