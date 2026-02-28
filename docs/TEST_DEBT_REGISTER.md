# TEST DEBT REGISTER
## Battwheels OS — Remaining Test Files Requiring Fixes
## Created: 2026-02-28 (Phase 0.5 Triage)

---

## Overview

After Phase 0.5 triage, **76 Bucket A test files** remain with failures.
All have had TRIVIAL fixes applied (credentials, env vars, sys.path).
Remaining failures are MODERATE effort — requiring auth fixtures, test data updates,
or expectation corrections.

### Root Cause Distribution

| Root Cause | Files | Description |
|-----------|-------|-------------|
| No auth mechanism | 24 | Tests call endpoints without authentication tokens |
| Test data/expectations mismatch | 30 | Tests expect specific data/responses that have changed |
| Setup errors (cascading) | 5 | Auth setup fails, cascading to all dependent tests |
| Hardcoded expired JWT | 2 | Hardcoded JWT tokens instead of login-based auth |
| API/code changes | 2 | Backend code evolved, tests reference old signatures |
| All tests skipped | 8 | Deprecated/conditional — no active test value |
| Near-passing (1-3 failures) | 5 | Close to green, minor fixes needed |

---

## MODULE CLUSTER MAPPING

### Cluster 1: Items & Inventory (13 files, ~260 tests)

| File | Tests | Status | Root Cause | Fix Effort |
|------|-------|--------|------------|------------|
| test_items_enhanced.py | 19 | 19 failed | No auth mechanism | MODERATE |
| test_items_phase2.py | 23 | 11 failed, 12 skipped | No auth mechanism | MODERATE |
| test_items_phase3.py | 10 | 10 failed | No auth mechanism | MODERATE |
| test_items_enhanced_parts_fix.py | 6 | 6 failed | Test data mismatch | MODERATE |
| test_items_enhanced_zoho_columns.py | 14 | 14 skipped | All skipped (deprecated) | TRIVIAL |
| test_items_zoho_features.py | 28 | 27 skipped | All skipped (deprecated) | TRIVIAL |
| test_items_estimates_integration.py | 16 | 16 failed | No auth mechanism | MODERATE |
| test_items_pricelists_inventory.py | 13 | 13 failed | Test data mismatch | MODERATE |
| test_inventory_adjustments_v2.py | 18 | 12 failed, 1 skip, 5 errors | No auth mechanism | MODERATE |
| test_inventory_adjustments_phase2.py | 15 | 13 failed, 2 skipped | No auth mechanism | MODERATE |
| test_inventory_hr_modules.py | 33 | 26 failed, 7 passed | Test data mismatch | MODERATE |
| test_stock_indicator.py | 9 | 9 failed | Test data mismatch | MODERATE |
| test_serial_batch_pdf_templates.py | 34 | 22 failed, 11 skipped | No auth mechanism | MODERATE |

### Cluster 2: Estimates & Invoices (14 files, ~270 tests)

| File | Tests | Status | Root Cause | Fix Effort |
|------|-------|--------|------------|------------|
| test_estimates_enhanced.py | 35 | 10 failed, 25 skipped | No auth mechanism | MODERATE |
| test_estimates_phase1.py | 32 | 5 failed, 1 passed, 26 skipped | No auth mechanism | MODERATE |
| test_estimates_phase2.py | 22 | 12 failed, 7 passed, 3 skipped | Test data mismatch | MODERATE |
| test_estimate_bug_fixes.py | 11 | 11 errors | Setup errors | MODERATE |
| test_estimate_edit_status.py | 7 | 7 failed | Test data mismatch | MODERATE |
| test_estimate_workflow_buttons.py | 12 | 4 failed, 8 passed | Test data mismatch | MODERATE |
| test_convert_invoice_stock_transfers.py | 24 | 5 failed, 15 skipped | Test data mismatch | MODERATE |
| test_invoice_automation.py | 20 | 14 failed, 6 skipped | No auth mechanism | MODERATE |
| test_invoice_notification.py | 21 | 17 failed, 4 passed | Test data mismatch | MODERATE |
| test_invoices_estimates_enhanced_zoho.py | 19 | 19 skipped | All skipped (deprecated) | TRIVIAL |
| test_recurring_invoices_pdf.py | 21 | 8 failed, 13 skipped | No auth mechanism | MODERATE |
| test_bills_inventory_enhanced.py | 38 | 11 failed, 1 passed, 26 skipped | No auth mechanism | MODERATE |
| test_composite_items_invoice_settings.py | 24 | 13 failed, 11 skipped | No auth mechanism | MODERATE |
| test_gst_accounting_flow.py | 20 | 7 failed, 7 passed, 6 skipped | Test data mismatch | MODERATE |

