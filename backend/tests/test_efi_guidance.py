"""
Tests for Battwheels Knowledge Brain - EFI Guidance Layer
Tests for Hinglish mode, visual specs, and ask-back functionality
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from unittest.mock import MagicMock, AsyncMock, patch


# ==================== HINGLISH TEMPLATE TESTS ====================

class TestHinglishTemplates:
    """Tests for Hinglish prompt templates"""
    
    def test_hinglish_system_prompt_contains_keywords(self):
        """Test that Hinglish system prompt has expected keywords"""
        from services.ai_guidance_service import HINGLISH_SYSTEM_PROMPT
        
        # Check for Hinglish instruction
        assert "Hinglish" in HINGLISH_SYSTEM_PROMPT
        assert "Hindi-English" in HINGLISH_SYSTEM_PROMPT
        
        # Check for shop-floor terms
        assert "multimeter" in HINGLISH_SYSTEM_PROMPT
        assert "BMS" in HINGLISH_SYSTEM_PROMPT
        assert "MCU" in HINGLISH_SYSTEM_PROMPT
        
        # Check for safety rules
        assert "SAFETY" in HINGLISH_SYSTEM_PROMPT.upper()
        assert "HV isolation" in HINGLISH_SYSTEM_PROMPT
    
    def test_ask_back_prompt_structure(self):
        """Test ask-back prompt has safe checklist"""
        from services.ai_guidance_service import ASK_BACK_PROMPT
        
        assert "SAFE CHECKLIST" in ASK_BACK_PROMPT
        assert "HV system isolation" in ASK_BACK_PROMPT
        assert "12V auxiliary battery" in ASK_BACK_PROMPT
    
    def test_quick_mode_instructions(self):
        """Test quick mode has 60-90 second guidance"""
        from services.ai_guidance_service import QUICK_MODE_INSTRUCTIONS
        
        assert "60-90 second" in QUICK_MODE_INSTRUCTIONS
        assert "5-7" in QUICK_MODE_INSTRUCTIONS  # Max steps
        
    def test_deep_mode_instructions(self):
        """Test deep mode has decision tree logic"""
        from services.ai_guidance_service import DEEP_MODE_INSTRUCTIONS
        
        assert "decision tree" in DEEP_MODE_INSTRUCTIONS.lower()
        assert "branching" in DEEP_MODE_INSTRUCTIONS.lower()


# ==================== VISUAL SPEC TESTS ====================

class TestVisualSpecService:
    """Tests for visual specification generation"""
    
    def test_generate_flowchart(self):
        """Test Mermaid flowchart generation"""
        from services.visual_spec_service import VisualSpecService
        
        steps = [
            {"action": "Check HV isolation", "expected": "Isolated"},
            {"action": "Check 12V battery", "expected": "12.4V+"},
            {"action": "Read DTCs", "expected": "No faults"}
        ]
        
        result = VisualSpecService.generate_flowchart("Test Flow", steps)
        
        assert result["type"] == "mermaid"
        assert result["diagram_type"] == "flowchart"
        assert "graph TD" in result["code"]
        assert "START" in result["code"]
        assert "END" in result["code"]
    
    def test_flowchart_max_nodes(self):
        """Test flowchart respects max 8 nodes"""
        from services.visual_spec_service import VisualSpecService
        
        # Create 10 steps
        steps = [{"action": f"Step {i}"} for i in range(10)]
        
        result = VisualSpecService.generate_flowchart("Test", steps)
        
        # Should have max 8 step nodes
        assert result["code"].count("[\"Step") <= 8
    
    def test_generate_gauge_spec(self):
        """Test gauge chart specification"""
        from services.visual_spec_service import VisualSpecService
        
        result = VisualSpecService.generate_gauge_spec(
            title="Battery SOC",
            value=75,
            max_value=100,
            unit="%"
        )
        
        assert result["type"] == "gauge"
        assert result["value"] == 75
        assert result["max"] == 100
        assert result["unit"] == "%"
        assert result["color"] == "#10b981"  # Green for 75%
    
    def test_gauge_zones_coloring(self):
        """Test gauge changes color based on zones"""
        from services.visual_spec_service import VisualSpecService
        
        # Critical zone (0-10)
        low_result = VisualSpecService.generate_gauge_spec("SOC", 5)
        assert low_result["color"] == "#ef4444"  # Red
        
        # Warning zone (10-30)
        warn_result = VisualSpecService.generate_gauge_spec("SOC", 20)
        assert warn_result["color"] == "#f59e0b"  # Amber
        
        # Normal zone (30-100)
        good_result = VisualSpecService.generate_gauge_spec("SOC", 80)
        assert good_result["color"] == "#10b981"  # Green
    
    def test_generate_bar_chart_spec(self):
        """Test horizontal bar chart specification"""
        from services.visual_spec_service import VisualSpecService
        
        data = [
            {"label": "BMS Fault", "value": 80},
            {"label": "Charger Issue", "value": 50},
            {"label": "Cell Imbalance", "value": 30}
        ]
        
        result = VisualSpecService.generate_bar_chart_spec("Causes", data)
        
        assert result["type"] == "horizontal_bar"
        assert len(result["data"]) == 3
        assert result["data"][0]["percentage"] == 80.0
    
    def test_bar_chart_max_items(self):
        """Test bar chart respects max 6 items"""
        from services.visual_spec_service import VisualSpecService
        
        data = [{"label": f"Item {i}", "value": i * 10} for i in range(10)]
        
        result = VisualSpecService.generate_bar_chart_spec("Test", data)
        
        assert len(result["data"]) <= 6


# ==================== EV DIAGNOSTIC TEMPLATES ====================

class TestEVDiagnosticTemplates:
    """Tests for predefined EV diagnostic templates"""
    
    def test_battery_not_charging_flow(self):
        """Test battery not charging template"""
        from services.visual_spec_service import EVDiagnosticTemplates
        
        template = EVDiagnosticTemplates.battery_not_charging_flow()
        
        assert template["type"] == "mermaid"
        assert "Battery Not Charging" in template["title"]
        assert "BMS" in template["code"]
    
    def test_motor_not_running_flow(self):
        """Test motor not running template"""
        from services.visual_spec_service import EVDiagnosticTemplates
        
        template = EVDiagnosticTemplates.motor_not_running_flow()
        
        assert template["type"] == "mermaid"
        assert "Motor Not Running" in template["title"]
        assert "Hall" in template["code"]  # Hall sensor check
    
    def test_range_anxiety_flow(self):
        """Test reduced range template"""
        from services.visual_spec_service import EVDiagnosticTemplates
        
        template = EVDiagnosticTemplates.range_anxiety_flow()
        
        assert template["type"] == "mermaid"
        assert "Reduced Range" in template["title"]


# ==================== ASK-BACK LOGIC TESTS ====================

class TestAskBackLogic:
    """Tests for missing information detection and ask-back"""
    
    @pytest.mark.asyncio
    async def test_missing_info_triggers_ask_back(self):
        """Test that missing vehicle model triggers ask-back questions"""
        from services.ai_guidance_service import AIGuidanceService, GuidanceContext
        
        mock_db = MagicMock()
        service = AIGuidanceService(mock_db)
        
        # Context with missing info
        context = GuidanceContext(
            ticket_id="TKT-TEST",
            organization_id="test-org",
            vehicle_make=None,  # Missing
            vehicle_model=None,  # Missing
            symptoms=None,  # Missing
            dtc_codes=None,  # Missing
            description="Test"
        )
        
        # Check missing info detection
        missing = service._check_missing_info(context)
        
        assert len(missing) > 0
        assert any(q["id"] == "vehicle_model" for q in missing)
        assert any(q["id"] == "symptoms" for q in missing)
    
    @pytest.mark.asyncio
    async def test_complete_context_no_ask_back(self):
        """Test that complete context doesn't trigger unnecessary ask-back"""
        from services.ai_guidance_service import AIGuidanceService, GuidanceContext
        
        mock_db = MagicMock()
        service = AIGuidanceService(mock_db)
        
        # Complete context
        context = GuidanceContext(
            ticket_id="TKT-TEST",
            organization_id="test-org",
            vehicle_make="Ola",
            vehicle_model="S1 Pro",
            symptoms=["Battery not charging", "SOC stuck"],
            dtc_codes=["P0A1F"],
            description="Battery issue",
            battery_soc=45.0,
            last_repair_notes="Battery replaced 6 months ago"
        )
        
        missing = service._check_missing_info(context)
        
        # Should have fewer questions with complete info
        assert len(missing) == 0


