"""
Rental service for managing rental lifecycle operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from app.modules.transactions.models import (
    TransactionHeader, 
    TransactionLine,
    TransactionType,
    TransactionStatus,
    RentalStatus,
    RentalLifecycle,
    RentalReturnEvent,
    RentalItemInspection,
    ReturnEventType,
    InspectionCondition
)
from app.core.errors import NotFoundError, ValidationError, ConflictError
import logging

logger = logging.getLogger(__name__)


class RentalStatusService:
    """Service for managing rental status transitions."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_rental_transaction(self, transaction_id: UUID) -> TransactionHeader:
        """Get rental transaction with validation."""
        result = await self.session.execute(
            select(TransactionHeader)
            .where(
                and_(
                    TransactionHeader.id == transaction_id,
                    TransactionHeader.transaction_type == TransactionType.RENTAL,
                    TransactionHeader.is_active == True
                )
            )
            .options(selectinload(TransactionHeader.transaction_lines))
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise NotFoundError(f"Rental transaction {transaction_id} not found")
        
        return transaction
    
    async def get_or_create_lifecycle(self, transaction_id: UUID) -> RentalLifecycle:
        """Get existing lifecycle or create new one."""
        # Try to get existing lifecycle
        result = await self.session.execute(
            select(RentalLifecycle)
            .where(RentalLifecycle.transaction_id == transaction_id)
        )
        lifecycle = result.scalar_one_or_none()
        
        if lifecycle:
            return lifecycle
        
        # Create new lifecycle for transaction
        transaction = await self.get_rental_transaction(transaction_id)
        
        lifecycle = RentalLifecycle(
            transaction_id=transaction_id,
            current_status=RentalStatus.ACTIVE.value,
            expected_return_date=transaction.rental_end_date,
            total_returned_quantity=0,
            total_late_fees=0,
            total_damage_fees=0,
            total_other_fees=0
        )
        
        self.session.add(lifecycle)
        await self.session.commit()
        await self.session.refresh(lifecycle)
        
        # Update transaction header status
        await self.session.execute(
            update(TransactionHeader)
            .where(TransactionHeader.id == transaction_id)
            .values(current_rental_status=RentalStatus.ACTIVE.value)
        )
        await self.session.commit()
        
        logger.info(f"Created rental lifecycle for transaction {transaction_id}")
        return lifecycle
    
    async def update_rental_status(
        self, 
        transaction_id: UUID, 
        new_status: RentalStatus, 
        changed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> RentalLifecycle:
        """Update rental status with validation."""
        lifecycle = await self.get_or_create_lifecycle(transaction_id)
        old_status = lifecycle.current_status
        
        # Validate status transition
        if not self._is_valid_status_transition(old_status, new_status.value):
            raise ValidationError(f"Invalid status transition from {old_status} to {new_status.value}")
        
        # Update lifecycle
        lifecycle.current_status = new_status.value
        lifecycle.last_status_change = datetime.utcnow()
        lifecycle.status_changed_by = changed_by
        if notes:
            lifecycle.notes = notes
        
        # Update transaction header
        await self.session.execute(
            update(TransactionHeader)
            .where(TransactionHeader.id == transaction_id)
            .values(current_rental_status=new_status.value)
        )
        
        await self.session.commit()
        logger.info(f"Updated rental {transaction_id} status from {old_status} to {new_status.value}")
        
        return lifecycle
    
    def _is_valid_status_transition(self, from_status: str, to_status: str) -> bool:
        """Validate if status transition is allowed."""
        valid_transitions = {
            RentalStatus.ACTIVE.value: [
                RentalStatus.LATE.value,
                RentalStatus.EXTENDED.value,
                RentalStatus.PARTIAL_RETURN.value,
                RentalStatus.COMPLETED.value
            ],
            RentalStatus.LATE.value: [
                RentalStatus.EXTENDED.value,
                RentalStatus.LATE_PARTIAL_RETURN.value,
                RentalStatus.COMPLETED.value
            ],
            RentalStatus.EXTENDED.value: [
                RentalStatus.ACTIVE.value,
                RentalStatus.LATE.value,
                RentalStatus.PARTIAL_RETURN.value,
                RentalStatus.COMPLETED.value
            ],
            RentalStatus.PARTIAL_RETURN.value: [
                RentalStatus.LATE_PARTIAL_RETURN.value,
                RentalStatus.COMPLETED.value
            ],
            RentalStatus.LATE_PARTIAL_RETURN.value: [
                RentalStatus.COMPLETED.value
            ],
            RentalStatus.COMPLETED.value: []  # Terminal state
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    async def auto_update_late_status(self, as_of_date: Optional[date] = None) -> List[UUID]:
        """Automatically update rentals to LATE status based on due date."""
        if not as_of_date:
            as_of_date = date.today()
        
        # Find active rentals past due date
        result = await self.session.execute(
            select(TransactionHeader.id)
            .where(
                and_(
                    TransactionHeader.transaction_type == TransactionType.RENTAL,
                    TransactionHeader.current_rental_status.in_([
                        RentalStatus.ACTIVE.value,
                        RentalStatus.EXTENDED.value
                    ]),
                    TransactionHeader.rental_end_date < as_of_date,
                    TransactionHeader.is_active == True
                )
            )
        )
        
        overdue_ids = [row[0] for row in result.fetchall()]
        
        # Update to LATE status
        for transaction_id in overdue_ids:
            try:
                lifecycle = await self.get_or_create_lifecycle(transaction_id)
                current_status = RentalStatus(lifecycle.current_status)
                
                if current_status == RentalStatus.ACTIVE:
                    await self.update_rental_status(transaction_id, RentalStatus.LATE)
                elif current_status == RentalStatus.EXTENDED:
                    await self.update_rental_status(transaction_id, RentalStatus.LATE)
                elif current_status == RentalStatus.PARTIAL_RETURN:
                    await self.update_rental_status(transaction_id, RentalStatus.LATE_PARTIAL_RETURN)
                    
            except Exception as e:
                logger.error(f"Error updating rental {transaction_id} to late status: {e}")
        
        logger.info(f"Updated {len(overdue_ids)} rentals to late status")
        return overdue_ids


class RentalReturnService:
    """Service for managing rental return operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.status_service = RentalStatusService(session)
    
    async def initiate_return(
        self,
        transaction_id: UUID,
        return_date: date,
        items_to_return: List[Dict[str, Any]],
        processed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> RentalReturnEvent:
        """Initiate a return event for rental items."""
        lifecycle = await self.status_service.get_or_create_lifecycle(transaction_id)
        transaction = await self.status_service.get_rental_transaction(transaction_id)
        
        # Validate items to return
        total_quantity = Decimal('0')
        validated_items = []
        
        for item in items_to_return:
            line_id = UUID(item['transaction_line_id'])
            quantity = Decimal(str(item['quantity']))
            
            # Find transaction line
            line = next((l for l in transaction.transaction_lines if l.id == line_id), None)
            if not line:
                raise ValidationError(f"Transaction line {line_id} not found")
            
            # Check available quantity
            available = line.quantity - line.returned_quantity
            if quantity > available:
                raise ValidationError(f"Cannot return {quantity} of item {line.description}, only {available} available")
            
            validated_items.append({
                'transaction_line_id': str(line_id),
                'quantity': float(quantity),
                'item_description': line.description,
                'unit_price': float(line.unit_price)
            })
            total_quantity += quantity
        
        # Create return event
        return_event = RentalReturnEvent(
            rental_lifecycle_id=lifecycle.id,
            event_type=ReturnEventType.PARTIAL_RETURN.value,
            event_date=return_date,
            processed_by=processed_by,
            items_returned=validated_items,
            total_quantity_returned=total_quantity,
            notes=notes
        )
        
        self.session.add(return_event)
        await self.session.commit()
        await self.session.refresh(return_event)
        
        logger.info(f"Initiated return event {return_event.id} for rental {transaction_id}")
        return return_event
    
    async def record_inspection(
        self,
        return_event_id: UUID,
        transaction_line_id: UUID,
        quantity_inspected: Decimal,
        condition: InspectionCondition,
        inspected_by: Optional[UUID] = None,
        damage_details: Optional[Dict[str, Any]] = None
    ) -> RentalItemInspection:
        """Record inspection results for returned items."""
        # Get return event
        result = await self.session.execute(
            select(RentalReturnEvent)
            .where(RentalReturnEvent.id == return_event_id)
            .options(selectinload(RentalReturnEvent.rental_lifecycle))
        )
        return_event = result.scalar_one_or_none()
        
        if not return_event:
            raise NotFoundError(f"Return event {return_event_id} not found")
        
        # Create inspection record
        inspection = RentalItemInspection(
            return_event_id=return_event_id,
            transaction_line_id=transaction_line_id,
            quantity_inspected=quantity_inspected,
            condition=condition.value,
            inspected_by=inspected_by,
            has_damage=damage_details is not None,
            damage_description=damage_details.get('description') if damage_details else None,
            damage_photos=damage_details.get('photos') if damage_details else None,
            damage_fee_assessed=Decimal(str(damage_details.get('damage_fee', 0))) if damage_details else Decimal('0'),
            cleaning_fee_assessed=Decimal(str(damage_details.get('cleaning_fee', 0))) if damage_details else Decimal('0'),
            replacement_required=damage_details.get('replacement_required', False) if damage_details else False,
            replacement_cost=Decimal(str(damage_details.get('replacement_cost', 0))) if damage_details and damage_details.get('replacement_cost') else None,
            return_to_stock=not (damage_details and damage_details.get('replacement_required', False)),
            inspection_notes=damage_details.get('notes') if damage_details else None
        )
        
        self.session.add(inspection)
        
        # Update return event with fees
        if damage_details:
            return_event.damage_fees_charged += inspection.damage_fee_assessed + inspection.cleaning_fee_assessed
            if inspection.replacement_cost:
                return_event.other_fees_charged += inspection.replacement_cost
        
        await self.session.commit()
        await self.session.refresh(inspection)
        
        logger.info(f"Recorded inspection for return event {return_event_id}, line {transaction_line_id}")
        return inspection
    
    async def complete_return(
        self,
        return_event_id: UUID,
        payment_collected: Decimal = Decimal('0'),
        refund_issued: Decimal = Decimal('0'),
        receipt_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> RentalReturnEvent:
        """Complete a return event with payment processing."""
        # Get return event with inspections
        result = await self.session.execute(
            select(RentalReturnEvent)
            .where(RentalReturnEvent.id == return_event_id)
            .options(
                selectinload(RentalReturnEvent.rental_lifecycle),
            )
        )
        return_event = result.scalar_one_or_none()
        
        if not return_event:
            raise NotFoundError(f"Return event {return_event_id} not found")
        
        lifecycle = return_event.rental_lifecycle
        
        # Update return event with payment info
        return_event.payment_collected = payment_collected
        return_event.refund_issued = refund_issued
        return_event.receipt_number = receipt_number
        if notes:
            return_event.notes = notes
        
        # Update lifecycle totals
        lifecycle.total_returned_quantity += return_event.total_quantity_returned
        lifecycle.total_damage_fees += return_event.damage_fees_charged
        lifecycle.total_late_fees += return_event.late_fees_charged
        lifecycle.total_other_fees += return_event.other_fees_charged
        
        # Update transaction line returned quantities
        if return_event.items_returned:
            for item in return_event.items_returned:
                line_id = UUID(item['transaction_line_id'])
                quantity = Decimal(str(item['quantity']))
                
                await self.session.execute(
                    update(TransactionLine)
                    .where(TransactionLine.id == line_id)
                    .values(
                        returned_quantity=TransactionLine.returned_quantity + quantity,
                        return_date=return_event.event_date
                    )
                )
        
        # Check if all items are returned and update status
        transaction = await self.status_service.get_rental_transaction(lifecycle.transaction_id)
        total_quantity = sum(line.quantity for line in transaction.transaction_lines)
        
        if lifecycle.total_returned_quantity >= total_quantity:
            # All items returned - mark as completed
            await self.status_service.update_rental_status(
                lifecycle.transaction_id, 
                RentalStatus.COMPLETED
            )
            return_event.event_type = ReturnEventType.FULL_RETURN.value
        else:
            # Partial return - update status accordingly
            current_status = RentalStatus(lifecycle.current_status)
            if current_status == RentalStatus.ACTIVE:
                await self.status_service.update_rental_status(
                    lifecycle.transaction_id, 
                    RentalStatus.PARTIAL_RETURN
                )
            elif current_status == RentalStatus.LATE:
                await self.status_service.update_rental_status(
                    lifecycle.transaction_id, 
                    RentalStatus.LATE_PARTIAL_RETURN
                )
        
        await self.session.commit()
        logger.info(f"Completed return event {return_event_id}")
        
        return return_event
    
    async def extend_rental(
        self,
        transaction_id: UUID,
        new_end_date: date,
        reason: str,
        processed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> RentalReturnEvent:
        """Extend rental period."""
        lifecycle = await self.status_service.get_or_create_lifecycle(transaction_id)
        
        # Create extension event
        extension_event = RentalReturnEvent(
            rental_lifecycle_id=lifecycle.id,
            event_type=ReturnEventType.EXTENSION.value,
            event_date=date.today(),
            processed_by=processed_by,
            new_return_date=new_end_date,
            extension_reason=reason,
            notes=notes
        )
        
        self.session.add(extension_event)
        
        # Update lifecycle and transaction
        lifecycle.expected_return_date = new_end_date
        
        await self.session.execute(
            update(TransactionHeader)
            .where(TransactionHeader.id == transaction_id)
            .values(rental_end_date=new_end_date)
        )
        
        # Update status to EXTENDED
        await self.status_service.update_rental_status(
            transaction_id, 
            RentalStatus.EXTENDED,
            changed_by=processed_by
        )
        
        await self.session.commit()
        logger.info(f"Extended rental {transaction_id} to {new_end_date}")
        
        return extension_event


class RentalService:
    """Main rental service combining all rental operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.status_service = RentalStatusService(session)
        self.return_service = RentalReturnService(session)
    
    async def get_active_rentals(
        self, 
        customer_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        overdue_only: bool = False
    ) -> List[TransactionHeader]:
        """Get list of active rentals with filters."""
        query = select(TransactionHeader).where(
            and_(
                TransactionHeader.transaction_type == TransactionType.RENTAL,
                TransactionHeader.current_rental_status.in_([
                    RentalStatus.ACTIVE.value,
                    RentalStatus.LATE.value,
                    RentalStatus.EXTENDED.value,
                    RentalStatus.PARTIAL_RETURN.value,
                    RentalStatus.LATE_PARTIAL_RETURN.value
                ]),
                TransactionHeader.is_active == True
            )
        ).options(selectinload(TransactionHeader.transaction_lines))
        
        if customer_id:
            query = query.where(TransactionHeader.customer_id == str(customer_id))
        
        if location_id:
            query = query.where(TransactionHeader.location_id == str(location_id))
        
        if overdue_only:
            query = query.where(TransactionHeader.rental_end_date < date.today())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rental_details(self, transaction_id: UUID) -> Dict[str, Any]:
        """Get comprehensive rental details."""
        transaction = await self.status_service.get_rental_transaction(transaction_id)
        lifecycle = await self.status_service.get_or_create_lifecycle(transaction_id)
        
        # Get return events
        result = await self.session.execute(
            select(RentalReturnEvent)
            .where(RentalReturnEvent.rental_lifecycle_id == lifecycle.id)
            .order_by(RentalReturnEvent.event_date.desc())
        )
        return_events = result.scalars().all()
        
        return {
            'transaction': transaction,
            'lifecycle': lifecycle,
            'return_events': return_events,
            'total_fees': lifecycle.total_fees,
            'is_overdue': transaction.rental_end_date < date.today() if transaction.rental_end_date else False
        }