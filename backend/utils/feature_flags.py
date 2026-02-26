"""
Battwheels OS - Feature Flags Utility
======================================
Deterministic feature flag evaluation for controlled rollout.
"""

import hashlib
from typing import Optional


async def feature_enabled(db, feature_key: str, org_id: str) -> bool:
    """
    Check if a feature flag is enabled for a given organization.
    
    Flag statuses:
    - "off": Disabled for everyone
    - "on": Enabled for everyone
    - "canary": Enabled only for specific org_ids in canary_org_ids
    - "percentage": Enabled for a deterministic percentage of orgs
    """
    flag = await db.feature_flags.find_one({"feature_key": feature_key}, {"_id": 0})
    if not flag:
        return False
    
    status = flag.get("status", "off")
    
    if status == "off":
        return False
    elif status == "on":
        return True
    elif status == "canary":
        return org_id in flag.get("canary_org_ids", [])
    elif status == "percentage":
        # Deterministic hash so same org always gets same result
        hash_val = int(hashlib.md5(f"{feature_key}:{org_id}".encode()).hexdigest(), 16)
        return (hash_val % 100) < flag.get("percentage", 0)
    
    return False


async def get_all_flags(db) -> list:
    """Get all feature flags"""
    return await db.feature_flags.find({}, {"_id": 0}).to_list(100)


async def get_flag(db, feature_key: str) -> Optional[dict]:
    """Get a single feature flag"""
    return await db.feature_flags.find_one({"feature_key": feature_key}, {"_id": 0})
