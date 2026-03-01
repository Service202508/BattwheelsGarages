"""Smoke test to verify conftest.py fixtures work correctly."""
import requests

def test_base_url_fixture(base_url):
    assert base_url.startswith("http"), f"Invalid base_url: {base_url}"

def test_admin_token_fixture(admin_token):
    assert admin_token and len(admin_token) > 20, "Admin token looks invalid"

def test_demo_token_fixture(demo_token):
    assert demo_token and len(demo_token) > 20, "Demo token looks invalid"

def test_auth_headers_fixture(auth_headers):
    assert "Authorization" in auth_headers
    assert auth_headers["Authorization"].startswith("Bearer ")

def test_admin_headers_fixture(admin_headers):
    assert "Authorization" in admin_headers
    assert admin_headers["Authorization"].startswith("Bearer ")

def test_admin_can_access_health(base_url, admin_headers):
    resp = requests.get(f"{base_url}/api/health", headers=admin_headers)
    assert resp.status_code == 200

def test_demo_can_access_health(base_url, auth_headers):
    resp = requests.get(f"{base_url}/api/health", headers=auth_headers)
    assert resp.status_code == 200
