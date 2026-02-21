"""
Battwheels OS - SaaS Multi-Tenant Core Architecture
==================================================

Enterprise-grade multi-tenant isolation layer for cloud SaaS deployment.

This module provides:
- TenantContext: Central context object propagated through all layers
- TenantGuard: Hard enforcement of tenant boundaries
- TenantRepository: Base class for tenant-aware data access
- TenantEventEmitter: Tenant-tagged event emission

Architecture:
    Request → TenantGuard → TenantContext → Services → TenantRepository → MongoDB

Key Guarantees:
- Zero cross-tenant data access
- Mandatory org_id on all tenant data
- Audit logging of all access attempts
- Default-deny on missing context

Version: 1.0.0
Author: Battwheels Cloud Architecture Team
"""

from .context import (
    TenantContext,
    TenantContextManager,
    get_tenant_context,
    init_tenant_context_manager,
    tenant_context_required,
)

from .guard import (
    TenantGuard,
    TenantGuardMiddleware,
    tenant_boundary_check,
    enforce_tenant_isolation,
)

from .repository import (
    TenantRepository,
    TenantQueryBuilder,
    create_tenant_repository,
)

from .events import (
    TenantEvent,
    TenantEventEmitter,
    emit_tenant_event,
)

from .audit import (
    TenantAuditLog,
    TenantAuditService,
    audit_tenant_action,
)

from .exceptions import (
    TenantContextMissing,
    TenantAccessDenied,
    TenantBoundaryViolation,
    TenantDataLeakAttempt,
)

__all__ = [
    # Context
    "TenantContext",
    "TenantContextManager", 
    "get_tenant_context",
    "init_tenant_context_manager",
    "tenant_context_required",
    # Guard
    "TenantGuard",
    "TenantGuardMiddleware",
    "tenant_boundary_check",
    "enforce_tenant_isolation",
    # Repository
    "TenantRepository",
    "TenantQueryBuilder",
    "create_tenant_repository",
    # Events
    "TenantEvent",
    "TenantEventEmitter",
    "emit_tenant_event",
    # Audit
    "TenantAuditLog",
    "TenantAuditService",
    "audit_tenant_action",
    # Exceptions
    "TenantContextMissing",
    "TenantAccessDenied",
    "TenantBoundaryViolation",
    "TenantDataLeakAttempt",
]
