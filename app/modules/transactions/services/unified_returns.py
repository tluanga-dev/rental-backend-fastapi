"""
Unified return service with factory pattern for handling all return types.
"""
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.models import (
    TransactionHeader, 
    TransactionLine,
    TransactionType,
    TransactionStatus,
    LineItemType
)
from app.modules.transactions.models.metadata import TransactionMetadata
from app.modules.transactions.models.inspections import RentalInspection, PurchaseCreditMemo
from app.modules.transactions.schemas import (
    TransactionHeaderCreate,
    TransactionLineCreate,
    TransactionWithLinesResponse
)
from app.modules.transactions.schemas.returns import (
    ReturnTransactionCreate,
    SaleReturnCreate,
    PurchaseReturnCreate,
    RentalReturnCreate,
    ReturnDetailsResponse,
    ReturnValidationResponse,
    RentalInspectionCreate,
    RentalInspectionResponse,
    PurchaseCreditMemoCreate,
    PurchaseCreditMemoResponse,
    ReturnWorkflowState,
    SaleReturnDetails,
    PurchaseReturnDetails,
    RentalReturnDetails
)
from app.modules.transactions.services.return_processors import (
    ReturnProcessor,
    SaleReturnProcessor,
    PurchaseReturnProcessor,
    RentalReturnProcessor
)
from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.core.logger import logger


