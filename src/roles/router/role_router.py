"""
Role router (Presentation Layer)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.core.dependencies import DatabaseDep
from src.roles.service.role_service import RoleService
from src.roles.schema.role import Role, RoleCreate, RoleUpdate, Permission, PermissionCreate


router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate, db: DatabaseDep):
    """Create a new role"""
    service = RoleService(db)
    return service.create_role(role)


@router.get("/", response_model=List[Role])
def get_roles(db: DatabaseDep, skip: int = 0, limit: int = 100):
    """Get all roles"""
    service = RoleService(db)
    return service.get_roles(skip, limit)


@router.get("/{role_id}", response_model=Role)
def get_role(role_id: int, db: DatabaseDep):
    """Get role by ID"""
    service = RoleService(db)
    return service.get_role(role_id)


@router.put("/{role_id}", response_model=Role)
def update_role(role_id: int, role: RoleUpdate, db: DatabaseDep):
    """Update role"""
    service = RoleService(db)
    return service.update_role(role_id, role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: DatabaseDep):
    """Delete role"""
    service = RoleService(db)
    service.delete_role(role_id)
    return None


# Permission endpoints
@router.post("/permissions", response_model=Permission, status_code=status.HTTP_201_CREATED)
def create_permission(permission: PermissionCreate, db: DatabaseDep):
    """Create a new permission"""
    service = RoleService(db)
    return service.create_permission(permission)


@router.get("/permissions", response_model=List[Permission])
def get_permissions(db: DatabaseDep):
    """Get all permissions"""
    service = RoleService(db)
    return service.get_permissions()

