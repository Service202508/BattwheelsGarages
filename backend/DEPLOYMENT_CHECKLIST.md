# Battwheels OS — Beta Deployment Checklist

## Pre-Deployment (before clicking Deploy)

### Environment Variables
- [ ] DB_NAME = battwheels (production)
- [ ] ENVIRONMENT = production
- [ ] REACT_APP_ENVIRONMENT = production
- [ ] REACT_APP_BACKEND_URL = <beta domain>/api/v1
- [ ] JWT_SECRET = <generate new 64-char random string>
- [ ] VAULT_MASTER_KEY = <generate new 64-char random>
- [ ] MONGO_URL = <MongoDB Atlas connection string>
- [ ] RAZORPAY_KEY_ID = <keep test mode for beta>
- [ ] RAZORPAY_KEY_SECRET = <keep test mode>
- [ ] RESEND_API_KEY = <current key, already real>
- [ ] SENDER_EMAIL = service@battwheels.com
- [ ] EMERGENT_LLM_KEY = <current Gemini key>
- [ ] SENTRY_DSN = <current or new prod project>
- [ ] CORS_ORIGINS = https://<beta-domain>

### Database Readiness
- [ ] Platform admin exists in battwheels DB
- [ ] 4 pricing plans seeded
- [ ] 37 GST state codes seeded
- [ ] Default CoA template seeded
- [ ] EFI platform patterns copied (61)
- [ ] Zero test orgs in production

### Security
- [ ] JWT_SECRET is DIFFERENT from dev
- [ ] VAULT_MASTER_KEY is DIFFERENT from dev
- [ ] CORS_ORIGINS does NOT include localhost
- [ ] Debug mode OFF
- [ ] No hardcoded credentials in code

### Frontend
- [ ] Production build succeeds
- [ ] No console.log in production code
- [ ] Error boundaries on all pages
- [ ] Sentry configured for frontend errors

## Post-Deployment (after clicking Deploy)

### Smoke Test (do these within 5 minutes)
- [ ] Homepage loads (check all 15 tour steps)
- [ ] Registration: create a new org
- [ ] Login: login as the new org owner
- [ ] Create a ticket
- [ ] EFI guidance returns (not "Could not load")
- [ ] Create an estimate
- [ ] Convert estimate to invoice
- [ ] Download invoice PDF
- [ ] Send invoice email (check real delivery)
- [ ] Platform admin login works

### Monitoring
- [ ] Sentry receiving errors (test with intentional 404)
- [ ] MongoDB Atlas metrics accessible
- [ ] Resend email delivery dashboard accessible

## Rollback Plan
If critical issues found after deployment:
1. Switch DB_NAME back to battwheels_dev
2. Or point to battwheels_staging (validated)
3. Investigate on dev, fix, re-deploy
