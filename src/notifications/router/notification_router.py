"""
Notification router (Presentation Layer)
"""
from typing import List
from fastapi import APIRouter, Depends, status
from src.core.dependencies import DatabaseDep
from src.core.auth import get_current_active_user
from src.notifications.service.notification_service import NotificationService
from src.notifications.schema.notification import (
    Notification as NotificationSchema,
    NotificationCreate,
)
from src.users.model.user import User


router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── Authenticated endpoints (for citizens) ──

@router.get("/my", response_model=List[NotificationSchema])
def get_my_notifications(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
):
    """Get current user's notifications"""
    service = NotificationService(db)
    return service.get_user_notifications(
        current_user.id, skip, limit, unread_only
    )


@router.get("/my/unread-count")
def get_my_unread_count(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Get count of unread notifications for current user"""
    service = NotificationService(db)
    count = service.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.post("/my/{notification_id}/read", response_model=NotificationSchema)
def mark_notification_read(
    notification_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Mark a single notification as read"""
    service = NotificationService(db)
    return service.mark_as_read(notification_id, current_user.id)


@router.post("/my/mark-all-read")
def mark_all_read(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Mark all notifications as read for current user"""
    service = NotificationService(db)
    count = service.mark_all_as_read(current_user.id)
    return {"message": f"تم تحديد {count} إشعار كمقروء", "count": count}


# ── Admin / internal endpoints ──

@router.post("/", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: NotificationCreate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new notification (admin use)"""
    service = NotificationService(db)
    return service.create_notification(notification)
