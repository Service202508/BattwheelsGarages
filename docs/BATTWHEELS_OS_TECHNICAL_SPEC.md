# Battwheels OS — Technical Specification v2.0

## EV Failure Intelligence Platform Architecture

**Document Version:** 2.0  
**Classification:** Proprietary — Battwheels Services Pvt. Ltd.  
**Last Updated:** February 2026  

---

# Executive Summary

Battwheels OS is a self-improving service platform that transforms every EV repair into network-wide intelligence. The core value proposition—**One EV Failure Solved. Thousands Prevented.**—requires an architecture that captures field discoveries in real-time, converts them into structured repair knowledge, and synchronizes this intelligence across hundreds of distributed locations without bottlenecks.

This specification defines the production-grade infrastructure required to deliver on that promise at scale.

---

# 1. System Architecture

## 1.1 High-Level Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BATTWHEELS OS PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   GARAGES   │  │ DIAGNOSTICS │  │ MARKETPLACE │  │     EFI     │        │
│  │ OPERATIONS  │  │     AI      │  │     API     │  │    CORE     │        │
│  │   Domain    │  │   Domain    │  │   Domain    │  │   Domain    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                   │                                        │
│                    ┌──────────────▼──────────────┐                         │
│                    │     EVENT BUS (Kafka)       │                         │
│                    │   Central Nervous System    │                         │
│                    └──────────────┬──────────────┘                         │
│                                   │                                        │
│         ┌─────────────────────────┼─────────────────────────┐              │
│         ▼                         ▼                         ▼              │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐         │
│  │  MongoDB    │          │   Redis     │          │ Elasticsearch│         │
│  │  Primary    │          │   Cache     │          │   Search     │         │
│  │  Datastore  │          │   Layer     │          │   Engine     │         │
│  └─────────────┘          └─────────────┘          └─────────────┘         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                         EDGE LAYER (Per Location)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Location   │  │  Location   │  │  Location   │  │  Location   │        │
│  │   Agent     │  │   Agent     │  │   Agent     │  │   Agent     │        │
│  │  (Delhi)    │  │ (Mumbai)    │  │ (Bangalore) │  │   (...)     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1.2 Domain Service Architecture

### 1.2.1 EFI Core (Failure Intelligence Engine)

The central intelligence system. All other domains feed into and consume from EFI.

```
┌─────────────────────────────────────────────────────────────────┐
│                        EFI CORE DOMAIN                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Failure Card    │    │   AI Matching    │                  │
│  │    Service       │    │    Service       │                  │
│  │                  │    │                  │                  │
│  │  - Create/CRUD   │    │  - 4-Stage       │                  │
│  │  - Approve       │    │    Pipeline      │                  │
│  │  - Deprecate     │    │  - Embedding     │                  │
│  │  - Version       │    │    Generation    │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                            │
│           └───────────┬───────────┘                            │
│                       ▼                                        │
│           ┌──────────────────┐                                 │
│           │   Confidence     │                                 │
│           │     Engine       │                                 │
│           │                  │                                 │
│           │  - Score Update  │                                 │
│           │  - History Track │                                 │
│           │  - Effectiveness │                                 │
│           └────────┬─────────┘                                 │
│                    │                                           │
│                    ▼                                           │
│           ┌──────────────────┐                                 │
│           │    Pattern       │                                 │
│           │    Detection     │                                 │
│           │                  │                                 │
│           │  - Emerging      │                                 │
│           │  - Clustering    │                                 │
│           │  - Alerts        │                                 │
│           └──────────────────┘                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Technology Choices:**
- **Language:** Python 3.11+ with FastAPI
- **Primary Store:** MongoDB (document flexibility for failure cards)
- **Search:** Elasticsearch (semantic search, fuzzy matching)
- **Vector Store:** MongoDB Atlas Vector Search or Pinecone (embedding similarity)
- **Cache:** Redis (hot failure cards, match results)

**Rationale:** Failure cards have complex, nested structures that evolve. Document databases handle schema evolution better than relational. The 4-stage matching pipeline requires both exact matching (signatures) and fuzzy matching (semantic), necessitating Elasticsearch integration.

### 1.2.2 Garages Operations Domain

Manages multi-location service workflows, technician assignments, and job lifecycle.

```
┌─────────────────────────────────────────────────────────────────┐
│                   GARAGES OPERATIONS DOMAIN                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Location   │  │   Ticket     │  │  Technician  │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           ▼                                    │
│                  ┌──────────────┐                              │
│                  │  Scheduling  │                              │
│                  │    Engine    │                              │
│                  └──────────────┘                              │
│                                                                 │
│  Events Emitted:                                               │
│  - TICKET_CREATED → Triggers EFI AI matching                   │
│  - TICKET_CLOSED → Triggers Confidence update                  │
│  - TECHNICIAN_ASSIGNED → Resource allocation                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2.3 Diagnostics AI Domain

Provides automated root cause analysis and predictive diagnostics.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DIAGNOSTICS AI DOMAIN                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  RCA Engine      │    │  Predictive      │                  │
│  │                  │    │  Diagnostics     │                  │
│  │  - Fault Tree    │    │                  │                  │
│  │    Analysis      │    │  - Failure       │                  │
│  │  - Root Cause    │    │    Probability   │                  │
│  │    Inference     │    │  - Maintenance   │                  │
│  │  - Evidence      │    │    Prediction    │                  │
│  │    Scoring       │    │                  │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                            │
│           └───────────┬───────────┘                            │
│                       ▼                                        │
│           ┌──────────────────┐                                 │
│           │  Diagnostic      │                                 │
│           │  Tree Generator  │                                 │
│           │                  │                                 │
│           │  - Step-by-step  │                                 │
│           │  - Dynamic path  │                                 │
│           │  - Evidence req  │                                 │
│           └──────────────────┘                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2.4 Marketplace API Domain

External integrations for parts, vendors, and third-party services.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MARKETPLACE API DOMAIN                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Parts     │  │    Vendor    │  │   External   │          │
│  │  Inventory   │  │   Services   │  │ Diagnostics  │          │
│  │    API       │  │     API      │  │    Tools     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           ▼                                    │
│                  ┌──────────────┐                              │
│                  │  Integration │                              │
│                  │    Gateway   │                              │
│                  │              │                              │
│                  │  - Rate      │                              │
│                  │    Limiting  │                              │
│                  │  - Circuit   │                              │
│                  │    Breaker   │                              │
│                  │  - Retry     │                              │
│                  └──────────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 1.3 Event-Driven Architecture

All domain communication flows through a central event bus.

```python
# Core Event Types
class EventType(Enum):
    # Ticket Lifecycle
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_CLOSED = "ticket.closed"
    TICKET_ASSIGNED = "ticket.assigned"
    
    # EFI Core
    FAILURE_CARD_CREATED = "failure_card.created"
    FAILURE_CARD_APPROVED = "failure_card.approved"
    FAILURE_CARD_USED = "failure_card.used"
    FAILURE_CARD_DEPRECATED = "failure_card.deprecated"
    
    # Intelligence
    NEW_FAILURE_DETECTED = "failure.new_detected"
    MATCH_COMPLETED = "match.completed"
    CONFIDENCE_UPDATED = "confidence.updated"
    PATTERN_DETECTED = "pattern.detected"
    
    # Sync
    NETWORK_SYNC_REQUIRED = "sync.required"
    LOCATION_ONLINE = "location.online"
    LOCATION_OFFLINE = "location.offline"
```

**Event Flow Example: New Failure Discovery**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Technician │    │   Ticket    │    │    EFI      │    │   Network   │
│   closes    │───▶│  Service    │───▶│   Service   │───▶│    Sync     │
│   ticket    │    │             │    │             │    │             │
└─────────────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
                          │                  │                  │
                   TICKET_CLOSED      CONFIDENCE_       NETWORK_SYNC_
                          │           UPDATED +         REQUIRED
                          │           NEW_FAILURE_            │
                          │           DETECTED                │
                          ▼                  ▼                 ▼
                   ┌─────────────────────────────────────────────┐
                   │              EVENT BUS (Kafka)              │
                   │                                             │
                   │  Topic: efi.events                          │
                   │  Partitions: By location_id                 │
                   │  Retention: 7 days                          │
                   │  Replication: 3                             │
                   └─────────────────────────────────────────────┘
