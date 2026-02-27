"""
Battwheels OS - Data Sanitization Service
Identifies and removes test/dummy data with full audit logging
"""

import asyncio
import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ============== TEST DATA PATTERNS ==============

TEST_PATTERNS = {
    "name_patterns": [
        r"^test",
        r"^dummy",
        r"^sample",
        r"^demo",
        r"TEST_",
        r"DUMMY_",
        r"SAMPLE_",
        r"temp_",
        r"_test$",
        r"_dummy$",
        r"^fake",
        r"lorem\s*ipsum",
        r"^xxx",
        r"^zzz",
        r"placeholder",
        r"TEST\d+",
    ],
    "email_patterns": [
        r"@test\.",
        r"@dummy\.",
        r"@example\.",
        r"@fake\.",
        r"test@",
        r"dummy@",
        r"noreply@",
        r"@mailinator\.",
        r"@yopmail\.",
        r"xxx@",
    ],
    "phone_patterns": [
        r"^0{10}",
        r"^1{10}",
        r"^9999999999",
        r"^1234567890",
        r"^0000000000",
        r"123-456-7890",
    ],
    "vin_patterns": [
        r"^TEST",
        r"^DUMMY",
        r"^XXXX",
        r"^0{17}",
        r"^1{17}",
        r"TESTVEHICLE",
        r"SAMPLEVEHICLE",
    ],
    "invalid_values": {
        "negative_quantity": lambda x: x.get("quantity", 0) < 0 or x.get("stock", 0) < 0,
        "zero_price_product": lambda x: x.get("item_type") == "inventory" and x.get("rate", 1) <= 0,
        "unrealistic_odometer": lambda x: x.get("odometer_reading", 0) > 9999999,
        "future_dates": lambda x: x.get("created_at") and x.get("created_at") > datetime.now(timezone.utc).isoformat(),
    }
}

# Collection deletion order (respect referential integrity)
DELETION_ORDER = [
    # Child records first
    "invoice_payments",
    "invoice_line_items",
    "invoice_attachments",
    "invoice_comments",
    "invoice_history",
    "invoice_share_links",
    "estimate_line_items",
    "estimate_attachments",
    "estimate_history",
    "estimate_share_links",
    "bill_line_items",
    "bill_payments",
    "bill_history",
    "salesorder_line_items",
    "salesorder_fulfillments",
    "salesorder_history",
    "po_line_items",
    "payment_history",
    "item_history",
    "item_serial_numbers",
    "item_batch_numbers",
    "item_serial_batches",
    "item_stock_locations",
    "item_prices",
    "contact_history",
    "contact_persons",
    "customer_history",
    "customer_credits",
    "inventory_history",
    "serial_batch_history",
    "technician_action_logs",
    # Parent records
    "invoices",
    "invoices_enhanced",
    "estimates",
    "estimates_enhanced",
    "bills",
    "bills_enhanced",
    "salesorders",
    "salesorders_enhanced",
    "sales_orders",
    "purchaseorders",
    "purchase_orders",
    "purchase_orders_enhanced",
    "creditnotes",
    "vendorcredits",
    "customerpayments",
    "vendorpayments",
    "payments",
    "expenses",
    "shipments",
    "failure_cards",
    "tickets",
    "work_orders",
    "items",
    "inventory",
    "parts",
    "service_items",
    "contacts",
    "contacts_enhanced",
    "customers",
    "customers_enhanced",
    "suppliers",
    "vehicles",
]


class DataSanitizationResult(BaseModel):
    collection: str
    total_records: int
    test_records_found: int
    records_deleted: int
    records_kept: int
    sample_deleted: List[Dict] = []
    errors: List[str] = []


class SanitizationReport(BaseModel):
    job_id: str
    organization_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str
    mode: str  # "audit" or "delete"
    collections_processed: int = 0
    total_records_scanned: int = 0
    total_test_records: int = 0
    total_deleted: int = 0
    results: List[DataSanitizationResult] = []
    rollback_available: bool = False


