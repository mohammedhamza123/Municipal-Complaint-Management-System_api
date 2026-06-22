"""
Issue/Problem SQLAlchemy model (Infrastructure Layer)
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.core.database import Base


class IssueStatus(str, enum.Enum):
    """Issue status enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Issue(Base):
    """Issue/Problem model"""
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_hash = Column(String, index=True, nullable=False)  # For duplicate prevention
    status = Column(Enum(IssueStatus), default=IssueStatus.PENDING, nullable=False)
    priority = Column(Integer, default=1)  # 1=Low, 2=Medium, 3=High, 4=Critical
    complaints_count = Column(Integer, default=1, nullable=False)  # Number of linked complaints
    is_active = Column(Boolean, default=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    image = Column(String, nullable=True)  # issue image filename (from first complaint)
    resolved_image = Column(String, nullable=True)  # photo after fix by employee
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    department = relationship("Department")
    complaints = relationship("Complaint", back_populates="issue")
    reports = relationship("IssueReport", back_populates="issue", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="issue")
    assignments = relationship("Assignment", back_populates="issue")
