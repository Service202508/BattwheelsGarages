"""
Marketplace API Tests - Testing all marketplace endpoints
Tests: Products, Categories, Inventory, Pricing, Orders, Quick-Search, Auth
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMarketplaceProducts:
    """Product catalog endpoint tests"""
    
    def test_get_products_list(self):
        """Test GET /api/marketplace/products returns product list"""
        response = requests.get(f"{BASE_URL}/api/marketplace/products")
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert isinstance(data["products"], list)
        print(f"SUCCESS: Found {data['total']} products")
    
    def test_get_products_with_pagination(self):
        """Test pagination works correctly"""
        response = requests.get(f"{BASE_URL}/api/marketplace/products?page=1&limit=6")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["products"]) <= 6
        assert data["page"] == 1
        print(f"SUCCESS: Pagination working - {len(data['products'])} products on page 1")
    
    def test_get_products_with_category_filter(self):
        """Test category filtering"""
        response = requests.get(f"{BASE_URL}/api/marketplace/products?category=Batteries")
        assert response.status_code == 200
        
        data = response.json()
        for product in data["products"]:
            assert product["category"] == "Batteries"
        print(f"SUCCESS: Category filter working - {len(data['products'])} Batteries found")
    
    def test_get_products_with_search(self):
        """Test search functionality"""
        response = requests.get(f"{BASE_URL}/api/marketplace/products?search=motor")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["products"], list)
        print(f"SUCCESS: Search working - {len(data['products'])} results for 'motor'")
    
    def test_get_products_with_role_pricing(self):
        """Test role-based pricing"""
        # Public pricing
        response_public = requests.get(f"{BASE_URL}/api/marketplace/products?role=public")
        assert response_public.status_code == 200
        public_data = response_public.json()
        
        # Technician pricing (20% discount)
        response_tech = requests.get(f"{BASE_URL}/api/marketplace/products?role=technician")
        assert response_tech.status_code == 200
        tech_data = response_tech.json()
        
        if public_data["products"] and tech_data["products"]:
            public_price = public_data["products"][0]["final_price"]
            tech_price = tech_data["products"][0]["final_price"]
            assert tech_price < public_price
            print(f"SUCCESS: Role pricing working - Public: ₹{public_price}, Technician: ₹{tech_price}")


class TestMarketplaceCategories:
    """Category endpoint tests"""
    
    def test_get_categories(self):
        """Test GET /api/marketplace/categories"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        
        # Verify category structure
        if data["categories"]:
            cat = data["categories"][0]
            assert "name" in cat
            assert "count" in cat
            assert "slug" in cat
        
        print(f"SUCCESS: Found {len(data['categories'])} categories")
        for cat in data["categories"]:
            print(f"  - {cat['name']}: {cat['count']} products")


class TestMarketplaceQuickSearch:
    """Quick search endpoint tests (Technician Mode)"""
    
    def test_quick_search_basic(self):
        """Test GET /api/marketplace/quick-search"""
        response = requests.get(f"{BASE_URL}/api/marketplace/quick-search?q=battery")
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert "search_query" in data
        print(f"SUCCESS: Quick search returned {data['count']} results for 'battery'")
    
    def test_quick_search_with_vehicle_model(self):
        """Test quick search with vehicle model filter"""
        response = requests.get(f"{BASE_URL}/api/marketplace/quick-search?q=motor&vehicle_model=Ather")
        assert response.status_code == 200
        
        data = response.json()
        assert "filters_applied" in data
        assert data["filters_applied"]["vehicle_model"] == "Ather"
        print(f"SUCCESS: Quick search with vehicle filter returned {data['count']} results")
    
    def test_quick_search_with_failure_type(self):
        """Test quick search with failure type filter"""
        response = requests.get(f"{BASE_URL}/api/marketplace/quick-search?q=controller&failure_type=throttle")
        assert response.status_code == 200
        
        data = response.json()
        assert "filters_applied" in data
        print(f"SUCCESS: Quick search with failure type returned {data['count']} results")


