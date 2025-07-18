from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

# Import caching utilities
from app.core.cache import cached, RentalCache, cache

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
    RentalStatus,
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
    RentableItemResponse,
    LocationAvailability,
)
from app.modules.customers.repository import CustomerRepository
from app.modules.inventory.repository import ItemRepository, InventoryUnitRepository
from app.modules.inventory.service import InventoryService
from app.modules.inventory.models import StockLevel, StockMovement
from app.modules.inventory.models import MovementType, ReferenceType
from app.core.logger import get_purchase_logger
from app.modules.system.services.audit_service import AuditService


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
        self.audit_service = AuditService(session)

    # ... [keeping existing methods for brevity] ...

    async def create_new_rental_optimized(self, rental_data: NewRentalRequest) -> NewRentalResponse:
        """
        Create a new rental transaction with optimized performance.
        
        This method addresses the 30+ second timeout issues by:
        1. Batch validation of all items in a single query
        2. Bulk stock level lookups instead of individual queries
        3. Single database transaction for all operations
        4. Reduced database commits from N+1 to 1
        
        Expected performance improvement: 30+ seconds to <2 seconds (93% faster)
        """
        try:
            self.logger.log_debug_info("Starting optimized rental creation", {
                "customer_id": str(rental_data.customer_id),
                "location_id": str(rental_data.location_id),
                "item_count": len(rental_data.items)
            })

            # Step 1: Batch validation - single query for all items
            item_ids = [item.item_id for item in rental_data.items]
            validated_items = await self._batch_validate_rental_items(item_ids)
            
            # Step 2: Batch stock level lookup - single query for all items
            stock_levels = await self._batch_get_stock_levels_for_rental(
                item_ids, rental_data.location_id
            )
            
            # Step 3: Validate stock availability for all items
            self._validate_stock_availability_for_rental(
                rental_data.items, stock_levels
            )

            # Step 4: Generate transaction number efficiently
            transaction_number = await self._generate_rental_transaction_number(rental_data)

            # Step 5: Create transaction and lines in single transaction
            async with self.session.begin():
                # Create transaction header
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
                    deposit_amount=rental_data.deposit_amount or Decimal("0"),
                    delivery_required=rental_data.delivery_required,
                    delivery_address=rental_data.delivery_address,
                    delivery_date=rental_data.delivery_date,
                    delivery_time=rental_data.delivery_time,
                    pickup_required=rental_data.pickup_required,
                    pickup_date=rental_data.pickup_date,
                    pickup_time=rental_data.pickup_time,
                    is_active=True,
                )
                self.session.add(transaction)
                await self.session.flush()  # Get ID for foreign key references

                # Create transaction lines and calculate totals
                total_amount = Decimal("0")
                tax_total = Decimal("0")
                discount_total = Decimal("0")
                transaction_lines = []
                stock_movements = []

                for idx, item in enumerate(rental_data.items):
                    item_details = validated_items[item.item_id]
                    unit_price = item_details.rental_rate_per_period or Decimal("0")
                    
                    # Calculate line values
                    line_subtotal = unit_price * Decimal(str(item.quantity)) * Decimal(str(item.rental_period_value))
                    tax_amount = (line_subtotal * (item.tax_rate or Decimal("0"))) / 100
                    discount_amount = item.discount_amount or Decimal("0")
                    line_total = line_subtotal + tax_amount - discount_amount

                    # Create transaction line
                    line = TransactionLine(
                        transaction_id=str(transaction.id),
                        line_number=idx + 1,
                        line_type=LineItemType.PRODUCT,
                        item_id=str(item.item_id),
                        description=f"Rental: {item_details.item_name} ({item.rental_period_value} days)",
                        quantity=Decimal(str(item.quantity)),
                        unit_price=unit_price,
                        tax_rate=item.tax_rate or Decimal("0"),
                        tax_amount=tax_amount,
                        discount_amount=discount_amount,
                        line_total=line_total,
                        rental_period_value=item.rental_period_value,
                        rental_period_unit=RentalPeriodUnit.DAYS,
                        rental_start_date=item.rental_start_date,
                        rental_end_date=item.rental_end_date,
                        notes=item.notes or "",
                        is_active=True,
                    )
                    transaction_lines.append(line)
                    
                    total_amount += line_total
                    tax_total += tax_amount
                    discount_total += discount_amount

                # Bulk add transaction lines
                self.session.add_all(transaction_lines)

                # Update transaction totals
                transaction.subtotal = total_amount - tax_total + discount_total
                transaction.tax_amount = tax_total
                transaction.discount_amount = discount_total
                transaction.total_amount = total_amount

                # Step 6: Batch process stock operations
                await self._batch_process_rental_stock_operations(
                    rental_data.items, stock_levels, transaction.id
                )

            # Transaction committed automatically by async with
            
            # Invalidate stock cache after updates
            await RentalCache.invalidate_stock_cache(
                [item.item_id for item in rental_data.items], 
                str(rental_data.location_id)
            )

            self.logger.log_debug_info("Optimized rental creation completed", {
                "transaction_id": str(transaction.id),
                "transaction_number": transaction_number,
                "total_amount": str(total_amount)
            })

            # Get complete transaction for response
            result = await self.get_transaction_with_lines(transaction.id)

            return NewRentalResponse(
                success=True,
                message="Rental transaction created successfully (optimized)",
                data=result.model_dump(),
                transaction_id=transaction.id,
                transaction_number=transaction.transaction_number,
            )

        except Exception as e:
            self.logger.log_debug_info("Error in optimized rental creation", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            await self.session.rollback()
            raise e

    async def _batch_validate_rental_items(self, item_ids: List[UUID]) -> Dict[UUID, Any]:
        """Batch validate all rental items with caching."""
        # Use cached lookup for rentable items
        items = await RentalCache.get_rentable_items(self.session, item_ids)
        
        # Validate all items exist and are rentable
        found_items = {UUID(item.id): item for item in items}
        
        # Check for missing items
        missing_items = set(item_ids) - set(found_items.keys())
        if missing_items:
            raise NotFoundError(f"Items not found or not rentable: {list(missing_items)}")
        
        return found_items

    async def _batch_get_stock_levels_for_rental(self, item_ids: List[UUID], location_id: UUID) -> Dict[UUID, Any]:
        """Get stock levels with caching for rental operations."""
        # Use cached lookup for stock levels
        stock_levels = await RentalCache.get_stock_levels(self.session, item_ids, str(location_id))
        
        return {UUID(sl.item_id): sl for sl in stock_levels}

    def _validate_stock_availability_for_rental(self, items: List, stock_levels: Dict[UUID, Any]):
        """Validate stock availability for all rental items."""
        for item in items:
            stock_level = stock_levels.get(item.item_id)
            if not stock_level:
                raise ValidationError(
                    f"No stock found for item {item.item_id} at location"
                )
            
            requested_quantity = Decimal(str(item.quantity))
            available_quantity = stock_level.quantity_available
            
            if available_quantity < requested_quantity:
                raise ValidationError(
                    f"Insufficient stock for item {item.item_id}. "
                    f"Available: {available_quantity}, Requested: {requested_quantity}"
                )

    async def _batch_process_rental_stock_operations(
        self, 
        items: List, 
        stock_levels: Dict[UUID, Any], 
        transaction_id: UUID
    ):
        """
        Process all rental stock operations using bulk operations.
        Optimized version with bulk UPDATE instead of individual updates.
        """
        from app.modules.inventory.models import StockMovement, StockLevel
        from sqlalchemy import update, bindparam
        
        # Prepare bulk update data and stock movements
        stock_updates = []
        stock_movements = []
        
        for item in items:
            stock_level = stock_levels[item.item_id]
            quantity_change = Decimal(str(item.quantity))
            
            # Prepare update data for bulk operation
            stock_updates.append({
                'id': str(stock_level.id),
                'available_quantity': stock_level.available_quantity - quantity_change,
                'on_rent_quantity': stock_level.on_rent_quantity + quantity_change
            })
            
            # Create stock movement record
            movement = StockMovement(
                stock_level_id=stock_level.id,
                item_id=str(item.item_id),
                location_id=stock_level.location_id,
                movement_type=MovementType.RENTAL_OUT.value,
                reference_type=ReferenceType.TRANSACTION.value,
                reference_id=str(transaction_id),
                quantity_change=-quantity_change,
                quantity_before=stock_level.available_quantity,
                quantity_after=stock_level.available_quantity - quantity_change,
                reason=f"Rental transaction {transaction_id}",
                notes=f"Rental out - {item.quantity} units"
            )
            stock_movements.append(movement)
        
        # Execute bulk stock level update
        if stock_updates:
            stmt = (
                update(StockLevel)
                .where(StockLevel.id == bindparam('id'))
                .values(
                    available_quantity=bindparam('available_quantity'),
                    on_rent_quantity=bindparam('on_rent_quantity'),
                    updated_at=func.now()
                )
            )
            await self.session.execute(stmt, stock_updates)
        
        # Bulk add all stock movements
        if stock_movements:
            self.session.add_all(stock_movements)

    async def _generate_rental_transaction_number(self, rental_data: NewRentalRequest) -> str:
        """
        Generate unique rental transaction number efficiently.
        Optimized to avoid potential infinite loops and reduce database queries.
        """
        import time
        
        if rental_data.reference_number:
            # Quick existence check for custom reference number
            exists = await self.session.execute(
                select(1).where(
                    TransactionHeader.transaction_number == rental_data.reference_number
                ).limit(1)
            )
            if exists.scalar():
                raise ConflictError(f"Reference number '{rental_data.reference_number}' already exists")
            return rental_data.reference_number
        
        # Use timestamp-based generation for better uniqueness
        timestamp = int(time.time() * 1000)  # Millisecond precision
        date_str = rental_data.transaction_date.strftime('%Y%m%d')
        
        # Try timestamp-based number first (very unlikely to collide)
        transaction_number = f"REN-{date_str}-{timestamp % 1000000}"
        
        # Quick check if it exists
        exists = await self.session.execute(
            select(1).where(
                TransactionHeader.transaction_number == transaction_number
            ).limit(1)
        )
        
        if not exists.scalar():
            return transaction_number
        
        # Fallback: Add counter suffix if collision occurs
        for i in range(1, 100):
            transaction_number = f"REN-{date_str}-{timestamp % 1000000}-{i}"
            exists = await self.session.execute(
                select(1).where(
                    TransactionHeader.transaction_number == transaction_number
                ).limit(1)
            )
            if not exists.scalar():
                return transaction_number
        
        # If still no unique number, raise error (should never happen)
        raise ConflictError("Unable to generate unique transaction number")

    # ... [keeping existing methods] ...
