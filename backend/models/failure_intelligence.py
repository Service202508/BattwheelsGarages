"""
Battwheels OS - Failure Intelligence Models
Core data models for the EV Failure Intelligence (EFI) Platform

Version: 2.0 - Enhanced with diagnostic reasoning, confidence history, and pattern detection
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import hashlib

# ==================== ENUMS ====================

class FailureCardStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class SubsystemCategory(str, Enum):
    BATTERY = "battery"
    MOTOR = "motor"
    CONTROLLER = "controller"
    WIRING = "wiring"
    THROTTLE = "throttle"
    CHARGER = "charger"
    BMS = "bms"
    DISPLAY = "display"
    BRAKES = "brakes"
    SUSPENSION = "suspension"
    LIGHTS = "lights"
    HORN = "horn"
    BODY = "body"
    SOFTWARE = "software"
    OTHER = "other"

class FailureMode(str, Enum):
    COMPLETE_FAILURE = "complete_failure"
    INTERMITTENT = "intermittent"
    DEGRADATION = "degradation"
    ERRATIC_BEHAVIOR = "erratic_behavior"
    NO_RESPONSE = "no_response"
    OVERHEATING = "overheating"
    NOISE = "noise"
    VIBRATION = "vibration"
    LEAKAGE = "leakage"

class ConfidenceLevel(str, Enum):
    LOW = "low"           # < 0.4
    MEDIUM = "medium"     # 0.4 - 0.7
    HIGH = "high"         # 0.7 - 0.9
    VERIFIED = "verified" # > 0.9

class SourceType(str, Enum):
    """How the failure card was created"""
    FIELD_DISCOVERY = "field_discovery"      # Discovered by technician in field
    OEM_INPUT = "oem_input"                  # From manufacturer documentation
    INTERNAL_ANALYSIS = "internal_analysis"  # From internal engineering analysis
    PATTERN_DETECTION = "pattern_detection"  # Auto-generated from pattern analysis
    LEGACY_IMPORT = "legacy_import"          # Imported from legacy system

# ==================== SYMPTOM MODEL ====================

class Symptom(BaseModel):
    """Structured symptom for knowledge graph linking"""
    model_config = ConfigDict(extra="ignore")
    symptom_id: str = Field(default_factory=lambda: f"sym_{uuid.uuid4().hex[:8]}")
    code: str  # e.g., "SYM_BATT_001"
    category: SubsystemCategory
    description: str
    severity: str = "medium"  # low, medium, high, critical
    keywords: List[str] = []
    related_symptoms: List[str] = []  # Links to other symptom_ids

class SymptomCreate(BaseModel):
    code: str
    category: SubsystemCategory
    description: str
    severity: str = "medium"
    keywords: List[str] = []

# ==================== DIAGNOSTIC TREE MODEL (NEW) ====================

class DiagnosticNode(BaseModel):
    """Single node in the diagnostic decision tree"""
    node_id: str = Field(default_factory=lambda: f"dn_{uuid.uuid4().hex[:6]}")
    step_number: int
    question: str                          # "Is the battery voltage below 48V?"
    check_action: str                      # "Measure battery terminal voltage"
    expected_outcome: str                  # "Voltage should be 48-54V"
    tools_required: List[str] = []
    safety_warnings: List[str] = []
    duration_minutes: int = 5
    
    # Decision branches
    if_yes: Optional[str] = None           # Next node_id if condition is true
    if_no: Optional[str] = None            # Next node_id if condition is false
    leads_to_root_cause: Optional[str] = None  # If this confirms root cause

class DiagnosticTree(BaseModel):
    """
    Structured step-by-step diagnostic logic tree
    EFI is about reasoning, not just documentation
    """
    tree_id: str = Field(default_factory=lambda: f"dt_{uuid.uuid4().hex[:8]}")
    root_node_id: str                      # Starting point of diagnosis
    nodes: List[DiagnosticNode] = []       # All decision nodes
    total_paths: int = 0                   # Number of possible diagnostic paths
    avg_path_length: int = 0               # Average steps to diagnosis
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== FAILURE SIGNATURE MODEL (NEW) ====================

class FailureSignature(BaseModel):
    """
    Symptom + condition fingerprint for faster matching
    This is the PRIMARY key for fast failure card lookup
    """
    signature_id: str = Field(default_factory=lambda: f"sig_{uuid.uuid4().hex[:10]}")
    signature_hash: str = ""               # Computed hash for fast lookup
    
    # Core symptom indicators
    primary_symptoms: List[str] = []       # Most important symptoms (ordered)
    error_codes: List[str] = []            # OEM error codes
    subsystem: SubsystemCategory
    failure_mode: FailureMode
    
    # Environmental conditions
    temperature_range: Optional[str] = None  # "30-45°C"
    humidity_range: Optional[str] = None     # "high", "low", "normal"
    load_condition: Optional[str] = None     # "under_load", "idle", "charging"
    
    # Vehicle context
    mileage_range: Optional[str] = None      # "0-10000", "10000-50000", etc.
    vehicle_age_months: Optional[int] = None
    
    # Pattern indicators
    occurrence_pattern: str = "unknown"    # sporadic, daily, weekly, weather_dependent
    time_of_day_pattern: Optional[str] = None  # morning, afternoon, night, random
    
    def compute_hash(self) -> str:
        """Generate deterministic hash for signature matching"""
        components = [
            ",".join(sorted(self.primary_symptoms)),
            ",".join(sorted(self.error_codes)),
            self.subsystem.value if self.subsystem else "",
            self.failure_mode.value if self.failure_mode else "",
            self.temperature_range or "",
            self.load_condition or ""
        ]
        hash_input = "|".join(components).lower()
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

# ==================== CONFIDENCE HISTORY MODEL (NEW) ====================

class ConfidenceChangeEvent(BaseModel):
    """Track confidence score changes over time"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    previous_score: float
    new_score: float
    change_reason: str      # "success_outcome", "failure_outcome", "expert_review", "usage_decay"
    ticket_id: Optional[str] = None
    technician_id: Optional[str] = None
    notes: Optional[str] = None

