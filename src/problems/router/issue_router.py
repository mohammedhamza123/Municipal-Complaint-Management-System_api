"""
Issue router (Presentation Layer)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from src.core.dependencies import DatabaseDep
from src.core.auth import get_current_active_user, require_permission, has_role
from src.core.exceptions import DuplicateError, NotFoundError
from src.users.model.user import User
from src.problems.service.issue_service import IssueService
from src.problems.schema.issue import Issue, IssueCreate, IssueUpdate, DepartmentReport
from src.problems.model.issue import IssueStatus


router = APIRouter(prefix="/issues", tags=["issues"])


# ══════════════════════════════════════════════════════
# Static path endpoints MUST come before /{issue_id}
# Otherwise FastAPI tries to parse "my-assigned" etc. as int
# ══════════════════════════════════════════════════════

@router.get("/", response_model=List[Issue])
def get_issues(
    db: DatabaseDep,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    status: Optional[IssueStatus] = None,
    include_total: bool = Query(False, description="If true, response includes X-Total-Count header"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all issues (sorted by priority).
    - Public users: see all issues
    - Department heads: see only their department's issues
    - Admins: see all issues
    """
    service = IssueService(db)
    
    # Check if user is a department head
    from src.core.auth import is_department_head
    department_id = is_department_head(current_user, db)
    
    # If user is department head, filter by their department
    if department_id is not None:
        if include_total:
            total = service.repository.count_by_department(
                department_id, active_only=False, status=status
            )
            response.headers["X-Total-Count"] = str(total)
        return service.get_department_issues(
            department_id, skip, limit, active_only=False, status=status
        )

    if include_total:
        total = service.repository.count_all(status=status)
        response.headers["X-Total-Count"] = str(total)
    return service.get_issues(skip, limit, status)


@router.get("/my-reports/ids", response_model=List[int])
def get_my_reported_issue_ids(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Get list of issue IDs the current user has reported/upvoted."""
    service = IssueService(db)
    return service.get_user_reported_issue_ids(current_user.id)


@router.get("/my-department", response_model=List[Issue])
def get_my_department_issues(
    db: DatabaseDep,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[IssueStatus] = None,
    include_total: bool = Query(False, description="If true, sets X-Total-Count header"),
):
    """
    Get issues for the current user's department (for department heads).
    Only department heads can access this endpoint.
    """
    from src.core.auth import is_department_head
    from fastapi import HTTPException, status
    
    # Check if user is a department head
    department_id = is_department_head(current_user, db)
    if department_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for department heads"
        )
    
    service = IssueService(db)
    if include_total:
        total = service.repository.count_by_department(
            department_id, active_only=False, status=status
        )
        response.headers["X-Total-Count"] = str(total)
    return service.get_department_issues(
        department_id, skip, limit, active_only=False, status=status
    )


@router.get("/my-assigned", response_model=List[Issue])
def get_my_assigned_issues(
    db: DatabaseDep,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    status: Optional[IssueStatus] = None,
    include_total: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get issues assigned to the current user (employee).
    Returns all issues where assigned_to_id matches the current user.
    Optional status filter (e.g. resolved for the "fixed" gallery).
    """
    service = IssueService(db)
    if include_total:
        total = service.repository.count_by_assigned_user(
            current_user.id, status=status,
        )
        response.headers["X-Total-Count"] = str(total)
    return service.repository.get_by_assigned_user(
        current_user.id, skip, limit, status=status
    )


@router.get("/department-report", response_model=DepartmentReport)
def get_department_report(
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
    status_filter: IssueStatus = None,
    department_id: Optional[int] = Query(
        None,
        description="For admins: department to report. Heads ignore this (own department).",
    ),
):
    """
    Report for a department.
    - Department heads: always their department (query param ignored).
    - Superusers/admins: department_id query, else user's department_id, else first department in DB.
    """
    from src.core.auth import is_department_head
    from src.departments.model.department import Department

    head_department_id = is_department_head(current_user, db)

    if head_department_id is not None:
        target_department_id = head_department_id
    elif current_user.is_superuser or has_role(current_user, "admin"):
        target_department_id = department_id or current_user.department_id
        if target_department_id is None:
            first_dept = (
                db.query(Department).order_by(Department.id.asc()).first()
            )
            if first_dept is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="لا توجد أقسام في النظام لتوليد التقرير",
                )
            target_department_id = first_dept.id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذا التقرير متاح فقط لرؤساء الأقسام والمسؤولين",
        )

    service = IssueService(db)
    return service.get_department_report(target_department_id, status_filter)


