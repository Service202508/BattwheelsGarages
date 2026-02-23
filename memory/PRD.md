# Battwheels OS - Product Requirements Document

## Original Problem Statement

Battwheels OS is a multi-tenant SaaS platform for EV service management. It provides comprehensive workshop management including service tickets, job cards, invoicing, HR/payroll, inventory, and AI-assisted diagnostics (EFI - EV Failure Intelligence).

## Production Readiness Status - December 2025

### Updated After Critical Fixes: IMPROVED

**Overall Score: 7.5/10 (B-) — Up from 5.1/10**

### Critical Fixes Completed (December 2025)

| Fix | Status | Files Modified |
|-----|--------|----------------|
| ✅ Tenant Isolation | ALL routes protected via TenantGuardMiddleware | `core/tenant/guard.py`, `server.py` |
| ✅ Backend RBAC | Role-based access control enforced | `middleware/rbac.py` |
| ✅ Secrets Management | .env.example + startup validation | `config/env_validator.py` |
| ✅ Inventory → COGS | Stock movements + journal entries | `services/inventory_service.py` |

### Updated Scores

| Dimension | Before | After |
|-----------|--------|-------|
| Multi-Tenancy | 4/10 | 8/10 |
| RBAC | 3/10 | 8/10 |
| Security | 4/10 | 7/10 |
| Production Ready | 3/10 | 7/10 |

**Critical vulnerabilities: 0** (was 3)

### Remaining P1 Tasks

1. **Database Indexes** - Add compound indexes for multi-tenant queries
2. **Query Pagination** - Add pagination to all list endpoints
3. **Rate Limiting** - Add API rate limiting

### P2 (Post-Launch)

1. Form 16 PDF generation
2. Refund handling via Razorpay
3. Company logos in email templates
4. SLA automation for tickets

## Core Features Implemented

### Service Ticket System ✅
- Create/assign/track service tickets
- Job card costing with parts and labor
- Customer communication and approvals
- Public ticket tracking

### Finance Module ✅
- Invoices with GST handling
- Estimates and quotes
- Double-entry accounting
- Payment collection

### HR Module ✅
- Employee management
- Attendance tracking
- Payroll processing
- TDS compliance

### Inventory Module ✅ (Enhanced)
- Stock management
- Part allocation to tickets
- **Stock movements on consumption** (NEW)
- **COGS journal entries** (NEW)
- Low stock alerts
- Purchase orders

### EFI AI System ✅
- AI-assisted diagnostics (Gemini)
- Failure card knowledge base
- Hinglish technician guidance
- Confidence scoring

## Security Architecture (NEW)

### Middleware Stack
1. **TenantGuardMiddleware** - Enforces tenant context on ALL protected routes
2. **RBACMiddleware** - Enforces role-based access control

### Role Hierarchy
```
org_admin > manager > [accountant | technician | dispatcher] > viewer
customer / fleet_customer (portal access)
```

### Route Protection
- ALL routes require valid JWT + organization membership
- Public routes explicitly whitelisted
- Cross-tenant access blocked at middleware level
- Security alerts logged for violation attempts

## Tech Stack

- **Backend:** FastAPI, Pydantic, Motor (MongoDB)
- **Frontend:** React, TailwindCSS, Shadcn/UI
- **AI:** Gemini via Emergent LLM Key
- **Payments:** Razorpay (live), Stripe (test)

## Test Credentials

- Email: `admin@battwheels.in`
- Password: `admin`

## Key Files Reference

### Security
- `/app/backend/core/tenant/guard.py` - Tenant isolation middleware
- `/app/backend/middleware/rbac.py` - RBAC middleware
- `/app/backend/config/env_validator.py` - Env validation

### Business Logic
- `/app/backend/services/inventory_service.py` - Stock + COGS
- `/app/backend/services/double_entry_service.py` - Accounting engine
- `/app/backend/services/ticket_service.py` - Ticket management

### Configuration
- `/app/backend/.env.example` - Environment template
- `/app/PRODUCTION_READINESS_REPORT.md` - Full audit report
