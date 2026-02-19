"""
Battwheels OS - Ticket-Estimate Integration Service
Links service tickets with estimates for seamless job card workflow

Key features:
- Auto-create estimate on technician assignment
- Single source of truth (one estimate per ticket)
- Optimistic concurrency control
- Locking mechanism for approved/converted estimates
- Server-side total calculations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import uuid
import logging

logger = logging.getLogger(__name__)


# ==================== DATA MODELS ====================

class LineItemType:
    PART = "part"
    LABOUR = "labour"
    FEE = "fee"


class EstimateLineItemCreate(BaseModel):
    """Line item creation model"""
    type: str = Field(default=LineItemType.PART, pattern="^(part|labour|fee)$")
    item_id: Optional[str] = None  # Parts catalog ID (nullable for labour/fees)
    name: str = Field(..., min_length=1)
    description: str = ""
    qty: float = Field(default=1, gt=0)
    unit_price: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)
    tax_id: Optional[str] = None
    tax_rate: float = Field(default=0, ge=0, le=100)
    hsn_code: str = ""
    unit: str = "pcs"


class EstimateLineItemUpdate(BaseModel):
    """Line item update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    qty: Optional[float] = None
    unit_price: Optional[float] = None
    discount: Optional[float] = None
    tax_id: Optional[str] = None
    tax_rate: Optional[float] = None


class EstimateStatus:
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONVERTED = "converted"
    VOID = "void"


class ZohoSyncStatus:
    NOT_SYNCED = "not_synced"
    QUEUED = "queued"
    SYNCED = "synced"
    ERROR = "error"


# ==================== TICKET ESTIMATE SERVICE ====================

