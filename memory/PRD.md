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
- 37 cross-tenant data leak endpoints fixed
- RBAC middleware regex patterns fixed for owner role access

### UX Fixes (Session 16)
- EVFI Diagnosis Readability, Dropdown Empty States, Sidebar Contrast
- Dashboard & Inventory Tabs scrollable, Invoice Date Display fix

### Homepage Content Rewrite v2.0 (Session 17)
- Hero: "Stop Guessing. Start Fixing." + EVFI tagline + 4-benefit subtitle
- Problem section: "Billing & GST Chaos" with Hinglish quote
- LiveShowcase: Without/With comparisons, EVFI context, billing chain, Hinglish
- Five Audiences: Dealers tab added, all feature pills updated with EVFI
- EVFI section: Hinglish emotional hook, "Diagnoses & Resolves"
- Built for Scale: "Your Data, Only Yours" replacing "Multi-Tenant"
- Pricing: "tokens" -> "diagnoses" in all 4 tiers
- Flywheel: User-focused language
- CTA: Pain-focused Hinglish
- ProductTour: Updated titles, captions, final CTA

### Homepage Polish (Session 18 - Current)
- EVFI tagline "Battwheels EVFI™ AI Diagnosis & Troubleshooting" below hero heading
- All em dashes (—) replaced with hyphens (-) across 3 files (13+6+6=25 total)
- Stats updated: 990+ -> 1990+ patterns, 795+ -> 12195+ knowledge articles
- Product Tour: All 15 steps verified functional with correct content
- Build clean, DB_NAME=battwheels confirmed

### Files Modified (Session 18)
- `frontend/src/pages/SaaSLanding.jsx` — EVFI tagline, em dashes, stats
- `frontend/src/components/LiveShowcase.jsx` — em dashes replaced
- `frontend/src/components/ProductTour.jsx` — em dashes, stats updated

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
- Fix Trial Balance Report (shows 0.00)
- Refactor _enhanced file duplication
- Decompose "God Files" (reports_advanced.py)
- Unify invoices and ticket_invoices collections
- Migrate mocked emails to real EmailService
- Demo data naming convention (Pvt Ltd)
- Technician report "Avg Response N/A"

## Key Credentials
- Demo Org: demo@voltmotors.in / Demo@12345
- DB: battwheels (production), battwheels_dev (testing)
- EVFI™ is trademarked — always use EVFI™, never EFI
