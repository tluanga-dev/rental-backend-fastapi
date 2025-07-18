"""
Purchase transaction routes for API endpoints.
"""

from typing import Annotated, List, Optional
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import ValidationError

from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError, ConflictError
from app.modules.transactions.purchase.dependencies import get_purchase_service
from app.modules.transactions.purchase.service import PurchaseService
from app.modules.transactions.purchase.schemas import (
    NewPurchaseRequest, 
    PurchaseTransactionResponse,
    PurchaseTransactionFilterRequest,
    PurchaseTransactionListResponse,
    PurchaseTransactionDataResponse,
    PaginationParams
)
from app.modules.users.models import User


router = APIRouter(tags=["transactions"])


@router.post(
    "/new-purchase",
    response_model=PurchaseTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Purchase Transaction",
    description="Create a new purchase transaction with items and automatic stock level updates."
)
async def create_purchase_transaction(
    request: NewPurchaseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    purchase_service: Annotated[PurchaseService, Depends(get_purchase_service)]
) -> PurchaseTransactionResponse:
    """
    Create a new purchase transaction.
    
    This endpoint creates a complete purchase transaction including:
    - Transaction header with supplier, location, and financial details
    - Individual line items for each purchased item
    - Automatic stock level updates for inventory management
    - Comprehensive validation of all input data
    
    **Request Body:**
    - `supplier_id`: UUID of the supplier (required)
    - `location_id`: UUID of the location (required)
    - `purchase_date`: Date in YYYY-MM-DD format (required)
    - `notes`: Additional notes (optional, max 1000 chars)
    - `reference_number`: External reference (optional, max 50 chars)
    - `items`: Array of purchase items (required, min 1 item)
    
    **Item Fields:**
    - `item_id`: UUID of the item (required)
    - `quantity`: Quantity purchased (required, min 1)
    - `unit_cost`: Cost per unit (required, min 0)
    - `tax_rate`: Tax rate percentage (optional, 0-100)
    - `discount_amount`: Discount amount (optional, min 0)
    - `condition`: Item condition A/B/C/D (required)
    - `notes`: Item notes (optional, max 500 chars)
    
    **Response:**
    - Complete transaction details with calculated totals
    - Transaction number in format PUR-YYYYMMDD-XXXX
    - All line items with individual calculations
    - Success confirmation message
    
    **Validation Rules:**
    - All UUIDs must be valid format and reference existing entities
    - Dates must be in YYYY-MM-DD format
    - Numeric values must be within specified ranges
    - Condition codes must be A, B, C, or D
    - String lengths must not exceed maximums
    
    **Error Responses:**
    - 400: Invalid request data or validation errors
    - 404: Supplier, location, or item not found
    - 409: Transaction number generation conflict
    - 422: Validation errors with detailed field information
    """
    try:
        result = await purchase_service.create_new_purchase(request)
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the purchase transaction: {str(e)}"
        )


