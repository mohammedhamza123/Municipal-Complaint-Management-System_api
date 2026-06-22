"""
User router (Presentation Layer)
"""
from typing import List, Optional, Union, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from src.core.dependencies import DatabaseDep
from src.core.auth import require_permission, get_current_active_user
from src.users.model.user import User as UserModel
from src.users.service.user_service import UserService
from src.users.schema.user import User, UserCreate, UserUpdate


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_user(
    user: UserCreate,
    db: DatabaseDep,
    current_user: UserModel = Depends(require_permission("users", "create"))
):
    """
    Create a new user.
    - Admins can create users in any department
    - Department heads can only create users in their own department
    """
    from src.core.auth import is_department_head, has_role
    from src.core.exceptions import ForbiddenError
    
    # Check if current user is a department head (not admin)
    if not has_role(current_user, "admin") and not current_user.is_superuser:
        department_id = is_department_head(current_user, db)
        if department_id is not None:
            # Department head can only create users in their own department
            if user.department_id is None or user.department_id != department_id:
                raise ForbiddenError(
                    "You can only create users in your own department"
                )
    
    service = UserService(db)
    return service.create_user(user)


@router.get("", response_model=List[User])
@router.get("/", response_model=List[User], include_in_schema=False)
def get_users(
    db: DatabaseDep,
    current_user: UserModel = Depends(require_permission("users", "read")),
    skip: int = 0,
    limit: int = 100,
    page: Optional[int] = None,
    page_size: Optional[int] = None
):
    """Get all users with pagination.
    
    Supports both pagination styles:
    - skip/limit: Traditional offset-based pagination
    - page/page_size: Page-based pagination (converted to skip/limit)
    """
    # Convert page/page_size to skip/limit if provided
    if page is not None and page_size is not None:
        skip = (page - 1) * page_size
        limit = page_size
    elif page is not None:
        # If only page is provided, use default page_size
        page_size = page_size or 20
        skip = (page - 1) * page_size
        limit = page_size
    
    service = UserService(db)
    return service.get_users(skip, limit)


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    db: DatabaseDep,
    current_user: UserModel = Depends(require_permission("users", "read"))
):
    """Get user by ID"""
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: DatabaseDep,
    current_user: UserModel = Depends(require_permission("users", "update"))
):
    """Update user"""
    service = UserService(db)
    return service.update_user(user_id, user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: DatabaseDep,
    current_user: UserModel = Depends(require_permission("users", "delete"))
):
    """Delete user"""
    service = UserService(db)
    service.delete_user(user_id)
    return None


@router.get("/department-heads", response_model=List[User])
def get_department_heads(
    request: Request,
    db: DatabaseDep,
    current_user: UserModel = Depends(require_permission("users", "read")),
    skip: int = 0,
    limit: int = 100,
):
    """Get all users who are department heads"""
    # Get query parameters manually to handle list values
    query_params = request.query_params
    
    page = None
    page_size = None
    
    # Handle page parameter - query_params.get() returns string or None
    if 'page' in query_params:
        page_val = query_params.get('page')
        if page_val:
            try:
                # If it's a string, convert to int
                page = int(page_val)
            except (ValueError, TypeError):
                page = None
    
    # Handle page_size parameter
    if 'page_size' in query_params:
        page_size_val = query_params.get('page_size')
        if page_size_val:
            try:
                page_size = int(page_size_val)
            except (ValueError, TypeError):
                page_size = None
    
    # Convert page/page_size to skip/limit if provided
    if page is not None and page_size is not None:
        skip = (page - 1) * page_size
        limit = page_size
    elif page is not None:
        page_size = page_size or 20
        skip = (page - 1) * page_size
        limit = page_size
    
    service = UserService(db)
    return service.get_department_heads(skip, limit)

