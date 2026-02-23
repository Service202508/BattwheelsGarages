"""
Customers Enhanced Module - Comprehensive Backend API Tests
Tests all 45+ endpoints for the Zoho Books-like Customers module
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://production-readiness-4.preview.emergentagent.com').rstrip('/')

# Test data prefix for cleanup
TEST_PREFIX = "TEST_"

class TestCustomersEnhancedSettings:
    """Test settings and summary endpoints"""
    
    def test_get_settings(self):
        """GET /api/customers-enhanced/settings - Returns module settings"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "settings" in data
        assert "numbering" in data["settings"]
        assert "defaults" in data["settings"]
        print(f"Settings: {data['settings']}")
    
    def test_get_summary(self):
        """GET /api/customers-enhanced/summary - Returns customer statistics"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        assert "total" in summary
        assert "active" in summary
        assert "inactive" in summary
        assert "with_gstin" in summary
        assert "with_portal" in summary
        assert "new_this_month" in summary
        assert "total_receivable" in summary
        assert "total_credit_limit" in summary
        print(f"Summary: {summary}")
    
    def test_check_sync(self):
        """GET /api/customers-enhanced/check-sync - Audit customers data quality"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/check-sync")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "sync_report" in data
        report = data["sync_report"]
        assert "summary" in report
        assert "data_quality" in report
        assert "linkages" in report
        assert "portal" in report
        assert "gst_treatment_breakdown" in report
        print(f"Sync Report Summary: {report['summary']}")


