"""
Complaint Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.complaints.model.complaint import ComplaintStatus


class ComplaintBase(BaseModel):
    """Base complaint schema"""
    title: str
    description: str
    latitude: float              # Required — for area_hash
    longitude: float             # Required — for area_hash
    department_id: int           # Required — for issue grouping
    address: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    """Schema for creating a complaint"""
    pass


class ComplaintUpdate(BaseModel):
    """Schema for updating a complaint"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ComplaintStatus] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    assigned_to_id: Optional[int] = None
    department_id: Optional[int] = None
    issue_id: Optional[int] = None


class Complaint(BaseModel):
    """Complaint schema for API responses"""
    id: int
    title: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    department_id: Optional[int] = None
    address: Optional[str] = None
    image: Optional[str] = None
    status: ComplaintStatus
    created_by_id: int
    assigned_to_id: Optional[int] = None
    issue_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
