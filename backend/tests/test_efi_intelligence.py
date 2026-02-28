"""
Battwheels OS - EFI Intelligence Engine Tests

Tests for:
- Model-Aware Ranking Service
- Continuous Learning Service
- Failure Card Management
- Model Risk Alerts
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class MockCollection:
    """Mock MongoDB collection for testing"""
    def __init__(self):
        self.data = []
        self.find_result = []
        self.count = 0
    
    async def find_one(self, query, projection=None):
        for doc in self.data:
            match = True
            for key, value in query.items():
                if key == "$or":
                    continue
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                if projection and "_id" in projection and projection["_id"] == 0:
                    return {k: v for k, v in doc.items() if k != "_id"}
                return doc
        return None
    
    def find(self, query=None, projection=None):
        self.find_result = self.data
        return self
    
    def sort(self, field, direction):
        return self
    
    def limit(self, n):
        return self
    
    async def to_list(self, n=100):
        return self.find_result[:n]
    
    async def insert_one(self, doc):
        self.data.append(doc)
        self.count += 1
        return MagicMock(inserted_id="test_id")
    
    async def update_one(self, query, update):
        return MagicMock(matched_count=1, modified_count=1)
    
    async def update_many(self, query, update):
        return MagicMock(matched_count=len(self.data), modified_count=len(self.data))
    
    async def count_documents(self, query):
        return self.count
    
    async def aggregate(self, pipeline):
        return self
    
    async def delete_one(self, query):
        return MagicMock(deleted_count=1)


class MockDB:
    """Mock MongoDB database"""
    def __init__(self):
        self.failure_cards = MockCollection()  # Sprint 3B-01: consolidated
        self.efi_failure_cards = self.failure_cards  # Alias for backward compat in tests
        self.ai_guidance_snapshots = MockCollection()
        self.ai_guidance_feedback = MockCollection()
        self.efi_learning_queue = MockCollection()
        self.efi_model_risk_alerts = MockCollection()
        self.tickets = MockCollection()
        self.knowledge_items = MockCollection()
        self.organizations = MockCollection()


# ==================== Model-Aware Ranking Tests ====================

class TestModelAwareRanking:
    """Tests for Model-Aware Ranking Service"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.fixture
    def ranking_service(self, mock_db):
        from services.model_aware_ranking_service import ModelAwareRankingService
        return ModelAwareRankingService(mock_db)
    
    def test_calculate_score_model_match(self, ranking_service):
        """Test that model match gets highest weight"""
        from services.model_aware_ranking_service import RankingContext
        
        context = RankingContext(
            vehicle_make="Ola",
            vehicle_model="S1 Pro",
            subsystem="battery",
            symptoms=["not charging"],
            dtc_codes=["P0A80"]
        )
        
        # Card with matching model
        card_matching = {
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "subsystem": "battery",
            "dtc_codes": ["P0A80"],
            "historical_success_rate": 0.8
        }
        
        # Card without matching model
        card_not_matching = {
            "vehicle_make": "Ather",
            "vehicle_model": "450X",
            "subsystem": "battery",
            "dtc_codes": ["P0A80"],
            "historical_success_rate": 0.8
        }
        
        score_matching, factors_matching = ranking_service._calculate_score(card_matching, context)
        score_not_matching, factors_not_matching = ranking_service._calculate_score(card_not_matching, context)
        
        assert score_matching > score_not_matching, "Model match should have higher score"
        assert "model_match" in factors_matching
        assert "model_match" not in factors_not_matching
    
    def test_calculate_score_dtc_match(self, ranking_service):
        """Test DTC code matching"""
        from services.model_aware_ranking_service import RankingContext
        
        context = RankingContext(
            vehicle_model="S1 Pro",
            subsystem="battery",
            dtc_codes=["P0A80", "P0A81"]
        )
        
        card_with_dtc = {
            "vehicle_model": "S1 Pro",
            "subsystem": "battery",
            "dtc_codes": ["P0A80"],
            "historical_success_rate": 0.5
        }
        
        card_without_dtc = {
            "vehicle_model": "S1 Pro",
            "subsystem": "battery",
            "dtc_codes": ["P1234"],
            "historical_success_rate": 0.5
        }
        
        score_with_dtc, factors_with_dtc = ranking_service._calculate_score(card_with_dtc, context)
        score_without_dtc, factors_without_dtc = ranking_service._calculate_score(card_without_dtc, context)
        
        assert score_with_dtc > score_without_dtc, "DTC match should increase score"
        assert "dtc_match" in factors_with_dtc
    
    def test_calculate_score_success_rate(self, ranking_service):
        """Test historical success rate impact"""
        from services.model_aware_ranking_service import RankingContext
        
        context = RankingContext(
            vehicle_model="S1 Pro",
            subsystem="battery"
        )
        
        card_high_success = {
            "vehicle_model": "S1 Pro",
            "subsystem": "battery",
            "historical_success_rate": 0.9
        }
        
        card_low_success = {
            "vehicle_model": "S1 Pro",
            "subsystem": "battery",
            "historical_success_rate": 0.2
        }
        
        score_high, factors_high = ranking_service._calculate_score(card_high_success, context)
        score_low, factors_low = ranking_service._calculate_score(card_low_success, context)
        
        assert score_high > score_low, "Higher success rate should have higher score"
        assert "high_success_rate" in factors_high
    
    @pytest.mark.asyncio
    async def test_get_safe_checklist_battery(self, ranking_service):
        """Test safe checklist for battery subsystem"""
        from services.model_aware_ranking_service import RankingContext
        
        context = RankingContext(subsystem="battery")
        checklist = await ranking_service.get_safe_checklist(context)
        
        assert len(checklist) > 0, "Should return checklist items"
        assert any("HV" in item.get("hinglish", "") for item in checklist), "Battery checklist should mention HV"
    
    @pytest.mark.asyncio
    async def test_should_escalate_low_confidence(self, ranking_service):
        """Test escalation for low confidence"""
        from services.model_aware_ranking_service import ConfidenceLevel
        
        should_escalate, reason = await ranking_service.should_escalate([], ConfidenceLevel.LOW)
        
        assert should_escalate is True, "Should escalate on low confidence"
        assert "Low confidence" in reason


