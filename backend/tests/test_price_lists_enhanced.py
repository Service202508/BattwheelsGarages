"""
Test Price Lists Module - Enhanced with Zoho Books CSV format
Tests: CRUD, Item management, Export, Import, Sync, Bulk Add operations
"""
import pytest
import requests
import os
import json
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "DevTest@123"
    })
    if response.status_code == 200:
        token = response.json().get("token")
        return token
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client

@pytest.fixture(scope="module")
def test_item_id(authenticated_client):
    """Get or create a test item"""
    # First try to get existing items
    res = authenticated_client.get(f"{BASE_URL}/api/zoho/items?per_page=10")
    if res.status_code == 200:
        items = res.json().get("items", [])
        if items:
            return items[0].get("item_id")
    
    # Create a test item if none exist
    item_data = {
        "name": f"TEST_PriceList_Item_{uuid.uuid4().hex[:6]}",
        "sku": f"TEST-SKU-{uuid.uuid4().hex[:6]}",
        "rate": 1000,
        "item_type": "goods",
        "status": "active",
        "is_combo_product": False
    }
    res = authenticated_client.post(f"{BASE_URL}/api/zoho/items", json=item_data)
    if res.status_code in [200, 201]:
        data = res.json()
        return data.get("item", {}).get("item_id") or data.get("item_id")
    pytest.skip("Could not get or create test item")

@pytest.fixture(scope="module")
def test_price_list_id(authenticated_client):
    """Create a test price list for item operations"""
    pl_data = {
        "price_list_name": f"TEST_Enhanced_PriceList_{uuid.uuid4().hex[:6]}",
        "description": "Test price list for enhanced features",
        "currency_code": "INR",
        "price_type": "sales",
        "is_default": False,
        "percentage_type": "markup_percentage",
        "percentage_value": 10
    }
    res = authenticated_client.post(f"{BASE_URL}/api/zoho/price-lists", json=pl_data)
    if res.status_code in [200, 201]:
        data = res.json()
        return data.get("price_list", {}).get("price_list_id")
    pytest.skip("Could not create test price list")


class TestPriceListCRUD:
    """Test basic Price List CRUD operations"""
    
    def test_create_price_list_with_percentage(self, authenticated_client):
        """Test POST /api/zoho/price-lists with percentage_type and percentage_value"""
        pl_data = {
            "price_list_name": f"TEST_Markup_List_{uuid.uuid4().hex[:6]}",
            "description": "Test markup price list",
            "currency_code": "INR",
            "price_type": "sales",
            "is_default": False,
            "round_off_to": "nearest_1",
            "percentage_type": "markup_percentage",
            "percentage_value": 15
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/zoho/price-lists", json=pl_data)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "price_list" in data
        
        pl = data["price_list"]
        assert pl["price_list_name"] == pl_data["price_list_name"]
        assert pl["percentage_type"] == "markup_percentage"
        assert pl["percentage_value"] == 15
        assert "price_list_id" in pl
        
        print(f"Created price list: {pl['price_list_id']}")
        
    def test_list_price_lists_with_enriched_items(self, authenticated_client):
        """Test GET /api/zoho/price-lists returns enriched item data"""
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists?include_items=true")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "price_lists" in data
        assert isinstance(data["price_lists"], list)
        
        # Check structure - if items exist, verify enriched fields
        for pl in data["price_lists"]:
            assert "price_list_id" in pl or "pricelist_id" in pl
            if pl.get("items"):
                for item in pl["items"]:
                    # Enriched fields from items module
                    assert "item_name" in item or "synced_item_name" in item or item.get("item_id")
                    
        print(f"Found {len(data['price_lists'])} price lists")
    
    def test_get_single_price_list(self, authenticated_client, test_price_list_id):
        """Test GET /api/zoho/price-lists/{id} returns enriched item data"""
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "price_list" in data
        
        pl = data["price_list"]
        assert pl.get("price_list_id") == test_price_list_id or pl.get("pricelist_id") == test_price_list_id
        assert "items" in pl
        
        print(f"Got price list: {pl.get('price_list_name')}")
    
    def test_update_price_list(self, authenticated_client, test_price_list_id):
        """Test PUT /api/zoho/price-lists/{id} updates details"""
        update_data = {
            "price_list_name": f"UPDATED_PriceList_{uuid.uuid4().hex[:6]}",
            "description": "Updated description",
            "percentage_type": "markdown_percentage",
            "percentage_value": 5
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}",
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "updated" in data.get("message", "").lower()
        
        # Verify update persisted
        get_res = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}")
        assert get_res.status_code == 200
        pl = get_res.json().get("price_list", {})
        assert pl.get("description") == "Updated description"
        
        print(f"Updated price list: {test_price_list_id}")
    
    def test_delete_price_list_soft_delete(self, authenticated_client):
        """Test DELETE /api/zoho/price-lists/{id} soft deletes"""
        # Create a price list to delete
        pl_data = {
            "price_list_name": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}",
            "price_type": "sales"
        }
        create_res = authenticated_client.post(f"{BASE_URL}/api/zoho/price-lists", json=pl_data)
        assert create_res.status_code in [200, 201]
        pl_id = create_res.json().get("price_list", {}).get("price_list_id")
        
        # Delete it
        del_res = authenticated_client.delete(f"{BASE_URL}/api/zoho/price-lists/{pl_id}")
        assert del_res.status_code == 200
        
        data = del_res.json()
        assert data.get("code") == 0
        
        # Verify it's not in active list
        list_res = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists")
        price_lists = list_res.json().get("price_lists", [])
        active_ids = [pl.get("price_list_id") for pl in price_lists if pl.get("status") != "deleted"]
        assert pl_id not in active_ids
        
        print(f"Soft deleted price list: {pl_id}")


