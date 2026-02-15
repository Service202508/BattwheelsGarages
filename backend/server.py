from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'battwheels-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

# Create the main app
app = FastAPI(title="Battwheels OS API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "customer"  # admin, technician, customer
    designation: Optional[str] = None
    phone: Optional[str] = None
    picture: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "customer"
    designation: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    created_at: datetime
    is_active: bool = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class Vehicle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    vehicle_id: str = Field(default_factory=lambda: f"veh_{uuid.uuid4().hex[:12]}")
    owner_id: str
    owner_name: str
    make: str
    model: str
    year: int
    registration_number: str
    battery_capacity: float
    current_status: str = "active"  # active, in_workshop, serviced
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VehicleCreate(BaseModel):
    owner_name: str
    make: str
    model: str
    year: int
    registration_number: str
    battery_capacity: float

class Ticket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ticket_id: str = Field(default_factory=lambda: f"tkt_{uuid.uuid4().hex[:12]}")
    vehicle_id: str
    customer_id: str
    assigned_technician_id: Optional[str] = None
    title: str
    description: str
    category: str  # battery, motor, charging, suspension, electrical, other
    priority: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, in_progress, resolved, closed
    ai_diagnosis: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class TicketCreate(BaseModel):
    vehicle_id: str
    title: str
    description: str
    category: str
    priority: str = "medium"

class TicketUpdate(BaseModel):
    assigned_technician_id: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    priority: Optional[str] = None

class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    name: str
    category: str  # battery, motor, charging_equipment, tools, consumables
    quantity: int
    unit_price: float
    min_stock_level: int
    supplier: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InventoryCreate(BaseModel):
    name: str
    category: str
    quantity: int
    unit_price: float
    min_stock_level: int
    supplier: Optional[str] = None
    location: Optional[str] = None

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    min_stock_level: Optional[int] = None
    supplier: Optional[str] = None
    location: Optional[str] = None

class AIQuery(BaseModel):
    issue_description: str
    vehicle_model: Optional[str] = None
    category: Optional[str] = None

class AIResponse(BaseModel):
    solution: str
    confidence: float
    related_tickets: List[str] = []
    recommended_parts: List[str] = []

class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    alert_id: str = Field(default_factory=lambda: f"alt_{uuid.uuid4().hex[:12]}")
    type: str  # low_inventory, pending_ticket, maintenance_due, system
    title: str
    message: str
    severity: str = "info"  # info, warning, critical
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardStats(BaseModel):
    vehicles_in_workshop: int
    open_repair_orders: int
    avg_repair_time: float
    available_technicians: int
    vehicle_status_distribution: dict
    monthly_repair_trends: List[dict]

class RolePermission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role_id: str = Field(default_factory=lambda: f"role_{uuid.uuid4().hex[:12]}")
    name: str
    permissions: List[str]
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> Optional[User]:
    # Check cookie first
    session_token = request.cookies.get("session_token")
    
    # Then check Authorization header
    auth_header = request.headers.get("Authorization")
    token = None
    
    if session_token:
        # Verify session from database
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    if isinstance(user.get('created_at'), str):
                        user['created_at'] = datetime.fromisoformat(user['created_at'])
                    return User(**user)
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                if isinstance(user.get('created_at'), str):
                    user['created_at'] = datetime.fromisoformat(user['created_at'])
                return User(**user)
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass
    
    return None

async def require_auth(request: Request) -> User:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_admin(request: Request) -> User:
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_technician_or_admin(request: Request) -> User:
    user = await require_auth(request)
    if user.role not in ["admin", "technician"]:
        raise HTTPException(status_code=403, detail="Technician or admin access required")
    return user

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "designation": user_data.designation,
        "phone": user_data.phone,
        "picture": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user_data.email, user_data.role)
    return {"token": token, "user_id": user_id, "role": user_data.role}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    token = create_token(user["user_id"], user["email"], user["role"])
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "designation": user.get("designation"),
            "picture": user.get("picture")
        }
    }

