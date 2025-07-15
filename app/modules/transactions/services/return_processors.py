"""
Return processors implementing strategy pattern for type-specific return handling.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.models import TransactionHeader, TransactionLine
from app.modules.transactions.schemas.returns import (
    ReturnTransactionCreate,
    SaleReturnCreate,
    PurchaseReturnCreate,
    RentalReturnCreate,
    SaleReturnLineItem,
    PurchaseReturnLineItem,
    RentalReturnLineItem
)
from app.core.errors import ValidationError


class ReturnProcessor(ABC):
    """Abstract base class for return processors."""
    
    def __init__(self, transaction_service, inventory_service, session: AsyncSession):
        self.transaction_service = transaction_service
        self.inventory_service = inventory_service
        self.session = session
    
    @abstractmethod
    async def validate_return(
        self, 
        original_txn: TransactionHeader, 
        return_data: ReturnTransactionCreate
    ) -> List[str]:
        """
        Validate return based on type-specific rules.
        Returns list of validation errors.
        """
        pass
    
    @abstractmethod
    async def process_inventory(
        self, 
        return_txn: TransactionHeader, 
        return_data: ReturnTransactionCreate
    ) -> None:
        """Process inventory changes for the return."""
        pass
    
    @abstractmethod
    async def calculate_financials(
        self, 
        original_txn: TransactionHeader, 
        return_data: ReturnTransactionCreate
    ) -> Dict[str, Decimal]:
        """Calculate refunds, fees, etc."""
        pass
    
    @abstractmethod
    async def post_process(
        self, 
        return_txn: TransactionHeader, 
        return_data: ReturnTransactionCreate
    ) -> None:
        """Any post-processing steps specific to return type."""
        pass
    
    def _find_line(self, transaction: TransactionHeader, line_id: UUID) -> Optional[TransactionLine]:
        """Find a transaction line by ID."""
        return next(
            (line for line in transaction.transaction_lines if str(line.id) == str(line_id)),
            None
        )
    
    async def _validate_common_rules(
        self, 
        original_txn: TransactionHeader, 
        return_data: ReturnTransactionCreate
    ) -> List[str]:
        """Common validation rules for all return types."""
        errors = []
        
        # Check if all return line items reference valid original lines
        for item in return_data.return_items:
            original_line = self._find_line(original_txn, item.original_line_id)
            if not original_line:
                errors.append(f"Original line {item.original_line_id} not found in transaction")
                continue
            
            # Check if quantity is valid
            already_returned = original_line.returned_quantity or Decimal("0")
            if item.return_quantity > (original_line.quantity - already_returned):
                errors.append(
                    f"Cannot return {item.return_quantity} for line {item.original_line_id}. "
                    f"Original: {original_line.quantity}, Already returned: {already_returned}"
                )
        
        return errors


class SaleReturnProcessor(ReturnProcessor):
    """Processes sale returns."""
    
    async def validate_return(
        self, 
        original_txn: TransactionHeader, 
        return_data: SaleReturnCreate
    ) -> List[str]:
        """Validate sale return specific rules."""
        errors = await self._validate_common_rules(original_txn, return_data)
        
        # Check return window (30 days by default)
        days_since_sale = (datetime.now() - original_txn.transaction_date).days
        if days_since_sale > 30:
            errors.append(f"Return period expired. Sale was {days_since_sale} days ago (max: 30)")
        
        # Check if transaction is completed
        if original_txn.status != "COMPLETED":
            errors.append("Can only return completed sales")
        
        # Validate item conditions for refund method
        for item in return_data.return_items:
            if return_data.refund_method == "ORIGINAL_PAYMENT":
                if item.condition == "DAMAGED":
                    errors.append("Damaged items cannot be refunded to original payment")
                if not item.original_packaging:
                    errors.append("Original packaging required for full refund")
        
        # Validate exchange transaction
        if return_data.refund_method == "EXCHANGE" and not return_data.exchange_transaction_id:
            errors.append("Exchange transaction ID required for exchange returns")
        
        return errors
    
    async def process_inventory(
        self, 
        return_txn: TransactionHeader, 
        return_data: SaleReturnCreate
    ) -> None:
        """Add items back to stock based on condition."""
        for idx, item in enumerate(return_data.return_items):
            if not item.return_to_stock:
                continue
            
            line = return_txn.transaction_lines[idx]
            
            # Determine stock status based on condition
            if item.condition in ["NEW", "OPENED"]:
                stock_status = "AVAILABLE"
            elif item.condition == "USED":
                stock_status = "AVAILABLE_USED"
            else:  # DAMAGED
                stock_status = "REQUIRES_INSPECTION"
            
            # Adjust stock level
            await self.inventory_service.adjust_stock_level(
                item_id=line.item_id,
                location_id=return_data.restock_location_id or return_txn.location_id,
                quantity_change=abs(line.quantity),  # Make positive
                transaction_type="SALE_RETURN",
                reference_id=str(return_txn.id),
                notes=f"Sale return - Condition: {item.condition}, Status: {stock_status}"
            )
    
    async def calculate_financials(
        self, 
        original_txn: TransactionHeader, 
        return_data: SaleReturnCreate
    ) -> Dict[str, Decimal]:
        """Calculate refund amount minus any fees."""
        financials = {
            'subtotal': Decimal("0"),
            'restocking_fee': Decimal("0"),
            'shipping_deduction': Decimal("0"),
            'net_refund': Decimal("0")
        }
        
        # Calculate base refund amount
        for item in return_data.return_items:
            original_line = self._find_line(original_txn, item.original_line_id)
            if not original_line:
                continue
            
            # Calculate item refund based on condition
            item_refund = original_line.unit_price * item.return_quantity
            
            # Apply condition-based deductions
            if item.condition == "OPENED":
                item_refund *= Decimal("0.95")  # 5% deduction
            elif item.condition == "USED":
                item_refund *= Decimal("0.80")  # 20% deduction
            elif item.condition == "DAMAGED":
                item_refund *= Decimal("0.50")  # 50% deduction
            
            financials['subtotal'] += item_refund
        
        # Apply restocking fee if not all items have original packaging
        if not all(item.original_packaging for item in return_data.return_items):
            financials['restocking_fee'] = financials['subtotal'] * Decimal("0.15")  # 15% fee
        
        # Return shipping cost
        if return_data.customer_pays_shipping and return_data.return_shipping_cost:
            financials['shipping_deduction'] = return_data.return_shipping_cost
        
        # Calculate net refund
        financials['net_refund'] = (
            financials['subtotal'] - 
            financials['restocking_fee'] - 
            financials['shipping_deduction']
        )
        
        # Store the refund method for reference
        financials['refund_method'] = return_data.refund_method
        
        return financials
    
    async def post_process(
        self, 
        return_txn: TransactionHeader, 
        return_data: SaleReturnCreate
    ) -> None:
        """Handle post-processing for sale returns."""
        # Link exchange transaction if applicable
        if return_data.refund_method == "EXCHANGE" and return_data.exchange_transaction_id:
            # Update the exchange transaction to reference this return
            exchange_txn = await self.transaction_service.get_by_id(
                return_data.exchange_transaction_id
            )
            if exchange_txn:
                exchange_txn.reference_transaction_id = str(return_txn.id)
                await self.session.commit()
        
        # Schedule quality check if required
        if return_data.quality_check_required:
            # This would typically create a task in a task management system
            # For now, we'll just add a note
            return_txn.notes = (return_txn.notes or "") + "\n[QUALITY_CHECK_REQUIRED]"


class PurchaseReturnProcessor(ReturnProcessor):
    """Processes purchase returns to suppliers."""
    
    async def validate_return(
        self, 
        original_txn: TransactionHeader, 
        return_data: PurchaseReturnCreate
    ) -> List[str]:
        """Validate purchase return specific rules."""
        errors = await self._validate_common_rules(original_txn, return_data)
        
        # RMA number is usually required
        if not return_data.supplier_rma_number:
            errors.append("Supplier RMA number is required for purchase returns")
        
        # Check if transaction type is purchase
        if original_txn.transaction_type != "PURCHASE":
            errors.append("Can only create purchase returns for purchase transactions")
        
        # Validate quality claim consistency
        if return_data.quality_claim:
            has_supplier_fault = any(item.supplier_fault for item in return_data.return_items)
            if not has_supplier_fault:
                errors.append("Quality claim requires at least one item marked as supplier fault")
        
        # Check return authorization date
        if return_data.return_authorization_date:
            if return_data.return_authorization_date > date.today():
                errors.append("Return authorization date cannot be in the future")
        
        return errors
    
    async def process_inventory(
        self, 
        return_txn: TransactionHeader, 
        return_data: PurchaseReturnCreate
    ) -> None:
        """Remove items from stock for supplier return."""
        for idx, item in enumerate(return_data.return_items):
            line = return_txn.transaction_lines[idx]
            
            # Remove from stock (negative adjustment)
            await self.inventory_service.adjust_stock_level(
                item_id=line.item_id,
                location_id=return_txn.location_id,
                quantity_change=-abs(line.quantity),  # Make negative
                transaction_type="PURCHASE_RETURN",
                reference_id=str(return_txn.id),
                notes=f"Purchase return to supplier - RMA: {return_data.supplier_rma_number}"
            )
            
            # If defective, might need to track separately
            if item.supplier_fault:
                # Could create a defective inventory record
                pass
    
    async def calculate_financials(
        self, 
        original_txn: TransactionHeader, 
        return_data: PurchaseReturnCreate
    ) -> Dict[str, Decimal]:
        """Calculate expected credit from supplier."""
        financials = {
            'return_value': Decimal("0"),
            'supplier_restocking_fee': Decimal("0"),
            'expected_credit': Decimal("0"),
            'shipping_cost': Decimal("0")
        }
        
        # Calculate return value
        for item in return_data.return_items:
            original_line = self._find_line(original_txn, item.original_line_id)
            if not original_line:
                continue
            
            # Use purchase price (unit_price for purchases is cost)
            item_value = original_line.unit_price * item.return_quantity
            financials['return_value'] += item_value
        
        # Apply supplier restocking fee if specified
        if return_data.supplier_restocking_fee_percent:
            fee_rate = return_data.supplier_restocking_fee_percent / 100
            financials['supplier_restocking_fee'] = financials['return_value'] * fee_rate
        
        # Calculate expected credit
        financials['expected_credit'] = (
            financials['return_value'] - 
            financials['supplier_restocking_fee']
        )
        
        # Note shipping cost if tracked
        if return_data.return_shipping_cost:
            financials['shipping_cost'] = return_data.return_shipping_cost
        
        return financials
    
    async def post_process(
        self, 
        return_txn: TransactionHeader, 
        return_data: PurchaseReturnCreate
    ) -> None:
        """Handle post-processing for purchase returns."""
        # Create expected credit tracking
        if return_data.supplier_credit_expected and return_data.expected_credit_date:
            # This would typically create an accounts payable credit expectation
            # For now, we'll add metadata
            return_txn.notes = (return_txn.notes or "") + (
                f"\n[EXPECTED_CREDIT: {return_data.expected_credit_date}]"
            )
        
        # Track quality claims
        if return_data.quality_claim:
            return_txn.notes = (return_txn.notes or "") + "\n[QUALITY_CLAIM]"


class RentalReturnProcessor(ReturnProcessor):
    """Processes rental returns with inspection workflow."""
    
    async def validate_return(
        self, 
        original_txn: TransactionHeader, 
        return_data: RentalReturnCreate
    ) -> List[str]:
        """Validate rental return specific rules."""
        errors = await self._validate_common_rules(original_txn, return_data)
        
        # Check if transaction is a rental
        if original_txn.transaction_type != "RENTAL":
            errors.append("Can only create rental returns for rental transactions")
        
        # All rental items must be returned
        for line in original_txn.transaction_lines:
            total_being_returned = sum(
                item.return_quantity 
                for item in return_data.return_items 
                if str(item.original_line_id) == str(line.id)
            )
            
            already_returned = line.returned_quantity or Decimal("0")
            if (already_returned + total_being_returned) < line.quantity:
                errors.append(
                    f"All rental items must be returned. "
                    f"Line {line.id} missing {line.quantity - already_returned - total_being_returned} items"
                )
        
        # Validate photos for damaged items
        if return_data.photos_required:
            has_damage = any(
                item.condition_on_return in ["POOR", "DAMAGED"] 
                for item in return_data.return_items
            )
            if has_damage and not return_data.photo_urls:
                errors.append("Photos required for damaged rental returns")
        
        # Validate deposit amount
        if return_data.deposit_amount < 0:
            errors.append("Deposit amount cannot be negative")
        
        return errors
    
    async def process_inventory(
        self, 
        return_txn: TransactionHeader, 
        return_data: RentalReturnCreate
    ) -> None:
        """Update rental inventory status based on condition."""
        for idx, item in enumerate(return_data.return_items):
            line = return_txn.transaction_lines[idx]
            
            # Determine inventory status based on condition
            if item.condition_on_return in ["EXCELLENT", "GOOD"]:
                status = "AVAILABLE"
            elif item.condition_on_return == "FAIR":
                if item.cleaning_condition != "CLEAN":
                    status = "REQUIRES_CLEANING"
                else:
                    status = "AVAILABLE"
            else:  # POOR or DAMAGED
                status = "REQUIRES_INSPECTION"
            
            # Update inventory unit status if tracked by unit
            if line.inventory_unit_id:
                await self.inventory_service.update_inventory_unit_status(
                    unit_id=line.inventory_unit_id,
                    status=status,
                    condition=item.condition_on_return,
                    notes=item.damage_description
                )
            else:
                # Update general stock status
                await self.inventory_service.update_stock_condition(
                    item_id=line.item_id,
                    location_id=return_txn.location_id,
                    quantity=item.return_quantity,
                    condition=item.condition_on_return,
                    status=status
                )
            
            # Move stock from on rent back to available for all returns
            try:
                # Get stock level for this item/location
                stock_level = await self.inventory_service.stock_level_repository.get_by_item_location(
                    line.item_id, return_txn.location_id
                )
                
                if stock_level:
                    from decimal import Decimal
                    # Move quantity from on rent back to available
                    await self.inventory_service.return_from_rent(
                        stock_level_id=stock_level.id,
                        quantity=Decimal(str(item.return_quantity)),
                        transaction_id=str(return_txn.id)
                    )
                    
                    self.logger.log_debug_info("Stock returned from rent", {
                        "item_id": str(line.item_id),
                        "quantity": item.return_quantity,
                        "return_transaction_id": str(return_txn.id),
                        "stock_level_id": str(stock_level.id),
                        "condition": item.condition_on_return
                    })
                else:
                    # Log warning if no stock level found
                    self.logger.log_debug_info("No stock level found for rental return", {
                        "item_id": str(line.item_id),
                        "location_id": str(return_txn.location_id),
                        "quantity": item.return_quantity
                    })
                    
            except Exception as stock_error:
                # Log the error but don't fail the return
                self.logger.log_debug_info("Error updating stock for rental return", {
                    "item_id": str(line.item_id),
                    "error": str(stock_error),
                    "return_transaction_id": str(return_txn.id)
                })
    
    async def calculate_financials(
        self, 
        original_txn: TransactionHeader, 
        return_data: RentalReturnCreate
    ) -> Dict[str, Decimal]:
        """Calculate deposit refund after deductions."""
        financials = {
            'original_deposit': return_data.deposit_amount,
            'late_fee': Decimal("0"),
            'damage_fee': Decimal("0"),
            'cleaning_fee': Decimal("0"),
            'missing_items_fee': Decimal("0"),
            'total_deductions': Decimal("0"),
            'deposit_refund': Decimal("0")
        }
        
        # Calculate late fee if applicable
        if return_data.late_fee_applicable and return_data.late_fee_amount:
            financials['late_fee'] = return_data.late_fee_amount
        elif return_data.actual_return_date > return_data.scheduled_return_date:
            # Auto-calculate late fee
            days_late = (return_data.actual_return_date - return_data.scheduled_return_date).days
            # Use 10% of daily rate as late fee
            daily_rate = original_txn.total_amount / 30  # Rough estimate
            financials['late_fee'] = daily_rate * days_late * Decimal("0.1")
        
        # Calculate damage fees
        for item in return_data.return_items:
            if item.condition_on_return == "DAMAGED":
                if item.estimated_repair_cost:
                    financials['damage_fee'] += item.estimated_repair_cost
                else:
                    # Default damage fee based on severity
                    financials['damage_fee'] += Decimal("200")
            elif item.condition_on_return == "POOR":
                financials['damage_fee'] += Decimal("100")
            
            # Additional fee for beyond normal wear
            if item.beyond_normal_wear:
                financials['damage_fee'] += Decimal("50")
            
            # Missing accessories fee
            if item.missing_accessories:
                financials['missing_items_fee'] += Decimal("25") * len(item.missing_accessories)
        
        # Cleaning fee
        if return_data.cleaning_required and return_data.cleaning_fee:
            financials['cleaning_fee'] = return_data.cleaning_fee
        else:
            # Auto-calculate based on condition
            needs_major_cleaning = any(
                item.cleaning_condition == "MAJOR_CLEANING" 
                for item in return_data.return_items
            )
            needs_minor_cleaning = any(
                item.cleaning_condition == "MINOR_CLEANING" 
                for item in return_data.return_items
            )
            
            if needs_major_cleaning:
                financials['cleaning_fee'] = Decimal("75")
            elif needs_minor_cleaning:
                financials['cleaning_fee'] = Decimal("25")
        
        # Calculate total deductions and deposit refund
        financials['total_deductions'] = (
            financials['late_fee'] +
            financials['damage_fee'] +
            financials['cleaning_fee'] +
            financials['missing_items_fee']
        )
        
        financials['deposit_refund'] = max(
            financials['original_deposit'] - financials['total_deductions'],
            Decimal("0")
        )
        
        return financials
    
    async def post_process(
        self, 
        return_txn: TransactionHeader, 
        return_data: RentalReturnCreate
    ) -> None:
        """Handle post-processing for rental returns."""
        # Create inspection tasks for damaged items
        inspection_required = False
        
        for item in return_data.return_items:
            if item.condition_on_return in ["POOR", "DAMAGED"]:
                inspection_required = True
                # Create inspection task
                priority = "HIGH" if item.functionality_check == "NOT_WORKING" else "MEDIUM"
                
                # Add inspection requirement to notes
                inspection_note = (
                    f"\n[INSPECTION_REQUIRED: {item.condition_on_return}, "
                    f"Priority: {priority}]"
                )
                return_txn.notes = (return_txn.notes or "") + inspection_note
        
        # Handle photo documentation
        if return_data.photo_urls:
            photo_note = f"\n[PHOTOS: {len(return_data.photo_urls)} photos attached]"
            return_txn.notes = (return_txn.notes or "") + photo_note
        
        # Mark if deposit was fully refunded
        deposit_refund = return_txn.financial_summary.get('deposit_refund', Decimal("0"))
        if deposit_refund == return_data.deposit_amount:
            return_txn.notes = (return_txn.notes or "") + "\n[DEPOSIT_FULLY_REFUNDED]"
        elif deposit_refund == 0:
            return_txn.notes = (return_txn.notes or "") + "\n[DEPOSIT_FULLY_RETAINED]"