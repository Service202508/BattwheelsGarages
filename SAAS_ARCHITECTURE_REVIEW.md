━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BATTWHEELS OS
ENTERPRISE SaaS ARCHITECTURE REVIEW
Principal Architect Assessment
Date: February 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## EXECUTIVE VERDICT

**SaaS Architecture Maturity: 2.5/5**
- 1 = Single-tenant app with org field
- 2 = Basic multi-tenant, manual ops
- 3 = Proper multi-tenant, limited platform layer
- 4 = Enterprise SaaS, missing advanced features
- 5 = Zoho/Salesforce grade

**Current Level: 2.5/5**
**Target for Enterprise Sales: 4/5**
**Gap to Target: ~18 months of focused engineering**

**Verdict:**
Battwheels OS is a technically ambitious, well-intentioned platform that has made a genuine effort at multi-tenancy — the right architectural concepts (TenantContextManager, TenantGuardMiddleware, EntitlementService, RBACMiddleware, OrganizationUser memberships, subscription plan models) are present in the codebase. However, the platform suffers from a critical and pervasive problem: the security infrastructure is built in the `core/` layer but is inconsistently applied across the older monolithic `server.py` routes and several business-logic route files. More seriously, there is **zero platform-owner layer** — Battwheels (the SaaS company) has no mechanism to view, manage, suspend, or bill its tenants from a central dashboard. This is not just a missing feature; it means the SaaS business model itself is not technically operational. Before this can be sold as enterprise SaaS to even a mid-market customer, a platform admin layer must be built, entitlement enforcement must be API-level (not just UI-level), and the ~15 unscoped routes in server.py must be patched. The good news: the foundation is correct. The framework is there. The gaps are engineering effort, not architectural re-design.

---

## SCORECARD

| Dimension                          | Score | Grade |
|------------------------------------|-------|-------|
| Multi-Tenancy Foundation           |  5/10 | C+    |
| Organisation Architecture          |  6/10 | B-    |
| User and Role Architecture         |  5/10 | C+    |
| Portal Architecture                |  7/10 | B     |
| Platform Owner Layer               |  0/10 | F     |
| API and Integration Architecture   |  3/10 | D     |
| Database Architecture              |  6/10 | B-    |
| Security Architecture              |  5/10 | C+    |
| Operational Architecture           |  4/10 | C     |
| Enterprise Readiness               |  3/10 | D     |
| **TOTAL**                          |**44/100**| **D+** |

---

## DIMENSION FINDINGS

---

### DIMENSION 1 — MULTI-TENANCY FOUNDATION (5/10)

#### 1.1 Isolation Model

**Strategy: Row-level isolation using `organization_id` on every document.**

This is the correct strategy for a shared-infrastructure SaaS at this scale. The intent is clear and the architecture documents it properly. However, the implementation is **inconsistent** across the codebase.

The `core/tenant/guard.py` defines a `TENANT_COLLECTIONS` set listing ~60 collections that must have `organization_id`. The `TenantGuardMiddleware` validates the JWT and sets `request.state.tenant_org_id`. The `scope_query()` and `scope_document()` helpers are available.

**CRITICAL FINDING — Collections/Routes Missing Org Scoping:**

The monolithic `server.py` contains the original pre-refactor routes. These routes were written before the multi-tenant layer was built and have **not been retrofitted**.

Evidence from `server.py`:

```python
# Line 1466 — get_users() — Returns ALL users across ALL orgs
@api_router.get("/users")
async def get_users(request: Request):
    await require_admin(request)
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users  # NO organization_id FILTER

# Lines 1801-1808 — get_allocations() — Returns ALL allocations globally
@api_router.get("/allocations")
async def get_allocations(request: Request, ticket_id: Optional[str] = None):
    await require_auth(request)
    query = {}  # EMPTY QUERY — NO TENANT SCOPING
    if ticket_id:
        query["ticket_id"] = ticket_id
    allocations = await db.allocations.find(query, {"_id": 0}).to_list(1000)
    return allocations  # DATA LEAK — returns all orgs' allocations

# Lines 1751 — create_allocation() — Verifies ticket without org check
    item = await db.inventory.find_one({"item_id": data.item_id}, {"_id": 0})  # No org_id
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})  # No org_id
```

