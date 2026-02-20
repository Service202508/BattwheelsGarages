"""
Battwheels Knowledge Brain - Database Models
Multi-tenant knowledge base for EV diagnostics with RAG support
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class KnowledgeType(str, Enum):
    FAILURE_CARD = "failure_card"
    REPAIR_PROCEDURE = "repair_procedure"
    FAULT_TREE = "fault_tree"
    ERROR_CODE = "error_code"
    SAFETY_PROTOCOL = "safety_protocol"
    MANUAL = "manual"
    RESOLVED_TICKET = "resolved_ticket"
    SOP = "sop"


class KnowledgeScope(str, Enum):
    GLOBAL = "global"  # Battwheels curated - available to all tenants
    TENANT = "tenant"  # Tenant-specific knowledge


class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class VehicleCategory(str, Enum):
    TWO_WHEELER = "2W"
    THREE_WHEELER = "3W"
    FOUR_WHEELER = "4W"


class Subsystem(str, Enum):
    BATTERY = "battery"
    BMS = "bms"
    MOTOR = "motor"
    CONTROLLER = "controller"
    CHARGER = "charger"
    TELEMATICS = "telematics"
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    SOFTWARE = "software"


class Severity(str, Enum):
    CRITICAL = "critical"  # Safety hazard
    HIGH = "high"          # Vehicle inoperable
    MEDIUM = "medium"      # Reduced functionality
    LOW = "low"            # Minor issue


# ==================== KNOWLEDGE BASE MODELS ====================

class KnowledgeArticle(BaseModel):
    """Core knowledge article model for the Knowledge Brain"""
    knowledge_id: str
    organization_id: Optional[str] = None  # None for global knowledge
    scope: KnowledgeScope = KnowledgeScope.GLOBAL
    knowledge_type: KnowledgeType
    
    # Content
    title: str
    summary: str
    content: str  # Markdown formatted
    symptoms: List[str] = []
    dtc_codes: List[str] = []  # Diagnostic Trouble Codes
    
    # Vehicle context
    vehicle_category: Optional[VehicleCategory] = None
    vehicle_make: Optional[str] = None  # Ola, Ather, TVS, etc.
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    
    # Classification
    subsystem: Optional[Subsystem] = None
    tags: List[str] = []
    severity: Optional[Severity] = None
    
    # Quality metrics
    confidence_score: float = 0.8  # 0.0 to 1.0
    usage_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    
    # Approval workflow
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    version: int = 1
    
    # Timestamps
    created_at: str
    updated_at: str
    last_verified_at: Optional[str] = None
    
    # Source tracking
    source_type: Optional[str] = None  # "ticket", "manual", "expert"
    source_id: Optional[str] = None    # Original ticket_id, document_id, etc.
    
    # Embeddings for RAG (stored separately for efficiency)
    embedding_id: Optional[str] = None


class FailureCard(BaseModel):
    """Structured failure card - extends knowledge article"""
    failure_card_id: str
    knowledge_id: str  # Link to knowledge article
    organization_id: Optional[str] = None
    scope: KnowledgeScope = KnowledgeScope.GLOBAL
    
    # Problem definition
    problem_title: str
    problem_description: str
    symptoms: List[str] = []
    dtc_codes: List[str] = []
    error_messages: List[str] = []
    
    # Vehicle info
    vehicle_category: Optional[VehicleCategory] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    subsystem: Optional[Subsystem] = None
    component: Optional[str] = None
    
    # Diagnosis
    preliminary_checks: List[str] = []  # Safety/visual checks first
    diagnostic_steps: List[Dict[str, Any]] = []  # Step-by-step with decisions
    test_points: List[Dict[str, Any]] = []  # Measurement points with expected values
    
    # Root causes (ranked by probability)
    probable_causes: List[Dict[str, Any]] = []  # [{cause, probability, evidence}]
    
    # Resolution
    fix_procedures: List[Dict[str, Any]] = []  # Step-by-step fixes
    parts_required: List[Dict[str, Any]] = []  # [{part_name, part_number, qty}]
    tools_required: List[str] = []
    estimated_repair_time: Optional[int] = None  # minutes
    
    # Safety
    safety_warnings: List[str] = []
    ppe_required: List[str] = []
    high_voltage_involved: bool = False
    
    # Escalation
    escalation_triggers: List[str] = []  # When to escalate
    expert_notes: Optional[str] = None
    
    # Quality
    confidence_score: float = 0.8
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    last_verified_at: Optional[str] = None
    
    # Timestamps
    created_at: str
    updated_at: str


class ErrorCodeDefinition(BaseModel):
    """Error/DTC code definitions"""
    code_id: str
    organization_id: Optional[str] = None
    scope: KnowledgeScope = KnowledgeScope.GLOBAL
    
    dtc_code: str  # e.g., "P0A1F", "U0100"
    code_standard: str  # "OBD2", "CAN", "Proprietary"
    
    description: str
    detailed_explanation: str
    
    # Related info
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    subsystem: Optional[Subsystem] = None
    severity: Severity = Severity.MEDIUM
    
    # Resolution
    common_causes: List[str] = []
    diagnostic_steps: List[str] = []
    related_failure_cards: List[str] = []  # failure_card_ids
    
    created_at: str
    updated_at: str


# ==================== AI INTERACTION MODELS ====================

class AIQueryRequest(BaseModel):
    """Request model for AI assistance"""
    query: str
    category: str = "general"  # general, battery, motor, electrical, diagnosis
    
    # Context for better answers
    ticket_id: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_category: Optional[VehicleCategory] = None
    dtc_codes: List[str] = []
    symptoms: List[str] = []
    
    # User context
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    organization_id: Optional[str] = None
    portal_type: str = "technician"


class AISource(BaseModel):
    """Source citation for AI response"""
    source_id: str
    source_type: str  # "failure_card", "manual", "ticket", "error_code"
    title: str
    relevance_score: float
    snippet: str
    link: Optional[str] = None  # Internal link to view full source


class AIQueryResponse(BaseModel):
    """Response model for AI assistance"""
    response: str
    ai_enabled: bool = True
    category: str = "general"
    
    # Source citations
    sources: List[AISource] = []
    sources_used: int = 0
    
    # Structured response components
    diagnosis_summary: Optional[str] = None
    confidence_level: str = "medium"  # low, medium, high
    safety_warnings: List[str] = []
    diagnostic_steps: List[Dict[str, Any]] = []
    probable_causes: List[Dict[str, Any]] = []
    recommended_parts: List[Dict[str, Any]] = []
    escalation_recommended: bool = False
    escalation_reason: Optional[str] = None
    
    # Suggestions
    estimate_suggestions: List[Dict[str, Any]] = []  # Parts/labor to add
    
    # Tracking
    query_id: str
    response_time_ms: int = 0


class AIFeedback(BaseModel):
    """Feedback on AI response"""
    query_id: str
    feedback_type: str  # "helpful", "not_helpful", "wrong", "unsafe"
    reason: Optional[str] = None
    missing_info: Optional[str] = None
    correct_answer: Optional[str] = None
    user_id: str
    organization_id: str
    created_at: str


class EscalationRequest(BaseModel):
    """Request to escalate to human expert"""
    query_id: str
    ticket_id: Optional[str] = None
    organization_id: str
    
    # Context
    original_query: str
    ai_response: str
    sources_checked: List[str] = []
    
    # Vehicle info
    vehicle_info: Optional[Dict[str, Any]] = None
    symptoms: List[str] = []
    dtc_codes: List[str] = []
    
    # Attachments
    images: List[str] = []
    documents: List[str] = []
    
    # Priority
    urgency: str = "normal"  # low, normal, high, critical
    reason: str
    
    # User
    user_id: str
    user_name: str


# ==================== FEATURE FLAGS ====================

class TenantAIConfig(BaseModel):
    """Per-tenant AI configuration"""
    organization_id: str
    
    # Feature flags
    ai_assist_enabled: bool = True
    zendesk_enabled: bool = False
    knowledge_ingestion_enabled: bool = True
    auto_suggest_enabled: bool = True
    
    # Zendesk config (if enabled)
    zendesk_subdomain: Optional[str] = None
    zendesk_api_token: Optional[str] = None
    zendesk_email: Optional[str] = None
    
    # Customization
    custom_system_prompt: Optional[str] = None
    blocked_categories: List[str] = []
    
    # Limits
    daily_query_limit: int = 1000
    queries_today: int = 0
    
    created_at: str
    updated_at: str
