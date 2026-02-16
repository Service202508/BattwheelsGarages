# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

**Core Principle:** EFI is about reasoning, not just documentation.

## What's Been Implemented

### Event-Driven Tickets Module (Feb 16, 2026) ✅ NEW

**First module migrated to event-driven architecture as part of P0 backend refactoring.**

Architecture:
- **Routes**: `/app/backend/routes/tickets.py` - Thin controller layer (377 lines)
- **Services**: `/app/backend/services/ticket_service.py` - Business logic with event emission (762 lines)
- **Events**: `/app/backend/events/ticket_events.py` - Event handlers for AI matching and confidence (429 lines)
- **Dispatcher**: `/app/backend/events/event_dispatcher.py` - Central event system (489 lines)

Event Flow:
```
Route -> Service (emit event) -> Dispatcher -> Handlers -> Side effects
```

Events Implemented:
| Event | Trigger | Handlers |
|-------|---------|----------|
| `TICKET_CREATED` | Ticket creation | AI matching (populates suggested_failure_cards) |
| `TICKET_UPDATED` | Any ticket update | Logging |
| `TICKET_STATUS_CHANGED` | Status transition | Notifications |
| `TICKET_ASSIGNED` | Technician assignment | Notifications |
| `TICKET_CLOSED` | Ticket closure | Confidence engine (updates failure card metrics) |
| `FAILURE_CARD_USED` | Card selection | Usage tracking |
| `NEW_FAILURE_DETECTED` | Undocumented issue | Auto-create draft failure card |

Ticket Lifecycle States:
- `open` → `assigned` → `in_progress` → `pending_parts` → `resolved` → `closed`
- `reopened` state for re-opened tickets

Key Features:
- **AI Matching on Creation**: TICKET_CREATED triggers 4-stage AI matching pipeline
- **Confidence Engine on Closure**: TICKET_CLOSED updates failure card confidence scores
- **Undocumented Issue Detection**: Closing without failure card triggers draft creation
- **Status History Tracking**: Full audit trail with timestamps and user attribution
- **Backward Compatibility**: Legacy routes maintained

Test Results: **25/25 tests passed (100%)**

### EFI Master Fault Tree Import Engine (Feb 16, 2026) ✅

**Complete structured data ingestion pipeline for importing EV failure intelligence from Excel files.**

Components:
- **Parsing Engine**: Reads Excel, detects sections (vehicle category + subsystem), splits multi-value fields
- **Validation Pipeline**: Required field checks, quality validation, warning/error flagging
- **Field Mapping**: Converts Excel columns to FAILURE_CARD schema with intelligent inference
- **Deduplication**: Signature hash + title similarity matching
- **Version Control**: Increments version for updates, tracks source reference
- **Batch Processing**: Progress tracking, rollback on failure

Import Results from Battwheels Master Fault Tree:
- **251 rows parsed** from Excel
- **63 new failure cards created**
- **4 existing cards updated**
- **184 duplicates skipped**
- **0 errors**

### EV Failure Intelligence Engine v2.0 (Feb 16, 2026) ✅ ENHANCED

**Core Entity: FAILURE_CARD (Central Intelligence Object)**
- `failure_id` - Unique identifier
- `title`, `description` - Human-readable info
- `failure_signature` - Symptom + condition fingerprint for fast matching
- `signature_hash` - Computed hash for fast lookup
- `diagnostic_tree` - Structured step-by-step diagnostic logic tree
- `symptoms[]` - Structured symptom tags with knowledge graph links
- `subsystem_category` - battery, motor, controller, wiring, charger, BMS, etc.
- `root_cause` - Structured root cause description
- `verification_steps[]` - Diagnostic steps with tools/safety warnings
- `resolution_steps[]` - Resolution steps with parts/tools/skill level
- `required_parts[]` - Parts needed with alternatives
- `vehicle_models[]` - Compatible vehicles (make, model, year range)
- `failure_conditions[]` - Environmental/usage conditions
- `confidence_score` - 0-1 score based on usage outcomes
- `confidence_history[]` - Track confidence changes over time
- `first_detected_at` - When this failure was first seen
- `last_used_at` - When this card was last used
- `source_type` - field_discovery | oem_input | internal_analysis | pattern_detection
- `version` - Versioned knowledge objects
- `status` - draft/pending_review/approved/deprecated

