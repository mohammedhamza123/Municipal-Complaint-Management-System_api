"""
Department repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.departments.model.department import Department
from src.core.exceptions import NotFoundError


class DepartmentRepository:
    """Repository for department data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, department_data: dict) -> Department:
        """Create a new department"""
        department = Department(**department_data)
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department
    
    def get_by_id(self, department_id: int) -> Optional[Department]:
        """Get department by ID"""
        return self.db.query(Department).filter(Department.id == department_id).first()
    
    def get_by_name(self, name: str) -> Optional[Department]:
        """Get department by name"""
        return self.db.query(Department).filter(Department.name == name).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Department]:
        """Get all departments"""
        return self.db.query(Department).offset(skip).limit(limit).all()
    
    def update(self, department_id: int, department_data: dict) -> Department:
        """Update department"""
        department = self.get_by_id(department_id)
        if not department:
            raise NotFoundError("Department", str(department_id))
        
        for key, value in department_data.items():
            setattr(department, key, value)
        
        self.db.commit()
        self.db.refresh(department)
        return department
    
    def delete(self, department_id: int) -> bool:
        """Delete department"""
        department = self.get_by_id(department_id)
        if not department:
            raise NotFoundError("Department", str(department_id))
        
        self.db.delete(department)
        self.db.commit()
        return True




