# ==================== VERIFICATION STEP MODEL ====================

class VerificationStep(BaseModel):
    """Diagnostic step to verify failure"""
    step_number: int
    action: str
    expected_result: str
    tools_required: List[str] = []
    safety_warnings: List[str] = []
    duration_minutes: int = 5

# ==================== RESOLUTION STEP MODEL ====================

class ResolutionStep(BaseModel):
    """Step to resolve the failure"""
    step_number: int
    action: str
    details: Optional[str] = None
    tools_required: List[str] = []
    parts_required: List[str] = []  # Part IDs
    safety_warnings: List[str] = []
    duration_minutes: int = 10
    skill_level: str = "intermediate"  # basic, intermediate, advanced, expert

# ==================== REQUIRED PART MODEL ====================

class RequiredPart(BaseModel):
    """Part required for resolution"""
    part_id: Optional[str] = None  # Links to inventory
    part_name: str
    part_number: Optional[str] = None
    quantity: int = 1
    is_critical: bool = True
    alternatives: List[str] = []  # Alternative part names/numbers
    estimated_cost: float = 0.0

# ==================== FAILURE CONDITION MODEL ====================

class FailureCondition(BaseModel):
    """Environmental/usage conditions when failure occurs"""
    condition_type: str  # temperature, humidity, load, mileage, age
    value_range: Optional[str] = None  # e.g., "35-45°C"
    description: str
    correlation_strength: float = 0.5  # 0-1

# ==================== VEHICLE COMPATIBILITY MODEL ====================

class VehicleCompatibility(BaseModel):
    """Vehicle models this failure card applies to"""
    make: str
    model: str
    variants: List[str] = []
    year_range: Optional[str] = None  # e.g., "2022-2025"
    firmware_versions: List[str] = []

# ==================== MAIN FAILURE CARD MODEL (ENHANCED) ====================

