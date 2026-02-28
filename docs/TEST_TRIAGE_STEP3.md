# STEP 3 — BUCKET A ANALYSIS (83 files)

## Summary by Root Cause & Fix Effort

| Root Cause | Count | Fix Effort |
|-----------|-------|------------|
| Already passing (Phase 0 / correct config) | 4 | TRIVIAL — just add to core |
| Missing sys.path (unit tests) | 4 | TRIVIAL — add sys.path insert |
| Wrong credentials (admin@battwheels.in) | 44 | TRIVIAL — change to dev@battwheels.internal |
| No auth mechanism at all | 24 | MODERATE — need to add login fixture |
| Hardcoded JWT tokens | 2 | MODERATE — replace with login-based auth |
| ENV config (other) | 4 | TRIVIAL — fix env var sourcing |
| API changes (code evolved past tests) | 1 | MODERATE — update test expectations |
| **TOTAL** | **83** | **TRIVIAL: 56, MODERATE: 27** |

---

### test_csrf_middleware.py (6 tests) — TRIVIAL
- **Root Cause:** Already correct credentials
- **Test Functions:**
  - test_get_sets_csrf_cookie
  - test_post_with_bearer_bypasses_csrf
  - test_auth_login_bypasses_csrf
  - test_auth_forgot_password_bypasses_csrf
  - test_post_with_cookie_no_csrf_blocked
  - test_post_with_csrf_mismatch_blocked

### test_sanitization_middleware.py (8 tests) — TRIVIAL
- **Root Cause:** Already correct credentials
- **Test Functions:**
  - test_login_strips_html_from_email
  - test_password_with_special_chars_not_corrupted
  - test_strips_script_tags
  - test_strips_img_onerror
  - test_password_field_exempt
  - test_new_password_field_exempt
  - test_nested_dict_sanitization
  - test_list_sanitization

### test_gstr3b_rcm.py (4 tests) — TRIVIAL
- **Root Cause:** Already correct credentials
- **Test Functions:**
  - test_report_has_section_3_1_d
  - test_report_has_table_4a_rcm
  - test_summary_has_rcm_liability
  - test_zero_rcm_when_no_rcm_bills

### test_calculations_regression.py (29 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_basic_line_item_exclusive_tax
  - test_line_item_inclusive_tax
  - test_line_item_no_tax
  - test_line_item_cgst_sgst_split
  - test_line_item_igst
  - test_basic_invoice_totals
  - test_invoice_with_discount
  - test_invoice_with_shipping
  - test_invoice_with_adjustment
  - test_intra_state_tax_breakdown
  - test_inter_state_tax_breakdown
  - test_reverse_tax_calculation
  - test_oldest_first_allocation
  - test_proportional_allocation
  - test_overpayment_handling
  - test_unapply_payment
  - test_current_bucket
  - test_overdue_buckets
  - test_aging_summary
  - test_valid_gst_number
  - test_invalid_gst_number
  - test_empty_gst_number
  - test_round_half_up
  - test_round_negative
  - test_round_whole_numbers
  - test_zero_quantity
  - test_zero_rate
  - test_very_large_numbers
  - test_decimal_precision

### test_efi_guidance.py (22 tests) — TRIVIAL
- **Root Cause:** Missing sys.path for backend imports
- **Test Functions:**
  - test_hinglish_system_prompt_contains_keywords
  - test_ask_back_prompt_structure
  - test_quick_mode_instructions
  - test_deep_mode_instructions
  - test_generate_flowchart
  - test_flowchart_max_nodes
  - test_generate_gauge_spec
  - test_gauge_zones_coloring
  - test_generate_bar_chart_spec
  - test_bar_chart_max_items
  - test_battery_not_charging_flow
  - test_motor_not_running_flow
  - test_range_anxiety_flow
async   - test_missing_info_triggers_ask_back
async   - test_complete_context_no_ask_back
  - test_default_guidance_enabled
async   - test_is_enabled_check
  - test_high_confidence_with_many_sources
  - test_low_confidence_with_no_sources
async   - test_battery_fix_suggests_battery_parts
  - test_mermaid_diagram_has_required_fields
  - test_chart_spec_has_required_fields

### test_efi_intelligence.py (15 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_calculate_score_model_match
  - test_calculate_score_dtc_match
  - test_calculate_score_success_rate
async   - test_get_safe_checklist_battery
async   - test_should_escalate_low_confidence
async   - test_capture_ticket_closure
async   - test_create_draft_failure_card
async   - test_pattern_detection_trigger
  - test_snapshot_model_creation
  - test_context_hash_computation
  - test_feedback_model_creation
  - test_failure_card_creation
  - test_failure_card_with_metrics
  - test_alert_creation
async   - test_failure_cards_tenant_filtered

### test_entitlement_service.py (14 tests) — TRIVIAL
- **Root Cause:** Missing sys.path for backend imports
- **Test Functions:**
  - test_feature_plan_requirements_defined
  - test_plan_hierarchy_defined
  - test_get_minimum_plan_for_feature
  - test_upgrade_suggestion
  - test_feature_not_available_exception
  - test_usage_limit_exceeded_exception
  - test_subscription_required_exception
  - test_subscription_expired_exception
  - test_require_feature_returns_callable
  - test_require_usage_limit_returns_callable
  - test_require_subscription_returns_callable
  - test_feature_gate_decorator_exists
  - test_feature_gate_creates_wrapper
async   - test_func

### test_knowledge_brain.py (16 tests) — TRIVIAL
- **Root Cause:** Missing sys.path for backend imports
- **Test Functions:**
  - test_llm_provider_factory_default
  - test_llm_provider_factory_get_provider
  - test_gemini_provider_model_name
  - test_gemini_provider_custom_model
  - test_provider_availability_without_key
  - test_get_llm_provider_helper
  - test_default_ai_config
async   - test_get_tenant_config_returns_defaults
async   - test_is_feature_enabled
  - test_zendesk_bridge_stub
async   - test_zendesk_bridge_create_ticket_stub
async   - test_escalation_creation
  - test_category_determination
async   - test_knowledge_search_respects_tenant_scope
async   - test_rag_pipeline_with_no_sources
async   - test_escalation_creates_timeline_entry

### test_ai_diagnostic_assistant.py (10 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_ai_health_endpoint_available
  - test_diagnose_battery_issue_admin
  - test_diagnose_motor_issue_technician
  - test_diagnose_electrical_issue
  - test_diagnose_charging_issue
  - test_diagnose_with_dtc_codes
  - test_diagnose_minimal_input
  - test_admin_login_success
  - test_technician_login_success
  - test_invalid_login_rejected

### test_all_settings.py (17 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_get_categories_returns_8
  - test_categories_have_required_structure
  - test_expected_category_ids_present
  - test_get_all_settings
  - test_get_gst_settings
  - test_update_gst_settings
  - test_get_tds_settings
  - test_get_msme_settings
  - test_get_vehicle_settings
  - test_get_ticket_settings
  - test_get_billing_settings
  - test_get_inventory_settings
  - test_get_efi_settings
  - test_get_custom_fields
  - test_get_workflows
  - test_settings_require_auth
  - test_settings_require_org

### test_all_settings_complete.py (25 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_list_organization_users
  - test_get_organization_roles
  - test_get_custom_fields_list
  - test_get_custom_fields_by_module
  - test_create_custom_field
  - test_create_dropdown_custom_field
  - test_delete_custom_field
  - test_get_workflow_rules_list
  - test_get_workflow_rules_by_module
  - test_create_workflow_rule
  - test_update_workflow_rule
  - test_delete_workflow_rule
  - test_get_work_orders_settings
  - test_update_work_orders_settings
  - test_get_customers_settings
  - test_update_customers_settings
  - test_get_efi_settings
  - test_update_efi_settings
  - test_get_portal_settings
  - test_update_portal_settings
  - test_categories_structure
  - test_users_roles_category_items
  - test_customization_category_items
  - test_automation_category_has_workflows
  - test_modules_category_has_all_modules

