# REMEDIATION AUDIT 2026 — Battwheels OS

**Audit Date:** 2026-02-28  
**Auditor:** E1 Agent (Emergent Labs)  
**Audit Type:** Read-Only, Comprehensive, Full-Codebase  
**Codebase Snapshot:** Post H-01/H-02 hard-cap sprint + items_enhanced.py 66-endpoint tenant fix  
**Test Suite Baseline:** 322 passed, 0 failed, 51 skipped  

---

## Table of Contents

| Section | Title | Priority |
|---------|-------|----------|
| 1 | Org-Level Tenant Isolation (Pattern A/B/C) | HIGH |
| 2 | User-Level Isolation within Org (Pattern D) | HIGH |
| 3 | Middleware Chain | STANDARD |
| 4 | RBAC across All Modules | STANDARD |
| 5 | Indian Accounting Standards | STANDARD |
| 6 | GST Compliance | HIGH |
| 7 | Payroll Statutory Compliance | HIGH |
| 8 | Core Workflow Chain (10-Step Chain) | DEEPEST |
| 9 | EFI Architecture | DEEPEST |
| 10 | Module Completeness (24 Modules) | STANDARD |
| 11 | Test Coverage | STANDARD |
| F | Verification Gaps & Audit Limitations | — |

---

# Section 1 — Org-Level Tenant Isolation (Pattern A/B/C)

## 1.1 Pattern A: Routes that query tenant collections WITHOUT organization_id

### 1.1.1 CRITICAL — EFI Decision Engine (services/efi_decision_engine.py)

**File:** `services/efi_decision_engine.py` (471 lines)  
**Severity:** P0 — CRITICAL  
**org_id/organization_id references:** ZERO  
**DB operations affected:** ALL  

Every database operation in this file is completely unscoped:

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| 93 | `find_one` | `efi_decision_trees` | No org_id filter |
| 107 | `insert_one` | `efi_decision_trees` | No org_id in document |
| 135 | `insert_one` | `efi_sessions` | No org_id in document |
| 153 | `find_one` | `efi_sessions` | No org_id filter |
| 162 | `find_one` | `efi_decision_trees` | No org_id filter |
| 182 | `find_one` | `efi_sessions` | No org_id filter |
| 202 | `find_one` | `efi_sessions` | No org_id filter |
| 206 | `find_one` | `efi_decision_trees` | No org_id filter |
| 290 | `update_one` | `efi_sessions` | No org_id filter |
| 375 | `insert_one` | `learning_queue` | No org_id in document |
| 404+ | `find` | `learning_queue` | No org_id filter |

**Impact:** Any tenant can read/modify/complete EFI diagnostic sessions belonging to another tenant. Decision tree data is globally shared without scoping.

### 1.1.2 CRITICAL — EFI Embedding Service (services/efi_embedding_service.py)

**File:** `services/efi_embedding_service.py` (612 lines)  
**Severity:** P0 — CRITICAL  
**org_id/organization_id references:** ZERO  

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| 477 | `find` | `failure_cards` | `.to_list(1000)` — no org_id |
| 482 | `find` | `failure_cards` | No org_id filter |
| 494 | `find` | `efi_decision_trees` | `.to_list(1000)` — no org_id |
| 534 | `find_one` | `failure_cards` | No org_id filter |
| 554 | `update_one` | `failure_cards` | No org_id filter |
| 575 | `find` | `failure_cards` | `.to_list(1000)` — no org_id |

**Impact:** Embedding similarity searches return cross-tenant failure cards. Embedding updates modify cards globally.

### 1.1.3 CRITICAL — Embedding Service (services/embedding_service.py)

**File:** `services/embedding_service.py` (462 lines)  
**Severity:** P0 — CRITICAL  
**org_id/organization_id references:** ZERO  

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| 82 | `find_one` | `embedding_cache` | No org_id filter |
| 101 | `update_one` | `embedding_cache` | No org_id filter |
| 145 | `find_one` | `embedding_cache` | No org_id filter |
| 181 | `update_one` | `embedding_cache` | No org_id filter |
| 270 | `find` | Parameterized collection | No org_id filter |
| 361 | `find` | `failure_cards` | No org_id filter |
| 369 | `find` | `failure_cards` | No org_id filter |
| 392 | `update_one` | `failure_cards` | No org_id filter |
| 416 | `find_one` | `failure_cards` | No org_id filter |
| 427 | `update_one` | `failure_cards` | No org_id filter |

**Impact:** Cross-tenant data leakage through embedding cache and similarity search.

### 1.1.4 HIGH — Notification Service (services/notification_service.py)

**File:** `services/notification_service.py`  
**Severity:** P1 — HIGH  
**org_id/organization_id references:** ZERO  

| Line | Operation | Collection | Issue |
|------|-----------|------------|-------|
| 254 | `insert_one` | `notification_logs` | No org_id in document |
| 316 | `find_one` | `tickets` | Queries by `ticket_id` only — no org_id |
| 375 | `find` | `notification_logs` | No org_id filter |

**Impact:** Notification logs are unscoped. If ticket_id collision occurs (UUID-based, low risk but non-zero), notifications could cross tenants.

### 1.1.5 HIGH — Scheduler Service (services/scheduler.py)

**File:** `services/scheduler.py`  
**org_id/organization_id references:** ZERO  

All scheduled tasks run without tenant context, potentially processing data across tenants.

### 1.1.6 HIGH — Event Processor (services/event_processor.py)

**File:** `services/event_processor.py`  
**org_id/organization_id references:** ZERO  

Event processing pipeline lacks tenant scoping.

### 1.1.7 HIGH — Visual Spec Service (services/visual_spec_service.py)

**File:** `services/visual_spec_service.py`  
**org_id/organization_id references:** ZERO  

### 1.1.8 HIGH — Search Service (services/search_service.py)

**File:** `services/search_service.py`  
**org_id/organization_id references:** ZERO (for DB-level, though GST references exist)  

### 1.1.9 MEDIUM — Finance Calculator (services/finance_calculator.py)

**File:** `services/finance_calculator.py`  
**org_id/organization_id references:** ZERO  

Pure calculation service — no DB operations, so no direct leak risk. But if tax config is org-specific, this is a compliance gap.

### 1.1.10 MEDIUM — LLM Provider (services/llm_provider.py)

**File:** `services/llm_provider.py`  
**org_id/organization_id references:** ZERO  

No DB operations — purely an API wrapper. Low risk.

### 1.1.11 MEDIUM — log_item_history helper (routes/items_enhanced.py:2827)

**File:** `routes/items_enhanced.py:2827`  
**Severity:** P1 — HIGH  

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

**Issue:** `organization_id` is NOT included in the inserted document. The `get_all_item_history` endpoint (line 2839) correctly queries with `organization_id`, but documents inserted by `log_item_history` will NEVER match because they lack the field. This means:
1. History records are orphaned (not queryable per-tenant)
2. If a global query ever runs, history from all tenants would intermingle

**Called from:** Lines 908, 1765, 2481, 2489, 2518, 2798, 2816, 2920 (8 call sites)

### 1.1.12 Pattern A violations in routes — files that DON'T use `organization_id` at all

These route files have NO reference to `organization_id`:

| File | Line Count | Risk |
|------|-----------|------|
| `routes/stripe_webhook.py` | ~80 | LOW (webhook, external) |
| `routes/__init__.py` | ~10 | N/A (package init) |

Note: `routes/banking.py` uses `org_id` (from JWT/headers) and passes it to banking_service which does scope correctly. `routes/period_locks.py` uses `org_id` field (not `organization_id`) — an inconsistency but functionally scoped.

---

## 1.2 Pattern B: Routes that use extract_org_id but don't enforce non-null

**File:** `utils/database.py:18-26`

```python
def extract_org_id(request) -> Optional[str]:
    org_id = request.headers.get("X-Organization-ID") or request.headers.get("x-organization-id")
    if not org_id:
        org_id = getattr(getattr(request, "state", None), "tenant_org_id", None)
    return org_id
```

**Issue:** Returns `Optional[str]`. Many routes call this but DON'T check for `None` before using it in queries.

```python
def org_query(org_id: Optional[str], extra: dict = None) -> dict:
    q = {}
    if org_id:
        q["organization_id"] = org_id
    if extra:
        q.update(extra)
    return q
```

**Issue:** `org_query` silently drops `organization_id` when `org_id` is `None`, returning an UNSCOPED query. This is a systemic soft-fail design that can lead to cross-tenant data leakage.

