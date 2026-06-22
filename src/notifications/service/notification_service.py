"""
Notification service (Application Layer)
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.notifications.repository.notification_repository import NotificationRepository
from src.notifications.schema.notification import NotificationCreate, NotificationUpdate
from src.core.exceptions import NotFoundError
from src.notifications.model.notification import Notification, NotificationType
from src.core.firebase_service import send_push_notification
from src.users.model.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationRepository(db)
    
    def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification and send FCM push"""
        notification_dict = notification_data.model_dump()
        # Ensure created_at is set with UTC timezone
        if "created_at" not in notification_dict:
            notification_dict["created_at"] = datetime.now(timezone.utc)
        notification = self.repository.create(notification_dict)
        
        # Send FCM push notification
        self._send_fcm(notification)
        
        return notification
    
    def create_and_push(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
    ) -> Notification:
        """
        Helper: create notification + send FCM push in one call.
        Used internally by other services (complaint, issue, etc.)
        """
        notification = self.repository.create({
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "created_at": datetime.now(timezone.utc),  # Explicitly set UTC time
        })
        
        self._send_fcm(notification)
        return notification
    
    def _send_fcm(self, notification: Notification):
        """Send FCM push for a notification"""
        try:
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                logger.warning(f"FCM: User {notification.user_id} not found")
                return
            if not user.fcm_token:
                logger.warning(f"FCM: User {user.id} ({user.username}) has no FCM token")
                return
            
            logger.info(f"FCM: Sending push to user {user.id} ({user.username}), token={user.fcm_token[:20]}...")
            result = send_push_notification(
                token=user.fcm_token,
                title=notification.title,
                body=notification.message,
                data={
                    "notification_id": str(notification.id),
                    "type": str(notification.type.value) if notification.type else "info",
                    "related_entity_type": notification.related_entity_type or "",
                    "related_entity_id": str(notification.related_entity_id or ""),
                },
            )
            logger.info(f"FCM: Push result = {result}")
        except Exception as e:
            logger.error(f"FCM: Failed to send push: {e}")
            pass  # Don't fail the request if FCM fails

    def get_notification(self, notification_id: int) -> Notification:
        """Get notification by ID"""
        notification = self.repository.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification", str(notification_id))
        return notification
    
    def get_user_notifications(
        self, user_id: int, skip: int = 0, limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications by user"""
        return self.repository.get_by_user(user_id, skip, limit, unread_only)
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        return self.repository.get_unread_count(user_id)
    
    def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        """Mark a single notification as read"""
        notification = self.repository.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification", str(notification_id))
        if notification.user_id != user_id:
            raise NotFoundError("Notification", str(notification_id))
        return self.repository.update(notification_id, {
            "is_read": True,
            "read_at": datetime.now(timezone.utc),
        })
    
    def update_notification(self, notification_id: int, notification_data: NotificationUpdate) -> Notification:
        """Update notification"""
        update_dict = notification_data.model_dump(exclude_unset=True)
        
        if "is_read" in update_dict and update_dict["is_read"]:
            update_dict["read_at"] = datetime.now(timezone.utc)
        elif "is_read" in update_dict and not update_dict["is_read"]:
            update_dict["read_at"] = None
        
        return self.repository.update(notification_id, update_dict)
    
    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        return self.repository.mark_all_as_read(user_id)
    
    def delete_notification(self, notification_id: int) -> bool:
        """Delete notification"""
        return self.repository.delete(notification_id)
