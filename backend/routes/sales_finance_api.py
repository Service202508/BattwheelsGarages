from utils.helpers import create_ledger_entry, generate_po_number, generate_invoice_number, generate_sales_number
from utils.auth import require_auth, create_token, hash_password
"""
Battwheels OS - Sales, Invoices, Payments, Finance Routes (extracted from server.py)
Sales Orders, Invoices, Payments, Ledger, Accounting, Chart of Accounts
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from schemas.models import (
    SalesOrder, SalesOrderCreate, SalesOrderUpdate,
    Invoice, InvoiceCreate, InvoiceUpdate,
    Payment, PaymentCreate, LedgerEntry, AccountSummary, CostAllocation,
    ChartOfAccount,
)
from core.tenant.context import TenantContext, tenant_context_required

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sales & Finance Core"])
db = None

def init_router(database):
    global db
    db = database

@router.post("/sales-orders")
async def create_sales_order(data: SalesOrderCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_technician_or_admin(request)
    
    # Get ticket details
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get vehicle details
    vehicle = await db.vehicles.find_one({"vehicle_id": ticket["vehicle_id"]}, {"_id": 0})
    
    # Calculate totals
    services_total = sum(s.get("price", 0) * s.get("quantity", 1) for s in data.services)
    parts_total = sum(p.get("price", 0) * p.get("quantity", 1) for p in data.parts)
    subtotal = services_total + parts_total + data.labor_charges
    
    discount_amount = subtotal * (data.discount_percent / 100)
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * 0.18  # 18% GST
    total_amount = taxable_amount + tax_amount
    
    sales_number = await generate_sales_number(ctx.org_id)
    
    sales_order = SalesOrder(
        ticket_id=data.ticket_id,
        customer_id=ticket["customer_id"],
        customer_name=vehicle.get("owner_name", "") if vehicle else "",
        vehicle_id=ticket["vehicle_id"],
        services=data.services,
        parts=data.parts,
        labor_charges=data.labor_charges,
        parts_total=parts_total,
        services_total=services_total,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_percent=data.discount_percent,
        discount_amount=discount_amount,
        total_amount=total_amount,
        created_by=user.user_id
    )
    
    doc = sales_order.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.sales_orders.insert_one(doc)
    
    # Update ticket
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id},
        {"$set": {"has_sales_order": True, "estimated_cost": total_amount}}
    )
    
    return sales_order.model_dump()

@router.get("/sales-orders")
async def get_sales_orders(request: Request, status: Optional[str] = None):
    await require_auth(request)
    query = {}
    if status:
        query["status"] = status
    orders = await db.sales_orders.find(query, {"_id": 0}).to_list(1000)
    return orders

@router.get("/sales-orders/{sales_id}")
async def get_sales_order(sales_id: str, request: Request):
    await require_auth(request)
    order = await db.sales_orders.find_one({"sales_id": sales_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return order

@router.put("/sales-orders/{sales_id}")
async def update_sales_order(sales_id: str, update: SalesOrderUpdate, request: Request):
    user = await require_auth(request)
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update.approval_status in ["level1_approved", "level2_approved"]:
        update_dict["approved_by"] = user.user_id
        if update.approval_status == "level2_approved":
            update_dict["status"] = "approved"
    
    await db.sales_orders.update_one({"sales_id": sales_id}, {"$set": update_dict})
    order = await db.sales_orders.find_one({"sales_id": sales_id}, {"_id": 0})
    return order

# ==================== INVOICE ROUTES ====================

@router.post("/invoices")
async def create_invoice(data: InvoiceCreate, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_technician_or_admin(request)
    
    # Get ticket details
    ticket = await db.tickets.find_one({"ticket_id": data.ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get vehicle and customer details (vehicle_id may be None)
    vehicle_id = ticket.get("vehicle_id")
    vehicle = None
    if vehicle_id:
        vehicle = await db.vehicles.find_one({"vehicle_id": vehicle_id}, {"_id": 0})
    
    # Calculate totals
    subtotal = sum(item.get("amount", 0) for item in data.line_items)
    tax_amount = (subtotal - data.discount_amount) * 0.18
    total_amount = subtotal - data.discount_amount + tax_amount
    
    invoice_number = await generate_invoice_number(ctx.org_id)
    due_date = datetime.now(timezone.utc) + timedelta(days=data.due_days)
    
    invoice = Invoice(
        invoice_number=invoice_number,
        sales_id=data.sales_id,
        ticket_id=data.ticket_id,
        customer_id=ticket.get("customer_id", user.user_id),
        customer_name=ticket.get("customer_name") or (vehicle.get("owner_name", "") if vehicle else ""),
        customer_email=ticket.get("customer_email") or (vehicle.get("owner_email") if vehicle else None),
        customer_phone=ticket.get("contact_number") or (vehicle.get("owner_phone") if vehicle else None),
        vehicle_id=vehicle_id,
        vehicle_details=f"{vehicle['make']} {vehicle['model']} ({vehicle['registration_number']})" if vehicle else ticket.get("vehicle_number"),
        line_items=data.line_items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=data.discount_amount,
        total_amount=total_amount,
        balance_due=total_amount,
        due_date=due_date,
        notes=data.notes,
        created_by=user.user_id
    )
    
    doc = invoice.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['due_date'] = doc['due_date'].isoformat()
    doc['organization_id'] = ctx.org_id   # tenant scope
    await db.invoices.insert_one(doc)
    
    # Update ticket
    await db.tickets.update_one(
        {"ticket_id": data.ticket_id},
        {"$set": {"has_invoice": True, "invoice_id": invoice.invoice_id, "actual_cost": total_amount}}
    )
    
    # Create ledger entry
    await create_ledger_entry(
        account_type="asset",
        account_name="Accounts Receivable",
        description=f"Invoice: {invoice_number}",
        reference_type="invoice",
        reference_id=invoice.invoice_id,
        debit=total_amount,
        credit=0,
        created_by=user.user_id,
        ticket_id=data.ticket_id,
        vehicle_id=ticket["vehicle_id"]
    )
    
    return invoice.model_dump()

@router.get("/invoices")
async def get_invoices(request: Request, status: Optional[str] = None, ctx: TenantContext = Depends(tenant_context_required)):
    user = await require_auth(request)
    query = {"organization_id": ctx.org_id}   # tenant-scoped
    if status:
        query["status"] = status
    if user.role == "customer":
        query["customer_id"] = user.user_id
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request, ctx: TenantContext = Depends(tenant_context_required)):
    await require_auth(request)
    invoice = await db.invoices.find_one(
        {"invoice_id": invoice_id, "organization_id": ctx.org_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, update: InvoiceUpdate, request: Request):
    await require_technician_or_admin(request)
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": update_dict})
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    return invoice

@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, request: Request):
    """Generate and download invoice PDF with GST compliance"""
    from services.invoice_service import generate_invoice_pdf
    from fastapi.responses import StreamingResponse
    
    await require_auth(request)
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Transform existing invoice format to PDF service format
    customer_data = {
        "name": invoice.get("customer_name", "Customer"),
        "address": "",
        "city": "Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "gstin": None
    }
    
    # Try to get customer details
    if invoice.get("customer_id"):
        customer = await db.customers.find_one({"customer_id": invoice["customer_id"]}, {"_id": 0})
        if customer:
            customer_data = {
                "name": customer.get("name", invoice.get("customer_name", "")),
                "address": customer.get("address", ""),
                "city": customer.get("city", "Delhi"),
                "state": customer.get("state", "Delhi"),
                "pincode": customer.get("pincode", "110001"),
                "gstin": customer.get("gstin")
            }
    
    # Transform line items
    line_items = []
    for item in invoice.get("line_items", []):
        line_items.append({
            "description": item.get("description", item.get("name", "Service")),
            "hsn_sac": item.get("hsn_sac", "998714"),
            "quantity": item.get("quantity", 1),
            "unit": item.get("unit", "pcs"),
            "rate": item.get("rate", item.get("amount", 0)),
            "gst_percent": 18
        })
    
    # Build PDF-compatible invoice
    pdf_invoice = {
        "invoice_id": invoice.get("invoice_id"),
        "invoice_number": invoice.get("invoice_number"),
        "invoice_date": invoice.get("created_at", datetime.now(timezone.utc).isoformat())[:10].replace("-", "/"),
        "due_date": invoice.get("due_date", datetime.now(timezone.utc).isoformat())[:10].replace("-", "/"),
        "terms": "Due on Receipt",
        "vehicle_number": invoice.get("vehicle_details", "").split("(")[-1].replace(")", "") if invoice.get("vehicle_details") else "N/A",
        "po_number": invoice.get("invoice_number"),
        "place_of_supply": customer_data.get("state", "Delhi"),
        "place_of_supply_code": "07",  # Default to Delhi
        "customer": customer_data,
        "line_items": line_items,
        "sub_total": invoice.get("subtotal", 0),
        "igst_amount": invoice.get("tax_amount", 0),
        "cgst_amount": 0,
        "sgst_amount": 0,
        "rounding": 0,
        "total_amount": invoice.get("total_amount", 0),
        "total_in_words": ""
    }
    
    # Calculate total in words
    from services.invoice_service import number_to_words
    pdf_invoice["total_in_words"] = number_to_words(pdf_invoice["total_amount"])
    
    # Generate PDF
    pdf_buffer = generate_invoice_pdf(pdf_invoice)
    
    filename = f"{invoice.get('invoice_number', invoice_id)}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== PAYMENT ROUTES ====================

@router.post("/payments")
async def record_payment(data: PaymentCreate, request: Request):
    user = await require_technician_or_admin(request)
    
    # Get invoice
    invoice = await db.invoices.find_one({"invoice_id": data.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment = Payment(
        invoice_id=data.invoice_id,
        amount=data.amount,
        payment_method=data.payment_method,
        reference_number=data.reference_number,
        notes=data.notes,
        received_by=user.user_id
    )
    
    doc = payment.model_dump()
    doc['payment_date'] = doc['payment_date'].isoformat()
    await db.payments.insert_one(doc)
    
    # Update invoice — support both legacy (total_amount) and enhanced (grand_total) schema
    total = invoice.get("grand_total") or invoice.get("total_amount", 0)
    current_paid = invoice.get("amount_paid", 0)
    new_amount_paid = current_paid + data.amount
    new_balance = total - new_amount_paid
    
    payment_status = "paid" if new_balance <= 0 else "partial"
    invoice_status = "paid" if new_balance <= 0 else "partially_paid"
    
    update_data = {
        "amount_paid": new_amount_paid,
        "balance_due": max(0, new_balance),
        "payment_status": payment_status,
        "status": invoice_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if new_balance <= 0:
        update_data["paid_date"] = datetime.now(timezone.utc).isoformat()
    
    await db.invoices.update_one({"invoice_id": data.invoice_id}, {"$set": update_data})
    
    # Create ledger entries
    await create_ledger_entry(
        account_type="asset",
        account_name="Cash/Bank",
        description=f"Payment received: {data.payment_method}",
        reference_type="payment",
        reference_id=payment.payment_id,
        debit=data.amount,
        credit=0,
        created_by=user.user_id,
        ticket_id=invoice.get("ticket_id"),
        vehicle_id=invoice.get("vehicle_id")
    )
    
    await create_ledger_entry(
        account_type="asset",
        account_name="Accounts Receivable",
        description=f"Payment received for Invoice {invoice.get('invoice_number', invoice.get('invoice_id', 'N/A'))}",
        reference_type="payment",
        reference_id=payment.payment_id,
        debit=0,
        credit=data.amount,
        created_by=user.user_id,
        ticket_id=invoice.get("ticket_id"),
        vehicle_id=invoice.get("vehicle_id")
    )
    
    # Record revenue
    await create_ledger_entry(
        account_type="revenue",
        account_name="Service Revenue",
        description=f"Revenue from Invoice {invoice.get('invoice_number', invoice.get('invoice_id', 'N/A'))}",
        reference_type="payment",
        reference_id=payment.payment_id,
        debit=0,
        credit=data.amount,
        created_by=user.user_id,
        ticket_id=invoice.get("ticket_id"),
        vehicle_id=invoice.get("vehicle_id")
    )
    
    # Update vehicle total service cost
    await db.vehicles.update_one(
        {"vehicle_id": invoice.get("vehicle_id")},
        {"$inc": {"total_service_cost": data.amount}}
    )
    
    return payment.model_dump()

@router.get("/payments")
async def get_payments(request: Request, invoice_id: Optional[str] = None):
    await require_auth(request)
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    payments = await db.payments.find(query, {"_id": 0}).to_list(1000)
    return payments

# ==================== ACCOUNTING/LEDGER ROUTES ====================

@router.get("/ledger")
async def get_ledger(
    request: Request,
    account_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    await require_admin(request)
    
    query = {}
    if account_type:
        query["account_type"] = account_type
    if start_date:
        query["entry_date"] = {"$gte": start_date}
    if end_date:
        if "entry_date" in query:
            query["entry_date"]["$lte"] = end_date
        else:
            query["entry_date"] = {"$lte": end_date}
    
    entries = await db.ledger.find(query, {"_id": 0}).sort("entry_date", -1).to_list(1000)
    return entries

@router.get("/accounting/summary")
async def get_accounting_summary(request: Request):
    await require_admin(request)
    
    # Calculate totals from ledger
    pipeline = [
        {"$group": {
            "_id": "$account_type",
            "total_debit": {"$sum": "$debit"},
            "total_credit": {"$sum": "$credit"}
        }}
    ]
    
    results = await db.ledger.aggregate(pipeline).to_list(10)
    
    totals = {r["_id"]: {"debit": r["total_debit"], "credit": r["total_credit"]} for r in results}
    
    revenue = totals.get("revenue", {"credit": 0})["credit"]
    expenses = totals.get("expense", {"debit": 0})["debit"]
    receivables = totals.get("asset", {"debit": 0})["debit"] - totals.get("asset", {"credit": 0})["credit"]
    payables = totals.get("liability", {"credit": 0})["credit"] - totals.get("liability", {"debit": 0})["debit"]
    
    return AccountSummary(
        total_revenue=revenue,
        total_expenses=expenses,
        total_receivables=max(0, receivables),
        total_payables=max(0, payables),
        gross_profit=revenue - expenses,
        net_profit=revenue - expenses
    )

@router.get("/accounting/ticket/{ticket_id}")

@router.get("/accounting/ticket/{ticket_id}")
async def get_ticket_financials(ticket_id: str, request: Request):
    """Get all financial data for a specific ticket"""
    await require_auth(request)
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    allocations = await db.allocations.find({"ticket_id": ticket_id}, {"_id": 0}).to_list(100)
    sales_order = await db.sales_orders.find_one({"ticket_id": ticket_id}, {"_id": 0})
    invoice = await db.invoices.find_one({"ticket_id": ticket_id}, {"_id": 0})
    ledger_entries = await db.ledger.find({"ticket_id": ticket_id}, {"_id": 0}).to_list(100)
    
    return {
        "ticket": ticket,
        "allocations": allocations,
        "sales_order": sales_order,
        "invoice": invoice,
        "ledger_entries": ledger_entries,
        "summary": {
            "parts_cost": sum(a["total_price"] for a in allocations if a["status"] != "returned"),
            "labor_cost": ticket.get("labor_cost", 0),
            "total_cost": ticket.get("actual_cost", 0),
            "amount_paid": invoice.get("amount_paid", 0) if invoice else 0,
            "balance_due": invoice.get("balance_due", 0) if invoice else 0
        }
    }

# ==================== AI DIAGNOSIS ====================

# Issue category knowledge base for EV-specific diagnosis
ISSUE_CATEGORY_KNOWLEDGE = {
    "battery": {
        "common_causes": ["Cell degradation", "BMS fault", "Thermal runaway risk", "Connection corrosion", "Overcharging damage"],
        "diagnostic_steps": ["Check battery voltage levels", "Measure cell balance", "Inspect BMS error codes", "Check temperature sensors", "Verify charging history"],
        "safety_warnings": ["High voltage hazard - use insulated tools", "Do not puncture or damage cells", "Ensure proper ventilation"],
        "parts": ["Battery cells", "BMS module", "Thermal sensors", "Cooling fan", "Battery connectors"]
    },
    "motor": {
        "common_causes": ["Bearing wear", "Winding damage", "Controller failure", "Overheating", "Magnet demagnetization"],
        "diagnostic_steps": ["Listen for unusual sounds", "Check motor temperature", "Measure phase resistance", "Inspect motor controller", "Test regenerative braking"],
        "safety_warnings": ["Allow motor to cool before inspection", "Disconnect power before testing", "Beware of moving parts"],
        "parts": ["Motor bearings", "Motor controller", "Hall sensors", "Motor windings", "Cooling system"]
    },
    "charging": {
        "common_causes": ["Charger malfunction", "Port damage", "Communication error", "Cable fault", "Onboard charger failure"],
        "diagnostic_steps": ["Check charging port pins", "Verify charger output", "Test communication protocol", "Inspect cable condition", "Check fuses"],
        "safety_warnings": ["Never charge with damaged cable", "Ensure proper grounding", "Don't use in wet conditions"],
        "parts": ["Charging port", "Onboard charger", "Charging cable", "DC-DC converter", "Fuses"]
    },
    "electrical": {
        "common_causes": ["Short circuit", "Ground fault", "Wire damage", "Connector corrosion", "Relay failure"],
        "diagnostic_steps": ["Check all fuses", "Inspect wire harness", "Test relay operation", "Measure insulation resistance", "Check ground connections"],
        "safety_warnings": ["Isolate HV battery before work", "Use multimeter properly", "Check for arc flash risk"],
        "parts": ["Fuses", "Relays", "Connectors", "Wire harness", "Junction box"]
    },
    "mechanical": {
        "common_causes": ["Brake wear", "Drivetrain issues", "Gear damage", "Belt/chain wear", "Transmission fault"],
        "diagnostic_steps": ["Inspect brake pads/discs", "Check drivetrain noise", "Test gear engagement", "Measure belt tension", "Check fluid levels"],
        "safety_warnings": ["Support vehicle properly on stands", "Use wheel chocks", "Wear safety glasses"],
        "parts": ["Brake pads", "Brake discs", "Drive belt", "Gearbox components", "CV joints"]
    },
    "software": {
        "common_causes": ["Firmware bug", "ECU error", "Communication failure", "Calibration issue", "Software corruption"],
        "diagnostic_steps": ["Read diagnostic codes", "Check ECU communication", "Verify firmware version", "Test CAN bus", "Check software updates"],
        "safety_warnings": ["Don't interrupt firmware updates", "Backup settings before reset", "Use authorized diagnostic tools"],
        "parts": ["ECU module", "Diagnostic interface", "Software license", "Communication module"]
    },
    "suspension": {
        "common_causes": ["Shock absorber wear", "Spring damage", "Bushing deterioration", "Alignment issues", "Strut mount failure"],
        "diagnostic_steps": ["Check ride height", "Inspect shock absorbers", "Test bushings for play", "Measure wheel alignment", "Check for leaks"],
        "safety_warnings": ["Use spring compressor carefully", "Support vehicle securely", "Beware of compressed springs"],
        "parts": ["Shock absorbers", "Coil springs", "Control arm bushings", "Strut mounts", "Ball joints"]
    },
    "braking": {
        "common_causes": ["Brake pad wear", "Rotor damage", "Brake fluid contamination", "ABS sensor fault", "Regenerative brake issue"],
        "diagnostic_steps": ["Measure pad thickness", "Check rotor condition", "Test brake fluid", "Read ABS codes", "Test regenerative braking"],
        "safety_warnings": ["Brake dust is hazardous", "Use proper brake cleaner", "Check for asbestos in older vehicles"],
        "parts": ["Brake pads", "Rotors/discs", "Brake fluid", "ABS sensors", "Calipers"]
    },
    "cooling": {
        "common_causes": ["Coolant leak", "Pump failure", "Radiator blockage", "Thermostat fault", "Fan malfunction"],
        "diagnostic_steps": ["Check coolant level", "Inspect for leaks", "Test pump operation", "Check thermostat", "Test cooling fan"],
        "safety_warnings": ["Don't open hot cooling system", "Coolant is toxic", "Allow system to cool"],
        "parts": ["Coolant pump", "Radiator", "Thermostat", "Cooling fan", "Hoses and clamps"]
    },
    "hvac": {
        "common_causes": ["Compressor failure", "Refrigerant leak", "Blower motor issue", "Heater core problem", "Climate control fault"],
        "diagnostic_steps": ["Check refrigerant pressure", "Test compressor clutch", "Check blower motor", "Inspect heater core", "Test climate controls"],
        "safety_warnings": ["Refrigerant requires special handling", "Don't release to atmosphere", "Use certified equipment"],
        "parts": ["AC compressor", "Condenser", "Blower motor", "Heater core", "Climate control module"]
    },
    "other": {
        "common_causes": ["General wear", "Environmental damage", "User error", "Design defect", "Unknown"],
        "diagnostic_steps": ["Visual inspection", "Functional testing", "Document symptoms", "Review service history", "Consult technical manual"],
        "safety_warnings": ["Follow general safety procedures", "Use PPE", "Document all findings"],
        "parts": ["Varies by issue"]
    }
}

# Vehicle category specific considerations
VEHICLE_CATEGORY_CONTEXT = {
    "2_wheeler": {
        "description": "Electric Scooters and Motorcycles",
        "specific_issues": ["Hub motor issues", "Swappable battery problems", "Compact controller faults", "Kick-start backup failure"],
        "typical_range": "80-150 km per charge",
        "voltage_range": "48V-72V systems",
        "special_notes": "Smaller battery packs, more exposed to weather, often swappable batteries"
    },
    "3_wheeler": {
        "description": "Electric Auto-Rickshaws, E-Rickshaws, and Cargo Loaders",
        "specific_issues": ["Overloading damage", "Lead-acid to lithium conversion issues", "Controller overheating", "Differential problems"],
        "typical_range": "80-120 km per charge",
        "voltage_range": "48V-60V systems (passenger), 72V+ (cargo)",
        "special_notes": "Heavy-duty usage, frequent charging, often lead-acid batteries in older models"
    },
    "4_wheeler_commercial": {
        "description": "Electric LCVs, Delivery Vans, and Pickup Trucks",
        "specific_issues": ["Payload stress on motor", "Frequent start-stop wear", "Cargo area electrical issues", "Fleet telematics problems"],
        "typical_range": "100-200 km per charge",
        "voltage_range": "300V-400V high voltage systems",
        "special_notes": "Commercial duty cycles, need for quick turnaround, fleet management integration"
    },
    "car": {
        "description": "Electric Passenger Cars",
        "specific_issues": ["Infotainment system glitches", "Advanced driver assistance faults", "Complex HV battery management", "Thermal management issues"],
        "typical_range": "200-500 km per charge",
        "voltage_range": "350V-800V high voltage systems",
        "special_notes": "Most complex systems, multiple ECUs, advanced safety features, OTA updates"
    }
}

@router.post("/ai/diagnose")

@router.get("/chart-of-accounts")
async def get_chart_of_accounts(request: Request):
    await require_auth(request)
    accounts = await db.chart_of_accounts.find({}, {"_id": 0}).to_list(500)
    return accounts

@router.get("/chart-of-accounts/by-type/{account_type}")
async def get_accounts_by_type(account_type: str, request: Request):
    await require_auth(request)
    accounts = await db.chart_of_accounts.find(
        {"account_type": account_type, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    return accounts

# ==================== MIGRATION ROUTES ====================
