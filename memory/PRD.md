# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

**Core Principle:** EFI is about reasoning, not just documentation.

## What's Been Implemented

### EFI Master Fault Tree Import Engine (Feb 16, 2026) ✅ NEW

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

Excel Column Mappings:
- `Complaint Description` → `title`, `symptom_text`, `failure_signature`
- `Root Causes (Probability Order)` → `root_cause`, `secondary_causes`, `probable_causes`
- `Diagnostic Steps` → `diagnostic_tree` (structured nodes)
- `Fault Tree Logic` → `fault_tree_logic` (parsed JSON)
- `Resolution Steps` → `resolution_steps[]`
- `Prevention Tips` → `prevention_guidelines[]`

Admin UI Features:
- Quick Import (one-click for default file)
- Custom file upload
- Preview before import
- Progress tracking
- Results summary

### EV Failure Intelligence Engine v2.0 (Feb 16, 2026) ✅ ENHANCED

**Core Entity: FAILURE_CARD (Central Intelligence Object)**
- `failure_id` - Unique identifier
- `title`, `description` - Human-readable info
- `failure_signature` - **NEW** Symptom + condition fingerprint for fast matching
- `signature_hash` - **NEW** Computed hash for fast lookup
- `diagnostic_tree` - **NEW** Structured step-by-step diagnostic logic tree
- `symptoms[]` - Structured symptom tags with knowledge graph links
- `subsystem_category` - battery, motor, controller, wiring, charger, BMS, etc.
- `root_cause` - Structured root cause description
- `verification_steps[]` - Diagnostic steps with tools/safety warnings
- `resolution_steps[]` - Resolution steps with parts/tools/skill level
- `required_parts[]` - Parts needed with alternatives
- `vehicle_models[]` - Compatible vehicles (make, model, year range)
- `failure_conditions[]` - Environmental/usage conditions
- `confidence_score` - 0-1 score based on usage outcomes
- `confidence_history[]` - **NEW** Track confidence changes over time
- `first_detected_at` - **NEW** When this failure was first seen
- `last_used_at` - **NEW** When this card was last used
- `source_type` - **NEW** field_discovery | oem_input | internal_analysis | pattern_detection
- `version` - Versioned knowledge objects
- `status` - draft/pending_review/approved/deprecated

**TECHNICIAN_ACTION (Enhanced with Reasoning Capture)**
- `attempted_diagnostics[]` - **NEW** Full diagnostic journey with hypotheses
- `rejected_hypotheses[]` - **NEW** What was ruled out (for AI learning)
- `failure_card_accuracy_rating` - 1-5 rating
- `failure_card_modifications[]` - What was different from card

**PART_USAGE (Enhanced for Pattern Detection)**
- `expected_vs_actual` - **NEW** Boolean to detect wrong diagnosis / hidden patterns
- `expectation_notes` - **NEW** Why part usage didn't match expectation

**AI Matching Pipeline v2.0 (Priority Order)**
1. **Stage 1: Failure Signature Match** - Fastest, highest confidence (< 5ms)
2. **Stage 2: Subsystem + Vehicle Filtering** - Context-aware (< 30ms)
3. **Stage 3: Semantic Similarity** - Deep understanding (< 100ms)
4. **Stage 4: Keyword Fallback** - Last resort (< 50ms)

**Architecture Rule:** AI assists ranking. Human-approved FAILURE_CARD remains source of truth.

**Event-Driven Workflows (4 Workflows)**
1. `ticket.created` → Auto-trigger AI matching
2. `failure.discovered` → Auto-create draft failure card
3. `ticket.resolved` → Update confidence scores with history tracking
4. `pattern.detected` → **NEW** Emerging pattern detection for expert review

**Emerging Pattern Detection (NEW)**
- Scheduled background job
- Detects repeating symptoms without linked failure_card
- Detects abnormal part replacement patterns
- Auto-flags for expert review
- **EFI must discover intelligence, not only react**

### Backend Architecture (Feb 16, 2026) ✅
```
/app/backend/
├── models/
│   └── failure_intelligence.py  # EFI data models (900+ lines)
├── routes/
│   ├── failure_intelligence.py  # EFI API routes (1000+ lines)
│   └── fault_tree_import.py     # NEW - Import API routes
├── services/
│   ├── event_processor.py       # EFI event workflows
│   ├── fault_tree_import.py     # NEW - Import engine (800+ lines)
│   ├── invoice_service.py       # PDF generation
│   └── notification_service.py  # Email/WhatsApp
├── utils/
│   ├── database.py              # DB config
│   └── auth.py                  # Auth helpers
└── server.py                    # Main server (modular)
```

### Frontend Pages
- `/fault-tree-import` - NEW - Admin import interface
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

### P0 (Immediate) - COMPLETED ✅
- [x] EFI Core Architecture Validation
- [x] Core Data Models Implementation
- [x] Event-Driven Workflows Implementation
- [x] AI Matching Pipeline (4-stage)
- [x] Master Fault Tree Import Engine

### P1 (High Priority - Next)
- [ ] UI Theme Overhaul (deferred until EFI stable)
- [ ] GST-Compliant PDF Invoice Integration
- [ ] Notification Workflow Integration
- [ ] Backend Refactoring (migrate remaining from server.py)

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

### Fault Tree Import Endpoints (NEW)
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
