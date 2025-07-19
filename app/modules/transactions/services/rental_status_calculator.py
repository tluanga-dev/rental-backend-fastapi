"""
Rental Status Calculation Service

Implements the exact business rules defined in the PRD for calculating
rental transaction status at both header and line item levels.
"""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.modules.transactions.base.models import (
    TransactionHeader, 
    TransactionLine,
    TransactionType,
    RentalStatus,
    RentalLifecycle,
    RentalStatusLog,
    RentalStatusChangeReason
)
from app.core.errors import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class LineItemStatus(PyEnum):
    """Line item rental status as defined in PRD."""
    ACTIVE = "ACTIVE"
    LATE = "LATE"
    LATE_PARTIAL_RETURN = "LATE_PARTIAL_RETURN"
    PARTIAL_RETURN = "PARTIAL_RETURN"
    RETURNED = "RETURNED"


class HeaderStatus(PyEnum):
    """Header rental status as defined in PRD."""
    ACTIVE = "ACTIVE"
    LATE = "LATE"
    LATE_PARTIAL_RETURN = "LATE_PARTIAL_RETURN"
    PARTIAL_RETURN = "PARTIAL_RETURN"
    RETURNED = "RETURNED"


class RentalStatusCalculator:
    """
    Service for calculating rental status according to PRD business rules.
    
    This service implements the exact status calculation logic defined in the PRD:
    
    Line Item Status Rules:
    1. Active: Item with correct quantity is within return time frame AND no returns made yet
    2. Late: Item is past the return period
    3. Late - Partial Return: Some quantity returned AND item return time has passed
    4. Partial Return: Item is within return time frame AND item is not fully returned yet
    5. Returned: Item is returned within the return time frame
    
    Header Status Rules:
    1. Active: All items within return time frame AND no returns made yet
    2. Late: Some or all items are past the return period
    3. Late - Partial Return: Some items returned AND some or all items are late for return
    4. Partial Return: All items within return time frame AND some items returned
    5. Returned: All items are returned
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def calculate_line_item_status(
        self, 
        line: TransactionLine, 
        as_of_date: Optional[date] = None
    ) -> LineItemStatus:
        """
        Calculate the status of a single rental line item according to PRD rules.
        
        Args:
            line: The transaction line to evaluate
            as_of_date: Date to calculate status as of (defaults to today)
            
        Returns:
            LineItemStatus enum value
        """
        if not as_of_date:
            as_of_date = date.today()
        
        # Get rental dates from the line
        rental_end_date = line.rental_end_date
        if not rental_end_date:
            # If no rental end date, treat as active
            return LineItemStatus.ACTIVE
        
        # Check if item is past return period
        is_past_return_period = rental_end_date < as_of_date
        
        # Check return status
        total_quantity = line.quantity
        returned_quantity = line.returned_quantity or Decimal('0')
        has_returns = returned_quantity > 0
        is_fully_returned = returned_quantity >= total_quantity
        
        # Apply PRD business rules
        if is_fully_returned:
            # Rule 5: Returned - Item is fully returned
            return LineItemStatus.RETURNED
        elif has_returns and is_past_return_period:
            # Rule 3: Late - Partial Return - Some quantity returned AND past return time
            return LineItemStatus.LATE_PARTIAL_RETURN
        elif has_returns and not is_past_return_period:
            # Rule 4: Partial Return - Item is within time frame AND not fully returned
            return LineItemStatus.PARTIAL_RETURN
        elif is_past_return_period:
            # Rule 2: Late - Item is past the return period
            return LineItemStatus.LATE
        else:
            # Rule 1: Active - Within time frame AND no returns made yet
            return LineItemStatus.ACTIVE
    
    async def calculate_header_status(
        self, 
        transaction: TransactionHeader, 
        as_of_date: Optional[date] = None
    ) -> HeaderStatus:
        """
        Calculate the status of a rental transaction header according to PRD rules.
        
        Args:
            transaction: The transaction header to evaluate
            as_of_date: Date to calculate status as of (defaults to today)
            
        Returns:
            HeaderStatus enum value
        """
        if not as_of_date:
            as_of_date = date.today()
        
        # Ensure we have transaction lines loaded
        if not transaction.transaction_lines:
            result = await self.session.execute(
                select(TransactionHeader)
                .where(TransactionHeader.id == transaction.id)
                .options(selectinload(TransactionHeader.transaction_lines))
            )
            transaction = result.scalar_one_or_none()
            if not transaction:
                raise NotFoundError(f"Transaction {transaction.id} not found")
        
        # Calculate status for each line item
        line_statuses = []
        for line in transaction.transaction_lines:
            line_status = await self.calculate_line_item_status(line, as_of_date)
            line_statuses.append(line_status)
        
        if not line_statuses:
            # No lines, default to active
            return HeaderStatus.ACTIVE
        
        # Count status types
        status_counts = {
            LineItemStatus.ACTIVE: 0,
            LineItemStatus.LATE: 0,
            LineItemStatus.LATE_PARTIAL_RETURN: 0,
            LineItemStatus.PARTIAL_RETURN: 0,
            LineItemStatus.RETURNED: 0
        }
        
        for status in line_statuses:
            status_counts[status] += 1
        
        total_lines = len(line_statuses)
        has_late_items = status_counts[LineItemStatus.LATE] > 0 or status_counts[LineItemStatus.LATE_PARTIAL_RETURN] > 0
        has_returned_items = status_counts[LineItemStatus.RETURNED] > 0 or status_counts[LineItemStatus.PARTIAL_RETURN] > 0 or status_counts[LineItemStatus.LATE_PARTIAL_RETURN] > 0
        all_returned = status_counts[LineItemStatus.RETURNED] == total_lines
        
        # Apply PRD business rules for header status
        if all_returned:
            # Rule 5: Returned - All items are returned
            return HeaderStatus.RETURNED
        elif has_late_items and has_returned_items:
            # Rule 3: Late - Partial Return - Some items returned AND some or all items are late
            return HeaderStatus.LATE_PARTIAL_RETURN
        elif has_late_items:
            # Rule 2: Late - Some or all items are past the return period
            return HeaderStatus.LATE
        elif has_returned_items:
            # Rule 4: Partial Return - All items within time frame AND some items returned
            return HeaderStatus.PARTIAL_RETURN
        else:
            # Rule 1: Active - All items within time frame AND no returns made yet
            return HeaderStatus.ACTIVE
    
    async def calculate_transaction_status(
        self, 
        transaction_id: UUID, 
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive status for a rental transaction.
        
        Args:
            transaction_id: ID of the transaction to evaluate
            as_of_date: Date to calculate status as of (defaults to today)
            
        Returns:
            Dictionary containing header status, line statuses, and metadata
        """
        if not as_of_date:
            as_of_date = date.today()
        
        # Get transaction with lines
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
        
        # Calculate header status
        header_status = await self.calculate_header_status(transaction, as_of_date)
        
        # Calculate line statuses
        line_statuses = []
        for line in transaction.transaction_lines:
            line_status = await self.calculate_line_item_status(line, as_of_date)
            line_statuses.append({
                'line_id': line.id,
                'sku': line.sku,
                'description': line.description,
                'status': line_status.value,
                'quantity': float(line.quantity),
                'returned_quantity': float(line.returned_quantity or 0),
                'rental_start_date': line.rental_start_date.isoformat() if line.rental_start_date else None,
                'rental_end_date': line.rental_end_date.isoformat() if line.rental_end_date else None,
                'days_overdue': (as_of_date - line.rental_end_date).days if line.rental_end_date and line.rental_end_date < as_of_date else 0
            })
        
        # Calculate summary statistics
        total_quantity = sum(line.quantity for line in transaction.transaction_lines)
        total_returned = sum(line.returned_quantity or 0 for line in transaction.transaction_lines)
        return_percentage = (float(total_returned) / float(total_quantity) * 100) if total_quantity > 0 else 0
        
        overdue_lines = [ls for ls in line_statuses if ls['days_overdue'] > 0]
        max_overdue_days = max((ls['days_overdue'] for ls in overdue_lines), default=0)
        
        return {
            'transaction_id': transaction_id,
            'header_status': header_status.value,
            'line_statuses': line_statuses,
            'calculated_as_of': as_of_date.isoformat(),
            'summary': {
                'total_lines': len(line_statuses),
                'total_quantity': float(total_quantity),
                'total_returned_quantity': float(total_returned),
                'return_percentage': round(return_percentage, 2),
                'overdue_lines_count': len(overdue_lines),
                'max_overdue_days': max_overdue_days,
                'expected_return_date': transaction.rental_end_date.isoformat() if transaction.rental_end_date else None
            }
        }
    
    async def find_status_changes_needed(
        self, 
        transaction_ids: Optional[List[UUID]] = None,
        as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all rental transactions that need status updates.
        
        Args:
            transaction_ids: Specific transaction IDs to check (None = check all active rentals)
            as_of_date: Date to calculate status as of (defaults to today)
            
        Returns:
            List of transactions with current vs calculated status differences
        """
        if not as_of_date:
            as_of_date = date.today()
        
        # Build query for rental transactions
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
        
        if transaction_ids:
            query = query.where(TransactionHeader.id.in_(transaction_ids))
        
        result = await self.session.execute(query)
        transactions = result.scalars().all()
        
        changes_needed = []
        
        for transaction in transactions:
            try:
                # Calculate what the status should be
                calculated_status = await self.calculate_header_status(transaction, as_of_date)
                current_status = transaction.current_rental_status
                
                # Check if status change is needed
                if current_status != calculated_status.value:
                    status_data = await self.calculate_transaction_status(transaction.id, as_of_date)
                    
                    changes_needed.append({
                        'transaction_id': transaction.id,
                        'current_status': current_status,
                        'calculated_status': calculated_status.value,
                        'status_data': status_data,
                        'priority': self._get_change_priority(current_status, calculated_status.value),
                        'reason': self._get_change_reason(current_status, calculated_status.value)
                    })
                    
            except Exception as e:
                logger.error(f"Error calculating status for transaction {transaction.id}: {e}")
                continue
        
        # Sort by priority (high priority changes first)
        changes_needed.sort(key=lambda x: x['priority'], reverse=True)
        
        logger.info(f"Found {len(changes_needed)} transactions needing status updates")
        return changes_needed
    
    def _get_change_priority(self, current_status: str, new_status: str) -> int:
        """Get priority for status change (higher number = higher priority)."""
        # High priority: becoming overdue
        if current_status in ['ACTIVE', 'PARTIAL_RETURN'] and new_status in ['LATE', 'LATE_PARTIAL_RETURN']:
            return 10
        
        # Medium priority: return-related changes
        if 'RETURN' in new_status:
            return 5
        
        # Low priority: other changes
        return 1
    
    def _get_change_reason(self, current_status: str, new_status: str) -> str:
        """Get human-readable reason for status change."""
        if current_status in ['ACTIVE', 'PARTIAL_RETURN'] and new_status in ['LATE', 'LATE_PARTIAL_RETURN']:
            return "Items are now past due date"
        elif 'PARTIAL_RETURN' in new_status and 'PARTIAL_RETURN' not in current_status:
            return "Some items have been returned"
        elif new_status == 'RETURNED':
            return "All items have been returned"
        else:
            return f"Status changed from {current_status} to {new_status}"