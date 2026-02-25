# Battwheels OS — Database Migrations

All schema migrations live here. Each migration is a standalone Python script
that can be run independently and is **idempotent** (safe to run multiple times).

## Rules

1. **Never modify customer data content** — only structure changes (new fields, indexes, collection renames)
2. **Always test in battwheels_dev first**, then battwheels_staging, then production
3. **Every migration must be idempotent** — running it twice produces the same result
4. **Name format:** `YYYYMMDD_NNN_description.py` (e.g., `20260225_001_add_period_locks_collection.py`)
5. **Log every production run** in `/app/docs/INCIDENTS.md`

## Promotion Path

```
battwheels_dev  →  battwheels_staging  →  battwheels (production)
```

## How to Run

```bash
# Against dev (default)
cd /app/backend && export $(grep -v '^#' .env | xargs) && python3 ../scripts/migrations/YYYYMMDD_NNN_description.py

# Against staging (override DB_NAME)
DB_NAME=battwheels_staging python3 ../scripts/migrations/YYYYMMDD_NNN_description.py

# Against production (requires approval — see ENVIRONMENT_SOP.md Rule 3)
DB_NAME=battwheels python3 ../scripts/migrations/YYYYMMDD_NNN_description.py
```

## Migration Log

| Date | Migration | Dev | Staging | Prod | Notes |
|------|-----------|-----|---------|------|-------|
| — | — | — | — | — | No migrations run yet |
