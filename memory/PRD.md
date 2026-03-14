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
- Fixed EVFI match endpoint Stage 2.5 to properly search `efi_platform_patterns`
- Enhanced matching with fault_category detection, title regex, vehicle-only fallback
- Added `query` alias for `symptom_text` in FailureMatchRequest
- Fixed PlanLimits model_validator to map DB field `ai_calls_per_month`
- Created AIUsageCounter component with color-coded usage display
- Added counter to EVFI page header and sidebar bottom
- Auto-refresh counter after AI calls
- CORS reverted to explicit origins (Emergent domains handled by regex)

### Deployment Readiness
- CORS configured: explicit origins + regex for Emergent domains

## Prioritized Backlog

### P1 (Upcoming)
- Phase C-7: Production readiness (secrets management, Sentry, production seed data)
- Phase C-8/C-9: pytest suite recovery (582 failed, 468 errors)
- Phase C-10: Final E2E testing and cleanup

### P2 (Future)
- Enhance Banking Module (compute balances from journal entries)
- Deploy to Staging + full QA
- Deploy to Production
- Purge secrets from Git history
- Fix login rate limiting (add IP-based checks)
- Unify duplicate P&L report endpoints

## Known Issues
- pytest suite broken (582 failed, 468 errors)
- Login rate limiting insufficient (no IP check)

## Mocked Services
- Email Service (email_service.py)
- Razorpay integration (disabled)

## Test Credentials
- Workshop Owner: demo@voltmotors.in / Demo@12345
- Technician: Tech@12345
- Customer Portal: via portal_access_token in contacts collection

## Key API Endpoints
- `/api/v1/evfi/match` POST - AI failure matching (supports query alias)
- `/api/v1/subscriptions/current` GET - Subscription + usage + limits
- `/api/v1/subscriptions/usage` GET - Detailed usage breakdown
- `/api/v1/recurring-invoices/process-due` POST - Auto-generate invoices
- `/api/v1/journal-entries/accounts/sync-balances` POST - Recalc account balances

## Key Collections
- `efi_platform_patterns`: 277 patterns (61 generic + 216 brand-specific for 7 brands)
- `failure_cards`: Org-specific failure knowledge base
- `plans`: 4 plans with AI call limits (Free:10, Starter:25, Professional:100, Enterprise:unlimited)
