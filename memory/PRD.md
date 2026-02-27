# Battwheels OS — Product Requirements Document

## Original Problem Statement
Battwheels OS is a SaaS platform for EV garages and service centers. The platform provides multi-tenant organization management, ticketing, invoicing, inventory, HR, GST compliance, and AI-powered diagnostics.

## Architecture
- **Frontend:** React (port 3000)
- **Backend:** FastAPI (port 8001)
- **Database:** MongoDB (3 environments: battwheels, battwheels_staging, battwheels_dev)
- **Auth:** JWT + bcrypt password hashing

## Three-Environment Discipline
| Environment | Database | Purpose |
|---|---|---|
| Development | battwheels_dev | All new code, experiments, testing |
| Staging | battwheels_staging | Pre-release QA gate |
| Production | battwheels | Live data, real customers |

## SaaS Architecture (Post-Reset)
- **Production:** 1 user (platform-admin@battwheels.in), 0 orgs, 0 customers
- **Staging:** Mirrors production (1 platform-admin, 0 orgs)
- **Dev:** Volt Motors demo org with sample data (DO NOT TOUCH)
- Customers sign up through the self-serve signup flow

## What's Been Implemented

### Sprint: Beta Launch Gate (COMPLETED - 2026-02-27)
- Test suite pass rate: 86.4% (322 passed, 0 failed, 51 skipped)
- Readiness score: 86/100
- Fixed all critical bugs in signup flow, GST compliance, RBAC

### Credential Security Audit (COMPLETED - 2026-02-27)
- All 13 production passwords reset with strong bcrypt hashes
- Temporary test accounts cleaned from dev DB

### Production Reset — Clean Slate for SaaS Launch (COMPLETED - 2026-02-27)
- Phase 0: Session start protocol — all 5 checks passed
- Phase 1: Full production audit — 223 collections, 2,222 documents catalogued
- Phase 2: Production wiped — all data deleted, platform-admin preserved
- Phase 3: Platform admin login verified (BUG FIXED: bleach sanitization corrupting passwords with & character)
- Phase 4: End-to-end signup flow tested and verified (signup, login, module access, PA visibility)
- Phase 5: Dev environment verified untouched
- Phase 6: Staging set up to mirror production
- Phase 7: Final state report generated

### Bugs Fixed During Reset
1. **Sanitization middleware corrupting passwords:** `bleach.clean()` was converting `&` to `&amp;` in password fields. Fixed by adding auth/signup endpoints to `SANITIZE_BYPASS_PREFIXES` in `middleware/sanitization.py`.
2. **Password field leak in login response:** Login response was exposing a stale `password` field (bcrypt hash). Fixed by adding `"password"` to the exclusion filter in `routes/auth.py`.

## Prioritized Backlog

### P0 — Critical
- None currently blocking

### P1 — High Priority (Tech Debt)
- H-01/H-02: Implement pagination for 435+ unbounded database queries
- H-07: Seed battwheels_staging database for proper QA environment

### P2 — Medium Priority
- Address 51 skipped tests (missing data fixtures for Form16, starter plans, technician portal)
- Address remaining Medium/Low priority audit items

### P3 — Future
- WhatsApp integration (currently mocked)
- End-to-end verification for Form16, live Razorpay
- Full staging promotion workflow

## Key Credentials
- **Dev:** demo@voltmotors.in, dev@battwheels.internal (DevTest@123)
- **Production:** platform-admin@battwheels.in (v4Nx6^3Xh&uPWwxK9HOs)
- **Staging:** platform-admin@battwheels.in (same password as production)

## 3rd Party Integrations
- Razorpay (payment processing)
- Resend (email)
- bcrypt (password hashing)
- bleach (input sanitization)
- Sentry (error monitoring)
