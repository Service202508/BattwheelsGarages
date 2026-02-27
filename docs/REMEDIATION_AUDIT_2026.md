# REMEDIATION AUDIT 2026 — Battwheels OS

**Audit Date:** 2026-02-28  
**Auditor:** E1 Agent (Emergent Labs)  
**Audit Type:** Read-Only, Comprehensive, Full-Codebase  
**Codebase Snapshot:** Post H-01/H-02 hard-cap sprint + items_enhanced.py 66-endpoint tenant fix  
**Test Suite Baseline:** 322 passed, 0 failed, 51 skipped  

---

## Table of Contents

| Section | Title | Priority Level |
|---------|-------|----------------|
| A | Executive Summary | — |
| B | Scope & Methodology | — |
| C | Org-Level Tenant Isolation (Pattern A/B/C) | HIGH |
| D | User-Level Isolation within Org (Pattern D) | HIGH |
| E | Middleware Chain | STANDARD |
| F | RBAC across All Modules | STANDARD |
| G | Indian Accounting Standards | STANDARD |
| H | GST Compliance | HIGH |
| I | Payroll Statutory Compliance | HIGH |
| J | Core Workflow Chain (10-Step Chain) | DEEPEST |
| K | EFI Architecture | DEEPEST |
| L | Module Completeness (24 Modules) | STANDARD |
| M | Test Coverage | STANDARD |
| N | Verification Gaps & Audit Limitations | — |

---

# Section A — Executive Summary

This audit examined 58,000+ lines of route code and 15,000+ lines of service code across the entire Battwheels OS codebase. The platform is a multi-tenant SaaS ERP for EV service businesses running on FastAPI + MongoDB.

**Critical Findings Count:**

| Severity | Count | Category |
|----------|-------|----------|
| P0 — Critical | 8 | Tenant isolation, RBAC bypass, statutory errors |
| P1 — High | 22 | Isolation gaps, compliance gaps, unbounded queries |
| P2 — Medium | 19 | Mocked features, missing modules, test gaps |
| INFO | 6 | Design notes, intentional tradeoffs |

**Top 3 Critical Discoveries:**

1. **RBAC Bypass (P0):** 20 route files (including ALL `-enhanced` modules) are unmapped in RBAC and fall through to "allow all authenticated users" — a viewer or customer can access invoice, billing, and item management endpoints. (Section F.2)
2. **EFI Tenant Isolation (P0):** 3 core EFI services (`efi_decision_engine.py`, `efi_embedding_service.py`, `embedding_service.py`) have ZERO `organization_id` references while performing extensive cross-tenant database operations. (Section K.2)
3. **Scheduler Cross-Tenant (P0):** `services/scheduler.py` runs all scheduled jobs (invoice overdue marking, recurring invoice generation, payment reminders) without ANY organization_id filtering, affecting data across ALL tenants simultaneously. (Section C.1.5)

---

# Section B — Scope & Methodology

## B.1 Scope

Every file in the following directories was examined:
- `backend/routes/` — 67 Python files
- `backend/services/` — 23 Python files
- `backend/middleware/` — 5 Python files
- `backend/core/tenant/` — 5 Python files
- `backend/utils/` — 5 Python files
- `backend/tests/` — 122 test files (pattern-level analysis)

## B.2 Methodology

1. **Pattern scanning:** `grep -rn` for `organization_id`, `org_id`, `extract_org_id`, `org_query`, `to_list`, `find({})`, `count_documents({})` across all route and service files.
2. **File-level review:** Every service file was checked for DB operations and org_id references. Every route file was checked for its RBAC prefix mapping.
3. **RBAC prefix verification:** Python script executed to test all 67 route prefixes against the compiled RBAC `ROUTE_PERMISSIONS` patterns.
4. **Middleware chain trace:** All 5 middleware files reviewed line-by-line. Execution order verified against Starlette LIFO model.
5. **Compliance gap analysis:** Indian statutory rates, slabs, and requirements compared against code implementations in `hr_service.py`, `tds_service.py`, and `gst.py`.
6. **Workflow chain trace:** 10-step workflow traced through all participating files to verify data flow and isolation.

## B.3 Tools Used

- `grep -rn` for pattern detection
- `wc -l` for file sizing
- Python script for RBAC pattern matching verification
- Direct file reading for line-level analysis

---

# Section C — Org-Level Tenant Isolation (Pattern A/B/C)

## C.1 Pattern A: Services with ZERO organization_id — Direct Cross-Tenant Risk

### C.1.1 CRITICAL — EFI Decision Engine

**File:** `services/efi_decision_engine.py` (471 lines)  
**Severity:** P0  
**org_id references:** 0  

Every database operation is completely unscoped:

| Line | Operation | Collection | Query/Doc |
|------|-----------|------------|-----------|
| `services/efi_decision_engine.py:93` | `find_one` | `efi_decision_trees` | `{"tree_id": tree_id}` — no org_id |
| `services/efi_decision_engine.py:107` | `insert_one` | `efi_decision_trees` | Doc has no org_id field |
| `services/efi_decision_engine.py:135` | `insert_one` | `efi_sessions` | Doc has no org_id field |
| `services/efi_decision_engine.py:153` | `find_one` | `efi_sessions` | `{"session_id": session_id}` — no org_id |
| `services/efi_decision_engine.py:162` | `find_one` | `efi_decision_trees` | `{"tree_id": ...}` — no org_id |
| `services/efi_decision_engine.py:182` | `find_one` | `efi_sessions` | `{"session_id": session_id}` — no org_id |
| `services/efi_decision_engine.py:202` | `find_one` | `efi_sessions` | `{"session_id": session_id}` — no org_id |
| `services/efi_decision_engine.py:206` | `find_one` | `efi_decision_trees` | `{"tree_id": session["tree_id"]}` — no org_id |
| `services/efi_decision_engine.py:290` | `update_one` | `efi_sessions` | `{"session_id": session_id}` — no org_id |
| `services/efi_decision_engine.py:375` | `insert_one` | `learning_queue` | Doc has no org_id field |
| `services/efi_decision_engine.py:404+` | `find` | `learning_queue` | No org_id filter |

**Impact:** Any tenant can read, modify, or complete EFI diagnostic sessions belonging to another tenant by knowing or guessing a `session_id`.

### C.1.2 CRITICAL — EFI Embedding Service

**File:** `services/efi_embedding_service.py` (612 lines)  
**Severity:** P0  
**org_id references:** 0  

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| `services/efi_embedding_service.py:477` | `find` | `failure_cards` | `.to_list(1000)` — no org_id |
| `services/efi_embedding_service.py:482` | `find` | `failure_cards` | No org_id filter |
| `services/efi_embedding_service.py:494` | `find` | `efi_decision_trees` | `.to_list(1000)` — no org_id, global scan |
| `services/efi_embedding_service.py:534` | `find_one` | `failure_cards` | `{"failure_id": failure_id}` — no org_id |
| `services/efi_embedding_service.py:554` | `update_one` | `failure_cards` | No org_id in filter |
| `services/efi_embedding_service.py:575` | `find` | `failure_cards` | `.to_list(1000)` — global scan |

**Impact:** Embedding similarity searches return failure cards from ALL tenants. Embedding updates modify cards globally.

### C.1.3 CRITICAL — Generic Embedding Service

**File:** `services/embedding_service.py` (462 lines)  
**Severity:** P0  
**org_id references:** 0  

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| `services/embedding_service.py:82` | `find_one` | `embedding_cache` | No org_id |
| `services/embedding_service.py:101` | `update_one` | `embedding_cache` | No org_id |
| `services/embedding_service.py:145` | `find_one` | `embedding_cache` | No org_id |
| `services/embedding_service.py:181` | `update_one` | `embedding_cache` | No org_id |
| `services/embedding_service.py:270` | `find` | Parameterized collection | No org_id — searches ANY collection without scoping |
| `services/embedding_service.py:361` | `find` | `failure_cards` | No org_id |
| `services/embedding_service.py:369` | `find` | `failure_cards` | No org_id |
| `services/embedding_service.py:392` | `update_one` | `failure_cards` | No org_id |
| `services/embedding_service.py:416` | `find_one` | `failure_cards` | No org_id |
| `services/embedding_service.py:427` | `update_one` | `failure_cards` | No org_id |

**Impact:** Cross-tenant data leakage through embedding cache. The parameterized collection search at line 270 is especially dangerous as it can search ANY collection without tenant scoping.

### C.1.4 CRITICAL — Event Processor

**File:** `services/event_processor.py` (884 lines)  
**Severity:** P0  
**org_id references:** 0  

All database operations are unscoped:

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| `services/event_processor.py:89` | `update_one` | `efi_events` | No org_id in filter |
| `services/event_processor.py:101` | `update_one` | `efi_events` | No org_id in filter |
| `services/event_processor.py:126` | `find_one` | `tickets` | `{"ticket_id": ticket_id}` only — no org_id |
| `services/event_processor.py:157` | `update_one` | `tickets` | No org_id in filter |
| `services/event_processor.py:224` | `find` | `failure_cards` | No org_id |
| `services/event_processor.py:246` | `find` | `failure_cards` | No org_id |
| `services/event_processor.py:285` | `find` | `failure_cards` | No org_id |
| `services/event_processor.py:321` | `find` | `failure_cards` | No org_id |
| `services/event_processor.py:369` | `find_one` | `technician_actions` | No org_id |
| `services/event_processor.py:370` | `find_one` | `tickets` | No org_id |
| `services/event_processor.py:461` | `insert_one` | `failure_cards` | No org_id in document |
| `services/event_processor.py:513` | `find_one` | `technician_actions` | No org_id |
| `services/event_processor.py:526` | `find_one` | `failure_cards` | No org_id |
| `services/event_processor.py:570` | `update_one` | `failure_cards` | No org_id |
| `services/event_processor.py:623` | `update_one` | `failure_cards` | No org_id |
| `services/event_processor.py:635` | `update_one` | `failure_cards` | No org_id |
| `services/event_processor.py:682` | `insert_one` | `emerging_patterns` | No org_id in document |
| `services/event_processor.py:732` | `aggregate` | `tickets` | No org_id in $match |
| `services/event_processor.py:792` | `aggregate` | `part_usage` | No org_id in $match |
| `services/event_processor.py:865` | `insert_one` | `efi_events` | No org_id in document |
| `services/event_processor.py:869` | `find` | `efi_events` | No org_id |

**Impact:** Event processor handles ticket-created events, failure card creation, pattern detection, and confidence updates — all without tenant scoping. A ticket event from Org A can trigger failure card updates that affect Org B's data.

