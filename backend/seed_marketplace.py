"""
Seed script for Marketplace Products
Creates realistic EV parts catalog aligned with Battwheels OS schema
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Sample product catalog - realistic EV parts
PRODUCTS = [
    # ============== 2W PARTS ==============
    {
        "sku": "BW-2W-CTR-001",
        "name": "BLDC Motor Controller 48V 25A",
        "slug": "bldc-motor-controller-48v-25a",
        "category": "2W Parts",
        "subcategory": "Controllers",
        "description": "High-performance BLDC motor controller for 2-wheeler EVs. Features regenerative braking, over-current protection, and programmable settings. Compatible with most 48V electric scooters.",
        "short_description": "48V 25A BLDC Controller with regen braking",
        "specifications": {
            "voltage": "48V",
            "current": "25A",
            "max_power": "1200W",
            "protection": "Over-current, Over-voltage, Under-voltage",
            "features": ["Regenerative Braking", "Cruise Control", "Reverse Mode"]
        },
        "compatibility": ["Ather 450X", "Ola S1 Pro", "TVS iQube", "Bajaj Chetak", "Hero Vida V1"],
        "vehicle_category": ["2W"],
        "brand": "Battwheels Certified",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 12,
        "weight_kg": 0.8,
        "images": ["/marketplace/products/controller-2w-001.jpg"],
        "tags": ["controller", "bldc", "motor controller", "2 wheeler", "48v"],
        "base_price": 4999,
        "stock_quantity": 25
    },
    {
        "sku": "BW-2W-THR-001",
        "name": "Universal EV Throttle Assembly",
        "slug": "universal-ev-throttle-assembly",
        "category": "2W Parts",
        "subcategory": "Throttle & Controls",
        "description": "Premium quality throttle assembly with hall sensor. Smooth response curve, weather-resistant design. Direct replacement for most 2-wheeler EVs.",
        "short_description": "Hall sensor throttle - universal fit",
        "specifications": {
            "type": "Hall Sensor",
            "voltage": "1-4.2V output",
            "connector": "3-pin JST",
            "cable_length": "1.2m"
        },
        "compatibility": ["Ather 450", "Ola S1", "TVS iQube", "Bounce Infinity", "Hero Electric"],
        "vehicle_category": ["2W"],
        "brand": "Battwheels",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 6,
        "weight_kg": 0.15,
        "images": ["/marketplace/products/throttle-2w-001.jpg"],
        "tags": ["throttle", "accelerator", "hall sensor", "2 wheeler"],
        "base_price": 899,
        "stock_quantity": 50
    },
    {
        "sku": "BW-2W-DSP-001",
        "name": "LCD Display Speedometer - 2W Universal",
        "slug": "lcd-display-speedometer-2w",
        "category": "2W Parts",
        "subcategory": "Displays & Instruments",
        "description": "Multi-function LCD display for electric scooters. Shows speed, battery %, odometer, trip meter, and error codes. Easy installation with plug-and-play connectors.",
        "short_description": "Universal LCD speedometer with battery indicator",
        "specifications": {
            "display_size": "3.5 inch",
            "voltage_range": "36V-72V",
            "features": ["Speed", "Battery %", "Odometer", "Trip", "Error Codes"],
            "waterproof_rating": "IP65"
        },
        "compatibility": ["Universal 2W EVs"],
        "vehicle_category": ["2W"],
        "brand": "Battwheels",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 6,
        "weight_kg": 0.2,
        "images": ["/marketplace/products/display-2w-001.jpg"],
        "tags": ["display", "speedometer", "lcd", "instrument cluster"],
        "base_price": 1499,
        "stock_quantity": 30
    },
    
    # ============== 3W PARTS ==============
    {
        "sku": "BW-3W-CTR-001",
        "name": "BLDC Motor Controller 60V 45A - 3W",
        "slug": "bldc-motor-controller-60v-45a-3w",
        "category": "3W Parts",
        "subcategory": "Controllers",
        "description": "Heavy-duty motor controller designed for electric auto rickshaws and cargo vehicles. High current capacity with advanced thermal management.",
        "short_description": "60V 45A Controller for E-Rickshaws",
        "specifications": {
            "voltage": "60V",
            "current": "45A peak",
            "max_power": "2700W",
            "cooling": "Passive + Active Fan",
            "protection": "Over-current, Over-temperature, Short-circuit"
        },
        "compatibility": ["Mahindra Treo", "Piaggio Ape E-City", "Kinetic Safar", "Lohia Comfort"],
        "vehicle_category": ["3W"],
        "brand": "Battwheels Certified",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 12,
        "weight_kg": 1.5,
        "images": ["/marketplace/products/controller-3w-001.jpg"],
        "tags": ["controller", "3 wheeler", "e-rickshaw", "60v", "high power"],
        "base_price": 8999,
        "stock_quantity": 15
    },
    {
        "sku": "BW-3W-MTR-001",
        "name": "Hub Motor 1500W - E-Rickshaw",
        "slug": "hub-motor-1500w-e-rickshaw",
        "category": "3W Parts",
        "subcategory": "Motors",
        "description": "Direct drive hub motor for e-rickshaws. High torque, maintenance-free design with integrated hall sensors. Drop-in replacement for most 3W EVs.",
        "short_description": "1500W Hub Motor - Direct replacement",
        "specifications": {
            "power": "1500W",
            "voltage": "48V-60V",
            "torque": "120Nm",
            "efficiency": ">85%",
            "type": "Brushless Hub Motor"
        },
        "compatibility": ["Mahindra Treo", "Piaggio Ape", "YC Electric", "Lohia"],
        "vehicle_category": ["3W"],
        "brand": "Battwheels",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 18,
        "weight_kg": 12,
        "images": ["/marketplace/products/motor-3w-001.jpg"],
        "tags": ["motor", "hub motor", "1500w", "e-rickshaw", "3 wheeler"],
        "base_price": 14999,
        "stock_quantity": 8
    },
    
    # ============== 4W PARTS ==============
    {
        "sku": "BW-4W-OBC-001",
        "name": "On-Board Charger 3.3kW - 4W EV",
        "slug": "on-board-charger-3-3kw-4w",
        "category": "4W Parts",
        "subcategory": "Chargers",
        "description": "High-efficiency on-board charger for 4-wheeler EVs. CAN bus communication, intelligent charging algorithm, compact design.",
        "short_description": "3.3kW OBC with CAN communication",
        "specifications": {
            "power": "3.3kW",
            "input": "230V AC",
            "output": "48V-96V DC",
            "efficiency": ">94%",
            "communication": "CAN Bus"
        },
        "compatibility": ["Tata Nexon EV", "MG ZS EV", "Mahindra XUV400", "Hyundai Kona"],
        "vehicle_category": ["4W"],
        "brand": "Battwheels Certified",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 24,
        "weight_kg": 5,
        "images": ["/marketplace/products/obc-4w-001.jpg"],
        "tags": ["charger", "on-board charger", "obc", "4 wheeler", "ev charger"],
        "base_price": 35000,
        "stock_quantity": 5
    },
    {
        "sku": "BW-4W-BMS-001",
        "name": "Battery Management System - 96S",
        "slug": "battery-management-system-96s",
        "category": "4W Parts",
        "subcategory": "BMS",
        "description": "Advanced BMS for lithium battery packs. Supports up to 96 cells in series. Cell balancing, temperature monitoring, SOC estimation.",
        "short_description": "96S BMS with active balancing",
        "specifications": {
            "cells": "96S max",
            "balancing": "Active",
            "current_sensing": "Hall effect",
            "communication": "CAN, UART",
            "protection": "OV, UV, OC, OT, Short-circuit"
        },
        "compatibility": ["Universal 4W EVs", "Custom Battery Packs"],
        "vehicle_category": ["4W"],
        "brand": "Battwheels",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 12,
        "weight_kg": 0.5,
        "images": ["/marketplace/products/bms-4w-001.jpg"],
        "tags": ["bms", "battery management", "96s", "lithium", "cell balancing"],
        "base_price": 25000,
        "stock_quantity": 10
    },
    
    # ============== BATTERIES ==============
    {
        "sku": "BW-BAT-LFP-48-30",
        "name": "Lithium Iron Phosphate Battery 48V 30Ah",
        "slug": "lfp-battery-48v-30ah",
        "category": "Batteries",
        "subcategory": "LFP Batteries",
        "description": "Premium LiFePO4 battery pack for 2W/3W EVs. 3000+ cycle life, safe chemistry, integrated BMS. Ideal replacement battery or upgrade.",
        "short_description": "48V 30Ah LFP - 3000+ cycles",
        "specifications": {
            "chemistry": "LiFePO4",
            "voltage": "48V (51.2V nominal)",
            "capacity": "30Ah",
            "energy": "1.54kWh",
            "cycles": "3000+",
            "weight": "15kg"
        },
        "compatibility": ["Universal 2W/3W EVs", "Conversion Kits"],
        "vehicle_category": ["2W", "3W"],
        "brand": "Battwheels Energy",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 36,
        "weight_kg": 15,
        "images": ["/marketplace/products/battery-lfp-48-30.jpg"],
        "tags": ["battery", "lfp", "lithium", "48v", "lifepo4"],
        "base_price": 42000,
        "stock_quantity": 12
    },
    {
        "sku": "BW-BAT-NMC-72-40",
        "name": "Lithium NMC Battery 72V 40Ah",
        "slug": "nmc-battery-72v-40ah",
        "category": "Batteries",
        "subcategory": "NMC Batteries",
        "description": "High energy density NMC battery for performance EVs. Excellent range, fast charging capable. Integrated smart BMS with Bluetooth monitoring.",
        "short_description": "72V 40Ah NMC - High Performance",
        "specifications": {
            "chemistry": "NMC (Nickel Manganese Cobalt)",
            "voltage": "72V (84V max)",
            "capacity": "40Ah",
            "energy": "2.88kWh",
            "max_discharge": "2C",
            "fast_charge": "1C capable"
        },
        "compatibility": ["High-performance 2W", "E-rickshaws", "Custom builds"],
        "vehicle_category": ["2W", "3W"],
        "brand": "Battwheels Energy",
        "oem_aftermarket": "aftermarket",
        "is_certified": True,
        "warranty_months": 24,
        "weight_kg": 22,
        "images": ["/marketplace/products/battery-nmc-72-40.jpg"],
        "tags": ["battery", "nmc", "lithium", "72v", "high performance"],
        "base_price": 68000,
        "stock_quantity": 6
    },
    {
        "sku": "BW-BAT-REF-48-20",
        "name": "Refurbished Battery 48V 20Ah (Certified)",
        "slug": "refurbished-battery-48v-20ah",
        "category": "Batteries",
        "subcategory": "Refurbished",
        "description": "Certified refurbished battery pack. Tested and reconditioned to 80%+ original capacity. Economical option with Battwheels quality assurance.",
        "short_description": "Refurbished 48V 20Ah - Budget friendly",
        "specifications": {
            "chemistry": "LiFePO4",
            "voltage": "48V",
            "capacity": "20Ah (80%+ of original)",
            "energy": "0.96kWh min",
            "condition": "Refurbished - Grade A"
        },
        "compatibility": ["Ather", "Ola", "TVS", "Hero Electric"],
        "vehicle_category": ["2W"],
        "brand": "Battwheels Refurb",
        "oem_aftermarket": "refurbished",
        "is_certified": True,
        "warranty_months": 6,
        "weight_kg": 12,
        "images": ["/marketplace/products/battery-refurb-48-20.jpg"],
        "tags": ["battery", "refurbished", "budget", "48v", "certified"],
        "base_price": 18000,
        "stock_quantity": 8
    },
    
    # ============== DIAGNOSTIC TOOLS ==============
    {
        "sku": "BW-DIAG-PRO-001",
        "name": "EV Diagnostic Scanner Pro",
        "slug": "ev-diagnostic-scanner-pro",
        "category": "Diagnostic Tools",
        "subcategory": "Scanners",
        "description": "Professional-grade EV diagnostic tool. Reads battery health, motor parameters, controller errors. Compatible with CAN bus and proprietary protocols.",
        "short_description": "Pro EV Scanner - Multi-protocol",
        "specifications": {
            "protocols": ["CAN Bus", "UART", "Modbus"],
            "display": "4.3 inch touchscreen",
            "battery": "Built-in rechargeable",
            "updates": "OTA via WiFi",
            "compatibility": "100+ EV models"
        },
        "compatibility": ["Universal - 2W/3W/4W EVs"],
        "vehicle_category": ["2W", "3W", "4W"],
        "brand": "Battwheels Tools",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 12,
        "weight_kg": 0.4,
        "images": ["/marketplace/products/diagnostic-pro-001.jpg"],
        "tags": ["diagnostic", "scanner", "tool", "obd", "can bus"],
        "base_price": 24999,
        "stock_quantity": 15
    },
    {
        "sku": "BW-DIAG-BMS-001",
        "name": "BMS Cell Tester & Balancer",
        "slug": "bms-cell-tester-balancer",
        "category": "Diagnostic Tools",
        "subcategory": "Testers",
        "description": "Portable cell tester and active balancer. Test individual cells, check IR values, and manually balance battery packs. Essential tool for battery servicing.",
        "short_description": "Cell tester with active balancing",
        "specifications": {
            "voltage_range": "0-5V per cell",
            "current_range": "0-20A",
            "ir_measurement": "Yes",
            "balancing_current": "2A",
            "cells_supported": "Up to 24S"
        },
        "compatibility": ["All lithium battery packs"],
        "vehicle_category": ["2W", "3W", "4W"],
        "brand": "Battwheels Tools",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 12,
        "weight_kg": 1.2,
        "images": ["/marketplace/products/cell-tester-001.jpg"],
        "tags": ["bms", "cell tester", "balancer", "battery tool", "diagnostic"],
        "base_price": 12999,
        "stock_quantity": 20
    },
    {
        "sku": "BW-DIAG-MTR-001",
        "name": "Motor Analyzer & Dyno Interface",
        "slug": "motor-analyzer-dyno-interface",
        "category": "Diagnostic Tools",
        "subcategory": "Analyzers",
        "description": "Advanced motor testing interface. Measures RPM, torque, efficiency curves. Connect to PC for detailed analysis and reporting.",
        "short_description": "Motor performance analyzer",
        "specifications": {
            "rpm_range": "0-20,000 RPM",
            "torque_range": "0-200 Nm",
            "power_calculation": "Real-time",
            "interface": "USB to PC",
            "software": "Windows compatible"
        },
        "compatibility": ["BLDC Motors", "PMSM Motors"],
        "vehicle_category": ["2W", "3W", "4W"],
        "brand": "Battwheels Tools",
        "oem_aftermarket": "oem",
        "is_certified": True,
        "warranty_months": 12,
        "weight_kg": 2,
        "images": ["/marketplace/products/motor-analyzer-001.jpg"],
        "tags": ["motor", "analyzer", "dyno", "diagnostic", "testing"],
        "base_price": 45000,
        "stock_quantity": 5
    },
    
    # ============== REFURBISHED COMPONENTS ==============
    {
        "sku": "BW-REF-CTR-001",
        "name": "Refurbished Controller - Ola S1 Pro",
        "slug": "refurbished-controller-ola-s1-pro",
        "category": "Refurbished Components",
        "subcategory": "Controllers",
        "description": "Factory reconditioned controller for Ola S1 Pro. Tested and certified by Battwheels. Economical replacement with quality assurance.",
        "short_description": "Refurb Ola S1 Pro Controller",
        "specifications": {
            "original_model": "Ola S1 Pro",
            "condition": "Refurbished - Grade A",
            "testing": "100% functional verified",
            "includes": "Controller unit only"
        },
        "compatibility": ["Ola S1 Pro", "Ola S1"],
        "vehicle_category": ["2W"],
        "brand": "OEM Refurbished",
        "oem_aftermarket": "refurbished",
        "is_certified": True,
        "warranty_months": 3,
        "weight_kg": 1,
        "images": ["/marketplace/products/refurb-controller-ola.jpg"],
        "tags": ["refurbished", "controller", "ola", "certified"],
        "base_price": 8999,
        "stock_quantity": 4
    },
    {
        "sku": "BW-REF-MTR-001",
        "name": "Refurbished Hub Motor - Ather 450",
        "slug": "refurbished-hub-motor-ather-450",
        "category": "Refurbished Components",
        "subcategory": "Motors",
        "description": "Certified refurbished hub motor from Ather 450. Bearings replaced, windings tested, hall sensors verified. Like-new performance at 40% savings.",
        "short_description": "Refurb Ather 450 Motor",
        "specifications": {
            "original_model": "Ather 450",
            "power": "5.4kW peak",
            "condition": "Refurbished - Grade A",
            "parts_replaced": "Bearings, seals"
        },
        "compatibility": ["Ather 450", "Ather 450X", "Ather 450 Plus"],
        "vehicle_category": ["2W"],
        "brand": "OEM Refurbished",
        "oem_aftermarket": "refurbished",
        "is_certified": True,
        "warranty_months": 6,
        "weight_kg": 8,
        "images": ["/marketplace/products/refurb-motor-ather.jpg"],
        "tags": ["refurbished", "motor", "ather", "hub motor", "certified"],
        "base_price": 18999,
        "stock_quantity": 3
    }
]

async def seed_products():
    """Seed the marketplace products collection"""
    print("Starting marketplace product seeding...")
    
    # Clear existing products (optional - comment out to append)
    await db.marketplace_products.delete_many({})
    print("Cleared existing products")
    
    # Add timestamps to all products
    for product in PRODUCTS:
        product["created_at"] = datetime.utcnow()
        product["updated_at"] = datetime.utcnow()
        product["is_active"] = True
    
    # Insert products
    result = await db.marketplace_products.insert_many(PRODUCTS)
    print(f"Inserted {len(result.inserted_ids)} products")
    
    # Create indexes
    await db.marketplace_products.create_index("sku", unique=True)
    await db.marketplace_products.create_index("slug", unique=True)
    await db.marketplace_products.create_index("category")
    await db.marketplace_products.create_index("vehicle_category")
    await db.marketplace_products.create_index([("name", "text"), ("description", "text"), ("tags", "text")])
    print("Created indexes")
    
    # Print summary
    categories = await db.marketplace_products.distinct("category")
    print(f"\nCategories: {categories}")
    
    for cat in categories:
        count = await db.marketplace_products.count_documents({"category": cat})
        print(f"  - {cat}: {count} products")
    
    print("\n✅ Marketplace seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_products())
