"""
Complaint router (Presentation Layer)
"""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from src.core.dependencies import DatabaseDep
from src.core.auth import get_current_active_user, is_department_head, has_role
from src.complaints.service.complaint_service import ComplaintService
from src.complaints.schema.complaint import Complaint, ComplaintCreate, ComplaintUpdate
from src.complaints.model.complaint import ComplaintStatus
from src.users.model.user import User

router = APIRouter(prefix="/complaints", tags=["complaints"])

COMPLAINTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "uploads", "complaints",
)


def _save_complaint_image(file: UploadFile) -> Optional[str]:
    """Save a complaint image and return the filename"""
    if not file or not file.filename:
        return None

    ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED:
        return None

    content = file.file.read()
    if len(content) > 5 * 1024 * 1024:
        return None

    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(COMPLAINTS_DIR, exist_ok=True)
    with open(os.path.join(COMPLAINTS_DIR, filename), "wb") as f:
        f.write(content)
    return filename


@router.post("/", response_model=Complaint, status_code=status.HTTP_201_CREATED)
def create_complaint(
    db: DatabaseDep,
    title: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    department_id: int = Form(...),
    address: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new complaint with optional image (authenticated)"""
    # Save image if provided
    image_filename = None
    if image and image.filename:
        image_filename = _save_complaint_image(image)

    complaint_data = ComplaintCreate(
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        department_id=department_id,
        address=address,
    )

    service = ComplaintService(db)
    complaint = service.create_complaint(complaint_data, current_user.id, image_filename=image_filename)
    return complaint


@router.get("/", response_model=List[Complaint])
def get_complaints(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[ComplaintStatus] = None,
):
    """
    Get complaints.
    - Regular users: see their own complaints
    - Department heads: see all complaints from their department
    - Admins: see all complaints
    """
    service = ComplaintService(db)
    
    # Check if user is a department head
    department_id = is_department_head(current_user, db)
    
    # If user is department head, show all complaints from their department
    if department_id is not None:
        return service.get_department_complaints(department_id, skip, limit, status)
    
    # If user is admin/superuser, show all complaints
    if current_user.is_superuser or has_role(current_user, "admin"):
        return service.get_complaints(skip, limit, status)
    
    # Regular users see only their own complaints
    return service.get_user_complaints(current_user.id, skip, limit)


@router.get("/{complaint_id}", response_model=Complaint)
def get_complaint(
    complaint_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complaint by ID.
    - Regular users: can only see their own complaints
    - Department heads: can see complaints from their department
    - Admins: can see any complaint
    """
    from fastapi import HTTPException, status
    
    service = ComplaintService(db)
    complaint = service.get_complaint(complaint_id)
    
    # Check if user is a department head
    user_dept_id = is_department_head(current_user, db)
    
    # If user is department head, they can see complaints from their department
    if user_dept_id is not None:
        if complaint.department_id != user_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access complaints from your own department"
            )
        return complaint
    
    # If user is admin/superuser, they can see any complaint
    if current_user.is_superuser or has_role(current_user, "admin"):
        return complaint
    
    # Regular users can only see their own complaints
    if complaint.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own complaints"
        )
    
    return complaint


@router.put("/{complaint_id}", response_model=Complaint)
def update_complaint(complaint_id: int, complaint: ComplaintUpdate, db: DatabaseDep):
    """Update complaint"""
    service = ComplaintService(db)
    return service.update_complaint(complaint_id, complaint)


@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint(complaint_id: int, db: DatabaseDep):
    """Delete complaint"""
    service = ComplaintService(db)
    service.delete_complaint(complaint_id)
    return None


@router.get("/my-department", response_model=List[Complaint])
def get_my_department_complaints(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[ComplaintStatus] = None,
):
    """
    Get complaints for the current user's department (for department heads).
    Only department heads can access this endpoint.
    """
    from fastapi import HTTPException, status
    
    # Check if user is a department head
    department_id = is_department_head(current_user, db)
    if department_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for department heads"
        )
    
    service = ComplaintService(db)
    return service.get_department_complaints(department_id, skip, limit, status)