### test_audit_logging.py (15 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_audit_entry_exists
  - test_schema_complete
  - test_before_snapshot_null_for_create
  - test_after_snapshot_has_data
  - test_org_id_populated
  - test_timestamp_present
  - test_update_creates_audit
  - test_before_snapshot_present
  - test_after_snapshot_present
  - test_void_creates_audit
  - test_void_before_snapshot
  - test_void_after_snapshot
  - test_journal_audit_exists
  - test_user_role_not_empty
  - test_user_role_is_valid_role

### test_banking_stock_transfers.py (22 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_seed_all_data
  - test_list_bank_accounts
  - test_get_single_bank_account
  - test_dashboard_stats
  - test_list_chart_of_accounts
  - test_create_chart_account
  - test_trial_balance_report
  - test_profit_loss_report
  - test_balance_sheet_report
  - test_cash_flow_report
  - test_list_journal_entries
  - test_create_journal_entry_balanced
  - test_create_journal_entry_unbalanced_fails
  - test_reconciliation_history
  - test_start_reconciliation
  - test_list_stock_transfers
  - test_stock_transfers_stats
  - test_stock_transfers_filter_by_status
  - test_list_warehouses
  - test_list_stock
  - test_stock_transfers_page_data
  - test_accountant_page_data

### test_bills_inventory_enhanced.py (38 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_bills_summary
  - test_create_bill
  - test_list_bills
  - test_get_bill_detail
  - test_open_bill
  - test_record_payment
  - test_get_bill_payments
  - test_clone_bill
  - test_get_po_summary
  - test_create_purchase_order
  - test_list_purchase_orders
  - test_get_purchase_order_detail
  - test_issue_purchase_order
  - test_receive_purchase_order
  - test_convert_po_to_bill
  - test_aging_report
  - test_vendor_wise_report
  - test_get_inventory_summary
  - test_list_warehouses
  - test_create_warehouse
  - test_get_warehouse_detail
  - test_create_variant
  - test_list_variants
  - test_get_variant_detail
  - test_create_bundle
  - test_list_bundles
  - test_get_bundle_detail
  - test_create_serial_number
  - test_create_batch
  - test_list_serial_batches
  - test_add_stock_adjustment
  - test_subtract_stock_adjustment
  - test_list_adjustments
  - test_stock_summary_report
  - test_low_stock_report
  - test_valuation_report
  - test_movement_report
  - test_cleanup_test_data

### test_complaint_dashboard.py (19 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_admin_login
  - test_technician_login
  - test_get_all_tickets
  - test_get_tickets_by_status_open
  - test_get_tickets_by_status_technician_assigned
  - test_get_tickets_by_status_in_progress
  - test_get_tickets_by_status_resolved
  - test_unauthorized_access
  - test_get_ticket_by_id
  - test_get_nonexistent_ticket
  - test_get_technicians
  - test_assign_technician_to_ticket
  - test_update_ticket_status_to_in_progress
  - test_update_ticket_with_estimated_items
  - test_get_inventory
  - test_get_services
  - test_kpi_counts
  - test_create_ticket
  - test_invoice_endpoint_exists

### test_composite_items_invoice_settings.py (24 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_summary
  - test_list_composite_items
  - test_list_by_type_kit
  - test_get_inventory_items
  - test_create_composite_item
  - test_get_composite_item
  - test_check_build_availability
  - test_build_composite_item_insufficient_stock
  - test_delete_composite_item
  - test_get_reminder_settings
  - test_update_reminder_settings
  - test_get_late_fee_settings
  - test_update_late_fee_settings
  - test_get_overdue_invoices
  - test_get_due_soon_invoices
  - test_get_aging_report
  - test_get_recurring_summary
  - test_list_recurring_invoices
  - test_create_recurring_invoice
  - test_get_recurring_invoice
  - test_generate_invoice_now
  - test_stop_recurring_invoice
  - test_resume_recurring_invoice
  - test_delete_recurring_invoice

### test_contact_integration.py (23 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_contact_search_all
  - test_contact_search_with_query
  - test_contact_search_by_type_customer
  - test_contact_search_by_type_vendor
  - test_contact_search_includes_source
  - test_get_contact_for_transaction
  - test_get_contact_for_transaction_not_found
  - test_get_contact_transactions
  - test_get_contact_transactions_filtered_by_type
  - test_get_contact_transactions_pagination
  - test_get_contact_balance_summary
  - test_invoices_with_contacts
  - test_bills_with_contacts
  - test_estimates_with_contacts
  - test_purchase_orders_with_contacts
  - test_migration_dry_run
  - test_link_transactions_dry_run
  - test_report_customers_by_revenue
  - test_report_vendors_by_expense
  - test_report_receivables_aging
  - test_report_payables_aging
  - test_invoices_filter_by_status
  - test_invoices_filter_by_customer

### test_contacts_enhanced.py (37 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_list_tags
  - test_create_tag
  - test_get_tag_by_id
  - test_update_tag
  - test_duplicate_tag_name_rejected
  - test_list_contacts
  - test_get_contacts_summary
  - test_get_indian_states
  - test_create_customer_contact
  - test_create_vendor_contact
  - test_create_both_type_contact
  - test_get_contact_by_id
  - test_update_contact
  - test_filter_contacts_by_type
  - test_search_contacts
  - test_valid_gstin
  - test_invalid_gstin_format
  - test_gstin_state_detection
  - test_add_contact_person
  - test_list_contact_persons
  - test_update_contact_person
  - test_add_billing_address
  - test_add_shipping_address
  - test_list_addresses
  - test_filter_addresses_by_type
  - test_enable_portal_access
  - test_disable_portal_access
  - test_email_statement
  - test_statement_history
  - test_deactivate_contact
  - test_activate_contact
  - test_customers_endpoint
  - test_vendors_endpoint
  - test_delete_test_persons
  - test_delete_test_addresses
  - test_delete_test_contacts
  - test_delete_test_tags

### test_contacts_invoices_enhanced.py (35 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_summary_returns_correct_counts
  - test_summary_with_contact_type_filter
  - test_list_all_contacts
  - test_list_filter_by_customer_type
  - test_list_filter_by_vendor_type
  - test_list_with_search
  - test_list_pagination
  - test_create_customer_contact
  - test_create_vendor_contact
  - test_create_both_type_contact
  - test_contact_detail_returns_persons_addresses_balance_aging
  - test_contact_detail_not_found
  - test_enable_portal
  - test_disable_portal
  - test_email_statement
  - test_summary_returns_statistics
  - test_summary_with_period_filter
  - test_create_invoice_with_line_items
  - test_list_invoices
  - test_list_invoices_with_filters
  - test_record_payment
  - test_record_full_payment
  - test_draft_to_sent
  - test_send_invoice_email
  - test_clone_invoice
  - test_void_invoice
  - test_aging_report
  - test_customer_wise_report
  - test_monthly_report
  - test_list_tags
  - test_create_tag
  - test_get_indian_states
  - test_validate_valid_gstin
  - test_validate_invalid_gstin
  - test_customers_enhanced_redirect

### test_convert_invoice_stock_transfers.py (24 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_ticket
  - test_estimate_for_conversion
  - test_warehouses
  - test_item_with_stock
  - test_convert_approved_estimate_to_invoice
  - test_cannot_convert_draft_estimate
  - test_cannot_convert_same_estimate_twice
  - test_convert_nonexistent_estimate
  - test_create_stock_transfer
  - test_cannot_transfer_to_same_warehouse
  - test_cannot_transfer_insufficient_stock
  - test_ship_transfer
  - test_cannot_ship_non_draft_transfer
  - test_receive_transfer
  - test_cannot_receive_non_transit_transfer
  - test_void_draft_transfer
  - test_void_in_transit_transfer_returns_stock
  - test_void_received_transfer_reverses_both
  - test_cannot_void_already_voided
  - test_get_stats_summary
  - test_get_stats_with_org_filter
  - test_list_transfers
  - test_list_transfers_by_status
  - test_get_single_transfer