class FailureCard(BaseModel):
    """
    Core entity: EV Failure Intelligence Card
    This is the most important entity in the system.
    
    Enhanced v2.0:
    - diagnostic_tree: Structured reasoning logic
    - failure_signature: Fast matching fingerprint
    - confidence_history: Track learning over time
    - source_type: Origin of knowledge
    """
    model_config = ConfigDict(extra="ignore")
    
    # === IDENTIFICATION ===
    failure_id: str = Field(default_factory=lambda: f"fc_{uuid.uuid4().hex[:12]}")
    title: str
    description: Optional[str] = None
    
    # === CLASSIFICATION ===
    subsystem_category: SubsystemCategory
    failure_mode: FailureMode = FailureMode.COMPLETE_FAILURE
    
    # === FAILURE SIGNATURE (NEW - Primary matching key) ===
    failure_signature: Optional[FailureSignature] = None
    signature_hash: Optional[str] = None  # Denormalized for fast query
    
    # === SYMPTOMS (Knowledge Graph Links) ===
    symptoms: List[Symptom] = []
    symptom_codes: List[str] = []  # Quick reference codes
    symptom_text: Optional[str] = None  # Free-text symptom description
    error_codes: List[str] = []  # OEM error codes
    
    # === ROOT CAUSE ANALYSIS ===
    root_cause: str
    root_cause_details: Optional[str] = None
    secondary_causes: List[str] = []
    
    # === DIAGNOSTIC TREE (NEW - Structured reasoning) ===
    diagnostic_tree: Optional[DiagnosticTree] = None
    
    # === DIAGNOSTIC PROCESS (Legacy - kept for compatibility) ===
    verification_steps: List[VerificationStep] = []
    diagnostic_tools: List[str] = []
    diagnostic_duration_minutes: int = 30
    
    # === RESOLUTION ===
    resolution_steps: List[ResolutionStep] = []
    resolution_summary: Optional[str] = None
    estimated_repair_time_minutes: int = 60
    skill_level_required: str = "intermediate"
    
    # === PARTS ===
    required_parts: List[RequiredPart] = []
    estimated_parts_cost: float = 0.0
    estimated_labor_cost: float = 0.0
    estimated_total_cost: float = 0.0
    
    # === VEHICLE COMPATIBILITY ===
    vehicle_models: List[VehicleCompatibility] = []
    universal_failure: bool = False  # Applies to all EVs
    
    # === CONDITIONS ===
    failure_conditions: List[FailureCondition] = []
    
    # === INTELLIGENCE METRICS ===
    confidence_score: float = 0.5  # 0.0 - 1.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    effectiveness_score: float = 0.0
    
    # === CONFIDENCE HISTORY (NEW - Track learning over time) ===
    confidence_history: List[ConfidenceChangeEvent] = []
    
    # === AI/ML METADATA ===
    embedding_vector: Optional[List[float]] = None  # For semantic search
    keywords: List[str] = []
    tags: List[str] = []
    
    # === VERSIONING ===
    version: int = 1
    status: FailureCardStatus = FailureCardStatus.DRAFT
    
    # === PROVENANCE (ENHANCED) ===
    source_type: SourceType = SourceType.FIELD_DISCOVERY  # NEW
    source_ticket_id: Optional[str] = None
    source_garage_id: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    
    # === TIMESTAMPS (ENHANCED) ===
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    first_detected_at: Optional[datetime] = None  # NEW - When this failure was first seen
    last_used_at: Optional[datetime] = None       # NEW - When this card was last used
    
    # === VERSION HISTORY ===
    version_history: List[Dict[str, Any]] = []
    
    # === NETWORK SYNC ===
    synced_to_network: bool = False
    last_sync_at: Optional[datetime] = None

class FailureCardCreate(BaseModel):
    """Input model for creating a failure card"""
    title: str
    description: Optional[str] = None
    subsystem_category: SubsystemCategory
    failure_mode: FailureMode = FailureMode.COMPLETE_FAILURE
    
    # Failure signature components
    failure_signature: Optional[dict] = None
    
    symptom_codes: List[str] = []
    symptom_text: Optional[str] = None
    error_codes: List[str] = []
    
    root_cause: str
    root_cause_details: Optional[str] = None
    secondary_causes: List[str] = []
    
    # Diagnostic tree
    diagnostic_tree: Optional[dict] = None
    
    verification_steps: List[dict] = []
    resolution_steps: List[dict] = []
    required_parts: List[dict] = []
    
    vehicle_models: List[dict] = []
    universal_failure: bool = False
    failure_conditions: List[dict] = []
    
    keywords: List[str] = []
    tags: List[str] = []
    
    source_type: SourceType = SourceType.FIELD_DISCOVERY
    source_ticket_id: Optional[str] = None