class TestMarketplaceInventory:
    """Inventory endpoint tests"""
    
    def test_get_inventory_for_product(self):
        """Test GET /api/marketplace/inventory/{product_id}"""
        # First get a product ID
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=1")
        assert products_response.status_code == 200
        products = products_response.json()["products"]
        
        if products:
            product_id = products[0]["id"]
            response = requests.get(f"{BASE_URL}/api/marketplace/inventory/{product_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "sku" in data
            assert "stock_quantity" in data
            assert "stock_status" in data
            assert "nearest_locations" in data
            print(f"SUCCESS: Inventory check - SKU: {data['sku']}, Stock: {data['stock_quantity']}")
    
    def test_bulk_inventory_check(self):
        """Test POST /api/marketplace/inventory/bulk-check"""
        # Get some product IDs
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=3")
        products = products_response.json()["products"]
        product_ids = [p["id"] for p in products]
        
        response = requests.post(
            f"{BASE_URL}/api/marketplace/inventory/bulk-check",
            json=product_ids
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "inventory" in data
        print(f"SUCCESS: Bulk inventory check for {len(data['inventory'])} products")


class TestMarketplacePricing:
    """Pricing endpoint tests"""
    
    def test_get_pricing_tiers(self):
        """Test GET /api/marketplace/pricing/{product_id}"""
        # Get a product ID
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=1")
        products = products_response.json()["products"]
        
        if products:
            product_id = products[0]["id"]
            response = requests.get(f"{BASE_URL}/api/marketplace/pricing/{product_id}?role=public")
            assert response.status_code == 200
            
            data = response.json()
            assert "base_price" in data
            assert "your_role" in data
            assert "your_price" in data
            assert "all_tiers" in data
            
            # Verify all tiers present
            roles = [tier["role"] for tier in data["all_tiers"]]
            assert "public" in roles
            assert "fleet" in roles
            assert "technician" in roles
            
            print(f"SUCCESS: Pricing tiers - Base: ₹{data['base_price']}")
            for tier in data["all_tiers"]:
                print(f"  - {tier['role']}: ₹{tier['final_price']} ({tier['discount_percent']}% off)")


class TestMarketplaceAuth:
    """Phone OTP authentication tests"""
    
    def test_send_otp(self):
        """Test POST /api/marketplace/auth/send-otp"""
        response = requests.post(
            f"{BASE_URL}/api/marketplace/auth/send-otp",
            json={"phone": "9876543210"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "debug_otp" in data  # For testing only
        assert "expires_in_seconds" in data
        print(f"SUCCESS: OTP sent - Debug OTP: {data['debug_otp']}")
        return data["debug_otp"]
    
    def test_verify_otp_success(self):
        """Test POST /api/marketplace/auth/verify-otp with valid OTP"""
        # First send OTP
        send_response = requests.post(
            f"{BASE_URL}/api/marketplace/auth/send-otp",
            json={"phone": "9876543211"}
        )
        otp = send_response.json()["debug_otp"]
        
        # Verify OTP
        response = requests.post(
            f"{BASE_URL}/api/marketplace/auth/verify-otp",
            json={"phone": "9876543211", "otp": otp}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "public"  # Default role
        print(f"SUCCESS: OTP verified - User ID: {data['user']['id']}, Role: {data['user']['role']}")
        return data["token"]
    
    def test_verify_otp_invalid(self):
        """Test POST /api/marketplace/auth/verify-otp with invalid OTP"""
        # First send OTP
        requests.post(
            f"{BASE_URL}/api/marketplace/auth/send-otp",
            json={"phone": "9876543212"}
        )
        
        # Try invalid OTP
        response = requests.post(
            f"{BASE_URL}/api/marketplace/auth/verify-otp",
            json={"phone": "9876543212", "otp": "000000"}
        )
        assert response.status_code == 400
        print("SUCCESS: Invalid OTP correctly rejected")
    
    def test_get_user_profile(self):
        """Test GET /api/marketplace/auth/me"""
        # Get a valid token first
        send_response = requests.post(
            f"{BASE_URL}/api/marketplace/auth/send-otp",
            json={"phone": "9876543213"}
        )
        otp = send_response.json()["debug_otp"]
        
        verify_response = requests.post(
            f"{BASE_URL}/api/marketplace/auth/verify-otp",
            json={"phone": "9876543213", "otp": otp}
        )
        token = verify_response.json()["token"]
        
        # Get profile
        response = requests.get(f"{BASE_URL}/api/marketplace/auth/me?token={token}")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "phone" in data
        assert "role" in data
        print(f"SUCCESS: Profile retrieved - Phone: {data['phone']}, Role: {data['role']}")


class TestMarketplaceOrders:
    """Order creation and management tests"""
    
    def test_create_order_cod(self):
        """Test POST /api/marketplace/orders with COD payment"""
        # Get a product first
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=1")
        products = products_response.json()["products"]
        
        if products:
            product = products[0]
            
            order_data = {
                "items": [{"product_id": product["id"], "quantity": 1}],
                "shipping_address": {
                    "name": "Test User",
                    "phone": "9876543210",
                    "address_line1": "123 Test Street",
                    "city": "Delhi",
                    "state": "Delhi",
                    "pincode": "110001"
                },
                "payment_method": "cod",
                "user_role": "public"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/marketplace/orders",
                json=order_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert "id" in data
            assert "order_number" in data
            assert data["status"] == "pending"
            assert data["payment_method"] == "cod"
            assert "total" in data
            print(f"SUCCESS: Order created - {data['order_number']}, Total: ₹{data['total']}")
            return data["order_number"]
    
    def test_create_order_razorpay(self):
        """Test POST /api/marketplace/orders with Razorpay payment"""
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=2")
        products = products_response.json()["products"]
        
        if len(products) >= 2:
            order_data = {
                "items": [
                    {"product_id": products[0]["id"], "quantity": 1},
                    {"product_id": products[1]["id"], "quantity": 2}
                ],
                "shipping_address": {
                    "name": "Test Fleet User",
                    "phone": "9876543220",
                    "address_line1": "456 Fleet Street",
                    "city": "Gurugram",
                    "state": "Haryana",
                    "pincode": "122001"
                },
                "payment_method": "razorpay",
                "user_role": "fleet"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/marketplace/orders",
                json=order_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["payment_method"] == "razorpay"
            print(f"SUCCESS: Razorpay order created - {data['order_number']}")
    
    def test_get_order_by_id(self):
        """Test GET /api/marketplace/orders/{order_id}"""
        # Create an order first
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=1")
        products = products_response.json()["products"]
        
        if products:
            order_data = {
                "items": [{"product_id": products[0]["id"], "quantity": 1}],
                "shipping_address": {
                    "name": "Test",
                    "phone": "9876543230",
                    "address_line1": "Test Address",
                    "city": "Delhi",
                    "state": "Delhi",
                    "pincode": "110001"
                },
                "payment_method": "cod",
                "user_role": "public"
            }
            
            create_response = requests.post(f"{BASE_URL}/api/marketplace/orders", json=order_data)
            order_id = create_response.json()["id"]
            
            # Get order
            response = requests.get(f"{BASE_URL}/api/marketplace/orders/{order_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == order_id
            print(f"SUCCESS: Order retrieved - {data['order_number']}, Status: {data['status']}")


class TestProductDetails:
    """Single product endpoint tests"""
    
    def test_get_product_by_id(self):
        """Test GET /api/marketplace/products/{product_id}"""
        # Get a product ID first
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=1")
        products = products_response.json()["products"]
        
        if products:
            product_id = products[0]["id"]
            response = requests.get(f"{BASE_URL}/api/marketplace/products/{product_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == product_id
            assert "name" in data
            assert "sku" in data
            assert "final_price" in data
            print(f"SUCCESS: Product details - {data['name']} (SKU: {data['sku']})")
    
    def test_get_product_by_sku(self):
        """Test GET /api/marketplace/products/sku/{sku}"""
        # Get a product SKU first
        products_response = requests.get(f"{BASE_URL}/api/marketplace/products?limit=1")
        products = products_response.json()["products"]
        
        if products:
            sku = products[0]["sku"]
            response = requests.get(f"{BASE_URL}/api/marketplace/products/sku/{sku}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["sku"] == sku
            print(f"SUCCESS: Product by SKU - {data['name']}")
    
    def test_get_product_invalid_id(self):
        """Test GET /api/marketplace/products/{invalid_id} returns 400"""
        response = requests.get(f"{BASE_URL}/api/marketplace/products/invalid-id")
        assert response.status_code == 400
        print("SUCCESS: Invalid product ID correctly returns 400")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
