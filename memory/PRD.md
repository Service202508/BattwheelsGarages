# Battwheels OS — Product Requirements Document

## Product Overview
Full-stack SaaS platform for automotive service businesses. Multi-tenant architecture with React frontend, FastAPI backend, and MongoDB.

## Core Users
- **Platform Admin** (platform-admin@battwheels.in) — System-wide operations
- **Org Admin/Owner** — Business operations, financial management
- **Accountant** — Financial entries, period management
- **Technician** — Ticket work, service delivery

## Architecture
```
Frontend: React + Shadcn/UI + TailwindCSS (port 3000)
Backend: FastAPI + Motor (async MongoDB) (port 8001)
Database: MongoDB (battwheels=prod, battwheels_dev=dev, battwheels_staging=staging)
```

## What's Been Implemented

### Week 1 (Complete)
- Unified JWT auth system
- Initial audit logging framework
- Base multi-tenant architecture

### Week 2 (Complete)
- 3 password reset flows with tests
- TicketDetail.jsx and HRDashboard.jsx pages
- Environment badge + PWA service worker
- ENVIRONMENT_SOP.md and CODING_STANDARDS.md

### Pre-Week 3 Production Safety (Complete — 2026-02-25)
- Production contamination assessment and cleanup
- Added Rule 8 (Customers Are Sacrosanct) to ENVIRONMENT_SOP.md
- Created "Battwheels OS Internal" org for production testing

### Week 3 Prompt 1: Infrastructure Scaffolding (Complete — 2026-02-25)
- Created /app/docs/INCIDENTS.md, /app/scripts/migrations/ directory
- Provisioned battwheels_staging database

### Week 3 Prompt 2: Period Locking (Complete — 2026-02-25)
- Backend service, API routes, middleware on 8 route files, frontend UI
- 409 PERIOD_LOCKED global handler in apiFetch
- 17/17 tests passed

### Week 3 Prompt 3: Audit Log Coverage + Estimate→Ticket (Complete — 2026-02-25)
- Fixed audit_log.py to write to audit_logs collection
- 14 new audit points across the application
- Estimate→Ticket conversion flow
- 13/13 tests passed

### Week 3 Prompt 4: Security Hardening (Complete — 2026-02-25)
- **CSRF Protection (Double Submit Cookie pattern):**
  - Backend middleware: `/app/backend/middleware/csrf.py`
  - Sets `csrf_token` cookie (HttpOnly=false, Secure, SameSite=none)
  - Validates `X-CSRF-Token` header matches cookie for mutation methods
  - Bearer-token auth requests bypass CSRF (per OWASP — Authorization header can't be forged cross-origin)
  - Defense-in-depth: validates CSRF if header IS provided even with bearer token
  - Exempt paths: /api/auth/, /api/public/, /api/webhooks/, /api/health, /api/contact, /api/book-demo
- **Input Sanitization (bleach):**
  - Backend middleware: `/app/backend/middleware/sanitize.py`
  - Strips ALL HTML tags from JSON string inputs on POST/PUT/PATCH
  - Uses `bleach.clean(strip=True)` — recursive for nested objects/arrays
  - Prevents stored XSS attacks
- **Frontend apiFetch integration:**
  - Extended existing unified API client (`/app/frontend/src/utils/api.js`)
  - `getCookie()` helper reads csrf_token from document.cookie
  - Auto-injects `X-CSRF-Token` header on POST/PUT/PATCH/DELETE
  - Auto-refreshes CSRF cookie on CSRF_MISSING/CSRF_INVALID errors
- **Middleware order:** Request → CSRF → TenantGuard → RBAC → Sanitization → RateLimit → Route
- **CORS updated:** Added `X-CSRF-Token` to allowed headers
- **Testing:** 16/16 tests passed (100% backend + frontend)

## Prioritized Backlog

### P0 (Next)
- **Prompt 5:** Refactor monolithic EstimatesEnhanced.jsx (2966 lines → smaller components) + GST calculation bug fix
  - USER REQUESTED: Come back before starting Prompt 5 for additional instructions about preserving Estimate→Ticket conversion button

### P2 (Technical Debt)
- Consolidate audit_log vs audit_logs dual-collection issue
- Consolidate invoices vs invoices_enhanced dual-collection issue
- Fix empty password hash bug in seed scripts
- Recover/reset platform-admin@battwheels.in password

## Credentials Registry
- admin@battwheels.in / q56*09ps4ltWR96MVPvO (prod)
- internal@battwheels.in / lbC9qFOmjbJapYtUp^h1 (prod internal)
- demo@voltmotors.in / Demo@12345 (dev)
- dev@battwheels.internal / DevTest@123 (dev)

## Key Environment Rules
1. Development uses DB_NAME=battwheels_dev
2. Production data (battwheels) is NEVER touched by development
3. Customer orgs are sacrosanct (Rule 8)
4. All audit logging writes to audit_logs collection
5. Period locks enforced on all financial write endpoints
6. CSRF Double Submit Cookie enforced on all mutation endpoints
7. Input sanitization (bleach) strips HTML from all JSON inputs