`contact_integration.py` performs bulk queries across collections without `organization_id` filters on several endpoints. Example (line 453): `legacy_contacts = await db["contacts"].find({}, {"_id": 0}).to_list(10000)` — returns all contacts from all organizations.

`reports_advanced.py` (line 189): `invoices = await invoices_collection.find(...)` — filters by `org_id` only if the context provides it, with a conditional fallback that queries all orgs.

The `failure_intelligence.py` model definition has **no `organization_id` field** — failure cards appear to be global/shared data which may be intentional for cross-org AI learning but represents a design decision that needs explicit documentation.

**Partially mitigated by:** The `TenantGuardMiddleware` blocks unauthenticated requests and validates org membership, so an attacker must be an authenticated member of *some* org. But a low-privilege user at Org A can call `/api/allocations` and receive all allocations from every organization on the platform — this is a **cross-tenant data leak**.

#### 1.2 Query-Level Enforcement

The middleware architecture correctly delegates to the `scope_query()` helper, but enforcement is **opt-in at the route handler level, not enforced at the query level.** There is no database query interceptor.

The newer modules (invoices_enhanced, items_enhanced, contacts_enhanced, estimates_enhanced) use `ctx.scope_query()` consistently. The older routes in `server.py` do not. This creates a two-tier system where the security of each endpoint depends on which era it was written in.

**RBAC Middleware has a dangerous fallback:**
```python
# middleware/rbac.py — Line 256-258
if allowed_roles is None:
    # Route not in permissions map - allow authenticated users
    logger.info(f"RBAC: Route {path} not in map, allowing {user_role}")
    return await call_next(request)  # PASSES THROUGH
```
Any route not listed in `ROUTE_PERMISSIONS` is accessible to any authenticated user regardless of role. Given the large number of routes in this application, this is a significant gap.

#### 1.3 Tenant Context Propagation

**Propagation chain is well-designed:**
1. JWT contains `org_id` (most trusted — set at login/switch)
2. `X-Organization-ID` header (validated against membership)
3. `org_id` query param (validated against membership)
4. User's first active org (fallback)

**Validation before use: YES.** Even if a user sends a fake `X-Organization-ID` header, `_validate_membership()` in `TenantIsolationMiddleware` runs a database check before allowing access. This is correct.

**However:** The `require_auth()` helper in `server.py` (and `utils/auth.py`) does not validate org membership — it only checks if the JWT is valid. Many older routes call `require_auth()` or `require_admin()` (defined in server.py) instead of using the `tenant_context_required` dependency. This means those routes are auth-protected but not org-scoped.

#### 1.4 Cross-Tenant Data Leak Analysis

- **In-memory shared state:** The module-level `_context_manager` singleton in `context.py` has a `_permission_cache` and `_org_cache` dict that is shared across all requests. This is intentional for performance but carries risk if cache keys are not strictly namespaced.
- **File uploads:** `/app/uploads/` stores files without visible org-scoped subdirectory structure. A file uploaded by Org A could potentially be accessed by Org B if the URL is guessable.
- **Background jobs:** The `scheduler.py` and `sla.py` background jobs need independent investigation for org scoping. The SLA breach job queries all tickets that have breached — needs verification of org_id scoping.
- **EFI failure cards:** Designed as global/shared knowledge base (no `organization_id`). This is a deliberate choice for AI cross-pollination but must be documented as a policy exception, not a gap.

#### 1.5 Tenant Onboarding Completeness

**`POST /api/organizations/signup` provisions:**
- Organization record ✅
- Admin user account ✅
- Organization membership (owner role) ✅
- Starter plan subscription (14-day trial) ✅
- RBAC role initialization ✅

**NOT provisioned automatically:**
- Default Chart of Accounts ❌
- Default SLA configuration ❌
- Default invoice numbering sequences ❌
- Default expense categories ❌
- Seed/demo data ❌
- Email verification (flag exists but not enforced) ⚠️