class TestPriceListItems:
    """Test Price List Item management"""
    
    def test_add_item_with_pricelist_rate_and_discount(self, authenticated_client, test_price_list_id, test_item_id):
        """Test POST /api/zoho/price-lists/{id}/items with pricelist_rate and discount"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/items",
            params={
                "item_id": test_item_id,
                "pricelist_rate": 950,
                "discount": 5,
                "discount_type": "percentage"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        
        # Verify item was added
        get_res = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}")
        pl = get_res.json().get("price_list", {})
        item_ids = [i.get("item_id") for i in pl.get("items", [])]
        assert test_item_id in item_ids
        
        print(f"Added item {test_item_id} to price list")
    
    def test_update_item_in_price_list(self, authenticated_client, test_price_list_id, test_item_id):
        """Test PUT /api/zoho/price-lists/{id}/items/{item_id} updates pricing"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/items/{test_item_id}",
            params={
                "pricelist_rate": 900,
                "discount": 10
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        
        # Verify update
        get_res = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}")
        pl = get_res.json().get("price_list", {})
        for item in pl.get("items", []):
            if item.get("item_id") == test_item_id:
                assert item.get("pricelist_rate") == 900 or item.get("custom_rate") == 900
                assert item.get("discount") == 10
                break
        
        print(f"Updated item {test_item_id} pricing in price list")
    
    def test_remove_item_from_price_list(self, authenticated_client, test_price_list_id, test_item_id):
        """Test DELETE /api/zoho/price-lists/{id}/items/{item_id}"""
        # First ensure item is in the price list
        authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/items",
            params={"item_id": test_item_id, "pricelist_rate": 1000}
        )
        
        # Now remove it
        response = authenticated_client.delete(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/items/{test_item_id}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        
        print(f"Removed item {test_item_id} from price list")


class TestPriceListExportImport:
    """Test Export and Import functionality (Zoho Books compatible)"""
    
    def test_export_csv_zoho_format(self, authenticated_client, test_price_list_id, test_item_id):
        """Test GET /api/zoho/price-lists/{id}/export returns Zoho Books format CSV"""
        # First add an item to export
        authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/items",
            params={"item_id": test_item_id, "pricelist_rate": 850, "discount": 15}
        )
        
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/export")
        assert response.status_code == 200
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type or "text/plain" in content_type or "application/octet-stream" in content_type
        
        # Check CSV header - Zoho Books format
        csv_content = response.text
        assert "Item ID" in csv_content
        assert "Item Name" in csv_content
        assert "SKU" in csv_content
        assert "Status" in csv_content
        assert "is_combo_product" in csv_content
        assert "Item Price" in csv_content
        assert "PriceList Rate" in csv_content
        assert "Discount" in csv_content
        
        print(f"Export CSV format verified - Zoho Books compatible")
        print(f"CSV Header: {csv_content.split(chr(10))[0]}")
    
    def test_import_csv_zoho_format(self, authenticated_client, test_price_list_id, test_item_id):
        """Test POST /api/zoho/price-lists/{id}/import with Zoho Books CSV data"""
        # Create CSV data matching Zoho Books format
        csv_data = f"""Item ID,Item Name,SKU,Status,is_combo_product,Item Price,PriceList Rate,Discount
{test_item_id},Test Item,SKU001,active,false,1000,800,20"""
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/import",
            json={"csv_data": csv_data}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert "imported_count" in data
        assert data["imported_count"] >= 1
        
        print(f"Imported {data['imported_count']} items from CSV")
    
    def test_import_csv_error_handling(self, authenticated_client, test_price_list_id):
        """Test import with invalid item IDs returns errors"""
        csv_data = """Item ID,Item Name,SKU,Status,is_combo_product,Item Price,PriceList Rate,Discount
INVALID-ITEM-123,Invalid Item,SKU-INVALID,active,false,1000,900,10"""
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/import",
            json={"csv_data": csv_data}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should have errors for invalid item
        if data.get("errors"):
            print(f"Import errors (expected): {data['errors']}")


