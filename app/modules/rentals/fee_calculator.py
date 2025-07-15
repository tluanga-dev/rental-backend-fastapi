"""
Fee calculation utilities for rental transactions.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.transactions.models import (
    TransactionHeader, 
    TransactionLine,
    RentalLifecycle
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RentalFeeCalculator:
    """Calculator for rental-related fees."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Default fee configuration (should come from settings or database)
        self.default_late_fee_rate = Decimal('0.05')  # 5% per day
        self.max_late_fee_multiplier = Decimal('3.0')  # Max 3x daily rate
        self.default_damage_rate = Decimal('0.10')  # 10% of item value
        self.default_cleaning_fee = Decimal('25.00')  # $25 default cleaning
    
    async def calculate_late_fees(
        self, 
        transaction_id: UUID,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate late fees for a rental transaction."""
        if not as_of_date:
            as_of_date = date.today()
        
        # Get transaction details
        result = await self.session.execute(
            select(TransactionHeader)
            .where(TransactionHeader.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction or not transaction.rental_end_date:
            return {
                'late_fee_days': 0,
                'late_fee_amount': Decimal('0'),
                'is_overdue': False
            }
        
        # Calculate days overdue
        days_overdue = max(0, (as_of_date - transaction.rental_end_date).days)
        is_overdue = days_overdue > 0
        
        if not is_overdue:
            return {
                'late_fee_days': 0,
                'late_fee_amount': Decimal('0'),
                'is_overdue': False
            }
        
        # Calculate daily rental amount (base for late fee calculation)
        daily_rental_amount = self._calculate_daily_rental_amount(transaction)
        
        # Get late fee rate (could be customer-specific or item-specific)
        late_fee_rate = await self._get_late_fee_rate(transaction_id)
        
        # Calculate late fee
        daily_late_fee = daily_rental_amount * late_fee_rate
        max_late_fee = daily_rental_amount * self.max_late_fee_multiplier
        
        total_late_fee = min(daily_late_fee * days_overdue, max_late_fee)
        
        return {
            'late_fee_days': days_overdue,
            'late_fee_rate': late_fee_rate,
            'daily_rental_amount': daily_rental_amount,
            'daily_late_fee': daily_late_fee,
            'late_fee_amount': total_late_fee,
            'max_late_fee': max_late_fee,
            'is_overdue': True
        }
    
    async def calculate_damage_fees(
        self, 
        transaction_line_id: UUID,
        damage_level: str,
        custom_damage_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Calculate damage fees for a specific item."""
        # Get transaction line details
        result = await self.session.execute(
            select(TransactionLine)
            .where(TransactionLine.id == transaction_line_id)
        )
        line = result.scalar_one_or_none()
        
        if not line:
            return {
                'damage_fee': Decimal('0'),
                'cleaning_fee': Decimal('0'),
                'replacement_cost': Decimal('0'),
                'total_damage_cost': Decimal('0')
            }
        
        # If custom amount provided, use it
        if custom_damage_amount:
            return {
                'damage_fee': custom_damage_amount,
                'cleaning_fee': Decimal('0'),
                'replacement_cost': Decimal('0'),
                'total_damage_cost': custom_damage_amount
            }
        
        # Calculate based on damage level
        item_value = line.unit_price
        damage_fee = Decimal('0')
        cleaning_fee = Decimal('0')
        replacement_cost = Decimal('0')
        
        if damage_level == 'MINOR':
            cleaning_fee = self.default_cleaning_fee
        elif damage_level == 'MODERATE':
            damage_fee = item_value * Decimal('0.25')  # 25% of value
            cleaning_fee = self.default_cleaning_fee
        elif damage_level == 'MAJOR':
            damage_fee = item_value * Decimal('0.50')  # 50% of value
            cleaning_fee = self.default_cleaning_fee * 2
        elif damage_level == 'TOTAL_LOSS':
            replacement_cost = item_value
        
        total_damage_cost = damage_fee + cleaning_fee + replacement_cost
        
        return {
            'damage_level': damage_level,
            'item_value': item_value,
            'damage_fee': damage_fee,
            'cleaning_fee': cleaning_fee,
            'replacement_cost': replacement_cost,
            'total_damage_cost': total_damage_cost
        }
    
    async def calculate_total_rental_fees(
        self, 
        transaction_id: UUID,
        as_of_date: Optional[date] = None,
        include_pending_damage: bool = True
    ) -> Dict[str, Any]:
        """Calculate comprehensive fee breakdown for a rental."""
        if not as_of_date:
            as_of_date = date.today()
        
        # Get transaction and lifecycle
        transaction_result = await self.session.execute(
            select(TransactionHeader)
            .where(TransactionHeader.id == transaction_id)
        )
        transaction = transaction_result.scalar_one_or_none()
        
        lifecycle_result = await self.session.execute(
            select(RentalLifecycle)
            .where(RentalLifecycle.transaction_id == transaction_id)
        )
        lifecycle = lifecycle_result.scalar_one_or_none()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        # Calculate late fees
        late_fee_info = await self.calculate_late_fees(transaction_id, as_of_date)
        
        # Get accumulated fees from lifecycle
        accumulated_late_fees = lifecycle.total_late_fees if lifecycle else Decimal('0')
        accumulated_damage_fees = lifecycle.total_damage_fees if lifecycle else Decimal('0')
        accumulated_other_fees = lifecycle.total_other_fees if lifecycle else Decimal('0')
        
        # Calculate new late fees (not yet charged)
        new_late_fees = max(Decimal('0'), late_fee_info['late_fee_amount'] - accumulated_late_fees)
        
        # Calculate totals
        total_fees = (
            accumulated_late_fees + 
            accumulated_damage_fees + 
            accumulated_other_fees + 
            new_late_fees
        )
        
        # Calculate amounts due considering deposits and advance payments
        deposit_credit = transaction.deposit_amount or Decimal('0') if transaction.deposit_paid else Decimal('0')
        advance_credit = transaction.customer_advance_balance or Decimal('0')
        
        amount_due = max(Decimal('0'), total_fees - deposit_credit - advance_credit)
        refund_due = max(Decimal('0'), deposit_credit + advance_credit - total_fees)
        
        return {
            'transaction_id': transaction_id,
            'calculation_date': as_of_date,
            'base_rental_amount': transaction.total_amount,
            
            # Late fee breakdown
            'late_fee_info': late_fee_info,
            'accumulated_late_fees': accumulated_late_fees,
            'new_late_fees': new_late_fees,
            'total_late_fees': accumulated_late_fees + new_late_fees,
            
            # Other fees
            'accumulated_damage_fees': accumulated_damage_fees,
            'accumulated_other_fees': accumulated_other_fees,
            'total_accumulated_fees': accumulated_late_fees + accumulated_damage_fees + accumulated_other_fees,
            
            # Totals
            'total_fees': total_fees,
            'deposit_credit': deposit_credit,
            'advance_payment_credit': advance_credit,
            'total_credits': deposit_credit + advance_credit,
            'amount_due': amount_due,
            'refund_due': refund_due,
            'net_amount': amount_due - refund_due
        }
    
    async def estimate_extension_cost(
        self,
        transaction_id: UUID,
        new_end_date: date,
        current_end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Estimate cost for extending rental period."""
        # Get transaction
        result = await self.session.execute(
            select(TransactionHeader)
            .where(TransactionHeader.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        original_end_date = current_end_date or transaction.rental_end_date
        if not original_end_date:
            raise ValueError("No end date available for extension calculation")
        
        if new_end_date <= original_end_date:
            raise ValueError("New end date must be after current end date")
        
        # Calculate extension period
        extension_days = (new_end_date - original_end_date).days
        
        # Calculate daily rate
        daily_rate = self._calculate_daily_rental_amount(transaction)
        
        # Calculate extension cost
        extension_cost = daily_rate * extension_days
        
        # Check for extension fees (could be a percentage or flat fee)
        extension_fee_rate = Decimal('0.10')  # 10% fee for extensions
        extension_fee = extension_cost * extension_fee_rate
        
        total_extension_cost = extension_cost + extension_fee
        
        return {
            'original_end_date': original_end_date,
            'new_end_date': new_end_date,
            'extension_days': extension_days,
            'daily_rate': daily_rate,
            'extension_cost': extension_cost,
            'extension_fee_rate': extension_fee_rate,
            'extension_fee': extension_fee,
            'total_extension_cost': total_extension_cost
        }
    
    def _calculate_daily_rental_amount(self, transaction: TransactionHeader) -> Decimal:
        """Calculate daily rental amount from transaction."""
        if not transaction.rental_period or not transaction.rental_period_unit:
            # Fallback: assume total amount is for the entire period
            if transaction.rental_start_date and transaction.rental_end_date:
                total_days = (transaction.rental_end_date - transaction.rental_start_date).days
                return transaction.total_amount / max(1, total_days)
            return transaction.total_amount
        
        # Calculate based on rental period unit
        total_amount = transaction.total_amount
        period = transaction.rental_period
        
        if transaction.rental_period_unit == 'DAY':
            return total_amount / period
        elif transaction.rental_period_unit == 'WEEK':
            return total_amount / (period * 7)
        elif transaction.rental_period_unit == 'MONTH':
            return total_amount / (period * 30)  # Approximate
        elif transaction.rental_period_unit == 'HOUR':
            return total_amount / (period / 24)  # Convert to days
        
        return total_amount
    
    async def _get_late_fee_rate(self, transaction_id: UUID) -> Decimal:
        """Get late fee rate for transaction (could be customer or item specific)."""
        # For now, return default rate
        # In future, could check customer preferences, item categories, etc.
        return self.default_late_fee_rate
    
    async def calculate_partial_return_adjustment(
        self,
        transaction_id: UUID,
        returned_items: list,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate fee adjustments for partial returns."""
        if not as_of_date:
            as_of_date = date.today()
        
        # Get transaction lines
        result = await self.session.execute(
            select(TransactionLine)
            .where(TransactionLine.transaction_id == transaction_id)
        )
        lines = result.scalars().all()
        
        total_original_value = sum(line.quantity * line.unit_price for line in lines)
        total_returned_value = Decimal('0')
        
        # Calculate returned value
        for returned_item in returned_items:
            line_id = returned_item.get('transaction_line_id')
            quantity = Decimal(str(returned_item.get('quantity', 0)))
            
            line = next((l for l in lines if str(l.id) == str(line_id)), None)
            if line:
                returned_value = quantity * line.unit_price
                total_returned_value += returned_value
        
        # Calculate proportional adjustment
        if total_original_value > 0:
            return_percentage = total_returned_value / total_original_value
            remaining_percentage = Decimal('1') - return_percentage
        else:
            return_percentage = Decimal('0')
            remaining_percentage = Decimal('1')
        
        # Get current fee calculation
        fee_info = await self.calculate_total_rental_fees(transaction_id, as_of_date)
        
        # Adjust fees proportionally for remaining items
        adjusted_late_fees = fee_info['new_late_fees'] * remaining_percentage
        
        return {
            'total_original_value': total_original_value,
            'total_returned_value': total_returned_value,
            'return_percentage': return_percentage,
            'remaining_percentage': remaining_percentage,
            'original_late_fees': fee_info['new_late_fees'],
            'adjusted_late_fees': adjusted_late_fees,
            'late_fee_reduction': fee_info['new_late_fees'] - adjusted_late_fees
        }