**Affected routes (using `extract_org_id` + `org_query`):**
- `routes/reports_advanced.py` — 14 endpoints
- `routes/efi_guided.py` — 20 endpoints
- `routes/export.py` — 6+ endpoints
- `routes/pdf_templates.py` — 4 endpoints
- `routes/productivity.py` — 5+ endpoints
- `routes/fault_tree_import.py` — 5+ endpoints
- `routes/composite_items.py` — 5+ endpoints
- `routes/serial_batch_tracking.py` — 8+ endpoints
- `routes/invoice_automation.py` — 5+ endpoints
- `routes/gst.py` — 10+ endpoints
- `routes/inventory_adjustments_v2.py` — 20+ endpoints
- `routes/technician_portal.py` — 8+ endpoints
- `routes/inventory_enhanced.py` — 15+ endpoints
- `routes/data_migration.py` — 5+ endpoints
- `routes/amc.py` — 8+ endpoints
- `routes/recurring_invoices.py` — 6+ endpoints
- `routes/permissions.py` — 5+ endpoints
- `routes/master_data.py` — 3+ endpoints

**Total at-risk endpoints:** ~150+

**Mitigating factor:** The TenantGuardMiddleware sets `request.state.tenant_org_id` before routes execute, so `extract_org_id` should find it in fallback. BUT the middleware's public endpoint list is broad, and if any route is accidentally marked public, the fallback fails silently.

---

## 1.3 Pattern C: Aggregation pipelines without $match on organization_id as first stage

**Affected files:**

| File | Line | Pipeline starts with |
|------|------|---------------------|
| `routes/reports_advanced.py:78` | Aggregation pipeline | Uses `org_query` (Pattern B risk) |
| `routes/reports_advanced.py:131` | Aggregation pipeline | Uses `org_query` |
| `routes/reports_advanced.py:176` | Aggregation pipeline | Uses `org_query` |
| `routes/invoices_enhanced.py:360` | Aggregation pipeline | Has org_id in $match |
| `routes/contact_integration.py:602` | Aggregation pipeline | Has org_id in $match |
| `services/double_entry_service.py:1594` | Aggregation pipeline | Has org_id |
| `routes/insights.py:763` | Aggregation pipeline | Uses `get_org_id` |

The TenantGuard's `validate_aggregation` method (guard.py:223) does check for $match as the first stage, but this is only used if routes explicitly call the guard. Most routes build pipelines manually and bypass the guard entirely.

---

## 1.4 Unbounded Query Residuals

Despite the H-01/H-02 hard-cap sprint, significant high-limit queries remain:

| Limit | Count | Files |
|-------|-------|-------|
| `.to_list(10000)` | 11 | gst.py, reports.py, items_enhanced.py, time_tracking.py, operations_api.py, estimates_enhanced.py, payments_received.py, invoice_automation.py |
| `.to_list(5000)` | 7 | invoices_enhanced.py, reports.py, insights.py, data_migration.py, inventory_adjustments_v2.py |
| `.to_list(2000)` | 6 | reports_advanced.py, bills_enhanced.py, inventory_enhanced.py, inventory.py, inventory_api.py |
| `.to_list(1000)` | 8+ | contact_integration.py, efi_embedding_service.py, etc. |

**Total high-limit queries:** 32+

These remain as a performance and OOM risk for large tenants. The `.to_list(10000)` calls in `gst.py` are especially concerning since GSTR-1/3B reports iterate ALL invoices for a month.

---

# Section 2 — User-Level Isolation within Org (Pattern D)

## 2.1 User-Level Data Access

Pattern D concerns: Can a regular user within an org access data they shouldn't (e.g., another user's draft estimates, another technician's assignments)?

### 2.1.1 Technician Portal (routes/technician_portal.py)

The technician portal uses `extract_org_id` for tenant scoping but DOES NOT filter by `assigned_technician_id` or `user_id` for listing tickets. A technician can see ALL tickets in the organization, not just their own assignments.

**File:** `routes/technician_portal.py`  
**Severity:** P2 — MEDIUM  

### 2.1.2 Customer Portal (routes/customer_portal.py)

Customer portal auth creates a separate token with `role: "customer"`. Queries should scope by `customer_id` to prevent one customer seeing another's invoices/tickets.

**Review needed:** Full audit of customer portal queries to verify `customer_id` scoping.

### 2.1.3 HR Self-Service

**File:** `routes/hr.py`  
The `_is_self_only` function (line 142) exists to check if a user should only see their own data:

```python
def _is_self_only(user: dict) -> bool:
```

This is used in some HR endpoints but NOT consistently across all sensitive endpoints (e.g., payroll data, TDS data, Form 16 data).

### 2.1.4 Activity Tracking

**File:** `services/activity_service.py` — 5 org_id references  
Activity logs are org-scoped but not user-scoped. Any user in the org can see all activity logs for the entire org.

### 2.1.5 Document Access

**File:** `routes/documents.py`  
Document access is org-scoped but not role/user restricted. Any authenticated org member can access all documents.

---

# Section 3 — Middleware Chain

## 3.1 Middleware Stack Order (server.py:227-231)

```python
app.add_middleware(RateLimitMiddleware)      # Outermost
app.add_middleware(SanitizationMiddleware)   # 4
app.add_middleware(CSRFMiddleware)           # 3
app.add_middleware(RBACMiddleware)           # 2
app.add_middleware(TenantGuardMiddleware)    # 1 (Innermost — runs first)
```

**Execution order (Starlette LIFO):** TenantGuard → RBAC → CSRF → Sanitization → RateLimit

This is **correct**. TenantGuard runs first, sets `request.state.tenant_*`, RBAC checks role, CSRF validates tokens, Sanitization strips HTML, RateLimit counts.

## 3.2 Middleware Gaps

### 3.2.1 CSRF secure flag

**File:** `middleware/csrf.py:100`
```python
secure=False,  # Set True in production behind HTTPS
```
**Issue:** CSRF cookie `secure` flag is hardcoded to `False`. Should be `True` in production (behind HTTPS). This is a deployment-time fix but should be env-driven.

### 3.2.2 Rate Limit storage

**File:** `middleware/rate_limit.py:112`
```python
self._request_counts = {}  # In-memory rate limit tracking (use Redis in production)
```
**Issue:** In-memory rate limiting resets on every server restart. In a multi-pod Kubernetes deployment, rate limits are per-pod, not global. This makes rate limiting ineffective in production.

### 3.2.3 RBAC fallthrough for unmapped routes

**File:** `middleware/rbac.py:282-284`
```python
if allowed_roles is None:
    # Route not in permissions map - allow authenticated users
    return await call_next(request)
```
**Issue:** Any route NOT in `ROUTE_PERMISSIONS` map is allowed for ALL authenticated users. This is DENY-by-default in theory but ALLOW-by-default in practice for unmapped routes.

**Unmapped routes include:**
- `/api/v1/inv-adjustments/...` (inventory adjustments — prefix mismatch)
- `/api/v1/banking/...` (banking module)
- `/api/v1/finance/period-locks/...` (period locks)
- Any future route not added to the map

### 3.2.4 TenantGuard no-role fallthrough

**File:** `middleware/rbac.py:270-274`
```python
if not user_role:
    logger.info(f"RBAC: No role found for path {path} - letting through for auth check")
    return await call_next(request)
```
**Issue:** If TenantGuardMiddleware fails to set the role, RBAC lets the request through. This is a defense-in-depth gap.

### 3.2.5 Deprecated middleware/tenant.py tombstone

**File:** `middleware/tenant.py`  
Correctly tombstoned. No issue.

## 3.3 Security Headers

**File:** `server.py:238-246`  
All standard security headers are present: X-Content-Type-Options, X-Frame-Options, HSTS, X-XSS-Protection, Referrer-Policy, CSP. 

**CSP Issue:** `connect-src` allows `https://*.emergentagent.com` — this is correct for development but should be restricted in production.

---

# Section 4 — RBAC across All Modules

## 4.1 Role Hierarchy

**File:** `middleware/rbac.py:26-38`

```
owner > admin > org_admin > manager > accountant/hr/technician/dispatcher > viewer
customer/fleet_customer (separate hierarchy)
```

**Issue:** `owner` and `admin` have identical permissions in most contexts. The hierarchy includes `admin` > `org_admin` but this is confusing — in practice, both should be equivalent.

## 4.2 RBAC Gaps

### 4.2.1 Missing route patterns

The following route prefixes are NOT in `ROUTE_PERMISSIONS`:

