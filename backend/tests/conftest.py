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


@pytest.fixture(scope="session", autouse=True)
def _seed_test_data(_db):
    """Seed required test entities that many test files reference by hardcoded IDs."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    dev_org = "dev-internal-testing-001"
    demo_org = "demo-volt-motors-001"

    # --- Contacts (customers / vendors) referenced by tests ---
    test_contacts = [
        {
            "contact_id": "CON-235065AEEC94",
            "contact_number": "C-SEED-001",
            "contact_type": "customer",
            "name": "Rahul Sharma",
            "display_name": "Rahul Sharma",
            "email": "rahul.sharma@test.com",
            "phone": "9876543210",
            "organization_id": dev_org,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
        {
            "contact_id": "CUST-93AE14BE3618",
            "contact_number": "C-SEED-002",
            "contact_type": "customer",
            "name": "Full Zoho Test Co",
            "display_name": "Full Zoho Test Co",
            "email": "zoho.test@test.com",
            "phone": "9876543211",
            "organization_id": dev_org,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
        {
            "contact_id": "1837096000000463081",
            "contact_number": "C-SEED-003",
            "contact_type": "customer",
            "name": "Integration Test Contact",
            "display_name": "Integration Test Contact",
            "email": "integration@test.com",
            "phone": "9876543212",
            "organization_id": dev_org,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
    ]
    for contact in test_contacts:
        _db.contacts.update_one(
            {"contact_id": contact["contact_id"]},
            {"$setOnInsert": contact},
            upsert=True,
        )

    # --- Items referenced by tests ---
    test_items = [
        {
            "item_id": "I-DDC36534C55C",
            "name": "EV Battery Service",
            "item_type": "service",
            "sku": "SVC-BAT-001",
            "unit_price": 5000,
            "rate": 5000,
            "sales_rate": 5000,
            "quantity": 0,
            "organization_id": dev_org,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
        {
            "item_id": "1837096000000446195",
            "name": "12V Battery replacement",
            "item_type": "inventory",
            "sku": "BAT-12V-001",
            "unit_price": 200,
            "rate": 200,
            "sales_rate": 200,
            "purchase_rate": 150,
            "quantity": 100,
            "organization_id": dev_org,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
        {
            "item_id": "1837096000001141394",
            "name": "2 Wheeler Seatcover-25",
            "item_type": "inventory",
            "sku": "SC-2W-025",
            "unit_price": 200,
            "rate": 200,
            "sales_rate": 200,
            "quantity": 50,
            "organization_id": dev_org,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
    ]
    for item in test_items:
        _db.items.update_one(
            {"item_id": item["item_id"]},
            {"$setOnInsert": item},
            upsert=True,
        )
        # Ensure rate fields are always set
        _db.items.update_one(
            {"item_id": item["item_id"]},
            {"$set": {
                "rate": item.get("rate", item.get("unit_price", 0)),
                "sales_rate": item.get("sales_rate", item.get("unit_price", 0)),
            }},
        )

    # --- Price Lists ---
    _db.price_lists.update_one(
        {"pricelist_id": "PL-B575D8BF"},
        {"$setOnInsert": {
            "pricelist_id": "PL-B575D8BF",
            "organization_id": dev_org,
            "name": "Wholesale",
            "description": "Wholesale price list - 15% discount",
            "discount_percentage": 15.0,
            "markup_percentage": 0.0,
            "is_active": True,
            "item_count": 1,
            "created_time": now,
            "updated_time": now,
        }},
        upsert=True,
    )

    # --- Item Prices (link items to price lists) ---
    _db.item_prices.update_one(
        {"item_id": "1837096000000446195", "price_list_id": "PL-B575D8BF"},
        {"$setOnInsert": {
            "price_id": "IP-SEED-001",
            "item_id": "1837096000000446195",
            "item_name": "12V Battery replacement",
            "organization_id": dev_org,
            "price_list_id": "PL-B575D8BF",
            "price_list_name": "Wholesale",
            "rate": 170.0,
            "created_time": now,
            "updated_time": now,
        }},
        upsert=True,
    )

    # --- Assign Wholesale price list to CUST-93AE14BE3618 ---
    _db.contacts.update_one(
        {"contact_id": "CUST-93AE14BE3618"},
        {"$set": {
            "price_list_id": "PL-B575D8BF",
            "price_list_name": "Wholesale",
            "sales_price_list_id": "PL-B575D8BF",
        }},
    )

    yield
    # Cleanup: remove seeded test data
    _db.contacts.delete_many({"contact_id": {"$in": [c["contact_id"] for c in test_contacts]}})
    _db.items.delete_many({"item_id": {"$in": [i["item_id"] for i in test_items]}})
    _db.price_lists.delete_many({"pricelist_id": "PL-B575D8BF"})
    _db.item_prices.delete_many({"price_list_id": "PL-B575D8BF"})


# ── Guard: re-seed critical entities before each test MODULE ──
# Some test files delete contacts/items via API calls during their execution.
# This fixture detects missing seed data and restores it cheaply.
_CRITICAL_CONTACTS = {
    "CON-235065AEEC94": {
        "contact_id": "CON-235065AEEC94",
        "contact_number": "C-SEED-001",
        "contact_type": "customer",
        "name": "Rahul Sharma",
        "display_name": "Rahul Sharma",
        "email": "rahul.sharma@test.com",
        "phone": "9876543210",
        "organization_id": "dev-internal-testing-001",
        "status": "active",
    },
    "CUST-93AE14BE3618": {
        "contact_id": "CUST-93AE14BE3618",
        "contact_number": "C-SEED-002",
        "contact_type": "customer",
        "name": "Full Zoho Test Co",
        "display_name": "Full Zoho Test Co",
        "email": "zoho.test@test.com",
        "phone": "9876543211",
        "organization_id": "dev-internal-testing-001",
        "status": "active",
        "price_list_id": "PL-B575D8BF",
        "price_list_name": "Wholesale",
        "sales_price_list_id": "PL-B575D8BF",
    },
    "1837096000000463081": {
        "contact_id": "1837096000000463081",
        "contact_number": "C-SEED-003",
        "contact_type": "customer",
        "name": "Integration Test Contact",
        "display_name": "Integration Test Contact",
        "email": "integration@test.com",
        "phone": "9876543212",
        "organization_id": "dev-internal-testing-001",
        "status": "active",
    },
}

_CRITICAL_ITEMS = {
    "I-DDC36534C55C": {
        "item_id": "I-DDC36534C55C",
        "name": "EV Battery Service",
        "item_type": "service",
        "sku": "SVC-BAT-001",
        "unit_price": 5000,
        "rate": 5000,
        "sales_rate": 5000,
        "quantity": 0,
        "organization_id": "dev-internal-testing-001",
        "status": "active",
    },
    "1837096000000446195": {
        "item_id": "1837096000000446195",
        "name": "12V Battery replacement",
        "item_type": "inventory",
        "sku": "BAT-12V-001",
        "unit_price": 200,
        "rate": 200,
        "sales_rate": 200,
        "purchase_rate": 150,
        "quantity": 100,
        "organization_id": "dev-internal-testing-001",
        "status": "active",
    },
    "1837096000001141394": {
        "item_id": "1837096000001141394",
        "name": "2 Wheeler Seatcover-25",
        "item_type": "inventory",
        "sku": "SC-2W-025",
        "unit_price": 200,
        "rate": 200,
        "sales_rate": 200,
        "quantity": 50,
        "organization_id": "dev-internal-testing-001",
        "status": "active",
    },
}


@pytest.fixture(scope="module", autouse=True)
def _reseed_if_missing(_db):
    """Cheaply verify and re-seed critical test entities before each module.

    This guards against state pollution where a prior test module deletes
    contacts or items via API calls, causing later tests to receive 404.
    """
    for cid, doc in _CRITICAL_CONTACTS.items():
        _db.contacts.update_one(
            {"contact_id": cid},
            {"$set": doc},
            upsert=True,
        )

    for iid, doc in _CRITICAL_ITEMS.items():
        _db.items.update_one(
            {"item_id": iid},
            {"$set": doc},
            upsert=True,
        )

    # Ensure price list exists
    _db.price_lists.update_one(
        {"pricelist_id": "PL-B575D8BF"},
        {"$set": {
            "pricelist_id": "PL-B575D8BF",
            "organization_id": "dev-internal-testing-001",
            "name": "Wholesale",
            "description": "Wholesale price list - 15% discount",
            "discount_percentage": 15.0,
            "markup_percentage": 0.0,
            "is_active": True,
        }},
        upsert=True,
    )

    # Ensure item-price link exists
    _db.item_prices.update_one(
        {"item_id": "1837096000000446195", "price_list_id": "PL-B575D8BF"},
        {"$set": {
            "price_id": "IP-SEED-001",
            "item_id": "1837096000000446195",
            "item_name": "12V Battery replacement",
            "organization_id": "dev-internal-testing-001",
            "price_list_id": "PL-B575D8BF",
            "price_list_name": "Wholesale",
            "rate": 170.0,
        }},
        upsert=True,
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
        if isinstance(headers, dict):
            headers = dict(headers)
            if "Authorization" not in headers:
                headers["Authorization"] = f"Bearer {token}"
            if "X-Organization-ID" not in headers:
                headers["X-Organization-ID"] = "dev-internal-testing-001"
            kwargs["headers"] = headers
        return _ORIGINAL_SESSION_REQUEST(self, method, url, **kwargs)

    requests.Session.request = _patched_request
    yield
    requests.Session.request = _ORIGINAL_SESSION_REQUEST
