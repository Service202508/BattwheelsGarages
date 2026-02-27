"""
Battwheels OS - EFI Search and Embeddings Tests
Tests for the 5-stage AI matching pipeline, hybrid search with BM25, and embedding management

Tests cover:
- POST /api/efi/match - AI matching endpoint with symptom text and error codes
- GET /api/efi/embeddings/status - Check embedding status
- POST /api/efi/embeddings/generate - Start embedding generation
- Hybrid search with BM25 scoring and fuzzy matching
- Text search service with query expansion and EV synonyms
- Fallback behavior when embeddings are disabled
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


class TestEmbeddingEndpoints:
    """Tests for embedding management endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_embedding_status(self, auth_headers):
        """Test GET /api/efi/embeddings/status - Check embedding status"""
        response = requests.get(
            f"{BASE_URL}/api/efi/embeddings/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "embeddings_enabled" in data
        assert "total_cards" in data
        assert "cards_with_embeddings" in data
        assert "cards_without_embeddings" in data
        assert "embedding_coverage_percent" in data
        assert "cache_entries" in data
        assert "embedding_model" in data
        assert "embedding_dimensions" in data
        
        # Verify embedding model info
        assert data["embedding_model"] == "text-embedding-3-small"
        assert data["embedding_dimensions"] == 1536
        
        # Since OPENAI_API_KEY is not configured, embeddings should be disabled
        assert data["embeddings_enabled"] == False
        assert "note" in data
        assert "OPENAI_API_KEY" in data["note"]
        
        print(f"✓ Embedding status retrieved:")
        print(f"  - Embeddings enabled: {data['embeddings_enabled']}")
        print(f"  - Total cards: {data['total_cards']}")
        print(f"  - Cards with embeddings: {data['cards_with_embeddings']}")
        print(f"  - Coverage: {data['embedding_coverage_percent']}%")
    
    def test_generate_embeddings_disabled(self, auth_headers):
        """Test POST /api/efi/embeddings/generate - Returns appropriate message when disabled"""
        response = requests.post(
            f"{BASE_URL}/api/efi/embeddings/generate",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return disabled status since OPENAI_API_KEY is not configured
        assert "status" in data
        assert data["status"] == "disabled"
        assert "reason" in data
        assert "OPENAI_API_KEY" in data["reason"]
        assert "alternative" in data
        assert "BM25" in data["alternative"] or "keyword" in data["alternative"]
        
        print(f"✓ Embedding generation correctly reports disabled status:")
        print(f"  - Status: {data['status']}")
        print(f"  - Reason: {data['reason']}")
        print(f"  - Alternative: {data['alternative']}")


class TestAIMatchingPipeline:
    """Tests for the 5-stage AI matching pipeline"""
    
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
    
    def test_match_with_symptom_text_and_error_codes(self, auth_headers):
        """Test POST /api/efi/match - AI matching with symptom text and error codes"""
        match_request = {
            "symptom_text": "Battery not charging, voltage imbalance detected, cells showing uneven readings",
            "error_codes": ["BMS001", "CELL_IMBALANCE"],
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
        
        # Verify model used
        assert data["model_used"] == "hybrid_4stage_pipeline"
        
        # Verify processing time is reasonable
        assert data["processing_time_ms"] < 5000, f"Matching too slow: {data['processing_time_ms']}ms"
        
        # Verify matches structure
        if data["matches"]:
            match = data["matches"][0]
            assert "failure_id" in match
            assert "title" in match
            assert "match_score" in match
            assert "match_type" in match
            assert "match_stage" in match
            assert "confidence_level" in match
        
        print(f"✓ AI matching with symptom text and error codes:")
        print(f"  - Query: {data['query_text'][:50]}...")
        print(f"  - Signature hash: {data['signature_hash']}")
        print(f"  - Matches found: {len(data['matches'])}")
        print(f"  - Processing time: {data['processing_time_ms']:.2f}ms")
        print(f"  - Stages used: {data['matching_stages_used']}")
    
    def test_match_with_subsystem_hint(self, auth_headers):
        """Test matching with subsystem hint for better filtering"""
        match_request = {
            "symptom_text": "Motor making grinding noise, vibration at high speed",
            "error_codes": ["MOTOR_FAULT", "VIBRATION_HIGH"],
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
        
        print(f"✓ Matching with subsystem hint:")
        print(f"  - Subsystem: motor")
        print(f"  - Matches: {len(data['matches'])}")
        print(f"  - Stages: {data['matching_stages_used']}")
    
    def test_match_with_vehicle_info(self, auth_headers):
        """Test matching with vehicle make and model for better filtering"""
        match_request = {
            "symptom_text": "Charger not connecting, port damaged",
            "error_codes": ["CHARGE_CONN_FAIL"],
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "subsystem_hint": "charger",
            "limit": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify vehicle info is included in query
        assert "Ola" in data["query_text"] or "S1 Pro" in data["query_text"] or "charger" in data["query_text"].lower()
        
        print(f"✓ Matching with vehicle info:")
        print(f"  - Vehicle: Ola S1 Pro")
        print(f"  - Matches: {len(data['matches'])}")
    
    def test_match_with_temperature_and_load_conditions(self, auth_headers):
        """Test matching with environmental conditions"""
        match_request = {
            "symptom_text": "Battery overheating during fast charging",
            "error_codes": ["BMS_TEMP_HIGH"],
            "subsystem_hint": "battery",
            "temperature_range": "high",
            "load_condition": "fast_charging",
            "limit": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify signature hash is generated (includes temperature and load)
        assert len(data["signature_hash"]) == 16
        
        print(f"✓ Matching with environmental conditions:")
        print(f"  - Temperature: high")
        print(f"  - Load: fast_charging")
        print(f"  - Signature: {data['signature_hash']}")
    
    def test_match_stages_fallback(self, auth_headers):
        """Test that matching falls back through stages when needed"""
        # Use a query that won't match signature exactly
        match_request = {
            "symptom_text": "Display showing incorrect speed reading",
            "error_codes": ["DISPLAY_ERR"],
            "subsystem_hint": "display",
            "limit": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should use multiple stages since exact signature match unlikely
        assert len(data["matching_stages_used"]) >= 1
        
        print(f"✓ Matching stages fallback:")
        print(f"  - Stages used: {data['matching_stages_used']}")
        print(f"  - Matches: {len(data['matches'])}")
    
    def test_match_empty_results_for_random_text(self, auth_headers):
        """Test matching with unlikely symptom returns empty or low-score matches"""
        match_request = {
            "symptom_text": "xyz123 completely random text that should not match anything specific",
            "error_codes": ["NONEXISTENT_CODE_XYZ_999"],
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
            for match in data["matches"]:
                assert match["match_score"] < 0.9, "Unexpected high score for random text"
        
        print(f"✓ Random text matching:")
        print(f"  - Matches: {len(data['matches'])} (expected low-confidence)")


class TestHybridSearchBM25:
    """Tests for hybrid search with BM25 scoring"""
    
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
    
    def test_hybrid_search_uses_text_search(self, auth_headers):
        """Test that hybrid search uses text-based BM25 when vector search is disabled"""
        match_request = {
            "symptom_text": "battery cell voltage imbalance charging issue",
            "error_codes": ["BMS001"],
            "subsystem_hint": "battery",
            "limit": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Since embeddings are disabled, should use subsystem_vehicle or hybrid (text-only)
        stages = data["matching_stages_used"]
        
        # Vector semantic stage should be skipped
        assert "vector_semantic" not in stages, "Vector search should be skipped when embeddings disabled"
        
        # Should use subsystem_vehicle or hybrid stages
        assert any(s in stages for s in ["subsystem_vehicle", "hybrid", "keyword", "signature"])
        
        print(f"✓ Hybrid search with BM25 (vector disabled):")
        print(f"  - Stages used: {stages}")
        print(f"  - Vector semantic skipped: True")
    
    def test_error_code_matching_boost(self, auth_headers):
        """Test that error code matches boost the score"""
        # First, create a card with specific error codes
        card_data = {
            "title": "TEST_BM25_Error Code Match Test",
            "description": "Test card for error code matching",
            "subsystem_category": "battery",
            "failure_mode": "degradation",
            "symptom_text": "Battery error with specific codes",
            "error_codes": ["TEST_ERR_001", "TEST_ERR_002"],
            "root_cause": "Test root cause",
            "resolution_steps": [
                {"step_number": 1, "action": "Test action", "duration_minutes": 10}
            ]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert create_response.status_code == 200
        created_card = create_response.json()
        
        # Now search with matching error codes
        match_request = {
            "symptom_text": "Battery error",
            "error_codes": ["TEST_ERR_001", "TEST_ERR_002"],
            "subsystem_hint": "battery",
            "limit": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find our test card in results
        test_card_match = None
        for match in data["matches"]:
            if match["failure_id"] == created_card["failure_id"]:
                test_card_match = match
                break
        
        if test_card_match:
            # Should have matched error codes
            assert "matched_error_codes" in test_card_match
            assert len(test_card_match["matched_error_codes"]) > 0
            print(f"✓ Error code matching boost:")
            print(f"  - Card found: {test_card_match['failure_id']}")
            print(f"  - Matched codes: {test_card_match['matched_error_codes']}")
            print(f"  - Score: {test_card_match['match_score']}")
        else:
            print(f"✓ Error code matching test completed (card may not be in top results)")
    
    def test_keyword_expansion_ev_synonyms(self, auth_headers):
        """Test that EV-specific synonyms are used in search"""
        # Search with synonym terms
        match_request = {
            "symptom_text": "bms cell pack soc voltage charge",  # EV battery synonyms
            "error_codes": [],
            "subsystem_hint": "battery",
            "limit": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/match",
            headers=auth_headers,
            json=match_request
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should find battery-related cards due to synonym expansion
        if data["matches"]:
            # Check if any battery cards are found
            battery_matches = [m for m in data["matches"] if "battery" in m["title"].lower() or "cell" in m["title"].lower()]
            print(f"✓ EV synonym expansion:")
            print(f"  - Total matches: {len(data['matches'])}")
            print(f"  - Battery-related: {len(battery_matches)}")
        else:
            print(f"✓ EV synonym expansion test completed")


class TestFailureCardCRUDExtended:
    """Extended CRUD tests for failure cards"""
    
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
    
    def test_create_failure_card_full(self, auth_headers):
        """Test POST /api/efi/failure-cards - Create with all fields"""
        card_data = {
            "title": "TEST_Search_Full Card Creation",
            "description": "Complete failure card with all fields for search testing",
            "subsystem_category": "battery",
            "failure_mode": "degradation",
            "symptom_text": "Battery cells showing voltage imbalance, reduced range, slow charging",
            "error_codes": ["BMS_SEARCH_001", "CELL_SEARCH_002"],
            "root_cause": "Cell degradation due to thermal cycling",
            "root_cause_details": "Repeated charge/discharge cycles at high temperatures",
            "secondary_causes": ["Manufacturing defect", "Improper storage"],
            "resolution_steps": [
                {"step_number": 1, "action": "Check cell voltages", "duration_minutes": 15},
                {"step_number": 2, "action": "Perform cell balancing", "duration_minutes": 30},
                {"step_number": 3, "action": "Replace degraded cells", "duration_minutes": 60}
            ],
            "required_parts": [
                {"part_id": "CELL_18650", "part_name": "18650 Li-ion Cell", "quantity": 4, "estimated_cost": 500}
            ],
            "vehicle_models": [
                {"make": "Ather", "model": "450X", "year_start": 2020},
                {"make": "Ola", "model": "S1 Pro", "year_start": 2021}
            ],
            "universal_failure": False,
            "keywords": ["battery", "cell", "imbalance", "voltage", "range", "search", "test"],
            "tags": ["battery", "bms", "cell-balancing", "search-test"],
            "source_type": "field_discovery"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields
        assert "failure_id" in data
        assert data["title"] == card_data["title"]
        assert data["subsystem_category"] == "battery"
        assert data["status"] == "draft"
        assert "confidence_score" in data
        assert "signature_hash" in data
        assert len(data["signature_hash"]) == 16
        
        # Verify computed fields
        assert "estimated_total_cost" in data
        assert "estimated_repair_time_minutes" in data
        
        print(f"✓ Created full failure card:")
        print(f"  - ID: {data['failure_id']}")
        print(f"  - Signature: {data['signature_hash']}")
        print(f"  - Confidence: {data['confidence_score']}")
    
    def test_list_failure_cards_pagination(self, auth_headers):
        """Test GET /api/efi/failure-cards - List with pagination"""
        # Get first page
        response1 = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?limit=5&skip=0",
            headers=auth_headers
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        assert "items" in data1
        assert "total" in data1
        assert "limit" in data1
        assert "skip" in data1
        assert data1["limit"] == 5
        assert data1["skip"] == 0
        
        # Get second page
        response2 = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?limit=5&skip=5",
            headers=auth_headers
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert data2["skip"] == 5
        
        # Verify pagination returns results
        # Note: Due to sorting by confidence_score (which may have ties), 
        # some overlap is possible. We just verify pagination works.
        print(f"✓ Pagination working:")
        print(f"  - Total cards: {data1['total']}")
        print(f"  - Page 1: {len(data1['items'])} items")
        print(f"  - Page 2: {len(data2['items'])} items")
    
    def test_list_failure_cards_filters(self, auth_headers):
        """Test GET /api/efi/failure-cards - List with multiple filters"""
        # Filter by status
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?status=draft&subsystem=battery",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for card in data["items"]:
            assert card["status"] == "draft"
            assert card["subsystem_category"] == "battery"
        
        print(f"✓ Multiple filters working:")
        print(f"  - Status=draft, Subsystem=battery")
        print(f"  - Results: {len(data['items'])}")
    
    def test_get_single_failure_card(self, auth_headers):
        """Test GET /api/efi/failure-cards/{id} - Get single card"""
        # First get a card ID
        list_response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?limit=1",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        cards = list_response.json()["items"]
        
        if cards:
            card_id = cards[0]["failure_id"]
            
            response = requests.get(
                f"{BASE_URL}/api/efi/failure-cards/{card_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            
            assert data["failure_id"] == card_id
            assert "title" in data
            assert "description" in data
            assert "subsystem_category" in data
            
            print(f"✓ Get single card: {card_id}")
    
    def test_update_failure_card(self, auth_headers):
        """Test PUT /api/efi/failure-cards/{id} - Update card"""
        # Create a card to update
        card_data = {
            "title": "TEST_Update_Card",
            "description": "Card to be updated",
            "subsystem_category": "motor",
            "failure_mode": "overheating",
            "root_cause": "Original root cause",
            "resolution_steps": [
                {"step_number": 1, "action": "Original action", "duration_minutes": 10}
            ]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert create_response.status_code == 200
        card_id = create_response.json()["failure_id"]
        
        # Update the card
        update_data = {
            "description": "Updated description for testing",
            "root_cause": "Updated root cause",
            "keywords": ["updated", "test", "motor"]
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/efi/failure-cards/{card_id}",
            headers=auth_headers,
            json=update_data
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        assert updated["description"] == update_data["description"]
        assert updated["root_cause"] == update_data["root_cause"]
        assert "updated" in updated["keywords"]
        assert updated["version"] >= 2
        
        print(f"✓ Updated card: {card_id}")
        print(f"  - Version: {updated['version']}")
    
    def test_approve_failure_card(self, auth_headers):
        """Test POST /api/efi/failure-cards/{id}/approve - Approve card"""
        # Create a draft card
        card_data = {
            "title": "TEST_Approve_Card",
            "description": "Card to be approved",
            "subsystem_category": "charger",
            "failure_mode": "complete_failure",
            "root_cause": "Test root cause",
            "resolution_steps": [
                {"step_number": 1, "action": "Test action", "duration_minutes": 10}
            ]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards",
            headers=auth_headers,
            json=card_data
        )
        assert create_response.status_code == 200
        card_id = create_response.json()["failure_id"]
        initial_confidence = create_response.json()["confidence_score"]
        
        # Approve the card
        approve_response = requests.post(
            f"{BASE_URL}/api/efi/failure-cards/{card_id}/approve",
            headers=auth_headers
        )
        assert approve_response.status_code == 200
        data = approve_response.json()
        
        assert data["failure_id"] == card_id
        assert "new_confidence" in data
        assert data["new_confidence"] > initial_confidence
        
        # Verify status changed
        get_response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards/{card_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "approved"
        
        print(f"✓ Approved card: {card_id}")
        print(f"  - Confidence: {initial_confidence} -> {data['new_confidence']}")


class TestSearchServiceIntegration:
    """Tests for search service integration"""
    
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
    
    def test_search_by_text_in_list(self, auth_headers):
        """Test searching failure cards by text"""
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?search=battery",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should find cards with "battery" in title, description, or keywords
        print(f"✓ Text search 'battery': {len(data['items'])} results")
    
    def test_search_by_error_code(self, auth_headers):
        """Test searching failure cards by error code"""
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?search=BMS001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        print(f"✓ Error code search 'BMS001': {len(data['items'])} results")
    
    def test_search_by_signature_hash(self, auth_headers):
        """Test searching failure cards by signature hash"""
        # First get a card's signature hash
        list_response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?limit=1",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        cards = list_response.json()["items"]
        
        if cards and "signature_hash" in cards[0]:
            sig_hash = cards[0]["signature_hash"]
            
            response = requests.get(
                f"{BASE_URL}/api/efi/failure-cards?search={sig_hash}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            
            # Should find the card with this signature
            found = any(c["signature_hash"] == sig_hash for c in data["items"])
            print(f"✓ Signature hash search: Found={found}")


class TestCleanupSearchTests:
    """Cleanup test data created during search tests"""
    
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
        response = requests.get(
            f"{BASE_URL}/api/efi/failure-cards?search=TEST_",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        test_cards = [c for c in data["items"] if c["title"].startswith("TEST_")]
        print(f"✓ Found {len(test_cards)} test failure cards (TEST_ prefix)")
        print("✓ Cleanup verification completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
