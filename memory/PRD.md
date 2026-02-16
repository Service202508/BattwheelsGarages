# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

**Core Principle:** EFI is about reasoning, not just documentation.

## What's Been Implemented

### Complete Zoho Books ERP System (Feb 16, 2026) ✅ COMPLETE

**Backend API Modules (`/api/erp/`):**

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

### P0 (Next)
- [ ] Enable vector embeddings with OPENAI_API_KEY
- [ ] Online payments via Razorpay (currently view-only)
- [ ] Customer notifications (ticket status, invoice, AMC expiry alerts)

### P1 (Future)
- [ ] Elasticsearch for production-scale search
- [ ] Location Agent & Offline Mode
- [ ] Kafka for real-time sync
- [ ] Event handlers for HR events

### P2 (Backlog)
- [ ] Kubernetes migration with HPA
- [ ] Migrate remaining monolith routes (Customers, Sales)
- [ ] UI Theme Overhaul

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
