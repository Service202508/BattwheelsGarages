# Battwheels OS — Product Requirements Document

## Product Overview
Battwheels OS is a full-stack SaaS platform (React/FastAPI/MongoDB) for EV service management. It includes multi-tenant architecture, double-entry accounting, GST compliance, HR/Payroll, inventory management, AI diagnostics, fleet management, and Zoho Books integration.

## Core Architecture
- **Frontend:** React + Shadcn UI
- **Backend:** FastAPI (Python 3.11)
- **Database:** MongoDB (Motor async driver)
- **Auth:** JWT-based + Emergent Google Auth
- **AI:** Gemini 3 Flash (Emergent LLM Key)
- **Integrations:** Razorpay, Stripe (test), Resend, Sentry, WeasyPrint, WhatsApp (mocked)

## Multi-Tenancy
- TenantGuardMiddleware enforces org_id on all non-public routes
- RBACMiddleware enforces role-based access control
- All collections scoped by `organization_id`

---

## Completed Work

### P0 Security Fixes (2026-02-25) — ALL VERIFIED
1. **P0-1: RBAC Bypass Fix** — Path normalization in `middleware/rbac.py` strips `/v1` before matching ROUTE_PERMISSIONS patterns. 17/17 tests passed.
2. **P0-2: Zoho Sync Guard** — All `delete_many` and `drop_collection` calls in `routes/zoho_sync.py` scoped by `organization_id` + environment gate.
3. **P0-3: AI Tenant Scoping** — `routes/ai_assistant.py` extracts org_id/user_id from `request.state` (not request body). Session ID org-scoped.
4. **P0-4: Journal Idempotency** — Application-level check + unique sparse index on `(organization_id, source_document_id, source_document_type)` in `journal_entries` collection. Trial balance confirmed BALANCED.

### Previous Session Work
- Data integrity migration: 1,172 documents fixed for multi-tenancy
- Public route fix for ticket submission
- JWT secret unification
- Compound index creation
- Comprehensive security audits

---

## Prioritized Backlog

### P1 — Next
- **Credit Notes (GST Compliance):** Full credit note feature with journal entries and GST handling

### P2
- Refactor `EstimatesEnhanced.jsx` (2900+ lines)
- Consolidate 5 redundant auth middleware files into 1

### P3
- Configure live WhatsApp credentials
- Implement Celery for background jobs

### P4
- E2E Playwright tests
- Logo swap

---

## Test Credentials
- Admin: `admin@battwheels.in` / `TestPass@123`
- Technician: `tech@battwheels.in` / `TestPass@123`
- Org ID: `6996dcf072ffd2a2395fee7b`
