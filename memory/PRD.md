# BattWheels EV Service Platform - PRD

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
- **Database:** MongoDB (motor/pymongo)
- **Background Jobs:** asyncio tasks (recurring invoices every 6h, SLA breach detection every 30min)

## What's Been Implemented
- Phase B-4: Module Verification (SLA, Recurring Invoices, Data Export)
- Phase C-1: Inventory-Accounting Integration (invoice stock deduction, journal entries)
- Phase C-2: Payroll-Accounting Integration & Balance Sync
- Phase C-3: Background Automation Schedulers (recurring invoices, SLA breach detection)
- Phase C-4: Frontend AI Limit & Upgrade Workflow (429 handling, AILimitPrompt component)
- Phase C-5: Frontend HR & Reassign Fixes
- Phase C-6 (Partial): EVFI Data Seeding (216 brand-specific patterns seeded)
- Deployment Readiness: CORS_ORIGINS fixed to wildcard for Emergent deployment

## Current Status
- **Phase C-6 IN PROGRESS:** EVFI match endpoint needs fix to query `efi_platform_patterns` + AI token counter not started

## Prioritized Backlog

### P0 (In Progress)
- Fix EVFI match endpoint to include brand-specific patterns
- AI Token Counter on EVFI pages + Header

### P1 (Upcoming)
- Phase C-7: Production readiness (secrets, Sentry, production seed data)
- Phase C-8/C-9: pytest suite recovery
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
- EVFI search ignores brand-specific patterns (fix in progress)

## Mocked Services
- Email Service (email_service.py)
- Razorpay integration (disabled)

## Test Credentials
- Workshop Owner: demo@voltmotors.in / Demo@12345
- Technician: Tech@12345
- Customer Portal: via portal_access_token in contacts collection
