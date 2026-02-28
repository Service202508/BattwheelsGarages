"""
Battwheels OS - Payroll Statutory Calculation Tests
Sprint 4A-02: Dedicated tests for PF/ESI/PT calculations.

All tests are pure unit tests — no DB required.
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.hr_service import (
    calculate_professional_tax,
    PF_WAGE_CEILING,
    ESI_WAGE_CEILING,
)

# ==================== PF CEILING TESTS ====================

class TestPFWageCeiling:
    """PF contributions are capped at PF_WAGE_CEILING = ₹15,000"""
    
    def test_pf_ceiling_value(self):
        assert PF_WAGE_CEILING == 15000
    
    def test_basic_below_ceiling(self):
        basic = 12000
        pf_wages = min(basic, PF_WAGE_CEILING)
        assert pf_wages == 12000
    
    def test_basic_at_ceiling(self):
        basic = 15000
        pf_wages = min(basic, PF_WAGE_CEILING)
        assert pf_wages == 15000
    
    def test_basic_above_ceiling(self):
        basic = 25000
        pf_wages = min(basic, PF_WAGE_CEILING)
        assert pf_wages == 15000


# ==================== EPS/EPF SPLIT TESTS ====================

class TestEPSEPFSplit:
    """Employer PF split: EPS = 8.33%, EPF = 3.67% of pf_wages"""
    
    def test_split_at_ceiling(self):
        pf_wages = 15000
        employer_eps = round(pf_wages * 0.0833, 2)
        employer_epf = round(pf_wages * 0.0367, 2)
        assert employer_eps == 1249.50
        assert employer_epf == 550.50
    
    def test_split_below_ceiling(self):
        pf_wages = 12000
        employer_eps = round(pf_wages * 0.0833, 2)
        employer_epf = round(pf_wages * 0.0367, 2)
        assert employer_eps == 999.60
        assert employer_epf == 440.40
    
    def test_split_sums_to_12_percent(self):
        """employer_eps + employer_epf ≈ pf_wages * 0.12 within ±1 rupee"""
        for pf_wages in [10000, 12000, 15000]:
            employer_eps = round(pf_wages * 0.0833, 2)
            employer_epf = round(pf_wages * 0.0367, 2)
            total = employer_eps + employer_epf
            expected = pf_wages * 0.12
            assert abs(total - expected) <= 1, (
                f"pf_wages={pf_wages}: eps={employer_eps} + epf={employer_epf} "
                f"= {total}, expected ≈ {expected}"
            )
    
    def test_split_above_ceiling_uses_cap(self):
        basic = 25000
        pf_wages = min(basic, PF_WAGE_CEILING)  # 15000
        employer_eps = round(pf_wages * 0.0833, 2)
        employer_epf = round(pf_wages * 0.0367, 2)
        assert pf_wages == 15000
        assert employer_eps == 1249.50
        assert employer_epf == 550.50


# ==================== PF ADMIN & EDLI TESTS ====================

class TestPFAdminEDLI:
    """PF admin charges = 0.5%, EDLI charges = 0.5% of pf_wages"""
    
    def test_pf_admin_at_ceiling(self):
        pf_wages = 15000
        pf_admin = round(pf_wages * 0.005, 2)
        assert pf_admin == 75.00
    
    def test_edli_at_ceiling(self):
        pf_wages = 15000
        edli = round(pf_wages * 0.005, 2)
        assert edli == 75.00
    
    def test_pf_admin_below_ceiling(self):
        pf_wages = 10000
        pf_admin = round(pf_wages * 0.005, 2)
        assert pf_admin == 50.00
    
    def test_edli_below_ceiling(self):
        pf_wages = 10000
        edli = round(pf_wages * 0.005, 2)
        assert edli == 50.00


# ==================== ESI TESTS ====================

class TestESICeiling:
    """ESI applicable only when gross <= ESI_WAGE_CEILING (₹21,000)"""
    
    def test_esi_ceiling_value(self):
        assert ESI_WAGE_CEILING == 21000
    
    def test_esi_below_ceiling(self):
        gross = 18000
        employee_esi = round(gross * 0.0075, 2)
        employer_esi = round(gross * 0.0325, 2)
        assert employee_esi == 135.00
        assert employer_esi == 585.00
    
    def test_esi_at_ceiling(self):
        gross = 21000
        employee_esi = round(gross * 0.0075, 2)
        employer_esi = round(gross * 0.0325, 2)
        assert employee_esi == 157.50
        assert employer_esi == 682.50
    
    def test_esi_above_ceiling_zero(self):
        gross = 21001
        esi_applies = gross <= ESI_WAGE_CEILING
        assert esi_applies is False
        employee_esi = round(gross * 0.0075, 2) if esi_applies else 0
        employer_esi = round(gross * 0.0325, 2) if esi_applies else 0
        assert employee_esi == 0
        assert employer_esi == 0
    
    def test_esi_well_above_ceiling(self):
        gross = 50000
        esi_applies = gross <= ESI_WAGE_CEILING
        assert esi_applies is False


# ==================== PROFESSIONAL TAX TESTS ====================

class TestProfessionalTax:
    """Professional tax per state slabs"""
    
    def test_mh_below_7500(self):
        assert calculate_professional_tax(7500, "MH", 1) == 0
    
    def test_mh_mid_slab(self):
        assert calculate_professional_tax(7501, "MH", 1) == 175
    
    def test_mh_above_10000_non_feb(self):
        assert calculate_professional_tax(10001, "MH", 6) == 200
    
    def test_mh_february_special(self):
        """Maharashtra: February PT = 300 when gross > 10000"""
        assert calculate_professional_tax(10001, "MH", 2) == 300
    
    def test_mh_february_below_10000(self):
        """MH Feb special only applies when gross > 10000"""
        assert calculate_professional_tax(9000, "MH", 2) == 175
    
    def test_ka_below_threshold(self):
        assert calculate_professional_tax(15000, "KA", 1) == 0
    
    def test_ka_above_threshold(self):
        assert calculate_professional_tax(15001, "KA", 1) == 200
    
    def test_dl_no_pt(self):
        """Delhi has no Professional Tax"""
        assert calculate_professional_tax(50000, "DL", 1) == 0
    
    def test_default_state_no_pt(self):
        """Unknown states default to zero PT"""
        assert calculate_professional_tax(50000, "XX", 1) == 0
    
    def test_up_no_pt(self):
        """Uttar Pradesh has no PT"""
        assert calculate_professional_tax(100000, "UP", 1) == 0
    
    def test_gj_mid_slab(self):
        """Gujarat: ₹6000-₹8999 → ₹80"""
        assert calculate_professional_tax(7000, "GJ", 1) == 80
    
    def test_tn_high_slab(self):
        """Tamil Nadu: above 20000 → ₹166.5"""
        assert calculate_professional_tax(25000, "TN", 1) == 166.5
    
    def test_case_insensitive(self):
        """State code should be case-insensitive"""
        assert calculate_professional_tax(10001, "mh", 1) == 200
        assert calculate_professional_tax(10001, "Mh", 1) == 200
