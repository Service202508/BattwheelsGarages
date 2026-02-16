# Battwheels OS - EV Failure Intelligence (EFI) Core Architecture

**Version:** 2.0  
**Date:** December 2025  
**Status:** Architecture Validation Phase  
**Purpose:** Finalize core system architecture before UI/theme implementation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture Diagram](#2-system-architecture-diagram)
3. [Core Data Models](#3-core-data-models)
4. [Event-Driven Workflows](#4-event-driven-workflows)
5. [AI Pipeline Integration](#5-ai-pipeline-integration)
6. [Modular Backend Structure](#6-modular-backend-structure)
7. [Implementation Roadmap](#7-implementation-roadmap)

---

## 1. Executive Summary

### Core Principle
**Every repair builds shared knowledge.** EFI is not just a ticket system—it's a continuously learning intelligence platform where:
- Structured failure knowledge is the **primary data asset**
- Operational modules (Tickets, Inventory, HR) **feed into** the EFI core
- AI matching and confidence scoring create **compounding intelligence**

### Architecture Philosophy
```
┌─────────────────────────────────────────────────────────────────┐
│                    OPERATIONAL LAYER                            │
│  (Tickets, Inventory, HR, Invoicing - generates raw data)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EFI CORE LAYER                               │
│  (Failure Cards, Knowledge Graph, AI Matching, Confidence)      │
│  ════════════════════════════════════════════════════════════   │
│  This is the BRAIN of the system - all intelligence lives here  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NETWORK SYNC LAYER                           │
│  (Cross-location sync, knowledge distribution)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. System Architecture Diagram

### 2.1 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BATTWHEELS EFI PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         CLIENT LAYER                                   │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │  Web App    │  │ Mobile App  │  │ Technician  │  │  Admin      │  │ │
│  │  │  (React)    │  │  (Future)   │  │   Portal    │  │  Dashboard  │  │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │ │
│  └─────────┼────────────────┼────────────────┼────────────────┼─────────┘ │
│            └────────────────┴────────────────┴────────────────┘           │
│                                    │                                       │
│                           ┌────────▼────────┐                             │
│                           │   API Gateway   │                             │
│                           │   (FastAPI)     │                             │
│                           └────────┬────────┘                             │
│                                    │                                       │
│  ┌─────────────────────────────────┼─────────────────────────────────┐   │
│  │                          EFI CORE ENGINE                           │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │                    FAILURE_CARD (Central Entity)             │  │   │
│  │  │  • Symptoms • Root Cause • Resolution Steps • Parts          │  │   │
│  │  │  • Vehicle Compatibility • Confidence Score • Usage Stats    │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                                │                                   │   │
│  │  ┌──────────────┐  ┌──────────▼──────────┐  ┌──────────────┐     │   │
│  │  │   TICKET     │  │  KNOWLEDGE_GRAPH    │  │  AI_PIPELINE │     │   │
│  │  │   (Input)    │──│  (Relationships)    │──│  (Matching)  │     │   │
│  │  └──────────────┘  └─────────────────────┘  └──────────────┘     │   │
│  │                                │                                   │   │
│  │  ┌──────────────┐  ┌──────────▼──────────┐  ┌──────────────┐     │   │
│  │  │ TECHNICIAN   │  │  CONFIDENCE_ENGINE  │  │  PART_USAGE  │     │   │
│  │  │ _ACTION      │──│  (Learning Loop)    │──│  (Tracking)  │     │   │
│  │  └──────────────┘  └─────────────────────┘  └──────────────┘     │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────┼─────────────────────────────────┐   │
│  │                        EVENT BUS                                   │   │
│  │  ticket.created → failure.matched → action.recorded → card.updated │   │
│  └─────────────────────────────────┬─────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────┼─────────────────────────────────┐   │
│  │                     DATA PERSISTENCE                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │   │
│  │  │  MongoDB    │  │   Redis     │  │  S3/MinIO   │               │   │
│  │  │  (Docs)     │  │  (Cache)    │  │  (Files)    │               │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EFI DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CAPTURE PHASE                    INTELLIGENCE PHASE                        │
│  ═════════════                    ══════════════════                        │
│                                                                             │
│  ┌─────────────┐                  ┌─────────────────────────────────┐      │
│  │   TICKET    │                  │        AI MATCHING              │      │
│  │   Created   │─────────────────▶│  ┌───────────────────────────┐ │      │
│  │             │                  │  │ 1. Error Code Match (95%) │ │      │
│  │ • Symptoms  │                  │  │ 2. Keyword Match  (70%)   │ │      │
│  │ • Vehicle   │                  │  │ 3. Semantic Match (60%)   │ │      │
│  │ • Error Codes                  │  │ 4. Vehicle Filter (50%)   │ │      │
│  └─────────────┘                  │  └───────────────────────────┘ │      │
│                                   └────────────┬────────────────────┘      │
│                                                │                            │
│                                                ▼                            │
│                                   ┌─────────────────────────────────┐      │
│  EXECUTION PHASE                  │     SUGGESTED_FAILURE_CARDS     │      │
│  ═══════════════                  │     (Ranked by confidence)      │      │
│                                   └────────────┬────────────────────┘      │
│  ┌─────────────┐                               │                            │
│  │ TECHNICIAN  │◀──────────────────────────────┘                            │
│  │   ACTION    │                                                            │
│  │             │                  ┌─────────────────────────────────┐      │
│  │ • Used Card │─────────────────▶│     CONFIDENCE UPDATE           │      │
│  │ • Parts Used│                  │                                 │      │
│  │ • Outcome   │                  │  Success → confidence += 0.01   │      │
│  │ • New Issue?│                  │  Failure → confidence -= 0.02   │      │
│  └─────────────┘                  └────────────┬────────────────────┘      │
│                                                │                            │
│                                                ▼                            │
│  LEARNING PHASE                   ┌─────────────────────────────────┐      │
│  ══════════════                   │     FAILURE_CARD UPDATED        │      │
│                                   │                                 │      │
│  ┌─────────────┐                  │  • usage_count++                │      │
│  │ NEW FAILURE │◀─────────────────│  • success_count++ (if success) │      │
│  │ DISCOVERED  │                  │  • effectiveness recalculated   │      │
│  │             │                  └─────────────────────────────────┘      │
│  │ Auto-create │                                                           │
│  │ DRAFT card  │                                                           │
│  └─────────────┘                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Data Models

### 3.1 FAILURE_CARD (Central Knowledge Object)

The FAILURE_CARD is the **most important entity** in the system. It represents structured, reusable repair knowledge.

**EFI is about reasoning, not just documentation.**

```python
class FailureCard:
    """
    Central Knowledge Object - Every repair solution becomes a card
    Enhanced v2.0 with diagnostic reasoning and confidence tracking
    """
    # === IDENTIFICATION ===
    failure_id: str           # fc_abc123def456
    version: int              # Versioned knowledge (1, 2, 3...)
    status: FailureCardStatus # draft | pending_review | approved | deprecated
    
    # === CLASSIFICATION ===
    title: str                # "BMS Cell Balancing Circuit Failure"
    description: str          # Detailed description
    subsystem_category: SubsystemCategory  # battery, motor, controller, bms, charger...
    failure_mode: FailureMode # complete_failure, intermittent, degradation...
    
    # === FAILURE SIGNATURE (NEW - Primary Matching Key) ===
    failure_signature: FailureSignature  # Symptom + condition fingerprint
    signature_hash: str       # Computed hash for fast lookup
    
    # === SYMPTOM SIGNATURE ===
    symptoms: List[Symptom]   # Structured symptom objects (knowledge graph links)
    symptom_codes: List[str]  # Quick reference: ["SYM_BATT_001", "SYM_CHRG_003"]
    symptom_text: str         # Free-text: "Battery not charging beyond 80%"
    error_codes: List[str]    # OEM codes: ["E401", "E402"]
    
    # === ROOT CAUSE ANALYSIS ===
    root_cause: str           # "BMS cell balancing circuit failure"
    root_cause_details: str   # Extended explanation
    secondary_causes: List[str]  # ["thermal stress", "manufacturing_defect"]
    
    # === DIAGNOSTIC TREE (NEW - Structured Reasoning) ===
    diagnostic_tree: DiagnosticTree  # Step-by-step diagnostic logic tree
    # Contains: root_node_id, nodes[], decision branches, confirmation paths
    
    # === DIAGNOSTIC PROCESS (Legacy) ===
    verification_steps: List[VerificationStep]  # How to verify this failure
    diagnostic_tools: List[str]                 # Tools needed for diagnosis
    diagnostic_duration_minutes: int            # Expected diagnosis time
    
    # === RESOLUTION ===
    resolution_steps: List[ResolutionStep]      # Step-by-step fix
    resolution_summary: str                     # Quick summary
    estimated_repair_time_minutes: int
    skill_level_required: str  # basic, intermediate, advanced, expert
    
    # === PARTS ===
    required_parts: List[RequiredPart]
    estimated_parts_cost: float
    estimated_labor_cost: float
    estimated_total_cost: float
    
    # === VEHICLE COMPATIBILITY ===
    vehicle_models: List[VehicleCompatibility]  # Which vehicles this applies to
    universal_failure: bool   # True if applies to all EVs
    
    # === CONDITIONS ===
    failure_conditions: List[FailureCondition]  # When this failure occurs
    
    # === INTELLIGENCE METRICS ===
    confidence_score: float   # 0.0 - 1.0 (continuously updated)
    confidence_level: ConfidenceLevel  # low, medium, high, verified
    usage_count: int          # How many times this card was used
    success_count: int        # Successful repairs using this card
    failure_count: int        # Failed repairs using this card
    effectiveness_score: float  # success_count / usage_count + bonuses
    
    # === CONFIDENCE HISTORY (NEW - Track Learning Over Time) ===
    confidence_history: List[ConfidenceChangeEvent]  # Track all confidence changes
    # Each entry: {timestamp, previous_score, new_score, change_reason, ticket_id}
    
    # === AI/ML METADATA ===
    embedding_vector: List[float]  # 768-dim semantic embedding
    keywords: List[str]       # Auto-extracted keywords
    tags: List[str]           # Manual tags
    
    # === PROVENANCE (ENHANCED) ===
    source_type: SourceType   # field_discovery | oem_input | internal_analysis | pattern_detection
    source_ticket_id: str     # Original ticket that created this card
    source_garage_id: str     # Garage where first discovered
    created_by: str           # Technician who created
    approved_by: str          # Expert who approved
    
    # === TIMESTAMPS (ENHANCED) ===
    created_at: datetime
    updated_at: datetime
    approved_at: datetime
    first_detected_at: datetime  # NEW - When this failure was first seen
    last_used_at: datetime       # NEW - When this card was last used
    
    # === VERSION HISTORY ===
    version_history: List[dict]  # Track all changes
    
    # === NETWORK SYNC ===
    synced_to_network: bool
    last_sync_at: datetime
```

### 3.1.1 FailureSignature (Fast Matching Key)

```python
class FailureSignature:
    """
    Symptom + condition fingerprint for faster matching
    PRIMARY key for fast failure card lookup
    """
    signature_id: str
    signature_hash: str           # Computed hash for fast lookup
    
    # Core symptom indicators
    primary_symptoms: List[str]   # Most important symptoms (ordered)
    error_codes: List[str]        # OEM error codes
    subsystem: SubsystemCategory
    failure_mode: FailureMode
    
    # Environmental conditions
    temperature_range: str        # "30-45°C"
    humidity_range: str           # "high", "low", "normal"
    load_condition: str           # "under_load", "idle", "charging"
    
    # Vehicle context
    mileage_range: str            # "0-10000", "10000-50000", etc.
    vehicle_age_months: int
    
    # Pattern indicators
    occurrence_pattern: str       # sporadic, daily, weekly, weather_dependent
    time_of_day_pattern: str      # morning, afternoon, night, random
```

### 3.1.2 DiagnosticTree (Structured Reasoning)

```python
class DiagnosticTree:
    """
    Structured step-by-step diagnostic logic tree
    EFI is about reasoning, not just documentation
    """
    tree_id: str
    root_node_id: str             # Starting point of diagnosis
    nodes: List[DiagnosticNode]   # All decision nodes
    total_paths: int              # Number of possible diagnostic paths
    avg_path_length: int          # Average steps to diagnosis

class DiagnosticNode:
    """Single node in the diagnostic decision tree"""
    node_id: str
    step_number: int
    question: str                 # "Is the battery voltage below 48V?"
    check_action: str             # "Measure battery terminal voltage"
    expected_outcome: str         # "Voltage should be 48-54V"
    tools_required: List[str]
    safety_warnings: List[str]
    duration_minutes: int
    
    # Decision branches
    if_yes: str                   # Next node_id if condition is true
    if_no: str                    # Next node_id if condition is false
    leads_to_root_cause: str      # If this confirms root cause
```

### 3.2 TICKET (Operational Input)

```python
class Ticket:
    """
    Service ticket - operational data that feeds into EFI
    """
    # === IDENTIFICATION ===
    ticket_id: str            # tkt_xyz789
    status: TicketStatus      # open, in_progress, pending_parts, resolved, closed
    
    # === VEHICLE INFO ===
    vehicle_id: str
    vehicle_type: str         # two_wheeler, three_wheeler, four_wheeler
    vehicle_make: str         # Ather, Ola, TVS, Tata
    vehicle_model: str        # 450X, S1 Pro, iQube
    vehicle_number: str       # Registration
    vehicle_mileage_km: int
    vehicle_firmware: str     # Firmware version if available
    
    # === CUSTOMER INFO ===
    customer_id: str
    customer_name: str
    customer_contact: str
    customer_type: str        # individual, fleet, corporate
    
    # === COMPLAINT ===
    title: str
    description: str
    category: str             # battery, motor, charging, electrical, mechanical
    priority: str             # low, medium, high, critical
    error_codes_reported: List[str]
    
    # === ASSIGNMENT ===
    assigned_technician_id: str
    assigned_technician_name: str
    assigned_at: datetime
    
    # === EFI INTEGRATION ===
    suggested_failure_cards: List[str]  # Failure card IDs suggested by AI
    selected_failure_card: str          # Card chosen by technician
    ai_match_performed: bool
    ai_match_timestamp: datetime
    
    # === RESOLUTION ===
    resolution: str
    resolution_type: str      # workshop, onsite, pickup, remote
    parts_used: List[dict]
    labor_hours: float
    
    # === COSTING ===
    estimated_cost: float
    actual_cost: float
    parts_cost: float
    labor_cost: float
    
    # === OUTCOME (feeds into EFI) ===
    resolution_successful: bool
    customer_satisfaction: int  # 1-5
    revisit_required: bool
    new_failure_discovered: bool
    
    # === STATUS HISTORY ===
    status_history: List[dict]  # [{status, timestamp, updated_by}]
    
    # === TIMESTAMPS ===
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime
    closed_at: datetime
```

### 3.3 TECHNICIAN_ACTION (Repair Execution Record)

**Do NOT store only final outcome.** Track the reasoning journey for AI learning.

```python
class TechnicianAction:
    """
    Records what the technician actually did - critical for learning
    Enhanced v2.0 with diagnostic reasoning capture
    """
    # === IDENTIFICATION ===
    action_id: str            # act_abc123
    ticket_id: str            # Link to ticket
    technician_id: str
    technician_name: str
    
    # === DIAGNOSTIC PHASE (ENHANCED) ===
    diagnostic_steps_performed: List[str]      # What was checked
    attempted_diagnostics: List[AttemptedDiagnostic]  # NEW - Detailed attempts
    rejected_hypotheses: List[RejectedHypothesis]     # NEW - What was ruled out
    observations: List[str]   # What was found
    measurements: Dict[str, Any]  # Voltage readings, temperatures, etc.
    photos: List[str]         # Evidence photos (S3 URLs)
    diagnostic_time_minutes: int
    
    # === FAILURE CARD INTERACTION ===
    failure_cards_suggested: List[str]    # IDs shown to technician
    failure_cards_viewed: List[str]       # IDs technician looked at
    failure_card_used: str                # ID of card actually used
    failure_card_helpful: bool            # Did it help? (explicit feedback)
    failure_card_accuracy_rating: int     # 1-5 rating
    failure_card_modifications: List[str] # What was different from card
    
    # === RESOLUTION PHASE ===
    resolution_steps_followed: List[str]  # Steps actually performed
    parts_used: List[PartUsage]           # Parts consumed
    tools_used: List[str]                 # Tools employed
    resolution_time_minutes: int
    
    # === OUTCOME ===
    resolution_outcome: str   # success, partial, failed, escalated
    issue_resolved: bool
    new_issue_found: bool
    escalation_reason: str    # If escalated
    
    # === DISCOVERY (New Knowledge) ===
    new_failure_discovered: bool
    new_failure_description: str
    new_failure_root_cause: str
    new_failure_resolution: str
    suggest_new_card: bool    # Technician suggests creating new card
    
    # === FEEDBACK ===
    technician_notes: str
    difficulty_rating: int    # 1-5 (how hard was this repair)
    documentation_quality_rating: int  # 1-5 (how good was the failure card)
    
    # === TIMESTAMPS ===
    started_at: datetime
    completed_at: datetime

class AttemptedDiagnostic:
    """Records a single diagnostic attempt - for AI learning"""
    step_id: str
    hypothesis: str           # What they thought was wrong
    check_performed: str      # What they did to verify
    result: str               # What they found
    confirmed: bool           # Did this confirm the hypothesis?
    tools_used: List[str]
    measurements: Dict[str, Any]
    timestamp: datetime

class RejectedHypothesis:
    """Records ruled out possibilities - for AI learning"""
    hypothesis: str           # What was considered
    reason_rejected: str      # Why it was ruled out
    evidence: str             # What evidence disproved it
    ruled_out_at: datetime
```

### 3.4 PART_USAGE (Parts Consumption Tracking)

```python
class PartUsage:
    """
    Tracks parts consumption - feeds into inventory and cost analysis
    """
    # === IDENTIFICATION ===
    usage_id: str             # use_abc123
    ticket_id: str
    action_id: str
    
    # === PART INFO ===
    part_id: str              # Inventory item ID
    part_name: str
    part_number: str          # SKU
    category: str             # battery, motor, controller, wiring...
    
    # === QUANTITY ===
    quantity_allocated: int   # Reserved from inventory
    quantity_used: int        # Actually consumed
    quantity_returned: int    # Returned to inventory
    
    # === COST ===
    unit_cost: float
    total_cost: float
    
    # === FAILURE CARD LINK ===
    failure_card_id: str      # Which card recommended this part
    was_recommended: bool     # Was this part in the card's required_parts?
    is_substitute: bool       # Was this a substitute for recommended part?
    substitute_for: str       # Original part it replaced
    
    # === STATUS ===
    status: str               # allocated, used, returned, damaged
    
    # === TIMESTAMPS ===
    allocated_at: datetime
    used_at: datetime
    returned_at: datetime
```

### 3.5 KNOWLEDGE_RELATIONSHIP (Knowledge Graph Edge)

```python
class KnowledgeRelationship:
    """
    Connects entities in the knowledge graph
    """
    # === IDENTIFICATION ===
    relation_id: str          # rel_abc123
    
    # === SOURCE ===
    source_type: str          # symptom, failure_card, part, vehicle, subsystem
    source_id: str
    source_label: str         # Human-readable label
    
    # === RELATIONSHIP ===
    relation_type: str        # causes, resolves, requires, affects, similar_to
    weight: float             # 0.0 - 1.0 (strength of relationship)
    confidence: float         # How sure are we about this relationship
    
    # === TARGET ===
    target_type: str
    target_id: str
    target_label: str
    
    # === METADATA ===
    bidirectional: bool       # Does relationship work both ways?
    evidence_count: int       # How many times observed
    last_observed: datetime
    
    # === PROVENANCE ===
    created_by: str           # user_id or "system"
    creation_method: str      # manual, inferred, ai_generated
    created_at: datetime
```

### 3.6 Entity Relationship Diagram

```
                                    ┌─────────────────┐
                                    │    VEHICLE      │
                                    │                 │
                                    │ • make          │
                                    │ • model         │
                                    │ • year          │
                                    └────────┬────────┘
                                             │
                                             │ has_failure
                                             ▼
┌─────────────────┐    creates    ┌─────────────────────────┐
│     TICKET      │──────────────▶│      FAILURE_CARD       │
│                 │               │                         │
│ • symptoms      │               │ • root_cause            │
│ • error_codes   │               │ • resolution_steps      │
│ • description   │               │ • required_parts        │
└────────┬────────┘               │ • confidence_score      │
         │                        └────────────┬────────────┘
         │                                     │
         │ generates                           │ recommends
         ▼                                     ▼
┌─────────────────┐    uses       ┌─────────────────┐
│   TECHNICIAN    │──────────────▶│      PART       │
│   _ACTION       │               │                 │
│                 │               │ • name          │
│ • steps done    │               │ • quantity      │
│ • outcome       │               │ • cost          │
│ • feedback      │               └─────────────────┘
└────────┬────────┘
         │
         │ records
         ▼
┌─────────────────┐
│   PART_USAGE    │
│                 │
│ • qty_used      │
│ • cost          │
│ • was_helpful   │
└─────────────────┘

         KNOWLEDGE GRAPH RELATIONSHIPS
         ══════════════════════════════

┌─────────────┐                    ┌─────────────┐
│   SYMPTOM   │──── causes ───────▶│   FAILURE   │
│             │                    │   _CARD     │
│ • code      │◀─── indicates ─────│             │
│ • description                    │ • root_cause│
└─────────────┘                    └──────┬──────┘
                                          │
                        resolves ─────────┤
                                          │
                                   ┌──────▼──────┐
                                   │    PART     │
                                   │             │
                                   │ • name      │
                                   │ • cost      │
                                   └─────────────┘
```

---

## 4. Event-Driven Workflows

### 4.1 Event Types

```python
class EFIEventType(Enum):
    # === TICKET LIFECYCLE ===
    TICKET_CREATED = "ticket.created"
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_IN_PROGRESS = "ticket.in_progress"
    TICKET_RESOLVED = "ticket.resolved"
    TICKET_CLOSED = "ticket.closed"
    
    # === AI MATCHING ===
    MATCH_REQUESTED = "match.requested"
    MATCH_COMPLETED = "match.completed"
    MATCH_FAILED = "match.failed"
    
    # === TECHNICIAN ACTIONS ===
    ACTION_STARTED = "action.started"
    ACTION_COMPLETED = "action.completed"
    CARD_USED = "card.used"
    CARD_RATED = "card.rated"
    NEW_FAILURE_DISCOVERED = "failure.discovered"
    
    # === FAILURE CARD LIFECYCLE ===
    CARD_CREATED = "card.created"
    CARD_SUBMITTED = "card.submitted_for_review"
    CARD_APPROVED = "card.approved"
    CARD_DEPRECATED = "card.deprecated"
    CARD_UPDATED = "card.updated"
    
    # === CONFIDENCE UPDATES ===
    CONFIDENCE_UPDATED = "confidence.updated"
    EFFECTIVENESS_RECALCULATED = "effectiveness.recalculated"
    
    # === NETWORK SYNC ===
    SYNC_REQUESTED = "sync.requested"
    SYNC_COMPLETED = "sync.completed"
```

### 4.2 Workflow Definitions

#### Workflow 1: Ticket Created → Trigger AI Similarity Matching

```
┌─────────────────────────────────────────────────────────────────┐
│              WORKFLOW: TICKET_CREATED                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER: New ticket created via API                            │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │ 1. TICKET_CREATED│                                          │
│  │    Event         │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 2. Extract       │                                          │
│  │    Symptoms      │                                          │
│  │    • error_codes │                                          │
│  │    • description │                                          │
│  │    • category    │                                          │
│  │    • vehicle     │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 3. AI Matching   │                                          │
│  │    Pipeline      │                                          │
│  │    • Exact code  │                                          │
│  │    • Keyword     │                                          │
│  │    • Semantic    │                                          │
│  │    • Vehicle     │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 4. Update Ticket │                                          │
│  │    • suggested_  │                                          │
│  │      failure_    │                                          │
│  │      cards[]     │                                          │
│  │    • ai_match_   │                                          │
│  │      performed   │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 5. Emit          │                                          │
│  │    MATCH_        │                                          │
│  │    COMPLETED     │                                          │
│  └──────────────────┘                                          │
│                                                                 │
│  OUTPUT: Ticket has suggested_failure_cards populated           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Workflow 2: Technician Marks Undocumented Issue → Auto-Create Failure Card Draft

```
┌─────────────────────────────────────────────────────────────────┐
│              WORKFLOW: NEW_FAILURE_DISCOVERED                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER: TechnicianAction.new_failure_discovered = true        │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │ 1. NEW_FAILURE   │                                          │
│  │    _DISCOVERED   │                                          │
│  │    Event         │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 2. Extract from  │                                          │
│  │    TechAction    │                                          │
│  │    • description │                                          │
│  │    • root_cause  │                                          │
│  │    • resolution  │                                          │
│  │    • parts_used  │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 3. Extract from  │                                          │
│  │    Ticket        │                                          │
│  │    • vehicle     │                                          │
│  │    • category    │                                          │
│  │    • error_codes │                                          │
│  │    • symptoms    │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 4. Create DRAFT  │                                          │
│  │    FailureCard   │                                          │
│  │    • status=draft│                                          │
│  │    • confidence  │                                          │
│  │      =0.3 (new)  │                                          │
│  │    • source_     │                                          │
│  │      ticket_id   │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 5. Emit          │                                          │
│  │    CARD_CREATED  │                                          │
│  │    + Notify      │                                          │
│  │    expert queue  │                                          │
│  └──────────────────┘                                          │
│                                                                 │
│  OUTPUT: New draft failure card for expert review               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Workflow 3: Ticket Closure → Update Failure Intelligence Confidence Score

```
┌─────────────────────────────────────────────────────────────────┐
│              WORKFLOW: TICKET_RESOLVED                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER: Ticket status changed to "resolved"                   │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │ 1. TICKET_       │                                          │
│  │    RESOLVED      │                                          │
│  │    Event         │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 2. Get Linked    │                                          │
│  │    TechAction    │                                          │
│  │    • card_used   │                                          │
│  │    • outcome     │                                          │
│  │    • rating      │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 3. Determine     │                                          │
│  │    Success       │                                          │
│  │    • outcome==   │                                          │
│  │      "success"   │                                          │
│  │    • no revisit  │                                          │
│  │    • customer    │                                          │
│  │      satisfied   │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────┐              │
│  │ 4. Update FailureCard Metrics                │              │
│  │                                              │              │
│  │    IF used_failure_card:                     │              │
│  │       usage_count += 1                       │              │
│  │                                              │              │
│  │       IF success:                            │              │
│  │          success_count += 1                  │              │
│  │          confidence += 0.01                  │              │
│  │       ELSE:                                  │              │
│  │          failure_count += 1                  │              │
│  │          confidence -= 0.02                  │              │
│  │                                              │              │
│  │       effectiveness = calculate_effectiveness│              │
│  │       confidence_level = get_level(score)    │              │
│  └────────┬─────────────────────────────────────┘              │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ 5. Emit          │                                          │
│  │    CONFIDENCE_   │                                          │
│  │    UPDATED       │                                          │
│  └──────────────────┘                                          │
│                                                                 │
│  OUTPUT: Failure card confidence/effectiveness updated          │
│                                                                 │
│  FORMULA:                                                       │
│  ════════                                                       │
│  effectiveness = (success_count / usage_count)                  │
│                  + min(0.1, usage_count / 100)  # usage bonus   │
│                                                                 │
│  confidence_level:                                              │
│    < 0.4  → LOW                                                 │
│    0.4-0.7 → MEDIUM                                             │
│    0.7-0.9 → HIGH                                               │
│    > 0.9  → VERIFIED                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Event Processing Implementation

```python
class EFIEventProcessor:
    """
    Central event processor for EFI workflows
    """
    
    async def process_event(self, event: EFIEvent):
        """Route event to appropriate handler"""
        handlers = {
            "ticket.created": self.handle_ticket_created,
            "ticket.resolved": self.handle_ticket_resolved,
            "action.completed": self.handle_action_completed,
            "failure.discovered": self.handle_new_failure,
            "card.approved": self.handle_card_approved,
        }
        
        handler = handlers.get(event.event_type)
        if handler:
            result = await handler(event)
            await self.mark_processed(event, result)
    
    async def handle_ticket_created(self, event: EFIEvent):
        """Workflow 1: Auto-trigger AI matching"""
        ticket_id = event.data["ticket_id"]
        ticket = await db.tickets.find_one({"ticket_id": ticket_id})
        
        # Build match request
        match_request = FailureMatchRequest(
            symptom_text=f"{ticket['title']} {ticket['description']}",
            error_codes=ticket.get("error_codes_reported", []),
            vehicle_make=ticket.get("vehicle_make"),
            vehicle_model=ticket.get("vehicle_model"),
            limit=5
        )
        
        # Perform matching
        matches = await self.ai_matcher.match(match_request)
        
        # Update ticket with suggestions
        await db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {
                "suggested_failure_cards": [m.failure_id for m in matches],
                "ai_match_performed": True,
                "ai_match_timestamp": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"matches_found": len(matches)}
    
    async def handle_ticket_resolved(self, event: EFIEvent):
        """Workflow 3: Update confidence scores"""
        ticket_id = event.data["ticket_id"]
        
        # Get technician action
        action = await db.technician_actions.find_one({"ticket_id": ticket_id})
        if not action:
            return {"skipped": "no_action_found"}
        
        failure_card_id = action.get("failure_card_used")
        if not failure_card_id:
            return {"skipped": "no_card_used"}
        
        # Determine success
        is_success = (
            action.get("resolution_outcome") == "success" and
            not action.get("new_issue_found", False)
        )
        
        # Update card metrics
        card = await db.failure_cards.find_one({"failure_id": failure_card_id})
        
        usage_count = card.get("usage_count", 0) + 1
        success_count = card.get("success_count", 0) + (1 if is_success else 0)
        failure_count = card.get("failure_count", 0) + (0 if is_success else 1)
        
        # Calculate new scores
        effectiveness = self.calculate_effectiveness(
            success_count, failure_count, usage_count
        )
        confidence = min(1.0, max(0.0, 
            card.get("confidence_score", 0.5) + (0.01 if is_success else -0.02)
        ))
        
        await db.failure_cards.update_one(
            {"failure_id": failure_card_id},
            {"$set": {
                "usage_count": usage_count,
                "success_count": success_count,
                "failure_count": failure_count,
                "effectiveness_score": effectiveness,
                "confidence_score": confidence,
                "confidence_level": self.get_confidence_level(confidence)
            }}
        )
        
        return {"card_updated": failure_card_id, "new_confidence": confidence}
    
    async def handle_new_failure(self, event: EFIEvent):
        """Workflow 2: Auto-create draft failure card"""
        action_id = event.data["action_id"]
        ticket_id = event.data["ticket_id"]
        
        # Get action and ticket details
        action = await db.technician_actions.find_one({"action_id": action_id})
        ticket = await db.tickets.find_one({"ticket_id": ticket_id})
        
        # Create draft card
        draft_card = FailureCard(
            title=f"[DRAFT] {action.get('new_failure_description', 'New Issue')}",
            description=action.get("observations", [])[:500],
            subsystem_category=self.infer_subsystem(ticket.get("category")),
            root_cause=action.get("new_failure_root_cause", "Under Investigation"),
            resolution_steps=[{
                "step_number": 1,
                "action": action.get("new_failure_resolution", "Resolution pending"),
                "duration_minutes": 30
            }],
            source_ticket_id=ticket_id,
            created_by=action.get("technician_id"),
            status=FailureCardStatus.DRAFT,
            confidence_score=0.3,  # Low initial confidence for new cards
            vehicle_models=[{
                "make": ticket.get("vehicle_make"),
                "model": ticket.get("vehicle_model")
            }]
        )
        
        doc = draft_card.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.failure_cards.insert_one(doc)
        
        # Notify expert queue (would integrate with notification service)
        await self.notify_expert_queue(draft_card.failure_id)
        
        return {"draft_card_created": draft_card.failure_id}
```

---

## 5. AI Pipeline Integration

### 5.1 AI Matching Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI MATCHING PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT: FailureMatchRequest                                     │
│  • symptom_text: "Battery not charging beyond 80%"              │
│  • error_codes: ["E401", "E402"]                                │
│  • vehicle_make: "Ather"                                        │
│  • vehicle_model: "450X"                                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 STAGE 1: EXACT MATCH                     │   │
│  │                                                          │   │
│  │  Query: error_codes IN card.error_codes                  │   │
│  │  Score: 0.95 (high confidence for exact code match)      │   │
│  │  Speed: < 10ms                                           │   │
│  │                                                          │   │
│  │  IF exact_match.confidence > 0.95:                       │   │
│  │     RETURN exact_match (fast path)                       │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 STAGE 2: KEYWORD MATCH                   │   │
│  │                                                          │   │
│  │  Extract keywords from symptom_text                      │   │
│  │  Query: keywords IN card.keywords                        │   │
│  │  Score: 0.3 + (overlap_count * 0.1), max 0.8             │   │
│  │  Speed: < 50ms                                           │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 STAGE 3: SEMANTIC MATCH                  │   │
│  │                                                          │   │
│  │  Generate embedding: OpenAI text-embedding-3-small       │   │
│  │  Vector search: cosine similarity                        │   │
│  │  Score: similarity * 0.85                                │   │
│  │  Speed: < 200ms                                          │   │
│  │                                                          │   │
│  │  Note: Fallback to keyword hash if embedding fails       │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 STAGE 4: VEHICLE FILTER                  │   │
│  │                                                          │   │
│  │  Filter by: vehicle_models.make, vehicle_models.model    │   │
│  │  Boost: +0.1 for exact vehicle match                     │   │
│  │  Penalty: -0.2 for incompatible vehicles                 │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 ENSEMBLE RANKING                         │   │
│  │                                                          │   │
│  │  final_score = (                                         │   │
│  │      0.4 * exact_score +                                 │   │
│  │      0.3 * keyword_score +                               │   │
│  │      0.2 * semantic_score +                              │   │
│  │      0.1 * vehicle_bonus                                 │   │
│  │  ) * effectiveness_multiplier                            │   │
│  │                                                          │   │
│  │  effectiveness_multiplier = 0.5 + (effectiveness * 0.5)  │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  OUTPUT: List[FailureMatchResult] sorted by final_score         │
│  • failure_id                                                   │
│  • title                                                        │
│  • match_score (0-1)                                            │
│  • match_type (exact/semantic/partial)                          │
│  • matched_symptoms                                             │
│  • confidence_level                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Integration Points

```python
AI_INTEGRATION_POINTS = {
    "embedding_generation": {
        "model": "text-embedding-3-small",
        "provider": "OpenAI (via Emergent LLM Key)",
        "dimension": 1536,
        "use_cases": [
            "Failure card indexing",
            "Semantic symptom matching",
            "Similar failure detection"
        ]
    },
    
    "root_cause_analysis": {
        "model": "gpt-4o-mini",
        "provider": "OpenAI (via Emergent LLM Key)",
        "use_cases": [
            "Analyze technician observations",
            "Suggest root causes",
            "Generate failure card drafts"
        ]
    },
    
    "keyword_extraction": {
        "method": "TF-IDF + NER",
        "use_cases": [
            "Extract keywords from descriptions",
            "Build searchable index",
            "Auto-tag failure cards"
        ]
    }
}
```

---

## 6. Modular Backend Structure

### 6.1 Target Directory Structure

```
/app/backend/
├── server.py                 # Main FastAPI app + router registration
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
│
├── models/                   # Pydantic data models
│   ├── __init__.py
│   ├── failure_intelligence.py  # FailureCard, TechnicianAction, etc.
│   ├── ticket.py                # Ticket models
│   ├── employee.py              # Employee models
│   ├── inventory.py             # Inventory, Parts models
│   ├── invoice.py               # Invoice, Payment models
│   └── auth.py                  # User, Session models
│
├── routes/                   # API route handlers
│   ├── __init__.py
│   ├── auth.py                  # /api/auth/*
│   ├── failure_intelligence.py  # /api/efi/*
│   ├── tickets.py               # /api/tickets/*
│   ├── employees.py             # /api/employees/*
│   ├── inventory.py             # /api/inventory/*
│   ├── invoices.py              # /api/invoices/*
│   └── analytics.py             # /api/analytics/*
│
├── services/                 # Business logic & integrations
│   ├── __init__.py
│   ├── ai_matching.py           # AI failure matching service
│   ├── event_processor.py       # EFI event processing
│   ├── confidence_engine.py     # Confidence score calculations
│   ├── invoice_service.py       # PDF generation
│   └── notification_service.py  # Email/WhatsApp
│
├── utils/                    # Shared utilities
│   ├── __init__.py
│   ├── database.py              # MongoDB connection
│   ├── auth.py                  # JWT, password hashing
│   └── helpers.py               # Common helpers
│
└── tests/                    # Test files
    ├── __init__.py
    ├── test_failure_cards.py
    ├── test_matching.py
    └── test_events.py
```

### 6.2 Module Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND LAYER ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                      ROUTES LAYER                          │ │
│  │                  (API Endpoints)                           │ │
│  │                                                            │ │
│  │  • Receives HTTP requests                                  │ │
│  │  • Validates input (Pydantic)                              │ │
│  │  • Calls services                                          │ │
│  │  • Returns responses                                       │ │
│  │  • NO business logic here                                  │ │
│  └────────────────────────┬──────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                     SERVICES LAYER                         │ │
│  │                  (Business Logic)                          │ │
│  │                                                            │ │
│  │  • AI matching algorithms                                  │ │
│  │  • Event processing                                        │ │
│  │  • Confidence calculations                                 │ │
│  │  • External integrations (OpenAI, Resend, Twilio)          │ │
│  │  • Complex business rules                                  │ │
│  └────────────────────────┬──────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                     MODELS LAYER                           │ │
│  │                  (Data Structures)                         │ │
│  │                                                            │ │
│  │  • Pydantic models for validation                          │ │
│  │  • Enums for type safety                                   │ │
│  │  • Request/Response schemas                                │ │
│  │  • NO logic, just data shapes                              │ │
│  └────────────────────────┬──────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                      UTILS LAYER                           │ │
│  │                  (Shared Utilities)                        │ │
│  │                                                            │ │
│  │  • Database connection                                     │ │
│  │  • Authentication helpers                                  │ │
│  │  • Common functions                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Roadmap

### Phase 1: Core Data Models (Current)
- [x] FailureCard model defined
- [x] TechnicianAction model defined
- [ ] **Ticket model enhanced** with EFI fields
- [ ] **PartUsage model created**
- [ ] **KnowledgeRelationship model enhanced**

### Phase 2: Event-Driven Workflows
- [ ] Event processor service created
- [ ] Workflow 1: Ticket → AI Matching
- [ ] Workflow 2: New Failure → Draft Card
- [ ] Workflow 3: Resolution → Confidence Update

### Phase 3: AI Pipeline
- [ ] Semantic embedding integration (OpenAI)
- [ ] Enhanced matching algorithm
- [ ] Keyword extraction automation

### Phase 4: Backend Refactoring
- [ ] Extract models to `/models/`
- [ ] Extract routes to `/routes/`
- [ ] Create services layer
- [ ] Deprecate monolithic server.py

### Phase 5: Frontend Integration
- [ ] EFI Dashboard
- [ ] Failure Card CRUD UI
- [ ] Matching visualization
- [ ] Technician action forms

---

## Appendix: Quick Reference

### API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/efi/failure-cards` | POST | Create failure card |
| `/api/efi/failure-cards` | GET | List with filters |
| `/api/efi/failure-cards/{id}` | GET | Get single card |
| `/api/efi/failure-cards/{id}` | PUT | Update card |
| `/api/efi/failure-cards/{id}/approve` | POST | Approve for network |
| `/api/efi/match` | POST | AI failure matching |
| `/api/efi/match-ticket/{id}` | POST | Match ticket to cards |
| `/api/efi/technician-actions` | POST | Record action |
| `/api/efi/events` | GET | List events |
| `/api/efi/events/process` | POST | Process pending |

### Key Formulas

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

### Collections (MongoDB)

| Collection | Purpose |
|------------|---------|
| `failure_cards` | Core knowledge objects |
| `tickets` | Service tickets |
| `technician_actions` | Repair records |
| `part_usage` | Parts consumption |
| `knowledge_relations` | Graph edges |
| `efi_events` | Event log |
| `symptoms` | Symptom library |