@router.get("/department/{department_id}/report", response_model=DepartmentReport)
def get_specific_department_report(
    department_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
    status_filter: IssueStatus = None,
):
    """
    Generate a report for a specific department (admin or that department's head only).
    """
    from src.core.auth import is_department_head
    
    # Check permissions
    user_dept_id = is_department_head(current_user, db)
    
    if user_dept_id is not None and user_dept_id != department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="يمكنك فقط عرض تقارير قسمك"
        )
    
    if user_dept_id is None and not (current_user.is_superuser or has_role(current_user, "admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية لعرض هذا التقرير"
        )
    
    service = IssueService(db)
    return service.get_department_report(department_id, status_filter)


@router.get("/department/{department_id}", response_model=List[Issue])
def get_department_issues(
    department_id: int,
    db: DatabaseDep,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    include_total: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get issues for a specific department (sorted by priority).
    - Department heads can only access their own department
    - Admins can access any department
    """
    from src.core.auth import is_department_head
    from fastapi import HTTPException, status
    
    # Check if user is a department head
    user_dept_id = is_department_head(current_user, db)
    
    # If user is department head, they can only see their own department
    if user_dept_id is not None and user_dept_id != department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access issues from your own department"
        )
    
    # Admins can access any department
    if not (current_user.is_superuser or has_role(current_user, "admin")):
        # Regular users can access any department (public)
        pass
    
    service = IssueService(db)
    if include_total:
        total = service.repository.count_by_department(
            department_id, active_only=True, status=None
        )
        response.headers["X-Total-Count"] = str(total)
    return service.get_department_issues(department_id, skip, limit)


# ══════════════════════════════════════════════════════
# Dynamic /{issue_id} routes (MUST come AFTER static paths)
# ══════════════════════════════════════════════════════

@router.get("/{issue_id}", response_model=Issue)
def get_issue(
    issue_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get issue by ID.
    - Department heads can only access issues from their department
    - Admins can access any issue
    """
    from src.core.auth import is_department_head
    from fastapi import HTTPException, status
    
    service = IssueService(db)
    issue = service.get_issue(issue_id)
    
    # Check if user is a department head
    user_dept_id = is_department_head(current_user, db)
    
    # If user is department head, they can only see issues from their department
    if user_dept_id is not None:
        if issue.department_id != user_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access issues from your own department"
            )
    
    # Admins and regular users can access any issue
    return issue


@router.post("/", response_model=Issue, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue: IssueCreate,
    db: DatabaseDep,
    current_user: User = Depends(require_permission("issues", "create"))
):
    """Create a new issue manually (requires 'issues:create' permission)"""
    service = IssueService(db)
    return service.create_issue(issue, current_user.id)


@router.put("/{issue_id}", response_model=Issue)
def update_issue(
    issue_id: int,
    issue: IssueUpdate,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update issue (department heads, assigned employees, or admins).
    - Department heads can update issues from their department
    - Employees can only update issues assigned to them (status only)
    - Admins can update any issue
    """
    from src.core.auth import is_department_head, has_role
    from fastapi import HTTPException, status
    
    service = IssueService(db)
    existing_issue = service.get_issue(issue_id)
    
    # Check if user is a department head
    user_dept_id = is_department_head(current_user, db)
    
    # If user is department head, they can only update issues from their department
    if user_dept_id is not None:
        if existing_issue.department_id != user_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update issues from your own department"
            )
    # If user is admin, they can update any issue
    elif current_user.is_superuser or has_role(current_user, "admin"):
        pass  # Admin can update anything
    # If user is employee (not admin, not department head), they can only update assigned issues
    elif existing_issue.assigned_to_id == current_user.id:
        pass  # Employee can update their assigned issue
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update issues assigned to you"
        )

    # Assigned employees (not admin / dept head) must attach an "after fix" photo when
    # moving to resolved or closed so `resolved_image` is available to citizens.
    update_payload = issue.model_dump(exclude_unset=True)
    new_status = update_payload.get("status")
    is_assigned_only_employee = (
        existing_issue.assigned_to_id == current_user.id
        and user_dept_id is None
        and not current_user.is_superuser
        and not has_role(current_user, "admin")
    )
    if is_assigned_only_employee and new_status is not None:
        resolved_img = update_payload.get("resolved_image")
        if new_status == IssueStatus.RESOLVED:
            if not resolved_img:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="يجب إرفاق صورة بعد المعالجة عند تعيين الحالة «تم الحل»",
                )
        elif new_status == IssueStatus.CLOSED:
            if not resolved_img and not existing_issue.resolved_image:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="يجب إرفاق صورة بعد المعالجة قبل إغلاق المشكلة",
                )
    
    return service.update_issue(
        issue_id, issue, acting_user_id=current_user.id,
    )


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    issue_id: int,
    db: DatabaseDep,
    current_user: User = Depends(require_permission("issues", "delete"))
):
    """
    Delete issue (requires 'issues:delete' permission).
    - Department heads can only delete issues from their department
    - Admins can delete any issue
    """
    from src.core.auth import is_department_head
    from fastapi import HTTPException, status
    
    service = IssueService(db)
    existing_issue = service.get_issue(issue_id)
    
    # Check if user is a department head
    user_dept_id = is_department_head(current_user, db)
    
    # If user is department head, they can only delete issues from their department
    if user_dept_id is not None:
        if existing_issue.department_id != user_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete issues from your own department"
            )
    
    service.delete_issue(issue_id)
    return None


# ═══════════════════════════════════════════════
# ── Report / Upvote Endpoints ──
# ═══════════════════════════════════════════════

@router.post("/{issue_id}/report")
def report_issue(
    issue_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Report/upvote an issue (like button).
    Each citizen can report an issue only once.
    """
    service = IssueService(db)
    try:
        return service.report_issue(issue_id, current_user.id)
    except DuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="لقد قمت بالإبلاغ عن هذه المشكلة مسبقاً",
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المشكلة غير موجودة",
        )


@router.delete("/{issue_id}/report", status_code=status.HTTP_200_OK)
def unreport_issue(
    issue_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """Remove a report/upvote from an issue."""
    service = IssueService(db)
    try:
        return service.unreport_issue(issue_id, current_user.id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم تقم بالإبلاغ عن هذه المشكلة",
        )


# ═══════════════════════════════════════════════
# ── Assignment Endpoints ──
# ═══════════════════════════════════════════════

@router.post("/{issue_id}/assign/{employee_id}", response_model=Issue)
def assign_issue_to_employee(
    issue_id: int,
    employee_id: int,
    db: DatabaseDep,
    current_user: User = Depends(get_current_active_user),
):
    """
    Assign an issue to an employee.
    - Department heads can assign issues from their department to employees in their department
    - Admins can assign any issue to any employee
    - Sends notification to the employee with issue details
    """
    from src.core.auth import is_department_head, has_role
    from fastapi import HTTPException, status
    
    service = IssueService(db)
    issue = service.get_issue(issue_id)
    
    # Check permissions
    user_dept_id = is_department_head(current_user, db)
    
    # Department heads can only assign issues from their department
    if user_dept_id is not None:
        if issue.department_id != user_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign issues from your own department"
            )
    
    # Admins and department heads can assign
    if not has_role(current_user, "admin") and user_dept_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to assign issues"
        )
    
    return service.assign_issue_to_employee(issue_id, employee_id, current_user.id)