### Cluster 3: Contacts & Customers (7 files, ~200 tests)

| File | Tests | Status | Root Cause | Fix Effort |
|------|-------|--------|------------|------------|
| test_contacts_enhanced.py | 37 | 16 failed, 4 passed, 17 skipped | No auth mechanism | MODERATE |
| test_contacts_invoices_enhanced.py | 35 | 23 failed, 3 passed, 9 skipped | No auth mechanism | MODERATE |
| test_contact_integration.py | 23 | 22 failed, 1 passed | Test data mismatch | MODERATE |
| test_customers_enhanced.py | 52 | 20 failed, 2 passed, 30 skipped | No auth mechanism | MODERATE |
| test_customer_portal.py | 19 | 6 failed, 1 passed, 12 skipped | Test data mismatch | MODERATE |
| test_customer_portal_auth.py | 21 | 2 failed, 4 passed, 15 skipped | Test data mismatch | MODERATE |
| test_complaint_dashboard.py | 19 | 15 failed, 4 passed | Test data mismatch | MODERATE |

### Cluster 4: EFI / AI Intelligence (7 files, ~120 tests)

| File | Tests | Status | Root Cause | Fix Effort |
|------|-------|--------|------------|------------|
| test_efi_intelligence.py | 15 | 5 failed, 10 passed | API changes (missing arg) | MODERATE |
| test_efi_intelligence_api.py | 15 | 15 failed | No auth mechanism | MODERATE |
| test_efi_module.py | 24 | 12 failed, 2 passed, 8 errors | Setup errors | MODERATE |
| test_efi_guided.py | 21 | 8 failed, 3 passed, 8 skipped | Test data mismatch | MODERATE |
| test_efi_search_embeddings.py | 21 | 21 failed | Test data mismatch | MODERATE |
| test_ai_diagnostic_assistant.py | 10 | 8 failed, 2 passed | Test data mismatch | MODERATE |
| test_new_ai_features_map_integration.py | 14 | 4 failed, 6 passed, 4 skipped | Test data mismatch | MODERATE |

### Cluster 5: HR, Payroll, Finance (8 files, ~175 tests)

| File | Tests | Status | Root Cause | Fix Effort |
|------|-------|--------|------------|------------|
| test_hr_module.py | 16 | 13 failed, 3 passed | Test data mismatch | MODERATE |
| test_employee_creation.py | 7 | 6 failed, 1 passed | Test data mismatch | MODERATE |
| test_employee_module.py | 21 | 19 failed, 2 passed | Test data mismatch | MODERATE |
| test_projects_tds_features.py | 26 | 7 failed, 1 passed, 18 skipped | Test data mismatch | MODERATE |
| test_financial_time_docs.py | 31 | 22 failed, 1 passed, 8 skipped | Test data mismatch | MODERATE |
| test_reports.py | 16 | 16 failed | Test data mismatch | MODERATE |
| test_insights.py | 34 | 34 failed | Hardcoded expired JWT | MODERATE |
| test_audit_logging.py | 15 | 1 passed, 14 errors | Setup errors | MODERATE |

### Cluster 6: Zoho Integration (5 files, ~133 tests — mostly skipped)

