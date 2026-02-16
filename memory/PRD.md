# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system (Battwheels OS) with integrated AI for Electric failure intelligence. The system includes a full Enterprise ERP with legacy data migration, HR/Payroll module, and a comprehensive technical specification for production deployment.

## What's Been Implemented

### Technical Specification Document (Feb 16, 2026) ✅ NEW
Comprehensive 100KB+ architecture document at `/app/docs/TECHNICAL_SPEC.md` covering:
- **System Architecture**: Microservices topology, data layer design
- **Failure Intelligence Pipeline**: AI-assisted matching, failure card structure
- **Integration Layer**: Service adapters, event-driven patterns
- **Scalability Design**: Database sharding, caching layers
- **AI/ML Models**: Symptom classifier, root cause analyzer, solution ranker
- **Data Synchronization**: Cross-location sync, conflict resolution
- **Security & Governance**: RBAC, encryption, audit trails
- **Continuous Improvement**: Feedback loops, effectiveness metrics
- **Operational Considerations**: Deployment, monitoring, DR

### Invoice PDF Generation (Feb 16, 2026) ✅ NEW
GST-compliant tax invoice matching Battwheels Services template:
- **Company Header**: Battwheels Services Private Limited, GSTIN: 07AAMCB4976D1ZG
- **GST Breakdown**: IGST for inter-state, CGST/SGST for intra-state
- **Itemized Billing**: HSN/SAC codes, quantity, rate, tax amounts
- **Bank Details**: KOTAK MAHINDRA BANK, Account: 0648556556, IFSC: KKBK0004635
- **QR Code**: UPI payment link for easy payment
- **Total in Words**: Indian numbering system (Lakh, Crore)

### Notification Service (Feb 16, 2026) ✅ NEW
Email and WhatsApp notifications for ticket lifecycle:
- **Email Templates**: ticket_created, ticket_assigned, estimate_shared, invoice_generated, ticket_resolved
- **WhatsApp Templates**: Same events with formatted messages
- **Background Processing**: Non-blocking async sending
- **Logging**: Full notification audit trail
- **Note**: MOCKED - Needs RESEND_API_KEY and TWILIO credentials to send actual messages

### Employee Management Module (Feb 16, 2026)
Comprehensive employee onboarding with India compliance:
- Personal, Employment, Salary, Compliance, Bank details
- Auto-calculated deductions: PF (12%), ESI (0.75%), Professional Tax, TDS
- Role-based access: Admin, Manager, Technician, Accountant, Customer Support

### Previous Implementations
- Complaint Dashboard & Job Card (Feb 16, 2026)
- Service Ticket Form
- HR & Payroll (Attendance, Leave, Payroll)
- Data Migration (~10,000 records)
- Core ERP (Inventory, Suppliers, PO, Sales, Invoices, Accounting)
- AI Diagnostic Assistant (GPT-5.2)

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI
- Backend: FastAPI, Motor (MongoDB async)
- Database: MongoDB
- AI: Emergent LLM Integration
- PDF: ReportLab, QRCode
- Notifications: Resend (Email), Twilio (WhatsApp)

## Test Credentials
- **Admin:** admin@battwheels.in / admin123
- **Technician:** deepak@battwheelsgarages.in / tech123
- **Test Employee:** test.employee@battwheels.in / test123

## API Endpoints

### Invoice APIs
```
GET    /api/invoices              - List all invoices
POST   /api/invoices              - Create invoice from ticket
GET    /api/invoices/{id}         - Get invoice details
GET    /api/invoices/{id}/pdf     - Download GST-compliant PDF
PUT    /api/invoices/{id}         - Update invoice status
```

### Notification APIs
```
POST   /api/notifications/send-email           - Send email notification
POST   /api/notifications/send-whatsapp        - Send WhatsApp notification
POST   /api/notifications/ticket-notification/{id} - Auto-send for ticket events
GET    /api/notifications/logs                 - Get notification logs
GET    /api/notifications/stats                - Get notification statistics
```

## Directory Structure
```
/app/
├── backend/
│   ├── services/
│   │   ├── invoice_service.py    # PDF generation
│   │   └── notification_service.py # Email/WhatsApp
│   ├── routes/
│   │   └── auth.py               # Auth routes (refactored)
│   ├── models/
│   ├── utils/
│   ├── migration/
│   │   └── legacy_migrator.py
│   ├── tests/
│   │   ├── test_employee_module.py
│   │   └── test_invoice_notification.py
│   └── server.py                 # Main API (4100+ lines)
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Employees.jsx     # Employee management
│       │   ├── Tickets.jsx       # Complaint dashboard
│       │   └── ...
│       └── components/
│           └── JobCard.jsx
├── docs/
│   └── TECHNICAL_SPEC.md         # Architecture doc (100KB+)
└── memory/
    └── PRD.md                    # This file
```

## Prioritized Backlog

### P0 (Completed) ✅
- [x] ERP System with all modules
- [x] Legacy data migration
- [x] HR & Payroll module
- [x] Complaint Dashboard with Job Card
- [x] Employee Management with India compliance
- [x] Technical Specification document
- [x] Invoice PDF generation (GST compliant)
- [x] Notification service (Email/WhatsApp)

### P1 (Next Phase)
- [ ] Configure Resend API key for email sending
- [ ] Configure Twilio for WhatsApp notifications
- [ ] Backend refactoring (split server.py into modules)
- [ ] Google Maps integration for location picker
- [ ] File upload to cloud storage

### P2 (Future)
- [ ] Mobile app for field technicians
- [ ] Customer portal with estimate approval
- [ ] Real-time tracking with WebSockets
- [ ] Failure Intelligence Engine (from tech spec)
- [ ] AI-assisted matching (from tech spec)

## Testing
- Employee Module: 100% pass rate (21/21 tests)
- Invoice/Notification: 100% pass rate (21/21 tests)
- Test files: /app/backend/tests/
- Test reports: /app/test_reports/iteration_6.json

## Environment Variables Needed
```env
# Backend (.env)
MONGO_URL=<configured>
DB_NAME=<configured>
JWT_SECRET=<configured>

# For Notifications (OPTIONAL - service works without but skips sending)
RESEND_API_KEY=re_xxxxx
SENDER_EMAIL=onboarding@resend.dev
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```