| Route Prefix | Actual Prefix | Issue |
|--------------|---------------|-------|
| `/api/inv-adjustments/...` | `inventory_adjustments_v2.py` uses `/inv-adjustments` | Not mapped — open to all authenticated users |
| `/api/banking/...` | `banking.py` uses `/banking` | Maps to finance pattern, but `banking_module.py` uses `/banking-module` which IS mapped |
| `/api/finance/period-locks/...` | `period_locks.py` | Maps to `/api/finance/.*` pattern ✓ |
| `/api/reports-advanced/...` | `reports_advanced.py` | Not explicitly mapped — falls through |
| `/api/tally-export/...` | `tally_export.py` | Not mapped |
| `/api/vendor-credits/...` | `vendor_credits.py` | Not mapped |
| `/api/delivery-challans/...` | `delivery_challans.py` | IS mapped ✓ |

### 4.2.2 Inline role checks inconsistency

Some routes perform their own role checks (e.g., `require_admin`, `require_role`) in addition to middleware RBAC. This creates inconsistency:

- `routes/hr.py:142`: `_is_self_only()` — custom role check
- `routes/platform_admin.py`: Uses `require_admin` decorator
- `routes/organizations.py`: Uses TenantContext permission checks
- `routes/items_enhanced.py`: No inline role checks beyond middleware

### 4.2.3 Accountant can't access HR attendance/leave

**File:** `middleware/rbac.py:53-54`
```python
r"^/api/hr/attendance.*$": ["org_admin", "admin", "owner", "manager", "hr", "technician", "accountant"],
r"^/api/hr/leave.*$":     ["org_admin", "admin", "owner", "manager", "hr", "technician", "accountant"],
```
Accountant is correctly included for attendance/leave (needed for payroll processing). ✓

### 4.2.4 Technician can access all items

**File:** `middleware/rbac.py:77`
```python
r"^/api/items/.*$": ["org_admin", "admin", "owner", "manager", "accountant", "technician"],
```
Technicians can see ALL items including pricing. This may be intentional for EFI guidance but should be reviewed for business sensitivity.

---

# Section 5 — Indian Accounting Standards

## 5.1 Double-Entry Accounting System

**File:** `services/double_entry_service.py` (1649 lines)

### 5.1.1 Implemented Features

- Chart of Accounts with system accounts (auto-created per org)
- Journal entry creation with debit/credit validation
- Trial Balance generation
- Profit & Loss statement
- Balance Sheet
- Account Ledger with running balance
- Posting hooks for invoices, bills, payments, expenses, payroll
- Reference number generation per entry type
- Entry reversal support

### 5.1.2 Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No fiscal year management | P1 | No concept of Indian Financial Year (April-March). P&L/BS use arbitrary date ranges |
| No opening/closing balance carry-forward | P1 | No year-end closing process |
| No multi-currency support | P2 | All amounts assumed INR |
| No depreciation schedules | P2 | No asset depreciation (SLM/WDV as per Companies Act) |
| No accrual accounting support | P2 | No accrual/deferral entries |
| No TDS payable tracking in CoA | P1 | TDS is calculated but not posted to specific TDS payable accounts per section |
| No bank reconciliation journal integration | P2 | Banking module is separate from double-entry |
| No audit trail for journal modifications | P1 | Journal entries can be created/reversed but no tamper-evident log |
| No period locking integration | P1 | `period_locks.py` exists but uses `org_id` field (not `organization_id`) and is not consulted before journal posting |

### 5.1.3 Decimal Precision

**File:** `services/double_entry_service.py:207`
```python
def round_currency(amount: float | Decimal | int) -> Decimal:
```
Uses Python `Decimal` for currency — **correct** approach for financial calculations.

---

# Section 6 — GST Compliance

## 6.1 GST Module Overview

**File:** `routes/gst.py` (1146 lines)

### 6.1.1 Implemented Features

- GSTIN validation (format + checksum)
- CGST/SGST/IGST split based on place of supply
- GSTR-1 report generation (JSON, Excel, PDF)
- GSTR-3B report generation (JSON, Excel, PDF)
- HSN/SAC summary report
- Indian state code mapping (all 37 states + UTs)
- Reverse Charge Mechanism (RCM) handling in GSTR-3B
- Organization GST settings management

### 6.1.2 GSTIN Validation

**File:** `routes/gst.py:104-131`

Validates:
- Length (15 characters) ✓
- State code (first 2 digits) ✓
- PAN format (characters 3-12) ✓
- Entity code (character 13) ✓
- Check digit (character 15) — **NOT validated** (just checked for alphanumeric)

**Gap:** No Luhn/mod-based checksum validation for the 15th character. Invalid GSTINs with correct format but wrong checksum will pass.

### 6.1.3 GST Rate Handling

```python
GST_RATES = [0, 5, 12, 18, 28]
```

**Gap:** Does not handle:
- Cess rates (e.g., 1%, 3%, 5% additional cess on luxury goods)
- Compensation Cess
- 0.25% and 3% GST rates (for rough diamonds, gold)

### 6.1.4 GSTR-1 Report Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No B2C (Small) segregation | P1 | All invoices treated as B2B. B2C invoices < ₹2.5L not reported in separate section |
| No credit note/debit note section | P1 | GSTR-1 requires CDN section for credit notes. Not generated |
| No advance payment section | P2 | Advance received (Table 11A) not tracked |
| No amendment section | P2 | Amendments to previous returns (Table 9) not generated |
| No HSN-wise summary by rate | P1 | HSN summary exists but doesn't split by GST rate as required |
| No e-Invoice IRN integration | P2 | Mentioned as "placeholder" in module docstring |
| No GSTR-1 JSON in govt format | P1 | Report format is custom, not matching GST portal's JSON schema |
| Unbounded query `.to_list(10000)` | P1 | 6 instances in gst.py pull ALL invoices for a month without pagination |

### 6.1.5 GSTR-3B Report Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No ITC categorization | P1 | Input Tax Credit not split into eligible/ineligible/reversed as per Table 4 |
| No inter-state vs intra-state B2C split | P1 | Table 3.2 requires this split |
| No exempt/nil-rated/non-GST segregation | P2 | Table 5 of GSTR-3B not populated |
| RCM calculation present but basic | P2 | Only checks `reverse_charge: True` flag, doesn't validate RCM categories |
| No previous period adjustment | P2 | Cannot incorporate tax adjustments from prior months |

### 6.1.6 Missing GST Features

| Feature | Status | Impact |
|---------|--------|--------|
| GSTR-2A/2B reconciliation | NOT IMPLEMENTED | Cannot reconcile purchase data with supplier returns |
| E-way bill generation | NOT IMPLEMENTED | Required for goods transport > ₹50,000 |
| GST payment challan (PMT-06) | NOT IMPLEMENTED | Cannot generate payment challans |
| Composition scheme handling | NOT IMPLEMENTED | No support for composition dealers |
| GST annual return (GSTR-9) | NOT IMPLEMENTED | No annual return generation |
| Multi-GSTIN per org | NOT IMPLEMENTED | Organizations with multiple branches need separate GSTINs |
| Input Tax Credit register | NOT IMPLEMENTED | No ITC ledger maintenance |

---

# Section 7 — Payroll Statutory Compliance

## 7.1 Payroll Module Overview

**Files:**
- `routes/hr.py` (1879 lines)
- `services/hr_service.py` (~600 lines)
- `services/tds_service.py`
- `services/posting_hooks.py` (payroll journal entry)

### 7.1.1 Implemented Features

- Employee CRUD with Indian compliance fields (PAN, Aadhaar, PF number, ESI number)
- Salary structure: Basic + HRA + DA + Special Allowance
- PF calculation (12% of basic)
- ESI calculation (0.75% if gross ≤ ₹21,000)
- Professional Tax (flat ₹200)
- TDS calculation and tracking
- Form 16 generation (Part A + Part B)
- Payroll journal entry posting
- Bulk Form 16 ZIP download
- TDS challan recording
- Attendance and leave management

### 7.1.2 PF Compliance Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| PF ceiling not enforced | P1 | PF calculated on full basic. Should cap at ₹15,000/month basic for employer contribution |
| No PF admin charges | P1 | Employer pays 0.5% admin + 0.5% EDLI. Not calculated |
| No pension fund split | P1 | Of 12% employer contribution, 8.33% goes to EPS (capped at ₹15,000 wage). Not split |
| No PF ECR generation | P2 | Cannot generate Electronic Challan-cum-Return for EPFO |
| No UAN integration | P2 | No link to Universal Account Number system |
| Voluntary PF (VPF) not supported | P2 | Employee cannot opt for > 12% |

