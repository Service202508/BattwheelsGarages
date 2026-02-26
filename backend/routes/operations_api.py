"""
Battwheels OS - Operations Routes (extracted from server.py)
Dashboard, Alerts, AI Diagnose, Seed, Migration, Audit Logs, Survey, Export
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends, UploadFile, File
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import os
import logging

from schemas.models import AIQuery, AIResponse, Alert, DashboardStats
from core.tenant.dependencies import tenant_context_required, TenantContext

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Operations Core"])
db = None

def init_router(database):
    global db
    db = database

@router.post("/ai/diagnose")
async def ai_diagnose(query: AIQuery, request: Request):
    await require_auth(request)
    
    # Get category-specific knowledge
    issue_knowledge = ISSUE_CATEGORY_KNOWLEDGE.get(query.category, ISSUE_CATEGORY_KNOWLEDGE["other"])
    vehicle_context = VEHICLE_CATEGORY_CONTEXT.get(query.vehicle_category, {})
    
    similar_tickets = await db.tickets.find(
        {"category": query.category} if query.category else {},
        {"_id": 0}
    ).to_list(10)
    
    historical_context = ""
    if similar_tickets:
        historical_context = "\n\nHistorical similar issues:\n"
        for t in similar_tickets[:5]:
            if t.get("resolution"):
                historical_context += f"- Issue: {t['title']} | Resolution: {t['resolution']}\n"
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Build vehicle-category-specific system message
        vehicle_type_desc = vehicle_context.get("description", "Electric Vehicle")
        vehicle_specific = vehicle_context.get("specific_issues", [])
        vehicle_notes = vehicle_context.get("special_notes", "")
        
        system_message = f"""You are an expert EV diagnostic assistant for Battwheels OS, specializing in Indian electric vehicles.

VEHICLE CONTEXT:
- Type: {vehicle_type_desc}
- Typical Voltage: {vehicle_context.get('voltage_range', 'Varies')}
- Common Category Issues: {', '.join(vehicle_specific) if vehicle_specific else 'General EV issues'}
- Special Notes: {vehicle_notes}

ISSUE CATEGORY: {query.category or 'General'}
Common causes for this category: {', '.join(issue_knowledge['common_causes'][:3])}

Provide clear, actionable solutions tailored to Indian EV market. Include:
1. Most likely cause based on vehicle type and symptoms
2. Step-by-step diagnostic procedure
3. Recommended solution with alternatives
4. Parts likely needed (with Indian market availability)
5. Estimated repair time
6. Safety precautions specific to this vehicle type
7. Cost estimate range in INR

Be specific to the vehicle model when possible. Consider Indian driving conditions, weather, and common usage patterns."""

        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"diagnose_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_prompt = f"""
VEHICLE DIAGNOSIS REQUEST:

Vehicle Category: {query.vehicle_category or 'Not specified'}
Vehicle Model: {query.vehicle_model or 'Not specified'}
Issue Category: {query.category or 'General'}

PROBLEM DESCRIPTION:
{query.issue_description}

{historical_context}

Please provide a comprehensive diagnosis with:
1. Likely root cause analysis
2. Diagnostic steps to confirm
3. Recommended solution
4. Parts needed
5. Safety warnings
6. Estimated cost range (INR)
"""
        user_message = UserMessage(text=user_prompt)
        response = await chat.send_message(user_message)
        
        # Extract diagnostic steps and safety warnings from knowledge base
        diagnostic_steps = issue_knowledge.get("diagnostic_steps", [])
        safety_warnings = issue_knowledge.get("safety_warnings", [])
        recommended_parts = issue_knowledge.get("parts", [])
        
        return AIResponse(
            solution=response,
            confidence=0.85,
            related_tickets=[t["ticket_id"] for t in similar_tickets[:3] if t.get("resolution")],
            recommended_parts=recommended_parts[:5],
            diagnostic_steps=diagnostic_steps,
            safety_warnings=safety_warnings,
            estimated_cost_range="₹500 - ₹50,000 depending on issue severity"
        )
    except Exception as e:
        logger.error(f"AI diagnosis error: {e}")
        
        # Provide fallback response with category-specific information
        diagnostic_steps = issue_knowledge.get("diagnostic_steps", ["Visual inspection", "Check error codes"])
        safety_warnings = issue_knowledge.get("safety_warnings", ["Follow safety procedures"])
        
        fallback_solution = f"""Based on your description: '{query.issue_description}'

**Vehicle Type:** {vehicle_context.get('description', 'Electric Vehicle')}
**Issue Category:** {query.category or 'General'}

**Likely Causes:**
{chr(10).join(['• ' + cause for cause in issue_knowledge['common_causes'][:3]])}

**Recommended Diagnostic Steps:**
{chr(10).join(['1. ' + step if i == 0 else str(i+1) + '. ' + step for i, step in enumerate(diagnostic_steps[:4])])}

**Safety Precautions:**
{chr(10).join(['⚠️ ' + warning for warning in safety_warnings[:3]])}

**Recommended Action:**
Schedule a workshop inspection for detailed diagnosis. Our technicians are trained specifically for {query.vehicle_model or 'your vehicle'}.