```

## 1.4 API Gateway Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       API GATEWAY                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                   Kong / Envoy                        │      │
│  │                                                       │      │
│  │  Routes:                                              │      │
│  │  /api/tickets/*     → Garages Operations             │      │
│  │  /api/efi/*         → EFI Core                       │      │
│  │  /api/diagnostics/* → Diagnostics AI                 │      │
│  │  /api/marketplace/* → Marketplace API                │      │
│  │  /api/sync/*        → Synchronization Service        │      │
│  │                                                       │      │
│  │  Cross-Cutting:                                       │      │
│  │  - JWT Validation                                     │      │
│  │  - Rate Limiting (per location, per user)            │      │
│  │  - Request Logging                                    │      │
│  │  - Circuit Breaking                                   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# 2. Failure Intelligence Pipeline

## 2.1 End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FAILURE INTELLIGENCE PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAGE 1: FIELD DETECTION                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  Technician reports issue → Ticket created with:                │       │
│  │  - Symptom description (free text)                              │       │
│  │  - Error codes (OBD/proprietary)                                │       │
│  │  - Vehicle info (make, model, VIN)                              │       │
│  │  - Photos/videos (optional)                                     │       │
│  │  - Environmental conditions                                     │       │
│  │                                                                  │       │
│  │  Event: TICKET_CREATED                                          │       │
│  └──────────────────────────────────┬──────────────────────────────┘       │
│                                     │                                       │
│                                     ▼                                       │
│  STAGE 2: AI MATCHING                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  4-Stage Matching Pipeline (< 50ms total):                      │       │
│  │                                                                  │       │
│  │  1. SIGNATURE MATCH (< 5ms)                                     │       │
│  │     - Hash(symptoms + error_codes + subsystem)                  │       │
│  │     - Exact match against signature_hash index                  │       │
│  │     - Score: 0.95 (highest confidence)                          │       │
│  │                                                                  │       │
│  │  2. SUBSYSTEM + VEHICLE FILTER (< 10ms)                         │       │
│  │     - Filter by subsystem_category                              │       │
│  │     - Filter by vehicle_models[].make/model                     │       │
│  │     - Score bonus for exact vehicle match                       │       │
│  │     - Score: 0.70-0.85                                          │       │
│  │                                                                  │       │
│  │  3. SEMANTIC SIMILARITY (< 25ms)                                │       │
│  │     - Generate embedding: embed(symptom_text)                   │       │
│  │     - Vector similarity search (cosine)                         │       │
│  │     - Top-k retrieval from vector index                         │       │
│  │     - Score: 0.50-0.75                                          │       │
│  │                                                                  │       │
│  │  4. KEYWORD FALLBACK (< 10ms)                                   │       │
│  │     - Elasticsearch full-text search                            │       │
│  │     - Fuzzy matching on title, description                      │       │
│  │     - Score: 0.30-0.50                                          │       │
│  │                                                                  │       │
│  │  Output: Top 5 ranked failure cards                             │       │
│  │  Event: MATCH_COMPLETED                                         │       │
│  └──────────────────────────────────┬──────────────────────────────┘       │
│                                     │                                       │
│                                     ▼                                       │
│  STAGE 3: TECHNICIAN DIAGNOSIS                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  Technician reviews suggested cards:                            │       │
│  │  - Follows diagnostic_tree steps                                │       │
│  │  - Records observations at each step                            │       │
│  │  - Marks rejected_hypotheses with reasoning                     │       │
│  │  - Selects best-matching card OR flags as "new failure"         │       │
│  │                                                                  │       │
│  │  Data Captured:                                                 │       │
│  │  - attempted_diagnostics[]: {step, result, timestamp}           │       │
│  │  - rejected_hypotheses[]: {card_id, reason, ruled_out_at}       │       │
│  │  - observations: {measurements, photos, notes}                  │       │
│  │  - selected_failure_card: card_id | null                        │       │
│  │                                                                  │       │
│  │  Event: TECHNICIAN_ACTION_COMPLETED                             │       │
│  └──────────────────────────────────┬──────────────────────────────┘       │
│                                     │                                       │
│                                     ▼                                       │
│  STAGE 4: RESOLUTION & FEEDBACK                                            │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  Ticket closure with outcome:                                   │       │
│  │                                                                  │       │
│  │  IF selected_failure_card exists:                               │       │
│  │    - Update card.usage_count++                                  │       │
│  │    - Update card.success_count or failure_count                 │       │
│  │    - Recalculate confidence_score                               │       │
│  │    - Append to confidence_history[]                             │       │
│  │    - Event: CONFIDENCE_UPDATED                                  │       │
│  │                                                                  │       │
│  │  IF no card selected AND resolution_outcome = "success":        │       │
│  │    - Flag as NEW UNDOCUMENTED FAILURE                           │       │
│  │    - Auto-create DRAFT failure card                             │       │
│  │    - Queue for expert review                                    │       │
│  │    - Event: NEW_FAILURE_DETECTED                                │       │
│  │                                                                  │       │
│  │  Event: TICKET_CLOSED                                           │       │
│  └──────────────────────────────────┬──────────────────────────────┘       │
│                                     │                                       │
│                                     ▼                                       │
│  STAGE 5: NETWORK SYNCHRONIZATION                                          │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  On NEW_FAILURE_DETECTED or FAILURE_CARD_APPROVED:              │       │
│  │                                                                  │       │
│  │  1. Central store updated                                       │       │
│  │  2. Elasticsearch index refreshed                               │       │
│  │  3. Vector embeddings regenerated                               │       │
│  │  4. Cache invalidated (Redis)                                   │       │
│  │  5. NETWORK_SYNC_REQUIRED event broadcast                       │       │
│  │  6. All location agents receive update                          │       │
│  │  7. Local caches refreshed                                      │       │
│  │                                                                  │       │
│  │  Time to availability: < 60 seconds                             │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Failure Card Data Structure

```python
class FailureCard:
    """
    Core knowledge unit in the EFI system.
    Represents a documented, reusable repair solution.
    """
    
    # Identity
    failure_id: str              # "fc_" + uuid4().hex[:12]
    version: int                 # Increments on each update
    
    # Classification
    title: str                   # Human-readable title
    description: str             # Detailed description
    subsystem_category: str      # battery, motor, controller, bms, charger, wiring
    failure_mode: str            # degradation, sudden_failure, intermittent, etc.
    
    # Failure Signature (for fast matching)
    failure_signature: {
        primary_symptoms: List[str],     # Normalized symptom codes
        error_codes: List[str],          # OBD codes, proprietary codes
        subsystem: str,
        failure_mode: str,
        temperature_range: str,          # cold, normal, hot
        load_condition: str              # idle, low, high, peak
    }
    signature_hash: str          # SHA256(signature)[:16] for O(1) lookup
    
    # Diagnostic Intelligence
    diagnostic_tree: {
        root: {
            question: str,
            evidence_required: str,
            branches: [
                {
                    condition: str,
                    next_step: str | "DIAGNOSIS_CONFIRMED",
                    confidence_boost: float
                }
            ]
        },
        steps: Dict[str, DiagnosticStep]
    }
    
    # Resolution Intelligence
    root_cause: str
    root_cause_details: str
    secondary_causes: List[str]
    
    verification_steps: List[{
        step_number: int,
        description: str,
        tools_required: List[str],
        expected_result: str,
        safety_warnings: List[str]
    }]
    
    resolution_steps: List[{
        step_number: int,
        description: str,
        tools_required: List[str],
        parts_required: List[str],
        estimated_time_minutes: int,
        skill_level: str,        # junior, mid, senior, specialist
        safety_warnings: List[str]
    }]
    
    required_parts: List[{
        part_id: str,
        part_name: str,
        quantity: int,
        is_mandatory: bool,
        alternatives: List[str],
        estimated_cost: float
    }]
    
    # Vehicle Compatibility
    vehicle_models: List[{
        make: str,
        model: str,
        year_start: int,
        year_end: int,
        variant: str
    }]
    universal_failure: bool      # Applies to all EVs
    
    # Environmental Conditions
    failure_conditions: List[{
        condition_type: str,     # temperature, humidity, load, terrain
        value_range: str,
        is_trigger: bool
    }]
    
    # Confidence & Effectiveness (Learning Metrics)
    confidence_score: float      # 0.0 - 1.0
    confidence_level: str        # low, medium, high, verified
    confidence_history: List[{
        timestamp: datetime,
        previous_score: float,
        new_score: float,
        change_reason: str,      # usage_success, usage_failure, expert_review, etc.
        ticket_id: str,
        technician_id: str
    }]
    
    usage_count: int
    success_count: int
    failure_count: int
    effectiveness_score: float   # success_count / usage_count + usage_bonus
    
    # Lifecycle
    status: str                  # draft, pending_review, approved, deprecated
    source_type: str             # field_discovery, oem_input, pattern_detection
    source_ticket_id: str
    
    created_at: datetime
    updated_at: datetime
    first_detected_at: datetime
    last_used_at: datetime
    approved_at: datetime
    approved_by: str
    
    # Search Optimization
    keywords: List[str]          # Auto-extracted + manual
    tags: List[str]
    embedding_vector: List[float]  # 1536-dim for text-embedding-3-small
    
    # Cost Estimates
    estimated_repair_time_minutes: int
    estimated_parts_cost: float
    estimated_labor_cost: float
    estimated_total_cost: float
```

## 2.3 Indexing Strategy

```yaml
# MongoDB Indexes
failure_cards:
  indexes:
    - name: "signature_hash_idx"
      keys: {signature_hash: 1}
      unique: true
      purpose: "O(1) signature matching"
    
    - name: "subsystem_status_idx"
      keys: {subsystem_category: 1, status: 1, confidence_score: -1}
      purpose: "Stage 2 filtering"
    
    - name: "vehicle_model_idx"
      keys: {"vehicle_models.make": 1, "vehicle_models.model": 1}
      purpose: "Vehicle compatibility lookup"
    
    - name: "text_search_idx"
      keys: {title: "text", description: "text", root_cause: "text", keywords: "text"}
      purpose: "Stage 4 keyword fallback"
    
    - name: "effectiveness_idx"
      keys: {status: 1, effectiveness_score: -1, usage_count: -1}
      purpose: "Top performing cards dashboard"

# Elasticsearch Index
failure_cards_search:
  mappings:
    properties:
      failure_id: {type: keyword}
      title: {type: text, analyzer: ev_symptom_analyzer}
      description: {type: text, analyzer: ev_symptom_analyzer}
      symptom_text: {type: text, analyzer: ev_symptom_analyzer}
      root_cause: {type: text}
      keywords: {type: keyword}
      error_codes: {type: keyword}
      subsystem_category: {type: keyword}
      vehicle_models: {type: nested}
      confidence_score: {type: float}
      effectiveness_score: {type: float}
      embedding_vector: {type: dense_vector, dims: 1536, similarity: cosine}

