"""
Rental Returns Module

Handles all rental return operations including inspections, damage assessments, and deposit calculations.
"""

from app.modules.transactions.rental_returns.schemas import (
    RentalReturnLineItem,
    RentalReturnCreate,
    RentalReturnDetails,
    RentalInspectionCreate,
    RentalInspectionResponse,
    RentalReturnSummary,
    RentalDamageAssessment,
    RentalReturnFees,
)
from app.modules.transactions.rental_returns.service import RentalReturnsService
from app.modules.transactions.rental_returns.routes import router as rental_returns_router

__all__ = [
    # Schemas
    "RentalReturnLineItem",
    "RentalReturnCreate",
    "RentalReturnDetails",
    "RentalInspectionCreate",
    "RentalInspectionResponse",
    "RentalReturnSummary",
    "RentalDamageAssessment",
    "RentalReturnFees",
    # Service
    "RentalReturnsService",
    # Router
    "rental_returns_router",
]