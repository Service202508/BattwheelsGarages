"""
Database Seeding Script for Battwheels Garages
Seeds: 5 Services, 3 Blog Posts, 8 Testimonials
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from uuid import uuid4
import os

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'test_database')

# Sample Services Data (5 services)
services_data = [
    {
        "id": str(uuid4()),
        "title": "Onsite EV Diagnosis & Repair",
        "slug": "onsite-ev-diagnosis-repair",
        "short_description": "Expert technicians diagnose and fix your EV right where it breaks down. No towing required for most issues.",
        "long_description": "Our flagship service brings certified EV technicians directly to your location. Using advanced diagnostic tools, we identify issues with motors, controllers, wiring, and electronics on the spot. 85% of breakdowns are resolved without towing, saving you time and money. Available for 2W, 3W, 4W, and commercial EVs across 11 cities.",
        "vehicle_segments": ["2W", "3W", "4W", "Commercial"],
        "pricing_model": "inspection_based",
        "price": None,
        "display_order": 1,
        "is_active": True,
        "status": "active",
        "icon": "Wrench",
        "features": ["Same-day response", "No towing charges", "Certified EV technicians", "All major brands covered"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Battery Health Check & BMS Diagnostics",
        "slug": "battery-health-check-bms",
        "short_description": "Comprehensive battery analysis including cell balancing, BMS health, and degradation assessment.",
        "long_description": "Your EV battery is its most valuable component. Our Battery Health Check service provides detailed insights into cell-level performance, state of health (SoH), state of charge accuracy, and BMS functionality. We identify weak cells, calibration issues, and provide recommendations to extend battery life. Essential for fleet operators tracking asset health.",
        "vehicle_segments": ["2W", "3W", "4W", "Commercial"],
        "pricing_model": "fixed",
        "price": 1499,
        "display_order": 2,
        "is_active": True,
        "status": "active",
        "icon": "Battery",
        "features": ["Cell-level analysis", "SoH reporting", "BMS diagnostics", "Degradation forecast"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Motor & Controller Service",
        "slug": "motor-controller-service",
        "short_description": "Expert servicing of BLDC/PMSM motors, controllers, and drive systems for optimal performance.",
        "long_description": "EV motors and controllers require specialized knowledge that traditional mechanics lack. Our technicians are trained in BLDC and PMSM motor diagnostics, controller firmware issues, throttle response calibration, and regenerative braking optimization. We handle overheating issues, bearing replacements, and controller repairs for all major EV brands.",
        "vehicle_segments": ["2W", "3W", "4W"],
        "pricing_model": "inspection_based",
        "price": None,
        "display_order": 3,
        "is_active": True,
        "status": "active",
        "icon": "Settings",
        "features": ["BLDC/PMSM expertise", "Controller diagnostics", "Firmware updates", "Thermal management"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Fleet AMC Programs",
        "slug": "fleet-amc-programs",
        "short_description": "Annual Maintenance Contracts designed for fleet operators with guaranteed SLAs and priority response.",
        "long_description": "Our Fleet AMC programs are built for operators who need predictable maintenance costs and guaranteed uptime. Includes preventive maintenance schedules, priority breakdown response, dedicated account manager, monthly health reports, and discounted spare parts. Customizable packages for 10+ vehicle fleets with city-wide coverage.",
        "vehicle_segments": ["2W", "3W", "4W", "Commercial"],
        "pricing_model": "contact_for_quote",
        "price": None,
        "display_order": 4,
        "is_active": True,
        "status": "active",
        "icon": "Truck",
        "features": ["Guaranteed 2-hour response", "Preventive maintenance", "Monthly reporting", "Dedicated account manager"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Periodic EV Service",
        "slug": "periodic-ev-service",
        "short_description": "Scheduled maintenance to keep your EV running smoothly — brakes, suspension, electronics, and more.",
        "long_description": "EVs need different maintenance than ICE vehicles. Our Periodic Service covers brake pad inspection (EVs wear brakes differently due to regen), suspension checks, tire rotation, coolant system inspection (for liquid-cooled batteries), electrical connection checks, and software updates where applicable. Recommended every 10,000 km or 6 months.",
        "vehicle_segments": ["2W", "3W", "4W"],
        "pricing_model": "fixed",
        "price": 2499,
        "display_order": 5,
        "is_active": True,
        "status": "active",
        "icon": "Zap",
        "features": ["Comprehensive 50-point check", "Brake system inspection", "Software updates", "Fluid top-ups included"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
]

# Sample Blog Posts Data (3 blogs)
blogs_data = [
    {
        "id": str(uuid4()),
        "title": "Why Onsite EV Repair is the Future of Fleet Maintenance",
        "slug": "onsite-ev-repair-future-fleet-maintenance",
        "thumbnail": "/assets/blog/onsite-repair.jpg",
        "category": "Fleet Ops",
        "excerpt": "Traditional workshop-based servicing doesn't work for EV fleets. Here's why onsite repair is becoming the gold standard for fleet operators across India.",
        "content": """<h2>The Problem with Traditional EV Servicing</h2>
