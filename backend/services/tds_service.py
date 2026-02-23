"""
Battwheels OS - TDS Calculation Service (P1)
============================================

Comprehensive TDS (Tax Deducted at Source) calculation engine for Indian payroll.

Features:
- New Regime (FY 2024-25) and Old Regime tax calculation
- HRA exemption calculation
- Chapter VIA deductions (80C, 80D, 80CCD, etc.)
- Monthly TDS calculation with YTD adjustment
- Form 16 data generation
- Journal entries for payroll

Tax Slabs FY 2024-25:
- New Regime: 0-3L (NIL), 3-7L (5%), 7-10L (10%), 10-12L (15%), 12-15L (20%), >15L (30%)
- Old Regime: 0-2.5L (NIL), 2.5-5L (5%), 5-10L (20%), >10L (30%)
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import re
import logging

logger = logging.getLogger(__name__)


# ==================== CONSTANTS ====================

# Standard Deduction (FY 2024-25) - Both regimes
STANDARD_DEDUCTION = 50000

# Section 80C Maximum
MAX_80C = 150000

# Section 80D Maximum
MAX_80D_SELF = 25000
MAX_80D_PARENTS = 25000
MAX_80D_SENIOR_PARENTS = 50000

# Section 80CCD(1B) NPS Maximum
MAX_80CCD_1B = 50000

# Section 80TTA Maximum (Savings Interest)
MAX_80TTA = 10000

# Cess Rate
CESS_RATE = 0.04  # 4% Health & Education Cess

# No PAN TDS Rate (Section 206AA)
NO_PAN_TDS_RATE = 0.20  # 20%

# Surcharge Slabs
SURCHARGE_SLABS = [
    (50_00_000, 1_00_00_000, 0.10),   # 50L-1Cr: 10%
    (1_00_00_000, 2_00_00_000, 0.15), # 1Cr-2Cr: 15%
    (2_00_00_000, 5_00_00_000, 0.25), # 2Cr-5Cr: 25%
    (5_00_00_000, float('inf'), 0.37) # >5Cr: 37%
]

# New Regime Tax Slabs (FY 2024-25)
NEW_REGIME_SLABS = [
    (0, 3_00_000, 0.00),
    (3_00_000, 7_00_000, 0.05),
    (7_00_000, 10_00_000, 0.10),
    (10_00_000, 12_00_000, 0.15),
    (12_00_000, 15_00_000, 0.20),
    (15_00_000, float('inf'), 0.30)
]

# Old Regime Tax Slabs
OLD_REGIME_SLABS = [
    (0, 2_50_000, 0.00),
    (2_50_000, 5_00_000, 0.05),
    (5_00_000, 10_00_000, 0.20),
    (10_00_000, float('inf'), 0.30)
]

# Rebate under Section 87A
REBATE_LIMIT_NEW_REGIME = 7_00_000
REBATE_LIMIT_OLD_REGIME = 5_00_000


# ==================== PAN VALIDATION ====================

def validate_pan(pan: str) -> Tuple[bool, str]:
    """
    Validate PAN format: AAAAA0000A
    First 5: Letters, Next 4: Numbers, Last 1: Letter
    Fourth character indicates holder type (P=Individual, C=Company, etc.)
    """
    if not pan:
        return False, "PAN number is required"
    
    pan = pan.upper().strip()
    
    if len(pan) != 10:
        return False, "PAN must be exactly 10 characters"
    
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    if not re.match(pattern, pan):
        return False, "Invalid PAN format. Expected: AAAAA0000A"
    
    # Fourth character must be valid entity type
    entity_types = ['A', 'B', 'C', 'F', 'G', 'H', 'L', 'J', 'P', 'T', 'E']
    if pan[3] not in entity_types:
        return False, f"Invalid entity type in PAN. Fourth character must be one of: {', '.join(entity_types)}"
    
    return True, "Valid PAN"


# ==================== HRA EXEMPTION CALCULATION ====================

def calculate_hra_exemption(
    basic_annual: float,
    hra_received_annual: float,
    rent_paid_annual: float,
    is_metro: bool = True
) -> float:
    """
    Calculate HRA exemption (Old Regime only)
    
    Exempt HRA = Minimum of:
    1. Actual HRA received
    2. Rent paid minus 10% of basic salary
    3. 50% of basic (metro) or 40% of basic (non-metro)
    """
    if rent_paid_annual <= 0 or hra_received_annual <= 0:
        return 0
    
    # Option 1: Actual HRA received
    option1 = hra_received_annual
    
    # Option 2: Rent paid minus 10% of basic
    option2 = max(0, rent_paid_annual - (0.10 * basic_annual))
    
    # Option 3: 50% (metro) or 40% (non-metro) of basic
    metro_percentage = 0.50 if is_metro else 0.40
    option3 = basic_annual * metro_percentage
    
    exempt_hra = min(option1, option2, option3)
    
    return round(exempt_hra, 2)


# ==================== CHAPTER VIA DEDUCTIONS ====================

def calculate_chapter_via_deductions(declarations: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate Chapter VIA deductions (Old Regime only)
    
    Sections covered:
    - 80C: EPF, LIC, PPF, ELSS, Home Loan Principal, etc. (max ₹1.5L)
    - 80D: Health Insurance (max ₹25K self, ₹50K senior parents)
    - 80CCD(1B): NPS (max ₹50K)
    - 80E: Education Loan Interest (actual)
    - 80G: Donations (50% or 100%)
    - 80TTA: Savings Interest (max ₹10K)
    """
    result = {
        "80C": 0,
        "80D": 0,
        "80CCD_1B": 0,
        "80E": 0,
        "80G": 0,
        "80TTA": 0,
        "total": 0
    }
    
    # Section 80C components
    section_80c = 0
    section_80c += declarations.get("epf_contribution", 0)
    section_80c += declarations.get("lic_premium", 0)
    section_80c += declarations.get("ppf_contribution", 0)
    section_80c += declarations.get("elss_investment", 0)
    section_80c += declarations.get("home_loan_principal", 0)
    section_80c += declarations.get("children_tuition", 0)
    section_80c += declarations.get("nsc_fds", 0)
    result["80C"] = min(section_80c, MAX_80C)
    
    # Section 80D - Health Insurance
    section_80d = 0
    section_80d += min(declarations.get("health_insurance_self", 0), MAX_80D_SELF)
    
    parents_limit = MAX_80D_SENIOR_PARENTS if declarations.get("parents_senior_citizen", False) else MAX_80D_PARENTS
    section_80d += min(declarations.get("health_insurance_parents", 0), parents_limit)
    result["80D"] = section_80d
    
    # Section 80CCD(1B) - NPS
    result["80CCD_1B"] = min(declarations.get("nps_contribution", 0), MAX_80CCD_1B)
    
    # Section 80E - Education Loan Interest (no limit)
    result["80E"] = declarations.get("education_loan_interest", 0)
    
    # Section 80G - Donations
    donations_100 = declarations.get("donations_100_percent", 0)
    donations_50 = declarations.get("donations_50_percent", 0) * 0.5
    result["80G"] = donations_100 + donations_50
    
    # Section 80TTA - Savings Interest
    result["80TTA"] = min(declarations.get("savings_interest", 0), MAX_80TTA)
    
    # Total
    result["total"] = sum([
        result["80C"],
        result["80D"],
        result["80CCD_1B"],
        result["80E"],
        result["80G"],
        result["80TTA"]
    ])
    
    return result


