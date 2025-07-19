"""
Simplified Rentals Routes

Streamlined API endpoints for rental operations.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.rentals.service_simplified import SimplifiedRentalsService
from app.modules.transactions.rentals.schemas import (
    RentalResponse,
    NewRentalRequest,
    NewRentalResponse,
)
from app.core.errors import NotFoundError, ValidationError, ConflictError

router = APIRouter(tags=["rentals-simplified"])


def get_rentals_service(session: AsyncSession = Depends(get_session)) -> SimplifiedRentalsService:
    """Get simplified rentals service instance."""
    return SimplifiedRentalsService(session)


@router.post("/", response_model=NewRentalResponse, status_code=status.HTTP_201_CREATED)
async def create_rental(
    rental_data: NewRentalRequest,
    service: SimplifiedRentalsService = Depends(get_rentals_service),
):
    """
    Create a new rental transaction - simplified endpoint.
    
    This is a streamlined version that:
    - Uses a single optimized method
    - Reduces complexity while maintaining functionality
    - Provides consistent performance
    """
    try:
        return await service.create_rental(rental_data)
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


@router.get("/{rental_id}", response_model=RentalResponse)
async def get_rental(
    rental_id: UUID, 
    service: SimplifiedRentalsService = Depends(get_rentals_service)
):
    """Get a single rental transaction by ID."""
    try:
        return await service.get_rental(rental_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=List[RentalResponse])
async def get_rentals(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    location_id: Optional[UUID] = Query(None, description="Filter by location ID"),
    service: SimplifiedRentalsService = Depends(get_rentals_service),
):
    """Get rental transactions with basic filtering."""
    return await service.get_rentals(
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        location_id=location_id,
    )
