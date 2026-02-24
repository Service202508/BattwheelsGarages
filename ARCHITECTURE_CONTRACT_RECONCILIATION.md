# Architecture Contract Reconciliation Report
## Battwheels OS — Critical & High Mismatches Only

**Date:** 2026-02-20
**Scope:** P0 findings only + any newly discovered Critical/High mismatches
**Status:** READ-ONLY ANALYSIS — No code changes made

---

## 1. Full Route Coverage Map — `/api/v1/*`

### Middleware Execution Order (LIFO — last added runs first)

```
Request → CORSMiddleware → SecurityHeaders → TenantGuardMiddleware → RBACMiddleware → RateLimitMiddleware → Route Handler
```

**Binding order in `server.py` (lines 6619–6633):**
```python
app.add_middleware(RateLimitMiddleware)    # Runs LAST
app.add_middleware(RBACMiddleware)          # Runs 2nd
app.add_middleware(TenantGuardMiddleware)   # Runs 1st
```

### Guard Coverage Matrix

| Guard Layer             | Covers `/api/v1/*`? | Evidence |
|------------------------|---------------------|----------|
| **JWT Authentication** | YES                 | `TenantGuardMiddleware.dispatch()` in `core/tenant/guard.py:483` blocks unauthenticated requests to all non-public paths |
| **Tenant Isolation**   | YES                 | Same middleware validates `organization_id` + membership |
| **RBAC (Role Check)**  | **NO — BYPASSED**   | All patterns in `ROUTE_PERMISSIONS` use `/api/<section>/...` — none use `/api/v1/<section>/...`. See Section 2. |
| **Rate Limiting**      | YES                 | `RateLimitMiddleware` runs on all paths |

### Routes WITHOUT RBAC Coverage (ALL `/api/v1/*` routes)

Every route mounted on `v1_router` is affected. This includes **60+ route modules** with hundreds of endpoints:
- Finance: `/api/v1/journal-entries/*`, `/api/v1/invoices-enhanced/*`, `/api/v1/bills-enhanced/*`
- HR: `/api/v1/hr/*`, `/api/v1/employees/*`, `/api/v1/payroll/*`
- Operations: `/api/v1/tickets/*`, `/api/v1/inventory/*`
- Admin: `/api/v1/organizations/*`, `/api/v1/settings/*`, `/api/v1/permissions/*`
- Integrations: `/api/v1/zoho-sync/*`, `/api/v1/razorpay/*`, `/api/v1/stripe/*`
- AI: `/api/v1/ai-assist/*`, `/api/v1/ai-guidance/*`, `/api/v1/efi/*`
- Data: `/api/v1/data-management/*`, `/api/v1/data-migration/*`, `/api/v1/seed/*`

**Impact:** Any authenticated user (even `viewer` or `customer` role) can access ALL v1 endpoints including finance, HR, admin settings, data management, and destructive operations.

---

## 2. RBAC Bypass — Root Cause Evidence

### The Bug

**File:** `backend/middleware/rbac.py`
**Root Cause:** Pattern mismatch between RBAC route definitions and actual route paths.

**RBAC route patterns (rbac.py lines 42–155)** define paths like:
```python
ROUTE_PERMISSIONS = {
    r"^/api/finance/.*$":           ["org_admin", "admin", "owner", "accountant"],
    r"^/api/hr/payroll.*$":         ["org_admin", "admin", "owner"],
    r"^/api/invoices/.*$":          ["org_admin", "admin", "owner", "accountant", "manager"],
    r"^/api/ai/.*$":                ["org_admin", "admin", "owner", "manager", "technician"],
    # ... etc
}
```

**Actual request paths** for all business routes are:
```
/api/v1/finance/...
/api/v1/hr/payroll...
/api/v1/invoices-enhanced/...
/api/v1/ai-assist/...
```

The patterns match `/api/<section>` but actual paths are `/api/v1/<section>`.

### Proof of Bypass

In `rbac.py:264–269`:
```python
allowed_roles = get_allowed_roles(path)

if allowed_roles is None:
    # Route not in permissions map - allow authenticated users
    logger.info(f"RBAC: Route {path} not in map, allowing {user_role}")
    return await call_next(request)
```

