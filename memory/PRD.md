# Battwheels OS — Product Requirements Document

## Original Problem Statement
Comprehensive security audit and hardening of the Battwheels OS multi-tenant ERP platform. Primary focus: eliminate cross-tenant data leaks (Pattern A violations) and enforce secrets management.

## Core Requirements
1. **Multi-Tenancy Data Isolation (Pattern A):** Every DB query accessing tenant-specific data MUST be filtered by `organization_id`.
2. **Secrets Management:** No production secrets in version control.
3. **Defense-in-Depth:** Validation guards at both route and service layers.
4. **Centralized Guards:** `require_org_id` utility for route layer; `ValueError` guards for service layer.

## What's Been Implemented

### Phase 1: Route-Layer Hardening (COMPLETE)
- Created `require_org_id` in `utils/database.py`
- Replaced ~383 vulnerable `extract_org_id` calls across 28 route files
- All route endpoints now raise 403 on missing org context

### Phase 2: Secrets Management (COMPLETE)
- Scrubbed all production secrets from `backend/.env`
- Created `backend/.env.example` template
- Removed hardcoded passwords from seed scripts

### Phase 3: Service-Layer Hardening (IN PROGRESS)
- **`double_entry_service.py`** — COMPLETE: 1 critical cross-tenant write fix + 16 defense-in-depth guards
- **`reports_advanced.py`** — COMPLETE: 13 endpoints hardened
- **`master_data.py`** — COMPLETE: queries classified as org-scoped vs platform-global
- **`hr_service.py`** — COMPLETE (2025-02-XX): 23 tenant-scoped queries secured, 12 defense-in-depth guards added, 84 insertions / 76 deletions. Critical fixes: leave_requests missing org_id, generate_payroll processing all orgs' employees.

## Prioritized Backlog

### P0 (Critical)
- [x] Route-layer hardening (383 calls)
- [x] Secrets management
- [x] `double_entry_service.py`
- [x] `hr_service.py`
- [ ] Update route-layer callers for new `hr_service.py` signatures (breaking change by design)

### P1 (High)
- [ ] Audit & fix `ticket_service.py`
- [ ] Audit & fix `ticket_estimate_service.py`
- [ ] Audit `scheduler.py` for org_id bypass

### P2 (Medium)
- [ ] Audit all remaining service files from CTO audit
- [ ] Purge secrets from Git history (BFG Repo-Cleaner)
- [ ] Verify production deployment pipeline
- [ ] Deploy security fixes

### P3 (Low)
- [ ] Fix backend test suite (550 passed, 621 failed, 825 skipped, 436 errors)

## Architecture
- Backend: FastAPI + MongoDB (battwheels_dev)
- Frontend: React
- Multi-tenancy: organization_id-based row-level filtering
- Security pattern: `require_org_id` (routes) + `ValueError` guards (services)
