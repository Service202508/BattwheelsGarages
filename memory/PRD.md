# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow, EV-specific failure intelligence, and enterprise-grade inventory management.

---

## Implementation Status

### Verified Complete (Feb 18, 2026 - Current Session)

#### All P1 Tasks - VERIFIED WORKING
- **Invoice Automation Settings**: 5-tab UI (Overdue, Due Soon, Recurring, Reminders, Late Fees) fully connected to backend APIs
- **Recurring Invoices**: Complete frontend/backend with create, view, manage, start/stop, generate-now functionality
- **Inventory Adjustment Reasons Management**: Admin dialog to add/edit/delete adjustment reasons (10 default reasons seeded)

### Previously Completed
- Inventory Adjustments v2 (Phases 1-3): Full Draft → Adjusted → Void workflow, Import/Export, PDF, ABC Report, Item Integration
- Composite Items: Full management page with Build/Unbuild, BOM detail view
- WeasyPrint PDF Generation (invoices/quotes)
- Zoho-Style Sales Modules (all phases)
- Items Module (all phases)
- Quotes/Estimates Module
- Enhanced Contacts Management
- Customer Portal

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

---

## Remaining Backlog

### P0 (High Priority)
- Un-mock Resend email (requires RESEND_API_KEY from user)

### P1 (Medium Priority)
- Customer self-service portal improvements
- Advanced sales reports
- Multi-warehouse support
- Advanced inventory: packages, serial/batch tracking

### P2 (Low Priority)
- Propagate standardized UI components across all pages
- Un-mock Razorpay payments
- Signature capture on quote acceptance
- PDF template customization

---

## Key Modules & Routes

### Invoice Automation (`/invoice-settings`)
- Aging Report with bucket breakdown
- Overdue/Due-Soon invoice tracking
- Payment reminder settings (before/after due date)
- Late fee configuration (percentage/fixed, grace period)
- Auto credit application

### Recurring Invoices (`/recurring-invoices`)
- Profile creation (daily/weekly/monthly/yearly)
- Generate-now, pause/resume functionality
- MRR tracking and summary stats

### Inventory Adjustments (`/inventory-adjustments`)
- Quantity and value adjustments
- Draft → Adjusted → Void workflow
- Import/Export CSV, PDF generation
- ABC Classification & FIFO reports
- Reasons management dialog

### Composite Items (`/composite-items`)
- Bundle/kit creation with component items
- Build/Unbuild operations
- BOM (Bill of Materials) tracking
