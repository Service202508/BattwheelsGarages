# BattWheels OS — Product Requirements Document

## Overview
BattWheels OS is a fleet/garage management SaaS for electric vehicles. It provides service ticket management, EVFI (diagnostic AI), invoicing, inventory, HR, and comprehensive reporting for EV workshops.

## Core Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI (dark theme, "bw-volt" green accent)
- **Backend**: FastAPI + MongoDB (via Motor async driver)
- **Auth**: JWT-based, multi-tenant with organization_id scoping
- **AI**: Gemini via Emergent LLM Key (EVFI diagnostic engine)
- **Payments**: Razorpay
- **Email**: Resend
- **Monitoring**: Sentry

## What's Been Implemented

### Security (Session 15)
- 37 cross-tenant data leak endpoints fixed (23 LEAK, 14 PARTIAL)
- RBAC middleware regex patterns fixed for owner role access
- All summary/stats endpoints now enforce organization_id scoping

### UX Fixes (Session 16 — Current)
- **EVFI Diagnosis Readability**: Responsive padding (px-3 mobile / px-6 desktop), break-words, flex-shrink-0 badges, max-w-4xl desktop width
- **Dropdown Empty States**: All major dropdowns (customer, item, service, parts) show helpful empty states with navigation links when no data exists
- **Sidebar Contrast**: Section labels at 50% opacity (up from 25%), nav items at 75% opacity (up from 65%), icons at 50% (up from 40%)
- **Single Close Mechanism**: Mobile Sheet X button styled for dark theme with z-10, no duplicate close buttons
- **Dashboard Tabs Scrollable**: overflow-x-auto with touch scrolling, hidden scrollbar, flex-shrink-0 on each tab
- **Inventory Tabs Scrollable**: Same pattern applied to ItemsEnhanced tabs
- **Invoice Date Display**: whitespace-nowrap + min-w-[100px] prevents date truncation on mobile
- **Estimate Date Inputs**: min-w-[140px] prevents truncation

### Testing Status
- All 11 UX fixes verified at 390px (mobile) and 1920px (desktop) — 100% pass rate
- Build passes successfully

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
- Fix React hydration warnings (span in tbody)
- Demo data naming convention (Pvt Ltd)
- Technician report "Avg Response N/A"

## Key Credentials
- Demo Org: demo@voltmotors.in / Demo@12345
- DB: battwheels (production), battwheels_dev (testing)
- EVFI branding is trademarked — always use EVFI, never EFI
