"""
Financial Reports Module Tests
Tests for Profit & Loss, Balance Sheet, AR Aging, AP Aging, and Sales by Customer reports
with JSON, PDF, and Excel export capabilities
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestReportsModule:
    """Test Financial Reports endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "dev@battwheels.internal",
            "password": "DevTest@123"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
    
    # ============== PROFIT & LOSS TESTS ==============
    
    def test_profit_loss_json(self):
        """Test GET /api/reports/profit-loss returns JSON data"""
        response = self.session.get(f"{BASE_URL}/api/reports/profit-loss")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("code") == 0, "Expected code 0 for success"
        assert data.get("report") == "profit_and_loss", "Expected report type profit_and_loss"
        
        # Verify required fields
        assert "period" in data, "Missing period field"
        assert "total_income" in data, "Missing total_income field"
        assert "total_cogs" in data, "Missing total_cogs field"
        assert "gross_profit" in data, "Missing gross_profit field"
        assert "total_expenses" in data, "Missing total_expenses field"
        assert "net_profit" in data, "Missing net_profit field"
        assert "margins" in data, "Missing margins field"
        
        # Verify period structure
        assert "start_date" in data["period"], "Missing start_date in period"
        assert "end_date" in data["period"], "Missing end_date in period"
        
        # Verify margins structure
        assert "gross_margin_percent" in data["margins"], "Missing gross_margin_percent"
        assert "net_margin_percent" in data["margins"], "Missing net_margin_percent"
        
        print(f"P&L Report: Income={data['total_income']}, Net Profit={data['net_profit']}")
    
    def test_profit_loss_with_date_filter(self):
        """Test GET /api/reports/profit-loss with date range filter"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/profit-loss",
            params={"start_date": "2025-01-01", "end_date": "2025-12-31"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["period"]["start_date"] == "2025-01-01"
        assert data["period"]["end_date"] == "2025-12-31"
        print(f"P&L with date filter: {data['period']}")
    
    def test_profit_loss_pdf_export(self):
        """Test GET /api/reports/profit-loss?format=pdf exports PDF"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/profit-loss",
            params={"format": "pdf"}
        )
        assert response.status_code == 200, f"PDF export failed: {response.status_code}"
        
        # Verify content type
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got {content_type}"
        
        # Verify content disposition
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, "Expected attachment disposition"
        assert "profit_loss" in content_disp, "Expected profit_loss in filename"
        assert ".pdf" in content_disp, "Expected .pdf extension"
        
        # Verify PDF content (starts with %PDF)
        assert response.content[:4] == b'%PDF', "Content does not appear to be a valid PDF"
        
        print(f"P&L PDF export successful, size: {len(response.content)} bytes")
    
    def test_profit_loss_excel_export(self):
        """Test GET /api/reports/profit-loss?format=excel exports Excel"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/profit-loss",
            params={"format": "excel"}
        )
        assert response.status_code == 200, f"Excel export failed: {response.status_code}"
        
        # Verify content type
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "excel" in content_type.lower(), f"Expected Excel content type, got {content_type}"
        
        # Verify content disposition
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, "Expected attachment disposition"
        assert ".xlsx" in content_disp, "Expected .xlsx extension"
        
        # Verify Excel content (starts with PK for ZIP-based xlsx)
        assert response.content[:2] == b'PK', "Content does not appear to be a valid Excel file"
        
        print(f"P&L Excel export successful, size: {len(response.content)} bytes")
    
    # ============== BALANCE SHEET TESTS ==============
    
    def test_balance_sheet_json(self):
        """Test GET /api/reports/balance-sheet returns JSON data"""
        response = self.session.get(f"{BASE_URL}/api/reports/balance-sheet")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("code") == 0, "Expected code 0 for success"
        assert data.get("report") == "balance_sheet", "Expected report type balance_sheet"
        
        # Verify required fields
        assert "as_of_date" in data, "Missing as_of_date field"
        assert "assets" in data, "Missing assets field"
        assert "liabilities" in data, "Missing liabilities field"
        assert "equity" in data, "Missing equity field"
        
        # Verify assets structure
        assets = data["assets"]
        assert "accounts_receivable" in assets, "Missing accounts_receivable in assets"
        assert "bank_balance" in assets, "Missing bank_balance in assets"
        assert "inventory_value" in assets, "Missing inventory_value in assets"
        assert "total" in assets, "Missing total in assets"
        
        # Verify liabilities structure
        liabilities = data["liabilities"]
        assert "accounts_payable" in liabilities, "Missing accounts_payable in liabilities"
        assert "total" in liabilities, "Missing total in liabilities"
        
        # Verify equity structure
        equity = data["equity"]
        assert "retained_earnings" in equity, "Missing retained_earnings in equity"
        assert "total" in equity, "Missing total in equity"
        
        print(f"Balance Sheet: Assets={assets['total']}, Liabilities={liabilities['total']}, Equity={equity['total']}")
    
    def test_balance_sheet_pdf_export(self):
        """Test GET /api/reports/balance-sheet?format=pdf exports PDF"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/balance-sheet",
            params={"format": "pdf"}
        )
        assert response.status_code == 200, f"PDF export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got {content_type}"
        assert response.content[:4] == b'%PDF', "Content does not appear to be a valid PDF"
        
        print(f"Balance Sheet PDF export successful, size: {len(response.content)} bytes")
    
    def test_balance_sheet_excel_export(self):
        """Test GET /api/reports/balance-sheet?format=excel exports Excel"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/balance-sheet",
            params={"format": "excel"}
        )
        assert response.status_code == 200, f"Excel export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "excel" in content_type.lower(), f"Expected Excel content type, got {content_type}"
        assert response.content[:2] == b'PK', "Content does not appear to be a valid Excel file"
        
        print(f"Balance Sheet Excel export successful, size: {len(response.content)} bytes")
    
    # ============== AR AGING TESTS ==============
    
    def test_ar_aging_json(self):
        """Test GET /api/reports/ar-aging returns JSON data"""
        response = self.session.get(f"{BASE_URL}/api/reports/ar-aging")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("code") == 0, "Expected code 0 for success"
        assert data.get("report") == "ar_aging", "Expected report type ar_aging"
        
        # Verify required fields
        assert "as_of_date" in data, "Missing as_of_date field"
        assert "aging_data" in data, "Missing aging_data field"
        assert "total_ar" in data, "Missing total_ar field"
        assert "invoices" in data, "Missing invoices field"
        
        # Verify aging buckets
        aging = data["aging_data"]
        assert "current" in aging, "Missing current bucket"
        assert "1_30" in aging, "Missing 1_30 bucket"
        assert "31_60" in aging, "Missing 31_60 bucket"
        assert "61_90" in aging, "Missing 61_90 bucket"
        assert "over_90" in aging, "Missing over_90 bucket"
        
        # Verify invoices structure (if any)
        if data["invoices"]:
            inv = data["invoices"][0]
            assert "invoice_number" in inv, "Missing invoice_number in invoice"
            assert "customer_name" in inv, "Missing customer_name in invoice"
            assert "due_date" in inv, "Missing due_date in invoice"
            assert "days_overdue" in inv, "Missing days_overdue in invoice"
            assert "balance" in inv, "Missing balance in invoice"
        
        print(f"AR Aging: Total AR={data['total_ar']}, Invoices count={len(data['invoices'])}")
    
    def test_ar_aging_pdf_export(self):
        """Test GET /api/reports/ar-aging?format=pdf exports PDF"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/ar-aging",
            params={"format": "pdf"}
        )
        assert response.status_code == 200, f"PDF export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got {content_type}"
        assert response.content[:4] == b'%PDF', "Content does not appear to be a valid PDF"
        
        print(f"AR Aging PDF export successful, size: {len(response.content)} bytes")
    
    def test_ar_aging_excel_export(self):
        """Test GET /api/reports/ar-aging?format=excel exports Excel"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/ar-aging",
            params={"format": "excel"}
        )
        assert response.status_code == 200, f"Excel export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "excel" in content_type.lower(), f"Expected Excel content type, got {content_type}"
        assert response.content[:2] == b'PK', "Content does not appear to be a valid Excel file"
        
        print(f"AR Aging Excel export successful, size: {len(response.content)} bytes")
    
    # ============== AP AGING TESTS ==============
    
    def test_ap_aging_json(self):
        """Test GET /api/reports/ap-aging returns JSON data"""
        response = self.session.get(f"{BASE_URL}/api/reports/ap-aging")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("code") == 0, "Expected code 0 for success"
        assert data.get("report") == "ap_aging", "Expected report type ap_aging"
        
        # Verify required fields
        assert "as_of_date" in data, "Missing as_of_date field"
        assert "aging_data" in data, "Missing aging_data field"
        assert "total_ap" in data, "Missing total_ap field"
        assert "bills" in data, "Missing bills field"
        
        # Verify aging buckets
        aging = data["aging_data"]
        assert "current" in aging, "Missing current bucket"
        assert "1_30" in aging, "Missing 1_30 bucket"
        assert "31_60" in aging, "Missing 31_60 bucket"
        assert "61_90" in aging, "Missing 61_90 bucket"
        assert "over_90" in aging, "Missing over_90 bucket"
        
        # Verify bills structure (if any)
        if data["bills"]:
            bill = data["bills"][0]
            assert "bill_number" in bill, "Missing bill_number in bill"
            assert "vendor_name" in bill, "Missing vendor_name in bill"
            assert "due_date" in bill, "Missing due_date in bill"
            assert "days_overdue" in bill, "Missing days_overdue in bill"
            assert "balance" in bill, "Missing balance in bill"
        
        print(f"AP Aging: Total AP={data['total_ap']}, Bills count={len(data['bills'])}")
    
    def test_ap_aging_pdf_export(self):
        """Test GET /api/reports/ap-aging?format=pdf exports PDF"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/ap-aging",
            params={"format": "pdf"}
        )
        assert response.status_code == 200, f"PDF export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got {content_type}"
        assert response.content[:4] == b'%PDF', "Content does not appear to be a valid PDF"
        
        print(f"AP Aging PDF export successful, size: {len(response.content)} bytes")
    
    def test_ap_aging_excel_export(self):
        """Test GET /api/reports/ap-aging?format=excel exports Excel"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/ap-aging",
            params={"format": "excel"}
        )
        assert response.status_code == 200, f"Excel export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "excel" in content_type.lower(), f"Expected Excel content type, got {content_type}"
        assert response.content[:2] == b'PK', "Content does not appear to be a valid Excel file"
        
        print(f"AP Aging Excel export successful, size: {len(response.content)} bytes")
    
    # ============== SALES BY CUSTOMER TESTS ==============
    
    def test_sales_by_customer_json(self):
        """Test GET /api/reports/sales-by-customer returns JSON data"""
        response = self.session.get(f"{BASE_URL}/api/reports/sales-by-customer")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("code") == 0, "Expected code 0 for success"
        assert data.get("report") == "sales_by_customer", "Expected report type sales_by_customer"
        
        # Verify required fields
        assert "period" in data, "Missing period field"
        assert "sales_data" in data, "Missing sales_data field"
        assert "total_sales" in data, "Missing total_sales field"
        assert "total_invoices" in data, "Missing total_invoices field"
        
        # Verify period structure
        assert "start_date" in data["period"], "Missing start_date in period"
        assert "end_date" in data["period"], "Missing end_date in period"
        
        # Verify sales_data structure (if any)
        if data["sales_data"]:
            item = data["sales_data"][0]
            assert "customer_name" in item, "Missing customer_name in sales_data"
            assert "total_sales" in item, "Missing total_sales in sales_data"
            assert "invoice_count" in item, "Missing invoice_count in sales_data"
        
        print(f"Sales by Customer: Total Sales={data['total_sales']}, Customers={len(data['sales_data'])}")
    
    def test_sales_by_customer_pdf_export(self):
        """Test GET /api/reports/sales-by-customer?format=pdf exports PDF"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/sales-by-customer",
            params={"format": "pdf"}
        )
        assert response.status_code == 200, f"PDF export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got {content_type}"
        assert response.content[:4] == b'%PDF', "Content does not appear to be a valid PDF"
        
        print(f"Sales by Customer PDF export successful, size: {len(response.content)} bytes")
    
    def test_sales_by_customer_excel_export(self):
        """Test GET /api/reports/sales-by-customer?format=excel exports Excel"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/sales-by-customer",
            params={"format": "excel"}
        )
        assert response.status_code == 200, f"Excel export failed: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "spreadsheetml" in content_type or "excel" in content_type.lower(), f"Expected Excel content type, got {content_type}"
        assert response.content[:2] == b'PK', "Content does not appear to be a valid Excel file"
        
        print(f"Sales by Customer Excel export successful, size: {len(response.content)} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
