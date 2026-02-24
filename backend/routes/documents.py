"""
Battwheels OS - Documents Management API Routes
Document library for receipts, attachments, service photos
"""

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import base64
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/documents", tags=["Documents"])

# Database connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Document storage path
UPLOAD_DIR = "/app/uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def get_org_id(request: Request) -> Optional[str]:
    """Get organization ID from request header"""
    return request.headers.get("X-Organization-ID")


# ==================== MODELS ====================

class DocumentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    document_type: str = "general"  # receipt, invoice, photo, contract, report, other
    folder_id: Optional[str] = None
    tags: List[str] = []
    related_entity_type: Optional[str] = None  # ticket, invoice, contact, item, etc
    related_entity_id: Optional[str] = None
    file_content: Optional[str] = None  # Base64 encoded
    file_name: Optional[str] = None
    mime_type: Optional[str] = None

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = None

class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_folder_id: Optional[str] = None
    color: str = "#3B82F6"


# ==================== FOLDERS ====================

@router.get("/folders")
async def list_folders(request: Request, parent_id: str = ""):
    """List document folders"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    query = {"organization_id": org_id}
    if parent_id:
        query["parent_folder_id"] = parent_id
    else:
        query["parent_folder_id"] = {"$in": [None, ""]}
    
    folders = await db.document_folders.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    
    # Get document counts for each folder
    for folder in folders:
        folder["document_count"] = await db.documents.count_documents({
            "organization_id": org_id,
            "folder_id": folder["folder_id"]
        })
    
    return {"code": 0, "folders": folders}


@router.post("/folders")
async def create_folder(request: Request, folder: FolderCreate):
    """Create a new folder"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    # Check for duplicate name
    existing = await db.document_folders.find_one({
        "organization_id": org_id,
        "name": folder.name,
        "parent_folder_id": folder.parent_folder_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Folder with this name already exists")
    
    folder_id = f"FLD-{uuid.uuid4().hex[:12].upper()}"
    
    folder_doc = {
        "folder_id": folder_id,
        "organization_id": org_id,
        "name": folder.name,
        "parent_folder_id": folder.parent_folder_id,
        "color": folder.color,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.document_folders.insert_one(folder_doc)
    folder_doc.pop("_id", None)
    
    return {"code": 0, "folder": folder_doc, "message": "Folder created"}


@router.delete("/folders/{folder_id}")
async def delete_folder(request: Request, folder_id: str, force: bool = False):
    """Delete a folder"""
    org_id = await get_org_id(request)
    
    folder = await db.document_folders.find_one({
        "folder_id": folder_id,
        "organization_id": org_id
    })
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check for documents in folder
    doc_count = await db.documents.count_documents({
        "organization_id": org_id,
        "folder_id": folder_id
    })
    
    if doc_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Folder contains {doc_count} documents. Use force=true to delete anyway."
        )
    
    # Delete folder and move documents to root
    if force and doc_count > 0:
        await db.documents.update_many(
            {"folder_id": folder_id},
            {"$set": {"folder_id": None}}
        )
    
    await db.document_folders.delete_one({"folder_id": folder_id})
    
    return {"code": 0, "message": "Folder deleted"}


# ==================== DOCUMENTS ====================

@router.get("/")
async def list_documents(request: Request, folder_id: str = "", document_type: str = "", related_entity_type: str = "", related_entity_id: str = "", tag: str = "", search: str = "", page: int = 1, per_page: int = 50):
    """List documents with filters"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    query = {"organization_id": org_id}
    
    if folder_id:
        query["folder_id"] = folder_id
    if document_type:
        query["document_type"] = document_type
    if related_entity_type:
        query["related_entity_type"] = related_entity_type
    if related_entity_id:
        query["related_entity_id"] = related_entity_id
    if tag:
        query["tags"] = tag
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    skip = (page - 1) * per_page
    documents = await db.documents.find(query, {"_id": 0, "file_content": 0}).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    total = await db.documents.count_documents(query)
    
    return {
        "code": 0,
        "documents": documents,
        "page_context": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }


@router.post("/")
async def create_document(request: Request, doc: DocumentCreate):
    """Create a new document"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    document_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
    
    # Handle file content
    file_path = None
    file_size = 0
    
    if doc.file_content:
        try:
            # Decode base64 content
            file_data = base64.b64decode(doc.file_content)
            file_size = len(file_data)
            
            # Generate file path
            ext = doc.file_name.split(".")[-1] if doc.file_name and "." in doc.file_name else "bin"
            file_path = f"{UPLOAD_DIR}/{document_id}.{ext}"
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(file_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to save file: {str(e)}")
    
    doc_doc = {
        "document_id": document_id,
        "organization_id": org_id,
        "name": doc.name,
        "description": doc.description,
        "document_type": doc.document_type,
        "folder_id": doc.folder_id,
        "tags": doc.tags,
        "related_entity_type": doc.related_entity_type,
        "related_entity_id": doc.related_entity_id,
        "file_name": doc.file_name,
        "file_path": file_path,
        "file_size": file_size,
        "mime_type": doc.mime_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": request.headers.get("X-User-ID"),
        "status": "active"
    }
    
    await db.documents.insert_one(doc_doc)
    doc_doc.pop("_id", None)
    
    return {"code": 0, "document": doc_doc, "message": "Document created"}


@router.get("/{document_id}")
async def get_document(request: Request, document_id: str, include_content: bool = False):
    """Get document details"""
    org_id = await get_org_id(request)
    
    projection = {"_id": 0}
    if not include_content:
        projection["file_content"] = 0
    
    doc = await db.documents.find_one(
        {"document_id": document_id, "organization_id": org_id},
        projection
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Load file content if requested
    if include_content and doc.get("file_path"):
        try:
            with open(doc["file_path"], "rb") as f:
                doc["file_content"] = base64.b64encode(f.read()).decode()
        except:
            doc["file_content"] = None
    
    return {"code": 0, "document": doc}


@router.put("/{document_id}")
async def update_document(request: Request, document_id: str, update: DocumentUpdate):
    """Update document metadata"""
    org_id = await get_org_id(request)
    
    existing = await db.documents.find_one({
        "document_id": document_id,
        "organization_id": org_id
    })
    
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.documents.update_one(
        {"document_id": document_id},
        {"$set": update_data}
    )
    
    updated = await db.documents.find_one({"document_id": document_id}, {"_id": 0, "file_content": 0})
    return {"code": 0, "document": updated, "message": "Document updated"}


@router.delete("/{document_id}")
async def delete_document(request: Request, document_id: str):
    """Delete a document"""
    org_id = await get_org_id(request)
    
    doc = await db.documents.find_one({
        "document_id": document_id,
        "organization_id": org_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    if doc.get("file_path"):
        try:
            os.remove(doc["file_path"])
        except:
            pass
    
    await db.documents.delete_one({"document_id": document_id})
    
    return {"code": 0, "message": "Document deleted"}


# ==================== TAGS ====================

@router.get("/tags/all")
async def list_all_tags(request: Request):
    """Get all document tags"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    # Aggregate unique tags
    pipeline = [
        {"$match": {"organization_id": org_id}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 100}
    ]
    
    tags = []
    async for doc in db.documents.aggregate(pipeline):
        tags.append({"tag": doc["_id"], "count": doc["count"]})
    
    return {"code": 0, "tags": tags}


# ==================== BULK OPERATIONS ====================

@router.post("/bulk/move")
async def bulk_move_documents(request: Request, document_ids: List[str], folder_id: str):
    """Move multiple documents to a folder"""
    org_id = await get_org_id(request)
    
    result = await db.documents.update_many(
        {"document_id": {"$in": document_ids}, "organization_id": org_id},
        {"$set": {"folder_id": folder_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"code": 0, "message": f"Moved {result.modified_count} documents"}


@router.post("/bulk/tag")
async def bulk_tag_documents(request: Request, document_ids: List[str], tags: List[str]):
    """Add tags to multiple documents"""
    org_id = await get_org_id(request)
    
    result = await db.documents.update_many(
        {"document_id": {"$in": document_ids}, "organization_id": org_id},
        {
            "$addToSet": {"tags": {"$each": tags}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"code": 0, "message": f"Tagged {result.modified_count} documents"}


@router.delete("/bulk/delete")
async def bulk_delete_documents(request: Request, document_ids: List[str]):
    """Delete multiple documents"""
    org_id = await get_org_id(request)
    
    # Get file paths first
    docs = await db.documents.find(
        {"document_id": {"$in": document_ids}, "organization_id": org_id},
        {"file_path": 1}
    ).to_list(len(document_ids))
    
    # Delete files
    for doc in docs:
        if doc.get("file_path"):
            try:
                os.remove(doc["file_path"])
            except:
                pass
    
    result = await db.documents.delete_many({
        "document_id": {"$in": document_ids},
        "organization_id": org_id
    })
    
    return {"code": 0, "message": f"Deleted {result.deleted_count} documents"}


# ==================== STATS ====================

@router.get("/stats/summary")
async def get_document_stats(request: Request):
    """Get document statistics"""
    org_id = await get_org_id(request)
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-ID required")
    
    total_docs = await db.documents.count_documents({"organization_id": org_id})
    total_folders = await db.document_folders.count_documents({"organization_id": org_id})
    
    # Count by type
    type_counts = {}
    pipeline = [
        {"$match": {"organization_id": org_id}},
        {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
    ]
    async for doc in db.documents.aggregate(pipeline):
        type_counts[doc["_id"] or "other"] = doc["count"]
    
    # Calculate total size
    total_size = 0
    async for doc in db.documents.find({"organization_id": org_id}, {"file_size": 1}):
        total_size += doc.get("file_size", 0)
    
    # Recent documents
    recent = await db.documents.find(
        {"organization_id": org_id},
        {"_id": 0, "document_id": 1, "name": 1, "document_type": 1, "created_at": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "code": 0,
        "stats": {
            "total_documents": total_docs,
            "total_folders": total_folders,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_type": type_counts,
            "recent_documents": recent
        }
    }
