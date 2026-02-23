"""
Test All Settings Complete API Endpoints
Tests for the complete Zoho Books-style All Settings feature including:
- Users & Roles panel
- Roles & Permissions panel
- Custom Fields Builder
- Workflow Rules Builder
- Work Orders Settings
- Customers Settings
- EFI Settings
- Portal Settings
"""
import os
import pytest
import requests
import uuid
from typing import Optional

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = 'https://erp-expenses-bills.preview.emergentagent.com'

# Test organization ID
ORG_ID = "org_71f0df814d6d"


@pytest.fixture(scope="module")
def auth_headers():
    """Login and get auth token for all tests"""
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@battwheels.in",
        "password": "admin123"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    
    token = login_res.json().get("token")
    assert token, "No token in login response"
    
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Organization-ID": ORG_ID
    }


class TestUsersPanel:
    """Test Users & Roles panel - List users, invite user, edit role"""
    
    def test_list_organization_users(self, auth_headers):
        """GET /api/org/users - List all users in org"""
        res = requests.get(f"{BASE_URL}/api/org/users", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get users: {res.text}"
        
        data = res.json()
        assert "users" in data, "Response should contain 'users' key"
        assert "total" in data, "Response should contain 'total' key"
        assert isinstance(data["users"], list), "Users should be a list"
        
        # Check user structure
        if data["users"]:
            user_item = data["users"][0]
            assert "membership" in user_item, "User item should have 'membership'"
            assert "user" in user_item, "User item should have 'user' details"
            
            membership = user_item["membership"]
            assert "role" in membership, "Membership should have 'role'"
            assert "user_id" in membership, "Membership should have 'user_id'"
    
    def test_get_organization_roles(self, auth_headers):
        """GET /api/org/roles - Get available roles and permissions"""
        res = requests.get(f"{BASE_URL}/api/org/roles", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get roles: {res.text}"
        
        data = res.json()
        assert "roles" in data, "Response should contain 'roles' key"
        
        roles = data["roles"]
        assert len(roles) >= 7, f"Expected at least 7 roles, got {len(roles)}"
        
        # Check for expected roles
        role_names = [r["role"] for r in roles]
        expected_roles = ["owner", "admin", "manager", "dispatcher", "technician", "accountant", "viewer"]
        for expected in expected_roles:
            assert expected in role_names, f"Missing role: {expected}"
        
        # Check role structure
        for role in roles:
            assert "role" in role, "Role should have 'role' key"
            assert "name" in role, "Role should have 'name' key"
            assert "permissions" in role, "Role should have 'permissions' key"
            assert isinstance(role["permissions"], list), "Permissions should be a list"


class TestCustomFieldsBuilder:
    """Test Custom Fields Builder - CRUD operations"""
    
    def test_get_custom_fields_list(self, auth_headers):
        """GET /api/settings/custom-fields - Get list of custom fields"""
        res = requests.get(f"{BASE_URL}/api/settings/custom-fields", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get custom fields: {res.text}"
        
        data = res.json()
        assert isinstance(data, list), "Custom fields should return a list"
    
    def test_get_custom_fields_by_module(self, auth_headers):
        """GET /api/settings/custom-fields?module=vehicles - Filter by module"""
        res = requests.get(f"{BASE_URL}/api/settings/custom-fields?module=vehicles", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get custom fields: {res.text}"
        
        data = res.json()
        assert isinstance(data, list), "Custom fields should return a list"
        # If there are fields, they should be for vehicles module
        for field in data:
            if "module" in field:
                assert field["module"] == "vehicles", f"Wrong module: {field.get('module')}"
    
    def test_create_custom_field(self, auth_headers):
        """POST /api/settings/custom-fields - Create a custom field"""
        test_field = {
            "module": "vehicles",
            "field_name": f"test_field_{uuid.uuid4().hex[:8]}",
            "label": f"Test Field {uuid.uuid4().hex[:4]}",
            "data_type": "text",
            "description": "Test field for automated testing",
            "placeholder": "Enter value",
            "is_required": False,
            "is_searchable": True,
            "is_visible_in_list": True,
            "options": []
        }
        
        res = requests.post(f"{BASE_URL}/api/settings/custom-fields", headers=auth_headers, json=test_field)
        assert res.status_code == 200, f"Failed to create custom field: {res.text}"
        
        data = res.json()
        assert "field_id" in data, "Response should contain field_id"
        assert data["label"] == test_field["label"], "Label should match"
        assert data["module"] == test_field["module"], "Module should match"
        assert data["data_type"] == test_field["data_type"], "Data type should match"
        
        # Store field_id for cleanup
        return data["field_id"]
    
    def test_create_dropdown_custom_field(self, auth_headers):
        """POST /api/settings/custom-fields - Create a dropdown field"""
        test_field = {
            "module": "tickets",
            "field_name": f"test_dropdown_{uuid.uuid4().hex[:8]}",
            "label": f"Test Dropdown {uuid.uuid4().hex[:4]}",
            "data_type": "dropdown",
            "description": "Test dropdown for automated testing",
            "is_required": False,
            "is_searchable": True,
            "is_visible_in_list": True,
            "options": [
                {"value": "option_1", "label": "Option 1", "sort_order": 0},
                {"value": "option_2", "label": "Option 2", "sort_order": 1},
                {"value": "option_3", "label": "Option 3", "sort_order": 2}
            ]
        }
        
        res = requests.post(f"{BASE_URL}/api/settings/custom-fields", headers=auth_headers, json=test_field)
        assert res.status_code == 200, f"Failed to create dropdown field: {res.text}"
        
        data = res.json()
        assert "field_id" in data, "Response should contain field_id"
        assert data["data_type"] == "dropdown", "Data type should be dropdown"
        # Options should be preserved
        if "options" in data:
            assert len(data["options"]) >= 3, "Should have at least 3 options"
    
    def test_delete_custom_field(self, auth_headers):
        """DELETE /api/settings/custom-fields/{field_id} - Delete a field"""
        # First create a field to delete
        test_field = {
            "module": "vehicles",
            "field_name": f"to_delete_{uuid.uuid4().hex[:8]}",
            "label": f"To Delete {uuid.uuid4().hex[:4]}",
            "data_type": "text",
            "is_required": False
        }
        
        create_res = requests.post(f"{BASE_URL}/api/settings/custom-fields", headers=auth_headers, json=test_field)
        assert create_res.status_code == 200, f"Failed to create field: {create_res.text}"
        
        field_id = create_res.json().get("field_id")
        assert field_id, "No field_id in create response"
        
        # Now delete it
        delete_res = requests.delete(f"{BASE_URL}/api/settings/custom-fields/{field_id}", headers=auth_headers)
        assert delete_res.status_code == 200, f"Failed to delete field: {delete_res.text}"


class TestWorkflowRulesBuilder:
    """Test Workflow Rules Builder - CRUD operations"""
    
    def test_get_workflow_rules_list(self, auth_headers):
        """GET /api/settings/workflows - Get list of workflow rules"""
        res = requests.get(f"{BASE_URL}/api/settings/workflows", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get workflows: {res.text}"
        
        data = res.json()
        assert isinstance(data, list), "Workflows should return a list"
    
    def test_get_workflow_rules_by_module(self, auth_headers):
        """GET /api/settings/workflows?module=tickets - Filter by module"""
        res = requests.get(f"{BASE_URL}/api/settings/workflows?module=tickets", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get workflows: {res.text}"
        
        data = res.json()
        assert isinstance(data, list), "Workflows should return a list"
    
    def test_create_workflow_rule(self, auth_headers):
        """POST /api/settings/workflows - Create a workflow rule"""
        test_rule = {
            "module": "tickets",
            "name": f"Test Workflow {uuid.uuid4().hex[:4]}",
            "description": "Test workflow rule for automated testing",
            "trigger_type": "on_create",
            "conditions": [
                {"field": "priority", "operator": "equals", "value": "high", "logic": "and"}
            ],
            "actions": [
                {
                    "action_type": "email_alert",
                    "name": "Send alert email",
                    "email_alert": {
                        "subject": "High Priority Ticket Created",
                        "body": "A new high priority ticket has been created.",
                        "to_emails": ["test@example.com"]
                    }
                }
            ],
            "is_active": True
        }
        
        res = requests.post(f"{BASE_URL}/api/settings/workflows", headers=auth_headers, json=test_rule)
        assert res.status_code == 200, f"Failed to create workflow: {res.text}"
        
        data = res.json()
        assert "rule_id" in data, "Response should contain rule_id"
        assert data["name"] == test_rule["name"], "Name should match"
        assert data["module"] == test_rule["module"], "Module should match"
        assert data["trigger_type"] == test_rule["trigger_type"], "Trigger type should match"
        
        return data["rule_id"]
    
    def test_update_workflow_rule(self, auth_headers):
        """PATCH /api/settings/workflows/{rule_id} - Update a workflow rule"""
        # First create a rule
        test_rule = {
            "module": "tickets",
            "name": f"To Update {uuid.uuid4().hex[:4]}",
            "trigger_type": "on_create",
            "conditions": [],
            "actions": [],
            "is_active": True
        }
        
        create_res = requests.post(f"{BASE_URL}/api/settings/workflows", headers=auth_headers, json=test_rule)
        assert create_res.status_code == 200, f"Failed to create workflow: {create_res.text}"
        
        rule_id = create_res.json().get("rule_id")
        assert rule_id, "No rule_id in create response"
        
        # Update it
        update_data = {
            "is_active": False,
            "description": "Updated description"
        }
        
        update_res = requests.patch(f"{BASE_URL}/api/settings/workflows/{rule_id}", headers=auth_headers, json=update_data)
        assert update_res.status_code == 200, f"Failed to update workflow: {update_res.text}"
        
        data = update_res.json()
        assert data["is_active"] == False, "is_active should be False"
    
    def test_delete_workflow_rule(self, auth_headers):
        """DELETE /api/settings/workflows/{rule_id} - Delete a workflow rule"""
        # First create a rule to delete
        test_rule = {
            "module": "tickets",
            "name": f"To Delete {uuid.uuid4().hex[:4]}",
            "trigger_type": "on_create",
            "conditions": [],
            "actions": [],
            "is_active": False
        }
        
        create_res = requests.post(f"{BASE_URL}/api/settings/workflows", headers=auth_headers, json=test_rule)
        assert create_res.status_code == 200, f"Failed to create workflow: {create_res.text}"
        
        rule_id = create_res.json().get("rule_id")
        
        # Now delete it
        delete_res = requests.delete(f"{BASE_URL}/api/settings/workflows/{rule_id}", headers=auth_headers)
        assert delete_res.status_code == 200, f"Failed to delete workflow: {delete_res.text}"


class TestWorkOrderSettings:
    """Test Work Orders Settings panel"""
    
    def test_get_work_orders_settings(self, auth_headers):
        """GET /api/settings/modules/work-orders - Get work orders settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/work-orders", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get work orders settings: {res.text}"
        
        data = res.json()
        assert isinstance(data, dict), "Work orders settings should be a dict"
        # Settings exist as dict - could be empty initially or have default values
    
    def test_update_work_orders_settings(self, auth_headers):
        """PATCH /api/settings/modules/work-orders - Update work orders settings"""
        update_data = {
            "labor_rate": 850.00,
            "approval_threshold": 25000,
            "require_approval_above_threshold": True,
            "enable_time_tracking": True,
            "default_priority": "normal"
        }
        
        res = requests.patch(f"{BASE_URL}/api/settings/modules/work-orders", headers=auth_headers, json=update_data)
        assert res.status_code == 200, f"Failed to update work orders settings: {res.text}"
        
        data = res.json()
        # Verify updates
        if "labor_rate" in data:
            assert data["labor_rate"] == 850.00, "Labor rate should be updated"


class TestCustomersSettings:
    """Test Customers Settings panel"""
    
    def test_get_customers_settings(self, auth_headers):
        """GET /api/settings/modules/customers - Get customers settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/customers", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get customers settings: {res.text}"
        
        data = res.json()
        assert isinstance(data, dict), "Customers settings should be a dict"
        
        # Check expected fields
        expected_fields = ["default_credit_limit", "default_payment_terms",
                          "enable_customer_portal", "portal_permissions",
                          "require_gst_for_b2b"]
        found_fields = [f for f in expected_fields if f in data]
        assert len(found_fields) >= 1, f"Should have at least one customer setting. Got: {list(data.keys())}"
    
    def test_update_customers_settings(self, auth_headers):
        """PATCH /api/settings/modules/customers - Update customers settings"""
        update_data = {
            "default_credit_limit": 100000,
            "default_payment_terms": 30,
            "enable_customer_portal": True,
            "require_gst_for_b2b": True
        }
        
        res = requests.patch(f"{BASE_URL}/api/settings/modules/customers", headers=auth_headers, json=update_data)
        assert res.status_code == 200, f"Failed to update customers settings: {res.text}"
        
        data = res.json()
        # Verify updates
        if "default_credit_limit" in data:
            assert data["default_credit_limit"] == 100000, "Credit limit should be updated"


class TestEFISettings:
    """Test EFI (Failure Intelligence) Settings panel"""
    
    def test_get_efi_settings(self, auth_headers):
        """GET /api/settings/modules/efi - Get EFI settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/efi", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get EFI settings: {res.text}"
        
        data = res.json()
        assert isinstance(data, dict), "EFI settings should be a dict"
        
        # Check actual fields from response
        expected_fields = ["enable_ai_diagnosis", "enable_knowledge_base", 
                          "enable_parts_recommendation", "auto_suggest_similar_cases",
                          "confidence_threshold"]
        found_fields = [f for f in expected_fields if f in data]
        assert len(found_fields) >= 1, f"Should have at least one EFI setting. Got: {list(data.keys())}"
    
    def test_update_efi_settings(self, auth_headers):
        """PATCH /api/settings/modules/efi - Update EFI settings"""
        update_data = {
            "enable_ai_diagnosis": True,
            "enable_knowledge_base": True,
            "enable_parts_recommendation": True,
            "auto_suggest_similar_cases": True,
            "confidence_threshold": 0.75
        }
        
        res = requests.patch(f"{BASE_URL}/api/settings/modules/efi", headers=auth_headers, json=update_data)
        assert res.status_code == 200, f"Failed to update EFI settings: {res.text}"
        
        data = res.json()
        # Verify updates
        if "enable_ai_diagnosis" in data:
            assert data["enable_ai_diagnosis"] == True, "AI diagnosis should be enabled"


class TestPortalSettings:
    """Test Customer Portal Settings panel"""
    
    def test_get_portal_settings(self, auth_headers):
        """GET /api/settings/modules/portal - Get portal settings"""
        res = requests.get(f"{BASE_URL}/api/settings/modules/portal", headers=auth_headers)
        assert res.status_code == 200, f"Failed to get portal settings: {res.text}"
        
        data = res.json()
        assert isinstance(data, dict), "Portal settings should be a dict"
        
        # Check actual fields from response
        expected_fields = ["enable_customer_portal", "enable_vendor_portal",
                          "allow_ticket_creation", "allow_invoice_download",
                          "allow_estimate_approval"]
        found_fields = [f for f in expected_fields if f in data]
        assert len(found_fields) >= 1, f"Should have at least one portal setting. Got: {list(data.keys())}"
    
    def test_update_portal_settings(self, auth_headers):
        """PATCH /api/settings/modules/portal - Update portal settings"""
        update_data = {
            "enable_customer_portal": True,
            "enable_vendor_portal": False,
            "allow_ticket_creation": True,
            "allow_invoice_download": True,
            "allow_estimate_approval": True
        }
        
        res = requests.patch(f"{BASE_URL}/api/settings/modules/portal", headers=auth_headers, json=update_data)
        assert res.status_code == 200, f"Failed to update portal settings: {res.text}"
        
        data = res.json()
        # Verify updates
        if "enable_customer_portal" in data:
            assert data["enable_customer_portal"] == True, "Customer portal should be enabled"


class TestSettingsNavigation:
    """Test settings navigation and category structure"""
    
    def test_categories_structure(self, auth_headers):
        """GET /api/settings/categories - Verify complete structure"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        assert res.status_code == 200, f"Failed to get categories: {res.text}"
        
        data = res.json()
        categories = data.get("categories", [])
        
        # Check 8 categories exist
        assert len(categories) == 8, f"Expected 8 categories, got {len(categories)}"
        
        # Check each category has items with proper structure
        for cat in categories:
            assert "id" in cat, "Category should have 'id'"
            assert "name" in cat, "Category should have 'name'"
            assert "items" in cat, "Category should have 'items'"
            assert len(cat["items"]) > 0, f"Category {cat['name']} should have items"
            
            for item in cat["items"]:
                assert "id" in item, "Item should have 'id'"
                assert "name" in item, "Item should have 'name'"
                assert "path" in item, "Item should have 'path'"
    
    def test_users_roles_category_items(self, auth_headers):
        """Verify Users & Roles category has correct items"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        data = res.json()
        
        users_cat = next((c for c in data["categories"] if c["id"] == "users"), None)
        assert users_cat is not None, "Users category should exist"
        
        item_ids = [i["id"] for i in users_cat["items"]]
        assert "users" in item_ids, "Should have 'users' item"
        assert "roles" in item_ids, "Should have 'roles' item"
    
    def test_customization_category_items(self, auth_headers):
        """Verify Customization category has custom-fields and workflows"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        data = res.json()
        
        custom_cat = next((c for c in data["categories"] if c["id"] == "customization"), None)
        assert custom_cat is not None, "Customization category should exist"
        
        item_ids = [i["id"] for i in custom_cat["items"]]
        assert "custom-fields" in item_ids, "Should have 'custom-fields' item"
    
    def test_automation_category_has_workflows(self, auth_headers):
        """Verify Automation category has workflows"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        data = res.json()
        
        auto_cat = next((c for c in data["categories"] if c["id"] == "automation"), None)
        assert auto_cat is not None, "Automation category should exist"
        
        item_ids = [i["id"] for i in auto_cat["items"]]
        assert "workflows" in item_ids, "Should have 'workflows' item"
    
    def test_modules_category_has_all_modules(self, auth_headers):
        """Verify Module Settings has all expected modules"""
        res = requests.get(f"{BASE_URL}/api/settings/categories")
        data = res.json()
        
        modules_cat = next((c for c in data["categories"] if c["id"] == "modules"), None)
        assert modules_cat is not None, "Modules category should exist"
        
        item_ids = [i["id"] for i in modules_cat["items"]]
        expected_modules = ["work-orders", "customers", "efi", "portal"]
        for mod in expected_modules:
            assert mod in item_ids, f"Should have '{mod}' module item"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
