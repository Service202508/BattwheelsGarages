"""
E-Invoice & Tally Export Module
Generates GST-compliant e-invoice JSON and Tally-compatible XML exports
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import logging
from fastapi import Request
from utils.database import extract_org_id, org_query


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["export"])

# Database connection
def get_db():
    from server import db
    return db

# ============== E-INVOICE GENERATION (GST Compliant) ==============

class EInvoiceConfig(BaseModel):
    gstin: str = "29AABCU9603R1ZJ"  # Supplier GSTIN
    legal_name: str = "Battwheels EV Solutions Pvt Ltd"
    trade_name: str = "Battwheels Garages"
    address: str = "123 Industrial Area"
    city: str = "New Delhi"
    state_code: str = "07"
    pin_code: str = "110001"
    email: str = "accounts@battwheels.in"
    phone: str = "9876543210"

# Default config (can be updated via settings)
DEFAULT_CONFIG = EInvoiceConfig()

@router.get("/einvoice/{invoice_id}")
async def generate_einvoice(request: Request, invoice_id: str):
    org_id = extract_org_id(request)
    """Generate GST e-invoice JSON for a given invoice"""
    db = get_db()
    
    # Fetch invoice
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Fetch customer details
    customer = await db.contacts.find_one({"contact_id": invoice.get("customer_id")}, {"_id": 0})
    
    # Build e-invoice structure as per GST schema
    einvoice = {
        "Version": "1.1",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": "B2B",  # B2B, SEZWP, SEZWOP, EXPWP, EXPWOP, DEXP
            "RegRev": "N",
            "EcmGstin": None,
            "IgstOnIntra": "N"
        },
        "DocDtls": {
            "Typ": "INV",  # INV, CRN, DBN
            "No": invoice.get("invoice_number", ""),
            "Dt": format_date_for_einvoice(invoice.get("date", "")),
        },
        "SellerDtls": {
            "Gstin": DEFAULT_CONFIG.gstin,
            "LglNm": DEFAULT_CONFIG.legal_name,
            "TrdNm": DEFAULT_CONFIG.trade_name,
            "Addr1": DEFAULT_CONFIG.address,
            "Loc": DEFAULT_CONFIG.city,
            "Pin": int(DEFAULT_CONFIG.pin_code),
            "Stcd": DEFAULT_CONFIG.state_code,
            "Em": DEFAULT_CONFIG.email,
            "Ph": DEFAULT_CONFIG.phone
        },
        "BuyerDtls": {
            "Gstin": customer.get("gst_no", "URP") if customer else "URP",  # URP = Unregistered Person
            "LglNm": customer.get("contact_name", invoice.get("customer_name", "")),
            "TrdNm": customer.get("company_name", customer.get("contact_name", "")),
            "Addr1": customer.get("billing_address", {}).get("street", ""),
            "Loc": customer.get("billing_address", {}).get("city", ""),
            "Pin": int(customer.get("billing_address", {}).get("zip", "110001") or "110001"),
            "Stcd": customer.get("billing_address", {}).get("state_code", "07") or "07",
            "Pos": invoice.get("place_of_supply", "07"),
            "Ph": customer.get("phone", ""),
            "Em": customer.get("email", "")
        },
        "ItemList": [],
        "ValDtls": {
            "AssVal": invoice.get("sub_total", 0),
            "CgstVal": invoice.get("tax_total", 0) / 2 if invoice.get("place_of_supply", "07") == "07" else 0,
            "SgstVal": invoice.get("tax_total", 0) / 2 if invoice.get("place_of_supply", "07") == "07" else 0,
            "IgstVal": invoice.get("tax_total", 0) if invoice.get("place_of_supply", "07") != "07" else 0,
            "CesVal": 0,
            "StCesVal": 0,
            "Discount": invoice.get("discount_total", 0),
            "OthChrg": invoice.get("shipping_charge", 0) + invoice.get("adjustment", 0),
            "RndOffAmt": 0,
            "TotInvVal": invoice.get("total", 0),
            "TotInvValFc": 0
        },
        "PayDtls": {
            "Nm": "",
            "AccDet": "",
            "Mode": "",
            "FinInsBr": "",
            "PayTerm": str(invoice.get("payment_terms", 15)),
            "PayInstr": "",
            "CrTrn": "",
            "DirDr": "",
            "CrDay": invoice.get("payment_terms", 15),
            "PaidAmt": invoice.get("payment_made", 0),
            "PaymtDue": invoice.get("balance", 0)
        }
    }
    
    # Add line items
    for idx, item in enumerate(invoice.get("line_items", []), 1):
        qty = item.get("quantity", 1)
        rate = item.get("rate", 0)
        discount = item.get("discount", 0)
        taxable = (qty * rate) - discount
        tax_rate = item.get("tax_percentage", 18)
        tax_amount = taxable * (tax_rate / 100)
        
        is_intra_state = invoice.get("place_of_supply", "07") == "07"
        
        einvoice["ItemList"].append({
            "SlNo": str(idx),
            "PrdDesc": item.get("name", item.get("description", "")),
            "IsServc": "Y" if item.get("item_type", "service") == "service" else "N",
            "HsnCd": item.get("hsn_or_sac", "998719"),
            "Qty": qty,
            "Unit": item.get("unit", "OTH"),
            "UnitPrice": rate,
            "TotAmt": qty * rate,
            "Discount": discount,
            "PreTaxVal": taxable,
            "AssAmt": taxable,
            "GstRt": tax_rate,
            "IgstAmt": tax_amount if not is_intra_state else 0,
            "CgstAmt": tax_amount / 2 if is_intra_state else 0,
            "SgstAmt": tax_amount / 2 if is_intra_state else 0,
            "CesRt": 0,
            "CesAmt": 0,
            "CesNonAdvlAmt": 0,
            "StateCesRt": 0,
            "StateCesAmt": 0,
            "StateCesNonAdvlAmt": 0,
            "OthChrg": 0,
            "TotItemVal": taxable + tax_amount
        })
    
    return {
        "code": 0,
        "invoice_id": invoice_id,
        "invoice_number": invoice.get("invoice_number"),
        "einvoice_json": einvoice
    }

@router.get("/einvoice/{invoice_id}/download")
async def download_einvoice(request: Request, invoice_id: str):
    org_id = extract_org_id(request)
    """Download e-invoice as JSON file"""
    result = await generate_einvoice(invoice_id)
    
    json_content = json.dumps(result["einvoice_json"], indent=2)
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="einvoice_{result["invoice_number"]}.json"'
        }
    )

# ============== TALLY EXPORT ==============

@router.get("/tally/invoices")
async def export_invoices_to_tally(request: Request, start_date: str = "", end_date: str = "", limit: int = 100):
    org_id = extract_org_id(request)
    """Export invoices in Tally-compatible XML format"""
    db = get_db()
    
    query = {}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    
    invoices = await db.invoices.find(query, {"_id": 0}).limit(limit).to_list(length=limit)
    
    # Create Tally XML structure
    root = ET.Element("ENVELOPE")
    
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
    
    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
    
    request_data = ET.SubElement(import_data, "REQUESTDATA")
    
    for inv in invoices:
        voucher = ET.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")
        voucher_elem = ET.SubElement(voucher, "VOUCHER", VCHTYPE="Sales", ACTION="Create")
        
        ET.SubElement(voucher_elem, "DATE").text = format_date_for_tally(inv.get("date", ""))
        ET.SubElement(voucher_elem, "VOUCHERTYPENAME").text = "Sales"
        ET.SubElement(voucher_elem, "VOUCHERNUMBER").text = inv.get("invoice_number", "")
        ET.SubElement(voucher_elem, "REFERENCE").text = inv.get("reference_number", "")
        ET.SubElement(voucher_elem, "PARTYLEDGERNAME").text = inv.get("customer_name", "")
        ET.SubElement(voucher_elem, "EFFECTIVEDATE").text = format_date_for_tally(inv.get("date", ""))
        ET.SubElement(voucher_elem, "ISINVOICE").text = "Yes"
        ET.SubElement(voucher_elem, "PERSISTEDVIEW").text = "Invoice Voucher View"
        
        # Party ledger entry (debit)
        party_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(party_entry, "LEDGERNAME").text = inv.get("customer_name", "")
        ET.SubElement(party_entry, "ISDEEMEDPOSITIVE").text = "Yes"
        ET.SubElement(party_entry, "AMOUNT").text = f"-{inv.get('total', 0)}"
        
        # Sales ledger entry (credit)
        for item in inv.get("line_items", []):
            sales_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(sales_entry, "LEDGERNAME").text = "Sales"
            ET.SubElement(sales_entry, "ISDEEMEDPOSITIVE").text = "No"
            amount = item.get("quantity", 1) * item.get("rate", 0)
            ET.SubElement(sales_entry, "AMOUNT").text = str(amount)
            
            # GST entries
            tax_amount = amount * (item.get("tax_percentage", 18) / 100)
            if inv.get("place_of_supply", "07") == "07":
                # Intra-state: CGST + SGST
                cgst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(cgst_entry, "LEDGERNAME").text = f"CGST @ {item.get('tax_percentage', 18)/2}%"
                ET.SubElement(cgst_entry, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(cgst_entry, "AMOUNT").text = str(tax_amount / 2)
                
                sgst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(sgst_entry, "LEDGERNAME").text = f"SGST @ {item.get('tax_percentage', 18)/2}%"
                ET.SubElement(sgst_entry, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(sgst_entry, "AMOUNT").text = str(tax_amount / 2)
            else:
                # Inter-state: IGST
                igst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(igst_entry, "LEDGERNAME").text = f"IGST @ {item.get('tax_percentage', 18)}%"
                ET.SubElement(igst_entry, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(igst_entry, "AMOUNT").text = str(tax_amount)
    
    xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    return Response(
        content=xml_string,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="tally_invoices_{datetime.now().strftime("%Y%m%d")}.xml"'
        }
    )

@router.get("/tally/bills")
async def export_bills_to_tally(request: Request, start_date: str = "", end_date: str = "", limit: int = 100):
    org_id = extract_org_id(request)
    """Export bills (purchases) in Tally-compatible XML format"""
    db = get_db()
    
    query = {}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    
    bills = await db.bills.find(query, {"_id": 0}).limit(limit).to_list(length=limit)
    
    root = ET.Element("ENVELOPE")
    
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
    
    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
    
    request_data = ET.SubElement(import_data, "REQUESTDATA")
    
    for bill in bills:
        voucher = ET.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")
        voucher_elem = ET.SubElement(voucher, "VOUCHER", VCHTYPE="Purchase", ACTION="Create")
        
        ET.SubElement(voucher_elem, "DATE").text = format_date_for_tally(bill.get("date", ""))
        ET.SubElement(voucher_elem, "VOUCHERTYPENAME").text = "Purchase"
        ET.SubElement(voucher_elem, "VOUCHERNUMBER").text = bill.get("bill_number", "")
        ET.SubElement(voucher_elem, "REFERENCE").text = bill.get("reference_number", "")
        ET.SubElement(voucher_elem, "PARTYLEDGERNAME").text = bill.get("vendor_name", "")
        
        # Vendor ledger entry (credit)
        party_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(party_entry, "LEDGERNAME").text = bill.get("vendor_name", "")
        ET.SubElement(party_entry, "ISDEEMEDPOSITIVE").text = "No"
        ET.SubElement(party_entry, "AMOUNT").text = str(bill.get('total', 0))
        
        # Purchase ledger entry (debit)
        for item in bill.get("line_items", []):
            purchase_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(purchase_entry, "LEDGERNAME").text = "Purchase"
            ET.SubElement(purchase_entry, "ISDEEMEDPOSITIVE").text = "Yes"
            amount = item.get("quantity", 1) * item.get("rate", 0)
            ET.SubElement(purchase_entry, "AMOUNT").text = f"-{amount}"
            
            # Input GST entries
            tax_amount = amount * (item.get("tax_percentage", 18) / 100)
            if bill.get("destination_of_supply", "07") == "07":
                cgst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(cgst_entry, "LEDGERNAME").text = f"Input CGST @ {item.get('tax_percentage', 18)/2}%"
                ET.SubElement(cgst_entry, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(cgst_entry, "AMOUNT").text = f"-{tax_amount / 2}"
                
                sgst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(sgst_entry, "LEDGERNAME").text = f"Input SGST @ {item.get('tax_percentage', 18)/2}%"
                ET.SubElement(sgst_entry, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(sgst_entry, "AMOUNT").text = f"-{tax_amount / 2}"
            else:
                igst_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(igst_entry, "LEDGERNAME").text = f"Input IGST @ {item.get('tax_percentage', 18)}%"
                ET.SubElement(igst_entry, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(igst_entry, "AMOUNT").text = f"-{tax_amount}"
    
    xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    return Response(
        content=xml_string,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="tally_bills_{datetime.now().strftime("%Y%m%d")}.xml"'
        }
    )

@router.get("/tally/payments")
async def export_payments_to_tally(request: Request, start_date: str = "", end_date: str = "", limit: int = 100):
    org_id = extract_org_id(request)
    """Export customer payments in Tally-compatible XML format"""
    db = get_db()
    
    query = {}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    
    payments = await db.customerpayments.find(query, {"_id": 0}).limit(limit).to_list(length=limit)
    
    root = ET.Element("ENVELOPE")
    
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
    
    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
    
    request_data = ET.SubElement(import_data, "REQUESTDATA")
    
    for pmt in payments:
        voucher = ET.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")
        voucher_elem = ET.SubElement(voucher, "VOUCHER", VCHTYPE="Receipt", ACTION="Create")
        
        ET.SubElement(voucher_elem, "DATE").text = format_date_for_tally(pmt.get("date", ""))
        ET.SubElement(voucher_elem, "VOUCHERTYPENAME").text = "Receipt"
        ET.SubElement(voucher_elem, "VOUCHERNUMBER").text = pmt.get("payment_number", "")
        ET.SubElement(voucher_elem, "REFERENCE").text = pmt.get("reference_number", "")
        ET.SubElement(voucher_elem, "PARTYLEDGERNAME").text = pmt.get("customer_name", "")
        ET.SubElement(voucher_elem, "NARRATION").text = pmt.get("description", "")
        
        # Bank/Cash entry (debit)
        bank_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
        bank_name = "Cash" if pmt.get("payment_mode") == "Cash" else "Bank Account"
        ET.SubElement(bank_entry, "LEDGERNAME").text = bank_name
        ET.SubElement(bank_entry, "ISDEEMEDPOSITIVE").text = "Yes"
        ET.SubElement(bank_entry, "AMOUNT").text = f"-{pmt.get('amount', 0)}"
        
        # Customer entry (credit)
        party_entry = ET.SubElement(voucher_elem, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(party_entry, "LEDGERNAME").text = pmt.get("customer_name", "")
        ET.SubElement(party_entry, "ISDEEMEDPOSITIVE").text = "No"
        ET.SubElement(party_entry, "AMOUNT").text = str(pmt.get('amount', 0))
    
    xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    return Response(
        content=xml_string,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="tally_payments_{datetime.now().strftime("%Y%m%d")}.xml"'
        }
    )

@router.get("/tally/ledgers")
async def export_ledgers_to_tally(request: Request):
    org_id = extract_org_id(request)
    """Export customer and vendor ledgers in Tally-compatible XML format"""
    db = get_db()
    
    contacts = await db.contacts.find({"status": "active"}, {"_id": 0}).to_list(length=1000)
    
    root = ET.Element("ENVELOPE")
    
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
    
    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "All Masters"
    
    request_data = ET.SubElement(import_data, "REQUESTDATA")
    
    for contact in contacts:
        message = ET.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")
        ledger = ET.SubElement(message, "LEDGER", NAME=contact.get("contact_name", ""), ACTION="Create")
        
        # Determine parent group
        if contact.get("contact_type") == "customer":
            parent = "Sundry Debtors"
        else:
            parent = "Sundry Creditors"
        
        ET.SubElement(ledger, "PARENT").text = parent
        ET.SubElement(ledger, "ISBILLWISEON").text = "Yes"
        ET.SubElement(ledger, "AFFECTSSTOCK").text = "No"
        
        # Address details
        if contact.get("billing_address"):
            addr = contact["billing_address"]
            addr_list = ET.SubElement(ledger, "ADDRESS.LIST")
            if addr.get("street"):
                ET.SubElement(addr_list, "ADDRESS").text = addr.get("street", "")
            if addr.get("city"):
                ET.SubElement(addr_list, "ADDRESS").text = f"{addr.get('city', '')}, {addr.get('state', '')}"
            if addr.get("zip"):
                ET.SubElement(addr_list, "ADDRESS").text = f"PIN: {addr.get('zip', '')}"
        
        # GST details
        if contact.get("gst_no"):
            ET.SubElement(ledger, "PARTYGSTIN").text = contact.get("gst_no", "")
            ET.SubElement(ledger, "GSTREGISTRATIONTYPE").text = "Regular"
        
        # Contact details
        if contact.get("email"):
            ET.SubElement(ledger, "EMAIL").text = contact.get("email", "")
        if contact.get("phone"):
            ET.SubElement(ledger, "PHONENUMBER").text = contact.get("phone", "")
    
    xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    return Response(
        content=xml_string,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="tally_ledgers_{datetime.now().strftime("%Y%m%d")}.xml"'
        }
    )

# ============== HELPER FUNCTIONS ==============

def format_date_for_einvoice(date_str: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY for e-invoice"""
    if not date_str:
        return datetime.now().strftime("%d/%m/%Y")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return date_str