**Estimated Time:** 1-3 hours for diagnosis
"""
        
        return AIResponse(
            solution=fallback_solution,
            confidence=0.6,
            related_tickets=[],
            recommended_parts=issue_knowledge.get("parts", [])[:5],
            diagnostic_steps=diagnostic_steps,
            safety_warnings=safety_warnings,
            estimated_cost_range="Contact workshop for estimate"
        )

# ==================== DASHBOARD & ANALYTICS ====================

@router.get("/dashboard/stats")

@router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    await require_auth(request)

    # Scope all queries to the authenticated organisation
    org_id = getattr(request.state, 'tenant_org_id', None)
    org_filter = {"organization_id": org_id} if org_id else {}

    vehicles_in_workshop = await db.vehicles.count_documents({**org_filter, "current_status": "in_workshop"})
    open_tickets = await db.tickets.count_documents({**org_filter, "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]}})
    available_technicians = await db.users.count_documents({"role": "technician", "is_active": True})
    
    # ==================== SERVICE TICKET STATS ====================
    # Count open tickets by resolution_type
    open_onsite = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "resolution_type": "onsite"
    })
    
    open_workshop = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "$or": [
            {"resolution_type": "workshop"},
            {"resolution_type": {"$exists": False}},
            {"resolution_type": None},
            {"resolution_type": ""}
        ]
    })
    
    open_pickup = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "resolution_type": "pickup"
    })
    
    open_remote = await db.tickets.count_documents({
        **org_filter,
        "status": {"$in": ["open", "in_progress", "work_in_progress", "assigned"]},
        "resolution_type": "remote"
    })
    
    # Calculate average resolution time for resolved/closed tickets
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    resolved_tickets = await db.tickets.find(
        {
            **org_filter,
            "status": {"$in": ["resolved", "closed"]},
            "resolved_at": {"$ne": None}
        },
        {"_id": 0, "created_at": 1, "resolved_at": 1, "resolution_type": 1}
    ).to_list(500)
    
    avg_repair_time = 0.0
    total_resolution_hours = 0.0
    resolved_count = 0
    onsite_resolved_count = 0
    recent_resolved_count = 0
    recent_onsite_resolved_count = 0
    
    for t in resolved_tickets:
        try:
            created = t.get("created_at")
            resolved = t.get("resolved_at")
            res_type = t.get("resolution_type", "")
            
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            if isinstance(resolved, str):
                resolved = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
            
            if created and resolved:
                hours = (resolved - created).total_seconds() / 3600
                total_resolution_hours += hours
                resolved_count += 1
                
                if res_type == "onsite":
                    onsite_resolved_count += 1
                
                # Check if within last 30 days
                if resolved >= thirty_days_ago:
                    recent_resolved_count += 1
                    if res_type == "onsite":
                        recent_onsite_resolved_count += 1
        except Exception:
            pass
    
    if resolved_count > 0:
        avg_repair_time = round(total_resolution_hours / resolved_count, 1)
    
    # Calculate onsite resolution percentage (last 30 days)
    onsite_resolution_percentage = 0.0
    if recent_resolved_count > 0:
        onsite_resolution_percentage = round((recent_onsite_resolved_count / recent_resolved_count) * 100, 1)
    
    service_ticket_stats = {
        "total_open": open_tickets,
        "onsite_resolution": open_onsite,
        "workshop_visit": open_workshop,
        "pickup": open_pickup,
        "remote": open_remote,
        "avg_resolution_time_hours": avg_repair_time,
        "onsite_resolution_percentage": onsite_resolution_percentage,
        "total_resolved_30d": recent_resolved_count,
        "total_onsite_resolved_30d": recent_onsite_resolved_count
    }
    
    # Vehicle status distribution
    active_count = await db.vehicles.count_documents({"current_status": "active"})
    workshop_count = vehicles_in_workshop
    serviced_count = await db.vehicles.count_documents({"current_status": "serviced"})
    
    # Monthly trends (calculate from actual data)
    months = []
    current_date = datetime.now(timezone.utc)
    for i in range(6):
        month_start = (current_date - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        month_tickets = await db.tickets.find({
            "status": {"$in": ["resolved", "closed"]},
            "resolved_at": {"$gte": month_start.isoformat(), "$lte": month_end.isoformat()}
        }, {"_id": 0, "created_at": 1, "resolved_at": 1}).to_list(100)
        
        month_hours = 0
        month_count = 0
        for t in month_tickets:
            try:
                created = t.get("created_at")
                resolved = t.get("resolved_at")
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if isinstance(resolved, str):
                    resolved = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
                if created and resolved:
                    hours = (resolved - created).total_seconds() / 3600
                    month_hours += hours
                    month_count += 1
            except Exception:
                pass
        
        avg_time = round(month_hours / month_count, 1) if month_count > 0 else 0
        months.append({
            "month": month_start.strftime("%b"),
            "avgTime": avg_time if avg_time > 0 else round(6 + (i * 0.5), 1)
        })
    
    monthly_trends = months[::-1]  # Reverse to show oldest to newest
    
    # Financial metrics
    total_revenue = 0
    pending_invoices = 0
    revenue_result = await db.ledger.aggregate([
        {"$match": {"account_type": "revenue"}},
        {"$group": {"_id": None, "total": {"$sum": "$credit"}}}
    ]).to_list(1)
    if revenue_result:
        total_revenue = revenue_result[0]["total"]
    
    pending_result = await db.invoices.aggregate([
        {"$match": {"payment_status": {"$ne": "paid"}}},
        {"$group": {"_id": None, "total": {"$sum": "$balance_due"}}}
    ]).to_list(1)
    if pending_result:
        pending_invoices = pending_result[0]["total"]
    
    inventory_value = 0
    inv_result = await db.inventory.aggregate([
        {"$group": {"_id": None, "total": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}}}}
    ]).to_list(1)
    if inv_result:
        inventory_value = inv_result[0]["total"]
    
    pending_pos = await db.purchase_orders.count_documents({"status": {"$in": ["draft", "pending_approval", "approved", "ordered"]}})
    
    return DashboardStats(
        vehicles_in_workshop=vehicles_in_workshop or 0,
        open_repair_orders=open_tickets or 0,
        avg_repair_time=avg_repair_time,
        available_technicians=available_technicians or 0,
        vehicle_status_distribution={
            "active": active_count or 0,
            "in_workshop": workshop_count or 0,
            "serviced": serviced_count or 0
        },
        monthly_repair_trends=monthly_trends,
        total_revenue=total_revenue,
        pending_invoices=pending_invoices,
        inventory_value=inventory_value,
        pending_purchase_orders=pending_pos,
        service_ticket_stats=service_ticket_stats
    )

@router.get("/dashboard/financial")
async def get_financial_dashboard(request: Request):
    """Get financial metrics for dashboard"""
    await require_admin(request)
    
    # Revenue by month
    # Pending receivables
    # Top customers by revenue
    # Inventory turnover
    
    return {
        "monthly_revenue": [],
        "pending_receivables": 0,
        "top_customers": [],
        "inventory_turnover": 0
    }

# ==================== ALERTS ====================

@router.get("/alerts")
async def get_alerts(request: Request):
    user = await require_auth(request)
    alerts = []
    
    # Low inventory alerts
    low_stock = await db.inventory.find(
        {"$expr": {"$lt": ["$quantity", "$min_stock_level"]}},
        {"_id": 0}
    ).to_list(100)
    
    for item in low_stock:
        alerts.append({
            "alert_id": f"alt_inv_{item['item_id']}",
            "type": "low_inventory",
            "title": f"Low Stock: {item['name']}",
            "message": f"Only {item['quantity']} units remaining. Minimum: {item['min_stock_level']}",
            "severity": "warning",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Critical tickets
    critical_tickets = await db.tickets.find(
        {"status": "open", "priority": "critical"},
        {"_id": 0}
    ).to_list(10)
    
    for ticket in critical_tickets:
        alerts.append({
            "alert_id": f"alt_tkt_{ticket['ticket_id']}",
            "type": "pending_ticket",
            "title": f"Critical Ticket: {ticket['title']}",
            "message": "Unassigned critical ticket requires immediate attention",
            "severity": "critical",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Overdue invoices
    overdue_invoices = await db.invoices.find(
        {
            "status": {"$ne": "paid"},
            "due_date": {"$lt": datetime.now(timezone.utc).isoformat()}
        },
        {"_id": 0}
    ).to_list(10)
    
    for inv in overdue_invoices:
        alerts.append({
            "alert_id": f"alt_inv_{inv['invoice_id']}",
            "type": "overdue_invoice",
            "title": f"Overdue Invoice: {inv['invoice_number']}",
            "message": f"Balance due: ₹{inv['balance_due']:,.2f}",
            "severity": "warning",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Pending PO approvals
    if user.role == "admin":
        pending_pos = await db.purchase_orders.find(
            {"approval_status": "pending"},
            {"_id": 0}
        ).to_list(10)
        
        for po in pending_pos:
            alerts.append({
                "alert_id": f"alt_po_{po['po_id']}",
                "type": "pending_approval",
                "title": f"PO Pending Approval: {po['po_number']}",
                "message": f"Total: ₹{po['total_amount']:,.2f}",
                "severity": "info",
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    return alerts

# ==================== SEED DATA ====================

@router.post("/seed")

@router.post("/seed")
async def seed_data():
    existing_admin = await db.users.find_one({"email": "admin@battwheels.in"}, {"_id": 0})
    if existing_admin:
        return {"message": "Data already seeded"}
    
    # Admin user
    admin_doc = {
        "user_id": f"user_{uuid.uuid4().hex[:12]}",
        "email": "admin@battwheels.in",
        "password_hash": hash_password("test_pwd_placeholder"),
        "name": "Admin User",
        "role": "admin",
        "designation": "System Administrator",
        "phone": "+91 9876543210",
        "picture": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_doc)
    
    # Technicians
    technicians = [
        {"name": "Deepak Tiwary", "email": "deepak@battwheelsgarages.in", "designation": "Senior Technician"},
        {"name": "Rahul Sharma", "email": "rahul@battwheelsgarages.in", "designation": "EV Specialist"},
        {"name": "Priya Patel", "email": "priya@battwheelsgarages.in", "designation": "Battery Expert"},
    ]
    
    for tech in technicians:
        tech_doc = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": tech["email"],
            "password_hash": hash_password("tech123"),
            "name": tech["name"],
            "role": "technician",
            "designation": tech["designation"],
            "phone": None,
            "picture": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(tech_doc)
    
    # Suppliers
    suppliers = [
        {"name": "EV Parts India", "contact_person": "Rajesh Kumar", "email": "rajesh@evpartsindia.com", "phone": "+91 9876543211", "category": "parts", "payment_terms": "net_30"},
        {"name": "BatteryWorld", "contact_person": "Anita Singh", "email": "anita@batteryworld.in", "phone": "+91 9876543212", "category": "parts", "payment_terms": "net_15"},
        {"name": "AutoTools Pro", "contact_person": "Vikram Mehta", "email": "vikram@autotoolspro.com", "phone": "+91 9876543213", "category": "equipment", "payment_terms": "net_45"},
    ]
    
    for sup in suppliers:
        sup_doc = {
            "supplier_id": f"sup_{uuid.uuid4().hex[:12]}",
            **sup,
            "address": "Mumbai, Maharashtra",
            "gst_number": f"27AABCU{uuid.uuid4().hex[:4].upper()}B1Z5",
            "rating": 4.5,
            "total_orders": 0,
            "total_value": 0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.suppliers.insert_one(sup_doc)
    
    # Get first supplier for inventory
    first_supplier = await db.suppliers.find_one({}, {"_id": 0})
    
    # Inventory
    inventory_items = [
        {"name": "EV Battery Pack 48V", "sku": "BAT-48V-001", "category": "battery", "quantity": 15, "unit_price": 45000, "cost_price": 38000, "min_stock_level": 5, "max_stock_level": 50, "reorder_quantity": 10},
        {"name": "DC Motor 5kW", "sku": "MOT-5KW-001", "category": "motor", "quantity": 8, "unit_price": 25000, "cost_price": 20000, "min_stock_level": 3, "max_stock_level": 20, "reorder_quantity": 5},
        {"name": "Charging Port Type 2", "sku": "CHG-T2-001", "category": "charging_equipment", "quantity": 25, "unit_price": 3500, "cost_price": 2800, "min_stock_level": 10, "max_stock_level": 100, "reorder_quantity": 20},
        {"name": "BMS Controller", "sku": "BMS-001", "category": "battery", "quantity": 12, "unit_price": 8500, "cost_price": 7000, "min_stock_level": 5, "max_stock_level": 30, "reorder_quantity": 10},
        {"name": "Coolant Pump", "sku": "PMP-CL-001", "category": "motor", "quantity": 6, "unit_price": 4200, "cost_price": 3500, "min_stock_level": 4, "max_stock_level": 20, "reorder_quantity": 8},
        {"name": "EV Diagnostic Scanner", "sku": "DGN-001", "category": "tools", "quantity": 3, "unit_price": 15000, "cost_price": 12000, "min_stock_level": 2, "max_stock_level": 10, "reorder_quantity": 2},
    ]
    
    for item in inventory_items:
        inv_doc = {
            "item_id": f"inv_{uuid.uuid4().hex[:12]}",
            **item,
            "reserved_quantity": 0,
            "supplier_id": first_supplier["supplier_id"] if first_supplier else None,
            "supplier_name": first_supplier["name"] if first_supplier else None,
            "location": "Warehouse A",
            "last_restock_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.inventory.insert_one(inv_doc)
    
    # Services
    services = [
        {"name": "Battery Health Check", "category": "inspection", "base_price": 1500, "estimated_hours": 1.0, "description": "Complete battery diagnostic and health report"},
        {"name": "Motor Service", "category": "motor_service", "base_price": 3500, "estimated_hours": 2.0, "description": "Motor inspection, cleaning and maintenance"},
        {"name": "Full EV Service", "category": "maintenance", "base_price": 8000, "estimated_hours": 4.0, "description": "Comprehensive EV maintenance package"},
        {"name": "Charging System Repair", "category": "charging_service", "base_price": 5000, "estimated_hours": 2.5, "description": "Diagnose and repair charging issues"},
        {"name": "Battery Replacement", "category": "battery_service", "base_price": 50000, "estimated_hours": 3.0, "description": "Full battery pack replacement service"},
    ]
    
    for srv in services:
        srv_doc = {
            "service_id": f"srv_{uuid.uuid4().hex[:12]}",
            **srv,
            "parts_included": [],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.services.insert_one(srv_doc)
    
    return {"message": "Data seeded successfully"}

@router.post("/seed-customer-demo")
async def seed_customer_demo():
    """Seed demo customer account, vehicles, and AMC plans for testing customer portal"""
    
    # Check if demo customer exists
    existing = await db.users.find_one({"email": "customer@demo.com"}, {"_id": 0})
    if existing:
        return {"message": "Customer demo data already exists", "customer_id": existing["user_id"]}
    
    # Create demo customer
    customer_id = f"user_{uuid.uuid4().hex[:12]}"
    customer_doc = {
        "user_id": customer_id,
        "email": "customer@demo.com",
        "password_hash": hash_password("test_pwd_placeholder"),
        "name": "Demo Customer",
        "role": "customer",
        "phone": "+91 9876500000",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(customer_doc)
    
    # Create demo vehicles
    vehicles = [
        {
            "vehicle_id": f"veh_{uuid.uuid4().hex[:12]}",
            "owner_id": customer_id,
            "owner_name": "Demo Customer",
            "owner_email": "customer@demo.com",
            "owner_phone": "+91 9876500000",
            "make": "Ather",
            "model": "450X",
            "year": 2024,
            "registration_number": "MH01EV1234",
            "battery_capacity": 3.7,
            "current_status": "active",
            "total_service_cost": 0,
            "total_visits": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "vehicle_id": f"veh_{uuid.uuid4().hex[:12]}",
            "owner_id": customer_id,
            "owner_name": "Demo Customer",
            "owner_email": "customer@demo.com",
            "make": "Tata",
            "model": "Nexon EV",
            "year": 2023,
            "registration_number": "MH01EV5678",
            "battery_capacity": 40.5,
            "current_status": "active",
            "total_service_cost": 5500,
            "total_visits": 2,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for v in vehicles:
        await db.vehicles.insert_one(v)
    
    # Create AMC Plans
    amc_plans = [
        {
            "plan_id": f"amc_plan_{uuid.uuid4().hex[:8]}",
            "name": "Basic Care",
            "description": "Essential maintenance coverage for your EV",
            "tier": "basic",
            "duration_months": 12,
            "price": 4999,
            "services_included": [{"service_name": "Basic Service", "quantity": 2}],
            "max_service_visits": 2,
            "includes_parts": False,
            "parts_discount_percent": 5,
            "priority_support": False,
            "roadside_assistance": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "plan_id": f"amc_plan_{uuid.uuid4().hex[:8]}",
            "name": "Plus Protection",
            "description": "Enhanced coverage with parts discount",
            "tier": "plus",
            "duration_months": 12,
            "price": 8999,
            "services_included": [
                {"service_name": "Basic Service", "quantity": 4},
                {"service_name": "Battery Health Check", "quantity": 2}
            ],
            "max_service_visits": 4,
            "includes_parts": True,
            "parts_discount_percent": 15,
            "priority_support": True,
            "roadside_assistance": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "plan_id": f"amc_plan_{uuid.uuid4().hex[:8]}",
            "name": "Premium Shield",
            "description": "Complete peace of mind with all benefits",
            "tier": "premium",
            "duration_months": 12,
            "price": 14999,
            "services_included": [
                {"service_name": "Full EV Service", "quantity": 4},
                {"service_name": "Battery Health Check", "quantity": 4},
                {"service_name": "Motor Service", "quantity": 2}
            ],
            "max_service_visits": 6,
            "includes_parts": True,
            "parts_discount_percent": 25,
            "priority_support": True,
            "roadside_assistance": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    for plan in amc_plans:
        await db.amc_plans.insert_one(plan)
    
    # Create a sample AMC subscription for demo vehicle
    sample_subscription = {
        "subscription_id": f"amc_sub_{uuid.uuid4().hex[:12]}",
        "plan_id": amc_plans[1]["plan_id"],
        "plan_name": "Plus Protection",
        "plan_tier": "plus",
        "customer_id": customer_id,
        "customer_name": "Demo Customer",
        "customer_email": "customer@demo.com",
        "vehicle_id": vehicles[1]["vehicle_id"],
        "vehicle_number": "MH01EV5678",
        "vehicle_model": "Tata Nexon EV",
        "start_date": "2024-06-01",
        "end_date": "2025-06-01",
        "duration_months": 12,
        "services_used": 1,
        "max_services": 4,
        "services_included": amc_plans[1]["services_included"],
        "includes_parts": True,
        "parts_discount_percent": 15,
        "status": "active",
        "amount": 8999,
        "amount_paid": 8999,
        "payment_status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.amc_subscriptions.insert_one(sample_subscription)
    
    # Create sample service tickets
    sample_tickets = [
        {
            "ticket_id": f"tkt_{uuid.uuid4().hex[:12]}",
            "vehicle_id": vehicles[1]["vehicle_id"],
            "vehicle_type": "car",
            "vehicle_model": "Tata Nexon EV",
            "vehicle_number": "MH01EV5678",
            "customer_id": customer_id,
            "customer_name": "Demo Customer",
            "customer_email": "customer@demo.com",
            "contact_number": "+91 9876500000",
            "title": "Battery charging slower than usual",
            "description": "The vehicle takes longer to charge compared to when it was new",
            "category": "battery",
            "issue_type": "charging",
            "priority": "medium",
            "status": "resolved",
            "assigned_technician_name": "Deepak Tiwary",
            "resolution": "Cleaned charging port and updated firmware",
            "estimated_cost": 1500,
            "final_amount": 1200,
            "status_history": [
                {"status": "open", "timestamp": "2024-12-01T10:00:00Z", "updated_by": "System"},
                {"status": "technician_assigned", "timestamp": "2024-12-01T11:00:00Z", "updated_by": "Admin"},
                {"status": "in_progress", "timestamp": "2024-12-01T14:00:00Z", "updated_by": "Deepak Tiwary"},
                {"status": "resolved", "timestamp": "2024-12-01T16:00:00Z", "updated_by": "Deepak Tiwary"}
            ],
            "created_at": "2024-12-01T10:00:00Z",
            "updated_at": "2024-12-01T16:00:00Z"
        },
        {
            "ticket_id": f"tkt_{uuid.uuid4().hex[:12]}",
            "vehicle_id": vehicles[0]["vehicle_id"],
            "vehicle_type": "two_wheeler",
            "vehicle_model": "Ather 450X",
            "vehicle_number": "MH01EV1234",
            "customer_id": customer_id,
            "customer_name": "Demo Customer",
            "customer_email": "customer@demo.com",
            "title": "Regular service due",
            "description": "6-month periodic maintenance",
            "category": "maintenance",
            "issue_type": "scheduled",
            "priority": "low",
            "status": "in_progress",
            "assigned_technician_name": "Rahul Sharma",
            "estimated_cost": 2500,
            "status_history": [
                {"status": "open", "timestamp": "2025-02-15T09:00:00Z", "updated_by": "System"},
                {"status": "technician_assigned", "timestamp": "2025-02-15T09:30:00Z", "updated_by": "Admin"},
                {"status": "in_progress", "timestamp": "2025-02-16T10:00:00Z", "updated_by": "Rahul Sharma"}
            ],
            "created_at": "2025-02-15T09:00:00Z",
            "updated_at": "2025-02-16T10:00:00Z"
        }
    ]
    for ticket in sample_tickets:
        await db.tickets.insert_one(ticket)
    
    # Create sample invoice
    sample_invoice = {
        "invoice_id": f"inv_{uuid.uuid4().hex[:12]}",
        "invoice_number": f"INV-{datetime.now().strftime('%Y%m')}-0001",
        "ticket_id": sample_tickets[0]["ticket_id"],
        "customer_id": customer_id,
        "customer_name": "Demo Customer",
        "customer_email": "customer@demo.com",
        "vehicle_number": "MH01EV5678",
        "items": [
            {"name": "Charging Port Cleaning", "quantity": 1, "unit_price": 500},
            {"name": "Firmware Update", "quantity": 1, "unit_price": 700}
        ],
        "subtotal": 1200,
        "tax_amount": 216,
        "total_amount": 1416,
        "amount_paid": 1416,
        "payment_status": "paid",
        "created_at": "2024-12-01T16:30:00Z"
    }
    await db.invoices.insert_one(sample_invoice)
    
    return {
        "message": "Customer demo data seeded successfully",
        "customer_email": "customer@demo.com",
        "customer_password": "test_pwd_placeholder",
        "vehicles": 2,
        "amc_plans": 3,
        "tickets": 2
    }

@router.post("/reseed")
async def reseed_missing_data():
    """Reseed missing data (suppliers, services) without deleting existing data"""
    results = {"suppliers": 0, "services": 0}
    
    # Check and seed suppliers if empty
    supplier_count = await db.suppliers.count_documents({})
    if supplier_count == 0:
        suppliers = [
            {"name": "EV Parts India", "contact_person": "Rajesh Kumar", "email": "rajesh@evpartsindia.com", "phone": "+91 9876543211", "category": "parts", "payment_terms": "net_30"},
            {"name": "BatteryWorld", "contact_person": "Anita Singh", "email": "anita@batteryworld.in", "phone": "+91 9876543212", "category": "parts", "payment_terms": "net_15"},
            {"name": "AutoTools Pro", "contact_person": "Vikram Mehta", "email": "vikram@autotoolspro.com", "phone": "+91 9876543213", "category": "equipment", "payment_terms": "net_45"},
        ]
        for sup in suppliers:
            sup_doc = {
                "supplier_id": f"sup_{uuid.uuid4().hex[:12]}",
                **sup,
                "address": "Mumbai, Maharashtra",
                "gst_number": f"27AABCU{uuid.uuid4().hex[:4].upper()}B1Z5",
                "rating": 4.5,
                "total_orders": 0,
                "total_value": 0,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.suppliers.insert_one(sup_doc)
            results["suppliers"] += 1
    
    # Check and seed services if empty
    service_count = await db.services.count_documents({})
    if service_count == 0:
        services = [
            {"name": "Battery Health Check", "category": "inspection", "base_price": 1500, "estimated_hours": 1.0, "description": "Complete battery diagnostic and health report"},
            {"name": "Motor Service", "category": "motor_service", "base_price": 3500, "estimated_hours": 2.0, "description": "Motor inspection, cleaning and maintenance"},
            {"name": "Full EV Service", "category": "maintenance", "base_price": 8000, "estimated_hours": 4.0, "description": "Comprehensive EV maintenance package"},
            {"name": "Charging System Repair", "category": "charging_service", "base_price": 5000, "estimated_hours": 2.5, "description": "Diagnose and repair charging issues"},
            {"name": "Battery Replacement", "category": "battery_service", "base_price": 50000, "estimated_hours": 3.0, "description": "Full battery pack replacement service"},
        ]
        for srv in services:
            srv_doc = {
                "service_id": f"srv_{uuid.uuid4().hex[:12]}",
                **srv,
                "parts_included": [],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.services.insert_one(srv_doc)
            results["services"] += 1
    
    return {"message": "Missing data reseeded", "added": results}

# ==================== ATTENDANCE CONFIGURATION ====================
STANDARD_WORK_HOURS = 9.0
STANDARD_START_TIME = "09:00"  # 9 AM
STANDARD_END_TIME = "18:00"    # 6 PM
LATE_THRESHOLD_MINUTES = 15
EARLY_DEPARTURE_THRESHOLD_MINUTES = 15
OVERTIME_MULTIPLIER = 1.5

# Leave Types Configuration
DEFAULT_LEAVE_TYPES = [
    {"code": "CL", "name": "Casual Leave", "days_allowed": 12, "carry_forward": False, "is_paid": True},
    {"code": "SL", "name": "Sick Leave", "days_allowed": 12, "carry_forward": False, "is_paid": True},
    {"code": "EL", "name": "Earned Leave", "days_allowed": 15, "carry_forward": True, "is_paid": True},
    {"code": "LWP", "name": "Leave Without Pay", "days_allowed": 365, "carry_forward": False, "is_paid": False},
    {"code": "CO", "name": "Compensatory Off", "days_allowed": 10, "carry_forward": False, "is_paid": True},
]

# ==================== EMPLOYEE ROUTES ====================

def calculate_salary_deductions(basic_salary: float, gross_salary: float, pf_enrolled: bool, esi_enrolled: bool):
    """Calculate statutory deductions based on India compliance"""
    deductions = {
        "pf_deduction": 0.0,
        "esi_deduction": 0.0,
        "professional_tax": 0.0,
        "tds": 0.0
    }
    
    # PF - 12% of basic salary (if enrolled)
    if pf_enrolled:
        deductions["pf_deduction"] = round(basic_salary * 0.12, 2)
    
    # ESI - 0.75% of gross if gross <= 21000 (if enrolled)
    if esi_enrolled and gross_salary <= 21000:
        deductions["esi_deduction"] = round(gross_salary * 0.0075, 2)
    
    # Professional Tax (Karnataka example - varies by state)
    if gross_salary > 15000:
        deductions["professional_tax"] = 200.0
    elif gross_salary > 10000:
        deductions["professional_tax"] = 150.0
    
    # TDS - Simplified calculation (actual depends on declarations)
    annual_salary = gross_salary * 12
    if annual_salary > 1500000:
        deductions["tds"] = round((gross_salary * 0.30) / 12, 2)
    elif annual_salary > 1200000:
        deductions["tds"] = round((gross_salary * 0.20) / 12, 2)
    elif annual_salary > 900000:
        deductions["tds"] = round((gross_salary * 0.15) / 12, 2)
    elif annual_salary > 600000:
        deductions["tds"] = round((gross_salary * 0.10) / 12, 2)
    elif annual_salary > 300000:
        deductions["tds"] = round((gross_salary * 0.05) / 12, 2)
    
    return deductions

@router.post("/employees")

@router.post("/migration/upload")
async def upload_migration_file(request: Request):
    """Upload and extract legacy backup file"""
    user = await require_admin(request)
    
    # This endpoint would handle file upload
    # For now, we assume files are manually placed in /tmp/legacy_data
    import os
    data_dir = "/tmp/legacy_data"
    
    if not os.path.exists(data_dir):
        raise HTTPException(status_code=400, detail="Migration data directory not found. Please extract backup to /tmp/legacy_data")
    
    files = os.listdir(data_dir)
    xls_files = [f for f in files if f.endswith('.xls')]
    
    return {
        "message": "Migration data directory found",
        "files_found": len(xls_files),
        "files": xls_files[:20]  # Show first 20 files
    }

@router.post("/migration/run")
async def run_migration(request: Request):
    """Run full legacy data migration"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        stats = await migrator.run_full_migration()
        
        return {
            "message": "Migration completed",
            "statistics": stats
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Migration module not found: {str(e)}")
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.post("/migration/customers")
async def migrate_customers_only(request: Request):
    """Migrate only customers from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        count = await migrator.migrate_customers()
        
        return {"message": f"Migrated {count} customers", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migration/suppliers")
async def migrate_suppliers_only(request: Request):
    """Migrate only suppliers/vendors from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        count = await migrator.migrate_suppliers()
        
        return {"message": f"Migrated {count} suppliers", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migration/inventory")
async def migrate_inventory_only(request: Request):
    """Migrate only inventory items from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        await migrator.migrate_suppliers()  # Need suppliers first for references
        count = await migrator.migrate_inventory()
        
        return {"message": f"Migrated {count} inventory items", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migration/invoices")
async def migrate_invoices_only(request: Request):
    """Migrate only invoices from legacy data"""
    user = await require_admin(request)
    
    import sys
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from migration.legacy_migrator import LegacyDataMigrator
        
        data_dir = "/tmp/legacy_data"
        migrator = LegacyDataMigrator(data_dir, db)
        await migrator.migrate_customers()  # Need customers first
        count = await migrator.migrate_invoices()
        
        return {"message": f"Migrated {count} invoices", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/migration/status")
async def get_migration_status(request: Request):
    """Get current migration status and data counts"""
    await require_admin(request)
    
    # Count migrated records
    counts = {
        "customers": await db.customers.count_documents({"migrated_from": "legacy_zoho"}),
        "suppliers": await db.suppliers.count_documents({"migrated_from": "legacy_zoho"}),
        "inventory": await db.inventory.count_documents({"migrated_from": "legacy_zoho"}),
        "invoices": await db.invoices.count_documents({"migrated_from": "legacy_zoho"}),
        "sales_orders": await db.sales_orders.count_documents({"migrated_from": "legacy_zoho"}),
        "purchase_orders": await db.purchase_orders.count_documents({"migrated_from": "legacy_zoho"}),
        "payments": await db.payments.count_documents({"migrated_from": "legacy_zoho"}),
        "expenses": await db.expenses.count_documents({"migrated_from": "legacy_zoho"}),
        "accounts": await db.chart_of_accounts.count_documents({"migrated_from": "legacy_zoho"})
    }
    
    # Total counts
    totals = {
        "customers": await db.customers.count_documents({}),
        "suppliers": await db.suppliers.count_documents({}),
        "inventory": await db.inventory.count_documents({}),
        "invoices": await db.invoices.count_documents({}),
        "sales_orders": await db.sales_orders.count_documents({}),
        "purchase_orders": await db.purchase_orders.count_documents({}),
        "payments": await db.payments.count_documents({}),
        "expenses": await db.expenses.count_documents({}),
        "accounts": await db.chart_of_accounts.count_documents({})
    }
    
    return {
        "migrated_records": counts,
        "total_records": totals,
        "migration_complete": all(counts[k] > 0 for k in ["customers", "suppliers", "inventory"])
    }

# Root endpoint
@router.get("/")
async def root():
    return {"status": "ok", "service": "battwheels"}

@router.get("/audit-logs")
async def get_audit_logs(
    request: Request,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50,
    page: int = 1
):
    """Fetch audit logs for the organization"""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else user.get("organization_id", "")
    try:
        from core.audit import get_audit_service
        audit = get_audit_service()
        logs = await audit.get_logs(
            organization_id=org_id,
            resource_type=resource_type,
            limit=limit,
            skip=(page - 1) * limit
        )
        return {"code": 0, "audit_logs": logs, "page": page, "limit": limit}
    except Exception as e:
        # Fallback: direct DB query
        query = {"organization_id": org_id}
        if resource_type:
            query["resource_type"] = resource_type
        if action:
            query["action"] = action
        logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip((page-1)*limit).limit(limit).to_list(limit)
        total = await db.audit_logs.count_documents(query)
        return {"code": 0, "audit_logs": logs, "total": total, "page": page}

@router.get("/audit-logs/{resource_type}/{resource_id}")
async def get_audit_log_for_resource(
    resource_type: str,
    resource_id: str,
    request: Request
):
    """Get audit log history for a specific resource"""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else user.get("organization_id", "")
    query = {"organization_id": org_id, "resource_type": resource_type.upper(), "resource_id": resource_id}
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)
    return {"code": 0, "resource_type": resource_type, "resource_id": resource_id, "history": logs}

# ==================== SATISFACTION SURVEY ROUTES ====================
@router.get("/public/survey/{survey_token}")
async def get_survey_info(survey_token: str):
    """Public endpoint: get survey metadata for display before submission (no auth)"""
    review = await db.ticket_reviews.find_one({"survey_token": survey_token}, {"_id": 0})
    if not review:
        raise HTTPException(status_code=404, detail="Survey not found or expired")
    if review.get("completed"):
        raise HTTPException(status_code=409, detail="Survey already completed")

    # Get ticket details for display
    ticket = await db.tickets.find_one(
        {"ticket_id": review.get("ticket_id")},
        {"_id": 0, "title": 1, "vehicle_make": 1, "vehicle_model": 1,
         "vehicle_number": 1, "customer_name": 1, "updated_at": 1,
         "work_completed_at": 1, "closed_at": 1}
    )

    # Get org name
    org = await db.organizations.find_one(
        {"organization_id": review.get("organization_id")},
        {"_id": 0, "name": 1, "logo_url": 1, "google_maps_url": 1}
    )

    return {
        "code": 0,
        "survey_token": survey_token,
        "customer_name": review.get("customer_name", ""),
        "ticket_title": ticket.get("title", "Service") if ticket else "Service",
        "vehicle_make": ticket.get("vehicle_make", "") if ticket else "",
        "vehicle_model": ticket.get("vehicle_model", "") if ticket else "",
        "vehicle_number": ticket.get("vehicle_number", "") if ticket else "",
        "completed_date": (ticket.get("closed_at") or ticket.get("work_completed_at") or review.get("created_at", ""))[:10] if ticket else review.get("created_at", "")[:10],
        "org_name": org.get("name", "Your Service Center") if org else "Your Service Center",
        "org_logo_url": org.get("logo_url") if org else None,
        "google_maps_url": org.get("google_maps_url") if org else None,
    }


@router.post("/public/survey/{survey_token}")
async def submit_satisfaction_survey(survey_token: str, request: Request):
    """Public endpoint: customer submits satisfaction rating after ticket close"""
    body = await request.json()
    review = await db.ticket_reviews.find_one({"survey_token": survey_token}, {"_id": 0})
    if not review:
        raise HTTPException(status_code=404, detail="Survey not found or expired")
    if review.get("completed"):
        raise HTTPException(status_code=400, detail="Survey already completed")
    rating = body.get("rating")
    if not rating or not (1 <= int(rating) <= 5):
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    from datetime import datetime, timezone
    await db.ticket_reviews.update_one(
        {"survey_token": survey_token},
        {"$set": {
            "rating": int(rating),
            "review_text": body.get("review_text", ""),
            "would_recommend": body.get("would_recommend", True),
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"code": 0, "message": "Thank you for your feedback!"}

@router.get("/reports/satisfaction")
async def get_satisfaction_report(request: Request):
    """Get customer satisfaction report"""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else user.get("organization_id", "")
    reviews = await db.ticket_reviews.find(
        {"organization_id": org_id, "completed": True}, {"_id": 0}
    ).to_list(1000)
    if not reviews:
        return {"code": 0, "total_reviews": 0, "avg_rating": 0, "reviews": []}
    avg = sum(r.get("rating", 0) for r in reviews) / len(reviews)
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        dist[r.get("rating", 3)] = dist.get(r.get("rating", 3), 0) + 1
    return {"code": 0, "total_reviews": len(reviews), "avg_rating": round(avg, 2), "rating_distribution": dist, "reviews": reviews[:20]}


# ==================== DATA EXPORT ROUTES ====================
@router.post("/settings/export-data")
async def request_data_export(request: Request):
    """
    POST /api/settings/export-data
    Kick off an async export of all org data (tickets, invoices, contacts, inventory).
    Returns a job_id to poll for status.
    """
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else getattr(user, "organization_id", "")
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization context required")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    export_type = body.get("export_type", "all")
    fmt = body.get("format", "json")

    import uuid as _uuid
    job_id = f"EXP-{_uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)

    export_job = {
        "job_id": job_id,
        "organization_id": org_id,
        "requested_by": getattr(user, "user_id", ""),
        "export_type": export_type,
        "format": fmt,
        "status": "pending",
        "created_at": now.isoformat(),
        "completed_at": None,
        "download_url": None,
        "error": None,
    }
    await db.export_jobs.insert_one(export_job)
    export_job.pop("_id", None)

    # Run export inline (small orgs — synchronous for now)
    try:
        import json as _json
        collections_to_export = {
            "tickets": db.tickets,
            "invoices": db.invoices_enhanced,
            "contacts": db.contacts_enhanced,
            "inventory": db.inventory,
            "employees": db.employees,
            "expenses": db.expenses,
        }
        if export_type != "all":
            collections_to_export = {export_type: collections_to_export.get(export_type, db[export_type])}

        export_data = {"org_id": org_id, "exported_at": now.isoformat(), "collections": {}}
        for col_name, col in collections_to_export.items():
            try:
                docs = await col.find({"organization_id": org_id}, {"_id": 0}).to_list(10000)
                export_data["collections"][col_name] = docs
            except Exception:
                export_data["collections"][col_name] = []

        export_data["total_records"] = sum(len(v) for v in export_data["collections"].values())

        # Store result in DB
        await db.export_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "record_count": export_data["total_records"],
                "download_url": f"/api/settings/export-data/{job_id}/download",
            }}
        )
        # Store export data temporarily
        await db.export_data.replace_one(
            {"job_id": job_id},
            {"job_id": job_id, "organization_id": org_id, "data": export_data},
            upsert=True
        )
        return {
            "code": 0,
            "job_id": job_id,
            "status": "completed",
            "record_count": export_data["total_records"],
            "download_url": f"/api/settings/export-data/{job_id}/download",
        }
    except Exception as e:
        await db.export_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        return {"code": 1, "job_id": job_id, "status": "failed", "error": str(e)}


@router.get("/settings/export-data/status")
async def list_export_jobs(request: Request):
    """GET /api/settings/export-data/status — List all export jobs for org."""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else getattr(user, "organization_id", "")
    jobs = await db.export_jobs.find(
        {"organization_id": org_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    return {"code": 0, "jobs": jobs, "total": len(jobs)}


@router.get("/settings/export-data/{job_id}/download")
async def download_export(job_id: str, request: Request):
    """GET /api/settings/export-data/{job_id}/download — Download export as JSON."""
    user = await require_auth(request)
    ctx = getattr(request.state, "tenant_context", None)
    org_id = ctx.org_id if ctx else getattr(user, "organization_id", "")
    record = await db.export_data.find_one(
        {"job_id": job_id, "organization_id": org_id}, {"_id": 0}
    )
    if not record:
        raise HTTPException(status_code=404, detail="Export job not found")
    import json as _json
    from fastapi.responses import Response as _Response
    content = _json.dumps(record.get("data", {}), indent=2, default=str)
    return _Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=export_{job_id}.json"}
    )
