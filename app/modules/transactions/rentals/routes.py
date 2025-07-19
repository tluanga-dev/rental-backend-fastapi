"""
Rentals Routes

API endpoints for rental-related operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.rentals.service import RentalsService
from app.modules.transactions.base.models import (
    TransactionStatus,
    PaymentStatus,
    RentalStatus,
)
from app.modules.transactions.rentals.schemas import (
    RentalResponse,
    NewRentalRequest,
    NewRentalResponse,
    RentableItemResponse,
    RentalPeriodUpdate,
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(tags=["rentals"])


def get_rentals_service(session: AsyncSession = Depends(get_session)) -> RentalsService:
    """Get rentals service instance."""
    return RentalsService(session)


@router.get("/", response_model=List[RentalResponse])
async def get_rental_transactions(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    location_id: Optional[UUID] = Query(None, description="Filter by location ID"),
    status: Optional[TransactionStatus] = Query(None, description="Filter by transaction status"),
    rental_status: Optional[RentalStatus] = Query(None, description="Filter by rental status"),
    date_from: Optional[date] = Query(None, description="Filter by rental start date (from)"),
    date_to: Optional[date] = Query(None, description="Filter by rental end date (to)"),
    overdue_only: bool = Query(False, description="Show only overdue rentals"),
    service: RentalsService = Depends(get_rentals_service),
):
    """
    Get rental transactions with comprehensive filtering options.
    
    This endpoint provides rental-specific filtering and includes lifecycle information:
    - Filter by customer, location, transaction status, or rental status
    - Filter by rental date range (start/end dates)
    - Show only overdue rentals
    - Includes rental lifecycle information (current status, fees, etc.)
    - Supports pagination
    
    Filters:
    - customer_id: Filter by specific customer UUID
    - location_id: Filter by specific location UUID  
    - status: Filter by transaction status (DRAFT, CONFIRMED, COMPLETED, etc.)
    - rental_status: Filter by rental status (ACTIVE, LATE, PARTIAL_RETURN, etc.)
    - date_from/date_to: Filter by rental start/end date range
    - overdue_only: Show only rentals that are past their end date
    
    Returns list of rental transactions with lifecycle information.
    """
    return await service.get_rental_transactions(
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        location_id=location_id,
        status=status,
        rental_status=rental_status,
        date_from=date_from,
        date_to=date_to,
        overdue_only=overdue_only,
    )


@router.get("/rentable-items", response_model=List[RentableItemResponse])
async def get_rentable_items(
    location_id: Optional[UUID] = Query(None, description="Filter by specific location"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    service: RentalsService = Depends(get_rentals_service),
):
    """
    Get rentable items with current stock availability by location.
    
    This endpoint returns all items that are:
    - Marked as rentable (is_rentable=True)
    - Active status
    - Have available quantity > 0 in at least one location
    
    The response includes:
    - Item details (SKU, name, rental rate, security deposit)
    - Total available quantity across all locations
    - Breakdown of availability by location
    - Related information (brand, category, unit of measurement)
    
    Use this endpoint when building rental forms to show available items.
    """
    return await service.get_rentable_items_with_availability(
        location_id=location_id,
        category_id=category_id,
        skip=skip,
        limit=limit
    )


@router.get("/{rental_id}", response_model=RentalResponse)
async def get_rental_by_id(
    rental_id: UUID, service: RentalsService = Depends(get_rentals_service)
):
    """Get a single rental transaction by ID with rental-specific format."""
    try:
        return await service.get_rental_by_id(rental_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/new", response_model=NewRentalResponse, status_code=status.HTTP_201_CREATED)
async def create_new_rental(
    rental_data: NewRentalRequest,
    service: RentalsService = Depends(get_rentals_service),
):
    """
    Create a new rental transaction with the simplified format.

    This endpoint accepts rental data in the exact format sent by the frontend:
    - transaction_date as string in YYYY-MM-DD format
    - customer_id as string UUID (must exist and be able to transact)
    - location_id as string UUID (must exist)
    - payment_method as string (CASH, CARD, BANK_TRANSFER, CHECK, ONLINE)
    - payment_reference as string (optional)
    - notes as string (optional)
    - items array with:
      * item_id as string UUID (must exist and be rentable)
      * quantity as integer (>=0, allows reservations)
      * rental_period_value as integer (>=0, number of days)
      * tax_rate as decimal (0-100, optional)
      * discount_amount as decimal (>=0, optional)
      * rental_start_date as string YYYY-MM-DD (item-specific)
      * rental_end_date as string YYYY-MM-DD (item-specific, must be after start)
      * notes as string (optional)

    Features:
    - Automatically fetches rental rates from item master data
    - Generates unique transaction numbers (REN-YYYYMMDD-XXXX)
    - Supports item-level rental date management
    - Comprehensive validation at header and line levels

    Returns a standardized response with success status, message, transaction data, and identifiers.
    """
    try:
        return await service.create_new_rental(rental_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/new-optimized", response_model=NewRentalResponse, status_code=status.HTTP_201_CREATED)
async def create_new_rental_optimized(
    rental_data: NewRentalRequest,
    service: RentalsService = Depends(get_rentals_service),
):
    """
    Create a new rental transaction with optimized batch processing.
    
    This is the optimized version of the new-rental endpoint that eliminates
    the 30+ second timeout issues by implementing:
    
    - Batch validation of all items in a single query
    - Bulk stock level lookups instead of individual queries
    - Single database transaction for all operations
    - Reduced database commits from N+1 to 1
    
    Expected performance improvement: 30+ seconds to <2 seconds (93% faster)
    
    Same input format as /new-rental but with dramatically improved performance.
    """
    try:
        return await service.create_new_rental_optimized(rental_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.put("/{rental_id}/extend", response_model=RentalResponse)
async def extend_rental_period(
    rental_id: UUID,
    extension_data: RentalPeriodUpdate,
    service: RentalsService = Depends(get_rentals_service),
):
    """Extend rental period."""
    try:
        return await service.extend_rental_period(rental_id, extension_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/reports/due-for-return", response_model=List[RentalResponse])
async def get_rentals_due_for_return(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: RentalsService = Depends(get_rentals_service),
):
    """Get rental transactions due for return."""
    return await service.get_rental_transactions_due_for_return(as_of_date)


@router.get("/reports/overdue", response_model=List[RentalResponse])
async def get_overdue_rentals(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: RentalsService = Depends(get_rentals_service),
):
    """Get overdue rental transactions."""
    return await service.get_overdue_rentals(as_of_date)