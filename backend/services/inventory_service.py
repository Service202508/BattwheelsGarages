"""
Battwheels OS - Inventory Service
Business logic for inventory management with event emission

Handles:
- Inventory CRUD
- Stock allocations for tickets
- Low stock alerts
- Purchase order integration
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import logging

from events import get_dispatcher, EventType, EventPriority

logger = logging.getLogger(__name__)


class InventoryService:
    """Inventory management service with event emission"""
    
    def __init__(self, db):
        self.db = db
        self.dispatcher = get_dispatcher()
        logger.info("InventoryService initialized")
    
    async def create_item(
        self,
        name: str,
        sku: str,
        category: str,
        quantity: int,
        unit_price: float,
        reorder_level: int = 10,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """Create inventory item"""
        item_id = f"inv_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        item = {
            "item_id": item_id,
            "name": name,
            "sku": sku,
            "category": category,
            "quantity": quantity,
            "reserved_quantity": 0,
            "unit_price": unit_price,
            "reorder_level": reorder_level,
            "status": "active",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await self.db.inventory.insert_one(item)
        
        # Check low stock
        if quantity <= reorder_level:
            await self.dispatcher.emit(
                EventType.INVENTORY_LOW,
                {"item_id": item_id, "name": name, "quantity": quantity, "reorder_level": reorder_level},
                source="inventory_service",
                user_id=user_id
            )
        
        return await self.db.inventory.find_one({"item_id": item_id}, {"_id": 0})
    
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get inventory item"""
        return await self.db.inventory.find_one({"item_id": item_id}, {"_id": 0})
    
    async def list_items(
        self,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List inventory items"""
        query = {}
        if category:
            query["category"] = category
        if low_stock_only:
            query["$expr"] = {"$lte": ["$quantity", "$reorder_level"]}
        
        return await self.db.inventory.find(query, {"_id": 0}).to_list(limit)
    
    async def update_item(
        self,
        item_id: str,
        updates: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """Update inventory item"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.db.inventory.update_one(
            {"item_id": item_id},
            {"$set": updates}
        )
        
        item = await self.db.inventory.find_one({"item_id": item_id}, {"_id": 0})
        
        # Check low stock after update
        if item and item.get("quantity", 0) <= item.get("reorder_level", 10):
            await self.dispatcher.emit(
                EventType.INVENTORY_LOW,
                {"item_id": item_id, "name": item.get("name"), "quantity": item.get("quantity")},
                source="inventory_service",
                user_id=user_id
            )
        
        return item
    
    async def allocate_for_ticket(
        self,
        ticket_id: str,
        item_id: str,
        quantity: int,
        technician_id: str
    ) -> Dict[str, Any]:
        """Allocate inventory for a ticket"""
        item = await self.db.inventory.find_one({"item_id": item_id}, {"_id": 0})
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        available = item.get("quantity", 0) - item.get("reserved_quantity", 0)
        if quantity > available:
            raise ValueError(f"Insufficient stock. Available: {available}")
        
        allocation_id = f"alloc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        allocation = {
            "allocation_id": allocation_id,
            "ticket_id": ticket_id,
            "item_id": item_id,
            "item_name": item.get("name"),
            "quantity_allocated": quantity,
            "quantity_used": 0,
            "quantity_returned": 0,
            "unit_price": item.get("unit_price", 0),
            "status": "allocated",
            "allocated_by": technician_id,
            "allocated_at": now.isoformat(),
            "created_at": now.isoformat()
        }
        
        await self.db.allocations.insert_one(allocation)
        
        # Reserve inventory
        await self.db.inventory.update_one(
            {"item_id": item_id},
            {"$inc": {"reserved_quantity": quantity}}
        )
        
        # Emit event
        await self.dispatcher.emit(
            EventType.INVENTORY_ALLOCATED,
            {"allocation_id": allocation_id, "ticket_id": ticket_id, "item_id": item_id, "quantity": quantity},
            source="inventory_service",
            user_id=technician_id
        )
        
        return await self.db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
    
    async def use_allocation(
        self,
        allocation_id: str,
        quantity_used: int,
        user_id: str,
        job_card_id: str = None,
        job_card_number: str = None,
        organization_id: str = None
    ) -> Dict[str, Any]:
        """
        Mark allocated inventory as used.
        
        CRITICAL: This method now properly handles:
        1. Updates inventory quantity
        2. Creates stock_movement record for audit trail
        3. Posts COGS journal entry for accounting
        """
        allocation = await self.db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
        if not allocation:
            raise ValueError(f"Allocation {allocation_id} not found")
        
        available = allocation.get("quantity_allocated", 0) - allocation.get("quantity_used", 0)
        if quantity_used > available:
            raise ValueError(f"Cannot use more than allocated. Available: {available}")
        
        now = datetime.now(timezone.utc)
        
        # Get item details for cost calculation
        item = await self.db.inventory.find_one({"item_id": allocation["item_id"]}, {"_id": 0})
        if not item:
            raise ValueError(f"Item {allocation['item_id']} not found")
        
        # Calculate cost (using unit_price as average cost)
        unit_cost = item.get("unit_price", 0)
        total_cost = round(unit_cost * quantity_used, 2)
        
        # Get organization_id from allocation or parameter
        org_id = organization_id or allocation.get("organization_id")
        
        # 1. Update allocation record
        await self.db.allocations.update_one(
            {"allocation_id": allocation_id},
            {"$inc": {"quantity_used": quantity_used}, "$set": {"used_at": now.isoformat()}}
        )
        
        # 2. Update inventory quantity
        await self.db.inventory.update_one(
            {"item_id": allocation["item_id"]},
            {"$inc": {"quantity": -quantity_used, "reserved_quantity": -quantity_used}}
        )
        
        # 3. Create stock_movement record (CRITICAL for audit trail)
        movement_id = f"stm_{uuid.uuid4().hex[:12]}"
        stock_movement = {
            "movement_id": movement_id,
            "item_id": allocation["item_id"],
            "item_name": item.get("name", "Unknown"),
            "item_sku": item.get("sku", ""),
            "movement_type": "CONSUMPTION",
            "reference_type": "JOB_CARD" if job_card_id else "ALLOCATION",
            "reference_id": job_card_id or allocation.get("ticket_id", allocation_id),
            "reference_number": job_card_number or allocation.get("ticket_id", "N/A"),
            "movement_date": now.isoformat(),
            "quantity": -quantity_used,  # Negative for consumption
            "unit_cost": unit_cost,
            "total_value": total_cost,
            "organization_id": org_id,
            "created_by": user_id,
            "created_at": now.isoformat(),
            "notes": f"Parts consumed from allocation {allocation_id}"
        }
        await self.db.stock_movements.insert_one(stock_movement)
        logger.info(f"Stock movement created: {movement_id} - {quantity_used} x {item.get('name')} @ ₹{unit_cost} = ₹{total_cost}")
        
        # 4. Post COGS journal entry (CRITICAL for accounting)
        if total_cost > 0 and org_id:
            await self._post_cogs_entry(
                item_name=item.get("name", "Unknown"),
                quantity=quantity_used,
                unit_cost=unit_cost,
                total_cost=total_cost,
                job_card_id=job_card_id,
                job_card_number=job_card_number,
                organization_id=org_id,
                user_id=user_id,
                movement_id=movement_id
            )
        
        # 5. Emit event
        await self.dispatcher.emit(
            EventType.INVENTORY_USED,
            {
                "allocation_id": allocation_id,
                "item_id": allocation["item_id"],
                "quantity": quantity_used,
                "unit_cost": unit_cost,
                "total_cost": total_cost,
                "movement_id": movement_id
            },
            source="inventory_service",
            user_id=user_id
        )
        
        # 6. Check low stock
        updated_item = await self.db.inventory.find_one({"item_id": allocation["item_id"]}, {"_id": 0})
        if updated_item and updated_item.get("quantity", 0) <= updated_item.get("reorder_level", 10):
            await self.dispatcher.emit(
                EventType.INVENTORY_LOW,
                {"item_id": updated_item["item_id"], "name": updated_item.get("name"), "quantity": updated_item.get("quantity")},
                source="inventory_service",
                user_id=user_id,
                priority=EventPriority.HIGH
            )
        
        return await self.db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
    
    async def _post_cogs_entry(
        self,
        item_name: str,
        quantity: int,
        unit_cost: float,
        total_cost: float,
        job_card_id: str,
        job_card_number: str,
        organization_id: str,
        user_id: str,
        movement_id: str
    ):
        """
        Post COGS (Cost of Goods Sold) journal entry.
        
        Accounting impact:
        - DEBIT: Cost of Goods Sold (Expense) - increases expense
        - CREDIT: Inventory (Asset) - decreases asset
        """
        try:
            now = datetime.now(timezone.utc)
            entry_id = f"je_{uuid.uuid4().hex[:12]}"
            
            narration = (
                f"Parts consumed: {item_name} × {quantity} | "
                f"Job Card: {job_card_number or 'N/A'} | "
                f"Avg Cost: ₹{unit_cost}"
            )
            
            journal_entry = {
                "entry_id": entry_id,
                "entry_date": now.strftime("%Y-%m-%d"),
                "reference_number": movement_id,
                "description": narration,
                "organization_id": organization_id,
                "created_by": user_id,
                "entry_type": "COGS",
                "source_document_id": job_card_id or movement_id,
                "source_document_type": "JOB_CARD" if job_card_id else "STOCK_MOVEMENT",
                "is_posted": True,
                "is_reversed": False,
                "reversed_entry_id": "",
                "lines": [
                    {
                        "line_id": f"jel_{uuid.uuid4().hex[:8]}",
                        "account_id": "COST_OF_GOODS_SOLD",
                        "account_name": "Cost of Goods Sold",
                        "account_code": "5100",
                        "account_type": "Expense",
                        "debit_amount": total_cost,
                        "credit_amount": 0,
                        "description": f"COGS - {item_name}"
                    },
                    {
                        "line_id": f"jel_{uuid.uuid4().hex[:8]}",
                        "account_id": "INVENTORY",
                        "account_name": "Inventory",
                        "account_code": "1300",
                        "account_type": "Asset",
                        "debit_amount": 0,
                        "credit_amount": total_cost,
                        "description": f"Inventory reduction - {item_name}"
                    }
                ],
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            await self.db.journal_entries.insert_one(journal_entry)
            logger.info(f"COGS journal entry posted: {entry_id} for ₹{total_cost}")
            
        except Exception as e:
            logger.error(f"Failed to post COGS journal entry: {e}")
            # Don't fail the main operation - just log the error
    
    async def return_allocation(
        self,
        allocation_id: str,
        quantity_returned: int,
        user_id: str
    ) -> Dict[str, Any]:
        """Return unused allocated inventory"""
        allocation = await self.db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
        if not allocation:
            raise ValueError(f"Allocation {allocation_id} not found")
        
        unused = allocation.get("quantity_allocated", 0) - allocation.get("quantity_used", 0) - allocation.get("quantity_returned", 0)
        if quantity_returned > unused:
            raise ValueError(f"Cannot return more than unused. Unused: {unused}")
        
        await self.db.allocations.update_one(
            {"allocation_id": allocation_id},
            {"$inc": {"quantity_returned": quantity_returned}, "$set": {"returned_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Release reservation
        await self.db.inventory.update_one(
            {"item_id": allocation["item_id"]},
            {"$inc": {"reserved_quantity": -quantity_returned}}
        )
        
        # Emit event
        await self.dispatcher.emit(
            EventType.INVENTORY_RETURNED,
            {"allocation_id": allocation_id, "item_id": allocation["item_id"], "quantity": quantity_returned},
            source="inventory_service",
            user_id=user_id
        )
        
        return await self.db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})


# Service factory
_inventory_service: Optional[InventoryService] = None

def get_inventory_service() -> InventoryService:
    if _inventory_service is None:
        raise ValueError("InventoryService not initialized")
    return _inventory_service

def init_inventory_service(db) -> InventoryService:
    global _inventory_service
    _inventory_service = InventoryService(db)
    return _inventory_service
