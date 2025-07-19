"""
Rental Returns Repository

Data access layer for rental return operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload

from app.modules.transactions.rental_returns.models import RentalInspection, RentalReturnEvent
from app.modules.transactions.base.models import TransactionHeader, TransactionType, TransactionStatus
from app.shared.repository import BaseRepository


class RentalInspectionRepository(BaseRepository[RentalInspection]):
    """Repository for rental inspection operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RentalInspection, session)
    
    async def get_by_return_id(self, return_id: UUID) -> Optional[RentalInspection]:
        """Get inspection by return transaction ID."""
        result = await self.session.execute(
            select(RentalInspection).where(
                RentalInspection.return_id == str(return_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_inspector(self, inspector_id: UUID) -> List[RentalInspection]:
        """Get all inspections performed by a specific inspector."""
        result = await self.session.execute(
            select(RentalInspection).where(
                RentalInspection.inspector_id == str(inspector_id)
            ).order_by(RentalInspection.inspection_date.desc())
        )
        return result.scalars().all()
    
    async def get_pending_customer_disputes(self) -> List[RentalInspection]:
        """Get inspections with pending customer disputes."""
        result = await self.session.execute(
            select(RentalInspection).where(
                RentalInspection.customer_disputed == True
            ).order_by(RentalInspection.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_condition(self, condition: str) -> List[RentalInspection]:
        """Get inspections by overall condition."""
        result = await self.session.execute(
            select(RentalInspection).where(
                RentalInspection.overall_condition == condition
            ).order_by(RentalInspection.inspection_date.desc())
        )
        return result.scalars().all()


class RentalReturnEventRepository(BaseRepository[RentalReturnEvent]):
    """Repository for rental return event operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RentalReturnEvent, session)
    
    async def get_by_rental_id(self, rental_id: UUID) -> List[RentalReturnEvent]:
        """Get all return events for a rental transaction."""
        result = await self.session.execute(
            select(RentalReturnEvent).where(
                RentalReturnEvent.rental_id == str(rental_id)
            ).order_by(RentalReturnEvent.return_date.asc())
        )
        return result.scalars().all()
    
    async def get_latest_by_rental_id(self, rental_id: UUID) -> Optional[RentalReturnEvent]:
        """Get the most recent return event for a rental."""
        result = await self.session.execute(
            select(RentalReturnEvent).where(
                RentalReturnEvent.rental_id == str(rental_id)
            ).order_by(RentalReturnEvent.return_date.desc()).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_date_range(
        self, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None
    ) -> List[RentalReturnEvent]:
        """Get return events within a date range."""
        filters = []
        
        if date_from:
            filters.append(RentalReturnEvent.return_date >= date_from)
        if date_to:
            filters.append(RentalReturnEvent.return_date <= date_to)
        
        stmt = select(RentalReturnEvent)
        if filters:
            stmt = stmt.where(and_(*filters))
        
        stmt = stmt.order_by(RentalReturnEvent.return_date.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_events_with_late_fees(self) -> List[RentalReturnEvent]:
        """Get return events that have late fees."""
        result = await self.session.execute(
            select(RentalReturnEvent).where(
                RentalReturnEvent.late_fee > 0
            ).order_by(RentalReturnEvent.return_date.desc())
        )
        return result.scalars().all()
    
    async def get_events_with_damage_fees(self) -> List[RentalReturnEvent]:
        """Get return events that have damage fees."""
        result = await self.session.execute(
            select(RentalReturnEvent).where(
                RentalReturnEvent.damage_fee > 0
            ).order_by(RentalReturnEvent.return_date.desc())
        )
        return result.scalars().all()
    
    async def get_events_requiring_inspection(self) -> List[RentalReturnEvent]:
        """Get return events that require inspection."""
        result = await self.session.execute(
            select(RentalReturnEvent).where(
                RentalReturnEvent.inspection_required == True
            ).order_by(RentalReturnEvent.return_date.desc())
        )
        return result.scalars().all()


class RentalReturnsRepository:
    """Main repository for rental returns operations combining inspection and event repositories."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.inspection_repo = RentalInspectionRepository(session)
        self.event_repo = RentalReturnEventRepository(session)
    
    async def get_returns_pending_inspection(self, days_old: int = 7) -> List[Dict[str, Any]]:
        """Get rental returns that are pending inspection."""
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days_old)
        
        # Query returns without inspections
        stmt = (
            select(TransactionHeader)
            .outerjoin(
                RentalInspection,
                RentalInspection.return_id == TransactionHeader.id
            )
            .where(
                and_(
                    TransactionHeader.transaction_type == TransactionType.RENTAL_RETURN,
                    TransactionHeader.transaction_date <= cutoff_date,
                    TransactionHeader.status != TransactionStatus.COMPLETED,
                    RentalInspection.id.is_(None)
                )
            )
        )
        
        result = await self.session.execute(stmt)
        returns = result.scalars().all()
        
        pending = []
        for return_txn in returns:
            metadata = return_txn.metadata or {}
            
            pending.append({
                "return_id": return_txn.id,
                "transaction_number": return_txn.transaction_number,
                "return_date": return_txn.transaction_date,
                "days_pending": (datetime.utcnow() - return_txn.transaction_date).days,
                "customer_id": return_txn.customer_id,
                "inspection_required": metadata.get("inspection_required", True),
                "total_fees": float(return_txn.total_amount or 0)
            })
        
        return pending
    
    async def get_inspection_statistics(
        self, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get inspection statistics for a date range."""
        filters = []
        
        if date_from:
            filters.append(RentalInspection.inspection_date >= date_from)
        if date_to:
            filters.append(RentalInspection.inspection_date <= date_to)
        
        # Base query
        base_query = select(RentalInspection)
        if filters:
            base_query = base_query.where(and_(*filters))
        
        # Total inspections
        total_result = await self.session.execute(
            select(func.count()).select_from(
                base_query.subquery()
            )
        )
        total_inspections = total_result.scalar()
        
        # Condition breakdown
        condition_result = await self.session.execute(
            select(
                RentalInspection.overall_condition,
                func.count().label('count')
            ).select_from(
                base_query.subquery()
            ).group_by(RentalInspection.overall_condition)
        )
        condition_breakdown = {row.overall_condition: row.count for row in condition_result}
        
        # Customer disputes
        disputes_result = await self.session.execute(
            select(func.count()).where(
                and_(
                    RentalInspection.customer_disputed == True,
                    *filters
                )
            )
        )
        customer_disputes = disputes_result.scalar()
        
        # Average costs
        cost_result = await self.session.execute(
            select(
                func.avg(RentalInspection.estimated_repair_cost).label('avg_repair'),
                func.avg(RentalInspection.estimated_cleaning_cost).label('avg_cleaning'),
                func.avg(RentalInspection.recommended_deposit_deduction).label('avg_deduction')
            ).select_from(
                base_query.subquery()
            )
        )
        cost_row = cost_result.first()
        
        return {
            "total_inspections": total_inspections,
            "condition_breakdown": condition_breakdown,
            "customer_disputes": customer_disputes,
            "dispute_rate": (customer_disputes / total_inspections * 100) if total_inspections > 0 else 0,
            "average_costs": {
                "repair_cost": float(cost_row.avg_repair or 0),
                "cleaning_cost": float(cost_row.avg_cleaning or 0),
                "deposit_deduction": float(cost_row.avg_deduction or 0)
            }
        }