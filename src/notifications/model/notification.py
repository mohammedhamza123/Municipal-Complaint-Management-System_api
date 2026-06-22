"""
Notification SQLAlchemy model (Infrastructure Layer)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.core.database import Base


class NotificationType(str, enum.Enum):
    """Notification type enum"""
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.INFO, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    related_entity_type = Column(String, nullable=True)  # e.g., "issue", "complaint", "assignment"
    related_entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")




























