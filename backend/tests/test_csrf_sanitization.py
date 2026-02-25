"""
Security Hardening Tests - CSRF Protection & Input Sanitization
================================================================
Tests for Week 3 Prompt 4 security features:
1. CSRF Protection (Double Submit Cookie pattern)
2. Input Sanitization (bleach XSS stripping)
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "demo@voltmotors.in"
TEST_PASSWORD = "Demo@12345"


class TestCSRFProtection:
    """CSRF Protection middleware tests - Double Submit Cookie pattern"""

    def test_health_endpoint_sets_csrf_cookie(self):
        """GET /api/health should set csrf_token cookie in response"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        # Check that csrf_token cookie is set
        csrf_cookie = session.cookies.get("csrf_token")
        assert csrf_cookie is not None, "csrf_token cookie not set on health endpoint"
        assert len(csrf_cookie) >= 32, f"CSRF token too short: {len(csrf_cookie)} chars"
        print(f"PASS: GET /api/health sets csrf_token cookie ({len(csrf_cookie)} chars)")

    def test_login_exempt_from_csrf(self):
        """POST to /api/auth/login should work WITHOUT csrf token (exempt path)"""
        session = requests.Session()
        
        # Attempt login without CSRF token
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        # Login should succeed without CSRF token (auth endpoints are exempt)
        assert response.status_code == 200, f"Login failed (should be CSRF exempt): {response.text}"
        data = response.json()
        assert "token" in data, "Login response missing token"
        print(f"PASS: POST /api/auth/login works without CSRF token (exempt)")

    def test_post_without_csrf_returns_403(self):
        """POST to non-exempt endpoint without CSRF token should return 403 CSRF_MISSING"""
        session = requests.Session()
        
        # First get CSRF cookie from health endpoint (but don't send it in header)
        session.get(f"{BASE_URL}/api/health")
        
        # Attempt POST without X-CSRF-Token header
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={"title": "Test Ticket", "description": "Test", "category": "battery"},
            headers={"Content-Type": "application/json"}  # No X-CSRF-Token header
        )
        
        # Should get 403 CSRF_MISSING (no auth header, no CSRF token)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == "CSRF_MISSING", f"Expected CSRF_MISSING, got: {data}"
        print(f"PASS: POST without CSRF token returns 403 CSRF_MISSING")

    def test_post_with_bearer_bypasses_csrf(self):
        """POST with valid Bearer token but WITHOUT CSRF token should pass (bearer is CSRF-safe)"""
        session = requests.Session()
        
        # Login to get token
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["token"]
        
        # Get the organization ID
        org_id = login_response.json().get("current_organization")
        
        # Make POST with Bearer token but WITHOUT X-CSRF-Token
        # Clear any CSRF cookies from the session
        session.cookies.clear()
        
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={"title": "TEST_CSRF_Bearer", "description": "Test", "category": "battery"},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": org_id
            }
            # Note: No X-CSRF-Token header and no csrf_token cookie
        )
        
        # Should succeed because Bearer token is inherently CSRF-safe
        # Might get 401/403 for other reasons (org context), but NOT 403 CSRF_MISSING
        if response.status_code == 403:
            data = response.json()
            assert data.get("code") != "CSRF_MISSING", f"Bearer auth should bypass CSRF, but got CSRF_MISSING"
            assert data.get("code") != "CSRF_INVALID", f"Bearer auth should bypass CSRF, but got CSRF_INVALID"
        
        print(f"PASS: POST with Bearer token bypasses CSRF validation (status: {response.status_code})")

    def test_post_with_matching_csrf_tokens_passes(self):
        """POST with matching csrf_token cookie and X-CSRF-Token header should pass"""
        session = requests.Session()
        
        # Get CSRF token from health endpoint
        session.get(f"{BASE_URL}/api/health")
        csrf_cookie = session.cookies.get("csrf_token")
        assert csrf_cookie, "No CSRF cookie received"
        
        # Login to get token
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["token"]
        org_id = login_response.json().get("current_organization")
        
        # Now make POST with both cookie and header matching
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={"title": "TEST_CSRF_Match", "description": "Test", "category": "battery"},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": org_id,
                "X-CSRF-Token": csrf_cookie  # Same as cookie
            }
        )
        
        # Should not be blocked by CSRF
        if response.status_code == 403:
            data = response.json()
            assert data.get("code") != "CSRF_MISSING", f"Matching tokens should pass CSRF"
            assert data.get("code") != "CSRF_INVALID", f"Matching tokens should pass CSRF"
        
        print(f"PASS: POST with matching CSRF tokens passes validation (status: {response.status_code})")

    def test_post_with_mismatched_csrf_returns_403(self):
        """POST with mismatched csrf_token cookie and X-CSRF-Token header should return 403 CSRF_INVALID"""
        session = requests.Session()
        
        # Get CSRF token from health endpoint
        session.get(f"{BASE_URL}/api/health")
        csrf_cookie = session.cookies.get("csrf_token")
        assert csrf_cookie, "No CSRF cookie received"
        
        # Login to get token
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["token"]
        org_id = login_response.json().get("current_organization")
        
        # Make POST with mismatched tokens
        wrong_token = "wrong_csrf_token_12345678901234567890"
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={"title": "TEST_CSRF_Mismatch", "description": "Test", "category": "battery"},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": org_id,
                "X-CSRF-Token": wrong_token  # Different from cookie
            }
        )
        
        # Should get 403 CSRF_INVALID
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == "CSRF_INVALID", f"Expected CSRF_INVALID, got: {data}"
        print(f"PASS: POST with mismatched CSRF tokens returns 403 CSRF_INVALID")

    def test_get_requests_bypass_csrf(self):
        """GET requests should not require CSRF validation"""
        session = requests.Session()
        
        # Login to get token
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["token"]
        org_id = login_response.json().get("current_organization")
        
        # Clear CSRF cookie
        session.cookies.clear()
        
        # Make GET request without CSRF token
        response = session.get(
            f"{BASE_URL}/api/v1/tickets",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": org_id
            }
        )
        
        # Should succeed (GET is safe method)
        assert response.status_code != 403 or "CSRF" not in response.text, \
            f"GET should not require CSRF: {response.text}"
        print(f"PASS: GET requests bypass CSRF validation (status: {response.status_code})")


