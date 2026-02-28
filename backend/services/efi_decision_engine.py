"""
EFI Decision Tree Engine - Guided Diagnostic Execution
Handles step-by-step diagnostics with PASS/FAIL branching
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)


# ==================== PYDANTIC MODELS ====================

class DiagnosticStep(BaseModel):
    """Single diagnostic step in decision tree"""
    step_id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    order: int
    instruction: str
    expected_measurement: Optional[str] = None
    reference_image: Optional[str] = None  # URL to diagram/image
    tools_required: List[str] = []
    safety_notes: Optional[str] = None
    pass_action: str = "next"  # "next", "skip_to:{step_id}", "resolution:{resolution_id}"
    fail_action: str = "next"  # Same format
    pass_next_step: Optional[str] = None
    fail_next_step: Optional[str] = None


class ResolutionNode(BaseModel):
    """Resolution endpoint in decision tree"""
    resolution_id: str = Field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    parts_required: List[Dict[str, Any]] = []  # [{"part_id": "", "name": "", "quantity": 1, "price": 0}]
    labor_hours: float = 0.0
    labor_rate: float = 500.0  # Per hour
    expected_time_minutes: int = 60
    success_rate: float = 0.85


class DecisionTree(BaseModel):
    """Complete diagnostic decision tree"""
    tree_id: str = Field(default_factory=lambda: f"tree_{uuid.uuid4().hex[:8]}")
    failure_card_id: str
    version: int = 1
    steps: List[DiagnosticStep] = []
    resolutions: List[ResolutionNode] = []
    entry_step_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StepOutcome(BaseModel):
    """Record of technician completing a step"""
    step_id: str
    outcome: str  # "pass" or "fail"
    actual_measurement: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    time_taken_seconds: int = 0


class EFISession(BaseModel):
    """Active EFI diagnostic session for a job card"""
    session_id: str = Field(default_factory=lambda: f"efi_{uuid.uuid4().hex[:8]}")
    ticket_id: str
    job_card_id: Optional[str] = None
    failure_card_id: str
    tree_id: str
    current_step_id: Optional[str] = None
    completed_steps: List[StepOutcome] = []
    status: str = "active"  # "active", "completed", "abandoned"
    selected_resolution_id: Optional[str] = None
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    technician_id: Optional[str] = None
    technician_name: Optional[str] = None


# ==================== DECISION TREE ENGINE ====================

class EFIDecisionTreeEngine:
    """Engine for executing diagnostic decision trees"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_tree_for_card(self, failure_card_id: str) -> Optional[Dict]:
        """Get decision tree for a failure card"""
        tree = await self.db.efi_decision_trees.find_one(
            {"failure_card_id": failure_card_id},
            {"_id": 0}
        )
        return tree
    
    async def create_tree(self, tree: DecisionTree) -> Dict:
        """Create a new decision tree"""
        tree_dict = tree.model_dump()
        
        # Set entry step
        if tree.steps and not tree.entry_step_id:
            tree_dict["entry_step_id"] = tree.steps[0].step_id
        
        await self.db.efi_decision_trees.insert_one(tree_dict)
        return tree_dict
    
    async def start_session(
        self, 
        ticket_id: str, 
        failure_card_id: str,
        org_id: str,
        technician_id: Optional[str] = None,
        technician_name: Optional[str] = None
    ) -> Dict:
        """Start a new EFI diagnostic session"""
        
        # Get the decision tree (TIER 2 — no org_id)
        tree = await self.get_tree_for_card(failure_card_id)
        if not tree:
            raise ValueError(f"No decision tree found for failure card {failure_card_id}")
        
        # Create session
        session = EFISession(
            ticket_id=ticket_id,
            failure_card_id=failure_card_id,
            tree_id=tree["tree_id"],
            current_step_id=tree.get("entry_step_id"),
            technician_id=technician_id,
            technician_name=technician_name
        )
        
        session_dict = session.model_dump()
        session_dict["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
        await self.db.efi_sessions.insert_one(session_dict.copy())
        
        # Return session with current step details
        current_step = None
        if session.current_step_id:
            for step in tree.get("steps", []):
                if step["step_id"] == session.current_step_id:
                    current_step = step
                    break
        
        return {
            **session_dict,
            "current_step": current_step,
            "tree": tree
        }
    
    async def get_session(self, session_id: str, org_id: str = None) -> Optional[Dict]:
        """Get session with current step details"""
        query = {"session_id": session_id}
        if org_id:
            query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
        session = await self.db.efi_sessions.find_one(query, {"_id": 0})
        
        if not session:
            return None
        
        # Get tree and current step
        tree = await self.db.efi_decision_trees.find_one(
            {"tree_id": session["tree_id"]},
            {"_id": 0}
        )
        
        current_step = None
        if tree and session.get("current_step_id"):
            for step in tree.get("steps", []):
                if step["step_id"] == session["current_step_id"]:
                    current_step = step
                    break
        
        return {
            **session,
            "current_step": current_step,
            "tree": tree
        }
    
    async def get_session_by_ticket(self, ticket_id: str, org_id: str = None) -> Optional[Dict]:
        """Get active session for a ticket"""
        query = {"ticket_id": ticket_id, "status": "active"}
        if org_id:
            query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
        session = await self.db.efi_sessions.find_one(query, {"_id": 0})
        
        if session:
            return await self.get_session(session["session_id"])
        return None
    
    async def record_step_outcome(
        self,
        session_id: str,
        step_id: str,
        outcome: str,  # "pass" or "fail"
        org_id: str = None,
        actual_measurement: Optional[str] = None,
        notes: Optional[str] = None,
        time_taken_seconds: int = 0
    ) -> Dict:
        """Record step outcome and advance to next step"""
        
        session_query = {"session_id": session_id}
        if org_id:
            session_query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
        session = await self.db.efi_sessions.find_one(session_query)
        if not session:
            raise ValueError("Session not found")
        
        tree = await self.db.efi_decision_trees.find_one({"tree_id": session["tree_id"]})
        if not tree:
            raise ValueError("Decision tree not found")
        
        # Find current step
        current_step = None
        for step in tree.get("steps", []):
            if step["step_id"] == step_id:
                current_step = step
                break
        
        if not current_step:
            raise ValueError("Step not found")
        
        # Create outcome record
        step_outcome = StepOutcome(
            step_id=step_id,
            outcome=outcome,
            actual_measurement=actual_measurement,
            notes=notes,
            time_taken_seconds=time_taken_seconds
        )
        
        # Determine next action
        action = current_step.get("pass_action" if outcome == "pass" else "fail_action", "next")
        next_step_field = "pass_next_step" if outcome == "pass" else "fail_next_step"
        next_step_id = current_step.get(next_step_field)
        
        update_data = {
            "$push": {"completed_steps": step_outcome.model_dump()},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
        
        result = {
            "action": action,
            "outcome_recorded": True
        }
        
        if action.startswith("resolution:"):
            # Reached a resolution
            resolution_id = action.split(":")[1]
            update_data["$set"]["status"] = "completed"
            update_data["$set"]["selected_resolution_id"] = resolution_id
            update_data["$set"]["completed_at"] = datetime.now(timezone.utc).isoformat()
            update_data["$set"]["current_step_id"] = None
            
            # Get resolution details
            for res in tree.get("resolutions", []):
                if res["resolution_id"] == resolution_id:
                    result["resolution"] = res
                    break
            
            result["session_completed"] = True
        elif action == "next" or next_step_id:
            # Move to next step
            if next_step_id:
                next_step_id = next_step_id
            else:
                # Find next step by order
                current_order = current_step.get("order", 0)
                next_step = None
                for step in sorted(tree.get("steps", []), key=lambda s: s.get("order", 0)):
                    if step.get("order", 0) > current_order:
                        next_step = step
                        break
                next_step_id = next_step["step_id"] if next_step else None
            
            if next_step_id:
                update_data["$set"]["current_step_id"] = next_step_id
                # Get next step details
                for step in tree.get("steps", []):
                    if step["step_id"] == next_step_id:
                        result["next_step"] = step
                        break
            else:
                # No more steps - auto-complete if we have a default resolution
                if tree.get("resolutions"):
                    default_res = tree["resolutions"][0]
                    update_data["$set"]["status"] = "completed"
                    update_data["$set"]["selected_resolution_id"] = default_res["resolution_id"]
                    update_data["$set"]["completed_at"] = datetime.now(timezone.utc).isoformat()
                    result["resolution"] = default_res
                    result["session_completed"] = True
        
        await self.db.efi_sessions.update_one(
            {"session_id": session_id, "organization_id": session.get("organization_id")},
            update_data
        )
        
        # Log action (TIER 1: org-scoped — Sprint 1C)
        await self.db.technician_action_logs.insert_one({
            "log_id": f"log_{uuid.uuid4().hex[:8]}",
            "organization_id": session.get("organization_id"),
            "session_id": session_id,
            "ticket_id": session["ticket_id"],
            "step_id": step_id,
            "outcome": outcome,
            "action_type": "diagnostic_step",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "technician_id": session.get("technician_id")
        })
        
        return result
    
    async def get_suggested_estimate(self, session_id: str, org_id: str = None) -> Optional[Dict]:
        """Get smart estimate from completed session"""
        query = {"session_id": session_id}
        if org_id:
            query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
        session = await self.db.efi_sessions.find_one(query)
        if not session or session.get("status") != "completed":
            return None
        
        tree = await self.db.efi_decision_trees.find_one({"tree_id": session["tree_id"]})
        if not tree:
            return None
        
        resolution_id = session.get("selected_resolution_id")
        resolution = None
        for res in tree.get("resolutions", []):
            if res["resolution_id"] == resolution_id:
                resolution = res
                break
        
        if not resolution:
            return None
        
        # Calculate estimate
        parts_total = sum(
            p.get("price", 0) * p.get("quantity", 1) 
            for p in resolution.get("parts_required", [])
        )
        labor_total = resolution.get("labor_hours", 1) * resolution.get("labor_rate", 500)
        
        return {
            "resolution": resolution,
            "parts": resolution.get("parts_required", []),
            "parts_total": parts_total,
            "labor_hours": resolution.get("labor_hours", 1),
            "labor_rate": resolution.get("labor_rate", 500),
            "labor_total": labor_total,
            "estimated_total": parts_total + labor_total,
            "expected_time_minutes": resolution.get("expected_time_minutes", 60),
            "gst_rate": 18,
            "gst_amount": (parts_total + labor_total) * 0.18,
            "grand_total": (parts_total + labor_total) * 1.18
        }


# ==================== LEARNING ENGINE ====================

class EFILearningEngine:
    """Captures job completion data for continuous learning"""
    
    def __init__(self, db):
        self.db = db
    
    async def capture_job_completion(
        self,
        ticket_id: str,
        org_id: str,
        session_id: Optional[str] = None,
        actual_resolution: Optional[str] = None,
        actual_parts_used: List[Dict] = None,
        actual_time_minutes: int = 0,
        deviation_notes: Optional[str] = None,
        outcome: str = "success"  # "success", "partial", "failure"
    ) -> Dict:
        """Capture job completion data for learning"""
        
        learning_entry = {
            "entry_id": f"learn_{uuid.uuid4().hex[:8]}",
            "organization_id": org_id,  # TIER 1: org-scoped — Sprint 1C
            "ticket_id": ticket_id,
            "session_id": session_id,
            "actual_resolution": actual_resolution,
            "actual_parts_used": actual_parts_used or [],
            "actual_time_minutes": actual_time_minutes,
            "deviation_notes": deviation_notes,
            "outcome": outcome,
            "status": "pending_review",  # Requires engineer approval
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewed_by": None,
            "proposed_card_id": None
        }
        
        # Check if this suggests a new failure card
        if session_id:
            session_query = {"session_id": session_id}
            if org_id:
                session_query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
            session = await self.db.efi_sessions.find_one(session_query)
            if session:
                # If there's significant deviation, propose new card
                has_deviation = (
                    deviation_notes or 
                    outcome != "success" or
                    (actual_parts_used and len(actual_parts_used) > 0)
                )
                if has_deviation:
                    learning_entry["suggest_new_card"] = True
        
        await self.db.efi_learning_queue.insert_one(learning_entry)
        
        return learning_entry
    
    async def get_pending_learning_items(self, limit: int = 50, org_id: str = None) -> List[Dict]:
        """Get items pending engineer review"""
        query = {"status": "pending_review"}
        if org_id:
            query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
        items = await self.db.efi_learning_queue.find(
            query,
            {"_id": 0}
        ).sort("captured_at", -1).limit(limit).to_list(limit)
        return items
    
    async def approve_learning_item(
        self,
        entry_id: str,
        action: str,  # "create_card", "update_card", "dismiss"
        reviewer_id: str,
        reviewer_name: str,
        org_id: str = None,
        notes: Optional[str] = None
    ) -> Dict:
        """Review and act on learning item"""
        
        query = {"entry_id": entry_id}
        if org_id:
            query["organization_id"] = org_id  # TIER 1: org-scoped — Sprint 1C
        item = await self.db.efi_learning_queue.find_one(query)
        if not item:
            raise ValueError("Learning item not found")
        
        update = {
            "status": "reviewed",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": reviewer_name,
            "review_action": action,
            "review_notes": notes
        }
        
        if action == "create_card":
            # Create draft failure card from learning
            # This would need more context from the ticket
            update["proposed_card_created"] = True
        
        await self.db.efi_learning_queue.update_one(
            {"entry_id": entry_id, "organization_id": item.get("organization_id")},
            {"$set": update}
        )
        
        return {**item, **update}


# ==================== SINGLETON INSTANCES ====================

_decision_engine: Optional[EFIDecisionTreeEngine] = None
_learning_engine: Optional[EFILearningEngine] = None


def get_decision_tree_engine(db=None) -> Optional[EFIDecisionTreeEngine]:
    global _decision_engine
    if _decision_engine is None and db is not None:
        _decision_engine = EFIDecisionTreeEngine(db)
    return _decision_engine


def get_learning_engine(db=None) -> Optional[EFILearningEngine]:
    global _learning_engine
    if _learning_engine is None and db is not None:
        _learning_engine = EFILearningEngine(db)
    return _learning_engine


def init_efi_engines(db):
    global _decision_engine, _learning_engine
    _decision_engine = EFIDecisionTreeEngine(db)
    _learning_engine = EFILearningEngine(db)
    return _decision_engine, _learning_engine
