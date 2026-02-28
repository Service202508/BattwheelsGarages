"""
Battwheels OS - Pagination Utilities
=====================================

Standard pagination pattern for all list endpoints.
Supports both skip/limit (backward compat) and cursor-based (keyset) pagination.

Usage (cursor-based — preferred for high-traffic endpoints):
    from utils.pagination import paginate_keyset, get_pagination_params_v2

    @router.get("/items")
    async def list_items(
        cursor: Optional[str] = Query(None),
        limit: int = Query(25, ge=1, le=100),
    ):
        query = {"organization_id": org_id}
        return await paginate_keyset(
            db.items, query,
            sort_field="created_at", sort_order=-1,
            tiebreaker_field="item_id",
            limit=limit, cursor=cursor,
        )

Usage (legacy skip/limit):
    from utils.pagination import paginate, PaginationParams, PaginatedResponse

    @router.get("/items")
    async def list_items(pagination: PaginationParams = Depends()):
        query = {"organization_id": org_id}
        return await paginate(db.items, query, pagination)
"""

from typing import Optional, List, Any, Dict, Tuple
from fastapi import Query
from pydantic import BaseModel, Field
from dataclasses import dataclass
import math
import base64
import json


# Maximum allowed limit to prevent unbounded queries
MAX_LIMIT = 100
DEFAULT_LIMIT = 25
DEFAULT_PAGE = 1


class PaginationMeta(BaseModel):
    """Pagination metadata in response"""
    page: int = Field(description="Current page number (1-indexed)")
    limit: int = Field(description="Items per page")
    total_count: int = Field(description="Total number of items matching query")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages after this")
    has_prev: bool = Field(description="Whether there are pages before this")


class PaginatedResponse(BaseModel):
    """Standard paginated response format"""
    data: List[Any] = Field(description="Array of items for this page")
    pagination: PaginationMeta = Field(description="Pagination metadata")


@dataclass
class PaginationParams:
    """
    Dependency for extracting pagination parameters from query string.
    
    Usage:
        @router.get("/items")
        async def list_items(pagination: PaginationParams = Depends(get_pagination_params)):
            ...
    """
    page: int = DEFAULT_PAGE
    limit: int = DEFAULT_LIMIT
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    
    @property
    def skip(self) -> int:
        """Calculate number of documents to skip"""
        return (self.page - 1) * self.limit
    
    @property
    def sort_direction(self) -> int:
        """MongoDB sort direction: 1 for ASC, -1 for DESC"""
        return 1 if self.sort_order.lower() == "asc" else -1