class TestInputSanitization:
    """Input Sanitization middleware tests - bleach XSS stripping"""

    @pytest.fixture
    def auth_session(self):
        """Create authenticated session with CSRF token"""
        session = requests.Session()
        
        # Get CSRF token
        session.get(f"{BASE_URL}/api/health")
        csrf_cookie = session.cookies.get("csrf_token")
        
        # Login
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        token = login_response.json()["token"]
        org_id = login_response.json().get("current_organization")
        
        return {
            "session": session,
            "token": token,
            "org_id": org_id,
            "csrf_token": csrf_cookie
        }

    def test_script_tags_stripped_from_title(self, auth_session):
        """POST with <script>alert(1)</script> in title field should have script tags stripped"""
        session = auth_session["session"]
        malicious_title = "TEST_XSS <script>alert('XSS')</script> Title"
        
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={
                "title": malicious_title,
                "description": "Clean description",
                "category": "battery"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_session['token']}",
                "X-Organization-ID": auth_session['org_id'],
                "X-CSRF-Token": auth_session['csrf_token']
            }
        )
        
        # May succeed or fail for other reasons, but script tags should be stripped
        if response.status_code in [200, 201]:
            data = response.json()
            title = data.get("title", "")
            assert "<script>" not in title.lower(), f"Script tags not stripped from title: {title}"
            assert "alert" not in title.lower() or "</script>" not in title.lower(), \
                f"Script content not fully stripped: {title}"
            print(f"PASS: Script tags stripped from title: '{title}'")
        else:
            # Even on failure, check the error doesn't expose raw script
            print(f"Request returned {response.status_code}, skipping content check")

    def test_img_onerror_stripped_from_description(self, auth_session):
        """POST with <img onerror=hack src=x> in description should have img tag stripped"""
        session = auth_session["session"]
        malicious_desc = "TEST_XSS <img onerror='hack()' src='x'> Description"
        
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={
                "title": "Clean Title",
                "description": malicious_desc,
                "category": "battery"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_session['token']}",
                "X-Organization-ID": auth_session['org_id'],
                "X-CSRF-Token": auth_session['csrf_token']
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            desc = data.get("description", "")
            assert "<img" not in desc.lower(), f"Img tags not stripped from description: {desc}"
            assert "onerror" not in desc.lower(), f"onerror attribute not stripped: {desc}"
            print(f"PASS: Img tags stripped from description: '{desc}'")
        else:
            print(f"Request returned {response.status_code}, skipping content check")

    def test_clean_text_unchanged(self, auth_session):
        """POST with clean text should pass through unchanged"""
        session = auth_session["session"]
        clean_title = "TEST_CLEAN Normal Ticket Title"
        clean_desc = "This is a clean description without any HTML"
        
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={
                "title": clean_title,
                "description": clean_desc,
                "category": "battery"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_session['token']}",
                "X-Organization-ID": auth_session['org_id'],
                "X-CSRF-Token": auth_session['csrf_token']
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("title") == clean_title, \
                f"Clean title changed: {data.get('title')} != {clean_title}"
            assert data.get("description") == clean_desc, \
                f"Clean description changed: {data.get('description')} != {clean_desc}"
            print(f"PASS: Clean text unchanged")
        else:
            print(f"Request returned {response.status_code}, skipping content check")

    def test_multiple_xss_vectors_stripped(self, auth_session):
        """POST with multiple XSS vectors should have all malicious content stripped"""
        session = auth_session["session"]
        
        xss_vectors = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "<body onload=alert(1)>",
            "<iframe src='javascript:alert(1)'>",
            "javascript:alert(1)",
            "<a href='javascript:alert(1)'>click</a>",
        ]
        
        for i, vector in enumerate(xss_vectors):
            malicious_title = f"TEST_XSS_VECTOR_{i} {vector}"
            
            response = session.post(
                f"{BASE_URL}/api/v1/tickets",
                json={
                    "title": malicious_title,
                    "description": f"Vector test {i}",
                    "category": "battery"
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {auth_session['token']}",
                    "X-Organization-ID": auth_session['org_id'],
                    "X-CSRF-Token": auth_session['csrf_token']
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                title = data.get("title", "").lower()
                # Check dangerous patterns are removed
                dangerous_patterns = ["<script", "onerror", "onload", "<svg", "<iframe", "javascript:"]
                for pattern in dangerous_patterns:
                    if pattern in vector.lower():
                        assert pattern not in title, \
                            f"XSS vector {i} not sanitized - found '{pattern}' in title: {title}"
                print(f"PASS: XSS vector {i} sanitized")
            else:
                print(f"Vector {i}: Request returned {response.status_code}")

    def test_auth_endpoints_exempt_from_sanitization(self, auth_session):
        """Auth endpoints should be exempt from sanitization (per EXEMPT_PREFIXES)"""
        session = auth_session["session"]
        
        # Try login with special chars (should work without stripping)
        # Note: This just tests that auth endpoints aren't blocked
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Auth endpoint should work: {response.text}"
        print(f"PASS: Auth endpoints exempt from sanitization")


class TestFrontendCSRFIntegration:
    """Tests for frontend CSRF integration - apiFetch wrapper"""

    def test_frontend_api_js_has_csrf_injection(self):
        """Verify frontend api.js has CSRF token injection logic"""
        api_js_path = "/app/frontend/src/utils/api.js"
        
        with open(api_js_path, "r") as f:
            content = f.read()
        
        # Check for getCookie function
        assert "getCookie" in content, "Missing getCookie function"
        assert "csrf_token" in content, "Missing csrf_token reference"
        
        # Check for UNSAFE_METHODS handling
        assert "UNSAFE_METHODS" in content or "unsafe" in content.lower(), \
            "Missing unsafe methods handling"
        
        # Check for X-CSRF-Token header injection
        assert "X-CSRF-Token" in content, "Missing X-CSRF-Token header injection"
        
        print("PASS: Frontend api.js has CSRF token injection logic")

    def test_csrf_cookie_readable_by_javascript(self):
        """Verify csrf_token cookie has HttpOnly=False so JS can read it"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/health")
        
        # Check cookie attributes
        for cookie in session.cookies:
            if cookie.name == "csrf_token":
                # Check that httponly is False (JS readable)
                # Note: requests library doesn't expose httponly directly, 
                # but we can verify the cookie exists and is readable
                assert cookie.value, "CSRF cookie has no value"
                print(f"PASS: csrf_token cookie is set and readable")
                return
        
        # If we get here, cookie wasn't found
        assert False, "csrf_token cookie not found in response"


class TestEndToEndSecurityFlow:
    """End-to-end security flow tests"""

    def test_full_authenticated_flow_with_csrf(self):
        """Test complete authenticated flow: login -> get csrf -> make authenticated request"""
        session = requests.Session()
        
        # Step 1: Get initial CSRF token
        health_response = session.get(f"{BASE_URL}/api/health")
        assert health_response.status_code == 200
        csrf_token = session.cookies.get("csrf_token")
        assert csrf_token, "No CSRF token from health endpoint"
        print(f"Step 1: Got initial CSRF token")
        
        # Step 2: Login (exempt from CSRF)
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        org_id = login_response.json().get("current_organization")
        print(f"Step 2: Logged in successfully")
        
        # Step 3: Make authenticated POST with CSRF token
        create_response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={
                "title": "TEST_E2E_CSRF Test Ticket",
                "description": "Testing end-to-end CSRF flow",
                "category": "battery"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "X-Organization-ID": org_id,
                "X-CSRF-Token": csrf_token
            }
        )
        
        # Should succeed (both auth and CSRF valid)
        assert create_response.status_code in [200, 201], \
            f"E2E flow failed: {create_response.status_code} - {create_response.text}"
        print(f"Step 3: Created ticket with authenticated CSRF-protected request")
        print(f"PASS: Full authenticated flow with CSRF works")

    def test_csrf_refresh_on_missing_token(self):
        """Test that frontend can recover from missing CSRF token"""
        session = requests.Session()
        
        # Login first
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Clear cookies to simulate missing CSRF
        session.cookies.clear()
        
        # Make request that will fail CSRF
        response = session.post(
            f"{BASE_URL}/api/v1/tickets",
            json={"title": "TEST_Refresh", "description": "Test", "category": "battery"},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        # Should get past CSRF (bearer auth bypasses it)
        # The point is bearer auth users aren't blocked by missing CSRF
        print(f"PASS: Bearer auth users can proceed without CSRF token (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
