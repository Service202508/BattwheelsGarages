# Battwheels OS — Product Requirements Document

## Original Problem Statement
Build and maintain Battwheels OS, a multi-tenant SaaS platform for EV service businesses. The platform includes CRM, invoicing, inventory, ticketing, HR, AI diagnostics (EVFI™), and reporting modules.

## Architecture
- **Frontend:** React + Shadcn/UI + TailwindCSS (port 3000)
- **Backend:** FastAPI + MongoDB (port 8001)
- **Database:** MongoDB (battwheels = production, battwheels_dev = testing)
- **Auth:** JWT + TenantGuard middleware
- **3rd Party:** Sentry, Razorpay, Resend, Gemini (EVFI), ZXing

## What's Been Implemented

### Subscription Plan Gating (Complete)
- 4-tier plans: free_trial, starter, professional, enterprise
- Frontend: planConfig.js, UpgradePrompt.jsx, lock icons in Layout.jsx
- Backend: plan_enforcement.py middleware, record limits in routes

### Open Registration (Complete)
- Beta code removed from frontend forms
- invite_code made optional in backend

### Homepage UX (Complete)
- Mobile hamburger menu on SaaSLanding.jsx
- 4-tier pricing section matching planConfig.js

### Mobile UX Bug Fixes — 11 total (Complete)
- EVFI diagnosis panel responsive layout
- Scrollable tab bars, sidebar fixes, empty-state handling
- Barcode scanner camera, vehicle category seeding

### Cross-Tenant Data Leak Fix — Wave 4 (Complete, Mar 11 2026)
- **37 endpoints fixed** across 17 files
- 23 LEAK endpoints: added org_id to all queries
- 14 PARTIAL endpoints: removed `if org_id else {}` pattern
- Verification: 33/33 endpoints clean (zero suspicious data in new org)

## Prioritized Backlog

### P0 — Blocking
- [x] Cross-tenant leak investigation (complete)
- [x] Cross-tenant fixes — 37 endpoints (complete)
- [ ] First Customer Journey Audit (full UI/UX walkthrough)
- [ ] RBAC permission map — operations/dashboard routes returning 403

### P1 — High
- [ ] Fix CI/CD pipeline
- [ ] Migrate remaining mocked emails to Resend
- [ ] Backend test suite fix (conftest.py fixture issue)
- [ ] Orphaned tenant records cleanup (org_56469233873f, org_90677017dafe)

### P2 — Medium/Backlog
- [ ] Trial Balance Report ₹0.00
- [ ] Payslip PDF generation
- [ ] Collection consolidation (invoices + ticket_invoices)
- [ ] God file decomposition (reports_advanced.py)
- [ ] _enhanced file duplication refactor
- [ ] Vehicle categories automated seeding in deployment script

## Known Issues
- Backend test suite fails (dev@battwheels.internal fixture missing)
- RBAC_UNMAPPED_ROUTE for some operations endpoints
- Email verification status unclear in production
- pre-commit hook false positives on multi-line `import {` blocks

## Credentials
- Platform Admin: platform-admin@battwheels.in / v4Nx6^3Xh&uPWwxK9HOs
- Demo Org Owner: demo@voltmotors.in / Demo@12345

## Rollback Point
- Checkpoint: 4f2f7227 (pre-cross-tenant-fix)
