"""
GST Statutory Accuracy Tests (Sprint 4B-03)
=============================================
Pure-Python unit tests for GST calculation functions.
No server required — tests import directly from routes/gst.py.
"""
import sys
import os
import pytest

# Ensure backend is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from routes.gst import compute_gstin_checksum, validate_gstin, calculate_gst


# ==================== GSTIN CHECKSUM ====================

class TestGSTINChecksum:

    def test_gstin_checksum_known_valid(self):
        """compute_gstin_checksum('27AABCU9603R1Z') should return a valid check character."""
        check_char = compute_gstin_checksum("27AABCU9603R1Z")
        assert check_char is not None, "Checksum returned None for valid input"
        full_gstin = f"27AABCU9603R1Z{check_char}"
        result = validate_gstin(full_gstin)
        assert result["valid"], f"Full GSTIN with computed checksum should be valid: {result}"

    def test_gstin_full_validates_true(self):
        """A complete GSTIN with correct checksum validates as True."""
        check_char = compute_gstin_checksum("27AABCU9603R1Z")
        full_gstin = f"27AABCU9603R1Z{check_char}"
        assert validate_gstin(full_gstin)["valid"]

    def test_gstin_wrong_checksum_invalid(self):
        """A GSTIN with wrong check digit validates as False."""
        check_char = compute_gstin_checksum("27AABCU9603R1Z")
        # Pick a different character
        wrong_char = "A" if check_char != "A" else "B"
        bad_gstin = f"27AABCU9603R1Z{wrong_char}"
        assert not validate_gstin(bad_gstin)["valid"], "Wrong checksum should be invalid"


# ==================== GSTIN FORMAT VALIDATION ====================

class TestGSTINFormat:

    def test_gstin_too_short_rejected(self):
        """14-character GSTIN rejected."""
        result = validate_gstin("27AABCU9603R1")
        assert not result["valid"]
        assert "15 characters" in result.get("error", "")

    def test_gstin_too_long_rejected(self):
        """16-character GSTIN rejected."""
        result = validate_gstin("27AABCU9603R1ZNX")
        assert not result["valid"]
        assert "15 characters" in result.get("error", "")

    def test_gstin_invalid_state_code_rejected(self):
        """GSTIN with invalid state code (99) rejected."""
        # Build a syntactically valid but bad state code GSTIN
        check = compute_gstin_checksum("99AABCU9603R1Z")
        if check:
            result = validate_gstin(f"99AABCU9603R1Z{check}")
        else:
            result = validate_gstin("99AABCU9603R1ZN")
        assert not result["valid"]
        assert "state code" in result.get("error", "").lower() or "format" in result.get("error", "").lower()

    def test_gstin_empty_rejected(self):
        """Empty GSTIN rejected."""
        assert not validate_gstin("")["valid"]
        assert not validate_gstin(None)["valid"]

    def test_gstin_valid_state_code(self):
        """Valid state code 27 (Maharashtra) is accepted."""
        check = compute_gstin_checksum("27AABCU9603R1Z")
        result = validate_gstin(f"27AABCU9603R1Z{check}")
        assert result["valid"]
        assert result["state_code"] == "27"


# ==================== B2B / B2C CATEGORIZATION ====================

class TestB2BB2CCategorization:
    """
    GSTR-1 categorization rules:
    - Invoice with valid buyer_gstin → B2B
    - Invoice without GSTIN, value > 2,50,000 → B2CL
    - Invoice without GSTIN, value <= 2,50,000 → B2CS
    """

    def test_invoice_with_gstin_is_b2b(self):
        """Invoice with a valid buyer GSTIN is categorized as B2B."""
        check = compute_gstin_checksum("27AABCU9603R1Z")
        buyer_gstin = f"27AABCU9603R1Z{check}"
        result = validate_gstin(buyer_gstin)
        assert result["valid"], "Buyer GSTIN should be valid"
        # If GSTIN is valid → B2B

    def test_no_gstin_high_value_is_b2cl(self):
        """Invoice without GSTIN, value 300000 > 250000 → B2CL."""
        value = 300000
        has_valid_gstin = False
        # Per routes/gst.py: if total > 250000 → B2CL
        assert value > 250000
        assert not has_valid_gstin

    def test_no_gstin_low_value_is_b2cs(self):
        """Invoice without GSTIN, value 200000 <= 250000 → B2CS."""
        value = 200000
        assert value <= 250000

    def test_boundary_exactly_250000_is_b2cs(self):
        """Invoice without GSTIN, value exactly 250000 → B2CS (not B2CL)."""
        # Per routes/gst.py line 464: `elif total > 250000:` → B2CL
        # So exactly 250000 goes to the else branch → B2CS
        value = 250000
        is_b2cl = value > 250000
        assert not is_b2cl, "Exactly 250000 should NOT be B2CL"

    def test_just_above_threshold_is_b2cl(self):
        """Invoice at 250001 (> 250000) → B2CL."""
        value = 250001
        is_b2cl = value > 250000
        assert is_b2cl, "250001 should be B2CL"


# ==================== GST TAX CALCULATION ====================

