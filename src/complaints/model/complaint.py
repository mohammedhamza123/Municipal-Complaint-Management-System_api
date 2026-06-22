"""
Complaint SQLAlchemy model (Infrastructure Layer)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.core.database import Base


class ComplaintStatus(str, enum.Enum):
    """Complaint status enum"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Complaint(Base):
    """Complaint model"""
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.PENDING, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    image = Column(String, nullable=True)  # complaint image filename
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True)  # Related issue
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    department = relationship("Department")
    issue = relationship("Issue", back_populates="complaints")