@router.get(
    "/purchases/",
    response_model=PurchaseTransactionListResponse,
    summary="List Purchase Transactions",
    description="Get a list of purchase transactions with filtering and pagination support."
)
async def list_purchase_transactions(
    start_date: Optional[date] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier ID"),
    location_id: Optional[UUID] = Query(None, description="Filter by location ID"),
    status: Optional[str] = Query(None, description="Filter by transaction status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    transaction_number: Optional[str] = Query(None, description="Filter by transaction number (partial match)"),
    min_amount: Optional[Decimal] = Query(None, ge=0, description="Minimum transaction amount"),
    max_amount: Optional[Decimal] = Query(None, ge=0, description="Maximum transaction amount"),
    item_ids: Optional[List[UUID]] = Query(None, description="Filter by item IDs (transactions containing these items)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    sort_by: Optional[str] = Query(None, description="Sort by field (transaction_date, transaction_number, total_amount)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    current_user: Annotated[User, Depends(get_current_user)],
    purchase_service: Annotated[PurchaseService, Depends(get_purchase_service)]
) -> PurchaseTransactionListResponse:
    """
    List purchase transactions with advanced filtering.
    
    This endpoint provides comprehensive filtering capabilities for purchase transactions:
    
    **Filter Options:**
    - **Date Range**: Filter by transaction date range
    - **Supplier**: Filter by specific supplier
    - **Location**: Filter by specific location
    - **Status**: Filter by transaction status (PENDING, COMPLETED, CANCELLED, etc.)
    - **Payment Status**: Filter by payment status (PENDING, PAID, PARTIAL, etc.)
    - **Transaction Number**: Partial match on transaction number
    - **Amount Range**: Filter by transaction amount range
    - **Items**: Filter by items contained in transactions
    
    **Pagination:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 100, max: 1000)
    - `sort_by`: Field to sort by (transaction_date, transaction_number, total_amount)
    - `sort_order`: Sort direction (asc, desc)
    
    **Response:**
    - List of purchase transaction summaries
    - Pagination metadata
    - Supplier and location names for display
    
    **Example Usage:**
    ```
    GET /api/transactions/purchases/?start_date=2024-01-01&end_date=2024-12-31&supplier_id=123e4567-e89b-12d3-a456-426614174000
    ```
    """
    try:
        # Build filter request
        filter_request = PurchaseTransactionFilterRequest(
            start_date=start_date,
            end_date=end_date,
            supplier_id=supplier_id,
            location_id=location_id,
            status=status,
            payment_status=payment_status,
            transaction_number=transaction_number,
            min_amount=min_amount,
            max_amount=max_amount,
            item_ids=item_ids
        )
        
        # Build pagination request
        pagination_request = PaginationParams(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get transactions
        result = await purchase_service.list_purchase_transactions(
            filters=filter_request,
            pagination=pagination_request
        )
        
        return PurchaseTransactionListResponse(
            success=True,
            message="Purchase transactions retrieved successfully",
            data=result["data"],
            pagination=result["pagination"]
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving purchase transactions: {str(e)}"
        )


@router.get(
    "/purchases/{transaction_id}",
    response_model=PurchaseTransactionDataResponse,
    summary="Get Purchase Transaction by ID",
    description="Get detailed information about a specific purchase transaction."
)
async def get_purchase_transaction(
    transaction_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    purchase_service: Annotated[PurchaseService, Depends(get_purchase_service)]
) -> PurchaseTransactionDataResponse:
    """
    Get detailed purchase transaction by ID.
    
    **Path Parameters:**
    - `transaction_id`: UUID of the purchase transaction
    
    **Response:**
    - Complete transaction details
    - All line items with full information
    - Supplier and location details
    - Financial calculations
    
    **Error Responses:**
    - 404: Transaction not found
    - 400: Invalid transaction ID format
    """
    try:
        transaction = await purchase_service.get_purchase_transaction_by_id(transaction_id)
        return transaction
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the purchase transaction: {str(e)}"
        )


@router.get(
    "/purchases/supplier/{supplier_id}",
    response_model=PurchaseTransactionListResponse,
    summary="Get Purchase Transactions by Supplier",
    description="Get all purchase transactions for a specific supplier."
)
async def get_purchase_transactions_by_supplier(
    supplier_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: Annotated[User, Depends(get_current_user)],
    purchase_service: Annotated[PurchaseService, Depends(get_purchase_service)]
) -> PurchaseTransactionListResponse:
    """
    Get purchase transactions for a specific supplier.
    
    **Path Parameters:**
    - `supplier_id`: UUID of the supplier
    
    **Query Parameters:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 100, max: 1000)
    
    **Response:**
    - List of purchase transactions for the supplier
    - Transaction summaries with enriched data
    """
    try:
        transactions = await purchase_service.get_purchase_transactions_by_supplier(
            supplier_id=supplier_id,
            skip=skip,
            limit=limit
        )
        
        return PurchaseTransactionListResponse(
            success=True,
            message=f"Purchase transactions for supplier {supplier_id} retrieved successfully",
            data=transactions,
            pagination={
                "total": len(transactions),
                "skip": skip,
                "limit": limit,
                "current_page": (skip // limit) + 1 if limit > 0 else 1,
                "total_pages": (len(transactions) + limit - 1) // limit if limit > 0 else 1,
                "has_next": skip + limit < len(transactions),
                "has_prev": skip > 0
            }
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving supplier transactions: {str(e)}"
        )


@router.get(
    "/purchases/items/",
    response_model=PurchaseTransactionListResponse,
    summary="Get Purchase Transactions by Items",
    description="Get purchase transactions that contain specific items."
)
async def get_purchase_transactions_by_items(
    item_ids: List[UUID] = Query(..., description="List of item IDs to filter by"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: Annotated[User, Depends(get_current_user)],
    purchase_service: Annotated[PurchaseService, Depends(get_purchase_service)]
) -> PurchaseTransactionListResponse:
    """
    Get purchase transactions containing specific items.
    
    **Query Parameters:**
    - `item_ids`: List of item UUIDs (required)
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 100, max: 1000)
    
    **Response:**
    - List of purchase transactions containing the specified items
    - Transaction summaries with enriched data
    
    **Example:**
    ```
    GET /api/transactions/purchases/items/?item_ids=123e4567-e89b-12d3-a456-426614174000&item_ids=456e7890-e89b-12d3-a456-426614174001
    ```
    """
    try:
        transactions = await purchase_service.get_purchase_transactions_by_items(
            item_ids=item_ids,
            skip=skip,
            limit=limit
        )
        
        return PurchaseTransactionListResponse(
            success=True,
            message=f"Purchase transactions containing specified items retrieved successfully",
            data=transactions,
            pagination={
                "total": len(transactions),
                "skip": skip,
                "limit": limit,
                "current_page": (skip // limit) + 1 if limit > 0 else 1,
                "total_pages": (len(transactions) + limit - 1) // limit if limit > 0 else 1,
                "has_next": skip + limit < len(transactions),
                "has_prev": skip > 0
            }
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving item transactions: {str(e)}"
        )
