# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality. The system should provide comprehensive business management capabilities including:
- Customer and vendor management
- Quotes/Estimates with full lifecycle management
- Invoicing and billing
- Inventory management
- HR and payroll
- EV-specific failure intelligence diagnostics

---

## Current Implementation Status

### ✅ Completed Features

#### Core ERP Modules
- **Dashboard**: Real-time metrics, charts, and KPIs
- **Contacts Management**: Unified customer/vendor management with GST validation
- **Items/Inventory**: Product catalog with HSN codes, pricing, stock tracking
- **Estimates/Quotes**: Full Zoho-style workflow (see Phase 1 below)
- **Sales Orders**: Order management with fulfillment tracking
- **Invoices**: GST-compliant invoicing with payment tracking
- **Bills**: Vendor bill management
- **Purchase Orders**: Procurement workflow
- **Banking**: Account management and reconciliation
- **Reports**: Financial and operational reporting
- **GST Compliance**: Tax filing and reconciliation

#### HR & Operations
- **Employees**: Staff management
- **Attendance**: Time tracking
- **Leave Management**: PTO system
- **Payroll**: Salary processing
- **Technician Productivity**: Performance metrics

#### EV-Specific Features
- **EV Failure Intelligence (EFI)**: AI-powered diagnostic decision trees
- **Fault Tree Import**: Excel-based diagnostic path import
- **Failure Intelligence**: Pattern recognition and analysis
- **Vehicles**: EV fleet management
- **AMC Management**: Annual maintenance contracts

#### Platform Features
- **Authentication**: JWT + Google OAuth via Emergent
- **Customer Portal**: Self-service for customers
- **Zoho Sync**: Two-way data synchronization
- **Activity Logs**: Audit trail
- **Multi-user Support**: Role-based access (admin, technician, manager, customer)

---

## Quotes/Estimates Module - Zoho Books Enhancement

### Phase 1: Core Infrastructure ✅ COMPLETED (Feb 18, 2026)

#### Implemented Features:

**1. Attachments System**
- Upload up to 3 files per estimate (10MB max each)
- Supported formats: PDF, images, Word, Excel, text, CSV
- File stored in MongoDB as Base64
- Endpoints:
  - `POST /api/estimates-enhanced/{id}/attachments` - Upload
  - `GET /api/estimates-enhanced/{id}/attachments` - List
  - `GET /api/estimates-enhanced/{id}/attachments/{attachment_id}` - Download
  - `DELETE /api/estimates-enhanced/{id}/attachments/{attachment_id}` - Delete

**2. Public Share Link**
- Generate secure shareable URLs for customers
- Configurable options:
  - Expiry period (default 30 days)
  - Password protection (optional)
  - Allow/disallow customer accept
  - Allow/disallow customer decline
- Endpoints:
  - `POST /api/estimates-enhanced/{id}/share` - Create share link
  - `GET /api/estimates-enhanced/{id}/share-links` - List active links
  - `DELETE /api/estimates-enhanced/{id}/share/{share_link_id}` - Revoke

**3. Customer Viewed Status**
- New status in workflow: `customer_viewed`
- Auto-updates when customer opens estimate via public link
- Tracks first view timestamp
- Status flow: draft → sent → customer_viewed → accepted/declined → converted

**4. PDF Generation**
- Professional HTML template with Battwheels branding
- Full estimate details including line items, taxes, totals
- Falls back to HTML for client-side printing if WeasyPrint unavailable
- Endpoints:
  - `GET /api/estimates-enhanced/{id}/pdf` - Download PDF
  - `GET /api/estimates-enhanced/{id}/preview-html` - Get HTML for preview

**5. Public Quote View Page**
- New route: `/quote/:shareToken`
- No authentication required
- Shows:
  - Professional estimate display
  - Customer info, dates, line items
  - Accept/Decline buttons (when allowed)
  - Download PDF button
  - Attachments list with download

**6. Preferences System**
- Automation settings for estimate workflow
- Configurable options:
  - Auto-convert accepted estimates to invoice/sales order
  - Auto-send converted documents
  - Notification settings
- Endpoint: `GET/PUT /api/estimates-enhanced/preferences`

---

### Phase 2: Workflow & Automation (Upcoming)
- [ ] Un-mock email service (Resend integration)
- [ ] Automatic invoice conversion on acceptance
- [ ] PDF template selection
- [ ] Email notifications for status changes

### Phase 3: Usability & Data Management (Future)
- [ ] Import/Export (CSV/XLS)
- [ ] Custom fields management
- [ ] Bulk actions (multi-select status update)
- [ ] Enhanced notification system

---

## API Endpoints Reference

### Estimates Enhanced
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/estimates-enhanced/ | List estimates |
| POST | /api/estimates-enhanced/ | Create estimate |
| GET | /api/estimates-enhanced/{id} | Get estimate detail |
| PUT | /api/estimates-enhanced/{id} | Update estimate |
| DELETE | /api/estimates-enhanced/{id} | Delete estimate |
| PUT | /api/estimates-enhanced/{id}/status | Update status |
| POST | /api/estimates-enhanced/{id}/share | Create share link |
| GET | /api/estimates-enhanced/{id}/share-links | List share links |
| DELETE | /api/estimates-enhanced/{id}/share/{link_id} | Revoke share link |
| POST | /api/estimates-enhanced/{id}/attachments | Upload attachment |
| GET | /api/estimates-enhanced/{id}/attachments | List attachments |
| GET | /api/estimates-enhanced/{id}/attachments/{att_id} | Download |
| DELETE | /api/estimates-enhanced/{id}/attachments/{att_id} | Delete |
| GET | /api/estimates-enhanced/{id}/pdf | Download PDF |
| GET | /api/estimates-enhanced/public/{shareToken} | Public view |
| POST | /api/estimates-enhanced/public/{shareToken}/action | Accept/Decline |
| GET | /api/estimates-enhanced/preferences | Get preferences |
| PUT | /api/estimates-enhanced/preferences | Update preferences |

---

## Technical Stack

- **Frontend**: React, TailwindCSS, Shadcn/UI, Recharts
- **Backend**: FastAPI, Pydantic, Motor (async MongoDB)
- **Database**: MongoDB
- **Auth**: JWT + Emergent-managed Google OAuth
- **AI**: Gemini (via Emergent LLM Key) for EFI semantic analysis

---

## Mocked Integrations
- **Email (Resend)**: Mocked - logs to console
- **PDF (WeasyPrint)**: Falls back to HTML
- **Payment (Razorpay)**: Mocked

---

## Test Credentials
- **Admin**: admin@battwheels.in / admin123
- **Technician**: deepak@battwheelsgarages.in / tech123

---

## Recent Test Reports
- `/app/test_reports/iteration_33.json` - Phase 1 Estimates (100% pass)
- `/app/test_reports/iteration_32.json` - EFI System

---

## Next Priority Tasks
1. **Phase 2 - Email Integration**: Un-mock Resend for sending estimates
2. **Phase 2 - Auto-conversion**: Implement automatic invoice creation
3. **Phase 2 - PDF Templates**: Multiple template selection
4. Legacy data migration (346 contacts pending)
