# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system/web application (Battwheels OS) with integrated AI for Electric failure intelligence which learns from failure cards of EV issues. The application features:
- Customer portal and technician portal
- Admin management with role-based access
- AI-powered "Answer Module" for EV troubleshooting

## User Personas

### 1. Admin
- Full system access
- User and role management
- System configuration
- View all reports and analytics

### 2. Technician
- Access to tickets assigned to them
- Inventory management
- Vehicle status updates
- AI diagnostic tool access

### 3. Customer
- View own vehicles and tickets
- Create new service tickets
- Access AI diagnostic assistant
- Track repair status

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

### Operations
- [x] Ticket/Complaint Management with status tracking
- [x] Vehicle Registration and Status Management
- [x] Inventory Management with low-stock alerts
- [x] AI Diagnostic Assistant powered by GPT-5.2
- [x] Alerts System

### User Management
- [x] User CRUD operations
- [x] Role assignment (admin only)
- [x] User status (active/inactive)

## What's Been Implemented (Feb 15, 2026)

### Backend (FastAPI + MongoDB)
- Complete authentication system (JWT + Google OAuth)
- User management with role-based permissions
- Vehicle CRUD operations with status tracking
- Ticket management with technician assignment
- Inventory management with stock tracking
- AI diagnosis endpoint using Emergent LLM (GPT-5.2)
- Dashboard statistics API
- Alerts system for low inventory and critical tickets
- Data seeding for demo purposes

### Frontend (React + Tailwind + Shadcn/UI)
- Dark theme UI matching Battwheels OS design
- Responsive sidebar navigation
- Login page with tabs (Login/Register)
- Dashboard with metric cards and charts (Recharts)
- Tickets management with filters and status updates
- New Ticket creation form
- Inventory management with add/edit functionality
- AI Diagnostic Assistant with category selection
- Vehicles management
- User management (admin only)
- Alerts page
- Settings page

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Recharts
- Backend: FastAPI, Motor (MongoDB async driver)
- Database: MongoDB
- AI: Emergent LLM Integration (GPT-5.2)
- Auth: JWT + Emergent Google OAuth

## Prioritized Backlog

### P0 (Completed)
- [x] Authentication (JWT + Google OAuth)
- [x] Dashboard with analytics
- [x] Ticket management
- [x] AI Diagnostic Assistant
- [x] Inventory management
- [x] Role-based access

### P1 (Next Phase)
- [ ] Email notifications for ticket updates
- [ ] Predictive maintenance alerts based on vehicle history
- [ ] Export reports (PDF/Excel)
- [ ] Mobile app optimizations

### P2 (Future)
- [ ] Payment integration for services
- [ ] Real-time chat between customer and technician
- [ ] Vehicle health monitoring integration (OBD-II)
- [ ] Multi-garage support

## Next Tasks List
1. Implement email notifications using SendGrid/Resend
2. Add predictive maintenance ML model
3. Create report export functionality
4. Add more comprehensive role permissions
5. Implement real-time updates using WebSockets