The `is_onboarded` flag exists but the setup wizard (`/setup` route) depends on the user manually completing it. Time to "fully functional" is 5-10 minutes if the user understands what to configure. No guided onboarding automation for accounting setup.

---

### DIMENSION 2 — ORGANISATION ARCHITECTURE (6/10)

#### 2.1 Organisation Data Model

**Present fields:** name, slug, industry_type, plan_type, logo_url, website, email, phone, address, city, state, country, pincode, gstin, is_active, org_type (internal/customer/partner/demo), branding settings (per-org — GOOD).

**Settings sub-document includes:** currency, timezone, date_format, fiscal_year_start, SLA settings, inventory settings, invoice settings (prefix, GST, payment terms), notification settings.

**Missing GST-compliance fields:** PAN number field is absent from the org model (employees have PAN but org itself does not).

**Critical missing per-org configurations:**
- SMTP/email config per org — global Resend key only
- Razorpay per-org config — single `.env` key for all orgs
- E-Invoice IRP credentials per org — single `.env` key
- Custom domain support — not present

This means the platform cannot yet serve multiple independent garages with separate payment collection, separate email from-addresses, or separate GST e-invoice configurations. This is a **hard blocker for multi-tenant B2B billing**.

#### 2.2 Subscription and Module Control

**Model quality: EXCELLENT.** The `SubscriptionService`, `EntitlementService`, and `PlanFeatures` models are properly designed with 28 granular feature flags across 4 plans.

**Critical Gap: Entitlement enforcement is NOT applied on API routes.**

The `require_feature()` FastAPI dependency exists in `core/subscriptions/entitlement.py`. It is almost never used in actual route definitions. For example, the HR/payroll routes in `server.py` (payroll is an Enterprise feature) are accessible to organizations on the Free plan — the middleware only checks the user's role (`require_admin`), not whether their org's subscription includes payroll.

Evidence:
```python
# server.py — create_payroll_record — no feature gate
@api_router.post("/hr/payroll")
async def create_payroll_entry(data: PayrollRecord, request: Request):
    await require_admin(request)  # Only checks role, not plan
```

This means the entitlement system is largely decorative — plans are defined but not enforced at the API layer. A Free plan organization could theoretically call all Enterprise-tier APIs if they know the endpoint URL.

**Platform owner cannot:**
- Onboard new tenants (no admin API)
- Suspend tenants (no admin API — only `is_active` field exists)
- Change tenant plans (no admin API)
- View all tenants (no admin endpoint)

#### 2.3 Organisation Hierarchy

`OrgType` enum supports `INTERNAL`, `PARTNER`, `FRANCHISE` types — this is forward-looking architecture. However, there is **no `parent_org_id` field** on the Organization model, and no hierarchical query logic. Franchise/branch architecture would require adding a parent org relationship and propagating user roles across the hierarchy.

---

### DIMENSION 3 — USER AND ROLE ARCHITECTURE (5/10)

#### 3.1 User Model

Users can belong to multiple organisations via the `organization_users` collection. The `/api/auth/switch-organization` endpoint is implemented and tested. This is a good foundation for multi-org users (e.g., a CA managing multiple workshop clients).

**Critical misalignment:** The `users` collection has a global `role` field (e.g., `admin`, `technician`). The `organization_users` collection has a separate per-membership `role` field. These can diverge.

The frontend `App.js` uses `auth.user.role` (global role from `users` collection, Line 330) for route access decisions — not the org-specific role from the membership. The RBAC middleware correctly uses `request.state.tenant_user_role` (the membership role), but the frontend makes independent decisions based on the potentially stale global role. A user who joins Org B as `viewer` but has global role `admin` will see admin UI in Org B's context.

#### 3.2 Role Architecture

7 system roles: owner, admin, manager, dispatcher, technician, accountant, viewer.

**Roles are entirely hardcoded in:**
- `middleware/rbac.py` (`ROLE_PERMISSIONS` dict)
- `core/org/models.py` (`OrgUserRole` enum)

