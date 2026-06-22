"""
Assignment repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.assignments.model.assignment import Assignment, AssignmentStatus
from src.core.exceptions import NotFoundError


class AssignmentRepository:
    """Repository for assignment data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, assignment_data: dict) -> Assignment:
        """Create a new assignment"""
        assignment = Assignment(**assignment_data)
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def get_by_id(self, assignment_id: int) -> Optional[Assignment]:
        """Get assignment by ID"""
        return self.db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[AssignmentStatus] = None) -> List[Assignment]:
        """Get all assignments"""
        query = self.db.query(Assignment)
        if status:
            query = query.filter(Assignment.status == status)
        return query.offset(skip).limit(limit).all()
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Assignment]:
        """Get assignments by user"""
        return self.db.query(Assignment).filter(
            Assignment.assigned_to_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_by_issue(self, issue_id: int) -> List[Assignment]:
        """Get assignments by issue"""
        return self.db.query(Assignment).filter(Assignment.issue_id == issue_id).all()
    
    def update(self, assignment_id: int, assignment_data: dict) -> Assignment:
        """Update assignment"""
        assignment = self.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", str(assignment_id))
        
        for key, value in assignment_data.items():
            setattr(assignment, key, value)
        
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def delete(self, assignment_id: int) -> bool:
        """Delete assignment"""
        assignment = self.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", str(assignment_id))
        
        self.db.delete(assignment)
        self.db.commit()
        return True




























