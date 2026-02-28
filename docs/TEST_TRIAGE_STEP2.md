# STEP 2 — TEST FILE TRIAGE CLASSIFICATION (107 Excluded Files)

## Core Suite Coverage Reference (25 files)
Modules covered: Auth/Security, Multi-tenancy (CRUD/scoping/isolation), GST (module/GSTR-3B/credit notes/statutory), Finance, Subscription/SaaS (safety/onboarding/entitlements/Razorpay), RBAC (portals/negative), Tickets, Payroll Statutory, Period Locks, Journal Audit, P0/P1 Fixes.

---

| # | File Name | Tests | Module/Feature (1-line) | Core Covers? | Bucket |
|---|-----------|-------|------------------------|-------------|--------|
| 1 | test_csrf_middleware.py | 6 | CSRF middleware validation (Phase 0 addition) | NO | **A** |
| 2 | test_sanitization_middleware.py | 8 | Input sanitization middleware (Phase 0 addition) | NO | **A** |
| 3 | test_gstr3b_rcm.py | 4 | GSTR-3B Reverse Charge Mechanism (Phase 0 addition) | Partial (GST) | **A** |
| 4 | test_calculations_regression.py | 29 | Line item tax/discount calculations (unit test, no HTTP) | NO | **A** |
| 5 | test_efi_guidance.py | 22 | EFI Hinglish templates (unit test, no HTTP) | NO | **A** |
| 6 | test_efi_intelligence.py | 15 | EFI model-aware ranking (unit test, no HTTP) | NO | **A** |
| 7 | test_entitlement_service.py | 14 | Entitlement service internals (unit test, no HTTP) | Partial (API) | **A** |
| 8 | test_knowledge_brain.py | 16 | LLM provider factory + knowledge brain (unit test, no HTTP) | NO | **A** |
| 9 | test_ai_diagnostic_assistant.py | 10 | AI diagnostic assistant endpoints | NO | **A** |
| 10 | test_all_settings.py | 17 | Settings categories API | NO | **A** |
| 11 | test_all_settings_complete.py | 25 | Settings complete: users, roles, org panels | NO | **A** |
| 12 | test_audit_logging.py | 15 | Audit trail on invoice create/update/void | NO | **A** |
| 13 | test_banking_stock_transfers.py | 22 | Banking accounts + stock transfer CRUD | NO | **A** |
| 14 | test_bills_inventory_enhanced.py | 38 | Bills enhanced module: CRUD, filters, payments | NO | **A** |
| 15 | test_complaint_dashboard.py | 19 | Complaint/ticket dashboard (multi-role) | Partial (Tickets) | **A** |
| 16 | test_composite_items_invoice_settings.py | 24 | Composite items + invoice settings | NO | **A** |
| 17 | test_contact_integration.py | 23 | Contact integration search API | NO | **A** |
| 18 | test_contacts_enhanced.py | 37 | Contacts tags CRUD, enhanced contacts | NO | **A** |
| 19 | test_contacts_invoices_enhanced.py | 35 | Contacts + invoices enhanced summary/CRUD | NO | **A** |
| 20 | test_convert_invoice_stock_transfers.py | 24 | Estimate-to-invoice conversion + stock | NO | **A** |
| 21 | test_customer_portal.py | 19 | Customer portal dashboard + features | NO | **A** |
| 22 | test_customer_portal_auth.py | 21 | Customer portal auth (enable, login, tokens) | NO | **A** |
| 23 | test_customers_enhanced.py | 52 | Customers enhanced: settings, summary, sync | NO | **A** |
| 24 | test_employee_creation.py | 7 | Employee CRUD (create, list, update) | NO | **A** |
| 25 | test_employee_module.py | 21 | Employee module comprehensive (CRUD + roles) | NO | **A** |
| 26 | test_efi_guided.py | 21 | EFI guided: seed data, embeddings, search | NO | **A** |
| 27 | test_efi_intelligence_api.py | 15 | EFI intelligence: guidance snapshots, feedback | NO | **A** |
| 28 | test_efi_module.py | 24 | EFI failure cards CRUD | NO | **A** |
| 29 | test_efi_search_embeddings.py | 21 | EFI embeddings: status, generate, search | NO | **A** |
| 30 | test_estimate_bug_fixes.py | 11 | Estimate bug fixes (data key, line_items) | NO | **A** |
| 31 | test_estimate_edit_status.py | 7 | Estimate edit + status transitions | NO | **A** |
| 32 | test_estimate_workflow_buttons.py | 12 | Estimate workflow (ensure, approve, reject) | NO | **A** |
| 33 | test_estimates_enhanced.py | 35 | Estimates enhanced: settings, summary, reports | NO | **A** |
| 34 | test_estimates_phase1.py | 32 | Estimates phase 1: preferences, automation | NO | **A** |
| 35 | test_estimates_phase2.py | 22 | Estimates phase 2: PDF templates, custom fields | NO | **A** |
| 36 | test_financial_time_docs.py | 31 | Financial dashboard: summary, receivables, payables | NO | **A** |
| 37 | test_gst_accounting_flow.py | 20 | GST accounting flow: ticket-to-invoice with GST | Partial (GST) | **A** |
| 38 | test_hr_module.py | 16 | HR: attendance, leave, team summary | NO | **A** |
| 39 | test_insights.py | 34 | Revenue/business insights API | NO | **A** |
| 40 | test_inventory_adjustments_phase2.py | 15 | Inventory adjustments: CSV export/import | NO | **A** |
| 41 | test_inventory_adjustments_v2.py | 18 | Inventory adjustments: reasons CRUD, create/approve | NO | **A** |
| 42 | test_inventory_hr_modules.py | 33 | Inventory list/filter + HR combined module test | NO | **A** |
| 43 | test_invoice_automation.py | 20 | Invoice automation: aging, overdue, reminders | NO | **A** |
| 44 | test_invoice_notification.py | 21 | Invoice PDF + email notification | NO | **A** |
| 45 | test_invoices_estimates_enhanced_zoho.py | 19 | Invoice enhanced: Zoho-parity actions (send, void) | NO | **A** |
| 46 | test_items_enhanced.py | 19 | Items: groups, warehouses, categories | NO | **A** |
| 47 | test_items_enhanced_parts_fix.py | 6 | Items trailing-slash bug fix verification | NO | **A** |
| 48 | test_items_enhanced_zoho_columns.py | 14 | Items: Zoho column mapping, export | NO | **A** |
| 49 | test_items_estimates_integration.py | 16 | Items-estimates pricing integration | NO | **A** |
| 50 | test_items_phase2.py | 23 | Items price lists: contact pricing | NO | **A** |
| 51 | test_items_phase3.py | 10 | Items preferences API | NO | **A** |
| 52 | test_items_pricelists_inventory.py | 13 | Items + Zoho price lists + inventory | NO | **A** |
| 53 | test_items_zoho_features.py | 28 | Items search/sort/filter Zoho-parity | NO | **A** |
| 54 | test_new_ai_features_map_integration.py | 14 | AI issue suggestions (public + auth) | NO | **A** |
| 55 | test_new_features_iteration64.py | 15 | Inventory stock endpoint + org settings export/import + customer portal | NO | **A** |
| 56 | test_notifications_export.py | 21 | Notifications CRUD + data export | NO | **A** |
| 57 | test_onboarding_checklist.py | 16 | Onboarding checklist status API | NO | **A** |
| 58 | test_p2_p3_p4_pwa.py | 34 | WhatsApp settings + P2/P3/P4 features + PWA | NO | **A** |
| 59 | test_password_reset.py | 9 | Self-service password change (uses localhost) | Partial (pwd mgmt) | **A** |
| 60 | test_payments_received.py | 25 | Payments received: summary, list, filters | NO | **A** |
| 61 | test_phase_b_sprint.py | 16 | Delivery challans CRUD (unique module) | NO | **A** |
| 62 | test_price_lists_enhanced.py | 20 | Price lists CRUD via Zoho API | NO | **A** |
| 63 | test_production_readiness_iteration103.py | 26 | Razorpay refund + Form16 + SLA config/dashboard | Partial (Razorpay) | **A** |
| 64 | test_projects_tds_features.py | 26 | Projects CRUD + TDS calculation | NO | **A** |
| 65 | test_public_ticket_master_data.py | 21 | Public ticket creation + master data seed | Partial (Tickets) | **A** |
| 66 | test_recurring_invoices_pdf.py | 21 | Recurring invoices CRUD + PDF generation | NO | **A** |
| 67 | test_reports.py | 16 | Reports: profit-loss, balance sheet, trial balance | NO | **A** |
| 68 | test_sales_orders_enhanced.py | 28 | Sales orders: settings, summary, CRUD, reports | NO | **A** |
| 69 | test_serial_batch_pdf_templates.py | 34 | Serial/batch tracking + PDF templates | NO | **A** |
| 70 | test_service_ticket_dashboard.py | 15 | Service ticket dashboard stats | Partial (Tickets) | **A** |
| 71 | test_setup_wizard_email_usage.py | 14 | Setup wizard + email usage API | NO | **A** |
| 72 | test_sprint_6b_knowledge_pipeline.py | 13 | EFI knowledge pipeline (process-queue) | NO | **A** |
| 73 | test_sprint_6c_cursor_pagination.py | 17 | Cursor-based pagination (tickets, contacts, items) | NO | **A** |
| 74 | test_stock_indicator.py | 9 | Stock availability indicator on estimates | NO | **A** |
| 75 | test_team_subscription_management.py | 18 | Team subscription: current, entitlements, plans | Partial (Subs) | **A** |
| 76 | test_ticket_estimate_integration.py | 20 | Ticket-estimate ensure/CRUD integration | Partial (Tickets) | **A** |
| 77 | test_ticket_workflow_lifecycle.py | 11 | Ticket workflow: start_work, end_work, status transitions | Partial (Tickets) | **A** |
| 78 | test_zoho_api.py | 51 | Zoho CRUD: contacts, items, invoices, estimates | NO | **A** |
| 79 | test_zoho_books_module.py | 17 | Zoho Books: customers, invoices, bills | NO | **A** |
| 80 | test_zoho_extended.py | 16 | Zoho: delivery challans, projects, recurring | NO | **A** |
| 81 | test_zoho_new_modules.py | 34 | Zoho: recurring bills, vendor credits, purchase orders | NO | **A** |
| 82 | test_zoho_parity_services.py | 15 | Zoho parity: finance calc service, contacts, estimates | NO | **A** |
| 83 | test_data_management.py | 14 | Data management: counts, sync, test-connection | NO | **A** |
| 84 | test_cross_portal_validation.py | 11 | Cross-portal data validation (direct DB, no HTTP) | YES (RBAC portals) | **B** |
| 85 | test_api_versioning_multitenancy.py | 18 | API health + auth + versioning basics | YES (Stabilisation) | **B** |
| 86 | test_mobile_responsive_p1.py | 11 | Auth login + platform audit status | YES (Stabilisation) | **B** |
| 87 | test_erp_api.py | 22 | Basic auth + health + ERP smoke test | YES (Stabilisation) | **B** |
| 88 | test_data_consistency_audit.py | 15 | Org context + data consistency checks | YES (Multi-tenant) | **B** |
| 89 | test_comprehensive_erp_modules.py | 44 | Items/contacts/invoices/estimates smoke (all in Bucket A) | YES (Bucket A files) | **B** |
| 90 | test_17flow_audit.py | 44 | 17-step platform flow audit (signup→reports) | YES (Broad smoke) | **C** |
| 91 | test_comprehensive_audit.py | 46 | Comprehensive platform audit (uses API_BASE_URL) | YES (Wrong env var) | **C** |
| 92 | test_enterprise_qa_audit.py | 25 | Enterprise QA audit: multi-role login checks | YES (Broad smoke) | **C** |
| 93 | test_audit_blockers.py | 34 | Audit blockers: health, login, org endpoints | YES (Broad smoke) | **C** |
| 94 | test_final_certification.py | 35 | One-time final certification test | YES (One-time) | **C** |
| 95 | test_deployment_ready.py | 14 | One-time deployment readiness check | YES (One-time) | **C** |
| 96 | test_upgrade_regression.py | 35 | One-time upgrade regression check | YES (One-time) | **C** |
| 97 | test_regression_suite.py | 19 | Regression suite (uses TEST_API_URL) | YES (Wrong env var) | **C** |
| 98 | test_hardening_sprint.py | 20 | Hardening sprint: health, versioning | YES (Sprint artifact) | **C** |
| 99 | test_phase_cde.py | 12 | Phase CDE sprint (hardcoded localhost:8001) | YES (Sprint artifact) | **C** |
| 100 | test_phase_cde_comprehensive.py | 20 | Phase CDE comprehensive (sprint artifact) | YES (Sprint artifact) | **C** |
| 101 | test_phase_fg.py | 16 | Phase FG sprint (hardcoded localhost:8001) | YES (Sprint artifact) | **C** |
| 102 | test_phase_fg_comprehensive.py | 33 | Phase FG comprehensive (sprint artifact) | YES (Sprint artifact) | **C** |
| 103 | test_battwheels_evolution_sprint.py | 25 | Evolution sprint grab-bag (tickets, HR, EFI) | YES (Sprint artifact) | **C** |
| 104 | test_key_modules_iteration59.py | 34 | Iteration 59 module grab-bag | YES (Sprint artifact) | **C** |
| 105 | test_new_features_iter104.py | 29 | Iteration 104 features: bcrypt, login | YES (Sprint artifact) | **C** |
| 106 | test_week2_features.py | 15 | Week 2 features: audit log, estimates | YES (Sprint artifact) | **C** |
| 107 | test_zoho_parity_regression.py | 8 | Zoho parity regression (uses TEST_API_URL) | YES (Wrong env var) | **C** |

