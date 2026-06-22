"""
Assignment service (Application Layer)
"""
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from src.assignments.repository.assignment_repository import AssignmentRepository
from src.assignments.schema.assignment import AssignmentCreate, AssignmentUpdate
from src.core.exceptions import NotFoundError
from src.assignments.model.assignment import Assignment, AssignmentStatus


class AssignmentService:
    """Service for assignment business logic"""
    
    def __init__(self, db: Session):
        self.repository = AssignmentRepository(db)
    
    def create_assignment(self, assignment_data: AssignmentCreate, assigned_by_id: int) -> Assignment:
        """Create a new assignment"""
        assignment_dict = assignment_data.model_dump()
        assignment_dict["assigned_by_id"] = assigned_by_id
        return self.repository.create(assignment_dict)
    
    def get_assignment(self, assignment_id: int) -> Assignment:
        """Get assignment by ID"""
        assignment = self.repository.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", str(assignment_id))
        return assignment
    
    def get_assignments(self, skip: int = 0, limit: int = 100, status: AssignmentStatus = None) -> List[Assignment]:
        """Get all assignments"""
        return self.repository.get_all(skip, limit, status)
    
    def get_user_assignments(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Assignment]:
        """Get assignments by user"""
        return self.repository.get_by_user(user_id, skip, limit)
    
    def get_issue_assignments(self, issue_id: int) -> List[Assignment]:
        """Get assignments by issue"""
        return self.repository.get_by_issue(issue_id)
    
    def update_assignment(self, assignment_id: int, assignment_data: AssignmentUpdate) -> Assignment:
        """Update assignment"""
        update_dict = assignment_data.model_dump(exclude_unset=True)
        
        # If status changed to completed, set completed_at
        if "status" in update_dict and update_dict["status"] == AssignmentStatus.COMPLETED:
            update_dict["completed_at"] = datetime.utcnow()
        
        return self.repository.update(assignment_id, update_dict)
    
    def delete_assignment(self, assignment_id: int) -> bool:
        """Delete assignment"""
        return self.repository.delete(assignment_id)

