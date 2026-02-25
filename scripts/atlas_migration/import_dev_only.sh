#!/bin/bash
# =============================================================
#  IMPORT (DEV ONLY): battwheels_dev → MongoDB Atlas
#  Safe first step — validate the pipeline before production
#
#  Usage:
#    ./import_dev_only.sh "mongodb+srv://user:pass@cluster.mongodb.net"
# =============================================================
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "ERROR: Atlas connection string required"
  echo "Usage: ./import_dev_only.sh \"mongodb+srv://user:pass@cluster.mongodb.net\""
  exit 1
fi

ATLAS_URI="$1"
DUMP_DIR="/app/scripts/atlas_migration/dumps"

if [ ! -d "$DUMP_DIR/battwheels_dev" ]; then
  echo "ERROR: battwheels_dev dump not found at $DUMP_DIR/battwheels_dev"
  echo "Run export_local.sh first"
  exit 1
fi

echo "============================================================"
echo "  IMPORT: battwheels_dev → MongoDB Atlas"
echo "  Target: Atlas cluster"
echo "  Source: $DUMP_DIR/battwheels_dev"
echo "  Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"

echo ""
echo ">>> Importing battwheels_dev (development)..."
mongorestore \
  --uri="$ATLAS_URI" \
  --db=battwheels_dev \
  --dir="$DUMP_DIR/battwheels_dev" \
  --drop

echo ""
echo "============================================================"
echo "  IMPORT COMPLETE — battwheels_dev only"
echo ""
echo "  Next: Run verify_dev_only.sh to confirm counts match"
echo "============================================================"
