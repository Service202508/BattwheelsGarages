#!/usr/bin/env python3
"""
Public API and SEO Test Suite for Battwheels Garages
Tests public endpoints and SEO implementation as requested in the review
"""

import requests
import json
import sys
from datetime import datetime
import xml.etree.ElementTree as ET

# Get backend URL from environment - using the same URL as frontend
BACKEND_URL = "https://battwheels-ev-1.preview.emergentagent.com/api"
FRONTEND_URL = "https://battwheels-ev-1.preview.emergentagent.com"

class PublicAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.frontend_url = FRONTEND_URL
        self.test_results = []
    
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
    
    def test_public_services_api(self):
        """Test GET /api/services - Should return services list or empty array"""
        try:
            response = requests.get(f"{self.base_url}/services", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required structure
                if "services" in data and "total" in data:
                    if isinstance(data["services"], list) and isinstance(data["total"], int):
                        if data["total"] == len(data["services"]):
                            self.log_test("Public Services API", True, 
                                        f"Correct structure - {data['total']} services returned", 
                                        {"total": data["total"], "services_count": len(data["services"])})
                            return True
                        else:
                            self.log_test("Public Services API", False, 
                                        f"Total count mismatch: total={data['total']}, array_length={len(data['services'])}", data)
                    else:
                        self.log_test("Public Services API", False, 
                                    f"Invalid data types: services={type(data['services'])}, total={type(data['total'])}", data)
                else:
                    self.log_test("Public Services API", False, 
                                f"Missing required fields. Expected: services, total. Got: {list(data.keys())}", data)
            else:
                self.log_test("Public Services API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Services API", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_public_blogs_api(self):
        """Test GET /api/blogs - Should return blogs list with pagination"""
        try:
            response = requests.get(f"{self.base_url}/blogs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required structure
                required_fields = ["blogs", "total", "skip", "limit"]
                if all(field in data for field in required_fields):
                    if (isinstance(data["blogs"], list) and 
                        isinstance(data["total"], int) and 
                        isinstance(data["skip"], int) and 
                        isinstance(data["limit"], int)):
                        
                        # Check default pagination values
                        if data["skip"] == 0 and data["limit"] == 20:
                            self.log_test("Public Blogs API", True, 
                                        f"Correct structure - {data['total']} blogs, skip={data['skip']}, limit={data['limit']}", 
                                        {"total": data["total"], "blogs_count": len(data["blogs"]), 
                                         "skip": data["skip"], "limit": data["limit"]})
                            return True
                        else:
                            self.log_test("Public Blogs API", False, 
                                        f"Incorrect default pagination: skip={data['skip']}, limit={data['limit']}", data)
                    else:
                        self.log_test("Public Blogs API", False, 
                                    f"Invalid data types in response", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Public Blogs API", False, 
                                f"Missing required fields: {missing}", data)
            else:
                self.log_test("Public Blogs API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Blogs API", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_public_blogs_category_filter(self):
        """Test GET /api/blogs?category=Fleet%20Ops - Should filter by category"""
        try:
            response = requests.get(f"{self.base_url}/blogs?category=Fleet%20Ops", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required structure
                required_fields = ["blogs", "total", "skip", "limit"]
                if all(field in data for field in required_fields):
                    if isinstance(data["blogs"], list):
                        # Check if any blogs returned have the correct category (if any exist)
                        category_correct = True
                        for blog in data["blogs"]:
                            if "category" in blog and blog["category"] != "Fleet Ops":
                                category_correct = False
                                break
                        
                        if category_correct:
                            self.log_test("Public Blogs Category Filter", True, 
                                        f"Category filter working - {data['total']} Fleet Ops blogs", 
                                        {"total": data["total"], "category": "Fleet Ops"})
                            return True
                        else:
                            self.log_test("Public Blogs Category Filter", False, 
                                        f"Category filter not working - found blogs with wrong category", data)
                    else:
                        self.log_test("Public Blogs Category Filter", False, 
                                    f"Blogs field is not a list: {type(data['blogs'])}", data)
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Public Blogs Category Filter", False, 
                                f"Missing required fields: {missing}", data)
            else:
                self.log_test("Public Blogs Category Filter", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Blogs Category Filter", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_public_testimonials_api(self):
        """Test GET /api/testimonials - Should return testimonials list"""
        try:
            response = requests.get(f"{self.base_url}/testimonials", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required structure
                if "testimonials" in data and "total" in data:
                    if isinstance(data["testimonials"], list) and isinstance(data["total"], int):
                        if data["total"] == len(data["testimonials"]):
                            self.log_test("Public Testimonials API", True, 
                                        f"Correct structure - {data['total']} testimonials returned", 
                                        {"total": data["total"], "testimonials_count": len(data["testimonials"])})
                            return True
                        else:
                            self.log_test("Public Testimonials API", False, 
                                        f"Total count mismatch: total={data['total']}, array_length={len(data['testimonials'])}", data)
                    else:
                        self.log_test("Public Testimonials API", False, 
                                    f"Invalid data types: testimonials={type(data['testimonials'])}, total={type(data['total'])}", data)
                else:
                    self.log_test("Public Testimonials API", False, 
                                f"Missing required fields. Expected: testimonials, total. Got: {list(data.keys())}", data)
            else:
                self.log_test("Public Testimonials API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Testimonials API", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_public_jobs_api(self):
        """Test GET /api/jobs - Should return jobs list"""
        try:
            response = requests.get(f"{self.base_url}/jobs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required structure
                if "jobs" in data and "total" in data:
                    if isinstance(data["jobs"], list) and isinstance(data["total"], int):
                        if data["total"] == len(data["jobs"]):
                            self.log_test("Public Jobs API", True, 
                                        f"Correct structure - {data['total']} jobs returned", 
                                        {"total": data["total"], "jobs_count": len(data["jobs"])})
                            return True
                        else:
                            self.log_test("Public Jobs API", False, 
                                        f"Total count mismatch: total={data['total']}, array_length={len(data['jobs'])}", data)
                    else:
                        self.log_test("Public Jobs API", False, 
                                    f"Invalid data types: jobs={type(data['jobs'])}, total={type(data['total'])}", data)
                else:
                    self.log_test("Public Jobs API", False, 
                                f"Missing required fields. Expected: jobs, total. Got: {list(data.keys())}", data)
            else:
                self.log_test("Public Jobs API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Public Jobs API", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_sitemap_xml(self):
        """Test GET /sitemap.xml - Should return XML sitemap"""
        try:
            response = requests.get(f"{self.frontend_url}/sitemap.xml", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Check if it's valid XML
                try:
                    root = ET.fromstring(content)
                    
                    # Check if it's a sitemap
                    if root.tag.endswith('urlset'):
                        urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
                        if len(urls) > 0:
                            self.log_test("Sitemap XML", True, 
                                        f"Valid XML sitemap with {len(urls)} URLs", 
                                        {"url_count": len(urls), "content_type": response.headers.get('content-type', 'unknown')})
                            return True
                        else:
                            self.log_test("Sitemap XML", False, 
                                        f"Sitemap has no URLs", {"content": content[:200]})
                    else:
                        self.log_test("Sitemap XML", False, 
                                    f"Not a valid sitemap XML - root tag: {root.tag}", {"content": content[:200]})
                        
                except ET.ParseError as e:
                    self.log_test("Sitemap XML", False, 
                                f"Invalid XML format: {str(e)}", {"content": content[:200]})
            else:
                self.log_test("Sitemap XML", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Sitemap XML", False, f"Request failed: {str(e)}")
        
        return False
    
    def test_robots_txt(self):
        """Test GET /robots.txt - Should return robots.txt content"""
        try:
            response = requests.get(f"{self.frontend_url}/robots.txt", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Check if it contains basic robots.txt directives
                if "User-agent:" in content and ("Allow:" in content or "Disallow:" in content):
                    # Check for sitemap reference
                    if "Sitemap:" in content:
                        self.log_test("Robots.txt", True, 
                                    f"Valid robots.txt with sitemap reference", 
                                    {"content_length": len(content), "has_sitemap": True})
                        return True
                    else:
                        self.log_test("Robots.txt", True, 
                                    f"Valid robots.txt but no sitemap reference", 
                                    {"content_length": len(content), "has_sitemap": False})
                        return True
                else:
                    self.log_test("Robots.txt", False, 
                                f"Invalid robots.txt format", {"content": content[:200]})
            else:
                self.log_test("Robots.txt", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Robots.txt", False, f"Request failed: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """Run all public API and SEO tests"""
        print(f"🚀 Starting Battwheels Public API & SEO Tests")
        print(f"Backend URL: {self.base_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print("=" * 60)
        
        # Test public API endpoints
        print("\n📋 Testing Public API Endpoints...")
        self.test_public_services_api()
        self.test_public_blogs_api()
        self.test_public_blogs_category_filter()
        self.test_public_testimonials_api()
        self.test_public_jobs_api()
        
        # Test SEO static files
        print("\n🔍 Testing SEO Static Files...")
        self.test_sitemap_xml()
        self.test_robots_txt()
        
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
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        return passed == total

if __name__ == "__main__":
    tester = PublicAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)