---

## SUMMARY

| Bucket | Count | Description |
|--------|-------|-------------|
| **A** | 83 | Tests unique functionality not covered by core suite. Worth fixing. |
| **B** | 6 | Duplicates coverage already in core suite. Candidate for deletion. |
| **C** | 18 | Sprint-specific or one-off tests with no ongoing value. Candidate for archive. |
| **Total** | 107 | |

### Bucket A Breakdown by Fix Effort (preliminary):
- **Phase 0 additions** (3 files, 18 tests): Already passing, just add to core script
- **Unit tests / no HTTP** (5 files, 96 tests): No BASE_URL needed, likely pass as-is
- **HTTP tests needing BASE_URL fix** (75 files, ~1600 tests): Need environment config fixes

### Bucket B Files (6):
- test_cross_portal_validation.py, test_api_versioning_multitenancy.py, test_mobile_responsive_p1.py
- test_erp_api.py, test_data_consistency_audit.py, test_comprehensive_erp_modules.py

### Bucket C Files (18):
- Sprint artifacts: test_hardening_sprint, test_phase_cde, test_phase_cde_comprehensive, test_phase_fg, test_phase_fg_comprehensive, test_battwheels_evolution_sprint, test_week2_features
- Iteration artifacts: test_key_modules_iteration59, test_new_features_iter104
- Audit artifacts: test_17flow_audit, test_comprehensive_audit, test_enterprise_qa_audit, test_audit_blockers
- One-time checks: test_final_certification, test_deployment_ready, test_upgrade_regression
- Wrong env var: test_regression_suite, test_zoho_parity_regression
