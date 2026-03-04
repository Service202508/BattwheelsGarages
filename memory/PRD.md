# Battwheels OS — Product Requirements Document

## Original Problem Statement
EV service platform for the electric vehicle industry. Full-stack FastAPI + React + MongoDB application with multi-tenant architecture, financial management, ticket management, inventory, GST compliance, and AI-powered features.

## Core Architecture
- **Backend:** FastAPI with Motor (async MongoDB)
- **Frontend:** React with Shadcn UI
- **Database:** MongoDB (battwheels_dev for development)
- **Multi-Tenancy:** TenantGuardMiddleware → RBAC → CSRF → Sanitization → RateLimit
- **Auth:** JWT-based with session cookie fallback

## What's Been Implemented

### P1 CLEANUP BATCH (2026-03-04)
- **FIX 1 (DB Connection):** Removed standalone MongoClient from reports_advanced.py and 10 other files. All use shared `utils.database` now.
- **FIX 2 (Plan Sync):** Corrected volt-motors org: both `plan` and `plan_type` set to "professional". Verified via /api/v1/ai-usage/status.
- **FIX 3 (Error Boundary):** Created ErrorBoundary.jsx class component, wrapped App.js content. Frontend build verified.
- **FIX 4 (Journal reference_id):** Added `reference_id` and `reference_type` to JournalEntry.to_dict() in double_entry_service.py, aligning API-created entries with seed data.
- **Verification Gate:** 1430 backend tests pass, all API flows working, frontend builds, production DB untouched.

### P0 Security Fix: org_id Trust Chain (2026-03-04)
- **COMPLETED**: Secured org_id resolution across entire codebase
- All 25 files with direct header/cookie reads patched to use middleware-validated `request.state.tenant_org_id`
- Created comprehensive cross-tenant isolation test suite (7 tests)

### Existing Features (Pre-Audit)
- Ticket management system with 7128 records
- Invoice system (canonical + enhanced) with 1655 records
- GST/statutory compliance module
- HR module
- Inventory management with serial/batch tracking
- AI/EFI intelligence services
- Customer/business/technician portals
- Financial dashboard with receivables/payables
- PDF template system
- Notification system
- SLA management
- Knowledge brain
- Banking module
- Expense management

## Prioritized Backlog

### P0 — Critical (Completed)
- [x] Tenant Isolation Bypass — org_id trust chain secured
- [x] DB Connection in reports_advanced.py — fixed
- [x] Plan/plan_type sync — corrected
- [x] Error Boundary — implemented
- [x] Journal reference_id alignment — fixed

### P0 — Critical (Remaining)
- [ ] Risk of Writing to Production Database — Add env/DB mismatch guard in server.py

### P1 — High Priority
- [ ] Inefficient DoS Protection — Reorder middleware chain (rate limiter first)
- [ ] Non-Functional Deployment Pipeline — CI/CD workflows have placeholder TODOs
- [ ] User Verification of Homepage & Product Tour (SaaSLanding.jsx, ProductTour.jsx)

### P2 — Architectural Debt
- [ ] Refactor `_enhanced` file duplication pattern
- [ ] Break down 16+ god files (>1500 lines)
- [ ] Consolidate `plan` vs `plan_type` codebase-wide (code refactor)
- [ ] Centralize database connection logic

### P3 — Testing & Quality
- [ ] Frontend test coverage (96 pages, 0 tests)
- [ ] Improve seed data quality and staging DB
- [ ] Pre-existing SLA breaches test failure (test_production_readiness_iteration103.py)

## Environment
- **Development DB**: battwheels_dev
- **Staging DB**: battwheels_staging
- **Production DB**: battwheels (READ-ONLY for agent)
- **Credentials**: demo@voltmotors.in / Demo@12345

## Key API Endpoints
- POST /api/auth/login
- GET /api/v1/tickets
- GET /api/v1/invoices-enhanced/summary
- GET /api/v1/dashboard/financial/summary
- GET /api/v1/reports-advanced/revenue/monthly
- GET /api/v1/ai-usage/status
- POST /api/v1/journal-entries
- GET /api/health

## 3rd Party Integrations
- Sentry: Configured for error monitoring
- Razorpay: Integrated but disabled (test keys)
- Gemini: API key NOT SET
- Resend: API key SET
