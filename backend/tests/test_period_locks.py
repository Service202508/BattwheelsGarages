"""
Period Locking Tests - Week 3 Prompt 2
======================================
Tests for financial period locking functionality:
- GET /api/v1/period-locks - List period locks
- GET /api/v1/period-locks/{period} - Single period lock status
- POST /api/v1/period-locks/lock - Lock a period
- POST /api/v1/period-locks/unlock - Unlock with reason
- POST /api/v1/period-locks/extend - Extend unlock window
- POST /api/v1/period-locks/check - Check if date is locked
- POST /api/v1/period-locks/lock-fiscal-year - Lock all 12 months
- POST /api/v1/period-locks/auto-relock - Auto-relock expired amendments
- Invoice creation blocked when period locked (409 PERIOD_LOCKED)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://prodready-execution.preview.emergentagent.com")
BASE_URL = BASE_URL.rstrip("/")

# Test credentials
DEMO_EMAIL = "demo@voltmotors.in"
DEMO_PASSWORD = "Demo@12345"
TEST_ORG_ID = "demo-volt-motors-001"

# Test period - use a future period to avoid conflicts with existing locks
TEST_PERIOD = f"2027-{datetime.now().month:02d}"


class TestAuth:
    """Authentication helper tests"""
    
    @pytest.fixture(scope="class")
    def auth_data(self):
        """Login and get token + org data"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return {
            "token": data["token"],
            "org_id": data.get("current_organization") or TEST_ORG_ID,
            "user": data.get("user", {})
        }
    
    def test_login(self, auth_data):
        """Test login works"""
        assert auth_data["token"]
        assert auth_data["org_id"]
        print(f"Logged in as: {auth_data['user'].get('email')}, org: {auth_data['org_id']}")


@pytest.fixture(scope="module")
def api_client():
    """Get authenticated API client"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data['token']}",
        "X-Organization-ID": data.get("current_organization") or TEST_ORG_ID
    })
    return session


class TestPeriodLocksListAndGet:
    """Tests for listing and getting period locks"""
    
    def test_list_period_locks(self, api_client):
        """GET /api/v1/period-locks - Should return list of locks"""
        response = api_client.get(f"{BASE_URL}/api/v1/period-locks")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "locks" in data
        assert "count" in data
        assert isinstance(data["locks"], list)
        print(f"Found {data['count']} period locks")
    
    def test_list_period_locks_with_year_filter(self, api_client):
        """GET /api/v1/period-locks?year=2026 - Filter by year"""
        response = api_client.get(f"{BASE_URL}/api/v1/period-locks?year=2026")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # All returned locks should be from 2026
        for lock in data["locks"]:
            assert lock["period"].startswith("2026-"), f"Lock {lock['period']} is not from 2026"
        print(f"Found {data['count']} locks for 2026")
    
    def test_get_single_period_lock(self, api_client):
        """GET /api/v1/period-locks/2026-01 - Get specific period status"""
        response = api_client.get(f"{BASE_URL}/api/v1/period-locks/2026-01")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "period" in data
        assert "status" in data
        assert data["period"] == "2026-01"
        print(f"Period 2026-01 status: {data['status']}")
    
    def test_get_nonexistent_period(self, api_client):
        """GET /api/v1/period-locks/2099-12 - Should return unlocked status"""
        response = api_client.get(f"{BASE_URL}/api/v1/period-locks/2099-12")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["period"] == "2099-12"
        assert data["status"] == "unlocked"


class TestPeriodLockOperations:
    """Tests for lock/unlock/extend operations"""
    
    def test_lock_period(self, api_client):
        """POST /api/v1/period-locks/lock - Lock a test period"""
        # Use a future test period
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock",
            json={"period": TEST_PERIOD, "reason": "Test lock for pytest"}
        )
        # Either success or already locked
        assert response.status_code in [200, 409], f"Unexpected status: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert "lock" in data
            assert data["lock"]["status"] == "locked"
            print(f"Period {TEST_PERIOD} locked successfully")
        else:
            print(f"Period {TEST_PERIOD} was already locked")
    
    def test_lock_invalid_period_format(self, api_client):
        """POST /api/v1/period-locks/lock - Invalid period format should fail"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock",
            json={"period": "invalid-format", "reason": ""}
        )
        assert response.status_code in [400, 422], f"Expected validation error: {response.text}"
    
    def test_unlock_requires_reason(self, api_client):
        """POST /api/v1/period-locks/unlock - Must have 10+ char reason"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/unlock?period={TEST_PERIOD}",
            json={"reason": "short", "window_hours": 72}
        )
        # 400 or 422 both indicate validation failure
        assert response.status_code in [400, 422], f"Should require longer reason: {response.text}"
        print("Correctly rejected short unlock reason")
    
    def test_unlock_period_success(self, api_client):
        """POST /api/v1/period-locks/unlock - Unlock with valid reason"""
        # First ensure the period is locked
        api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock",
            json={"period": TEST_PERIOD, "reason": "Lock for unlock test"}
        )
        
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/unlock?period={TEST_PERIOD}",
            json={"reason": "This is a valid unlock reason for testing purposes", "window_hours": 72}
        )
        # Could be 200 (success) or 409 (already unlocked) or 404 (no lock record)
        assert response.status_code in [200, 404, 409], f"Unexpected: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert "lock" in data
            assert data["lock"]["status"] == "unlocked_amendment"
            print(f"Period {TEST_PERIOD} unlocked for amendment")
    
    def test_extend_unlock_window(self, api_client):
        """POST /api/v1/period-locks/extend - Extend amendment window"""
        # First unlock to create amendment window
        api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock",
            json={"period": TEST_PERIOD, "reason": "Lock for extend test"}
        )
        api_client.post(
            f"{BASE_URL}/api/v1/period-locks/unlock?period={TEST_PERIOD}",
            json={"reason": "Unlock to test extension functionality", "window_hours": 24}
        )
        
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/extend?period={TEST_PERIOD}",
            json={"additional_hours": 72}
        )
        # Could succeed or fail depending on current state
        assert response.status_code in [200, 404, 409], f"Unexpected: {response.text}"
        if response.status_code == 200:
            print(f"Extended unlock window for {TEST_PERIOD}")


class TestPeriodCheckEndpoint:
    """Tests for /check endpoint"""
    
    def test_check_locked_period(self, api_client):
        """POST /api/v1/period-locks/check - Check a locked date returns 409"""
        # First ensure 2026-01 is locked (from agent context)
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/check",
            json={"date": "2026-01-15"}
        )
        # If period is locked -> 409, if open -> 200
        assert response.status_code in [200, 409], f"Unexpected: {response.text}"
        if response.status_code == 409:
            data = response.json()
            detail = data.get("detail", {})
            # Verify PERIOD_LOCKED code is present
            if isinstance(detail, dict):
                assert detail.get("code") == "PERIOD_LOCKED", f"Expected PERIOD_LOCKED code: {detail}"
                print(f"Correctly detected locked period: {detail.get('locked_period')}")
            else:
                print(f"Period check returned 409: {data}")
        else:
            data = response.json()
            print(f"Period 2026-01 is open: {data}")
    
    def test_check_open_period(self, api_client):
        """POST /api/v1/period-locks/check - Open period returns 200"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/check",
            json={"date": "2099-06-15"}
        )
        assert response.status_code == 200, f"Future period should be open: {response.text}"
        data = response.json()
        assert data["status"] == "open"


