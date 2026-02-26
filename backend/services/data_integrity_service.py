"""
Battwheels OS - Data Integrity & Referential Completeness Service
Ensures consistent data relationships and field completeness across all Battwheels OS modules
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

logger = logging.getLogger(__name__)


class DataIntegrityService:
    """Service for maintaining data integrity and referential completeness"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # ============== SCHEMA DEFINITIONS ==============
    
    # Required fields for each collection (Zoho Books parity)
    REQUIRED_FIELDS = {
        "invoices": {
            "invoice_id": str,
            "invoice_number": str,
            "customer_id": str,
            "customer_name": str,
            "invoice_date": str,
            "due_date": str,
            "status": str,
            "grand_total": float,
            "balance_due": float,
            "subtotal": float,
            "total_tax": float,
            "currency_code": str,
            "organization_id": str,
            "line_items": list,
        },
        "estimates": {
            "estimate_id": str,
            "estimate_number": str,
            "customer_id": str,
            "customer_name": str,
            "date": str,
            "expiry_date": str,
            "status": str,
            "total": float,
            "subtotal": float,
            "organization_id": str,
            "line_items": list,
        },
        "contacts": {
            "contact_id": str,
            "contact_name": str,
            "contact_type": str,  # customer/vendor
            "organization_id": str,
        },
        "items": {
            "item_id": str,
            "name": str,
            "rate": float,
            "item_type": str,  # sales/purchase/sales_and_purchase/inventory
            "organization_id": str,
        },
        "bills": {
            "bill_id": str,
            "bill_number": str,
            "vendor_id": str,
            "vendor_name": str,
            "date": str,
            "due_date": str,
            "status": str,
            "total": float,
            "balance": float,
            "organization_id": str,
        },
        "payments": {
            "payment_id": str,
            "payment_number": str,
            "customer_id": str,
            "amount": float,
            "payment_date": str,
            "payment_mode": str,
            "organization_id": str,
        },
        "expenses": {
            "expense_id": str,
            "date": str,
            "amount": float,
            "account_id": str,
            "organization_id": str,
        },
        "purchase_orders": {
            "po_id": str,
            "po_number": str,
            "supplier_id": str,
            "order_date": str,
            "status": str,
            "total_amount": float,
            "organization_id": str,
        },
        "sales_orders": {
            "salesorder_id": str,
            "salesorder_number": str,
            "customer_id": str,
            "date": str,
            "status": str,
            "total": float,
            "organization_id": str,
        },
        "creditnotes": {
            "creditnote_id": str,
            "creditnote_number": str,
            "customer_id": str,
            "date": str,
            "status": str,
            "total": float,
            "balance": float,
            "organization_id": str,
        },
        "vendorcredits": {
            "vendor_credit_id": str,
            "vendor_credit_number": str,
            "vendor_id": str,
            "date": str,
            "status": str,
            "total": float,
            "balance": float,
            "organization_id": str,
        },
        "tickets": {
            "ticket_id": str,
            "title": str,
            "status": str,
            "priority": str,
            "organization_id": str,
            "created_at": str,
        },
    }
    
    # Foreign key relationships
    FOREIGN_KEYS = {
        "invoices": [
            ("customer_id", "contacts", "contact_id"),
        ],
        "estimates": [
            ("customer_id", "contacts", "contact_id"),
        ],
        "bills": [
            ("vendor_id", "contacts", "contact_id"),
        ],
        "payments": [
            ("customer_id", "contacts", "contact_id"),
            ("invoice_id", "invoices", "invoice_id"),
        ],
        "purchase_orders": [
            ("supplier_id", "suppliers", "supplier_id"),
        ],
        "sales_orders": [
            ("customer_id", "contacts", "contact_id"),
        ],
        "creditnotes": [
            ("customer_id", "contacts", "contact_id"),
        ],
        "vendorcredits": [
            ("vendor_id", "contacts", "contact_id"),
        ],
        "tickets": [
            ("customer_id", "contacts", "contact_id"),
            ("vehicle_id", "vehicles", "vehicle_id"),
            ("assigned_technician_id", "users", "user_id"),
        ],
        "ticket_estimates": [
            ("ticket_id", "tickets", "ticket_id"),
            ("customer_id", "contacts", "contact_id"),
        ],
        "ticket_invoices": [
            ("ticket_id", "tickets", "ticket_id"),
            ("estimate_id", "ticket_estimates", "estimate_id"),
        ],
    }
    
    # Field aliases (different field names that mean the same thing)
    FIELD_ALIASES = {
        "invoices": {
            "total": "grand_total",
            "balance": "balance_due",
            "sub_total": "subtotal",
            "tax_total": "total_tax",
            "date": "invoice_date",
        },
        "estimates": {
            "estimate_date": "date",
            "grand_total": "total",
            "sub_total": "subtotal",
        },
        "bills": {
            "bill_date": "date",
            "grand_total": "total",
            "balance_due": "balance",
        },
        "payments": {
            "date": "payment_date",
            "payment_method": "payment_mode",
        },
        "expenses": {
            "expense_date": "date",
        },
    }
    
    # ============== AUDIT METHODS ==============
    
    async def run_full_audit(self, organization_id: Optional[str] = None) -> Dict:
        """Run comprehensive data integrity audit"""
        audit_id = f"AUDIT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        results = {
            "audit_id": audit_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "organization_id": organization_id,
            "field_completeness": {},
            "referential_integrity": {},
            "data_quality": {},
            "recommendations": [],
        }
        
        # 1. Check field completeness for each collection
        for collection in self.REQUIRED_FIELDS.keys():
            completeness = await self._check_field_completeness(collection, organization_id)
            results["field_completeness"][collection] = completeness
        
        # 2. Check referential integrity
        for collection, fk_defs in self.FOREIGN_KEYS.items():
            integrity = await self._check_referential_integrity(collection, fk_defs, organization_id)
            results["referential_integrity"][collection] = integrity
        
        # 3. Check data quality issues
        quality = await self._check_data_quality(organization_id)
        results["data_quality"] = quality
        
        # 4. Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store audit results (copy to avoid modifying return value)
        import copy
        audit_copy = copy.deepcopy(results)
        await self.db.data_integrity_audits.insert_one(audit_copy)
        
        return results
    
    async def _check_field_completeness(
        self, 
        collection: str, 
        organization_id: Optional[str] = None
    ) -> Dict:
        """Check field completeness for a collection"""
        required = self.REQUIRED_FIELDS.get(collection, {})
        aliases = self.FIELD_ALIASES.get(collection, {})
        
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        total = await self.db[collection].count_documents(filter_query)
        
        if total == 0:
            return {"total": 0, "missing_fields": {}}
        
        missing_fields = {}
        
        for field, field_type in required.items():
            # Check both the primary field name and any aliases
            field_names = [field]
            for alias, canonical in aliases.items():
                if canonical == field:
                    field_names.append(alias)
            
            # Build OR query for field and its aliases
            or_conditions = []
            for fname in field_names:
                or_conditions.extend([
                    {fname: {"$exists": False}},
                    {fname: None},
                    {fname: ""},
                ])
            
            missing = await self.db[collection].count_documents({
                **filter_query,
                "$and": [
                    {"$or": or_conditions}
                ]
            })
            
            if missing > 0:
                missing_fields[field] = {
                    "missing_count": missing,
                    "percentage": round((missing / total) * 100, 2)
                }
        
        return {
            "total": total,
            "missing_fields": missing_fields,
            "completeness_score": round(100 - (len(missing_fields) / len(required) * 100), 2) if required else 100
        }
    
    async def _check_referential_integrity(
        self,
        collection: str,
        fk_definitions: List[Tuple[str, str, str]],
        organization_id: Optional[str] = None
    ) -> Dict:
        """Check referential integrity for a collection"""
        results = {}
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        for fk_field, ref_collection, ref_field in fk_definitions:
            # Get all FK values from source collection
            pipeline = [
                {"$match": {
                    **filter_query,
                    fk_field: {"$exists": True, "$ne": None, "$ne": ""}
                }},
                {"$group": {"_id": f"${fk_field}"}},
            ]
            
            fk_values = set()
            async for doc in self.db[collection].aggregate(pipeline):
                if doc["_id"]:
                    fk_values.add(doc["_id"])
            
            if not fk_values:
                results[fk_field] = {"valid": 0, "invalid": 0, "orphan_ids": []}
                continue
            
            # Get valid reference values
            ref_pipeline = [
                {"$match": {ref_field: {"$in": list(fk_values)}}},
                {"$group": {"_id": f"${ref_field}"}},
            ]
            
            valid_refs = set()
            async for doc in self.db[ref_collection].aggregate(ref_pipeline):
                if doc["_id"]:
                    valid_refs.add(doc["_id"])
            
            orphans = fk_values - valid_refs
            
            results[fk_field] = {
                "total_references": len(fk_values),
                "valid": len(valid_refs),
                "invalid": len(orphans),
                "orphan_ids": list(orphans)[:10],  # Limit to first 10
                "ref_collection": ref_collection
            }
        
        return results
    
    async def _check_data_quality(self, organization_id: Optional[str] = None) -> Dict:
        """Check various data quality issues"""
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        quality = {}
        
        # 1. Check for duplicate invoice numbers
        pipeline = [
            {"$match": filter_query},
            {"$group": {"_id": "$invoice_number", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$count": "duplicates"}
        ]
        result = await self.db.invoices.aggregate(pipeline).to_list(1)
        quality["duplicate_invoice_numbers"] = result[0]["duplicates"] if result else 0
        
        # 2. Check for invoices with balance > total
        quality["invoices_balance_exceeds_total"] = await self.db.invoices.count_documents({
            **filter_query,
            "$expr": {"$gt": ["$balance_due", "$grand_total"]}
        })
        
        # 3. Check for negative amounts
        quality["negative_invoice_totals"] = await self.db.invoices.count_documents({
            **filter_query,
            "grand_total": {"$lt": 0}
        })
        
        # 4. Check for future-dated invoices (more than 30 days ahead)
        from datetime import timedelta
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        quality["far_future_invoices"] = await self.db.invoices.count_documents({
            **filter_query,
            "invoice_date": {"$gt": future_date}
        })
        
        # 5. Check for orphan line items (invoice_line_items without parent)
        invoice_ids = set()
        async for inv in self.db.invoices.find(filter_query, {"invoice_id": 1}):
            invoice_ids.add(inv.get("invoice_id"))
        
        orphan_lines = await self.db.invoice_line_items.count_documents({
            "invoice_id": {"$nin": list(invoice_ids)}
        })
        quality["orphan_invoice_line_items"] = orphan_lines
        
        # 6. Check for payments without invoice allocation
        quality["unallocated_payments"] = await self.db.payments.count_documents({
            **filter_query,
            "$or": [
                {"allocations": {"$exists": False}},
                {"allocations": []},
                {"allocations": None}
            ],
            "invoice_id": {"$exists": False}
        })
        
        # 7. Check for items without prices
        quality["items_without_rate"] = await self.db.items.count_documents({
            **filter_query,
            "$or": [
                {"rate": {"$exists": False}},
                {"rate": None},
                {"rate": 0}
            ]
        })
        
        return quality
    
    def _generate_recommendations(self, audit_results: Dict) -> List[Dict]:
        """Generate actionable recommendations based on audit results"""
        recommendations = []
        
        # Field completeness recommendations
        for collection, data in audit_results.get("field_completeness", {}).items():
            for field, info in data.get("missing_fields", {}).items():
                if info["percentage"] > 10:  # More than 10% missing
                    recommendations.append({
                        "priority": "HIGH" if info["percentage"] > 50 else "MEDIUM",
                        "type": "FIELD_COMPLETENESS",
                        "collection": collection,
                        "field": field,
                        "message": f"{info['missing_count']} records ({info['percentage']}%) missing '{field}' in {collection}",
                        "action": f"Run field normalization for {collection}.{field}"
                    })
        
        # Referential integrity recommendations
        for collection, fk_data in audit_results.get("referential_integrity", {}).items():
            for fk_field, info in fk_data.items():
                if isinstance(info, dict) and info.get("invalid", 0) > 0:
                    recommendations.append({
                        "priority": "HIGH",
                        "type": "REFERENTIAL_INTEGRITY",
                        "collection": collection,
                        "field": fk_field,
                        "message": f"{info['invalid']} orphan references in {collection}.{fk_field}",
                        "action": f"Link orphan records to valid {info['ref_collection']} or create placeholder records"
                    })
        
        # Data quality recommendations
        quality = audit_results.get("data_quality", {})
        
        if quality.get("duplicate_invoice_numbers", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "type": "DATA_QUALITY",
                "message": f"{quality['duplicate_invoice_numbers']} duplicate invoice numbers found",
                "action": "Deduplicate invoices or assign unique numbers"
            })
        
        if quality.get("unallocated_payments", 0) > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "type": "DATA_QUALITY",
                "message": f"{quality['unallocated_payments']} payments without invoice allocation",
                "action": "Allocate payments to invoices or mark as advance payments"
            })
        
        return recommendations
    
    # ============== REPAIR METHODS ==============
    
    async def repair_field_completeness(
        self,
        collection: str,
        organization_id: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict:
        """Repair missing fields by normalizing aliases and setting defaults"""
        aliases = self.FIELD_ALIASES.get(collection, {})
        required = self.REQUIRED_FIELDS.get(collection, {})
        
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        repairs = {"normalized": 0, "defaults_set": 0, "skipped": 0}
        
        # Get all documents that need repair
        cursor = self.db[collection].find(filter_query)
        
        async for doc in cursor:
            updates = {}
            doc_id = doc.get("_id")
            
            # Normalize aliases
            for alias, canonical in aliases.items():
                if alias in doc and canonical not in doc:
                    updates[canonical] = doc[alias]
            
            # Set defaults for missing required fields
            for field, field_type in required.items():
                if field not in doc and field not in updates:
                    if field_type == str:
                        updates[field] = ""
                    elif field_type == float:
                        updates[field] = 0.0
                    elif field_type == list:
                        updates[field] = []
                    elif field_type == dict:
                        updates[field] = {}
            
            if updates and not dry_run:
                await self.db[collection].update_one(
                    {"_id": doc_id},
                    {"$set": updates}
                )
                repairs["normalized"] += len([k for k in updates if k in aliases.values()])
                repairs["defaults_set"] += len([k for k in updates if k not in aliases.values()])
            elif updates:
                repairs["skipped"] += 1
        
        return repairs
    
    async def repair_referential_integrity(
        self,
        collection: str,
        fk_field: str,
        ref_collection: str,
        ref_field: str,
        organization_id: Optional[str] = None,
        strategy: str = "create_placeholder",  # or "nullify"
        dry_run: bool = True
    ) -> Dict:
        """Repair orphan references"""
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        # Get orphan FK values
        fk_values = set()
        async for doc in self.db[collection].find({
            **filter_query,
            fk_field: {"$exists": True, "$ne": None, "$ne": ""}
        }, {fk_field: 1}):
            fk_values.add(doc.get(fk_field))
        
        valid_refs = set()
        async for doc in self.db[ref_collection].find({
            ref_field: {"$in": list(fk_values)}
        }, {ref_field: 1}):
            valid_refs.add(doc.get(ref_field))
        
        orphans = fk_values - valid_refs
        
        repairs = {"orphans_found": len(orphans), "repaired": 0, "strategy": strategy}
        
        if not orphans or dry_run:
            return repairs
        
        if strategy == "create_placeholder":
            # Create placeholder records in reference collection
            for orphan_id in orphans:
                placeholder = {
                    ref_field: orphan_id,
                    "name": f"[Auto-created] {orphan_id}",
                    "contact_name": f"[Auto-created] {orphan_id}",
                    "contact_type": "customer",
                    "organization_id": organization_id or "default",
                    "source": "integrity_repair",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "is_placeholder": True,
                }
                
                await self.db[ref_collection].update_one(
                    {ref_field: orphan_id},
                    {"$setOnInsert": placeholder},
                    upsert=True
                )
                repairs["repaired"] += 1
        
        elif strategy == "nullify":
            # Set orphan references to null
            result = await self.db[collection].update_many(
                {
                    **filter_query,
                    fk_field: {"$in": list(orphans)}
                },
                {"$set": {fk_field: None}}
            )
            repairs["repaired"] = result.modified_count
        
        return repairs
    
    async def normalize_invoice_fields(self, organization_id: Optional[str] = None) -> Dict:
        """Normalize invoice fields from legacy format to standard format"""
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        updates_made = 0
        
        async for invoice in self.db.invoices.find(filter_query):
            updates = {}
            
            # Normalize field names
            if "total" in invoice and "grand_total" not in invoice:
                updates["grand_total"] = invoice["total"]
            
            if "balance" in invoice and "balance_due" not in invoice:
                updates["balance_due"] = invoice["balance"]
            
            if "sub_total" in invoice and "subtotal" not in invoice:
                updates["subtotal"] = invoice["sub_total"]
            
            if "date" in invoice and "invoice_date" not in invoice:
                updates["invoice_date"] = invoice["date"]
            
            # Ensure numeric fields
            for field in ["grand_total", "balance_due", "subtotal", "total_tax"]:
                if field in invoice and invoice[field] is None:
                    updates[field] = 0.0
            
            # Ensure status
            if "status" not in invoice or not invoice["status"]:
                updates["status"] = "draft"
            
            # Ensure currency
            if "currency_code" not in invoice:
                updates["currency_code"] = "INR"
            
            # Generate invoice_id if missing
            if "invoice_id" not in invoice or not invoice["invoice_id"]:
                updates["invoice_id"] = f"inv_{uuid.uuid4().hex[:12]}"
            
            if updates:
                await self.db.invoices.update_one(
                    {"_id": invoice["_id"]},
                    {"$set": updates}
                )
                updates_made += 1
        
        return {"invoices_normalized": updates_made}
    
    async def normalize_estimate_fields(self, organization_id: Optional[str] = None) -> Dict:
        """Normalize estimate fields"""
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        updates_made = 0
        
        async for estimate in self.db.estimates.find(filter_query):
            updates = {}
            
            # Normalize field names
            if "estimate_date" in estimate and "date" not in estimate:
                updates["date"] = estimate["estimate_date"]
            
            if "grand_total" in estimate and "total" not in estimate:
                updates["total"] = estimate["grand_total"]
            
            if "sub_total" in estimate and "subtotal" not in estimate:
                updates["subtotal"] = estimate["sub_total"]
            
            # Generate estimate_id if missing
            if "estimate_id" not in estimate or not estimate["estimate_id"]:
                updates["estimate_id"] = f"est_{uuid.uuid4().hex[:12]}"
            
            # Ensure status
            if "status" not in estimate:
                updates["status"] = "draft"
            
            if updates:
                await self.db.estimates.update_one(
                    {"_id": estimate["_id"]},
                    {"$set": updates}
                )
                updates_made += 1
        
        return {"estimates_normalized": updates_made}
    
    async def sync_customer_references(self, organization_id: Optional[str] = None) -> Dict:
        """Synchronize customer references between contacts and local IDs"""
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        # Build customer ID mapping (legacy_contact_id -> local contact_id)
        customer_map = {}
        async for contact in self.db.contacts.find({}, {"contact_id": 1, "legacy_contact_id": 1}):
            zoho_id = contact.get("legacy_contact_id")
            local_id = contact.get("contact_id")
            if zoho_id and local_id:
                customer_map[zoho_id] = local_id
                customer_map[local_id] = local_id  # Also map local to local
        
        updates = {"invoices": 0, "estimates": 0, "payments": 0}
        
        # Update invoices
        async for invoice in self.db.invoices.find({
            **filter_query,
            "customer_id": {"$nin": list(customer_map.values())}
        }):
            cust_id = invoice.get("customer_id")
            if cust_id in customer_map:
                await self.db.invoices.update_one(
                    {"_id": invoice["_id"]},
                    {"$set": {"customer_id": customer_map[cust_id]}}
                )
                updates["invoices"] += 1
        
        # Update estimates
        async for estimate in self.db.estimates.find({
            **filter_query,
            "customer_id": {"$nin": list(customer_map.values())}
        }):
            cust_id = estimate.get("customer_id")
            if cust_id in customer_map:
                await self.db.estimates.update_one(
                    {"_id": estimate["_id"]},
                    {"$set": {"customer_id": customer_map[cust_id]}}
                )
                updates["estimates"] += 1
        
        return updates
    
    # ============== ZOHO PARITY ENHANCEMENTS ==============
    
    async def add_missing_zoho_fields(self, collection: str, organization_id: Optional[str] = None) -> Dict:
        """Add Zoho Books standard fields that are missing"""
        ZOHO_STANDARD_FIELDS = {
            "invoices": {
                "is_inclusive_tax": False,
                "is_discount_before_tax": True,
                "discount_type": "entity_level",
                "shipping_charge": 0.0,
                "adjustment": 0.0,
                "adjustment_description": "",
                "payment_terms": 0,
                "payment_terms_label": "Due on Receipt",
                "template_id": None,
                "template_name": None,
                "payment_expected_date": None,
                "payment_reminder_enabled": False,
                "payment_made": 0.0,
                "credits_applied": 0.0,
                "taxes": [],
                "contact_persons": [],
                "custom_fields": [],
                "documents": [],
            },
            "estimates": {
                "is_inclusive_tax": False,
                "is_discount_before_tax": True,
                "discount_type": "entity_level",
                "shipping_charge": 0.0,
                "adjustment": 0.0,
                "template_id": None,
                "template_name": None,
                "taxes": [],
                "contact_persons": [],
                "custom_fields": [],
            },
            "contacts": {
                "payment_terms": 0,
                "payment_terms_label": "Due on Receipt",
                "credit_limit": 0.0,
                "outstanding_receivable_amount": 0.0,
                "outstanding_payable_amount": 0.0,
                "unused_credits_receivable_amount": 0.0,
                "unused_credits_payable_amount": 0.0,
                "language_code": "en",
                "is_portal_enabled": False,
                "custom_fields": [],
                "contact_persons": [],
                "notes": "",
            },
            "items": {
                "unit": "pcs",
                "item_type": "sales",
                "product_type": "goods",
                "is_taxable": True,
                "tax_exemption_id": None,
                "tax_exemption_code": None,
                "account_id": None,
                "account_name": None,
                "purchase_account_id": None,
                "purchase_account_name": None,
                "inventory_account_id": None,
                "inventory_account_name": None,
                "reorder_level": 0,
                "initial_stock": 0,
                "initial_stock_rate": 0.0,
                "vendor_id": None,
                "vendor_name": None,
                "custom_fields": [],
                "image_document_id": None,
            },
            "bills": {
                "payment_terms": 0,
                "payment_terms_label": "Due on Receipt",
                "is_inclusive_tax": False,
                "shipping_charge": 0.0,
                "adjustment": 0.0,
                "payment_made": 0.0,
                "credits_applied": 0.0,
                "taxes": [],
                "custom_fields": [],
                "documents": [],
            },
        }
        
        zoho_fields = ZOHO_STANDARD_FIELDS.get(collection, {})
        if not zoho_fields:
            return {"message": f"No Zoho standard fields defined for {collection}"}
        
        filter_query = {}
        if organization_id:
            filter_query["organization_id"] = organization_id
        
        updates_made = 0
        
        async for doc in self.db[collection].find(filter_query):
            updates = {}
            
            for field, default_value in zoho_fields.items():
                if field not in doc:
                    updates[field] = default_value
            
            if updates:
                await self.db[collection].update_one(
                    {"_id": doc["_id"]},
                    {"$set": updates}
                )
                updates_made += 1
        
        return {
            "collection": collection,
            "documents_updated": updates_made,
            "fields_added": list(zoho_fields.keys())
        }
