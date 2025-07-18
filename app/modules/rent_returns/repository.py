"""
Rent Return Repository

Data access layer for rent return operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import func, and_, or_, desc, asc

from app.modules.transactions.base.repository import BaseTransactionRepository, BaseTransactionLineRepository
from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType, TransactionStatus
from app.modules.rent_returns.models import RentReturn, RentReturnLine, RentReturnInspection


class RentReturnsRepository(BaseTransactionRepository):
    """Repository for rent return operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_rent_return(self, return_data: Dict[str, Any]) -> RentReturn:
        """Create a new rent return."""
        rent_return = RentReturn(**return_data)
        rent_return.transaction_type = TransactionType.RETURN
        
        self.session.add(rent_return)
        await self.session.commit()
        await self.session.refresh(rent_return)
        return rent_return
    
    async def get_rent_return_by_id(self, return_id: UUID) -> Optional[RentReturn]:
        """Get rent return by ID with line items."""
        query = select(RentReturn).where(
            RentReturn.id == return_id
        ).options(
            selectinload(RentReturn.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_rent_return_by_number(self, return_number: str) -> Optional[RentReturn]:
        """Get rent return by return number."""
        query = select(RentReturn).where(
            RentReturn.return_number == return_number
        ).options(
            selectinload(RentReturn.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_returns_by_rental(self, rental_id: UUID) -> List[RentReturn]:
        """Get all returns for a specific rental."""
        query = select(RentReturn).where(
            RentReturn.original_rental_id == rental_id
        ).options(
            selectinload(RentReturn.transaction_lines)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_inspections(self, limit: int = 100) -> List[RentReturn]:
        """Get returns with pending inspections."""
        query = select(RentReturn).where(
            RentReturn.inspection_completed == False
        ).order_by(desc(RentReturn.return_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_damaged_returns(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[RentReturn]:
        """Get returns with damage."""
        query = select(RentReturn).where(
            RentReturn.total_damage_cost > 0
        )
        
        if date_from:
            query = query.where(RentReturn.return_date >= date_from)
        if date_to:
            query = query.where(RentReturn.return_date <= date_to)
        
        query = query.order_by(desc(RentReturn.return_date))
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def generate_return_number(self) -> str:
        """Generate next return number."""
        query = select(func.max(RentReturn.return_number)).where(
            RentReturn.return_number.like("RET-%")
        )
        result = await self.session.execute(query)
        max_return = result.scalar()
        
        if max_return:
            try:
                number = int(max_return.split("-")[1]) + 1
            except (IndexError, ValueError):
                number = 1
        else:
            number = 1
        
        return f"RET-{number:06d}"


class RentReturnLineRepository(BaseTransactionLineRepository):
    """Repository for rent return line operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
    
    async def create_rent_return_line(self, line_data: Dict[str, Any]) -> RentReturnLine:
        """Create a new rent return line."""
        line = RentReturnLine(**line_data)
        self.session.add(line)
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def get_damaged_items(self, return_id: Optional[UUID] = None) -> List[RentReturnLine]:
        """Get damaged items from returns."""
        query = select(RentReturnLine).where(
            or_(
                RentReturnLine.damage_noted == True,
                RentReturnLine.repair_cost > 0
            )
        )
        
        if return_id:
            query = query.where(RentReturnLine.transaction_id == return_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class RentReturnInspectionRepository:
    """Repository for rent return inspection operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_inspection(self, inspection_data: Dict[str, Any]) -> RentReturnInspection:
        """Create a new inspection."""
        inspection = RentReturnInspection(**inspection_data)
        self.session.add(inspection)
        await self.session.commit()
        await self.session.refresh(inspection)
        return inspection
    
    async def get_inspection_by_return_id(self, return_id: UUID) -> Optional[RentReturnInspection]:
        """Get inspection for a return."""
        query = select(RentReturnInspection).where(
            RentReturnInspection.return_id == return_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()