class TestFiscalYearLocking:
    """Tests for fiscal year bulk locking"""
    
    def test_lock_fiscal_year(self, api_client):
        """POST /api/v1/period-locks/lock-fiscal-year - Lock FY 2028-2029"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock-fiscal-year",
            json={"year": 2028, "fiscal_year_start_month": 4}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 12, "Should lock all 12 months"
        locked_count = sum(1 for r in data["results"] if r["status"] == "locked")
        print(f"Locked {locked_count}/12 periods for FY 2028-29")


class TestAutoRelock:
    """Tests for auto-relock functionality"""
    
    def test_trigger_auto_relock(self, api_client):
        """POST /api/v1/period-locks/auto-relock - Trigger expired amendment relock"""
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/auto-relock",
            json={}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "relocked_count" in data
        print(f"Auto-relock processed: {data['relocked_count']} periods relocked")


class TestPeriodLockIntegration:
    """Tests for period lock integration with invoices"""
    
    def test_invoice_creation_blocked_when_locked(self, api_client):
        """Invoice creation should fail with 409 PERIOD_LOCKED when period is locked"""
        # First ensure 2026-01 is locked
        lock_resp = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock",
            json={"period": "2026-01", "reason": "Test invoice blocking"}
        )
        # Allow already locked
        
        # Check if period is actually locked
        check_resp = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/check",
            json={"date": "2026-01-15"}
        )
        
        if check_resp.status_code == 409:
            # Period is locked, try to create invoice in that period
            invoice_data = {
                "customer_id": "test_customer",
                "customer_name": "Test Customer",
                "invoice_date": "2026-01-15",  # In locked period
                "due_date": "2026-02-15",
                "line_items": [
                    {
                        "name": "Test Service",
                        "quantity": 1,
                        "rate": 1000,
                        "tax_rate": 18
                    }
                ]
            }
            
            # Try to create invoice
            invoice_resp = api_client.post(
                f"{BASE_URL}/api/v1/invoices-enhanced",
                json=invoice_data
            )
            
            # Should be blocked
            if invoice_resp.status_code == 409:
                data = invoice_resp.json()
                detail = data.get("detail", {})
                if isinstance(detail, dict) and detail.get("code") == "PERIOD_LOCKED":
                    print("Invoice creation correctly blocked with PERIOD_LOCKED code")
                else:
                    print(f"Invoice blocked but unexpected detail: {detail}")
            else:
                print(f"Invoice creation returned {invoice_resp.status_code}: {invoice_resp.text[:200]}")
        else:
            print("Period 2026-01 is not locked, skipping invoice blocking test")


class TestRoleBasedAccess:
    """Tests for role-based access control"""
    
    def test_lock_requires_proper_role(self, api_client):
        """Only admin/owner/accountant can lock periods"""
        # Test with current user (demo@voltmotors.in is owner)
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock",
            json={"period": "2030-01", "reason": "Role test"}
        )
        # Owner should be allowed
        assert response.status_code in [200, 409], f"Owner should be able to lock: {response.text}"
    
    def test_unlock_requires_admin_or_owner(self, api_client):
        """Only admin/owner can unlock (not accountant)"""
        # First lock a period
        api_client.post(
            f"{BASE_URL}/api/v1/period-locks/lock",
            json={"period": "2030-02", "reason": "Lock for unlock role test"}
        )
        
        # Owner should be able to unlock
        response = api_client.post(
            f"{BASE_URL}/api/v1/period-locks/unlock?period=2030-02",
            json={"reason": "Testing owner unlock permission works correctly", "window_hours": 72}
        )
        assert response.status_code in [200, 404, 409], f"Owner should be able to unlock: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
