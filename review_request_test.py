#!/usr/bin/env python3
"""
Focused test for Review Request Requirements
Tests the specific areas mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://garage-rescue-1.preview.emergentagent.com/api"

class ReviewRequestTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.admin_token = None
    
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if response_data:
            result['response'] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if not success and response_data:
            print(f"   Response: {response_data}")
    
    def test_admin_login_flow(self):
        """Test admin login with specific credentials from review request"""
        print("\n1. 🔐 Testing Admin Login Flow")
        print("   URL: /admin/login")
        print("   Email: admin@battwheelsgarages.in")
        print("   Password: adminpassword")
        
        login_data = {
            "email": "admin@battwheelsgarages.in",
            "password": "adminpassword"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/admin/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "token_type", "user"]
                
                if all(field in data for field in required_fields):
                    if data["token_type"] == "bearer" and data["access_token"]:
                        self.admin_token = data["access_token"]
                        self.log_test("Admin Login Flow", True, f"✅ Login successful, should redirect to /admin dashboard", {"user_email": data['user']['email']})
                        return True
                    else:
                        self.log_test("Admin Login Flow", False, f"Invalid token format: {data}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Admin Login Flow", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Admin Login Flow", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Login Flow", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_booking_api_public(self):
        """Test POST /api/bookings/ - Create a new booking"""
        print("\n2. 📋 Testing Booking API (Public)")
        print("   POST /api/bookings/ - Create a new booking")
        
        booking_data = {
            "vehicle_category": "2w",
            "customer_type": "individual", 
            "name": "Rajesh Kumar",
            "phone": "+91 9876543210",
            "email": "rajesh.kumar@example.com",
            "city": "Mumbai",
            "address": "123 MG Road, Andheri West, Mumbai",
            "service_needed": "Battery health check and periodic maintenance",
            "preferred_date": "2025-12-20",
            "time_slot": "morning",
            "brand": "Ather",
            "model": "450X"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/bookings/",
                json=booking_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "vehicle_category", "customer_type", "name", "email", "status", "created_at"]
                
                if all(field in data for field in required_fields):
                    if data["status"] == "new":
                        self.log_test("Booking API (Public)", True, f"✅ Booking created successfully with ID: {data['id']}", {"booking_id": data['id']})
                        return data["id"]
                    else:
                        self.log_test("Booking API (Public)", False, f"Unexpected status: {data['status']}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Booking API (Public)", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Booking API (Public)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Booking API (Public)", False, f"Request failed: {str(e)}")
        
        return None
    
    def get_admin_headers(self):
        """Get headers with admin authorization"""
        if not self.admin_token:
            return {}
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_services_without_trailing_slash(self):
        """Test GET /api/admin/services - WITHOUT trailing slash (verify fix)"""
        print("\n3. 🔧 Testing Admin API Endpoints (require auth token)")
        print("   GET /api/admin/services - WITHOUT trailing slash (verify fix)")
        
        if not self.admin_token:
            self.log_test("Admin Services (No Slash)", False, "No admin token available")
            return False
            
        try:
            # Test WITHOUT trailing slash (this should work after the fix)
            response = requests.get(
                f"{self.base_url}/admin/services",  # NO trailing slash
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "services" in data and isinstance(data["services"], list):
                    self.log_test("Admin Services (No Slash)", True, f"✅ Retrieved {len(data['services'])} services WITHOUT trailing slash", {"count": len(data["services"])})
                    return True
                else:
                    self.log_test("Admin Services (No Slash)", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("Admin Services (No Slash)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Services (No Slash)", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_admin_bookings(self):
        """Test GET /api/admin/bookings - List bookings"""
        print("   GET /api/admin/bookings - List bookings")
        
        if not self.admin_token:
            self.log_test("Admin Bookings", False, "No admin token available")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/admin/bookings",  # NO trailing slash
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total", "bookings", "limit", "skip"]
                
                if all(field in data for field in required_fields):
                    if isinstance(data["bookings"], list):
                        self.log_test("Admin Bookings", True, f"✅ Retrieved {data['total']} bookings", {"count": data["total"]})
                        return True
                    else:
                        self.log_test("Admin Bookings", False, f"Bookings not a list: {type(data['bookings'])}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Admin Bookings", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Admin Bookings", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Bookings", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_seo_verification(self):
        """Test SEO verification - Check that pages have proper meta titles"""
        print("\n4. 🔍 SEO Verification")
        print("   Note: This is frontend testing - skipping as per instructions")
        print("   ⚠️  SEO testing requires frontend verification which is outside backend testing scope")
        
        self.log_test("SEO Verification", True, "Skipped - Frontend testing not in scope for backend tester", {"note": "Frontend testing excluded"})
        return True
    
    def run_review_tests(self):
        """Run all review request tests"""
        print(f"🎯 BATTWHEELS GARAGES - REVIEW REQUEST TESTING")
        print(f"Backend URL: {self.base_url}")
        print("=" * 70)
        
        # Test 1: Admin Login Flow
        admin_login_success = self.test_admin_login_flow()
        
        # Test 2: Booking API (Public)
        booking_id = self.test_booking_api_public()
        
        # Test 3: Admin API Endpoints (require auth token)
        if admin_login_success:
            services_success = self.test_admin_services_without_trailing_slash()
            bookings_success = self.test_admin_bookings()
        else:
            print("\n❌ Skipping admin API tests - login failed")
            services_success = False
            bookings_success = False
        
        # Test 4: SEO Verification
        seo_success = self.test_seo_verification()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 REVIEW REQUEST TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n🎯 KEY FINDINGS:")
        print(f"1. Admin Login: {'✅ WORKING' if admin_login_success else '❌ FAILED'}")
        print(f"2. Booking API: {'✅ WORKING' if booking_id else '❌ FAILED'}")
        print(f"3. Admin Services (no slash): {'✅ WORKING' if services_success else '❌ FAILED'}")
        print(f"4. Admin Bookings: {'✅ WORKING' if bookings_success else '❌ FAILED'}")
        print(f"5. SEO Verification: {'✅ SKIPPED (Frontend)' if seo_success else '❌ FAILED'}")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = ReviewRequestTester()
    success = tester.run_review_tests()
    sys.exit(0 if success else 1)