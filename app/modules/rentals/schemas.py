"""
Rental Schemas

Pydantic schemas for rental operations.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator
from uuid import UUID

from app.modules.transaction_base.schemas import (
    TransactionHeaderCreate,
    TransactionHeaderResponse,
    TransactionLineCreate,
    TransactionLineResponse,
    TransactionListResponse,
    TransactionHeaderUpdate,
)
from app.modules.transaction_base.models import RentalStatus, RentalPeriodUnit


class RentalLineCreate(TransactionLineCreate):
    """Schema for creating a rental line item."""
    
    item_serial_number: Optional[str] = None
    item_condition_out: str = Field(default="A", max_length=1)
    item_condition_in: Optional[str] = Field(None, max_length=1)
    damage_reported: bool = False
    damage_description: Optional[str] = None
    damage_cost: Decimal = Field(default=Decimal("0"), ge=0)
    item_late_fee: Decimal = Field(default=Decimal("0"), ge=0)


class RentalLineUpdate(BaseModel):
    """Schema for updating a rental line item."""
    
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    item_serial_number: Optional[str] = None
    item_condition_out: Optional[str] = Field(None, max_length=1)
    item_condition_in: Optional[str] = Field(None, max_length=1)
    damage_reported: Optional[bool] = None
    damage_description: Optional[str] = None
    damage_cost: Optional[Decimal] = Field(None, ge=0)
    item_late_fee: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class RentalLineResponse(TransactionLineResponse):
    """Schema for rental line item responses."""
    
    item_serial_number: Optional[str] = None
    item_condition_out: Optional[str] = None
    item_condition_in: Optional[str] = None
    damage_reported: bool
    damage_description: Optional[str] = None
    damage_cost: Decimal
    item_late_fee: Decimal
    
    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if this rental line is overdue."""
        if not self.rental_end_date:
            return False
        return self.rental_end_date < date.today() and not self.return_date
    
    @computed_field
    @property
    def days_overdue(self) -> int:
        """Calculate days overdue for this line."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.rental_end_date).days
    
    @computed_field
    @property
    def has_damage(self) -> bool:
        """Check if item has damage."""
        return self.damage_reported or self.damage_cost > 0
    
    @computed_field
    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost including damage and late fees."""
        return self.line_total + self.damage_cost + self.item_late_fee


class RentalCreate(TransactionHeaderCreate):
    """Schema for creating a new rental."""
    
    # Rental-specific fields
    rental_agreement_number: Optional[str] = None
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    
    # Rental terms
    rental_period: Optional[int] = Field(None, gt=0)
    rental_period_unit: Optional[RentalPeriodUnit] = None
    daily_rate: Optional[Decimal] = Field(None, ge=0)
    
    # Security deposit
    security_deposit_amount: Optional[Decimal] = Field(None, ge=0)
    security_deposit_paid: bool = False
    
    # Late fees
    late_fee_rate: Optional[Decimal] = Field(None, ge=0)
    late_fee_amount: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Extension tracking
    extension_count: int = Field(default=0, ge=0)
    max_extensions_allowed: int = Field(default=3, ge=0)
    
    # Rental status
    rental_status: RentalStatus = RentalStatus.ACTIVE
    
    # Override to use RentalLineCreate
    transaction_lines: List[RentalLineCreate] = Field(default_factory=list)
    
    @field_validator("rental_end_date")
    def validate_rental_dates(cls, v, values):
        """Validate that rental end date is after start date."""
        if v and values.get('rental_start_date') and v <= values['rental_start_date']:
            raise ValueError("Rental end date must be after start date")
        return v


class RentalUpdate(TransactionHeaderUpdate):
    """Schema for updating a rental."""
    
    # Rental-specific fields
    rental_agreement_number: Optional[str] = None
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    
    # Rental terms
    rental_period: Optional[int] = Field(None, gt=0)
    rental_period_unit: Optional[RentalPeriodUnit] = None
    daily_rate: Optional[Decimal] = Field(None, ge=0)
    
    # Security deposit
    security_deposit_amount: Optional[Decimal] = Field(None, ge=0)
    security_deposit_paid: Optional[bool] = None
    
    # Late fees
    late_fee_rate: Optional[Decimal] = Field(None, ge=0)
    late_fee_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Extension tracking
    extension_count: Optional[int] = Field(None, ge=0)
    max_extensions_allowed: Optional[int] = Field(None, ge=0)
    
    # Rental status
    rental_status: Optional[RentalStatus] = None


