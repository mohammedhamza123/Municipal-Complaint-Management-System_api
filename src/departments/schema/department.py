"""
Department Pydantic schemas (Presentation Layer)
"""
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from typing import Optional, Any, List, Union


class DepartmentBase(BaseModel):
    """Base department schema"""
    name: str
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department"""
    head_id: Optional[int] = None
    
    @field_validator('head_id', mode='before')
    @classmethod
    def convert_head_id(cls, v: Any) -> Optional[int]:
        """Convert head_id from string or list to int if needed"""
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, list):
            # If it's a list, take the first element
            if len(v) > 0:
                v = v[0]
            else:
                return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"head_id must be a number, got: {v}")
        return v


class DepartmentUpdate(BaseModel):
    """Schema for updating a department"""
    name: Optional[str] = None
    description: Optional[str] = None
    head_id: Optional[int] = None
    
    @field_validator('head_id', mode='before')
    @classmethod
    def convert_head_id(cls, v: Any) -> Optional[int]:
        """Convert head_id from string or list to int if needed"""
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, list):
            # If it's a list, take the first element
            if len(v) > 0:
                v = v[0]
            else:
                return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"head_id must be a number, got: {v}")
        return v


class AssignHeadRequest(BaseModel):
    """Schema for assigning a department head"""
    head_id: int
    
    @model_validator(mode='before')
    @classmethod
    def validate_data(cls, data: Any) -> Any:
        """Pre-process data before validation - handles all input formats"""
        # Handle if data is already a list (edge case)
        if isinstance(data, list):
            if len(data) == 0:
                raise ValueError("head_id is required")
            # If it's a list, try to extract the first element
            first_item = data[0]
            if isinstance(first_item, dict) and 'head_id' in first_item:
                data = first_item
            else:
                # Treat the list itself as head_id
                data = {'head_id': first_item}
        
        # Handle dict format
        if isinstance(data, dict):
            # Handle head_id in dict
            if 'head_id' in data:
                head_id = data['head_id']
                
                # Convert list to first element (handle nested lists)
                while isinstance(head_id, list):
                    if len(head_id) == 0:
                        raise ValueError("head_id cannot be an empty list")
                    head_id = head_id[0]  # Extract first element
                
                # Convert string to int
                if isinstance(head_id, str):
                    head_id = head_id.strip()
                    if head_id == "":
                        raise ValueError("head_id cannot be empty")
                    try:
                        head_id = int(head_id)
                    except ValueError:
                        raise ValueError(f"head_id must be a number, got: {head_id}")
                
                # Convert float to int
                elif isinstance(head_id, float):
                    head_id = int(head_id)
                
                # Ensure it's an int
                elif not isinstance(head_id, int):
                    raise ValueError(f"head_id must be a number, got: {type(head_id).__name__} ({head_id})")
                
                data['head_id'] = head_id
            else:
                # If head_id is missing, raise error
                raise ValueError("head_id is required")
        
        return data
    
    @field_validator('head_id', mode='before')
    @classmethod
    def convert_head_id(cls, v: Any) -> int:
        """Convert head_id from string or list to int if needed"""
        if v is None:
            raise ValueError("head_id is required")
        
        # Handle nested lists
        while isinstance(v, list):
            if len(v) == 0:
                raise ValueError("head_id cannot be an empty list")
            v = v[0]  # Extract first element and continue
        
        # Handle string
        if isinstance(v, str):
            v = v.strip()  # Remove whitespace
            if v == "":
                raise ValueError("head_id cannot be empty")
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"head_id must be a number, got: {v}")
        
        # Handle int
        if isinstance(v, int):
            return v
        
        # Handle float
        if isinstance(v, float):
            return int(v)
        
        # Handle other types
        raise ValueError(f"head_id must be a number, got: {type(v).__name__} ({v})")
    
    class Config:
        # Allow extra fields to be ignored
        extra = "ignore"


class HeadInfo(BaseModel):
    """Schema for department head info"""
    id: int
    username: str
    full_name: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class Department(DepartmentBase):
    """Department schema for API responses"""
    id: int
    head_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DepartmentWithHead(Department):
    """Department schema with head details"""
    head: Optional[HeadInfo] = None

    class Config:
        from_attributes = True