# Custom Analyzer for EV Domain
ev_symptom_analyzer:
  type: custom
  tokenizer: standard
  filter:
    - lowercase
    - ev_synonym_filter  # "bms" = "battery management system"
    - ev_stopwords       # Remove common non-diagnostic words
```

## 2.4 Real-Time Matching API

```python
@router.post("/efi/match")
async def match_failure(request: FailureMatchRequest) -> FailureMatchResponse:
    """
    4-Stage AI Matching Pipeline
    
    SLA: < 50ms p99 latency
    """
    start_time = time.perf_counter()
    
    # Stage 1: Signature Match (fastest path)
    signature_hash = compute_signature_hash(request)
    stage1_matches = await db.failure_cards.find(
        {"signature_hash": signature_hash, "status": "approved"},
        {"_id": 0, "embedding_vector": 0}
    ).limit(5).to_list(5)
    
    if stage1_matches and stage1_matches[0].get("confidence_score", 0) > 0.8:
        # High-confidence exact match - return immediately
        return FailureMatchResponse(
            matches=stage1_matches,
            match_type="signature",
            processing_time_ms=(time.perf_counter() - start_time) * 1000
        )
    
    # Stage 2: Subsystem + Vehicle Filter
    stage2_query = build_subsystem_vehicle_query(request)
    stage2_matches = await db.failure_cards.find(
        stage2_query, {"_id": 0, "embedding_vector": 0}
    ).sort("effectiveness_score", -1).limit(20).to_list(20)
    
    # Stage 3: Semantic Similarity
    embedding = await generate_embedding(request.symptom_text)
    stage3_matches = await vector_search(
        collection="failure_cards",
        vector=embedding,
        filter={"status": "approved"},
        limit=10
    )
    
    # Stage 4: Keyword Fallback
    stage4_matches = await elasticsearch.search(
        index="failure_cards_search",
        query=build_fuzzy_query(request.symptom_text, request.error_codes)
    )
    
    # Merge and rank results
    all_matches = merge_and_rank(
        stage1_matches, stage2_matches, stage3_matches, stage4_matches
    )
    
    return FailureMatchResponse(
        matches=all_matches[:5],
        matching_stages_used=get_stages_used(),
        processing_time_ms=(time.perf_counter() - start_time) * 1000
    )
```

---

# 3. Integration Layer

## 3.1 Domain Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                              ┌─────────────────┐      │
│  │     GARAGES     │                              │       EFI       │      │
│  │   OPERATIONS    │                              │      CORE       │      │
│  └────────┬────────┘                              └────────┬────────┘      │
│           │                                                │               │
│           │  TICKET_CREATED ─────────────────────────────▶│               │
│           │  (symptom_text, error_codes, vehicle)         │               │
│           │                                                │               │
│           │◀───────────────────────────────── MATCH_RESULT│               │
│           │  (suggested_failure_cards[])                   │               │
│           │                                                │               │
│           │  TICKET_CLOSED ──────────────────────────────▶│               │
│           │  (resolution_outcome, selected_card)          │               │
│           │                                                │               │
│           │◀──────────────────────────── CONFIDENCE_UPDATED│              │
│           │  (card_id, new_score)                          │               │
│           │                                                │               │
│  ┌────────┴────────┐                              ┌────────┴────────┐      │
│  │   DIAGNOSTICS   │                              │   MARKETPLACE   │      │
│  │       AI        │                              │      API        │      │
│  └────────┬────────┘                              └────────┬────────┘      │
│           │                                                │               │
│           │  DIAGNOSTIC_REQUEST ─────────────────────────▶│               │
│           │  (failure_card_id, observations)              │               │
│           │                                                │               │
│           │◀─────────────────────────── DIAGNOSTIC_RESULT │               │
│           │  (next_step, evidence_required)               │               │
│           │                                                │               │
│           │                     PARTS_LOOKUP ─────────────▶│               │
│           │                     (required_parts[])         │               │
│           │                                                │               │
│           │◀──────────────────────────── PARTS_AVAILABILITY│              │
│           │                     (available, alternatives)  │               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.2 Integration Contracts

### 3.2.1 Garages Operations → EFI Core

```python
# Event: TICKET_CREATED
class TicketCreatedEvent:
    ticket_id: str
    location_id: str
    technician_id: str
    
    # Required for AI matching
    title: str
    description: str
    symptom_text: str
    error_codes: List[str]
    
    # Vehicle context
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    vehicle_vin: str
    
    # Environmental context
    temperature_ambient: float
    vehicle_load_state: str
    
    timestamp: datetime

# Response: Match Result (async via event)
class MatchResultEvent:
    ticket_id: str
    suggested_failure_cards: List[{
        failure_id: str,
        title: str,
        match_score: float,
        match_type: str,
        confidence_score: float,
        resolution_summary: str
    }]
    ai_match_timestamp: datetime
    processing_time_ms: float
```

### 3.2.2 EFI Core → Diagnostics AI

```python
# Request: Diagnostic Session
class DiagnosticSessionRequest:
    ticket_id: str
    failure_card_id: str
    current_step: str
    observations: List[{
        step_id: str,
        observation: str,
        measurement: str,
        evidence_photo_url: str
    }]

# Response: Next Diagnostic Step
class DiagnosticStepResponse:
    next_step_id: str
    question: str
    evidence_required: str
    expected_outcomes: List[{
        outcome: str,
        leads_to: str,
        confidence_impact: float
    }]
    alternative_hypotheses: List[str]
```

### 3.2.3 EFI Core → Marketplace API

```python
# Request: Parts Availability
class PartsLookupRequest:
    location_id: str
    required_parts: List[{
        part_id: str,
        part_name: str,
        quantity: int,
        priority: str  # critical, preferred, optional
    }]
    vehicle_make: str
    vehicle_model: str

# Response: Parts Availability
class PartsAvailabilityResponse:
    available_parts: List[{
        part_id: str,
        in_stock: int,
        location_stock: int,
        network_stock: int,
        unit_price: float,
        eta_if_ordered: str
    }]
    alternatives: List[{
        original_part_id: str,
        alternative_part_id: str,
        compatibility_score: float,
        price_difference: float
    }]
    nearest_location_with_stock: str
```

## 3.3 Error Handling & Fallbacks

```python
class IntegrationGateway:
    """
    Central gateway for all cross-domain integrations.
    Implements circuit breaker, retry, and fallback patterns.
    """
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exceptions=[TimeoutError, ConnectionError]
        )
    
    @circuit_breaker
    @retry(max_attempts=3, backoff=exponential)
    async def call_efi_matching(self, request: MatchRequest) -> MatchResponse:
        """
        Call EFI matching service with resilience.
        
        Fallback behavior:
        1. If EFI service down: Return cached top-10 cards for subsystem
        2. If cache miss: Return empty suggestions with manual_review flag
        """
        try:
            response = await self.efi_client.match(request)
            await self.cache.set(f"match:{request.signature_hash}", response, ttl=3600)
            return response
        except CircuitBreakerOpen:
            # Fallback to cache
            cached = await self.cache.get(f"match:{request.signature_hash}")
            if cached:
                return cached.with_flag(source="cache", stale=True)
            
            # Fallback to top cards for subsystem
            top_cards = await self.cache.get(f"top_cards:{request.subsystem}")
            if top_cards:
                return MatchResponse(
                    matches=top_cards,
                    source="fallback",
                    manual_review_required=True
                )
            
            return MatchResponse(matches=[], manual_review_required=True)
```

---

# 4. Scalability Design

## 4.1 Database Architecture for Scale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DATABASE SCALABILITY DESIGN                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    MONGODB CLUSTER                               │       │
│  │                                                                  │       │
│  │  GLOBAL COLLECTIONS (Single Source of Truth)                    │       │
│  │  ┌─────────────────────────────────────────────────────────┐   │       │
│  │  │  failure_cards        │  Central knowledge base          │   │       │
│  │  │  symptoms             │  Symptom library                 │   │       │
│  │  │  knowledge_relations  │  Graph edges                     │   │       │
│  │  │  emerging_patterns    │  Pattern detection results       │   │       │
│  │  └─────────────────────────────────────────────────────────┘   │       │
│  │                                                                  │       │
│  │  LOCATION-SHARDED COLLECTIONS (Sharded by location_id)         │       │
│  │  ┌─────────────────────────────────────────────────────────┐   │       │
│  │  │  tickets              │  Shard key: {location_id: 1}     │   │       │
│  │  │  technician_actions   │  Shard key: {location_id: 1}     │   │       │
│  │  │  part_usage           │  Shard key: {location_id: 1}     │   │       │
│  │  │  inventory            │  Shard key: {location_id: 1}     │   │       │
│  │  │  attendance           │  Shard key: {location_id: 1}     │   │       │
│  │  └─────────────────────────────────────────────────────────┘   │       │
│  │                                                                  │       │
│  │  Topology:                                                      │       │
│  │  - Config servers: 3 (replica set)                              │       │
│  │  - Shard 1: 3 replicas (locations 001-100)                      │       │
│  │  - Shard 2: 3 replicas (locations 101-200)                      │       │
│  │  - Shard 3: 3 replicas (locations 201-300)                      │       │
│  │  - ... (add shards as locations grow)                           │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                      REDIS CLUSTER                               │       │
│  │                                                                  │       │
│  │  HOT DATA CACHE                                                 │       │
│  │  ┌─────────────────────────────────────────────────────────┐   │       │
│  │  │  failure_cards:approved     │  All approved cards (5MB)  │   │       │
│  │  │  failure_cards:hot          │  Top 100 most used         │   │       │
│  │  │  match_results:{hash}       │  Recent match results      │   │       │
│  │  │  location:{id}:active_tickets│  Per-location hot data    │   │       │
│  │  └─────────────────────────────────────────────────────────┘   │       │
│  │                                                                  │       │
│  │  Configuration:                                                 │       │
│  │  - 6 nodes (3 masters, 3 replicas)                              │       │
│  │  - 16GB RAM per node                                            │       │
│  │  - LRU eviction for match_results                               │       │
│  │  - No eviction for failure_cards (critical data)                │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4.2 Horizontal Scaling Strategy

### 4.2.1 Stateless Service Scaling

```yaml
# Kubernetes HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: efi-matching-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: efi-matching-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: match_requests_per_second
        target:
          type: AverageValue
          averageValue: 100