# ==================== FEATURE FLAG TESTS ====================

class TestGuidanceFeatureFlags:
    """Tests for EFI Guidance Layer feature flags"""
    
    def test_default_guidance_enabled(self):
        """Test that EFI guidance is enabled by default"""
        from services.feature_flags import DEFAULT_AI_CONFIG
        
        assert DEFAULT_AI_CONFIG["efi_guidance_layer_enabled"] is True
        assert DEFAULT_AI_CONFIG["hinglish_mode_enabled"] is True
        assert DEFAULT_AI_CONFIG["visual_diagrams_enabled"] is True
        assert DEFAULT_AI_CONFIG["ask_back_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_is_enabled_check(self):
        """Test guidance enabled check for tenant"""
        from services.ai_guidance_service import AIGuidanceService
        from services.feature_flags import FeatureFlagService
        
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value={
            "organization_id": "test-org",
            "efi_guidance_layer_enabled": True
        })
        mock_db.tenant_ai_config = mock_collection
        
        service = AIGuidanceService(mock_db)
        service.feature_flags = FeatureFlagService(mock_db)
        
        # Test is_enabled
        # Note: This would need actual async testing setup


# ==================== CONFIDENCE DETERMINATION TESTS ====================

class TestConfidenceDetermination:
    """Tests for confidence level determination"""
    
    def test_high_confidence_with_many_sources(self):
        """Test high confidence when 3+ relevant sources"""
        from services.ai_guidance_service import AIGuidanceService, GuidanceConfidence
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        service = AIGuidanceService(mock_db)
        
        # Mock sources with high relevance
        class MockSource:
            def __init__(self, score):
                self.relevance_score = score
        
        sources = [
            MockSource(0.9),
            MockSource(0.85),
            MockSource(0.8)
        ]
        
        confidence = service._determine_confidence(sources)
        assert confidence == GuidanceConfidence.HIGH
    
    def test_low_confidence_with_no_sources(self):
        """Test low confidence when no sources"""
        from services.ai_guidance_service import AIGuidanceService, GuidanceConfidence
        
        mock_db = MagicMock()
        service = AIGuidanceService(mock_db)
        
        confidence = service._determine_confidence([])
        assert confidence == GuidanceConfidence.LOW


