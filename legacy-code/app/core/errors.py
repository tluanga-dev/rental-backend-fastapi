from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, DataError
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Business Logic Exceptions
class BusinessException(AppException):
    """Base exception for business logic errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class CacheError(AppException):
    """Exception raised for cache-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class ValidationError(AppException):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)}
        )


class DuplicateException(AppException):
    """Exception raised when attempting to create a duplicate resource."""
    
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource, "field": field, "value": str(value)}
        )


class ValidationException(AppException):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": errors or {}}
        )




# Domain-Specific Exceptions
class InsufficientStockException(BusinessException):
    """Exception raised when there's insufficient stock for an operation."""
    
    def __init__(self, item_id: str, requested: int, available: int):
        super().__init__(
            message="Insufficient stock available",
            details={
                "item_id": item_id,
                "requested_quantity": requested,
                "available_quantity": available
            }
        )


class InvalidStatusTransitionException(BusinessException):
    """Exception raised when an invalid status transition is attempted."""
    
    def __init__(self, entity: str, current_status: str, new_status: str):
        super().__init__(
            message=f"Cannot transition {entity} from {current_status} to {new_status}",
            details={
                "entity": entity,
                "current_status": current_status,
                "new_status": new_status
            }
        )


class RentalException(BusinessException):
    """Base exception for rental-related errors."""
    pass


class ItemNotAvailableException(RentalException):
    """Exception raised when an item is not available for rental."""
    
    def __init__(self, item_id: str, start_date: str, end_date: str):
        super().__init__(
            message="Item is not available for the requested period",
            details={
                "item_id": item_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )


class CustomerException(BusinessException):
    """Base exception for customer-related errors."""
    pass


class CustomerBlacklistedException(CustomerException):
    """Exception raised when a blacklisted customer attempts an operation."""
    
    def __init__(self, customer_id: str):
        super().__init__(
            message="Customer is blacklisted and cannot perform this operation",
            details={"customer_id": customer_id}
        )


class CreditLimitExceededException(CustomerException):
    """Exception raised when a customer exceeds their credit limit."""
    
    def __init__(self, customer_id: str, amount: float, credit_limit: float):
        super().__init__(
            message="Transaction exceeds customer credit limit",
            details={
                "customer_id": customer_id,
                "transaction_amount": amount,
                "credit_limit": credit_limit
            }
        )


class PaymentException(BusinessException):
    """Base exception for payment-related errors."""
    pass


class PaymentProcessingException(PaymentException):
    """Exception raised when payment processing fails."""
    
    def __init__(self, transaction_id: str, reason: str):
        super().__init__(
            message="Payment processing failed",
            details={
                "transaction_id": transaction_id,
                "reason": reason
            }
        )


class RefundException(PaymentException):
    """Exception raised when refund processing fails."""
    
    def __init__(self, transaction_id: str, reason: str):
        super().__init__(
            message="Refund processing failed",
            details={
                "transaction_id": transaction_id,
                "reason": reason
            }
        )


# Technical Exceptions
class DatabaseException(AppException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR"
        )


class ExternalServiceException(AppException):
    """Exception raised when an external service call fails."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )


class ConfigurationException(AppException):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Configuration error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR"
        )


# Exception Handlers
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    logger.error(f"Application error: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handle validation exceptions."""
    logger.warning(f"Validation error: {str(exc)}")
    
    if isinstance(exc, RequestValidationError):
        errors = exc.errors()
    else:
        errors = exc.errors() if hasattr(exc, 'errors') else [{"msg": str(exc)}]
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {"errors": errors}
            }
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors."""
    logger.error(f"Database integrity error: {str(exc)}")
    
    # Parse the error to provide a more user-friendly message
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "DUPLICATE_RESOURCE",
                    "message": "Resource already exists",
                    "details": {"error": error_msg}
                }
            }
        )
    elif "FOREIGN KEY constraint failed" in error_msg or "foreign key" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_REFERENCE",
                    "message": "Invalid reference to related resource",
                    "details": {"error": error_msg}
                }
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "Database operation failed",
                    "details": {"error": error_msg}
                }
            }
        )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": {}
            }
        }
    )


# Aliases for backward compatibility
NotFoundError = NotFoundException
ValidationError = ValidationException
ConflictError = DuplicateException
BusinessRuleError = BusinessException


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


def setup_exception_handlers(app):
    """Setup all exception handlers for the application."""
    register_exception_handlers(app)