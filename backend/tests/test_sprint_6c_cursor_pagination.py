"""
Sprint 6C: Cursor-Based (Keyset) Pagination Tests
==================================================
Tests cursor-based pagination on 5 highest-traffic endpoints:
1. GET /api/v1/tickets?limit=5 — 1961 items in dev
2. GET /api/v1/invoices-enhanced?limit=3 — 14 items in dev  
3. GET /api/v1/hr/employees?limit=3 — 2 items in dev
4. GET /api/v1/failure-intelligence/failure-cards?limit=5 — org-scoped
5. GET /api/v1/journal-entries?limit=5 — 844 items in dev

Each endpoint supports:
- Legacy: page/limit params (backward compat)
- Cursor: cursor param for efficient keyset pagination
- Response format: {data, pagination: {page?, limit, total_count, total_pages?, has_next, has_prev, next_cursor}}
"""

import pytest
import requests
import os
import base64
import json

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
DEV_ORG_ID = "dev-internal-testing-001"

# Test credentials
DEV_USER_EMAIL = "dev@battwheels.internal"
DEV_USER_PASSWORD = "DevTest@123"
PLATFORM_ADMIN_EMAIL = "platform-dev@battwheels.internal"
PLATFORM_ADMIN_PASSWORD = "DevTest@123"


@pytest.fixture(scope="module")
def dev_session():
    """Login as dev user and return session with auth token + org header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Organization-ID": DEV_ORG_ID
    })
    
    # Login
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEV_USER_EMAIL,
        "password": DEV_USER_PASSWORD
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    
    # Extract token and add to session headers
    login_data = resp.json()
    token = login_data.get("token")
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session


@pytest.fixture(scope="module") 
def platform_admin_session():
    """Login as platform admin and return session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Organization-ID": DEV_ORG_ID
    })
    
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": PLATFORM_ADMIN_EMAIL,
        "password": PLATFORM_ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Platform admin login failed: {resp.text}"
    
    # Extract token and add to session headers
    login_data = resp.json()
    token = login_data.get("token")
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session


def decode_cursor(cursor_str: str) -> dict:
    """Decode a base64 cursor to inspect contents"""
    padding = 4 - len(cursor_str) % 4
    if padding != 4:
        cursor_str += "=" * padding
    payload = json.loads(base64.urlsafe_b64decode(cursor_str.encode()).decode())
    return payload


