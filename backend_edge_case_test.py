#!/usr/bin/env python3
"""
Backend API Edge Case Tests for Battwheels Garages
Tests error handling and edge cases
"""

import requests
import json
import sys

# Get backend URL from environment
BACKEND_URL = "https://car-repair-zone-1.preview.emergentagent.com/api"

class EdgeCaseTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
    
    def log_test(self, test_name, success, message):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
    
    def test_invalid_booking_data(self):
        """Test creating booking with invalid data"""
        invalid_data = {
            "vehicle_category": "2w",
            "customer_type": "individual",
            # Missing required fields
            "name": "Test User"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/bookings/",
                json=invalid_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 422:  # Validation error
                self.log_test("Invalid Booking Data", True, "Correctly rejected invalid booking data")
                return True
            else:
                self.log_test("Invalid Booking Data", False, f"Expected 422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Booking Data", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_nonexistent_booking(self):
        """Test getting a non-existent booking"""
        fake_id = "nonexistent-booking-id"
        
        try:
            response = requests.get(f"{self.base_url}/bookings/{fake_id}", timeout=10)
            
            if response.status_code == 404:
                self.log_test("Nonexistent Booking", True, "Correctly returned 404 for non-existent booking")
                return True
            else:
                self.log_test("Nonexistent Booking", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Nonexistent Booking", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_invalid_status_update(self):
        """Test updating booking with invalid status"""
        # First create a booking to get a valid ID
        booking_data = {
            "vehicle_category": "2w",
            "customer_type": "individual",
            "brand": "Test",
            "service_needed": "Test service",
            "preferred_date": "2025-12-15",
            "address": "Test Address",
            "city": "Test City",
            "name": "Test User",
            "phone": "+91 9999999999",
            "email": "test@test.com"
        }
        
        try:
            # Create booking
            create_response = requests.post(
                f"{self.base_url}/bookings/",
                json=booking_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if create_response.status_code == 200:
                booking_id = create_response.json()["id"]
                
                # Try to update with invalid status
                response = requests.patch(
                    f"{self.base_url}/bookings/{booking_id}/status",
                    params={"status": "invalid_status"},
                    timeout=10
                )
                
                if response.status_code == 400:
                    self.log_test("Invalid Status Update", True, "Correctly rejected invalid status")
                    return True
                else:
                    self.log_test("Invalid Status Update", False, f"Expected 400, got {response.status_code}")
            else:
                self.log_test("Invalid Status Update", False, "Failed to create test booking")
                
        except Exception as e:
            self.log_test("Invalid Status Update", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_invalid_email_format(self):
        """Test creating booking with invalid email"""
        invalid_email_data = {
            "vehicle_category": "2w",
            "customer_type": "individual",
            "brand": "Test",
            "service_needed": "Test service",
            "preferred_date": "2025-12-15",
            "address": "Test Address",
            "city": "Test City",
            "name": "Test User",
            "phone": "+91 9999999999",
            "email": "invalid-email-format"  # Invalid email
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/bookings/",
                json=invalid_email_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 422:  # Validation error
                self.log_test("Invalid Email Format", True, "Correctly rejected invalid email format")
                return True
            else:
                self.log_test("Invalid Email Format", False, f"Expected 422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Email Format", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_fleet_enquiry_edge_cases(self):
        """Test fleet enquiry with edge case data"""
        edge_case_data = {
            "company_name": "Test Company",
            "contact_person": "Test Person",
            "role": "manager",
            "email": "test@company.com",
            "phone": "+91 9999999999",
            "city": "Test City",
            "vehicle_count_2w": 0,  # Zero vehicles
            "vehicle_count_3w": 0,
            "vehicle_count_4w": 0,
            "vehicle_count_commercial": 0,
            "requirements": [],  # Empty requirements
            "details": ""  # Empty details
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/fleet-enquiries/",
                json=edge_case_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Fleet Enquiry Edge Cases", True, "Handled edge case data correctly")
                return True
            else:
                self.log_test("Fleet Enquiry Edge Cases", False, f"Expected 200, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Fleet Enquiry Edge Cases", False, f"Request failed: {str(e)}")
        
        return False
    
    def run_edge_case_tests(self):
        """Run all edge case tests"""
        print(f"🧪 Starting Edge Case Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Run edge case tests
        self.test_invalid_booking_data()
        self.test_nonexistent_booking()
        self.test_invalid_status_update()
        self.test_invalid_email_format()
        self.test_fleet_enquiry_edge_cases()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 EDGE CASE TEST SUMMARY")
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
    tester = EdgeCaseTester()
    success = tester.run_edge_case_tests()
    sys.exit(0 if success else 1)