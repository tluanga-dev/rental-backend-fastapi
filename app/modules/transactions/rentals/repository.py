"""
Rentals Repository

Data access layer for rental-specific operations.
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
    RentalStatus,
)
from app.modules.transactions.base.repository import TransactionHeaderRepository


class RentalsRepository(TransactionHeaderRepository):
    """Repository for rental-specific operations."""

    async def get_rentals(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[TransactionStatus] = None,
        rental_status: Optional[RentalStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        overdue_only: bool = False,
    ) -> List[TransactionHeader]:
        """Get rental transactions with filtering."""
        filters = [TransactionHeader.transaction_type == TransactionType.RENTAL]
        
        if customer_id:
            filters.append(TransactionHeader.customer_id == str(customer_id))
        if location_id:
            filters.append(TransactionHeader.location_id == str(location_id))
        if status:
            filters.append(TransactionHeader.status == status)
        if date_from:
            filters.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))

        stmt = (
            select(TransactionHeader)
            .where(and_(*filters))
            .options(selectinload(TransactionHeader.transaction_lines))
            .order_by(TransactionHeader.transaction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        rentals = result.scalars().unique().all()
        
        # Additional filtering for rental status and overdue
        if rental_status or overdue_only:
            filtered_rentals = []
            for rental in rentals:
                # Check rental status in transaction lines
                if rental_status:
                    has_matching_status = any(
                        line.current_rental_status == rental_status 
                        for line in rental.transaction_lines
                    )
                    if not has_matching_status:
                        continue
                
                # Check if overdue
                if overdue_only:
                    is_overdue = any(
                        line.rental_end_date and line.rental_end_date < date.today() and 
                        line.returned_quantity < line.quantity
                        for line in rental.transaction_lines
                    )
                    if not is_overdue:
                        continue
                
                filtered_rentals.append(rental)
            return filtered_rentals
        
        return rentals

    async def get_rental_by_id(self, rental_id: UUID) -> Optional[TransactionHeader]:
        """Get a single rental transaction by ID."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.id == rental_id,
                    TransactionHeader.transaction_type == TransactionType.RENTAL
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_rental_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get rental summary statistics."""
        filters = [TransactionHeader.transaction_type == TransactionType.RENTAL]
        
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
            func.count(TransactionHeader.id).label('total_rentals'),
            func.sum(TransactionHeader.total_amount).label('total_amount'),
            func.sum(TransactionHeader.deposit_amount).label('total_deposits'),
            func.avg(TransactionHeader.total_amount).label('average_amount'),
        ).where(and_(*filters))
        
        result = await self.session.execute(stmt)
        summary = result.first()
        
        # Get active rentals count
        active_filters = filters + [TransactionHeader.status != TransactionStatus.COMPLETED]
        active_stmt = select(func.count(TransactionHeader.id)).where(and_(*active_filters))
        active_result = await self.session.execute(active_stmt)
        active_count = active_result.scalar()
        
        return {
            'total_rentals': summary.total_rentals or 0,
            'active_rentals': active_count or 0,
            'total_amount': float(summary.total_amount or 0),
            'total_deposits': float(summary.total_deposits or 0),
            'average_amount': float(summary.average_amount or 0),
        }

    async def get_rentals_due_for_return(
        self,
        as_of_date: Optional[date] = None
    ) -> List[TransactionHeader]:
        """Get rentals due for return."""
        target_date = as_of_date or date.today()
        
        stmt = (
            select(TransactionHeader)
            .join(TransactionLine)
            .where(
                and_(
                    TransactionHeader.transaction_type == TransactionType.RENTAL,
                    TransactionHeader.status != TransactionStatus.COMPLETED,
                    TransactionLine.rental_end_date <= target_date,
                    TransactionLine.returned_quantity < TransactionLine.quantity
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
            .distinct()
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_overdue_rentals(
        self,
        as_of_date: Optional[date] = None
    ) -> List[TransactionHeader]:
        """Get overdue rentals."""
        target_date = as_of_date or date.today()
        
        stmt = (
            select(TransactionHeader)
            .join(TransactionLine)
            .where(
                and_(
                    TransactionHeader.transaction_type == TransactionType.RENTAL,
                    TransactionHeader.status != TransactionStatus.COMPLETED,
                    TransactionLine.rental_end_date < target_date,
                    TransactionLine.returned_quantity < TransactionLine.quantity
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
            .distinct()
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_customer_rental_history(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionHeader]:
        """Get rental history for a specific customer."""
        stmt = (
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.customer_id == str(customer_id),
                    TransactionHeader.transaction_type == TransactionType.RENTAL,
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

    async def get_rental_utilization_by_item(
        self,
        item_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get rental utilization statistics for a specific item."""
        filters = [
            TransactionHeader.transaction_type == TransactionType.RENTAL,
            TransactionLine.item_id == str(item_id),
            TransactionHeader.is_active == True
        ]
        
        if date_from:
            filters.append(TransactionLine.rental_start_date >= date_from)
        if date_to:
            filters.append(TransactionLine.rental_end_date <= date_to)

        # Get rental statistics
        stmt = (
            select(
                func.count(TransactionLine.id).label('total_rentals'),
                func.sum(TransactionLine.quantity).label('total_quantity_rented'),
                func.sum(TransactionLine.line_total).label('total_revenue'),
                func.avg(func.julianday(TransactionLine.rental_end_date) - 
                        func.julianday(TransactionLine.rental_start_date)).label('avg_rental_days')
            )
            .join(TransactionHeader)
            .where(and_(*filters))
        )
        
        result = await self.session.execute(stmt)
        stats = result.first()
        
        return {
            'item_id': item_id,
            'total_rentals': stats.total_rentals or 0,
            'total_quantity_rented': float(stats.total_quantity_rented or 0),
            'total_revenue': float(stats.total_revenue or 0),
            'average_rental_days': float(stats.avg_rental_days or 0),
        }

    async def update_rental_status(
        self,
        rental_id: UUID,
        status: TransactionStatus
    ) -> bool:
        """Update rental transaction status."""
        stmt = (
            update(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.id == rental_id,
                    TransactionHeader.transaction_type == TransactionType.RENTAL
                )
            )
            .values(status=status, updated_at=func.now())
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0