```

### 4.2.2 Load Distribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LOAD DISTRIBUTION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Request Flow:                                                             │
│                                                                             │
│  Client ──▶ CDN/Edge ──▶ Load Balancer ──▶ API Gateway ──▶ Service         │
│                │              │                 │             │            │
│                │              │                 │             │            │
│         Static assets    Round-robin      Rate limiting   Instance        │
│         (JS, CSS)        + health check   + JWT validation selection      │
│                                                                             │
│  Routing Strategy:                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  READ requests (GET /api/efi/*)                                 │       │
│  │    → Any healthy instance (round-robin)                         │       │
│  │    → Redis cache check first                                    │       │
│  │    → MongoDB read from nearest replica                          │       │
│  │                                                                  │       │
│  │  WRITE requests (POST/PUT /api/efi/*)                           │       │
│  │    → Primary instance for consistency                           │       │
│  │    → MongoDB write to primary                                   │       │
│  │    → Async cache invalidation                                   │       │
│  │    → Async event emission                                       │       │
│  │                                                                  │       │
│  │  MATCH requests (POST /api/efi/match)                           │       │
│  │    → Dedicated matching pool (CPU-optimized instances)          │       │
│  │    → Parallel stage execution                                   │       │
│  │    → Result caching for identical signatures                    │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4.3 Performance Optimization

### 4.3.1 Caching Strategy

```python
class CacheManager:
    """
    Multi-tier caching for EFI system.
    
    Tier 1: Local in-memory (LRU, 1000 items, ~100MB)
    Tier 2: Redis cluster (shared, 16GB)
    Tier 3: MongoDB (source of truth)
    """
    
    # Cache configuration
    CACHE_CONFIG = {
        "failure_cards:approved": {
            "ttl": 3600,           # 1 hour
            "invalidate_on": ["FAILURE_CARD_APPROVED", "FAILURE_CARD_DEPRECATED"],
            "warm_on_startup": True
        },
        "failure_cards:hot": {
            "ttl": 300,            # 5 minutes
            "max_items": 100,
            "rank_by": "usage_count"
        },
        "match_results": {
            "ttl": 600,            # 10 minutes
            "key_format": "match:{signature_hash}",
            "eviction": "lru"
        },
        "embeddings": {
            "ttl": 86400,          # 24 hours
            "key_format": "embed:{text_hash}",
            "storage": "redis"     # Not in local cache (too large)
        }
    }
    
    async def get_failure_card(self, failure_id: str) -> FailureCard:
        # Tier 1: Local cache
        if card := self.local_cache.get(failure_id):
            return card
        
        # Tier 2: Redis
        if card := await self.redis.get(f"card:{failure_id}"):
            self.local_cache.set(failure_id, card)
            return card
        
        # Tier 3: MongoDB
        card = await self.db.failure_cards.find_one({"failure_id": failure_id})
        if card:
            await self.redis.set(f"card:{failure_id}", card, ex=3600)
            self.local_cache.set(failure_id, card)
        
        return card
```

### 4.3.2 Query Optimization

```python
# Optimized aggregation pipeline for top-performing cards
EFFECTIVENESS_REPORT_PIPELINE = [
    # Stage 1: Filter to approved cards with usage
    {"$match": {"status": "approved", "usage_count": {"$gt": 0}}},
    
    # Stage 2: Project only needed fields (reduce memory)
    {"$project": {
        "_id": 0,
        "failure_id": 1,
        "title": 1,
        "subsystem_category": 1,
        "usage_count": 1,
        "success_count": 1,
        "effectiveness_score": 1,
        "confidence_score": 1
    }},
    
    # Stage 3: Sort by effectiveness
    {"$sort": {"effectiveness_score": -1}},
    
    # Stage 4: Limit results
    {"$limit": 50}
]

# Index hint for optimal execution
db.failure_cards.aggregate(
    EFFECTIVENESS_REPORT_PIPELINE,
    hint="effectiveness_idx"
)
```

## 4.4 Scaling from 5 to 500 Locations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCALING ROADMAP                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: 5-20 Locations (Current)                                         │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Infrastructure:                                                 │       │
│  │  - Single MongoDB replica set (3 nodes)                         │       │
│  │  - Single Redis cluster (6 nodes)                               │       │
│  │  - 3-5 API instances                                            │       │
│  │  - Single Kafka cluster                                         │       │
│  │                                                                  │       │
│  │  Estimated Capacity:                                            │       │
│  │  - 500 concurrent tickets                                       │       │
│  │  - 50 matches/second                                            │       │
│  │  - 100 technicians                                              │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  PHASE 2: 20-100 Locations                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Infrastructure Changes:                                        │       │
│  │  - Enable MongoDB sharding (2 shards)                           │       │
│  │  - Add Elasticsearch cluster (3 nodes)                          │       │
│  │  - Scale API instances (10-15)                                  │       │
│  │  - Add dedicated matching pool                                  │       │
│  │                                                                  │       │
│  │  Estimated Capacity:                                            │       │
│  │  - 2,500 concurrent tickets                                     │       │
│  │  - 200 matches/second                                           │       │
│  │  - 500 technicians                                              │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  PHASE 3: 100-300 Locations                                                │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Infrastructure Changes:                                        │       │
│  │  - MongoDB sharding (5 shards)                                  │       │
│  │  - Redis cluster expansion (12 nodes)                           │       │
│  │  - Multi-region deployment (2 regions)                          │       │
│  │  - Edge caching at regional level                               │       │
│  │  - Dedicated ML inference cluster                               │       │
│  │                                                                  │       │
│  │  Estimated Capacity:                                            │       │
│  │  - 7,500 concurrent tickets                                     │       │
│  │  - 500 matches/second                                           │       │
│  │  - 1,500 technicians                                            │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  PHASE 4: 300-500+ Locations                                               │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Infrastructure Changes:                                        │       │
│  │  - MongoDB sharding (10+ shards)                                │       │
│  │  - Multi-region active-active                                   │       │
│  │  - Global CDN for static assets                                 │       │
│  │  - Regional API gateways                                        │       │
│  │  - Dedicated vector search cluster                              │       │
│  │                                                                  │       │
│  │  Estimated Capacity:                                            │       │
│  │  - 15,000+ concurrent tickets                                   │       │
│  │  - 1,000+ matches/second                                        │       │
│  │  - 3,000+ technicians                                           │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 5. AI/ML Models

## 5.1 Model Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI/ML MODEL ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                  EMBEDDING MODEL                                 │       │
│  │                                                                  │       │
│  │  Model: text-embedding-3-small (OpenAI) or all-MiniLM-L6-v2     │       │
│  │  Dimensions: 1536 (OpenAI) or 384 (local)                       │       │
│  │  Input: Symptom text + error codes + vehicle context            │       │
│  │  Output: Dense vector for similarity search                     │       │
│  │                                                                  │       │
│  │  Use cases:                                                     │       │
│  │  - Failure card embedding (offline batch)                       │       │
│  │  - Query embedding (real-time)                                  │       │
│  │  - Semantic similarity (Stage 3 matching)                       │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                  ROOT CAUSE CLASSIFIER                           │       │
│  │                                                                  │       │
│  │  Architecture: Fine-tuned BERT or XGBoost ensemble              │       │
│  │  Input: Symptom features + diagnostic observations              │       │
│  │  Output: Probability distribution over root causes              │       │
│  │                                                                  │       │
│  │  Features:                                                      │       │
│  │  - Error code presence (binary vector)                          │       │
│  │  - Symptom keywords (TF-IDF)                                    │       │
│  │  - Vehicle attributes (categorical encoded)                     │       │
│  │  - Environmental conditions (numerical)                         │       │
│  │  - Historical patterns (aggregated features)                    │       │
│  │                                                                  │       │
│  │  Training:                                                      │       │
│  │  - Dataset: Closed tickets with confirmed root causes           │       │
│  │  - Labels: Failure card IDs (multi-class)                       │       │
│  │  - Retraining: Weekly batch with new confirmed cases            │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                  PATTERN DETECTION MODEL                         │       │
│  │                                                                  │       │
│  │  Architecture: DBSCAN clustering + anomaly detection            │       │
│  │  Input: Recent unresolved tickets + rejected hypotheses         │       │
│  │  Output: Emerging pattern candidates                            │       │
│  │                                                                  │       │
│  │  Pipeline:                                                      │       │
│  │  1. Embed unresolved ticket symptoms                            │       │
│  │  2. Cluster by similarity (DBSCAN, eps=0.3)                     │       │
│  │  3. Filter clusters with count > threshold (3)                  │       │
│  │  4. Extract common features (error codes, vehicle, subsystem)   │       │
│  │  5. Flag for expert review                                      │       │
│  │                                                                  │       │
│  │  Trigger: Nightly batch job                                     │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                  CONFIDENCE SCORING MODEL                        │       │
│  │                                                                  │       │
│  │  Architecture: Bayesian update formula                          │       │
│  │                                                                  │       │
│  │  Formula:                                                       │       │
│  │  new_confidence = old_confidence + adjustment                   │       │
│  │                                                                  │       │
│  │  where adjustment =                                             │       │
│  │    if success: min(0.01, (1 - old_confidence) * 0.05)          │       │
│  │    if failure: max(-0.02, old_confidence * -0.1)               │       │
│  │                                                                  │       │
│  │  Effectiveness formula:                                         │       │
│  │  effectiveness = (success_count / usage_count) +                │       │
│  │                  min(0.1, usage_count / 100)                    │       │
│  │                                                                  │       │
│  │  Confidence levels:                                             │       │
│  │  - VERIFIED:  confidence >= 0.90                                │       │
│  │  - HIGH:      0.70 <= confidence < 0.90                         │       │
│  │  - MEDIUM:    0.40 <= confidence < 0.70                         │       │
│  │  - LOW:       confidence < 0.40                                 │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 Training Data Pipeline

```python
class TrainingDataPipeline:
    """
    Automated training data generation from production data.
    """
    
    async def generate_training_data(self, lookback_days: int = 90):
        """
        Generate training dataset from closed tickets.
        
        Criteria for inclusion:
        - Ticket status = "closed"
        - resolution_outcome in ["success", "partial"]
        - selected_failure_card is not None
        - Time since closure > 7 days (allow for feedback)
        """
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        feedback_window = datetime.now(timezone.utc) - timedelta(days=7)
        
        pipeline = [
            {"$match": {
                "status": "closed",
                "resolution_outcome": {"$in": ["success", "partial"]},
                "selected_failure_card": {"$ne": None},
                "closed_at": {"$gte": cutoff_date.isoformat(), "$lte": feedback_window.isoformat()}
            }},
            {"$lookup": {
                "from": "failure_cards",
                "localField": "selected_failure_card",
                "foreignField": "failure_id",
                "as": "failure_card"
            }},
            {"$unwind": "$failure_card"},
            {"$project": {
                "features": {
                    "symptom_text": "$title",
                    "description": "$description",
                    "error_codes": "$error_codes_reported",
                    "vehicle_make": "$vehicle_make",
                    "vehicle_model": "$vehicle_model",
                    "subsystem": "$failure_card.subsystem_category"
                },
                "label": "$selected_failure_card",
                "weight": {"$cond": [
                    {"$eq": ["$resolution_outcome", "success"]}, 1.0, 0.5
                ]}
            }}
        ]
        
        training_data = await self.db.tickets.aggregate(pipeline).to_list(None)
        
        return TrainingDataset(
            samples=training_data,
            generated_at=datetime.now(timezone.utc),
            source="production_tickets",
            sample_count=len(training_data)
        )
