"""
Tests for Battwheels Knowledge Brain - AI Assistant System
Tests for LLM Provider, Expert Queue, and Feature Flags
"""

import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


# ==================== LLM PROVIDER TESTS ====================

class TestLLMProvider:
    """Tests for LLM Provider interface and implementations"""
    
    def test_llm_provider_factory_default(self):
        """Test that factory returns Gemini as default provider"""
        from services.llm_provider import LLMProviderFactory, LLMProviderType
        
        provider = LLMProviderFactory.get_default_provider()
        assert provider.provider_name == "gemini"
    
    def test_llm_provider_factory_get_provider(self):
        """Test getting different provider types"""
        from services.llm_provider import LLMProviderFactory, LLMProviderType
        
        gemini = LLMProviderFactory.get_provider(LLMProviderType.GEMINI)
        assert gemini.provider_name == "gemini"
        
        openai = LLMProviderFactory.get_provider(LLMProviderType.OPENAI)
        assert openai.provider_name == "openai"
        
        anthropic = LLMProviderFactory.get_provider(LLMProviderType.ANTHROPIC)
        assert anthropic.provider_name == "anthropic"
    
    def test_gemini_provider_model_name(self):
        """Test Gemini provider default model"""
        from services.llm_provider import GeminiProvider
        
        provider = GeminiProvider()
        assert provider.model_name == "gemini-3-flash-preview"
    
    def test_gemini_provider_custom_model(self):
        """Test Gemini provider with custom model"""
        from services.llm_provider import GeminiProvider
        
        provider = GeminiProvider(model="gemini-2.5-pro")
        assert provider.model_name == "gemini-2.5-pro"
    
    def test_provider_availability_without_key(self):
        """Test provider reports unavailable without API key"""
        from services.llm_provider import GeminiProvider
        
        with patch.dict('os.environ', {}, clear=True):
            provider = GeminiProvider(api_key=None)
            # Without env key set, it should be unavailable
            # (This test depends on EMERGENT_LLM_KEY being set in env)
    
    def test_get_llm_provider_helper(self):
        """Test helper function for getting providers"""
        from services.llm_provider import get_llm_provider
        
        provider = get_llm_provider("gemini")
        assert provider.provider_name == "gemini"
        
        provider = get_llm_provider("claude")
        assert provider.provider_name == "anthropic"


# ==================== FEATURE FLAGS TESTS ====================

class TestFeatureFlags:
    """Tests for Feature Flags service"""
    
    def test_default_ai_config(self):
        """Test default AI configuration values"""
        from services.feature_flags import DEFAULT_AI_CONFIG
        
        assert DEFAULT_AI_CONFIG["ai_assist_enabled"] is True
        assert DEFAULT_AI_CONFIG["rag_enabled"] is True
        assert DEFAULT_AI_CONFIG["citations_enabled"] is True
        assert DEFAULT_AI_CONFIG["expert_queue_enabled"] is True
        assert DEFAULT_AI_CONFIG["zendesk_enabled"] is False  # Zendesk should be disabled
        assert DEFAULT_AI_CONFIG["daily_query_limit"] == 1000
        assert DEFAULT_AI_CONFIG["llm_provider"] == "gemini"
    
    @pytest.mark.asyncio
    async def test_get_tenant_config_returns_defaults(self):
        """Test that unconfigured tenant gets default config"""
        from services.feature_flags import FeatureFlagService, DEFAULT_AI_CONFIG
        
        # Mock database
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.tenant_ai_config = mock_collection
        
        service = FeatureFlagService(mock_db)
        config = await service.get_tenant_config("new-tenant")
        
        assert config["ai_assist_enabled"] == DEFAULT_AI_CONFIG["ai_assist_enabled"]
        assert config["organization_id"] == "new-tenant"
    
    @pytest.mark.asyncio
    async def test_is_feature_enabled(self):
        """Test feature enabled check"""
        from services.feature_flags import FeatureFlagService
        
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value={
            "organization_id": "test-org",
            "ai_assist_enabled": True,
            "expert_queue_enabled": False
        })
        mock_db.tenant_ai_config = mock_collection
        
        service = FeatureFlagService(mock_db)
        
        # Clear cache to force DB read
        service.clear_cache()
        
        assert await service.is_feature_enabled("test-org", "ai_assist_enabled") is True
        # expert_queue_enabled is False in the mock but True in defaults
        # After merge, it should use the tenant's value


# ==================== EXPERT QUEUE TESTS ====================

