"""
EFI Guided Execution API Tests
Tests for EV Failure Intelligence diagnostic system
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://audit-fixes-5.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "test_pwd_placeholder"
TECH_EMAIL = "deepak@battwheelsgarages.in"
TECH_PASSWORD = "tech123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def tech_token():
    """Get technician authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TECH_EMAIL, "password": TECH_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Technician authentication failed")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin request headers"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def tech_headers(tech_token):
    """Technician request headers"""
    return {
        "Authorization": f"Bearer {tech_token}",
        "Content-Type": "application/json"
    }


class TestEFISeedData:
    """Test EFI seed data endpoint"""
    
    def test_seed_failure_cards(self, admin_headers):
        """Test seeding failure cards and decision trees"""
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/seed",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_cards" in data
        assert data["total_cards"] >= 14  # Should have at least 14 cards


class TestEFIEmbeddings:
    """Test EFI embedding generation"""
    
    def test_generate_all_embeddings(self, admin_headers):
        """Test generating embeddings for all failure cards"""
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/embeddings/generate-all",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "success" in data
        assert data["failed"] == 0
    
    def test_embedding_status(self, tech_headers):
        """Test embedding status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/embeddings/status",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_cards" in data
        assert "cards_with_embeddings" in data
        assert "coverage_percent" in data


class TestEFIFailureCards:
    """Test failure cards listing and retrieval"""
    
    def test_list_failure_cards(self, tech_headers):
        """Test listing all failure cards"""
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/failure-cards",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert "total" in data
        assert len(data["cards"]) > 0
    
    def test_list_failure_cards_by_subsystem(self, tech_headers):
        """Test filtering failure cards by subsystem"""
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/failure-cards?subsystem=battery",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        # All returned cards should be battery subsystem
        for card in data["cards"]:
            assert card.get("subsystem_category") == "battery"
    
    def test_get_single_failure_card(self, tech_headers):
        """Test getting a single failure card with decision tree"""
        # First get list to find a card ID
        list_response = requests.get(
            f"{BASE_URL}/api/efi-guided/failure-cards?limit=1",
            headers=tech_headers
        )
        assert list_response.status_code == 200
        cards = list_response.json()["cards"]
        if not cards:
            pytest.skip("No failure cards available")
        
        failure_id = cards[0]["failure_id"]
        
        # Get single card
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/failure-cards/{failure_id}",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["failure_id"] == failure_id
        assert "title" in data
        assert "subsystem_category" in data


class TestEFISuggestions:
    """Test EFI suggestions endpoint"""
    
    @pytest.fixture
    def test_ticket_id(self, admin_headers):
        """Get or create a test ticket"""
        # Get existing tickets
        response = requests.get(
            f"{BASE_URL}/api/tickets?limit=5",
            headers=admin_headers
        )
        if response.status_code == 200:
            tickets = response.json().get("tickets", [])
            if tickets:
                return tickets[0]["ticket_id"]
        pytest.skip("No tickets available for testing")
    
    def test_get_suggestions_for_ticket(self, tech_headers, test_ticket_id):
        """Test getting EFI suggestions for a ticket"""
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/suggestions/{test_ticket_id}",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == test_ticket_id
        assert "suggested_paths" in data
        assert "classified_subsystem" in data
        assert "has_active_session" in data
    
    def test_suggestions_include_confidence_scores(self, tech_headers, test_ticket_id):
        """Test that suggestions include confidence scores"""
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/suggestions/{test_ticket_id}",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for path in data.get("suggested_paths", []):
            assert "similarity_score" in path
            assert "confidence_level" in path
            assert path["confidence_level"] in ["high", "medium", "low"]


class TestEFIDiagnosticSession:
    """Test EFI diagnostic session workflow"""
    
    @pytest.fixture
    def test_ticket_id(self, admin_headers):
        """Get or create a test ticket"""
        response = requests.get(
            f"{BASE_URL}/api/tickets?limit=5",
            headers=admin_headers
        )
        if response.status_code == 200:
            tickets = response.json().get("tickets", [])
            if tickets:
                return tickets[0]["ticket_id"]
        pytest.skip("No tickets available for testing")
    
    @pytest.fixture
    def failure_card_with_tree(self, tech_headers):
        """Get a failure card that has a decision tree"""
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/failure-cards",
            headers=tech_headers
        )
        if response.status_code == 200:
            cards = response.json().get("cards", [])
            # Find cards with decision trees (seeded cards have them)
            for card in cards:
                if card.get("source_type") == "seeded":
                    return card["failure_id"]
        pytest.skip("No failure cards with decision trees available")
    
    def test_start_diagnostic_session(self, tech_headers, test_ticket_id, failure_card_with_tree):
        """Test starting a diagnostic session"""
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/session/start",
            headers=tech_headers,
            json={
                "ticket_id": test_ticket_id,
                "failure_card_id": failure_card_with_tree
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["ticket_id"] == test_ticket_id
        assert data["failure_card_id"] == failure_card_with_tree
        assert data["status"] == "active"
        assert "current_step" in data
        assert "tree" in data
        
        return data["session_id"]
    
    def test_session_without_decision_tree_fails(self, tech_headers, test_ticket_id):
        """Test that starting session without decision tree fails"""
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/session/start",
            headers=tech_headers,
            json={
                "ticket_id": test_ticket_id,
                "failure_card_id": "nonexistent_card"
            }
        )
        assert response.status_code == 400
    
    def test_get_session(self, tech_headers, test_ticket_id, failure_card_with_tree):
        """Test getting session details"""
        # Start a session first
        start_response = requests.post(
            f"{BASE_URL}/api/efi-guided/session/start",
            headers=tech_headers,
            json={
                "ticket_id": test_ticket_id,
                "failure_card_id": failure_card_with_tree
            }
        )
        if start_response.status_code != 200:
            pytest.skip("Could not start session")
        
        session_id = start_response.json()["session_id"]
        
        # Get session
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/session/{session_id}",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "current_step" in data
        assert "tree" in data


class TestEFIStepRecording:
    """Test recording PASS/FAIL outcomes for diagnostic steps"""
    
    @pytest.fixture
    def active_session(self, tech_headers, admin_headers):
        """Create an active session for testing"""
        # Get a ticket
        tickets_response = requests.get(
            f"{BASE_URL}/api/tickets?limit=5",
            headers=admin_headers
        )
        if tickets_response.status_code != 200:
            pytest.skip("Could not get tickets")
        
        tickets = tickets_response.json().get("tickets", [])
        if not tickets:
            pytest.skip("No tickets available")
        
        ticket_id = tickets[0]["ticket_id"]
        
        # Get a failure card with decision tree
        cards_response = requests.get(
            f"{BASE_URL}/api/efi-guided/failure-cards",
            headers=tech_headers
        )
        if cards_response.status_code != 200:
            pytest.skip("Could not get failure cards")
        
        cards = cards_response.json().get("cards", [])
        failure_card_id = None
        for card in cards:
            if card.get("source_type") == "seeded":
                failure_card_id = card["failure_id"]
                break
        
        if not failure_card_id:
            pytest.skip("No failure cards with decision trees")
        
        # Start session
        start_response = requests.post(
            f"{BASE_URL}/api/efi-guided/session/start",
            headers=tech_headers,
            json={
                "ticket_id": ticket_id,
                "failure_card_id": failure_card_id
            }
        )
        if start_response.status_code != 200:
            pytest.skip("Could not start session")
        
        return start_response.json()
    
    def test_record_pass_outcome(self, tech_headers, active_session):
        """Test recording PASS outcome for a step"""
        session_id = active_session["session_id"]
        current_step_id = active_session["current_step"]["step_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/session/{session_id}/step/{current_step_id}",
            headers=tech_headers,
            json={
                "outcome": "pass",
                "notes": "Test pass outcome"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["outcome_recorded"] == True
        assert "action" in data
    
    def test_record_fail_outcome(self, tech_headers, active_session):
        """Test recording FAIL outcome for a step"""
        session_id = active_session["session_id"]
        current_step_id = active_session["current_step"]["step_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/session/{session_id}/step/{current_step_id}",
            headers=tech_headers,
            json={
                "outcome": "fail",
                "notes": "Test fail outcome"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["outcome_recorded"] == True
        assert "action" in data


class TestEFISmartEstimate:
    """Test smart estimate generation from completed sessions"""
    
    def test_estimate_requires_completed_session(self, tech_headers):
        """Test that estimate endpoint requires completed session"""
        # Try to get estimate for non-existent session
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/session/nonexistent/estimate",
            headers=tech_headers
        )
        assert response.status_code == 404


class TestEFIDecisionTrees:
    """Test decision tree management"""
    
    def test_get_decision_tree(self, tech_headers):
        """Test getting decision tree for a failure card"""
        # Get a failure card with decision tree
        cards_response = requests.get(
            f"{BASE_URL}/api/efi-guided/failure-cards",
            headers=tech_headers
        )
        if cards_response.status_code != 200:
            pytest.skip("Could not get failure cards")
        
        cards = cards_response.json().get("cards", [])
        failure_card_id = None
        for card in cards:
            if card.get("source_type") == "seeded":
                failure_card_id = card["failure_id"]
                break
        
        if not failure_card_id:
            pytest.skip("No failure cards with decision trees")
        
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/trees/{failure_card_id}",
            headers=tech_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "tree_id" in data
        assert "steps" in data
        assert "resolutions" in data
        assert len(data["steps"]) > 0
        assert len(data["resolutions"]) > 0


class TestEFIAuthentication:
    """Test authentication requirements for EFI endpoints"""
    
    def test_suggestions_requires_auth(self):
        """Test that suggestions endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/efi-guided/suggestions/test_ticket"
        )
        assert response.status_code == 401
    
    def test_session_start_requires_auth(self):
        """Test that session start requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/session/start",
            json={"ticket_id": "test", "failure_card_id": "test"}
        )
        assert response.status_code == 401
    
    def test_seed_requires_admin(self, tech_headers):
        """Test that seed endpoint requires admin role"""
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/seed",
            headers=tech_headers
        )
        assert response.status_code == 403
    
    def test_embeddings_generate_requires_admin(self, tech_headers):
        """Test that embeddings generation requires admin role"""
        response = requests.post(
            f"{BASE_URL}/api/efi-guided/embeddings/generate-all",
            headers=tech_headers
        )
        assert response.status_code == 403
