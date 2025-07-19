"""
Purchase Repository

Data access layer for purchase-specific operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload

from app.modules.transactions.models import (
    TransactionHeader,
    TransactionLine,
    TransactionType,
    TransactionStatus,
    PaymentStatus,
)
from app.modules.transactions.base.repository import TransactionHeaderRepository


class PurchaseRepository(TransactionHeaderRepository):
    """Repository for purchase-specific operations."""

    async def get_purchases(
        self,
        skip: int = 0,
        limit: int = 100,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        amount_from: Optional[Decimal] = None,
        amount_to: Optional[Decimal] = None,
        supplier_id: Optional[UUID] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
    ) -> List[TransactionHeader]:
        """Get purchase transactions with filtering."""
        filters = [TransactionHeader.transaction_type == TransactionType.PURCHASE]
        
        if date_from:
            filters.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
        if amount_from:
            filters.append(TransactionHeader.total_amount >= amount_from)
        if amount_to:
            filters.append(TransactionHeader.total_amount <= amount_to)
        if supplier_id:
            filters.append(TransactionHeader.customer_id == str(supplier_id))
        if status:
            filters.append(TransactionHeader.status == status)
        if payment_status:
            filters.append(TransactionHeader.payment_status == payment_status)

        stmt = (
            select(TransactionHeader)
            .where(and_(*filters))
            .options(selectinload(TransactionHeader.transaction_lines))
            .order_by(TransactionHeader.transaction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_purchase_by_id(self, purchase_id: UUID) -> Optional[TransactionHeader]:
        """Get a single purchase transaction by ID."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.id == purchase_id,
                    TransactionHeader.transaction_type == TransactionType.PURCHASE
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        supplier_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get purchase summary statistics."""
        filters = [TransactionHeader.transaction_type == TransactionType.PURCHASE]
        
        if date_from:
            filters.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
        if supplier_id:
            filters.append(TransactionHeader.customer_id == str(supplier_id))

        # Get aggregated data
        stmt = select(
            func.count(TransactionHeader.id).label('total_purchases'),
            func.sum(TransactionHeader.total_amount).label('total_amount'),
            func.sum(TransactionHeader.tax_amount).label('total_tax'),
            func.sum(TransactionHeader.discount_amount).label('total_discount'),
            func.avg(TransactionHeader.total_amount).label('average_amount'),
        ).where(and_(*filters))
        
        result = await self.session.execute(stmt)
        summary = result.first()
        
        return {
            'total_purchases': summary.total_purchases or 0,
            'total_amount': float(summary.total_amount or 0),
            'total_tax': float(summary.total_tax or 0),
            'total_discount': float(summary.total_discount or 0),
            'average_amount': float(summary.average_amount or 0),
        }

    async def get_purchase_returns(self, purchase_id: UUID) -> List[TransactionHeader]:
        """Get all return transactions for a purchase."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.reference_transaction_id == str(purchase_id),
                    TransactionHeader.transaction_type == TransactionType.RETURN,
                    TransactionHeader.is_active == True
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
            .order_by(TransactionHeader.transaction_date.desc())
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_supplier_purchase_history(
        self,
        supplier_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionHeader]:
        """Get purchase history for a specific supplier."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.customer_id == str(supplier_id),
                    TransactionHeader.transaction_type == TransactionType.PURCHASE,
                    TransactionHeader.is_active == True
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
            .order_by(TransactionHeader.transaction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def update_purchase_payment_status(
        self,
        purchase_id: UUID,
        payment_status: PaymentStatus,
        paid_amount: Optional[Decimal] = None
    ) -> bool:
        """Update payment status for a purchase."""
        values = {'payment_status': payment_status}
        if paid_amount is not None:
            values['paid_amount'] = paid_amount
            
        stmt = (
            update(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.id == purchase_id,
                    TransactionHeader.transaction_type == TransactionType.PURCHASE
                )
            )
            .values(**values)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0