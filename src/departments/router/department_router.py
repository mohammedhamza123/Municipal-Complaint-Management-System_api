"""
Department router (Presentation Layer)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.core.dependencies import DatabaseDep
from src.core.auth import get_current_user, get_current_active_user, require_role, require_permission
from src.users.model.user import User
from src.departments.service.department_service import DepartmentService
from src.departments.schema.department import (
    Department,
    DepartmentWithHead,
    DepartmentCreate,
    DepartmentUpdate,
    AssignHeadRequest,
    HeadInfo,
)
from src.users.schema.user import User as UserSchema


router = APIRouter(prefix="/departments", tags=["departments"])


# ──────────────────────────────────────────────────────
# Public endpoints (any authenticated user)
# ──────────────────────────────────────────────────────

@router.get("/", response_model=List[Department])
def get_departments(db: DatabaseDep, skip: int = 0, limit: int = 100):
    """Get all departments (public)"""
    service = DepartmentService(db)
    return service.get_departments(skip, limit)


# ──────────────────────────────────────────────────────
# Admin-only endpoints
# ──────────────────────────────────────────────────────

@router.post("/", response_model=Department, status_code=status.HTTP_201_CREATED)
def create_department(
    department: DepartmentCreate,
    db: DatabaseDep,
    current_user: User = Depends(require_role("admin")),
):
    """Create a new department (admin only)"""
    service = DepartmentService(db)
    return service.create_department(department)


# ──────────────────────────────────────────────────────
# Department Head Endpoints (MUST be before /{department_id} routes!)
# Static paths like /my-department must come before dynamic /{department_id}
# otherwise FastAPI will try to parse "my-department" as an integer.
# ──────────────────────────────────────────────────────

@router.get("/my-department", response_model=DepartmentWithHead)
def get_my_department(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current user's department (if they are a department head).
    Only department heads can access this endpoint.
    """
    from src.core.auth import is_department_head
    from src.core.exceptions import ForbiddenError
    
    department_id = is_department_head(current_user, db)
    if department_id is None:
        raise ForbiddenError("You must be a department head to access this endpoint")
    
    service = DepartmentService(db)
    return service.get_department(department_id)


@router.get("/my-department/employees", response_model=List[UserSchema])
def get_my_department_employees(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all employees in the current user's department.
    Only department heads can access this endpoint.
    """
    from src.core.auth import is_department_head
    from src.core.exceptions import ForbiddenError
    
    # Check if user is department head
    department_id = is_department_head(current_user, db)
    if department_id is None:
        raise ForbiddenError(
            "You must be a department head to access this endpoint. "
            "Current user is not assigned as head of any department."
        )
    
    service = DepartmentService(db)
    return service.get_department_employees(department_id)


@router.get("/my-department/statistics")
def get_my_department_statistics(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get statistics for the current user's department.
    Only department heads can access this endpoint.
    Returns:
    - employee_count: Number of employees in the department
    - issue_count: Number of issues in the department
    - complaint_count: Number of complaints in the department
    - has_head: Whether the department has a head
    """
    from src.core.auth import is_department_head
    from src.core.exceptions import ForbiddenError
    
    department_id = is_department_head(current_user, db)
    if department_id is None:
        raise ForbiddenError("You must be a department head to access this endpoint")
    
    service = DepartmentService(db)
    return service.get_department_statistics(department_id)


# ──────────────────────────────────────────────────────
# Dynamic /{department_id} routes (MUST come AFTER /my-department routes)
# ──────────────────────────────────────────────────────

@router.get("/{department_id}", response_model=DepartmentWithHead)
def get_department(
    department_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get department by ID with head info.
    - Admins can view any department
    - Department heads can only view their own department
    - Regular users can view any department (public info)
    """
    from src.core.auth import is_department_head, has_role
    
    # Check if user is department head of this department
    user_dept_id = is_department_head(current_user, db)
    
    # Department heads can only view their own department (unless they're admin)
    if not has_role(current_user, "admin"):
        if user_dept_id is not None and user_dept_id != department_id:
            from src.core.exceptions import ForbiddenError
            raise ForbiddenError("You can only view your own department")
    
    service = DepartmentService(db)
    return service.get_department(department_id)


@router.put("/{department_id}", response_model=Department)
def update_department(
    department_id: int,
    department: DepartmentUpdate,
    db: DatabaseDep,
    current_user: User = Depends(require_role("admin")),
):
    """Update department (admin only)"""
    service = DepartmentService(db)
    return service.update_department(department_id, department)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: DatabaseDep,
    current_user: User = Depends(require_role("admin")),
):
    """Delete department (admin only)"""
    service = DepartmentService(db)
    service.delete_department(department_id)
    return None


# ──────────────────────────────────────────────────────
# Department Head Management (admin only)
# ──────────────────────────────────────────────────────

@router.post("/{department_id}/head", response_model=DepartmentWithHead)
def assign_department_head(
    department_id: int,
    request: AssignHeadRequest,
    db: DatabaseDep,
    current_user: User = Depends(require_role("admin")),
):
    """
    Assign a user as head of a department (admin only).
    This will also:
    - Give the user the 'manager' role
    - Set the user's department to this department
    """
    try:
        service = DepartmentService(db)
        return service.assign_head(department_id, request.head_id)
    except ValueError as e:
        # Handle validation errors with better messages
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete("/{department_id}/head", response_model=DepartmentWithHead)
def remove_department_head(
    department_id: int,
    db: DatabaseDep,
    current_user: User = Depends(require_role("admin")),
):
    """Remove the head from a department (admin only)"""
    service = DepartmentService(db)
    return service.remove_head(department_id)


# ──────────────────────────────────────────────────────
# Department Employees (by ID)
# ──────────────────────────────────────────────────────

@router.get("/{department_id}/employees", response_model=List[UserSchema])
def get_department_employees(
    department_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all employees in a department.
    - Admins can view any department's employees
    - Department heads can only view their own department's employees
    """
    from src.core.auth import is_department_head, has_role
    
    # Check if user is department head of this department
    user_dept_id = is_department_head(current_user, db)
    
    # Admins can view any department, department heads can only view their own
    if not has_role(current_user, "admin"):
        if user_dept_id is None or user_dept_id != department_id:
            from src.core.exceptions import ForbiddenError
            raise ForbiddenError("You can only view employees of your own department")
    
    service = DepartmentService(db)
    return service.get_department_employees(department_id)


@router.get("/{department_id}/statistics")
def get_department_statistics(
    department_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get statistics for a department.
    - Admins can view statistics for any department
    - Department heads can only view statistics for their own department
    """
    from src.core.auth import is_department_head, has_role
    from src.core.exceptions import ForbiddenError
    
    # Check if user is department head of this department
    user_dept_id = is_department_head(current_user, db)
    
    # Admins can view any department, department heads can only view their own
    if not has_role(current_user, "admin"):
        if user_dept_id is None or user_dept_id != department_id:
            raise ForbiddenError("You can only view statistics of your own department")
    
    service = DepartmentService(db)
    return service.get_department_statistics(department_id)
