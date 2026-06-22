"""
Issue/Problem Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from src.problems.model.issue import IssueStatus


class IssueUserBrief(BaseModel):
    """معلومات مختصرة عن مستخدم كصاحب بلاغ أو مكلَّف مهمة."""

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    profile_image: Optional[str] = None

    model_config = {"from_attributes": True}


class IssueBase(BaseModel):
    """Base issue schema"""
    title: str
    description: str
    latitude: float
    longitude: float
    priority: int = 1
    department_id: Optional[int] = None
    image: Optional[str] = None


class IssueCreate(IssueBase):
    """Schema for creating an issue"""
    pass


class IssueUpdate(BaseModel):
    """Schema for updating an issue"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[int] = None
    assigned_to_id: Optional[int] = None
    department_id: Optional[int] = None
    resolved_image: Optional[str] = None


class Issue(IssueBase):
    """Issue schema for API responses"""
    id: int
    area_hash: str
    status: IssueStatus
    is_active: bool
    complaints_count: int = 1
    created_by_id: int
    assigned_to_id: Optional[int] = None
    resolved_by_id: Optional[int] = None
    image: Optional[str] = None
    resolved_image: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_by: Optional[IssueUserBrief] = None
    assigned_to: Optional[IssueUserBrief] = None
    resolved_by: Optional[IssueUserBrief] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# ── Report Schemas (for department head reports) ──
# ═══════════════════════════════════════════════

class IssueReportItem(BaseModel):
    """Single issue item in the department report"""
    id: int
    title: str
    description: str
    status: IssueStatus
    priority: int
    complaints_count: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    reporter_name: Optional[str] = None
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


class DepartmentReport(BaseModel):
    """Full department report response"""
    department_name: str
    department_id: int
    total_issues: int
    resolved_count: int
    in_progress_count: int
    pending_count: int
    closed_count: int
    issues: List[IssueReportItem]
    generated_at: datetime