### C.1.5 CRITICAL — Scheduler Service

**File:** `services/scheduler.py` (350 lines)  
**Severity:** P0  
**org_id references:** 0  

All scheduled jobs run globally without tenant context:

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| `services/scheduler.py:31` | `update_many` | `invoices` | Marks invoices overdue globally — no org_id |
| `services/scheduler.py:53` | `find` | `recurring_invoices` | Finds active recurring invoices globally |
| `services/scheduler.py:64` | `find_one_and_update` | `counters` | Counter increment without org_id |
| `services/scheduler.py:100` | `insert_one` | `invoices` | Inserts invoice without org_id |
| `services/scheduler.py:103` | `update_one` | `contacts` | Updates contact without org_id |
| `services/scheduler.py:142` | `update_one` | `recurring_invoices` | Updates without org_id |
| `services/scheduler.py:172` | `find` | `recurring_expenses` | Finds expenses globally |
| `services/scheduler.py:203` | `insert_one` | `expenses` | Inserts expense without org_id |
| `services/scheduler.py:233` | `update_one` | `recurring_expenses` | Updates without org_id |
| `services/scheduler.py:260` | `find` | `invoices` | Finds overdue invoices globally |
| `services/scheduler.py:283` | `find_one` | `contacts` | Customer lookup without org_id |
| `services/scheduler.py:306` | `insert_one` | `payment_reminders` | Inserts reminder without org_id |
| `services/scheduler.py:309` | `update_one` | `invoices` | Updates invoice without org_id |

**Impact:** Scheduled jobs for overdue marking, recurring invoice generation, and payment reminders affect ALL tenants' data indiscriminately. A recurring invoice from Org A could potentially pick up a counter intended for Org B.

### C.1.6 HIGH — Notification Service

**File:** `services/notification_service.py` (399 lines)  
**Severity:** P1  
**org_id references:** 0  

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| `services/notification_service.py:254` | `insert_one` | `notification_logs` | No org_id in document |
| `services/notification_service.py:316` | `find_one` | `tickets` | `{"ticket_id": ticket_id}` only — no org_id |
| `services/notification_service.py:375` | `find` | `notification_logs` | No org_id in query |
| `services/notification_service.py:398` | `aggregate` | `notification_logs` | No org_id in pipeline |

### C.1.7 HIGH — Search Service

**File:** `services/search_service.py` (438 lines)  
**Severity:** P1  
**org_id references:** 0  

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| `services/search_service.py:230` | `find` | `failure_cards` | No org_id in query |
| `services/search_service.py:237` | `find` | `failure_cards` | No org_id in query |

**Impact:** Text/keyword search across failure cards returns cross-tenant results.

### C.1.8 HIGH — Failure Intelligence Service (Partial)

**File:** `services/failure_intelligence_service.py` (983 lines)  
**Severity:** P1  
**org_id references:** 3 (all optional)  

The `find_matching_cards` method at line 277:
```python
organization_id: Optional[str] = None
...
if organization_id:
    query["organization_id"] = organization_id
```

**Unscoped operations:**

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| `services/failure_intelligence_service.py:530` | `find` | `failure_cards` | Signature match — no org_id |
| `services/failure_intelligence_service.py:557` | `find` | `failure_cards` | Subsystem match — no org_id |
| `services/failure_intelligence_service.py:674` | `find` | `failure_cards` | Keyword match — no org_id |
| `services/failure_intelligence_service.py:728` | `find_one` | `tickets` | `{"ticket_id": ticket_id}` — no org_id |
| `services/failure_intelligence_service.py:881` | `find_one` | `tickets` | No org_id |
| `services/failure_intelligence_service.py:885` | `find_one` | `inventory` | `{"item_id": data.part_id}` — no org_id |
| `services/failure_intelligence_service.py:926` | `count_documents({})` | `failure_cards` | Global count — no org_id |
| `services/failure_intelligence_service.py:927` | `count_documents({"status": "approved"})` | `failure_cards` | Global count — no org_id |
| `services/failure_intelligence_service.py:928` | `count_documents({"status": "draft"})` | `failure_cards` | Global count — no org_id |
| `services/failure_intelligence_service.py:930` | `find` | `failure_cards` | Global top cards — no org_id |

### C.1.9 HIGH — log_item_history helper

**File:** `routes/items_enhanced.py:2827`  
**Severity:** P1  

```python
async def log_item_history(db, item_id: str, action: str, changes: dict, user_name: str):
    history_entry = {
        "history_id": f"IH-{uuid.uuid4().hex[:8].upper()}",
        "item_id": item_id,
        "action": action,
        "changes": changes,
        "user_name": user_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.item_history.insert_one(history_entry)
```

**Issue:** `organization_id` is NOT included in the inserted document. The `get_all_item_history` endpoint at `routes/items_enhanced.py:2839` queries with `organization_id`, but inserted documents lack it, making them invisible per-tenant and globally orphaned.

**Called from 9 sites:**
- `routes/items_enhanced.py:908`
- `routes/items_enhanced.py:1765`
- `routes/items_enhanced.py:2481`
- `routes/items_enhanced.py:2489`
- `routes/items_enhanced.py:2518`
- `routes/items_enhanced.py:2798`
- `routes/items_enhanced.py:2816`
- `routes/items_enhanced.py:2827` (definition)
- `routes/items_enhanced.py:2920`

### C.1.10 INFO — Services with no DB operations (no tenant risk)

| File | Lines | Risk | Reason |
|------|-------|------|--------|
| `services/visual_spec_service.py` | 480 | NONE | Pure computation — no DB calls |
| `services/finance_calculator.py` | ~200 | NONE | Pure calculation — no DB calls |
| `services/llm_provider.py` | ~200 | NONE | External API wrapper — no DB calls |

---

## C.2 Pattern B: Soft-Fail org_query Design

**File:** `utils/database.py:18-35`

```python
def extract_org_id(request) -> Optional[str]:  # Line 18
    org_id = request.headers.get("X-Organization-ID") or request.headers.get("x-organization-id")
    if not org_id:
        org_id = getattr(getattr(request, "state", None), "tenant_org_id", None)
    return org_id

def org_query(org_id: Optional[str], extra: dict = None) -> dict:  # Line 29
    q = {}
    if org_id:
        q["organization_id"] = org_id
    if extra:
        q.update(extra)
    return q
```

**Issue at `utils/database.py:29`:** `org_query` silently drops `organization_id` when `org_id` is `None`. Returns an UNSCOPED query `{}`. Any route that passes `None` org_id gets a global query.

**Mitigating factor:** TenantGuardMiddleware at `core/tenant/guard.py:103` sets `request.state.tenant_org_id` before routes execute. But if any route is on a public path or middleware fails silently (see `middleware/rbac.py:270-274`), the fallback fails.

**Routes using `extract_org_id` + `org_query` (Pattern B risk, ~150+ endpoints):**

| File | Endpoint Count | Line Range |
|------|---------------|------------|
| `routes/reports_advanced.py` | ~14 | Lines 43-660 |
| `routes/efi_guided.py` | ~20 | Lines 90-636 |
| `routes/export.py` | ~6 | Entire file |
| `routes/pdf_templates.py` | ~4 | Entire file |
| `routes/productivity.py` | ~5 | Entire file |
| `routes/fault_tree_import.py` | ~5 | Entire file |
| `routes/composite_items.py` | ~5 | Entire file |
| `routes/serial_batch_tracking.py` | ~8 | Entire file |
| `routes/invoice_automation.py` | ~5 | Entire file |
| `routes/gst.py` | ~10 | Lines 350-1084 |
| `routes/inventory_adjustments_v2.py` | ~20 | Lines 185-779 |
| `routes/technician_portal.py` | ~8 | Entire file |
| `routes/inventory_enhanced.py` | ~15 | Entire file |
| `routes/data_migration.py` | ~5 | Lines 178-516 |
| `routes/amc.py` | ~8 | Entire file |
| `routes/recurring_invoices.py` | ~6 | Entire file |
| `routes/permissions.py` | ~5 | Entire file |
| `routes/master_data.py` | ~3 | Entire file |

---

## C.3 Pattern C: Aggregation pipelines without $match on organization_id

The TenantGuard's `validate_aggregation` method at `core/tenant/guard.py:223` checks for `$match` as the first stage, but routes must explicitly call the guard. Most routes build pipelines manually and bypass the guard.

**Affected files (manual pipeline construction):**

| File:Line | Collection | First $match has org_id? |
|-----------|------------|-------------------------|
| `routes/reports_advanced.py:78` | `invoices` | Uses `org_query` (Pattern B risk) |
| `routes/reports_advanced.py:131` | `bills` | Uses `org_query` |
| `routes/reports_advanced.py:176` | `payments` | Uses `org_query` |
| `services/event_processor.py:732` | `tickets` | NO — global aggregation |
| `services/event_processor.py:792` | `part_usage` | NO — global aggregation |
| `services/notification_service.py:398` | `notification_logs` | NO — global aggregation |

---

## C.4 Unbounded Query Residuals

Despite H-01/H-02 hard-cap sprint, high-limit queries remain:

### `.to_list(10000)` — 11 instances

| File:Line | Collection |
|-----------|------------|
| `routes/gst.py:366` | `invoices_enhanced` |
| `routes/gst.py:373` | `invoices` |
| `routes/gst.py:729` | `invoices_enhanced` |
| `routes/gst.py:761` | `bills_enhanced` |
| `routes/gst.py:766` | `bills` |
| `routes/gst.py:822` | `bills` |
| `routes/gst.py:1084` | `invoices_enhanced` |
| `routes/reports.py:1494` | `inventory` |
| `routes/items_enhanced.py:2551` | `items` |
| `routes/operations_api.py:1273` | Per-collection export |
| `routes/time_tracking.py:535` | `time_entries` |
| `routes/estimates_enhanced.py:1614` | `estimates` |
| `routes/payments_received.py:278` | `payments` |
| `routes/payments_received.py:669` | `payments` |
| `routes/invoice_automation.py:473` | `invoices` |
| `services/double_entry_service.py:1594` | `journal_entries` |

### `.to_list(5000)` — 7 instances

| File:Line | Collection |
|-----------|------------|
| `routes/invoices_enhanced.py:2371` | `invoices_enhanced` |
| `routes/reports.py:1354` | `bills` |
| `routes/reports.py:1594` | `journal_entries` |
| `routes/insights.py:763` | `tickets` |
| `routes/data_migration.py:278` | `customers` |
| `routes/data_migration.py:316` | `vendors` |
| `routes/inventory_adjustments_v2.py:779` | `adjustments` |

