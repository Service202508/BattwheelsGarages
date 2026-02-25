"""
DEPRECATED — DO NOT USE
========================
This file contained TenantIsolationMiddleware which is NOT mounted in server.py.
Active tenant enforcement is handled by TenantGuardMiddleware in core/tenant/guard.py.

This file is preserved as a tombstone to prevent accidental re-introduction.
If you need tenant middleware, use:
    from core.tenant.guard import TenantGuardMiddleware

Tombstoned: 2026-02-25 (Grand Audit C-04)
"""

# NO CLASSES OR FUNCTIONS — intentionally empty.
# Any import from this file should fail loudly.
