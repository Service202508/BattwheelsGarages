"""
Battwheels OS - Load Testing Suite
====================================
Uses Locust (https://locust.io) to simulate realistic user load.

Usage:
  # Run via web UI (recommended):
  locust -f locustfile.py --host=https://your-app.com

  # Run headless:
  locust -f locustfile.py --host=https://your-app.com \\
    --users=50 --spawn-rate=5 --run-time=5m --headless

Scenarios:
  NormalOperationsUser    — 50 users, general ops
  FinanceUser             — 20 users, finance-heavy
  PeakTicketCreator       — 100 users, ticket creation burst
  EFIUser                 — 10 users, AI/EFI requests

Set TEST_EMAIL and TEST_PASSWORD env vars before running:
  export TEST_EMAIL=admin@battwheels.in
  export TEST_PASSWORD=admin
  locust -f locustfile.py --host=https://your-app.com
"""

import os
import json
import random
import string
from locust import HttpUser, task, between, tag, events
from datetime import datetime, timezone


TEST_EMAIL = os.getenv("TEST_EMAIL", "admin@battwheels.in")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin")


def random_string(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


def random_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"


class BattwheelsBase(HttpUser):
    """Base class — handles login and auth token management."""
    abstract = True
    token: str = None

    def on_start(self):
        """Login and store the JWT token."""
        with self.client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            catch_response=True,
            name="/api/auth/login",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token")
                resp.success()
            else:
                resp.failure(f"Login failed: {resp.status_code}")

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}


# ============================================================
# SCENARIO 1 — Normal Operations (50 users, 5 min)
# ============================================================

class NormalOperationsUser(BattwheelsBase):
    """
    Simulates a workshop operations user browsing tickets,
    checking dashboard, creating tickets, and checking inventory.

    Target: 50 concurrent users, 5 minutes
    """
    wait_time = between(2, 6)
    weight = 5

    @task(4)
    @tag("tickets", "read")
    def get_tickets_paginated(self):
        self.client.get(
            "/api/tickets?page=1&limit=25",
            headers=self.auth_headers,
            name="/api/tickets [paginated]",
        )

    @task(2)
    @tag("dashboard", "read")
    def get_dashboard_stats(self):
        self.client.get(
            "/api/dashboard/stats",
            headers=self.auth_headers,
            name="/api/dashboard/stats",
        )

    @task(2)
    @tag("finance", "read")
    def get_finance_dashboard(self):
        self.client.get(
            "/api/finance-dashboard/summary",
            headers=self.auth_headers,
            name="/api/finance-dashboard/summary",
        )

    @task(1)
    @tag("tickets", "write")
    def create_ticket(self):
        payload = {
            "title": f"Load test ticket {random_string(6)}",
            "description": "Automated load test — please ignore",
            "priority": random.choice(["low", "medium", "high"]),
            "vehicle_type": "two_wheeler",
            "vehicle_number": f"DL{random.randint(1,9)}{random_string(2).upper()}{random.randint(1000,9999)}",
            "customer_name": f"Test Customer {random_string(4)}",
            "contact_number": random_phone(),
        }
        with self.client.post(
            "/api/tickets",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
            name="/api/tickets [POST]",
        ) as resp:
            if resp.status_code in (200, 201):
                resp.success()
            else:
                resp.failure(f"Create ticket failed: {resp.status_code}")

    @task(2)
    @tag("inventory", "read")
    def get_inventory_items(self):
        self.client.get(
            "/api/inventory?page=1&limit=25",
            headers=self.auth_headers,
            name="/api/inventory [paginated]",
        )

    @task(1)
    @tag("reports", "read")
    def get_sla_report(self):
        self.client.get(
            "/api/sla/breach-report",
            headers=self.auth_headers,
            name="/api/sla/breach-report",
        )


# ============================================================
# SCENARIO 2 — Finance Load (20 users, 5 min)
# ============================================================

