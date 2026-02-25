#!/bin/bash
# =============================================================
#  IMPORT: BSON dump files → MongoDB Atlas
#  Run AFTER export_local.sh and Atlas cluster creation
#
#  Usage:
#    ./import_to_atlas.sh "mongodb+srv://user:pass@cluster.mongodb.net"
#
#  This imports all three databases: battwheels, battwheels_dev,
#  battwheels_staging
# =============================================================
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "ERROR: Atlas connection string required"
  echo "Usage: ./import_to_atlas.sh \"mongodb+srv://user:pass@cluster.mongodb.net\""
  exit 1
fi

ATLAS_URI="$1"
DUMP_DIR="/app/scripts/atlas_migration/dumps"

if [ ! -d "$DUMP_DIR" ]; then
  echo "ERROR: Dump directory not found at $DUMP_DIR"
  echo "Run export_local.sh first"
  exit 1
fi

echo "============================================================"
echo "  IMPORT: BSON dumps → MongoDB Atlas"
echo "  Target: Atlas cluster"
echo "  Source: $DUMP_DIR"
echo "  Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"

# --- Production (battwheels) ---
if [ -d "$DUMP_DIR/battwheels" ]; then
  echo ""
  echo ">>> Importing battwheels (production)..."
  mongorestore \
    --uri="$ATLAS_URI" \
    --db=battwheels \
    --dir="$DUMP_DIR/battwheels" \
    --drop \
    --quiet
  echo "    battwheels imported successfully"
else
  echo "WARN: No battwheels dump found, skipping"
fi

# --- Development (battwheels_dev) ---
if [ -d "$DUMP_DIR/battwheels_dev" ]; then
  echo ""
  echo ">>> Importing battwheels_dev (development)..."
  mongorestore \
    --uri="$ATLAS_URI" \
    --db=battwheels_dev \
    --dir="$DUMP_DIR/battwheels_dev" \
    --drop \
    --quiet
  echo "    battwheels_dev imported successfully"
else
  echo "WARN: No battwheels_dev dump found, skipping"
fi

# --- Staging (battwheels_staging) ---
if [ -d "$DUMP_DIR/battwheels_staging" ]; then
  echo ""
  echo ">>> Importing battwheels_staging (staging)..."
  mongorestore \
    --uri="$ATLAS_URI" \
    --db=battwheels_staging \
    --dir="$DUMP_DIR/battwheels_staging" \
    --drop \
    --quiet
  echo "    battwheels_staging imported successfully"
else
  echo "WARN: No battwheels_staging dump found, skipping"
fi

echo ""
echo "============================================================"
echo "  IMPORT COMPLETE"
echo ""
echo "  Next steps:"
echo "  1. Run verify_atlas.sh to confirm data integrity"
echo "  2. Update MONGO_URL in your deployment env vars"
echo "============================================================"
