#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class BattwheelsAPITester:
    def __init__(self, base_url="https://p0-p1-patch.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_seed_data(self):
        """Seed initial data"""
        return self.run_test("Seed Data", "POST", "seed", 200)

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@battwheels.in", "password": "test_pwd_placeholder"}
        )
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['user_id']
            print(f"   Token acquired: {self.token[:20]}...")
            return True
        return False

    def test_auth_me(self):
        """Test get current user"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test("Dashboard Stats", "GET", "dashboard/stats", 200)
        if success:
            required_fields = ['vehicles_in_workshop', 'open_repair_orders', 'avg_repair_time', 'available_technicians']
            for field in required_fields:
                if field not in response:
                    print(f"   ⚠️  Missing field: {field}")
                    return False
            print(f"   📊 Stats: Workshop={response.get('vehicles_in_workshop')}, Orders={response.get('open_repair_orders')}")
        return success

    def test_get_users(self):
        """Test get users (admin only)"""
        return self.run_test("Get Users", "GET", "users", 200)

    def test_get_technicians(self):
        """Test get technicians"""
        return self.run_test("Get Technicians", "GET", "technicians", 200)

    def test_get_vehicles(self):
        """Test get vehicles"""
        return self.run_test("Get Vehicles", "GET", "vehicles", 200)

    def test_create_vehicle(self):
        """Test create vehicle"""
        vehicle_data = {
            "owner_name": "Test Owner",
            "make": "Tata",
            "model": "Nexon EV",
            "year": 2024,
            "registration_number": "MH01AB1234",
            "battery_capacity": 40.5
        }
        success, response = self.run_test("Create Vehicle", "POST", "vehicles", 200, data=vehicle_data)
        if success and 'vehicle_id' in response:
            self.vehicle_id = response['vehicle_id']
            print(f"   🚗 Vehicle created: {self.vehicle_id}")
        return success

    def test_get_tickets(self):
        """Test get tickets"""
        return self.run_test("Get Tickets", "GET", "tickets", 200)

    def test_create_ticket(self):
        """Test create ticket"""
        if not hasattr(self, 'vehicle_id'):
            print("   ⚠️  Skipping - No vehicle ID available")
            return False
            
        ticket_data = {
            "vehicle_id": self.vehicle_id,
            "title": "Battery charging issue",
            "description": "Vehicle not charging beyond 80%",
            "category": "battery",
            "priority": "high"
        }
        success, response = self.run_test("Create Ticket", "POST", "tickets", 200, data=ticket_data)
        if success and 'ticket_id' in response:
            self.ticket_id = response['ticket_id']
            print(f"   🎫 Ticket created: {self.ticket_id}")
        return success

    def test_get_inventory(self):
        """Test get inventory"""
        return self.run_test("Get Inventory", "GET", "inventory", 200)

    def test_create_inventory_item(self):
        """Test create inventory item"""
        item_data = {
            "name": "Test Battery Pack",
            "category": "battery",
            "quantity": 10,
            "unit_price": 50000,
            "min_stock_level": 2,
            "supplier": "Test Supplier",
            "location": "Warehouse A"
        }
        success, response = self.run_test("Create Inventory Item", "POST", "inventory", 200, data=item_data)
        if success and 'item_id' in response:
            self.item_id = response['item_id']
            print(f"   📦 Item created: {self.item_id}")
        return success

    def test_ai_diagnose(self):
        """Test AI diagnosis"""
        query_data = {
            "issue_description": "My EV won't charge past 80%. The charging light blinks red.",
            "vehicle_model": "Tata Nexon EV",
            "category": "battery"
        }
        success, response = self.run_test("AI Diagnose", "POST", "ai/diagnose", 200, data=query_data)
        if success:
            if 'solution' in response:
                print(f"   🤖 AI Response: {response['solution'][:100]}...")
            else:
                print("   ⚠️  No solution in response")
                return False
        return success

    def test_get_alerts(self):
        """Test get alerts"""
        return self.run_test("Get Alerts", "GET", "alerts", 200)

    def test_get_roles(self):
        """Test get roles"""
        return self.run_test("Get Roles", "GET", "roles", 200)

    def test_logout(self):
        """Test logout"""
        return self.run_test("Logout", "POST", "auth/logout", 200)

def main():
    print("🚀 Starting Battwheels OS API Testing...")
    print("=" * 60)
    
    tester = BattwheelsAPITester()
    
    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Seed Data", tester.test_seed_data),
        ("Admin Login", tester.test_admin_login),
        ("Auth Me", tester.test_auth_me),
        ("Dashboard Stats", tester.test_dashboard_stats),
        ("Get Users", tester.test_get_users),
        ("Get Technicians", tester.test_get_technicians),
        ("Get Vehicles", tester.test_get_vehicles),
        ("Create Vehicle", tester.test_create_vehicle),
        ("Get Tickets", tester.test_get_tickets),
        ("Create Ticket", tester.test_create_ticket),
        ("Get Inventory", tester.test_get_inventory),
        ("Create Inventory Item", tester.test_create_inventory_item),
        ("AI Diagnose", tester.test_ai_diagnose),
        ("Get Alerts", tester.test_get_alerts),
        ("Get Roles", tester.test_get_roles),
        ("Logout", tester.test_logout),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            tester.failed_tests.append({"test": test_name, "error": str(e)})
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests ({len(tester.failed_tests)}):")
        for failure in tester.failed_tests:
            error_msg = failure.get('error', f"Expected {failure.get('expected')}, got {failure.get('actual')}")
            print(f"   • {failure['test']}: {error_msg}")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())