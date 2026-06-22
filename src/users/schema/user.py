"""
User Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List, Any, Union


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    department_id: Optional[int] = None
    profile_image: Optional[str] = None
    
    @field_validator('email', mode='before')
    @classmethod
    def convert_email(cls, v: Any) -> str:
        """Convert email from list or other types to string if needed"""
        if isinstance(v, str):
            return v
        if isinstance(v, list) and len(v) > 0:
            return str(v[0])
        return str(v)
    
    @field_validator('username', mode='before')
    @classmethod
    def convert_username(cls, v: Any) -> str:
        """Convert username from list or other types to string if needed"""
        if isinstance(v, str):
            return v
        if isinstance(v, list) and len(v) > 0:
            return str(v[0])
        return str(v)
    
    @field_validator('full_name', mode='before')
    @classmethod
    def convert_full_name(cls, v: Any) -> Optional[str]:
        """Convert full_name from list or other types to string if needed"""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, list) and len(v) > 0:
            return str(v[0])
        return str(v) if v else None
    
    @field_validator('department_id', mode='before')
    @classmethod
    def convert_department_id(cls, v: Any) -> Optional[int]:
        """Convert department_id from string to int if needed"""
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, list) and len(v) > 0:
            v = v[0]
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"department_id must be a number, got: {v}")
        return v


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str
    role_ids: Optional[List[int]] = None
    
    @field_validator('role_ids', mode='before')
    @classmethod
    def convert_role_ids(cls, v: Any) -> Optional[List[int]]:
        """Convert role_ids from strings to ints if needed"""
        if v is None:
            return None
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, int):
                    result.append(item)
                elif isinstance(item, str):
                    try:
                        result.append(int(item))
                    except ValueError:
                        raise ValueError(f"role_ids must be numbers, got: {item}")
                else:
                    raise ValueError(f"role_ids must be a list of numbers, got: {item}")
            return result
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """User schema as stored in database"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """User schema for API responses"""
    roles: List[str] = []

    @field_validator('roles', mode='before')
    @classmethod
    def convert_roles(cls, v: Any) -> List[str]:
        """Convert Role objects to role name strings"""
        if not v:
            return []
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif hasattr(item, 'name'):
                result.append(item.name)
            else:
                result.append(str(item))
        return result
