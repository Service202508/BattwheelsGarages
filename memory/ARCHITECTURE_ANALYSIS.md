# Battwheels OS - SaaS Architecture Analysis Report

**Date:** February 21, 2026  
**Version:** 1.0  
**Purpose:** Comprehensive analysis of current architecture and integration plan for enterprise SaaS features

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Architecture Analysis Report](#1-architecture-analysis-report)
3. [Development Plan Assessment](#2-development-plan-assessment)
4. [Non-Disruption Strategy](#3-non-disruption-strategy)
5. [Decision & Advisory Section](#4-decision--advisory-section)

---

## EXECUTIVE SUMMARY

### Current State
Battwheels OS has a **fully implemented multi-tenant backend architecture** (Phases A-G) with:
- ✅ Tenant Context Manager with org_id resolution
- ✅ Organization-scoped RBAC with system + custom roles
- ✅ Tenant Guard for data isolation enforcement
- ✅ Plan-based feature configuration
- ✅ AI/EFI isolation per organization
- ✅ SaaS onboarding flow (Landing, Signup, Org Selection)

### Assessment Result
**GO for SaaS Feature Development** - The existing architecture provides a solid foundation. The proposed enhancements (subscription management, feature entitlements, user provisioning) can be layered **without disrupting** existing modules.

### Key Findings
1. **Tenant isolation is STRONG** - 70+ collections have `organization_id` enforcement
2. **RBAC is mature** - System roles + custom roles per organization
3. **Plan features exist** - `config/plan_features.py` has Zoho Books-style gating
4. **Gap identified** - Missing formal `Subscription` entity and runtime entitlement service

---

## 1. ARCHITECTURE ANALYSIS REPORT

### 1.1 Current Module Architecture

| Module Category | Modules | Tenant-Aware | RBAC Enforced |
|-----------------|---------|--------------|---------------|
| **Core Operations** | Tickets, Vehicles, Estimates, Invoices | ✅ Yes | ✅ Yes |
| **Finance/ERP** | Invoices, Payments, Bills, Banking, Ledger | ✅ Yes | ✅ Yes |
| **Inventory** | Items, Stock, Serial/Batch Tracking, Warehouses | ✅ Yes | ✅ Yes |
| **HR/Payroll** | Employees, Attendance, Leave, Payroll | ✅ Yes | ✅ Yes |
| **Intelligence (EFI)** | Failure Cards, AI Guidance, Knowledge Brain | ✅ Yes | ✅ Yes |
| **Zoho Sync** | Contacts, Items, Invoices, Customers | ✅ Yes | ✅ Yes |
| **Settings** | Organization, Users, Permissions, Templates | ✅ Yes | ✅ Yes |

### 1.2 Data Model Overview

#### Collections WITH `organization_id` (Tenant-Scoped)
```
TENANT_COLLECTIONS = {
    # Core business data
    "tickets", "vehicles", "invoices", "estimates", "payments",
    "contacts", "customers", "items", "inventory", "suppliers",
    "purchase_orders", "sales_orders", "expenses", "bills",
    "credit_notes", "vendor_credits", "recurring_invoices",
    
    # Operations
    "amc_plans", "amc_subscriptions", "time_entries",
    "documents", "document_folders", "allocations",
    
    # HR & Payroll
    "employees", "attendance", "leave_requests", "payroll_records",
    
    # EFI Intelligence
    "failure_cards", "technician_actions", "part_usage",
    "ai_guidance_snapshots", "ai_guidance_feedback",
    "model_risk_alerts", "structured_failure_cards",
    "expert_escalations", "learning_events",
    
    # Knowledge
    "knowledge_articles", "knowledge_embeddings",
    "error_code_definitions", "fault_trees",
    
    # Settings & Config
    "organization_settings", "custom_fields", "workflow_rules",
    "pdf_templates", "notification_preferences",
    
    # Financial
    "ledger", "journal_entries", "bank_accounts",
    "bank_transactions", "reconciliations", "chart_of_accounts",
    
    # Stock
    "stock", "stock_transfers", "warehouses",
    "serial_numbers", "batch_numbers"
}
```

#### Collections WITHOUT `organization_id` (Global)
```
GLOBAL_COLLECTIONS = {
    "users", "user_sessions", "organizations", "organization_users",
    "audit_logs", "event_log", "sync_jobs", "sync_status",
    "master_vehicle_categories", "master_vehicle_models", "master_issue_types",
    "taxes", "currencies", "countries", "states"
}
```

### 1.3 Current Tenant Context Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     REQUEST LIFECYCLE                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Request arrives with:                                         │
│     • Authorization: Bearer <JWT>                                 │
│     • X-Organization-ID: org_xxx                                  │
│                                                                   │
│  2. TenantContextManager.resolve_context():                       │
│     • Validate JWT → extract user_id                              │
│     • Resolve org_id (header > query > default)                   │
│     • Verify membership in organization_users                     │
│     • Load organization data (plan, status)                       │
│     • Load role permissions from tenant_roles                     │
│     • Create immutable TenantContext                              │
│                                                                   │
│  3. TenantContext propagates to:                                  │
│     • Route handlers (via Depends)                                │
│     • Services (passed as parameter)                              │
│     • Repositories (auto-scope queries)                           │
│     • Event emitters (attach metadata)                            │
│                                                                   │
│  4. TenantGuard enforces on every DB operation:                   │
│     • validate_query() - adds/checks org_id                       │
│     • validate_document() - stamps org_id on insert               │
│     • validate_aggregation() - ensures $match on org_id           │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 Current RBAC Structure

**System Roles (cloned per-organization):**
```python
SYSTEM_ROLE_TEMPLATES = {
    "admin":      # Full access to all modules
    "manager":    # Operations, sales, reports
    "technician": # Assigned tickets, AI assistant
    "customer":   # View own tickets/invoices
}
```

**Organization-specific roles stored in `tenant_roles` collection:**
```json
{
  "role_id": "role_abc123",
  "organization_id": "org_xxx",
  "role_code": "admin",
  "name": "Administrator",
  "is_system": true,
  "permissions": {
    "tickets": {"view": true, "create": true, "edit": true, "delete": true},
    "invoices": {"view": true, "create": true, "edit": true, "delete": true},
    ...
  }
}
```

### 1.5 Current Plan/Feature Configuration

Located in `/app/backend/config/plan_features.py`:

| Plan | Max Users | Max Invoices/Month | Key Features |
|------|-----------|-------------------|--------------|
| FREE | 1 | 50 | Basic invoicing, estimates |
| STANDARD | 3 | 500 | + Inventory, multi-currency, recurring |
| PROFESSIONAL | 5 | 2,000 | + Serial/batch, custom reports, workflows |
| PREMIUM | 10 | 5,000 | + Time tracking, budgeting, project tracking |
| ULTIMATE | Unlimited | Unlimited | All features |

**Decorators available:**
```python
@require_feature("serial_batch_tracking")
@require_limit("max_users", count_func)
```

### 1.6 Tenant Isolation Verification

**Isolation mechanisms in place:**
1. **Middleware**: `TenantGuardMiddleware` logs all requests
2. **Query validation**: `TenantGuard.validate_query()` enforces org_id
3. **Insert validation**: `TenantGuard.validate_document()` stamps org_id
4. **Aggregation safety**: Pipeline injection of `$match` on org_id
5. **Violation recording**: Logged with timestamp, user, attempted org
6. **AI isolation**: Separate vector stores per `namespace=org_id`

**Test suite locations:**
- `/app/backend/tests/test_tenant_isolation.py`
- `/app/backend/tests/test_tenant_features.py`
- `/app/backend/tests/test_tenant_final.py`

---

## 2. DEVELOPMENT PLAN ASSESSMENT

### 2.1 Proposed Entity Mapping

#### NEW: Plans Collection (Static Configuration)
```json
{
  "plan_id": "plan_starter",
  "code": "starter",
  "name": "Starter",
  "description": "For small workshops",
  "billing_cycle": "monthly",
  "price_monthly": 2999,
  "price_annual": 29990,
  "currency": "INR",
  "features": {
    "ops.tickets": {"enabled": true, "limit": null},
    "ops.vehicles": {"enabled": true, "limit": 100},
    "finance.invoicing": {"enabled": true, "limit": 500},
    "finance.recurring_invoices": {"enabled": false},
    "efi.failure_intelligence": {"enabled": true},
    "efi.ai_guidance": {"enabled": true, "limit": 100},
    "inventory.tracking": {"enabled": true},
    "inventory.serial_batch": {"enabled": false},
    "hr.attendance": {"enabled": false},
    "hr.payroll": {"enabled": false},
    "integrations.zoho_sync": {"enabled": false},
    "integrations.api_access": {"enabled": false}
  },
  "limits": {
    "max_users": 3,
    "max_technicians": 2,
    "max_vehicles": 100,
    "max_invoices_per_month": 500,
    "storage_gb": 5
  },
  "is_active": true
}
```

#### NEW: Subscriptions Collection
```json
{
  "subscription_id": "sub_xxx",
  "organization_id": "org_xxx",
  "plan_id": "plan_professional",
  "status": "active",  // active, trialing, past_due, canceled, suspended
  "current_period_start": "2026-02-01T00:00:00Z",
  "current_period_end": "2026-03-01T00:00:00Z",
  "trial_end": null,
  "cancel_at_period_end": false,
  "payment_method": "stripe",
  "stripe_subscription_id": "sub_1xxx",
  "usage_this_period": {
    "invoices_created": 42,
    "ai_guidance_calls": 15,
    "storage_used_mb": 1250
  },
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-02-21T08:00:00Z"
}
```

#### ENHANCED: Organizations Collection
Add `org_type` field:
```json
{
  "organization_id": "org_xxx",
  "name": "Mumbai EV Workshop",
  "org_type": "customer",  // NEW: "internal" or "customer"
  "plan_type": "professional",
  "subscription_id": "sub_xxx",  // NEW: Reference to subscription
  "is_active": true,
  ...
}
```

### 2.2 Feature Entitlement Service Design

**Location:** `/app/backend/core/entitlements/`

```
core/entitlements/
├── __init__.py
├── service.py          # EntitlementService class
├── decorators.py       # @require_entitlement, @check_limit
├── models.py           # Plan, Subscription, UsageRecord
└── cache.py            # Redis/memory cache for performance
```

**EntitlementService API:**
```python
class EntitlementService:
    async def check_feature(self, ctx: TenantContext, feature_key: str) -> bool:
        """Check if organization can use a feature"""
        
    async def check_limit(self, ctx: TenantContext, limit_key: str, increment: int = 1) -> LimitResult:
        """Check and optionally consume from a limit quota"""
        
    async def get_usage(self, org_id: str, period: str = "current") -> UsageReport:
        """Get current usage statistics"""
        
    async def enforce(self, ctx: TenantContext, feature_key: str) -> None:
        """Raise HTTPException if feature not allowed"""
```

**Integration with existing RBAC:**
```python
# In route handler
@router.post("/tickets")
async def create_ticket(
    ctx: TenantContext = Depends(tenant_context_required),
    entitlements: EntitlementService = Depends(get_entitlement_service)
):
    # 1. RBAC check (existing)
    ctx.require_permission("tickets:create")
    
    # 2. Entitlement check (NEW)
    await entitlements.enforce(ctx, "ops.tickets")
    
    # 3. Usage limit check (NEW)
    limit_result = await entitlements.check_limit(ctx, "max_tickets_per_month")
    if not limit_result.allowed:
        raise HTTPException(429, f"Ticket limit reached ({limit_result.used}/{limit_result.limit})")
    
    # 4. Create ticket...
```

### 2.3 Impact Analysis

| Component | Impact | Changes Required |
|-----------|--------|-----------------|
| **Database** | LOW | Add 2 new collections (plans, subscriptions), add 2 fields to organizations |
| **TenantContext** | LOW | Add `subscription` field, load from cache |
| **Routes** | MEDIUM | Add entitlement checks to feature-gated routes |
| **Frontend** | MEDIUM | Add subscription management UI, feature toggles |
| **Existing Logic** | NONE | All existing business logic unchanged |

### 2.4 User Type / Role Clarification

**Current roles in OrgUserRole enum:**
```python
class OrgUserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    DISPATCHER = "dispatcher"
    TECHNICIAN = "technician"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"
```

**Proposed additions:**
```python
class OrgUserRole(str, Enum):
    # Existing
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    DISPATCHER = "dispatcher"
    TECHNICIAN = "technician"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"
    
    # NEW - Customer Types
    BUSINESS_CUSTOMER = "business_customer"   # Fleet manager
    INDIVIDUAL_CUSTOMER = "individual_customer"  # Single vehicle owner
```

**User flow by type:**
| User Type | Primary Portal | Capabilities |
|-----------|---------------|--------------|
| Admin/Owner | Admin Dashboard | Full org management |
| Manager | Admin Dashboard | Operations oversight |
| Technician | Technician App | Execute tickets, diagnostics |
| Business Customer | Business Portal | Fleet management, invoices |
| Individual Customer | Customer Portal | Book service, view history |

---

## 3. NON-DISRUPTION STRATEGY

### 3.1 Phased Integration Plan

#### Phase 1: Data Layer (2-3 days)
**Objective:** Add new collections without touching existing code

1. Create `plans` collection with default plan definitions
2. Create `subscriptions` collection with schema
3. Add `org_type` and `subscription_id` to organizations
4. Create migration script to assign default subscription to existing orgs

**Verification:**
- All existing queries continue to work
- No changes to existing route handlers
- Run existing test suite (100% pass required)

#### Phase 2: Entitlement Service (3-4 days)
**Objective:** Build central entitlement checking service

1. Create `/app/backend/core/entitlements/` module
2. Implement `EntitlementService` class
3. Add service initialization to `server.py`
4. Create `@require_entitlement` decorator
5. Add to TenantContext loading pipeline

**Verification:**
- Unit tests for EntitlementService
- Decorator does not affect routes without it
- Context loading adds <5ms latency

#### Phase 3: Route Integration (5-7 days)
**Objective:** Add entitlement checks to feature-gated routes

Priority order:
1. AI/EFI routes (high-value feature)
2. Recurring invoices
3. Serial/batch tracking
4. Multi-warehouse
5. Custom reports
6. API access

**Verification:**
- Feature works for entitled plans
- Feature returns 403 with upgrade message for non-entitled plans
- No impact on non-gated routes

#### Phase 4: Admin Portal (3-4 days)
**Objective:** Organization admin can manage subscription

1. Subscription overview page
2. Plan comparison modal
3. Upgrade/downgrade flow
4. Usage statistics dashboard
5. User invitation interface

**Verification:**
- Admins can view current plan
- Plan change triggers Stripe checkout
- Usage displays accurately

#### Phase 5: User Provisioning (3-4 days)
**Objective:** Complete user invitation flow

1. Email invitation with magic link
2. Invite acceptance flow
3. Role assignment during invite
4. Bulk invite for business customers

**Verification:**
- Invited user receives email
- Clicking link joins correct organization
- Proper role is assigned

### 3.2 Rollback Procedures

#### Per-Phase Rollback

| Phase | Rollback Procedure | Data Impact |
|-------|-------------------|-------------|
| Phase 1 | Drop new collections, revert migration | None on existing data |
| Phase 2 | Remove entitlement imports from server.py | None |
| Phase 3 | Remove decorator calls from routes | None |
| Phase 4 | Revert frontend changes via git | None |
| Phase 5 | Disable invitation endpoints | Pending invites orphaned |

#### Emergency Rollback Script
```bash
# /app/scripts/rollback_entitlements.sh
#!/bin/bash

# 1. Disable entitlement service
export ENTITLEMENTS_ENABLED=false

# 2. Restart backend
sudo supervisorctl restart backend

# 3. (If needed) Drop collections
# mongo $MONGO_URL --eval "db.subscriptions.drop(); db.plans.drop();"
```

### 3.3 Automated Regression Test Plan

**Test categories:**
1. **Cross-tenant isolation** - Verify org A cannot see org B data
2. **Cross-role access** - Verify technician cannot access admin routes
3. **Feature gating** - Verify plan limits are enforced
4. **Workflow integrity** - Ticket → Invoice → Payment chain works

**Test execution:**
```bash
# Run before and after each phase
pytest /app/backend/tests/test_tenant_isolation.py -v
pytest /app/backend/tests/test_tenant_features.py -v

# Add new entitlement tests
pytest /app/backend/tests/test_entitlements.py -v
```

---

## 4. DECISION & ADVISORY SECTION

### 4.1 Go/No-Go Checkpoints

| Checkpoint | Criteria | Current Status |
|------------|----------|----------------|
| **Phase 1 Entry** | Existing test suite passes | ✅ READY |
| **Phase 1 Exit** | Migration complete, no query failures | PENDING |
| **Phase 2 Entry** | Phase 1 verified | PENDING |
| **Phase 2 Exit** | EntitlementService unit tests pass | PENDING |
| **Phase 3 Entry** | Phase 2 verified | PENDING |
| **Phase 3 Exit** | Integration tests for gated features pass | PENDING |
| **Phase 4 Entry** | Phase 3 verified | PENDING |
| **Phase 4 Exit** | Admin can manage subscription | PENDING |
| **Phase 5 Entry** | Phase 4 verified | PENDING |
| **Phase 5 Exit** | User invitation flow complete | PENDING |

### 4.2 Required Refactors vs Optional Improvements

#### REQUIRED (Blocking)
1. Add `subscription_id` to organizations collection
2. Create EntitlementService with caching
3. Add `org_type` field for internal/customer distinction

#### RECOMMENDED (High Value)
1. Redis caching for entitlement lookups
2. Usage metering pipeline (async)
3. Webhook for Stripe subscription events

#### OPTIONAL (Nice to Have)
1. Plan comparison widget in landing page
2. Usage forecasting/alerts
3. Seat-based pricing model

### 4.3 Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Entitlement check latency** | Medium | High | Aggressive caching, batch lookups |
| **Plan migration confusion** | Low | Medium | Clear UI, confirmation dialogs |
| **Feature flag inconsistency** | Low | High | Centralized config, CI validation |
| **Existing org data loss** | Very Low | Critical | Migration script tested on staging |
| **Stripe webhook failures** | Medium | Medium | Retry queue, manual fallback |

### 4.4 Internal vs External Organization Handling

**Key principle:** `org_type` is metadata, NOT a security bypass.

```python
# In TenantGuard - NO special handling for internal orgs
def validate_query(self, collection, query, ctx):
    # Same rules apply regardless of org_type
    query["organization_id"] = ctx.org_id
    return query
```

**Internal org privileges via RBAC:**
```python
# If internal orgs need extra features, add a role
SYSTEM_ROLE_TEMPLATES["battwheels_ops"] = {
    "name": "Battwheels Operations",
    "permissions": {
        "admin": {"view": True, "create": True, "edit": True, "delete": True},
        "super_reports": {"view": True},
        ...
    }
}
```

---

## APPENDIX A: File References

| File | Purpose |
|------|---------|
| `/app/backend/core/tenant/context.py` | TenantContext, TenantContextManager |
| `/app/backend/core/tenant/rbac.py` | TenantRBACService, role templates |
| `/app/backend/core/tenant/guard.py` | TenantGuard, query validation |
| `/app/backend/core/org/models.py` | Organization, OrgUserRole enums |
| `/app/backend/core/org/service.py` | OrganizationService |
| `/app/backend/config/plan_features.py` | Plan definitions, feature flags |
| `/app/backend/routes/organizations.py` | Org signup API |
| `/app/backend/routes/auth.py` | Login, org switching |

---

## APPENDIX B: Collection Index Recommendations

For performance with multi-tenant queries:

```javascript
// Compound indexes for tenant-scoped queries
db.tickets.createIndex({"organization_id": 1, "created_at": -1})
db.invoices.createIndex({"organization_id": 1, "status": 1, "created_at": -1})
db.subscriptions.createIndex({"organization_id": 1}, {unique: true})
db.organization_users.createIndex({"user_id": 1, "status": 1})
db.plans.createIndex({"code": 1}, {unique: true})
```

---

**Document Status:** COMPLETE  
**Next Action:** Await user approval to begin Phase 1 implementation