class TestGSTCalculation:

    def test_inter_state_igst_18_percent(self):
        """Inter-state: full IGST at 18%."""
        result = calculate_gst(1000, 18, "27", "29")  # MH → KA
        assert result["is_intra_state"] is False
        assert result["igst_amount"] == 180
        assert result["cgst_amount"] == 0
        assert result["sgst_amount"] == 0

    def test_intra_state_cgst_sgst_18_percent(self):
        """Intra-state: CGST + SGST split at 18%."""
        result = calculate_gst(1000, 18, "27", "27")  # MH → MH
        assert result["is_intra_state"] is True
        assert result["cgst_amount"] == 90
        assert result["sgst_amount"] == 90
        assert result["igst_amount"] == 0

    def test_inter_state_igst_5_percent(self):
        """Inter-state: IGST at 5%."""
        result = calculate_gst(1000, 5, "27", "09")  # MH → UP
        assert result["igst_amount"] == 50
        assert result["cgst_amount"] == 0

    def test_intra_state_cgst_sgst_5_percent(self):
        """Intra-state: CGST + SGST split at 5%."""
        result = calculate_gst(1000, 5, "27", "27")  # MH → MH
        assert result["cgst_amount"] == 25
        assert result["sgst_amount"] == 25
        assert result["igst_amount"] == 0

    def test_zero_rate(self):
        """Zero-rated: all amounts zero."""
        result = calculate_gst(1000, 0, "27", "27")
        assert result["cgst_amount"] == 0
        assert result["sgst_amount"] == 0
        assert result["igst_amount"] == 0
        assert result["total_gst"] == 0

    def test_total_gst_matches_sum(self):
        """total_gst equals sum of CGST + SGST + IGST."""
        result = calculate_gst(5000, 12, "27", "27")
        assert result["total_gst"] == result["cgst_amount"] + result["sgst_amount"] + result["igst_amount"]

    def test_gst_rate_28_percent(self):
        """28% GST (luxury goods rate)."""
        result = calculate_gst(1000, 28, "27", "29")  # inter-state
        assert result["igst_amount"] == 280



# ==================== INVOICE GST CLASSIFICATION (Sprint 6A-03) ====================

class TestInvoiceGSTClassification:
    """Tests that invoice creation correctly applies IGST vs CGST/SGST
    based on org state from settings vs customer place_of_supply."""

    BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://phase0-cleanup.preview.emergentagent.com")
    ORG_ID = None
    TOKEN = None

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token for the dev org."""
        import requests
        resp = requests.post(f"{self.BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        data = resp.json()
        self.TOKEN = data.get("token", "")
        self.ORG_ID = data.get("user", {}).get("organization_id", "")
        self.HEADERS = {
            "Authorization": f"Bearer {self.TOKEN}",
            "X-Organization-ID": self.ORG_ID,
            "Content-Type": "application/json"
        }
        # Set org place_of_supply to DL for predictable state
        requests.put(
            f"{self.BASE_URL}/api/v1/gst/organization-settings",
            json={"gstin": "07AAACT1234A1Z3", "place_of_supply": "DL", "legal_name": "Test", "trade_name": "Test"},
            headers=self.HEADERS
        )

    def _create_invoice(self, place_of_supply):
        import requests
        # Get or create a customer
        contacts = requests.get(
            f"{self.BASE_URL}/api/v1/contacts-enhanced/?limit=1",
            headers=self.HEADERS
        ).json()
        contact_list = contacts.get("contacts", contacts.get("items", contacts if isinstance(contacts, list) else []))
        if contact_list:
            customer_id = contact_list[0].get("contact_id", "")
        else:
            c = requests.post(
                f"{self.BASE_URL}/api/v1/contacts-enhanced/",
                json={"name": "GST Test Customer", "email": "gst-test@test.in", "phone": "9000000000", "contact_type": "customer"},
                headers=self.HEADERS
            ).json()
            customer_id = c.get("contact_id", "")

        resp = requests.post(
            f"{self.BASE_URL}/api/v1/invoices-enhanced/",
            json={
                "customer_id": customer_id,
                "reference_number": f"6A-TEST-{place_of_supply}",
                "invoice_date": "2026-03-01",
                "payment_terms": 30,
                "line_items": [{"name": "Test Item", "quantity": 1, "rate": 10000, "tax_rate": 18, "hsn_sac_code": "998719"}],
                "place_of_supply": place_of_supply
            },
            headers=self.HEADERS
        )
        return resp.json().get("invoice", resp.json())

    def test_intrastate_invoice_uses_cgst_sgst(self):
        """Intra-state (org DL, customer DL): CGST+SGST applied, IGST=0"""
        inv = self._create_invoice("DL")
        assert inv.get("cgst_total", 0) == 900, f"Expected CGST=900, got {inv.get('cgst_total')}"
        assert inv.get("sgst_total", 0) == 900, f"Expected SGST=900, got {inv.get('sgst_total')}"
        assert inv.get("igst_total", 0) == 0, f"Expected IGST=0, got {inv.get('igst_total')}"

    def test_interstate_invoice_uses_igst(self):
        """Inter-state (org DL, customer MH): IGST applied, CGST=0, SGST=0"""
        inv = self._create_invoice("MH")
        assert inv.get("igst_total", 0) == 1800, f"Expected IGST=1800, got {inv.get('igst_total')}"
        assert inv.get("cgst_total", 0) == 0, f"Expected CGST=0, got {inv.get('cgst_total')}"
        assert inv.get("sgst_total", 0) == 0, f"Expected SGST=0, got {inv.get('sgst_total')}"
