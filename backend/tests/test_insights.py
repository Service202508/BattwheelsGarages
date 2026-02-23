"""
Data Insights API Endpoints Tests
Tests for: /api/insights/revenue, /api/insights/operations,
           /api/insights/technicians, /api/insights/efi,
           /api/insights/customers, /api/insights/inventory
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
SESSION_TOKEN = "test_session_insights_1771885529665"

HEADERS = {
    "Authorization": f"Bearer {SESSION_TOKEN}",
    "Content-Type": "application/json",
}

PARAMS = {
    "date_from": "2025-01-01",
    "date_to": "2025-12-31",
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def get(path, params=None):
    return requests.get(
        f"{BASE_URL}/api/insights/{path}",
        headers=HEADERS,
        params=params or PARAMS,
        timeout=15,
    )


# ── Revenue Insights ─────────────────────────────────────────────────────────
class TestRevenueInsights:
    """Revenue Intelligence endpoint tests"""

    def test_revenue_returns_200(self):
        resp = get("revenue")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"

    def test_revenue_has_required_keys(self):
        resp = get("revenue")
        data = resp.json()
        assert "kpis" in data, f"Missing 'kpis' key. Got: {list(data.keys())}"
        assert "trend" in data, f"Missing 'trend' key. Got: {list(data.keys())}"
        assert "by_type" in data, f"Missing 'by_type' key. Got: {list(data.keys())}"

    def test_revenue_kpis_structure(self):
        resp = get("revenue")
        kpis = resp.json()["kpis"]
        required = ["revenue", "avg_invoice", "collection_rate", "ar", "paid_count", "total_count"]
        for key in required:
            assert key in kpis, f"Missing kpi key: {key}"

    def test_revenue_trend_is_list(self):
        resp = get("revenue")
        trend = resp.json()["trend"]
        assert isinstance(trend, list), f"trend should be a list, got: {type(trend)}"

    def test_revenue_by_type_is_list(self):
        resp = get("revenue")
        by_type = resp.json()["by_type"]
        assert isinstance(by_type, list), f"by_type should be a list, got: {type(by_type)}"

    def test_revenue_with_current_month_params(self):
        """Test with This Month params (default scenario)"""
        resp = requests.get(
            f"{BASE_URL}/api/insights/revenue",
            headers=HEADERS,
            params={"date_from": "2026-02-01", "date_to": "2026-02-28"},
            timeout=15,
        )
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}"
        data = resp.json()
        assert "kpis" in data and "trend" in data and "by_type" in data


# ── Operations Insights ───────────────────────────────────────────────────────
class TestOperationsInsights:
    """Workshop Operations endpoint tests"""

    def test_operations_returns_200(self):
        resp = get("operations")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"

    def test_operations_has_required_keys(self):
        resp = get("operations")
        data = resp.json()
        assert "kpis" in data, f"Missing 'kpis'. Got: {list(data.keys())}"
        assert "volume" in data, f"Missing 'volume'. Got: {list(data.keys())}"
        assert "vehicle_dist" in data, f"Missing 'vehicle_dist'. Got: {list(data.keys())}"

    def test_operations_kpis_structure(self):
        resp = get("operations")
        kpis = resp.json()["kpis"]
        required = ["tickets_resolved", "avg_resolution_hours", "sla_compliance_rate",
                    "first_fix_rate", "total_tickets"]
        for key in required:
            assert key in kpis, f"Missing kpi key: {key}"

    def test_operations_volume_is_list(self):
        resp = get("operations")
        volume = resp.json()["volume"]
        assert isinstance(volume, list)

    def test_operations_vehicle_dist_is_list(self):
        resp = get("operations")
        vd = resp.json()["vehicle_dist"]
        assert isinstance(vd, list)


# ── Technicians Insights ──────────────────────────────────────────────────────
class TestTechnicianInsights:
    """Technician Performance endpoint tests"""

    def test_technicians_returns_200(self):
        resp = get("technicians")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"

    def test_technicians_has_required_keys(self):
        resp = get("technicians")
        data = resp.json()
        assert "leaderboard" in data, f"Missing 'leaderboard'. Got: {list(data.keys())}"
        assert "heatmap" in data, f"Missing 'heatmap'. Got: {list(data.keys())}"
        assert "vehicle_types" in data, f"Missing 'vehicle_types'. Got: {list(data.keys())}"

    def test_technicians_leaderboard_is_list(self):
        resp = get("technicians")
        lb = resp.json()["leaderboard"]
        assert isinstance(lb, list)

    def test_technicians_heatmap_is_list(self):
        resp = get("technicians")
        hm = resp.json()["heatmap"]
        assert isinstance(hm, list)

    def test_technicians_vehicle_types_is_list(self):
        resp = get("technicians")
        vt = resp.json()["vehicle_types"]
        assert isinstance(vt, list)

    def test_technicians_leaderboard_item_structure(self):
        """If leaderboard has entries, verify structure"""
        resp = get("technicians")
        lb = resp.json()["leaderboard"]
        if lb:
            first = lb[0]
            required = ["id", "name", "tickets_closed"]
            for key in required:
                assert key in first, f"Missing leaderboard key: {key}"


# ── EFI Intelligence ──────────────────────────────────────────────────────────
class TestEfiInsights:
    """EFI Intelligence endpoint tests"""

    def test_efi_returns_200(self):
        resp = get("efi")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"

    def test_efi_has_required_keys(self):
        resp = get("efi")
        data = resp.json()
        assert "stats" in data, f"Missing 'stats'. Got: {list(data.keys())}"
        assert "failure_patterns" in data, f"Missing 'failure_patterns'. Got: {list(data.keys())}"

    def test_efi_stats_structure(self):
        resp = get("efi")
        stats = resp.json()["stats"]
        required = ["diagnoses_run", "most_diagnosed", "total_fault_types", "total_in_period"]
        for key in required:
            assert key in stats, f"Missing stats key: {key}"

    def test_efi_failure_patterns_is_list(self):
        resp = get("efi")
        fp = resp.json()["failure_patterns"]
        assert isinstance(fp, list)

    def test_efi_optional_keys_present(self):
        resp = get("efi")
        data = resp.json()
        # vehicle_fault_chart and fault_types are expected keys
        assert "vehicle_fault_chart" in data, f"Missing 'vehicle_fault_chart'. Got: {list(data.keys())}"
        assert "fault_types" in data, f"Missing 'fault_types'. Got: {list(data.keys())}"


# ── Customer Intelligence ─────────────────────────────────────────────────────
class TestCustomerInsights:
    """Customer Intelligence endpoint tests"""

    def test_customers_returns_200(self):
        resp = get("customers")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"

    def test_customers_has_required_keys(self):
        resp = get("customers")
        data = resp.json()
        assert "kpis" in data, f"Missing 'kpis'. Got: {list(data.keys())}"
        assert "rating_trend" in data, f"Missing 'rating_trend'. Got: {list(data.keys())}"
        assert "top_customers" in data, f"Missing 'top_customers'. Got: {list(data.keys())}"

    def test_customers_kpis_structure(self):
        resp = get("customers")
        kpis = resp.json()["kpis"]
        required = ["new_customers", "returning_customers", "avg_rating", "response_rate"]
        for key in required:
            assert key in kpis, f"Missing kpi key: {key}"

    def test_customers_rating_trend_is_list(self):
        resp = get("customers")
        rt = resp.json()["rating_trend"]
        assert isinstance(rt, list)

    def test_customers_top_customers_is_list(self):
        resp = get("customers")
        tc = resp.json()["top_customers"]
        assert isinstance(tc, list)


# ── Inventory Intelligence ────────────────────────────────────────────────────
class TestInventoryInsights:
    """Inventory Intelligence endpoint tests"""

    def test_inventory_returns_200(self):
        resp = get("inventory")
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"

    def test_inventory_has_required_keys(self):
        resp = get("inventory")
        data = resp.json()
        assert "kpis" in data, f"Missing 'kpis'. Got: {list(data.keys())}"
        assert "stock_health" in data, f"Missing 'stock_health'. Got: {list(data.keys())}"
        assert "fast_movers" in data, f"Missing 'fast_movers'. Got: {list(data.keys())}"
        assert "dead_stock" in data, f"Missing 'dead_stock'. Got: {list(data.keys())}"

    def test_inventory_kpis_structure(self):
        resp = get("inventory")
        kpis = resp.json()["kpis"]
        required = ["total_value", "below_reorder", "parts_used", "dead_stock_count"]
        for key in required:
            assert key in kpis, f"Missing kpi key: {key}"

    def test_inventory_stock_health_is_list(self):
        resp = get("inventory")
        sh = resp.json()["stock_health"]
        assert isinstance(sh, list)

    def test_inventory_fast_movers_is_list(self):
        resp = get("inventory")
        fm = resp.json()["fast_movers"]
        assert isinstance(fm, list)

    def test_inventory_dead_stock_is_list(self):
        resp = get("inventory")
        ds = resp.json()["dead_stock"]
        assert isinstance(ds, list)

    def test_inventory_stock_health_items(self):
        resp = get("inventory")
        sh = resp.json()["stock_health"]
        assert len(sh) >= 1, "stock_health should have at least one item"
        if sh:
            item = sh[0]
            required = ["label", "value", "count", "color"]
            for key in required:
                assert key in item, f"Missing stock_health item key: {key}"
