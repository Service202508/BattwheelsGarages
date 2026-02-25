# Battwheels OS — Product Requirements Document

## Product Overview
Battwheels OS is a full-stack SaaS platform (React/FastAPI/MongoDB) for EV service management. Multi-tenant architecture, double-entry accounting, GST compliance, HR/Payroll, inventory management, AI diagnostics, fleet management, and Zoho Books integration.

## Core Architecture
- **Frontend:** React + Shadcn UI
- **Backend:** FastAPI (Python 3.11)
- **Database:** MongoDB (Motor async driver)
- **Auth:** JWT-based + Emergent Google Auth
- **AI:** Gemini 3 Flash (Emergent LLM Key)
- **Integrations:** Razorpay, Stripe (test), Resend, Sentry, WeasyPrint, WhatsApp (MOCKED)

## Multi-Tenancy
- TenantGuardMiddleware enforces org_id on all non-public routes
- RBACMiddleware enforces role-based access control (path normalization fixed)
- All collections scoped by `organization_id`

---

## Completed Work

### P1: Credit Notes — GST Compliance (2026-02-25) — VERIFIED 15/15 + Frontend
- **Backend:** Full CRUD at `/api/v1/credit-notes/` (POST create, GET list, GET single, GET PDF)
- **Journal Templates:**
  - Outstanding invoice: DEBIT Sales Revenue + GST Payable, CREDIT Accounts Receivable
  - Paid invoice: DEBIT Sales Revenue + GST Payable, CREDIT Refund Payable (code 2410)
- **Validation:** Rejects DRAFT invoices, exceeds-total, exceeds-remaining, GST treatment matches original
- **PDF:** WeasyPrint with full GST breakdown (CGST/SGST or IGST), prominent "CREDIT NOTE" label
- **Sequence:** Atomic CN-00001 format via sequences collection
- **Frontend:** CreditNoteCreateModal + CreditNoteViewModal, accessible from invoice detail
- **Indexes:** org_date, org_invoice, unique org_number on credit_notes collection
- **Trial balance BALANCED after all CN postings**

### P0 Security Fixes (2026-02-25) — ALL VERIFIED 17/17
1. **RBAC Bypass Fix** — Path normalization in `middleware/rbac.py`
2. **Zoho Sync Guard** — All destructive ops scoped by org_id + env gate
3. **AI Tenant Scoping** — org_id/user_id from request.state, session org-scoped
4. **Journal Idempotency** — Application check + unique sparse index

### Previous Session
- Data integrity migration (1,172 documents fixed)
- Public route fix, JWT secret unification, compound indexes
- Comprehensive security audits

---

## Prioritized Backlog

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

## Key Files
- `/app/backend/routes/credit_notes.py` — Credit notes CRUD + PDF + journal posting
- `/app/backend/middleware/rbac.py` — RBAC with path normalization
- `/app/backend/services/double_entry_service.py` — Journal entries with idempotency
- `/app/frontend/src/components/CreditNoteModal.jsx` — Create + View modals

## Test Credentials
- Admin: `admin@battwheels.in` / `TestPass@123`
- Technician: `tech@battwheels.in` / `TestPass@123`
- Org ID: `6996dcf072ffd2a2395fee7b`
