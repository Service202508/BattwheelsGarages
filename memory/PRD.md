# Battwheels OS — Product Requirements Document

## Original Problem Statement
Full-stack SaaS application (React + FastAPI + MongoDB) for EV workshop management. Features include multi-tenant architecture, ticket management, estimates/invoices, inventory, accounting (double-entry), payroll, CRM, and a customer portal.

## Architecture
- **Frontend:** React (Vite/CRA) with Shadcn/UI, TailwindCSS
- **Backend:** FastAPI with Motor (async MongoDB)
- **Database:** MongoDB
- **Auth:** JWT + Emergent-managed Google Auth
- **Integrations:** Resend (email), Razorpay, Stripe (test), Gemini (Emergent LLM Key), WhatsApp (MOCKED)

## What's Been Implemented

### Core Modules
- Full multi-tenant SaaS with subdomain-based routing
- Complete estimates module (create, edit with line items, send, accept, convert to invoice)
- Complete invoicing with GST, payment tracking, journal entries
- Ticket/Job Card management with technician portal
- Inventory management with stock tracking
- Double-entry accounting with trial balance, P&L
- Customer portal with estimate accept/decline
- Leads management dashboard for platform admin
- Sales funnel optimization (Book Demo CTA)

### Password Management (Feb 24, 2026)
1. **Admin Reset Password** — KeyRound button in Employee table actions + "Reset Login Password" button in Employee Detail dialog. Admin sets new password, bcrypt-hashed on save.
2. **Self-Service Password Change** — Settings → Security section. Requires current password + new password (6+ chars) + confirmation.
3. **Forgot Password Flow** — "Forgot password?" link on login page opens modal. Sends time-limited (1hr) reset link via Resend email. Token stored hashed (SHA256) in `password_reset_tokens` collection. `/reset-password` page handles token validation and new password entry.

### Estimates Bug Fixes (Feb 24, 2026)
- Bug A: "Error updating estimate" — fixed field name mismatches + added line item support to PUT endpoint
- Bug B: Empty line items in Edit modal — fixed field normalization between estimate types
- Bug C: Estimates list not loading — fixed `data.estimates` → `data.data` key mismatch
- Chain fixes: Collection name bug in estimate-to-invoice conversion, field mapping for tax/HSN/discount

## New Endpoints (Password Management)
- `POST /api/auth/change-password` — authenticated, self-service
- `POST /api/auth/forgot-password` — public, anti-enumeration
- `POST /api/auth/reset-password` — public, token-based
- `POST /api/employees/{id}/reset-password` — admin-only

## New DB Collections
- `password_reset_tokens`: user_id, email, token_hash (SHA256), expires_at (1hr TTL), used (bool)

## Credentials
- Platform Admin: platform-admin@battwheels.in / admin
- Org Admin: admin@battwheels.in / q56*09ps4ltWR96MVPvO (reset Feb 24 2026)
- Technician: tech@battwheels.in / tech123

### Environment Separation (Feb 24, 2026)
- Three-environment structure: production (`battwheels`), staging (`battwheels_staging`), development (`battwheels_dev`)
- Demo org "Volt Motors" seeded in dev DB with 3 months of realistic data (14 tickets, 8 invoices, 8 customers, 10 inventory items, 3 employees, 11 accounts, 2 payroll runs)
- Dev org "Battwheels Dev" seeded in dev DB for internal testing
- Production health check script (`verify_prod_org.py`) — read-only, checks contamination
- Environment badge in Platform Admin header (PRODUCTION/STAGING/DEVELOPMENT)
- CODING_STANDARDS.md updated with Rule 4 (Three-Environment Discipline)
- Makefile with seed/reseed/check-prod targets
- Demo login: demo@voltmotors.in / Demo@12345 (dev DB only)
- Dev login: dev@battwheels.internal / DevTest@123 (dev DB only)

## New Files (Environment Separation)
- `/app/scripts/seed_demo_org.py` — Seeds Volt Motors demo org (dev/staging only)
- `/app/scripts/seed_dev_org.py` — Seeds Battwheels Dev org (dev only)
- `/app/scripts/verify_prod_org.py` — Read-only prod health check
- `/app/config/environments/README.md` — Environment documentation
- `/app/Makefile` — Dev commands (seed-demo, seed-dev, reseed-dev, check-prod)

## Backlog (Prioritized)
- **P0:** Guide through production deployment (5-step checklist)
- **P1:** Refactor `@app.on_event('startup')` → lifespan context manager
- **P2:** Logo swap (pending user direction)
- **P3:** Refactor EstimatesEnhanced.jsx (tech debt)
- **P4:** E2E tests with Playwright
- **P5:** Configure live WhatsApp credentials

## Mocked Services
- WhatsApp integration (`whatsapp_service.py`) — awaiting live credentials

## Known Technical Debt
- Sentry's browserTracingIntegration consumes fetch response bodies — all error handling uses `res.clone().json()` with status-based fallbacks
- `@app.on_event('startup')` is deprecated — should use lifespan context manager
- EstimatesEnhanced.jsx is a recurring refactoring candidate
- 4 auth middleware files could be consolidated
