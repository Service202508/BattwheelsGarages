# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

**Core Principle:** EFI is about reasoning, not just documentation.

## What's Been Implemented

### Bills & Purchase Orders Enhanced Module (Feb 17, 2026) ✅ COMPLETE - NEW

**Full Payables Management System:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Bills CRUD** | `/api/bills-enhanced/` | ✅ List/Create/Detail | ✅ |
| **Bill Payments** | `/api/bills-enhanced/{id}/payments` | ✅ Record payments | ✅ |
| **Purchase Orders CRUD** | `/api/bills-enhanced/purchase-orders` | ✅ Create/List POs | ✅ |
| **PO Status Workflow** | `issue`, `receive`, `convert-to-bill` | ✅ Draft→Issued→Received→Billed | ✅ |
| **Bill Summary** | `/api/bills-enhanced/summary` | ✅ Total, Draft, Open, Overdue, Paid | ✅ |
| **PO Summary** | `/api/bills-enhanced/purchase-orders/summary` | ✅ Statistics by status | ✅ |
| **Aging Report** | `/api/bills-enhanced/aging-report` | ✅ By aging bucket | ✅ |
| **Vendor-wise Report** | `/api/bills-enhanced/vendor-wise` | ✅ Payables by vendor | ✅ |
| **Open/Void/Clone Bill** | Status actions | ✅ Bill lifecycle | ✅ |

**Frontend Features:**
- New page at `/bills-enhanced` (Bills in Purchases section)
- Summary cards: Total Bills, Draft, Open, Overdue, Total Payable, Total Paid
- Tabs: Bills, Purchase Orders, Overdue
- Create Bill dialog: Vendor, Bill Number, Date, Payment Terms, Line Items
- Create PO dialog: Vendor, Order Date, Expected Delivery, Line Items
- Bill Detail dialog: Header info, line items table, totals, payments, history
- PO Detail dialog: With status actions (Issue, Receive, Convert to Bill)
- Pay button for recording payments
- Status filter and search

---

### Recurring Bills Module (Feb 17, 2026) ✅ COMPLETE - NEW

**Automated Vendor Payment Scheduling:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Recurring Bill CRUD** | `/api/zoho/recurring-bills` | ✅ List/Create/Detail | ✅ |
| **Stop/Resume** | `/api/zoho/recurring-bills/{id}/stop\|resume` | ✅ Action buttons | ✅ |
| **Auto Generation** | `/api/zoho/recurring-bills/generate` | ✅ Generate Due Bills | ✅ |
| **Frequency Options** | weekly, monthly, yearly | ✅ Select dropdown | ✅ |
| **Line Items** | Embedded in profile | ✅ Add/Remove items | ✅ |

**Frontend Features:**
- New page at `/recurring-bills` (Purchases → Recurring Bills)
- Summary cards: Total Profiles, Active, Stopped, Monthly Estimate
- Tabs: Active, Stopped, All
- Create dialog with vendor, frequency, line items
- Stop/Resume/Delete actions per profile

---

### Fixed Assets Module (Feb 17, 2026) ✅ COMPLETE - NEW

**Asset Tracking with Depreciation:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Asset CRUD** | `/api/zoho/fixed-assets` | ✅ List/Create/Detail | ✅ |
| **Asset Summary** | `/api/zoho/fixed-assets/summary` | ✅ By type, totals | ✅ |
| **Depreciation** | `/api/zoho/fixed-assets/{id}/depreciate` | ✅ Record monthly | ✅ |
| **Disposal/Sale** | `/api/zoho/fixed-assets/{id}/dispose` | ✅ With gain/loss calc | ✅ |
| **Write-Off** | `/api/zoho/fixed-assets/{id}/write-off` | ✅ Bad asset write-off | ✅ |
| **Asset Types** | furniture, vehicle, computer, equipment, etc. | ✅ Filter by type | ✅ |

**Frontend Features:**
- New page at `/fixed-assets` (Finance → Fixed Assets)
- Summary cards: Total Assets, Active, Purchase Value, Depreciation, Book Value
- Tabs: Active, Fully Depreciated, Disposed
- Create dialog with asset details, useful life, depreciation method
- Depreciation preview calculator
- Detail dialog with financial info, depreciation history
- Action buttons: Record Depreciation, Dispose/Sell, Write Off

---

### Custom Modules (Feb 17, 2026) ✅ COMPLETE - NEW

**Dynamic Module Builder:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Module CRUD** | `/api/zoho/custom-modules` | ✅ Create/List modules | ✅ |
| **Field Types** | text, number, date, dropdown, checkbox, etc. | ✅ Field builder UI | ✅ |
| **Record CRUD** | `/api/zoho/custom-modules/{id}/records` | ✅ Add/Edit/Delete | ✅ |
| **Search Records** | Query param: search | ✅ Search input | ✅ |
| **Deactivate Module** | DELETE `/api/zoho/custom-modules/{id}` | ✅ Soft delete | ✅ |

**Frontend Features:**
- New page at `/custom-modules` (Administration → Custom Modules)
- Two-panel layout: Modules list (left), Records view (right)
- Field builder with drag-and-drop style UI
- Dynamic form generation based on module fields
- Record detail dialog with all field values

---

### Inventory Enhanced Module (Feb 17, 2026) ✅ COMPLETE - NEW

**Advanced Inventory Management with Variants, Bundles, Shipments, Returns:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Warehouses** | `/api/inventory-enhanced/warehouses` | ✅ CRUD + Stock view | ✅ |
| **Item Variants** | `/api/inventory-enhanced/variants` | ✅ Size/color variations | ✅ |
| **Bundles/Kits** | `/api/inventory-enhanced/bundles` | ✅ Composite items | ✅ |
| **Bundle Assembly** | `/api/inventory-enhanced/bundles/{id}/assemble` | ✅ Consume components | ✅ |
| **Serial Numbers** | `/api/inventory-enhanced/serial-batches` | ✅ Individual tracking | ✅ |
| **Batch/Lot Tracking** | `/api/inventory-enhanced/serial-batches` | ✅ Group tracking | ✅ |
| **Shipments** | `/api/inventory-enhanced/shipments` | ✅ From Sales Orders | ✅ |
| **Shipment Status** | `ship`, `deliver` actions | ✅ Packed→Shipped→Delivered | ✅ |
| **Returns** | `/api/inventory-enhanced/returns` | ✅ Return from shipment | ✅ |
| **Stock Adjustments** | `/api/inventory-enhanced/adjustments` | ✅ Add/Subtract/Set | ✅ |
| **Stock Summary Report** | `/api/inventory-enhanced/reports/stock-summary` | ✅ Value by item | ✅ |
| **Low Stock Report** | `/api/inventory-enhanced/reports/low-stock` | ✅ Below reorder level | ✅ |
| **Valuation Report** | `/api/inventory-enhanced/reports/valuation` | ✅ By item type | ✅ |
| **Movement Report** | `/api/inventory-enhanced/reports/movement` | ✅ Stock history | ✅ |

**Frontend Features:**
- New page at `/inventory-enhanced` (Inventory Advanced in Catalog section)
- Summary cards: Items, Variants, Bundles, Warehouses, Stock Value, Low Stock
- Tabs: Overview, Warehouses, Variants, Bundles, Serial/Batch, Shipments, Returns
- Overview: Low Stock Alerts, Pending Shipments, Pending Returns
- Create dialogs for: Warehouse, Variant, Bundle, Serial/Batch
- Stock Adjustment dialog: Item, Warehouse, Add/Subtract/Set, Reason
- Warehouse detail with stock items table
- Bundle detail with components and max assemblable count
- Assemble bundle button (consumes component stock)
- Shipment actions: Ship, Deliver
- Return actions: Process

