"""
Purchase Service

Business logic for purchase transaction operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, func

from app.core.errors import NotFoundError, ValidationError
from app.modules.transactions.base.models import (
    TransactionHeader, 
    TransactionType, 
    TransactionLine,
    TransactionStatus,
    PaymentStatus
)
from app.modules.transactions.purchase.schemas import (
    PurchaseResponse,
    PurchaseDetail,
    NewPurchaseRequest,
    NewPurchaseResponse
)
from app.modules.transactions.base.repository import TransactionHeaderRepository, TransactionLineRepository
from app.modules.suppliers.repository import SupplierRepository
from app.modules.master_data.locations.repository import LocationRepository
from app.modules.master_data.item_master.repository import ItemMasterRepository
from app.modules.inventory.repository import StockLevelRepository, StockMovementRepository
from app.modules.inventory.models import MovementType, ReferenceType


class PurchaseService:
    """Service for handling purchase transaction operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repository = TransactionHeaderRepository(session)
        self.transaction_line_repository = TransactionLineRepository(session)
        self.supplier_repository = SupplierRepository(session)
        self.location_repository = LocationRepository(session)
        self.item_repository = ItemMasterRepository(session)
        self.stock_level_repository = StockLevelRepository(session)
        self.stock_movement_repository = StockMovementRepository(session)
    
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
        """
        Get purchase transactions with filtering options.
        """
        # Build query
        query = select(TransactionHeader).where(
            TransactionHeader.transaction_type == TransactionType.PURCHASE
        )
        
        # Apply filters
        if date_from:
            query = query.where(TransactionHeader.transaction_date >= date_from)
        if date_to:
            query = query.where(TransactionHeader.transaction_date <= date_to)
        if amount_from:
            query = query.where(TransactionHeader.total_amount >= amount_from)
        if amount_to:
            query = query.where(TransactionHeader.total_amount <= amount_to)
        if supplier_id:
            query = query.where(TransactionHeader.customer_id == str(supplier_id))
        if status:
            query = query.where(TransactionHeader.status == status)
        if payment_status:
            query = query.where(TransactionHeader.payment_status == payment_status)
            
        # Add ordering and pagination
        query = query.order_by(TransactionHeader.transaction_date.desc())
        query = query.offset(skip).limit(limit)
        
        # Execute query with eager loading
        query = query.options(selectinload(TransactionHeader.transaction_lines))
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        # Transform to purchase response format
        purchase_responses = []
        for transaction in transactions:
            # Get supplier details
            supplier = None
            if transaction.customer_id:
                supplier = await self.supplier_repository.get_by_id(UUID(transaction.customer_id))
            
            # Get location details
            location = None
            if transaction.location_id:
                location = await self.location_repository.get_by_id(UUID(transaction.location_id))
                
            # Get item details for each line
            items_details = {}
            for line in transaction.transaction_lines:
                if line.item_id:
                    item = await self.item_repository.get_by_id(UUID(line.item_id))
                    if item:
                        items_details[str(line.item_id)] = {
                            "id": item.id,
                            "name": item.item_name
                        }
            
            # Convert transaction to dict with proper line serialization
            transaction_dict = {
                "id": transaction.id,
                "transaction_number": transaction.transaction_number,
                "transaction_type": transaction.transaction_type,
                "transaction_date": transaction.transaction_date,
                "customer_id": transaction.customer_id,
                "location_id": transaction.location_id,
                "status": transaction.status,
                "payment_status": transaction.payment_status,
                "subtotal": transaction.subtotal,
                "tax_amount": transaction.tax_amount,
                "discount_amount": transaction.discount_amount,
                "total_amount": transaction.total_amount,
                "notes": transaction.notes,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at,
                "transaction_lines": [
                    {
                        "id": line.id,
                        "item_id": line.item_id,
                        "quantity": line.quantity,
                        "unit_price": line.unit_price,
                        "tax_rate": line.tax_rate,
                        "tax_amount": line.tax_amount,
                        "discount_amount": line.discount_amount,
                        "line_total": line.line_total,
                        "description": line.description,
                        "notes": line.notes,
                        "created_at": line.created_at,
                        "updated_at": line.updated_at,
                    }
                    for line in transaction.transaction_lines
                ]
            }
            
            purchase_response = PurchaseResponse.from_transaction(
                transaction_dict,
                supplier_details={"id": supplier.id, "name": supplier.company_name} if supplier else None,
                location_details={"id": location.id, "name": location.location_name} if location else None,
                items_details=items_details
            )
            purchase_responses.append(purchase_response)
            
        return purchase_responses
    
    async def get_purchase_by_id(self, purchase_id: UUID) -> PurchaseResponse:
        """Get a single purchase transaction by ID."""
        transaction = await self.transaction_repository.get_by_id(purchase_id)
        
        if not transaction:
            raise NotFoundError(f"Purchase transaction {purchase_id} not found")
            
        if transaction.transaction_type != TransactionType.PURCHASE:
            raise ValidationError(f"Transaction {purchase_id} is not a purchase transaction")
        
        # Get supplier details
        supplier = None
        if transaction.customer_id:
            supplier = await self.supplier_repository.get_by_id(UUID(transaction.customer_id))
        
        # Get location details
        location = None
        if transaction.location_id:
            location = await self.location_repository.get_by_id(UUID(transaction.location_id))
            
        # Get item details for each line
        items_details = {}
        for line in transaction.transaction_lines:
            if line.item_id:
                item = await self.item_repository.get_by_id(UUID(line.item_id))
                if item:
                    items_details[str(line.item_id)] = {
                        "id": item.id,
                        "name": item.item_name
                    }
        
        # Convert transaction to dict with proper line serialization
        transaction_dict = {
            "id": transaction.id,
            "transaction_number": transaction.transaction_number,
            "transaction_type": transaction.transaction_type,
            "transaction_date": transaction.transaction_date,
            "customer_id": transaction.customer_id,
            "location_id": transaction.location_id,
            "status": transaction.status,
            "payment_status": transaction.payment_status,
            "subtotal": transaction.subtotal,
            "tax_amount": transaction.tax_amount,
            "discount_amount": transaction.discount_amount,
            "total_amount": transaction.total_amount,
            "notes": transaction.notes,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            "transaction_lines": [
                {
                    "id": line.id,
                    "item_id": line.item_id,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "tax_rate": line.tax_rate,
                    "tax_amount": line.tax_amount,
                    "discount_amount": line.discount_amount,
                    "line_total": line.line_total,
                    "description": line.description,
                    "notes": line.notes,
                    "created_at": line.created_at,
                    "updated_at": line.updated_at,
                }
                for line in transaction.transaction_lines
            ]
        }
        
        return PurchaseResponse.from_transaction(
            transaction_dict,
            supplier_details={"id": supplier.id, "name": supplier.company_name} if supplier else None,
            location_details={"id": location.id, "name": location.location_name} if location else None,
            items_details=items_details
        )
    
    async def create_new_purchase(self, purchase_data: NewPurchaseRequest) -> NewPurchaseResponse:
        """Create a new purchase transaction."""
        # Validate supplier exists
        supplier = await self.supplier_repository.get_by_id(purchase_data.supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {purchase_data.supplier_id} not found")
        
        # Validate location exists
        location = await self.location_repository.get_by_id(purchase_data.location_id)
        if not location:
            raise NotFoundError(f"Location with ID {purchase_data.location_id} not found")
        
        # Validate all items exist
        for item_data in purchase_data.items:
            item = await self.item_repository.get_by_id(UUID(item_data.item_id))
            if not item:
                raise NotFoundError(f"Item with ID {item_data.item_id} not found")
        
        # Generate transaction number
        transaction_number = await self._generate_transaction_number()
        
        # Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.PURCHASE,
            transaction_date=purchase_data.purchase_date,
            customer_id=str(purchase_data.supplier_id),  # supplier_id maps to customer_id
            location_id=str(purchase_data.location_id),
            status=TransactionStatus.COMPLETED,
            payment_status=PaymentStatus.PENDING,
            notes=purchase_data.notes,
            reference_number=purchase_data.reference_number,
            subtotal=Decimal("0"),
            tax_amount=Decimal("0"),
            discount_amount=Decimal("0"),
            total_amount=Decimal("0"),
            paid_amount=Decimal("0"),
            created_by=str(UUID("00000000-0000-0000-0000-000000000000")),  # System user
            updated_by=str(UUID("00000000-0000-0000-0000-000000000000"))
        )
        
        self.session.add(transaction)
        await self.session.flush()
        
        # Create transaction lines and calculate totals
        line_number = 1
        subtotal = Decimal("0")
        total_tax = Decimal("0")
        total_discount = Decimal("0")
        
        for item_data in purchase_data.items:
            # Get item details for description
            item = await self.item_repository.get_by_id(UUID(item_data.item_id))
            
            # Calculate line amounts
            line_subtotal = Decimal(str(item_data.quantity)) * Decimal(str(item_data.unit_cost))
            tax_amount = (line_subtotal * Decimal(str(item_data.tax_rate or 0))) / 100
            discount_amount = Decimal(str(item_data.discount_amount or 0))
            line_total = line_subtotal + tax_amount - discount_amount
            
            # Create transaction line
            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                item_id=str(item_data.item_id),
                quantity=Decimal(str(item_data.quantity)),
                unit_price=Decimal(str(item_data.unit_cost)),
                tax_rate=Decimal(str(item_data.tax_rate or 0)),
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                line_total=line_total,
                description=f"{item.item_name} (Condition: {item_data.condition})",
                notes=item_data.notes
            )
            
            self.session.add(line)
            
            # Update totals
            subtotal += line_subtotal
            total_tax += tax_amount
            total_discount += discount_amount
            line_number += 1
            
            # Update stock levels
            await self._update_stock_for_purchase(
                item_id=UUID(item_data.item_id),
                location_id=purchase_data.location_id,
                quantity=Decimal(str(item_data.quantity)),
                transaction_id=transaction.id,
                condition=item_data.condition
            )
        
        # Update transaction totals
        transaction.subtotal = subtotal
        transaction.tax_amount = total_tax
        transaction.discount_amount = total_discount
        transaction.total_amount = subtotal + total_tax - total_discount
        
        await self.session.commit()
        
        # Return response
        return NewPurchaseResponse(
            success=True,
            message="Purchase created successfully",
            transaction_id=transaction.id,
            transaction_number=transaction.transaction_number,
            data={
                "id": str(transaction.id),
                "transaction_number": transaction.transaction_number,
                "transaction_type": transaction.transaction_type.value,
                "transaction_date": transaction.transaction_date.isoformat(),
                "supplier_id": transaction.customer_id,
                "location_id": transaction.location_id,
                "status": transaction.status.value,
                "payment_status": transaction.payment_status.value,
                "subtotal": float(transaction.subtotal),
                "tax_amount": float(transaction.tax_amount),
                "discount_amount": float(transaction.discount_amount),
                "total_amount": float(transaction.total_amount),
                "transaction_lines": [
                    {
                        "id": str(line.id),
                        "line_number": line.line_number,
                        "item_id": line.item_id,
                        "quantity": float(line.quantity),
                        "unit_price": float(line.unit_price),
                        "tax_rate": float(line.tax_rate),
                        "tax_amount": float(line.tax_amount),
                        "discount_amount": float(line.discount_amount),
                        "line_total": float(line.line_total),
                        "description": line.description
                    }
                    for line in transaction.transaction_lines
                ]
            }
        )
    
    async def _generate_transaction_number(self) -> str:
        """Generate unique transaction number."""
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get count of purchases today
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = select(func.count(TransactionHeader.id)).where(
            and_(
                TransactionHeader.transaction_type == TransactionType.PURCHASE,
                TransactionHeader.created_at >= start_of_day
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        
        return f"PUR-{date_str}-{count + 1:04d}"
    
    async def _update_stock_for_purchase(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity: Decimal,
        transaction_id: UUID,
        condition: str
    ):
        """Update stock levels for a purchase."""
        # Get or create stock level
        stock_level = await self.stock_level_repository.get_by_item_and_location(
            item_id, location_id
        )
        
        if not stock_level:
            # Create new stock level
            stock_level = await self.stock_level_repository.create_stock_level(
                item_id=item_id,
                location_id=location_id,
                quantity_on_hand=quantity,
                quantity_available=quantity
            )
        else:
            # Update existing stock level
            stock_level.quantity_on_hand += quantity
            stock_level.quantity_available += quantity
        
        # Create stock movement record
        await self.stock_movement_repository.create_movement(
            item_id=item_id,
            location_id=location_id,
            movement_type=MovementType.PURCHASE,
            quantity_change=quantity,
            reference_type=ReferenceType.TRANSACTION,
            reference_id=str(transaction_id),
            notes=f"Purchase transaction - Condition: {condition}",
            quantity_before=stock_level.quantity_on_hand - quantity,
            quantity_after=stock_level.quantity_on_hand
        )
        
        await self.session.commit()