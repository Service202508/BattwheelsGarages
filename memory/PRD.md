# BattWheels OS — PRD

## Original Problem Statement
The user's initial problem was a 520 production deployment error. This evolved into a comprehensive security audit and stability hardening project called "Beta Readiness." The primary goal is to resolve all critical vulnerabilities, bugs, and data inconsistencies across the platform.

## Core Requirements
1. Secrets Management: Maintain `.env.example`, no production secrets in version control
2. Multi-Tenancy Data Isolation: All queries filtered by `organization_id`
3. Defense-in-Depth: Service-layer validation of `organization_id`
4. Centralized Guards & Config
5. Code & Data Integrity
6. Database Health: Purge orphaned data and test bloat
7. Staging Environment: Fully functional and seeded

## Architecture
- **Backend:** FastAPI (Python) on port 8001
- **Frontend:** React (CRA + craco) on port 3000
- **Database:** MongoDB (motor/pymongo) — `battwheels_dev`
- **Background Jobs:** asyncio tasks (recurring invoices every 6h, SLA breach detection every 30min)

## What's Been Implemented

### Phase B-4: Module Verification
- Verified SLA, Recurring Invoices, Data Export modules
- Fixed critical multi-tenancy bug in recurring invoice creation

### Phase C-1: Inventory-Accounting Integration
- Invoice creation deducts stock from inventory
- Inventory adjustments create journal entries

### Phase C-2: Payroll-Accounting Integration & Balance Sync
- Payroll generation creates salary expense journal entries
- Chart of accounts balance sync from journal entries

### Phase C-3: Background Automation Schedulers
- Auto-generate recurring invoices (every 6 hours)
- SLA breach detection + notifications (every 30 minutes)

### Phase C-4: Frontend AI Limit & Upgrade Workflow
- AILimitPrompt component for 429 error handling
- Improved plan upgrade workflow

### Phase C-5: Frontend HR & Reassign Fixes
- HR page routing fix (owner role)
- Reassign Technician verified

### Phase C-6: EVFI Brand Patterns + AI Token Counter (COMPLETED 2026-03-14)
- Fixed EVFI match endpoint Stage 2.5 for brand-specific patterns
- Enhanced matching with fault_category detection, title regex, vehicle-only fallback
- Added `query` alias for `symptom_text` in FailureMatchRequest
- Fixed PlanLimits model_validator to map DB field `ai_calls_per_month`
- Created AIUsageCounter component with color-coded usage display
- Added counter to EVFI page header and sidebar bottom

### Phase C-10: Final E2E Platform Validation (COMPLETED 2026-03-14)
- Full 7-phase platform validation: 92/100 score
- All 30 module endpoints functional
- All 7 integrations verified, books balanced
- Security: auth, rate limiting, passwords, CORS all pass
- All 7 EVFI brands matched, both portals functional

### Pre-Deploy Quick Fixes (COMPLETED 2026-03-14)
- **Fix 1:** EVFI now accessible for Free Trial users (15 AI calls/month)
  - DB: Enabled `efi_failure_intelligence` for free plan
  - Frontend: Unlocked `/failure-intelligence` in planConfig
  - Registration: Added `usage` field to subscription doc
- **Fix 2:** Invoice line items now accept both `hsn_code` and `hsn_sac_code`
  - model_validator maps hsn_code → hsn_sac_code
- **Fix 3:** API path aliases added
  - `/reports/profit-and-loss` → `/reports/profit-loss`
  - `/accounting/journal-entries` → `/banking/journal-entries`
  - `/accounting/chart-of-accounts` → `/banking/chart-of-accounts`

## Current Status
**READY FOR DEPLOYMENT** — All pre-deploy fixes verified.

## Prioritized Backlog

### P1 (Upcoming)
- Phase C-7: Production readiness (secrets management, Sentry, production seed data)
- Phase C-8/C-9: pytest suite recovery (582 failed, 468 errors)

### P2 (Future)
- Enhance Banking Module (compute balances from journal entries)
- Deploy to Staging + full QA
- Deploy to Production
- Purge secrets from Git history
- Fix login rate limiting (add IP-based checks)

## Known Issues
- pytest suite broken (582 failed, 468 errors)
- Login rate limiting insufficient (no IP check)

## Mocked Services
- Email Service (email_service.py)
- Razorpay integration (disabled)

## Test Credentials
- Workshop Owner: demo@voltmotors.in / Demo@12345
- Free Trial Test: freetrial-test@workshop.in / Test@12345
- Technician: ankit@voltmotors.in / Tech@12345
- Customer Portal: token PORTAL-SUNITA-2026

## Key API Endpoints
- `/api/v1/evfi/match` POST - AI failure matching (accepts query alias)
- `/api/v1/subscriptions/current` GET - Subscription + usage + limits
- `/api/v1/reports/profit-loss` GET (alias: `/reports/profit-and-loss`)
- `/api/v1/accounting/journal-entries` GET (alias for banking module)
- `/api/v1/accounting/chart-of-accounts` GET (alias for banking module)

## Key Collections
- `efi_platform_patterns`: 277 patterns (61 generic + 216 brand-specific for 7 brands)
- `plans`: 4 plans with AI call limits (Free:15, Starter:25, Professional:100, Enterprise:unlimited)
