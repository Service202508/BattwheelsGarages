# Period Locking Design Document

**C-03 | Day 5 of Week 1 Remediation**
**Status:** Design Only — No Code Implementation
**Author:** Automated Agent | Date: 2026-02-25

---

## 1. What Constitutes a Locked Period?

### Definition
A **locked period** is a calendar month (e.g., `2026-01`) aligned to the Indian GST filing calendar. This is the natural unit because:
- GSTR-1 and GSTR-3B are filed monthly
- The Battwheels OS GSTR reports already operate on `YYYY-MM` granularity
- Payroll runs are monthly
- Trial balance and P&L are generated per-month

### Who Defines It?
The **organization owner** (role: `admin` or `owner`) defines which periods are locked for their own org. Each organization manages its own lock schedule independently — multi-tenant isolation applies.

The **platform** does not auto-lock periods. Auto-locking would require knowledge of each org's filing deadlines, which vary by GST return type and taxpayer category. Instead, the platform provides the tooling; the org decides when to lock.

### Granularity
- **Lock unit:** Calendar month (`YYYY-MM`)
- **One lock record per org per month** — no partial-month locks
- **Fiscal year alignment:** The org's `fiscal_year_start` setting (e.g., `04-01` for April) is informational only. Locks are still per calendar month. A "lock entire FY" action would create 12 individual month-lock records.

---

## 2. Who Can Lock and Unlock?

### Lock
| Actor | Can Lock? | Constraint |
|-------|-----------|------------|
| Org Owner / Admin | Yes | Must have role `admin` or `owner` in `organization_users` |
| Org Accountant | Yes | Role `accountant` — they are the primary users of this feature |
| Org Staff / Technician | No | Insufficient privilege |
| Platform Super-Admin | No | Platform admins do not lock org periods — this is an org-level decision |

### Unlock
Unlocking is a **privileged, audited action** because it re-opens a period that may have already been filed with GST authorities.

| Actor | Can Unlock? | Constraint |
|-------|-------------|------------|
| Org Owner / Admin | Yes | Must provide a mandatory `reason` string (min 10 chars). Reason is stored in the lock record and in the audit log. |
| Org Accountant | No | Accountants can lock but cannot unilaterally unlock. This prevents accidental re-opening. |
| Platform Super-Admin | Yes (override) | Emergency only. Requires `reason` and `override_ticket_id` (reference to a support ticket). Logged separately as a platform-level audit event. |

### Unlock Cooldown
After unlocking, the period remains unlocked for a configurable window (default: **72 hours**). After the window expires, the period auto-relocks unless the user explicitly extends or re-locks manually. This prevents "forgot to re-lock" scenarios.

---

## 3. What Does Locking Block?

A locked period blocks **all write operations** where the **effective financial date** falls within the locked month. The effective date depends on the entity type:

| Entity | Effective Date Field | Blocked Operations |
|--------|---------------------|--------------------|
| Invoice | `invoice_date` | Create, Update (if date changes), Void |
| Credit Note | `created_at` (CN date) | Create |
| Journal Entry | `entry_date` | Create, Reverse |
| Payment (invoice) | `payment_date` | Record, Delete |
| Payment (received) | `payment_date` | Record, Delete |
| Bill | `bill_date` | Create, Update, Void |
| Expense | `expense_date` | Create, Update, Delete |
| Payroll | Pay period month (`YYYY-MM` of the payslip) | Run payroll, Edit payslip |
| Bank Transaction | `transaction_date` | Create, Reconcile, Categorize |

