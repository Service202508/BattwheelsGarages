# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

**Core Principle:** EFI is about reasoning, not just documentation.

## What's Been Implemented

### Enhanced Items/Inventory Management Module (Feb 17, 2026) ✅ COMPLETE - NEW

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

### P0 (Next)
- [ ] Enable vector embeddings with OPENAI_API_KEY
- [ ] Configure Razorpay with production keys (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
- [ ] Customer notifications (ticket status, invoice, AMC expiry alerts)

### P1 (Future)
- [ ] Elasticsearch for production-scale search
- [ ] Email service integration (SendGrid/Resend) for actual email delivery
- [ ] Cron job setup for automated scheduler execution
- [ ] On-demand Sync button to pull latest data from Zoho Books

### P2 (Backlog)
- [ ] Kubernetes migration with HPA
- [ ] Deprecate legacy books.py and erp.py files
- [ ] E-invoicing government portal integration
- [ ] Apply Logo to Favicon

## UI/UX Design System (Feb 16, 2026)

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