# ==================== TAX SLAB CALCULATION ====================

def calculate_tax_on_slabs(taxable_income: float, slabs: List[Tuple]) -> float:
    """
    Calculate tax based on income slabs
    """
    tax = 0.0
    
    for lower, upper, rate in slabs:
        if taxable_income <= lower:
            break
        
        taxable_in_slab = min(taxable_income, upper) - lower
        tax += taxable_in_slab * rate
    
    return round(tax, 2)


def calculate_surcharge(tax: float, taxable_income: float) -> float:
    """
    Calculate surcharge for high earners
    """
    for lower, upper, rate in SURCHARGE_SLABS:
        if lower < taxable_income <= upper:
            surcharge = tax * rate
            
            # Marginal relief at threshold
            if taxable_income - lower < surcharge:
                surcharge = taxable_income - lower
            
            return round(surcharge, 2)
    
    return 0.0


# ==================== MAIN TDS CALCULATION ENGINE ====================

class TDSCalculator:
    """
    TDS Calculation Engine
    
    Calculates monthly TDS based on:
    - Annual income projection
    - Tax regime (New/Old)
    - Applicable deductions
    - YTD TDS already deducted
    """
    
    def __init__(self, db):
        self.db = db
    
    async def calculate_annual_tax(
        self,
        employee_id: str,
        financial_year: str,  # Format: "2024-25"
        salary_structure: Dict[str, float],
        tax_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate annual tax liability
        
        Args:
            employee_id: Employee ID
            financial_year: FY in format "2024-25"
            salary_structure: Monthly salary components
            tax_config: Employee tax configuration (regime, declarations)
        
        Returns:
            Detailed tax calculation breakdown
        """
        # Extract salary components (monthly)
        basic_monthly = salary_structure.get("basic", 0)
        hra_monthly = salary_structure.get("hra", 0)
        da_monthly = salary_structure.get("da", 0)
        special_monthly = salary_structure.get("special_allowance", 0)
        other_monthly = salary_structure.get("other_allowances", 0)
        
        # Annual amounts
        basic_annual = basic_monthly * 12
        hra_annual = hra_monthly * 12
        gross_annual = (basic_monthly + hra_monthly + da_monthly + special_monthly + other_monthly) * 12
        
        # Add expected bonus/arrears
        bonus = salary_structure.get("expected_bonus", 0)
        arrears = salary_structure.get("expected_arrears", 0)
        gross_annual += bonus + arrears
        
        # Tax regime
        tax_regime = tax_config.get("tax_regime", "new")
        declarations = tax_config.get("declarations", {})
        has_pan = bool(tax_config.get("pan_number"))
        
        # Initialize calculation
        calc = {
            "employee_id": employee_id,
            "financial_year": financial_year,
            "tax_regime": tax_regime,
            "has_pan": has_pan,
            "gross_annual": gross_annual,
            "exempt_allowances": 0,
            "standard_deduction": STANDARD_DEDUCTION,
            "chapter_via_deductions": 0,
            "taxable_income": 0,
            "tax_before_rebate": 0,
            "rebate_87a": 0,
            "tax_after_rebate": 0,
            "surcharge": 0,
            "cess": 0,
            "total_tax_liability": 0,
            "breakdown": {}
        }
        
        # Step 1: Calculate Exempt Allowances (Old Regime only)
        if tax_regime == "old":
            # HRA Exemption
            hra_exemption = 0
            if declarations.get("rent_paid_monthly", 0) > 0:
                hra_exemption = calculate_hra_exemption(
                    basic_annual=basic_annual,
                    hra_received_annual=hra_annual,
                    rent_paid_annual=declarations.get("rent_paid_monthly", 0) * 12,
                    is_metro=declarations.get("is_metro_city", True)
                )
            
            # LTA Exemption (only if claimed)
            lta_exemption = declarations.get("lta_claimed", 0)
            
            # Children Education + Hostel Allowance
            # ₹100/month/child (max 2) + ₹300/month/child (max 2)
            children = min(declarations.get("number_of_children", 0), 2)
            children_education = children * 100 * 12
            hostel_allowance = children * 300 * 12 if declarations.get("children_in_hostel", False) else 0
            
            calc["exempt_allowances"] = hra_exemption + lta_exemption + children_education + hostel_allowance
            calc["breakdown"]["hra_exemption"] = hra_exemption
            calc["breakdown"]["lta_exemption"] = lta_exemption
            calc["breakdown"]["children_education"] = children_education
            calc["breakdown"]["hostel_allowance"] = hostel_allowance
        
        # Step 2: Adjusted Gross Salary
        adjusted_gross = gross_annual - calc["exempt_allowances"]
        calc["breakdown"]["adjusted_gross"] = adjusted_gross
        
        # Step 3: Less Standard Deduction
        net_salary_income = adjusted_gross - STANDARD_DEDUCTION
        calc["breakdown"]["net_salary_income"] = net_salary_income
        
        # Step 4: Add/Less Other Income
        other_income = declarations.get("other_income", 0)
        income_before_deductions = net_salary_income + other_income
        calc["breakdown"]["other_income"] = other_income
        calc["breakdown"]["income_before_deductions"] = income_before_deductions
        
        # Step 5: Chapter VIA Deductions (Old Regime only)
        if tax_regime == "old":
            via_deductions = calculate_chapter_via_deductions(declarations)
            calc["chapter_via_deductions"] = via_deductions["total"]
            calc["breakdown"]["chapter_via"] = via_deductions
        
        # Step 6: Net Taxable Income
        taxable_income = max(0, income_before_deductions - calc["chapter_via_deductions"])
        calc["taxable_income"] = taxable_income
        
        # Step 7: Calculate Tax Based on Slabs
        slabs = NEW_REGIME_SLABS if tax_regime == "new" else OLD_REGIME_SLABS
        tax_before_rebate = calculate_tax_on_slabs(taxable_income, slabs)
        calc["tax_before_rebate"] = tax_before_rebate
        
        # Step 8: Apply Rebate u/s 87A
        rebate_limit = REBATE_LIMIT_NEW_REGIME if tax_regime == "new" else REBATE_LIMIT_OLD_REGIME
        if taxable_income <= rebate_limit:
            calc["rebate_87a"] = tax_before_rebate
            tax_after_rebate = 0
        else:
            calc["rebate_87a"] = 0
            tax_after_rebate = tax_before_rebate
        calc["tax_after_rebate"] = tax_after_rebate
        
        # Step 9: Calculate Surcharge (high earners)
        surcharge = calculate_surcharge(tax_after_rebate, taxable_income)
        calc["surcharge"] = surcharge
        
        # Step 10: Calculate Cess
        tax_plus_surcharge = tax_after_rebate + surcharge
        cess = round(tax_plus_surcharge * CESS_RATE, 2)
        calc["cess"] = cess
        
        # Step 11: Total Tax Liability
        total_tax = tax_plus_surcharge + cess
        calc["total_tax_liability"] = round(total_tax, 2)
        
        # Special case: No PAN - 20% flat rate
        if not has_pan and total_tax > 0:
            no_pan_tax = gross_annual * NO_PAN_TDS_RATE
            if no_pan_tax > total_tax:
                calc["total_tax_liability"] = round(no_pan_tax, 2)
                calc["breakdown"]["no_pan_rate_applied"] = True
        
        return calc
    
    async def calculate_monthly_tds(
        self,
        employee_id: str,
        month: int,  # 1-12 (April=1, March=12)
        year: int,   # Calendar year
        salary_structure: Dict[str, float],
        tax_config: Dict[str, Any],
        ytd_tds_deducted: float = 0
    ) -> Dict[str, Any]:
        """
        Calculate monthly TDS
        
        Monthly TDS = (Annual Tax - YTD TDS) / Remaining Months
        """
        # Determine financial year
        fy_start_year = year if month >= 4 else year - 1
        financial_year = f"{fy_start_year}-{str(fy_start_year + 1)[-2:]}"
        
        # Calculate annual tax
        annual_calc = await self.calculate_annual_tax(
            employee_id=employee_id,
            financial_year=financial_year,
            salary_structure=salary_structure,
            tax_config=tax_config
        )
        
        annual_tax = annual_calc["total_tax_liability"]
        
        # Calculate remaining months in FY
        # April = month 1, March = month 12
        fy_month = month if month >= 4 else month + 9  # Convert to FY month number
        remaining_months = 12 - fy_month + 1
        
        # Calculate monthly TDS
        remaining_tax = max(0, annual_tax - ytd_tds_deducted)
        
        if remaining_months <= 0:
            monthly_tds = remaining_tax  # Last month - deduct all
        else:
            monthly_tds = remaining_tax / remaining_months
        
        # Round to nearest rupee
        monthly_tds = round(monthly_tds, 0)
        
        return {
            "employee_id": employee_id,
            "month": month,
            "year": year,
            "financial_year": financial_year,
            "annual_calculation": annual_calc,
            "annual_tax_liability": annual_tax,
            "ytd_tds_deducted": ytd_tds_deducted,
            "remaining_tax": remaining_tax,
            "remaining_months": remaining_months,
            "monthly_tds": monthly_tds,
            "is_final_month": remaining_months == 1
        }
    
    async def get_ytd_tds(self, employee_id: str, financial_year: str) -> float:
        """
        Get Year-to-Date TDS already deducted
        """
        # Parse financial year
        fy_start_year = int(financial_year.split("-")[0])
        
        # Query payroll records for this FY
        pipeline = [
            {
                "$match": {
                    "employee_id": employee_id,
                    "$or": [
                        {"year": fy_start_year, "month": {"$gte": 4}},  # Apr-Dec
                        {"year": fy_start_year + 1, "month": {"$lte": 3}}  # Jan-Mar
                    ],
                    "status": {"$in": ["processed", "paid"]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_tds": {"$sum": "$deductions.tds"}
                }
            }
        ]
        
        result = await self.db.payroll.aggregate(pipeline).to_list(1)
        
        return result[0]["total_tds"] if result else 0


# ==================== FORM 16 DATA GENERATOR ====================

class Form16Generator:
    """
    Generate Form 16 data structure for an employee
    """
    
    def __init__(self, db):
        self.db = db
        self.tds_calculator = TDSCalculator(db)
    
    async def generate_form16_data(
        self,
        employee_id: str,
        assessment_year: str,  # e.g., "2025-26" for FY 2024-25
        employer_details: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate Form 16 Part A and Part B data
        
        Args:
            employee_id: Employee ID
            assessment_year: Assessment year (FY + 1)
            employer_details: TAN, PAN, name, address of employer
        """
        # Calculate financial year from assessment year
        ay_start = int(assessment_year.split("-")[0])
        fy_start = ay_start - 1
        financial_year = f"{fy_start}-{str(fy_start + 1)[-2:]}"
        
        # Get employee details
        employee = await self.db.employees.find_one(
            {"employee_id": employee_id},
            {"_id": 0}
        )
        
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        # Get all payroll records for the FY
        payroll_records = await self.db.payroll.find({
            "employee_id": employee_id,
            "$or": [
                {"year": fy_start, "month": {"$gte": 4}},
                {"year": fy_start + 1, "month": {"$lte": 3}}
            ],
            "status": {"$in": ["processed", "paid"]}
        }, {"_id": 0}).to_list(12)
        
        # Get TDS challans
        challans = await self.db.tds_challans.find({
            "organization_id": employer_details.get("organization_id"),
            "financial_year": financial_year
        }, {"_id": 0}).to_list(100)
        
        # Calculate totals
        total_gross = sum(p.get("earnings", {}).get("gross", 0) for p in payroll_records)
        total_tds = sum(p.get("deductions", {}).get("tds", 0) for p in payroll_records)
        
        # Quarter-wise breakdown
        quarters = {
            "Q1": {"months": [4, 5, 6], "tds_deducted": 0, "tds_deposited": 0, "challans": []},
            "Q2": {"months": [7, 8, 9], "tds_deducted": 0, "tds_deposited": 0, "challans": []},
            "Q3": {"months": [10, 11, 12], "tds_deducted": 0, "tds_deposited": 0, "challans": []},
            "Q4": {"months": [1, 2, 3], "tds_deducted": 0, "tds_deposited": 0, "challans": []}
        }
        
        for record in payroll_records:
            month = record.get("month", 0)
            tds = record.get("deductions", {}).get("tds", 0)
            
            for q_name, q_data in quarters.items():
                if month in q_data["months"]:
                    q_data["tds_deducted"] += tds
                    break
        
        # Match challans to quarters
        for challan in challans:
            quarter = challan.get("quarter")
            if quarter in quarters:
                quarters[quarter]["tds_deposited"] += challan.get("amount", 0)
                quarters[quarter]["challans"].append({
                    "challan_number": challan.get("challan_number"),
                    "date": challan.get("deposit_date"),
                    "amount": challan.get("amount")
                })
        
        # Get tax calculation
        tax_config = employee.get("tax_config", {})
        salary_structure = employee.get("salary_structure", {})
        
        annual_calc = await self.tds_calculator.calculate_annual_tax(
            employee_id=employee_id,
            financial_year=financial_year,
            salary_structure=salary_structure,
            tax_config=tax_config
        )
        
        # Build Form 16 data structure
        form16_data = {
            "form_type": "Form 16",
            "assessment_year": assessment_year,
            "financial_year": financial_year,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            
            # Part A - Certificate of TDS
            "part_a": {
                "employer": {
                    "tan": employer_details.get("tan"),
                    "pan": employer_details.get("pan"),
                    "name": employer_details.get("name"),
                    "address": employer_details.get("address")
                },
                "employee": {
                    "pan": employee.get("pan_number", tax_config.get("pan_number")),
                    "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
                    "designation": employee.get("designation"),
                    "address": employee.get("address", {})
                },
                "period_of_employment": {
                    "from": employee.get("joining_date") or f"{fy_start}-04-01",
                    "to": f"{fy_start + 1}-03-31"  # Assuming full year
                },
                "quarter_wise_summary": quarters,
                "total_tds_deducted": total_tds,
                "total_tds_deposited": sum(q["tds_deposited"] for q in quarters.values())
            },
            
            # Part B - Details of Salary Paid and Tax Deducted
            "part_b": {
                "gross_salary": annual_calc["gross_annual"],
                "exempt_allowances": {
                    "hra": annual_calc.get("breakdown", {}).get("hra_exemption", 0),
                    "lta": annual_calc.get("breakdown", {}).get("lta_exemption", 0),
                    "other": annual_calc.get("breakdown", {}).get("children_education", 0) + 
                             annual_calc.get("breakdown", {}).get("hostel_allowance", 0),
                    "total": annual_calc["exempt_allowances"]
                },
                "net_salary": annual_calc["gross_annual"] - annual_calc["exempt_allowances"],
                "standard_deduction": annual_calc["standard_deduction"],
                "income_from_salary": annual_calc.get("breakdown", {}).get("net_salary_income", 0),
                "other_income": annual_calc.get("breakdown", {}).get("other_income", 0),
                "gross_total_income": annual_calc.get("breakdown", {}).get("income_before_deductions", 0),
                "deductions_via": annual_calc.get("breakdown", {}).get("chapter_via", {}),
                "total_deductions": annual_calc["chapter_via_deductions"],
                "total_taxable_income": annual_calc["taxable_income"],
                "tax_on_total_income": annual_calc["tax_before_rebate"],
                "rebate_87a": annual_calc["rebate_87a"],
                "tax_after_rebate": annual_calc["tax_after_rebate"],
                "surcharge": annual_calc["surcharge"],
                "cess": annual_calc["cess"],
                "total_tax_liability": annual_calc["total_tax_liability"],
                "tds_deducted": total_tds,
                "balance_tax": annual_calc["total_tax_liability"] - total_tds
            }
        }
        
        return form16_data


# ==================== PAYROLL JOURNAL ENTRY GENERATOR ====================

async def generate_payroll_journal_entries(
    db,
    payroll_run_id: str,
    month: str,
    year: int,
    organization_id: str,
    payroll_summary: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate journal entries for payroll run (Step 3)
    
    Entry 1: Salary Expense Accrual
    Entry 2: TDS Payable
    Entry 3: PF Payable
    Entry 4: ESI Payable
    """
    from services.double_entry_service import get_double_entry_service
    
    journal_entries = []
    now = datetime.now(timezone.utc)
    
    de_service = get_double_entry_service()
    
    # Extract totals
    total_gross = payroll_summary.get("total_gross", 0)
    total_net = payroll_summary.get("total_net", 0)
    total_tds = payroll_summary.get("total_tds", 0)
    total_employee_pf = payroll_summary.get("total_employee_pf", 0)
    total_employer_pf = payroll_summary.get("total_employer_pf", 0)
    total_employee_esi = payroll_summary.get("total_employee_esi", 0)
    total_employer_esi = payroll_summary.get("total_employer_esi", 0)
    total_professional_tax = payroll_summary.get("total_professional_tax", 0)
    employee_count = payroll_summary.get("employee_count", 0)
    
    # Entry 1: Salary Expense Accrual
    entry1_lines = []
    
    # Debits
    entry1_lines.append({
        "account_type": "SALARY_EXPENSE",
        "debit": total_gross,
        "credit": 0,
        "description": f"Salary expense for {month} {year}"
    })
    
    if total_employer_pf > 0:
        entry1_lines.append({
            "account_type": "EMPLOYER_PF_EXPENSE",
            "debit": total_employer_pf,
            "credit": 0,
            "description": "Employer PF contribution"
        })
    
    if total_employer_esi > 0:
        entry1_lines.append({
            "account_type": "EMPLOYER_ESI_EXPENSE",
            "debit": total_employer_esi,
            "credit": 0,
            "description": "Employer ESI contribution"
        })
    
    # Credits
    entry1_lines.append({
        "account_type": "SALARY_PAYABLE",
        "debit": 0,
        "credit": total_net,
        "description": "Net salary payable"
    })
    
    if total_tds > 0:
        entry1_lines.append({
            "account_type": "TDS_PAYABLE",
            "debit": 0,
            "credit": total_tds,
            "description": "TDS deducted"
        })
    
    if total_employee_pf > 0:
        entry1_lines.append({
            "account_type": "EMPLOYEE_PF_PAYABLE",
            "debit": 0,
            "credit": total_employee_pf,
            "description": "Employee PF deducted"
        })
    
    if total_employer_pf > 0:
        entry1_lines.append({
            "account_type": "EMPLOYER_PF_PAYABLE",
            "debit": 0,
            "credit": total_employer_pf,
            "description": "Employer PF payable"
        })
    
    if total_employee_esi + total_employer_esi > 0:
        entry1_lines.append({
            "account_type": "ESI_PAYABLE",
            "debit": 0,
            "credit": total_employee_esi + total_employer_esi,
            "description": "ESI payable (employee + employer)"
        })
    
    if total_professional_tax > 0:
        entry1_lines.append({
            "account_type": "PROFESSIONAL_TAX_PAYABLE",
            "debit": 0,
            "credit": total_professional_tax,
            "description": "Professional tax deducted"
        })
    
    # Create journal entry
    total_debit = sum(line["debit"] for line in entry1_lines)
    total_credit = sum(line["credit"] for line in entry1_lines)
    
    entry1 = {
        "entry_type": "PAYROLL",
        "organization_id": organization_id,
        "reference_type": "PAYROLL_RUN",
        "reference_id": payroll_run_id,
        "date": now.isoformat(),
        "narration": f"Payroll for {month} {year} — {employee_count} employees",
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "lines": entry1_lines,
        "created_at": now
    }
    
    await db.journal_entries.insert_one(entry1)
    journal_entries.append(entry1)
    
    logger.info(f"Created payroll journal entry for {month} {year}: ₹{total_debit:,.2f}")
    
    return journal_entries


# ==================== SERVICE FACTORY ====================

_tds_calculator: Optional[TDSCalculator] = None
_form16_generator: Optional[Form16Generator] = None


def get_tds_calculator() -> TDSCalculator:
    if _tds_calculator is None:
        raise ValueError("TDSCalculator not initialized")
    return _tds_calculator


def get_form16_generator() -> Form16Generator:
    if _form16_generator is None:
        raise ValueError("Form16Generator not initialized")
    return _form16_generator


def init_tds_service(db):
    global _tds_calculator, _form16_generator
    _tds_calculator = TDSCalculator(db)
    _form16_generator = Form16Generator(db)
    logger.info("TDS Service initialized")
    return _tds_calculator
