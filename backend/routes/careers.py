from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from models import CareerApplication
from typing import Optional
from services.file_storage import file_storage
from services.email_service import email_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/careers", tags=["careers"])

from server import db


@router.post("/applications")
async def create_career_application(
    job_id: int = Form(...),
    job_title: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    experience: Optional[str] = Form(None),
    cv_file: UploadFile = File(...)
):
    """
    Create a new career application with CV upload
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_ext = cv_file.filename.split('.')[-1].lower()
        if f'.{file_ext}' not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Validate file size (5MB max)
        file_content = await cv_file.read()
        if len(file_content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")

        # Upload CV to storage
        success, file_url, error = await file_storage.upload_file(
            file_content=file_content,
            original_filename=cv_file.filename,
            folder='careers/cvs'
        )

        if not success:
            raise HTTPException(status_code=500, detail=f"File upload failed: {error}")

        # Create application object
        application = CareerApplication(
            job_id=job_id,
            job_title=job_title,
            name=name,
            email=email,
            phone=phone,
            experience=experience,
            cv_filename=cv_file.filename,
            cv_path=file_url
        )

        # Save to database
        application_dict = application.dict()
        result = await db.career_applications.insert_one(application_dict)

        # Send email notification
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #16a34a;">New Career Application</h2>
            
            <h3>Job Details:</h3>
            <ul>
                <li><strong>Position:</strong> {job_title}</li>
                <li><strong>Job ID:</strong> {job_id}</li>
            </ul>
            
            <h3>Candidate Details:</h3>
            <ul>
                <li><strong>Name:</strong> {name}</li>
                <li><strong>Email:</strong> {email}</li>
                <li><strong>Phone:</strong> {phone}</li>
                <li><strong>Experience:</strong> {experience or 'N/A'}</li>
            </ul>
            
            <h3>CV:</h3>
            <p><a href="{file_url}" style="color: #16a34a; text-decoration: none;">Download CV ({cv_file.filename})</a></p>
        </body>
        </html>
        """

        text_content = f"""
        New Career Application
        
        Position: {job_title}
        Candidate: {name}
        Email: {email}
        Phone: {phone}
        Experience: {experience or 'N/A'}
        CV: {file_url}
        """

        await email_service.send_email(
            to_email='service@battwheelsgarages.in',
            subject=f'📄 New Job Application - {job_title}',
            html_content=html_content,
            text_content=text_content
        )

        logger.info(f"✅ Career application created: {application.id}")
        return {
            "success": True,
            "message": "Application submitted successfully",
            "application_id": application.id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating career application: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating application: {str(e)}")


@router.get("/applications")
async def get_all_applications(status: str = None, limit: int = 100):
    """
    Get all career applications (for admin)
    """
    try:
        query = {}
        if status:
            query["status"] = status

        applications = await db.career_applications.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return applications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching applications: {str(e)}")
