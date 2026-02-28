"""
Test Suite for Entitlement Service
===================================

Tests the feature entitlement system for SaaS subscriptions.
"""

import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import datetime, timezone, timedelta

# Test the entitlement service
class TestEntitlementService:
    """Tests for the EntitlementService class"""
    
    def test_feature_plan_requirements_defined(self):
        """Verify all feature requirements are defined"""
        from core.subscriptions.entitlement import EntitlementService
        
        service = EntitlementService()
        
        # Should have feature requirements for all known features
        assert "efi_ai_guidance" in service.FEATURE_PLAN_REQUIREMENTS
        assert "hr_payroll" in service.FEATURE_PLAN_REQUIREMENTS
        assert "finance_invoicing" in service.FEATURE_PLAN_REQUIREMENTS
        assert "advanced_sso" in service.FEATURE_PLAN_REQUIREMENTS
    
    def test_plan_hierarchy_defined(self):
        """Verify plan hierarchy is correct"""
        from core.subscriptions.entitlement import EntitlementService
        from core.subscriptions.models import PlanCode
        
        service = EntitlementService()
        
        assert service.PLAN_HIERARCHY == [
            PlanCode.FREE,
            PlanCode.STARTER,
            PlanCode.PROFESSIONAL,
            PlanCode.ENTERPRISE
        ]
    
    def test_get_minimum_plan_for_feature(self):
        """Test getting minimum plan requirement for features"""
        from core.subscriptions.entitlement import EntitlementService
        from core.subscriptions.models import PlanCode
        
        service = EntitlementService()
        
        # Free features
        assert service.get_minimum_plan_for_feature("finance_invoicing") == PlanCode.FREE
        assert service.get_minimum_plan_for_feature("portal_technician") == PlanCode.FREE
        
        # Starter features
        assert service.get_minimum_plan_for_feature("efi_ai_guidance") == PlanCode.STARTER
        assert service.get_minimum_plan_for_feature("ops_amc") == PlanCode.STARTER
        
        # Professional features
        assert service.get_minimum_plan_for_feature("integrations_zoho_sync") == PlanCode.PROFESSIONAL
        assert service.get_minimum_plan_for_feature("advanced_reports") == PlanCode.PROFESSIONAL
        
        # Enterprise features
        assert service.get_minimum_plan_for_feature("hr_payroll") == PlanCode.ENTERPRISE
        assert service.get_minimum_plan_for_feature("advanced_sso") == PlanCode.ENTERPRISE
    
    def test_upgrade_suggestion(self):
        """Test upgrade suggestion logic"""
        from core.subscriptions.entitlement import EntitlementService
        from core.subscriptions.models import PlanCode
        
        service = EntitlementService()
        
        # On Free plan, suggest Starter for starter features
        suggestion = service._get_upgrade_suggestion("efi_ai_guidance", PlanCode.FREE)
        assert suggestion == "Starter"
        
        # On Starter plan, suggest Professional for professional features
        suggestion = service._get_upgrade_suggestion("integrations_zoho_sync", PlanCode.STARTER)
        assert suggestion == "Professional"
        
        # On Professional plan, suggest Enterprise for enterprise features
        suggestion = service._get_upgrade_suggestion("hr_payroll", PlanCode.PROFESSIONAL)
        assert suggestion == "Enterprise"


class TestEntitlementExceptions:
    """Tests for entitlement exception handling"""
    
    def test_feature_not_available_exception(self):
        """Test FeatureNotAvailable exception"""
        from core.subscriptions.entitlement import FeatureNotAvailable
        
        exc = FeatureNotAvailable(
            feature="hr_payroll",
            plan="starter",
            upgrade_to="Enterprise"
        )
        
        assert exc.status_code == 403
        assert "hr_payroll" in exc.detail["feature"]
        assert "starter" in exc.detail["current_plan"]
        assert "Enterprise" in exc.detail["upgrade_to"]
    
    def test_usage_limit_exceeded_exception(self):
        """Test UsageLimitExceeded exception"""
        from core.subscriptions.entitlement import UsageLimitExceeded
        
        exc = UsageLimitExceeded(
            feature="invoices",
            limit=500,
            current=500
        )
        
        assert exc.status_code == 429
        assert exc.detail["limit"] == 500
        assert exc.detail["current"] == 500
    
    def test_subscription_required_exception(self):
        """Test SubscriptionRequired exception"""
        from core.subscriptions.entitlement import SubscriptionRequired
        
        exc = SubscriptionRequired()
        
        assert exc.status_code == 402
        assert "subscription_required" in exc.detail["error"]
    
    def test_subscription_expired_exception(self):
        """Test SubscriptionExpired exception"""
        from core.subscriptions.entitlement import SubscriptionExpired
        
        expired_at = datetime.now(timezone.utc)
        exc = SubscriptionExpired(expired_at)
        
        assert exc.status_code == 402
        assert "subscription_expired" in exc.detail["error"]


class TestEntitlementDependencies:
    """Tests for FastAPI dependencies"""
    
    def test_require_feature_returns_callable(self):
        """Test require_feature returns a dependency"""
        from core.subscriptions.entitlement import require_feature
        
        dependency = require_feature("efi_ai_guidance")
        assert callable(dependency)
    
    def test_require_usage_limit_returns_callable(self):
        """Test require_usage_limit returns a dependency"""
        from core.subscriptions.entitlement import require_usage_limit
        
        dependency = require_usage_limit("max_invoices_per_month")
        assert callable(dependency)
    
    def test_require_subscription_returns_callable(self):
        """Test require_subscription returns a dependency"""
        from core.subscriptions.entitlement import require_subscription
        
        dependency = require_subscription()
        assert callable(dependency)


class TestFeatureGateDecorator:
    """Tests for the feature_gate decorator"""
    
    def test_feature_gate_decorator_exists(self):
        """Test feature_gate decorator can be imported"""
        from core.subscriptions.entitlement import feature_gate
        
        assert callable(feature_gate)
    
    def test_feature_gate_creates_wrapper(self):
        """Test feature_gate creates a wrapper function"""
        from core.subscriptions.entitlement import feature_gate
        
        @feature_gate("test_feature")
        async def test_func(org_id: str):
            return "result"
        
        assert callable(test_func)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
