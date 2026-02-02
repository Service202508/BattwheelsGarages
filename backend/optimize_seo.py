"""
SEO Optimization Script for Blog Posts
Fixes meta titles, descriptions, and ensures all SEO fields are properly set
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'test_database')

# Optimized SEO data for all 20 blog posts
SEO_OPTIMIZATIONS = {
    'onsite-ev-repair-near-me-delhi-ncr': {
        'meta_title': 'Onsite EV Repair Near Me Delhi NCR | Battwheels',
        'meta_desc': 'Professional onsite EV repair in Delhi NCR. Mobile diagnostics & repair at your location. 2-hour response, 85% onsite fix rate. Book now!',
        'tags': ['onsite EV repair', 'Delhi NCR', 'mobile EV service', 'EV diagnostics', 'EV repair near me'],
        'focus_keyword': 'onsite EV repair Delhi NCR'
    },
    'ev-roadside-assistance-fleet-operators-guide': {
        'meta_title': 'EV Roadside Assistance for Fleets | Battwheels',
        'meta_desc': 'Complete guide to EV roadside assistance for fleet operators. SLAs, response times, onsite resolution. Expert EV breakdown service.',
        'tags': ['EV roadside assistance', 'fleet operators', 'EV breakdown', 'RSA', 'fleet management'],
        'focus_keyword': 'EV roadside assistance fleet'
    },
    'electric-two-wheeler-service-noida-guide': {
        'meta_title': 'Electric Two-Wheeler Service Noida | Battwheels',
        'meta_desc': 'Complete guide to e-scooter service in Noida. Ather, Ola, TVS iQube maintenance & repairs. Expert 2W EV technicians.',
        'tags': ['electric two-wheeler', 'Noida', 'e-scooter service', 'Ather service', 'Ola service'],
        'focus_keyword': 'electric two-wheeler service Noida'
    },
    'choose-ev-service-plan-fleet-2w-3w-4w': {
        'meta_title': 'EV Service Plan for Fleet 2W 3W 4W | Battwheels',
        'meta_desc': 'Guide to choosing the right EV service plan for 2W, 3W, or 4W fleet. Compare plans, coverage, and costs.',
        'tags': ['EV service plan', 'fleet management', '2W 3W 4W', 'maintenance plan', 'fleet service'],
        'focus_keyword': 'EV service plan fleet'
    },
    'ev-battery-health-check-diagnostics-costs': {
        'meta_title': 'EV Battery Health Check & Diagnostics | Battwheels',
        'meta_desc': 'Complete guide to EV battery health checks. Cell-level diagnostics, BMS analysis, capacity testing. Protect your battery.',
        'tags': ['EV battery', 'battery health', 'diagnostics', 'BMS', 'battery maintenance'],
        'focus_keyword': 'EV battery health check'
    },
    'preventive-maintenance-checklist-ev-fleets': {
        'meta_title': 'EV Fleet Preventive Maintenance Checklist',
        'meta_desc': 'Complete preventive maintenance checklist for EV fleets. Daily, weekly, monthly checks. Reduce downtime by 40%.',
        'tags': ['preventive maintenance', 'EV fleet', 'checklist', 'reduce downtime', 'fleet maintenance'],
        'focus_keyword': 'EV fleet preventive maintenance'
    },
    'bldc-motor-repair-troubleshooting-e-scooters': {
        'meta_title': 'BLDC Motor Repair for E-Scooters | Battwheels',
        'meta_desc': 'BLDC motor repair guide for electric scooters. Common problems, troubleshooting steps, when to seek professional help.',
        'tags': ['BLDC motor', 'e-scooter repair', 'motor troubleshooting', 'electric motor', 'EV repair'],
        'focus_keyword': 'BLDC motor repair e-scooter'
    },
    'e-rickshaw-maintenance-battery-swapping-best-practices': {
        'meta_title': 'E-Rickshaw Maintenance & Battery Swapping Tips',
        'meta_desc': 'E-rickshaw maintenance guide. Battery swapping best practices, daily checklist, common problems. Maximize lifespan.',
        'tags': ['e-rickshaw', 'battery swapping', 'maintenance', 'electric three-wheeler', 'e-rickshaw service'],
        'focus_keyword': 'e-rickshaw maintenance'
    },
    'telematics-battwheels-os-integration-fleet-uptime': {
        'meta_title': 'Battwheels OS Telematics Integration | Fleet',
        'meta_desc': 'How Battwheels OS integrates with telematics for predictive maintenance. Reduce fleet downtime by 35%.',
        'tags': ['Battwheels OS', 'telematics', 'fleet management', 'predictive maintenance', 'fleet uptime'],
        'focus_keyword': 'telematics fleet management'
    },
    'reduce-ev-downtime-case-studies-delhi-noida': {
        'meta_title': 'EV Fleet Case Studies Delhi NCR | Battwheels',
        'meta_desc': 'Real case studies: How Battwheels reduced EV fleet downtime by 72% for delivery and logistics fleets in Delhi-Noida.',
        'tags': ['case study', 'fleet management', 'Delhi NCR', 'reduce downtime', 'EV fleet'],
        'focus_keyword': 'reduce EV downtime case study'
    },
    'custom-sla-ev-fleets-what-to-ask-service-provider': {
        'meta_title': 'Custom SLA for EV Fleets | Service Agreement',
        'meta_desc': 'Guide to negotiating SLAs with EV service providers. Key elements, red flags, questions to ask.',
        'tags': ['SLA', 'service agreement', 'fleet service', 'EV maintenance', 'service contract'],
        'focus_keyword': 'SLA EV fleet service'
    },
    'top-signs-need-ev-diagnostic-software-hardware': {
        'meta_title': 'Professional EV Diagnostics - When You Need It',
        'meta_desc': '5 signs you need professional EV diagnostic tools beyond OBD. Cell-level battery analysis and more.',
        'tags': ['EV diagnostics', 'OBD scanner', 'professional tools', 'battery diagnostics', 'EV testing'],
        'focus_keyword': 'professional EV diagnostics'
    },
    'monthly-vs-annual-ev-service-plans-comparison': {
        'meta_title': 'Monthly vs Annual EV Service Plans Compared',
        'meta_desc': 'Detailed comparison of monthly vs annual EV service plans. Real cost analysis and ROI breakdown.',
        'tags': ['service plan comparison', 'monthly vs annual', 'EV maintenance cost', 'fleet budget'],
        'focus_keyword': 'EV service plan comparison'
    },
    'battwheels-garages-reviews-customer-stories-delhi-noida': {
        'meta_title': 'Battwheels Reviews | Customer Stories Delhi NCR',
        'meta_desc': 'Real reviews from Battwheels customers in Delhi NCR. EV owners and fleet operators share experiences.',
        'tags': ['reviews', 'customer stories', 'testimonials', 'Delhi NCR', 'Battwheels reviews'],
        'focus_keyword': 'Battwheels Garages reviews'
    },
    'spot-poor-quality-throttles-counterfeit-ev-parts': {
        'meta_title': 'Spot Counterfeit EV Parts | Quality Guide',
        'meta_desc': 'How to identify poor-quality and counterfeit EV parts. Protect your vehicle from fake components.',
        'tags': ['counterfeit parts', 'EV safety', 'quality parts', 'throttle', 'fake EV parts'],
        'focus_keyword': 'counterfeit EV parts'
    },
    'ev-charging-habits-extend-battery-life-tips': {
        'meta_title': 'EV Charging Tips to Extend Battery Life',
        'meta_desc': 'Expert tips on EV charging habits that extend battery life. The 20-80 rule and more.',
        'tags': ['EV charging', 'battery life', 'charging tips', 'battery maintenance', 'extend battery'],
        'focus_keyword': 'EV charging extend battery life'
    },
    'onsite-ev-repair-safety-protocols-certifications': {
        'meta_title': 'EV Repair Safety Protocols & Certifications',
        'meta_desc': 'EV repair safety protocols and technician certifications explained. High-voltage safety, PPE requirements.',
        'tags': ['EV safety', 'technician certification', 'high voltage', 'safety protocols', 'EV repair'],
        'focus_keyword': 'EV repair safety certification'
    },
    'cost-comparison-ev-maintenance-vs-ice-vehicles-roi-fleets': {
        'meta_title': 'EV vs ICE Maintenance Cost | Fleet ROI',
        'meta_desc': 'EV vs ICE vehicle maintenance cost comparison for fleets. Real numbers, TCO analysis, ROI breakdown.',
        'tags': ['EV vs ICE', 'maintenance cost', 'TCO', 'fleet ROI', 'cost comparison'],
        'focus_keyword': 'EV vs ICE maintenance cost'
    },
    'monthly-performance-reports-fleet-lower-downtime': {
        'meta_title': 'Fleet Performance Reports | Reduce Downtime',
        'meta_desc': 'How fleet managers use monthly performance reports to reduce downtime. Key metrics and data analytics.',
        'tags': ['fleet management', 'performance reports', 'data analytics', 'downtime reduction'],
        'focus_keyword': 'fleet performance reports'
    },
    'scale-aftersales-ev-oem-lessons-battwheels': {
        'meta_title': 'Scale EV Aftersales for OEMs | Battwheels',
        'meta_desc': 'How EV OEMs can scale aftersales without heavy investment. Partnership model and case studies.',
        'tags': ['EV OEM', 'aftersales', 'partnership', 'service network', 'OEM service'],
        'focus_keyword': 'scale EV aftersales OEM'
    }
}


async def optimize_seo():
    """
    Update all blog posts with optimized SEO data
    """
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Connecting to MongoDB...")
    print(f"Database: {db_name}")
    print("")
    print("Optimizing SEO for all blog posts...")
    print("=" * 60)
    
    updated_count = 0
    
    for slug, seo_data in SEO_OPTIMIZATIONS.items():
        # Find blog by slug
        blog = await db.blog_posts.find_one({"slug": slug})
        
        if blog:
            # Verify meta_title length
            meta_title = seo_data['meta_title']
            if len(meta_title) > 60:
                print(f"⚠️  WARNING: {slug} meta_title still > 60 chars ({len(meta_title)})")
                meta_title = meta_title[:57] + "..."
            
            # Verify meta_desc length
            meta_desc = seo_data['meta_desc']
            if len(meta_desc) > 160:
                print(f"⚠️  WARNING: {slug} meta_desc still > 160 chars ({len(meta_desc)})")
                meta_desc = meta_desc[:157] + "..."
            
            # Update blog with optimized SEO
            update_data = {
                "meta_title": meta_title,
                "meta_desc": meta_desc,
                "tags": seo_data['tags'],
                "focus_keyword": seo_data['focus_keyword'],
                "is_published": True,
                "updated_at": datetime.now(timezone.utc)
            }
            
            await db.blog_posts.update_one(
                {"slug": slug},
                {"$set": update_data}
            )
            
            print(f"✅ {slug}")
            print(f"   Title: {meta_title} ({len(meta_title)} chars)")
            updated_count += 1
        else:
            print(f"❌ NOT FOUND: {slug}")
    
    print("")
    print("=" * 60)
    print(f"SEO Optimization Complete! Updated {updated_count} blog posts")
    
    # Verify updates
    print("")
    print("Verification - checking all blogs have proper SEO:")
    cursor = db.blog_posts.find({})
    all_valid = True
    async for blog in cursor:
        issues = []
        if not blog.get('meta_title'):
            issues.append('missing meta_title')
        elif len(blog.get('meta_title', '')) > 60:
            issues.append(f"meta_title too long ({len(blog['meta_title'])})")
        
        if not blog.get('meta_desc'):
            issues.append('missing meta_desc')
        elif len(blog.get('meta_desc', '')) > 160:
            issues.append(f"meta_desc too long ({len(blog['meta_desc'])})")
        
        if not blog.get('is_published'):
            issues.append('not published')
        
        if issues:
            print(f"⚠️  {blog['slug']}: {', '.join(issues)}")
            all_valid = False
    
    if all_valid:
        print("✅ All blog posts have valid SEO configuration!")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(optimize_seo())