---

### Customer Portal Module (Feb 17, 2026) ✅ COMPLETE - NEW

**Self-Service Portal for Customers:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Portal Login** | `/api/customer-portal/login` | ✅ Token-based login with session | ✅ |
| **Dashboard** | `/api/customer-portal/dashboard` | ✅ Summary cards, recent invoices | ✅ |
| **View Invoices** | `/api/customer-portal/invoices` | ✅ List + detail view | ✅ |
| **View Estimates** | `/api/customer-portal/estimates` | ✅ List + detail view | ✅ |
| **Accept/Decline Estimate** | `/api/customer-portal/estimates/{id}/accept|decline` | ✅ Customer actions | ✅ |
| **Payment History** | `/api/customer-portal/payments` | ✅ All payments list | ✅ |
| **Account Statement** | `/api/customer-portal/statement` | ✅ Invoices + payments summary | ✅ |
| **Profile** | `/api/customer-portal/profile` | ✅ Contact details + addresses | ✅ |
| **Session Management** | `/api/customer-portal/session|logout` | ✅ 24-hour sessions | ✅ |

**Frontend Features:**
- Beautiful dark-themed login page at `/customer-portal`
- Token-based authentication (token sent via portal invite email)
- Dashboard with summary cards (Total Invoiced, Paid, Outstanding, Overdue)
- Tabs: Dashboard, Invoices, Estimates, Payments, Statement
- Invoice and estimate detail dialogs with line items
- Accept/Decline buttons for pending estimates
- Account statement with transaction history

---

### Advanced Reports with Charts (Feb 17, 2026) ✅ COMPLETE - NEW

**Visual Analytics Dashboard:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Dashboard Summary** | `/api/reports-advanced/dashboard-summary` | ✅ KPI cards | ✅ |
| **Monthly Revenue** | `/api/reports-advanced/revenue/monthly` | ✅ Bar chart | ✅ |
| **Quarterly Revenue** | `/api/reports-advanced/revenue/quarterly` | ✅ By quarter | ✅ |
| **Yearly Comparison** | `/api/reports-advanced/revenue/yearly-comparison` | ✅ Multi-year | ✅ |
| **Receivables Aging** | `/api/reports-advanced/receivables/aging` | ✅ Pie/bar chart | ✅ |
| **Receivables Trend** | `/api/reports-advanced/receivables/trend` | ✅ Line chart | ✅ |
| **Top Customers Revenue** | `/api/reports-advanced/customers/top-revenue` | ✅ Horizontal bar | ✅ |
| **Top Outstanding** | `/api/reports-advanced/customers/top-outstanding` | ✅ Horizontal bar | ✅ |
| **Customer Acquisition** | `/api/reports-advanced/customers/acquisition` | ✅ Line chart | ✅ |
| **Sales Funnel** | `/api/reports-advanced/sales/funnel` | ✅ Funnel chart | ✅ |
| **Invoice Status** | `/api/reports-advanced/invoices/status-distribution` | ✅ Donut chart | ✅ |
| **Payment Trend** | `/api/reports-advanced/payments/trend` | ✅ Line chart | ✅ |
| **Payment Modes** | `/api/reports-advanced/payments/by-mode` | ✅ Pie chart | ✅ |

**Frontend Features:**
- New page at `/reports-advanced` (Analytics in sidebar)
- KPI cards: This Month, YTD, Outstanding, Overdue (color-coded gradients)
- Tabs: Overview, Revenue, Receivables, Customers
- Pure CSS charts (no external library dependency):
  - Bar charts (vertical & horizontal)
  - Donut/Pie charts
  - Line charts with gradient fill
  - Funnel chart with conversion rates
- Interactive legends and tooltips
- Currency formatting in Indian notation (₹K)

---

### Invoices Enhanced Module (Feb 17, 2026) ✅ COMPLETE

**Comprehensive Invoice Management with Full Zoho Books Functionality:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Invoices CRUD** | `/api/invoices-enhanced/` | ✅ List with filters + Create dialog | ✅ |
| **Line Items** | Embedded in invoice | ✅ Add/Update/Delete with tax calculations | ✅ |
| **GST Calculations** | Auto-calculated | ✅ CGST/SGST or IGST based on place of supply | ✅ |
| **Summary Dashboard** | `/api/invoices-enhanced/summary` | ✅ Total, Draft, Overdue, Paid, Outstanding | ✅ |
| **Send Invoice** | `/api/invoices-enhanced/{id}/send` | ✅ **MOCKED** (logs only) | ✅ |
| **Mark Sent** | `/api/invoices-enhanced/{id}/mark-sent` | ✅ Manual status update | ✅ |
| **Record Payment** | `/api/invoices-enhanced/{id}/payments` | ✅ Partial/Full payment recording | ✅ |
| **Delete Payment** | DELETE `/api/invoices-enhanced/{id}/payments/{pid}` | ✅ Payment reversal | ✅ |
| **Clone Invoice** | `/api/invoices-enhanced/{id}/clone` | ✅ Clone as new draft | ✅ |
| **Void Invoice** | `/api/invoices-enhanced/{id}/void` | ✅ With reason tracking | ✅ |
| **Write-Off** | `/api/invoices-enhanced/{id}/write-off` | ✅ Bad debt write-off | ✅ |
| **Aging Report** | `/api/invoices-enhanced/reports/aging` | ✅ Current, 1-30, 31-60, 61-90, 90+ buckets | ✅ |
| **Customer-wise Report** | `/api/invoices-enhanced/reports/customer-wise` | ✅ Top customers by outstanding | ✅ |
| **Monthly Report** | `/api/invoices-enhanced/reports/monthly` | ✅ Monthly breakdown by year | ✅ |
| **Recurring Invoices** | `/api/invoices-enhanced/recurring` | ✅ Recurring profile management | ✅ |
| **Create from Sales Order** | `/api/invoices-enhanced/from-salesorder/{id}` | ✅ One-click conversion | ✅ |
| **Create from Estimate** | `/api/invoices-enhanced/from-estimate/{id}` | ✅ One-click conversion | ✅ |
| **Bulk Actions** | `/api/invoices-enhanced/bulk-action` | ✅ Send, Void, Mark Paid, Delete | ✅ |

**Frontend Features:**
- New page at `/invoices-enhanced` with Summary Cards and Tabs
- Summary cards: Total Invoices, Draft, Overdue, Paid, Total Invoiced, Outstanding
- Tabs: All Invoices, Overdue, Drafts
- Invoice list with search, status filter, customer filter
- Create Invoice dialog with customer select, line items, tax rates
- Line item calculations: Qty × Rate - Discount + Tax = Total
- Payment recording dialog with mode, reference, date
- Detail dialog with line items, totals breakdown, payments history
- Status-specific action buttons (Send, Mark Sent, Record Payment, Clone, Void, Delete)

**Test Results: 17/17 backend API tests passed (100%)**

---

### Unified Contacts Module v2 (Feb 17, 2026) ✅ COMPLETE - ARCHITECTURAL MERGE

**IMPORTANT: Customers Enhanced module has been merged into Contacts Enhanced v2**

