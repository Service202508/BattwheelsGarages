# Battwheels OS — Load Testing Guide

## Overview

This directory contains load tests for Battwheels OS using [Locust](https://locust.io).

**Do NOT run these tests against production.** Run against a staging environment or a dedicated load-test instance.

---

## Prerequisites

```bash
pip install locust
```

Set credentials:
```bash
export TEST_EMAIL=admin@battwheels.in
export TEST_PASSWORD=admin
export TARGET_HOST=https://your-staging-url.com
```

---

## Running Tests

### Web UI (recommended for first-time runs)
```bash
cd /app/load_tests
locust -f locustfile.py --host=$TARGET_HOST
# Open http://localhost:8089 to configure and start
```

### Headless (CI/CD)
```bash
locust -f locustfile.py \
  --host=$TARGET_HOST \
  --users=50 --spawn-rate=5 \
  --run-time=5m \
  --headless \
  --csv=results/normal_ops
```

---

## Scenarios

### Scenario 1 — Normal Operations
**Class:** `NormalOperationsUser`  
**Users:** 50 concurrent  
**Duration:** 5 minutes  

Simulates typical workshop day: browsing tickets, checking dashboard, creating tickets, viewing inventory.

```bash
locust -f locustfile.py --host=$TARGET_HOST \
  --users=50 --spawn-rate=5 --run-time=5m \
  --headless -u NormalOperationsUser
```

### Scenario 2 — Finance Load
**Class:** `FinanceUser`  
**Users:** 20 concurrent  
**Duration:** 5 minutes  

Simulates accountants running P&L, balance sheets, aging reports, and journal entries.

```bash
locust -f locustfile.py --host=$TARGET_HOST \
  --users=20 --spawn-rate=2 --run-time=5m \
  --headless -u FinanceUser
```

### Scenario 3 — Peak Ticket Creation Burst
**Class:** `PeakTicketCreator`  
**Users:** 100 concurrent  
**Duration:** 2 minutes  

All users create tickets simultaneously. Tests race conditions in ticket numbering, journal entry concurrency, and inventory stock deduction.

```bash
locust -f locustfile.py --host=$TARGET_HOST \
  --users=100 --spawn-rate=20 --run-time=2m \
  --headless -u PeakTicketCreator
```

### Scenario 4 — AI/EFI Load
**Class:** `EFIUser`  
**Users:** 10 concurrent  
**Duration:** 5 minutes  

Low-concurrency AI diagnostic requests. Verifies rate limiting triggers at ~20/min threshold.

```bash
locust -f locustfile.py --host=$TARGET_HOST \
  --users=10 --spawn-rate=1 --run-time=5m \
  --headless -u EFIUser
```

---

## Performance Thresholds

| Metric | Threshold | Action if Failed |
|--------|-----------|------------------|
| 95th percentile response time | < 500ms | Investigate slow endpoints, add DB indexes |
| 99th percentile response time | < 2000ms | Check query plans, cache frequent reads |
| Error rate | < 1% | Triage errors; 429s are expected under rate limiting |
| Database deadlocks | 0 | Check concurrent write patterns, add indexes |
| Memory (backend pod) | < 512MB sustained | Scale horizontally or optimize queries |
| Ticket creation throughput | > 10 tickets/sec | Confirm with MongoDB write concern |

---

## Interpreting Results

After a headless run with `--csv=results/scenario_name`, you get:
- `results/scenario_name_stats.csv` — aggregate RPS, response times, failure count
- `results/scenario_name_failures.csv` — individual failure details

**Key columns:**
- `Requests/s` — throughput
- `95%` — 95th percentile response time (ms)
- `Failure %` — % of failed requests (non-2xx or timeout)

**Green zone:** 95% < 500ms, Failure% < 1%  
**Yellow zone:** 95% 500-1500ms, Failure% 1-3%  
**Red zone:** 95% > 1500ms or Failure% > 3%

---

## What to Fix if Thresholds Fail

### Slow response (95% > 500ms)
1. `GET /api/journal-entries` — add compound index on `(organization_id, created_at)`
2. `GET /api/invoices-enhanced/` — add index on `(organization_id, invoice_number, status)`
3. Enable MongoDB query profiler: `db.setProfilingLevel(1, { slowms: 100 })`

### High error rate
1. Check `/var/log/supervisor/backend.err.log` for tracebacks
2. Look for `429 Too Many Requests` (expected from rate limiter)
3. Look for `500 Internal Server Error` (bugs) and `503 Service Unavailable` (overload)

### Database deadlocks
1. Enable MongoDB `mongostat` and watch `locked%`
2. Ensure all writes use `upsert: true` where possible
3. Check `APScheduler` SLA background job — may conflict with bulk writes

### Memory pressure
1. Check `motor` connection pool size (`maxPoolSize=50` default)
2. Use `ulimit` to profile worker memory
3. Consider horizontal scaling via `supervisord` multi-process

---

## Before Beta Launch — Checklist

```
□ Run Scenario 1 (Normal Operations) — all green
□ Run Scenario 2 (Finance Load) — all green  
□ Run Scenario 3 (Peak Burst, 2min) — error rate < 1%, no deadlocks
□ Run Scenario 4 (EFI, verify rate limiting) — 429s appear at ~20/min
□ Check MongoDB slow query log — no query > 100ms in normal ops
□ Verify Sentry captures errors during load test
□ Confirm APScheduler SLA job does not fail under load
□ Document baseline numbers for production monitoring
```

---

## Adding New Scenarios

Create a new class inheriting from `BattwheelsBase`:

```python
class MyScenario(BattwheelsBase):
    wait_time = between(2, 5)
    weight = 1  # Relative weighting when running mixed users

    @task(3)
    def my_endpoint(self):
        self.client.get("/api/my-endpoint", headers=self.auth_headers)
```
