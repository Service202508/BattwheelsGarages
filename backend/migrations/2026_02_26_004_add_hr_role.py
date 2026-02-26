"""Add HR role to RBAC system. No DB changes needed — roles are code-defined."""


async def up(db):
    # HR role is defined in middleware/rbac.py ROLE_HIERARCHY
    # This migration is a no-op marker to track that the HR role was introduced in v2.5.0
    return "HR role added to RBAC hierarchy (code change, no DB migration needed)"


async def down(db):
    pass
