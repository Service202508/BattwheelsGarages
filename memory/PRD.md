# Battwheels OS — Product Requirements Document

## Problem Statement
Full-stack SaaS platform (React/FastAPI/MongoDB) for EV workshop management. The platform underwent a comprehensive "Grand Final Audit" identifying production-readiness gaps. A strict "Week 1" and "Week 2" remediation plan was created and is being executed.

## Architecture
- **Frontend**: React (CRA) + Shadcn/UI + TailwindCSS
- **Backend**: FastAPI + MongoDB (Motor) + Multi-tenant (TenantGuard)
- **Auth**: JWT + Emergent Google Auth
- **Integrations**: Resend (email), Razorpay, Stripe (test), Gemini (Emergent LLM), Sentry, WhatsApp (mocked)

## What's Been Implemented

### Week 1 (Complete)
- [x] JWT unification
- [x] Dead code removal
- [x] Route scoping
- [x] GSTR credit note inclusion (C-06)
- [x] Audit logging for financial mutations (C-05)
- [x] Period-locking design document (C-03)

### Week 2 (Complete — Feb 25, 2026)
- [x] **M-NEW-02**: Fixed `user_role` in audit entries (field mismatch: `user_role` → `tenant_user_role`)
- [x] **H-NEW-01**: Fixed 3 unscoped `organization_settings` queries in `gst.py`
- [x] **Estimates Chain**: Verified end-to-end (Create → Edit → Save → Convert to Invoice). Both reported bugs (edit modal, save error) are NOT reproducible — chain working correctly
- [x] **Password Reset — 3 Flows**:
  - Flow 1: Admin resets employee password (`POST /api/v1/employees/{id}/reset-password`)
  - Flow 2: Self-service password change (`POST /api/auth/change-password`)
  - Flow 3: Forgot password via email with Resend (`POST /api/auth/forgot-password` + `POST /api/auth/reset-password`)
  - Password strength validation (8+ chars, uppercase, number, special char)
  - Tokens stored as SHA-256 hashes, 1-hour TTL, one-time use
  - Audit logging for admin password resets
  - DB indexes: token_hash (unique), user_id, expires_at (TTL)
- [x] **TicketDetail Standalone Page**: Full-page view at `/tickets/:ticketId` with 6 sections (Customer/Vehicle, Service, Costs, Activity Timeline, Status/Actions, Invoice)
- [x] **HR Dashboard**: Landing page at `/hr` with KPI cards, attendance summary, leave requests, payroll table, quick links
- [x] **Environment Badge**: Platform Admin header shows PRODUCTION/STAGING/DEVELOPMENT badge fetched from backend
- [x] **PWA Service Worker**: `service-worker.js` created with network-first strategy, registered in `index.js`

## Test Coverage
- `test_audit_logging.py`: 15 tests (including 2 new for user_role)
- `test_gstr3b_credit_notes.py`: 15 tests
- `test_password_reset.py`: 9 tests
- `test_week2_features.py`: 15 tests (created by testing agent)
- **Total: 54 tests**

## Remaining/Future Tasks

### P1 — Upcoming
- Refactor `EstimatesEnhanced.jsx` (2,900+ lines)
- Configure live WhatsApp credentials

### P2 — Backlog
- Period locking implementation (design doc exists at `/app/docs/PERIOD_LOCKING_DESIGN.md`)
- Enhanced reporting and analytics
- Mobile-responsive optimization

## Key Credentials
- **Admin**: admin@battwheels.in / Admin@12345
- **Dev**: dev@battwheels.internal / DevTest@123
- **Org ID**: 6996dcf072ffd2a2395fee7b
