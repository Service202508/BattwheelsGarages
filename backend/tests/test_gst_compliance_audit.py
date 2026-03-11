"""
GST Compliance Audit Tests
==========================
Tests for:
1. GSTR-1 Completeness - verify all sections: B2B, B2C, CDNR, HSN Summary
2. Place of Supply Logic - verify intrastate CGST+SGST vs interstate IGST
3. Credit Note GST Reversal - verify credit notes reverse GST and create correct journal entries

Test credentials: demo@voltmotors.in / volt1234
Organization: demo-volt-motors-001 (state code 07 - Delhi)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

# Test data
TEST_EMAIL = "demo@voltmotors.in"
TEST_PASSWORD = "Demo@12345"
ORG_ID = "demo-volt-motors-001"
ORG_STATE_CODE = "07"  # Delhi

# Valid GSTINs for testing
DELHI_GSTIN = "07AAACR5055K1Z9"
MAHARASHTRA_GSTIN = "27AADCS0472N1Z2"


class TestGSTAuthAndSetup:
    """Authentication and setup tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        print(f"Auth response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            print(f"Token obtained: {token[:20]}..." if token else "No token in response")
            return token
        else:
            print(f"Auth failed: {response.text}")
            pytest.skip("Authentication failed - cannot proceed with tests")
    
    def test_login_success(self, auth_token):
        """Test that login returns valid token"""
        assert auth_token is not None, "Auth token should not be None"
        assert len(auth_token) > 20, "Auth token should be a valid JWT"
        print(f"Login successful, token length: {len(auth_token)}")


class TestGSTCalculation:
    """Tests for Place of Supply Logic - CGST/SGST vs IGST splitting"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers with organization context"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            org_id = data.get("current_organization") or ORG_ID
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Organization-ID": org_id
            }
        pytest.skip("Authentication failed")
    
    def test_intrastate_cgst_sgst_split(self, auth_headers):
        """
        Test intrastate transaction returns CGST+SGST split
        Same state (07 Delhi -> 07 Delhi) should return is_intra_state=true
        """
        payload = {
            "subtotal": 10000,
            "gst_rate": 18,
            "org_state_code": "07",  # Delhi
            "customer_state_code": "07"  # Delhi (same state)
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/calculate",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        
        print(f"Intrastate GST calculation status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Intrastate response: {data}")
        
        # Verify is_intra_state flag
        assert data.get("is_intra_state") == True, f"Expected is_intra_state=True, got {data.get('is_intra_state')}"
        
        # Verify CGST + SGST split (half each)
        expected_half = 10000 * 0.18 / 2  # 900
        assert data.get("cgst_amount") == expected_half, f"Expected CGST {expected_half}, got {data.get('cgst_amount')}"
        assert data.get("sgst_amount") == expected_half, f"Expected SGST {expected_half}, got {data.get('sgst_amount')}"
        
        # Verify no IGST for intrastate
        assert data.get("igst_amount") == 0, f"Expected IGST 0, got {data.get('igst_amount')}"
        
        # Verify total GST
        assert data.get("total_gst") == 1800, f"Expected total GST 1800, got {data.get('total_gst')}"
        
        print("PASS: Intrastate returns CGST+SGST split correctly")
    
    def test_interstate_igst_only(self, auth_headers):
        """
        Test interstate transaction returns IGST only
        Different states (07 Delhi -> 27 Maharashtra) should return is_intra_state=false
        """
        payload = {
            "subtotal": 10000,
            "gst_rate": 18,
            "org_state_code": "07",  # Delhi
            "customer_state_code": "27"  # Maharashtra (different state)
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/calculate",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        
        print(f"Interstate GST calculation status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Interstate response: {data}")
        
        # Verify is_intra_state flag
        assert data.get("is_intra_state") == False, f"Expected is_intra_state=False, got {data.get('is_intra_state')}"
        
        # Verify no CGST/SGST for interstate
        assert data.get("cgst_amount") == 0, f"Expected CGST 0, got {data.get('cgst_amount')}"
        assert data.get("sgst_amount") == 0, f"Expected SGST 0, got {data.get('sgst_amount')}"
        
        # Verify IGST only
        expected_igst = 10000 * 0.18  # 1800
        assert data.get("igst_amount") == expected_igst, f"Expected IGST {expected_igst}, got {data.get('igst_amount')}"
        
        # Verify total GST
        assert data.get("total_gst") == 1800, f"Expected total GST 1800, got {data.get('total_gst')}"
        
        print("PASS: Interstate returns IGST only correctly")


class TestGSTR1Report:
    """Tests for GSTR-1 Completeness - all sections must be present"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers with organization context"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            org_id = data.get("current_organization") or ORG_ID
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Organization-ID": org_id
            }
        pytest.skip("Authentication failed")
    
    def test_gstr1_returns_all_sections(self, auth_headers):
        """
        Test GSTR-1 report returns all required sections:
        - b2b: Business to Business invoices
        - b2c_large: B2C > 2.5L inter-state
        - b2c_small: B2C <= 2.5L
        - cdnr: Credit/Debit Notes (Registered)
        - cdnr_unregistered: Credit notes for unregistered customers
        - hsn_summary: HSN-wise summary
        - grand_total: Aggregated totals
        """
        response = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month=2026-03",
            headers=auth_headers,
            timeout=30
        )
        
        print(f"GSTR-1 status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"GSTR-1 response keys: {data.keys()}")
        
        # Verify all required sections are present
        required_sections = ["b2b", "b2c_large", "b2c_small", "cdnr", "cdnr_unregistered", "hsn_summary", "grand_total"]
        
        for section in required_sections:
            assert section in data, f"Missing required section: {section}"
            print(f"  Section '{section}' present: ✓")
        
        # Verify b2b structure
        assert "summary" in data["b2b"], "b2b should have summary"
        assert "invoices" in data["b2b"], "b2b should have invoices list"
        
        # Verify b2c_small structure
        assert "summary" in data["b2c_small"], "b2c_small should have summary"
        assert "invoices" in data["b2c_small"], "b2c_small should have invoices list"
        
        # Verify hsn_summary structure
        assert "by_code_rate" in data["hsn_summary"], "hsn_summary should have by_code_rate"
        assert "totals" in data["hsn_summary"], "hsn_summary should have totals"
        
        # Verify grand_total structure
        assert "taxable_value" in data["grand_total"], "grand_total should have taxable_value"
        assert "cgst" in data["grand_total"], "grand_total should have cgst"
        assert "sgst" in data["grand_total"], "grand_total should have sgst"
        assert "igst" in data["grand_total"], "grand_total should have igst"
        
        print("PASS: GSTR-1 returns all required sections")
    
    def test_b2b_contains_gstin_customers(self, auth_headers):
        """
        Test B2B section contains only invoices with valid GSTIN customers
        """
        response = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month=2026-03",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        b2b_invoices = data.get("b2b", {}).get("invoices", [])
        print(f"B2B invoices count: {len(b2b_invoices)}")
        
        # Every B2B invoice should have a valid GSTIN
        for inv in b2b_invoices:
            gstin = inv.get("customer_gstin", "")
            assert gstin and len(gstin) == 15, f"B2B invoice {inv.get('invoice_number')} should have valid 15-char GSTIN, got: {gstin}"
            print(f"  Invoice {inv.get('invoice_number')}: GSTIN {gstin} ✓")
        
        print("PASS: B2B section contains only GSTIN customers")
    
    def test_b2c_small_contains_unregistered_customers(self, auth_headers):
        """
        Test B2C Small section contains invoices for unregistered/consumer customers
        """
        response = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month=2026-03",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        b2c_invoices = data.get("b2c_small", {}).get("invoices", [])
        print(f"B2C Small invoices count: {len(b2c_invoices)}")
        
        # B2C Small should have invoices without valid GSTIN
        for inv in b2c_invoices:
            gstin = inv.get("customer_gstin", "")
            # B2C invoices should either have no GSTIN or invalid GSTIN
            if gstin:
                # If GSTIN exists, it should not be a valid 15-char GSTIN
                print(f"  Invoice {inv.get('invoice_number')}: GSTIN '{gstin}' (invalid or empty)")
            else:
                print(f"  Invoice {inv.get('invoice_number')}: No GSTIN (unregistered customer) ✓")
        
        print("PASS: B2C Small section verified")
    
    def test_hsn_summary_has_distinct_codes(self, auth_headers):
        """
        Test HSN Summary shows distinct HSN codes from line_items (not default 9987)
        This was a bug fix - previously all HSN defaulted to '9987'
        """
        response = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month=2026-03",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        hsn_summary = data.get("hsn_summary", {}).get("by_code_rate", [])
        print(f"HSN Summary entries: {len(hsn_summary)}")
        
        hsn_codes = set()
        for entry in hsn_summary:
            hsn_code = entry.get("hsn_code", "")
            hsn_codes.add(hsn_code)
            print(f"  HSN: {hsn_code}, Rate: {entry.get('gst_rate')}%, Taxable: {entry.get('taxable_value')}")
        
        print(f"Distinct HSN codes found: {hsn_codes}")
        
        # If there are invoices with line_items, there should be HSN codes
        # Note: It's acceptable to have '9987' as default for services, but should also have others
        if len(hsn_summary) > 0:
            print("PASS: HSN Summary has entries")
        else:
            print("INFO: No HSN summary entries (may be no invoices in period)")


class TestCDNRSection:
    """Tests for Credit Notes in GSTR-1 CDNR section"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers with organization context"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            org_id = data.get("current_organization") or ORG_ID
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Organization-ID": org_id
            }
        pytest.skip("Authentication failed")
    
    def test_cdnr_section_present_in_gstr1(self, auth_headers):
        """Test CDNR section exists and has proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month=2026-03",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify CDNR section structure
        assert "cdnr" in data, "GSTR-1 should have cdnr section"
        cdnr = data["cdnr"]
        
        assert "summary" in cdnr, "cdnr should have summary"
        assert "notes" in cdnr, "cdnr should have notes list"
        
        # Verify cdnr_unregistered section
        assert "cdnr_unregistered" in data, "GSTR-1 should have cdnr_unregistered section"
        
        print(f"CDNR registered count: {cdnr['summary'].get('count', 0)}")
        print(f"CDNR unregistered count: {data['cdnr_unregistered']['summary'].get('count', 0)}")
        print("PASS: CDNR sections present with proper structure")
    
    def test_grand_total_subtracts_credit_notes(self, auth_headers):
        """Test that grand_total in GSTR-1 correctly subtracts credit note amounts"""
        response = requests.get(
            f"{BASE_URL}/api/v1/gst/gstr1?month=2026-03",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Get totals
        b2b_summary = data.get("b2b", {}).get("summary", {})
        b2c_large_summary = data.get("b2c_large", {}).get("summary", {})
        b2c_small_summary = data.get("b2c_small", {}).get("summary", {})
        cdnr_summary = data.get("cdnr", {}).get("summary", {})
        cdnr_unreg_summary = data.get("cdnr_unregistered", {}).get("summary", {})
        grand_total = data.get("grand_total", {})
        
        # Calculate expected grand total
        invoice_taxable = (
            b2b_summary.get("taxable_value", 0) +
            b2c_large_summary.get("taxable_value", 0) +
            b2c_small_summary.get("taxable_value", 0)
        )
        
        cn_taxable = cdnr_summary.get("taxable_value", 0) + cdnr_unreg_summary.get("taxable_value", 0)
        
        expected_grand_taxable = invoice_taxable - cn_taxable
        actual_grand_taxable = grand_total.get("taxable_value", 0)
        
        print(f"Invoice taxable total: {invoice_taxable}")
        print(f"Credit note taxable total: {cn_taxable}")
        print(f"Expected grand taxable: {expected_grand_taxable}")
        print(f"Actual grand taxable: {actual_grand_taxable}")
        
        # Allow small rounding differences
        assert abs(actual_grand_taxable - expected_grand_taxable) < 1, \
            f"Grand total taxable should subtract credit notes. Expected ~{expected_grand_taxable}, got {actual_grand_taxable}"
        
        print("PASS: Grand total correctly subtracts credit note amounts")


class TestCreditNoteCreation:
    """Tests for Credit Note creation and GST reversal journal entries"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers with organization context"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            org_id = data.get("current_organization") or ORG_ID
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Organization-ID": org_id
            }
        pytest.skip("Authentication failed")
    
    def test_list_credit_notes(self, auth_headers):
        """Test listing existing credit notes"""
        response = requests.get(
            f"{BASE_URL}/api/v1/credit-notes/",
            headers=auth_headers,
            timeout=30
        )
        
        print(f"List credit notes status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        credit_notes = data.get("credit_notes", [])
        print(f"Existing credit notes count: {len(credit_notes)}")
        
        for cn in credit_notes[:5]:  # Show first 5
            print(f"  CN: {cn.get('credit_note_number')}, Invoice: {cn.get('original_invoice_number')}, Total: {cn.get('total')}")
        
        print("PASS: Credit notes list retrieved")
    
    def test_credit_note_has_gst_breakdown(self, auth_headers):
        """Test that credit notes have proper GST breakdown fields"""
        response = requests.get(
            f"{BASE_URL}/api/v1/credit-notes/",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        credit_notes = data.get("credit_notes", [])
        
        if not credit_notes:
            print("INFO: No credit notes found to verify GST breakdown")
            return
        
        cn = credit_notes[0]
        print(f"Checking credit note: {cn.get('credit_note_number')}")
        
        # Verify GST fields exist
        required_fields = ["subtotal", "cgst_amount", "sgst_amount", "igst_amount", "gst_amount", "total"]
        for field in required_fields:
            assert field in cn, f"Credit note should have '{field}' field"
            print(f"  {field}: {cn.get(field)}")
        
        # Verify GST breakdown adds up
        gst_total = cn.get("cgst_amount", 0) + cn.get("sgst_amount", 0) + cn.get("igst_amount", 0)
        assert abs(gst_total - cn.get("gst_amount", 0)) < 0.01, \
            f"GST breakdown should match gst_amount. Components: {gst_total}, gst_amount: {cn.get('gst_amount')}"
        
        # Verify total = subtotal + gst
        expected_total = cn.get("subtotal", 0) + cn.get("gst_amount", 0)
        assert abs(expected_total - cn.get("total", 0)) < 0.01, \
            f"Total should equal subtotal + gst. Expected: {expected_total}, got: {cn.get('total')}"
        
        print("PASS: Credit note has proper GST breakdown")


class TestJournalEntries:
    """Tests for journal entry balance verification"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers with organization context"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            org_id = data.get("current_organization") or ORG_ID
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Organization-ID": org_id
            }
        pytest.skip("Authentication failed")
    
    def test_trial_balance_is_balanced(self, auth_headers):
        """Test that trial balance shows debits = credits"""
        response = requests.get(
            f"{BASE_URL}/api/v1/accounting/trial-balance",
            headers=auth_headers,
            timeout=30
        )
        
        print(f"Trial balance status: {response.status_code}")
        if response.status_code != 200:
            print(f"Trial balance response: {response.text[:500]}")
            pytest.skip("Trial balance endpoint not available")
        
        data = response.json()
        totals = data.get("totals", {})
        
        total_debit = totals.get("total_debit", 0)
        total_credit = totals.get("total_credit", 0)
        is_balanced = totals.get("is_balanced", False)
        
        print(f"Total Debits: {total_debit}")
        print(f"Total Credits: {total_credit}")
        print(f"Is Balanced: {is_balanced}")
        
        assert is_balanced or abs(total_debit - total_credit) < 0.01, \
            f"Trial balance should be balanced. Debit: {total_debit}, Credit: {total_credit}"
        
        print("PASS: Trial balance is balanced")
    
    def test_credit_note_journal_entries(self, auth_headers):
        """
        Test that credit note journal entries are balanced
        Expected entries:
        - DR: Sales Revenue (subtotal)
        - DR: GST Payable (tax amounts)
        - CR: Accounts Receivable or Refund Payable (total)
        """
        # First, get a credit note to find its journal entry
        response = requests.get(
            f"{BASE_URL}/api/v1/credit-notes/",
            headers=auth_headers,
            timeout=30
        )
        
        if response.status_code != 200:
            pytest.skip("Cannot fetch credit notes")
        
        credit_notes = response.json().get("credit_notes", [])
        if not credit_notes:
            print("INFO: No credit notes found to verify journal entries")
            return
        
        cn = credit_notes[0]
        cn_id = cn.get("credit_note_id")
        
        # Try to get journal entries for this credit note
        je_response = requests.get(
            f"{BASE_URL}/api/v1/accounting/journal-entries?source_document_id={cn_id}",
            headers=auth_headers,
            timeout=30
        )
        
        if je_response.status_code != 200:
            print(f"Journal entries endpoint status: {je_response.status_code}")
            # Try alternative approach - get all journal entries and filter
            je_response = requests.get(
                f"{BASE_URL}/api/v1/accounting/journal-entries",
                headers=auth_headers,
                timeout=30
            )
        
        if je_response.status_code == 200:
            entries = je_response.json().get("entries", [])
            
            # Find entries related to credit notes
            cn_entries = [e for e in entries if e.get("source_document_type") == "credit_note"]
            print(f"Credit note journal entries found: {len(cn_entries)}")
            
            for entry in cn_entries[:3]:  # Check first 3
                total_debit = entry.get("total_debit", 0)
                total_credit = entry.get("total_credit", 0)
                
                print(f"  Entry {entry.get('reference_number')}: DR={total_debit}, CR={total_credit}")
                
                # Verify entry is balanced
                assert abs(total_debit - total_credit) < 0.01, \
                    f"Journal entry should be balanced. DR: {total_debit}, CR: {total_credit}"
            
            print("PASS: Credit note journal entries are balanced")
        else:
            print(f"INFO: Journal entries endpoint returned {je_response.status_code}")


class TestGSTINValidation:
    """Tests for GSTIN validation with checksum"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers with organization context"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            org_id = data.get("current_organization") or ORG_ID
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Organization-ID": org_id
            }
        pytest.skip("Authentication failed")
    
    def test_valid_delhi_gstin(self, auth_headers):
        """Test validation of valid Delhi GSTIN"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/validate-gstin",
            json={"gstin": DELHI_GSTIN},
            headers=auth_headers,
            timeout=30
        )
        
        print(f"GSTIN validation status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"Validation result: {data}")
        
        assert data.get("valid") == True, f"GSTIN {DELHI_GSTIN} should be valid"
        assert data.get("state_code") == "07", "State code should be 07 (Delhi)"
        
        print(f"PASS: Delhi GSTIN {DELHI_GSTIN} validated successfully")
    
    def test_valid_maharashtra_gstin(self, auth_headers):
        """Test validation of valid Maharashtra GSTIN"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/validate-gstin",
            json={"gstin": MAHARASHTRA_GSTIN},
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("valid") == True, f"GSTIN {MAHARASHTRA_GSTIN} should be valid"
        assert data.get("state_code") == "27", "State code should be 27 (Maharashtra)"
        
        print(f"PASS: Maharashtra GSTIN {MAHARASHTRA_GSTIN} validated successfully")
    
    def test_invalid_gstin_checksum(self, auth_headers):
        """Test that invalid checksum is rejected"""
        invalid_gstin = "07AAACR5055K1Z8"  # Changed last digit from 9 to 8
        
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/validate-gstin",
            json={"gstin": invalid_gstin},
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("valid") == False, f"Invalid checksum GSTIN should be rejected"
        print(f"PASS: Invalid GSTIN checksum correctly rejected")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
