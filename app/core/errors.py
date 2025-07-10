"""Core error classes for the application."""

from typing import Optional, Dict, Any


class BaseError(Exception):
    """Base exception class for application errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(BaseError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, "NOT_FOUND_ERROR", details)


class ConflictError(BaseError):
    """Raised when an operation conflicts with existing data."""
    
    def __init__(self, message: str, conflicting_field: Optional[str] = None, conflicting_value: Optional[str] = None):
        self.conflicting_field = conflicting_field
        self.conflicting_value = conflicting_value
        details = {}
        if conflicting_field:
            details["conflicting_field"] = conflicting_field
        if conflicting_value:
            details["conflicting_value"] = conflicting_value
        super().__init__(message, "CONFLICT_ERROR", details)


class BusinessRuleError(BaseError):
    """Raised when a business rule is violated."""
    
    def __init__(self, message: str, rule_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.rule_name = rule_name
        self.context = context or {}
        details = {"context": self.context}
        if rule_name:
            details["rule_name"] = rule_name
        super().__init__(message, "BUSINESS_RULE_ERROR", details)


class AuthenticationError(BaseError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(BaseError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", required_permission: Optional[str] = None):
        self.required_permission = required_permission
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class DatabaseError(BaseError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        self.operation = operation
        self.table = table
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        super().__init__(message, "DATABASE_ERROR", details)


# Export all error classes
__all__ = [
    "BaseError",
    "ValidationError",
    "NotFoundError", 
    "ConflictError",
    "BusinessRuleError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseError"
]