"""
Ticket-Estimate Integration Tests
Tests for the new ticket-estimate integration feature:
- Auto-create estimate on technician assignment
- Ensure estimate endpoint (idempotent)
- Line item CRUD operations
- Concurrency control (version check)
- Locking mechanism
- Status operations (approve, send, lock)
"""

import pytest
import requests
import uuid
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://gst-report-update.preview.emergentagent.com"

# Test credentials from main agent
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "admin123"
ORGANIZATION_ID = "org_71f0df814d6d"
TEST_TICKET_ID = "tkt_796dbcc03efa"  # Existing test ticket
TEST_ESTIMATE_ID = "est_f3c7baf128ab"  # Existing test estimate

# Track created resources for cleanup
created_estimates = []
created_line_items = []


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create a session with auth headers"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "X-Organization-ID": ORGANIZATION_ID,
        "Content-Type": "application/json"
    })
    return session


class TestTicketEstimateEnsure:
    """Test POST /api/tickets/{id}/estimate/ensure - Idempotent estimate creation"""
    
    def test_ensure_estimate_creates_new(self, api_client):
        """Test creating estimate for ticket that doesn't have one"""
        # First check if test ticket exists
        response = api_client.get(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}")
        if response.status_code == 404:
            pytest.skip(f"Test ticket {TEST_TICKET_ID} not found")
        
        response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        
        # Should return 200 regardless of whether estimate exists or not
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Expected code 0, got {data}"
        assert "estimate" in data, "Response should contain estimate"
        
        estimate = data["estimate"]
        assert estimate.get("estimate_id"), "Estimate should have estimate_id"
        assert estimate.get("estimate_number"), "Estimate should have estimate_number"
        assert estimate.get("ticket_id") == TEST_TICKET_ID, "Estimate should be linked to ticket"
        assert estimate.get("status") in ["draft", "sent", "approved"], "Estimate should have valid status"
        assert "version" in estimate, "Estimate should have version for concurrency"
        assert "line_items" in estimate, "Estimate should include line_items array"
        
        created_estimates.append(estimate.get("estimate_id"))
        print(f"Ensure estimate returned: {estimate.get('estimate_id')}")
    
    def test_ensure_estimate_idempotent(self, api_client):
        """Test that calling ensure twice returns same estimate"""
        # Call ensure first time
        response1 = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        assert response1.status_code == 200
        estimate1 = response1.json().get("estimate")
        
        # Call ensure second time
        response2 = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        assert response2.status_code == 200
        estimate2 = response2.json().get("estimate")
        
        # Should return the same estimate
        assert estimate1.get("estimate_id") == estimate2.get("estimate_id"), \
            "Multiple ensure calls should return same estimate_id"
        assert estimate1.get("estimate_number") == estimate2.get("estimate_number"), \
            "Multiple ensure calls should return same estimate_number"
        
        print(f"Idempotent verify: {estimate1.get('estimate_id')} == {estimate2.get('estimate_id')}")
    
    def test_ensure_estimate_for_nonexistent_ticket(self, api_client):
        """Test ensure estimate for ticket that doesn't exist"""
        fake_ticket_id = f"tkt_fake_{uuid.uuid4().hex[:12]}"
        response = api_client.post(f"{BASE_URL}/api/tickets/{fake_ticket_id}/estimate/ensure")
        
        # Should return 404 for non-existent ticket
        assert response.status_code == 404, f"Expected 404 for fake ticket, got {response.status_code}"
        print(f"Non-existent ticket correctly returns 404")


