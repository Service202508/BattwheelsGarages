"""Indian Financial Year utilities (April 1 - March 31)."""
from datetime import date, datetime


def get_indian_financial_year(reference_date: date = None) -> dict:
    if reference_date is None:
        reference_date = date.today()
    year = reference_date.year
    month = reference_date.month
    fy_start_year = year if month >= 4 else year - 1
    fy_end_year = fy_start_year + 1
    return {
        "start": datetime(fy_start_year, 4, 1),
        "end": datetime(fy_end_year, 3, 31, 23, 59, 59),
        "label": f"FY {fy_start_year}-{str(fy_end_year)[2:]}",
        "start_year": fy_start_year,
        "end_year": fy_end_year,
    }
