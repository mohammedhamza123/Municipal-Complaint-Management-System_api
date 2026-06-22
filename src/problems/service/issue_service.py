"""
Issue service (Application Layer)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from src.problems.repository.issue_repository import IssueRepository
from src.problems.schema.issue import IssueCreate, IssueUpdate, IssueReportItem, DepartmentReport
from src.core.exceptions import DuplicateError, NotFoundError
from src.core.utils import generate_area_hash
from src.problems.model.issue import Issue, IssueStatus
from src.problems.model.issue_report import IssueReport


class IssueService:
    """Service for issue business logic"""
    
    def __init__(self, db: Session):
        self.repository = IssueRepository(db)
    
    def create_issue(self, issue_data: IssueCreate, created_by_id: int) -> Issue:
        """Create a new issue with area_hash + department_id duplicate prevention"""
        # Generate area hash
        area_hash = generate_area_hash(issue_data.latitude, issue_data.longitude)
        
        # Check for duplicate: same area + same department
        if issue_data.department_id:
            existing = self.repository.get_by_area_and_department(
                area_hash, issue_data.department_id, active_only=True
            )
            if existing:
                raise DuplicateError(
                    "Issue",
                    f"active issue already exists in this area for this department (Issue #{existing.id})"
                )
        else:
            # Fallback: check by area_hash only
            existing = self.repository.get_by_area_hash(area_hash, active_only=True)
            if existing:
                raise DuplicateError("Issue", f"active issue already exists in this area")
        
        issue_dict = issue_data.model_dump()
        issue_dict["area_hash"] = area_hash
        issue_dict["created_by_id"] = created_by_id
        issue_dict["complaints_count"] = 1
        
        return self.repository.create(issue_dict)
    
    def get_issue(self, issue_id: int) -> Issue:
        """Get issue by ID"""
        issue = self.repository.get_by_id(issue_id)
        if not issue:
            raise NotFoundError("Issue", str(issue_id))
        return issue
    
    def get_issues(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[IssueStatus] = None
    ) -> List[Issue]:
        """Get all issues (sorted by priority desc)"""
        return self.repository.get_all(skip, limit, status)
    
    def get_department_issues(
        self,
        department_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        status: Optional[IssueStatus] = None,
    ) -> List[Issue]:
        """Get issues for a specific department"""
        return self.repository.get_by_department(
            department_id, skip, limit, active_only, status
        )
    
    def update_issue(
        self,
        issue_id: int,
        issue_data: IssueUpdate,
        acting_user_id: Optional[int] = None,
    ) -> Issue:
        """Update issue. When status enters resolved/closed, sets resolved_at and optionally resolved_by_id."""
        existing = self.repository.get_by_id(issue_id)
        if not existing:
            raise NotFoundError("Issue", str(issue_id))

        update_dict = issue_data.model_dump(exclude_unset=True)
        old_status = existing.status

        terminal = frozenset({IssueStatus.RESOLVED, IssueStatus.CLOSED})
        if "status" in update_dict:
            new_status = update_dict["status"]
            if new_status in terminal and old_status not in terminal:
                update_dict["resolved_at"] = datetime.now(timezone.utc)
                if acting_user_id is not None:
                    update_dict["resolved_by_id"] = acting_user_id
                if new_status == IssueStatus.RESOLVED:
                    update_dict["is_active"] = False

        return self.repository.update(issue_id, update_dict)
    
    def delete_issue(self, issue_id: int) -> bool:
        """Delete issue"""
        return self.repository.delete(issue_id)

    # ─── Report / Upvote Methods ───

    def report_issue(self, issue_id: int, user_id: int) -> dict:
        """
        Add a report/upvote to an issue.
        Returns dict with the updated issue info.
        Raises DuplicateError if the user already reported.
        """
        # Check issue exists
        issue = self.repository.get_by_id(issue_id)
        if not issue:
            raise NotFoundError("Issue", str(issue_id))

        # Check if already reported
        existing = self.repository.get_report(issue_id, user_id)
        if existing:
            raise DuplicateError("Report", "لقد قمت بالإبلاغ عن هذه المشكلة مسبقاً")

        self.repository.add_report(issue_id, user_id)

        # Return fresh issue
        updated_issue = self.repository.get_by_id(issue_id)
        return {
            "message": "تم الإبلاغ بنجاح",
            "issue_id": issue_id,
            "complaints_count": updated_issue.complaints_count,
            "priority": updated_issue.priority,
        }

    def unreport_issue(self, issue_id: int, user_id: int) -> dict:
        """Remove a report/upvote from an issue."""
        issue = self.repository.get_by_id(issue_id)
        if not issue:
            raise NotFoundError("Issue", str(issue_id))

        removed = self.repository.remove_report(issue_id, user_id)
        if not removed:
            raise NotFoundError("Report", "لم تقم بالإبلاغ عن هذه المشكلة")

        updated_issue = self.repository.get_by_id(issue_id)
        return {
            "message": "تم إلغاء الإبلاغ",
            "issue_id": issue_id,
            "complaints_count": updated_issue.complaints_count,
            "priority": updated_issue.priority,
        }

    def get_user_reported_issue_ids(self, user_id: int) -> List[int]:
        """Get list of issue IDs the user has reported"""
        return self.repository.get_user_reported_issue_ids(user_id)

    def get_department_report(
        self,
        department_id: int,
        status_filter: Optional[IssueStatus] = None,
    ) -> DepartmentReport:
        """
        Generate a professional report for a department head.
        Includes resolved issues with reporter/employee names.
        """
        from src.departments.model.department import Department
        from sqlalchemy.orm import joinedload

        # Get department name
        department = self.repository.db.query(Department).filter(
            Department.id == department_id
        ).first()
        if not department:
            raise NotFoundError("Department", str(department_id))

        # Get all department issues with relationships loaded
        query = self.repository.db.query(Issue).options(
            joinedload(Issue.created_by),
            joinedload(Issue.assigned_to),
            joinedload(Issue.department),
        ).filter(Issue.department_id == department_id)

        if status_filter:
            query = query.filter(Issue.status == status_filter)

        query = query.order_by(Issue.resolved_at.desc().nullslast(), Issue.created_at.desc())
        all_issues = query.all()

        # Build report items
        items = []
        for issue in all_issues:
            reporter_name = None
            if issue.created_by:
                reporter_name = issue.created_by.full_name or issue.created_by.username

            employee_name = None
            if issue.assigned_to:
                employee_name = issue.assigned_to.full_name or issue.assigned_to.username

            items.append(IssueReportItem(
                id=issue.id,
                title=issue.title,
                description=issue.description,
                status=issue.status,
                priority=issue.priority or 1,
                complaints_count=issue.complaints_count or 0,
                created_at=issue.created_at,
                resolved_at=issue.resolved_at,
                reporter_name=reporter_name,
                employee_name=employee_name,
                department_name=department.name,
                latitude=issue.latitude,
                longitude=issue.longitude,
            ))

        # Count by status
        resolved_count = sum(1 for i in all_issues if i.status == IssueStatus.RESOLVED)
        in_progress_count = sum(1 for i in all_issues if i.status == IssueStatus.IN_PROGRESS)
        pending_count = sum(1 for i in all_issues if i.status == IssueStatus.PENDING)
        closed_count = sum(1 for i in all_issues if i.status == IssueStatus.CLOSED)

        return DepartmentReport(
            department_name=department.name,
            department_id=department_id,
            total_issues=len(all_issues),
            resolved_count=resolved_count,
            in_progress_count=in_progress_count,
            pending_count=pending_count,
            closed_count=closed_count,
            issues=items,
            generated_at=datetime.now(timezone.utc),
        )
    
    def assign_issue_to_employee(
        self,
        issue_id: int,
        employee_id: int,
        assigned_by_id: int
    ) -> Issue:
        """
        Assign an issue to an employee.
        - Updates the issue's assigned_to_id
        - Changes status to IN_PROGRESS if it was PENDING
        - Sends notification to the employee
        """
        from src.users.model.user import User
        from src.notifications.service.notification_service import NotificationService
        from src.notifications.model.notification import NotificationType
        from fastapi import HTTPException, status
        
        # Get issue
        issue = self.get_issue(issue_id)
        
        # Get employee
        employee = self.repository.db.query(User).filter(User.id == employee_id).first()
        if not employee:
            raise NotFoundError("User", str(employee_id))
        
        if not employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign issue to inactive user"
            )
        
        # Verify employee is in the same department as the issue
        if issue.department_id and employee.department_id != issue.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee must be in the same department as the issue"
            )
        
        # Update issue
        update_dict = {
            "assigned_to_id": employee_id,
        }
        
        # Change status to IN_PROGRESS if it was PENDING
        if issue.status == IssueStatus.PENDING:
            update_dict["status"] = IssueStatus.IN_PROGRESS
        
        updated_issue = self.repository.update(issue_id, update_dict)
        
        # Send notification to employee with full issue details
        notification_service = NotificationService(self.repository.db)
        message = f"تم إسناد المشكلة '{issue.title}' إليك.\n"
        message += f"الوصف: {issue.description}\n"
        message += f"الموقع: ({issue.latitude}, {issue.longitude})\n"
        if issue.image:
            message += f"يوجد صورة مرفقة"
        
        notification_service.create_and_push(
            user_id=employee_id,
            title="تم إسناد مشكلة جديدة لك",
            message=message,
            notification_type=NotificationType.INFO,
            related_entity_type="issue",
            related_entity_id=issue_id,
        )
        
        return updated_issue