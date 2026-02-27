"""
Test Estimate Edit functionality at different statuses.
Tests: Edit button should be available for all statuses EXCEPT 'converted' and 'void'.
Verification: User requested estimates to be editable at any stage until converted to Invoice.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEstimateEditStatus:
    """Test estimate editing availability at different statuses"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@battwheels.in", "password": "DevTest@123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_draft_estimate_can_be_edited(self, headers):
        """Test editing a Draft status estimate - should succeed"""
        # Get Draft estimate EST-00062
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/?search=EST-00062",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get estimate: {response.text}"
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        # Find the draft estimate
        draft_estimate = None
        for est in estimates:
            if est.get("estimate_number") == "EST-00062":
                draft_estimate = est
                break
        
        if not draft_estimate:
            pytest.skip("EST-00062 not found, skipping draft edit test")
        
        estimate_id = draft_estimate.get("estimate_id")
        current_status = draft_estimate.get("status")
        
        print(f"Found EST-00062 with status: {current_status}, ID: {estimate_id}")
        
        # Attempt to update the estimate (simple field change)
        update_payload = {
            "reference_number": f"TEST-EDIT-DRAFT-{current_status}"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json=update_payload
        )
        
        print(f"Update response status: {update_response.status_code}")
        print(f"Update response: {update_response.text[:500]}")
        
        assert update_response.status_code == 200, f"Edit failed for draft estimate: {update_response.text}"
        assert update_response.json().get("code") == 0
        print(f"PASS: Draft estimate (EST-00062) can be edited successfully")
    
    def test_sent_estimate_can_be_edited(self, headers):
        """Test editing a Sent status estimate - should succeed"""
        # Get Sent estimate EST-00059
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/?search=EST-00059",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        sent_estimate = None
        for est in estimates:
            if est.get("estimate_number") == "EST-00059":
                sent_estimate = est
                break
        
        if not sent_estimate:
            pytest.skip("EST-00059 not found")
        
        estimate_id = sent_estimate.get("estimate_id")
        current_status = sent_estimate.get("status")
        
        print(f"Found EST-00059 with status: {current_status}, ID: {estimate_id}")
        
        update_payload = {
            "reference_number": f"TEST-EDIT-SENT-{current_status}"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json=update_payload
        )
        
        print(f"Update response status: {update_response.status_code}")
        
        assert update_response.status_code == 200, f"Edit failed for sent estimate: {update_response.text}"
        assert update_response.json().get("code") == 0
        print(f"PASS: Sent estimate (EST-00059) can be edited successfully")
    
    def test_accepted_estimate_can_be_edited(self, headers):
        """Test editing an Accepted status estimate - should succeed"""
        # Get Accepted estimate EST-00037
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/?search=EST-00037",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        accepted_estimate = None
        for est in estimates:
            if est.get("estimate_number") == "EST-00037":
                accepted_estimate = est
                break
        
        if not accepted_estimate:
            pytest.skip("EST-00037 not found")
        
        estimate_id = accepted_estimate.get("estimate_id")
        current_status = accepted_estimate.get("status")
        
        print(f"Found EST-00037 with status: {current_status}, ID: {estimate_id}")
        
        update_payload = {
            "reference_number": f"TEST-EDIT-ACCEPTED-{current_status}"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json=update_payload
        )
        
        print(f"Update response status: {update_response.status_code}")
        
        assert update_response.status_code == 200, f"Edit failed for accepted estimate: {update_response.text}"
        assert update_response.json().get("code") == 0
        print(f"PASS: Accepted estimate (EST-00037) can be edited successfully")
    
    def test_converted_estimate_cannot_be_edited(self, headers):
        """Test editing a Converted status estimate - should FAIL with 400"""
        # Get Converted estimate EST-00036
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/?search=EST-00036",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        converted_estimate = None
        for est in estimates:
            if est.get("estimate_number") == "EST-00036":
                converted_estimate = est
                break
        
        if not converted_estimate:
            pytest.skip("EST-00036 not found")
        
        estimate_id = converted_estimate.get("estimate_id")
        current_status = converted_estimate.get("status")
        
        print(f"Found EST-00036 with status: {current_status}, ID: {estimate_id}")
        
        # Verify it's actually converted status
        if current_status != "converted":
            print(f"WARNING: EST-00036 status is '{current_status}', not 'converted'")
        
        update_payload = {
            "reference_number": f"TEST-EDIT-CONVERTED"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json=update_payload
        )
        
        print(f"Update response status: {update_response.status_code}")
        print(f"Update response: {update_response.text[:300]}")
        
        # Should fail with 400 error
        assert update_response.status_code == 400, f"Converted estimate should NOT be editable, but got {update_response.status_code}"
        assert "cannot be edited" in update_response.text.lower() or "converted" in update_response.text.lower()
        print(f"PASS: Converted estimate (EST-00036) correctly blocked from editing")
    
    def test_declined_estimate_can_be_edited(self, headers):
        """Test editing a Declined status estimate - should succeed"""
        # Search for any declined estimate
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/?status=declined&per_page=5",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        if len(estimates) == 0:
            pytest.skip("No declined estimates found")
        
        declined_estimate = estimates[0]
        estimate_id = declined_estimate.get("estimate_id")
        estimate_number = declined_estimate.get("estimate_number")
        
        print(f"Found declined estimate: {estimate_number}, ID: {estimate_id}")
        
        update_payload = {
            "reference_number": f"TEST-EDIT-DECLINED"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json=update_payload
        )
        
        print(f"Update response status: {update_response.status_code}")
        
        assert update_response.status_code == 200, f"Edit failed for declined estimate: {update_response.text}"
        print(f"PASS: Declined estimate can be edited successfully")
    
    def test_expired_estimate_can_be_edited(self, headers):
        """Test editing an Expired status estimate - should succeed"""
        # Search for any expired estimate
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/?status=expired&per_page=5",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        if len(estimates) == 0:
            pytest.skip("No expired estimates found")
        
        expired_estimate = estimates[0]
        estimate_id = expired_estimate.get("estimate_id")
        estimate_number = expired_estimate.get("estimate_number")
        
        print(f"Found expired estimate: {estimate_number}, ID: {estimate_id}")
        
        update_payload = {
            "reference_number": f"TEST-EDIT-EXPIRED"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/estimates-enhanced/{estimate_id}",
            headers=headers,
            json=update_payload
        )
        
        print(f"Update response status: {update_response.status_code}")
        
        assert update_response.status_code == 200, f"Edit failed for expired estimate: {update_response.text}"
        print(f"PASS: Expired estimate can be edited successfully")


class TestEstimateStatusSummary:
    """Test to verify estimate statuses exist in the system"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@battwheels.in", "password": "DevTest@123"}
        )
        assert response.status_code == 200
        return response.json().get("access_token") or response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_estimates_summary(self, headers):
        """Get summary of all estimate statuses"""
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/summary",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get("summary", {})
        by_status = summary.get("by_status", {})
        
        print("\n=== ESTIMATES SUMMARY BY STATUS ===")
        for status, count in by_status.items():
            print(f"  {status}: {count}")
        print(f"  TOTAL: {summary.get('total', 0)}")
        print(f"  Total Value: ₹{summary.get('total_value', 0):,.2f}")
        print("===================================\n")
        
        assert summary.get("total", 0) > 0, "No estimates found in system"