This merge creates a single source of truth for all contact data (customers, vendors, or both). The `/customers-enhanced` route now redirects to `/contacts`.

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Unified Contact CRUD** | `/api/contacts-enhanced/` | ✅ Customer/Vendor/Both types | ✅ |
| **Contact Type Filter** | `?contact_type=customer|vendor` | ✅ Type badges | ✅ |
| **Summary Dashboard** | `/api/contacts-enhanced/summary` | ✅ Total, Customers, Vendors, GSTIN, Portal, Receivable, Payable | ✅ |
| **GSTIN Validation** | `/api/contacts-enhanced/validate-gstin/{gstin}` | ✅ Auto-parse state, PAN, entity | ✅ |
| **Contact Persons** | `/api/contacts-enhanced/{id}/persons` | ✅ Add/Update/Delete/Set Primary | ✅ |
| **Multiple Addresses** | `/api/contacts-enhanced/{id}/addresses` | ✅ Billing/Shipping with defaults | ✅ |
| **Portal Access** | `/api/contacts-enhanced/{id}/enable-portal` | ✅ Token gen + **MOCKED** email | ✅ |
| **Email Statement** | `/api/contacts-enhanced/{id}/email-statement` | ✅ **MOCKED** (email/PDF) | ✅ |
| **Statement Data** | `/api/contacts-enhanced/{id}/statement` | ✅ Invoices, payments, balance | ✅ |
| **Credits & Refunds** | `/api/contacts-enhanced/{id}/credits|refunds` | ✅ Add credit, create refund | ✅ |
| **Tags System** | `/api/contacts-enhanced/tags` | ✅ Create/assign/remove tags | ✅ |
| **Status Management** | `/api/contacts-enhanced/{id}/activate|deactivate` | ✅ With pending invoice check | ✅ |
| **Balance & Aging** | Calculated from invoices | ✅ Current, 1-30, 31-60, 61-90, 90+ days | ✅ |
| **Transaction History** | `/api/contacts-enhanced/{id}/transactions` | ✅ Estimates/SO/Invoices/Bills/Payments | ✅ |
| **Bulk Operations** | `/api/contacts-enhanced/bulk-action` | ✅ Activate/deactivate/delete/tags | ✅ |
| **Reports** | `/api/contacts-enhanced/reports/` | ✅ By segment, top customers, top vendors, aging, new contacts | ✅ |
| **Quick Actions** | `/api/contacts-enhanced/{id}/quick-estimate|invoice|bill` | ✅ Redirect with contact pre-filled | ✅ |
| **Data Quality Check** | `/api/contacts-enhanced/check-sync` | ✅ Audit with suggestions | ✅ |

**Deprecated Routes:**
- `/api/customers-enhanced/` → Use `/api/contacts-enhanced/?contact_type=customer`
- `/customers-enhanced` (frontend) → Redirects to `/contacts`

**Test Results: 18/18 backend API tests passed (100%)**

---

### Sales Orders Module (Feb 17, 2026) ✅ COMPLETE

**Post-Estimate Order Confirmation with Inventory Reservation and Fulfillment:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Sales Orders CRUD** | `/api/sales-orders-enhanced/` | ✅ List with filters + Create form | ✅ |
| **Line Items** | `/api/sales-orders-enhanced/{id}/line-items` | ✅ Add/Update/Delete | ✅ |
| **Status Workflow** | `/api/sales-orders-enhanced/{id}/status` | ✅ Draft→Confirmed→Open→Fulfilled→Closed | ✅ |
| **Confirm Order** | `/api/sales-orders-enhanced/{id}/confirm` | ✅ Reserves stock | ✅ |
| **Void Order** | `/api/sales-orders-enhanced/{id}/void` | ✅ Releases reserved stock | ✅ |
| **Create Fulfillment** | `/api/sales-orders-enhanced/{id}/fulfill` | ✅ Partial/full shipment | ✅ |
| **Convert to Invoice** | `/api/sales-orders-enhanced/{id}/convert-to-invoice` | ✅ One-click conversion | ✅ |
| **Clone Order** | `/api/sales-orders-enhanced/{id}/clone` | ✅ Clone button | ✅ |
| **Send Order** | `/api/sales-orders-enhanced/{id}/send` | ✅ **MOCKED** (logs only) | ✅ |
| **GST Calculations** | Auto-calculated | ✅ CGST/SGST or IGST | ✅ |
| **Fulfillment Pipeline** | `/api/sales-orders-enhanced/reports/fulfillment-summary` | ✅ Visual pipeline | ✅ |

**Frontend Features:**
- New page at `/sales-orders` with Summary Cards and Fulfillment Pipeline
- Summary cards: Total Orders, Draft, Confirmed, Open, Closed, Total Value, Pending Invoice
- Fulfillment Pipeline: Unfulfilled → Partially Fulfilled → Fulfilled with values and rate
- Orders list with search, status filter, fulfillment filter
- Create New tab with customer search, line items, delivery method
- Detail dialog with line items (Ordered/Fulfilled/Remaining), fulfillments, history
- Status-specific action buttons (Confirm, Fulfill, Convert to Invoice, Send, Void, Clone)

**Test Results: 28/28 backend tests passed (100%)**

---

### Quick Quote Enhancement (Feb 17, 2026) ✅ COMPLETE - NEW

**UX Optimization for Contact-to-Estimate Workflow:**
- Added "Quick Quote" button on Contact detail dialog
- Click navigates to `/estimates` with customer pre-filled
- URL params `customer_id` and `customer_name` auto-populate create form
- Streamlines sales workflow for repeat customers

---

### Estimates/Quotes Module (Feb 17, 2026) ✅ COMPLETE

**Full Sales Cycle Entry Point with GST Calculations and Workflow:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Estimates CRUD** | `/api/estimates-enhanced/` | ✅ List with filters + Create form | ✅ |
| **Line Items** | `/api/estimates-enhanced/{id}/line-items` | ✅ Add/Update/Delete | ✅ |
| **Status Workflow** | `/api/estimates-enhanced/{id}/status` | ✅ Draft→Sent→Accepted/Declined→Converted | ✅ |
| **Send Estimate** | `/api/estimates-enhanced/{id}/send` | ✅ **MOCKED** (logs only) | ✅ |
| **Mark Accepted/Declined** | `/api/estimates-enhanced/{id}/mark-accepted|declined` | ✅ Action buttons | ✅ |
| **Convert to Invoice** | `/api/estimates-enhanced/{id}/convert-to-invoice` | ✅ One-click conversion | ✅ |
| **Convert to Sales Order** | `/api/estimates-enhanced/{id}/convert-to-sales-order` | ✅ One-click conversion | ✅ |
| **Clone Estimate** | `/api/estimates-enhanced/{id}/clone` | ✅ Clone button | ✅ |
| **GST Calculations** | Auto-calculated | ✅ CGST/SGST (intra-state) or IGST (inter-state) | ✅ |
| **Summary Statistics** | `/api/estimates-enhanced/summary` | ✅ Summary cards | ✅ |
| **Conversion Funnel** | `/api/estimates-enhanced/reports/conversion-funnel` | ✅ Visual funnel | ✅ |
| **Reports** | `/api/estimates-enhanced/reports/by-status|by-customer` | ✅ Analytics | ✅ |

**Frontend Features:**
- New page at `/estimates` with Summary Cards and Conversion Funnel
- Summary cards: Total, Draft, Sent, Accepted, Expired, Converted, Total Value
- Conversion Funnel visualization: Created → Sent → Accepted → Converted with percentages
- Estimates list with search, status filter, and action buttons (View, Clone)
- Create New tab with customer search, date pickers, line items management
- Line item calculations: Qty × Rate - Discount + Tax = Total
- Document-level discount (percent/amount), shipping charge, adjustment
- Detail dialog with line items table, totals breakdown, history, and status-specific action buttons

**Test Results: 35/35 backend tests passed (100%)**

---

### Contact Integration Module (Feb 17, 2026) ✅ COMPLETE

