"""
IssueReport SQLAlchemy model — tracks which user reported/upvoted which issue.
Each user can report an issue only once (unique constraint on user_id + issue_id).
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class IssueReport(Base):
    """Tracks citizen reports/upvotes on issues"""
    __tablename__ = "issue_reports"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint: one report per user per issue
    __table_args__ = (
        UniqueConstraint("issue_id", "user_id", name="uq_issue_user_report"),
    )

    # Relationships
    issue = relationship("Issue", back_populates="reports")
    user = relationship("User")

























