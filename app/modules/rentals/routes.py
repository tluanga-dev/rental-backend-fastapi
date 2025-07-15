"""
Rental-specific API endpoints for rental lifecycle management.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.rentals.rental_service import (
    RentalService, 
    RentalStatusService, 
    RentalReturnService
)
from app.modules.rentals.fee_calculator import RentalFeeCalculator
from app.modules.rentals.schemas_new import (
    RentalReturnInitiateRequest,
    RentalItemInspectionRequest,
    RentalReturnCompleteRequest,
    RentalExtensionRequest,
    RentalStatusUpdateRequest,
    BatchStatusUpdateRequest,
    RentalTransactionResponse,
    RentalDetailsResponse,
    RentalReturnEventResponse,
    RentalItemInspectionResponse,
    RentalListResponse,
    RentalDashboardResponse,
    RentalQueryParams,
    RentalFeeCalculation,
    BatchStatusUpdateResponse
)
from app.modules.transactions.models import RentalStatus, InspectionCondition
from app.core.errors import NotFoundError, ValidationError, ConflictError

router = APIRouter(tags=["Rental Management"])


def get_rental_service(session: AsyncSession = Depends(get_session)) -> RentalService:
    """Get rental service instance."""
    return RentalService(session)


def get_rental_status_service(session: AsyncSession = Depends(get_session)) -> RentalStatusService:
    """Get rental status service instance."""
    return RentalStatusService(session)


def get_rental_return_service(session: AsyncSession = Depends(get_session)) -> RentalReturnService:
    """Get rental return service instance."""
    return RentalReturnService(session)


def get_fee_calculator(session: AsyncSession = Depends(get_session)) -> RentalFeeCalculator:
    """Get fee calculator instance."""
    return RentalFeeCalculator(session)


# Rental listing and details endpoints
@router.get("/", response_model=RentalListResponse)
async def list_rentals(
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    status: Optional[RentalStatus] = Query(None, description="Filter by rental status"),
    overdue_only: bool = Query(False, description="Show only overdue rentals"),
    date_from: Optional[date] = Query(None, description="Filter by rental start date"),
    date_to: Optional[date] = Query(None, description="Filter by rental end date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: RentalService = Depends(get_rental_service),
):
    """
    List rental transactions with filtering and pagination.
    
    Supports filtering by:
    - Customer ID
    - Location ID
    - Rental status
    - Overdue status
    - Date range
    """
    try:
        rentals = await service.get_active_rentals(
            customer_id=customer_id,
            location_id=location_id,
            overdue_only=overdue_only
        )
        
        # Simple pagination for now (can be enhanced)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_rentals = rentals[start:end]
        
        total_pages = (len(rentals) + page_size - 1) // page_size
        
        return RentalListResponse(
            rentals=[RentalTransactionResponse.model_validate(r) for r in paginated_rentals],
            total_count=len(rentals),
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{transaction_id}", response_model=RentalDetailsResponse)
async def get_rental_details(
    transaction_id: UUID,
    service: RentalService = Depends(get_rental_service),
):
    """Get detailed information about a specific rental."""
    try:
        details = await service.get_rental_details(transaction_id)
        
        return RentalDetailsResponse(
            transaction=RentalTransactionResponse.model_validate(details['transaction']),
            lifecycle=details['lifecycle'],
            return_events=details['return_events'],
            inspections=[],  # Will be populated when we add inspection queries
            total_fees=details['total_fees'],
            is_overdue=details['is_overdue'],
            days_overdue=(date.today() - details['transaction'].rental_end_date).days if details['is_overdue'] else 0
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Rental status management endpoints
@router.patch("/{transaction_id}/status", response_model=RentalTransactionResponse)
async def update_rental_status(
    transaction_id: UUID,
    request: RentalStatusUpdateRequest,
    service: RentalStatusService = Depends(get_rental_status_service),
):
    """Update rental status manually."""
    try:
        await service.update_rental_status(
            transaction_id=transaction_id,
            new_status=request.new_status,
            notes=request.notes
        )
        
        # Get updated transaction
        updated_transaction = await service.get_rental_transaction(transaction_id)
        return RentalTransactionResponse.model_validate(updated_transaction)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/batch-status-update", response_model=BatchStatusUpdateResponse)
async def batch_update_rental_status(
    request: BatchStatusUpdateRequest,
    service: RentalStatusService = Depends(get_rental_status_service),
):
    """Update status for multiple rentals at once."""
    updated_transactions = []
    failed_transactions = []
    
    for transaction_id in request.transaction_ids:
        try:
            await service.update_rental_status(
                transaction_id=transaction_id,
                new_status=request.new_status,
                notes=request.notes
            )
            updated_transactions.append(transaction_id)
        except Exception as e:
            failed_transactions.append({
                "transaction_id": str(transaction_id),
                "error": str(e)
            })
    
    return BatchStatusUpdateResponse(
        updated_count=len(updated_transactions),
        failed_count=len(failed_transactions),
        failed_transactions=failed_transactions,
        updated_transactions=updated_transactions
    )


# Rental return process endpoints
@router.post("/{transaction_id}/returns/initiate", response_model=RentalReturnEventResponse)
async def initiate_rental_return(
    transaction_id: UUID,
    request: RentalReturnInitiateRequest,
    service: RentalReturnService = Depends(get_rental_return_service),
):
    """
    Initiate a rental return process.
    
    This creates a return event and validates that the items can be returned.
    After this, items need to be inspected before the return can be completed.
    """
    try:
        items_to_return = [
            {
                'transaction_line_id': str(item.transaction_line_id),
                'quantity': item.quantity
            }
            for item in request.items_to_return
        ]
        
        return_event = await service.initiate_return(
            transaction_id=transaction_id,
            return_date=request.return_date,
            items_to_return=items_to_return,
            notes=request.notes
        )
        
        return RentalReturnEventResponse.model_validate(return_event)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/returns/{return_event_id}/inspect", response_model=RentalItemInspectionResponse)
async def record_item_inspection(
    return_event_id: UUID,
    request: RentalItemInspectionRequest,
    service: RentalReturnService = Depends(get_rental_return_service),
):
    """
    Record inspection results for returned items.
    
    This should be called for each item or item group being inspected.
    Inspection results determine any damage fees and whether items can be restocked.
    """
    try:
        damage_details = None
        if request.inspection_details.has_damage:
            damage_details = {
                'description': request.inspection_details.damage_description,
                'photos': request.inspection_details.damage_photos or [],
                'damage_fee': request.inspection_details.damage_fee or 0,
                'cleaning_fee': request.inspection_details.cleaning_fee or 0,
                'replacement_required': request.inspection_details.replacement_required,
                'replacement_cost': request.inspection_details.replacement_cost,
                'notes': request.inspection_details.notes
            }
        
        inspection = await service.record_inspection(
            return_event_id=return_event_id,
            transaction_line_id=request.transaction_line_id,
            quantity_inspected=request.quantity_inspected,
            condition=request.inspection_details.condition,
            damage_details=damage_details
        )
        
        return RentalItemInspectionResponse.model_validate(inspection)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/returns/{return_event_id}/complete", response_model=RentalReturnEventResponse)
async def complete_rental_return(
    return_event_id: UUID,
    request: RentalReturnCompleteRequest,
    service: RentalReturnService = Depends(get_rental_return_service),
):
    """
    Complete a rental return with payment processing.
    
    This finalizes the return, processes payments/refunds, and updates rental status.
    Should be called after all items have been inspected.
    """
    try:
        return_event = await service.complete_return(
            return_event_id=return_event_id,
            payment_collected=request.payment_collected,
            refund_issued=request.refund_issued,
            receipt_number=request.receipt_number,
            notes=request.notes
        )
        
        return RentalReturnEventResponse.model_validate(return_event)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Rental extension endpoint
@router.post("/{transaction_id}/extend", response_model=RentalReturnEventResponse)
async def extend_rental_period(
    transaction_id: UUID,
    request: RentalExtensionRequest,
    service: RentalReturnService = Depends(get_rental_return_service),
):
    """
    Extend the rental period for a transaction.
    
    This creates an extension event and updates the expected return date.
    Can be used to prevent or resolve late status.
    """
    try:
        extension_event = await service.extend_rental(
            transaction_id=transaction_id,
            new_end_date=request.new_end_date,
            reason=request.reason,
            notes=request.notes
        )
        
        return RentalReturnEventResponse.model_validate(extension_event)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Utility endpoints
@router.post("/update-late-status", response_model=List[UUID])
async def update_overdue_rentals(
    as_of_date: Optional[date] = Query(None, description="Date to check against (defaults to today)"),
    service: RentalStatusService = Depends(get_rental_status_service),
):
    """
    Batch update rentals to LATE status if they're past due.
    
    This is typically called by a scheduled job but can be triggered manually.
    Returns list of transaction IDs that were updated.
    """
    try:
        updated_ids = await service.auto_update_late_status(as_of_date)
        return updated_ids
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/dashboard/stats", response_model=RentalDashboardResponse)
async def get_rental_dashboard_stats(
    service: RentalService = Depends(get_rental_service),
):
    """
    Get rental dashboard statistics.
    
    Provides summary statistics for rental management dashboard.
    """
    try:
        # Get active rentals
        active_rentals = await service.get_active_rentals()
        
        # Calculate statistics
        total_active = len(active_rentals)
        overdue_count = sum(1 for r in active_rentals if r.rental_end_date and r.rental_end_date < date.today())
        partial_returns = sum(1 for r in active_rentals if r.current_rental_status in ['PARTIAL_RETURN', 'LATE_PARTIAL_RETURN'])
        
        # For now, return mock data for fees (would need additional queries for real data)
        return RentalDashboardResponse(
            active_rentals=total_active,
            overdue_rentals=overdue_count,
            partial_returns=partial_returns,
            completed_today=0,  # Would need query for today's completions
            total_fees_pending=0,  # Would need lifecycle fee aggregation
            total_fees_collected_today=0  # Would need today's payment aggregation
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Fee calculation endpoint
@router.get("/{transaction_id}/calculate-fees", response_model=RentalFeeCalculation)
async def calculate_rental_fees(
    transaction_id: UUID,
    as_of_date: Optional[date] = Query(None, description="Calculate fees as of this date"),
    calculator: RentalFeeCalculator = Depends(get_fee_calculator),
):
    """
    Calculate current fees for a rental.
    
    This provides a breakdown of all fees including late fees, damage fees, etc.
    Useful for showing customers what they owe before completing a return.
    """
    try:
        fee_info = await calculator.calculate_total_rental_fees(transaction_id, as_of_date)
        
        return RentalFeeCalculation(
            base_amount=fee_info['base_rental_amount'],
            late_fee_days=fee_info['late_fee_info']['late_fee_days'],
            late_fee_rate=fee_info['late_fee_info'].get('late_fee_rate', 0),
            late_fee_amount=fee_info['total_late_fees'],
            damage_fees=fee_info['accumulated_damage_fees'],
            other_fees=fee_info['accumulated_other_fees'],
            total_fees=fee_info['total_fees'],
            deposit_credit=fee_info['deposit_credit'],
            advance_payment_credit=fee_info['advance_payment_credit'],
            amount_due=fee_info['amount_due']
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))