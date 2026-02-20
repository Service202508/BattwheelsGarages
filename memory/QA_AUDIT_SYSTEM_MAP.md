# Battwheels OS - QA Audit System Map
## Phase 0: Discovery & Baseline
### Generated: December 2025

---

## 1. SYSTEM OVERVIEW

### 1.1 Technology Stack
| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 18, TailwindCSS, Shadcn/UI | Hot reload enabled |
| Backend | FastAPI, Motor (async MongoDB) | Port 8001 internal |
| Database | MongoDB | Multi-tenant architecture |
| Auth | JWT + Emergent Google OAuth | Session-based + token |
| PDF | WeasyPrint + ReportLab | Invoice/estimate generation |
| AI | Gemini (via Emergent LLM Key) | Issue suggestions, diagnostics |
| Payments | Stripe (test), Razorpay (mock) | Both integrated |
| Maps | Leaflet + OpenStreetMap | Location picker |
| External Sync | Zoho Books API (India) | Live sync |

### 1.2 Multi-Tenant Architecture
- **Header-based:** `X-Organization-ID` required for most API calls
- **Data scoping:** All collections filtered by `organization_id`
- **Organization switching:** UI supports multi-org for admin users

---

## 2. MODULE INVENTORY

### 2.1 Core Business Modules

| Module | Backend Route | Frontend Page | Collection(s) | Status |
|--------|---------------|---------------|---------------|--------|
| **Tickets/Service** | `/api/tickets` | `Tickets.jsx`, `JobCard.jsx` | `tickets`, `ticket_activities` | ACTIVE |
| **Estimates** | `/api/ticket-estimates`, `/api/estimates-enhanced` | `EstimatesEnhanced.jsx`, `EstimateItemsPanel.jsx` | `ticket_estimates`, `estimates` | ACTIVE |
| **Invoices** | `/api/invoices-enhanced` | `InvoicesEnhanced.jsx` | `invoices`, `invoice_line_items`, `invoice_payments` | ACTIVE |
| **Payments Received** | `/api/payments-received` | `PaymentsReceived.jsx` | `payments_received`, `customer_credits` | ACTIVE |
| **Contacts/Customers** | `/api/contacts-enhanced` | `ContactsEnhanced.jsx` | `contacts` | ACTIVE |
| **Items/Inventory** | `/api/items-enhanced`, `/api/inventory-enhanced` | `ItemsEnhanced.jsx`, `InventoryEnhanced.jsx` | `items`, `items_enhanced`, `item_stock_locations` | ACTIVE |
| **Sales Orders** | `/api/sales-orders-enhanced` | `SalesOrdersEnhanced.jsx` | `salesorders` | ACTIVE |
| **Bills** | `/api/bills-enhanced` | `BillsEnhanced.jsx` | `bills` | ACTIVE |
| **AMC Contracts** | `/api/amc` | `AMCManagement.jsx` | `amc_contracts` | ACTIVE |

### 2.2 Portal Modules

| Portal | Backend Route | Layout | Target User |
|--------|---------------|--------|-------------|
| **Admin Portal** | Multiple routes | `Layout.jsx` | Admin/Manager |
| **Technician Portal** | `/api/technician/*` | `TechnicianLayout.jsx` | Technicians |
| **Business Customer Portal** | `/api/business/*` | `BusinessLayout.jsx` | B2B Customers |
| **Customer Portal** | `/api/customer-portal/*` | `CustomerLayout.jsx` | Individual Customers |
| **Public Ticket** | `/api/public/tickets/*` | None (public) | Anonymous |

### 2.3 Finance & Accounting

| Module | Backend Route | Frontend Page | Collection(s) |
|--------|---------------|---------------|---------------|
| **Banking** | `/api/banking` | `Banking.jsx` | `bank_accounts`, `bank_transactions` |
| **Accountant** | `/api/banking/*` | `Accountant.jsx` | `chart_of_accounts`, `journal_entries`, `reconciliations` |
| **Financial Dashboard** | `/api/dashboard/financial/*` | `Home.jsx` | Aggregated from multiple |
| **GST Reports** | `/api/gst/*` | `GSTReports.jsx` | `gst_returns` |
| **Time Tracking** | `/api/time-tracking/*` | `TimeTracking.jsx` | `time_entries` |

