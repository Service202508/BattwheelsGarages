# Battwheels OS — Product Requirements Document

## Project Overview
EV Workshop Management Platform with integrated accounting, inventory, HR, and AI-powered diagnostics (EVFI).

## Current Phase: Beta Readiness (Phase C)
Multi-session deep integration work to make all modules talk to each other.

---

## Completed Work (Phase C Sessions)

### C-1: Invoice→Inventory + Inventory→Journal ✅
- Invoice creation now deducts stock from inventory with history tracking
- Inventory adjustments create double-entry journal entries
- Commits: c41439bd, 3a36f7bb

### C-2: Payroll→Journal + CoA Balance Sync ✅
- Payroll generation creates salary expense journal entries (fixed account code 6000)
- Chart of Accounts balances sync from journal entries on every entry
- New endpoint: POST /api/v1/journal-entries/accounts/sync-balances
- Commits: c9da0f5a, 1140fc98

### C-3: Background Jobs ✅
- Recurring invoice auto-generation (every 6 hours)
- SLA breach auto-detection with notifications (every 30 minutes)
- Both registered in server.py lifespan
- Commit: f9829264

### C-4: Frontend - AI Limits + Plan Upgrade ✅
- 429 AI limit handling with AILimitPrompt component
- Applied to: AIDiagnosticAssistant, EVFIGuidancePanel, FailureIntelligence
- Plan upgrade workflow with Razorpay fallback to contact email
- Commits: c69fce52, 9fb2471f

### C-5: Frontend - HR Routes + Plan Limits ✅
- Added "owner" role to HR, Payroll, Employees, Attendance, Leave routes
- Set AI call limits for all plans in database:
  - Free Trial: 10 AI calls/mo
  - Starter: 25 AI calls/mo
  - Professional: 100 AI calls/mo
  - Enterprise: Unlimited
- Reassign Technician: Already fully implemented (verified working)
- Commit: c2ff30c3

---

## Upcoming Tasks (Phase C Remaining)

### C-6: EVFI Enhancement
- Brand patterns integration
- Token counter for AI usage display

### C-7: Production Preparation
- Secrets management
- Sentry error tracking
- Database seeding scripts

### C-8-9: Test Suite Recovery
- Fix pytest suite (582 failed, 468 errors)
- Create regression test files

### C-10: Final E2E + Cleanup
- End-to-end testing
- Code cleanup and documentation

---

## Key Technical Decisions

1. **Background Jobs**: Using asyncio tasks in FastAPI lifespan (not Celery/APScheduler)
2. **Balance Sync**: Per-entry sync + batch endpoint (hybrid approach)
3. **AI Limits**: Enforced at service layer with 429 response
4. **Role-Based Access**: "owner" role added to all admin-level routes

---

## API Endpoints Added/Modified

- `POST /api/v1/journal-entries/accounts/sync-balances` - Batch balance recalculation
- `POST /api/v1/recurring-invoices/process-due` - Manual trigger for recurring invoices
- Background: `_recurring_invoice_scheduler()` - Auto-generates due invoices
- Background: `_sla_breach_checker()` - Flags SLA breaches, creates notifications

---

## Database Changes

- `plans` collection: Added `limits.ai_calls_per_month` for all plans
- `subscriptions` collection: Added `features.ai_calls_per_month`
- `inventory_history` collection: Now populated on invoice stock deductions
- `sla_breaches` collection: Populated by background SLA checker
- `notifications` collection: SLA breach notifications added

---

## Credentials for Testing
- Workshop Owner: demo@voltmotors.in / Demo@12345
- Database: battwheels_dev (development), battwheels (production - UNTOUCHED)
