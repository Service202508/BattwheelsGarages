# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

**Core Principle:** EFI is about reasoning, not just documentation.

## What's Been Implemented

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
| **EFI** | `/routes/failure_intelligence.py` (640 lines) | `/services/failure_intelligence_service.py` (900 lines) | 22/22 ✅ | Complete |
| **Inventory** | `/routes/inventory.py` (150 lines) | `/services/inventory_service.py` (220 lines) | 10/10 ✅ | Complete |
| **HR** | `/routes/hr.py` (350 lines) | `/services/hr_service.py` (400 lines) | 23/23 ✅ | Complete |

**Total Tests: 80/80 passed (100%)**

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

### EFI Features
- **4-Stage AI Matching Pipeline** (~4ms processing)
  1. Signature match (0.95 score)
  2. Subsystem + vehicle filtering (0.85 max)
  3. Semantic similarity (0.7 max)
  4. Keyword fallback (0.5 max)
- **Confidence Engine** - Updates scores on ticket closure
- **Fault Tree Import** - Excel to failure cards
- **Knowledge Graph** - Entity relationships

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
│   ├── inventory_service.py
│   ├── hr_service.py
│   ├── invoice_service.py
│   └── notification_service.py
├── tests/
│   ├── test_tickets_module.py      (25 tests)
│   ├── test_efi_module.py          (22 tests)
│   └── test_inventory_hr_modules.py (33 tests)
└── server.py
```

## API Endpoints Summary

### Tickets `/api/tickets`
- `POST /` - Create (emits TICKET_CREATED)
- `GET /` - List with filters
- `GET /{id}` - Get single
- `PUT /{id}` - Update (emits TICKET_UPDATED)
- `POST /{id}/close` - Close (emits TICKET_CLOSED)
- `POST /{id}/assign` - Assign (emits TICKET_ASSIGNED)
- `GET /{id}/matches` - Get AI suggestions
- `POST /{id}/select-card` - Select failure card

### EFI `/api/efi`
- `POST /failure-cards` - Create
- `GET /failure-cards` - List
- `PUT /failure-cards/{id}` - Update
- `POST /failure-cards/{id}/approve` - Approve
- `POST /match` - AI matching
- `GET /analytics/overview` - Analytics

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

## Prioritized Backlog

### Completed ✅
- [x] Event-Driven Architecture
- [x] Tickets Module Migration
- [x] EFI Module Migration
- [x] Inventory Module Migration
- [x] HR Module Migration
- [x] AI Matching Pipeline
- [x] Fault Tree Import Engine

### P1 (Next)
- [ ] Event handlers for HR events
- [ ] Invoice PDF generation integration
- [ ] Frontend integration with new routes

### P2 (Future)
- [ ] UI Theme Overhaul
- [ ] Mobile app
- [ ] Knowledge Graph visualization

## Test Results
- **Tickets**: 25/25 (100%)
- **EFI**: 22/22 (100%)
- **Inventory**: 10/10 (100%)
- **HR**: 23/23 (100%)
- **Total**: 80/80 (100%)

## 3rd Party Integrations
- Emergent LLM Key - AI features
- Emergent Google Auth - Social login
- Resend - Email (requires API key)
- Twilio - WhatsApp (requires API key)

## Test Credentials
- **Email:** `admin@battwheels.in`
- **Password:** `admin123`
