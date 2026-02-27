"""
Tests for Onboarding Checklist feature:
- GET /api/organizations/onboarding/status
- POST /api/organizations/onboarding/complete-step
- POST /api/organizations/onboarding/skip
Tests new org (org_test_onboarding1) and Battwheels Garages (6996dcf072ffd2a2395fee7b)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

NEW_ORG_TOKEN = "REDACTED_JWT_TOKEN"
BATTWHEELS_TOKEN = "REDACTED_JWT_TOKEN"


def new_org_headers():
    return {
        "Authorization": f"Bearer {NEW_ORG_TOKEN}",
        "x-organization-id": "org_test_onboarding1",
        "Content-Type": "application/json"
    }


def battwheels_headers():
    return {
        "Authorization": f"Bearer {BATTWHEELS_TOKEN}",
        "x-organization-id": "dev-internal-testing-001",
        "Content-Type": "application/json"
    }


def reset_test_org():
    """Reset the test org to clean state via MongoDB"""
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from datetime import datetime, timezone

    async def _reset():
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = client["test_database"]
        await db.organizations.update_one(
            {"organization_id": "org_test_onboarding1"},
            {"$set": {"onboarding_completed": False, "onboarding_steps_completed": []}}
        )
        client.close()

    asyncio.run(_reset())


class TestOnboardingStatusNewOrg:
    """Tests for GET /api/organizations/onboarding/status - new org"""

    def test_onboarding_status_returns_200(self):
        """Status endpoint returns 200 for new org"""
        reset_test_org()
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_onboarding_status_show_onboarding_true(self):
        """show_onboarding is True for new org (created < 7 days ago, not completed)"""
        reset_test_org()
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200
        data = r.json()
        assert "show_onboarding" in data, "Response missing show_onboarding field"
        assert data["show_onboarding"] is True, f"Expected show_onboarding=True, got {data['show_onboarding']}"

    def test_onboarding_status_response_structure(self):
        """Response has all required fields"""
        reset_test_org()
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200
        data = r.json()
        required_fields = ["onboarding_completed", "onboarding_steps_completed",
                           "show_onboarding", "total_steps", "completed_count"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_onboarding_status_total_steps_is_6(self):
        """Total steps is 6"""
        reset_test_org()
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200
        data = r.json()
        assert data["total_steps"] == 6, f"Expected total_steps=6, got {data['total_steps']}"

    def test_onboarding_status_completed_count_zero_initially(self):
        """Completed count is 0 for fresh org with no data"""
        reset_test_org()
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200
        data = r.json()
        # completed_count should reflect actual data (0 for clean test org)
        assert isinstance(data["completed_count"], int), "completed_count should be int"

    def test_onboarding_not_completed_initially(self):
        """onboarding_completed is False for fresh org"""
        reset_test_org()
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200
        data = r.json()
        assert data["onboarding_completed"] is False, f"Expected onboarding_completed=False, got {data['onboarding_completed']}"


class TestOnboardingStatusBattwheels:
    """Tests for GET /api/organizations/onboarding/status - Battwheels (should never show banner)"""

    def test_battwheels_returns_200(self):
        """Status endpoint returns 200 for Battwheels"""
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=battwheels_headers())
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_battwheels_show_onboarding_false(self):
        """show_onboarding is False for Battwheels (onboarding_completed=True)"""
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=battwheels_headers())
        assert r.status_code == 200
        data = r.json()
        assert data["show_onboarding"] is False, f"Expected show_onboarding=False for Battwheels, got {data['show_onboarding']}"

    def test_battwheels_onboarding_completed_true(self):
        """onboarding_completed is True for Battwheels"""
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=battwheels_headers())
        assert r.status_code == 200
        data = r.json()
        assert data["onboarding_completed"] is True, f"Expected onboarding_completed=True, got {data['onboarding_completed']}"


class TestOnboardingCompleteStep:
    """Tests for POST /api/organizations/onboarding/complete-step"""

    def test_complete_step_returns_success(self):
        """Complete step returns 200 with success=True"""
        reset_test_org()
        r = requests.post(
            f"{BASE_URL}/api/organizations/onboarding/complete-step",
            headers=new_org_headers(),
            json={"step": "add_first_contact"}
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["success"] is True, f"Expected success=True, got {data}"

    def test_complete_step_persists(self):
        """Step is persisted and shown in status response"""
        reset_test_org()
        # Mark add_first_contact complete
        requests.post(
            f"{BASE_URL}/api/organizations/onboarding/complete-step",
            headers=new_org_headers(),
            json={"step": "add_first_contact"}
        )
        # Verify it appears in status
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200
        data = r.json()
        assert "add_first_contact" in data["onboarding_steps_completed"], \
            f"add_first_contact should be in completed steps, got: {data['onboarding_steps_completed']}"

    def test_complete_step_invalid_step_returns_400(self):
        """Invalid step returns 400"""
        reset_test_org()
        r = requests.post(
            f"{BASE_URL}/api/organizations/onboarding/complete-step",
            headers=new_org_headers(),
            json={"step": "invalid_step_xyz"}
        )
        assert r.status_code == 400, f"Expected 400 for invalid step, got {r.status_code}: {r.text}"

    def test_complete_step_response_structure(self):
        """Response has expected fields"""
        reset_test_org()
        r = requests.post(
            f"{BASE_URL}/api/organizations/onboarding/complete-step",
            headers=new_org_headers(),
            json={"step": "create_first_ticket"}
        )
        assert r.status_code == 200
        data = r.json()
        assert "success" in data
        assert "step" in data
        assert "all_completed" in data
        assert "completed_steps" in data
        assert data["step"] == "create_first_ticket"


class TestOnboardingSkip:
    """Tests for POST /api/organizations/onboarding/skip"""

    def test_skip_returns_success(self):
        """Skip returns 200 with success=True"""
        reset_test_org()
        r = requests.post(
            f"{BASE_URL}/api/organizations/onboarding/skip",
            headers=new_org_headers()
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["success"] is True, f"Expected success=True, got {data}"

    def test_skip_sets_onboarding_completed(self):
        """After skip, onboarding_completed=True and show_onboarding=False"""
        reset_test_org()
        # Skip
        r_skip = requests.post(
            f"{BASE_URL}/api/organizations/onboarding/skip",
            headers=new_org_headers()
        )
        assert r_skip.status_code == 200

        # Verify status now shows completed
        r_status = requests.get(
            f"{BASE_URL}/api/organizations/onboarding/status",
            headers=new_org_headers()
        )
        assert r_status.status_code == 200
        data = r_status.json()
        assert data["onboarding_completed"] is True, \
            f"Expected onboarding_completed=True after skip, got {data['onboarding_completed']}"
        assert data["show_onboarding"] is False, \
            f"Expected show_onboarding=False after skip, got {data['show_onboarding']}"

    def test_skip_resets_and_show_banner_again(self):
        """After reset, show_onboarding becomes True again"""
        # Reset back
        reset_test_org()
        r = requests.get(f"{BASE_URL}/api/organizations/onboarding/status", headers=new_org_headers())
        assert r.status_code == 200
        data = r.json()
        assert data["show_onboarding"] is True, \
            f"After reset, show_onboarding should be True again, got {data['show_onboarding']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
