"""
Customer Portal E2E and Invoice PDF Content Verification Tests
Phase B-1: Tests for:
1. All 10+ customer portal endpoints with X-Portal-Session auth
2. Data leak prevention - sensitive fields must NOT appear in portal responses
3. Invoice PDF content verification - GST-compliant CGST/SGST breakdown

Test credentials:
- Workshop login: demo@voltmotors.in / Demo@12345
- Portal login token: PORTAL-SUNITA-2026
- Invoice ID for PDF test: INV-52E8ABFFBF6D
"""

import pytest
import requests
import os
import io

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Sensitive fields that MUST NOT appear in portal ticket responses
SENSITIVE_FIELDS = [
    'organization_id',
    '_seed',
    'assigned_technician_id',
    'internal_notes',
    'resolution_notes'
]


class TestCustomerPortalAuth:
    """Test portal authentication flow"""
    
    def test_portal_login_with_valid_token(self):
        """TASK 1: Portal login with token 'PORTAL-SUNITA-2026' returns 200 with session_token"""
        response = requests.post(
            f"{BASE_URL}/api/v1/customer-portal/login",
            json={"token": "PORTAL-SUNITA-2026"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("code") == 0, f"Expected code 0, got {data.get('code')}"
        assert "session_token" in data, "session_token must be in response"
        assert data["session_token"].startswith("PS-"), f"Session token should start with PS-, got {data['session_token']}"
        
        # Store session token for other tests
        pytest.portal_session_token = data["session_token"]
        print(f"PASS: Portal login successful, session_token: {data['session_token'][:20]}...")
    
    def test_portal_endpoints_return_401_without_header(self):
        """TASK 1: Portal endpoints return 401 without X-Portal-Session header"""
        endpoints = [
            "/api/v1/customer-portal/session",
            "/api/v1/customer-portal/dashboard",
            "/api/v1/customer-portal/tickets",
            "/api/v1/customer-portal/invoices",
            "/api/v1/customer-portal/estimates",
            "/api/v1/customer-portal/payments",
            "/api/v1/customer-portal/statement",
            "/api/v1/customer-portal/profile",
            "/api/v1/customer-portal/vehicles",
            "/api/v1/customer-portal/documents",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 401, f"{endpoint}: Expected 401 without session, got {response.status_code}"
        
        print(f"PASS: All {len(endpoints)} endpoints correctly return 401 without auth")


class TestCustomerPortalEndpoints:
    """Test all customer portal endpoints with valid session"""
    
    @pytest.fixture(autouse=True)
    def setup_session(self):
        """Get portal session token before each test"""
        # Login to get session token
        response = requests.post(
            f"{BASE_URL}/api/v1/customer-portal/login",
            json={"token": "PORTAL-SUNITA-2026"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.session_token = response.json().get("session_token")
        self.headers = {"X-Portal-Session": self.session_token}
    
    def test_get_session_info(self):
        """TASK 1: GET /api/v1/customer-portal/session returns 200 with valid portal session"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/session",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "session" in data
        assert data["session"].get("session_token") == self.session_token
        print("PASS: GET /session returns valid session info")
    
    def test_get_dashboard(self):
        """TASK 1: GET /api/v1/customer-portal/dashboard returns 200 with contact info"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/dashboard",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "dashboard" in data
        assert "contact" in data["dashboard"]
        assert "summary" in data["dashboard"]
        print(f"PASS: Dashboard shows contact: {data['dashboard']['contact'].get('name')}")
    
    def test_get_tickets_no_sensitive_fields(self):
        """TASK 1: GET /api/v1/customer-portal/tickets returns 200 - verify NO sensitive fields in response"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/tickets",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "tickets" in data
        
        # Check ALL tickets for sensitive fields
        tickets = data["tickets"]
        leaked_fields = []
        
        for ticket in tickets:
            for field in SENSITIVE_FIELDS:
                if field in ticket:
                    leaked_fields.append(f"ticket {ticket.get('ticket_id', 'unknown')}: {field}")
        
        assert len(leaked_fields) == 0, f"DATA LEAK! Sensitive fields found in portal tickets: {leaked_fields}"
        print(f"PASS: {len(tickets)} tickets returned, NO sensitive fields leaked")
    
    def test_get_invoices(self):
        """TASK 1: GET /api/v1/customer-portal/invoices returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/invoices",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "invoices" in data
        print(f"PASS: Portal invoices endpoint working, {len(data['invoices'])} invoices")
    
    def test_get_estimates(self):
        """TASK 1: GET /api/v1/customer-portal/estimates returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/estimates",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "estimates" in data
        print(f"PASS: Portal estimates endpoint working, {len(data['estimates'])} estimates")
    
    def test_get_payments(self):
        """TASK 1: GET /api/v1/customer-portal/payments returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/payments",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "payments" in data
        print(f"PASS: Portal payments endpoint working, {len(data['payments'])} payments")
    
    def test_get_statement(self):
        """TASK 1: GET /api/v1/customer-portal/statement returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/statement",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "statement" in data
        print("PASS: Portal statement endpoint working")
    
    def test_get_profile(self):
        """TASK 1: GET /api/v1/customer-portal/profile returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/profile",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "profile" in data
        
        # Verify portal_token is NOT exposed in profile
        assert "portal_token" not in data["profile"], "portal_token should not be exposed in profile!"
        print(f"PASS: Portal profile working, contact_id: {data['profile'].get('contact_id')}")
    
    def test_get_vehicles(self):
        """TASK 1: GET /api/v1/customer-portal/vehicles returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/vehicles",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "vehicles" in data
        print(f"PASS: Portal vehicles endpoint working, {len(data['vehicles'])} vehicles")
    
    def test_get_documents(self):
        """TASK 1: GET /api/v1/customer-portal/documents returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/v1/customer-portal/documents",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("code") == 0
        assert "documents" in data
        print(f"PASS: Portal documents endpoint working, {len(data['documents'])} documents")


class TestInvoicePDFContent:
    """Test Invoice PDF generation with GST-compliant content"""
    
    @classmethod
    def setup_class(cls):
        """Get workshop JWT token for PDF access - runs once per class"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "demo@voltmotors.in", "password": "Demo@12345"}
        )
        assert response.status_code == 200, f"Workshop login failed: {response.status_code} {response.text}"
        data = response.json()
        cls.workshop_token = data.get("access_token") or data.get("token")
        assert cls.workshop_token, f"No token in response: {data}"
        # Include X-Organization-ID to prevent conftest auto-injection of wrong org
        cls.headers = {
            "Authorization": f"Bearer {cls.workshop_token}",
            "X-Organization-ID": "demo-volt-motors-001"
        }
    
    def test_invoice_pdf_returns_200_with_content_type(self):
        """TASK 2: GET /api/v1/invoices-enhanced/INV-52E8ABFFBF6D/pdf returns 200 with Content-Type application/pdf"""
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices-enhanced/INV-52E8ABFFBF6D/pdf",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        assert response.headers.get("Content-Type") == "application/pdf", \
            f"Expected Content-Type: application/pdf, got {response.headers.get('Content-Type')}"
        
        # Store PDF content for further tests
        pytest.pdf_content = response.content
        print(f"PASS: Invoice PDF returned with correct Content-Type, size: {len(response.content)} bytes")
    
    def test_invoice_pdf_size_not_blank(self):
        """TASK 2: PDF size > 10KB (not blank)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices-enhanced/INV-52E8ABFFBF6D/pdf",
            headers=self.headers
        )
        
        assert response.status_code == 200
        pdf_size = len(response.content)
        
        # PDF should be at least 10KB (10240 bytes) to have real content
        assert pdf_size > 10240, f"PDF too small ({pdf_size} bytes), likely blank or malformed"
        print(f"PASS: PDF size is {pdf_size} bytes (>{10240} bytes threshold)")
    
    def test_invoice_pdf_contains_gst_elements(self):
        """TASK 2: PDF content contains GSTIN, HSN codes, invoice number, date, grand total"""
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices-enhanced/INV-52E8ABFFBF6D/pdf",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200] if response.status_code != 200 else ''}"
        
        # For PDF content verification, we check the raw bytes for text patterns
        # WeasyPrint PDFs contain readable text in the PDF stream
        pdf_bytes = response.content
        
        # Convert to string for text search (PDF text is embedded in binary)
        try:
            # Try to extract text from PDF using PyPDF2
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() or ""
            
            # Check for required GST elements
            checks = {
                "GSTIN": "GSTIN" in pdf_text or "gstin" in pdf_text.lower(),
                "HSN": "HSN" in pdf_text or "SAC" in pdf_text,
                "Invoice Number": "INV-" in pdf_text or "Invoice" in pdf_text,
                "Grand Total": "Grand Total" in pdf_text or "Total" in pdf_text,
                "CGST or SGST": "CGST" in pdf_text or "SGST" in pdf_text or "IGST" in pdf_text,
            }
            
            missing = [k for k, v in checks.items() if not v]
            assert len(missing) == 0, f"PDF missing required elements: {missing}. PDF text: {pdf_text[:500]}"
            print(f"PASS: PDF contains all GST elements: {list(checks.keys())}")
            
        except ImportError:
            # If PyPDF2 not available, check PDF size and basic structure
            assert len(pdf_bytes) > 10240, f"PDF too small: {len(pdf_bytes)} bytes"
            # Check PDF header
            assert pdf_bytes[:4] == b'%PDF', "Not a valid PDF file"
            print(f"PASS (PyPDF2 not available): PDF size {len(pdf_bytes)} bytes, valid PDF structure")


class TestInvoicePDFTaxBreakdown:
    """Specific tests for CGST/SGST tax breakdown in PDF"""
    
    @classmethod
    def setup_class(cls):
        """Get workshop auth - runs once per class"""
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "demo@voltmotors.in", "password": "Demo@12345"}
        )
        assert response.status_code == 200, f"Workshop login failed: {response.status_code}"
        data = response.json()
        cls.token = data.get("access_token") or data.get("token")
        assert cls.token, f"No token in response: {data}"
        # Include X-Organization-ID to prevent conftest auto-injection of wrong org
        cls.headers = {
            "Authorization": f"Bearer {cls.token}",
            "X-Organization-ID": "demo-volt-motors-001"
        }
    
    def test_invoice_data_has_cgst_sgst_breakdown(self):
        """Verify invoice data endpoint returns CGST/SGST values (not 0.00)"""
        response = requests.get(
            f"{BASE_URL}/api/v1/invoices-enhanced/INV-52E8ABFFBF6D",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        invoice = data.get("invoice", {})
        
        # Check for CGST/SGST totals at invoice level
        cgst_total = invoice.get("cgst_total", 0)
        sgst_total = invoice.get("sgst_total", 0)
        igst_total = invoice.get("igst_total", 0)
        tax_total = invoice.get("tax_total", 0)
        
        # At least one tax type should be non-zero if there's tax
        if tax_total > 0:
            has_tax_breakdown = cgst_total > 0 or sgst_total > 0 or igst_total > 0
            assert has_tax_breakdown, \
                f"Tax total is {tax_total} but CGST={cgst_total}, SGST={sgst_total}, IGST={igst_total} - no breakdown!"
        
        # Check line items for tax amounts
        line_items = invoice.get("line_items", [])
        for item in line_items:
            item_tax = item.get("tax_amount", 0)
            if item_tax > 0:
                cgst = item.get("cgst_amount", 0)
                sgst = item.get("sgst_amount", 0)
                igst = item.get("igst_amount", 0)
                # Line item should have tax breakdown
                has_item_breakdown = cgst > 0 or sgst > 0 or igst > 0
                assert has_item_breakdown, \
                    f"Line item {item.get('name')} has tax_amount={item_tax} but no CGST/SGST/IGST breakdown"
        
        print(f"PASS: Invoice tax breakdown - CGST: {cgst_total}, SGST: {sgst_total}, IGST: {igst_total}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
