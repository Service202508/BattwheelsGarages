# Battwheels OS - Product Requirements Document

## Original Problem Statement
Build a production-grade accounting ERP system ("Battwheels OS") cloning Zoho Books functionality with comprehensive quote-to-invoice workflow and EV-specific failure intelligence.

---

## Implementation Status

### ✅ Quotes/Estimates Module (COMPLETE)

**Phase 1 - Core Infrastructure:**
- Attachments: Up to 3 files (10MB each) per estimate
- Public Share Links: Secure URLs with expiry, password protection
- Customer Viewed Status: Auto-tracking via public link
- PDF Generation: HTML template with WeasyPrint fallback

**Phase 2 - Workflow & Automation:**
- Auto-conversion: Accepted quotes → invoices/sales orders
- PDF Templates: Standard, Professional, Minimal
- Import/Export: CSV/JSON with template
- Custom Fields: Full CRUD management
- Bulk Actions: Void, delete, mark_sent, mark_expired
- Legacy Migration: 346 contacts migrated (452 total)

### ✅ Backlog Items (COMPLETE - Feb 18, 2026)

**1. Cmd+K Command Palette**
- Global keyboard shortcut (⌘K / Ctrl+K)
- Quick Actions: Create estimates, invoices, tickets, contacts, expenses
- Page Navigation: All 20+ modules searchable
- Recent searches with localStorage persistence
- Keyboard navigation (↑↓ navigate, ↵ select, esc close)

**2. EFI Decision Tree Images**
- Upload images for diagnostic steps (max 5MB, JPG/PNG/GIF/WebP)
- Store in MongoDB with base64 encoding
- Display inline in EFI Side Panel
- Click to view full-size
- Endpoints:
  - `POST /api/efi-guided/failure-cards/{id}/step-image`
  - `GET /api/efi-guided/step-image/{image_id}`
  - `GET /api/efi-guided/failure-cards/{id}/images`
  - `DELETE /api/efi-guided/step-image/{image_id}`

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
- `/app/test_reports/iteration_34.json` - Phase 2 Estimates
- `/app/test_reports/iteration_33.json` - Phase 1 Estimates

---

## Remaining Backlog
- Un-mock Razorpay payments
- Un-mock Resend email
- Enhanced notification system
- Signature capture on acceptance
