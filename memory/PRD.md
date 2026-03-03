# Battwheels OS - Product Requirements & Status

## Product Overview
Battwheels OS is an EV service management platform with AI-powered diagnostics, onsite-first service intelligence, and enterprise-grade ERP capabilities built exclusively for electric vehicles.

## Core Architecture
- **Backend:** FastAPI (Python) on port 8001
- **Frontend:** React (craco) on port 3000
- **Database:** MongoDB (`battwheels_dev`)
- **Auth:** JWT-based with RBAC middleware
- **Tenant System:** Multi-tenant with organization_users membership

## What's Been Implemented
- Full ERP modules: Invoices, Bills, Estimates, Contacts, Inventory, HR, Payroll
- EFI (Failure Intelligence) engine with AI diagnostics
- Multi-tenant architecture with RBAC
- Customer/Business/Technician portals
- Subscription and payment integration (Razorpay)
- Reporting and analytics dashboards

## Stability Audit (2026-03-03)

### Completed
- Fixed test infrastructure (conftest.py auto-inject auth, rate-limit protection, password protection)
- Fixed URL prefix mismatch in 140+ test files (/api/ → /api/v1/)
- Fixed 12+ files with wrong credentials
- Fixed 5 files with wrong organization IDs
- Added 15 missing RBAC route permissions
- Verified frontend build integrity (clean compile)
- Verified 10/10 critical API endpoints working
- Generated `docs/STABILITY_AUDIT_REPORT.md`

### Test Suite Status
- **Passed:** 1993 (was ~1668, +325)
- **Failed:** 604 (was 745, -141)
- **Errors:** 7 (was 255, -248)
- **Skipped:** 467
- **Pass Rate:** 65% (was ~54%)

### Remaining Work (P0-P2)

#### P0: Fix remaining test failures
- ~250 tests for rolled-back features (need archival decision)
- ~50 tests hitting 500 server errors (need backend code fixes)
- 7 EFI module errors (tenant validation server bug)

#### P1: Test cleanup
- Update ~150 tests with response format mismatches
- Fix ~80 tests with wrong endpoint paths
- Fix ~75 tests with test logic bugs

#### P2: External integration verification
- Razorpay integration (needs live keys)
- Resend email service (needs API key)
- IRP e-invoice integration (needs credentials)
- Sentry monitoring (needs DSN)

## Key Credentials
- Demo User: `demo@voltmotors.in` / `Demo@12345`
- Dev Admin: `dev@battwheels.internal` / `DevTest@123`
- Platform Admin: `platform-admin@battwheels.in` / `DevTest@123`
- Admin: `admin@battwheels.in` / `DevTest@123`
