# Battwheels Garages - Product Requirements Document

## Overview
Battwheels Garages is India's first no-towing-first EV service network. The website serves as the digital presence for the company, providing information about services, allowing bookings, and showcasing the company's offerings.

## Target Audience
- EV Fleet Operators (2W, 3W, 4W commercial vehicles)
- Individual EV Owners
- EV OEMs seeking aftersales partnerships
- Quick Commerce & Hyperlocal Delivery companies

## Core Features

### Public Website
- **Home Page**: Hero section, stats, services overview, testimonials, FAQs
- **About Us**: Company vision, mission, and goals
- **Services**: 8 service categories (Periodic EV Service, Motor & Controller, Battery & BMS, etc.)
- **Industries**: Target industry segments served
- **Subscriptions/Plans**: Dynamic pricing for 2W/3W/4W vehicle categories
- **Blog**: SEO-optimized articles with category filtering and pagination (20 articles)
- **Careers**: Job listings
- **Contact**: Contact form, Google Maps integration

### Admin Panel
- Dashboard with stats overview (Bookings, Contacts, Services, Blogs, Testimonials, Jobs)
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
- **Authentication**: JWT for admin panel

## Completed Features (as of Feb 2, 2025)

### Blog SEO Optimization - COMPLETED (Feb 2, 2025)
- [x] All 20 blogs have optimized meta_title (≤60 chars)
- [x] All 20 blogs have optimized meta_desc (≤160 chars)
- [x] All 20 blogs have focus keywords and tags
- [x] All 20 blogs are published and indexable
- [x] Sitemap includes all 40 URLs (20 pages + 20 blogs)
- [x] robots.txt allows crawling of /blog
- [x] BlogPosting JSON-LD schema on every post
- [x] BreadcrumbList JSON-LD schema for navigation
- [x] Related Articles section (3 posts per article)
- [x] Featured Articles in footer for internal linking

### Blog Data Migration - COMPLETED (Feb 2, 2025)
- [x] Migrated 20 blog posts from mockData.js to MongoDB
- [x] Fixed trailing slash issues in all admin API calls
- [x] Dashboard now shows correct blog count (20 posts, 20 published)
- [x] Admin blog management fully functional
- [x] Public blog page fetches from MongoDB API

### Technical SEO Implementation - COMPLETED (Jan 29, 2025)
- [x] Dynamic XML sitemap with all 20 blog URLs (`/api/sitemap.xml`)
- [x] Static sitemap.xml in public folder with all pages
- [x] robots.txt allowing blog crawling
- [x] BlogPosting JSON-LD schema on all blog posts
- [x] BreadcrumbList JSON-LD schema for navigation
- [x] Canonical URLs on all pages
- [x] meta robots: "index, follow" on all public pages
- [x] OpenGraph and Twitter Card meta tags
- [x] Related Articles section for internal linking (3 posts per article)
- [x] Featured Articles in footer for homepage-to-blog linking
- [x] H1/H2/H3 proper heading hierarchy in blog content
- [x] Article schema with datePublished, dateModified, author
- [x] noscript fallback content for crawlers

### Blog Section - COMPLETED
- [x] 20 SEO-optimized blog articles in MongoDB
- [x] Category filtering (11 categories: Fleet Ops, EV Tech Deep Dive, Local Services, etc.)
- [x] Pagination (9 posts per page)
- [x] Post cards with images, dates, authors, excerpts
- [x] Read More links to individual blog posts

### Subscription Page - COMPLETED
- [x] Vehicle category selector (2W/3W/4W)
- [x] Dynamic pricing updates
- [x] Three plans: Starter, Fleet Essential, Fleet Essential Pro

### Admin Panel Fixes - COMPLETED (Feb 2, 2025)
- [x] Fixed all trailing slash API issues
- [x] Dashboard shows correct stats
- [x] Blog management shows all 20 posts
- [x] All CRUD operations working

## Admin Credentials
- **URL**: `/admin/login`
- **Email**: `admin@battwheelsgarages.in`
- **Password**: `Admin@123`

## API Endpoints

### Public
- `POST /api/bookings` - Create service booking
- `GET /api/blogs` - Get published blogs (20 posts)
- `GET /api/services` - Get active services

### Admin
- `POST /api/admin/auth/login` - Admin authentication
- `GET /api/admin/bookings` - Get all bookings
- `GET/POST/PUT/DELETE /api/admin/services` - Services CRUD
- `GET/POST/PUT/DELETE /api/admin/blogs` - Blogs CRUD (20 posts)
- `GET/POST/PUT/DELETE /api/admin/testimonials` - Testimonials CRUD
- `GET/POST/PUT/DELETE /api/admin/jobs` - Jobs CRUD

## Upcoming Tasks
1. Deploy latest changes to production (battwheelsgarages.in)
2. Submit sitemap to Google Search Console
3. Configure GA4 with actual tracking ID

## Future/Backlog
- Domain binding verification
- Sentry error monitoring
- Content humanization review
- SEO meta tags optimization per page
- [x] Three plans: Starter, Fleet Essential, Fleet Essential Pro

### Homepage - COMPLETED
- [x] Achievements/Awards section
- [x] Vehicle types carousel (auto-scrolling)
- [x] Vision/Mission moved to About Us page
- [x] Trusted Partners section with 25 OEM/Fleet logos (Feb 6, 2025)
  - Includes: Bajaj, JEM, Altigreen, Exponent, Indofast, Shiplog, Alt Mobility, Gentari, Magenta, Sun Mobility, Bounce, Lectrix, OSM, Zypp Electric, Delhivery, eBlu, Euler, Log9, MoEVing, Piaggio, Quantum, Ola Electric, OPG Mobility, Yulu, Lithium

### Navigation - COMPLETED
- [x] About Us added to header
- [x] Header logo (transparent PNG)

### Admin Panel - COMPLETED
- [x] Admin login with JWT authentication
- [x] Dashboard with stats
- [x] CRUD for services, blogs, testimonials, jobs, bookings

## Known Issues

### Admin Login (User-Reported)
- User reports intermittent "Incorrect email or password" errors
- Automated tests pass consistently
- Debug logging added to frontend
- **Possible causes**: Browser caching, environment differences
- **Credentials**: admin@battwheelsgarages.in / Admin@123

### ESLint Warnings
- 500+ ESLint warnings (mostly unused variables)
- Non-critical but should be cleaned up

## Data Architecture

### Blog Data (Currently Mocked)
- Blog posts stored in `/app/frontend/src/data/mockData.js`
- Future: Move to MongoDB collection with backend API

### Admin Users
- Collection: `admin_users`
- Fields: email, hashed_password, name, role, is_active, last_login

## API Endpoints

### Public
- `POST /api/bookings` - Create service booking
- `GET /api/blogs` - Get published blogs
- `GET /api/services` - Get active services

### Admin
- `POST /api/admin/auth/login` - Admin authentication
- `GET /api/admin/bookings` - Get all bookings
- `GET/POST/PUT/DELETE /api/admin/services` - Services CRUD
- `GET/POST/PUT/DELETE /api/admin/blogs` - Blogs CRUD

## Upcoming Tasks
1. Complete Admin CRUD functionality
2. Move blog data to MongoDB
3. Fix ESLint warnings
4. GA4 full event tracking

## Future/Backlog
- Domain binding (battwheelsgarages.in)
- Sentry error monitoring
- Content humanization review
- SEO meta tags optimization
