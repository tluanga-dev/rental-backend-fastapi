"""
Rentals Module

This module handles all rental-related operations including rental creation,
lifecycle management, extensions, and rental status tracking.
"""

from app.modules.rentals.services import RentalsService
from app.modules.rentals.repository import RentalsRepository
from app.modules.rentals.schemas import (
    RentalCreate,
    RentalResponse,
    RentalUpdate,
    RentalLifecycleResponse,
    RentalListResponse,
    RentalExtensionRequest,
)

__all__ = [
    "RentalsService",
    "RentalsRepository", 
    "RentalCreate",
    "RentalResponse",
    "RentalUpdate",
    "RentalLifecycleResponse",
    "RentalListResponse",
    "RentalExtensionRequest",
]