class TicketEstimateService:
    """
    Service for managing estimates linked to service tickets
    
    Single source of truth: Job Card and Estimates module share the same record
    """
    
    def __init__(self, db):
        self.db = db
        self.estimates = db["ticket_estimates"]  # New collection for ticket-linked estimates
        self.estimate_line_items = db["ticket_estimate_line_items"]
        self.estimate_history = db["ticket_estimate_history"]
        logger.info("TicketEstimateService initialized")
    
    # ==================== ESTIMATE CREATION ====================
    
    async def ensure_estimate(
        self,
        ticket_id: str,
        organization_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Ensure an estimate exists for a ticket.
        Creates one if missing, returns existing if present.
        
        Idempotent: Multiple calls return the same estimate.
        """
        # Check if estimate already exists
        existing = await self.estimates.find_one(
            {"ticket_id": ticket_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if existing:
            # Fetch line items
            line_items = await self.estimate_line_items.find(
                {"estimate_id": existing["estimate_id"]},
                {"_id": 0}
            ).sort("sort_index", 1).to_list(1000)
            existing["line_items"] = line_items
            return existing
        
        # Get ticket data to copy context
        ticket = await self.db.tickets.find_one(
            {"ticket_id": ticket_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Generate estimate ID and number
        estimate_id = f"est_{uuid.uuid4().hex[:12]}"
        estimate_number = await self._get_next_estimate_number(organization_id)
        now = datetime.now(timezone.utc)
        
        # Create estimate document
        estimate_doc = {
            "estimate_id": estimate_id,
            "estimate_number": estimate_number,
            "organization_id": organization_id,
            
            # Ticket linkage (unique per ticket)
            "ticket_id": ticket_id,
            "work_order_id": None,
            
            # Copied from ticket
            "customer_id": ticket.get("customer_id"),
            "customer_name": ticket.get("customer_name"),
            "customer_email": ticket.get("customer_email"),
            "contact_number": ticket.get("contact_number"),
            "vehicle_id": ticket.get("vehicle_id"),
            "vehicle_number": ticket.get("vehicle_number"),
            "vehicle_make": ticket.get("vehicle_make"),
            "vehicle_model": ticket.get("vehicle_model"),
            "assigned_technician_id": ticket.get("assigned_technician_id"),
            "assigned_technician_name": ticket.get("assigned_technician_name"),
            
            # Status
            "status": EstimateStatus.DRAFT,
            
            # Money fields (computed server-side)
            "subtotal": 0.0,
            "tax_total": 0.0,
            "discount_total": 0.0,
            "grand_total": 0.0,
            "currency": "INR",
            
            # Notes
            "notes": "",
            "terms": "",
            "subject": f"Estimate for Ticket #{ticket_id}",
            
            # Locking
            "lock_reason": None,
            "locked_at": None,
            "locked_by": None,
            
            # Zoho sync (Phase 4 - not used yet)
            "zoho_estimate_id": None,
            "zoho_sync_status": ZohoSyncStatus.NOT_SYNCED,
            "zoho_last_synced_at": None,
            
            # Optimistic concurrency
            "version": 1,
            
            # Timestamps
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": user_id,
            "created_by_name": user_name,
        }
        
        await self.estimates.insert_one(estimate_doc)
        
        # Log history
        await self._log_history(
            estimate_id, "created", 
            f"Estimate created from ticket {ticket_id}",
            user_id, user_name
        )
        
        # Return without _id
        result = await self.estimates.find_one(
            {"estimate_id": estimate_id},
            {"_id": 0}
        )
        result["line_items"] = []
        
        logger.info(f"Created estimate {estimate_id} for ticket {ticket_id}")
        return result
    
    # ==================== GET ESTIMATE ====================
    
    async def get_estimate_by_ticket(
        self,
        ticket_id: str,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get estimate for a ticket with line items"""
        estimate = await self.estimates.find_one(
            {"ticket_id": ticket_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not estimate:
            return None
        
        # Fetch line items
        line_items = await self.estimate_line_items.find(
            {"estimate_id": estimate["estimate_id"]},
            {"_id": 0}
        ).sort("sort_index", 1).to_list(1000)
        
        estimate["line_items"] = line_items
        return estimate
    
    async def get_estimate_by_id(
        self,
        estimate_id: str,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get estimate by ID with line items"""
        estimate = await self.estimates.find_one(
            {"estimate_id": estimate_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not estimate:
            return None
        
        # Fetch line items
        line_items = await self.estimate_line_items.find(
            {"estimate_id": estimate_id},
            {"_id": 0}
        ).sort("sort_index", 1).to_list(1000)
        
        estimate["line_items"] = line_items
        return estimate
    
    # ==================== LINE ITEM CRUD ====================
    
    async def add_line_item(
        self,
        estimate_id: str,
        organization_id: str,
        item_data: EstimateLineItemCreate,
        user_id: str,
        user_name: str,
        version: int
    ) -> Dict[str, Any]:
        """Add a line item to estimate with inventory tracking for parts"""
        # Validate estimate and check lock (raises on error)
        estimate = await self._get_and_validate_estimate(
            estimate_id, organization_id, version
        )
        
        line_item_id = f"eli_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        # Get current max sort_index
        max_item = await self.estimate_line_items.find_one(
            {"estimate_id": estimate_id},
            sort=[("sort_index", -1)]
        )
        sort_index = (max_item.get("sort_index", 0) + 1) if max_item else 1
        
        # Calculate line total
        line_total = self._calculate_line_total(
            item_data.qty, item_data.unit_price, item_data.discount, item_data.tax_rate
        )
        
        # Get inventory info if this is a part with an item_id
        inventory_reserved = False
        inventory_item = None
        if item_data.type == "part" and item_data.item_id:
            # Check if item exists in inventory
            inventory_item = await self.db.items_enhanced.find_one(
                {"item_id": item_data.item_id, "organization_id": organization_id},
                {"_id": 0}
            )
            
            # Track inventory allocation for approved estimates
            if inventory_item and estimate.get("status") == "approved":
                # Reserve inventory when estimate is approved
                inventory_reserved = True
                await self._reserve_inventory(
                    item_id=item_data.item_id,
                    quantity=item_data.qty,
                    estimate_id=estimate_id,
                    organization_id=organization_id,
                    user_id=user_id
                )
        
        line_item_doc = {
            "line_item_id": line_item_id,
            "estimate_id": estimate_id,
            "type": item_data.type,
            "item_id": item_data.item_id,
            "name": item_data.name,
            "description": item_data.description,
            "qty": item_data.qty,
            "unit": item_data.unit,
            "unit_price": item_data.unit_price,
            "discount": item_data.discount,
            "tax_id": item_data.tax_id,
            "tax_rate": item_data.tax_rate,
            "hsn_code": item_data.hsn_code,
            "line_total": line_total,
            "sort_index": sort_index,
            "inventory_reserved": inventory_reserved,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        await self.estimate_line_items.insert_one(line_item_doc)
        
        # Recalculate totals and increment version
        await self._recalculate_totals(estimate_id)
        await self._increment_version(estimate_id)
        
        # Log history
        await self._log_history(
            estimate_id, "line_item_added",
            f"Added {item_data.type}: {item_data.name}" + (" (inventory reserved)" if inventory_reserved else ""),
            user_id, user_name
        )
        
        # Return updated estimate
        return await self.get_estimate_by_id(estimate_id, organization_id)
    
    async def update_line_item(
        self,
        estimate_id: str,
        line_item_id: str,
        organization_id: str,
        item_data: EstimateLineItemUpdate,
        user_id: str,
        user_name: str,
        version: int
    ) -> Dict[str, Any]:
        """Update a line item"""
        # Validate estimate and check lock (raises on error)
        await self._get_and_validate_estimate(
            estimate_id, organization_id, version
        )
        
        # Get existing line item
        existing = await self.estimate_line_items.find_one(
            {"line_item_id": line_item_id, "estimate_id": estimate_id}
        )
        if not existing:
            raise ValueError(f"Line item {line_item_id} not found")
        
        # Build update dict
        update_dict = {k: v for k, v in item_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Recalculate line total
        qty = update_dict.get("qty", existing.get("qty", 1))
        unit_price = update_dict.get("unit_price", existing.get("unit_price", 0))
        discount = update_dict.get("discount", existing.get("discount", 0))
        tax_rate = update_dict.get("tax_rate", existing.get("tax_rate", 0))
        update_dict["line_total"] = self._calculate_line_total(qty, unit_price, discount, tax_rate)
        
        await self.estimate_line_items.update_one(
            {"line_item_id": line_item_id},
            {"$set": update_dict}
        )
        
        # Recalculate totals and increment version
        await self._recalculate_totals(estimate_id)
        await self._increment_version(estimate_id)
        
        # Log history
        await self._log_history(
            estimate_id, "line_item_updated",
            f"Updated line item: {existing.get('name')}",
            user_id, user_name
        )
        
        return await self.get_estimate_by_id(estimate_id, organization_id)
    
    async def delete_line_item(
        self,
        estimate_id: str,
        line_item_id: str,
        organization_id: str,
        user_id: str,
        user_name: str,
        version: int
    ) -> Dict[str, Any]:
        """Delete a line item"""
        # Validate estimate and check lock (raises on error)
        await self._get_and_validate_estimate(
            estimate_id, organization_id, version
        )
        
        # Get line item for logging
        existing = await self.estimate_line_items.find_one(
            {"line_item_id": line_item_id, "estimate_id": estimate_id}
        )
        if not existing:
            raise ValueError(f"Line item {line_item_id} not found")
        
        await self.estimate_line_items.delete_one(
            {"line_item_id": line_item_id, "estimate_id": estimate_id}
        )
        
        # Recalculate totals and increment version
        await self._recalculate_totals(estimate_id)
        await self._increment_version(estimate_id)
        
        # Log history
        await self._log_history(
            estimate_id, "line_item_deleted",
            f"Removed line item: {existing.get('name')}",
            user_id, user_name
        )
        
        return await self.get_estimate_by_id(estimate_id, organization_id)
    
    # ==================== STATUS OPERATIONS ====================
    
    async def approve_estimate(
        self,
        estimate_id: str,
        organization_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Approve an estimate"""
        estimate = await self.estimates.find_one(
            {"estimate_id": estimate_id, "organization_id": organization_id}
        )
        
        if not estimate:
            raise ValueError(f"Estimate {estimate_id} not found")
        
        if estimate.get("locked_at"):
            raise ValueError("Cannot approve locked estimate")
        
        now = datetime.now(timezone.utc)
        await self.estimates.update_one(
            {"estimate_id": estimate_id},
            {
                "$set": {
                    "status": EstimateStatus.APPROVED,
                    "approved_at": now.isoformat(),
                    "approved_by": user_id,
                    "approved_by_name": user_name,
                    "updated_at": now.isoformat()
                },
                "$inc": {"version": 1}
            }
        )
        
        # Log history
        await self._log_history(
            estimate_id, "approved",
            "Estimate approved",
            user_id, user_name
        )
        
        # Update ticket status if needed
        if estimate.get("ticket_id"):
            await self.db.tickets.update_one(
                {"ticket_id": estimate["ticket_id"]},
                {
                    "$set": {
                        "status": "estimate_approved",
                        "updated_at": now.isoformat()
                    },
                    "$push": {
                        "status_history": {
                            "status": "estimate_approved",
                            "timestamp": now.isoformat(),
                            "updated_by": user_name
                        }
                    }
                }
            )
        
        return await self.get_estimate_by_id(estimate_id, organization_id)
    
    async def send_estimate(
        self,
        estimate_id: str,
        organization_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Mark estimate as sent"""
        estimate = await self.estimates.find_one(
            {"estimate_id": estimate_id, "organization_id": organization_id}
        )
        
        if not estimate:
            raise ValueError(f"Estimate {estimate_id} not found")
        
        if estimate.get("locked_at"):
            raise ValueError("Cannot send locked estimate")
        
        now = datetime.now(timezone.utc)
        await self.estimates.update_one(
            {"estimate_id": estimate_id},
            {
                "$set": {
                    "status": EstimateStatus.SENT,
                    "sent_at": now.isoformat(),
                    "sent_by": user_id,
                    "updated_at": now.isoformat()
                },
                "$inc": {"version": 1}
            }
        )
        
        # Log history
        await self._log_history(
            estimate_id, "sent",
            "Estimate sent to customer",
            user_id, user_name
        )
        
        # Update ticket status
        if estimate.get("ticket_id"):
            await self.db.tickets.update_one(
                {"ticket_id": estimate["ticket_id"]},
                {
                    "$set": {
                        "status": "estimate_shared",
                        "updated_at": now.isoformat()
                    },
                    "$push": {
                        "status_history": {
                            "status": "estimate_shared",
                            "timestamp": now.isoformat(),
                            "updated_by": user_name
                        }
                    }
                }
            )
        
        return await self.get_estimate_by_id(estimate_id, organization_id)
    
    async def lock_estimate(
        self,
        estimate_id: str,
        organization_id: str,
        reason: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Lock an estimate to prevent further edits"""
        estimate = await self.estimates.find_one(
            {"estimate_id": estimate_id, "organization_id": organization_id}
        )
        
        if not estimate:
            raise ValueError(f"Estimate {estimate_id} not found")
        
        if estimate.get("locked_at"):
            raise ValueError("Estimate is already locked")
        
        now = datetime.now(timezone.utc)
        await self.estimates.update_one(
            {"estimate_id": estimate_id},
            {
                "$set": {
                    "lock_reason": reason,
                    "locked_at": now.isoformat(),
                    "locked_by": user_id,
                    "locked_by_name": user_name,
                    "updated_at": now.isoformat()
                },
                "$inc": {"version": 1}
            }
        )
        
        # Log history
        await self._log_history(
            estimate_id, "locked",
            f"Estimate locked: {reason}",
            user_id, user_name
        )
        
        return await self.get_estimate_by_id(estimate_id, organization_id)
    
    async def unlock_estimate(
        self,
        estimate_id: str,
        organization_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Unlock an estimate to allow further edits (admin only)"""
        estimate = await self.estimates.find_one(
            {"estimate_id": estimate_id, "organization_id": organization_id}
        )
        
        if not estimate:
            raise ValueError(f"Estimate {estimate_id} not found")
        
        if not estimate.get("locked_at"):
            raise ValueError("Estimate is not locked")
        
        now = datetime.now(timezone.utc)
        await self.estimates.update_one(
            {"estimate_id": estimate_id},
            {
                "$set": {
                    "lock_reason": None,
                    "locked_at": None,
                    "locked_by": None,
                    "locked_by_name": None,
                    "updated_at": now.isoformat()
                },
                "$inc": {"version": 1}
            }
        )
        
        # Log history
        await self._log_history(
            estimate_id, "unlocked",
            "Estimate unlocked for editing",
            user_id, user_name
        )
        
        return await self.get_estimate_by_id(estimate_id, organization_id)
    
    # ==================== CONVERSION TO INVOICE ====================
    
    async def convert_to_invoice(
        self,
        estimate_id: str,
        organization_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Convert an approved estimate to an invoice.
        Only approved estimates can be converted.
        """
        estimate = await self.estimates.find_one(
            {"estimate_id": estimate_id, "organization_id": organization_id}
        )
        
        if not estimate:
            raise ValueError(f"Estimate {estimate_id} not found")
        
        if estimate.get("status") != EstimateStatus.APPROVED:
            raise ValueError("Only approved estimates can be converted to invoices")
        
        if estimate.get("converted_to_invoice"):
            raise ValueError("Estimate has already been converted to an invoice")
        
        # Get line items
        line_items = await self.estimate_line_items.find(
            {"estimate_id": estimate_id}
        ).to_list(1000)
        
        now = datetime.now(timezone.utc)
        
        # Generate invoice number
        invoice_number = await self._get_next_invoice_number(organization_id)
        invoice_id = f"inv_{uuid.uuid4().hex[:12]}"
        
        # Create invoice document
        invoice_doc = {
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "organization_id": organization_id,
            "source": "ticket_estimate",
            "source_estimate_id": estimate_id,
            "ticket_id": estimate.get("ticket_id"),
            
            # Customer info
            "customer_id": estimate.get("customer_id"),
            "customer_name": estimate.get("customer_name"),
            "customer_email": estimate.get("customer_email"),
            "contact_number": estimate.get("contact_number"),
            
            # Vehicle info
            "vehicle_id": estimate.get("vehicle_id"),
            "vehicle_number": estimate.get("vehicle_number"),
            "vehicle_make": estimate.get("vehicle_make"),
            "vehicle_model": estimate.get("vehicle_model"),
            
            # Line items
            "line_items": [{
                "line_item_id": item.get("line_item_id"),
                "type": item.get("type"),
                "item_id": item.get("item_id"),
                "name": item.get("name"),
                "description": item.get("description"),
                "qty": item.get("qty"),
                "unit": item.get("unit"),
                "unit_price": item.get("unit_price"),
                "discount": item.get("discount", 0),
                "tax_rate": item.get("tax_rate", 0),
                "hsn_code": item.get("hsn_code", ""),
                "line_total": item.get("line_total", 0),
            } for item in line_items],
            
            # Totals
            "subtotal": estimate.get("subtotal", 0),
            "tax_total": estimate.get("tax_total", 0),
            "discount_total": estimate.get("discount_total", 0),
            "grand_total": estimate.get("grand_total", 0),
            "currency": estimate.get("currency", "INR"),
            
            # Status
            "status": "draft",
            "payment_status": "unpaid",
            "balance_due": estimate.get("grand_total", 0),
            
            # Dates
            "invoice_date": now.strftime("%Y-%m-%d"),
            "due_date": (now.replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%Y-%m-%d"),
            
            # Metadata
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": user_id,
            "created_by_name": user_name,
        }
        
        await self.db.ticket_invoices.insert_one(invoice_doc)
        
        # Update estimate
        await self.estimates.update_one(
            {"estimate_id": estimate_id},
            {
                "$set": {
                    "status": EstimateStatus.CONVERTED,
                    "converted_to_invoice": invoice_id,
                    "converted_at": now.isoformat(),
                    "converted_by": user_id,
                    "updated_at": now.isoformat()
                },
                "$inc": {"version": 1}
            }
        )
        
        # Log history
        await self._log_history(
            estimate_id, "converted",
            f"Converted to invoice {invoice_number}",
            user_id, user_name
        )
        
        # Update ticket status
        if estimate.get("ticket_id"):
            await self.db.tickets.update_one(
                {"ticket_id": estimate["ticket_id"]},
                {
                    "$set": {
                        "status": "invoiced",
                        "invoice_id": invoice_id,
                        "updated_at": now.isoformat()
                    },
                    "$push": {
                        "status_history": {
                            "status": "invoiced",
                            "timestamp": now.isoformat(),
                            "updated_by": user_name
                        }
                    }
                }
            )
        
        # Return invoice document (without _id)
        invoice_doc.pop("_id", None)
        return {
            "invoice": invoice_doc,
            "estimate": await self.get_estimate_by_id(estimate_id, organization_id)
        }
    
    async def _get_next_invoice_number(self, organization_id: str) -> str:
        """Generate next invoice number for organization"""
        settings = await self.db.ticket_estimate_settings.find_one(
            {"organization_id": organization_id, "type": "invoice_numbering"}
        )
        
        if not settings:
            settings = {
                "organization_id": organization_id,
                "type": "invoice_numbering",
                "prefix": "TKT-INV-",
                "next_number": 1,
                "padding": 5
            }
            await self.db.ticket_estimate_settings.insert_one(settings)
        
        number = str(settings["next_number"]).zfill(settings.get("padding", 5))
        invoice_number = f"{settings.get('prefix', 'TKT-INV-')}{number}"
        
        await self.db.ticket_estimate_settings.update_one(
            {"organization_id": organization_id, "type": "invoice_numbering"},
            {"$inc": {"next_number": 1}}
        )
        
        return invoice_number
    
    # ==================== HELPER METHODS ====================
    
    async def _get_next_estimate_number(self, organization_id: str) -> str:
        """Generate next estimate number for organization"""
        # Get settings or create default
        settings = await self.db.ticket_estimate_settings.find_one(
            {"organization_id": organization_id, "type": "numbering"}
        )
        
        if not settings:
            settings = {
                "organization_id": organization_id,
                "type": "numbering",
                "prefix": "TKT-EST-",
                "next_number": 1,
                "padding": 5
            }
            await self.db.ticket_estimate_settings.insert_one(settings)
        
        number = str(settings["next_number"]).zfill(settings.get("padding", 5))
        estimate_number = f"{settings.get('prefix', 'TKT-EST-')}{number}"
        
        # Increment for next time
        await self.db.ticket_estimate_settings.update_one(
            {"organization_id": organization_id, "type": "numbering"},
            {"$inc": {"next_number": 1}}
        )
        
        return estimate_number
    
    async def _get_and_validate_estimate(
        self,
        estimate_id: str,
        organization_id: str,
        version: int
    ) -> Dict[str, Any]:
        """Get estimate and validate for update"""
        estimate = await self.estimates.find_one(
            {"estimate_id": estimate_id, "organization_id": organization_id},
            {"_id": 0}  # Exclude MongoDB _id to avoid JSON serialization issues
        )
        
        if not estimate:
            raise ValueError(f"Estimate {estimate_id} not found")
        
        # Check if locked
        if estimate.get("locked_at"):
            raise LockedEstimateError(
                f"Estimate is locked: {estimate.get('lock_reason', 'No reason provided')}",
                estimate.get("locked_at"),
                estimate.get("locked_by_name")
            )
        
        # Check version for concurrency
        if estimate.get("version", 1) != version:
            raise ConcurrencyError(
                f"Version mismatch: expected {version}, got {estimate.get('version')}",
                estimate
            )
        
        return estimate
    
    def _calculate_line_total(
        self,
        qty: float,
        unit_price: float,
        discount: float,
        tax_rate: float
    ) -> float:
        """Calculate line item total with tax"""
        subtotal = qty * unit_price
        after_discount = subtotal - discount
        tax = after_discount * (tax_rate / 100)
        return round(after_discount + tax, 2)
    
    async def _recalculate_totals(self, estimate_id: str):
        """Recalculate estimate totals from line items"""
        line_items = await self.estimate_line_items.find(
            {"estimate_id": estimate_id}
        ).to_list(1000)
        
        subtotal = 0.0
        tax_total = 0.0
        discount_total = 0.0
        
        for item in line_items:
            qty = item.get("qty", 1)
            unit_price = item.get("unit_price", 0)
            discount = item.get("discount", 0)
            tax_rate = item.get("tax_rate", 0)
            
            item_subtotal = qty * unit_price
            item_tax = (item_subtotal - discount) * (tax_rate / 100)
            
            subtotal += item_subtotal
            discount_total += discount
            tax_total += item_tax
        
        grand_total = subtotal - discount_total + tax_total
        
        await self.estimates.update_one(
            {"estimate_id": estimate_id},
            {
                "$set": {
                    "subtotal": round(subtotal, 2),
                    "tax_total": round(tax_total, 2),
                    "discount_total": round(discount_total, 2),
                    "grand_total": round(grand_total, 2),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    async def _increment_version(self, estimate_id: str) -> int:
        """Increment estimate version and return new version"""
        result = await self.estimates.find_one_and_update(
            {"estimate_id": estimate_id},
            {"$inc": {"version": 1}},
            return_document=True
        )
        return result.get("version", 1)
    
    async def _log_history(
        self,
        estimate_id: str,
        action: str,
        description: str,
        user_id: str,
        user_name: str
    ):
        """Log estimate history entry"""
        await self.estimate_history.insert_one({
            "history_id": f"eh_{uuid.uuid4().hex[:12]}",
            "estimate_id": estimate_id,
            "action": action,
            "description": description,
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # ==================== INVENTORY TRACKING ====================
    
    async def _reserve_inventory(
        self,
        item_id: str,
        quantity: float,
        estimate_id: str,
        organization_id: str,
        user_id: str
    ):
        """Reserve inventory for an estimate line item"""
        now = datetime.now(timezone.utc)
        
        # Get the item's stock location (use primary warehouse)
        warehouse = await self.db.warehouses.find_one(
            {"organization_id": organization_id, "is_primary": True}
        )
        warehouse_id = warehouse["warehouse_id"] if warehouse else "default"
        
        # Update stock location - increase reserved_stock
        await self.db.item_stock_locations.update_one(
            {"item_id": item_id, "warehouse_id": warehouse_id},
            {
                "$inc": {"reserved_stock": quantity},
                "$set": {"updated_time": now.isoformat()}
            },
            upsert=True
        )
        
        # Log inventory allocation
        await self.db.inventory_allocations.insert_one({
            "allocation_id": f"alloc_{uuid.uuid4().hex[:12]}",
            "item_id": item_id,
            "estimate_id": estimate_id,
            "organization_id": organization_id,
            "quantity": quantity,
            "warehouse_id": warehouse_id,
            "status": "reserved",
            "created_at": now.isoformat(),
            "created_by": user_id
        })
        
        logger.info(f"Reserved {quantity} units of item {item_id} for estimate {estimate_id}")
    
    async def _release_inventory(
        self,
        item_id: str,
        quantity: float,
        estimate_id: str,
        organization_id: str,
        user_id: str
    ):
        """Release reserved inventory when line item is removed"""
        now = datetime.now(timezone.utc)
        
        # Find the allocation
        allocation = await self.db.inventory_allocations.find_one({
            "item_id": item_id,
            "estimate_id": estimate_id,
            "status": "reserved"
        })
        
        if allocation:
            warehouse_id = allocation.get("warehouse_id", "default")
            
            # Update stock location - decrease reserved_stock
            await self.db.item_stock_locations.update_one(
                {"item_id": item_id, "warehouse_id": warehouse_id},
                {
                    "$inc": {"reserved_stock": -quantity},
                    "$set": {"updated_time": now.isoformat()}
                }
            )
            
            # Update allocation status
            await self.db.inventory_allocations.update_one(
                {"allocation_id": allocation["allocation_id"]},
                {"$set": {"status": "released", "released_at": now.isoformat()}}
            )
            
            logger.info(f"Released {quantity} units of item {item_id} from estimate {estimate_id}")
    
    async def _consume_inventory(
        self,
        item_id: str,
        quantity: float,
        estimate_id: str,
        organization_id: str,
        user_id: str
    ):
        """Consume reserved inventory when estimate is converted to invoice"""
        now = datetime.now(timezone.utc)
        
        # Find the allocation
        allocation = await self.db.inventory_allocations.find_one({
            "item_id": item_id,
            "estimate_id": estimate_id,
            "status": "reserved"
        })
        
        if allocation:
            warehouse_id = allocation.get("warehouse_id", "default")
            
            # Update stock location - decrease both available and reserved
            await self.db.item_stock_locations.update_one(
                {"item_id": item_id, "warehouse_id": warehouse_id},
                {
                    "$inc": {
                        "available_stock": -quantity,
                        "reserved_stock": -quantity
                    },
                    "$set": {"updated_time": now.isoformat()}
                }
            )
            
            # Update allocation status
            await self.db.inventory_allocations.update_one(
                {"allocation_id": allocation["allocation_id"]},
                {"$set": {"status": "consumed", "consumed_at": now.isoformat()}}
            )
            
            # Log inventory history
            await self.db.inventory_history.insert_one({
                "history_id": f"hist_{uuid.uuid4().hex[:12]}",
                "item_id": item_id,
                "warehouse_id": warehouse_id,
                "action": "consumed_for_estimate",
                "quantity_change": -quantity,
                "reason": f"Consumed for estimate {estimate_id}",
                "user_id": user_id,
                "timestamp": now.isoformat()
            })
            
            logger.info(f"Consumed {quantity} units of item {item_id} for estimate {estimate_id}")


# ==================== CUSTOM EXCEPTIONS ====================

class LockedEstimateError(Exception):
    """Raised when trying to modify a locked estimate"""
    def __init__(self, message: str, locked_at: str, locked_by: str):
        super().__init__(message)
        self.locked_at = locked_at
        self.locked_by = locked_by


class ConcurrencyError(Exception):
    """Raised on version mismatch"""
    def __init__(self, message: str, current_estimate: dict):
        super().__init__(message)
        self.current_estimate = current_estimate


# ==================== SERVICE INSTANCE ====================

_service: Optional[TicketEstimateService] = None


def init_ticket_estimate_service(database) -> TicketEstimateService:
    """Initialize service with database"""
    global _service
    _service = TicketEstimateService(database)
    return _service


def get_ticket_estimate_service() -> TicketEstimateService:
    """Get the service instance"""
    if _service is None:
        raise RuntimeError("TicketEstimateService not initialized")
    return _service
