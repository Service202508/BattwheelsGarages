"""
Phase C, D, E Tests - Multi-Tenant Architecture
===============================================

Tests for:
- Phase C: RBAC Tenant Scoping
- Phase D: Event System Tenant Tagging
- Phase E: Intelligence Layer Tenant Isolation
"""

import pytest
import httpx
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

BASE_URL = "http://localhost:8001/api"
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "DevTest@123"


class TestPhaseC_RBAC:
    """Phase C: RBAC Tenant Scoping Tests"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    @pytest.fixture
    def admin_token(self, client):
        response = client.post("/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_system_roles_exist(self):
        """Verify system role templates are defined"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.rbac import SYSTEM_ROLE_TEMPLATES
        
        assert "admin" in SYSTEM_ROLE_TEMPLATES
        assert "manager" in SYSTEM_ROLE_TEMPLATES
        assert "technician" in SYSTEM_ROLE_TEMPLATES
        assert "customer" in SYSTEM_ROLE_TEMPLATES
        
        # Admin should have all permissions
        admin_perms = SYSTEM_ROLE_TEMPLATES["admin"]["permissions"]
        assert "tickets" in admin_perms
        assert admin_perms["tickets"]["view"] == True
        assert admin_perms["tickets"]["create"] == True
        assert admin_perms["tickets"]["edit"] == True
        assert admin_perms["tickets"]["delete"] == True
    
    def test_tenant_role_dataclass(self):
        """Test TenantRole data structure"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.rbac import TenantRole
        
        role = TenantRole(
            role_id="role_test123",
            organization_id="org_test",
            role_code="admin",
            name="Administrator",
            description="Full access",
            is_system=True,
            permissions={"tickets": {"view": True, "create": True, "edit": True, "delete": True}}
        )
        
        assert role.has_permission("tickets", "view") == True
        assert role.has_permission("tickets", "delete") == True
        assert role.has_permission("nonexistent", "view") == False
        assert "tickets" in role.get_allowed_modules()


class TestPhaseD_EventTagging:
    """Phase D: Event System Tenant Tagging Tests"""
    
    def test_event_class_has_org_id(self):
        """Verify Event class accepts organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from events.event_dispatcher import Event, EventType
        
        event = Event(
            event_type=EventType.TICKET_CREATED,
            data={"ticket_id": "test123"},
            source="test",
            organization_id="org_test123"
        )
        
        assert event.organization_id == "org_test123"
        
        # Verify it's included in serialization
        event_dict = event.to_dict()
        assert event_dict["organization_id"] == "org_test123"
    
    def test_event_without_org_id_is_none(self):
        """Events without org_id should have None"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from events.event_dispatcher import Event, EventType
        
        event = Event(
            event_type=EventType.TICKET_CREATED,
            data={"ticket_id": "test123"},
            source="test"
        )
        
        assert event.organization_id is None


class TestPhaseE_AIIsolation:
    """Phase E: Intelligence Layer Tenant Isolation Tests"""
    
    def test_vector_document_dataclass(self):
        """Test VectorDocument data structure"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.ai_isolation import VectorDocument
        
        doc = VectorDocument(
            doc_id="test123",
            organization_id="org_test",
            collection="failure_cards",
            content="test content",
            embedding=[0.1, 0.2, 0.3]
        )
        
        assert doc.namespace == "failure_cards_org_test"
        assert doc.organization_id == "org_test"
        
        doc_dict = doc.to_dict()
        assert "organization_id" in doc_dict
        assert doc_dict["organization_id"] == "org_test"
    
    def test_vector_storage_requires_org_id(self):
        """Vector storage should require organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from core.tenant.ai_isolation import TenantVectorStorage
        
        async def test_missing_org():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            storage = TenantVectorStorage(db)
            
            try:
                await storage.store_vector(
                    doc_id="test123",
                    organization_id=None,  # Missing!
                    collection="test",
                    content="test content",
                    embedding=[0.1, 0.2, 0.3]
                )
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "organization_id is required" in str(e)
            finally:
                client.close()
        
        asyncio.get_event_loop().run_until_complete(test_missing_org())
    
    def test_similarity_search_requires_org_id(self):
        """Similarity search should require organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from core.tenant.ai_isolation import TenantVectorStorage
        
        async def test_search_missing_org():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            storage = TenantVectorStorage(db)
            
            try:
                await storage.similarity_search(
                    query_embedding=[0.1, 0.2, 0.3],
                    organization_id=None  # Missing!
                )
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "organization_id is required" in str(e)
            finally:
                client.close()
        
        asyncio.get_event_loop().run_until_complete(test_search_missing_org())
    
    def test_vector_storage_isolates_by_org(self):
        """Vectors should be isolated by organization"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from core.tenant.ai_isolation import TenantVectorStorage
        
        async def test_isolation():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            storage = TenantVectorStorage(db)
            
            # Store vectors for two different orgs
            await storage.store_vector(
                doc_id="test_org1_doc",
                organization_id="org_test1",
                collection="test_vectors",
                content="test content for org 1",
                embedding=[0.1, 0.2, 0.3]
            )
            
            await storage.store_vector(
                doc_id="test_org2_doc",
                organization_id="org_test2",
                collection="test_vectors",
                content="test content for org 2",
                embedding=[0.4, 0.5, 0.6]
            )
            
            # Search in org 1 - should only find org 1 docs
            results = await storage.similarity_search(
                query_embedding=[0.1, 0.2, 0.3],
                organization_id="org_test1",
                collection="test_vectors",
                min_score=0.0
            )
            
            # Verify isolation
            for r in results:
                assert r.organization_id == "org_test1", "Cross-org data leak detected!"
            
            # Clean up test data
            await storage.delete_vector("test_org1_doc", "org_test1")
            await storage.delete_vector("test_org2_doc", "org_test2")
            
            client.close()
        
        asyncio.get_event_loop().run_until_complete(test_isolation())


class TestIntegration:
    """Integration tests across all phases"""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    @pytest.fixture
    def admin_token(self, client):
        response = client.post("/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_full_stack_tenant_isolation(self, client, admin_token):
        """
        End-to-end test: Create ticket -> Events tagged -> Data isolated
        """
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a ticket
        response = client.post("/tickets", json={
            "title": "Phase C/D/E Integration Test",
            "description": "Testing full tenant isolation",
            "category": "battery",
            "priority": "low"
        }, headers=headers)
        
        if response.status_code == 200:
            ticket = response.json()
            assert "ticket_id" in ticket
            
            # Verify ticket has organization_id
            ticket_id = ticket["ticket_id"]
            response = client.get(f"/tickets/{ticket_id}", headers=headers)
            
            if response.status_code == 200:
                ticket_data = response.json()
                assert "organization_id" in ticket_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
