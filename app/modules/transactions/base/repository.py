"""
Base Transaction Repository

Shared repository functionality for all transaction types.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.shared.repository import BaseRepository
from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType, TransactionStatus


class BaseTransactionRepository(BaseRepository[TransactionHeader]):
    """Base repository for transaction operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TransactionHeader, session)
    
    async def get_by_transaction_number(self, transaction_number: str) -> Optional[TransactionHeader]:
        """Get transaction by transaction number."""
        query = select(TransactionHeader).where(
            TransactionHeader.transaction_number == transaction_number
        ).options(
            selectinload(TransactionHeader.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_lines(self, transaction_id: UUID) -> Optional[TransactionHeader]:
        """Get transaction with all line items."""
        query = select(TransactionHeader).where(
            TransactionHeader.id == transaction_id
        ).options(
            selectinload(TransactionHeader.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_type(
        self,
        transaction_type: TransactionType,
        limit: int = 100,
        offset: int = 0,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[TransactionHeader]:
        """Get transactions by type with filters."""
        query = select(TransactionHeader).where(
            TransactionHeader.transaction_type == transaction_type
        )
        
        # Apply filters
        if customer_id:
            query = query.where(TransactionHeader.customer_id == customer_id)
        if location_id:
            query = query.where(TransactionHeader.location_id == location_id)
        if status:
            query = query.where(TransactionHeader.status == status)
        if date_from:
            query = query.where(TransactionHeader.transaction_date >= date_from)
        if date_to:
            query = query.where(TransactionHeader.transaction_date <= date_to)
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_by_type(
        self,
        transaction_type: TransactionType,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> int:
        """Count transactions by type with filters."""
        query = select(func.count(TransactionHeader.id)).where(
            TransactionHeader.transaction_type == transaction_type
        )
        
        # Apply same filters as get_by_type
        if customer_id:
            query = query.where(TransactionHeader.customer_id == customer_id)
        if location_id:
            query = query.where(TransactionHeader.location_id == location_id)
        if status:
            query = query.where(TransactionHeader.status == status)
        if date_from:
            query = query.where(TransactionHeader.transaction_date >= date_from)
        if date_to:
            query = query.where(TransactionHeader.transaction_date <= date_to)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def get_by_customer(
        self,
        customer_id: str,
        transaction_type: Optional[TransactionType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TransactionHeader]:
        """Get transactions for a specific customer."""
        query = select(TransactionHeader).where(
            TransactionHeader.customer_id == customer_id
        )
        
        if transaction_type:
            query = query.where(TransactionHeader.transaction_type == transaction_type)
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_reference(self, reference_transaction_id: UUID) -> List[TransactionHeader]:
        """Get transactions that reference another transaction (e.g., returns)."""
        query = select(TransactionHeader).where(
            TransactionHeader.reference_transaction_id == reference_transaction_id
        ).options(
            selectinload(TransactionHeader.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_payments(
        self,
        transaction_type: Optional[TransactionType] = None,
        customer_id: Optional[str] = None
    ) -> List[TransactionHeader]:
        """Get transactions with pending payments."""
        query = select(TransactionHeader).where(
            TransactionHeader.paid_amount < TransactionHeader.total_amount
        )
        
        if transaction_type:
            query = query.where(TransactionHeader.transaction_type == transaction_type)
        if customer_id:
            query = query.where(TransactionHeader.customer_id == customer_id)
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_financial_summary(
        self,
        transaction_type: TransactionType,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get financial summary for transaction type."""
        query = select(
            func.count(TransactionHeader.id).label("total_transactions"),
            func.sum(TransactionHeader.total_amount).label("total_amount"),
            func.sum(TransactionHeader.paid_amount).label("paid_amount"),
            func.sum(TransactionHeader.total_amount - TransactionHeader.paid_amount).label("outstanding_amount")
        ).where(
            TransactionHeader.transaction_type == transaction_type
        )
        
        if date_from:
            query = query.where(TransactionHeader.transaction_date >= date_from)
        if date_to:
            query = query.where(TransactionHeader.transaction_date <= date_to)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        return {
            "total_transactions": row.total_transactions or 0,
            "total_amount": row.total_amount or Decimal("0"),
            "paid_amount": row.paid_amount or Decimal("0"),
            "outstanding_amount": row.outstanding_amount or Decimal("0")
        }
    
    async def update_status(self, transaction_id: UUID, status: TransactionStatus) -> bool:
        """Update transaction status."""
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return False
        
        transaction.status = status
        await self.session.commit()
        return True
    
    async def update_payment(
        self,
        transaction_id: UUID,
        paid_amount: Decimal,
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None
    ) -> bool:
        """Update payment information."""
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return False
        
        transaction.paid_amount = paid_amount
        if payment_method:
            transaction.payment_method = payment_method
        if payment_reference:
            transaction.payment_reference = payment_reference
        
        await self.session.commit()
        return True


class BaseTransactionLineRepository(BaseRepository[TransactionLine]):
    """Base repository for transaction line operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TransactionLine, session)
    
    async def get_by_transaction(self, transaction_id: UUID) -> List[TransactionLine]:
        """Get all line items for a transaction."""
        query = select(TransactionLine).where(
            TransactionLine.transaction_id == transaction_id
        ).order_by(TransactionLine.line_number)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_item(self, item_id: str) -> List[TransactionLine]:
        """Get all line items for a specific item."""
        query = select(TransactionLine).where(
            TransactionLine.item_id == item_id
        ).options(
            joinedload(TransactionLine.transaction)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_inventory_unit(self, inventory_unit_id: str) -> List[TransactionLine]:
        """Get all line items for a specific inventory unit."""
        query = select(TransactionLine).where(
            TransactionLine.inventory_unit_id == inventory_unit_id
        ).options(
            joinedload(TransactionLine.transaction)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_fulfillment_status(
        self,
        line_id: UUID,
        fulfillment_status: str
    ) -> bool:
        """Update fulfillment status for a line item."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.fulfillment_status = fulfillment_status
        await self.session.commit()
        return True
    
    async def update_return_info(
        self,
        line_id: UUID,
        returned_quantity: Decimal,
        return_date: Optional[date] = None,
        return_condition: Optional[str] = None,
        inspection_status: Optional[str] = None
    ) -> bool:
        """Update return information for a line item."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.returned_quantity = returned_quantity
        if return_date:
            line.return_date = return_date
        if return_condition:
            line.return_condition = return_condition
        if inspection_status:
            line.inspection_status = inspection_status
        
        await self.session.commit()
        return True