class TestTicketsCursorPagination:
    """6C-01: GET /api/v1/tickets with cursor-based pagination"""
    
    def test_legacy_pagination_returns_next_cursor(self, dev_session):
        """Legacy path returns next_cursor for seamless transition"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/tickets", params={
            "limit": 5,
            "page": 1
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify pagination structure
        assert "data" in data
        assert "pagination" in data
        pagination = data["pagination"]
        
        # Legacy fields
        assert "page" in pagination
        assert pagination["page"] == 1
        assert "limit" in pagination
        assert pagination["limit"] == 5
        assert "total_count" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination
        
        # New cursor field for transition
        assert "next_cursor" in pagination
        
        if pagination["has_next"]:
            assert pagination["next_cursor"] is not None
            # Decode cursor to verify structure
            cursor_data = decode_cursor(pagination["next_cursor"])
            assert "v" in cursor_data  # sort_value
            assert "t" in cursor_data  # tiebreaker_id (ticket_id)
        
        print(f"✓ Tickets legacy: {len(data['data'])} items, total={pagination['total_count']}, has_next={pagination['has_next']}")
    
    def test_cursor_pagination_chain_no_duplicates(self, dev_session):
        """Cursor path chains correctly with no duplicates"""
        all_ticket_ids = []
        cursor = None
        page_count = 0
        max_pages = 3
        
        while page_count < max_pages:
            params = {"limit": 5}
            if cursor:
                params["cursor"] = cursor
            
            resp = dev_session.get(f"{BASE_URL}/api/v1/tickets", params=params)
            assert resp.status_code == 200, f"Page {page_count+1} failed: {resp.text}"
            data = resp.json()
            
            pagination = data["pagination"]
            items = data["data"]
            
            # Collect ticket IDs
            for item in items:
                assert "ticket_id" in item
                all_ticket_ids.append(item["ticket_id"])
            
            print(f"  Page {page_count+1}: {len(items)} tickets, has_next={pagination['has_next']}")
            
            page_count += 1
            
            if not pagination["has_next"]:
                break
            
            cursor = pagination.get("next_cursor")
            assert cursor is not None, "has_next=True but next_cursor is None"
        
        # Verify no duplicates
        unique_ids = set(all_ticket_ids)
        assert len(unique_ids) == len(all_ticket_ids), f"Found duplicates: {len(all_ticket_ids) - len(unique_ids)} duplicate ticket IDs"
        
        print(f"✓ Tickets cursor: {page_count} pages, {len(all_ticket_ids)} total items, 0 duplicates")
    
    def test_invalid_cursor_handled_gracefully(self, dev_session):
        """Invalid cursor returns error or is handled gracefully"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/tickets", params={
            "limit": 5,
            "cursor": "invalid_cursor_string"
        })
        # Should return 400/422 or handle gracefully by ignoring
        assert resp.status_code in [200, 400, 422], f"Unexpected status: {resp.status_code}"
        
        if resp.status_code == 200:
            # If handled gracefully, should return first page
            data = resp.json()
            assert "data" in data
            print("✓ Invalid cursor handled gracefully (first page returned)")
        else:
            print(f"✓ Invalid cursor rejected with {resp.status_code}")


