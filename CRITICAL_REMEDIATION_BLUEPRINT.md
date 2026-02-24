# BATTWHEELS OS — CRITICAL REMEDIATION BLUEPRINT
## Structured Remediation Plan for 4 Critical Findings
### Date: 2026-02-24 | Mode: PLANNING ONLY | No Code Modification

---

# ISSUE 1: RBAC v1 BYPASS

## Section 1 — Root Cause Confirmation

**Finding: CONFIRMED — CRITICAL**

The RBAC middleware pattern matching is broken for ALL v1-prefixed routes.

**Root Cause:** `middleware/rbac.py` defines `ROUTE_PERMISSIONS` with patterns like `r"^/api/finance/.*$"`. But the actual route structure is:
- `api_router` has `prefix="/api"` (server.py:134)
- `v1_router` has `prefix="/v1"` (server.py:135)
- `v1_router` is included inside `api_router` (server.py:5415+)
- So the actual URL path becomes `/api/v1/finance/...`

**Fallthrough behavior:** When `get_allowed_roles(path)` returns `None` (no pattern match), the middleware says at line 262:
```python
if allowed_roles is None:
    # Route not in permissions map - allow authenticated users
    return await call_next(request)
```

This means ALL v1 routes are **allowed for any authenticated user regardless of role**.

**Exact affected files:**
- `/app/backend/middleware/rbac.py` — Lines 43-156 (ROUTE_PERMISSIONS dict)
- `/app/backend/server.py` — Lines 134-135 (router prefix definitions), Line 6627 (middleware registration)

**Exact affected routes:** All 110+ inline `@v1_router.*` routes in server.py plus all 1,309 routes in external route files mounted on `v1_router`.

**Attack surface:** A user with `technician` role can:
- Access `/api/v1/finance/dashboard` (finance data)
- Access `/api/v1/hr/payroll-run` (payroll data)
- Access `/api/v1/invoices` (billing data)
- Access `/api/v1/journal-entries` (accounting data)
- Access `/api/v1/organizations/settings` (admin settings)

## Section 2 — Impact Surface Mapping

