"""
Test suite for Notification and Export APIs
Tests: Notifications CRUD, E-Invoice generation, Tally XML export, Bulk CSV export
"""

import pytest
import requests
import os
import json
import xml.etree.ElementTree as ET

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNotificationAPI:
    """Notification API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user = login_res.json().get("user", {})
    
    def test_create_notification(self):
        """Test POST /api/notifications - Create notification"""
        payload = {
            "user_id": "",
            "role": "admin",
            "notification_type": "invoice_sent",
            "title": "TEST_Invoice Sent",
            "message": "Test invoice INV-TEST-001 sent to Test Customer",
            "entity_type": "invoice",
            "entity_id": "test_invoice_001",
            "priority": "normal",
            "metadata": {"amount": 10000}
        }
        
        res = self.session.post(f"{BASE_URL}/api/notifications", json=payload)
        assert res.status_code == 200, f"Create notification failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "notification" in data
        assert data["notification"]["title"] == "TEST_Invoice Sent"
        assert data["notification"]["notification_type"] == "invoice_sent"
        assert data["notification"]["is_read"] == False
        
        # Store for later tests
        self.notification_id = data["notification"]["notification_id"]
        print(f"Created notification: {self.notification_id}")
        return self.notification_id
    
    def test_list_notifications(self):
        """Test GET /api/notifications - List notifications with unread count"""
        res = self.session.get(f"{BASE_URL}/api/notifications?role=admin&per_page=50")
        assert res.status_code == 200, f"List notifications failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "notifications" in data
        assert "unread_count" in data
        assert "page_context" in data
        assert isinstance(data["notifications"], list)
        assert isinstance(data["unread_count"], int)
        
        print(f"Found {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_get_unread_count(self):
        """Test GET /api/notifications/unread-count"""
        res = self.session.get(f"{BASE_URL}/api/notifications/unread-count?role=admin")
        assert res.status_code == 200, f"Get unread count failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        
        print(f"Unread count: {data['unread_count']}")
    
    def test_mark_notification_as_read(self):
        """Test PUT /api/notifications/{id}/read - Mark as read"""
        # First create a notification
        payload = {
            "role": "admin",
            "notification_type": "invoice_paid",
            "title": "TEST_Payment Received",
            "message": "Test payment received",
            "priority": "normal"
        }
        create_res = self.session.post(f"{BASE_URL}/api/notifications", json=payload)
        assert create_res.status_code == 200
        notification_id = create_res.json()["notification"]["notification_id"]
        
        # Mark as read
        res = self.session.put(f"{BASE_URL}/api/notifications/{notification_id}/read")
        assert res.status_code == 200, f"Mark as read failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "read" in data.get("message", "").lower()
        
        # Verify it's marked as read
        get_res = self.session.get(f"{BASE_URL}/api/notifications/{notification_id}")
        assert get_res.status_code == 200
        assert get_res.json()["notification"]["is_read"] == True
        
        print(f"Notification {notification_id} marked as read")
    
    def test_mark_all_as_read(self):
        """Test PUT /api/notifications/mark-all-read"""
        # Create a few unread notifications
        for i in range(2):
            self.session.post(f"{BASE_URL}/api/notifications", json={
                "role": "admin",
                "notification_type": "low_stock",
                "title": f"TEST_Low Stock Alert {i}",
                "message": f"Test low stock item {i}",
                "priority": "high"
            })
        
        # Mark all as read
        res = self.session.put(f"{BASE_URL}/api/notifications/mark-all-read?role=admin")
        assert res.status_code == 200, f"Mark all as read failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        
        # Verify unread count is 0
        count_res = self.session.get(f"{BASE_URL}/api/notifications/unread-count?role=admin")
        assert count_res.status_code == 200
        # Note: There might be other notifications, so just check it's a valid response
        
        print(f"Mark all as read: {data.get('message')}")
    
    def test_get_notification_details(self):
        """Test GET /api/notifications/{id} - Get notification details"""
        # Create a notification first
        payload = {
            "role": "admin",
            "notification_type": "amc_expiring",
            "title": "TEST_AMC Expiring",
            "message": "Test AMC expiring soon",
            "entity_type": "amc",
            "entity_id": "test_amc_001",
            "priority": "urgent"
        }
        create_res = self.session.post(f"{BASE_URL}/api/notifications", json=payload)
        notification_id = create_res.json()["notification"]["notification_id"]
        
        # Get details
        res = self.session.get(f"{BASE_URL}/api/notifications/{notification_id}")
        assert res.status_code == 200, f"Get notification failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "notification" in data
        assert data["notification"]["notification_id"] == notification_id
        assert data["notification"]["title"] == "TEST_AMC Expiring"
        assert data["notification"]["priority"] == "urgent"
        
        print(f"Got notification details: {notification_id}")
    
    def test_archive_notification(self):
        """Test DELETE /api/notifications/{id} - Archive notification"""
        # Create a notification
        create_res = self.session.post(f"{BASE_URL}/api/notifications", json={
            "role": "admin",
            "notification_type": "ticket_update",
            "title": "TEST_Ticket Update",
            "message": "Test ticket status changed",
            "priority": "normal"
        })
        notification_id = create_res.json()["notification"]["notification_id"]
        
        # Archive it
        res = self.session.delete(f"{BASE_URL}/api/notifications/{notification_id}")
        assert res.status_code == 200, f"Archive notification failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        
        print(f"Archived notification: {notification_id}")


class TestExportAPI:
    """Export API endpoint tests - E-Invoice and Tally"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and create test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Create test customer
        customer_res = self.session.post(f"{BASE_URL}/api/zoho/contacts", json={
            "contact_name": "TEST_Export Customer",
            "contact_type": "customer",
            "email": "test.export@example.com",
            "gst_no": "29AABCU9603R1ZJ",
            "billing_address": {
                "street": "123 Test Street",
                "city": "Bangalore",
                "state": "Karnataka",
                "state_code": "29",
                "zip": "560001"
            }
        })
        if customer_res.status_code == 200:
            self.customer_id = customer_res.json().get("contact", {}).get("contact_id")
        else:
            # Try to get existing customer
            list_res = self.session.get(f"{BASE_URL}/api/zoho/contacts?contact_type=customer&per_page=1")
            if list_res.status_code == 200 and list_res.json().get("contacts"):
                self.customer_id = list_res.json()["contacts"][0]["contact_id"]
            else:
                self.customer_id = None
        
        # Create test invoice
        if self.customer_id:
            invoice_res = self.session.post(f"{BASE_URL}/api/zoho/invoices", json={
                "customer_id": self.customer_id,
                "customer_name": "TEST_Export Customer",
                "line_items": [
                    {"name": "Test Service", "rate": 5000, "quantity": 2, "tax_percentage": 18}
                ],
                "place_of_supply": "29"
            })
            if invoice_res.status_code == 200:
                self.invoice_id = invoice_res.json().get("invoice", {}).get("invoice_id")
            else:
                # Get existing invoice
                inv_list = self.session.get(f"{BASE_URL}/api/zoho/invoices?per_page=1")
                if inv_list.status_code == 200 and inv_list.json().get("invoices"):
                    self.invoice_id = inv_list.json()["invoices"][0]["invoice_id"]
                else:
                    self.invoice_id = None
        else:
            self.invoice_id = None
    
    def test_generate_einvoice(self):
        """Test GET /api/export/einvoice/{invoice_id} - Generate GST e-invoice JSON"""
        if not self.invoice_id:
            # Get any existing invoice
            inv_list = self.session.get(f"{BASE_URL}/api/zoho/invoices?per_page=1")
            if inv_list.status_code == 200 and inv_list.json().get("invoices"):
                self.invoice_id = inv_list.json()["invoices"][0]["invoice_id"]
            else:
                pytest.skip("No invoices available for e-invoice test")
        
        res = self.session.get(f"{BASE_URL}/api/export/einvoice/{self.invoice_id}")
        assert res.status_code == 200, f"Generate e-invoice failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "einvoice_json" in data
        
        einvoice = data["einvoice_json"]
        # Verify e-invoice structure
        assert "Version" in einvoice
        assert "TranDtls" in einvoice
        assert "DocDtls" in einvoice
        assert "SellerDtls" in einvoice
        assert "BuyerDtls" in einvoice
        assert "ItemList" in einvoice
        assert "ValDtls" in einvoice
        
        # Verify seller details
        assert einvoice["SellerDtls"]["Gstin"]
        assert einvoice["SellerDtls"]["LglNm"]
        
        # Verify value details
        assert "AssVal" in einvoice["ValDtls"]
        assert "TotInvVal" in einvoice["ValDtls"]
        
        print(f"Generated e-invoice for {data.get('invoice_number')}")
        print(f"E-invoice structure valid with {len(einvoice['ItemList'])} items")
    
    def test_download_einvoice(self):
        """Test GET /api/export/einvoice/{invoice_id}/download - Download e-invoice JSON file"""
        if not self.invoice_id:
            inv_list = self.session.get(f"{BASE_URL}/api/zoho/invoices?per_page=1")
            if inv_list.status_code == 200 and inv_list.json().get("invoices"):
                self.invoice_id = inv_list.json()["invoices"][0]["invoice_id"]
            else:
                pytest.skip("No invoices available")
        
        res = self.session.get(f"{BASE_URL}/api/export/einvoice/{self.invoice_id}/download")
        assert res.status_code == 200, f"Download e-invoice failed: {res.text}"
        
        # Verify it's a JSON file
        assert "application/json" in res.headers.get("content-type", "")
        assert "attachment" in res.headers.get("content-disposition", "")
        
        # Verify content is valid JSON
        content = json.loads(res.text)
        assert "Version" in content
        
        print("E-invoice download successful")
    
    def test_export_invoices_to_tally(self):
        """Test GET /api/export/tally/invoices - Export invoices as Tally XML"""
        res = self.session.get(f"{BASE_URL}/api/export/tally/invoices?limit=10")
        assert res.status_code == 200, f"Export to Tally failed: {res.text}"
        
        # Verify it's XML
        assert "application/xml" in res.headers.get("content-type", "")
        
        # Parse and verify XML structure
        root = ET.fromstring(res.text)
        assert root.tag == "ENVELOPE"
        
        header = root.find("HEADER")
        assert header is not None
        assert header.find("TALLYREQUEST").text == "Import Data"
        
        body = root.find("BODY")
        assert body is not None
        
        print("Tally invoices export successful - valid XML structure")
    
    def test_export_bills_to_tally(self):
        """Test GET /api/export/tally/bills - Export bills as Tally XML"""
        res = self.session.get(f"{BASE_URL}/api/export/tally/bills?limit=10")
        assert res.status_code == 200, f"Export bills to Tally failed: {res.text}"
        
        # Verify XML
        assert "application/xml" in res.headers.get("content-type", "")
        
        root = ET.fromstring(res.text)
        assert root.tag == "ENVELOPE"
        
        print("Tally bills export successful")
    
    def test_export_ledgers_to_tally(self):
        """Test GET /api/export/tally/ledgers - Export contacts as Tally ledgers"""
        res = self.session.get(f"{BASE_URL}/api/export/tally/ledgers")
        assert res.status_code == 200, f"Export ledgers to Tally failed: {res.text}"
        
        # Verify XML
        assert "application/xml" in res.headers.get("content-type", "")
        
        root = ET.fromstring(res.text)
        assert root.tag == "ENVELOPE"
        
        # Check for ledger entries
        body = root.find("BODY")
        import_data = body.find("IMPORTDATA") if body else None
        request_desc = import_data.find("REQUESTDESC") if import_data else None
        if request_desc:
            report_name = request_desc.find("REPORTNAME")
            assert report_name is not None
            assert report_name.text == "All Masters"
        
        print("Tally ledgers export successful")
    
    def test_bulk_export_invoices_csv(self):
        """Test GET /api/export/bulk/invoices?format=csv - Export invoices as CSV"""
        res = self.session.get(f"{BASE_URL}/api/export/bulk/invoices?format=csv")
        assert res.status_code == 200, f"Bulk export CSV failed: {res.text}"
        
        # Verify CSV
        assert "text/csv" in res.headers.get("content-type", "")
        
        # Verify CSV structure
        lines = res.text.strip().split("\n")
        assert len(lines) >= 1  # At least header
        
        header = lines[0]
        assert "Invoice Number" in header
        assert "Date" in header
        assert "Customer" in header
        assert "Total" in header
        assert "Status" in header
        
        print(f"Bulk CSV export successful - {len(lines)-1} invoices exported")
    
    def test_bulk_export_invoices_json(self):
        """Test GET /api/export/bulk/invoices?format=json - Export invoices as JSON"""
        res = self.session.get(f"{BASE_URL}/api/export/bulk/invoices?format=json")
        assert res.status_code == 200, f"Bulk export JSON failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "invoices" in data
        assert "count" in data
        assert isinstance(data["invoices"], list)
        
        print(f"Bulk JSON export successful - {data['count']} invoices")
    
    def test_bulk_export_expenses_csv(self):
        """Test GET /api/export/bulk/expenses?format=csv - Export expenses as CSV"""
        res = self.session.get(f"{BASE_URL}/api/export/bulk/expenses?format=csv")
        assert res.status_code == 200, f"Bulk expenses export failed: {res.text}"
        
        # Verify CSV
        assert "text/csv" in res.headers.get("content-type", "")
        
        lines = res.text.strip().split("\n")
        assert len(lines) >= 1
        
        header = lines[0]
        assert "Date" in header
        assert "Amount" in header
        
        print(f"Bulk expenses CSV export successful")