No custom role creation is possible. No permission matrix that org admin can configure. This is acceptable for early-stage SaaS but is a gap versus Zoho/Freshworks where org admins define granular custom roles.

#### 3.3 Role-Based Access Control

**Backend middleware (RBACMiddleware):** Maps URL patterns to allowed roles. Enforced for all non-public routes. ✅

**Frontend route guards:** `ProtectedRoute` uses `allowedRoles` prop — enforced at page level. ✅

**Gaps:**
1. The RBAC fallback passes through any unregistered route. Many legacy routes are not in `ROUTE_PERMISSIONS`.
2. Frontend uses global `user.role`, not org-specific role (described above).
3. Data-level filtering (e.g., technician can only see their OWN assigned tickets) is partially implemented but inconsistent. In `server.py` vehicles route, non-admin users are filtered to their own vehicles. But the main tickets route doesn't appear to do this consistently.

#### 3.4 Portal User Types

Four distinct user types exist:
- **Internal (admin/manager/accountant/technician):** Main app at `/dashboard`
- **Individual customers:** Customer portal at `/customer`
- **Business/fleet customers:** Business portal at `/business`

All authenticate through the same `/api/auth/login` endpoint — role-based redirect on the frontend. No separate login pages. This is acceptable but means the login page is confusingly generic.

Customer data scoping: Customer portal routes go to `/api/customer-portal/*` which maps to RBAC role `customer` — the backend customer portal routes should scope data by `customer_id`. Needs audit to confirm every endpoint filters by customer identity.

---

### DIMENSION 4 — PORTAL ARCHITECTURE (7/10)

#### 4.1 Portal Separation

All portals are **same SPA, different route prefixes** with role-based access:
- Internal app: `/dashboard`, `/tickets`, `/invoices`, etc.
- Customer portal: `/customer/*`
- Technician portal: `/technician/*`
- Business portal: `/business/*`
- Public pages: `/submit-ticket`, `/track-ticket`, `/quote/:shareToken`

No subdomain routing. Single deployment serves all portals. Acceptable for current scale but creates a large attack surface — a XSS vulnerability in one portal could affect all portals.

#### 4.2 Technician Portal

Implemented at `/technician/*` with dedicated `TechnicianLayout` and separate pages. Routes enforce `allowedRoles={["technician"]}` on frontend and `/api/technician-portal/*` maps to RBAC role `technician`.

Backend RBAC blocks technicians from `/api/finance/*`, `/api/banking/*`, `/api/hr/payroll*`. ✅

Technician can see: assigned tickets, their own attendance, leave, payroll, productivity.

Gap: No explicit server-side filter ensuring technicians only see THEIR assigned tickets (must audit `routes/technician_portal.py`).

#### 4.3 Customer Portal

Separate `CustomerLayout`, individual customer pages for: vehicles, service history, invoices, payments, AMC contracts.

Authentication: Customer logs in via main login — no magic-link or OTP-based customer authentication (which would be more appropriate for B2C customers).

Gap: Customer portal still uses the same JWT-based auth, no separate "lighter" auth for consumer users.

#### 4.4 Fleet/Business Customer Portal

Business portal exists at `/business/*` with `BusinessLayout`. Separate pages for fleet, tickets, invoices, AMC, reports. This is more comprehensive than most competitors at this stage. ✅

Gap: Fleet reports are basic summaries. No vehicle-level drill-down with cross-vehicle analytics.

#### 4.5 Public Pages

Three public pages:
- `/submit-ticket` — PublicTicketForm with no auth ✅
- `/track-ticket` — TrackTicket by ticket number ✅  
- `/quote/:shareToken` — PublicQuoteView by share token ✅

Backend public routes properly whitelisted in `TenantIsolationMiddleware.PUBLIC_ROUTES`. ✅ These are properly isolated from internal application data.

---

### DIMENSION 5 — PLATFORM OWNER LAYER (0/10)

**THIS DIMENSION IS THE MOST CRITICAL FINDING OF THIS REVIEW.**

There is **no platform owner layer whatsoever.** Not a single route, page, model, or concept in the codebase represents Battwheels (the SaaS company) looking down at its tenants as a platform operator.