def format_date_for_tally(date_str: str) -> str:
    """Convert YYYY-MM-DD to YYYYMMDD for Tally"""
    if not date_str:
        return datetime.now().strftime("%Y%m%d")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y%m%d")
    except:
        return date_str.replace("-", "")

# ============== BULK EXPORT ==============

@router.get("/bulk/invoices")
async def bulk_export_invoices(request: Request, format: str = "csv", start_date: str = "", end_date: str = ""):
    org_id = extract_org_id(request)
    """Export invoices in CSV or Excel format"""
    db = get_db()
    
    query = {}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(length=10000)
    
    if format == "csv":
        # Generate CSV
        csv_lines = ["Invoice Number,Date,Customer,Subtotal,Tax,Total,Balance,Status"]
        for inv in invoices:
            csv_lines.append(
                f'{inv.get("invoice_number","")},{inv.get("date","")},{inv.get("customer_name","").replace(",","")},'
                f'{inv.get("sub_total",0)},{inv.get("tax_total",0)},{inv.get("total",0)},{inv.get("balance",0)},{inv.get("status","")}'
            )
        
        csv_content = "\n".join(csv_lines)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="invoices_export_{datetime.now().strftime("%Y%m%d")}.csv"'
            }
        )
    else:
        # Return JSON
        return {"code": 0, "invoices": invoices, "count": len(invoices)}

@router.get("/bulk/expenses")
async def bulk_export_expenses(request: Request, format: str = "csv", start_date: str = "", end_date: str = ""):
    org_id = extract_org_id(request)
    """Export expenses in CSV format"""
    db = get_db()
    
    query = {}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    
    expenses = await db.expenses.find(query, {"_id": 0}).to_list(length=10000)
    
    if format == "csv":
        csv_lines = ["Date,Account,Vendor,Amount,Tax,Total,Description"]
        for exp in expenses:
            csv_lines.append(
                f'{exp.get("date","")},{(exp.get("expense_account_name") or "").replace(",","")},{(exp.get("vendor_name") or "").replace(",","")},'
                f'{exp.get("amount",0)},{exp.get("tax_amount",0)},{exp.get("total",0)},{(exp.get("description") or "").replace(",","")}'
            )
        
        csv_content = "\n".join(csv_lines)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="expenses_export_{datetime.now().strftime("%Y%m%d")}.csv"'
            }
        )
    else:
        return {"code": 0, "expenses": expenses, "count": len(expenses)}
