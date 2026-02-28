"""
Scheduled Jobs Service
Handles automated tasks like overdue invoice updates and payment reminders
"""
from datetime import datetime, timezone, timedelta
import logging
import uuid
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
_client = AsyncIOMotorClient(MONGO_URL)
_db = _client[DB_NAME]

def get_db():
    return _db


async def update_overdue_invoices():
    """
    Update invoice status to 'overdue' for invoices past due date.
    Should be run daily.
    SCHEDULER-FIX: org_id scoped from each invoice record — Sprint 1B
    """
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Fetch matching invoices with their org_ids first
    invoices = await db.invoices.find(
        {
            "status": {"$in": ["sent", "partial"]},
            "due_date": {"$lt": today},
            "balance": {"$gt": 0}
        },
        {"_id": 1, "organization_id": 1}
    ).to_list(length=1000)
    
    updated = 0
    for inv in invoices:
        # SCHEDULER-FIX: org_id scoped from invoice record — Sprint 1B
        await db.invoices.update_one(
            {"_id": inv["_id"], "organization_id": inv.get("organization_id")},
            {"$set": {"status": "overdue"}}
        )
        updated += 1
    
    logger.info(f"Marked {updated} invoices as overdue")
    return {"updated": updated}


async def generate_recurring_invoices():
    """
    Generate invoices from recurring invoice profiles that are due.
    Should be run daily.
    """
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Find recurring invoices due for generation
    recurring = await db.recurring_invoices.find({
        "status": "active",
        "next_invoice_date": {"$lte": today}
    }, {"_id": 0}).to_list(length=500)
    
    generated = 0
    errors = []
    
    for ri in recurring:
        try:
            # Get next invoice number
            counter = await db.counters.find_one_and_update(
                {"_id": "invoices"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            seq = counter.get("seq", 1)
            invoice_number = f"INV-{seq:06d}"
            invoice_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
            
            # Calculate due date based on payment terms
            payment_terms = ri.get("payment_terms", 30)
            due_date = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=payment_terms)).strftime("%Y-%m-%d")
            
            # Create invoice
            invoice = {
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "customer_id": ri.get("customer_id"),
                "customer_name": ri.get("customer_name"),
                "date": today,
                "due_date": due_date,
                "payment_terms": payment_terms,
                "line_items": ri.get("line_items", []),
                "sub_total": ri.get("sub_total", 0),
                "tax_total": ri.get("tax_total", 0),
                "discount_total": ri.get("discount_total", 0),
                "total": ri.get("total", 0),
                "balance": ri.get("total", 0),
                "status": "sent",
                "from_recurring_invoice_id": ri.get("recurring_invoice_id"),
                "notes": ri.get("notes", ""),
                "terms": ri.get("terms", ""),
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await db.invoices.insert_one(invoice)
            
            # Update customer outstanding
            await db.contacts.update_one(
                {"contact_id": ri.get("customer_id")},
                {"$inc": {"outstanding_receivable_amount": ri.get("total", 0)}}
            )
            
            # Calculate next invoice date
            frequency = ri.get("recurrence_frequency", "monthly")
            repeat_every = ri.get("repeat_every", 1)
            
            current_date = datetime.strptime(ri.get("next_invoice_date"), "%Y-%m-%d")
            
            if frequency == "daily":
                next_date = current_date + timedelta(days=repeat_every)
            elif frequency == "weekly":
                next_date = current_date + timedelta(weeks=repeat_every)
            elif frequency == "monthly":
                next_month = current_date.month + repeat_every
                next_year = current_date.year + (next_month - 1) // 12
                next_month = ((next_month - 1) % 12) + 1
                try:
                    next_date = current_date.replace(year=next_year, month=next_month)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    next_date = current_date.replace(year=next_year, month=next_month, day=min(current_date.day, last_day))
            elif frequency == "yearly":
                next_date = current_date.replace(year=current_date.year + repeat_every)
            else:
                next_date = current_date + timedelta(days=30 * repeat_every)
            
            next_date_str = next_date.strftime("%Y-%m-%d")
            
            # Check if end date reached
            end_date = ri.get("end_date")
            new_status = ri.get("status")
            if end_date and next_date_str > end_date and not ri.get("never_expires"):
                new_status = "expired"
            
            # Update recurring invoice
            await db.recurring_invoices.update_one(
                {"recurring_invoice_id": ri.get("recurring_invoice_id")},
                {
                    "$set": {
                        "next_invoice_date": next_date_str,
                        "last_invoice_date": today,
                        "status": new_status
                    },
                    "$inc": {"invoices_generated": 1}
                }
            )
            
            generated += 1
            
        except Exception as e:
            logger.error(f"Error generating invoice for {ri.get('recurring_invoice_id')}: {e}")
            errors.append({"recurring_invoice_id": ri.get("recurring_invoice_id"), "error": str(e)})
    
    logger.info(f"Generated {generated} invoices from recurring profiles")
    return {"generated": generated, "errors": errors}


async def generate_recurring_expenses():
    """
    Generate expenses from recurring expense profiles that are due.
    Should be run daily.
    """
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    recurring = await db.recurring_expenses.find({
        "status": "active",
        "next_expense_date": {"$lte": today}
    }, {"_id": 0}).to_list(length=500)
    
    generated = 0
    
    for re in recurring:
        try:
            expense_id = f"EXP-{uuid.uuid4().hex[:12].upper()}"
            
            expense = {
                "expense_id": expense_id,
                "vendor_id": re.get("vendor_id", ""),
                "vendor_name": re.get("vendor_name", ""),
                "account_id": re.get("account_id"),
                "account_name": re.get("account_name"),
                "date": today,
                "amount": re.get("amount", 0),
                "tax_percentage": re.get("tax_percentage", 0),
                "tax_amount": re.get("tax_amount", 0),
                "total": re.get("total", 0),
                "description": re.get("description", ""),
                "is_billable": re.get("is_billable", False),
                "customer_id": re.get("customer_id", ""),
                "project_id": re.get("project_id", ""),
                "from_recurring_expense_id": re.get("recurring_expense_id"),
                "status": "unbilled",
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await db.expenses.insert_one(expense)
            
            # Calculate next date (simplified)
            frequency = re.get("recurrence_frequency", "monthly")
            repeat_every = re.get("repeat_every", 1)
            current = datetime.strptime(re.get("next_expense_date"), "%Y-%m-%d")
            
            if frequency == "daily":
                next_date = current + timedelta(days=repeat_every)
            elif frequency == "weekly":
                next_date = current + timedelta(weeks=repeat_every)
            elif frequency == "yearly":
                next_date = current.replace(year=current.year + repeat_every)
            else:  # monthly
                next_month = current.month + repeat_every
                next_year = current.year + (next_month - 1) // 12
                next_month = ((next_month - 1) % 12) + 1
                try:
                    next_date = current.replace(year=next_year, month=next_month)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    next_date = current.replace(year=next_year, month=next_month, day=min(current.day, last_day))
            
            next_date_str = next_date.strftime("%Y-%m-%d")
            
            new_status = re.get("status")
            if re.get("end_date") and next_date_str > re.get("end_date"):
                new_status = "expired"
            
            await db.recurring_expenses.update_one(
                {"recurring_expense_id": re.get("recurring_expense_id")},
                {
                    "$set": {"next_expense_date": next_date_str, "last_expense_date": today, "status": new_status},
                    "$inc": {"expenses_generated": 1}
                }
            )
            
            generated += 1
            
        except Exception as e:
            logger.error(f"Error generating expense for {re.get('recurring_expense_id')}: {e}")
    
    logger.info(f"Generated {generated} expenses from recurring profiles")
    return {"generated": generated}


async def send_payment_reminders():
    """
    Send payment reminders for overdue invoices.
    Should be run daily.
    """
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_date = datetime.strptime(today, "%Y-%m-%d")
    
    # Find overdue invoices with balance
    overdue = await db.invoices.find({
        "status": "overdue",
        "balance": {"$gt": 0}
    }, {"_id": 0}).to_list(length=500)
    
    reminders_sent = 0
    
    for invoice in overdue:
        try:
            due_date = datetime.strptime(invoice.get("due_date", today), "%Y-%m-%d")
            days_overdue = (today_date - due_date).days
            
            # Check last reminder date to avoid spam
            last_reminder = invoice.get("last_reminder_date")
            if last_reminder:
                last_reminder_date = datetime.strptime(last_reminder, "%Y-%m-%d")
                days_since_reminder = (today_date - last_reminder_date).days
                
                # Send reminders at intervals: 1 day, 7 days, 14 days, 30 days overdue
                if days_since_reminder < 7:
                    continue
            
            # Get customer email
            customer = await db.contacts.find_one(
                {"contact_id": invoice.get("customer_id")},
                {"_id": 0, "email": 1, "contact_name": 1}
            )
            
            if not customer or not customer.get("email"):
                continue
            
            # Create reminder record
            reminder = {
                "reminder_id": f"REM-{uuid.uuid4().hex[:12].upper()}",
                "invoice_id": invoice.get("invoice_id"),
                "invoice_number": invoice.get("invoice_number"),
                "customer_id": invoice.get("customer_id"),
                "customer_name": invoice.get("customer_name"),
                "customer_email": customer.get("email"),
                "amount_due": invoice.get("balance"),
                "days_overdue": days_overdue,
                "reminder_type": "overdue",
                "status": "queued",
                "created_time": datetime.now(timezone.utc).isoformat()
            }
            
            await db.payment_reminders.insert_one(reminder)
            
            # Update invoice with reminder info
            await db.invoices.update_one(
                {"invoice_id": invoice.get("invoice_id")},
                {
                    "$set": {"last_reminder_date": today},
                    "$inc": {"reminder_count": 1}
                }
            )
            
            reminders_sent += 1
            
        except Exception as e:
            logger.error(f"Error sending reminder for invoice {invoice.get('invoice_id')}: {e}")
    
    logger.info(f"Queued {reminders_sent} payment reminders")
    return {"reminders_queued": reminders_sent}


async def run_all_scheduled_jobs():
    """Run all scheduled jobs - can be triggered via API"""
    results = {}
    
    try:
        results["overdue_invoices"] = await update_overdue_invoices()
    except Exception as e:
        results["overdue_invoices"] = {"error": str(e)}
    
    try:
        results["recurring_invoices"] = await generate_recurring_invoices()
    except Exception as e:
        results["recurring_invoices"] = {"error": str(e)}
    
    try:
        results["recurring_expenses"] = await generate_recurring_expenses()
    except Exception as e:
        results["recurring_expenses"] = {"error": str(e)}
    
    try:
        results["payment_reminders"] = await send_payment_reminders()
    except Exception as e:
        results["payment_reminders"] = {"error": str(e)}
    
    return results
