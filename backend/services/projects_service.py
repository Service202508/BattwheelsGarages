"""
Battwheels OS - Projects Service
================================

Project management backend with:
- Project CRUD operations
- Task management
- Time logging
- Expense tracking
- Profitability calculation
- Invoice generation from projects
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger(__name__)


# ==================== PROJECT STATUS ENUM ====================

PROJECT_STATUSES = ["PLANNING", "ACTIVE", "ON_HOLD", "COMPLETED", "CANCELLED"]
TASK_STATUSES = ["TODO", "IN_PROGRESS", "REVIEW", "DONE"]
TASK_PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
BILLING_TYPES = ["FIXED", "HOURLY", "RETAINER"]


# ==================== PROJECTS SERVICE ====================

class ProjectsService:
    """Projects management service"""
    
    def __init__(self, db):
        self.db = db
        self.projects = db.projects
        self.tasks = db.project_tasks
        self.time_logs = db.project_time_logs
        self.expenses = db.project_expenses
    
    # ==================== PROJECT CRUD ====================
    
    async def create_project(
        self,
        organization_id: str,
        name: str,
        description: str = "",
        client_id: Optional[str] = None,
        status: str = "PLANNING",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        deadline: Optional[str] = None,
        budget_amount: float = 0,
        budget_currency: str = "INR",
        billing_type: str = "FIXED",
        hourly_rate: float = 0,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new project"""
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        project = {
            "project_id": project_id,
            "organization_id": organization_id,
            "name": name,
            "description": description,
            "client_id": client_id,
            "status": status if status in PROJECT_STATUSES else "PLANNING",
            "start_date": start_date,
            "end_date": end_date,
            "deadline": deadline,
            "budget_amount": budget_amount,
            "budget_currency": budget_currency,
            "billing_type": billing_type if billing_type in BILLING_TYPES else "FIXED",
            "hourly_rate": hourly_rate,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
            "is_archived": False
        }
        
        await self.projects.insert_one(project)
        logger.info(f"Created project: {project_id} - {name}")
        
        return {k: v for k, v in project.items() if k != "_id"}
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        return await self.projects.find_one(
            {"project_id": project_id},
            {"_id": 0}
        )
    
    async def list_projects(
        self,
        organization_id: str,
        status: Optional[str] = None,
        client_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List projects with optional filters"""
        query = {"organization_id": organization_id, "is_archived": {"$ne": True}}
        
        if status:
            query["status"] = status
        if client_id:
            query["client_id"] = client_id
        
        cursor = self.projects.find(query, {"_id": 0})
        cursor.sort("created_at", -1).skip(skip).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def update_project(
        self,
        project_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update project"""
        # Remove protected fields
        updates.pop("project_id", None)
        updates.pop("organization_id", None)
        updates.pop("created_at", None)
        updates.pop("created_by", None)
        
        # Validate status and billing_type
        if "status" in updates and updates["status"] not in PROJECT_STATUSES:
            updates.pop("status")
        if "billing_type" in updates and updates["billing_type"] not in BILLING_TYPES:
            updates.pop("billing_type")
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.projects.find_one_and_update(
            {"project_id": project_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def delete_project(self, project_id: str) -> bool:
        """Soft delete project"""
        result = await self.projects.update_one(
            {"project_id": project_id},
            {"$set": {"is_archived": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0
    
    # ==================== TASK MANAGEMENT ====================
    
    async def create_task(
        self,
        project_id: str,
        title: str,
        description: str = "",
        assigned_to: Optional[str] = None,
        status: str = "TODO",
        priority: str = "MEDIUM",
        due_date: Optional[str] = None,
        estimated_hours: float = 0,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a task for a project"""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        task = {
            "task_id": task_id,
            "project_id": project_id,
            "title": title,
            "description": description,
            "assigned_to": assigned_to,
            "status": status if status in TASK_STATUSES else "TODO",
            "priority": priority if priority in TASK_PRIORITIES else "MEDIUM",
            "due_date": due_date,
            "estimated_hours": estimated_hours,
            "actual_hours": 0,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }
        
        await self.tasks.insert_one(task)
        logger.info(f"Created task: {task_id} for project {project_id}")
        
        return {k: v for k, v in task.items() if k != "_id"}
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        return await self.tasks.find_one({"task_id": task_id}, {"_id": 0})
    
    async def list_tasks(
        self,
        project_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks for a project"""
        query = {"project_id": project_id}
        
        if status:
            query["status"] = status
        if assigned_to:
            query["assigned_to"] = assigned_to
        
        return await self.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    async def update_task(
        self,
        task_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update task"""
        updates.pop("task_id", None)
        updates.pop("project_id", None)
        updates.pop("created_at", None)
        
        if "status" in updates and updates["status"] not in TASK_STATUSES:
            updates.pop("status")
        if "priority" in updates and updates["priority"] not in TASK_PRIORITIES:
            updates.pop("priority")
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.tasks.find_one_and_update(
            {"task_id": task_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        result = await self.tasks.delete_one({"task_id": task_id})
        return result.deleted_count > 0
    
    # ==================== TIME LOGGING ====================
    
    async def log_time(
        self,
        project_id: str,
        employee_id: str,
        hours_logged: float,
        description: str = "",
        task_id: Optional[str] = None,
        log_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log time against a project"""
        log_id = f"timelog_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        time_log = {
            "log_id": log_id,
            "project_id": project_id,
            "task_id": task_id,
            "employee_id": employee_id,
            "hours_logged": hours_logged,
            "description": description,
            "log_date": log_date or now.split("T")[0],
            "created_at": now
        }
        
        await self.time_logs.insert_one(time_log)
        
        # Update task actual hours if task specified
        if task_id:
            await self.tasks.update_one(
                {"task_id": task_id},
                {"$inc": {"actual_hours": hours_logged}}
            )
        
        logger.info(f"Logged {hours_logged}h for project {project_id}")
        
        return {k: v for k, v in time_log.items() if k != "_id"}
    
    async def get_time_logs(
        self,
        project_id: str,
        employee_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get time logs for a project"""
        query = {"project_id": project_id}
        
        if employee_id:
            query["employee_id"] = employee_id
        
        if start_date:
            query["log_date"] = query.get("log_date", {})
            query["log_date"]["$gte"] = start_date
        
        if end_date:
            query["log_date"] = query.get("log_date", {})
            query["log_date"]["$lte"] = end_date
        
        return await self.time_logs.find(query, {"_id": 0}).sort("log_date", -1).to_list(500)
    
    # ==================== EXPENSE TRACKING ====================
    
    async def add_expense(
        self,
        project_id: str,
        amount: float,
        description: str,
        expense_date: Optional[str] = None,
        expense_id: Optional[str] = None,
        approved_by: Optional[str] = None,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Add expense to project"""
        pe_id = f"proj_exp_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        expense = {
            "project_expense_id": pe_id,
            "project_id": project_id,
            "expense_id": expense_id,  # Link to main expenses if exists
            "amount": amount,
            "description": description,
            "category": category,
            "expense_date": expense_date or now.split("T")[0],
            "approved_by": approved_by,
            "created_at": now
        }
        
        await self.expenses.insert_one(expense)
        logger.info(f"Added expense ₹{amount} to project {project_id}")
        
        return {k: v for k, v in expense.items() if k != "_id"}
    
    async def get_expenses(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all expenses for a project"""
        return await self.expenses.find(
            {"project_id": project_id},
            {"_id": 0}
        ).sort("expense_date", -1).to_list(200)
    
    # ==================== PROFITABILITY CALCULATION ====================
    
    async def calculate_profitability(
        self,
        project_id: str,
        employee_cost_rate: float = 500  # Default ₹500/hour
    ) -> Dict[str, Any]:
        """
        Calculate project profitability
        
        Revenue:
          - Fixed: budget_amount
          - Hourly: total_hours × hourly_rate
        Cost:
          - Total expenses
          - Employee cost (hours × cost rate)
        Profit:
          - Revenue - Cost
        """
        project = await self.get_project(project_id)
        if not project:
            return {"error": "Project not found"}
        
        # Get time logs
        time_logs = await self.get_time_logs(project_id)
        total_hours = sum(log.get("hours_logged", 0) for log in time_logs)
        
        # Get tasks for estimated hours
        tasks = await self.list_tasks(project_id)
        estimated_hours = sum(task.get("estimated_hours", 0) for task in tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == "DONE"])
        total_tasks = len(tasks)
        
        # Get expenses
        expenses = await self.get_expenses(project_id)
        total_expenses = sum(exp.get("amount", 0) for exp in expenses)
        
        # Calculate revenue
        billing_type = project.get("billing_type", "FIXED")
        if billing_type == "FIXED":
            revenue = project.get("budget_amount", 0)
        elif billing_type == "HOURLY":
            revenue = total_hours * project.get("hourly_rate", 0)
        else:  # RETAINER
            revenue = project.get("budget_amount", 0)
        
        # Calculate costs
        employee_cost = total_hours * employee_cost_rate
        total_cost = total_expenses + employee_cost
        
        # Calculate profit
        gross_profit = revenue - total_cost
        margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0
        
        # Completion percentage
        hours_completion = (total_hours / estimated_hours * 100) if estimated_hours > 0 else 0
        tasks_completion = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        completion_pct = (hours_completion + tasks_completion) / 2 if estimated_hours > 0 else tasks_completion
        
        return {
            "project_id": project_id,
            "project_name": project.get("name"),
            "billing_type": billing_type,
            "budget": project.get("budget_amount", 0),
            "hourly_rate": project.get("hourly_rate", 0),
            "revenue": round(revenue, 2),
            "costs": {
                "expenses": round(total_expenses, 2),
                "employee_cost": round(employee_cost, 2),
                "total": round(total_cost, 2)
            },
            "gross_profit": round(gross_profit, 2),
            "margin_pct": round(margin_pct, 1),
            "hours": {
                "estimated": estimated_hours,
                "logged": round(total_hours, 2),
                "remaining": max(0, estimated_hours - total_hours)
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "pending": total_tasks - completed_tasks
            },
            "completion_pct": round(completion_pct, 1),
            "is_profitable": gross_profit >= 0,
            "status": project.get("status")
        }
    
    # ==================== INVOICE GENERATION ====================
    
    async def generate_invoice_data(
        self,
        project_id: str,
        include_time_logs: bool = True,
        include_expenses: bool = False,
        group_by: str = "task"  # "task" or "time_log"
    ) -> Dict[str, Any]:
        """
        Generate invoice data from project
        
        Returns line items based on:
        - Time logs grouped by task (or individual entries)
        - Optionally include reimbursable expenses
        """
        project = await self.get_project(project_id)
        if not project:
            return {"error": "Project not found"}
        
        line_items = []
        
        if include_time_logs:
            if group_by == "task":
                # Group time by task
                tasks = await self.list_tasks(project_id)
                for task in tasks:
                    if task.get("actual_hours", 0) > 0:
                        if project.get("billing_type") == "HOURLY":
                            amount = task["actual_hours"] * project.get("hourly_rate", 0)
                        else:
                            # For fixed, prorate based on hours
                            total_estimated = sum(t.get("estimated_hours", 0) for t in tasks)
                            if total_estimated > 0:
                                amount = project.get("budget_amount", 0) * (task.get("estimated_hours", 0) / total_estimated)
                            else:
                                amount = 0
                        
                        line_items.append({
                            "name": task.get("title"),
                            "description": task.get("description", ""),
                            "quantity": task.get("actual_hours", 0),
                            "unit": "hours",
                            "rate": project.get("hourly_rate", 0) if project.get("billing_type") == "HOURLY" else amount / max(task.get("actual_hours", 1), 1),
                            "amount": round(amount, 2),
                            "task_id": task.get("task_id")
                        })
            else:
                # Individual time log entries
                time_logs = await self.get_time_logs(project_id)
                for log in time_logs:
                    amount = log.get("hours_logged", 0) * project.get("hourly_rate", 0)
                    line_items.append({
                        "name": log.get("description") or f"Work on {log.get('log_date')}",
                        "description": "",
                        "quantity": log.get("hours_logged", 0),
                        "unit": "hours",
                        "rate": project.get("hourly_rate", 0),
                        "amount": round(amount, 2),
                        "time_log_id": log.get("log_id")
                    })
        
        if include_expenses:
            expenses = await self.get_expenses(project_id)
            for exp in expenses:
                line_items.append({
                    "name": f"Expense: {exp.get('description')}",
                    "description": exp.get("category", ""),
                    "quantity": 1,
                    "unit": "nos",
                    "rate": exp.get("amount", 0),
                    "amount": exp.get("amount", 0),
                    "expense_id": exp.get("project_expense_id")
                })
        
        total_amount = sum(item.get("amount", 0) for item in line_items)
        
        return {
            "project_id": project_id,
            "project_name": project.get("name"),
            "client_id": project.get("client_id"),
            "billing_type": project.get("billing_type"),
            "line_items": line_items,
            "sub_total": round(total_amount, 2),
            "notes": f"Invoice for project: {project.get('name')}"
        }


# ==================== SERVICE FACTORY ====================

_projects_service: Optional[ProjectsService] = None


def get_projects_service() -> ProjectsService:
    if _projects_service is None:
        raise ValueError("ProjectsService not initialized")
    return _projects_service


def init_projects_service(db) -> ProjectsService:
    global _projects_service
    _projects_service = ProjectsService(db)
    logger.info("Projects Service initialized")
    return _projects_service
