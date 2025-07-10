from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from uuid import UUID

from app.modules.rentals.models import (
    ReturnStatus, DamageLevel, ReturnType, InspectionStatus, 
    FeeType, ReturnLineStatus
)


class RentalReturnCreate(BaseModel):
    """Schema for creating a new rental return."""
    rental_transaction_id: UUID = Field(..., description="Rental transaction ID")
    return_date: date = Field(..., description="Return date")
    return_type: ReturnType = Field(default=ReturnType.FULL, description="Return type")
    return_status: ReturnStatus = Field(default=ReturnStatus.INITIATED, description="Return status")
    return_location_id: Optional[UUID] = Field(None, description="Return location ID")
    expected_return_date: Optional[date] = Field(None, description="Expected return date")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v, info):
        expected_date = info.data.get('expected_return_date')
        if expected_date and v < expected_date:
            pass  # Early return is allowed
        return v


class RentalReturnUpdate(BaseModel):
    """Schema for updating a rental return."""
    return_date: Optional[date] = Field(None, description="Return date")
    return_type: Optional[ReturnType] = Field(None, description="Return type")
    return_status: Optional[ReturnStatus] = Field(None, description="Return status")
    return_location_id: Optional[UUID] = Field(None, description="Return location ID")
    expected_return_date: Optional[date] = Field(None, description="Expected return date")
    processed_by: Optional[UUID] = Field(None, description="Processed by user ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v, info):
        expected_date = info.data.get('expected_return_date')
        if v and expected_date and v < expected_date:
            pass  # Early return is allowed
        return v


class RentalReturnResponse(BaseModel):
    """Schema for rental return response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_transaction_id: UUID
    return_date: date
    return_type: ReturnType
    return_status: ReturnStatus
    return_location_id: Optional[UUID]
    expected_return_date: Optional[date]
    processed_by: Optional[UUID]
    notes: Optional[str]
    total_late_fee: Decimal
    total_damage_fee: Decimal
    total_deposit_release: Decimal
    total_refund_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Return {self.id} - {self.return_type.value}"
    
    @computed_field
    @property
    def is_late(self) -> bool:
        if not self.expected_return_date:
            return False
        return self.return_date > self.expected_return_date
    
    @computed_field
    @property
    def days_late(self) -> int:
        if not self.is_late:
            return 0
        return (self.return_date - self.expected_return_date).days
    
    @computed_field
    @property
    def is_partial_return(self) -> bool:
        return self.return_type == ReturnType.PARTIAL
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        return self.return_status == ReturnStatus.COMPLETED
    
    @computed_field
    @property
    def total_fees(self) -> Decimal:
        return self.total_late_fee + self.total_damage_fee


class RentalReturnListResponse(BaseModel):
    """Schema for rental return list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_transaction_id: UUID
    return_date: date
    return_type: ReturnType
    return_status: ReturnStatus
    return_location_id: Optional[UUID]
    expected_return_date: Optional[date]
    total_late_fee: Decimal
    total_damage_fee: Decimal
    total_refund_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Return {self.id} - {self.return_type.value}"
    
    @computed_field
    @property
    def is_late(self) -> bool:
        if not self.expected_return_date:
            return False
        return self.return_date > self.expected_return_date
    
    @computed_field
    @property
    def total_fees(self) -> Decimal:
        return self.total_late_fee + self.total_damage_fee


class RentalReturnLineCreate(BaseModel):
    """Schema for creating a new rental return line."""
    inventory_unit_id: UUID = Field(..., description="Inventory unit ID")
    original_quantity: Decimal = Field(default=Decimal("1"), ge=0, description="Original quantity")
    returned_quantity: Decimal = Field(default=Decimal("0"), ge=0, description="Returned quantity")
    damage_level: DamageLevel = Field(default=DamageLevel.NONE, description="Damage level")
    line_status: ReturnLineStatus = Field(default=ReturnLineStatus.PENDING, description="Line status")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('returned_quantity')
    @classmethod
    def validate_returned_quantity(cls, v, info):
        original_quantity = info.data.get('original_quantity', Decimal("1"))
        if v > original_quantity:
            raise ValueError("Returned quantity cannot exceed original quantity")
        return v


class RentalReturnLineUpdate(BaseModel):
    """Schema for updating a rental return line."""
    original_quantity: Optional[Decimal] = Field(None, ge=0, description="Original quantity")
    returned_quantity: Optional[Decimal] = Field(None, ge=0, description="Returned quantity")
    damage_level: Optional[DamageLevel] = Field(None, description="Damage level")
    line_status: Optional[ReturnLineStatus] = Field(None, description="Line status")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('returned_quantity')
    @classmethod
    def validate_returned_quantity(cls, v, info):
        original_quantity = info.data.get('original_quantity')
        if v and original_quantity and v > original_quantity:
            raise ValueError("Returned quantity cannot exceed original quantity")
        return v


class RentalReturnLineResponse(BaseModel):
    """Schema for rental return line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_return_id: UUID
    inventory_unit_id: UUID
    original_quantity: Decimal
    returned_quantity: Decimal
    damage_level: DamageLevel
    line_status: ReturnLineStatus
    late_fee: Decimal
    damage_fee: Decimal
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Return Line {self.id}"
    
    @computed_field
    @property
    def remaining_quantity(self) -> Decimal:
        return self.original_quantity - self.returned_quantity
    
    @computed_field
    @property
    def is_fully_returned(self) -> bool:
        return self.returned_quantity >= self.original_quantity
    
    @computed_field
    @property
    def is_partially_returned(self) -> bool:
        return 0 < self.returned_quantity < self.original_quantity
    
    @computed_field
    @property
    def has_damage(self) -> bool:
        return self.damage_level != DamageLevel.NONE
    
    @computed_field
    @property
    def is_processed(self) -> bool:
        return self.line_status == ReturnLineStatus.PROCESSED
    
    @computed_field
    @property
    def total_fee(self) -> Decimal:
        return self.late_fee + self.damage_fee


class RentalReturnLineListResponse(BaseModel):
    """Schema for rental return line list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_return_id: UUID
    inventory_unit_id: UUID
    original_quantity: Decimal
    returned_quantity: Decimal
    damage_level: DamageLevel
    line_status: ReturnLineStatus
    late_fee: Decimal
    damage_fee: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Return Line {self.id}"
    
    @computed_field
    @property
    def total_fee(self) -> Decimal:
        return self.late_fee + self.damage_fee


class InspectionReportCreate(BaseModel):
    """Schema for creating a new inspection report."""
    inventory_unit_id: UUID = Field(..., description="Inventory unit ID")
    inspected_by: UUID = Field(..., description="Inspected by user ID")
    inspection_date: datetime = Field(..., description="Inspection date")
    inspection_status: InspectionStatus = Field(default=InspectionStatus.PENDING, description="Inspection status")
    damage_level: DamageLevel = Field(default=DamageLevel.NONE, description="Damage level found")
    damage_description: Optional[str] = Field(None, description="Damage description")
    repair_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Repair cost estimate")
    replacement_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Replacement cost estimate")
    inspection_notes: Optional[str] = Field(None, description="Inspection notes")
    
    @field_validator('damage_description')
    @classmethod
    def validate_damage_description(cls, v, info):
        damage_level = info.data.get('damage_level')
        if damage_level and damage_level != DamageLevel.NONE and not v:
            raise ValueError("Damage description is required when damage level is not NONE")
        return v


class InspectionReportUpdate(BaseModel):
    """Schema for updating an inspection report."""
    inspected_by: Optional[UUID] = Field(None, description="Inspected by user ID")
    inspection_date: Optional[datetime] = Field(None, description="Inspection date")
    inspection_status: Optional[InspectionStatus] = Field(None, description="Inspection status")
    damage_level: Optional[DamageLevel] = Field(None, description="Damage level found")
    damage_description: Optional[str] = Field(None, description="Damage description")
    repair_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Repair cost estimate")
    replacement_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Replacement cost estimate")
    inspection_notes: Optional[str] = Field(None, description="Inspection notes")
    
    @field_validator('damage_description')
    @classmethod
    def validate_damage_description(cls, v, info):
        damage_level = info.data.get('damage_level')
        if damage_level and damage_level != DamageLevel.NONE and not v:
            raise ValueError("Damage description is required when damage level is not NONE")
        return v


class InspectionReportResponse(BaseModel):
    """Schema for inspection report response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_return_id: UUID
    inventory_unit_id: UUID
    inspected_by: UUID
    inspection_date: datetime
    inspection_status: InspectionStatus
    damage_level: DamageLevel
    damage_description: Optional[str]
    repair_cost_estimate: Optional[Decimal]
    replacement_cost_estimate: Optional[Decimal]
    inspection_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Inspection {self.id}"
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        return self.inspection_status == InspectionStatus.COMPLETED
    
    @computed_field
    @property
    def has_damage(self) -> bool:
        return self.damage_level != DamageLevel.NONE
    
    @computed_field
    @property
    def recommended_fee(self) -> Decimal:
        """Get recommended fee based on damage level."""
        if self.damage_level == DamageLevel.NONE:
            return Decimal("0.00")
        elif self.damage_level == DamageLevel.MINOR:
            return self.repair_cost_estimate or Decimal("50.00")
        elif self.damage_level == DamageLevel.MODERATE:
            return self.repair_cost_estimate or Decimal("150.00")
        elif self.damage_level == DamageLevel.MAJOR:
            return self.repair_cost_estimate or Decimal("300.00")
        elif self.damage_level == DamageLevel.TOTAL_LOSS:
            return self.replacement_cost_estimate or Decimal("500.00")
        else:
            return Decimal("0.00")


class InspectionReportListResponse(BaseModel):
    """Schema for inspection report list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_return_id: UUID
    inventory_unit_id: UUID
    inspected_by: UUID
    inspection_date: datetime
    inspection_status: InspectionStatus
    damage_level: DamageLevel
    repair_cost_estimate: Optional[Decimal]
    replacement_cost_estimate: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Inspection {self.id}"
    
    @computed_field
    @property
    def has_damage(self) -> bool:
        return self.damage_level != DamageLevel.NONE


class ReturnStatusUpdate(BaseModel):
    """Schema for updating return status."""
    status: ReturnStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Status update notes")


class LineStatusUpdate(BaseModel):
    """Schema for updating return line status."""
    status: ReturnLineStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Status update notes")


class DamageAssessment(BaseModel):
    """Schema for damage assessment."""
    damage_level: DamageLevel = Field(..., description="Damage level")
    damage_description: Optional[str] = Field(None, description="Damage description")
    repair_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Repair cost estimate")
    replacement_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Replacement cost estimate")
    notes: Optional[str] = Field(None, description="Assessment notes")
    
    @field_validator('damage_description')
    @classmethod
    def validate_damage_description(cls, v, info):
        damage_level = info.data.get('damage_level')
        if damage_level and damage_level != DamageLevel.NONE and not v:
            raise ValueError("Damage description is required when damage level is not NONE")
        return v


class FeeCalculation(BaseModel):
    """Schema for fee calculation."""
    late_fee: Decimal = Field(default=Decimal("0.00"), ge=0, description="Late fee")
    damage_fee: Decimal = Field(default=Decimal("0.00"), ge=0, description="Damage fee")
    reason: Optional[str] = Field(None, description="Fee calculation reason")
    notes: Optional[str] = Field(None, description="Fee calculation notes")


class DepositCalculation(BaseModel):
    """Schema for deposit calculation."""
    original_deposit: Decimal = Field(..., ge=0, description="Original deposit amount")
    deposit_release: Decimal = Field(..., ge=0, description="Deposit release amount")
    reason: Optional[str] = Field(None, description="Deposit calculation reason")
    notes: Optional[str] = Field(None, description="Deposit calculation notes")


class InspectionCompletion(BaseModel):
    """Schema for completing inspection."""
    damage_level: DamageLevel = Field(..., description="Final damage level")
    damage_description: Optional[str] = Field(None, description="Damage description")
    repair_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Repair cost estimate")
    replacement_cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Replacement cost estimate")
    inspection_notes: Optional[str] = Field(None, description="Inspection notes")
    
    @field_validator('damage_description')
    @classmethod
    def validate_damage_description(cls, v, info):
        damage_level = info.data.get('damage_level')
        if damage_level and damage_level != DamageLevel.NONE and not v:
            raise ValueError("Damage description is required when damage level is not NONE")
        return v


class InspectionFailure(BaseModel):
    """Schema for failing inspection."""
    reason: str = Field(..., description="Failure reason")
    notes: Optional[str] = Field(None, description="Failure notes")


class RentalReturnWithLinesResponse(BaseModel):
    """Schema for rental return with lines response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    rental_transaction_id: UUID
    return_date: date
    return_type: ReturnType
    return_status: ReturnStatus
    return_location_id: Optional[UUID]
    expected_return_date: Optional[date]
    processed_by: Optional[UUID]
    notes: Optional[str]
    total_late_fee: Decimal
    total_damage_fee: Decimal
    total_deposit_release: Decimal
    total_refund_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    return_lines: List[RentalReturnLineResponse] = []
    inspection_reports: List[InspectionReportResponse] = []
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Return {self.id} - {self.return_type.value}"
    
    @computed_field
    @property
    def line_count(self) -> int:
        return len(self.return_lines)
    
    @computed_field
    @property
    def inspection_count(self) -> int:
        return len(self.inspection_reports)
    
    @computed_field
    @property
    def total_fees(self) -> Decimal:
        return self.total_late_fee + self.total_damage_fee


class RentalReturnSummary(BaseModel):
    """Schema for rental return summary."""
    total_returns: int
    completed_returns: int
    pending_returns: int
    cancelled_returns: int
    total_late_fees: Decimal
    total_damage_fees: Decimal
    total_refunds: Decimal
    returns_by_status: dict[str, int]
    returns_by_type: dict[str, int]
    average_processing_time: float  # in hours


class RentalReturnReport(BaseModel):
    """Schema for rental return report."""
    returns: List[RentalReturnListResponse]
    summary: RentalReturnSummary
    date_range: dict[str, date]


class RentalReturnSearch(BaseModel):
    """Schema for rental return search."""
    rental_transaction_id: Optional[UUID] = Field(None, description="Rental transaction ID")
    return_type: Optional[ReturnType] = Field(None, description="Return type")
    return_status: Optional[ReturnStatus] = Field(None, description="Return status")
    return_location_id: Optional[UUID] = Field(None, description="Return location ID")
    processed_by: Optional[UUID] = Field(None, description="Processed by user ID")
    date_from: Optional[date] = Field(None, description="Return date from")
    date_to: Optional[date] = Field(None, description="Return date to")
    expected_date_from: Optional[date] = Field(None, description="Expected return date from")
    expected_date_to: Optional[date] = Field(None, description="Expected return date to")
    is_late: Optional[bool] = Field(None, description="Filter by late returns")
    has_damage: Optional[bool] = Field(None, description="Filter by damage")
    
    @field_validator('date_to')
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and info.data.get('date_from') is not None:
            if v < info.data.get('date_from'):
                raise ValueError("Date to must be after date from")
        return v
    
    @field_validator('expected_date_to')
    @classmethod
    def validate_expected_date_range(cls, v, info):
        if v is not None and info.data.get('expected_date_from') is not None:
            if v < info.data.get('expected_date_from'):
                raise ValueError("Expected date to must be after expected date from")
        return v


class RentalDashboard(BaseModel):
    """Schema for rental dashboard."""
    active_rentals: int
    overdue_returns: int
    returns_due_today: int
    returns_due_this_week: int
    pending_inspections: int
    total_outstanding_fees: Decimal
    recent_returns: List[RentalReturnListResponse]
    overdue_returns_list: List[RentalReturnListResponse]


class RentalAnalytics(BaseModel):
    """Schema for rental analytics."""
    rental_performance: dict[str, Any]
    return_trends: dict[str, Any]
    damage_statistics: dict[str, Any]
    fee_analysis: dict[str, Any]
    customer_behavior: dict[str, Any]