# BATTWHEELS OS — CODING STANDARDS
## Multi-Tenancy & Data Integrity Engineering Rules

```
Version: 1.0
Effective: February 2026
Origin: Post-audit remediation (26 vs 0 ticket mismatch incident)
Applies to: All backend route files that query MongoDB
```

---

## CONTEXT

In February 2026, a systematic audit of 7 application modules uncovered three repeating
patterns that silently infected 5 of 7 modules. The most serious — missing `organization_id`
filters — was not a display bug. Invoice summaries, journal entries, and EFI failure history
were returning data across all tenants. In a multi-tenant SaaS, that is a data isolation breach.

These standards exist so this class of bug cannot ship again.

---

## THE 3 PREVENTION RULES

---

### RULE 1 — Every MongoDB Query MUST be Scoped by `organization_id`

**Pattern A: Missing tenant filter (the most critical violation)**

This is a data isolation breach. Any endpoint returning unscoped data exposes aggregate
financial, operational, or customer data from every organization on the platform to every
other organization.

#### ❌ WRONG

```python
# Returns data from ALL organizations — data isolation breach
@router.get("/invoices/summary")
async def get_invoice_summary(request: Request):
    pipeline = [
        {"$group": {"_id": "$status", "total": {"$sum": "$amount"}}}
    ]
    result = await db.invoices.aggregate(pipeline).to_list(100)
    return result
```

#### ✅ CORRECT

```python
# Scoped to the requesting organization only
@router.get("/invoices/summary")
async def get_invoice_summary(request: Request):
    org_id = TenantContext.get_org_id(request)  # Extracted from authenticated JWT
    pipeline = [
        {"$match": {"organization_id": org_id}},  # MUST be the first stage
        {"$group": {"_id": "$status", "total": {"$sum": "$amount"}}}
    ]
    result = await db.invoices.aggregate(pipeline).to_list(100)
    return result
```

**Checklist for every new route:**
- [ ] `org_id = TenantContext.get_org_id(request)` is present
- [ ] `{"organization_id": org_id}` is in every `find()`, `find_one()`, `count_documents()`, and as the first `$match` in every aggregation pipeline
- [ ] No `find({})` calls exist on any user-data collection

---

### RULE 2 — Counts MUST Be Computed at the Database Layer

**Pattern B: Client-side counting (a scaling time-bomb)**

Client-side counting silently breaks the moment any organization accumulates more records
than the page size. If pagination returns 25 records and there are 30, a client-side count
returns 25 instead of 30. This is what caused the 26 vs 0 ticket count mismatch.

#### ❌ WRONG

```python
# Fetches one page of records, then counts in Python
# Returns 25 when real count is 300 — fails silently, no error, no log
@router.get("/tickets/stats")
async def get_ticket_stats(request: Request):
    org_id = TenantContext.get_org_id(request)
    all_tickets = await db.tickets.find(
        {"organization_id": org_id}
    ).to_list(1000)  # Arbitrary ceiling

    open_count  = len([t for t in all_tickets if t["status"] == "open"])
    closed_count = len([t for t in all_tickets if t["status"] == "closed"])
    return {"open": open_count, "closed": closed_count}
```

#### ✅ CORRECT

```python
# Count at the database layer — always accurate regardless of record volume
@router.get("/tickets/stats")
async def get_ticket_stats(request: Request):
    org_id = TenantContext.get_org_id(request)

    open_count   = await db.tickets.count_documents({"organization_id": org_id, "status": "open"})
    closed_count = await db.tickets.count_documents({"organization_id": org_id, "status": "closed"})
    pending_count = await db.tickets.count_documents({"organization_id": org_id, "status": "pending"})

    return {"open": open_count, "closed": closed_count, "pending": pending_count}
```

**Or using a single aggregation for efficiency:**

```python
# Preferred: single round-trip using aggregation
pipeline = [
    {"$match": {"organization_id": org_id}},
    {"$group": {"_id": "$status", "count": {"$sum": 1}}}
]
result = await db.tickets.aggregate(pipeline).to_list(None)
counts = {row["_id"]: row["count"] for row in result}
```

**Checklist for every stats/summary endpoint:**
- [ ] No `len([x for x in list if ...])` pattern exists for calculating displayed counts
- [ ] `count_documents()` or an aggregation `$group` is used instead
- [ ] The count query is independently scoped with `organization_id` — not derived from a previously fetched list

