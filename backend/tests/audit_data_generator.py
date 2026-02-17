#!/usr/bin/env python3
"""
Comprehensive Production Audit & Test Data Generator for Battwheels OS
Generates 1000+ items, 500+ contacts, 200+ estimates with full workflow simulations
"""

import asyncio
import random
import string
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Indian states for GSTIN
INDIAN_STATES = {
    '01': 'Jammu & Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab', '04': 'Chandigarh',
    '05': 'Uttarakhand', '06': 'Haryana', '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh',
    '10': 'Bihar', '11': 'Sikkim', '12': 'Arunachal Pradesh', '13': 'Nagaland', '14': 'Manipur',
    '15': 'Mizoram', '16': 'Tripura', '17': 'Meghalaya', '18': 'Assam', '19': 'West Bengal',
    '20': 'Jharkhand', '21': 'Odisha', '22': 'Chhattisgarh', '23': 'Madhya Pradesh',
    '24': 'Gujarat', '27': 'Maharashtra', '29': 'Karnataka', '32': 'Kerala', '33': 'Tamil Nadu',
    '36': 'Telangana', '37': 'Andhra Pradesh'
}

def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def generate_gstin(state_code: str = None) -> str:
    if not state_code:
        state_code = random.choice(list(INDIAN_STATES.keys()))
    pan = ''.join(random.choices(string.ascii_uppercase, k=5)) + ''.join(random.choices(string.digits, k=4)) + random.choice(string.ascii_uppercase)
    entity = random.choice(['1', '2', '3', '4'])
    check = random.choice(string.ascii_uppercase + string.digits)
    return f"{state_code}{pan}{entity}Z{check}"

def generate_phone():
    return f"+91{''.join(random.choices(string.digits, k=10))}"

def generate_email(name: str):
    domain = random.choice(['gmail.com', 'yahoo.com', 'company.in', 'business.com'])
    return f"{name.lower().replace(' ', '.')}@{domain}"