### test_customer_portal.py (19 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_customer_login_success
  - test_admin_login_success
  - test_invalid_login
  - test_get_dashboard
  - test_dashboard_requires_auth
  - test_get_vehicles
  - test_vehicles_requires_auth
  - test_get_service_history
  - test_service_history_with_status_filter
  - test_service_history_with_limit
  - test_get_invoices
  - test_get_payments_due
  - test_get_amc_subscriptions
  - test_get_available_amc_plans
  - test_admin_get_amc_plans
  - test_admin_get_amc_subscriptions
  - test_admin_get_amc_analytics
  - test_customer_cannot_access_admin_amc_routes
  - test_admin_can_access_customer_portal

### test_customer_portal_auth.py (21 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_portal_login_success
  - test_portal_login_invalid_token
  - test_portal_login_short_token
  - test_dashboard_with_header
  - test_dashboard_with_query_param
  - test_invoices_with_header
  - test_invoices_with_query_param
  - test_estimates_with_header
  - test_estimates_with_query_param
  - test_profile_with_header
  - test_profile_with_query_param
  - test_statement_with_header
  - test_statement_with_query_param
  - test_missing_session_token
  - test_invalid_session_token_header
  - test_invalid_session_token_query
  - test_enable_portal_for_contact
  - test_enable_portal_invalid_contact
  - test_logout_with_header
  - test_session_info_with_header
  - test_session_info_with_query_param

### test_customers_enhanced.py (52 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_settings
  - test_get_summary
  - test_check_sync
  - test_validate_valid_gstin_delhi
  - test_validate_valid_gstin_maharashtra
  - test_validate_invalid_gstin_format
  - test_validate_invalid_state_code
  - test_create_customer_basic
  - test_create_customer_with_gstin
  - test_create_customer_invalid_gstin
  - test_list_customers
  - test_list_customers_with_search
  - test_list_customers_by_gst_treatment
  - test_get_customer_detail
  - test_update_customer
  - test_get_customer_not_found
  - test_add_contact_person
  - test_add_second_person
  - test_get_customer_persons
  - test_update_person
  - test_set_primary_person
  - test_add_billing_address
  - test_add_shipping_address
  - test_get_customer_addresses
  - test_update_address
  - test_enable_portal
  - test_disable_portal
  - test_get_statement
  - test_email_statement
  - test_deactivate_customer
  - test_activate_customer
  - test_add_credit
  - test_get_credits
  - test_create_refund
  - test_refund_insufficient_credits
  - test_create_tag
  - test_get_all_tags
  - test_add_tag_to_customer
  - test_remove_tag_from_customer
  - test_get_transactions
  - test_get_transactions_by_type
  - test_bulk_activate
  - test_bulk_add_tag
  - test_report_by_segment
  - test_report_top_customers
  - test_report_aging_summary
  - test_quick_estimate
  - test_create_customer_for_delete_test
  - test_create_estimate_for_customer
  - test_delete_customer_with_transactions
  - test_delete_test_customers
  - test_delete_test_tags

### test_data_management.py (14 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_get_data_counts_success
  - test_get_data_counts_requires_org_id
  - test_test_connection_success
  - test_get_sync_status
  - test_sanitization_audit_mode
  - test_sanitization_invalid_mode
  - test_full_sync_starts_background_job
  - test_fix_negative_stock
  - test_cleanup_orphaned_records
  - test_sync_single_module
  - test_validate_integrity
  - test_validate_completeness
  - test_get_sanitization_history
  - test_get_sync_history

### test_efi_guided.py (21 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_seed_failure_cards
  - test_generate_all_embeddings
  - test_embedding_status
  - test_list_failure_cards
  - test_list_failure_cards_by_subsystem
  - test_get_single_failure_card
  - test_ticket_id
  - test_get_suggestions_for_ticket
  - test_suggestions_include_confidence_scores
  - test_ticket_id
  - test_start_diagnostic_session
  - test_session_without_decision_tree_fails
  - test_get_session
  - test_record_pass_outcome
  - test_record_fail_outcome
  - test_estimate_requires_completed_session
  - test_get_decision_tree
  - test_suggestions_requires_auth
  - test_session_start_requires_auth
  - test_seed_requires_admin
  - test_embeddings_generate_requires_admin

### test_efi_intelligence_api.py (15 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_snapshot_info_non_existing_ticket
  - test_check_context_requires_ticket
  - test_feedback_summary_endpoint
  - test_create_failure_card
  - test_get_failure_cards_with_tenant_isolation
  - test_approve_failure_card
  - test_rank_causes_returns_top_3
  - test_low_confidence_returns_safe_checklist
  - test_ranking_weights_model_match_higher
  - test_capture_ticket_closure
  - test_learning_stats
  - test_get_risk_alerts
  - test_risk_alerts_filter_by_status
  - test_get_dashboard_summary
  - test_guidance_status

### test_efi_module.py (24 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_admin_login_success
  - test_failure_card_id
  - test_create_failure_card_with_event_emission
  - test_list_failure_cards
  - test_list_failure_cards_with_filters
  - test_get_single_failure_card
  - test_get_nonexistent_failure_card
  - test_update_failure_card
  - test_get_confidence_history
  - test_match_failure_basic
  - test_match_failure_with_subsystem_hint
  - test_match_failure_empty_results
  - test_ticket_id
  - test_match_ticket_to_failures
  - test_match_nonexistent_ticket
  - test_get_ticket_matches
  - test_get_analytics_overview
  - test_get_effectiveness_report
  - test_approve_failure_card
  - test_approve_already_approved_card
  - test_deprecate_failure_card
  - test_ticket_creation_triggers_ai_matching
  - test_full_ticket_lifecycle_with_efi
  - test_cleanup_verification

### test_efi_search_embeddings.py (21 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_get_embedding_status
  - test_generate_embeddings_disabled
  - test_match_with_symptom_text_and_error_codes
  - test_match_with_subsystem_hint
  - test_match_with_vehicle_info
  - test_match_with_temperature_and_load_conditions
  - test_match_stages_fallback
  - test_match_empty_results_for_random_text
  - test_hybrid_search_uses_text_search
  - test_error_code_matching_boost
  - test_keyword_expansion_ev_synonyms
  - test_create_failure_card_full
  - test_list_failure_cards_pagination
  - test_list_failure_cards_filters
  - test_get_single_failure_card
  - test_update_failure_card
  - test_approve_failure_card
  - test_search_by_text_in_list
  - test_search_by_error_code
  - test_search_by_signature_hash
  - test_cleanup_verification

### test_employee_creation.py (7 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_admin_login
  - test_create_employee_with_correct_fields
  - test_get_employees_list
  - test_new_employee_can_login
  - test_create_employee_with_all_fields
  - test_create_employee_missing_required_fields
  - test_create_employee_duplicate_email

### test_employee_module.py (21 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_admin_login
  - test_employee_login
  - test_get_employees_list
  - test_get_employees_filter_by_department
  - test_get_employees_filter_by_status
  - test_get_single_employee
  - test_get_nonexistent_employee
  - test_get_managers_list
  - test_get_roles_list
  - test_create_employee_full
  - test_create_employee_duplicate_email
  - test_update_employee
  - test_update_employee_salary_recalculates_deductions
  - test_delete_employee_soft_delete
  - test_pf_deduction_calculation
  - test_esi_deduction_calculation
  - test_esi_not_applied_above_threshold
  - test_professional_tax_calculation
  - test_unauthorized_access
  - test_non_admin_cannot_create_employee
  - test_cleanup_test_employees

### test_estimate_bug_fixes.py (11 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_estimates_list_returns_data_key
  - test_estimates_list_has_pagination
  - test_estimate_detail_has_line_items
  - test_line_items_have_required_fields
  - test_update_estimate_with_line_items
  - test_update_estimate_returns_line_items
  - test_estimate_to_invoice_finds_estimate
  - test_converted_estimate_cannot_convert_again
  - test_ticket_estimates_list
  - test_estimate_accepts_none_discount
  - test_estimate_accepts_percent_discount

### test_estimate_edit_status.py (7 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_draft_estimate_can_be_edited
  - test_sent_estimate_can_be_edited
  - test_accepted_estimate_can_be_edited
  - test_converted_estimate_cannot_be_edited
  - test_declined_estimate_can_be_edited
  - test_expired_estimate_can_be_edited
  - test_get_estimates_summary

