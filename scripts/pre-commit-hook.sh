#!/bin/bash
# Battwheels OS — Pre-commit hook
# Blocks commits containing broken code.
# Install: cp scripts/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(jsx|js|tsx)$' || true)

# a) ESLint on staged JS/JSX/TSX files (frontend only)
FRONTEND_FILES=$(echo "$STAGED_FILES" | grep "^frontend/src/" | sed 's|^frontend/||' || true)
if [ -n "$FRONTEND_FILES" ]; then
  echo "Running ESLint on staged frontend files..."
  cd /app/frontend
  npx eslint $FRONTEND_FILES --quiet
  if [ $? -ne 0 ]; then
    echo "ESLint failed. Fix errors before committing."
    exit 1
  fi
  cd /app
fi

# b) Fast syntax check if any frontend files are staged
if echo "$STAGED_FILES" | grep -q "^frontend/"; then
  echo "Running frontend syntax check..."
  cd /app/frontend
  npx eslint src/ --quiet --no-eslintrc --rule '{"no-dupe-args": "error", "no-dupe-keys": "error"}' 2>/dev/null
  cd /app
fi

# c) Python syntax check on staged .py files
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
if [ -n "$STAGED_PY" ]; then
  echo "Running Python syntax check on staged files..."
  for f in $STAGED_PY; do
    python -m py_compile "/app/$f" 2>&1
    if [ $? -ne 0 ]; then
      echo "Python syntax error in $f. Fix before committing."
      exit 1
    fi
  done
fi

echo "Pre-commit checks passed."
exit 0
