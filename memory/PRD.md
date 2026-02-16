# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system (Battwheels OS) with integrated AI for Electric failure intelligence. The system includes a full Enterprise ERP with legacy data migration and HR/Payroll module.

## What's Been Implemented

### Employee Management Module (Feb 16, 2026) ✅ NEW
Comprehensive employee onboarding and management with India compliance:

**Personal Information:**
- Name, DOB, Gender, Phone, Personal Email
- Current/Permanent Address (City, State, Pincode)
- Emergency Contact (Name, Phone, Relation)

**Employment Details:**
- Auto-generated Employee Code (EMP0001, EMP0002...)
- Work Email, Department, Designation
- Employment Type (Full-time, Part-time, Contract, Intern, Probation)
- Joining Date, Shift, Reporting Manager

**Salary Structure (Monthly):**
- Earnings: Basic, HRA, DA, Conveyance, Medical, Special Allowance
- Auto-calculated Gross Salary
- Deductions: PF (12%), ESI (0.75%), Professional Tax, TDS
- Auto-calculated Net Salary

**India Compliance:**
- PAN Number, Aadhaar Number
- PF Number, UAN (when enrolled)
- ESI Number (when enrolled)

**Bank Details:**
- Bank Name, Account Number, IFSC Code, Branch

**Role-Based Access:**
- Admin: Full access to all modules
- Manager: HR + Reports access
- Technician: Tickets + Job Cards access
- Accountant: Finance modules only
- Customer Support: Tickets only

**Features:**
- User account auto-created with password
- Leave balance auto-initialized
- Soft delete (deactivates user account)
- Search, filter by department/status

### Complaint Dashboard & Job Card (Feb 16, 2026)
- 5 KPI Cards with clickable filtering
- Data table with search and pagination
- Job Card dialog with full ticket workflow
- Role-based action buttons

### Previous Implementations
- Service Ticket Form (comprehensive)
- HR & Payroll (Attendance, Leave, Payroll)
- Data Migration (~10,000 records)
- Core ERP (Inventory, Suppliers, PO, Sales, Invoices, Accounting)
- AI Diagnostic Assistant (GPT-5.2)

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI
- Backend: FastAPI, Motor (MongoDB async)
- Database: MongoDB
- AI: Emergent LLM Integration

## Test Credentials
- **Admin:** admin@battwheels.in / admin123
- **Technician:** deepak@battwheelsgarages.in / tech123
- **Test Employee:** test.employee@battwheels.in / test123

## API Endpoints

### Employee APIs
```
GET    /api/employees              - List all employees (filters: department, status)
GET    /api/employees/{id}         - Get employee details
POST   /api/employees              - Create employee with user account
PUT    /api/employees/{id}         - Update employee
DELETE /api/employees/{id}         - Soft delete (deactivate)
GET    /api/employees/managers/list - List managers for dropdown
GET    /api/employees/roles/list    - List available roles
```

### Salary Calculation Logic
```python
# Gross = Basic + HRA + DA + Conveyance + Medical + Special + Other
# PF = 12% of Basic (if enrolled)
# ESI = 0.75% of Gross (if enrolled AND Gross <= 21000)
# Professional Tax = 200 (if Gross > 15000), 150 (if > 10000)
# TDS = Based on annual salary slabs (5% - 30%)
# Net = Gross - PF - ESI - Professional Tax - TDS
```

## Prioritized Backlog

### P0 (Completed) ✅
- [x] ERP System with all modules
- [x] Legacy data migration
- [x] HR & Payroll module (Attendance, Leave, Payroll)
- [x] Enhanced service ticket form
- [x] Complaint Dashboard with KPI cards
- [x] Job Card with full workflow
- [x] Employee Management with India compliance

### P1 (Next Phase)
- [ ] Backend refactoring (split server.py into modules)
- [ ] Google Maps integration for location picker
- [ ] Invoice PDF generation
- [ ] Email notifications on status changes

### P2 (Future)
- [ ] Mobile app for field technicians
- [ ] Customer portal with estimate approval
- [ ] Real-time tracking with WebSockets
- [ ] WhatsApp/SMS notifications
- [ ] Employee document uploads (ID proofs)

## Testing
- Employee Module: 100% pass rate (21/21 tests)
- Complaint Dashboard: 100% pass rate (19/19 tests)
- Test files: /app/backend/tests/
- Test reports: /app/test_reports/iteration_5.json
