"""
Transaction metadata model for storing type-specific return data.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import BaseModel, UUIDType


class TransactionMetadata(BaseModel):
    """
    Transaction metadata model for storing flexible type-specific data.
    
    This model allows storing type-specific properties for returns and other
    transaction types without modifying the core transaction schema.
    """
    
    __tablename__ = "transaction_metadata"
    
    # Core fields
    transaction_id = Column(
        UUIDType(), 
        ForeignKey("transaction_headers.id"), 
        nullable=False,
        comment="Transaction ID this metadata belongs to"
    )
    metadata_type = Column(
        String(50), 
        nullable=False, 
        comment="Type of metadata (e.g., RETURN_SALE_RETURN)"
    )
    metadata_content = Column(
        JSONB, 
        nullable=False, 
        comment="JSON content with type-specific data"
    )
    
    # Relationships
    transaction = relationship(
        "TransactionHeader", 
        back_populates="metadata_entries",
        lazy="select"
    )
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_transaction_metadata_txn_id', 'transaction_id'),
        Index('idx_transaction_metadata_type', 'metadata_type'),
        Index('idx_transaction_metadata_content', 'metadata_content', postgresql_using='gin'),
    )
    
    def __init__(
        self,
        transaction_id: str,
        metadata_type: str,
        metadata_content: Dict[str, Any],
        **kwargs
    ):
        """
        Initialize transaction metadata.
        
        Args:
            transaction_id: Transaction this metadata belongs to
            metadata_type: Type identifier for the metadata
            metadata_content: Dictionary of type-specific data
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.transaction_id = transaction_id
        self.metadata_type = metadata_type
        self.metadata_content = metadata_content
        self._validate()
    
    def _validate(self):
        """Validate metadata."""
        if not self.transaction_id:
            raise ValueError("Transaction ID is required")
        
        if not self.metadata_type:
            raise ValueError("Metadata type is required")
        
        if not isinstance(self.metadata_content, dict):
            raise ValueError("Metadata content must be a dictionary")
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from metadata content.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from metadata or default
        """
        return self.metadata_content.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set a value in metadata content.
        
        Args:
            key: Key to set
            value: Value to store
        """
        if self.metadata_content is None:
            self.metadata_content = {}
        self.metadata_content[key] = value
    
    def update_values(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple values in metadata content.
        
        Args:
            updates: Dictionary of updates to apply
        """
        if self.metadata_content is None:
            self.metadata_content = {}
        self.metadata_content.update(updates)
    
    @property
    def is_return_metadata(self) -> bool:
        """Check if this is return-related metadata."""
        return self.metadata_type.startswith("RETURN_")
    
    @property
    def return_type(self) -> Optional[str]:
        """Get return type if this is return metadata."""
        if self.is_return_metadata:
            return self.metadata_type.replace("RETURN_", "")
        return None
    
    def __str__(self) -> str:
        """String representation."""
        return f"TransactionMetadata({self.id}: {self.metadata_type})"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"TransactionMetadata(id={self.id}, "
            f"transaction_id={self.transaction_id}, "
            f"type='{self.metadata_type}', "
            f"content_keys={list(self.metadata_content.keys()) if self.metadata_content else []})"
        )