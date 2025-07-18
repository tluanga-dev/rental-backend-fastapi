"""
Rent Return Schemas

Pydantic schemas for rent return operations.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field
from uuid import UUID

from app.modules.transactions.base.schemas import (
    TransactionHeaderCreate,
    TransactionHeaderResponse,
    TransactionLineCreate,
    TransactionLineResponse,
    TransactionListResponse,
    TransactionHeaderUpdate,
)


class RentReturnLineCreate(TransactionLineCreate):
    """Schema for creating a rent return line item."""
    
    original_rental_line_id: UUID
    condition_on_return: str = Field(default="A", max_length=1)
    damage_noted: bool = False
    damage_description: Optional[str] = None
    damage_photos: Optional[str] = None
    repair_cost: Decimal = Field(default=Decimal("0"), ge=0)
    cleaning_notes: Optional[str] = None
    cleaning_fee: Decimal = Field(default=Decimal("0"), ge=0)
    return_to_inventory: bool = True
    inventory_location: Optional[str] = None


class RentReturnLineResponse(TransactionLineResponse):
    """Schema for rent return line item responses."""
    
    original_rental_line_id: UUID
    condition_on_return: str
    damage_noted: bool
    damage_description: Optional[str] = None
    damage_photos: Optional[str] = None
    repair_cost: Decimal
    cleaning_notes: Optional[str] = None
    cleaning_fee: Decimal
    return_to_inventory: bool
    inventory_location: Optional[str] = None
    
    @computed_field
    @property
    def total_fees(self) -> Decimal:
        """Calculate total fees for this item."""
        return self.repair_cost + self.cleaning_fee
    
    @computed_field
    @property
    def is_damaged(self) -> bool:
        """Check if item is damaged."""
        return self.damage_noted or self.repair_cost > 0
    
    @computed_field
    @property
    def needs_cleaning(self) -> bool:
        """Check if item needs cleaning."""
        return self.cleaning_fee > 0


class RentReturnCreate(TransactionHeaderCreate):
    """Schema for creating a new rent return."""
    
    return_number: Optional[str] = None
    original_rental_id: UUID
    return_date: date
    return_reason: Optional[str] = None
    
    # Inspection details
    inspection_completed: bool = False
    inspection_date: Optional[date] = None
    inspected_by: Optional[str] = None
    
    # Damage assessment
    total_damage_cost: Decimal = Field(default=Decimal("0"), ge=0)
    damage_deposit_deducted: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Cleaning fees
    cleaning_required: bool = False
    cleaning_cost: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Late fees
    late_return: bool = False
    late_fee_amount: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Deposit refund
    deposit_refund_amount: Decimal = Field(default=Decimal("0"), ge=0)
    deposit_refund_processed: bool = False
    deposit_refund_date: Optional[date] = None
    
    # Override to use RentReturnLineCreate
    transaction_lines: List[RentReturnLineCreate] = Field(default_factory=list)


class RentReturnUpdate(TransactionHeaderUpdate):
    """Schema for updating a rent return."""
    
    return_number: Optional[str] = None
    return_date: Optional[date] = None
    return_reason: Optional[str] = None
    
    # Inspection details
    inspection_completed: Optional[bool] = None
    inspection_date: Optional[date] = None
    inspected_by: Optional[str] = None
    
    # Damage assessment
    total_damage_cost: Optional[Decimal] = Field(None, ge=0)
    damage_deposit_deducted: Optional[Decimal] = Field(None, ge=0)
    
    # Cleaning fees
    cleaning_required: Optional[bool] = None
    cleaning_cost: Optional[Decimal] = Field(None, ge=0)
    
    # Late fees
    late_return: Optional[bool] = None
    late_fee_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Deposit refund
    deposit_refund_amount: Optional[Decimal] = Field(None, ge=0)
    deposit_refund_processed: Optional[bool] = None
    deposit_refund_date: Optional[date] = None


class RentReturnResponse(TransactionHeaderResponse):
    """Schema for rent return responses."""
    
    return_number: Optional[str] = None
    original_rental_id: UUID
    return_date: date
    return_reason: Optional[str] = None
    
    # Inspection details
    inspection_completed: bool
    inspection_date: Optional[date] = None
    inspected_by: Optional[str] = None
    
    # Damage assessment
    total_damage_cost: Decimal
    damage_deposit_deducted: Decimal
    
    # Cleaning fees
    cleaning_required: bool
    cleaning_cost: Decimal
    
    # Late fees
    late_return: bool
    late_fee_amount: Decimal
    
    # Deposit refund
    deposit_refund_amount: Decimal
    deposit_refund_processed: bool
    deposit_refund_date: Optional[date] = None
    
    # Override to use RentReturnLineResponse
    transaction_lines: List[RentReturnLineResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def total_deductions(self) -> Decimal:
        """Calculate total deductions from deposit."""
        return self.total_damage_cost + self.cleaning_cost + self.late_fee_amount
    
    @computed_field
    @property
    def net_refund_amount(self) -> Decimal:
        """Calculate net refund amount after deductions."""
        return max(Decimal("0"), self.deposit_refund_amount - self.total_deductions)
    
    @computed_field
    @property
    def has_damage(self) -> bool:
        """Check if return has damage."""
        return self.total_damage_cost > 0
    
    @computed_field
    @property
    def requires_cleaning(self) -> bool:
        """Check if return requires cleaning."""
        return self.cleaning_required or self.cleaning_cost > 0


class RentReturnListResponse(TransactionListResponse):
    """Response schema for rent return lists."""
    
    rent_returns: List[RentReturnResponse] = Field(alias="transactions")


class RentReturnInspectionRequest(BaseModel):
    """Schema for rent return inspection requests."""
    
    inspection_type: str = "RETURN"
    inspector_id: str
    overall_condition: str = Field(max_length=1)
    inspection_notes: Optional[str] = None
    damage_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    photos: Optional[List[str]] = Field(default_factory=list)
    documents: Optional[List[str]] = Field(default_factory=list)


class RentReturnInspectionResponse(BaseModel):
    """Schema for rent return inspection responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    return_id: UUID
    inspection_type: str
    inspection_date: datetime
    inspector_id: str
    overall_condition: str
    inspection_notes: Optional[str] = None
    total_damage_value: Decimal
    photos: Optional[str] = None
    documents: Optional[str] = None
    approved: bool
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None


