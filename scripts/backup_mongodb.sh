#!/usr/bin/env bash
# Battwheels OS — MongoDB Backup Script
# Runs daily via cron. Keeps 7 days of compressed backups.
# Backup dir: /var/backups/mongodb/

set -euo pipefail

BACKUP_DIR="/var/backups/mongodb"
DB_NAME="${DB_NAME:-test_database}"
MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}"
RETENTION_DAYS=7
LOG_FILE="/var/log/mongodb_backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "Starting MongoDB backup — database: ${DB_NAME}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Run mongodump
mongodump \
    --uri="${MONGO_URL}" \
    --db="${DB_NAME}" \
    --out="${BACKUP_PATH}" \
    --gzip \
    2>>"$LOG_FILE"

if [ $? -ne 0 ]; then
    log "ERROR: mongodump failed!"
    exit 1
fi

# Verify the backup produced files
FILE_COUNT=$(find "${BACKUP_PATH}" -name "*.bson.gz" | wc -l)
if [ "$FILE_COUNT" -eq 0 ]; then
    log "ERROR: Backup produced no .bson.gz files — backup is empty!"
    rm -rf "${BACKUP_PATH}"
    exit 1
fi

log "Backup complete: ${BACKUP_PATH} (${FILE_COUNT} collection files)"

# Prune backups older than RETENTION_DAYS
DELETED=$(find "${BACKUP_DIR}" -maxdepth 1 -type d -name "${DB_NAME}_*" \
    -mtime "+${RETENTION_DAYS}" -print -exec rm -rf {} + | wc -l)
log "Pruned ${DELETED} backup(s) older than ${RETENTION_DAYS} days"

log "Backup job finished successfully"
