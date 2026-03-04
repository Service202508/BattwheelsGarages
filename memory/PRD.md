# Battwheels OS — Product Requirements Document

## Original Problem Statement
Battwheels OS is an EV service workshop management SaaS platform. After a stability audit, the codebase was reverted, and a "REBUILD SESSION 1 — P0: EFI + FLOW BLOCKERS" was initiated to restore high-priority features.

## Architecture
- **Frontend**: React + Vite (craco), shadcn/ui, Tailwind CSS
- **Backend**: FastAPI + MongoDB (motor async)
- **DB**: MongoDB (`battwheels_dev` for dev, `battwheels` for production)
- **Auth**: JWT-based, RBAC with roles (platform_admin, owner, technician, etc.)

## Credentials
- Demo User: `demo@voltmotors.in` / `Demo@12345`
- Dev Admin: `platform-admin@battwheels.in` / `DevTest@123`
- Owner User: `dev@battwheels.internal` / `DevTest@123`

## Completed Tasks (Session 1A - 2026-03-04)

### Task 0: Verification Scripts — DONE
- `/app/scripts/verify_platform.sh` — exists, executable
- `/app/scripts/verify_prod_org.py` — exists, valid Python

### Task 1: Vehicle Category Dropdown Fix — DONE
- **Root cause**: 218 duplicate entries in `vehicle_categories` collection (seed script ran multiple times without idempotency)
- **Fix**: Cleaned duplicates (kept 5 unique: 2W_EV, 3W_EV, 4W_EV, COMM_EV, LEV), added unique index on `code`
- Also cleaned 882 duplicate `vehicle_models` (35 unique remain), added unique index on `model_id`
- Made seed function idempotent (uses upsert instead of insert_many)

### Task 2: Platform Admin Fixes — DONE
- **Back arrow**: Added back button (`data-testid="platform-admin-back-btn"`) to PlatformAdmin header using `navigate(-1)`
- **Logout button**: Already existed (`data-testid="platform-admin-logout-btn"`) with `onLogout` prop properly passed from App.js

## Prioritized Backlog

### P0 — Next Session (Tasks 3-6)
- Task 3: EFI Intelligence Panel in Ticket Detail
- Task 4: EFI All 7 Modes + Hinglish Fix (EFIGuidancePanel.jsx bugs)
- Task 5: AI Diagnosis Branding + IP Protection (remove copy/share buttons)
- Task 6: Investigate Items Route 404 (`/api/v1/items`)

### P3 — Future
- Fix skipped password reset tests (state pollution in `test_password_reset.py`)
- Investigate failed API spot-checks (404s on `items/search`, `efi-guided/failure-cards`)
