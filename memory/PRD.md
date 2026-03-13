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

## Pending (P1)
- Advanced Reports endpoints (404)
- EVFI Guided Diagnosis endpoint (separate from guidance — 404)
- HR/Employees frontend page

## Backlog (P2/P3)
- Deploy to Staging + full QA
- Clean up test data from battwheels_dev
- Deploy to Production
- Purge secrets from Git history
- Fix backend test suite (582 failed)
- Standardize customer_id vs contact_id fields
- EVFI: expand patterns beyond motor category
- AI token tracking: wire explicit usage tracking into guidance routes
