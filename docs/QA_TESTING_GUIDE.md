# QA Testing Guide — Battwheels OS
## Pre-Founder Manual QA Checklist

---

## Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Demo Owner | demo@voltmotors.in | Demo@12345 |
| Platform Admin | platform-admin@battwheels.in | DevTest@123 |
| Technician | tech.a@battwheels.internal | TechA@123 |
| Org Admin | admin@battwheels.in | DevTest@123 |

**Application URL:** Use the preview URL from frontend/.env (`REACT_APP_BACKEND_URL`)

---

## Module-by-Module Test Checklist

### 1. Authentication & Login
- [ ] Login with demo@voltmotors.in
- [ ] Login with invalid credentials (should show error)
- [ ] Verify JWT token refresh / session persistence
- [ ] Logout and verify redirect to login page

### 2. Tickets
- [ ] Create a new ticket with vehicle details
- [ ] Assign ticket to a technician
- [ ] Start work, complete work, close ticket
- [ ] Verify EFI diagnostic suggestions appear
- [ ] Check ticket appears in ticket list with correct status

### 3. Estimates
- [ ] Create a new estimate for a customer
- [ ] Add line items with quantities and rates
- [ ] Convert estimate to invoice
- [ ] Verify estimate shows in estimate list
- [ ] Test estimate PDF generation

### 4. Invoices
- [ ] Create a new invoice with line items
- [ ] Apply GST (CGST/SGST/IGST based on state)
- [ ] Record payment against invoice
- [ ] Verify invoice status changes (draft -> sent -> paid)
- [ ] Test invoice PDF generation

### 5. Contacts / Customers
- [ ] Create a new customer contact
- [ ] Search for existing contacts
- [ ] View customer transaction history
- [ ] Update contact details

### 6. Inventory / Items
- [ ] Create a new inventory item
- [ ] Adjust stock levels
- [ ] Create composite items
- [ ] Check stock valuation report
- [ ] Verify low-stock alerts (if applicable)

### 7. Projects
- [ ] Create a new project
- [ ] Assign tasks to team members
- [ ] Log hours against project
- [ ] Check project dashboard for progress

### 8. Sales Orders
- [ ] Create a sales order
- [ ] Confirm the order
- [ ] Convert to invoice
- [ ] Void an order
- [ ] Check summary/reports

### 9. AMC (Annual Maintenance Contracts)
- [ ] Create an AMC plan
- [ ] Subscribe a customer to the plan
- [ ] Record service usage
- [ ] Check AMC analytics dashboard

### 10. Time Tracking
- [ ] Create a manual time entry
- [ ] Start/stop a timer
- [ ] View unbilled hours
- [ ] Check time summary report

### 11. Reports
- [ ] View Profit & Loss report
- [ ] View Balance Sheet
- [ ] View AR/AP Aging reports
- [ ] Check Sales by Customer
- [ ] View Technician Performance

### 12. GST Compliance
- [ ] View GST summary
- [ ] Check GSTR-3B data
- [ ] Verify HSN summary
- [ ] Test e-invoice generation (if configured)

### 13. HR & Payroll
- [ ] View employee list
- [ ] Check attendance records
- [ ] View payroll calculations
- [ ] Test leave management

### 14. EFI (Electric Failure Intelligence)
- [ ] Browse failure cards
- [ ] Check diagnostic guidance for a ticket
- [ ] View failure analytics/intelligence
- [ ] Verify knowledge brain articles

### 15. Customer Portal (External)
- [ ] Login with a portal token
- [ ] View invoices from customer perspective
- [ ] View estimates and accept/reject
- [ ] Submit a support request
- [ ] Logout from portal

### 16. Technician Portal
- [ ] Login as technician
- [ ] View assigned tickets
- [ ] Check in / check out attendance
- [ ] Submit a leave request
- [ ] View productivity metrics

### 17. Platform Admin
- [ ] Login as platform admin
- [ ] View all organizations list
- [ ] Check platform metrics (total orgs, users, revenue)
- [ ] Manage feature flags
- [ ] View revenue health dashboard

---

## Known Limitations

| Area | Status | Notes |
|------|--------|-------|
| WhatsApp Notifications | MOCKED | Twilio not configured; notifications log only |
| E-Invoice (IRP) | PLACEHOLDER | IRP integration is stubbed |
| Razorpay Payments | TEST MODE | Using test keys, no real transactions |
| Zendesk Integration | STUBBED | ZendeskBridge is a stub in expert_queue_service |
| Form16 Generation | NOT IMPLEMENTED | Endpoint does not exist |
| Advanced Reports | ENTITLEMENT-GATED | Requires professional/enterprise plan |

---

## How to Report Issues

1. **Screenshot** the issue with the URL visible
2. **Note** the exact steps to reproduce
3. **Include** the user role you were logged in as
4. **Check** the browser console (F12) for any errors
5. **Report** with: Module > Action > Expected vs Actual

---

## Automated Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total backend endpoints | 1,181 |
| Tests passing | 906 |
| Tests skipped (external deps) | 13 |
| Tests failed | 0 |
| Modules with comprehensive tests | 18 |

---

*Generated: 2026-03-01 | Phase 2 Cluster 4 Part 2*
