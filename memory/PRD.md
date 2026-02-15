# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system (Battwheels OS) with integrated AI for Electric failure intelligence. The system includes a full Enterprise ERP with legacy data migration and HR/Payroll module.

## What's Been Implemented (Feb 15, 2026)

### HR & Payroll Module (NEW)
- **Attendance Management**
  - Clock In/Out with real-time tracking
  - Standard work hours: 9:00 AM - 6:00 PM (9 hours)
  - Late arrival detection (>15 min after 9 AM)
  - Early departure warnings (<15 min before 6 PM)
  - Overtime calculation (hours > 9)
  - Monthly attendance summary with productivity metrics
  - Team overview for managers/admin

- **Leave Management**
  - 5 Leave Types: CL (12), SL (12), EL (15), LWP (365), CO (10)
  - Leave request workflow with manager approval
  - Leave balance tracking
  - Pending/Approved/Rejected status
  - Automatic attendance marking for approved leaves

- **Payroll Integration**
  - Auto-calculate based on attendance
  - Base salary = Hourly rate × 9 hours × working days
  - Overtime pay = 1.5× hourly rate
  - Deductions: Absence + Late penalty (₹100/day)
  - Monthly payroll generation (admin)
  - Individual payslip view

### Data Migration (Completed)
- ~10,000 records migrated from Zoho Books
- Customers, Suppliers, Inventory, Invoices, Sales/Purchase Orders, Payments, Expenses, Chart of Accounts

### Core ERP Modules
- Ticket/Complaint Management
- Inventory Management
- Supplier/Vendor Management
- Sales & Purchase Orders
- Invoices & Payments
- Accounting/Ledger
- AI Diagnostic Assistant (GPT-5.2)

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI
- Backend: FastAPI, Motor (MongoDB async)
- Database: MongoDB
- AI: Emergent LLM Integration

## Test Credentials
- **Admin:** admin@battwheels.in / admin123

## API Endpoints - HR Module
- `POST /api/attendance/clock-in` - Clock in
- `POST /api/attendance/clock-out` - Clock out with break time
- `GET /api/attendance/today` - Today's attendance
- `GET /api/attendance/my-records` - Monthly records with summary
- `GET /api/attendance/team-summary` - Team metrics (admin)
- `GET /api/leave/types` - Leave types
- `GET /api/leave/balance` - User's leave balance
- `POST /api/leave/request` - Apply for leave
- `GET /api/leave/my-requests` - User's leave requests
- `GET /api/leave/pending-approvals` - Pending approvals (admin)
- `PUT /api/leave/{id}/approve` - Approve/reject leave
- `POST /api/payroll/generate` - Generate monthly payroll (admin)
- `GET /api/payroll/records` - All payroll records (admin)
- `GET /api/payroll/my-records` - User's payslips

## Test Results (Feb 15, 2026)
- Backend: **100% (16/16 tests passed)**
- Frontend: **100% (all pages working)**
- Test file: `/app/backend/tests/test_hr_module.py`

## Prioritized Backlog

### P0 (Completed)
- [x] ERP System with all modules
- [x] Legacy data migration
- [x] Attendance tracking with clock in/out
- [x] Leave management with approval workflow
- [x] Payroll calculation and generation

### P1 (Next Phase)
- [ ] Invoice PDF generation
- [ ] Shift management (multiple shift timings)
- [ ] Biometric integration
- [ ] Email notifications for approvals

### P2 (Future)
- [ ] Payment gateway integration
- [ ] Real-time WebSocket updates
- [ ] Mobile app for attendance
- [ ] Advanced payroll features (tax, PF, ESI)