def get_pagination_params(
    page: int = Query(default=DEFAULT_PAGE, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Items per page (max 100)"),
    sort_by: Optional[str] = Query(default=None, description="Field to sort by"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order: asc or desc")
) -> PaginationParams:
    """
    FastAPI dependency for extracting pagination parameters.
    Enforces limits and defaults.
    """
    # Cap limit at MAX_LIMIT
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    if limit < 1:
        limit = DEFAULT_LIMIT
    
    # Ensure page is at least 1
    if page < 1:
        page = DEFAULT_PAGE
    
    return PaginationParams(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )


async def paginate(
    collection,
    query: Dict[str, Any],
    pagination: PaginationParams,
    projection: Dict[str, Any] = None,
    default_sort_field: str = "created_at"
) -> Dict[str, Any]:
    """
    Execute paginated MongoDB query.
    
    Args:
        collection: MongoDB collection
        query: Filter query
        pagination: Pagination parameters
        projection: Fields to include/exclude (always excludes _id)
        default_sort_field: Field to sort by if none specified
    
    Returns:
        Dict with 'data' and 'pagination' keys
    """
    # Default projection excludes _id
    if projection is None:
        projection = {"_id": 0}
    elif "_id" not in projection:
        projection["_id"] = 0
    
    # Get total count
    total_count = await collection.count_documents(query)
    
    # Calculate total pages
    total_pages = math.ceil(total_count / pagination.limit) if total_count > 0 else 1
    
    # Adjust page if out of bounds
    page = min(pagination.page, total_pages)
    skip = (page - 1) * pagination.limit
    
    # Determine sort field
    sort_field = pagination.sort_by or default_sort_field
    sort_direction = pagination.sort_direction
    
    # Execute query
    cursor = collection.find(query, projection)
    cursor = cursor.sort(sort_field, sort_direction)
    cursor = cursor.skip(skip)
    cursor = cursor.limit(pagination.limit)
    
    data = await cursor.to_list(length=pagination.limit)
    
    return {
        "data": data,
        "pagination": {
            "page": page,
            "limit": pagination.limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


async def paginate_aggregation(
    collection,
    pipeline: List[Dict[str, Any]],
    pagination: PaginationParams,
    count_pipeline: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute paginated MongoDB aggregation pipeline.
    
    Args:
        collection: MongoDB collection
        pipeline: Aggregation pipeline (without $skip/$limit)
        pagination: Pagination parameters
        count_pipeline: Optional separate pipeline for counting
                       (useful for complex aggregations)
    
    Returns:
        Dict with 'data' and 'pagination' keys
    """
    # Get total count
    if count_pipeline:
        count_result = await collection.aggregate(count_pipeline).to_list(1)
    else:
        # Add $count stage to existing pipeline
        count_pipe = pipeline.copy()
        count_pipe.append({"$count": "total"})
        count_result = await collection.aggregate(count_pipe).to_list(1)
    
    total_count = count_result[0]["total"] if count_result else 0
    total_pages = math.ceil(total_count / pagination.limit) if total_count > 0 else 1
    
    # Adjust page if out of bounds
    page = min(pagination.page, total_pages)
    skip = (page - 1) * pagination.limit
    
    # Add sort, skip, limit to pipeline
    paginated_pipeline = pipeline.copy()
    
    if pagination.sort_by:
        paginated_pipeline.append({
            "$sort": {pagination.sort_by: pagination.sort_direction}
        })
    
    paginated_pipeline.append({"$skip": skip})
    paginated_pipeline.append({"$limit": pagination.limit})
    
    # Execute
    data = await collection.aggregate(paginated_pipeline).to_list(pagination.limit)
    
    return {
        "data": data,
        "pagination": {
            "page": page,
            "limit": pagination.limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


def enforce_pagination_on_cursor(cursor, max_limit: int = MAX_LIMIT):
    """
    Utility to ensure any cursor has a limit.
    Use as a safety net for routes that might bypass pagination.
    """
    # This is mainly for audit purposes - in production,
    # use the paginate() function directly
    return cursor.limit(max_limit)


# ==================== CURSOR-BASED (KEYSET) PAGINATION ====================


def encode_cursor(sort_value: Any, tiebreaker_value: Any) -> str:
    """Encode a cursor from a sort field value and a tiebreaker (unique) field value."""
    payload = json.dumps({"v": sort_value, "t": tiebreaker_value})
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor_str: str) -> Tuple[Any, Any]:
    """Decode a cursor string back to (sort_value, tiebreaker_value)."""
    padding = 4 - len(cursor_str) % 4
    if padding != 4:
        cursor_str += "=" * padding
    payload = json.loads(base64.urlsafe_b64decode(cursor_str.encode()).decode())
    return payload["v"], payload["t"]


async def paginate_keyset(
    collection,
    query: Dict[str, Any],
    sort_field: str,
    sort_order: int,
    tiebreaker_field: str,
    limit: int = DEFAULT_LIMIT,
    cursor: Optional[str] = None,
    projection: Optional[Dict[str, Any]] = None,
    include_total: bool = True,
) -> Dict[str, Any]:
    """
    Cursor-based (keyset) pagination for MongoDB.

    Uses sort_field + tiebreaker_field for deterministic ordering.
    When cursor is provided, seeks directly to the correct position
    without scanning skipped documents.

    When cursor is None, returns the first page (backward compatible
    with skip/limit clients that don't pass a cursor).

    Args:
        collection: Motor collection
        query: Base filter query (org-scoped, status filters, etc.)
        sort_field: Primary sort field (e.g. "created_at", "invoice_date")
        sort_order: 1 for ascending, -1 for descending
        tiebreaker_field: Unique field for tie-breaking (e.g. "ticket_id")
        limit: Page size (capped at MAX_LIMIT)
        cursor: Opaque cursor from previous response's next_cursor
        projection: MongoDB projection (always excludes _id)
        include_total: Whether to compute total_count (expensive at scale)

    Returns:
        {
            "data": [...],
            "pagination": {
                "limit": N,
                "total_count": N,
                "has_next": bool,
                "next_cursor": "..." | null,
                "has_prev": bool
            }
        }
    """
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT

    if projection is None:
        projection = {"_id": 0}
    elif "_id" not in projection:
        projection["_id"] = 0

    # Ensure tiebreaker field is in projection (needed for cursor construction)
    if tiebreaker_field not in projection and not any(v == 1 for v in projection.values() if isinstance(v, int) and v == 1):
        pass  # projection is exclusion-based, tiebreaker included by default
    elif any(v == 1 for v in projection.values() if isinstance(v, int)):
        # inclusion-based projection: ensure tiebreaker and sort field are included
        projection[tiebreaker_field] = 1
        projection[sort_field] = 1

    # Total count from base query (before cursor filter)
    total_count = 0
    if include_total:
        total_count = await collection.count_documents(query)

    has_prev = False

    # Apply cursor filter
    if cursor:
        has_prev = True
        sort_value, tie_value = decode_cursor(cursor)

        if sort_order == -1:
            cursor_filter = {"$or": [
                {sort_field: {"$lt": sort_value}},
                {sort_field: sort_value, tiebreaker_field: {"$lt": tie_value}},
            ]}
        else:
            cursor_filter = {"$or": [
                {sort_field: {"$gt": sort_value}},
                {sort_field: sort_value, tiebreaker_field: {"$gt": tie_value}},
            ]}

        query = {"$and": [query, cursor_filter]}

    # Fetch limit + 1 to detect has_next
    items = await collection.find(query, projection).sort([
        (sort_field, sort_order),
        (tiebreaker_field, sort_order),
    ]).limit(limit + 1).to_list(limit + 1)

    has_next = len(items) > limit
    if has_next:
        items = items[:limit]

    # Build next_cursor from last item
    next_cursor = None
    if has_next and items:
        last = items[-1]
        next_cursor = encode_cursor(last.get(sort_field), last.get(tiebreaker_field))

    return {
        "data": items,
        "pagination": {
            "limit": limit,
            "total_count": total_count,
            "has_next": has_next,
            "has_prev": has_prev,
            "next_cursor": next_cursor,
        },
    }