### `.to_list(2000)` — 6 instances

| File:Line | Collection |
|-----------|------------|
| `routes/reports_advanced.py:204` | `invoices` |
| `routes/bills_enhanced.py:631` | `bills` |
| `routes/inventory_enhanced.py:1563` | `stock_locations` |
| `routes/inventory_enhanced.py:1567` | `items` |
| `routes/inventory.py:350` | `stock` |
| `routes/inventory_api.py:193` | `stock` |

**Total high-limit queries:** 24+ at 2000+, 7 at 5000, 16+ at 10000

---

## C.5 Unscoped `.find({})` calls

| File:Line | Collection | Risk |
|-----------|------------|------|
| `routes/invoices_enhanced.py:696` | `invoice_templates` | Templates visible cross-tenant |
| `routes/sales_finance_api.py:608` | `chart_of_accounts` | CoA visible cross-tenant |
| `routes/permissions.py:199` | `role_permissions` | Global by design (may be intentional) |
| `routes/platform_admin.py:606` | `feature_flags` | Global by design (admin-only) |
| `routes/data_migration.py:196` | `migration_logs` | No org_id |
| `routes/data_migration.py:233` | `customers` | No org_id |
| `routes/data_migration.py:244` | `vendors` | No org_id |
| `services/efi_embedding_service.py:494` | `efi_decision_trees` | No org_id — global scan |
| `services/efi_embedding_service.py:575` | `failure_cards` | No org_id — global scan |
| `services/data_integrity_service.py:707` | `contacts` | Iterates ALL contacts globally |

---

# Section D — User-Level Isolation within Org (Pattern D)

## D.1 Technician Portal — No Assignment Filtering

**File:** `routes/technician_portal.py`  
**Severity:** P2  
**Prefix:** `/technician`

The technician portal uses `extract_org_id` for tenant scoping but does NOT filter by `assigned_technician_id` when listing tickets. Any technician can see ALL tickets in the organization, not just their assigned ones.

**Evidence:** `routes/technician_portal.py` — endpoint functions use `extract_org_id` but no `assigned_to` or `technician_id` filter in ticket listing queries.

## D.2 HR Self-Service — Inconsistent Enforcement

**File:** `routes/hr.py:142`
```python
def _is_self_only(user: dict) -> bool:
```

This function exists to check if a user should only see their own data. Used in some HR endpoints but NOT consistently applied across all sensitive endpoints (payroll, TDS, Form 16).

**Evidence:** `routes/hr.py` — `_is_self_only` defined at line 142 but not called in payroll calculation (`routes/hr.py:460`) or Form 16 generation endpoints.

## D.3 Activity Logs — Org-Scoped but Not User-Scoped

**File:** `services/activity_service.py`  
**org_id references:** 5 (at lines 104, 122, 143, 236, 244)

Activity logs are org-scoped (correctly) but any org member can see all activity logs for the entire org. No user-level filtering.

## D.4 Document Access — No Role-Based Restriction

**File:** `routes/documents.py`  
Documents are org-scoped but any authenticated org member can access all documents regardless of role or ownership.

## D.5 Customer Portal — Needs customer_id Verification

**File:** `routes/customer_portal.py`  
Customer portal creates separate tokens with `role: "customer"`. Queries should scope by `customer_id` to prevent one customer from seeing another's invoices/tickets within the same org.

**Not fully verified:** Line-by-line audit of customer_portal.py was pattern-level only.

---

# Section E — Middleware Chain

## E.1 Middleware Stack Order

**File:** `server.py:227-231`

```python
app.add_middleware(RateLimitMiddleware)      # 5 — Outermost
app.add_middleware(SanitizationMiddleware)   # 4
app.add_middleware(CSRFMiddleware)           # 3
app.add_middleware(RBACMiddleware)           # 2
app.add_middleware(TenantGuardMiddleware)    # 1 — Innermost (runs first)
```

**Execution order (Starlette LIFO):** TenantGuard → RBAC → CSRF → Sanitization → RateLimit

This ordering is **correct**. TenantGuard runs first (sets `request.state.tenant_*`), RBAC checks role, CSRF validates tokens, Sanitization strips HTML, RateLimit counts.

## E.2 Findings

### E.2.1 CSRF secure flag hardcoded False

**File:** `middleware/csrf.py:102`
```python
secure=False,        # Set True in production behind HTTPS
```
**Severity:** P2 — Should be environment-driven.

### E.2.2 Rate limit in-memory only

**File:** `middleware/rate_limit.py:112`
```python
self._request_counts = {}  # In-memory rate limit tracking
```
**Severity:** P2 — Resets on restart. Per-pod only in multi-pod deployment. Ineffective in production.

### E.2.3 RBAC no-role fallthrough

**File:** `middleware/rbac.py:270-274`
```python
if not user_role:
    logger.info(f"RBAC: No role found for path {path} - letting through for auth check")
    return await call_next(request)
```
**Severity:** P1 — If TenantGuardMiddleware fails to set role, RBAC lets request through.

### E.2.4 Security Headers

**File:** `server.py:238-246`  
All standard headers present: X-Content-Type-Options, X-Frame-Options, HSTS, X-XSS-Protection, Referrer-Policy, CSP.

**CSP note:** `connect-src` allows `https://*.emergentagent.com` — correct for development, should be restricted in production.

### E.2.5 Deprecated middleware/tenant.py

**File:** `middleware/tenant.py`  
Correctly tombstoned with comment at line 15: "Any import from this file should fail loudly." No issue.

---

# Section F — RBAC across All Modules

## F.1 Role Hierarchy

**File:** `middleware/rbac.py:26-38`

```
owner > admin > org_admin > manager > accountant/hr/technician/dispatcher > viewer
customer/fleet_customer (separate hierarchy)
```

## F.2 CRITICAL — 20 Route Files Bypass RBAC

**File:** `middleware/rbac.py:282-285`
```python
if allowed_roles is None:
    # Route not in permissions map - allow authenticated users
    logger.info(f"RBAC: Route {path} (normalized: {normalized_path}) not in map, allowing {user_role}")
    return await call_next(request)
```

**Severity:** P0  
**Root cause:** The RBAC `ROUTE_PERMISSIONS` map at `middleware/rbac.py:42-156` uses simple route prefixes like `^/api/invoices/.*$`, but the actual route files use `-enhanced` suffixes like `/invoices-enhanced`. The regex `^/api/invoices/.*$` does NOT match `/api/invoices-enhanced/...` because the character after `invoices` is `-` not `/`.

**Verified by executing Python regex matching script against all 67 route prefixes.**

**Unmapped route files (open to ALL authenticated users including viewer, customer, technician):**

| # | Route File | Prefix | Lines | Risk |
|---|-----------|--------|-------|------|
| 1 | `routes/invoices_enhanced.py` | `/invoices-enhanced` | 2407 | P0 — Financial |
| 2 | `routes/bills_enhanced.py` | `/bills-enhanced` | 976 | P0 — Financial |
| 3 | `routes/items_enhanced.py` | `/items-enhanced` | 3423 | P0 — Pricing |
| 4 | `routes/contacts_enhanced.py` | `/contacts-enhanced` | 2245 | P0 — PII |
| 5 | `routes/estimates_enhanced.py` | `/estimates-enhanced` | 3011 | P1 — Pricing |
| 6 | `routes/inventory_enhanced.py` | `/inventory-enhanced` | 1734 | P1 — Stock |
| 7 | `routes/sales_orders_enhanced.py` | `/sales-orders-enhanced` | 1557 | P1 — Pricing |
| 8 | `routes/reports_advanced.py` | `/reports-advanced` | 736 | P1 — Analytics |
| 9 | `routes/contact_integration.py` | `/contact-integration` | ~600 | P1 — CRM |
| 10 | `routes/invoice_automation.py` | `/invoice-automation` | ~500 | P1 — Financial |
| 11 | `routes/invoice_payments.py` | `/invoice-payments` | ~400 | P0 — Payments |
| 12 | `routes/vendor_credits.py` | `/vendor-credits` | ~300 | P1 — Financial |
| 13 | `routes/efi_guided.py` | `/efi-guided` | 690 | P2 — EFI |
| 14 | `routes/ai_assistant.py` | `/ai-assist` | 202 | P2 — AI |
| 15 | `routes/expert_queue.py` | `/expert-queue` | 347 | P2 — EFI |
| 16 | `routes/inventory_adjustments_v2.py` | `/inv-adjustments` | 1148 | P1 — Inventory |
| 17 | `routes/serial_batch_tracking.py` | `/serial-batch` | ~400 | P2 — Tracking |
| 18 | `routes/sla.py` | `/sla` | 934 | P2 — Config |
| 19 | `routes/financial_dashboard.py` | `/dashboard/financial` | ~300 | P1 — Analytics |
| 20 | `routes/insights.py` | `/insights` | ~800 | P2 — Analytics |

**Total unprotected endpoints:** ~250+ across these 20 files.

**Impact:** A `viewer` role user, or even a `customer` portal user with a valid JWT, can potentially access ALL invoice CRUD operations, billing data, item pricing, contact PII, and more. The RBAC module's documentation at `middleware/rbac.py:11` says "DENY by default" but the actual implementation is "ALLOW by default" for unmapped routes.

## F.3 RBAC — Correctly Mapped Routes

The following route prefixes ARE correctly mapped:

| Prefix | RBAC Pattern | Roles |
|--------|-------------|-------|
| `/invoices/` | `r"^/api/invoices/.*$"` | org_admin, admin, owner, accountant, manager |
| `/bills/` | `r"^/api/bills/.*$"` | org_admin, admin, owner, accountant |
| `/items/` | `r"^/api/items/.*$"` | org_admin, admin, owner, manager, accountant, technician |
| `/contacts/` | `r"^/api/contacts/.*$"` | org_admin, admin, owner, manager, dispatcher |
| `/estimates/` | `r"^/api/estimates/.*$"` | org_admin, admin, owner, manager, technician, dispatcher |
| `/inventory/` | `r"^/api/inventory/.*$"` | org_admin, admin, owner, manager, accountant |
| `/hr/` | `r"^/api/hr/.*$"` | org_admin, admin, owner, hr |
| `/gst/` | `r"^/api/gst/.*$"` | org_admin, admin, owner, accountant |
| `/tickets/` | `r"^/api/tickets/.*$"` | org_admin, admin, owner, manager, technician, dispatcher |
| `/payments` | `r"^/api/payments.*$"` | org_admin, admin, owner, accountant |