**Links Enhanced Contacts to Existing Transactions:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Unified Contact Search** | `/api/contact-integration/contacts/search` | ✅ Searches enhanced + legacy | ✅ |
| **Transaction-Ready Contact** | `/api/contact-integration/contacts/{id}/for-transaction` | ✅ With addresses | ✅ |
| **Transaction History** | `/api/contact-integration/contacts/{id}/transactions` | ✅ In contact detail dialog | ✅ |
| **Balance Summary** | `/api/contact-integration/contacts/{id}/balance-summary` | ✅ Receivable/Payable breakdown | ✅ |
| **Top Customers Report** | `/api/contact-integration/reports/customers-by-revenue` | ✅ Revenue ranking | ✅ |
| **Top Vendors Report** | `/api/contact-integration/reports/vendors-by-expense` | ✅ Expense ranking | ✅ |
| **Receivables Aging** | `/api/contact-integration/reports/receivables-aging` | ✅ By customer (49 with ₹50L) | ✅ |
| **Payables Aging** | `/api/contact-integration/reports/payables-aging` | ✅ By vendor | ✅ |
| **Migration Tools** | `/api/contact-integration/migrate/contacts-to-enhanced` | ✅ Dry-run (346 contacts) | ✅ |

**Test Results: 23/23 backend tests passed (100%)**

---

### Enhanced Contacts Module (Feb 17, 2026) ✅ COMPLETE

**Comprehensive Contact Management System (Replaces Customers/Vendors):**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Contact Tags** | `/api/contacts-enhanced/tags` | ✅ CRUD with color picker | ✅ |
| **Contacts** | `/api/contacts-enhanced/` | ✅ Customer/Vendor/Both types | ✅ |
| **Contact Persons** | `/api/contacts-enhanced/{id}/persons` | ✅ Multiple + Primary marking | ✅ |
| **Addresses** | `/api/contacts-enhanced/{id}/addresses` | ✅ Billing/Shipping + Defaults | ✅ |
| **GSTIN Validation** | `/api/contacts-enhanced/validate-gstin/{gstin}` | ✅ Auto-detect state/PAN | ✅ |
| **Portal Access** | `/api/contacts-enhanced/{id}/enable-portal` | ✅ Token generation | ✅ |
| **Email Statements** | `/api/contacts-enhanced/{id}/email-statement` | ✅ **MOCKED** (logs only) | ✅ |
| **Activate/Deactivate** | `/api/contacts-enhanced/{id}/activate|deactivate` | ✅ Status toggle | ✅ |

**Frontend Features:**
- New page at `/contacts` with Contacts and Tags tabs
- Summary cards: Total Contacts, Customers, Vendors, With GSTIN, Receivable, Payable
- Contact detail dialog with persons, addresses, balance, transaction history
- GSTIN auto-validation with state/PAN extraction
- Action buttons: Enable Portal, Email Statement, Deactivate, Delete

**Test Results: 37/37 backend tests passed (100%)**

---

### Enhanced Items/Inventory Management Module (Feb 17, 2026) ✅ COMPLETE

**Comprehensive Inventory Management System:**

| Feature | Backend API | Frontend UI | Status |
|---------|-------------|-------------|--------|
| **Item Groups** | `/api/items-enhanced/groups` | ✅ CRUD + hierarchy | ✅ |
| **Warehouses** | `/api/items-enhanced/warehouses` | ✅ Multi-warehouse + Primary | ✅ |
| **Price Lists** | `/api/items-enhanced/price-lists` | ✅ Discount/Markup support | ✅ |
| **Inventory Items** | `/api/items-enhanced/` | ✅ Full CRUD + stock tracking | ✅ |
| **Stock Adjustments** | `/api/items-enhanced/adjustments` | ✅ Add/Subtract with reasons | ✅ |
| **Low Stock Alerts** | `/api/items-enhanced/low-stock` | ✅ Reorder level tracking | ✅ |
| **Stock Summary** | `/api/items-enhanced/reports/stock-summary` | ✅ Total value calculation | ✅ |
| **Inventory Valuation** | `/api/items-enhanced/reports/valuation` | ✅ Purchase/Sales value | ✅ |

**Frontend Features:**
- New page at `/inventory-management` with 5 tabs
- Summary cards: Total Items, Groups, Warehouses, Price Lists, Low Stock, Stock Value
- Low Stock Alerts section with shortage indicators
- Create/Edit/Delete dialogs for all entity types

**Test Results: 19/19 backend tests passed (100%)**

---

### GST Compliance Module (Feb 17, 2026) ✅ COMPLETE

**Full Indian GST Compliance System:**

| Feature | Backend API | Frontend UI | PDF Export | Excel Export |
|---------|-------------|-------------|------------|--------------|
| **GSTR-1 (Outward Supplies)** | `/api/gst/gstr1` | ✅ B2B, B2C Large, B2C Small | ✅ | ✅ |
| **GSTR-3B (Summary Return)** | `/api/gst/gstr3b` | ✅ Output Tax, ITC, Net Payable | ✅ | ✅ |
| **HSN Summary** | `/api/gst/hsn-summary` | ✅ HSN-wise breakdown | - | ✅ |
| **GSTIN Validation** | `/api/gst/validate-gstin` | ✅ Dialog with validation | - | - |
| **GST Calculation** | `/api/gst/calculate` | Auto-calculate | - | - |
| **Organization Settings** | `/api/gst/organization-settings` | ✅ Settings dialog | - | - |

**Test Results: 20/20 backend tests passed (100%)**

---

### Frontend UI for Backend Features (Feb 17, 2026) ✅ COMPLETE

**5 New Frontend Pages for Existing Backend APIs:**

| Page | Route | Backend API | Status |
|------|-------|-------------|--------|
| **Recurring Expenses** | `/recurring-expenses` | `/zoho/recurring-expenses` | ✅ Full CRUD + Generate Due |
| **Project Tasks** | `/project-tasks` | `/zoho/projects/{id}/tasks` | ✅ Full CRUD with progress tracking |
| **Opening Balances** | `/opening-balances` | `/zoho/opening-balances` | ✅ 3 tabs (Customers, Vendors, Accounts) |
| **Exchange Rates** | `/exchange-rates` | `/zoho/settings/exchange-rates` | ✅ Multi-currency support |
| **Activity Logs** | `/activity-logs` | `/zoho/activity-logs` | ✅ Audit trail with filters |

**Test Results: 100% frontend tests passed**

---

### On-Demand Zoho Sync (Feb 17, 2026) ✅ COMPLETE - NEW

**Live Zoho Books Integration Page:**

| Feature | Description |
|---------|-------------|
| **Test Connection** | Validates Zoho API credentials and shows Organization ID |
| **Full Sync** | One-click sync of ALL modules with progress tracking |
| **Individual Module Sync** | 11 separate module buttons for selective sync |
| **Sync History** | Table showing all past sync activities with status |

**Supported Modules:**
- Contacts (Customers & Vendors)
- Items (Products & Services)
- Invoices, Bills, Estimates, Expenses
- Payments (Customer & Vendor)
- Purchase Orders, Sales Orders
- Credit Notes, Bank Accounts

**Connection Status:** ✅ Connected to Zoho Books (Org ID: REDACTED_ORG_ID)

---

### Financial Reports with PDF/Excel Export (Feb 17, 2026) ✅ COMPLETE

**Comprehensive Financial Reporting System:**

