"""
Return-specific API endpoints for the unified return system.
"""
from typing import List, Union, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_session
from app.modules.transactions.services.unified_returns import UnifiedReturnService
from app.modules.transactions.service import TransactionService
from app.modules.inventory.service import InventoryService
from app.modules.transactions.schemas import TransactionWithLinesResponse
from app.modules.transactions.schemas.returns import (
    SaleReturnCreate,
    PurchaseReturnCreate,
    RentalReturnCreate,
    ReturnTransactionCreate,
    ReturnValidationResponse,
    ReturnDetailsResponse,
    ReturnStatusUpdate,
    ReturnWorkflowState,
    RentalInspectionCreate,
    RentalInspectionResponse,
    PurchaseCreditMemoCreate,
    PurchaseCreditMemoResponse
)
from app.core.errors import NotFoundError, ValidationError, ConflictError


router = APIRouter(prefix="/returns", tags=["Returns"])


# Dependency to get unified return service
async def get_unified_return_service(session: AsyncSession = Depends(get_session)) -> UnifiedReturnService:
    """Get unified return service instance."""
    transaction_service = TransactionService(session)
    inventory_service = InventoryService(session)
    return UnifiedReturnService(transaction_service, inventory_service, session)


@router.post("/validate", response_model=ReturnValidationResponse)
async def validate_return(
    return_data: Union[SaleReturnCreate, PurchaseReturnCreate, RentalReturnCreate],
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Validate a return before processing.
    
    This endpoint allows checking if a return is valid without creating it.
    It returns any validation errors, warnings, and estimated refund amounts.
    """
    try:
        return await service.validate_return(return_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sale", response_model=TransactionWithLinesResponse, status_code=status.HTTP_201_CREATED)
async def create_sale_return(
    return_data: SaleReturnCreate,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Create a sale return transaction.
    
    This endpoint processes returns from customers, including:
    - Full or partial returns
    - Different refund methods (original payment, store credit, exchange)
    - Condition-based pricing adjustments
    - Automatic inventory updates
    """
    try:
        return await service.create_return(return_data)
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
            detail=f"Error creating sale return: {str(e)}"
        )