Note: `/payments` pattern uses `payments.*` (no `/` after `payments`) which DOES match `/payments-received/...`. This is the ONLY enhanced route that is accidentally covered.

---

# Section G — Indian Accounting Standards

## G.1 Double-Entry Accounting System

**File:** `services/double_entry_service.py` (1649 lines)

### G.1.1 Implemented Features

| Feature | Status | File:Line |
|---------|--------|-----------|
| Chart of Accounts (per-org) | ✓ | `services/double_entry_service.py:235` |
| Journal entry create with debit/credit validation | ✓ | `services/double_entry_service.py:267` |
| Trial Balance | ✓ | `services/double_entry_service.py:1161` |
| Profit & Loss statement | ✓ | `services/double_entry_service.py:1300` |
| Balance Sheet | ✓ | `services/double_entry_service.py:1390` |
| Account Ledger with running balance | ✓ | `services/double_entry_service.py:1539` |
| Posting hooks (invoice, bill, payment, expense, payroll) | ✓ | `services/posting_hooks.py:30-324` |
| Entry reversal | ✓ | `services/double_entry_service.py:415` |
| Decimal precision using Python `Decimal` | ✓ | `services/double_entry_service.py:207` |

### G.1.2 Compliance Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No Indian fiscal year (April-March) | P1 | P&L and Balance Sheet at `services/double_entry_service.py:1300` and `:1390` accept arbitrary date ranges. No concept of fiscal year boundaries |
| No year-end closing process | P1 | No mechanism to carry forward opening balances to next fiscal year |
| No multi-currency support | P2 | All amounts assumed INR. No currency field or conversion |
| No depreciation schedules | P2 | No asset depreciation (SLM/WDV as per Companies Act 2013) |
| No accrual accounting | P2 | No accrual/deferral journal entries |
| No TDS payable account per section | P1 | TDS calculated (`services/tds_service.py`) but not posted to section-specific TDS payable accounts (194A, 194C, etc.) |
| No bank reconciliation integration | P2 | Banking module at `routes/banking.py` is separate from double-entry journal system |
| No audit trail for journal modifications | P1 | Journal entries can be created/reversed at `services/double_entry_service.py:267,415` but no tamper-evident modification log |
| No period lock enforcement | P1 | `routes/period_locks.py:18` exists but `services/posting_hooks.py` does NOT check period locks before posting. Invoice dated in locked period still posts |

---

# Section H — GST Compliance

## H.1 GST Module Overview

**File:** `routes/gst.py` (1146 lines)

### H.1.1 Implemented Features

| Feature | Status | File:Line |
|---------|--------|-----------|
| GSTIN validation (format, state code, PAN) | ✓ | `routes/gst.py:104-131` |
| CGST/SGST/IGST calculation | ✓ | `routes/gst.py:133-168` |
| GSTR-1 report (JSON, Excel, PDF) | ✓ | `routes/gst.py:315-505` |
| GSTR-3B report (JSON, Excel, PDF) | ✓ | `routes/gst.py:695-975` |
| HSN/SAC summary | ✓ | `routes/gst.py:975-1050` |
| Indian state code mapping (37 states + UTs) | ✓ | `routes/gst.py:48-103` |
| Reverse Charge Mechanism in GSTR-3B | PARTIAL | `routes/gst.py:818-840` |
| Organization GST settings | ✓ | Multiple endpoints |

### H.1.2 GSTIN Validation Gaps

**File:** `routes/gst.py:104-131`

| Check | Status | Detail |
|-------|--------|--------|
| Length = 15 | ✓ | Line 109 |
| State code (digits 1-2) | ✓ | Line 112 |
| PAN format (digits 3-12) | ✓ | Line 118 |
| Entity code (digit 13) | ✓ | Line 121 |
| **Checksum digit (digit 15)** | **MISSING** | Line 128 only checks `isalnum()`. The Luhn mod-36 checksum algorithm for the 15th character is NOT implemented |

### H.1.3 GST Rate Gaps

**File:** `routes/gst.py:99`
```python
GST_RATES = [0, 5, 12, 18, 28]
```

**Missing rates:**
- 0.25% (rough precious/semi-precious stones)
- 3% (gold, silver, platinum)
- Cess rates (1%, 3%, 5%, additional cess on luxury goods)
- Compensation Cess

### H.1.4 GSTR-1 Report Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No B2C (Small) segregation | P1 | All invoices treated as B2B. B2C invoices < ₹2.5L per state not segregated per Table 7 |
| No credit note/debit note section | P1 | CDN section (Table 9A) for credit notes not generated |
| No advance payment section | P2 | Table 11A (advances received) not tracked |
| No amendment section | P2 | Table 9 (amendments to previous returns) not generated |
| No HSN summary by GST rate | P1 | HSN summary at `routes/gst.py:975` exists but doesn't split by rate |
| No e-Invoice IRN integration | P2 | Mentioned in module docstring but not implemented |
| Not GST portal JSON format | P1 | Report format is custom, not matching `gst.gov.in` JSON upload schema |
| Unbounded queries `.to_list(10000)` | P1 | `routes/gst.py:366,373,729,761,766,822,1084` — 7 instances pull ALL invoices for a month |

### H.1.5 GSTR-3B Report Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No ITC categorization | P1 | Input Tax Credit not split into eligible/ineligible/reversed per Table 4 |
| No inter-state vs intra-state B2C split | P1 | Table 3.2 requires this split — not implemented |
| No exempt/nil-rated/non-GST segregation | P2 | Table 5 not populated |
| RCM basic only | P2 | `routes/gst.py:818-840` checks `reverse_charge: True` flag only, doesn't validate RCM categories |
| No previous period adjustment | P2 | Cannot incorporate tax adjustments from prior months |

### H.1.6 Missing GST Features

| Feature | Status | Impact |
|---------|--------|--------|
| GSTR-2A/2B reconciliation | NOT IMPLEMENTED | Cannot reconcile purchase data with supplier returns |
| E-way bill generation | NOT IMPLEMENTED | Required for goods transport > ₹50,000 |
| PMT-06 payment challan | NOT IMPLEMENTED | Cannot generate payment challans |
| Composition scheme | NOT IMPLEMENTED | No support for composition dealers |
| GSTR-9 annual return | NOT IMPLEMENTED | No annual return generation |
| Multi-GSTIN per org | NOT IMPLEMENTED | Organizations with multiple branch GSTINs not supported |
| ITC register/ledger | NOT IMPLEMENTED | No ITC ledger maintenance |

---

# Section I — Payroll Statutory Compliance

## I.1 Payroll Module Files

- `routes/hr.py` (1879 lines)
- `services/hr_service.py` (~600 lines)
- `services/tds_service.py` (826 lines)
- `services/posting_hooks.py` (payroll journal posting)

## I.2 TDS (Income Tax) — Most Complete Component

**File:** `services/tds_service.py` (826 lines)

| Feature | Status | File:Line |
|---------|--------|-----------|
| New Regime slabs (FY 2024-25) | ✓ | `services/tds_service.py:31` |
| Old Regime slabs | ✓ | `services/tds_service.py:305` |
| Standard deduction | ✓ | `services/tds_service.py:31` |
| HRA exemption calculation | ✓ | `services/tds_service.py:115` |
| Section 80C (max ₹1.5L) | ✓ | `services/tds_service.py:34-35` |
| Section 80D (medical insurance) | ✓ | `services/tds_service.py:37-40` |
| Section 80CCD(1B) NPS (max ₹50K) | ✓ | `services/tds_service.py:43` |
| Surcharge calculation | ✓ | `services/tds_service.py:235` |
| PAN validation | ✓ | `services/tds_service.py:87` |
| Monthly TDS with YTD adjustment | ✓ | `services/tds_service.py:417` |
| Form 16 data generation (Part A + B) | ✓ | `services/tds_service.py:518` |
| Payroll journal entries | ✓ | `services/tds_service.py:669` |
| org_id present | ✓ | `services/tds_service.py:558,674,784` |

### I.2.1 TDS Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| Tax slabs for FY 2024-25 only | P2 | Need annual update mechanism for new FY slabs. No configurable slab system |
| 26AS reconciliation | P2 | Cannot verify TDS deposits against Form 26AS |
| Form 16 certificate number | P1 | Certificate number and TAN validation not robust |
| Section 80E/80G/80TTA not listed | P2 | Education loan interest, donations, savings interest deductions missing |

## I.3 PF (Provident Fund) Compliance

**File:** `services/hr_service.py:460-496`

```python
pf_deduction = basic * 0.12  # 12% of basic                    # Line 460
esi_deduction = gross * 0.0075 if gross <= 21000 else 0          # Line 461
professional_tax = 200  # Standard PT                            # Line 462
...
"pf_employer": round(employer_pf, 2),                            # Line 492
"esi_employer": round(employer_esi, 2)                           # Line 493
"ctc": round(gross + employer_pf + employer_esi, 2)              # Line 496
```

| Gap | Severity | File:Line | Detail |
|-----|----------|-----------|--------|
| PF ceiling not enforced | P1 | `services/hr_service.py:460` | PF calculated on FULL basic. Should cap at ₹15,000/month basic for employer contribution. Employee PF can be on full basic, but employer's share (and pension split) MUST cap at ₹15,000 |
| No pension fund (EPS) split | P1 | `services/hr_service.py:460` | Of 12% employer contribution, 8.33% goes to EPS (capped at ₹15,000 wage). Not split |
| No PF admin charges | P1 | Not found | Employer pays 0.5% admin + 0.5% EDLI. Not calculated anywhere |
| No PF ECR generation | P2 | Not found | Cannot generate Electronic Challan-cum-Return for EPFO portal |
| No UAN integration | P2 | Not found | No link to Universal Account Number system |
| VPF not supported | P2 | Not found | Employee cannot opt for > 12% voluntary PF |

## I.4 ESI (Employee State Insurance) Compliance

| Gap | Severity | File:Line | Detail |
|-----|----------|-----------|--------|
| ESI employer rate MISSING | P0 | `services/hr_service.py:461` | Code calculates employee ESI at 0.75% but does NOT calculate employer ESI at 3.25% in the deduction section. The `employer_esi` variable IS used at line 493 but its calculation is not visible — needs verification of where `employer_esi` is defined |
| ESI wage ceiling hardcoded | P1 | `services/hr_service.py:461` | ₹21,000 is correct for 2024-25 but hardcoded. Should be configurable |
| No ESI contribution register | P2 | Not found | Cannot generate ESI return forms |

## I.5 Professional Tax Compliance

