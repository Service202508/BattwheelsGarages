# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow, EV-specific failure intelligence, and enterprise-grade inventory management.

---

## Implementation Status

### ✅ Items Module Enhancement - Phase 2 (COMPLETE - Feb 18, 2026)

**Contact Price List Association:**
- Assign sales price list to customers
- Assign purchase price list to vendors
- Auto-apply during transaction creation
- API: `POST/GET /api/items-enhanced/contact-price-lists`

**Line-Item Level Pricing:**
- Calculate prices based on contact's price list
- Support custom rate overrides
- Apply markup/discount automatically
- Configurable rounding (none, nearest 1/5/10)
- API: `POST /api/items-enhanced/calculate-line-prices`

**Bulk Price Setting:**
- Apply percentage markup/discount to all items
- Custom per-item pricing option
- API: `POST /api/items-enhanced/price-lists/{id}/set-prices`

**Barcode/QR Code Support:**
- Create barcodes for items (CODE128, EAN13, QR)
- Auto-generate from SKU if empty
- Barcode/SKU lookup endpoint
- Batch lookup for multiple items
- API: `POST /api/items-enhanced/barcodes`
- API: `GET /api/items-enhanced/lookup/barcode/{value}`
- API: `POST /api/items-enhanced/lookup/batch`

**Advanced Reports (Phase 3 Early Delivery):**
- **Sales by Item**: Revenue, quantity sold, avg selling price
- **Purchases by Item**: Cost, quantity purchased, avg purchase price
- **Inventory Valuation**: FIFO method, total value, cost rate
- **Item Movement**: Stock in/out history, adjustments, sales, purchases
- API: `GET /api/items-enhanced/reports/sales-by-item`
- API: `GET /api/items-enhanced/reports/purchases-by-item`
- API: `GET /api/items-enhanced/reports/inventory-valuation`
- API: `GET /api/items-enhanced/reports/item-movement`

**UI Enhancements:**
- Reports tab with 3 report cards (Sales, Purchases, Valuation)
- Barcode Lookup dialog (More menu)
- "Assign to Contact" button on Price Lists tab
- "Set Bulk Prices" action on price list cards
- Refresh Reports button

---

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
- `/app/test_reports/iteration_36.json` - Items Module Phase 2 (100% pass)
- `/app/test_reports/iteration_35.json` - Items Module Phase 1 (100% pass)
- `/app/test_reports/iteration_34.json` - Phase 2 Estimates
- `/app/test_reports/iteration_33.json` - Phase 1 Estimates

---

## Upcoming Tasks (Phase 3 - Customization)
1. **Field Customization UI**
   - Configure default fields visibility
   - PDF field display settings
   - Access permissions per role

2. **Item Preferences Page**
   - SKU auto-generation settings
   - HSN/SAC enforcement rules
   - Notification preferences
   - Default values configuration

---

## Future Tasks
1. **Composite Items**
   - Kit/assembly items
   - Bill of Materials (BOM)
   - Auto-stock deduction on sale

2. **Multi-Warehouse**
   - Per-location stock tracking
   - Transfer between warehouses
   - Location-specific pricing

3. **Advanced Inventory**
   - Package tracking
   - Shipment integration
   - Serial number tracking

---

## Remaining Backlog
- Un-mock WeasyPrint PDF (missing libpangoft2)
- Un-mock Razorpay payments
- Un-mock Resend email
- Enhanced notification system
- Signature capture on quote acceptance
