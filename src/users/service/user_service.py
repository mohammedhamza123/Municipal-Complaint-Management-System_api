"""
User service (Application Layer)
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.users.repository.user_repository import UserRepository
from src.users.schema.user import UserCreate, UserUpdate
from src.core.security import get_password_hash, verify_password
from src.core.exceptions import DuplicateError
from src.users.model.user import User


class UserService:
    """Service for user business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.repository.get_by_email(user_data.email):
            raise DuplicateError("User", f"email: {user_data.email}")
        
        if self.repository.get_by_username(user_data.username):
            raise DuplicateError("User", f"username: {user_data.username}")
        
        # Hash password
        user_dict = user_data.model_dump(exclude={'role_ids'})
        user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
        
        # Create user
        user = self.repository.create(user_dict)
        
        # Assign roles if provided
        if user_data.role_ids:
            user = self.repository.set_roles(user.id, user_data.role_ids)
        
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.repository.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.repository.get_by_email(email)
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users"""
        return self.repository.get_all(skip, limit)
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user"""
        update_dict = user_data.model_dump(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_dict:
            update_dict["hashed_password"] = get_password_hash(update_dict.pop("password"))
        
        return self.repository.update(user_id, update_dict)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        return self.repository.delete(user_id)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = self.repository.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def add_role_to_user(self, user_id: int, role_id: int) -> User:
        """Add role to user"""
        return self.repository.add_role(user_id, role_id)
    
    def remove_role_from_user(self, user_id: int, role_id: int) -> User:
        """Remove role from user"""
        return self.repository.remove_role(user_id, role_id)
    
    def set_user_roles(self, user_id: int, role_ids: list[int]) -> User:
        """Set user roles (replace all existing roles)"""
        return self.repository.set_roles(user_id, role_ids)
    
    def get_department_heads(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users who are department heads"""
        return self.repository.get_department_heads(skip, limit)

