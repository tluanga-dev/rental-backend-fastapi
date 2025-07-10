from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Text, Index
from sqlalchemy.orm import relationship, validates

from app.db.base import BaseModel, NamedModelMixin

if TYPE_CHECKING:
    from app.modules.inventory.models import Item


class UnitOfMeasurement(BaseModel, NamedModelMixin):
    """
    Unit of measurement model for items in the inventory.
    
    Attributes:
        name: Unit name (from NamedModelMixin)
        abbreviation: Unit abbreviation (e.g., "kg", "pcs", "m")
        description: Unit description (from NamedModelMixin)
        items: Items using this unit
    """
    
    __tablename__ = "units_of_measurement"
    
    # Override name column with specific constraints
    name = Column(String(50), nullable=False, unique=True, index=True, comment="Unit name")
    abbreviation = Column(String(10), nullable=True, unique=True, index=True, comment="Unit abbreviation")
    
    # Relationships
    items = relationship("Item", back_populates="unit_of_measurement", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_unit_name_active', 'name', 'is_active'),
        Index('idx_unit_abbreviation_active', 'abbreviation', 'is_active'),
    )
    
    def __init__(
        self,
        name: str,
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Unit of Measurement.
        
        Args:
            name: Unit name
            abbreviation: Unit abbreviation
            description: Unit description
            **kwargs: Additional BaseModel fields
        """
        super().__init__(name=name, description=description, **kwargs)
        self.abbreviation = abbreviation
        self._validate()
    
    def _validate(self):
        """Validate unit business rules."""
        # Name validation
        if not self.name or not self.name.strip():
            raise ValueError("Unit name cannot be empty")
        
        if len(self.name) > 50:
            raise ValueError("Unit name cannot exceed 50 characters")
        
        # Abbreviation validation
        if self.abbreviation:
            if not self.abbreviation.strip():
                raise ValueError("Unit abbreviation cannot be empty if provided")
            
            if len(self.abbreviation) > 10:
                raise ValueError("Unit abbreviation cannot exceed 10 characters")
        
        # Description validation
        if self.description and len(self.description) > 500:
            raise ValueError("Unit description cannot exceed 500 characters")
    
    @validates('name')
    def validate_name(self, key, value):
        """Validate unit name."""
        if not value or not value.strip():
            raise ValueError("Unit name cannot be empty")
        if len(value) > 50:
            raise ValueError("Unit name cannot exceed 50 characters")
        return value.strip()
    
    @validates('abbreviation')
    def validate_abbreviation(self, key, value):
        """Validate unit abbreviation."""
        if value is not None:
            if not value.strip():
                raise ValueError("Unit abbreviation cannot be empty if provided")
            if len(value) > 10:
                raise ValueError("Unit abbreviation cannot exceed 10 characters")
            return value.strip()
        return value
    
    @validates('description')
    def validate_description(self, key, value):
        """Validate unit description."""
        if value is not None:
            if len(value) > 500:
                raise ValueError("Unit description cannot exceed 500 characters")
            return value.strip() if value.strip() else None
        return value
    
    def update_details(
        self,
        name: Optional[str] = None,
        abbreviation: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """
        Update unit details.
        
        Args:
            name: New unit name
            abbreviation: New unit abbreviation
            description: New unit description
            updated_by: User making the update
        """
        if name is not None:
            if not name or not name.strip():
                raise ValueError("Unit name cannot be empty")
            if len(name) > 50:
                raise ValueError("Unit name cannot exceed 50 characters")
            self.name = name.strip()
        
        if abbreviation is not None:
            if abbreviation and not abbreviation.strip():
                raise ValueError("Unit abbreviation cannot be empty if provided")
            if abbreviation and len(abbreviation) > 10:
                raise ValueError("Unit abbreviation cannot exceed 10 characters")
            self.abbreviation = abbreviation.strip() if abbreviation else None
        
        if description is not None:
            if description and len(description) > 500:
                raise ValueError("Unit description cannot exceed 500 characters")
            self.description = description.strip() if description else None
        
        self.updated_by = updated_by
    
    def has_items(self) -> bool:
        """Check if unit has associated items."""
        return bool(self.items)
    
    def can_delete(self) -> bool:
        """Check if unit can be deleted."""
        # Can only delete if no items are associated
        return not self.has_items() and self.is_active
    
    @property
    def display_name(self) -> str:
        """Get display name for the unit."""
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name
    
    @property
    def item_count(self) -> int:
        """Get number of items using this unit."""
        return len(self.items) if self.items else 0
    
    def __str__(self) -> str:
        """String representation of unit."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of unit."""
        return (
            f"UnitOfMeasurement(id={self.id}, name='{self.name}', "
            f"abbreviation='{self.abbreviation}', active={self.is_active})"
        )