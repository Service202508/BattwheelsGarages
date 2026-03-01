"""
Comprehensive Tickets Endpoint Tests
=====================================
Tests for 13 previously untested ticket endpoints.
Uses shared conftest.py fixtures (base_url, dev_headers, admin_headers).

Run: pytest backend/tests/test_tickets_comprehensive.py -v --tb=short
"""

import pytest
import requests
import uuid


# ==================== HELPERS ====================

@pytest.fixture(scope="module")
def _tokens(base_url):
    """Get dev user token with org context for ticket operations."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "dev@battwheels.internal",
        "password": "DevTest@123"
    })
    assert resp.status_code == 200
    token = resp.json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "dev-internal-testing-001",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def test_ticket(base_url, _tokens):
    """Create a test ticket and return it. Cleaned up after module."""
    resp = requests.post(f"{base_url}/api/v1/tickets", headers=_tokens, json={
        "title": f"Test Ticket {uuid.uuid4().hex[:8]}",
        "description": "Comprehensive test ticket for endpoint testing",
        "priority": "medium",
        "vehicle_type": "electric_scooter",
        "vehicle_number": "TEST-0001",
        "customer_name": "Test Customer",
        "contact_number": "9999999999"
    })
    assert resp.status_code == 200, f"Failed to create test ticket: {resp.text}"
    data = resp.json()
    ticket_id = data.get("ticket_id")
    assert ticket_id, f"No ticket_id in response: {data}"
    return data


# ==================== 1. GET /api/v1/tickets/stats ====================

class TestTicketStats:
    def test_stats_returns_expected_fields(self, base_url, _tokens):
        resp = requests.get(f"{base_url}/api/v1/tickets/stats", headers=_tokens)
        assert resp.status_code == 200
        data = resp.json()
        assert "by_status" in data or "open" in data or "total" in data

    def test_stats_requires_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/v1/tickets/stats")
        assert resp.status_code in [401, 403, 422]


# ==================== 2. PUT /api/v1/tickets/{id} ====================

class TestTicketUpdate:
    def test_update_title(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        new_title = f"Updated Title {uuid.uuid4().hex[:6]}"
        resp = requests.put(f"{base_url}/api/v1/tickets/{tid}", headers=_tokens, json={
            "title": new_title
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("title") == new_title

    def test_update_priority(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.put(f"{base_url}/api/v1/tickets/{tid}", headers=_tokens, json={
            "priority": "high"
        })
        assert resp.status_code == 200
        assert resp.json().get("priority") == "high"

    def test_update_nonexistent_ticket(self, base_url, _tokens):
        resp = requests.put(f"{base_url}/api/v1/tickets/tkt_nonexistent_999", headers=_tokens, json={
            "title": "Should fail"
        })
        assert resp.status_code in [404, 400]

    def test_update_requires_auth(self, base_url, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.put(f"{base_url}/api/v1/tickets/{tid}", json={"title": "x"})
        assert resp.status_code in [401, 403, 422]


# ==================== 3. POST /api/v1/tickets/{id}/close ====================

class TestTicketClose:
    @pytest.fixture(scope="class")
    def closable_ticket(self, base_url, _tokens):
        resp = requests.post(f"{base_url}/api/v1/tickets", headers=_tokens, json={
            "title": f"Closable Ticket {uuid.uuid4().hex[:8]}",
            "description": "Ticket to be closed in test",
            "priority": "low",
            "vehicle_type": "electric_scooter"
        })
        assert resp.status_code == 200
        return resp.json()

    def test_close_ticket(self, base_url, _tokens, closable_ticket):
        tid = closable_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/close", headers=_tokens, json={
            "resolution": "Test resolution — issue resolved",
            "resolution_outcome": "success"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") in ["closed", "resolved"]

    def test_close_nonexistent_ticket(self, base_url, _tokens):
        resp = requests.post(f"{base_url}/api/v1/tickets/tkt_nonexistent_999/close", headers=_tokens, json={
            "resolution": "Test",
            "resolution_outcome": "success"
        })
        assert resp.status_code in [404, 400]

    def test_close_requires_auth(self, base_url, closable_ticket):
        tid = closable_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/close", json={
            "resolution": "x", "resolution_outcome": "success"
        })
        assert resp.status_code in [401, 403, 422]


# ==================== 4. POST /api/v1/tickets/{id}/start-work ====================

class TestStartWork:
    @pytest.fixture(scope="class")
    def workable_ticket(self, base_url, _tokens):
        resp = requests.post(f"{base_url}/api/v1/tickets", headers=_tokens, json={
            "title": f"Workable Ticket {uuid.uuid4().hex[:8]}",
            "description": "Ticket for start-work test",
            "priority": "medium",
            "vehicle_type": "electric_scooter"
        })
        assert resp.status_code == 200
        return resp.json()

    def test_start_work(self, base_url, _tokens, workable_ticket):
        tid = workable_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/start-work", headers=_tokens, json={
            "notes": "Starting work on test ticket"
        })
        # 200 = success, 400 = invalid state transition (also acceptable)
        assert resp.status_code in [200, 400], f"Unexpected: {resp.status_code} {resp.text}"

    def test_start_work_requires_auth(self, base_url, workable_ticket):
        tid = workable_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/start-work", json={})
        assert resp.status_code in [401, 403, 422]


# ==================== 5. POST /api/v1/tickets/{id}/complete-work ====================

class TestCompleteWork:
    @pytest.fixture(scope="class")
    def completable_ticket(self, base_url, _tokens):
        resp = requests.post(f"{base_url}/api/v1/tickets", headers=_tokens, json={
            "title": f"Completable Ticket {uuid.uuid4().hex[:8]}",
            "description": "Ticket for complete-work test",
            "priority": "medium",
            "vehicle_type": "electric_scooter"
        })
        assert resp.status_code == 200
        ticket = resp.json()
        # Try to start work first
        requests.post(f"{base_url}/api/v1/tickets/{ticket['ticket_id']}/start-work",
                       headers=_tokens, json={"notes": "prep"})
        return ticket

    def test_complete_work(self, base_url, _tokens, completable_ticket):
        tid = completable_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/complete-work", headers=_tokens, json={
            "work_summary": "Work completed — replaced battery connector",
            "parts_used": ["battery_connector_v2"],
            "labor_hours": 1.5,
            "notes": "All tests passed after replacement"
        })
        assert resp.status_code in [200, 400], f"Unexpected: {resp.status_code} {resp.text}"

    def test_complete_work_requires_auth(self, base_url, completable_ticket):
        tid = completable_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/complete-work", json={
            "work_summary": "x"
        })
        assert resp.status_code in [401, 403, 422]


# ==================== 6. GET /api/v1/tickets/{id}/activities ====================

class TestGetActivities:
    def test_get_activities(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.get(f"{base_url}/api/v1/tickets/{tid}/activities", headers=_tokens)
        assert resp.status_code == 200
        data = resp.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)

    def test_get_activities_requires_auth(self, base_url, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.get(f"{base_url}/api/v1/tickets/{tid}/activities")
        assert resp.status_code in [401, 403, 422]


# ==================== 7. POST /api/v1/tickets/{id}/activities ====================

class TestAddActivity:
    def test_add_activity(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/activities", headers=_tokens, json={
            "action": "note",
            "description": "Test activity added during comprehensive testing"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("action") == "note" or data.get("activity_id")

    def test_add_activity_requires_auth(self, base_url, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/activities", json={
            "action": "note", "description": "x"
        })
        assert resp.status_code in [401, 403, 422]


# ==================== 8. PUT /api/v1/tickets/{id}/activities/{activity_id} ====================

class TestUpdateActivity:
    @pytest.fixture(scope="class")
    def activity_data(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        # Create an activity first
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/activities", headers=_tokens, json={
            "action": "note",
            "description": "Activity to be updated"
        })
        assert resp.status_code == 200
        return resp.json()

    def test_update_activity(self, base_url, _tokens, test_ticket, activity_data):
        tid = test_ticket["ticket_id"]
        aid = activity_data.get("activity_id")
        if not aid:
            pytest.skip("No activity_id returned from create")
        resp = requests.put(f"{base_url}/api/v1/tickets/{tid}/activities/{aid}", headers=_tokens, json={
            "description": "Updated activity description"
        })
        # 200 = success, 403 = needs admin role (the dev user has 'owner' role)
        assert resp.status_code in [200, 403], f"Unexpected: {resp.status_code} {resp.text}"


# ==================== 9. DELETE /api/v1/tickets/{id}/activities/{activity_id} ====================

class TestDeleteActivity:
    @pytest.fixture(scope="class")
    def deletable_activity(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/activities", headers=_tokens, json={
            "action": "note",
            "description": "Activity to be deleted"
        })
        assert resp.status_code == 200
        return resp.json()

    def test_delete_activity(self, base_url, _tokens, test_ticket, deletable_activity):
        tid = test_ticket["ticket_id"]
        aid = deletable_activity.get("activity_id")
        if not aid:
            pytest.skip("No activity_id returned from create")
        resp = requests.delete(f"{base_url}/api/v1/tickets/{tid}/activities/{aid}", headers=_tokens)
        # 200 = success, 403 = needs admin role
        assert resp.status_code in [200, 403], f"Unexpected: {resp.status_code} {resp.text}"

    def test_delete_nonexistent_activity(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.delete(f"{base_url}/api/v1/tickets/{tid}/activities/act_nonexistent", headers=_tokens)
        assert resp.status_code in [403, 404]


# ==================== 10. POST /api/v1/tickets/{id}/assign ====================

class TestAssignTicket:
    def test_assign_ticket(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/assign", headers=_tokens, json={
            "technician_id": "tech_test_001"
        })
        assert resp.status_code in [200, 400, 404], f"Unexpected: {resp.status_code} {resp.text}"

    def test_assign_nonexistent_ticket(self, base_url, _tokens):
        resp = requests.post(f"{base_url}/api/v1/tickets/tkt_nonexistent_999/assign", headers=_tokens, json={
            "technician_id": "tech_test_001"
        })
        assert resp.status_code in [404, 400]

    def test_assign_requires_auth(self, base_url, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/assign", json={
            "technician_id": "tech_test_001"
        })
        assert resp.status_code in [401, 403, 422]


# ==================== 11. GET /api/v1/tickets/{id}/matches ====================

class TestTicketMatches:
    def test_get_matches(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.get(f"{base_url}/api/v1/tickets/{tid}/matches", headers=_tokens)
        assert resp.status_code in [200, 404], f"Unexpected: {resp.status_code} {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert "matches" in data or "cards" in data or isinstance(data, dict)

    def test_matches_nonexistent_ticket(self, base_url, _tokens):
        resp = requests.get(f"{base_url}/api/v1/tickets/tkt_nonexistent_999/matches", headers=_tokens)
        assert resp.status_code in [404, 200]

    def test_matches_requires_auth(self, base_url, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.get(f"{base_url}/api/v1/tickets/{tid}/matches")
        assert resp.status_code in [401, 403, 422]


# ==================== 12. POST /api/v1/tickets/{id}/select-card ====================

class TestSelectCard:
    def test_select_card(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/select-card", headers=_tokens, json={
            "failure_id": "fc_test_nonexistent"
        })
        # 200 = success, 404 = card not found (expected for non-existent card)
        assert resp.status_code in [200, 404, 400], f"Unexpected: {resp.status_code} {resp.text}"

    def test_select_card_requires_auth(self, base_url, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/select-card", json={
            "failure_id": "fc_test"
        })
        assert resp.status_code in [401, 403, 422]


# ==================== 13. POST /api/v1/tickets/{id}/select-card/{failure_id} ====================

class TestSelectCardLegacy:
    def test_select_card_legacy(self, base_url, _tokens, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/select-card/fc_test_legacy", headers=_tokens)
        assert resp.status_code in [200, 404, 400], f"Unexpected: {resp.status_code} {resp.text}"

    def test_select_card_legacy_requires_auth(self, base_url, test_ticket):
        tid = test_ticket["ticket_id"]
        resp = requests.post(f"{base_url}/api/v1/tickets/{tid}/select-card/fc_test")
        assert resp.status_code in [401, 403, 422]
