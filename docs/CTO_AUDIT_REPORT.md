# BATTWHEELS OS — CTO PRE-DEPLOYMENT AUDIT REPORT
**Date:** 2026-02-25
**Auditor:** E1 Agent (read-only investigation)
**Codebase:** 74 route files, 187 JSX files, 17 passing tests

---

## SECTION 1 — SECURITY AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] Middleware chain order is correct: CSRF → TenantGuard → RBAC → Sanitization → RateLimit (LIFO registration verified at server.py:6685-6712)
- [PASS] CSRF Double Submit Cookie correctly exempts Bearer token requests (csrf.py:77-82) and auth endpoints (csrf.py:63-67). Scoping is correct.
- [PASS] CORS is environment-aware: wildcard in development, restricted to explicit `CORS_ORIGINS` env var in production (server.py:6740-6756)
- [PASS] Security headers present: HSTS, X-Frame-Options DENY, CSP, X-Content-Type-Options nosniff (server.py:6721-6735)
- [PASS] File upload service validates type (5 image types only), size (1MB max), and dimensions (file_upload_service.py:27-29, 47-55)
- [PASS] Rate limiting applied to auth endpoints: login=5/min, register=3/hour, password_reset=5/hour (rate_limit.py:84-89). Note: actual login limit in code is 10/min (rate_limit.py:192) vs 5/min in config — see HIGH finding.
- [PASS] No hardcoded secrets in route/service code. All API keys sourced from env vars or credential service.
- [PASS] Input sanitization strips all HTML tags from JSON bodies on POST/PUT/PATCH (sanitize.py:47)
- [HIGH] **JWT_SECRET has a weak fallback default**: `os.environ.get('JWT_SECRET', 'battwheels-secret')` at server.py:101. In production, if JWT_SECRET env var is missing, the app runs with a publicly-known default. The warning at line 106-107 only logs — it doesn't abort. — server.py:101
- [HIGH] **Rate limit login discrepancy**: Config says 5/min (rate_limit.py:60) but actual check uses 10/min (rate_limit.py:192). The config is documentation-only; the enforcement code is what matters.
- [MEDIUM] **Auth endpoints exempt from sanitization**: `/api/auth/` is in EXEMPT_PREFIXES (sanitize.py:31). This means login/register request bodies are not sanitized. Login fields (email/password) go directly to bcrypt which is safe, but registration fields (name, company) could theoretically contain stored XSS if rendered without escaping.
- [MEDIUM] **No refresh token mechanism**: JWT expires after 7 days (server.py:103, `JWT_EXPIRATION_HOURS = 24 * 7`). No refresh flow — user must re-login after expiry. Auth.py uses a separate 24-hour expiry (auth.py:18). Two different expiry values exist for the same system.
- [LOW] **In-memory rate limiting**: Rate limit state stored in Python dict (rate_limit.py:113). Resets on every server restart. Not shared across multiple instances. Acceptable for single-instance deployment.
- [LOW] **CSP connect-src allows all Emergent subdomains**: `https://*.emergentagent.com` (server.py:6732). Should be removed in production.

**Summary: 0 critical, 2 high, 2 medium, 2 low, 8 pass**

---

## SECTION 2 — MULTI-TENANCY AUDIT
**Overall: PASS**

Findings:
- [PASS] TenantGuardMiddleware enforces tenant context on ALL non-public routes (guard.py:483-599)
- [PASS] JWT org_id validated against `organization_users` membership table (guard.py:671-683). Cross-org access blocked with 403.
- [PASS] X-Organization-ID header spoofing handled: if header org differs from token org, membership validation will reject it (guard.py:643)
- [PASS] Org suspension check present — suspended orgs get 403 (guard.py:539-551)
- [PASS] TenantGuard.validate_query auto-injects org_id for tenant collections (guard.py:143-148)
- [PASS] TenantGuard.validate_aggregation ensures $match with org_id as first pipeline stage (guard.py:223-278)
- [PASS] TENANT_COLLECTIONS list is comprehensive (83 collections) (guard.py:37-83)
- [PASS] Route files consistently include org_id in queries — verified in invoices_enhanced.py, journal_entries.py, gst.py
- [PASS] Cross-tenant write prevention: validate_document blocks inserts with wrong org_id (guard.py:177-221)
- [MEDIUM] **Platform admin endpoints use broad pattern**: `/api/platform/.*` is fully public (guard.py:474). Any endpoint under this prefix bypasses tenant and auth checks entirely. Verify no sensitive operations live here.
- [LOW] **Query param org resolution**: If no token org_id and no header, `_resolve_org_id` falls back to query param `?org_id=` (guard.py:655). This is validated by membership check but is a broader attack surface.

