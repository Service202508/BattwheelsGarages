# BattWheels OS — Product Requirements Document

## Overview
BattWheels OS is a fleet/garage management SaaS for electric vehicles. It provides service ticket management, EVFI™ (diagnostic AI), invoicing, inventory, HR, and comprehensive reporting for EV workshops.

## Core Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI (dark theme, "bw-volt" green accent #CBFF00)
- **Backend**: FastAPI + MongoDB (via Motor async driver)
- **Auth**: JWT-based, multi-tenant with organization_id scoping
- **AI**: Gemini via Emergent LLM Key (EVFI™ diagnostic engine)
- **Payments**: Razorpay
- **Email**: Resend
- **Monitoring**: Sentry

## What's Been Implemented

### Security (Session 15)
- 37 cross-tenant data leak endpoints fixed (23 LEAK, 14 PARTIAL)
- RBAC middleware regex patterns fixed for owner role access
- All summary/stats endpoints enforce organization_id scoping

### UX Fixes (Session 16)
- EVFI Diagnosis Readability: Responsive padding, break-words, max-w-4xl desktop
- Dropdown Empty States: Customer, item, service, parts show helpful empty states
- Sidebar Contrast: Section labels 50% opacity, nav items 75% opacity
- Dashboard & Inventory Tabs: Horizontally scrollable on mobile
- Invoice Date Display: No truncation with whitespace-nowrap

### Homepage Content Rewrite v2.0 (Session 17 — Current)
- **TASK 1**: Hero → "Stop Guessing. Start Fixing." + 4-benefit subtitle + VAHAN connecting line
- **TASK 2**: Problem section → "Billing & GST Chaos" with new Hinglish quote
- **TASK 3**: LiveShowcase → Without/With comparisons, EVFI context lines, billing chain, Hinglish
- **TASK 4**: Opportunity → Closing paragraph with ₹25,000 Cr + EVFI
- **TASK 5**: Five Audiences → Added Dealers tab, updated all feature pills
- **TASK 6**: EVFI section → Hinglish emotional hook, "Diagnoses & Resolves"
- **TASK 7**: Built for Scale → "Your Data, Only Yours" replacing "Multi-Tenant"
- **TASK 8**: Pricing → "tokens" → "diagnoses" in all 4 tiers
- **TASK 9**: Flywheel → User-focused language, "Yeh aapka competitive advantage hai"
- **TASK 10**: CTA → Pain-focused Hinglish CTA
- **TASK 11**: ProductTour → Updated titles, captions, final CTA
- **TASK 12**: Global sweep verified (0 "workshop owner", 0 "tokens", 30+ EVFI mentions)

### Files Modified (Session 17)
- `frontend/src/pages/SaaSLanding.jsx` — All landing page content
- `frontend/src/components/LiveShowcase.jsx` — 5 showcase panels enhanced
- `frontend/src/components/ProductTour.jsx` — Tour step titles/captions updated

## Prioritized Backlog

### P0
- First Customer Journey Audit (new user onboarding walkthrough)

### P1
- Fix backend test suite (conftest.py fixture issue)
- Clean orphaned tenant records in production DB
- Automate vehicle category seeding for new orgs
- Verify production email service (Resend)
- Fix CI/CD pipeline

### P2
- Implement Payslip PDF generation
- Fix Trial Balance Report (shows ₹0.00)
- Refactor _enhanced file duplication
- Decompose "God Files" (reports_advanced.py)
- Unify invoices and ticket_invoices collections
- Migrate mocked emails to real EmailService
- Demo data naming convention (Pvt Ltd)
- Technician report "Avg Response N/A"

## Key Credentials
- Demo Org: demo@voltmotors.in / Demo@12345
- DB: battwheels (production), battwheels_dev (testing)
- EVFI™ branding is trademarked — always use EVFI™, never EFI
