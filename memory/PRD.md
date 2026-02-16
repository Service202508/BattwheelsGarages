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

### P0 (Next)
- [ ] Enable vector embeddings with OPENAI_API_KEY
- [ ] Frontend integration with EFI matching UI

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

### Theme: Industrial Intelligence
- **Archetype**: The Performance Pro
- **Style**: Dark Mode First, Industrial/Technical

### Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| Deep Obsidian | #050505 | Main background |
| Dark Green | #0B462F | Brand primary, headers |
| Paper Dark | #0B1210 | Cards, sidebar |
| Vibrant Green | #65D396 | Accent, CTAs, active states |
| White | #FFFFFF | Primary text |
| Gray 400 | #9CA3AF | Secondary text |
| Gray 500 | #6B7280 | Muted text |

### Typography
- **Headings**: Barlow (bold, uppercase for H1)
- **Body**: Manrope (high legibility)
- **Data/Mono**: JetBrains Mono

### Components
- **Border Radius**: Sharp (0.25rem) for industrial look
- **Cards**: bg-[#0B1210] with 1px borders
- **Buttons**: Vibrant green with glow effect
- **Active States**: Green accent with border highlight

### Design Guidelines File
- Location: `/app/design_guidelines.json`

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
