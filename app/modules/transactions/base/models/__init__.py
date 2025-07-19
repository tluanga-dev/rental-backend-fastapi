"""
Transaction models package - organized for better maintainability.
"""

# Import core models from their respective files
from .transaction_headers import (
    TransactionHeader,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    PaymentStatus,
    RentalPeriodUnit,
    RentalStatus,
)

from .transaction_lines import (
    TransactionLine,
    LineItemType,
)


# Import additional models
from .metadata import TransactionMetadata
from .inspections import RentalInspection, PurchaseCreditMemo
from .events import TransactionEvent
from .rental_lifecycle import (
    RentalLifecycle, 
    RentalReturnEvent, 
    RentalItemInspection,
    RentalStatusLog,
    ReturnEventType,
    InspectionCondition,
    RentalStatusChangeReason
)

# Export all models for backward compatibility
__all__ = [
    # Core enums
    "TransactionType",
    "TransactionStatus", 
    "PaymentMethod",
    "PaymentStatus",
    "RentalPeriodUnit",
    "RentalStatus",
    "LineItemType",
    
    # Core models
    "TransactionHeader",
    "TransactionLine",
    
    # Additional models
    "TransactionMetadata",
    "TransactionEvent",
    "RentalInspection",
    "PurchaseCreditMemo",
    
    # Rental lifecycle models
    "RentalLifecycle",
    "RentalReturnEvent", 
    "RentalItemInspection",
    "RentalStatusLog",
    "ReturnEventType",
    "InspectionCondition",
    "RentalStatusChangeReason"
]