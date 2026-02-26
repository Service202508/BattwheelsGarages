"""
Battwheels OS - Shared Helper Functions (extracted from server.py)
Ledger entries, number generators, etc.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

db = None

def init_helpers(database):
    global db
    db = database

async def create_ledger_entry(
    account_type: str,
    account_name: str,
    description: str,
    reference_type: str,
    reference_id: str,
    debit: float,
    credit: float,
    created_by: str,
    ticket_id: Optional[str] = None,
    vehicle_id: Optional[str] = None
):
    """Create an accounting ledger entry for audit trail"""
    entry = {
        "entry_id": f"led_{uuid.uuid4().hex[:12]}",
        "entry_date": datetime.now(timezone.utc).isoformat(),
        "account_type": account_type,
        "account_name": account_name,
        "description": description,
        "reference_type": reference_type,
        "reference_id": reference_id,
        "ticket_id": ticket_id,
        "vehicle_id": vehicle_id,
        "debit": debit,
        "credit": credit,
        "balance": debit - credit,
        "created_by": created_by
    }
    await db.ledger.insert_one(entry)
    return entry

async def generate_po_number(org_id: str = None):
    """Generate sequential PO number per organisation (atomic, race-condition safe)"""
    if org_id:
        result = await db.sequences.find_one_and_update(
            {"organization_id": org_id, "sequence_type": "PURCHASE_ORDER"},
            {"$inc": {"current_value": 1}},
            upsert=True,
            return_document=True
        )
        seq = result["current_value"]
        return f"PO-{datetime.now().strftime('%Y%m')}-{str(seq).zfill(4)}"
    # Fallback for legacy calls without org_id
    count = await db.purchase_orders.count_documents({"organization_id": {"$exists": False}})
    return f"PO-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

async def generate_invoice_number(org_id: str = None):
    """Generate sequential invoice number per organisation (atomic, race-condition safe)"""
    if org_id:
        result = await db.sequences.find_one_and_update(
            {"organization_id": org_id, "sequence_type": "INVOICE"},
            {"$inc": {"current_value": 1}},
            upsert=True,
            return_document=True
        )
        seq = result["current_value"]
        return f"INV-{datetime.now().strftime('%Y%m')}-{str(seq).zfill(4)}"
    # Fallback
    count = await db.invoices.count_documents({"organization_id": {"$exists": False}})
    return f"INV-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

async def generate_sales_number(org_id: str = None):
    """Generate sequential sales order number per organisation (atomic, race-condition safe)"""
    if org_id:
        result = await db.sequences.find_one_and_update(
            {"organization_id": org_id, "sequence_type": "SALES_ORDER"},
            {"$inc": {"current_value": 1}},
            upsert=True,
            return_document=True
        )
        seq = result["current_value"]
        return f"SO-{datetime.now().strftime('%Y%m')}-{str(seq).zfill(4)}"
    # Fallback
    count = await db.sales_orders.count_documents({"organization_id": {"$exists": False}})
    return f"SO-{datetime.now().strftime('%Y%m')}-{str(count + 1).zfill(4)}"

