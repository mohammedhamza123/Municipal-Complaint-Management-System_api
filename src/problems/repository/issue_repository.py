"""
Issue repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from src.problems.model.issue import Issue, IssueStatus
from src.problems.model.issue_report import IssueReport
from src.core.exceptions import NotFoundError


class IssueRepository:
    """Repository for issue data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, issue_data: dict) -> Issue:
        """Create a new issue"""
        issue = Issue(**issue_data)
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue
    
    def get_by_id(self, issue_id: int) -> Optional[Issue]:
        """Get issue by ID"""
        return (
            self.db.query(Issue)
            .options(
                joinedload(Issue.created_by),
                joinedload(Issue.assigned_to),
                joinedload(Issue.resolved_by),
            )
            .filter(Issue.id == issue_id)
            .first()
        )
    
    def get_by_area_hash(self, area_hash: str, active_only: bool = True) -> Optional[Issue]:
        """Get active issue by area hash (without department filter)"""
        query = self.db.query(Issue).filter(Issue.area_hash == area_hash)
        if active_only:
            query = query.filter(Issue.is_active == True)
        return query.first()
    
    def get_by_area_and_department(
        self,
        area_hash: str,
        department_id: int,
        active_only: bool = True
    ) -> Optional[Issue]:
        """
        Get active issue by area_hash AND department_id.
        This is the key uniqueness check: same location + same department = same issue.
        """
        query = self.db.query(Issue).filter(
            and_(
                Issue.area_hash == area_hash,
                Issue.department_id == department_id
            )
        )
        if active_only:
            query = query.filter(Issue.is_active == True)
        return query.first()
    
    def increment_complaints_count(self, issue_id: int) -> Issue:
        """Increment the complaints count of an issue and return updated issue"""
        issue = self.get_by_id(issue_id)
        if not issue:
            raise NotFoundError("Issue", str(issue_id))
        
        issue.complaints_count = (issue.complaints_count or 0) + 1
        self.db.commit()
        self.db.refresh(issue)
        return issue
    
    def update_priority(self, issue_id: int, priority: int) -> Issue:
        """Update priority of an issue"""
        issue = self.get_by_id(issue_id)
        if not issue:
            raise NotFoundError("Issue", str(issue_id))
        
        issue.priority = priority
        self.db.commit()
        self.db.refresh(issue)
        return issue
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[IssueStatus] = None,
        active_only: bool = False
    ) -> List[Issue]:
        """Get all issues with optional filters"""
        query = (
            self.db.query(Issue)
            .options(
                joinedload(Issue.created_by),
                joinedload(Issue.assigned_to),
                joinedload(Issue.resolved_by),
            )
        )
        if status:
            query = query.filter(Issue.status == status)
        if active_only:
            query = query.filter(Issue.is_active == True)
        return query.order_by(
            Issue.priority.desc(),
            Issue.complaints_count.desc(),
            Issue.created_at.desc()
        ).offset(skip).limit(limit).all()

    def count_all(
        self,
        status: Optional[IssueStatus] = None,
        active_only: bool = False,
    ) -> int:
        q = self.db.query(func.count(Issue.id)).select_from(Issue)
        if status:
            q = q.filter(Issue.status == status)
        if active_only:
            q = q.filter(Issue.is_active == True)
        return int(q.scalar() or 0)
    
    def get_by_department(
        self,
        department_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        status: Optional[IssueStatus] = None,
    ) -> List[Issue]:
        """Get issues for a specific department, sorted by priority"""
        query = (
            self.db.query(Issue)
            .options(
                joinedload(Issue.created_by),
                joinedload(Issue.assigned_to),
                joinedload(Issue.resolved_by),
            )
            .filter(Issue.department_id == department_id)
        )
        if status is not None:
            query = query.filter(Issue.status == status)
        elif active_only:
            query = query.filter(Issue.is_active == True)
        return query.order_by(
            Issue.priority.desc(),
            Issue.complaints_count.desc(),
            Issue.created_at.desc()
        ).offset(skip).limit(limit).all()

    def count_by_department(
        self,
        department_id: int,
        active_only: bool = True,
        status: Optional[IssueStatus] = None,
    ) -> int:
        q = self.db.query(func.count(Issue.id)).filter(
            Issue.department_id == department_id
        )
        if status is not None:
            q = q.filter(Issue.status == status)
        elif active_only:
            q = q.filter(Issue.is_active == True)
        return int(q.scalar() or 0)
    
    def update(self, issue_id: int, issue_data: dict) -> Issue:
        """Update issue"""
        issue = self.get_by_id(issue_id)
        if not issue:
            raise NotFoundError("Issue", str(issue_id))
        
        for key, value in issue_data.items():
            setattr(issue, key, value)
        
        self.db.commit()
        self.db.refresh(issue)
        return issue
    
    def delete(self, issue_id: int) -> bool:
        """Delete issue"""
        issue = self.get_by_id(issue_id)
        if not issue:
            raise NotFoundError("Issue", str(issue_id))
        
        self.db.delete(issue)
        self.db.commit()
        return True
    
    def deactivate_duplicates(self, area_hash: str, exclude_id: int):
        """Deactivate other active issues with the same area_hash"""
        self.db.query(Issue).filter(
            and_(
                Issue.area_hash == area_hash,
                Issue.id != exclude_id,
                Issue.is_active == True
            )
        ).update({"is_active": False})
        self.db.commit()

    # ─── Issue Report Methods ───

    def get_report(self, issue_id: int, user_id: int) -> Optional[IssueReport]:
        """Check if a user has already reported an issue"""
        return self.db.query(IssueReport).filter(
            and_(
                IssueReport.issue_id == issue_id,
                IssueReport.user_id == user_id,
            )
        ).first()

    def add_report(self, issue_id: int, user_id: int) -> IssueReport:
        """Add a report/upvote to an issue"""
        report = IssueReport(issue_id=issue_id, user_id=user_id)
        self.db.add(report)

        # Increment complaints_count on the issue
        issue = self.get_by_id(issue_id)
        if issue:
            issue.complaints_count = (issue.complaints_count or 0) + 1
            # Recalculate priority
            from src.core.utils import calculate_priority
            issue.priority = calculate_priority(issue.complaints_count)

        self.db.commit()
        self.db.refresh(report)
        return report

    def remove_report(self, issue_id: int, user_id: int) -> bool:
        """Remove a report/upvote from an issue"""
        report = self.get_report(issue_id, user_id)
        if not report:
            return False

        self.db.delete(report)

        # Decrement complaints_count on the issue
        issue = self.get_by_id(issue_id)
        if issue and issue.complaints_count and issue.complaints_count > 0:
            issue.complaints_count -= 1
            from src.core.utils import calculate_priority
            issue.priority = calculate_priority(issue.complaints_count)

        self.db.commit()
        return True

    def get_user_reported_issue_ids(self, user_id: int) -> List[int]:
        """Get list of issue IDs that a user has reported"""
        reports = self.db.query(IssueReport.issue_id).filter(
            IssueReport.user_id == user_id
        ).all()
        return [r[0] for r in reports]
    
    def get_by_assigned_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[IssueStatus] = None,
    ) -> List[Issue]:
        """Get issues assigned to a specific user (employee)"""
        query = (
            self.db.query(Issue)
            .options(
                joinedload(Issue.created_by),
                joinedload(Issue.assigned_to),
                joinedload(Issue.resolved_by),
            )
            .filter(Issue.assigned_to_id == user_id)
        )
        if status is not None:
            query = query.filter(Issue.status == status)
        return query.order_by(
            Issue.priority.desc(),
            Issue.created_at.desc()
        ).offset(skip).limit(limit).all()

    def count_by_assigned_user(
        self,
        user_id: int,
        status: Optional[IssueStatus] = None,
    ) -> int:
        q = self.db.query(func.count(Issue.id)).filter(
            Issue.assigned_to_id == user_id
        )
        if status is not None:
            q = q.filter(Issue.status == status)
        return int(q.scalar() or 0)