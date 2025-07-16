from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.transactions.models import (
    TransactionHeader,
    TransactionLine,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    PaymentStatus,
    RentalPeriodUnit,
    LineItemType,
)
from app.modules.transactions.repository import (
    TransactionHeaderRepository,
    TransactionLineRepository,
)
from app.modules.transactions.schemas import (
    TransactionHeaderCreate,
    TransactionHeaderUpdate,
    TransactionHeaderResponse,
    TransactionHeaderListResponse,
    TransactionHeaderWithLinesListResponse,
    TransactionWithLinesResponse,
    TransactionLineCreate,
    TransactionLineUpdate,
    TransactionLineResponse,
    TransactionLineListResponse,
    PaymentCreate,
    RefundCreate,
    StatusUpdate,
    DiscountApplication,
    ReturnProcessing,
    RentalPeriodUpdate,
    RentalReturn,
    TransactionSummary,
    TransactionReport,
    TransactionSearch,
    PurchaseResponse,
    PurchaseItemCreate,
    NewPurchaseRequest,
    NewPurchaseResponse,
    RentalItemCreate,
    NewRentalRequest,
    NewRentalResponse,
    SaleItemCreate,
    NewSaleRequest,
    NewSaleResponse,
)
from app.modules.customers.repository import CustomerRepository
from app.modules.inventory.repository import ItemRepository, InventoryUnitRepository
from app.modules.inventory.service import InventoryService
from app.modules.inventory.models import StockLevel
from app.core.logger import get_purchase_logger