### test_estimate_workflow_buttons.py (12 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_1_get_draft_estimate
  - test_2_get_sent_estimate_tkt_c86867066be6
  - test_3_get_approved_estimate_TKT_000054
  - test_4_send_estimate_api_works
  - test_5_approve_estimate_api_works
  - test_6_lock_estimate_requires_admin
  - test_7_unlock_estimate_admin_only
  - test_8_verify_estimate_status_transitions
  - test_1_draft_buttons
  - test_2_sent_buttons
  - test_3_approved_buttons
  - test_4_locked_buttons

### test_estimates_enhanced.py (35 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_settings
  - test_get_summary
  - test_conversion_funnel_report
  - test_report_by_status
  - test_report_by_customer
  - test_01_create_estimate
  - test_02_list_estimates
  - test_03_list_estimates_with_status_filter
  - test_04_list_estimates_with_search
  - test_05_get_estimate_detail
  - test_06_update_estimate
  - test_07_get_estimate_not_found
  - test_01_add_line_item
  - test_02_update_line_item
  - test_03_delete_line_item
  - test_01_send_estimate
  - test_02_verify_sent_status
  - test_03_mark_accepted
  - test_04_verify_accepted_status
  - test_01_convert_to_invoice
  - test_02_verify_converted_status
  - test_01_clone_estimate
  - test_02_delete_cloned_estimate
  - test_03_cannot_delete_non_draft
  - test_01_create_and_accept_for_so
  - test_02_convert_to_sales_order
  - test_01_create_and_send_for_decline
  - test_02_mark_declined
  - test_03_verify_declined_status
  - test_04_resend_declined_estimate
  - test_invalid_status_transition
  - test_create_without_customer
  - test_create_with_invalid_customer
  - test_update_non_draft_estimate
  - test_add_line_item_to_non_draft

### test_estimates_phase1.py (32 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_preferences
  - test_update_preferences
  - test_summary_includes_customer_viewed
  - test_01_get_customer
  - test_02_create_estimate_for_phase1
  - test_01_create_share_link
  - test_02_get_share_links
  - test_03_create_password_protected_link
  - test_01_access_public_quote
  - test_02_verify_customer_viewed_status
  - test_03_invalid_share_token
  - test_01_send_estimate_first
  - test_02_access_public_quote_after_send
  - test_03_verify_customer_viewed_status_after_access
  - test_04_customer_accept_action
  - test_05_verify_accepted_status
  - test_01_create_estimate_for_decline
  - test_02_send_and_create_share_link
  - test_03_customer_decline_action
  - test_04_verify_declined_status
  - test_01_create_estimate_for_attachments
  - test_02_upload_attachment
  - test_03_list_attachments
  - test_04_download_attachment
  - test_05_delete_attachment
  - test_06_attachment_limit_validation
  - test_01_generate_pdf
  - test_02_pdf_for_nonexistent_estimate
  - test_01_revoke_share_link
  - test_01_create_estimate_with_attachment_for_public
  - test_02_public_view_shows_attachments
  - test_cleanup_test_estimates

### test_estimates_phase2.py (22 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_list_pdf_templates
  - test_template_colors
  - test_list_custom_fields
  - test_add_custom_field
  - test_add_dropdown_custom_field
  - test_delete_custom_field
  - test_verify_custom_fields_after_operations
  - test_export_csv
  - test_export_json
  - test_export_with_status_filter
  - test_import_template_download
  - test_bulk_action_mark_sent
  - test_bulk_action_void
  - test_bulk_action_mark_expired
  - test_bulk_action_delete_draft_only
  - test_bulk_status_update
  - test_bulk_action_invalid_action
  - test_contacts_enhanced_count
  - test_legacy_contacts_count
  - test_pdf_default_template
  - test_pdf_with_template_endpoint_exists
  - test_summary_endpoint

### test_financial_time_docs.py (31 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_login_works
  - test_financial_summary
  - test_cash_flow
  - test_cash_flow_with_period
  - test_income_expense
  - test_income_expense_methods
  - test_top_expenses
  - test_bank_accounts
  - test_projects_watchlist
  - test_quick_stats
  - test_financial_summary_requires_org_id
  - test_list_time_entries
  - test_create_time_entry
  - test_get_time_entry
  - test_update_time_entry
  - test_start_timer
  - test_get_active_timers
  - test_stop_timer
  - test_get_unbilled_hours
  - test_time_summary_report
  - test_delete_time_entry
  - test_list_documents
  - test_list_folders
  - test_create_folder
  - test_document_stats_summary
  - test_create_document
  - test_get_document
  - test_update_document
  - test_list_tags
  - test_delete_document
  - test_delete_folder

### test_gst_accounting_flow.py (20 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_01_login
  - test_02_list_tickets
  - test_03_get_ticket_details
  - test_04_create_customer_contact
  - test_05_create_inventory_item
  - test_06_create_estimate
  - test_07_verify_gst_calculations
  - test_08_approve_estimate
  - test_09_convert_estimate_to_invoice
  - test_10_verify_invoice_gst_breakdown
  - test_11_record_payment
  - test_12_chart_of_accounts
  - test_13_zoho_sync_disconnect_endpoint
  - test_14_tax_configurations
  - test_99_cleanup
  - test_list_estimates
  - test_list_invoices
  - test_list_contacts
  - test_list_items
  - test_list_payments

### test_hr_module.py (16 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_admin_login
  - test_get_today_attendance
  - test_get_my_attendance_records
  - test_get_team_summary_admin
  - test_get_leave_types
  - test_get_leave_balance
  - test_get_my_leave_requests
  - test_get_pending_approvals_admin
  - test_get_payroll_records_admin
  - test_get_my_payroll_records
  - test_generate_payroll_admin
  - test_attendance_to_payroll_flow
  - test_leave_balance_update_on_request
  - test_attendance_without_auth
  - test_leave_without_auth
  - test_payroll_without_auth

### test_insights.py (34 tests) — MODERATE
- **Root Cause:** Hardcoded expired JWT tokens
- **Test Functions:**
  - test_revenue_returns_200
  - test_revenue_has_required_keys
  - test_revenue_kpis_structure
  - test_revenue_trend_is_list
  - test_revenue_by_type_is_list
  - test_revenue_with_current_month_params
  - test_operations_returns_200
  - test_operations_has_required_keys
  - test_operations_kpis_structure
  - test_operations_volume_is_list
  - test_operations_vehicle_dist_is_list
  - test_technicians_returns_200
  - test_technicians_has_required_keys
  - test_technicians_leaderboard_is_list
  - test_technicians_heatmap_is_list
  - test_technicians_vehicle_types_is_list
  - test_technicians_leaderboard_item_structure
  - test_efi_returns_200
  - test_efi_has_required_keys
  - test_efi_stats_structure
  - test_efi_failure_patterns_is_list
  - test_efi_optional_keys_present
  - test_customers_returns_200
  - test_customers_has_required_keys
  - test_customers_kpis_structure
  - test_customers_rating_trend_is_list
  - test_customers_top_customers_is_list
  - test_inventory_returns_200
  - test_inventory_has_required_keys
  - test_inventory_kpis_structure
  - test_inventory_stock_health_is_list
  - test_inventory_fast_movers_is_list
  - test_inventory_dead_stock_is_list
  - test_inventory_stock_health_items

### test_inventory_adjustments_phase2.py (15 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_export_csv_returns_csv_content
  - test_export_csv_with_filters
  - test_export_csv_with_date_range
  - test_validate_import_with_valid_csv
  - test_validate_import_detects_missing_items
  - test_process_import_creates_draft_adjustments
  - test_pdf_generation_returns_pdf
  - test_pdf_for_invalid_id_returns_404
  - test_abc_report_returns_classification
  - test_abc_drill_down_for_item
  - test_abc_drill_down_invalid_item
  - test_create_adjustment_with_ticket_id
  - test_ticket_id_in_export
  - test_items_endpoint_exists
  - test_full_import_workflow

