# Battwheels OS — Product Requirements Document

## Original Problem Statement
Comprehensive UX and brand consistency overhaul titled "Beta Readiness" and "UX Polish." Work is broken into granular "Micro-Phases." The application is an AI-powered EV service platform (Battwheels OS) for Indian electric vehicle garages.

## Architecture
- **Frontend:** React (CRA) with Tailwind CSS + Shadcn/UI
- **Backend:** FastAPI (Python) with MongoDB
- **Database:** MongoDB (battwheels_dev locally, Atlas in production)
- **Auth:** JWT-based with multi-tenant RBAC
- **Payments:** Razorpay integration
- **Email:** Resend (mocked in dev)
- **AI:** EVFI (Electric Vehicle Failure Intelligence) diagnostic engine

## What's Been Implemented

### Session 1 — Typography & UX Polish
- Typography design token system (`.bw-` classes) in `index.css`
- Page title standardization across 5 key pages
- Financial typography (`bw-text-money` monospace) on 15 currency elements
- Rogue font eradication (Syne, DM Serif Display) from 7 files
- Bug fix: Recurring expenses error toast
- Bug fix: P&L report showing ₹0 (rerouted to journal-based endpoint)
- Logo audit (read-only) identifying 6+ inconsistent instances

### Session 2 — Brand, Security, & Bug Fixes (March 14, 2026)
- BattwheelsLogo component created and reverted (deferred for redesign)
- ScrollToTop component added for route navigation
- Razorpay integration audit (read-only)
- CSRF exemption for Razorpay webhook endpoints
- Webhook route alias at `/payments/razorpay/webhook`
- Registration fix: added `organization_id` to user document in signup handler
- **Registration P0 fix:** `OrganizationCreate` Pydantic model now accepts both `{name, email, password}` and `{admin_name, admin_email, admin_password}` field conventions via `model_validator`, fixing 422/500 errors for users submitting with plain field names
- Full platform verification: 80/80 endpoints passing

## Prioritized Backlog

### P0 — Critical
- [x] CSRF exempt for Razorpay webhooks
- [x] Webhook route alias
- [x] ScrollToTop on route navigation
- [x] Registration organization_id consistency fix
- [ ] BattwheelsLogo shared component (deferred — needs redesign from user)
- [ ] Replace 6 hardcoded logo instances

### P1 — High
- [ ] P&L PDF/Excel export uses wrong endpoint (exports ₹0)
- [ ] Refactor ServiceMetricCard for valueClassName prop
- [ ] Continue `.bw-` typography classes (sidebar, tables, forms)
- [ ] Login rate limiting — composite key (ip + email)
- [ ] Staging environment seeding with realistic data
- [ ] pytest suite recovery

### P2 — Medium
- [ ] Activate production Resend email integration
- [ ] Activate production Razorpay integration
- [ ] Deploy to staging + full QA
- [ ] Deploy to production

## Known Issues
- `pytest` suite is non-functional (full rewrite needed)
- P&L PDF/Excel export generates reports with ₹0 data
- Email service is mocked in dev (Resend)
- Razorpay uses placeholder keys (`rzp_test_disabled`) in dev

## Credentials
- Workshop Owner: `demo@voltmotors.in` / `Demo@12345`
- Technician: `ankit@voltmotors.in` / `Tech@12345`
- Customer Portal: Token `PORTAL-SUNITA-2026`
