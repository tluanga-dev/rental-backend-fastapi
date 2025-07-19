"""
Rental Returns Service

Business logic for rental return operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.transactions.base.models import (
    TransactionHeader,
    TransactionLine,
    TransactionType,
    TransactionStatus,
    PaymentStatus,
    RentalStatus,
)
from app.modules.transactions.rental_returns.models import RentalInspection, RentalReturnEvent
from app.modules.transactions.base.repository import TransactionHeaderRepository, TransactionLineRepository
from app.modules.transactions.rental_returns.schemas import (
    RentalReturn,
    RentalReturnCreate,
    RentalReturnDetails,
    RentalInspectionCreate,
    RentalInspectionResponse,
    RentalReturnSummary,
    RentalDamageAssessment,
    RentalReturnFees,
)
from app.modules.transactions.rentals.service import RentalsService
from app.modules.customers.repository import CustomerRepository
from app.modules.inventory.repository import ItemRepository, StockLevelRepository
from app.modules.inventory.models import StockLevel, StockMovement, MovementType, ReferenceType
from app.modules.master_data.locations.repository import LocationRepository
from app.core.logger import get_purchase_logger


class RentalReturnsService:
    """Service for rental return operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repository = TransactionHeaderRepository(session)
        self.line_repository = TransactionLineRepository(session)
        self.customer_repository = CustomerRepository(session)
        self.item_repository = ItemRepository(session)
        self.stock_level_repository = StockLevelRepository(session)
        self.location_repository = LocationRepository(session)
        self.rentals_service = RentalsService(session)
        self.logger = get_purchase_logger()

    async def create_rental_return(self, return_data: RentalReturnCreate) -> TransactionHeader:
        """
        Create a comprehensive rental return transaction.
        
        This handles:
        - Creating return transaction
        - Calculating all fees
        - Processing deposit deductions
        - Updating inventory
        - Recording return events
        """
        try:
            # Get original rental transaction
            original_transaction = await self.transaction_repository.get_with_lines(
                return_data.original_transaction_id
            )
            
            if not original_transaction:
                raise NotFoundError(f"Original transaction {return_data.original_transaction_id} not found")
            
            if original_transaction.transaction_type != TransactionType.RENTAL:
                raise ValidationError("Original transaction is not a rental")
            
            # Calculate fees
            fees = self._calculate_return_fees(return_data, original_transaction)
            
            # Create return transaction
            async with self.session.begin():
                # Generate return transaction number
                return_number = await self._generate_return_number("RET")
                
                # Create return transaction header
                return_transaction = TransactionHeader(
                    transaction_number=return_number,
                    transaction_type=TransactionType.RENTAL_RETURN,
                    transaction_date=return_data.return_date,
                    customer_id=original_transaction.customer_id,
                    location_id=original_transaction.location_id,
                    status=TransactionStatus.PENDING,
                    reference_transaction_id=str(original_transaction.id),
                    notes=return_data.return_reason_notes or "",
                    
                    # Financial details
                    subtotal=Decimal("0"),
                    discount_amount=Decimal("0"),
                    tax_amount=Decimal("0"),
                    total_amount=fees.total_fees,
                    deposit_amount=return_data.deposit_amount,
                    deposit_refund_amount=return_data.deposit_refund_amount,
                    
                    # Metadata for rental return specifics
                    metadata={
                        "return_type": "RENTAL_RETURN",
                        "scheduled_return_date": str(return_data.scheduled_return_date),
                        "actual_return_date": str(return_data.actual_return_date),
                        "days_late": (return_data.actual_return_date - return_data.scheduled_return_date).days,
                        "late_fee_amount": str(fees.late_fee),
                        "damage_fee_amount": str(fees.damage_fee),
                        "cleaning_fee_amount": str(fees.cleaning_fee),
                        "deposit_deductions": str(return_data.deposit_deductions),
                        "inspection_required": return_data.damage_assessment_required,
                        "photos_urls": return_data.photo_urls,
                    },
                    
                    is_active=True,
                )
                self.session.add(return_transaction)
                await self.session.flush()
                
                # Process return items
                for idx, item in enumerate(return_data.return_items):
                    # Get original line
                    original_line = next(
                        (line for line in original_transaction.transaction_lines 
                         if str(line.id) == str(item.original_line_id)),
                        None
                    )
                    
                    if not original_line:
                        raise NotFoundError(f"Original line {item.original_line_id} not found")
                    
                    # Create return line
                    return_line = TransactionLine(
                        transaction_id=str(return_transaction.id),
                        line_number=idx + 1,
                        line_type=original_line.line_type,
                        item_id=original_line.item_id,
                        description=f"Return: {original_line.description}",
                        quantity=item.return_quantity,
                        unit_price=original_line.unit_price,
                        line_total=Decimal("0"),  # Returns typically have negative or zero line totals
                        
                        # Return specific fields
                        returned_quantity=item.return_quantity,
                        return_date=return_data.actual_return_date,
                        return_condition=item.condition_on_return[0],  # First letter for code
                        current_rental_status=RentalStatus.COMPLETED,
                        
                        # Metadata for item-specific return details
                        metadata={
                            "condition_on_return": item.condition_on_return,
                            "damage_description": item.damage_description,
                            "damage_photos": item.damage_photos,
                            "cleaning_condition": item.cleaning_condition,
                            "functionality_check": item.functionality_check,
                            "missing_accessories": item.missing_accessories,
                            "estimated_repair_cost": str(item.estimated_repair_cost) if item.estimated_repair_cost else None,
                            "beyond_normal_wear": item.beyond_normal_wear,
                        },
                        
                        is_active=True,
                    )
                    self.session.add(return_line)
                    
                    # Update original line
                    original_line.returned_quantity = (original_line.returned_quantity or Decimal("0")) + item.return_quantity
                    original_line.return_date = return_data.actual_return_date
                    original_line.current_rental_status = RentalStatus.COMPLETED
                    
                    # Update inventory
                    await self._update_inventory_for_return(
                        item_id=UUID(original_line.item_id),
                        location_id=UUID(original_transaction.location_id),
                        quantity=item.return_quantity,
                        condition=item.condition_on_return,
                        transaction_id=return_transaction.id
                    )
                
                # Create return event
                return_event = RentalReturnEvent(
                    rental_id=str(original_transaction.id),
                    return_date=return_data.actual_return_date,
                    days_late=(return_data.actual_return_date - return_data.scheduled_return_date).days,
                    late_fee=fees.late_fee,
                    damage_fee=fees.damage_fee,
                    cleaning_fee=fees.cleaning_fee,
                    total_deductions=fees.total_fees,
                    deposit_refund=return_data.deposit_refund_amount or Decimal("0"),
                    inspection_required=return_data.damage_assessment_required,
                    processed_by=str(return_data.processed_by) if return_data.processed_by else None,
                )
                self.session.add(return_event)
                
                # Update original transaction status
                all_returned = all(
                    line.returned_quantity >= line.quantity 
                    for line in original_transaction.transaction_lines
                )
                
                if all_returned:
                    original_transaction.status = TransactionStatus.COMPLETED
                else:
                    original_transaction.status = TransactionStatus.PARTIAL
            
            # Return the complete transaction
            return await self.transaction_repository.get_with_lines(return_transaction.id)
            
        except Exception as e:
            self.logger.log_debug_info("Error creating rental return", {"error": str(e)})
            await self.session.rollback()
            raise

    async def quick_rental_return(self, rental_id: UUID, return_data: RentalReturn) -> Dict[str, Any]:
        """
        Quick rental return for simple cases.
        
        This is a simplified version that doesn't create a full return transaction.
        """
        try:
            # Get the rental transaction
            transaction = await self.transaction_repository.get_with_lines(rental_id)
            
            if not transaction:
                raise NotFoundError(f"Rental transaction {rental_id} not found")
            
            # Verify it's a rental transaction
            if transaction.transaction_type != TransactionType.RENTAL:
                raise ValidationError(f"Transaction {rental_id} is not a rental")
            
            # Process return for each line
            async with self.session.begin():
                for line in transaction.transaction_lines:
                    if line.returned_quantity < line.quantity:
                        # Update returned quantity
                        line.returned_quantity = line.quantity
                        line.return_date = return_data.actual_return_date
                        line.return_condition = "A"  # Default to good condition
                        line.current_rental_status = RentalStatus.COMPLETED
                        
                        # Update stock levels
                        stock_level = await self.stock_level_repository.get_by_item_location(
                            UUID(line.item_id), UUID(transaction.location_id)
                        )
                        
                        if stock_level:
                            stock_level.available_quantity += line.quantity
                            stock_level.on_rent_quantity -= line.quantity
                            
                            # Create stock movement
                            movement = StockMovement(
                                stock_level_id=stock_level.id,
                                item_id=line.item_id,
                                location_id=transaction.location_id,
                                movement_type=MovementType.RENTAL_RETURN.value,
                                reference_type=ReferenceType.TRANSACTION.value,
                                reference_id=str(transaction.id),
                                quantity_change=line.quantity,
                                quantity_before=stock_level.available_quantity - line.quantity,
                                quantity_after=stock_level.available_quantity,
                                reason=f"Rental return - Transaction {transaction.transaction_number}",
                                notes=return_data.notes or ""
                            )
                            self.session.add(movement)
                
                # Update transaction status
                transaction.status = TransactionStatus.COMPLETED
                
                # Apply any fees
                if return_data.late_fees:
                    transaction.total_amount += return_data.late_fees
                if return_data.damage_fees:
                    transaction.total_amount += return_data.damage_fees
            
            return {
                "success": True,
                "message": "Rental return completed successfully",
                "transaction_id": transaction.id,
                "late_fees": float(return_data.late_fees or 0),
                "damage_fees": float(return_data.damage_fees or 0)
            }
            
        except Exception as e:
            self.logger.log_debug_info("Error completing rental return", {"error": str(e)})
            await self.session.rollback()
            raise

    async def get_rental_return_details(self, return_id: UUID) -> RentalReturnDetails:
        """Get comprehensive rental return details."""
        try:
            # Get return transaction
            return_txn = await self.transaction_repository.get_with_lines(return_id)
            
            if not return_txn or return_txn.transaction_type != TransactionType.RENTAL_RETURN:
                raise NotFoundError(f"Rental return {return_id} not found")
            
            # Get metadata
            metadata = return_txn.metadata or {}
            
            # Check if inspection exists
            inspection = await self.session.execute(
                select(RentalInspection).where(
                    RentalInspection.return_id == str(return_id)
                )
            )
            inspection_result = inspection.scalar_one_or_none()
            
            return RentalReturnDetails(
                scheduled_return_date=date.fromisoformat(metadata.get("scheduled_return_date", str(date.today()))),
                actual_return_date=date.fromisoformat(metadata.get("actual_return_date", str(date.today()))),
                days_late=metadata.get("days_late", 0),
                late_fee_applicable=metadata.get("days_late", 0) > 0,
                late_fee_amount=Decimal(metadata.get("late_fee_amount", "0")),
                damage_assessment_required=metadata.get("inspection_required", False),
                cleaning_required=Decimal(metadata.get("cleaning_fee_amount", "0")) > 0,
                cleaning_fee=Decimal(metadata.get("cleaning_fee_amount", "0")),
                deposit_amount=return_txn.deposit_amount or Decimal("0"),
                deposit_deductions=Decimal(metadata.get("deposit_deductions", "0")),
                deposit_refund_amount=return_txn.deposit_refund_amount or Decimal("0"),
                total_fees=return_txn.total_amount or Decimal("0"),
                inspection_completed=inspection_result is not None,
                inspection_id=UUID(inspection_result.id) if inspection_result else None,
                photos_urls=metadata.get("photos_urls", [])
            )
            
        except Exception as e:
            self.logger.log_debug_info("Error getting rental return details", {"error": str(e)})
            raise

    async def get_rental_return_summary(self, return_id: UUID) -> RentalReturnSummary:
        """Get financial summary of rental return."""
        try:
            # Get return transaction
            return_txn = await self.transaction_repository.get_with_lines(return_id)
            
            if not return_txn or return_txn.transaction_type != TransactionType.RENTAL_RETURN:
                raise NotFoundError(f"Rental return {return_id} not found")
            
            # Get original rental transaction
            original_txn = None
            if return_txn.reference_transaction_id:
                original_txn = await self.transaction_repository.get_by_id(
                    UUID(return_txn.reference_transaction_id)
                )
            
            # Get metadata
            metadata = return_txn.metadata or {}
            
            # Calculate amounts
            late_fees = Decimal(metadata.get("late_fee_amount", "0"))
            damage_fees = Decimal(metadata.get("damage_fee_amount", "0"))
            cleaning_fees = Decimal(metadata.get("cleaning_fee_amount", "0"))
            other_fees = Decimal("0")  # Could include administrative fees, etc.
            
            total_deductions = late_fees + damage_fees + cleaning_fees + other_fees
            deposit_refund = (return_txn.deposit_amount or Decimal("0")) - total_deductions
            
            # Amount due calculation
            amount_due = total_deductions - (return_txn.deposit_amount or Decimal("0"))
            if amount_due < 0:
                amount_due = Decimal("0")
            
            return RentalReturnSummary(
                original_rental_amount=original_txn.total_amount if original_txn else Decimal("0"),
                deposit_amount=return_txn.deposit_amount or Decimal("0"),
                late_fees=late_fees,
                damage_fees=damage_fees,
                cleaning_fees=cleaning_fees,
                other_fees=other_fees,
                total_deductions=total_deductions,
                deposit_refund=max(deposit_refund, Decimal("0")),
                amount_due=amount_due,
                payment_status=return_txn.payment_status.value if return_txn.payment_status else "PENDING"
            )
            
        except Exception as e:
            self.logger.log_debug_info("Error getting rental return summary", {"error": str(e)})
            raise

    async def create_rental_inspection(self, inspection_data: RentalInspectionCreate) -> RentalInspectionResponse:
        """Create rental inspection record."""
        try:
            # Verify return exists
            return_txn = await self.transaction_repository.get_by_id(inspection_data.return_id)
            
            if not return_txn or return_txn.transaction_type != TransactionType.RENTAL_RETURN:
                raise NotFoundError(f"Rental return {inspection_data.return_id} not found")
            
            async with self.session.begin():
                # Create inspection
                inspection = RentalInspection(
                    return_id=str(inspection_data.return_id),
                    inspector_id=str(inspection_data.inspector_id),
                    inspection_date=inspection_data.inspection_date,
                    overall_condition=inspection_data.overall_condition,
                    cleanliness_rating=inspection_data.cleanliness_rating,
                    functionality_rating=inspection_data.functionality_rating,
                    damage_findings=inspection_data.damage_findings,
                    missing_items=inspection_data.missing_items,
                    repair_recommendations=inspection_data.repair_recommendations,
                    estimated_repair_cost=inspection_data.estimated_repair_cost,
                    estimated_cleaning_cost=inspection_data.estimated_cleaning_cost,
                    recommended_deposit_deduction=inspection_data.recommended_deposit_deduction,
                    inspection_photos=inspection_data.inspection_photos,
                    inspection_notes=inspection_data.inspection_notes,
                    customer_signature=inspection_data.customer_signature,
                    customer_disputed=inspection_data.customer_disputed,
                    dispute_notes=inspection_data.dispute_notes,
                )
                self.session.add(inspection)
                await self.session.flush()
                
                # Update return transaction status
                return_txn.status = TransactionStatus.PROCESSING
                
                # Update deposit deductions if recommended
                if inspection_data.recommended_deposit_deduction > 0:
                    deposit_refund = (return_txn.deposit_amount or Decimal("0")) - inspection_data.recommended_deposit_deduction
                    return_txn.deposit_refund_amount = max(deposit_refund, Decimal("0"))
            
            return RentalInspectionResponse.model_validate(inspection)
            
        except Exception as e:
            self.logger.log_debug_info("Error creating rental inspection", {"error": str(e)})
            await self.session.rollback()
            raise

    async def get_rental_inspection(self, return_id: UUID) -> Optional[RentalInspectionResponse]:
        """Get rental inspection for a return."""
        try:
            result = await self.session.execute(
                select(RentalInspection).where(
                    RentalInspection.return_id == str(return_id)
                )
            )
            inspection = result.scalar_one_or_none()
            
            if inspection:
                return RentalInspectionResponse.model_validate(inspection)
            return None
            
        except Exception as e:
            self.logger.log_debug_info("Error getting rental inspection", {"error": str(e)})
            raise

    async def update_rental_inspection(self, inspection_data: RentalInspectionCreate) -> RentalInspectionResponse:
        """Update existing rental inspection."""
        try:
            # Get existing inspection
            result = await self.session.execute(
                select(RentalInspection).where(
                    RentalInspection.return_id == str(inspection_data.return_id)
                )
            )
            inspection = result.scalar_one_or_none()
            
            if not inspection:
                # Create new if doesn't exist
                return await self.create_rental_inspection(inspection_data)
            
            # Update existing
            async with self.session.begin():
                for key, value in inspection_data.model_dump(exclude={'return_id'}).items():
                    setattr(inspection, key, value)
                
                inspection.updated_at = datetime.utcnow()
            
            return RentalInspectionResponse.model_validate(inspection)
            
        except Exception as e:
            self.logger.log_debug_info("Error updating rental inspection", {"error": str(e)})
            await self.session.rollback()
            raise

    async def get_damage_assessments(self, return_id: UUID) -> List[RentalDamageAssessment]:
        """Get damage assessments from return lines."""
        try:
            # Get return transaction with lines
            return_txn = await self.transaction_repository.get_with_lines(return_id)
            
            if not return_txn or return_txn.transaction_type != TransactionType.RENTAL_RETURN:
                raise NotFoundError(f"Rental return {return_id} not found")
            
            assessments = []
            
            for line in return_txn.transaction_lines:
                metadata = line.metadata or {}
                
                # Check if item has damage
                if metadata.get("condition_on_return") in ["POOR", "DAMAGED"]:
                    # Get item details
                    item = await self.item_repository.get_by_id(UUID(line.item_id))
                    
                    if item:
                        # Determine severity
                        severity = "MINOR"
                        if metadata.get("beyond_normal_wear"):
                            severity = "SEVERE"
                        elif metadata.get("functionality_check") == "NOT_WORKING":
                            severity = "MODERATE"
                        
                        # Determine action
                        repair_cost = Decimal(metadata.get("estimated_repair_cost", "0"))
                        replacement_cost = item.unit_cost or Decimal("0")
                        
                        recommended_action = "REPAIR"
                        if repair_cost > replacement_cost * Decimal("0.7"):
                            recommended_action = "REPLACE"
                        elif metadata.get("functionality_check") == "NOT_WORKING" and repair_cost > replacement_cost * Decimal("0.5"):
                            recommended_action = "WRITE_OFF"
                        
                        assessment = RentalDamageAssessment(
                            item_id=UUID(line.item_id),
                            item_name=item.item_name,
                            damage_type=metadata.get("damage_description", "General damage"),
                            severity=severity,
                            repair_cost=repair_cost,
                            replacement_cost=replacement_cost,
                            recommended_action=recommended_action,
                            photos=metadata.get("damage_photos", []),
                            notes=metadata.get("damage_description")
                        )
                        assessments.append(assessment)
            
            return assessments
            
        except Exception as e:
            self.logger.log_debug_info("Error getting damage assessments", {"error": str(e)})
            raise

    async def calculate_rental_return_fees(self, return_id: UUID) -> RentalReturnFees:
        """Calculate detailed fee breakdown for a rental return."""
        try:
            # Get return transaction
            return_txn = await self.transaction_repository.get_with_lines(return_id)
            
            if not return_txn or return_txn.transaction_type != TransactionType.RENTAL_RETURN:
                raise NotFoundError(f"Rental return {return_id} not found")
            
            # Get metadata
            metadata = return_txn.metadata or {}
            
            # Get inspection if exists
            inspection = await self.get_rental_inspection(return_id)
            
            # Calculate fees
            late_fee = Decimal(metadata.get("late_fee_amount", "0"))
            damage_fee = Decimal(metadata.get("damage_fee_amount", "0"))
            cleaning_fee = Decimal(metadata.get("cleaning_fee_amount", "0"))
            
            # Calculate missing item fees
            missing_item_fee = Decimal("0")
            for line in return_txn.transaction_lines:
                line_metadata = line.metadata or {}
                missing_accessories = line_metadata.get("missing_accessories", [])
                if missing_accessories:
                    # Estimate $10 per missing accessory (could be item-specific)
                    missing_item_fee += Decimal(str(len(missing_accessories) * 10))
            
            # Administrative fee (if applicable)
            administrative_fee = Decimal("0")
            if metadata.get("days_late", 0) > 7:
                administrative_fee = Decimal("25")  # Late processing fee
            
            return RentalReturnFees(
                late_fee=late_fee,
                damage_fee=damage_fee,
                cleaning_fee=cleaning_fee,
                missing_item_fee=missing_item_fee,
                administrative_fee=administrative_fee
            )
            
        except Exception as e:
            self.logger.log_debug_info("Error calculating rental return fees", {"error": str(e)})
            raise

    async def approve_deposit_refund(
        self,
        return_id: UUID,
        approved_by: UUID,
        refund_amount: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve deposit refund for rental return."""
        try:
            # Get return transaction
            return_txn = await self.transaction_repository.get_by_id(return_id)
            
            if not return_txn or return_txn.transaction_type != TransactionType.RENTAL_RETURN:
                raise NotFoundError(f"Rental return {return_id} not found")
            
            async with self.session.begin():
                # Update refund amount if provided
                if refund_amount is not None:
                    return_txn.deposit_refund_amount = refund_amount
                
                # Update status
                return_txn.status = TransactionStatus.COMPLETED
                
                # Add approval to metadata
                metadata = return_txn.metadata or {}
                metadata["deposit_approved"] = True
                metadata["deposit_approved_by"] = str(approved_by)
                metadata["deposit_approved_at"] = datetime.utcnow().isoformat()
                if notes:
                    metadata["deposit_approval_notes"] = notes
                return_txn.metadata = metadata
            
            return {
                "success": True,
                "message": "Deposit refund approved",
                "return_id": return_id,
                "refund_amount": float(return_txn.deposit_refund_amount or 0),
                "approved_by": approved_by,
                "approved_at": datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.log_debug_info("Error approving deposit refund", {"error": str(e)})
            await self.session.rollback()
            raise

    async def get_pending_inspections(self, days_old: int = 7) -> List[Dict[str, Any]]:
        """Get rental returns pending inspection."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Query returns without inspections
            stmt = (
                select(TransactionHeader)
                .outerjoin(
                    RentalInspection,
                    RentalInspection.return_id == TransactionHeader.id
                )
                .where(
                    and_(
                        TransactionHeader.transaction_type == TransactionType.RENTAL_RETURN,
                        TransactionHeader.transaction_date <= cutoff_date,
                        TransactionHeader.status != TransactionStatus.COMPLETED,
                        RentalInspection.id.is_(None)
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            returns = result.scalars().all()
            
            pending = []
            for return_txn in returns:
                metadata = return_txn.metadata or {}
                
                pending.append({
                    "return_id": return_txn.id,
                    "transaction_number": return_txn.transaction_number,
                    "return_date": return_txn.transaction_date,
                    "days_pending": (datetime.utcnow() - return_txn.transaction_date).days,
                    "customer_id": return_txn.customer_id,
                    "inspection_required": metadata.get("inspection_required", True),
                    "total_fees": float(return_txn.total_amount or 0)
                })
            
            return pending
            
        except Exception as e:
            self.logger.log_debug_info("Error getting pending inspections", {"error": str(e)})
            raise

    async def get_deposit_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get summary of deposit refunds and deductions."""
        try:
            # Build query
            filters = [TransactionHeader.transaction_type == TransactionType.RENTAL_RETURN]
            
            if date_from:
                filters.append(TransactionHeader.transaction_date >= datetime.combine(date_from, datetime.min.time()))
            if date_to:
                filters.append(TransactionHeader.transaction_date <= datetime.combine(date_to, datetime.max.time()))
            
            stmt = select(TransactionHeader).where(and_(*filters))
            result = await self.session.execute(stmt)
            returns = result.scalars().all()
            
            # Calculate summary
            total_deposits = Decimal("0")
            total_refunds = Decimal("0")
            total_deductions = Decimal("0")
            return_count = len(returns)
            
            deduction_breakdown = {
                "late_fees": Decimal("0"),
                "damage_fees": Decimal("0"),
                "cleaning_fees": Decimal("0"),
                "other_fees": Decimal("0")
            }
            
            for return_txn in returns:
                metadata = return_txn.metadata or {}
                
                deposit = return_txn.deposit_amount or Decimal("0")
                refund = return_txn.deposit_refund_amount or Decimal("0")
                deduction = deposit - refund
                
                total_deposits += deposit
                total_refunds += refund
                total_deductions += deduction
                
                # Breakdown by type
                deduction_breakdown["late_fees"] += Decimal(metadata.get("late_fee_amount", "0"))
                deduction_breakdown["damage_fees"] += Decimal(metadata.get("damage_fee_amount", "0"))
                deduction_breakdown["cleaning_fees"] += Decimal(metadata.get("cleaning_fee_amount", "0"))
            
            deduction_breakdown["other_fees"] = total_deductions - sum(deduction_breakdown.values())
            
            return {
                "period": {
                    "from": date_from,
                    "to": date_to
                },
                "summary": {
                    "total_returns": return_count,
                    "total_deposits_held": float(total_deposits),
                    "total_deposits_refunded": float(total_refunds),
                    "total_deductions": float(total_deductions),
                    "average_deduction": float(total_deductions / return_count) if return_count > 0 else 0,
                    "refund_percentage": float((total_refunds / total_deposits) * 100) if total_deposits > 0 else 0
                },
                "deduction_breakdown": {
                    k: float(v) for k, v in deduction_breakdown.items()
                }
            }
            
        except Exception as e:
            self.logger.log_debug_info("Error getting deposit summary", {"error": str(e)})
            raise

    # Helper methods
    def _calculate_return_fees(self, return_data: RentalReturnCreate, original_transaction: TransactionHeader) -> RentalReturnFees:
        """Calculate all fees for rental return."""
        late_fee = return_data.late_fee_amount or Decimal("0")
        damage_fee = Decimal("0")
        cleaning_fee = return_data.cleaning_fee or Decimal("0")
        missing_item_fee = Decimal("0")
        administrative_fee = Decimal("0")
        
        # Calculate damage fees from items
        for item in return_data.return_items:
            if item.estimated_repair_cost:
                damage_fee += item.estimated_repair_cost
            
            if item.missing_accessories:
                # Estimate fee for missing accessories
                missing_item_fee += Decimal(str(len(item.missing_accessories) * 10))
        
        # Administrative fee for very late returns
        if return_data.late_fee_applicable and (return_data.actual_return_date - return_data.scheduled_return_date).days > 7:
            administrative_fee = Decimal("25")
        
        return RentalReturnFees(
            late_fee=late_fee,
            damage_fee=damage_fee,
            cleaning_fee=cleaning_fee,
            missing_item_fee=missing_item_fee,
            administrative_fee=administrative_fee
        )

    async def _generate_return_number(self, prefix: str) -> str:
        """Generate unique return transaction number."""
        import time
        
        timestamp = int(time.time() * 1000)
        date_str = datetime.utcnow().strftime('%Y%m%d')
        
        # Try timestamp-based number first
        transaction_number = f"{prefix}-{date_str}-{timestamp % 1000000}"
        
        # Check if it exists
        exists = await self.session.execute(
            select(1).where(
                TransactionHeader.transaction_number == transaction_number
            ).limit(1)
        )
        
        if not exists.scalar():
            return transaction_number
        
        # Fallback with counter
        for i in range(1, 100):
            transaction_number = f"{prefix}-{date_str}-{timestamp % 1000000}-{i}"
            exists = await self.session.execute(
                select(1).where(
                    TransactionHeader.transaction_number == transaction_number
                ).limit(1)
            )
            if not exists.scalar():
                return transaction_number
        
        raise ConflictError("Unable to generate unique transaction number")

    async def _update_inventory_for_return(
        self,
        item_id: UUID,
        location_id: UUID,
        quantity: Decimal,
        condition: str,
        transaction_id: UUID
    ):
        """Update inventory when items are returned."""
        # Get stock level
        stock_level = await self.stock_level_repository.get_by_item_location(item_id, location_id)
        
        if not stock_level:
            raise ValidationError(f"No stock level found for item {item_id} at location {location_id}")
        
        # Update quantities based on condition
        if condition in ["EXCELLENT", "GOOD", "FAIR"]:
            # Return to available stock
            stock_level.available_quantity += quantity
            stock_level.on_rent_quantity -= quantity
        else:
            # Damaged items go to damaged quantity
            stock_level.damaged_quantity = (stock_level.damaged_quantity or Decimal("0")) + quantity
            stock_level.on_rent_quantity -= quantity
        
        # Create stock movement
        movement = StockMovement(
            stock_level_id=stock_level.id,
            item_id=str(item_id),
            location_id=str(location_id),
            movement_type=MovementType.RENTAL_RETURN.value,
            reference_type=ReferenceType.TRANSACTION.value,
            reference_id=str(transaction_id),
            quantity_change=quantity,
            quantity_before=stock_level.available_quantity - quantity,
            quantity_after=stock_level.available_quantity,
            reason=f"Rental return - Condition: {condition}",
            notes=f"Return transaction {transaction_id}"
        )
        self.session.add(movement)