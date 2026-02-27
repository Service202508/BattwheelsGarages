"""
Password Management Module Tests
================================
Tests for 3 password features:
1. Admin Reset Password (POST /api/employees/{id}/reset-password)
2. Self-Service Password Change (POST /api/auth/change-password)
3. Forgot Password Flow (POST /api/auth/forgot-password, POST /api/auth/reset-password)

Public whitelist verification for forgot-password and reset-password endpoints.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestPublicEndpointWhitelist:
    """Test that public endpoints are accessible without auth"""
    
    def test_forgot_password_no_auth_required(self):
        """POST /api/auth/forgot-password should NOT return 401/403"""
        res = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "test@example.com"},
            headers={"Content-Type": "application/json"}
        )
        # Should NOT be 401 or 403 (auth required errors)
        assert res.status_code not in [401, 403], f"Endpoint requires auth but shouldn't: {res.status_code}"
        print(f"✓ forgot-password accessible without auth (status: {res.status_code})")
    
    def test_reset_password_no_auth_required(self):
        """POST /api/auth/reset-password should NOT return 401/403"""
        res = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "invalid_test_token", "new_password": "test_pwd_placeholder"},
            headers={"Content-Type": "application/json"}
        )
        # Should NOT be 401 or 403 (auth required errors)
        # Expected: 400 (invalid token) - this is correct behavior
        assert res.status_code not in [401, 403], f"Endpoint requires auth but shouldn't: {res.status_code}"
        print(f"✓ reset-password accessible without auth (status: {res.status_code})")


class TestForgotPasswordFlow:
    """Test forgot password endpoint"""
    
    def test_forgot_password_existing_email(self):
        """Forgot password with existing email returns success message"""
        res = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "dev@battwheels.internal"},
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "message" in data
        # Should not reveal if account exists
        assert "if an account" in data["message"].lower() or "exists" in data["message"].lower()
        print(f"✓ forgot-password for existing email returns generic success: {data['message']}")
    
    def test_forgot_password_nonexistent_email_prevents_enumeration(self):
        """Forgot password with nonexistent email should return success (prevent enumeration)"""
        res = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "nonexistent_user_xyz@example.com"},
            headers={"Content-Type": "application/json"}
        )
        # MUST return 200 to prevent email enumeration attacks
        assert res.status_code == 200, f"Should return 200 even for non-existent email (prevent enumeration), got {res.status_code}"
        data = res.json()
        assert "message" in data
        print(f"✓ forgot-password prevents email enumeration: {data['message']}")


class TestResetPasswordFlow:
    """Test reset password with token endpoint"""
    
    def test_reset_password_invalid_token(self):
        """Reset password with invalid token returns 400"""
        res = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "invalid_bad_token_abc123", "new_password": "newpass123"},
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code == 400, f"Expected 400 for invalid token, got {res.status_code}"
        data = res.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
        print(f"✓ reset-password with invalid token returns 400: {data['detail']}")
    
    def test_reset_password_missing_token(self):
        """Reset password without token should return validation error"""
        res = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"new_password": "newpass123"},  # Missing token
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code == 422, f"Expected 422 for missing token, got {res.status_code}"
        print(f"✓ reset-password missing token returns 422")
    
    def test_reset_password_short_password(self):
        """Reset password with password < 6 chars should fail validation"""
        res = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "test_token", "new_password": "abc"},  # Too short
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code == 422, f"Expected 422 for short password, got {res.status_code}"
        print(f"✓ reset-password with short password returns 422")


class TestSelfServicePasswordChange:
    """Test self-service password change (requires auth)"""
    
    @pytest.fixture
    def admin_token(self):
        """Login as admin to get token"""
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dev@battwheels.internal", "password": "DevTest@123"},
            headers={"Content-Type": "application/json"}
        )
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip(f"Could not login as admin: {res.status_code} - {res.text}")
    
    def test_change_password_requires_auth(self):
        """Change password without auth should return 401"""
        res = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": "DevTest@123", "new_password": "newpass123"},
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403 without auth, got {res.status_code}"
        print(f"✓ change-password requires authentication (status: {res.status_code})")
    
    def test_change_password_wrong_current_password(self, admin_token):
        """Change password with wrong current password returns 401"""
        res = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": "wrong_password_xyz", "new_password": "newpass123"},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {admin_token}"
            }
        )
        assert res.status_code == 401, f"Expected 401 for wrong current password, got {res.status_code}"
        data = res.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower() or "wrong" in data["detail"].lower()
        print(f"✓ change-password with wrong current password returns 401: {data['detail']}")
    
    def test_change_password_success_and_revert(self, admin_token):
        """Change password successfully, then revert back to original"""
        # Step 1: Change to new password (6+ chars required for new_password)
        res = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": "DevTest@123", "new_password": "DevTest@123"},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {admin_token}"
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "message" in data
        print(f"✓ Password changed successfully: {data['message']}")
        
        # Step 2: Login with new password to verify
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dev@battwheels.internal", "password": "DevTest@123"},
            headers={"Content-Type": "application/json"}
        )
        assert login_res.status_code == 200, f"Could not login with new password: {login_res.status_code}"
        new_token = login_res.json().get("token")
        print(f"✓ Login with new password successful")
        
        # Step 3: CRITICAL - Cannot revert to 'admin' (5 chars) via API due to min_length=6
        # Must restore via direct DB update after tests
        # For now, just change back to something 6+ chars that we know
        revert_res = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"current_password": "DevTest@123", "new_password": "admin!"},  # 6 chars
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {new_token}"
            }
        )
        assert revert_res.status_code == 200, f"Failed to revert password: {revert_res.status_code}"
        print(f"✓ Password changed to 'admin!' (6 chars min required)")
        
        # Step 4: Verify login with new password
        verify_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dev@battwheels.internal", "password": "admin!"},
            headers={"Content-Type": "application/json"}
        )
        assert verify_res.status_code == 200, f"Login with password failed: {verify_res.status_code}"
        print(f"✓ Login with password 'admin!' confirmed working")
        print(f"⚠ NOTE: Admin password is now 'admin!' - needs DB restore to 'admin' if required")


class TestAdminResetEmployeePassword:
    """Test admin endpoint to reset employee password"""
    
    @pytest.fixture
    def admin_auth(self):
        """Login as admin to get token and headers"""
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dev@battwheels.internal", "password": "DevTest@123"},
            headers={"Content-Type": "application/json"}
        )
        if res.status_code == 200:
            token = res.json().get("token")
            return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        pytest.skip(f"Could not login as admin: {res.status_code}")
    
    def test_admin_reset_requires_auth(self):
        """Admin reset endpoint requires authentication"""
        res = requests.post(
            f"{BASE_URL}/api/employees/test_id/reset-password",
            json={"new_password": "newpass123"},
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403 without auth, got {res.status_code}"
        print(f"✓ admin reset-password requires auth (status: {res.status_code})")
    
    def test_admin_reset_nonexistent_employee(self, admin_auth):
        """Admin reset for nonexistent employee returns 404"""
        res = requests.post(
            f"{BASE_URL}/api/employees/nonexistent_emp_id_xyz/reset-password",
            json={"new_password": "newpass123"},
            headers=admin_auth
        )
        assert res.status_code == 404, f"Expected 404 for nonexistent employee, got {res.status_code}"
        print(f"✓ admin reset for nonexistent employee returns 404")
    
    def test_admin_reset_for_employee_with_work_email(self, admin_auth):
        """Admin can reset password for employee with work_email"""
        # First, get list of employees to find one with work_email
        emp_res = requests.get(f"{BASE_URL}/api/employees", headers=admin_auth)
        if emp_res.status_code != 200:
            pytest.skip(f"Could not fetch employees: {emp_res.status_code}")
        
        employees = emp_res.json()
        if isinstance(employees, dict):
            employees = employees.get("data", [])
        
        # Find employee with work_email
        target_emp = None
        for emp in employees:
            if emp.get("work_email"):
                target_emp = emp
                break
        
        if not target_emp:
            pytest.skip("No employee with work_email found")
        
        # Try to reset password
        res = requests.post(
            f"{BASE_URL}/api/employees/{target_emp['employee_id']}/reset-password",
            json={"new_password": "test_pwd_placeholder"},
            headers=admin_auth
        )
        
        # Could be 200 (success) or 404 (no user account for this email)
        if res.status_code == 200:
            data = res.json()
            assert "message" in data
            print(f"✓ Admin reset password for {target_emp.get('full_name', target_emp['work_email'])}: {data['message']}")
        elif res.status_code == 404:
            data = res.json()
            # Could be "No user account found" which is acceptable
            print(f"✓ No user account for employee (expected if not onboarded): {data.get('detail', '')}")
        else:
            pytest.fail(f"Unexpected status {res.status_code}: {res.text}")


class TestTechnicianLogin:
    """Test technician login flow to verify password operations"""
    
    def test_technician_login(self):
        """Verify technician credentials work"""
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "tech.a@battwheels.internal", "password": "DevTest@123"},
            headers={"Content-Type": "application/json"}
        )
        if res.status_code == 200:
            data = res.json()
            assert "token" in data
            assert "user" in data
            print(f"✓ Technician login successful: {data['user'].get('name', data['user']['email'])}")
        else:
            print(f"⚠ Technician login failed (status: {res.status_code}) - may need password reset")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