### test_inventory_adjustments_v2.py (18 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_reasons_seeds_defaults
  - test_create_custom_reason
  - test_disable_reason
  - test_create_draft_quantity_adjustment
  - test_list_adjustments_with_filters
  - test_get_adjustment_detail_with_audit
  - test_convert_to_adjusted
  - test_void_adjusted
  - test_create_value_adjustment_adjusted
  - test_create_and_delete_draft
  - test_delete_adjusted_fails
  - test_get_summary
  - test_adjustment_summary_report
  - test_fifo_tracking_report
  - test_abc_classification_report
  - test_get_numbering_settings
  - test_convert_non_draft_fails
  - test_void_non_adjusted_fails

### test_inventory_hr_modules.py (33 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_admin_login_success
  - test_list_inventory_items
  - test_list_inventory_by_category
  - test_list_low_stock_items
  - test_create_inventory_item
  - test_get_inventory_item
  - test_get_nonexistent_item_returns_404
  - test_update_inventory_item
  - test_delete_inventory_item
  - test_create_allocation
  - test_list_allocations
  - test_list_employees
  - test_create_employee
  - test_get_employee
  - test_get_nonexistent_employee_returns_404
  - test_update_employee
  - test_get_leave_types
  - test_get_today_attendance
  - test_get_leave_balance
  - test_request_leave
  - test_get_my_leave_requests
  - test_request_leave_insufficient_balance
  - test_calculate_payroll
  - test_calculate_payroll_nonexistent_employee
  - test_get_payroll_records
  - test_list_tickets
  - test_get_ticket_stats
  - test_list_failure_cards
  - test_get_efi_analytics
  - test_inventory_without_auth
  - test_hr_employees_without_auth
  - test_hr_attendance_without_auth
  - test_hr_leave_balance_without_auth

### test_invoice_automation.py (20 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_aging_report
  - test_get_overdue_invoices
  - test_get_due_soon_invoices
  - test_get_reminder_settings
  - test_update_reminder_settings
  - test_get_late_fee_settings
  - test_update_late_fee_settings
  - test_send_reminder
  - test_send_reminder_invalid_invoice
  - test_get_reminder_history
  - test_calculate_late_fee
  - test_auto_apply_credits_invalid_invoice
  - test_create_payment_link
  - test_create_payment_link_invalid_invoice
  - test_get_payment_status_invalid_session
  - test_get_invoice_payment_link
  - test_list_payment_transactions
  - test_get_online_payments_summary
  - test_send_bulk_reminders_empty_list
  - test_send_bulk_reminders

### test_invoice_notification.py (21 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_list_invoices
  - test_create_invoice_for_pdf_test
  - test_get_invoice_pdf
  - test_invoice_pdf_not_found
  - test_invoice_contains_company_header
  - test_invoice_gst_breakdown
  - test_send_email_notification
  - test_send_email_invalid_template
  - test_send_whatsapp_notification
  - test_send_whatsapp_invalid_template
  - test_ticket_notification
  - test_ticket_notification_not_found
  - test_get_notification_logs
  - test_get_notification_logs_filtered
  - test_get_notification_stats
  - test_technical_spec_exists
  - test_ticket_created_template
  - test_ticket_assigned_template
  - test_estimate_shared_template
  - test_invoice_generated_template
  - test_ticket_resolved_template

### test_invoices_estimates_enhanced_zoho.py (19 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_invoice_detail
  - test_update_draft_invoice_notes
  - test_update_non_draft_invoice_limited
  - test_create_share_link
  - test_share_link_for_draft_fails
  - test_list_attachments_empty
  - test_upload_attachment
  - test_delete_attachment
  - test_list_comments_empty
  - test_add_comment
  - test_delete_comment
  - test_get_invoice_history
  - test_pdf_endpoint_exists
  - test_get_estimate_detail
  - test_update_draft_estimate_notes
  - test_list_estimates
  - test_estimates_summary
  - test_clone_invoice
  - test_void_invoice

### test_items_enhanced.py (19 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_list_item_groups
  - test_create_item_group
  - test_get_item_group
  - test_list_warehouses
  - test_create_warehouse
  - test_get_warehouse
  - test_list_price_lists
  - test_create_price_list
  - test_get_price_list
  - test_list_items
  - test_create_inventory_item
  - test_get_item
  - test_low_stock_items
  - test_list_adjustments
  - test_create_adjustment
  - test_stock_summary
  - test_inventory_valuation
  - test_create_stock_location
  - test_get_item_stock_locations

### test_items_enhanced_parts_fix.py (6 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_items_enhanced_with_trailing_slash
  - test_items_enhanced_without_search_query
  - test_items_enhanced_with_search_query
  - test_items_enhanced_inventory_type_filter
  - test_items_have_required_fields_for_estimate
  - test_pagination_context

### test_items_enhanced_zoho_columns.py (14 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_health_check
  - test_items_endpoint_available
  - test_create_item_with_full_zoho_fields
  - test_create_item_minimal_fields
  - test_export_csv_has_39_columns
  - test_export_template_has_correct_columns
  - test_export_json_format
  - test_item_list_with_new_fields
  - test_create_service_item_with_gst
  - test_create_item_with_weighted_average_valuation
  - test_get_single_item_details
  - test_update_item_zoho_fields
  - test_export_csv_data_integrity
  - test_cleanup_test_items

### test_items_estimates_integration.py (16 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_item_price_without_contact
  - test_get_item_price_with_contact_having_price_list
  - test_get_item_price_invalid_item
  - test_get_contact_pricing_summary
  - test_get_contact_pricing_summary_invalid_contact
  - test_get_item_pricing_for_estimate_without_customer
  - test_get_item_pricing_for_estimate_with_customer
  - test_get_item_pricing_invalid_item
  - test_get_customer_pricing_info
  - test_get_customer_pricing_invalid_customer
  - test_create_estimate_with_price_list_customer
  - test_create_estimate_with_manual_rate_override
  - test_create_estimate_multiple_items_with_price_list
  - test_verify_wholesale_price_list_exists
  - test_verify_customer_has_price_list_assigned
  - test_get_existing_estimate_with_price_list

### test_items_phase2.py (23 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_assign_price_list_to_contact
  - test_get_contact_price_lists
  - test_get_contact_price_lists_not_found
  - test_calculate_line_prices_basic
  - test_calculate_line_prices_with_contact
  - test_calculate_line_prices_multiple_items
  - test_set_bulk_prices_percentage
  - test_set_bulk_prices_custom
  - test_create_barcode
  - test_barcode_lookup
  - test_barcode_lookup_not_found
  - test_batch_barcode_lookup
  - test_sales_by_item_report
  - test_sales_by_item_report_with_filters
  - test_purchases_by_item_report
  - test_inventory_valuation_report
  - test_item_movement_report
  - test_item_movement_report_with_date_filter
  - test_items_list
  - test_price_lists
  - test_groups
  - test_warehouses
  - test_summary

### test_items_phase3.py (10 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_preferences
  - test_update_preferences
  - test_get_field_config
  - test_update_field_config
  - test_update_single_field_config
  - test_get_fields_for_role
  - test_generate_sku_disabled
  - test_generate_sku_enabled
  - test_preferences_affect_sku_generation
  - test_field_config_mandatory_fields

### test_items_pricelists_inventory.py (13 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_list_items
  - test_list_items_filter_by_type
  - test_search_items
  - test_create_item
  - test_list_price_lists
  - test_create_price_list
  - test_add_item_to_price_list
  - test_list_inventory_adjustments
  - test_create_inventory_adjustment
  - test_list_adjustments_by_reason
  - test_items_endpoint_exists
  - test_price_lists_endpoint_exists
  - test_inventory_adjustments_endpoint_exists

### test_items_zoho_features.py (28 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_search_items_by_name
  - test_search_items_by_sku
  - test_sort_by_name_asc
  - test_sort_by_sales_rate_desc
  - test_sort_by_stock
  - test_filter_by_inventory_type
  - test_filter_by_service_type
  - test_filter_by_active_status
  - test_item_id
  - test_bulk_clone
  - test_bulk_deactivate
  - test_bulk_activate
  - test_bulk_delete
  - test_bulk_action_empty_list
  - test_export_csv
  - test_import_template_download
  - test_list_custom_fields
  - test_create_text_custom_field
  - test_create_dropdown_custom_field
  - test_create_sales_price_list
  - test_create_purchase_price_list
  - test_get_all_history
  - test_get_item_specific_history
  - test_add_stock_adjustment
  - test_subtract_stock_adjustment
  - test_create_item_with_all_fields
  - test_update_item
  - test_delete_item_no_transactions