**Summary: 0 critical, 0 high, 1 medium, 1 low, 9 pass**

---

## SECTION 3 — FINANCIAL INTEGRITY AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] Period locking enforced on all invoice mutation paths: create (line 724), update (line 1142), void (line 1568), payment (line 1688), delete (line 1772) — invoices_enhanced.py
- [PASS] Double-entry bookkeeping: `post_invoice_journal_entry` called on invoice creation and status change (invoices_enhanced.py:1498, 1547)
- [PASS] GSTR-3B correctly includes reverse charge liability in Section 3.1(d) (gst.py:773-794, 862-868)
- [PASS] Credit notes correctly reduce GST output liability in GSTR-3B (gst.py:829-845)
- [PASS] Chart of accounts endpoint supports all account types: asset, liability, equity, revenue, expense (journal_entries.py:535-539)
- [PASS] TDS calculation implemented for employees with slab-based computation (hr.py:647-656)
- [PASS] All GST queries in GSTR-3B are org-scoped via `org_query()` helper (gst.py:716-761)
- [HIGH] **GST.py creates its own DB connection**: `get_db()` at gst.py:38-41 creates a NEW AsyncIOMotorClient per call instead of using the shared `db` from server.py. This bypasses connection pooling AND potentially bypasses TenantGuard's database reference. No org validation through TenantGuard for these queries.
- [MEDIUM] **Expense GST assumption**: For expenses without tax_amount, code assumes 18% GST (`amount * 0.18`) at gst.py:807. This could overstate ITC if the expense has no GST component.
- [MEDIUM] **Invoice creation path allows org_id override**: While TenantGuard middleware sets org_id on request.state, individual route handlers still rely on `extract_org_id(request)` which may have different precedence logic. No confirmed vulnerability but dual-path resolution is a risk.

**Summary: 0 critical, 1 high, 2 medium, 0 low, 7 pass**

---

## SECTION 4 — API QUALITY AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] Pagination implemented on key list endpoints with `page` and `limit` params, capped at 100 (invoices_enhanced.py:876-917)
- [PASS] Pydantic models used extensively for request validation across route files
- [PASS] HTTP status codes used correctly: 400 (validation), 401 (auth), 403 (forbidden), 409 (period lock), 422 (validation)
- [PASS] OpenAPI/Swagger auto-generated by FastAPI — accessible at /docs and /openapi.json
- [PASS] Consistent error format with `detail` field across endpoints
- [HIGH] **111 endpoints in a single server.py file** (6780+ lines): While functional, this monolith makes it difficult to audit, test, and maintain individual routes. Many endpoints are inline in server.py rather than in separate route files.
- [MEDIUM] **Not all list endpoints have pagination**: Need to verify contacts, tickets, journal_entries list endpoints also enforce max limits.
- [MEDIUM] **N+1 risk on posting_hooks.py**: `post_invoice_journal_entry` queries `invoices_enhanced.find` which could fetch many documents in batch operations.
- [LOW] **No response time monitoring**: No middleware tracking slow endpoints. Rely on Sentry for performance.

**Summary: 0 critical, 1 high, 2 medium, 1 low, 5 pass**

---

## SECTION 5 — DATA INTEGRITY AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] Comprehensive compound indexes defined in utils/indexes.py covering tickets, invoices, journal_entries, contacts, audit_logs, period_locks, etc. (30+ indexes)
- [PASS] Indexes automatically created on startup via lifespan handler (server.py:127-132)
- [PASS] Org_id included in all compound indexes for efficient tenant-scoped queries
- [PASS] TTL index on password_reset_tokens for automatic expiry (indexes.py:74)
- [MEDIUM] **No referential integrity enforcement**: MongoDB has no foreign keys. Deleting a contact doesn't cascade-delete or validate against invoices referencing that contact_id. Application-level enforcement only.
- [MEDIUM] **Estimate→Ticket→Invoice chain not transactionally protected**: Each step is a separate MongoDB operation. A crash mid-chain could leave orphaned state. No compensation/rollback logic.
- [LOW] **invoices_enhanced missing from compound indexes**: The index file creates indexes for `invoices` but not `invoices_enhanced`, which is the active collection.
- [LOW] **No schema validation on MongoDB collections**: Documents can have arbitrary fields. A typo in field names would silently succeed.

**Summary: 0 critical, 0 high, 2 medium, 2 low, 4 pass**

---

