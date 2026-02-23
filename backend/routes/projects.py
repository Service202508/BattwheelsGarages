"""
Battwheels OS - Projects API Routes
===================================

RESTful API for project management:
- Project CRUD
- Task management
- Time logging
- Expense tracking
- Profitability reports
- Invoice generation from projects
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging

from services.projects_service import (
    init_projects_service, 
    get_projects_service,
    PROJECT_STATUSES,
    TASK_STATUSES,
    TASK_PRIORITIES,
    BILLING_TYPES
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


# ==================== PYDANTIC MODELS ====================

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    client_id: Optional[str] = None
    status: str = "PLANNING"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    deadline: Optional[str] = None
    budget_amount: float = 0
    budget_currency: str = "INR"
    billing_type: str = "FIXED"
    hourly_rate: float = 0


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    deadline: Optional[str] = None
    budget_amount: Optional[float] = None
    hourly_rate: Optional[float] = None
    billing_type: Optional[str] = None


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assigned_to: Optional[str] = None
    status: str = "TODO"
    priority: str = "MEDIUM"
    due_date: Optional[str] = None
    estimated_hours: float = 0


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None


class TimeLogCreate(BaseModel):
    hours_logged: float
    description: str = ""
    task_id: Optional[str] = None
    log_date: Optional[str] = None
    employee_id: Optional[str] = None  # Optional - will use current user if not provided


class ExpenseCreate(BaseModel):
    amount: float
    description: str
    expense_date: Optional[str] = None
    expense_id: Optional[str] = None
    category: str = "general"


class ProjectInvoiceRequest(BaseModel):
    """Enhanced invoice generation from project time logs"""
    billing_period_from: str  # YYYY-MM-DD
    billing_period_to: str    # YYYY-MM-DD
    include_expenses: bool = False
    line_item_grouping: str = "BY_TASK"  # BY_TASK, BY_EMPLOYEE, BY_DATE
    notes: Optional[str] = None


class InvoiceGenerateRequest(BaseModel):
    include_time_logs: bool = True
    include_expenses: bool = False
    group_by: str = "task"  # "task" or "time_log"


class ExpenseApprovalRequest(BaseModel):
    """Expense approval/rejection"""
    approved: bool = True


# ==================== DEPENDENCY ====================

db_ref = None

def set_db(db):
    global db_ref
    db_ref = db
    init_projects_service(db)


def get_service():
    if db_ref is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return get_projects_service()
    except:
        return init_projects_service(db_ref)


async def get_org_id(request: Request) -> str:
    """Extract organization ID from JWT token"""
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            import jwt
            import os
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, os.environ.get("JWT_SECRET", "battwheels-secret"), algorithms=["HS256"])
            return payload.get("org_id", "")
    except:
        pass
    return ""


async def get_current_user_id(request: Request) -> str:
    """Extract user ID from JWT token"""
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            import jwt
            import os
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, os.environ.get("JWT_SECRET", "battwheels-secret"), algorithms=["HS256"])
            return payload.get("user_id", "")
    except:
        pass
    return ""


# ==================== PROJECT ROUTES ====================

@router.get("")
async def list_projects(
    request: Request,
    status: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List all projects for the organization"""
    service = get_service()
    org_id = await get_org_id(request)
    
    projects = await service.list_projects(
        organization_id=org_id,
        status=status,
        client_id=client_id,
        skip=skip,
        limit=limit
    )
    
    # Get summary stats for each project
    for project in projects:
        tasks = await service.list_tasks(project["project_id"])
        time_logs = await service.get_time_logs(project["project_id"])
        
        project["task_count"] = len(tasks)
        project["completed_tasks"] = len([t for t in tasks if t.get("status") == "DONE"])
        project["total_hours"] = sum(log.get("hours_logged", 0) for log in time_logs)
    
    return {
        "code": 0,
        "projects": projects,
        "total": len(projects)
    }


@router.post("")
async def create_project(data: ProjectCreate, request: Request):
    """Create a new project"""
    service = get_service()
    org_id = await get_org_id(request)
    user_id = await get_current_user_id(request)
    
    project = await service.create_project(
        organization_id=org_id,
        name=data.name,
        description=data.description,
        client_id=data.client_id,
        status=data.status,
        start_date=data.start_date,
        end_date=data.end_date,
        deadline=data.deadline,
        budget_amount=data.budget_amount,
        budget_currency=data.budget_currency,
        billing_type=data.billing_type,
        hourly_rate=data.hourly_rate,
        created_by=user_id
    )
    
    return {"code": 0, "message": "Project created", "project": project}


