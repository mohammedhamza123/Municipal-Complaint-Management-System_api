"""
Complaint repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.complaints.model.complaint import Complaint, ComplaintStatus
from src.core.exceptions import NotFoundError


class ComplaintRepository:
    """Repository for complaint data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, complaint_data: dict) -> Complaint:
        """Create a new complaint"""
        complaint = Complaint(**complaint_data)
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint
    
    def get_by_id(self, complaint_id: int) -> Optional[Complaint]:
        """Get complaint by ID"""
        return self.db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ComplaintStatus] = None
    ) -> List[Complaint]:
        """Get all complaints"""
        query = self.db.query(Complaint)
        if status:
            query = query.filter(Complaint.status == status)
        return query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Complaint]:
        """Get complaints created by a user"""
        return self.db.query(Complaint).filter(
            Complaint.created_by_id == user_id
        ).order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_department(
        self,
        department_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ComplaintStatus] = None
    ) -> List[Complaint]:
        """Get complaints for a specific department"""
        query = self.db.query(Complaint).filter(
            Complaint.department_id == department_id
        )
        if status:
            query = query.filter(Complaint.status == status)
        return query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_assigned(
        self,
        assigned_to_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """Get complaints assigned to a specific user"""
        return self.db.query(Complaint).filter(
            Complaint.assigned_to_id == assigned_to_id
        ).order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    
    def update(self, complaint_id: int, complaint_data: dict) -> Complaint:
        """Update complaint"""
        complaint = self.get_by_id(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint", str(complaint_id))
        
        for key, value in complaint_data.items():
            setattr(complaint, key, value)
        
        self.db.commit()
        self.db.refresh(complaint)
        return complaint
    
    def delete(self, complaint_id: int) -> bool:
        """Delete complaint"""
        complaint = self.get_by_id(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint", str(complaint_id))
        
        self.db.delete(complaint)
        self.db.commit()
        return True
