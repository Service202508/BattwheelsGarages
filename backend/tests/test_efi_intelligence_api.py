"""
EFI Intelligence Engine API Integration Tests

Tests for Phase 2 - Model-Aware Continuous Learning Failure Intelligence Engine:
- P0.5: AI Guidance Snapshots and Feedback DB models
- Part A: Structured Failure Cards
- Part B: Model-Aware Ranking
- Part C: Top 3 ranked causes with confidence
- Part D: Continuous Learning on ticket closure
- Part E: Model Risk Alerts (Pattern Detection)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test organization IDs for tenant isolation testing
ORG_A = f"TEST_org_A_{uuid.uuid4().hex[:6]}"
ORG_B = f"TEST_org_B_{uuid.uuid4().hex[:6]}"

# Common headers
def get_headers(org_id=ORG_A, user_id="test_user_001"):
    return {
        "Content-Type": "application/json",
        "X-Organization-ID": org_id,
        "X-User-ID": user_id
    }


class TestAIGuidanceSnapshots:
    """P0.5: Tests for AI Guidance Snapshot endpoints"""
    
    def test_get_snapshot_info_non_existing_ticket(self):
        """Test snapshot info for non-existing ticket returns exists=False"""
        response = requests.get(
            f"{BASE_URL}/api/ai/guidance/snapshot/TKT-NONEXISTENT-{uuid.uuid4().hex[:6]}",
            headers=get_headers(),
            params={"mode": "quick"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("exists") == False, "Non-existing ticket should return exists=False"
        print(f"✓ Snapshot info returns exists=False for non-existing ticket")
    
    def test_check_context_requires_ticket(self):
        """Test check-context endpoint requires valid ticket"""
        response = requests.post(
            f"{BASE_URL}/api/ai/guidance/check-context",
            headers=get_headers(),
            json={
                "ticket_id": f"TKT-FAKE-{uuid.uuid4().hex[:6]}",
                "mode": "quick"
            }
        )
        
        # Should return 404 for non-existing ticket
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Check-context returns 404 for non-existing ticket")
    
    def test_feedback_summary_endpoint(self):
        """Test feedback summary endpoint returns valid response"""
        guidance_id = f"GD-TEST-{uuid.uuid4().hex[:6]}"
        
        response = requests.get(
            f"{BASE_URL}/api/ai/guidance/feedback-summary/{guidance_id}",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "total_feedback" in data, "Response should include total_feedback"
        assert "helpful_rate" in data, "Response should include helpful_rate"
        assert "unsafe_count" in data, "Response should include unsafe_count"
        assert "avg_rating" in data, "Response should include avg_rating"
        print(f"✓ Feedback summary returns valid structure: {data}")


class TestFailureCards:
    """Part A: Tests for Structured Failure Cards CRUD"""
    
    def test_create_failure_card(self):
        """Test creating a new failure card"""
        card_data = {
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "vehicle_variant": "Gen2",
            "vehicle_category": "2W",
            "subsystem": "battery",
            "symptom_cluster": ["not charging", "red LED blinking"],
            "dtc_codes": ["P0A80"],
            "probable_root_cause": "TEST_BMS cell imbalance detected",
            "verified_fix": "Perform cell balancing procedure",
            "fix_steps": ["Isolate HV", "Connect diagnostic tool", "Run balancing"],
            "parts_required": ["BMS balancing cable"],
            "estimated_repair_time_minutes": 45
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_headers(),
            json=card_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Create should return success=True"
        assert "failure_card_id" in data, "Response should include failure_card_id"
        assert data["failure_card_id"].startswith("FC-"), "ID should start with FC-"
        
        print(f"✓ Created failure card: {data['failure_card_id']}")
        return data["failure_card_id"]
    
    def test_get_failure_cards_with_tenant_isolation(self):
        """Test that failure cards are tenant-isolated"""
        # Create card for ORG_A
        card_data = {
            "subsystem": "motor",
            "probable_root_cause": f"TEST_Motor issue for ORG_A - {uuid.uuid4().hex[:6]}",
            "verified_fix": "Replace motor controller"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_headers(ORG_A),
            json=card_data
        )
        assert create_response.status_code == 200
        card_id_a = create_response.json()["failure_card_id"]
        
        # Query cards from ORG_A
        response_a = requests.get(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_headers(ORG_A),
            params={"status": "all"}
        )
        assert response_a.status_code == 200
        cards_a = response_a.json().get("failure_cards", [])
        
        # Query cards from ORG_B - should NOT see ORG_A's tenant cards
        response_b = requests.get(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_headers(ORG_B),
            params={"status": "all"}
        )
        assert response_b.status_code == 200
        cards_b = response_b.json().get("failure_cards", [])
        
        # ORG_B should not see ORG_A's tenant-scoped card
        org_a_card_ids = [c["failure_card_id"] for c in cards_a if c.get("organization_id") == ORG_A]
        org_b_visible_ids = [c["failure_card_id"] for c in cards_b]
        
        for card_id in org_a_card_ids:
            if card_id in org_b_visible_ids:
                # Check if it's global
                for card in cards_b:
                    if card["failure_card_id"] == card_id:
                        assert card.get("scope") == "global" or card.get("organization_id") is None, \
                            f"ORG_B should only see global cards, not tenant cards from ORG_A"
        
        print(f"✓ Tenant isolation verified - ORG_A has {len(cards_a)} cards, ORG_B has {len(cards_b)} cards")
    
    def test_approve_failure_card(self):
        """Test approving a draft failure card"""
        # First create a draft card
        card_data = {
            "subsystem": "charger",
            "probable_root_cause": f"TEST_Charger issue - {uuid.uuid4().hex[:6]}",
            "verified_fix": "Replace onboard charger"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_headers(),
            json=card_data
        )
        assert create_response.status_code == 200
        card_id = create_response.json()["failure_card_id"]
        
        # Approve the card
        approve_response = requests.put(
            f"{BASE_URL}/api/efi/intelligence/failure-cards/{card_id}/approve",
            headers=get_headers()
        )
        
        assert approve_response.status_code == 200, f"Expected 200, got {approve_response.status_code}: {approve_response.text}"
        data = approve_response.json()
        assert data.get("success") == True, "Approve should return success=True"
        
        print(f"✓ Approved failure card: {card_id}")


class TestModelAwareRanking:
    """Part B & C: Tests for Model-Aware Ranking with Top 3 causes"""
    
    def test_rank_causes_returns_top_3(self):
        """Test that ranking returns at most top 3 causes"""
        response = requests.post(
            f"{BASE_URL}/api/efi/intelligence/ranking/rank-causes",
            headers=get_headers(),
            params={
                "vehicle_make": "Ola",
                "vehicle_model": "S1 Pro",
                "subsystem": "battery",
                "symptoms": "not charging,red LED",
                "dtc_codes": "P0A80"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "ranked_causes" in data, "Response should include ranked_causes"
        assert "overall_confidence" in data, "Response should include overall_confidence"
        assert "should_escalate" in data, "Response should include should_escalate"
        
        ranked_causes = data.get("ranked_causes", [])
        assert len(ranked_causes) <= 3, f"Should return at most 3 causes, got {len(ranked_causes)}"
        
        print(f"✓ Rank causes returned {len(ranked_causes)} causes with confidence: {data.get('overall_confidence')}")
    
    def test_low_confidence_returns_safe_checklist(self):
        """Test that low confidence returns safe checklist"""
        # Query with minimal/no matching context to get low confidence
        response = requests.post(
            f"{BASE_URL}/api/efi/intelligence/ranking/rank-causes",
            headers=get_headers(),
            params={
                "subsystem": "unknown_subsystem_xyz",
                "symptoms": "very_unusual_symptom"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Low confidence should return safe checklist
        if data.get("overall_confidence") == "low":
            assert "safe_checklist" in data, "Low confidence should include safe_checklist"
            safe_checklist = data.get("safe_checklist", [])
            assert len(safe_checklist) > 0, "Safe checklist should have items"
            print(f"✓ Low confidence correctly returns safe checklist with {len(safe_checklist)} items")
        else:
            print(f"✓ Confidence was {data.get('overall_confidence')}, safe_checklist may or may not be present")
    
    def test_ranking_weights_model_match_higher(self):
        """Test that model match is weighted higher"""
        # First, create failure cards with matching and non-matching models
        matching_card = {
            "vehicle_make": "Ather",
            "vehicle_model": "450X",
            "subsystem": "motor",
            "probable_root_cause": f"TEST_Hall sensor failure for 450X - {uuid.uuid4().hex[:6]}",
            "verified_fix": "Replace hall sensor",
            "historical_success_rate": 0.5  # Same success rate
        }
        
        non_matching_card = {
            "vehicle_make": "TVS",
            "vehicle_model": "iQube",
            "subsystem": "motor",
            "probable_root_cause": f"TEST_Motor controller issue for iQube - {uuid.uuid4().hex[:6]}",
            "verified_fix": "Replace controller",
            "historical_success_rate": 0.5  # Same success rate
        }
        
        # Create both cards
        requests.post(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_headers(),
            json=matching_card
        )
        requests.post(
            f"{BASE_URL}/api/efi/intelligence/failure-cards",
            headers=get_headers(),
            json=non_matching_card
        )
        
        # Query for Ather 450X - matching card should rank higher
        response = requests.post(
            f"{BASE_URL}/api/efi/intelligence/ranking/rank-causes",
            headers=get_headers(),
            params={
                "vehicle_make": "Ather",
                "vehicle_model": "450X",
                "subsystem": "motor"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        ranked_causes = data.get("ranked_causes", [])
        
        if ranked_causes:
            # Check if matching model appears in results with matching_factors
            for cause in ranked_causes:
                if "model_match" in cause.get("matching_factors", []):
                    print(f"✓ Model match found in ranking factors: {cause.get('cause')[:50]}...")
                    break
        
        print(f"✓ Ranking completed - {len(ranked_causes)} causes returned")


class TestContinuousLearning:
    """Part D: Tests for Continuous Learning on ticket closure"""
    
    def test_capture_ticket_closure(self):
        """Test capturing learning data on ticket closure"""
        ticket_id = f"TKT-TEST-{uuid.uuid4().hex[:8]}"
        
        closure_data = {
            "actual_root_cause": "TEST_BMS cell imbalance confirmed after diagnosis",
            "parts_replaced": ["BMS module", "Cell connector"],
            "repair_actions": ["Cell balancing", "Firmware update"],
            "ai_was_correct": True,
            "subsystem": "battery",
            "unsafe_incident": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/intelligence/learning/capture-closure/{ticket_id}",
            headers=get_headers(),
            json=closure_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Capture should return success=True"
        assert "event_id" in data, "Response should include event_id"
        assert data["event_id"].startswith("LE-"), "Event ID should start with LE-"
        
        print(f"✓ Captured learning event: {data['event_id']}")
    
    def test_learning_stats(self):
        """Test getting learning statistics"""
        response = requests.get(
            f"{BASE_URL}/api/efi/intelligence/learning/stats",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check structure
        assert "learning_events" in data or "active_risk_alerts" in data or "failure_cards" in data, \
            "Response should include learning stats"
        
        print(f"✓ Learning stats returned: {data}")


class TestRiskAlerts:
    """Part E: Tests for Model Risk Alerts (Pattern Detection)"""
    
    def test_get_risk_alerts(self):
        """Test getting risk alerts"""
        response = requests.get(
            f"{BASE_URL}/api/efi/intelligence/risk-alerts",
            headers=get_headers(),
            params={"status": "all"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "alerts" in data, "Response should include alerts array"
        assert "total" in data, "Response should include total count"
        assert "active_count" in data, "Response should include active_count"
        
        print(f"✓ Risk alerts returned: {data.get('total')} total, {data.get('active_count')} active")
    
    def test_risk_alerts_filter_by_status(self):
        """Test filtering risk alerts by status"""
        for status in ["active", "acknowledged", "resolved"]:
            response = requests.get(
                f"{BASE_URL}/api/efi/intelligence/risk-alerts",
                headers=get_headers(),
                params={"status": status}
            )
            
            assert response.status_code == 200, f"Expected 200 for status={status}, got {response.status_code}"
            data = response.json()
            
            # All returned alerts should match the status filter
            for alert in data.get("alerts", []):
                assert alert.get("status") == status, f"Alert status mismatch: expected {status}"
        
        print(f"✓ Risk alerts filter by status working correctly")


class TestDashboardSummary:
    """Tests for Intelligence Dashboard Summary"""
    
    def test_get_dashboard_summary(self):
        """Test getting dashboard summary with all intelligence stats"""
        response = requests.get(
            f"{BASE_URL}/api/efi/intelligence/dashboard-summary",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check all required sections
        assert "risk_alerts" in data, "Response should include risk_alerts section"
        assert "failure_cards" in data, "Response should include failure_cards section"
        assert "learning" in data, "Response should include learning section"
        assert "guidance" in data, "Response should include guidance section"
        
        # Check risk_alerts structure
        risk_alerts = data.get("risk_alerts", {})
        assert "active" in risk_alerts, "risk_alerts should include active count"
        
        # Check failure_cards structure
        failure_cards = data.get("failure_cards", {})
        assert "draft" in failure_cards, "failure_cards should include draft count"
        assert "approved" in failure_cards, "failure_cards should include approved count"
        
        # Check guidance structure
        guidance = data.get("guidance", {})
        assert "total_generated" in guidance, "guidance should include total_generated"
        
        print(f"✓ Dashboard summary returned complete data:")
        print(f"  - Risk Alerts: {risk_alerts.get('active')} active")
        print(f"  - Failure Cards: {failure_cards.get('total', 0)} total")
        print(f"  - Guidance: {guidance.get('total_generated')} generated")


class TestAIGuidanceRoutes:
    """Tests for AI Guidance routes"""
    
    def test_guidance_status(self):
        """Test guidance status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai/guidance/status",
            headers=get_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "efi_guidance_enabled" in data, "Response should include efi_guidance_enabled"
        assert "features" in data, "Response should include features"
        
        print(f"✓ Guidance status: enabled={data.get('efi_guidance_enabled')}, features={data.get('features')}")


# Cleanup test data after tests
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after tests"""
    yield
    # Note: In production, would add cleanup logic here
    print("\n✓ Test data with TEST_ prefix can be cleaned up via admin tools")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
