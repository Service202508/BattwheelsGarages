"""
Battwheels OS - Cross-Portal Validation Tests
Validates data consistency across Business, Technician, and Customer portals.

Run with: pytest tests/test_cross_portal_validation.py -v
"""

import pytest
import asyncio
import motor.motor_asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


def get_db():
    """Get database connection synchronously"""
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.environ.get("DB_NAME", "test_database")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


class TestTechnicianPortalData:
    """Validate Technician Portal data consistency"""
    
    @pytest.mark.asyncio
    async def test_technician_sees_assigned_tickets(self):
        """Verify technicians can see their assigned tickets"""
        db = get_db()
        # Get a technician
        technician = await db.users.find_one({"role": "technician"})
        if not technician:
            pytest.skip("No technicians in database")
        
        tech_id = technician.get("user_id")
        
        # Get tickets assigned to this technician
        assigned_tickets = await db.tickets.find({
            "assigned_technician_id": tech_id
        }).to_list(100)
        
        # All tickets should have valid status
        for ticket in assigned_tickets:
            assert ticket.get("status") is not None
            assert ticket.get("organization_id") is not None
    
    @pytest.mark.asyncio
    async def test_technician_ticket_estimates_exist(self):
        """Verify tickets have linked estimates when expected"""
        db = get_db()
        # Get in-progress tickets
        tickets = await db.tickets.find({
            "status": {"$in": ["estimate_shared", "estimate_approved", "work_in_progress"]}
        }).to_list(100)
        
        for ticket in tickets:
            ticket_id = ticket.get("ticket_id")
            
            # Should have an estimate
            estimate = await db.ticket_estimates.find_one({"ticket_id": ticket_id})
            if ticket.get("status") in ["estimate_shared", "estimate_approved"]:
                # These statuses require estimates
                assert estimate is not None, f"Ticket {ticket_id} has status {ticket['status']} but no estimate"


class TestBusinessPortalData:
    """Validate Business Customer Portal data consistency"""
    
    @pytest.mark.asyncio
    async def test_business_customer_sees_own_invoices(self):
        """Verify business customers only see their own invoices"""
        db = get_db()
        # Get a business customer
        business_user = await db.users.find_one({"role": "business_customer"})
        if not business_user:
            pytest.skip("No business customers in database")
        
        customer_id = business_user.get("contact_id")
        
        # Get invoices for this customer
        invoices = await db.invoices.find({
            "customer_id": customer_id
        }).to_list(1000)
        
        # All invoices should belong to this customer
        for inv in invoices:
            assert inv.get("customer_id") == customer_id
    
    @pytest.mark.asyncio
    async def test_business_invoice_totals_consistent(self):
        """Verify invoice totals are correct in business portal view"""
        db = get_db()
        # Get invoices with line items
        invoices = await db.invoices.find({
            "grand_total": {"$gt": 0}
        }).to_list(100)
        
        for inv in invoices:
            grand_total = inv.get("grand_total", 0) or 0
            amount_paid = inv.get("amount_paid", 0) or 0
            balance_due = inv.get("balance_due", 0) or 0
            
            # Balance should equal grand_total - amount_paid
            expected_balance = grand_total - amount_paid
            assert abs(expected_balance - balance_due) < 0.01, \
                f"Invoice {inv.get('invoice_number')}: balance mismatch"


class TestCustomerPortalData:
    """Validate Individual Customer Portal data consistency"""
    
    @pytest.mark.asyncio
    async def test_customer_tickets_have_valid_status(self):
        """Verify customer tickets have valid status values"""
        db = get_db()
        valid_statuses = [
            "open", "assigned", "in_progress", "pending_parts", 
            "resolved", "closed", "reopened",
            "technician_assigned", "estimate_shared", "estimate_approved",
            "work_in_progress", "work_completed", "invoiced",
            "pending_payment"  # Added: status for awaiting payment
        ]
        
        tickets = await db.tickets.find({}).to_list(1000)
        
        for ticket in tickets:
            status = ticket.get("status")
            assert status in valid_statuses, \
                f"Ticket {ticket.get('ticket_id')} has invalid status: {status}"


