# SECTION F — TRIAGE REFLECTIONS

## Which files were hard to classify? Why?

1. **Sprint-named files testing unique modules** — Files like `test_phase_b_sprint.py` (delivery challans), `test_sprint_6b_knowledge_pipeline.py` (EFI process queue), and `test_sprint_6c_cursor_pagination.py` (cursor pagination) were named as sprint artifacts but are the ONLY tests for their respective features. Classified them as Bucket A because the functionality they test is unique. Lesson: sprint naming doesn't mean the tests lack ongoing value.

2. **test_comprehensive_erp_modules.py** — This tests items, contacts, invoices, estimates across the board. Core suite doesn't cover these modules, but dedicated Bucket A files do (test_items_enhanced, test_contacts_enhanced, etc.). Classified as Bucket B because it's a shallow smoke test that would become redundant once the dedicated files are fixed.

3. **test_new_features_iteration64.py** — Named as an iteration artifact (suggesting Bucket C) but tests unique org settings export/import functionality. Classified as Bucket A. Iteration naming is misleading.

4. **test_production_readiness_iteration103.py** — Tests Razorpay refund, Form16, SLA config, pagination. Mix of modules. Core has Razorpay coverage but not refund-specific. Kept as Bucket A due to unique SLA/Form16 coverage.

5. **Zoho test files** — All 5 are entirely skipped with deprecation marks. They test unique Zoho integration, but since ALL tests are skipped, they provide zero active coverage. Classified as Bucket A (unique) but noted as effectively dormant.

## Were any Bucket A files that you expected to be TRIVIAL actually harder than expected?

**Yes — the 44 credential-fix files.** I expected that changing `admin@battwheels.in` → `dev@battwheels.internal` would make most pass. In reality, only **1 out of 44** (test_sprint_6c_cursor_pagination) passed cleanly after the credential fix. The remaining 43 have secondary issues:

- **No auth fixture:** Many files (especially test_bills_inventory_enhanced, test_contacts_enhanced, test_items_enhanced families) make HTTP requests WITHOUT any authentication headers at all. They need a login fixture added.
- **Test data expectations:** Tests assert specific counts, IDs, or data structures that don't exist in the dev database. E.g., test_employee_creation expects creating a new employee will succeed but the org doesn't have the right plan/entitlements.
- **Cascading failures:** Some tests are ordered (test_01, test_02, etc.) where test_01 creates data used by test_02. When test_01 fails, everything cascades.

The **sed-based `\b` word boundary** also incorrectly matched `platform-admin@battwheels.in` → `platform-dev@battwheels.internal` in 2 files. This was caught and corrected during verification.

## Any files that test functionality you suspect is genuinely broken (not just environment issues)?

1. **test_efi_intelligence.py** — The `RankingContext` constructor now requires an `organization_id` argument that the tests don't provide. This suggests a **real API change** that wasn't accompanied by test updates. The EFI ranking feature may have been modified without verifying backward compatibility.

2. **test_entitlement_service.py** — Two tests fail because `get_minimum_plan_for_feature("advanced_reports")` returns `starter` instead of `professional`, and the exception detail shows `"Payroll"` instead of `"hr_payroll"`. This could indicate plan hierarchy was restructured without updating tests, or the plan structure genuinely changed and tests need updating.

3. **test_audit_logging.py** — 14 of 15 tests error out. The one test that passes is basic auth. All audit-trail tests (invoice create, update, void producing audit entries) fail. This could indicate the audit logging system has issues, or the test expectations don't match current behavior.

4. **test_reports.py** — All 16 tests fail. Given that reports (P&L, balance sheet, trial balance) are critical business features, this warrants investigation to determine if the reports API is actually broken or just the test expectations are wrong.

5. **test_setup_wizard_email_usage.py** — All 14 tests error. Setup wizard and email usage are onboarding-critical features.

## What could you not verify?

1. **Full pytest run completion** — The full pytest suite takes >5 minutes and timed out. I could not get a final total count of remaining failures across all active test files to provide a precise improvement metric.

2. **Whether "no auth" files would pass with auth added** — I classified 24 files as needing auth mechanisms, but I did not actually add auth fixtures to test this theory. The true fix effort could be higher if endpoints have changed.

3. **Zoho integration state** — All 5 Zoho test files are entirely skipped. I cannot determine if the underlying Zoho integration actually works. The skip conditions may be legitimate (no Zoho credentials in dev) or may mask real issues.

4. **Whether the 8 all-skipped files should be archived** — test_ticket_workflow_lifecycle, test_zoho_api, test_zoho_books_module, test_zoho_extended, test_zoho_new_modules, test_invoices_estimates_enhanced_zoho, test_items_enhanced_zoho_columns, and test_items_zoho_features are all 100% skipped. They remain in active test files but contribute zero coverage. I kept them as Bucket A because the features they reference are real, but they're effectively dead weight until skip conditions are addressed.

5. **Impact on full pytest failure count** — The pre-triage baseline was ~1700 failures/errors. With 24 files archived (containing roughly ~550 tests), the theoretical reduction is significant, but I couldn't verify the exact new failure count due to timeout.