# ==================== ESTIMATE SUGGESTION TESTS ====================

class TestEstimateSuggestions:
    """Tests for parts/labour suggestion generation"""
    
    @pytest.mark.asyncio
    async def test_battery_fix_suggests_battery_parts(self):
        """Test that battery-related fix suggests battery parts"""
        from services.ai_guidance_service import AIGuidanceService, GuidanceContext
        
        mock_db = MagicMock()
        service = AIGuidanceService(mock_db)
        
        context = GuidanceContext(
            ticket_id="TKT-TEST",
            organization_id="test-org",
            category="battery",
            description="Battery issue"
        )
        
        guidance_result = {
            "recommended_fix": "Battery BMS module needs replacement. Check connector seating."
        }
        
        suggestions = await service._generate_estimate_suggestions(context, guidance_result)
        
        # Should suggest battery-related parts
        part_names = [s["name"] for s in suggestions if s["type"] == "part"]
        assert any("Battery" in name or "BMS" in name for name in part_names)
        
        # Should include labour
        labour_items = [s for s in suggestions if s["type"] == "labour"]
        assert len(labour_items) > 0


# ==================== DIAGRAM SPEC VALIDATION ====================

class TestDiagramSpecValidation:
    """Tests for diagram specification schema validation"""
    
    def test_mermaid_diagram_has_required_fields(self):
        """Test Mermaid diagram spec has all required fields"""
        from services.visual_spec_service import VisualSpecService
        
        steps = [{"action": "Step 1"}, {"action": "Step 2"}]
        result = VisualSpecService.generate_flowchart("Test", steps)
        
        assert "type" in result
        assert "diagram_type" in result
        assert "code" in result
        assert "title" in result
        
        assert result["type"] == "mermaid"
        assert isinstance(result["code"], str)
    
    def test_chart_spec_has_required_fields(self):
        """Test chart spec has all required fields"""
        from services.visual_spec_service import VisualSpecService
        
        result = VisualSpecService.generate_gauge_spec("Test", 50)
        
        assert "type" in result
        assert "title" in result
        assert "value" in result
        assert "max" in result
        assert "color" in result
        assert "zones" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