### test_new_ai_features_map_integration.py (14 tests) — TRIVIAL
- **Root Cause:** ENV/config issue
- **Test Functions:**
  - test_ai_suggestions_battery_issue
  - test_ai_suggestions_motor_issue
  - test_ai_suggestions_minimal_input
  - test_business_dashboard
  - test_business_fleet
  - test_business_tickets
  - test_business_invoices
  - test_technician_ai_assist_battery_query
  - test_technician_ai_assist_motor_query
  - test_technician_ai_assist_general_query
  - test_technician_dashboard
  - test_vehicle_categories
  - test_vehicle_models
  - test_service_charges

### test_new_features_iteration64.py (15 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_stock_endpoint_returns_200
  - test_stock_endpoint_with_warehouse_filter
  - test_export_organization_settings
  - test_import_organization_settings
  - test_import_invalid_format_rejected
  - test_portal_login
  - test_get_customer_tickets_empty
  - test_create_support_ticket
  - test_get_ticket_detail
  - test_add_ticket_comment
  - test_get_customer_vehicles
  - test_get_current_organization
  - test_list_user_organizations
  - test_get_organization_settings
  - test_get_roles

### test_notifications_export.py (21 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_create_notification
  - test_list_notifications
  - test_get_unread_count
  - test_mark_notification_as_read
  - test_mark_all_as_read
  - test_get_notification_details
  - test_archive_notification
  - test_generate_einvoice
  - test_download_einvoice
  - test_export_invoices_to_tally
  - test_export_bills_to_tally
  - test_export_ledgers_to_tally
  - test_bulk_export_invoices_csv
  - test_bulk_export_invoices_json
  - test_bulk_export_expenses_csv
  - test_check_overdue_invoices
  - test_check_expiring_amcs
  - test_check_low_stock
  - test_notification_preferences_get
  - test_notification_preferences_update
  - test_cleanup_test_notifications

### test_onboarding_checklist.py (16 tests) — MODERATE
- **Root Cause:** Hardcoded expired JWT tokens
- **Test Functions:**
  - test_onboarding_status_returns_200
  - test_onboarding_status_show_onboarding_true
  - test_onboarding_status_response_structure
  - test_onboarding_status_total_steps_is_6
  - test_onboarding_status_completed_count_zero_initially
  - test_onboarding_not_completed_initially
  - test_battwheels_returns_200
  - test_battwheels_show_onboarding_false
  - test_battwheels_onboarding_completed_true
  - test_complete_step_returns_success
  - test_complete_step_persists
  - test_complete_step_invalid_step_returns_400
  - test_complete_step_response_structure
  - test_skip_returns_success
  - test_skip_sets_onboarding_completed
  - test_skip_resets_and_show_banner_again

### test_p2_p3_p4_pwa.py (34 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_get_whatsapp_settings_returns_200
  - test_get_whatsapp_settings_has_configured_field
  - test_get_whatsapp_settings_has_phone_number_id_field
  - test_post_whatsapp_settings_saves_credentials
  - test_get_after_save_shows_configured
  - test_delete_whatsapp_settings_removes_credentials
  - test_get_after_delete_shows_not_configured
  - test_whatsapp_test_returns_400_no_phone
  - test_send_invoice_email_channel_works
  - test_tally_xml_returns_200_for_valid_range
  - test_tally_xml_response_has_content_disposition
  - test_tally_xml_content_type_is_xml
  - test_tally_xml_starts_with_xml_declaration
  - test_tally_xml_is_valid_xml
  - test_tally_xml_contains_envelope_structure
  - test_tally_xml_no_entries_returns_404
  - test_tally_xml_invalid_date_returns_400
  - test_tally_xml_date_from_after_to_returns_400
  - test_signup_is_public_route_no_auth_needed
  - test_signup_returns_token
  - test_signup_creates_org_with_trial_ends_at
  - test_signup_with_city_phone_vehicle_types
  - test_signup_duplicate_email_returns_400
  - test_signup_plan_type_is_free_trial
  - test_manifest_json_accessible
  - test_manifest_json_has_name
  - test_manifest_json_has_theme_color
  - test_manifest_json_has_icons
  - test_sw_js_accessible
  - test_sw_js_is_javascript
  - test_icon_192_accessible
  - test_icon_512_accessible
  - test_icon_192_is_png
  - test_icon_512_is_png

### test_password_reset.py (9 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_change_password_wrong_current
  - test_change_password_success
  - test_change_password_weak_password
  - test_forgot_password_valid_email
  - test_forgot_password_unknown_email
  - test_reset_password_invalid_token
  - test_reset_password_valid_token
  - test_reset_password_used_token
  - test_reset_password_expired_token

### test_payments_received.py (25 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_summary_default_period
  - test_summary_different_periods
  - test_list_all_payments
  - test_list_payments_by_customer
  - test_list_payments_by_mode
  - test_list_payments_search
  - test_list_payments_pagination
  - test_get_existing_payment
  - test_get_nonexistent_payment
  - test_get_customer_open_invoices
  - test_list_all_credits
  - test_list_credits_by_status
  - test_get_customer_credits
  - test_record_retainer_payment
  - test_record_payment_invalid_customer
  - test_record_payment_with_bank_charges
  - test_delete_payment
  - test_delete_nonexistent_payment
  - test_get_settings
  - test_report_by_customer
  - test_report_by_mode
  - test_export_payments
  - test_get_import_template
  - test_refund_requires_available_credit
  - test_cleanup_test_payments

### test_phase_b_sprint.py (16 tests) — TRIVIAL
- **Root Cause:** Already correct credentials
- **Test Functions:**
  - test_01_list_delivery_challans
  - test_02_create_delivery_challan
  - test_03_get_delivery_challan_by_id
  - test_04_update_delivery_challan
  - test_05_cannot_delete_delivered_challan
  - test_06_delete_draft_challan
  - test_01_list_vendor_credits
  - test_02_create_vendor_credit_locked_period_fails
  - test_03_create_vendor_credit_open_period
  - test_04_get_vendor_credit_by_id
  - test_05_apply_vendor_credit_creates_journal_entry
  - test_06_cannot_delete_applied_credit
  - test_07_delete_draft_vendor_credit
  - test_bills_enhanced_list
  - test_balance_sheet_endpoint
  - test_profit_loss_endpoint

### test_price_lists_enhanced.py (20 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_item_id
  - test_price_list_id
  - test_create_price_list_with_percentage
  - test_list_price_lists_with_enriched_items
  - test_get_single_price_list
  - test_update_price_list
  - test_delete_price_list_soft_delete
  - test_add_item_with_pricelist_rate_and_discount
  - test_update_item_in_price_list
  - test_remove_item_from_price_list
  - test_export_csv_zoho_format
  - test_import_csv_zoho_format
  - test_import_csv_error_handling
  - test_sync_items_updates_data
  - test_bulk_add_with_markup
  - test_bulk_add_with_markdown
  - test_get_nonexistent_price_list_returns_404
  - test_update_nonexistent_price_list_returns_404
  - test_add_nonexistent_item_returns_404
  - test_import_without_csv_data_returns_error

### test_production_readiness_iteration103.py (26 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_razorpay_refund_endpoint_exists_and_validates
  - test_razorpay_refund_with_nonexistent_credit_note
  - test_razorpay_refund_with_existing_credit_note
  - test_get_refund_status_endpoint
  - test_check_razorpay_payment_endpoint
  - test_razorpay_refund_status_check_with_mock_id
  - test_form16_data_endpoint_exists
  - test_form16_pdf_endpoint_exists
  - test_form16_invalid_fy_format
  - test_form16_with_existing_employee
  - test_sla_config_get
  - test_sla_config_put
  - test_sla_dashboard
  - test_sla_status_ticket_not_found
  - test_sla_status_existing_ticket
  - test_sla_check_breaches
  - test_new_ticket_has_sla_fields
  - test_sla_deadlines_correct_for_high_priority
  - test_backend_server_responds
  - test_backend_health_after_sentry_init
  - test_invoices_paginated
  - test_bills_paginated
  - test_contacts_paginated
  - test_tickets_paginated
  - test_credit_notes_paginated
  - test_employees_paginated