class FailureCardUpdate(BaseModel):
    """Input model for updating a failure card"""
    title: Optional[str] = None
    description: Optional[str] = None
    subsystem_category: Optional[SubsystemCategory] = None
    failure_mode: Optional[FailureMode] = None
    
    failure_signature: Optional[dict] = None
    
    symptom_codes: Optional[List[str]] = None
    symptom_text: Optional[str] = None
    error_codes: Optional[List[str]] = None
    
    root_cause: Optional[str] = None
    root_cause_details: Optional[str] = None
    secondary_causes: Optional[List[str]] = None
    
    diagnostic_tree: Optional[dict] = None
    
    verification_steps: Optional[List[dict]] = None
    resolution_steps: Optional[List[dict]] = None
    required_parts: Optional[List[dict]] = None
    
    vehicle_models: Optional[List[dict]] = None
    failure_conditions: Optional[List[dict]] = None
    
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    status: Optional[FailureCardStatus] = None
    confidence_score: Optional[float] = None

# ==================== ATTEMPTED DIAGNOSTIC MODEL (NEW) ====================

class AttemptedDiagnostic(BaseModel):
    """Records a single diagnostic attempt by technician"""
    step_id: str = Field(default_factory=lambda: f"diag_{uuid.uuid4().hex[:6]}")
    hypothesis: str                        # What they thought was wrong
    check_performed: str                   # What they did to verify
    result: str                            # What they found
    confirmed: bool                        # Did this confirm the hypothesis?
    tools_used: List[str] = []
    measurements: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RejectedHypothesis(BaseModel):
    """Records a hypothesis that was ruled out"""
    hypothesis: str                        # What was considered
    reason_rejected: str                   # Why it was ruled out
    evidence: str                          # What evidence disproved it
    ruled_out_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== TECHNICIAN ACTION MODEL (ENHANCED) ====================

class TechnicianAction(BaseModel):
    """
    Records technician diagnostic and repair actions
    
    Enhanced v2.0:
    - attempted_diagnostics: Full diagnostic journey
    - rejected_hypotheses: What was ruled out (for AI learning)
    """
    model_config = ConfigDict(extra="ignore")
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}")
    ticket_id: str
    technician_id: str
    technician_name: Optional[str] = None
    
    # === DIAGNOSTIC PHASE (ENHANCED) ===
    diagnostic_steps_performed: List[str] = []      # Simple list (legacy)
    attempted_diagnostics: List[AttemptedDiagnostic] = []  # NEW - Detailed attempts
    rejected_hypotheses: List[RejectedHypothesis] = []     # NEW - What was ruled out
    observations: List[str] = []
    measurements: Dict[str, Any] = {}
    photos: List[str] = []
    diagnostic_time_minutes: int = 0
    
    # === RESOLUTION ===
    parts_used: List[dict] = []
    resolution_steps_followed: List[str] = []
    resolution_outcome: str  # success, partial, failed, escalated
    resolution_time_minutes: int = 0
    
    # === FAILURE CARD INTERACTION ===
    failure_cards_suggested: List[str] = []  # IDs shown to technician
    failure_cards_viewed: List[str] = []     # IDs technician looked at
    failure_card_used: Optional[str] = None  # ID of card used
    failure_card_helpful: Optional[bool] = None
    failure_card_accuracy_rating: Optional[int] = None  # 1-5
    failure_card_modifications: List[str] = []  # What was different from card
    
    # === DISCOVERY ===
    new_failure_discovered: bool = False
    new_failure_description: Optional[str] = None
    new_failure_root_cause: Optional[str] = None
    new_failure_resolution: Optional[str] = None
    suggest_new_card: bool = False
    
    # === FEEDBACK ===
    technician_notes: Optional[str] = None
    difficulty_rating: Optional[int] = None  # 1-5
    documentation_quality_rating: Optional[int] = None  # 1-5 (how good was the card)
    time_spent_minutes: int = 0
    
    # === TIMESTAMPS ===
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class TechnicianActionCreate(BaseModel):
    ticket_id: str
    diagnostic_steps_performed: List[str] = []
    attempted_diagnostics: List[dict] = []    # NEW
    rejected_hypotheses: List[dict] = []      # NEW
    observations: List[str] = []
    measurements: Dict[str, Any] = {}
    parts_used: List[dict] = []
    resolution_outcome: str
    failure_card_used: Optional[str] = None
    failure_card_helpful: Optional[bool] = None
    failure_card_accuracy_rating: Optional[int] = None
    failure_card_modifications: List[str] = []
    new_failure_discovered: bool = False
    new_failure_description: Optional[str] = None
    new_failure_root_cause: Optional[str] = None
    new_failure_resolution: Optional[str] = None
    suggest_new_card: bool = False
    technician_notes: Optional[str] = None
    difficulty_rating: Optional[int] = None
    documentation_quality_rating: Optional[int] = None
    time_spent_minutes: int = 0