class TestGetTicketEstimate:
    """Test GET /api/tickets/{id}/estimate - Get estimate with line items"""
    
    def test_get_estimate_by_ticket(self, api_client):
        """Test getting estimate for a ticket"""
        # First ensure estimate exists
        ensure_response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        if ensure_response.status_code != 200:
            pytest.skip("Could not ensure estimate for test")
        
        response = api_client.get(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "estimate" in data
        
        estimate = data["estimate"]
        assert estimate.get("ticket_id") == TEST_TICKET_ID
        assert "line_items" in estimate
        assert isinstance(estimate["line_items"], list)
        
        # Verify estimate structure
        assert "subtotal" in estimate, "Estimate should have subtotal"
        assert "tax_total" in estimate, "Estimate should have tax_total"
        assert "grand_total" in estimate, "Estimate should have grand_total"
        
        print(f"Got estimate: {estimate.get('estimate_id')} with {len(estimate.get('line_items', []))} items")
    
    def test_get_estimate_by_id(self, api_client):
        """Test getting estimate by its ID"""
        # First ensure we have an estimate
        ensure_response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        if ensure_response.status_code != 200:
            pytest.skip("Could not ensure estimate")
        
        estimate_id = ensure_response.json()["estimate"]["estimate_id"]
        
        response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{estimate_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("code") == 0
        assert data["estimate"]["estimate_id"] == estimate_id
        
        print(f"Get by ID successful: {estimate_id}")
    
    def test_get_nonexistent_estimate(self, api_client):
        """Test getting estimate for ticket without one"""
        fake_ticket_id = f"tkt_noest_{uuid.uuid4().hex[:8]}"
        response = api_client.get(f"{BASE_URL}/api/tickets/{fake_ticket_id}/estimate")
        
        # Should return 404
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestLineItemCRUD:
    """Test line item CRUD operations with concurrency control"""
    
    @pytest.fixture(autouse=True)
    def setup_estimate(self, api_client):
        """Ensure we have an estimate to work with"""
        response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        if response.status_code == 200:
            self.estimate = response.json()["estimate"]
            self.estimate_id = self.estimate["estimate_id"]
            self.current_version = self.estimate.get("version", 1)
        else:
            pytest.skip("Could not ensure estimate for line item tests")
    
    def test_add_part_line_item(self, api_client):
        """Test adding a part line item"""
        # Refresh estimate to get latest version
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        if get_response.status_code == 200:
            self.current_version = get_response.json()["estimate"].get("version", 1)
        
        response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "part",
                "name": "TEST_Battery Pack 48V",
                "description": "High capacity lithium battery",
                "qty": 1,
                "unit": "pcs",
                "unit_price": 25000.00,
                "discount": 0,
                "tax_rate": 18,
                "hsn_code": "8507",
                "version": self.current_version
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        
        estimate = data["estimate"]
        assert len(estimate.get("line_items", [])) > 0, "Should have at least 1 line item"
        
        # Find the newly added item
        new_items = [i for i in estimate["line_items"] if "TEST_Battery" in i.get("name", "")]
        assert len(new_items) > 0, "Should find the newly added item"
        
        line_item = new_items[-1]
        assert line_item["type"] == "part"
        assert line_item["unit_price"] == 25000.00
        assert line_item["tax_rate"] == 18
        assert "line_total" in line_item, "Should have calculated line_total"
        
        created_line_items.append(line_item.get("line_item_id"))
        print(f"Added part line item: {line_item.get('line_item_id')}")
    
    def test_add_labour_line_item(self, api_client):
        """Test adding a labour line item"""
        # Get latest version
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        current_version = get_response.json()["estimate"].get("version", 1)
        
        response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "labour",
                "name": "TEST_Installation Labour",
                "description": "Battery installation and calibration",
                "qty": 2,
                "unit": "hrs",
                "unit_price": 500.00,
                "discount": 0,
                "tax_rate": 18,
                "version": current_version
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        labour_items = [i for i in data["estimate"]["line_items"] if i.get("type") == "labour" and "TEST_" in i.get("name", "")]
        assert len(labour_items) > 0, "Should have added labour item"
        
        print(f"Added labour line item")
    
    def test_add_fee_line_item(self, api_client):
        """Test adding a fee line item"""
        # Get latest version
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        current_version = get_response.json()["estimate"].get("version", 1)
        
        response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "fee",
                "name": "TEST_Diagnostic Fee",
                "description": "Vehicle diagnostic assessment",
                "qty": 1,
                "unit": "pcs",
                "unit_price": 500.00,
                "discount": 0,
                "tax_rate": 18,
                "version": current_version
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"Added fee line item")
    
    def test_update_line_item(self, api_client):
        """Test updating a line item"""
        # First add an item to update
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        estimate = get_response.json()["estimate"]
        current_version = estimate.get("version", 1)
        
        # Add an item first
        add_response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "part",
                "name": "TEST_Item to Update",
                "qty": 1,
                "unit_price": 100.00,
                "tax_rate": 18,
                "version": current_version
            }
        )
        
        if add_response.status_code != 200:
            pytest.skip("Could not add item to update")
        
        estimate = add_response.json()["estimate"]
        new_version = estimate.get("version", 1)
        test_items = [i for i in estimate["line_items"] if "TEST_Item to Update" in i.get("name", "")]
        
        if not test_items:
            pytest.skip("Could not find added item")
        
        line_item_id = test_items[-1]["line_item_id"]
        
        # Now update it
        response = api_client.patch(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items/{line_item_id}",
            json={
                "name": "TEST_Updated Item Name",
                "qty": 2,
                "unit_price": 150.00,
                "version": new_version
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        updated_items = [i for i in data["estimate"]["line_items"] if i.get("line_item_id") == line_item_id]
        assert len(updated_items) == 1, "Should find updated item"
        
        updated = updated_items[0]
        assert updated["name"] == "TEST_Updated Item Name"
        assert updated["qty"] == 2
        assert updated["unit_price"] == 150.00
        
        print(f"Updated line item: {line_item_id}")
    
    def test_delete_line_item(self, api_client):
        """Test deleting a line item"""
        # First add an item to delete
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        current_version = get_response.json()["estimate"].get("version", 1)
        
        add_response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "fee",
                "name": "TEST_Item to Delete",
                "qty": 1,
                "unit_price": 50.00,
                "tax_rate": 0,
                "version": current_version
            }
        )
        
        if add_response.status_code != 200:
            pytest.skip("Could not add item to delete")
        
        estimate = add_response.json()["estimate"]
        new_version = estimate.get("version", 1)
        test_items = [i for i in estimate["line_items"] if "TEST_Item to Delete" in i.get("name", "")]
        
        if not test_items:
            pytest.skip("Could not find item to delete")
        
        line_item_id = test_items[-1]["line_item_id"]
        initial_count = len(estimate["line_items"])
        
        # Delete the item
        response = api_client.delete(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items/{line_item_id}?version={new_version}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify item is gone
        remaining_items = [i for i in data["estimate"]["line_items"] if i.get("line_item_id") == line_item_id]
        assert len(remaining_items) == 0, "Deleted item should not be present"
        
        print(f"Deleted line item: {line_item_id}")


class TestConcurrencyControl:
    """Test optimistic concurrency control (version mismatch returns 409)"""
    
    @pytest.fixture(autouse=True)
    def setup_estimate(self, api_client):
        """Ensure we have an estimate to work with"""
        response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        if response.status_code == 200:
            self.estimate = response.json()["estimate"]
            self.estimate_id = self.estimate["estimate_id"]
        else:
            pytest.skip("Could not ensure estimate")
    
    def test_version_mismatch_returns_409(self, api_client):
        """Test that using wrong version returns 409 Conflict"""
        # Use a wrong version number
        wrong_version = 99999
        
        response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "part",
                "name": "TEST_Should Fail - Wrong Version",
                "qty": 1,
                "unit_price": 100.00,
                "tax_rate": 18,
                "version": wrong_version
            }
        )
        
        assert response.status_code == 409, f"Expected 409 for version mismatch, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data, "Should have error detail"
        assert "current_estimate" in data.get("detail", {}), "Should include current_estimate in error"
        
        print(f"Concurrency check working: 409 returned for version mismatch")
    
    def test_update_with_wrong_version(self, api_client):
        """Test that update with wrong version returns 409"""
        # First get the estimate
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        estimate = get_response.json()["estimate"]
        
        # Add an item first
        add_response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "part",
                "name": "TEST_Concurrency Test Item",
                "qty": 1,
                "unit_price": 100.00,
                "tax_rate": 18,
                "version": estimate.get("version", 1)
            }
        )
        
        if add_response.status_code != 200:
            pytest.skip("Could not add test item")
        
        new_estimate = add_response.json()["estimate"]
        test_items = [i for i in new_estimate["line_items"] if "TEST_Concurrency" in i.get("name", "")]
        
        if not test_items:
            pytest.skip("Could not find test item")
        
        line_item_id = test_items[-1]["line_item_id"]
        
        # Try to update with old version (should fail)
        old_version = estimate.get("version", 1)  # This is now stale
        
        response = api_client.patch(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items/{line_item_id}",
            json={
                "qty": 5,
                "version": old_version  # Stale version
            }
        )
        
        assert response.status_code == 409, f"Expected 409 for stale version, got {response.status_code}"
        print(f"Update with stale version correctly returns 409")