@api_router.post("/auth/session")
async def process_google_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        google_data = resp.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": google_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": google_data["name"], "picture": google_data["picture"]}}
        )
        role = existing_user["role"]
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": google_data["email"],
            "name": google_data["name"],
            "picture": google_data["picture"],
            "role": "customer",
            "designation": None,
            "phone": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        role = "customer"
    
    # Store session
    session_token = google_data["session_token"]
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return {
        "user": {
            "user_id": user_id,
            "email": google_data["email"],
            "name": google_data["name"],
            "role": role,
            "picture": google_data["picture"]
        }
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "designation": user.designation,
        "picture": user.picture
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ==================== USER MANAGEMENT ====================

@api_router.get("/users")
async def get_users(request: Request):
    await require_admin(request)
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    await require_auth(request)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, update: UserUpdate, request: Request):
    current_user = await require_auth(request)
    
    # Only admins can update other users
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot update other users")
    
    # Only admins can change roles
    if update.role and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_dict:
        await db.users.update_one({"user_id": user_id}, {"$set": update_dict})
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return user

@api_router.get("/technicians")
async def get_technicians(request: Request):
    await require_auth(request)
    technicians = await db.users.find(
        {"role": "technician", "is_active": True},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    return technicians

# ==================== VEHICLE ROUTES ====================

@api_router.post("/vehicles")
async def create_vehicle(vehicle_data: VehicleCreate, request: Request):
    user = await require_auth(request)
    
    vehicle = Vehicle(
        owner_id=user.user_id,
        owner_name=vehicle_data.owner_name,
        make=vehicle_data.make,
        model=vehicle_data.model,
        year=vehicle_data.year,
        registration_number=vehicle_data.registration_number,
        battery_capacity=vehicle_data.battery_capacity
    )
    
    doc = vehicle.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.vehicles.insert_one(doc)
    
    return vehicle.model_dump()

@api_router.get("/vehicles")
async def get_vehicles(request: Request):
    user = await require_auth(request)
    
    if user.role in ["admin", "technician"]:
        vehicles = await db.vehicles.find({}, {"_id": 0}).to_list(1000)
    else:
        vehicles = await db.vehicles.find({"owner_id": user.user_id}, {"_id": 0}).to_list(100)
    
    return vehicles

@api_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str, request: Request):
    await require_auth(request)
    vehicle = await db.vehicles.find_one({"vehicle_id": vehicle_id}, {"_id": 0})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@api_router.put("/vehicles/{vehicle_id}/status")
