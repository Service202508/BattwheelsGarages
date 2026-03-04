"""
Tests for AI Diagnostic Token Service
======================================
8 tests covering: status, consumption, limits, reset, trial expiry,
enterprise unlimited, API auth.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.ai_token_service import (
    get_plan_token_limit,
    get_token_status,
    consume_token,
    init_ai_token_service,
    _is_free_trial_expired,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_db():
    """Create a mock MongoDB database."""
    db = MagicMock()
    db.ai_usage = AsyncMock()
    db.organizations = AsyncMock()
    return db


@pytest.fixture
def setup_service(mock_db):
    """Init the ai_token_service with mock db."""
    init_ai_token_service(mock_db)
    return mock_db


# ==================== TESTS ====================

class TestAITokenService:

    def test_get_token_status_returns_correct_structure(self, setup_service):
        """Test 1: get_token_status returns correct structure"""
        db = setup_service
        db.organizations.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "plan": "professional",
            "created_at": datetime.now(timezone.utc),
        })
        db.ai_usage.find_one = AsyncMock(return_value=None)
        db.ai_usage.insert_one = AsyncMock()

        result = asyncio.get_event_loop().run_until_complete(
            get_token_status("org-1")
        )

        assert "tokens_used" in result
        assert "tokens_limit" in result
        assert "tokens_remaining" in result
        assert "plan" in result
        assert result["tokens_limit"] == 100
        assert result["tokens_remaining"] == 100
        assert result["tokens_used"] == 0
        assert result["plan"] == "professional"

    def test_consume_token_decrements_count(self, setup_service):
        """Test 2: consume_token decrements count"""
        db = setup_service
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")

        db.organizations.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "plan": "starter",
            "created_at": datetime.now(timezone.utc),
        })
        db.ai_usage.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "month": current_month,
            "tokens_used": 5,
            "tokens_limit": 25,
            "plan": "starter",
            "sessions": [],
        })
        db.ai_usage.update_one = AsyncMock()

        result = asyncio.get_event_loop().run_until_complete(
            consume_token("org-1", "sess-1", "tkt-1")
        )

        assert result["success"] is True
        assert result["tokens_remaining"] == 19  # 25 - 5 - 1 = 19
        db.ai_usage.update_one.assert_called_once()

    def test_consume_token_rejects_when_limit_reached(self, setup_service):
        """Test 3: consume_token rejects when limit reached"""
        db = setup_service
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")

        db.organizations.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "plan": "starter",
            "created_at": datetime.now(timezone.utc),
        })
        db.ai_usage.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "month": current_month,
            "tokens_used": 25,
            "tokens_limit": 25,
            "plan": "starter",
            "sessions": [],
        })

        result = asyncio.get_event_loop().run_until_complete(
            consume_token("org-1", "sess-1", "tkt-1")
        )

        assert result["success"] is False
        assert "limit reached" in result["error"]

    def test_lazy_monthly_reset_works(self, setup_service):
        """Test 4: lazy monthly reset works (new month creates fresh doc)"""
        db = setup_service
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")

        db.organizations.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "plan": "professional",
            "created_at": datetime.now(timezone.utc),
        })
        # No usage doc for current month → triggers lazy creation
        db.ai_usage.find_one = AsyncMock(return_value=None)
        db.ai_usage.insert_one = AsyncMock()

        result = asyncio.get_event_loop().run_until_complete(
            get_token_status("org-1")
        )

        assert result["tokens_used"] == 0
        assert result["tokens_remaining"] == 100
        assert result["month"] == current_month
        db.ai_usage.insert_one.assert_called_once()

    def test_free_trial_expires_after_14_days(self, setup_service):
        """Test 5: free trial expires after 14 days"""
        db = setup_service

        # Org created 20 days ago — trial expired
        db.organizations.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "plan": "free",
            "created_at": datetime.now(timezone.utc) - timedelta(days=20),
        })
        db.ai_usage.find_one = AsyncMock(return_value=None)
        db.ai_usage.insert_one = AsyncMock()

        result = asyncio.get_event_loop().run_until_complete(
            get_token_status("org-1")
        )

        assert result["tokens_limit"] == 0
        assert result["tokens_remaining"] == 0

    def test_enterprise_has_unlimited_tokens(self, setup_service):
        """Test 6: enterprise has unlimited tokens"""
        db = setup_service

        db.organizations.find_one = AsyncMock(return_value={
            "organization_id": "org-1",
            "plan": "enterprise",
            "created_at": datetime.now(timezone.utc),
        })
        db.ai_usage.find_one = AsyncMock(return_value=None)

        result = asyncio.get_event_loop().run_until_complete(
            get_token_status("org-1")
        )

        assert result["unlimited"] is True
        assert result["tokens_limit"] == -1

    def test_api_endpoint_returns_200_with_valid_auth(self):
        """Test 7: API endpoint returns 200 with valid auth"""
        from fastapi.testclient import TestClient

        # We test via live API call instead of TestClient for simplicity
        import requests
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        if api_url == "http://localhost:8001":
            api_url = "http://localhost:8001/api"

        # Login
        login_resp = requests.post(
            f"{api_url}/v1/auth/login",
            json={"email": "demo@voltmotors.in", "password": "Demo@12345"},
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token") or login_resp.json().get("token")

        # Get org_id
        org_id = login_resp.json().get("user", {}).get("organization_id", "demo-volt-motors-001")

        # Call status endpoint
        resp = requests.get(
            f"{api_url}/v1/ai-usage/status",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": org_id,
            },
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "tokens_used" in data
        assert "tokens_limit" in data
        assert "tokens_remaining" in data
        assert "plan" in data

    def test_api_endpoint_returns_401_without_auth(self):
        """Test 8: API endpoint returns 401 without auth"""
        import requests
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        if api_url == "http://localhost:8001":
            api_url = "http://localhost:8001/api"

        resp = requests.get(f"{api_url}/v1/ai-usage/status")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
