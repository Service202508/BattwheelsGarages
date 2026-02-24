"""
Battwheels OS - Master Data Routes
Unified Vehicle Categories, Models (OEMs), and Issue Suggestions
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from fastapi import Request
from utils.database import extract_org_id, org_query


def get_db():
    from server import db
    return db

router = APIRouter(prefix="/master-data", tags=["Master Data"])


# ==================== MODELS ====================

class VehicleCategoryCreate(BaseModel):
    name: str
    code: str  # e.g., "2W_EV", "3W_EV", "4W_EV"
    description: Optional[str] = None
    icon: Optional[str] = None  # lucide icon name
    is_ev: bool = True
    is_active: bool = True

class VehicleModelCreate(BaseModel):
    name: str  # e.g., "Ola S1 Pro", "Ather 450X"
    oem: str  # e.g., "Ola Electric", "Ather Energy"
    category_code: str  # e.g., "2W_EV"
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    battery_type: Optional[str] = None  # e.g., "Li-ion 3.97 kWh"
    motor_type: Optional[str] = None
    range_km: Optional[int] = None
    is_active: bool = True

class EVIssueSuggestionCreate(BaseModel):
    title: str
    category_codes: List[str]  # applicable vehicle categories
    model_ids: List[str] = []  # specific models (empty = all in category)
    issue_type: str  # battery, motor, charging, controller, etc.
    common_symptoms: List[str] = []
    severity: str = "medium"  # low, medium, high, critical
    is_active: bool = True


# ==================== VEHICLE CATEGORIES ====================

@router.get("/vehicle-categories")
async def list_vehicle_categories(
    active_only: bool = True,
    ev_only: bool = False, request: Request):
    org_id = extract_org_id(request)
    """List all vehicle categories"""
    db = get_db()
    query = {}
    if active_only:
        query["is_active"] = True
    if ev_only:
        query["is_ev"] = True
    
    categories = await db.vehicle_categories.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return {"categories": categories, "total": len(categories)}

@router.post("/vehicle-categories")
async def create_vehicle_category(data: VehicleCategoryCreate, request: Request):
    org_id = extract_org_id(request)
    """Create a new vehicle category (admin only)"""
    db = get_db()
    
    # Check if code already exists
    existing = await db.vehicle_categories.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail=f"Category code '{data.code}' already exists")
    
    category_id = f"vcat_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    
    category = {
        "category_id": category_id,
        **data.model_dump(),
        "sort_order": 0,
        "created_at": now,
        "updated_at": now
    }
    
    await db.vehicle_categories.insert_one(category)
    del category["_id"]
    return category

@router.put("/vehicle-categories/{category_id}")
async def update_vehicle_category(category_id: str, data: VehicleCategoryCreate, request: Request):
    org_id = extract_org_id(request)
    """Update a vehicle category"""
    db = get_db()
    
    result = await db.vehicle_categories.update_one(
        {"category_id": category_id},
        {"$set": {**data.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return await db.vehicle_categories.find_one({"category_id": category_id}, {"_id": 0})

@router.delete("/vehicle-categories/{category_id}")
async def delete_vehicle_category(category_id: str, request: Request):
    org_id = extract_org_id(request)
    """Soft delete a vehicle category"""
    db = get_db()
    result = await db.vehicle_categories.update_one(
        {"category_id": category_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deactivated"}


# ==================== VEHICLE MODELS (OEMs) ====================

@router.get("/vehicle-models")
async def list_vehicle_models(
    category_code: Optional[str] = None,
    oem: Optional[str] = None,
    active_only: bool = True,
    search: Optional[str] = None, request: Request):
    org_id = extract_org_id(request)
    """List vehicle models with optional filtering"""
    db = get_db()
    query = {}
    
    if active_only:
        query["is_active"] = True
    if category_code:
        query["category_code"] = category_code
    if oem:
        query["oem"] = {"$regex": oem, "$options": "i"}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"oem": {"$regex": search, "$options": "i"}}
        ]
    
    models = await db.vehicle_models.find(query, {"_id": 0}).sort([("oem", 1), ("name", 1)]).to_list(500)
    
    # Group by OEM for frontend convenience
    oems_map = {}
    for model in models:
        oem_name = model.get("oem", "Unknown")
        if oem_name not in oems_map:
            oems_map[oem_name] = []
        oems_map[oem_name].append(model)
    
    return {
        "models": models,
        "by_oem": oems_map,
        "total": len(models)
    }

@router.get("/vehicle-models/oems")
async def list_oems(category_code: Optional[str] = None, request: Request):
    org_id = extract_org_id(request)
    """List distinct OEMs"""
    db = get_db()
    query = {"is_active": True}
    if category_code:
        query["category_code"] = category_code
    
    oems = await db.vehicle_models.distinct("oem", query)
    return {"oems": sorted(oems)}

@router.post("/vehicle-models")
async def create_vehicle_model(data: VehicleModelCreate, request: Request):
    org_id = extract_org_id(request)
    """Create a new vehicle model"""
    db = get_db()
    
    # Verify category exists
    category = await db.vehicle_categories.find_one({"code": data.category_code})
    if not category:
        raise HTTPException(status_code=400, detail=f"Category '{data.category_code}' not found")
    
    model_id = f"vmod_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    
    model = {
        "model_id": model_id,
        **data.model_dump(),
        "category_name": category.get("name"),
        "created_at": now,
        "updated_at": now
    }
    
    await db.vehicle_models.insert_one(model)
    del model["_id"]
    return model

@router.put("/vehicle-models/{model_id}")
async def update_vehicle_model(model_id: str, data: VehicleModelCreate, request: Request):
    org_id = extract_org_id(request)
    """Update a vehicle model"""
    db = get_db()
    
    result = await db.vehicle_models.update_one(
        {"model_id": model_id},
        {"$set": {**data.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return await db.vehicle_models.find_one({"model_id": model_id}, {"_id": 0})

@router.delete("/vehicle-models/{model_id}")
async def delete_vehicle_model(model_id: str, request: Request):
    org_id = extract_org_id(request)
    """Soft delete a vehicle model"""
    db = get_db()
    result = await db.vehicle_models.update_one(
        {"model_id": model_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deactivated"}


# ==================== EV ISSUE SUGGESTIONS ====================

@router.get("/issue-suggestions")
async def get_issue_suggestions(
    category_code: Optional[str] = None,
    model_id: Optional[str] = None,
    issue_type: Optional[str] = None,
    search: Optional[str] = None, request: Request):
    org_id = extract_org_id(request)
    """Get EV issue suggestions based on vehicle category/model"""
    db = get_db()
    query = {"is_active": True}
    
    if category_code:
        query["category_codes"] = category_code
    
    if model_id:
        query["$or"] = [
            {"model_ids": model_id},
            {"model_ids": {"$size": 0}}  # Suggestions for all models in category
        ]
    
    if issue_type:
        query["issue_type"] = issue_type
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"common_symptoms": {"$elemMatch": {"$regex": search, "$options": "i"}}}
        ]
    
    suggestions = await db.ev_issue_suggestions.find(query, {"_id": 0}).sort("usage_count", -1).to_list(50)
    
    # Also get suggestions from historical ticket data (EFI)
    if category_code or model_id:
        efi_query = {"is_active": True}
        if category_code:
            efi_query["$or"] = [
                {"vehicle_category": category_code},
                {"applicable_vehicles": {"$regex": category_code, "$options": "i"}}
            ]
        
        efi_cards = await db.failure_cards.find(
            efi_query,
            {"_id": 0, "failure_id": 1, "title": 1, "subsystem_category": 1, "symptoms": 1, "confidence_score": 1}
        ).sort("confidence_score", -1).limit(10).to_list(10)
        
        # Convert EFI cards to suggestion format
        for card in efi_cards:
            suggestions.append({
                "suggestion_id": card.get("failure_id"),
                "title": card.get("title"),
                "issue_type": card.get("subsystem_category", "general"),
                "common_symptoms": card.get("symptoms", [])[:3],
                "source": "efi",
                "confidence": card.get("confidence_score", 0)
            })
    
    return {"suggestions": suggestions, "total": len(suggestions)}

@router.post("/issue-suggestions")
async def create_issue_suggestion(data: EVIssueSuggestionCreate, request: Request):
    org_id = extract_org_id(request)
    """Create a new EV issue suggestion"""
    db = get_db()
    
    suggestion_id = f"evis_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    
    suggestion = {
        "suggestion_id": suggestion_id,
        **data.model_dump(),
        "usage_count": 0,
        "source": "manual",
        "created_at": now,
        "updated_at": now
    }
    
    await db.ev_issue_suggestions.insert_one(suggestion)
    del suggestion["_id"]
    return suggestion

@router.post("/issue-suggestions/{suggestion_id}/increment-usage")
async def increment_suggestion_usage(suggestion_id: str, request: Request):
    org_id = extract_org_id(request)
    """Increment usage count when a suggestion is selected"""
    db = get_db()
    await db.ev_issue_suggestions.update_one(
        {"suggestion_id": suggestion_id},
        {"$inc": {"usage_count": 1}}
    )
    return {"message": "Usage count updated"}


# ==================== SEED DATA ====================

@router.post("/seed")
async def seed_master_data(request: Request):
    org_id = extract_org_id(request)
    """Seed initial master data for vehicle categories, models, and issue suggestions"""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if already seeded
    existing_categories = await db.vehicle_categories.count_documents(org_query(org_id))
    if existing_categories > 0:
        return {"message": "Master data already exists", "categories": existing_categories}
    
    # Vehicle Categories
    categories = [
        {
            "category_id": "vcat_2w_ev",
            "code": "2W_EV",
            "name": "Two Wheeler EV (Scooter/Bike)",
            "description": "Electric scooters and motorcycles",
            "icon": "bike",
            "is_ev": True,
            "is_active": True,
            "sort_order": 1,
            "created_at": now,
            "updated_at": now
        },
        {
            "category_id": "vcat_3w_ev",
            "code": "3W_EV",
            "name": "Three Wheeler EV (Auto)",
            "description": "Electric auto-rickshaws and cargo vehicles",
            "icon": "truck",
            "is_ev": True,
            "is_active": True,
            "sort_order": 2,
            "created_at": now,
            "updated_at": now
        },
        {
            "category_id": "vcat_4w_ev",
            "code": "4W_EV",
            "name": "Four Wheeler EV (Car/SUV)",
            "description": "Electric cars and SUVs",
            "icon": "car",
            "is_ev": True,
            "is_active": True,
            "sort_order": 3,
            "created_at": now,
            "updated_at": now
        },
        {
            "category_id": "vcat_comm_ev",
            "code": "COMM_EV",
            "name": "Commercial EV (Bus/Truck)",
            "description": "Electric buses, trucks, and commercial vehicles",
            "icon": "bus",
            "is_ev": True,
            "is_active": True,
            "sort_order": 4,
            "created_at": now,
            "updated_at": now
        },
        {
            "category_id": "vcat_lev",
            "code": "LEV",
            "name": "Light Electric Vehicle",
            "description": "E-cycles, e-rickshaws, golf carts",
            "icon": "bicycle",
            "is_ev": True,
            "is_active": True,
            "sort_order": 5,
            "created_at": now,
            "updated_at": now
        }
    ]
    
    await db.vehicle_categories.insert_many(categories)
    
    # Vehicle Models (Popular EVs in India)
    models = [
        # Two Wheelers
        {"model_id": "vmod_ola_s1_pro", "name": "S1 Pro", "oem": "Ola Electric", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 3.97 kWh", "range_km": 181, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_ola_s1_air", "name": "S1 Air", "oem": "Ola Electric", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 2.5 kWh", "range_km": 101, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_ather_450x", "name": "450X", "oem": "Ather Energy", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 3.7 kWh", "range_km": 150, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_ather_450s", "name": "450S", "oem": "Ather Energy", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 2.9 kWh", "range_km": 115, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_tvs_iqube", "name": "iQube", "oem": "TVS Motor", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 4.56 kWh", "range_km": 145, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_bajaj_chetak", "name": "Chetak", "oem": "Bajaj Auto", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 3.0 kWh", "range_km": 127, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_hero_vida_v1", "name": "Vida V1", "oem": "Hero MotoCorp", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 3.94 kWh", "range_km": 165, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_simple_one", "name": "Simple One", "oem": "Simple Energy", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 4.8 kWh", "range_km": 212, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_revolt_rv400", "name": "RV400", "oem": "Revolt Motors", "category_code": "2W_EV", "category_name": "Two Wheeler EV (Scooter/Bike)", "battery_type": "Li-ion 3.24 kWh", "range_km": 150, "is_active": True, "created_at": now, "updated_at": now},
        
        # Three Wheelers
        {"model_id": "vmod_mahindra_treo", "name": "Treo", "oem": "Mahindra Electric", "category_code": "3W_EV", "category_name": "Three Wheeler EV (Auto)", "battery_type": "Li-ion 7.37 kWh", "range_km": 130, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_piaggio_ape_e_xtra", "name": "Ape E-Xtra", "oem": "Piaggio", "category_code": "3W_EV", "category_name": "Three Wheeler EV (Auto)", "battery_type": "Li-ion 8.0 kWh", "range_km": 95, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_euler_hiload", "name": "HiLoad", "oem": "Euler Motors", "category_code": "3W_EV", "category_name": "Three Wheeler EV (Auto)", "battery_type": "Li-ion 12.5 kWh", "range_km": 151, "is_active": True, "created_at": now, "updated_at": now},
        
        # Four Wheelers
        {"model_id": "vmod_tata_nexon_ev", "name": "Nexon EV", "oem": "Tata Motors", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 40.5 kWh", "range_km": 465, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_tata_tiago_ev", "name": "Tiago EV", "oem": "Tata Motors", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 24 kWh", "range_km": 315, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_tata_punch_ev", "name": "Punch EV", "oem": "Tata Motors", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 35 kWh", "range_km": 421, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_mg_zs_ev", "name": "ZS EV", "oem": "MG Motor", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 50.3 kWh", "range_km": 461, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_mahindra_xuv400", "name": "XUV400", "oem": "Mahindra Electric", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 39.4 kWh", "range_km": 456, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_byd_atto3", "name": "Atto 3", "oem": "BYD", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 60.48 kWh", "range_km": 521, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_hyundai_kona", "name": "Kona Electric", "oem": "Hyundai", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 39.2 kWh", "range_km": 452, "is_active": True, "created_at": now, "updated_at": now},
        {"model_id": "vmod_kia_ev6", "name": "EV6", "oem": "Kia", "category_code": "4W_EV", "category_name": "Four Wheeler EV (Car/SUV)", "battery_type": "Li-ion 77.4 kWh", "range_km": 528, "is_active": True, "created_at": now, "updated_at": now},
        
        # Commercial
        {"model_id": "vmod_tata_ace_ev", "name": "Ace EV", "oem": "Tata Motors", "category_code": "COMM_EV", "category_name": "Commercial EV (Bus/Truck)", "battery_type": "Li-ion 21.3 kWh", "range_km": 154, "is_active": True, "created_at": now, "updated_at": now},
    ]
    
    await db.vehicle_models.insert_many(models)
    
    # EV Issue Suggestions
    issue_suggestions = [
        # Battery Issues
        {"suggestion_id": "evis_batt_01", "title": "Battery not charging / Charging stops midway", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "battery", "common_symptoms": ["Charger shows error", "Battery percentage not increasing", "Charging takes too long"], "severity": "high", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_batt_02", "title": "Battery draining faster than usual", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "battery", "common_symptoms": ["Range reduced significantly", "Battery percentage drops quickly", "Vehicle shuts down unexpectedly"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_batt_03", "title": "Battery swelling / Overheating", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "battery", "common_symptoms": ["Battery pack feels hot", "Visible swelling", "Burning smell"], "severity": "critical", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_batt_04", "title": "BMS error / Battery management fault", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "battery", "common_symptoms": ["Error code on display", "Vehicle won't start", "Warning lights on"], "severity": "high", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        
        # Motor Issues
        {"suggestion_id": "evis_motor_01", "title": "Motor making unusual noise", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "motor", "common_symptoms": ["Grinding sound", "Whining noise", "Clicking during acceleration"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_motor_02", "title": "Reduced power / Acceleration issues", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "motor", "common_symptoms": ["Vehicle feels sluggish", "Takes longer to reach top speed", "Power cuts intermittently"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_motor_03", "title": "Motor overheating", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "motor", "common_symptoms": ["Temperature warning on display", "Power limited mode activated", "Motor feels very hot"], "severity": "high", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        
        # Charging Issues
        {"suggestion_id": "evis_charge_01", "title": "Charger not connecting / Recognition issue", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "charging", "common_symptoms": ["Charger LED not turning on", "No response when plugged in", "Error on charger display"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_charge_02", "title": "Charging port damaged / Water ingress", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "charging", "common_symptoms": ["Visible damage on port", "Corrosion/rust visible", "Charger fits loosely"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_charge_03", "title": "Fast charging not working", "category_codes": ["4W_EV", "COMM_EV"], "issue_type": "charging", "common_symptoms": ["DC fast charger not recognized", "Charging at slow speed only", "Error at public charging station"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        
        # Controller/Electronics
        {"suggestion_id": "evis_ctrl_01", "title": "Display not working / Blank screen", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "controller", "common_symptoms": ["No display at all", "Flickering screen", "Partial display working"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_ctrl_02", "title": "Vehicle not starting / Electronics failure", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "controller", "common_symptoms": ["Key/button press not responding", "No lights coming on", "Error codes on startup"], "severity": "high", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_ctrl_03", "title": "App connectivity issues", "category_codes": ["2W_EV", "4W_EV"], "issue_type": "controller", "common_symptoms": ["Cannot connect to vehicle app", "GPS not tracking", "Remote features not working"], "severity": "low", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        
        # General/Other
        {"suggestion_id": "evis_gen_01", "title": "Brakes making noise", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "brakes", "common_symptoms": ["Squealing sound", "Grinding noise", "Vibration when braking"], "severity": "high", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_gen_02", "title": "Tyre / Wheel issue", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "tyre", "common_symptoms": ["Puncture", "Wheel wobble", "Uneven wear"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_gen_03", "title": "Suspension / Ride quality issue", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "suspension", "common_symptoms": ["Bumpy ride", "Noise from suspension", "Vehicle leaning"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_gen_04", "title": "Body / Exterior damage", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "body", "common_symptoms": ["Scratches", "Dents", "Broken parts"], "severity": "low", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
        {"suggestion_id": "evis_gen_05", "title": "Lights not working", "category_codes": ["2W_EV", "3W_EV", "4W_EV"], "issue_type": "electrical", "common_symptoms": ["Headlight dim/off", "Tail light not working", "Indicators malfunction"], "severity": "medium", "is_active": True, "usage_count": 0, "source": "manual", "created_at": now, "updated_at": now},
    ]
    
    await db.ev_issue_suggestions.insert_many(issue_suggestions)
    
    return {
        "message": "Master data seeded successfully",
        "categories": len(categories),
        "models": len(models),
        "issue_suggestions": len(issue_suggestions)
    }
