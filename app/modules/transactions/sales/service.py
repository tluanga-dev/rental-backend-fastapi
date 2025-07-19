"""
Sales Service

Business logic for sales-related operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.transactions.models import (
    TransactionHeader,
    TransactionLine,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    PaymentStatus,
    LineItemType,
)
from app.modules.transactions.base.repository import (
    TransactionHeaderRepository,
    TransactionLineRepository,
)
from app.modules.transactions.sales.schemas import (
    SaleResponse,
    SaleItemCreate,
    NewSaleRequest,
    NewSaleResponse,
    CustomerNestedResponse,
    LocationNestedResponse,
    SaleLineItemResponse,
)
from app.modules.customers.repository import CustomerRepository
from app.modules.inventory.repository import ItemRepository, StockLevelRepository, InventoryUnitRepository
from app.modules.inventory.models import StockLevel, StockMovement, MovementType, ReferenceType, InventoryUnit
from app.modules.master_data.locations.repository import LocationRepository
from app.core.logger import get_purchase_logger


class SalesService:
    """Service for sales transaction operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repository = TransactionHeaderRepository(session)
        self.line_repository = TransactionLineRepository(session)
        self.customer_repository = CustomerRepository(session)
        self.item_repository = ItemRepository(session)
        self.stock_level_repository = StockLevelRepository(session)
        self.inventory_unit_repository = InventoryUnitRepository(session)
        self.location_repository = LocationRepository(session)
        self.logger = get_purchase_logger()

    async def get_sale_transactions(
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
    ) -> List[SaleResponse]:
        """Get sale transactions with filtering options."""
        try:
            # Build filter conditions
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

            # Query transactions with lines
            stmt = (
                select(TransactionHeader)
                .where(and_(*filters))
                .options(selectinload(TransactionHeader.transaction_lines))
                .order_by(TransactionHeader.transaction_date.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            transactions = result.scalars().unique().all()

            # Get all unique customer and location IDs
            customer_ids = list({UUID(t.customer_id) for t in transactions if t.customer_id})
            location_ids = list({UUID(t.location_id) for t in transactions if t.location_id})
            
            # Batch fetch customers and locations
            customers = {}
            locations = {}
            
            if customer_ids:
                customers = {}
                for customer_id in customer_ids:
                    customer = await self.customer_repository.get_by_id(customer_id)
                    if customer:
                        customers[customer.id] = customer
            
            if location_ids:
                for location_id in location_ids:
                    location = await self.location_repository.get_by_id(location_id)
                    if location:
                        locations[location.id] = location

            # Get all unique item IDs from transaction lines
            item_ids = []
            for transaction in transactions:
                for line in transaction.transaction_lines:
                    if line.item_id:
                        item_ids.append(UUID(line.item_id))
            
            # Batch fetch items
            items = {}
            if item_ids:
                for item_id in list(set(item_ids)):
                    item = await self.item_repository.get_by_id(item_id)
                    if item:
                        items[str(item.id)] = {"id": item.id, "name": item.item_name}

            # Transform to sale response format
            sale_responses = []
            for transaction in transactions:
                customer = customers.get(UUID(transaction.customer_id)) if transaction.customer_id else None
                location = locations.get(UUID(transaction.location_id)) if transaction.location_id else None
                
                sale_response = SaleResponse.from_transaction(
                    transaction.to_dict(),
                    customer_details={"id": customer.id, "name": customer.name} if customer else None,
                    location_details={"id": location.id, "name": location.name} if location else None,
                    items_details=items
                )
                sale_responses.append(sale_response)

            return sale_responses

        except Exception as e:
            self.logger.log_debug_info("Error getting sale transactions", {"error": str(e)})
            raise

    async def get_sale_by_id(self, sale_id: UUID) -> SaleResponse:
        """Get a single sale transaction by ID."""
        try:
            # Get transaction with lines
            transaction = await self.transaction_repository.get_with_lines(sale_id)
            
            if not transaction:
                raise NotFoundError(f"Sale transaction {sale_id} not found")
            
            # Verify it's a sale transaction
            if transaction.transaction_type != TransactionType.SALE:
                raise ValidationError(f"Transaction {sale_id} is not a sale")

            # Get customer and location details
            customer = None
            location = None
            
            if transaction.customer_id:
                customer = await self.customer_repository.get_by_id(UUID(transaction.customer_id))
            
            if transaction.location_id:
                location = await self.location_repository.get_by_id(UUID(transaction.location_id))

            # Get item details for all lines
            item_ids = [UUID(line.item_id) for line in transaction.transaction_lines if line.item_id]
            items = {}
            
            if item_ids:
                for item_id in list(set(item_ids)):
                    item = await self.item_repository.get_by_id(item_id)
                    if item:
                        items[str(item.id)] = {"id": item.id, "name": item.item_name}

            # Transform to sale response
            return SaleResponse.from_transaction(
                transaction.to_dict(),
                customer_details={"id": customer.id, "name": customer.name} if customer else None,
                location_details={"id": location.id, "name": location.name} if location else None,
                items_details=items
            )

        except Exception as e:
            self.logger.log_debug_info("Error getting sale by ID", {"error": str(e)})
            raise

    async def create_new_sale(self, sale_data: NewSaleRequest) -> NewSaleResponse:
        """Create a new sale transaction."""
        try:
            self.logger.log_debug_info("Creating new sale", {"customer_id": str(sale_data.customer_id)})

            # Validate customer exists and can transact
            customer = await self.customer_repository.get_by_id(sale_data.customer_id)
            if not customer:
                raise NotFoundError(f"Customer {sale_data.customer_id} not found")
            
            if not customer.can_transact:
                raise ValidationError(f"Customer {customer.name} is not allowed to transact")

            # Validate all items exist and are saleable
            item_ids = [item.item_id for item in sale_data.items]
            items_dict = {}
            for item_id in item_ids:
                item = await self.item_repository.get_by_id(item_id)
                if item:
                    items_dict[str(item.id)] = item
            
            missing_items = set(str(item_id) for item_id in item_ids) - set(items_dict.keys())
            if missing_items:
                raise NotFoundError(f"Items not found: {list(missing_items)}")
            
            # Validate items are saleable
            non_saleable = [item.item_name for item in items_dict.values() if not item.is_saleable]
            if non_saleable:
                raise ValidationError(f"Items are not saleable: {non_saleable}")

            # Get default location if not provided
            location_id = None
            if hasattr(sale_data, 'location_id') and sale_data.location_id:
                location_id = sale_data.location_id
            else:
                # Get default location from settings or first available
                default_location = await self._get_default_location()
                location_id = default_location.id

            # Validate stock availability
            await self._validate_stock_availability(sale_data.items, location_id)

            # Generate transaction number
            transaction_number = await self._generate_sale_transaction_number(sale_data)

            # Begin transaction
            async with self.session.begin():
                # Create transaction header
                transaction = TransactionHeader(
                    transaction_number=transaction_number,
                    transaction_type=TransactionType.SALE,
                    transaction_date=datetime.combine(sale_data.transaction_date, datetime.min.time()),
                    customer_id=str(sale_data.customer_id),
                    location_id=str(location_id),
                    status=TransactionStatus.CONFIRMED,
                    payment_status=PaymentStatus.PENDING,
                    notes=sale_data.notes or "",
                    subtotal=Decimal("0"),
                    discount_amount=Decimal("0"),
                    tax_amount=Decimal("0"),
                    total_amount=Decimal("0"),
                    paid_amount=Decimal("0"),
                    is_active=True,
                )
                self.session.add(transaction)
                await self.session.flush()

                # Create transaction lines and calculate totals
                total_amount = Decimal("0")
                tax_total = Decimal("0")
                discount_total = Decimal("0")
                
                for idx, item_data in enumerate(sale_data.items):
                    item = items_dict[str(item_data.item_id)]
                    
                    # Calculate line totals
                    line_subtotal = item_data.unit_cost * Decimal(str(item_data.quantity))
                    tax_amount = (line_subtotal * (item_data.tax_rate or Decimal("0"))) / 100
                    discount_amount = item_data.discount_amount or Decimal("0")
                    line_total = line_subtotal + tax_amount - discount_amount

                    # Create transaction line
                    line = TransactionLine(
                        transaction_id=str(transaction.id),
                        line_number=idx + 1,
                        line_type=LineItemType.PRODUCT,
                        item_id=str(item.id),
                        description=item.item_name,
                        quantity=Decimal(str(item_data.quantity)),
                        unit_price=item_data.unit_cost,
                        tax_rate=item_data.tax_rate or Decimal("0"),
                        tax_amount=tax_amount,
                        discount_amount=discount_amount,
                        line_total=line_total,
                        notes=item_data.notes or "",
                        is_active=True,
                    )
                    self.session.add(line)
                    
                    total_amount += line_total
                    tax_total += tax_amount
                    discount_total += discount_amount

                    # Update stock levels and inventory units
                    await self._update_stock_for_sale(
                        item_id=item.id,
                        location_id=location_id,
                        quantity=item_data.quantity,
                        transaction_id=transaction.id,
                        customer_id=sale_data.customer_id
                    )

                # Update transaction totals
                transaction.subtotal = total_amount - tax_total + discount_total
                transaction.tax_amount = tax_total
                transaction.discount_amount = discount_total
                transaction.total_amount = total_amount

            # Get complete transaction for response
            result = await self.transaction_repository.get_with_lines(transaction.id)

            return NewSaleResponse(
                success=True,
                message="Sale transaction created successfully",
                data=result.to_dict(),
                transaction_id=transaction.id,
                transaction_number=transaction.transaction_number,
            )

        except Exception as e:
            self.logger.log_debug_info("Error creating sale", {"error": str(e)})
            await self.session.rollback()
            raise

    async def _get_default_location(self) -> Any:
        """Get default location for sales."""
        # Try to get the first active location
        stmt = select(self.location_repository.model).where(
            self.location_repository.model.is_active == True
        ).limit(1)
        result = await self.session.execute(stmt)
        location = result.scalar_one_or_none()
        
        if not location:
            raise ValidationError("No active locations found")
        
        return location

    async def _validate_stock_availability(self, items: List[SaleItemCreate], location_id: UUID):
        """Validate stock availability for all sale items."""
        for item in items:
            stock_level = await self.stock_level_repository.get_by_item_location(item.item_id, location_id)
            
            if not stock_level:
                raise ValidationError(f"No stock found for item {item.item_id} at location")
            
            if stock_level.available_quantity < Decimal(str(item.quantity)):
                raise ValidationError(
                    f"Insufficient stock for item {item.item_id}. "
                    f"Available: {stock_level.available_quantity}, Requested: {item.quantity}"
                )

    async def _generate_sale_transaction_number(self, sale_data: NewSaleRequest) -> str:
        """Generate unique sale transaction number."""
        if sale_data.reference_number:
            # Check if reference number already exists
            exists = await self.session.execute(
                select(1).where(
                    TransactionHeader.transaction_number == sale_data.reference_number
                ).limit(1)
            )
            if exists.scalar():
                raise ConflictError(f"Reference number '{sale_data.reference_number}' already exists")
            return sale_data.reference_number
        
        # Generate automatic number
        date_str = sale_data.transaction_date.strftime('%Y%m%d')
        
        # Get count of sales for the date
        count_result = await self.session.execute(
            select(func.count(TransactionHeader.id)).where(
                and_(
                    TransactionHeader.transaction_type == TransactionType.SALE,
                    func.date(TransactionHeader.transaction_date) == sale_data.transaction_date
                )
            )
        )
        count = count_result.scalar() or 0
        
        # Generate number with retry logic
        for i in range(100):
            transaction_number = f"SAL-{date_str}-{count + i + 1:04d}"
            exists = await self.session.execute(
                select(1).where(
                    TransactionHeader.transaction_number == transaction_number
                ).limit(1)
            )
            if not exists.scalar():
                return transaction_number
        
        raise ConflictError("Unable to generate unique transaction number")

    async def _update_stock_for_sale(
        self, 
        item_id: UUID, 
        location_id: UUID, 
        quantity: int,
        transaction_id: UUID,
        customer_id: UUID
    ):
        """Update stock levels and inventory units for a sale."""
        # Get stock level
        stock_level = await self.stock_level_repository.get_by_item_location(item_id, location_id)
        
        if not stock_level:
            raise ValidationError(f"Stock level not found for item {item_id} at location {location_id}")

        # Update stock level
        old_quantity = stock_level.quantity_on_hand
        old_available = stock_level.available_quantity
        
        stock_level.quantity_on_hand -= Decimal(str(quantity))
        stock_level.available_quantity -= Decimal(str(quantity))

        # Create stock movement record
        movement = StockMovement(
            stock_level_id=stock_level.id,
            item_id=str(item_id),
            location_id=str(location_id),
            movement_type=MovementType.SALE.value,
            reference_type=ReferenceType.TRANSACTION.value,
            reference_id=str(transaction_id),
            quantity_change=-Decimal(str(quantity)),
            quantity_before=old_quantity,
            quantity_after=stock_level.quantity_on_hand,
            reason=f"Sale transaction {transaction_id}",
            notes=f"Sale of {quantity} units to customer {customer_id}",
        )
        self.session.add(movement)

        # Mark inventory units as sold
        stmt = (
            select(InventoryUnit)
            .where(
                and_(
                    InventoryUnit.item_id == str(item_id),
                    InventoryUnit.location_id == str(location_id),
                    InventoryUnit.status == "AVAILABLE"
                )
            )
            .limit(quantity)
        )
        result = await self.session.execute(stmt)
        units = result.scalars().all()

        for unit in units:
            unit.status = "SOLD"
            unit.assigned_to_customer_id = str(customer_id)
            unit.transaction_id = str(transaction_id)

    async def get_sale_returns(self, sale_id: UUID) -> Dict[str, Any]:
        """Get all return transactions for a specific sale."""
        try:
            # Get the original sale transaction
            sale_txn = await self.transaction_repository.get(sale_id)
            
            if not sale_txn:
                raise NotFoundError(f"Sale transaction {sale_id} not found")
            
            # Verify it's a sale transaction
            if sale_txn.transaction_type != TransactionType.SALE:
                raise ValidationError(f"Transaction {sale_id} is not a sale transaction")
            
            # Get all return transactions that reference this sale
            returns = await self.transaction_repository.get_all_with_lines(
                reference_transaction_id=sale_id,
                transaction_type=TransactionType.RETURN,
                active_only=True
            )
            
            # Transform to response format
            return_list = []
            for return_txn in returns:
                return_list.append({
                    "id": return_txn.id,
                    "transaction_number": return_txn.transaction_number,
                    "transaction_date": return_txn.transaction_date,
                    "status": return_txn.status,
                    "total_amount": float(return_txn.total_amount),
                    "items_returned": len(return_txn.transaction_lines),
                    "created_at": return_txn.created_at
                })
            
            return {
                "sale_id": sale_id,
                "sale_number": sale_txn.transaction_number,
                "returns": return_list,
                "total_returns": len(return_list)
            }
            
        except Exception as e:
            self.logger.log_debug_info("Error getting sale returns", {"error": str(e)})
            raise