class DataSanitizationService:
    """Service for identifying and removing test/dummy data"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency"""
        compiled = {}
        for key, patterns in TEST_PATTERNS.items():
            if isinstance(patterns, list):
                compiled[key] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled
    
    def _is_test_record(self, record: Dict, patterns: Dict) -> Tuple[bool, List[str]]:
        """Check if a record matches test data patterns"""
        reasons = []
        
        # Check name patterns
        name_fields = ["name", "contact_name", "customer_name", "vendor_name", 
                       "item_name", "description", "company_name", "vehicle_name"]
        for field in name_fields:
            value = record.get(field, "")
            if value:
                for pattern in patterns.get("name_patterns", []):
                    if pattern.search(str(value)):
                        reasons.append(f"Name field '{field}' matches test pattern: {value}")
                        break
        
        # Check email patterns
        email_fields = ["email", "contact_email", "customer_email"]
        for field in email_fields:
            value = record.get(field, "")
            if value:
                for pattern in patterns.get("email_patterns", []):
                    if pattern.search(str(value)):
                        reasons.append(f"Email '{field}' matches test pattern: {value}")
                        break
        
        # Check phone patterns
        phone_fields = ["phone", "mobile", "contact_phone"]
        for field in phone_fields:
            value = record.get(field, "")
            if value:
                for pattern in patterns.get("phone_patterns", []):
                    if pattern.search(str(value)):
                        reasons.append(f"Phone '{field}' matches test pattern: {value}")
                        break
        
        # Check VIN patterns
        vin = record.get("vin", "")
        if vin:
            for pattern in patterns.get("vin_patterns", []):
                if pattern.search(str(vin)):
                    reasons.append(f"VIN matches test pattern: {vin}")
                    break
        
        # Check invalid values
        for check_name, check_fn in TEST_PATTERNS["invalid_values"].items():
            try:
                if check_fn(record):
                    reasons.append(f"Invalid value detected: {check_name}")
            except Exception:
                pass
        
        return len(reasons) > 0, reasons
    
    async def _create_backup(self, collection_name: str, records: List[Dict], job_id: str) -> str:
        """Create backup of records before deletion"""
        backup_collection = f"_backup_{job_id}_{collection_name}"
        if records:
            # Remove _id to allow re-insertion
            clean_records = [{k: v for k, v in r.items() if k != "_id"} for r in records]
            await self.db[backup_collection].insert_many(clean_records)
        return backup_collection
    
    async def analyze_collection(
        self, 
        collection_name: str, 
        organization_id: str,
        patterns: Dict
    ) -> DataSanitizationResult:
        """Analyze a single collection for test data"""
        result = DataSanitizationResult(
            collection=collection_name,
            total_records=0,
            test_records_found=0,
            records_deleted=0,
            records_kept=0,
            sample_deleted=[],
            errors=[]
        )
        
        try:
            # Build org filter
            org_filter = {"organization_id": organization_id} if organization_id else {}
            
            # Count total
            result.total_records = await self.db[collection_name].count_documents(org_filter)
            
            if result.total_records == 0:
                return result
            
            # Scan for test records
            test_records = []
            cursor = self.db[collection_name].find(org_filter)
            
            async for record in cursor:
                is_test, reasons = self._is_test_record(record, patterns)
                if is_test:
                    record_id = str(record.get("_id", record.get("id", "unknown")))
                    test_records.append({
                        "id": record_id,
                        "name": record.get("name", record.get("contact_name", record.get("item_name", "N/A"))),
                        "reasons": reasons
                    })
            
            result.test_records_found = len(test_records)
            result.records_kept = result.total_records - result.test_records_found
            result.sample_deleted = test_records[:5]  # Sample of first 5
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Error analyzing {collection_name}: {e}")
        
        return result
    
    async def sanitize_collection(
        self,
        collection_name: str,
        organization_id: str,
        patterns: Dict,
        job_id: str,
        dry_run: bool = True
    ) -> DataSanitizationResult:
        """Sanitize a single collection - remove test data"""
        result = DataSanitizationResult(
            collection=collection_name,
            total_records=0,
            test_records_found=0,
            records_deleted=0,
            records_kept=0,
            sample_deleted=[],
            errors=[]
        )
        
        try:
            org_filter = {"organization_id": organization_id} if organization_id else {}
            result.total_records = await self.db[collection_name].count_documents(org_filter)
            
            if result.total_records == 0:
                return result
            
            # Find test records
            test_record_ids = []
            test_records_full = []
            cursor = self.db[collection_name].find(org_filter)
            
            async for record in cursor:
                is_test, reasons = self._is_test_record(record, patterns)
                if is_test:
                    test_record_ids.append(record["_id"])
                    test_records_full.append(record)
                    result.sample_deleted.append({
                        "id": str(record["_id"]),
                        "name": record.get("name", record.get("contact_name", "N/A")),
                        "reasons": reasons[:3]  # First 3 reasons
                    })
            
            result.test_records_found = len(test_record_ids)
            
            if not dry_run and test_record_ids:
                # Create backup first
                await self._create_backup(collection_name, test_records_full, job_id)
                
                # Delete test records
                delete_result = await self.db[collection_name].delete_many(
                    {"_id": {"$in": test_record_ids}}
                )
                result.records_deleted = delete_result.deleted_count
                
                # Log deletion
                await self.db.sanitization_audit_log.insert_many([
                    {
                        "job_id": job_id,
                        "collection": collection_name,
                        "record_id": str(rid),
                        "action": "deleted",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "organization_id": organization_id
                    }
                    for rid in test_record_ids
                ])
            
            result.records_kept = result.total_records - result.records_deleted
            result.sample_deleted = result.sample_deleted[:10]  # Limit to 10 samples
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Error sanitizing {collection_name}: {e}")
        
        return result
    
    async def run_sanitization(
        self,
        organization_id: str,
        mode: str = "audit",  # "audit" or "delete"
        collections: Optional[List[str]] = None
    ) -> SanitizationReport:
        """Run full sanitization process"""
        job_id = f"SAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        report = SanitizationReport(
            job_id=job_id,
            organization_id=organization_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            status="running",
            mode=mode
        )
        
        # Save initial report
        await self.db.sanitization_jobs.insert_one(report.dict())
        
        try:
            patterns = self._compile_patterns()
            target_collections = collections or DELETION_ORDER
            
            for collection_name in target_collections:
                # Check if collection exists
                if collection_name not in await self.db.list_collection_names():
                    continue
                
                if mode == "audit":
                    result = await self.analyze_collection(
                        collection_name, organization_id, patterns
                    )
                else:
                    result = await self.sanitize_collection(
                        collection_name, organization_id, patterns, job_id, dry_run=False
                    )
                
                report.results.append(result)
                report.collections_processed += 1
                report.total_records_scanned += result.total_records
                report.total_test_records += result.test_records_found
                report.total_deleted += result.records_deleted
            
            report.status = "completed"
            report.completed_at = datetime.now(timezone.utc).isoformat()
            report.rollback_available = mode == "delete"
            
        except Exception as e:
            report.status = "failed"
            report.completed_at = datetime.now(timezone.utc).isoformat()
            logger.error(f"Sanitization failed: {e}")
        
        # Update final report
        await self.db.sanitization_jobs.update_one(
            {"job_id": job_id},
            {"$set": report.dict()}
        )
        
        return report
    
    async def rollback_sanitization(self, job_id: str) -> Dict:
        """Rollback a sanitization job using backups"""
        result = {
            "job_id": job_id,
            "status": "started",
            "collections_restored": 0,
            "records_restored": 0,
            "errors": []
        }
        
        try:
            # Find backup collections
            all_collections = await self.db.list_collection_names()
            backup_collections = [c for c in all_collections if c.startswith(f"_backup_{job_id}_")]
            
            for backup_col in backup_collections:
                original_name = backup_col.replace(f"_backup_{job_id}_", "")
                
                # Get backup records
                # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
                backup_records = await self.db[backup_col].find({}).to_list(length=1000)
                
                if backup_records:
                    # Restore to original collection
                    await self.db[original_name].insert_many(backup_records)
                    result["records_restored"] += len(backup_records)
                    result["collections_restored"] += 1
                    
                    # Drop backup
                    await self.db[backup_col].drop()
            
            # Update audit log
            await self.db.sanitization_audit_log.update_many(
                {"job_id": job_id},
                {"$set": {"rolled_back": True, "rolled_back_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            result["status"] = "completed"
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            logger.error(f"Rollback failed: {e}")
        
        return result
    
    async def get_sanitization_report(self, job_id: str) -> Optional[SanitizationReport]:
        """Get sanitization report by job ID"""
        doc = await self.db.sanitization_jobs.find_one({"job_id": job_id}, {"_id": 0})
        if doc:
            return SanitizationReport(**doc)
        return None
    
    async def list_sanitization_jobs(self, organization_id: str, limit: int = 20) -> List[Dict]:
        """List recent sanitization jobs"""
        cursor = self.db.sanitization_jobs.find(
            {"organization_id": organization_id},
            {"_id": 0, "results": 0}  # Exclude detailed results for list view
        ).sort("started_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)


# ============== DATA VALIDATION SERVICE ==============

class DataValidationService:
    """Service for validating data quality after cleanup"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def validate_referential_integrity(self, organization_id: str) -> Dict:
        """Check referential integrity across collections"""
        issues = []
        
        # Check invoices reference existing customers
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        invoices = await self.db.invoices.find(
            {"organization_id": organization_id},
            {"customer_id": 1, "invoice_number": 1}
        ).to_list(length=1000)
        
        customer_ids = set()
        async for c in self.db.contacts.find({"organization_id": organization_id}, {"contact_id": 1}):
            customer_ids.add(c.get("contact_id"))
        
        for inv in invoices:
            if inv.get("customer_id") and inv["customer_id"] not in customer_ids:
                issues.append({
                    "type": "orphan_invoice",
                    "invoice": inv.get("invoice_number"),
                    "missing_customer": inv.get("customer_id")
                })
        
        # Check items have valid stock levels
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        items_with_negative = await self.db.items.find(
            {"organization_id": organization_id, "stock_on_hand": {"$lt": 0}},
            {"item_id": 1, "name": 1, "stock_on_hand": 1}
        ).to_list(length=1000)
        
        for item in items_with_negative:
            issues.append({
                "type": "negative_stock",
                "item": item.get("name"),
                "stock": item.get("stock_on_hand")
            })
        
        return {
            "organization_id": organization_id,
            "validation_date": datetime.now(timezone.utc).isoformat(),
            "total_issues": len(issues),
            "issues": issues[:50],  # Limit to 50
            "status": "clean" if not issues else "issues_found"
        }
    
    async def validate_data_completeness(self, organization_id: str) -> Dict:
        """Check for required fields and data completeness"""
        completeness_issues = []
        
        # Check contacts have required fields
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        contacts = await self.db.contacts.find(
            {"organization_id": organization_id}
        ).to_list(length=1000)
        
        for contact in contacts:
            missing = []
            if not contact.get("contact_name"):
                missing.append("contact_name")
            if not contact.get("email") and not contact.get("phone"):
                missing.append("email or phone")
            
            if missing:
                completeness_issues.append({
                    "type": "incomplete_contact",
                    "contact_id": contact.get("contact_id"),
                    "missing_fields": missing
                })
        
        return {
            "organization_id": organization_id,
            "validation_date": datetime.now(timezone.utc).isoformat(),
            "total_issues": len(completeness_issues),
            "issues": completeness_issues[:50],
            "status": "complete" if not completeness_issues else "incomplete_data"
        }
