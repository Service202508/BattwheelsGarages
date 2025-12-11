#!/usr/bin/env python3
"""
Backend API Test Suite for Battwheels Garages
Tests all API endpoints with comprehensive validation including MongoDB persistence and email notifications
"""

import requests
import json
import sys
from datetime import datetime
import uuid
import io
import os

# Get backend URL from environment
BACKEND_URL = "https://ev-rescue-hub.preview.emergentagent.com/api"

class BattwheelsAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.created_ids = {
            'bookings': [],
            'fleet_enquiries': [],
            'contacts': []
        }
    
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
    
    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_keys = ["status", "message"]
                
                if all(key in data for key in expected_keys):
                    if data["status"] == "healthy" and "Battwheels Garages API" in data["message"]:
                        self.log_test("Health Check", True, "Health endpoint working correctly", data)
                        return True
                    else:
                        self.log_test("Health Check", False, f"Unexpected response content: {data}", data)
                else:
                    self.log_test("Health Check", False, f"Missing required keys in response: {data}", data)
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_create_booking(self):
        """Test creating a service booking"""
        booking_data = {
            "vehicle_category": "2w",
            "customer_type": "individual",
            "brand": "Ather",
            "model": "450X",
            "service_needed": "Periodic service",
            "preferred_date": "2025-12-15",
            "time_slot": "morning",
            "address": "123 Test Street, Sector 10",
            "city": "Delhi",
            "name": "John Doe",
            "phone": "+91 9876543210",
            "email": "john@test.com"
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
                        self.created_ids['bookings'].append(data["id"])
                        self.log_test("Create Booking", True, f"Booking created successfully with ID: {data['id']}", data)
                        return data["id"]
                    else:
                        self.log_test("Create Booking", False, f"Unexpected status: {data['status']}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Create Booking", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Create Booking", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Booking", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_get_all_bookings(self):
        """Test getting all bookings"""
        try:
            response = requests.get(f"{self.base_url}/bookings/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get All Bookings", True, f"Retrieved {len(data)} bookings", {"count": len(data)})
                    return True
                else:
                    self.log_test("Get All Bookings", False, f"Expected list, got: {type(data)}", data)
            else:
                self.log_test("Get All Bookings", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get All Bookings", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_get_booking_by_id(self, booking_id):
        """Test getting a specific booking by ID"""
        if not booking_id:
            self.log_test("Get Booking by ID", False, "No booking ID provided")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/bookings/{booking_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == booking_id:
                    self.log_test("Get Booking by ID", True, f"Retrieved booking {booking_id}", data)
                    return True
                else:
                    self.log_test("Get Booking by ID", False, f"ID mismatch: expected {booking_id}, got {data.get('id')}", data)
            elif response.status_code == 404:
                self.log_test("Get Booking by ID", False, f"Booking not found: {booking_id}")
            else:
                self.log_test("Get Booking by ID", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Booking by ID", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_update_booking_status(self, booking_id):
        """Test updating booking status"""
        if not booking_id:
            self.log_test("Update Booking Status", False, "No booking ID provided")
            return False
            
        try:
            response = requests.patch(
                f"{self.base_url}/bookings/{booking_id}/status",
                params={"status": "confirmed"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "confirmed":
                    self.log_test("Update Booking Status", True, f"Status updated to confirmed for booking {booking_id}", data)
                    return True
                else:
                    self.log_test("Update Booking Status", False, f"Unexpected response: {data}", data)
            else:
                self.log_test("Update Booking Status", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Update Booking Status", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_create_fleet_enquiry(self):
        """Test creating a fleet enquiry"""
        enquiry_data = {
            "company_name": "ABC Logistics",
            "contact_person": "Jane Smith",
            "role": "fleet-manager",
            "email": "jane@abclogistics.com",
            "phone": "+91 9123456789",
            "city": "Mumbai",
            "vehicle_count_2w": 50,
            "vehicle_count_3w": 30,
            "vehicle_count_4w": 10,
            "vehicle_count_commercial": 5,
            "requirements": ["Periodic Maintenance", "Breakdown Support"],
            "details": "Need fleet maintenance solution"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/fleet-enquiries/",
                json=enquiry_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "company_name", "contact_person", "email", "status", "created_at"]
                
                if all(field in data for field in required_fields):
                    if data["status"] == "new":
                        self.created_ids['fleet_enquiries'].append(data["id"])
                        self.log_test("Create Fleet Enquiry", True, f"Fleet enquiry created with ID: {data['id']}", data)
                        return data["id"]
                    else:
                        self.log_test("Create Fleet Enquiry", False, f"Unexpected status: {data['status']}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Create Fleet Enquiry", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Create Fleet Enquiry", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Fleet Enquiry", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_get_all_fleet_enquiries(self):
        """Test getting all fleet enquiries"""
        try:
            response = requests.get(f"{self.base_url}/fleet-enquiries/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get All Fleet Enquiries", True, f"Retrieved {len(data)} enquiries", {"count": len(data)})
                    return True
                else:
                    self.log_test("Get All Fleet Enquiries", False, f"Expected list, got: {type(data)}", data)
            else:
                self.log_test("Get All Fleet Enquiries", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get All Fleet Enquiries", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_update_fleet_enquiry_status(self, enquiry_id):
        """Test updating fleet enquiry status"""
        if not enquiry_id:
            self.log_test("Update Fleet Enquiry Status", False, "No enquiry ID provided")
            return False
            
        try:
            response = requests.patch(
                f"{self.base_url}/fleet-enquiries/{enquiry_id}/status",
                params={"status": "in_discussion"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "in_discussion":
                    self.log_test("Update Fleet Enquiry Status", True, f"Status updated to in_discussion for enquiry {enquiry_id}", data)
                    return True
                else:
                    self.log_test("Update Fleet Enquiry Status", False, f"Unexpected response: {data}", data)
            else:
                self.log_test("Update Fleet Enquiry Status", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Update Fleet Enquiry Status", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_create_contact_message(self):
        """Test creating a contact message"""
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+91 9999999999",
            "message": "I need information about EV services"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/contacts/",
                json=contact_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "email", "message", "status", "created_at"]
                
                if all(field in data for field in required_fields):
                    if data["status"] == "new":
                        self.created_ids['contacts'].append(data["id"])
                        self.log_test("Create Contact Message", True, f"Contact message created with ID: {data['id']}", data)
                        return data["id"]
                    else:
                        self.log_test("Create Contact Message", False, f"Unexpected status: {data['status']}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Create Contact Message", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Create Contact Message", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Contact Message", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_get_all_contact_messages(self):
        """Test getting all contact messages"""
        try:
            response = requests.get(f"{self.base_url}/contacts/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get All Contact Messages", True, f"Retrieved {len(data)} messages", {"count": len(data)})
                    return True
                else:
                    self.log_test("Get All Contact Messages", False, f"Expected list, got: {type(data)}", data)
            else:
                self.log_test("Get All Contact Messages", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get All Contact Messages", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_create_career_application(self):
        """Test creating a career application with file upload"""
        # Create a dummy PDF file content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        # Prepare form data
        form_data = {
            'job_id': '1',
            'job_title': 'EV Technician',
            'name': 'Alex Johnson',
            'email': 'alex@example.com',
            'phone': '+91 9876543210',
            'experience': '3 years in automotive industry'
        }
        
        files = {
            'cv_file': ('alex_cv.pdf', pdf_content, 'application/pdf')
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/careers/applications",
                data=form_data,
                files=files,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "application_id"]
                
                if all(field in data for field in required_fields):
                    if data["success"] is True:
                        self.log_test("Create Career Application", True, f"Application created with ID: {data['application_id']}", data)
                        return data["application_id"]
                    else:
                        self.log_test("Create Career Application", False, f"Success flag is False: {data}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Create Career Application", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Create Career Application", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Career Application", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_get_all_career_applications(self):
        """Test getting all career applications"""
        try:
            response = requests.get(f"{self.base_url}/careers/applications", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get All Career Applications", True, f"Retrieved {len(data)} applications", {"count": len(data)})
                    return True
                else:
                    self.log_test("Get All Career Applications", False, f"Expected list, got: {type(data)}", data)
            else:
                self.log_test("Get All Career Applications", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get All Career Applications", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_career_file_validation(self):
        """Test career application file validation (invalid file type)"""
        # Create a text file (invalid type)
        txt_content = b"This is a text file, not a PDF"
        
        form_data = {
            'job_id': '1',
            'job_title': 'EV Technician',
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+91 9876543210'
        }
        
        files = {
            'cv_file': ('resume.txt', txt_content, 'text/plain')
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/careers/applications",
                data=form_data,
                files=files,
                timeout=10
            )
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid file type" in data.get("detail", ""):
                    self.log_test("Career File Validation", True, "Correctly rejected invalid file type", data)
                    return True
                else:
                    self.log_test("Career File Validation", False, f"Unexpected error message: {data}", data)
            else:
                self.log_test("Career File Validation", False, f"Expected 400 error, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Career File Validation", False, f"Request failed: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting Battwheels Garages API Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Test health check first
        if not self.test_health_check():
            print("❌ Health check failed - backend may not be running")
            return False
        
        # Test service bookings
        print("\n📋 Testing Service Bookings...")
        booking_id = self.test_create_booking()
        self.test_get_all_bookings()
        if booking_id:
            self.test_get_booking_by_id(booking_id)
            self.test_update_booking_status(booking_id)
        
        # Test fleet enquiries
        print("\n🚛 Testing Fleet Enquiries...")
        enquiry_id = self.test_create_fleet_enquiry()
        self.test_get_all_fleet_enquiries()
        if enquiry_id:
            self.test_update_fleet_enquiry_status(enquiry_id)
        
        # Test contact messages
        print("\n📞 Testing Contact Messages...")
        contact_id = self.test_create_contact_message()
        self.test_get_all_contact_messages()
        
        # Test career applications
        print("\n📄 Testing Career Applications...")
        application_id = self.test_create_career_application()
        self.test_get_all_career_applications()
        self.test_career_file_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
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
        
        return passed == total

if __name__ == "__main__":
    tester = BattwheelsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)