class TestEstimateLocking:
    """Test estimate locking mechanism (returns 423 when locked)"""
    
    @pytest.fixture(autouse=True)
    def setup_fresh_estimate(self, api_client):
        """Create a fresh ticket and estimate for locking tests"""
        # First try to use the test ticket
        response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        if response.status_code == 200:
            self.estimate = response.json()["estimate"]
            self.estimate_id = self.estimate["estimate_id"]
            # Check if already locked
            if self.estimate.get("locked_at"):
                pytest.skip("Test estimate is already locked, cannot test locking flow")
        else:
            pytest.skip("Could not get test estimate")
    
    def test_lock_estimate_as_admin(self, api_client):
        """Test locking an estimate (admin/manager only)"""
        # First approve the estimate (required before locking)
        approve_response = api_client.post(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/approve")
        
        if approve_response.status_code not in [200, 400]:  # 400 if already approved/locked
            pytest.skip(f"Could not approve estimate: {approve_response.status_code}")
        
        # Now lock it
        response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/lock",
            json={"reason": "TEST_Locked for conversion to invoice"}
        )
        
        # Note: If estimate is already locked, we'll get 400
        if response.status_code == 400:
            error = response.json()
            if "already locked" in str(error).lower():
                print(f"Estimate already locked - skipping lock test")
                pytest.skip("Estimate already locked")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert data["estimate"].get("locked_at"), "Should have locked_at timestamp"
        assert "TEST_Locked" in (data["estimate"].get("lock_reason") or ""), "Should have lock reason"
        
        print(f"Estimate locked successfully")
    
    def test_modify_locked_estimate_returns_423(self, api_client):
        """Test that modifying a locked estimate returns 423"""
        # Get the estimate
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        estimate = get_response.json()["estimate"]
        
        # If not locked, lock it first
        if not estimate.get("locked_at"):
            # First approve
            api_client.post(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/approve")
            
            # Then lock
            lock_response = api_client.post(
                f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/lock",
                json={"reason": "TEST_Locked for 423 test"}
            )
            
            if lock_response.status_code != 200:
                pytest.skip("Could not lock estimate for test")
            
            estimate = lock_response.json()["estimate"]
        
        # Now try to add item to locked estimate
        response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "part",
                "name": "TEST_Should Fail - Locked",
                "qty": 1,
                "unit_price": 100.00,
                "tax_rate": 18,
                "version": estimate.get("version", 1)
            }
        )
        
        assert response.status_code == 423, f"Expected 423 for locked estimate, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data, "Should have error detail"
        
        print(f"Locked estimate correctly returns 423 on modification attempt")


