"""
Role repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.roles.model.role import Role, Permission
from src.core.exceptions import NotFoundError


class RoleRepository:
    """Repository for role data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_role(self, role_data: dict) -> Role:
        """Create a new role"""
        role = Role(**role_data)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID"""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def get_all_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles"""
        return self.db.query(Role).offset(skip).limit(limit).all()
    
    def update_role(self, role_id: int, role_data: dict) -> Role:
        """Update role"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role", str(role_id))
        
        for key, value in role_data.items():
            if key != "permission_ids":
                setattr(role, key, value)
        
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def delete_role(self, role_id: int) -> bool:
        """Delete role"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role", str(role_id))
        
        self.db.delete(role)
        self.db.commit()
        return True
    
    def add_permissions_to_role(self, role_id: int, permission_ids: List[int]):
        """Add permissions to role"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role", str(role_id))
        
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        role.permissions.extend(permissions)
        self.db.commit()
    
    def remove_permissions_from_role(self, role_id: int, permission_ids: List[int]):
        """Remove permissions from role"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise NotFoundError("Role", str(role_id))
        
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        for perm in permissions:
            role.permissions.remove(perm)
        self.db.commit()
    
    # Permission methods
    def create_permission(self, permission_data: dict) -> Permission:
        """Create a new permission"""
        permission = Permission(**permission_data)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission
    
    def get_permission_by_id(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID"""
        return self.db.query(Permission).filter(Permission.id == permission_id).first()
    
    def get_permission_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name"""
        return self.db.query(Permission).filter(Permission.name == name).first()
    
    def get_all_permissions(self) -> List[Permission]:
        """Get all permissions"""
        return self.db.query(Permission).all()

