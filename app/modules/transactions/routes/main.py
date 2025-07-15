from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.service import TransactionService
from app.modules.transactions.models import (
    TransactionType,
    TransactionStatus,
    PaymentStatus,
    LineItemType,
)
from app.modules.transactions.schemas import (
    TransactionHeaderCreate,
    TransactionHeaderUpdate,
    TransactionHeaderResponse,
    TransactionHeaderListResponse,
    TransactionHeaderWithLinesListResponse,
    TransactionWithLinesResponse,
    TransactionLineCreate,
    TransactionLineUpdate,
    TransactionLineResponse,
    TransactionLineListResponse,
    PaymentCreate,
    RefundCreate,
    StatusUpdate,
    DiscountApplication,
    ReturnProcessing,
    RentalPeriodUpdate,
    RentalReturn,
    TransactionSummary,
    TransactionReport,
    TransactionSearch,
    PurchaseResponse,
    NewPurchaseRequest,
    NewPurchaseResponse,
    NewRentalRequest,
    NewRentalResponse,
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(tags=["transactions"])


def get_transaction_service(session: AsyncSession = Depends(get_session)) -> TransactionService:
    """Get transaction service instance."""
    return TransactionService(session)


# Transaction Header endpoints
@router.post("/", response_model=TransactionHeaderResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionHeaderCreate,
    service: TransactionService = Depends(get_transaction_service),
):
    """Create a new transaction."""
    try:
        return await service.create_transaction(transaction_data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/purchases", response_model=List[PurchaseResponse])
async def get_purchase_transactions(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    date_from: Optional[date] = Query(None, description="Purchase date from (inclusive)"),
    date_to: Optional[date] = Query(None, description="Purchase date to (inclusive)"),
    amount_from: Optional[Decimal] = Query(None, ge=0, description="Minimum total amount"),
    amount_to: Optional[Decimal] = Query(None, ge=0, description="Maximum total amount"),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier ID"),
    status: Optional[TransactionStatus] = Query(None, description="Transaction status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Payment status"),
    service: TransactionService = Depends(get_transaction_service),
):
    """
    Get purchase transactions with filtering options.
    
    Filters:
    - date_from/date_to: Filter by purchase date range
    - amount_from/amount_to: Filter by total amount range
    - supplier_id: Filter by specific supplier
    - status: Filter by transaction status
    - payment_status: Filter by payment status
    
    Returns list of purchase transactions with purchase-specific line item format.
    """
    return await service.get_purchase_transactions(
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        amount_from=amount_from,
        amount_to=amount_to,
        supplier_id=supplier_id,
        status=status,
        payment_status=payment_status,
    )


@router.get("/purchases/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase_by_id(
    purchase_id: UUID, service: TransactionService = Depends(get_transaction_service)
):
    """Get a single purchase transaction by ID with purchase-specific format."""
    try:
        return await service.get_purchase_by_id(purchase_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/new-rental", response_model=NewRentalResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_rental(
    rental_data: NewRentalRequest,
    service: TransactionService = Depends(get_transaction_service),
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


@router.get("/{transaction_id}", response_model=TransactionHeaderResponse)
async def get_transaction(
    transaction_id: UUID, service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction by ID."""
    try:
        return await service.get_transaction(transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/number/{transaction_number}", response_model=TransactionHeaderResponse)
async def get_transaction_by_number(
    transaction_number: str, service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction by number."""
    try:
        return await service.get_transaction_by_number(transaction_number)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{transaction_id}/with-lines", response_model=TransactionWithLinesResponse)
async def get_transaction_with_lines(
    transaction_id: UUID, service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction with lines."""
    try:
        return await service.get_transaction_with_lines(transaction_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=List[TransactionHeaderWithLinesListResponse])
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
    service: TransactionService = Depends(get_transaction_service),
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
        active_only=active_only,
    )


@router.post("/search", response_model=List[TransactionHeaderListResponse])
async def search_transactions(
    search_params: TransactionSearch,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    service: TransactionService = Depends(get_transaction_service),
):
    """Search transactions."""
    return await service.search_transactions(
        search_params=search_params, skip=skip, limit=limit, active_only=active_only
    )


@router.put("/{transaction_id}", response_model=TransactionHeaderResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionHeaderUpdate,
    service: TransactionService = Depends(get_transaction_service),
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
    transaction_id: UUID, service: TransactionService = Depends(get_transaction_service)
):
    """Delete a transaction."""
    try:
        success = await service.delete_transaction(transaction_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{transaction_id}/status", response_model=TransactionHeaderResponse)
async def update_transaction_status(
    transaction_id: UUID,
    status_update: StatusUpdate,
    service: TransactionService = Depends(get_transaction_service),
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
    service: TransactionService = Depends(get_transaction_service),
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
    service: TransactionService = Depends(get_transaction_service),
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
    service: TransactionService = Depends(get_transaction_service),
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
    transaction_id: UUID, service: TransactionService = Depends(get_transaction_service)
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
    service: TransactionService = Depends(get_transaction_service),
):
    """Complete rental return."""
    try:
        return await service.complete_rental_return(transaction_id, return_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Transaction Line endpoints
@router.post(
    "/{transaction_id}/lines",
    response_model=TransactionLineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_transaction_line(
    transaction_id: UUID,
    line_data: TransactionLineCreate,
    service: TransactionService = Depends(get_transaction_service),
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
    line_id: UUID, service: TransactionService = Depends(get_transaction_service)
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
    service: TransactionService = Depends(get_transaction_service),
):
    """Get transaction lines."""
    return await service.get_transaction_lines(transaction_id, active_only)


@router.put("/lines/{line_id}", response_model=TransactionLineResponse)
async def update_transaction_line(
    line_id: UUID,
    line_data: TransactionLineUpdate,
    service: TransactionService = Depends(get_transaction_service),
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
    line_id: UUID, service: TransactionService = Depends(get_transaction_service)
):
    """Delete transaction line."""
    try:
        success = await service.delete_transaction_line(line_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction line not found"
            )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/lines/{line_id}/discount", response_model=TransactionLineResponse)
async def apply_line_discount(
    line_id: UUID,
    discount_data: DiscountApplication,
    service: TransactionService = Depends(get_transaction_service),
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
    service: TransactionService = Depends(get_transaction_service),
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
    service: TransactionService = Depends(get_transaction_service),
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
    service: TransactionService = Depends(get_transaction_service),
):
    """Get transaction summary."""
    return await service.get_transaction_summary(
        date_from=date_from, date_to=date_to, active_only=active_only
    )


@router.get("/reports/full", response_model=TransactionReport)
async def get_transaction_report(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    active_only: bool = Query(True),
    service: TransactionService = Depends(get_transaction_service),
):
    """Get transaction report."""
    return await service.get_transaction_report(
        date_from=date_from, date_to=date_to, active_only=active_only
    )


@router.get("/reports/overdue", response_model=List[TransactionHeaderListResponse])
async def get_overdue_transactions(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: TransactionService = Depends(get_transaction_service),
):
    """Get overdue transactions."""
    return await service.get_overdue_transactions(as_of_date)


@router.get("/reports/outstanding", response_model=List[TransactionHeaderListResponse])
async def get_outstanding_transactions(
    service: TransactionService = Depends(get_transaction_service),
):
    """Get transactions with outstanding balance."""
    return await service.get_outstanding_transactions()


@router.get("/reports/due-for-return", response_model=List[TransactionHeaderListResponse])
async def get_rental_transactions_due_for_return(
    as_of_date: Optional[date] = Query(None, description="As of date"),
    service: TransactionService = Depends(get_transaction_service),
):
    """Get rental transactions due for return."""
    return await service.get_rental_transactions_due_for_return(as_of_date)


# Purchase-specific endpoints (POST /purchases removed, keeping /new-purchase)

@router.get("/purchase-returns/purchase/{purchase_id}")
async def get_purchase_returns(
    purchase_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
):
    """
    Get all return transactions for a specific purchase.
    
    This endpoint retrieves all return transactions that reference
    the given purchase transaction ID.
    """
    try:
        # Get the original purchase transaction
        purchase_txn = await service.get_transaction(purchase_id)
        
        # Handle both enum and string values
        transaction_type_value = purchase_txn.transaction_type
        if hasattr(transaction_type_value, 'value'):
            transaction_type_value = transaction_type_value.value
            
        if transaction_type_value != "PURCHASE":
            raise ValidationError(f"Transaction {purchase_id} is not a purchase transaction")
        
        # Get all return transactions that reference this purchase
        returns = await service.transaction_repository.get_all_with_lines(
            reference_transaction_id=purchase_id,
            transaction_type=TransactionType.RETURN,
            active_only=True
        )
        
        # Transform to response format
        return_list = []
        for return_txn in returns:
            return_list.append({
                "id": return_txn.id,
                "transaction_number": return_txn.transaction_number,
                "transaction_date": return_txn.transaction_date,
                "status": return_txn.status,
                "total_amount": float(return_txn.total_amount),
                "items_returned": len(return_txn.transaction_lines),
                "created_at": return_txn.created_at
            })
        
        return {
            "purchase_id": purchase_id,
            "purchase_number": purchase_txn.transaction_number,
            "returns": return_list,
            "total_returns": len(return_list)
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting purchase returns: {str(e)}"
        )


@router.post(
    "/new-purchase", response_model=NewPurchaseResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_purchase(
    purchase_data: NewPurchaseRequest,
    service: TransactionService = Depends(get_transaction_service),
):
    """
    Create a new purchase transaction with the simplified format.

    This endpoint accepts purchase data in the exact format sent by the frontend:
    - supplier_id as string UUID
    - location_id as string UUID
    - purchase_date as string in YYYY-MM-DD format
    - notes as string (can be empty)
    - reference_number as string (can be empty)
    - items array with item_id as string, quantity, unit_cost, tax_rate, discount_amount, condition, notes

    Returns a standardized response with success status, message, transaction data, and identifiers.
    """
    try:
        return await service.create_new_purchase(purchase_data)
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