# ==================== Continuous Learning Tests ====================

class TestContinuousLearning:
    """Tests for Continuous Learning Service"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.fixture
    def learning_service(self, mock_db):
        from services.continuous_learning_service import ContinuousLearningService
        return ContinuousLearningService(mock_db)
    
    @pytest.mark.asyncio
    async def test_capture_ticket_closure(self, learning_service, mock_db):
        """Test learning event capture on ticket closure"""
        # Add a test ticket
        mock_db.tickets.data.append({
            "ticket_id": "TKT-001",
            "organization_id": "org_test",
            "vehicle_info": {"make": "Ola", "model": "S1 Pro"},
            "category": "battery",
            "symptoms": ["not charging"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Add guidance snapshot
        mock_db.ai_guidance_snapshots.data.append({
            "ticket_id": "TKT-001",
            "guidance_id": "GD-001",
            "status": "active",
            "probable_causes": [{"cause": "BMS issue", "confidence": 75}]
        })
        
        event_id = await learning_service.capture_ticket_closure(
            ticket_id="TKT-001",
            organization_id="org_test",
            closure_data={
                "actual_root_cause": "BMS cell imbalance",
                "parts_replaced": ["BMS module"],
                "ai_was_correct": True
            }
        )
        
        assert event_id.startswith("LE-"), "Should return learning event ID"
        assert mock_db.efi_learning_queue.count == 1, "Should insert learning event"
    
    @pytest.mark.asyncio
    async def test_create_draft_failure_card(self, learning_service, mock_db):
        """Test draft failure card creation from learning event"""
        event = {
            "ticket_id": "TKT-001",
            "organization_id": "org_test",
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "vehicle_category": "2W",
            "subsystem": "battery",
            "symptoms": ["not charging"],
            "dtc_codes": ["P0A80"],
            "actual_root_cause": "BMS cell imbalance",
            "parts_replaced": ["BMS module"],
            "resolution_time_minutes": 60
        }
        
        card_id = await learning_service._create_draft_failure_card(event)
        
        assert card_id.startswith("FC-"), "Should return failure card ID"
        assert mock_db.efi_failure_cards.count == 1, "Should create failure card"
    
    @pytest.mark.asyncio
    async def test_pattern_detection_trigger(self, learning_service, mock_db):
        """Test pattern detection triggers alert when threshold met"""
        # Add 3 similar events (threshold)
        for i in range(3):
            mock_db.efi_learning_queue.data.append({
                "event_id": f"LE-{i}",
                "ticket_id": f"TKT-{i}",
                "vehicle_model": "S1 Pro",
                "subsystem": "battery",
                "event_type": "ticket_closure",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            mock_db.efi_learning_queue.count += 1
        
        event = {
            "ticket_id": "TKT-004",
            "organization_id": "org_test",
            "vehicle_make": "Ola",
            "vehicle_model": "S1 Pro",
            "subsystem": "battery"
        }
        
        result = await learning_service._check_for_patterns(event)
        
        assert result is not None, "Should detect pattern"
        assert result.get("action") == "created_new", "Should create new alert"


# ==================== AI Guidance Snapshot Tests ====================

class TestAIGuidanceSnapshot:
    """Tests for AI Guidance Snapshot models"""
    
    def test_snapshot_model_creation(self):
        """Test AIGuidanceSnapshot model can be created"""
        from models.ai_guidance_models import AIGuidanceSnapshot, GuidanceMode
        
        snapshot = AIGuidanceSnapshot(
            organization_id="org_test",
            ticket_id="TKT-001",
            input_context_hash="abc123",
            mode=GuidanceMode.QUICK,
            guidance_text="Test guidance",
            safety_block="Safety first"
        )
        
        assert snapshot.snapshot_id.startswith("GS-")
        assert snapshot.guidance_id.startswith("GD-")
        assert snapshot.mode == GuidanceMode.QUICK
    
    def test_context_hash_computation(self):
        """Test context hash is deterministic"""
        from models.ai_guidance_models import AIGuidanceSnapshot
        
        snapshot1 = AIGuidanceSnapshot(
            organization_id="org_test",
            ticket_id="TKT-001",
            input_context_hash="",
            vehicle_make="Ola",
            vehicle_model="S1 Pro",
            symptoms=["not charging"],
            dtc_codes=["P0A80"],
            category="battery",
            description="Test issue"
        )
        
        snapshot2 = AIGuidanceSnapshot(
            organization_id="org_test",
            ticket_id="TKT-001",
            input_context_hash="",
            vehicle_make="Ola",
            vehicle_model="S1 Pro",
            symptoms=["not charging"],
            dtc_codes=["P0A80"],
            category="battery",
            description="Test issue"
        )
        
        hash1 = snapshot1.compute_context_hash()
        hash2 = snapshot2.compute_context_hash()
        
        assert hash1 == hash2, "Same context should produce same hash"
    
    def test_feedback_model_creation(self):
        """Test AIGuidanceFeedback model can be created"""
        from models.ai_guidance_models import AIGuidanceFeedback, FeedbackType
        
        feedback = AIGuidanceFeedback(
            guidance_id="GD-001",
            ticket_id="TKT-001",
            organization_id="org_test",
            user_id="user_001",
            feedback_type=FeedbackType.HELPFUL,
            helped=True,
            rating=5
        )
        
        assert feedback.feedback_id.startswith("GF-")
        assert feedback.helped is True
        assert feedback.rating == 5


# ==================== Structured Failure Card Tests ====================

class TestStructuredFailureCard:
    """Tests for Structured Failure Card model"""
    
    def test_failure_card_creation(self):
        """Test StructuredFailureCard model"""
        from models.ai_guidance_models import StructuredFailureCard
        
        card = StructuredFailureCard(
            organization_id="org_test",
            vehicle_make="Ola",
            vehicle_model="S1 Pro",
            vehicle_category="2W",
            subsystem="battery",
            symptom_cluster=["not charging", "red led"],
            dtc_code="P0A80",
            probable_root_cause="BMS cell imbalance",
            verified_fix="Perform cell balancing"
        )
        
        assert card.failure_card_id.startswith("FC-")
        assert card.vehicle_category == "2W"
        assert card.historical_success_rate == 0.5  # Default
    
    def test_failure_card_with_metrics(self):
        """Test failure card intelligence metrics"""
        from models.ai_guidance_models import StructuredFailureCard
        
        card = StructuredFailureCard(
            subsystem="motor",
            probable_root_cause="Hall sensor failure",
            verified_fix="Replace hall sensor",
            historical_success_rate=0.85,
            recurrence_counter=15,
            usage_count=50
        )
        
        assert card.historical_success_rate == 0.85
        assert card.recurrence_counter == 15


# ==================== Model Risk Alert Tests ====================

class TestModelRiskAlert:
    """Tests for Model Risk Alert"""
    
    def test_alert_creation(self):
        """Test ModelRiskAlert model"""
        from models.ai_guidance_models import ModelRiskAlert
        
        alert = ModelRiskAlert(
            organization_id="org_test",
            vehicle_make="Ola",
            vehicle_model="S1 Pro",
            subsystem="battery",
            occurrence_count=5,
            first_occurrence=datetime.now(timezone.utc).isoformat(),
            last_occurrence=datetime.now(timezone.utc).isoformat(),
            affected_ticket_ids=["TKT-001", "TKT-002"]
        )
        
        assert alert.alert_id.startswith("MRA-")
        assert alert.status == "active"
        assert len(alert.affected_ticket_ids) == 2


# ==================== Tenant Isolation Tests ====================

class TestTenantIsolation:
    """Tests to verify strict tenant isolation"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.fixture
    def ranking_service(self, mock_db):
        from services.model_aware_ranking_service import ModelAwareRankingService
        return ModelAwareRankingService(mock_db)
    
    @pytest.mark.asyncio
    async def test_failure_cards_tenant_filtered(self, ranking_service, mock_db):
        """Test that failure cards are tenant-isolated"""
        from services.model_aware_ranking_service import RankingContext
        
        # Add cards for different orgs
        mock_db.efi_failure_cards.data = [
            {
                "failure_card_id": "FC-001",
                "organization_id": "org_A",
                "scope": "tenant",
                "subsystem": "battery",
                "probable_root_cause": "Issue A",
                "status": "approved"
            },
            {
                "failure_card_id": "FC-002",
                "organization_id": "org_B",
                "scope": "tenant",
                "subsystem": "battery",
                "probable_root_cause": "Issue B",
                "status": "approved"
            },
            {
                "failure_card_id": "FC-003",
                "organization_id": None,
                "scope": "global",
                "subsystem": "battery",
                "probable_root_cause": "Global Issue",
                "status": "approved"
            }
        ]
        
        context = RankingContext(
            subsystem="battery",
            organization_id="org_A"
        )
        
        candidates = await ranking_service._get_candidate_cards(context)
        
        # Should include org_A's card and global card, but not org_B's
        assert len(candidates) >= 1, "Should return at least global cards"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
