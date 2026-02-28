# Sprint 5A Final Report — Production Gate: Credentials & Pre-Production Audit

**Sprint Duration:** 2026-03-01
**Sprint Goal:** Wire missing production credentials with graceful degradation, conduct fresh honest audit

---

## A. Credential Status

| Credential | Status | Details |
|------------|--------|---------|
| `SENTRY_DSN` | **SET** | Real DSN (`https://REDACTED...`). Sentry monitoring active. |
| `RESEND_API_KEY` | **SET** | Real key (`REDACTED`). Email service initialized. |
| `RAZORPAY_KEY_ID` | **SET (TEST)** | Test key (`rzp_test_...`). Not live — payment creation works in test mode, will fail for real transactions. |
| `RAZORPAY_KEY_SECRET` | **SET (TEST)** | Test secret (len=8). Paired with test key_id. |
| `RAZORPAY_WEBHOOK_SECRET` | **SET** | Webhook validation active. |
| `IRP_USERNAME` | **N/A** | IRP credentials are stored per-organization in DB via `services/einvoice_service.py` (lines 119-120), not env vars. The e-invoice endpoint returns `"E-Invoice not configured"` gracefully when org hasn't set up IRP config. |
| `IRP_PASSWORD` | **N/A** | Same as above — per-org DB storage. |
| `GEMINI_API_KEY` | **N/A** | Not used directly. Platform uses `EMERGENT_LLM_KEY` (SET, len=30) via emergentintegrations. |
| `JWT_SECRET` | **SET** | Real secret (len=64). |
| `MONGO_URL` | **SET** | Local MongoDB connection. Production uses separate Atlas instance. |
| `CORS_ORIGINS` | **SET** | Configured (len=53). |

### Failure Modes:

| Credential | If Missing | Failure Mode | File:Line |
|------------|-----------|--------------|-----------|
| `SENTRY_DSN` | Already graceful | `if SENTRY_DSN:` guard — skips init, logs warning | `server.py:35-43` |
| `RESEND_API_KEY` | Already graceful | Returns `{"status": "mocked", "message": "Email logged (Resend not configured)"}` | `services/email_service.py:35-41, 188` |
| `RAZORPAY_KEY_ID` | Already graceful | `get_razorpay_client()` returns `None`; endpoints check `is_razorpay_configured()` and return user-friendly message | `routes/razorpay.py:57-58, 63-67, 162` |
| `IRP credentials` | Already graceful | `check_einvoice_eligibility()` returns `{"eligible": false, "reason": "E-Invoice not configured"}`; generate-irn returns `{"success": false, "skip_irn": true}` | `routes/einvoice.py:133-140` |

---

## B. Graceful Degradation Applied

**No changes needed.** All four credential categories already have graceful degradation:

- **Sentry** (`server.py:35-43`): `if SENTRY_DSN:` guard wraps init in try/except. If missing or failed, logs warning and continues.
- **Resend** (`services/email_service.py:29-41`): Checks `RESEND_AVAILABLE and RESEND_API_KEY` before init. Send calls return `{"status": "mocked"}` when unconfigured.
- **Razorpay** (`routes/razorpay.py:48-67`): `get_razorpay_client()` returns `None` when keys missing. All payment endpoints check `is_razorpay_configured()` first.
- **IRP** (`routes/einvoice.py:124-140`): `check_einvoice_eligibility()` queries per-org DB config. Returns non-blocking `skip_irn: true` when unconfigured.

No before/after code — the existing code is already correct.

---

## C. Pre-Production Audit Results

### 3.1 SECURITY

**a. Multi-tenant isolation (org_query scoping):**
```
grep -rn 'org_query(None\|organization_id=None' --include="*.py" services/ routes/
```
**Result: 0 matches.** All queries are scoped. **PASS**

