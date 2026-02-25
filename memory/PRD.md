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

### Week 1 Remediation — Day 4: C-05 Audit Logging (2026-02-25) — VERIFIED 13/13
- **Utility:** `utils/audit_log.py` — `log_financial_action()` with full schema
- **Schema:** org_id, user_id, user_role, action (CREATE/UPDATE/VOID/DELETE), entity_type, entity_id, timestamp (UTC), ip_address, before_snapshot, after_snapshot
- **Mutation points covered:**
  - Invoice CREATE/UPDATE/VOID (`routes/invoices_enhanced.py`)
  - Payment CREATE (`routes/invoices_enhanced.py`)
  - Credit Note CREATE (`routes/credit_notes.py`)
  - Journal Entry CREATE (`services/double_entry_service.py`)
- **before_snapshot:** null for CREATE, full document for UPDATE/VOID
- **IP extraction:** From X-Forwarded-For (K8s ingress) or direct client

### Week 1 Remediation — Day 3: C-06 GSTR Credit Note Inclusion (2026-02-25) — VERIFIED 15/15 + Staging
- **Root bug:** All 6 `org_query(request, ...)` calls in `gst.py` passed Request object instead of org_id string — BSON serialization failure, complete tenant scoping bypass
- **Fix:** `org_query(org_id, ...)` in all 8 GSTR-1 + GSTR-3B queries; added `org_id = extract_org_id(request)` to GSTR-3B function; org-scoped bills/expenses queries
- **Credit note logic validated:** CN subtotals reduce section_3_1 taxable_value; CGST/SGST/IGST adjusted separately; partial CNs deduct only CN amount; cross-period CNs treated by CN date
- **Staging validation:** Two separate orgs ran without error, figures differ per org, no cross-org contamination

### Week 1 Remediation — Days 1-2 (2026-02-25)
- **C-01:** JWT secret unification + bcrypt password hashing
- **C-04:** Dead tenant middleware tombstoned
- **C-02:** Route scoping audit — fixed banking_module.py, data_integrity.py, seed_utility.py

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

### P0 (Week 1 Remaining)
- **Day 5: C-03 Period Locking** — Design document delivered at `/app/docs/PERIOD_LOCKING_DESIGN.md`. No code. Awaiting user confirmation.

### P0 (Week 2)
- **H-NEW-01 (HIGH):** `organization_settings.find_one({})` in `gst.py` line 715 — unscoped, returns first org's settings. Must scope by org_id.
- **H-01:** Banking module cross-tenant — partially fixed, needs full verification

### P1
- HIGH severity audit findings (broken estimate-to-invoice chain, etc.)
- **M-NEW-01 (MEDIUM):** No reverse-charge filtering in GSTR-3B outward liability

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
- `/app/backend/utils/audit_log.py` — Financial audit logging utility
- `/app/backend/routes/gst.py` — GSTR-1 and GSTR-3B with credit note inclusion (C-06 fix)
- `/app/backend/routes/credit_notes.py` — Credit notes CRUD + PDF + journal posting
- `/app/backend/routes/invoices_enhanced.py` — Invoice CRUD with audit logging
- `/app/backend/middleware/rbac.py` — RBAC with path normalization
- `/app/backend/services/double_entry_service.py` — Journal entries with idempotency + audit logging
- `/app/frontend/src/components/CreditNoteModal.jsx` — Create + View modals
- `/app/FINDINGS_TRACKER.md` — Active findings from Week 1 remediation

## Test Credentials
- Admin: `admin@battwheels.in` / `Admin@12345`
- Org ID: `6996dcf072ffd2a2395fee7b`
