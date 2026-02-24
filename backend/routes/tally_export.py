"""
Tally XML Export Route
=======================

Exports journal entries as TallyPrime-compatible XML.

GET /api/finance/export/tally-xml
  Query params: date_from (YYYY-MM-DD), date_to (YYYY-MM-DD)
  Returns: XML file download

XML format: TallyPrime voucher import format.
Each journal entry → one VOUCHER block.
Each line item → one ALLLEDGERENTRIES.LIST block.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import os
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from core.tenant.context import TenantContext, tenant_context_required
from fastapi import Depends

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance/export", tags=["Finance Export"])

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]


def _date_to_tally(date_str: str) -> str:
    """Convert YYYY-MM-DD to Tally's YYYYMMDD format."""
    try:
        dt = datetime.fromisoformat(str(date_str)[:10])
        return dt.strftime("%Y%m%d")
    except Exception:
        return datetime.now().strftime("%Y%m%d")


def _build_tally_xml(entries: list, org_name: str) -> str:
    """Build TallyPrime-compatible XML from journal entries."""
    root = ET.Element("ENVELOPE")

    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")

    req_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(req_desc, "REPORTNAME").text = "Vouchers"
    static_vars = ET.SubElement(req_desc, "STATICVARIABLES")
    ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = org_name

    req_data = ET.SubElement(import_data, "REQUESTDATA")

    for entry in entries:
        tally_msg = ET.SubElement(req_data, "TALLYMESSAGE")
        tally_msg.set("xmlns:UDF", "TallyUDF")

        voucher = ET.SubElement(tally_msg, "VOUCHER")
        voucher.set("VCHTYPE", "Journal")
        voucher.set("ACTION", "Create")

        ET.SubElement(voucher, "DATE").text = _date_to_tally(
            entry.get("entry_date", "") or entry.get("date", "")
        )
        ET.SubElement(voucher, "NARRATION").text = (
            entry.get("description", "") or entry.get("narration", "") or "Journal Entry"
        )
        ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Journal"

        line_items = entry.get("line_items", entry.get("entries", []))
        for line in line_items:
            account = line.get("account_name", line.get("account", "Unknown"))
            debit_amount = float(line.get("debit", 0) or 0)
            credit_amount = float(line.get("credit", 0) or 0)

            # Tally uses one entry per side:
            # DEBIT: ISDEEMEDPOSITIVE=Yes, AMOUNT=negative value
            # CREDIT: ISDEEMEDPOSITIVE=No, AMOUNT=positive value
            if debit_amount > 0:
                le = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(le, "LEDGERNAME").text = account
                ET.SubElement(le, "ISDEEMEDPOSITIVE").text = "Yes"
                ET.SubElement(le, "AMOUNT").text = f"-{debit_amount:.2f}"
            elif credit_amount > 0:
                le = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ET.SubElement(le, "LEDGERNAME").text = account
                ET.SubElement(le, "ISDEEMEDPOSITIVE").text = "No"
                ET.SubElement(le, "AMOUNT").text = f"{credit_amount:.2f}"

    # Pretty-print with declaration
    ET.indent(root)
    xml_bytes = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes


@router.get("/tally-xml")
async def export_tally_xml(request: Request, date_from: str = Query(..., description="Start date YYYY-MM-DD"),
    date_to: str = Query(..., description="End date YYYY-MM-DD"),
    ctx: TenantContext = Depends(tenant_context_required),
):
    """
    Export journal entries as TallyPrime-compatible XML.
    Returns a downloadable .xml file.
    """
    # Validate dates
    try:
        dt_from = datetime.fromisoformat(date_from).replace(hour=0, minute=0, second=0)
        dt_to = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if dt_from > dt_to:
        raise HTTPException(status_code=400, detail="date_from must be before date_to.")

    # Fetch journal entries in range
    query = {
        "organization_id": ctx.org_id,
        "$or": [
            {"entry_date": {"$gte": date_from, "$lte": date_to}},
            {"date": {"$gte": date_from, "$lte": date_to}},
        ],
    }
    entries = await db.journal_entries.find(query, {"_id": 0}).sort("entry_date", 1).to_list(5000)

    if not entries:
        raise HTTPException(
            status_code=404,
            detail=f"No journal entries found between {date_from} and {date_to}."
        )

    # Get org name
    org = await db.organizations.find_one({"organization_id": ctx.org_id}, {"_id": 0, "name": 1})
    org_name = org.get("name", "Organisation") if org else "Organisation"

    # Build XML
    try:
        xml_content = _build_tally_xml(entries, org_name)
    except Exception as e:
        logger.error(f"Tally XML build failed for org {ctx.org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"XML generation failed: {str(e)}")

    # Validate XML (catch malformed output)
    try:
        ET.fromstring(xml_content.split("\n", 1)[1])  # Skip XML declaration for parsing
    except ET.ParseError as e:
        logger.error(f"Generated XML is invalid: {e}")
        raise HTTPException(status_code=500, detail=f"Generated XML is invalid: {str(e)}")

    filename = f"tally-{date_from}-{date_to}.xml"
    logger.info(f"Tally XML export: {len(entries)} entries for org {ctx.org_id} ({date_from} to {date_to})")

    return Response(
        content=xml_content.encode("utf-8"),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def init_tally_export_router(app_db):
    global db
    db = app_db
    return router
