"""
Base Transaction Services

Shared service functionality for all transaction types.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType, TransactionStatus
from app.modules.transactions.base.repository import BaseTransactionRepository, BaseTransactionLineRepository
from app.modules.transactions.base.schemas import (
    TransactionHeaderCreate,
    TransactionHeaderUpdate,
    TransactionHeaderResponse,
    TransactionLineCreate,
    TransactionLineUpdate,
    TransactionLineResponse,
    TransactionListResponse,
    TransactionSummary
)


class BaseTransactionService:
    """Base service for transaction operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.header_repository = BaseTransactionRepository(session)
        self.line_repository = BaseTransactionLineRepository(session)
    
    async def get_transaction(self, transaction_id: UUID) -> Optional[TransactionHeaderResponse]:
        """Get transaction by ID."""
        transaction = await self.header_repository.get_with_lines(transaction_id)
        if not transaction:
            return None
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_by_transaction_number(self, transaction_number: str) -> Optional[TransactionHeaderResponse]:
        """Get transaction by transaction number."""
        transaction = await self.header_repository.get_by_transaction_number(transaction_number)
        if not transaction:
            return None
        return TransactionHeaderResponse.model_validate(transaction)
    
    async def get_transactions_by_type(
        self,
        transaction_type: TransactionType,
        page: int = 1,
        page_size: int = 100,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> TransactionListResponse:
        """Get transactions by type with pagination."""
        offset = (page - 1) * page_size
        
        transactions = await self.header_repository.get_by_type(
            transaction_type=transaction_type,
            limit=page_size,
            offset=offset,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        total = await self.header_repository.count_by_type(
            transaction_type=transaction_type,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        transaction_summaries = [
            TransactionSummary.model_validate(transaction)
            for transaction in transactions
        ]
        
        total_pages = (total + page_size - 1) // page_size
        
        return TransactionListResponse(
            transactions=transaction_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def get_customer_transactions(
        self,
        customer_id: str,
        transaction_type: Optional[TransactionType] = None,
        page: int = 1,
        page_size: int = 100
    ) -> TransactionListResponse:
        """Get transactions for a specific customer."""
        offset = (page - 1) * page_size
        
        transactions = await self.header_repository.get_by_customer(
            customer_id=customer_id,
            transaction_type=transaction_type,
            limit=page_size,
            offset=offset
        )
        
        # For total count, we need to implement count_by_customer in repository
        total = len(transactions)  # Simplified for now
        
        transaction_summaries = [
            TransactionSummary.model_validate(transaction)
            for transaction in transactions
        ]
        
        total_pages = (total + page_size - 1) // page_size
        
        return TransactionListResponse(
            transactions=transaction_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_transaction(
        self,
        transaction_id: UUID,
        update_data: TransactionHeaderUpdate
    ) -> Optional[TransactionHeaderResponse]:
        """Update transaction."""
        transaction = await self.header_repository.get_by_id(transaction_id)
        if not transaction:
            return None
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)
        
        await self.session.commit()
        
        # Return updated transaction
        return await self.get_transaction(transaction_id)
    
    async def update_status(
        self,
        transaction_id: UUID,
        status: TransactionStatus
    ) -> Optional[TransactionHeaderResponse]:
        """Update transaction status."""
        success = await self.header_repository.update_status(transaction_id, status)
        if not success:
            return None
        
        return await self.get_transaction(transaction_id)
    
    async def update_payment(
        self,
        transaction_id: UUID,
        paid_amount: Decimal,
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None
    ) -> Optional[TransactionHeaderResponse]:
        """Update payment information."""
        success = await self.header_repository.update_payment(
            transaction_id=transaction_id,
            paid_amount=paid_amount,
            payment_method=payment_method,
            payment_reference=payment_reference
        )
        if not success:
            return None
        
        return await self.get_transaction(transaction_id)
    
    async def get_pending_payments(
        self,
        transaction_type: Optional[TransactionType] = None,
        customer_id: Optional[str] = None
    ) -> List[TransactionHeaderResponse]:
        """Get transactions with pending payments."""
        transactions = await self.header_repository.get_pending_payments(
            transaction_type=transaction_type,
            customer_id=customer_id
        )
        
        return [
            TransactionHeaderResponse.model_validate(transaction)
            for transaction in transactions
        ]
    
    async def get_financial_summary(
        self,
        transaction_type: TransactionType,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get financial summary for transaction type."""
        return await self.header_repository.get_financial_summary(
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to
        )
    
    async def delete_transaction(self, transaction_id: UUID) -> bool:
        """Delete transaction."""
        transaction = await self.header_repository.get_by_id(transaction_id)
        if not transaction:
            return False
        
        await self.header_repository.delete(transaction_id)
        return True
    
    def generate_transaction_number(self, transaction_type: TransactionType) -> str:
        """Generate transaction number based on type."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        type_prefix = {
            TransactionType.SALE: "SAL",
            TransactionType.PURCHASE: "PUR",
            TransactionType.RENTAL: "REN",
            TransactionType.RETURN: "RET",
            TransactionType.ADJUSTMENT: "ADJ"
        }
        prefix = type_prefix.get(transaction_type, "TXN")
        return f"{prefix}-{timestamp}"
    
    def calculate_transaction_totals(self, lines: List[TransactionLineCreate]) -> Dict[str, Decimal]:
        """Calculate transaction totals from line items."""
        subtotal = Decimal("0")
        total_discount = Decimal("0")
        total_tax = Decimal("0")
        
        for line in lines:
            line_subtotal = line.quantity * line.unit_price
            subtotal += line_subtotal
            total_discount += line.discount_amount
            total_tax += line.tax_amount
        
        total_amount = subtotal - total_discount + total_tax
        
        return {
            "subtotal": subtotal,
            "discount_amount": total_discount,
            "tax_amount": total_tax,
            "total_amount": total_amount
        }
    
    def validate_transaction_data(self, transaction_data: TransactionHeaderCreate) -> List[str]:
        """Validate transaction data and return list of errors."""
        errors = []
        
        # Validate line items
        if not transaction_data.transaction_lines:
            errors.append("Transaction must have at least one line item")
        
        # Validate line numbers are unique
        line_numbers = [line.line_number for line in transaction_data.transaction_lines]
        if len(line_numbers) != len(set(line_numbers)):
            errors.append("Line numbers must be unique")
        
        # Validate amounts
        if transaction_data.paid_amount > transaction_data.total_amount:
            errors.append("Paid amount cannot exceed total amount")
        
        # Validate dates
        if transaction_data.due_date and transaction_data.due_date < transaction_data.transaction_date.date():
            errors.append("Due date cannot be before transaction date")
        
        return errors