"""
Test suite for Zoho Extended Features APIs
Tests: Delivery Challans, Projects, Recurring Invoices, Taxes, Chart of Accounts, Journal Entries, Vendor Credits
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

pytestmark = pytest.mark.skip(reason="deprecated — Zoho integration removed")

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDeliveryChallans:
    """Delivery Challans API tests"""
    
    def test_list_delivery_challans(self):
        """Test listing delivery challans"""
        response = requests.get(f"{BASE_URL}/api/zoho/delivery-challans")
        assert response.status_code == 200
        data = response.json()
        assert "delivery_challans" in data
        assert data["code"] == 0
        print(f"Found {len(data['delivery_challans'])} delivery challans")
    
    def test_create_delivery_challan(self):
        """Test creating a delivery challan"""
        # First get a customer
        customers_res = requests.get(f"{BASE_URL}/api/zoho/contacts?contact_type=customer&per_page=10")
        customers = customers_res.json().get("contacts", [])
        
        if not customers:
            pytest.skip("No customers available for testing")
        
        customer = customers[0]
        
        payload = {
            "customer_id": customer["contact_id"],
            "customer_name": customer["contact_name"],
            "challan_type": "delivery",
            "reference_number": "TEST-DC-001",
            "line_items": [
                {"name": "TEST_Item_1", "rate": 1000, "quantity": 2}
            ],
            "notes": "Test delivery challan"
        }
        
        response = requests.post(f"{BASE_URL}/api/zoho/delivery-challans", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "delivery_challan" in data
        assert data["delivery_challan"]["customer_name"] == customer["contact_name"]
        print(f"Created delivery challan: {data['delivery_challan']['challan_number']}")


class TestProjects:
    """Projects API tests"""
    
    def test_list_projects(self):
        """Test listing projects"""
        response = requests.get(f"{BASE_URL}/api/zoho/projects")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert data["code"] == 0
        print(f"Found {len(data['projects'])} projects")
    
    def test_create_project(self):
        """Test creating a project"""
        # First get a customer
        customers_res = requests.get(f"{BASE_URL}/api/zoho/contacts?contact_type=customer&per_page=10")
        customers = customers_res.json().get("contacts", [])
        
        if not customers:
            pytest.skip("No customers available for testing")
        
        customer = customers[0]
        
        payload = {
            "project_name": "TEST_Project_001",
            "customer_id": customer["contact_id"],
            "customer_name": customer["contact_name"],
            "description": "Test project for API testing",
            "billing_type": "fixed_cost",
            "rate": 500,
            "budget_hours": 100
        }
        
        response = requests.post(f"{BASE_URL}/api/zoho/projects", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "project" in data
        assert data["project"]["project_name"] == "TEST_Project_001"
        print(f"Created project: {data['project']['project_id']}")
        return data["project"]["project_id"]
    
    def test_list_time_entries(self):
        """Test listing time entries"""
        response = requests.get(f"{BASE_URL}/api/zoho/time-entries")
        assert response.status_code == 200
        data = response.json()
        assert "time_entries" in data
        assert data["code"] == 0
        print(f"Found {len(data['time_entries'])} time entries")


class TestRecurringInvoices:
    """Recurring Invoices API tests"""
    
    def test_list_recurring_invoices(self):
        """Test listing recurring invoices"""
        response = requests.get(f"{BASE_URL}/api/zoho/recurring-invoices")
        assert response.status_code == 200
        data = response.json()
        assert "recurring_invoices" in data
        assert data["code"] == 0
        print(f"Found {len(data['recurring_invoices'])} recurring invoices")
    
    def test_create_recurring_invoice(self):
        """Test creating a recurring invoice"""
        # First get a customer
        customers_res = requests.get(f"{BASE_URL}/api/zoho/contacts?contact_type=customer&per_page=10")
        customers = customers_res.json().get("contacts", [])
        
        if not customers:
            pytest.skip("No customers available for testing")
        
        customer = customers[0]
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        payload = {
            "customer_id": customer["contact_id"],
            "customer_name": customer["contact_name"],
            "recurrence_name": "TEST_Monthly_Maintenance",
            "recurrence_frequency": "monthly",
            "repeat_every": 1,
            "start_date": start_date,
            "never_expires": True,
            "line_items": [
                {"name": "TEST_Service", "rate": 5000, "quantity": 1, "tax_percentage": 18}
            ],
            "payment_terms": 15
        }
        
        response = requests.post(f"{BASE_URL}/api/zoho/recurring-invoices", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "recurring_invoice" in data
        assert data["recurring_invoice"]["recurrence_name"] == "TEST_Monthly_Maintenance"
        print(f"Created recurring invoice: {data['recurring_invoice']['recurring_invoice_id']}")


class TestTaxes:
    """Taxes API tests"""
    
    def test_list_taxes(self):
        """Test listing taxes"""
        response = requests.get(f"{BASE_URL}/api/zoho/taxes")
        assert response.status_code == 200
        data = response.json()
        assert "taxes" in data
        assert data["code"] == 0
        print(f"Found {len(data['taxes'])} taxes")
    
    def test_create_tax(self):
        """Test creating a tax"""
        payload = {
            "tax_name": "TEST_GST_5",
            "tax_percentage": 5,
            "tax_type": "tax",
            "is_default": False,
            "description": "Test GST 5%"
        }
        
        response = requests.post(f"{BASE_URL}/api/zoho/taxes", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "tax" in data
        assert data["tax"]["tax_name"] == "TEST_GST_5"
        assert data["tax"]["tax_percentage"] == 5
        print(f"Created tax: {data['tax']['tax_id']}")
    
    def test_list_tax_groups(self):
        """Test listing tax groups"""
        response = requests.get(f"{BASE_URL}/api/zoho/tax-groups")
        assert response.status_code == 200
        data = response.json()
        assert "tax_groups" in data
        assert data["code"] == 0
        print(f"Found {len(data['tax_groups'])} tax groups")


class TestChartOfAccounts:
    """Chart of Accounts API tests"""
    
    def test_list_chart_of_accounts(self):
        """Test listing chart of accounts"""
        response = requests.get(f"{BASE_URL}/api/zoho/chartofaccounts")
        assert response.status_code == 200
        data = response.json()
        assert "chartofaccounts" in data
        assert data["code"] == 0
        print(f"Found {len(data['chartofaccounts'])} accounts")
    
    def test_create_account(self):
        """Test creating an account"""
        payload = {
            "account_name": "TEST_Cash_Account",
            "account_code": "1001",
            "account_type": "asset",
            "description": "Test cash account"
        }
        
        response = requests.post(f"{BASE_URL}/api/zoho/chartofaccounts", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "account" in data
        assert data["account"]["account_name"] == "TEST_Cash_Account"
        print(f"Created account: {data['account']['account_id']}")


class TestJournalEntries:
    """Journal Entries API tests"""
    
    def test_list_journal_entries(self):
        """Test listing journal entries"""
        response = requests.get(f"{BASE_URL}/api/zoho/journals")
        assert response.status_code == 200
        data = response.json()
        assert "journals" in data
        assert data["code"] == 0
        print(f"Found {len(data['journals'])} journal entries")
    
    def test_create_journal_entry(self):
        """Test creating a balanced journal entry"""
        payload = {
            "reference_number": "TEST-JE-001",
            "notes": "Test journal entry",
            "line_items": [
                {"account_id": "ACC-CASH", "account_name": "Cash", "debit": 5000, "credit": 0},
                {"account_id": "ACC-SALES", "account_name": "Sales Revenue", "debit": 0, "credit": 5000}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/zoho/journals", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "journal" in data
        assert data["journal"]["total_debit"] == data["journal"]["total_credit"]
        print(f"Created journal entry: {data['journal']['journal_id']}")


class TestVendorCredits:
    """Vendor Credits API tests"""
    
    def test_list_vendor_credits(self):
        """Test listing vendor credits"""
        response = requests.get(f"{BASE_URL}/api/zoho/vendorcredits")
        assert response.status_code == 200
        data = response.json()
        assert "vendorcredits" in data
        assert data["code"] == 0
        print(f"Found {len(data['vendorcredits'])} vendor credits")
    
    def test_create_vendor_credit(self):
        """Test creating a vendor credit"""
        # First get a vendor
        vendors_res = requests.get(f"{BASE_URL}/api/zoho/contacts?contact_type=vendor&per_page=10")
        vendors = vendors_res.json().get("contacts", [])
        
        if not vendors:
            pytest.skip("No vendors available for testing")
        
        vendor = vendors[0]
        
        payload = {
            "vendor_id": vendor["contact_id"],
            "vendor_name": vendor["contact_name"],
            "reason": "Purchase Return",
            "line_items": [
                {"name": "TEST_Returned_Item", "rate": 2000, "quantity": 1, "tax_percentage": 18}
            ],
            "notes": "Test vendor credit"
        }
        
        response = requests.post(f"{BASE_URL}/api/zoho/vendorcredits", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "vendorcredit" in data
        assert data["vendorcredit"]["vendor_name"] == vendor["contact_name"]
        print(f"Created vendor credit: {data['vendorcredit']['vendorcredit_id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
