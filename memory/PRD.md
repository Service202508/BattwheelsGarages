# Battwheels OS — Product Requirements Document

## Original Problem Statement
Full-stack SaaS application (React + FastAPI + MongoDB) for EV workshop management. Features include multi-tenant architecture, ticket management, estimates/invoices, inventory, accounting (double-entry), payroll, CRM, and a customer portal.

## Architecture
- **Frontend:** React (Vite/CRA) with Shadcn/UI, TailwindCSS
- **Backend:** FastAPI with Motor (async MongoDB)
- **Database:** MongoDB
- **Auth:** JWT + Emergent-managed Google Auth
- **Integrations:** Resend (email), Razorpay, Stripe (test), Gemini (Emergent LLM Key), WhatsApp (MOCKED)

## What's Been Implemented
- Full multi-tenant SaaS with subdomain-based routing
- Complete estimates module (create, edit with line items, send, accept, convert to invoice)
- Complete invoicing with GST, payment tracking, journal entries
- Ticket/Job Card management with technician portal
- Inventory management with stock tracking
- Double-entry accounting with trial balance, P&L
- Customer portal with estimate accept/decline
- Leads management dashboard for platform admin
- Sales funnel optimization (Book Demo CTA)
- Pre-deployment audit (17 flows verified)

## Recent Changes (Feb 24, 2026)
### Bug Fixes
1. **Bug A — "Error updating estimate" on Save**: Root cause was frontend sending wrong field names (`estimate_date` instead of `date`, `customer_notes` instead of `notes`, `terms_conditions` instead of `terms_and_conditions`) AND backend PUT not handling `line_items`. Fixed in both `EstimatesEnhanced.jsx` and `estimates_enhanced.py`.
2. **Bug B — Empty line items in Edit modal**: Root cause was `handleOpenEdit` not normalizing field names between enhanced estimates (`quantity`/`rate`) and ticket estimates (`qty`/`unit_price`). Fixed in `EstimatesEnhanced.jsx`.
3. **Bug C — Estimates list not loading**: Frontend read `data.estimates` but backend returns `data.data`. Fixed to `data.data || data.estimates || []`.

### Chain Audit Fixes
4. **Estimate-to-Invoice collection bug**: `create_invoice_from_estimate` queried `db["estimates_enhanced"]` but estimates are stored in `db["estimates"]`. Fixed.
5. **Field name mapping in conversion**: `tax_percentage`→`tax_rate`, `hsn_code`→`hsn_sac_code`, `discount_percent`→`discount_value` — all handled with fallback lookups.
6. **Backend PUT endpoint enhanced**: Now accepts `line_items` in request body, atomically deletes old items and inserts new ones with recalculated totals.

## Chain Status (Estimates → Ticket → Invoice → Accounting)
| Link | Status | Notes |
|------|--------|-------|
| Estimate ↔ Ticket | ✅ Working | Ticket estimates linked via ticket_id |
| Estimate → Invoice | ✅ Fixed | Collection name bug resolved, field mapping fixed |
| Invoice → Inventory | ✅ Working | Stock deducted on invoice send, reversed on void |
| Invoice → Journal | ✅ Working | DR AR / CR Revenue / CR GST on send |
| Payment → Journal | ✅ Working | DR Bank / CR AR |
| Parts → COGS | ⚠️ Not automated | No auto COGS posting on ticket close; happens via invoice |

## Credentials
- Platform Admin: platform-admin@battwheels.in / admin
- Org Admin: admin@battwheels.in / admin
- Technician: tech@battwheels.in / tech123

## Backlog (Prioritized)
- **P0:** Guide through production deployment (5-step checklist)
- **P1:** Refactor `@app.on_event('startup')` → lifespan context manager
- **P2:** Logo swap (pending user direction)
- **P3:** Refactor EstimatesEnhanced.jsx (tech debt)
- **P4:** E2E tests with Playwright
- **P5:** Configure live WhatsApp credentials

## Mocked Services
- WhatsApp integration (`whatsapp_service.py`) — awaiting live credentials
