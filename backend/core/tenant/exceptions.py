"""
Tenant Context Exceptions
========================

Custom exceptions for tenant isolation violations.
All exceptions include detailed context for security auditing.
"""

from typing import Optional, Dict, Any


class TenantException(Exception):
    """Base exception for all tenant-related errors"""
    
    def __init__(
        self,
        message: str,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.org_id = org_id
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/audit"""
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "metadata": self.metadata
        }


class TenantContextMissing(TenantException):
    """
    Raised when a tenant context is required but not present.
    
    This is a P0 security violation - no endpoint should work without context
    unless explicitly marked as public.
    """
    
    def __init__(
        self,
        endpoint: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        message = f"Tenant context missing for endpoint: {endpoint}"
        super().__init__(
            message=message,
            user_id=user_id,
            metadata={**(metadata or {}), "endpoint": endpoint}
        )
        self.endpoint = endpoint


class TenantAccessDenied(TenantException):
    """
    Raised when a user attempts to access an organization they don't belong to.
    
    This is logged as a potential security incident.
    """
    
    def __init__(
        self,
        user_id: str,
        attempted_org_id: str,
        user_orgs: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        message = f"User {user_id} denied access to organization {attempted_org_id}"
        super().__init__(
            message=message,
            org_id=attempted_org_id,
            user_id=user_id,
            metadata={
                **(metadata or {}),
                "attempted_org_id": attempted_org_id,
                "user_organizations": user_orgs or []
            }
        )
        self.attempted_org_id = attempted_org_id
        self.user_orgs = user_orgs


class TenantBoundaryViolation(TenantException):
    """
    Raised when a query or operation attempts to cross tenant boundaries.
    
    Examples:
    - Query without organization_id filter on tenant data
    - Insert document missing organization_id
    - Update affecting records in other organizations
    
    This is the most critical security exception.
    """
    
    def __init__(
        self,
        operation: str,
        collection: str,
        current_org_id: str,
        violation_type: str,
        query: Optional[Dict] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        message = (
            f"Tenant boundary violation: {operation} on {collection} "
            f"(org: {current_org_id}, type: {violation_type})"
        )
        super().__init__(
            message=message,
            org_id=current_org_id,
            resource_type=collection,
            metadata={
                **(metadata or {}),
                "operation": operation,
                "collection": collection,
                "violation_type": violation_type,
                "query_attempted": query
            }
        )
        self.operation = operation
        self.collection = collection
        self.violation_type = violation_type
        self.query = query


class TenantDataLeakAttempt(TenantException):
    """
    Raised when an operation could potentially leak data across tenants.
    
    This is raised proactively when:
    - Vector similarity search doesn't include org filter
    - Aggregation pipeline doesn't start with $match on org_id
    - Join/lookup operations cross tenant boundaries
    
    Treated as a critical security incident.
    """
    
    def __init__(
        self,
        operation: str,
        source_org_id: str,
        potential_leak_reason: str,
        affected_collections: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        message = (
            f"Potential data leak attempt: {operation} "
            f"(org: {source_org_id}, reason: {potential_leak_reason})"
        )
        super().__init__(
            message=message,
            org_id=source_org_id,
            metadata={
                **(metadata or {}),
                "operation": operation,
                "leak_reason": potential_leak_reason,
                "affected_collections": affected_collections or []
            }
        )
        self.operation = operation
        self.potential_leak_reason = potential_leak_reason
        self.affected_collections = affected_collections


class TenantQuotaExceeded(TenantException):
    """
    Raised when a tenant exceeds their plan limits.
    
    Examples:
    - Too many users
    - Too many API calls
    - Storage quota exceeded
    """
    
    def __init__(
        self,
        org_id: str,
        quota_type: str,
        current_usage: int,
        limit: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        message = (
            f"Quota exceeded for {org_id}: {quota_type} "
            f"(usage: {current_usage}, limit: {limit})"
        )
        super().__init__(
            message=message,
            org_id=org_id,
            metadata={
                **(metadata or {}),
                "quota_type": quota_type,
                "current_usage": current_usage,
                "limit": limit
            }
        )
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.limit = limit


class TenantSuspended(TenantException):
    """
    Raised when attempting to access a suspended organization.
    """
    
    def __init__(
        self,
        org_id: str,
        suspension_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        message = f"Organization {org_id} is suspended"
        if suspension_reason:
            message += f": {suspension_reason}"
        
        super().__init__(
            message=message,
            org_id=org_id,
            metadata={
                **(metadata or {}),
                "suspension_reason": suspension_reason
            }
        )
        self.suspension_reason = suspension_reason