```

## 5.3 Model Evaluation Metrics

```python
class ModelEvaluator:
    """
    Evaluate AI matching model performance.
    """
    
    METRICS = {
        "match_accuracy": {
            "description": "Percentage of tickets where selected card was in top-5 suggestions",
            "target": 0.80,
            "critical_threshold": 0.60
        },
        "top_1_accuracy": {
            "description": "Percentage where selected card was top suggestion",
            "target": 0.50,
            "critical_threshold": 0.30
        },
        "mean_reciprocal_rank": {
            "description": "Average 1/rank of correct card",
            "target": 0.60,
            "critical_threshold": 0.40
        },
        "no_match_rate": {
            "description": "Percentage of tickets with no useful suggestions",
            "target": 0.10,  # Lower is better
            "critical_threshold": 0.25
        },
        "latency_p99": {
            "description": "99th percentile matching latency (ms)",
            "target": 50,
            "critical_threshold": 100
        }
    }
    
    async def evaluate(self, test_period_days: int = 30) -> EvaluationReport:
        """
        Run evaluation on recent production data.
        """
        # Get tickets where technician selected a card
        test_tickets = await self.get_test_tickets(test_period_days)
        
        results = {
            "match_accuracy": 0,
            "top_1_accuracy": 0,
            "mrr_sum": 0,
            "no_match_count": 0
        }
        
        for ticket in test_tickets:
            suggested = ticket.get("suggested_failure_cards", [])
            selected = ticket.get("selected_failure_card")
            
            if not selected:
                continue
            
            if selected in suggested:
                results["match_accuracy"] += 1
                rank = suggested.index(selected) + 1
                results["mrr_sum"] += 1 / rank
                
                if rank == 1:
                    results["top_1_accuracy"] += 1
            else:
                results["no_match_count"] += 1
        
        total = len(test_tickets)
        
        return EvaluationReport(
            period_days=test_period_days,
            sample_size=total,
            metrics={
                "match_accuracy": results["match_accuracy"] / total,
                "top_1_accuracy": results["top_1_accuracy"] / total,
                "mean_reciprocal_rank": results["mrr_sum"] / total,
                "no_match_rate": results["no_match_count"] / total
            },
            alerts=self.check_thresholds(results, total)
        )
```

## 5.4 Continuous Learning Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CONTINUOUS LEARNING LOOP                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │    ┌─────────┐      ┌─────────┐      ┌─────────┐               │       │
│  │    │ Ticket  │      │  AI     │      │ Techni- │               │       │
│  │    │ Created │ ───▶ │ Match   │ ───▶ │ cian    │               │       │
│  │    └─────────┘      └─────────┘      │ Review  │               │       │
│  │                                       └────┬────┘               │       │
│  │                                            │                    │       │
│  │         ┌──────────────────────────────────┘                    │       │
│  │         │                                                       │       │
│  │         ▼                                                       │       │
│  │    ┌─────────┐      ┌─────────┐      ┌─────────┐               │       │
│  │    │ Ticket  │      │ Conf.   │      │ Model   │               │       │
│  │    │ Closed  │ ───▶ │ Engine  │ ───▶ │ Retrain │               │       │
│  │    └─────────┘      └─────────┘      └────┬────┘               │       │
│  │                                            │                    │       │
│  │         ┌──────────────────────────────────┘                    │       │
│  │         │                                                       │       │
│  │         ▼                                                       │       │
│  │    ┌─────────┐      ┌─────────┐      ┌─────────┐               │       │
│  │    │ Better  │      │ Network │      │ Next    │               │       │
│  │    │ Match   │ ◀─── │ Sync    │ ◀─── │ Ticket  │               │       │
│  │    └─────────┘      └─────────┘      └─────────┘               │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  Feedback Signals:                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  1. Card selection (implicit positive signal)                   │       │
│  │  2. Resolution outcome (success/failure explicit signal)        │       │
│  │  3. Time to resolution (efficiency signal)                      │       │
│  │  4. Technician rating (1-5 stars, explicit quality signal)      │       │
│  │  5. Card modifications (improvement suggestions)                │       │
│  │  6. Rejected hypotheses (negative signal for ranking)           │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 6. Data Synchronization

## 6.1 Synchronization Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA SYNCHRONIZATION ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    CENTRAL HUB                                   │       │
│  │                                                                  │       │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │       │
│  │  │  MongoDB    │    │   Kafka     │    │   Redis     │         │       │
│  │  │  Primary    │    │   Cluster   │    │   Cache     │         │       │
│  │  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │       │
│  │         │                  │                  │                 │       │
│  │         └──────────────────┼──────────────────┘                 │       │
│  │                            │                                    │       │
│  │                    ┌───────▼───────┐                            │       │
│  │                    │  Sync Service │                            │       │
│  │                    │               │                            │       │
│  │                    │  - Change     │                            │       │
│  │                    │    Detection  │                            │       │
│  │                    │  - Conflict   │                            │       │
│  │                    │    Resolution │                            │       │
│  │                    │  - Broadcast  │                            │       │
│  │                    └───────┬───────┘                            │       │
│  │                            │                                    │       │
│  └────────────────────────────┼────────────────────────────────────┘       │
│                               │                                            │
│           ┌───────────────────┼───────────────────┐                        │
│           │                   │                   │                        │
│           ▼                   ▼                   ▼                        │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │  Location   │     │  Location   │     │  Location   │                  │
│  │   Agent     │     │   Agent     │     │   Agent     │                  │
│  │  (Delhi)    │     │  (Mumbai)   │     │ (Bangalore) │                  │
│  │             │     │             │     │             │                  │
│  │ Local Cache │     │ Local Cache │     │ Local Cache │                  │
│  │ SQLite DB   │     │ SQLite DB   │     │ SQLite DB   │                  │
│  └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.2 Synchronization Strategy

### 6.2.1 Failure Cards (Global → Local)

```python
class FailureCardSyncManager:
    """
    Manages synchronization of failure cards from central to locations.
    
    Strategy: Push-based with pull fallback
    - New approved cards pushed immediately via Kafka
    - Locations pull full sync on startup or after extended offline
    """
    
    async def push_card_update(self, card: FailureCard, event_type: str):
        """
        Push failure card update to all locations.
        """
        sync_event = SyncEvent(
            event_type=event_type,
            entity_type="failure_card",
            entity_id=card.failure_id,
            payload=card.model_dump(),
            timestamp=datetime.now(timezone.utc),
            version=card.version
        )
        
        await self.kafka.produce(
            topic="efi.sync.failure_cards",
            key=card.failure_id,
            value=sync_event.model_dump_json()
        )
        
        # Invalidate all location caches
        await self.redis.publish("cache_invalidate", {
            "entity_type": "failure_card",
            "entity_id": card.failure_id
        })
    
    async def pull_full_sync(self, location_id: str, last_sync_version: int):
        """
        Full sync for location after startup or offline period.
        """
        # Get all cards updated since last sync
        cards = await self.db.failure_cards.find({
            "status": "approved",
            "version": {"$gt": last_sync_version}
        }, {"_id": 0, "embedding_vector": 0}).to_list(None)
        
        return SyncResponse(
            location_id=location_id,
            cards=cards,
            current_version=await self.get_max_version(),
            sync_timestamp=datetime.now(timezone.utc)
        )
