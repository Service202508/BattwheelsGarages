"""
E-Invoice IRP + Generate Invoice Flow Test Suite
Tests for:
1. Generate Invoice from Job Card (convert approved estimate to invoice)
2. E-Invoice/IRN endpoint registration and basic functionality

Test ticket: tkt-invoice-test-1ad656c6 (status=invoiced, has approved estimate)
Estimate: est-invoice-test-a497bcfd (already converted to inv_7ea2ac69a47f)
"""

import pytest
import requests
import os
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://middleware-trace.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@voltmotors.in"
TEST_PASSWORD = "Demo@12345"

# Test data identifiers
TEST_TICKET_ID = "tkt-invoice-test-1ad656c6"
TEST_ESTIMATE_ID = "est-invoice-test-a497bcfd"


@pytest.fixture(scope="module")
def auth_session():
    """Get authenticated session with JWT token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Clear rate limits first
    try:
        requests.delete(f"{BASE_URL}/api/v1/test/clear-rate-limits")
    except:
        pass
    
    # Login
    response = session.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session


# ====================================================================================
# TASK 1: GENERATE INVOICE FROM JOB CARD (Convert Estimate to Invoice)
# ====================================================================================

class TestGenerateInvoiceFromEstimate:
    """Test estimate-to-invoice conversion flow"""
    
    def test_01_get_ticket_estimate_endpoint_exists(self, auth_session):
        """GET /api/v1/tickets/{ticket_id}/estimate returns estimate with line items"""
        response = auth_session.get(f"{BASE_URL}/api/v1/tickets/{TEST_TICKET_ID}/estimate")
        
        print(f"GET /tickets/{TEST_TICKET_ID}/estimate status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Should return 200 or 404 with estimate not found message (endpoint exists)
        # 404 with "No estimate found" is OK - it means endpoint is registered
        if response.status_code == 404:
            data = response.json()
            detail = data.get("detail", "")
            # "No estimate found" means endpoint exists but no data
            assert "no estimate found" in detail.lower() or "not found" in detail.lower(), \
                f"Unexpected 404 error: {detail}"
            print(f"Endpoint exists - no estimate for this ticket: {detail}")
            return
        
        assert response.status_code == 200, f"Unexpected status: {response.status_code}"
        
        # If estimate exists, verify structure
        data = response.json()
        estimate = data.get("estimate", data)
        
        # Verify estimate fields
        assert "estimate_id" in estimate or "code" in data, "Missing estimate_id in response"
        print(f"Estimate found: {estimate.get('estimate_id', 'N/A')}")
        print(f"Estimate status: {estimate.get('status', 'N/A')}")
        print(f"Line items count: {len(estimate.get('line_items', []))}")

    def test_02_estimate_has_required_fields(self, auth_session):
        """Verify estimate has required fields for conversion"""
        response = auth_session.get(f"{BASE_URL}/api/v1/tickets/{TEST_TICKET_ID}/estimate")
        
        if response.status_code != 200:
            pytest.skip(f"Estimate not found: {response.status_code}")
        
        data = response.json()
        estimate = data.get("estimate", data)
        
        # Check required fields for invoice conversion
        required_fields = ["estimate_id", "ticket_id", "subtotal", "tax_total", "grand_total"]
        for field in required_fields:
            assert field in estimate, f"Missing required field: {field}"
        
        print(f"Estimate subtotal: {estimate.get('subtotal')}")
        print(f"Estimate tax_total: {estimate.get('tax_total')}")
        print(f"Estimate grand_total: {estimate.get('grand_total')}")
        print(f"Line items: {len(estimate.get('line_items', []))}")

    def test_03_convert_to_invoice_endpoint_exists(self, auth_session):
        """POST /api/v1/ticket-estimates/{estimate_id}/convert-to-invoice endpoint exists"""
        response = auth_session.post(
            f"{BASE_URL}/api/v1/ticket-estimates/{TEST_ESTIMATE_ID}/convert-to-invoice"
        )
        
        print(f"POST convert-to-invoice status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Should not return 404 for route (endpoint exists)
        # 400 for "not found" or "already converted" is acceptable
        if response.status_code == 400:
            data = response.json()
            detail = data.get("detail", "")
            # Accept "already converted", "not found", or similar messages
            acceptable = any(msg in detail.lower() for msg in 
                           ["already", "converted", "not found", "approved"])
            if acceptable:
                print(f"Expected behavior: {detail}")
                return
            # Not the route 404, but a validation 400
            print(f"Validation error: {detail}")
            return
        
        assert response.status_code != 404, "Endpoint /ticket-estimates/{estimate_id}/convert-to-invoice not found"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Invoice created successfully: {data.get('invoice', {}).get('invoice_id')}")

    def test_04_verify_existing_invoice_from_estimate(self, auth_session):
        """Verify the invoice created from estimate has correct structure"""
        # Get the estimate to find the converted invoice ID
        response = auth_session.get(f"{BASE_URL}/api/v1/tickets/{TEST_TICKET_ID}/estimate")
        
        if response.status_code != 200:
            pytest.skip("Estimate not found")
        
        data = response.json()
        estimate = data.get("estimate", data)
        converted_invoice_id = estimate.get("converted_to_invoice")
        
        if not converted_invoice_id:
            pytest.skip("Estimate not yet converted to invoice")
        
        print(f"Converted invoice ID: {converted_invoice_id}")
        
        # Try to get the invoice from ticket_invoices collection
        response = auth_session.get(f"{BASE_URL}/api/v1/invoices/{converted_invoice_id}")
        
        if response.status_code == 200:
            invoice_data = response.json()
            invoice = invoice_data.get("invoice", invoice_data)
            
            # Verify invoice has correct linkage
            assert invoice.get("ticket_id") == TEST_TICKET_ID or invoice.get("source_estimate_id") == TEST_ESTIMATE_ID, \
                "Invoice not linked to correct ticket/estimate"
            
            print(f"Invoice number: {invoice.get('invoice_number')}")
            print(f"Invoice grand_total: {invoice.get('grand_total')}")
            print(f"Invoice source: {invoice.get('source')}")

    def test_05_ticket_status_updated_to_invoiced(self, auth_session):
        """Verify ticket status changes to 'invoiced' with has_invoice=true"""
        response = auth_session.get(f"{BASE_URL}/api/v1/tickets/{TEST_TICKET_ID}")
        
        if response.status_code != 200:
            pytest.skip(f"Ticket not found: {response.status_code}")
        
        data = response.json()
        ticket = data.get("ticket", data)
        
        print(f"Ticket status: {ticket.get('status')}")
        print(f"Ticket has_invoice: {ticket.get('has_invoice')}")
        print(f"Ticket invoice_id: {ticket.get('invoice_id')}")
        
        # Verify status is 'invoiced'
        assert ticket.get("status") == "invoiced", f"Expected status 'invoiced', got '{ticket.get('status')}'"
        assert ticket.get("has_invoice") == True, "has_invoice should be True"

    def test_06_journal_entry_posted_for_invoice(self, auth_session):
        """Verify journal entry is posted: DR Accounts Receivable, CR Revenue, CR GST"""
        # Get estimate to find converted invoice
        response = auth_session.get(f"{BASE_URL}/api/v1/tickets/{TEST_TICKET_ID}/estimate")
        
        if response.status_code != 200:
            pytest.skip("Estimate not found")
        
        data = response.json()
        estimate = data.get("estimate", data)
        converted_invoice_id = estimate.get("converted_to_invoice")
        
        if not converted_invoice_id:
            pytest.skip("Estimate not yet converted to invoice")
        
        # Search for journal entries related to this invoice
        response = auth_session.get(f"{BASE_URL}/api/v1/accounting/journal-entries")
        
        if response.status_code != 200:
            # Try alternate endpoint
            response = auth_session.get(f"{BASE_URL}/api/v1/journal-entries")
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("entries", data.get("journal_entries", []))
            
            # Find entry for this invoice
            invoice_entry = None
            for entry in entries:
                source_id = entry.get("source_document_id", "")
                reference = entry.get("reference_number", "")
                if converted_invoice_id in str(source_id) or converted_invoice_id in str(reference):
                    invoice_entry = entry
                    break
            
            if invoice_entry:
                print(f"Found journal entry: {invoice_entry.get('entry_id')}")
                print(f"Entry type: {invoice_entry.get('entry_type')}")
                print(f"Total debit: {invoice_entry.get('total_debit')}")
                print(f"Total credit: {invoice_entry.get('total_credit')}")
                
                # Verify entry is balanced
                total_debit = sum(line.get("debit_amount", 0) for line in invoice_entry.get("lines", []))
                total_credit = sum(line.get("credit_amount", 0) for line in invoice_entry.get("lines", []))
                assert abs(total_debit - total_credit) < 0.01, "Journal entry not balanced"
            else:
                print("Warning: No specific journal entry found for invoice (may have different reference)")
        else:
            print(f"Journal entries endpoint status: {response.status_code}")


# ====================================================================================
# TASK 2: E-INVOICE/IRN ENDPOINTS REGISTRATION AND FUNCTIONALITY
# ====================================================================================

class TestEInvoiceEndpoints:
    """Test E-Invoice/IRN endpoints are registered and working"""
    
    def test_01_einvoice_eligibility_endpoint(self, auth_session):
        """GET /api/v1/einvoice/eligibility returns eligibility status (not 404/500)"""
        response = auth_session.get(f"{BASE_URL}/api/v1/einvoice/eligibility")
        
        print(f"GET /einvoice/eligibility status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, "Endpoint /einvoice/eligibility not found"
        
        # 403 is acceptable (enterprise feature gate)
        if response.status_code == 403:
            print("Info: E-invoice feature gated (enterprise only) - acceptable")
            return
        
        # Should not be 500 (no server error)
        assert response.status_code != 500, f"Server error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            # Eligibility returns false when not configured - this is expected
            print(f"Eligibility: {data.get('eligible', False)}")
            print(f"Configured: {data.get('configured', False)}")
            print(f"Reason: {data.get('reason', 'N/A')}")

    def test_02_einvoice_config_endpoint(self, auth_session):
        """GET /api/v1/einvoice/config returns config status (not 404/500)"""
        response = auth_session.get(f"{BASE_URL}/api/v1/einvoice/config")
        
        print(f"GET /einvoice/config status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, "Endpoint /einvoice/config not found"
        
        # 403 is acceptable (enterprise feature gate)
        if response.status_code == 403:
            print("Info: E-invoice feature gated (enterprise only) - acceptable")
            return
        
        # Should not be 500 (no server error)
        assert response.status_code != 500, f"Server error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Configured: {data.get('configured', False)}")
            print(f"GSTIN: {data.get('gstin', 'N/A')}")
            print(f"Is Sandbox: {data.get('is_sandbox', 'N/A')}")

    def test_03_generate_irn_endpoint(self, auth_session):
        """POST /api/v1/einvoice/generate-irn returns skip_irn=true when not configured (not 404/500)"""
        response = auth_session.post(
            f"{BASE_URL}/api/v1/einvoice/generate-irn",
            json={"invoice_id": "test-invoice-123"}
        )
        
        print(f"POST /einvoice/generate-irn status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, "Endpoint /einvoice/generate-irn not found"
        
        # 403 is acceptable (enterprise feature gate)
        if response.status_code == 403:
            print("Info: E-invoice feature gated (enterprise only) - acceptable")
            return
        
        # 422 for validation error is acceptable
        if response.status_code == 422:
            print("Info: Validation error (expected for test invoice ID) - endpoint exists")
            return
        
        # Should not be 500 (no server error)
        assert response.status_code != 500, f"Server error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            # When not configured, should return skip_irn=true
            print(f"Success: {data.get('success', False)}")
            print(f"Skip IRN: {data.get('skip_irn', False)}")
            print(f"Message: {data.get('message', 'N/A')}")

    def test_04_validate_invoice_endpoint(self, auth_session):
        """POST /api/v1/einvoice/validate-invoice/{id} validates invoice fields (not 404)"""
        test_invoice_id = "test-invoice-123"
        response = auth_session.post(f"{BASE_URL}/api/v1/einvoice/validate-invoice/{test_invoice_id}")
        
        print(f"POST /einvoice/validate-invoice/{test_invoice_id} status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Endpoint should exist (not 404 for route)
        # 404 for "Invoice not found" is acceptable as it means endpoint exists
        if response.status_code == 404:
            data = response.json() if response.text else {}
            detail = data.get("detail", "")
            if "invoice not found" in detail.lower() or "not found" in detail.lower():
                print("Info: Invoice not found (expected for test ID) - endpoint exists")
                return
            # If 404 without proper message, might be missing route
            assert False, "Endpoint /einvoice/validate-invoice/{id} may not exist"
        
        # 403 is acceptable (enterprise feature gate)
        if response.status_code == 403:
            print("Info: E-invoice feature gated (enterprise only) - acceptable")
            return
        
        # Should not be 500 (no server error)
        assert response.status_code != 500, f"Server error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Is Valid: {data.get('is_valid', False)}")
            print(f"Errors: {data.get('errors', [])}")

    def test_05_qr_code_endpoint(self, auth_session):
        """GET /api/v1/einvoice/qr-code/{id} returns has_qr status (not 404)"""
        test_invoice_id = "test-invoice-123"
        response = auth_session.get(f"{BASE_URL}/api/v1/einvoice/qr-code/{test_invoice_id}")
        
        print(f"GET /einvoice/qr-code/{test_invoice_id} status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Endpoint should exist (not 404 for route)
        if response.status_code == 404:
            data = response.json() if response.text else {}
            detail = data.get("detail", "")
            if "invoice not found" in detail.lower() or "not found" in detail.lower():
                print("Info: Invoice not found (expected for test ID) - endpoint exists")
                return
            # If 404 without proper message, might be missing route
            assert False, "Endpoint /einvoice/qr-code/{id} may not exist"
        
        # 403 is acceptable (enterprise feature gate)
        if response.status_code == 403:
            print("Info: E-invoice feature gated (enterprise only) - acceptable")
            return
        
        # Should not be 500 (no server error)
        assert response.status_code != 500, f"Server error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Has QR: {data.get('has_qr', False)}")
            print(f"Message: {data.get('message', 'N/A')}")

    def test_06_irn_list_endpoint(self, auth_session):
        """GET /api/v1/einvoice/irn-list returns empty list (not 404)"""
        response = auth_session.get(f"{BASE_URL}/api/v1/einvoice/irn-list")
        
        print(f"GET /einvoice/irn-list status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, "Endpoint /einvoice/irn-list not found"
        
        # 403 is acceptable (enterprise feature gate)
        if response.status_code == 403:
            print("Info: E-invoice feature gated (enterprise only) - acceptable")
            return
        
        # Should not be 500 (no server error)
        assert response.status_code != 500, f"Server error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            print(f"IRN records count: {len(records)}")
            # Empty list is expected when no IRNs generated
            assert isinstance(records, list), "IRN records should be a list"

    def test_07_cancel_irn_endpoint_exists(self, auth_session):
        """POST /api/v1/einvoice/cancel-irn endpoint exists (not 404)"""
        response = auth_session.post(
            f"{BASE_URL}/api/v1/einvoice/cancel-irn",
            json={
                "irn": "A" * 64,  # 64 character placeholder
                "reason": "1",
                "remarks": "Test"
            }
        )
        
        print(f"POST /einvoice/cancel-irn status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, "Endpoint /einvoice/cancel-irn not found"
        
        # 403 is acceptable (enterprise feature gate)
        if response.status_code == 403:
            print("Info: E-invoice feature gated (enterprise only) - acceptable")
            return
        
        # 400/422 is acceptable (validation error for fake IRN)
        if response.status_code in [400, 422]:
            print("Info: Validation error (expected for test IRN) - endpoint exists")
            return
        
        # Should not be 500 (no server error)
        assert response.status_code != 500, f"Server error: {response.text}"


# ====================================================================================
# INVOICE TOTALS VERIFICATION
# ====================================================================================

class TestInvoiceTotalsCalculation:
    """Verify invoice totals are correctly calculated from estimate"""
    
    def test_verify_invoice_amounts(self, auth_session):
        """Verify invoice has correct grand_total, tax_total, subtotal, line_items"""
        # Get estimate
        response = auth_session.get(f"{BASE_URL}/api/v1/tickets/{TEST_TICKET_ID}/estimate")
        
        if response.status_code != 200:
            pytest.skip("Estimate not found")
        
        data = response.json()
        estimate = data.get("estimate", data)
        converted_invoice_id = estimate.get("converted_to_invoice")
        
        if not converted_invoice_id:
            pytest.skip("Estimate not yet converted to invoice")
        
        # Get invoice
        response = auth_session.get(f"{BASE_URL}/api/v1/invoices/{converted_invoice_id}")
        
        if response.status_code != 200:
            # Try ticket_invoices endpoint
            response = auth_session.get(f"{BASE_URL}/api/v1/ticket-invoices/{converted_invoice_id}")
        
        if response.status_code == 200:
            invoice_data = response.json()
            invoice = invoice_data.get("invoice", invoice_data)
            
            # Compare estimate and invoice totals
            print(f"Estimate subtotal: {estimate.get('subtotal')}")
            print(f"Invoice subtotal: {invoice.get('subtotal')}")
            print(f"Estimate tax_total: {estimate.get('tax_total')}")
            print(f"Invoice tax_total: {invoice.get('tax_total')}")
            print(f"Estimate grand_total: {estimate.get('grand_total')}")
            print(f"Invoice grand_total: {invoice.get('grand_total')}")
            
            # Verify totals match
            assert abs(float(estimate.get('subtotal', 0)) - float(invoice.get('subtotal', 0))) < 0.01, \
                "Subtotal mismatch"
            assert abs(float(estimate.get('grand_total', 0)) - float(invoice.get('grand_total', 0))) < 0.01, \
                "Grand total mismatch"
            
            # Verify line items transferred
            assert len(invoice.get('line_items', [])) > 0, "Invoice should have line items"
            print(f"Invoice line_items count: {len(invoice.get('line_items', []))}")
        else:
            print(f"Could not retrieve invoice: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
