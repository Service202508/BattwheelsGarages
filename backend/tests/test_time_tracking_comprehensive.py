"""
Comprehensive Time Tracking Endpoint Tests
============================================
Tests for all /api/v1/time-tracking/* endpoints.
Uses shared conftest.py fixtures (base_url, dev_headers).

Run: pytest backend/tests/test_time_tracking_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid


@pytest.fixture(scope="module")
def _headers(base_url, dev_token):
    """Auth headers with org context for time tracking."""
    return {
        "Authorization": f"Bearer {dev_token}",
        "X-Organization-ID": "dev-internal-testing-001",
        "Content-Type": "application/json",
    }


PREFIX = "/api/v1/time-tracking"
TEST_USER_ID = f"user-test-{uuid.uuid4().hex[:6]}"
TEST_USER_NAME = "Test Technician"


# ==================== 1. CREATE TIME ENTRY ====================

class TestCreateTimeEntry:

    @pytest.fixture(scope="class")
    def created_entry(self, base_url, _headers):
        resp = requests.post(f"{base_url}{PREFIX}/entries", headers=_headers, json={
            "user_id": TEST_USER_ID,
            "user_name": TEST_USER_NAME,
            "date": "2026-03-01",
            "hours": 3.5,
            "description": "Test time entry",
            "task_type": "service",
            "billable": True,
            "hourly_rate": 150.0,
        })
        assert resp.status_code in [200, 201], f"Entry creation failed: {resp.text}"
        return resp.json()

    def test_create_entry_returns_id(self, created_entry):
        entry = created_entry.get("entry", created_entry)
        assert "entry_id" in entry or "id" in entry

    def test_create_entry_requires_auth(self, base_url):
        resp = requests.post(f"{base_url}{PREFIX}/entries", json={
            "user_id": "x", "user_name": "x", "date": "2026-01-01", "hours": 1,
        })
        assert resp.status_code in [401, 403]


# ==================== 2. LIST TIME ENTRIES ====================

class TestListTimeEntries:

    def test_list_entries(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/entries", headers=_headers)
        assert resp.status_code == 200

    def test_list_entries_filter_user(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/entries?user_id={TEST_USER_ID}", headers=_headers)
        assert resp.status_code == 200

    def test_list_entries_filter_billable(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/entries?billable=true", headers=_headers)
        assert resp.status_code == 200


# ==================== 3. GET SINGLE ENTRY ====================

class TestGetTimeEntry:

    @pytest.fixture(scope="class")
    def _entry_id(self, base_url, _headers):
        resp = requests.post(f"{base_url}{PREFIX}/entries", headers=_headers, json={
            "user_id": TEST_USER_ID,
            "user_name": TEST_USER_NAME,
            "date": "2026-03-01",
            "hours": 1.0,
            "description": "Get test entry",
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        entry = data.get("entry", data)
        return entry.get("entry_id") or entry.get("id")

    def test_get_entry(self, base_url, _headers, _entry_id):
        resp = requests.get(f"{base_url}{PREFIX}/entries/{_entry_id}", headers=_headers)
        assert resp.status_code == 200

    def test_get_nonexistent_entry(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/entries/nonexistent-entry-xyz", headers=_headers)
        assert resp.status_code == 404


# ==================== 4. UPDATE TIME ENTRY ====================

class TestUpdateTimeEntry:

    @pytest.fixture(scope="class")
    def _entry_id(self, base_url, _headers):
        resp = requests.post(f"{base_url}{PREFIX}/entries", headers=_headers, json={
            "user_id": TEST_USER_ID,
            "user_name": TEST_USER_NAME,
            "date": "2026-03-01",
            "hours": 2.0,
            "description": "Update test entry",
        })
        assert resp.status_code in [200, 201]
        data = resp.json()
        entry = data.get("entry", data)
        return entry.get("entry_id") or entry.get("id")

    def test_update_entry(self, base_url, _headers, _entry_id):
        resp = requests.put(f"{base_url}{PREFIX}/entries/{_entry_id}", headers=_headers, json={
            "hours": 2.5,
            "notes": "Updated by test",
        })
        assert resp.status_code == 200


# ==================== 5. DELETE TIME ENTRY ====================

class TestDeleteTimeEntry:

    def test_delete_entry(self, base_url, _headers):
        # Create then delete
        resp = requests.post(f"{base_url}{PREFIX}/entries", headers=_headers, json={
            "user_id": TEST_USER_ID,
            "user_name": TEST_USER_NAME,
            "date": "2026-03-01",
            "hours": 0.5,
            "description": "Delete test",
        })
        assert resp.status_code in [200, 201]
        entry = resp.json().get("entry", resp.json())
        eid = entry.get("entry_id") or entry.get("id")
        resp2 = requests.delete(f"{base_url}{PREFIX}/entries/{eid}", headers=_headers)
        assert resp2.status_code == 200

    def test_delete_nonexistent_404(self, base_url, _headers):
        resp = requests.delete(f"{base_url}{PREFIX}/entries/nonexistent-xyz", headers=_headers)
        assert resp.status_code == 404


# ==================== 6. TIMER (START/STOP) ====================

class TestTimer:

    @pytest.fixture(scope="class")
    def started_timer(self, base_url, _headers):
        resp = requests.post(f"{base_url}{PREFIX}/timer/start", headers=_headers, json={
            "user_id": TEST_USER_ID,
            "user_name": TEST_USER_NAME,
            "description": "Timer test",
            "task_type": "service",
            "billable": True,
        })
        assert resp.status_code in [200, 201], f"Timer start failed: {resp.text}"
        return resp.json()

    def test_start_timer(self, started_timer):
        timer = started_timer.get("timer", started_timer)
        assert "timer_id" in timer or "id" in timer

    def test_active_timers(self, base_url, _headers, started_timer):
        resp = requests.get(f"{base_url}{PREFIX}/timer/active", headers=_headers)
        assert resp.status_code == 200

    def test_stop_timer(self, base_url, _headers, started_timer):
        timer = started_timer.get("timer", started_timer)
        tid = timer.get("timer_id") or timer.get("id")
        resp = requests.post(f"{base_url}{PREFIX}/timer/stop/{tid}", headers=_headers)
        assert resp.status_code == 200


# ==================== 7. UNBILLED HOURS ====================

class TestUnbilledHours:

    def test_get_unbilled_hours(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/unbilled", headers=_headers)
        assert resp.status_code == 200


# ==================== 8. REPORTS / SUMMARY ====================

class TestTimeSummary:

    def test_time_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/reports/summary", headers=_headers)
        assert resp.status_code == 200

    def test_time_summary_group_by_user(self, base_url, _headers):
        resp = requests.get(f"{base_url}{PREFIX}/reports/summary?group_by=user", headers=_headers)
        assert resp.status_code == 200
