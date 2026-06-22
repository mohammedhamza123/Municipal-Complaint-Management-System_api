"""
Role Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PermissionBase(BaseModel):
    """Base permission schema"""
    name: str
    resource: str
    action: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    """Schema for creating a permission"""
    pass


class Permission(PermissionBase):
    """Permission schema for API responses"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role schema"""
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a role"""
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    """Schema for updating a role"""
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class Role(RoleBase):
    """Role schema for API responses"""
    id: int
    permissions: List[Permission] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True




