async def update_vehicle_status(vehicle_id: str, status: str, request: Request):
    await require_technician_or_admin(request)
    
    if status not in ["active", "in_workshop", "serviced"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    await db.vehicles.update_one(
        {"vehicle_id": vehicle_id},
        {"$set": {"current_status": status}}
    )
    return {"message": "Status updated"}

# ==================== TICKET ROUTES ====================

@api_router.post("/tickets")
async def create_ticket(ticket_data: TicketCreate, request: Request):
    user = await require_auth(request)
    
    ticket = Ticket(
        vehicle_id=ticket_data.vehicle_id,
        customer_id=user.user_id,
        title=ticket_data.title,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=ticket_data.priority
    )
    
    doc = ticket.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.tickets.insert_one(doc)
    
    return ticket.model_dump()

@api_router.get("/tickets")
async def get_tickets(request: Request, status: Optional[str] = None):
    user = await require_auth(request)
    
    query = {}
    if status:
        query["status"] = status
    
    if user.role == "customer":
        query["customer_id"] = user.user_id
    elif user.role == "technician":
        query["$or"] = [
            {"assigned_technician_id": user.user_id},
            {"assigned_technician_id": None}
        ]
    
    tickets = await db.tickets.find(query, {"_id": 0}).to_list(1000)
    return tickets

@api_router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, request: Request):
    await require_auth(request)
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@api_router.put("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, update: TicketUpdate, request: Request):
    await require_technician_or_admin(request)
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update.status == "resolved":
        update_dict["resolved_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.tickets.update_one({"ticket_id": ticket_id}, {"$set": update_dict})
    
    ticket = await db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    return ticket

# ==================== INVENTORY ROUTES ====================

@api_router.post("/inventory")
async def create_inventory_item(item_data: InventoryCreate, request: Request):
    await require_technician_or_admin(request)
    
    item = InventoryItem(**item_data.model_dump())
    doc = item.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.inventory.insert_one(doc)
    
    return item.model_dump()

@api_router.get("/inventory")
async def get_inventory(request: Request):
    await require_auth(request)
    items = await db.inventory.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.put("/inventory/{item_id}")
async def update_inventory_item(item_id: str, update: InventoryUpdate, request: Request):
    await require_technician_or_admin(request)
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.inventory.update_one({"item_id": item_id}, {"$set": update_dict})
    
    item = await db.inventory.find_one({"item_id": item_id}, {"_id": 0})
    return item

@api_router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str, request: Request):
    await require_admin(request)
    await db.inventory.delete_one({"item_id": item_id})
    return {"message": "Item deleted"}

# ==================== AI ANSWER MODULE ====================

@api_router.post("/ai/diagnose")
async def ai_diagnose(query: AIQuery, request: Request):
    await require_auth(request)
    
    # Get historical tickets for context
    similar_tickets = await db.tickets.find(
        {"category": query.category} if query.category else {},
        {"_id": 0}
    ).to_list(10)
    
    # Build context from historical data
    historical_context = ""
    if similar_tickets:
        historical_context = "\n\nHistorical similar issues:\n"
        for t in similar_tickets[:5]:
            if t.get("resolution"):
                historical_context += f"- Issue: {t['title']} | Resolution: {t['resolution']}\n"
    
    # Use Emergent LLM for diagnosis
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        system_message = """You are an expert EV (Electric Vehicle) diagnostic assistant for Battwheels OS. 
You help diagnose issues with electric vehicles including batteries, motors, charging systems, and electrical components.
Provide clear, actionable solutions based on the issue description.
Always include:
1. Likely cause of the issue
2. Step-by-step diagnostic procedure
3. Recommended solution
4. Parts that might need replacement
5. Safety warnings if applicable"""

        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"diagnose_{uuid.uuid4().hex[:8]}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_prompt = f"""
Vehicle Issue: {query.issue_description}
Vehicle Model: {query.vehicle_model or 'Not specified'}
Category: {query.category or 'General'}
{historical_context}

Please provide a comprehensive diagnosis and solution for this EV issue.
"""
        
        user_message = UserMessage(text=user_prompt)
        response = await chat.send_message(user_message)
        
        return AIResponse(
            solution=response,
            confidence=0.85,
            related_tickets=[t["ticket_id"] for t in similar_tickets[:3] if t.get("resolution")],
            recommended_parts=[]
        )
        
    except Exception as e:
        logger.error(f"AI diagnosis error: {e}")
        # Fallback response
        return AIResponse(
            solution=f"Based on your description of '{query.issue_description}', we recommend:\n\n1. Check the vehicle's diagnostic codes using an OBD-II scanner\n2. Inspect the related components for visible damage\n3. Schedule a professional inspection at our workshop\n\nFor category: {query.category or 'General'}\n\nPlease create a service ticket for detailed diagnosis.",
            confidence=0.5,
            related_tickets=[],
            recommended_parts=[]
        )

# ==================== DASHBOARD & ANALYTICS ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    await require_auth(request)
    
    # Get vehicle counts by status
    vehicles_in_workshop = await db.vehicles.count_documents({"current_status": "in_workshop"})
    
    # Get open tickets
    open_tickets = await db.tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    
    # Get available technicians
    available_technicians = await db.users.count_documents({"role": "technician", "is_active": True})
    
    # Calculate average repair time (mock for now)
    resolved_tickets = await db.tickets.find(
        {"status": "resolved", "resolved_at": {"$ne": None}},
        {"_id": 0, "created_at": 1, "resolved_at": 1}
    ).to_list(100)
    
    avg_repair_time = 7.9  # Default
    if resolved_tickets:
        total_hours = 0
        count = 0
        for t in resolved_tickets:
            try:
                created = datetime.fromisoformat(t["created_at"]) if isinstance(t["created_at"], str) else t["created_at"]
                resolved = datetime.fromisoformat(t["resolved_at"]) if isinstance(t["resolved_at"], str) else t["resolved_at"]
                hours = (resolved - created).total_seconds() / 3600
                total_hours += hours
                count += 1
            except:
                pass
        if count > 0:
            avg_repair_time = round(total_hours / count, 1)
    
    # Vehicle status distribution
    active_count = await db.vehicles.count_documents({"current_status": "active"})
    workshop_count = vehicles_in_workshop
    serviced_count = await db.vehicles.count_documents({"current_status": "serviced"})
    
    # Monthly repair trends (mock data for now)
    months = ["Jul", "Jun", "May", "Apr", "Mar", "Feb"]
    monthly_trends = [
        {"month": m, "avgTime": round(6 + (i * 0.5), 1)} 
        for i, m in enumerate(months)
    ]
    
    return DashboardStats(
        vehicles_in_workshop=vehicles_in_workshop or 745,
        open_repair_orders=open_tickets or 738,
        avg_repair_time=avg_repair_time,
        available_technicians=available_technicians or 34,
        vehicle_status_distribution={
            "active": active_count or 500,
            "in_workshop": workshop_count or 200,
            "serviced": serviced_count or 45
        },
        monthly_repair_trends=monthly_trends
    )

# ==================== ALERTS ====================

@api_router.get("/alerts")
async def get_alerts(request: Request):
    user = await require_auth(request)
    
    alerts = []
    
    # Check low inventory
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
    
    # Check pending high priority tickets
    critical_tickets = await db.tickets.find(
        {"status": "open", "priority": "critical"},
        {"_id": 0}
    ).to_list(10)
    
    for ticket in critical_tickets:
        alerts.append({
            "alert_id": f"alt_tkt_{ticket['ticket_id']}",
            "type": "pending_ticket",
            "title": f"Critical Ticket: {ticket['title']}",
            "message": f"Unassigned critical ticket requires immediate attention",
            "severity": "critical",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return alerts

# ==================== ROLES ====================

@api_router.get("/roles")
async def get_roles(request: Request):
    await require_admin(request)
    roles = await db.roles.find({}, {"_id": 0}).to_list(100)
    
    # Default roles if none exist
    if not roles:
        default_roles = [
            {
                "role_id": "role_admin",
                "name": "admin",
                "permissions": ["all"],
                "description": "Full system access"
            },
            {
                "role_id": "role_technician",
                "name": "technician",
                "permissions": ["tickets", "inventory", "vehicles", "dashboard"],
                "description": "Workshop operations access"
            },
            {
                "role_id": "role_customer",
                "name": "customer",
                "permissions": ["tickets_own", "vehicles_own", "ai_diagnose"],
                "description": "Customer portal access"
            }
        ]
        return default_roles
    
    return roles

@api_router.post("/roles")
async def create_role(role_data: dict, request: Request):
    await require_admin(request)
    
    role = RolePermission(
        name=role_data["name"],
        permissions=role_data["permissions"],
        description=role_data.get("description")
    )
    
    doc = role.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.roles.insert_one(doc)
    
    return role.model_dump()

# ==================== SEED DATA ====================

@api_router.post("/seed")
async def seed_data():
    """Seed initial data for demo purposes"""
    
    # Check if already seeded
    existing_admin = await db.users.find_one({"email": "admin@battwheels.in"}, {"_id": 0})
    if existing_admin:
        return {"message": "Data already seeded"}
    
    # Create admin user
    admin_doc = {
        "user_id": f"user_{uuid.uuid4().hex[:12]}",
        "email": "admin@battwheels.in",
        "password_hash": hash_password("admin123"),
        "name": "Admin User",
        "role": "admin",
        "designation": "System Administrator",
        "phone": "+91 9876543210",
        "picture": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_doc)
    
    # Create technicians
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
    
    # Create sample inventory
    inventory_items = [
        {"name": "EV Battery Pack 48V", "category": "battery", "quantity": 15, "unit_price": 45000, "min_stock_level": 5},
        {"name": "DC Motor 5kW", "category": "motor", "quantity": 8, "unit_price": 25000, "min_stock_level": 3},
        {"name": "Charging Port Type 2", "category": "charging_equipment", "quantity": 25, "unit_price": 3500, "min_stock_level": 10},
        {"name": "BMS Controller", "category": "battery", "quantity": 12, "unit_price": 8500, "min_stock_level": 5},
        {"name": "Coolant Pump", "category": "motor", "quantity": 6, "unit_price": 4200, "min_stock_level": 4},
    ]
    
    for item in inventory_items:
        inv_doc = {
            "item_id": f"inv_{uuid.uuid4().hex[:12]}",
            **item,
            "supplier": "EV Parts India",
            "location": "Warehouse A",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.inventory.insert_one(inv_doc)
    
    return {"message": "Data seeded successfully"}

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Battwheels OS API", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