```

### 6.2.2 Tickets (Local → Central)

```python
class TicketSyncManager:
    """
    Manages synchronization of tickets from locations to central.
    
    Strategy: Event-sourced with local persistence
    - Tickets created/updated locally first (offline-capable)
    - Events queued for central sync
    - Automatic retry on connectivity
    """
    
    async def sync_ticket_event(self, event: TicketEvent):
        """
        Sync ticket event from location to central.
        """
        # Store in local WAL first
        await self.local_wal.append(event)
        
        try:
            # Attempt immediate sync
            response = await self.central_api.post(
                "/api/sync/tickets",
                json=event.model_dump()
            )
            
            if response.status_code == 200:
                await self.local_wal.mark_synced(event.event_id)
                return SyncResult.SUCCESS
            
        except (ConnectionError, TimeoutError):
            # Queue for retry
            await self.retry_queue.enqueue(event)
            return SyncResult.QUEUED
    
    async def process_retry_queue(self):
        """
        Background task to retry failed syncs.
        """
        while True:
            events = await self.retry_queue.get_pending(limit=100)
            
            for event in events:
                result = await self.sync_ticket_event(event)
                if result == SyncResult.SUCCESS:
                    await self.retry_queue.remove(event.event_id)
            
            await asyncio.sleep(30)  # Retry every 30 seconds
```

## 6.3 Conflict Resolution

```python
class ConflictResolver:
    """
    Handles conflicts in distributed data synchronization.
    
    Resolution strategies by entity type:
    - Failure cards: Central wins (single source of truth)
    - Tickets: Last-write-wins with merge for concurrent edits
    - Technician actions: Append-only (no conflicts)
    """
    
    RESOLUTION_STRATEGIES = {
        "failure_card": "central_wins",
        "ticket": "last_write_wins_with_merge",
        "technician_action": "append_only",
        "confidence_update": "accumulate"
    }
    
    async def resolve_ticket_conflict(
        self,
        local: Ticket,
        central: Ticket
    ) -> Ticket:
        """
        Merge conflicting ticket updates.
        """
        # Compare update timestamps
        local_updated = datetime.fromisoformat(local.updated_at)
        central_updated = datetime.fromisoformat(central.updated_at)
        
        if central_updated > local_updated:
            # Central is newer, but preserve local observations
            merged = central.model_copy()
            
            # Merge observations (union)
            local_obs = set(o["timestamp"] for o in local.observations)
            for obs in central.observations:
                if obs["timestamp"] not in local_obs:
                    merged.observations.append(obs)
            
            # Merge status history (union, sorted by timestamp)
            all_history = local.status_history + central.status_history
            merged.status_history = sorted(
                {h["timestamp"]: h for h in all_history}.values(),
                key=lambda x: x["timestamp"]
            )
            
            return merged
        else:
            # Local is newer, sync to central
            return local
    
    async def resolve_confidence_conflict(
        self,
        card_id: str,
        updates: List[ConfidenceUpdate]
    ) -> float:
        """
        Accumulate confidence updates from multiple sources.
        """
        # Sort by timestamp
        updates.sort(key=lambda x: x.timestamp)
        
        # Apply in sequence
        current = await self.db.failure_cards.find_one(
            {"failure_id": card_id},
            {"confidence_score": 1}
        )
        
        confidence = current.get("confidence_score", 0.5)
        
        for update in updates:
            if update.change_reason == "usage_success":
                confidence = min(1.0, confidence + 0.01)
            elif update.change_reason == "usage_failure":
                confidence = max(0.0, confidence - 0.02)
            elif update.change_reason == "expert_approval":
                confidence = min(1.0, confidence + 0.2)
        
        return confidence
```

## 6.4 Offline Mode Handling

```python
class OfflineModeManager:
    """
    Handles operation when location loses connectivity.
    
    Capabilities in offline mode:
    - Create/update tickets (queued for sync)
    - Match against locally cached failure cards
    - Record technician actions
    - View cached diagnostic trees
    
    Limitations in offline mode:
    - No new failure card creation
    - No confidence updates (queued)
    - Stale match suggestions (cache age warning)
    """
    
    def __init__(self, location_id: str):
        self.location_id = location_id
        self.local_db = SQLiteDatabase(f"location_{location_id}.db")
        self.sync_queue = PersistentQueue(f"sync_queue_{location_id}.db")
        self.last_sync = None
        self.offline_mode = False
    
    async def check_connectivity(self) -> bool:
        """
        Check if central hub is reachable.
        """
        try:
            response = await self.central_api.get("/health", timeout=5)
            if response.status_code == 200:
                if self.offline_mode:
                    await self.on_reconnect()
                self.offline_mode = False
                return True
        except Exception:
            pass
        
        self.offline_mode = True
        return False
    
    async def on_reconnect(self):
        """
        Handle reconnection after offline period.
        """
        logger.info(f"Location {self.location_id} reconnected")
        
        # 1. Pull any missed failure card updates
        await self.pull_failure_card_updates()
        
        # 2. Push queued local changes
        await self.flush_sync_queue()
        
        # 3. Refresh local cache
        await self.refresh_local_cache()
        
        # 4. Emit reconnection event
        await self.emit_event("LOCATION_ONLINE", {"location_id": self.location_id})
    
    async def match_offline(self, request: MatchRequest) -> MatchResponse:
        """
        Perform matching against local cache in offline mode.
        """
        # Check cache freshness
        cache_age = datetime.now(timezone.utc) - self.last_sync
        stale_warning = cache_age > timedelta(hours=24)
        
        # Query local SQLite cache
        matches = await self.local_db.query(
            """
            SELECT * FROM failure_cards
            WHERE subsystem_category = ?
            AND status = 'approved'
            ORDER BY effectiveness_score DESC
            LIMIT 5
            """,
            [request.subsystem_hint]
        )
        
        return MatchResponse(
            matches=matches,
            source="local_cache",
            stale_warning=stale_warning,
            cache_age_hours=cache_age.total_seconds() / 3600,
            offline_mode=True
        )
```

---

# 7. Security & Governance

## 7.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SECURITY ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AUTHENTICATION                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  Primary: JWT with RS256 signing                                │       │
│  │  - Access token: 15 min expiry                                  │       │
│  │  - Refresh token: 7 day expiry (stored in HttpOnly cookie)      │       │
│  │                                                                  │       │
│  │  Token payload:                                                 │       │
│  │  {                                                              │       │
│  │    "user_id": "usr_xxx",                                        │       │
│  │    "email": "tech@battwheels.in",                               │       │
│  │    "role": "technician",                                        │       │
│  │    "location_id": "loc_delhi_01",                               │       │
│  │    "permissions": ["ticket:read", "ticket:write", "efi:read"],  │       │
│  │    "iat": 1708000000,                                           │       │
│  │    "exp": 1708000900                                            │       │
│  │  }                                                              │       │
│  │                                                                  │       │
│  │  Alternative: Google OAuth (Emergent-managed)                   │       │
│  │  - For admin users with @battwheels.in domain                   │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  AUTHORIZATION (RBAC)                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  Roles:                                                         │       │
│  │  ┌───────────────────────────────────────────────────────────┐ │       │
│  │  │ SUPER_ADMIN    │ Full system access, all locations        │ │       │
│  │  │ LOCATION_ADMIN │ Full access within assigned location     │ │       │
│  │  │ MANAGER        │ Team management, reports, approvals      │ │       │
│  │  │ TECHNICIAN     │ Tickets, diagnostics, EFI read           │ │       │
│  │  │ CUSTOMER       │ Own tickets only, read-only              │ │       │
│  │  └───────────────────────────────────────────────────────────┘ │       │
│  │                                                                  │       │
│  │  Resource-based permissions:                                    │       │
│  │  - ticket:{create,read,update,close,assign}                     │       │
│  │  - efi:{read,create,update,approve,deprecate}                   │       │
│  │  - inventory:{read,create,update,allocate}                      │       │
│  │  - hr:{read,create,update,payroll}                              │       │
│  │  - reports:{view,export}                                        │       │
│  │  - admin:{users,locations,settings}                             │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 7.2 Data Encryption

```yaml
# Encryption configuration
encryption:
  at_rest:
    database:
      provider: "MongoDB Enterprise Encryption"
      algorithm: "AES-256-GCM"
      key_management: "AWS KMS" # or Azure Key Vault
      encrypted_fields:
        - "users.password_hash"
        - "employees.aadhaar_number"
        - "employees.pan_number"
        - "employees.bank_details"
        - "customers.contact_number"
    
    file_storage:
      provider: "S3 Server-Side Encryption"
      algorithm: "AES-256"
      key_rotation: "90 days"
  
  in_transit:
    api:
      protocol: "TLS 1.3"
      certificate_provider: "Let's Encrypt"
      hsts_enabled: true
      hsts_max_age: 31536000
    
    database:
      protocol: "TLS 1.2+"
      mutual_tls: true
    
    internal_services:
      protocol: "mTLS"
      certificate_authority: "Internal PKI"
