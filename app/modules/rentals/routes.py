"""
Rental Routes

API endpoints for rental operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.transactions.base.models import TransactionStatus, RentalStatus
from app.modules.rentals.services import RentalsService
from app.modules.rentals.schemas import (
    RentalCreate,
    RentalUpdate,
    RentalResponse,
    RentalListResponse,
    RentalReportResponse,
    RentalDashboardResponse,
    RentalLifecycleResponse,
    RentalExtensionRequest,
    RentalCheckoutRequest,
    RentalCheckinRequest,
    RentalStatusUpdateRequest,
    RentalReportRequest,
)

router = APIRouter(prefix="/rentals", tags=["rentals"])


def get_rentals_service(session: AsyncSession = Depends(get_session)) -> RentalsService:
    """Get rentals service instance."""
    return RentalsService(session)


@router.post("/", response_model=RentalResponse)
async def create_rental(
    rental_data: RentalCreate,
    service: RentalsService = Depends(get_rentals_service)
):
    """Create a new rental."""
    try:
        return await service.create_rental(rental_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=RentalListResponse)
async def get_rentals(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    status: Optional[TransactionStatus] = Query(None),
    rental_status: Optional[RentalStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rentals with pagination and filters."""
    return await service.get_rentals(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        location_id=location_id,
        status=status,
        rental_status=rental_status,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/{rental_id}", response_model=RentalResponse)
async def get_rental(
    rental_id: UUID,
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rental by ID."""
    rental = await service.get_rental(rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental


@router.put("/{rental_id}", response_model=RentalResponse)
async def update_rental(
    rental_id: UUID,
    update_data: RentalUpdate,
    service: RentalsService = Depends(get_rentals_service)
):
    """Update rental."""
    rental = await service.update_rental(rental_id, update_data)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental


@router.delete("/{rental_id}")
async def delete_rental(
    rental_id: UUID,
    service: RentalsService = Depends(get_rentals_service)
):
    """Delete rental."""
    try:
        success = await service.delete_rental(rental_id)
        if not success:
            raise HTTPException(status_code=404, detail="Rental not found")
        return {"message": "Rental deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agreement/{agreement_number}", response_model=RentalResponse)
async def get_rental_by_agreement(
    agreement_number: str,
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rental by agreement number."""
    rental = await service.get_rental_by_agreement_number(agreement_number)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental


@router.post("/{rental_id}/extend", response_model=RentalResponse)
async def extend_rental(
    rental_id: UUID,
    extension_request: RentalExtensionRequest,
    service: RentalsService = Depends(get_rentals_service)
):
    """Extend rental period."""
    try:
        rental = await service.extend_rental(rental_id, extension_request)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        return rental
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rental_id}/checkout", response_model=RentalResponse)
async def checkout_rental(
    rental_id: UUID,
    checkout_request: RentalCheckoutRequest,
    service: RentalsService = Depends(get_rentals_service)
):
    """Process rental checkout."""
    rental = await service.checkout_rental(rental_id, checkout_request)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental


@router.post("/{rental_id}/checkin", response_model=RentalResponse)
async def checkin_rental(
    rental_id: UUID,
    checkin_request: RentalCheckinRequest,
    service: RentalsService = Depends(get_rentals_service)
):
    """Process rental checkin."""
    rental = await service.checkin_rental(rental_id, checkin_request)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental


@router.patch("/{rental_id}/status", response_model=RentalResponse)
async def update_rental_status(
    rental_id: UUID,
    status_update: RentalStatusUpdateRequest,
    service: RentalsService = Depends(get_rentals_service)
):
    """Update rental status."""
    rental = await service.update_rental_status(rental_id, status_update)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental


@router.get("/status/active", response_model=List[RentalResponse])
async def get_active_rentals(
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get active rentals."""
    return await service.get_active_rentals(
        customer_id=customer_id,
        location_id=location_id,
        limit=limit
    )


@router.get("/status/overdue", response_model=List[RentalResponse])
async def get_overdue_rentals(
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get overdue rentals."""
    return await service.get_overdue_rentals(
        customer_id=customer_id,
        location_id=location_id,
        limit=limit
    )


@router.get("/due/today", response_model=List[RentalResponse])
async def get_rentals_due_today(
    location_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rentals due today."""
    return await service.get_rentals_due_today(
        location_id=location_id,
        limit=limit
    )


@router.get("/due/week", response_model=List[RentalResponse])
async def get_rentals_due_this_week(
    location_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rentals due this week."""
    return await service.get_rentals_due_this_week(
        location_id=location_id,
        limit=limit
    )


@router.get("/customer/{customer_id}", response_model=RentalListResponse)
async def get_customer_rentals(
    customer_id: str,
    status: Optional[RentalStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rentals for a specific customer."""
    return await service.get_customer_rentals(
        customer_id=customer_id,
        status=status,
        page=page,
        page_size=page_size
    )


@router.get("/{rental_id}/lifecycle", response_model=RentalLifecycleResponse)
async def get_rental_lifecycle(
    rental_id: UUID,
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rental lifecycle information."""
    lifecycle = await service.get_rental_lifecycle(rental_id)
    if not lifecycle:
        raise HTTPException(status_code=404, detail="Rental lifecycle not found")
    return lifecycle


@router.post("/reports/rentals", response_model=RentalReportResponse)
async def generate_rental_report(
    report_request: RentalReportRequest,
    service: RentalsService = Depends(get_rentals_service)
):
    """Generate rental report."""
    return await service.get_rental_report(
        date_from=report_request.date_from,
        date_to=report_request.date_to,
        customer_id=report_request.customer_id,
        location_id=report_request.location_id,
        rental_status=report_request.rental_status
    )


@router.get("/dashboard/summary", response_model=RentalDashboardResponse)
async def get_rental_dashboard(
    location_id: Optional[str] = Query(None),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rental dashboard data."""
    return await service.get_rental_dashboard(location_id=location_id)


@router.get("/reports/summary")
async def get_rental_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    rental_status: Optional[RentalStatus] = Query(None),
    service: RentalsService = Depends(get_rentals_service)
):
    """Get rental summary statistics."""
    return await service.get_rental_report(
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        location_id=location_id,
        rental_status=rental_status
    )