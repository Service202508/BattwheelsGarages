# Battwheels OS - Product Requirements Document

## Original Problem Statement

Battwheels OS is a multi-tenant SaaS platform for EV service management. It provides comprehensive workshop management including service tickets, job cards, invoicing, HR/payroll, inventory, and AI-assisted diagnostics (EFI - EV Failure Intelligence).

## Production Readiness Audit - December 2025

### Audit Outcome: NOT PRODUCTION READY

**Overall Score: 5.1/10 (D+)**

### Critical Findings

| Dimension | Score | Status |
|-----------|-------|--------|
| Multi-Tenancy | 4/10 | FAILED - Only 3.6% routes use tenant_context |
| RBAC | 3/10 | FAILED - Backend has no role enforcement |
| Security | 4/10 | FAILED - Credentials in repository |
| EFI AI | 8/10 | PASSED - Real AI integration working |
| Business Ops | 6/10 | PARTIAL - Core features work |

### P0 (Must Fix Before ANY Deployment)

1. **Tenant Isolation** - Add `tenant_context_required` to ALL 150+ routes
2. **Backend RBAC** - Implement role checking middleware
3. **Secrets Management** - Remove `.env` from repo, use vault
4. **Password Hashing** - Standardize on bcrypt (currently mixed)

### P1 (Fix Before Customer-Facing Deployment)

1. **Inventory-Accounting Link** - Wire parts consumption to COGS journal entries
2. **Database Indexes** - Add compound indexes for multi-tenant queries
3. **Query Pagination** - Add pagination to all list endpoints

### P2 (Post-Launch Improvements)

1. Form 16 PDF generation
2. Refund handling via Razorpay
3. Company logos in email templates
4. SLA automation for tickets

## Core Requirements (Original)

### Service Ticket System
- Create/assign/track service tickets
- Job card costing with parts and labor
- Customer communication and approvals
- Public ticket tracking

### Finance Module
- Invoices with GST handling
- Estimates and quotes
- Double-entry accounting
- Payment collection

### HR Module
- Employee management
- Attendance tracking
- Payroll processing
- TDS compliance

### Inventory Module
- Stock management
- Part allocation to tickets
- Low stock alerts
- Purchase orders

### EFI AI System
- AI-assisted diagnostics
- Failure card knowledge base
- Hinglish technician guidance
- Confidence scoring

## Architecture

```
/app/
├── backend/
│   ├── core/           # Multi-tenant foundation
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   └── models/         # Data models
└── frontend/
    └── src/
        ├── pages/      # Main views
        └── components/ # Reusable UI
```

## Tech Stack

- **Backend:** FastAPI, Pydantic, Motor (MongoDB)
- **Frontend:** React, TailwindCSS, Shadcn/UI
- **AI:** Gemini via Emergent LLM Key
- **Payments:** Razorpay (live), Stripe (test)

## 3rd Party Integrations

| Integration | Status |
|-------------|--------|
| Razorpay | LIVE |
| NIC E-Invoice | SANDBOX |
| Resend Email | CONFIGURED |
| Gemini AI | LIVE |
| Zoho Books | CONFIGURED |

## Test Credentials

- Email: `admin@battwheels.in`
- Password: `admin`

## What's Been Implemented

- Multi-organization login flow
- Service ticket lifecycle
- Invoice generation with GST
- Estimate workflow
- Customer/supplier management
- Basic HR and payroll
- Inventory tracking
- AI diagnostic guidance
- Customer portal
- Business portal

## What's NOT Working (Per Audit)

1. Tenant isolation on most routes
2. Role-based access control on backend
3. Inventory to accounting integration
4. Stock movement audit trail
5. COGS journal entries from parts usage

## Next Steps (Post-Audit)

1. Review `/app/PRODUCTION_READINESS_REPORT.md` for detailed findings
2. Prioritize P0 security fixes
3. Add test coverage for multi-tenant scenarios
4. Implement backend RBAC middleware
5. Re-audit after fixes complete
