"""
Rental Services

Business logic for rental operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transaction_base.services import BaseTransactionService
from app.modules.transaction_base.models import TransactionType, TransactionStatus, RentalStatus
from app.modules.rentals.repository import RentalsRepository, RentalLineRepository, RentalLifecycleRepository
from app.modules.rentals.schemas import (
    RentalCreate,
    RentalUpdate,
    RentalResponse,
    RentalListResponse,
    RentalReportResponse,
    RentalDashboardResponse,
    RentalLifecycleResponse,
    RentalExtensionRequest,
    RentalExtensionResponse,
    RentalCheckoutRequest,
    RentalCheckinRequest,
    RentalStatusUpdateRequest,
    RentalLineUpdate,
    RentalLineResponse,
)


class RentalsService(BaseTransactionService):
    """Service for rental operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.rentals_repository = RentalsRepository(session)
        self.rental_line_repository = RentalLineRepository(session)
        self.rental_lifecycle_repository = RentalLifecycleRepository(session)
    
    async def create_rental(self, rental_data: RentalCreate) -> RentalResponse:
        """Create a new rental."""
        # Validate rental data
        errors = self.validate_rental_data(rental_data)
        if errors:
            raise ValueError(f"Invalid rental data: {', '.join(errors)}")
        
        # Generate transaction number if not provided
        if not hasattr(rental_data, 'transaction_number') or not rental_data.transaction_number:
            transaction_number = self.generate_transaction_number(TransactionType.RENTAL)
        else:
            transaction_number = rental_data.transaction_number
        
        # Generate agreement number if not provided
        agreement_number = rental_data.rental_agreement_number
        if not agreement_number:
            agreement_number = await self.rentals_repository.generate_agreement_number()
        
        # Calculate totals
        totals = self.calculate_transaction_totals(rental_data.transaction_lines)
        
        # Prepare rental data
        rental_dict = rental_data.model_dump(exclude={'transaction_lines'})
        rental_dict.update({
            'transaction_number': transaction_number,
            'rental_agreement_number': agreement_number,
            'transaction_type': TransactionType.RENTAL,
            **totals
        })
        
        # Create rental
        rental = await self.rentals_repository.create_rental(rental_dict)
        
        # Create rental lines
        for line_data in rental_data.transaction_lines:
            line_dict = line_data.model_dump()
            line_dict.update({
                'transaction_id': rental.id,
                'line_total': (line_data.quantity * line_data.unit_price) - line_data.discount_amount + line_data.tax_amount
            })
            await self.rental_line_repository.create_rental_line(line_dict)
        
        # Create rental lifecycle
        lifecycle_data = {
            'transaction_id': rental.id,
            'stage': 'CREATED',
            'current_status': rental_data.rental_status.value
        }
        await self.rental_lifecycle_repository.create_lifecycle(lifecycle_data)
        
        # Refresh and return
        rental = await self.rentals_repository.get_rental_by_id(rental.id)
        return RentalResponse.model_validate(rental)
    
    async def get_rental(self, rental_id: UUID) -> Optional[RentalResponse]:
        """Get rental by ID."""
        rental = await self.rentals_repository.get_rental_by_id(rental_id)
        if not rental:
            return None
        return RentalResponse.model_validate(rental)
    
    async def get_rental_by_agreement_number(self, agreement_number: str) -> Optional[RentalResponse]:
        """Get rental by agreement number."""
        rental = await self.rentals_repository.get_rental_by_agreement_number(agreement_number)
        if not rental:
            return None
        return RentalResponse.model_validate(rental)
    
    async def get_rentals(
        self,
        page: int = 1,
        page_size: int = 100,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[TransactionStatus] = None,
        rental_status: Optional[RentalStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> RentalListResponse:
        """Get rentals with pagination and filters."""
        offset = (page - 1) * page_size
        
        rentals = await self.rentals_repository.get_by_type(
            transaction_type=TransactionType.RENTAL,
            limit=page_size,
            offset=offset,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        total = await self.rentals_repository.count_by_type(
            transaction_type=TransactionType.RENTAL,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        rental_responses = [RentalResponse.model_validate(rental) for rental in rentals]
        total_pages = (total + page_size - 1) // page_size
        
        return RentalListResponse(
            rentals=rental_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_rental(self, rental_id: UUID, update_data: RentalUpdate) -> Optional[RentalResponse]:
        """Update rental."""
        rental = await self.rentals_repository.get_rental_by_id(rental_id)
        if not rental:
            return None
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(rental, field, value)
        
        await self.session.commit()
        
        # Return updated rental
        return await self.get_rental(rental_id)
    
    async def delete_rental(self, rental_id: UUID) -> bool:
        """Delete rental."""
        rental = await self.rentals_repository.get_rental_by_id(rental_id)
        if not rental:
            return False
        
        # Can only delete pending rentals
        if rental.status != TransactionStatus.PENDING:
            raise ValueError("Can only delete pending rentals")
        
        await self.rentals_repository.delete(rental_id)
        return True
    
    async def extend_rental(
        self,
        rental_id: UUID,
        extension_request: RentalExtensionRequest
    ) -> Optional[RentalResponse]:
        """Extend rental period."""
        rental = await self.rentals_repository.get_rental_by_id(rental_id)
        if not rental:
            return None
        
        if not rental.can_extend:
            raise ValueError("Maximum extensions reached")
        
        success = await self.rentals_repository.extend_rental(
            rental_id=rental_id,
            new_end_date=extension_request.new_end_date,
            extension_fee=extension_request.extension_fee
        )
        
        if not success:
            return None
        
        # Update rental status to EXTENDED
        await self.rentals_repository.update_rental_status(
            rental_id=rental_id,
            status=RentalStatus.EXTENDED
        )
        
        return await self.get_rental(rental_id)
    
    async def checkout_rental(
        self,
        rental_id: UUID,
        checkout_request: RentalCheckoutRequest
    ) -> Optional[RentalResponse]:
        """Process rental checkout."""
        rental = await self.rentals_repository.get_rental_by_id(rental_id)
        if not rental:
            return None
        
        # Mark checkout as completed
        await self.rental_lifecycle_repository.complete_checkout(rental_id)
        
        # Update rental status
        await self.rentals_repository.update_rental_status(
            rental_id=rental_id,
            status=RentalStatus.ACTIVE
        )
        
        # Update lifecycle stage
        await self.rental_lifecycle_repository.update_stage(
            rental_id=rental_id,
            new_stage='CHECKED_OUT'
        )
        
        return await self.get_rental(rental_id)
    
    async def checkin_rental(
        self,
        rental_id: UUID,
        checkin_request: RentalCheckinRequest
    ) -> Optional[RentalResponse]:
        """Process rental checkin."""
        rental = await self.rentals_repository.get_rental_by_id(rental_id)
        if not rental:
            return None
        
        # Mark checkin as completed
        await self.rental_lifecycle_repository.complete_checkin(rental_id)
        
        # Update rental status and return date
        await self.rentals_repository.update_rental_status(
            rental_id=rental_id,
            status=RentalStatus.COMPLETED,
            return_date=checkin_request.return_date
        )
        
        # Update lifecycle stage
        await self.rental_lifecycle_repository.update_stage(
            rental_id=rental_id,
            new_stage='CHECKED_IN'
        )
        
        # Process damage reports
        for damage_report in checkin_request.damage_reports:
            await self.rental_line_repository.update_item_condition(
                line_id=damage_report["line_id"],
                condition_in=damage_report.get("condition", "D"),
                damage_reported=True,
                damage_description=damage_report.get("damage_description"),
                damage_cost=damage_report.get("damage_cost", Decimal("0"))
            )
        
        return await self.get_rental(rental_id)
    
    async def update_rental_status(
        self,
        rental_id: UUID,
        status_update: RentalStatusUpdateRequest
    ) -> Optional[RentalResponse]:
        """Update rental status."""
        success = await self.rentals_repository.update_rental_status(
            rental_id=rental_id,
            status=status_update.new_status
        )
        
        if not success:
            return None
        
        return await self.get_rental(rental_id)
    
    async def get_active_rentals(
        self,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RentalResponse]:
        """Get active rentals."""
        rentals = await self.rentals_repository.get_active_rentals(
            customer_id=customer_id,
            location_id=location_id,
            limit=limit
        )
        
        return [RentalResponse.model_validate(rental) for rental in rentals]
    
    async def get_overdue_rentals(
        self,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RentalResponse]:
        """Get overdue rentals."""
        rentals = await self.rentals_repository.get_overdue_rentals(
            customer_id=customer_id,
            location_id=location_id,
            limit=limit
        )
        
        return [RentalResponse.model_validate(rental) for rental in rentals]
    
    async def get_rentals_due_today(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RentalResponse]:
        """Get rentals due today."""
        rentals = await self.rentals_repository.get_rentals_due_today(
            location_id=location_id,
            limit=limit
        )
        
        return [RentalResponse.model_validate(rental) for rental in rentals]
    
    async def get_rentals_due_this_week(
        self,
        location_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RentalResponse]:
        """Get rentals due this week."""
        rentals = await self.rentals_repository.get_rentals_due_this_week(
            location_id=location_id,
            limit=limit
        )
        
        return [RentalResponse.model_validate(rental) for rental in rentals]
    
    async def get_customer_rentals(
        self,
        customer_id: str,
        status: Optional[RentalStatus] = None,
        page: int = 1,
        page_size: int = 100
    ) -> RentalListResponse:
        """Get rentals for a specific customer."""
        offset = (page - 1) * page_size
        
        rentals = await self.rentals_repository.get_customer_rentals(
            customer_id=customer_id,
            status=status,
            limit=page_size,
            offset=offset
        )
        
        total = len(rentals)  # Simplified for now
        rental_responses = [RentalResponse.model_validate(rental) for rental in rentals]
        total_pages = (total + page_size - 1) // page_size
        
        return RentalListResponse(
            rentals=rental_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def get_rental_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        rental_status: Optional[RentalStatus] = None
    ) -> RentalReportResponse:
        """Generate rental report."""
        summary = await self.rentals_repository.get_rental_summary(
            date_from=date_from,
            date_to=date_to,
            customer_id=customer_id,
            location_id=location_id
        )
        
        # Get detailed rentals for the report
        rentals = await self.rentals_repository.get_by_type(
            transaction_type=TransactionType.RENTAL,
            customer_id=customer_id,
            location_id=location_id,
            date_from=date_from,
            date_to=date_to,
            limit=1000  # Limit for performance
        )
        
        rental_responses = [RentalResponse.model_validate(rental) for rental in rentals]
        
        # Calculate additional metrics
        total_damage_costs = sum(rental.total_damage_cost for rental in rental_responses)
        total_late_fees = sum(rental.total_late_fees for rental in rental_responses)
        on_time_returns = sum(1 for rental in rental_responses if rental.is_completed and not rental.is_overdue)
        late_returns = sum(1 for rental in rental_responses if rental.is_completed and rental.is_overdue)
        damage_incidents = sum(1 for rental in rental_responses if rental.has_damage)
        
        return RentalReportResponse(
            period_start=date_from,
            period_end=date_to,
            total_rentals=summary["total_rentals"],
            total_revenue=summary["total_revenue"],
            total_damage_costs=total_damage_costs,
            total_late_fees=summary["total_late_fees"],
            average_rental_amount=summary["average_rental"],
            average_rental_duration=summary["average_duration"],
            active_rentals=summary["active_rentals"],
            overdue_rentals=summary["overdue_rentals"],
            completed_rentals=summary["completed_rentals"],
            extended_rentals=summary["extended_rentals"],
            on_time_returns=on_time_returns,
            late_returns=late_returns,
            damage_incidents=damage_incidents,
            rentals=rental_responses
        )
    
    async def get_rental_dashboard(
        self,
        location_id: Optional[str] = None
    ) -> RentalDashboardResponse:
        """Get rental dashboard data."""
        # Get counts
        active_rentals = await self.rentals_repository.get_active_rentals(
            location_id=location_id,
            limit=1000
        )
        overdue_rentals = await self.rentals_repository.get_overdue_rentals(
            location_id=location_id,
            limit=1000
        )
        due_today = await self.rentals_repository.get_rentals_due_today(
            location_id=location_id,
            limit=1000
        )
        due_this_week = await self.rentals_repository.get_rentals_due_this_week(
            location_id=location_id,
            limit=1000
        )
        
        # Get recent activities
        recent_rentals = await self.rentals_repository.get_active_rentals(
            location_id=location_id,
            limit=10
        )
        
        return RentalDashboardResponse(
            total_active_rentals=len(active_rentals),
            total_overdue_rentals=len(overdue_rentals),
            total_due_today=len(due_today),
            total_due_this_week=len(due_this_week),
            total_revenue_this_month=Decimal("0"),  # Would need month calculation
            total_outstanding_late_fees=Decimal("0"),  # Would need calculation
            most_rented_items=[],  # Would need item analysis
            top_customers=[],  # Would need customer analysis
            recent_rentals=[RentalResponse.model_validate(rental) for rental in recent_rentals[:5]],
            recent_returns=[]  # Would need return analysis
        )
    
    async def get_rental_lifecycle(self, rental_id: UUID) -> Optional[RentalLifecycleResponse]:
        """Get rental lifecycle information."""
        lifecycle = await self.rental_lifecycle_repository.get_lifecycle_by_rental_id(rental_id)
        if not lifecycle:
            return None
        
        return RentalLifecycleResponse.model_validate(lifecycle)
    
    def validate_rental_data(self, rental_data: RentalCreate) -> List[str]:
        """Validate rental data."""
        errors = []
        
        # Call base validation
        errors.extend(self.validate_transaction_data(rental_data))
        
        # Rental-specific validation
        if rental_data.customer_id is None:
            errors.append("Customer ID is required for rentals")
        
        if rental_data.rental_start_date and rental_data.rental_end_date:
            if rental_data.rental_end_date <= rental_data.rental_start_date:
                errors.append("Rental end date must be after start date")
        
        # Validate line items
        for line in rental_data.transaction_lines:
            if not line.rental_start_date or not line.rental_end_date:
                errors.append(f"Rental dates are required for line {line.line_number}")
            
            if line.rental_start_date and line.rental_end_date:
                if line.rental_end_date <= line.rental_start_date:
                    errors.append(f"Rental end date must be after start date for line {line.line_number}")
        
        return errors