When `get_allowed_roles("/api/v1/hr/payroll/generate")` is called:
- It checks `r"^/api/hr/payroll.*$"` against `/api/v1/hr/payroll/generate` → **NO MATCH**
- Returns `None`
- Middleware logs "not in map, allowing" and passes through

### Secondary Finding: Redundant TenantIsolationMiddleware

`middleware/tenant.py` defines `TenantIsolationMiddleware` (a separate class from `TenantGuardMiddleware` in `core/tenant/guard.py`). However, `server.py` only adds `TenantGuardMiddleware` (line 6632). The `TenantIsolationMiddleware` in `middleware/tenant.py` is **dead code** — it is never mounted. The handoff incorrectly attributed the RBAC bypass to string matching in `middleware/tenant.py`, but the actual issue is in `middleware/rbac.py`.

---

## 3. AI Assistant Data Flow Map

### Current Flow (VULNERABLE)

```
Client → POST /api/v1/ai-assist/diagnose
         │
         ├── TenantGuardMiddleware sets:
         │     request.state.tenant_org_id = "org_xxx"
         │     request.state.tenant_user_id = "user_xxx"
         │
         └── ai_assistant.py:ai_diagnose()
              │
              ├── Reads data.query, data.category, data.portal_type
              ├── Reads data.context.user_name (from request body — NOT from auth)
              │
              ├── Builds system prompt (portal-specific, NO tenant data)
              │
              ├── Creates LlmChat session:
              │     session_id = f"ai_{data.portal_type}_{random_hex}"   ← NOT org-scoped
              │
              ├── Sends query to Gemini
              │     NO database queries — no tenant data exposed currently
              │     NO vector store queries — no embeddings used
              │     NO RAG pipeline — pure LLM call
              │
              └── Returns response
```

### Where `organization_id` IS Missing

| Check Point | Status | Evidence |
|-------------|--------|----------|
| Route handler extracts `org_id` from `request.state` | **MISSING** | `ai_assistant.py` never reads `request.state.tenant_org_id` |
| Database queries scoped by `org_id` | **N/A** | No DB queries in current implementation |
| Vector/embedding namespace | **N/A** | No vector store used (pure LLM, no RAG) |
| LLM session isolation by org | **MISSING** | `session_id` uses random hex, not org-scoped |
| User identity from auth (not body) | **MISSING** | User name comes from `data.context.user_name` (client-supplied) |

### Actual Risk Assessment

**Current risk is MODERATE, not CRITICAL.** The AI assistant currently makes no database queries and has no RAG pipeline. It's a stateless LLM call. There is no tenant data being leaked because no tenant data is being fetched. However:
- **Future risk is CRITICAL** — any addition of RAG, knowledge base, or ticket context lookup without org_id scoping would create a cross-tenant leak.
- **Session spoofing risk** — `user_name` and `portal_type` come from the request body, not from authenticated context.

### Where `org_id` SHOULD Be Injected (for future-proofing and correctness)

1. Extract `org_id` from `request.state.tenant_org_id` (set by TenantGuardMiddleware)
2. Use `org_id` as namespace prefix in `session_id`: `f"ai_{org_id}_{portal_type}_{hex}"`
3. Extract `user_name` from authenticated user, not from request body
4. If/when adding RAG: all vector queries MUST filter by `organization_id`

---

## 4. Zoho Sync Destructive Operations — Call Sites

**File:** `backend/routes/zoho_sync.py`
**Endpoint:** `POST /api/v1/zoho-sync/disconnect-and-purge`
**Mounted on:** `v1_router` (line 5495 in server.py)

### Destructive Call Sites

| Line | Operation | Filter | Scoped by Org? | Scoped by Source? | Risk |
|------|-----------|--------|----------------|-------------------|------|
| **863** | `db[collection_name].delete_many(filter_query)` | `{"source": "zoho_books"}` for some collections | **NO** | YES (partial) | HIGH — deletes ALL orgs' Zoho data |
| **866** | `db[collection_name].delete_many({})` | `{}` (EMPTY — deletes ALL records) | **NO** | **NO** | **CRITICAL** — wipes entire collections |
| **880** | `db.drop_collection(coll)` | N/A — drops entire collection | **NO** | N/A | **CRITICAL** — drops backup collections for ALL tenants |