| Report | Backend API | Frontend UI | PDF Export | Excel Export |
|--------|-------------|-------------|------------|--------------|
| **Profit & Loss** | `/api/reports/profit-loss` | ✅ Summary cards + detailed table | ✅ WeasyPrint | ✅ openpyxl |
| **Balance Sheet** | `/api/reports/balance-sheet` | ✅ Assets/Liabilities/Equity cards | ✅ WeasyPrint | ✅ openpyxl |
| **AR Aging** | `/api/reports/ar-aging` | ✅ Aging buckets + invoice table | ✅ WeasyPrint | ✅ openpyxl |
| **AP Aging** | `/api/reports/ap-aging` | ✅ Aging buckets + bill table | ✅ WeasyPrint | ✅ openpyxl |
| **Sales by Customer** | `/api/reports/sales-by-customer` | ✅ Customer ranking table | ✅ WeasyPrint | ✅ openpyxl |

**Key Features:**
- Date range filters for period-based reports (P&L, Sales)
- Point-in-time filters for snapshot reports (Balance Sheet, Aging)
- Professional PDF output with company branding and styling
- Excel export with formatted headers, currency formatting, and totals
- All reports built from real Zoho Books data (14,000+ records)

**Test Results: 16/16 backend tests passed (100%)**

---

### Extended Zoho Books Features (Feb 16, 2026) ✅ COMPLETE

**All Missing Zoho Books Features Now Implemented:**

| Feature | Frontend Page | Backend API | Status |
|---------|---------------|-------------|--------|
| **Items Management** | `/items` | `/api/zoho/items` (CRUD), `/api/zoho/items/bulk-import`, `/api/zoho/items/export`, `/api/zoho/items/import-template` | ✅ |
| **Price Lists** | `/price-lists` | `/api/zoho/price-lists`, add/remove items | ✅ |
| **Inventory Adjustments** | `/inventory-adjustments` | `/api/zoho/inventory-adjustments` | ✅ |
| **Projects & Time Tracking** | `/projects` | `/api/zoho/projects`, `/api/zoho/time-entries` | ✅ |
| **Delivery Challans** | `/delivery-challans` | `/api/zoho/delivery-challans`, convert-to-invoice | ✅ |
| **Recurring Invoices** | `/recurring-transactions` | `/api/zoho/recurring-invoices`, stop/resume | ✅ |
| **Retainer Invoices** | (via API) | `/api/zoho/retainer-invoices`, apply to invoice | ✅ |
| **Taxes & Tax Groups** | `/taxes` | `/api/zoho/taxes`, `/api/zoho/tax-groups` | ✅ |
| **Chart of Accounts** | `/chart-of-accounts` | `/api/zoho/chartofaccounts` | ✅ |
| **Journal Entries** | `/journal-entries` | `/api/zoho/journals` (debit/credit validation) | ✅ |
| **Vendor Credits** | `/vendor-credits` | `/api/zoho/vendorcredits`, apply to bills | ✅ |
| **Documents/Attachments** | (via API) | `/api/zoho/documents` | ✅ |
| **Payment Reminders** | (via API) | `/api/zoho/payment-reminders/templates`, /send | ✅ |
| **Organization Settings** | `/settings` | `/api/zoho/settings/organization` | ✅ |
| **Number Series** | (via API) | `/api/zoho/settings/number-series` | ✅ |

**Test Results: 35+ API endpoints tested (100%)**

**New Backend Features Added (Feb 16, 2026):**
- **Recurring Expenses:** Full CRUD + auto-generation via `/recurring-expenses/generate`
- **Project Tasks:** Task management within projects
- **Opening Balances:** Set initial balances for customers, vendors, accounts
- **Payment Links:** Generate shareable payment links for invoices
- **Currency Exchange Rates:** Multi-currency support with rate management
- **Activity Logs/Audit Trail:** Track all entity changes
- **Contacts Bulk Import/Export:** CSV import/export with template

**Updated Navigation Sidebar:**
- **Catalog & Inventory:** Items, Services & Parts, Price Lists, Inventory Adjustments
- **Projects & Time:** Projects
- **Sales:** Customers, Quotes, Sales Orders, Delivery Challans, Invoices, Recurring Invoices, Credit Notes
- **Purchases:** Vendors, Purchase Orders, Bills, Vendor Credits
- **Finance:** Expenses, Banking, Chart of Accounts, Journal Entries, Reports, Accounting
- **Administration:** Taxes, Users, Data Migration

---

### Complete Zoho Books API System (Feb 16, 2026) ✅ COMPLETE

**NEW: Comprehensive Zoho-style API (`/api/zoho/`):**

A full-featured Zoho Books v3 compatible API has been implemented with 51 tested endpoints covering:

| Module | Endpoints | Key Features |
|--------|-----------|--------------|
| **Contacts** | 7 | Customer/Vendor CRUD, Active/Inactive status, Portal access |
| **Contact Persons** | 4 | Multiple contacts per company, Primary marking |
| **Items** | 6 | Services & Goods, Stock tracking, Tax configuration |
| **Estimates** | 8 | Full lifecycle, Convert to Invoice/Sales Order |
| **Invoices** | 8 | Payment tracking, Void, Write-off, Balance management |
| **Sales Orders** | 7 | Confirm, Convert to Invoice, Status tracking |
| **Purchase Orders** | 7 | Issue, Convert to Bill, Delivery tracking |
| **Bills** | 6 | Vendor invoices, Payment tracking, Void |
| **Credit Notes** | 5 | Apply to invoices, Refund processing |
| **Vendor Credits** | 4 | Apply to bills |
| **Customer Payments** | 4 | Multi-invoice application, Payment modes |
| **Vendor Payments** | 3 | Multi-bill application |
| **Expenses** | 5 | Categories, Billable tracking, Tax |
| **Bank Accounts** | 5 | Multiple account types, Balance tracking |
| **Bank Transactions** | 4 | Categorize, Match to invoices/bills |
| **Chart of Accounts** | 5 | Asset/Liability/Equity/Income/Expense |
| **Journal Entries** | 4 | Debit/Credit validation |
| **Reports** | 6 | Dashboard, P&L, Receivables/Payables Aging, GST |

**Test Results: 51/51 tests passed (100%)**

**Key Workflows Implemented:**
1. **Sales Flow:** Contact → Item → Estimate → (Accept) → Sales Order → Invoice → Payment
2. **Purchase Flow:** Vendor → Purchase Order → (Issue) → Bill → Payment
3. **Credit Flow:** Credit Note → Apply to Invoice / Refund

---

### Frontend Pages for ERP Modules (Feb 16, 2026) ✅ COMPLETE

**New Pages Created:**
| Page | Route | Features |
|------|-------|----------|
| **Bills** | `/bills` | List vendor bills, create bill, status filters, record payments |
| **Credit Notes** | `/credit-notes` | Create credit notes, apply to invoices |
| **Banking** | `/banking` | Bank accounts list, transactions, deposits/withdrawals |
| **Reports** | `/reports` | 5-tab dashboard (Dashboard, P&L, Receivables, Payables, GST) |

**Updated Navigation:**
- Sales: Customers, Quotes, Sales Orders, Invoices, Credit Notes
- Purchases: Vendors, Purchase Orders, Bills
- Finance: Expenses, Banking, Reports, Accounting

---

### Event-Driven Notifications (Feb 16, 2026) ✅ COMPLETE

**Backend API (`/api/notifications/`):**
- Create, list, mark as read notifications
- Notification types: invoice_paid, invoice_overdue, amc_expiring, low_stock, ticket_update
- Priority levels: low, normal, high, urgent
- Scheduled checks for overdue invoices, expiring AMCs, low stock
- User notification preferences

**Frontend:**
- Notification bell icon in header with unread badge
- Popover showing notification list with icons
- Mark as read, mark all read functionality

---

### E-Invoice & Tally Export (Feb 16, 2026) ✅ COMPLETE

