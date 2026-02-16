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
        user_id: str
    ) -> Dict[str, Any]:
        """Mark allocated inventory as used"""
        allocation = await self.db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
        if not allocation:
            raise ValueError(f"Allocation {allocation_id} not found")
        
        available = allocation.get("quantity_allocated", 0) - allocation.get("quantity_used", 0)
        if quantity_used > available:
            raise ValueError(f"Cannot use more than allocated. Available: {available}")
        
        now = datetime.now(timezone.utc)
        
        await self.db.allocations.update_one(
            {"allocation_id": allocation_id},
            {"$inc": {"quantity_used": quantity_used}, "$set": {"used_at": now.isoformat()}}
        )
        
        # Update inventory
        await self.db.inventory.update_one(
            {"item_id": allocation["item_id"]},
            {"$inc": {"quantity": -quantity_used, "reserved_quantity": -quantity_used}}
        )
        
        # Emit event
        await self.dispatcher.emit(
            EventType.INVENTORY_USED,
            {"allocation_id": allocation_id, "item_id": allocation["item_id"], "quantity": quantity_used},
            source="inventory_service",
            user_id=user_id
        )
        
        # Check low stock
        item = await self.db.inventory.find_one({"item_id": allocation["item_id"]}, {"_id": 0})
        if item and item.get("quantity", 0) <= item.get("reorder_level", 10):
            await self.dispatcher.emit(
                EventType.INVENTORY_LOW,
                {"item_id": item["item_id"], "name": item.get("name"), "quantity": item.get("quantity")},
                source="inventory_service",
                user_id=user_id,
                priority=EventPriority.HIGH
            )
        
        return await self.db.allocations.find_one({"allocation_id": allocation_id}, {"_id": 0})
    
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