### Affected Collections with Empty Filter (line 866)

These collections have `{}` as filter — meaning ALL records for ALL tenants are deleted:
```python
("invoice_line_items", {}),
("estimate_line_items", {}),
("bill_line_items", {}),
("salesorder_line_items", {}),
("po_line_items", {}),
("invoice_history", {}),
("estimate_history", {}),
("bill_history", {}),
("salesorder_history", {}),
("contact_history", {}),
("item_history", {}),
("sync_logs", {}),
("sync_status", {}),
("sync_events", {}),
("sync_jobs", {}),
("books_customers", {}),
("books_invoices", {}),
("books_payments", {}),
("books_vendors", {}),
("item_stock", {}),
("item_stock_locations", {}),
("item_batch_numbers", {}),
("item_serial_numbers", {}),
("item_serial_batches", {}),
("payments_received", {}),
("payment_history", {}),
("invoice_payments", {}),
("bill_payments", {}),
```

### Environment/Tenant Guards

| Guard | Present? | Evidence |
|-------|----------|----------|
| Environment check (`if ENVIRONMENT != 'production'`) | **NO** | Not present in the function |
| Tenant scoping (`organization_id` in filter) | **NO** | Only `{"source": "zoho_books"}` for some; `{}` for others |
| Confirmation flag | YES | `request.confirm` must be `True` (line 776) |
| Auth required | YES (implicit) | TenantGuardMiddleware blocks unauthenticated access |
| Role check (RBAC) | **NO (bypassed)** | See Section 2 — RBAC doesn't cover `/api/v1/*` |

### Additional Destructive Operations in Other Files

| File | Line | Operation | Scoped? |
|------|------|-----------|---------|
| `data_sanitization_service.py:345` | `delete_many` | YES (has filter) |
| `data_management.py:372` | `delete_many` | Partial |
| `purge_audit_org.py:28` | `delete_many` | YES (by org_id) |
| `purge_test_orgs.py:39` | `delete_many` | YES (by org_id) |

---

## 5. Journal Posting Flow — Double-Post Analysis

### Flow: Invoice → Journal Entry

```
1. POST /api/v1/invoices-enhanced/{invoice_id}/send
   OR
   POST /api/v1/invoices-enhanced/{invoice_id}/mark-sent
         │
         ├── invoices_enhanced.py:1462-1466 (send endpoint)
         │     if was_draft and org_id:
         │         await post_invoice_journal_entry(org_id, invoice)
         │
         ├── invoices_enhanced.py:1511-1515 (mark-sent endpoint)
         │     org_id = invoice.get("organization_id", "")
         │     if org_id:
         │         await post_invoice_journal_entry(org_id, invoice)
         │
         └── posting_hooks.py:30-62
              │
              └── double_entry_service.py:508 post_sales_invoice()
                   │
                   └── double_entry_service.py:366 create_journal_entry()
                        │
                        ├── Generates new reference_number (always unique)
                        ├── Validates debit == credit
                        └── journal_entries.insert_one(entry_dict)
                             ← NO check for existing entry with same source_document_id
```

### Idempotency Check — ABSENT

**In `create_journal_entry()` (double_entry_service.py:366–449):**
- No check for `source_document_id` + `source_document_type` uniqueness
- No `find_one` before `insert_one`
- No unique index on `(organization_id, source_document_id, source_document_type)`

**In `post_invoice_journal_entry()` (posting_hooks.py:30–62):**
- No check for existing journal entry for this invoice
- No duplicate prevention at any level

**In `invoices_enhanced.py` send/mark-sent endpoints (lines 1462-1466, 1511-1515):**
- No guard like `if not already_posted`
- The `was_draft` check on the send endpoint (line 1463) provides partial protection (only posts when transitioning from draft)
- BUT the mark-sent endpoint (line 1512) has NO such check
- Repeated calls to mark-sent will create duplicate entries

### Contrast with `post_all_unposted_invoices()` (posting_hooks.py:294–333)

This batch function DOES have an idempotency check:
```python
posted_ids = await service.journal_entries.distinct("source_document_id", {
    "organization_id": organization_id,
    "source_document_type": "invoice"
})
invoices = await db.invoices_enhanced.find({
    "invoice_id": {"$nin": posted_ids}  # ← Excludes already-posted
})
```