**Backend API (`/api/export/`):**
| Endpoint | Description |
|----------|-------------|
| `GET /einvoice/{id}` | Generate GST-compliant e-invoice JSON |
| `GET /einvoice/{id}/download` | Download e-invoice as JSON file |
| `GET /tally/invoices` | Export sales invoices as Tally XML |
| `GET /tally/bills` | Export purchase bills as Tally XML |
| `GET /tally/payments` | Export payments as Tally XML |
| `GET /tally/ledgers` | Export contacts as Tally ledgers |
| `GET /bulk/invoices?format=csv` | Bulk export invoices as CSV |
| `GET /bulk/expenses?format=csv` | Bulk export expenses as CSV |

**Test Results: 21/21 tests passed (100%)**

---

### Legacy ERP System (`/api/erp/`) ✅

**Backend API Modules:**

1. **Quotes/Estimates**
   - Create, list, view quotes
   - Convert to Sales Order or Invoice
   - Status tracking (draft, sent, accepted, declined, expired, invoiced)

2. **Sales Orders**
   - Full CRUD operations
   - Convert from Quote
   - Convert to Invoice (full or partial)
   - Status: draft, confirmed, partially_invoiced, invoiced, closed

3. **Purchase Orders**
   - Create PO for vendors
   - Convert to Bill
   - Status: draft, issued, partially_billed, billed, closed

4. **Bills (Vendor Invoices)**
   - Record vendor bills
   - Payment tracking
   - Status: open, partially_paid, paid, overdue

5. **Customer Payments**
   - Multi-mode payments (Cash, UPI, Bank Transfer, NEFT, RTGS)
   - Auto-apply to invoices
   - Bank account tracking

6. **Vendor Payments**
   - Pay vendor bills
   - Reference number tracking

7. **Expenses**
   - 23 expense categories
   - Multiple payment methods
   - Vendor tracking
   - Billable expense marking

8. **Credit Notes**
   - Issue refunds/adjustments
   - Link to invoices

9. **Journal Entries**
   - Manual accounting adjustments
   - Debit/Credit validation

10. **Inventory Adjustments**
    - Stock corrections
    - Write-offs

11. **Reports**
    - Receivables Aging (0-30, 31-60, 61-90, 90+ days)
    - Payables Aging
    - Profit & Loss Statement
    - GST Summary (GSTR-1, GSTR-3B)
    - Dashboard Summary

**Imported Data from Zoho Backup:**
| Module | Records |
|--------|---------|
| Customers | 153 |
| Vendors | 150 |
| Services | 300 |
| Parts | 700 |
| Expenses | 2,266 |
| Sales Orders | 300 |
| Purchase Orders | 50 |
| Customer Payments | 1,000 |
| Quotes | 300 |

**Frontend Pages:**
- `/quotes` - Quotes/Estimates management
- `/sales` - Sales Orders
- `/purchases` - Purchase Orders
- `/invoices` - Invoice management with GST
- `/expenses` - Expense tracking with categories
- `/customers` - Customer management
- `/inventory` - Services & Parts

### Login Page Redesign (Feb 16, 2026) ✅

- Clean white background (removed dark theme)
- Animated 2W, 3W, 4W vehicle icons with timed highlighting
- "Your Onsite EV Resolution Partner" tagline
- Battwheels logo in top-right corner
- Professional form with tabs (Login/Register)

### Customer Portal (Feb 16, 2026) ✅

**Features:**
- **Role-based access control** - Same login, JWT redirect by role (customer→/customer, admin→/dashboard)
- **Customer Dashboard** - Vehicle count, active services, pending payments, AMC status
- **My Vehicles** - Vehicle cards with service history, AMC status, battery info
- **Service History** - Ticket timeline view with status badges and detail dialog
- **Invoices** - View and download invoices with payment status
- **Payments Due** - Outstanding balance tracking (online payment P1)
- **AMC Plans** - Active subscriptions with usage counters, available plans for purchase

**Security:**
- Strict RBAC enforced on all admin routes (customers cannot access /dashboard, /tickets, etc.)
- Customer portal APIs return only customer's own data

**AMC System:**
- Admin-configurable plans (Basic/Plus/Premium stored as data, not constants)
- Subscription tracking with usage counters
- Auto-expiry detection (active/expiring/expired status)
- Renewal workflow

**Demo Credentials:**
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@battwheels.in | admin123 |
| Technician | deepak@battwheelsgarages.in | tech123 |
| Customer | customer@demo.com | customer123 |

### Complete Event-Driven Architecture (Feb 16, 2026) ✅

All major modules migrated to event-driven architecture with thin routes and service layers.

**Architecture Pattern:**
```
Route (thin) → Service (business logic + emit event) → Dispatcher → Handlers → Side effects
```

### Modules Migrated

| Module | Routes | Service | Tests | Status |
|--------|--------|---------|-------|--------|
| **Tickets** | `/routes/tickets.py` (380 lines) | `/services/ticket_service.py` (760 lines) | 25/25 ✅ | Complete |
| **EFI** | `/routes/failure_intelligence.py` (700 lines) | `/services/failure_intelligence_service.py` (980 lines) | 43/43 ✅ | Complete |
| **Inventory** | `/routes/inventory.py` (150 lines) | `/services/inventory_service.py` (220 lines) | 10/10 ✅ | Complete |
| **HR** | `/routes/hr.py` (350 lines) | `/services/hr_service.py` (400 lines) | 23/23 ✅ | Complete |

**Total Tests: 101/101 passed (100%)**

### Production Search System (Feb 16, 2026) ✅

**5-Stage AI Matching Pipeline:**
1. **Signature Match** (Stage 1) - Hash-based exact match, 0.95 score, fastest
2. **Subsystem + Vehicle Filter** (Stage 2) - Filters by subsystem/vehicle, 0.85 max score
3. **Vector Semantic Search** (Stage 3) - OpenAI embeddings (requires OPENAI_API_KEY)
4. **Hybrid Text+BM25 Search** (Stage 4) - Text search with BM25 scoring
5. **Keyword Fallback** (Stage 5) - Simple keyword matching, 0.5 max score

**Search Features:**
- BM25 probabilistic ranking
- EV-specific synonym expansion (battery→bms,cell,pack,soc,voltage,charge etc.)
- Fuzzy matching with Levenshtein distance
- Error code matching boost
- Vehicle make/model matching boost
- Query tokenization and stopword removal

### Event System

| Event | Source | Handlers |
|-------|--------|----------|
| `ticket.created` | Ticket creation | AI matching, notification |
| `ticket.closed` | Ticket closure | Confidence engine, notification |
| `ticket.status_changed` | Status update | Notification |
| `failure_card.created` | Card creation | Notification |
| `failure_card.approved` | Card approval | Confidence boost, notification |
| `failure_card.used` | Card usage | Usage tracking |
| `failure.new_detected` | Undocumented issue | Draft card creation |
| `inventory.low_stock` | Low stock | Alert notification |
| `inventory.allocated` | Allocation | Logging |
| `employee.created` | Employee creation | Logging |
| `attendance.marked` | Clock in/out | Logging |
| `leave.requested` | Leave request | Logging |
| `payroll.processed` | Payroll generation | Logging |

### HR Features (Indian Compliance)
- **Employee Management** - PF, ESI, PAN, Aadhaar
- **Attendance** - Clock in/out with late detection
- **Leave Management** - 6 leave types, balance tracking
- **Payroll** - Auto-calculate with deductions

### Inventory Features
- **Stock Management** - CRUD with reorder levels
- **Allocations** - Reserve for tickets
- **Low Stock Alerts** - Event-driven notifications

