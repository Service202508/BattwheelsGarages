# Battwheels OS - QA Audit Findings Report
## Phase 1: Calculation & Logic Audit
### Generated: February 2026

---

## EXECUTIVE SUMMARY

| Category | Status | Issues Found |
|----------|--------|--------------|
| Finance Calculator | ✅ PASS | 0 |
| Payment Allocation | ✅ PASS | 0 |
| Tax Calculations | ✅ PASS | 0 |
| Aging Buckets | ✅ PASS | 0 |
| Invoice Data Integrity | ⚠️ WARNING | 2 |
| Zoho Sync Field Mapping | ⚠️ WARNING | 1 |

---

## 1. VERIFIED CALCULATIONS (ALL PASS)

### 1.1 Finance Calculator (`/app/backend/services/finance_calculator.py`)

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Basic line item (exclusive tax) | qty=2, rate=10000, tax=18%, discount=10% | total=21240 | 21240 | ✅ |
| Inclusive tax extraction | total=1180, tax=18% | taxable=1000, tax=180 | Correct | ✅ |
| IGST (inter-state) | amount=5000, tax=18% | IGST=900, CGST=0, SGST=0 | Correct | ✅ |
| CGST/SGST split | amount=10000, tax=18% | CGST=9%=900, SGST=9%=900 | Correct | ✅ |
| Currency rounding | 10.125 | 10.13 (ROUND_HALF_UP) | 10.13 | ✅ |

### 1.2 Payment Allocation (`/app/backend/services/finance_calculator.py`)

| Test | Scenario | Expected | Actual | Status |
|------|----------|----------|--------|--------|
| Oldest-first | Pay 2500 across INV-001(1000), INV-002(2000) | Allocate: 1000, 1500 | Correct | ✅ |
| Over-payment | Pay 1000, balance=500 | Allocate 500, excess=500 | Correct | ✅ |
| Proportional | Pay 1000 across 2 x 1000 invoices | 500 each | Correct | ✅ |
| Unapply | Reverse allocation | Correct reversal amounts | Correct | ✅ |

### 1.3 Tax Calculations

| Test | Scenario | Status |
|------|----------|--------|
| Intra-state (CGST+SGST) | Delhi to Delhi | ✅ Correctly splits |
| Inter-state (IGST) | Delhi to Karnataka | ✅ Correctly applies |
| Reverse tax (inclusive) | Extract tax from total | ✅ Correct formula |
| GST validation | 07AAMCB4976D1ZG | ✅ Valid format |

### 1.4 Aging Buckets

| Due Date vs Today | Expected Bucket | Status |
|-------------------|-----------------|--------|
| Future | current | ✅ |
| Today | current | ✅ |
| 15 days ago | 1-30 | ✅ |
| 45 days ago | 31-60 | ✅ |
| 75 days ago | 61-90 | ✅ |
| 120 days ago | 90+ | ✅ |

---

## 2. DATA INTEGRITY ISSUES

### 2.1 ISSUE: Zoho Sync Field Mapping Mismatch

**Severity:** MEDIUM  
**Location:** `/app/backend/services/zoho_realtime_sync.py`, lines 114-136

**Problem:**
The Zoho Books API returns invoice totals in fields like `total` and `balance`, but the application expects `grand_total` and `balance_due`. This causes synced invoices to have NULL values for these critical fields.

**Evidence:**
```
Zoho-synced invoices: 8264 with grand_total=None
Recent invoices:
  INV-BWG004278: grand_total=None, source=zoho_books
  INV-BWG004277: grand_total=None, source=zoho_books
```

**Field Mapping (Current):**
```python
"invoices": {
    "zoho_to_local": {
        "total": "total",           # ← Should map to "grand_total"
        "balance": "balance",       # ← Should map to "balance_due"
        ...
    }
}
```

**Recommended Fix:**
```python
"invoices": {
    "zoho_to_local": {
        "total": "grand_total",      # ← Fix
        "balance": "balance_due",    # ← Fix
        "sub_total": "subtotal",     # ← Also normalize
        ...
    }
}
```

**Impact:**
- Dashboard financial summaries show incorrect totals
- Invoice listings show 0 for amounts
- Reports are inaccurate

---

### 2.2 ISSUE: Inconsistent Invoice Grand Total Calculation

**Severity:** LOW  
**Invoices Affected:** 2 out of 8270 (0.02%)

**Invoice 1: INV-00034**
```
subtotal: 0
total_tax: 0
total_discount: 866.11
grand_total: 19400.79
line_items_count: 0
```
**Analysis:** This appears to be an incomplete import or corrupted record. No line items exist but discount is applied.

**Invoice 2: INV-00027**
```
Expected: subtotal(2300) + tax(414) - discount(315) + shipping(150) + adjustment(-50) = 2499
Stored: 2699
Difference: 200
```
**Analysis:** Discount may have been double-counted or not applied correctly. Could be a one-time data entry error.

**Recommendation:** 
- Add data validation on invoice save
- Add recalculation API endpoint for admins
- Consider running a one-time data fix script

---

## 3. CALCULATION CODE QUALITY ASSESSMENT

### 3.1 Strengths

1. **Centralized Finance Calculator:** All financial calculations are in one service (`finance_calculator.py`), making it easy to audit and maintain.

2. **Decimal Precision:** Uses Python's `Decimal` type with explicit rounding (ROUND_HALF_UP), avoiding floating-point errors.

3. **GST Compliance:** Correctly handles Indian GST rules (CGST/SGST split, IGST for inter-state).

4. **Optimistic Concurrency:** Estimate service uses version numbers to prevent concurrent edit conflicts.

5. **Inventory Tracking:** Stock reservation/consumption is properly tracked through estimate lifecycle.

### 3.2 Areas for Improvement

1. **Field Name Consistency:** Multiple field names exist for the same concept:
   - `subtotal` vs `sub_total`
   - `grand_total` vs `total`
   - `balance_due` vs `balance`
   
   **Recommendation:** Standardize to one set of field names across all collections.

2. **Missing Validation:** Invoice creation doesn't validate that `grand_total = subtotal + tax - discount + shipping + adjustment`.

   **Recommendation:** Add server-side validation before save.

3. **No Audit Trail for Calculations:** When totals are modified, there's no record of the calculation.

   **Recommendation:** Log calculation inputs and outputs for debugging.

---

## 4. NEXT AUDIT PHASE

### Phase 2: Workflow/State Machine Audit

1. **Ticket Status Transitions:** Verify all valid state transitions are enforced
2. **Estimate Locking:** Verify locked estimates cannot be modified
3. **Invoice Status Updates:** Verify payment triggers correct status changes
4. **Payment Reversal:** Verify unapply payment correctly restores balances

### Phase 3: Cross-Module Reconciliation

1. **Invoice ↔ Payment:** Sum of payment allocations = invoice.amount_paid
2. **Estimate → Invoice:** Line items correctly transfer
3. **Inventory Tracking:** Reserved + Available = Total stock

---

## 5. RECOMMENDED ACTIONS

### P0 (Critical - Fix Before Deploy)
1. ~~Fix Zoho sync field mapping for `grand_total` and `balance_due`~~

### P1 (High - Fix Soon)
1. Add invoice calculation validation on save
2. Standardize field names across collections
3. Create data repair script for existing inconsistent invoices

### P2 (Medium - Backlog)
1. Add calculation audit logging
2. Create admin recalculation endpoint
3. Add unit tests for edge cases

---

*Audit conducted: February 2026*  
*Next scheduled audit: Phase 2 - Workflow/State Machine*