This proves the architects knew about the idempotency need but only implemented it in the batch path, not the individual posting path.

### Double-Post Scenarios

| Scenario | Double-Post? | Evidence |
|----------|-------------|----------|
| Send invoice (draft→sent) called twice | NO (2nd call fails: "Only draft invoices can be sent") | Status changes to "sent" on first call |
| Mark-sent called twice on same invoice | **YES** | No `was_draft` guard; status check only prevents draft→sent, but mark-sent can be called repeatedly if status is already "sent" |
| Network retry on send | **Possible** | If first request succeeds but response is lost, retry could re-post |
| Invoice voided then re-sent | **YES** | No check if journal entry already exists for this `source_document_id` |

Wait — let me re-verify the mark-sent guard. Looking at lines 1494-1495:
```python
if invoice.get("status") != "draft":
    raise HTTPException(status_code=400, detail="Only draft invoices can be marked as sent")
```

This means mark-sent also requires draft status. So the `was_draft` scenario is similar. But the key remaining risk is:
1. **Race condition**: Two concurrent requests could both read `status=draft` and both post
2. **Invoice re-opened**: If an invoice is set back to draft and re-sent
3. **No database-level constraint**: Even if application logic is correct today, nothing prevents duplicate entries at the DB level

---

## 6. Minimal Patch Blueprint — Per P0 Fix

### P0-1: RBAC Bypass Fix

**Root Cause:** RBAC patterns use `/api/...` paths but routes are mounted at `/api/v1/...`

**Patch:** Update ALL patterns in `ROUTE_PERMISSIONS` (middleware/rbac.py) to include `/api/v1/...` variants.

```python
# BEFORE (broken):
r"^/api/hr/payroll.*$": ["org_admin", "admin", "owner"],

# AFTER (fixed — cover both legacy and v1):
r"^/api(/v1)?/hr/payroll.*$": ["org_admin", "admin", "owner"],
```

**Alternative (simpler):** Normalize the path in the RBAC middleware before pattern matching:
```python
# In RBACMiddleware.dispatch(), before get_allowed_roles():
normalized_path = re.sub(r'^/api/v1/', '/api/', path)
allowed_roles = get_allowed_roles(normalized_path)
```

**Recommended approach:** Path normalization (simpler, less error-prone, covers future routes automatically).

**Test cases:**
1. Login as `technician` → GET `/api/v1/hr/payroll/records` → expect 403
2. Login as `viewer` → POST `/api/v1/data-management/...` → expect 403
3. Login as `admin` → GET `/api/v1/hr/payroll/records` → expect 200
4. Login as `accountant` → GET `/api/v1/invoices-enhanced/` → expect 200
5. Cross-org test: User in Org A → access Org B route → expect 403 (already covered by TenantGuard)

**Rollback plan:** Remove the normalization line. No schema changes, no data migration.

---

### P0-2: Zoho Sync Destructive Operations Guard

**Root Cause:** `disconnect-and-purge` endpoint deletes data across all tenants with `delete_many({})`.

**Patch (3 layers):**

**Layer 1 — Tenant scoping:** Add `organization_id` filter to ALL delete operations:
```python
# BEFORE:
result = await db[collection_name].delete_many({})

# AFTER:
org_id = request.state.tenant_org_id  # From TenantGuardMiddleware
result = await db[collection_name].delete_many({"organization_id": org_id})
```

**Layer 2 — Environment gate:** Block in production unless explicitly enabled:
```python
env = os.environ.get("ENVIRONMENT", "development")
if env == "production" and not os.environ.get("ALLOW_PRODUCTION_PURGE"):
    raise HTTPException(status_code=403, detail="Purge operations blocked in production")
```

**Layer 3 — Remove `drop_collection()`:** Replace with scoped `delete_many`:
```python
# BEFORE:
await db.drop_collection(coll)

# AFTER:
await db[coll].delete_many({"organization_id": org_id})
```

**Test cases:**
1. Call disconnect-and-purge as Org A → verify only Org A's zoho data is deleted
2. Call disconnect-and-purge as Org A → verify Org B's data is untouched
3. Call in production environment without `ALLOW_PRODUCTION_PURGE` → expect 403
4. Verify backup collections are only purged for the requesting org

