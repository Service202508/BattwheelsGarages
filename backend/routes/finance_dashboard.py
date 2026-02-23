"""
Finance Dashboard API Routes
============================
Provides aggregated financial data for the dashboard view.

Author: Battwheels OS
"""

from fastapi import APIRouter, Request, HTTPException
import logging
import jwt

from services.finance_dashboard_service import (
    init_finance_dashboard_service,
    get_finance_dashboard_service
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/finance/dashboard", tags=["Finance Dashboard"])

db_ref = None


def set_db(db):
    global db_ref
    db_ref = db
    init_finance_dashboard_service(db)


def get_service():
    return get_finance_dashboard_service()


async def get_org_id(request: Request) -> str:
    org_id = request.headers.get("X-Organization-ID")
    if org_id:
        return org_id
    
    org_id = request.cookies.get("org_id")
    if org_id:
        return org_id
    
    user = getattr(request.state, "user", None)
    if user and user.get("org_id"):
        return user.get("org_id")
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, options={"verify_signature": False})
            if payload.get("org_id"):
                return payload.get("org_id")
        except:
            pass
    
    raise HTTPException(status_code=400, detail="Organization ID required")


@router.get("")
async def get_dashboard(request: Request):
    """Get complete finance dashboard data"""
    service = get_service()
    org_id = await get_org_id(request)
    
    data = await service.get_dashboard_data(org_id)
    
    return {"code": 0, "dashboard": data}


@router.get("/cash-position")
async def get_cash_position(request: Request):
    """Get cash position cards data only"""
    service = get_service()
    org_id = await get_org_id(request)
    
    data = await service._get_cash_position(org_id)
    
    return {"code": 0, "cash_position": data}


@router.get("/cash-flow")
async def get_cash_flow(request: Request, months: int = 6):
    """Get cash flow trend data"""
    service = get_service()
    org_id = await get_org_id(request)
    
    data = await service._get_cash_flow_trend(org_id, months)
    
    return {"code": 0, "cash_flow": data}


@router.get("/alerts")
async def get_alerts(request: Request):
    """Get overdue bills, pending expenses, and upcoming bills"""
    service = get_service()
    org_id = await get_org_id(request)
    
    overdue_bills = await service._get_overdue_bills(org_id)
    pending_expenses = await service._get_pending_expenses(org_id)
    upcoming_bills = await service._get_upcoming_bills(org_id)
    
    return {
        "code": 0,
        "alerts": {
            "overdue_bills": overdue_bills,
            "pending_expenses": pending_expenses,
            "upcoming_bills": upcoming_bills
        }
    }
