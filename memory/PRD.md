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

## Prioritized Backlog

### P0 — Full Codebase Pattern A Audit
- Audit ALL remaining route files for Pattern A violations (contacts_enhanced, invoices_enhanced, bills_enhanced, etc.)
- Fix `log_item_history` helper to accept and include org_id

### P1 — Sprint 3 (Cursor Pagination)
- Replace H-01/H-02 hard caps with proper cursor-based pagination
- Implement cursor pagination utility
- Migrate Tier 1 list endpoints to cursor-based pagination
- Migrate Tier 2 endpoints (reports, HR, banking)

### P2 — Test Coverage
- Address 51 skipped tests by creating necessary data fixtures
- Create fixtures for Form16, starter plans, technician portal routes

### P3 — Remaining Audit Items
- Tier 2/3 query hard caps (38 queries at 5000+, 80 at 1000+)
- Medium/Low priority items from original platform audit

## Credentials
- **Dev:** dev@battwheels.internal / DevTest@123
- **Platform Admin:** platform-admin@battwheels.in / v4Nx6^3Xh&uPWwxK9HOs

## 3rd Party Integrations
- Razorpay, Resend, bleach, bcrypt
- WhatsApp integration remains MOCKED
