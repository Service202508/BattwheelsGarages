"""
Phase F and G Comprehensive Tests - Multi-Tenant SaaS Platform
==============================================================

Tests for all features in Phase F (Token Vault) and Phase G (Observability):
1. Authentication returns token
2. Tickets CRUD operations scoped to organization
3. Invalid X-Organization-ID header returns 403
4. Token vault requires organization_id
5. Activity logging works for org
6. Usage quotas track correctly
7. Enhanced routes work (invoices, estimates, contacts, items, sales orders)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

# Use the production URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://security-overhaul-3.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "admin123"
TECH_EMAIL = "deepak@battwheelsgarages.in"
TECH_PASSWORD = "tech123"


class TestAuthentication:
    """Test authentication returns JWT token"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    def test_admin_login_returns_token(self, session):
        """Admin login should return JWT token"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert len(data["token"]) > 0, "Token should not be empty"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"PASS: Admin login returns JWT token ({len(data['token'])} chars)")
    
    def test_technician_login_returns_token(self, session):
        """Technician login should return JWT token"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TECH_EMAIL,
            "password": TECH_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        print(f"PASS: Technician login returns JWT token")
    
    def test_invalid_credentials_rejected(self, session):
        """Invalid credentials should be rejected"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Should reject invalid credentials: {response.text}"
        print("PASS: Invalid credentials rejected with 401")


class TestTicketsCRUD:
    """Test Tickets CRUD operations scoped to organization"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    @pytest.fixture
    def admin_token(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_list_tickets_requires_auth(self, session):
        """Listing tickets should require authentication"""
        response = session.get(f"{BASE_URL}/api/tickets")
        assert response.status_code == 401, f"Should require auth: {response.status_code}"
        print("PASS: List tickets requires authentication")
    
    def test_list_tickets_with_auth(self, session, admin_token):
        """Authenticated user can list tickets scoped to their org"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = session.get(f"{BASE_URL}/api/tickets", headers=headers)
        assert response.status_code == 200, f"Failed to list tickets: {response.text}"
        
        data = response.json()
        # Response could be a list or object with tickets key
        tickets = data if isinstance(data, list) else data.get("tickets", [])
        assert isinstance(tickets, list), "Should return list of tickets"
        print(f"PASS: List tickets returns {len(tickets)} tickets")
    
    def test_create_ticket_inherits_org_id(self, session, admin_token):
        """Created ticket should inherit organization_id"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        ticket_data = {
            "title": f"TEST_Phase_FG_Ticket_{uuid.uuid4().hex[:8]}",
            "description": "Testing Phase F/G tenant isolation",
            "category": "battery",
            "priority": "medium"
        }
        
        response = session.post(f"{BASE_URL}/api/tickets", json=ticket_data, headers=headers)
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        
        ticket = response.json()
        assert "ticket_id" in ticket, "Should return ticket_id"
        
        # Verify ticket has organization_id
        ticket_id = ticket["ticket_id"]
        response = session.get(f"{BASE_URL}/api/tickets/{ticket_id}", headers=headers)
        assert response.status_code == 200, f"Failed to get ticket: {response.text}"
        
        fetched = response.json()
        assert "organization_id" in fetched, "Ticket should have organization_id"
        assert fetched["organization_id"] is not None, "organization_id should not be None"
        print(f"PASS: Created ticket {ticket_id} has organization_id: {fetched['organization_id']}")


