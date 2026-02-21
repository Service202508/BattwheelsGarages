"""
Tenant Observability & Governance Service (Phase G)
===================================================

Provides tenant-aware logging, monitoring, and governance capabilities.

Features:
- Per-organization activity logging
- Tenant-scoped metrics collection
- Usage tracking and quota monitoring
- Data retention policies
- Compliance audit trails

Architecture:
- All logs tagged with organization_id
- Metrics aggregated per-tenant
- Retention policies applied per-org based on plan
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ActivityCategory(str, Enum):
    AUTH = "auth"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    ADMIN = "admin"
    INTEGRATION = "integration"
    BILLING = "billing"
    SECURITY = "security"
    SYSTEM = "system"


@dataclass
class TenantActivityLog:
    """Activity log entry scoped to organization"""
    log_id: str
    organization_id: str
    user_id: Optional[str]
    category: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    level: str = "info"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "category": self.category,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "level": self.level,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp
        }


@dataclass
class TenantMetrics:
    """Metrics snapshot for an organization"""
    organization_id: str
    period_start: str
    period_end: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "metrics": self.metrics
        }


@dataclass
class UsageQuota:
    """Usage quota tracking for an organization"""
    organization_id: str
    quota_type: str  # e.g., "api_calls", "storage_gb", "users"
    limit: int
    used: int
    period: str  # "daily", "monthly", "unlimited"
    reset_at: Optional[str] = None
    
    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)
    
    @property
    def is_exceeded(self) -> bool:
        return self.used >= self.limit
    
    @property
    def usage_percent(self) -> float:
        if self.limit == 0:
            return 0.0
        return (self.used / self.limit) * 100


class TenantObservabilityService:
    """
    Tenant-aware observability service.
    
    Provides:
    - Activity logging per organization
    - Metrics collection per organization
    - Usage tracking and quota management
    - Data retention enforcement
    """
    
    def __init__(self, db):
        self.db = db
        self.activity_logs = db.tenant_activity_logs
        self.metrics = db.tenant_metrics
        self.quotas = db.tenant_quotas
        self._index_created = False
    
    async def ensure_indexes(self):
        """Create necessary indexes"""
        if self._index_created:
            return
        
        try:
            # Activity logs indexes
            await self.activity_logs.create_index([
                ("organization_id", 1),
                ("timestamp", -1)
            ])
            await self.activity_logs.create_index([
                ("organization_id", 1),
                ("category", 1),
                ("timestamp", -1)
            ])
            
            # Metrics indexes
            await self.metrics.create_index([
                ("organization_id", 1),
                ("period_start", -1)
            ])
            
            # Quotas indexes
            await self.quotas.create_index([
                ("organization_id", 1),
                ("quota_type", 1)
            ], unique=True)
            
            self._index_created = True
            logger.info("Observability indexes created")
        except Exception as e:
            logger.warning(f"Index creation skipped: {e}")
    
    # ==================== ACTIVITY LOGGING ====================
    
    async def log_activity(
        self,
        organization_id: str,
        category: str,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: str = "info",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TenantActivityLog:
        """Log an activity for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required for activity logging")
        
        await self.ensure_indexes()
        
        import uuid
        log_entry = TenantActivityLog(
            log_id=f"log_{uuid.uuid4().hex[:12]}",
            organization_id=organization_id,
            user_id=user_id,
            category=category,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            level=level,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        await self.activity_logs.insert_one(log_entry.to_dict())
        
        return log_entry
    
    async def query_activity_logs(
        self,
        organization_id: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Query activity logs for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        query = {"organization_id": organization_id}
        
        if category:
            query["category"] = category
        if user_id:
            query["user_id"] = user_id
        
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date.isoformat()
            if end_date:
                query["timestamp"]["$lte"] = end_date.isoformat()
        
        logs = await self.activity_logs.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        return logs
    
    async def get_activity_summary(
        self,
        organization_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get activity summary for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        pipeline = [
            {
                "$match": {
                    "organization_id": organization_id,
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        by_category = {}
        async for doc in self.activity_logs.aggregate(pipeline):
            by_category[doc["_id"]] = doc["count"]
        
        total = sum(by_category.values())
        
        return {
            "organization_id": organization_id,
            "period_days": days,
            "total_activities": total,
            "by_category": by_category
        }
    
    # ==================== METRICS ====================
    
    async def record_metrics(
        self,
        organization_id: str,
        metrics: Dict[str, Any],
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> TenantMetrics:
        """Record metrics for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        now = datetime.now(timezone.utc)
        start = period_start or now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = period_end or now
        
        metric_entry = TenantMetrics(
            organization_id=organization_id,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            metrics=metrics
        )
        
        await self.metrics.update_one(
            {
                "organization_id": organization_id,
                "period_start": start.isoformat()
            },
            {"$set": metric_entry.to_dict()},
            upsert=True
        )
        
        return metric_entry
    
    async def get_metrics_history(
        self,
        organization_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get metrics history for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        metrics = await self.metrics.find(
            {
                "organization_id": organization_id,
                "period_start": {"$gte": start_date}
            },
            {"_id": 0}
        ).sort("period_start", -1).to_list(days)
        
        return metrics
    
    # ==================== QUOTA MANAGEMENT ====================
    
    async def set_quota(
        self,
        organization_id: str,
        quota_type: str,
        limit: int,
        period: str = "monthly"
    ) -> UsageQuota:
        """Set a quota for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        # Calculate reset time
        now = datetime.now(timezone.utc)
        if period == "daily":
            reset_at = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            next_month = now.replace(day=1) + timedelta(days=32)
            reset_at = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            reset_at = None
        
        quota = UsageQuota(
            organization_id=organization_id,
            quota_type=quota_type,
            limit=limit,
            used=0,
            period=period,
            reset_at=reset_at.isoformat() if reset_at else None
        )
        
        await self.quotas.update_one(
            {"organization_id": organization_id, "quota_type": quota_type},
            {"$set": {
                "organization_id": organization_id,
                "quota_type": quota_type,
                "limit": limit,
                "period": period,
                "reset_at": quota.reset_at
            }, "$setOnInsert": {"used": 0}},
            upsert=True
        )
        
        return quota
    
    async def increment_usage(
        self,
        organization_id: str,
        quota_type: str,
        amount: int = 1
    ) -> Optional[UsageQuota]:
        """Increment usage for a quota"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        result = await self.quotas.find_one_and_update(
            {"organization_id": organization_id, "quota_type": quota_type},
            {"$inc": {"used": amount}},
            return_document=True
        )
        
        if result:
            return UsageQuota(
                organization_id=result["organization_id"],
                quota_type=result["quota_type"],
                limit=result["limit"],
                used=result["used"],
                period=result["period"],
                reset_at=result.get("reset_at")
            )
        return None
    
    async def get_quota_status(
        self,
        organization_id: str,
        quota_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get quota status for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        query = {"organization_id": organization_id}
        if quota_type:
            query["quota_type"] = quota_type
        
        docs = await self.quotas.find(query, {"_id": 0}).to_list(20)
        
        status = []
        for doc in docs:
            quota = UsageQuota(**doc)
            status.append({
                "quota_type": quota.quota_type,
                "limit": quota.limit,
                "used": quota.used,
                "remaining": quota.remaining,
                "usage_percent": round(quota.usage_percent, 2),
                "is_exceeded": quota.is_exceeded,
                "period": quota.period,
                "reset_at": quota.reset_at
            })
        
        return status
    
    # ==================== DATA RETENTION ====================
    
    async def apply_retention_policy(
        self,
        organization_id: str,
        collection_name: str,
        retention_days: int
    ) -> int:
        """Apply data retention policy - delete old records"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
        
        collection = self.db[collection_name]
        result = await collection.delete_many({
            "organization_id": organization_id,
            "timestamp": {"$lt": cutoff}
        })
        
        if result.deleted_count > 0:
            logger.info(f"Retention: Deleted {result.deleted_count} records from {collection_name} for org {organization_id}")
        
        return result.deleted_count
    
    async def get_organization_stats(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive stats for an organization"""
        if not organization_id:
            raise ValueError("organization_id is required")
        
        # Get activity summary
        activity_summary = await self.get_activity_summary(organization_id, days=30)
        
        # Get quota status
        quota_status = await self.get_quota_status(organization_id)
        
        # Get recent metrics
        recent_metrics = await self.get_metrics_history(organization_id, days=7)
        
        return {
            "organization_id": organization_id,
            "activity_summary": activity_summary,
            "quotas": quota_status,
            "recent_metrics": recent_metrics[:7]  # Last 7 days
        }


# ==================== SERVICE SINGLETON ====================

_observability_service: Optional[TenantObservabilityService] = None


def init_tenant_observability_service(db) -> TenantObservabilityService:
    """Initialize the tenant observability service singleton"""
    global _observability_service
    _observability_service = TenantObservabilityService(db)
    logger.info("TenantObservabilityService initialized (Phase G)")
    return _observability_service


def get_tenant_observability_service() -> TenantObservabilityService:
    """Get the tenant observability service singleton"""
    if _observability_service is None:
        raise RuntimeError("TenantObservabilityService not initialized")
    return _observability_service
