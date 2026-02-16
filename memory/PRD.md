# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

**Core Principle:** EFI is about reasoning, not just documentation.

## What's Been Implemented

### Event-Driven Architecture (Feb 16, 2026) ✅ COMPLETE

**P0 Backend Refactoring completed for intelligence-critical modules.**

Event System Architecture:
```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Route  │ --> │  Dispatcher │ --> │   Handlers   │ --> │ Services │
│  (thin) │     │  (central)  │     │ (async)      │     │ (DB/etc) │
└─────────┘     └─────────────┘     └──────────────┘     └──────────┘
```

#### Tickets Module ✅
- **Routes**: `/app/backend/routes/tickets.py` - Thin controllers (~380 lines)
- **Services**: `/app/backend/services/ticket_service.py` - Business logic (~760 lines)
- **Events Emitted**:
  - `TICKET_CREATED` → AI matching → populates `suggested_failure_cards`
  - `TICKET_UPDATED` → Logging
  - `TICKET_STATUS_CHANGED` → Notifications
  - `TICKET_ASSIGNED` → Notifications
  - `TICKET_CLOSED` → Confidence engine → updates failure card metrics
  - `NEW_FAILURE_DETECTED` → Auto-creates draft failure card
- **Tests**: 25/25 passed

#### EFI Module ✅
- **Routes**: `/app/backend/routes/failure_intelligence.py` - Thin controllers (~640 lines)
- **Services**: `/app/backend/services/failure_intelligence_service.py` - Business logic (~900 lines)
- **Events Emitted**:
  - `FAILURE_CARD_CREATED` → Logging, notifications
  - `FAILURE_CARD_UPDATED` → Version tracking
  - `FAILURE_CARD_APPROVED` → Confidence boost, network distribution
  - `FAILURE_CARD_DEPRECATED` → Archival
  - `FAILURE_CARD_USED` → Usage tracking, confidence updates
  - `MATCH_COMPLETED` → Analytics
- **Tests**: 22/22 passed

### EFI Master Fault Tree Import Engine ✅
- 251 rows parsed from Excel
- 63 new failure cards created
- 4 existing cards updated

### AI Matching Pipeline (4-Stage) ✅
1. **Stage 1: Signature Match** - Fastest, 0.95 score, < 5ms
2. **Stage 2: Subsystem + Vehicle** - Context-aware, 0.85 max
3. **Stage 3: Semantic Similarity** - Keyword overlap, 0.7 max
4. **Stage 4: Keyword Fallback** - Text search, 0.5 max
- **Average processing time**: ~4ms

### Backend Architecture
```
/app/backend/
├── events/
│   ├── __init__.py              # init_event_system()
│   ├── event_dispatcher.py      # Central dispatcher (490 lines)
│   ├── ticket_events.py         # AI matching, confidence handlers
│   ├── failure_events.py        # Card lifecycle handlers
│   └── notification_events.py   # Notification triggers
├── models/
│   └── failure_intelligence.py  # EFI data models (900+ lines)
├── routes/
│   ├── tickets.py               # Event-driven (380 lines)
│   ├── failure_intelligence.py  # Event-driven (640 lines)
│   └── fault_tree_import.py     # Import API
├── services/
│   ├── ticket_service.py        # Ticket business logic (760 lines)
│   ├── failure_intelligence_service.py  # EFI logic (900 lines)
│   ├── event_processor.py       # Pattern detection
│   ├── fault_tree_import.py     # Import engine (800 lines)
│   ├── invoice_service.py       # PDF generation (655 lines)
│   └── notification_service.py  # Email/WhatsApp (400 lines)
├── tests/
│   ├── test_tickets_module.py   # 25 tests
│   └── test_efi_module.py       # 22 tests
└── server.py                    # Main server (being modularized)
```

## Prioritized Backlog

### P0 (Immediate) ✅ COMPLETE
- [x] Event-Driven Architecture Scaffolding
- [x] Tickets Module Migration
- [x] EFI Module Migration
- [x] AI Matching Pipeline
- [x] Fault Tree Import Engine

### P1 (High Priority - Next)
- [ ] Import Module Migration (stability)
- [ ] Invoices Module Migration (event-driven PDF generation)
- [ ] Notifications Module Migration (as event subscribers)
- [ ] HR / Employees / ERP Modules (admin features)

### P2 (Medium Priority)
- [ ] GST-Compliant PDF Invoice Integration
- [ ] UI Theme Overhaul
- [ ] Mobile app for field technicians

### P3 (Future/Backlog)
- [ ] Knowledge Graph Visualization
- [ ] Enhance EFI with OpenAI embeddings
- [ ] Cross-location network sync
- [ ] Refine Frontend RBAC

## API Endpoints Summary

### Tickets (Event-Driven)
| Endpoint | Events Emitted |
|----------|----------------|
| `POST /api/tickets` | TICKET_CREATED |
| `PUT /api/tickets/{id}` | TICKET_UPDATED, TICKET_STATUS_CHANGED |
| `POST /api/tickets/{id}/close` | TICKET_CLOSED, FAILURE_CARD_USED |
| `POST /api/tickets/{id}/assign` | TICKET_ASSIGNED |

### EFI (Event-Driven)
| Endpoint | Events Emitted |
|----------|----------------|
| `POST /api/efi/failure-cards` | FAILURE_CARD_CREATED |
| `PUT /api/efi/failure-cards/{id}` | FAILURE_CARD_UPDATED |
| `POST /api/efi/failure-cards/{id}/approve` | FAILURE_CARD_APPROVED |
| `POST /api/efi/match` | MATCH_COMPLETED |

### Event Handlers
| Event | Handlers |
|-------|----------|
| `ticket.created` | AI matching, notification |
| `ticket.closed` | Confidence engine, notification |
| `failure_card.approved` | Confidence boost, notification |
| `failure_card.used` | Usage tracking |
| `failure.new_detected` | Draft card creation |

## Test Results
- **Tickets Module**: 25/25 tests passed (100%)
- **EFI Module**: 22/22 tests passed (100%)
- **Total**: 47/47 tests passed (100%)

## 3rd Party Integrations
- **Emergent LLM Key** - AI features
- **Emergent-managed Google Auth** - Social login
- **Resend** - Email (requires API key)
- **Twilio** - WhatsApp (requires API key)

## Test Credentials
- **Email:** `admin@battwheels.in`
- **Password:** `admin123`
