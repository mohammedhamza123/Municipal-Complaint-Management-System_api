"""
User roles management router (Presentation Layer)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from src.core.dependencies import DatabaseDep
from src.core.auth import get_current_active_user, require_permission
from src.users.service.user_service import UserService
from src.users.model.user import User
from src.users.schema.user import User as UserSchema
from src.roles.schema.role import Role


router = APIRouter(prefix="/users", tags=["user-roles"])


class AssignRoleRequest(BaseModel):
    """Request schema for assigning role"""
    role_id: int


class AssignRolesRequest(BaseModel):
    """Request schema for assigning multiple roles"""
    role_ids: List[int]


@router.post("/{user_id}/roles", response_model=UserSchema)
def assign_role_to_user(
    user_id: int,
    request: AssignRoleRequest,
    db: DatabaseDep,
    current_user: User = Depends(require_permission("users", "update"))
):
    """Assign a role to a user"""
    service = UserService(db)
    return service.add_role_to_user(user_id, request.role_id)


@router.put("/{user_id}/roles", response_model=UserSchema)
def set_user_roles(
    user_id: int,
    request: AssignRolesRequest,
    db: DatabaseDep,
    current_user: User = Depends(require_permission("users", "update"))
):
    """Set user roles (replace all existing roles)"""
    service = UserService(db)
    return service.set_user_roles(user_id, request.role_ids)


@router.delete("/{user_id}/roles/{role_id}", response_model=UserSchema)
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: DatabaseDep,
    current_user: User = Depends(require_permission("users", "update"))
):
    """Remove a role from a user"""
    service = UserService(db)
    return service.remove_role_from_user(user_id, role_id)


@router.get("/{user_id}/roles", response_model=List[Role])
def get_user_roles(
    user_id: int,
    db: DatabaseDep,
    current_user: User = Depends(require_permission("users", "read"))
):
    """Get all roles for a user"""
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.roles




























