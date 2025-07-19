"""
Rentals Module

Handles all rental-related transactions including creation, retrieval, and returns.
"""

from app.modules.transactions.rentals.schemas import (
    RentalResponse,
    NewRentalRequest,
    NewRentalResponse,
    RentalItemCreate,
    RentalLineItemResponse,
    RentalDetail,
    RentalListResponse,
    CustomerNestedResponse,
    LocationNestedResponse,
    ItemNestedResponse,
    RentableItemResponse,
    LocationAvailability,
    BrandNested,
    CategoryNested,
    UnitOfMeasurementNested,
    RentalPeriodUpdate,
)
from app.modules.transactions.rentals.services import RentalsService
from app.modules.transactions.rentals.repository import RentalsRepository
from app.modules.transactions.rentals.routes import router as rentals_router

__all__ = [
    # Schemas
    "RentalResponse",
    "NewRentalRequest",
    "NewRentalResponse",
    "RentalItemCreate",
    "RentalLineItemResponse",
    "RentalDetail",
    "RentalListResponse",
    "CustomerNestedResponse",
    "LocationNestedResponse",
    "ItemNestedResponse",
    "RentableItemResponse",
    "LocationAvailability",
    "BrandNested",
    "CategoryNested",
    "UnitOfMeasurementNested",
    "RentalPeriodUpdate",
    # Service and Repository
    "RentalsService",
    "RentalsRepository",
    # Router
    "rentals_router",
]