from fastapi import APIRouter
from fastapi.responses import Response
from datetime import datetime

router = APIRouter(tags=["seo"])

# All blog slugs from mockData.js - these are the 20 SEO-optimized articles
BLOG_SLUGS = [
    'onsite-ev-repair-near-me-delhi-ncr',
    'ev-roadside-assistance-fleet-operators-guide',
    'electric-two-wheeler-service-noida-guide',
    'choose-ev-service-plan-fleet-2w-3w-4w',
    'ev-battery-health-check-diagnostics-costs',
    'preventive-maintenance-checklist-ev-fleets',
    'bldc-motor-repair-troubleshooting-e-scooters',
    'e-rickshaw-maintenance-battery-swapping-best-practices',
    'telematics-battwheels-os-integration-fleet-uptime',
    'reduce-ev-downtime-case-studies-delhi-noida',
    'custom-sla-ev-fleets-what-to-ask-service-provider',
    'top-signs-need-ev-diagnostic-software-hardware',
    'monthly-vs-annual-ev-service-plans-comparison',
    'battwheels-garages-reviews-customer-stories-delhi-noida',
    'spot-poor-quality-throttles-counterfeit-ev-parts',
    'ev-charging-habits-extend-battery-life-tips',
    'onsite-ev-repair-safety-protocols-certifications',
    'cost-comparison-ev-maintenance-vs-ice-vehicles-roi-fleets',
    'monthly-performance-reports-fleet-lower-downtime',
    'scale-aftersales-ev-oem-lessons-battwheels',
]

# Static pages
STATIC_PAGES = [
    {'loc': '/', 'changefreq': 'weekly', 'priority': '1.0'},
    {'loc': '/about', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services', 'changefreq': 'weekly', 'priority': '0.9'},
    {'loc': '/services/periodic', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services/motor-controller', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services/battery-bms', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services/charger', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services/brakes-tyres', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services/body-paint', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services/roadside', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/services/fleet', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/blog', 'changefreq': 'daily', 'priority': '0.9'},
    {'loc': '/careers', 'changefreq': 'weekly', 'priority': '0.7'},
    {'loc': '/contact', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/book-service', 'changefreq': 'monthly', 'priority': '0.9'},
    {'loc': '/fleet-oem', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/battwheels-os', 'changefreq': 'monthly', 'priority': '0.7'},
    {'loc': '/industries', 'changefreq': 'monthly', 'priority': '0.7'},
    {'loc': '/plans', 'changefreq': 'monthly', 'priority': '0.8'},
    {'loc': '/faq', 'changefreq': 'monthly', 'priority': '0.6'},
]

@router.get("/api/sitemap.xml")
async def generate_sitemap():
    """
    Generate dynamic XML sitemap including all blog posts
    """
    base_url = "https://battwheelsgarages.in"
    today = datetime.now().strftime("%Y-%m-%d")
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Add static pages
    for page in STATIC_PAGES:
        xml_content += f'''  <url>
    <loc>{base_url}{page['loc']}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{page['changefreq']}</changefreq>
    <priority>{page['priority']}</priority>
  </url>\n'''
    
    # Add all blog posts
    for slug in BLOG_SLUGS:
        xml_content += f'''  <url>
    <loc>{base_url}/blog/{slug}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>\n'''
    
    xml_content += '</urlset>'
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Type": "application/xml; charset=utf-8",
            "Cache-Control": "public, max-age=3600"
        }
    )

@router.get("/api/seo/blog-urls")
async def get_blog_urls():
    """
    Return list of all blog URLs for SEO verification
    """
    base_url = "https://battwheelsgarages.in"
    return {
        "total_blogs": len(BLOG_SLUGS),
        "blog_urls": [f"{base_url}/blog/{slug}" for slug in BLOG_SLUGS]
    }