### 7.1.3 ESI Compliance Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| ESI rate incorrect | P0 | Code uses `0.0075` (0.75%). Current rate: Employee 0.75% ✓, Employer 3.25%. Only employee share calculated |
| ESI wage ceiling | P1 | Hardcoded ₹21,000. Current ceiling is ₹21,000 ✓ but should be configurable for future changes |
| No ESI contribution register | P2 | Cannot generate ESI return |
| No ESI exemption handling | P2 | No handling of ESI-exempt employees |

### 7.1.4 Professional Tax Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| Flat ₹200 for all states | P0 | Professional Tax varies by state (₹0 to ₹2,500). Maharashtra: slab-based. Karnataka: flat ₹200. Telangana: slab-based |
| No state-wise PT slabs | P0 | Must support different slabs per employee's work state |
| No PT exemption for certain months | P2 | Some states exempt PT in February |

### 7.1.5 TDS (Income Tax) Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| TDS calculation exists | — | `services/tds_service.py` handles TDS |
| Old vs New regime handling | P1 | Needs verification — both regimes should be supported |
| No HRA exemption calculation | P1 | HRA exemption under Section 10(13A) not calculated (minimum of actual HRA, 50%/40% of basic, rent - 10% basic) |
| No Section 80C/80D deduction tracking | P1 | Investment declarations not tracked for TDS projection |
| No 26AS reconciliation | P2 | Cannot verify TDS deposits against Form 26AS |
| Form 16 Part A — certificate number | P1 | Form 16 generated but certificate number and TAN validation not robust |

### 7.1.6 Missing Payroll Features

| Feature | Status | Impact |
|---------|--------|--------|
| Gratuity calculation | NOT IMPLEMENTED | Required for employees with 5+ years. Formula: (15 × last drawn salary × years of service) / 26 |
| Bonus calculation (Payment of Bonus Act) | NOT IMPLEMENTED | Statutory bonus 8.33% to 20% of basic+DA for eligible employees |
| LTA/LTC exemption | NOT IMPLEMENTED | Leave Travel Allowance exemption tracking |
| Reimbursement management | NOT IMPLEMENTED | No expense reimbursement through payroll |
| Loan/advance deduction | NOT IMPLEMENTED | No salary advance or loan EMI deduction |
| Full & Final settlement | NOT IMPLEMENTED | No FnF process for exiting employees |
| Arrears calculation | NOT IMPLEMENTED | No backdated salary revision processing |
| CTC breakdown to components | PARTIAL | CTC field exists but automatic component breakdown from CTC not implemented |
| Pay slip PDF generation | PARTIAL | Form 16 exists but monthly pay slip is not separately generated |

### 7.1.7 Employer Contribution Tracking

**File:** `services/hr_service.py:492-493`
```python
"pf_employer": round(employer_pf, 2),
"esi_employer": round(employer_esi, 2)
```

Employer PF (12%) and ESI (3.25%) are calculated but:
- Not posted to separate journal accounts
- Not tracked for statutory return filing
- No due date tracking for deposit compliance (15th of next month for PF, 15th for ESI)

---

# Section 8 — Core Workflow Chain (10-Step Chain)

This section receives the DEEPEST audit as it is the core product differentiator.

## 8.1 The 10-Step Workflow

The core Battwheels workflow chain:
1. **Ticket Creation** → 2. **EFI Diagnosis** → 3. **Estimate Generation** → 4. **Customer Approval** → 5. **Parts Allocation** → 6. **Work Execution** → 7. **Work Completion** → 8. **Invoice Generation** → 9. **Payment Collection** → 10. **Journal Entry / Accounting**

### 8.2 Step 1: Ticket Creation

**Files:** `routes/tickets.py`, `services/ticket_service.py`

**Implementation:**
- Ticket creation via `TicketService.create_ticket()` (service line 167)
- Generates unique `ticket_id` (UUID-based)
- Supports organization_id scoping (passed via `data.organization_id`)
- Vehicle lookup by registration number
- SLA config loaded per organization
- Event emission: `TICKET_CREATED` event dispatched

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| `organization_id` passed as optional parameter | P1 | `services/ticket_service.py:120`: `organization_id: Optional[str] = None`. If not provided, ticket is created WITHOUT org scoping |
| No duplicate ticket detection | P2 | Same vehicle + same complaint can create duplicate tickets |
| No ticket number sequence per org | P2 | `ticket_id` is UUID-based, no human-readable sequence (e.g., TKT-0001) per organization |
| Public ticket creation bypasses tenant context | INFO | `routes/public_tickets.py` creates tickets from public forms — this is by design but org_id must be injected from the public form's org reference |

### 8.3 Step 2: EFI Diagnosis

**Files:** `services/efi_decision_engine.py`, `routes/efi_guided.py`, `services/efi_embedding_service.py`, `services/failure_intelligence_service.py`, `services/ai_guidance_service.py`

**Implementation:**
- EFI (Engine Failure Intelligence) is a multi-layered AI system:
  - Layer 1: Failure card matching via embedding similarity
  - Layer 2: Decision tree guided diagnostics
  - Layer 3: AI-powered guidance (LLM integration)
  - Layer 4: Expert escalation queue
  - Layer 5: Continuous learning from resolved tickets

**Architecture (11,492 total lines across 19 files):**

```
Ticket → [Failure Card Matching] → [Decision Tree] → [AI Guidance] → [Expert Queue]
                 ↓                        ↓                ↓               ↓
         EFI Embedding Service    EFI Decision Engine   AI Guidance    Expert Queue
         (embedding_service.py)   (efi_decision_engine) (ai_guidance)  (expert_queue)
                 ↓                        ↓                ↓               ↓
         failure_cards collection  efi_decision_trees   ai_queries     expert_escalations
         knowledge_embeddings     efi_sessions         ai_guidance_*   learning_events
```

**CRITICAL Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| **efi_decision_engine.py: ZERO org_id** | P0 | 471 lines, ALL DB operations unscoped. Sessions, trees, learning items accessible cross-tenant. See Section 1.1.1 |
| **efi_embedding_service.py: ZERO org_id** | P0 | 612 lines, similarity searches return cross-tenant failure cards. See Section 1.1.2 |
| **embedding_service.py: ZERO org_id** | P0 | 462 lines, embedding cache and card queries unscoped. See Section 1.1.3 |
| failure_intelligence_service.py scoping | P1 | Only 3 org_id references. Most internal methods lack scoping. `find_matching_cards` (the core matching function) may return global results |
| model_aware_ranking_service.py soft scoping | P1 | `organization_id: Optional[str]` — ranking uses `$or` with `[{org_id}, {None}]` which can return global results |
| Decision tree → Estimate handoff | P1 | `get_suggested_estimate` (efi_decision_engine.py:309) generates estimate data from session but doesn't include org_id in the estimate template |
| No EFI data ownership tracking | P2 | Failure cards created by org A can be surfaced to org B through similarity search |
| Learning engine cross-pollination | P2 | `EFILearningEngine.capture_job_completion` (line 359) stores learning data that may be processed globally |
| AI query logging lacks tenant isolation | P1 | `ai_assist_service.py:69`: `organization_id` set to `"global"` as fallback |

**Architectural Gap:** The EFI system was designed with a "shared knowledge" philosophy (global failure cards benefit all tenants), but this conflicts with the multi-tenant isolation requirement. The system needs a clear `scope` field (global vs tenant) on all EFI data, with tenant-specific data strictly isolated.

### 8.4 Step 3: Estimate Generation

**Files:** `routes/estimates_enhanced.py` (3011 lines), `services/ticket_estimate_service.py`

**Implementation:**
- Estimate creation from ticket or standalone
- Line item management (add/update/delete)
- Status workflow: Draft → Sent → Approved → Declined/Expired
- Estimate locking mechanism
- PDF generation
- Public estimate viewing (shareable link)
- Bulk status operations
- Estimate history tracking

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| `organization_id` set at line 60 only | P1 | `query["organization_id"] = org_id` — this is the ONLY place org_id is set for the entire list query. Other endpoints rely on `ticket_estimate_service` which does scope |
| Estimate → Invoice conversion (line 2210+) | P1 | Conversion pulls org_id from `estimate.get("organization_id")` — if estimate was created without org_id (legacy data), conversion creates an unscoped invoice |
| No estimate number sequence per org | P2 | Uses UUID-based IDs |
| Public estimate view bypass | INFO | `/estimates/public/{id}` is public by design — no auth needed. Security relies on estimate_id being unguessable |
| `ticket_estimate_service.py` properly scoped | ✓ | Service uses org_id consistently in queries and inserts |

### 8.5 Step 4: Customer Approval

