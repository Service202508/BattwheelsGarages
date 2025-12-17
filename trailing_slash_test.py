#!/usr/bin/env python3
"""
Test to verify trailing slash behavior
"""

import requests
import json

BACKEND_URL = "https://garage-rescue-1.preview.emergentagent.com/api"

def test_trailing_slash_behavior():
    # First login to get token
    login_data = {
        "email": "admin@battwheelsgarages.in",
        "password": "adminpassword"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/admin/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing trailing slash behavior:")
    
    # Test WITH trailing slash
    print("\n1. Testing WITH trailing slash:")
    response_with_slash = requests.get(
        f"{BACKEND_URL}/admin/services/",  # WITH trailing slash
        headers=headers,
        allow_redirects=False  # Don't follow redirects
    )
    print(f"   Status: {response_with_slash.status_code}")
    if response_with_slash.status_code == 307:
        print(f"   Redirect to: {response_with_slash.headers.get('location', 'N/A')}")
    
    # Test WITHOUT trailing slash
    print("\n2. Testing WITHOUT trailing slash:")
    response_without_slash = requests.get(
        f"{BACKEND_URL}/admin/services",  # WITHOUT trailing slash
        headers=headers
    )
    print(f"   Status: {response_without_slash.status_code}")
    if response_without_slash.status_code == 200:
        data = response_without_slash.json()
        print(f"   Services count: {len(data.get('services', []))}")
    else:
        print(f"   Error: {response_without_slash.text}")

if __name__ == "__main__":
    test_trailing_slash_behavior()