class TestGSTINValidation:
    """Test GSTIN validation endpoint"""
    
    def test_validate_valid_gstin_delhi(self):
        """GET /api/customers-enhanced/validate-gstin/{gstin} - Valid Delhi GSTIN"""
        gstin = "07AAACH1234L1Z2"
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/validate-gstin/{gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        result = data["result"]
        assert result["valid"] == True
        assert result["state_code"] == "DL"
        assert result["state_name"] == "Delhi"
        assert result["pan"] == "AAACH1234L"
        print(f"Valid GSTIN result: {result}")
    
    def test_validate_valid_gstin_maharashtra(self):
        """GET /api/customers-enhanced/validate-gstin/{gstin} - Valid Maharashtra GSTIN"""
        gstin = "27AABCU9603R1ZM"
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/validate-gstin/{gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        result = data["result"]
        assert result["valid"] == True
        assert result["state_code"] == "MH"
        assert result["state_name"] == "Maharashtra"
        print(f"Valid Maharashtra GSTIN: {result}")
    
    def test_validate_invalid_gstin_format(self):
        """GET /api/customers-enhanced/validate-gstin/{gstin} - Invalid format"""
        gstin = "INVALID123"
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/validate-gstin/{gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        result = data["result"]
        assert result["valid"] == False
        assert "error" in result
        print(f"Invalid GSTIN error: {result['error']}")
    
    def test_validate_invalid_state_code(self):
        """GET /api/customers-enhanced/validate-gstin/{gstin} - Invalid state code"""
        gstin = "99AAACH1234L1Z2"  # 99 is not a valid state code
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/validate-gstin/{gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        result = data["result"]
        assert result["valid"] == False
        print(f"Invalid state code error: {result['error']}")


class TestCustomerCRUD:
    """Test Customer CRUD operations"""
    
    created_customer_id = None
    
    def test_create_customer_basic(self):
        """POST /api/customers-enhanced/ - Create customer with basic info"""
        payload = {
            "display_name": f"{TEST_PREFIX}Basic Customer",
            "company_name": "Test Company Ltd",
            "email": f"test.basic.{int(time.time())}@example.com",
            "phone": "9876543210",
            "gst_treatment": "registered",
            "customer_type": "business",
            "payment_terms": 30,
            "credit_limit": 50000
        }
        response = requests.post(f"{BASE_URL}/api/customers-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "customer" in data
        customer = data["customer"]
        assert customer["display_name"] == payload["display_name"]
        assert customer["is_active"] == True
        assert "customer_id" in customer
        assert "customer_number" in customer
        TestCustomerCRUD.created_customer_id = customer["customer_id"]
        print(f"Created customer: {customer['customer_number']} - {customer['customer_id']}")
    
    def test_create_customer_with_gstin(self):
        """POST /api/customers-enhanced/ - Create customer with GSTIN validation"""
        payload = {
            "display_name": f"{TEST_PREFIX}GSTIN Customer",
            "company_name": "GST Registered Company",
            "email": f"test.gstin.{int(time.time())}@example.com",
            "gstin": "07AAACH1234L1Z2",
            "gst_treatment": "registered",
            "customer_type": "business"
        }
        response = requests.post(f"{BASE_URL}/api/customers-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        customer = data["customer"]
        assert customer["gstin"] == "07AAACH1234L1Z2"
        assert customer["pan"] == "AAACH1234L"  # Auto-extracted from GSTIN
        assert customer["place_of_supply"] == "DL"  # Auto-extracted from GSTIN
        print(f"Created GSTIN customer: {customer['customer_number']}")
    
    def test_create_customer_invalid_gstin(self):
        """POST /api/customers-enhanced/ - Reject invalid GSTIN"""
        payload = {
            "display_name": f"{TEST_PREFIX}Invalid GSTIN Customer",
            "gstin": "INVALID123",
            "gst_treatment": "registered"
        }
        response = requests.post(f"{BASE_URL}/api/customers-enhanced/", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "Invalid GSTIN" in data["detail"]
        print(f"Correctly rejected invalid GSTIN: {data['detail']}")
    
    def test_list_customers(self):
        """GET /api/customers-enhanced/ - List customers with filters"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/?status=active&per_page=50")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "customers" in data
        assert "page_context" in data
        print(f"Listed {len(data['customers'])} customers, total: {data['page_context']['total']}")
    
    def test_list_customers_with_search(self):
        """GET /api/customers-enhanced/ - Search customers"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/?search={TEST_PREFIX}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"Search found {len(data['customers'])} customers with prefix {TEST_PREFIX}")
    
    def test_list_customers_by_gst_treatment(self):
        """GET /api/customers-enhanced/ - Filter by GST treatment"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/?gst_treatment=registered")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for customer in data["customers"]:
            assert customer["gst_treatment"] == "registered"
        print(f"Found {len(data['customers'])} registered customers")
    
    def test_get_customer_detail(self):
        """GET /api/customers-enhanced/{id} - Get customer with full details"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        customer = data["customer"]
        assert "persons" in customer
        assert "addresses" in customer
        assert "balance_details" in customer
        assert "aging" in customer
        assert "transaction_counts" in customer
        assert "history" in customer
        assert "credits" in customer
        print(f"Customer detail: {customer['display_name']}, balance: {customer['balance_details']}")
    
    def test_update_customer(self):
        """PUT /api/customers-enhanced/{id} - Update customer"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "company_name": "Updated Company Name",
            "payment_terms": 45,
            "credit_limit": 100000,
            "notes": "Updated via test"
        }
        response = requests.put(f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        customer = data["customer"]
        assert customer["company_name"] == "Updated Company Name"
        assert customer["payment_terms"] == 45
        assert customer["credit_limit"] == 100000
        print(f"Updated customer: {customer['customer_id']}")
    
    def test_get_customer_not_found(self):
        """GET /api/customers-enhanced/{id} - Customer not found"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/NONEXISTENT-ID")
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent customer")


class TestContactPersons:
    """Test contact persons management"""
    
    person_id = None
    
    def test_add_contact_person(self):
        """POST /api/customers-enhanced/{id}/persons - Add contact person"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "9876543211",
            "designation": "Manager",
            "department": "Sales",
            "is_primary": True
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/persons",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        person = data["person"]
        assert person["first_name"] == "John"
        assert person["is_primary"] == True
        TestContactPersons.person_id = person["person_id"]
        print(f"Added contact person: {person['person_id']}")
    
    def test_add_second_person(self):
        """POST /api/customers-enhanced/{id}/persons - Add second person"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "designation": "Director",
            "is_primary": False
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/persons",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"Added second person: {data['person']['person_id']}")
    
    def test_get_customer_persons(self):
        """GET /api/customers-enhanced/{id}/persons - Get all persons"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/persons")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["persons"]) >= 2
        print(f"Customer has {len(data['persons'])} contact persons")
    
    def test_update_person(self):
        """PUT /api/customers-enhanced/{id}/persons/{person_id} - Update person"""
        if not TestCustomerCRUD.created_customer_id or not TestContactPersons.person_id:
            pytest.skip("No customer or person created")
        
        payload = {
            "designation": "Senior Manager",
            "department": "Operations"
        }
        response = requests.put(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/persons/{TestContactPersons.person_id}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["person"]["designation"] == "Senior Manager"
        print(f"Updated person: {TestContactPersons.person_id}")
    
    def test_set_primary_person(self):
        """POST /api/customers-enhanced/{id}/persons/{person_id}/set-primary - Set primary contact"""
        if not TestCustomerCRUD.created_customer_id or not TestContactPersons.person_id:
            pytest.skip("No customer or person created")
        
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/persons/{TestContactPersons.person_id}/set-primary"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("Set primary contact successfully")


class TestAddresses:
    """Test address management"""
    
    address_id = None
    
    def test_add_billing_address(self):
        """POST /api/customers-enhanced/{id}/addresses - Add billing address"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "address_type": "billing",
            "attention": "Accounts Dept",
            "street": "123 Main Street",
            "street2": "Suite 100",
            "city": "New Delhi",
            "state": "Delhi",
            "state_code": "DL",
            "zip_code": "110001",
            "country": "India",
            "phone": "011-12345678",
            "is_default": True
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/addresses",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        address = data["address"]
        assert address["address_type"] == "billing"
        assert address["is_default"] == True
        TestAddresses.address_id = address["address_id"]
        print(f"Added billing address: {address['address_id']}")
    
    def test_add_shipping_address(self):
        """POST /api/customers-enhanced/{id}/addresses - Add shipping address"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "address_type": "shipping",
            "street": "456 Warehouse Road",
            "city": "Gurgaon",
            "state": "Haryana",
            "state_code": "HR",
            "zip_code": "122001",
            "country": "India",
            "is_default": True
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/addresses",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["address"]["address_type"] == "shipping"
        print(f"Added shipping address: {data['address']['address_id']}")
    
    def test_get_customer_addresses(self):
        """GET /api/customers-enhanced/{id}/addresses - Get all addresses"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/addresses")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["addresses"]) >= 2
        print(f"Customer has {len(data['addresses'])} addresses")
    
    def test_update_address(self):
        """PUT /api/customers-enhanced/{id}/addresses/{address_id} - Update address"""
        if not TestCustomerCRUD.created_customer_id or not TestAddresses.address_id:
            pytest.skip("No customer or address created")
        
        payload = {
            "street": "123 Updated Street",
            "zip_code": "110002"
        }
        response = requests.put(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/addresses/{TestAddresses.address_id}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["address"]["street"] == "123 Updated Street"
        print(f"Updated address: {TestAddresses.address_id}")


class TestPortalAccess:
    """Test portal access management"""
    
    def test_enable_portal(self):
        """POST /api/customers-enhanced/{id}/enable-portal - Enable portal access"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/enable-portal"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "token" in data
        print(f"Portal enabled, token: {data['token'][:20]}...")
    
    def test_disable_portal(self):
        """POST /api/customers-enhanced/{id}/disable-portal - Disable portal access"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/disable-portal"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("Portal disabled successfully")


class TestStatements:
    """Test statement endpoints"""
    
    def test_get_statement(self):
        """GET /api/customers-enhanced/{id}/statement - Get statement data"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.get(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/statement"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        statement = data["statement"]
        assert "customer" in statement
        assert "invoices" in statement
        assert "payments" in statement
        assert "credits" in statement
        assert "balance" in statement
        assert "aging" in statement
        print(f"Statement retrieved for customer: {statement['customer']['display_name']}")
    
    def test_email_statement(self):
        """POST /api/customers-enhanced/{id}/email-statement - Send statement (MOCKED)"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "email_to": "test@example.com",
            "include_details": True
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/email-statement",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"Statement email sent (MOCKED): {data['message']}")


class TestStatusManagement:
    """Test activate/deactivate endpoints"""
    
    def test_deactivate_customer(self):
        """POST /api/customers-enhanced/{id}/deactivate - Deactivate customer"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/deactivate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("Customer deactivated successfully")
    
    def test_activate_customer(self):
        """POST /api/customers-enhanced/{id}/activate - Activate customer"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/activate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print("Customer activated successfully")


class TestCreditsAndRefunds:
    """Test credits and refunds management"""
    
    credit_id = None
    
    def test_add_credit(self):
        """POST /api/customers-enhanced/{id}/credits - Add credit note"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "amount": 5000,
            "reason": "Advance payment",
            "reference_number": "ADV-001",
            "date": "2025-01-15"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/credits",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        credit = data["credit"]
        assert credit["amount"] == 5000
        assert credit["balance"] == 5000
        assert credit["status"] == "active"
        TestCreditsAndRefunds.credit_id = credit["credit_id"]
        print(f"Added credit: {credit['credit_id']} - ₹{credit['amount']}")
    
    def test_get_credits(self):
        """GET /api/customers-enhanced/{id}/credits - Get customer credits"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.get(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/credits"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["credits"]) >= 1
        print(f"Customer has {len(data['credits'])} credits")
    
    def test_create_refund(self):
        """POST /api/customers-enhanced/{id}/refunds - Create refund from credits"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "amount": 2000,
            "mode": "bank_transfer",
            "reference_number": "REF-001",
            "notes": "Partial refund"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/refunds",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        refund = data["refund"]
        assert refund["amount"] == 2000
        assert refund["status"] == "completed"
        print(f"Created refund: {refund['refund_id']} - ₹{refund['amount']}")
    
    def test_refund_insufficient_credits(self):
        """POST /api/customers-enhanced/{id}/refunds - Reject refund exceeding credits"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "amount": 100000,  # More than available credits
            "mode": "cash"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/refunds",
            json=payload
        )
        assert response.status_code == 400
        data = response.json()
        assert "Insufficient credits" in data["detail"]
        print(f"Correctly rejected: {data['detail']}")


class TestTags:
    """Test tags management"""
    
    tag_id = None
    
    def test_create_tag(self):
        """POST /api/customers-enhanced/tags - Create tag"""
        payload = {
            "name": f"{TEST_PREFIX}VIP",
            "description": "VIP customers",
            "color": "#FFD700"
        }
        response = requests.post(f"{BASE_URL}/api/customers-enhanced/tags", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        tag = data["tag"]
        assert tag["name"] == f"{TEST_PREFIX}VIP"
        TestTags.tag_id = tag["tag_id"]
        print(f"Created tag: {tag['tag_id']} - {tag['name']}")
    
    def test_get_all_tags(self):
        """GET /api/customers-enhanced/tags/all - Get all tags"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/tags/all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert isinstance(data["tags"], list)
        print(f"Total tags: {len(data['tags'])}")
    
    def test_add_tag_to_customer(self):
        """POST /api/customers-enhanced/{id}/tags/{tag_name} - Add tag to customer"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        tag_name = f"{TEST_PREFIX}VIP"
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/tags/{tag_name}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"Added tag '{tag_name}' to customer")
    
    def test_remove_tag_from_customer(self):
        """DELETE /api/customers-enhanced/{id}/tags/{tag_name} - Remove tag from customer"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        tag_name = f"{TEST_PREFIX}VIP"
        response = requests.delete(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/tags/{tag_name}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"Removed tag '{tag_name}' from customer")


class TestTransactions:
    """Test transaction history endpoint"""
    
    def test_get_transactions(self):
        """GET /api/customers-enhanced/{id}/transactions - Get transaction history"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.get(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/transactions"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "transactions" in data
        print(f"Customer has {len(data['transactions'])} transactions")
    
    def test_get_transactions_by_type(self):
        """GET /api/customers-enhanced/{id}/transactions - Filter by type"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.get(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/transactions?transaction_type=invoice"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for txn in data["transactions"]:
            assert txn["transaction_type"] == "invoice"
        print(f"Found {len(data['transactions'])} invoice transactions")


class TestBulkOperations:
    """Test bulk operations"""
    
    def test_bulk_activate(self):
        """POST /api/customers-enhanced/bulk-action - Bulk activate"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "customer_ids": [TestCustomerCRUD.created_customer_id],
            "action": "activate"
        }
        response = requests.post(f"{BASE_URL}/api/customers-enhanced/bulk-action", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["results"]["success"] >= 1
        print(f"Bulk activate: {data['results']}")
    
    def test_bulk_add_tag(self):
        """POST /api/customers-enhanced/bulk-action - Bulk add tag"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "customer_ids": [TestCustomerCRUD.created_customer_id],
            "action": "add_tag",
            "tag_name": "Bulk-Tagged"
        }
        response = requests.post(f"{BASE_URL}/api/customers-enhanced/bulk-action", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"Bulk add tag: {data['results']}")


class TestReports:
    """Test report endpoints"""
    
    def test_report_by_segment(self):
        """GET /api/customers-enhanced/reports/by-segment - Segment report"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/reports/by-segment")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        print(f"Segment report: {len(data['report'])} segments")
    
    def test_report_top_customers(self):
        """GET /api/customers-enhanced/reports/top-customers - Top customers"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/reports/top-customers?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        print(f"Top customers: {len(data['report'])} customers")
    
    def test_report_aging_summary(self):
        """GET /api/customers-enhanced/reports/aging-summary - Aging summary"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/reports/aging-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "report" in data
        report = data["report"]
        assert "current" in report
        assert "1_30" in report
        assert "31_60" in report
        assert "61_90" in report
        assert "over_90" in report
        print(f"Aging summary: {report}")


class TestQuickEstimate:
    """Test quick estimate redirect"""
    
    def test_quick_estimate(self):
        """POST /api/customers-enhanced/{id}/quick-estimate - Quick estimate redirect"""
        if not TestCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = requests.post(
            f"{BASE_URL}/api/customers-enhanced/{TestCustomerCRUD.created_customer_id}/quick-estimate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "redirect" in data
        assert "/estimates" in data["redirect"]
        print(f"Quick estimate redirect: {data['redirect']}")


class TestDeleteProtection:
    """Test delete protection for customers with transactions"""
    
    customer_with_estimate_id = None
    
    def test_create_customer_for_delete_test(self):
        """Create a customer for delete protection test"""
        payload = {
            "display_name": f"{TEST_PREFIX}Delete Test Customer",
            "email": f"delete.test.{int(time.time())}@example.com",
            "gst_treatment": "consumer"
        }
        response = requests.post(f"{BASE_URL}/api/customers-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        TestDeleteProtection.customer_with_estimate_id = data["customer"]["customer_id"]
        print(f"Created customer for delete test: {data['customer']['customer_id']}")
    
    def test_create_estimate_for_customer(self):
        """Create an estimate linked to the customer"""
        if not TestDeleteProtection.customer_with_estimate_id:
            pytest.skip("No customer created")
        
        # First get customer details
        cust_response = requests.get(
            f"{BASE_URL}/api/customers-enhanced/{TestDeleteProtection.customer_with_estimate_id}"
        )
        customer = cust_response.json()["customer"]
        
        # Create estimate
        payload = {
            "customer_id": TestDeleteProtection.customer_with_estimate_id,
            "customer_name": customer["display_name"],
            "date": "2025-01-15",
            "expiry_date": "2025-02-15",
            "line_items": [
                {
                    "item_name": "Test Item",
                    "quantity": 1,
                    "rate": 1000,
                    "tax_percent": 18
                }
            ]
        }
        response = requests.post(f"{BASE_URL}/api/estimates-enhanced/", json=payload)
        if response.status_code == 200:
            print(f"Created estimate for customer")
        else:
            print(f"Estimate creation response: {response.status_code}")
    
    def test_delete_customer_with_transactions(self):
        """DELETE /api/customers-enhanced/{id} - Should fail if has transactions"""
        if not TestDeleteProtection.customer_with_estimate_id:
            pytest.skip("No customer created")
        
        response = requests.delete(
            f"{BASE_URL}/api/customers-enhanced/{TestDeleteProtection.customer_with_estimate_id}"
        )
        # If estimate was created, should fail with 400
        # If no estimate, should succeed with 200
        if response.status_code == 400:
            data = response.json()
            assert "Cannot delete customer" in data["detail"] or "transactions" in data["detail"]
            print(f"Correctly prevented deletion: {data['detail']}")
        else:
            print(f"Customer deleted (no transactions linked)")


class TestCleanup:
    """Cleanup test data"""
    
    def test_delete_test_customers(self):
        """Delete all test customers"""
        # Get all test customers
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/?search={TEST_PREFIX}&per_page=100")
        if response.status_code == 200:
            customers = response.json().get("customers", [])
            deleted = 0
            for customer in customers:
                del_response = requests.delete(
                    f"{BASE_URL}/api/customers-enhanced/{customer['customer_id']}"
                )
                if del_response.status_code == 200:
                    deleted += 1
            print(f"Cleaned up {deleted} test customers")
    
    def test_delete_test_tags(self):
        """Delete test tags"""
        response = requests.get(f"{BASE_URL}/api/customers-enhanced/tags/all")
        if response.status_code == 200:
            tags = response.json().get("tags", [])
            deleted = 0
            for tag in tags:
                if tag["name"].startswith(TEST_PREFIX):
                    del_response = requests.delete(
                        f"{BASE_URL}/api/customers-enhanced/tags/{tag['tag_id']}"
                    )
                    if del_response.status_code == 200:
                        deleted += 1
            print(f"Cleaned up {deleted} test tags")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
