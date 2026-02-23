"""
Comprehensive Tests for Enhanced Contacts Module
Tests: Tags, Contacts CRUD, Contact Persons, Addresses, Portal Access, Email Statements, GSTIN Validation
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://preview-insights.preview.emergentagent.com')

# Test data tracking
created_tag_ids = []
created_contact_ids = []
created_person_ids = []
created_address_ids = []


class TestContactTags:
    """Contact Tags CRUD Tests"""
    
    def test_list_tags(self):
        """Test listing all contact tags"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "tags" in data
        assert isinstance(data["tags"], list)
        print(f"✓ Listed {len(data['tags'])} tags")
    
    def test_create_tag(self):
        """Test creating a new contact tag"""
        tag_name = f"TEST_Tag_{uuid.uuid4().hex[:8]}"
        payload = {
            "name": tag_name,
            "description": "Test tag for automated testing",
            "color": "#10B981"
        }
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/tags", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["tag"]["name"] == tag_name
        assert data["tag"]["color"] == "#10B981"
        assert "tag_id" in data["tag"]
        created_tag_ids.append(data["tag"]["tag_id"])
        print(f"✓ Created tag: {tag_name} with ID: {data['tag']['tag_id']}")
    
    def test_get_tag_by_id(self):
        """Test getting a specific tag by ID"""
        if not created_tag_ids:
            pytest.skip("No tag created to test")
        tag_id = created_tag_ids[0]
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/tags/{tag_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["tag"]["tag_id"] == tag_id
        print(f"✓ Retrieved tag: {data['tag']['name']}")
    
    def test_update_tag(self):
        """Test updating a contact tag"""
        if not created_tag_ids:
            pytest.skip("No tag created to test")
        tag_id = created_tag_ids[0]
        payload = {
            "description": "Updated description for testing",
            "color": "#F59E0B"
        }
        response = requests.put(f"{BASE_URL}/api/contacts-enhanced/tags/{tag_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["tag"]["color"] == "#F59E0B"
        print(f"✓ Updated tag: {tag_id}")
    
    def test_duplicate_tag_name_rejected(self):
        """Test that duplicate tag names are rejected"""
        # First create a tag
        tag_name = f"TEST_Duplicate_{uuid.uuid4().hex[:8]}"
        payload = {"name": tag_name, "description": "First tag", "color": "#3B82F6"}
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/tags", json=payload)
        assert response.status_code == 200
        created_tag_ids.append(response.json()["tag"]["tag_id"])
        
        # Try to create another with same name
        response2 = requests.post(f"{BASE_URL}/api/contacts-enhanced/tags", json=payload)
        assert response2.status_code == 400
        print(f"✓ Duplicate tag name correctly rejected")


class TestContacts:
    """Contacts CRUD Tests"""
    
    def test_list_contacts(self):
        """Test listing all contacts"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "contacts" in data
        assert "page_context" in data
        print(f"✓ Listed {len(data['contacts'])} contacts")
    
    def test_get_contacts_summary(self):
        """Test getting contacts summary statistics"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "summary" in data
        summary = data["summary"]
        assert "total_contacts" in summary
        assert "customers" in summary
        assert "vendors" in summary
        assert "active" in summary
        print(f"✓ Summary: {summary['total_contacts']} contacts, {summary['customers']} customers, {summary['vendors']} vendors")
    
    def test_get_indian_states(self):
        """Test getting list of Indian states"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/states")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "states" in data
        assert len(data["states"]) > 30  # India has 36 states/UTs
        print(f"✓ Retrieved {len(data['states'])} Indian states")
    
    def test_create_customer_contact(self):
        """Test creating a customer contact"""
        contact_name = f"TEST_Customer_{uuid.uuid4().hex[:8]}"
        payload = {
            "name": contact_name,
            "company_name": "Test Company Pvt Ltd",
            "contact_type": "customer",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+91-9876543210",
            "gstin": "29AABCT1234A1Z5",  # Karnataka GSTIN
            "payment_terms": 30,
            "gst_treatment": "registered",
            "tax_treatment": "business_gst"
        }
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["contact"]["name"] == contact_name
        assert data["contact"]["contact_type"] == "customer"
        assert data["contact"]["place_of_supply"] == "KA"  # Auto-detected from GSTIN
        created_contact_ids.append(data["contact"]["contact_id"])
        print(f"✓ Created customer: {contact_name} with ID: {data['contact']['contact_id']}")
    
    def test_create_vendor_contact(self):
        """Test creating a vendor contact"""
        contact_name = f"TEST_Vendor_{uuid.uuid4().hex[:8]}"
        payload = {
            "name": contact_name,
            "company_name": "Test Supplier Ltd",
            "contact_type": "vendor",
            "email": f"vendor_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+91-11-12345678",
            "gstin": "27AABCT5678B1Z5",  # Maharashtra GSTIN
            "payment_terms": 45,
            "gst_treatment": "registered"
        }
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["contact"]["contact_type"] == "vendor"
        assert data["contact"]["place_of_supply"] == "MH"  # Auto-detected from GSTIN
        created_contact_ids.append(data["contact"]["contact_id"])
        print(f"✓ Created vendor: {contact_name}")
    
    def test_create_both_type_contact(self):
        """Test creating a contact that is both customer and vendor"""
        contact_name = f"TEST_Both_{uuid.uuid4().hex[:8]}"
        payload = {
            "name": contact_name,
            "contact_type": "both",
            "email": f"both_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+91-9999999999"
        }
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["contact"]["contact_type"] == "both"
        created_contact_ids.append(data["contact"]["contact_id"])
        print(f"✓ Created customer+vendor: {contact_name}")
    
    def test_get_contact_by_id(self):
        """Test getting a specific contact with full details"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["contact"]["contact_id"] == contact_id
        assert "persons" in data["contact"]
        assert "addresses" in data["contact"]
        assert "balance" in data["contact"]
        assert "usage" in data["contact"]
        print(f"✓ Retrieved contact: {data['contact']['name']}")
    
    def test_update_contact(self):
        """Test updating a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        payload = {
            "payment_terms": 60,
            "notes": "Updated via automated test"
        }
        response = requests.put(f"{BASE_URL}/api/contacts-enhanced/{contact_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["contact"]["payment_terms"] == 60
        print(f"✓ Updated contact: {contact_id}")
    
    def test_filter_contacts_by_type(self):
        """Test filtering contacts by type"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/?contact_type=customer")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All returned contacts should be customers or both
        for contact in data["contacts"]:
            assert contact["contact_type"] in ["customer", "both"]
        print(f"✓ Filtered customers: {len(data['contacts'])} results")
    
    def test_search_contacts(self):
        """Test searching contacts"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/?search=TEST_")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Search results: {len(data['contacts'])} contacts")


class TestGSTINValidation:
    """GSTIN Validation Tests"""
    
    def test_valid_gstin(self):
        """Test validation of a valid GSTIN"""
        gstin = "07AAAAA0000A1Z5"  # Delhi GSTIN
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/validate-gstin/{gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["valid"] == True
        assert data["details"]["state_code"] == "DL"
        assert data["details"]["state_name"] == "Delhi"
        assert data["details"]["pan"] == "AAAAA0000A"
        print(f"✓ Valid GSTIN: {gstin} -> State: {data['details']['state_name']}")
    
    def test_invalid_gstin_format(self):
        """Test validation of an invalid GSTIN format"""
        gstin = "INVALID123"
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/validate-gstin/{gstin}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["valid"] == False
        print(f"✓ Invalid GSTIN correctly rejected")
    
    def test_gstin_state_detection(self):
        """Test GSTIN state detection for different states"""
        test_cases = [
            ("29AABCT1234A1Z5", "KA", "Karnataka"),
            ("27AABCT5678B1Z5", "MH", "Maharashtra"),
            ("33AABCT9012C1Z5", "TN", "Tamil Nadu"),
        ]
        for gstin, expected_code, expected_name in test_cases:
            response = requests.get(f"{BASE_URL}/api/contacts-enhanced/validate-gstin/{gstin}")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] == True
            assert data["details"]["state_code"] == expected_code
            print(f"✓ GSTIN {gstin[:2]}... -> {expected_name}")


class TestContactPersons:
    """Contact Persons CRUD Tests"""
    
    def test_add_contact_person(self):
        """Test adding a person to a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        payload = {
            "first_name": "TEST_John",
            "last_name": "Doe",
            "email": f"john_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+91-9876543211",
            "designation": "Manager",
            "department": "Sales",
            "is_primary": True
        }
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/persons", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["person"]["first_name"] == "TEST_John"
        assert data["person"]["is_primary"] == True
        created_person_ids.append((contact_id, data["person"]["person_id"]))
        print(f"✓ Added person: {payload['first_name']} {payload['last_name']}")
    
    def test_list_contact_persons(self):
        """Test listing persons for a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/persons")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "persons" in data
        print(f"✓ Listed {len(data['persons'])} persons for contact")
    
    def test_update_contact_person(self):
        """Test updating a contact person"""
        if not created_person_ids:
            pytest.skip("No person created to test")
        contact_id, person_id = created_person_ids[0]
        payload = {
            "designation": "Senior Manager",
            "department": "Operations"
        }
        response = requests.put(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/persons/{person_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["person"]["designation"] == "Senior Manager"
        print(f"✓ Updated person: {person_id}")


class TestAddresses:
    """Contact Addresses CRUD Tests"""
    
    def test_add_billing_address(self):
        """Test adding a billing address to a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        payload = {
            "address_type": "billing",
            "attention": "Accounts Dept",
            "street": "123 Test Street",
            "street2": "Floor 2",
            "city": "Bangalore",
            "state": "Karnataka",
            "state_code": "KA",
            "zip_code": "560001",
            "country": "India",
            "is_default": True
        }
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/addresses", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["address"]["address_type"] == "billing"
        assert data["address"]["is_default"] == True
        created_address_ids.append((contact_id, data["address"]["address_id"]))
        print(f"✓ Added billing address: {payload['city']}")
    
    def test_add_shipping_address(self):
        """Test adding a shipping address to a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        payload = {
            "address_type": "shipping",
            "street": "456 Warehouse Road",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "state_code": "TN",
            "zip_code": "600001",
            "country": "India",
            "is_default": True
        }
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/addresses", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["address"]["address_type"] == "shipping"
        created_address_ids.append((contact_id, data["address"]["address_id"]))
        print(f"✓ Added shipping address: {payload['city']}")
    
    def test_list_addresses(self):
        """Test listing addresses for a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/addresses")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "addresses" in data
        print(f"✓ Listed {len(data['addresses'])} addresses")
    
    def test_filter_addresses_by_type(self):
        """Test filtering addresses by type"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/addresses?address_type=billing")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        for addr in data["addresses"]:
            assert addr["address_type"] == "billing"
        print(f"✓ Filtered billing addresses: {len(data['addresses'])} results")


class TestPortalAccess:
    """Portal Access Tests"""
    
    def test_enable_portal_access(self):
        """Test enabling portal access for a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/enable-portal")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "portal_token" in data
        print(f"✓ Portal enabled with token: {data['portal_token'][:20]}...")
    
    def test_disable_portal_access(self):
        """Test disabling portal access for a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/disable-portal")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        print(f"✓ Portal disabled for contact: {contact_id}")


class TestEmailStatements:
    """Email Statement Tests (MOCKED)"""
    
    def test_email_statement(self):
        """Test sending email statement (mocked)"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.post(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/email-statement")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "statement_preview" in data
        assert "balance" in data
        print(f"✓ Statement emailed (MOCKED): Preview length: {len(data['statement_preview'])} chars")
    
    def test_statement_history(self):
        """Test getting statement history"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/statement-history")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "statements" in data
        print(f"✓ Statement history: {len(data['statements'])} records")


class TestContactActivation:
    """Contact Activate/Deactivate Tests"""
    
    def test_deactivate_contact(self):
        """Test deactivating a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.put(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify deactivation
        get_response = requests.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}")
        assert get_response.json()["contact"]["is_active"] == False
        print(f"✓ Contact deactivated: {contact_id}")
    
    def test_activate_contact(self):
        """Test activating a contact"""
        if not created_contact_ids:
            pytest.skip("No contact created to test")
        contact_id = created_contact_ids[0]
        response = requests.put(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        
        # Verify activation
        get_response = requests.get(f"{BASE_URL}/api/contacts-enhanced/{contact_id}")
        assert get_response.json()["contact"]["is_active"] == True
        print(f"✓ Contact activated: {contact_id}")


class TestBackwardCompatibility:
    """Backward Compatibility Endpoint Tests"""
    
    def test_customers_endpoint(self):
        """Test backward compatible /customers endpoint"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/customers")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All returned should be customers or both
        for contact in data["contacts"]:
            assert contact["contact_type"] in ["customer", "both"]
        print(f"✓ /customers endpoint: {len(data['contacts'])} results")
    
    def test_vendors_endpoint(self):
        """Test backward compatible /vendors endpoint"""
        response = requests.get(f"{BASE_URL}/api/contacts-enhanced/vendors")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # All returned should be vendors or both
        for contact in data["contacts"]:
            assert contact["contact_type"] in ["vendor", "both"]
        print(f"✓ /vendors endpoint: {len(data['contacts'])} results")


class TestCleanup:
    """Cleanup test data"""
    
    def test_delete_test_persons(self):
        """Delete test persons"""
        for contact_id, person_id in created_person_ids:
            response = requests.delete(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/persons/{person_id}")
            if response.status_code == 200:
                print(f"✓ Deleted person: {person_id}")
    
    def test_delete_test_addresses(self):
        """Delete test addresses"""
        for contact_id, address_id in created_address_ids:
            response = requests.delete(f"{BASE_URL}/api/contacts-enhanced/{contact_id}/addresses/{address_id}")
            if response.status_code == 200:
                print(f"✓ Deleted address: {address_id}")
    
    def test_delete_test_contacts(self):
        """Delete test contacts"""
        for contact_id in created_contact_ids:
            response = requests.delete(f"{BASE_URL}/api/contacts-enhanced/{contact_id}")
            if response.status_code == 200:
                print(f"✓ Deleted contact: {contact_id}")
    
    def test_delete_test_tags(self):
        """Delete test tags"""
        for tag_id in created_tag_ids:
            response = requests.delete(f"{BASE_URL}/api/contacts-enhanced/tags/{tag_id}")
            if response.status_code == 200:
                print(f"✓ Deleted tag: {tag_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
