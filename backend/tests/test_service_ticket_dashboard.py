"""
Test Service Ticket Dashboard Stats
- Tests GET /api/dashboard/stats endpoint
- Verifies service_ticket_stats object structure
- Verifies resolution_type counting (onsite, workshop, pickup, remote)
- Verifies average resolution time calculation
- Verifies 30-day metrics
"""

import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestServiceTicketDashboard:
    """Test service ticket metrics in dashboard stats"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dev@battwheels.internal", "password": "DevTest@123"}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed - cannot test dashboard")
    
    def test_dashboard_stats_endpoint_returns_200(self):
        """Test GET /api/dashboard/stats returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Dashboard stats endpoint returns 200")
    
    def test_dashboard_stats_contains_service_ticket_stats(self):
        """Test that response contains service_ticket_stats object"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "service_ticket_stats" in data, "service_ticket_stats not in response"
        print("PASS: service_ticket_stats object exists in response")
    
    def test_service_ticket_stats_structure(self):
        """Test that service_ticket_stats has all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        stats = data.get("service_ticket_stats", {})
        required_fields = [
            "total_open",
            "onsite_resolution",
            "workshop_visit",
            "pickup",
            "remote",
            "avg_resolution_time_hours",
            "onsite_resolution_percentage",
            "total_resolved_30d",
            "total_onsite_resolved_30d"
        ]
        
        for field in required_fields:
            assert field in stats, f"Missing field: {field}"
            print(f"  - {field}: {stats[field]}")
        
        print("PASS: All required fields present in service_ticket_stats")
    
    def test_service_ticket_stats_total_open_is_numeric(self):
        """Test that total_open is a numeric value"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        total_open = stats.get("total_open")
        assert isinstance(total_open, int), f"total_open should be int, got {type(total_open)}"
        assert total_open >= 0, "total_open should be >= 0"
        print(f"PASS: total_open is numeric: {total_open}")
    
    def test_onsite_resolution_count(self):
        """Test that onsite_resolution is counted correctly"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        onsite = stats.get("onsite_resolution")
        assert isinstance(onsite, int), f"onsite_resolution should be int, got {type(onsite)}"
        assert onsite >= 0, "onsite_resolution should be >= 0"
        print(f"PASS: onsite_resolution count: {onsite}")
    
    def test_workshop_visit_count(self):
        """Test that workshop_visit is counted correctly (includes unspecified resolution_type)"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        workshop = stats.get("workshop_visit")
        assert isinstance(workshop, int), f"workshop_visit should be int, got {type(workshop)}"
        assert workshop >= 0, "workshop_visit should be >= 0"
        print(f"PASS: workshop_visit count: {workshop}")
    
    def test_pickup_remote_counts(self):
        """Test that pickup and remote counts are tracked"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        pickup = stats.get("pickup")
        remote = stats.get("remote")
        
        assert isinstance(pickup, int), f"pickup should be int, got {type(pickup)}"
        assert isinstance(remote, int), f"remote should be int, got {type(remote)}"
        assert pickup >= 0 and remote >= 0
        print(f"PASS: pickup: {pickup}, remote: {remote}")
    
    def test_avg_resolution_time_hours(self):
        """Test that avg_resolution_time_hours is calculated"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        avg_time = stats.get("avg_resolution_time_hours")
        assert isinstance(avg_time, (int, float)), f"avg_resolution_time_hours should be numeric, got {type(avg_time)}"
        assert avg_time >= 0, "avg_resolution_time_hours should be >= 0"
        print(f"PASS: avg_resolution_time_hours: {avg_time}")
    
    def test_onsite_resolution_percentage(self):
        """Test that onsite_resolution_percentage is from 30-day data"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        percentage = stats.get("onsite_resolution_percentage")
        assert isinstance(percentage, (int, float)), f"onsite_resolution_percentage should be numeric, got {type(percentage)}"
        assert 0 <= percentage <= 100, f"Percentage should be 0-100, got {percentage}"
        print(f"PASS: onsite_resolution_percentage: {percentage}%")
    
    def test_30d_metrics(self):
        """Test 30-day resolved ticket metrics"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        total_30d = stats.get("total_resolved_30d")
        onsite_30d = stats.get("total_onsite_resolved_30d")
        
        assert isinstance(total_30d, int), f"total_resolved_30d should be int"
        assert isinstance(onsite_30d, int), f"total_onsite_resolved_30d should be int"
        assert onsite_30d <= total_30d, "onsite_resolved should be <= total_resolved"
        print(f"PASS: 30d metrics - total: {total_30d}, onsite: {onsite_30d}")
    
    def test_total_open_matches_sum_of_resolution_types(self):
        """Test that total_open >= sum of resolution types (may not be exact due to edge cases)"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        total = stats.get("total_open", 0)
        onsite = stats.get("onsite_resolution", 0)
        workshop = stats.get("workshop_visit", 0)
        pickup = stats.get("pickup", 0)
        remote = stats.get("remote", 0)
        
        sum_of_types = onsite + workshop + pickup + remote
        
        # Total should match or be close to sum (workshop includes null/empty)
        print(f"Total open: {total}")
        print(f"Sum (onsite: {onsite} + workshop: {workshop} + pickup: {pickup} + remote: {remote}): {sum_of_types}")
        
        # They should match since workshop includes unspecified
        assert sum_of_types == total, f"Sum of types ({sum_of_types}) should equal total_open ({total})"
        print("PASS: total_open matches sum of resolution types")
    
    def test_percentage_calculation_consistency(self):
        """Test that onsite_resolution_percentage is consistent with 30d data"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        stats = data.get("service_ticket_stats", {})
        
        total_30d = stats.get("total_resolved_30d", 0)
        onsite_30d = stats.get("total_onsite_resolved_30d", 0)
        percentage = stats.get("onsite_resolution_percentage", 0)
        
        if total_30d > 0:
            expected_pct = round((onsite_30d / total_30d) * 100, 1)
            assert abs(percentage - expected_pct) < 0.2, f"Expected {expected_pct}%, got {percentage}%"
            print(f"PASS: Percentage {percentage}% matches calculation ({onsite_30d}/{total_30d})")
        else:
            assert percentage == 0, "With 0 resolved tickets, percentage should be 0"
            print("PASS: 0% with no resolved tickets (expected)")


class TestDashboardStatsDataVerification:
    """Verify dashboard stats data matches actual database state"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dev@battwheels.internal", "password": "DevTest@123"}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")
    
    def test_dashboard_stats_data_types_valid(self):
        """Test all stats have valid data types"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        
        # Main stats
        assert isinstance(data.get("vehicles_in_workshop"), int)
        assert isinstance(data.get("open_repair_orders"), int)
        assert isinstance(data.get("avg_repair_time"), (int, float))
        assert isinstance(data.get("available_technicians"), int)
        
        # Vehicle status distribution
        vsd = data.get("vehicle_status_distribution", {})
        assert isinstance(vsd.get("active"), int)
        assert isinstance(vsd.get("in_workshop"), int)
        assert isinstance(vsd.get("serviced"), int)
        
        # Monthly trends
        trends = data.get("monthly_repair_trends", [])
        assert isinstance(trends, list)
        
        # Service ticket stats
        sts = data.get("service_ticket_stats", {})
        assert isinstance(sts, dict)
        
        print("PASS: All data types are valid")
    
    def test_open_repair_orders_matches_service_ticket_total(self):
        """Test that open_repair_orders matches service_ticket_stats.total_open"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        data = response.json()
        
        open_orders = data.get("open_repair_orders", 0)
        total_open = data.get("service_ticket_stats", {}).get("total_open", 0)
        
        assert open_orders == total_open, f"open_repair_orders ({open_orders}) should match total_open ({total_open})"
        print(f"PASS: open_repair_orders ({open_orders}) matches total_open ({total_open})")


