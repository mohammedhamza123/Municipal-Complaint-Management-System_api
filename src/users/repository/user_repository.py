"""
User repository (Infrastructure Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.users.model.user import User
from src.core.exceptions import NotFoundError


class UserRepository:
    """Repository for user data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_data: dict) -> User:
        """Create a new user"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update(self, user_id: int, user_data: dict) -> User:
        """Update user"""
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        
        for key, value in user_data.items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def add_role(self, user_id: int, role_id: int) -> User:
        """Add role to user"""
        from src.roles.model.role import Role
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError("Role", str(role_id))
        
        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def remove_role(self, user_id: int, role_id: int) -> User:
        """Remove role from user"""
        from src.roles.model.role import Role
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError("Role", str(role_id))
        
        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def set_roles(self, user_id: int, role_ids: list[int]) -> User:
        """Set user roles (replace all existing roles)"""
        from src.roles.model.role import Role
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        
        roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
        user.roles = roles
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_department_heads(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users who are department heads"""
        from src.departments.model.department import Department
        from sqlalchemy.orm import joinedload
        
        # Get all department head IDs
        head_ids = self.db.query(Department.head_id).filter(
            Department.head_id.isnot(None)
        ).all()
        head_ids = [h[0] for h in head_ids if h[0] is not None]
        
        if not head_ids:
            return []
        
        # Get users who are department heads with eager loading of roles
        return self.db.query(User).options(
            joinedload(User.roles)
        ).filter(
            User.id.in_(head_ids),
            User.is_active == True
        ).offset(skip).limit(limit).all()

