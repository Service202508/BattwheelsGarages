#!/bin/bash
# Battwheels OS — Core Test Runner
# Sprint Completion Protocol: run this before any merge/deploy
# Category A tests only — core business logic

set -a
source /app/backend/.env 2>/dev/null
source /app/frontend/.env 2>/dev/null
set +a

export REACT_APP_BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"
export TESTING=1

cd /app

CORE_TESTS=(
  backend/tests/test_stabilisation_sprint_fixes.py
  backend/tests/test_p0_security_fixes.py
  backend/tests/test_p1_fixes.py
  backend/tests/test_subscription_safety_fixes.py
  backend/tests/test_multi_tenant.py
  backend/tests/test_multi_tenant_crud.py
  backend/tests/test_multi_tenant_scoping.py
  backend/tests/test_tenant_isolation.py
  backend/tests/test_period_locks.py
  backend/tests/test_gst_module.py
  backend/tests/test_gstr3b_credit_notes.py
  backend/tests/test_credit_notes_p1.py
  backend/tests/test_finance_module.py
  backend/tests/test_password_management.py
  backend/tests/test_rbac_portals.py
  backend/tests/test_saas_onboarding.py
  backend/tests/test_razorpay_integration.py
  backend/tests/test_subscription_entitlements_api.py
  backend/tests/test_entitlement_enforcement.py
  backend/tests/test_tickets_module.py
)

echo "========================================="
echo "  Battwheels OS — Core Test Suite"
echo "  $(date)"
echo "========================================="

python -m pytest "${CORE_TESTS[@]}" -v --tb=short 2>&1

EXIT_CODE=$?
echo ""
echo "========================================="
echo "  Exit code: $EXIT_CODE"
echo "========================================="
exit $EXIT_CODE