**Rollback plan:** Revert the 3 changes in `zoho_sync.py`. No schema changes.

---

### P0-3: AI Assistant Tenant Scoping

**Root Cause:** AI assistant ignores `organization_id` from auth context.

**Patch:**

1. Extract tenant context from middleware:
```python
@router.post("/diagnose", response_model=AIQueryResponse)
async def ai_diagnose(request: Request, data: AIQueryRequest):
    org_id = getattr(request.state, "tenant_org_id", None)
    user_id = getattr(request.state, "tenant_user_id", None)
    user_role = getattr(request.state, "tenant_user_role", "viewer")
```

2. Use `org_id` in session ID:
```python
session_id=f"ai_{org_id}_{data.portal_type}_{uuid.uuid4().hex[:8]}"
```

3. Get user name from database, not from request body:
```python
if user_id:
    db = get_db()
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "name": 1})
    user_name = user_doc.get("name", "User") if user_doc else "User"
```

**Test cases:**
1. Call `/diagnose` without auth → expect 401
2. Call `/diagnose` as Org A user → verify session_id contains Org A's ID
3. Call `/diagnose` with spoofed `context.user_name` → verify server uses authenticated name
4. Negative: Ensure no DB data from other orgs is accessible

**Rollback plan:** Revert changes in `ai_assistant.py`. No schema changes.

---

### P0-4: Journal Posting Idempotency

**Root Cause:** `create_journal_entry()` has no duplicate check on `(source_document_id, source_document_type)`.

**Patch (2 layers):**

**Layer 1 — Database unique index:**
```python
# In utils/indexes.py or startup:
await db.journal_entries.create_index(
    [("organization_id", 1), ("source_document_id", 1), ("source_document_type", 1)],
    unique=True,
    partialFilterExpression={"source_document_id": {"$ne": ""}},
    name="unique_source_document_per_org"
)
```

**Layer 2 — Application check in `create_journal_entry()`:**
```python
# Before insert, check for existing entry:
if source_document_id:
    existing = await self.journal_entries.find_one({
        "organization_id": organization_id,
        "source_document_id": source_document_id,
        "source_document_type": source_document_type,
        "is_reversed": False
    })
    if existing:
        logger.info(f"Journal entry already exists for {source_document_type} {source_document_id}")
        return True, "Journal entry already exists (idempotent)", existing
```

**Test cases:**
1. Create invoice → send invoice → verify 1 journal entry created
2. Send same invoice again → verify no duplicate (idempotent response)
3. Reverse the journal entry → re-send invoice → verify new entry is created
4. Concurrent sends (2 parallel requests) → verify only 1 entry (index enforces)
5. Verify `post_all_unposted_invoices` batch function still works correctly

**Rollback plan:** Drop the unique index. Revert the check in `create_journal_entry()`.

---

## 7. Architecture Contract Test Plan

### Automated Test Suite (pytest)

```
tests/
├── test_rbac_enforcement.py          # P0-1
├── test_zoho_sync_safety.py          # P0-2
├── test_ai_tenant_isolation.py       # P0-3
├── test_journal_idempotency.py       # P0-4
└── test_cross_tenant_negative.py     # Cross-org validation
```

### Test Cases Per Module

#### `test_rbac_enforcement.py`
```
TEST-RBAC-001: Viewer role → GET /api/v1/hr/payroll/records → 403
TEST-RBAC-002: Technician role → POST /api/v1/data-management/purge → 403
TEST-RBAC-003: Customer role → GET /api/v1/organizations/settings → 403
TEST-RBAC-004: Admin role → GET /api/v1/hr/payroll/records → 200
TEST-RBAC-005: Accountant role → GET /api/v1/invoices-enhanced/ → 200
TEST-RBAC-006: Accountant role → GET /api/v1/hr/payroll/records → 403
TEST-RBAC-007: Technician role → GET /api/v1/tickets/ → 200
TEST-RBAC-008: Public endpoints → no auth → 200 (unchanged)
TEST-RBAC-009: Auth endpoints → no auth → 200 (unchanged)
```