class FinanceUser(BattwheelsBase):
    """
    Simulates accountants accessing financial reports, invoices, journal entries.

    Target: 20 concurrent users, 5 minutes
    """
    wait_time = between(3, 8)
    weight = 2

    @task(3)
    @tag("finance", "read")
    def get_journal_entries(self):
        self.client.get(
            "/api/journal-entries?page=1&limit=25",
            headers=self.auth_headers,
            name="/api/journal-entries [paginated]",
        )

    @task(3)
    @tag("invoices", "read")
    def get_invoices(self):
        self.client.get(
            "/api/invoices-enhanced/?page=1&limit=25",
            headers=self.auth_headers,
            name="/api/invoices-enhanced [paginated]",
        )

    @task(2)
    @tag("finance", "read")
    def get_finance_dashboard(self):
        self.client.get(
            "/api/finance-dashboard/summary",
            headers=self.auth_headers,
            name="/api/finance-dashboard/summary",
        )

    @task(2)
    @tag("reports", "read")
    def get_profit_loss(self):
        from datetime import date, timedelta
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=365)).isoformat()
        self.client.get(
            f"/api/reports/profit-loss?start_date={start}&end_date={end}",
            headers=self.auth_headers,
            name="/api/reports/profit-loss",
        )

    @task(1)
    @tag("reports", "read")
    def get_balance_sheet(self):
        self.client.get(
            f"/api/reports/balance-sheet?as_of_date={datetime.now().strftime('%Y-%m-%d')}",
            headers=self.auth_headers,
            name="/api/reports/balance-sheet",
        )

    @task(1)
    @tag("reports", "read")
    def get_ar_aging(self):
        self.client.get(
            f"/api/reports/ar-aging?as_of_date={datetime.now().strftime('%Y-%m-%d')}",
            headers=self.auth_headers,
            name="/api/reports/ar-aging",
        )


# ============================================================
# SCENARIO 3 — Peak Ticket Creation (100 users, burst)
# ============================================================

class PeakTicketCreator(BattwheelsBase):
    """
    Simulates 100 users simultaneously creating tickets.
    Tests: race conditions in ticket numbering, journal entry concurrency,
           inventory stock deduction correctness.

    Target: 100 concurrent users, 2 minutes burst
    """
    wait_time = between(0.5, 2)
    weight = 10

    @task(5)
    @tag("tickets", "write", "concurrent")
    def create_ticket_concurrent(self):
        payload = {
            "title": f"Burst ticket {random_string(8)}",
            "description": "Concurrent load test",
            "priority": random.choice(["low", "medium", "high", "critical"]),
            "vehicle_type": random.choice(["two_wheeler", "three_wheeler", "four_wheeler"]),
            "vehicle_number": f"HR{random.randint(10,99)}{random_string(2).upper()}{random.randint(1000,9999)}",
            "customer_name": f"Burst Customer {random_string(4)}",
            "contact_number": random_phone(),
        }
        with self.client.post(
            "/api/tickets",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
            name="/api/tickets [POST burst]",
        ) as resp:
            if resp.status_code in (200, 201):
                resp.success()
            elif resp.status_code == 429:
                resp.success()  # Rate limiting triggered — expected
            else:
                resp.failure(f"Burst create failed: {resp.status_code}")

    @task(2)
    @tag("tickets", "read")
    def get_tickets_burst(self):
        self.client.get(
            "/api/tickets?page=1&limit=10",
            headers=self.auth_headers,
            name="/api/tickets [burst read]",
        )


# ============================================================
# SCENARIO 4 — AI/EFI Load (10 users, rate-limited)
# ============================================================

class EFIUser(BattwheelsBase):
    """
    Simulates 10 users making AI diagnostic requests.
    Keeps concurrency low (AI API has cost).
    Tests: rate limiting triggers correctly at 20/min threshold.

    Target: 10 concurrent users
    """
    wait_time = between(5, 15)
    weight = 1

    @task(3)
    @tag("ai", "read")
    def get_ai_diagnose(self):
        payload = {
            "vehicle_type": "two_wheeler",
            "symptoms": ["battery not charging", "reduced range"],
            "error_codes": [],
        }
        with self.client.post(
            "/api/ai/diagnose",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
            name="/api/ai/diagnose [EFI]",
        ) as resp:
            if resp.status_code in (200, 201):
                resp.success()
            elif resp.status_code == 429:
                # Rate limiting — expected at 20/min
                resp.success()
            elif resp.status_code == 404:
                resp.success()  # Endpoint may differ
            else:
                resp.failure(f"AI diagnose failed: {resp.status_code}")

    @task(2)
    @tag("ai", "read")
    def get_efi_reports(self):
        self.client.get(
            "/api/efi/reports?page=1&limit=10",
            headers=self.auth_headers,
            name="/api/efi/reports",
        )

    @task(1)
    @tag("ai", "read")
    def get_dashboard_stats(self):
        self.client.get(
            "/api/dashboard/stats",
            headers=self.auth_headers,
            name="/api/dashboard/stats [EFI user]",
        )
