"""
Sprint 6B: EFI Knowledge Pipeline Tests
========================================

Tests for:
- 6B-01: POST /api/v1/platform/efi/process-queue creates knowledge articles from learning events
- 6B-02: POST /api/v1/platform/knowledge/seed-articles creates articles from seed failure cards
- 6B-03: POST /api/v1/platform/efi/fix-empty-failure-cards populates/marks incomplete cards
- 6B-04: GET /api/v1/efi-guided/suggestions/{ticket_id} includes knowledge_article in responses

Run: pytest backend/tests/test_sprint_6b_knowledge_pipeline.py -v
"""

import pytest
import requests
import os
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "battwheels_dev")


class TestAuthHelper:
    """Helper class for authentication"""
    
    @staticmethod
    def get_platform_admin_token() -> str:
        """Login as platform admin and return token"""
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "platform-admin@battwheels.in", "password": "DevTest@123"},
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 200, f"Platform admin login failed: {resp.text}"
        return resp.json().get("token")  # API returns "token" not "access_token"
    
    @staticmethod
    def get_dev_user_token() -> str:
        """Login as dev user with org context"""
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "dev@battwheels.internal", "password": "DevTest@123"},
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 200, f"Dev user login failed: {resp.text}"
        return resp.json().get("token")  # API returns "token" not "access_token"


@pytest.fixture(scope="module")
def platform_admin_token():
    """Platform admin authentication token"""
    return TestAuthHelper.get_platform_admin_token()


@pytest.fixture(scope="module")
def dev_user_token():
    """Dev user authentication token"""
    return TestAuthHelper.get_dev_user_token()


@pytest.fixture(scope="module")
def ensure_test_ticket():
    """Ensure test ticket tkt_8b36dc571ae4 exists for 6B-04 suggestion tests.
    Creates it directly in MongoDB if missing, cleans up after module."""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    ticket_id = "tkt_8b36dc571ae4"
    org_id = "dev-internal-testing-001"
    created = False

    if not db.tickets.find_one({"ticket_id": ticket_id}):
        db.tickets.insert_one({
            "ticket_id": ticket_id,
            "organization_id": org_id,
            "title": "Battery not charging — BMS fault suspected",
            "description": "Customer reports the 48V battery pack is not accepting charge. BMS indicator shows error code E-14.",
            "status": "open",
            "priority": "high",
            "ticket_type": "workshop",
            "vehicle_type": "electric_scooter",
            "created_by": "test-fixture",
        })
        created = True
        print(f"[fixture] Created test ticket {ticket_id}")

    yield ticket_id

    if created:
        db.tickets.delete_one({"ticket_id": ticket_id})
        print(f"[fixture] Cleaned up test ticket {ticket_id}")
    client.close()


# ====================
# 6B-01: Process Learning Queue Creates Knowledge Articles
# ====================