## Backend Architecture
```
/app/backend/
├── events/
│   ├── __init__.py
│   ├── event_dispatcher.py
│   ├── ticket_events.py
│   ├── failure_events.py
│   └── notification_events.py
├── models/
│   └── failure_intelligence.py
├── routes/
│   ├── tickets.py           ✅ Event-driven
│   ├── failure_intelligence.py  ✅ Event-driven
│   ├── inventory.py         ✅ Event-driven
│   ├── hr.py               ✅ Event-driven
│   └── fault_tree_import.py
├── services/
│   ├── ticket_service.py
│   ├── failure_intelligence_service.py
│   ├── embedding_service.py   ✅ NEW - Vector embeddings
│   ├── search_service.py      ✅ NEW - BM25 + hybrid search
│   ├── inventory_service.py
│   ├── hr_service.py
│   ├── invoice_service.py
│   └── notification_service.py
├── tests/
│   ├── test_tickets_module.py      (25 tests)
│   ├── test_efi_module.py          (22 tests)
│   ├── test_efi_search_embeddings.py (21 tests)
│   └── test_inventory_hr_modules.py (33 tests)
└── server.py
```

## API Endpoints Summary

### EFI `/api/efi`
- `POST /match` - AI-powered failure matching (5-stage pipeline)
- `POST /failure-cards` - Create
- `GET /failure-cards` - List with filters
- `PUT /failure-cards/{id}` - Update
- `POST /failure-cards/{id}/approve` - Approve
- `GET /embeddings/status` - Check embedding status
- `POST /embeddings/generate` - Generate embeddings (requires OPENAI_API_KEY)
- `GET /analytics/overview` - Analytics

### Tickets `/api/tickets`
- `POST /` - Create (emits TICKET_CREATED)
- `GET /` - List with filters
- `GET /{id}` - Get single
- `PUT /{id}` - Update (emits TICKET_UPDATED)
- `POST /{id}/close` - Close (emits TICKET_CLOSED)
- `POST /{id}/assign` - Assign (emits TICKET_ASSIGNED)
- `GET /{id}/matches` - Get AI suggestions
- `POST /{id}/select-card` - Select failure card

### Inventory `/api/inventory`
- `POST /` - Create
- `GET /` - List
- `PUT /{id}` - Update
- `DELETE /{id}` - Delete
- `POST /allocations` - Allocate for ticket
- `PUT /allocations/{id}/use` - Mark used
- `PUT /allocations/{id}/return` - Return

### HR `/api/hr`
- `POST /employees` - Create
- `GET /employees` - List
- `PUT /employees/{id}` - Update
- `POST /attendance/clock-in` - Clock in
- `POST /attendance/clock-out` - Clock out
- `GET /attendance/today` - Today's attendance
- `POST /leave/request` - Request leave
- `PUT /leave/{id}/approve` - Approve leave
- `GET /payroll/calculate/{id}` - Calculate payroll
- `POST /payroll/generate` - Generate batch payroll

### Customer Portal `/api/customer`
- `GET /dashboard` - Customer dashboard summary
- `GET /vehicles` - Customer's registered vehicles
- `GET /service-history` - Service ticket history
- `GET /service-history/{ticket_id}` - Service detail with timeline
- `GET /invoices` - Customer invoices
- `GET /invoices/{invoice_id}` - Invoice detail
- `GET /payments-due` - Outstanding payments
- `GET /amc` - Customer's AMC subscriptions
- `GET /amc/{subscription_id}` - AMC detail with usage
- `GET /amc-plans` - Available AMC plans
- `POST /request-callback` - Request callback
- `POST /request-appointment` - Book service appointment

### AMC Management `/api/amc` (Admin)
- `POST /plans` - Create AMC plan
- `GET /plans` - List all plans
- `PUT /plans/{plan_id}` - Update plan
- `DELETE /plans/{plan_id}` - Deactivate plan
- `POST /subscriptions` - Create subscription
- `GET /subscriptions` - List subscriptions
- `PUT /subscriptions/{id}/use-service` - Record service usage
- `PUT /subscriptions/{id}/cancel` - Cancel subscription
- `POST /subscriptions/{id}/renew` - Renew subscription
- `GET /analytics` - AMC analytics

## Prioritized Backlog

### Completed ✅
- [x] Event-Driven Architecture
- [x] Tickets Module Migration
- [x] EFI Module Migration
- [x] Inventory Module Migration
- [x] HR Module Migration
- [x] AI Matching Pipeline (5-stage)
- [x] Fault Tree Import Engine
- [x] BM25 + Hybrid Search Service
- [x] Embedding Service (structure ready)
- [x] **UI/UX Theme Overhaul (Feb 16, 2026)** - Industrial Intelligence Theme
- [x] **Modal Scrollability Fix (Feb 16, 2026)** - Fixed all DialogContent components
- [x] **Customer Portal (Feb 16, 2026)** - Full customer portal with My Vehicles, Service History, Invoices, Payments Due, AMC Plans
- [x] **AMC System (Feb 16, 2026)** - Admin-configurable plans, subscriptions, usage tracking
- [x] **Role-Based Access Control (Feb 16, 2026)** - Strict RBAC on all routes
- [x] **Extended Zoho Books Features (Feb 16, 2026)** - Projects, Delivery Challans, Recurring Invoices, Taxes, Chart of Accounts, Journal Entries, Vendor Credits, Retainer Invoices, Inventory Adjustments, Price Lists, Payment Reminders
- [x] **PDF Generation (Feb 16, 2026)** - WeasyPrint integration for professional invoice PDFs
- [x] **Razorpay Integration (Feb 16, 2026)** - Payment orders, payment links, webhooks (mock mode - add keys to enable)
- [x] **Scheduled Jobs System (Feb 16, 2026)** - Overdue invoice updates, recurring invoice/expense generation, payment reminders
- [x] **Enhanced Items Module (Feb 17, 2026)** - Complete inventory management with Item Groups, Warehouses, Price Lists, Inventory Adjustments, Stock Tracking, Low Stock Alerts
- [x] **Enhanced Contacts Module (Feb 17, 2026)** - Unified contact management replacing Customers/Vendors, with Contact Persons, Addresses, Tags, GSTIN validation, Portal Access, Email Statements
- [x] **Contact Integration Module (Feb 17, 2026)** - Links enhanced contacts to transactions, unified search, transaction history, balance summaries, receivables/payables aging reports, migration tools
- [x] **Estimates/Quotes Module (Feb 17, 2026)** - Sales cycle entry point with CRUD, line items, status workflow (Draft→Sent→Accepted/Declined→Converted), GST auto-calc (CGST/SGST/IGST), conversion to Invoice/Sales Order, conversion funnel visualization

### P0 (Completed)
- [x] **Customers Enhanced Module (Feb 17, 2026)** - Comprehensive customer management with GSTIN validation, persons, addresses, portal, statements, credits/refunds, tags, balance/aging, bulk ops
- [x] **Sales Orders Module (Feb 17, 2026)** - Order confirmation, stock reservation on confirm, fulfillment tracking, partial/full shipments, convert to invoice
- [x] **Quick Quote Enhancement (Feb 17, 2026)** - Button on Contact detail navigates to Estimates with customer pre-filled

