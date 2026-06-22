"""
Custom exceptions
"""
from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    """Base exception for application"""
    pass


class NotFoundError(BaseAppException):
    """Resource not found exception"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with id: {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class DuplicateError(BaseAppException):
    """Duplicate resource exception"""
    def __init__(self, resource: str, field: str = None):
        message = f"{resource} already exists"
        if field:
            message += f" with {field}"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


class UnauthorizedError(BaseAppException):
    """Unauthorized access exception"""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(BaseAppException):
    """Forbidden access exception"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