Evidence:
```bash
$ grep -rn "platform_admin|super_admin|all_organizations|all_orgs" /app/backend/
# Returns: nothing except a test file mentioning "superadmin" as an INVALID role
```

No frontend page exists for platform admin (confirmed by directory scan).

**What this means in practice:**
- When a new workshop signs up at `battwheels.io`, Battwheels has no UI to see this happened
- Battwheels cannot view the list of registered organizations from any admin panel
- Battwheels cannot suspend a fraudulent or non-paying tenant (only through direct MongoDB access)
- Battwheels cannot change a tenant's plan (only through direct MongoDB access)
- Battwheels cannot view platform-wide usage to understand which features are being used
- Battwheels cannot access a tenant's data for support purposes (no impersonation with audit trail)
- Billing is entirely manual — no tenant is currently being charged for anything automated

This is not a minor gap. This is the difference between a product and a SaaS business. Without a platform admin layer, Battwheels OS is a product that has been installed for one customer (Battwheels Garages), not a functioning SaaS platform.

---

### DIMENSION 6 — API AND INTEGRATION ARCHITECTURE (3/10)

#### 6.1 API Structure

No versioning. All routes are at `/api/...` with no version prefix. Making any breaking API change in the future will break all existing integrations simultaneously.

OpenAPI/Swagger docs auto-generated by FastAPI at `/docs` — this is a genuine positive. ✅

No API key system for programmatic access per org. All access is through JWT-based user sessions, which expire and are user-bound (not machine-to-machine friendly).

#### 6.2 Webhook System

Defined as a feature flag in `subscription/models.py` as `integrations_webhooks: FeatureLimit` (Enterprise tier). **Not implemented.** No webhook subscription model, no event delivery queue, no retry logic.

#### 6.3 Integration Readiness

Existing integrations (Zoho, Razorpay, Stripe, E-Invoice) are hardcoded via global `.env` variables — they are not per-tenant. This means:

- Only one Razorpay account can receive payments across all tenants
- Only one E-Invoice IRP credential is used for all tenants
- Only one Zoho organisation can sync

This architecture **cannot support multi-tenant commercial operations** where each workshop has its own Razorpay account and GST E-Invoice credentials. This is a hard blocker that must be resolved before onboarding customer number two.

---

### DIMENSION 7 — DATABASE ARCHITECTURE (6/10)

#### 7.1 Schema Design

Row-level isolation is the correct choice for this scale. The `organization_id` field is present on all primary business collections.

Indexes: `add_performance_indexes.py` migration exists. Compound indexes need to have `organization_id` as the first field for optimal performance on tenant-scoped queries.

#### 7.2 Scalability Ceiling

- **10 organizations:** Completely fine with current architecture
- **100 organizations:** Likely fine if compound indexes are in place
- **1,000 organizations:** Report queries will become slow. Full-table scans on large collections (invoices, tickets) will cross tenant boundaries. Aggregation pipelines need `$match: {organization_id: ...}` as the first stage.
- **10,000 organizations:** Current architecture breaks down. Would need sharding by `organization_id`, keyset pagination replacing offset pagination, and likely a read replica for reporting.

The current `/api/inventory` route (server.py) has `limit: int = Query(25)` with pagination — this is correct. But the `generate_invoice_number()` function does `await db.invoices.count_documents({})` — a **global count across all tenants** — which will produce incorrect, duplicating invoice numbers as more tenants are added. This is a silent data integrity bug.

```python
# server.py Line 1223-1226 — BROKEN for multi-tenant
async def generate_invoice_number():
    count = await db.invoices.count_documents({})  # COUNTS ALL ORGS' INVOICES
    return f"INV-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"
```

#### 7.3 Data Portability

Export routes exist at `/api/export/*` — partial data export is available. No full "export everything for this org" function exists. No data deletion / right to erasure (GDPR compliance gap).

---

### DIMENSION 8 — SECURITY ARCHITECTURE (5/10)

#### 8.1 Authentication

