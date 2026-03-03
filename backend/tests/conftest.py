"""
Shared test fixtures for Battwheels OS test suite.

Provides reusable authentication fixtures so individual test files
don't need to implement their own login logic.

The _auto_inject_auth fixture monkey-patches requests.Session.request
to automatically inject Authorization headers into ALL outgoing HTTP
requests, unless the test is explicitly testing auth-denial behavior
(detected by test function name heuristics) or the request already
carries an Authorization header.

Usage in test files:
    def test_something(auth_headers):
        resp = requests.get(f"{base_url}/api/v1/tickets", headers=auth_headers)

    def test_admin_only(admin_headers):
        resp = requests.get(f"{base_url}/api/v1/platform/...", headers=admin_headers)
"""

import os
import re
import pymongo
import pytest
import requests

# ── Name patterns for tests that intentionally test auth denial ──
_NO_AUTH_PATTERNS = re.compile(
    r"requires_auth|require_auth|without_auth|without_token"
    r"|no_auth(?!.*required)|no_token|missing_auth|missing_session"
    r"|unauthorized|unauthenticated"
    r"|invalid_login|invalid_credentials|invalid_session|invalid_token"
    r"|wrong_org_token|wrong_current_password"
    r"|csrf|rate_limit|soft_delete"
    r"|_401|returns_401",
    re.IGNORECASE,
)

# Patterns that LOOK like no-auth tests but actually need auth
_AUTH_OK_PATTERNS = re.compile(
    r"no_auth_required|accessible_without|public|bypasses_csrf",
    re.IGNORECASE,
)

# Store original Session.request once at import time
_ORIGINAL_SESSION_REQUEST = requests.Session.request


@pytest.fixture(scope="session")
def _db():
    """Shared MongoDB client for the test session."""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "battwheels_dev")
    client = pymongo.MongoClient(mongo_url)
    db = client[db_name]
    yield db
    client.close()


@pytest.fixture(scope="session", autouse=True)
def _clear_login_attempts_session(_db):
    """Clear login_attempts collection at session boundaries."""
    _db.login_attempts.delete_many({})
    yield
    _db.login_attempts.delete_many({})


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_user_passwords(_db):
    """Ensure key test user passwords are correct at session start.
    
    Tests may corrupt passwords via change-password endpoints.
    This fixture resets them to known-good values.
    """
    import bcrypt
    import time
    users = {
        "demo@voltmotors.in": "Demo@12345",
        "dev@battwheels.internal": "DevTest@123",
        "platform-admin@battwheels.in": "DevTest@123",
        "admin@battwheels.in": "DevTest@123",
    }
    for email, password in users.items():
        new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        _db.users.update_one(
            {"email": email},
            {"$set": {"password_hash": new_hash, "pwd_version": time.time()}}
        )
    yield
    # Reset passwords again after tests (in case tests changed them)
    for email, password in users.items():
        new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        _db.users.update_one(
            {"email": email},
            {"$set": {"password_hash": new_hash, "pwd_version": time.time()}}
        )


@pytest.fixture(autouse=True)
def _clear_login_attempts_per_test(_db):
    """Clear login_attempts before EVERY test to prevent 429 cascading."""
    _db.login_attempts.delete_many({})


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
def auth_headers(dev_token):
    """Headers dict with dev user Bearer token + org context.
    
    Uses the dev user (owner role) for broadest access across tests.
    Tests that specifically need the demo user should use demo_token directly.
    """
    return {
        "Authorization": f"Bearer {dev_token}",
        "X-Organization-ID": "dev-internal-testing-001"
    }

@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """Headers dict with platform admin Bearer token + org context."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "X-Organization-ID": "dev-internal-testing-001"
    }

@pytest.fixture(scope="session")
def dev_token(base_url):
    """Login as dev user (owner role, dev org) and return JWT token."""
    resp = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "dev@battwheels.internal",
        "password": "DevTest@123"
    })
    assert resp.status_code == 200, f"Dev user login failed: {resp.text}"
    return resp.json()["token"]

@pytest.fixture(scope="session")
def dev_headers(dev_token):
    """Headers dict with dev user Bearer token + org header."""
    return {
        "Authorization": f"Bearer {dev_token}",
        "X-Organization-ID": "dev-internal-testing-001"
    }


@pytest.fixture(autouse=True)
def _auto_inject_auth(request, dev_token):
    """Monkey-patch requests to auto-inject dev auth + org context on every HTTP call.

    Uses the dev token (owner role, dev org) for broadest access.
    Skipped for tests whose name signals they are *testing* auth denial
    (e.g. ``test_list_requires_auth``).  The original ``Session.request``
    is restored after each test function.
    """
    test_name = request.node.name

    # Decide whether to inject
    if _AUTH_OK_PATTERNS.search(test_name):
        should_inject = True
    elif _NO_AUTH_PATTERNS.search(test_name):
        should_inject = False
    else:
        should_inject = True

    if not should_inject:
        yield
        return

    token = dev_token

    def _patched_request(self, method, url, **kwargs):
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        if isinstance(headers, dict) and "Authorization" not in headers:
            headers = dict(headers)
            headers["Authorization"] = f"Bearer {token}"
            if "X-Organization-ID" not in headers:
                headers["X-Organization-ID"] = "dev-internal-testing-001"
            kwargs["headers"] = headers
        return _ORIGINAL_SESSION_REQUEST(self, method, url, **kwargs)

    requests.Session.request = _patched_request
    yield
    requests.Session.request = _ORIGINAL_SESSION_REQUEST