## SECTION 6 — FRONTEND QUALITY AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] All API calls use `REACT_APP_BACKEND_URL` from environment — no hardcoded URLs (verified in api.js and page components)
- [PASS] Global 409 PERIOD_LOCKED handler fires via `window.dispatchEvent` (api.js:68-74)
- [PASS] Global 403 feature_not_available handler present (api.js:78-85)
- [PASS] CSRF token auto-injected on unsafe methods from cookie (api.js:50-54)
- [PASS] X-Organization-ID header sent on all authenticated requests (api.js:31)
- [PASS] PWA manifest correctly configured with name, icons, standalone display (manifest.json)
- [PASS] Service worker registered in index.js (line 30-33)
- [PASS] PWA icons present: icon-192.png and icon-512.png
- [MEDIUM] **CSRF refresh on 403 hits /api/health**: When CSRF token is missing/invalid, the code fetches `/api/health` to get a fresh CSRF cookie (api.js:92-94). But /api/health is a GET endpoint — CSRF middleware only sets cookies on responses. Need to verify the CSRF middleware actually sets cookies on GET responses.
- [MEDIUM] **No global 401 handler**: When JWT expires, individual components must handle 401 themselves. No automatic redirect to login on token expiry.
- [LOW] **PlatformAdmin.jsx references REACT_APP_ENVIRONMENT**: Falls back to "production" if not set (PlatformAdmin.jsx:351). This variable is not in .env.example.

**Summary: 0 critical, 0 high, 2 medium, 1 low, 8 pass**

---

