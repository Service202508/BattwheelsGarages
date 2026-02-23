"""
GST E-Invoice Service for Battwheels OS
Integrates with NIC Invoice Registration Portal (IRP) for IRN generation

API Documentation: https://einvoice1.gst.gov.in
Sandbox: https://einv-apisandbox.nic.in

Features:
- Authentication with IRP
- IRN Generation for B2B invoices
- IRN Cancellation (within 24 hours)
- QR Code generation from signed payload
- Multi-tenant credential management
"""

import os
import json
import hashlib
import base64
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.fernet import Fernet
import qrcode
from io import BytesIO

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

# NIC E-Invoice Endpoints
# Production: https://einvoice1.gst.gov.in
# Sandbox: https://einv-apisandbox.nic.in
EINVOICE_SANDBOX_URL = "https://einv-apisandbox.nic.in"
EINVOICE_PRODUCTION_URL = "https://einvoice1.gst.gov.in"

# API Endpoints
ENDPOINTS = {
    "auth": "/eivital/v1.04/auth",
    "generate_irn": "/eicore/v1.03/Invoice",
    "get_irn": "/eicore/v1.03/Invoice/irn/{irn}",
    "cancel_irn": "/eicore/v1.03/Invoice/Cancel",
    "get_gstin": "/eivital/v1.03/Master/gstin/{gstin}",
}

# REPLACE WITH REAL IRP SANDBOX CREDENTIALS
# These are placeholder values - organization-specific credentials
# should be stored in the database and retrieved at runtime
DEFAULT_SANDBOX_CREDENTIALS = {
    "client_id": "PLACEHOLDER_CLIENT_ID",
    "client_secret": "PLACEHOLDER_CLIENT_SECRET",
    "username": "PLACEHOLDER_USERNAME",
    "password": "PLACEHOLDER_PASSWORD",
    "gstin": "PLACEHOLDER_GSTIN"
}

# Encryption key for storing credentials (should be from environment)
ENCRYPTION_KEY = os.environ.get("EINVOICE_ENCRYPTION_KEY", Fernet.generate_key().decode())

# ==================== DATABASE ====================

def get_db():
    """Get database connection"""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "battwheels")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]

# ==================== ENCRYPTION HELPERS ====================

def get_cipher():
    """Get Fernet cipher for encryption/decryption"""
    key = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
    # Ensure key is valid Fernet key (32 bytes base64 encoded)
    if len(key) != 44:
        # Generate a consistent key from the provided value
        key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
    return Fernet(key)

def encrypt_credential(value: str) -> str:
    """Encrypt a credential value"""
    if not value:
        return ""
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def decrypt_credential(encrypted_value: str) -> str:
    """Decrypt a credential value"""
    if not encrypted_value:
        return ""
    try:
        cipher = get_cipher()
        return cipher.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt credential: {e}")
        return ""

# ==================== CREDENTIAL MANAGEMENT ====================

async def get_einvoice_config(org_id: str) -> Optional[Dict]:
    """Get E-Invoice configuration for an organization"""
    db = get_db()
    config = await db.einvoice_config.find_one(
        {"organization_id": org_id},
        {"_id": 0}
    )
    return config

async def save_einvoice_config(org_id: str, config: Dict) -> Dict:
    """Save E-Invoice configuration for an organization"""
    db = get_db()
    
    # Encrypt sensitive fields
    encrypted_config = {
        "organization_id": org_id,
        "gstin": config.get("gstin", ""),
        "irp_username": config.get("irp_username", ""),
        "irp_password_encrypted": encrypt_credential(config.get("irp_password", "")),
        "client_id": config.get("client_id", ""),
        "client_secret_encrypted": encrypt_credential(config.get("client_secret", "")),
        "is_sandbox": config.get("is_sandbox", True),
        "enabled": config.get("enabled", False),
        "turnover_threshold_met": config.get("turnover_threshold_met", False),
        "updated_at": datetime.now(timezone.utc),
        "created_at": config.get("created_at", datetime.now(timezone.utc))
    }
    
    await db.einvoice_config.update_one(
        {"organization_id": org_id},
        {"$set": encrypted_config},
        upsert=True
    )
    
    return {
        "code": 0,
        "message": "E-Invoice configuration saved successfully",
        "gstin": encrypted_config["gstin"],
        "enabled": encrypted_config["enabled"]
    }

async def delete_einvoice_config(org_id: str) -> Dict:
    """Delete E-Invoice configuration for an organization"""
    db = get_db()
    result = await db.einvoice_config.delete_one({"organization_id": org_id})
    return {
        "code": 0,
        "deleted": result.deleted_count > 0
    }

def get_decrypted_credentials(config: Dict) -> Dict:
    """Get decrypted credentials from config"""
    return {
        "gstin": config.get("gstin", ""),
        "username": config.get("irp_username", ""),
        "password": decrypt_credential(config.get("irp_password_encrypted", "")),
        "client_id": config.get("client_id", ""),
        "client_secret": decrypt_credential(config.get("client_secret_encrypted", ""))
    }

