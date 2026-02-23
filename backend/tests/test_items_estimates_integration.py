"""
Test Items/Price Lists Integration with Quotes/Estimates Module
Tests automatic customer-specific pricing when creating quotes.

Features tested:
- GET /api/items-enhanced/item-price/{item_id} - Get item price with optional contact_id
- GET /api/items-enhanced/contact-pricing-summary/{contact_id} - Get customer's pricing config
- GET /api/estimates-enhanced/item-pricing/{item_id}?customer_id= - Get item pricing for estimates
- GET /api/estimates-enhanced/customer-pricing/{customer_id} - Get customer's price list info
- POST /api/estimates-enhanced/ - Create estimate with automatic price list application
"""

import pytest
import requests
import os
import uuid

# Use the public URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://production-readiness-4.preview.emergentagent.com').rstrip('/')

# Test data from the review request
TEST_CUSTOMER_ID = "CUST-93AE14BE3618"  # Full Zoho Test Co - has Wholesale price list
TEST_ITEM_ID = "1837096000000446195"  # 12V Battery replacement - base rate ₹200
TEST_PRICE_LIST_ID = "PL-B575D8BF"  # Wholesale - 15% discount
EXPECTED_BASE_RATE = 200.0
EXPECTED_DISCOUNTED_RATE = 170.0  # 200 - 15% = 170
EXPECTED_DISCOUNT_PERCENTAGE = 15.0


class TestItemsEnhancedPriceEndpoints:
    """Test the new item-price and contact-pricing-summary endpoints in items-enhanced"""
    
    def test_get_item_price_without_contact(self):
        """Test getting item price without contact - should return base rate"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/item-price/{TEST_ITEM_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "pricing" in data
        
        pricing = data["pricing"]
        assert pricing["item_id"] == TEST_ITEM_ID
        assert pricing["item_name"] == "12V Battery replacement"
        assert pricing["base_rate"] == EXPECTED_BASE_RATE
        assert pricing["final_rate"] == EXPECTED_BASE_RATE  # No price list applied
        assert pricing["price_list_id"] is None
        assert pricing["price_list_name"] is None
        assert pricing["discount_applied"] == 0
    
    def test_get_item_price_with_contact_having_price_list(self):
        """Test getting item price with contact that has assigned price list"""
        response = requests.get(
            f"{BASE_URL}/api/items-enhanced/item-price/{TEST_ITEM_ID}",
            params={"contact_id": TEST_CUSTOMER_ID}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        pricing = data["pricing"]
        assert pricing["item_id"] == TEST_ITEM_ID
        assert pricing["base_rate"] == EXPECTED_BASE_RATE
        assert pricing["final_rate"] == EXPECTED_DISCOUNTED_RATE
        assert pricing["price_list_id"] == TEST_PRICE_LIST_ID
        assert pricing["price_list_name"] == "Wholesale"
        assert pricing["discount_applied"] == 30.0  # 200 - 170 = 30
        assert pricing["markup_applied"] == 0
    
    def test_get_item_price_invalid_item(self):
        """Test getting price for non-existent item"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/item-price/INVALID-ITEM-ID")
        assert response.status_code == 404
    
    def test_get_contact_pricing_summary(self):
        """Test getting pricing summary for a contact with price list"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/contact-pricing-summary/{TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "pricing_summary" in data
        
        summary = data["pricing_summary"]
        assert summary["contact_id"] == TEST_CUSTOMER_ID
        assert summary["contact_name"] == "Full Zoho Test"
        assert summary["sales_price_list"] is not None
        assert summary["sales_price_list"]["pricelist_id"] == TEST_PRICE_LIST_ID
        assert summary["sales_price_list"]["name"] == "Wholesale"
        assert summary["sales_price_list"]["discount_percentage"] == EXPECTED_DISCOUNT_PERCENTAGE
    
    def test_get_contact_pricing_summary_invalid_contact(self):
        """Test getting pricing summary for non-existent contact"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/contact-pricing-summary/INVALID-CONTACT")
        assert response.status_code == 404


