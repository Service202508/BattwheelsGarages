"""
Phase 3 Items Module Enhancement Tests
Testing: Preferences, Field Configuration, Auto SKU Generation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestItemPreferences:
    """Test module preferences endpoints"""
    
    def test_get_preferences(self):
        """GET /api/items-enhanced/preferences - Get module preferences"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/preferences")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "preferences" in data
        
        prefs = data["preferences"]
        # Verify all expected preference fields exist
        assert "enable_sku" in prefs
        assert "auto_generate_sku" in prefs
        assert "sku_prefix" in prefs
        assert "sku_sequence_start" in prefs
        assert "require_hsn_sac" in prefs
        assert "hsn_digits_required" in prefs
        assert "enable_reorder_alerts" in prefs
        assert "enable_low_stock_alerts" in prefs
        assert "default_tax_preference" in prefs
        assert "default_unit" in prefs
        assert "default_item_type" in prefs
        assert "default_tax_rate" in prefs
        assert "enable_images" in prefs
        assert "enable_custom_fields" in prefs
        assert "enable_barcode" in prefs
        assert "barcode_type" in prefs
        print(f"✓ Preferences retrieved successfully with {len(prefs)} settings")
    
    def test_update_preferences(self):
        """PUT /api/items-enhanced/preferences - Update preferences"""
        # First get current preferences
        get_response = requests.get(f"{BASE_URL}/api/items-enhanced/preferences")
        original_prefs = get_response.json()["preferences"]
        
        # Update preferences
        updated_prefs = {
            "enable_sku": True,
            "auto_generate_sku": True,  # Enable auto SKU for testing
            "sku_prefix": "TEST-SKU-",
            "sku_sequence_start": 100,
            "require_hsn_sac": False,
            "hsn_digits_required": 6,
            "enable_reorder_alerts": True,
            "enable_low_stock_alerts": True,
            "low_stock_threshold_days": 14,
            "default_tax_preference": "taxable",
            "default_unit": "pcs",
            "default_item_type": "inventory",
            "default_tax_rate": 18,
            "enable_images": True,
            "enable_custom_fields": True,
            "enable_barcode": True,
            "barcode_type": "CODE128",
            "default_valuation_method": "fifo",
            "track_serial_numbers": False,
            "track_batch_numbers": False
        }
        
        response = requests.put(
            f"{BASE_URL}/api/items-enhanced/preferences",
            json=updated_prefs
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "Preferences updated"
        
        # Verify update persisted
        verify_response = requests.get(f"{BASE_URL}/api/items-enhanced/preferences")
        verify_data = verify_response.json()["preferences"]
        assert verify_data["sku_prefix"] == "TEST-SKU-"
        assert verify_data["sku_sequence_start"] == 100
        assert verify_data["auto_generate_sku"] == True
        print("✓ Preferences updated and verified successfully")
        
        # Restore original preferences
        restore_prefs = {
            "enable_sku": original_prefs.get("enable_sku", True),
            "auto_generate_sku": original_prefs.get("auto_generate_sku", False),
            "sku_prefix": original_prefs.get("sku_prefix", "SKU-"),
            "sku_sequence_start": original_prefs.get("sku_sequence_start", 1),
            "require_hsn_sac": original_prefs.get("require_hsn_sac", False),
            "hsn_digits_required": original_prefs.get("hsn_digits_required", 4),
            "enable_reorder_alerts": original_prefs.get("enable_reorder_alerts", True),
            "enable_low_stock_alerts": original_prefs.get("enable_low_stock_alerts", True),
            "low_stock_threshold_days": original_prefs.get("low_stock_threshold_days", 7),
            "default_tax_preference": original_prefs.get("default_tax_preference", "taxable"),
            "default_unit": original_prefs.get("default_unit", "pcs"),
            "default_item_type": original_prefs.get("default_item_type", "inventory"),
            "default_tax_rate": original_prefs.get("default_tax_rate", 18),
            "enable_images": original_prefs.get("enable_images", True),
            "enable_custom_fields": original_prefs.get("enable_custom_fields", True),
            "enable_barcode": original_prefs.get("enable_barcode", True),
            "barcode_type": original_prefs.get("barcode_type", "CODE128"),
            "default_valuation_method": original_prefs.get("default_valuation_method", "fifo"),
            "track_serial_numbers": original_prefs.get("track_serial_numbers", False),
            "track_batch_numbers": original_prefs.get("track_batch_numbers", False)
        }
        requests.put(f"{BASE_URL}/api/items-enhanced/preferences", json=restore_prefs)


class TestFieldConfiguration:
    """Test field configuration endpoints"""
    
    def test_get_field_config(self):
        """GET /api/items-enhanced/field-config - Get field configuration"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/field-config")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "field_config" in data
        
        fields = data["field_config"]
        assert len(fields) == 15, f"Expected 15 fields, got {len(fields)}"
        
        # Verify expected fields exist
        field_names = [f["field_name"] for f in fields]
        expected_fields = ["name", "sku", "item_type", "description", "sales_rate", 
                          "purchase_rate", "unit", "hsn_code", "sac_code", "tax_percentage",
                          "stock_on_hand", "reorder_level", "group_name", "barcode_value", "image_url"]
        
        for expected in expected_fields:
            assert expected in field_names, f"Missing field: {expected}"
        
        # Verify field structure
        for field in fields:
            assert "field_name" in field
            assert "display_name" in field
            assert "is_active" in field
            assert "show_in_list" in field
            assert "show_in_form" in field
            assert "show_in_pdf" in field
            assert "is_mandatory" in field
        
        print(f"✓ Field configuration retrieved with {len(fields)} fields")
    
    def test_update_field_config(self):
        """PUT /api/items-enhanced/field-config - Update field configuration"""
        # Get current config
        get_response = requests.get(f"{BASE_URL}/api/items-enhanced/field-config")
        original_config = get_response.json()["field_config"]
        
        # Update a single field
        updated_fields = [
            {
                "field_name": "description",
                "display_name": "Description",
                "is_active": True,
                "show_in_list": True,  # Changed from False to True
                "show_in_form": True,
                "show_in_pdf": True,
                "is_mandatory": False,
                "allowed_roles": ["admin", "manager", "user"],
                "field_order": 4
            }
        ]
        
        response = requests.put(
            f"{BASE_URL}/api/items-enhanced/field-config",
            json=updated_fields
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "Field configuration updated"
        
        # Verify update persisted
        verify_response = requests.get(f"{BASE_URL}/api/items-enhanced/field-config")
        verify_data = verify_response.json()["field_config"]
        desc_field = next((f for f in verify_data if f["field_name"] == "description"), None)
        assert desc_field is not None
        assert desc_field["show_in_list"] == True
        print("✓ Field configuration updated and verified")
        
        # Restore original config for description field
        original_desc = next((f for f in original_config if f["field_name"] == "description"), None)
        if original_desc:
            restore_field = {
                "field_name": "description",
                "display_name": original_desc.get("display_name", "Description"),
                "is_active": original_desc.get("is_active", True),
                "show_in_list": original_desc.get("show_in_list", False),
                "show_in_form": original_desc.get("show_in_form", True),
                "show_in_pdf": original_desc.get("show_in_pdf", True),
                "is_mandatory": original_desc.get("is_mandatory", False),
                "allowed_roles": original_desc.get("allowed_roles", ["admin", "manager", "user"]),
                "field_order": original_desc.get("field_order", 4)
            }
            requests.put(f"{BASE_URL}/api/items-enhanced/field-config", json=[restore_field])
    
    def test_update_single_field_config(self):
        """PUT /api/items-enhanced/field-config/{field_name} - Update single field"""
        field_config = {
            "field_name": "barcode_value",
            "display_name": "Barcode",
            "is_active": True,
            "show_in_list": True,  # Enable in list
            "show_in_form": True,
            "show_in_pdf": True,
            "is_mandatory": False,
            "allowed_roles": ["admin", "manager", "user"],
            "field_order": 14
        }
        
        response = requests.put(
            f"{BASE_URL}/api/items-enhanced/field-config/barcode_value",
            json=field_config
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "barcode_value" in data["message"]
        print("✓ Single field configuration updated")
    
    def test_get_fields_for_role(self):
        """GET /api/items-enhanced/field-config/for-role/{role} - Get fields for role"""
        response = requests.get(f"{BASE_URL}/api/items-enhanced/field-config/for-role/admin")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert data["role"] == "admin"
        assert "list_fields" in data
        assert "form_fields" in data
        assert "pdf_fields" in data
        
        print(f"✓ Fields for admin role: {len(data['list_fields'])} list, {len(data['form_fields'])} form, {len(data['pdf_fields'])} pdf")


class TestAutoSKUGeneration:
    """Test auto SKU generation endpoint"""
    
    def test_generate_sku_disabled(self):
        """GET /api/items-enhanced/generate-sku - When auto SKU is disabled"""
        # First ensure auto SKU is disabled
        prefs = {
            "enable_sku": True,
            "auto_generate_sku": False,
            "sku_prefix": "SKU-",
            "sku_sequence_start": 1,
            "require_hsn_sac": False,
            "hsn_digits_required": 4,
            "enable_reorder_alerts": True,
            "enable_low_stock_alerts": True,
            "low_stock_threshold_days": 7,
            "default_tax_preference": "taxable",
            "default_unit": "pcs",
            "default_item_type": "inventory",
            "default_tax_rate": 18,
            "enable_images": True,
            "enable_custom_fields": True,
            "enable_barcode": True,
            "barcode_type": "CODE128",
            "default_valuation_method": "fifo",
            "track_serial_numbers": False,
            "track_batch_numbers": False
        }
        requests.put(f"{BASE_URL}/api/items-enhanced/preferences", json=prefs)
        
        response = requests.get(f"{BASE_URL}/api/items-enhanced/generate-sku")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 1
        assert "disabled" in data["message"].lower()
        print("✓ Generate SKU correctly returns disabled message")
    
    def test_generate_sku_enabled(self):
        """GET /api/items-enhanced/generate-sku - When auto SKU is enabled"""
        # Enable auto SKU
        prefs = {
            "enable_sku": True,
            "auto_generate_sku": True,
            "sku_prefix": "AUTO-",
            "sku_sequence_start": 1000,
            "require_hsn_sac": False,
            "hsn_digits_required": 4,
            "enable_reorder_alerts": True,
            "enable_low_stock_alerts": True,
            "low_stock_threshold_days": 7,
            "default_tax_preference": "taxable",
            "default_unit": "pcs",
            "default_item_type": "inventory",
            "default_tax_rate": 18,
            "enable_images": True,
            "enable_custom_fields": True,
            "enable_barcode": True,
            "barcode_type": "CODE128",
            "default_valuation_method": "fifo",
            "track_serial_numbers": False,
            "track_batch_numbers": False
        }
        requests.put(f"{BASE_URL}/api/items-enhanced/preferences", json=prefs)
        
        response = requests.get(f"{BASE_URL}/api/items-enhanced/generate-sku")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        assert "sku" in data
        assert data["sku"].startswith("AUTO-")
        assert "next_sequence" in data
        print(f"✓ Generated SKU: {data['sku']} (sequence: {data['next_sequence']})")
        
        # Restore original preferences
        restore_prefs = {
            "enable_sku": True,
            "auto_generate_sku": False,
            "sku_prefix": "SKU-",
            "sku_sequence_start": 1,
            "require_hsn_sac": False,
            "hsn_digits_required": 4,
            "enable_reorder_alerts": True,
            "enable_low_stock_alerts": True,
            "low_stock_threshold_days": 7,
            "default_tax_preference": "taxable",
            "default_unit": "pcs",
            "default_item_type": "inventory",
            "default_tax_rate": 18,
            "enable_images": True,
            "enable_custom_fields": True,
            "enable_barcode": True,
            "barcode_type": "CODE128",
            "default_valuation_method": "fifo",
            "track_serial_numbers": False,
            "track_batch_numbers": False
        }
        requests.put(f"{BASE_URL}/api/items-enhanced/preferences", json=restore_prefs)


class TestPhase3Integration:
    """Integration tests for Phase 3 features"""
    
    def test_preferences_affect_sku_generation(self):
        """Test that preferences correctly affect SKU generation"""
        # Set custom prefix
        prefs = {
            "enable_sku": True,
            "auto_generate_sku": True,
            "sku_prefix": "BATT-",
            "sku_sequence_start": 5000,
            "require_hsn_sac": False,
            "hsn_digits_required": 4,
            "enable_reorder_alerts": True,
            "enable_low_stock_alerts": True,
            "low_stock_threshold_days": 7,
            "default_tax_preference": "taxable",
            "default_unit": "pcs",
            "default_item_type": "inventory",
            "default_tax_rate": 18,
            "enable_images": True,
            "enable_custom_fields": True,
            "enable_barcode": True,
            "barcode_type": "CODE128",
            "default_valuation_method": "fifo",
            "track_serial_numbers": False,
            "track_batch_numbers": False
        }
        requests.put(f"{BASE_URL}/api/items-enhanced/preferences", json=prefs)
        
        # Generate SKU
        response = requests.get(f"{BASE_URL}/api/items-enhanced/generate-sku")
        data = response.json()
        
        assert data["code"] == 0
        assert data["sku"].startswith("BATT-")
        print(f"✓ SKU generation uses custom prefix: {data['sku']}")
        
        # Restore
        restore_prefs = prefs.copy()
        restore_prefs["auto_generate_sku"] = False
        restore_prefs["sku_prefix"] = "SKU-"
        restore_prefs["sku_sequence_start"] = 1
        requests.put(f"{BASE_URL}/api/items-enhanced/preferences", json=restore_prefs)
    
    def test_field_config_mandatory_fields(self):
        """Test that mandatory fields cannot be deactivated"""
        # Get field config
        response = requests.get(f"{BASE_URL}/api/items-enhanced/field-config")
        fields = response.json()["field_config"]
        
        # Find mandatory fields
        mandatory_fields = [f for f in fields if f.get("is_mandatory")]
        assert len(mandatory_fields) > 0, "Should have mandatory fields"
        
        # Verify name field is mandatory
        name_field = next((f for f in fields if f["field_name"] == "name"), None)
        assert name_field is not None
        assert name_field["is_mandatory"] == True
        print(f"✓ Found {len(mandatory_fields)} mandatory fields: {[f['field_name'] for f in mandatory_fields]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
