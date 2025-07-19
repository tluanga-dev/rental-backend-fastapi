"""
Simplified transaction routes for cross-module queries.

This module provides basic read-only endpoints for querying transactions
across all types (purchase, sales, rentals). Each transaction type has its
own specific routes for creation and management.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.shared.dependencies import get_session
from app.modules.transactions.base.models import (
    TransactionHeader,
    TransactionType,
    TransactionStatus,
    PaymentStatus,
)
from app.modules.transactions.base.repository import TransactionHeaderRepository
from app.core.errors import NotFoundError


router = APIRouter(tags=["transactions"])


def get_transaction_repository(session: AsyncSession = Depends(get_session)) -> TransactionHeaderRepository:
    """Get transaction repository instance."""
    return TransactionHeaderRepository(session)


# Read-only endpoints for cross-module transaction queries

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: UUID, 
    repository: TransactionHeaderRepository = Depends(get_transaction_repository)
):
    """Get transaction by ID (any type)."""
    try:
        transaction = await repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        return transaction
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/number/{transaction_number}")
async def get_transaction_by_number(
    transaction_number: str, 
    repository: TransactionHeaderRepository = Depends(get_transaction_repository)
):
    """Get transaction by number."""
    try:
        transaction = await repository.get_by_number(transaction_number)
        if not transaction:
            raise NotFoundError(f"Transaction {transaction_number} not found")
        return transaction
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/")
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    customer_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    repository: TransactionHeaderRepository = Depends(get_transaction_repository)
):
    """
    Get all transactions with optional filtering.
    
    This endpoint provides read-only access to transactions across all types.
    For type-specific operations, use the dedicated endpoints:
    - /api/purchases for purchase transactions
    - /api/sales for sales transactions  
    - /api/rentals for rental transactions
    """
    filters = {}
    if transaction_type:
        filters['transaction_type'] = transaction_type
    if status:
        filters['status'] = status
    if payment_status:
        filters['payment_status'] = payment_status
    if customer_id:
        filters['customer_id'] = str(customer_id)
    if location_id:
        filters['location_id'] = str(location_id)
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
        
    return await repository.get_all(
        skip=skip,
        limit=limit,
        filters=filters
    )


@router.get("/reports/summary")
async def get_transaction_summary(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    transaction_type: Optional[TransactionType] = None,
    session: AsyncSession = Depends(get_session)
):
    """Get transaction summary across all types."""
    query = select(
        TransactionHeader.transaction_type,
        func.count(TransactionHeader.id).label('count'),
        func.sum(TransactionHeader.total_amount).label('total_amount')
    ).where(
        TransactionHeader.is_active == True
    )
    
    if date_from:
        query = query.where(TransactionHeader.transaction_date >= date_from)
    if date_to:
        query = query.where(TransactionHeader.transaction_date <= date_to)
    if transaction_type:
        query = query.where(TransactionHeader.transaction_type == transaction_type)
    
    query = query.group_by(TransactionHeader.transaction_type)
    
    result = await session.execute(query)
    summary = result.all()
    
    return {
        "summary": [
            {
                "transaction_type": row.transaction_type,
                "count": row.count,
                "total_amount": float(row.total_amount or 0)
            }
            for row in summary
        ],
        "date_from": date_from,
        "date_to": date_to
    }