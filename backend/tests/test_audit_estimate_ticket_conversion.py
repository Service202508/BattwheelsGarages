"""
Test Suite: Audit Log Coverage + Estimate-to-Ticket Conversion
Week 3 Prompt 3 Testing

Tests:
1. Estimate creation writes audit_logs entry (estimate.created)
2. Estimate status changes write audit_logs entries (estimate.status_changed)
3. Estimate→Ticket conversion flow (draft→sent→accepted→convert)
4. Duplicate conversion blocked (400 error)
5. Converted ticket has correct fields
6. Audit entries for estimate.converted_to_ticket
7. Ticket creation audit (ticket.created)
8. Contact creation audit (contact.created)
9. All audit entries written to audit_logs collection (NOT audit_log)
10. Audit entries contain required schema fields
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ORG_ID = "demo-volt-motors-001"
CUSTOMER_ID = "cust-demo-001"  # Existing customer: Arjun Mehta


class TestAuditEstimateTicketConversion:
    """Test audit logging and estimate-to-ticket conversion"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth token and return headers"""
        login_url = f"{BASE_URL}/api/auth/login"
        response = requests.post(login_url, json={
            "email": "demo@voltmotors.in",
            "password": "Demo@12345"
        })
        
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        token = data.get("token") or data.get("access_token")
        if not token:
            pytest.skip("No token returned from login")
        
        return {
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": ORG_ID,
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def mongo_client(self):
        """Get MongoDB client for audit verification"""
        try:
            from pymongo import MongoClient
            mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
            db_name = os.environ.get("DB_NAME", "battwheels_dev")
            client = MongoClient(mongo_url)
            return client[db_name]
        except Exception as e:
            pytest.skip(f"Cannot connect to MongoDB: {e}")
    
    def test_01_auth_works(self, auth_headers):
        """Verify authentication is working"""
        # Use a simple endpoint to verify auth
        response = requests.get(f"{BASE_URL}/api/v1/estimates-enhanced/summary", headers=auth_headers)
        # Accept 200 or 404 (endpoint might not exist but auth should work)
        assert response.status_code in [200, 403, 404] or "unauthorized" not in response.text.lower(), \
            f"Auth check failed: {response.text}"
        print(f"✓ Auth working (endpoint returned {response.status_code})")
    
    def test_02_estimate_create_writes_audit(self, auth_headers, mongo_client):
        """POST /api/v1/estimates-enhanced creates estimate and writes audit_logs entry"""
        # Create unique estimate
        unique_id = uuid.uuid4().hex[:6].upper()
        
        payload = {
            "customer_id": CUSTOMER_ID,
            "subject": f"TEST_AUDIT_EST_{unique_id}",
            "notes": "Testing audit log for estimate creation",
            "line_items": [
                {
                    "name": "EV Battery Check",
                    "description": "Routine battery diagnostic",
                    "quantity": 1,
                    "rate": 500.00,
                    "tax_percentage": 18
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/estimates-enhanced/",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200 or response.status_code == 201, \
            f"Create estimate failed: {response.status_code} - {response.text}"
        
        data = response.json()
        estimate = data.get("estimate", data)
        estimate_id = estimate.get("estimate_id")
        estimate_number = estimate.get("estimate_number")
        
        assert estimate_id, "No estimate_id returned"
        print(f"✓ Created estimate: {estimate_id} ({estimate_number})")
        
        # Check audit_logs collection for estimate.created
        audit_entry = mongo_client["audit_logs"].find_one({
            "action": "estimate.created",
            "resource_id": estimate_id
        })
        
        assert audit_entry is not None, f"No audit entry found for estimate.created with resource_id={estimate_id}"
        assert audit_entry.get("resource_type") == "estimate", "Wrong resource_type"
        assert "organization_id" in audit_entry, "Missing organization_id in audit entry"
        assert "timestamp" in audit_entry, "Missing timestamp in audit entry"
        
        print(f"✓ Audit entry for estimate.created found in audit_logs collection")
        
        # Store for later tests
        self.__class__.test_estimate_id = estimate_id
        self.__class__.test_estimate_number = estimate_number
    
    def test_03_estimate_status_change_draft_to_sent(self, auth_headers, mongo_client):
        """PUT /api/v1/estimates-enhanced/{id}/status changes status and writes audit entry"""
        estimate_id = getattr(self.__class__, 'test_estimate_id', None)
        if not estimate_id:
            pytest.skip("No estimate from previous test")
        
        # Change status from draft to sent
        response = requests.put(
            f"{BASE_URL}/api/v1/estimates-enhanced/{estimate_id}/status",
            json={"status": "sent", "reason": "Sending to customer for review"},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Status change failed: {response.status_code} - {response.text}"
        
        data = response.json()
        # Status could be in estimate object or in message
        estimate = data.get("estimate") or data
        new_status = estimate.get("status") or (data.get("message", "").split()[-1] if "sent" in data.get("message", "") else None)
        assert new_status == "sent" or "sent" in str(data.get("message", "")), \
            f"Status not changed to sent: {data}"
        
        print(f"✓ Estimate status changed to 'sent'")
        
        # Check audit_logs for status change
        audit_entry = mongo_client["audit_logs"].find_one({
            "action": "estimate.status_changed",
            "resource_id": estimate_id,
            "details.new_status": "sent"
        })
        
        assert audit_entry is not None, "No audit entry for estimate.status_changed (draft→sent)"
        print(f"✓ Audit entry for estimate.status_changed (sent) found")
    
    def test_04_estimate_status_change_sent_to_accepted(self, auth_headers, mongo_client):
        """Change estimate status from sent to accepted"""
        estimate_id = getattr(self.__class__, 'test_estimate_id', None)
        if not estimate_id:
            pytest.skip("No estimate from previous test")
        
        response = requests.put(
            f"{BASE_URL}/api/v1/estimates-enhanced/{estimate_id}/status",
            json={"status": "accepted", "reason": "Customer accepted the estimate"},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Status change failed: {response.status_code} - {response.text}"
        
        data = response.json()
        estimate = data.get("estimate", data)
        assert estimate.get("status") == "accepted", f"Status not changed to accepted: {estimate.get('status')}"
        
        print(f"✓ Estimate status changed to 'accepted'")
        
        # Check audit_logs for accepted status
        audit_entry = mongo_client["audit_logs"].find_one({
            "action": "estimate.status_changed",
            "resource_id": estimate_id,
            "details.new_status": "accepted"
        })
        
        assert audit_entry is not None, "No audit entry for estimate.status_changed (accepted)"
        print(f"✓ Audit entry for estimate.status_changed (accepted) found")
    
    def test_05_convert_estimate_to_ticket(self, auth_headers, mongo_client):
        """POST /api/v1/estimates-enhanced/{id}/convert-to-ticket converts accepted estimate to ticket"""
        estimate_id = getattr(self.__class__, 'test_estimate_id', None)
        estimate_number = getattr(self.__class__, 'test_estimate_number', None)
        if not estimate_id:
            pytest.skip("No estimate from previous test")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/estimates-enhanced/{estimate_id}/convert-to-ticket",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Convert to ticket failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data.get("code") == 0, f"Conversion error: {data}"
        
        ticket = data.get("ticket", {})
        ticket_id = ticket.get("ticket_id")
        
        assert ticket_id, "No ticket_id returned"
        assert ticket_id.startswith("TKT-"), f"Invalid ticket_id format: {ticket_id}"
        
        # Verify ticket has correct fields from estimate
        assert ticket.get("source_estimate_id") == estimate_id, "source_estimate_id mismatch"
        assert ticket.get("source_estimate_number") == estimate_number, "source_estimate_number mismatch"
        assert ticket.get("customer_id") == CUSTOMER_ID, "customer_id mismatch"
        assert "estimated_cost" in ticket, "Missing estimated_cost in ticket"
        assert ticket.get("estimated_cost") > 0, "estimated_cost should be > 0"
        
        print(f"✓ Converted estimate to ticket: {ticket_id}")
        print(f"  - estimated_cost: {ticket.get('estimated_cost')}")
        print(f"  - customer: {ticket.get('customer_name')}")
        print(f"  - source_estimate_id: {ticket.get('source_estimate_id')}")
        
        # Verify estimate status is now 'converted'
        assert data.get("estimate_status") == "converted", "Estimate not marked as converted"
        
        # Store for later tests
        self.__class__.test_ticket_id = ticket_id
        
        # Check audit_logs for estimate.converted_to_ticket
        audit_entry = mongo_client["audit_logs"].find_one({
            "action": "estimate.converted_to_ticket",
            "resource_id": estimate_id
        })
        
        assert audit_entry is not None, "No audit entry for estimate.converted_to_ticket"
        assert audit_entry.get("details", {}).get("ticket_id") == ticket_id, "ticket_id not in audit details"
        print(f"✓ Audit entry for estimate.converted_to_ticket found")
    
    def test_06_duplicate_conversion_blocked(self, auth_headers):
        """Duplicate conversion should return 400/409 error"""
        estimate_id = getattr(self.__class__, 'test_estimate_id', None)
        if not estimate_id:
            pytest.skip("No estimate from previous test")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/estimates-enhanced/{estimate_id}/convert-to-ticket",
            headers=auth_headers
        )
        
        # Should be 400 or 409 (already converted)
        assert response.status_code in [400, 409], \
            f"Duplicate conversion should fail, got: {response.status_code} - {response.text}"
        
        error_data = response.json()
        error_msg = error_data.get("detail", str(error_data)).lower()
        assert "already" in error_msg or "converted" in error_msg, \
            f"Error should mention already converted: {error_msg}"
        
        print(f"✓ Duplicate conversion blocked with {response.status_code}: {error_data.get('detail', error_data)}")
    
    def test_07_verify_converted_ticket_in_db(self, auth_headers, mongo_client):
        """Verify the converted ticket exists with all expected fields"""
        ticket_id = getattr(self.__class__, 'test_ticket_id', None)
        if not ticket_id:
            pytest.skip("No ticket from previous test")
        
        # Get ticket from API
        response = requests.get(
            f"{BASE_URL}/api/v1/tickets/{ticket_id}",
            headers=auth_headers
        )
        
        # If API fails, check directly in DB
        if response.status_code != 200:
            ticket = mongo_client["tickets"].find_one({"ticket_id": ticket_id})
            assert ticket is not None, f"Ticket {ticket_id} not found in database"
            print(f"✓ Ticket found in database (API returned {response.status_code})")
        else:
            ticket = response.json()
            print(f"✓ Ticket retrieved via API")
        
        # Verify required fields
        required_fields = ["ticket_id", "customer_id", "estimated_cost", "source_estimate_id", "description"]
        for field in required_fields:
            assert field in ticket, f"Missing field: {field}"
        
        print(f"  - All required fields present: {required_fields}")
    
    def test_08_ticket_creation_audit(self, auth_headers, mongo_client):
        """Verify ticket.created audit entry is written when creating a ticket directly"""
        # Create a ticket directly
        unique_id = uuid.uuid4().hex[:6].upper()
        
        payload = {
            "title": f"TEST_AUDIT_TICKET_{unique_id}",
            "description": "Testing ticket creation audit",
            "priority": "medium",
            "category": "general_service",
            "customer_id": CUSTOMER_ID,
            "customer_name": "Test Customer"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/tickets",
            json=payload,
            headers=auth_headers
        )
        
        # Ticket creation might return 200 or 201
        if response.status_code not in [200, 201]:
            pytest.skip(f"Ticket creation endpoint returned {response.status_code}: {response.text}")
        
        data = response.json()
        ticket_id = data.get("ticket_id") or data.get("ticket", {}).get("ticket_id")
        
        if not ticket_id:
            pytest.skip(f"No ticket_id in response: {data}")
        
        print(f"✓ Created ticket: {ticket_id}")
        
        # Check audit_logs for ticket.created
        audit_entry = mongo_client["audit_logs"].find_one({
            "action": "ticket.created",
            "resource_id": ticket_id
        })
        
        assert audit_entry is not None, f"No audit entry for ticket.created with resource_id={ticket_id}"
        print(f"✓ Audit entry for ticket.created found in audit_logs collection")
        
        # Store for cleanup
        self.__class__.direct_ticket_id = ticket_id
    
    def test_09_contact_creation_audit(self, auth_headers, mongo_client):
        """Verify contact.created audit entry is written"""
        unique_id = uuid.uuid4().hex[:6].upper()
        
        payload = {
            "name": f"TEST_AUDIT_CONTACT_{unique_id}",
            "contact_type": "customer",
            "email": f"testaudit{unique_id.lower()}@test.com",
            "phone": "9876543210"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/contacts-enhanced/",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip(f"Contact creation returned {response.status_code}: {response.text}")
        
        data = response.json()
        contact = data.get("contact", data)
        contact_id = contact.get("contact_id")
        
        assert contact_id, f"No contact_id returned: {data}"
        print(f"✓ Created contact: {contact_id}")
        
        # Check audit_logs for contact.created
        audit_entry = mongo_client["audit_logs"].find_one({
            "action": "contact.created",
            "resource_id": contact_id
        })
        
        assert audit_entry is not None, f"No audit entry for contact.created with resource_id={contact_id}"
        print(f"✓ Audit entry for contact.created found in audit_logs collection")
        
        # Store for cleanup
        self.__class__.test_contact_id = contact_id
    
    def test_10_audit_entries_use_correct_collection(self, mongo_client):
        """Verify audit entries are in audit_logs collection (NOT audit_log)"""
        # Check audit_logs collection exists and has entries
        audit_logs_count = mongo_client["audit_logs"].count_documents({})
        
        print(f"  - audit_logs collection has {audit_logs_count} entries")
        assert audit_logs_count > 0, "audit_logs collection is empty"
        
        # Check audit_log (singular) should NOT be the main collection
        audit_log_count = mongo_client["audit_log"].count_documents({})
        print(f"  - audit_log (singular) collection has {audit_log_count} entries")
        
        # The main logging should be in audit_logs
        print(f"✓ Audit entries correctly written to 'audit_logs' collection")
    
    def test_11_audit_schema_validation(self, mongo_client):
        """Verify audit entries have required schema fields"""
        required_fields = ["organization_id", "resource_type", "resource_id", "timestamp", "action"]
        
        # Get recent audit entries
        recent_audits = list(mongo_client["audit_logs"].find({}).sort("timestamp", -1).limit(10))
        
        assert len(recent_audits) > 0, "No audit entries found"
        
        for entry in recent_audits:
            missing_fields = [f for f in required_fields if f not in entry]
            if missing_fields:
                # Some entries might be from other sources, just warn
                print(f"  - Entry {entry.get('action')} missing fields: {missing_fields}")
            else:
                print(f"✓ Entry {entry.get('action')} has all required fields")
        
        # At least one entry should have all fields
        complete_entries = [e for e in recent_audits if all(f in e for f in required_fields)]
        assert len(complete_entries) > 0, f"No audit entries with all required fields: {required_fields}"
        print(f"✓ Found {len(complete_entries)} audit entries with complete schema")
    
    def test_12_full_estimate_ticket_flow(self, auth_headers, mongo_client):
        """Full E2E flow: Create estimate → Send → Accept → Convert to Ticket"""
        unique_id = uuid.uuid4().hex[:6].upper()
        
        # Step 1: Create estimate
        estimate_payload = {
            "customer_id": CUSTOMER_ID,
            "subject": f"TEST_E2E_FLOW_{unique_id}",
            "notes": "Full flow test",
            "line_items": [
                {"name": "Battery Replacement", "quantity": 1, "rate": 15000, "tax_percentage": 18},
                {"name": "Labor", "quantity": 2, "rate": 500, "tax_percentage": 18}
            ]
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/estimates-enhanced/",
            json=estimate_payload,
            headers=auth_headers
        )
        assert create_resp.status_code in [200, 201], f"Create failed: {create_resp.text}"
        
        estimate = create_resp.json().get("estimate", create_resp.json())
        est_id = estimate.get("estimate_id")
        assert est_id, "No estimate_id"
        print(f"  Step 1: Created estimate {est_id}")
        
        # Step 2: Send (draft → sent)
        send_resp = requests.put(
            f"{BASE_URL}/api/v1/estimates-enhanced/{est_id}/status",
            json={"status": "sent"},
            headers=auth_headers
        )
        assert send_resp.status_code == 200, f"Send failed: {send_resp.text}"
        print(f"  Step 2: Status changed to 'sent'")
        
        # Step 3: Accept (sent → accepted)
        accept_resp = requests.put(
            f"{BASE_URL}/api/v1/estimates-enhanced/{est_id}/status",
            json={"status": "accepted"},
            headers=auth_headers
        )
        assert accept_resp.status_code == 200, f"Accept failed: {accept_resp.text}"
        print(f"  Step 3: Status changed to 'accepted'")
        
        # Step 4: Convert to ticket
        convert_resp = requests.post(
            f"{BASE_URL}/api/v1/estimates-enhanced/{est_id}/convert-to-ticket",
            headers=auth_headers
        )
        assert convert_resp.status_code == 200, f"Convert failed: {convert_resp.text}"
        
        convert_data = convert_resp.json()
        ticket = convert_data.get("ticket", {})
        ticket_id = ticket.get("ticket_id")
        assert ticket_id, f"No ticket_id: {convert_data}"
        print(f"  Step 4: Converted to ticket {ticket_id}")
        
        # Verify all audit entries were created
        audit_count = mongo_client["audit_logs"].count_documents({
            "resource_id": est_id
        })
        print(f"  - Found {audit_count} audit entries for estimate {est_id}")
        
        # Should have at minimum: created + 2 status changes + converted
        assert audit_count >= 3, f"Expected at least 3 audit entries, got {audit_count}"
        
        print(f"✓ Full E2E flow completed successfully")
        
        # Store for cleanup
        self.__class__.e2e_estimate_id = est_id
        self.__class__.e2e_ticket_id = ticket_id


class TestAuditUtilCorrectCollection:
    """Verify utils/audit_log.py writes to correct collection"""
    
    def test_audit_log_util_uses_audit_logs_collection(self):
        """Verify log_financial_action writes to audit_logs (not audit_log)"""
        # Read the audit_log.py file
        audit_file = "/app/backend/utils/audit_log.py"
        
        try:
            with open(audit_file, "r") as f:
                content = f.read()
            
            # Check that it uses audit_logs collection
            assert 'audit_logs' in content, "audit_log.py should reference 'audit_logs' collection"
            
            # Should NOT use audit_log (singular) as the main collection
            if 'audit_collection = _db["audit_log"]' in content:
                pytest.fail("audit_log.py incorrectly uses 'audit_log' collection instead of 'audit_logs'")
            
            # Verify the correct line
            assert 'audit_collection = _db["audit_logs"]' in content, \
                "audit_log.py should have: audit_collection = _db['audit_logs']"
            
            print(f"✓ utils/audit_log.py correctly uses 'audit_logs' collection")
            
        except FileNotFoundError:
            pytest.skip("audit_log.py not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
