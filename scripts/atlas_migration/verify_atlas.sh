#!/bin/bash
# =============================================================
#  VERIFY: Compare local MongoDB vs Atlas after import
#  Confirms document counts match for all databases
#
#  Usage:
#    ./verify_atlas.sh "mongodb+srv://user:pass@cluster.mongodb.net"
# =============================================================
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "ERROR: Atlas connection string required"
  echo "Usage: ./verify_atlas.sh \"mongodb+srv://user:pass@cluster.mongodb.net\""
  exit 1
fi

ATLAS_URI="$1"
LOCAL_URI="${MONGO_URL:-mongodb://localhost:27017}"

echo "============================================================"
echo "  VERIFY: Local MongoDB vs Atlas"
echo "  Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"

python3 -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def verify():
    local = AsyncIOMotorClient('$LOCAL_URI')
    atlas = AsyncIOMotorClient('$ATLAS_URI')

    all_ok = True

    for db_name in ['battwheels', 'battwheels_dev', 'battwheels_staging']:
        print(f'\n--- {db_name} ---')

        local_db = local[db_name]
        atlas_db = atlas[db_name]

        local_cols = set(await local_db.list_collection_names())
        atlas_cols = set(await atlas_db.list_collection_names())

        # Only check collections that have data locally
        mismatches = []
        checked = 0

        for col in sorted(local_cols):
            local_count = await local_db[col].count_documents({})
            if local_count == 0:
                continue

            checked += 1
            atlas_count = await atlas_db[col].count_documents({}) if col in atlas_cols else 0

            if local_count != atlas_count:
                mismatches.append(f'  MISMATCH: {col} local={local_count} atlas={atlas_count}')
                all_ok = False
            else:
                print(f'  OK: {col} ({local_count})')

        for m in mismatches:
            print(m)

        print(f'  Checked: {checked} collections with data')

    print()
    if all_ok:
        print('RESULT: ALL COUNTS MATCH')
    else:
        print('RESULT: MISMATCHES FOUND — review above')

    local.close()
    atlas.close()

asyncio.run(verify())
"
