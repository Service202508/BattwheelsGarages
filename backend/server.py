"""
Battwheels OS - Application Server
===================================
Minimal entry point: app creation, middleware, router mounting, health check.
All route handlers live in routes/. All models live in schemas/.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
import logging
import importlib
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== SENTRY ====================
def _scrub_sensitive_data(event, hint):
    SENSITIVE_KEYS = {"password","token","secret","api_key","gstin","pan_number","bank_account","ifsc_code","jwt","authorization","key_secret","webhook_secret","razorpay_key","otp","pin"}
    def scrub_dict(d):
        if not isinstance(d, dict): return d
        return {k: "[FILTERED]" if k.lower() in SENSITIVE_KEYS else scrub_dict(v) for k, v in d.items()}
    if "request" in event:
        if "data" in event["request"]: event["request"]["data"] = scrub_dict(event["request"]["data"])
        if "headers" in event["request"]: event["request"]["headers"] = scrub_dict(event["request"]["headers"])
    return event

SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(dsn=SENTRY_DSN, integrations=[FastApiIntegration()], traces_sample_rate=0.1, environment=os.environ.get("ENVIRONMENT","development"), before_send=_scrub_sensitive_data)
        logger.info("Sentry monitoring initialized")
    except Exception as e:
        logger.warning(f"Sentry init failed: {e}")

from config.env_validator import check_and_report
if not check_and_report():
    logger.warning("Missing env vars — continuing with defaults")

# ==================== DATABASE ====================
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME')]

# JWT — canonical source
from utils.auth import JWT_SECRET, JWT_ALGORITHM

# ==================== LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Battwheels OS...")
    try:
        await db.command("ping")
        logger.info("MongoDB connected")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")

    # Run migrations
    try:
        from migrations.runner import run_migrations
        await run_migrations(db)
        logger.info("Database migrations completed")
    except Exception as e:
        logger.warning(f"Migration runner failed: {e}")

    # Init shared helpers
    from utils.helpers import init_helpers
    init_helpers(db)

    # Ensure indexes
    try:
        from utils.indexes import ensure_compound_indexes
        await ensure_compound_indexes(db)
        logger.info("Compound indexes ensured on startup")
    except Exception as e:
        logger.warning(f"Index creation failed: {e}")

    logger.info("Battwheels OS started successfully")
    yield
    client.close()
    logger.info("Battwheels OS shutdown")

# ==================== APP ====================
app = FastAPI(title="Battwheels OS", lifespan=lifespan)
api_router = APIRouter(prefix="/api")
v1_router = APIRouter(prefix="/v1")

# ==================== EXCEPTION HANDLERS ====================
from core.tenant.exceptions import TenantAccessDenied, TenantContextMissing, TenantBoundaryViolation, TenantDataLeakAttempt, TenantQuotaExceeded, TenantSuspended

for exc_cls, msg in [
    (TenantAccessDenied, "Access denied"), (TenantContextMissing, "Organization context required"),
    (TenantBoundaryViolation, "Cross-tenant access denied"), (TenantDataLeakAttempt, "Security violation"),
    (TenantQuotaExceeded, "Usage limit reached"), (TenantSuspended, "Organization suspended"),
]:
    status = 403 if exc_cls != TenantQuotaExceeded else 429
    if exc_cls == TenantContextMissing: status = 400
    if exc_cls == TenantSuspended: status = 423
    app.add_exception_handler(exc_cls, lambda req, exc, s=status, m=msg: __import__('fastapi.responses', fromlist=['JSONResponse']).JSONResponse(status_code=s, content={"detail": str(exc) or m}))

# ==================== ROUTE LOADING ====================
# v1 routes (mounted at /api/v1/...)
V1_ROUTES = [
    "routes.tickets", "routes.ticket_estimates", "routes.estimates_enhanced",
    "routes.invoices_enhanced", "routes.items_enhanced", "routes.contacts_enhanced",
    "routes.inventory_enhanced", "routes.sales_orders_enhanced", "routes.bills_enhanced",
    "routes.credit_notes", "routes.payments_received", "routes.recurring_invoices",
    "routes.serial_batch_tracking", "routes.composite_items", "routes.stock_transfers",
    "routes.hr", "routes.gst", "routes.reports", "routes.reports_advanced",
    "routes.journal_entries",
    "routes.inventory", "routes.inventory_adjustments_v2",
    "routes.amc", "routes.documents", "routes.uploads", "routes.pdf_templates",
    "routes.notifications", "routes.subscriptions", "routes.time_tracking",
    "routes.projects", "routes.productivity", "routes.contact_integration",
    "routes.invoice_automation", "routes.invoice_payments", "routes.export",
    "routes.razorpay", "routes.einvoice",
    "routes.efi_guided", "routes.failure_cards", "routes.failure_intelligence",
    "routes.ai_assistant", "routes.ai_guidance", "routes.efi_intelligence",
    "routes.knowledge_brain", "routes.expert_queue",
    "routes.customer_portal", "routes.business_portal", "routes.technician_portal",
    "routes.data_integrity", "routes.data_management", "routes.data_migration",
    "routes.master_data", "routes.permissions", "routes.platform_admin",
    "routes.seed_utility", "routes.sla", "routes.insights",
    "routes.finance_dashboard", "routes.tally_export",
    "routes.expenses", "routes.banking",
    "routes.banking_module",
    "routes.financial_dashboard", "routes.organizations",
    # Extracted from server.py inline routes
    "routes.auth_main", "routes.entity_crud", "routes.inventory_api",
    "routes.sales_finance_api", "routes.operations_api",
    "routes.period_locks",
    "routes.delivery_challans", "routes.vendor_credits",
]

# API-level routes (mounted at /api/...)
API_ROUTES = [
    "routes.public_tickets", "routes.public_api", "routes.auth",
]

def _load_route(module_path, parent_router):
    """Load a route module, call its init function, and include its router."""
    try:
        mod = importlib.import_module(module_path)
        router = getattr(mod, "router", None)
        if not router:
            return
        # Call init function (various naming conventions)
        for init_name in ["init_router", "set_db", f"init_{module_path.split('.')[-1]}_router"]:
            init_fn = getattr(mod, init_name, None)
            if callable(init_fn):
                init_fn(db)
                break
        parent_router.include_router(router)
        logger.info(f"{module_path} loaded")
    except Exception as e:
        logger.error(f"Failed to load {module_path}: {e}")
        import traceback; traceback.print_exc()

for mod_path in V1_ROUTES:
    _load_route(mod_path, v1_router)

for mod_path in API_ROUTES:
    _load_route(mod_path, api_router)

# Mount routers
api_router.include_router(v1_router)
app.include_router(api_router)

# ==================== HEALTH ====================
@app.get("/api/health", tags=["Health"])
async def health_check():
    from config.platform import PLATFORM_VERSION, RELEASE_DATE
    import asyncio
    issues = []
    status_data = {"status": "healthy", "version": PLATFORM_VERSION, "release_date": RELEASE_DATE, "timestamp": datetime.now(timezone.utc).isoformat()}
    try:
        await asyncio.wait_for(db.command("ping"), timeout=2.0)
        status_data["mongodb"] = "connected"
    except Exception as e:
        status_data["mongodb"] = "disconnected"
        issues.append(f"MongoDB: {str(e)[:100]}")
    missing = [v for v in ["MONGO_URL", "JWT_SECRET"] if not os.environ.get(v)]
    if missing:
        issues.append(f"Missing env vars: {missing}")
    if issues:
        status_data["status"] = "degraded"
        status_data["issues"] = issues
    return status_data

# ==================== MULTI-TENANT INIT ====================
try:
    from core.tenant import init_tenant_context_manager, TenantGuardMiddleware
    from core.tenant.guard import init_tenant_guard
    from core.tenant.events import init_tenant_event_emitter
    from core.tenant.audit import init_tenant_audit_service
    from core.tenant.rbac import init_tenant_rbac_service
    from core.tenant.ai_isolation import init_tenant_ai_service
    from core.tenant.token_vault import init_tenant_token_vault
    from core.tenant.observability import init_tenant_observability_service
    from core.subscriptions import init_subscription_service, init_entitlement_service

    init_tenant_context_manager(db)
    init_tenant_guard(db)
    init_tenant_event_emitter(db)
    init_tenant_audit_service(db)
    init_tenant_rbac_service(db)
    init_tenant_ai_service(db)
    init_tenant_token_vault(db)
    init_tenant_observability_service(db)
    init_subscription_service(db)
    init_entitlement_service()
    TenantGuardMiddleware.set_db(db)

    from middleware.rate_limit import RateLimitMiddleware
    from middleware.rbac import RBACMiddleware
    from middleware.csrf import CSRFMiddleware
    from middleware.sanitization import SanitizationMiddleware
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SanitizationMiddleware)  # Sanitize: after CSRF, strips HTML from all JSON
    app.add_middleware(CSRFMiddleware)       # CSRF: after auth, before routes
    app.add_middleware(RBACMiddleware)
    app.add_middleware(TenantGuardMiddleware)
    logger.info("Multi-tenant system + middleware initialized")
except Exception as e:
    logger.error(f"Failed to initialize multi-tenant system: {e}")
    import traceback; traceback.print_exc()

# ==================== SECURITY + CORS ====================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' https://*.emergentagent.com https://*.battwheels.com; frame-ancestors 'none';"
    return response

_cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "https://battwheels.com,https://app.battwheels.com,https://debt-remediation-qa.preview.emergentagent.com").split(",") if o.strip()]
if os.environ.get("NODE_ENV") != "production":
    _cors_origins += ["http://localhost:3000", "http://localhost:3001"]
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=_cors_origins, allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"], allow_headers=["Authorization","Content-Type","X-Organization-ID","X-Requested-With","Accept","X-CSRF-Token"])
