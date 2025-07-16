"""
Audit Service

This service provides comprehensive audit logging capabilities for tracking
all system changes and transaction events. It integrates with both the
database-based audit log and the file-based transaction logger.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.modules.system.models import AuditLog
from app.modules.transactions.models.events import TransactionEvent
from app.core.transaction_logger import get_transaction_logger


class AuditService:
    """
    Service for managing comprehensive audit trails and transaction logging.
    
    This service coordinates between:
    - Database audit logs (AuditLog model)
    - Transaction events (TransactionEvent model)
    - File-based transaction logs (TransactionLogger)
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the audit service.
        
        Args:
            db_session: Database session for audit operations
        """
        self.db_session = db_session
        self.transaction_logger = get_transaction_logger()
        
    async def log_transaction_start(
        self,
        transaction_id: UUID,
        transaction_type: str,
        operation_name: str,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log the start of a transaction in both database and file logs.
        
        Args:
            transaction_id: Transaction identifier
            transaction_type: Type of transaction
            operation_name: Specific operation being performed
            user_id: User initiating the transaction
            session_id: Session identifier
            ip_address: Client IP address
            additional_data: Additional context data
        """
        # Start file-based logging
        self.transaction_logger.start_transaction_log(
            transaction_type=transaction_type,
            transaction_id=transaction_id,
            operation_name=operation_name
        )
        
        # Create database audit log
        await self._create_audit_log(
            entity_type="TRANSACTION",
            entity_id=str(transaction_id),
            action="CREATE",
            description=f"Started {transaction_type} transaction",
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            additional_data=additional_data
        )
        
        # Create transaction event
        await self._create_transaction_event(
            transaction_id=str(transaction_id),
            event_type="TRANSACTION_STARTED",
            description=f"{transaction_type} transaction initiated",
            category="TRANSACTION",
            user_id=str(user_id) if user_id else None,
            operation_name=operation_name,
            event_data=additional_data
        )
        
    async def log_validation_step(
        self,
        transaction_id: UUID,
        validation_type: str,
        result: bool,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> None:
        """
        Log validation steps and their results.
        
        Args:
            transaction_id: Transaction identifier
            validation_type: Type of validation performed
            result: Whether validation passed
            details: Validation details and results
            user_id: User performing the validation
        """
        # Log to file
        self.transaction_logger.log_validation(
            validation_type=validation_type,
            result=result,
            details=details
        )
        
        # Create transaction event
        await self._create_transaction_event(
            transaction_id=str(transaction_id),
            event_type="VALIDATION",
            description=f"{validation_type} validation {'passed' if result else 'failed'}",
            category="VALIDATION",
            status="SUCCESS" if result else "FAILURE",
            user_id=str(user_id) if user_id else None,
            event_data={
                "validation_type": validation_type,
                "result": result,
                "details": details or {}
            }
        )
        
    async def log_inventory_change(
        self,
        transaction_id: UUID,
        item_id: UUID,
        item_name: str,
        change_type: str,
        quantity_before: Decimal,
        quantity_after: Decimal,
        location_id: Optional[UUID] = None,
        location_name: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> None:
        """
        Log inventory changes caused by transactions.
        
        Args:
            transaction_id: Transaction identifier
            item_id: Item identifier
            item_name: Item name
            change_type: Type of change (SALE, PURCHASE, RENTAL_OUT, etc.)
            quantity_before: Quantity before change
            quantity_after: Quantity after change
            location_id: Location identifier
            location_name: Location name
            user_id: User making the change
        """
        quantity_change = quantity_after - quantity_before
        
        # Log to file
        self.transaction_logger.log_inventory_change(
            item_id=item_id,
            item_name=item_name,
            change_type=change_type,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            location_id=location_id,
            location_name=location_name
        )
        
        # Create audit log
        await self._create_audit_log(
            entity_type="INVENTORY",
            entity_id=str(item_id),
            action=change_type,
            description=f"Inventory change: {item_name} ({quantity_change:+})",
            user_id=user_id,
            old_values={
                "quantity": str(quantity_before),
                "location_id": str(location_id) if location_id else None
            },
            new_values={
                "quantity": str(quantity_after),
                "location_id": str(location_id) if location_id else None
            },
            additional_data={
                "transaction_id": str(transaction_id),
                "change_type": change_type,
                "location_name": location_name
            }
        )
        
        # Create transaction event
        await self._create_transaction_event(
            transaction_id=str(transaction_id),
            event_type="INVENTORY_CHANGE",
            description=f"Inventory {change_type}: {item_name} ({quantity_change:+})",
            category="INVENTORY",
            user_id=str(user_id) if user_id else None,
            event_data={
                "item_id": str(item_id),
                "item_name": item_name,
                "change_type": change_type,
                "quantity_before": str(quantity_before),
                "quantity_after": str(quantity_after),
                "quantity_change": str(quantity_change),
                "location_id": str(location_id) if location_id else None,
                "location_name": location_name
            }
        )
        
    async def log_payment_event(
        self,
        transaction_id: UUID,
        payment_type: str,
        amount: Decimal,
        method: str,
        status: str,
        reference: Optional[str] = None,
        user_id: Optional[UUID] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log payment-related events.
        
        Args:
            transaction_id: Transaction identifier
            payment_type: Type of payment
            amount: Payment amount
            method: Payment method
            status: Payment status
            reference: Payment reference
            user_id: User processing the payment
            additional_details: Additional payment details
        """
        # Log to file
        self.transaction_logger.log_payment_event(
            payment_type=payment_type,
            amount=amount,
            method=method,
            status=status,
            reference=reference,
            details=additional_details
        )
        
        # Create audit log
        await self._create_audit_log(
            entity_type="PAYMENT",
            entity_id=str(transaction_id),
            action=payment_type,
            description=f"Payment {payment_type}: {amount} via {method}",
            user_id=user_id,
            additional_data={
                "transaction_id": str(transaction_id),
                "amount": str(amount),
                "method": method,
                "status": status,
                "reference": reference,
                **(additional_details or {})
            }
        )
        
        # Create transaction event
        await self._create_transaction_event(
            transaction_id=str(transaction_id),
            event_type="PAYMENT_EVENT",
            description=f"Payment {payment_type}: {amount} via {method} - {status}",
            category="PAYMENT",
            user_id=str(user_id) if user_id else None,
            status="SUCCESS" if status in ["COMPLETED", "APPROVED"] else "PENDING",
            event_data={
                "payment_type": payment_type,
                "amount": str(amount),
                "method": method,
                "status": status,
                "reference": reference,
                "details": additional_details or {}
            }
        )
        
    async def log_master_data_change(
        self,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        action: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None,
        transaction_id: Optional[UUID] = None
    ) -> None:
        """
        Log changes to master data entities.
        
        Args:
            entity_type: Type of entity (CUSTOMER, ITEM, LOCATION, etc.)
            entity_id: Entity identifier
            entity_name: Entity name
            action: Action performed (CREATE, UPDATE, DELETE)
            old_values: Previous values
            new_values: New values
            user_id: User making the change
            transaction_id: Related transaction if applicable
        """
        # Log to file if part of a transaction
        if transaction_id and self.transaction_logger.current_transaction_id:
            self.transaction_logger.log_master_data_change(
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                change_type=action,
                old_values=old_values,
                new_values=new_values
            )
        
        # Create audit log
        await self._create_audit_log(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            description=f"{action} {entity_type}: {entity_name}",
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            additional_data={
                "transaction_id": str(transaction_id) if transaction_id else None
            }
        )
        
        # Create transaction event if part of a transaction
        if transaction_id:
            await self._create_transaction_event(
                transaction_id=str(transaction_id),
                event_type="MASTER_DATA_CHANGE",
                description=f"{action} {entity_type}: {entity_name}",
                category="MASTER_DATA",
                user_id=str(user_id) if user_id else None,
                event_data={
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "entity_name": entity_name,
                    "action": action,
                    "old_values": old_values or {},
                    "new_values": new_values or {}
                }
            )
            
    async def log_error(
        self,
        transaction_id: Optional[UUID],
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> None:
        """
        Log errors that occur during processing.
        
        Args:
            transaction_id: Transaction identifier if applicable
            error_type: Type of error
            error_message: Error message
            error_details: Additional error details
            stack_trace: Stack trace if available
            user_id: User associated with the error
        """
        # Log to file if part of a transaction
        if transaction_id and self.transaction_logger.current_transaction_id:
            self.transaction_logger.log_error(
                error_type=error_type,
                error_message=error_message,
                error_details=error_details,
                stack_trace=stack_trace
            )
        
        # Create audit log
        await self._create_audit_log(
            entity_type="SYSTEM",
            entity_id=str(transaction_id) if transaction_id else "SYSTEM",
            action="ERROR",
            description=f"Error: {error_type} - {error_message}",
            user_id=user_id,
            additional_data={
                "error_type": error_type,
                "error_message": error_message,
                "error_details": error_details or {},
                "stack_trace": stack_trace,
                "transaction_id": str(transaction_id) if transaction_id else None
            }
        )
        
        # Create transaction event if part of a transaction
        if transaction_id:
            await self._create_transaction_event(
                transaction_id=str(transaction_id),
                event_type="ERROR",
                description=error_message,
                category="ERROR",
                status="FAILURE",
                user_id=str(user_id) if user_id else None,
                error_code=error_type,
                error_message=error_message,
                event_data={
                    "error_details": error_details or {},
                    "stack_trace": stack_trace
                }
            )
            
    async def complete_transaction_log(
        self,
        transaction_id: UUID,
        final_status: str,
        user_id: Optional[UUID] = None,
        completion_notes: Optional[str] = None
    ) -> Optional[str]:
        """
        Complete transaction logging and generate final log file.
        
        Args:
            transaction_id: Transaction identifier
            final_status: Final transaction status
            user_id: User completing the transaction
            completion_notes: Additional completion notes
            
        Returns:
            Path to the generated log file if successful
        """
        # Create final audit log
        await self._create_audit_log(
            entity_type="TRANSACTION",
            entity_id=str(transaction_id),
            action="COMPLETE",
            description=f"Transaction completed with status: {final_status}",
            user_id=user_id,
            additional_data={
                "final_status": final_status,
                "completion_notes": completion_notes
            }
        )
        
        # Create final transaction event
        await self._create_transaction_event(
            transaction_id=str(transaction_id),
            event_type="TRANSACTION_COMPLETED",
            description=f"Transaction completed: {final_status}",
            category="TRANSACTION",
            user_id=str(user_id) if user_id else None,
            status="SUCCESS" if final_status == "COMPLETED" else "FAILURE",
            event_data={
                "final_status": final_status,
                "completion_notes": completion_notes
            }
        )
        
        # Complete file-based logging
        if self.transaction_logger.current_transaction_id == transaction_id:
            log_file = self.transaction_logger.complete_transaction_log(final_status)
            return str(log_file)
            
        return None
        
    async def get_transaction_audit_trail(
        self,
        transaction_id: UUID,
        include_events: bool = True,
        include_audit_logs: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve complete audit trail for a transaction.
        
        Args:
            transaction_id: Transaction identifier
            include_events: Whether to include transaction events
            include_audit_logs: Whether to include audit logs
            
        Returns:
            Dictionary containing audit trail data
        """
        result = {
            "transaction_events": [],
            "audit_logs": [],
            "summary": {
                "total_events": 0,
                "total_audit_logs": 0,
                "has_errors": False,
                "completion_status": None
            }
        }
        
        # Get transaction events
        if include_events:
            events_query = select(TransactionEvent).where(
                TransactionEvent.transaction_id == str(transaction_id)
            ).order_by(TransactionEvent.event_timestamp)
            
            events_result = await self.db_session.execute(events_query)
            events = events_result.scalars().all()
            
            result["transaction_events"] = [event.to_dict() for event in events]
            result["summary"]["total_events"] = len(events)
            result["summary"]["has_errors"] = any(
                event.status == "FAILURE" for event in events
            )
            
            # Get completion status from last event
            if events:
                last_event = events[-1]
                if last_event.event_type == "TRANSACTION_COMPLETED":
                    result["summary"]["completion_status"] = last_event.event_data.get("final_status")
        
        # Get audit logs
        if include_audit_logs:
            audit_query = select(AuditLog).where(
                or_(
                    AuditLog.entity_id == str(transaction_id),
                    AuditLog.additional_data.op('->>')('transaction_id') == str(transaction_id)
                )
            ).order_by(AuditLog.created_at)
            
            audit_result = await self.db_session.execute(audit_query)
            audit_logs = audit_result.scalars().all()
            
            result["audit_logs"] = [
                {
                    "id": str(log.id),
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "action": log.action,
                    "description": log.description,
                    "old_values": log.old_values,
                    "new_values": log.new_values,
                    "additional_data": log.additional_data,
                    "created_at": log.created_at.isoformat(),
                    "created_by": str(log.created_by) if log.created_by else None
                }
                for log in audit_logs
            ]
            result["summary"]["total_audit_logs"] = len(audit_logs)
        
        return result
        
    async def _create_audit_log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        description: str,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            created_by=user_id,
            session_id=session_id,
            ip_address=ip_address,
            old_values=old_values or {},
            new_values=new_values or {},
            additional_data=additional_data or {}
        )
        
        self.db_session.add(audit_log)
        await self.db_session.flush()
        return audit_log
        
    async def _create_transaction_event(
        self,
        transaction_id: str,
        event_type: str,
        description: str,
        category: str = "GENERAL",
        status: str = "SUCCESS",
        user_id: Optional[str] = None,
        operation_name: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> TransactionEvent:
        """Create a new transaction event."""
        event = TransactionEvent(
            transaction_id=transaction_id,
            event_type=event_type,
            description=description,
            event_category=category,
            status=status,
            user_id=user_id,
            operation_name=operation_name,
            error_code=error_code,
            error_message=error_message,
            event_data=event_data or {}
        )
        
        self.db_session.add(event)
        await self.db_session.flush()
        return event