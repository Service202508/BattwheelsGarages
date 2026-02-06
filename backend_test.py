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
BACKEND_URL = "https://battwheels-upgrade.preview.emergentagent.com/api"

class BattwheelsAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.admin_token = None
        self.created_ids = {
            'bookings': [],
            'fleet_enquiries': [],
            'contacts': [],
            'services': [],
            'blogs': [],
            'testimonials': [],
            'jobs': []
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
    
    def test_admin_login(self):
        """Test admin login with correct credentials"""
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
                        self.log_test("Admin Login", True, f"Login successful for {data['user']['email']}", {"user": data["user"]})
                        return True
                    else:
                        self.log_test("Admin Login", False, f"Invalid token format: {data}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Admin Login", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Request failed: {str(e)}")
        
        return False
    
    def get_admin_headers(self):
        """Get headers with admin authorization"""
        if not self.admin_token:
            return {}
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_get_bookings(self):
        """Test getting all bookings via admin API"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/bookings/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total", "bookings", "limit", "skip"]
                
                if all(field in data for field in required_fields):
                    if isinstance(data["bookings"], list):
                        self.log_test("Admin Get Bookings", True, f"Retrieved {data['total']} bookings", {"count": data["total"]})
                        return data["bookings"]
                    else:
                        self.log_test("Admin Get Bookings", False, f"Bookings not a list: {type(data['bookings'])}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Admin Get Bookings", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Admin Get Bookings", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Get Bookings", False, f"Request failed: {str(e)}")
        
        return []
    
    def test_admin_get_contacts(self):
        """Test getting all contacts via admin API"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/contacts/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total", "contacts", "limit", "skip"]
                
                if all(field in data for field in required_fields):
                    if isinstance(data["contacts"], list):
                        self.log_test("Admin Get Contacts", True, f"Retrieved {data['total']} contacts", {"count": data["total"]})
                        return True
                    else:
                        self.log_test("Admin Get Contacts", False, f"Contacts not a list: {type(data['contacts'])}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Admin Get Contacts", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Admin Get Contacts", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Get Contacts", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_admin_get_services(self):
        """Test getting all services via admin API"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/services/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "services" in data and isinstance(data["services"], list):
                    self.log_test("Admin Get Services", True, f"Retrieved {len(data['services'])} services", {"count": len(data["services"])})
                    return True
                else:
                    self.log_test("Admin Get Services", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("Admin Get Services", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Get Services", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_admin_get_blogs(self):
        """Test getting all blogs via admin API"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/blogs/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total", "blogs", "limit", "skip"]
                
                if all(field in data for field in required_fields):
                    if isinstance(data["blogs"], list):
                        self.log_test("Admin Get Blogs", True, f"Retrieved {data['total']} blogs", {"count": data["total"]})
                        return True
                    else:
                        self.log_test("Admin Get Blogs", False, f"Blogs not a list: {type(data['blogs'])}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Admin Get Blogs", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Admin Get Blogs", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Get Blogs", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_admin_get_testimonials(self):
        """Test getting all testimonials via admin API"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/testimonials/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "testimonials" in data and isinstance(data["testimonials"], list):
                    self.log_test("Admin Get Testimonials", True, f"Retrieved {len(data['testimonials'])} testimonials", {"count": len(data["testimonials"])})
                    return True
                else:
                    self.log_test("Admin Get Testimonials", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("Admin Get Testimonials", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Get Testimonials", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_admin_get_jobs(self):
        """Test getting all jobs via admin API"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/jobs/",
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "jobs" in data and isinstance(data["jobs"], list):
                    self.log_test("Admin Get Jobs", True, f"Retrieved {len(data['jobs'])} jobs", {"count": len(data["jobs"])})
                    return True
                else:
                    self.log_test("Admin Get Jobs", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("Admin Get Jobs", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Get Jobs", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_admin_create_service(self):
        """Test creating a new service via admin API"""
        service_data = {
            "title": "Battery Health Check",
            "slug": "battery-health-check",
            "short_description": "Quick battery diagnostics",
            "long_description": "Comprehensive battery health diagnostics and performance analysis",
            "vehicle_segments": ["2W", "3W", "4W"],
            "pricing_model": "fixed",
            "price": 299.0,
            "display_order": 1,
            "is_active": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/admin/services/",
                json=service_data,
                headers={**self.get_admin_headers(), "Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "service" in data and "message" in data:
                    service = data["service"]
                    if service.get("title") == service_data["title"] and service.get("slug") == service_data["slug"]:
                        self.created_ids['services'].append(service.get("id"))
                        self.log_test("Admin Create Service", True, f"Service created with ID: {service.get('id')}", service)
                        return service.get("id")
                    else:
                        self.log_test("Admin Create Service", False, f"Service data mismatch: {service}", data)
                else:
                    self.log_test("Admin Create Service", False, f"Invalid response format: {data}", data)
            else:
                self.log_test("Admin Create Service", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Create Service", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_admin_update_booking_status(self, bookings):
        """Test updating booking status via admin API"""
        if not bookings:
            self.log_test("Admin Update Booking Status", False, "No bookings available to test status update")
            return False
            
        booking_id = bookings[0].get("id")
        if not booking_id:
            self.log_test("Admin Update Booking Status", False, "No booking ID found in first booking")
            return False
            
        try:
            response = requests.patch(
                f"{self.base_url}/admin/bookings/{booking_id}/status",
                params={"status": "confirmed"},
                headers=self.get_admin_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "confirmed" and "message" in data:
                    self.log_test("Admin Update Booking Status", True, f"Status updated to confirmed for booking {booking_id}", data)
                    return True
                else:
                    self.log_test("Admin Update Booking Status", False, f"Unexpected response: {data}", data)
            else:
                self.log_test("Admin Update Booking Status", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Update Booking Status", False, f"Request failed: {str(e)}")
        
        return False
    
    def run_admin_tests(self):
        """Run all admin dashboard tests"""
        print(f"\n🔐 Testing Admin Dashboard APIs...")
        print("=" * 60)
        
        # Test admin login first
        if not self.test_admin_login():
            print("❌ Admin login failed - cannot proceed with admin tests")
            return False
        
        # Test all admin dashboard APIs
        print("\n📊 Testing Admin Dashboard APIs...")
        bookings = self.test_admin_get_bookings()
        self.test_admin_get_contacts()
        self.test_admin_get_services()
        self.test_admin_get_blogs()
        self.test_admin_get_testimonials()
        self.test_admin_get_jobs()
        
        # Test CRUD operations
        print("\n🔧 Testing Admin CRUD Operations...")
        service_id = self.test_admin_create_service()
        
        # Test status updates
        print("\n📝 Testing Admin Status Updates...")
        self.test_admin_update_booking_status(bookings)
        
        return True
    
    def test_public_services_api(self):
        """Test GET /api/services - Should return 5 services with specific fields"""
        try:
            response = requests.get(f"{self.base_url}/services", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "services" not in data:
                    self.log_test("Public Services API", False, "Missing 'services' key in response", data)
                    return False
                
                services = data["services"]
                
                # Check count
                if len(services) != 5:
                    self.log_test("Public Services API", False, f"Expected 5 services, got {len(services)}", {"count": len(services)})
                    return False
                
                # Check required fields in each service
                required_fields = ["title", "slug", "short_description", "vehicle_segments"]
                for i, service in enumerate(services):
                    missing_fields = [field for field in required_fields if field not in service]
                    if missing_fields:
                        self.log_test("Public Services API", False, f"Service {i+1} missing fields: {missing_fields}", service)
                        return False
                
                self.log_test("Public Services API", True, f"Successfully retrieved 5 services with all required fields", {"services_count": len(services)})
                return True
            else:
                self.log_test("Public Services API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Services API", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_public_blogs_api(self):
        """Test GET /api/blogs - Should return 3 blogs with specific fields"""
        try:
            response = requests.get(f"{self.base_url}/blogs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "blogs" not in data:
                    self.log_test("Public Blogs API", False, "Missing 'blogs' key in response", data)
                    return False
                
                blogs = data["blogs"]
                
                # Check count
                if len(blogs) != 3:
                    self.log_test("Public Blogs API", False, f"Expected 3 blogs, got {len(blogs)}", {"count": len(blogs)})
                    return False
                
                # Check required fields in each blog
                required_fields = ["title", "slug", "excerpt", "category"]
                for i, blog in enumerate(blogs):
                    missing_fields = [field for field in required_fields if field not in blog]
                    if missing_fields:
                        self.log_test("Public Blogs API", False, f"Blog {i+1} missing fields: {missing_fields}", blog)
                        return False
                    
                    # Check status is published (if present)
                    if "status" in blog and blog["status"] != "published":
                        self.log_test("Public Blogs API", False, f"Blog {i+1} status is not 'published': {blog['status']}", blog)
                        return False
                
                self.log_test("Public Blogs API", True, f"Successfully retrieved 3 blogs with all required fields", {"blogs_count": len(blogs)})
                return True
            else:
                self.log_test("Public Blogs API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Blogs API", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_public_testimonials_api(self):
        """Test GET /api/testimonials - Should return 8 testimonials with specific fields"""
        try:
            response = requests.get(f"{self.base_url}/testimonials", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if "testimonials" not in data:
                    self.log_test("Public Testimonials API", False, "Missing 'testimonials' key in response", data)
                    return False
                
                testimonials = data["testimonials"]
                
                # Check count
                if len(testimonials) != 8:
                    self.log_test("Public Testimonials API", False, f"Expected 8 testimonials, got {len(testimonials)}", {"count": len(testimonials)})
                    return False
                
                # Check required fields in each testimonial
                required_fields = ["name", "company", "role", "quote", "rating"]
                for i, testimonial in enumerate(testimonials):
                    missing_fields = [field for field in required_fields if field not in testimonial]
                    if missing_fields:
                        self.log_test("Public Testimonials API", False, f"Testimonial {i+1} missing fields: {missing_fields}", testimonial)
                        return False
                
                self.log_test("Public Testimonials API", True, f"Successfully retrieved 8 testimonials with all required fields", {"testimonials_count": len(testimonials)})
                return True
            else:
                self.log_test("Public Testimonials API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Testimonials API", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_specific_admin_login(self):
        """Test admin login with specific credentials from review request"""
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
                        self.log_test("Specific Admin Login", True, f"Login successful with specified credentials", {"user_email": data['user']['email']})
                        return True
                    else:
                        self.log_test("Specific Admin Login", False, f"Invalid token format: {data}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Specific Admin Login", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Specific Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Specific Admin Login", False, f"Request failed: {str(e)}")
        
        return False
    
    def run_review_request_tests(self):
        """Run tests specifically mentioned in the review request"""
        print(f"🎯 Running Review Request Specific Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Test health check first
        if not self.test_health_check():
            print("❌ Health check failed - backend may not be running")
            return False
        
        # Test specific API requirements
        print("\n🔍 Testing Specific API Requirements...")
        self.test_public_services_api()
        self.test_public_blogs_api()
        self.test_public_testimonials_api()
        self.test_specific_admin_login()
        
        return True
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting Battwheels Garages API Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # First run the specific review request tests
        self.run_review_request_tests()
        
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
        
        # Test admin dashboard
        self.run_admin_tests()
        
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