"""
Battwheels OS - Failure Intelligence Models
Core data models for the EV Failure Intelligence (EFI) Platform
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

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
    LOW = "low"       # < 0.4
    MEDIUM = "medium" # 0.4 - 0.7
    HIGH = "high"     # 0.7 - 0.9
    VERIFIED = "verified" # > 0.9

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

# ==================== MAIN FAILURE CARD MODEL ====================

class FailureCard(BaseModel):
    """
    Core entity: EV Failure Intelligence Card
    This is the most important entity in the system.
    """
    model_config = ConfigDict(extra="ignore")
    
    # Identification
    failure_id: str = Field(default_factory=lambda: f"fc_{uuid.uuid4().hex[:12]}")
    title: str
    description: Optional[str] = None
    
    # Classification
    subsystem_category: SubsystemCategory
    failure_mode: FailureMode = FailureMode.COMPLETE_FAILURE
    
    # Symptoms (Knowledge Graph Links)
    symptoms: List[Symptom] = []
    symptom_codes: List[str] = []  # Quick reference codes
    symptom_text: Optional[str] = None  # Free-text symptom description
    error_codes: List[str] = []  # OEM error codes
    
    # Root Cause Analysis
    root_cause: str
    root_cause_details: Optional[str] = None
    secondary_causes: List[str] = []
    
    # Diagnostic Process
    verification_steps: List[VerificationStep] = []
    diagnostic_tools: List[str] = []
    diagnostic_duration_minutes: int = 30
    
    # Resolution
    resolution_steps: List[ResolutionStep] = []
    resolution_summary: Optional[str] = None
    estimated_repair_time_minutes: int = 60
    skill_level_required: str = "intermediate"
    
    # Parts
    required_parts: List[RequiredPart] = []
    estimated_parts_cost: float = 0.0
    estimated_labor_cost: float = 0.0
    estimated_total_cost: float = 0.0
    
    # Vehicle Compatibility
    vehicle_models: List[VehicleCompatibility] = []
    universal_failure: bool = False  # Applies to all EVs
    
    # Conditions
    failure_conditions: List[FailureCondition] = []
    
    # Intelligence Metrics
    confidence_score: float = 0.5  # 0.0 - 1.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    effectiveness_score: float = 0.0
    
    # AI/ML Metadata
    embedding_vector: Optional[List[float]] = None  # For semantic search
    keywords: List[str] = []
    tags: List[str] = []
    
    # Versioning
    version: int = 1
    status: FailureCardStatus = FailureCardStatus.DRAFT
    
    # Provenance
    source_ticket_id: Optional[str] = None  # Original ticket that created this
    source_garage_id: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    
    # Version History
    version_history: List[Dict[str, Any]] = []
    
    # Network Sync
    synced_to_network: bool = False
    last_sync_at: Optional[datetime] = None

class FailureCardCreate(BaseModel):
    """Input model for creating a failure card"""
    title: str
    description: Optional[str] = None
    subsystem_category: SubsystemCategory
    failure_mode: FailureMode = FailureMode.COMPLETE_FAILURE
    
    symptom_codes: List[str] = []
    symptom_text: Optional[str] = None
    error_codes: List[str] = []
    
    root_cause: str
    root_cause_details: Optional[str] = None
    secondary_causes: List[str] = []
    
    verification_steps: List[dict] = []
    resolution_steps: List[dict] = []
    required_parts: List[dict] = []
    
    vehicle_models: List[dict] = []
    universal_failure: bool = False
    failure_conditions: List[dict] = []
    
    keywords: List[str] = []
    tags: List[str] = []
    
    source_ticket_id: Optional[str] = None

class FailureCardUpdate(BaseModel):
    """Input model for updating a failure card"""
    title: Optional[str] = None
    description: Optional[str] = None
    subsystem_category: Optional[SubsystemCategory] = None
    failure_mode: Optional[FailureMode] = None
    
    symptom_codes: Optional[List[str]] = None
    symptom_text: Optional[str] = None
    error_codes: Optional[List[str]] = None
    
    root_cause: Optional[str] = None
    root_cause_details: Optional[str] = None
    secondary_causes: Optional[List[str]] = None
    
    verification_steps: Optional[List[dict]] = None
    resolution_steps: Optional[List[dict]] = None
    required_parts: Optional[List[dict]] = None
    
    vehicle_models: Optional[List[dict]] = None
    failure_conditions: Optional[List[dict]] = None
    
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    status: Optional[FailureCardStatus] = None
    confidence_score: Optional[float] = None

# ==================== TECHNICIAN ACTION MODEL ====================

class TechnicianAction(BaseModel):
    """Records technician diagnostic and repair actions"""
    model_config = ConfigDict(extra="ignore")
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}")
    ticket_id: str
    technician_id: str
    
    # Diagnostic
    diagnostic_steps_performed: List[str] = []
    observations: List[str] = []
    measurements: Dict[str, Any] = {}
    photos: List[str] = []
    
    # Resolution
    parts_used: List[dict] = []
    resolution_steps_followed: List[str] = []
    resolution_outcome: str  # success, partial, failed, escalated
    
    # Failure Card Interaction
    failure_cards_suggested: List[str] = []  # IDs
    failure_card_used: Optional[str] = None  # ID of card used
    failure_card_helpful: Optional[bool] = None
    new_failure_discovered: bool = False
    
    # Feedback
    technician_notes: Optional[str] = None
    difficulty_rating: Optional[int] = None  # 1-5
    time_spent_minutes: int = 0
    
    # Timestamps
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class TechnicianActionCreate(BaseModel):
    ticket_id: str
    diagnostic_steps_performed: List[str] = []
    observations: List[str] = []
    measurements: Dict[str, Any] = {}
    parts_used: List[dict] = []
    resolution_outcome: str
    failure_card_used: Optional[str] = None
    failure_card_helpful: Optional[bool] = None
    new_failure_discovered: bool = False
    technician_notes: Optional[str] = None
    difficulty_rating: Optional[int] = None
    time_spent_minutes: int = 0

# ==================== AI MATCHING MODELS ====================

class FailureMatchRequest(BaseModel):
    """Request for AI failure matching"""
    symptom_text: str
    error_codes: List[str] = []
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    subsystem_hint: Optional[SubsystemCategory] = None
    limit: int = 5

class FailureMatchResult(BaseModel):
    """Single match result from AI matching"""
    failure_id: str
    title: str
    match_score: float  # 0-1
    match_type: str  # exact, semantic, partial
    matched_symptoms: List[str] = []
    confidence_level: ConfidenceLevel

class FailureMatchResponse(BaseModel):
    """Response from AI failure matching"""
    query_text: str
    matches: List[FailureMatchResult] = []
    processing_time_ms: float
    model_used: str

# ==================== KNOWLEDGE GRAPH MODELS ====================

class KnowledgeRelation(BaseModel):
    """Relationship in the knowledge graph"""
    relation_id: str = Field(default_factory=lambda: f"rel_{uuid.uuid4().hex[:8]}")
    source_type: str  # symptom, failure, part, vehicle, subsystem
    source_id: str
    relation_type: str  # causes, resolves, requires, affects, similar_to
    target_type: str
    target_id: str
    weight: float = 1.0  # Strength of relationship
    metadata: Dict[str, Any] = {}

class KnowledgeNode(BaseModel):
    """Node in the knowledge graph"""
    node_id: str
    node_type: str  # symptom, failure, part, vehicle, subsystem
    label: str
    properties: Dict[str, Any] = {}
    relations: List[str] = []  # relation_ids

# ==================== SYSTEM EVENTS ====================

class EFIEvent(BaseModel):
    """Event for event-driven processing"""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: str  # ticket_created, ticket_resolved, failure_card_created, match_performed
    source: str  # service that generated event
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processing_result: Optional[Dict[str, Any]] = None