class RentReturnReportRequest(BaseModel):
    """Schema for rent return report requests."""
    
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    customer_id: Optional[str] = None
    location_id: Optional[str] = None
    include_damage_only: bool = False
    include_late_returns_only: bool = False


class RentReturnReportResponse(BaseModel):
    """Schema for rent return report responses."""
    
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_returns: int
    total_damage_cost: Decimal
    total_cleaning_cost: Decimal
    total_late_fees: Decimal
    total_deposits_refunded: Decimal
    total_deposits_forfeited: Decimal
    average_return_processing_time: int
    
    # Breakdown by condition
    returns_by_condition: Dict[str, int] = Field(default_factory=dict)
    
    # Damage statistics
    damaged_returns: int
    damage_rate: Decimal
    
    # Late return statistics
    late_returns: int
    late_return_rate: Decimal
    
    rent_returns: List[RentReturnResponse] = Field(default_factory=list)


class DepositRefundRequest(BaseModel):
    """Schema for deposit refund requests."""
    
    refund_amount: Decimal = Field(gt=0)
    refund_date: date
    refund_method: str = "ORIGINAL_PAYMENT"
    refund_notes: Optional[str] = None


class DamageAssessmentRequest(BaseModel):
    """Schema for damage assessment requests."""
    
    line_id: UUID
    damage_description: str
    repair_cost: Decimal = Field(ge=0)
    photos: Optional[List[str]] = Field(default_factory=list)
    inspector_notes: Optional[str] = None