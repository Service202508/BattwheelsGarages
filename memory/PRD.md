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
- **Step 1:** Production contamination assessment (read-only)
- **Step 2:** Surgical cleanup of 6 test users, 4 test invoices, 2 test business_customers, 1 test audit entry, 1 test contact. Fixed org=None for 4 real staff users
- **Step 3:** Added Rule 8 (Customers Are Sacrosanct) to ENVIRONMENT_SOP.md + Rule 6 to CODING_STANDARDS.md
- **Step 4:** Created "Battwheels OS Internal" org (slug: battwheels-internal) for production testing
- **Emergency:** Fixed DB_NAME from battwheels→battwheels_dev, ENVIRONMENT from production→development

### Week 3 Prompt 1: Infrastructure Scaffolding (Complete — 2026-02-25)
- Created /app/docs/INCIDENTS.md with 3 initial incidents documented
- Created /app/scripts/migrations/ directory with README.md and migration_template.py
- Provisioned battwheels_staging database (34 collections, 28 indexes, empty)

### Week 3 Prompt 2: Period Locking (Complete — 2026-02-25)
- **Backend service:** services/period_lock_service.py — lock, unlock, extend, auto-relock, fiscal year bulk lock
- **Backend routes:** routes/period_locks.py — 8 API endpoints
- **Middleware integration:** check_period_lock() added to 8 route files (invoices_enhanced, credit_notes, journal_entries, payments_received, bills_enhanced, bills, expenses, banking_module, hr)
- **Frontend:** PeriodLocks.jsx — 12-month grid UI with lock/unlock/extend/fiscal year dialogs
- **Indexes:** 2 new indexes on period_locks collection
- **Global error handling:** 409 PERIOD_LOCKED intercepted in apiFetch
- **Testing:** 17/17 pass

### Week 3 Prompt 3: Audit Log Coverage + Estimate→Ticket (Complete — 2026-02-25)
- **Audit log fix:** utils/audit_log.py now writes to audit_logs (not audit_log)
- **14 new audit points:** ticket.created, ticket.assigned, estimate.created, estimate.status_changed, estimate.converted_to_ticket, bill.created, expense.created, bank_transaction.created, bank_transaction.reconciled, contact.created, contact.updated, payroll.run, journal_entry.reversed, estimate.converted_to_invoice
- **Estimate→Ticket flow:** POST /estimates-enhanced/{id}/convert-to-ticket — converts accepted estimates to service tickets with full data mapping
- **Testing:** 13/13 pass

## Prioritized Backlog

### P0 (Next)
- **Prompt 4:** CSRF protection + input sanitization (bleach)

### P1
- **Prompt 5:** EstimatesEnhanced.jsx refactor (2966 lines → smaller components) + GST calculation bug fix

### P2 (Flagged)
- Consolidate audit_log vs audit_logs dual-collection issue
- Fix empty password hash bug in seed scripts
- Consolidate invoices vs invoices_enhanced dual-collection issue
- Address org=None for some contacts_enhanced query patterns

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