@router.get("/{project_id}")
async def get_project(project_id: str, request: Request):
    """Get project details"""
    service = get_service()
    
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Include tasks and summary
    tasks = await service.list_tasks(project_id)
    time_logs = await service.get_time_logs(project_id)
    expenses = await service.get_expenses(project_id)
    
    project["tasks"] = tasks
    project["task_count"] = len(tasks)
    project["completed_tasks"] = len([t for t in tasks if t.get("status") == "DONE"])
    project["total_hours"] = sum(log.get("hours_logged", 0) for log in time_logs)
    project["total_expenses"] = sum(exp.get("amount", 0) for exp in expenses)
    
    return {"code": 0, "project": project}


@router.put("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, request: Request):
    """Update project"""
    service = get_service()
    
    updates = {k: v for k, v in data.dict().items() if v is not None}
    
    project = await service.update_project(project_id, updates)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"code": 0, "message": "Project updated", "project": project}


@router.delete("/{project_id}")
async def delete_project(project_id: str, request: Request):
    """Delete (archive) project"""
    service = get_service()
    
    success = await service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"code": 0, "message": "Project archived"}


# ==================== TASK ROUTES ====================

@router.get("/{project_id}/tasks")
async def list_tasks(
    project_id: str,
    request: Request,
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None)
):
    """List tasks for a project"""
    service = get_service()
    
    tasks = await service.list_tasks(project_id, status, assigned_to)
    
    return {"code": 0, "tasks": tasks, "total": len(tasks)}


@router.post("/{project_id}/tasks")
async def create_task(project_id: str, data: TaskCreate, request: Request):
    """Create a task for a project"""
    service = get_service()
    user_id = await get_current_user_id(request)
    
    # Verify project exists
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    task = await service.create_task(
        project_id=project_id,
        title=data.title,
        description=data.description,
        assigned_to=data.assigned_to,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
        estimated_hours=data.estimated_hours,
        created_by=user_id
    )
    
    return {"code": 0, "message": "Task created", "task": task}


@router.put("/{project_id}/tasks/{task_id}")
async def update_task(project_id: str, task_id: str, data: TaskUpdate, request: Request):
    """Update a task"""
    service = get_service()
    
    updates = {k: v for k, v in data.dict().items() if v is not None}
    
    task = await service.update_task(task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"code": 0, "message": "Task updated", "task": task}


@router.delete("/{project_id}/tasks/{task_id}")
async def delete_task(project_id: str, task_id: str, request: Request):
    """Delete a task"""
    service = get_service()
    
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"code": 0, "message": "Task deleted"}


# ==================== TIME LOG ROUTES ====================

