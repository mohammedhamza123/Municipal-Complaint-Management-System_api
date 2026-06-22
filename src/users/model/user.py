"""
User SQLAlchemy model (Infrastructure Layer)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    fcm_token = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)  # profile image filename
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", foreign_keys=[department_id])
    roles = relationship("Role", secondary="user_roles", back_populates="users")