### test_projects_tds_features.py (26 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_login_success
  - test_tds_summary_endpoint
  - test_tds_calculate_for_employee
  - test_tds_export_csv
  - test_mark_tds_deposited
  - test_mark_tds_deposited_duplicate_challan
  - test_list_tds_challans
  - test_form16_api
  - test_list_projects
  - test_get_project_detail
  - test_project_tasks
  - test_project_time_logs
  - test_project_expenses
  - test_project_profitability
  - test_project_dashboard_stats
  - test_add_expense_to_project
  - test_approve_expense
  - test_reject_expense
  - test_generate_invoice_from_project
  - test_invoice_grouping_by_employee
  - test_invoice_grouping_by_date
  - test_create_task
  - test_update_task_status
  - test_log_time
  - test_get_employee_tax_config
  - test_update_employee_tax_config

### test_public_ticket_master_data.py (21 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_seed_master_data
  - test_get_vehicle_categories
  - test_get_all_models
  - test_get_models_by_category
  - test_model_has_required_fields
  - test_get_issue_suggestions
  - test_suggestion_has_required_fields
  - test_suggestions_have_common_symptoms
  - test_get_service_charges
  - test_submit_business_ticket_no_payment
  - test_submit_individual_workshop_no_payment
  - test_submit_individual_onsite_requires_payment
  - test_submit_individual_onsite_with_diagnostic
  - test_verify_mock_payment
  - test_lookup_by_ticket_id
  - test_lookup_by_phone
  - test_get_ticket_details_with_token
  - test_get_ticket_without_token_fails
  - test_get_internal_vehicle_categories
  - test_get_internal_vehicle_models
  - test_get_internal_issue_suggestions

### test_recurring_invoices_pdf.py (21 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_01_list_recurring_invoices
  - test_02_get_recurring_summary
  - test_03_create_recurring_invoice
  - test_04_get_recurring_invoice
  - test_05_update_recurring_invoice
  - test_06_stop_recurring_invoice
  - test_07_resume_recurring_invoice
  - test_08_generate_invoice_now
  - test_09_delete_recurring_invoice
  - test_01_get_aging_report
  - test_02_get_overdue_invoices
  - test_03_get_due_soon_invoices
  - test_04_get_reminder_settings
  - test_05_save_reminder_settings
  - test_06_get_late_fee_settings
  - test_07_save_late_fee_settings
  - test_01_generate_invoice_pdf
  - test_02_generate_estimate_pdf
  - test_01_send_reminder
  - test_02_calculate_late_fee
  - test_03_get_reminder_history

### test_reports.py (16 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_profit_loss_json
  - test_profit_loss_with_date_filter
  - test_profit_loss_pdf_export
  - test_profit_loss_excel_export
  - test_balance_sheet_json
  - test_balance_sheet_pdf_export
  - test_balance_sheet_excel_export
  - test_ar_aging_json
  - test_ar_aging_pdf_export
  - test_ar_aging_excel_export
  - test_ap_aging_json
  - test_ap_aging_pdf_export
  - test_ap_aging_excel_export
  - test_sales_by_customer_json
  - test_sales_by_customer_pdf_export
  - test_sales_by_customer_excel_export

### test_sales_orders_enhanced.py (28 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_get_settings
  - test_get_summary
  - test_report_by_status
  - test_report_by_customer
  - test_fulfillment_summary
  - test_01_create_sales_order
  - test_02_list_sales_orders
  - test_03_list_with_status_filter
  - test_04_get_sales_order_detail
  - test_05_update_draft_sales_order
  - test_01_add_line_item
  - test_02_update_line_item
  - test_03_delete_line_item
  - test_01_create_order_for_workflow
  - test_02_confirm_order
  - test_03_create_fulfillment
  - test_04_get_fulfillments
  - test_05_convert_to_invoice
  - test_01_clone_sales_order
  - test_02_send_sales_order
  - test_01_create_order_for_void
  - test_02_confirm_then_void
  - test_03_delete_draft_order
  - test_04_cannot_delete_confirmed_order
  - test_invalid_customer
  - test_get_nonexistent_order
  - test_search_orders
  - test_cleanup_test_orders

### test_serial_batch_pdf_templates.py (34 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_item_id
  - test_serial_summary_report
  - test_batch_summary_report
  - test_expiring_batches_report
  - test_tracking_enabled_items
  - test_list_serial_numbers
  - test_list_serials_with_status_filter
  - test_create_serial_number
  - test_create_duplicate_serial_fails
  - test_bulk_create_serials
  - test_serial_lookup_by_number
  - test_update_serial_status
  - test_list_batch_numbers
  - test_create_batch_number
  - test_create_duplicate_batch_fails
  - test_adjust_batch_quantity
  - test_batch_depleted_status
  - test_configure_item_tracking
  - test_get_item_tracking_config
  - test_list_all_templates
  - test_list_templates_by_type
  - test_list_available_styles
  - test_get_template_by_id
  - test_get_nonexistent_template_returns_404
  - test_get_default_template_for_type
  - test_create_custom_template
  - test_duplicate_template
  - test_update_custom_template
  - test_cannot_update_system_template
  - test_delete_custom_template
  - test_cannot_delete_system_template
  - test_set_default_template
  - test_preview_template
  - test_preview_with_custom_data

### test_service_ticket_dashboard.py (15 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_dashboard_stats_endpoint_returns_200
  - test_dashboard_stats_contains_service_ticket_stats
  - test_service_ticket_stats_structure
  - test_service_ticket_stats_total_open_is_numeric
  - test_onsite_resolution_count
  - test_workshop_visit_count
  - test_pickup_remote_counts
  - test_avg_resolution_time_hours
  - test_onsite_resolution_percentage
  - test_30d_metrics
  - test_total_open_matches_sum_of_resolution_types
  - test_percentage_calculation_consistency
  - test_dashboard_stats_data_types_valid
  - test_open_repair_orders_matches_service_ticket_total
  - test_create_onsite_ticket_and_verify_stats

### test_setup_wizard_email_usage.py (14 tests) — TRIVIAL
- **Root Cause:** ENV/config issue
- **Test Functions:**
  - test_get_setup_status
  - test_update_organization_settings_profile
  - test_update_organization_settings_business
  - test_complete_setup
  - test_settings_requires_auth
  - test_complete_setup_requires_auth
  - test_invite_user_sends_email
  - test_duplicate_invite_rejected
  - test_subscription_current_still_works
  - test_subscription_limits_still_works
  - test_subscription_entitlements_still_works
  - test_list_members_works
  - test_list_invites_works
  - test_organization_me_works

### test_sprint_6b_knowledge_pipeline.py (13 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_process_queue_endpoint_requires_platform_admin
  - test_process_queue_succeeds_for_platform_admin
  - test_knowledge_articles_exist_from_learning_events
  - test_seed_articles_endpoint_requires_platform_admin
  - test_seed_articles_succeeds_and_returns_counts
  - test_seed_articles_idempotent_on_rerun
  - test_fix_empty_cards_endpoint_requires_platform_admin
  - test_fix_empty_cards_returns_report
  - test_excluded_from_efi_filter_in_find_similar
  - test_suggestions_endpoint_works
  - test_suggestions_include_knowledge_article_field
  - test_knowledge_article_matches_subsystem
  - test_full_pipeline_flow

### test_sprint_6c_cursor_pagination.py (17 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_legacy_pagination_returns_next_cursor
  - test_cursor_pagination_chain_no_duplicates
  - test_invalid_cursor_handled_gracefully
  - test_legacy_pagination_returns_next_cursor
  - test_cursor_pagination_chain_no_duplicates
  - test_legacy_pagination_returns_next_cursor
  - test_cursor_pagination_small_dataset
  - test_legacy_skip_limit_returns_items
  - test_cursor_pagination_with_confidence_sort
  - test_legacy_pagination_returns_next_cursor
  - test_cursor_pagination_chain_no_duplicates
  - test_tickets_without_cursor
  - test_invoices_without_cursor
  - test_employees_without_cursor
  - test_failure_cards_without_cursor
  - test_journal_entries_without_cursor
  - test_cursor_structure_validation