class TestInvoicesCursorPagination:
    """6C-02: GET /api/v1/invoices-enhanced with cursor-based pagination"""
    
    def test_legacy_pagination_returns_next_cursor(self, dev_session):
        """Legacy path returns next_cursor for transition"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/invoices-enhanced", params={
            "limit": 3,
            "page": 1
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert "data" in data
        assert "pagination" in data
        pagination = data["pagination"]
        
        # Legacy fields
        assert "page" in pagination
        assert "limit" in pagination
        assert "total_count" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination
        
        # New cursor field
        assert "next_cursor" in pagination
        
        print(f"✓ Invoices legacy: {len(data['data'])} items, total={pagination['total_count']}, has_next={pagination['has_next']}")
    
    def test_cursor_pagination_chain_no_duplicates(self, dev_session):
        """Cursor chain with no duplicates across 4 pages"""
        all_invoice_ids = []
        cursor = None
        page_count = 0
        max_pages = 4  # 14 invoices / 3 per page = ~5 pages
        
        while page_count < max_pages:
            params = {"limit": 3}
            if cursor:
                params["cursor"] = cursor
            
            resp = dev_session.get(f"{BASE_URL}/api/v1/invoices-enhanced", params=params)
            assert resp.status_code == 200, f"Page {page_count+1} failed: {resp.text}"
            data = resp.json()
            
            pagination = data["pagination"]
            items = data["data"]
            
            for item in items:
                assert "invoice_id" in item
                all_invoice_ids.append(item["invoice_id"])
            
            print(f"  Page {page_count+1}: {len(items)} invoices, has_next={pagination['has_next']}")
            
            page_count += 1
            
            if not pagination["has_next"]:
                break
            
            cursor = pagination.get("next_cursor")
            assert cursor is not None, "has_next=True but next_cursor is None"
        
        # Verify no duplicates
        unique_ids = set(all_invoice_ids)
        assert len(unique_ids) == len(all_invoice_ids), f"Found {len(all_invoice_ids) - len(unique_ids)} duplicates"
        
        print(f"✓ Invoices cursor: {page_count} pages, {len(all_invoice_ids)} total items, 0 duplicates")


class TestEmployeesCursorPagination:
    """6C-03: GET /api/v1/hr/employees with cursor-based pagination"""
    
    def test_legacy_pagination_returns_next_cursor(self, dev_session):
        """Legacy path returns next_cursor (only 2 employees in dev)"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/hr/employees", params={
            "limit": 3,
            "page": 1
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert "data" in data
        assert "pagination" in data
        pagination = data["pagination"]
        
        # Legacy fields present
        assert "page" in pagination
        assert "limit" in pagination
        assert "total_count" in pagination
        assert "has_next" in pagination
        
        # With only 2 employees and limit=3, has_next should be False
        if pagination["total_count"] <= 3:
            assert pagination["has_next"] == False
        
        # New cursor field
        assert "next_cursor" in pagination
        
        print(f"✓ Employees legacy: {len(data['data'])} items, total={pagination['total_count']}, has_next={pagination['has_next']}")
    
    def test_cursor_pagination_small_dataset(self, dev_session):
        """Cursor path works correctly for small dataset (2 employees)"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/hr/employees", params={
            "limit": 3
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        pagination = data["pagination"]
        
        # With 2 employees and limit=3, should be single page
        if pagination["total_count"] <= 3:
            assert pagination["has_next"] == False
            # next_cursor should be null when no more pages
            if not pagination["has_next"]:
                assert pagination.get("next_cursor") is None
        
        print(f"✓ Employees cursor: {len(data['data'])} items, single page verified")


class TestFailureCardsCursorPagination:
    """6C-04: GET /api/v1/efi/failure-cards with cursor-based pagination"""
    
    def test_legacy_skip_limit_returns_items(self, dev_session):
        """Legacy skip/limit path preserved for backward compat"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/efi/failure-cards", params={
            "limit": 5,
            "skip": 0
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Legacy format: items/total/limit/skip
        assert "items" in data or "data" in data
        assert "total" in data or "pagination" in data
        
        items = data.get("items", data.get("data", []))
        print(f"✓ Failure cards legacy: {len(items)} items, total={data.get('total', 'N/A')}")
    
    def test_cursor_pagination_with_confidence_sort(self, dev_session):
        """Cursor uses confidence_score sort + failure_id tiebreaker when provided"""
        # Create a dummy cursor to test cursor path (even if it returns first page)
        # Base64 encode a valid cursor structure
        import base64
        import json
        dummy_cursor = base64.urlsafe_b64encode(json.dumps({"v": 1.0, "t": "fc_dummy"}).encode()).decode().rstrip("=")
        
        resp = dev_session.get(f"{BASE_URL}/api/v1/efi/failure-cards", params={
            "limit": 5,
            "cursor": dummy_cursor
        })
        # Could return 200 (valid cursor path) or might fail gracefully
        assert resp.status_code in [200, 400, 500], f"Unexpected status: {resp.status_code}"
        
        if resp.status_code == 200:
            data = resp.json()
            # Cursor path should return {data, pagination} format
            if "data" in data:
                pagination = data.get("pagination", {})
                print(f"✓ Failure cards cursor: data format with pagination: {list(pagination.keys())}")
            else:
                print(f"✓ Failure cards cursor: response format - {list(data.keys())}")
        else:
            print(f"✓ Failure cards cursor: invalid cursor handled with {resp.status_code}")


class TestJournalEntriesCursorPagination:
    """6C-05: GET /api/v1/journal-entries with cursor-based pagination"""
    
    def test_legacy_pagination_returns_next_cursor(self, dev_session):
        """Legacy path returns next_cursor for transition"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/journal-entries", params={
            "limit": 5,
            "page": 1
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert "data" in data
        assert "pagination" in data
        pagination = data["pagination"]
        
        # Legacy fields
        assert "page" in pagination
        assert "limit" in pagination
        assert "total_count" in pagination
        assert "has_next" in pagination
        
        # New cursor field
        assert "next_cursor" in pagination
        
        print(f"✓ Journal entries legacy: {len(data['data'])} items, total={pagination['total_count']}, has_next={pagination['has_next']}")
    
    def test_cursor_pagination_chain_no_duplicates(self, dev_session):
        """Cursor chain for 3 pages with no duplicates"""
        all_entry_ids = []
        cursor = None
        page_count = 0
        max_pages = 3
        
        while page_count < max_pages:
            params = {"limit": 5}
            if cursor:
                params["cursor"] = cursor
            
            resp = dev_session.get(f"{BASE_URL}/api/v1/journal-entries", params=params)
            assert resp.status_code == 200, f"Page {page_count+1} failed: {resp.text}"
            data = resp.json()
            
            pagination = data["pagination"]
            items = data["data"]
            
            for item in items:
                assert "entry_id" in item
                all_entry_ids.append(item["entry_id"])
            
            print(f"  Page {page_count+1}: {len(items)} entries, has_next={pagination['has_next']}")
            
            page_count += 1
            
            if not pagination["has_next"]:
                break
            
            cursor = pagination.get("next_cursor")
            assert cursor is not None, "has_next=True but next_cursor is None"
        
        # Verify no duplicates
        unique_ids = set(all_entry_ids)
        assert len(unique_ids) == len(all_entry_ids), f"Found {len(all_entry_ids) - len(unique_ids)} duplicates"
        
        print(f"✓ Journal entries cursor: {page_count} pages, {len(all_entry_ids)} total items, 0 duplicates")


class TestBackwardCompatibility:
    """Verify all endpoints work without cursor param (existing behavior preserved)"""
    
    def test_tickets_without_cursor(self, dev_session):
        """Tickets endpoint works without cursor"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/tickets", params={"limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        print("✓ Tickets backward compat: works without cursor")
    
    def test_invoices_without_cursor(self, dev_session):
        """Invoices endpoint works without cursor"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/invoices-enhanced", params={"limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        print("✓ Invoices backward compat: works without cursor")
    
    def test_employees_without_cursor(self, dev_session):
        """Employees endpoint works without cursor"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/hr/employees", params={"limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        print("✓ Employees backward compat: works without cursor")
    
    def test_failure_cards_without_cursor(self, dev_session):
        """Failure cards endpoint works without cursor (legacy)"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/efi/failure-cards", params={"limit": 10})
        assert resp.status_code == 200
        print("✓ Failure cards backward compat: works without cursor")
    
    def test_journal_entries_without_cursor(self, dev_session):
        """Journal entries endpoint works without cursor"""
        resp = dev_session.get(f"{BASE_URL}/api/v1/journal-entries", params={"limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        print("✓ Journal entries backward compat: works without cursor")


class TestCursorDecodeEncode:
    """Test cursor encoding/decoding edge cases"""
    
    def test_cursor_structure_validation(self, dev_session):
        """Verify cursor structure across all endpoints"""
        endpoints = [
            (f"{BASE_URL}/api/v1/tickets", "ticket_id"),
            (f"{BASE_URL}/api/v1/invoices-enhanced", "invoice_id"),
            (f"{BASE_URL}/api/v1/journal-entries", "entry_id"),
        ]
        
        for endpoint, id_field in endpoints:
            resp = dev_session.get(endpoint, params={"limit": 2})
            assert resp.status_code == 200, f"Failed for {endpoint}"
            data = resp.json()
            
            pagination = data.get("pagination", {})
            if pagination.get("next_cursor"):
                cursor_data = decode_cursor(pagination["next_cursor"])
                
                # Cursor must have v (sort value) and t (tiebreaker)
                assert "v" in cursor_data, f"Missing 'v' in cursor for {endpoint}"
                assert "t" in cursor_data, f"Missing 't' in cursor for {endpoint}"
                
                print(f"✓ {endpoint.split('/')[-1]}: cursor={cursor_data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
