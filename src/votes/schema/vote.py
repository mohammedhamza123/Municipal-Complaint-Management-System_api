"""
Vote Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel
from datetime import datetime


class VoteBase(BaseModel):
    """Base vote schema"""
    issue_id: int
    is_upvote: bool = True


class VoteCreate(VoteBase):
    """Schema for creating a vote"""
    pass


class Vote(VoteBase):
    """Vote schema for API responses"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True




























