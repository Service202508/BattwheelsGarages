# Battwheels Garages - Product Requirements Document

## Overview
Battwheels Garages is India's first no-towing-first EV service network. The website serves as the digital presence for the company, providing information about services, allowing bookings, showcasing offerings, and now includes a **Marketplace Module** for EV spare parts and refurbished vehicle sales.

## Target Audience
- EV Fleet Operators (2W, 3W, 4W commercial vehicles)
- Individual EV Owners
- EV OEMs seeking aftersales partnerships
- Quick Commerce & Hyperlocal Delivery companies
- **EV Service Technicians** (internal marketplace users)

## Core Features

### Public Website
- **Home Page**: Hero section with flip-card animation, stats, services overview, testimonials, Trusted Partners section, FAQs
- **About Us**: Company vision, mission, and goals
- **Services**: 8 service categories (Periodic EV Service, Motor & Controller, Battery & BMS, etc.)
- **Industries**: Target industry segments served
- **Subscriptions/Plans**: Dynamic pricing for 2W/3W/4W vehicle categories
- **Blog**: SEO-optimized articles with category filtering and pagination (20 articles)
- **Battwheels OS**: Technology platform page with EV Failure Intelligence section
- **Careers**: Job listings
- **Contact**: Contact form, Google Maps integration

### Marketplace Module
- **Product Catalog**: 15 spare parts + 40 refurbished vehicles
- **Two Sections**:
  - **Spares & Components** (/marketplace/spares): 15 products across 6 categories
  - **Electric Vehicles** (/marketplace/electric-vehicles): 40 certified refurbished 2W/3W vehicles
- **Filters**: Vehicle Type, OEM Brand, Condition, Price Range
- **Search**: Full-text search by name, model, OEM
- **Cart System**: localStorage-based with quantity management
- **Checkout**: Address form with Razorpay (LIVE) + COD payment options
- **Role-Based Pricing**: Public (0%), Fleet (15% discount), Technician (20% discount)
- **Technician Quick-Order Mode**: Fast search interface for field operations
- **Phone OTP Authentication**: Indian market standard login (MOCKED - pending Twilio)

### Admin Panel
- Dashboard with stats overview
- Bookings management
- Services management
- Blog management (CRUD for 20 blog posts)
- Testimonials management
- Job listings management
- Contact enquiries management

## Technical Stack
- **Frontend**: React 18, Tailwind CSS, Shadcn/UI components
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT for admin panel, Phone OTP for marketplace (mocked)
- **Payments**: Razorpay (LIVE) + COD
- **Analytics**: Google Tag Manager + Google Analytics 4 (base install)

## Completed Features

### Request Callback Feature - COMPLETED (Feb 19, 2025)
- [x] "Request Callback" button on vehicle cards (green phone icon)
- [x] Modal with form: Name, Phone, Preferred Time, Message (optional)
- [x] Backend API: POST /api/callbacks stores requests in MongoDB
- [x] Toast notification on successful submission
- [x] Modal auto-closes after submission
- [x] GET /api/callbacks/count endpoint for admin dashboard

### EV Marketplace Refurbished Vehicles - COMPLETED (Feb 19, 2025)
- [x] Updated EV marketplace to show ONLY refurbished 2W & 3W vehicles
- [x] Seeded 40 certified refurbished vehicles (20 × 2-Wheelers, 20 × 3-Wheelers)
- [x] Removed 4W filtering options
- [x] Updated UI with "CERTIFIED REFURBISHED" branding
- [x] Added route alias `/marketplace/electric-vehicles` for cleaner URLs
- [x] OEM brands: Ather, Ola, TVS, Bajaj, Hero, Revolt, Okinawa, Greaves, Piaggio, Mahindra, Euler, Omega Seiki, Kinetic, Lohia, Atul, etc.

### Razorpay Live Integration - COMPLETED (Feb 2025)
- [x] Backend `/api/payments/create-order` endpoint
- [x] Backend `/api/payments/verify-signature` endpoint
- [x] Frontend Razorpay SDK integration in Checkout.jsx
- [x] **LIVE KEYS CONFIGURED** - rzp_live_SHxrYoF4NujVFl

### Cart & Checkout Redesign - COMPLETED (Feb 2025)
- [x] Modern e-commerce cart page design
- [x] Quantity controls, item removal
- [x] Order summary with totals
- [x] Seamless checkout flow