```

## 7.3 Audit Trail

```python
class AuditLogger:
    """
    Comprehensive audit logging for compliance.
    
    Logged events:
    - Authentication (login, logout, failed attempts)
    - Authorization (permission grants, denials)
    - Data access (read sensitive data)
    - Data modification (create, update, delete)
    - System events (config changes, deployments)
    """
    
    async def log_event(
        self,
        event_type: str,
        actor: str,
        resource: str,
        action: str,
        outcome: str,
        details: dict = None,
        ip_address: str = None
    ):
        audit_entry = {
            "audit_id": f"audit_{uuid.uuid4().hex}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": {
                "user_id": actor,
                "ip_address": ip_address,
                "user_agent": details.get("user_agent") if details else None
            },
            "resource": {
                "type": resource.split(":")[0],
                "id": resource.split(":")[1] if ":" in resource else None
            },
            "action": action,
            "outcome": outcome,  # success, denied, error
            "details": details,
            "location_id": details.get("location_id") if details else None
        }
        
        # Write to audit log (immutable, append-only)
        await self.db.audit_log.insert_one(audit_entry)
        
        # For critical events, also send to external SIEM
        if event_type in ["auth.failed", "data.deleted", "permission.escalation"]:
            await self.siem_client.send(audit_entry)
```

## 7.4 Data Privacy Controls

```python
class DataPrivacyManager:
    """
    GDPR/Indian data protection compliance.
    """
    
    PII_FIELDS = {
        "users": ["email", "phone", "name"],
        "employees": ["aadhaar_number", "pan_number", "bank_details", "address"],
        "customers": ["name", "contact_number", "email", "address"]
    }
    
    async def anonymize_user_data(self, user_id: str):
        """
        Right to erasure - anonymize all PII.
        """
        anonymized_id = f"anon_{hashlib.sha256(user_id.encode()).hexdigest()[:12]}"
        
        # Anonymize user record
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "email": f"{anonymized_id}@deleted.battwheels.in",
                "name": "Deleted User",
                "phone": None,
                "status": "deleted",
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Anonymize related records
        await self.db.tickets.update_many(
            {"customer_id": user_id},
            {"$set": {
                "customer_name": "Deleted User",
                "contact_number": None,
                "customer_email": None
            }}
        )
        
        # Log for compliance
        await self.audit.log_event(
            event_type="privacy.erasure",
            actor="system",
            resource=f"user:{user_id}",
            action="anonymize",
            outcome="success"
        )
    
    async def export_user_data(self, user_id: str) -> dict:
        """
        Right to data portability - export all user data.
        """
        data = {
            "user": await self.db.users.find_one({"user_id": user_id}, {"_id": 0}),
            "tickets": await self.db.tickets.find({"customer_id": user_id}, {"_id": 0}).to_list(None),
            "exported_at": datetime.now(timezone.utc).isoformat()
        }
        
        return data
```

---

# 8. Continuous Improvement Feedback Loops

## 8.1 Key Performance Indicators

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CONTINUOUS IMPROVEMENT METRICS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIMARY KPIs (Business Impact)                                            │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  1. DIAGNOSTIC TIME REDUCTION                                   │       │
│  │     Formula: avg_diagnosis_time_with_EFI / avg_diagnosis_time_baseline  │
│  │     Target: < 0.5 (50% reduction)                               │       │
│  │     Measurement: Time from ticket_created to first_action       │       │
│  │                                                                  │       │
│  │  2. FIRST-TIME FIX RATE (FTFR)                                  │       │
│  │     Formula: tickets_resolved_first_attempt / total_tickets     │       │
│  │     Target: > 0.85 (85% first-time fix)                         │       │
│  │     Measurement: Tickets without reopen within 7 days           │       │
│  │                                                                  │       │
│  │  3. MATCH ACCURACY                                              │       │
│  │     Formula: tickets_with_selected_card_in_top5 / total_matches │       │
│  │     Target: > 0.80 (80% accuracy)                               │       │
│  │     Measurement: Selected card rank in suggestions              │       │
│  │                                                                  │       │
│  │  4. KNOWLEDGE UTILIZATION RATE                                  │       │
│  │     Formula: tickets_using_failure_cards / total_tickets        │       │
│  │     Target: > 0.70 (70% utilization)                            │       │
│  │     Measurement: Tickets with selected_failure_card != null     │       │
│  │                                                                  │       │
│  │  5. NEW FAILURE DOCUMENTATION RATE                              │       │
│  │     Formula: new_cards_created / undocumented_issues_detected   │       │
│  │     Target: > 0.90 (90% documented)                             │       │
│  │     Measurement: NEW_FAILURE_DETECTED → card created            │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  SECONDARY KPIs (System Health)                                            │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                                                                  │       │
│  │  - Match latency p99: < 50ms                                    │       │
│  │  - Sync latency (card → all locations): < 60s                   │       │
│  │  - Cache hit rate: > 95%                                        │       │
│  │  - Model accuracy drift: < 5% month-over-month                  │       │
│  │  - Card confidence distribution: > 60% at HIGH or VERIFIED      │       │
│  │                                                                  │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 8.2 Feedback Loop Architecture

```python
class FeedbackLoopManager:
    """
    Orchestrates continuous improvement feedback loops.
    """
    
    async def process_ticket_closure_feedback(self, ticket: Ticket):
        """
        Extract learning signals from ticket closure.
        """
        feedback = TicketClosureFeedback(
            ticket_id=ticket.ticket_id,
            timestamp=datetime.now(timezone.utc),
            
            # Outcome signals
            resolution_outcome=ticket.resolution_outcome,
            time_to_resolution=self.calculate_ttr(ticket),
            reopened_within_7_days=await self.check_reopen(ticket.ticket_id),
            
            # Match quality signals
            suggested_cards=ticket.suggested_failure_cards,
            selected_card=ticket.selected_failure_card,
            selected_card_rank=self.get_rank(ticket),
            match_helpful=ticket.selected_failure_card is not None,
            
            # Technician feedback
            technician_rating=ticket.technician_feedback.get("card_rating"),
            technician_modifications=ticket.technician_feedback.get("modifications"),
            
            # New failure signal
            new_failure_detected=ticket.selected_failure_card is None and 
                                 ticket.resolution_outcome == "success"
        )
        
        # Store feedback
        await self.db.feedback_signals.insert_one(feedback.model_dump())
        
        # Trigger downstream updates
        if feedback.selected_card:
            await self.update_card_confidence(
                card_id=feedback.selected_card,
                outcome=feedback.resolution_outcome
            )
        
        if feedback.new_failure_detected:
            await self.queue_for_documentation(ticket)
        
        # Update metrics
        await self.metrics_service.record(feedback)
    
    async def run_weekly_model_evaluation(self):
        """
        Weekly evaluation and potential retraining.
        """
        # Evaluate current model performance
        evaluation = await self.model_evaluator.evaluate(test_period_days=7)
        
        # Check for drift
        previous_eval = await self.get_previous_evaluation()
        drift = abs(evaluation.match_accuracy - previous_eval.match_accuracy)
        
        if drift > 0.05 or evaluation.match_accuracy < 0.75:
            # Trigger retraining
            await self.training_pipeline.trigger_retrain(
                reason="accuracy_drift" if drift > 0.05 else "below_threshold",
                current_accuracy=evaluation.match_accuracy
            )
        
        # Store evaluation
        await self.db.model_evaluations.insert_one(evaluation.model_dump())
        
        # Alert if critical threshold breached
        if evaluation.match_accuracy < 0.60:
            await self.alerting.send_critical(
                "Model accuracy below critical threshold",
                evaluation
            )
```

## 8.3 Improvement Tracking Dashboard

```python
@router.get("/efi/analytics/improvement-report")
async def get_improvement_report(
    period: str = "30d",
    location_id: Optional[str] = None
) -> ImprovementReport:
    """
    Generate improvement tracking report.
    """
    period_start = parse_period(period)
    
    # Calculate current metrics
    current_metrics = await calculate_metrics(
        start=period_start,
        end=datetime.now(timezone.utc),
        location_id=location_id
    )
    
    # Calculate baseline (previous period)
    baseline_start = period_start - (datetime.now(timezone.utc) - period_start)
    baseline_metrics = await calculate_metrics(
        start=baseline_start,
        end=period_start,
        location_id=location_id
    )
    
    # Calculate improvements
    improvements = {
        "diagnostic_time": {
            "current": current_metrics.avg_diagnostic_time_minutes,
            "baseline": baseline_metrics.avg_diagnostic_time_minutes,
            "improvement_pct": calculate_improvement(
                baseline_metrics.avg_diagnostic_time_minutes,
                current_metrics.avg_diagnostic_time_minutes,
                lower_is_better=True
            )
        },
        "first_time_fix_rate": {
            "current": current_metrics.ftfr,
            "baseline": baseline_metrics.ftfr,
            "improvement_pct": calculate_improvement(
                baseline_metrics.ftfr,
                current_metrics.ftfr
            )
        },
        "match_accuracy": {
            "current": current_metrics.match_accuracy,
            "baseline": baseline_metrics.match_accuracy,
            "improvement_pct": calculate_improvement(
                baseline_metrics.match_accuracy,
                current_metrics.match_accuracy
            )
        },
        "knowledge_coverage": {
            "current": current_metrics.knowledge_utilization,
            "baseline": baseline_metrics.knowledge_utilization,
            "improvement_pct": calculate_improvement(
                baseline_metrics.knowledge_utilization,
                current_metrics.knowledge_utilization
            )
        }
    }
    
    # Identify top-performing cards
    top_cards = await db.failure_cards.find(
        {"status": "approved", "usage_count": {"$gt": 5}},
        {"_id": 0}
    ).sort("effectiveness_score", -1).limit(10).to_list(10)
    
    # Identify cards needing attention
    underperforming = await db.failure_cards.find({
        "status": "approved",
        "usage_count": {"$gt": 10},
        "effectiveness_score": {"$lt": 0.5}
    }, {"_id": 0}).to_list(10)
    
    return ImprovementReport(
        period=period,
        location_id=location_id,
        metrics=current_metrics,
        improvements=improvements,
        top_performing_cards=top_cards,
        cards_needing_review=underperforming,
        system_health={
            "total_failure_cards": await db.failure_cards.count_documents({}),
            "approved_cards": await db.failure_cards.count_documents({"status": "approved"}),
            "high_confidence_cards": await db.failure_cards.count_documents({
                "status": "approved", "confidence_score": {"$gte": 0.7}
            }),
            "avg_confidence": await calculate_avg_confidence()
        },
        generated_at=datetime.now(timezone.utc)
    )
