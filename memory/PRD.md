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
- Organizations (signup, invites, team management, branding)
- Contacts, Vehicles, Tickets, Invoices, Estimates, Bills
- Payments Received, Credit Notes, Sales Orders
- Items/Inventory, Chart of Accounts, Journal Entries
- HR/Employees, Subscriptions, EVFI AI

## What's Been Implemented

### Security & Stability (Sessions 1-6)
- Full multi-tenant security audit and hardening
- Database cleanup (191MB -> 11MB)
- Seed scripts for dev/staging/production
- Password security fix (removed plaintext passwords)
- Routing fixes for 6+ modules (307 redirect issues)
- Field consistency fixes (organization_id standardization)

### P0 Batch 2 (Session 7)
- Payment recording fix — corrected collection names (contacts/invoices)
- Registration fix — full flow: user + org + membership + subscription

### P0-6 Chain Breaks (Session 8 — Current)
- **FIX 1:** Added `organization_id` to estimates-enhanced and sales-orders-enhanced POST handlers
- **FIX 2:** Added `plan_id` to subscription created during registration (fixes EVFI for new orgs)
- **FIX 3:** Added empty-path POST decorator to invoices-enhanced (trailing slash 405)
- **FIX 4:** Added `invoice_id` convenience field to payment API with auto-allocation + invoice status update
- **Data fixes:** 3 orphaned estimates patched, 2 subscriptions missing plan_id patched
- **Full chain verified:** Register → Contact → Vehicle → Ticket → EVFI → Estimate → Invoice → Payment → Journal (all PASS)

## Pending (P1)
- Subscription API `plan_code: None` serialization fix
- Rate limiting on auth endpoints (slowapi)
- Advanced Reports endpoints (404)
- EVFI Guided Diagnosis endpoint (404)
- HR/Employees frontend page

## Backlog (P2/P3)
- Deploy to Staging + full QA
- Clean up test data from battwheels_dev
- Deploy to Production
- Purge secrets from Git history
- Fix backend test suite (582 failed, 468 errors)
- Standardize customer_id vs contact_id fields