@router.post("/purchase", response_model=TransactionWithLinesResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_return(
    return_data: PurchaseReturnCreate,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Create a purchase return transaction.
    
    This endpoint processes returns to suppliers, including:
    - RMA number tracking
    - Quality claims and defect tracking
    - Expected credit management
    - Automatic inventory reduction
    """
    try:
        return await service.create_return(return_data)
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
            detail=f"Error creating purchase return: {str(e)}"
        )


@router.post("/rental", response_model=TransactionWithLinesResponse, status_code=status.HTTP_201_CREATED)
async def create_rental_return(
    return_data: RentalReturnCreate,
    service: UnifiedReturnService = Depends(get_unified_return_service)
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
        return await service.create_return(return_data)
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


@router.get("/{return_id}", response_model=ReturnDetailsResponse)
async def get_return_details(
    return_id: UUID,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Get comprehensive return details including type-specific metadata.
    
    This endpoint returns all information about a return transaction,
    including the type-specific properties stored in metadata.
    """
    try:
        return await service.get_return_details(return_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting return details: {str(e)}"
        )


@router.put("/{return_id}/status", response_model=TransactionWithLinesResponse)
async def update_return_status(
    return_id: UUID,
    status_update: ReturnStatusUpdate,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Update return status with workflow validation.
    
    This endpoint updates the return workflow state and handles
    any side effects of the status change.
    """
    try:
        return_txn = await service.update_return_status(
            return_id=return_id,
            new_status=status_update.new_status,
            notes=status_update.notes,
            updated_by=status_update.updated_by
        )
        return TransactionWithLinesResponse.model_validate(return_txn)
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating return status: {str(e)}"
        )


# Additional endpoints for specific return operations

@router.get("/transaction/{transaction_id}/returnable-items")
async def get_returnable_items(
    transaction_id: UUID,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Get items that can be returned from a transaction.
    
    This endpoint analyzes a transaction and returns all items that
    are eligible for return, including quantities and conditions.
    """
    try:
        transaction_service = service.transaction_service
        transaction = await transaction_service.get_with_lines(transaction_id)
        
        if not transaction:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        
        returnable_items = []
        for line in transaction.transaction_lines:
            remaining_qty = line.quantity - (line.returned_quantity or Decimal("0"))
            if remaining_qty > 0:
                item_info = {
                    "line_id": line.id,
                    "item_id": line.item_id,
                    "description": line.description,
                    "original_quantity": float(line.quantity),
                    "returned_quantity": float(line.returned_quantity or 0),
                    "returnable_quantity": float(remaining_qty),
                    "unit_price": float(line.unit_price),
                    "line_total": float(line.line_total)
                }
                
                # Add rental-specific info if applicable
                if transaction.transaction_type == "RENTAL":
                    item_info["rental_start_date"] = line.rental_start_date
                    item_info["rental_end_date"] = line.rental_end_date
                    item_info["inventory_unit_id"] = line.inventory_unit_id
                
                returnable_items.append(item_info)
        
        return {
            "transaction_id": transaction_id,
            "transaction_number": transaction.transaction_number,
            "transaction_type": transaction.transaction_type,
            "transaction_date": transaction.transaction_date,
            "customer_id": transaction.customer_id,
            "total_amount": float(transaction.total_amount),
            "returnable_items": returnable_items
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting returnable items: {str(e)}"
        )


@router.post("/rental/{return_id}/inspection", response_model=RentalInspectionResponse)
async def submit_rental_inspection(
    return_id: UUID,
    inspection_data: RentalInspectionCreate,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Submit inspection results for a rental return.
    
    This endpoint allows recording inspection findings for rental returns,
    including damage assessments and repair cost estimates.
    """
    try:
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
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating rental inspection: {str(e)}"
        )


@router.post("/purchase/{return_id}/credit-memo", response_model=PurchaseCreditMemoResponse)
async def record_supplier_credit(
    return_id: UUID,
    credit_data: PurchaseCreditMemoCreate,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Record supplier credit memo for a purchase return.
    
    This endpoint allows recording when a supplier credit is received
    for a purchase return.
    """
    try:
        return await service.create_purchase_credit_memo(credit_data)
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
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording credit memo: {str(e)}"
        )


@router.get("/rental/{return_id}/inspection", response_model=RentalInspectionResponse)
async def get_rental_inspection(
    return_id: UUID,
    service: UnifiedReturnService = Depends(get_unified_return_service)
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
                detail="Inspection not found for this return"
            )
        return inspection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rental inspection: {str(e)}"
        )


@router.get("/purchase/{return_id}/credit-memo", response_model=PurchaseCreditMemoResponse)
async def get_supplier_credit(
    return_id: UUID,
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    Get supplier credit memo for a purchase return.
    
    This endpoint retrieves existing credit memo data for a purchase return.
    """
    try:
        credit_memo = await service.get_purchase_credit_memo(return_id)
        if not credit_memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit memo not found for this return"
            )
        return credit_memo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting credit memo: {str(e)}"
        )


@router.get("/")
async def list_returns(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    return_type: Optional[str] = Query(None, description="Filter by return type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Filter by date from"),
    date_to: Optional[date] = Query(None, description="Filter by date to"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    service: UnifiedReturnService = Depends(get_unified_return_service)
):
    """
    List return transactions with filtering.
    
    This endpoint returns a paginated list of return transactions
    with optional filtering by type, status, date range, and customer.
    """
    try:
        # This would use the transaction service with filters
        # For now, return a placeholder
        return {
            "total": 0,
            "skip": skip,
            "limit": limit,
            "returns": []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing returns: {str(e)}"
        )


# Import for proper type support
from decimal import Decimal