**b. RBAC route registration:**
- Route files on disk: 77
- Routes registered in server.py (V1_ROUTES + API_ROUTES): 75
- **Unregistered: 2** — `fault_tree_import.py` and `stripe_webhook.py`
- `fault_tree_import.py`: Admin utility for importing decision trees — low risk, not exposed
- `stripe_webhook.py`: Legacy/unused Stripe integration — not exposed
- **Verdict: PASS** (unregistered routes are not accessible; they aren't loaded)

**c. Pattern A compliance (unscoped finds):**
```
grep -rn '\.find({"' --include="*.py" services/ routes/ | grep -v org-scoping-terms
```
**Result: 11 matches.** Analyzed each:
| File | Line | Query | Risk |
|------|------|-------|------|
| `failure_intelligence.py:613` | `efi_events.find({"processed": False})` | SHARED-BRAIN (platform-wide event queue) | LOW — processing queue, not tenant data |
| `banking_module.py:731` | `bank_accounts.find({"is_active": True})` | Missing org scope | **MEDIUM** — should be scoped |
| `bills_enhanced.py:423,458` | `po_line_items.find({"po_id": po_id})` | Scoped by po_id (PO is already org-scoped) | LOW |
| `business_portal.py:577` | `amc_plans.find({"is_active": True})` | Platform plans (shared) | LOW |
| `inventory_enhanced.py:574,602,831` | `bundle_components/shipment_items.find({"bundle_id"/"shipment_id": ...})` | Scoped by parent ID | LOW |
| `contacts_enhanced.py:1134` | `contact_tags.find({"tag_id": {"$in": ...}})` | Tag lookup by IDs (already filtered from org-scoped contact) | LOW |
| `inventory_api.py:577` | `services.find({"is_active": True})` | Missing org scope | **MEDIUM** — should be scoped |
| `inventory_adjustments_v2.py:208` | `reasons.find({"is_active": True})` | Shared reference data | LOW |

**Verdict: PARTIAL** — 2 medium-risk unscoped finds (`banking_module.py:731`, `inventory_api.py:577`)

### 3.2 COMPLIANCE

**d. Professional Tax states:** **6 states** implemented in `services/hr_service.py`:
- MH (Maharashtra) — with February adjustment
- KA (Karnataka)
- TN (Tamil Nadu)
- GJ (Gujarat)
- DL (Delhi — no PT)
- UP (Uttar Pradesh — no PT)
**PASS**

**e. Period lock hooks:** **7 hooks** confirmed in `services/posting_hooks.py`:
1. `post_invoice_create` (line 66)
2. `post_payment_received` (line 104)
3. `post_bill_create` (line 143)
4. `post_payment_made` (line 181)
5. `post_expense_create` (line 219)
6. `post_payroll_run` (line 278)
7. `post_journal_reversal` (line 316)
**PASS** — all 7 hooks call `_check_period_lock`

**f. GSTIN checksum:** `compute_gstin_checksum` exists at `routes/gst.py:105`, called by `validate_gstin` at line 145. Used in 4 endpoint paths (validate, settings, GSTR-1 B2B/B2C classification).
**PASS**

### 3.3 EFI BRAIN

**g. Failure cards with embeddings:**
- `failure_cards`: 19 total, **14 with embedding_vector** (all under demo-volt-motors-001)
- `efi_failure_cards`: 0 (unused collection)
- `knowledge_articles`: 0
**PARTIAL** — embeddings exist for seed data but no org-specific cards generated from live tickets

**h. Auto-trigger pipeline:**
- Closed ticket `tkt_ecf2324e6757` via API
- Log confirms: `"Captured learning event LE-B52F0107561E for ticket tkt_ecf2324e6757"`
- `efi_learning_queue`: 33 documents, latest is the test ticket with `status=pending`
- **However:** No background processor converts queue items into failure cards + embeddings
- The pipeline is: ticket_closure → `efi_learning_queue` (WORKING) → failure_card creation + embedding (NOT AUTO-PROCESSED)
**PARTIAL** — capture works, processing does not auto-execute

**i. EFI suggestion quality:**
- Created ticket: "Battery draining fast, 50% range loss" (Electric Scooter, 2W)
- Called `GET /api/v1/efi-guided/suggestions/{ticket_id}`
- Result: Returned "Battery Communication Loss" (confidence 0.87, subsystem: battery)
- The match is semantically adjacent (battery domain) but not exact (communication loss vs capacity loss)
- **Rating: 6/10** — correct subsystem, wrong failure mode. Would improve with more org-specific training data.

### 3.4 TEST COVERAGE

**j. Current test metrics:** **419 passed / 0 failed / 20 skipped — CONFIRMED**

**k. Critical untested paths:**
- Banking module `bank_accounts.find({"is_active": True})` — no org scope test
- `inventory_api.py services.find({"is_active": True})` — no org scope test
- EFI learning queue → failure card processing pipeline — no test
- Razorpay live payment flow — only test keys available
- GSTR-3B ITC with non-zero vendor credits — no test data

### 3.5 KNOWN GAPS

| # | Gap | Status | Impact |
|---|-----|--------|--------|
| 1 | WhatsApp notifications | MOCKED | Notifications logged but not sent |
| 2 | Projects module | UI only | Backend exists, no frontend integration |
| 3 | ITC Rule 42/43 | Deferred to Sprint 5A+ | Hardcoded zero — correct if no exempt supplies |
| 4 | knowledge_articles pipeline | Incomplete | capture_ticket_closure writes to queue but queue not auto-processed |
| 5 | 20 skipped tests | Fixture infra | Complex inter-test dependencies |
| 6 | EFI learning queue processor | Missing | 33 pending items never processed into failure cards |
| 7 | Razorpay LIVE keys | Test only | Payment works in sandbox, not production |
| 8 | banking_module.py:731 | Unscoped find | bank_accounts query missing org_id |
| 9 | inventory_api.py:577 | Unscoped find | services query missing org_id |
| 10 | `efi_failure_cards` collection | Unused | 0 documents — dead schema alongside `failure_cards` (19 docs) |
| 11 | `stripe_webhook.py` | Dead code | Route file exists but not registered |
| 12 | `fault_tree_import.py` | Dead code | Route file exists but not registered |

---

## D. Score Assessment

Using the REMEDIATION_AUDIT_2026.md scoring rubric:

### Security & Isolation: 24/30
- Multi-tenant scoping: 18/20 (2 medium-risk unscoped finds remain)
- RBAC enforcement: 6/10 (all route files registered; 2 dead files not exposed; header spoofing blocked per Sprint 4B test)

### Statutory Compliance: 22/25
- PT: 6 states implemented, Feb adjustment for MH (5/5)
- GST: GSTIN validation, B2B/B2C categorization, GSTR-1/3B reports (8/10 — ITC Rule 42/43 deferred)
- Period locks: All 7 hooks wired (5/5)
- Payroll: PF ceiling, EPS/EPF split, ESI, granular keys (4/5 — no live payslip generation test)

### EFI Architecture: 12/20
- Failure cards with embeddings: 14/19 seeded (3/5)
- Auto-trigger pipeline: capture works, processing does not (2/5)
- Suggestion quality: 6/10 matches on subsystem (3/5)
- Knowledge articles: 0 (pipeline incomplete) (0/5)
- Decision trees: exist but not tested end-to-end (4/5 based on Sprint 3A work)

### Test Coverage: 13/15
- 419 passing tests, 0 failures (8/8)
- Cross-tenant, RBAC negative, GST statutory, journal audit covered (4/5)
- 20 skipped tests remain (1/2)

### Production Readiness: 6/10
- Graceful degradation: all 4 credential types handled (3/3)
- Razorpay: test keys only (0/2)
- Sentry: active (1/1)
- Resend: active (1/1)
- IRP: per-org DB config (not env var) — correct architecture (1/1)
- 2 unscoped DB queries in production code (0/2)

### Total: 77/100

### Gap to 90:
| Item | Points Available | Effort |
|------|-----------------|--------|
| Fix 2 unscoped finds (banking_module, inventory_api) | +4 | 15 min |
| Wire EFI learning queue processor (auto-process pending items) | +4 | 2 hours |
| Process 33 pending queue items into failure cards with embeddings | +2 | 30 min (after processor exists) |
| Razorpay live keys (user must provide) | +2 | User action |
| Fix 5+ of the 20 skipped tests | +1 | 1 hour |
| **Total reachable** | **+13 → 90/100** | |

---

## E. Files Modified

**No source files were modified in Sprint 5A.** This was a read-only audit sprint. All credential degradation was already in place.

---

## F. Test Results

**419 passed / 0 failed / 20 skipped** (unchanged from Sprint 4B)

---

## G. Production

```
verify_prod_org.py: ALL 6 GREEN

  [1] Platform Admin User    — PASS
  [2] Organizations           — PASS (0 orgs, clean SaaS state)
  [3] Subscription Plans      — PASS (4 plans)
  [4] Migrations              — PASS (4 records)
  [5] Unexpected Data Scan    — PASS
  [6] Test Data Contamination — PASS
```

---

## H. Verification Gaps

1. **banking_module.py:731** — `bank_accounts.find({"is_active": True})` has no org scope. Could leak bank accounts across tenants. Needs fix before production.
2. **inventory_api.py:577** — `services.find({"is_active": True})` has no org scope. Could leak service catalog across tenants. Needs fix before production.
3. **EFI learning queue has 33 unprocessed items** — no background processor exists to convert them into failure cards with embeddings. Pipeline is capture-only.
4. **Razorpay in TEST mode** — production payments will fail until live keys are provided.
5. **GSTR-3B ITC 4B/4D tested with zero-data only** — logic is correct but no end-to-end verification with non-zero vendor credits or blocked bills.
6. **No test for EFI suggestion accuracy** — only manual verification done (returned battery-subsystem match at 0.87 confidence for battery-drain ticket).

---

## I. Verdict

- **Credentials:** PARTIALLY SET (all env vars present; Razorpay in test mode)
- **Graceful degradation:** COMPLETE (already in place for all 4 categories)
- **Pre-production audit score:** **77/100**
- **Sprint 5B scope:** **SIGNIFICANT WORK (score < 85)** — need +13 points to reach 90, primarily: fix 2 unscoped queries and wire EFI learning processor
- **Ready for Sprint 5B:** YES
