from fastapi import HTTPException, status
from typing import Optional, Any


class CustomHTTPException(HTTPException):
    """Custom HTTP exception with additional error type"""
    
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[dict] = None,
        error_type: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_type = error_type or "GENERIC_ERROR"


class ValidationError(CustomHTTPException):
    """Validation error"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_type="VALIDATION_ERROR"
        )
        self.field = field


class NotFoundError(CustomHTTPException):
    """Resource not found error"""
    
    def __init__(self, resource: str, identifier: Any = None):
        detail = f"{resource} not found"
        if identifier:
            detail += f" with identifier: {identifier}"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_type="NOT_FOUND_ERROR"
        )


class AlreadyExistsError(CustomHTTPException):
    """Resource already exists error"""
    
    def __init__(self, resource: str, field: str, value: Any):
        detail = f"{resource} with {field} '{value}' already exists"
        
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_type="ALREADY_EXISTS_ERROR"
        )


class AuthenticationError(CustomHTTPException):
    """Authentication error"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
            error_type="AUTHENTICATION_ERROR"
        )


class AuthorizationError(CustomHTTPException):
    """Authorization error"""
    
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_type="AUTHORIZATION_ERROR"
        )


class InvalidCredentialsError(CustomHTTPException):
    """Invalid credentials error"""
    
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_type="INVALID_CREDENTIALS_ERROR"
        )


class DatabaseError(CustomHTTPException):
    """Database operation error"""
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_type="DATABASE_ERROR"
        )


class BusinessLogicError(CustomHTTPException):
    """Business logic error"""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_type="BUSINESS_LOGIC_ERROR"
        )