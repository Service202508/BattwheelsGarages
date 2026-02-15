# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system/web application (Battwheels OS) with integrated AI for Electric failure intelligence which learns from failure cards of EV issues. The application features:
- Customer portal and technician portal
- Admin management with role-based access
- AI-powered "Answer Module" for EV troubleshooting
- **Full Enterprise ERP System** with 5 integrated modules

## User Personas

### 1. Admin
- Full system access
- User and role management
- System configuration
- View all reports and analytics
- PO/Invoice approval authority
- Financial oversight

### 2. Technician
- Access to tickets assigned to them
- Inventory management
- Vehicle status updates
- AI diagnostic tool access
- Material allocation for repairs

### 3. Customer
- View own vehicles and tickets
- Create new service tickets
- Access AI diagnostic assistant
- Track repair status
- View invoices

## Core Requirements (Static)

### Authentication
- [x] JWT-based email/password login
- [x] Google OAuth via Emergent Auth
- [x] Role-based access control (admin, technician, customer)
- [x] Session management with secure cookies

### Dashboard
- [x] KPI Metrics: Vehicles in Workshop, Open Repair Orders, Avg Repair Time, Available Technicians
- [x] Vehicle Status Distribution (Donut Chart)
- [x] Repair Time Trend (Bar Chart)
- [x] Workshop Overview / Receivables Overview tabs
- [x] Financial metrics (Revenue, Pending Invoices, Inventory Value)

### Operations
- [x] Ticket/Complaint Management with status tracking
- [x] Vehicle Registration and Status Management
- [x] Inventory Management with low-stock alerts
- [x] AI Diagnostic Assistant powered by GPT-5.2
- [x] Alerts System (Critical tickets, Low inventory, Overdue invoices, Pending approvals)

### ERP Modules (Phase 2 - Completed)
- [x] **Inventory Management** - Stock tracking, material allocation, supplier linking, reorder levels
- [x] **Purchase Orders** - Vendor management, PO creation, multi-stage approval, stock receiving
- [x] **Sales Orders** - Service offerings, parts allocation, labor charges, multi-stage approval
- [x] **Invoices** - Invoice generation from tickets, payment tracking, multiple payment methods
- [x] **Accounting** - General ledger, revenue/expense tracking, accounts receivable/payable

## What's Been Implemented (Feb 15, 2026)

### Backend (FastAPI + MongoDB)
- Complete authentication system (JWT + Google OAuth)
- User management with role-based permissions
- Vehicle CRUD operations with status tracking
- Ticket management with technician assignment
- **Comprehensive ERP System:**
  - Inventory Management with reserved quantities
  - Supplier/Vendor Management
  - Material Allocation to Tickets
  - Purchase Order workflow with approval
  - Stock Receiving functionality
  - Service Offerings management
  - Sales Order creation with pricing
  - Invoice generation with GST (18%)
  - Payment recording (Cash, Card, UPI, Bank Transfer)
  - General Ledger for audit trail
  - Accounting summaries (Revenue, Expenses, Receivables, Payables)
- AI diagnosis endpoint using Emergent LLM (GPT-5.2)
- Dashboard statistics API with financial metrics
- Alerts system for low inventory, critical tickets, overdue invoices

### Frontend (React + Tailwind + Shadcn/UI)
- Dark theme UI matching Battwheels OS design
- Responsive sidebar navigation with categorized sections
- Login page with tabs (Login/Register)
- Dashboard with metric cards and charts (Recharts)
- Tickets management with filters and status updates
- New Ticket creation form
- **ERP Module Pages:**
  - Inventory Management with Add/Edit items, stock status badges
  - Supplier Management with contact details, ratings
  - Purchase Orders with PO creation dialog
  - Sales Orders with service/parts pricing
  - Invoices with payment recording dialog
  - Accounting with financial charts and General Ledger
- AI Diagnostic Assistant with category selection
- Vehicles management
- User management (admin only)
- Alerts page with categorized alerts

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Recharts
- Backend: FastAPI, Motor (MongoDB async driver)
- Database: MongoDB
- AI: Emergent LLM Integration (GPT-5.2)
- Auth: JWT + Emergent Google OAuth

## Test Credentials
- **Admin:** admin@battwheels.in / admin123
- **Technician:** deepak@battwheelsgarages.in / tech123

## Seeded Data
- 4 Users (1 Admin, 3 Technicians)
- 3 Suppliers (EV Parts India, BatteryWorld, AutoTools Pro)
- 6+ Inventory Items (Battery packs, Motors, Charging equipment, etc.)
- 5 Service Offerings (Battery Health Check, Motor Service, Full EV Service, etc.)

## Test Results (Feb 15, 2026)
- Backend: **100% (22/22 tests passed)**
- Frontend: **100% (all pages load correctly)**
- Test file: `/app/backend/tests/test_erp_api.py`

## Prioritized Backlog

### P0 (Completed)
- [x] Authentication (JWT + Google OAuth)
- [x] Dashboard with analytics
- [x] Ticket management
- [x] AI Diagnostic Assistant
- [x] Inventory management
- [x] Role-based access
- [x] Supplier/Vendor Management
- [x] Purchase Order System
- [x] Sales Order System
- [x] Invoice & Payment System
- [x] Accounting/Ledger System

### P1 (Next Phase)
- [ ] Email notifications for ticket updates
- [ ] Predictive maintenance alerts based on vehicle history
- [ ] Export reports (PDF/Excel)
- [ ] Invoice PDF generation
- [ ] Customer & Technician portal views

### P2 (Future)
- [ ] Payment gateway integration (Stripe/Razorpay)
- [ ] Real-time chat between customer and technician
- [ ] Vehicle health monitoring integration (OBD-II)
- [ ] Multi-garage support
- [ ] Refactor backend into modular APIRouter structure

## API Endpoints Summary

### Auth
- POST `/api/auth/register` - User registration
- POST `/api/auth/login` - JWT login
- POST `/api/auth/session` - Google OAuth session
- GET `/api/auth/me` - Get current user
- POST `/api/auth/logout` - Logout

### Users
- GET `/api/users` - List users (admin only)
- GET `/api/users/{id}` - Get user
- PUT `/api/users/{id}` - Update user
- GET `/api/technicians` - List technicians

### Vehicles & Tickets
- CRUD `/api/vehicles`
- CRUD `/api/tickets`

### ERP - Inventory
- CRUD `/api/inventory`
- POST `/api/allocations` - Material allocation
- PUT `/api/allocations/{id}/use` - Mark as used
- PUT `/api/allocations/{id}/return` - Return materials

### ERP - Procurement
- CRUD `/api/suppliers`
- CRUD `/api/purchase-orders`
- POST `/api/purchase-orders/{id}/receive` - Stock receiving

### ERP - Sales & Finance
- CRUD `/api/services`
- CRUD `/api/sales-orders`
- CRUD `/api/invoices`
- POST `/api/payments` - Record payment
- GET `/api/ledger` - General ledger
- GET `/api/accounting/summary` - Financial summary
- GET `/api/accounting/ticket/{id}` - Ticket financials

### Other
- GET `/api/dashboard/stats` - Dashboard metrics
- GET `/api/alerts` - System alerts
- POST `/api/ai/diagnose` - AI diagnosis
- POST `/api/seed` - Seed initial data
- POST `/api/reseed` - Reseed missing data