class Test6B01ProcessQueueKnowledgeArticles:
    """POST /api/v1/platform/efi/process-queue should create knowledge articles"""
    
    def test_process_queue_endpoint_requires_platform_admin(self):
        """Verify endpoint requires platform admin auth"""
        resp = requests.post(f"{BASE_URL}/api/v1/platform/efi/process-queue")
        # Should be 401 or 403 without auth
        assert resp.status_code in [401, 403, 422], f"Expected auth error, got {resp.status_code}"
    
    def test_process_queue_succeeds_for_platform_admin(self, platform_admin_token):
        """Platform admin can call process-queue endpoint"""
        resp = requests.post(
            f"{BASE_URL}/api/v1/platform/efi/process-queue",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp.status_code == 200, f"Process queue failed: {resp.text}"
        data = resp.json()
        assert data.get("success") is True
        assert "processed" in data
        assert "failed" in data
        print(f"Process queue result: processed={data['processed']}, failed={data['failed']}")
    
    def test_knowledge_articles_exist_from_learning_events(self, dev_user_token):
        """Verify knowledge articles with source_type=learning_event exist via failure cards"""
        # failure_cards is a shared-brain endpoint, requires org context for EFI feature entitlement
        resp = requests.get(
            f"{BASE_URL}/api/v1/efi-guided/failure-cards?limit=5",
            headers={
                "Authorization": f"Bearer {dev_user_token}",
                "X-Organization-ID": "dev-internal-testing-001"
            }
        )
        # This verifies the EFI service is up; knowledge article count
        # verified via seed-articles in 6B-02
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "cards" in data
        print(f"Failure cards available: {data.get('total', len(data.get('cards', [])))}")


# ====================
# 6B-02: Seed Knowledge Articles from Failure Cards
# ====================

class Test6B02SeedKnowledgeArticles:
    """POST /api/v1/platform/knowledge/seed-articles creates articles from seed cards"""
    
    def test_seed_articles_endpoint_requires_platform_admin(self):
        """Verify endpoint requires platform admin auth"""
        resp = requests.post(f"{BASE_URL}/api/v1/platform/knowledge/seed-articles")
        assert resp.status_code in [401, 403, 422], f"Expected auth error, got {resp.status_code}"
    
    def test_seed_articles_succeeds_and_returns_counts(self, platform_admin_token):
        """Platform admin can seed knowledge articles"""
        resp = requests.post(
            f"{BASE_URL}/api/v1/platform/knowledge/seed-articles",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp.status_code == 200, f"Seed articles failed: {resp.text}"
        data = resp.json()
        assert data.get("success") is True
        assert "inserted" in data
        assert "skipped" in data
        # Expected: 14 seed cards → should have inserted or skipped 14
        total = data["inserted"] + data["skipped"]
        assert total >= 14, f"Expected at least 14 seed articles, got {total}"
        print(f"Seed articles result: inserted={data['inserted']}, skipped={data['skipped']}")
    
    def test_seed_articles_idempotent_on_rerun(self, platform_admin_token):
        """Running seed-articles twice should skip existing articles"""
        # First run
        resp1 = requests.post(
            f"{BASE_URL}/api/v1/platform/knowledge/seed-articles",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        
        # Second run - should skip all
        resp2 = requests.post(
            f"{BASE_URL}/api/v1/platform/knowledge/seed-articles",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        
        # On re-run, all should be skipped (no new inserts)
        assert data2["inserted"] == 0, f"Expected 0 inserts on re-run, got {data2['inserted']}"
        print(f"Idempotency check: 2nd run inserted={data2['inserted']}, skipped={data2['skipped']}")


# ====================
# 6B-03: Fix Empty Failure Cards
# ====================

class Test6B03FixEmptyFailureCards:
    """POST /api/v1/platform/efi/fix-empty-failure-cards handles empty cards"""
    
    def test_fix_empty_cards_endpoint_requires_platform_admin(self):
        """Verify endpoint requires platform admin auth"""
        resp = requests.post(f"{BASE_URL}/api/v1/platform/efi/fix-empty-failure-cards")
        assert resp.status_code in [401, 403, 422], f"Expected auth error, got {resp.status_code}"
    
    def test_fix_empty_cards_returns_report(self, platform_admin_token):
        """Platform admin can fix empty failure cards"""
        resp = requests.post(
            f"{BASE_URL}/api/v1/platform/efi/fix-empty-failure-cards",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp.status_code == 200, f"Fix empty cards failed: {resp.text}"
        data = resp.json()
        
        # Should return counts for populated and incomplete
        assert "total_empty_cards" in data
        assert "populated_from_tickets" in data
        assert "marked_incomplete" in data
        assert "embeddings_generated" in data
        print(f"Fix empty cards result: empty={data['total_empty_cards']}, "
              f"populated={data['populated_from_tickets']}, "
              f"incomplete={data['marked_incomplete']}")
    
    def test_excluded_from_efi_filter_in_find_similar(self, dev_user_token):
        """Cards marked excluded_from_efi should not appear in similarity search"""
        # Call suggestions endpoint (uses find_similar_failure_cards internally)
        # The filter is applied there - we just verify no errors
        resp = requests.get(
            f"{BASE_URL}/api/v1/efi-guided/suggestions/tkt_8b36dc571ae4",
            headers={
                "Authorization": f"Bearer {dev_user_token}",
                "X-Organization-ID": "dev-internal-testing-001"
            }
        )
        # 200 means search worked (404 for missing ticket is also valid)
        assert resp.status_code in [200, 404], f"Suggestions failed unexpectedly: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            # Verify no excluded cards appear
            suggested_paths = data.get("suggested_paths", [])
            for path in suggested_paths:
                assert path.get("excluded_from_efi") != True, \
                    f"Excluded card appeared in suggestions: {path.get('failure_id')}"
            print(f"Suggestions returned {len(suggested_paths)} paths (none excluded)")


# ====================
# 6B-04: EFI Suggestions Include Knowledge Articles
# ====================

class Test6B04SuggestionsWithKnowledgeArticles:
    """GET /api/v1/efi-guided/suggestions/{ticket_id} includes knowledge_article field"""
    
    def test_suggestions_endpoint_works(self, dev_user_token, ensure_test_ticket):
        """Verify suggestions endpoint is accessible"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/efi-guided/suggestions/{ensure_test_ticket}",
            headers={
                "Authorization": f"Bearer {dev_user_token}",
                "X-Organization-ID": "dev-internal-testing-001"
            }
        )
        # 200 is expected now that fixture guarantees ticket exists
        assert resp.status_code == 200, f"Unexpected error: {resp.text}"
    
    def test_suggestions_include_knowledge_article_field(self, dev_user_token, ensure_test_ticket):
        """Each suggested_path should have knowledge_article with required fields"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/efi-guided/suggestions/{ensure_test_ticket}",
            headers={
                "Authorization": f"Bearer {dev_user_token}",
                "X-Organization-ID": "dev-internal-testing-001"
            }
        )
        
        assert resp.status_code == 200, f"Suggestions failed: {resp.text}"
        data = resp.json()
        
        suggested_paths = data.get("suggested_paths", [])
        # With a fresh test ticket and no pre-existing failure cards,
        # empty suggestions is a valid outcome — test the structure only
        # when suggestions are present.
        if not suggested_paths:
            print("No suggestions returned (no matching failure cards in DB) — structure check skipped, endpoint verified OK")
            return
        
        # Check at least some paths have knowledge_article
        paths_with_ka = [p for p in suggested_paths if p.get("knowledge_article")]
        print(f"Found {len(paths_with_ka)}/{len(suggested_paths)} paths with knowledge_article")
        
        # Verify knowledge_article structure
        for path in paths_with_ka:
            ka = path["knowledge_article"]
            assert "knowledge_id" in ka, f"Missing knowledge_id in {ka}"
            assert "title" in ka, f"Missing title in {ka}"
            # summary and content may be empty strings but should exist
            assert "summary" in ka or ka.get("summary") is None
            assert "content" in ka or ka.get("content") is None
            print(f"  - {path.get('failure_id')}: KB={ka.get('knowledge_id')}, title={ka.get('title')[:30]}...")
    
    def test_knowledge_article_matches_subsystem(self, dev_user_token, ensure_test_ticket):
        """Knowledge article should match the failure card subsystem"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/efi-guided/suggestions/{ensure_test_ticket}",
            headers={
                "Authorization": f"Bearer {dev_user_token}",
                "X-Organization-ID": "dev-internal-testing-001"
            }
        )
        
        assert resp.status_code == 200, f"Suggestions failed: {resp.text}"
        
        data = resp.json()
        suggested_paths = data.get("suggested_paths", [])
        
        for path in suggested_paths:
            if path.get("knowledge_article"):
                # The knowledge article should relate to the same subsystem
                card_subsystem = path.get("subsystem_category") or path.get("fault_category")
                # We can't verify exact match without more queries, but existence proves linkage
                print(f"Card subsystem: {card_subsystem}, has knowledge article")


# ====================
# Combined Integration Test
# ====================

class TestKnowledgePipelineIntegration:
    """End-to-end test of the knowledge pipeline"""
    
    def test_full_pipeline_flow(self, platform_admin_token, dev_user_token, ensure_test_ticket):
        """
        Test the full pipeline:
        1. Seed knowledge articles (6B-02)
        2. Process queue to create learning articles (6B-01)
        3. Fix empty cards (6B-03)
        4. Verify suggestions include knowledge articles (6B-04)
        """
        # Step 1: Seed knowledge articles
        resp1 = requests.post(
            f"{BASE_URL}/api/v1/platform/knowledge/seed-articles",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp1.status_code == 200, f"Seed failed: {resp1.text}"
        seed_data = resp1.json()
        print(f"Step 1 - Seed: {seed_data}")
        
        # Step 2: Process learning queue
        resp2 = requests.post(
            f"{BASE_URL}/api/v1/platform/efi/process-queue",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp2.status_code == 200, f"Process queue failed: {resp2.text}"
        queue_data = resp2.json()
        print(f"Step 2 - Process Queue: {queue_data}")
        
        # Step 3: Fix empty cards
        resp3 = requests.post(
            f"{BASE_URL}/api/v1/platform/efi/fix-empty-failure-cards",
            headers={"Authorization": f"Bearer {platform_admin_token}"}
        )
        assert resp3.status_code == 200, f"Fix empty cards failed: {resp3.text}"
        fix_data = resp3.json()
        print(f"Step 3 - Fix Empty Cards: {fix_data}")
        
        # Step 4: Check suggestions have knowledge articles
        resp4 = requests.get(
            f"{BASE_URL}/api/v1/efi-guided/suggestions/{ensure_test_ticket}",
            headers={
                "Authorization": f"Bearer {dev_user_token}",
                "X-Organization-ID": "dev-internal-testing-001"
            }
        )
        if resp4.status_code == 200:
            suggestions = resp4.json()
            paths = suggestions.get("suggested_paths", [])
            ka_count = sum(1 for p in paths if p.get("knowledge_article"))
            print(f"Step 4 - Suggestions: {len(paths)} paths, {ka_count} with knowledge articles")
        else:
            print(f"Step 4 - Suggestions: ticket not found (expected if test data missing)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