### 2.4 HR Modules

| Module | Backend Route | Frontend Page | Collection(s) |
|--------|---------------|---------------|---------------|
| **Employees** | `/api/employees` | `Employees.jsx` | `employees` |
| **Attendance** | `/api/hr/attendance` | `TechnicianAttendance.jsx` | `attendance` |
| **Leave Management** | `/api/hr/leave` | `TechnicianLeave.jsx` | `leave_requests`, `leave_balances` |
| **Payroll** | `/api/hr/payroll` | `TechnicianPayroll.jsx` | `payroll`, `payslips` |

### 2.5 System & Settings

| Module | Backend Route | Frontend Page | Collection(s) |
|--------|---------------|---------------|---------------|
| **Organization Settings** | `/api/org/*` | `OrganizationSettings.jsx` | `organizations`, `organization_settings` |
| **All Settings** | `/api/settings/*` | `AllSettings.jsx` | `settings`, `custom_fields`, `workflow_rules` |
| **Permissions/RBAC** | `/api/permissions/*` | `PermissionsManager.jsx` | `roles`, `permissions` |
| **Users** | `/api/users` | `Users.jsx` | `users` |
| **Data Management** | `/api/data-management/*` | `DataManagement.jsx` | Multiple |
| **Zoho Sync** | `/api/zoho/*` | `ZohoSync.jsx` | `zoho_sync_status` |

---

## 3. KEY ENTITIES & DATA MODELS

### 3.1 Ticket Entity (Central)
```
tickets {
  ticket_id: string (PK)
  organization_id: string (FK)
  customer_id: string (FK -> contacts)
  vehicle_id: string
  assigned_technician_id: string (FK -> users)
  status: enum [open, assigned, estimate_shared, estimate_approved, 
                work_in_progress, work_completed, invoiced, closed]
  priority: enum [low, medium, high, critical]
  estimated_cost: float
  actual_cost: float
  status_history: array[{status, timestamp, updated_by}]
}
```

### 3.2 Estimate Entity
```
ticket_estimates {
  estimate_id: string (PK)
  ticket_id: string (FK -> tickets) [UNIQUE per ticket]
  organization_id: string (FK)
  status: enum [draft, sent, approved, rejected, converted, void]
  subtotal: float (calculated)
  tax_total: float (calculated)
  discount_total: float (calculated)
  grand_total: float (calculated)
  version: int (optimistic concurrency)
  locked_at: datetime (null if editable)
}

ticket_estimate_line_items {
  line_item_id: string (PK)
  estimate_id: string (FK)
  type: enum [part, labour, fee]
  item_id: string (FK -> items, nullable)
  qty: float
  unit_price: float
  discount: float
  tax_rate: float
  line_total: float (calculated)
}
```

### 3.3 Invoice Entity
```
invoices {
  invoice_id: string (PK)
  invoice_number: string (auto-generated)
  organization_id: string (FK)
  customer_id: string (FK -> contacts)
  ticket_id: string (FK, nullable)
  status: enum [draft, sent, viewed, partially_paid, paid, overdue, void]
  sub_total: float
  tax_total: float
  shipping_charge: float
  adjustment: float
  grand_total: float
  balance_due: float
  amount_paid: float
}
```

### 3.4 Payment Entity
```
payments_received {
  payment_id: string (PK)
  payment_number: string (auto-generated)
  customer_id: string (FK -> contacts)
  amount: float
  payment_mode: enum [cash, cheque, bank_transfer, card, upi, online]
  allocations: array[{invoice_id, amount}]
  is_retainer: boolean
  status: enum [recorded, deposited, refunded]
}
```

### 3.5 Inventory Entity
```
items / items_enhanced {
  item_id: string (PK)
  organization_id: string (FK)
  item_type: enum [inventory, service, goods]
  sku: string
  stock_on_hand: float
  reorder_level: float
  rate: float
}

item_stock_locations {
  item_id: string (FK)
  warehouse_id: string (FK)
  available_stock: float
  reserved_stock: float
}
```

---

