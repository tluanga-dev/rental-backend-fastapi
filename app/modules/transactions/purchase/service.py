"""
Purchase transaction service for business logic.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.modules.transactions.models.transaction_headers import TransactionHeader, TransactionType
from app.modules.transactions.models.transaction_lines import TransactionLine
from app.modules.transactions.purchase.schemas import (
    PurchaseTransactionFilterRequest,
    PurchaseTransactionSummary,
    PurchaseTransactionDataResponse,
    PaginationParams
)
from app.modules.transactions.repository import TransactionRepository, TransactionLineRepository
from app.modules.suppliers.repository import SupplierRepository
from app.modules.master_data.locations.repository import LocationRepository
from app.modules.master_data.item_master.repository import ItemRepository


class PurchaseService:
    """Service for handling purchase transaction operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repository = TransactionRepository(session)
        self.transaction_line_repository = TransactionLineRepository(session)
        self.supplier_repository = SupplierRepository(session)
        self.location_repository = LocationRepository(session)
        self.item_repository = ItemRepository(session)
    
    async def list_purchase_transactions(
        self,
        filters: PurchaseTransactionFilterRequest,
        pagination: PaginationParams
    ) -> Dict[str, Any]:
        """
        List purchase transactions with filtering and pagination.
        
        Args:
            filters: Filter criteria
            pagination: Pagination parameters
            
        Returns:
            Dictionary containing transactions and pagination info
        """
        # Build filters dictionary
        filter_dict = {}
        if filters.start_date:
            filter_dict["start_date"] = datetime.combine(filters.start_date, datetime.min.time())
        if filters.end_date:
            filter_dict["end_date"] = datetime.combine(filters.end_date, datetime.max.time())
        if filters.supplier_id:
            filter_dict["supplier_id"] = filters.supplier_id
        if filters.location_id:
            filter_dict["location_id"] = filters.location_id
        if filters.status:
            filter_dict["status"] = filters.status
        if filters.payment_status:
            filter_dict["payment_status"] = filters.payment_status
        if filters.transaction_number:
            filter_dict["transaction_number"] = filters.transaction_number
        if filters.min_amount:
            filter_dict["min_amount"] = filters.min_amount
        if filters.max_amount:
            filter_dict["max_amount"] = filters.max_amount
        if filters.item_ids:
            filter_dict["item_ids"] = filters.item_ids
        
        # Get total count
        total_count = await self.transaction_repository.count_purchase_transactions(filter_dict)
        
        # Get transactions
        transactions = await self.transaction_repository.get_purchase_transactions_with_filters(
            filters=filter_dict,
            skip=pagination.skip,
            limit=pagination.limit,
            sort_by=pagination.sort_by or "transaction_date",
            sort_order=pagination.sort_order or "desc"
        )
        
        # Build response with enriched data
        transaction_summaries = []
        for transaction in transactions:
            # Get supplier name
            supplier_name = None
            if transaction.customer_id:
                supplier = await self.supplier_repository.get_by_id(UUID(transaction.customer_id))
                supplier_name = supplier.company_name if supplier else None
            
            # Get location name
            location_name = None
            if transaction.location_id:
                location = await self.location_repository.get_by_id(UUID(transaction.location_id))
                location_name = location.name if location else None
            
            summary = PurchaseTransactionSummary(
                id=transaction.id,
                transaction_number=transaction.transaction_number,
                transaction_date=transaction.transaction_date,
                supplier_name=supplier_name,
                location_name=location_name,
                status=transaction.status.value,
                payment_status=transaction.payment_status.value,
                total_amount=transaction.total_amount,
                item_count=len(transaction.transaction_lines),
                created_at=transaction.created_at
            )
            transaction_summaries.append(summary)
        
        # Calculate pagination metadata
        total_pages = (total_count + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 1
        current_page = (pagination.skip // pagination.limit) + 1 if pagination.limit > 0 else 1
        
        return {
            "data": transaction_summaries,
            "pagination": {
                "total": total_count,
                "skip": pagination.skip,
                "limit": pagination.limit,
                "current_page": current_page,
                "total_pages": total_pages,
                "has_next": current_page < total_pages,
                "has_prev": current_page > 1
            }
        }
    
    async def get_purchase_transaction_by_id(self, transaction_id: UUID) -> PurchaseTransactionDataResponse:
        """
        Get detailed purchase transaction by ID.
        
        Args:
            transaction_id: Transaction UUID
            
        Returns:
            Detailed transaction data
            
        Raises:
            NotFoundError: If transaction not found
        """
        transaction = await self.transaction_repository.get_purchase_transaction_details(transaction_id)
        if not transaction:
            raise NotFoundError(f"Purchase transaction with ID {transaction_id} not found")
        
        # Build response
        return PurchaseTransactionDataResponse(
            id=transaction.id,
            transaction_number=transaction.transaction_number,
            transaction_type=transaction.transaction_type.value,
            transaction_date=transaction.transaction_date.isoformat(),
            customer_id=UUID(transaction.customer_id) if transaction.customer_id else None,
            location_id=UUID(transaction.location_id) if transaction.location_id else None,
            status=transaction.status.value,
            payment_status=transaction.payment_status.value,
            subtotal=transaction.subtotal,
            discount_amount=transaction.discount_amount,
            tax_amount=transaction.tax_amount,
            total_amount=transaction.total_amount,
            paid_amount=transaction.paid_amount,
            notes=transaction.notes,
            created_at=transaction.created_at.isoformat(),
            updated_at=transaction.updated_at.isoformat(),
            transaction_lines=[
                PurchaseTransactionLineResponse(
                    id=line.id,
                    line_number=line.line_number,
                    item_id=UUID(line.item_id) if line.item_id else None,
                    description=line.description,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    tax_rate=line.tax_rate,
                    tax_amount=line.tax_amount,
                    discount_amount=line.discount_amount,
                    line_total=line.line_total,
                    notes=line.notes,
                    created_at=line.created_at.isoformat(),
                    updated_at=line.updated_at.isoformat()
                )
                for line in transaction.transaction_lines
            ]
        )
    
    async def get_purchase_transactions_by_supplier(
        self,
        supplier_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[PurchaseTransactionSummary]:
        """Get purchase transactions for a specific supplier."""
        # Validate supplier exists
        supplier = await self.supplier_repository.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        
        transactions = await self.transaction_repository.get_purchase_transactions_by_supplier(
            supplier_id=supplier_id,
            skip=skip,
            limit=limit
        )
        
        # Build summaries
        summaries = []
        for transaction in transactions:
            location_name = None
            if transaction.location_id:
                location = await self.location_repository.get_by_id(UUID(transaction.location_id))
                location_name = location.name if location else None
            
            summary = PurchaseTransactionSummary(
                id=transaction.id,
                transaction_number=transaction.transaction_number,
                transaction_date=transaction.transaction_date,
                supplier_name=supplier.company_name,
                location_name=location_name,
                status=transaction.status.value,
                payment_status=transaction.payment_status.value,
                total_amount=transaction.total_amount,
                item_count=len(transaction.transaction_lines),
                created_at=transaction.created_at
            )
            summaries.append(summary)
        
        return summaries
    
    async def get_purchase_transactions_by_items(
        self,
        item_ids: List[UUID],
        skip: int = 0,
        limit: int = 100
    ) -> List[PurchaseTransactionSummary]:
        """Get purchase transactions containing specific items."""
        # Validate items exist
        for item_id in item_ids:
            item = await self.item_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Item with ID {item_id} not found")
        
        transactions = await self.transaction_repository.get_purchase_transactions_by_items(
            item_ids=item_ids,
            skip=skip,
            limit=limit
        )
        
        # Build summaries
        summaries = []
        for transaction in transactions:
            supplier_name = None
            if transaction.customer_id:
                supplier = await self.supplier_repository.get_by_id(UUID(transaction.customer_id))
                supplier_name = supplier.company_name if supplier else None
            
            location_name = None
            if transaction.location_id:
                location = await self.location_repository.get_by_id(UUID(transaction.location_id))
                location_name = location.name if location else None
            
            summary = PurchaseTransactionSummary(
                id=transaction.id,
                transaction_number=transaction.transaction_number,
                transaction_date=transaction.transaction_date,
                supplier_name=supplier_name,
                location_name=location_name,
                status=transaction.status.value,
                payment_status=transaction.payment_status.value,
                total_amount=transaction.total_amount,
                item_count=len(transaction.transaction_lines),
                created_at=transaction.created_at
            )
            summaries.append(summary)
        
        return summaries