| File | Tests | Status | Root Cause | Fix Effort |
|------|-------|--------|------------|------------|
| test_zoho_api.py | 51 | 51 skipped | All skipped (deprecated) | TRIVIAL |
| test_zoho_books_module.py | 17 | 17 skipped | All skipped (deprecated) | TRIVIAL |
| test_zoho_extended.py | 16 | 16 skipped | All skipped (deprecated) | TRIVIAL |
| test_zoho_new_modules.py | 34 | 34 skipped | All skipped (deprecated) | TRIVIAL |
| test_zoho_parity_services.py | 15 | 15 skipped | All skipped (deprecated) | TRIVIAL |

### Cluster 7: Platform, SaaS, Settings (16 files, ~280 tests)

| File | Tests | Status | Root Cause | Fix Effort |
|------|-------|--------|------------|------------|
| test_all_settings.py | 17 | 16 failed, 1 passed | Test data mismatch | MODERATE |
| test_all_settings_complete.py | 25 | 25 failed | Test data mismatch | MODERATE |
| test_banking_stock_transfers.py | 22 | 18 failed, 4 skipped | Test data mismatch | MODERATE |
| test_data_management.py | 14 | 14 failed | Test data mismatch | MODERATE |
| test_entitlement_service.py | 14 | 2 failed, 11 passed | API changes | MODERATE |
| test_new_features_iteration64.py | 15 | 9 failed, 6 skipped | Test data mismatch | MODERATE |
| test_notifications_export.py | 21 | 18 failed, 1 passed, 2 skipped | Test data mismatch | MODERATE |
| test_onboarding_checklist.py | 16 | 16 failed | Hardcoded expired JWT | MODERATE |
| test_p2_p3_p4_pwa.py | 34 | 6 failed, 10 passed, 18 errors | Setup errors | MODERATE |
| test_password_reset.py | 9 | 9 failed | Test data mismatch | MODERATE |
| test_payments_received.py | 25 | 24 failed, 1 passed | No auth mechanism | MODERATE |
| test_phase_b_sprint.py | 16 | 3 failed, 10 passed, 3 skipped | Test data mismatch | MODERATE |
| test_price_lists_enhanced.py | 20 | 5 failed, 13 skipped | Test data mismatch | MODERATE |
| test_production_readiness_iteration103.py | 26 | 13 failed, 8 passed, 5 skipped | Test data mismatch | MODERATE |
| test_public_ticket_master_data.py | 21 | 18 failed, 3 passed | Test data mismatch | MODERATE |
| test_sales_orders_enhanced.py | 28 | 27 failed, 1 passed | No auth mechanism | MODERATE |
| test_service_ticket_dashboard.py | 15 | 11 failed, 3 passed, 1 skipped | Test data mismatch | MODERATE |
| test_setup_wizard_email_usage.py | 14 | 14 errors | Setup errors | MODERATE |
| test_team_subscription_management.py | 18 | 1 failed, 3 passed, 14 skipped | Test data mismatch | MODERATE |
| test_ticket_estimate_integration.py | 20 | 6 failed, 14 skipped | Test data mismatch | MODERATE |
| test_ticket_workflow_lifecycle.py | 11 | 10 skipped | All skipped | TRIVIAL |

---

## RECOMMENDED FIX ORDER

### Quick Wins (Near-passing files, 1-3 failures):
1. **test_entitlement_service.py** — 2 failed, 11 passed. Fix: update plan hierarchy expectations.
2. **test_team_subscription_management.py** — 1 failed, 3 passed, 14 skipped. Fix: verify subscription endpoint.
3. **test_customer_portal_auth.py** — 2 failed, 4 passed, 15 skipped. Fix: portal auth flow.
4. **test_phase_b_sprint.py** — 3 failed, 10 passed. Fix: vendor credit/bills endpoints.
5. **test_estimate_workflow_buttons.py** — 4 failed, 8 passed. Fix: estimate workflow expectations.

### High-Impact (Most tests, auth fixture needed):
1. Add shared `conftest.py` with login fixture → would fix all "No auth mechanism" files simultaneously.
2. Fix Cluster 1 (Items) and Cluster 2 (Estimates) for deepest business logic coverage.

### Skip for Now:
- Cluster 6 (Zoho) — All tests skipped/deprecated. Low value.
- Files with all tests skipped (8 files) — No active test value.

---

*This register should be updated as files are fixed and promoted to the core test suite.*
