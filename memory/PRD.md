# Battwheels OS — Product Requirements Document

## Original Problem Statement
Battwheels OS is a multi-tenant SaaS ERP platform for EV service businesses. The platform manages tickets, invoices, contacts, inventory, estimates, HR, banking, GST compliance, and more across three environments (dev/staging/production).

## Core Architecture
- **Backend:** FastAPI + MongoDB (motor) with multi-tenant isolation via `organization_id`
- **Frontend:** React with Shadcn/UI components
- **Databases:** battwheels_dev (development), battwheels_staging (staging), battwheels (production)
- **Auth:** JWT-based with role-based access control (RBAC)

## Key Documents
- `/app/ENVIRONMENT_SOP.md` — Three-environment discipline rules
- `/app/CODING_STANDARDS.md` — Multi-tenancy & data integrity rules (Pattern A/B/C)

## What's Been Implemented

### Production Reset & Verification (2026-02-27)
- Production and staging databases wiped clean (only platform-admin user + seed data)
- Password sanitization bug fixed (bleach.clean corrupting special characters)
- Login response password field leak patched
- `scripts/verify_prod_org.py` updated for SaaS architecture (0 orgs = PASS)
- Full test suite verified: 322 passed, 0 failed, 51 skipped

### H-01/H-02 Hard Cap Sprint (2026-02-27)
- **H-01:** All 11 completely unbounded queries (`.to_list(None)`) capped to 1000
  - services/fault_tree_import.py (1 query)
  - services/embedding_service.py (2 queries)
  - services/efi_embedding_service.py (4 queries)
  - services/data_sanitization_service.py (4 queries)
- **H-02:** 10 Tier 1 customer-facing queries capped from 10000 to 500
  - routes/contact_integration.py (3 queries)
  - routes/items_enhanced.py (7 queries)
- Export endpoints deliberately NOT touched (per instructions)

### Pattern A Remediation — items_enhanced.py (2026-02-27)
- **66 total violations fixed** across all 70 endpoints in items_enhanced.py
- Original 30 READ violations + 36 additional WRITE/CRUD violations discovered
- Every endpoint now includes `request: Request` param + `org_id = extract_org_id(request)`
- All queries include `"organization_id": org_id` in filters
- All inserts include `"organization_id": org_id` in documents
- 2 body param renames (BulkItemPriceSet, BulkActionRequest) to avoid Request naming conflict
- Automated scan confirms ZERO remaining violations
- Test suite: 322 passed, 0 failed, 51 skipped (no regressions)
- Production verified: ALL GREEN (6/6 PASS)

**Known gap:** `log_item_history` helper inserts history without org_id (requires signature change across callers)

### Full Codebase Audit — COMPLETED (2026-02-28)
- Comprehensive A-through-N audit completed with file:line citations
- Output: `/app/docs/REMEDIATION_AUDIT_2026.md` (1464 lines, 59 file citations, 641 table rows)
- Findings: 8 P0, 22 P1, 19 P2 items cataloged
- Key discoveries:
  - P0: 20 route files bypass RBAC (all `-enhanced` routes unmapped in ROUTE_PERMISSIONS)
  - P0: 5 services with ZERO tenant isolation (efi_decision_engine, efi_embedding_service, embedding_service, event_processor, scheduler)
  - P0: 11 EFI collections missing from TenantGuard TENANT_COLLECTIONS
  - P0: Professional Tax hardcoded flat ₹200 for all states
  - P1: Workflow chain broken at Steps 4→5 and 5→6

## Prioritized Backlog (Updated from Audit)

### P0 — Critical (Must Fix Before Production)
- P0-01: EFI Decision Engine — zero tenant isolation (services/efi_decision_engine.py)
- P0-02: EFI Embedding Service — zero tenant isolation (services/efi_embedding_service.py)
- P0-03: Embedding Service — zero tenant isolation (services/embedding_service.py)
- P0-04: Professional Tax hardcoded flat ₹200 for all states (services/hr_service.py)
- P0-05: ESI employer contribution not calculated correctly (services/hr_service.py)
- P0-06: 9 EFI collections missing from TenantGuard TENANT_COLLECTIONS (core/tenant/guard.py)

### P1 — High Priority
- P1-01: log_item_history missing org_id in inserted docs (routes/items_enhanced.py:2827)
- P1-02: org_query silently drops org_id when null (utils/database.py:29)
- P1-03: Notification service — no org_id (services/notification_service.py)
- P1-04: 32+ queries with .to_list(5000-10000) remaining
- P1-05: No period lock enforcement on journal entry creation
- P1-06: PF ceiling not enforced (₹15,000 basic cap)
- P1-07-08: GSTR-1/3B compliance gaps
- P1-09: No fiscal year concept in accounting
- P1-10: RBAC fallthrough for unmapped routes
- P1-11: Workflow chain broken at Steps 4→5 and 5→6
- P1-12-17: Additional tenant isolation gaps in services

### P2 — Medium Priority / Backlog
- Cursor-based pagination to replace all hard caps
- 51 skipped tests need data fixtures
- CSRF secure flag, rate limiting in-memory
- Multiple mocked email/notification features
- Payroll statutory gaps (HRA exemption, 80C/80D, gratuity, bonus)
- GST gaps (e-Way bill, GSTR-2A/2B, annual return)
- Projects module skeleton needs expansion

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / v4Nx6^3Xh&uPWwxK9HOs

## 3rd Party Integrations
- Razorpay, Resend, bleach, bcrypt
- WhatsApp integration remains MOCKED
