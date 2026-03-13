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
- Full multi-tenant security audit and hardening
- Database cleanup (191MB → 11MB)
- Seed scripts for dev/staging/production
- Password security fix (removed plaintext passwords)
- Routing fixes for 6+ modules (307 redirect issues)
- Field consistency fixes (organization_id standardization)
- Rate limiting on login endpoint
- **P0-4: Payment recording fix** — corrected collection names (contacts/invoices)
- **P0-5: Registration fix** — full flow: user + org + membership + subscription

## Pending (P1)
- Subscription API `plan_code: None` serialization fix
- Advanced Reports endpoints (404)
- EVFI Guided Diagnosis endpoint (404)
- HR/Employees frontend page

## Backlog (P2/P3)
- Deploy to Staging + full QA
- Clean up test data from battwheels_dev
- Deploy to Production
- Purge secrets from Git history
- Fix backend test suite
- Standardize customer_id vs contact_id fields
