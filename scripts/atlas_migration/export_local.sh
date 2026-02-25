#!/bin/bash
# =============================================================
#  EXPORT: Emergent local MongoDB → BSON dump files
#  Run this FIRST, before creating the Atlas cluster
#  Output: /app/scripts/atlas_migration/dumps/
# =============================================================
set -euo pipefail

DUMP_DIR="/app/scripts/atlas_migration/dumps"
MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"

echo "============================================================"
echo "  EXPORT: Local MongoDB → BSON dumps"
echo "  Source: $MONGO_URL"
echo "  Output: $DUMP_DIR"
echo "  Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"

rm -rf "$DUMP_DIR"
mkdir -p "$DUMP_DIR"

# --- Production (battwheels) ---
echo ""
echo ">>> Exporting battwheels (production)..."
mongodump \
  --uri="$MONGO_URL" \
  --db=battwheels \
  --out="$DUMP_DIR" \
  --quiet

PROD_COUNT=$(find "$DUMP_DIR/battwheels" -name "*.bson" | wc -l)
echo "    Collections exported: $PROD_COUNT"

# --- Development (battwheels_dev) ---
echo ""
echo ">>> Exporting battwheels_dev (development)..."
mongodump \
  --uri="$MONGO_URL" \
  --db=battwheels_dev \
  --out="$DUMP_DIR" \
  --quiet

DEV_COUNT=$(find "$DUMP_DIR/battwheels_dev" -name "*.bson" | wc -l)
echo "    Collections exported: $DEV_COUNT"

# --- Staging (battwheels_staging) - empty but export structure ---
echo ""
echo ">>> Exporting battwheels_staging (staging - empty)..."
mongodump \
  --uri="$MONGO_URL" \
  --db=battwheels_staging \
  --out="$DUMP_DIR" \
  --quiet

STAGING_COUNT=$(find "$DUMP_DIR/battwheels_staging" -name "*.bson" 2>/dev/null | wc -l)
echo "    Collections exported: $STAGING_COUNT"

# --- Summary ---
TOTAL_SIZE=$(du -sh "$DUMP_DIR" | cut -f1)
echo ""
echo "============================================================"
echo "  EXPORT COMPLETE"
echo "  Total size: $TOTAL_SIZE"
echo "  battwheels:         $PROD_COUNT collections"
echo "  battwheels_dev:     $DEV_COUNT collections"
echo "  battwheels_staging: $STAGING_COUNT collections"
echo ""
echo "  Next: Run import_to_atlas.sh with your Atlas connection string"
echo "============================================================"