## 4. PRIMARY WORKFLOWS

### 4.1 Ticket Lifecycle Workflow
```
[Open] --> Assign Technician --> [Assigned]
    |                                |
    v                                v
[Estimate Created (auto)]       [Estimate Shared] --> Customer Approves --> [Estimate Approved]
                                                              |
                                                              v
                                                    [Work In Progress] --> Complete Work --> [Work Completed]
                                                                                                    |
                                                                                                    v
                                                                              Convert to Invoice --> [Invoiced]
                                                                                                           |
                                                                                                           v
                                                                                                    [Closed]
```

### 4.2 Quote-to-Invoice Workflow
```
[Create Estimate] --> Add Line Items --> [Draft]
        |                                   |
        v                                   v
   [Send to Customer] ----------------> [Sent]
                                           |
                                           v
                              Customer Approves --> [Approved]
                                                       |
                                                       v
                                              Lock Estimate --> [Locked]
                                                                   |
                                                                   v
                                                        Convert to Invoice
```

### 4.3 Payment Flow
```
[Invoice Created] --> balance_due = grand_total
        |
        v
Record Payment --> Allocate to Invoice(s)
        |
        v
Update Invoice:
  - amount_paid += allocation
  - balance_due = grand_total - amount_paid
  - status = (balance_due <= 0) ? 'paid' : 'partially_paid'
        |
        v
Update Customer Balance (receivable_balance)
```

### 4.4 Inventory Flow (Estimates)
```
[Add Part to Estimate] --> Check Stock
        |
        v (If Approved)
Reserve Inventory:
  - reserved_stock += qty
  - Track in inventory_allocations
        |
        v (If Converted to Invoice)
Consume Inventory:
  - available_stock -= qty
  - reserved_stock -= qty
  - Log to inventory_history
```

---

## 5. CROSS-MODULE DEPENDENCIES

### 5.1 Module Dependency Matrix

| Source Module | Depends On | Nature of Dependency |
|---------------|------------|---------------------|
| Tickets | Contacts, Users, Vehicles | Customer/Technician lookup |
| Estimates | Tickets, Items, Inventory | Ticket linkage, Part catalog, Stock check |
| Invoices | Estimates, Contacts, Items | Conversion source, Customer, Line items |
| Payments | Invoices, Contacts | Allocation target, Customer balance |
| Inventory | Items, Warehouses | Stock locations |
| HR (Payroll) | Employees, Attendance | Salary calculation |

### 5.2 Critical Data Flows

1. **Ticket → Estimate → Invoice**
   - Ticket creates linked estimate
   - Estimate line items become invoice line items
   - Invoice links back to ticket via `ticket_id`

2. **Invoice → Payment → Customer Balance**
   - Payment allocations reduce invoice `balance_due`
   - Overpayments create `customer_credits`
   - Customer `receivable_balance` updated

3. **Estimate → Inventory**
   - Parts on estimates reserve inventory
   - Conversion to invoice consumes inventory
   - Stock levels affect part availability display

---

## 6. CALCULATION AUDIT TARGETS

### 6.1 High-Priority Calculations (P0)

| Calculation | Location | Formula |
|-------------|----------|---------|
| **Line Item Total** | `finance_calculator.py:70-148`, `ticket_estimate_service.py:1036-1047` | `(qty * unit_price - discount) * (1 + tax_rate/100)` |
| **Invoice Grand Total** | `finance_calculator.py:175-248`, `invoices_enhanced.py:263-298` | `sum(line_totals) - invoice_discount + shipping + adjustment` |
| **Payment Allocation** | `payments_received.py:116-161` | `balance_due = grand_total - sum(allocations) - write_off` |
| **Tax Split (CGST/SGST/IGST)** | `finance_calculator.py:326-361` | CGST = SGST = tax/2 (intra-state), IGST = tax (inter-state) |

### 6.2 Medium-Priority Calculations (P1)

| Calculation | Location | Formula |
|-------------|----------|---------|
| **Aging Bucket** | `finance_calculator.py:385-440` | Days overdue: current, 1-30, 31-60, 61-90, 90+ |
| **Rounding** | `finance_calculator.py:61-66` | Round to nearest 1/5/10 rupees |
| **Inventory Stock Status** | `ticket_estimate_service.py:266-365` | in_stock/low_stock/out_of_stock based on reorder_level |
| **Customer Receivables** | `payments_received.py:163-188` | Sum of `balance_due` across invoices |

