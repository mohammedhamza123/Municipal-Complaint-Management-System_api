"""
Notification Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel, field_serializer
from datetime import datetime, timezone
from typing import Optional
from src.notifications.model.notification import NotificationType


class NotificationBase(BaseModel):
    """Base notification schema"""
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    user_id: int


class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""
    is_read: Optional[bool] = None


class Notification(NotificationBase):
    """Notification schema for API responses"""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime, _info) -> str:
        """Serialize created_at to ISO 8601 format with timezone"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    @field_serializer('read_at')
    def serialize_read_at(self, dt: Optional[datetime], _info) -> Optional[str]:
        """Serialize read_at to ISO 8601 format with timezone"""
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    class Config:
        from_attributes = True