# ==================== IRP AUTHENTICATION ====================

class IRPAuthManager:
    """Manages authentication with IRP API"""
    
    def __init__(self, org_id: str, is_sandbox: bool = True):
        self.org_id = org_id
        self.is_sandbox = is_sandbox
        self.base_url = EINVOICE_SANDBOX_URL if is_sandbox else EINVOICE_PRODUCTION_URL
        self.token = None
        self.token_expiry = None
        self.sek = None  # Session Encryption Key
    
    async def get_credentials(self) -> Dict:
        """Get credentials for this organization"""
        config = await get_einvoice_config(self.org_id)
        if not config:
            raise ValueError("E-Invoice not configured for this organization")
        return get_decrypted_credentials(config)
    
    async def authenticate(self) -> Tuple[str, str]:
        """
        Authenticate with IRP and get auth token
        Returns: (auth_token, session_encryption_key)
        """
        creds = await self.get_credentials()
        
        # Prepare authentication payload
        auth_payload = {
            "UserName": creds["username"],
            "Password": creds["password"],
            "AppKey": creds["client_id"],
            "ForceRefreshAccessToken": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "gstin": creds["gstin"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}{ENDPOINTS['auth']}",
                    json=auth_payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"IRP Auth failed: {response.status_code} - {response.text}")
                    raise Exception(f"IRP Authentication failed: {response.status_code}")
                
                data = response.json()
                
                if data.get("Status") != 1:
                    error_msg = data.get("ErrorDetails", [{}])[0].get("ErrorMessage", "Unknown error")
                    raise Exception(f"IRP Authentication error: {error_msg}")
                
                result = data.get("Data", {})
                self.token = result.get("AuthToken")
                self.sek = result.get("Sek")  # Session Encryption Key
                self.token_expiry = datetime.now(timezone.utc) + timedelta(hours=5)  # Token valid for ~6 hours
                
                logger.info(f"IRP Authentication successful for org {self.org_id}")
                return self.token, self.sek
                
            except httpx.RequestError as e:
                logger.error(f"IRP Auth request error: {e}")
                raise Exception(f"Failed to connect to IRP: {e}")
    
    async def get_valid_token(self) -> Tuple[str, str]:
        """Get a valid auth token, refreshing if necessary"""
        if self.token and self.token_expiry and datetime.now(timezone.utc) < self.token_expiry:
            return self.token, self.sek
        return await self.authenticate()

# ==================== INVOICE VALIDATION ====================