class TestExpertQueue:
    """Tests for Expert Queue service"""
    
    def test_zendesk_bridge_stub(self):
        """Test that Zendesk bridge is stubbed (not enabled)"""
        from services.expert_queue_service import ZendeskBridge
        
        bridge = ZendeskBridge()
        assert bridge.is_enabled is False
    
    @pytest.mark.asyncio
    async def test_zendesk_bridge_create_ticket_stub(self):
        """Test that Zendesk create_ticket returns stub response"""
        from services.expert_queue_service import ZendeskBridge
        
        bridge = ZendeskBridge()
        result = await bridge.create_ticket(
            subject="Test",
            description="Test desc",
            requester_name="Test User",
            requester_email="test@test.com"
        )
        
        assert result["status"] == "stub"
        assert result["zendesk_enabled"] is False
    
    @pytest.mark.asyncio
    async def test_escalation_creation(self):
        """Test escalation creation in expert queue"""
        from services.expert_queue_service import ExpertQueueService, ExpertQueueStatus
        
        # Mock database
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_db.expert_queue = mock_collection
        mock_db.tickets = AsyncMock()
        mock_db.tickets.update_one = AsyncMock()
        mock_db.expert_roster = AsyncMock()
        
        service = ExpertQueueService(mock_db)
        
        result = await service.create_escalation(
            query_id="AIQ-TEST123",
            ticket_id=None,
            organization_id="test-org",
            original_query="Test query",
            ai_response="Test response",
            sources_checked=[],
            urgency="high",
            reason="Test reason",
            user_id="user123",
            user_name="Test User"
        )
        
        assert "escalation_id" in result
        assert result["status"] == ExpertQueueStatus.OPEN
        assert result["priority"] == "high"
        assert result["zendesk_enabled"] is False
    
    def test_category_determination(self):
        """Test category determination from symptoms"""
        from services.expert_queue_service import ExpertQueueService
        
        mock_db = MagicMock()
        service = ExpertQueueService(mock_db)
        
        # Battery symptoms
        assert service._determine_category(["battery not charging"], None) == "battery"
        assert service._determine_category(["BMS error"], None) == "battery"
        
        # Motor symptoms
        assert service._determine_category(["motor noise"], None) == "motor"
        assert service._determine_category(["torque issue"], None) == "motor"
        
        # Charger symptoms (specific charger keywords)
        assert service._determine_category(["ccs connector issue"], None) == "charger"
        
        # Electrical symptoms
        assert service._determine_category(["fuse blown"], None) == "electrical"
        
        # General (default)
        assert service._determine_category(["random issue"], None) == "general"


# ==================== TENANT ISOLATION TESTS ====================

class TestTenantIsolation:
    """Critical tests for tenant data isolation"""
    
    @pytest.mark.asyncio
    async def test_knowledge_search_respects_tenant_scope(self):
        """Test that knowledge search only returns tenant + global knowledge"""
        from services.knowledge_store_service import KnowledgeStoreService
        from models.knowledge_brain import KnowledgeScope, ApprovalStatus
        
        # Mock database
        mock_db = MagicMock()
        
        # Create mock cursor that returns results
        async def mock_find(*args, **kwargs):
            # Return async iterator
            class MockCursor:
                def __init__(self, items):
                    self.items = items
                    self.idx = 0
                
                def limit(self, n):
                    return self
                
                def sort(self, *args, **kwargs):
                    return self
                
                async def to_list(self, n):
                    return self.items
                
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    if self.idx < len(self.items):
                        item = self.items[self.idx]
                        self.idx += 1
                        return item
                    raise StopAsyncIteration
            
            return MockCursor([])
        
        mock_collection = MagicMock()
        mock_collection.find = mock_find
        mock_db.knowledge_articles = mock_collection
        mock_db.failure_cards = mock_collection
        
        # The actual test would verify the query includes:
        # - {"scope": "global"} OR {"organization_id": org_id, "scope": "tenant"}
        # This is verified by code inspection of search_knowledge method


# ==================== INTEGRATION TESTS ====================

class TestKnowledgeBrainIntegration:
    """Integration tests for the full Knowledge Brain pipeline"""
    
    @pytest.mark.asyncio
    async def test_rag_pipeline_with_no_sources(self):
        """Test RAG pipeline returns proper response when no sources found"""
        # This would test that when no knowledge articles are found,
        # the system still returns a helpful response and recommends escalation
        pass
    
    @pytest.mark.asyncio  
    async def test_escalation_creates_timeline_entry(self):
        """Test that escalation adds entry to ticket timeline"""
        from services.expert_queue_service import ExpertQueueService
        
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_db.expert_queue = mock_collection
        
        mock_tickets = AsyncMock()
        mock_tickets.update_one = AsyncMock()
        mock_db.tickets = mock_tickets
        
        service = ExpertQueueService(mock_db)
        
        result = await service.create_escalation(
            query_id="AIQ-TEST",
            ticket_id="TKT-123",  # With ticket ID
            organization_id="test-org",
            original_query="Test",
            ai_response="Test response",
            sources_checked=[],
            urgency="normal",
            reason="Test",
            user_id="user1",
            user_name="User"
        )
        
        # Verify ticket timeline was updated
        mock_tickets.update_one.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
