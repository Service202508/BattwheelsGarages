# Battwheels OS — Deployment Guide

## Architecture

Three Railway deployments, one MongoDB Atlas cluster with three databases:

| Deployment  | Railway Service      | MongoDB DB          | Domain                   |
|-------------|---------------------|---------------------|--------------------------|
| Development | battwheels-dev      | battwheels_dev      | dev.battwheels.com       |
| Staging     | battwheels-staging  | battwheels_staging  | staging.battwheels.com   |
| Production  | battwheels-prod     | battwheels          | app.battwheels.com       |

## Prerequisites

1. **MongoDB Atlas** — Create a free M0 cluster at [cloud.mongodb.com](https://cloud.mongodb.com)
   - Create three databases: `battwheels_dev`, `battwheels_staging`, `battwheels`
   - Create a database user with readWrite access
   - Whitelist `0.0.0.0/0` for Railway IP access (or use Atlas private networking)
   - Copy the connection string: `mongodb+srv://user:pass@cluster.mongodb.net/`

2. **Railway account** — Sign up at [railway.app](https://railway.app)

3. **GitHub repo** — Push codebase to a private GitHub repository

## First Deployment (Staging)

1. Go to Railway dashboard -> **New Project** -> **Deploy from GitHub repo**
2. Select your repository
3. Railway auto-detects the `Dockerfile` and `railway.toml`
4. Add environment variables (from `.env.example`):

| Variable | Value |
|----------|-------|
| `MONGO_URL` | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `DB_NAME` | `battwheels_staging` |
| `ENVIRONMENT` | `staging` |
| `JWT_SECRET` | (generate: `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| `SECRET_KEY` | (generate separately) |
| `RESEND_API_KEY` | Your Resend API key |
| `SENTRY_DSN` | Your Sentry DSN |
| `CORS_ORIGINS` | `https://staging.battwheels.com` |
| `RAZORPAY_KEY_ID` | Test mode key |
| `RAZORPAY_KEY_SECRET` | Test mode secret |
| `RAZORPAY_WEBHOOK_SECRET` | Test mode webhook secret |

5. Deploy -> wait for build -> verify `/api/health` returns `200`
6. (Optional) Add custom domain: `staging.battwheels.com`

## Promoting to Production

1. Staging must pass full QA first
2. Create a **separate** Railway service for production
3. Set environment variables with production values:
   - `DB_NAME=battwheels`
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS=https://app.battwheels.com`
   - Generate **new** `JWT_SECRET` and `SECRET_KEY` (never share between environments)
   - Use **live** Razorpay keys
4. Deploy
5. Verify: `curl https://app.battwheels.com/api/health`
6. Run: `DB_NAME=battwheels python3 scripts/verify_prod_org.py`
7. Point DNS for `app.battwheels.com` to Railway's provided URL

## Environment Variable Rules

- **Never** share `JWT_SECRET` or `SECRET_KEY` between environments
- **Never** use production `MONGO_URL` in development
- **Never** use live Razorpay keys in staging
- Each environment gets its own `SENTRY_DSN` project (or use environment tags)

## Running Migrations

```bash
# Test on staging first
DB_NAME=battwheels_staging python3 scripts/migrations/<migration_name>.py

# Then production (with explicit approval)
DB_NAME=battwheels python3 scripts/migrations/<migration_name>.py
```

## Rollback

Railway supports instant rollback to any previous deployment:
1. Go to Railway dashboard -> your service -> **Deployments** tab
2. Click the deployment you want to roll back to
3. Click **Redeploy**

## Health Check

The `/api/health` endpoint returns:
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected",
  "response_time_ms": 12.5,
  "timestamp": "2026-02-25T12:00:00Z"
}
```

Status codes: `200` = healthy, `503` = unhealthy (triggers Railway restart).

## Monitoring

- **Sentry**: Errors and performance traces (staging + production only)
- **Railway Logs**: Real-time log streaming in Railway dashboard
- **Health endpoint**: Polled every 30s by Railway
