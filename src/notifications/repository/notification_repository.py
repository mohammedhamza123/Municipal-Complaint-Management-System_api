"""
Notification repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from src.notifications.model.notification import Notification
from src.core.exceptions import NotFoundError


class NotificationRepository:
    """Repository for notification data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, notification_data: dict) -> Notification:
        """Create a new notification with correct timezone"""
        # Ensure created_at is set with UTC timezone
        if "created_at" not in notification_data:
            notification_data["created_at"] = datetime.now(timezone.utc)
        notification = Notification(**notification_data)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
    
    def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()
    
    def get_by_user(
        self, user_id: int, skip: int = 0, limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications by user"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Notification]:
        """Get all notifications"""
        return self.db.query(Notification).offset(skip).limit(limit).all()
    
    def update(self, notification_id: int, notification_data: dict) -> Notification:
        """Update notification"""
        notification = self.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification", str(notification_id))
        
        for key, value in notification_data.items():
            setattr(notification, key, value)
        
        self.db.commit()
        self.db.refresh(notification)
        return notification
    
    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        from datetime import datetime, timezone
        count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.now(timezone.utc),
        })
        self.db.commit()
        return count
    
    def delete(self, notification_id: int) -> bool:
        """Delete notification"""
        notification = self.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification", str(notification_id))
        
        self.db.delete(notification)
        self.db.commit()
        return True