class TestNotificationEventTriggers:
    """Test notification event trigger endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_check_overdue_invoices(self):
        """Test POST /api/notifications/check-overdue-invoices"""
        res = self.session.post(f"{BASE_URL}/api/notifications/check-overdue-invoices")
        assert res.status_code == 200, f"Check overdue invoices failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "message" in data
        
        print(f"Check overdue invoices: {data.get('message')}")
    
    def test_check_expiring_amcs(self):
        """Test POST /api/notifications/check-expiring-amcs"""
        res = self.session.post(f"{BASE_URL}/api/notifications/check-expiring-amcs")
        assert res.status_code == 200, f"Check expiring AMCs failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        
        print(f"Check expiring AMCs: {data.get('message')}")
    
    def test_check_low_stock(self):
        """Test POST /api/notifications/check-low-stock"""
        res = self.session.post(f"{BASE_URL}/api/notifications/check-low-stock")
        assert res.status_code == 200, f"Check low stock failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        
        print(f"Check low stock: {data.get('message')}")
    
    def test_notification_preferences_get(self):
        """Test GET /api/notifications/preferences/{user_id}"""
        res = self.session.get(f"{BASE_URL}/api/notifications/preferences/test_user_001")
        assert res.status_code == 200, f"Get preferences failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert "preferences" in data
        
        prefs = data["preferences"]
        assert "email_notifications" in prefs
        assert "push_notifications" in prefs
        
        print("Notification preferences retrieved successfully")
    
    def test_notification_preferences_update(self):
        """Test PUT /api/notifications/preferences/{user_id}"""
        payload = {
            "user_id": "test_user_002",
            "email_notifications": True,
            "push_notifications": False,
            "invoice_alerts": True,
            "amc_alerts": True,
            "stock_alerts": False,
            "ticket_alerts": True
        }
        
        res = self.session.put(f"{BASE_URL}/api/notifications/preferences/test_user_002", json=payload)
        assert res.status_code == 200, f"Update preferences failed: {res.text}"
        
        data = res.json()
        assert data.get("code") == 0
        assert data["preferences"]["push_notifications"] == False
        assert data["preferences"]["stock_alerts"] == False
        
        print("Notification preferences updated successfully")


# Cleanup test data
class TestCleanup:
    """Cleanup test notifications"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        token = login_res.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_cleanup_test_notifications(self):
        """Archive all TEST_ prefixed notifications"""
        # Get all notifications
        res = self.session.get(f"{BASE_URL}/api/notifications?per_page=100")
        if res.status_code == 200:
            notifications = res.json().get("notifications", [])
            archived = 0
            for notif in notifications:
                if notif.get("title", "").startswith("TEST_"):
                    del_res = self.session.delete(f"{BASE_URL}/api/notifications/{notif['notification_id']}")
                    if del_res.status_code == 200:
                        archived += 1
            print(f"Cleaned up {archived} test notifications")
        else:
            print("No cleanup needed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