| Gap | Severity | File:Line | Detail |
|-----|----------|-----------|--------|
| Flat ₹200 for ALL states | P0 | `services/hr_service.py:462` | Professional Tax varies by state: Maharashtra (slab: ₹0-₹2,500), Karnataka (₹200), Telangana (slab: ₹0-₹2,500), Gujarat (slab: ₹0-₹2,400), AP (slab), Tamil Nadu (slab: ₹0-₹2,500), etc. Multiple states have monthly slabs based on gross salary |
| No state-wise PT slabs | P0 | Not found | No state-based configuration for PT. Must support at least 15 state-specific slab structures |
| No PT exemption handling | P2 | Not found | Some states exempt PT in certain months (e.g., February exemption in some states) |

## I.6 Missing Payroll Features

| Feature | Status | Severity | Detail |
|---------|--------|----------|--------|
| Gratuity calculation | NOT IMPLEMENTED | P2 | Required for 5+ year employees. Formula: (15 × last drawn salary × years) / 26 |
| Bonus (Payment of Bonus Act) | NOT IMPLEMENTED | P2 | Statutory bonus 8.33%-20% of basic+DA for eligible employees |
| LTA/LTC exemption | NOT IMPLEMENTED | P2 | Leave Travel Allowance exemption tracking |
| Reimbursement management | NOT IMPLEMENTED | P2 | No expense reimbursement through payroll |
| Loan/advance deduction | NOT IMPLEMENTED | P2 | No salary advance or loan EMI deduction |
| Full & Final settlement | NOT IMPLEMENTED | P2 | No FnF process for exiting employees |
| Arrears calculation | NOT IMPLEMENTED | P2 | No backdated salary revision processing |
| Monthly pay slip PDF | NOT IMPLEMENTED | P2 | Form 16 exists but monthly pay slip not generated |
| PF/ESI due date tracking | NOT IMPLEMENTED | P1 | No tracking of deposit deadlines (15th of next month for PF, 15th for ESI) |

---

# Section J — Core Workflow Chain (10-Step Chain)

## J.1 The 10-Step Workflow

```
1. Ticket Creation → 2. EFI Diagnosis → 3. Estimate Generation → 4. Customer Approval
→ 5. Parts Allocation → 6. Work Execution → 7. Work Completion → 8. Invoice Generation
→ 9. Payment Collection → 10. Journal Entry / Accounting
```

## J.2 Step 1: Ticket Creation

**Files:** `routes/tickets.py` (prefix `/tickets`), `services/ticket_service.py` (1205 lines)

**Implementation:**
- Ticket creation via `TicketService.create_ticket()` at `services/ticket_service.py:167`
- Generates unique `ticket_id` (UUID-based)
- Vehicle lookup by registration number
- SLA config loaded per organization
- Event emission: `TICKET_CREATED` event dispatched

**Findings:**

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J2-1 | P1 | `services/ticket_service.py:120` | `organization_id: Optional[str] = None` — if not provided, ticket is created WITHOUT org scoping |
| J2-2 | P2 | Not found | No duplicate ticket detection (same vehicle + same complaint can create duplicates) |
| J2-3 | P2 | Not found | No human-readable ticket number sequence per org (UUID-based only) |
| J2-4 | INFO | `routes/public_tickets.py:176` | Public ticket creation bypasses tenant context — by design. Org reference injected from form |

## J.3 Step 2: EFI Diagnosis

**Files:** `services/efi_decision_engine.py` (471), `routes/efi_guided.py` (690), `services/efi_embedding_service.py` (612), `services/failure_intelligence_service.py` (983), `services/ai_guidance_service.py` (1069)

**Implementation:**
EFI is a multi-layered AI system:
- Layer 1: Failure card matching via embedding similarity
- Layer 2: Decision tree guided diagnostics
- Layer 3: AI-powered guidance (LLM integration)
- Layer 4: Expert escalation queue
- Layer 5: Continuous learning from resolved tickets

**Findings:**

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J3-1 | P0 | `services/efi_decision_engine.py:*` | ZERO org_id — all 471 lines. Sessions, trees, learning items accessible cross-tenant. See Section C.1.1 |
| J3-2 | P0 | `services/efi_embedding_service.py:*` | ZERO org_id — similarity searches return cross-tenant results. See Section C.1.2 |
| J3-3 | P0 | `services/embedding_service.py:*` | ZERO org_id — cache and card queries unscoped. See Section C.1.3 |
| J3-4 | P0 | `services/event_processor.py:*` | ZERO org_id — event processing crosses tenants. See Section C.1.4 |
| J3-5 | P1 | `services/failure_intelligence_service.py:277` | `organization_id: Optional[str] = None` in core matching function — silently unscoped when None |
| J3-6 | P1 | `services/model_aware_ranking_service.py:60` | `organization_id: Optional[str] = None` — ranking uses `$or` with `[{org_id}, {None}]` returning global results |
| J3-7 | P1 | `services/ai_assist_service.py:69` | `organization_id = request.organization_id or "global"` — defaults to global |
| J3-8 | P1 | `routes/failure_intelligence.py:114` | `org_id = request.headers.get("X-Organization-ID") or None` — only 2 lines reference org_id across 33 endpoint functions. Remaining 31 endpoints don't pass org_id to service |
| J3-9 | P1 | `services/efi_decision_engine.py:309` | `get_suggested_estimate` generates estimate template from session but doesn't include org_id in the estimate data |

**Data flow showing cross-tenant risk:**

```
Ticket Created (Org A)
  → event_processor.handle_ticket_created (NO ORG_ID)
    → failure_intelligence_service.find_matching_cards (org_id=None → global search)
      → embedding_service.find_similar (NO ORG_ID → searches ALL failure cards)
        → Returns cards from Org A, B, C, D mixed together
    → efi_embedding_service.find_similar_failure_cards (NO ORG_ID)
      → Also returns cross-tenant cards
  → Decision tree loaded from efi_decision_trees (NO ORG_ID)
  → Session created in efi_sessions (NO ORG_ID)
```

## J.4 Step 3: Estimate Generation

**Files:** `routes/estimates_enhanced.py` (3011 lines), `services/ticket_estimate_service.py`

**Implementation:**
- Estimate creation from ticket or standalone
- Line item management (add/update/delete)
- Status workflow: Draft → Sent → Approved → Declined/Expired
- PDF generation
- Public estimate viewing (shareable link)

**Findings:**

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J4-1 | P1 | `routes/estimates_enhanced.py:60` | `query["organization_id"] = org_id` — this is the ONLY place org_id is set for list queries. All other query construction relies on `ticket_estimate_service` |
| J4-2 | P1 | `routes/estimates_enhanced.py:2210` | Estimate→Invoice conversion: `org_id = estimate.get("organization_id")`. If legacy estimate lacks org_id, conversion creates unscoped invoice |
| J4-3 | P0 | Section F.2 | Route prefix `/estimates-enhanced` is NOT mapped in RBAC — open to all authenticated users |

## J.5 Step 4: Customer Approval

**Implementation:** Estimate status transition from `sent` → `approved`/`declined`

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J5-1 | INFO | `routes/public_tickets.py:614` | Customer approval via shared link — no auth required. Security by UUID obscurity |
| J5-2 | P2 | Not found | No digital signature or cryptographic consent record |
| J5-3 | P2 | Not found | No server-side enforcement of estimate expiry — expired estimates can still be approved |
| J5-4 | PARTIAL | `routes/estimates_enhanced.py:2132` | Sending mocked — "Send estimate to customer (mocked)" |

## J.6 Step 5: Parts Allocation

**Files:** `services/inventory_service.py` (553 lines), `routes/inventory_enhanced.py` (1734 lines)

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J6-1 | P1 | `services/inventory_service.py:176` | `organization_id: str = None` in `use_allocation` — optional. Falls back to allocation's org_id, but if allocation lacks org_id, scoping fails |
| J6-2 | P2 | Not found | No automatic allocation trigger from estimate approval. Manual step required — workflow chain broken |
| J6-3 | ✓ | `services/inventory_service.py:285` | COGS posting on allocation use correctly creates journal entries |

## J.7 Step 6: Work Execution

**File:** `services/ticket_service.py` (method at ~line 756)

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J7-1 | P2 | Not found | No cost tracking for work-in-progress (labour rate × hours) |
| J7-2 | P1 | Not found | No validation that technician starting work is the one assigned to the ticket |

## J.8 Step 7: Work Completion

**File:** `services/ticket_service.py` (method at ~line 812)

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J8-1 | P1 | `services/ticket_service.py:632` | `_update_efi_platform_patterns` feeds completion data to EFI system which has ZERO tenant isolation |
| J8-2 | P2 | Not found | No mandatory quality checklist before completion |
| J8-3 | P2 | Not found | No customer sign-off workflow |

## J.9 Step 8: Invoice Generation

**Files:** `routes/invoices_enhanced.py` (2407 lines)

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J9-1 | P0 | Section F.2 | Route prefix `/invoices-enhanced` is NOT mapped in RBAC |
| J9-2 | ✓ | `services/posting_hooks.py:30` | Double-entry posting on invoice creation works correctly |
| J9-3 | P1 | `routes/invoices_enhanced.py:2371` | `.to_list(5000)` for export — unbounded |
| J9-4 | P2 | Not found | E-invoice IRN generation is placeholder only |

## J.10 Step 9: Payment Collection

**Files:** `routes/payments_received.py` (1380 lines), `routes/razorpay.py`

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J10-1 | P1 | `routes/payments_received.py:278,669` | `.to_list(10000)` — unbounded export queries |
| J10-2 | ✓ | `services/posting_hooks.py:65` | Double-entry posting on payment works correctly |
| J10-3 | P2 | Not found | No advance payment tracking (advance against invoice) |
| J10-4 | P2 | Not found | No TDS deduction by customer tracking |
| J10-5 | P1 | `routes/razorpay.py:532` | Razorpay webhook processes payments. Webhook signature verification exists at line 402-421 but org_id validation for the payment mapping relies on invoice lookup only |

## J.11 Step 10: Journal Entry / Accounting

**Files:** `services/double_entry_service.py` (1649 lines), `services/posting_hooks.py`

| ID | Severity | File:Line | Detail |
|----|----------|-----------|--------|
| J11-1 | ✓ | `services/double_entry_service.py:267` | Journal entry creation requires `organization_id` |
| J11-2 | P1 | `services/posting_hooks.py:*` | No period lock check before journal posting. `routes/period_locks.py:18` exists but posting_hooks.py never consults it |
| J11-3 | P1 | `services/double_entry_service.py:1594` | `.to_list(10000)` for ledger query |
| J11-4 | P2 | `services/posting_hooks.py:294` | `post_all_unposted_invoices` exists but has no automated trigger/scheduler |