| Category | Affected |
|----------|----------|
| Dependent modules | ALL 16 modules (every v1 route bypasses RBAC) |
| Affected APIs | ~1,400+ route handlers |
| Background jobs | None (background jobs don't go through middleware) |
| Cross-module deps | RBAC → Auth → TenantGuard (middleware chain) |
| Tenant exposure | All roles within a tenant can access all functions |

**Note:** This is an intra-tenant privilege escalation, NOT a cross-tenant leak. A technician at Org A cannot see Org B's data (tenant guard still works), but can see Org A's payroll.

## Section 3 — Minimal Safe Patch Strategy

**Strategy: Dual-prefix pattern matching**

The safest, most surgical fix: modify `get_allowed_roles()` to normalize paths by stripping `/v1` before matching, OR duplicate each pattern with a `/v1/` variant.

**Option A (Recommended — path normalization):**

In `middleware/rbac.py`, modify `get_allowed_roles()`:
```python
def get_allowed_roles(path: str) -> Optional[List[str]]:
    # Normalize: strip /v1 segment for pattern matching
    normalized = path.replace("/api/v1/", "/api/")
    for pattern, roles in _PERMISSION_PATTERNS:
        if pattern.match(path) or pattern.match(normalized):
            return roles
    return None
```

**Lines changed:** 1 function, ~3 lines. No business logic change. No architecture rewrite. Fully reversible.

**Option B (Alternative — duplicate patterns):**
Add `/api/v1/` variants for every pattern. ~55 new lines. More verbose but explicit.

**Recommended: Option A** — single-point normalization, no pattern duplication.

## Section 4 — Validation Test Plan

**Pre-patch tests:**
1. Confirm technician CAN access `/api/v1/finance/dashboard` (proving the bypass exists)
2. Confirm technician CAN access `/api/v1/hr/employees` (proving the bypass)
3. Document current behavior baseline

**Post-patch tests:**
1. Technician CANNOT access `/api/v1/finance/dashboard` → 403
2. Technician CANNOT access `/api/v1/hr/payroll-run` → 403
3. Technician CAN access `/api/v1/tickets` → 200 (allowed per RBAC map)
4. Manager CAN access `/api/v1/tickets` → 200
5. Owner CAN access `/api/v1/finance/dashboard` → 200
6. Accountant CAN access `/api/v1/finance/dashboard` → 200
7. Public routes (`/api/public/...`) still work without auth
8. Auth routes (`/api/auth/login`) still work
9. Health endpoint still returns 200

**Cross-tenant test:** Not applicable (this is intra-tenant, not cross-tenant)

**Regression test:** Re-run full pytest suite (20 tests)

## Section 5 — Rollback Strategy

**Revert:** Single-line revert in `get_allowed_roles()` — remove the normalization line.
**Detection:** Monitor 403 responses in production. If legitimate users are blocked, logs will show `RBAC DENIED: User X with role 'Y' attempted to access Z`.
**Monitoring:** Add a temporary log line counting RBAC denials per role per hour for 48 hours post-patch.

## Section 6 — Risk Classification

| Dimension | Level | Rationale |
|-----------|-------|-----------|
| Implementation | **LOW** | 3-line change, no business logic |
| Operational | **LOW** | No downtime, hot-reloadable |
| Financial | **MEDIUM** | Unauthorized payroll access currently possible |
| Legal | **MEDIUM** | Data access violation (employee salary visibility) |

## Section 7 — Approval Gate

**Can be applied independently: YES**

No dependency on other fixes. This is a standalone middleware patch. Deploy first as it has the broadest attack surface.

---

# ISSUE 2: AI ASSISTANT ZERO TENANT SCOPING

## Section 1 — Root Cause Confirmation

**Finding: CONFIRMED but SEVERITY DOWNGRADED from CRITICAL to MEDIUM**

After forensic analysis, `ai_assistant.py` is a **stateless LLM chat wrapper** that:
- Makes ZERO database queries
- Makes ZERO vector search calls
- Makes ZERO retrieval calls against org-specific data
- Only calls Gemini with pre-defined system prompts
- Returns generic AI responses

**The original audit flagged "cross-tenant AI context leakage" but no tenant data is accessed or leaked.** The AI assistant simply answers generic EV repair/business questions with no org-specific data retrieval.

**Actual risk:** Structural gap — when org-specific AI features are added (knowledge brain integration, ticket history retrieval), the lack of org_id enforcement becomes critical. The risk is **future-facing**, not current.

**Exact affected file:** `/app/backend/routes/ai_assistant.py` — 190 lines

**Database calls:** 0
**Vector search calls:** 0
**Retrieval logic:** None — pure LLM prompt→response

## Section 2 — Impact Surface Mapping

| Category | Affected |
|----------|----------|
| Dependent modules | None currently (standalone) |
| Affected APIs | 2 endpoints: `POST /ai-assist/diagnose`, `GET /ai-assist/health` |
| Background jobs | None |
| Cross-module deps | None — stateless |
| Tenant exposure | **No data leakage currently.** Risk is structural for future org-specific AI features |

## Section 3 — Minimal Safe Patch Strategy

**Strategy: Add org_id extraction from request state (defensive coding)**

```python
@router.post("/diagnose", response_model=AIQueryResponse)
async def ai_diagnose(request: Request, data: AIQueryRequest):
    # Extract org context (defensive — for future data retrieval)
    org_id = getattr(request.state, "tenant_organization_id", None)
    user_id = getattr(request.state, "tenant_user_id", None)
    
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # ... rest of existing logic unchanged ...
```

**Lines changed:** ~5 lines at the top of the `ai_diagnose` function. No business logic change. No architecture rewrite.

**Additionally:** Add org_id to the session_id for AI chat sessions:
```python
session_id=f"ai_{data.portal_type}_{org_id}_{uuid.uuid4().hex[:8]}"
```

This ensures future AI conversation history is org-scoped.

## Section 4 — Validation Test Plan

**Pre-patch:**
1. Confirm AI endpoint works without org context → 200 (current behavior)
2. Confirm no database queries are made (log analysis)

**Post-patch:**
1. AI endpoint WITHOUT org context → 403
2. AI endpoint WITH valid org context → 200
3. AI response content is unchanged (same quality)
4. Session ID includes org_id (inspect logs)

**Cross-tenant test:**
1. User from Org A gets AI response → response does NOT contain Org B data (already true since no data retrieval)

## Section 5 — Rollback Strategy

**Revert:** Remove the org_id check at top of function. Single block deletion.
**Detection:** Monitor 403 responses on `/api/v1/ai-assist/diagnose`.
**Monitoring:** No special monitoring needed — low risk.

## Section 6 — Risk Classification

| Dimension | Level | Rationale |
|-----------|-------|-----------|
| Implementation | **LOW** | 5-line addition |
| Operational | **LOW** | No behavior change for valid users |
| Financial | **NONE** | No financial data involved |
| Legal | **LOW** | No data leakage currently |

## Section 7 — Approval Gate

**Can be applied independently: YES**

Standalone fix. No dependency on other issues. Lower priority than Issue 1 and 4.

---

# ISSUE 3: ZOHO SYNC UNSCOPED DESTRUCTIVE OPERATIONS

## Section 1 — Root Cause Confirmation

**Finding: CONFIRMED — CRITICAL**

**Exact location:** `/app/backend/routes/zoho_sync.py`
- **Line 863:** `await db[collection_name].delete_many(filter_query)` — Some collections use `{"source": "zoho_books"}` filter, but...
- **Line 866:** `await db[collection_name].delete_many({})` — **EMPTY FILTER** — deletes ALL documents in the collection regardless of tenant
- **Line 880:** `await db.drop_collection(coll)` — Drops backup collections entirely

**Function context:** This is inside `disconnect_and_purge()` (approx line 830), which is called when a user disconnects their Zoho Books integration.

**Collections affected by empty-filter delete (line 866):**
- `books_expenses`, `books_bills`, `books_invoices`, `books_contacts`, `books_items`, `books_payments`, `books_vendors`
- `item_prices`, `item_stock`, `item_stock_locations`, `item_batch_numbers`, `item_serial_numbers`, `item_serial_batches`
- `payments_received`, `payment_history`, `invoice_payments`, `bill_payments`

**Worst-case scenario:** If Org A disconnects Zoho, `delete_many({})` wipes Org B's `invoice_payments`, `payment_history`, and `payments_received` data.

**Attack surface:** Any user with `org_admin`/`admin`/`owner` role who has access to Zoho sync settings can trigger a platform-wide data wipe.

## Section 2 — Impact Surface Mapping

| Category | Affected |
|----------|----------|
| Dependent modules | Invoicing, Payments, Bills, Contacts, Inventory |
| Affected APIs | `POST /api/v1/zoho-sync/disconnect` (single trigger) |
| Background jobs | None |
| Cross-module deps | Payments → Invoices → Journal Entries → Trial Balance |
| Tenant exposure | **ALL TENANTS** — `delete_many({})` has no org filter |

**Cascading financial damage:** If `payments_received` or `invoice_payments` is wiped, the invoice status tracking breaks, the payment-to-AR reconciliation breaks, and the financial dashboard shows incorrect data.

## Section 3 — Minimal Safe Patch Strategy

**Strategy: Add mandatory org_id filter to ALL destructive operations**

**Patch 1 — Scope deletions to requesting organization:**
For every collection in the purge list, change:
```python
# BEFORE (line 866)
result = await db[collection_name].delete_many({})

# AFTER
result = await db[collection_name].delete_many({"organization_id": org_id})
```

**Patch 2 — Add hard guard:**
At the top of `disconnect_and_purge()`, add:
```python
org_id = extract_org_id(request)
if not org_id:
    raise HTTPException(status_code=400, detail="Organization context required for disconnect")
```

**Patch 3 — Drop collection guard:**
```python
# BEFORE (line 880)
await db.drop_collection(coll)

# AFTER — Only drop if collection name is org-prefixed
if coll.startswith(f"_backup_{org_id}"):
    await db.drop_collection(coll)
```

**Lines changed:** ~15 lines. No architecture change. No refactor. Surgical org_id injection into existing filters.

**Alternative (soft delete):** Replace `delete_many` with `update_many` setting `{"zoho_disconnected": True}`. Preserves data for recovery. This is safer but more complex and can be done as a follow-up.

## Section 4 — Validation Test Plan

**Pre-patch:**
1. Confirm `delete_many({})` currently has no org filter (code review — already confirmed)
2. Count documents per collection in both orgs BEFORE test

**Post-patch:**
1. Org A disconnects Zoho → only Org A's Zoho-synced data is deleted
2. Org B's data in ALL collections is UNCHANGED (count verification)
3. Org A's non-Zoho data in shared collections is UNCHANGED
4. Backup collection drop is org-scoped
5. Re-connect Zoho for Org A → sync works normally

**Cross-tenant test (MANDATORY):**
1. Create test data in both orgs
2. Org A disconnects → verify Org B untouched
3. Org B disconnects → verify Org A untouched

**Regression:** Re-run full pytest suite

## Section 5 — Rollback Strategy

**Revert:** Remove org_id filter from delete_many calls (revert to `{}`). Single-pass revert.
**Detection:** If users report missing Zoho data after reconnect, check `sync_logs` collection for purge events.
**Monitoring:** Add alert on `disconnect_and_purge` executions. Log org_id + deleted counts per collection.
**Recovery:** If data is accidentally deleted, restore from MongoDB backup (ensure backup schedule is in place before deploying this fix).

## Section 6 — Risk Classification

| Dimension | Level | Rationale |
|-----------|-------|-----------|
| Implementation | **LOW** | ~15 lines, simple filter injection |
| Operational | **HIGH** | Destructive operation — must test thoroughly |
| Financial | **CRITICAL** | Can wipe payment/invoice records |
| Legal | **CRITICAL** | Data loss across tenants — GDPR/IT Act violation |

## Section 7 — Approval Gate

**Can be applied independently: YES, and MUST be applied BEFORE multi-tenant operation**

This is the single most dangerous code path in the platform. Fix before onboarding any second customer. Bundle with a backup verification step.

---

# ISSUE 4: JOURNAL POSTING NO IDEMPOTENCY

## Section 1 — Root Cause Confirmation

**Finding: CONFIRMED — CRITICAL for financial integrity**

**Root cause:** `DoubleEntryService.create_journal_entry()` at `/app/backend/services/double_entry_service.py` line 442:
```python
await self.journal_entries.insert_one(entry_dict)
```

No check for existing entries with the same `source_document_id` + `source_document_type` before insertion.

**However — partial mitigation exists:** The `post_all_unposted_invoices()` function in `posting_hooks.py` (lines 282-310) DOES check for existing entries:
```python
posted_ids = await service.journal_entries.distinct("source_document_id", {
    "organization_id": organization_id,
    "source_document_type": "invoice"
})
invoices = await db.invoices_enhanced.find({
    "invoice_id": {"$nin": posted_ids}
}).to_list(1000)
```

But this is a **batch reconciliation function**, not a guard on individual posting.

**Duplicate call scenarios:**
1. **API retry:** Frontend retries a failed invoice creation → `post_invoice_journal_entry` called twice
2. **Webhook retry:** Razorpay webhook retries → payment journal entry posted twice (mitigated by Razorpay's idempotency guard, but NOT mitigated for non-Razorpay payments)
3. **Background task restart:** If server restarts during background posting, the task may re-execute
4. **Manual re-trigger:** Admin runs "post unposted invoices" while system is already posting → race condition

**Impact:** Each duplicate journal entry creates phantom debits and credits that throw off the trial balance, P&L, and all financial reports.

## Section 2 — Impact Surface Mapping

| Category | Affected |
|----------|----------|
| Dependent modules | ALL financial reports: Trial Balance, P&L, Balance Sheet, GSTR-1, GSTR-3B |
| Affected APIs | `post_invoice_journal_entry`, `post_payment_received_journal_entry`, `post_bill_journal_entry`, `post_expense_journal_entry`, `post_payroll_run_journal_entry` — 6 posting functions |
| Background jobs | Any background task that calls posting hooks |
| Cross-module deps | Invoice → Journal → Trial Balance → GST Reports → Tally Export |
| Tenant exposure | Per-tenant (duplicate entries affect only the triggering org) |

## Section 3 — Minimal Safe Patch Strategy

**Strategy: Add idempotency check in `create_journal_entry()` using `source_document_id` + `source_document_type`**

**Patch location:** `services/double_entry_service.py`, inside `create_journal_entry()`, before `insert_one()`:

```python
async def create_journal_entry(self, ...):
    # ... existing validation ...
    
    # Idempotency guard: prevent duplicate entries for same source document
    if source_document_id and source_document_type:
        existing = await self.journal_entries.find_one({
            "organization_id": organization_id,
            "source_document_id": source_document_id,
            "source_document_type": source_document_type,
            "is_reversed": {"$ne": True}  # Allow re-posting if original was reversed
        })
        if existing:
            logger.warning(
                f"Idempotency guard: Journal entry already exists for "
                f"{source_document_type} {source_document_id}"
            )
            return True, "Entry already exists", existing
    
    # ... existing insert_one() ...
```

**Additionally:** Create a unique compound index to enforce at DB level:
```python
await db.journal_entries.create_index(
    [("organization_id", 1), ("source_document_id", 1), 
     ("source_document_type", 1)],
    unique=True,
    sparse=True,  # Allow entries without source_document_id
    name="journal_idempotency_guard"
)
```

**Lines changed:** ~15 lines in `create_journal_entry()`, ~5 lines in `utils/indexes.py`. No business logic change. Purely additive guard.

**Debit/credit preservation:** The idempotency check happens BEFORE the balance validation and insert. If a duplicate is detected, the function returns the existing entry. No partial writes, no balance corruption.

## Section 4 — Validation Test Plan

**Pre-patch:**
1. Confirm calling `post_invoice_journal_entry` twice for same invoice creates 2 entries (proving the bug)
2. Count current journal entries
3. Verify trial balance is balanced

**Post-patch:**
1. Call `post_invoice_journal_entry` twice for same invoice → second call returns existing entry, count unchanged
2. Call `post_payment_received_journal_entry` twice for same payment → idempotent
3. Call `post_bill_journal_entry` twice → idempotent
4. Call `post_expense_journal_entry` twice → idempotent
5. Call `post_payroll_run_journal_entry` twice for same period → unique index blocks + idempotency guard
6. NEW invoice → journal entry created normally (1 entry)
7. REVERSED invoice → re-posting allowed (new entry for re-issued invoice)
8. Trial balance remains balanced through all tests
9. `post_all_unposted_invoices()` still works correctly

**Accounting chain validation:**
1. Create invoice → verify 1 journal entry (DR: AR, CR: Revenue + GST)
2. Record payment → verify 1 journal entry (DR: Bank, CR: AR)
3. Trial balance = balanced after both
4. Re-call both posting functions → no change (idempotent)
5. Trial balance still balanced

**Regression:** Full pytest suite

## Section 5 — Rollback Strategy

**Revert:** Remove the `find_one` check block from `create_journal_entry()`. Drop the unique index if created.
**Detection:** If legitimate journal entries fail to post (existing entry returned when none should exist), check the `source_document_id` and `source_document_type` combination.
**Monitoring:** Log all idempotency guard triggers for 48 hours. If >0 triggers, investigate the source of duplicate calls.

## Section 6 — Risk Classification

| Dimension | Level | Rationale |
|-----------|-------|-----------|
| Implementation | **LOW** | ~20 lines, additive guard |
| Operational | **MEDIUM** | New unique index — test with existing data first |
| Financial | **HIGH** | Directly protects accounting integrity |
| Legal | **MEDIUM** | Prevents incorrect financial statements |

## Section 7 — Approval Gate

**Can be applied independently: YES**

No dependency on other fixes. Can and should be deployed alongside or immediately after Issue 1.

---

# EXECUTIVE REMEDIATION PLAN

## Prioritized Fix Order

| Priority | Issue | Reason | Deploy |
|----------|-------|--------|--------|
| **1st** | Issue 1: RBAC v1 Bypass | Broadest attack surface — affects all 1,400+ endpoints | Immediate |
| **2nd** | Issue 3: Zoho Sync Destructive Ops | Most dangerous code path — can wipe all tenant data | Immediate |
| **3rd** | Issue 4: Journal Idempotency | Financial integrity guard — prevents accounting corruption | Same day |
| **4th** | Issue 2: AI Assistant Org Scoping | Defensive coding — no current data leak | Same day or next |

## Estimated Patch Complexity

| Issue | Lines Changed | Files Modified | Estimated Time |
|-------|--------------|----------------|----------------|
| Issue 1 | ~3 lines | 1 file (rbac.py) | 10 minutes |
| Issue 2 | ~5 lines | 1 file (ai_assistant.py) | 10 minutes |
| Issue 3 | ~15 lines | 1 file (zoho_sync.py) | 20 minutes |
| Issue 4 | ~20 lines | 2 files (double_entry_service.py, indexes.py) | 30 minutes |
| **Total** | **~43 lines** | **5 files** | **~70 minutes** |

## Testing Effort Estimate

| Phase | Tests | Time |
|-------|-------|------|
| Pre-patch baseline | 8 manual curl tests | 15 minutes |
| Patch implementation | As per plan above | 70 minutes |
| Post-patch verification | 25+ test cases across all 4 issues | 30 minutes |
| Regression (pytest) | 20 existing tests | 7 minutes |
| Cross-tenant isolation | 5 specific isolation tests | 20 minutes |
| **Total** | **~58 tests** | **~2.5 hours** |

## Deployment Risk Level

| Risk | Level | Mitigation |
|------|-------|-----------|
| Overall deployment risk | **LOW-MEDIUM** | All patches are additive guards (no removal of existing logic) |
| Service disruption | **NONE** | All changes are hot-reloadable |
| Data loss risk | **NONE** | No destructive operations in any patch |
| Rollback complexity | **LOW** | Each patch is independently reversible in <5 minutes |

## Production Safe Release Strategy

1. **Deploy Issue 1 (RBAC)** → Verify with role-specific curl tests → Confirm no legitimate users blocked
2. **Deploy Issue 3 (Zoho)** → Verify with mock disconnect test on dev DB → Confirm org-scoped deletion
3. **Deploy Issue 4 (Journal)** → Create unique index → Verify with duplicate posting test → Check trial balance
4. **Deploy Issue 2 (AI)** → Verify org context extraction → Confirm AI responses unchanged
5. **Run full regression suite** → 20/20 pass required
6. **Monitor logs for 48 hours** → Watch for RBAC denials, idempotency triggers, unexpected 403s

---

**This document is a remediation blueprint only. No code was modified. No schema was changed. No files were touched.**

**All proposed patches are minimal, surgical, reversible, and independently deployable.**
