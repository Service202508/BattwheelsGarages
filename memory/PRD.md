# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow, EV-specific failure intelligence, and enterprise-grade inventory management.

---

## Implementation Status

### Completed (Feb 18, 2026 - Current Session)

#### Inventory Adjustments Phase 2 - Import/Export & Reports (COMPLETE)
- **CSV Export**: Stream adjustments as CSV with applied filters, all columns including Ticket ID
- **CSV Import**: Validate endpoint (field detection, item matching, preview) + Process endpoint (creates drafts, grouped by reference number)
- **PDF Generation**: WeasyPrint-powered professional PDF documents for any adjustment
- **ABC Classification Report**: Items classified A/B/C by adjustment activity with drill-down to individual adjustments per item
- **Testing**: 100% (15/15 backend + 14/14 frontend features)

#### Inventory Adjustments Phase 3 - Item Integration & Ticket Linking (COMPLETE)
- **Adjust Stock from Items Page**: Per-item "Adjust Stock" action in ItemsEnhanced dropdown menu, navigates to pre-filled adjustment form
- **Ticket Linking**: Optional `ticket_id` field in adjustment creation, stored and visible in detail view and CSV export
- **Quick Adjust URL Params**: `/inventory-adjustments?quick_adjust={id}&item_name={name}&stock={qty}` auto-opens create dialog

#### Inventory Adjustments Phase 1 - Core Workflow (COMPLETE - Previous)
- Full Draft -> Adjusted -> Void workflow with stock impact
- CRUD, reasons management (9 defaults), audit trail, attachments
- Reports: Adjustment Summary, FIFO Cost Lot Tracking
- Paginated list with 7 summary cards, advanced filters

#### Composite Items Frontend (COMPLETE - Previous)
- Full management page with Build/Unbuild, BOM detail view

---

### Previously Completed
- WeasyPrint PDF Generation (invoices/quotes)
- Recurring Invoices (Backend + Frontend)
- Invoice Automation Settings (5-tab UI)
- Composite Items Backend
- Zoho-Style Sales Modules (all phases)
- Items Module (all phases)
- Quotes/Estimates Module

---

## Technical Stack
- **Backend**: FastAPI, MongoDB (Motor async)
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **Auth**: JWT + Emergent Google OAuth
- **AI**: Gemini (EFI semantic analysis)
- **Payments**: Stripe (active, test mode)
- **PDF**: WeasyPrint (active)

## Mocked Services
- **Email (Resend)**: Logs to console, pending `RESEND_API_KEY`
- **Razorpay**: Mocked

## Test Credentials
- **Admin**: admin@battwheels.in / admin123
- **Technician**: deepak@battwheelsgarages.in / tech123

## Test Reports
- `/app/test_reports/iteration_45.json` - Phase 2+3: Export/Import/PDF/ABC/Ticket (100%)
- `/app/test_reports/iteration_44.json` - Phase 1: Core CRUD + Workflow (100%)
- `/app/test_reports/iteration_43.json` - Composite Items + Invoice Settings

---

## Remaining Backlog

### P0 (High Priority)
- Un-mock Resend email (requires RESEND_API_KEY)

### P1 (Medium Priority)
- Customer self-service portal improvements
- Advanced sales reports
- Multi-warehouse support
- Advanced inventory: packages, serial/batch tracking

### P2 (Low Priority)
- Propagate standardized UI components across all pages
- Un-mock Razorpay payments
- Signature capture on quote acceptance
