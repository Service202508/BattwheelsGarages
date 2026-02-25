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

### Week 1-2 (Complete)
- Unified JWT auth, audit logging, multi-tenant architecture
- Password reset flows, TicketDetail/HRDashboard pages
- Environment badge, PWA service worker, docs (SOP, CODING_STANDARDS)

### Week 3 Emergency + Prompt 1 (Complete)
- Fixed backend .env to point to battwheels_dev
- Created INCIDENTS.md, migration scripts, provisioned battwheels_staging

### Week 3 Prompt 2: Period Locking (Complete)
- Full period locking system with backend service, API, middleware, and frontend UI
- 17/17 tests passed

### Week 3 Prompt 3: Audit Log + Estimate→Ticket (Complete)
- Fixed audit_log.py (correct collection + schema), 14 new audit points
- Estimate→Ticket conversion flow
- 13/13 tests passed

### Week 3 Prompt 4: Security Hardening (Complete — 2026-02-25)
- **CSRF Protection:** Double Submit Cookie pattern (`/app/backend/middleware/csrf.py`)
  - Cookie: `csrf_token`, Header: `X-CSRF-Token`, validates match on mutations
  - Bearer-token auth bypasses CSRF (per OWASP)
  - Exempt paths: /api/auth/, /api/public/, /api/webhooks/, etc.
- **Input Sanitization:** `bleach` middleware (`/app/backend/middleware/sanitize.py`)
  - Strips ALL HTML tags from JSON inputs on POST/PUT/PATCH
  - Fixed Starlette body caching issue (`request._body` override)
- **Frontend:** Extended `apiFetch` wrapper with CSRF token injection
- **Middleware order:** CSRF → TenantGuard → RBAC → Sanitization → RateLimit
- 16/16 tests passed

### Week 3 Prompt 5: EstimatesEnhanced Refactor + GSTR-3B Fix (Complete — 2026-02-25)
- **Refactored 2966-line monolith into 8 files (2226 total lines):**
  - `EstimatesEnhanced.jsx` → 6-line re-export wrapper
  - `estimates/index.jsx` → 122-line orchestrator with Tabs wrapper
  - `estimates/useEstimates.js` → 809-line custom hook (ALL state + handlers)
  - `estimates/EstimatesTable.jsx` → 217 lines (summary, table, ticket estimates)
  - `estimates/EstimateDetail.jsx` → 73 lines (detail dialog)
  - `estimates/EstimateActions.jsx` → 138 lines (action buttons, ticket banner, converted_to)
  - `estimates/EstimateModal.jsx` → 267 lines (create new form)
  - `estimates/EstimateDialogs.jsx` → 600 lines (all secondary dialogs)
- **Convert to Ticket flow preserved in EstimateActions.jsx:**
  - Linked Service Ticket banner (lines 31-43)
  - Open Job Card button (line 38)
  - Converted To display (line 112-117)
- **GSTR-3B Reverse Charge Fix:**
  - Added Section 3.1(d) for inward supplies liable to reverse charge
  - RCM bills/expenses tracked with `reverse_charge` flag
  - `rcm_tax_liability` added to summary
  - Net tax calculation includes RCM as outward liability
- 16/17 backend tests passed (94%), compilation clean (no errors)

## Key Environment Rules
1. Development uses DB_NAME=battwheels_dev
2. Production data (battwheels) is NEVER touched by development
3. Customer orgs are sacrosanct (Rule 8)
4. All audit logging writes to audit_logs collection
5. Period locks enforced on all financial write endpoints
6. CSRF Double Submit Cookie enforced on all mutation endpoints
7. Input sanitization (bleach) strips HTML from all JSON inputs

### Week 4: Production Readiness (Complete — 2026-02-25)
- **Prompt 0 (Quick Fixes):** Failing test fixed (17/17), dev/staging audit collections cleaned, seed scripts fixed (password hashing), platform-admin password reset, Sentry startup verified
- **Prompt 1 (Containerization):** Multi-stage Dockerfile, docker-compose.yml, docker-compose.prod.yml, .dockerignore
- **Prompt 2 (Railway Config):** railway.toml, railway.staging.toml, .env.example, docs/DEPLOYMENT.md
- **Prompt 3 (Hardening):** Environment-aware Sentry, CORS restricted in production, enhanced /api/health endpoint
- **Prompt 4 (Production Migrations):**
  - INC-004: Dropped empty `audit_log` collection from production (0 docs)
  - INC-005: Migrated INV-00001 from `invoices` → `invoices_enhanced` with all fixes (line_items fetched from invoice_line_items, payment_status derived, created_at preserved, GST fields preserved)
  - INC-005a: Original `invoices` collection preserved pending explicit drop approval
  - verify_prod_org.py: CLEAN (0 contamination, 0 demo orgs)
- **Production readiness score: 10/10**

## Prioritized Backlog

### P0 (Operational — Week 5)
- Deploy to Railway staging environment (follow docs/DEPLOYMENT.md)
- Create MongoDB Atlas cluster for staging/production
- Set up custom domains (dev.battwheels.com, staging.battwheels.com, app.battwheels.com)
- First production deployment on Railway

### P1 (Pending Decision)
- Drop original `invoices` collection from production (INC-005a — awaiting D's approval)

### P2 (Resolved Technical Debt)
- ~~Consolidate audit_log vs audit_logs dual-collection issue~~ (INC-004, done)
- ~~Consolidate invoices vs invoices_enhanced dual-collection issue~~ (INC-005, done)
- ~~Fix empty password hash bug in seed scripts~~ (done)
- ~~Recover/reset platform-admin@battwheels.in password~~ (done)

## Credentials
- admin@battwheels.in / q56*09ps4ltWR96MVPvO (prod)
- internal@battwheels.in / lbC9qFOmjbJapYtUp^h1 (prod internal)
- demo@voltmotors.in / Demo@12345 (dev)
- dev@battwheels.internal / DevTest@123 (dev)