<p>When an EV breaks down in your fleet, every hour of downtime costs money. Traditional workshops require towing, waiting in queues, and often lack EV-specific expertise. For fleet operators running tight schedules, this model simply doesn't work.</p>

<h2>Enter Onsite EV Repair</h2>
<p>Onsite repair flips the model. Instead of bringing the vehicle to the mechanic, we bring the mechanic to the vehicle. Our data shows that 85% of common EV issues — motor faults, controller errors, wiring problems, and battery alerts — can be diagnosed and fixed on location.</p>

<h2>The Economics Make Sense</h2>
<p>Consider a delivery fleet where each vehicle generates ₹1,500-2,000 daily. A breakdown that takes 2 days to fix at a workshop costs ₹3,000-4,000 in lost revenue alone, plus towing charges. Onsite repair typically resolves issues within 2-4 hours, the same day.</p>

<h2>What This Means for Fleet Operators</h2>
<p>Fleet operators partnering with onsite service providers like Battwheels report 30-40% reduction in vehicle downtime. With AMC programs, maintenance becomes predictable, and emergency breakdowns are handled with guaranteed SLAs.</p>""",
        "author": "Battwheels Team",
        "meta_title": "Onsite EV Repair: The Future of Fleet Maintenance | Battwheels",
        "meta_description": "Learn why onsite EV repair is becoming essential for fleet operators. Reduce downtime, cut costs, and keep your electric vehicles running.",
        "status": "published",
        "is_published": True,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Understanding EV Battery Health: What Fleet Managers Need to Know",
        "slug": "understanding-ev-battery-health-fleet-managers",
        "thumbnail": "/assets/blog/battery-health.jpg",
        "category": "EV Tech Deep Dive",
        "excerpt": "Battery degradation is the biggest concern for EV fleet operators. Learn how to monitor, maintain, and maximize the life of your fleet's batteries.",
        "content": """<h2>Why Battery Health Matters</h2>
<p>The battery pack represents 30-40% of an EV's value. Understanding its health isn't just about range — it's about asset value, operational efficiency, and long-term TCO. Fleet managers who actively monitor battery health see significantly better resale values and lower replacement costs.</p>

<h2>Key Metrics to Track</h2>
<p><strong>State of Health (SoH):</strong> This percentage tells you how much capacity remains compared to when the battery was new. A battery at 80% SoH has lost 20% of its original capacity.</p>
<p><strong>Cycle Count:</strong> Each full charge-discharge cycle contributes to degradation. Tracking cycles helps predict when batteries will need attention.</p>
<p><strong>Cell Balance:</strong> Healthy battery packs have cells that charge and discharge evenly. Imbalanced cells reduce range and can cause premature failure.</p>

<h2>Best Practices for Fleet Batteries</h2>
<ul>
<li>Avoid charging to 100% daily — 80-90% is optimal for longevity</li>
<li>Don't let batteries sit at very low charge for extended periods</li>
<li>Monitor charging temperatures — fast charging in extreme heat accelerates degradation</li>
<li>Schedule quarterly battery health checks for early issue detection</li>
</ul>

<h2>When to Be Concerned</h2>
<p>If SoH drops below 80% or you notice sudden range drops, it's time for a professional diagnostic. Early intervention can often restore performance through cell balancing or BMS recalibration.</p>""",
        "author": "Battwheels Tech Team",
        "meta_title": "EV Battery Health Guide for Fleet Managers | Battwheels",
        "meta_description": "Complete guide to understanding and maintaining EV battery health for fleet operations. Learn key metrics, best practices, and warning signs.",
        "status": "published",
        "is_published": True,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Battwheels Expands to 11 Cities: What This Means for EV Owners",
        "slug": "battwheels-expands-11-cities-ev-owners",
        "thumbnail": "/assets/blog/expansion.jpg",
        "category": "Company Updates",
        "excerpt": "We're now live in 11 cities across India. Here's our expansion story and what it means for EV owners and fleet operators nationwide.",
        "content": """<h2>From Delhi to Pan-India</h2>
<p>What started as a single garage in Okhla, Delhi has grown into India's largest EV-focused onsite service network. Today, we're proud to announce our presence in 11 cities: Delhi NCR (including Noida and Gurugram), Bengaluru, Chennai, Hyderabad, Jaipur, Lucknow, and more.</p>

<h2>Why We're Expanding</h2>
<p>EV adoption in India is accelerating. Fleet operators are deploying electric 2-wheelers and 3-wheelers at scale. OEMs are launching new models every quarter. But after-sales infrastructure hasn't kept pace. That's where Battwheels comes in.</p>

<h2>What This Means for You</h2>
<p><strong>For Individual EV Owners:</strong> No more searching for mechanics who understand EVs. Book a service online, and our technician comes to you.</p>
<p><strong>For Fleet Operators:</strong> Consistent service quality across cities. One vendor, one contract, nationwide coverage.</p>
<p><strong>For OEMs:</strong> A reliable after-sales partner to support your dealer network and direct customers.</p>

<h2>Coming Soon</h2>
<p>We're not stopping at 11. By end of 2025, we aim to cover 25 cities. If you're in a city where we're not yet present, let us know — your demand helps us prioritize expansion.</p>""",
        "author": "Battwheels Team",
        "meta_title": "Battwheels Now in 11 Cities Across India | Company Update",
        "meta_description": "Battwheels expands EV onsite service to 11 Indian cities. Learn about our growth and what it means for EV owners and fleet operators.",
        "status": "published",
        "is_published": True,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
]