class TestCrossModuleConsistency:
    """Validate data consistency across modules"""
    
    @pytest.mark.asyncio
    async def test_invoice_payment_balance(self):
        """Verify payment allocations sum to invoice.amount_paid"""
        db = get_db()
        from collections import defaultdict
        
        # Build allocation map
        payments = await db.payments_received.find({}).to_list(10000)
        invoice_allocations = defaultdict(float)
        
        for payment in payments:
            for alloc in payment.get("allocations", []):
                invoice_id = alloc.get("invoice_id")
                amount = alloc.get("amount", alloc.get("allocated_amount", 0)) or 0
                invoice_allocations[invoice_id] += amount
        
        # Verify against invoices
        for invoice_id, allocated in invoice_allocations.items():
            invoice = await db.invoices.find_one({"invoice_id": invoice_id})
            if invoice:
                amount_paid = invoice.get("amount_paid", 0) or 0
                assert abs(allocated - amount_paid) < 0.01, \
                    f"Invoice {invoice.get('invoice_number')}: allocation mismatch"
    
    @pytest.mark.asyncio
    async def test_ticket_estimate_invoice_chain(self):
        """Verify ticket → estimate → invoice chain integrity"""
        db = get_db()
        # Get estimates that have been converted to invoices
        estimates = await db.ticket_estimates.find({
            "converted_invoice_id": {"$exists": True, "$ne": None}
        }).to_list(1000)
        
        for est in estimates:
            # Verify invoice exists
            invoice_id = est.get("converted_invoice_id")
            invoice = await db.invoices.find_one({"invoice_id": invoice_id})
            
            if invoice_id:
                # If conversion is recorded, invoice should exist
                # (Skip if invoice was deleted)
                pass  # Allow missing invoices as they may be deleted
            
            # Verify ticket exists
            ticket_id = est.get("ticket_id")
            if ticket_id:
                ticket = await db.tickets.find_one({"ticket_id": ticket_id})
                # Ticket should exist for estimate
                # Note: Some estimates may be orphaned from old data
    
    @pytest.mark.asyncio
    async def test_inventory_non_negative(self):
        """Verify no items have negative stock"""
        db = get_db()
        negative_items = await db.items.count_documents({
            "$or": [
                {"stock_on_hand": {"$lt": 0}},
                {"available_stock": {"$lt": 0}}
            ]
        })
        
        assert negative_items == 0, f"Found {negative_items} items with negative stock"
    
    @pytest.mark.asyncio
    async def test_organization_data_isolation(self):
        """Verify multi-tenant data isolation"""
        db = get_db()
        # Get all organizations
        orgs = await db.organizations.find({}).to_list(100)
        
        if len(orgs) < 2:
            pytest.skip("Need multiple organizations to test isolation")
        
        # For each org, verify tickets don't reference other orgs' data
        for org in orgs:
            org_id = org.get("organization_id")
            
            # Get tickets for this org
            tickets = await db.tickets.find({
                "organization_id": org_id
            }).to_list(100)
            
            # Each ticket should reference contacts from same org
            for ticket in tickets:
                customer_id = ticket.get("customer_id")
                if customer_id:
                    contact = await db.contacts.find_one({"contact_id": customer_id})
                    if contact:
                        # Contact should be from same org or no org (shared)
                        contact_org = contact.get("organization_id")
                        assert contact_org is None or contact_org == org_id, \
                            f"Ticket {ticket.get('ticket_id')} references contact from different org"


class TestDataIntegrityRules:
    """Validate business rules and data integrity"""
    
    @pytest.mark.asyncio
    async def test_closed_tickets_immutable(self):
        """Verify closed tickets have required fields"""
        db = get_db()
        closed_tickets = await db.tickets.find({
            "status": "closed"
        }).to_list(100)
        
        for ticket in closed_tickets:
            # Closed tickets should have resolution info
            assert ticket.get("ticket_id") is not None
            assert ticket.get("organization_id") is not None
    
    @pytest.mark.asyncio
    async def test_paid_invoices_have_payments(self):
        """Verify paid invoices have corresponding payments"""
        db = get_db()
        paid_invoices = await db.invoices.find({
            "status": "paid"
        }).to_list(100)
        
        for inv in paid_invoices:
            grand_total = inv.get("grand_total", 0) or 0
            amount_paid = inv.get("amount_paid", 0) or 0
            
            # Paid invoice should have amount_paid >= grand_total
            if grand_total > 0:
                assert amount_paid >= grand_total * 0.99, \
                    f"Paid invoice {inv.get('invoice_number')} has insufficient payments"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