**AI Matching Pipeline v2.0 (Priority Order)**
1. **Stage 1: Failure Signature Match** - Fastest, highest confidence (< 5ms)
2. **Stage 2: Subsystem + Vehicle Filtering** - Context-aware (< 30ms)
3. **Stage 3: Semantic Similarity** - Deep understanding (< 100ms)
4. **Stage 4: Keyword Fallback** - Last resort (< 50ms)

### Backend Architecture (Feb 16, 2026) ✅
```
/app/backend/
├── events/                       # EVENT-DRIVEN ARCHITECTURE
│   ├── __init__.py              # init_event_system()
│   ├── event_dispatcher.py      # Central event system (489 lines)
│   ├── ticket_events.py         # AI matching, confidence handlers
│   ├── failure_events.py        # Failure card lifecycle handlers
│   └── notification_events.py   # Notification triggers
├── models/
│   └── failure_intelligence.py  # EFI data models (900+ lines)
├── routes/
│   ├── tickets.py               # NEW - Event-driven tickets (377 lines)
│   ├── failure_intelligence.py  # EFI API routes (1000+ lines)
│   └── fault_tree_import.py     # Import API routes
├── services/
│   ├── ticket_service.py        # NEW - Ticket business logic (762 lines)
│   ├── event_processor.py       # EFI event workflows
│   ├── fault_tree_import.py     # Import engine (800+ lines)
│   ├── invoice_service.py       # PDF generation
│   └── notification_service.py  # Email/WhatsApp
├── tests/
│   └── test_tickets_module.py   # NEW - 25 tests
└── server.py                    # Main server (being modularized)
```

### Frontend Pages
- `/fault-tree-import` - Admin import interface
- `/failure-intelligence` - EFI Dashboard
- All other ERP/HR/Operations pages

### Documentation Created
- `/app/docs/EFI_ARCHITECTURE.md` - Complete system architecture with diagrams
- `/app/docs/TECHNICAL_SPEC.md` - Technical specification

### Previous Implementations
- Complete ERP Suite (Inventory, Sales, Purchases, Accounting)
- Complaint Dashboard with KPI cards
- Employee Management with Indian compliance (PF, ESI)
- HR & Payroll module
- Invoice PDF Generation (GST compliant)
- Notification Service (Email via Resend, WhatsApp via Twilio)

## Prioritized Backlog

### P0 (Immediate) - IN PROGRESS
- [x] EFI Core Architecture Validation
- [x] Core Data Models Implementation
- [x] Event-Driven Workflows Implementation
- [x] AI Matching Pipeline (4-stage)
- [x] Master Fault Tree Import Engine
- [x] **Tickets Module Migration** ✅ COMPLETED
- [ ] **EFI Module Migration** (Failure Cards, approval flow, confidence updates)
- [ ] **Import Module Migration** (keeps ingestion stable + versioning)
- [ ] **Invoices Module Migration** (consumes events + needs stability for GST PDF)
- [ ] **Notifications Module Migration** (as event subscribers)
- [ ] HR / Employees / ERP Modules (last — not intelligence-critical)

### P1 (High Priority - Next)
- [ ] GST-Compliant PDF Invoice Integration
- [ ] Notification Workflow Integration
- [ ] UI Theme Overhaul (deferred until EFI stable)

### P2 (Medium Priority)
- [ ] EFI Dashboard UI
- [ ] Failure Card CRUD UI
- [ ] Knowledge Graph Visualization
- [ ] Technician Action Forms with Diagnostic Tree
- [ ] Mobile app for field technicians