### 6.3 Lower-Priority Calculations (P2)

| Calculation | Location |
|-------------|----------|
| HR Payroll | `hr.py` |
| AMC Pricing | `amc.py` |
| Reports Aggregation | `reports_advanced.py` |

---

## 7. INTEGRATION POINTS

### 7.1 External Integrations

| Integration | Status | Module | API Key Location |
|-------------|--------|--------|------------------|
| Zoho Books | LIVE | `zoho_api.py`, `zoho_sync.py` | `backend/.env` |
| Gemini AI | ACTIVE | `public_tickets.py`, `technician_portal.py` | Emergent LLM Key |
| Stripe | TEST MODE | `stripe_webhook.py` | `backend/.env` |
| Razorpay | MOCK | `razorpay.py`, `razorpay_service.py` | - |
| Resend Email | INACTIVE | - | Needs `RESEND_API_KEY` |

### 7.2 Internal Service Dependencies

| Service | Consumers | Events Emitted |
|---------|-----------|----------------|
| `TicketService` | Routes, Portals | TICKET_CREATED, TICKET_UPDATED, TICKET_CLOSED |
| `TicketEstimateService` | Routes | Line item CRUD, Approval, Locking |
| `InventoryService` | Estimates, Invoices | INVENTORY_LOW, INVENTORY_ALLOCATED, INVENTORY_USED |
| `NotificationService` | All modules | Email/SMS (mocked) |

---

## 8. BACKGROUND JOBS & EVENTS

### 8.1 Event System
- **Dispatcher:** `events/event_dispatcher.py`
- **Event Types:** Defined in `services/event_constants.py`
- **Handlers:** `services/event_processor.py`, `events/notification_events.py`

### 8.2 Scheduled Jobs
| Job | Schedule | Module |
|-----|----------|--------|
| Overdue Invoice Check | Daily | `services/scheduler.py` |
| Zoho Sync | Configurable | `services/zoho_realtime_sync.py` |
| Recurring Invoice Creation | Daily | `routes/recurring_invoices.py` |

---

## 9. KNOWN ISSUES & RISKS

### 9.1 Documented Issues
- **WeasyPrint Dependency:** May require `libpangoft2-1.0-0` reinstallation
- **Razorpay:** Mocked, not live
- **Email:** Inactive, requires API key

### 9.2 Potential Risk Areas (To Audit)
- [ ] Concurrent estimate edits (version mismatch handling)
- [ ] Payment over-allocation (can exceed invoice total?)
- [ ] Inventory negative stock scenarios
- [ ] Tax calculation edge cases (inclusive vs exclusive)
- [ ] Multi-tenant data leakage

---

## 10. TEST INFRASTRUCTURE

### 10.1 Existing Test Files
- `/app/backend/tests/test_comprehensive_audit.py`
- `/app/backend/tests/test_ticket_estimate_integration.py`
- `/app/backend/tests/test_invoice_automation.py`
- `/app/backend/tests/test_payments_received.py`
- `/app/backend/tests/test_regression_suite.py`

### 10.2 Test Reports
- `/app/test_reports/iteration_*.json` (latest: iteration_13)

---

## 11. NEXT AUDIT PHASES

### Phase 1: Calculation & Logic Audit
1. Verify line item calculations against `finance_calculator.py`
2. Test inclusive vs exclusive tax scenarios
3. Validate CGST/SGST/IGST split logic
4. Check payment allocation edge cases
5. Verify inventory stock calculations

### Phase 2: Workflow/State Machine Audit
1. Map all ticket status transitions
2. Verify estimate status workflow
3. Test invoice status updates
4. Validate payment flow impacts

### Phase 3: Cross-Module Reconciliation
1. Invoice ↔ Payment balance consistency
2. Estimate → Invoice data transfer
3. Inventory allocation tracking
4. Customer balance accuracy

---

*Document generated as part of QA Audit Phase 0*
