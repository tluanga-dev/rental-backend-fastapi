from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError, ConflictError
from app.modules.rentals.models import (
    RentalReturn, RentalReturnLine, InspectionReport,
    ReturnStatus, DamageLevel, ReturnType, InspectionStatus, ReturnLineStatus
)
from app.modules.rentals.repository import (
    RentalReturnRepository, RentalReturnLineRepository, InspectionReportRepository
)
from app.modules.rentals.schemas import (
    RentalReturnCreate, RentalReturnUpdate, RentalReturnResponse,
    RentalReturnListResponse, RentalReturnWithLinesResponse,
    RentalReturnLineCreate, RentalReturnLineUpdate, RentalReturnLineResponse,
    InspectionReportCreate, InspectionReportUpdate, InspectionReportResponse,
    ReturnStatusUpdate, LineStatusUpdate, DamageAssessment, FeeCalculation,
    DepositCalculation, InspectionCompletion, InspectionFailure,
    RentalReturnSummary, RentalReturnReport, RentalReturnSearch,
    RentalDashboard, RentalAnalytics
)
from app.modules.transactions.repository import TransactionHeaderRepository
from app.modules.inventory.repository import InventoryUnitRepository


class RentalService:
    """Service for rental operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.return_repository = RentalReturnRepository(session)
        self.line_repository = RentalReturnLineRepository(session)
        self.inspection_repository = InspectionReportRepository(session)
        self.transaction_repository = TransactionHeaderRepository(session)
        self.inventory_unit_repository = InventoryUnitRepository(session)
    
    # Rental Return operations
    async def create_rental_return(self, return_data: RentalReturnCreate) -> RentalReturnResponse:
        """Create a new rental return."""
        # Verify rental transaction exists
        transaction = await self.transaction_repository.get_by_id(return_data.rental_transaction_id)
        if not transaction:
            raise NotFoundError(f"Rental transaction with ID {return_data.rental_transaction_id} not found")
        
        # Verify it's a rental transaction
        if not transaction.is_rental():
            raise ValidationError("Transaction is not a rental transaction")
        
        # Check if return already exists for this transaction
        existing_returns = await self.return_repository.get_by_transaction(return_data.rental_transaction_id)
        if existing_returns:
            active_returns = [r for r in existing_returns if r.return_status not in [ReturnStatus.COMPLETED.value, ReturnStatus.CANCELLED.value]]
            if active_returns:
                raise ConflictError("Active return already exists for this rental transaction")
        
        # Create rental return
        rental_return = await self.return_repository.create(return_data)
        return RentalReturnResponse.model_validate(rental_return)
    
    async def get_rental_return(self, return_id: UUID) -> RentalReturnResponse:
        """Get rental return by ID."""
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        return RentalReturnResponse.model_validate(rental_return)
    
    async def get_rental_return_with_lines(self, return_id: UUID) -> RentalReturnWithLinesResponse:
        """Get rental return with lines."""
        rental_return = await self.return_repository.get_with_lines(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        return RentalReturnWithLinesResponse.model_validate(rental_return)
    
    async def get_rental_returns(
        self, 
        skip: int = 0, 
        limit: int = 100,
        return_type: Optional[ReturnType] = None,
        return_status: Optional[ReturnStatus] = None,
        return_location_id: Optional[UUID] = None,
        processed_by: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> List[RentalReturnListResponse]:
        """Get all rental returns with optional filtering."""
        returns = await self.return_repository.get_all(
            skip=skip,
            limit=limit,
            return_type=return_type,
            return_status=return_status,
            return_location_id=return_location_id,
            processed_by=processed_by,
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def search_rental_returns(
        self, 
        search_params: RentalReturnSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[RentalReturnListResponse]:
        """Search rental returns."""
        returns = await self.return_repository.search(
            search_params=search_params,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def update_rental_return(self, return_id: UUID, return_data: RentalReturnUpdate) -> RentalReturnResponse:
        """Update a rental return."""
        # Check if return exists
        existing_return = await self.return_repository.get_by_id(return_id)
        if not existing_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Check if return can be updated
        if existing_return.return_status in [ReturnStatus.COMPLETED.value, ReturnStatus.CANCELLED.value]:
            raise ValidationError("Cannot update completed or cancelled returns")
        
        # Update return
        rental_return = await self.return_repository.update(return_id, return_data)
        return RentalReturnResponse.model_validate(rental_return)
    
    async def delete_rental_return(self, return_id: UUID) -> bool:
        """Delete a rental return."""
        # Check if return exists
        existing_return = await self.return_repository.get_by_id(return_id)
        if not existing_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Check if return can be deleted
        if existing_return.return_status not in [ReturnStatus.PENDING.value, ReturnStatus.INITIATED.value]:
            raise ValidationError("Can only delete pending or initiated returns")
        
        return await self.return_repository.delete(return_id)
    
    async def update_return_status(self, return_id: UUID, status_update: ReturnStatusUpdate) -> RentalReturnResponse:
        """Update return status."""
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Validate status transition
        if not rental_return.can_transition_to(status_update.status):
            raise ValidationError(f"Cannot transition from {rental_return.return_status} to {status_update.status.value}")
        
        # Update status
        rental_return.update_status(status_update.status)
        
        # Add notes if provided
        if status_update.notes:
            status_note = f"\n[STATUS UPDATE] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {status_update.notes}"
            rental_return.notes = (rental_return.notes or "") + status_note
        
        await self.session.commit()
        await self.session.refresh(rental_return)
        
        return RentalReturnResponse.model_validate(rental_return)
    
    async def finalize_return(self, return_id: UUID) -> RentalReturnResponse:
        """Finalize the return process."""
        rental_return = await self.return_repository.get_with_lines(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Finalize return
        rental_return.finalize_return()
        
        await self.session.commit()
        await self.session.refresh(rental_return)
        
        return RentalReturnResponse.model_validate(rental_return)
    
    async def cancel_return(self, return_id: UUID, reason: str) -> RentalReturnResponse:
        """Cancel rental return."""
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Cancel return
        rental_return.cancel_return(reason)
        
        await self.session.commit()
        await self.session.refresh(rental_return)
        
        return RentalReturnResponse.model_validate(rental_return)
    
    # Rental Return Line operations
    async def add_return_line(self, return_id: UUID, line_data: RentalReturnLineCreate) -> RentalReturnLineResponse:
        """Add line to rental return."""
        # Check if return exists
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Check if return can be modified
        if rental_return.return_status in [ReturnStatus.COMPLETED.value, ReturnStatus.CANCELLED.value]:
            raise ValidationError("Cannot add lines to completed or cancelled returns")
        
        # Verify inventory unit exists
        inventory_unit = await self.inventory_unit_repository.get_by_id(line_data.inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {line_data.inventory_unit_id} not found")
        
        # Check if inventory unit is already in this return
        existing_lines = await self.line_repository.get_by_return(return_id)
        for line in existing_lines:
            if line.inventory_unit_id == str(line_data.inventory_unit_id):
                raise ConflictError(f"Inventory unit {line_data.inventory_unit_id} is already in this return")
        
        # Create line
        line = await self.line_repository.create(return_id, line_data)
        
        # Recalculate return totals
        await self._recalculate_return_totals(return_id)
        
        return RentalReturnLineResponse.model_validate(line)
    
    async def get_return_line(self, line_id: UUID) -> RentalReturnLineResponse:
        """Get return line by ID."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Return line with ID {line_id} not found")
        
        return RentalReturnLineResponse.model_validate(line)
    
    async def get_return_lines(self, return_id: UUID, active_only: bool = True) -> List[RentalReturnLineResponse]:
        """Get return lines."""
        lines = await self.line_repository.get_by_return(return_id, active_only)
        return [RentalReturnLineResponse.model_validate(line) for line in lines]
    
    async def update_return_line(self, line_id: UUID, line_data: RentalReturnLineUpdate) -> RentalReturnLineResponse:
        """Update return line."""
        # Check if line exists
        existing_line = await self.line_repository.get_by_id(line_id)
        if not existing_line:
            raise NotFoundError(f"Return line with ID {line_id} not found")
        
        # Check if return can be modified
        rental_return = await self.return_repository.get_by_id(UUID(existing_line.rental_return_id))
        if rental_return.return_status in [ReturnStatus.COMPLETED.value, ReturnStatus.CANCELLED.value]:
            raise ValidationError("Cannot update lines in completed or cancelled returns")
        
        # Update line
        line = await self.line_repository.update(line_id, line_data)
        
        # Recalculate return totals
        await self._recalculate_return_totals(UUID(existing_line.rental_return_id))
        
        return RentalReturnLineResponse.model_validate(line)
    
    async def delete_return_line(self, line_id: UUID) -> bool:
        """Delete return line."""
        # Check if line exists
        existing_line = await self.line_repository.get_by_id(line_id)
        if not existing_line:
            raise NotFoundError(f"Return line with ID {line_id} not found")
        
        # Check if return can be modified
        rental_return = await self.return_repository.get_by_id(UUID(existing_line.rental_return_id))
        if rental_return.return_status in [ReturnStatus.COMPLETED.value, ReturnStatus.CANCELLED.value]:
            raise ValidationError("Cannot delete lines from completed or cancelled returns")
        
        # Delete line
        success = await self.line_repository.delete(line_id)
        
        if success:
            # Recalculate return totals
            await self._recalculate_return_totals(UUID(existing_line.rental_return_id))
        
        return success
    
    async def update_line_status(self, line_id: UUID, status_update: LineStatusUpdate) -> RentalReturnLineResponse:
        """Update return line status."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Return line with ID {line_id} not found")
        
        # Update status
        line.update_status(ReturnLineStatus(status_update.status))
        
        # Add notes if provided
        if status_update.notes:
            status_note = f"\n[STATUS UPDATE] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {status_update.notes}"
            line.notes = (line.notes or "") + status_note
        
        await self.session.commit()
        await self.session.refresh(line)
        
        return RentalReturnLineResponse.model_validate(line)
    
    async def assess_damage(self, line_id: UUID, damage_assessment: DamageAssessment) -> RentalReturnLineResponse:
        """Assess damage for return line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Return line with ID {line_id} not found")
        
        # Update damage assessment
        line.damage_level = damage_assessment.damage_level.value
        
        # Calculate damage fee based on damage level
        if damage_assessment.damage_level == DamageLevel.MINOR:
            line.damage_fee = damage_assessment.repair_cost_estimate or Decimal("50.00")
        elif damage_assessment.damage_level == DamageLevel.MODERATE:
            line.damage_fee = damage_assessment.repair_cost_estimate or Decimal("150.00")
        elif damage_assessment.damage_level == DamageLevel.MAJOR:
            line.damage_fee = damage_assessment.repair_cost_estimate or Decimal("300.00")
        elif damage_assessment.damage_level == DamageLevel.TOTAL_LOSS:
            line.damage_fee = damage_assessment.replacement_cost_estimate or Decimal("500.00")
        else:
            line.damage_fee = Decimal("0.00")
        
        # Add assessment notes
        if damage_assessment.notes:
            damage_note = f"\n[DAMAGE ASSESSMENT] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {damage_assessment.notes}"
            line.notes = (line.notes or "") + damage_note
        
        await self.session.commit()
        await self.session.refresh(line)
        
        # Recalculate return totals
        await self._recalculate_return_totals(UUID(line.rental_return_id))
        
        return RentalReturnLineResponse.model_validate(line)
    
    async def calculate_fees(self, line_id: UUID, fee_calculation: FeeCalculation) -> RentalReturnLineResponse:
        """Calculate fees for return line."""
        line = await self.line_repository.get_by_id(line_id)
        if not line:
            raise NotFoundError(f"Return line with ID {line_id} not found")
        
        # Set fees
        line.set_late_fee(fee_calculation.late_fee)
        line.set_damage_fee(fee_calculation.damage_fee)
        
        # Add calculation notes
        if fee_calculation.notes:
            fee_note = f"\n[FEE CALCULATION] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {fee_calculation.notes}"
            line.notes = (line.notes or "") + fee_note
        
        await self.session.commit()
        await self.session.refresh(line)
        
        # Recalculate return totals
        await self._recalculate_return_totals(UUID(line.rental_return_id))
        
        return RentalReturnLineResponse.model_validate(line)
    
    # Inspection Report operations
    async def create_inspection_report(self, return_id: UUID, report_data: InspectionReportCreate) -> InspectionReportResponse:
        """Create inspection report."""
        # Check if return exists
        rental_return = await self.return_repository.get_by_id(return_id)
        if not rental_return:
            raise NotFoundError(f"Rental return with ID {return_id} not found")
        
        # Verify inventory unit exists
        inventory_unit = await self.inventory_unit_repository.get_by_id(report_data.inventory_unit_id)
        if not inventory_unit:
            raise NotFoundError(f"Inventory unit with ID {report_data.inventory_unit_id} not found")
        
        # Create inspection report
        report = await self.inspection_repository.create(return_id, report_data)
        return InspectionReportResponse.model_validate(report)
    
    async def get_inspection_report(self, report_id: UUID) -> InspectionReportResponse:
        """Get inspection report by ID."""
        report = await self.inspection_repository.get_by_id(report_id)
        if not report:
            raise NotFoundError(f"Inspection report with ID {report_id} not found")
        
        return InspectionReportResponse.model_validate(report)
    
    async def get_inspection_reports(self, return_id: UUID, active_only: bool = True) -> List[InspectionReportResponse]:
        """Get inspection reports for return."""
        reports = await self.inspection_repository.get_by_return(return_id, active_only)
        return [InspectionReportResponse.model_validate(report) for report in reports]
    
    async def update_inspection_report(self, report_id: UUID, report_data: InspectionReportUpdate) -> InspectionReportResponse:
        """Update inspection report."""
        # Check if report exists
        existing_report = await self.inspection_repository.get_by_id(report_id)
        if not existing_report:
            raise NotFoundError(f"Inspection report with ID {report_id} not found")
        
        # Check if report can be updated
        if existing_report.inspection_status == InspectionStatus.COMPLETED.value:
            raise ValidationError("Cannot update completed inspection report")
        
        # Update report
        report = await self.inspection_repository.update(report_id, report_data)
        return InspectionReportResponse.model_validate(report)
    
    async def complete_inspection(self, report_id: UUID, completion_data: InspectionCompletion) -> InspectionReportResponse:
        """Complete inspection."""
        report = await self.inspection_repository.get_by_id(report_id)
        if not report:
            raise NotFoundError(f"Inspection report with ID {report_id} not found")
        
        # Update inspection details
        report.damage_level = completion_data.damage_level.value
        report.damage_description = completion_data.damage_description
        report.repair_cost_estimate = completion_data.repair_cost_estimate
        report.replacement_cost_estimate = completion_data.replacement_cost_estimate
        report.inspection_notes = completion_data.inspection_notes
        
        # Complete inspection
        report.complete_inspection()
        
        await self.session.commit()
        await self.session.refresh(report)
        
        return InspectionReportResponse.model_validate(report)
    
    async def fail_inspection(self, report_id: UUID, failure_data: InspectionFailure) -> InspectionReportResponse:
        """Fail inspection."""
        report = await self.inspection_repository.get_by_id(report_id)
        if not report:
            raise NotFoundError(f"Inspection report with ID {report_id} not found")
        
        # Fail inspection
        report.fail_inspection(failure_data.reason)
        
        # Add failure notes
        if failure_data.notes:
            failure_note = f"\n[FAILURE NOTES] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {failure_data.notes}"
            report.inspection_notes = (report.inspection_notes or "") + failure_note
        
        await self.session.commit()
        await self.session.refresh(report)
        
        return InspectionReportResponse.model_validate(report)
    
    # Reporting operations
    async def get_rental_dashboard(self) -> RentalDashboard:
        """Get rental dashboard data."""
        today = date.today()
        
        # Get active rentals (transactions in progress)
        active_rentals_count = await self.transaction_repository.count_all(
            status=TransactionStatus.IN_PROGRESS,
            transaction_type=TransactionType.RENTAL
        )
        
        # Get overdue returns
        overdue_returns = await self.return_repository.get_overdue_returns(today)
        overdue_count = len(overdue_returns)
        
        # Get returns due today
        returns_due_today = await self.return_repository.get_returns_due_today(today)
        due_today_count = len(returns_due_today)
        
        # Get returns due this week
        week_end = today + timedelta(days=7)
        returns_due_week = await self.return_repository.get_all(
            date_from=today,
            date_to=week_end,
            return_status=ReturnStatus.PENDING
        )
        due_week_count = len(returns_due_week)
        
        # Get pending inspections
        pending_inspections = await self.inspection_repository.get_pending_inspections()
        pending_inspections_count = len(pending_inspections)
        
        # Calculate total outstanding fees
        all_returns = await self.return_repository.get_all(
            return_status=ReturnStatus.IN_PROGRESS
        )
        total_outstanding_fees = sum(
            ret.total_late_fee + ret.total_damage_fee for ret in all_returns
        )
        
        # Get recent returns
        recent_returns = await self.return_repository.get_all(limit=10)
        
        return RentalDashboard(
            active_rentals=active_rentals_count,
            overdue_returns=overdue_count,
            returns_due_today=due_today_count,
            returns_due_this_week=due_week_count,
            pending_inspections=pending_inspections_count,
            total_outstanding_fees=total_outstanding_fees,
            recent_returns=[RentalReturnListResponse.model_validate(ret) for ret in recent_returns],
            overdue_returns_list=[RentalReturnListResponse.model_validate(ret) for ret in overdue_returns]
        )
    
    async def get_rental_return_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> RentalReturnSummary:
        """Get rental return summary."""
        summary_data = await self.return_repository.get_return_summary(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        return RentalReturnSummary(
            total_returns=summary_data['total_returns'],
            completed_returns=summary_data['completed_returns'],
            pending_returns=summary_data['pending_returns'],
            cancelled_returns=summary_data['cancelled_returns'],
            total_late_fees=summary_data['total_late_fees'],
            total_damage_fees=summary_data['total_damage_fees'],
            total_refunds=summary_data['total_refunds'],
            returns_by_status=summary_data['returns_by_status'],
            returns_by_type=summary_data['returns_by_type'],
            average_processing_time=summary_data['average_processing_time']
        )
    
    async def get_rental_return_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> RentalReturnReport:
        """Get rental return report."""
        returns = await self.return_repository.get_all(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        summary = await self.get_rental_return_summary(
            date_from=date_from,
            date_to=date_to,
            active_only=active_only
        )
        
        return RentalReturnReport(
            returns=[RentalReturnListResponse.model_validate(ret) for ret in returns],
            summary=summary,
            date_range={
                'from': date_from or date.min,
                'to': date_to or date.today()
            }
        )
    
    async def get_overdue_returns(self, as_of_date: date = None) -> List[RentalReturnListResponse]:
        """Get overdue returns."""
        returns = await self.return_repository.get_overdue_returns(as_of_date)
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def get_returns_due_today(self, as_of_date: date = None) -> List[RentalReturnListResponse]:
        """Get returns due today."""
        returns = await self.return_repository.get_returns_due_today(as_of_date)
        return [RentalReturnListResponse.model_validate(ret) for ret in returns]
    
    async def get_pending_inspections(self) -> List[InspectionReportResponse]:
        """Get pending inspections."""
        reports = await self.inspection_repository.get_pending_inspections()
        return [InspectionReportResponse.model_validate(report) for report in reports]
    
    # Helper methods
    async def _recalculate_return_totals(self, return_id: UUID):
        """Recalculate return totals."""
        rental_return = await self.return_repository.get_with_lines(return_id)
        if rental_return:
            rental_return.calculate_totals()
            await self.session.commit()
    
    async def _calculate_late_fees(self, return_id: UUID, daily_rate: Decimal = Decimal("10.00")):
        """Calculate late fees for return."""
        rental_return = await self.return_repository.get_with_lines(return_id)
        if rental_return and rental_return.is_late():
            days_late = rental_return.days_late()
            for line in rental_return.return_lines:
                late_fee = line.returned_quantity * daily_rate * days_late
                line.set_late_fee(late_fee)
            
            await self.session.commit()
    
    async def _calculate_deposit_release(self, return_id: UUID, original_deposit: Decimal):
        """Calculate deposit release for return."""
        rental_return = await self.return_repository.get_with_lines(return_id)
        if rental_return:
            # Calculate proportional deposit release
            total_original = sum(line.original_quantity for line in rental_return.return_lines)
            total_returned = sum(line.returned_quantity for line in rental_return.return_lines)
            
            if total_original > 0:
                return_percentage = total_returned / total_original
                deposit_release = (return_percentage * original_deposit) - rental_return.total_late_fee - rental_return.total_damage_fee
                rental_return.total_deposit_release = max(deposit_release, Decimal("0.00"))
                
                await self.session.commit()


# Additional imports needed for the dashboard
from datetime import timedelta
from app.modules.transactions.models import TransactionStatus, TransactionType