"""
Role service (Application Layer)
"""
from typing import List
from sqlalchemy.orm import Session
from src.roles.repository.role_repository import RoleRepository
from src.roles.schema.role import RoleCreate, RoleUpdate, PermissionCreate
from src.core.exceptions import DuplicateError, NotFoundError
from src.roles.model.role import Role, Permission


class RoleService:
    """Service for role business logic"""
    
    def __init__(self, db: Session):
        self.repository = RoleRepository(db)
    
    def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role"""
        if self.repository.get_role_by_name(role_data.name):
            raise DuplicateError("Role", f"name: {role_data.name}")
        
        role_dict = role_data.model_dump(exclude={"permission_ids"})
        role = self.repository.create_role(role_dict)
        
        if role_data.permission_ids:
            self.repository.add_permissions_to_role(role.id, role_data.permission_ids)
            self.repository.db.refresh(role)
        
        return role
    
    def get_role(self, role_id: int) -> Role:
        """Get role by ID"""
        role = self.repository.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role", str(role_id))
        return role
    
    def get_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles"""
        return self.repository.get_all_roles(skip, limit)
    
    def update_role(self, role_id: int, role_data: RoleUpdate) -> Role:
        """Update role"""
        update_dict = role_data.model_dump(exclude_unset=True, exclude={"permission_ids"})
        role = self.repository.update_role(role_id, update_dict)
        
        if "permission_ids" in role_data.model_dump(exclude_unset=True):
            # Replace all permissions
            role.permissions.clear()
            self.repository.db.commit()
            if role_data.permission_ids:
                self.repository.add_permissions_to_role(role_id, role_data.permission_ids)
            self.repository.db.refresh(role)
        
        return role
    
    def delete_role(self, role_id: int) -> bool:
        """Delete role"""
        return self.repository.delete_role(role_id)
    
    # Permission methods
    def create_permission(self, permission_data: PermissionCreate) -> Permission:
        """Create a new permission"""
        if self.repository.get_permission_by_name(permission_data.name):
            raise DuplicateError("Permission", f"name: {permission_data.name}")
        
        return self.repository.create_permission(permission_data.model_dump())
    
    def get_permissions(self) -> List[Permission]:
        """Get all permissions"""
        return self.repository.get_all_permissions()

