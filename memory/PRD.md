# Battwheels OS — Product Requirements Document

## Problem Statement
Full-stack SaaS platform (React/FastAPI/MongoDB) for EV workshop management. Multi-tenant architecture with AI-powered EV Failure Intelligence (EFI) diagnostics + full business operations (accounting, GST, HR, inventory, service management).

## Architecture
- **Frontend**: React 19 (CRA + CRACO) + Shadcn/UI + TailwindCSS + Framer Motion
- **Backend**: FastAPI 0.132.0 + MongoDB (Motor) + Multi-tenant (TenantGuard)
- **Auth**: JWT (dual system in server.py + utils/auth.py) + Emergent Google Auth
- **Integrations**: Resend, Razorpay, Stripe (test), Gemini (Emergent LLM), Sentry, WhatsApp (coded, unconfigured), E-Invoice (sandbox)
- **Design**: Dark + Volt (#080C0F background, #C8FF00 accent)

## Current State: v2.5.0 (Feb 26, 2026)

### Architectural Evolution Sprint — COMPLETED
All 6 phases verified (25/25 backend tests + full frontend verification):

**Phase 1 — Two Ticket Types** ✅
- `ticket_type` field: "onsite" (customer-linked) or "workshop" (internal)
- Auto-detection by backend based on creation context
- `resolution_type` removed from all forms
- Filter tabs (All/Onsite/Workshop) on Tickets page
- Type badges on each ticket row

**Phase 2 — RBAC HR Role** ✅
- "hr" role added to ROLE_HIERARCHY
- HR role can access: HR Dashboard, Employees, Attendance, Leave, Payroll, Productivity
- HR role blocked from: Tickets, Finance, Invoices, Inventory, Contacts
- Employee-level data isolation on attendance endpoint
- Frontend sidebar filters sections by role

**Phase 3 — Public Form Enhancement** ✅
- Customer auto-detection endpoint: GET /api/public/customer-lookup?phone=X
- Auto-link or create contact on ticket submission
- resolution_type removed from public form

**Phase 4 — Estimate in Ticket Detail** ✅
- Estimate section embedded in TicketDetail page
- Create, view, navigate to full estimate from ticket context
- Reuses existing estimate endpoints (ticket_estimates)

**Phase 5 — Failure Card Pipeline** ✅
- failure_cards collection with indexes
- Auto-creation on ticket close
- CRUD API: POST/GET/PUT/GET-by-ticket
- Anonymised brain feed to efi_platform_patterns
- Strips org/customer/technician data before feeding

**Phase 6 — Feature Flags + Version + Migrations** ✅
- Feature flag system (off/canary/percentage/on)
- Platform admin CRUD for flags
- Version tracking: v2.5.0 in /api/health and frontend footer
- Migration system: runner.py + 4 migration files
- Runs on startup, tracks in migrations collection

### Environment
- **DB_NAME**: `battwheels_dev` (development)
- **ENVIRONMENT**: `development`
- **MONGO_URL**: `mongodb://localhost:27017` (local Emergent)

## Prioritized Backlog

### P0 — Critical
- [ ] Fix Trial Balance (returns 0/0 — journal entry schema mismatch)
- [ ] Fix 109 chart_of_accounts with None type
- [ ] Unify JWT system (dual system with different expiry)
- [ ] Fix 12 users missing organization_id (in production DB)

### P1 — High Priority
- [ ] Implement Period Locking (design doc exists)
- [ ] Implement CSRF Protection
- [ ] Add input sanitization middleware
- [ ] Complete audit log coverage across all modules
- [ ] Estimate → Ticket conversion flow
- [ ] SLA Automation
- [ ] Form 16 PDF generation
- [ ] Failure card completion modal (UI flow on ticket close)

### P2 — Medium Priority
- [ ] Refactor EstimatesEnhanced.jsx (2,966 lines)
- [ ] Refactor server.py (6,716 lines, 50+ inline models)
- [ ] Remove/archive Zoho dead code (242 endpoints)
- [ ] Remove duplicate razorpay.py
- [ ] Clean dead files (Banking_old.jsx.bak, etc.)
- [ ] Fix reverse charge in GSTR-3B
- [ ] Customer Portal full backend scoping
- [ ] Fleet/Business Portal aggregated view

### P3 — Future
- [ ] GSTR-2A Reconciliation
- [ ] E-way Bills
- [ ] PF/ESI Challan generation
- [ ] Dockerfile / railway.toml / CI/CD
- [ ] Security headers (X-Frame-Options, HSTS)
- [ ] Global 401 handling in frontend
- [ ] Redis-backed rate limiting
- [ ] EFI Layer 2 (Org Context) implementation

## Key Credentials
- **Demo**: demo@voltmotors.in / Demo@12345 (owner, demo-volt-motors-001)
- **Dev**: dev@battwheels.internal / DevTest@123 (owner, dev-internal-testing-001)

## Test Coverage
- test_battwheels_evolution_sprint.py — 25 tests covering all 6 phases
- 105+ legacy test files in backend/tests/
- 126 iteration JSON reports in test_reports/
