"""
Tenant Repository Module
=======================

Base repository class that enforces tenant isolation at the data access layer.

All database operations MUST go through a TenantRepository to ensure:
1. Queries always include organization_id
2. Inserts always add organization_id
3. Updates cannot change organization_id
4. Deletes are scoped to organization

This is the FINAL BARRIER before MongoDB - nothing gets through without org_id.
"""

from typing import Optional, Dict, Any, List, TypeVar, Generic, Type
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pydantic import BaseModel
import logging

from .context import TenantContext, get_tenant_context
from .guard import TenantGuard, get_tenant_guard, TENANT_COLLECTIONS, GLOBAL_COLLECTIONS
from .exceptions import TenantBoundaryViolation, TenantContextMissing

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class TenantQueryBuilder:
    """
    Fluent query builder that enforces tenant scoping.
    
    Usage:
        builder = TenantQueryBuilder(ctx, "tickets")
        query = builder.where({"status": "open"}).sort("created_at", -1).build()
        results = await db.tickets.find(query["filter"]).sort(query["sort"]).to_list()
    """
    
    def __init__(self, ctx: TenantContext, collection: str):
        self.ctx = ctx
        self.collection = collection
        self._filter: Dict[str, Any] = {}
        self._sort: List[tuple] = []
        self._projection: Optional[Dict[str, Any]] = None
        self._skip: int = 0
        self._limit: int = 0
    
    def where(self, conditions: Dict[str, Any]) -> 'TenantQueryBuilder':
        """Add filter conditions"""
        self._filter.update(conditions)
        return self
    
    def eq(self, field: str, value: Any) -> 'TenantQueryBuilder':
        """Add equality condition"""
        self._filter[field] = value
        return self
    
    def ne(self, field: str, value: Any) -> 'TenantQueryBuilder':
        """Add not-equal condition"""
        self._filter[field] = {"$ne": value}
        return self
    
    def in_list(self, field: str, values: List) -> 'TenantQueryBuilder':
        """Add $in condition"""
        self._filter[field] = {"$in": values}
        return self
    
    def exists(self, field: str, value: bool = True) -> 'TenantQueryBuilder':
        """Add $exists condition"""
        self._filter[field] = {"$exists": value}
        return self
    
    def gte(self, field: str, value: Any) -> 'TenantQueryBuilder':
        """Add >= condition"""
        self._filter.setdefault(field, {})
        self._filter[field]["$gte"] = value
        return self
    
    def lte(self, field: str, value: Any) -> 'TenantQueryBuilder':
        """Add <= condition"""
        self._filter.setdefault(field, {})
        self._filter[field]["$lte"] = value
        return self
    
    def regex(self, field: str, pattern: str, options: str = "i") -> 'TenantQueryBuilder':
        """Add regex search"""
        self._filter[field] = {"$regex": pattern, "$options": options}
        return self
    
    def sort(self, field: str, direction: int = -1) -> 'TenantQueryBuilder':
        """Add sort"""
        self._sort.append((field, direction))
        return self
    
    def project(self, fields: Dict[str, int]) -> 'TenantQueryBuilder':
        """Set projection"""
        self._projection = {"_id": 0, **fields}
        return self
    
    def skip(self, count: int) -> 'TenantQueryBuilder':
        """Set skip"""
        self._skip = count
        return self
    
    def limit(self, count: int) -> 'TenantQueryBuilder':
        """Set limit"""
        self._limit = count
        return self
    
    def paginate(self, page: int, per_page: int) -> 'TenantQueryBuilder':
        """Add pagination"""
        self._skip = (page - 1) * per_page
        self._limit = per_page
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final query with org_id enforced"""
        # Enforce org_id
        if self.collection in TENANT_COLLECTIONS:
            self._filter["organization_id"] = self.ctx.org_id
        
        result = {
            "filter": self._filter,
            "projection": self._projection or {"_id": 0}
        }
        
        if self._sort:
            result["sort"] = self._sort
        if self._skip:
            result["skip"] = self._skip
        if self._limit:
            result["limit"] = self._limit
        
        return result


class TenantRepository(Generic[T]):
    """
    Base repository with automatic tenant isolation.
    
    Extend this class for each entity type:
    
        class TicketRepository(TenantRepository[Ticket]):
            def __init__(self, db):
                super().__init__(db, "tickets", Ticket)
            
            async def find_open_tickets(self, ctx: TenantContext):
                return await self.find_many(ctx, {"status": "open"})
    
    All methods enforce tenant isolation automatically.
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        collection_name: str,
        model_class: Optional[Type[T]] = None
    ):
        self.db = db
        self.collection_name = collection_name
        self.collection: AsyncIOMotorCollection = db[collection_name]
        self.model_class = model_class
        self._guard = get_tenant_guard()
        
        # Determine if this is a tenant collection
        self.is_tenant_collection = collection_name in TENANT_COLLECTIONS
    
    def _get_guard(self) -> TenantGuard:
        """Get or create guard"""
        if self._guard is None:
            self._guard = get_tenant_guard()
        return self._guard
    
    def _validate_context(self, ctx: Optional[TenantContext]) -> TenantContext:
        """Ensure we have a valid context"""
        if ctx is None:
            ctx = get_tenant_context()
        
        if ctx is None and self.is_tenant_collection:
            raise TenantContextMissing(
                endpoint=f"repository:{self.collection_name}",
                metadata={"operation": "data_access"}
            )
        
        return ctx
    
    async def find_one(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any],
        projection: Optional[Dict] = None
    ) -> Optional[T]:
        """Find one document"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            filter_query = self._get_guard().validate_query(
                self.collection_name, filter_query.copy(), ctx
            )
        
        doc = await self.collection.find_one(
            filter_query,
            projection or {"_id": 0}
        )
        
        if doc and self.model_class:
            return self.model_class(**doc)
        return doc
    
    async def find_many(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any] = None,
        projection: Optional[Dict] = None,
        sort: Optional[List[tuple]] = None,
        skip: int = 0,
        limit: int = 1000
    ) -> List[T]:
        """Find multiple documents"""
        ctx = self._validate_context(ctx)
        filter_query = filter_query or {}
        
        if self.is_tenant_collection:
            filter_query = self._get_guard().validate_query(
                self.collection_name, filter_query.copy(), ctx
            )
        
        cursor = self.collection.find(filter_query, projection or {"_id": 0})
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        docs = await cursor.to_list(length=limit)
        
        if self.model_class:
            return [self.model_class(**doc) for doc in docs]
        return docs
    
    async def find_paginated(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 25,
        sort: Optional[List[tuple]] = None
    ) -> Dict[str, Any]:
        """Find with pagination"""
        ctx = self._validate_context(ctx)
        filter_query = filter_query or {}
        
        if self.is_tenant_collection:
            filter_query = self._get_guard().validate_query(
                self.collection_name, filter_query.copy(), ctx
            )
        
        total = await self.collection.count_documents(filter_query)
        skip = (page - 1) * per_page
        
        docs = await self.find_many(
            ctx, filter_query,
            sort=sort or [("created_at", -1)],
            skip=skip,
            limit=per_page
        )
        
        return {
            "items": docs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    async def count(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any] = None
    ) -> int:
        """Count documents"""
        ctx = self._validate_context(ctx)
        filter_query = filter_query or {}
        
        if self.is_tenant_collection:
            filter_query = self._get_guard().validate_query(
                self.collection_name, filter_query.copy(), ctx
            )
        
        return await self.collection.count_documents(filter_query)
    
    async def insert_one(
        self,
        ctx: TenantContext,
        document: Dict[str, Any]
    ) -> str:
        """Insert one document"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            document = self._get_guard().validate_document(
                self.collection_name, document.copy(), ctx
            )
        
        # Add timestamps
        now = datetime.now(timezone.utc).isoformat()
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        
        result = await self.collection.insert_one(document)
        
        # Return the ID field if present
        id_field = f"{self.collection_name.rstrip('s')}_id"
        return document.get(id_field) or str(result.inserted_id)
    
    async def insert_many(
        self,
        ctx: TenantContext,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert multiple documents"""
        ctx = self._validate_context(ctx)
        
        now = datetime.now(timezone.utc).isoformat()
        validated_docs = []
        
        for doc in documents:
            if self.is_tenant_collection:
                doc = self._get_guard().validate_document(
                    self.collection_name, doc.copy(), ctx
                )
            doc.setdefault("created_at", now)
            doc.setdefault("updated_at", now)
            validated_docs.append(doc)
        
        result = await self.collection.insert_many(validated_docs)
        return [str(id) for id in result.inserted_ids]
    
    async def update_one(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """Update one document"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            filter_query, update = self._get_guard().validate_update(
                self.collection_name, filter_query.copy(), update.copy(), ctx
            )
        
        # Add updated_at
        if "$set" not in update:
            update["$set"] = {}
        update["$set"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.collection.update_one(filter_query, update, upsert=upsert)
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def update_many(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """Update multiple documents"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            filter_query, update = self._get_guard().validate_update(
                self.collection_name, filter_query.copy(), update.copy(), ctx
            )
        
        if "$set" not in update:
            update["$set"] = {}
        update["$set"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.collection.update_many(filter_query, update)
        return result.modified_count
    
    async def delete_one(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any]
    ) -> bool:
        """Delete one document"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            filter_query = self._get_guard().validate_delete(
                self.collection_name, filter_query.copy(), ctx
            )
        
        result = await self.collection.delete_one(filter_query)
        return result.deleted_count > 0
    
    async def delete_many(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any]
    ) -> int:
        """Delete multiple documents"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            filter_query = self._get_guard().validate_delete(
                self.collection_name, filter_query.copy(), ctx
            )
        
        result = await self.collection.delete_many(filter_query)
        return result.deleted_count
    
    async def aggregate(
        self,
        ctx: TenantContext,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict]:
        """Run aggregation pipeline"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            pipeline = self._get_guard().validate_aggregation(
                self.collection_name, pipeline.copy(), ctx
            )
        
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    async def find_one_and_update(
        self,
        ctx: TenantContext,
        filter_query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = True
    ) -> Optional[T]:
        """Find and update atomically"""
        ctx = self._validate_context(ctx)
        
        if self.is_tenant_collection:
            filter_query, update = self._get_guard().validate_update(
                self.collection_name, filter_query.copy(), update.copy(), ctx
            )
        
        if "$set" not in update:
            update["$set"] = {}
        update["$set"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        from pymongo import ReturnDocument
        doc = await self.collection.find_one_and_update(
            filter_query,
            update,
            return_document=ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE,
            projection={"_id": 0}
        )
        
        if doc and self.model_class:
            return self.model_class(**doc)
        return doc
    
    def query(self, ctx: TenantContext) -> TenantQueryBuilder:
        """Start a fluent query"""
        return TenantQueryBuilder(ctx, self.collection_name)


def create_tenant_repository(
    db: AsyncIOMotorDatabase,
    collection_name: str,
    model_class: Optional[Type[BaseModel]] = None
) -> TenantRepository:
    """Factory function to create a tenant repository"""
    return TenantRepository(db, collection_name, model_class)
