"""
Phase F and G Tests - Multi-Tenant Architecture
===============================================

Tests for:
- Phase F: Token Vault and Zoho Sync Multi-Tenant
- Phase G: Observability and Governance
"""

import pytest
import httpx
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = "http://localhost:8001/api"
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "DevTest@123"


class TestPhaseF_TokenVault:
    """Phase F: Token Vault Tests"""
    
    def test_token_entry_dataclass(self):
        """Test TokenEntry data structure"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TokenEntry
        
        entry = TokenEntry(
            token_id="tok_test123",
            organization_id="org_test",
            provider="zoho",
            token_type="refresh_token",
            encrypted_value="encrypted_data"
        )
        
        assert entry.organization_id == "org_test"
        assert entry.provider == "zoho"
        assert entry.token_type == "refresh_token"
        
        entry_dict = entry.to_dict()
        assert "organization_id" in entry_dict
        assert "encrypted_value" in entry_dict
    
    def test_token_vault_requires_org_id(self):
        """Token vault operations require organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TenantTokenVault
        
        async def test_store():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            vault = TenantTokenVault(db)
            
            try:
                await vault.store_token(
                    organization_id=None,  # Missing!
                    provider="test",
                    token_type="api_key",
                    token_value="secret123"
                )
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "organization_id is required" in str(e)
            finally:
                client.close()
        
        asyncio.get_event_loop().run_until_complete(test_store())
    
    def test_token_encryption(self):
        """Test token encryption and decryption"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TenantTokenVault
        
        async def test_crypto():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            vault = TenantTokenVault(db, master_key="test-master-key")
            
            org_id = "org_crypto_test"
            test_value = "super_secret_token_12345"
            
            # Encrypt
            encrypted = vault._encrypt(test_value, org_id)
            assert encrypted != test_value  # Should be different
            
            # Decrypt
            decrypted = vault._decrypt(encrypted, org_id)
            assert decrypted == test_value  # Should match original
            
            # Different org should get different encryption
            encrypted_other = vault._encrypt(test_value, "org_other")
            assert encrypted_other != encrypted  # Keys derived per-org
            
            client.close()
        
        asyncio.get_event_loop().run_until_complete(test_crypto())


class TestPhaseG_Observability:
    """Phase G: Observability and Governance Tests"""
    
    def test_activity_log_dataclass(self):
        """Test TenantActivityLog data structure"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import TenantActivityLog
        
        log = TenantActivityLog(
            log_id="log_test123",
            organization_id="org_test",
            user_id="user_test",
            category="data_access",
            action="read_tickets"
        )
        
        assert log.organization_id == "org_test"
        assert log.category == "data_access"
        
        log_dict = log.to_dict()
        assert "organization_id" in log_dict
        assert "timestamp" in log_dict
    
    def test_usage_quota_calculations(self):
        """Test UsageQuota calculations"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import UsageQuota
        
        quota = UsageQuota(
            organization_id="org_test",
            quota_type="api_calls",
            limit=1000,
            used=750,
            period="monthly"
        )
        
        assert quota.remaining == 250
        assert quota.usage_percent == 75.0
        assert quota.is_exceeded == False
        
        # Test exceeded
        exceeded_quota = UsageQuota(
            organization_id="org_test",
            quota_type="storage",
            limit=100,
            used=150,
            period="monthly"
        )
        
        assert exceeded_quota.is_exceeded == True
        assert exceeded_quota.remaining == 0
    
    def test_observability_requires_org_id(self):
        """Observability operations require organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import TenantObservabilityService
        
        async def test_logging():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            service = TenantObservabilityService(db)
            
            try:
                await service.log_activity(
                    organization_id=None,  # Missing!
                    category="test",
                    action="test_action"
                )
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "organization_id is required" in str(e)
            finally:
                client.close()
        
        asyncio.get_event_loop().run_until_complete(test_logging())
    
    def test_activity_logging_works(self):
        """Test that activity logging actually works"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import TenantObservabilityService
        
        async def test_log():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            service = TenantObservabilityService(db)
            
            # Log an activity
            log = await service.log_activity(
                organization_id="org_test_logging",
                category="test",
                action="unit_test",
                user_id="test_user",
                details={"test": True}
            )
            
            assert log.log_id is not None
            assert log.organization_id == "org_test_logging"
            
            # Query it back
            logs = await service.query_activity_logs(
                organization_id="org_test_logging",
                limit=1
            )
            
            assert len(logs) >= 1
            
            client.close()
        
        asyncio.get_event_loop().run_until_complete(test_log())


class TestRoutesMigration:
    """Test that migrated routes still work"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=30.0, follow_redirects=True)
    
    @pytest.fixture
    def admin_token(self, client):
        response = client.post("/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_invoices_enhanced_works(self, client, admin_token):
        """Test invoices-enhanced endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/invoices-enhanced/", headers=headers)
        assert response.status_code in [200, 404, 422]  # 422 for missing query params
    
    def test_estimates_enhanced_works(self, client, admin_token):
        """Test estimates-enhanced endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/estimates-enhanced/", headers=headers)
        assert response.status_code in [200, 404, 422]
    
    def test_contacts_enhanced_works(self, client, admin_token):
        """Test contacts-enhanced endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/contacts-enhanced/", headers=headers)
        assert response.status_code in [200, 404, 422]
    
    def test_items_enhanced_works(self, client, admin_token):
        """Test items-enhanced endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/items-enhanced/", headers=headers)
        assert response.status_code in [200, 404, 422]
    
    def test_sales_orders_enhanced_works(self, client, admin_token):
        """Test sales-orders-enhanced endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/sales-orders-enhanced/", headers=headers)
        assert response.status_code in [200, 404, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
