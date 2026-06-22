"""
Assignment Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.assignments.model.assignment import AssignmentStatus


class AssignmentBase(BaseModel):
    """Base assignment schema"""
    issue_id: int
    assigned_to_id: int
    notes: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    """Schema for creating an assignment"""
    pass


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment"""
    status: Optional[AssignmentStatus] = None
    notes: Optional[str] = None


class Assignment(AssignmentBase):
    """Assignment schema for API responses"""
    id: int
    assigned_by_id: int
    status: AssignmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True




























