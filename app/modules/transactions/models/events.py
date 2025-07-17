"""
Transaction Event Models

This module defines models for tracking detailed transaction lifecycle events
and maintaining a comprehensive audit trail in the database.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from app.db.base import BaseModel, UUIDType


class TransactionEvent(BaseModel):
    """
    Model for tracking detailed transaction events and lifecycle changes.
    
    This model stores granular events that occur during transaction processing,
    providing a comprehensive audit trail for compliance and debugging.
    """
    
    __tablename__ = "transaction_events"
    
    # Core event information
    transaction_id = Column(
        UUIDType(), 
        ForeignKey("transaction_headers.id", ondelete="CASCADE"),
        nullable=False,
        comment="Transaction this event belongs to"
    )
    event_type = Column(
        String(50), 
        nullable=False, 
        comment="Type of event (CREATED, VALIDATED, PROCESSED, etc.)"
    )
    event_category = Column(
        String(30),
        nullable=False,
        default="GENERAL",
        comment="Event category (TRANSACTION, INVENTORY, PAYMENT, ERROR, etc.)"
    )
    
    # Event details
    description = Column(
        Text,
        nullable=False,
        comment="Human-readable description of the event"
    )
    event_data = Column(
        JSON,
        nullable=True,
        comment="Additional structured data related to the event"
    )
    
    # Context information
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered this event"
    )
    session_id = Column(
        String(100),
        nullable=True,
        comment="Session identifier for tracking user sessions"
    )
    ip_address = Column(
        String(45),
        nullable=True,
        comment="IP address of the client (supports IPv6)"
    )
    user_agent = Column(
        String(500),
        nullable=True,
        comment="User agent string from the request"
    )
    
    # System context
    service_name = Column(
        String(50),
        nullable=True,
        comment="Name of the service that generated this event"
    )
    operation_name = Column(
        String(100),
        nullable=True,
        comment="Specific operation being performed"
    )
    correlation_id = Column(
        String(100),
        nullable=True,
        comment="Correlation ID for tracking across services"
    )
    
    # Timing information
    event_timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When this event occurred"
    )
    processing_duration_ms = Column(
        String(20),
        nullable=True,
        comment="How long the operation took in milliseconds"
    )
    
    # Status and outcome
    status = Column(
        String(20),
        nullable=False,
        default="SUCCESS",
        comment="Event status (SUCCESS, FAILURE, WARNING, INFO)"
    )
    error_code = Column(
        String(50),
        nullable=True,
        comment="Error code if the event represents an error"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if the event represents an error"
    )
    
    # Related entities
    affected_entities = Column(
        JSON,
        nullable=True,
        comment="List of entities affected by this event"
    )
    
    # Relationships
    transaction = relationship("TransactionHeader", back_populates="events")
    user = relationship("User", lazy="select")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_transaction_events_transaction_id', 'transaction_id'),
        Index('idx_transaction_events_event_type', 'event_type'),
        Index('idx_transaction_events_category', 'event_category'),
        Index('idx_transaction_events_timestamp', 'event_timestamp'),
        Index('idx_transaction_events_user_id', 'user_id'),
        Index('idx_transaction_events_status', 'status'),
        Index('idx_transaction_events_operation', 'operation_name'),
        Index('idx_transaction_events_correlation', 'correlation_id'),
        # Composite indexes for common query patterns
        Index('idx_transaction_events_tx_type_time', 'transaction_id', 'event_type', 'event_timestamp'),
        Index('idx_transaction_events_category_status', 'event_category', 'status', 'event_timestamp'),
    )
    
    def __init__(
        self,
        transaction_id: str,
        event_type: str,
        description: str,
        event_category: str = "GENERAL",
        event_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a transaction event.
        
        Args:
            transaction_id: ID of the related transaction
            event_type: Type of event being logged
            description: Human-readable description
            event_category: Category of the event
            event_data: Additional structured data
            user_id: ID of the user who triggered the event
            **kwargs: Additional fields
        """
        super().__init__(**kwargs)
        self.transaction_id = transaction_id
        self.event_type = event_type
        self.event_category = event_category
        self.description = description
        self.event_data = event_data or {}
        self.user_id = user_id
        
    @classmethod
    def create_transaction_event(
        cls,
        transaction_id: str,
        event_type: str,
        description: str,
        category: str = "TRANSACTION",
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        status: str = "SUCCESS",
        duration_ms: Optional[int] = None
    ) -> "TransactionEvent":
        """
        Factory method to create a transaction event with standard fields.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Type of event
            description: Event description
            category: Event category
            data: Additional event data
            user_id: User who triggered the event
            operation: Operation being performed
            status: Event status
            duration_ms: Processing duration in milliseconds
            
        Returns:
            New TransactionEvent instance
        """
        return cls(
            transaction_id=transaction_id,
            event_type=event_type,
            description=description,
            event_category=category,
            event_data=data,
            user_id=user_id,
            operation_name=operation,
            status=status,
            processing_duration_ms=str(duration_ms) if duration_ms else None
        )
    
    @classmethod
    def create_inventory_event(
        cls,
        transaction_id: str,
        event_type: str,
        item_id: str,
        item_name: str,
        quantity_change: str,
        location_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> "TransactionEvent":
        """
        Factory method to create an inventory-related event.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Type of inventory event
            item_id: Item identifier
            item_name: Item name
            quantity_change: Quantity change (+/-)
            location_id: Location identifier
            user_id: User who triggered the event
            
        Returns:
            New TransactionEvent instance
        """
        data = {
            "item_id": item_id,
            "item_name": item_name,
            "quantity_change": quantity_change,
            "location_id": location_id
        }
        
        return cls(
            transaction_id=transaction_id,
            event_type=event_type,
            description=f"Inventory change: {item_name} ({quantity_change})",
            event_category="INVENTORY",
            event_data=data,
            user_id=user_id
        )
    
    @classmethod
    def create_payment_event(
        cls,
        transaction_id: str,
        event_type: str,
        amount: str,
        payment_method: str,
        payment_status: str,
        reference: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> "TransactionEvent":
        """
        Factory method to create a payment-related event.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Type of payment event
            amount: Payment amount
            payment_method: Payment method used
            payment_status: Payment status
            reference: Payment reference
            user_id: User who triggered the event
            
        Returns:
            New TransactionEvent instance
        """
        data = {
            "amount": amount,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "reference": reference
        }
        
        return cls(
            transaction_id=transaction_id,
            event_type=event_type,
            description=f"Payment event: {payment_method} {amount} - {payment_status}",
            event_category="PAYMENT",
            event_data=data,
            user_id=user_id
        )
    
    @classmethod
    def create_error_event(
        cls,
        transaction_id: str,
        error_type: str,
        error_message: str,
        error_code: Optional[str] = None,
        error_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> "TransactionEvent":
        """
        Factory method to create an error event.
        
        Args:
            transaction_id: Transaction identifier
            error_type: Type of error
            error_message: Error message
            error_code: Error code
            error_data: Additional error data
            user_id: User who triggered the event
            
        Returns:
            New TransactionEvent instance
        """
        return cls(
            transaction_id=transaction_id,
            event_type=error_type,
            description=error_message,
            event_category="ERROR",
            event_data=error_data,
            user_id=user_id,
            status="FAILURE",
            error_code=error_code,
            error_message=error_message
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary representation.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "id": str(self.id),
            "transaction_id": str(self.transaction_id),
            "event_type": self.event_type,
            "event_category": self.event_category,
            "description": self.description,
            "event_data": self.event_data,
            "user_id": str(self.user_id) if self.user_id else None,
            "event_timestamp": self.event_timestamp.isoformat(),
            "status": self.status,
            "operation_name": self.operation_name,
            "processing_duration_ms": self.processing_duration_ms,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "affected_entities": self.affected_entities
        }
    
    def __repr__(self) -> str:
        """String representation of the event."""
        return f"<TransactionEvent(id={self.id}, tx={self.transaction_id}, type={self.event_type})>"