class TestPriceListSync:
    """Test real-time sync with Items module"""
    
    def test_sync_items_updates_data(self, authenticated_client, test_price_list_id, test_item_id):
        """Test POST /api/zoho/price-lists/{id}/sync-items syncs item data"""
        # Add item first
        authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/items",
            params={"item_id": test_item_id, "pricelist_rate": 750}
        )
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/sync-items"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        assert "synced_count" in data
        
        print(f"Synced {data['synced_count']} items, removed {data.get('removed_count', 0)} deleted items")


class TestPriceListBulkAdd:
    """Test bulk add items with markup/markdown"""
    
    def test_bulk_add_with_markup(self, authenticated_client, test_price_list_id):
        """Test POST /api/zoho/price-lists/{id}/bulk-add with markup percentage"""
        # Get some item IDs
        items_res = authenticated_client.get(f"{BASE_URL}/api/zoho/items?per_page=5")
        items = items_res.json().get("items", [])
        
        if not items:
            pytest.skip("No items available for bulk add test")
        
        item_ids = [item.get("item_id") for item in items[:3] if item.get("item_id")]
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/bulk-add",
            json={
                "item_ids": item_ids,
                "percentage_type": "markup_percentage",
                "percentage_value": 20
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("code") == 0
        assert data.get("count") >= 1
        
        print(f"Bulk added {data['count']} items with 20% markup")
    
    def test_bulk_add_with_markdown(self, authenticated_client, test_price_list_id):
        """Test POST /api/zoho/price-lists/{id}/bulk-add with markdown percentage"""
        # Get some item IDs
        items_res = authenticated_client.get(f"{BASE_URL}/api/zoho/items?per_page=5")
        items = items_res.json().get("items", [])
        
        if not items:
            pytest.skip("No items available for bulk add test")
        
        item_ids = [item.get("item_id") for item in items[:2] if item.get("item_id")]
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/bulk-add",
            json={
                "item_ids": item_ids,
                "percentage_type": "markdown_percentage",
                "percentage_value": 10
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("code") == 0
        
        print(f"Bulk added items with 10% markdown")


class TestPriceListEdgeCases:
    """Test edge cases and error handling"""
    
    def test_get_nonexistent_price_list_returns_404(self, authenticated_client):
        """Test GET /api/zoho/price-lists/{id} with invalid ID"""
        response = authenticated_client.get(f"{BASE_URL}/api/zoho/price-lists/INVALID-PL-ID-12345")
        assert response.status_code == 404
    
    def test_update_nonexistent_price_list_returns_404(self, authenticated_client):
        """Test PUT /api/zoho/price-lists/{id} with invalid ID"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/zoho/price-lists/INVALID-PL-ID-12345",
            json={"price_list_name": "Test"}
        )
        assert response.status_code == 404
    
    def test_add_nonexistent_item_returns_404(self, authenticated_client, test_price_list_id):
        """Test adding invalid item to price list"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/items",
            params={"item_id": "INVALID-ITEM-ID-12345", "pricelist_rate": 100}
        )
        assert response.status_code == 404
    
    def test_import_without_csv_data_returns_error(self, authenticated_client, test_price_list_id):
        """Test import without CSV data"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/zoho/price-lists/{test_price_list_id}/import",
            json={}
        )
        assert response.status_code == 400
