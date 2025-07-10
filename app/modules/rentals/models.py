from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, Date, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.transactions.models import TransactionHeader
    from app.modules.master_data.locations.models import Location
    # from app.modules.auth.models import User  # Temporarily disabled
    from app.modules.inventory.models import InventoryUnit


class ReturnStatus(str, Enum):
    """Return status enumeration."""
    PENDING = "PENDING"
    INITIATED = "INITIATED"
    IN_INSPECTION = "IN_INSPECTION"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DamageLevel(str, Enum):
    """Damage level enumeration for returned items."""
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    TOTAL_LOSS = "TOTAL_LOSS"


class ReturnType(str, Enum):
    """Return type enumeration."""
    FULL = "FULL"
    PARTIAL = "PARTIAL"


class InspectionStatus(str, Enum):
    """Inspection status enumeration."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FeeType(str, Enum):
    """Fee type enumeration for return-related charges."""
    LATE_FEE = "LATE_FEE"
    DAMAGE_FEE = "DAMAGE_FEE"
    CLEANING_FEE = "CLEANING_FEE"
    REPLACEMENT_FEE = "REPLACEMENT_FEE"
    RESTOCKING_FEE = "RESTOCKING_FEE"


class ReturnLineStatus(str, Enum):
    """Return line status enumeration."""
    PENDING = "PENDING"
    INSPECTED = "INSPECTED"
    PROCESSED = "PROCESSED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"


class RentalReturn(BaseModel):
    """
    Rental return model for managing rental returns.
    
    Attributes:
        rental_transaction_id: Rental transaction ID
        return_date: Return date
        return_type: Return type (FULL, PARTIAL)
        return_status: Return status
        return_location_id: Return location ID
        expected_return_date: Expected return date
        processed_by: User who processed the return
        notes: Additional notes
        total_late_fee: Total late fee
        total_damage_fee: Total damage fee
        total_deposit_release: Total deposit release
        total_refund_amount: Total refund amount
        rental_transaction: Rental transaction relationship
        return_location: Return location relationship
        processed_by_user: Processed by user relationship
        return_lines: Return lines
        inspection_reports: Inspection reports
    """
    
    __tablename__ = "rental_returns"
    
    rental_transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False, comment="Rental transaction ID")
    return_date = Column(Date, nullable=False, comment="Return date")
    return_type = Column(String(20), nullable=False, default=ReturnType.FULL.value, comment="Return type")
    return_status = Column(String(20), nullable=False, default=ReturnStatus.INITIATED.value, comment="Return status")
    return_location_id = Column(UUIDType(), nullable=True, comment="Return location ID")  # ForeignKey("locations.id") - temporarily disabled
    expected_return_date = Column(Date, nullable=True, comment="Expected return date")
    processed_by = Column(UUIDType(), nullable=True, comment="Processed by user ID")  # ForeignKey("users.id") - temporarily disabled
    notes = Column(Text, nullable=True, comment="Additional notes")
    total_late_fee = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Total late fee")
    total_damage_fee = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Total damage fee")
    total_deposit_release = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Total deposit release")
    total_refund_amount = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Total refund amount")
    
    # Relationships
    rental_transaction = relationship("TransactionHeader", back_populates="rental_returns", lazy="select")
    # return_location = relationship("Location", back_populates="rental_returns", lazy="select")  # Temporarily disabled
    # processed_by_user = relationship("User", back_populates="processed_returns", lazy="select")  # Temporarily disabled
    return_lines = relationship("RentalReturnLine", back_populates="rental_return", lazy="select", cascade="all, delete-orphan")
    inspection_reports = relationship("InspectionReport", back_populates="rental_return", lazy="select", cascade="all, delete-orphan")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_rental_return_transaction', 'rental_transaction_id'),
        Index('idx_rental_return_date', 'return_date'),
        Index('idx_rental_return_type', 'return_type'),
        Index('idx_rental_return_status', 'return_status'),
        Index('idx_rental_return_location', 'return_location_id'),
        Index('idx_rental_return_processed_by', 'processed_by'),
        Index('idx_rental_return_expected_date', 'expected_return_date'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        rental_transaction_id: str,
        return_date: date,
        return_type: ReturnType = ReturnType.FULL,
        return_status: ReturnStatus = ReturnStatus.INITIATED,
        return_location_id: Optional[str] = None,
        expected_return_date: Optional[date] = None,
        processed_by: Optional[str] = None,
        notes: Optional[str] = None,
        total_late_fee: Decimal = Decimal("0.00"),
        total_damage_fee: Decimal = Decimal("0.00"),
        total_deposit_release: Decimal = Decimal("0.00"),
        total_refund_amount: Decimal = Decimal("0.00"),
        **kwargs
    ):
        """
        Initialize a Rental Return.
        
        Args:
            rental_transaction_id: Rental transaction ID
            return_date: Return date
            return_type: Return type
            return_status: Return status
            return_location_id: Return location ID
            expected_return_date: Expected return date
            processed_by: User who processed the return
            notes: Additional notes
            total_late_fee: Total late fee
            total_damage_fee: Total damage fee
            total_deposit_release: Total deposit release
            total_refund_amount: Total refund amount
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.rental_transaction_id = rental_transaction_id
        self.return_date = return_date
        self.return_type = return_type.value if isinstance(return_type, ReturnType) else return_type
        self.return_status = return_status.value if isinstance(return_status, ReturnStatus) else return_status
        self.return_location_id = return_location_id
        self.expected_return_date = expected_return_date
        self.processed_by = processed_by
        self.notes = notes
        self.total_late_fee = total_late_fee
        self.total_damage_fee = total_damage_fee
        self.total_deposit_release = total_deposit_release
        self.total_refund_amount = total_refund_amount
        self._validate()
    
    def _validate(self):
        """Validate rental return business rules."""
        # Return date validation
        if not self.return_date:
            raise ValueError("Return date is required")
        
        # Return type validation
        if self.return_type not in [rt.value for rt in ReturnType]:
            raise ValueError(f"Invalid return type: {self.return_type}")
        
        # Return status validation
        if self.return_status not in [rs.value for rs in ReturnStatus]:
            raise ValueError(f"Invalid return status: {self.return_status}")
        
        # Date validation
        if self.expected_return_date and self.return_date < self.expected_return_date:
            pass  # Early return is allowed
        
        # Amount validation
        if self.total_late_fee < 0:
            raise ValueError("Total late fee cannot be negative")
        
        if self.total_damage_fee < 0:
            raise ValueError("Total damage fee cannot be negative")
        
        if self.total_deposit_release < 0:
            raise ValueError("Total deposit release cannot be negative")
        
        if self.total_refund_amount < 0:
            raise ValueError("Total refund amount cannot be negative")
    
    def is_late(self) -> bool:
        """Check if the return is late."""
        if not self.expected_return_date:
            return False
        return self.return_date > self.expected_return_date
    
    def days_late(self) -> int:
        """Calculate number of days late."""
        if not self.is_late():
            return 0
        return (self.return_date - self.expected_return_date).days
    
    def is_partial_return(self) -> bool:
        """Check if this is a partial return."""
        return self.return_type == ReturnType.PARTIAL.value
    
    def is_completed(self) -> bool:
        """Check if the return is completed."""
        return self.return_status == ReturnStatus.COMPLETED.value
    
    def can_transition_to(self, new_status: ReturnStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            ReturnStatus.INITIATED.value: [
                ReturnStatus.IN_INSPECTION.value,
                ReturnStatus.CANCELLED.value
            ],
            ReturnStatus.IN_INSPECTION.value: [
                ReturnStatus.PARTIALLY_COMPLETED.value,
                ReturnStatus.COMPLETED.value,
                ReturnStatus.CANCELLED.value
            ],
            ReturnStatus.PARTIALLY_COMPLETED.value: [
                ReturnStatus.IN_INSPECTION.value,
                ReturnStatus.COMPLETED.value,
                ReturnStatus.CANCELLED.value
            ],
            ReturnStatus.COMPLETED.value: [],
            ReturnStatus.CANCELLED.value: []
        }
        
        return new_status.value in valid_transitions.get(self.return_status, [])
    
    def update_status(self, new_status: ReturnStatus, updated_by: Optional[str] = None):
        """Update return status with validation."""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.return_status} to {new_status.value}")
        
        self.return_status = new_status.value
        self.updated_by = updated_by
    
    def calculate_totals(self):
        """Recalculate totals from return lines."""
        if not self.return_lines:
            self.total_late_fee = Decimal("0.00")
            self.total_damage_fee = Decimal("0.00")
            self.total_deposit_release = Decimal("0.00")
            self.total_refund_amount = Decimal("0.00")
            return
        
        # Calculate totals from lines
        self.total_late_fee = sum(line.late_fee for line in self.return_lines)
        self.total_damage_fee = sum(line.damage_fee for line in self.return_lines)
        
        # Calculate refund amount
        self.total_refund_amount = self.total_deposit_release - self.total_late_fee - self.total_damage_fee
        self.total_refund_amount = max(self.total_refund_amount, Decimal("0.00"))
    
    def finalize_return(self, updated_by: Optional[str] = None):
        """Finalize the return process."""
        if not self.return_lines:
            raise ValueError("Cannot finalize return without return lines")
        
        # Validate all lines have been processed
        for line in self.return_lines:
            if line.line_status != ReturnLineStatus.PROCESSED.value:
                raise ValueError(f"Line {line.id} has not been processed")
        
        self.update_status(ReturnStatus.COMPLETED, updated_by)
        self.calculate_totals()
    
    def cancel_return(self, reason: Optional[str] = None, updated_by: Optional[str] = None):
        """Cancel the return."""
        if self.return_status == ReturnStatus.COMPLETED.value:
            raise ValueError("Cannot cancel completed return")
        
        self.return_status = ReturnStatus.CANCELLED.value
        
        if reason:
            cancel_note = f"\n[CANCELLED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {reason}"
            self.notes = (self.notes or "") + cancel_note
        
        self.updated_by = updated_by
    
    @property
    def display_name(self) -> str:
        """Get return display name."""
        return f"Return {self.id} - {self.return_type}"
    
    @property
    def line_count(self) -> int:
        """Get number of return lines."""
        return len(self.return_lines) if self.return_lines else 0
    
    def __str__(self) -> str:
        """String representation of rental return."""
        return f"RentalReturn({self.id}: {self.return_type} - {self.return_status})"
    
    def __repr__(self) -> str:
        """Developer representation of rental return."""
        return (
            f"RentalReturn(id={self.id}, transaction_id={self.rental_transaction_id}, "
            f"type='{self.return_type}', status='{self.return_status}', "
            f"return_date={self.return_date}, active={self.is_active})"
        )