**Implementation:** Estimate status transition from `sent` → `approved`/`declined`

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| Customer approval via shared link | INFO | Customer receives a link, views estimate, approves. No customer auth required — security by obscurity (UUID link) |
| No digital signature/consent record | P2 | No cryptographic proof of customer approval |
| No approval expiry enforcement | P2 | Estimates can have `expiry_date` but expired estimates can still be approved (no server-side block) |
| Approval notification | PARTIAL | Email sending is mocked (`routes/estimates_enhanced.py:2132`) |

### 8.6 Step 5: Parts Allocation

**Files:** `services/inventory_service.py`, `routes/inventory_enhanced.py`

**Implementation:**
- `allocate_for_ticket()` — reserves parts for a ticket
- `use_allocation()` — marks allocated parts as used
- `return_allocation()` — returns unused parts to stock
- Serial/batch tracking available
- COGS posting on usage

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| `organization_id` parameter optional in `use_allocation` | P1 | `services/inventory_service.py:176`: `organization_id: str = None`. Falls back to allocation's org_id, but if allocation lacks org_id, scoping fails |
| No automatic allocation from estimate | P2 | Estimate approval doesn't auto-allocate parts. Manual step required |
| COGS posting on allocation use | ✓ | `_post_cogs_entry` (line 285) correctly creates journal entries |
| Stock level validation | ✓ | Checks available quantity before allocation |
| Multi-warehouse support | PARTIAL | Warehouses exist in schema but allocation doesn't consider warehouse location |

### 8.7 Step 6: Work Execution

**Files:** `services/ticket_service.py` (`start_work` method, line 756)

**Implementation:**
- Technician starts work → ticket status changes to `in_progress`
- Time tracking integration
- Activity logging

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| No work-in-progress cost tracking | P2 | Time spent is tracked but not costed (no labour rate × hours calculation) |
| No parts consumption tracking during work | P2 | Parts allocated are used/returned manually, not tied to work steps |
| Technician assignment validation | P1 | No check that the technician starting work is the one assigned to the ticket |

### 8.8 Step 7: Work Completion

**Files:** `services/ticket_service.py` (`complete_work` method, line 812)

**Implementation:**
- Work completion with resolution notes
- Final parts used/returned reconciliation
- Quality check fields
- EFI learning capture on completion
- Event emission: `TICKET_COMPLETED`

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| EFI learning capture cross-tenant risk | P1 | `_update_efi_platform_patterns` (line 632) feeds completion data to EFI system which has no tenant isolation (see Section 8.3) |
| No mandatory checklist before completion | P2 | No enforced quality checklist |
| No customer sign-off workflow | P2 | Work completed without customer confirmation |

### 8.9 Step 8: Invoice Generation

**Files:** `routes/invoices_enhanced.py` (2407 lines), `services/invoice_service.py`

**Implementation:**
- Invoice creation (standalone or from estimate/ticket)
- GST calculation integration
- PDF generation with QR code
- Public invoice viewing (shareable link)
- Recurring invoice support
- Credit note integration
- Payment allocation
- Email/WhatsApp sending

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| Invoice from estimate conversion | P1 | `routes/estimates_enhanced.py:2210+` — org_id from estimate may be missing in legacy data |
| Invoice number sequence | ✓ | Uses organization-specific numbering |
| Double-entry posting on invoice creation | ✓ | `posting_hooks.post_invoice_journal_entry()` called |
| Invoice → Payment allocation | ✓ | Payment received can be allocated to specific invoices |
| `.to_list(5000)` for export | P1 | `routes/invoices_enhanced.py:2371` — unbounded export query |
| E-invoice integration | NOT IMPLEMENTED | IRN generation is a placeholder |

### 8.10 Step 9: Payment Collection

**Files:** `routes/payments_received.py` (1380 lines), `routes/invoice_payments.py`

**Implementation:**
- Payment recording with multiple modes (cash, bank transfer, UPI, cheque, Razorpay)
- Payment allocation to invoices
- Excess payment handling
- Payment receipt PDF
- Razorpay integration for online payments

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| `.to_list(10000)` for export | P1 | `routes/payments_received.py:278,669` — unbounded export |
| Double-entry posting on payment | ✓ | `posting_hooks.post_payment_received_journal_entry()` |
| No advance payment tracking | P2 | No advance against invoice concept |
| No TDS deduction on payment | P2 | Customer may deduct TDS before paying — this is not tracked |
| Razorpay webhook lacks org_id validation | P1 | Webhook processes payment by payment_id without verifying it belongs to the claimed org |

### 8.11 Step 10: Journal Entry / Accounting

**Files:** `services/double_entry_service.py` (1649 lines), `routes/journal_entries.py`, `services/posting_hooks.py`

**Implementation:**
- Automatic journal entries for: Invoice, Payment, Bill, Bill Payment, Expense, Payroll
- Manual journal entry creation
- Entry reversal
- Trial Balance, P&L, Balance Sheet
- Account ledger with running balance

**Findings:**

| Finding | Severity | Detail |
|---------|----------|--------|
| Organization-scoped CoA | ✓ | System accounts created per organization |
| Journal entry → org_id always set | ✓ | `create_journal_entry` requires `organization_id` parameter |
| No period lock enforcement | P1 | `posting_hooks.py` does NOT check `period_locks` before creating entries. An invoice dated in a locked period will still post |
| `.to_list(10000)` for ledger | P1 | `services/double_entry_service.py:1594` |
| No unposted entry queue | P2 | `post_all_unposted_invoices` (posting_hooks.py:294) exists but no automated trigger |
| No reconciliation with bank | P2 | Bank transactions and journal entries are separate systems |

### 8.12 Chain Integrity Summary

**End-to-End Chain Status:**

| Step | Link to Next | Status | Gap |
|------|-------------|--------|-----|
| 1→2 Ticket → EFI | Ticket ID passed to EFI matching | ✓ LINKED | EFI lacks tenant isolation |
| 2→3 EFI → Estimate | Decision tree suggests estimate | WEAK | `get_suggested_estimate` output lacks org_id |
| 3→4 Estimate → Approval | Status change + notification | PARTIAL | Notification mocked |
| 4→5 Approval → Allocation | MANUAL | BROKEN | No automatic trigger |
| 5→6 Allocation → Work | MANUAL | BROKEN | No automatic trigger |
| 6→7 Work → Completion | Status change | ✓ LINKED | |
| 7→8 Completion → Invoice | Semi-automatic | PARTIAL | Can create invoice from ticket but not automatic |
| 8→9 Invoice → Payment | Payment allocation | ✓ LINKED | |
| 9→10 Payment → Journal | Posting hooks | ✓ LINKED | Period lock not enforced |

**Critical Broken Links:** Steps 4→5 and 5→6 require manual intervention with no system-guided workflow.

---

# Section 9 — EFI Architecture

This section receives the DEEPEST audit as it is the core product differentiator.

## 9.1 EFI System Components (11,492 total lines)

### 9.1.1 Service Layer Components

| Component | File | Lines | Purpose | Tenant Isolation |
|-----------|------|-------|---------|-----------------|
| EFI Decision Engine | `services/efi_decision_engine.py` | 471 | Guided diagnostic step-by-step execution | **NONE** |
| EFI Embedding Service | `services/efi_embedding_service.py` | 612 | Vector similarity for failure card matching | **NONE** |
| Generic Embedding Service | `services/embedding_service.py` | 462 | Base embedding operations, cache management | **NONE** |
| Failure Intelligence Service | `services/failure_intelligence_service.py` | 983 | Core EFI business logic, card CRUD, matching | PARTIAL (3 refs) |
| Continuous Learning Service | `services/continuous_learning_service.py` | 524 | Post-resolution learning, model updates | PARTIAL (8 refs) |
| Model-Aware Ranking | `services/model_aware_ranking_service.py` | 413 | Vehicle model-specific failure ranking | PARTIAL (4 refs, Optional) |
| Expert Queue Service | `services/expert_queue_service.py` | 642 | Human expert escalation workflow | ✓ (10 refs) |
| Knowledge Store Service | `services/knowledge_store_service.py` | 465 | Knowledge article management | ✓ (14 refs) |
| AI Assist Service | `services/ai_assist_service.py` | 515 | LLM-powered general AI assistance | PARTIAL (fallback to "global") |
| AI Guidance Service | `services/ai_guidance_service.py` | 1069 | LLM-powered diagnostic guidance | ✓ (12+ refs) |
| EFI Seed Data | `services/efi_seed_data.py` | 1385 | Initial failure card/tree data | N/A (seed script) |

### 9.1.2 Route Layer Components

