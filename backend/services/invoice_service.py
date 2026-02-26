"""
Battwheels OS - Invoice Service with PDF Generation
Based on Battwheels Services Private Limited Tax Invoice Template
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from io import BytesIO
import uuid
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

router = APIRouter(prefix="/invoices", tags=["Invoices"])

# Company Details (configurable)
COMPANY_INFO = {
    "name": "Battwheels Services Private Limited",
    "address": "A-19 G-F Okhla Phase-2 Fiee Complex Kartar Tower",
    "area": "Okhla Industrial Estate",
    "city": "New Delhi",
    "state": "New Delhi",
    "pincode": "110020",
    "gstin": "07AAMCB4976D1ZG",
    "bank_name": "KOTAK MAHINDRA BANK ADCHINI DELHI",
    "account_name": "BATTWHEELS SERVICES PRIVATE LIMITED",
    "account_no": "0648556556",
    "ifsc": "KKBK0004635",
    "branch": "ADCHINI DELHI"
}

# HSN/SAC codes for common services
HSN_CODES = {
    "visit_charges": "998712",
    "labor_charges": "998725",
    "repair_services": "998714",
    "parts": "87089300",
    "brake_oil": "381900",
    "battery": "85076000",
    "motor": "85011091",
    "electrical": "85389000"
}

# Models
class InvoiceLineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    description: str
    hsn_sac: str
    quantity: float
    unit: str = "pcs"
    rate: float
    gst_percent: float = 18.0

class CustomerDetails(BaseModel):
    name: str
    address: str
    city: str
    state: str
    pincode: str
    gstin: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class InvoiceCreate(BaseModel):
    ticket_id: Optional[str] = None
    customer: CustomerDetails
    vehicle_number: Optional[str] = None
    place_of_supply: str
    place_of_supply_code: str
    line_items: List[InvoiceLineItem]
    terms: str = "Due on Receipt"
    notes: Optional[str] = None

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    invoice_id: str = Field(default_factory=lambda: f"INV-BWG{str(uuid.uuid4().hex[:6]).upper()}")
    invoice_number: str = ""
    ticket_id: Optional[str] = None
    garage_id: str = ""
    
    # Dates
    invoice_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%d/%m/%Y"))
    due_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%d/%m/%Y"))
    terms: str = "Due on Receipt"
    
    # Vehicle & PO
    vehicle_number: Optional[str] = None
    po_number: Optional[str] = None
    place_of_supply: str = ""
    place_of_supply_code: str = ""
    
    # Customer
    customer: dict = {}
    
    # Line Items
    line_items: List[dict] = []
    
    # Totals
    sub_total: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    rounding: float = 0.0
    total_amount: float = 0.0
    total_in_words: str = ""
    
    # Status
    status: str = "generated"
    payment_status: str = "pending"
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    pdf_url: Optional[str] = None

# Database reference
db = None

def init_router(database):
    global db
    db = database
    return router

def number_to_words(num: float) -> str:
    """Convert number to words (Indian format)"""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_less_than_thousand(n):
        if n == 0:
            return ""
        elif n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
        else:
            return ones[n // 100] + " Hundred" + (" " + convert_less_than_thousand(n % 100) if n % 100 != 0 else "")
    
    if num == 0:
        return "Zero"
    
    num = int(round(num))
    
    # Indian numbering system
    crore = num // 10000000
    lakh = (num % 10000000) // 100000
    thousand = (num % 100000) // 1000
    remainder = num % 1000
    
    result = []
    if crore:
        result.append(convert_less_than_thousand(crore) + " Crore")
    if lakh:
        result.append(convert_less_than_thousand(lakh) + " Lakh")
    if thousand:
        result.append(convert_less_than_thousand(thousand) + " Thousand")
    if remainder:
        result.append(convert_less_than_thousand(remainder))
    
    return " ".join(result)

def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code for payment"""
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generate_invoice_pdf(invoice: dict) -> BytesIO:
    """Generate PDF matching Battwheels invoice template"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=15*mm, rightMargin=15*mm,
                           topMargin=15*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=8,
        leading=10
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=7,
        leading=9
    )
    
    # ===== HEADER SECTION =====
    header_data = [
        [Paragraph(f"<b>{COMPANY_INFO['name']}</b>", title_style)],
        [Paragraph(f"{COMPANY_INFO['address']}", header_style)],
        [Paragraph(f"{COMPANY_INFO['area']}, {COMPANY_INFO['city']}, {COMPANY_INFO['state']} - {COMPANY_INFO['pincode']}", header_style)],
        [Paragraph(f"<b>GSTIN:</b> {COMPANY_INFO['gstin']}", header_style)],
    ]
    
    header_table = Table(header_data, colWidths=[180*mm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 5*mm))
    
    # TAX INVOICE title
    elements.append(Paragraph("<b>TAX INVOICE</b>", title_style))
    elements.append(Spacer(1, 5*mm))
    
    # ===== INVOICE DETAILS + SUPPLY DETAILS =====
    invoice_details = [
        [Paragraph(f"<b>Invoice #:</b> {invoice.get('invoice_number', invoice.get('invoice_id'))}", normal_style),
         Paragraph(f"<b>Place Of Supply:</b> {invoice.get('place_of_supply', '')} ({invoice.get('place_of_supply_code', '')})", normal_style)],
        [Paragraph(f"<b>Invoice Date:</b> {invoice.get('invoice_date', '')}", normal_style),
         Paragraph(f"<b>VEHICLE NUMBER:</b> {invoice.get('vehicle_number', 'N/A')}", normal_style)],
        [Paragraph(f"<b>Terms:</b> {invoice.get('terms', 'Due on Receipt')}", normal_style), ""],
        [Paragraph(f"<b>Due Date:</b> {invoice.get('due_date', '')}", normal_style), ""],
        [Paragraph(f"<b>P.O.#:</b> {invoice.get('po_number', invoice.get('vehicle_number', 'N/A'))}", normal_style), ""],
    ]
    
    details_table = Table(invoice_details, colWidths=[90*mm, 90*mm])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 5*mm))
    
    # ===== BILL TO SECTION =====
    customer = invoice.get('customer', {})
    bill_to_data = [
        [Paragraph("<b>Bill To</b>", normal_style)],
        [Paragraph(f"<b>{customer.get('name', '')}</b>", normal_style)],
        [Paragraph(f"{customer.get('address', '')}", small_style)],
        [Paragraph(f"{customer.get('city', '')}, {customer.get('state', '')} {customer.get('pincode', '')}", small_style)],
        [Paragraph("India", small_style)],
        [Paragraph(f"<b>GSTIN:</b> {customer.get('gstin', 'N/A')}", small_style)],
    ]
    
    bill_to_table = Table(bill_to_data, colWidths=[90*mm])
    bill_to_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(bill_to_table)
    elements.append(Spacer(1, 5*mm))
    
    # ===== LINE ITEMS TABLE =====
    # Determine if IGST or CGST/SGST based on state
    is_igst = invoice.get('place_of_supply_code') != '07'  # 07 is Delhi
    
    if is_igst:
        header_row = ['SN', 'Description', 'HSN/SAC', 'Qty', 'Rate', 'IGST %', 'Tax Amt', 'Amount']
        col_widths = [8*mm, 55*mm, 18*mm, 15*mm, 22*mm, 15*mm, 20*mm, 25*mm]
    else:
        header_row = ['SN', 'Description', 'HSN/SAC', 'Qty', 'Rate', 'CGST %', 'SGST %', 'Tax', 'Amount']
        col_widths = [8*mm, 50*mm, 16*mm, 12*mm, 20*mm, 12*mm, 12*mm, 18*mm, 25*mm]
    
    table_data = [header_row]
    
    line_items = invoice.get('line_items', [])
    for i, item in enumerate(line_items, 1):
        gst_rate = item.get('gst_percent', 18)
        amount = item.get('quantity', 1) * item.get('rate', 0)
        tax_amount = amount * gst_rate / 100
        
        if is_igst:
            row = [
                str(i),
                Paragraph(f"{item.get('description', '')}<br/><font size=6><i>({item.get('unit', 'pcs')})</i></font>", small_style),
                item.get('hsn_sac', ''),
                f"{item.get('quantity', 1):.2f}",
                f"{item.get('rate', 0):,.2f}",
                f"{gst_rate:.0f}%",
                f"{tax_amount:,.2f}",
                f"{amount:,.2f}"
            ]
        else:
            half_rate = gst_rate / 2
            half_tax = tax_amount / 2
            row = [
                str(i),
                Paragraph(f"{item.get('description', '')}<br/><font size=6><i>({item.get('unit', 'pcs')})</i></font>", small_style),
                item.get('hsn_sac', ''),
                f"{item.get('quantity', 1):.2f}",
                f"{item.get('rate', 0):,.2f}",
                f"{half_rate:.0f}%",
                f"{half_rate:.0f}%",
                f"{tax_amount:,.2f}",
                f"{amount:,.2f}"
            ]
        table_data.append(row)
    
    items_table = Table(table_data, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a4a4a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 3*mm))
    
    # ===== TOTALS SECTION =====
    sub_total = invoice.get('sub_total', 0)
    igst_amount = invoice.get('igst_amount', 0)
    cgst_amount = invoice.get('cgst_amount', 0)
    sgst_amount = invoice.get('sgst_amount', 0)
    rounding = invoice.get('rounding', 0)
    total = invoice.get('total_amount', 0)
    
    totals_data = [
        ['Sub Total', f"₹{sub_total:,.2f}"],
    ]
    
    if is_igst and igst_amount > 0:
        totals_data.append([f'IGST (18%)', f"₹{igst_amount:,.2f}"])
    else:
        if cgst_amount > 0:
            totals_data.append([f'CGST (9%)', f"₹{cgst_amount:,.2f}"])
        if sgst_amount > 0:
            totals_data.append([f'SGST (9%)', f"₹{sgst_amount:,.2f}"])
    
    if rounding != 0:
        totals_data.append(['Rounding', f"₹{rounding:,.2f}"])
    
    totals_data.append([Paragraph('<b>Total</b>', normal_style), Paragraph(f'<b>₹{total:,.2f}</b>', normal_style)])
    
    totals_table = Table(totals_data, colWidths=[140*mm, 38*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 3*mm))
    
    # Total in words
    elements.append(Paragraph(f"<b>Indian Rupee {invoice.get('total_in_words', '')} Only</b>", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # ===== BANK DETAILS + QR CODE =====
    # Generate QR code
    qr_data = f"upi://pay?pa=battwheels@kotak&pn=BATTWHEELS&am={total}&cu=INR"
    qr_buffer = generate_qr_code(qr_data)
    qr_image = Image(qr_buffer, width=25*mm, height=25*mm)
    
    bank_text = f"""<b>BANK DETAILS:</b><br/>
    ACCOUNT NAME: {COMPANY_INFO['account_name']}<br/>
    BANK NAME: {COMPANY_INFO['bank_name']}<br/>
    ACCOUNT NO: {COMPANY_INFO['account_no']}<br/>
    IFSC: {COMPANY_INFO['ifsc']}<br/>
    BRANCH: {COMPANY_INFO['branch']}"""
    
    bank_qr_data = [
        [Paragraph(bank_text, small_style), qr_image, Paragraph("<b>Scan QR to Pay</b>", small_style)]
    ]
    
    bank_table = Table(bank_qr_data, colWidths=[100*mm, 30*mm, 45*mm])
    bank_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
    ]))
    elements.append(bank_table)
    elements.append(Spacer(1, 5*mm))
    
    # Terms
    elements.append(Paragraph("<b>Terms & Conditions:</b>", small_style))
    elements.append(Paragraph("100% ADVANCE DUE ON E-INVOICE RECEIPT & WITHIN 7 DAYS OF TAX INVOICE GENERATION.", small_style))
    elements.append(Spacer(1, 10*mm))
    
    # Signature
    sig_data = [
        ['', Paragraph('<b>Authorised Signatory</b>', normal_style)],
        ['', ''],
        ['', Paragraph(f'For: {COMPANY_INFO["name"]}', small_style)]
    ]
    
    sig_table = Table(sig_data, colWidths=[120*mm, 55*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 20),
    ]))
    elements.append(sig_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

async def get_next_invoice_number() -> str:
    """Generate next sequential invoice number"""
    last_invoice = await db.invoices.find_one(
        {},
        sort=[("invoice_number", -1)],
        projection={"invoice_number": 1}
    )
    
    if last_invoice and last_invoice.get("invoice_number"):
        try:
            # Extract number from INV-BWG000123 format
            num = int(last_invoice["invoice_number"].replace("INV-BWG", ""))
            return f"INV-BWG{str(num + 1).zfill(6)}"
        except:
            pass
    
    return "INV-BWG000001"

# Routes
@router.post("")
async def create_invoice(data: InvoiceCreate, request: Request):
    """Create a new invoice"""
    # Calculate totals
    sub_total = 0
    total_tax = 0
    line_items_processed = []
    
    for item in data.line_items:
        amount = item.quantity * item.rate
        tax_amount = amount * item.gst_percent / 100
        sub_total += amount
        total_tax += tax_amount
        
        line_items_processed.append({
            "description": item.description,
            "hsn_sac": item.hsn_sac,
            "quantity": item.quantity,
            "unit": item.unit,
            "rate": item.rate,
            "gst_percent": item.gst_percent,
            "tax_amount": round(tax_amount, 2),
            "amount": round(amount, 2)
        })
    
    # Determine IGST vs CGST/SGST
    is_igst = data.place_of_supply_code != "07"  # 07 is Delhi
    
    if is_igst:
        igst_amount = round(total_tax, 2)
        cgst_amount = 0
        sgst_amount = 0
    else:
        igst_amount = 0
        cgst_amount = round(total_tax / 2, 2)
        sgst_amount = round(total_tax / 2, 2)
    
    # Calculate rounding
    raw_total = sub_total + total_tax
    rounded_total = round(raw_total)
    rounding = round(rounded_total - raw_total, 2)
    
    # Generate invoice number
    invoice_number = await get_next_invoice_number()
    
    invoice = Invoice(
        invoice_number=invoice_number,
        ticket_id=data.ticket_id,
        vehicle_number=data.vehicle_number,
        po_number=data.vehicle_number,
        place_of_supply=data.place_of_supply,
        place_of_supply_code=data.place_of_supply_code,
        terms=data.terms,
        customer=data.customer.model_dump(),
        line_items=line_items_processed,
        sub_total=round(sub_total, 2),
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        igst_amount=igst_amount,
        rounding=rounding,
        total_amount=rounded_total,
        total_in_words=number_to_words(rounded_total)
    )
    
    doc = invoice.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.invoices.insert_one(doc)
    
    # Update ticket if linked
    if data.ticket_id:
        await db.tickets.update_one(
            {"ticket_id": data.ticket_id},
            {"$set": {
                "has_invoice": True,
                "invoice_id": invoice.invoice_id,
                "status": "invoiced"
            }}
        )
    
    return invoice.model_dump()

@router.get("")
async def list_invoices(
    request: Request,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    limit: int = 50
):
    """List all invoices"""
    query = {}
    if status:
        query["status"] = status
    if payment_status:
        query["payment_status"] = payment_status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return invoices

@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request):
    """Get invoice by ID"""
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, request: Request):
    """Download invoice as PDF"""
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_buffer = generate_invoice_pdf(invoice)
    
    filename = f"{invoice.get('invoice_number', invoice_id)}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/from-ticket/{ticket_id}")
async def create_invoice_from_ticket(ticket_id: str, request: Request):
    """Create invoice directly from a resolved ticket"""
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get customer details
    customer_id = ticket.get("customer_id")
    customer = None
    if customer_id:
        customer = await db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
    
    if not customer:
        customer = {
            "name": ticket.get("customer_name", "Walk-in Customer"),
            "address": ticket.get("incident_location", ""),
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "gstin": None
        }
    
    # Build line items from ticket
    line_items = []
    
    # Add visit charges if onsite
    if ticket.get("ticket_type") == "onsite":
        line_items.append(InvoiceLineItem(
            description="CUSTOMER COMPLAINT VISIT CHARGES",
            hsn_sac=HSN_CODES["visit_charges"],
            quantity=1,
            unit="pcs",
            rate=299
        ))
    
    # Add parts from estimated/actual items
    parts = ticket.get("actual_items", {}).get("parts", []) or ticket.get("estimated_items", {}).get("parts", [])
    for part in parts:
        line_items.append(InvoiceLineItem(
            description=part.get("name", "Part"),
            hsn_sac=part.get("hsn", HSN_CODES["parts"]),
            quantity=part.get("quantity", 1),
            unit=part.get("unit", "pcs"),
            rate=part.get("rate", 0)
        ))
    
    # Add services/labor
    services = ticket.get("actual_items", {}).get("services", []) or ticket.get("estimated_items", {}).get("services", [])
    for service in services:
        line_items.append(InvoiceLineItem(
            description=service.get("name", "Service"),
            hsn_sac=service.get("hsn", HSN_CODES["labor_charges"]),
            quantity=service.get("quantity", 1),
            unit=service.get("unit", "hrs"),
            rate=service.get("rate", 0)
        ))
    
    # If no items, add default labor
    if not line_items:
        line_items.append(InvoiceLineItem(
            description="LABOR CHARGES - REPAIR SERVICE",
            hsn_sac=HSN_CODES["labor_charges"],
            quantity=1,
            unit="job",
            rate=ticket.get("estimated_cost", 500)
        ))
    
    # Create invoice
    invoice_data = InvoiceCreate(
        ticket_id=ticket_id,
        customer=CustomerDetails(**customer),
        vehicle_number=ticket.get("vehicle_number"),
        place_of_supply=customer.get("state", "Delhi"),
        place_of_supply_code="07",  # Delhi code
        line_items=line_items
    )
    
    return await create_invoice(invoice_data, request)
