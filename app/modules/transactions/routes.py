from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.service import TransactionService
from app.modules.transactions.models import TransactionType, TransactionStatus, PaymentStatus
from app.modules.transactions.schemas import (
    TransactionHeaderCreate, TransactionHeaderUpdate, TransactionHeaderResponse,
    TransactionHeaderListResponse, TransactionWithLinesResponse,
    TransactionLineCreate, TransactionLineUpdate, TransactionLineResponse,
    TransactionLineListResponse, PaymentCreate, RefundCreate, StatusUpdate,
    DiscountApplication, ReturnProcessing, RentalPeriodUpdate, RentalReturn,
    TransactionSummary, TransactionReport, TransactionSearch
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_service(session: AsyncSession = Depends(get_session)) -> TransactionService:
    """Get transaction service instance."""
    return TransactionService(session)


# Transaction Header endpoints
@router.post("/", response_model=TransactionHeaderResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionHeaderCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Create a new transaction."""
    try:
        return await service.create_transaction(transaction_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionHeaderResponse)
async def get_transaction(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction by ID."""
    try:
        return await service.get_transaction(transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/number/{transaction_number}", response_model=TransactionHeaderResponse)
async def get_transaction_by_number(
    transaction_number: str,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction by number."""
    try:
        return await service.get_transaction_by_number(transaction_number)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{transaction_id}/with-lines", response_model=TransactionWithLinesResponse)
async def get_transaction_with_lines(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction with lines."""
    try:
        return await service.get_transaction_with_lines(transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=List[TransactionHeaderListResponse])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    customer_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    sales_person_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    active_only: bool = Query(True),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get all transactions with optional filtering."""
    return await service.get_transactions(
        skip=skip,
        limit=limit,
        transaction_type=transaction_type,
        status=status,
        payment_status=payment_status,
        customer_id=customer_id,
        location_id=location_id,
        sales_person_id=sales_person_id,
        date_from=date_from,
        date_to=date_to,
        active_only=active_only
    )


@router.post("/search", response_model=List[TransactionHeaderListResponse])
async def search_transactions(
    search_params: TransactionSearch,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    service: TransactionService = Depends(get_transaction_service)
):
    """Search transactions."""
    return await service.search_transactions(
        search_params=search_params,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.put("/{transaction_id}", response_model=TransactionHeaderResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionHeaderUpdate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Update a transaction."""
    try:
        return await service.update_transaction(transaction_id, transaction_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service)
):
    """Delete a transaction."""
    try:
        success = await service.delete_transaction(transaction_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{transaction_id}/status", response_model=TransactionHeaderResponse)
async def update_transaction_status(
    transaction_id: UUID,
    status_update: StatusUpdate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Update transaction status."""
    try:
        return await service.update_transaction_status(transaction_id, status_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{transaction_id}/payments", response_model=TransactionHeaderResponse)
async def apply_payment(
    transaction_id: UUID,
    payment_data: PaymentCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Apply payment to transaction."""
    try:
        return await service.apply_payment(transaction_id, payment_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{transaction_id}/refunds", response_model=TransactionHeaderResponse)
async def process_refund(
    transaction_id: UUID,
    refund_data: RefundCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Process refund for transaction."""
    try:
        return await service.process_refund(transaction_id, refund_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{transaction_id}/cancel", response_model=TransactionHeaderResponse)
async def cancel_transaction(
    transaction_id: UUID,
    reason: str = Query(..., description="Cancellation reason"),
    service: TransactionService = Depends(get_transaction_service)
):
    """Cancel transaction."""
    try:
        return await service.cancel_transaction(transaction_id, reason)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{transaction_id}/overdue", response_model=TransactionHeaderResponse)
async def mark_transaction_overdue(
    transaction_id: UUID,
    service: TransactionService = Depends(get_transaction_service)
):
    """Mark transaction as overdue."""
    try:
        return await service.mark_transaction_overdue(transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{transaction_id}/rental-return", response_model=TransactionHeaderResponse)
async def complete_rental_return(
    transaction_id: UUID,
    return_data: RentalReturn,
    service: TransactionService = Depends(get_transaction_service)
):
    """Complete rental return."""
    try:
        return await service.complete_rental_return(transaction_id, return_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Transaction Line endpoints
@router.post("/{transaction_id}/lines", response_model=TransactionLineResponse, status_code=status.HTTP_201_CREATED)
async def add_transaction_line(
    transaction_id: UUID,
    line_data: TransactionLineCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Add line to transaction."""
    try:
        return await service.add_transaction_line(transaction_id, line_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/lines/{line_id}", response_model=TransactionLineResponse)
async def get_transaction_line(
    line_id: UUID,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction line by ID."""
    try:
        return await service.get_transaction_line(line_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{transaction_id}/lines", response_model=List[TransactionLineResponse])
async def get_transaction_lines(
    transaction_id: UUID,
    active_only: bool = Query(True),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction lines."""
    return await service.get_transaction_lines(transaction_id, active_only)


@router.put("/lines/{line_id}", response_model=TransactionLineResponse)
async def update_transaction_line(
    line_id: UUID,
    line_data: TransactionLineUpdate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Update transaction line."""
    try:
        return await service.update_transaction_line(line_id, line_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction_line(
    line_id: UUID,
    service: TransactionService = Depends(get_transaction_service)
):
    """Delete transaction line."""
    try:
        success = await service.delete_transaction_line(line_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction line not found")
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/lines/{line_id}/discount", response_model=TransactionLineResponse)
async def apply_line_discount(
    line_id: UUID,
    discount_data: DiscountApplication,
    service: TransactionService = Depends(get_transaction_service)
):
    """Apply discount to transaction line."""
    try:
        return await service.apply_line_discount(line_id, discount_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/lines/{line_id}/returns", response_model=TransactionLineResponse)
async def process_line_return(
    line_id: UUID,
    return_data: ReturnProcessing,
    service: TransactionService = Depends(get_transaction_service)
):
    """Process return for transaction line."""
    try:
        return await service.process_line_return(line_id, return_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/lines/{line_id}/rental-period", response_model=TransactionLineResponse)
async def update_rental_period(
    line_id: UUID,
    period_update: RentalPeriodUpdate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Update rental period for transaction line."""
    try:
        return await service.update_rental_period(line_id, period_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Reporting endpoints
@router.get("/reports/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    active_only: bool = Query(True),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction summary."""
    return await service.get_transaction_summary(
        date_from=date_from,
        date_to=date_to,
        active_only=active_only
    )


@router.get("/reports/full", response_model=TransactionReport)
async def get_transaction_report(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    active_only: bool = Query(True),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction report."""
    return await service.get_transaction_report(
        date_from=date_from,
        date_to=date_to,
        active_only=active_only
    )


@router.get("/reports/overdue", response_model=List[TransactionHeaderListResponse])
async def get_overdue_transactions(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get overdue transactions."""
    return await service.get_overdue_transactions(as_of_date)


@router.get("/reports/outstanding", response_model=List[TransactionHeaderListResponse])
async def get_outstanding_transactions(
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transactions with outstanding balance."""
    return await service.get_outstanding_transactions()


@router.get("/reports/due-for-return", response_model=List[TransactionHeaderListResponse])
async def get_rental_transactions_due_for_return(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get rental transactions due for return."""
    return await service.get_rental_transactions_due_for_return(as_of_date)