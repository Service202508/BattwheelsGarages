#!/usr/bin/env python3
"""
Focused Backend API Test for Review Request
Tests specific endpoints mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = "https://battwheels-ev-1.preview.emergentagent.com"

class ReviewRequestTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.api_url = f"{BACKEND_URL}/api"
        self.test_results = []
        self.admin_token = None
        self.created_service_id = None
    
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
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
    
    def test_health_endpoints(self):
        """Test both health check endpoints"""
        print("🏥 Testing Health Check Endpoints")
        print("=" * 50)
        
        # Test root health endpoint (Note: This returns HTML due to ingress routing)
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                # Check if it's HTML (frontend) or JSON (backend)
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type:
                    self.log_test("GET /health", True, "Root health endpoint returns frontend (expected due to ingress routing)")
                else:
                    try:
                        data = response.json()
                        if data.get("status") == "healthy":
                            self.log_test("GET /health", True, f"Root health check working: {data}")
                        else:
                            self.log_test("GET /health", False, f"Unexpected response: {data}", data)
                    except:
                        self.log_test("GET /health", False, f"Non-JSON response: {response.text[:100]}...")
            else:
                self.log_test("GET /health", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /health", False, f"Request failed: {str(e)}")
        
        # Test API health endpoint
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("GET /api/health", True, f"API health check working: {data}")
                else:
                    self.log_test("GET /api/health", False, f"Unexpected response: {data}", data)
            else:
                self.log_test("GET /api/health", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/health", False, f"Request failed: {str(e)}")
    
    def test_public_apis(self):
        """Test public API endpoints"""
        print("🌐 Testing Public API Endpoints")
        print("=" * 50)
        
        # Test services API
        try:
            response = requests.get(f"{self.api_url}/services", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "services" in data and isinstance(data["services"], list):
                    self.log_test("GET /api/services", True, f"Retrieved {len(data['services'])} services")
                else:
                    self.log_test("GET /api/services", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("GET /api/services", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/services", False, f"Request failed: {str(e)}")
        
        # Test testimonials API
        try:
            response = requests.get(f"{self.api_url}/testimonials", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "testimonials" in data and isinstance(data["testimonials"], list):
                    self.log_test("GET /api/testimonials", True, f"Retrieved {len(data['testimonials'])} testimonials")
                else:
                    self.log_test("GET /api/testimonials", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("GET /api/testimonials", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/testimonials", False, f"Request failed: {str(e)}")
        
        # Test blogs API
        try:
            response = requests.get(f"{self.api_url}/blogs", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "blogs" in data and isinstance(data["blogs"], list):
                    self.log_test("GET /api/blogs", True, f"Retrieved {len(data['blogs'])} blogs")
                else:
                    self.log_test("GET /api/blogs", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("GET /api/blogs", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/blogs", False, f"Request failed: {str(e)}")
    
    def test_admin_login(self):
        """Test admin authentication with specified credentials"""
        print("🔐 Testing Admin Authentication")
        print("=" * 50)
        
        login_data = {
            "email": "admin@battwheelsgarages.in",
            "password": "adminpassword"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/admin/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.admin_token = data["access_token"]
                    self.log_test("POST /api/admin/auth/login", True, f"Login successful, token received")
                    return True
                else:
                    self.log_test("POST /api/admin/auth/login", False, f"Missing token in response: {data}", data)
            else:
                self.log_test("POST /api/admin/auth/login", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("POST /api/admin/auth/login", False, f"Request failed: {str(e)}")
        
        return False
    
    def get_admin_headers(self):
        """Get headers with admin authorization"""
        if not self.admin_token:
            return {}
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_crud_services(self):
        """Test admin CRUD operations for services"""
        print("🔧 Testing Admin Services CRUD")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Admin Services CRUD", False, "No admin token available")
            return
        
        # Test GET services
        try:
            response = requests.get(
                f"{self.api_url}/admin/services/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "services" in data:
                    self.log_test("GET /api/admin/services", True, f"Retrieved {len(data['services'])} services")
                else:
                    self.log_test("GET /api/admin/services", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("GET /api/admin/services", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/admin/services", False, f"Request failed: {str(e)}")
        
        # Test POST service (create)
        service_data = {
            "title": "Test Service Review",
            "slug": f"test-service-review-{uuid.uuid4().hex[:8]}",
            "short_description": "Test service for review",
            "long_description": "Detailed test service description for review request",
            "vehicle_segments": ["2W", "3W"],
            "pricing_model": "fixed",
            "price": 199.0,
            "display_order": 99,
            "is_active": True
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/admin/services/",
                json=service_data,
                headers={**self.get_admin_headers(), "Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "service" in data and "id" in data["service"]:
                    self.created_service_id = data["service"]["id"]
                    self.log_test("POST /api/admin/services", True, f"Service created with ID: {self.created_service_id}")
                else:
                    self.log_test("POST /api/admin/services", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("POST /api/admin/services", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("POST /api/admin/services", False, f"Request failed: {str(e)}")
        
        # Test PUT service (update) - if we have a service ID
        if self.created_service_id:
            update_data = {
                "title": "Updated Test Service Review",
                "short_description": "Updated test service for review",
                "price": 249.0
            }
            
            try:
                response = requests.put(
                    f"{self.api_url}/admin/services/{self.created_service_id}",
                    json=update_data,
                    headers={**self.get_admin_headers(), "Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("PUT /api/admin/services/{id}", True, f"Service updated successfully")
                else:
                    self.log_test("PUT /api/admin/services/{id}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("PUT /api/admin/services/{id}", False, f"Request failed: {str(e)}")
            
            # Test DELETE service
            try:
                response = requests.delete(
                    f"{self.api_url}/admin/services/{self.created_service_id}",
                    headers=self.get_admin_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("DELETE /api/admin/services/{id}", True, f"Service deleted successfully")
                else:
                    self.log_test("DELETE /api/admin/services/{id}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("DELETE /api/admin/services/{id}", False, f"Request failed: {str(e)}")
    
    def test_admin_testimonials(self):
        """Test admin testimonials endpoint"""
        print("💬 Testing Admin Testimonials")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Admin Testimonials", False, "No admin token available")
            return
        
        try:
            response = requests.get(
                f"{self.api_url}/admin/testimonials/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "testimonials" in data:
                    self.log_test("GET /api/admin/testimonials", True, f"Retrieved {len(data['testimonials'])} testimonials")
                else:
                    self.log_test("GET /api/admin/testimonials", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("GET /api/admin/testimonials", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/admin/testimonials", False, f"Request failed: {str(e)}")
    
    def test_booking_submission(self):
        """Test booking submission with specified format"""
        print("📋 Testing Booking Submission")
        print("=" * 50)
        
        booking_data = {
            "name": "Test User",
            "phone": "9876543210",
            "email": "test@example.com",
            "vehicle_category": "2w",
            "customer_type": "individual",
            "service_needed": "Test booking service",
            "preferred_date": "2025-12-20",
            "address": "Test Address",
            "city": "Test City"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/bookings/",
                json=booking_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "name" in data:
                    self.log_test("POST /api/bookings", True, f"Booking created successfully with ID: {data['id']}")
                else:
                    self.log_test("POST /api/bookings", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("POST /api/bookings", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("POST /api/bookings", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all review request tests"""
        print("🎯 BATTWHEELS GARAGES - REVIEW REQUEST API TESTS")
        print("=" * 60)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 60)
        
        # Run all test categories
        self.test_health_endpoints()
        self.test_public_apis()
        
        # Admin tests require login first
        if self.test_admin_login():
            self.test_admin_crud_services()
            self.test_admin_testimonials()
        
        self.test_booking_submission()
        
        # Summary
        print("=" * 60)
        print("📊 REVIEW REQUEST TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        return passed == total

if __name__ == "__main__":
    tester = ReviewRequestTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)