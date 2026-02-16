# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system (Battwheels OS) with integrated AI for Electric failure intelligence. The system includes a full Enterprise ERP with legacy data migration and HR/Payroll module.

## What's Been Implemented

### Complaint Dashboard & Job Card (Feb 16, 2026) ✅ NEW
**Complaint Dashboard Features:**
- 5 KPI Cards: Open Tickets, Technician Assigned, Awaiting Approval, Work In Progress, Resolved This Week
- Clickable KPI cards for instant filtering
- Search bar filtering by ticket ID, customer name, vehicle number
- Data table with columns: ID, Customer, Vehicle, Issue, Priority, Status, Technician, Created
- Download CSV export functionality
- Pagination for large datasets

**Job Card Features:**
- Opens as a dialog when clicking any ticket
- Customer & Vehicle Details section (name, type, phone, email, vehicle number, model, type)
- Issue Details section (title, description, incident location)
- Itemized Cost Estimation (parts & services with GST)
- Status History timeline with timestamps
- Role-based Action Buttons:
  - Admin: Assign Technician (when Open)
  - Admin/Tech: Share Estimate (when Technician Assigned)
  - Customer: Approve Estimate
  - Tech: Start Work, Mark Resolved
  - Admin: Generate Invoice & Close
- Print/Download functionality

### Service Ticket Form
Comprehensive ticket submission form with sections:
1. **Vehicle Information** - Type, Model, Number
2. **Customer Details** - Type, Name, Phone, Email
3. **Complaint Specifics** - Issue Title, Type, Resolution, Priority, Description
4. **Incident Location** - Text address with map placeholder
5. **Attachments** - Multi-file upload

### HR & Payroll Module
- Attendance Management (Clock In/Out, 9hr standard)
- Leave Management (5 leave types with approval)
- Payroll Integration (auto-calculate from attendance)

### Data Migration
- ~10,000 records migrated from Zoho Books

### Core ERP Modules
- Ticket/Complaint Management
- Inventory, Suppliers, PO, Sales Orders
- Invoices, Expenses, Accounting
- AI Diagnostic Assistant (GPT-5.2)

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI
- Backend: FastAPI, Motor (MongoDB async)
- Database: MongoDB
- AI: Emergent LLM Integration

## Test Credentials
- **Admin:** admin@battwheels.in / admin123
- **Technician:** deepak@battwheelsgarages.in / tech123

## API Endpoints

### Ticket APIs
```
GET    /api/tickets           - List all tickets with filtering
GET    /api/tickets/{id}      - Get ticket details for Job Card
PUT    /api/tickets/{id}      - Update ticket status/assignment
POST   /api/tickets           - Create new ticket
GET    /api/technicians       - List technicians for assignment
GET    /api/inventory         - List parts for cost estimation
GET    /api/services          - List services for cost estimation
POST   /api/invoices          - Generate invoice from ticket
```

### Ticket Model Fields
```json
{
  "ticket_id": "string",
  "vehicle_type": "two_wheeler|three_wheeler|four_wheeler|commercial|other",
  "vehicle_model": "string",
  "vehicle_number": "string",
  "customer_type": "individual|business|fleet|dealer|rental",
  "customer_name": "string",
  "contact_number": "string",
  "customer_email": "string",
  "title": "string",
  "description": "string",
  "category": "string",
  "issue_type": "battery|motor|charging|controller|electrical|...",
  "resolution_type": "workshop|onsite|pickup|remote",
  "priority": "low|medium|high|critical",
  "status": "open|technician_assigned|estimate_shared|estimate_approved|in_progress|resolved|closed",
  "incident_location": "string",
  "estimated_items": {"parts": [], "services": []},
  "actual_items": {"parts": [], "services": []},
  "status_history": [{"status": "string", "timestamp": "ISO", "updated_by": "string"}]
}
```

## Prioritized Backlog

### P0 (Completed) ✅
- [x] ERP System with all modules
- [x] Legacy data migration
- [x] HR & Payroll module
- [x] Enhanced service ticket form
- [x] Complaint Dashboard with KPI cards
- [x] Job Card with full workflow

### P1 (Next Phase)
- [ ] Google Maps integration for location picker
- [ ] File upload to cloud storage
- [ ] Invoice PDF generation
- [ ] Email notifications
- [ ] Backend refactoring (split server.py)

### P2 (Future)
- [ ] Mobile app for field technicians
- [ ] Customer portal with estimate approval
- [ ] Real-time tracking with WebSockets
- [ ] WhatsApp/SMS notifications

## Testing
- Backend: 100% pass rate (19/19 tests)
- Frontend: All features verified working
- Test files: /app/backend/tests/test_complaint_dashboard.py
- Test reports: /app/test_reports/iteration_4.json
