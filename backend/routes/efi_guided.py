"""
EFI Guided Execution API Routes
Integrates with Job Card workflow for step-by-step diagnostics
"""
from fastapi import APIRouter, HTTPException, Request, Query, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import logging
import uuid
import base64
import io

from services.efi_embedding_service import get_efi_embedding_manager, init_efi_embedding_manager
from services.efi_decision_engine import (
    get_decision_tree_engine, 
    get_learning_engine,
    init_efi_engines,
    DecisionTree,
    DiagnosticStep,
    ResolutionNode
)
from core.subscriptions.entitlement import require_feature
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/efi-guided",
    tags=["EFI Guided Execution"],
    dependencies=[Depends(require_feature("efi_ai_guidance"))]
)

# Service references
_db = None
_embedding_manager = None
_decision_engine = None
_learning_engine = None

# Image storage collection
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
MAX_IMAGE_SIZE_MB = 5


def init_router(database):
    """Initialize router with database"""
    global _db, _embedding_manager, _decision_engine, _learning_engine
    _db = database
    _embedding_manager = init_efi_embedding_manager(database)
    _decision_engine, _learning_engine = init_efi_engines(database)
    logger.info("EFI Guided Execution router initialized")
    return router


# ==================== REQUEST MODELS ====================

class StartSessionRequest(BaseModel):
    ticket_id: str
    failure_card_id: str


class RecordOutcomeRequest(BaseModel):
    outcome: str  # "pass" or "fail"
    actual_measurement: Optional[str] = None
    notes: Optional[str] = None
    time_taken_seconds: int = 0


class CreateDecisionTreeRequest(BaseModel):
    failure_card_id: str
    steps: List[Dict[str, Any]]
    resolutions: List[Dict[str, Any]]


class CaptureCompletionRequest(BaseModel):
    ticket_id: str
    session_id: Optional[str] = None
    actual_resolution: Optional[str] = None
    actual_parts_used: List[Dict] = []
    actual_time_minutes: int = 0
    deviation_notes: Optional[str] = None
    outcome: str = "success"


# ==================== HELPER ====================

async def get_current_user(request: Request) -> dict:
    org_id = extract_org_id(request)
    """Get current authenticated user"""
    token = request.cookies.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if token and _db is not None:
        session = await _db.user_sessions.find_one({"session_token": token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await _db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user
    
    # Try JWT
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and _db is not None:
        token = auth_header.split(" ")[1]
        import jwt
        import os
        try:
            JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user = await _db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
        except Exception:
            pass
    
    raise HTTPException(status_code=401, detail="Not authenticated")


# ==================== COMPLAINT PRE-PROCESSING ====================

@router.post("/preprocess-complaint")
async def preprocess_complaint(
    request: Request,
    ticket_id: str,
    complaint_text: str
):
    org_id = extract_org_id(request)
    """
    FEATURE 1: Pre-process complaint when logged
    - AI classify subsystem
    - Generate embedding
    - Run similarity search
    - Store results (don't show full guidance yet)
    """
    user = await get_current_user(request)
    
    if not _embedding_manager:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    
    # Generate embedding and classify
    result = await _embedding_manager.generate_complaint_embedding(complaint_text)
    
    # Find similar failure cards
    similar_cards = await _embedding_manager.find_similar_failure_cards(
        embedding=result["embedding"],
        subsystem=result["classified_subsystem"],
        limit=5
    )
    
    # Store pre-processing results on ticket
    preprocessing_data = {
        "complaint_embedding": result["embedding"],
        "classified_subsystem": result["classified_subsystem"],
        "embedding_model": result["embedding_model"],
        "similar_cards": [
            {
                "failure_id": c["failure_id"],
                "title": c["title"],
                "similarity_score": c["similarity_score"],
                "confidence_level": c["confidence_level"]
            }
            for c in similar_cards
        ],
        "preprocessed_at": datetime.now(timezone.utc).isoformat(),
        "preprocessed_by": user.get("user_id")
    }
    
    await _db.tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {"efi_preprocessing": preprocessing_data}}
    )
    
    return {
        "ticket_id": ticket_id,
        "classified_subsystem": result["classified_subsystem"],
        "similar_cards_count": len(similar_cards),
        "top_match": similar_cards[0] if similar_cards else None,
        "status": "preprocessed"
    }


# ==================== GUIDED EXECUTION ====================

