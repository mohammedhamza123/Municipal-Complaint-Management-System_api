"""
Authentication router (Presentation Layer)
"""
import os
import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from src.core.dependencies import DatabaseDep
from src.core.config import settings
from src.core.security import verify_password, create_access_token
from src.core.auth import get_current_active_user
from src.users.service.user_service import UserService
from src.users.model.user import User
from src.users.schema.user import User as UserSchema, UserCreate

PROFILES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "uploads", "profiles",
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """Register response with user info and auto-login token"""
    access_token: str
    token_type: str = "bearer"
    user: UserSchema


class FCMTokenRequest(BaseModel):
    """FCM token registration request"""
    fcm_token: str


def _save_profile_image(file: UploadFile) -> Optional[str]:
    """Save a profile image and return the filename"""
    if not file or not file.filename:
        return None

    ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED:
        return None

    content = file.file.read()
    if len(content) > 5 * 1024 * 1024:  # 5 MB
        return None

    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(os.path.join(PROFILES_DIR, filename), "wb") as f:
        f.write(content)
    return filename


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    db: DatabaseDep,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
):
    """Register a new user with optional profile image, then auto-login"""
    # Save profile image if provided
    image_filename = None
    if profile_image and profile_image.filename:
        image_filename = _save_profile_image(profile_image)

    user_data = UserCreate(
        email=email,
        username=username,
        password=password,
        full_name=full_name,
    )
    service = UserService(db)
    user = service.create_user(user_data)

    # Save profile image filename to user
    if image_filename:
        user.profile_image = image_filename
        db.commit()
        db.refresh(user)

    # Auto-login: generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username},
        expires_delta=access_token_expires,
    )

    return RegisterResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserSchema.model_validate(user),
    )


@router.post("/login", response_model=Token)
def login(
    db: DatabaseDep,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login and get access token"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Login attempt - username/email: {form_data.username}")
    
    service = UserService(db)

    # Try to authenticate with email or username
    user = service.get_user_by_email(form_data.username)
    if not user:
        logger.info(f"User not found by email, trying username: {form_data.username}")
        user = service.repository.get_by_username(form_data.username)

    if not user:
        logger.warning(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {user.email}, is_active: {user.is_active}")
    
    password_valid = verify_password(form_data.password, user.hashed_password)
    logger.info(f"Password verification result: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Invalid password for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.post("/refresh", response_model=Token)
def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id), "email": current_user.email, "username": current_user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str
    new_password: str


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    request: ChangePasswordRequest,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Change the current user's password"""
    from src.core.security import get_password_hash

    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الحالية غير صحيحة",
        )

    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل",
        )

    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}


@router.post("/fcm-token", status_code=status.HTTP_200_OK)
def register_fcm_token(
    request: FCMTokenRequest,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Register or update the user's FCM device token"""
    current_user.fcm_token = request.fcm_token
    db.commit()
    return {"message": "FCM token registered successfully"}