class TransactionService:
    """Service for transaction processing operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repository = TransactionHeaderRepository(session)
        self.line_repository = TransactionLineRepository(session)
        self.customer_repository = CustomerRepository(session)
        self.item_repository = ItemRepository(session)
        self.inventory_unit_repository = InventoryUnitRepository(session)
        self.inventory_service = InventoryService(session)
        self.logger = get_purchase_logger()

    # Transaction Header operations
    async def create_transaction(
        self, transaction_data: TransactionHeaderCreate
    ) -> TransactionHeaderResponse:
        """Create a new transaction."""
        # Check if transaction number already exists
        existing_transaction = await self.transaction_repository.get_by_number(
            transaction_data.transaction_number
        )
        if existing_transaction:
            raise ConflictError(
                f"Transaction with number '{transaction_data.transaction_number}' already exists"
            )

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

    async def get_transaction_with_lines(
        self, transaction_id: UUID
    ) -> TransactionWithLinesResponse:
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
        active_only: bool = True,
    ) -> List[TransactionHeaderWithLinesListResponse]:
        """Get all transactions with optional filtering and nested line items."""
        transactions = await self.transaction_repository.get_all_with_lines(
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
            active_only=active_only,
        )

        return [
            TransactionHeaderWithLinesListResponse.model_validate(transaction)
            for transaction in transactions
        ]

    async def search_transactions(
        self,
        search_params: TransactionSearch,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[TransactionHeaderListResponse]:
        """Search transactions."""
        transactions = await self.transaction_repository.search(
            search_params=search_params, skip=skip, limit=limit, active_only=active_only
        )

        return [
            TransactionHeaderListResponse.model_validate(transaction)
            for transaction in transactions
        ]

    async def update_transaction(
        self, transaction_id: UUID, transaction_data: TransactionHeaderUpdate
    ) -> TransactionHeaderResponse:
        """Update a transaction."""
        # Check if transaction exists
        existing_transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not existing_transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")

        # Check if transaction can be updated
        if existing_transaction.status in [
            TransactionStatus.COMPLETED.value,
            TransactionStatus.CANCELLED.value,
            TransactionStatus.REFUNDED.value,
        ]:
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
        if existing_transaction.status not in [
            TransactionStatus.DRAFT.value,
            TransactionStatus.PENDING.value,
        ]:
            raise ValidationError("Can only delete draft or pending transactions")

        return await self.transaction_repository.delete(transaction_id)

    async def update_transaction_status(
        self, transaction_id: UUID, status_update: StatusUpdate
    ) -> TransactionHeaderResponse:
        """Update transaction status."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")

        # Validate status transition
        if not transaction.can_transition_to(status_update.status):
            raise ValidationError(
                f"Cannot transition from {transaction.status} to {status_update.status.value}"
            )

        # Update status
        transaction.update_status(status_update.status)

        # Add notes if provided
        if status_update.notes:
            status_note = f"\n[STATUS UPDATE] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {status_update.notes}"
            transaction.notes = (transaction.notes or "") + status_note

        await self.session.commit()
        await self.session.refresh(transaction)

        return TransactionHeaderResponse.model_validate(transaction)

    async def apply_payment(
        self, transaction_id: UUID, payment_data: PaymentCreate
    ) -> TransactionHeaderResponse:
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
            payment_reference=payment_data.payment_reference,
        )

        # Add payment notes
        if payment_data.notes:
            payment_note = f"\n[PAYMENT] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: ${payment_data.amount} via {payment_data.payment_method.value} - {payment_data.notes}"
            transaction.notes = (transaction.notes or "") + payment_note

        await self.session.commit()
        await self.session.refresh(transaction)

        return TransactionHeaderResponse.model_validate(transaction)

    async def process_refund(
        self, transaction_id: UUID, refund_data: RefundCreate
    ) -> TransactionHeaderResponse:
        """Process refund for transaction."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")

        # Process refund
        transaction.process_refund(
            refund_amount=refund_data.refund_amount, reason=refund_data.reason
        )

        # Add refund notes
        if refund_data.notes:
            refund_note = f"\n[REFUND NOTES] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {refund_data.notes}"
            transaction.notes = (transaction.notes or "") + refund_note

        await self.session.commit()
        await self.session.refresh(transaction)

        return TransactionHeaderResponse.model_validate(transaction)

    async def cancel_transaction(
        self, transaction_id: UUID, reason: str
    ) -> TransactionHeaderResponse:
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

    async def complete_rental_return(
        self, transaction_id: UUID, return_data: RentalReturn
    ) -> TransactionHeaderResponse:
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
    async def add_transaction_line(
        self, transaction_id: UUID, line_data: TransactionLineCreate
    ) -> TransactionLineResponse:
        """Add line to transaction."""
        # Check if transaction exists
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")

        # Check if transaction can be modified
        if transaction.status in [
            TransactionStatus.COMPLETED.value,
            TransactionStatus.CANCELLED.value,
            TransactionStatus.REFUNDED.value,
        ]:
            raise ValidationError(
                "Cannot add lines to completed, cancelled, or refunded transactions"
            )

        # Verify item exists if provided
        if line_data.item_id:
            item = await self.item_repository.get_by_id(line_data.item_id)
            if not item:
                raise NotFoundError(f"Item with ID {line_data.item_id} not found")

        # Verify inventory unit exists if provided
        if line_data.inventory_unit_id:
            inventory_unit = await self.inventory_unit_repository.get_by_id(
                line_data.inventory_unit_id
            )
            if not inventory_unit:
                raise NotFoundError(
                    f"Inventory unit with ID {line_data.inventory_unit_id} not found"
                )

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

    async def get_transaction_lines(
        self, transaction_id: UUID, active_only: bool = True
    ) -> List[TransactionLineResponse]:
        """Get transaction lines."""
        lines = await self.line_repository.get_by_transaction(transaction_id, active_only)
        return [TransactionLineResponse.model_validate(line) for line in lines]

    async def update_transaction_line(
        self, line_id: UUID, line_data: TransactionLineUpdate
    ) -> TransactionLineResponse:
        """Update transaction line."""
        # Check if line exists
        existing_line = await self.line_repository.get_by_id(line_id)
        if not existing_line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")

        # Check if transaction can be modified
        transaction = await self.transaction_repository.get_by_id(
            UUID(existing_line.transaction_id)
        )
        if transaction.status in [
            TransactionStatus.COMPLETED.value,
            TransactionStatus.CANCELLED.value,
            TransactionStatus.REFUNDED.value,
        ]:
            raise ValidationError(
                "Cannot update lines in completed, cancelled, or refunded transactions"
            )

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
        transaction = await self.transaction_repository.get_by_id(
            UUID(existing_line.transaction_id)
        )
        if transaction.status in [
            TransactionStatus.COMPLETED.value,
            TransactionStatus.CANCELLED.value,
            TransactionStatus.REFUNDED.value,
        ]:
            raise ValidationError(
                "Cannot delete lines from completed, cancelled, or refunded transactions"
            )

        # Delete line
        success = await self.line_repository.delete(line_id)

        if success:
            # Recalculate transaction totals
            await self._recalculate_transaction_totals(UUID(existing_line.transaction_id))

        return success

    async def apply_line_discount(
        self, line_id: UUID, discount_data: DiscountApplication
    ) -> TransactionLineResponse:
        """Apply discount to transaction line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")

        # Apply discount
        line.apply_discount(
            discount_percentage=discount_data.discount_percentage,
            discount_amount=discount_data.discount_amount,
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

    async def process_line_return(
        self, line_id: UUID, return_data: ReturnProcessing
    ) -> TransactionLineResponse:
        """Process return for transaction line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")

        # Process return
        line.process_return(
            return_quantity=return_data.return_quantity,
            return_date=return_data.return_date,
            return_reason=return_data.return_reason,
        )

        # Add return notes
        if return_data.notes:
            return_note = f"\n[RETURN NOTES] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {return_data.notes}"
            line.notes = (line.notes or "") + return_note

        await self.session.commit()
        await self.session.refresh(line)

        return TransactionLineResponse.model_validate(line)

    async def update_rental_period(
        self, line_id: UUID, period_update: RentalPeriodUpdate
    ) -> TransactionLineResponse:
        """Update rental period for transaction line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Transaction line with ID {line_id} not found")

        # Update rental period
        line.update_rental_period(period_update.new_end_date)

        # Add update notes
        if period_update.reason or period_update.notes:
            update_note = (
                f"\n[RENTAL PERIOD UPDATE] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: "
            )
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
        active_only: bool = True,
    ) -> TransactionSummary:
        """Get transaction summary."""
        summary_data = await self.transaction_repository.get_transaction_summary(
            date_from=date_from, date_to=date_to, active_only=active_only
        )

        return TransactionSummary(
            total_transactions=summary_data["total_transactions"],
            total_amount=summary_data["total_amount"],
            total_paid=summary_data["total_paid"],
            total_outstanding=summary_data["total_outstanding"],
            transactions_by_status=summary_data["transactions_by_status"],
            transactions_by_type=summary_data["transactions_by_type"],
            transactions_by_payment_status=summary_data["transactions_by_payment_status"],
        )

    async def get_transaction_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True,
    ) -> TransactionReport:
        """Get transaction report."""
        transactions = await self.transaction_repository.get_all(
            date_from=date_from, date_to=date_to, active_only=active_only
        )

        summary = await self.get_transaction_summary(
            date_from=date_from, date_to=date_to, active_only=active_only
        )

        return TransactionReport(
            transactions=[TransactionHeaderListResponse.model_validate(t) for t in transactions],
            summary=summary,
            date_range={"from": date_from or date.min, "to": date_to or date.today()},
        )

    async def get_overdue_transactions(
        self, as_of_date: date = None
    ) -> List[TransactionHeaderListResponse]:
        """Get overdue transactions."""
        transactions = await self.transaction_repository.get_overdue_transactions(as_of_date)
        return [TransactionHeaderListResponse.model_validate(t) for t in transactions]

    async def get_outstanding_transactions(self) -> List[TransactionHeaderListResponse]:
        """Get transactions with outstanding balance."""
        transactions = await self.transaction_repository.get_outstanding_transactions()
        return [TransactionHeaderListResponse.model_validate(t) for t in transactions]

    async def get_rental_transactions_due_for_return(
        self, as_of_date: date = None
    ) -> List[TransactionHeaderListResponse]:
        """Get rental transactions due for return."""
        transactions = await self.transaction_repository.get_rental_transactions_due_for_return(
            as_of_date
        )
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
        if transaction.status in [
            TransactionStatus.COMPLETED.value,
            TransactionStatus.CANCELLED.value,
            TransactionStatus.REFUNDED.value,
        ]:
            raise ValidationError("Cannot modify completed, cancelled, or refunded transactions")

    async def _validate_customer_can_transact(self, customer_id: UUID):
        """Validate if customer can transact."""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {customer_id} not found")

        if not customer.can_transact():
            raise ValidationError("Customer cannot transact due to blacklist status")

    async def _validate_item_availability(
        self, item_id: UUID, inventory_unit_id: Optional[UUID] = None
    ):
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

    async def get_purchase_transactions(
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
    ) -> List[PurchaseResponse]:
        """Get purchase transactions with filtering options."""
        # Use existing method but filter for purchase type
        transactions = await self.transaction_repository.get_all_with_lines(
            skip=skip,
            limit=limit,
            transaction_type=TransactionType.PURCHASE,
            customer_id=supplier_id,  # In purchases, supplier_id is stored in customer_id
            date_from=date_from,
            date_to=date_to,
            status=status,
            payment_status=payment_status,
            active_only=True,
        )

        # Apply amount filtering if specified
        filtered_transactions = []
        for transaction in transactions:
            if amount_from and transaction.total_amount < amount_from:
                continue
            if amount_to and transaction.total_amount > amount_to:
                continue
            filtered_transactions.append(transaction)

        # Collect unique supplier, location, and item IDs to fetch details
        supplier_ids = set()
        location_ids = set()
        item_ids = set()
        
        for transaction in filtered_transactions:
            supplier_ids.add(transaction.customer_id)  # supplier_id stored in customer_id
            location_ids.add(transaction.location_id)
            for line in transaction.transaction_lines:
                if line.item_id:
                    item_ids.add(line.item_id)
        
        # Fetch supplier details
        suppliers_dict = {}
        if supplier_ids:
            from app.modules.suppliers.repository import SupplierRepository
            supplier_repo = SupplierRepository(self.session)
            for supplier_id in supplier_ids:
                supplier = await supplier_repo.get_by_id(supplier_id)
                if supplier:
                    suppliers_dict[str(supplier_id)] = {
                        "id": supplier.id,
                        "name": supplier.company_name
                    }
        
        # Fetch location details
        locations_dict = {}
        if location_ids:
            from app.modules.master_data.locations.repository import LocationRepository
            location_repo = LocationRepository(self.session)
            for location_id in location_ids:
                location = await location_repo.get_by_id(location_id)
                if location:
                    locations_dict[str(location_id)] = {
                        "id": location.id,
                        "name": location.location_name
                    }
        
        # Fetch item details
        items_dict = {}
        if item_ids:
            from app.modules.master_data.item_master.repository import ItemMasterRepository
            item_repo = ItemMasterRepository(self.session)
            for item_id in item_ids:
                item = await item_repo.get_by_id(item_id)
                if item:
                    items_dict[str(item_id)] = {
                        "id": item.id,
                        "name": item.item_name
                    }
        
        # Transform to PurchaseResponse format
        purchase_responses = []
        for transaction in filtered_transactions:
            # Convert SQLAlchemy model to dict
            transaction_lines_dict = []
            for line in transaction.transaction_lines:
                line_dict = {
                    "id": line.id,
                    "item_id": line.item_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "tax_rate": line.tax_rate,
                    "discount_amount": line.discount_amount,
                    "tax_amount": line.tax_amount,
                    "line_total": line.line_total,
                    "notes": line.notes,
                    "created_at": line.created_at,
                    "updated_at": line.updated_at,
                }
                transaction_lines_dict.append(line_dict)
            
            transaction_dict = {
                "id": transaction.id,
                "customer_id": transaction.customer_id,  # This contains supplier_id
                "location_id": transaction.location_id,
                "transaction_number": transaction.transaction_number,
                "transaction_date": transaction.transaction_date,
                "notes": transaction.notes,
                "subtotal": transaction.subtotal,
                "tax_amount": transaction.tax_amount,
                "discount_amount": transaction.discount_amount,
                "total_amount": transaction.total_amount,
                "status": transaction.status,
                "payment_status": transaction.payment_status,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at,
                "transaction_lines": transaction_lines_dict,
            }
            
            # Get related details
            supplier_details = suppliers_dict.get(str(transaction.customer_id))
            location_details = locations_dict.get(str(transaction.location_id))
            
            purchase_responses.append(PurchaseResponse.from_transaction(
                transaction_dict, 
                supplier_details, 
                location_details, 
                items_dict
            ))

        return purchase_responses

    async def get_purchase_by_id(self, purchase_id: UUID) -> PurchaseResponse:
        """Get a single purchase transaction by ID."""
        # Get transaction with lines
        transaction = await self.transaction_repository.get_with_lines(purchase_id)
        if not transaction:
            raise NotFoundError(f"Purchase transaction with ID {purchase_id} not found")
        
        # Verify it's a purchase transaction
        # Handle both enum and string values
        transaction_type_value = transaction.transaction_type
        if hasattr(transaction_type_value, 'value'):
            transaction_type_value = transaction_type_value.value
        
        if transaction_type_value != TransactionType.PURCHASE.value:
            raise ValidationError(f"Transaction {purchase_id} is not a purchase transaction")
        
        # Fetch supplier details
        supplier_details = None
        if transaction.customer_id:
            from app.modules.suppliers.repository import SupplierRepository
            supplier_repo = SupplierRepository(self.session)
            supplier = await supplier_repo.get_by_id(transaction.customer_id)
            if supplier:
                supplier_details = {
                    "id": supplier.id,
                    "name": supplier.company_name
                }
        
        # Fetch location details
        location_details = None
        if transaction.location_id:
            from app.modules.master_data.locations.repository import LocationRepository
            location_repo = LocationRepository(self.session)
            location = await location_repo.get_by_id(transaction.location_id)
            if location:
                location_details = {
                    "id": location.id,
                    "name": location.location_name
                }
        
        # Fetch item details
        items_dict = {}
        item_ids = {line.item_id for line in transaction.transaction_lines if line.item_id}
        if item_ids:
            from app.modules.master_data.item_master.repository import ItemMasterRepository
            item_repo = ItemMasterRepository(self.session)
            for item_id in item_ids:
                item = await item_repo.get_by_id(item_id)
                if item:
                    items_dict[str(item_id)] = {
                        "id": item.id,
                        "name": item.item_name
                    }
        
        # Convert SQLAlchemy model to dict
        transaction_lines_dict = []
        for line in transaction.transaction_lines:
            line_dict = {
                "id": line.id,
                "item_id": line.item_id,
                "description": line.description,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "tax_rate": line.tax_rate,
                "discount_amount": line.discount_amount,
                "tax_amount": line.tax_amount,
                "line_total": line.line_total,
                "notes": line.notes,
                "created_at": line.created_at,
                "updated_at": line.updated_at,
            }
            transaction_lines_dict.append(line_dict)
        
        transaction_dict = {
            "id": transaction.id,
            "customer_id": transaction.customer_id,  # This contains supplier_id
            "location_id": transaction.location_id,
            "transaction_number": transaction.transaction_number,
            "transaction_date": transaction.transaction_date,
            "notes": transaction.notes,
            "subtotal": transaction.subtotal,
            "tax_amount": transaction.tax_amount,
            "discount_amount": transaction.discount_amount,
            "total_amount": transaction.total_amount,
            "status": transaction.status,
            "payment_status": transaction.payment_status,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            "transaction_lines": transaction_lines_dict,
        }
        
        return PurchaseResponse.from_transaction(transaction_dict, supplier_details, location_details, items_dict)

    async def create_new_purchase(self, purchase_data: NewPurchaseRequest) -> NewPurchaseResponse:
        """Create a new purchase transaction using the new-purchase endpoint format."""
        
        # Start comprehensive logging
        self.logger.log_purchase_start(purchase_data.model_dump())
        
        try:
            # Validate supplier exists
            from app.modules.suppliers.repository import SupplierRepository

            supplier_repo = SupplierRepository(self.session)
            supplier = await supplier_repo.get_by_id(purchase_data.supplier_id)
            if not supplier:
                self.logger.log_validation_step("Supplier Validation", False, f"Supplier ID {purchase_data.supplier_id} not found")
                raise NotFoundError(f"Supplier with ID {purchase_data.supplier_id} not found")
            
            self.logger.log_validation_step("Supplier Validation", True, f"Supplier found: {supplier.supplier_name if hasattr(supplier, 'supplier_name') else 'Unknown'}")

            # Validate location exists
            from app.modules.master_data.locations.repository import LocationRepository

            location_repo = LocationRepository(self.session)
            location = await location_repo.get_by_id(purchase_data.location_id)
            if not location:
                self.logger.log_validation_step("Location Validation", False, f"Location ID {purchase_data.location_id} not found")
                raise NotFoundError(f"Location with ID {purchase_data.location_id} not found")
            
            self.logger.log_validation_step("Location Validation", True, f"Location found: {location.location_name if hasattr(location, 'location_name') else 'Unknown'}")

            # Validate all items exist
            from app.modules.master_data.item_master.repository import ItemMasterRepository

            item_repo = ItemMasterRepository(self.session)
            validated_items = []
            for item in purchase_data.items:
                item_exists = await item_repo.get_by_id(item.item_id)
                if not item_exists:
                    self.logger.log_validation_step("Item Validation", False, f"Item ID {item.item_id} not found")
                    raise NotFoundError(f"Item with ID {item.item_id} not found")
                validated_items.append(item_exists)
            
            self.logger.log_validation_step("Items Validation", True, f"All {len(purchase_data.items)} items validated successfully")

            # Generate unique transaction number
            import random

            transaction_number = (
                f"PUR-{purchase_data.purchase_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            )

            # Ensure uniqueness
            while await self.transaction_repository.get_by_number(transaction_number):
                transaction_number = f"PUR-{purchase_data.purchase_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            self.logger.log_debug_info("Generated Transaction Number", transaction_number)

            # Create transaction header
            transaction = TransactionHeader(
                transaction_number=transaction_number,
                transaction_type=TransactionType.PURCHASE,
                transaction_date=datetime.combine(purchase_data.purchase_date, datetime.min.time()),
                customer_id=str(
                    purchase_data.supplier_id
                ),  # Store supplier_id in customer_id field
                location_id=str(purchase_data.location_id),
                status=TransactionStatus.COMPLETED,
                notes=purchase_data.notes or "",
                subtotal=Decimal("0"),
                discount_amount=Decimal("0"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("0"),
                paid_amount=Decimal("0"),
                deposit_amount=Decimal("0"),
            )

            # Add transaction to session
            self.session.add(transaction)
            await self.session.flush()  # Get the ID without committing
            
            # Log transaction creation
            self.logger.log_transaction_creation({
                "id": str(transaction.id),
                "transaction_number": transaction.transaction_number,
                "transaction_type": transaction.transaction_type.value,
                "status": transaction.status.value,
                "total_amount": str(transaction.total_amount)
            })
            self.logger.log_session_operation("Transaction added to session and flushed")

            # Create transaction lines
            total_amount = Decimal("0")
            tax_total = Decimal("0")
            discount_total = Decimal("0")

            for idx, item in enumerate(purchase_data.items):
                # Calculate line values
                line_subtotal = item.unit_cost * Decimal(str(item.quantity))
                tax_amount = (line_subtotal * (item.tax_rate or Decimal("0"))) / 100
                discount_amount = item.discount_amount or Decimal("0")
                line_total = line_subtotal + tax_amount - discount_amount

                # Create transaction line
                line = TransactionLine(
                    transaction_id=str(transaction.id),
                    line_number=idx + 1,
                    line_type=LineItemType.PRODUCT,
                    item_id=item.item_id,
                    description=f"Purchase: {item.item_id} (Condition: {item.condition})",
                    quantity=Decimal(str(item.quantity)),
                    unit_price=item.unit_cost,
                    tax_rate=item.tax_rate or Decimal("0"),
                    tax_amount=tax_amount,
                    discount_amount=discount_amount,
                    line_total=line_total,
                    notes=item.notes or "",
                )

                self.session.add(line)
                total_amount += line_total
                tax_total += tax_amount
                discount_total += discount_amount

            # Update transaction totals
            transaction.subtotal = total_amount - tax_total + discount_total
            transaction.tax_amount = tax_total
            transaction.discount_amount = discount_total
            transaction.total_amount = total_amount

            # Update stock levels for purchased items before committing
            self.logger.log_stock_level_processing_start(len(purchase_data.items))
            await self._update_stock_levels_for_purchase(purchase_data, transaction)
            self.logger.log_session_operation("Stock level processing completed")

            # Commit transaction (includes both transaction and stock level updates)
            self.logger.log_session_operation("Starting transaction commit")
            await self.session.commit()
            await self.session.refresh(transaction)
            self.logger.log_transaction_commit(True)

            # Get the complete transaction with lines for response
            result = await self.get_transaction_with_lines(transaction.id)

            response = NewPurchaseResponse(
                success=True,
                message="Purchase transaction created successfully",
                data=result.model_dump(),
                transaction_id=transaction.id,
                transaction_number=transaction.transaction_number,
            )
            
            self.logger.log_purchase_completion(True, str(transaction.id), response.model_dump())
            return response

        except Exception as e:
            self.logger.log_error(e, "Purchase Transaction Creation")
            self.logger.log_transaction_commit(False, str(e))
            await self.session.rollback()
            self.logger.log_session_operation("Transaction rolled back due to error")
            raise e

    async def create_new_sale(self, sale_data: NewSaleRequest) -> NewSaleResponse:
        """Create a new sale transaction using the new-sale endpoint format."""
        try:
            # Validate customer exists
            customer = await self.customer_repository.get_by_id(sale_data.customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {sale_data.customer_id} not found")

            # Verify customer can transact
            if not customer.can_transact():
                raise ValidationError("Customer cannot transact due to blacklist status")

            # Validate location exists (use first available location if not specified)
            from app.modules.master_data.locations.repository import LocationRepository
            location_repo = LocationRepository(self.session)
            
            # Get the first available location as a default
            locations = await location_repo.get_all(active_only=True)
            if not locations:
                raise NotFoundError("No active locations found")
            
            location = locations[0]  # Use first location as default

            # Validate all items exist and are available for sale
            from app.modules.master_data.item_master.repository import ItemMasterRepository
            item_repo = ItemMasterRepository(self.session)
            validated_items = []
            
            for item in sale_data.items:
                item_exists = await item_repo.get_by_id(item.item_id)
                if not item_exists:
                    raise NotFoundError(f"Item with ID {item.item_id} not found")
                if not item_exists.is_saleable:
                    raise ValidationError(f"Item {item.item_id} is not available for sale")
                validated_items.append(item_exists)

            # Check inventory availability
            for item in sale_data.items:
                existing_stock = await self.inventory_service.stock_level_repository.get_by_item_location(
                    item.item_id, location.id
                )
                if not existing_stock:
                    raise ValidationError(f"No stock found for item {item.item_id}")
                
                if existing_stock.quantity_available < Decimal(str(item.quantity)):
                    raise ValidationError(f"Insufficient stock for item {item.item_id}. Available: {existing_stock.quantity_available}, Requested: {item.quantity}")

            # Generate unique transaction number
            import random
            transaction_number = (
                f"SAL-{sale_data.transaction_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            )

            # Ensure uniqueness
            while await self.transaction_repository.get_by_number(transaction_number):
                transaction_number = f"SAL-{sale_data.transaction_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

            # Create transaction header
            transaction = TransactionHeader(
                transaction_number=transaction_number,
                transaction_type=TransactionType.SALE,
                transaction_date=datetime.combine(sale_data.transaction_date, datetime.min.time()),
                customer_id=str(sale_data.customer_id),
                location_id=str(location.id),
                status=TransactionStatus.COMPLETED,
                notes=sale_data.notes or "",
                subtotal=Decimal("0"),
                discount_amount=Decimal("0"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("0"),
                paid_amount=Decimal("0"),
                deposit_amount=Decimal("0"),
                payment_status=PaymentStatus.PAID,
            )

            # Add transaction to session
            self.session.add(transaction)
            await self.session.flush()  # Get the ID without committing

            # Create transaction lines
            total_amount = Decimal("0")
            tax_total = Decimal("0")
            discount_total = Decimal("0")

            for idx, item in enumerate(sale_data.items):
                # Calculate line values
                line_subtotal = item.unit_cost * Decimal(str(item.quantity))
                tax_amount = (line_subtotal * (item.tax_rate or Decimal("0"))) / 100
                discount_amount = item.discount_amount or Decimal("0")
                line_total = line_subtotal + tax_amount - discount_amount

                # Create transaction line
                line = TransactionLine(
                    transaction_id=str(transaction.id),
                    line_number=idx + 1,
                    line_type=LineItemType.PRODUCT,
                    item_id=str(item.item_id),
                    description=f"Sale: {validated_items[idx].item_name if idx < len(validated_items) else 'Unknown Item'}",
                    quantity=Decimal(str(item.quantity)),
                    unit_price=item.unit_cost,
                    tax_rate=item.tax_rate or Decimal("0"),
                    tax_amount=tax_amount,
                    discount_amount=discount_amount,
                    line_total=line_total,
                    notes=item.notes or "",
                )

                self.session.add(line)
                total_amount += line_total
                tax_total += tax_amount
                discount_total += discount_amount

            # Update transaction totals
            transaction.subtotal = total_amount - tax_total + discount_total
            transaction.tax_amount = tax_total
            transaction.discount_amount = discount_total
            transaction.total_amount = total_amount
            transaction.paid_amount = total_amount  # Sale is paid in full

            # Update inventory for sold items
            await self._update_inventory_for_sale(sale_data, transaction, location)

            # Commit transaction
            await self.session.commit()
            await self.session.refresh(transaction)

            # Get the complete transaction with lines for response
            result = await self.get_transaction_with_lines(transaction.id)

            response = NewSaleResponse(
                success=True,
                message="Sale transaction created successfully",
                data=result.model_dump(),
                transaction_id=transaction.id,
                transaction_number=transaction.transaction_number,
            )
            
            return response

        except Exception as e:
            await self.session.rollback()
            raise e

    async def create_new_rental(self, rental_data: NewRentalRequest) -> NewRentalResponse:
        """Create a new rental transaction using the new-rental endpoint format."""
        try:
            # Validate customer exists
            customer = await self.customer_repository.get_by_id(rental_data.customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {rental_data.customer_id} not found")

            # Verify customer can transact
            if not customer.can_transact():
                raise ValidationError("Customer cannot transact due to blacklist status")

            # Validate location exists
            from app.modules.master_data.locations.repository import LocationRepository
            location_repo = LocationRepository(self.session)
            location = await location_repo.get_by_id(rental_data.location_id)
            if not location:
                raise NotFoundError(f"Location with ID {rental_data.location_id} not found")

            # Validate all items exist and are rentable
            from app.modules.master_data.item_master.repository import ItemMasterRepository
            item_repo = ItemMasterRepository(self.session)
            for item in rental_data.items:
                item_exists = await item_repo.get_by_id(item.item_id)
                if not item_exists:
                    raise NotFoundError(f"Item with ID {item.item_id} not found")
                if not item_exists.is_rentable:
                    raise ValidationError(f"Item {item.item_id} is not available for rental")

            # Generate unique transaction number
            import random
            transaction_number = (
                f"REN-{rental_data.transaction_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            )

            # Ensure uniqueness
            while await self.transaction_repository.get_by_number(transaction_number):
                transaction_number = f"REN-{rental_data.transaction_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

            # Create transaction header (no rental dates at header level in new structure)
            transaction = TransactionHeader(
                transaction_number=transaction_number,
                transaction_type=TransactionType.RENTAL,
                transaction_date=datetime.combine(rental_data.transaction_date, datetime.min.time()),
                customer_id=str(rental_data.customer_id),
                location_id=str(rental_data.location_id),
                status=TransactionStatus.CONFIRMED,
                payment_method=PaymentMethod(rental_data.payment_method),
                payment_reference=rental_data.payment_reference or "",
                notes=rental_data.notes or "",
                subtotal=Decimal("0"),
                discount_amount=Decimal("0"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("0"),
                paid_amount=Decimal("0"),
                deposit_amount=Decimal("0"),
            )

            # Add transaction to session
            self.session.add(transaction)
            await self.session.flush()  # Get the ID without committing

            # Create transaction lines
            total_amount = Decimal("0")
            tax_total = Decimal("0")
            discount_total = Decimal("0")

            for idx, item in enumerate(rental_data.items):
                # Get item details to fetch rental rate
                item_details = await item_repo.get_by_id(item.item_id)
                if not item_details:
                    raise NotFoundError(f"Item with ID {item.item_id} not found")
                
                # Use item's rental rate as unit price (assuming daily rate)
                unit_price = item_details.rental_rate_per_period or Decimal("0")
                
                # Calculate line values based on quantity and rental period
                line_subtotal = unit_price * Decimal(str(item.quantity)) * Decimal(str(item.rental_period_value))
                tax_amount = (line_subtotal * (item.tax_rate or Decimal("0"))) / 100
                discount_amount = item.discount_amount or Decimal("0")
                line_total = line_subtotal + tax_amount - discount_amount

                # Default to DAYS for rental period unit since it's not provided in new structure
                rental_period_unit = RentalPeriodUnit.DAYS

                # Create transaction line
                line = TransactionLine(
                    transaction_id=str(transaction.id),
                    line_number=idx + 1,
                    line_type=LineItemType.PRODUCT,
                    item_id=item.item_id,
                    description=f"Rental: {item.item_id} ({item.rental_period_value} days)",
                    quantity=Decimal(str(item.quantity)),
                    unit_price=unit_price,
                    tax_rate=item.tax_rate or Decimal("0"),
                    tax_amount=tax_amount,
                    discount_amount=discount_amount,
                    line_total=line_total,
                    rental_period_value=item.rental_period_value,
                    rental_period_unit=rental_period_unit,
                    rental_start_date=item.rental_start_date,
                    rental_end_date=item.rental_end_date,
                    notes=item.notes or "",
                )

                self.session.add(line)
                total_amount += line_total
                tax_total += tax_amount
                discount_total += discount_amount

            # Update transaction totals
            transaction.subtotal = total_amount - tax_total + discount_total
            transaction.tax_amount = tax_total
            transaction.discount_amount = discount_total
            transaction.total_amount = total_amount

            # Commit transaction first
            await self.session.commit()
            await self.session.refresh(transaction)
            
            # Update stock levels for rented items (move from available to on rent)
            for item in rental_data.items:
                try:
                    # Get stock level for this item/location
                    stock_level = await self.inventory_service.stock_level_repository.get_by_item_location(
                        item.item_id, rental_data.location_id
                    )
                    
                    if stock_level:
                        # Move quantity from available to on rent
                        await self.inventory_service.rent_out_stock(
                            stock_level_id=stock_level.id,
                            quantity=Decimal(str(item.quantity)),
                            transaction_id=str(transaction.id)
                        )
                        
                        self.logger.log_debug_info("Stock moved to rent", {
                            "item_id": str(item.item_id),
                            "quantity": item.quantity,
                            "transaction_id": str(transaction.id),
                            "stock_level_id": str(stock_level.id)
                        })
                    else:
                        # Log warning if no stock level found
                        self.logger.log_debug_info("No stock level found for rental", {
                            "item_id": str(item.item_id),
                            "location_id": str(rental_data.location_id),
                            "quantity": item.quantity
                        })
                        
                except Exception as stock_error:
                    # Log the error but don't fail the transaction
                    self.logger.log_debug_info("Error updating stock for rental", {
                        "item_id": str(item.item_id),
                        "error": str(stock_error),
                        "transaction_id": str(transaction.id)
                    })

            # Get the complete transaction with lines for response
            result = await self.get_transaction_with_lines(transaction.id)

            return NewRentalResponse(
                success=True,
                message="Rental transaction created successfully",
                data=result.model_dump(),
                transaction_id=transaction.id,
                transaction_number=transaction.transaction_number,
            )

        except Exception as e:
            await self.session.rollback()
            raise e

    async def _update_stock_levels_for_purchase(self, purchase_data: NewPurchaseRequest, transaction: TransactionHeader):
        """Update stock levels for purchased items within the same database transaction."""
        from app.modules.inventory.schemas import StockLevelCreate
        
        for item in purchase_data.items:
            self.logger.log_debug_info(f"Processing Item {item.item_id}", {
                "item_id": str(item.item_id),
                "quantity": item.quantity,
                "location_id": str(purchase_data.location_id)
            })
            
            # Check if stock level already exists for this item/location
            existing_stock = await self.inventory_service.stock_level_repository.get_by_item_location(
                item.item_id, purchase_data.location_id
            )
            
            if existing_stock:
                # Log existing stock found
                existing_stock_data = {
                    "id": str(existing_stock.id),
                    "quantity_on_hand": existing_stock.quantity_on_hand,
                    "quantity_available": existing_stock.quantity_available,
                    "quantity_on_rent": existing_stock.quantity_on_rent
                }
                self.logger.log_item_stock_processing(str(item.item_id), item.quantity, existing_stock_data)
                
                # Update stock level using inventory service with stock movement tracking
                await self.inventory_service.adjust_stock_level(
                    item_id=item.item_id,
                    location_id=purchase_data.location_id,
                    quantity_change=item.quantity,
                    transaction_type="PURCHASE",
                    reference_id=str(transaction.id),
                    notes=f"Purchase transaction - Condition: {item.condition}"
                )
                
                self.logger.log_debug_info("Stock Quantity Adjusted with Movement Tracking", {
                    "item_id": str(item.item_id),
                    "added_quantity": item.quantity,
                    "transaction_id": str(transaction.id)
                })
            else:
                # Log new stock creation
                self.logger.log_item_stock_processing(str(item.item_id), item.quantity, None)
                
                # Create new stock level with purchased quantity using inventory service
                from decimal import Decimal
                stock_data = StockLevelCreate(
                    item_id=item.item_id,
                    location_id=purchase_data.location_id,
                    quantity_on_hand=Decimal(str(item.quantity)),
                    quantity_available=Decimal(str(item.quantity)),
                    quantity_on_rent=Decimal("0")
                )
                
                self.logger.log_stock_level_creation(stock_data.model_dump())
                
                # Create the stock level using inventory service to ensure proper tracking
                created_stock = await self.inventory_service.stock_level_repository.create(stock_data)
                
                # Now create the initial stock movement record for the purchase
                from app.modules.inventory.models import ReferenceType
                await self.inventory_service._create_stock_movement_record(
                    stock_level_id=created_stock.id,
                    movement_type="PURCHASE",
                    quantity_change=Decimal(str(item.quantity)),
                    quantity_before=Decimal("0"),
                    quantity_after=Decimal(str(item.quantity)),
                    reference_type=ReferenceType.TRANSACTION,
                    reference_id=str(transaction.id),
                    reason=f"Initial purchase - Condition: {item.condition}",
                    notes=f"Purchase transaction - Condition: {item.condition}"
                )
                
                self.logger.log_session_operation(f"Stock level created with movement tracking for item {item.item_id}")

    async def _update_inventory_for_sale(self, sale_data: NewSaleRequest, transaction: TransactionHeader, location):
        """Update inventory for sold items within the same database transaction."""
        from app.modules.inventory.models import MovementType, ReferenceType
        from decimal import Decimal
        
        for item in sale_data.items:
            # Check if stock level exists for this item/location
            existing_stock = await self.inventory_service.stock_level_repository.get_by_item_location(
                item.item_id, location.id
            )
            
            if not existing_stock:
                raise ValidationError(f"No stock found for item {item.item_id} at location {location.id}")
            
            # Validate sufficient stock
            if existing_stock.quantity_available < Decimal(str(item.quantity)):
                raise ValidationError(f"Insufficient stock for item {item.item_id}. Available: {existing_stock.quantity_available}, Requested: {item.quantity}")
            
            # Reduce stock levels
            quantity_change = -Decimal(str(item.quantity))
            await self.inventory_service.adjust_stock_level(
                item_id=item.item_id,
                location_id=location.id,
                quantity_change=quantity_change,
                transaction_type="SALE",
                reference_id=str(transaction.id),
                notes=f"Sale transaction - Item sold"
            )
            
            # Mark inventory units as sold (for tracked items)
            await self._mark_inventory_units_as_sold(item.item_id, location.id, item.quantity, transaction.id)

    async def _mark_inventory_units_as_sold(self, item_id: UUID, location_id: UUID, quantity: int, transaction_id: UUID):
        """Mark specific inventory units as sold."""
        from app.modules.inventory.models import InventoryUnitStatus
        
        # Get available inventory units for this item at this location
        available_units = await self.inventory_unit_repository.get_available_units(
            item_id=item_id,
            location_id=location_id,
            limit=quantity
        )
        
        if len(available_units) < quantity:
            # If we don't have enough individual units, just log this
            # This might happen for bulk items where we track stock levels but not individual units
            return
        
        # Mark the required number of units as sold
        for i in range(min(quantity, len(available_units))):
            unit = available_units[i]
            unit.mark_as_sold(updated_by=f"Transaction {transaction_id}")
            await self.session.flush()  # Flush to ensure changes are applied