class RentalReturnLine(BaseModel):
    """
    Rental return line model for managing individual items in a return.
    
    Attributes:
        rental_return_id: Rental return ID
        inventory_unit_id: Inventory unit ID
        original_quantity: Original quantity
        returned_quantity: Returned quantity
        damage_level: Damage level
        line_status: Line status
        late_fee: Late fee for this line
        damage_fee: Damage fee for this line
        notes: Additional notes
        rental_return: Rental return relationship
        inventory_unit: Inventory unit relationship
    """
    
    __tablename__ = "rental_return_lines"
    
    rental_return_id = Column(UUIDType(), ForeignKey("rental_returns.id"), nullable=False, comment="Rental return ID")
    inventory_unit_id = Column(UUIDType(), ForeignKey("inventory_units.id"), nullable=False, comment="Inventory unit ID")
    original_quantity = Column(Numeric(10, 2), nullable=False, default=1, comment="Original quantity")
    returned_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Returned quantity")
    damage_level = Column(String(20), nullable=False, default=DamageLevel.NONE.value, comment="Damage level")
    line_status = Column(String(20), nullable=False, default=ReturnLineStatus.PENDING.value, comment="Line status")
    late_fee = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Late fee for this line")
    damage_fee = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Damage fee for this line")
    notes = Column(Text, nullable=True, comment="Additional notes")
    
    # Relationships
    rental_return = relationship("RentalReturn", back_populates="return_lines", lazy="select")
    inventory_unit = relationship("InventoryUnit", back_populates="return_lines", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_rental_return_line_return', 'rental_return_id'),
        Index('idx_rental_return_line_inventory_unit', 'inventory_unit_id'),
        Index('idx_rental_return_line_damage_level', 'damage_level'),
        Index('idx_rental_return_line_status', 'line_status'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        rental_return_id: str,
        inventory_unit_id: str,
        original_quantity: Decimal = Decimal("1"),
        returned_quantity: Decimal = Decimal("0"),
        damage_level: DamageLevel = DamageLevel.NONE,
        line_status: ReturnLineStatus = ReturnLineStatus.PENDING,
        late_fee: Decimal = Decimal("0.00"),
        damage_fee: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Rental Return Line.
        
        Args:
            rental_return_id: Rental return ID
            inventory_unit_id: Inventory unit ID
            original_quantity: Original quantity
            returned_quantity: Returned quantity
            damage_level: Damage level
            line_status: Line status
            late_fee: Late fee for this line
            damage_fee: Damage fee for this line
            notes: Additional notes
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.rental_return_id = rental_return_id
        self.inventory_unit_id = inventory_unit_id
        self.original_quantity = original_quantity
        self.returned_quantity = returned_quantity
        self.damage_level = damage_level.value if isinstance(damage_level, DamageLevel) else damage_level
        self.line_status = line_status.value if isinstance(line_status, ReturnLineStatus) else line_status
        self.late_fee = late_fee
        self.damage_fee = damage_fee
        self.notes = notes
        self._validate()
    
    def _validate(self):
        """Validate rental return line business rules."""
        # Quantity validation
        if self.original_quantity < 0:
            raise ValueError("Original quantity cannot be negative")
        
        if self.returned_quantity < 0:
            raise ValueError("Returned quantity cannot be negative")
        
        if self.returned_quantity > self.original_quantity:
            raise ValueError("Returned quantity cannot exceed original quantity")
        
        # Damage level validation
        if self.damage_level not in [dl.value for dl in DamageLevel]:
            raise ValueError(f"Invalid damage level: {self.damage_level}")
        
        # Line status validation
        if self.line_status not in [ls.value for ls in ReturnLineStatus]:
            raise ValueError(f"Invalid line status: {self.line_status}")
        
        # Fee validation
        if self.late_fee < 0:
            raise ValueError("Late fee cannot be negative")
        
        if self.damage_fee < 0:
            raise ValueError("Damage fee cannot be negative")
    
    def set_late_fee(self, late_fee: Decimal):
        """Set late fee for this line."""
        if late_fee < 0:
            raise ValueError("Late fee cannot be negative")
        self.late_fee = late_fee
    
    def set_damage_fee(self, damage_fee: Decimal):
        """Set damage fee for this line."""
        if damage_fee < 0:
            raise ValueError("Damage fee cannot be negative")
        self.damage_fee = damage_fee
    
    def update_status(self, new_status: ReturnLineStatus, updated_by: Optional[str] = None):
        """Update line status."""
        if new_status.value not in [ls.value for ls in ReturnLineStatus]:
            raise ValueError(f"Invalid line status: {new_status.value}")
        
        self.line_status = new_status.value
        self.updated_by = updated_by
    
    def is_processed(self) -> bool:
        """Check if line is processed."""
        return self.line_status == ReturnLineStatus.PROCESSED.value
    
    def is_fully_returned(self) -> bool:
        """Check if all items are returned."""
        return self.returned_quantity >= self.original_quantity
    
    def is_partially_returned(self) -> bool:
        """Check if some items are returned."""
        return 0 < self.returned_quantity < self.original_quantity
    
    def has_damage(self) -> bool:
        """Check if item has damage."""
        return self.damage_level != DamageLevel.NONE.value
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Get remaining quantity to return."""
        return self.original_quantity - self.returned_quantity
    
    @property
    def total_fee(self) -> Decimal:
        """Get total fee for this line."""
        return self.late_fee + self.damage_fee
    
    @property
    def display_name(self) -> str:
        """Get line display name."""
        return f"Return Line {self.id}"
    
    def __str__(self) -> str:
        """String representation of rental return line."""
        return f"RentalReturnLine({self.id}: {self.returned_quantity}/{self.original_quantity})"
    
    def __repr__(self) -> str:
        """Developer representation of rental return line."""
        return (
            f"RentalReturnLine(id={self.id}, return_id={self.rental_return_id}, "
            f"inventory_unit_id={self.inventory_unit_id}, "
            f"quantity={self.returned_quantity}/{self.original_quantity}, "
            f"damage='{self.damage_level}', active={self.is_active})"
        )


class InspectionReport(BaseModel):
    """
    Inspection report model for documenting item inspections.
    
    Attributes:
        rental_return_id: Rental return ID
        inventory_unit_id: Inventory unit ID
        inspected_by: User who performed inspection
        inspection_date: Inspection date
        inspection_status: Inspection status
        damage_level: Damage level found
        damage_description: Damage description
        repair_cost_estimate: Repair cost estimate
        replacement_cost_estimate: Replacement cost estimate
        inspection_notes: Inspection notes
        rental_return: Rental return relationship
        inventory_unit: Inventory unit relationship
        inspected_by_user: Inspected by user relationship
    """
    
    __tablename__ = "inspection_reports"
    
    rental_return_id = Column(UUIDType(), ForeignKey("rental_returns.id"), nullable=False, comment="Rental return ID")
    inventory_unit_id = Column(UUIDType(), ForeignKey("inventory_units.id"), nullable=False, comment="Inventory unit ID")
    inspected_by = Column(UUIDType(), nullable=False, comment="Inspected by user ID")  # ForeignKey("users.id") - temporarily disabled
    inspection_date = Column(DateTime, nullable=False, comment="Inspection date")
    inspection_status = Column(String(20), nullable=False, default=InspectionStatus.PENDING.value, comment="Inspection status")
    damage_level = Column(String(20), nullable=False, default=DamageLevel.NONE.value, comment="Damage level found")
    damage_description = Column(Text, nullable=True, comment="Damage description")
    repair_cost_estimate = Column(Numeric(10, 2), nullable=True, comment="Repair cost estimate")
    replacement_cost_estimate = Column(Numeric(10, 2), nullable=True, comment="Replacement cost estimate")
    inspection_notes = Column(Text, nullable=True, comment="Inspection notes")
    
    # Relationships
    rental_return = relationship("RentalReturn", back_populates="inspection_reports", lazy="select")
    inventory_unit = relationship("InventoryUnit", back_populates="inspection_reports", lazy="select")
    # inspected_by_user = relationship("User", back_populates="inspection_reports", lazy="select")  # Temporarily disabled
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_inspection_report_return', 'rental_return_id'),
        Index('idx_inspection_report_inventory_unit', 'inventory_unit_id'),
        Index('idx_inspection_report_inspected_by', 'inspected_by'),
        Index('idx_inspection_report_date', 'inspection_date'),
        Index('idx_inspection_report_status', 'inspection_status'),
        Index('idx_inspection_report_damage_level', 'damage_level'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        rental_return_id: str,
        inventory_unit_id: str,
        inspected_by: str,
        inspection_date: datetime,
        inspection_status: InspectionStatus = InspectionStatus.PENDING,
        damage_level: DamageLevel = DamageLevel.NONE,
        damage_description: Optional[str] = None,
        repair_cost_estimate: Optional[Decimal] = None,
        replacement_cost_estimate: Optional[Decimal] = None,
        inspection_notes: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize an Inspection Report.
        
        Args:
            rental_return_id: Rental return ID
            inventory_unit_id: Inventory unit ID
            inspected_by: User who performed inspection
            inspection_date: Inspection date
            inspection_status: Inspection status
            damage_level: Damage level found
            damage_description: Damage description
            repair_cost_estimate: Repair cost estimate
            replacement_cost_estimate: Replacement cost estimate
            inspection_notes: Inspection notes
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.rental_return_id = rental_return_id
        self.inventory_unit_id = inventory_unit_id
        self.inspected_by = inspected_by
        self.inspection_date = inspection_date
        self.inspection_status = inspection_status.value if isinstance(inspection_status, InspectionStatus) else inspection_status
        self.damage_level = damage_level.value if isinstance(damage_level, DamageLevel) else damage_level
        self.damage_description = damage_description
        self.repair_cost_estimate = repair_cost_estimate
        self.replacement_cost_estimate = replacement_cost_estimate
        self.inspection_notes = inspection_notes
        self._validate()
    
    def _validate(self):
        """Validate inspection report business rules."""
        # Inspection status validation
        if self.inspection_status not in [is_status.value for is_status in InspectionStatus]:
            raise ValueError(f"Invalid inspection status: {self.inspection_status}")
        
        # Damage level validation
        if self.damage_level not in [dl.value for dl in DamageLevel]:
            raise ValueError(f"Invalid damage level: {self.damage_level}")
        
        # Cost validation
        if self.repair_cost_estimate is not None and self.repair_cost_estimate < 0:
            raise ValueError("Repair cost estimate cannot be negative")
        
        if self.replacement_cost_estimate is not None and self.replacement_cost_estimate < 0:
            raise ValueError("Replacement cost estimate cannot be negative")
        
        # Damage description validation
        if self.damage_level != DamageLevel.NONE.value and not self.damage_description:
            raise ValueError("Damage description is required when damage level is not NONE")
    
    def complete_inspection(self, updated_by: Optional[str] = None):
        """Complete the inspection."""
        if self.inspection_status == InspectionStatus.COMPLETED.value:
            raise ValueError("Inspection is already completed")
        
        self.inspection_status = InspectionStatus.COMPLETED.value
        self.updated_by = updated_by
    
    def fail_inspection(self, reason: str, updated_by: Optional[str] = None):
        """Fail the inspection."""
        if self.inspection_status == InspectionStatus.COMPLETED.value:
            raise ValueError("Cannot fail completed inspection")
        
        self.inspection_status = InspectionStatus.FAILED.value
        
        # Add failure reason to notes
        failure_note = f"\n[FAILED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {reason}"
        self.inspection_notes = (self.inspection_notes or "") + failure_note
        
        self.updated_by = updated_by
    
    def is_completed(self) -> bool:
        """Check if inspection is completed."""
        return self.inspection_status == InspectionStatus.COMPLETED.value
    
    def has_damage(self) -> bool:
        """Check if inspection found damage."""
        return self.damage_level != DamageLevel.NONE.value
    
    def get_recommended_fee(self) -> Decimal:
        """Get recommended fee based on damage level."""
        if self.damage_level == DamageLevel.NONE.value:
            return Decimal("0.00")
        elif self.damage_level == DamageLevel.MINOR.value:
            return self.repair_cost_estimate or Decimal("50.00")
        elif self.damage_level == DamageLevel.MODERATE.value:
            return self.repair_cost_estimate or Decimal("150.00")
        elif self.damage_level == DamageLevel.MAJOR.value:
            return self.repair_cost_estimate or Decimal("300.00")
        elif self.damage_level == DamageLevel.TOTAL_LOSS.value:
            return self.replacement_cost_estimate or Decimal("500.00")
        else:
            return Decimal("0.00")
    
    @property
    def display_name(self) -> str:
        """Get inspection display name."""
        return f"Inspection {self.id}"
    
    def __str__(self) -> str:
        """String representation of inspection report."""
        return f"InspectionReport({self.id}: {self.damage_level} - {self.inspection_status})"
    
    def __repr__(self) -> str:
        """Developer representation of inspection report."""
        return (
            f"InspectionReport(id={self.id}, return_id={self.rental_return_id}, "
            f"inventory_unit_id={self.inventory_unit_id}, "
            f"damage='{self.damage_level}', status='{self.inspection_status}', "
            f"active={self.is_active})"
        )