## J.12 Chain Integrity Summary

| Link | Status | Gap |
|------|--------|-----|
| 1→2 Ticket → EFI | ✓ LINKED | EFI lacks tenant isolation (P0) |
| 2→3 EFI → Estimate | WEAK | `get_suggested_estimate` at `efi_decision_engine.py:309` lacks org_id |
| 3→4 Estimate → Approval | PARTIAL | Notification mocked at `estimates_enhanced.py:2132` |
| 4→5 Approval → Allocation | **BROKEN** | No automatic trigger. Manual intervention required |
| 5→6 Allocation → Work | **BROKEN** | No automatic trigger. Manual intervention required |
| 6→7 Work → Completion | ✓ LINKED | Status transition works |
| 7→8 Completion → Invoice | PARTIAL | Can create invoice from ticket but not automatic |
| 8→9 Invoice → Payment | ✓ LINKED | Payment allocation works |
| 9→10 Payment → Journal | ✓ LINKED | Posting hooks work. Period lock not enforced |

---

# Section K — EFI Architecture

## K.1 System Size

**Total EFI codebase:** 11,492 lines across 19 files

### K.1.1 Service Layer

| Component | File | Lines | org_id Status |
|-----------|------|-------|--------------|
| EFI Decision Engine | `services/efi_decision_engine.py` | 471 | **ZERO** — 0 refs |
| EFI Embedding Service | `services/efi_embedding_service.py` | 612 | **ZERO** — 0 refs |
| Generic Embedding Service | `services/embedding_service.py` | 462 | **ZERO** — 0 refs |
| Event Processor | `services/event_processor.py` | 884 | **ZERO** — 0 refs |
| Failure Intelligence Service | `services/failure_intelligence_service.py` | 983 | **PARTIAL** — 3 refs (all Optional) |
| Continuous Learning | `services/continuous_learning_service.py` | 524 | **PARTIAL** — 8 refs |
| Model-Aware Ranking | `services/model_aware_ranking_service.py` | 413 | **PARTIAL** — 4 refs (Optional) |
| Expert Queue Service | `services/expert_queue_service.py` | 642 | ✓ — 10 refs |
| Knowledge Store | `services/knowledge_store_service.py` | 465 | ✓ — 14 refs |
| AI Assist Service | `services/ai_assist_service.py` | 515 | **PARTIAL** — fallback to "global" |
| AI Guidance Service | `services/ai_guidance_service.py` | 1069 | ✓ — 12+ refs |
| Search Service | `services/search_service.py` | 438 | **ZERO** — 0 refs |
| EFI Seed Data | `services/efi_seed_data.py` | 1385 | N/A (seed script) |

### K.1.2 Route Layer

| Component | File | Lines | org_id Status |
|-----------|------|-------|--------------|
| EFI Guided | `routes/efi_guided.py` | 690 | ✓ — `extract_org_id` on every endpoint |
| EFI Intelligence | `routes/efi_intelligence.py` | 604 | ✓ — `organization_id` in queries |
| Failure Intelligence | `routes/failure_intelligence.py` | 683 | **MINIMAL** — 2 lines (114, 125) across 33 functions |
| Failure Cards | `routes/failure_cards.py` | 264 | ✓ — `ctx.org_id` |
| Knowledge Brain | `routes/knowledge_brain.py` | 532 | ✓ — `org_id` consistently |
| Expert Queue | `routes/expert_queue.py` | 347 | ✓ — `org_id` |
| AI Assistant | `routes/ai_assistant.py` | 202 | **MINIMAL** — 1 ref (line 47), delegates to service |
| AI Guidance | `routes/ai_guidance.py` | 629 | ✓ — `org_id` consistently |

## K.2 EFI Collections — TenantGuard Registration

**File:** `core/tenant/guard.py:37-83` (TENANT_COLLECTIONS)  
**File:** `core/tenant/guard.py:86-93` (GLOBAL_COLLECTIONS)

| Collection | Used By | Has org_id in docs? | In TENANT_COLLECTIONS? | In GLOBAL_COLLECTIONS? | Status |
|------------|---------|---------------------|----------------------|----------------------|--------|
| `failure_cards` | Multiple | MIXED | YES (also MIXED_SCOPE at line 98) | NO | Declared tenant but queried without org_id by 4 services |
| `efi_decision_trees` | Decision engine | NO | **NO** | **NO** | **MISSING from both lists** |
| `efi_sessions` | Decision engine | NO | **NO** | **NO** | **MISSING from both lists** |
| `learning_queue` | Decision engine, Learning service | PARTIAL | **NO** | **NO** | **MISSING from both lists** |
| `embedding_cache` | Embedding service | NO | **NO** | **NO** | **MISSING from both lists** |
| `efi_events` | Event processor | NO | **NO** | **NO** | **MISSING from both lists** |
| `emerging_patterns` | Event processor | NO | **NO** | **NO** | **MISSING from both lists** |
| `symptoms` | Failure intelligence | UNKNOWN | **NO** | **NO** | **MISSING from both lists** |
| `knowledge_relations` | Failure intelligence | UNKNOWN | **NO** | **NO** | **MISSING from both lists** |
| `ai_queries` | AI assist | YES | **NO** | **NO** | **MISSING from both lists** |
| `ai_escalations` | AI assist | YES | **NO** | **NO** | **MISSING from both lists** |
| `knowledge_articles` | Knowledge store | YES | YES (also MIXED_SCOPE) | NO | ✓ |
| `knowledge_embeddings` | Knowledge store | YES | YES | NO | ✓ |
| `ai_guidance_snapshots` | AI guidance | YES | YES | NO | ✓ |
| `ai_guidance_feedback` | AI guidance | YES | YES | NO | ✓ |
| `expert_escalations` | Expert queue | YES | YES | NO | ✓ |
| `technician_actions` | Failure intelligence | YES | YES | NO | ✓ |
| `part_usage` | Failure intelligence | YES | YES | NO | ✓ |
| `model_risk_alerts` | Model ranking | YES | YES | NO | ✓ |
| `structured_failure_cards` | EFI intelligence | YES | YES | NO | ✓ |

**Total collections missing from guard lists: 11**

This means the TenantGuard middleware CANNOT auto-inject org_id for queries against these 11 collections, even if services start passing tenant context.

## K.3 Failure Card Matching Data Flow (Detail)

```
1. Ticket created with symptoms/description
   → routes/efi_guided.py calls service
   
2. failure_intelligence_service.find_matching_cards()
   (services/failure_intelligence_service.py:277)
   org_id is Optional[str] = None
   
   Stage 1: Signature matching
   → services/failure_intelligence_service.py:530
   → db.failure_cards.find(signature_query) — NO ORG_ID
   
   Stage 2: Subsystem + vehicle matching
   → services/failure_intelligence_service.py:557
   → db.failure_cards.find(subsystem_query) — NO ORG_ID
   
   Stage 3: Semantic embedding search
   → embedding_service.find_similar()
   → services/embedding_service.py:270
   → db[collection].find(query) — PARAMETERIZED COLLECTION, NO ORG_ID
   → Searches ANY collection without scoping
   
   Stage 4: efi_embedding_service.find_similar_failure_cards()
   → services/efi_embedding_service.py:462
   → services/efi_embedding_service.py:477: db.failure_cards.find(query).to_list(1000) — NO ORG_ID
   
   Stage 5: Keyword fallback
   → services/failure_intelligence_service.py:674
   → db.failure_cards.find(keyword_query) — NO ORG_ID

3. Results merged across all 5 stages
   → ALL stages return cards from ALL tenants
   → Route layer at efi_guided.py may filter by org_id AFTER receiving results
   → Performance waste + risk of filter bypass
```

## K.4 Decision Tree Execution Flow (Detail)

```
1. Tree loaded: efi_decision_engine.py:93
   → db.efi_decision_trees.find_one({"tree_id": tree_id}) — NO ORG_ID
   
2. Session created: efi_decision_engine.py:135
   → db.efi_sessions.insert_one(session_dict) — NO ORG_ID IN DOCUMENT
   
3. Step recorded: efi_decision_engine.py:182-290
   → db.efi_sessions.find_one({"session_id": session_id}) — NO ORG_ID
   → db.efi_sessions.update_one({"session_id": session_id}, update) — NO ORG_ID
   
4. Completion: efi_decision_engine.py:247-290
   → Sets status="completed", selected_resolution_id
   → db.efi_sessions.update_one — NO ORG_ID
   
5. Learning: efi_decision_engine.py:375
   → db.learning_queue.insert_one(learning_item) — NO ORG_ID IN DOCUMENT
```

**Attack surface:** Any authenticated user who obtains a `session_id` (which is just a UUID) can read, modify, or complete another tenant's diagnostic session.

## K.5 Continuous Learning Flow (Detail)

```
1. Ticket completed → ticket_service._update_efi_platform_patterns()
   (services/ticket_service.py:632)
   
2. → continuous_learning_service.capture_job_completion()
   (services/continuous_learning_service.py:44)
   organization_id parameter: REQUIRED (passed from ticket)
   → Stores learning event WITH org_id ✓
   
3. Batch processing reads learning_queue
   → Has org_id in events ✓
   
4. Updates failure card statistics/embeddings
   → efi_embedding_service.py: update functions have NO ORG_ID
   → Embedding updates at efi_embedding_service.py:554 affect card globally
   
5. Cross-pollination via embedding similarity:
   → Learning from Org A's resolution updates card embeddings globally
   → Org B's similarity search picks up these updates
```

**Architectural tension:** The EFI system was designed with a "shared knowledge" philosophy (global failure cards benefit all tenants), but this conflicts with the multi-tenant isolation requirement. A clear `scope` field (global vs tenant) is needed, with tenant-specific data strictly isolated.

## K.6 EFI Remediation Roadmap

| Priority | Action | Files | Impact |
|----------|--------|-------|--------|
| P0 | Add `organization_id` to ALL operations in `efi_decision_engine.py` | 1 file, ~20 DB operations | Isolate diagnostic sessions |
| P0 | Add `organization_id` to ALL operations in `efi_embedding_service.py` | 1 file, ~10 DB operations | Isolate similarity searches |
| P0 | Add `organization_id` to ALL operations in `embedding_service.py` | 1 file, ~10 DB operations | Isolate embedding cache |
| P0 | Add `organization_id` to ALL operations in `event_processor.py` | 1 file, ~21 DB operations | Isolate event processing |
| P0 | Add 11 missing collections to TENANT_COLLECTIONS in `guard.py` | 1 file | Enable middleware validation |
| P1 | Make `organization_id` REQUIRED (not Optional) in `failure_intelligence_service.py:277` | 1 file | Prevent silent unscoping |
| P1 | Add org_id passthrough to all 33 endpoints in `routes/failure_intelligence.py` | 1 file | Route-level fix |
| P1 | Make org_id required in `model_aware_ranking_service.py:60` | 1 file | Prevent global fallback |
| P1 | Fix AI assist org_id default at `ai_assist_service.py:69` | 1 file | Remove "global" fallback |
| P1 | Add org_id to search service at `search_service.py:230,237` | 1 file | Scope text search |

