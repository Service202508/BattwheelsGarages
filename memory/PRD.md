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

### P0 Security Fix: org_id Trust Chain (2026-03-04)
- **COMPLETED**: Secured org_id resolution across entire codebase
- All 25 files with direct header/cookie reads patched to use middleware-validated `request.state.tenant_org_id`
- Eliminated `extract_org_id` header trust in `utils/database.py`
- Fixed 3 local `get_org_id` functions (finance_dashboard, banking, expenses)
- Fixed 16+ additional route files with inline header reads
- Added defense-in-depth `tenant_org_id` priority in core/org utilities
- Created comprehensive cross-tenant isolation test suite (7 tests)
- **Verification**: 54 tests pass, production untouched, normal flow preserved

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

### P0 — Critical (Remaining)
- [ ] Risk of Writing to Production Database — Add env/DB mismatch guard in server.py
- [ ] Broken Financial Audit Trail — Fix invoice→journal_entry reference_id linkage

### P1 — High Priority
- [ ] Inefficient DoS Protection — Reorder middleware chain (rate limiter first)
- [ ] No Frontend Error Boundaries — Add ErrorBoundary wrapping entire React app
- [ ] Non-Functional Deployment Pipeline — CI/CD workflows have placeholder TODOs

### P2 — Architectural Debt
- [ ] Refactor `_enhanced` file duplication pattern
- [ ] Break down 16+ god files (>1500 lines)
- [ ] Fix `plan` vs `plan_type` inconsistency in organizations collection
- [ ] Centralize database connection logic

### P3 — Testing & Quality
- [ ] Frontend test coverage (96 pages, 0 tests)
- [ ] Improve seed data quality and staging DB

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
- GET /api/health

## 3rd Party Integrations
- Sentry: Configured for error monitoring
- Razorpay: Integrated but disabled (test keys)
- Gemini: API key NOT SET
- Resend: API key SET
