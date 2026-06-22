"""
Assignment router (Presentation Layer)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.core.dependencies import DatabaseDep
from src.assignments.service.assignment_service import AssignmentService
from src.assignments.schema.assignment import Assignment, AssignmentCreate, AssignmentUpdate
from src.assignments.model.assignment import AssignmentStatus


router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/", response_model=Assignment, status_code=status.HTTP_201_CREATED)
def create_assignment(assignment: AssignmentCreate, assigned_by_id: int, db: DatabaseDep):
    """Create a new assignment"""
    service = AssignmentService(db)
    return service.create_assignment(assignment, assigned_by_id)


@router.get("/", response_model=List[Assignment])
def get_assignments(
    db: DatabaseDep,
    skip: int = 0,
    limit: int = 100,
    status: AssignmentStatus = None
):
    """Get all assignments"""
    service = AssignmentService(db)
    return service.get_assignments(skip, limit, status)


@router.get("/{assignment_id}", response_model=Assignment)
def get_assignment(assignment_id: int, db: DatabaseDep):
    """Get assignment by ID"""
    service = AssignmentService(db)
    return service.get_assignment(assignment_id)


@router.put("/{assignment_id}", response_model=Assignment)
def update_assignment(assignment_id: int, assignment: AssignmentUpdate, db: DatabaseDep):
    """Update assignment"""
    service = AssignmentService(db)
    return service.update_assignment(assignment_id, assignment)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: int, db: DatabaseDep):
    """Delete assignment"""
    service = AssignmentService(db)
    service.delete_assignment(assignment_id)
    return None

