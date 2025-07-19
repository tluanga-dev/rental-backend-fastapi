"""
Rental Status Update Service

Centralized service for updating rental statuses with comprehensive logging
and audit trails. Integrates with the status calculator to apply changes.
"""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
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
from app.modules.transactions.services.rental_status_calculator import (
    RentalStatusCalculator,
    HeaderStatus,
    LineItemStatus
)
from app.core.errors import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class RentalStatusUpdater:
    """
    Service for updating rental statuses with comprehensive logging.
    
    This service provides centralized status update functionality that:
    - Uses the status calculator to determine correct statuses
    - Updates both transaction headers and rental lifecycles
    - Creates detailed audit logs of all changes
    - Supports both individual and batch updates
    - Integrates with return events and scheduled tasks
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.calculator = RentalStatusCalculator(session)
    
    async def update_transaction_status(
        self,
        transaction_id: UUID,
        changed_by: Optional[UUID] = None,
        change_reason: RentalStatusChangeReason = RentalStatusChangeReason.MANUAL_UPDATE,
        change_trigger: Optional[str] = None,
        notes: Optional[str] = None,
        as_of_date: Optional[date] = None,
        batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the status of a rental transaction and log the changes.
        
        Args:
            transaction_id: ID of the transaction to update
            changed_by: User ID making the change (None for system changes)
            change_reason: Reason for the status change
            change_trigger: What triggered the change (event ID, job name, etc.)
            notes: Additional notes about the change
            as_of_date: Date to calculate status as of (defaults to today)
            batch_id: Batch ID for scheduled updates
            
        Returns:
            Dictionary with update results and change details
        """
        if not as_of_date:
            as_of_date = date.today()
        
        # Calculate current status
        status_data = await self.calculator.calculate_transaction_status(transaction_id, as_of_date)
        new_header_status = status_data['header_status']
        
        # Get current transaction
        result = await self.session.execute(
            select(TransactionHeader)
            .where(TransactionHeader.id == transaction_id)
            .options(selectinload(TransactionHeader.transaction_lines))
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        
        old_header_status = transaction.current_rental_status
        header_changed = old_header_status != new_header_status
        
        changes_made = []
        
        # Update header status if needed
        if header_changed:
            # Update transaction header
            await self.session.execute(
                update(TransactionHeader)
                .where(TransactionHeader.id == transaction_id)
                .values(current_rental_status=new_header_status)
            )
            
            # Update rental lifecycle if exists
            lifecycle_result = await self.session.execute(
                select(RentalLifecycle)
                .where(RentalLifecycle.transaction_id == transaction_id)
            )
            lifecycle = lifecycle_result.scalar_one_or_none()
            
            if lifecycle:
                lifecycle.current_status = new_header_status
                lifecycle.last_status_change = datetime.utcnow()
                lifecycle.status_changed_by = changed_by
            
            # Log header status change
            header_log = await self._create_status_log(
                transaction_id=transaction_id,
                old_status=old_header_status,
                new_status=new_header_status,
                change_reason=change_reason,
                change_trigger=change_trigger,
                changed_by=changed_by,
                notes=notes,
                status_metadata={
                    'summary': status_data['summary'],
                    'as_of_date': as_of_date.isoformat()
                },
                batch_id=batch_id,
                system_generated=changed_by is None
            )
            
            changes_made.append({
                'type': 'header',
                'old_status': old_header_status,
                'new_status': new_header_status,
                'log_id': header_log.id
            })
        
        # Update line item statuses
        for line_data in status_data['line_statuses']:
            line_id = UUID(line_data['line_id'])
            new_line_status = line_data['status']
            
            # Get current line status
            line_result = await self.session.execute(
                select(TransactionLine)
                .where(TransactionLine.id == line_id)
            )
            line = line_result.scalar_one_or_none()
            
            if line:
                old_line_status = line.current_rental_status
                line_changed = old_line_status != new_line_status
                
                if line_changed:
                    # Update line status
                    line.current_rental_status = new_line_status
                    
                    # Log line status change
                    line_log = await self._create_status_log(
                        transaction_id=transaction_id,
                        transaction_line_id=line_id,
                        old_status=old_line_status,
                        new_status=new_line_status,
                        change_reason=change_reason,
                        change_trigger=change_trigger,
                        changed_by=changed_by,
                        notes=f"Line item: {line_data['description']}",
                        status_metadata={
                            'line_data': line_data,
                            'as_of_date': as_of_date.isoformat()
                        },
                        batch_id=batch_id,
                        system_generated=changed_by is None
                    )
                    
                    changes_made.append({
                        'type': 'line',
                        'line_id': line_id,
                        'sku': line_data['sku'],
                        'description': line_data['description'],
                        'old_status': old_line_status,
                        'new_status': new_line_status,
                        'log_id': line_log.id
                    })
        
        # Commit all changes
        await self.session.commit()
        
        result = {
            'transaction_id': transaction_id,
            'header_status_changed': header_changed,
            'changes_made': changes_made,
            'total_changes': len(changes_made),
            'status_data': status_data,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if changes_made:
            logger.info(f"Updated status for transaction {transaction_id}: {len(changes_made)} changes made")
        
        return result
    
    async def batch_update_overdue_statuses(
        self,
        transaction_ids: Optional[List[UUID]] = None,
        changed_by: Optional[UUID] = None,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Batch update rental statuses for overdue transactions.
        
        Args:
            transaction_ids: Specific transactions to update (None = all active rentals)
            changed_by: User ID making the change (None for system changes)
            as_of_date: Date to calculate status as of (defaults to today)
            
        Returns:
            Summary of batch update results
        """
        if not as_of_date:
            as_of_date = date.today()
        
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
        
        # Find transactions needing status updates
        changes_needed = await self.calculator.find_status_changes_needed(
            transaction_ids=transaction_ids,
            as_of_date=as_of_date
        )
        
        results = {
            'batch_id': batch_id,
            'started_at': datetime.utcnow().isoformat(),
            'as_of_date': as_of_date.isoformat(),
            'total_checked': len(changes_needed) if transaction_ids is None else len(transaction_ids or []),
            'updates_needed': len(changes_needed),
            'successful_updates': 0,
            'failed_updates': 0,
            'transaction_results': [],
            'summary': {
                'status_changes': {},
                'priority_breakdown': {}
            }
        }
        
        # Process each transaction needing updates
        for change in changes_needed:
            try:
                update_result = await self.update_transaction_status(
                    transaction_id=change['transaction_id'],
                    changed_by=changed_by,
                    change_reason=RentalStatusChangeReason.SCHEDULED_UPDATE,
                    change_trigger=f"batch_update_{batch_id}",
                    notes=change['reason'],
                    as_of_date=as_of_date,
                    batch_id=batch_id
                )
                
                results['successful_updates'] += 1
                results['transaction_results'].append({
                    'transaction_id': change['transaction_id'],
                    'status': 'success',
                    'old_status': change['current_status'],
                    'new_status': change['calculated_status'],
                    'changes_made': update_result['total_changes']
                })
                
                # Track status changes for summary
                status_change_key = f"{change['current_status']} -> {change['calculated_status']}"
                results['summary']['status_changes'][status_change_key] = results['summary']['status_changes'].get(status_change_key, 0) + 1
                
                # Track priority breakdown
                priority = change['priority']
                results['summary']['priority_breakdown'][priority] = results['summary']['priority_breakdown'].get(priority, 0) + 1
                
            except Exception as e:
                results['failed_updates'] += 1
                results['transaction_results'].append({
                    'transaction_id': change['transaction_id'],
                    'status': 'error',
                    'error_message': str(e)
                })
                logger.error(f"Failed to update status for transaction {change['transaction_id']}: {e}")
        
        results['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Batch update {batch_id} completed: {results['successful_updates']} successful, {results['failed_updates']} failed")
        
        return results
    
    async def update_status_from_return_event(
        self,
        transaction_id: UUID,
        return_event_id: UUID,
        changed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update rental status based on a return event.
        
        Args:
            transaction_id: ID of the rental transaction
            return_event_id: ID of the return event that triggered the update
            changed_by: User who processed the return
            notes: Additional notes about the return
            
        Returns:
            Status update results
        """
        return await self.update_transaction_status(
            transaction_id=transaction_id,
            changed_by=changed_by,
            change_reason=RentalStatusChangeReason.RETURN_EVENT,
            change_trigger=f"return_event_{return_event_id}",
            notes=notes or "Status updated due to return event"
        )
    
    async def get_status_history(
        self,
        transaction_id: UUID,
        line_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get status change history for a transaction or line item.
        
        Args:
            transaction_id: Transaction ID to get history for
            line_id: Specific line ID (None for header history)
            limit: Maximum number of records to return
            
        Returns:
            List of status change records
        """
        query = select(RentalStatusLog).where(
            RentalStatusLog.transaction_id == transaction_id
        )
        
        if line_id:
            query = query.where(RentalStatusLog.transaction_line_id == line_id)
        else:
            query = query.where(RentalStatusLog.transaction_line_id.is_(None))
        
        query = query.order_by(RentalStatusLog.changed_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                'id': log.id,
                'old_status': log.old_status,
                'new_status': log.new_status,
                'change_reason': log.change_reason,
                'change_trigger': log.change_trigger,
                'changed_by': log.changed_by,
                'changed_at': log.changed_at.isoformat(),
                'notes': log.notes,
                'metadata': log.status_metadata,
                'system_generated': log.system_generated,
                'batch_id': log.batch_id
            }
            for log in logs
        ]
    
    async def _create_status_log(
        self,
        transaction_id: UUID,
        new_status: str,
        change_reason: RentalStatusChangeReason,
        transaction_line_id: Optional[UUID] = None,
        old_status: Optional[str] = None,
        change_trigger: Optional[str] = None,
        changed_by: Optional[UUID] = None,
        notes: Optional[str] = None,
        status_metadata: Optional[Dict[str, Any]] = None,
        batch_id: Optional[str] = None,
        system_generated: bool = False
    ) -> RentalStatusLog:
        """Create a status change log entry."""
        log_entry = RentalStatusLog(
            transaction_id=transaction_id,
            transaction_line_id=transaction_line_id,
            old_status=old_status,
            new_status=new_status,
            change_reason=change_reason.value,
            change_trigger=change_trigger,
            changed_by=changed_by,
            notes=notes,
            status_metadata=status_metadata,
            system_generated=system_generated,
            batch_id=batch_id
        )
        
        self.session.add(log_entry)
        await self.session.flush()  # Get the ID without committing
        
        return log_entry