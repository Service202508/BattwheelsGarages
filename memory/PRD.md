# Battwheels OS - EV Command Center PRD

## Original Problem Statement
Build a full-stack EV Command Center operation system (Battwheels OS) with integrated AI for Electric failure intelligence. The system includes a full Enterprise ERP with legacy data migration capabilities.

## Data Migration (Feb 15, 2026 - COMPLETED)
Successfully migrated legacy ERP data from Zoho Books backup:

| Entity | Records Migrated |
|--------|------------------|
| Customers | 113 |
| Suppliers | 190 (+ 4 existing = 194) |
| Inventory Items | 1,159 (+ 7 existing = 1,166) |
| Invoices | 4,052 |
| Sales Orders | 24 |
| Purchase Orders | 9 |
| Payments | 2,565 |
| Expenses | 1,766 |
| Chart of Accounts | 109 |
| **TOTAL** | **~10,000 records** |

## What's Been Implemented

### Backend (FastAPI + MongoDB)
- Complete authentication (JWT + Google OAuth)
- Full ERP system with all modules
- **NEW: Customer entity with CRUD operations**
- **NEW: Expense tracking with ledger integration**
- **NEW: Chart of Accounts management**
- **NEW: Data Migration module** (`/app/backend/migration/`)
  - `legacy_migrator.py` - Full migration from Zoho Books XLS exports
  - Supports: Contacts, Vendors, Items, Invoices, Sales/Purchase Orders, Payments, Expenses, Chart of Accounts
- Migration API endpoints:
  - `POST /api/migration/upload` - Check legacy files
  - `POST /api/migration/run` - Run full migration
  - `GET /api/migration/status` - Get migration status

### Frontend (React + Tailwind + Shadcn/UI)
- **NEW: Customers page** (`/customers`) - Full customer management
- **NEW: Expenses page** (`/expenses`) - Expense tracking
- **NEW: Data Migration page** (`/data-migration`) - Admin-only migration dashboard
- Updated sidebar navigation with new sections

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Recharts
- Backend: FastAPI, Motor (MongoDB async), Pandas (for migration)
- Database: MongoDB
- AI: Emergent LLM Integration (GPT-5.2)

## Test Credentials
- **Admin:** admin@battwheels.in / admin123

## API Endpoints (NEW)
- `GET/POST /api/customers` - Customer CRUD
- `GET/POST /api/expenses` - Expense management
- `GET /api/expenses/summary` - Expense analytics
- `GET /api/chart-of-accounts` - Chart of Accounts
- `POST /api/migration/run` - Run data migration
- `GET /api/migration/status` - Migration status

## Migration Notes
1. Legacy data extracted to `/tmp/legacy_data`
2. Invoice files in `/tmp/legacy_data/invoice_data/`
3. Migration handles field mapping automatically
4. Duplicate prevention using `legacy_id` field
5. All migrated records tagged with `migrated_from: "legacy_zoho"`

## Prioritized Backlog

### P0 (Completed)
- [x] ERP System with all modules
- [x] Legacy data migration from Zoho Books
- [x] Customer management
- [x] Expense tracking
- [x] Chart of Accounts

### P1 (Next Phase)
- [ ] Invoice PDF generation
- [ ] Email notifications
- [ ] Customer/Technician portal views
- [ ] Export reports (PDF/Excel)

### P2 (Future)
- [ ] Payment gateway integration
- [ ] Real-time WebSocket updates
- [ ] Backend refactoring (modular APIRouter)
