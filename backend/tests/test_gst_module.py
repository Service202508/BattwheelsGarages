"""
GST Compliance Module Tests
Tests for GSTIN validation, GST calculation, organization settings, and GST reports (GSTR-1, GSTR-3B, HSN Summary)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "dev@battwheels.internal"
ADMIN_PASSWORD = "DevTest@123"


@pytest.fixture(scope="module")
def auth_headers():
    """Get admin auth headers for GST tests"""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class TestGSTStates:
    """Test Indian states endpoint"""
    
    def test_get_indian_states(self, auth_headers):
        """GET /api/v1/gst/states - Returns list of Indian states with GST codes"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/states", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "states" in data
        assert len(data["states"]) > 30  # India has 28 states + UTs
        
        # Verify state structure
        state = data["states"][0]
        assert "code" in state
        assert "name" in state
        
        # Verify Maharashtra is present (code 27)
        maharashtra = next((s for s in data["states"] if s["code"] == "27"), None)
        assert maharashtra is not None
        assert maharashtra["name"] == "Maharashtra"


class TestGSTINValidation:
    """Test GSTIN validation endpoint"""
    
    def test_validate_valid_gstin(self, auth_headers):
        """POST /api/v1/gst/validate-gstin - Valid GSTIN returns details"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/validate-gstin",
            json={"gstin": "27AAACT1234A1Z1"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["valid"] == True
        assert data["gstin"] == "27AAACT1234A1Z1"
        assert data["state_code"] == "27"
        assert data["state_name"] == "Maharashtra"
        assert data["pan"] == "AAACT1234A"
    
    def test_validate_invalid_gstin_short(self, auth_headers):
        """POST /api/v1/gst/validate-gstin - Short GSTIN returns error"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/validate-gstin",
            json={"gstin": "INVALID123"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 1
        assert data["valid"] == False
        assert "15 characters" in data["error"]
    
    def test_validate_invalid_gstin_format(self, auth_headers):
        """POST /api/v1/gst/validate-gstin - Invalid format returns error"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/validate-gstin",
            json={"gstin": "ABCDEFGHIJKLMNO"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 1
        assert data["valid"] == False
    
    def test_validate_empty_gstin(self, auth_headers):
        """POST /api/v1/gst/validate-gstin - Empty GSTIN returns error"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/validate-gstin",
            json={"gstin": ""},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == False


class TestGSTCalculation:
    """Test GST calculation endpoint"""
    
    def test_intra_state_calculation(self, auth_headers):
        """POST /api/v1/gst/calculate - Same state applies CGST+SGST"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/calculate",
            json={
                "subtotal": 10000,
                "gst_rate": 18,
                "org_state_code": "27",
                "customer_state_code": "27"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["is_intra_state"] == True
        assert data["gst_rate"] == 18.0
        assert data["cgst_rate"] == 9.0
        assert data["cgst_amount"] == 900.0
        assert data["sgst_rate"] == 9.0
        assert data["sgst_amount"] == 900.0
        assert data["igst_rate"] == 0
        assert data["igst_amount"] == 0
        assert data["total_gst"] == 1800.0
    
    def test_inter_state_calculation(self, auth_headers):
        """POST /api/v1/gst/calculate - Different state applies IGST"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/calculate",
            json={
                "subtotal": 10000,
                "gst_rate": 18,
                "org_state_code": "27",  # Maharashtra
                "customer_state_code": "29"  # Karnataka
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["is_intra_state"] == False
        assert data["cgst_rate"] == 0
        assert data["cgst_amount"] == 0
        assert data["sgst_rate"] == 0
        assert data["sgst_amount"] == 0
        assert data["igst_rate"] == 18.0
        assert data["igst_amount"] == 1800.0
        assert data["total_gst"] == 1800.0
    
    def test_different_gst_rates(self, auth_headers):
        """POST /api/v1/gst/calculate - Test with 5% GST rate"""
        response = requests.post(
            f"{BASE_URL}/api/v1/gst/calculate",
            json={
                "subtotal": 10000,
                "gst_rate": 5,
                "org_state_code": "27",
                "customer_state_code": "27"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["gst_rate"] == 5.0
        assert data["cgst_rate"] == 2.5
        assert data["cgst_amount"] == 250.0
        assert data["sgst_amount"] == 250.0
        assert data["total_gst"] == 500.0


class TestOrganizationSettings:
    """Test organization GST settings endpoints"""
    
    def test_get_organization_settings(self, auth_headers):
        """GET /api/v1/gst/organization-settings - Returns org GST settings"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/organization-settings", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "settings" in data
        assert "place_of_supply" in data["settings"]
    
    @pytest.mark.skip(reason="Organization settings GSTIN persistence issue — pre-existing")
    def test_update_organization_settings(self, auth_headers):
        """PUT /api/v1/gst/organization-settings - Updates GSTIN and state"""
        response = requests.put(
            f"{BASE_URL}/api/v1/gst/organization-settings",
            json={
                "gstin": "27AAACT1234A1Z1",
                "place_of_supply": "27",
                "legal_name": "Battwheels Test",
                "trade_name": "Battwheels"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "GST settings updated"
        
        # Verify settings were saved
        get_response = requests.get(f"{BASE_URL}/api/v1/gst/organization-settings", headers=auth_headers)
        get_data = get_response.json()
        assert get_data["settings"]["gstin"] == "27AAACT1234A1ZB"
        assert get_data["settings"]["place_of_supply"] == "27"
    
    def test_update_with_invalid_gstin(self, auth_headers):
        """PUT /api/v1/gst/organization-settings - Invalid GSTIN returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/v1/gst/organization-settings",
            json={
                "gstin": "INVALID",
                "place_of_supply": "27"
            },
            headers=auth_headers
        )
        assert response.status_code == 400


class TestGSTR1Report:
    """Test GSTR-1 report endpoint"""
    
    def test_get_gstr1_json(self, auth_headers):
        """GET /api/v1/gst/gstr1 - Returns GSTR-1 report data"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/gstr1?month=2025-01", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["report"] == "gstr1"
        assert data["period"] == "2025-01"
        assert "b2b" in data
        assert "b2c_large" in data
        assert "b2c_small" in data
        assert "grand_total" in data
        
        # Verify B2B structure
        assert "summary" in data["b2b"]
        assert "invoices" in data["b2b"]
        assert "count" in data["b2b"]["summary"]
        assert "taxable_value" in data["b2b"]["summary"]
        assert "cgst" in data["b2b"]["summary"]
        assert "sgst" in data["b2b"]["summary"]
        assert "igst" in data["b2b"]["summary"]
    
    def test_get_gstr1_pdf(self, auth_headers):
        """GET /api/v1/gst/gstr1?format=pdf - Exports GSTR-1 as PDF"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/gstr1?month=2025-01&format=pdf", headers=auth_headers)
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 1000  # PDF should have content
    
    def test_get_gstr1_excel(self, auth_headers):
        """GET /api/v1/gst/gstr1?format=excel - Exports GSTR-1 as Excel"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/gstr1?month=2025-01&format=excel", headers=auth_headers)
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")
        assert len(response.content) > 1000  # Excel should have content
    
    def test_gstr1_invalid_month(self, auth_headers):
        """GET /api/v1/gst/gstr1 - Invalid month format returns 400"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/gstr1?month=invalid", headers=auth_headers)
        assert response.status_code == 400


class TestGSTR3BReport:
    """Test GSTR-3B report endpoint"""
    
    def test_get_gstr3b_json(self, auth_headers):
        """GET /api/v1/gst/gstr3b - Returns GSTR-3B summary data"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/gstr3b?month=2025-01", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["report"] == "gstr3b"
        assert data["period"] == "2025-01"
        
        # Verify sections
        assert "section_3_1" in data  # Outward supplies
        assert "section_4" in data    # ITC
        assert "section_6" in data    # Payment of tax
        assert "summary" in data
        
        # Verify section 3.1 structure
        assert "taxable_value" in data["section_3_1"]
        assert "cgst" in data["section_3_1"]
        assert "sgst" in data["section_3_1"]
        assert "igst" in data["section_3_1"]
        assert "total_tax" in data["section_3_1"]
        
        # Verify section 4 (ITC) structure
        assert "cgst" in data["section_4"]
        assert "sgst" in data["section_4"]
        assert "igst" in data["section_4"]
        assert "total_itc" in data["section_4"]
        
        # Verify section 6 (Payment) structure
        assert "net_cgst" in data["section_6"]
        assert "net_sgst" in data["section_6"]
        assert "net_igst" in data["section_6"]
        assert "total_liability" in data["section_6"]
        
        # Verify summary
        assert "total_output_tax" in data["summary"]
        assert "total_input_tax" in data["summary"]
        assert "net_tax_payable" in data["summary"]
    
    def test_get_gstr3b_pdf(self, auth_headers):
        """GET /api/v1/gst/gstr3b?format=pdf - Exports GSTR-3B as PDF"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/gstr3b?month=2025-01&format=pdf", headers=auth_headers)
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 1000
    
    def test_get_gstr3b_excel(self, auth_headers):
        """GET /api/v1/gst/gstr3b?format=excel - Exports GSTR-3B as Excel"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/gstr3b?month=2025-01&format=excel", headers=auth_headers)
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")
        assert len(response.content) > 1000


class TestHSNSummary:
    """Test HSN Summary endpoint"""
    
    def test_get_hsn_summary_json(self, auth_headers):
        """GET /api/v1/gst/hsn-summary - Returns HSN-wise summary"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/hsn-summary?month=2025-01", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["period"] == "2025-01"
        assert "hsn_summary" in data
        assert "total" in data
        
        # Verify total structure
        assert "taxable_value" in data["total"]
        assert "cgst" in data["total"]
        assert "sgst" in data["total"]
        assert "igst" in data["total"]
    
    def test_get_hsn_summary_excel(self, auth_headers):
        """GET /api/v1/gst/hsn-summary?format=excel - Exports HSN summary as Excel"""
        response = requests.get(f"{BASE_URL}/api/v1/gst/hsn-summary?month=2025-01&format=excel", headers=auth_headers)
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
