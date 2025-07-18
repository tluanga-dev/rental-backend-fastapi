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
]