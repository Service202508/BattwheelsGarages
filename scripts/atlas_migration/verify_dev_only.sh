#!/bin/bash
# =============================================================
#  VERIFY (DEV ONLY): Compare local vs Atlas for battwheels_dev
#
#  Usage:
#    ./verify_dev_only.sh "mongodb+srv://user:pass@cluster.mongodb.net"
# =============================================================
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "ERROR: Atlas connection string required"
  echo "Usage: ./verify_dev_only.sh \"mongodb+srv://user:pass@cluster.mongodb.net\""
  exit 1
fi

ATLAS_URI="$1"
LOCAL_URI="${MONGO_URL:-mongodb://localhost:27017}"

echo "============================================================"
echo "  VERIFY: battwheels_dev — Local vs Atlas"
echo "  Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"

python3 -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def verify():
    local = AsyncIOMotorClient('$LOCAL_URI')
    atlas = AsyncIOMotorClient('$ATLAS_URI')

    db_name = 'battwheels_dev'
    print(f'\n--- {db_name} ---')

    local_db = local[db_name]
    atlas_db = atlas[db_name]

    local_cols = set(await local_db.list_collection_names())
    atlas_cols = set(await atlas_db.list_collection_names())

    mismatches = []
    checked = 0
    total_local = 0
    total_atlas = 0

    for col in sorted(local_cols):
        local_count = await local_db[col].count_documents({})
        if local_count == 0:
            continue

        checked += 1
        total_local += local_count
        atlas_count = await atlas_db[col].count_documents({}) if col in atlas_cols else 0
        total_atlas += atlas_count

        if local_count != atlas_count:
            mismatches.append(f'  MISMATCH: {col} local={local_count} atlas={atlas_count}')
        else:
            print(f'  OK: {col} ({local_count})')

    for m in mismatches:
        print(m)

    print(f'\n  Collections checked: {checked}')
    print(f'  Total docs local: {total_local}')
    print(f'  Total docs atlas: {total_atlas}')

    if not mismatches:
        print('\n  RESULT: ALL COUNTS MATCH — battwheels_dev verified')
    else:
        print(f'\n  RESULT: {len(mismatches)} MISMATCHES — review above')

    local.close()
    atlas.close()

asyncio.run(verify())
"