```

---

# 9. Operational Considerations

## 9.1 Deployment Strategy

```yaml
# Multi-location rollout strategy
deployment:
  strategy: "progressive_rollout"
  
  phases:
    pilot:
      locations: ["loc_delhi_hq"]
      duration: "2 weeks"
      success_criteria:
        - "system_uptime > 99.5%"
        - "match_accuracy > 70%"
        - "no_critical_bugs"
      rollback_trigger: "critical_bug OR uptime < 99%"
    
    phase_1:
      locations: ["loc_delhi_*", "loc_ncr_*"]  # 5-10 locations
      duration: "4 weeks"
      success_criteria:
        - "system_uptime > 99.5%"
        - "match_accuracy > 75%"
        - "user_satisfaction > 4.0/5"
    
    phase_2:
      locations: ["loc_north_*"]  # 20-50 locations
      duration: "6 weeks"
      success_criteria:
        - "system_uptime > 99.9%"
        - "match_accuracy > 80%"
        - "sync_latency < 60s"
    
    general_availability:
      locations: ["*"]  # All locations
      monitoring: "enhanced for 30 days"

# Kubernetes deployment
kubernetes:
  cluster:
    provider: "AWS EKS"
    regions: ["ap-south-1", "ap-south-2"]  # Mumbai, Hyderabad
    node_pools:
      general:
        instance_type: "m5.xlarge"
        min_nodes: 3
        max_nodes: 20
      ml_inference:
        instance_type: "g4dn.xlarge"
        min_nodes: 1
        max_nodes: 5
        taints: ["nvidia.com/gpu=present:NoSchedule"]
  
  deployments:
    efi-service:
      replicas: 3
      resources:
        requests: {cpu: "500m", memory: "1Gi"}
        limits: {cpu: "2000m", memory: "4Gi"}
      health_check:
        path: "/health"
        interval: 10s
        timeout: 5s
      rolling_update:
        max_surge: 1
        max_unavailable: 0
```

## 9.2 Monitoring & Observability

```yaml
observability:
  metrics:
    provider: "Prometheus + Grafana"
    
    custom_metrics:
      - name: "efi_match_latency_seconds"
        type: "histogram"
        buckets: [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
      
      - name: "efi_match_accuracy"
        type: "gauge"
        labels: ["location_id", "subsystem"]
      
      - name: "efi_confidence_distribution"
        type: "histogram"
        buckets: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
      
      - name: "efi_sync_lag_seconds"
        type: "gauge"
        labels: ["location_id"]
    
    alerts:
      - name: "HighMatchLatency"
        expr: "histogram_quantile(0.99, efi_match_latency_seconds) > 0.1"
        severity: "warning"
      
      - name: "LowMatchAccuracy"
        expr: "efi_match_accuracy < 0.6"
        severity: "critical"
      
      - name: "SyncLagHigh"
        expr: "efi_sync_lag_seconds > 300"
        severity: "warning"
  
  logging:
    provider: "Elasticsearch + Kibana"
    retention: "30 days"
    
    structured_fields:
      - "request_id"
      - "user_id"
      - "location_id"
      - "ticket_id"
      - "failure_card_id"
      - "event_type"
      - "latency_ms"
  
  tracing:
    provider: "Jaeger"
    sampling_rate: 0.1  # 10% of requests
    
    spans:
      - "api.request"
      - "efi.match.stage1"
      - "efi.match.stage2"
      - "efi.match.stage3"
      - "efi.match.stage4"
      - "db.query"
      - "cache.lookup"
      - "sync.publish"
```

## 9.3 Disaster Recovery

```yaml
disaster_recovery:
  rpo: "1 hour"  # Maximum data loss
  rto: "4 hours"  # Maximum downtime
  
  backup:
    mongodb:
      frequency: "hourly"
      retention: "30 days"
      destination: "s3://battwheels-backups/mongodb/"
      encryption: "AES-256"
    
    redis:
      frequency: "every 5 minutes"
      retention: "7 days"
      type: "RDB snapshots"
    
    elasticsearch:
      frequency: "daily"
      retention: "14 days"
      type: "snapshot to S3"
  
  replication:
    mongodb:
      type: "replica_set"
      members: 3
      read_preference: "primaryPreferred"
    
    cross_region:
      enabled: true
      secondary_region: "ap-south-2"
      replication_lag_alert: "30 seconds"
  
  recovery_procedures:
    database_failure:
      - "Automatic failover to secondary replica"
      - "DNS update (< 30 seconds)"
      - "Verify application connectivity"
      - "Alert on-call team"
    
    complete_region_failure:
      - "DNS failover to secondary region"
      - "Verify data consistency"
      - "Notify all locations of potential sync delays"
      - "Begin data reconciliation post-recovery"
    
    data_corruption:
      - "Identify corruption scope"
      - "Restore from last known good backup"
      - "Replay events from Kafka (if within retention)"
      - "Notify affected locations"
      - "Run data integrity checks"
```

## 9.4 Rollback Strategy

```python
class RollbackManager:
    """
    Manages safe rollbacks for failed deployments.
    """
    
    async def rollback_deployment(
        self,
        service: str,
        target_version: str,
        reason: str
    ):
        """
        Execute safe rollback.
        """
        # 1. Stop traffic to new version
        await self.traffic_manager.drain(service)
        
        # 2. Verify target version is stable
        if not await self.verify_version_stable(service, target_version):
            raise RollbackError(f"Target version {target_version} not stable")
        
        # 3. Execute rollback
        await self.kubernetes.rollback(service, target_version)
        
        # 4. Wait for health checks
        await self.wait_for_healthy(service, timeout=300)
        
        # 5. Restore traffic
        await self.traffic_manager.restore(service)
        
        # 6. Log and alert
        await self.audit.log_event(
            event_type="deployment.rollback",
            actor="system",
            resource=f"service:{service}",
            action="rollback",
            outcome="success",
            details={
                "from_version": await self.get_current_version(service),
                "to_version": target_version,
                "reason": reason
            }
        )
        
        await self.alerting.send_warning(
            f"Rollback executed for {service}",
            {"reason": reason, "target_version": target_version}
        )
    
    async def rollback_database_migration(
        self,
        migration_id: str,
        reason: str
    ):
        """
        Rollback a failed database migration.
        """
        migration = await self.get_migration(migration_id)
        
        if not migration.reversible:
            raise RollbackError("Migration is not reversible")
        
        # Execute down migration
        await self.run_migration(migration.down_script)
        
        # Update migration status
        await self.db.migrations.update_one(
            {"migration_id": migration_id},
            {"$set": {"status": "rolled_back", "rollback_reason": reason}}
        )
```

---

# 10. Risk Assessment & Mitigation

## 10.1 Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Database overload during peak** | Medium | High | Sharding, read replicas, caching |
| **AI matching degradation** | Medium | High | Continuous monitoring, automatic fallback to cached results |
| **Network partition between locations** | Medium | Medium | Offline mode, local queuing, eventual consistency |
| **Failure card data quality** | High | High | Expert review workflow, confidence scoring, deprecation |
| **Model drift over time** | Medium | Medium | Weekly evaluation, automatic retraining triggers |
| **Single point of failure** | Low | Critical | Multi-region deployment, no single points |
| **Data breach** | Low | Critical | Encryption, access controls, audit logging |
| **Sync conflicts** | Medium | Low | Conflict resolution strategies, version vectors |

## 10.2 Trade-offs Made

| Decision | Trade-off | Rationale |
|----------|-----------|-----------|
| **MongoDB over PostgreSQL** | Less ACID guarantees | Schema flexibility for evolving failure cards |
| **Eventual consistency** | May see stale data briefly | Enables offline operation and scalability |
| **4-stage matching** | Higher latency than single-stage | Better accuracy through multi-strategy approach |
| **Event-driven architecture** | Complexity overhead | Enables loose coupling and async processing |
| **Central hub model** | Dependency on hub connectivity | Simpler sync than peer-to-peer mesh |

---

# Appendix A: API Reference

See `/app/docs/API_REFERENCE.md` for complete API documentation.

# Appendix B: Data Dictionary

See `/app/docs/DATA_DICTIONARY.md` for complete schema definitions.

# Appendix C: Deployment Runbooks

See `/app/docs/RUNBOOKS.md` for operational procedures.

---

**Document Control:**
- Created: February 2026
- Author: Battwheels Engineering Team
- Review Cycle: Quarterly
- Next Review: May 2026
