# BattWheels Platform - Product Requirements Document

## Original Problem Statement
Multi-phase project to improve application stability, maintainability, feature set, and security. Current critical task: scrub all secrets from Git history to prepare the repository for public GitHub push.

## Architecture
- **Frontend:** React/CRACO
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **3rd Party:** Razorpay, Resend, Sentry, Zoho Books, Emergent LLM (GPT-4o-mini, Gemini-2.5-flash)

## Completed Work
- [2026-03-01] Git history secret scrubbing - Pass 3: Scrubbed `rzp_live_REDACTED`, partial Sentry DSN prefixes (`8b734d...`, `ae17014...`), Zoho Org ID (`60029414603`), `TEST_PASSWORD=admin` from all 4359 commits
- [Previous] Git history secret scrubbing - Pass 1 & 2: Removed `.env` files from history, scrubbed hardcoded secrets from source files using git-filter-repo
- [Previous] Security: CORS hardening, brute-force protection
- [Previous] Frontend: Cursor pagination modernization
- [Previous] Testing: 693 passing tests

## Current Status
- All known secret values scrubbed from git history
- Application healthy: backend, frontend, MongoDB all running
- Awaiting user verification via GitHub push

## Prioritized Backlog

### P0
- Push to GitHub (pending user verification)

### P1
- Decompose "God-Files" (Tickets, Estimates, EFI modules)
- Remediate Test Debt (26 test files per TEST_DEBT_REGISTER.md)
- Unskip 19 remaining core tests

### P2
- Backend Task Runner (Celery)
- Zendesk Integration (replace stub)
- Banking Cursor Pagination (backend + frontend)
- Frontend Test Suite (Jest/RTL or Cypress)

## Known Issues
- 19 core tests skipped
- 26 test files in test debt register need refactoring
- Banking frontend not migrated to cursor pagination (backend lacks support)
- Razorpay uses test/disabled keys
- expert_queue_service.py uses stub ZendeskBridge

## Credentials
- Dev Admin: platform-admin@battwheels.in / DevTest@123
- Demo User: demo@voltmotors.in / Demo@12345