### What Is NOT Blocked
- **Read operations** — all reports, lists, exports, PDFs remain accessible
- **Status changes that don't alter financial figures** — e.g., marking an invoice as "viewed" or "sent" (these update metadata, not amounts or dates)
- **Creating entities with dates in unlocked periods** — only the specific locked month is blocked
- **Editing non-date, non-financial fields** — e.g., changing `customer_notes` on an invoice in a locked period is allowed (it doesn't affect the financial record)

### Error Response
When a period-lock check fails, the endpoint returns:

```json
{
  "detail": "Period 2026-01 is locked for this organization. Unlock the period or use a date in an open period.",
  "code": "PERIOD_LOCKED",
  "locked_period": "2026-01",
  "locked_by": "user_abc123",
  "locked_at": "2026-02-01T10:00:00+00:00"
}
```

HTTP status: **409 Conflict** (not 403, because the user has permission — the resource state is the issue).

---

## 4. Handling Legitimate Corrections (Unlock Workflow)

### Problem
GST amendments (e.g., GSTR-1 amendments, debit/credit notes for prior periods) sometimes require posting to a period that has already been filed and locked. A blanket unlock creates a free-for-all where any user could modify the locked period.

### Solution: Scoped Unlock with Time Window

1. **Admin/Owner unlocks the period** with a mandatory reason (e.g., "GSTR-1 amendment for invoice INV-001").
2. The period enters an **UNLOCKED_AMENDMENT** state with a 72-hour window (configurable per org).
3. During this window, writes to the period are allowed but **every mutation is flagged** in the audit log with `"amendment_window": true`.
4. After the window expires, the period auto-relocks.
5. If the user needs more time, they can extend the window (max 2 extensions, total max 7 days).

### Alternative: Amendment-Only Mode (Future Enhancement)
A more restrictive option (not in v1): the period can be set to `AMENDMENT_ONLY`, which allows only credit notes and journal adjustments but blocks new invoices and payments. This provides a middle ground but adds complexity. Recommended for v2.

### Audit Trail
Every unlock/relock event is written to the `audit_log` collection:
```
action: UNLOCK_PERIOD / LOCK_PERIOD / EXTEND_UNLOCK
entity_type: period_lock
entity_id: "2026-01"
before_snapshot: { status: "locked", ... }
after_snapshot: { status: "unlocked_amendment", reason: "...", expires_at: "..." }
```

---

## 5. Endpoints Requiring Period-Lock Check

Every route that accepts a date field which could fall in a locked period must include a lock check **before** the write operation. Listed by route file:

### `routes/invoices_enhanced.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/invoices-enhanced/` | `invoice_date` |
| PUT | `/invoices-enhanced/{id}` | `invoice_date` (if changed) |
| POST | `/invoices-enhanced/{id}/void` | original `invoice_date` |
| POST | `/invoices-enhanced/{id}/payments` | `payment_date` |
| DELETE | `/invoices-enhanced/{id}/payments/{pid}` | original `payment_date` |
| POST | `/invoices-enhanced/{id}/send` | `invoice_date` (status change to "sent" on the invoice date) |
| POST | `/invoices-enhanced/from-salesorder/{id}` | generated `invoice_date` |
| POST | `/invoices-enhanced/from-estimate/{id}` | generated `invoice_date` |

### `routes/credit_notes.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/credit-notes/` | `created_at` (the CN's own date, not the referenced invoice date) |

### `routes/journal_entries.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/journal-entries/` | `entry_date` |
| POST | `/journal-entries/{id}/reverse` | `reversal_date` |

### `routes/payments_received.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/payments-received/` | `payment_date` |
| DELETE | `/payments-received/{id}` | original `payment_date` |

### `routes/bills_enhanced.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/bills-enhanced/` | `bill_date` |
| PUT | `/bills-enhanced/{id}` | `bill_date` (if changed) |
| POST | `/bills-enhanced/{id}/payments` | `payment_date` |

### `routes/bills.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/bills/` | `bill_date` |
| PUT | `/bills/{id}` | `bill_date` |

### `routes/expenses.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/expenses/` | `expense_date` |
| PUT | `/expenses/{id}` | `expense_date` (if changed) |
| DELETE | `/expenses/{id}` | original `expense_date` |

### `routes/banking_module.py`
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/banking/transactions` | `transaction_date` |
| PUT | `/banking/transactions/{id}/categorize` | `transaction_date` |
| POST | `/banking/transactions/{id}/reconcile` | `transaction_date` |

### `routes/hr.py` (Payroll)
| Method | Path | Date Field Checked |
|--------|------|--------------------|
| POST | `/hr/payroll/run` | payroll month (derived from request) |

### `services/double_entry_service.py` (Internal)
The `create_journal_entry()` and `reverse_journal_entry()` methods accept `entry_date` / `reversal_date`. The lock check should be performed at the **route level** (caller), not inside the service, to keep the service layer clean and avoid circular dependencies.

### `services/posting_hooks.py` (Internal)
All 6 posting functions (`post_invoice_journal_entry`, `post_payment_journal_entry`, `post_bill_journal_entry`, `post_bill_payment_journal_entry`, `post_expense_journal_entry`, `post_payroll_journal_entry`) derive their `entry_date` from the parent document. Since the parent document's creation endpoint already checks the lock, these do not need a separate check — the lock is enforced at the entry point.

> **PREREQUISITE NOTE:** Service-layer enforcement must be added before any background job or scheduled task is introduced that calls financial mutation functions directly. This is a hard prerequisite for the Celery backlog item. Route-level enforcement alone is insufficient when mutations can be triggered outside the HTTP request cycle (e.g., cron-based recurring invoice generation, scheduled payroll runs, async bank reconciliation). Before any such task is implemented, `check_period_lock()` must be called inside the service-layer functions or within the task itself.

---

## 6. Data Model

### Collection: `period_locks`

```javascript
{
  // Identity
  "lock_id": "lock_abc123",             // Unique ID
  "organization_id": "org_xyz",         // Tenant scope — INDEXED
  "period": "2026-01",                  // Calendar month — INDEXED (compound with org_id)

  // State
  "status": "locked",                   // "locked" | "unlocked" | "unlocked_amendment"

  // Lock metadata
  "locked_by": "user_abc",              // User ID who locked
  "locked_at": "2026-02-01T10:00:00Z",  // Timestamp of lock action
  "lock_reason": "Month-end close",     // Optional reason for locking

  // Unlock metadata (populated only when status != "locked")
  "unlocked_by": "user_xyz",            // User ID who unlocked
  "unlocked_at": "2026-02-15T09:00:00Z",
  "unlock_reason": "GSTR-1 amendment for INV-001",  // Mandatory
  "unlock_expires_at": "2026-02-18T09:00:00Z",      // Auto-relock timestamp
  "unlock_extension_count": 0,          // Max 2

  // Platform override (null unless platform admin intervened)
  "platform_override": null,
  // OR:
  // "platform_override": {
  //   "admin_id": "platform_admin_001",
  //   "ticket_id": "SUP-12345",
  //   "overridden_at": "2026-02-15T09:00:00Z"
  // },

  // Timestamps
  "created_at": "2026-02-01T10:00:00Z",
  "updated_at": "2026-02-15T09:00:00Z"
}
```

### Indexes

```javascript
// Unique compound: one lock record per org per period
{ "organization_id": 1, "period": 1 }  // UNIQUE

// Query by status for auto-relock cron
{ "status": 1, "unlock_expires_at": 1 }
```

### Helper Function Signature (Design Only)

```python
async def check_period_lock(org_id: str, date_str: str) -> None:
    """
    Raises HTTP 409 if the month containing `date_str` is locked for `org_id`.
    Called at the top of every write endpoint listed in Section 5.

    Parameters:
        org_id:   Organization ID from tenant context
        date_str: The effective financial date (YYYY-MM-DD or YYYY-MM-DDT...)

    Raises:
        HTTPException(409) with code PERIOD_LOCKED if the period is locked.
    """
    period = date_str[:7]  # "2026-01-15" → "2026-01"
    lock = await db.period_locks.find_one({
        "organization_id": org_id,
        "period": period,
        "status": "locked"
    }, {"_id": 0})
    if lock:
        raise HTTPException(
            status_code=409,
            detail=f"Period {period} is locked.",
            # ... include lock metadata
        )
```

---

## 7. Edge Cases

### 7.1 Credit Notes Referencing Invoices in Locked Periods
**Scenario:** Invoice INV-001 has `invoice_date: 2026-01-15`. Period 2026-01 is locked. User wants to issue a credit note in 2026-02 referencing INV-001.

**Decision:** The credit note's `created_at` is 2026-02, which is the **CN's own period**. The lock check applies to the CN date (2026-02), not the referenced invoice date (2026-01). If 2026-02 is unlocked, the CN is allowed.

**Rationale:** This aligns with GST rules — a credit note is reported in the period it is issued (GSTR-1 Section CDNR uses CN date), not the period of the original invoice. This is also consistent with the GSTR-3B cross-period handling implemented in Day 3 (C-06).

### 7.2 Payroll Postings
**Scenario:** Payroll for January 2026 is typically run in early February. If January is locked before payroll runs, the posting is blocked.

**Decision:** Payroll posting checks the **pay period month** (the month the salaries are for), not the date the payroll is processed. If January is locked, the January payroll cannot be run regardless of when the user clicks "Run Payroll."

**Mitigation:** Org admins should run payroll before locking the period. The UI should display a warning: "Period 2026-01 has not had payroll processed. Are you sure you want to lock?"

### 7.3 Year-End Closing Entries
**Scenario:** At fiscal year-end (March 31 for Indian FY), accountants post closing entries to transfer P&L balances to Retained Earnings. These entries have `entry_date` in March — which may already be locked.

**Decision:** Year-end closing follows the standard unlock workflow (Section 4). The admin unlocks March with reason "Year-end closing entries," posts the closing journals, then re-locks. No special exemption for closing entries.

**Future Enhancement:** A dedicated "Year-End Close" workflow that atomically posts all closing entries and re-locks the period in a single transaction. This eliminates the risk of the period being left unlocked.

### 7.4 Recurring Invoices
**Scenario:** A recurring invoice profile generates an invoice on the 1st of each month. If the current month is locked, the auto-generated invoice would fail.

**Decision:** Recurring invoice generation checks the period lock. If locked, the generation is skipped and a notification is sent to the org admin: "Recurring invoice for profile {name} could not be generated — period {month} is locked."

### 7.5 Bank Statement Import
**Scenario:** User imports a bank statement containing transactions from a locked period.

**Decision:** Transactions with dates in locked periods are **imported but flagged** as `"period_locked": true` and left in `unreconciled` status. They cannot be categorized or reconciled until the period is unlocked. This allows the bank feed to be complete without violating the lock.

### 7.6 Backdated Invoices
**Scenario:** User creates an invoice today (2026-02-25) but sets `invoice_date` to 2026-01-10 (a locked period).

**Decision:** Blocked. The lock check uses `invoice_date`, not `created_time`. The user must either unlock January or change the invoice date to February.

### 7.7 Void in Locked Period
**Scenario:** User wants to void an invoice whose `invoice_date` is in a locked period.

**Decision:** Blocked. Voiding changes the financial state of the entity (balance_due becomes 0, revenue is reversed). The period must be unlocked first.

### 7.8 Payment Deletion in Locked Period
**Scenario:** A payment was recorded with `payment_date: 2026-01-20`. January is now locked. User wants to delete the payment.

**Decision:** Blocked. Deleting a payment reverses the financial impact. The period must be unlocked first.

---

## Appendix: Implementation Sequence (When Approved)

This section is informational — no code to be written until approved.

1. **Create `utils/period_lock.py`** — `check_period_lock()` helper
2. **Create `routes/period_locks.py`** — CRUD endpoints for lock/unlock
3. **Add `check_period_lock()` call** to each of the 25+ endpoints listed in Section 5
4. **Add auto-relock cron** — background task that re-locks expired amendment windows
5. **Frontend:** Lock/unlock UI in Settings > Accounting > Period Management
6. **Tests:** Lock enforcement on each entity type, unlock workflow, cross-period CN allowed, auto-relock

Estimated effort: 2-3 days implementation + 1 day testing.

---

*End of design document. No code has been written. Awaiting confirmation before Day 5 is marked complete.*