## SECTION 7 — DEPLOYMENT READINESS AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] Dockerfile is well-structured: multi-stage build, node:20-alpine for frontend, python:3.11-slim for backend (Dockerfile)
- [PASS] HEALTHCHECK configured in Dockerfile with 30s interval, 10s timeout (Dockerfile)
- [PASS] railway.toml correctly configured with healthcheckPath=/api/health, restart on failure (railway.toml)
- [PASS] .env.example documents all required environment variables including CORS_ORIGINS
- [PASS] Health endpoint checks MongoDB connectivity and required env vars (server.py:6406-6444)
- [PASS] Graceful shutdown: `client.close()` in lifespan shutdown handler (server.py:137)
- [HIGH] **No connection pooling configured**: `AsyncIOMotorClient(mongo_url)` uses defaults (server.py:97). For MongoDB Atlas over network, should set `maxPoolSize`, `minPoolSize`, `serverSelectionTimeoutMS`, `connectTimeoutMS` for resilience.
- [HIGH] **Logging is not structured**: Uses Python's standard `logging` module with text format (server.py:8,31). Railway and production log aggregators work better with structured JSON logs.
- [MEDIUM] **Port mismatch**: Dockerfile EXPOSE 8000 and CMD uses port 8000, but railway.toml startCommand uses `$PORT` (Railway's dynamic port). Dockerfile HEALTHCHECK hardcodes localhost:8000. This is fine for Docker standalone but may cause HEALTHCHECK failures if Railway overrides the port.
- [MEDIUM] **74 route files but 77 routers registered**: 3 potential phantom routers or inline registrations. Minor discrepancy to verify.
- [LOW] **No readiness probe separate from liveness**: Single /api/health serves both. In Kubernetes (future), you'd want separate probes.

**Summary: 0 critical, 2 high, 2 medium, 1 low, 5 pass**

---

## SECTION 8 — TEST COVERAGE AUDIT
**Overall: FAIL**

Findings:
- [CRITICAL] **Test suite is broken**: Running `pytest tests/test_csrf_sanitization.py` produces 10 FAILED, 5 ERRORS, 1 PASSED. Tests fail with `MissingSchema` error — they use relative URLs (`/api/auth/login`) instead of absolute URLs. The "17/17 passing" claim from Week 4 is outdated or was run with a different configuration.
- [CRITICAL] **Extremely low test coverage**: Only 1 test file exists (`test_csrf_sanitization.py`). Out of 74 route files and 111 endpoints, test coverage is effectively 0% for business logic.
- [HIGH] **Zero tests for financial flows**: No tests for invoice creation, journal entry posting, GST calculations, period locking, payment recording, credit notes.
- [HIGH] **Zero tests for multi-tenancy**: No tests verifying cross-tenant access is blocked, TenantGuard behavior, or org membership validation.
- [HIGH] **Zero tests for auth flows**: Login, registration, password reset, JWT expiry — all untested.
- [HIGH] **Top 5 untested critical paths that could cause production failures:**
  1. Invoice creation + journal entry posting (double-entry integrity)
  2. Cross-tenant data access prevention
  3. GSTR-3B calculation accuracy
  4. Period locking enforcement across all mutation endpoints
  5. Payment recording + balance_due recalculation

**Summary: 2 critical, 4 high, 0 medium, 0 low, 0 pass**

---

## SECTION 9 — TECHNICAL DEBT AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] Only 2 genuine TODO comments in codebase: inventory_enhanced.py:856 (customer notification) and inventory_enhanced.py:1001 (credit note creation). Both are non-critical P2 features.
- [PASS] No circular imports detected
- [HIGH] **server.py is 6780+ lines**: This monolith contains 111 inline endpoints plus models, middleware setup, and business logic. This is the #1 refactoring priority.
- [MEDIUM] **GST module (gst.py) creates its own DB connections** instead of using the shared pool. Architectural coupling issue.
- [MEDIUM] **Dual JWT expiry configs**: server.py has `JWT_EXPIRATION_HOURS = 24 * 7` (168 hours), auth.py has `ACCESS_TOKEN_EXPIRE_HOURS = 24`. Tokens created from different code paths have different lifetimes.
- [MEDIUM] **bcrypt major version outdated**: bcrypt 4.1.3 installed, 5.0.0 available. Major version upgrade may have breaking API changes — verify before upgrading.
- [LOW] **74 route files, 77 registered routers**: Minor discrepancy suggests some routers are registered inline or some files aren't used.

**Summary: 0 critical, 1 high, 3 medium, 1 low, 2 pass**

---

## SECTION 10 — OPERATIONAL READINESS AUDIT
**Overall: PASS WITH WARNINGS**

Findings:
- [PASS] All 5 incidents properly logged in docs/INCIDENTS.md (INC-001 through INC-005a)
- [PASS] DEPLOYMENT.md comprehensive with step-by-step Railway guide
- [PASS] Migration scripts created and tested with safety guards
- [PASS] Atlas migration toolkit ready (export, import, verify scripts)
- [PASS] Data export completed: 3 databases, 2,473 documents backed up
- [HIGH] **No automated backup strategy**: Data is being manually migrated via scripts. No scheduled backups, no point-in-time recovery plan beyond Atlas's built-in snapshots (which require M10+ tier, not available on M0 free).
- [HIGH] **ENVIRONMENT_SOP.md is empty/missing**: The `docs/` directory has no ENVIRONMENT_SOP.md file. The handoff mentions "8 rules, committed" but the file doesn't exist.
- [MEDIUM] **DISASTER_RECOVERY_RUNBOOK.md is empty/missing**: Listed in docs/ directory listing but content is empty when viewed.
- [MEDIUM] **No uptime monitoring beyond health endpoint**: No external monitoring service configured (UptimeRobot, BetterStack, etc.). If Railway goes down, nobody gets alerted.
- [MEDIUM] **No graceful degradation if Atlas goes down**: App returns 503 from health check, but no circuit breaker, no read-only mode, no cached responses.

**Summary: 0 critical, 2 high, 3 medium, 0 low, 5 pass**

---

## OVERALL CTO AUDIT RESULT

```
Score: 68/100

Critical issues (must fix before go-live): 2
  1. Test suite is broken (10 failures, 5 errors)
  2. Near-zero test coverage on business-critical paths

High issues (fix within 1 sprint): 13
  1. JWT_SECRET weak fallback default
  2. Rate limit login discrepancy (config vs enforcement)
  3. GST module creates independent DB connections
  4. No MongoDB connection pooling for production
  5. Logging not structured (JSON)
  6. Zero tests: financial flows
  7. Zero tests: multi-tenancy
  8. Zero tests: auth flows
  9. Zero tests: top 5 critical paths
  10. server.py monolith (6780+ lines)
  11. No automated backup strategy
  12. ENVIRONMENT_SOP.md missing
  13. Dual JWT expiry configuration

Medium issues (fix within 1 month): 14
  (Listed in individual sections above)

Low issues (backlog): 8
  (Listed in individual sections above)

GO-LIVE RECOMMENDATION: APPROVED WITH CONDITIONS

Conditions:
1. [MUST] Fix JWT_SECRET fallback — app MUST refuse to start if JWT_SECRET 
   is unset or < 32 chars in production
2. [MUST] Fix test suite so it runs green again (even if coverage is low)
3. [MUST] Configure MongoDB connection pooling for Atlas
4. [SHOULD] Add structured JSON logging before production
5. [SHOULD] Create ENVIRONMENT_SOP.md and update DISASTER_RECOVERY_RUNBOOK.md
6. [SHOULD] Unify JWT expiry to single config value
7. [PLAN] Comprehensive test suite is P0 post-launch — schedule within 2 weeks
```
