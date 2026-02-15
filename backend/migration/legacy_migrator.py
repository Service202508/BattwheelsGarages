"""
Legacy ERP Data Migration Module for Battwheels OS
Handles migration from Zoho Books backup to current system
"""

import pandas as pd
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_currency(value) -> float:
    """Parse currency strings like 'INR 450.00' to float"""
    if pd.isna(value) or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Remove currency code and parse
    cleaned = re.sub(r'[A-Z]{3}\s*', '', str(value)).replace(',', '').strip()
    try:
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0


def parse_date(value) -> Optional[str]:
    """Parse various date formats to ISO string"""
    if pd.isna(value) or value is None:
        return None
    try:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            # Try different formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc).isoformat()
                except:
                    continue
        return datetime.now(timezone.utc).isoformat()
    except:
        return datetime.now(timezone.utc).isoformat()


def clean_string(value) -> Optional[str]:
    """Clean and validate string values"""
    if pd.isna(value) or value is None:
        return None
    return str(value).strip() if str(value).strip() else None


def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LegacyDataMigrator:
    """Handles migration of legacy ERP data to Battwheels OS"""
    
    def __init__(self, data_dir: str, db):
        self.data_dir = Path(data_dir)
        self.db = db
        self.stats = {
            "customers": {"total": 0, "migrated": 0, "errors": 0},
            "suppliers": {"total": 0, "migrated": 0, "errors": 0},
            "inventory": {"total": 0, "migrated": 0, "errors": 0},
            "invoices": {"total": 0, "migrated": 0, "errors": 0},
            "sales_orders": {"total": 0, "migrated": 0, "errors": 0},
            "purchase_orders": {"total": 0, "migrated": 0, "errors": 0},
            "payments": {"total": 0, "migrated": 0, "errors": 0},
            "expenses": {"total": 0, "migrated": 0, "errors": 0},
            "accounts": {"total": 0, "migrated": 0, "errors": 0},
        }
        self.customer_map = {}  # Map legacy customer ID to new ID
        self.supplier_map = {}  # Map legacy vendor ID to new ID
        self.item_map = {}  # Map legacy item ID to new ID
        
    async def run_full_migration(self) -> Dict[str, Any]:
        """Run complete migration in correct order"""
        logger.info("Starting full legacy data migration...")
        
        # Order matters - dependencies first
        await self.migrate_chart_of_accounts()
        await self.migrate_customers()
        await self.migrate_suppliers()
        await self.migrate_inventory()
        await self.migrate_purchase_orders()
        await self.migrate_sales_orders()
        await self.migrate_invoices()
        await self.migrate_payments()
        await self.migrate_expenses()
        
        logger.info("Migration complete!")
        return self.stats
    
    async def migrate_chart_of_accounts(self) -> int:
        """Migrate Chart of Accounts"""
        file_path = self.data_dir / "Chart_of_Accounts.xls"
        if not file_path.exists():
            logger.warning("Chart of Accounts file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["accounts"]["total"] = len(df)
        
        for _, row in df.iterrows():
            try:
                account_doc = {
                    "account_id": clean_string(row.get('Account ID')) or generate_id("acc"),
                    "account_name": clean_string(row.get('Account Name')),
                    "account_code": clean_string(row.get('Account Code')),
                    "description": clean_string(row.get('Description')),
                    "account_type": clean_string(row.get('Account Type')),
                    "parent_account": clean_string(row.get('Parent Account')),
                    "is_active": row.get('Account Status') == 'Active',
                    "currency": clean_string(row.get('Currency')) or "INR",
                    "migrated_from": "legacy_zoho",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Check if account exists
                existing = await self.db.chart_of_accounts.find_one(
                    {"account_id": account_doc["account_id"]}, {"_id": 0}
                )
                if not existing:
                    await self.db.chart_of_accounts.insert_one(account_doc)
                    self.stats["accounts"]["migrated"] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating account: {e}")
                self.stats["accounts"]["errors"] += 1
                
        return self.stats["accounts"]["migrated"]
    
    async def migrate_customers(self) -> int:
        """Migrate Contacts as Customers"""
        file_path = self.data_dir / "Contacts.xls"
        if not file_path.exists():
            logger.warning("Contacts file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["customers"]["total"] = len(df)
        
        for _, row in df.iterrows():
            try:
                legacy_id = clean_string(row.get('Customer Number'))
                new_id = generate_id("cust")
                
                customer_doc = {
                    "customer_id": new_id,
                    "legacy_id": legacy_id,
                    "customer_number": legacy_id,
                    "display_name": clean_string(row.get('Display Name')),
                    "company_name": clean_string(row.get('Company Name')),
                    "first_name": clean_string(row.get('First Name')),
                    "last_name": clean_string(row.get('Last Name')),
                    "salutation": clean_string(row.get('Salutation')),
                    "email": clean_string(row.get('Primary Contact EmailID')) or clean_string(row.get('EmailID')),
                    "phone": clean_string(row.get('Phone')),
                    "mobile": clean_string(row.get('MobilePhone')),
                    "website": clean_string(row.get('Website')),
                    "gst_number": clean_string(row.get('GST Identification Number (GSTIN)')),
                    "gst_treatment": clean_string(row.get('GST Treatment')),
                    "pan_number": clean_string(row.get('PAN Number')),
                    "billing_address": {
                        "attention": clean_string(row.get('Billing Attention')),
                        "address": clean_string(row.get('Billing Address')),
                        "street2": clean_string(row.get('Billing Street2')),
                        "city": clean_string(row.get('Billing City')),
                        "state": clean_string(row.get('Billing State')),
                        "country": clean_string(row.get('Billing Country')),
                        "zipcode": clean_string(row.get('Billing Code')),
                        "phone": clean_string(row.get('Billing Phone')),
                    },
                    "shipping_address": {
                        "attention": clean_string(row.get('Shipping Attention')),
                        "address": clean_string(row.get('Shipping Address')),
                        "street2": clean_string(row.get('Shipping Street2')),
                        "city": clean_string(row.get('Shipping City')),
                        "state": clean_string(row.get('Shipping State')),
                        "country": clean_string(row.get('Shipping Country')),
                        "zipcode": clean_string(row.get('Shipping Code')),
                    },
                    "currency_code": clean_string(row.get('Currency Code')) or "INR",
                    "payment_terms": clean_string(row.get('Payment Terms Label')) or "Due on Receipt",
                    "credit_limit": parse_currency(row.get('Credit Limit')),
                    "opening_balance": parse_currency(row.get('Opening Balance')),
                    "outstanding_balance": parse_currency(row.get('Outstanding Receivable Amount')),
                    "notes": clean_string(row.get('Notes')),
                    "status": "active" if row.get('Status') == 'Active' else "inactive",
                    "portal_enabled": row.get('Portal Enabled') == 'Yes',
                    "created_at": parse_date(row.get('Created Time')) or datetime.now(timezone.utc).isoformat(),
                    "updated_at": parse_date(row.get('Last Modified Time')),
                    "migrated_from": "legacy_zoho"
                }
                
                # Store mapping for later use
                if legacy_id:
                    self.customer_map[legacy_id] = new_id
                display_name = customer_doc.get('display_name')
                if display_name:
                    self.customer_map[display_name] = new_id
                
                # Check if customer exists
                existing = await self.db.customers.find_one(
                    {"$or": [
                        {"legacy_id": legacy_id},
                        {"display_name": display_name}
                    ]}, {"_id": 0}
                )
                if not existing:
                    await self.db.customers.insert_one(customer_doc)
                    self.stats["customers"]["migrated"] += 1
                else:
                    self.customer_map[legacy_id] = existing.get("customer_id")
                    if display_name:
                        self.customer_map[display_name] = existing.get("customer_id")
                    
            except Exception as e:
                logger.error(f"Error migrating customer: {e}")
                self.stats["customers"]["errors"] += 1
                
        return self.stats["customers"]["migrated"]
    
    async def migrate_suppliers(self) -> int:
        """Migrate Vendors as Suppliers"""
        file_path = self.data_dir / "Vendors.xls"
        if not file_path.exists():
            logger.warning("Vendors file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["suppliers"]["total"] = len(df)
        
        for _, row in df.iterrows():
            try:
                legacy_id = clean_string(row.get('Contact ID'))
                new_id = generate_id("sup")
                
                first_name = clean_string(row.get('First Name')) or ""
                last_name = clean_string(row.get('Last Name')) or ""
                contact_person = f"{first_name} {last_name}".strip() if first_name or last_name else None
                
                supplier_doc = {
                    "supplier_id": new_id,
                    "legacy_id": legacy_id,
                    "name": clean_string(row.get('Display Name')) or clean_string(row.get('Company Name')),
                    "company_name": clean_string(row.get('Company Name')),
                    "contact_person": contact_person,
                    "salutation": clean_string(row.get('Salutation')),
                    "first_name": clean_string(row.get('First Name')),
                    "last_name": clean_string(row.get('Last Name')),
                    "email": clean_string(row.get('EmailID')),
                    "phone": clean_string(row.get('Phone')),
                    "mobile": clean_string(row.get('MobilePhone')),
                    "website": clean_string(row.get('Website')),
                    "gst_number": clean_string(row.get('GST Identification Number (GSTIN)')),
                    "gst_treatment": clean_string(row.get('GST Treatment')),
                    "pan_number": clean_string(row.get('PAN Number')),
                    "source_of_supply": clean_string(row.get('Source of Supply')),
                    "address": clean_string(row.get('Billing Address')),
                    "billing_address": {
                        "attention": clean_string(row.get('Billing Attention')),
                        "address": clean_string(row.get('Billing Address')),
                        "city": clean_string(row.get('Billing City')),
                        "state": clean_string(row.get('Billing State')),
                        "country": clean_string(row.get('Billing Country')),
                        "zipcode": clean_string(row.get('Billing Code')),
                    },
                    "currency_code": clean_string(row.get('Currency Code')) or "INR",
                    "payment_terms": clean_string(row.get('Payment Terms Label')) or "net_30",
                    "opening_balance": parse_currency(row.get('Opening Balance')),
                    "outstanding_balance": parse_currency(row.get('Outstanding Payable Amount')),
                    "notes": clean_string(row.get('Notes')),
                    "category": "parts",  # Default, can be updated
                    "rating": 0.0,
                    "total_orders": 0,
                    "total_value": 0.0,
                    "is_active": row.get('Status') == 'Active',
                    "created_at": parse_date(row.get('Created Time')) or datetime.now(timezone.utc).isoformat(),
                    "updated_at": parse_date(row.get('Last Modified Time')),
                    "migrated_from": "legacy_zoho"
                }
                
                # Store mapping
                if legacy_id:
                    self.supplier_map[legacy_id] = new_id
                display_name = supplier_doc.get('name')
                if display_name:
                    self.supplier_map[display_name] = new_id
                
                # Check if supplier exists
                existing = await self.db.suppliers.find_one(
                    {"$or": [
                        {"legacy_id": legacy_id},
                        {"name": display_name}
                    ]}, {"_id": 0}
                )
                if not existing:
                    await self.db.suppliers.insert_one(supplier_doc)
                    self.stats["suppliers"]["migrated"] += 1
                else:
                    self.supplier_map[legacy_id] = existing.get("supplier_id")
                    if display_name:
                        self.supplier_map[display_name] = existing.get("supplier_id")
                    
            except Exception as e:
                logger.error(f"Error migrating supplier: {e}")
                self.stats["suppliers"]["errors"] += 1
                
        return self.stats["suppliers"]["migrated"]
    
    async def migrate_inventory(self) -> int:
        """Migrate Items as Inventory"""
        file_path = self.data_dir / "Item.xls"
        if not file_path.exists():
            logger.warning("Item file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["inventory"]["total"] = len(df)
        
        for _, row in df.iterrows():
            try:
                legacy_id = clean_string(row.get('Item ID'))
                new_id = generate_id("inv")
                
                # Map category from account
                account = clean_string(row.get('Account')) or "Sales"
                category = self._map_item_category(row.get('Item Type'), account)
                
                # Get vendor reference
                vendor_name = clean_string(row.get('Vendor'))
                supplier_id = self.supplier_map.get(vendor_name) if vendor_name else None
                
                item_doc = {
                    "item_id": new_id,
                    "legacy_id": legacy_id,
                    "name": clean_string(row.get('Item Name')),
                    "sku": clean_string(row.get('SKU')),
                    "hsn_sac": clean_string(row.get('HSN/SAC')),
                    "description": clean_string(row.get('Description')),
                    "category": category,
                    "item_type": clean_string(row.get('Item Type')) or "goods",
                    "unit": clean_string(row.get('Unit Name')) or clean_string(row.get('Usage unit')) or "pcs",
                    "unit_price": parse_currency(row.get('Rate')),
                    "cost_price": parse_currency(row.get('Purchase Rate')),
                    "quantity": int(row.get('Stock On Hand') or 0) if pd.notna(row.get('Stock On Hand')) else 0,
                    "reserved_quantity": 0,
                    "min_stock_level": int(row.get('Reorder Point') or 0) if pd.notna(row.get('Reorder Point')) else 5,
                    "max_stock_level": 1000,
                    "reorder_quantity": 10,
                    "opening_stock": int(row.get('Opening Stock') or 0) if pd.notna(row.get('Opening Stock')) else 0,
                    "opening_stock_value": parse_currency(row.get('Opening Stock Value')),
                    "sales_account": clean_string(row.get('Account')),
                    "sales_account_code": clean_string(row.get('Account Code')),
                    "purchase_account": clean_string(row.get('Purchase Account')),
                    "purchase_account_code": clean_string(row.get('Purchase Account Code')),
                    "inventory_account": clean_string(row.get('Inventory Account')),
                    "inventory_account_code": clean_string(row.get('Inventory Account Code')),
                    "tax_name": clean_string(row.get('Intra State Tax Name')),
                    "tax_rate": parse_currency(row.get('Intra State Tax Rate')),
                    "is_taxable": row.get('Taxable') == 'Taxable',
                    "is_sellable": row.get('Sellable') == 'true',
                    "is_purchasable": row.get('Purchasable') == 'true',
                    "track_inventory": row.get('Track Inventory') == 'true',
                    "supplier_id": supplier_id,
                    "supplier_name": vendor_name,
                    "location": clean_string(row.get('Location Name')) or "Main Warehouse",
                    "status": "active" if row.get('Status') == 'Active' else "inactive",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "migrated_from": "legacy_zoho"
                }
                
                # Store mapping
                if legacy_id:
                    self.item_map[legacy_id] = new_id
                item_name = item_doc.get('name')
                if item_name:
                    self.item_map[item_name] = new_id
                
                # Check if item exists
                existing = await self.db.inventory.find_one(
                    {"$or": [
                        {"legacy_id": legacy_id},
                        {"name": item_name, "sku": item_doc.get('sku')}
                    ]}, {"_id": 0}
                )
                if not existing:
                    await self.db.inventory.insert_one(item_doc)
                    self.stats["inventory"]["migrated"] += 1
                else:
                    self.item_map[legacy_id] = existing.get("item_id")
                    if item_name:
                        self.item_map[item_name] = existing.get("item_id")
                    
            except Exception as e:
                logger.error(f"Error migrating inventory item: {e}")
                self.stats["inventory"]["errors"] += 1
                
        return self.stats["inventory"]["migrated"]
    
    def _map_item_category(self, item_type: str, account: str) -> str:
        """Map legacy item type/account to category"""
        item_type = str(item_type).lower() if item_type else ""
        account = str(account).lower() if account else ""
        
        if 'battery' in item_type or 'battery' in account:
            return "battery"
        elif 'motor' in item_type:
            return "motor"
        elif 'charging' in item_type:
            return "charging_equipment"
        elif 'service' in item_type:
            return "services"
        elif 'tool' in item_type:
            return "tools"
        else:
            return "parts"
    
    async def migrate_purchase_orders(self) -> int:
        """Migrate Purchase Orders"""
        file_path = self.data_dir / "Purchase_Order.xls"
        if not file_path.exists():
            logger.warning("Purchase Order file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["purchase_orders"]["total"] = len(df)
        
        # Group by PO ID since each line item is a separate row
        grouped = df.groupby('Purchase Order ID')
        
        for po_id, group in grouped:
            try:
                first_row = group.iloc[0]
                
                # Get supplier reference
                vendor_name = clean_string(first_row.get('Vendor Name'))
                supplier_id = self.supplier_map.get(vendor_name) if vendor_name else None
                
                # Build line items
                items = []
                subtotal = 0
                for _, row in group.iterrows():
                    item_name = clean_string(row.get('Item Name'))
                    quantity = int(row.get('Quantity') or 0) if pd.notna(row.get('Quantity')) else 0
                    rate = parse_currency(row.get('Rate'))
                    item_total = parse_currency(row.get('Item Total'))
                    
                    items.append({
                        "item_id": self.item_map.get(item_name),
                        "item_name": item_name,
                        "description": clean_string(row.get('Item Desc')),
                        "hsn_sac": clean_string(row.get('HSN/SAC')),
                        "quantity": quantity,
                        "unit_price": rate,
                        "total_price": item_total,
                        "received_quantity": 0,
                        "tax_name": clean_string(row.get('Item Tax Name')),
                        "tax_rate": parse_currency(row.get('Item Tax %')),
                        "tax_amount": parse_currency(row.get('Item Tax Amount')),
                    })
                    subtotal += item_total
                
                # Map status
                legacy_status = clean_string(first_row.get('Purchase Order Status')) or "Draft"
                status_map = {
                    "Draft": "draft",
                    "Open": "approved",
                    "Billed": "received",
                    "Closed": "received",
                    "Cancelled": "cancelled"
                }
                status = status_map.get(legacy_status, "draft")
                
                po_doc = {
                    "po_id": generate_id("po"),
                    "legacy_id": clean_string(po_id),
                    "po_number": clean_string(first_row.get('Purchase Order Number')),
                    "reference_number": clean_string(first_row.get('Reference#')),
                    "supplier_id": supplier_id,
                    "supplier_name": vendor_name,
                    "order_date": parse_date(first_row.get('Purchase Order Date')),
                    "delivery_date": parse_date(first_row.get('Delivery Date')),
                    "items": items,
                    "subtotal": subtotal,
                    "tax_amount": parse_currency(first_row.get('Tax Total')),
                    "total_amount": parse_currency(first_row.get('Total')),
                    "status": status,
                    "approval_status": "approved" if status != "draft" else "pending",
                    "currency_code": clean_string(first_row.get('Currency Code')) or "INR",
                    "exchange_rate": parse_currency(first_row.get('Exchange Rate')) or 1.0,
                    "gst_treatment": clean_string(first_row.get('GST Treatment')),
                    "destination_of_supply": clean_string(first_row.get('Destination of Supply')),
                    "source_of_supply": clean_string(first_row.get('Source of Supply')),
                    "delivery_instructions": clean_string(first_row.get('Delivery Instructions')),
                    "notes": clean_string(first_row.get('Notes')),
                    "location_name": clean_string(first_row.get('Location Name')),
                    "created_by": "migration",
                    "created_at": parse_date(first_row.get('Purchase Order Date')) or datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "migrated_from": "legacy_zoho"
                }
                
                # Check if exists
                existing = await self.db.purchase_orders.find_one(
                    {"legacy_id": clean_string(po_id)}, {"_id": 0}
                )
                if not existing:
                    await self.db.purchase_orders.insert_one(po_doc)
                    self.stats["purchase_orders"]["migrated"] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating PO {po_id}: {e}")
                self.stats["purchase_orders"]["errors"] += 1
                
        return self.stats["purchase_orders"]["migrated"]
    
    async def migrate_sales_orders(self) -> int:
        """Migrate Sales Orders"""
        file_path = self.data_dir / "Sales_Order.xls"
        if not file_path.exists():
            logger.warning("Sales Order file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["sales_orders"]["total"] = len(df)
        
        # Group by SO ID
        grouped = df.groupby('SalesOrder ID')
        
        for so_id, group in grouped:
            try:
                first_row = group.iloc[0]
                
                # Get customer reference
                customer_name = clean_string(first_row.get('Customer Name'))
                customer_id = self.customer_map.get(customer_name) if customer_name else None
                
                # Build line items
                items = []
                parts = []
                services = []
                parts_total = 0
                services_total = 0
                
                for _, row in group.iterrows():
                    item_name = clean_string(row.get('Item Name'))
                    quantity = int(row.get('Quantity') or 0) if pd.notna(row.get('Quantity')) else 0
                    rate = parse_currency(row.get('Rate'))
                    item_total = parse_currency(row.get('Item Total'))
                    
                    item_data = {
                        "item_id": self.item_map.get(item_name),
                        "item_name": item_name,
                        "description": clean_string(row.get('Item Desc')),
                        "hsn_sac": clean_string(row.get('HSN/SAC')),
                        "quantity": quantity,
                        "unit_price": rate,
                        "total_price": item_total,
                        "discount": parse_currency(row.get('Discount')),
                        "discount_amount": parse_currency(row.get('Discount Amount')),
                        "tax_name": clean_string(row.get('Tax Name')),
                        "tax_rate": parse_currency(row.get('Item Tax %')),
                        "tax_amount": parse_currency(row.get('Item Tax Amount')),
                    }
                    
                    items.append(item_data)
                    
                    # Categorize as part or service
                    item_type = clean_string(row.get('Item Type'))
                    if item_type and 'service' in item_type.lower():
                        services.append(item_data)
                        services_total += item_total
                    else:
                        parts.append(item_data)
                        parts_total += item_total
                
                # Map status
                legacy_status = clean_string(first_row.get('Status')) or "draft"
                status_map = {
                    "draft": "draft",
                    "open": "approved",
                    "confirmed": "approved",
                    "invoiced": "invoiced",
                    "partially_invoiced": "approved",
                    "void": "cancelled",
                    "closed": "completed"
                }
                status = status_map.get(legacy_status.lower(), "draft")
                
                so_doc = {
                    "sales_id": generate_id("sal"),
                    "legacy_id": clean_string(so_id),
                    "sales_number": clean_string(first_row.get('SalesOrder Number')),
                    "reference_number": clean_string(first_row.get('Reference#')),
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "customer_number": clean_string(first_row.get('Customer Number')),
                    "ticket_id": None,  # Will need manual linking
                    "vehicle_id": None,  # Will need manual linking
                    "vehicle_number": clean_string(first_row.get('CF.VEHICLE NUMBER')),
                    "order_date": parse_date(first_row.get('Order Date')),
                    "expected_shipment_date": parse_date(first_row.get('Expected Shipment Date')),
                    "items": items,
                    "services": services,
                    "parts": parts,
                    "parts_total": parts_total,
                    "services_total": services_total,
                    "labor_charges": 0.0,
                    "subtotal": parse_currency(first_row.get('SubTotal')),
                    "discount_percent": parse_currency(first_row.get('Entity Discount Percent')),
                    "discount_amount": parse_currency(first_row.get('Discount Total')),
                    "tax_amount": parse_currency(first_row.get('Tax Total')),
                    "cgst": parse_currency(first_row.get('CGST')),
                    "sgst": parse_currency(first_row.get('SGST')),
                    "igst": parse_currency(first_row.get('IGST')),
                    "total_amount": parse_currency(first_row.get('Total')),
                    "balance": parse_currency(first_row.get('Balance')),
                    "status": status,
                    "custom_status": clean_string(first_row.get('Custom Status')),
                    "approval_status": "approved" if status != "draft" else "pending",
                    "currency_code": clean_string(first_row.get('Currency Code')) or "INR",
                    "exchange_rate": parse_currency(first_row.get('Exchange Rate')) or 1.0,
                    "gst_treatment": clean_string(first_row.get('GST Treatment')),
                    "place_of_supply": clean_string(first_row.get('Place of Supply')),
                    "billing_address": {
                        "attention": clean_string(first_row.get('Billing Attention')),
                        "address": clean_string(first_row.get('Billing Address')),
                        "city": clean_string(first_row.get('Billing City')),
                        "state": clean_string(first_row.get('Billing State')),
                        "country": clean_string(first_row.get('Billing Country')),
                        "zipcode": clean_string(first_row.get('Billing Code')),
                    },
                    "shipping_address": {
                        "attention": clean_string(first_row.get('Shipping Attention')),
                        "address": clean_string(first_row.get('Shipping Address')),
                        "city": clean_string(first_row.get('Shipping City')),
                        "state": clean_string(first_row.get('Shipping State')),
                        "country": clean_string(first_row.get('Shipping Country')),
                        "zipcode": clean_string(first_row.get('Shipping Code')),
                    },
                    "salesperson": clean_string(first_row.get('SalesPerson')),
                    "notes": clean_string(first_row.get('Notes')),
                    "terms_conditions": clean_string(first_row.get('Terms & Conditions')),
                    "location_name": clean_string(first_row.get('Location Name')),
                    "created_by": "migration",
                    "created_at": parse_date(first_row.get('Order Date')) or datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "migrated_from": "legacy_zoho"
                }
                
                # Check if exists
                existing = await self.db.sales_orders.find_one(
                    {"legacy_id": clean_string(so_id)}, {"_id": 0}
                )
                if not existing:
                    await self.db.sales_orders.insert_one(so_doc)
                    self.stats["sales_orders"]["migrated"] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating SO {so_id}: {e}")
                self.stats["sales_orders"]["errors"] += 1
                
        return self.stats["sales_orders"]["migrated"]
    
    async def migrate_invoices(self) -> int:
        """Migrate Invoices from both files"""
        invoice_files = [
            self.data_dir / "invoice_data" / "Invoice00.xls",
            self.data_dir / "invoice_data" / "Invoice01.xls"
        ]
        
        total_migrated = 0
        
        for file_path in invoice_files:
            if not file_path.exists():
                logger.warning(f"Invoice file not found: {file_path}")
                continue
                
            df = pd.read_excel(file_path)
            self.stats["invoices"]["total"] += len(df)
            
            # Group by Invoice ID
            grouped = df.groupby('Invoice ID')
            
            for inv_id, group in grouped:
                try:
                    first_row = group.iloc[0]
                    
                    # Get customer reference
                    customer_name = clean_string(first_row.get('Customer Name'))
                    customer_id = self.customer_map.get(customer_name) if customer_name else None
                    
                    # Build line items
                    line_items = []
                    for _, row in group.iterrows():
                        item_name = clean_string(row.get('Item Name'))
                        quantity = int(row.get('Quantity') or 0) if pd.notna(row.get('Quantity')) else 0
                        rate = parse_currency(row.get('Item Price'))
                        item_total = parse_currency(row.get('Item Total'))
                        
                        line_items.append({
                            "item_id": self.item_map.get(item_name),
                            "item_name": item_name,
                            "description": clean_string(row.get('Item Desc')),
                            "hsn_sac": clean_string(row.get('HSN/SAC')),
                            "quantity": quantity,
                            "rate": rate,
                            "amount": item_total,
                            "discount": parse_currency(row.get('Discount')),
                            "discount_amount": parse_currency(row.get('Discount Amount')),
                            "tax_name": clean_string(row.get('Item Tax')),
                            "tax_rate": parse_currency(row.get('Item Tax %')),
                            "tax_amount": parse_currency(row.get('Item Tax Amount')),
                            "cgst": parse_currency(row.get('CGST')),
                            "sgst": parse_currency(row.get('SGST')),
                            "igst": parse_currency(row.get('IGST')),
                        })
                    
                    # Map status
                    legacy_status = clean_string(first_row.get('Invoice Status')) or "Draft"
                    status_map = {
                        "Draft": "draft",
                        "Sent": "sent",
                        "Viewed": "sent",
                        "Overdue": "overdue",
                        "Partially Paid": "partially_paid",
                        "Paid": "paid",
                        "Closed": "paid",
                        "Void": "cancelled"
                    }
                    status = status_map.get(legacy_status, "draft")
                    
                    # Calculate payment status
                    total = parse_currency(first_row.get('Total'))
                    balance = parse_currency(first_row.get('Balance'))
                    if balance <= 0:
                        payment_status = "paid"
                    elif balance < total:
                        payment_status = "partial"
                    else:
                        payment_status = "unpaid"
                    
                    invoice_doc = {
                        "invoice_id": generate_id("inv"),
                        "legacy_id": clean_string(inv_id),
                        "invoice_number": clean_string(first_row.get('Invoice Number')),
                        "customer_id": customer_id,
                        "customer_name": customer_name,
                        "customer_email": clean_string(first_row.get('Primary Contact EmailID')),
                        "customer_phone": clean_string(first_row.get('Primary Contact Phone')),
                        "ticket_id": None,  # Will need manual linking
                        "vehicle_id": None,
                        "vehicle_number": clean_string(first_row.get('CF.VEHICLE NUMBER')),
                        "vehicle_details": clean_string(first_row.get('CF.VEHICLE NUMBER')),
                        "sales_id": None,  # Link to SO if available
                        "sales_order_number": clean_string(first_row.get('Sales Order Number')),
                        "invoice_date": parse_date(first_row.get('Invoice Date')),
                        "due_date": parse_date(first_row.get('Due Date')),
                        "line_items": line_items,
                        "subtotal": parse_currency(first_row.get('SubTotal')),
                        "discount_type": clean_string(first_row.get('Discount Type')),
                        "discount_percent": parse_currency(first_row.get('Entity Discount Percent')),
                        "discount_amount": parse_currency(first_row.get('Entity Discount Amount')),
                        "tax_rate": 18.0,  # Default GST
                        "tax_amount": parse_currency(first_row.get('Tax Total')),
                        "cgst": parse_currency(first_row.get('CGST Total')),
                        "sgst": parse_currency(first_row.get('SGST Total')),
                        "igst": parse_currency(first_row.get('IGST Total')),
                        "cess": parse_currency(first_row.get('CESS Total')),
                        "tds_amount": parse_currency(first_row.get('TDS Amount')),
                        "tcs_amount": parse_currency(first_row.get('TCS Amount')),
                        "shipping_charge": parse_currency(first_row.get('Shipping Charge')),
                        "adjustment": parse_currency(first_row.get('Adjustment')),
                        "adjustment_description": clean_string(first_row.get('Adjustment Description')),
                        "round_off": parse_currency(first_row.get('Round Off')),
                        "total_amount": total,
                        "amount_paid": total - balance,
                        "balance_due": balance,
                        "status": status,
                        "payment_status": payment_status,
                        "currency_code": clean_string(first_row.get('Currency Code')) or "INR",
                        "exchange_rate": parse_currency(first_row.get('Exchange Rate')) or 1.0,
                        "gst_treatment": clean_string(first_row.get('GST Treatment')),
                        "gst_number": clean_string(first_row.get('GST Identification Number (GSTIN)')),
                        "place_of_supply": clean_string(first_row.get('Place of Supply')),
                        "billing_address": {
                            "attention": clean_string(first_row.get('Billing Attention')),
                            "address": clean_string(first_row.get('Billing Address')),
                            "street2": clean_string(first_row.get('Billing Street2')),
                            "city": clean_string(first_row.get('Billing City')),
                            "state": clean_string(first_row.get('Billing State')),
                            "country": clean_string(first_row.get('Billing Country')),
                            "zipcode": clean_string(first_row.get('Billing Code')),
                            "phone": clean_string(first_row.get('Billing Phone')),
                        },
                        "shipping_address": {
                            "attention": clean_string(first_row.get('Shipping Attention')),
                            "address": clean_string(first_row.get('Shipping Address')),
                            "city": clean_string(first_row.get('Shipping City')),
                            "state": clean_string(first_row.get('Shipping State')),
                            "country": clean_string(first_row.get('Shipping Country')),
                            "zipcode": clean_string(first_row.get('Shipping Code')),
                        },
                        "payment_terms": clean_string(first_row.get('Payment Terms Label')),
                        "salesperson": clean_string(first_row.get('Sales person')),
                        "notes": clean_string(first_row.get('Notes')),
                        "terms_conditions": clean_string(first_row.get('Terms & Conditions')),
                        "subject": clean_string(first_row.get('Subject')),
                        "location_name": clean_string(first_row.get('Location Name')),
                        "e_waybill_number": clean_string(first_row.get('E-WayBill Number')),
                        "e_waybill_status": clean_string(first_row.get('E-WayBill Status')),
                        "last_payment_date": parse_date(first_row.get('Last Payment Date')),
                        "created_by": "migration",
                        "created_at": parse_date(first_row.get('Invoice Date')) or datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "paid_date": parse_date(first_row.get('Last Payment Date')) if payment_status == "paid" else None,
                        "migrated_from": "legacy_zoho"
                    }
                    
                    # Check if exists
                    existing = await self.db.invoices.find_one(
                        {"legacy_id": clean_string(inv_id)}, {"_id": 0}
                    )
                    if not existing:
                        await self.db.invoices.insert_one(invoice_doc)
                        self.stats["invoices"]["migrated"] += 1
                        total_migrated += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating invoice {inv_id}: {e}")
                    self.stats["invoices"]["errors"] += 1
                    
        return total_migrated
    
    async def migrate_payments(self) -> int:
        """Migrate Customer Payments"""
        file_path = self.data_dir / "Customer_Payment.xls"
        if not file_path.exists():
            logger.warning("Customer Payment file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["payments"]["total"] = len(df)
        
        for _, row in df.iterrows():
            try:
                # Get customer reference
                customer_name = clean_string(row.get('Customer Name'))
                customer_id = self.customer_map.get(customer_name) if customer_name else None
                
                payment_doc = {
                    "payment_id": generate_id("pay"),
                    "legacy_id": clean_string(row.get('CustomerPayment ID')),
                    "payment_number": clean_string(row.get('Payment Number')),
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "invoice_id": None,  # Will need linking
                    "invoice_number": clean_string(row.get('Invoice Number')),
                    "amount": parse_currency(row.get('Amount')),
                    "unused_amount": parse_currency(row.get('Unused Amount')),
                    "bank_charges": parse_currency(row.get('Bank Charges')),
                    "payment_method": clean_string(row.get('Mode')) or "cash",
                    "reference_number": clean_string(row.get('Reference Number')),
                    "description": clean_string(row.get('Description')),
                    "account_name": clean_string(row.get('Account Name')),
                    "account_code": clean_string(row.get('Account Code')),
                    "currency_code": clean_string(row.get('Currency Code')) or "INR",
                    "exchange_rate": parse_currency(row.get('Exchange Rate')) or 1.0,
                    "payment_date": parse_date(row.get('Payment Date')) or datetime.now(timezone.utc).isoformat(),
                    "received_by": "migration",
                    "notes": clean_string(row.get('Notes')),
                    "migrated_from": "legacy_zoho"
                }
                
                # Check if exists
                existing = await self.db.payments.find_one(
                    {"legacy_id": payment_doc["legacy_id"]}, {"_id": 0}
                )
                if not existing:
                    await self.db.payments.insert_one(payment_doc)
                    self.stats["payments"]["migrated"] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating payment: {e}")
                self.stats["payments"]["errors"] += 1
                
        return self.stats["payments"]["migrated"]
    
    async def migrate_expenses(self) -> int:
        """Migrate Expenses"""
        file_path = self.data_dir / "Expense.xls"
        if not file_path.exists():
            logger.warning("Expense file not found")
            return 0
            
        df = pd.read_excel(file_path)
        self.stats["expenses"]["total"] = len(df)
        
        for _, row in df.iterrows():
            try:
                # Get vendor reference
                vendor_name = clean_string(row.get('Vendor'))
                supplier_id = self.supplier_map.get(vendor_name) if vendor_name else None
                
                expense_doc = {
                    "expense_id": generate_id("exp"),
                    "legacy_id": clean_string(row.get('Entry Number')),
                    "expense_date": parse_date(row.get('Expense Date')),
                    "description": clean_string(row.get('Expense Description')),
                    "expense_account": clean_string(row.get('Expense Account')),
                    "expense_account_code": clean_string(row.get('Expense Account Code')),
                    "paid_through": clean_string(row.get('Paid Through')),
                    "paid_through_code": clean_string(row.get('Paid Through Account Code')),
                    "vendor_id": supplier_id,
                    "vendor_name": vendor_name,
                    "amount": parse_currency(row.get('Total')),
                    "subtotal": parse_currency(row.get('Sub Total')),
                    "tax_amount": parse_currency(row.get('Tax Amount')),
                    "cgst": parse_currency(row.get('CGST')),
                    "sgst": parse_currency(row.get('SGST')),
                    "igst": parse_currency(row.get('IGST')),
                    "hsn_sac": clean_string(row.get('HSN/SAC')),
                    "gst_treatment": clean_string(row.get('GST Treatment')),
                    "gst_number": clean_string(row.get('GST Identification Number (GSTIN)')),
                    "currency_code": clean_string(row.get('Currency Code')) or "INR",
                    "exchange_rate": parse_currency(row.get('Exchange Rate')) or 1.0,
                    "reference_number": clean_string(row.get('Reference Number')),
                    "is_billable": row.get('Is Billable') == 'Yes',
                    "customer_name": clean_string(row.get('Customer Name')),
                    "project_name": clean_string(row.get('Project Name')),
                    "location_name": clean_string(row.get('Location Name')),
                    "is_inclusive_tax": row.get('Is Inclusive Tax') == 'true',
                    "created_by": "migration",
                    "created_at": parse_date(row.get('Expense Date')) or datetime.now(timezone.utc).isoformat(),
                    "migrated_from": "legacy_zoho"
                }
                
                # Check if exists
                existing = await self.db.expenses.find_one(
                    {"legacy_id": expense_doc["legacy_id"]}, {"_id": 0}
                )
                if not existing:
                    await self.db.expenses.insert_one(expense_doc)
                    self.stats["expenses"]["migrated"] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating expense: {e}")
                self.stats["expenses"]["errors"] += 1
                
        return self.stats["expenses"]["migrated"]
