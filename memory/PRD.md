# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow, EV-specific failure intelligence, and enterprise-grade inventory management.

---

## Implementation Status

### Completed (Feb 18, 2026 - Latest Session)

#### Composite Items Frontend (COMPLETE)
- Full management page at `/composite-items`
- Summary cards: Total Items, Active, Kits, Assemblies, Bundles, Inventory Value
- Create dialog with component selection from inventory
- Build/Unbuild actions with availability checking
- Detail view with BOM and build history
- Search by name/SKU, filter by type
- Navigation item added under Inventory section
- Bug fix: Collection name corrected from `items_enhanced` to `items`

#### Invoice Automation Settings (COMPLETE - Verified)
- 5-tab UI: Overdue, Due Soon, Recurring, Reminders, Late Fees
- All tabs wired to backend APIs and working
- Reminder settings save/load
- Late fee settings save/load with conditional UI
- Bulk reminder sending for overdue invoices

#### Recurring Invoices (COMPLETE - Verified)
- Backend CRUD + generate-now + stop/resume
- Frontend integrated in InvoiceSettings page (Recurring tab)
- Create dialog with customer selection, frequency, line items
- MRR dashboard with stat cards

---

### Previously Completed

#### WeasyPrint PDF Generation (COMPLETE)
- Installed missing `libpangoft2-1.0-0` system library
- PDF generation fully functional for quotes, invoices, estimates

#### Composite Items Backend (COMPLETE)
- Full CRUD for composite/kit items
- Build/Unbuild with component stock management
- Availability checking with shortage detection
- Bill of Materials support with waste percentage

#### Recurring Invoices Backend (COMPLETE)
- Full CRUD for recurring invoice profiles
- Frequency: daily, weekly, monthly, yearly
- Generate-now and batch process-due endpoints
- Auto-calculate next invoice date

#### Zoho-Style Sales Modules - All Phases (COMPLETE)
- Phase 1: Payments Received Module
- Phase 2: Stripe Online Payments, Payment Reminders
- Phase 3: Late Fees, Aging Reports, Auto Credit Application

#### Items Module - All Phases (COMPLETE)
- Phase 1: Enhanced data model, bulk actions, import/export, custom fields
- Phase 2: Price lists, barcode support, advanced reports
- Phase 3: Preferences, field configuration, auto SKU, barcode scanner

#### Quotes/Estimates Module (COMPLETE)
- Attachments, public share links, PDF generation
- Auto-conversion, templates, import/export, bulk actions

---

## Technical Stack
- **Backend**: FastAPI, MongoDB (Motor async)
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **Auth**: JWT + Emergent Google OAuth
- **AI**: Gemini (EFI semantic analysis)
- **Payments**: Stripe (active, test mode)
- **PDF**: WeasyPrint (active)

---

## Mocked Services
- **Email (Resend)**: Logs to console, pending `RESEND_API_KEY`
- **Razorpay**: Mocked

---

## Test Credentials
- **Admin**: admin@battwheels.in / admin123
- **Technician**: deepak@battwheelsgarages.in / tech123

---

## Test Reports
- `/app/test_reports/iteration_43.json` - Composite Items + Invoice Settings (100% pass)
- `/app/test_reports/iteration_42.json` - Recurring Invoices + Invoice Automation UI
- `/app/test_reports/iteration_41.json` - Invoice Automation Phase 2&3
- `/app/test_reports/iteration_40.json` - Payments Received Final

---

## Remaining Backlog

### P0 (High Priority)
- Un-mock Resend email (requires RESEND_API_KEY from user)

### P1 (Medium Priority)
- Customer self-service portal improvements
- Advanced sales reports
- Multi-warehouse support

### P2 (Low Priority)
- Propagate standardized UI components across all pages
- Package tracking / shipment integration
- Serial number tracking
- Signature capture on quote acceptance
- Un-mock Razorpay payments
