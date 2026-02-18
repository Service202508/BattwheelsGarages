# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow, EV-specific failure intelligence, and enterprise-grade inventory management.

---

## Implementation Status

### Completed (Feb 18, 2026 - Current Session)

#### Zoho-Style Inventory Adjustments - Phase 1 (COMPLETE)
- **Full workflow**: Draft -> Adjusted -> Void with stock impact
- **Backend** (`/app/backend/routes/inventory_adjustments_v2.py`):
  - CRUD: Create, List (paginated/filterable), Get with audit trail, Update, Delete
  - Status transitions: Convert draft to adjusted (applies stock), Void (reverses stock)
  - Attachment support (up to 5 files, 10MB each)
  - Adjustment Reasons management (9 seeded defaults + custom CRUD)
  - Reports: Adjustment Summary, FIFO Cost Lot Tracking, ABC Classification
  - Auto-generated reference numbers with configurable prefix
  - Full audit trail logging
- **Frontend** (`/app/frontend/src/pages/InventoryAdjustments.jsx`):
  - Complete rewrite - Zoho-style list view with sortable columns
  - 7 summary stat cards (Total, Draft, Adjusted, Voided, This Month, Increases, Decreases)
  - Advanced filters: Status, Type, Reason, Date range, Warehouse, Search
  - Create/Edit dialog: Quantity & Value adjustment modes, line item management
  - Detail dialog with tabs (Line Items, Details, Audit Trail)
  - Reasons management dialog (add/disable)
  - Pagination, inline editing of line item quantities/values
- **Testing**: 100% pass rate (18/18 backend + all frontend features verified)

#### Composite Items Frontend (COMPLETE)
- Full management page at `/composite-items`
- Summary cards, Create dialog, Build/Unbuild, Detail view
- Bug fix: Collection name corrected from `items_enhanced` to `items`

---

### Previously Completed
- WeasyPrint PDF Generation
- Recurring Invoices (Backend + Frontend in InvoiceSettings)
- Invoice Automation Settings (5-tab UI)
- Composite Items Backend (CRUD, Build/Unbuild)
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
- `/app/test_reports/iteration_44.json` - Inventory Adjustments V2 (100% pass)
- `/app/test_reports/iteration_43.json` - Composite Items + Invoice Settings
- `/app/test_reports/iteration_42.json` - Recurring Invoices + Invoice Automation UI

---

## Remaining Backlog

### P0 (High Priority)
- Inventory Adjustments Phase 2: CSV/XLS import/export, ABC report with drill-down, PDF template for adjustments
- Inventory Adjustments Phase 3: Reason admin settings page, Adjust Stock button on item details, optional ticket linking

### P1 (Medium Priority)
- Un-mock Resend email (requires RESEND_API_KEY)
- Customer self-service portal improvements
- Advanced sales reports
- Multi-warehouse support

### P2 (Low Priority)
- Propagate standardized UI components
- Package tracking / serial numbers
- Un-mock Razorpay payments
