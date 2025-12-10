from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import uuid

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Job Posting Model
class JobPosting(BaseModel):
    id: int
    title: str
    location: str
    type: str  # Full-time, Part-time, Contract
    description: str
    requirements: List[str]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