---

# Section L — Module Completeness (24 Modules)

## L.1 Module Inventory

| # | Module | Route File(s) | Lines | Status | Completeness |
|---|--------|--------------|-------|--------|-------------|
| 1 | Authentication | `auth.py`, `auth_main.py` | ~400 | COMPLETE | 90% |
| 2 | Organizations | `organizations.py` | 1345 | COMPLETE | 85% |
| 3 | Tickets | `tickets.py` | ~400 | COMPLETE | 80% |
| 4 | Items | `items_enhanced.py` | 3423 | COMPLETE | 95% |
| 5 | Contacts | `contacts_enhanced.py` | 2245 | COMPLETE | 85% |
| 6 | Invoices | `invoices_enhanced.py` | 2407 | COMPLETE | 85% |
| 7 | Estimates | `estimates_enhanced.py` | 3011 | COMPLETE | 80% |
| 8 | Bills | `bills_enhanced.py` | 976 | FUNCTIONAL | 70% |
| 9 | Payments | `payments_received.py` | 1380 | FUNCTIONAL | 75% |
| 10 | Sales Orders | `sales_orders_enhanced.py` | 1557 | FUNCTIONAL | 70% |
| 11 | Inventory | `inventory_enhanced.py` | 1734 | FUNCTIONAL | 75% |
| 12 | HR/Payroll | `hr.py` | 1879 | FUNCTIONAL | 60% |
| 13 | GST | `gst.py` | 1146 | FUNCTIONAL | 50% |
| 14 | EFI/AI | 8 route files + 13 services | ~11500 | FUNCTIONAL | 65% |
| 15 | Reports | `reports.py`, `reports_advanced.py` | ~2350 | FUNCTIONAL | 70% |
| 16 | Banking | `banking.py`, `banking_module.py` | ~1317 | FUNCTIONAL | 60% |
| 17 | Journal Entries | `journal_entries.py` | ~500 | FUNCTIONAL | 75% |
| 18 | Projects | `projects.py` | 813 | SKELETON | 40% |
| 19 | Time Tracking | `time_tracking.py` | ~500 | FUNCTIONAL | 60% |
| 20 | Subscriptions | `subscriptions.py` | 725 | FUNCTIONAL | 70% |
| 21 | Customer Portal | `customer_portal.py` | ~500 | FUNCTIONAL | 60% |
| 22 | Technician Portal | `technician_portal.py` | 769 | FUNCTIONAL | 55% |
| 23 | Platform Admin | `platform_admin.py` | ~600 | FUNCTIONAL | 65% |
| 24 | Documents | `documents.py` | ~400 | FUNCTIONAL | 50% |

## L.2 Mocked/Placeholder Features

| Feature | File:Line | Status |
|---------|-----------|--------|
| Sales order sending | `routes/sales_orders_enhanced.py:1237` | MOCKED — "Send sales order to customer (mocked)" |
| Estimate sending | `routes/estimates_enhanced.py:2132` | MOCKED — "Send estimate to customer (mocked)" |
| Contact welcome email | `routes/contacts_enhanced.py:984` | MOCKED |
| Portal invite sending | `routes/contacts_enhanced.py:1509` | MOCKED |
| Statement PDF generation | `routes/contacts_enhanced.py:1612` | MOCKED |
| Statement email sending | `routes/contacts_enhanced.py:1622` | MOCKED |
| Payment thank-you email | `routes/payments_received.py:510` | MOCKED |
| Customer notification on stock | `routes/inventory_enhanced.py:856` | TODO comment |
| Credit note from inventory | `routes/inventory_enhanced.py:1001` | TODO comment |
| E-Invoice IRN | `routes/gst.py` module docstring | Placeholder |
| Productivity customer rating | `routes/productivity.py:251` | Hardcoded `4.5` |

## L.3 Missing Modules

| Module | Priority | Description |
|--------|----------|-------------|
| Purchase Orders (enhanced) | P1 | Only basic `purchase_orders` collection exists |
| Warehouse Management | P2 | Warehouses in schema but no transfer workflow |
| Approval Workflows | P1 | No configurable multi-level approval chains |
| Custom Reports Builder | P2 | All reports hardcoded |
| Audit Trail Viewer | P2 | Audit logs exist but no user-facing viewer |
| Notifications Center | P1 | Service exists but no in-app delivery mechanism |
| Dashboard Customization | P2 | Fixed dashboard layouts |
| Vendor Portal | P2 | Customer/business portals exist, no vendor self-serve |

---

# Section M — Test Coverage

## M.1 Test Suite Overview

- **Total test files:** 122 (at `backend/tests/`)
- **Last known results:** 322 passed, 0 failed, 51 skipped
- **Framework:** pytest

## M.2 Coverage by Module

| Module | Test Files | Assessment |
|--------|-----------|-----------|
| Items | 6 files (`test_items_enhanced.py`, `test_items_phase2.py`, `test_items_phase3.py`, `test_items_zoho_features.py`, `test_items_enhanced_zoho_columns.py`, `test_items_enhanced_parts_fix.py`) | HIGH |
| Estimates | 6 files (`test_estimates_enhanced.py`, `test_estimates_phase1.py`, `test_estimates_phase2.py`, `test_estimate_bug_fixes.py`, `test_estimate_edit_status.py`, `test_estimate_workflow_buttons.py`) | HIGH |
| Invoices | 3 files | MEDIUM |
| Contacts | 4 files | HIGH |
| HR/Payroll | 3 files (`test_hr_module.py`, `test_employee_creation.py`, `test_employee_module.py`) | MEDIUM — payroll calculation tests incomplete |
| GST | 3 files (`test_gst_module.py`, `test_gst_accounting_flow.py`, `test_gstr3b_credit_notes.py`) | MEDIUM |
| EFI | 6 files (`test_efi_guidance.py`, `test_efi_guided.py`, `test_efi_intelligence.py`, `test_efi_intelligence_api.py`, `test_efi_module.py`, `test_efi_search_embeddings.py`) | HIGH count but NO tenant isolation tests |
| Tenant Isolation | 4 files (`test_tenant_isolation.py`, `test_multi_tenant.py`, `test_multi_tenant_crud.py`, `test_multi_tenant_scoping.py`) | MEDIUM — gaps remain untested |
| RBAC | 1 file (`test_rbac_portals.py`) | LOW |
| Reports | 1 file (`test_reports.py`) | LOW |
| Payments | 1 file (`test_payments_received.py`) | LOW |
| Double-Entry | 1 file (`test_finance_module.py`) | LOW — 1 test file for 1649 lines |

## M.3 Skipped Test Categories

### Data-dependent skips (~25 tests)
Tests that skip because expected data doesn't exist. Examples:
- `tests/test_estimates_phase2.py:270`: "No draft estimates available"
- `tests/test_composite_items_invoice_settings.py:98`: "Not enough inventory items"
- `tests/test_contacts_invoices_enhanced.py:243`: "Test contact not created"

### Auth-dependent skips (~3 tests)
- `tests/test_final_certification.py:70`: "Admin login failed"
- `tests/test_final_certification.py:87`: "Tech login failed"
- `tests/test_reports.py:30`: "Authentication failed"

### Feature-dependent skips (~1 test)
- `tests/test_gst_module.py:200`: `@pytest.mark.skip(reason="Organization settings GSTIN persistence issue — pre-existing")`

### Workflow-dependent skips (~22 tests)
- `tests/test_ticket_estimate_integration.py`: 20+ skips due to estimate locking/state dependencies

## M.4 Critical Test Coverage Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No EFI tenant isolation tests | P0 | No test verifies EFI data is tenant-scoped. Given Section K findings, this is the highest-risk untested area |
| No cross-tenant data leak test (end-to-end) | P0 | No test creates data in Org A and verifies invisibility from Org B. Existing `test_multi_tenant_*.py` files are present but gaps in EFI, scheduler, notifications remain |
| No RBAC negative tests for enhanced routes | P0 | No test verifies that unmapped enhanced routes are denied to unauthorized roles. Given Section F.2 findings (20 bypassed routes), this is critical |
| No double-entry balance tests | P1 | No test verifies total debits = total credits after complex operations |
| No GST calculation accuracy tests | P1 | No test verifies CGST/SGST/IGST split correctness |
| No payroll statutory tests | P1 | No test verifies PF/ESI/PT calculations against Indian law |
| No full workflow chain test | P1 | No test executes the complete 10-step chain |
| No period lock enforcement test | P2 | No test verifies journal entries in locked periods are rejected |
| No concurrent modification tests | P2 | No race condition tests for inventory allocation |
| No RBAC negative tests | P2 | No test verifies technician CANNOT access finance routes |

---

# Section N — Verification Gaps & Audit Limitations

## N.1 What This Audit Could NOT Verify

| Limitation | Reason | Impact |
|-----------|--------|--------|
| Runtime middleware chain interaction | Read-only audit, no live testing | Middleware ordering verified in code. Actual runtime behavior untested |
| Actual cross-tenant data leak exploitation | No live database access | Pattern violations identified and cited with file:line, but not confirmed exploitable |
| Frontend tenant context propagation | Backend-only audit scope | Frontend may not correctly pass X-Organization-ID header on all requests |
| Razorpay webhook signature strength | No production credentials available | Webhook exists at `routes/razorpay.py:532`. Signature verification at lines 402-421 |
| Email delivery | Mocked in code (see Section L.2) | 7 mocked email features cannot be verified |
| LLM provider tenant isolation | External service boundary | OpenAI/Gemini API calls at `services/llm_provider.py` and `services/ai_guidance_service.py` may log tenant data |
| MongoDB index effectiveness | No query plan analysis performed | Compound indexes exist but query performance not verified |
| JWT secret strength | Value not inspectable in code | Only JWT usage pattern audited at `utils/auth.py` |
| Production environment config | Separate from dev config | CSRF secure flag (`middleware/csrf.py:102`), CORS origins, rate limit storage may differ |

## N.2 Files Examined at Pattern-Level Only (Not Line-by-Line)