class RentalResponse(TransactionHeaderResponse):
    """Schema for rental responses."""
    
    # Rental-specific fields
    rental_agreement_number: Optional[str] = None
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    
    # Rental terms
    rental_period: Optional[int] = None
    rental_period_unit: Optional[RentalPeriodUnit] = None
    daily_rate: Optional[Decimal] = None
    
    # Security deposit
    security_deposit_amount: Optional[Decimal] = None
    security_deposit_paid: bool
    
    # Late fees
    late_fee_rate: Optional[Decimal] = None
    late_fee_amount: Decimal
    
    # Extension tracking
    extension_count: int
    max_extensions_allowed: int
    
    # Rental status
    rental_status: RentalStatus
    
    # Override to use RentalLineResponse
    transaction_lines: List[RentalLineResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if rental is overdue."""
        if not self.rental_end_date:
            return False
        return self.rental_end_date < date.today() and not self.actual_return_date
    
    @computed_field
    @property
    def days_overdue(self) -> int:
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.rental_end_date).days
    
    @computed_field
    @property
    def can_extend(self) -> bool:
        """Check if rental can be extended."""
        return self.extension_count < self.max_extensions_allowed
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if rental is completed."""
        return self.actual_return_date is not None
    
    @computed_field
    @property
    def total_damage_cost(self) -> Decimal:
        """Calculate total damage cost across all items."""
        return sum(line.damage_cost for line in self.transaction_lines)
    
    @computed_field
    @property
    def total_late_fees(self) -> Decimal:
        """Calculate total late fees."""
        return self.late_fee_amount + sum(line.item_late_fee for line in self.transaction_lines)
    
    @computed_field
    @property
    def has_damage(self) -> bool:
        """Check if rental has any damage."""
        return any(line.has_damage for line in self.transaction_lines)


class RentalLifecycleResponse(BaseModel):
    """Schema for rental lifecycle responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    transaction_id: UUID
    stage: str
    stage_entered_at: datetime
    
    # Operational fields
    checkout_completed: bool
    checkout_completed_at: Optional[datetime] = None
    checkin_completed: bool
    checkin_completed_at: Optional[datetime] = None
    
    # Inspection fields
    pre_rental_inspection: bool
    post_rental_inspection: bool
    
    # Status tracking
    current_status: str


class RentalExtensionRequest(BaseModel):
    """Schema for rental extension requests."""
    
    new_end_date: date
    extension_fee: Decimal = Field(ge=0)
    reason: Optional[str] = None
    
    @field_validator("new_end_date")
    def validate_new_end_date(cls, v):
        """Validate that new end date is in the future."""
        if v <= date.today():
            raise ValueError("New end date must be in the future")
        return v


class RentalExtensionResponse(BaseModel):
    """Schema for rental extension responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    rental_id: UUID
    extension_number: int
    original_end_date: date
    new_end_date: date
    extension_days: int
    extension_fee: Decimal
    requested_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    reason: Optional[str] = None


class RentalListResponse(TransactionListResponse):
    """Response schema for rental lists."""
    
    rentals: List[RentalResponse] = Field(alias="transactions")


class RentalReportRequest(BaseModel):
    """Schema for rental report requests."""
    
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    customer_id: Optional[str] = None
    location_id: Optional[str] = None
    rental_status: Optional[RentalStatus] = None
    include_completed: bool = True
    include_overdue_only: bool = False


class RentalReportResponse(BaseModel):
    """Schema for rental report responses."""
    
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_rentals: int
    total_revenue: Decimal
    total_damage_costs: Decimal
    total_late_fees: Decimal
    average_rental_amount: Decimal
    average_rental_duration: int
    
    # Breakdown by status
    active_rentals: int
    overdue_rentals: int
    completed_rentals: int
    extended_rentals: int
    
    # Performance metrics
    on_time_returns: int
    late_returns: int
    damage_incidents: int
    
    rentals: List[RentalResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def on_time_return_rate(self) -> Optional[Decimal]:
        """Calculate on-time return rate."""
        total_returns = self.on_time_returns + self.late_returns
        if total_returns == 0:
            return None
        return Decimal(self.on_time_returns) / Decimal(total_returns) * 100


class RentalDashboardResponse(BaseModel):
    """Schema for rental dashboard responses."""
    
    total_active_rentals: int
    total_overdue_rentals: int
    total_due_today: int
    total_due_this_week: int
    total_revenue_this_month: Decimal
    total_outstanding_late_fees: Decimal
    
    # Top metrics
    most_rented_items: List[Dict[str, Any]] = Field(default_factory=list)
    top_customers: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recent activities
    recent_rentals: List[RentalResponse] = Field(default_factory=list)
    recent_returns: List[RentalResponse] = Field(default_factory=list)


class RentalCheckoutRequest(BaseModel):
    """Schema for rental checkout requests."""
    
    checkout_notes: Optional[str] = None
    pre_rental_inspection_completed: bool = False
    items_condition: List[Dict[str, str]] = Field(default_factory=list)  # {item_id: condition}


class RentalCheckinRequest(BaseModel):
    """Schema for rental checkin requests."""
    
    return_date: date
    checkin_notes: Optional[str] = None
    post_rental_inspection_completed: bool = False
    items_condition: List[Dict[str, str]] = Field(default_factory=list)  # {item_id: condition}
    damage_reports: List[Dict[str, Any]] = Field(default_factory=list)  # {item_id, damage_desc, cost}


class RentalStatusUpdateRequest(BaseModel):
    """Schema for rental status update requests."""
    
    new_status: RentalStatus
    reason: Optional[str] = None
    notes: Optional[str] = None