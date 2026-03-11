# Battwheels OS — Product Requirements Document

## Original Problem Statement
Battwheels OS is India's AI-powered EV service platform (SaaS). The platform provides multi-tenant workshop management with EVFI™ (Electric Vehicle Failure Intelligence) diagnostics, ticketing, invoicing, AMC, inventory, HR, payroll, and financial reporting.

## Core Architecture
- **Backend:** FastAPI (Python) on port 8001
- **Frontend:** React (CRA + craco) on port 3000
- **Database:** MongoDB (production: `battwheels`, dev: `battwheels_dev`)
- **3rd Party:** Resend (email), Razorpay (payments), Sentry (monitoring), Gemini via Emergent LLM Key (AI)

## Current Environment
- `DB_NAME=battwheels` (PRODUCTION)
- `ENVIRONMENT=production`
- `TESTING=0`
- Dev backup: `/app/backend/.env.dev_backup`

## What's Been Implemented

### Session: March 10, 2026

#### 1. Cross-Tenant Data Leak Fixes (2 remaining)
- **`sales_finance_api.py:451`** — Added `organization_id` filter to ledger aggregation
- **`operations_api.py:322-336`** — Added `org_filter` to invoices, inventory, purchase_orders queries
- Removed hardcoded fake `monthly_repair_trends` data
- **All 10 tested endpoints return ZERO data for new orgs** ✅

#### 2. Production DB Switch
- Verified prod DB readiness (4/4 checks pass)
- Switched `DB_NAME=battwheels`, `ENVIRONMENT=production`, `TESTING=0`
- Reset platform admin password in prod
- Full smoke test: signup, login, tenant isolation — all pass

#### 3. EFI → EVFI™ Trademark Rename
- **253 instances** renamed across 40+ files (frontend + backend)
- 4 JSX files renamed: EFIResponseCard → EVFIResponseCard, EFIGuidancePanel → EVFIGuidancePanel, EFISidePanel → EVFISidePanel, TicketEFIPanel → TicketEVFIPanel
- All imports, function names (canAccessEVFI), test IDs updated
- System prompts updated to "Battwheels EVFI™"
- Full form: "Electric Vehicle Failure Intelligence"
- Backend routes: `/efi` → `/evfi` with backward-compat middleware
- RBAC + rate limiter patterns updated
- **ZERO standalone "EFI" remaining** in frontend or backend
- DB collections/env vars preserved (not renamed)

#### 4. IP Protection Technical Safeguards
- **Beta Access Gate:** Invite-only registration via `invite_code` field
  - 20 codes seeded: `BATTWHEELS-BETA-001` through `BATTWHEELS-BETA-020`
  - Validated on org signup, one-time use, tracked
  - Added to Register.jsx + SaaSLanding.jsx signup forms
- **EVFI Response Watermarking:** Zero-width Unicode watermark injected in every EVFI response, encoding org_id for IP tracing
- **AI Rate Limiting:** Free trial: 25 tokens/month (verified working)
- **Right-click Protection:** Disabled context menu on battwheels.com (production only)
- **Terms of Service:** Added clauses for reverse engineering, scraping, UI copying, EVFI output commercial use, watermark tampering

#### 5. Email Verification Flow
- **Backend:** `email_verified`, `verification_token`, `verification_token_expires` fields on signup
- **Verification email:** Branded HTML sent via Resend on registration
- **`GET /api/auth/verify-email?token=`** — Verifies email, clears token
- **`POST /api/auth/resend-verification`** — Resends with new token (24h expiry)
- **Login response** includes `email_verified` status
- **`/auth/me`** excludes verification tokens from response
- **Frontend:** `VerifyEmail.jsx` page (success/error/resend states)
- **Layout.jsx:** Amber verification banner for unverified users
- **Register.jsx:** Shows "Check your email" after successful signup
- **SaaSLanding.jsx:** Shows verification sent message in modal
- CSRF, RBAC, TenantGuard exemptions added for new endpoints

#### 6. Subscription Plan Gating (March 10, 2026)
- **planConfig.js:** Single source of truth for 4 plans (free_trial/starter/professional/enterprise), module access matrix (60+ routes), module descriptions, helper functions
- **UpgradePrompt.jsx:** Branded upgrade prompt shown when clicking locked modules — lock icon, title, description, plan comparison, UPGRADE CTA button
- **Layout.jsx sidebar:** Lock icons on inaccessible modules, click-to-show-upgrade-prompt, clears on route change
- **PlanEnforcementMiddleware:** Backend safety net gating write operations (POST/PUT/PATCH/DELETE) on 30+ route prefixes; GET always allowed
- **Record limits:** free_trial enforced at tickets(20), contacts(10), estimates(10), invoices(10), items(20) in route handlers
- **FeatureGateBanner:** Updated to handle both "free" and "free_trial" plan names

#### 7. Open Registration + Mobile UX Fixes (March 11, 2026)
- **Beta code made optional:** Registration open to all visitors, beta codes still accepted if provided
- **Mobile nav redesigned:** Hamburger menu on mobile, desktop nav unchanged
- **Pricing updated:** 4-tier pricing matching planConfig.js (Free Trial/Starter/Professional/Enterprise)
- **11 Mobile UX bugs fixed:**
  - EVFI diagnosis response: break-words, responsive padding, no text clipping
  - Dashboard/Inventory/Estimates tabs: overflow-x-auto with flex-shrink-0 for horizontal scrolling
  - Sidebar text contrast: increased from 0.45 to 0.65 opacity
  - Removed duplicate close button from mobile sidebar
  - Invoice form: responsive grid (1→3 cols), date field min-width, customer/item empty states
  - Vehicle categories seeded in production DB (6 EV categories)
  - Barcode scanner: camera permission request + rear camera preference
- **Testing:** 100% pass rate on all bugs (iteration_152.json)

## Prioritized Backlog

### P0 (Critical)
- [ ] First Customer Journey Audit (UI/UX walkthrough for all modules)

### P1 (High)
- [ ] Fix endpoint access bugs for new orgs (Operations Stats, Banking, HR Dashboard — 403/404s)
- [ ] Trial Balance Report data gap (aggregation logic)
- [ ] Fix CI/CD deployment pipeline
- [ ] Migrate remaining mocked emails to real EmailService

### P2 (Medium)
- [ ] Implement Payslip PDF Generation
- [ ] Refactor `_enhanced` file duplication
- [ ] Unify `invoices` / `ticket_invoices` collections
- [ ] Decompose "God Files" (reports_advanced.py, reports.py)
- [ ] Fix flaky backend tests (pytest hangs)

### P3 (Low)
- [ ] Demo data naming convention cleanup
- [ ] Technician Report "Avg Response N/A" fix

## Credentials
- **Platform Admin:** `platform-admin@battwheels.in` / `v4Nx6^3Xh&uPWwxK9HOs`
- **Demo Org:** `demo@voltmotors.in` / `Demo@12345`
- **Beta Codes:** BATTWHEELS-BETA-001 through BATTWHEELS-BETA-020
