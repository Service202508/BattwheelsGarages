"""
Battwheels OS - AI Guidance Models
Database models for EFI Guidance Layer: Snapshots and Feedback

P0.5 Foundation - Mandatory first implementation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import hashlib


# ==================== ENUMS ====================

class GuidanceMode(str, Enum):
    QUICK = "quick"   # 60-90 second read
    DEEP = "deep"     # Full decision tree


class GuidanceConfidence(str, Enum):
    HIGH = "high"       # 3+ matching sources, confidence >= 70%
    MEDIUM = "medium"   # 1-2 matching sources, confidence 40-70%
    LOW = "low"         # No matching sources - requires ask-back


class FeedbackType(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    UNSAFE = "unsafe"
    INCORRECT = "incorrect"
    STEP_FAILED = "step_failed"


class SnapshotStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"


# ==================== AI GUIDANCE SNAPSHOT ====================

class GuidanceDiagnosticStep(BaseModel):
    """Single diagnostic step in the guidance"""
    step: int
    action: str
    hinglish: str
    expected: Optional[str] = None
    pass_action: Optional[str] = None
    fail_action: Optional[str] = None


class GuidanceProbableCause(BaseModel):
    """Ranked probable cause"""
    cause: str
    confidence: int  # 0-100
    evidence: Optional[str] = None


class GuidanceEstimateSuggestion(BaseModel):
    """Part or labour suggestion for estimate"""
    type: str  # "part" or "labour"
    name: str
    category: Optional[str] = None
    quantity: int = 1
    hours: Optional[float] = None
    rate: Optional[float] = None
    estimated_cost: float = 0.0
    confidence: str = "medium"  # low, medium, high


class GuidanceDiagramSpec(BaseModel):
    """Mermaid diagram specification"""
    type: str = "mermaid"
    code: str
    title: Optional[str] = None


class GuidanceChartsSpec(BaseModel):
    """Micro-chart specifications"""
    soc_gauge: Optional[Dict[str, Any]] = None
    causes_chart: Optional[Dict[str, Any]] = None
    time_estimate: Optional[Dict[str, Any]] = None
    confidence_indicator: Optional[Dict[str, Any]] = None


class AIGuidanceSnapshot(BaseModel):
    """
    Versioned snapshot of AI-generated guidance.
    
    Purpose: Persist generated guidance for:
    - Reuse if context unchanged (idempotency)
    - Audit trail
    - Learning feedback loop
    - Technician reference
    
    Key Features:
    - input_context_hash for idempotency (regenerate only if context changed)
    - version tracking for superseded snapshots
    - tenant isolation via organization_id
    - Feature flag controlled
    """
    model_config = ConfigDict(extra="ignore")
    
    # === IDENTIFICATION ===
    snapshot_id: str = Field(default_factory=lambda: f"GS-{uuid.uuid4().hex[:12].upper()}")
    guidance_id: str = Field(default_factory=lambda: f"GD-{uuid.uuid4().hex[:8].upper()}")
    
    # === TENANT ISOLATION ===
    organization_id: str
    
    # === CONTEXT (for idempotency) ===
    ticket_id: str
    input_context_hash: str  # MD5 hash of input context for reuse detection
    
    # === GENERATION METADATA ===
    mode: GuidanceMode = GuidanceMode.QUICK
    confidence: GuidanceConfidence = GuidanceConfidence.MEDIUM
    version: int = 1  # Incremented when regenerated
    status: SnapshotStatus = SnapshotStatus.ACTIVE
    superseded_by: Optional[str] = None  # snapshot_id of newer version
    
    # === GUIDANCE CONTENT ===
    guidance_text: str = ""  # Full Hinglish guidance
    safety_block: str = ""   # Safety-first section
    symptom_summary: str = ""
    
    # === STRUCTURED DATA ===
    diagnostic_steps: List[GuidanceDiagnosticStep] = []
    probable_causes: List[GuidanceProbableCause] = []
    recommended_fix: str = ""
    
    # === VISUAL SPECS ===
    diagram_spec: Optional[GuidanceDiagramSpec] = None
    charts_spec: Optional[GuidanceChartsSpec] = None
    
    # === ESTIMATE INTEGRATION ===
    estimate_suggestions: List[GuidanceEstimateSuggestion] = []
    estimate_items_added: int = 0  # Count of items added to estimate
    
    # === SOURCES ===
    sources: List[Dict[str, Any]] = []  # Source citations
    sources_count: int = 0
    
    # === ASK-BACK ===
    needs_ask_back: bool = False
    ask_back_questions: List[Dict[str, Any]] = []
    ask_back_answers: Optional[Dict[str, Any]] = None
    
    # === VEHICLE CONTEXT (for model-aware ranking) ===
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    vehicle_category: Optional[str] = None  # 2W, 3W, 4W
    
    # === ISSUE CONTEXT ===
    symptoms: List[str] = []
    dtc_codes: List[str] = []
    category: str = "general"
    description: str = ""
    
    # === FEEDBACK METRICS ===
    feedback_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    unsafe_count: int = 0
    avg_rating: float = 0.0
    
    # === USAGE TRACKING ===
    view_count: int = 0
    last_viewed_at: Optional[str] = None
    regenerated_count: int = 0
    
    # === TIMESTAMPS ===
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None  # For auto-cleanup
    
    # === GENERATION STATS ===
    generation_time_ms: int = 0
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3-flash-preview"
    
    def compute_context_hash(self) -> str:
        """
        Generate deterministic hash for idempotency.
        Same context = same hash = can reuse snapshot.
        """
        components = [
            self.ticket_id,
            self.vehicle_make or "",
            self.vehicle_model or "",
            self.vehicle_variant or "",
            self.category,
            self.description[:200] if self.description else "",
            ",".join(sorted(self.symptoms)),
            ",".join(sorted(self.dtc_codes)),
            str(self.ask_back_answers) if self.ask_back_answers else ""
        ]
        hash_input = "|".join(components).lower().strip()
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]


class AIGuidanceSnapshotCreate(BaseModel):
    """Input model for creating a guidance snapshot"""
    ticket_id: str
    organization_id: str
    mode: str = "quick"
    
    # Context
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    vehicle_category: Optional[str] = None
    symptoms: List[str] = []
    dtc_codes: List[str] = []
    category: str = "general"
    description: str = ""
    
    # Ask-back answers (if provided)
    ask_back_answers: Optional[Dict[str, Any]] = None


# ==================== AI GUIDANCE FEEDBACK ====================

class AIGuidanceFeedback(BaseModel):
    """
    Feedback on AI guidance quality.
    
    Purpose:
    - Track helpfulness of guidance
    - Identify unsafe/incorrect guidance
    - Feed into continuous learning loop
    - Improve ranking algorithms
    
    Key Features:
    - Links to snapshot_id and guidance_id
    - Captures specific step failures
    - Tenant isolated
    - User tracking for accountability
    """
    model_config = ConfigDict(extra="ignore")
    
    # === IDENTIFICATION ===
    feedback_id: str = Field(default_factory=lambda: f"GF-{uuid.uuid4().hex[:12].upper()}")
    
    # === LINKS ===
    guidance_id: str
    snapshot_id: Optional[str] = None
    ticket_id: str
    
    # === TENANT ISOLATION ===
    organization_id: str
    
    # === USER ===
    user_id: str
    user_name: Optional[str] = None
    user_role: Optional[str] = None  # technician, admin, etc.
    
    # === FEEDBACK TYPE ===
    feedback_type: FeedbackType = FeedbackType.HELPFUL
    helped: bool = True
    rating: Optional[int] = None  # 1-5 stars
    
    # === ISSUE DETAILS ===
    unsafe: bool = False
    incorrect: bool = False
    step_failed: Optional[int] = None  # Which step failed (1-indexed)
    failed_step_action: Optional[str] = None
    
    # === DETAILED FEEDBACK ===
    comment: Optional[str] = None
    correct_diagnosis: Optional[str] = None  # What was actually wrong
    actual_fix: Optional[str] = None  # What actually fixed it
    missing_parts: List[str] = []  # Parts that should have been suggested
    missing_steps: List[str] = []  # Steps that were missing
    
    # === RESOLUTION OUTCOME ===
    issue_resolved: bool = True
    resolution_time_minutes: Optional[int] = None
    escalated: bool = False
    
    # === TIMESTAMPS ===
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # === LEARNING FLAG ===
    processed_for_learning: bool = False
    processed_at: Optional[str] = None


class AIGuidanceFeedbackCreate(BaseModel):
    """Input model for submitting feedback"""
    guidance_id: str
    ticket_id: str
    helped: bool
    
    # Optional details
    unsafe: bool = False
    incorrect: bool = False
    step_failed: Optional[int] = None
    comment: Optional[str] = None
    rating: Optional[int] = None
    correct_diagnosis: Optional[str] = None
    actual_fix: Optional[str] = None


# ==================== FAILURE CARD (Enhanced for Intelligence Engine) ====================

class StructuredFailureCard(BaseModel):
    """
    Normalized Failure Card schema for Model-Aware Ranking.
    
    Part A of Phase 2 - Structured Failure Ontology
    
    Key Fields for Ranking:
    - vehicle_make, vehicle_model, vehicle_variant (model match)
    - subsystem (subsystem match)
    - symptom_cluster (symptom similarity)
    - dtc_code (DTC match)
    - historical_success_rate (success-based ranking)
    - recurrence_counter (frequency-based ranking)
    """
    model_config = ConfigDict(extra="ignore")
    
    # === IDENTIFICATION ===
    failure_card_id: str = Field(default_factory=lambda: f"FC-{uuid.uuid4().hex[:12].upper()}")
    
    # === TENANT ISOLATION ===
    organization_id: Optional[str] = None  # None = global/battwheels curated
    scope: str = "global"  # "global" or "tenant"
    
    # === VEHICLE CLASSIFICATION ===
    vehicle_make: Optional[str] = None     # Ola, Ather, TVS, Bajaj, Hero, etc.
    vehicle_model: Optional[str] = None    # S1 Pro, 450X, iQube, etc.
    vehicle_variant: Optional[str] = None  # Gen1, Gen2, Plus, etc.
    vehicle_category: str = "2W"           # 2W, 3W, 4W
    
    # === SUBSYSTEM ===
    subsystem: str  # battery, motor, controller, charger, bms, electrical, etc.
    component: Optional[str] = None  # More specific: cell_module, hall_sensor, etc.
    
    # === SYMPTOMS ===
    symptom_cluster: List[str] = []  # Primary symptoms
    symptom_text: Optional[str] = None  # Free-text description
    
    # === DTC CODES ===
    dtc_code: Optional[str] = None  # Primary DTC
    dtc_codes: List[str] = []       # All related DTCs
    
    # === ROOT CAUSE ===
    probable_root_cause: str
    secondary_causes: List[str] = []
    
    # === VERIFIED FIX ===
    verified_fix: str
    fix_steps: List[str] = []
    parts_required: List[str] = []
    estimated_repair_time_minutes: int = 60
    
    # === INTELLIGENCE METRICS (for Model-Aware Ranking) ===
    historical_success_rate: float = 0.5  # 0.0 to 1.0
    recurrence_counter: int = 0           # How many times this failure occurred
    usage_count: int = 0                  # Times this card was used
    positive_feedback_count: int = 0
    negative_feedback_count: int = 0
    
    # === CONFIDENCE ===
    confidence_score: float = 0.5  # 0.0 to 1.0
    last_confidence_update: Optional[str] = None
    
    # === TIMESTAMPS ===
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    first_detected_at: Optional[str] = None
    last_used_at: Optional[str] = None
    
    # === APPROVAL ===
    status: str = "draft"  # draft, pending_review, approved, deprecated
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    
    # === SOURCE ===
    source_type: str = "field_discovery"  # field_discovery, oem_input, pattern_detection
    source_ticket_id: Optional[str] = None


# ==================== MODEL RISK ALERT (Part E - Pattern Detection) ====================

class ModelRiskAlert(BaseModel):
    """
    Alert for detected pattern (Part E - Lean Pattern Detection).
    
    Triggered when:
    - ≥3 similar failures in 30 days
    - Same model + subsystem combination
    
    Displayed only in supervisor dashboard.
    """
    model_config = ConfigDict(extra="ignore")
    
    alert_id: str = Field(default_factory=lambda: f"MRA-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str
    
    # Pattern details
    vehicle_make: str
    vehicle_model: str
    subsystem: str
    
    # Statistics
    occurrence_count: int
    first_occurrence: str
    last_occurrence: str
    affected_ticket_ids: List[str] = []
    
    # Status
    status: str = "active"  # active, acknowledged, resolved, dismissed
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    # Linked failure card (if created)
    linked_failure_card_id: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
