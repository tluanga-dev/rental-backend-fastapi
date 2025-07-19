"""
Sales Repository

Data access layer for sales-specific operations.
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


class SalesRepository(TransactionHeaderRepository):
    """Repository for sales-specific operations."""

    async def get_sales(
        self,
        skip: int = 0,
        limit: int = 100,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        amount_from: Optional[Decimal] = None,
        amount_to: Optional[Decimal] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
    ) -> List[TransactionHeader]:
        """Get sale transactions with filtering."""
        filters = [TransactionHeader.transaction_type == TransactionType.SALE]
        
        if date_from:
            filters.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
        if amount_from:
            filters.append(TransactionHeader.total_amount >= amount_from)
        if amount_to:
            filters.append(TransactionHeader.total_amount <= amount_to)
        if customer_id:
            filters.append(TransactionHeader.customer_id == str(customer_id))
        if location_id:
            filters.append(TransactionHeader.location_id == str(location_id))
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

    async def get_sale_by_id(self, sale_id: UUID) -> Optional[TransactionHeader]:
        """Get a single sale transaction by ID."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.id == sale_id,
                    TransactionHeader.transaction_type == TransactionType.SALE
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sale_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get sale summary statistics."""
        filters = [TransactionHeader.transaction_type == TransactionType.SALE]
        
        if date_from:
            filters.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
        if customer_id:
            filters.append(TransactionHeader.customer_id == str(customer_id))
        if location_id:
            filters.append(TransactionHeader.location_id == str(location_id))

        # Get aggregated data
        stmt = select(
            func.count(TransactionHeader.id).label('total_sales'),
            func.sum(TransactionHeader.total_amount).label('total_amount'),
            func.sum(TransactionHeader.tax_amount).label('total_tax'),
            func.sum(TransactionHeader.discount_amount).label('total_discount'),
            func.avg(TransactionHeader.total_amount).label('average_amount'),
        ).where(and_(*filters))
        
        result = await self.session.execute(stmt)
        summary = result.first()
        
        return {
            'total_sales': summary.total_sales or 0,
            'total_amount': float(summary.total_amount or 0),
            'total_tax': float(summary.total_tax or 0),
            'total_discount': float(summary.total_discount or 0),
            'average_amount': float(summary.average_amount or 0),
        }

    async def get_sale_returns(self, sale_id: UUID) -> List[TransactionHeader]:
        """Get all return transactions for a sale."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.reference_transaction_id == str(sale_id),
                    TransactionHeader.transaction_type == TransactionType.RETURN,
                    TransactionHeader.is_active == True
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
            .order_by(TransactionHeader.transaction_date.desc())
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_customer_sale_history(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionHeader]:
        """Get sale history for a specific customer."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.customer_id == str(customer_id),
                    TransactionHeader.transaction_type == TransactionType.SALE,
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

    async def get_top_selling_items(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top selling items by quantity or revenue."""
        filters = [
            TransactionHeader.transaction_type == TransactionType.SALE,
            TransactionHeader.is_active == True
        ]
        
        if date_from:
            filters.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))

        # Join with transaction lines and aggregate
        stmt = (
            select(
                TransactionLine.item_id,
                func.sum(TransactionLine.quantity).label('total_quantity'),
                func.sum(TransactionLine.line_total).label('total_revenue'),
                func.count(TransactionLine.id).label('transaction_count')
            )
            .join(TransactionHeader)
            .where(and_(*filters))
            .group_by(TransactionLine.item_id)
            .order_by(func.sum(TransactionLine.quantity).desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        items = result.all()
        
        return [
            {
                'item_id': item.item_id,
                'total_quantity': float(item.total_quantity),
                'total_revenue': float(item.total_revenue),
                'transaction_count': item.transaction_count
            }
            for item in items
        ]

    async def update_sale_payment_status(
        self,
        sale_id: UUID,
        payment_status: PaymentStatus,
        paid_amount: Optional[Decimal] = None
    ) -> bool:
        """Update payment status for a sale."""
        values = {'payment_status': payment_status}
        if paid_amount is not None:
            values['paid_amount'] = paid_amount
            
        stmt = (
            update(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.id == sale_id,
                    TransactionHeader.transaction_type == TransactionType.SALE
                )
            )
            .values(**values)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0