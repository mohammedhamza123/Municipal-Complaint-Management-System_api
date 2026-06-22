"""
Complaint service (Application Layer)

Core Logic:
  1. Citizen submits a complaint with (title, description, lat, lng, department_id)
  2. System generates area_hash from lat/lng
  3. Check: is there an active Issue with same area_hash + department_id?
     - YES → link complaint to existing issue, increment counter, recalculate priority, DELETE image
     - NO  → create a new Issue automatically, link complaint to it, SET issue image from complaint
  4. If the department has a head → auto-assign complaint & issue to that head
  5. Send notification to the citizen about complaint status
"""
import os
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.complaints.repository.complaint_repository import ComplaintRepository
from src.complaints.schema.complaint import ComplaintCreate, ComplaintUpdate
from src.core.exceptions import NotFoundError
from src.core.utils import generate_area_hash, calculate_priority
from src.complaints.model.complaint import Complaint, ComplaintStatus
from src.problems.model.issue import Issue, IssueStatus
from src.problems.repository.issue_repository import IssueRepository
from src.departments.model.department import Department
from src.notifications.service.notification_service import NotificationService
from src.notifications.model.notification import NotificationType


class ComplaintService:
    """Service for complaint business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ComplaintRepository(db)
        self.issue_repository = IssueRepository(db)
        self.notification_service = NotificationService(db)
    
    def create_complaint(self, complaint_data: ComplaintCreate, created_by_id: int, image_filename: str = None) -> Complaint:
        """
        Create a new complaint and auto-manage the linked Issue.
        
        Flow:
          1. Generate area_hash from coordinates
          2. Look for existing active Issue with same (area_hash, department_id)
          3. If found → link, increment count, bump priority
          4. If not found → create new Issue, link complaint
          5. Auto-assign to department head if available
          6. Send notification to citizen
        """
        complaint_dict = complaint_data.model_dump()
        complaint_dict["created_by_id"] = created_by_id
        if image_filename:
            complaint_dict["image"] = image_filename
        
        lat = complaint_dict["latitude"]
        lng = complaint_dict["longitude"]
        dept_id = complaint_dict["department_id"]
        
        # ── Step 1: Generate area_hash ──
        area_hash = generate_area_hash(lat, lng)
        
        # ── Step 2: Find department head for auto-assignment ──
        department = self.db.query(Department).filter(
            Department.id == dept_id
        ).first()
        
        head_id = department.head_id if department else None
        dept_name = department.name if department else "غير محدد"
        
        # ── Step 3: Find or create Issue ──
        existing_issue = self.issue_repository.get_by_area_and_department(
            area_hash=area_hash,
            department_id=dept_id,
            active_only=True
        )
        
        linked_to_existing = False
        
        if existing_issue:
            # ── Issue EXISTS → link complaint, increment counter, DELETE image ──
            complaint_dict["issue_id"] = existing_issue.id
            
            # Delete complaint image if exists (to save space)
            if image_filename:
                image_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "uploads", "complaints", image_filename
                )
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception:
                    pass  # Ignore deletion errors
                # Don't save image to complaint
                complaint_dict["image"] = None
            
            # Increment complaints count
            new_count = (existing_issue.complaints_count or 0) + 1
            existing_issue.complaints_count = new_count
            
            # Recalculate priority based on new count
            new_priority = calculate_priority(new_count)
            existing_issue.priority = new_priority
            
            # Update issue title to reflect count
            self.db.commit()
            self.db.refresh(existing_issue)
            linked_to_existing = True
        else:
            # ── No Issue exists → create new one with image from first complaint ──
            # Don't auto-assign to head - let head review and assign to employee
            new_issue = Issue(
                title=complaint_dict["title"],
                description=complaint_dict["description"],
                latitude=lat,
                longitude=lng,
                area_hash=area_hash,
                status=IssueStatus.PENDING,
                priority=1,
                complaints_count=1,
                is_active=True,
                created_by_id=created_by_id,
                department_id=dept_id,
                assigned_to_id=None,  # Don't auto-assign - let head review first
                image=image_filename,  # Set issue image from first complaint
            )
            self.db.add(new_issue)
            self.db.flush()  # Get the ID without committing
            
            complaint_dict["issue_id"] = new_issue.id
        
        # ── Step 4: Don't auto-assign complaint - let head review first ──
        # Complaint stays unassigned until head reviews and assigns to employee
        complaint_dict["assigned_to_id"] = None
        complaint_dict["status"] = ComplaintStatus.PENDING
        
        # ── Step 5: Create the complaint ──
        complaint = Complaint(**complaint_dict)
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        
        # ── Step 6: Send notification to citizen ──
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Sending notification to citizen user_id={created_by_id}")
        try:
            if linked_to_existing:
                self.notification_service.create_and_push(
                    user_id=created_by_id,
                    title="تم ربط شكواك بمشكلة موجودة",
                    message=f"تم ربط شكواك '{complaint.title}' بمشكلة موجودة في قسم {dept_name}. عدد البلاغات: {existing_issue.complaints_count}",
                    notification_type=NotificationType.INFO,
                    related_entity_type="complaint",
                    related_entity_id=complaint.id,
                )
            else:
                self.notification_service.create_and_push(
                    user_id=created_by_id,
                    title="تم استلام شكواك",
                    message=f"تم تسجيل شكواك '{complaint.title}' بنجاح وإنشاء مشكلة جديدة في قسم {dept_name}.",
                    notification_type=NotificationType.SUCCESS,
                    related_entity_type="complaint",
                    related_entity_id=complaint.id,
                )
            
            # Notify department head about new complaint (not assigned yet)
            if head_id:
                self.notification_service.create_and_push(
                    user_id=head_id,
                    title="شكوى جديدة تحتاج للمراجعة",
                    message=f"تم استلام شكوى جديدة '{complaint.title}' في قسم {dept_name}. يرجى مراجعتها وإسنادها لموظف.",
                    notification_type=NotificationType.WARNING,
                    related_entity_type="complaint",
                    related_entity_id=complaint.id,
                )
        except Exception as e:
            _logger.error(f"Failed to send notification: {e}")
            pass  # Don't fail complaint creation if notification fails
        
        return complaint
    
    def get_complaint(self, complaint_id: int) -> Complaint:
        """Get complaint by ID"""
        complaint = self.repository.get_by_id(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint", str(complaint_id))
        return complaint
    
    def get_complaints(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ComplaintStatus] = None
    ) -> List[Complaint]:
        """Get all complaints"""
        return self.repository.get_all(skip, limit, status)
    
    def get_user_complaints(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """Get complaints by user"""
        return self.repository.get_by_user(user_id, skip, limit)
    
    def get_department_complaints(
        self,
        department_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ComplaintStatus] = None
    ) -> List[Complaint]:
        """Get complaints for a specific department"""
        return self.repository.get_by_department(department_id, skip, limit, status)
    
    def get_assigned_complaints(
        self,
        assigned_to_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """Get complaints assigned to a specific user"""
        return self.repository.get_by_assigned(assigned_to_id, skip, limit)
    
    def update_complaint(self, complaint_id: int, complaint_data: ComplaintUpdate) -> Complaint:
        """Update complaint and send status notification"""
        complaint = self.repository.get_by_id(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint", str(complaint_id))
        
        old_status = complaint.status
        update_dict = complaint_data.model_dump(exclude_unset=True)
        
        # If status changed to resolved, set resolved_at
        if "status" in update_dict and update_dict["status"] == ComplaintStatus.RESOLVED:
            update_dict["resolved_at"] = datetime.now(timezone.utc)
        
        updated_complaint = self.repository.update(complaint_id, update_dict)
        
        # ── Send notification on status change ──
        new_status = update_dict.get("status")
        if new_status and new_status != old_status:
            try:
                status_messages = {
                    ComplaintStatus.REVIEWED: ("شكواك قيد المراجعة", "تم مراجعة شكواك وسيتم التعامل معها قريباً.", NotificationType.INFO),
                    ComplaintStatus.IN_PROGRESS: ("جاري العمل على شكواك", "تم البدء في معالجة شكواك.", NotificationType.WARNING),
                    ComplaintStatus.RESOLVED: ("تم حل شكواك ✅", "تم حل شكواك بنجاح! شكراً لمساهمتك.", NotificationType.SUCCESS),
                    ComplaintStatus.REJECTED: ("تم رفض شكواك", "عذراً، تم رفض شكواك. يمكنك تقديم شكوى جديدة.", NotificationType.ERROR),
                }
                
                if new_status in status_messages:
                    title, message, notif_type = status_messages[new_status]
                    self.notification_service.create_and_push(
                        user_id=updated_complaint.created_by_id,
                        title=title,
                        message=f"{message}\nالشكوى: {updated_complaint.title}",
                        notification_type=notif_type,
                        related_entity_type="complaint",
                        related_entity_id=updated_complaint.id,
                    )
            except Exception:
                pass
        
        return updated_complaint
    
    def delete_complaint(self, complaint_id: int) -> bool:
        """Delete complaint"""
        return self.repository.delete(complaint_id)
