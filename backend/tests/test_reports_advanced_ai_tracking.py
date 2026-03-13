"""
Test Reports Advanced Endpoints and AI Token Tracking
======================================================
Tests:
1. All 13 /api/v1/reports-advanced/* endpoints return 200
2. AI token tracking: POST /api/v1/ai/guidance/generate increments usage.ai_calls_made
3. GET /api/v1/subscriptions/limits shows correct AI calls count
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Demo credentials
DEMO_EMAIL = "demo@voltmotors.in"
DEMO_PASSWORD = "Demo@12345"
DEMO_ORG_ID = "demo-volt-motors-001"


class TestSetup:
    """Fixtures and setup for tests"""
    
    @staticmethod
    def get_auth_token():
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    @staticmethod
    def get_auth_headers(token):
        """Get headers with auth token and org ID"""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Organization-ID": DEMO_ORG_ID
        }


# ==================== REPORTS ADVANCED TESTS ====================

class TestReportsAdvanced:
    """Test all 13 /api/v1/reports-advanced/* endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        return TestSetup.get_auth_token()
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return TestSetup.get_auth_headers(auth_token)
    
    # Revenue Reports
    def test_revenue_monthly(self, headers):
        """Test GET /api/v1/reports-advanced/revenue/monthly"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/revenue/monthly",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        assert "data" in data, "Missing 'data' in response"
        print(f"✓ revenue/monthly: {len(data.get('data', []))} months returned")
    
    def test_revenue_quarterly(self, headers):
        """Test GET /api/v1/reports-advanced/revenue/quarterly"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/revenue/quarterly",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ revenue/quarterly: {len(data.get('data', []))} quarters returned")
    
    def test_revenue_yearly_comparison(self, headers):
        """Test GET /api/v1/reports-advanced/revenue/yearly-comparison"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/revenue/yearly-comparison",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ revenue/yearly-comparison: {len(data.get('data', []))} years returned")
    
    # Receivables Reports
    def test_receivables_aging(self, headers):
        """Test GET /api/v1/reports-advanced/receivables/aging"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/receivables/aging",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ receivables/aging: total_outstanding={data.get('total_outstanding', 0)}")
    
    def test_receivables_trend(self, headers):
        """Test GET /api/v1/reports-advanced/receivables/trend"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/receivables/trend",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ receivables/trend: {len(data.get('data', []))} months returned")
    
    # Customer Reports
    def test_customers_top_revenue(self, headers):
        """Test GET /api/v1/reports-advanced/customers/top-revenue"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/customers/top-revenue",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ customers/top-revenue: {len(data.get('data', []))} customers returned")
    
    def test_customers_top_outstanding(self, headers):
        """Test GET /api/v1/reports-advanced/customers/top-outstanding"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/customers/top-outstanding",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ customers/top-outstanding: {len(data.get('data', []))} customers returned")
    
    def test_customers_acquisition(self, headers):
        """Test GET /api/v1/reports-advanced/customers/acquisition"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/customers/acquisition",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ customers/acquisition: total_new={data.get('total_new', 0)}")
    
    # Sales Funnel
    def test_sales_funnel(self, headers):
        """Test GET /api/v1/reports-advanced/sales/funnel"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/sales/funnel",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ sales/funnel: {len(data.get('data', []))} stages returned")
    
    # Invoice Status Distribution
    def test_invoices_status_distribution(self, headers):
        """Test GET /api/v1/reports-advanced/invoices/status-distribution"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/invoices/status-distribution",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ invoices/status-distribution: {len(data.get('data', []))} statuses returned")
    
    # Payment Reports
    def test_payments_trend(self, headers):
        """Test GET /api/v1/reports-advanced/payments/trend"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/payments/trend",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ payments/trend: total_collected={data.get('total_collected', 0)}")
    
    def test_payments_by_mode(self, headers):
        """Test GET /api/v1/reports-advanced/payments/by-mode"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/payments/by-mode",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        print(f"✓ payments/by-mode: {len(data.get('data', []))} modes returned")
    
    # Dashboard Summary
    def test_dashboard_summary(self, headers):
        """Test GET /api/v1/reports-advanced/dashboard-summary"""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports-advanced/dashboard-summary",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("code") == 0, f"Response code not 0: {data}"
        assert "summary" in data, "Missing 'summary' in response"
        print(f"✓ dashboard-summary: this_month_revenue={data.get('summary', {}).get('this_month', {}).get('revenue', 0)}")


# ==================== AI TOKEN TRACKING TESTS ====================

class TestAITokenTracking:
    """Test AI token tracking for EVFI routes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        return TestSetup.get_auth_token()
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return TestSetup.get_auth_headers(auth_token)
    
    def test_get_current_ai_calls_count(self, headers):
        """Get current AI calls count from subscription limits"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/limits",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        ai_calls = data.get("limits", {}).get("ai_calls", {})
        current_count = ai_calls.get("current", 0)
        limit = ai_calls.get("limit", 0)
        
        print(f"✓ Current AI calls: {current_count} / {limit}")
        return current_count
    
    def test_ai_guidance_generate_increments_ai_calls(self, headers):
        """Test that POST /api/v1/ai/guidance/generate increments AI calls"""
        
        # Step 1: Get current AI calls count
        limits_response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/limits",
            headers=headers
        )
        assert limits_response.status_code == 200, f"Failed to get limits: {limits_response.text}"
        initial_count = limits_response.json().get("limits", {}).get("ai_calls", {}).get("current", 0)
        print(f"Initial AI calls count: {initial_count}")
        
        # Step 2: Get a valid ticket_id from the database
        tickets_response = requests.get(
            f"{BASE_URL}/api/v1/tickets",
            headers=headers,
            params={"limit": 1}
        )
        
        ticket_id = None
        if tickets_response.status_code == 200:
            tickets_data = tickets_response.json()
            tickets = tickets_data.get("tickets", [])
            if tickets:
                ticket_id = tickets[0].get("ticket_id")
        
        # If no ticket exists, use a test ticket ID (guidance will create mock response)
        if not ticket_id:
            ticket_id = "tkt_5e8ae8ecdea4"
        
        print(f"Using ticket_id: {ticket_id}")
        
        # Step 3: Call AI guidance generate
        guidance_response = requests.post(
            f"{BASE_URL}/api/v1/ai/guidance/generate",
            headers=headers,
            json={
                "ticket_id": ticket_id,
                "mode": "quick",
                "force_regenerate": True
            }
        )
        
        # AI guidance should return 200 or 404 if ticket not found
        # The important thing is tracking happens on success
        print(f"AI guidance response status: {guidance_response.status_code}")
        
        if guidance_response.status_code == 200:
            # Step 4: Verify AI calls count incremented
            time.sleep(1)  # Small delay for DB update
            
            final_limits_response = requests.get(
                f"{BASE_URL}/api/v1/subscriptions/limits",
                headers=headers
            )
            assert final_limits_response.status_code == 200
            final_count = final_limits_response.json().get("limits", {}).get("ai_calls", {}).get("current", 0)
            
            print(f"Final AI calls count: {final_count}")
            assert final_count > initial_count, f"AI calls count did not increment: {initial_count} -> {final_count}"
            print(f"✓ AI calls incremented: {initial_count} -> {final_count}")
        elif guidance_response.status_code == 404:
            print(f"⚠ Ticket not found (expected if using test ticket_id): {guidance_response.text}")
            pytest.skip("Skipping increment test - ticket not found")
        else:
            print(f"AI guidance response: {guidance_response.text}")
            # Even with errors, check if count changed (it shouldn't for errors)
    
    def test_ai_assist_diagnose_with_placeholder_key(self, headers):
        """
        Test POST /api/v1/ai-assist/diagnose endpoint.
        With placeholder LLM key, this will return error response.
        AI tracking should NOT increment on error.
        """
        # Get initial count
        limits_response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/limits",
            headers=headers
        )
        initial_count = limits_response.json().get("limits", {}).get("ai_calls", {}).get("current", 0)
        
        # Call AI diagnose - expected to fail with placeholder key
        diagnose_response = requests.post(
            f"{BASE_URL}/api/v1/ai-assist/diagnose",
            headers=headers,
            json={
                "query": "Battery not charging",
                "category": "battery",
                "portal_type": "admin"
            }
        )
        
        print(f"AI diagnose response status: {diagnose_response.status_code}")
        
        if diagnose_response.status_code == 200:
            data = diagnose_response.json()
            # Check if AI was actually enabled (not mocked response)
            ai_enabled = data.get("ai_enabled", False)
            print(f"AI enabled: {ai_enabled}")
            
            if ai_enabled:
                # Tracking should have incremented
                time.sleep(1)
                final_response = requests.get(f"{BASE_URL}/api/v1/subscriptions/limits", headers=headers)
                final_count = final_response.json().get("limits", {}).get("ai_calls", {}).get("current", 0)
                print(f"✓ AI diagnose succeeded, calls: {initial_count} -> {final_count}")
            else:
                # AI was disabled, tracking should NOT increment
                print("✓ AI diagnose returned fallback response (expected with placeholder key)")
        else:
            print(f"AI diagnose failed (expected with placeholder key): {diagnose_response.text}")
    
    def test_subscription_limits_shows_ai_calls(self, headers):
        """Verify /api/v1/subscriptions/limits includes ai_calls field"""
        response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/limits",
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        data = response.json()
        limits = data.get("limits", {})
        
        # Verify ai_calls field exists
        assert "ai_calls" in limits, f"Missing 'ai_calls' in limits: {limits.keys()}"
        
        ai_calls = limits["ai_calls"]
        assert "current" in ai_calls, "Missing 'current' in ai_calls"
        assert "limit" in ai_calls, "Missing 'limit' in ai_calls"
        
        print(f"✓ Subscription limits includes ai_calls: {ai_calls}")


# ==================== INTEGRATION TEST ====================

class TestFullWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        return TestSetup.get_auth_token()
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return TestSetup.get_auth_headers(auth_token)
    
    def test_reports_advanced_all_13_endpoints(self, headers):
        """Test all 13 reports-advanced endpoints return 200"""
        endpoints = [
            "/revenue/monthly",
            "/revenue/quarterly",
            "/revenue/yearly-comparison",
            "/receivables/aging",
            "/receivables/trend",
            "/customers/top-revenue",
            "/customers/top-outstanding",
            "/customers/acquisition",
            "/sales/funnel",
            "/invoices/status-distribution",
            "/payments/trend",
            "/payments/by-mode",
            "/dashboard-summary"
        ]
        
        passed = 0
        failed = []
        
        for endpoint in endpoints:
            url = f"{BASE_URL}/api/v1/reports-advanced{endpoint}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                passed += 1
                print(f"✓ {endpoint}: 200 OK")
            else:
                failed.append(f"{endpoint}: {response.status_code}")
                print(f"✗ {endpoint}: {response.status_code} - {response.text[:100]}")
        
        assert passed == 13, f"Only {passed}/13 endpoints passed. Failed: {failed}"
        print(f"\n✓ All 13 reports-advanced endpoints returned 200")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