@router.get("/suggestions/{ticket_id}")
async def get_efi_suggestions(request: Request, ticket_id: str):
    org_id = extract_org_id(request)
    """
    FEATURE 2: Get EFI suggestions when Job Card opened
    Returns ranked failure cards with confidence scores
    """
    await get_current_user(request)
    
    # Get ticket with preprocessing data
    ticket = await _db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    preprocessing = ticket.get("efi_preprocessing", {})
    
    # If not preprocessed, do it now
    if not preprocessing.get("similar_cards"):
        complaint_text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
        result = await _embedding_manager.generate_complaint_embedding(complaint_text)
        
        similar_cards = await _embedding_manager.find_similar_failure_cards(
            embedding=result["embedding"],
            subsystem=result.get("classified_subsystem"),
            limit=5
        )
    else:
        # Get full card details for stored similar cards
        similar_cards = []
        for card_ref in preprocessing.get("similar_cards", []):
            card = await _db.failure_cards.find_one(
                {"failure_id": card_ref["failure_id"]},
                {"_id": 0}
            )
            if card:
                card["similarity_score"] = card_ref["similarity_score"]
                card["confidence_level"] = card_ref["confidence_level"]
                similar_cards.append(card)
    
    # Check if decision trees exist for these cards
    for card in similar_cards:
        tree = await _db.efi_decision_trees.find_one(
            {"failure_card_id": card["failure_id"]},
            {"_id": 0, "tree_id": 1, "steps": 1}
        )
        card["has_decision_tree"] = tree is not None
        card["decision_tree_steps"] = len(tree.get("steps", [])) if tree else 0
    
    # Check for active session
    active_session = await _db.efi_sessions.find_one(
        {"ticket_id": ticket_id, "status": "active"},
        {"_id": 0}
    )
    
    return {
        "ticket_id": ticket_id,
        "classified_subsystem": preprocessing.get("classified_subsystem", "unknown"),
        "suggested_paths": similar_cards,
        "active_session": active_session,
        "has_active_session": active_session is not None
    }


@router.post("/session/start")
async def start_diagnostic_session(request: Request, data: StartSessionRequest):
    org_id = extract_org_id(request)
    """
    Start EFI diagnostic session for a ticket
    Technician selects a failure card path to follow
    """
    user = await get_current_user(request)
    
    if not _decision_engine:
        raise HTTPException(status_code=503, detail="Decision engine not initialized")
    
    try:
        session = await _decision_engine.start_session(
            ticket_id=data.ticket_id,
            failure_card_id=data.failure_card_id,
            technician_id=user.get("user_id"),
            technician_name=user.get("name")
        )
        
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(request: Request, session_id: str):
    org_id = extract_org_id(request)
    """Get current session state with step details"""
    await get_current_user(request)
    
    if not _decision_engine:
        raise HTTPException(status_code=503, detail="Decision engine not initialized")
    
    session = await _decision_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/session/ticket/{ticket_id}")
async def get_session_by_ticket(request: Request, ticket_id: str):
    org_id = extract_org_id(request)
    """Get active session for a ticket"""
    await get_current_user(request)
    
    if not _decision_engine:
        raise HTTPException(status_code=503, detail="Decision engine not initialized")
    
    session = await _decision_engine.get_session_by_ticket(ticket_id)
    return session or {"active_session": None}


