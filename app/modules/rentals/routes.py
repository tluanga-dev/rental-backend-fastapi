from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.shared.dependencies import get_session
from app.modules.rentals.service import RentalService
from app.modules.rentals.schemas import (
    RentalReturnCreate, RentalReturnUpdate, RentalReturnResponse,
    RentalReturnListResponse, RentalReturnWithLinesResponse,
    RentalReturnLineCreate, RentalReturnLineUpdate, RentalReturnLineResponse,
    InspectionReportCreate, InspectionReportUpdate, InspectionReportResponse,
    ReturnStatusUpdate, LineStatusUpdate, DamageAssessment, FeeCalculation,
    DepositCalculation, InspectionCompletion, InspectionFailure,
    RentalReturnSummary, RentalReturnReport, RentalReturnSearch,
    RentalDashboard, RentalAnalytics
)
from app.modules.rentals.models import ReturnStatus, ReturnType, DamageLevel, InspectionStatus


router = APIRouter(prefix="/rentals", tags=["Rental Operations"])


# Import the rental service dependency
from app.shared.dependencies import get_rental_service


# Rental Return endpoints
@router.post("/returns", response_model=RentalReturnResponse, status_code=status.HTTP_201_CREATED)
async def create_rental_return(
    return_data: RentalReturnCreate,
    service: RentalService = Depends(get_rental_service)
):
    """Create a new rental return."""
    try:
        return await service.create_rental_return(return_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/returns/{return_id}", response_model=RentalReturnResponse)
async def get_rental_return(
    return_id: UUID,
    service: RentalService = Depends(get_rental_service)
):
    """Get rental return by ID."""
    try:
        return await service.get_rental_return(return_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/returns/{return_id}/with-lines", response_model=RentalReturnWithLinesResponse)
async def get_rental_return_with_lines(
    return_id: UUID,
    service: RentalService = Depends(get_rental_service)
):
    """Get rental return with lines and inspection reports."""
    try:
        return await service.get_rental_return_with_lines(return_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/returns", response_model=List[RentalReturnListResponse])
async def get_rental_returns(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    return_type: Optional[ReturnType] = Query(None, description="Filter by return type"),
    return_status: Optional[ReturnStatus] = Query(None, description="Filter by return status"),
    return_location_id: Optional[UUID] = Query(None, description="Filter by return location"),
    processed_by: Optional[UUID] = Query(None, description="Filter by processor"),
    date_from: Optional[date] = Query(None, description="Filter by return date from"),
    date_to: Optional[date] = Query(None, description="Filter by return date to"),
    active_only: bool = Query(True, description="Only active returns"),
    service: RentalService = Depends(get_rental_service)
):
    """Get all rental returns with optional filtering."""
    try:
        return await service.get_rental_returns(
            skip=skip,
            limit=limit,
            return_type=return_type,
            return_status=return_status,
            return_location_id=return_location_id,
            processed_by=processed_by,
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/returns/search", response_model=List[RentalReturnListResponse])
async def search_rental_returns(
    search_params: RentalReturnSearch,
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    active_only: bool = Query(True, description="Only active returns"),
    service: RentalService = Depends(get_rental_service)
):
    """Search rental returns."""
    try:
        return await service.search_rental_returns(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/returns/{return_id}", response_model=RentalReturnResponse)
async def update_rental_return(
    return_id: UUID,
    return_data: RentalReturnUpdate,
    service: RentalService = Depends(get_rental_service)
):
    """Update a rental return."""
    try:
        return await service.update_rental_return(return_id, return_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/returns/{return_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rental_return(
    return_id: UUID,
    service: RentalService = Depends(get_rental_service)
):
    """Delete a rental return."""
    try:
        success = await service.delete_rental_return(return_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/returns/{return_id}/status", response_model=RentalReturnResponse)
async def update_return_status(
    return_id: UUID,
    status_update: ReturnStatusUpdate,
    service: RentalService = Depends(get_rental_service)
):
    """Update return status."""
    try:
        return await service.update_return_status(return_id, status_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/returns/{return_id}/finalize", response_model=RentalReturnResponse)
async def finalize_return(
    return_id: UUID,
    service: RentalService = Depends(get_rental_service)
):
    """Finalize the return process."""
    try:
        return await service.finalize_return(return_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/returns/{return_id}/cancel", response_model=RentalReturnResponse)
async def cancel_return(
    return_id: UUID,
    reason: str = Query(..., description="Cancellation reason"),
    service: RentalService = Depends(get_rental_service)
):
    """Cancel rental return."""
    try:
        return await service.cancel_return(return_id, reason)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Rental Return Line endpoints
@router.post("/returns/{return_id}/lines", response_model=RentalReturnLineResponse, status_code=status.HTTP_201_CREATED)
async def add_return_line(
    return_id: UUID,
    line_data: RentalReturnLineCreate,
    service: RentalService = Depends(get_rental_service)
):
    """Add line to rental return."""
    try:
        return await service.add_return_line(return_id, line_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/returns/{return_id}/lines", response_model=List[RentalReturnLineResponse])
async def get_return_lines(
    return_id: UUID,
    active_only: bool = Query(True, description="Only active lines"),
    service: RentalService = Depends(get_rental_service)
):
    """Get return lines."""
    try:
        return await service.get_return_lines(return_id, active_only)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/lines/{line_id}", response_model=RentalReturnLineResponse)
async def get_return_line(
    line_id: UUID,
    service: RentalService = Depends(get_rental_service)
):
    """Get return line by ID."""
    try:
        return await service.get_return_line(line_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/lines/{line_id}", response_model=RentalReturnLineResponse)
async def update_return_line(
    line_id: UUID,
    line_data: RentalReturnLineUpdate,
    service: RentalService = Depends(get_rental_service)
):
    """Update return line."""
    try:
        return await service.update_return_line(line_id, line_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_return_line(
    line_id: UUID,
    service: RentalService = Depends(get_rental_service)
):
    """Delete return line."""
    try:
        success = await service.delete_return_line(line_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line not found")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/lines/{line_id}/status", response_model=RentalReturnLineResponse)
async def update_line_status(
    line_id: UUID,
    status_update: LineStatusUpdate,
    service: RentalService = Depends(get_rental_service)
):
    """Update return line status."""
    try:
        return await service.update_line_status(line_id, status_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/lines/{line_id}/assess-damage", response_model=RentalReturnLineResponse)
async def assess_damage(
    line_id: UUID,
    damage_assessment: DamageAssessment,
    service: RentalService = Depends(get_rental_service)
):
    """Assess damage for return line."""
    try:
        return await service.assess_damage(line_id, damage_assessment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/lines/{line_id}/calculate-fees", response_model=RentalReturnLineResponse)
async def calculate_fees(
    line_id: UUID,
    fee_calculation: FeeCalculation,
    service: RentalService = Depends(get_rental_service)
):
    """Calculate fees for return line."""
    try:
        return await service.calculate_fees(line_id, fee_calculation)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Inspection Report endpoints
@router.post("/returns/{return_id}/inspections", response_model=InspectionReportResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection_report(
    return_id: UUID,
    report_data: InspectionReportCreate,
    service: RentalService = Depends(get_rental_service)
):
    """Create inspection report."""
    try:
        return await service.create_inspection_report(return_id, report_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/returns/{return_id}/inspections", response_model=List[InspectionReportResponse])
async def get_inspection_reports(
    return_id: UUID,
    active_only: bool = Query(True, description="Only active reports"),
    service: RentalService = Depends(get_rental_service)
):
    """Get inspection reports for return."""
    try:
        return await service.get_inspection_reports(return_id, active_only)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/inspections/{report_id}", response_model=InspectionReportResponse)
async def get_inspection_report(
    report_id: UUID,
    service: RentalService = Depends(get_rental_service)
):
    """Get inspection report by ID."""
    try:
        return await service.get_inspection_report(report_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/inspections/{report_id}", response_model=InspectionReportResponse)
async def update_inspection_report(
    report_id: UUID,
    report_data: InspectionReportUpdate,
    service: RentalService = Depends(get_rental_service)
):
    """Update inspection report."""
    try:
        return await service.update_inspection_report(report_id, report_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/inspections/{report_id}/complete", response_model=InspectionReportResponse)
async def complete_inspection(
    report_id: UUID,
    completion_data: InspectionCompletion,
    service: RentalService = Depends(get_rental_service)
):
    """Complete inspection."""
    try:
        return await service.complete_inspection(report_id, completion_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/inspections/{report_id}/fail", response_model=InspectionReportResponse)
async def fail_inspection(
    report_id: UUID,
    failure_data: InspectionFailure,
    service: RentalService = Depends(get_rental_service)
):
    """Fail inspection."""
    try:
        return await service.fail_inspection(report_id, failure_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Dashboard and Reporting endpoints
@router.get("/dashboard", response_model=RentalDashboard)
async def get_rental_dashboard(
    service: RentalService = Depends(get_rental_service)
):
    """Get rental dashboard data."""
    try:
        return await service.get_rental_dashboard()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/summary", response_model=RentalReturnSummary)
async def get_rental_return_summary(
    date_from: Optional[date] = Query(None, description="Summary date from"),
    date_to: Optional[date] = Query(None, description="Summary date to"),
    active_only: bool = Query(True, description="Only active returns"),
    service: RentalService = Depends(get_rental_service)
):
    """Get rental return summary."""
    try:
        return await service.get_rental_return_summary(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/detailed", response_model=RentalReturnReport)
async def get_rental_return_report(
    date_from: Optional[date] = Query(None, description="Report date from"),
    date_to: Optional[date] = Query(None, description="Report date to"),
    active_only: bool = Query(True, description="Only active returns"),
    service: RentalService = Depends(get_rental_service)
):
    """Get rental return report."""
    try:
        return await service.get_rental_return_report(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/overdue", response_model=List[RentalReturnListResponse])
async def get_overdue_returns(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: RentalService = Depends(get_rental_service)
):
    """Get overdue returns."""
    try:
        return await service.get_overdue_returns(as_of_date)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/due-today", response_model=List[RentalReturnListResponse])
async def get_returns_due_today(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: RentalService = Depends(get_rental_service)
):
    """Get returns due today."""
    try:
        return await service.get_returns_due_today(as_of_date)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/pending-inspections", response_model=List[InspectionReportResponse])
async def get_pending_inspections(
    service: RentalService = Depends(get_rental_service)
):
    """Get pending inspections."""
    try:
        return await service.get_pending_inspections()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Health check endpoint
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for rental operations."""
    return {"status": "healthy", "service": "rental-operations"}