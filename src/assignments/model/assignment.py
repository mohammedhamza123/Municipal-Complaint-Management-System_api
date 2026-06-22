"""
Assignment SQLAlchemy model (Infrastructure Layer)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.core.database import Base


class AssignmentStatus(str, enum.Enum):
    """Assignment status enum"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Assignment(Base):
    """Assignment model"""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PENDING, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    issue = relationship("Issue", back_populates="assignments")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])




