# ==================== PART USAGE MODEL (ENHANCED) ====================

class PartUsage(BaseModel):
    """
    Tracks parts consumption linked to failure cards
    
    Enhanced v2.0:
    - expected_vs_actual: Detect wrong diagnosis / hidden patterns
    - failure_card linkage for intelligence reinforcement
    """
    model_config = ConfigDict(extra="ignore")
    usage_id: str = Field(default_factory=lambda: f"use_{uuid.uuid4().hex[:12]}")
    ticket_id: str
    action_id: Optional[str] = None        # Link to TechnicianAction
    
    # === PART INFO ===
    part_id: str                           # Inventory item ID
    part_name: str
    part_number: Optional[str] = None      # SKU
    category: Optional[str] = None         # battery, motor, controller...
    
    # === QUANTITY ===
    quantity_allocated: int = 0            # Reserved from inventory
    quantity_used: int = 0                 # Actually consumed
    quantity_returned: int = 0             # Returned to inventory
    
    # === COST ===
    unit_cost: float = 0.0
    total_cost: float = 0.0
    
    # === FAILURE CARD LINK (for intelligence) ===
    failure_card_id: Optional[str] = None  # Which card recommended this part
    was_recommended: bool = False          # Was this part in card's required_parts?
    is_substitute: bool = False            # Was this a substitute?
    substitute_for: Optional[str] = None   # Original part it replaced
    
    # === EXPECTATION VS REALITY (NEW) ===
    expected_vs_actual: bool = True        # True if part usage matched expectation
    expectation_notes: Optional[str] = None  # Why it didn't match
    
    # === STATUS ===
    status: str = "allocated"              # allocated, used, returned, damaged
    
    # === TIMESTAMPS ===
    allocated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None

class PartUsageCreate(BaseModel):
    ticket_id: str
    action_id: Optional[str] = None
    part_id: str
    quantity_used: int
    failure_card_id: Optional[str] = None
    was_recommended: bool = False
    is_substitute: bool = False
    substitute_for: Optional[str] = None
    expected_vs_actual: bool = True
    expectation_notes: Optional[str] = None

# ==================== AI MATCHING MODELS (ENHANCED) ====================

class FailureMatchRequest(BaseModel):
    """Request for AI failure matching"""
    symptom_text: str
    error_codes: List[str] = []
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_mileage: Optional[int] = None
    subsystem_hint: Optional[SubsystemCategory] = None
    failure_mode_hint: Optional[FailureMode] = None
    
    # Failure signature components for direct matching
    temperature_range: Optional[str] = None
    load_condition: Optional[str] = None
    
    limit: int = 5

class FailureMatchResult(BaseModel):
    """Single match result from AI matching"""
    failure_id: str
    title: str
    match_score: float  # 0-1
    match_type: str     # signature, subsystem, semantic, keyword
    match_stage: int    # Which stage matched (1-4)
    matched_symptoms: List[str] = []
    matched_error_codes: List[str] = []
    confidence_level: ConfidenceLevel
    effectiveness_score: float = 0.0

class FailureMatchResponse(BaseModel):
    """Response from AI failure matching"""
    query_text: str
    signature_hash: Optional[str] = None
    matches: List[FailureMatchResult] = []
    processing_time_ms: float
    model_used: str
    matching_stages_used: List[str] = []

# ==================== KNOWLEDGE GRAPH MODELS (ENHANCED) ====================

