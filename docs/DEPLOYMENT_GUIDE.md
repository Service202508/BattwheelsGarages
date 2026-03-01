# Battwheels OS — Deployment Guide

## Prerequisites

- **MongoDB Atlas** cluster (separate clusters for staging and production)
- **Node.js** 18+ with Yarn
- **Python** 3.11+
- **External service accounts:**
  - Resend (transactional email)
  - Razorpay (payment gateway)
  - Sentry (error monitoring)
  - Emergent LLM (AI features)

---

## Environment Setup

### 1. Clone and install

```bash
git clone <repo-url> && cd battwheels-os
cd backend && pip install -r requirements.txt && cd ..
cd frontend && yarn install && cd ..
```

### 2. Configure environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit each `.env` file with values for your target environment.

### 3. Required vs optional variables

| Variable | Required | Notes |
|---|---|---|
| `MONGO_URL` | Yes | MongoDB connection string |
| `DB_NAME` | Yes | `battwheels_dev`, `battwheels_staging`, or `battwheels` |
| `JWT_SECRET` | Yes | Must be unique per environment |
| `CORS_ORIGINS` | Yes | Frontend URL for CORS |
| `REACT_APP_BACKEND_URL` | Yes | Backend API URL |
| `RESEND_API_KEY` | Yes | Email delivery |
| `RAZORPAY_KEY_ID` | Production | Payment processing |
| `SENTRY_DSN` | Recommended | Error tracking |
| `EMERGENT_LLM_KEY` | Optional | AI features |

### 4. Generate a secure JWT_SECRET

```bash
openssl rand -hex 32
```

Use a different secret for each environment.

---

## Deployment Steps

### Development (Local)

```bash
# Terminal 1: Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend
yarn start
```

Verify: `curl http://localhost:8001/api/health`

### Staging

1. Push to `develop` branch — CI pipeline runs automatically
2. If all checks pass, `deploy-staging` job executes
3. Verify staging: `curl https://staging.battwheels.com/api/health`

### Production

1. Merge `develop` into `main` via pull request
2. CI pipeline runs on `main` push
3. `deploy-production` job requires manual approval (GitHub Environment)
4. Approve deployment in GitHub Actions UI
5. Verify production: `curl https://battwheels.com/api/health`

---

## Safety Checklist (Before Every Production Deploy)

```
[ ] All backend tests pass (bash scripts/run_core_tests.sh)
[ ] Frontend builds with 0 errors (cd frontend && npx craco build)
[ ] Frontend syntax check passes (bash scripts/verify_platform.sh)
[ ] verify_prod_org.py shows ALL GREEN
[ ] verify_platform.sh shows 6/6 PASS
[ ] No .env files in git (git ls-files | grep '\.env$')
[ ] CORS_ORIGINS set correctly for target environment
[ ] JWT_SECRET is unique per environment
[ ] Sentry DSN is configured and verified
[ ] Database backup taken before deploy
```

---

## Rollback Procedure

### Code rollback

```bash
# Find last known good commit
git log --oneline -10

# Revert to it
git revert HEAD --no-edit  # Revert last commit
# OR
git reset --hard <commit-sha>  # Hard reset (destructive)
git push --force-with-lease origin main
```

### Database rollback

1. Locate the latest backup in MongoDB Atlas: Clusters > Backup > Restores
2. Restore to a new cluster (do NOT overwrite production)
3. Verify restored data, then swap the `MONGO_URL` if needed

### Emergency contacts

- Platform Admin: platform-admin@battwheels.in
- Escalation: Check team Slack channel #battwheels-ops

---

## Monitoring

### Health check endpoint

```
GET /api/health
Expected: {"status": "healthy", "mongodb": "connected"}
```

### Sentry dashboard

- URL: https://sentry.io (check organization settings for project link)
- Alerts configured for: unhandled exceptions, 5xx spike, slow transactions

### When alerts fire

1. Check Sentry for error details and stack trace
2. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
3. Run `bash scripts/verify_platform.sh` for full health check
4. If production is down, initiate rollback procedure above
5. Post-incident: document root cause in `/app/docs/` directory
