from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.transactions.models import (
    TransactionHeader, TransactionLine,
    TransactionType, TransactionStatus, PaymentMethod, PaymentStatus,
    RentalPeriodUnit, LineItemType
)
from app.modules.transactions.repository import (
    TransactionHeaderRepository, TransactionLineRepository
)
from app.modules.transactions.schemas import (
    TransactionHeaderCreate, TransactionHeaderUpdate, TransactionHeaderResponse,
    TransactionHeaderListResponse, TransactionWithLinesResponse,
    TransactionLineCreate, TransactionLineUpdate, TransactionLineResponse,
    TransactionLineListResponse, PaymentCreate, RefundCreate, StatusUpdate,
    DiscountApplication, ReturnProcessing, RentalPeriodUpdate, RentalReturn,
    TransactionSummary, TransactionReport, TransactionSearch
)
from app.modules.customers.repository import CustomerRepository
from app.modules.inventory.repository import ItemRepository, InventoryUnitRepository


class TransactionService:
    """Service for transaction processing operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repository = TransactionHeaderRepository(session)
        self.line_repository = TransactionLineRepository(session)
        self.customer_repository = CustomerRepository(session)
        self.item_repository = ItemRepository(session)
        self.inventory_unit_repository = InventoryUnitRepository(session)
    
    # Transaction Header operations
    async def create_transaction(self, transaction_data: TransactionHeaderCreate) -> TransactionHeaderResponse:
        """Create a new transaction."""
        # Check if transaction number already exists
        existing_transaction = await self.transaction_repository.get_by_number(transaction_data.transaction_number)
        if existing_transaction:
            raise ConflictError(f"Transaction with number '{transaction_data.transaction_number}' already exists")
        
        # Verify customer exists
        customer = await self.customer_repository.get_by_id(transaction_data.customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {transaction_data.customer_id} not found")
        
        # Verify customer can transact
        if not customer.can_transact():
            raise ValidationError("Customer cannot transact due to blacklist status")
        
        # Create transaction
        transaction = await self.transaction_repository.create(transaction_data)
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_transaction(self, transaction_id: UUID) -> TransactionHeaderResponse:
        """Get transaction by ID."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_transaction_by_number(self, transaction_number: str) -> TransactionHeaderResponse:
        """Get transaction by number."""
        transaction = await self.transaction_repository.get_by_number(transaction_number)
        if not transaction:
            raise NotFoundError(f"Transaction with number '{transaction_number}' not found")
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_transaction_with_lines(self, transaction_id: UUID) -> TransactionWithLinesResponse:
        """Get transaction with lines."""
        transaction = await self.transaction_repository.get_with_lines(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        return TransactionWithLinesResponse.model_validate(transaction)
    
    async def get_transactions(
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
    ) -> List[TransactionHeaderListResponse]:
        """Get all transactions with optional filtering."""
        transactions = await self.transaction_repository.get_all(
            skip=skip,
            limit=limit,
            transaction_type=transaction_type,
            status=status,
            payment_status=payment_status,
            customer_id=customer_id,
            location_id=location_id,
            sales_person_id=sales_person_id,
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        return [TransactionHeaderListResponse.model_validate(transaction) for transaction in transactions]
    
    async def search_transactions(
        self, 
        search_params: TransactionSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[TransactionHeaderListResponse]:
        """Search transactions."""
        transactions = await self.transaction_repository.search(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [TransactionHeaderListResponse.model_validate(transaction) for transaction in transactions]
    
    async def update_transaction(self, transaction_id: UUID, transaction_data: TransactionHeaderUpdate) -> TransactionHeaderResponse:
        """Update a transaction."""
        # Check if transaction exists
        existing_transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not existing_transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Check if transaction can be updated
        if existing_transaction.status in [TransactionStatus.COMPLETED.value, TransactionStatus.CANCELLED.value, TransactionStatus.REFUNDED.value]:
            raise ValidationError("Cannot update completed, cancelled, or refunded transactions")
        
        # Update transaction
        transaction = await self.transaction_repository.update(transaction_id, transaction_data)
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def delete_transaction(self, transaction_id: UUID) -> bool:
        """Delete a transaction."""
        # Check if transaction exists
        existing_transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not existing_transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Check if transaction can be deleted
        if existing_transaction.status not in [TransactionStatus.DRAFT.value, TransactionStatus.PENDING.value]:
            raise ValidationError("Can only delete draft or pending transactions")
        
        return await self.transaction_repository.delete(transaction_id)
    
    async def update_transaction_status(self, transaction_id: UUID, status_update: StatusUpdate) -> TransactionHeaderResponse:
        """Update transaction status."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Validate status transition
        if not transaction.can_transition_to(status_update.status):
            raise ValidationError(f"Cannot transition from {transaction.status} to {status_update.status.value}")
        
        # Update status
        transaction.update_status(status_update.status)
        
        # Add notes if provided
        if status_update.notes:
            status_note = f"\n[STATUS UPDATE] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {status_update.notes}"
            transaction.notes = (transaction.notes or "") + status_note
        
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def apply_payment(self, transaction_id: UUID, payment_data: PaymentCreate) -> TransactionHeaderResponse:
        """Apply payment to transaction."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Validate payment amount
        if payment_data.amount > transaction.balance_due:
            raise ValidationError("Payment amount exceeds balance due")
        
        # Apply payment
        transaction.apply_payment(
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            payment_reference=payment_data.payment_reference
        )
        
        # Add payment notes
        if payment_data.notes:
            payment_note = f"\n[PAYMENT] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: ${payment_data.amount} via {payment_data.payment_method.value} - {payment_data.notes}"
            transaction.notes = (transaction.notes or "") + payment_note
        
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def process_refund(self, transaction_id: UUID, refund_data: RefundCreate) -> TransactionHeaderResponse:
        """Process refund for transaction."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Process refund
        transaction.process_refund(
            refund_amount=refund_data.refund_amount,
            reason=refund_data.reason
        )
        
        # Add refund notes
        if refund_data.notes:
            refund_note = f"\n[REFUND NOTES] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {refund_data.notes}"
            transaction.notes = (transaction.notes or "") + refund_note
        
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def cancel_transaction(self, transaction_id: UUID, reason: str) -> TransactionHeaderResponse:
        """Cancel transaction."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Cancel transaction
        transaction.cancel_transaction(reason)
        
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def mark_transaction_overdue(self, transaction_id: UUID) -> TransactionHeaderResponse:
        """Mark transaction as overdue."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Mark as overdue
        transaction.mark_as_overdue()
        
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def complete_rental_return(self, transaction_id: UUID, return_data: RentalReturn) -> TransactionHeaderResponse:
        """Complete rental return."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Complete rental return
        transaction.complete_rental_return(return_data.actual_return_date)
        
        # Add return notes
        if return_data.condition_notes or return_data.notes:
            return_note = f"\n[RENTAL RETURN] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: "
            if return_data.condition_notes:
                return_note += f"Condition: {return_data.condition_notes}. "
            if return_data.notes:
                return_note += f"Notes: {return_data.notes}"
            transaction.notes = (transaction.notes or "") + return_note
        
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return TransactionHeaderResponse.model_validate(transaction)
    
    # Transaction Line operations
    async def add_transaction_line(self, transaction_id: UUID, line_data: TransactionLineCreate) -> TransactionLineResponse:
        """Add line to transaction."""
        # Check if transaction exists
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        # Check if transaction can be modified
        if transaction.status in [TransactionStatus.COMPLETED.value, TransactionStatus.CANCELLED.value, TransactionStatus.REFUNDED.value]:
            raise ValidationError("Cannot add lines to completed, cancelled, or refunded transactions")
        
        # Verify item exists if provided
        if line_data.item_id:
            item = await self.item_repository.get_by_id(line_data.item_id)
            if not item:
                raise NotFoundError(f"Item with ID {line_data.item_id} not found")
        
        # Verify inventory unit exists if provided
        if line_data.inventory_unit_id:
            inventory_unit = await self.inventory_unit_repository.get_by_id(line_data.inventory_unit_id)
            if not inventory_unit:
                raise NotFoundError(f"Inventory unit with ID {line_data.inventory_unit_id} not found")
        
        # Create line
        line = await self.line_repository.create(transaction_id, line_data)
        
        # Recalculate transaction totals
        await self._recalculate_transaction_totals(transaction_id)
        
        return TransactionLineResponse.model_validate(line)
    
    async def get_transaction_line(self, line_id: UUID) -> TransactionLineResponse:
        """Get transaction line by ID."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        return TransactionLineResponse.model_validate(line)
    
    async def get_transaction_lines(self, transaction_id: UUID, active_only: bool = True) -> List[TransactionLineResponse]:
        """Get transaction lines."""
        lines = await self.line_repository.get_by_transaction(transaction_id, active_only)
        return [TransactionLineResponse.model_validate(line) for line in lines]
    
    async def update_transaction_line(self, line_id: UUID, line_data: TransactionLineUpdate) -> TransactionLineResponse:
        """Update transaction line."""
        # Check if line exists
        existing_line = await self.line_repository.get_by_id(line_id)
        if not existing_line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        # Check if transaction can be modified
        transaction = await self.transaction_repository.get_by_id(UUID(existing_line.transaction_id))
        if transaction.status in [TransactionStatus.COMPLETED.value, TransactionStatus.CANCELLED.value, TransactionStatus.REFUNDED.value]:
            raise ValidationError("Cannot update lines in completed, cancelled, or refunded transactions")
        
        # Update line
        line = await self.line_repository.update(line_id, line_data)
        
        # Recalculate transaction totals
        await self._recalculate_transaction_totals(UUID(existing_line.transaction_id))
        
        return TransactionLineResponse.model_validate(line)
    
    async def delete_transaction_line(self, line_id: UUID) -> bool:
        """Delete transaction line."""
        # Check if line exists
        existing_line = await self.line_repository.get_by_id(line_id)
        if not existing_line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        # Check if transaction can be modified
        transaction = await self.transaction_repository.get_by_id(UUID(existing_line.transaction_id))
        if transaction.status in [TransactionStatus.COMPLETED.value, TransactionStatus.CANCELLED.value, TransactionStatus.REFUNDED.value]:
            raise ValidationError("Cannot delete lines from completed, cancelled, or refunded transactions")
        
        # Delete line
        success = await self.line_repository.delete(line_id)
        
        if success:
            # Recalculate transaction totals
            await self._recalculate_transaction_totals(UUID(existing_line.transaction_id))
        
        return success
    
    async def apply_line_discount(self, line_id: UUID, discount_data: DiscountApplication) -> TransactionLineResponse:
        """Apply discount to transaction line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        # Apply discount
        line.apply_discount(
            discount_percentage=discount_data.discount_percentage,
            discount_amount=discount_data.discount_amount
        )
        
        # Add discount notes
        if discount_data.reason:
            discount_note = f"\n[DISCOUNT] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {discount_data.reason}"
            line.notes = (line.notes or "") + discount_note
        
        await self.session.commit()
        await self.session.refresh(line)
        
        # Recalculate transaction totals
        await self._recalculate_transaction_totals(UUID(line.transaction_id))
        
        return TransactionLineResponse.model_validate(line)
    
    async def process_line_return(self, line_id: UUID, return_data: ReturnProcessing) -> TransactionLineResponse:
        """Process return for transaction line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        # Process return
        line.process_return(
            return_quantity=return_data.return_quantity,
            return_date=return_data.return_date,
            return_reason=return_data.return_reason
        )
        
        # Add return notes
        if return_data.notes:
            return_note = f"\n[RETURN NOTES] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {return_data.notes}"
            line.notes = (line.notes or "") + return_note
        
        await self.session.commit()
        await self.session.refresh(line)
        
        return TransactionLineResponse.model_validate(line)
    
    async def update_rental_period(self, line_id: UUID, period_update: RentalPeriodUpdate) -> TransactionLineResponse:
        """Update rental period for transaction line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")
        
        # Update rental period
        line.update_rental_period(period_update.new_end_date)
        
        # Add update notes
        if period_update.reason or period_update.notes:
            update_note = f"\n[RENTAL PERIOD UPDATE] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: "
            if period_update.reason:
                update_note += f"Reason: {period_update.reason}. "
            if period_update.notes:
                update_note += f"Notes: {period_update.notes}"
            line.notes = (line.notes or "") + update_note
        
        await self.session.commit()
        await self.session.refresh(line)
        
        return TransactionLineResponse.model_validate(line)
    
    # Reporting operations
    async def get_transaction_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> TransactionSummary:
        """Get transaction summary."""
        summary_data = await self.transaction_repository.get_transaction_summary(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        return TransactionSummary(
            total_transactions=summary_data['total_transactions'],
            total_amount=summary_data['total_amount'],
            total_paid=summary_data['total_paid'],
            total_outstanding=summary_data['total_outstanding'],
            transactions_by_status=summary_data['transactions_by_status'],
            transactions_by_type=summary_data['transactions_by_type'],
            transactions_by_payment_status=summary_data['transactions_by_payment_status']
        )
    
    async def get_transaction_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> TransactionReport:
        """Get transaction report."""
        transactions = await self.transaction_repository.get_all(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        summary = await self.get_transaction_summary(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        return TransactionReport(
            transactions=[TransactionHeaderListResponse.model_validate(t) for t in transactions],
            summary=summary,
            date_range={
                'from': date_from or date.min,
                'to': date_to or date.today()
            }
        )
    
    async def get_overdue_transactions(self, as_of_date: date = None) -> List[TransactionHeaderListResponse]:
        """Get overdue transactions."""
        transactions = await self.transaction_repository.get_overdue_transactions(as_of_date)
        return [TransactionHeaderListResponse.model_validate(t) for t in transactions]
    
    async def get_outstanding_transactions(self) -> List[TransactionHeaderListResponse]:
        """Get transactions with outstanding balance."""
        transactions = await self.transaction_repository.get_outstanding_transactions()
        return [TransactionHeaderListResponse.model_validate(t) for t in transactions]
    
    async def get_rental_transactions_due_for_return(self, as_of_date: date = None) -> List[TransactionHeaderListResponse]:
        """Get rental transactions due for return."""
        transactions = await self.transaction_repository.get_rental_transactions_due_for_return(as_of_date)
        return [TransactionHeaderListResponse.model_validate(t) for t in transactions]
    
    # Helper methods
    async def _recalculate_transaction_totals(self, transaction_id: UUID):
        """Recalculate transaction totals."""
        transaction = await self.transaction_repository.get_with_lines(transaction_id)
        if transaction:
            transaction.calculate_totals()
            await self.session.commit()
    
    async def _validate_transaction_modification(self, transaction: TransactionHeader):
        """Validate if transaction can be modified."""
        if transaction.status in [TransactionStatus.COMPLETED.value, TransactionStatus.CANCELLED.value, TransactionStatus.REFUNDED.value]:
            raise ValidationError("Cannot modify completed, cancelled, or refunded transactions")
    
    async def _validate_customer_can_transact(self, customer_id: UUID):
        """Validate if customer can transact."""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {customer_id} not found")
        
        if not customer.can_transact():
            raise ValidationError("Customer cannot transact due to blacklist status")
    
    async def _validate_item_availability(self, item_id: UUID, inventory_unit_id: Optional[UUID] = None):
        """Validate item availability."""
        item = await self.item_repository.get_by_id(item_id)
        if not item:
            raise NotFoundError(f"Item with ID {item_id} not found")
        
        if not item.is_active():
            raise ValidationError("Item is not active")
        
        if inventory_unit_id:
            inventory_unit = await self.inventory_unit_repository.get_by_id(inventory_unit_id)
            if not inventory_unit:
                raise NotFoundError(f"Inventory unit with ID {inventory_unit_id} not found")
            
            if not inventory_unit.is_available():
                raise ValidationError("Inventory unit is not available")