class KnowledgeRelation(BaseModel):
    """Relationship in the knowledge graph"""
    relation_id: str = Field(default_factory=lambda: f"rel_{uuid.uuid4().hex[:8]}")
    source_type: str      # symptom, failure_card, part, vehicle, subsystem
    source_id: str
    source_label: Optional[str] = None
    relation_type: str    # causes, resolves, requires, affects, similar_to, co_occurs
    target_type: str
    target_id: str
    target_label: Optional[str] = None
    weight: float = 1.0   # Strength of relationship
    confidence: float = 0.5  # How sure are we
    evidence_count: int = 1  # How many times observed
    bidirectional: bool = False
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_observed_at: Optional[datetime] = None

class KnowledgeNode(BaseModel):
    """Node in the knowledge graph"""
    node_id: str
    node_type: str  # symptom, failure_card, part, vehicle, subsystem
    label: str
    properties: Dict[str, Any] = {}
    relations: List[str] = []  # relation_ids

# ==================== PATTERN DETECTION MODELS (NEW) ====================

class EmergingPattern(BaseModel):
    """
    Detected pattern for expert review
    EFI must discover intelligence, not only react
    """
    pattern_id: str = Field(default_factory=lambda: f"pat_{uuid.uuid4().hex[:12]}")
    pattern_type: str       # symptom_cluster, part_anomaly, failure_trend
    
    # Pattern details
    description: str
    detected_symptoms: List[str] = []
    affected_vehicles: List[dict] = []  # [{make, model, count}]
    affected_parts: List[dict] = []     # [{part_id, name, anomaly_type}]
    
    # Statistics
    occurrence_count: int = 0
    first_occurrence: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_occurrence: Optional[datetime] = None
    frequency: str = "unknown"  # daily, weekly, monthly, sporadic
    
    # Analysis
    has_linked_failure_card: bool = False
    linked_failure_card_id: Optional[str] = None
    confidence_score: float = 0.0
    
    # Status
    status: str = "detected"  # detected, under_review, confirmed, dismissed
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    
    # Action taken
    action_taken: Optional[str] = None  # created_card, updated_card, dismissed
    created_card_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PatternDetectionConfig(BaseModel):
    """Configuration for pattern detection job"""
    min_occurrences: int = 3            # Minimum times to see pattern
    lookback_days: int = 30             # How far back to analyze
    symptom_similarity_threshold: float = 0.7
    part_anomaly_threshold: float = 1.5  # Standard deviations from normal

# ==================== SYSTEM EVENTS (ENHANCED) ====================

class EFIEventType(str, Enum):
    """All event types in the EFI system"""
    # Ticket lifecycle
    TICKET_CREATED = "ticket.created"
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_IN_PROGRESS = "ticket.in_progress"
    TICKET_RESOLVED = "ticket.resolved"
    TICKET_CLOSED = "ticket.closed"
    
    # AI Matching
    MATCH_REQUESTED = "match.requested"
    MATCH_COMPLETED = "match.completed"
    MATCH_FAILED = "match.failed"
    
    # Technician actions
    ACTION_STARTED = "action.started"
    ACTION_COMPLETED = "action.completed"
    CARD_USED = "card.used"
    CARD_RATED = "card.rated"
    NEW_FAILURE_DISCOVERED = "failure.discovered"
    
    # Failure card lifecycle
    CARD_CREATED = "card.created"
    CARD_SUBMITTED = "card.submitted_for_review"
    CARD_APPROVED = "card.approved"
    CARD_DEPRECATED = "card.deprecated"
    CARD_UPDATED = "card.updated"
    
    # Confidence updates
    CONFIDENCE_UPDATED = "confidence.updated"
    EFFECTIVENESS_RECALCULATED = "effectiveness.recalculated"
    
    # Pattern detection (NEW)
    PATTERN_DETECTED = "pattern.detected"
    PATTERN_REVIEWED = "pattern.reviewed"
    PATTERN_ACTIONED = "pattern.actioned"
    
    # Network sync
    SYNC_REQUESTED = "sync.requested"
    SYNC_COMPLETED = "sync.completed"

class EFIEvent(BaseModel):
    """Event for event-driven processing"""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: str  # Use EFIEventType values
    source: str      # service that generated event
    priority: int = 5  # 1 (highest) to 10 (lowest)
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    processing_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