class TestEstimatesEnhancedPricingEndpoints:
    """Test the new pricing endpoints in estimates-enhanced module"""
    
    def test_get_item_pricing_for_estimate_without_customer(self):
        """Test getting item pricing without customer - returns base rate"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/item-pricing/{TEST_ITEM_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "item" in data
        
        item = data["item"]
        assert item["item_id"] == TEST_ITEM_ID
        assert item["base_rate"] == EXPECTED_BASE_RATE
        assert item["rate"] == EXPECTED_BASE_RATE  # No customer, no price list
        assert item["price_list_id"] is None
    
    def test_get_item_pricing_for_estimate_with_customer(self):
        """Test getting item pricing with customer that has price list"""
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/item-pricing/{TEST_ITEM_ID}",
            params={"customer_id": TEST_CUSTOMER_ID}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        item = data["item"]
        assert item["item_id"] == TEST_ITEM_ID
        assert item["name"] == "12V Battery replacement"
        assert item["base_rate"] == EXPECTED_BASE_RATE
        assert item["rate"] == EXPECTED_DISCOUNTED_RATE  # Price list applied
        assert item["price_list_id"] == TEST_PRICE_LIST_ID
        assert item["price_list_name"] == "Wholesale"
        assert item["discount_applied"] == 30.0
    
    def test_get_item_pricing_invalid_item(self):
        """Test getting pricing for non-existent item"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/item-pricing/INVALID-ITEM")
        assert response.status_code == 404
    
    def test_get_customer_pricing_info(self):
        """Test getting customer pricing info for estimates UI"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/customer-pricing/{TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "pricing" in data
        
        pricing = data["pricing"]
        assert pricing["customer_id"] == TEST_CUSTOMER_ID
        assert pricing["customer_name"] == "Full Zoho Test"
        assert pricing["sales_price_list"] is not None
        assert pricing["sales_price_list"]["pricelist_id"] == TEST_PRICE_LIST_ID
        assert pricing["sales_price_list"]["name"] == "Wholesale"
        assert pricing["sales_price_list"]["discount_percentage"] == EXPECTED_DISCOUNT_PERCENTAGE
    
    def test_get_customer_pricing_invalid_customer(self):
        """Test getting pricing for non-existent customer"""
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/customer-pricing/INVALID-CUSTOMER")
        assert response.status_code == 404


class TestEstimateCreationWithPriceList:
    """Test estimate creation with automatic price list application"""
    
    def test_create_estimate_with_price_list_customer(self):
        """Test creating estimate for customer with price list - prices should be adjusted"""
        estimate_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "subject": f"TEST_Price List Integration {uuid.uuid4().hex[:8]}",
            "line_items": [
                {
                    "item_id": TEST_ITEM_ID,
                    "name": "12V Battery replacement",
                    "quantity": 2,
                    "rate": 0,  # Let the system apply price list rate
                    "tax_percentage": 18
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/estimates-enhanced/",
            json=estimate_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "estimate" in data
        
        estimate = data["estimate"]
        
        # Verify price list info on estimate header
        assert estimate["price_list_id"] == TEST_PRICE_LIST_ID
        assert estimate["price_list_name"] == "Wholesale"
        assert estimate["customer_id"] == TEST_CUSTOMER_ID
        
        # Verify line item pricing
        assert len(estimate["line_items"]) == 1
        line_item = estimate["line_items"][0]
        
        assert line_item["rate"] == EXPECTED_DISCOUNTED_RATE  # 170, not 200
        assert line_item["base_rate"] == EXPECTED_BASE_RATE  # Original rate tracked
        assert line_item["price_list_applied"] == "Wholesale"
        assert line_item["discount_from_pricelist"] == 30.0  # 200 - 170
        
        # Verify totals (2 items at 170 = 340 + 18% tax = 401.2)
        assert estimate["subtotal"] == 340.0
        assert estimate["total_tax"] == 61.2  # 340 * 0.18
        assert estimate["grand_total"] == 401.2
        
        # Store estimate_id for cleanup
        self.created_estimate_id = estimate["estimate_id"]
    
    def test_create_estimate_with_manual_rate_override(self):
        """Test that manual rate override takes precedence over price list"""
        manual_rate = 150.0  # Override the price list rate
        
        estimate_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "subject": f"TEST_Manual Rate Override {uuid.uuid4().hex[:8]}",
            "line_items": [
                {
                    "item_id": TEST_ITEM_ID,
                    "name": "12V Battery replacement",
                    "quantity": 1,
                    "rate": manual_rate,  # Manual override
                    "tax_percentage": 18
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/estimates-enhanced/",
            json=estimate_data
        )
        assert response.status_code == 200
        
        data = response.json()
        estimate = data["estimate"]
        line_item = estimate["line_items"][0]
        
        # Manual rate should be used
        assert line_item["rate"] == manual_rate
        assert estimate["subtotal"] == manual_rate
    
    def test_create_estimate_multiple_items_with_price_list(self):
        """Test creating estimate with multiple items - all should get price list applied"""
        estimate_data = {
            "customer_id": TEST_CUSTOMER_ID,
            "subject": f"TEST_Multiple Items {uuid.uuid4().hex[:8]}",
            "line_items": [
                {
                    "item_id": TEST_ITEM_ID,
                    "name": "12V Battery replacement",
                    "quantity": 3,
                    "rate": 0,
                    "tax_percentage": 18
                },
                {
                    "name": "Custom Service Item",  # No item_id - custom item
                    "quantity": 1,
                    "rate": 500,  # Custom rate
                    "tax_percentage": 18
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/estimates-enhanced/",
            json=estimate_data
        )
        assert response.status_code == 200
        
        data = response.json()
        estimate = data["estimate"]
        
        assert len(estimate["line_items"]) == 2
        
        # First item should have price list applied
        item1 = estimate["line_items"][0]
        assert item1["rate"] == EXPECTED_DISCOUNTED_RATE
        assert item1["price_list_applied"] == "Wholesale"
        
        # Second item is custom - no price list
        item2 = estimate["line_items"][1]
        assert item2["rate"] == 500
        assert item2.get("price_list_applied") is None


class TestPriceListVerification:
    """Verify the price list configuration is correct"""
    
    def test_verify_wholesale_price_list_exists(self):
        """Verify the Wholesale price list exists with correct discount"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/price-lists/{TEST_PRICE_LIST_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        price_list = data["price_list"]
        assert price_list["name"] == "Wholesale"
        assert price_list["discount_percentage"] == EXPECTED_DISCOUNT_PERCENTAGE
        assert price_list["is_active"] == True
    
    def test_verify_customer_has_price_list_assigned(self):
        """Verify the test customer has the Wholesale price list assigned"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/contact-price-lists/{TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        contact_pl = data["contact_price_lists"]
        assert contact_pl["sales_price_list_id"] == TEST_PRICE_LIST_ID
        assert contact_pl["sales_price_list"]["name"] == "Wholesale"


class TestExistingEstimatesWithPriceList:
    """Verify existing test estimates have price list info"""
    
    def test_get_existing_estimate_with_price_list(self):
        """Get an existing estimate and verify price list info is present"""
        # Get list of estimates for the test customer
        response = requests.get(
            f"{BASE_URL}/api/estimates-enhanced/",
            params={"customer_id": TEST_CUSTOMER_ID, "per_page": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        estimates = data.get("estimates", [])
        
        # Find an estimate with price list info
        estimate_with_pl = None
        for est in estimates:
            if est.get("price_list_name"):
                estimate_with_pl = est
                break
        
        if estimate_with_pl:
            assert estimate_with_pl["price_list_name"] == "Wholesale"
            assert estimate_with_pl["price_list_id"] == TEST_PRICE_LIST_ID


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_estimates():
    """Cleanup test estimates after all tests"""
    yield
    # After tests, delete TEST_ prefixed estimates
    try:
        response = requests.get(f"{BASE_URL}/api/estimates-enhanced/?per_page=100")
        if response.status_code == 200:
            estimates = response.json().get("estimates", [])
            for est in estimates:
                if est.get("subject", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/estimates-enhanced/{est['estimate_id']}")
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
