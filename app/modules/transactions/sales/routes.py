"""
Sales Routes

API endpoints for sales-related operations.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.sales.service import SalesService
from app.modules.transactions.models import (
    TransactionStatus,
    PaymentStatus,
)
from app.modules.transactions.sales.schemas import (
    SaleResponse,
    NewSaleRequest,
    NewSaleResponse,
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(prefix="/sales", tags=["sales"])


def get_sales_service(session: AsyncSession = Depends(get_session)) -> SalesService:
    """Get sales service instance."""
    return SalesService(session)


@router.get("/", response_model=List[SaleResponse])
async def get_sale_transactions(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    date_from: Optional[date] = Query(None, description="Sale date from (inclusive)"),
    date_to: Optional[date] = Query(None, description="Sale date to (inclusive)"),
    amount_from: Optional[Decimal] = Query(None, ge=0, description="Minimum total amount"),
    amount_to: Optional[Decimal] = Query(None, ge=0, description="Maximum total amount"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    location_id: Optional[UUID] = Query(None, description="Filter by location ID"),
    status: Optional[TransactionStatus] = Query(None, description="Transaction status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Payment status"),
    service: SalesService = Depends(get_sales_service),
):
    """
    Get sale transactions with filtering options.
    
    Filters:
    - date_from/date_to: Filter by sale date range
    - amount_from/amount_to: Filter by total amount range
    - customer_id: Filter by specific customer
    - location_id: Filter by specific location
    - status: Filter by transaction status
    - payment_status: Filter by payment status
    
    Returns list of sale transactions with sale-specific line item format.
    """
    return await service.get_sale_transactions(
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        amount_from=amount_from,
        amount_to=amount_to,
        customer_id=customer_id,
        location_id=location_id,
        status=status,
        payment_status=payment_status,
    )


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale_by_id(
    sale_id: UUID, service: SalesService = Depends(get_sales_service)
):
    """Get a single sale transaction by ID with sale-specific format."""
    try:
        return await service.get_sale_by_id(sale_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/new", response_model=NewSaleResponse, status_code=status.HTTP_201_CREATED)
async def create_new_sale(
    sale_data: NewSaleRequest,
    service: SalesService = Depends(get_sales_service),
):
    """
    Create a new sale transaction with the simplified format.

    This endpoint accepts sale data in the exact format sent by the frontend:
    - customer_id as string UUID (must exist and be able to transact)
    - transaction_date as string in YYYY-MM-DD format
    - notes as string (optional)
    - reference_number as string (optional, max 50 chars)
    - items array with:
      * item_id as string UUID (must exist and be saleable)
      * quantity as integer (>=1, required)
      * unit_cost as decimal (>=0, price per unit)
      * tax_rate as decimal (0-100, optional, defaults to 0)
      * discount_amount as decimal (>=0, optional, defaults to 0)
      * notes as string (optional)

    Features:
    - Automatically validates customer can transact
    - Generates unique transaction numbers (SAL-YYYYMMDD-XXXX)
    - Updates inventory stock levels and marks units as sold
    - Creates stock movement records for audit trail
    - Supports item-level discounts and taxes
    - Comprehensive validation at header and line levels

    Returns a standardized response with success status, message, transaction data, and identifiers.
    """
    try:
        return await service.create_new_sale(sale_data)
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


@router.get("/returns/{sale_id}")
async def get_sale_returns(
    sale_id: UUID,
    service: SalesService = Depends(get_sales_service),
):
    """
    Get all return transactions for a specific sale.
    
    This endpoint retrieves all return transactions that reference
    the given sale transaction ID.
    """
    try:
        return await service.get_sale_returns(sale_id)
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
            detail=f"Error getting sale returns: {str(e)}"
        )