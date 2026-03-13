# Battwheels OS — Product Requirements Document

## Overview
AI-powered EV workshop management SaaS platform with multi-tenant architecture, double-entry accounting, EVFI (EV Failure Intelligence), and full service lifecycle management.

## Architecture
- **Backend:** FastAPI + MongoDB (Motor async driver)
- **Frontend:** React
- **Auth:** JWT (bcrypt passwords, SHA256 migration path)
- **Multi-tenancy:** organization_id-based data isolation
- **Database:** MongoDB (battwheels_dev for development)

## Core Modules
- Auth (register, login, password management)
- Organizations, Contacts, Vehicles, Tickets, Invoices, Estimates, Bills
- Payments Received, Credit Notes, Sales Orders
- Items/Inventory, Chart of Accounts, Journal Entries
- HR/Employees, Subscriptions, EVFI AI

## Completed Work

### Sessions 1-6: Security & Stability
- Full multi-tenant security audit and hardening
- Database cleanup (191MB -> 11MB), seed scripts
- Password security fix, routing fixes, field consistency

### Session 7: P0 Batch 2
- Payment recording fix (correct collection names)
- Registration fix (full user+org+membership+subscription flow)

### Session 8: P0-6 Chain Breaks
- Added organization_id to estimates-enhanced and sales-orders-enhanced POST
- Added plan_id to registration subscription (fixed EVFI for new orgs)
- Invoice POST trailing slash fix, payment auto-allocation

### Session 9: P1 Batch 1
- Rate limiting: login (5/email/15min), register (3/IP/min), forgot-password (3/IP/min)
- Subscription plan_code serialization confirmed working (was already fixed by plan_id fix)
- EVFI patterns audit: 61 platform patterns, 150 decision trees, 1102 knowledge articles

### Session 10: EVFI UX Fixes
- AI Assistant layout: widened response panel (40/60 split instead of 50/50)
- EVFI Guidance fallback: pattern-based diagnostics when LLM unavailable
  - 6 structured steps per category (battery/motor/controller/electrical)
  - Hinglish translations, probable causes with confidence scores
  - Graceful degradation — no blank panels

### Session 11: Live Feedback Fixes
- Technician "Assign/Reassign" button state-aware
- Subscription pricing corrected in DB; new signups get free_trial plan

### Session 12: Beta Readiness — Reports & Token Tracking (2026-03-13)
- **Advanced Reports:** Verified all 13 /reports-advanced/* endpoints return 200 (route registration was already correct)
- **AI Token Tracking:** Wired UsageTracker.increment_usage("ai_calls") to all EVFI LLM routes:
  - `ai_assistant.py` /diagnose — tracks after successful LLM call
  - `ai_guidance.py` /generate — tracks after guidance generation
  - `efi_guided.py` /session/start — tracks after successful session creation
  - Initialized UsageTracker singleton in server.py
- Subscription page now correctly shows AI Calls (e.g., "2 / 100, 98 remaining")
- Testing: 100% backend (18/18), 100% frontend verified

### Session 13: Plan Limit Enforcement + EVFI Guided Endpoint (2026-03-13)
- **AI Call Limit Enforcement:** Added `check_limit("ai_calls")` guard BEFORE LLM calls on all routes:
  - `ai_assistant.py` /diagnose — blocks with 429 when at limit
  - `ai_guidance.py` /generate — blocks with 429 when at limit
  - `efi_guided.py` /session/start — blocks with 429 when at limit
  - `efi_guided.py` /start (new) — blocks with 429 when at limit
  - 429 response includes: error, message, current_usage, limit, upgrade_url
  - Plan limits: free=10, starter=25, professional=100, enterprise=unlimited
- **EVFI Guided Standalone Endpoint:** New `POST /evfi-guided/start`
  - Accepts: vehicle_make, vehicle_model, symptom, category (optional), mode (hinglish/classic)
  - Returns: safety_warnings, diagnostic_steps, probable_causes, recommended_fix
  - Auto-detects category from symptom keywords (battery/motor/controller/electrical)
  - Hinglish mode includes Hindi translations; classic mode strips them
  - Uses pattern-based fallback (works without LLM)
- Testing: 100% backend (16/16 tests passed)

### Session 14: Phase B-1 — Customer Portal + Invoice PDF (2026-03-13)
- **Customer Portal:** All 10 endpoints verified (200 OK)
  - Portal auth: POST /customer-portal/login with token → X-Portal-Session header
  - Dashboard, tickets, invoices, estimates, payments, statement, profile, vehicles, documents
  - 401 returned without valid session
  - **Data leak fix:** Excluded organization_id, _seed, assigned_technician_id, internal_notes, resolution_notes, efi_preprocessing from portal ticket responses
- **Invoice PDF:** GST-compliant, 25KB
  - **Fix:** CGST/SGST were ₹0.00 because data stored tax as IGST even for intra-state
  - Root cause: pdf_service.py used `item.get('cgst_amount', tax/2)` but cgst_amount was explicitly 0
  - Fix: Split IGST into CGST/SGST when intra-state (is_igst=False) and cgst/sgst are 0
  - Verified: GSTIN, HSN codes (8507, 998719), CGST ₹990 + SGST ₹990, Grand Total ₹12,980
- Testing: 100% backend (16/16 tests passed)

### Session 15: Phase B-2 — Technician Portal + Financial Reports (2026-03-13)
- **Technician Portal:** All endpoints verified (200 OK)
  - Tech login: ankit@voltmotors.in / Tech@12345 — role=technician
  - Fixed null org_id on voltmotors techs (ankit, ravi)
  - Dashboard, tickets (9 assigned), ticket detail, start-work, productivity, attendance, leave, payroll
  - Access control: tech correctly blocked from contacts (403)
- **Financial Reports Fix:** P&L and Balance Sheet returned all zeros
  - Root cause: AccountType enum uses title-case ("Income", "Expense", "Asset", "Liability") but seed data uses lowercase ("revenue", "expense", "asset", "liability")
  - Fix: Added lowercase values to $in filters and classification logic in double_entry_service.py
  - P&L: Income=₹36,750, Expenses=₹217,200, Net Profit=-₹180,450
  - Balance Sheet: Assets=₹26,165, Liabilities=₹206,615, Equity=-₹180,450, **Balanced=True**
  - Trial Balance: ₹335,565 debit/credit (balanced)
  - Account Ledger: working with running balance
- Testing: 100% backend (16/16 tests passed)

## Pending (P2)
- Reassign Technician full backend functionality
- Plan Upgrade workflow

## Backlog (P2/P3)
- Banking module reports read from chart_of_accounts (always 0) — need to sync from journal entries
- HR/Employees frontend page
- Deploy to Staging + full QA
- Clean up test data from battwheels_dev
- Deploy to Production
- Purge secrets from Git history
- Fix backend test suite (582 failed)
- Standardize customer_id vs contact_id fields
- EVFI: expand patterns beyond motor category
- Login rate limiting IP enhancement (prevent email spraying)
- Frontend: handle 429 AI limit on EVFI page with upgrade prompt
