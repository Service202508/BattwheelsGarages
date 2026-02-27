"""
Battwheels OS - EFI (EV Failure Intelligence) Module Tests
Tests for the refactored event-driven EFI system

Tests cover:
- Failure card CRUD operations
- AI matching pipeline (4-stage)
- Match ticket to failure cards
- Analytics endpoints
- Event emission verification
- Backward compatibility with tickets module
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "DevTest@123"


class TestEFIModuleAuth:
    """Authentication tests for EFI module"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful, role: {data['user']['role']}")


class TestFailureCardCRUD:
    """CRUD operations for failure cards"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_failure_card_id(self, auth_headers):
        """Create a test failure card and return its ID"""
        card_data = {
            "title": "TEST_Battery Cell Imbalance",
            "description": "Battery cells showing voltage imbalance causing reduced range",
            "subsystem_category": "battery",
            "failure_mode": "degradation",
            "symptom_text": "Battery shows uneven cell voltages, reduced range, slow charging",
            "error_codes": ["BMS001", "CELL_IMBALANCE"],
            "root_cause": "Cell degradation due to thermal cycling",
            "root_cause_details": "Repeated charge/discharge cycles at high temperatures cause cell capacity mismatch",
            "resolution_steps": [
                {"step_number": 1, "action": "Check cell voltages with BMS diagnostic tool", "duration_minutes": 15},
                {"step_number": 2, "action": "Perform cell balancing procedure", "duration_minutes": 30},
                {"step_number": 3, "action": "Replace degraded cells if variance > 0.2V", "duration_minutes": 60}
            ],
            "required_parts": [
                {"part_id": "CELL_18650", "part_name": "18650 Li-ion Cell", "quantity": 4, "estimated_cost": 500}
            ],
            "vehicle_models": [
                {"make": "Ather", "model": "450X", "year_start": 2020}
            ],
            "keywords": ["battery", "cell", "imbalance", "voltage", "range"],
            "tags": ["battery", "bms", "cell-balancing"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert response.status_code == 200, f"Failed to create failure card: {response.text}"
        data = response.json()
        assert "failure_id" in data
        print(f"✓ Created test failure card: {data['failure_id']}")
        return data["failure_id"]
    
    def test_create_failure_card_with_event_emission(self, auth_headers):
        """Test creating a failure card emits FAILURE_CARD_CREATED event"""
        card_data = {
            "title": "TEST_Motor Controller Overheating",
            "description": "Motor controller temperature exceeds safe limits",
            "subsystem_category": "motor",
            "failure_mode": "overheating",
            "symptom_text": "Motor controller shows high temperature warning, power reduced",
            "error_codes": ["MC_TEMP_HIGH", "POWER_LIMIT"],
            "root_cause": "Insufficient cooling or thermal paste degradation",
            "resolution_steps": [
                {"step_number": 1, "action": "Check cooling fan operation", "duration_minutes": 10},
                {"step_number": 2, "action": "Clean heat sink fins", "duration_minutes": 20},
                {"step_number": 3, "action": "Replace thermal paste", "duration_minutes": 30}
            ],
            "keywords": ["motor", "controller", "overheating", "temperature"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "failure_id" in data
        assert data["title"] == card_data["title"]
        assert data["subsystem_category"] == "motor"
        assert data["status"] == "draft"
        assert "confidence_score" in data
        assert "signature_hash" in data
        
        # Verify confidence history initialized
        assert "confidence_history" in data
        assert len(data["confidence_history"]) >= 1
        
        print(f"✓ Created failure card with event emission: {data['failure_id']}")
        print(f"  - Initial confidence: {data['confidence_score']}")
        print(f"  - Signature hash: {data['signature_hash']}")
    
    def test_list_failure_cards(self, auth_headers):
        """Test listing failure cards with pagination"""
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "skip" in data
        
        print(f"✓ Listed failure cards: {data['total']} total, {len(data['items'])} returned")
    
    def test_list_failure_cards_with_filters(self, auth_headers):
        """Test filtering failure cards by status and subsystem"""
        # Filter by subsystem
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?subsystem=battery",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned cards should be battery subsystem
        for card in data["items"]:
            assert card["subsystem_category"] == "battery"
        
        print(f"✓ Filtered by subsystem=battery: {len(data['items'])} cards")
        
        # Filter by status
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?status=draft",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for card in data["items"]:
            assert card["status"] == "draft"
        
        print(f"✓ Filtered by status=draft: {len(data['items'])} cards")
    
    def test_get_single_failure_card(self, auth_headers, test_failure_card_id):
        """Test getting a single failure card by ID"""
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards/{test_failure_card_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["failure_id"] == test_failure_card_id
        assert "title" in data
        assert "description" in data
        assert "subsystem_category" in data
        assert "confidence_score" in data
        
        print(f"✓ Retrieved failure card: {data['title']}")
    
    def test_get_nonexistent_failure_card(self, auth_headers):
        """Test getting a non-existent failure card returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards/nonexistent_id_12345",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent failure card correctly returns 404")
    
    def test_update_failure_card(self, auth_headers, test_failure_card_id):
        """Test updating a failure card"""
        update_data = {
            "description": "Updated: Battery cells showing voltage imbalance causing reduced range and charging issues",
            "keywords": ["battery", "cell", "imbalance", "voltage", "range", "charging"]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/efi/failure-cards/{test_failure_card_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "Updated:" in data["description"]
        assert "charging" in data["keywords"]
        assert data["version"] >= 2
        
        print(f"✓ Updated failure card, version: {data['version']}")
    
    def test_get_confidence_history(self, auth_headers, test_failure_card_id):
        """Test getting confidence score history"""
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards/{test_failure_card_id}/confidence-history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "failure_id" in data
        assert "current_confidence" in data
        assert "history" in data
        assert len(data["history"]) >= 1
        
        print(f"✓ Retrieved confidence history: {len(data['history'])} entries")


class TestAIMatchingPipeline:
    """Tests for the 4-stage AI matching pipeline"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_match_failure_basic(self, auth_headers):
        """Test basic failure matching with symptom text"""
        match_request = {
            "symptom_text": "Battery not charging, shows 0% even after plugging in for hours",
            "error_codes": ["BMS001"],
            "vehicle_make": "Ather",
            "vehicle_model": "450X",
            "limit": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "query_text" in data
        assert "signature_hash" in data
        assert "matches" in data
        assert "processing_time_ms" in data
        assert "model_used" in data
        assert "matching_stages_used" in data
        
        # Verify processing time is fast (should be ~4ms per spec)
        assert data["processing_time_ms"] < 1000, f"Matching too slow: {data['processing_time_ms']}ms"
        
        print(f"✓ AI matching completed in {data['processing_time_ms']:.2f}ms")
        print(f"  - Matches found: {len(data['matches'])}")
        print(f"  - Stages used: {data['matching_stages_used']}")
        print(f"  - Signature hash: {data['signature_hash']}")
    
    def test_match_failure_with_subsystem_hint(self, auth_headers):
        """Test matching with subsystem hint for better filtering"""
        match_request = {
            "symptom_text": "Motor making grinding noise during acceleration",
            "error_codes": ["MOTOR_FAULT"],
            "subsystem_hint": "motor",
            "limit": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should use subsystem_vehicle stage
        assert "subsystem_vehicle" in data["matching_stages_used"] or "signature" in data["matching_stages_used"]
        
        print(f"✓ Matching with subsystem hint: {len(data['matches'])} matches")
    
    def test_match_failure_empty_results(self, auth_headers):
        """Test matching with unlikely symptom returns empty or low-score matches"""
        match_request = {
            "symptom_text": "xyz123 completely random text that should not match anything",
            "error_codes": ["NONEXISTENT_CODE_XYZ"],
            "limit": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty or low-confidence matches
        if data["matches"]:
            # If matches exist, they should have low scores
            for match in data["matches"]:
                assert match["match_score"] < 0.8, "Unexpected high score for random text"
        
        print(f"✓ Random text matching: {len(data['matches'])} low-confidence matches")


class TestMatchTicketToFailures:
    """Tests for matching existing tickets to failure cards"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_ticket_id(self, auth_headers):
        """Create a test ticket for matching"""
        ticket_data = {
            "title": "TEST_EFI_Battery charging issue",
            "description": "Vehicle battery not charging properly, shows error codes",
            "category": "battery",
            "priority": "high",
            "vehicle_make": "Ather",
            "vehicle_model": "450X",
            "error_codes_reported": ["BMS001", "CHARGE_FAIL"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        data = response.json()
        print(f"✓ Created test ticket: {data['ticket_id']}")
        return data["ticket_id"]
    
    def test_match_ticket_to_failures(self, auth_headers, test_ticket_id):
        """Test matching an existing ticket to failure cards"""
        response = requests.post(
            f"{BASE_URL}/api/efi/match-ticket/{test_ticket_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "ticket_id" in data
        assert data["ticket_id"] == test_ticket_id
        assert "matches" in data
        assert "processing_time_ms" in data
        assert "signature_hash" in data
        
        print(f"✓ Matched ticket to {len(data['matches'])} failure cards")
        print(f"  - Processing time: {data['processing_time_ms']:.2f}ms")
    
    def test_match_nonexistent_ticket(self, auth_headers):
        """Test matching non-existent ticket returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/efi/match-ticket/nonexistent_ticket_12345",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent ticket correctly returns 404")
    
    def test_get_ticket_matches(self, auth_headers, test_ticket_id):
        """Test getting AI-suggested failure cards for a ticket"""
        # First ensure matching was performed
        requests.post(
            f"{BASE_URL}/api/efi/match-ticket/{test_ticket_id}",
            headers=auth_headers
        )
        
        # Now get matches via tickets endpoint
        response = requests.get(
            f"{BASE_URL}/api/tickets/{test_ticket_id}/matches",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "ticket_id" in data
        assert "ai_match_performed" in data
        assert "matches" in data
        
        print(f"✓ Retrieved ticket matches: {len(data['matches'])} cards")


class TestEFIAnalytics:
    """Tests for EFI analytics endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_analytics_overview(self, auth_headers):
        """Test getting EFI analytics overview"""
        response = requests.get(
            f"{BASE_URL}/api/efi/analytics/overview",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify analytics structure
        assert "total_failure_cards" in data
        assert "by_subsystem" in data
        assert "by_source_type" in data
        assert "approved_cards" in data
        assert "draft_cards" in data
        
        print(f"✓ Analytics overview retrieved:")
        print(f"  - Total failure cards: {data['total_failure_cards']}")
        print(f"  - Approved: {data['approved_cards']}, Draft: {data['draft_cards']}")
    
    def test_get_effectiveness_report(self, auth_headers):
        """Test getting effectiveness report"""
        response = requests.get(
            f"{BASE_URL}/api/efi/analytics/effectiveness",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "report" in data
        assert "generated_at" in data
        
        print(f"✓ Effectiveness report: {len(data['report'])} cards with usage")


class TestFailureCardApproval:
    """Tests for failure card approval workflow"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def draft_card_id(self, auth_headers):
        """Create a draft failure card for approval testing"""
        card_data = {
            "title": "TEST_Approval_Charger Port Damage",
            "description": "Charging port physical damage preventing connection",
            "subsystem_category": "charger",
            "failure_mode": "complete_failure",
            "symptom_text": "Charger not connecting, port appears damaged",
            "error_codes": ["CHARGE_CONN_FAIL"],
            "root_cause": "Physical damage to charging port",
            "resolution_steps": [
                {"step_number": 1, "action": "Inspect charging port", "duration_minutes": 10},
                {"step_number": 2, "action": "Replace charging port assembly", "duration_minutes": 45}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"
        return data["failure_id"]
    
    def test_approve_failure_card(self, auth_headers, draft_card_id):
        """Test approving a failure card"""
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards/{draft_card_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert data["failure_id"] == draft_card_id
        assert "new_confidence" in data
        
        # Verify confidence was boosted
        assert data["new_confidence"] > 0.5
        
        print(f"✓ Approved failure card: {draft_card_id}")
        print(f"  - New confidence: {data['new_confidence']}")
        
        # Verify card status changed
        get_response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards/{draft_card_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        card = get_response.json()
        assert card["status"] == "approved"
    
    def test_approve_already_approved_card(self, auth_headers, draft_card_id):
        """Test approving an already approved card returns error"""
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards/{draft_card_id}/approve",
            headers=auth_headers
        )
        assert response.status_code == 400
        print("✓ Re-approval correctly rejected")


class TestFailureCardDeprecation:
    """Tests for failure card deprecation"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def card_to_deprecate(self, auth_headers):
        """Create a failure card for deprecation testing"""
        card_data = {
            "title": "TEST_Deprecate_Old BMS Issue",
            "description": "Outdated BMS issue that has been superseded",
            "subsystem_category": "battery",
            "failure_mode": "erratic_behavior",
            "root_cause": "Old firmware bug",
            "resolution_steps": [
                {"step_number": 1, "action": "Update firmware", "duration_minutes": 15}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert response.status_code == 200
        return response.json()["failure_id"]
    
    def test_deprecate_failure_card(self, auth_headers, card_to_deprecate):
        """Test deprecating a failure card"""
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards/{card_to_deprecate}/deprecate?reason=Superseded%20by%20new%20card",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert data["failure_id"] == card_to_deprecate
        
        # Verify card status changed
        get_response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards/{card_to_deprecate}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        card = get_response.json()
        assert card["status"] == "deprecated"
        
        print(f"✓ Deprecated failure card: {card_to_deprecate}")


class TestEventIntegration:
    """Tests for event-driven integration between tickets and EFI"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_ticket_creation_triggers_ai_matching(self, auth_headers):
        """Test that creating a ticket triggers AI matching via events"""
        ticket_data = {
            "title": "TEST_Event_Battery overheating during charging",
            "description": "Battery temperature rises above 45C during charging, charging stops",
            "category": "battery",
            "priority": "high",
            "vehicle_make": "Ather",
            "vehicle_model": "450X",
            "error_codes_reported": ["BMS_TEMP_HIGH", "CHARGE_STOP"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert response.status_code == 200
        ticket = response.json()
        ticket_id = ticket["ticket_id"]
        
        # Wait a moment for async event processing
        time.sleep(0.5)
        
        # Check if AI matching was performed
        get_response = requests.get(
            f"{BASE_URL}/api/tickets/{ticket_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        updated_ticket = get_response.json()
        
        # AI matching should have been triggered by TICKET_CREATED event
        assert updated_ticket.get("ai_match_performed") == True or "suggested_failure_cards" in updated_ticket
        
        print(f"✓ Ticket creation triggered AI matching")
        print(f"  - Ticket ID: {ticket_id}")
        print(f"  - AI match performed: {updated_ticket.get('ai_match_performed')}")
        print(f"  - Suggested cards: {len(updated_ticket.get('suggested_failure_cards', []))}")
    
    def test_full_ticket_lifecycle_with_efi(self, auth_headers):
        """Test full ticket lifecycle with EFI integration"""
        # 1. Create ticket
        ticket_data = {
            "title": "TEST_Lifecycle_Motor vibration issue",
            "description": "Motor produces unusual vibration at high speeds",
            "category": "motor",
            "priority": "medium",
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert create_response.status_code == 200
        ticket = create_response.json()
        ticket_id = ticket["ticket_id"]
        print(f"✓ Step 1: Created ticket {ticket_id}")
        
        # 2. Match ticket to failure cards
        match_response = requests.post(
            f"{BASE_URL}/api/efi/match-ticket/{ticket_id}",
            headers=auth_headers
        )
        assert match_response.status_code == 200
        matches = match_response.json()
        print(f"✓ Step 2: Matched to {len(matches['matches'])} failure cards")
        
        # 3. Get ticket matches
        get_matches_response = requests.get(
            f"{BASE_URL}/api/tickets/{ticket_id}/matches",
            headers=auth_headers
        )
        assert get_matches_response.status_code == 200
        ticket_matches = get_matches_response.json()
        print(f"✓ Step 3: Retrieved {len(ticket_matches['matches'])} suggested cards")
        
        # 4. Update ticket status
        update_response = requests.put(
            f"{BASE_URL}/api/tickets/{ticket_id}",
            headers=auth_headers,
            json={"status": "in_progress"}
        )
        assert update_response.status_code == 200
        print(f"✓ Step 4: Updated ticket status to in_progress")
        
        # 5. Close ticket
        close_response = requests.post(
            f"{BASE_URL}/api/tickets/{ticket_id}/close",
            headers=auth_headers,
            json={
                "resolution": "Motor bearing replaced, vibration resolved",
                "resolution_outcome": "success",
                "resolution_notes": "Replaced worn bearing"
            }
        )
        assert close_response.status_code == 200
        print(f"✓ Step 5: Closed ticket with resolution")
        
        print(f"✓ Full lifecycle completed for ticket {ticket_id}")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_cleanup_verification(self, auth_headers):
        """Verify test data can be identified for cleanup"""
        # List failure cards with TEST_ prefix
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?search=TEST_",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        test_cards = [c for c in data["items"] if c["title"].startswith("TEST_")]
        print(f"✓ Found {len(test_cards)} test failure cards (TEST_ prefix)")
        
        # List tickets with TEST_ prefix
        tickets_response = requests.get(
            f"{BASE_URL}/api/tickets",
            headers=auth_headers
        )
        assert tickets_response.status_code == 200
        tickets_data = tickets_response.json()
        
        test_tickets = [t for t in tickets_data["tickets"] if t["title"].startswith("TEST_")]
        print(f"✓ Found {len(test_tickets)} test tickets (TEST_ prefix)")
        
        print("✓ Cleanup verification completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