JWT with 7-day expiry in production (`JWT_EXPIRATION_HOURS = 24 * 7`). No token refresh mechanism — once stolen, a token is valid for 7 days.

**Critical: Dual password hashing systems.** `utils/auth.py` uses SHA256 (`hashlib.sha256`). `server.py` uses bcrypt. These are two incompatible hashing systems. Users created via `server.py`'s `/api/auth/register` use bcrypt. Users created elsewhere may use SHA256. A user who registers via one path cannot authenticate via the path that uses the other hash. This is a latent bug and a security weakness (SHA256 is not suitable for password storage).

```python
# utils/auth.py Line 25-27 — WRONG
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# server.py Line 1118-1119 — CORRECT
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

No brute-force protection on the login endpoint (rate limiting exists as a global middleware but no account lockout).

No multi-factor authentication.

#### 8.2 Authorization

Cross-tenant access at the API level is prevented by `TenantGuardMiddleware` for routes that correctly use `tenant_context_required`. For older routes (`/api/allocations`, `/api/users`, etc.), cross-tenant access is possible for any authenticated user.

#### 8.3 Data Security

- Sentry integration awaiting production DSN — error data currently has no observability
- CORS wildcard in development (`CORS_ORIGINS=*`) — must be locked to specific domains before production
- File upload paths are not org-scoped in the filesystem (`/app/uploads/`)

---

### DIMENSION 9 — OPERATIONAL ARCHITECTURE (4/10)

#### 9.1 Deployment

Running in a Kubernetes container (this preview env). Backend is a FastAPI monolith. No microservices decomposition. Hot reload via Supervisor.

No formal CI/CD pipeline documented. No database migration system — migrations are Python scripts in `/migrations/` that must be run manually.

#### 9.2 Monitoring

Sentry integration is coded and waits for `SENTRY_DSN` env var. Until that's set, there is zero error observability in production.

No per-tenant error tracking — Sentry will aggregate all tenant errors into a single error stream.

No distributed tracing (request_id is generated in TenantContext but not propagated to Sentry).

Background job observability: SLA breach detection job is started on startup with no heartbeat monitoring.

#### 9.3 Backup and Recovery

No documented backup strategy. No data restore API. Single MongoDB instance with no replica set mentioned. If MongoDB data is lost, there is no recovery path.

---

### DIMENSION 10 — ENTERPRISE READINESS (3/10)

An enterprise fleet operator evaluating this platform would find:
- **Can credibly demo:** Ticket management, invoice generation, technician portal, EFI AI diagnostics, vehicle service history, customer portal
- **Would ask for and is missing:** SSO/SAML login, custom roles and permissions, audit logs (complete), per-org API keys, data export/backup, SLA reporting dashboard, multi-location support, 99.9% SLA guarantee, GDPR compliance documentation, security questionnaire responses

---

## ZOHO COMPARISON MATRIX

| Feature                       | Zoho    | This Platform |
|-------------------------------|---------|---------------|
| Multi-tenant isolation        | ✅      | ⚠️ Partial (middleware correct, some routes unscoped) |
| Per-org module control        | ✅      | ⚠️ Model defined, API enforcement missing |
| Custom roles per org          | ✅      | ❌ Not built |
| Platform super-admin          | ✅      | ❌ Not built (critical gap) |
| Subscription management       | ✅      | ⚠️ Model built, payment flow incomplete |
| Public API versioning         | ✅      | ❌ No versioning |
| Webhook subscriptions         | ✅      | ❌ Defined in model, not implemented |
| Audit logs (complete)         | ✅      | ⚠️ Partial (ActivityService exists, coverage limited) |
| Custom fields per module      | ✅      | ❌ Not built |
| SSO/SAML                      | ✅      | ❌ Not built |
| White-labelling               | ✅      | ⚠️ Per-org branding colors/logo — no custom domain |
| Data export per tenant        | ✅      | ⚠️ Partial export routes, no full org data dump |
| Mobile apps                   | ✅      | ❌ Web only |
| Offline capability            | ✅      | ❌ Not built |
| Multi-language                | ✅      | ❌ Not built |
| Per-org payment config        | ✅      | ❌ Global Razorpay key (hard blocker) |
| Per-org email config          | ✅      | ❌ Global Resend key |
| Tenant onboarding automation  | ✅      | ⚠️ Partial (no CoA, no SLA defaults) |

---

## CRITICAL ARCHITECTURAL GAPS
*Must fix before this can be sold as multi-tenant SaaS to any paying customer.*

**GAP 1: No Platform Admin Layer**
There is no mechanism for Battwheels (the SaaS operator) to manage tenants. Before a second customer can be onboarded, a minimal admin panel is needed: list all orgs, view their plan/status, activate/suspend, change plan.

**GAP 2: Per-Tenant Integration Credentials**
Razorpay, Resend (email), and E-Invoice IRP credentials are single global `.env` values. For multi-tenant operations, these must move to per-org encrypted storage (e.g., a `tenant_credentials` collection). This is the hardest integration blocker.

**GAP 3: Unscoped Routes in server.py**
At minimum 5 routes have confirmed cross-tenant data leaks:
- `GET /api/allocations` — no org filter
- `GET /api/users` — returns all users  
- `GET /api/technicians` — returns all technicians globally
- Multiple routes in `contact_integration.py`
- `generate_invoice_number()` — counts globally

**GAP 4: Entitlement Enforcement Not Active**
`EntitlementService` and `require_feature()` dependency exist but are not attached to routes. A Free-tier org can call Enterprise-tier APIs.

---

## HIGH PRIORITY GAPS
*Needed within 6 months for platform credibility.*

1. **API Versioning (`/api/v1/`)** — Cannot make breaking changes without this
2. **Invoice/PO number generation scoped per org** — Currently counts globally, produces duplicates at scale
3. **Consistent use of `tenant_context_required`** in all remaining server.py routes
4. **Webhook delivery system** — Required for any OEM integration
5. **Complete data export per tenant** — GDPR/privacy requirement
6. **Frontend org-specific role usage** — Use membership role, not global `user.role`
7. **Fix dual password hashing** — Standardize on bcrypt everywhere
8. **Token expiry reduction + refresh token** — 7-day JWT without refresh is a security risk

---

## MEDIUM PRIORITY GAPS
*12-month roadmap.*

1. Custom roles configurable by org admin
2. Full audit logs for all write operations
3. SSO/SAML support for enterprise customers
4. Custom domain support for white-labelling
5. Mobile-responsive PWA or native mobile
6. Multi-language support (at minimum, English + Hindi)
7. Per-org API keys for programmatic access
8. MongoDB replica set for HA
9. Formal backup and restore procedures

---

## WHAT WORKS WELL

1. **Multi-tenant data model is architecturally correct.** The `organization_id` pattern, `organization_users` membership table, and `TenantContext` propagation model are professionally designed and would be recognizable to any senior SaaS engineer.

2. **RBAC middleware is comprehensive.** The route-to-role permission matrix covers 30+ route patterns. The role hierarchy with inheritance is a clean implementation.

3. **Subscription plan model is enterprise-grade.** The 4-tier plan model with 28 feature flags and usage limits shows deep product thinking. The `EntitlementService` with `require_feature()` decorator pattern is production-quality when actually applied.

4. **Portal architecture is distinctive.** Having 4 separate portals (internal, customer, technician, business/fleet) in a single coherent application is rare in vertical SaaS at this maturity level. Most competitors have one.

5. **EFI/AI module is genuinely differentiated.** The failure intelligence engine with confidence scoring, knowledge brain, and expert escalation has no direct equivalent in competing workshop management software. This is the platform's most defensible technical moat.

6. **Organization signup and onboarding flow is functionally complete.** A new organization can self-serve from signup to first invoice in under 10 minutes, which is competitive.

7. **Event-driven architecture in newer modules.** The `events/` framework for ticket and business events provides a foundation for future webhook delivery and cross-module automation.

---

## RECOMMENDED ARCHITECTURE ROADMAP

### Phase 1 — Fix for Beta (0-30 days):
- [ ] Patch all unscoped routes in `server.py` (5 confirmed, scan for more)
- [ ] Standardize password hashing to bcrypt (remove SHA256 from `utils/auth.py`)
- [ ] Scope `generate_invoice_number()`, `generate_po_number()`, `generate_sales_number()` per org
- [ ] Reduce JWT expiry to 24h, add refresh token endpoint
- [ ] Lock CORS to specific production origins

### Phase 2 — Platform Layer (30-90 days):
- [ ] Build Platform Admin panel (minimal: list orgs, view usage, change plan, suspend)
- [ ] Move integration credentials to per-org encrypted storage (`tenant_credentials` collection)
- [ ] Wire `require_feature()` to at minimum: HR/payroll routes, advanced reports, multi-warehouse, API access routes
- [ ] Fix frontend to use org-specific role from membership, not global `user.role`
- [ ] Add `/api/v1/` prefix to all routes (with `/api/` alias maintained for backward compat)
- [ ] Org-scoped file storage paths

### Phase 3 — Enterprise Grade (90-180 days):
- [ ] Webhook delivery system (event queue → delivery worker → retry logic)
- [ ] Custom roles per organization
- [ ] Complete audit log coverage (all write operations)
- [ ] Full data export per tenant (CSV/JSON of all collections)
- [ ] Data deletion / right to erasure
- [ ] Per-org email configuration (SMTP settings stored in tenant record)
- [ ] MongoDB replica set with automated backups
- [ ] Sentry with tenant context tagging

### Phase 4 — Scale (180-365 days):
- [ ] Keyset pagination on high-volume collections
- [ ] Compound index optimization with `organization_id` as first field
- [ ] Read replica for report generation
- [ ] Custom domain support (subdomain per tenant)
- [ ] SSO/SAML integration
- [ ] Mobile PWA or native app
- [ ] API key management per org (machine-to-machine auth)
- [ ] Horizontal scaling plan for backend (current monolith → service decomposition)

---

## ARCHITECT'S FINAL STATEMENT

Battwheels OS represents a genuine engineering investment in EV workshop management software. The codebase is larger than most early-stage SaaS products, the EFI module is technically differentiated, and the team has correctly identified multi-tenancy as a first-class concern by building `TenantContext`, `TenantGuardMiddleware`, and `EntitlementService`. This is not a shallow product — it has depth.

However, there is a fundamental gap between "multi-tenant foundation exists in the code" and "multi-tenant SaaS platform is operational." Today, Battwheels OS operates as a product installed for one customer (Battwheels Garages) with the infrastructure to eventually serve more. The most visible expression of this gap is the complete absence of any platform owner layer — Battwheels the company has no operational visibility into Battwheels the SaaS platform.

The three changes that would have the highest immediate impact are: (1) building a minimal platform admin dashboard so the business can see and manage its tenants, (2) moving integration credentials to per-org storage so a second customer can be onboarded with their own Razorpay and email account, and (3) patching the 5+ confirmed unscoped routes in `server.py` to close the cross-tenant data leaks. These three changes alone would elevate the platform from "demo-ready for one customer" to "ready to onboard the second paying customer."

The single most important architectural decision to make in the next 30 days is: **resolve the credentials per-tenant problem.** It is the hardest problem, it has the longest implementation timeline, and everything else (per-org billing, per-org invoicing, per-org communications) depends on it. A `tenant_credentials` collection with encrypted storage of per-org Razorpay, email, and E-Invoice credentials, accessible via a key management service, is the linchpin change. Building around it will force the right conversations about multi-tenancy to happen at every layer of the stack — and those conversations are what will turn this promising product into a real SaaS platform.

The EFI module remains the strongest case for enterprise adoption. If the platform can demonstrate that failure patterns learned from 100 workshops improve diagnosis quality for a new workshop on day one, that is a network effect that no point-of-sale ERP vendor can replicate. The architecture for this intelligence layer is well-designed. The investment in platform fundamentals — particularly the platform admin layer and per-tenant credential management — is what will allow that learning flywheel to spin up across real, independent customers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF REPORT
Principal Architect Review — Battwheels OS
February 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
