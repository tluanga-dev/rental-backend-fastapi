from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import and_, or_, func, select, update, delete, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.modules.rentals.models import (
    RentalReturn, RentalReturnLine, InspectionReport,
    ReturnStatus, DamageLevel, ReturnType, InspectionStatus, ReturnLineStatus
)
from app.modules.rentals.schemas import (
    RentalReturnCreate, RentalReturnUpdate,
    RentalReturnLineCreate, RentalReturnLineUpdate,
    InspectionReportCreate, InspectionReportUpdate,
    RentalReturnSearch
)


class RentalReturnRepository:
    """Repository for RentalReturn operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, return_data: RentalReturnCreate) -> RentalReturn:
        """Create a new rental return."""
        rental_return = RentalReturn(
            rental_transaction_id=str(return_data.rental_transaction_id),
            return_date=return_data.return_date,
            return_type=return_data.return_type,
            return_status=return_data.return_status,
            return_location_id=str(return_data.return_location_id) if return_data.return_location_id else None,
            expected_return_date=return_data.expected_return_date,
            notes=return_data.notes
        )
        
        self.session.add(rental_return)
        await self.session.commit()
        await self.session.refresh(rental_return)
        return rental_return
    
    async def get_by_id(self, return_id: UUID) -> Optional[RentalReturn]:
        """Get rental return by ID."""
        query = select(RentalReturn).where(RentalReturn.id == return_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_lines(self, return_id: UUID) -> Optional[RentalReturn]:
        """Get rental return with lines and inspection reports."""
        query = select(RentalReturn).options(
            selectinload(RentalReturn.return_lines),
            selectinload(RentalReturn.inspection_reports)
        ).where(RentalReturn.id == return_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_transaction(self, transaction_id: UUID, active_only: bool = True) -> List[RentalReturn]:
        """Get rental returns by transaction."""
        query = select(RentalReturn).where(RentalReturn.rental_transaction_id == str(transaction_id))
        
        if active_only:
            query = query.where(RentalReturn.is_active == True)
        
        query = query.order_by(desc(RentalReturn.return_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_all(
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
    ) -> List[RentalReturn]:
        """Get all rental returns with optional filtering."""
        query = select(RentalReturn)
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(RentalReturn.is_active == True)
        if return_type:
            conditions.append(RentalReturn.return_type == return_type.value)
        if return_status:
            conditions.append(RentalReturn.return_status == return_status.value)
        if return_location_id:
            conditions.append(RentalReturn.return_location_id == str(return_location_id))
        if processed_by:
            conditions.append(RentalReturn.processed_by == str(processed_by))
        if date_from:
            conditions.append(RentalReturn.return_date >= date_from)
        if date_to:
            conditions.append(RentalReturn.return_date <= date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(RentalReturn.return_date)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_all(
        self,
        return_type: Optional[ReturnType] = None,
        return_status: Optional[ReturnStatus] = None,
        return_location_id: Optional[UUID] = None,
        processed_by: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> int:
        """Count all rental returns with optional filtering."""
        query = select(func.count(RentalReturn.id))
        
        # Apply filters
        conditions = []
        if active_only:
            conditions.append(RentalReturn.is_active == True)
        if return_type:
            conditions.append(RentalReturn.return_type == return_type.value)
        if return_status:
            conditions.append(RentalReturn.return_status == return_status.value)
        if return_location_id:
            conditions.append(RentalReturn.return_location_id == str(return_location_id))
        if processed_by:
            conditions.append(RentalReturn.processed_by == str(processed_by))
        if date_from:
            conditions.append(RentalReturn.return_date >= date_from)
        if date_to:
            conditions.append(RentalReturn.return_date <= date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def search(
        self, 
        search_params: RentalReturnSearch,
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[RentalReturn]:
        """Search rental returns."""
        query = select(RentalReturn)
        
        conditions = []
        if active_only:
            conditions.append(RentalReturn.is_active == True)
        
        if search_params.rental_transaction_id:
            conditions.append(RentalReturn.rental_transaction_id == str(search_params.rental_transaction_id))
        if search_params.return_type:
            conditions.append(RentalReturn.return_type == search_params.return_type.value)
        if search_params.return_status:
            conditions.append(RentalReturn.return_status == search_params.return_status.value)
        if search_params.return_location_id:
            conditions.append(RentalReturn.return_location_id == str(search_params.return_location_id))
        if search_params.processed_by:
            conditions.append(RentalReturn.processed_by == str(search_params.processed_by))
        if search_params.date_from:
            conditions.append(RentalReturn.return_date >= search_params.date_from)
        if search_params.date_to:
            conditions.append(RentalReturn.return_date <= search_params.date_to)
        if search_params.expected_date_from:
            conditions.append(RentalReturn.expected_return_date >= search_params.expected_date_from)
        if search_params.expected_date_to:
            conditions.append(RentalReturn.expected_return_date <= search_params.expected_date_to)
        if search_params.is_late is not None:
            if search_params.is_late:
                conditions.append(RentalReturn.return_date > RentalReturn.expected_return_date)
            else:
                conditions.append(
                    or_(
                        RentalReturn.expected_return_date.is_(None),
                        RentalReturn.return_date <= RentalReturn.expected_return_date
                    )
                )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(RentalReturn.return_date)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_overdue_returns(self, as_of_date: date = None) -> List[RentalReturn]:
        """Get overdue returns."""
        if as_of_date is None:
            as_of_date = date.today()
        
        query = select(RentalReturn).where(
            and_(
                RentalReturn.expected_return_date < as_of_date,
                RentalReturn.return_status.not_in([
                    ReturnStatus.COMPLETED.value,
                    ReturnStatus.CANCELLED.value
                ]),
                RentalReturn.is_active == True
            )
        )
        
        query = query.order_by(asc(RentalReturn.expected_return_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_returns_due_today(self, as_of_date: date = None) -> List[RentalReturn]:
        """Get returns due today."""
        if as_of_date is None:
            as_of_date = date.today()
        
        query = select(RentalReturn).where(
            and_(
                RentalReturn.expected_return_date == as_of_date,
                RentalReturn.return_status.not_in([
                    ReturnStatus.COMPLETED.value,
                    ReturnStatus.CANCELLED.value
                ]),
                RentalReturn.is_active == True
            )
        )
        
        query = query.order_by(asc(RentalReturn.expected_return_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_inspections(self) -> List[RentalReturn]:
        """Get returns with pending inspections."""
        query = select(RentalReturn).where(
            and_(
                RentalReturn.return_status == ReturnStatus.IN_INSPECTION.value,
                RentalReturn.is_active == True
            )
        )
        
        query = query.order_by(asc(RentalReturn.return_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, return_id: UUID, return_data: RentalReturnUpdate) -> Optional[RentalReturn]:
        """Update a rental return."""
        query = select(RentalReturn).where(RentalReturn.id == return_id)
        result = await self.session.execute(query)
        rental_return = result.scalar_one_or_none()
        
        if not rental_return:
            return None
        
        # Update fields
        update_data = return_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['return_location_id', 'processed_by']:
                setattr(rental_return, field, str(value) if value else None)
            else:
                setattr(rental_return, field, value)
        
        await self.session.commit()
        await self.session.refresh(rental_return)
        return rental_return
    
    async def delete(self, return_id: UUID) -> bool:
        """Soft delete a rental return."""
        query = select(RentalReturn).where(RentalReturn.id == return_id)
        result = await self.session.execute(query)
        rental_return = result.scalar_one_or_none()
        
        if not rental_return:
            return False
        
        rental_return.is_active = False
        await self.session.commit()
        return True
    
    async def get_return_summary(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """Get return summary statistics."""
        query = select(RentalReturn)
        
        conditions = []
        if active_only:
            conditions.append(RentalReturn.is_active == True)
        if date_from:
            conditions.append(RentalReturn.return_date >= date_from)
        if date_to:
            conditions.append(RentalReturn.return_date <= date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        returns = result.scalars().all()
        
        total_returns = len(returns)
        completed_returns = len([r for r in returns if r.return_status == ReturnStatus.COMPLETED.value])
        pending_returns = len([r for r in returns if r.return_status in [ReturnStatus.PENDING.value, ReturnStatus.INITIATED.value]])
        cancelled_returns = len([r for r in returns if r.return_status == ReturnStatus.CANCELLED.value])
        
        total_late_fees = sum(r.total_late_fee for r in returns)
        total_damage_fees = sum(r.total_damage_fee for r in returns)
        total_refunds = sum(r.total_refund_amount for r in returns)
        
        # Count by status
        status_counts = {}
        for status in ReturnStatus:
            status_counts[status.value] = len([r for r in returns if r.return_status == status.value])
        
        # Count by type
        type_counts = {}
        for return_type in ReturnType:
            type_counts[return_type.value] = len([r for r in returns if r.return_type == return_type.value])
        
        # Calculate average processing time
        completed_with_times = [r for r in returns if r.return_status == ReturnStatus.COMPLETED.value and r.created_at and r.updated_at]
        if completed_with_times:
            total_processing_time = sum(
                (r.updated_at - r.created_at).total_seconds() / 3600 
                for r in completed_with_times
            )
            average_processing_time = total_processing_time / len(completed_with_times)
        else:
            average_processing_time = 0.0
        
        return {
            'total_returns': total_returns,
            'completed_returns': completed_returns,
            'pending_returns': pending_returns,
            'cancelled_returns': cancelled_returns,
            'total_late_fees': total_late_fees,
            'total_damage_fees': total_damage_fees,
            'total_refunds': total_refunds,
            'returns_by_status': status_counts,
            'returns_by_type': type_counts,
            'average_processing_time': average_processing_time
        }


class RentalReturnLineRepository:
    """Repository for RentalReturnLine operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, return_id: UUID, line_data: RentalReturnLineCreate) -> RentalReturnLine:
        """Create a new rental return line."""
        line = RentalReturnLine(
            rental_return_id=str(return_id),
            inventory_unit_id=str(line_data.inventory_unit_id),
            original_quantity=line_data.original_quantity,
            returned_quantity=line_data.returned_quantity,
            damage_level=line_data.damage_level,
            line_status=line_data.line_status,
            notes=line_data.notes
        )
        
        self.session.add(line)
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def get_by_id(self, line_id: UUID) -> Optional[RentalReturnLine]:
        """Get rental return line by ID."""
        query = select(RentalReturnLine).where(RentalReturnLine.id == line_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_return(self, return_id: UUID, active_only: bool = True) -> List[RentalReturnLine]:
        """Get rental return lines by return."""
        query = select(RentalReturnLine).where(RentalReturnLine.rental_return_id == str(return_id))
        
        if active_only:
            query = query.where(RentalReturnLine.is_active == True)
        
        query = query.order_by(asc(RentalReturnLine.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_inventory_unit(self, inventory_unit_id: UUID, active_only: bool = True) -> List[RentalReturnLine]:
        """Get rental return lines by inventory unit."""
        query = select(RentalReturnLine).where(RentalReturnLine.inventory_unit_id == str(inventory_unit_id))
        
        if active_only:
            query = query.where(RentalReturnLine.is_active == True)
        
        query = query.order_by(desc(RentalReturnLine.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_lines_with_damage(self, damage_level: Optional[DamageLevel] = None) -> List[RentalReturnLine]:
        """Get return lines with damage."""
        query = select(RentalReturnLine).where(
            and_(
                RentalReturnLine.damage_level != DamageLevel.NONE.value,
                RentalReturnLine.is_active == True
            )
        )
        
        if damage_level:
            query = query.where(RentalReturnLine.damage_level == damage_level.value)
        
        query = query.order_by(desc(RentalReturnLine.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, line_id: UUID, line_data: RentalReturnLineUpdate) -> Optional[RentalReturnLine]:
        """Update a rental return line."""
        query = select(RentalReturnLine).where(RentalReturnLine.id == line_id)
        result = await self.session.execute(query)
        line = result.scalar_one_or_none()
        
        if not line:
            return None
        
        # Update fields
        update_data = line_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)
        
        await self.session.commit()
        await self.session.refresh(line)
        return line
    
    async def delete(self, line_id: UUID) -> bool:
        """Soft delete a rental return line."""
        query = select(RentalReturnLine).where(RentalReturnLine.id == line_id)
        result = await self.session.execute(query)
        line = result.scalar_one_or_none()
        
        if not line:
            return False
        
        line.is_active = False
        await self.session.commit()
        return True


class InspectionReportRepository:
    """Repository for InspectionReport operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, return_id: UUID, report_data: InspectionReportCreate) -> InspectionReport:
        """Create a new inspection report."""
        report = InspectionReport(
            rental_return_id=str(return_id),
            inventory_unit_id=str(report_data.inventory_unit_id),
            inspected_by=str(report_data.inspected_by),
            inspection_date=report_data.inspection_date,
            inspection_status=report_data.inspection_status,
            damage_level=report_data.damage_level,
            damage_description=report_data.damage_description,
            repair_cost_estimate=report_data.repair_cost_estimate,
            replacement_cost_estimate=report_data.replacement_cost_estimate,
            inspection_notes=report_data.inspection_notes
        )
        
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def get_by_id(self, report_id: UUID) -> Optional[InspectionReport]:
        """Get inspection report by ID."""
        query = select(InspectionReport).where(InspectionReport.id == report_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_return(self, return_id: UUID, active_only: bool = True) -> List[InspectionReport]:
        """Get inspection reports by return."""
        query = select(InspectionReport).where(InspectionReport.rental_return_id == str(return_id))
        
        if active_only:
            query = query.where(InspectionReport.is_active == True)
        
        query = query.order_by(desc(InspectionReport.inspection_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_inventory_unit(self, inventory_unit_id: UUID, active_only: bool = True) -> List[InspectionReport]:
        """Get inspection reports by inventory unit."""
        query = select(InspectionReport).where(InspectionReport.inventory_unit_id == str(inventory_unit_id))
        
        if active_only:
            query = query.where(InspectionReport.is_active == True)
        
        query = query.order_by(desc(InspectionReport.inspection_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_inspector(self, inspector_id: UUID, active_only: bool = True) -> List[InspectionReport]:
        """Get inspection reports by inspector."""
        query = select(InspectionReport).where(InspectionReport.inspected_by == str(inspector_id))
        
        if active_only:
            query = query.where(InspectionReport.is_active == True)
        
        query = query.order_by(desc(InspectionReport.inspection_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_inspections(self) -> List[InspectionReport]:
        """Get pending inspections."""
        query = select(InspectionReport).where(
            and_(
                InspectionReport.inspection_status == InspectionStatus.PENDING.value,
                InspectionReport.is_active == True
            )
        )
        
        query = query.order_by(asc(InspectionReport.inspection_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_completed_inspections(
        self, 
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[InspectionReport]:
        """Get completed inspections."""
        query = select(InspectionReport).where(
            and_(
                InspectionReport.inspection_status == InspectionStatus.COMPLETED.value,
                InspectionReport.is_active == True
            )
        )
        
        if date_from:
            query = query.where(InspectionReport.inspection_date >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.where(InspectionReport.inspection_date <= datetime.combine(date_to, datetime.max.time()))
        
        query = query.order_by(desc(InspectionReport.inspection_date))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, report_id: UUID, report_data: InspectionReportUpdate) -> Optional[InspectionReport]:
        """Update an inspection report."""
        query = select(InspectionReport).where(InspectionReport.id == report_id)
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            return None
        
        # Update fields
        update_data = report_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['inspected_by']:
                setattr(report, field, str(value) if value else None)
            else:
                setattr(report, field, value)
        
        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def delete(self, report_id: UUID) -> bool:
        """Soft delete an inspection report."""
        query = select(InspectionReport).where(InspectionReport.id == report_id)
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            return False
        
        report.is_active = False
        await self.session.commit()
        return True