| Component | File | Lines | Tenant Isolation |
|-----------|------|-------|-----------------|
| EFI Guided Routes | `routes/efi_guided.py` | 690 | ✓ (uses `extract_org_id` on every endpoint) |
| EFI Intelligence Routes | `routes/efi_intelligence.py` | 604 | ✓ (uses `organization_id` in queries) |
| Failure Intelligence Routes | `routes/failure_intelligence.py` | 683 | PARTIAL (only 1 org_id ref at line 125) |
| Failure Cards Routes | `routes/failure_cards.py` | 264 | ✓ (uses `ctx.org_id`) |
| Knowledge Brain Routes | `routes/knowledge_brain.py` | 532 | ✓ (uses `org_id` consistently) |
| Expert Queue Routes | `routes/expert_queue.py` | 347 | ✓ (uses `org_id`) |
| AI Assistant Routes | `routes/ai_assistant.py` | 202 | MINIMAL (1 ref, delegates to service) |
| AI Guidance Routes | `routes/ai_guidance.py` | 629 | ✓ (uses `org_id` consistently) |

## 9.2 EFI Data Flow Architecture

### 9.2.1 Failure Card Matching Flow

```
1. Ticket created with symptoms/description
2. routes/efi_guided.py calls get_matching_cards()
3. → failure_intelligence_service.find_matching_cards()
4.   → embedding_service.find_similar() [NO ORG_ID]
5.     → Queries failure_cards collection [NO ORG_ID FILTER]
6.     → Returns similarity-ranked cards from ALL tenants
7. → efi_embedding_service.find_similar_failure_cards() [NO ORG_ID]
8.   → Also returns cross-tenant cards
9. Route layer filters by org_id AFTER receiving results
```

**Critical Issue:** The similarity search happens GLOBALLY, then route-level filtering attempts to restrict. But:
- Performance waste: searches across all tenants before filtering
- If route-level filtering has a bug, cross-tenant data leaks
- Embedding vectors themselves may leak information (if embeddings are compared across tenants)

### 9.2.2 Decision Tree Execution Flow

```
1. Failure card selected → Tree loaded from efi_decision_trees
2. Session created → efi_sessions [NO ORG_ID]
3. Technician executes steps, recording pass/fail
4. Each step outcome recorded → efi_sessions.update [NO ORG_ID]
5. Tree branches based on outcome
6. Resolution reached → suggested estimate generated [NO ORG_ID]
7. Learning captured → learning_queue [NO ORG_ID]
```

**Critical Issue:** The entire decision tree execution is tenant-blind. Any user with a valid session_id from another tenant could:
1. Read the session state
2. Record step outcomes
3. Modify the session
4. Access the suggested estimate

### 9.2.3 Continuous Learning Flow

```
1. Ticket completed with resolution data
2. ticket_service._update_efi_platform_patterns() 
3. → continuous_learning_service.capture_job_completion()
4.   → Stores learning event [HAS ORG_ID]
5.   → Queue for model update processing
6. Batch processing:
7.   → Reads learning_queue [HAS ORG_ID]
8.   → Updates failure card statistics [NO ORG_ID in embedding update]
9.   → May cross-pollinate via embedding similarity
```

**Partial Fix:** Learning events DO have org_id. But when these events are processed and used to update failure card embeddings/statistics, the update functions in `efi_embedding_service.py` have no org_id, meaning updates affect global card data.

## 9.3 EFI Collections Map

| Collection | Used By | Has org_id | In TENANT_COLLECTIONS | Status |
|------------|---------|-----------|----------------------|--------|
| `failure_cards` | Multiple services | MIXED | YES | Declared tenant but queried without org_id by 3 services |
| `efi_decision_trees` | Decision engine | NO | NO | **Missing from both TENANT and GLOBAL lists** |
| `efi_sessions` | Decision engine | NO | NO | **Missing from both TENANT and GLOBAL lists** |
| `learning_queue` | Learning service | YES | NO | Missing from guard lists |
| `knowledge_articles` | Knowledge store | YES | YES (mixed scope) | Correctly mixed-scope |
| `knowledge_embeddings` | Knowledge store | YES | YES | ✓ |
| `embedding_cache` | Embedding service | NO | NO | Missing from guard lists |
| `ai_queries` | AI assist | YES | NO | Missing from guard lists |
| `ai_escalations` | AI assist | YES | NO | Missing from guard lists |
| `ai_guidance_snapshots` | AI guidance | YES | YES | ✓ |
| `ai_guidance_feedback` | AI guidance | YES | YES | ✓ |
| `expert_escalations` | Expert queue | YES | YES | ✓ |
| `technician_actions` | Failure intelligence | YES | YES | ✓ |
| `part_usage` | Failure intelligence | YES | YES | ✓ |
| `symptoms` | Failure intelligence | UNKNOWN | NO | Missing from guard lists |
| `knowledge_relations` | Failure intelligence | UNKNOWN | NO | Missing from guard lists |
| `efi_events` | Failure intelligence | UNKNOWN | NO | Missing from guard lists |
| `model_risk_alerts` | Model ranking | YES | YES | ✓ |
| `structured_failure_cards` | EFI intelligence | YES | YES | ✓ |

**Collections missing from TenantGuard lists (guard.py TENANT_COLLECTIONS):**
- `efi_decision_trees`
- `efi_sessions`
- `learning_queue`
- `embedding_cache`
- `ai_queries`
- `ai_escalations`
- `symptoms`
- `knowledge_relations`
- `efi_events`

This means even if routes/services start passing org_id, the TenantGuard middleware won't auto-inject or validate org_id for these collections.

## 9.4 EFI Remediation Priorities

| Priority | Action | Impact |
|----------|--------|--------|
| P0 | Add `organization_id` to ALL operations in `efi_decision_engine.py` | Isolate diagnostic sessions per tenant |
| P0 | Add `organization_id` to ALL operations in `efi_embedding_service.py` | Isolate similarity searches per tenant |
| P0 | Add `organization_id` to ALL operations in `embedding_service.py` | Isolate embedding cache per tenant |
| P0 | Add `efi_decision_trees`, `efi_sessions`, `embedding_cache` to TENANT_COLLECTIONS in guard.py | Enable middleware validation |
| P1 | Implement `scope` field on `failure_cards` (global/tenant) with proper filtering | Allow shared knowledge while protecting tenant-specific data |
| P1 | Add org_id propagation to `failure_intelligence_service.py` internal methods | Ensure all internal queries are scoped |
| P1 | Fix `model_aware_ranking_service.py` — make org_id required, not optional | Prevent global result fallback |
| P2 | Add org_id to remaining missing collections in guard.py | Complete the isolation map |

---

# Section 10 — Module Completeness (24 Modules)

## 10.1 Module Inventory and Status

| # | Module | Route File | Lines | Status | Completeness |
|---|--------|-----------|-------|--------|-------------|
| 1 | Authentication | `auth.py`, `auth_main.py` | ~400 | COMPLETE | 90% — Google OAuth exists, password reset works |
| 2 | Organizations | `organizations.py` | 1345 | COMPLETE | 85% — Full CRUD, onboarding, branding, settings |
| 3 | Tickets | `tickets.py` | ~400 | COMPLETE | 80% — Full lifecycle, EFI integration |
| 4 | Items | `items_enhanced.py` | 3423 | COMPLETE | 95% — Largest module, recently patched for tenant isolation |
| 5 | Contacts | `contacts_enhanced.py` | 2245 | COMPLETE | 85% — Customer/vendor management |
| 6 | Invoices | `invoices_enhanced.py` | 2407 | COMPLETE | 85% — Full lifecycle, GST, PDF, email |
| 7 | Estimates | `estimates_enhanced.py` | 3011 | COMPLETE | 80% — Full workflow, PDF, public view |
| 8 | Bills | `bills_enhanced.py` | 976 | FUNCTIONAL | 70% — CRUD + approval, needs more features |
| 9 | Payments | `payments_received.py` | 1380 | FUNCTIONAL | 75% — Multi-mode payment, allocation |
| 10 | Sales Orders | `sales_orders_enhanced.py` | 1557 | FUNCTIONAL | 70% — Full lifecycle, sending mocked |
| 11 | Inventory | `inventory_enhanced.py` | 1734 | FUNCTIONAL | 75% — Stock tracking, allocations, serial/batch |
| 12 | HR/Payroll | `hr.py` | 1879 | FUNCTIONAL | 60% — Payroll, TDS, Form 16. Many statutory gaps |
| 13 | GST | `gst.py` | 1146 | FUNCTIONAL | 50% — GSTR-1/3B only. Many compliance gaps |
| 14 | EFI/AI | 8 route files | ~4000 | FUNCTIONAL | 65% — Rich feature set but tenant isolation broken |
| 15 | Reports | `reports.py`, `reports_advanced.py` | 2350 | FUNCTIONAL | 70% — Multiple report types |
| 16 | Banking | `banking.py`, `banking_module.py` | 1317 | FUNCTIONAL | 60% — Account CRUD, transactions, no reconciliation |
| 17 | Journal Entries | `journal_entries.py` | ~500 | FUNCTIONAL | 75% — CRUD + auto-posting |
| 18 | Projects | `projects.py` | 813 | SKELETON | 40% — Basic CRUD, no PM features |
| 19 | Time Tracking | `time_tracking.py` | ~500 | FUNCTIONAL | 60% — Clock in/out, entries |
| 20 | Subscriptions | `subscriptions.py` | 725 | FUNCTIONAL | 70% — Plan management, entitlements |
| 21 | Customer Portal | `customer_portal.py` | ~500 | FUNCTIONAL | 60% — View tickets/invoices |
| 22 | Technician Portal | `technician_portal.py` | 769 | FUNCTIONAL | 55% — View assignments, update tickets |
| 23 | Platform Admin | `platform_admin.py` | ~600 | FUNCTIONAL | 65% — Org management, flags |
| 24 | Documents | `documents.py` | ~400 | FUNCTIONAL | 50% — Upload/download, no versioning |

