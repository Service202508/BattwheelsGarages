from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4

# Service Booking Model
class ServiceBooking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_category: str
    customer_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    service_needed: str
    preferred_date: str
    time_slot: Optional[str] = None
    address: str
    city: str
    name: str
    phone: str
    email: EmailStr
    status: str = "new"  # new, confirmed, in_progress, completed, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServiceBookingCreate(BaseModel):
    vehicle_category: str
    customer_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    service_needed: str
    preferred_date: str
    time_slot: Optional[str] = None
    address: str
    city: str
    name: str
    phone: str
    email: EmailStr

# Fleet/OEM Enquiry Model
class FleetEnquiry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    contact_person: str
    role: str
    email: EmailStr
    phone: str
    city: str
    vehicle_count_2w: Optional[int] = 0
    vehicle_count_3w: Optional[int] = 0
    vehicle_count_4w: Optional[int] = 0
    vehicle_count_commercial: Optional[int] = 0
    requirements: List[str] = []
    details: Optional[str] = None
    status: str = "new"  # new, in_discussion, closed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FleetEnquiryCreate(BaseModel):
    company_name: str
    contact_person: str
    role: str
    email: EmailStr
    phone: str
    city: str
    vehicle_count_2w: Optional[int] = 0
    vehicle_count_3w: Optional[int] = 0
    vehicle_count_4w: Optional[int] = 0
    vehicle_count_commercial: Optional[int] = 0
    requirements: List[str] = []
    details: Optional[str] = None

# Contact Form Model
class ContactMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str
    status: str = "new"  # new, responded
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str

# Career Application Model
class CareerApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: int
    job_title: str
    name: str
    email: EmailStr
    phone: str
    experience: Optional[str] = None
    cv_filename: Optional[str] = None
    cv_path: Optional[str] = None
    status: str = "new"  # new, reviewed, shortlisted, rejected
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CareerApplicationCreate(BaseModel):
    job_id: int
    job_title: str
    name: str
    email: EmailStr
    phone: str
    experience: Optional[str] = None

# Testimonial Model (for admin management)
class Testimonial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    designation: str
    company: str
    content: str
    rating: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Blog Post Model (for admin management)
class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    excerpt: str
    content: str
    category: str
    image: str
    is_published: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Job Posting Model
class JobPosting(BaseModel):
    id: int
    title: str
    location: str
    type: str  # Full-time, Part-time, Contract
    description: str
    requirements: List[str]
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Admin User Model
class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    email: EmailStr
    hashed_password: str
    name: str
    role: str = "admin"  # admin, super_admin
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "admin"


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


# Service Model (for admin CRUD)
class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    slug: str
    short_description: str
    long_description: str
    vehicle_segments: List[str]  # ["2W", "3W", "4W", "Commercial"]
    pricing_model: str  # "fixed", "inspection_based", "contact_for_quote"
    price: Optional[float] = None
    display_order: int = 0
    is_active: bool = True
    icon: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceCreate(BaseModel):
    title: str
    slug: str
    short_description: str
    long_description: str
    vehicle_segments: List[str]
    pricing_model: str
    price: Optional[float] = None
    display_order: int = 0
    is_active: bool = True
    icon: Optional[str] = None


class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    vehicle_segments: Optional[List[str]] = None
    pricing_model: Optional[str] = None
    price: Optional[float] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    icon: Optional[str] = None


# Blog Post Model
class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    slug: str
    thumbnail: Optional[str] = None
    category: str  # "ev_aftersales", "fleet_ops", "product_updates", "case_studies"
    excerpt: str
    content: str  # Rich text/Markdown
    author: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: bool = False
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BlogPostCreate(BaseModel):
    title: str
    slug: str
    thumbnail: Optional[str] = None
    category: str
    excerpt: str
    content: str
    author: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: bool = False


class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    thumbnail: Optional[str] = None
    category: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None


# Testimonial Model
class Testimonial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    company: str
    role: str
    quote: str
    rating: int = 5  # 1-5
    featured: bool = False
    avatar: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TestimonialCreate(BaseModel):
    name: str
    company: str
    role: str
    quote: str
    rating: int = 5
    featured: bool = False
    avatar: Optional[str] = None


class TestimonialUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    quote: Optional[str] = None
    rating: Optional[int] = None
    featured: Optional[bool] = None
    avatar: Optional[str] = None


# Job Posting Model (Enhanced)
class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    location: str
    job_type: str  # "full_time", "part_time", "contract", "field_technician"
    department: str  # "operations", "tech", "sales", "support"
    description: str
    requirements: List[str]
    responsibilities: List[str]
    application_email: Optional[str] = None
    application_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobCreate(BaseModel):
    title: str
    location: str
    job_type: str
    department: str
    description: str
    requirements: List[str]
    responsibilities: List[str]
    application_email: Optional[str] = None
    application_url: Optional[str] = None
    is_active: bool = True


class JobUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    application_email: Optional[str] = None
    application_url: Optional[str] = None
    is_active: Optional[bool] = None


# Booking Note Model (for internal admin notes)
class BookingNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    booking_id: str
    admin_email: str
    note: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