class TestTenantIsolation:
    """Test Invalid X-Organization-ID header returns 403"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    @pytest.fixture
    def admin_token(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_invalid_org_id_returns_403_tickets(self, session, admin_token):
        """Invalid X-Organization-ID should return 403 for tickets"""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": f"org_{uuid.uuid4().hex[:12]}"  # Random invalid org
        }
        
        response = session.get(f"{BASE_URL}/api/tickets", headers=headers)
        assert response.status_code == 403, f"Should return 403, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "TENANT_ACCESS_DENIED" in str(data) or "Access denied" in str(data), \
            f"Should indicate tenant access denied: {data}"
        print("PASS: Invalid X-Organization-ID returns 403 for tickets")
    
    def test_invalid_org_id_returns_403_vehicles(self, session, admin_token):
        """Invalid X-Organization-ID should return 403 for vehicles"""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": f"org_{uuid.uuid4().hex[:12]}"
        }
        
        response = session.get(f"{BASE_URL}/api/vehicles", headers=headers)
        assert response.status_code == 403, f"Should return 403, got {response.status_code}"
        print("PASS: Invalid X-Organization-ID returns 403 for vehicles")
    
    def test_invalid_org_id_returns_403_inventory(self, session, admin_token):
        """Invalid X-Organization-ID should return 403 for inventory"""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": f"org_{uuid.uuid4().hex[:12]}"
        }
        
        response = session.get(f"{BASE_URL}/api/inventory", headers=headers)
        assert response.status_code == 403, f"Should return 403, got {response.status_code}"
        print("PASS: Invalid X-Organization-ID returns 403 for inventory")


class TestPhaseF_TokenVault:
    """Test Token Vault requires organization_id"""
    
    def test_token_vault_requires_org_id_store(self):
        """Token vault store_token should require organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TenantTokenVault
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
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
                print("PASS: Token vault store_token requires organization_id")
            finally:
                client.close()
        
        asyncio.get_event_loop().run_until_complete(test_store())
    
    def test_token_vault_requires_org_id_get(self):
        """Token vault get_token should require organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TenantTokenVault
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_get():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            vault = TenantTokenVault(db)
            
            try:
                await vault.get_token(
                    organization_id=None,  # Missing!
                    provider="test",
                    token_type="api_key"
                )
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "organization_id is required" in str(e)
                print("PASS: Token vault get_token requires organization_id")
            finally:
                client.close()
        
        asyncio.get_event_loop().run_until_complete(test_get())
    
    def test_token_vault_encryption_decryption(self):
        """Token vault should encrypt and decrypt tokens correctly"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TenantTokenVault
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_crypto():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            vault = TenantTokenVault(db, master_key="test-master-key-12345")
            
            org_id = f"org_test_{uuid.uuid4().hex[:8]}"
            secret_value = f"super_secret_token_{uuid.uuid4().hex}"
            
            # Encrypt
            encrypted = vault._encrypt(secret_value, org_id)
            assert encrypted != secret_value, "Encrypted should differ from original"
            
            # Decrypt
            decrypted = vault._decrypt(encrypted, org_id)
            assert decrypted == secret_value, "Decrypted should match original"
            
            # Different org gets different encryption
            other_org = f"org_other_{uuid.uuid4().hex[:8]}"
            encrypted_other = vault._encrypt(secret_value, other_org)
            assert encrypted_other != encrypted, "Different orgs should get different encryption"
            
            client.close()
            print("PASS: Token vault encryption/decryption works correctly")
        
        asyncio.get_event_loop().run_until_complete(test_crypto())
    
    def test_token_vault_store_and_retrieve(self):
        """Token vault should store and retrieve tokens correctly"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TenantTokenVault
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_store_retrieve():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            vault = TenantTokenVault(db)
            
            org_id = f"org_test_vault_{uuid.uuid4().hex[:8]}"
            provider = "test_provider"
            token_type = "api_key"
            token_value = f"test_secret_{uuid.uuid4().hex}"
            
            # Store
            entry = await vault.store_token(
                organization_id=org_id,
                provider=provider,
                token_type=token_type,
                token_value=token_value
            )
            assert entry.organization_id == org_id
            assert entry.provider == provider
            
            # Retrieve
            retrieved = await vault.get_token(org_id, provider, token_type)
            assert retrieved == token_value, "Retrieved token should match stored"
            
            # Clean up
            await vault.delete_token(org_id, provider, token_type)
            
            client.close()
            print("PASS: Token vault store and retrieve works correctly")
        
        asyncio.get_event_loop().run_until_complete(test_store_retrieve())


class TestPhaseG_Observability:
    """Test Activity logging and Usage quotas for organization"""
    
    def test_activity_logging_requires_org_id(self):
        """Activity logging should require organization_id"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import TenantObservabilityService
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
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
                print("PASS: Activity logging requires organization_id")
            finally:
                client.close()
        
        asyncio.get_event_loop().run_until_complete(test_logging())
    
    def test_activity_logging_works(self):
        """Activity logging should work correctly"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import TenantObservabilityService
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_log():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            service = TenantObservabilityService(db)
            
            org_id = f"org_test_obs_{uuid.uuid4().hex[:8]}"
            
            # Log activity
            log = await service.log_activity(
                organization_id=org_id,
                category="data_access",
                action="test_action",
                user_id="test_user",
                details={"test": True, "phase": "G"}
            )
            
            assert log.log_id is not None, "Log should have ID"
            assert log.organization_id == org_id, "Log should have org_id"
            assert log.category == "data_access"
            
            # Query logs
            logs = await service.query_activity_logs(org_id, limit=10)
            assert len(logs) >= 1, "Should have at least 1 log"
            
            # Verify latest log
            latest = logs[0]
            assert latest["organization_id"] == org_id
            
            client.close()
            print(f"PASS: Activity logging works - logged {log.log_id}")
        
        asyncio.get_event_loop().run_until_complete(test_log())
    
    def test_usage_quota_tracking(self):
        """Usage quotas should track correctly"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import TenantObservabilityService, UsageQuota
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_quota():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['test_database']
            service = TenantObservabilityService(db)
            
            org_id = f"org_test_quota_{uuid.uuid4().hex[:8]}"
            quota_type = "api_calls"
            
            # Set quota
            quota = await service.set_quota(
                organization_id=org_id,
                quota_type=quota_type,
                limit=1000,
                period="monthly"
            )
            
            assert quota.limit == 1000
            assert quota.period == "monthly"
            
            # Increment usage
            updated = await service.increment_usage(org_id, quota_type, 100)
            assert updated is not None, "Should return updated quota"
            assert updated.used == 100, f"Should have 100 used, got {updated.used}"
            
            # Check remaining
            assert updated.remaining == 900
            assert updated.usage_percent == 10.0
            assert updated.is_exceeded == False
            
            # Get quota status
            status = await service.get_quota_status(org_id)
            assert len(status) >= 1, "Should have quota status"
            
            client.close()
            print(f"PASS: Usage quota tracking works - 100/1000 used")
        
        asyncio.get_event_loop().run_until_complete(test_quota())
    
    def test_quota_exceeded_detection(self):
        """Should detect when quota is exceeded"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import UsageQuota
        
        # Test exceeded
        quota = UsageQuota(
            organization_id="org_test",
            quota_type="storage",
            limit=100,
            used=150,
            period="monthly"
        )
        
        assert quota.is_exceeded == True, "Should be exceeded"
        assert quota.remaining == 0, "Remaining should be 0"
        assert quota.usage_percent == 150.0, "Usage percent should be 150"
        print("PASS: Quota exceeded detection works")


class TestEnhancedRoutes:
    """Test Enhanced routes work (invoices, estimates, contacts, items, sales orders)"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    @pytest.fixture
    def admin_token(self, session):
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_invoices_enhanced_endpoint(self, session, admin_token):
        """invoices-enhanced endpoint should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = session.get(f"{BASE_URL}/api/invoices-enhanced/", headers=headers)
        assert response.status_code == 200, f"Invoices enhanced failed: {response.text}"
        
        data = response.json()
        assert "invoices" in data or "code" in data, "Should return valid response"
        print("PASS: invoices-enhanced endpoint works")
    
    def test_estimates_enhanced_endpoint(self, session, admin_token):
        """estimates-enhanced endpoint should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = session.get(f"{BASE_URL}/api/estimates-enhanced/", headers=headers)
        assert response.status_code == 200, f"Estimates enhanced failed: {response.text}"
        
        data = response.json()
        assert "estimates" in data or "code" in data, "Should return valid response"
        print("PASS: estimates-enhanced endpoint works")
    
    def test_contacts_enhanced_endpoint(self, session, admin_token):
        """contacts-enhanced endpoint should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = session.get(f"{BASE_URL}/api/contacts-enhanced/", headers=headers)
        assert response.status_code == 200, f"Contacts enhanced failed: {response.text}"
        
        data = response.json()
        assert "contacts" in data or "code" in data, "Should return valid response"
        print("PASS: contacts-enhanced endpoint works")
    
    def test_items_enhanced_endpoint(self, session, admin_token):
        """items-enhanced endpoint should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = session.get(f"{BASE_URL}/api/items-enhanced/", headers=headers)
        assert response.status_code == 200, f"Items enhanced failed: {response.text}"
        
        data = response.json()
        assert "items" in data or "code" in data, "Should return valid response"
        print("PASS: items-enhanced endpoint works")
    
    def test_sales_orders_enhanced_endpoint(self, session, admin_token):
        """sales-orders-enhanced endpoint should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = session.get(f"{BASE_URL}/api/sales-orders-enhanced/", headers=headers)
        assert response.status_code == 200, f"Sales orders enhanced failed: {response.text}"
        
        data = response.json()
        assert "salesorders" in data or "code" in data or isinstance(data, list), \
            "Should return valid response"
        print("PASS: sales-orders-enhanced endpoint works")


class TestServicesModulesExist:
    """Test that all tenant service modules exist and can be imported"""
    
    def test_tenant_context_module_exists(self):
        """TenantContext module should exist and be importable"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.context import TenantContext, TenantContextManager
        from core.tenant.context import tenant_context_required, optional_tenant_context
        
        assert TenantContext is not None
        assert TenantContextManager is not None
        print("PASS: TenantContext module exists and is importable")
    
    def test_tenant_guard_module_exists(self):
        """TenantGuard module should exist and be importable"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.guard import TenantGuard, TenantGuardMiddleware
        
        assert TenantGuard is not None
        assert TenantGuardMiddleware is not None
        print("PASS: TenantGuard module exists and is importable")
    
    def test_tenant_token_vault_module_exists(self):
        """TenantTokenVault module should exist and be importable"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.token_vault import TenantTokenVault, TokenEntry
        from core.tenant.token_vault import TenantZohoSyncService
        
        assert TenantTokenVault is not None
        assert TokenEntry is not None
        assert TenantZohoSyncService is not None
        print("PASS: TenantTokenVault module exists and is importable")
    
    def test_tenant_observability_module_exists(self):
        """TenantObservabilityService module should exist and be importable"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core.tenant.observability import TenantObservabilityService
        from core.tenant.observability import TenantActivityLog, UsageQuota, TenantMetrics
        
        assert TenantObservabilityService is not None
        assert TenantActivityLog is not None
        assert UsageQuota is not None
        print("PASS: TenantObservabilityService module exists and is importable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
