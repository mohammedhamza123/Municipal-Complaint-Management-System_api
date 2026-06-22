"""
Vote SQLAlchemy model (Infrastructure Layer)
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class Vote(Base):
    """Vote model"""
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_upvote = Column(Boolean, default=True)  # True for upvote, False for downvote
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Unique constraint: one vote per user per issue
    __table_args__ = (UniqueConstraint('issue_id', 'user_id', name='unique_user_issue_vote'),)
    
    # Relationships
    issue = relationship("Issue", back_populates="votes")
    user = relationship("User")




























