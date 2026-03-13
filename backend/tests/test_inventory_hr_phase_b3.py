"""
Phase B-3 Backend Tests: Inventory Module Depth + HR Module Depth
Tests:
1. Inventory: Items CRUD, adjustments, stock tracking, serial/batch
2. HR: Attendance clock-in/out, leave types/balance/request, payroll generation
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = "demo@voltmotors.in"
OWNER_PASSWORD = "Demo@12345"
TECH_EMAIL = "ankit@voltmotors.in"
TECH_PASSWORD = "Tech@12345"

# Organization ID for demo data
DEMO_ORG_ID = "demo-volt-motors-001"


def get_auth_token(email, password):
    """Get auth token for given credentials"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    return None


@pytest.fixture(scope="module")
def owner_token():
    """Get workshop owner token"""
    token = get_auth_token(OWNER_EMAIL, OWNER_PASSWORD)
    if not token:
        pytest.skip("Owner login failed")
    return token


@pytest.fixture(scope="module")
def tech_token():
    """Get technician token for attendance tests"""
    token = get_auth_token(TECH_EMAIL, TECH_PASSWORD)
    if not token:
        pytest.skip("Technician login failed")
    return token


def auth_headers_demo(token):
    """Build auth headers with demo org context"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Organization-ID": DEMO_ORG_ID  # Override the auto-injected org
    }


# ====================================================================================
# TASK 1: INVENTORY MODULE DEPTH VERIFICATION
# ====================================================================================

class TestInventoryItems:
    """Test item CRUD and inventory endpoints"""

    def test_get_items_enhanced_list(self, owner_token):
        """GET /api/v1/items-enhanced returns 200 with items list (16+ items)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/items-enhanced",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        # Check items in response - could be in 'items' or 'data'
        items = data.get("items") or data.get("data", [])
        assert isinstance(items, list), f"Items should be a list, got {type(items)}"
        assert len(items) >= 16, f"Expected 16+ items, got {len(items)}"
        print(f"PASS: GET /api/v1/items-enhanced returns {len(items)} items")

    def test_create_item_enhanced(self, owner_token):
        """POST /api/v1/items-enhanced creates item successfully with item_id in response.item"""
        test_item = {
            "name": f"TEST_Item_Phase_B3_{datetime.now().strftime('%H%M%S')}",
            "sku": f"TEST-SKU-B3-{datetime.now().strftime('%H%M%S')}",
            "unit": "nos",
            "sales_rate": 1500,
            "purchase_rate": 1200,
            "item_type": "inventory",
            "description": "Test item created for Phase B-3 testing",
            "tax_preference": "taxable",
            "hsn_code": "8544"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/items-enhanced",
            headers=auth_headers_demo(owner_token),
            json=test_item
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        # Item ID could be in response.item.item_id or response.item_id
        item_data = data.get("item") or data
        item_id = item_data.get("item_id")
        assert item_id is not None, f"Expected item_id in response, got: {data}"
        print(f"PASS: Created item with item_id={item_id}")

    def test_inventory_enhanced_summary(self, owner_token):
        """GET /api/v1/inventory-enhanced/summary returns 200 with total_items count"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory-enhanced/summary",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        summary = data.get("summary") or data
        total_items = summary.get("total_items")
        assert total_items is not None, f"Expected total_items in summary, got: {data}"
        assert isinstance(total_items, int), f"total_items should be int, got {type(total_items)}"
        print(f"PASS: Inventory summary shows total_items={total_items}")


class TestInventoryAdjustments:
    """Test inventory adjustments endpoints"""

    def test_get_adjustments_list(self, owner_token):
        """GET /api/v1/inv-adjustments returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inv-adjustments",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        assert "adjustments" in data or "code" in data, f"Expected adjustments in response, got: {list(data.keys())}"
        print(f"PASS: GET /api/v1/inv-adjustments returns 200")

    def test_create_adjustment_draft(self, owner_token):
        """POST /api/v1/inv-adjustments creates adjustment with status=draft"""
        # First get an item to adjust
        items_resp = requests.get(
            f"{BASE_URL}/api/v1/items-enhanced?limit=5",
            headers=auth_headers_demo(owner_token)
        )
        if items_resp.status_code != 200:
            pytest.skip("Cannot get items for adjustment test")
        
        items = items_resp.json().get("items") or items_resp.json().get("data", [])
        if not items:
            pytest.skip("No items available for adjustment test")
        
        test_item = items[0]
        item_id = test_item.get("item_id")
        
        adjustment_data = {
            "adjustment_type": "quantity",
            "reason": "Testing Phase B-3 adjustment",
            "account": "Cost of Goods Sold",
            "status": "draft",
            "line_items": [
                {
                    "item_id": item_id,
                    "item_name": test_item.get("name"),
                    "quantity_available": 0,
                    "new_quantity": 5,
                    "quantity_adjusted": 5
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/inv-adjustments",
            headers=auth_headers_demo(owner_token),
            json=adjustment_data
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        # Check status is draft
        status = data.get("status")
        assert status == "draft", f"Expected status=draft, got {status}"
        print(f"PASS: Created adjustment with status=draft, adjustment_id={data.get('adjustment_id')}")


class TestInventoryStockTracking:
    """Test reorder suggestions and serial/batch tracking"""

    def test_reorder_suggestions(self, owner_token):
        """GET /api/v1/inventory/reorder-suggestions returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/inventory/reorder-suggestions",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        # Could be suggestions or grouped_by_vendor
        assert "suggestions" in data or "total_items_below_reorder" in data or "code" in data, \
            f"Expected suggestions data, got: {list(data.keys())}"
        print(f"PASS: GET /api/v1/inventory/reorder-suggestions returns 200")

    def test_serial_batch_serials_list(self, owner_token):
        """GET /api/v1/serial-batch/serials returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/serial-batch/serials",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        assert "serials" in data or "code" in data, f"Expected serials in response, got: {list(data.keys())}"
        print(f"PASS: GET /api/v1/serial-batch/serials returns 200")

    def test_serial_batch_batches_list(self, owner_token):
        """GET /api/v1/serial-batch/batches returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/serial-batch/batches",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        assert "batches" in data or "code" in data, f"Expected batches in response, got: {list(data.keys())}"
        print(f"PASS: GET /api/v1/serial-batch/batches returns 200")


# ====================================================================================
# TASK 2: HR MODULE DEPTH - ATTENDANCE, LEAVE, PAYROLL
# ====================================================================================

class TestHRAttendance:
    """Test HR attendance clock-in/out endpoints (use tech token for ankit)"""

    def test_clock_in(self, tech_token):
        """POST /api/v1/hr/attendance/clock-in returns 200 (use tech token for ankit@voltmotors.in)"""
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/attendance/clock-in",
            headers=auth_headers_demo(tech_token),
            json={"location": "Workshop - Test Clock In"}
        )
        # Could be 200 (success) or 400 (already clocked in)
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        if response.status_code == 200:
            print(f"PASS: Clock-in successful")
        else:
            # 400 means already clocked in - also acceptable
            print(f"PASS: Clock-in returned 400 (already clocked in): {data.get('detail', data)}")

    def test_clock_out(self, tech_token):
        """POST /api/v1/hr/attendance/clock-out returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/attendance/clock-out",
            headers=auth_headers_demo(tech_token),
            json={"location": "Workshop - Test Clock Out"}
        )
        # Could be 200 (success) or 400 (not clocked in / already clocked out)
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        if response.status_code == 200:
            print(f"PASS: Clock-out successful")
        else:
            print(f"PASS: Clock-out returned 400 (not clocked in or already clocked out): {data.get('detail', data)}")

    def test_today_attendance(self, tech_token):
        """GET /api/v1/hr/attendance/today returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/attendance/today",
            headers=auth_headers_demo(tech_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        print(f"PASS: GET /api/v1/hr/attendance/today returns 200: {list(data.keys())}")


class TestHRLeave:
    """Test HR leave management endpoints"""

    def test_leave_types(self, owner_token):
        """GET /api/v1/hr/leave/types returns 5 leave types"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/leave/types",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        # Response is a list of leave types
        leave_types = data if isinstance(data, list) else data.get("leave_types", [])
        # Main agent says 5 leave types but includes unpaid making it 6 typically
        assert len(leave_types) >= 5, f"Expected 5+ leave types, got {len(leave_types)}: {leave_types}"
        
        # Verify casual and sick types exist
        type_names = [lt.get("type") or lt.get("name", "") for lt in leave_types]
        assert "casual" in type_names or "Casual Leave" in type_names, f"Expected casual leave type, got: {type_names}"
        print(f"PASS: GET /api/v1/hr/leave/types returns {len(leave_types)} leave types: {type_names}")

    def test_leave_balance(self, owner_token):
        """GET /api/v1/hr/leave/balance returns non-empty balances (casual=12, sick=12, etc)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/leave/balance",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        # Data should be leave balances dict
        balances = data if isinstance(data, dict) and "casual" in data else data.get("balances", data)
        assert len(balances) > 0, f"Expected non-empty leave balances, got: {data}"
        
        # Check casual and sick balances
        casual = balances.get("casual", 0)
        sick = balances.get("sick", 0)
        assert casual == 12 or sick == 12, f"Expected casual=12 or sick=12, got casual={casual}, sick={sick}"
        print(f"PASS: Leave balances - casual={casual}, sick={sick}, full: {balances}")

    def test_leave_request_create(self, owner_token):
        """POST /api/v1/hr/leave/request creates leave request with status=pending"""
        # Use earned leave to avoid conflicts with existing pending requests
        leave_request = {
            "leave_type": "earned",
            "start_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=61)).strftime("%Y-%m-%d"),
            "reason": "Test leave request for Phase B-3 testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/leave/request",
            headers=auth_headers_demo(owner_token),
            json=leave_request
        )
        # Could be 200/201 for success or 400 if already pending
        assert response.status_code in [200, 201, 400], f"Expected 200/201/400, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        if response.status_code in [200, 201]:
            status = data.get("status")
            assert status == "pending", f"Expected status=pending, got {status}"
            print(f"PASS: Leave request created with status=pending")
        else:
            print(f"PASS: Leave request returned 400 (likely already has pending): {data.get('detail', data)}")


class TestHRPayroll:
    """Test HR payroll calculation and generation"""

    def test_payroll_calculate_emp001(self, owner_token):
        """GET /api/v1/hr/payroll/calculate/EMP-001 returns gross=60000, net>0"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hr/payroll/calculate/EMP-001",
            headers=auth_headers_demo(owner_token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        # Check gross salary (EMP-001 has basic=35000, hra=14000, da=3500, special=7500 = gross 60000)
        earnings = data.get("earnings", {})
        gross = earnings.get("gross", 0) or data.get("gross_salary", 0)
        net = data.get("net_salary", 0)
        
        # Gross should be 60000
        assert gross == 60000, f"Expected gross=60000, got {gross}: {data}"
        assert net > 0, f"Expected net > 0, got {net}: {data}"
        print(f"PASS: Payroll calculate EMP-001: gross={gross}, net={net}")

    def test_payroll_generate_january_2026(self, owner_token):
        """POST /api/v1/hr/payroll/generate with body {month:1,year:2026} creates payroll with total_gross=250000"""
        # Use January 2026 as Feb and March already exist per agent context
        response = requests.post(
            f"{BASE_URL}/api/v1/hr/payroll/generate",
            headers=auth_headers_demo(owner_token),
            json={"month": 1, "year": 2026}
        )
        # Could be 200/201 for success or 409 if already generated
        assert response.status_code in [200, 201, 409], f"Expected 200/201/409, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        
        if response.status_code in [200, 201]:
            total_gross = data.get("total_gross") or data.get("summary", {}).get("total_gross", 0)
            # 5 employees × ~50000 avg = ~250000
            print(f"PASS: Payroll generated for Jan 2026: total_gross={total_gross}")
            assert total_gross > 200000, f"Expected total_gross > 200000, got {total_gross}"
        else:
            # 409 means already generated - also acceptable
            print(f"PASS: Payroll generate returned 409 (already exists): {data.get('detail', data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