@router.post("/session/{session_id}/step/{step_id}")
async def record_step_outcome(request: Request, session_id: str, 
    step_id: str, 
    data: RecordOutcomeRequest
):
    org_id = extract_org_id(request)
    """
    FEATURE 3: Record PASS/FAIL for diagnostic step
    Advances to next step or resolution based on decision tree
    """
    await get_current_user(request)
    
    if not _decision_engine:
        raise HTTPException(status_code=503, detail="Decision engine not initialized")
    
    try:
        result = await _decision_engine.record_step_outcome(
            session_id=session_id,
            step_id=step_id,
            outcome=data.outcome,
            actual_measurement=data.actual_measurement,
            notes=data.notes,
            time_taken_seconds=data.time_taken_seconds
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== SMART ESTIMATE ====================

@router.get("/session/{session_id}/estimate")
async def get_smart_estimate(request: Request, session_id: str):
    org_id = extract_org_id(request)
    """
    FEATURE 4: Get smart estimate from completed session
    Auto-suggests parts, labor, time based on resolution
    """
    await get_current_user(request)
    
    if not _decision_engine:
        raise HTTPException(status_code=503, detail="Decision engine not initialized")
    
    estimate = await _decision_engine.get_suggested_estimate(session_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="No estimate available. Session may not be completed.")
    
    return estimate


# ==================== CONTINUOUS LEARNING ====================

@router.post("/learning/capture")
async def capture_completion(request: Request, data: CaptureCompletionRequest):
    org_id = extract_org_id(request)
    """
    FEATURE 5: Capture job completion for learning
    Records actual steps, deviations, parts used
    """
    await get_current_user(request)
    
    if not _learning_engine:
        raise HTTPException(status_code=503, detail="Learning engine not initialized")
    
    result = await _learning_engine.capture_job_completion(
        ticket_id=data.ticket_id,
        session_id=data.session_id,
        actual_resolution=data.actual_resolution,
        actual_parts_used=data.actual_parts_used,
        actual_time_minutes=data.actual_time_minutes,
        deviation_notes=data.deviation_notes,
        outcome=data.outcome
    )
    
    return result


@router.get("/learning/pending")
async def get_pending_learning(request: Request, limit: int = Query(50, le=200)):
    org_id = extract_org_id(request)
    """Get learning items pending engineer review"""
    user = await get_current_user(request)
    
    # Require admin/engineer role
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Engineer access required")
    
    if not _learning_engine:
        raise HTTPException(status_code=503, detail="Learning engine not initialized")
    
    items = await _learning_engine.get_pending_learning_items(limit)
    return {"items": items, "count": len(items)}


@router.post("/learning/{entry_id}/review")
async def review_learning_item(request: Request, entry_id: str, action: str, notes: Optional[str] = None):
    org_id = extract_org_id(request)
    """Review learning item - engineer approval"""
    user = await get_current_user(request)
    
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Engineer access required")
    
    if not _learning_engine:
        raise HTTPException(status_code=503, detail="Learning engine not initialized")
    
    try:
        result = await _learning_engine.approve_learning_item(
            entry_id=entry_id,
            action=action,
            reviewer_id=user.get("user_id"),
            reviewer_name=user.get("name", "Unknown"),
            notes=notes
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== DECISION TREE MANAGEMENT ====================

@router.post("/trees")
async def create_decision_tree(request: Request, data: CreateDecisionTreeRequest):
    org_id = extract_org_id(request)
    """Create decision tree for a failure card"""
    user = await get_current_user(request)
    
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not _decision_engine:
        raise HTTPException(status_code=503, detail="Decision engine not initialized")
    
    # Convert step dicts to DiagnosticStep objects
    steps = [DiagnosticStep(**s) for s in data.steps]
    resolutions = [ResolutionNode(**r) for r in data.resolutions]
    
    tree = DecisionTree(
        failure_card_id=data.failure_card_id,
        steps=steps,
        resolutions=resolutions
    )
    
    result = await _decision_engine.create_tree(tree)
    return result


@router.get("/trees/{failure_card_id}")
async def get_decision_tree(request: Request, failure_card_id: str):
    org_id = extract_org_id(request)
    """Get decision tree for a failure card"""
    await get_current_user(request)
    
    if not _decision_engine:
        raise HTTPException(status_code=503, detail="Decision engine not initialized")
    
    tree = await _decision_engine.get_tree_for_card(failure_card_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Decision tree not found")
    
    return tree


# ==================== EMBEDDING MANAGEMENT ====================

@router.post("/embeddings/generate-all")
async def generate_all_embeddings(request: Request):
    org_id = extract_org_id(request)
    """Generate embeddings for all failure cards"""
    user = await get_current_user(request)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not _embedding_manager:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    
    result = await _embedding_manager.embed_all_cards()
    return result


@router.get("/embeddings/status")
async def get_embedding_status(request: Request):
    org_id = extract_org_id(request)
    """Get embedding status for failure cards"""
    await get_current_user(request)
    
    total = await _db.failure_cards.count_documents(org_query(org_id))
    with_embeddings = await _db.failure_cards.count_documents({
        "embedding_vector": {"$exists": True, "$ne": None}
    })
    
    return {
        "total_cards": total,
        "cards_with_embeddings": with_embeddings,
        "cards_without_embeddings": total - with_embeddings,
        "coverage_percent": round((with_embeddings / total * 100), 2) if total > 0 else 0
    }


# ==================== SEED DATA ====================

@router.post("/seed")
async def seed_failure_data(request: Request):
    org_id = extract_org_id(request)
    """Seed failure cards and decision trees (Admin only)"""
    user = await get_current_user(request)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from services.efi_seed_data import seed_failure_cards_and_trees
    
    result = await seed_failure_cards_and_trees(_db)
    
    # Skip embedding generation during seeding to avoid timeouts
    # Embeddings will be generated on-demand or via separate endpoint
    result["embeddings_note"] = "Use /api/efi-guided/embeddings/generate-all to generate embeddings"
    
    return {
        "status": "success",
        "message": f"Seeded {result['cards_inserted']} failure cards and {result['trees_inserted']} decision trees",
        **result
    }


@router.get("/failure-cards")
async def list_failure_cards(request: Request, subsystem: Optional[str] = None, limit: int = Query(50, le=200),
    skip: int = 0
):
    """List all failure cards with optional filtering"""
    await get_current_user(request)
    
    query = {}
    if subsystem:
        query["subsystem_category"] = subsystem
    
    cards = await _db.failure_cards.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await _db.failure_cards.count_documents(query)
    
    return {
        "cards": cards,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/failure-cards/{failure_id}")
async def get_failure_card(request: Request, failure_id: str):
    org_id = extract_org_id(request)
    """Get a single failure card by ID"""
    await get_current_user(request)
    
    card = await _db.failure_cards.find_one({"failure_id": failure_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    # Also get decision tree if exists
    tree = await _db.efi_decision_trees.find_one(
        {"failure_card_id": failure_id},
        {"_id": 0}
    )
    
    return {
        **card,
        "decision_tree": tree
    }



# ==================== STEP IMAGE ENDPOINTS ====================

@router.post("/failure-cards/{failure_id}/step-image")
async def upload_step_image(request: Request, failure_id: str, step_order: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload an image for a specific decision tree step"""
    await get_current_user(request)
    
    # Validate failure card exists
    card = await _db.failure_cards.find_one({"failure_id": failure_id})
    if not card:
        raise HTTPException(status_code=404, detail="Failure card not found")
    
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid image type. Allowed: {ALLOWED_IMAGE_TYPES}")
    
    # Read and validate size
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image exceeds {MAX_IMAGE_SIZE_MB}MB limit")
    
    # Generate image ID
    image_id = f"EFI_IMG_{uuid.uuid4().hex[:12]}"
    
    # Store image
    image_doc = {
        "image_id": image_id,
        "failure_id": failure_id,
        "step_order": step_order,
        "filename": file.filename,
        "content_type": file.content_type,
        "file_size": len(content),
        "image_data": base64.b64encode(content).decode('utf-8'),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await _db.efi_step_images.insert_one(image_doc)
    
    # Update decision tree step with image reference
    await _db.efi_decision_trees.update_one(
        {"failure_card_id": failure_id, "steps.order": step_order},
        {"$set": {"steps.$.reference_image": f"/api/efi-guided/step-image/{image_id}"}}
    )
    
    # Also update failure card if decision tree is embedded
    await _db.failure_cards.update_one(
        {"failure_id": failure_id, "decision_tree.steps.order": step_order},
        {"$set": {"decision_tree.steps.$.reference_image": f"/api/efi-guided/step-image/{image_id}"}}
    )
    
    return {
        "code": 0,
        "message": "Image uploaded successfully",
        "image_id": image_id,
        "image_url": f"/api/efi-guided/step-image/{image_id}"
    }


@router.get("/step-image/{image_id}")
async def get_step_image(request: Request, image_id: str):
    org_id = extract_org_id(request)
    """Get a step image by ID (public endpoint for display)"""
    image = await _db.efi_step_images.find_one({"image_id": image_id})
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_data = base64.b64decode(image["image_data"])
    
    return StreamingResponse(
        io.BytesIO(image_data),
        media_type=image["content_type"],
        headers={"Content-Disposition": f"inline; filename={image['filename']}"}
    )


@router.get("/failure-cards/{failure_id}/images")
async def list_step_images(request: Request, failure_id: str):
    org_id = extract_org_id(request)
    """List all images for a failure card's decision tree"""
    await get_current_user(request)
    
    images = await _db.efi_step_images.find(
        {"failure_id": failure_id},
        {"_id": 0, "image_data": 0}
    ).to_list(50)
    
    return {"code": 0, "images": images}


@router.delete("/step-image/{image_id}")
async def delete_step_image(request: Request, image_id: str):
    org_id = extract_org_id(request)
    """Delete a step image"""
    await get_current_user(request)
    
    image = await _db.efi_step_images.find_one({"image_id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Remove image reference from decision tree
    await _db.efi_decision_trees.update_many(
        {"steps.reference_image": f"/api/efi-guided/step-image/{image_id}"},
        {"$unset": {"steps.$.reference_image": ""}}
    )
    
    await _db.failure_cards.update_many(
        {"decision_tree.steps.reference_image": f"/api/efi-guided/step-image/{image_id}"},
        {"$unset": {"decision_tree.steps.$.reference_image": ""}}
    )
    
    # Delete image
    await _db.efi_step_images.delete_one({"image_id": image_id})
    
    return {"code": 0, "message": "Image deleted"}