class UnifiedReturnService:
    """
    Main service for handling all return types using factory pattern.
    """
    
    def __init__(self, transaction_service, inventory_service, session: AsyncSession):
        self.transaction_service = transaction_service
        self.inventory_service = inventory_service
        self.session = session
        
        # Initialize processors
        self.processors: Dict[str, ReturnProcessor] = {
            "SALE_RETURN": SaleReturnProcessor(transaction_service, inventory_service, session),
            "PURCHASE_RETURN": PurchaseReturnProcessor(transaction_service, inventory_service, session),
            "RENTAL_RETURN": RentalReturnProcessor(transaction_service, inventory_service, session)
        }
    
    def _get_processor(self, return_type: str) -> ReturnProcessor:
        """Get the appropriate processor for return type."""
        processor = self.processors.get(return_type)
        if not processor:
            raise ValueError(f"Unknown return type: {return_type}")
        return processor
    
    async def validate_return(
        self, 
        return_data: Union[SaleReturnCreate, PurchaseReturnCreate, RentalReturnCreate]
    ) -> ReturnValidationResponse:
        """
        Validate a return without creating it.
        
        Args:
            return_data: Return data to validate
            
        Returns:
            Validation response with errors, warnings, and estimates
        """
        try:
            # Get original transaction
            original_txn = await self.transaction_service.get_with_lines(
                return_data.original_transaction_id
            )
            if not original_txn:
                return ReturnValidationResponse(
                    is_valid=False,
                    errors=[f"Original transaction {return_data.original_transaction_id} not found"]
                )
            
            # Get processor
            processor = self._get_processor(return_data.return_type)
            
            # Run validation
            errors = await processor.validate_return(original_txn, return_data)
            
            # Calculate estimated financials if no errors
            estimated_refund = None
            estimated_fees = None
            if not errors:
                financials = await processor.calculate_financials(original_txn, return_data)
                estimated_refund = financials.get('net_refund', Decimal("0"))
                estimated_fees = {
                    k: v for k, v in financials.items() 
                    if k not in ['net_refund', 'subtotal']
                }
            
            # Add warnings (non-blocking issues)
            warnings = []
            if return_data.return_type == "SALE_RETURN":
                days_since_sale = (datetime.now() - original_txn.transaction_date).days
                if days_since_sale > 14:
                    warnings.append(f"Sale is {days_since_sale} days old. Restocking fee may apply.")
            
            return ReturnValidationResponse(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                estimated_refund=estimated_refund,
                estimated_fees=estimated_fees
            )
            
        except Exception as e:
            logger.error(f"Error validating return: {str(e)}")
            return ReturnValidationResponse(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    async def create_return(
        self,
        return_data: Union[SaleReturnCreate, PurchaseReturnCreate, RentalReturnCreate]
    ) -> TransactionWithLinesResponse:
        """
        Create any type of return transaction.
        
        Args:
            return_data: Return data with type-specific properties
            
        Returns:
            Created return transaction with lines
        """
        # Get processor
        processor = self._get_processor(return_data.return_type)
        
        # 1. Get and validate original transaction
        original_txn = await self.transaction_service.get_with_lines(
            return_data.original_transaction_id
        )
        if not original_txn:
            raise NotFoundError(f"Original transaction {return_data.original_transaction_id} not found")
        
        # 2. Run type-specific validation
        errors = await processor.validate_return(original_txn, return_data)
        if errors:
            raise ValidationError("; ".join(errors))
        
        # 3. Calculate financials
        financials = await processor.calculate_financials(original_txn, return_data)
        
        # 4. Create return transaction
        async with self.session.begin():
            # Create header
            return_header = await self._create_return_header(
                original_txn,
                return_data,
                financials
            )
            
            # Create lines
            return_lines = await self._create_return_lines(
                original_txn,
                return_data
            )
            
            # Create the transaction
            return_txn = await self.transaction_service.create_transaction_with_lines(
                return_header,
                return_lines
            )
            
            # Store financial summary in transaction
            return_txn.financial_summary = financials
            
            # 5. Process inventory changes
            await processor.process_inventory(return_txn, return_data)
            
            # 6. Update original transaction
            await self._update_original_transaction(
                original_txn,
                return_data,
                return_txn
            )
            
            # 7. Run type-specific post-processing
            await processor.post_process(return_txn, return_data)
            
            # 8. Store type-specific metadata
            await self._store_return_metadata(return_txn, return_data)
            
            # 9. Set initial workflow state
            return_txn.return_workflow_state = ReturnWorkflowState.INITIATED
            
            await self.session.commit()
            
            # Log return creation
            logger.info(
                f"Created {return_data.return_type} transaction {return_txn.transaction_number} "
                f"for original transaction {original_txn.transaction_number}"
            )
        
        return TransactionWithLinesResponse.model_validate(return_txn)
    
    async def _create_return_header(
        self,
        original_txn: TransactionHeader,
        return_data: ReturnTransactionCreate,
        financials: Dict[str, Decimal]
    ) -> TransactionHeaderCreate:
        """Create return transaction header."""
        # Generate return number
        return_number = await self._generate_return_number(return_data.return_type)
        
        # Calculate return amounts (negative for returns)
        subtotal = -abs(financials.get('subtotal', Decimal("0")))
        fees = sum(
            v for k, v in financials.items() 
            if 'fee' in k.lower() and k != 'net_refund'
        )
        
        return TransactionHeaderCreate(
            transaction_number=return_number,
            transaction_type=TransactionType.RETURN,
            transaction_date=return_data.return_date,
            customer_id=original_txn.customer_id,
            location_id=original_txn.location_id,
            sales_person_id=return_data.processed_by,
            status=TransactionStatus.PENDING,
            reference_transaction_id=original_txn.id,
            notes=f"{return_data.return_type}: {return_data.return_reason_code} - {return_data.return_reason_notes or ''}",
            subtotal=subtotal,
            discount_amount=Decimal("0"),
            tax_amount=Decimal("0"),  # Returns typically don't have tax
            total_amount=subtotal + fees
        )
    
    async def _create_return_lines(
        self,
        original_txn: TransactionHeader,
        return_data: ReturnTransactionCreate
    ) -> List[TransactionLineCreate]:
        """Create return transaction lines."""
        return_lines = []
        
        for idx, item in enumerate(return_data.return_items):
            # Find original line
            original_line = next(
                (line for line in original_txn.transaction_lines 
                 if str(line.id) == str(item.original_line_id)),
                None
            )
            
            if not original_line:
                continue
            
            # Create return line with negative quantity
            return_line = TransactionLineCreate(
                line_number=idx + 1,
                line_type=original_line.line_type,
                item_id=original_line.item_id,
                inventory_unit_id=original_line.inventory_unit_id,
                description=f"RETURN: {original_line.description}",
                quantity=-abs(item.return_quantity),  # Negative for returns
                unit_price=original_line.unit_price,
                discount_percentage=Decimal("0"),
                discount_amount=Decimal("0"),
                tax_rate=original_line.tax_rate,
                notes=item.return_reason
            )
            
            # Add return-specific fields based on type
            if hasattr(item, 'condition'):
                return_line.return_condition = item.condition
            if hasattr(item, 'return_to_stock'):
                return_line.return_to_stock = item.return_to_stock
            
            return_lines.append(return_line)
        
        return return_lines
    
    async def _update_original_transaction(
        self,
        original_txn: TransactionHeader,
        return_data: ReturnTransactionCreate,
        return_txn: TransactionHeader
    ) -> None:
        """Update original transaction with return information."""
        # Update returned quantities on original lines
        for item in return_data.return_items:
            original_line = next(
                (line for line in original_txn.transaction_lines 
                 if str(line.id) == str(item.original_line_id)),
                None
            )
            
            if original_line:
                original_line.returned_quantity = (
                    (original_line.returned_quantity or Decimal("0")) + 
                    item.return_quantity
                )
                original_line.return_date = return_data.return_date.date()
        
        # Add return reference to notes
        return_note = f"\n[RETURN: {return_txn.transaction_number} on {return_data.return_date.date()}]"
        original_txn.notes = (original_txn.notes or "") + return_note
        
        # Update status if fully returned
        all_returned = all(
            line.returned_quantity >= line.quantity 
            for line in original_txn.transaction_lines
        )
        if all_returned and original_txn.transaction_type == TransactionType.SALE:
            original_txn.status = TransactionStatus.REFUNDED
    
    async def _store_return_metadata(
        self,
        return_txn: TransactionHeader,
        return_data: Union[SaleReturnCreate, PurchaseReturnCreate, RentalReturnCreate]
    ) -> None:
        """Store type-specific return data in metadata table."""
        # Convert return data to dict, excluding base fields and items
        metadata_content = return_data.dict(
            exclude={
                "original_transaction_id", 
                "return_date", 
                "return_reason_code",
                "return_reason_notes",
                "processed_by",
                "return_items"
            }
        )
        
        # Add return type to metadata
        metadata_content['return_type'] = return_data.return_type
        
        # Create metadata entry
        metadata = TransactionMetadata(
            transaction_id=str(return_txn.id),
            metadata_type=f"RETURN_{return_data.return_type}",
            metadata_content=metadata_content
        )
        
        self.session.add(metadata)
    
    async def get_return_details(self, return_id: UUID) -> ReturnDetailsResponse:
        """
        Get comprehensive return details including type-specific metadata.
        
        Args:
            return_id: Return transaction ID
            
        Returns:
            Return details with type-specific information
        """
        # Get transaction with lines
        return_txn = await self.transaction_service.get_with_lines(return_id)
        if not return_txn:
            raise NotFoundError(f"Return transaction {return_id} not found")
        
        if return_txn.transaction_type != TransactionType.RETURN:
            raise ValidationError(f"Transaction {return_id} is not a return")
        
        # Get metadata
        metadata_entry = await self._get_transaction_metadata(return_id)
        if not metadata_entry:
            raise NotFoundError(f"Return metadata for {return_id} not found")
        
        # Build type-specific details
        return_type = metadata_entry.metadata_content.get('return_type')
        
        if return_type == 'SALE_RETURN':
            specific_details = SaleReturnDetails(**metadata_entry.metadata_content)
        elif return_type == 'PURCHASE_RETURN':
            specific_details = PurchaseReturnDetails(**metadata_entry.metadata_content)
        elif return_type == 'RENTAL_RETURN':
            specific_details = RentalReturnDetails(**metadata_entry.metadata_content)
        else:
            raise ValueError(f"Unknown return type: {return_type}")
        
        # Build return lines with metadata
        return_lines = []
        for line in return_txn.transaction_lines:
            line_dict = {
                'id': line.id,
                'line_number': line.line_number,
                'item_id': line.item_id,
                'description': line.description,
                'quantity': abs(line.quantity),  # Show positive
                'unit_price': line.unit_price,
                'line_total': abs(line.line_total),
                'return_condition': line.return_condition,
                'return_to_stock': line.return_to_stock,
                'inspection_status': line.inspection_status,
                'notes': line.notes
            }
            return_lines.append(line_dict)
        
        return ReturnDetailsResponse(
            id=return_txn.id,
            transaction_number=return_txn.transaction_number,
            return_type=return_type,
            original_transaction_id=return_txn.reference_transaction_id,
            return_date=return_txn.transaction_date,
            status=return_txn.status,
            financial_summary=return_txn.financial_summary or {},
            specific_details=specific_details,
            return_lines=return_lines,
            created_at=return_txn.created_at,
            updated_at=return_txn.updated_at
        )
    
    async def update_return_status(
        self,
        return_id: UUID,
        new_status: str,
        notes: Optional[str] = None,
        updated_by: Optional[UUID] = None
    ) -> TransactionHeader:
        """
        Update return status with workflow validation.
        
        Args:
            return_id: Return transaction ID
            new_status: New workflow status
            notes: Optional status update notes
            updated_by: User making the update
            
        Returns:
            Updated transaction
        """
        # Get return transaction
        return_txn = await self.transaction_service.get_by_id(return_id)
        if not return_txn or return_txn.transaction_type != TransactionType.RETURN:
            raise NotFoundError(f"Return transaction {return_id} not found")
        
        # Update workflow state
        old_state = return_txn.return_workflow_state
        return_txn.return_workflow_state = new_status
        
        # Add status note
        if notes:
            status_note = f"\n[STATUS: {old_state} → {new_status}] {notes}"
            return_txn.notes = (return_txn.notes or "") + status_note
        
        # Update transaction status based on workflow state
        if new_status == ReturnWorkflowState.COMPLETED:
            return_txn.status = TransactionStatus.COMPLETED
        elif new_status == ReturnWorkflowState.CANCELLED:
            return_txn.status = TransactionStatus.CANCELLED
        
        await self.session.commit()
        
        logger.info(
            f"Updated return {return_txn.transaction_number} status: "
            f"{old_state} → {new_status}"
        )
        
        return return_txn
    
    async def _get_transaction_metadata(self, transaction_id: UUID) -> Optional[TransactionMetadata]:
        """Get transaction metadata."""
        result = await self.session.execute(
            select(TransactionMetadata).where(
                TransactionMetadata.transaction_id == str(transaction_id),
                TransactionMetadata.metadata_type.like("RETURN_%")
            )
        )
        return result.scalar_one_or_none()
    
    async def _generate_return_number(self, return_type: str) -> str:
        """Generate unique return number."""
        prefix_map = {
            "SALE_RETURN": "SR",
            "PURCHASE_RETURN": "PR", 
            "RENTAL_RETURN": "RR"
        }
        
        prefix = prefix_map.get(return_type, "RET")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        return f"{prefix}-{timestamp}"
    
    # Inspection workflow methods
    
    async def create_rental_inspection(self, inspection_data: RentalInspectionCreate) -> RentalInspectionResponse:
        """
        Create rental return inspection record.
        
        Args:
            inspection_data: Inspection details
            
        Returns:
            Created inspection record
        """
        # Validate return exists and is rental type
        return_txn = await self.transaction_service.get_by_id(inspection_data.return_id)
        if not return_txn:
            raise NotFoundError(f"Return transaction {inspection_data.return_id} not found")
        
        # Get metadata to verify it's a rental return
        metadata_entry = await self._get_transaction_metadata(inspection_data.return_id)
        if not metadata_entry or metadata_entry.metadata_content.get('return_type') != 'RENTAL_RETURN':
            raise ValidationError("Inspection can only be created for rental returns")
        
        # Check if inspection already exists
        existing_inspection = await self.session.execute(
            select(RentalInspection).where(
                RentalInspection.return_id == str(inspection_data.return_id)
            )
        )
        if existing_inspection.scalar_one_or_none():
            raise ConflictError("Inspection already exists for this return")
        
        # Calculate financial summary from line inspections
        total_repair_cost = sum(
            item.repair_cost_estimate or Decimal("0") 
            for item in inspection_data.line_inspections
        )
        total_cleaning_cost = sum(
            item.cleaning_cost_estimate or Decimal("0")
            for item in inspection_data.line_inspections  
        )
        total_deductions = total_repair_cost + total_cleaning_cost
        
        # Calculate deposit refund
        original_deposit = metadata_entry.metadata_content.get('deposit_amount', Decimal("0"))
        deposit_refund_amount = max(Decimal("0"), Decimal(str(original_deposit)) - total_deductions)
        
        # Create inspection record
        inspection = RentalInspection(
            return_id=inspection_data.return_id,
            inspector_id=inspection_data.inspector_id,
            inspection_date=inspection_data.inspection_date,
            overall_condition=inspection_data.overall_condition,
            inspection_passed=inspection_data.inspection_passed,
            total_repair_cost=total_repair_cost,
            total_cleaning_cost=total_cleaning_cost,
            total_deductions=total_deductions,
            deposit_refund_amount=deposit_refund_amount,
            general_notes=inspection_data.general_notes,
            customer_notification_required=inspection_data.customer_notification_required,
            follow_up_actions=inspection_data.follow_up_actions,
            line_inspections=[item.model_dump() for item in inspection_data.line_inspections]
        )
        
        self.session.add(inspection)
        
        # Update return workflow state
        return_txn.return_workflow_state = ReturnWorkflowState.INSPECTION_COMPLETE
        
        # Update inventory units based on inspection results
        for line_inspection in inspection_data.line_inspections:
            if line_inspection.inventory_unit_id:
                await self._update_unit_after_inspection(line_inspection)
        
        await self.session.commit()
        
        logger.info(
            f"Created rental inspection for return {return_txn.transaction_number} "
            f"by inspector {inspection_data.inspector_id}"
        )
        
        return RentalInspectionResponse.model_validate(inspection)
    
    async def get_rental_inspection(self, return_id: UUID) -> Optional[RentalInspectionResponse]:
        """Get rental inspection for a return."""
        result = await self.session.execute(
            select(RentalInspection).where(
                RentalInspection.return_id == str(return_id)
            )
        )
        inspection = result.scalar_one_or_none()
        
        if inspection:
            return RentalInspectionResponse.model_validate(inspection)
        return None
    
    async def _update_unit_after_inspection(self, line_inspection) -> None:
        """Update inventory unit status based on inspection results."""
        if not line_inspection.inventory_unit_id:
            return
        
        # Determine new status based on inspection
        if line_inspection.recommended_action == "RETURN_TO_STOCK":
            if line_inspection.condition_rating in ["EXCELLENT", "GOOD"]:
                new_status = "AVAILABLE"
            else:
                new_status = "AVAILABLE_USED"
        elif line_inspection.recommended_action == "REPAIR_FIRST":
            new_status = "REQUIRES_REPAIR"
        elif line_inspection.recommended_action == "DEEP_CLEANING":
            new_status = "REQUIRES_CLEANING"
        elif line_inspection.recommended_action == "DISPOSAL":
            new_status = "DISPOSED"
        else:
            new_status = "REQUIRES_INSPECTION"
        
        # Update unit status
        await self.inventory_service.update_inventory_unit_status(
            unit_id=line_inspection.inventory_unit_id,
            status=new_status,
            condition=line_inspection.condition_rating,
            notes=f"Post-rental inspection: {line_inspection.inspector_notes}"
        )
    
    # Purchase credit memo methods
    
    async def create_purchase_credit_memo(self, credit_data: PurchaseCreditMemoCreate) -> PurchaseCreditMemoResponse:
        """
        Record supplier credit memo for purchase return.
        
        Args:
            credit_data: Credit memo details
            
        Returns:
            Created credit memo record
        """
        # Validate return exists and is purchase type
        return_txn = await self.transaction_service.get_by_id(credit_data.return_id)
        if not return_txn:
            raise NotFoundError(f"Return transaction {credit_data.return_id} not found")
        
        # Get metadata to verify it's a purchase return
        metadata_entry = await self._get_transaction_metadata(credit_data.return_id)
        if not metadata_entry or metadata_entry.metadata_content.get('return_type') != 'PURCHASE_RETURN':
            raise ValidationError("Credit memo can only be created for purchase returns")
        
        # Check if credit memo already exists
        existing_memo = await self.session.execute(
            select(PurchaseCreditMemo).where(
                PurchaseCreditMemo.return_id == str(credit_data.return_id)
            )
        )
        if existing_memo.scalar_one_or_none():
            raise ConflictError("Credit memo already exists for this return")
        
        # Create credit memo record
        credit_memo = PurchaseCreditMemo(
            return_id=credit_data.return_id,
            credit_memo_number=credit_data.credit_memo_number,
            credit_date=credit_data.credit_date,
            credit_amount=credit_data.credit_amount,
            credit_type=credit_data.credit_type,
            currency=credit_data.currency,
            exchange_rate=credit_data.exchange_rate,
            line_credits=credit_data.line_credits,
            credit_terms=credit_data.credit_terms,
            supplier_notes=credit_data.supplier_notes,
            received_by=credit_data.received_by
        )
        
        self.session.add(credit_memo)
        
        # Update return workflow state
        return_txn.return_workflow_state = ReturnWorkflowState.REFUND_PROCESSED
        
        # Update metadata with credit information
        metadata_entry.metadata_content.update({
            'credit_received': True,
            'credit_received_date': credit_data.credit_date.isoformat(),
            'credit_memo_number': credit_data.credit_memo_number,
            'credit_amount': float(credit_data.credit_amount)
        })
        
        await self.session.commit()
        
        logger.info(
            f"Recorded credit memo {credit_data.credit_memo_number} "
            f"for return {return_txn.transaction_number}"
        )
        
        return PurchaseCreditMemoResponse.model_validate(credit_memo)
    
    async def get_purchase_credit_memo(self, return_id: UUID) -> Optional[PurchaseCreditMemoResponse]:
        """Get purchase credit memo for a return."""
        result = await self.session.execute(
            select(PurchaseCreditMemo).where(
                PurchaseCreditMemo.return_id == str(return_id)
            )
        )
        credit_memo = result.scalar_one_or_none()
        
        if credit_memo:
            return PurchaseCreditMemoResponse.model_validate(credit_memo)
        return None


# Import for query
from sqlalchemy import select