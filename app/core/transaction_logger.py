"""
Comprehensive Transaction Logger

This module provides a generic transaction logging mechanism that captures
all transaction data and its effects across the system including:
- Transaction lifecycle events
- Inventory changes
- Master data impacts
- Payment processing
- Error handling

File naming convention: transaction-name-mm-hh-ddmmyy.md
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pathlib import Path
from decimal import Decimal

from app.core.config import settings


class TransactionLogger:
    """
    Comprehensive transaction logger that creates detailed markdown logs
    for all transaction operations and their system-wide effects.
    """
    
    def __init__(self, base_log_dir: str = "logs/transactions"):
        """
        Initialize the transaction logger.
        
        Args:
            base_log_dir: Base directory for transaction logs
        """
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        self.current_transaction_id: Optional[UUID] = None
        self.current_log_file: Optional[Path] = None
        self.transaction_start_time: Optional[datetime] = None
        self.log_data: Dict[str, Any] = {}
        
    def start_transaction_log(
        self, 
        transaction_type: str, 
        transaction_id: UUID,
        operation_name: str = None
    ) -> None:
        """
        Start logging for a new transaction.
        
        Args:
            transaction_type: Type of transaction (SALE, PURCHASE, RENTAL, etc.)
            transaction_id: Unique transaction identifier
            operation_name: Optional specific operation name
        """
        self.current_transaction_id = transaction_id
        self.transaction_start_time = datetime.now()
        
        # Generate filename: operation-name-mm-hh-ddmmyy.md
        timestamp = self.transaction_start_time
        operation = operation_name or transaction_type.lower()
        filename = f"{operation}-{timestamp.strftime('%m-%H-%d%m%y')}.md"
        
        self.current_log_file = self.base_log_dir / filename
        
        # Initialize log data structure
        self.log_data = {
            "transaction_info": {
                "transaction_id": str(transaction_id),
                "transaction_type": transaction_type,
                "operation_name": operation,
                "start_time": timestamp.isoformat(),
                "status": "STARTED"
            },
            "system_state": {
                "before": {},
                "after": {}
            },
            "events": [],
            "errors": [],
            "inventory_changes": [],
            "master_data_changes": [],
            "payment_events": [],
            "audit_trail": []
        }
        
        self._log_event("TRANSACTION_STARTED", "Transaction logging initiated")
        
    def log_event(
        self, 
        event_type: str, 
        description: str, 
        data: Dict[str, Any] = None,
        user_id: str = None
    ) -> None:
        """
        Log a transaction event.
        
        Args:
            event_type: Type of event (VALIDATION, PROCESSING, ERROR, etc.)
            description: Human-readable description
            data: Additional event data
            user_id: User who triggered the event
        """
        self._log_event(event_type, description, data, user_id)
        
    def log_validation(
        self, 
        validation_type: str, 
        result: bool, 
        details: Dict[str, Any] = None
    ) -> None:
        """
        Log validation steps and results.
        
        Args:
            validation_type: Type of validation performed
            result: Whether validation passed
            details: Validation details and results
        """
        self._log_event(
            "VALIDATION",
            f"{validation_type} validation {'passed' if result else 'failed'}",
            {
                "validation_type": validation_type,
                "result": result,
                "details": details or {}
            }
        )
        
    def log_inventory_change(
        self,
        item_id: UUID,
        item_name: str,
        change_type: str,
        quantity_before: Decimal,
        quantity_after: Decimal,
        location_id: UUID = None,
        location_name: str = None
    ) -> None:
        """
        Log inventory changes caused by the transaction.
        
        Args:
            item_id: Item identifier
            item_name: Item name
            change_type: Type of change (SALE, PURCHASE, RENTAL_OUT, RENTAL_RETURN)
            quantity_before: Quantity before change
            quantity_after: Quantity after change
            location_id: Location identifier
            location_name: Location name
        """
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "item_id": str(item_id),
            "item_name": item_name,
            "change_type": change_type,
            "quantity_before": str(quantity_before),
            "quantity_after": str(quantity_after),
            "quantity_changed": str(quantity_after - quantity_before),
            "location_id": str(location_id) if location_id else None,
            "location_name": location_name
        }
        
        self.log_data["inventory_changes"].append(change_record)
        self._log_event("INVENTORY_CHANGE", f"{change_type} - {item_name}", change_record)
        
    def log_master_data_change(
        self,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        change_type: str,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None
    ) -> None:
        """
        Log changes to master data entities.
        
        Args:
            entity_type: Type of entity (CUSTOMER, ITEM, LOCATION, etc.)
            entity_id: Entity identifier
            entity_name: Entity name
            change_type: Type of change (CREATE, UPDATE, DELETE)
            old_values: Previous values
            new_values: New values
        """
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "entity_name": entity_name,
            "change_type": change_type,
            "old_values": old_values or {},
            "new_values": new_values or {}
        }
        
        self.log_data["master_data_changes"].append(change_record)
        self._log_event("MASTER_DATA_CHANGE", f"{change_type} {entity_type} - {entity_name}", change_record)
        
    def log_payment_event(
        self,
        payment_type: str,
        amount: Decimal,
        method: str,
        status: str,
        reference: str = None,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Log payment-related events.
        
        Args:
            payment_type: Type of payment (DEPOSIT, FULL_PAYMENT, REFUND, etc.)
            amount: Payment amount
            method: Payment method
            status: Payment status
            reference: Payment reference
            details: Additional payment details
        """
        payment_record = {
            "timestamp": datetime.now().isoformat(),
            "payment_type": payment_type,
            "amount": str(amount),
            "method": method,
            "status": status,
            "reference": reference,
            "details": details or {}
        }
        
        self.log_data["payment_events"].append(payment_record)
        self._log_event("PAYMENT_EVENT", f"{payment_type} - {amount} via {method}", payment_record)
        
    def log_error(
        self,
        error_type: str,
        error_message: str,
        error_details: Dict[str, Any] = None,
        stack_trace: str = None
    ) -> None:
        """
        Log errors that occur during transaction processing.
        
        Args:
            error_type: Type of error
            error_message: Error message
            error_details: Additional error details
            stack_trace: Stack trace if available
        """
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "error_details": error_details or {},
            "stack_trace": stack_trace
        }
        
        self.log_data["errors"].append(error_record)
        self._log_event("ERROR", f"{error_type}: {error_message}", error_record)
        
    def log_system_state_before(self, state_data: Dict[str, Any]) -> None:
        """
        Capture system state before transaction processing.
        
        Args:
            state_data: System state data
        """
        self.log_data["system_state"]["before"] = {
            **state_data,
            "timestamp": datetime.now().isoformat()
        }
        self._log_event("SYSTEM_STATE_CAPTURED", "System state before transaction captured")
        
    def log_system_state_after(self, state_data: Dict[str, Any]) -> None:
        """
        Capture system state after transaction processing.
        
        Args:
            state_data: System state data
        """
        self.log_data["system_state"]["after"] = {
            **state_data,
            "timestamp": datetime.now().isoformat()
        }
        self._log_event("SYSTEM_STATE_CAPTURED", "System state after transaction captured")
        
    def complete_transaction_log(self, status: str = "COMPLETED") -> Path:
        """
        Complete the transaction log and write to file.
        
        Args:
            status: Final transaction status
            
        Returns:
            Path to the created log file
        """
        if not self.current_log_file:
            raise ValueError("No transaction log session started")
            
        end_time = datetime.now()
        duration = (end_time - self.transaction_start_time).total_seconds()
        
        # Update transaction info
        self.log_data["transaction_info"].update({
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "status": status
        })
        
        self._log_event("TRANSACTION_COMPLETED", f"Transaction completed with status: {status}")
        
        # Generate markdown content
        markdown_content = self._generate_markdown_log()
        
        # Write to file
        with open(self.current_log_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        # Reset logger state
        log_file = self.current_log_file
        self._reset_logger_state()
        
        return log_file
        
    def _log_event(
        self, 
        event_type: str, 
        description: str, 
        data: Dict[str, Any] = None,
        user_id: str = None
    ) -> None:
        """Internal method to log events."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "data": data or {},
            "user_id": user_id
        }
        
        self.log_data["events"].append(event)
        
    def _generate_markdown_log(self) -> str:
        """Generate markdown formatted log content."""
        tx_info = self.log_data["transaction_info"]
        
        markdown = f"""# Transaction Log: {tx_info['operation_name'].upper()}

**Transaction ID**: `{tx_info['transaction_id']}`  
**Type**: {tx_info['transaction_type']}  
**Status**: {tx_info['status']}  
**Start Time**: {tx_info['start_time']}  
**End Time**: {tx_info.get('end_time', 'N/A')}  
**Duration**: {tx_info.get('duration_seconds', 0):.2f} seconds

---

## Transaction Events

| Timestamp | Event Type | Description |
|-----------|------------|-------------|
"""
        
        for event in self.log_data["events"]:
            timestamp = event["timestamp"].split("T")[1][:8]  # HH:MM:SS
            markdown += f"| {timestamp} | {event['event_type']} | {event['description']} |\n"
            
        # Inventory Changes
        if self.log_data["inventory_changes"]:
            markdown += "\n---\n\n## Inventory Changes\n\n"
            for change in self.log_data["inventory_changes"]:
                markdown += f"""### {change['item_name']} ({change['change_type']})
- **Item ID**: `{change['item_id']}`
- **Location**: {change['location_name'] or 'N/A'}
- **Quantity Before**: {change['quantity_before']}
- **Quantity After**: {change['quantity_after']}
- **Change**: {change['quantity_changed']}
- **Timestamp**: {change['timestamp']}

"""

        # Master Data Changes
        if self.log_data["master_data_changes"]:
            markdown += "\n---\n\n## Master Data Changes\n\n"
            for change in self.log_data["master_data_changes"]:
                markdown += f"""### {change['entity_type']}: {change['entity_name']}
- **Change Type**: {change['change_type']}
- **Entity ID**: `{change['entity_id']}`
- **Timestamp**: {change['timestamp']}

"""
                if change['old_values']:
                    markdown += "**Previous Values**:\n```json\n"
                    markdown += json.dumps(change['old_values'], indent=2)
                    markdown += "\n```\n\n"
                    
                if change['new_values']:
                    markdown += "**New Values**:\n```json\n"
                    markdown += json.dumps(change['new_values'], indent=2)
                    markdown += "\n```\n\n"

        # Payment Events
        if self.log_data["payment_events"]:
            markdown += "\n---\n\n## Payment Events\n\n"
            for payment in self.log_data["payment_events"]:
                markdown += f"""### {payment['payment_type']}
- **Amount**: {payment['amount']}
- **Method**: {payment['method']}
- **Status**: {payment['status']}
- **Reference**: {payment.get('reference', 'N/A')}
- **Timestamp**: {payment['timestamp']}

"""

        # System State Comparison
        if self.log_data["system_state"]["before"] or self.log_data["system_state"]["after"]:
            markdown += "\n---\n\n## System State Changes\n\n"
            
            if self.log_data["system_state"]["before"]:
                markdown += "### Before Transaction\n```json\n"
                markdown += json.dumps(self.log_data["system_state"]["before"], indent=2, default=str)
                markdown += "\n```\n\n"
                
            if self.log_data["system_state"]["after"]:
                markdown += "### After Transaction\n```json\n"
                markdown += json.dumps(self.log_data["system_state"]["after"], indent=2, default=str)
                markdown += "\n```\n\n"

        # Errors
        if self.log_data["errors"]:
            markdown += "\n---\n\n## Errors and Issues\n\n"
            for error in self.log_data["errors"]:
                markdown += f"""### {error['error_type']}
- **Message**: {error['error_message']}
- **Timestamp**: {error['timestamp']}

"""
                if error['error_details']:
                    markdown += "**Details**:\n```json\n"
                    markdown += json.dumps(error['error_details'], indent=2, default=str)
                    markdown += "\n```\n\n"
                    
                if error['stack_trace']:
                    markdown += "**Stack Trace**:\n```\n"
                    markdown += error['stack_trace']
                    markdown += "\n```\n\n"

        # Summary
        markdown += f"""---

## Summary

- **Total Events**: {len(self.log_data['events'])}
- **Inventory Changes**: {len(self.log_data['inventory_changes'])}
- **Master Data Changes**: {len(self.log_data['master_data_changes'])}
- **Payment Events**: {len(self.log_data['payment_events'])}
- **Errors**: {len(self.log_data['errors'])}

---

*Log generated on {datetime.now().isoformat()}*
"""
        
        return markdown
        
    def _reset_logger_state(self) -> None:
        """Reset logger state after completing a transaction log."""
        self.current_transaction_id = None
        self.current_log_file = None
        self.transaction_start_time = None
        self.log_data = {}


# Global transaction logger instance
transaction_logger = TransactionLogger()


def get_transaction_logger() -> TransactionLogger:
    """Get the global transaction logger instance."""
    return transaction_logger