@router.get("/{project_id}/time-logs")
async def get_time_logs(
    project_id: str,
    request: Request,
    employee_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get time logs for a project"""
    service = get_service()
    
    logs = await service.get_time_logs(project_id, employee_id, start_date, end_date)
    total_hours = sum(log.get("hours_logged", 0) for log in logs)
    
    return {
        "code": 0,
        "time_logs": logs,
        "total": len(logs),
        "total_hours": round(total_hours, 2)
    }


@router.post("/{project_id}/time-log")
async def log_time(project_id: str, data: TimeLogCreate, request: Request):
    """Log time against a project"""
    service = get_service()
    user_id = await get_current_user_id(request)
    
    # Verify project exists
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    employee_id = data.employee_id or user_id
    
    log = await service.log_time(
        project_id=project_id,
        employee_id=employee_id,
        hours_logged=data.hours_logged,
        description=data.description,
        task_id=data.task_id,
        log_date=data.log_date
    )
    
    return {"code": 0, "message": "Time logged", "time_log": log}


# ==================== EXPENSE ROUTES ====================

@router.get("/{project_id}/expenses")
async def get_expenses(project_id: str, request: Request):
    """Get expenses for a project"""
    service = get_service()
    
    expenses = await service.get_expenses(project_id)
    total = sum(exp.get("amount", 0) for exp in expenses)
    
    return {
        "code": 0,
        "expenses": expenses,
        "total": len(expenses),
        "total_amount": round(total, 2)
    }


@router.post("/{project_id}/expenses")
async def add_expense(project_id: str, data: ExpenseCreate, request: Request):
    """Add expense to a project"""
    service = get_service()
    user_id = await get_current_user_id(request)
    
    # Verify project exists
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    expense = await service.add_expense(
        project_id=project_id,
        amount=data.amount,
        description=data.description,
        expense_date=data.expense_date,
        expense_id=data.expense_id,
        category=data.category,
        approved_by=user_id
    )
    
    # Post journal entry for project expense
    try:
        org_id = await get_org_id(request)
        journal_entry = {
            "entry_type": "PROJECT_EXPENSE",
            "organization_id": org_id,
            "reference_type": "PROJECT",
            "reference_id": project_id,
            "date": datetime.now(timezone.utc).isoformat(),
            "narration": f"Project expense: {data.description} | Project: {project.get('name')}",
            "total_debit": data.amount,
            "total_credit": data.amount,
            "lines": [
                {
                    "account_type": "PROJECT_EXPENSE",
                    "debit": data.amount,
                    "credit": 0,
                    "description": data.description
                },
                {
                    "account_type": "ACCOUNTS_PAYABLE",
                    "debit": 0,
                    "credit": data.amount,
                    "description": "Project expense payable"
                }
            ],
            "created_at": datetime.now(timezone.utc)
        }
        await db_ref.journal_entries.insert_one(journal_entry)
    except Exception as e:
        logger.warning(f"Failed to post journal entry for project expense: {e}")
    
    return {"code": 0, "message": "Expense added", "expense": expense}


# ==================== PROFITABILITY ====================

@router.get("/{project_id}/profitability")
async def get_profitability(
    project_id: str,
    request: Request,
    employee_cost_rate: float = Query(500, description="Employee hourly cost rate")
):
    """Get project profitability analysis"""
    service = get_service()
    
    profitability = await service.calculate_profitability(project_id, employee_cost_rate)
    
    if "error" in profitability:
        raise HTTPException(status_code=404, detail=profitability["error"])
    
    return {"code": 0, "profitability": profitability}


# ==================== INVOICE GENERATION ====================

@router.post("/{project_id}/invoice")
async def generate_invoice(project_id: str, data: InvoiceGenerateRequest, request: Request):
    """Generate invoice from project"""
    service = get_service()
    
    invoice_data = await service.generate_invoice_data(
        project_id=project_id,
        include_time_logs=data.include_time_logs,
        include_expenses=data.include_expenses,
        group_by=data.group_by
    )
    
    if "error" in invoice_data:
        raise HTTPException(status_code=404, detail=invoice_data["error"])
    
    # Create actual invoice if we have line items
    if invoice_data.get("line_items"):
        try:
            org_id = await get_org_id(request)
            
            # Get client details
            client_id = invoice_data.get("client_id")
            client = None
            if client_id:
                client = await db_ref.contacts.find_one({"contact_id": client_id}, {"_id": 0})
            
            # Create invoice
            import uuid
            invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
            invoice_number = f"PROJ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
            
            invoice = {
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "organization_id": org_id,
                "project_id": project_id,
                "customer_id": client_id,
                "customer_name": client.get("name") if client else "Project Client",
                "customer_email": client.get("email") if client else "",
                "customer_gstin": client.get("gstin") if client else "",
                "invoice_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "due_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "sub_total": invoice_data["sub_total"],
                "tax_total": 0,
                "grand_total": invoice_data["sub_total"],
                "balance_due": invoice_data["sub_total"],
                "status": "draft",
                "notes": invoice_data.get("notes", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db_ref.invoices.insert_one(invoice)
            
            # Create line items
            for idx, item in enumerate(invoice_data["line_items"]):
                line_item = {
                    "line_item_id": f"li_{uuid.uuid4().hex[:12]}",
                    "invoice_id": invoice_id,
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "quantity": item["quantity"],
                    "unit": item.get("unit", "nos"),
                    "rate": item["rate"],
                    "amount": item["amount"],
                    "tax_rate": 0,
                    "tax_amount": 0,
                    "total": item["amount"],
                    "order": idx + 1
                }
                await db_ref.invoice_line_items.insert_one(line_item)
            
            invoice_data["invoice_id"] = invoice_id
            invoice_data["invoice_number"] = invoice_number
            invoice_data["message"] = "Invoice created successfully"
            
        except Exception as e:
            logger.error(f"Failed to create invoice: {e}")
            invoice_data["message"] = f"Invoice data generated but creation failed: {str(e)}"
    
    return {"code": 0, **invoice_data}


# ==================== DASHBOARD STATS ====================

@router.get("/stats/dashboard")
async def get_dashboard_stats(request: Request):
    """Get project dashboard statistics"""
    service = get_service()
    org_id = await get_org_id(request)
    
    projects = await service.list_projects(org_id)
    
    # Calculate stats
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.get("status") == "ACTIVE"])
    completed_projects = len([p for p in projects if p.get("status") == "COMPLETED"])
    
    total_budget = sum(p.get("budget_amount", 0) for p in projects)
    
    # Get recent activity
    recent_logs = []
    for project in projects[:5]:
        logs = await service.get_time_logs(project["project_id"])
        for log in logs[:3]:
            log["project_name"] = project.get("name")
            recent_logs.append(log)
    
    recent_logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "code": 0,
        "stats": {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "on_hold_projects": len([p for p in projects if p.get("status") == "ON_HOLD"]),
            "total_budget": total_budget,
            "projects_by_status": {
                status: len([p for p in projects if p.get("status") == status])
                for status in PROJECT_STATUSES
            }
        },
        "recent_activity": recent_logs[:10]
    }