### P0 (Next)
- [x] **Bills & Purchase Orders Enhanced Module (Feb 17, 2026)** - Full payables module with Bills CRUD, Bill Payments, PO workflow (Draft→Issued→Received→Billed), Convert PO to Bill, Aging Report, Vendor-wise Report - ✅ COMPLETE
- [x] **Inventory Enhanced Module (Feb 17, 2026)** - Variants (size/color), Bundles/Kits, Serial/Batch tracking, Warehouses, Shipments, Returns, Stock Adjustments, Reports (Stock Summary, Low Stock, Valuation, Movement) - ✅ COMPLETE
- [x] **Recurring Bills Module (Feb 17, 2026)** - Full recurring bill profiles with CRUD, stop/resume, auto-generation, vendor integration - ✅ COMPLETE
- [x] **Fixed Assets Module (Feb 17, 2026)** - Asset tracking with depreciation (straight-line), disposal, write-off, summary reports, by-type filtering - ✅ COMPLETE
- [x] **Custom Modules (Feb 17, 2026)** - Dynamic custom module builder with field types (text, number, date, dropdown, etc.), record management, search - ✅ COMPLETE
- [x] **Code Cleanup (Feb 17, 2026)** - Deleted deprecated customers_enhanced files, renamed contacts_enhanced_v2 to contacts_enhanced - ✅ COMPLETE
- [ ] **Legacy Data Migration** - Migrate 346 legacy customers/vendors into unified Contacts model
- [ ] Enable vector embeddings with OPENAI_API_KEY
- [ ] Configure Razorpay with production keys (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
- [ ] Customer notifications (ticket status, invoice, AMC expiry alerts)

### P1 (Future)
- [ ] **Real Email Integration** - Un-mock email sending for portal invites, statements, and quotes using SendGrid/Resend
- [ ] Elasticsearch for production-scale search
- [ ] Cron job setup for automated scheduler execution
- [ ] On-demand Sync button to pull latest data from Zoho Books

### P2 (Backlog)
- [ ] **Activate Razorpay Integration** - Enable live payment gateway with user's production keys
- [ ] **Full Customer Portal Functionality** - Expand token structure into full self-service portal
- [ ] **Advanced Reporting** - Enhanced contact-centric reports
- [ ] **Deprecate Old Routes** - Remove legacy routes and old customers/vendors pages
- [ ] Kubernetes migration with HPA
- [ ] E-invoicing government portal integration
- [ ] Apply Logo to Favicon

## UI/UX Design System (Feb 16-17, 2026)

### Unified Component System (Feb 17, 2026) ✅ COMPLETE
**Created a unified StatCard component system replacing all ad-hoc KPI card implementations.**

**New Components Created:**
| Component | Location | Purpose |
|-----------|----------|---------|
| `StatCard` | `/components/ui/stat-card.jsx` | Basic stat card with variants |
| `MetricCard` | `/components/ui/stat-card.jsx` | Dashboard-style larger metric display |
| `GradientStatCard` | `/components/ui/stat-card.jsx` | Gradient background for analytics |
| `StatCardGrid` | `/components/ui/stat-card.jsx` | Responsive grid layout container |
| `MiniStatCard` | `/components/ui/stat-card.jsx` | Compact stat for tight spaces |
| `formatCurrencyCompact` | `/components/ui/stat-card.jsx` | Indian currency abbreviation (L/Cr) |
| `ResponsiveTable` | `/components/ui/data-display.jsx` | Mobile-friendly table wrapper |
| `TableSkeleton` | `/components/ui/data-display.jsx` | Loading skeleton for tables |
| `EmptyState` | `/components/ui/data-display.jsx` | Illustrative empty state component |
| `PageSkeleton` | `/components/ui/data-display.jsx` | Full page loading skeleton |

**Variant Support:** default, success, warning, danger, info, purple, teal

**Pages Updated with PageHeader & StatCard:**
- ✅ Dashboard.jsx - MetricCard components
- ✅ ContactsEnhanced.jsx - PageHeader + StatCardGrid + ResponsiveTable + EmptyState
- ✅ InvoicesEnhanced.jsx - PageHeader + StatCardGrid
- ✅ FixedAssets.jsx - PageHeader + StatCardGrid
- ✅ ReportsAdvanced.jsx - PageHeader + GradientStatCard
- ✅ ItemsEnhanced.jsx - PageHeader + StatCardGrid
- ✅ BillsEnhanced.jsx - PageHeader + StatCardGrid

**Deprecated Files Deleted:**
- `/app/backend/routes/books.py`
- `/app/backend/routes/erp.py`
- `/app/frontend/src/components/KPICard.jsx`

### KPI Card Overflow Fix (Feb 17, 2026) ✅ COMPLETE
- **New Component:** `/app/frontend/src/components/KPICard.jsx`
- **Exports:** `KPICard`, `MetricCard`, `GradientKPICard`, `formatCurrencyCompact`
- **Features:**
  - Responsive font sizing (`text-lg sm:text-xl md:text-2xl`)
  - Text truncation with `truncate` class
  - Indian numbering abbreviations (L for Lakhs, Cr for Crores)
  - Variant styling (default, success, warning, danger, info, purple)
  - Mobile-first grid layouts (`grid-cols-2 md:grid-cols-3 lg:grid-cols-6`)
- **Pages Updated:**
  - Dashboard.jsx - Uses `MetricCard` component
  - ContactsEnhanced.jsx - Uses `KPICard` component  
  - InvoicesEnhanced.jsx - Uses `KPICard` component
  - FixedAssets.jsx - Uses `KPICard` component
  - ReportsAdvanced.jsx - Uses `GradientKPICard` component
- **Currency Formatting:**
  - Values < ₹1L: Full format (e.g., ₹5,580)
  - Values ≥ ₹1L: Lakh format (e.g., ₹29.3L)
  - Values ≥ ₹1Cr: Crore format (e.g., ₹1.5Cr)

### Login Page Redesign (Feb 16, 2026) ✅
- Simplified from cluttered 6-card layout to clean 3-feature design
- Logo positioned in top-left of hero panel
- Removed pipeline icons and excess benefit cards
- Clean vertical feature list with icons
- Polished form with improved spacing

### Theme: Light Professional (Current)
- **Style**: Clean, Modern SaaS
- **Mode**: Light Theme

### Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| White | #FFFFFF | Main background, cards |
| Gray 50 | #F9FAFB | Page background |
| Dark Green | #0B462F | Brand primary, sidebar title, buttons |
| Green 600 | #2F8F5C | Accent, active states |
| Gray 200 | #E5E7EB | Borders |
| Gray 600 | #4B5563 | Secondary text |
| Gray 900 | #111827 | Primary text |

### Components
- **Border Radius**: 0.375rem (rounded-lg)
- **Cards**: White with gray-200 borders, shadow-sm
- **Buttons**: Dark green (#0B462F) with white text
- **Active States**: Green background tint with dark green text
- **Sidebar**: White background, gray borders

- [ ] Knowledge Graph visualization

## Test Results
- **Tickets**: 25/25 (100%)
- **EFI Core**: 22/22 (100%)
- **EFI Search/Embeddings**: 21/21 (100%)
- **Inventory**: 10/10 (100%)
- **HR**: 23/23 (100%)
- **Total**: 101/101 (100%)

## 3rd Party Integrations
- **Emergent LLM Key** - AI chat features (does NOT support embeddings)
- **OpenAI API Key** - Required for vector embeddings (OPENAI_API_KEY env var)
- **Emergent Google Auth** - Social login
- **Resend** - Email (requires API key)
- **Twilio** - WhatsApp (requires API key)

## Test Credentials
- **Email:** `admin@battwheels.in`
- **Password:** `admin123`

## Key Technical Notes
1. **Embeddings require OPENAI_API_KEY** - Emergent LLM key only supports chat completions, not embeddings
2. **Search fallback** - When embeddings disabled, system uses keyword/BM25 search (Stage 4-5)
3. **Processing time** - AI matching averages 2-10ms per query