### test_stock_indicator.py (9 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_1_stock_indicator_in_stock
  - test_2_labour_items_no_stock_info
  - test_3_stock_status_in_stock
  - test_4_stock_status_low_stock
  - test_5_stock_status_out_of_stock
  - test_6_parts_catalog_shows_stock
  - test_7_add_part_returns_stock_info
  - test_8_stock_info_includes_all_fields
  - test_9_parts_without_item_id_no_stock

### test_team_subscription_management.py (18 tests) — TRIVIAL
- **Root Cause:** ENV/config issue
- **Test Functions:**
  - test_get_current_subscription
  - test_get_subscription_entitlements
  - test_get_subscription_limits
  - test_subscription_requires_auth
  - test_compare_plans_public
  - test_list_members
  - test_list_invitations
  - test_invite_user
  - test_invite_user_duplicate
  - test_invite_user_invalid_role
  - test_cancel_invitation
  - test_cancel_nonexistent_invitation
  - test_update_member_role
  - test_update_role_invalid
  - test_team_endpoints_require_auth
  - test_get_my_organizations
  - test_get_current_organization
  - test_cleanup_test_invites

### test_ticket_estimate_integration.py (20 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_ensure_estimate_creates_new
  - test_ensure_estimate_idempotent
  - test_ensure_estimate_for_nonexistent_ticket
  - test_get_estimate_by_ticket
  - test_get_estimate_by_id
  - test_get_nonexistent_estimate
  - test_add_part_line_item
  - test_add_labour_line_item
  - test_add_fee_line_item
  - test_update_line_item
  - test_delete_line_item
  - test_version_mismatch_returns_409
  - test_update_with_wrong_version
  - test_lock_estimate_as_admin
  - test_modify_locked_estimate_returns_423
  - test_send_estimate
  - test_approve_estimate
  - test_list_estimates
  - test_list_estimates_with_status_filter
  - test_totals_update_on_add

### test_ticket_workflow_lifecycle.py (11 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_ticket
  - test_start_work_on_estimate_approved
  - test_complete_work_requires_work_summary
  - test_close_ticket_after_work_completed
  - test_get_activities
  - test_add_activity_note
  - test_admin_edit_activity
  - test_admin_delete_activity
  - test_status_history_shows_transitions
  - test_approve_estimate_updates_ticket_status
  - test_full_workflow_transitions

### test_zoho_api.py (51 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_01_create_customer
  - test_02_create_vendor
  - test_03_list_contacts
  - test_04_get_contact_details
  - test_05_update_contact
  - test_06_mark_contact_inactive
  - test_07_mark_contact_active
  - test_01_create_service_item
  - test_02_create_goods_item
  - test_03_list_items
  - test_01_create_estimate
  - test_02_list_estimates
  - test_03_mark_estimate_sent
  - test_04_mark_estimate_accepted
  - test_01_create_invoice
  - test_02_list_invoices
  - test_03_mark_invoice_sent
  - test_04_convert_estimate_to_invoice
  - test_01_create_salesorder
  - test_02_convert_salesorder_to_invoice
  - test_03_convert_estimate_to_salesorder
  - test_01_create_purchaseorder
  - test_02_list_purchaseorders
  - test_03_convert_purchaseorder_to_bill
  - test_01_create_bill
  - test_02_list_bills
  - test_01_create_creditnote
  - test_02_apply_creditnote_to_invoice
  - test_01_create_vendorcredit
  - test_01_record_customer_payment
  - test_02_list_customer_payments
  - test_01_record_vendor_payment
  - test_01_create_expense
  - test_02_list_expenses
  - test_01_create_bank_account
  - test_02_list_bank_accounts
  - test_03_create_bank_transaction
  - test_04_list_bank_transactions
  - test_01_create_account
  - test_02_list_accounts
  - test_01_create_journal_entry
  - test_02_journal_validation_debit_credit_mismatch
  - test_03_list_journals
  - test_01_dashboard_report
  - test_02_profit_and_loss_report
  - test_03_receivables_report
  - test_04_payables_report
  - test_05_gst_report
  - test_01_sales_workflow
  - test_02_purchase_workflow
  - test_cleanup_test_data

### test_zoho_books_module.py (17 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_admin_login_success
  - test_login_invalid_credentials
  - test_list_customers
  - test_customer_search
  - test_customer_has_required_fields
  - test_create_customer
  - test_list_services
  - test_service_has_hsn_code
  - test_service_search
  - test_list_parts
  - test_part_has_stock_info
  - test_list_invoices
  - test_invoice_has_gst_calculation
  - test_create_invoice_with_gst
  - test_analytics_summary
  - test_list_vendors
  - test_list_accounts

### test_zoho_extended.py (16 tests) — MODERATE
- **Root Cause:** No authentication mechanism
- **Test Functions:**
  - test_list_delivery_challans
  - test_create_delivery_challan
  - test_list_projects
  - test_create_project
  - test_list_time_entries
  - test_list_recurring_invoices
  - test_create_recurring_invoice
  - test_list_taxes
  - test_create_tax
  - test_list_tax_groups
  - test_list_chart_of_accounts
  - test_create_account
  - test_list_journal_entries
  - test_create_journal_entry
  - test_list_vendor_credits
  - test_create_vendor_credit

### test_zoho_new_modules.py (34 tests) — TRIVIAL
- **Root Cause:** Wrong credentials (admin@battwheels.in)
- **Test Functions:**
  - test_list_recurring_bills
  - test_create_recurring_bill
  - test_get_recurring_bill
  - test_stop_recurring_bill
  - test_resume_recurring_bill
  - test_generate_due_bills
  - test_delete_recurring_bill
  - test_get_fixed_assets_summary
  - test_list_fixed_assets
  - test_create_fixed_asset
  - test_get_fixed_asset
  - test_record_depreciation
  - test_dispose_asset
  - test_create_and_write_off_asset
  - test_delete_fixed_asset
  - test_list_custom_modules
  - test_create_custom_module
  - test_get_custom_module
  - test_create_custom_record
  - test_list_custom_records
  - test_get_custom_record
  - test_update_custom_record
  - test_search_custom_records
  - test_validate_required_fields
  - test_delete_custom_record
  - test_deactivate_custom_module
  - test_list_contacts
  - test_contacts_summary
  - test_filter_customers
  - test_filter_vendors
  - test_validate_gstin
  - test_get_indian_states
  - test_contact_tags
  - test_check_sync

### test_zoho_parity_services.py (15 tests) — TRIVIAL
- **Root Cause:** Missing sys.path for backend imports
- **Test Functions:**
  - test_finance_calculator_import
  - test_line_item_calculation_via_estimate
  - test_activity_service_import
  - test_estimate_activity_endpoint_exists
  - test_estimate_activity_structure
  - test_invoice_history_endpoint_exists
  - test_payment_activity_endpoint_exists
  - test_payment_receipt_pdf_endpoint_exists
  - test_sales_order_activity_endpoint_exists
  - test_sales_order_pdf_endpoint_exists
  - test_contact_activity_endpoint_exists
  - test_invoice_attachments_list
  - test_invoice_comments_list
  - test_invoice_share_link_creation
  - test_cleanup_test_data

---

## Meaningful Coverage Assessment

All 83 Bucket A files test modules NOT in the core suite (25 files).
They collectively cover: EFI/AI intelligence, Employee CRUD, Customer Portal,
Items/Inventory management, Estimates workflow, Invoice automation, Contacts,
Zoho integration, HR/Attendance, Reports, Banking, Sales Orders, Payments,
Notifications, Price Lists, Serial/Batch tracking, Composite Items,
Delivery Challans, Projects/TDS, Setup Wizard, and more.

**Yes — fixing these files would dramatically expand test coverage.
The core suite covers only infrastructure/security; these cover all business modules.**