class TestEstimateStatusOperations:
    """Test estimate status operations (approve, send)"""
    
    @pytest.fixture(autouse=True)
    def setup_estimate(self, api_client):
        """Ensure we have an estimate"""
        response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        if response.status_code == 200:
            self.estimate = response.json()["estimate"]
            self.estimate_id = self.estimate["estimate_id"]
        else:
            pytest.skip("Could not ensure estimate")
    
    def test_send_estimate(self, api_client):
        """Test sending an estimate"""
        # Check if locked
        if self.estimate.get("locked_at"):
            pytest.skip("Cannot send locked estimate")
        
        response = api_client.post(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/send")
        
        if response.status_code == 400:
            # Might be locked or already in a state that can't be sent
            print(f"Could not send estimate (might be locked): {response.text}")
            pytest.skip("Estimate cannot be sent in current state")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        # Status might be 'sent' or could remain if already past that stage
        
        print(f"Send estimate: status is now {data['estimate'].get('status')}")
    
    def test_approve_estimate(self, api_client):
        """Test approving an estimate"""
        # Check if locked
        if self.estimate.get("locked_at"):
            pytest.skip("Cannot approve locked estimate")
        
        response = api_client.post(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/approve")
        
        if response.status_code == 400:
            error_text = response.text.lower()
            if "locked" in error_text:
                pytest.skip("Estimate is locked")
            # Otherwise could be already approved
            print(f"Approve response: {response.text}")
        
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("code") == 0
            assert data["estimate"].get("status") == "approved", "Status should be approved"
            print(f"Estimate approved successfully")
        else:
            print(f"Estimate might already be approved or locked")


class TestListTicketEstimates:
    """Test listing ticket estimates"""
    
    def test_list_estimates(self, api_client):
        """Test listing all estimates for organization"""
        response = api_client.get(f"{BASE_URL}/api/ticket-estimates")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "estimates" in data
        assert "page_context" in data
        
        estimates = data["estimates"]
        assert isinstance(estimates, list)
        
        page_context = data["page_context"]
        assert "page" in page_context
        assert "per_page" in page_context
        assert "total" in page_context
        
        print(f"Listed {len(estimates)} estimates (total: {page_context['total']})")
    
    def test_list_estimates_with_status_filter(self, api_client):
        """Test listing estimates with status filter"""
        response = api_client.get(f"{BASE_URL}/api/ticket-estimates?status=draft")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        # All returned estimates should have draft status
        for est in estimates:
            assert est.get("status") == "draft", f"Expected draft status, got {est.get('status')}"
        
        print(f"Listed {len(estimates)} draft estimates")


class TestTotalsCalculation:
    """Test that server calculates totals correctly"""
    
    @pytest.fixture(autouse=True)
    def setup_estimate(self, api_client):
        """Ensure we have an estimate"""
        response = api_client.post(f"{BASE_URL}/api/tickets/{TEST_TICKET_ID}/estimate/ensure")
        if response.status_code == 200:
            self.estimate = response.json()["estimate"]
            self.estimate_id = self.estimate["estimate_id"]
        else:
            pytest.skip("Could not ensure estimate")
    
    def test_totals_update_on_add(self, api_client):
        """Test that totals are recalculated when adding items"""
        # Get initial totals
        get_response = api_client.get(f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}")
        estimate = get_response.json()["estimate"]
        
        if estimate.get("locked_at"):
            pytest.skip("Cannot test on locked estimate")
        
        initial_subtotal = estimate.get("subtotal", 0)
        initial_grand_total = estimate.get("grand_total", 0)
        current_version = estimate.get("version", 1)
        
        # Add an item
        add_response = api_client.post(
            f"{BASE_URL}/api/ticket-estimates/{self.estimate_id}/line-items",
            json={
                "type": "part",
                "name": "TEST_Totals Test Item",
                "qty": 2,
                "unit_price": 1000.00,
                "discount": 100,
                "tax_rate": 18,
                "version": current_version
            }
        )
        
        if add_response.status_code != 200:
            pytest.skip(f"Could not add item: {add_response.text}")
        
        new_estimate = add_response.json()["estimate"]
        
        # Verify totals updated
        # Subtotal should increase by qty * unit_price = 2 * 1000 = 2000
        # Tax should be (2000 - 100) * 0.18 = 342
        # So grand total should increase by 2000 - 100 + 342 = 2242
        
        assert new_estimate.get("subtotal", 0) > initial_subtotal, "Subtotal should increase"
        assert new_estimate.get("grand_total", 0) > initial_grand_total, "Grand total should increase"
        
        print(f"Totals updated: subtotal {initial_subtotal} -> {new_estimate.get('subtotal')}, grand_total {initial_grand_total} -> {new_estimate.get('grand_total')}")


# Cleanup fixture at the end
@pytest.fixture(scope="module", autouse=True)
def cleanup(api_client):
    """Cleanup test data after all tests"""
    yield
    
    # Note: In a real scenario, we might want to clean up TEST_ prefixed items
    # For now, we'll leave them as they're prefixed with TEST_ for identification
    print(f"Created estimates: {created_estimates}")
    print(f"Created line items: {created_line_items}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