## 10.2 Mocked/Placeholder Features

| Feature | File | Line | Status |
|---------|------|------|--------|
| Sales order sending | `sales_orders_enhanced.py:1237` | Mocked | "Send sales order to customer (mocked)" |
| Estimate sending | `estimates_enhanced.py:2132` | Mocked | "Send estimate to customer (mocked)" |
| Contact welcome email | `contacts_enhanced.py:984` | Mocked | |
| Portal invite sending | `contacts_enhanced.py:1509` | Mocked | |
| Statement PDF | `contacts_enhanced.py:1612` | Mocked | |
| Statement email | `contacts_enhanced.py:1622` | Mocked | |
| Payment thank you email | `payments_received.py:510` | Mocked | |
| E-Invoice IRN | `gst.py` (module docstring) | Placeholder | |
| Customer notification on stock | `inventory_enhanced.py:856` | TODO | |
| Credit note from inventory | `inventory_enhanced.py:1001` | TODO | |
| WhatsApp Business API | `services/whatsapp_service.py` | REAL (not mocked) | Requires per-org Meta credentials |

## 10.3 Missing Modules (Not Implemented)

| Module | Priority | Description |
|--------|----------|-------------|
| Purchase Orders (enhanced) | P1 | Only basic `purchase_orders` collection exists. No full PO workflow |
| Warehouse Management | P2 | Warehouses exist in schema but no inter-warehouse transfer workflow |
| Approval Workflows | P1 | No configurable multi-level approval chains |
| Custom Reports Builder | P2 | Reports are hardcoded, no user-defined report builder |
| Audit Trail Viewer | P2 | Audit logs exist but no user-facing viewer/search |
| Notifications Center | P1 | Notification service exists but no in-app notification delivery |
| Dashboard Customization | P2 | Fixed dashboard layouts |
| Vendor Portal | P2 | Customer/business portals exist, no vendor self-serve portal |

---

# Section 11 — Test Coverage

## 11.1 Test Suite Overview

- **Total test files:** 122
- **Last known results:** 322 passed, 0 failed, 51 skipped
- **Test framework:** pytest
- **Test location:** `backend/tests/`

## 11.2 Coverage by Module

| Module | Test Files | Coverage Assessment |
|--------|-----------|-------------------|
| Items | `test_items_enhanced.py`, `test_items_phase2.py`, `test_items_phase3.py`, `test_items_zoho_features.py`, `test_items_enhanced_zoho_columns.py`, `test_items_enhanced_parts_fix.py` | HIGH — 6 dedicated files |
| Estimates | `test_estimates_enhanced.py`, `test_estimates_phase1.py`, `test_estimates_phase2.py`, `test_estimate_bug_fixes.py`, `test_estimate_edit_status.py`, `test_estimate_workflow_buttons.py` | HIGH — 6 dedicated files |
| Invoices | `test_invoices_estimates_enhanced_zoho.py`, `test_invoice_automation.py`, `test_invoice_notification.py` | MEDIUM — 3 files |
| Contacts | `test_contacts_enhanced.py`, `test_contacts_invoices_enhanced.py`, `test_contact_integration.py`, `test_customers_enhanced.py` | HIGH — 4 files |
| HR/Payroll | `test_hr_module.py`, `test_employee_creation.py`, `test_employee_module.py` | MEDIUM — 3 files, but payroll calculation tests incomplete |
| GST | `test_gst_module.py`, `test_gst_accounting_flow.py`, `test_gstr3b_credit_notes.py` | MEDIUM — 3 files |
| EFI | `test_efi_guidance.py`, `test_efi_guided.py`, `test_efi_intelligence.py`, `test_efi_intelligence_api.py`, `test_efi_module.py`, `test_efi_search_embeddings.py` | HIGH — 6 files, but no tenant isolation tests for EFI |
| Tenant Isolation | `test_tenant_isolation.py`, `test_multi_tenant.py`, `test_multi_tenant_crud.py`, `test_multi_tenant_scoping.py` | MEDIUM — 4 files, but based on current findings many gaps remain untested |
| RBAC | `test_rbac_portals.py` | LOW — 1 file |
| Subscriptions | `test_subscription_entitlements_api.py`, `test_subscription_safety_fixes.py`, `test_team_subscription_management.py` | MEDIUM — 3 files |
| Reports | `test_reports.py` | LOW — 1 file for 2 route files |
| Banking | `test_banking_stock_transfers.py` | LOW — 1 file (combined with stock transfers) |
| Payments | `test_payments_received.py` | LOW — 1 file |
| Inventory | `test_inventory_adjustments_v2.py`, `test_inventory_adjustments_phase2.py`, `test_inventory_hr_modules.py` | MEDIUM — 3 files |
| Period Locks | `test_period_locks.py` | LOW — 1 file |
| Customer Portal | `test_customer_portal.py`, `test_customer_portal_auth.py`, `test_cross_portal_validation.py` | MEDIUM — 3 files |
| Double-Entry | `test_finance_module.py` | LOW — 1 file for 1649 lines of service code |

## 11.3 Skipped Test Analysis

51 tests are skipped. Major skip categories:

### Data-Dependent Skips
Tests that skip because expected data doesn't exist (draft estimates, contacts, invoices, etc.). These need data fixture creation.

### Authentication-Dependent Skips
- `test_final_certification.py:70`: Admin login failed
- `test_final_certification.py:87`: Tech login failed
- `test_reports.py:30`: Auth failed

### Feature-Dependent Skips
- `test_gst_module.py:200`: GSTIN persistence issue (marked as pre-existing)
- `test_composite_items_invoice_settings.py`: Multiple skips for missing inventory items

### Workflow-Dependent Skips
- `test_ticket_estimate_integration.py`: 20+ skips — estimate locking workflow makes tests fragile

## 11.4 Test Coverage Gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| No EFI tenant isolation tests | P0 | No test verifies that EFI data is tenant-scoped |
| No cross-tenant data leak tests | P0 | No test creates data in Org A and verifies it's invisible to Org B |
| No double-entry balance verification tests | P1 | No test verifies debit = credit after complex operations |
| No GST calculation accuracy tests | P1 | No test verifies CGST/SGST/IGST split correctness |
| No payroll statutory tests | P1 | No test verifies PF/ESI/PT calculations against Indian law |
| No workflow chain end-to-end test | P1 | No test executes the full 10-step chain |
| No load/stress tests for pagination | P2 | No test verifies the `.to_list(10000)` endpoints under load |
| No RBAC negative tests | P2 | No test verifies that a technician CANNOT access finance routes |
| No period lock enforcement test | P2 | No test verifies that journal entries in locked periods are rejected |
| No concurrent modification tests | P2 | No test for race conditions in inventory allocation |

---

# Section F — Verification Gaps & Audit Limitations

## F.1 What This Audit Could NOT Verify

| Limitation | Reason | Impact |
|-----------|--------|--------|
| Runtime behavior of middleware chain | Read-only audit, no live testing | Middleware ordering is correct in code, but actual runtime interaction untested |
| Actual cross-tenant data leak | No live database access | Pattern violations identified but not confirmed as exploitable |
| Frontend tenant context propagation | Backend-only audit | Frontend may or may not correctly pass X-Organization-ID header |
| Razorpay webhook authenticity | No production credentials | Webhook signature verification not audited |
| Email delivery | Mocked in code | Cannot verify email actually delivers |
| LLM provider tenant isolation | External service | OpenAI/Gemini API calls may log tenant data |
| MongoDB index effectiveness | No query plan analysis | Compound indexes exist but query performance not verified |
| JWT secret strength | Not inspectable | JWT_SECRET value not visible, only usage pattern audited |
| Production environment config | Different from dev | CSRF secure flag, CORS origins, rate limit storage may differ |

