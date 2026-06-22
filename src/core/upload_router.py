"""
File upload router - handles profile pictures and complaint images
"""
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from src.core.dependencies import DatabaseDep
from src.core.auth import get_current_active_user
from src.users.model.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
PROFILES_DIR = os.path.join(UPLOAD_DIR, "profiles")
COMPLAINTS_DIR = os.path.join(UPLOAD_DIR, "complaints")
ISSUES_RESOLVED_DIR = os.path.join(UPLOAD_DIR, "issues_resolved")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _save_file(file: UploadFile, dest_dir: str) -> str:
    """Save uploaded file and return the filename"""
    # Validate extension
    _, ext = os.path.splitext(file.filename or "file.jpg")
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"نوع الملف غير مدعوم. الأنواع المسموحة: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read content
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="حجم الملف كبير جداً. الحد الأقصى 5 ميغابايت"
        )

    # Generate unique filename
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(dest_dir, filename)

    os.makedirs(dest_dir, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)

    return filename


@router.post("/profile-image")
def upload_profile_image(
    db: DatabaseDep,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload or update profile image for the current user"""
    # Delete old profile image if exists
    if current_user.profile_image:
        old_path = os.path.join(PROFILES_DIR, current_user.profile_image)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = _save_file(file, PROFILES_DIR)
    current_user.profile_image = filename
    db.commit()

    return {"filename": filename, "url": f"/uploads/profiles/{filename}"}


@router.post("/complaint-image")
def upload_complaint_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a complaint image (returns filename to attach to complaint)"""
    filename = _save_file(file, COMPLAINTS_DIR)
    return {"filename": filename, "url": f"/uploads/complaints/{filename}"}


@router.post("/issue-resolved-image")
def upload_issue_resolved_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload an 'after repair' image; use returned filename in PUT /issues/{id} as resolved_image."""
    filename = _save_file(file, ISSUES_RESOLVED_DIR)
    return {"filename": filename, "url": f"/uploads/issues_resolved/{filename}"}

