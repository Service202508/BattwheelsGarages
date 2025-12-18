"""
Seed job postings for Battwheels Garages Careers page
Run this script to populate the jobs collection
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from uuid import uuid4

# Job postings data
JOBS = [
    {
        "id": str(uuid4()),
        "title": "EV Technician - Field Service",
        "department": "Operations",
        "location": "Delhi NCR",
        "type": "Full-time",
        "experience": "1-3 years",
        "description": "Join our field service team to diagnose and repair electric vehicles onsite. You'll work with cutting-edge EV technology including batteries, motors, controllers, and BMS systems.",
        "responsibilities": [
            "Perform onsite EV diagnosis and repair for 2W, 3W, and 4W vehicles",
            "Use diagnostic tools to identify electrical and mechanical issues",
            "Maintain service records and update job status in Battwheels OS",
            "Provide excellent customer service and communication",
            "Follow safety protocols for high-voltage EV systems"
        ],
        "requirements": [
            "ITI/Diploma in Electrical or Automobile Engineering",
            "1-3 years experience in EV or automobile repair",
            "Knowledge of EV components: batteries, motors, controllers",
            "Valid driving license (2W mandatory, 4W preferred)",
            "Good communication skills in Hindi and English"
        ],
        "benefits": [
            "Competitive salary + incentives",
            "Health insurance for self and family",
            "EV training and certifications",
            "Career growth opportunities",
            "Tools and equipment provided"
        ],
        "salary_range": "₹18,000 - ₹30,000 per month",
        "is_active": True,
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Senior EV Diagnostic Engineer",
        "department": "Technical",
        "location": "Bengaluru",
        "type": "Full-time",
        "experience": "3-5 years",
        "description": "Lead our technical team in advanced EV diagnostics. Work on complex cases involving BMS calibration, motor controller programming, and CAN bus analysis.",
        "responsibilities": [
            "Diagnose complex EV issues using advanced diagnostic tools",
            "Perform BMS calibration and battery health assessments",
            "Train junior technicians on EV repair procedures",
            "Develop diagnostic protocols for new EV models",
            "Liaise with OEMs for technical support and parts"
        ],
        "requirements": [
            "B.Tech/B.E. in Electrical/Electronics Engineering",
            "3-5 years experience in EV diagnostics",
            "Expertise in BMS, motor controllers, and CAN protocols",
            "Experience with diagnostic tools like OBD scanners",
            "Strong problem-solving and analytical skills"
        ],
        "benefits": [
            "Competitive salary package",
            "Performance bonuses",
            "Health and life insurance",
            "Professional development budget",
            "Flexible work arrangements"
        ],
        "salary_range": "₹45,000 - ₹70,000 per month",
        "is_active": True,
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Fleet Account Manager",
        "department": "Sales",
        "location": "Mumbai",
        "type": "Full-time",
        "experience": "2-4 years",
        "description": "Manage relationships with fleet operators and drive B2B sales. You'll work with logistics companies, e-commerce fleets, and OEMs to provide comprehensive EV service solutions.",
        "responsibilities": [
            "Acquire and manage fleet operator accounts",
            "Present Battwheels service solutions to potential clients",
            "Negotiate SLAs and service contracts",
            "Coordinate with operations team for service delivery",
            "Achieve monthly and quarterly sales targets"
        ],
        "requirements": [
            "Bachelor's degree in Business/Marketing",
            "2-4 years B2B sales experience (automotive/logistics preferred)",
            "Understanding of EV ecosystem and fleet operations",
            "Strong presentation and negotiation skills",
            "Proficiency in CRM tools and MS Office"
        ],
        "benefits": [
            "Base salary + attractive commissions",
            "Company vehicle or travel allowance",
            "Health insurance",
            "Quarterly performance bonuses",
            "Stock options for high performers"
        ],
        "salary_range": "₹35,000 - ₹55,000 per month + incentives",
        "is_active": True,
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Operations Coordinator",
        "department": "Operations",
        "location": "Delhi NCR",
        "type": "Full-time",
        "experience": "1-2 years",
        "description": "Coordinate daily operations including technician dispatch, job scheduling, and customer communication. Be the backbone of our service delivery.",
        "responsibilities": [
            "Schedule and dispatch technicians for service calls",
            "Monitor job progress and update customers",
            "Coordinate spare parts and inventory",
            "Handle customer queries and escalations",
            "Generate daily/weekly operations reports"
        ],
        "requirements": [
            "Graduate in any discipline",
            "1-2 years experience in operations/logistics",
            "Excellent communication skills",
            "Proficiency in MS Excel and Google Sheets",
            "Ability to work in shifts"
        ],
        "benefits": [
            "Competitive salary",
            "Health insurance",
            "Performance incentives",
            "Fast-track career growth",
            "Learning opportunities"
        ],
        "salary_range": "₹20,000 - ₹28,000 per month",
        "is_active": True,
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Full Stack Developer",
        "department": "Technology",
        "location": "Remote / Delhi NCR",
        "type": "Full-time",
        "experience": "2-4 years",
        "description": "Build and maintain Battwheels OS - our EV service management platform. Work on React frontend, FastAPI backend, and MongoDB database.",
        "responsibilities": [
            "Develop features for Battwheels OS platform",
            "Build RESTful APIs and integrate third-party services",
            "Optimize application performance and scalability",
            "Write clean, maintainable code with proper documentation",
            "Collaborate with product team on feature requirements"
        ],
        "requirements": [
            "B.Tech/B.E. in Computer Science or equivalent",
            "2-4 years experience in full-stack development",
            "Proficiency in React.js, Python/FastAPI, MongoDB",
            "Experience with AWS or GCP",
            "Understanding of CI/CD and DevOps practices"
        ],
        "benefits": [
            "Competitive salary",
            "Remote work flexibility",
            "Health insurance",
            "Learning budget",
            "Stock options"
        ],
        "salary_range": "₹50,000 - ₹80,000 per month",
        "is_active": True,
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid4()),
        "title": "Customer Support Executive",
        "department": "Customer Success",
        "location": "Delhi NCR",
        "type": "Full-time",
        "experience": "0-2 years",
        "description": "Be the first point of contact for our customers. Handle service inquiries, booking requests, and ensure customer satisfaction.",
        "responsibilities": [
            "Handle inbound calls and chat queries",
            "Book service appointments and track job status",
            "Resolve customer complaints and escalations",
            "Follow up with customers post-service",
            "Maintain customer records in CRM"
        ],
        "requirements": [
            "Graduate in any discipline",
            "0-2 years customer service experience",
            "Excellent communication in Hindi and English",
            "Basic computer skills",
            "Customer-first attitude"
        ],
        "benefits": [
            "Fixed salary + incentives",
            "Health insurance",
            "Rotational shifts with allowances",
            "Career growth to team lead roles",
            "Training and certifications"
        ],
        "salary_range": "₹15,000 - ₹22,000 per month",
        "is_active": True,
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
]

async def seed_jobs():
    client = AsyncIOMotorClient("os.environ.get("MONGO_URL", "mongodb://localhost:27017")")
    db = client["test_database"]
    
    # Clear existing jobs
    await db.jobs.delete_many({})
    print("Cleared existing jobs")
    
    # Insert new jobs
    result = await db.jobs.insert_many(JOBS)
    print(f"Inserted {len(result.inserted_ids)} job postings")
    
    # Verify
    count = await db.jobs.count_documents({})
    print(f"Total jobs in database: {count}")
    
    # List jobs
    async for job in db.jobs.find({}, {"title": 1, "department": 1, "location": 1}):
        print(f"  - {job['title']} ({job['department']}) - {job['location']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_jobs())
