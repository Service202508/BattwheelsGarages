# BATTWHEELS OS — DISASTER RECOVERY RUNBOOK

**Version:** 1.0  
**Date:** February 2026  
**Owner:** Platform Engineering

---

## 1. Scope

This runbook covers database backup/restore procedures for Battwheels OS. The application runs on Kubernetes (Emergent platform) with MongoDB (local, supervisor-managed).

---

## 2. Backup Configuration

| Item | Value |
|------|-------|
| Database | MongoDB (`test_database`) at `mongodb://localhost:27017` |
| Backup tool | `mongodump` (installed at `/usr/bin/mongodump`) |
| Backup directory | `/var/backups/mongodb/` |
| Schedule | Daily at 02:00 UTC via `/etc/cron.d/battwheels-mongodb-backup` |
| Retention | 7 days (older backups auto-pruned by script) |
| Backup script | `/app/scripts/backup_mongodb.sh` |
| Log file | `/var/log/mongodb_backup.log` |

---

## 3. Verify Backups Are Running

```bash
# Check last backup log entries
tail -20 /var/log/mongodb_backup.log

# List available backups
ls -lh /var/backups/mongodb/

# Count collections in latest backup
find /var/backups/mongodb -name "*.bson.gz" | wc -l
# Expected: 218+ files
```

---

## 4. Manual Backup (Run Immediately)

```bash
DB_NAME=test_database MONGO_URL=mongodb://localhost:27017 /app/scripts/backup_mongodb.sh
```

---

## 5. Restore from Backup

### Step 1: Identify backup to restore

```bash
ls -lt /var/backups/mongodb/
# Pick the most recent directory, e.g.: test_database_20260224_020000
```

### Step 2: Stop the application (prevent writes during restore)

```bash
sudo supervisorctl stop backend
```

### Step 3: (Optional) Drop existing database

```bash
mongosh mongodb://localhost:27017 --eval "use test_database; db.dropDatabase()"
```

### Step 4: Restore from backup

```bash
BACKUP_PATH="/var/backups/mongodb/test_database_YYYYMMDD_HHMMSS"

mongorestore \
  --uri="mongodb://localhost:27017" \
  --db="test_database" \
  --gzip \
  --drop \
  "${BACKUP_PATH}/test_database/"
```

### Step 5: Verify restore

```bash
mongosh mongodb://localhost:27017 --eval "
  use test_database;
  print('Collections:', db.getCollectionNames().length);
  print('Orgs:', db.organizations.countDocuments({}));
  print('Users:', db.users.countDocuments({}));
  print('Invoices:', db.invoices.countDocuments({}));
"
```

### Step 6: Restart the backend

```bash
sudo supervisorctl start backend
# Verify health
curl http://localhost:8001/api/health
```

---

## 6. RTO / RPO Targets

| Metric | Target |
|--------|--------|
| **RPO (Recovery Point Objective)** | ≤ 24 hours (daily backup) |
| **RTO (Recovery Time Objective)** | ≤ 2 hours (manual restore) |

---

## 7. Incident Response Playbook

### Scenario A: Database Corruption

1. Run manual backup of any accessible data: `mongodump --db test_database --out /tmp/emergency_backup`
2. Execute restore procedure (Section 5)
3. Notify all active organizations via email (Resend)
4. Post incident report within 48 hours

### Scenario B: Complete Pod/Container Loss

The local MongoDB data is stored on the container's filesystem. In a full pod restart:
- **Action:** MongoDB data may be lost if not using persistent volumes
- **Mitigation:** Contact Emergent platform support immediately for volume recovery
- **Long-term fix:** Migrate to MongoDB Atlas with automated cloud backups

### Scenario C: Accidental Data Deletion by User

1. Identify the affected collection and time of deletion from audit logs: `GET /api/audit-logs`
2. Restore from the backup immediately prior to deletion timestamp
3. If partial restore needed, use `mongorestore --collection <collection_name>`

---

## 8. Production Recommendations (Pre-Launch)

- [ ] **Migrate to MongoDB Atlas** (minimum M10 for production) — enables point-in-time recovery, automated snapshots, and offsite redundancy
- [ ] **Enable Atlas Continuous Backup** — 10-minute RPO
- [ ] **Test restore quarterly** — document results in this runbook
- [ ] **Set up backup monitoring alert** — check `/var/log/mongodb_backup.log` for ERROR strings daily
- [ ] **Offsite storage** — sync `/var/backups/mongodb/` to S3 or GCS bucket

---

## 9. Contacts

| Role | Contact |
|------|---------|
| Platform Engineering | Battwheels Engineering Team |
| Emergent Platform Support | support@emergentagent.com |
| MongoDB Atlas Support | https://support.mongodb.com |

---

*Last updated: February 2026*
