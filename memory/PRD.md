# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow, EV-specific failure intelligence, and enterprise-grade inventory management.

---

## Implementation Status

### ✅ Items Module Enhancement - Phase 1 (COMPLETE - Feb 18, 2026)

**Enhanced Data Model:**
- Full Zoho Books-style item schema with:
  - SKU, HSN/SAC codes with validation
  - Sales/Purchase descriptions and rates
  - Tax preferences (taxable/non-taxable/exempt)
  - Intra-state and inter-state tax rates (GST)
  - Inventory valuation method (FIFO)
  - Opening stock and reorder levels
  - Item images (base64 storage)
  - Custom fields support

**List View Enhancements:**
- Advanced search (name, SKU, description, HSN code)
- Multi-column sorting (name, price, stock, date)
- Filtering by type, group, active status
- Bulk selection with checkboxes
- Responsive table with all columns

**Bulk Actions:**
- Clone items (creates copy with suffix)
- Activate/deactivate items
- Delete items (with transaction check)

**Import/Export:**
- Export to CSV with column selection
- Export to JSON format
- Import CSV with field mapping
- Download import template
- Overwrite existing by SKU match

**Item History:**
- Track all changes (create, update, adjust)
- Audit trail with user and timestamp
- Action-specific change details

**Custom Fields:**
- Create custom fields (text, number, date, dropdown, checkbox)
- Required field option
- Show in list/PDF options
- Delete unused fields

**Price Lists:**
- Sales and Purchase price list types
- Percentage-based pricing (markup/markdown)
- Associate with customers/vendors

**Inventory Adjustments:**
- Quantity adjustments (add/subtract)
- Value adjustments (depreciation/appreciation)
- Reason tracking (damage, recount, transfer)
- Full audit trail

**Reports:**
- Stock summary with total value
- Low stock alerts
- Inventory valuation report

**API Endpoints:**
- `GET/POST /api/items-enhanced/` - CRUD items
- `POST /api/items-enhanced/bulk-action` - Bulk operations
- `GET /api/items-enhanced/export` - CSV/JSON export
- `GET /api/items-enhanced/export/template` - Import template
- `POST /api/items-enhanced/import` - CSV import
- `GET /api/items-enhanced/history` - Item history
- `GET/POST /api/items-enhanced/custom-fields` - Custom fields
- `POST /api/items-enhanced/value-adjustments` - Value adjustments
- `GET/POST /api/items-enhanced/preferences` - Module preferences
- `POST /api/items-enhanced/validate-hsn` - HSN code validation
- `POST /api/items-enhanced/validate-sac` - SAC code validation

**UI Route:** `/inventory-management`

---

### ✅ Quotes/Estimates Module (COMPLETE)

**Phase 1 - Core Infrastructure:**
- Attachments: Up to 3 files (10MB each) per estimate
- Public Share Links: Secure URLs with expiry, password protection
- Customer Viewed Status: Auto-tracking via public link
- PDF Generation: HTML template with WeasyPrint fallback

**Phase 2 - Workflow & Automation:**
- Auto-conversion: Accepted quotes → invoices/sales orders
- PDF Templates: Standard, Professional, Minimal
- Import/Export: CSV/JSON with template
- Custom Fields: Full CRUD management
- Bulk Actions: Void, delete, mark_sent, mark_expired
- Legacy Migration: 346 contacts migrated (452 total)

### ✅ Backlog Items (COMPLETE - Feb 18, 2026)

**1. Cmd+K Command Palette**
- Global keyboard shortcut (⌘K / Ctrl+K)
- Quick Actions: Create estimates, invoices, tickets, contacts, expenses
- Page Navigation: All 20+ modules searchable
- Recent searches with localStorage persistence
- Keyboard navigation (↑↓ navigate, ↵ select, esc close)

**2. EFI Decision Tree Images**
- Upload images for diagnostic steps (max 5MB, JPG/PNG/GIF/WebP)
- Store in MongoDB with base64 encoding
- Display inline in EFI Side Panel
- Click to view full-size
- Endpoints:
  - `POST /api/efi-guided/failure-cards/{id}/step-image`
  - `GET /api/efi-guided/step-image/{image_id}`
  - `GET /api/efi-guided/failure-cards/{id}/images`
  - `DELETE /api/efi-guided/step-image/{image_id}`

---

## Technical Stack
- **Backend**: FastAPI, MongoDB (Motor async)
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **Auth**: JWT + Emergent Google OAuth
- **AI**: Gemini (EFI semantic analysis)

---

## Mocked Services
- **WeasyPrint PDF**: Falls back to HTML
- **Email (Resend)**: Logs to console
- **Razorpay**: Mocked

---

## Test Credentials
- **Admin**: admin@battwheels.in / admin123
- **Technician**: deepak@battwheelsgarages.in / tech123

---

## Test Reports
- `/app/test_reports/iteration_35.json` - Items Module Phase 1 (100% pass)
- `/app/test_reports/iteration_34.json` - Phase 2 Estimates
- `/app/test_reports/iteration_33.json` - Phase 1 Estimates

---

## Upcoming Tasks (Phase 2 - Items)
1. **Advanced Inventory Reports**
   - Sales by Item report
   - Purchases by Item report
   - FIFO batch-wise valuation report

2. **Field Customization UI**
   - Configure default fields visibility
   - PDF field display settings
   - Access permissions per role

3. **Composite Items (Future)**
   - Kit/assembly items
   - Bill of Materials (BOM)
   - Auto-stock deduction

4. **Multi-Warehouse (Future)**
   - Per-location stock tracking
   - Transfer between warehouses
   - Location-specific pricing

---

## Remaining Backlog
- Un-mock WeasyPrint PDF (missing libpangoft2)
- Un-mock Razorpay payments
- Un-mock Resend email
- Enhanced notification system
- Signature capture on quote acceptance