## F.2 Files NOT Fully Examined

Due to the breadth of the codebase (58,000+ lines of route code, 15,000+ lines of service code), these files were examined at grep/pattern level but not line-by-line:

| File | Lines | Reason |
|------|-------|--------|
| `routes/items_enhanced.py` | 3423 | Recently patched — spot-checked only `log_item_history` |
| `routes/estimates_enhanced.py` | 3011 | Spot-checked key areas |
| `routes/contacts_enhanced.py` | 2245 | Pattern-level check |
| `routes/reports.py` | 1639 | Pattern-level check |
| `routes/sla.py` | 934 | org_id confirmed at pattern level |
| `routes/banking_module.py` | 927 | Separate from `banking.py`, assumed similar patterns |
| `services/efi_seed_data.py` | 1385 | Seed script — not production code path |
| Most test files | 122 files | Analyzed skip patterns, not test correctness |

## F.3 Assumptions Made

1. TenantGuardMiddleware runs on ALL non-public routes (confirmed by middleware chain order and server.py mounting)
2. `extract_org_id` will find `request.state.tenant_org_id` set by middleware (correct per middleware code)
3. UUID-based IDs are sufficiently unguessable for public links (statistically sound but not cryptographically guaranteed)
4. MongoDB _id serialization issues are addressed (projection `{"_id": 0}` used consistently based on prior sprint work)

## F.4 Auditor's Confidence Levels

| Section | Confidence | Rationale |
|---------|-----------|-----------|
| Section 1 (Tenant Isolation) | HIGH | Comprehensive grep + file analysis |
| Section 2 (User Isolation) | MEDIUM | Pattern-level, not line-by-line |
| Section 3 (Middleware) | HIGH | Full file review of all 5 middleware files |
| Section 4 (RBAC) | HIGH | Full review of rbac.py + route mapping |
| Section 5 (Accounting) | HIGH | Full review of double_entry_service.py functions |
| Section 6 (GST) | HIGH | Full review of gst.py + compliance gap analysis |
| Section 7 (Payroll) | HIGH | Full review of hr_service.py + Indian law comparison |
| Section 8 (Workflow Chain) | HIGH | Deep trace through all 10 steps |
| Section 9 (EFI Architecture) | HIGH | Every EFI service and route file analyzed |
| Section 10 (Module Completeness) | MEDIUM | Based on file existence + pattern analysis |
| Section 11 (Test Coverage) | MEDIUM | Based on file listing + skip analysis |

---

# Appendix A — Remediation Priority Matrix

## P0 — Critical (Must Fix Before Production)

| ID | Finding | Section | Files |
|----|---------|---------|-------|
| P0-01 | EFI Decision Engine — zero tenant isolation | 9.1 | `services/efi_decision_engine.py` |
| P0-02 | EFI Embedding Service — zero tenant isolation | 9.1 | `services/efi_embedding_service.py` |
| P0-03 | Embedding Service — zero tenant isolation | 9.1 | `services/embedding_service.py` |
| P0-04 | Professional Tax hardcoded flat ₹200 for all states | 7.1.4 | `services/hr_service.py` |
| P0-05 | ESI employer contribution not calculated correctly (only employee share) | 7.1.3 | `services/hr_service.py` |
| P0-06 | 9 EFI collections missing from TenantGuard TENANT_COLLECTIONS | 9.3 | `core/tenant/guard.py` |

## P1 — High (Must Fix Within Sprint)

| ID | Finding | Section | Files |
|----|---------|---------|-------|
| P1-01 | `log_item_history` missing organization_id in inserted docs | 1.1.11 | `routes/items_enhanced.py:2827` |
| P1-02 | `org_query` silently drops org_id when null | 1.2 | `utils/database.py:29` |
| P1-03 | Notification service — no org_id on logs or queries | 1.1.4 | `services/notification_service.py` |
| P1-04 | 32+ queries with `.to_list(5000-10000)` remaining | 1.4 | Multiple files |
| P1-05 | No period lock enforcement on journal entry creation | 8.11 | `services/posting_hooks.py` |
| P1-06 | PF ceiling not enforced (₹15,000 basic cap) | 7.1.2 | `services/hr_service.py` |
| P1-07 | GSTR-1 missing B2C/CDN/HSN-by-rate sections | 6.1.4 | `routes/gst.py` |
| P1-08 | GSTR-3B missing ITC categorization | 6.1.5 | `routes/gst.py` |
| P1-09 | No fiscal year concept in accounting | 5.1.2 | `services/double_entry_service.py` |
| P1-10 | RBAC fallthrough for unmapped routes | 3.2.3 | `middleware/rbac.py:282` |
| P1-11 | Workflow chain broken at Steps 4→5 and 5→6 | 8.12 | Architecture gap |
| P1-12 | `failure_intelligence_service.py` — internal methods lack org_id | 9.1 | `services/failure_intelligence_service.py` |
| P1-13 | `model_aware_ranking_service.py` — org_id optional | 9.1 | `services/model_aware_ranking_service.py` |
| P1-14 | `ai_assist_service.py` — org_id defaults to "global" | 9.1 | `services/ai_assist_service.py` |
| P1-15 | Scheduler/EventProcessor — no org_id | 1.1.5/6 | `services/scheduler.py`, `services/event_processor.py` |
| P1-16 | Ticket creation org_id optional in service | 8.2 | `services/ticket_service.py:120` |
| P1-17 | Razorpay webhook lacks org_id validation | 8.10 | `routes/razorpay.py` |
| P1-18 | No cross-tenant data leak tests | 11.4 | Test gap |

## P2 — Medium (Backlog)

| ID | Finding | Section | Files |
|----|---------|---------|-------|
| P2-01 | CSRF secure flag hardcoded False | 3.2.1 | `middleware/csrf.py` |
| P2-02 | Rate limiting in-memory only | 3.2.2 | `middleware/rate_limit.py` |
| P2-03 | Estimate → Invoice conversion org_id from legacy data | 8.4 | `routes/estimates_enhanced.py` |
| P2-04 | Multiple mocked email/notification features | 10.2 | Various |
| P2-05 | No HRA exemption calculation | 7.1.5 | `services/hr_service.py` |
| P2-06 | No Section 80C/80D deduction tracking | 7.1.5 | `services/hr_service.py` |
| P2-07 | No gratuity/bonus calculation | 7.1.6 | `services/hr_service.py` |
| P2-08 | No e-Way bill generation | 6.1.6 | Not implemented |
| P2-09 | No GSTR-2A/2B reconciliation | 6.1.6 | Not implemented |
| P2-10 | Projects module is skeleton | 10.1 | `routes/projects.py` |
| P2-11 | Technician sees all org tickets (Pattern D) | 2.1.1 | `routes/technician_portal.py` |
| P2-12 | No work-in-progress cost tracking | 8.7 | Architecture gap |
| P2-13 | No concurrent modification safeguards for inventory | 11.4 | Architecture gap |
| P2-14 | 51 skipped tests need data fixtures | 11.3 | Test infrastructure |
| P2-15 | `period_locks.py` uses `org_id` not `organization_id` | 1.1.12 | `routes/period_locks.py` |
| P2-16 | `inv-adjustments` route prefix not in RBAC map | 4.2.1 | `middleware/rbac.py` |

---

# Appendix B — Quick Reference: Files Needing Immediate Attention

```
# P0 — Zero tenant isolation (entire files need org_id injection)
services/efi_decision_engine.py          471 lines
services/efi_embedding_service.py        612 lines
services/embedding_service.py            462 lines

# P0 — Guard configuration
core/tenant/guard.py                     Add 9 collections to TENANT_COLLECTIONS

# P1 — Specific function/line fixes
routes/items_enhanced.py:2827            log_item_history — add org_id
utils/database.py:29                     org_query — raise on None org_id
services/notification_service.py         Add org_id to all operations
services/hr_service.py:460-462           Fix PF ceiling, ESI employer, PT slabs
routes/gst.py:366,729                    Fix unbounded .to_list(10000) calls
services/posting_hooks.py                Add period_lock check before posting
middleware/rbac.py:282                   Change fallthrough from allow to deny
services/ticket_service.py:120           Make organization_id required
```

---

**End of Audit**

*This document is the master remediation checklist for Battwheels OS. All future development sprints should reference this document for prioritization. Updated: 2026-02-28*
