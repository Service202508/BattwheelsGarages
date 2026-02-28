"""
Test Data Management API endpoints
- Data counts
- Zoho connection test
- Sanitization (audit mode)
- Full sync trigger
- Cleanup operations (negative stock, orphaned records)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ORG_ID = "org_71f0df814d6d"

# Authentication
AUTH_EMAIL = "dev@battwheels.internal"
AUTH_PASSWORD = "DevTest@123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": AUTH_EMAIL,
        "password": AUTH_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Create headers with auth token and org ID"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "X-Organization-ID": ORG_ID
    }


class TestDataCounts:
    """Test GET /api/data-management/counts endpoint"""
    
    def test_get_data_counts_success(self, auth_headers):
        """Test retrieving data counts for all collections"""
        response = requests.get(f"{BASE_URL}/api/data-management/counts", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "code" in data
        assert data["code"] == 0
        assert "counts" in data
        
        counts = data["counts"]
        
        # Verify expected collections are present
        expected_collections = [
            "vehicles", "tickets", "work_orders", "items", "contacts",
            "invoices", "estimates", "bills", "expenses", "payments"
        ]
        
        for col in expected_collections:
            assert col in counts, f"Missing collection: {col}"
            assert "total" in counts[col]
            assert "zoho_synced" in counts[col]
            assert "local_only" in counts[col]
        
        print(f"SUCCESS: Retrieved counts for {len(counts)} collections")
        print(f"Sample counts - Items: {counts.get('items', {}).get('total', 0)}, Contacts: {counts.get('contacts', {}).get('total', 0)}")
    
    def test_get_data_counts_requires_org_id(self, auth_token):
        """Test that X-Organization-ID header is required"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(f"{BASE_URL}/api/data-management/counts", headers=headers)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("SUCCESS: Endpoint correctly requires X-Organization-ID header")


class TestZohoConnection:
    """Test Zoho Books connection endpoints"""
    
    def test_test_connection_success(self, auth_headers):
        """Test GET /api/data-management/sync/test-connection"""
        response = requests.get(f"{BASE_URL}/api/data-management/sync/test-connection", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "connection" in data
        
        connection = data["connection"]
        assert "status" in connection
        
        if connection["status"] == "connected":
            print(f"SUCCESS: Zoho Books connected to org: {connection.get('active_org', 'N/A')}")
            assert "token_valid" in connection
            assert connection["token_valid"] == True
        else:
            print(f"WARNING: Zoho Books not connected - {connection.get('error', 'Unknown error')}")
    
    def test_get_sync_status(self, auth_headers):
        """Test GET /api/data-management/sync/status"""
        response = requests.get(f"{BASE_URL}/api/data-management/sync/status", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "status" in data
        
        status = data["status"]
        print(f"SUCCESS: Retrieved sync status - Organization: {status.get('organization_id', 'N/A')}")


class TestSanitization:
    """Test data sanitization endpoints"""
    
    def test_sanitization_audit_mode(self, auth_headers):
        """Test POST /api/data-management/sanitize with mode=audit"""
        response = requests.post(
            f"{BASE_URL}/api/data-management/sanitize",
            headers=auth_headers,
            json={"mode": "audit"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "report" in data
        
        report = data["report"]
        
        # Verify report structure
        assert "job_id" in report
        assert "organization_id" in report
        assert "status" in report
        assert "mode" in report
        assert report["mode"] == "audit"
        assert "total_records_scanned" in report
        assert "total_test_records" in report
        assert "results" in report
        
        print(f"SUCCESS: Audit completed - Job ID: {report['job_id']}")
        print(f"Records scanned: {report['total_records_scanned']}")
        print(f"Test records found: {report['total_test_records']}")
        
        # Verify results breakdown
        if report["results"]:
            print(f"Collections processed: {len(report['results'])}")
            for result in report["results"][:3]:  # Show first 3
                print(f"  - {result['collection']}: {result['test_records_found']} test records")
    
    def test_sanitization_invalid_mode(self, auth_headers):
        """Test sanitization with invalid mode returns error"""
        response = requests.post(
            f"{BASE_URL}/api/data-management/sanitize",
            headers=auth_headers,
            json={"mode": "invalid_mode"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("SUCCESS: Invalid mode correctly rejected")


class TestFullSync:
    """Test full sync endpoint"""
    
    def test_full_sync_starts_background_job(self, auth_headers):
        """Test POST /api/data-management/sync/full starts a background job"""
        response = requests.post(f"{BASE_URL}/api/data-management/sync/full", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "message" in data
        assert "sync_id" in data
        
        print(f"SUCCESS: Full sync started - Sync ID: {data['sync_id']}")
        print(f"Message: {data['message']}")


class TestCleanupOperations:
    """Test cleanup endpoints"""
    
    def test_fix_negative_stock(self, auth_headers):
        """Test POST /api/data-management/cleanup/negative-stock"""
        response = requests.post(f"{BASE_URL}/api/data-management/cleanup/negative-stock", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "message" in data
        
        print(f"SUCCESS: Negative stock fix - {data['message']}")
    
    def test_cleanup_orphaned_records(self, auth_headers):
        """Test POST /api/data-management/cleanup/orphaned-records"""
        response = requests.post(f"{BASE_URL}/api/data-management/cleanup/orphaned-records", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "cleaned" in data
        
        cleaned = data["cleaned"]
        print(f"SUCCESS: Orphaned records cleanup - {cleaned}")


class TestSyncModule:
    """Test individual module sync"""
    
    def test_sync_single_module(self, auth_headers):
        """Test POST /api/data-management/sync/module for contacts"""
        response = requests.post(
            f"{BASE_URL}/api/data-management/sync/module",
            headers=auth_headers,
            json={"module": "contacts", "full_sync": False}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "result" in data
        
        result = data["result"]
        print(f"SUCCESS: Module sync - Status: {result.get('status', 'unknown')}")
        if result.get("records_synced"):
            print(f"Records synced: {result['records_synced']}")


class TestValidation:
    """Test data validation endpoints"""
    
    def test_validate_integrity(self, auth_headers):
        """Test GET /api/data-management/validate/integrity"""
        response = requests.get(f"{BASE_URL}/api/data-management/validate/integrity", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "validation" in data
        
        validation = data["validation"]
        print(f"SUCCESS: Integrity validation - Status: {validation.get('status', 'unknown')}")
        print(f"Total issues: {validation.get('total_issues', 0)}")
    
    def test_validate_completeness(self, auth_headers):
        """Test GET /api/data-management/validate/completeness"""
        response = requests.get(f"{BASE_URL}/api/data-management/validate/completeness", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "validation" in data
        
        validation = data["validation"]
        print(f"SUCCESS: Completeness validation - Status: {validation.get('status', 'unknown')}")
        print(f"Total issues: {validation.get('total_issues', 0)}")


class TestSanitizationHistory:
    """Test sanitization history and status endpoints"""
    
    def test_get_sanitization_history(self, auth_headers):
        """Test GET /api/data-management/sanitize/history"""
        response = requests.get(f"{BASE_URL}/api/data-management/sanitize/history", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "jobs" in data
        
        print(f"SUCCESS: Retrieved {len(data['jobs'])} sanitization job(s) from history")
    
    def test_get_sync_history(self, auth_headers):
        """Test GET /api/data-management/sync/history"""
        response = requests.get(f"{BASE_URL}/api/data-management/sync/history", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "code" in data
        assert data["code"] == 0
        assert "history" in data
        
        print(f"SUCCESS: Retrieved {len(data['history'])} sync job(s) from history")