class EInvoiceValidator:
    """Validates invoice data before IRN generation"""
    
    REQUIRED_FIELDS = [
        "invoice_number",
        "invoice_date",
        "customer_gstin",
        "supplier_gstin",
        "place_of_supply",
        "total_amount"
    ]
    
    REQUIRED_LINE_ITEM_FIELDS = [
        "name",
        "hsn_sac_code",
        "quantity",
        "rate",
        "amount"
    ]
    
    @staticmethod
    def validate_gstin(gstin: str) -> bool:
        """Validate GSTIN format (15 characters)"""
        if not gstin or len(gstin) != 15:
            return False
        # GSTIN format: 2 digits (state) + 10 char PAN + 1 entity + 1 check
        import re
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
        return bool(re.match(pattern, gstin.upper()))
    
    @staticmethod
    def validate_hsn_code(hsn: str) -> bool:
        """Validate HSN/SAC code (4, 6, or 8 digits)"""
        if not hsn:
            return False
        hsn = hsn.strip()
        return hsn.isdigit() and len(hsn) in [4, 6, 8]
    
    @staticmethod
    def validate_place_of_supply(pos: str) -> bool:
        """Validate Place of Supply code (2 digits)"""
        if not pos:
            return False
        return pos.isdigit() and len(pos) == 2 and 1 <= int(pos) <= 37
    
    @classmethod
    def validate_invoice(cls, invoice: Dict, line_items: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate invoice for E-Invoice compliance
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required invoice fields
        for field in cls.REQUIRED_FIELDS:
            if not invoice.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate supplier GSTIN
        supplier_gstin = invoice.get("supplier_gstin", "")
        if supplier_gstin and not cls.validate_gstin(supplier_gstin):
            errors.append(f"Invalid supplier GSTIN format: {supplier_gstin}")
        
        # Validate customer GSTIN (for B2B)
        customer_gstin = invoice.get("customer_gstin", "")
        if customer_gstin and customer_gstin != "URP":  # URP = Unregistered Person / Export
            if not cls.validate_gstin(customer_gstin):
                errors.append(f"Invalid customer GSTIN format: {customer_gstin}")
        
        # Validate place of supply
        pos = invoice.get("place_of_supply", "")
        if pos and not cls.validate_place_of_supply(pos):
            errors.append(f"Invalid Place of Supply code: {pos}")
        
        # Validate line items
        if not line_items:
            errors.append("Invoice must have at least one line item")
        else:
            for i, item in enumerate(line_items):
                # Check required fields
                for field in cls.REQUIRED_LINE_ITEM_FIELDS:
                    if field == "hsn_sac_code":
                        hsn = item.get("hsn_sac_code") or item.get("hsn_code", "")
                        if not hsn:
                            errors.append(f"Line item {i+1}: Missing HSN/SAC code")
                        elif not cls.validate_hsn_code(hsn):
                            errors.append(f"Line item {i+1}: Invalid HSN/SAC code: {hsn}")
                    elif not item.get(field):
                        errors.append(f"Line item {i+1}: Missing {field}")
        
        return len(errors) == 0, errors

# ==================== E-INVOICE SCHEMA BUILDER ====================

class EInvoiceSchemaBuilder:
    """Builds GST E-Invoice JSON schema payload"""
    
    # Document type codes
    DOC_TYPES = {
        "INV": "INV",  # Invoice
        "CRN": "CRN",  # Credit Note
        "DBN": "DBN"   # Debit Note
    }
    
    # Supply type codes
    SUPPLY_TYPES = {
        "B2B": "B2B",      # Business to Business
        "B2C": "B2C",      # Business to Consumer
        "SEZWP": "SEZWP",  # SEZ with payment
        "SEZWOP": "SEZWOP", # SEZ without payment
        "EXP": "EXPWP",    # Export with payment
        "DEXP": "DEXP"     # Deemed export
    }
    
    @staticmethod
    def get_financial_year(invoice_date: datetime) -> str:
        """Get financial year string (e.g., '2024-25')"""
        year = invoice_date.year
        month = invoice_date.month
        if month < 4:  # Before April, previous FY
            return f"{year-1}-{str(year)[2:]}"
        return f"{year}-{str(year+1)[2:]}"
    
    @staticmethod
    def format_date(dt: datetime) -> str:
        """Format date as DD/MM/YYYY"""
        return dt.strftime("%d/%m/%Y")
    
    @staticmethod
    def round_amount(amount: float) -> float:
        """Round amount to 2 decimal places"""
        return round(float(amount), 2)
    
    @classmethod
    def build_payload(cls, invoice: Dict, line_items: List[Dict], 
                      supplier: Dict, buyer: Dict) -> Dict:
        """
        Build E-Invoice JSON payload conforming to GST INV-01 schema
        
        Args:
            invoice: Invoice document
            line_items: List of line item documents
            supplier: Supplier/seller details
            buyer: Buyer/customer details
            
        Returns:
            Dict: E-Invoice JSON payload
        """
        invoice_date = invoice.get("invoice_date")
        if isinstance(invoice_date, str):
            invoice_date = datetime.fromisoformat(invoice_date.replace("Z", "+00:00"))
        
        # Determine supply type
        supply_type = cls.SUPPLY_TYPES.get(
            invoice.get("supply_type", "B2B"),
            cls.SUPPLY_TYPES["B2B"]
        )
        
        # Build transaction details
        tran_dtls = {
            "TaxSch": "GST",
            "SupTyp": supply_type,
            "RegRev": "N",  # Reverse charge: N=No, Y=Yes
            "EcmGstin": None,  # E-commerce GSTIN if applicable
            "IgstOnIntra": "N"  # IGST on intra-state supply: N=No
        }
        
        # Build document details
        doc_dtls = {
            "Typ": cls.DOC_TYPES.get(invoice.get("doc_type", "INV"), "INV"),
            "No": invoice.get("invoice_number", ""),
            "Dt": cls.format_date(invoice_date)
        }
        
        # Build seller details
        seller_dtls = {
            "Gstin": supplier.get("gstin", ""),
            "LglNm": supplier.get("legal_name", supplier.get("name", "")),
            "TrdNm": supplier.get("trade_name", supplier.get("name", "")),
            "Addr1": supplier.get("address_line1", supplier.get("address", ""))[:100],
            "Addr2": supplier.get("address_line2", "")[:100] if supplier.get("address_line2") else None,
            "Loc": supplier.get("city", supplier.get("location", ""))[:100],
            "Pin": int(supplier.get("pincode", supplier.get("zip", "000000"))[:6]) if supplier.get("pincode") or supplier.get("zip") else 000000,
            "Stcd": supplier.get("state_code", supplier.get("gstin", "")[:2] if supplier.get("gstin") else ""),
            "Ph": supplier.get("phone", "")[:12] if supplier.get("phone") else None,
            "Em": supplier.get("email", "")[:100] if supplier.get("email") else None
        }
        
        # Build buyer details
        buyer_dtls = {
            "Gstin": buyer.get("gstin", "URP"),  # URP for unregistered
            "LglNm": buyer.get("legal_name", buyer.get("name", ""))[:100],
            "TrdNm": buyer.get("trade_name", buyer.get("name", ""))[:100] if buyer.get("trade_name") else None,
            "Pos": invoice.get("place_of_supply", buyer.get("state_code", ""))[:2],
            "Addr1": buyer.get("address_line1", buyer.get("billing_address", {}).get("address", ""))[:100],
            "Addr2": buyer.get("address_line2", "")[:100] if buyer.get("address_line2") else None,
            "Loc": buyer.get("city", buyer.get("billing_address", {}).get("city", ""))[:100],
            "Pin": int(str(buyer.get("pincode", buyer.get("billing_address", {}).get("zip", "000000")))[:6]) if buyer.get("pincode") or buyer.get("billing_address", {}).get("zip") else 000000,
            "Stcd": buyer.get("state_code", buyer.get("gstin", "")[:2] if buyer.get("gstin") else ""),
            "Ph": buyer.get("phone", "")[:12] if buyer.get("phone") else None,
            "Em": buyer.get("email", "")[:100] if buyer.get("email") else None
        }
        
        # Build item list
        item_list = []
        for idx, item in enumerate(line_items, 1):
            hsn = item.get("hsn_sac_code") or item.get("hsn_code", "")
            quantity = cls.round_amount(item.get("quantity", 1))
            unit_price = cls.round_amount(item.get("rate", 0))
            discount = cls.round_amount(item.get("discount_amount", 0))
            taxable_value = cls.round_amount(item.get("taxable_amount", item.get("amount", 0) - discount))
            
            # Tax calculation
            gst_rate = float(item.get("tax_rate", item.get("gst_rate", 18)))
            is_igst = invoice.get("is_igst", False) or item.get("tax_type") == "igst"
            
            if is_igst:
                igst_amt = cls.round_amount(taxable_value * gst_rate / 100)
                cgst_amt = 0
                sgst_amt = 0
            else:
                igst_amt = 0
                cgst_amt = cls.round_amount(taxable_value * gst_rate / 200)
                sgst_amt = cls.round_amount(taxable_value * gst_rate / 200)
            
            cess_amt = cls.round_amount(item.get("cess_amount", 0))
            total_item_val = cls.round_amount(taxable_value + igst_amt + cgst_amt + sgst_amt + cess_amt)
            
            item_entry = {
                "SlNo": str(idx),
                "PrdDesc": item.get("name", item.get("description", ""))[:300],
                "IsServc": "Y" if hsn.startswith("99") else "N",  # SAC codes start with 99
                "HsnCd": hsn[:8],
                "Barcde": item.get("barcode", "")[:30] if item.get("barcode") else None,
                "Qty": quantity,
                "FreeQty": cls.round_amount(item.get("free_quantity", 0)),
                "Unit": item.get("unit", "OTH")[:8].upper(),  # Unit of measure
                "UnitPrice": unit_price,
                "TotAmt": cls.round_amount(quantity * unit_price),
                "Discount": discount,
                "PreTaxVal": None,  # Pre-tax value if applicable
                "AssAmt": taxable_value,
                "GstRt": gst_rate,
                "IgstAmt": igst_amt,
                "CgstAmt": cgst_amt,
                "SgstAmt": sgst_amt,
                "CesRt": float(item.get("cess_rate", 0)),
                "CesAmt": cess_amt,
                "CesNonAdvlAmt": 0,
                "StateCesRt": 0,
                "StateCesAmt": 0,
                "StateCesNonAdvlAmt": 0,
                "OthChrg": cls.round_amount(item.get("other_charges", 0)),
                "TotItemVal": total_item_val,
                "OrdLineRef": item.get("order_line_ref", "")[:50] if item.get("order_line_ref") else None,
                "OrgCntry": item.get("origin_country", "IN")[:2] if item.get("origin_country") else None,
                "PrdSlNo": item.get("serial_number", "")[:20] if item.get("serial_number") else None,
                "BchDtls": {
                    "Nm": item.get("batch_name", "")[:20],
                    "ExpDt": cls.format_date(item["batch_expiry"]) if item.get("batch_expiry") else None,
                    "WrDt": cls.format_date(item["warranty_date"]) if item.get("warranty_date") else None
                } if item.get("batch_name") else None,
                "AttribDtls": None  # Additional attributes if needed
            }
            
            # Remove None values
            item_entry = {k: v for k, v in item_entry.items() if v is not None}
            if item_entry.get("BchDtls"):
                item_entry["BchDtls"] = {k: v for k, v in item_entry["BchDtls"].items() if v is not None}
                if not item_entry["BchDtls"]:
                    del item_entry["BchDtls"]
            
            item_list.append(item_entry)
        
        # Calculate totals
        total_taxable = sum(cls.round_amount(item.get("AssAmt", 0)) for item in item_list)
        total_igst = sum(cls.round_amount(item.get("IgstAmt", 0)) for item in item_list)
        total_cgst = sum(cls.round_amount(item.get("CgstAmt", 0)) for item in item_list)
        total_sgst = sum(cls.round_amount(item.get("SgstAmt", 0)) for item in item_list)
        total_cess = sum(cls.round_amount(item.get("CesAmt", 0)) for item in item_list)
        total_discount = sum(cls.round_amount(item.get("Discount", 0)) for item in item_list)
        other_charges = cls.round_amount(invoice.get("other_charges", 0))
        round_off = cls.round_amount(invoice.get("round_off_amount", 0))
        
        total_invoice_value = cls.round_amount(
            total_taxable + total_igst + total_cgst + total_sgst + 
            total_cess + other_charges + round_off
        )
        
        # Build value details
        val_dtls = {
            "AssVal": total_taxable,
            "CgstVal": total_cgst,
            "SgstVal": total_sgst,
            "IgstVal": total_igst,
            "CesVal": total_cess,
            "StCesVal": 0,
            "Discount": total_discount,
            "OthChrg": other_charges,
            "RndOffAmt": round_off,
            "TotInvVal": total_invoice_value,
            "TotInvValFc": None  # Foreign currency value if applicable
        }
        
        # Build payment details (optional)
        pay_dtls = None
        if invoice.get("payment_mode"):
            pay_dtls = {
                "Nm": invoice.get("payee_name", "")[:100] if invoice.get("payee_name") else None,
                "AccDet": invoice.get("bank_account", "")[:18] if invoice.get("bank_account") else None,
                "Mode": invoice.get("payment_mode", "")[:18] if invoice.get("payment_mode") else None,
                "FinInsBr": invoice.get("bank_ifsc", "")[:11] if invoice.get("bank_ifsc") else None,
                "PayTerm": invoice.get("payment_terms", "")[:100] if invoice.get("payment_terms") else None,
                "PayInstr": invoice.get("payment_instructions", "")[:100] if invoice.get("payment_instructions") else None,
                "CrTrn": invoice.get("credit_transfer", "")[:100] if invoice.get("credit_transfer") else None,
                "DirDr": invoice.get("direct_debit", "")[:100] if invoice.get("direct_debit") else None,
                "CrDay": int(invoice.get("credit_days", 0)) if invoice.get("credit_days") else None,
                "PaidAmt": cls.round_amount(invoice.get("paid_amount", 0)) if invoice.get("paid_amount") else None,
                "PaymtDue": cls.round_amount(invoice.get("balance_due", total_invoice_value))
            }
            pay_dtls = {k: v for k, v in pay_dtls.items() if v is not None}
        
        # Build reference details (optional)
        ref_dtls = None
        if invoice.get("reference_number") or invoice.get("po_number"):
            ref_dtls = {
                "InvRm": invoice.get("remarks", "")[:100] if invoice.get("remarks") else None,
                "DocPerdDtls": {
                    "InvStDt": cls.format_date(invoice["period_start"]) if invoice.get("period_start") else None,
                    "InvEndDt": cls.format_date(invoice["period_end"]) if invoice.get("period_end") else None
                } if invoice.get("period_start") else None,
                "PrecDocDtls": [{
                    "InvNo": invoice.get("original_invoice_number", "")[:16],
                    "InvDt": cls.format_date(invoice["original_invoice_date"]) if invoice.get("original_invoice_date") else None,
                    "OthRefNo": invoice.get("reference_number", "")[:20] if invoice.get("reference_number") else None
                }] if invoice.get("original_invoice_number") else None,
                "ContrDtls": [{
                    "RecAdvRef": invoice.get("receipt_advice_ref", "")[:20] if invoice.get("receipt_advice_ref") else None,
                    "RecAdvDt": cls.format_date(invoice["receipt_advice_date"]) if invoice.get("receipt_advice_date") else None,
                    "Tendor": invoice.get("tender_ref", "")[:20] if invoice.get("tender_ref") else None,
                    "ContrRefNo": invoice.get("contract_ref", "")[:20] if invoice.get("contract_ref") else None,
                    "ExtRefr": invoice.get("external_ref", "")[:20] if invoice.get("external_ref") else None,
                    "ProjRefr": invoice.get("project_ref", "")[:20] if invoice.get("project_ref") else None,
                    "PORefr": invoice.get("po_number", "")[:16] if invoice.get("po_number") else None,
                    "PORefDt": cls.format_date(invoice["po_date"]) if invoice.get("po_date") else None
                }] if invoice.get("po_number") or invoice.get("contract_ref") else None
            }
            ref_dtls = {k: v for k, v in ref_dtls.items() if v is not None}
        
        # Build final payload
        payload = {
            "Version": "1.1",
            "TranDtls": tran_dtls,
            "DocDtls": doc_dtls,
            "SellerDtls": {k: v for k, v in seller_dtls.items() if v is not None},
            "BuyerDtls": {k: v for k, v in buyer_dtls.items() if v is not None},
            "ItemList": item_list,
            "ValDtls": val_dtls
        }
        
        if pay_dtls:
            payload["PayDtls"] = pay_dtls
        if ref_dtls:
            payload["RefDtls"] = ref_dtls
        
        # Add dispatch/ship details if different from seller
        if invoice.get("dispatch_from") and invoice.get("dispatch_from") != supplier.get("address"):
            payload["DispDtls"] = {
                "Nm": invoice.get("dispatch_name", supplier.get("name", ""))[:100],
                "Addr1": invoice.get("dispatch_address1", "")[:100],
                "Addr2": invoice.get("dispatch_address2", "")[:100] if invoice.get("dispatch_address2") else None,
                "Loc": invoice.get("dispatch_city", "")[:100],
                "Pin": int(invoice.get("dispatch_pincode", "000000")[:6]),
                "Stcd": invoice.get("dispatch_state_code", "")[:2]
            }
        
        # Add ship-to details if different from buyer
        if invoice.get("shipping_address"):
            ship_addr = invoice.get("shipping_address", {})
            payload["ShipDtls"] = {
                "Gstin": ship_addr.get("gstin", buyer.get("gstin", "URP")),
                "LglNm": ship_addr.get("name", buyer.get("name", ""))[:100],
                "TrdNm": ship_addr.get("trade_name", "")[:100] if ship_addr.get("trade_name") else None,
                "Addr1": ship_addr.get("address", "")[:100],
                "Addr2": ship_addr.get("address2", "")[:100] if ship_addr.get("address2") else None,
                "Loc": ship_addr.get("city", "")[:100],
                "Pin": int(str(ship_addr.get("zip", "000000"))[:6]),
                "Stcd": ship_addr.get("state_code", "")[:2]
            }
        
        return payload

# ==================== IRN GENERATION ====================

class IRNGenerator:
    """Handles IRN generation with IRP"""
    
    def __init__(self, org_id: str, is_sandbox: bool = True):
        self.org_id = org_id
        self.is_sandbox = is_sandbox
        self.auth_manager = IRPAuthManager(org_id, is_sandbox)
        self.base_url = EINVOICE_SANDBOX_URL if is_sandbox else EINVOICE_PRODUCTION_URL
    
    async def generate_irn(self, invoice: Dict, line_items: List[Dict],
                           supplier: Dict, buyer: Dict) -> Dict:
        """
        Generate IRN for an invoice
        
        Args:
            invoice: Invoice document
            line_items: List of line items
            supplier: Supplier/seller details
            buyer: Buyer/customer details
            
        Returns:
            Dict with IRN, acknowledgement details, signed QR data
        """
        db = get_db()
        
        # Validate invoice
        is_valid, errors = EInvoiceValidator.validate_invoice(invoice, line_items)
        if not is_valid:
            return {
                "code": 1,
                "success": False,
                "errors": errors,
                "message": "Invoice validation failed"
            }
        
        # Build payload
        payload = EInvoiceSchemaBuilder.build_payload(invoice, line_items, supplier, buyer)
        
        # Get auth token
        try:
            token, sek = await self.auth_manager.get_valid_token()
        except Exception as e:
            return {
                "code": 1,
                "success": False,
                "message": f"Authentication failed: {str(e)}"
            }
        
        # Get credentials for headers
        creds = await self.auth_manager.get_credentials()
        
        headers = {
            "Content-Type": "application/json",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "gstin": creds["gstin"],
            "user_name": creds["username"],
            "AuthToken": token,
            "Gstin": creds["gstin"]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}{ENDPOINTS['generate_irn']}",
                    json=payload,
                    headers=headers
                )
                
                response_data = response.json()
                
                if response.status_code != 200 or response_data.get("Status") != 1:
                    error_details = response_data.get("ErrorDetails", [])
                    error_messages = [e.get("ErrorMessage", "Unknown error") for e in error_details]
                    logger.error(f"IRN generation failed: {error_messages}")
                    return {
                        "code": 1,
                        "success": False,
                        "errors": error_messages,
                        "message": "IRN generation failed",
                        "response": response_data
                    }
                
                # Extract successful response
                result = response_data.get("Data", {})
                
                irn_data = {
                    "irn": result.get("Irn"),
                    "ack_no": result.get("AckNo"),
                    "ack_date": result.get("AckDt"),
                    "signed_invoice": result.get("SignedInvoice"),
                    "signed_qr_code": result.get("SignedQRCode"),
                    "status": result.get("Status"),
                    "generated_at": datetime.now(timezone.utc)
                }
                
                # Store IRN record
                irn_record = {
                    "organization_id": self.org_id,
                    "invoice_id": invoice.get("invoice_id"),
                    "invoice_number": invoice.get("invoice_number"),
                    **irn_data,
                    "payload": payload,
                    "response": response_data
                }
                
                await db.einvoice_irn.insert_one(irn_record)
                
                # Update invoice with IRN details
                await db.invoices.update_one(
                    {"invoice_id": invoice.get("invoice_id")},
                    {"$set": {
                        "irn": irn_data["irn"],
                        "irn_ack_no": irn_data["ack_no"],
                        "irn_ack_date": irn_data["ack_date"],
                        "irn_signed_qr": irn_data["signed_qr_code"],
                        "irn_status": "registered",
                        "irn_generated_at": irn_data["generated_at"]
                    }}
                )
                
                # Update journal entry narration with IRN reference
                try:
                    irn_narration = f"IRN: {irn_data['irn']} | Ack: {irn_data['ack_no']} | {irn_data['ack_date']}"
                    await db.journal_entries.update_one(
                        {
                            "source_document_id": invoice.get("invoice_id"),
                            "organization_id": self.org_id
                        },
                        {"$set": {
                            "irn_reference": irn_narration,
                            "narration": irn_narration
                        }}
                    )
                except Exception as je_error:
                    logger.warning(f"Could not update journal entry with IRN: {je_error}")
                
                logger.info(f"IRN generated successfully: {irn_data['irn']}")
                
                return {
                    "code": 0,
                    "success": True,
                    "message": "IRN generated successfully",
                    **irn_data
                }
                
            except httpx.RequestError as e:
                logger.error(f"IRN generation request error: {e}")
                return {
                    "code": 1,
                    "success": False,
                    "message": f"Failed to connect to IRP: {str(e)}"
                }
    
    async def cancel_irn(self, irn: str, reason: str, cancel_remarks: str = "") -> Dict:
        """
        Cancel an IRN within 24 hours of generation
        
        Args:
            irn: The IRN to cancel
            reason: Cancellation reason code (1=Duplicate, 2=Data entry mistake, 3=Order cancelled, 4=Other)
            cancel_remarks: Additional remarks
            
        Returns:
            Dict with cancellation status
        """
        db = get_db()
        
        # Check if IRN exists and is within 24 hours
        irn_record = await db.einvoice_irn.find_one({"irn": irn, "organization_id": self.org_id})
        if not irn_record:
            return {
                "code": 1,
                "success": False,
                "message": "IRN not found"
            }
        
        generated_at = irn_record.get("generated_at")
        if generated_at:
            if isinstance(generated_at, str):
                generated_at = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            time_diff = datetime.now(timezone.utc) - generated_at
            if time_diff > timedelta(hours=24):
                return {
                    "code": 1,
                    "success": False,
                    "message": "IRN cancellation window (24 hours) has expired"
                }
        
        # Get auth token
        try:
            token, sek = await self.auth_manager.get_valid_token()
        except Exception as e:
            return {
                "code": 1,
                "success": False,
                "message": f"Authentication failed: {str(e)}"
            }
        
        creds = await self.auth_manager.get_credentials()
        
        headers = {
            "Content-Type": "application/json",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "gstin": creds["gstin"],
            "user_name": creds["username"],
            "AuthToken": token,
            "Gstin": creds["gstin"]
        }
        
        cancel_payload = {
            "Irn": irn,
            "CnlRsn": reason,  # 1-4
            "CnlRem": cancel_remarks[:100] if cancel_remarks else ""
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}{ENDPOINTS['cancel_irn']}",
                    json=cancel_payload,
                    headers=headers
                )
                
                response_data = response.json()
                
                if response.status_code != 200 or response_data.get("Status") != 1:
                    error_details = response_data.get("ErrorDetails", [])
                    error_messages = [e.get("ErrorMessage", "Unknown error") for e in error_details]
                    return {
                        "code": 1,
                        "success": False,
                        "errors": error_messages,
                        "message": "IRN cancellation failed"
                    }
                
                result = response_data.get("Data", {})
                
                # Update IRN record
                await db.einvoice_irn.update_one(
                    {"irn": irn},
                    {"$set": {
                        "status": "cancelled",
                        "cancel_reason": reason,
                        "cancel_remarks": cancel_remarks,
                        "cancelled_at": datetime.now(timezone.utc),
                        "cancel_response": response_data
                    }}
                )
                
                # Get reason text
                reason_texts = {
                    "1": "Duplicate",
                    "2": "Data Entry Mistake",
                    "3": "Order Cancelled",
                    "4": "Other"
                }
                reason_text = reason_texts.get(reason, "Other")
                
                invoice_id = irn_record.get("invoice_id")
                
                # Update invoice status to CANCELLED (5A)
                await db.invoices.update_one(
                    {"invoice_id": invoice_id},
                    {"$set": {
                        "status": "cancelled",
                        "irn_status": "cancelled",
                        "irn_cancelled_at": datetime.now(timezone.utc).isoformat(),
                        "irn_cancel_reason": reason,
                        "irn_cancel_remarks": cancel_remarks,
                        "updated_time": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Post reversal journal entry (5A)
                invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
                if invoice:
                    try:
                        # Create reversal journal entry
                        reversal_entry = {
                            "entry_type": "IRN_CANCELLATION",
                            "organization_id": self.org_id,
                            "reference_type": "INVOICE",
                            "reference_id": invoice_id,
                            "date": datetime.now(timezone.utc).isoformat(),
                            "narration": f"IRN Cancelled: Reason: {reason_text} | Original IRN: {irn}",
                            "total_debit": invoice.get("grand_total", 0),
                            "total_credit": invoice.get("grand_total", 0),
                            "created_at": datetime.now(timezone.utc),
                            "lines": [
                                # Reverse: Credit Accounts Receivable (was debit)
                                {
                                    "account_type": "ACCOUNTS_RECEIVABLE",
                                    "debit": 0,
                                    "credit": invoice.get("grand_total", 0),
                                    "description": f"IRN Cancelled - Reversal for {invoice.get('invoice_number')}"
                                },
                                # Reverse: Debit Sales Revenue (was credit)
                                {
                                    "account_type": "SALES_REVENUE",
                                    "debit": invoice.get("sub_total", 0),
                                    "credit": 0,
                                    "description": f"IRN Cancelled - Sales Reversal"
                                },
                                # Reverse: Debit Tax Payable (was credit)
                                {
                                    "account_type": "TAX_PAYABLE",
                                    "debit": invoice.get("tax_total", 0),
                                    "credit": 0,
                                    "description": f"IRN Cancelled - Tax Reversal"
                                }
                            ]
                        }
                        await db.journal_entries.insert_one(reversal_entry)
                        logger.info(f"Posted IRN cancellation reversal journal entry for invoice {invoice.get('invoice_number')}")
                    except Exception as je:
                        logger.warning(f"Failed to post reversal journal entry: {je}")
                    
                    # Add to invoice history (5A)
                    try:
                        history_entry = {
                            "invoice_id": invoice_id,
                            "action": "irn_cancelled",
                            "details": f"IRN cancelled: {reason_text}. Original IRN: {irn}",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "user": "system"
                        }
                        await db.invoice_history.insert_one(history_entry)
                    except Exception as he:
                        logger.warning(f"Failed to add history entry: {he}")
                
                logger.info(f"IRN cancelled successfully: {irn}")
                
                return {
                    "code": 0,
                    "success": True,
                    "message": "IRN cancelled successfully",
                    "cancel_date": result.get("CancelDate")
                }
                
            except httpx.RequestError as e:
                logger.error(f"IRN cancellation request error: {e}")
                return {
                    "code": 1,
                    "success": False,
                    "message": f"Failed to connect to IRP: {str(e)}"
                }

# ==================== QR CODE GENERATION ====================

def generate_qr_code_image(signed_qr_data: str, size: int = 200) -> bytes:
    """
    Generate QR code image from signed QR data received from IRP
    
    IMPORTANT: This uses the signed QR data from IRP, NOT self-generated data.
    The QR code content is the exact signed payload from the IRP response.
    
    Args:
        signed_qr_data: The SignedQRCode field from IRP response
        size: QR code size in pixels
        
    Returns:
        PNG image bytes
    """
    if not signed_qr_data:
        raise ValueError("Signed QR data is required")
    
    qr = qrcode.QRCode(
        version=None,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(signed_qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to specified size
    img = img.resize((size, size))
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return buffer.getvalue()

def generate_qr_code_base64(signed_qr_data: str, size: int = 200) -> str:
    """
    Generate QR code as base64 string for embedding in HTML/PDF
    
    Args:
        signed_qr_data: The SignedQRCode field from IRP response
        size: QR code size in pixels
        
    Returns:
        Base64 encoded PNG image
    """
    img_bytes = generate_qr_code_image(signed_qr_data, size)
    return base64.b64encode(img_bytes).decode()

# ==================== UTILITY FUNCTIONS ====================

async def check_einvoice_eligibility(org_id: str) -> Dict:
    """
    Check if organization is eligible/configured for E-Invoicing
    
    Returns:
        Dict with eligibility status and configuration
    """
    config = await get_einvoice_config(org_id)
    
    if not config:
        return {
            "eligible": False,
            "configured": False,
            "reason": "E-Invoice not configured. Configure in Organization Settings.",
            "threshold_applicable": None
        }
    
    if not config.get("enabled"):
        return {
            "eligible": False,
            "configured": True,
            "reason": "E-Invoice is disabled for this organization",
            "threshold_applicable": config.get("turnover_threshold_met", False)
        }
    
    # Check if required credentials are present
    required = ["gstin", "irp_username", "irp_password_encrypted", "client_id", "client_secret_encrypted"]
    missing = [f for f in required if not config.get(f)]
    
    if missing:
        return {
            "eligible": False,
            "configured": True,
            "reason": f"Missing credentials: {', '.join(missing)}",
            "threshold_applicable": config.get("turnover_threshold_met", False)
        }
    
    return {
        "eligible": True,
        "configured": True,
        "gstin": config.get("gstin"),
        "is_sandbox": config.get("is_sandbox", True),
        "threshold_applicable": config.get("turnover_threshold_met", False)
    }

async def get_irn_details(org_id: str, invoice_id: str) -> Optional[Dict]:
    """Get IRN details for an invoice"""
    db = get_db()
    return await db.einvoice_irn.find_one(
        {"organization_id": org_id, "invoice_id": invoice_id},
        {"_id": 0, "payload": 0, "response": 0}
    )

async def list_irn_records(org_id: str, skip: int = 0, limit: int = 50,
                           status: str = None) -> List[Dict]:
    """List IRN records for an organization"""
    db = get_db()
    query = {"organization_id": org_id}
    if status:
        query["status"] = status
    
    cursor = db.einvoice_irn.find(
        query,
        {"_id": 0, "payload": 0, "response": 0}
    ).sort("generated_at", -1).skip(skip).limit(limit)
    
    return await cursor.to_list(length=limit)
