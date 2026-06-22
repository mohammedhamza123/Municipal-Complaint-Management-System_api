"""
Authentication and authorization dependencies
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from .database import get_db
from .security import decode_access_token
from .exceptions import UnauthorizedError, ForbiddenError
from .dependencies import DatabaseDep
from src.users.model.user import User
from src.roles.model.role import Role, Permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = UnauthorizedError("Could not validate credentials")
    
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Token missing user identifier")
    
    # Ensure user_id is an integer
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedError("Invalid user identifier in token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError("User not found")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_user_permissions(user: User, db: Optional[Session] = None) -> List[str]:
    """
    Get all permissions for a user (from all their roles)
    """
    permissions = set()
    
    # Superuser has all permissions
    if user.is_superuser:
        return ["*"]  # All permissions
    
    # Refresh user roles if needed
    if db:
        db.refresh(user, ["roles"])
    
    # Get permissions from all user roles
    for role in user.roles:
        if db:
            db.refresh(role, ["permissions"])
        for permission in role.permissions:
            # Format: "resource:action" or just permission name
            perm_name = f"{permission.resource}:{permission.action}"
            permissions.add(perm_name)
            permissions.add(permission.name)  # Also add the name
    
    return list(permissions)


def has_permission(user: User, resource: str, action: str, db: Optional[Session] = None) -> bool:
    """
    Check if user has a specific permission
    """
    if user.is_superuser:
        return True
    
    perm_string = f"{resource}:{action}"
    user_permissions = get_user_permissions(user, db)
    
    # Check for exact match or wildcard
    return perm_string in user_permissions or "*" in user_permissions


def has_role(user: User, role_name: str) -> bool:
    """
    Check if user has a specific role
    """
    if user.is_superuser:
        return True
    
    return any(role.name == role_name for role in user.roles)


def require_permission(resource: str, action: str):
    """
    Dependency factory to require a specific permission
    """
    def permission_checker(
        db: DatabaseDep,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not has_permission(current_user, resource, action, db):
            raise ForbiddenError(
                f"Permission required: {resource}:{action}"
            )
        return current_user
    
    return permission_checker


def require_role(role_name: str):
    """
    Dependency factory to require a specific role
    """
    def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not has_role(current_user, role_name):
            raise ForbiddenError(
                f"Role required: {role_name}"
            )
        return current_user
    
    return role_checker


def require_any_role(*role_names: str):
    """
    Dependency factory to require any of the specified roles
    """
    def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not any(has_role(current_user, role_name) for role_name in role_names):
            raise ForbiddenError(
                f"One of these roles required: {', '.join(role_names)}"
            )
        return current_user
    
    return role_checker


def is_department_head(user: User, db: Session) -> Optional[int]:
    """
    Check if user is a department head and return their department_id.
    Returns None if user is not a department head.
    """
    from src.departments.model.department import Department
    department = db.query(Department).filter(Department.head_id == user.id).first()
    if department:
        return department.id
    return None


def require_department_head():
    """
    Dependency factory to require that user is a department head.
    Returns the department_id the user is head of.
    """
    def head_checker(
        db: DatabaseDep,
        current_user: User = Depends(get_current_active_user)
    ) -> tuple[User, int]:
        department_id = is_department_head(current_user, db)
        if department_id is None:
            raise ForbiddenError("User must be a department head")
        return current_user, department_id
    
    return head_checker
