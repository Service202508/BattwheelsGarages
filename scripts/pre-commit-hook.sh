#!/bin/bash
# Battwheels OS — Pre-commit hook
# Blocks commits containing broken code.
# Install: bash scripts/install-hooks.sh

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM || true)

# a) Syntax check staged frontend JS/JSX/TSX files using Node parser
FRONTEND_FILES=$(echo "$STAGED_FILES" | grep "^frontend/src/.*\.\(jsx\|js\|tsx\)$" || true)
if [ -n "$FRONTEND_FILES" ]; then
  echo "Checking frontend file syntax..."
  SYNTAX_FAIL=0
  for f in $FRONTEND_FILES; do
    NODE_PATH=/app/frontend/node_modules node -e "
      const fs = require('fs');
      const acorn = require('acorn');
      const jsx = require('acorn-jsx');
      const parser = acorn.Parser.extend(jsx());
      try {
        parser.parse(fs.readFileSync('/app/$f', 'utf8'), { sourceType: 'module', ecmaVersion: 2022 });
      } catch(e) {
        console.error('Syntax error in $f:', e.message);
        process.exit(1);
      }
    " 2>&1
    if [ $? -ne 0 ]; then
      SYNTAX_FAIL=1
    fi
  done
  if [ $SYNTAX_FAIL -ne 0 ]; then
    echo "Frontend syntax check failed. Fix errors before committing."
    exit 1
  fi
  echo "Frontend syntax: OK"
fi

# b) Check for duplicate imports in staged frontend files
if [ -n "$FRONTEND_FILES" ]; then
  for f in $FRONTEND_FILES; do
    DUPES=$(grep "^import " "/app/$f" | sort | uniq -d || true)
    if [ -n "$DUPES" ]; then
      echo "Duplicate import in $f:"
      echo "$DUPES"
      echo "Fix duplicate imports before committing."
      exit 1
    fi
  done
fi

# c) Python syntax check on staged .py files
STAGED_PY=$(echo "$STAGED_FILES" | grep '\.py$' || true)
if [ -n "$STAGED_PY" ]; then
  echo "Checking Python file syntax..."
  for f in $STAGED_PY; do
    python -m py_compile "/app/$f" 2>&1
    if [ $? -ne 0 ]; then
      echo "Python syntax error in $f. Fix before committing."
      exit 1
    fi
  done
  echo "Python syntax: OK"
fi

echo "Pre-commit checks passed."
exit 0