| File | Lines | Reason |
|------|-------|--------|
| `routes/items_enhanced.py` | 3423 | Recently patched (66 fixes) — spot-checked `log_item_history` only |
| `routes/contacts_enhanced.py` | 2245 | Pattern-level org_id check |
| `routes/reports.py` | 1639 | Pattern-level check |
| `routes/sla.py` | 934 | org_id confirmed at pattern level |
| `routes/banking_module.py` | 927 | Assumed similar patterns to banking.py |
| `routes/customer_portal.py` | ~500 | Pattern-level — customer_id scoping not fully verified |
| `routes/expenses.py` | ~500 | Pattern-level check |
| `services/efi_seed_data.py` | 1385 | Seed script — not production code path |
| 122 test files | Varies | Analyzed skip patterns and file names, not test logic |

## N.3 Assumptions Made

1. TenantGuardMiddleware runs on ALL non-public routes (confirmed by `server.py:227-231` middleware chain and `core/tenant/context.py` logic)
2. `extract_org_id` will find `request.state.tenant_org_id` set by middleware (confirmed by `utils/database.py:18-26` fallback logic)
3. UUID-based IDs are sufficiently unguessable for public links (statistically sound — 2^128 space — but not cryptographically guaranteed)
4. MongoDB `_id` serialization handled by `{"_id": 0}` projections (prior sprint addressed this)

## N.4 Auditor Confidence Levels

| Section | Confidence | Rationale |
|---------|-----------|-----------|
| C (Tenant Isolation) | HIGH | Every service file checked for org_id count + DB operations enumerated |
| D (User Isolation) | MEDIUM | Pattern-level for most files, not line-by-line |
| E (Middleware) | HIGH | All 5 middleware files + server.py reviewed line-by-line |
| F (RBAC) | **VERY HIGH** | Python script executed to verify all 67 route prefixes against RBAC patterns |
| G (Accounting) | HIGH | Full review of `double_entry_service.py` function signatures |
| H (GST) | HIGH | Full review of `gst.py` + comparison against GST law requirements |
| I (Payroll) | HIGH | Full review of `hr_service.py` + `tds_service.py` + Indian statutory rate comparison |
| J (Workflow Chain) | HIGH | Deep trace through all 10 steps with file:line citations |
| K (EFI Architecture) | **VERY HIGH** | Every EFI service + route file analyzed with org_id count and DB operation enumeration |
| L (Module Completeness) | MEDIUM | Based on file existence, line count, and pattern analysis |
| M (Test Coverage) | MEDIUM | Based on file listing, skip analysis, and gap identification |

---

# Appendix — Remediation Priority Matrix

## P0 — Critical (Must Fix Before Production)

| ID | Finding | Section | File:Line |
|----|---------|---------|-----------|
| P0-01 | 20 route files bypass RBAC (all `-enhanced` routes unmapped) | F.2 | `middleware/rbac.py:42-156,282` |
| P0-02 | EFI Decision Engine — zero tenant isolation (471 lines, ~11 DB ops) | C.1.1 / K.2 | `services/efi_decision_engine.py:93,107,135,153,162,182,202,206,290,375` |
| P0-03 | EFI Embedding Service — zero tenant isolation (612 lines, ~6 DB ops) | C.1.2 / K.2 | `services/efi_embedding_service.py:477,482,494,534,554,575` |
| P0-04 | Embedding Service — zero tenant isolation (462 lines, ~10 DB ops) | C.1.3 / K.2 | `services/embedding_service.py:82,101,145,181,270,361,369,392,416,427` |
| P0-05 | Event Processor — zero tenant isolation (884 lines, ~21 DB ops) | C.1.4 / K.2 | `services/event_processor.py:89,101,126,157,224,246,285,321,369,370,461,513,526,570,623,635,682,732,792,865,869` |
| P0-06 | Scheduler — zero tenant isolation, all jobs global | C.1.5 | `services/scheduler.py:31,53,100,103,142,172,203,233,260,283,306,309` |
| P0-07 | Professional Tax hardcoded ₹200 for all states | I.5 | `services/hr_service.py:462` |
| P0-08 | 11 EFI collections missing from TenantGuard TENANT_COLLECTIONS | K.2 | `core/tenant/guard.py:37-83` |

## P1 — High (Must Fix Within Sprint)

| ID | Finding | Section | File:Line |
|----|---------|---------|-----------|
| P1-01 | `log_item_history` missing org_id in documents | C.1.9 | `routes/items_enhanced.py:2827-2838` |
| P1-02 | `org_query` silently drops org_id when null — returns `{}` | C.2 | `utils/database.py:29-35` |
| P1-03 | Notification service — zero org_id on all 4 DB operations | C.1.6 | `services/notification_service.py:254,316,375,398` |
| P1-04 | 24+ queries at `.to_list(2000-10000)` | C.4 | Multiple files (see C.4 table) |
| P1-05 | Period lock not enforced on journal entry creation | G.1.2 / J.11 | `services/posting_hooks.py` — missing check |
| P1-06 | PF ceiling not enforced (₹15,000 basic cap) | I.3 | `services/hr_service.py:460` |
| P1-07 | No pension fund (EPS) split from employer PF | I.3 | `services/hr_service.py:460` |
| P1-08 | PF admin charges not calculated (0.5% + 0.5% EDLI) | I.3 | Not found |
| P1-09 | GSTR-1 missing B2C/CDN/HSN-by-rate sections | H.1.4 | `routes/gst.py:315-505` |
| P1-10 | GSTR-3B missing ITC categorization | H.1.5 | `routes/gst.py:695-975` |
| P1-11 | No Indian fiscal year in accounting | G.1.2 | `services/double_entry_service.py:1300,1390` |
| P1-12 | RBAC no-role fallthrough allows unauthenticated pass | E.2.3 | `middleware/rbac.py:270-274` |
| P1-13 | Workflow chain broken at Steps 4→5 and 5→6 | J.12 | Architecture gap |
| P1-14 | `failure_intelligence_service.py` — org_id Optional in core matching | K.1.1 | `services/failure_intelligence_service.py:277` |
| P1-15 | `model_aware_ranking_service.py` — org_id Optional | K.1.1 | `services/model_aware_ranking_service.py:60` |
| P1-16 | `ai_assist_service.py` — org_id defaults to "global" | K.1.1 | `services/ai_assist_service.py:69` |
| P1-17 | Search service — zero org_id in failure card queries | C.1.7 | `services/search_service.py:230,237` |
| P1-18 | `routes/failure_intelligence.py` — 31/33 endpoints don't pass org_id | K.1.2 | `routes/failure_intelligence.py:96-354` |
| P1-19 | Ticket creation org_id optional in service | J.2 | `services/ticket_service.py:120` |
| P1-20 | ESI wage ceiling hardcoded ₹21,000 | I.4 | `services/hr_service.py:461` |
| P1-21 | No audit trail for journal modifications | G.1.2 | `services/double_entry_service.py:267,415` |
| P1-22 | Form 16 certificate number validation weak | I.2.1 | `services/tds_service.py:518` |

## P2 — Medium (Backlog)

| ID | Finding | Section | File:Line |
|----|---------|---------|-----------|
| P2-01 | CSRF secure flag hardcoded False | E.2.1 | `middleware/csrf.py:102` |
| P2-02 | Rate limiting in-memory only | E.2.2 | `middleware/rate_limit.py:112` |
| P2-03 | Estimate→Invoice conversion org_id from legacy data | J.4 | `routes/estimates_enhanced.py:2210` |
| P2-04 | 7 mocked email/notification features | L.2 | Various |
| P2-05 | No HRA exemption in payroll (only in TDS) | I.6 | Not found in hr_service.py |
| P2-06 | No gratuity calculation | I.6 | Not found |
| P2-07 | No bonus (Payment of Bonus Act) | I.6 | Not found |
| P2-08 | No e-Way bill generation | H.1.6 | Not found |
| P2-09 | No GSTR-2A/2B reconciliation | H.1.6 | Not found |
| P2-10 | Projects module skeleton (40%) | L.1 | `routes/projects.py` |
| P2-11 | Technician sees all org tickets | D.1 | `routes/technician_portal.py` |
| P2-12 | No WIP cost tracking | J.7 | Not found |
| P2-13 | No concurrent modification safeguards | M.4 | Not found |
| P2-14 | 51 skipped tests need data fixtures | M.3 | `backend/tests/` |
| P2-15 | `period_locks.py` uses `org_id` not `organization_id` (naming inconsistency) | C.1.12 | `routes/period_locks.py` |
| P2-16 | No multi-currency support | G.1.2 | Not found |
| P2-17 | No depreciation schedules | G.1.2 | Not found |
| P2-18 | GSTIN checksum (Luhn mod-36) not validated | H.1.2 | `routes/gst.py:128` |
| P2-19 | No full workflow chain end-to-end test | M.4 | Test gap |

---

# Appendix B — Quick Reference: Files Needing Immediate Attention

```
# P0 — RBAC bypass fix (add patterns for all enhanced routes)
middleware/rbac.py:42-156        Add 20 missing route patterns

# P0 — Zero tenant isolation (entire files need org_id injection)
services/efi_decision_engine.py          471 lines, 11 DB operations
services/efi_embedding_service.py        612 lines, 6 DB operations
services/embedding_service.py            462 lines, 10 DB operations
services/event_processor.py              884 lines, 21 DB operations
services/scheduler.py                    350 lines, 13 DB operations

# P0 — Guard configuration
core/tenant/guard.py:37-83       Add 11 collections to TENANT_COLLECTIONS

# P0 — Statutory
services/hr_service.py:462       Professional Tax — implement state-wise slabs

# P1 — Specific fixes
routes/items_enhanced.py:2827    log_item_history — add org_id param and in document
utils/database.py:29             org_query — raise on None org_id (fail-fast)
services/notification_service.py Add org_id to all 4 DB operations
services/hr_service.py:460       PF ceiling cap at ₹15,000 basic
services/posting_hooks.py        Add period_lock check before all journal posts
middleware/rbac.py:270-274       Change no-role fallthrough to deny
services/ticket_service.py:120   Make organization_id required (not Optional)
services/failure_intelligence_service.py:277  Make org_id required
routes/failure_intelligence.py   Add org_id to all 33 endpoint functions
```

---

**End of Audit**

*This document is the master remediation checklist for Battwheels OS. All future development sprints must reference this document for prioritization.*  
*Generated: 2026-02-28 | Auditor: E1 Agent (Emergent Labs)*  
*File: /app/docs/REMEDIATION_AUDIT_2026.md*
