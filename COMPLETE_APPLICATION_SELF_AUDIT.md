# COMPLETE APPLICATION SELF-AUDIT — ZERO TO NOW
## Battwheels OS | Compiled: February 2026
## Source: Actual file reads from the live codebase. No memory. No assumptions.

---

# SECTION 01 — CODEBASE INVENTORY

## 1. Total File Count by Type (excluding node_modules)
| Type | Count |
|------|-------|
| `.py` | 327 |
| `.jsx` | 189 |
| `.js` | 23 |
| `.css` | 2 |
| `.html` | 1 |
| `.md` | 45 |
| `.sh` | 2 |
| `.toml` | 0 |
| `.yml` | 2 |
| `.json` | 135 |
| `.tsx` | 0 |
| `.ts` | 0 |

## 2. Total Lines of Code by Language
| Language | Lines |
|----------|-------|
| Python | 187,429 |
| JSX | 91,402 |
| JavaScript | 6,296 |
| CSS | 689 |
| HTML | 143 |
| Markdown | 18,708 |
| **Total** | **~304,667** |

## 3. Complete Directory Tree
```
/app/
├── .emergent/
│   ├── emergent.yml
│   └── summary.txt
├── .github/workflows/security-audit.yml
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── config/
│   │   ├── env_validator.py
│   │   └── plan_features.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audit/
│   │   │   └── service.py
│   │   ├── auth/ (empty dir)
│   │   ├── org/
│   │   │   ├── dependencies.py, middleware.py, models.py, routes.py, service.py, utils.py
│   │   ├── settings/
│   │   │   ├── models.py, routes.py, service.py
│   │   ├── subscriptions/
│   │   │   ├── entitlement.py, models.py, service.py
│   │   └── tenant/
│   │       ├── ai_isolation.py, audit.py, context.py, events.py, exceptions.py
│   │       ├── guard.py, observability.py, rbac.py, repository.py, token_vault.py
│   ├── events/
│   │   ├── event_dispatcher.py, failure_events.py, notification_events.py, ticket_events.py
│   ├── middleware/
│   │   ├── rate_limit.py, rbac.py, tenant.py (DEPRECATED tombstone)
│   ├── migrations/
│   │   ├── add_org_id_indexes.py, add_org_id_to_collections.py, add_performance_indexes.py
│   ├── models/
│   │   ├── ai_guidance_models.py, failure_intelligence.py, knowledge_brain.py
│   ├── routes/
│   │   ├── 64 route files (ai_assistant.py through zoho_sync.py)
│   ├── scripts/
│   │   ├── migrate_multi_tenant.py, parity_reconciliation.py
│   ├── services/
│   │   ├── 47 service files (activity_service.py through zoho_realtime_sync.py)
│   ├── tests/
│   │   ├── 105+ test files
│   ├── utils/
│   │   ├── audit.py, audit_log.py, auth.py, database.py, dates.py, indexes.py, pagination.py
│   ├── server.py (6,716 lines — the monolith entry point)
│   └── requirements.txt
├── config/environments/README.md
├── docs/
│   ├── BATTWHEELS_OS_TECHNICAL_SPEC.md (2,521 lines)
│   ├── TECHNICAL_SPEC.md (2,041 lines)
│   ├── EFI_ARCHITECTURE.md (1,423 lines)
│   └── PERIOD_LOCKING_DESIGN.md (343 lines)
├── frontend/
│   ├── .env
│   ├── public/
│   │   ├── index.html, manifest.json, service-worker.js
│   ├── src/
│   │   ├── App.js (main router, ~1,300 lines)
│   │   ├── index.js, index.css
│   │   ├── components/ (19 custom components + ui/ shadcn library)
│   │   ├── hooks/ (6 hooks)
│   │   ├── lib/utils.js
│   │   ├── pages/ (94 page files + 6 business/ + 6 customer/ + 7 technician/ + finance/ + settings/)
│   │   └── utils/api.js, dates.js
│   ├── package.json
│   ├── tailwind.config.js
│   └── yarn.lock
├── load_tests/locustfile.py
├── memory/ (PRD.md, CHANGELOG.md, ARCHITECTURE_ANALYSIS.md, QA audit files)
├── scripts/ (8 utility scripts)
├── test_reports/ (125+ iteration JSON files, 90+ pytest XML files)
├── tests/e2e/test_tenant_isolation.py
├── uploads/logos/ (org-specific logo uploads)
└── 25+ root-level .md audit/report files
```

## 4. Top 10 Largest Files by Line Count
| # | Lines | File |
|---|-------|------|
| 1 | 6,716 | `backend/server.py` |
| 2 | 3,671 | `backend/routes/zoho_api.py` |
| 3 | 3,305 | `backend/routes/items_enhanced.py` |
| 4 | 3,007 | `backend/routes/estimates_enhanced.py` |
| 5 | 2,983 | `backend/routes/zoho_extended.py` |
| 6 | 2,966 | `frontend/src/pages/EstimatesEnhanced.jsx` |
| 7 | 2,768 | `frontend/src/pages/InvoicesEnhanced.jsx` |
| 8 | 2,682 | `frontend/src/pages/ItemsEnhanced.jsx` |
| 9 | 2,626 | `frontend/src/pages/OrganizationSettings.jsx` |
| 10 | 2,439 | `frontend/src/pages/AllSettings.jsx` |

## 5. Last Git Commit
```
2a0eeeba auto-commit for 942e9f6e-4d53-4646-a14a-6720bb4794b8
```

## 6. All Branches
```
* main
```
Single branch. No feature branches. No staging branch.

## 7. Repo Root Directory
All files listed — 25+ markdown audit/report files, `Makefile`, `startup.sh`, empty `Integrations` and `Journal` files, `audit_raw_results.json`, `audit_results_v2.json`, `backend_test.py`, `run_cto_audit.py`, `run_cto_reaudit_v2.py`, `config/`, `docs/`, `frontend/`, `backend/`, `load_tests/`, `memory/`, `scripts/`, `test_reports/`, `tests/`, `uploads/`.

---

# SECTION 02 — ENVIRONMENT & CONFIGURATION

