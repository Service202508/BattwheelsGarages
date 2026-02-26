# Battwheels OS — Product Requirements Document

## Problem Statement
Full-stack SaaS platform (React/FastAPI/MongoDB) for EV workshop management. Multi-tenant architecture serving Battwheels Garages and future customers.

## Architecture
- **Frontend**: React 19 (CRA + CRACO) + Shadcn/UI + TailwindCSS + Framer Motion
- **Backend**: FastAPI 0.132.0 + MongoDB (Motor) + Multi-tenant (TenantGuard)
- **Auth**: JWT (dual system — server.py 7d + utils/auth.py 1d) + Emergent Google Auth
- **Integrations**: Resend (email), Razorpay (LIVE keys!), Stripe (test), Gemini (Emergent LLM), Sentry, WhatsApp (coded but unconfigured), E-Invoice (sandbox)

## Current State (Post Self-Audit, Feb 2026)
- **DB_NAME**: `battwheels` (PRODUCTION) — **MUST be changed to `battwheels_dev`**
- **ENVIRONMENT**: `production` — **MUST be changed to `development`**
- **Production Readiness Score**: 4/10
- **Total Endpoints**: ~700+ across 64+ route files
- **Total Lines of Code**: ~304,667
- **File Count**: 327 .py, 189 .jsx, 23 .js, 45 .md

## What's Working End-to-End
- Login/Registration, Ticket CRUD, Public Ticket Submission
- Invoice Creation with GST + PDF, Estimate Create/Convert
- Contact Management, EFI Diagnostic, Items Management
- Expense Management, GST Reports (GSTR-1, GSTR-3B)
- HR Attendance, Leave Management, Password Reset (all 3 flows)
- RBAC + Tenant Isolation enforcement

## Critical Issues (P0)
1. DB_NAME points to production database
2. Razorpay uses LIVE keys in development
3. 12/13 users missing organization_id
4. Trial Balance returns 0/0 (broken)
5. Two JWT systems with different expiry

## Implementation History

### Week 1 (Complete)
- JWT unification, dead code removal, route scoping
- GSTR credit note inclusion, audit logging, period-locking design doc

### Week 2 (Complete — Feb 25, 2026)
- Fixed user_role in audit entries
- Verified estimates chain end-to-end
- Password reset (3 flows) with validation + audit logging
- TicketDetail page, HR Dashboard, Environment Badge, PWA Service Worker

### Self-Audit (Feb 26, 2026)
- Complete 16-section codebase audit delivered
- Identified all critical issues, dead code, missing features

## Prioritized Backlog

### P0 — Emergency
- [ ] Fix DB_NAME to `battwheels_dev`, ENVIRONMENT to `development`
- [ ] Assess production DB contamination
- [ ] Fix Razorpay to test keys for development
- [ ] Fix 12 users missing organization_id
- [ ] Fix Trial Balance (journal entry schema mismatch)

### P1 — High Priority
- [ ] Implement Period Locking (design doc exists)
- [ ] Fix 109 chart_of_accounts with None type
- [ ] Implement CSRF Protection
- [ ] Unify JWT system (remove duplicate)
- [ ] Add input sanitization middleware
- [ ] Complete audit log coverage across all modules
- [ ] Estimate → Ticket conversion flow
- [ ] Create INCIDENTS.md, scripts/migrations/

### P2 — Medium Priority
- [ ] Refactor EstimatesEnhanced.jsx (2,966 lines)
- [ ] Refactor server.py (6,716 lines, 50+ inline models)
- [ ] Remove/archive Zoho dead code (242 endpoints, 6,654 lines)
- [ ] Remove duplicate razorpay.py (keep razorpay_routes.py)
- [ ] Clean dead files (Banking_old.jsx.bak, Bills_old.jsx.bak, empty root files)
- [ ] Fix reverse charge in GSTR-3B
- [ ] Provision battwheels_staging database

### P3 — Future
- [ ] GSTR-2A Reconciliation
- [ ] E-way Bills
- [ ] PF/ESI Challan generation
- [ ] Deployment config (Dockerfile, CI/CD)
- [ ] Security headers (X-Frame-Options, HSTS, etc.)
- [ ] Global 401 handling in frontend
- [ ] Live WhatsApp credential configuration
- [ ] Redis-backed rate limiting

## Key Credentials
- **Admin**: admin@battwheels.in / Admin@12345
- **Platform Admin**: platform-admin@battwheels.in / PASSWORD LOST
- **Org ID**: 6996dcf072ffd2a2395fee7b

## Test Coverage
- 105+ test files in backend/tests/
- 125+ iteration JSON reports in test_reports/
- Key test suites: password_reset (9), week2_features (15), audit_logging (15), gstr3b (15)
