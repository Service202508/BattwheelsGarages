"""
Comprehensive Reports Endpoint Tests
======================================
Tests for /api/v1/reports/* and /api/v1/reports-advanced/* endpoints.
Uses shared conftest.py fixtures (base_url, dev_headers).

Run: pytest backend/tests/test_reports_comprehensive.py -v --tb=short
"""

import pytest
import requests


@pytest.fixture(scope="module")
def _headers(base_url, dev_token):
    """Auth headers with org context for reports."""
    return {
        "Authorization": f"Bearer {dev_token}",
        "X-Organization-ID": "dev-internal-testing-001",
        "Content-Type": "application/json",
    }


REPORTS = "/api/v1/reports"
ADVANCED = "/api/v1/reports-advanced"


# ==================== FINANCIAL REPORTS (/reports) ====================

class TestProfitAndLoss:

    def test_profit_loss_report(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/profit-loss", headers=_headers)
        assert resp.status_code == 200

    def test_profit_loss_with_dates(self, base_url, _headers):
        resp = requests.get(
            f"{base_url}{REPORTS}/profit-loss?start_date=2025-01-01&end_date=2025-12-31",
            headers=_headers
        )
        assert resp.status_code == 200


class TestBalanceSheet:

    def test_balance_sheet_report(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/balance-sheet", headers=_headers)
        assert resp.status_code == 200


class TestARAgingReport:

    def test_ar_aging(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/ar-aging", headers=_headers)
        assert resp.status_code == 200


class TestAPAgingReport:

    def test_ap_aging(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/ap-aging", headers=_headers)
        assert resp.status_code == 200


class TestSalesByCustomer:

    def test_sales_by_customer(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/sales-by-customer", headers=_headers)
        assert resp.status_code == 200


class TestTechnicianPerformance:

    def test_technician_performance(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/technician-performance", headers=_headers)
        assert resp.status_code == 200


class TestInventoryValuation:

    def test_inventory_valuation(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/inventory-valuation", headers=_headers)
        assert resp.status_code == 200


class TestTrialBalance:

    def test_trial_balance(self, base_url, _headers):
        resp = requests.get(f"{base_url}{REPORTS}/trial-balance", headers=_headers)
        assert resp.status_code == 200


class TestReportsRequireAuth:

    def test_profit_loss_no_auth(self, base_url):
        resp = requests.get(f"{base_url}{REPORTS}/profit-loss")
        assert resp.status_code in [401, 403]


# ==================== ADVANCED REPORTS (/reports-advanced) ====================

class TestMonthlyRevenue:

    def test_monthly_revenue(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/revenue/monthly", headers=_headers)
        # May require entitlement; 200 or 403 both acceptable
        assert resp.status_code in [200, 403]

    def test_monthly_revenue_with_year(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/revenue/monthly?year=2025", headers=_headers)
        assert resp.status_code in [200, 403]


class TestQuarterlyRevenue:

    def test_quarterly_revenue(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/revenue/quarterly", headers=_headers)
        assert resp.status_code in [200, 403]


class TestYearlyComparison:

    def test_yearly_comparison(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/revenue/yearly-comparison", headers=_headers)
        assert resp.status_code in [200, 403]


class TestReceivables:

    def test_receivables_aging(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/receivables/aging", headers=_headers)
        assert resp.status_code in [200, 403]

    def test_receivables_trend(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/receivables/trend", headers=_headers)
        assert resp.status_code in [200, 403]


class TestCustomerReports:

    def test_top_revenue_customers(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/customers/top-revenue", headers=_headers)
        assert resp.status_code in [200, 403]

    def test_top_outstanding_customers(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/customers/top-outstanding", headers=_headers)
        assert resp.status_code in [200, 403]

    def test_customer_acquisition(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/customers/acquisition", headers=_headers)
        assert resp.status_code in [200, 403]


class TestSalesFunnel:

    def test_sales_funnel(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/sales/funnel", headers=_headers)
        assert resp.status_code in [200, 403]


class TestInvoiceDistribution:

    def test_invoice_status_distribution(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/invoices/status-distribution", headers=_headers)
        assert resp.status_code in [200, 403]


class TestPaymentReports:

    def test_payment_trend(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/payments/trend", headers=_headers)
        assert resp.status_code in [200, 403]

    def test_payments_by_mode(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/payments/by-mode", headers=_headers)
        assert resp.status_code in [200, 403]


class TestDashboardSummary:

    def test_dashboard_summary(self, base_url, _headers):
        resp = requests.get(f"{base_url}{ADVANCED}/dashboard-summary", headers=_headers)
        assert resp.status_code in [200, 403]