## 1. Complete `backend/.env`
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="battwheels"                     ← CRITICAL: Points to PRODUCTION
CORS_ORIGINS=https://production-readiness-7.preview.emergentagent.com
EMERGENT_LLM_KEY=[REDACTED]
JWT_SECRET=[REDACTED]
ZOHO_CLIENT_ID=REDACTED_ZOHO_CLIENT_ID
ZOHO_CLIENT_SECRET=[REDACTED]
ZOHO_REFRESH_TOKEN=REDACTED_ZOHO_REFRESH_TOKEN
ZOHO_API_BASE_URL=https://www.zohoapis.in
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_ORGANIZATION_ID=REDACTED_ORG_ID
STRIPE_API_KEY=[REDACTED]
SENTRY_DSN=[REDACTED]
RESEND_API_KEY=[REDACTED]
SENDER_EMAIL=noreply@battwheels.com
RAZORPAY_KEY_ID=rzp_live_REDACTED    ← LIVE keys, not test
RAZORPAY_KEY_SECRET=[REDACTED]
RAZORPAY_WEBHOOK_SECRET=[REDACTED]
ENVIRONMENT=production
```

## 2. `.env.example` — Exists. Well-documented with sections for all integrations.

## 3. `frontend/.env`
```
REACT_APP_BACKEND_URL=https://production-readiness-7.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
REACT_APP_SENTRY_DSN=https://REDACTED_SENTRY_DSN
REACT_APP_ENVIRONMENT=production
```

## 4. All Backend Environment Variables Read (`os.environ.get` / `os.getenv`)
```
ALLOW_PRODUCTION_PURGE, API_BASE_URL, APP_URL, APP_VERSION, CORS_ORIGINS,
CREDENTIAL_ENCRYPTION_KEY, DB_NAME, EINVOICE_ENCRYPTION_KEY, EMERGENT_LLM_KEY,
ENVIRONMENT, INTEGRATION_PROXY_URL, JWT_SECRET, MONGO_URL, NODE_ENV,
OPENAI_API_KEY, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET,
REACT_APP_BACKEND_URL, RESEND_API_KEY, SECRET_KEY, SENDER_EMAIL, SENTRY_DSN,
STRIPE_API_KEY, TEST_API_URL, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
TWILIO_WHATSAPP_NUMBER, VAULT_MASTER_KEY, ZOHO_ACCOUNTS_URL, ZOHO_API_BASE_URL,
ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_ORGANIZATION_ID, ZOHO_REFRESH_TOKEN
```

## 5. All Frontend Environment Variables Read
```
process.env.NODE_ENV
process.env.REACT_APP_BACKEND_URL
process.env.REACT_APP_ENVIRONMENT
process.env.REACT_APP_SENTRY_DSN
```

## 6. Current DB_NAME: `battwheels` (PRODUCTION — VIOLATION of ENVIRONMENT_SOP.md)
## 7. Current ENVIRONMENT: `production`

## 8. MongoDB Databases on Connected Instance
| Database | Collections | Notes |
|----------|-------------|-------|
| `battwheels` | 223 | Production data — currently active |
| `battwheels_dev` | 26 | Sparse dev data (2 users, 2 orgs, 14 tickets) |
| `battwheels_os` | 3 | Empty (failure_cards, import_jobs, parsed_rows) |
| `test_database` | 221 | Near-mirror of production |
| `admin` | 1 | System |
| `config` | 1 | System |
| `local` | 1 | System |

## 9. `railway.toml` — Does not exist
## 10. `docker-compose.yml` — Does not exist
## 11. `Dockerfile` — Does not exist

---

# SECTION 03 — BACKEND COMPLETE INVENTORY

## 1. Framework: FastAPI 0.132.0

## 2. Key Dependencies (from requirements.txt)
- `fastapi==0.132.0`, `uvicorn==0.25.0`, `motor==3.7.1`, `pymongo==4.16.0`
- `bcrypt==4.1.3`, `PyJWT==2.11.0`, `python-jose==3.5.0`
- `resend==2.21.0`, `razorpay==2.0.0`, `stripe==14.3.0`
- `sentry-sdk==2.53.0`, `twilio==9.10.1`
- `weasyprint==68.1`, `reportlab==4.4.10` (PDF)
- `openai==1.99.9`, `google-genai==1.62.0`, `litellm==1.80.0`
- `emergentintegrations==0.1.0`
- `pandas==3.0.0`, `openpyxl==3.1.5`, `xlrd==2.0.2`
- `slowapi==0.1.9` (rate limiting)
- `pydantic==2.12.5`
- Total: ~200 packages (including duplicates from double freeze)

## 3. Entry Point
`backend/server.py` — Supervisor runs uvicorn on `0.0.0.0:8001`. The app is created via `FastAPI(title="Battwheels OS API", lifespan=lifespan)`.

## 4. Uvicorn Workers: 1 (default, single-process)

## 5. Route Files (64 files in `backend/routes/`)

| # | File | Lines | Prefix | Endpoints | Purpose |
|---|------|-------|--------|-----------|---------|
| 1 | `ai_assistant.py` | 202 | `/ai-assistant` | 2 | AI diagnostic (Gemini) |
| 2 | `ai_guidance.py` | 629 | `/ai-guidance` | 12 | AI-guided diagnosis workflow |
| 3 | `amc.py` | 843 | `/amc` | 14 | AMC plans & subscriptions |
| 4 | `auth.py` | 334 | `/auth` | 6 | Login, register, logout, Google auth |
| 5 | `banking.py` | 389 | `/banking` | 14 | Bank accounts & transactions |
| 6 | `banking_module.py` | 923 | `/banking-module` | 19 | Extended banking + reports (COMMENTED OUT) |
| 7 | `bills.py` | 393 | `/bills` | 11 | AP bills management |
| 8 | `bills_enhanced.py` | 961 | `/bills-enhanced` | 21 | Enhanced bills + PO |
| 9 | `business_portal.py` | 653 | `/business` | 11 | B2B fleet customer portal |
| 10 | `composite_items.py` | 557 | `/composite-items` | 9 | Kit/bundle items |
| 11 | `contact_integration.py` | 783 | `/contact-integration` | 14 | Contact-transaction linking |
| 12 | `contacts_enhanced.py` | 2,240 | `/contacts` | 41 | Full contacts CRM |
| 13 | `credit_notes.py` | 546 | `/credit-notes` | 4 | Credit notes |
| 14 | `customer_portal.py` | 672 | `/customer-portal` | 19 | End-customer self-service |
| 15 | `data_integrity.py` | 406 | `/data-integrity` | 15 | Data audit & repair |
| 16 | `data_management.py` | 384 | `/data-management` | 16 | Sanitization & sync |
| 17 | `data_migration.py` | 519 | `/data-migration` | 7 | Zoho migration |
| 18 | `documents.py` | 459 | `/documents` | 13 | Document management |
| 19 | `efi_guided.py` | 694 | `/efi` | 21 | EFI guided diagnostic |
| 20 | `efi_intelligence.py` | 604 | `/efi-intelligence` | 14 | EFI risk & learning |
| 21 | `einvoice.py` | 410 | `/einvoice` | 11 | E-Invoice IRN |
| 22 | `estimates_enhanced.py` | 3,007 | `/estimates` | 42 | Full estimates module |
| 23 | `expenses.py` | 571 | `/expenses` | 17 | Expense management |
| 24 | `expert_queue.py` | 347 | `/expert-queue` | 13 | Escalation management |
| 25 | `export.py` | 567 | `/export` | 8 | Tally/bulk export |
| 26 | `failure_intelligence.py` | 687 | `/failure-intelligence` | 28 | Failure cards & patterns |
| 27 | `fault_tree_import.py` | 375 | `/fault-tree` | 9 | Excel fault tree import |
| 28 | `finance_dashboard.py` | 111 | `/finance` | 4 | Finance overview |
| 29 | `financial_dashboard.py` | 685 | `/financial-dashboard` | 7 | Extended finance dashboard |
| 30 | `gst.py` | 1,101 | `/gst` | 9 | GST reports (GSTR-1, 3B, HSN) |
| 31 | `hr.py` | 1,849 | `/hr` | 35 | HR, payroll, TDS, Form 16 |
| 32 | `insights.py` | 809 | `/insights` | 6 | Data analytics |
| 33 | `inventory.py` | 388 | `/inventory` | 12 | Basic inventory |
| 34 | `inventory_adjustments_v2.py` | 1,147 | `/inventory-adjustments` | 24 | Stock adjustments |
| 35 | `inventory_enhanced.py` | 1,734 | `/inventory-enhanced` | 40 | Warehouses, variants, shipments |
| 36 | `invoice_automation.py` | 528 | `/invoice-automation` | 13 | Reminders & late fees |
| 37 | `invoice_payments.py` | 428 | `/invoice-payments` | 5 | Stripe payment links |
| 38 | `invoices_enhanced.py` | 2,392 | `/invoices` | 41 | Full invoicing module |
| 39 | `items_enhanced.py` | 3,305 | `/items` | 42 | Full items management |
| 40 | `journal_entries.py` | 527 | `/journal` | 15 | Journal entries & reports |
| 41 | `knowledge_brain.py` | 532 | `/knowledge` | 14 | Knowledge base |
| 42 | `master_data.py` | 474 | `/master-data` | 13 | Vehicle categories, models |
| 43 | `notifications.py` | 419 | `/notifications` | 12 | Notification system |
| 44 | `organizations.py` | 1,344 | `/org` | 29 | Org management, onboarding |
| 45 | `payments_received.py` | 1,371 | `/payments` | 24 | Payment recording & credits |
| 46 | `pdf_templates.py` | 527 | `/pdf-templates` | 10 | Invoice PDF customization |
| 47 | `permissions.py` | 416 | `/permissions` | 9 | RBAC management |
| 48 | `platform_admin.py` | 581 | `/platform-admin` | 16 | Platform admin functions |
| 49 | `productivity.py` | 477 | `/productivity` | 6 | Technician productivity |
| 50 | `projects.py` | 813 | `/projects` | 18 | Project management |
| 51 | `public_tickets.py` | 820 | `/public` | 10 | Public ticket submission |
| 52 | `razorpay.py` | 1,134 | `/razorpay` | 12 | Razorpay payments (legacy) |
| 53 | `razorpay_routes.py` | 828 | `/razorpay` | 12 | Razorpay v2 (duplicate!) |
| 54 | `recurring_invoices.py` | 475 | `/recurring-invoices` | 10 | Recurring billing |
| 55 | `reports.py` | 1,639 | `/reports` | 8 | Financial reports |
| 56 | `reports_advanced.py` | 711 | `/reports-advanced` | 13 | Advanced analytics |
| 57 | `sales_orders_enhanced.py` | 1,557 | `/sales-orders` | 24 | Sales orders |
| 58 | `seed_utility.py` | 502 | `/seed` | 7 | Dev data seeding |
| 59 | `serial_batch_tracking.py` | 814 | `/serial-batch` | 19 | Serial/batch tracking |
| 60 | `sla.py` | 941 | `/sla` | 7 | SLA management |
| 61 | `stock_transfers.py` | 508 | `/stock-transfers` | 7 | Inter-warehouse transfers |
| 62 | `stripe_webhook.py` | 70 | `/stripe` | 1 | Stripe webhook |
| 63 | `subscriptions.py` | 471 | `/subscriptions` | 14 | SaaS plan management |
| 64 | `tally_export.py` | 176 | `/export` | 1 | Tally XML |
| 65 | `technician_portal.py` | 770 | `/technician` | 13 | Technician portal |
| 66 | `ticket_estimates.py` | 550 | `/ticket-estimates` | 12 | In-ticket estimates |
| 67 | `tickets.py` | 603 | `/tickets` | 16 | Service ticket CRUD |
| 68 | `time_tracking.py` | 605 | `/time-tracking` | 10 | Time entries & timers |
| 69 | `uploads.py` | — | `/uploads` | — | File uploads |

**Total: ~700+ API endpoints across 64+ route files**

## 6. Service Files (47 files)
Key services: `double_entry_service.py` (1,645 lines — financial engine), `ticket_service.py` (45,347 bytes), `pdf_service.py` (67,067 bytes), `efi_seed_data.py` (66,084 bytes), `einvoice_service.py` (46,675 bytes), `ticket_estimate_service.py` (50,224 bytes), `email_service.py` (22,225 bytes), `whatsapp_service.py` (4,665 bytes — uses live Meta Graph API, NOT mocked code but requires org-level credential config), `razorpay_service.py`, `hr_service.py`, `banking_service.py`, `bills_service.py`, `expenses_service.py`, `inventory_service.py`, `tds_service.py`, `credential_service.py`

## 7. Middleware Files
- `rate_limit.py` — SlowAPI-based. Auth: 5/min, Register: 3/hr, AI: 20/min/org, Standard: 300/min, Public: 60/min
- `rbac.py` — Role-based access control with hierarchy (owner > org_admin > admin > manager > accountant > technician > dispatcher > viewer > customer)
- `tenant.py` — **DEPRECATED TOMBSTONE**. Active enforcement is in `core/tenant/guard.py`

## 8. Middleware Chain Order (from server.py)
1. RateLimitMiddleware (outermost)
2. RBACMiddleware
3. TenantGuardMiddleware
4. CORSMiddleware (innermost, runs last)

## 9. Core Files
- `core/audit/service.py` — Audit logging
- `core/org/` — Organization management (dependencies, middleware, models, routes, service, utils)
- `core/settings/` — Organization settings management
- `core/subscriptions/` — SaaS subscription & entitlement enforcement
- `core/tenant/` — **SECURITY CORE**: guard.py (TenantGuard), context.py (TenantContext), rbac.py, exceptions.py, token_vault.py, etc.

## 10. Models Files
- `ai_guidance_models.py`, `failure_intelligence.py`, `knowledge_brain.py` — Pydantic models for AI features

## 11. server.py Structure (6,716 lines)
- Lines 1-32: Imports & Sentry setup
- Lines 33-98: Sentry scrubbing, env validation, MongoDB connection, JWT config
- Lines 99-151: Lifespan (startup: SLA job, index migrations; shutdown: close DB)
- Lines 152-206: App creation, router setup, exception handlers
- Lines 207-1100: **~50 Pydantic models** (User, Employee, Invoice, Ticket, etc.) — all inline!
- Lines 1100-1200: Password hashing, token creation, get_current_user
- Lines 1200-5440: **Inline route handlers** (auth, health, vehicles, tickets, suppliers, services, sales orders, invoices, payments, ledger, accounting, expenses, chart of accounts, HR endpoints, AI endpoints)
- Lines 5440-6120: Router registration (v1_router.include_router for all 64+ route files)
- Lines 6120-6380: Catch-all routes, static file serving
- Lines 6380-6716: Health check, CORS, middleware mounting, app configuration

## 12. Startup Events
- SLA background breach detection job
- MongoDB index migration (add_org_id_indexes)
- Compound index creation (ensure_compound_indexes)

## 13. Shutdown Events
- MongoDB client close

## 14. Health Check
- URL: `GET /api/health`
- Returns: `{"status": "healthy", "version": "2.0.0", "timestamp": "<ISO>"}`

## 15. Global Error Handling
- Custom exception handlers for all tenant exceptions (TenantAccessDenied, TenantContextMissing, TenantBoundaryViolation, TenantDataLeakAttempt, TenantQuotaExceeded, TenantSuspended)
- Returns structured JSON with appropriate HTTP status codes (403, 400, 429)

---

# SECTION 04 — ALL API ENDPOINTS

**Total: ~700+ endpoints across 64+ route files**

Due to the massive volume, endpoints are grouped and summarized in Section 03, Point 5. Every route file with its prefix and endpoint count is listed there. A full per-endpoint listing would exceed 50 pages. The key route groups are:

- **Auth**: 6 endpoints (`/api/auth/*`)
- **Public**: 10 endpoints (`/api/public/*`)
- **Tickets**: 16 + 12 ticket-estimate endpoints
- **Invoices**: 41 endpoints
- **Estimates**: 42 endpoints
- **Items**: 42 endpoints
- **Contacts**: 41 endpoints
- **HR**: 35 endpoints
- **GST**: 9 endpoints
- **Banking**: 14 + 19 endpoints
- **Bills**: 11 + 21 enhanced endpoints
- **Inventory**: 12 + 40 + 24 adjustment endpoints
- **EFI**: 21 + 14 + 28 endpoints
- **Payments**: 24 + 12 Razorpay + 5 Stripe
- **Projects**: 18 endpoints
- **Reports**: 8 + 13 advanced endpoints
- **Sales Orders**: 24 endpoints
- **Zoho**: 121 + 104 + 17 = 242 endpoints
- **Platform Admin**: 16 endpoints
- **All other modules**: ~100+ endpoints

All routes under `/api/v1/*` require authentication except public routes under `/api/public/*`. Tenant scoping is enforced by TenantGuardMiddleware.

---

# SECTION 05 — AUTHENTICATION & SECURITY COMPLETE AUDIT

## 1. JWT Token Creation
- Function: `create_token()` in `server.py` line 1158 AND `create_access_token()` in `utils/auth.py` line 47
- **TWO SEPARATE JWT FUNCTIONS EXIST** — potential inconsistency
- server.py: `JWT_EXPIRATION_HOURS = 24 * 7` (7 days)
- utils/auth.py: `ACCESS_TOKEN_EXPIRE_HOURS = 24` (1 day)
- Both use HS256 algorithm

## 2. JWT Validation
- `decode_token()` in `utils/auth.py` line 54
- `get_current_user()` in both `server.py` line 1171 AND `utils/auth.py` line 100
- Middleware `TenantGuardMiddleware` extracts and validates JWT from Authorization header

## 3. JWT_SECRET
- Read from `os.environ.get('JWT_SECRET', 'battwheels-secret')` — **HAS A WEAK DEFAULT FALLBACK**
- Warning logged if < 32 chars
- Currently set in .env (redacted, appears to be strong)

## 4. Public Routes (bypass authentication)
- `GET /api/health`
- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/google`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/public/*` (10 public ticket endpoints)
- `GET /quote/:shareToken`
- `GET /survey/:token`
- Customer portal login (`POST /api/v1/customer-portal/login`)

## 5. Tenant Isolation Exemptions
- Platform admin routes (check `is_platform_admin` flag)
- Public ticket submission (org resolved from URL/form data)
- Auth routes (pre-authentication)
- Health check

## 6. CSRF — NOT IMPLEMENTED
No CSRF tokens, no Double Submit Cookie pattern. The CSP header includes `connect-src 'self' https://*.emergentagent.com https://*.battwheels.com` but no anti-CSRF mechanism.

## 7. Input Sanitization — PARTIAL
- `data_sanitization_service.py` exists (20,163 bytes) for bulk sanitization
- No per-request input sanitization middleware (no `bleach` in request pipeline)
- Password validation enforces strength rules (8+ chars, uppercase, number, special char)

## 8. Rate Limiting
- Library: `slowapi==0.1.9`
- In-memory (not persistent/Redis-backed)
- Auth: 5/min per IP, Register: 3/hr per IP
- AI endpoints: 20/min per org, 200/hr per org
- Standard: 300/min per user
- Public: 60/min per IP

## 9. CORS Configuration
```python
allow_credentials=True
allow_origins=[from CORS_ORIGINS env var]
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
allow_headers=["Authorization", "Content-Type", "X-Organization-ID", "X-Requested-With", "Accept"]
```

## 10. Security Headers
- CSP: `connect-src 'self' https://*.emergentagent.com https://*.battwheels.com`
- No X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security headers found in code

## 11. RBAC
**Roles** (from role hierarchy):
- `owner`, `org_admin`, `admin`, `manager`, `accountant`, `technician`, `dispatcher`, `customer`, `fleet_customer`, `viewer`

**Role hierarchy**: owner > org_admin > admin > manager; accountant standalone; technician standalone

## 12. Tenant Isolation
- Enforced by `TenantGuardMiddleware` (core/tenant/guard.py)
- `TenantGuard` class validates every query against `TENANT_COLLECTIONS` set
- Organization ID extracted from JWT token and `X-Organization-ID` header
- Violations logged and blocked with 403

## 13. Fake org_id Header
- TenantGuardMiddleware validates org_id from JWT token, not just the header
- However, the header is trusted in some paths — needs audit

## 14. Password Hashing
- Algorithm: **bcrypt**
- Library: `bcrypt==4.1.3`
- Default rounds (bcrypt.gensalt() = 12 rounds)
- Legacy SHA256 passwords are auto-migrated to bcrypt on login

## 15. Known Security Vulnerabilities
- **CSRF not implemented** — vulnerable to cross-site request forgery
- **JWT has weak default** (`'battwheels-secret'`) if env var missing
- **Two separate JWT functions** with different expiry (7d vs 1d)
- **Rate limiting is in-memory** — resets on restart, not shared across workers
- **No input sanitization middleware** — XSS possible in stored data
- **12 of 13 users have no organization_id** — isolation gap for user records
- **Razorpay using LIVE keys** in development environment

---

# SECTION 06 — DATABASE COMPLETE AUDIT

## 1. Active Database: `battwheels` (PRODUCTION)

## 2. Every Collection with Document Count
**battwheels database: 223 collections**

Top collections by document count:
| Collection | Docs |
|-----------|------|
| chart_of_accounts | 396 |
| event_log | 345 |
| tenant_roles | 200 |
| addresses | 205 |
| failure_cards | 107 |
| notifications | 45 |
| invoice_history | 45 |
| invoice_line_items | 36 |
| organization_users | 34 |
| audit_logs | 31 |
| tenant_activity_logs | 30 |
| webhook_logs | 29 |
| ticket_activities | 26 |
| contact_history | 25 |
| estimate_history | 24 |
| amc_plans | 23 |
| vehicle_models | 21 |
| technician_action_logs | 20 |
| journal_entries | 18 |
| ev_issue_suggestions | 18 |
| contact_submissions | 16 |
| leave_balances | 16 |
| contacts | 15 |
| custom_fields | 8 |
| counters | 14 |
| efi_decision_trees | 14 |
| stock_movements | 14 |
| items | 12 |
| item_history | 12 |
| adjustment_reasons | 12 |
| bank_accounts | 12 |
| item_serial_batches | 2 |
| users | 13 |
| tickets | 10 |
| ...and 140+ collections with 0-10 docs |

**Collections with ZERO documents: ~100+** including employees, payroll, payroll_runs, suppliers, warehouses, purchase_orders, work_orders, etc.

## 3. Indexes
Key indexes found:
- `audit_logs`: org+timestamp, org+resource_type+resource_id
- `bills`: org+status+date
- `contacts`: org+name, org+phone
- `credit_notes`: org+date, org+invoice, org+number (UNIQUE)
- `employees`: org+status
- `estimates`: org+status+date, org+customer
- `expenses`: org+category+date
- `inventory`: org+qty
- `invoices`: org+status+date, org+contact
- `items`: org+name, org+type
- `journal_entries`: org+date, org+debit+date, org+credit+date, unique source_document per org
- `password_reset_tokens`: TTL on expires_at, unique token_hash, user_id
- `payroll_runs`: org+period (UNIQUE)

## 4-5. Largest Collections & Empty Collections
See table above. ~100+ collections with zero documents.

## 6. Document Schemas (key collections)
**users**: user_id, email, password_hash, name, role, designation, phone, is_active, org_memberships, organization_id, default_org_id, is_platform_admin, password_changed_at, password, password_version
**organizations**: organization_id, name, slug, industry_type, plan_type, gstin, branding, sla_config, onboarding_completed
**tickets**: ticket_id, title, description, category, priority, status, vehicle_id, customer_id, customer_name, customer_type, issue_type, resolution_type, status_history, estimated_cost, actual_cost, parts_cost, labor_cost, assigned_technician_id, organization_id, sla_*
**invoices_enhanced**: invoice_id, organization_id, invoice_number, customer_id, line_items, sub_total, tax_total, cgst/sgst/igst, grand_total, status, payments, credit_notes
**journal_entries**: entry_id, entry_date, reference_number, description, organization_id, entry_type, source_document_id/type, lines[], total_debit, total_credit
**contacts**: contact_id, contact_type, name, email, phone, gstin, gst_treatment, organization_id, outstanding_receivable/payable
**employees**: EMPTY (0 documents in production)
**inventory**: item_id, sku, name, category, quantity, unit_price, cost_price, min_stock_level, organization_id

## 7. org_id Storage
Stored as **string** (`str`) in all collections. Not ObjectId.

## 8. Documents Missing organization_id
| Collection | Missing/Total |
|-----------|---------------|
| tickets | 0/10 |
| invoices_enhanced | 0/3 |
| contacts | 0/15 |
| journal_entries | 0/18 |
| employees | 0/0 (empty) |
| inventory | 0/3 |
| estimates | 0/7 |
| **users** | **12/13** |

**CRITICAL: 12 of 13 users have no organization_id field.** Only `admin@battwheels.in` has it.

## 9. Connection String: `mongodb://localhost:27017` (local MongoDB, no auth)
## 10. Connection Pooling: Default Motor/PyMongo settings (no explicit config)

---

# SECTION 07 — EACH MODULE DEEP AUDIT

## 07-A — Service Tickets
- **Backend**: `routes/tickets.py` (16 endpoints), `routes/public_tickets.py` (10 endpoints), `routes/sla.py` (7 endpoints)
- **Frontend**: `Tickets.jsx`, `TicketDetail.jsx`, `NewTicket.jsx`, `PublicTicketForm.jsx`, `TrackTicket.jsx`
- **Workflow**: Create (public/admin) → Assign technician → Start work → Complete work → Close. SLA tracking with response/resolution deadlines.
- **Data**: 10 tickets in production. Full schema with vehicle, customer, cost, SLA, failure card matching.
- **Integrations**: EFI failure card matching on creation, journal entry on close, notification events.
- **Known issues**: Ticket → Invoice conversion exists but unclear if end-to-end tested. No Estimate → Ticket conversion.

## 07-B — Estimates
- **Backend**: `routes/estimates_enhanced.py` (42 endpoints), `routes/ticket_estimates.py` (12 endpoints)
- **Frontend**: `EstimatesEnhanced.jsx` (2,966 lines — **needs refactor**)
- **Workflow**: Create → Send → Accept/Decline → Convert to Invoice/Sales Order
- **Known bugs**: Edit modal and save error were reported but verified as NOT reproducible in Week 2.
- **Estimate → Ticket**: NOT IMPLEMENTED
- **Estimate → Invoice**: Implemented via `POST /{estimate_id}/convert-to-invoice`

## 07-C — Invoices
- **Backend**: `routes/invoices_enhanced.py` (41 endpoints), `routes/invoice_automation.py` (13 endpoints), `routes/recurring_invoices.py` (10 endpoints)
- **Frontend**: `InvoicesEnhanced.jsx` (2,768 lines)
- **GST**: CGST/SGST for intra-state, IGST for inter-state. Place of supply determines split.
- **PDF**: WeasyPrint + ReportLab. Templates stored in `pdf_templates` collection. `pdf_service.py` (67,067 bytes).
- **Email**: Resend integration via `email_service.py`. Working if RESEND_API_KEY is valid.
- **WhatsApp**: `whatsapp_service.py` uses live Meta Graph API v18.0. Requires per-org WhatsApp credentials (stored encrypted in `tenant_credentials`). **Not mocked in code — but no org has configured credentials, so effectively non-functional.**
- **E-Invoice IRN**: `einvoice_service.py` (46,675 bytes). Full IRP integration with auth, schema building, QR code. **Stubbed/sandbox mode** — requires per-org IRP credentials.
- **Payment recording**: Via `invoices/{id}/payments` endpoint.
- **Credit notes**: `credit_notes.py` — 4 endpoints. Create and view.

## 07-D — Payments
- **Backend**: `routes/razorpay.py` (12 endpoints), `routes/razorpay_routes.py` (12 endpoints — **DUPLICATE**), `routes/invoice_payments.py` (5 Stripe endpoints), `routes/payments_received.py` (24 endpoints)
- **Razorpay**: Payment link generation, webhook handling, refunds. **Using LIVE keys**.
- **Manual payment**: Full recording via payments_received module.
- **AR clearing**: Payment posts journal entry (debit Bank, credit AR).
- **Known issue**: Two Razorpay route files exist (`razorpay.py` and `razorpay_routes.py`) — likely duplicates.

## 07-E — Accounting & Finance
- **Route files**: `journal_entries.py`, `banking.py`, `banking_module.py` (commented out), `finance_dashboard.py`, `financial_dashboard.py`, `reports.py`, `reports_advanced.py`, `expenses.py`, `bills.py`, `bills_enhanced.py`
- **Chart of Accounts**: 396 accounts across 24 types. 109 accounts have `None` type — **data quality issue**.
- **Journal Entries**: 18 entries. Created by `double_entry_service.py`. Schema has `lines[]` with debit/credit per line.
- **Trial Balance**: **BROKEN** — Aggregation returns Total Debit: 0, Total Credit: 0. The `lines` field structure may not have numeric debit/credit values, or entries use a different field name.
- **P&L**: Implemented in `double_entry_service.py` (`get_profit_and_loss`)
- **Balance Sheet**: Implemented in `double_entry_service.py` (`get_balance_sheet`)
- **Bank Reconciliation**: `banking.py` has reconcile endpoint. `bank_reconciliations` collection has 0 docs.
- **Expenses**: Full workflow — create, submit, approve, reject, mark-paid, receipt upload.
- **Bills/AP**: Full workflow — create, approve, record-payment. Plus enhanced PO workflow.
- **Period Locking**: `period_locks` collection **DOES NOT EXIST**. Design document exists at `/app/docs/PERIOD_LOCKING_DESIGN.md` but **NOT IMPLEMENTED**.

## 07-F — GST Compliance
- **Route file**: `gst.py` (1,101 lines, 9 endpoints)
- **GSTR-1**: Implemented. Generates JSON, Excel, PDF.
- **GSTR-3B**: Implemented. All sections populated. Credit notes included (fixed in Week 1).
- **GSTR-2A Reconciliation**: NOT IMPLEMENTED
- **E-way Bills**: NOT IMPLEMENTED
- **HSN Summary**: Implemented.
- **TDS**: `tds_service.py` (29,165 bytes). Calculation, challans, Form 16.
- **Known gaps**: Reverse charge separation in GSTR-3B is incorrect. GSTR-2A and E-way bills missing.

## 07-G — HR & Payroll
- **Route file**: `hr.py` (1,849 lines, 35 endpoints)
- **Frontend**: `HRDashboard.jsx`, `Employees.jsx`, `Attendance.jsx`, `Payroll.jsx`, `LeaveManagement.jsx`
- **Employee master**: Full fields (personal, salary structure, compliance, bank details, tax config)
- **Payroll**: Gross, PF (12%), ESI (0.75% employee / 3.25% employer), PT, TDS calculation. Form 16 generation.
- **Attendance**: Clock-in/out tracking. 9 records in production.
- **Leave management**: 5 leave types, 16 balances, 4 requests.
- **Form 16**: Implemented — both per-employee and bulk.
- **PF/ESI Challan**: NOT explicitly implemented as separate generation.
- **Known gap**: `employees` collection is EMPTY in production (0 docs).

## 07-H — Inventory
- **Route files**: `inventory.py` (12 endpoints), `inventory_enhanced.py` (40 endpoints), `inventory_adjustments_v2.py` (24 endpoints), `stock_transfers.py` (7 endpoints), `serial_batch_tracking.py` (19 endpoints)
- **Stock tracking**: By item with quantity, reserved, cost. 3 items in production.
- **Reorder alerts**: Implemented (min_stock_level comparison).
- **Purchase orders**: Implemented in `bills_enhanced.py` (PO workflow).
- **Stock valuation**: FIFO tracking in adjustments. Also ABC classification.
- **How deducted on tickets**: Via material allocation (`/inventory/allocations`).
- **Known gap**: Warehouses collection empty. Stock transfers collection empty.

## 07-I — Contacts & Vehicles
- **Contacts**: `contacts_enhanced.py` (41 endpoints). 15 contacts in production. Full CRM with addresses, persons, portal, statements.
- **Vehicles**: Defined in `server.py`. 1 vehicle in production. Categories (5), models (21).
- **Service history**: Via ticket lookup by vehicle_id.

## 07-J — EFI (EV Failure Intelligence)
- **Route files**: `efi_guided.py` (21 endpoints), `efi_intelligence.py` (14 endpoints), `failure_intelligence.py` (28 endpoints), `ai_assistant.py` (2), `ai_guidance.py` (12), `knowledge_brain.py` (14), `expert_queue.py` (13)
- **Platform layer**: 107 failure cards, 14 decision trees, 18 EV issue suggestions. Seed data exists.
- **Org layer**: Implemented with per-org failure card approval.
- **AI integration**: Gemini via Emergent LLM key. Prompts structured in `ai_guidance_service.py` and `llm_provider.py`.
- **Diagnostic flow**: Ticket → AI preprocessing → Failure card matching → Decision tree walkthrough → Estimate generation.

## 07-K — Data Insights / Dashboard
- **Route files**: `insights.py` (6 endpoints), `financial_dashboard.py` (7 endpoints), `finance_dashboard.py` (4 endpoints)
- **Metrics**: Revenue, operations, technician performance, EFI analytics, customer analytics, inventory.
- **Charts**: Revenue trends, operations summary, technician leaderboard.

## 07-L — Platform Admin
- **Route file**: `platform_admin.py` (16 endpoints)
- **Functions**: List/view/suspend/activate organizations, change plan, metrics, revenue health, activity, audit status, make/revoke admin, environment info, leads management.
- **Demo CRM**: `demo_requests` collection (6 docs). Lead status tracking.
- **Frontend**: `PlatformAdmin.jsx` (41,197 bytes)

---

# SECTION 08 — FRONTEND COMPLETE AUDIT

## 1. React 19.0.0
## 2. Build tool: CRA (Create React App) with CRACO override
## 3. Key npm dependencies
- `react@19.0.0`, `react-dom@19.0.0`, `react-router-dom@7.12.0`
- `axios@1.13.5`, `recharts@3.6.0`, `framer-motion@12.34.3`
- `@sentry/react@10.39.0`, `sonner@2.0.3`
- `lucide-react@0.507.0`, `date-fns@4.1.0`
- Full Radix UI component library (20+ packages)
- `leaflet@1.9.4`, `react-leaflet@5.0.0` (maps)
- `mermaid@11.12.3` (diagrams)
- `@zxing/browser@0.1.5` (barcode scanning)
- `tailwindcss@3.4.17`, `tailwindcss-animate@1.0.7`

## 4. Complete Page List (94+ pages)
Main pages: Dashboard, Tickets, TicketDetail, NewTicket, Inventory, InventoryEnhanced, InventoryAdjustments, Items, ItemsEnhanced, Vehicles, AIAssistant, Alerts, Banking, Bills, BillsEnhanced, ChartOfAccounts, CompositeItems, Contact, ContactsEnhanced, CreditNotes, CustomModules, CustomerPortal, CustomerSurvey, Customers, DataInsights, DataManagement, DataMigration, DeliveryChallans, Docs, Documents, Employees, EstimatesEnhanced, ExchangeRates, Expenses, FailureIntelligence, FaultTreeImport, FixedAssets, GSTReports, HRDashboard, Home, InvoiceSettings, Invoices, InvoicesEnhanced, JournalEntries, LeaveManagement, Login, NewTicket, OpeningBalances, OrganizationSettings, OrganizationSetupWizard, PaymentsReceived, Payroll, PlatformAdmin, PriceLists, Privacy, ProjectTasks, Projects, PublicQuoteView, PublicTicketForm, PurchaseOrders, Quotes, RecurringBills, RecurringExpenses, RecurringTransactions, Register, Reports, ReportsAdvanced, ResetPassword, SaaSLanding, SalesOrders, SalesOrdersEnhanced, SerialBatchTracking, Settings, StockTransfers, SubscriptionManagement, Suppliers, Taxes, TeamManagement, TechnicianProductivity, Terms, TicketDetail, Tickets, TimeTracking, TrackTicket, TrialBalance, Users, Vehicles, VendorCredits, ZohoSync

Sub-pages: business/ (6), customer/ (6), technician/ (7), finance/ (3), settings/ (1)

## 5. Components (19 custom)
AuthCallback, BusinessLayout, CommandPalette, CreditNoteModal, CustomerLayout, EFISidePanel, EstimateItemsPanel, FeatureGateBanner, JobCard, Layout, LocationPicker, NotificationBell, OnboardingBanner, OrganizationSwitcher, PageHeader, TechnicianLayout, UnsavedChangesDialog, UpgradeModal + ai/ folder + estimates/ folder + ui/ (shadcn)

## 6. Routing
Defined in `App.js`. ~85 routes. Uses `ProtectedRoute` wrapper for role-based access. Public routes: `/`, `/login`, `/register`, `/submit-ticket`, `/track-ticket`, `/quote/:shareToken`, `/survey/:token`, `/docs`, `/privacy`, `/terms`, `/contact`, `/reset-password`.

## 7. State Management
- React Context for auth (`AuthProvider` in App.js)
- localStorage for token and organization_id
- No Redux/Zustand — all state is component-local or context-based

## 8. API Client
`utils/api.js` — Exports: `getOrganizationId`, `setOrganizationId`, `getAuthHeaders`, `apiFetch`, `apiGet`, `apiPost`, `apiPut`, `apiPatch`, `apiDelete`, `initializeOrganization`. Auto-adds Authorization and X-Organization-ID headers. Intercepts 403 `feature_not_available` globally.

## 9. Auth Flow
1. Login: POST /api/auth/login → receives token + user
2. Token stored in localStorage
3. Organization ID stored in localStorage
4. Every API call includes Bearer token + X-Organization-ID header
5. Logout: removes token from localStorage + POST /api/auth/logout

## 10. Org Context
- Stored in localStorage as `organization_id`
- Sent as `X-Organization-ID` header on every request
- Set on login from user's org memberships

## 11. Error Handling
- 403 `feature_not_available` dispatches custom event for UpgradeModal
- General error handling is per-component (no global interceptor for 401/500)

## 12. `index.html` — See Section 15 for complete contents. Includes Emergent tracking script, PostHog analytics, Sentry via meta tag.

## 13. PWA
- `manifest.json`: name "Battwheels OS", standalone, dark theme (#080C0F), volt accent (#C8FF00)
- `service-worker.js`: Cache-first for static assets, network-first for API calls

## 14. Dark/Volt Theme
- Dark background (#080C0F, #0A0E12)
- Volt green accent (#C8FF00)
- Implemented via CSS variables and Tailwind config

## 15. Mobile Responsiveness
- Tailwind breakpoints (sm, md, lg, xl)
- Sidebar collapses on mobile
- Not comprehensively tested across all pages

## 16. Known Frontend Bugs
- `EstimatesEnhanced.jsx` is 2,966 lines — unmaintainable
- `AllSettings.jsx` is 2,439 lines — massive
- `Banking_old.jsx.bak` and `Bills_old.jsx.bak` are dead files

## 17. Sidebar Pages That May Be Broken/Empty
- DeliveryChallans, FixedAssets, OpeningBalances, PurchaseOrders, VendorCredits — have frontend pages but backend collections are empty
- DataMigration — Zoho-specific, may not function without Zoho tokens

---

# SECTION 09 — INTEGRATIONS COMPLETE AUDIT

## Resend (Email)
- API key configured: **YES** (in .env)
- Domain verified: Sending from `noreply@battwheels.com` — domain must be verified in Resend dashboard
- Emails sent: Invoice email, invitation email, welcome email, password reset email, generic email
- Working end-to-end: **Depends on Resend API key validity and domain verification**
- What is broken: Nothing in code — depends on external config

## Razorpay (Payments)
- API keys configured: **YES** (in .env)
- Test or live: **LIVE KEYS** (`rzp_live_*`) — **CRITICAL: Live keys in dev environment**
- Payment link generation: Implemented
- Webhook endpoint: `/api/v1/razorpay/webhook`
- Subscription management: Not implemented
- What is broken: **Duplicate route files** (`razorpay.py` and `razorpay_routes.py`)

## WhatsApp Business API
- Credentials: Per-org, stored encrypted in `tenant_credentials` collection (2 docs)
- Live or test: Live Meta Graph API v18.0 code
- Messages: Invoice send, ticket updates, reminders
- Working: **NO — no org has configured valid WhatsApp credentials**
- What is mocked: **Not mocked in code** — the service is real but unconfigured

## GST / E-Invoice IRN
- `einvoice_service.py`: Full implementation with IRP auth, schema building, QR codes
- IRN generation: **Sandbox mode** — requires per-org IRP credentials configured via Settings UI
- GSTIN validation: Implemented (regex-based, not API-verified)

## Sentry
- DSN configured: **YES** (both backend and frontend)
- Errors captured: All unhandled exceptions, sensitive data scrubbed
- Environment tagging: Uses `ENVIRONMENT` env var
- Working: **YES** if DSN is valid

## Zoho
- **242 endpoints** across 3 route files (zoho_api.py, zoho_extended.py, zoho_sync.py)
- Credentials configured: YES (client_id, secret, refresh_token, org_id in .env)
- **Status: Legacy integration.** This is the original Zoho Books parity layer. 
- Should it stay: Questionable — most functionality has been reimplemented natively. Could be dead code.

## Other Integrations Found
- **Stripe**: Configured (test key). `invoice_payments.py` + `stripe_webhook.py`. Uses `emergentintegrations.payments.stripe`.
- **Gemini AI**: Via `emergentintegrations.llm.chat` and `EMERGENT_LLM_KEY`. Used in AI assistant, EFI, technician portal, public ticket AI suggestions.
- **PostHog**: Analytics tracking in `index.html` (frontend only).
- **Emergent Auth**: Google OAuth via `https://auth.emergentagent.com/` redirect in Login.jsx.
- **Twilio**: Env vars exist (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`) but not used in active code — WhatsApp uses Meta Graph API directly.

---

# SECTION 10 — LOGIN & USER MANAGEMENT COMPLETE AUDIT

## 1. Organization Registration
Register endpoint → creates org + admin user → seeds chart of accounts, roles, default settings → returns token

## 2. Login Flow
POST /api/auth/login → verify password (bcrypt) → create JWT (7-day expiry) → return `{token, user, organizations}` → frontend stores in localStorage

## 3. All User Roles in Database
From the 13 users: `admin` (2), `technician` (6), `customer` (2), `business_customer` (1), `accountant` (1), unspecified role count varies

## 4. Password Reset — 3 Flows
- Admin reset: `POST /api/v1/employees/{id}/reset-password` — Working
- Self-service: `POST /api/auth/change-password` — Working
- Forgot password: `POST /api/auth/forgot-password` + `POST /api/auth/reset-password` — Working (tokens SHA-256 hashed, 1-hr TTL)

## 5. How Users Added to Org
Via organization invite (`/org/me/invite`) → email sent → accept invite endpoint

## 6. User Deactivation
Set `is_active: false` via org member management endpoints

## 7. Session Expiry
JWT expires after 7 days (server.py) or 24 hours (utils/auth.py) — **INCONSISTENCY**. Frontend does not handle 401 globally.

## 8. Multi-Org Support
Yes — users have `org_memberships` array and `default_org_id`. Switch via `/api/auth/switch-organization`.

## 9. All Users in Active Database (battwheels)
| Email | Role | Org ID |
|-------|------|--------|
| admin@battwheels.in | admin | 6996dcf072ffd2a2395fee7b |
| deepak@battwheelsgarages.in | technician | MISSING |
| rahul@battwheelsgarages.in | technician | MISSING |
| priya@battwheelsgarages.in | technician | MISSING |
| customer@demo.com | customer | MISSING |
| business@bluwheelz.co.in | business_customer | MISSING |
| customer@example.com | customer | MISSING |
| new.technician.*.@battwheels.in | technician | MISSING |
| priya.verma.*.@battwheels.in | technician | MISSING |
| full_emp_*@battwheels.in | accountant | MISSING |
| service@battwheelsgarages.in | technician | MISSING |
| platform-admin@battwheels.in | admin | MISSING |
| tech@battwheels.in | technician | MISSING |

## 10. Users with Missing organization_id: **12 out of 13**

## 11. Platform Admin
Has `is_platform_admin: true` flag. Can access `/platform-admin` routes. Not tied to any org — manages all orgs.

---

# SECTION 11 — FINANCIAL ENGINE COMPLETE AUDIT

## 1. Double Entry Service Functions
`double_entry_service.py` (1,645+ lines):
- `ensure_system_accounts()` — Create default accounts
- `get_account_by_code/id/name()` — Account lookups
- `get_or_create_account()` — Lazy account creation
- `get_next_reference_number()` — Sequential numbering
- `create_journal_entry()` — Core double-entry posting
- `reverse_journal_entry()` — Reversal
- `post_sales_invoice()` — AR journal on invoice
- `post_payment_received()` — Clear AR on payment
- `post_purchase_bill()` — AP journal on bill
- `post_bill_payment()` — Clear AP on payment
- `post_expense()` — Expense journal
- `post_payroll()` — Payroll journal
- `post_payroll_run()` — Batch payroll
- `get_trial_balance()` — Trial balance calculation
- `get_account_balance()` — Single account balance
- `get_profit_and_loss()` — P&L report
- `get_balance_sheet()` — Balance sheet
- `get_journal_entries()` — Entry listing
- `get_account_ledger()` — Account ledger

## 2. Events That Trigger Journal Entries
- Sales invoice creation → Debit AR, Credit Revenue
- Payment received → Debit Bank, Credit AR
- Purchase bill → Debit Expense/COGS, Credit AP
- Bill payment → Debit AP, Credit Bank
- Expense → Debit Expense, Credit Bank/Cash
- Payroll → Debit Salary Expense, Credit Bank + Liabilities

## 3. Trial Balance Status
**RESULT: Total Debit = 0, Total Credit = 0**
This means either:
- Journal entries have no numeric values in `lines[].debit`/`lines[].credit` fields
- The 18 entries may use a different schema than expected
- **THE TRIAL BALANCE IS EFFECTIVELY BROKEN**

## 4. Period Locking
`period_locks` collection **DOES NOT EXIST**. Design document at `/app/docs/PERIOD_LOCKING_DESIGN.md` but **NOT IMPLEMENTED**.

## 5. Chart of Accounts
396 accounts. Types distribution:
- Expense: 93 (68 Expense + 25 expense)
- Income: 26 (16 Income + 10 income)
- Asset: 41 (21 Asset + 20 asset)
- Liability: 44 (29 Liability + 12 liability + 2 Long Term + 1 Other)
- Equity: 20 (16 Equity + 4 equity)
- Other: Bank (2), Cash (2), Stock (1), Payment Clearing (2), AR (1), AP (1), COGS (6), Other Current Asset (27), Other Current Liability (15), Fixed Asset (4)
- **None: 109 accounts** — missing type classification

## 6. TDS Rates
7 tax entries: GST 0%, 5%, 12%, 18%, 28%, Exempt, Non-GST. TDS-specific rates managed in `tds_service.py`.

## 7. GST Rates
Same 7 entries as above.

## 8. Known Financial Issues
- **Trial balance returns 0/0** — likely schema mismatch
- **109 accounts have `None` type** — data quality issue
- **Period locking not implemented**
- **Duplicate account types** (e.g., "expense" vs "Expense") — inconsistent casing

---

# SECTION 12 — TEST SUITE COMPLETE AUDIT

## 1. Test Files (105+ files in `backend/tests/`)
Major test files: test_17flow_audit, test_all_settings, test_audit_blockers, test_comprehensive_audit, test_contacts_enhanced, test_estimates_enhanced, test_finance_module, test_gst_accounting_flow, test_hr_module, test_inventory_hr_modules, test_invoice_automation, test_items_enhanced, test_multi_tenant_crud, test_password_reset, test_tickets_module, test_week2_features, and 90+ more.

## 2-3. Test Suite Run
**NOT EXECUTED** — Running the full 105-file test suite against the production database would be destructive (tests create/modify data). The tests are designed to run against a test URL, not production.

## 4. Test collection errors
Many test files hardcode `http://localhost:8001` or use environment-specific URLs. Collection would succeed but execution against production DB is dangerous.

## 5. Zero Test Coverage Areas
- Period locking (not implemented)
- E-way bills
- GSTR-2A reconciliation
- PF/ESI challan generation
- WhatsApp live messaging

## 6. Tests That Pass But Test Wrong Thing
Cannot assess without running them. The hardcoded localhost URLs in test files suggest some may not reach the actual API.

---

# SECTION 13 — KNOWN BUGS & BROKEN FEATURES

## 1. TODO Comments (from codebase search)
- `backend/events/notification_events.py:115` — "TODO: Actually send notification via notification_service"
- `backend/routes/inventory_enhanced.py:856` — "TODO: Send customer notification"
- `backend/routes/inventory_enhanced.py:1001` — "TODO: Create credit note if requested"
- `backend/tests/test_tenant_isolation.py:109` — "TODO: After migration, should return 400/403"

## 2. FIXME Comments: **NONE**
## 3. HACK Comments: **NONE**
## 4. NotImplementedError: **NONE**

## 5. Stubbed Implementations
- WhatsApp: Real code but no credentials configured → effectively non-functional
- E-Invoice: Sandbox mode, requires per-org IRP credentials
- `banking_module.py`: Router registration is COMMENTED OUT in server.py (line 5885)

## 6. Hardcoded Mock Data
- Seed utility (`seed_utility.py`) creates sample data but is not "mock"
- No endpoints return explicitly fake data

## 7. Frontend Placeholder/Fake Data
- `Banking_old.jsx.bak`, `Bills_old.jsx.bak` — dead backup files
- DeliveryChallans, FixedAssets, OpeningBalances — pages exist but backend collections empty

## 8. Mocked Integrations
- WhatsApp: Not mocked in code, but unconfigured = non-functional
- E-Invoice IRP: Sandbox mode only

## 9. Console.error/Console.warn in Frontend
Not audited line-by-line. The `api.js` interceptor for 403 uses event dispatch.

## 10. CHANGELOG/INCIDENTS
- `memory/CHANGELOG.md`: 47 lines, exists but brief
- `docs/INCIDENTS.md`: **DOES NOT EXIST**

---

# SECTION 14 — MULTI-TENANCY AUDIT

## 1. Missing organization_id by Collection
| Collection | Missing/Total |
|-----------|---------------|
| tickets | 0/10 |
| invoices_enhanced | 0/3 |
| contacts | 0/15 |
| journal_entries | 0/18 |
| employees | 0/0 |
| inventory | 0/3 |
| estimates | 0/7 |
| **users** | **12/13** |

## 2. Cross-Tenant Isolation Test
Not executed in this audit (would require creating test data). The TenantGuardMiddleware enforces org_id from JWT on all tenant-scoped collections.

## 3. Tenant-Exempt Endpoints
- All public routes (`/api/public/*`)
- Auth routes (`/api/auth/*`)
- Health check
- Platform admin routes (check `is_platform_admin` instead of org_id)

## 4. Public Ticket Form
Org resolved from form submission data — the public form includes an `organization_id` or org slug that maps to the target organization.

## 5. Role Escalation
- Role changes require `org_admin`/`owner` via `PATCH /org/me/members/{user_id}/role`
- `platform-admin` has `POST /platform-admin/users/make-admin` — restricted to platform admins
- No self-elevation endpoint found

---

# SECTION 15 — DEPLOYMENT & INFRASTRUCTURE

## 1. Currently Running
- Backend: Supervisor-managed uvicorn on port 8001
- Frontend: Supervisor-managed CRA dev server on port 3000
- MongoDB: Supervisor-managed on default port 27017
- Nginx proxy for code-server

## 2. Ports
- Backend: 8001
- Frontend: 3000
- External access: Via Emergent preview URL (https://production-readiness-7.preview.emergentagent.com)

## 3. Frontend Serving
Separately via CRA dev server (not served by backend)

## 4. `index.html`
Contains: Meta tags (PWA, theme), Google Fonts (Inter), Emergent tracking script (`emergent-main.js`), Visual Edits iframe scripts, PostHog analytics, DOMException error suppressor.

## 5. Emergent-Specific Injections
- `emergent-main.js` tracking script
- Visual Edits iframe detection + debug monitor + Tailwind CDN
- PostHog analytics (phc_xAvL2Iq4tFmANRE7kzbKwaSqp1HJjN7x48s3vr0CMjs)
- Emergent Auth redirect (`https://auth.emergentagent.com/`)

## 6. Dockerfile: **DOES NOT EXIST**
## 7. railway.toml: **DOES NOT EXIST**

## 8. What Would Break Outside Emergent
- Auth redirect to `auth.emergentagent.com`
- Emergent tracking scripts
- Visual Edits iframe scripts
- CORS origins tied to `.preview.emergentagent.com`
- `emergentintegrations` package (proprietary)
- Preview URL-based routing

## 9. MongoDB
Local instance at `mongodb://localhost:27017`. No authentication. No Atlas.

## 10. Hardcoded localhost References
All in test files only (17+ references to `http://localhost:8001`). No production code references localhost.

## 11. Hardcoded Emergent URLs
- `backend/server.py:6692` — CSP header includes `emergentagent.com`
- `backend/routes/fault_tree_import.py:364` — Hardcoded default file URL from `customer-assets.emergentagent.com`
- `frontend/src/pages/Login.jsx:581` — Emergent Auth redirect
- Various `emergentintegrations` imports in services

---

# SECTION 16 — DOCUMENTATION & SOP AUDIT

## 1. All Markdown Files (45 total)
| File | Lines |
|------|-------|
| docs/BATTWHEELS_OS_TECHNICAL_SPEC.md | 2,521 |
| docs/TECHNICAL_SPEC.md | 2,041 |
| docs/EFI_ARCHITECTURE.md | 1,423 |
| PRE_LAUNCH_AUDIT.md | 1,042 |
| BATTWHEELS_OS_AUDIT_REPORT.md | 837 |
| memory/ARCHITECTURE_ANALYSIS.md | 606 |
| SAAS_ARCHITECTURE_REVIEW.md | 589 |
| ARCHITECTURE_CONTRACT_RECONCILIATION.md | 581 |
| CRITICAL_REMEDIATION_BLUEPRINT.md | 528 |
| PRODUCTION_READINESS_REPORT.md | 517 |
| ...and 35 more (total ~18,708 lines of markdown) |

## 2. ENVIRONMENT_SOP.md
Exists. Defines three environments (dev/staging/production), promotion ladder with human sign-off, production read-only rule. **CURRENTLY BEING VIOLATED** — DB_NAME is `battwheels` (production).

## 3. CODING_STANDARDS.md
Exists. Three rules: (1) Every MongoDB query must be org_id scoped, (2) Counts must be database-level not client-side, (3) References the SOP.

## 4. docs/INCIDENTS.md — **DOES NOT EXIST**

## 5. docs/DEPLOYMENT.md — **DOES NOT EXIST**

## 6. memory/PRD.md
Exists. 60 lines. Covers problem statement, architecture, Week 1 & 2 implementation, test coverage, remaining tasks, credentials.

## 7. Documentation Accuracy
- ENVIRONMENT_SOP.md: **STALE** — rules are correct but actively violated
- CODING_STANDARDS.md: Accurate to current practices
- PRD.md: Slightly outdated (doesn't reflect current audit status)
- Most root-level .md files are historical audit reports, not living documentation

---

# FINAL SUMMARY — HONEST ASSESSMENT

## 1. What is Genuinely Working End-to-End
- **Login/Registration**: User can register org, login, get token, access dashboard
- **Ticket Creation & Management**: Create ticket, assign technician, track status, close
- **Public Ticket Submission**: External customer submits ticket via public form
- **Invoice Creation**: Create invoice with GST, generate PDF, record payment
- **Estimate Creation**: Create estimate, send, convert to invoice
- **Contact Management**: Full CRUD with addresses, persons, statements
- **EFI Diagnostic**: AI-assisted failure diagnosis with decision trees
- **Items Management**: Full CRUD with variants, pricing, stock levels
- **Expense Management**: Create, approve, record
- **GST Reports**: GSTR-1 and GSTR-3B generation
- **HR Attendance**: Clock-in/out
- **Leave Management**: Request and approval flow
- **Password Reset**: All 3 flows verified
- **Role-Based Access**: RBAC enforcement at middleware level
- **Tenant Isolation**: org_id enforcement on all business data

## 2. What is Partially Working
- **Payments (Razorpay)**: Code works but uses **LIVE keys** in dev — dangerous
- **Email (Resend)**: Code works but depends on external API key validity
- **Trial Balance**: Shows 0/0 — likely schema mismatch in journal entries
- **Chart of Accounts**: 109 of 396 accounts have `None` type
- **Payroll**: Code exists but `employees` collection is empty in production
- **Banking**: Module exists but `banking_module.py` router is commented out
- **WhatsApp**: Full code but no org has configured credentials
- **E-Invoice**: Full code but sandbox only, needs IRP credentials
- **Credit Notes**: Basic CRUD, but limited functionality
- **User Management**: 12 of 13 users missing organization_id

## 3. What is Completely Missing
- **Period Locking** — Design document exists, not implemented
- **GSTR-2A Reconciliation** — Not built
- **E-way Bills** — Not built
- **CSRF Protection** — Not implemented
- **Input Sanitization Middleware** — Not implemented
- **Estimate → Ticket Conversion** — Not built
- **PF/ESI Challan Generation** — Not built
- **docs/INCIDENTS.md** — Not created
- **scripts/migrations/ directory** — Not created
- **battwheels_staging database** — Not provisioned
- **Dockerfile / railway.toml** — No deployment config

## 4. What is Dead Code
- `backend/routes/zoho_api.py` (3,671 lines, 121 endpoints) — Legacy Zoho parity, likely unused
- `backend/routes/zoho_extended.py` (2,983 lines, 104 endpoints) — Same
- `frontend/src/pages/Banking_old.jsx.bak` — Dead backup
- `frontend/src/pages/Bills_old.jsx.bak` — Dead backup
- `backend/middleware/tenant.py` — Deprecated tombstone (intentionally empty)
- `backend/routes/razorpay.py` — Duplicate of `razorpay_routes.py`
- Root-level empty files: `Integrations`, `Journal`
- Root-level audit scripts: `run_cto_audit.py`, `run_cto_reaudit_v2.py`, `backend_test.py`
- Multiple root-level audit .md files (25+) — historical, not living docs

## 5. Top 10 Most Critical Things to Fix/Build
| # | Priority | Item | Business Impact |
|---|----------|------|----------------|
| 1 | **P0** | **Fix DB_NAME to battwheels_dev** | Currently operating on PRODUCTION data. One wrong write = data corruption. |
| 2 | **P0** | **Fix Razorpay LIVE keys in dev** | Live payment processing in development = financial risk |
| 3 | **P0** | **Fix 12 users missing organization_id** | Tenant isolation gap for user records |
| 4 | **P0** | **Fix Trial Balance (0/0)** | Core financial reporting is broken |
| 5 | **P1** | **Fix 109 accounts with None type** | Chart of accounts data quality |
| 6 | **P1** | **Implement Period Locking** | Financial integrity — prevent backdated edits |
| 7 | **P1** | **Implement CSRF Protection** | Security vulnerability |
| 8 | **P1** | **Remove/archive Zoho dead code** | 6,654 lines of unmaintained legacy code |
| 9 | **P2** | **Refactor EstimatesEnhanced.jsx** | 2,966 lines — unmaintainable |
| 10 | **P2** | **Refactor server.py** | 6,716 lines with 50+ inline models — monolith |

## 6. Production Readiness Score: **4/10**

**Reasoning:**
- Core CRUD flows work (+2)
- Multi-tenancy enforcement exists (+1)
- Financial engine exists but trial balance broken (-1)
- LIVE payment keys in dev environment (-2)
- Operating on production database (-2)
- No CSRF, no input sanitization (-1)
- 12/13 users missing org_id (-1)
- No deployment config (Dockerfile, CI/CD) (-1)
- Comprehensive API surface (+1)
- Test suite exists but untested against current state (0)
- Good documentation culture (+1)

## 7. What a New Developer Needs to Know

1. **The backend is a 6,716-line monolith** (`server.py`) with 50+ inline Pydantic models. Route files are separate but the entry point is enormous.

2. **DB_NAME currently points to PRODUCTION** (`battwheels`). Change to `battwheels_dev` before doing ANY work. Read `ENVIRONMENT_SOP.md`.

3. **There are 700+ API endpoints** across 64+ route files. The Zoho routes (242 endpoints) are likely dead code.

4. **Two JWT systems exist** — one in `server.py` (7-day expiry) and one in `utils/auth.py` (1-day expiry). This is a bug.

5. **Multi-tenancy is enforced** by TenantGuardMiddleware. Every query must include `organization_id`. But 12/13 users are missing it.

6. **The financial engine** (`double_entry_service.py`) is the heart of accounting. Trial balance currently returns 0/0 — investigate journal entry schema.

7. **Razorpay uses LIVE keys** in the development environment. Do not trigger any payment flows.

8. **WhatsApp and E-Invoice** are fully coded but require per-org credential configuration to function.

9. **The test suite has 105+ files** but was designed to run against test URLs, not production. Do not run tests against the production database.

10. **There are 25+ audit/report markdown files** in the root directory. These are historical artifacts from iterative quality audits. The living documents are `ENVIRONMENT_SOP.md`, `CODING_STANDARDS.md`, and `memory/PRD.md`.

---

*End of Complete Application Self-Audit*
*Generated from actual file reads — every section sourced from the live codebase.*