### Marketplace Images - COMPLETED (Feb 2025)
- [x] AI-generated product-specific images for all 28 items
- [x] High-quality vehicle images for refurbished EVs

### Homepage Flip-Card Fix - COMPLETED (Feb 2025)
- [x] Fixed glitchy 3D flip animation on hero section

### Google Tag Manager - COMPLETED (Feb 2025)
- [x] GTM script installed in index.html
- [ ] Tags and triggers need configuration in GTM dashboard

### Battwheels OS Page - COMPLETED (Feb 2025)
- [x] Added "EV Failure Intelligence" section
- [x] "Patented Technology" branding

### Footer Redesign - COMPLETED (Feb 2025)
- [x] Modern layout with improved spacing
- [x] Updated company name

### Site Content Updates - COMPLETED (Feb 2025)
- [x] Updated "Trusted by" section with fleet operators
- [x] Changed "minor repairs" to "critical electrical, electronic, and mechanical repairs"
- [x] Updated sitemap.xml with marketplace URLs

### Blog SEO Optimization - COMPLETED (Feb 2, 2025)
- [x] 20 blogs with optimized meta titles/descriptions
- [x] BlogPosting JSON-LD schema
- [x] BreadcrumbList JSON-LD schema
- [x] Related Articles section

### Technical SEO - COMPLETED (Jan 29, 2025)
- [x] XML sitemap with all pages
- [x] robots.txt configuration
- [x] Canonical URLs
- [x] OpenGraph and Twitter Card meta tags

## Admin Credentials
- **URL**: `/admin/login`
- **Email**: `admin@battwheelsgarages.in`
- **Password**: `Admin@123`

## Razorpay Credentials (LIVE)
- **Key ID**: `rzp_live_SHxrYoF4NujVFl`
- **Key Secret**: `UDVyYxshrVtPFlRSlIBQkkFV`
- **WARNING**: These are production keys. Real transactions will be processed.

## API Endpoints

### Marketplace
- `GET /api/marketplace/vehicles` - Get vehicles with filters
- `GET /api/marketplace/vehicles/oems` - Get list of OEM brands
- `GET /api/marketplace/products` - Get spare parts
- `GET /api/marketplace/products/slug/{slug}` - Get product by slug
- `POST /api/payments/create-order` - Create Razorpay order
- `POST /api/payments/verify-signature` - Verify payment
- `POST /api/callbacks` - Submit callback request
- `GET /api/callbacks/count` - Get callback request count

### Admin
- `POST /api/admin/auth/login` - Admin authentication
- `GET/POST/PUT/DELETE /api/admin/blogs` - Blogs CRUD
- `GET/POST/PUT/DELETE /api/admin/services` - Services CRUD
- `GET/POST/PUT/DELETE /api/admin/testimonials` - Testimonials CRUD

## Pending Issues

### P1 - Sitemap Google Search Console
- **Status**: BLOCKED - awaiting user feedback on exact error message
- **What we've done**: Updated sitemap.xml with current URLs and lastmod dates

### P2 - Configure GTM Tags
- **Status**: NOT STARTED
- **What's needed**: User to configure tags/triggers in GTM dashboard

## Upcoming Tasks
1. **Test Live Payment Flow** - End-to-end purchase test with Razorpay (needs user permission)
2. **Twilio SMS OTP Integration** - Real phone verification (DEFERRED - awaiting credentials)
3. **Configure GTM Tags** - Event tracking setup in Google Tag Manager

## Future/Backlog
- Marketplace Phase 2: Failure intelligence recommendations, predictive parts
- Google Analytics 4 full event tracking
- Live chat widget integration
- Testimonials section enhancement
- Refactor: Rename `Marketplace.jsx` to `SparesAndComponents.jsx`

## Known Issues
- Phone OTP login is currently **MOCKED** (no real SMS verification)
- ESLint warnings resolved (0 errors, 0 warnings)

## File Structure (Key Files)
```
/app
├── backend
│   ├── routes/
│   │   ├── marketplace.py
│   │   └── payments.py
│   ├── seed_refurbished_vehicles.py
│   └── server.py
└── frontend
    └── src
        ├── App.js (routes)
        ├── pages/marketplace/
        │   ├── ElectricVehicles.jsx
        │   ├── Marketplace.jsx (Spares)
        │   ├── Cart.jsx
        │   └── Checkout.jsx
        └── pages/BattwheelsOS.jsx
```