---

### RULE 3 — Never Hardcode an `organization_id` Value

**Pattern C: Hardcoded org ID (a ghost tenant lock)**

A hardcoded org ID does one of two things: (a) every call is silently locked to one specific
organization — meaning all other organizations see empty data, or (b) it targets a
non-existent "default" org — meaning the endpoint returns nothing for every real user.
This pattern was found in three separate API calls in the Journal Entries module.

#### ❌ WRONG

```python
# Locked to a ghost org — every real user sees empty data
@router.get("/journal-entries")
async def list_journal_entries(request: Request):
    entries = await db.journal_entries.find(
        {"organization_id": "default"}  # WRONG: hardcoded ghost org
    ).to_list(100)
    return entries


# Also wrong — using a module-level constant with a literal value
DEFAULT_ORG = "org_abc123"

@router.get("/failure-cards")
async def get_failure_cards(request: Request):
    cards = await db.failure_cards.find(
        {"organization_id": DEFAULT_ORG}  # WRONG: only one org sees data
    ).to_list(100)
    return cards
```

#### ✅ CORRECT

```python
# org_id is always derived from the authenticated request context
@router.get("/journal-entries")
async def list_journal_entries(request: Request):
    org_id = TenantContext.get_org_id(request)  # Always from JWT/session
    entries = await db.journal_entries.find(
        {"organization_id": org_id}
    ).to_list(100)
    return entries
```

**Checklist for every new route:**
- [ ] No string literal is used as an `organization_id` value in any query
- [ ] No module-level or file-level `ORG_ID = "..."` constant exists
- [ ] `TenantContext.get_org_id(request)` is the only source of `org_id` in queries

---

## QUICK REFERENCE CARD

```
New route? Run this mental checklist before opening a PR:

  1. FILTER     db.collection.find({"organization_id": org_id, ...})
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                            Present on EVERY query? YES / NO

  2. COUNT      Used count_documents() or $group aggregation?
                NOT len([x for x in list])? YES / NO

  3. SOURCE     org_id comes from TenantContext.get_org_id(request)?
                NOT a hardcoded string or module constant? YES / NO

All three YES → safe to ship.
Any NO → fix before PR.
```

---

## CLEAN MODULE REFERENCE

The following modules were audited in February 2026 and passed all three rules.
Use them as reference implementations for new modules:

- `backend/routes/inventory.py` + `services/inventory_service.py`
- `backend/routes/hr.py` + `services/hr_service.py`
- `backend/routes/contacts_enhanced.py`
- `backend/routes/insights.py`

---

## ENFORCEMENT

These rules are enforced by:
1. **This document** — reviewed in all PR descriptions for new route files
2. **Tenant isolation comments** — single-line guard comment at the top of every route file
3. **Pre-deployment checklist** — `PRE_DEPLOYMENT_AUDIT.md` Prevention Rules Checklist

Any PR adding a new route file to `/backend/routes/` MUST include the tenant isolation
comment and MUST be reviewed against this checklist before merge.


---

## RULE 4 — Three-Environment Discipline

Battwheels OS operates three environments. Every developer and every AI agent must know which environment they are in before making any change.

### Environments

| Environment | Database | Org | Purpose |
|-------------|----------|-----|---------|
| **production** | test_database | Battwheels Garages (real data) | Live customer use only |
| **staging** | battwheels_staging | Battwheels Garages Staging | Pre-deploy testing |
| **development** | battwheels_dev | Volt Motors Demo + Battwheels Dev | Feature development |

### The One Rule
**NEVER seed, modify, or delete data in the production database during development or testing.**
- Production = `test_database` (DB_NAME from .env)
- Staging = `battwheels_staging` database
- Dev = `battwheels_dev` database

### Promotion Path
```
Code change written -> tested in dev -> tested in staging -> deployed to production
```

### Demo Credentials (for sales demos — never show production)
- Login: demo@voltmotors.in
- Password: Demo@12345
- Reseed anytime: `make seed-demo`

### Dev Credentials (for internal testing only)
- Login: dev@battwheels.internal
- Password: DevTest@123
- Reseed anytime: `make reseed-dev`