#### `test_zoho_sync_safety.py`
```
TEST-ZOHO-001: Call disconnect-and-purge as Org A → only Org A data deleted
TEST-ZOHO-002: After Org A purge → Org B data intact (cross-org negative)
TEST-ZOHO-003: Production env without ALLOW_PRODUCTION_PURGE → 403
TEST-ZOHO-004: No drop_collection calls remain in code (static analysis)
TEST-ZOHO-005: All delete_many calls have organization_id filter (static analysis)
```

#### `test_ai_tenant_isolation.py`
```
TEST-AI-001: Call /diagnose without auth → 401
TEST-AI-002: Call /diagnose as Org A → response.session contains org_id
TEST-AI-003: user_name from auth context, not request body
TEST-AI-004: If RAG added later → must filter by organization_id (future guard)
```

#### `test_journal_idempotency.py`
```
TEST-JE-001: Post invoice journal entry → 1 entry created
TEST-JE-002: Post same invoice again → no duplicate, idempotent response
TEST-JE-003: Reverse entry → re-post → new entry created (correct behavior)
TEST-JE-004: Unique index exists on (org_id, source_document_id, source_document_type)
TEST-JE-005: Concurrent duplicate inserts → only 1 succeeds (index enforcement)
TEST-JE-006: Batch post_all_unposted_invoices → no duplicates
```

#### `test_cross_tenant_negative.py` (Staging Protocol)
```
Setup: Org A (battwheels internal), Org B (test customer)

TEST-XT-001: Org A user with Org B header → 403
TEST-XT-002: Org A admin → cannot see Org B invoices
TEST-XT-003: Org A admin → cannot delete Org B data via zoho-sync
TEST-XT-004: Org B user → RBAC enforces correct role for Org B
TEST-XT-005: AI query from Org A → cannot access Org B knowledge (when RAG exists)
TEST-XT-006: Journal entry from Org A invoice → scoped to Org A only
```

---

## Staging Validation Protocol

### Two-Org Setup

| Org | Name | Role | Credential |
|-----|------|------|------------|
| **Org A** | Battwheels Internal | `admin@battwheels.in` | `<prod admin>` |
| **Org B** | Test Customer | `dev@battwheels.internal` / `DevTest@123` | Test org |

### Execution Order

1. **Pre-fix baseline**: Run all negative tests above → document current failures
2. **Apply P0-1 (RBAC)** → Run `test_rbac_enforcement.py` + regression on auth flows
3. **Apply P0-2 (Zoho)** → Run `test_zoho_sync_safety.py` + verify no data loss
4. **Apply P0-3 (AI)** → Run `test_ai_tenant_isolation.py`
5. **Apply P0-4 (Journal)** → Run `test_journal_idempotency.py` + trial balance check
6. **Cross-tenant sweep**: Run `test_cross_tenant_negative.py` with both orgs
7. **Regression**: Run existing pytest suite (20/20 must still pass)

### Regression Gates Between Patches

After each P0 fix:
- [ ] All new tests for that fix pass
- [ ] Existing 20/20 pytest suite passes
- [ ] Login flow works for both orgs
- [ ] Dashboard loads for both orgs
- [ ] No 500 errors in backend logs

---

## Summary of Findings

| # | Issue | Severity | Root Cause File | Fix Complexity |
|---|-------|----------|-----------------|----------------|
| P0-1 | RBAC Bypass | **CRITICAL** | `middleware/rbac.py` | LOW — 1 line path normalization |
| P0-2 | Zoho Destructive Ops | **CRITICAL** | `routes/zoho_sync.py` | MEDIUM — scope all filters + env gate |
| P0-3 | AI Tenant Scoping | **HIGH** (not CRITICAL currently) | `routes/ai_assistant.py` | LOW — extract org_id from request.state |
| P0-4 | Journal Idempotency | **CRITICAL** | `services/double_entry_service.py` | MEDIUM — index + application check |

### Additional Finding: Dead Code

`middleware/tenant.py` (`TenantIsolationMiddleware`) is **never mounted** in `server.py`. Only `TenantGuardMiddleware` from `core/tenant/guard.py` is active. This is not a security issue but is misleading during audits.

---

**END OF RECONCILIATION REPORT**
**Next Step:** User review and approval of patch order and approach before any code changes.