# Sample Testimonials Data (8 testimonials)
testimonials_data = [
    {
        "id": str(uuid4()),
        "name": "Rohit Malhotra",
        "company": "QuickDeliver Logistics",
        "role": "Fleet Operations Manager",
        "quote": "Downtime kills fleet economics. Battwheels' onsite EV repair model helped us reduce vehicle idle time by 40%. Their technicians understand EV systems deeply and fix issues without unnecessary towing.",
        "rating": 5,
        "featured": True,
        "category": "2w-fleet",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "name": "Ankit Verma",
        "company": "GreenRide E-Autos",
        "role": "City Head - Bengaluru",
        "quote": "Earlier, even small EV issues meant half-day downtime. Battwheels' team resolves most problems onsite for our e-rickshaw fleet. It's a huge operational win for us.",
        "rating": 5,
        "featured": True,
        "category": "3w-fleet",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "name": "Pradeep Singh",
        "company": "FastTrack Hyperlocal",
        "role": "Operations Lead",
        "quote": "Battwheels Garages isn't just a service vendor — they behave like an uptime partner. Fast diagnosis, honest recommendations, and clear communication at every step.",
        "rating": 5,
        "featured": True,
        "category": "logistics",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "name": "Neha Aggarwal",
        "company": "EVLease India",
        "role": "Program Manager",
        "quote": "We needed a reliable after-sales partner for multiple EV brands. Battwheels' EV-only focus and structured processes make them easy to work with at scale.",
        "rating": 5,
        "featured": False,
        "category": "leasing",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "name": "Suresh Kumar",
        "company": "CargoPower EVs",
        "role": "Fleet Owner",
        "quote": "Their understanding of motors, controllers, and wiring issues is far better than local garages. Battwheels has helped extend the life of our vehicles and reduce repeat failures.",
        "rating": 5,
        "featured": False,
        "category": "commercial",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "name": "Amit Yadav",
        "company": "SwiftKart Deliveries",
        "role": "Regional Operations Manager",
        "quote": "What stands out is speed. Most breakdowns are handled onsite within hours. Battwheels understands fleet pressure and works with that urgency.",
        "rating": 5,
        "featured": True,
        "category": "2w-fleet",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "name": "Deepak Rawat",
        "company": "CorpCab Electric",
        "role": "Fleet Supervisor",
        "quote": "Structured service, proper documentation, and reliable technicians — Battwheels brings discipline to EV maintenance, which is rare in this space.",
        "rating": 5,
        "featured": False,
        "category": "4w-fleet",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "name": "Vikram Chauhan",
        "company": "EV Motors India (OEM Partner)",
        "role": "Operations Director",
        "quote": "Battwheels understands OEM expectations around safety, diagnostic accuracy, and reporting. Their processes align well with professional EV after-sales standards.",
        "rating": 5,
        "featured": True,
        "category": "oem",
        "status": "active",
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]

async def seed_database():
    """Seed the database with sample data"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Starting database seeding...")
    
    # Clear existing data (optional - comment out if you want to preserve existing data)
    # await db.services.delete_many({})
    # await db.blogs.delete_many({})
    # await db.testimonials.delete_many({})
    
    # Insert Services
    print("\n📦 Seeding Services...")
    for service in services_data:
        existing = await db.services.find_one({"slug": service["slug"]})
        if not existing:
            await db.services.insert_one(service)
            print(f"  ✅ Added: {service['title']}")
        else:
            print(f"  ⏭️  Skipped (exists): {service['title']}")
    
    # Insert Blogs
    print("\n📝 Seeding Blog Posts...")
    for blog in blogs_data:
        existing = await db.blogs.find_one({"slug": blog["slug"]})
        if not existing:
            await db.blogs.insert_one(blog)
            print(f"  ✅ Added: {blog['title']}")
        else:
            print(f"  ⏭️  Skipped (exists): {blog['title']}")
    
    # Insert Testimonials
    print("\n💬 Seeding Testimonials...")
    for testimonial in testimonials_data:
        existing = await db.testimonials.find_one({"name": testimonial["name"], "company": testimonial["company"]})
        if not existing:
            await db.testimonials.insert_one(testimonial)
            print(f"  ✅ Added: {testimonial['name']} - {testimonial['company']}")
        else:
            print(f"  ⏭️  Skipped (exists): {testimonial['name']}")
    
    # Verify counts
    services_count = await db.services.count_documents({})
    blogs_count = await db.blogs.count_documents({})
    testimonials_count = await db.testimonials.count_documents({})
    
    print(f"\n✨ Seeding complete!")
    print(f"   Services: {services_count}")
    print(f"   Blogs: {blogs_count}")
    print(f"   Testimonials: {testimonials_count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
