"""
Department service (Application Layer)
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.departments.repository.department_repository import DepartmentRepository
from src.departments.schema.department import DepartmentCreate, DepartmentUpdate
from src.core.exceptions import DuplicateError, NotFoundError
from src.departments.model.department import Department
from src.users.model.user import User
from src.roles.model.role import Role


class DepartmentService:
    """Service for department business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = DepartmentRepository(db)
    
    def create_department(self, department_data: DepartmentCreate) -> Department:
        """Create a new department"""
        if self.repository.get_by_name(department_data.name):
            raise DuplicateError("Department", f"name: {department_data.name}")
        
        dept_dict = department_data.model_dump()
        
        # Validate head_id if provided
        if dept_dict.get("head_id"):
            self._validate_head(dept_dict["head_id"])
        
        return self.repository.create(dept_dict)
    
    def get_department(self, department_id: int) -> Department:
        """Get department by ID with head info loaded"""
        # Use eager loading to ensure head relationship is loaded
        department = self.db.query(Department).options(
            joinedload(Department.head)
        ).filter(Department.id == department_id).first()
        if not department:
            raise NotFoundError("Department", str(department_id))
        return department
    
    def get_departments(self, skip: int = 0, limit: int = 100) -> List[Department]:
        """Get all departments"""
        return self.repository.get_all(skip, limit)
    
    def update_department(self, department_id: int, department_data: DepartmentUpdate) -> Department:
        """Update department"""
        update_dict = department_data.model_dump(exclude_unset=True)
        
        # Validate head_id if being updated
        if "head_id" in update_dict and update_dict["head_id"] is not None:
            self._validate_head(update_dict["head_id"])
        
        return self.repository.update(department_id, update_dict)
    
    def delete_department(self, department_id: int) -> bool:
        """Delete department"""
        return self.repository.delete(department_id)
    
    def assign_head(self, department_id: int, head_id: int) -> Department:
        """
        Assign a user as head of a department.
        - Validates the user exists and is active
        - If department already has a head, removes the old head first
        - Checks if the new head is already head of another department
        - Assigns the 'manager' role to the user
        - Sets the user's department_id to this department
        """
        # 1. Get department
        department = self.repository.get_by_id(department_id)
        if not department:
            raise NotFoundError("Department", str(department_id))
        
        # 2. Validate new head user
        new_head = self._validate_head(head_id)
        
        # 3. Check if the new head is already head of another department
        existing_dept = self.db.query(Department).filter(
            Department.head_id == head_id,
            Department.id != department_id
        ).first()
        if existing_dept:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User is already head of department '{existing_dept.name}'. Please remove them first."
            )
        
        # 4. If department already has a head, handle the old head
        old_head_id = department.head_id
        if old_head_id and old_head_id != head_id:
            old_head = self.db.query(User).filter(User.id == old_head_id).first()
            if old_head:
                # Remove manager role from old head (only if they have no other manager roles)
                # Keep them as employee in the department (don't change department_id)
                manager_role = self.db.query(Role).filter(Role.name == "manager").first()
                if manager_role and manager_role in old_head.roles:
                    # Check if old head is head of any other department
                    other_dept = self.db.query(Department).filter(
                        Department.head_id == old_head_id,
                        Department.id != department_id
                    ).first()
                    if not other_dept:
                        # Only remove manager role if not head of another department
                        old_head.roles.remove(manager_role)
        
        # 5. Assign 'manager' role to new head if not already assigned
        manager_role = self.db.query(Role).filter(Role.name == "manager").first()
        if manager_role and manager_role not in new_head.roles:
            new_head.roles.append(manager_role)
        
        # 6. Set new head's department
        new_head.department_id = department_id
        
        # 7. Update department head
        department.head_id = head_id
        
        self.db.commit()
        # Reload department with head relationship
        self.db.refresh(department)
        # Ensure head is loaded
        _ = department.head  # Access to trigger lazy load if needed
        return department
    
    def remove_head(self, department_id: int) -> Department:
        """
        Remove the head from a department.
        - Removes the head_id from the department
        - Removes 'manager' role from the old head if they're not head of another department
        - Keeps the user as an employee in the department (doesn't change department_id)
        """
        department = self.repository.get_by_id(department_id)
        if not department:
            raise NotFoundError("Department", str(department_id))
        
        old_head_id = department.head_id
        if old_head_id:
            old_head = self.db.query(User).filter(User.id == old_head_id).first()
            if old_head:
                # Check if old head is head of any other department
                other_dept = self.db.query(Department).filter(
                    Department.head_id == old_head_id,
                    Department.id != department_id
                ).first()
                
                # Only remove manager role if not head of another department
                if not other_dept:
                    manager_role = self.db.query(Role).filter(Role.name == "manager").first()
                    if manager_role and manager_role in old_head.roles:
                        old_head.roles.remove(manager_role)
        
        # Remove head from department
        department.head_id = None
        
        self.db.commit()
        # Reload department with head relationship
        self.db.refresh(department)
        # Ensure head is loaded
        _ = department.head  # Access to trigger lazy load if needed
        return department
    
    def get_department_employees(self, department_id: int) -> List[User]:
        """Get all users/employees in a department"""
        from sqlalchemy.orm import joinedload
        
        department = self.repository.get_by_id(department_id)
        if not department:
            raise NotFoundError("Department", str(department_id))
        
        # Eager load roles to ensure they're serialized correctly
        return self.db.query(User).options(
            joinedload(User.roles)
        ).filter(
            User.department_id == department_id,
            User.is_active == True
        ).all()
    
    def get_department_statistics(self, department_id: int) -> dict:
        """Get statistics for a department"""
        department = self.repository.get_by_id(department_id)
        if not department:
            raise NotFoundError("Department", str(department_id))
        
        # Count employees
        employee_count = self.db.query(User).filter(
            User.department_id == department_id,
            User.is_active == True
        ).count()
        
        # Count issues (if issues table exists)
        issue_count = 0
        try:
            from src.problems.model.issue import Issue
            issue_count = self.db.query(Issue).filter(
                Issue.department_id == department_id
            ).count()
        except:
            pass
        
        # Count complaints (if complaints table exists)
        complaint_count = 0
        try:
            from src.complaints.model.complaint import Complaint
            complaint_count = self.db.query(Complaint).filter(
                Complaint.department_id == department_id
            ).count()
        except:
            pass
        
        return {
            "department_id": department_id,
            "department_name": department.name,
            "employee_count": employee_count,
            "issue_count": issue_count,
            "complaint_count": complaint_count,
            "has_head": department.head_id is not None
        }
    
    def _validate_head(self, head_id: int) -> User:
        """Validate that a user can be department head"""
        user = self.db.query(User).filter(User.id == head_id).first()
        if not user:
            raise NotFoundError("User", str(head_id))
        if not user.is_active:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign inactive user as department head"
            )
        return user
