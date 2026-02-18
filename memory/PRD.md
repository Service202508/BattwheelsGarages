# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow, EV-specific failure intelligence, and enterprise-grade inventory management.

---

## Implementation Status

### ✅ Zoho-Style Sales Modules - Phase 1 (COMPLETE - Feb 18, 2026)

**Payments Received Module (NEW):**
- Full Zoho-style payment recording with multi-invoice allocation
- Overpayments automatically create customer credits
- Retainer/advance payments support
- Refund functionality for credits
- Import/export payments (CSV)
- Payment summary and reports (by customer, by mode)
- Route: `/payments-received`

**API Endpoints:**
- `GET /api/payments-received/` - List payments with filters
- `POST /api/payments-received/` - Record new payment
- `GET /api/payments-received/{id}` - Payment details
- `DELETE /api/payments-received/{id}` - Delete payment
- `GET /api/payments-received/customer/{id}/open-invoices` - Customer's open invoices
- `POST /api/payments-received/{id}/refund` - Process refund
- `POST /api/payments-received/apply-credit` - Apply credit to invoice
- `GET /api/payments-received/credits` - List customer credits
- `GET /api/payments-received/summary` - Summary statistics
- `GET /api/payments-received/export` - Export to CSV

**Invoice Integration:**
- Invoice detail now shows payments from new module (`payments_received`)
- Shows available customer credits with "Apply" button
- Credits can be applied directly to invoice balance
- Credit application creates audit trail

**Customer Statement Enhancement:**
- Statement now includes payments from `payments_received` module
- Running balance calculation
- Available credits shown in summary

**Test Data:**
- Payments: PMT-00001 (₹3,000), PMT-00002 (₹4,000 with ₹510 remaining credit)
- Customer credits tracked automatically

---

### ✅ Items/Price Lists ↔ Quotes Integration (COMPLETE - Feb 18, 2026)

**Automatic Customer Pricing:**
- When creating quotes, automatically apply customer's assigned price list
- Price list badge shown on customer selection (e.g., "₹ Wholesale (-15%)")
- Item selection auto-fetches customer-specific pricing
- Toast notification shows price adjustments

**Backend Integration:**
- `GET /api/items-enhanced/item-price/{item_id}?contact_id=` - Single item pricing with price list
- `GET /api/items-enhanced/contact-pricing-summary/{contact_id}` - Customer's pricing config
- `GET /api/estimates-enhanced/item-pricing/{item_id}?customer_id=` - Item pricing for UI
- `GET /api/estimates-enhanced/customer-pricing/{customer_id}` - Customer price list info
- Estimate creation now stores `price_list_id`, `price_list_name` on estimate
- Line items track `base_rate`, `rate`, `price_list_applied`, `discount_from_pricelist`

**Frontend Integration (EstimatesEnhanced.jsx):**
- `customerPricing` state to track selected customer's price list
- `fetchCustomerPricing()` - Called when customer selected
- `fetchItemPricing()` - Gets item price with price list applied
- `selectItem()` updated to apply customer's price list automatically
- Line items table shows discounted rate with strikethrough original price
- Price list badge below item name in line items

**Verified Test Data:**
- Customer: `CUST-93AE14BE3618` (Full Zoho Test Co) - Wholesale price list
- Price List: `PL-B575D8BF` (Wholesale) - 15% discount
- Item: `1837096000000446195` (12V Battery) - Base ₹200 → Discounted ₹170

---

### ✅ Items Module Enhancement - Phase 3 (COMPLETE - Feb 18, 2026)

**Item Preferences Page:**
- SKU Settings: Enable/disable, auto-generate, prefix, sequence start
- HSN/SAC Settings: Require HSN/SAC, digits required (4/6/8)
- Alerts & Notifications: Low stock alerts, reorder point alerts
- Default Values: Unit, item type, tax rate
- Features: Enable images, custom fields, barcode
- API: `GET/PUT /api/items-enhanced/preferences`

**Field Configuration UI:**
- 15 default fields with visibility controls
- Configure: Active, Show in List, Show in Form, Show in PDF, Required
- Per-role field access (`/api/items-enhanced/field-config/for-role/{role}`)
- API: `GET/PUT /api/items-enhanced/field-config`

**Auto SKU Generation:**
- Generates sequential SKUs with configurable prefix
- Respects sequence start setting
- API: `GET /api/items-enhanced/generate-sku`

**Barcode Scanner Integration:**
- Camera-based barcode scanning using @zxing/library
- Real-time scanning with video preview
- Auto-lookup on scan detection
- Manual fallback input

**UI Enhancements (More Menu):**
- Preferences option with full settings dialog
- Field Configuration option with table UI
- Scan Barcode option with camera dialog

---

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
- `/app/test_reports/iteration_38.json` - Items/Price Lists Integration (100% pass)
- `/app/test_reports/iteration_37.json` - Items Module Phase 3 (100% pass)
- `/app/test_reports/iteration_36.json` - Items Module Phase 2 (100% pass)
- `/app/test_reports/iteration_35.json` - Items Module Phase 1 (100% pass)
- `/app/test_reports/iteration_34.json` - Phase 2 Estimates
- `/app/test_reports/iteration_33.json` - Phase 1 Estimates

---

## All Items Module Features Complete ✅

### Phase 1: Core Enhancements
- Enhanced data model (SKU, HSN/SAC, tax, inventory tracking)
- Advanced list view (search, sort, filter)
- Bulk actions (clone, activate/deactivate, delete)
- Import/Export (CSV/JSON)
- Item history tracking
- Custom fields

### Phase 2: Price Lists & Adjustments
- Contact price list association
- Line-item level pricing
- Bulk price setting
- Barcode/QR support
- Advanced reports (Sales, Purchases, Valuation, Movement)

### Phase 3: Customization
- Item Preferences page
- Field Configuration UI
- Auto SKU generation
- Barcode scanner integration

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