### P3 (Future/Backlog)
- [ ] Enhance EFI with OpenAI embeddings
- [ ] Real-time updates using WebSockets
- [ ] Refine Frontend RBAC
- [ ] Cross-location network sync

## API Endpoints Summary

### Tickets Endpoints (NEW - Event-Driven)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tickets` | POST | Create ticket (emits TICKET_CREATED) |
| `/api/tickets` | GET | List with filters |
| `/api/tickets/{id}` | GET | Get single ticket |
| `/api/tickets/{id}` | PUT | Update ticket (emits TICKET_UPDATED) |
| `/api/tickets/{id}/close` | POST | Close with resolution (emits TICKET_CLOSED) |
| `/api/tickets/{id}/assign` | POST | Assign technician (emits TICKET_ASSIGNED) |
| `/api/tickets/{id}/matches` | GET | Get AI-suggested failure cards |
| `/api/tickets/{id}/select-card` | POST | Select failure card (emits FAILURE_CARD_USED) |
| `/api/tickets/stats` | GET | Dashboard statistics |

### EFI Core Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/efi/failure-cards` | POST | Create failure card |
| `/api/efi/failure-cards` | GET | List with filters |
| `/api/efi/failure-cards/{id}` | GET | Get single card |
| `/api/efi/failure-cards/{id}` | PUT | Update card |
| `/api/efi/failure-cards/{id}/approve` | POST | Approve for network |
| `/api/efi/failure-cards/{id}/confidence-history` | GET | Get confidence history |
| `/api/efi/match` | POST | AI failure matching (4-stage) |
| `/api/efi/match-ticket/{id}` | POST | Match ticket to cards |
| `/api/efi/technician-actions` | POST | Record action |
| `/api/efi/part-usage` | POST | Record part usage |
| `/api/efi/patterns` | GET | List emerging patterns |
| `/api/efi/patterns/{id}/review` | POST | Review pattern |
| `/api/efi/patterns/detect` | POST | Trigger detection job |
| `/api/efi/analytics/overview` | GET | EFI analytics |
| `/api/efi/events` | GET | List events |
| `/api/efi/events/process` | POST | Process pending events |

### Fault Tree Import Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/import/upload` | POST | Upload Excel file |
| `/api/import/upload-url` | POST | Import from URL |
| `/api/import/quick` | POST | Quick import from default file |
| `/api/import/jobs` | GET | List import jobs |
| `/api/import/jobs/{id}` | GET | Get job status |
| `/api/import/jobs/{id}/preview` | GET | Preview parsed data |
| `/api/import/jobs/{id}/execute` | POST | Execute import |
| `/api/import/jobs/{id}/results` | GET | Get import results |

## Key Database Collections
- `failure_cards` - Core knowledge objects
- `technician_actions` - Repair records with reasoning
- `part_usage` - Parts consumption with expectation tracking
- `emerging_patterns` - Detected patterns for review
- `efi_events` - Event log
- `event_log` - Central event system log
- `notifications` - Notification queue
- `symptoms` - Symptom library
- `knowledge_relations` - Graph edges

## Key Formulas
```python
# Effectiveness Score
effectiveness = (success_count / usage_count) + min(0.1, usage_count / 100)

# Confidence Update
if success:
    confidence = min(1.0, confidence + 0.01)
else:
    confidence = max(0.0, confidence - 0.02)

# Confidence Levels
LOW      = confidence < 0.4
MEDIUM   = 0.4 <= confidence < 0.7
HIGH     = 0.7 <= confidence < 0.9
VERIFIED = confidence >= 0.9
```

## 3rd Party Integrations
- **Emergent LLM Key** - AI features (embeddings, text generation)
- **Emergent-managed Google Auth** - Social login
- **Resend** - Email notifications (User API Key)
- **Twilio** - WhatsApp notifications (User API Key)

## Test Credentials
- **Email:** `admin@battwheels.in`
- **Password:** `admin123`
