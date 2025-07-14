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
    PurchaseCreate,
    PurchaseResponse,
    NewPurchaseRequest,
    NewPurchaseResponse,
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


# Purchase-specific endpoints
@router.post("/purchases", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase(
    purchase_data: PurchaseCreate, service: TransactionService = Depends(get_transaction_service)
):
    """Create a new purchase transaction."""
    try:
        # Validate supplier exists
        from app.modules.suppliers.repository import SupplierRepository

        supplier_repo = SupplierRepository(service.session)
        supplier = await supplier_repo.get_by_id(purchase_data.supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {purchase_data.supplier_id} not found",
            )

        # Validate location exists
        from app.modules.master_data.locations.repository import LocationRepository

        location_repo = LocationRepository(service.session)
        location = await location_repo.get_by_id(purchase_data.location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with ID {purchase_data.location_id} not found",
            )

        # Validate all items exist
        from app.modules.master_data.item_master.repository import ItemMasterRepository

        item_repo = ItemMasterRepository(service.session)
        for item in purchase_data.items:
            item_exists = await item_repo.get_by_id(item.item_id)
            if not item_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item with ID {item.item_id} not found",
                )

        # Generate transaction number for purchase
        from datetime import datetime
        import random

        transaction_number = f"PUR-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        # For purchases, we need to create the transaction without customer validation
        # since supplier_id is not a customer_id
        from app.modules.transactions.models import TransactionHeader

        # Create transaction directly using the model
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.PURCHASE.value,
            transaction_date=datetime.combine(purchase_data.purchase_date, datetime.min.time()),
            customer_id=str(purchase_data.supplier_id),  # Store supplier_id in customer_id field
            location_id=str(purchase_data.location_id),
            status=TransactionStatus.COMPLETED.value,
            payment_status=PaymentStatus.PENDING.value,
            notes=purchase_data.notes,
            reference_transaction_id=None,
            rental_start_date=None,
            rental_end_date=None,
            actual_return_date=None,
            payment_method=None,
            payment_reference=None,
            sales_person_id=None,
            subtotal=Decimal("0"),
            discount_amount=Decimal("0"),
            tax_amount=Decimal("0"),
            total_amount=Decimal("0"),
            paid_amount=Decimal("0"),
            deposit_amount=Decimal("0"),
        )

        # Add to session and commit
        service.session.add(transaction)
        await service.session.commit()
        await service.session.refresh(transaction)

        # Add line items
        total_amount = Decimal("0")
        for idx, item in enumerate(purchase_data.items):
            # Calculate line values
            line_subtotal = item.unit_cost * Decimal(str(item.quantity))
            tax_amount = (line_subtotal * (item.tax_rate or Decimal("0"))) / 100
            discount_amount = item.discount_amount or Decimal("0")
            line_total = line_subtotal + tax_amount - discount_amount

            # Create line model directly
            from app.modules.transactions.models import TransactionLine

            line = TransactionLine(
                transaction_id=str(transaction.id),
                line_number=idx + 1,
                line_type=LineItemType.PRODUCT.value,
                item_id=str(item.item_id),
                description=f"Purchase item {idx + 1}",
                quantity=Decimal(str(item.quantity)),
                unit_price=item.unit_cost,
                tax_rate=item.tax_rate or Decimal("0"),
                discount_amount=discount_amount,
                discount_percentage=Decimal("0"),
                tax_amount=tax_amount,
                line_total=line_total,
                notes=item.notes,
                inventory_unit_id=None,
                rental_period_value=None,
                rental_period_unit=None,
                rental_start_date=None,
                rental_end_date=None,
                returned_quantity=Decimal("0"),
                return_date=None,
            )

            service.session.add(line)
            total_amount += line_total

        # Apply purchase-level discount if provided
        if purchase_data.discount_amount and purchase_data.discount_amount > 0:
            # Add a discount line
            discount_line = TransactionLine(
                transaction_id=str(transaction.id),
                line_number=len(purchase_data.items) + 1,
                line_type=LineItemType.DISCOUNT.value,
                description="Purchase discount",
                quantity=Decimal("1"),
                unit_price=-purchase_data.discount_amount,
                tax_rate=Decimal("0"),
                discount_amount=Decimal("0"),
                discount_percentage=Decimal("0"),
                tax_amount=Decimal("0"),
                line_total=-purchase_data.discount_amount,
                notes="Overall purchase discount",
                item_id=None,
                inventory_unit_id=None,
                rental_period_value=None,
                rental_period_unit=None,
                rental_start_date=None,
                rental_end_date=None,
                returned_quantity=Decimal("0"),
                return_date=None,
            )
            service.session.add(discount_line)
            total_amount -= purchase_data.discount_amount

        # Add purchase-level tax if provided
        if purchase_data.tax_amount and purchase_data.tax_amount > 0:
            total_amount += purchase_data.tax_amount

        # Update transaction totals
        transaction.subtotal = total_amount - (purchase_data.tax_amount or Decimal("0"))
        transaction.tax_amount = purchase_data.tax_amount or Decimal("0")
        transaction.discount_amount = purchase_data.discount_amount or Decimal("0")
        transaction.total_amount = total_amount

        # Commit all changes
        await service.session.commit()
        await service.session.refresh(transaction)

        # Get the complete transaction with lines
        result = await service.get_transaction_with_lines(transaction.id)

        # Return as PurchaseResponse using the from_transaction classmethod
        return PurchaseResponse.from_transaction(result.model_dump())

    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


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
