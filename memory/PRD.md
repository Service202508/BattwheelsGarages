# Battwheels OS — Product Requirements Document

## Original Problem Statement
Full-stack ERP/SaaS platform for Battwheels (electric vehicle service business). Multi-tenant architecture with FastAPI backend, React frontend, MongoDB database.

## Platform Architecture
- **Backend:** FastAPI (Python 3.11) on port 8001
- **Frontend:** React on port 3000
- **Database:** MongoDB (battwheels_dev for development)
- **Auth:** JWT-based, multi-tenant with org_id scoping
- **Integrations:** Razorpay (test mode), Resend, Zoho, Sentry, Emergent LLM

## Completed Phases

### Phase 0 — Surgical Cleanup Sprint (2026-02-28)
All 6 items completed:
1. Fixed broken employee password reset endpoint
2. Verified CSRF middleware (pre-existing, added 6 tests)
3. Verified GSTR-3B RCM handling (pre-existing, added 4 tests)
4. Fixed input sanitization middleware (password exemption bug)
5. Resolved duplicate TechnicianProductivity.jsx naming
6. Removed vestigial STRIPE_API_KEY and dead code

### Phase 0.5 — Test Infrastructure Triage (2026-02-28)
Complete 5-step triage of 132 test files:
- **Core suite expanded:** 25 → 33 files, 429 → 542 passing tests (+26.3%)
- **8 files promoted to core:** csrf_middleware, gstr3b_rcm, calculations_regression, sanitization_middleware, efi_guidance, knowledge_brain, sprint_6c_cursor_pagination, sprint_6b_knowledge_pipeline
- **6 files archived as duplicates** (Bucket B → backend/tests/archive/duplicate/)
- **18 files archived as sprint artifacts** (Bucket C → backend/tests/archive/sprint_history/)
- **76 files documented in TEST_DEBT_REGISTER.md** (Bucket A, MODERATE effort)
- **Production verified:** verify_prod_org.py 6/6 PASS, ALL GREEN

### Phase 2C — Financial Test Coverage & Security (2026-02-28)
- Added comprehensive tests for Invoices, Credit Notes, Accounting, GST (71 new tests)
- Fixed CORS vulnerability and implemented login rate-limiting
- Migrated Invoices and JournalEntries frontend to cursor pagination
- Core test suite: **693 passed, 19 skipped, 0 failed**

### Security — Git History Secret Scrub (2026-03-01)
- Removed `backend/.env` and `frontend/.env` from all 4,354 commits using `git-filter-repo`
- Scrubbed 11 secret values from docs/code files (EMERGENT_LLM_KEY, JWT_SECRET, ZOHO creds, RESEND_API_KEY, SENTRY_DSN)
- Cleaned duplicate entries from `.gitignore`
- Verified: 0 secrets remain in git history, application healthy post-rewrite
- **Status: READY FOR GITHUB PUSH**

## Current Health
- Core test suite: **693 passed, 19 skipped, 0 failed**
- Production: **ALL GREEN** (verify_prod_org.py)
- Razorpay: Test mode only
- Git history: **CLEAN** — no secrets in any commit

## Prioritized Backlog

### P0 (Critical)
- Push cleaned repository to GitHub

### P1 (High)
- Frontend migration to server-side cursor pagination (5 endpoints)
- Address remaining platform audit findings (UI/UX inconsistencies, pattern violations)
- Provide LIVE Razorpay keys (User Action)

### P2 (Medium)
- Fix near-passing Bucket A test files (5 files with 1-3 failures each)
- Create shared conftest.py with login fixture for "no auth" test files (24 files)
- Unskip remaining 14 tests in core suite (webhooks, Form16, Razorpay)
- Fix Pattern A violations (queries without org_id filters)

### P3 (Low)
- Implement proper background task runner (Celery)
- Migrate hybrid EFI embeddings to true embedding model
- Add frontend automated tests
- Clean up hardcoded off-theme colors/inline styles
- Remediate remaining 76 Bucket A test files per TEST_DEBT_REGISTER.md

## Key Documents
- `/app/ENVIRONMENT_SOP.md` — Environment safety rules
- `/app/docs/TEST_DEBT_REGISTER.md` — 76 remaining test files with fix guidance
- `/app/docs/TEST_TRIAGE_STEP2.md` — Full classification of all 107 excluded files
- `/app/docs/TEST_TRIAGE_STEP3.md` — Detailed Bucket A analysis with test function lists
- `/app/docs/TEST_TRIAGE_SECTION_F.md` — Triage reflections and uncertainties
- `/app/scripts/run_core_tests.sh` — Core test suite (33 files)
- `/app/scripts/verify_prod_org.py` — Production health check

## Key Credentials (Dev Environment)
- Dev user: `dev@battwheels.internal` / `DevTest@123` (role: owner)
- Platform admin: `platform-admin@battwheels.in` / `DevTest@123`
- Demo user: `demo@voltmotors.in` / `Demo@12345`
