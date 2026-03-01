#!/bin/bash
set -e
PASS=0
FAIL=0

echo "========================================="
echo "BATTWHEELS OS — PLATFORM VERIFICATION"
echo "$(date -u '+%Y-%m-%d %H:%M UTC')"
echo "========================================="
echo ""

# Check 1: Backend health
echo "CHECK 1: Backend API health..."
HEALTH=$(curl -s http://localhost:8001/api/health 2>/dev/null || echo "")
if echo "$HEALTH" | grep -q "healthy"; then
  echo "  PASS — Backend API: healthy"
  PASS=$((PASS+1))
else
  echo "  FAIL — Backend API: NOT RESPONDING"
  FAIL=$((FAIL+1))
fi

# Check 2: Frontend build
echo "CHECK 2: Frontend build..."
cd /app/frontend
BUILD_OUT=$(NODE_OPTIONS="--max-old-space-size=4096" npx craco build 2>&1)
BUILD_EXIT=$?
if [ $BUILD_EXIT -eq 0 ]; then
  echo "  PASS — Frontend build: compiled successfully"
  PASS=$((PASS+1))
else
  echo "  FAIL — Frontend build: FAILED"
  echo "$BUILD_OUT" | tail -10
  FAIL=$((FAIL+1))
fi

# Check 3: Backend core tests
echo "CHECK 3: Backend core tests..."
cd /app
TEST_OUT=$(bash scripts/run_core_tests.sh 2>&1)
FAILED_COUNT=$(echo "$TEST_OUT" | grep -oP '\d+ failed' | head -1 || echo "")
if [ -n "$FAILED_COUNT" ]; then
  echo "  FAIL — Backend tests: $FAILED_COUNT"
  echo "$TEST_OUT" | tail -5
  FAIL=$((FAIL+1))
else
  PASSED=$(echo "$TEST_OUT" | grep -oP '\d+ passed' | head -1)
  echo "  PASS — Backend tests: $PASSED"
  PASS=$((PASS+1))
fi

# Check 4: Production safety
echo "CHECK 4: Production database safety..."
cd /app
source backend/.env 2>/dev/null
PROD_OUT=$(MONGO_URL="$MONGO_URL" python scripts/verify_prod_org.py 2>&1)
if echo "$PROD_OUT" | grep -q "ALL GREEN"; then
  echo "  PASS — Production: ALL GREEN"
  PASS=$((PASS+1))
else
  echo "  FAIL — Production: ISSUES DETECTED"
  echo "$PROD_OUT" | tail -10
  FAIL=$((FAIL+1))
fi

# Check 5: Frontend syntax (acorn parser)
echo "CHECK 5: Frontend syntax check..."
cd /app/frontend
SYNTAX_ERRORS=0
for f in $(find src/ -name "*.jsx" -o -name "*.js" -o -name "*.tsx" | grep -v node_modules); do
  NODE_PATH=/app/frontend/node_modules node -e "
    const fs = require('fs');
    const acorn = require('acorn');
    const jsx = require('acorn-jsx');
    const parser = acorn.Parser.extend(jsx());
    try {
      parser.parse(fs.readFileSync('$f', 'utf8'), { sourceType: 'module', ecmaVersion: 2022 });
    } catch(e) {
      console.error('  Syntax error: $f —', e.message);
      process.exit(1);
    }
  " 2>&1
  if [ $? -ne 0 ]; then
    SYNTAX_ERRORS=$((SYNTAX_ERRORS+1))
  fi
done
if [ $SYNTAX_ERRORS -eq 0 ]; then
  echo "  PASS — Frontend syntax: all files valid"
  PASS=$((PASS+1))
else
  echo "  FAIL — Frontend syntax: $SYNTAX_ERRORS files with errors"
  FAIL=$((FAIL+1))
fi

# Check 6: Python syntax
echo "CHECK 6: Backend Python syntax..."
cd /app/backend
PY_ERRORS=0
for f in $(find . -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*"); do
  python -m py_compile "$f" 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "  Syntax error: $f"
    PY_ERRORS=$((PY_ERRORS+1))
  fi
done
if [ $PY_ERRORS -eq 0 ]; then
  echo "  PASS — Python syntax: all files valid"
  PASS=$((PASS+1))
else
  echo "  FAIL — Python syntax: $PY_ERRORS files with errors"
  FAIL=$((FAIL+1))
fi

# Summary
echo ""
echo "========================================="
TOTAL=$((PASS+FAIL))
echo "RESULT: $PASS/$TOTAL checks passed"
if [ $FAIL -gt 0 ]; then
  echo "STATUS: PLATFORM HAS ISSUES"
  exit 1
else
  echo "STATUS: PLATFORM HEALTHY"
  exit 0
fi
