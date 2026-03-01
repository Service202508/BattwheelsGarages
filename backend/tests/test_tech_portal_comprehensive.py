"""
Comprehensive Technician Portal Endpoint Tests
================================================
Tests for all /api/v1/technician/* endpoints.
Uses JWT auth with technician role (tech.a@battwheels.internal).

Run: pytest backend/tests/test_tech_portal_comprehensive.py -v --tb=short
"""

import pytest
import requests


PREFIX = "/api/v1/technician"
TECH_ORG = "dev-internal-testing-001"


@pytest.fixture(scope="module")
def _tech_headers(base_url):
    """Login as technician and return headers."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "tech.a@battwheels.internal",
        "password": "TechA@123",
    })
    assert resp.status_code == 200, f"Technician login failed: {resp.text}"
    token = resp.json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": TECH_ORG,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def _non_tech_headers(base_url, dev_token):
    """Non-technician headers (owner role) to verify RBAC."""
    return {
        "Authorization": f"Bearer {dev_token}",
        "X-Organization-ID": TECH_ORG,
        "Content-Type": "application/json",
    }


# ==================== DASHBOARD ====================

class TestTechDashboard:

    def test_get_dashboard(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/dashboard", headers=_tech_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_dashboard_requires_technician(self, base_url, _non_tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/dashboard", headers=_non_tech_headers)
        assert resp.status_code == 403

    def test_dashboard_no_auth(self, base_url):
        resp = requests.get(f"{base_url}{PREFIX}/dashboard")
        assert resp.status_code == 401


# ==================== TICKETS ====================

class TestTechTickets:

    def test_list_tickets(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/tickets", headers=_tech_headers)
        assert resp.status_code == 200

    def test_list_tickets_filter_status(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/tickets?status=open", headers=_tech_headers)
        assert resp.status_code == 200

    def test_get_ticket_nonexistent(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/tickets/NONEXISTENT-TKT", headers=_tech_headers)
        assert resp.status_code == 404


# ==================== ATTENDANCE ====================

class TestTechAttendance:

    def test_get_attendance(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/attendance", headers=_tech_headers)
        assert resp.status_code == 200

    def test_check_in(self, base_url, _tech_headers):
        resp = requests.post(f"{base_url}{PREFIX}/attendance/check-in", headers=_tech_headers)
        # May succeed or return 400 if already checked in
        assert resp.status_code in [200, 400]

    def test_check_out(self, base_url, _tech_headers):
        resp = requests.post(f"{base_url}{PREFIX}/attendance/check-out", headers=_tech_headers)
        # May succeed or return 400 if not checked in
        assert resp.status_code in [200, 400]


# ==================== LEAVE ====================

class TestTechLeave:

    def test_list_leave_requests(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/leave", headers=_tech_headers)
        assert resp.status_code == 200

    def test_request_leave(self, base_url, _tech_headers):
        resp = requests.post(f"{base_url}{PREFIX}/leave", headers=_tech_headers, json={
            "start_date": "2026-04-01",
            "end_date": "2026-04-02",
            "reason": "Test leave request",
            "leave_type": "casual",
        })
        assert resp.status_code in [200, 201]


# ==================== PAYROLL ====================

class TestTechPayroll:

    def test_get_payroll(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/payroll", headers=_tech_headers)
        assert resp.status_code == 200


# ==================== PRODUCTIVITY ====================

class TestTechProductivity:

    def test_get_productivity(self, base_url, _tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/productivity", headers=_tech_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


# ==================== AI ASSIST ====================

class TestTechAIAssist:

    def test_ai_assist(self, base_url, _tech_headers):
        resp = requests.post(f"{base_url}{PREFIX}/ai-assist", headers=_tech_headers, json={
            "query": "How do I diagnose a battery drain issue?",
            "category": "diagnosis",
            "context": {"vehicle_type": "2W"},
        })
        # May return 200 or 500/503 (if LLM not configured)
        assert resp.status_code in [200, 500, 503]


# ==================== RBAC: Non-technician blocked ====================

class TestTechRBAC:

    def test_tickets_blocked_for_non_tech(self, base_url, _non_tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/tickets", headers=_non_tech_headers)
        assert resp.status_code == 403

    def test_attendance_blocked_for_non_tech(self, base_url, _non_tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/attendance", headers=_non_tech_headers)
        assert resp.status_code == 403

    def test_leave_blocked_for_non_tech(self, base_url, _non_tech_headers):
        resp = requests.get(f"{base_url}{PREFIX}/leave", headers=_non_tech_headers)
        assert resp.status_code == 403
