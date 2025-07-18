"""
Rent Return Routes

API endpoints for rent return operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.rent_returns.services import RentReturnsService
from app.modules.rent_returns.schemas import (
    RentReturnCreate,
    RentReturnUpdate,
    RentReturnResponse,
    RentReturnListResponse,
    RentReturnInspectionRequest,
    RentReturnInspectionResponse,
    DepositRefundRequest,
    DamageAssessmentRequest,
)

router = APIRouter(prefix="/rent-returns", tags=["rent-returns"])


def get_rent_returns_service(session: AsyncSession = Depends(get_session)) -> RentReturnsService:
    """Get rent returns service instance."""
    return RentReturnsService(session)


@router.post("/", response_model=RentReturnResponse)
async def create_rent_return(
    return_data: RentReturnCreate,
    service: RentReturnsService = Depends(get_rent_returns_service)
):
    """Create a new rent return."""
    return await service.create_rent_return(return_data)


@router.get("/", response_model=RentReturnListResponse)
async def get_rent_returns(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    customer_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: RentReturnsService = Depends(get_rent_returns_service)
):
    """Get rent returns with pagination and filters."""
    return await service.get_rent_returns(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        location_id=location_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/{return_id}", response_model=RentReturnResponse)
async def get_rent_return(
    return_id: UUID,
    service: RentReturnsService = Depends(get_rent_returns_service)
):
    """Get rent return by ID."""
    rent_return = await service.get_rent_return(return_id)
    if not rent_return:
        raise HTTPException(status_code=404, detail="Rent return not found")
    return rent_return


@router.post("/{return_id}/inspection", response_model=RentReturnInspectionResponse)
async def process_inspection(
    return_id: UUID,
    inspection_request: RentReturnInspectionRequest,
    service: RentReturnsService = Depends(get_rent_returns_service)
):
    """Process return inspection."""
    return await service.process_inspection(return_id, inspection_request)


@router.post("/{return_id}/refund", response_model=RentReturnResponse)
async def process_deposit_refund(
    return_id: UUID,
    refund_request: DepositRefundRequest,
    service: RentReturnsService = Depends(get_rent_returns_service)
):
    """Process deposit refund."""
    result = await service.process_deposit_refund(return_id, refund_request)
    if not result:
        raise HTTPException(status_code=404, detail="Rent return not found")
    return result


@router.get("/pending/inspections", response_model=List[RentReturnResponse])
async def get_pending_inspections(
    limit: int = Query(100, ge=1, le=1000),
    service: RentReturnsService = Depends(get_rent_returns_service)
):
    """Get returns with pending inspections."""
    return await service.get_pending_inspections(limit=limit)


@router.get("/damaged/list", response_model=List[RentReturnResponse])
async def get_damaged_returns(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: RentReturnsService = Depends(get_rent_returns_service)
):
    """Get returns with damage."""
    return await service.get_damaged_returns(
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )