"""
Rental Returns Routes

API endpoints for rental return operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.rental_returns.service import RentalReturnsService
from app.modules.transactions.rental_returns.schemas import (
    RentalReturn,
    RentalReturnCreate,
    RentalReturnDetails,
    RentalInspectionCreate,
    RentalInspectionResponse,
    RentalReturnSummary,
    RentalDamageAssessment,
    RentalReturnFees,
)
from app.modules.transactions.schemas import TransactionWithLinesResponse
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(tags=["rental-returns"])


def get_rental_returns_service(session: AsyncSession = Depends(get_session)) -> RentalReturnsService:
    """Get rental returns service instance."""
    return RentalReturnsService(session)


@router.post("/", response_model=TransactionWithLinesResponse, status_code=status.HTTP_201_CREATED)
async def create_rental_return(
    return_data: RentalReturnCreate,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """
    Create a rental return transaction.
    
    This endpoint processes rental returns, including:
    - Late fee calculations
    - Damage assessments
    - Cleaning fees
    - Deposit calculations and refunds
    - Inspection requirements
    """
    try:
        return await service.create_rental_return(return_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating rental return: {str(e)}"
        )


@router.post("/{rental_id}/quick-return", response_model=Dict[str, Any])
async def quick_rental_return(
    rental_id: UUID,
    return_data: RentalReturn,
    service: RentalReturnsService = Depends(get_rental_returns_service),
):
    """
    Quick rental return for simple cases.
    
    Use this endpoint for straightforward returns without detailed inspection.
    """
    try:
        return await service.quick_rental_return(rental_id, return_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{return_id}", response_model=RentalReturnDetails)
async def get_rental_return_details(
    return_id: UUID,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """
    Get comprehensive rental return details.
    
    Returns all information about a rental return transaction,
    including fees, damages, and inspection results.
    """
    try:
        return await service.get_rental_return_details(return_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{return_id}/summary", response_model=RentalReturnSummary)
async def get_rental_return_summary(
    return_id: UUID,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """
    Get financial summary of rental return.
    
    Provides a breakdown of all fees, deductions, and refunds.
    """
    try:
        return await service.get_rental_return_summary(return_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{return_id}/inspection", response_model=RentalInspectionResponse)
async def create_rental_inspection(
    return_id: UUID,
    inspection_data: RentalInspectionCreate,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """
    Submit inspection results for a rental return.
    
    This endpoint allows recording inspection findings for rental returns,
    including damage assessments and repair cost estimates.
    """
    try:
        # Ensure return_id matches
        inspection_data.return_id = return_id
        return await service.create_rental_inspection(inspection_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{return_id}/inspection", response_model=RentalInspectionResponse)
async def get_rental_inspection(
    return_id: UUID,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """
    Get inspection results for a rental return.
    
    This endpoint retrieves existing inspection data for a rental return.
    """
    try:
        inspection = await service.get_rental_inspection(return_id)
        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No inspection found for this return"
            )
        return inspection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rental inspection: {str(e)}"
        )


@router.put("/{return_id}/inspection", response_model=RentalInspectionResponse)
async def update_rental_inspection(
    return_id: UUID,
    inspection_data: RentalInspectionCreate,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """Update existing rental inspection."""
    try:
        inspection_data.return_id = return_id
        return await service.update_rental_inspection(inspection_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{return_id}/damages", response_model=List[RentalDamageAssessment])
async def get_damage_assessments(
    return_id: UUID,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """Get all damage assessments for a rental return."""
    try:
        return await service.get_damage_assessments(return_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{return_id}/fees", response_model=RentalReturnFees)
async def get_rental_return_fees(
    return_id: UUID,
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """Get detailed fee breakdown for a rental return."""
    try:
        return await service.calculate_rental_return_fees(return_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{return_id}/approve-deposit-refund", response_model=Dict[str, Any])
async def approve_deposit_refund(
    return_id: UUID,
    approved_by: UUID = Query(..., description="User approving the refund"),
    refund_amount: Optional[Decimal] = Query(None, description="Override refund amount"),
    notes: Optional[str] = Query(None, description="Approval notes"),
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """
    Approve deposit refund for rental return.
    
    This finalizes the deposit refund amount and updates the return status.
    """
    try:
        return await service.approve_deposit_refund(
            return_id=return_id,
            approved_by=approved_by,
            refund_amount=refund_amount,
            notes=notes
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/reports/pending-inspections", response_model=List[Dict[str, Any]])
async def get_pending_inspections(
    days_old: int = Query(7, description="Returns older than X days"),
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """Get rental returns pending inspection."""
    return await service.get_pending_inspections(days_old)


@router.get("/reports/deposit-summary")
async def get_deposit_summary(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    service: RentalReturnsService = Depends(get_rental_returns_service)
):
    """Get summary of deposit refunds and deductions."""
    return await service.get_deposit_summary(date_from, date_to)