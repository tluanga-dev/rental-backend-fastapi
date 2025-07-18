"""
Rental Repository

Data access layer for rental operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.modules.transactions.base.repository import BaseTransactionRepository, BaseTransactionLineRepository
from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType, TransactionStatus
from app.modules.rentals.models import Rental, RentalLine, RentalLifecycle, RentalExtension
from app.modules.transactions.base.models import RentalStatus


class RentalsRepository(BaseTransactionRepository):
    """Repository for rental operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_rental(self, rental_data: Dict[str, Any]) -> Rental:
        """Create a new rental."""
        rental = Rental(**rental_data)
        rental.transaction_type = TransactionType.RENTAL
        
        self.session.add(rental)
        await self.session.commit()
        await self.session.refresh(rental)
        return rental
    
    async def get_rental_by_id(self, rental_id: UUID) -> Optional[Rental]:
        """Get rental by ID with line items."""
        query = select(Rental).where(
            Rental.id == rental_id
        ).options(
            selectinload(Rental.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_rental_by_agreement_number(self, agreement_number: str) -> Optional[Rental]:
        """Get rental by agreement number."""
        query = select(Rental).where(
            Rental.rental_agreement_number == agreement_number
        ).options(
            selectinload(Rental.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_rentals(
        self,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Rental]:
        """Get active rentals."""
        query = select(Rental).where(
            Rental.rental_status == RentalStatus.ACTIVE
        )
        
        if customer_id:
            query = query.where(Rental.customer_id == customer_id)
        if location_id:
            query = query.where(Rental.location_id == location_id)
        
        query = query.order_by(desc(Rental.rental_start_date))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_overdue_rentals(
        self,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Rental]:
        """Get overdue rentals."""
        today = date.today()
        query = select(Rental).where(
            and_(
                Rental.rental_end_date < today,
                Rental.actual_return_date.is_(None),
                Rental.rental_status.in_([RentalStatus.ACTIVE, RentalStatus.LATE])
            )
        )
        
        if customer_id:
            query = query.where(Rental.customer_id == customer_id)
        if location_id:
            query = query.where(Rental.location_id == location_id)
        
        query = query.order_by(desc(Rental.rental_end_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rentals_due_today(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Rental]:
        """Get rentals due today."""
        today = date.today()
        query = select(Rental).where(
            and_(
                Rental.rental_end_date == today,
                Rental.actual_return_date.is_(None)
            )
        )
        
        if location_id:
            query = query.where(Rental.location_id == location_id)
        
        query = query.order_by(desc(Rental.rental_start_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rentals_due_this_week(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Rental]:
        """Get rentals due this week."""
        today = date.today()
        week_end = today + timedelta(days=7)
        query = select(Rental).where(
            and_(
                Rental.rental_end_date >= today,
                Rental.rental_end_date <= week_end,
                Rental.actual_return_date.is_(None)
            )
        )
        
        if location_id:
            query = query.where(Rental.location_id == location_id)
        
        query = query.order_by(asc(Rental.rental_end_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_customer_rentals(
        self,
        customer_id: str,
        status: Optional[RentalStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Rental]:
        """Get rentals for a specific customer."""
        query = select(Rental).where(
            Rental.customer_id == customer_id
        )
        
        if status:
            query = query.where(Rental.rental_status == status)
        
        query = query.order_by(desc(Rental.rental_start_date))
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rental_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get rental summary statistics."""
        query = select(
            func.count(Rental.id).label("total_rentals"),
            func.sum(Rental.total_amount).label("total_revenue"),
            func.sum(Rental.late_fee_amount).label("total_late_fees"),
            func.sum(Rental.security_deposit_amount).label("total_deposits"),
            func.avg(Rental.total_amount).label("average_rental"),
            func.avg(
                func.extract('day', Rental.rental_end_date - Rental.rental_start_date)
            ).label("average_duration"),
            func.count(Rental.id).filter(Rental.rental_status == RentalStatus.ACTIVE).label("active_rentals"),
            func.count(Rental.id).filter(Rental.rental_status == RentalStatus.LATE).label("overdue_rentals"),
            func.count(Rental.id).filter(Rental.rental_status == RentalStatus.COMPLETED).label("completed_rentals"),
            func.count(Rental.id).filter(Rental.rental_status == RentalStatus.EXTENDED).label("extended_rentals")
        ).where(
            Rental.transaction_type == TransactionType.RENTAL
        )
        
        # Apply filters
        if date_from:
            query = query.where(Rental.rental_start_date >= date_from)
        if date_to:
            query = query.where(Rental.rental_start_date <= date_to)
        if customer_id:
            query = query.where(Rental.customer_id == customer_id)
        if location_id:
            query = query.where(Rental.location_id == location_id)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        return {
            "total_rentals": row.total_rentals or 0,
            "total_revenue": row.total_revenue or Decimal("0"),
            "total_late_fees": row.total_late_fees or Decimal("0"),
            "total_deposits": row.total_deposits or Decimal("0"),
            "average_rental": row.average_rental or Decimal("0"),
            "average_duration": int(row.average_duration or 0),
            "active_rentals": row.active_rentals or 0,
            "overdue_rentals": row.overdue_rentals or 0,
            "completed_rentals": row.completed_rentals or 0,
            "extended_rentals": row.extended_rentals or 0
        }
    
    async def update_rental_status(
        self,
        rental_id: UUID,
        status: RentalStatus,
        return_date: Optional[date] = None
    ) -> bool:
        """Update rental status."""
        rental = await self.get_rental_by_id(rental_id)
        if not rental:
            return False
        
        rental.rental_status = status
        if return_date:
            rental.actual_return_date = return_date
        
        await self.session.commit()
        return True
    
    async def extend_rental(
        self,
        rental_id: UUID,
        new_end_date: date,
        extension_fee: Decimal = Decimal("0")
    ) -> bool:
        """Extend rental period."""
        rental = await self.get_rental_by_id(rental_id)
        if not rental:
            return False
        
        # Update rental
        old_end_date = rental.rental_end_date
        rental.rental_end_date = new_end_date
        rental.extension_count += 1
        
        if extension_fee > 0:
            rental.total_amount += extension_fee
        
        # Create extension record
        extension = RentalExtension(
            rental_id=rental_id,
            extension_number=rental.extension_count,
            original_end_date=old_end_date,
            new_end_date=new_end_date,
            extension_days=(new_end_date - old_end_date).days,
            extension_fee=extension_fee,
            approved_at=datetime.utcnow()
        )
        
        self.session.add(extension)
        await self.session.commit()
        return True
    
    async def calculate_late_fees(self, rental_id: UUID) -> Decimal:
        """Calculate late fees for a rental."""
        rental = await self.get_rental_by_id(rental_id)
        if not rental or not rental.is_overdue:
            return Decimal("0")
        
        days_overdue = rental.days_overdue
        daily_rate = rental.late_fee_rate or Decimal("0")
        
        return daily_rate * days_overdue
    
    async def generate_agreement_number(self) -> str:
        """Generate next rental agreement number."""
        query = select(func.max(Rental.rental_agreement_number)).where(
            Rental.rental_agreement_number.like("RA-%")
        )
        result = await self.session.execute(query)
        max_agreement = result.scalar()
        
        if max_agreement:
            # Extract number from format RA-000001
            try:
                number = int(max_agreement.split("-")[1]) + 1
            except (IndexError, ValueError):
                number = 1
        else:
            number = 1
        
        return f"RA-{number:06d}"


class RentalLineRepository(BaseTransactionLineRepository):
    """Repository for rental line operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_rental_line(self, line_data: Dict[str, Any]) -> RentalLine:
        """Create a new rental line."""
        line = RentalLine(**line_data)
        self.session.add(line)
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def get_rental_lines(self, rental_id: UUID) -> List[RentalLine]:
        """Get all line items for a rental."""
        query = select(RentalLine).where(
            RentalLine.transaction_id == rental_id
        ).order_by(RentalLine.line_number)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_item_condition(
        self,
        line_id: UUID,
        condition_in: str,
        damage_reported: bool = False,
        damage_description: Optional[str] = None,
        damage_cost: Decimal = Decimal("0")
    ) -> bool:
        """Update item condition upon return."""
        line = await self.get_by_id(line_id)
        if not line:
            return False
        
        line.item_condition_in = condition_in
        line.damage_reported = damage_reported
        line.damage_description = damage_description
        line.damage_cost = damage_cost
        
        await self.session.commit()
        return True
    
    async def get_damaged_items(
        self,
        rental_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[RentalLine]:
        """Get items with damage reports."""
        query = select(RentalLine).where(
            or_(
                RentalLine.damage_reported == True,
                RentalLine.damage_cost > 0
            )
        )
        
        if rental_id:
            query = query.where(RentalLine.transaction_id == rental_id)
        
        query = query.order_by(desc(RentalLine.updated_at))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class RentalLifecycleRepository:
    """Repository for rental lifecycle operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_lifecycle(self, lifecycle_data: Dict[str, Any]) -> RentalLifecycle:
        """Create a new rental lifecycle."""
        lifecycle = RentalLifecycle(**lifecycle_data)
        self.session.add(lifecycle)
        await self.session.commit()
        await self.session.refresh(lifecycle)
        return lifecycle
    
    async def get_lifecycle_by_rental_id(self, rental_id: UUID) -> Optional[RentalLifecycle]:
        """Get lifecycle for a rental."""
        query = select(RentalLifecycle).where(
            RentalLifecycle.transaction_id == rental_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_stage(
        self,
        rental_id: UUID,
        new_stage: str,
        stage_entered_at: Optional[datetime] = None
    ) -> bool:
        """Update lifecycle stage."""
        lifecycle = await self.get_lifecycle_by_rental_id(rental_id)
        if not lifecycle:
            return False
        
        lifecycle.stage = new_stage
        lifecycle.stage_entered_at = stage_entered_at or datetime.utcnow()
        
        await self.session.commit()
        return True
    
    async def complete_checkout(self, rental_id: UUID) -> bool:
        """Mark checkout as completed."""
        lifecycle = await self.get_lifecycle_by_rental_id(rental_id)
        if not lifecycle:
            return False
        
        lifecycle.checkout_completed = True
        lifecycle.checkout_completed_at = datetime.utcnow()
        
        await self.session.commit()
        return True
    
    async def complete_checkin(self, rental_id: UUID) -> bool:
        """Mark checkin as completed."""
        lifecycle = await self.get_lifecycle_by_rental_id(rental_id)
        if not lifecycle:
            return False
        
        lifecycle.checkin_completed = True
        lifecycle.checkin_completed_at = datetime.utcnow()
        
        await self.session.commit()
        return True