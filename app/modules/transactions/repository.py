"""
Transaction repository for database operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text

from app.modules.transactions.models.transaction_headers import TransactionHeader, TransactionType
from app.modules.transactions.models.transaction_lines import TransactionLine
from app.shared.repository import BaseRepository


class TransactionRepository(BaseRepository[TransactionHeader]):
    """Repository for transaction operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TransactionHeader, session)
    
    async def get_by_number(self, transaction_number: str) -> Optional[TransactionHeader]:
        """Get transaction by transaction number."""
        query = select(TransactionHeader).where(
            TransactionHeader.transaction_number == transaction_number
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_lines(self, transaction_id: UUID) -> Optional[TransactionHeader]:
        """Get transaction with its line items."""
        query = select(TransactionHeader).where(
            TransactionHeader.id == transaction_id
        ).options(selectinload(TransactionHeader.transaction_lines))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_with_lines(
        self, 
        transaction: TransactionHeader, 
        lines: List[TransactionLine]
    ) -> TransactionHeader:
        """Create transaction with line items."""
        self.session.add(transaction)
        await self.session.flush()
        
        # Add lines with proper transaction reference
        for line in lines:
            line.transaction_id = transaction.id
            self.session.add(line)
        
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction
    
    async def get_transactions_by_customer(
        self, 
        customer_id: UUID, 
        limit: int = 100
    ) -> List[TransactionHeader]:
        """Get transactions for a customer/supplier."""
        query = select(TransactionHeader).where(
            TransactionHeader.customer_id == str(customer_id)
        ).order_by(TransactionHeader.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_transactions_by_location(
        self, 
        location_id: UUID, 
        limit: int = 100
    ) -> List[TransactionHeader]:
        """Get transactions for a location."""
        query = select(TransactionHeader).where(
            TransactionHeader.location_id == str(location_id)
        ).order_by(TransactionHeader.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_transactions_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[TransactionHeader]:
        """Get transactions within date range."""
        query = select(TransactionHeader).where(
            TransactionHeader.transaction_date >= start_date,
            TransactionHeader.transaction_date <= end_date
        ).order_by(TransactionHeader.transaction_date.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_purchase_transactions_with_filters(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "transaction_date",
        sort_order: str = "desc"
    ) -> List[TransactionHeader]:
        """Get purchase transactions with advanced filtering."""
        query = select(TransactionHeader).where(
            TransactionHeader.transaction_type == TransactionType.PURCHASE
        )
        
        # Apply filters
        if filters.get("start_date"):
            query = query.where(TransactionHeader.transaction_date >= filters["start_date"])
        
        if filters.get("end_date"):
            query = query.where(TransactionHeader.transaction_date <= filters["end_date"])
        
        if filters.get("supplier_id"):
            query = query.where(TransactionHeader.customer_id == str(filters["supplier_id"]))
        
        if filters.get("location_id"):
            query = query.where(TransactionHeader.location_id == str(filters["location_id"]))
        
        if filters.get("status"):
            query = query.where(TransactionHeader.status == filters["status"])
        
        if filters.get("payment_status"):
            query = query.where(TransactionHeader.payment_status == filters["payment_status"])
        
        if filters.get("transaction_number"):
            query = query.where(
                TransactionHeader.transaction_number.ilike(f"%{filters['transaction_number']}%")
            )
        
        if filters.get("min_amount"):
            query = query.where(TransactionHeader.total_amount >= filters["min_amount"])
        
        if filters.get("max_amount"):
            query = query.where(TransactionHeader.total_amount <= filters["max_amount"])
        
        # Filter by items if provided
        if filters.get("item_ids"):
            item_ids = [str(item_id) for item_id in filters["item_ids"]]
            subquery = (
                select(TransactionLine.transaction_id)
                .where(TransactionLine.item_id.in_(item_ids))
                .distinct()
            )
            query = query.where(TransactionHeader.id.in_(subquery))
        
        # Apply sorting
        sort_column = getattr(TransactionHeader, sort_by, TransactionHeader.transaction_date)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Eager load transaction lines
        query = query.options(selectinload(TransactionHeader.transaction_lines))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_purchase_transactions(self, filters: Dict[str, Any]) -> int:
        """Count purchase transactions with filters."""
        query = select(func.count(TransactionHeader.id)).where(
            TransactionHeader.transaction_type == TransactionType.PURCHASE
        )
        
        # Apply same filters as get_purchase_transactions_with_filters
        if filters.get("start_date"):
            query = query.where(TransactionHeader.transaction_date >= filters["start_date"])
        
        if filters.get("end_date"):
            query = query.where(TransactionHeader.transaction_date <= filters["end_date"])
        
        if filters.get("supplier_id"):
            query = query.where(TransactionHeader.customer_id == str(filters["supplier_id"]))
        
        if filters.get("location_id"):
            query = query.where(TransactionHeader.location_id == str(filters["location_id"]))
        
        if filters.get("status"):
            query = query.where(TransactionHeader.status == filters["status"])
        
        if filters.get("payment_status"):
            query = query.where(TransactionHeader.payment_status == filters["payment_status"])
        
        if filters.get("transaction_number"):
            query = query.where(
                TransactionHeader.transaction_number.ilike(f"%{filters['transaction_number']}%")
            )
        
        if filters.get("min_amount"):
            query = query.where(TransactionHeader.total_amount >= filters["min_amount"])
        
        if filters.get("max_amount"):
            query = query.where(TransactionHeader.total_amount <= filters["max_amount"])
        
        if filters.get("item_ids"):
            item_ids = [str(item_id) for item_id in filters["item_ids"]]
            subquery = (
                select(TransactionLine.transaction_id)
                .where(TransactionLine.item_id.in_(item_ids))
                .distinct()
            )
            query = query.where(TransactionHeader.id.in_(subquery))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def get_purchase_transactions_by_supplier(
        self,
        supplier_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionHeader]:
        """Get purchase transactions for a specific supplier."""
        query = (
            select(TransactionHeader)
            .where(
                TransactionHeader.transaction_type == TransactionType.PURCHASE,
                TransactionHeader.customer_id == str(supplier_id)
            )
            .order_by(TransactionHeader.transaction_date.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(TransactionHeader.transaction_lines))
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_purchase_transactions_by_items(
        self,
        item_ids: List[UUID],
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionHeader]:
        """Get purchase transactions containing specific items."""
        item_id_strings = [str(item_id) for item_id in item_ids]
        
        subquery = (
            select(TransactionLine.transaction_id)
            .where(TransactionLine.item_id.in_(item_id_strings))
            .distinct()
        )
        
        query = (
            select(TransactionHeader)
            .where(
                TransactionHeader.transaction_type == TransactionType.PURCHASE,
                TransactionHeader.id.in_(subquery)
            )
            .order_by(TransactionHeader.transaction_date.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(TransactionHeader.transaction_lines))
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_purchase_transaction_details(self, transaction_id: UUID) -> Optional[TransactionHeader]:
        """Get detailed purchase transaction with all related data."""
        query = (
            select(TransactionHeader)
            .where(
                TransactionHeader.id == transaction_id,
                TransactionHeader.transaction_type == TransactionType.PURCHASE
            )
            .options(
                selectinload(TransactionHeader.transaction_lines),
                # Add joins for supplier and location when models are available
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class TransactionLineRepository(BaseRepository[TransactionLine]):
    """Repository for transaction line operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TransactionLine, session)
    
    async def get_by_transaction_id(self, transaction_id: UUID) -> List[TransactionLine]:
        """Get all lines for a transaction."""
        query = select(TransactionLine).where(
            TransactionLine.transaction_id == transaction_id
        ).order_by(TransactionLine.line_number)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_item_id(self, item_id: UUID) -> List[TransactionLine]:
        """Get all lines for an item."""
        query = select(TransactionLine).where(
            TransactionLine.item_id == str(item_id)
        ).order_by(TransactionLine.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_bulk(self, lines: List[TransactionLine]) -> List[TransactionLine]:
        """Create multiple transaction lines."""
        for line in lines:
            self.session.add(line)
        await self.session.flush()
        return lines
