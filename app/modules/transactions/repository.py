from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import and_, or_, func, select, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.modules.transactions.models import (
    TransactionHeader, TransactionLine,
    TransactionType, TransactionStatus, PaymentMethod, PaymentStatus,
    RentalPeriodUnit, LineItemType
)
from app.modules.transactions.schemas import (
    TransactionHeaderCreate, TransactionHeaderUpdate,
    TransactionLineCreate, TransactionLineUpdate,
    TransactionSearch
)


class TransactionHeaderRepository:
    """Repository for TransactionHeader operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, transaction_data: TransactionHeaderCreate) -> TransactionHeader:
        """Create a new transaction header."""
        transaction = TransactionHeader(
            transaction_number=transaction_data.transaction_number,
            transaction_type=transaction_data.transaction_type,
            transaction_date=transaction_data.transaction_date,
            customer_id=str(transaction_data.customer_id),
            location_id=str(transaction_data.location_id),
            sales_person_id=str(transaction_data.sales_person_id) if transaction_data.sales_person_id else None,
            status=transaction_data.status,
            payment_status=transaction_data.payment_status,
            reference_transaction_id=str(transaction_data.reference_transaction_id) if transaction_data.reference_transaction_id else None,
            rental_start_date=transaction_data.rental_start_date,
            rental_end_date=transaction_data.rental_end_date,
            notes=transaction_data.notes
        )
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def get_by_id(self, transaction_id: UUID) -> Optional[TransactionHeader]:
        """Get transaction header by ID."""
        query = select(TransactionHeader).where(TransactionHeader.id == transaction_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_number(self, transaction_number: str) -> Optional[TransactionHeader]:
        """Get transaction header by number."""
        query = select(TransactionHeader).where(TransactionHeader.transaction_number == transaction_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_lines(self, transaction_id: UUID) -> Optional[TransactionHeader]:
        """Get transaction header with lines."""
        query = select(TransactionHeader).options(
            selectinload(TransactionHeader.transaction_lines)
        ).where(TransactionHeader.id == transaction_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        sales_person_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> List[TransactionHeader]:
        """Get all transaction headers with optional filtering."""
        query = select(TransactionHeader)
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(TransactionHeader.is_active == True)
        if transaction_type:
            conditions.append(TransactionHeader.transaction_type == transaction_type.value)
        if status:
            conditions.append(TransactionHeader.status == status.value)
        if payment_status:
            conditions.append(TransactionHeader.payment_status == payment_status.value)
        if customer_id:
            conditions.append(TransactionHeader.customer_id == str(customer_id))
        if location_id:
            conditions.append(TransactionHeader.location_id == str(location_id))
        if sales_person_id:
            conditions.append(TransactionHeader.sales_person_id == str(sales_person_id))
        if date_from:
            conditions.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            conditions.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(TransactionHeader.transaction_date)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_all(
        self,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        sales_person_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> int:
        """Count all transaction headers with optional filtering."""
        query = select(func.count(TransactionHeader.id))
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(TransactionHeader.is_active == True)
        if transaction_type:
            conditions.append(TransactionHeader.transaction_type == transaction_type.value)
        if status:
            conditions.append(TransactionHeader.status == status.value)
        if payment_status:
            conditions.append(TransactionHeader.payment_status == payment_status.value)
        if customer_id:
            conditions.append(TransactionHeader.customer_id == str(customer_id))
        if location_id:
            conditions.append(TransactionHeader.location_id == str(location_id))
        if sales_person_id:
            conditions.append(TransactionHeader.sales_person_id == str(sales_person_id))
        if date_from:
            conditions.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            conditions.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def search(
        self, 
        search_params: TransactionSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[TransactionHeader]:
        """Search transaction headers."""
        query = select(TransactionHeader)
        
        conditions = []
        if active_only:
            conditions.append(TransactionHeader.is_active == True)
        
        if search_params.transaction_number:
            conditions.append(TransactionHeader.transaction_number.ilike(f"%{search_params.transaction_number}%"))
        if search_params.transaction_type:
            conditions.append(TransactionHeader.transaction_type == search_params.transaction_type.value)
        if search_params.customer_id:
            conditions.append(TransactionHeader.customer_id == str(search_params.customer_id))
        if search_params.location_id:
            conditions.append(TransactionHeader.location_id == str(search_params.location_id))
        if search_params.sales_person_id:
            conditions.append(TransactionHeader.sales_person_id == str(search_params.sales_person_id))
        if search_params.status:
            conditions.append(TransactionHeader.status == search_params.status.value)
        if search_params.payment_status:
            conditions.append(TransactionHeader.payment_status == search_params.payment_status.value)
        if search_params.date_from:
            conditions.append(TransactionHeader.transaction_date >= datetime.combine(search_params.date_from, datetime.min.time()))
        if search_params.date_to:
            conditions.append(TransactionHeader.transaction_date <= datetime.combine(search_params.date_to, datetime.max.time()))
        if search_params.amount_from:
            conditions.append(TransactionHeader.total_amount >= search_params.amount_from)
        if search_params.amount_to:
            conditions.append(TransactionHeader.total_amount <= search_params.amount_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(TransactionHeader.transaction_date)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_customer(self, customer_id: UUID, active_only: bool = True) -> List[TransactionHeader]:
        """Get transactions by customer."""
        query = select(TransactionHeader).where(TransactionHeader.customer_id == str(customer_id))
        
        if active_only:
            query = query.where(TransactionHeader.is_active == True)
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_location(self, location_id: UUID, active_only: bool = True) -> List[TransactionHeader]:
        """Get transactions by location."""
        query = select(TransactionHeader).where(TransactionHeader.location_id == str(location_id))
        
        if active_only:
            query = query.where(TransactionHeader.is_active == True)
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_sales_person(self, sales_person_id: UUID, active_only: bool = True) -> List[TransactionHeader]:
        """Get transactions by sales person."""
        query = select(TransactionHeader).where(TransactionHeader.sales_person_id == str(sales_person_id))
        
        if active_only:
            query = query.where(TransactionHeader.is_active == True)
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_overdue_transactions(self, as_of_date: date = None) -> List[TransactionHeader]:
        """Get overdue transactions."""
        if as_of_date is None:
            as_of_date = date.today()
        
        query = select(TransactionHeader).where(
            and_(
                TransactionHeader.payment_status == PaymentStatus.OVERDUE.value,
                TransactionHeader.status.not_in([
                    TransactionStatus.CANCELLED.value,
                    TransactionStatus.REFUNDED.value
                ]),
                TransactionHeader.is_active == True
            )
        )
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_outstanding_transactions(self) -> List[TransactionHeader]:
        """Get transactions with outstanding balance."""
        query = select(TransactionHeader).where(
            and_(
                TransactionHeader.paid_amount < TransactionHeader.total_amount,
                TransactionHeader.payment_status != PaymentStatus.CANCELLED.value,
                TransactionHeader.status.not_in([
                    TransactionStatus.CANCELLED.value,
                    TransactionStatus.REFUNDED.value
                ]),
                TransactionHeader.is_active == True
            )
        )
        
        query = query.order_by(desc(TransactionHeader.transaction_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rental_transactions_due_for_return(self, as_of_date: date = None) -> List[TransactionHeader]:
        """Get rental transactions due for return."""
        if as_of_date is None:
            as_of_date = date.today()
        
        query = select(TransactionHeader).where(
            and_(
                TransactionHeader.transaction_type == TransactionType.RENTAL.value,
                TransactionHeader.status == TransactionStatus.IN_PROGRESS.value,
                TransactionHeader.rental_end_date <= as_of_date,
                TransactionHeader.actual_return_date.is_(None),
                TransactionHeader.is_active == True
            )
        )
        
        query = query.order_by(asc(TransactionHeader.rental_end_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, transaction_id: UUID, transaction_data: TransactionHeaderUpdate) -> Optional[TransactionHeader]:
        """Update a transaction header."""
        query = select(TransactionHeader).where(TransactionHeader.id == transaction_id)
        result = await self.session.execute(query)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            return None
        
        # Update fields
        update_data = transaction_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['customer_id', 'location_id', 'sales_person_id', 'reference_transaction_id']:
                setattr(transaction, field, str(value) if value else None)
            else:
                setattr(transaction, field, value)
        
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def delete(self, transaction_id: UUID) -> bool:
        """Soft delete a transaction header."""
        query = select(TransactionHeader).where(TransactionHeader.id == transaction_id)
        result = await self.session.execute(query)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            return False
        
        transaction.is_active = False
        await self.session.commit()
        return True
    
    async def get_transaction_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """Get transaction summary statistics."""
        query = select(TransactionHeader)
        
        conditions = []
        if active_only:
            conditions.append(TransactionHeader.is_active == True)
        if date_from:
            conditions.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            conditions.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        total_transactions = len(transactions)
        total_amount = sum(t.total_amount for t in transactions)
        total_paid = sum(t.paid_amount for t in transactions)
        total_outstanding = total_amount - total_paid
        
        # Count by status
        status_counts = {}
        for status in TransactionStatus:
            status_counts[status.value] = len([t for t in transactions if t.status == status.value])
        
        # Count by type
        type_counts = {}
        for transaction_type in TransactionType:
            type_counts[transaction_type.value] = len([t for t in transactions if t.transaction_type == transaction_type.value])
        
        # Count by payment status
        payment_status_counts = {}
        for payment_status in PaymentStatus:
            payment_status_counts[payment_status.value] = len([t for t in transactions if t.payment_status == payment_status.value])
        
        return {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'transactions_by_status': status_counts,
            'transactions_by_type': type_counts,
            'transactions_by_payment_status': payment_status_counts
        }


class TransactionLineRepository:
    """Repository for TransactionLine operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, transaction_id: UUID, line_data: TransactionLineCreate) -> TransactionLine:
        """Create a new transaction line."""
        line = TransactionLine(
            transaction_id=str(transaction_id),
            line_number=line_data.line_number,
            line_type=line_data.line_type,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            item_id=str(line_data.item_id) if line_data.item_id else None,
            inventory_unit_id=str(line_data.inventory_unit_id) if line_data.inventory_unit_id else None,
            discount_percentage=line_data.discount_percentage,
            discount_amount=line_data.discount_amount,
            tax_rate=line_data.tax_rate,
            rental_period_value=line_data.rental_period_value,
            rental_period_unit=line_data.rental_period_unit,
            rental_start_date=line_data.rental_start_date,
            rental_end_date=line_data.rental_end_date,
            notes=line_data.notes
        )
        
        # Calculate line total
        line.calculate_line_total()
        
        self.session.add(line)
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def get_by_id(self, line_id: UUID) -> Optional[TransactionLine]:
        """Get transaction line by ID."""
        query = select(TransactionLine).where(TransactionLine.id == line_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_transaction(self, transaction_id: UUID, active_only: bool = True) -> List[TransactionLine]:
        """Get transaction lines by transaction."""
        query = select(TransactionLine).where(TransactionLine.transaction_id == str(transaction_id))
        
        if active_only:
            query = query.where(TransactionLine.is_active == True)
        
        query = query.order_by(asc(TransactionLine.line_number))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_item(self, item_id: UUID, active_only: bool = True) -> List[TransactionLine]:
        """Get transaction lines by item."""
        query = select(TransactionLine).where(TransactionLine.item_id == str(item_id))
        
        if active_only:
            query = query.where(TransactionLine.is_active == True)
        
        query = query.order_by(desc(TransactionLine.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_inventory_unit(self, inventory_unit_id: UUID, active_only: bool = True) -> List[TransactionLine]:
        """Get transaction lines by inventory unit."""
        query = select(TransactionLine).where(TransactionLine.inventory_unit_id == str(inventory_unit_id))
        
        if active_only:
            query = query.where(TransactionLine.is_active == True)
        
        query = query.order_by(desc(TransactionLine.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rental_lines_due_for_return(self, as_of_date: date = None) -> List[TransactionLine]:
        """Get rental lines due for return."""
        if as_of_date is None:
            as_of_date = date.today()
        
        query = select(TransactionLine).where(
            and_(
                TransactionLine.line_type == LineItemType.PRODUCT.value,
                TransactionLine.rental_end_date <= as_of_date,
                TransactionLine.return_date.is_(None),
                TransactionLine.returned_quantity < TransactionLine.quantity,
                TransactionLine.is_active == True
            )
        )
        
        query = query.order_by(asc(TransactionLine.rental_end_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, line_id: UUID, line_data: TransactionLineUpdate) -> Optional[TransactionLine]:
        """Update a transaction line."""
        query = select(TransactionLine).where(TransactionLine.id == line_id)
        result = await self.session.execute(query)
        line = result.scalar_one_or_none()
        
        if not line:
            return None
        
        # Update fields
        update_data = line_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['item_id', 'inventory_unit_id']:
                setattr(line, field, str(value) if value else None)
            else:
                setattr(line, field, value)
        
        # Recalculate line total
        line.calculate_line_total()
        
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def delete(self, line_id: UUID) -> bool:
        """Soft delete a transaction line."""
        query = select(TransactionLine).where(TransactionLine.id == line_id)
        result = await self.session.execute(query)
        line = result.scalar_one_or_none()
        
        if not line:
            return False
        
        line.is_active = False
        await self.session.commit()
        return True
    
    async def get_next_line_number(self, transaction_id: UUID) -> int:
        """Get the next line number for a transaction."""
        query = select(func.coalesce(func.max(TransactionLine.line_number), 0) + 1).where(
            TransactionLine.transaction_id == str(transaction_id)
        )
        result = await self.session.execute(query)
        return result.scalar()
    
    async def resequence_lines(self, transaction_id: UUID) -> bool:
        """Resequence line numbers for a transaction."""
        query = select(TransactionLine).where(
            and_(
                TransactionLine.transaction_id == str(transaction_id),
                TransactionLine.is_active == True
            )
        ).order_by(TransactionLine.line_number)
        
        result = await self.session.execute(query)
        lines = result.scalars().all()
        
        for i, line in enumerate(lines, 1):
            line.line_number = i
        
        await self.session.commit()
        return True