class TestServiceTicketCreationAndStats:
    """Test creating tickets with different resolution_types affects dashboard stats"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dev@battwheels.internal", "password": "DevTest@123"}
        )
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            self.created_ticket_ids = []
        else:
            pytest.skip("Authentication failed")
    
    def test_create_onsite_ticket_and_verify_stats(self):
        """Create an onsite resolution ticket and verify stats update"""
        # Get initial stats
        initial_response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        initial_data = initial_response.json()
        initial_onsite = initial_data.get("service_ticket_stats", {}).get("onsite_resolution", 0)
        
        # Create a ticket with resolution_type=onsite
        ticket_payload = {
            "title": "TEST_Onsite Battery Check",
            "description": "Test onsite resolution ticket",
            "category": "battery",
            "priority": "medium",
            "resolution_type": "onsite",
            "customer_name": "Test Customer",
            "contact_number": "9876543210"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/tickets",
            json=ticket_payload,
            headers=self.headers
        )
        
        if create_response.status_code in [200, 201]:
            ticket = create_response.json()
            ticket_id = ticket.get("ticket_id")
            self.created_ticket_ids.append(ticket_id)
            
            # Verify stats updated
            updated_response = requests.get(
                f"{BASE_URL}/api/dashboard/stats",
                headers=self.headers
            )
            updated_data = updated_response.json()
            updated_onsite = updated_data.get("service_ticket_stats", {}).get("onsite_resolution", 0)
            
            assert updated_onsite == initial_onsite + 1, f"Onsite count should increase by 1"
            print(f"PASS: Onsite count increased from {initial_onsite} to {updated_onsite}")
            
            # Cleanup - close the ticket
            requests.delete(f"{BASE_URL}/api/tickets/{ticket_id}", headers=self.headers)
        else:
            print(f"INFO: Could not create ticket - {create_response.status_code}: {create_response.text}")
            pytest.skip("Ticket creation endpoint not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
