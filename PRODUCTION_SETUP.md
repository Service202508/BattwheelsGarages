# Battwheels OS — Production Launch Setup Guide

Last updated: Feb 2026

---

## Current Configuration Status

| Service | Backend .env | Frontend .env | Status |
|---------|-------------|---------------|--------|
| MongoDB | ✅ MONGO_URL | — | Ready |
| JWT Auth | ✅ JWT_SECRET | — | Ready |
| AI/LLM | ✅ EMERGENT_LLM_KEY | — | Ready |
| Zoho Sync | ✅ All ZOHO_* keys | — | Ready |
| **Sentry** | ❌ SENTRY_DSN missing | ❌ REACT_APP_SENTRY_DSN empty | Needs keys |
| **Resend Email** | ❌ RESEND_API_KEY missing | — | Needs key |
| **Razorpay** | ❌ Keys missing | — | Needs keys |
| **E-Invoice** | Stored per-org in DB | — | Configure in UI |

---

## 1. Sentry Error Monitoring

**Priority: HIGH** — Without Sentry, production errors are invisible.

### Setup Steps

1. Go to [sentry.io](https://sentry.io) → **New Project**
2. Select **FastAPI** → name it `battwheels-backend` → copy the DSN
3. Create a second project → **React** → name it `battwheels-frontend` → copy the DSN
4. Add to `/app/backend/.env`:

```
SENTRY_DSN=https://xxxxxxxx@oNNNNNN.ingest.sentry.io/NNNNNNN
ENVIRONMENT=production
APP_VERSION=1.0.0
```

5. Add to `/app/frontend/.env`:

```
REACT_APP_SENTRY_DSN=https://xxxxxxxx@oNNNNNN.ingest.sentry.io/NNNNNNN
```

### What's already wired up

- **Backend** (`server.py`): Sentry initializes on startup if `SENTRY_DSN` is set. FastAPI integration, PII scrubbing, 10% trace sampling.
- **Frontend** (`index.js`): Sentry initializes if `REACT_APP_SENTRY_DSN` is set. Browser tracing, session replay (masked), error boundary on root.

### Verification

After adding keys and restarting, go to **Sentry dashboard** and look for a test event. You can trigger one with:
```bash
curl https://your-domain.com/api/sentry-test  # Will 404, but the request itself is traced
```

---

## 2. Resend Transactional Email

**Priority: CRITICAL** — Invoices, tickets, SLA alerts, and team invites cannot be sent without this.

### What breaks without it

- Invoice email delivery silently fails
- Ticket confirmation emails not sent
- SLA breach alerts not sent
- Team invitation emails not delivered
- All emails are logged to console only

### Setup Steps

1. Go to [resend.com](https://resend.com) → **API Keys** → **Create API Key**
2. Verify your sending domain (e.g., `battwheels.in`) under **Domains**
3. Add to `/app/backend/.env`:

```
RESEND_API_KEY=re_REDACTED
SENDER_EMAIL=noreply@battwheels.in
APP_URL=https://your-production-domain.com
```

> **Important:** `SENDER_EMAIL` must be a verified Resend domain. Without domain verification, emails go to spam or bounce.

### Email templates that use your org logo

After uploading your organization logo in **Settings → General → Organization Logo**, the following emails will include it:
- Invoice emails
- Ticket confirmation
- SLA breach notifications
- Team invitations (base template)

---

## 3. Razorpay — Live Payment Keys

**Priority: CRITICAL** — Without live keys, all payments are TEST transactions (not real money).

### Setup Steps

1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com)
2. **Switch to LIVE mode** (toggle at top-left — default is Test)
3. Go to **Settings → API Keys → Generate Key**
4. Copy `Key ID` and `Key Secret`
5. Go to **Settings → Webhooks → Add New Webhook**:
   - URL: `https://your-production-domain.com/api/payments/razorpay/webhook`
   - Events to enable: `payment.captured`, `payment.failed`, `refund.created`, `refund.failed`
   - Copy the **Webhook Secret**
6. Add to `/app/backend/.env`:

```
RAZORPAY_KEY_ID=rzp_live_REDACTED
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Per-organization override

If you're running multiple garages on the same instance, each organization can have its own Razorpay keys configured via:
**Settings → Integrations → Razorpay Configuration**

The org-level keys always take precedence over the `.env` fallback keys.

### Verification

```bash
curl -X POST https://your-domain.com/api/payments/config \
  -H "Authorization: Bearer <admin-token>" | python3 -m json.tool
# Should show: "configured": true, "test_mode": false
```

---

## 4. E-Invoice (IRP) — Production Switch

**Priority: MEDIUM** — Required before onboarding B2B customers with turnover > ₹5 crore.

### Important: Org-level Configuration (not .env)

IRP credentials are stored **per-organization in the database**, configured via the Settings UI. Do NOT put them in `.env`.

### Setup Steps

1. Register on [einvoice1.gst.gov.in](https://einvoice1.gst.gov.in) with your GSTIN
2. Get API credentials:
   - Client ID
   - Client Secret
   - Username / Password (separate from GST portal login)
3. Go to **Settings → Finance → E-Invoice** in Battwheels OS
4. Fill in all credentials → **Save**
5. Run **Test Connection** to verify sandbox access
6. When ready for production: toggle **Sandbox → Production**

### Environment difference

| Setting | Sandbox | Production |
|---------|---------|-----------|
| IRP Endpoint | `einvoice-api.trial.nic.in` | `einvoice1.gst.gov.in` |
| IRN generation | Test IRNs (not valid) | Real GST-registered IRNs |
| Usage | Integration testing | Live customer invoices |

> Switch from Sandbox to Production **only after** you've verified end-to-end IRN generation with test invoices.

---

## Restart Sequence After Adding .env Keys

After adding any new environment variables to `.env`:

```bash
sudo supervisorctl restart backend
# Wait 5 seconds
sudo supervisorctl status backend
# Should show: RUNNING
```

The frontend reads `.env` at **build time** — restart is sufficient for the backend. For frontend changes (`REACT_APP_*`), the values are embedded at build time and available after a page reload.

---

## Full Production Launch Checklist

```
□ Set SENTRY_DSN in backend .env
□ Set REACT_APP_SENTRY_DSN in frontend .env
□ Verify Sentry receives test events (both projects)

□ Set RESEND_API_KEY in backend .env
□ Set SENDER_EMAIL to verified domain address
□ Set APP_URL to production domain
□ Send a test invoice email and verify delivery

□ Set RAZORPAY_KEY_ID (live key, not test)
□ Set RAZORPAY_KEY_SECRET (live key)
□ Set RAZORPAY_WEBHOOK_SECRET
□ Update webhook URL in Razorpay dashboard to production domain
□ Process a ₹1 test payment end-to-end

□ Configure IRP credentials in org settings (sandbox first)
□ Test IRN generation on sandbox with a test invoice
□ Switch to production IRP endpoint
□ Generate first live IRN on a real invoice

□ Restart backend after .env changes
□ Run load test against production: locust -f /app/load_tests/locustfile.py
□ Verify Sentry shows load test traces
□ Set JWT_SECRET to a strong production key (openssl rand -hex 32)
□ Set CORS_ORIGINS to exact production frontend URL (not *)
```

---

## Security Hardening (Before GA)

```bash
# Generate a strong JWT secret
openssl rand -hex 32

# Replace weak default in backend .env:
# JWT_SECRET=REDACTED_JWT_SECRET
# → JWT_SECRET=<output from above>

# Lock CORS to your production domain:
# CORS_ORIGINS=*
# → CORS_ORIGINS=https://your-production-domain.com
```

> **Critical:** The current JWT secret (`REDACTED_JWT_SECRET`) and CORS (`*`) are development values. These MUST be changed before going live.

---

## Contact / Support

- Sentry docs: https://docs.sentry.io/platforms/python/integrations/fastapi/
- Resend docs: https://resend.com/docs/introduction
- Razorpay docs: https://razorpay.com/docs/payments/server-integration/
- IRP docs: https://einvoice1.gst.gov.in/Documents/APIReferenceDocs.pdf
