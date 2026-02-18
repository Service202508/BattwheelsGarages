# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow.

---

## Implementation Status

### ✅ Phase 1 - Core Infrastructure (COMPLETE - Feb 18, 2026)
- **Attachments**: Upload up to 3 files (10MB each) per estimate
- **Public Share Links**: Secure URLs for customer review with expiry, password protection
- **Customer Viewed Status**: Auto-tracks when customers access via public link
- **PDF Generation**: HTML template generation (WeasyPrint fallback)

### ✅ Phase 2 - Workflow & Automation (COMPLETE - Feb 18, 2026)
- **Auto-conversion**: Backend logic for auto-converting accepted quotes (configurable in preferences)
- **PDF Templates**: 3 templates - Standard (green), Professional (navy), Minimal (gray)
- **Import/Export**: CSV/JSON export with status filtering, CSV import with template
- **Custom Fields**: CRUD for custom field definitions
- **Bulk Actions**: Multi-select for void, delete, mark_sent, mark_expired
- **Legacy Migration**: 346 contacts migrated (452 total)

---

## API Endpoints

### Estimates Enhanced
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /templates | List 3 PDF templates |
| GET | /custom-fields | List custom field definitions |
| POST | /custom-fields | Add custom field |
| DELETE | /custom-fields/{name} | Delete custom field |
| GET | /export | Export estimates (CSV/JSON) |
| GET | /import/template | Download CSV import template |
| POST | /import | Import estimates from CSV |
| POST | /bulk/action | Bulk void/delete/mark_sent/mark_expired |
| POST | /bulk/status | Bulk status update |
| GET | /{id}/pdf/{template_id} | PDF with template |
| POST | /{id}/share | Create share link |
| GET | /public/{token} | Public quote view |
| POST | /public/{token}/action | Customer accept/decline |

---

## Technical Stack
- **Backend**: FastAPI, MongoDB (Motor async)
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **Auth**: JWT + Emergent Google OAuth
- **AI**: Gemini (EFI semantic analysis)

---

## Mocked Services
- **WeasyPrint PDF**: Falls back to HTML
- **Email (Resend)**: Logs to console
- **Razorpay**: Mocked

---

## Test Credentials
- **Admin**: admin@battwheels.in / admin123
- **Technician**: deepak@battwheelsgarages.in / tech123

---

## Test Reports
- `/app/test_reports/iteration_34.json` - Phase 2 (100% pass)
- `/app/test_reports/iteration_33.json` - Phase 1 (100% pass)

---

## Upcoming Tasks (Phase 3)
1. Email Integration - Un-mock Resend for sending quotes
2. Enhanced notification system
3. Signature capture on acceptance
4. Project association for quotes

## Backlog
- Cmd+K command palette
- EFI decision tree images
- Un-mock Razorpay payments