class AuditDataGenerator:
    def __init__(self):
        self.client = None
        self.db = None
        self.created_items = []
        self.created_contacts = []
        self.created_estimates = []
        self.created_sales_orders = []
        self.created_invoices = []
        self.created_bills = []
        self.created_warehouses = []
        
    async def connect(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        print(f"Connected to MongoDB: {DB_NAME}")
        
    async def close(self):
        if self.client:
            self.client.close()
    
    async def generate_warehouses(self, count: int = 5):
        """Generate additional warehouses for multi-location inventory"""
        print(f"\n📦 Generating {count} warehouses...")
        warehouses_col = self.db['warehouses']
        
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad', 'Kolkata', 'Ahmedabad']
        
        for i in range(count):
            warehouse = {
                "warehouse_id": generate_id("WH"),
                "name": f"Warehouse {cities[i % len(cities)]}",
                "code": f"WH-{cities[i % len(cities)][:3].upper()}-{i+1:02d}",
                "address": f"{random.randint(1, 500)} Industrial Area",
                "city": cities[i % len(cities)],
                "state": random.choice(['Maharashtra', 'Karnataka', 'Delhi', 'Tamil Nadu']),
                "pincode": f"{random.randint(400001, 600099)}",
                "is_primary": i == 0,
                "is_active": True,
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            await warehouses_col.insert_one(warehouse)
            self.created_warehouses.append(warehouse)
        
        print(f"   ✅ Created {count} warehouses")
        return self.created_warehouses
    
    async def generate_items(self, count: int = 200):
        """Generate diverse items with variants, bundles, and stock"""
        print(f"\n📦 Generating {count} items with variants and bundles...")
        items_col = self.db['items']
        variants_col = self.db['item_variants']
        bundles_col = self.db['item_bundles']
        stock_col = self.db['item_stock_locations']
        
        categories = ['Engine Parts', 'Battery Components', 'Motor Parts', 'Electrical', 'Body Parts', 'Accessories', 'Fluids', 'Tools']
        units = ['pcs', 'kg', 'ltr', 'set', 'box', 'unit']
        
        base_items = []
        
        for i in range(count):
            item_type = random.choices(['inventory', 'non_inventory', 'service'], weights=[70, 20, 10])[0]
            category = random.choice(categories)
            
            item = {
                "item_id": generate_id("ITEM"),
                "name": f"{category} - {random.choice(['Premium', 'Standard', 'Basic', 'Pro', 'Elite'])} {i+1}",
                "sku": f"SKU-{category[:3].upper()}-{i+1:05d}",
                "description": f"High quality {category.lower()} for EV applications",
                "item_type": item_type,
                "unit": random.choice(units),
                "purchase_rate": round(random.uniform(100, 5000), 2),
                "sales_rate": round(random.uniform(150, 7500), 2),
                "tax_id": "GST18",
                "tax_percentage": random.choice([5, 12, 18, 28]),
                "hsn_code": f"{random.randint(8400, 8550)}{random.randint(10, 99)}",
                "track_inventory": item_type == 'inventory',
                "reorder_level": random.randint(5, 50) if item_type == 'inventory' else 0,
                "status": "active",
                "category": category,
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await items_col.insert_one(item)
            base_items.append(item)
            self.created_items.append(item)
            
            # Create stock locations for inventory items
            if item_type == 'inventory' and self.created_warehouses:
                for wh in self.created_warehouses[:3]:
                    stock = {
                        "location_id": generate_id("LOC"),
                        "item_id": item["item_id"],
                        "warehouse_id": wh["warehouse_id"],
                        "available_stock": random.randint(0, 100),
                        "reserved_stock": random.randint(0, 10),
                        "created_time": datetime.now(timezone.utc).isoformat()
                    }
                    await stock_col.insert_one(stock)
            
            # Create variants for some items (20%)
            if random.random() < 0.2 and item_type == 'inventory':
                for variant_name in random.sample(['Small', 'Medium', 'Large', 'Red', 'Blue', 'Black'], k=random.randint(2, 4)):
                    variant = {
                        "variant_id": generate_id("VAR"),
                        "item_id": item["item_id"],
                        "item_name": item["name"],
                        "variant_name": variant_name,
                        "sku": f"{item['sku']}-{variant_name[:3].upper()}",
                        "additional_rate": round(random.uniform(50, 500), 2),
                        "effective_rate": item["sales_rate"] + round(random.uniform(50, 500), 2),
                        "attributes": {"size": variant_name} if variant_name in ['Small', 'Medium', 'Large'] else {"color": variant_name},
                        "status": "active",
                        "created_time": datetime.now(timezone.utc).isoformat()
                    }
                    await variants_col.insert_one(variant)
        
        # Create bundles (10% of items)
        print(f"   Creating bundles...")
        for i in range(count // 10):
            components = random.sample(base_items[:50], k=random.randint(2, 5))
            bundle = {
                "bundle_id": generate_id("BDL"),
                "name": f"Service Kit {i+1}",
                "sku": f"BDL-KIT-{i+1:04d}",
                "description": f"Complete service kit with {len(components)} items",
                "rate": sum(c["sales_rate"] for c in components) * 0.9,  # 10% bundle discount
                "auto_calculate_rate": True,
                "component_count": len(components),
                "status": "active",
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            await bundles_col.insert_one(bundle)
            
            # Add bundle components
            for comp in components:
                await self.db['bundle_components'].insert_one({
                    "component_id": generate_id("COMP"),
                    "bundle_id": bundle["bundle_id"],
                    "item_id": comp["item_id"],
                    "item_name": comp["name"],
                    "quantity": random.randint(1, 3),
                    "unit_rate": comp["sales_rate"]
                })
        
        print(f"   ✅ Created {count} items, {count // 5} variants, {count // 10} bundles")
        return self.created_items
    
    async def generate_contacts(self, count: int = 100):
        """Generate diverse contacts with GSTIN, persons, addresses"""
        print(f"\n👥 Generating {count} contacts with full details...")
        contacts_col = self.db['contacts_enhanced']
        persons_col = self.db['contact_persons']
        addresses_col = self.db['addresses']
        
        company_suffixes = ['Pvt Ltd', 'LLP', 'Industries', 'Solutions', 'Enterprises', 'Trading Co']
        first_names = ['Rahul', 'Priya', 'Amit', 'Deepa', 'Vijay', 'Sunita', 'Raj', 'Anita', 'Suresh', 'Kavita']
        last_names = ['Sharma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Agarwal', 'Jain', 'Shah', 'Mehta', 'Reddy']
        
        for i in range(count):
            contact_type = random.choices(['customer', 'vendor', 'both'], weights=[50, 30, 20])[0]
            state_code = random.choice(list(INDIAN_STATES.keys()))
            
            is_business = random.random() < 0.7
            if is_business:
                name = f"{random.choice(first_names)} {random.choice(company_suffixes)}"
            else:
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            contact = {
                "contact_id": generate_id("CON"),
                "name": name,
                "display_name": name,
                "contact_type": contact_type,
                "company_name": name if is_business else "",
                "email": generate_email(name),
                "phone": generate_phone(),
                "mobile": generate_phone(),
                "gstin": generate_gstin(state_code) if is_business and random.random() < 0.8 else "",
                "pan": ''.join(random.choices(string.ascii_uppercase, k=5)) + ''.join(random.choices(string.digits, k=4)) + random.choice(string.ascii_uppercase),
                "place_of_supply": INDIAN_STATES[state_code],
                "gst_treatment": random.choice(['registered', 'unregistered', 'consumer', 'overseas']) if is_business else 'consumer',
                "payment_terms": random.choice([0, 7, 15, 30, 45, 60]),
                "credit_limit": random.randint(10000, 500000) if contact_type in ['customer', 'both'] else 0,
                "currency": "INR",
                "outstanding_receivables": round(random.uniform(0, 100000), 2) if contact_type in ['customer', 'both'] else 0,
                "outstanding_payables": round(random.uniform(0, 50000), 2) if contact_type in ['vendor', 'both'] else 0,
                "tags": random.sample(['VIP', 'Regular', 'New', 'Premium', 'Bulk Buyer', 'Credit Risk'], k=random.randint(0, 3)),
                "portal_enabled": random.random() < 0.3,
                "status": "active",
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await contacts_col.insert_one(contact)
            self.created_contacts.append(contact)
            
            # Add contact persons
            for j in range(random.randint(1, 3)):
                person = {
                    "person_id": generate_id("PER"),
                    "contact_id": contact["contact_id"],
                    "first_name": random.choice(first_names),
                    "last_name": random.choice(last_names),
                    "email": generate_email(f"{random.choice(first_names)}{i}{j}"),
                    "phone": generate_phone(),
                    "designation": random.choice(['Manager', 'Director', 'Owner', 'Accountant', 'Purchaser']),
                    "is_primary": j == 0,
                    "created_time": datetime.now(timezone.utc).isoformat()
                }
                await persons_col.insert_one(person)
            
            # Add addresses
            for addr_type in ['billing', 'shipping']:
                address = {
                    "address_id": generate_id("ADDR"),
                    "contact_id": contact["contact_id"],
                    "address_type": addr_type,
                    "attention": contact["name"],
                    "street": f"{random.randint(1, 500)} {random.choice(['MG Road', 'Station Road', 'Industrial Area', 'Market Street'])}",
                    "city": random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad']),
                    "state": INDIAN_STATES[state_code],
                    "pincode": f"{random.randint(100001, 999999)}",
                    "country": "India",
                    "is_primary": True,
                    "created_time": datetime.now(timezone.utc).isoformat()
                }
                await addresses_col.insert_one(address)
        
        print(f"   ✅ Created {count} contacts with persons and addresses")
        return self.created_contacts
    
    async def generate_estimates(self, count: int = 50):
        """Generate estimates with full workflow"""
        print(f"\n📝 Generating {count} estimates with line items...")
        estimates_col = self.db['estimates_enhanced']
        line_items_col = self.db['estimate_line_items']
        
        statuses = ['draft', 'sent', 'accepted', 'declined', 'converted']
        
        for i in range(count):
            customer = random.choice([c for c in self.created_contacts if c['contact_type'] in ['customer', 'both']])
            items_for_estimate = random.sample(self.created_items[:100], k=random.randint(1, 5))
            
            estimate_id = generate_id("EST")
            sub_total = 0
            tax_total = 0
            line_items = []
            
            for item in items_for_estimate:
                qty = random.randint(1, 10)
                rate = item["sales_rate"]
                amount = qty * rate
                tax = amount * (item.get("tax_percentage", 18) / 100)
                
                line_item = {
                    "line_item_id": generate_id("LI"),
                    "estimate_id": estimate_id,
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "hsn_sac_code": item.get("hsn_code", ""),
                    "quantity": qty,
                    "unit": item.get("unit", "pcs"),
                    "rate": rate,
                    "discount_type": "percentage",
                    "discount_value": random.choice([0, 5, 10]),
                    "tax_rate": item.get("tax_percentage", 18),
                    "amount": amount,
                    "tax_amount": tax,
                    "total": amount + tax
                }
                line_items.append(line_item)
                sub_total += amount
                tax_total += tax
                await line_items_col.insert_one(line_item)
            
            status = random.choices(statuses, weights=[20, 30, 30, 10, 10])[0]
            
            estimate = {
                "estimate_id": estimate_id,
                "estimate_number": f"EST-{datetime.now().strftime('%Y%m')}-{i+1:05d}",
                "customer_id": customer["contact_id"],
                "customer_name": customer["name"],
                "customer_gstin": customer.get("gstin", ""),
                "place_of_supply": customer.get("place_of_supply", "Maharashtra"),
                "estimate_date": (datetime.now() - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d"),
                "expiry_date": (datetime.now() + timedelta(days=random.randint(7, 30))).strftime("%Y-%m-%d"),
                "reference_number": f"REF-{random.randint(1000, 9999)}",
                "status": status,
                "sub_total": round(sub_total, 2),
                "discount_type": "percentage",
                "discount_value": random.choice([0, 5, 10]),
                "total_discount": round(sub_total * random.choice([0, 0.05, 0.1]), 2),
                "tax_total": round(tax_total, 2),
                "grand_total": round(sub_total + tax_total, 2),
                "notes": "Thank you for your business!",
                "terms_conditions": "Standard terms apply",
                "converted_to_invoice": status == 'converted',
                "converted_to_sales_order": status == 'converted' and random.random() < 0.5,
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await estimates_col.insert_one(estimate)
            self.created_estimates.append(estimate)
        
        print(f"   ✅ Created {count} estimates with line items")
        return self.created_estimates
    
    async def generate_sales_orders(self, count: int = 30):
        """Generate sales orders from accepted estimates"""
        print(f"\n📋 Generating {count} sales orders...")
        so_col = self.db['salesorders_enhanced']
        so_line_items_col = self.db['salesorder_line_items']
        
        statuses = ['draft', 'confirmed', 'fulfilled', 'closed', 'void']
        
        for i in range(count):
            customer = random.choice([c for c in self.created_contacts if c['contact_type'] in ['customer', 'both']])
            items_for_so = random.sample(self.created_items[:100], k=random.randint(1, 5))
            
            so_id = generate_id("SO")
            sub_total = 0
            tax_total = 0
            
            for item in items_for_so:
                qty = random.randint(1, 10)
                rate = item["sales_rate"]
                amount = qty * rate
                tax = amount * (item.get("tax_percentage", 18) / 100)
                
                line_item = {
                    "line_item_id": generate_id("LI"),
                    "salesorder_id": so_id,
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "quantity": qty,
                    "rate": rate,
                    "amount": amount,
                    "tax_rate": item.get("tax_percentage", 18),
                    "tax_amount": tax,
                    "total": amount + tax
                }
                await so_line_items_col.insert_one(line_item)
                sub_total += amount
                tax_total += tax
            
            status = random.choices(statuses, weights=[10, 30, 40, 15, 5])[0]
            
            so = {
                "salesorder_id": so_id,
                "salesorder_number": f"SO-{datetime.now().strftime('%Y%m')}-{i+1:05d}",
                "customer_id": customer["contact_id"],
                "customer_name": customer["name"],
                "order_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "expected_shipment_date": (datetime.now() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
                "status": status,
                "sub_total": round(sub_total, 2),
                "tax_total": round(tax_total, 2),
                "grand_total": round(sub_total + tax_total, 2),
                "shipment_status": "shipped" if status in ['fulfilled', 'closed'] else "pending",
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await so_col.insert_one(so)
            self.created_sales_orders.append(so)
        
        print(f"   ✅ Created {count} sales orders")
        return self.created_sales_orders
    
    async def generate_invoices(self, count: int = 40):
        """Generate invoices with payment tracking"""
        print(f"\n🧾 Generating {count} invoices...")
        inv_col = self.db['invoices_enhanced']
        inv_line_items_col = self.db['invoice_line_items']
        payments_col = self.db['invoice_payments']
        
        statuses = ['draft', 'sent', 'partially_paid', 'paid', 'overdue', 'void']
        
        for i in range(count):
            customer = random.choice([c for c in self.created_contacts if c['contact_type'] in ['customer', 'both']])
            items_for_inv = random.sample(self.created_items[:100], k=random.randint(1, 5))
            
            inv_id = generate_id("INV")
            sub_total = 0
            tax_total = 0
            
            for item in items_for_inv:
                qty = random.randint(1, 10)
                rate = item["sales_rate"]
                amount = qty * rate
                tax = amount * (item.get("tax_percentage", 18) / 100)
                
                line_item = {
                    "line_item_id": generate_id("LI"),
                    "invoice_id": inv_id,
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "quantity": qty,
                    "rate": rate,
                    "amount": amount,
                    "tax_rate": item.get("tax_percentage", 18),
                    "tax_amount": tax,
                    "total": amount + tax
                }
                await inv_line_items_col.insert_one(line_item)
                sub_total += amount
                tax_total += tax
            
            grand_total = round(sub_total + tax_total, 2)
            status = random.choices(statuses, weights=[10, 20, 20, 30, 15, 5])[0]
            
            # Calculate payments based on status
            amount_paid = 0
            if status == 'paid':
                amount_paid = grand_total
            elif status == 'partially_paid':
                amount_paid = round(grand_total * random.uniform(0.2, 0.8), 2)
            
            invoice = {
                "invoice_id": inv_id,
                "invoice_number": f"INV-{datetime.now().strftime('%Y%m')}-{i+1:05d}",
                "customer_id": customer["contact_id"],
                "customer_name": customer["name"],
                "customer_gstin": customer.get("gstin", ""),
                "invoice_date": (datetime.now() - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d"),
                "due_date": (datetime.now() + timedelta(days=random.randint(-30, 30))).strftime("%Y-%m-%d"),
                "status": status,
                "sub_total": round(sub_total, 2),
                "tax_total": round(tax_total, 2),
                "grand_total": grand_total,
                "amount_paid": amount_paid,
                "balance_due": round(grand_total - amount_paid, 2),
                "payment_terms": customer.get("payment_terms", 30),
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await inv_col.insert_one(invoice)
            self.created_invoices.append(invoice)
            
            # Create payment records
            if amount_paid > 0:
                payment = {
                    "payment_id": generate_id("PMT"),
                    "invoice_id": inv_id,
                    "amount": amount_paid,
                    "payment_mode": random.choice(['bank_transfer', 'upi', 'cheque', 'cash', 'card']),
                    "payment_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                    "reference_number": f"TXN{random.randint(100000, 999999)}",
                    "created_time": datetime.now(timezone.utc).isoformat()
                }
                await payments_col.insert_one(payment)
        
        print(f"   ✅ Created {count} invoices with payments")
        return self.created_invoices
    
    async def generate_bills(self, count: int = 30):
        """Generate bills and purchase orders for vendors"""
        print(f"\n📑 Generating {count} bills and purchase orders...")
        bills_col = self.db['bills_enhanced']
        bill_line_items_col = self.db['bill_line_items']
        po_col = self.db['purchase_orders_enhanced']
        
        for i in range(count):
            vendor = random.choice([c for c in self.created_contacts if c['contact_type'] in ['vendor', 'both']])
            items_for_bill = random.sample(self.created_items[:100], k=random.randint(1, 5))
            
            bill_id = generate_id("BILL")
            sub_total = 0
            tax_total = 0
            
            for item in items_for_bill:
                qty = random.randint(1, 20)
                rate = item["purchase_rate"]
                amount = qty * rate
                tax = amount * (item.get("tax_percentage", 18) / 100)
                
                line_item = {
                    "line_item_id": generate_id("LI"),
                    "bill_id": bill_id,
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "quantity": qty,
                    "rate": rate,
                    "amount": amount,
                    "tax_rate": item.get("tax_percentage", 18),
                    "tax_amount": tax,
                    "total": amount + tax
                }
                await bill_line_items_col.insert_one(line_item)
                sub_total += amount
                tax_total += tax
            
            grand_total = round(sub_total + tax_total, 2)
            status = random.choices(['draft', 'open', 'partially_paid', 'paid', 'overdue'], weights=[10, 30, 20, 30, 10])[0]
            
            amount_paid = 0
            if status == 'paid':
                amount_paid = grand_total
            elif status == 'partially_paid':
                amount_paid = round(grand_total * random.uniform(0.2, 0.8), 2)
            
            bill = {
                "bill_id": bill_id,
                "bill_number": f"BILL-{datetime.now().strftime('%Y%m')}-{i+1:05d}",
                "vendor_id": vendor["contact_id"],
                "vendor_name": vendor["name"],
                "vendor_gstin": vendor.get("gstin", ""),
                "bill_date": (datetime.now() - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d"),
                "due_date": (datetime.now() + timedelta(days=random.randint(-30, 30))).strftime("%Y-%m-%d"),
                "status": status,
                "sub_total": round(sub_total, 2),
                "tax_total": round(tax_total, 2),
                "grand_total": grand_total,
                "amount_paid": amount_paid,
                "balance_due": round(grand_total - amount_paid, 2),
                "payment_terms": vendor.get("payment_terms", 30),
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await bills_col.insert_one(bill)
            self.created_bills.append(bill)
        
        # Generate Purchase Orders
        for i in range(count // 2):
            vendor = random.choice([c for c in self.created_contacts if c['contact_type'] in ['vendor', 'both']])
            items_for_po = random.sample(self.created_items[:100], k=random.randint(1, 5))
            
            po_id = generate_id("PO")
            sub_total = sum(item["purchase_rate"] * random.randint(1, 10) for item in items_for_po)
            
            po = {
                "po_id": po_id,
                "po_number": f"PO-{datetime.now().strftime('%Y%m')}-{i+1:05d}",
                "vendor_id": vendor["contact_id"],
                "vendor_name": vendor["name"],
                "order_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "expected_delivery_date": (datetime.now() + timedelta(days=random.randint(7, 30))).strftime("%Y-%m-%d"),
                "status": random.choices(['draft', 'issued', 'received', 'billed'], weights=[20, 30, 30, 20])[0],
                "sub_total": round(sub_total, 2),
                "tax_total": round(sub_total * 0.18, 2),
                "grand_total": round(sub_total * 1.18, 2),
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await po_col.insert_one(po)
        
        print(f"   ✅ Created {count} bills and {count // 2} purchase orders")
        return self.created_bills
    
    async def generate_shipments_and_returns(self, count: int = 20):
        """Generate shipments and returns"""
        print(f"\n🚚 Generating {count} shipments and returns...")
        shipments_col = self.db['shipments']
        returns_col = self.db['inventory_returns']
        
        for i in range(count):
            so = random.choice(self.created_sales_orders) if self.created_sales_orders else None
            if not so:
                continue
            
            shipment = {
                "shipment_id": generate_id("SHP"),
                "sales_order_id": so["salesorder_id"],
                "sales_order_number": so["salesorder_number"],
                "customer_id": so["customer_id"],
                "customer_name": so["customer_name"],
                "package_number": f"PKG-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}",
                "carrier": random.choice(['Delhivery', 'BlueDart', 'DTDC', 'FedEx', 'Self']),
                "tracking_number": f"TRK{random.randint(1000000000, 9999999999)}",
                "status": random.choices(['packed', 'shipped', 'delivered'], weights=[20, 30, 50])[0],
                "shipped_date": (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat() if random.random() < 0.8 else None,
                "delivered_date": (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat() if random.random() < 0.5 else None,
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await shipments_col.insert_one(shipment)
            
            # Create some returns (20%)
            if random.random() < 0.2 and shipment["status"] == "delivered":
                ret = {
                    "return_id": generate_id("RET"),
                    "shipment_id": shipment["shipment_id"],
                    "sales_order_id": so["salesorder_id"],
                    "customer_id": so["customer_id"],
                    "customer_name": so["customer_name"],
                    "reason": random.choice(['Damaged', 'Wrong item', 'Not needed', 'Defective', 'Size mismatch']),
                    "restock": random.random() < 0.7,
                    "status": random.choice(['pending', 'processed']),
                    "return_date": datetime.now(timezone.utc).isoformat(),
                    "created_time": datetime.now(timezone.utc).isoformat()
                }
                await returns_col.insert_one(ret)
        
        print(f"   ✅ Created {count} shipments with returns")
    
    async def generate_serial_batches(self, count: int = 50):
        """Generate serial numbers and batch tracking"""
        print(f"\n🔢 Generating {count} serial/batch numbers...")
        serials_col = self.db['item_serial_batches']
        
        inventory_items = [i for i in self.created_items if i.get('track_inventory')]
        
        for i in range(count):
            item = random.choice(inventory_items) if inventory_items else random.choice(self.created_items)
            tracking_type = random.choice(['serial', 'batch'])
            
            serial = {
                "serial_batch_id": generate_id("SB"),
                "item_id": item["item_id"],
                "tracking_type": tracking_type,
                "number": f"{'SN' if tracking_type == 'serial' else 'LOT'}-{random.randint(100000, 999999)}",
                "warehouse_id": self.created_warehouses[0]["warehouse_id"] if self.created_warehouses else "",
                "quantity": 1 if tracking_type == 'serial' else random.randint(10, 100),
                "available_quantity": 1 if tracking_type == 'serial' else random.randint(5, 100),
                "expiry_date": (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d") if tracking_type == 'batch' else None,
                "status": random.choices(['available', 'sold', 'returned'], weights=[70, 20, 10])[0],
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await serials_col.insert_one(serial)
        
        print(f"   ✅ Created {count} serial/batch numbers")
    
    async def run_full_generation(self):
        """Run complete test data generation"""
        print("\n" + "="*60)
        print("🚀 BATTWHEELS OS - COMPREHENSIVE TEST DATA GENERATION")
        print("="*60)
        
        await self.connect()
        
        try:
            # Generate in dependency order
            await self.generate_warehouses(5)
            await self.generate_items(200)
            await self.generate_contacts(100)
            await self.generate_estimates(50)
            await self.generate_sales_orders(30)
            await self.generate_invoices(40)
            await self.generate_bills(30)
            await self.generate_shipments_and_returns(20)
            await self.generate_serial_batches(50)
            
            print("\n" + "="*60)
            print("✅ TEST DATA GENERATION COMPLETE")
            print("="*60)
            print(f"""
Summary:
  📦 Warehouses: {len(self.created_warehouses)}
  🏷️  Items: {len(self.created_items)}
  👥 Contacts: {len(self.created_contacts)}
  📝 Estimates: {len(self.created_estimates)}
  📋 Sales Orders: {len(self.created_sales_orders)}
  🧾 Invoices: {len(self.created_invoices)}
  📑 Bills: {len(self.created_bills)}
""")
            
        finally:
            await self.close()

if __name__ == "__main__":
    generator = AuditDataGenerator()
    asyncio.run(generator.run_full_generation())
