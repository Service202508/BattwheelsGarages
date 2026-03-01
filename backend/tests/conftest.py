"""
Shared test fixtures for Battwheels OS test suite.

Provides reusable authentication fixtures so individual test files
don't need to implement their own login logic.

Usage in test files:
    def test_something(auth_headers):
        resp = requests.get(f"{base_url}/api/v1/tickets", headers=auth_headers)

    def test_admin_only(admin_headers):
        resp = requests.get(f"{base_url}/api/v1/platform/...", headers=admin_headers)
"""

import os
import pytest
import requests

@pytest.fixture(scope="session")
def base_url():
    """Backend API base URL."""
    url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
    return url.rstrip("/")

@pytest.fixture(scope="session")
def admin_token(base_url):
    """Login as platform admin and return JWT token."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "platform-admin@battwheels.in",
        "password": "DevTest@123"
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["token"]

@pytest.fixture(scope="session")
def demo_token(base_url):
    """Login as demo user and return JWT token."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "demo@voltmotors.in",
        "password": "Demo@12345"
    })
    assert resp.status_code == 200, f"Demo login failed: {resp.text}"
    return resp.json()["token"]

@pytest.fixture(scope="session")
def auth_headers(demo_token):
    """Headers dict with demo user Bearer token."""
    return {"Authorization": f"Bearer {demo_token}"}

@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """Headers dict with platform admin Bearer token."""
    return {"Authorization": f"Bearer {admin_token}"}
