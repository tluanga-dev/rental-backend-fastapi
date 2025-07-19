"""
Purchase Routes

API endpoints for purchase-related operations.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.purchase.service import PurchaseService
from app.modules.transactions.base.models import (
    TransactionStatus,
    PaymentStatus,
)
from app.modules.transactions.purchase.schemas import (
    PurchaseResponse,
    NewPurchaseRequest,
    NewPurchaseResponse,
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(tags=["purchases"])


def get_purchase_service(session: AsyncSession = Depends(get_session)) -> PurchaseService:
    """Get purchase service instance."""
    return PurchaseService(session)


@router.get("/", response_model=List[PurchaseResponse])
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
    service: PurchaseService = Depends(get_purchase_service),
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


@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase_by_id(
    purchase_id: UUID, service: PurchaseService = Depends(get_purchase_service)
):
    """Get a single purchase transaction by ID with purchase-specific format."""
    try:
        return await service.get_purchase_by_id(purchase_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/new", response_model=NewPurchaseResponse, status_code=status.HTTP_201_CREATED)
async def create_new_purchase(
    purchase_data: NewPurchaseRequest,
    service: PurchaseService = Depends(get_purchase_service),
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
        print("Creating new purchase with data:", purchase_data)
        return await service.create_new_purchase(purchase_data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        import traceback
        print(f"ERROR: Full exception details: {e}")
        print(f"ERROR: Exception type: {type(e)}")
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/returns/{purchase_id}")
async def get_purchase_returns(
    purchase_id: UUID,
    service: PurchaseService = Depends(get_purchase_service),
):
    """
    Get all return transactions for a specific purchase.
    
    This endpoint retrieves all return transactions that reference
    the given purchase transaction ID.
    """
    try:
        return await service.get_purchase_returns(purchase_id)
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