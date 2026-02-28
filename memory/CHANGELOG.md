# Battwheels OS — Changelog

## 2026-03-01 — Sprint 4A Complete

### 4A-01: Skipped Test Audit
- Unskipped 40 tests by creating dev fixtures (platform admin, professional user, technician, starter user)
- Fixed API URL prefixes in test code (added `/api/v1/` prefix)
- Added `X-Organization-ID` headers to test requests requiring tenant context
- Unskipped 7 technician portal RBAC tests by adding `r"^/api/technician(/.*)?$"` to ROUTE_PERMISSIONS in `middleware/rbac.py`
- Fixed `test_rbac_portals.py` BASE_URL from env var to `http://localhost:8001`
- Fixed test order dependency in `test_entitlement_enforcement.py` (plan revert cleanup now runs reliably)
- **Result:** 47 of 51 skipped tests now passing. 4 remain (1 intentional, 3 deferred).

### 4A-02: Payroll Statutory Tests
- Created `tests/test_payroll_statutory.py` with 30 unit tests
- Coverage: PF wage ceiling (15000), EPS/EPF split, PF Admin/EDLI charges, ESI ceiling (21000), multi-state Professional Tax (MH, KA, GJ, TN, DL, UP)
- All 30 tests passing

### 4A-03: Dev Platform Admin
- Created `scripts/create_dev_platform_admin.py` for platform admin user
- Created `scripts/seed_dev_org.py` for organizations, subscriptions, and test users
- Users: platform-admin@battwheels.in, dev@battwheels.internal, deepak@battwheelsgarages.in, john@testcompany.com

### 4A-04: Period Lock Refactor
- Created `utils/period_lock.py` with `check_period_lock`, `enforce_period_lock`, `check_period_locked`
- Updated `services/posting_hooks.py` and `services/double_entry_service.py` to import from shared utility
- Eliminated circular dependency risk

### 4A-05: Batch Payroll Granular Keys
- Updated `services/hr_service.py` `generate_payroll` to aggregate: `pf_employer_epf`, `pf_employer_eps`, `pf_admin`, `edli`, `esi_employer`, `esi_employee`, `professional_tax`
- `post_payroll_run` now receives accurate granular statutory data
