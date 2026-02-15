# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system (Battwheels OS) with integrated AI for Electric failure intelligence. The system includes a full Enterprise ERP with legacy data migration and HR/Payroll module.

## What's Been Implemented (Feb 15, 2026)

### New Service Ticket Form (Updated)
Comprehensive ticket submission form with sections:
1. **Vehicle Information**
   - Vehicle Type (Two Wheeler, Three Wheeler, Four Wheeler, Commercial)
   - Vehicle Model
   - Vehicle Number (auto-uppercase)

2. **Customer Details**
   - Customer Type (Individual, Business, Fleet, Dealer, Rental)
   - Full Name
   - Contact Number (+91 prefix)
   - Email Address

3. **Complaint Specifics**
   - Issue Title
   - Issue Type (Battery, Motor, Charging, Controller, etc.)
   - Resolution Type (Workshop, On-Site, Pickup & Drop, Remote)
   - Priority (Low, Medium, High, Critical)
   - Detailed Description

4. **Incident Location**
   - Text address input
   - Search/Map integration placeholder
   - Map picker placeholder

5. **Attachments**
   - Multi-file upload (images, documents)
   - Preview for images
   - File size display

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

## New Ticket API Fields
```json
{
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
  "incident_location": "string",
  "attachments_count": 0
}
```

## Prioritized Backlog

### P0 (Completed)
- [x] ERP System with all modules
- [x] Legacy data migration
- [x] HR & Payroll module
- [x] Enhanced service ticket form

### P1 (Next Phase)
- [ ] Google Maps integration for location picker
- [ ] File upload to cloud storage
- [ ] Invoice PDF generation
- [ ] Email notifications

### P2 (Future)
- [ ] Mobile app for field technicians
- [ ] Customer portal
- [ ] Real-time tracking
