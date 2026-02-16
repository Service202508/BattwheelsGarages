# Battwheels OS - EV Failure Intelligence Platform PRD

## Original Problem Statement
Build an AI-native EV Failure Intelligence (EFI) Platform where structured failure knowledge is the core data model. Every EV issue solved once must become a reusable, standardized solution across the entire technician network.

## What's Been Implemented

### EV Failure Intelligence Engine (Feb 16, 2026) ✅ NEW

**Core Entity: FAILURE_CARD**
- `failure_id` - Unique identifier
- `title`, `description` - Human-readable info
- `symptoms[]` - Structured symptom tags with knowledge graph links
- `subsystem_category` - battery, motor, controller, wiring, charger, BMS, etc.
- `root_cause` - Structured root cause description
- `verification_steps[]` - Diagnostic steps with tools/safety warnings
- `resolution_steps[]` - Resolution steps with parts/tools/skill level
- `required_parts[]` - Parts needed with alternatives
- `vehicle_models[]` - Compatible vehicles (make, model, year range)
- `failure_conditions[]` - Environmental/usage conditions
- `confidence_score` - 0-1 score based on usage outcomes
- `version` - Versioned knowledge objects
- `status` - draft/pending_review/approved/deprecated

**AI Matching Pipeline**
- Stage 1: Exact error code matching (95% confidence)
- Stage 2: Subsystem + keyword matching
- Stage 3: Semantic similarity search
- Stage 4: Vehicle-specific filtering
- Ensemble ranking with weighted scores

**Knowledge Graph Structure**
- Symptoms ↔ Failures ↔ Parts ↔ Vehicles
- Relationship types: causes, resolves, requires, affects, similar_to

**Event-Driven Workflow**
- `ticket_created` → Auto-trigger AI matching
- `ticket_resolved` → Update confidence scores
- `new_failure_discovered` → Auto-create draft card
- `failure_card_approved` → Trigger network sync

### Backend Refactoring (Feb 16, 2026) ✅
```
/app/backend/
├── models/
│   └── failure_intelligence.py  # EFI data models (800+ lines)
├── routes/
│   └── failure_intelligence.py  # EFI API routes (750+ lines)
├── services/
│   ├── invoice_service.py       # PDF generation
│   └── notification_service.py  # Email/WhatsApp
├── utils/
│   ├── database.py              # DB config
│   └── auth.py                  # Auth helpers
└── server.py                    # Main server (modular)
```

### Previous Implementations
- Technical Specification Document (`/app/docs/TECHNICAL_SPEC.md`)
- Invoice PDF Generation (GST compliant)
- Notification Service (Email/WhatsApp)
- Employee Management with India compliance
- Complaint Dashboard & Job Card
- Core ERP modules
- HR & Payroll

## API Endpoints

### EFI (Failure Intelligence) APIs
```
POST   /api/efi/failure-cards           - Create failure card
GET    /api/efi/failure-cards           - List with filters
GET    /api/efi/failure-cards/{id}      - Get single card
PUT    /api/efi/failure-cards/{id}      - Update card
POST   /api/efi/failure-cards/{id}/approve    - Approve for network
POST   /api/efi/failure-cards/{id}/deprecate  - Deprecate card

POST   /api/efi/match                   - AI failure matching
POST   /api/efi/match-ticket/{id}       - Match ticket to failures

POST   /api/efi/technician-actions      - Record tech actions
GET    /api/efi/technician-actions      - List actions

POST   /api/efi/symptoms                - Add symptom to library
GET    /api/efi/symptoms                - List symptoms

POST   /api/efi/relations               - Create knowledge relation
GET    /api/efi/relations               - Query relations
GET    /api/efi/graph/{type}/{id}       - Get entity graph

GET    /api/efi/analytics/overview      - EFI analytics
GET    /api/efi/analytics/effectiveness - Effectiveness report
GET    /api/efi/events                  - List system events
POST   /api/efi/events/process          - Process pending events
```

## Data Models

### FailureCard (Core Entity)
```json
{
  "failure_id": "fc_abc123",
  "title": "BMS Cell Balancing Failure",
  "subsystem_category": "bms",
  "failure_mode": "degradation",
  "symptom_text": "Battery stops charging at 80%",
  "error_codes": ["E401", "E402"],
  "root_cause": "BMS cell balancing circuit failure",
  "verification_steps": [...],
  "resolution_steps": [...],
  "required_parts": [...],
  "vehicle_models": [{"make": "Ather", "model": "450X"}],
  "confidence_score": 0.85,
  "usage_count": 234,
  "success_count": 220,
  "status": "approved",
  "version": 3
}
```

## Test Credentials
- **Admin:** admin@battwheels.in / admin123
- **Technician:** deepak@battwheelsgarages.in / tech123

## Architecture Highlights

### Intelligence Flow
```
Ticket Created
    ↓
AI Matching (symptoms → failure cards)
    ↓
Suggest Solutions to Technician
    ↓
Technician Uses/Modifies Solution
    ↓
Record Outcome (TechnicianAction)
    ↓
Update Confidence Scores
    ↓
New Failure? → Create Draft Card
    ↓
Expert Review → Approve
    ↓
Network Sync → All Garages
```

### Continuous Learning
- Every repair outcome updates confidence scores
- Success rate = success_count / usage_count
- High-performing cards get recommended first
- Low-performing cards get flagged for review

## Prioritized Backlog

### P0 (Completed) ✅
- [x] EFI Engine with failure cards
- [x] AI matching pipeline
- [x] Knowledge graph structure
- [x] Technician actions tracking
- [x] Event-driven workflow
- [x] Analytics dashboard
- [x] Backend modularization

### P1 (Next Phase)
- [ ] Semantic embeddings with OpenAI
- [ ] Real-time network sync (WebSocket)
- [ ] Mobile app for field technicians
- [ ] PDF/Email for failure card sharing

### P2 (Future)
- [ ] Multi-OEM vehicle support
- [ ] Predictive failure detection
- [ ] Automated card generation from tickets
- [ ] Integration with OEM diagnostic tools

## Testing
- EFI Engine: Tested via curl (matching, card creation)
- Frontend: Screenshot verified
- Test reports: /app/test_reports/
