"""
Rental-specific Pydantic schemas for API requests and responses.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from app.modules.transactions.base.models import RentalStatus, ReturnEventType, InspectionCondition


# Base schemas
class RentalItemBase(BaseModel):
    """Base schema for rental items."""
    transaction_line_id: UUID = Field(..., description="Transaction line ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity to return")


class InspectionDetailsBase(BaseModel):
    """Base schema for inspection details."""
    condition: InspectionCondition = Field(..., description="Item condition")
    has_damage: bool = Field(default=False, description="Whether item has damage")
    damage_description: Optional[str] = Field(None, description="Description of damage")
    damage_photos: Optional[List[str]] = Field(None, description="URLs of damage photos")
    damage_fee: Optional[Decimal] = Field(None, ge=0, description="Damage fee assessed")
    cleaning_fee: Optional[Decimal] = Field(None, ge=0, description="Cleaning fee assessed")
    replacement_required: bool = Field(default=False, description="Whether replacement is required")
    replacement_cost: Optional[Decimal] = Field(None, ge=0, description="Cost of replacement")
    return_to_stock: bool = Field(default=True, description="Whether item can be returned to stock")
    notes: Optional[str] = Field(None, description="Inspection notes")


# Request schemas
class RentalReturnInitiateRequest(BaseModel):
    """Schema for initiating a rental return."""
    return_date: date = Field(..., description="Date of return")
    items_to_return: List[RentalItemBase] = Field(..., min_length=1, description="Items being returned")
    notes: Optional[str] = Field(None, description="Return notes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "return_date": "2025-07-14",
                "items_to_return": [
                    {
                        "transaction_line_id": "550e8400-e29b-41d4-a716-446655440000",
                        "quantity": 2
                    }
                ],
                "notes": "Customer returning early"
            }
        }
    )


class RentalItemInspectionRequest(BaseModel):
    """Schema for recording item inspection."""
    transaction_line_id: UUID = Field(..., description="Transaction line ID")
    quantity_inspected: Decimal = Field(..., gt=0, description="Quantity inspected")
    inspection_details: InspectionDetailsBase = Field(..., description="Inspection details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_line_id": "550e8400-e29b-41d4-a716-446655440000",
                "quantity_inspected": 2,
                "inspection_details": {
                    "condition": "GOOD",
                    "has_damage": False,
                    "return_to_stock": True,
                    "notes": "Items in good condition"
                }
            }
        }
    )


class RentalReturnCompleteRequest(BaseModel):
    """Schema for completing a rental return."""
    payment_collected: Decimal = Field(default=0, ge=0, description="Payment collected")
    refund_issued: Decimal = Field(default=0, ge=0, description="Refund issued")
    receipt_number: Optional[str] = Field(None, description="Receipt number")
    notes: Optional[str] = Field(None, description="Completion notes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "payment_collected": 25.00,
                "refund_issued": 0,
                "receipt_number": "RCP-20250714-001",
                "notes": "Late fees collected"
            }
        }
    )


class RentalExtensionRequest(BaseModel):
    """Schema for extending rental period."""
    new_end_date: date = Field(..., description="New rental end date")
    reason: str = Field(..., min_length=1, max_length=200, description="Reason for extension")
    notes: Optional[str] = Field(None, description="Additional notes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_end_date": "2025-07-21",
                "reason": "Customer requested additional time",
                "notes": "Approved by manager"
            }
        }
    )


class RentalStatusUpdateRequest(BaseModel):
    """Schema for updating rental status."""
    new_status: RentalStatus = Field(..., description="New rental status")
    notes: Optional[str] = Field(None, description="Status change notes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_status": "LATE",
                "notes": "Automatically updated - overdue"
            }
        }
    )


# Response schemas
class RentalLifecycleResponse(BaseModel):
    """Schema for rental lifecycle response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transaction_id: UUID
    current_status: str
    last_status_change: datetime
    status_changed_by: Optional[UUID]
    total_returned_quantity: Decimal
    expected_return_date: Optional[date]
    total_late_fees: Decimal
    total_damage_fees: Decimal
    total_other_fees: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def total_fees(self) -> Decimal:
        """Calculate total fees."""
        return self.total_late_fees + self.total_damage_fees + self.total_other_fees


class RentalReturnEventResponse(BaseModel):
    """Schema for rental return event response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rental_lifecycle_id: UUID
    event_type: str
    event_date: date
    processed_by: Optional[UUID]
    processed_at: datetime
    items_returned: Optional[List[Dict[str, Any]]]
    total_quantity_returned: Decimal
    late_fees_charged: Decimal
    damage_fees_charged: Decimal
    other_fees_charged: Decimal
    payment_collected: Decimal
    refund_issued: Decimal
    new_return_date: Optional[date]
    extension_reason: Optional[str]
    notes: Optional[str]
    receipt_number: Optional[str]

    @property
    def total_fees_charged(self) -> Decimal:
        """Calculate total fees charged."""
        return self.late_fees_charged + self.damage_fees_charged + self.other_fees_charged

    @property
    def net_amount(self) -> Decimal:
        """Calculate net payment amount."""
        return self.payment_collected - self.refund_issued


class RentalItemInspectionResponse(BaseModel):
    """Schema for rental item inspection response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    return_event_id: UUID
    transaction_line_id: UUID
    quantity_inspected: Decimal
    condition: str
    inspected_by: Optional[UUID]
    inspected_at: datetime
    has_damage: bool
    damage_description: Optional[str]
    damage_photos: Optional[List[str]]
    damage_fee_assessed: Decimal
    cleaning_fee_assessed: Decimal
    replacement_required: bool
    replacement_cost: Optional[Decimal]
    return_to_stock: bool
    stock_location: Optional[str]
    inspection_notes: Optional[str]

    @property
    def total_fees_assessed(self) -> Decimal:
        """Calculate total fees assessed."""
        return (
            self.damage_fee_assessed + 
            self.cleaning_fee_assessed + 
            (self.replacement_cost or Decimal('0'))
        )


class RentalTransactionResponse(BaseModel):
    """Schema for rental transaction response with lifecycle info."""
    model_config = ConfigDict(from_attributes=True)

    # Transaction fields
    id: UUID
    transaction_number: str
    transaction_date: datetime
    customer_id: Optional[str]
    location_id: Optional[str]
    status: str
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    rental_period: Optional[int]
    rental_period_unit: Optional[str]
    total_amount: Decimal
    paid_amount: Decimal
    deposit_amount: Optional[Decimal]
    deposit_paid: bool
    current_rental_status: Optional[str]
    customer_advance_balance: Decimal
    
    # New delivery fields
    delivery_required: bool
    delivery_address: Optional[str]
    delivery_date: Optional[date]
    delivery_time: Optional[time]
    
    # New pickup fields
    pickup_required: bool
    pickup_date: Optional[date]
    pickup_time: Optional[time]

    # Lifecycle info
    lifecycle: Optional[RentalLifecycleResponse] = None
    
    @property
    def is_overdue(self) -> bool:
        """Check if rental is overdue."""
        if not self.rental_end_date:
            return False
        return self.rental_end_date < date.today()

    @property
    def days_overdue(self) -> int:
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.rental_end_date).days
    
    @property
    def reference_number(self) -> str:
        """Alias for transaction_number to match frontend expectations."""
        return self.transaction_number


class RentalDetailsResponse(BaseModel):
    """Comprehensive rental details response."""
    model_config = ConfigDict(from_attributes=True)

    transaction: RentalTransactionResponse
    lifecycle: RentalLifecycleResponse
    return_events: List[RentalReturnEventResponse]
    inspections: List[RentalItemInspectionResponse]
    total_fees: Decimal
    is_overdue: bool
    days_overdue: int


class RentalListResponse(BaseModel):
    """Schema for rental list response."""
    rentals: List[RentalTransactionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class RentalDashboardResponse(BaseModel):
    """Schema for rental dashboard statistics."""
    active_rentals: int
    overdue_rentals: int
    partial_returns: int
    completed_today: int
    total_fees_pending: Decimal
    total_fees_collected_today: Decimal

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "active_rentals": 45,
                "overdue_rentals": 8,
                "partial_returns": 3,
                "completed_today": 12,
                "total_fees_pending": 1250.00,
                "total_fees_collected_today": 350.00
            }
        }
    )


# Query parameters schemas
class RentalQueryParams(BaseModel):
    """Query parameters for rental listing."""
    customer_id: Optional[UUID] = Field(None, description="Filter by customer")
    location_id: Optional[UUID] = Field(None, description="Filter by location")
    status: Optional[RentalStatus] = Field(None, description="Filter by status")
    overdue_only: bool = Field(False, description="Show only overdue rentals")
    date_from: Optional[date] = Field(None, description="Filter by rental start date")
    date_to: Optional[date] = Field(None, description="Filter by rental end date")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class ReturnEventQueryParams(BaseModel):
    """Query parameters for return events."""
    event_type: Optional[ReturnEventType] = Field(None, description="Filter by event type")
    date_from: Optional[date] = Field(None, description="Filter by event date")
    date_to: Optional[date] = Field(None, description="Filter by event date")
    processed_by: Optional[UUID] = Field(None, description="Filter by processor")


# Utility schemas
class RentalFeeCalculation(BaseModel):
    """Schema for rental fee calculations."""
    base_amount: Decimal
    late_fee_days: int
    late_fee_rate: Decimal
    late_fee_amount: Decimal
    damage_fees: Decimal
    other_fees: Decimal
    total_fees: Decimal
    deposit_credit: Decimal
    advance_payment_credit: Decimal
    amount_due: Decimal

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "base_amount": 100.00,
                "late_fee_days": 3,
                "late_fee_rate": 0.05,
                "late_fee_amount": 15.00,
                "damage_fees": 25.00,
                "other_fees": 0.00,
                "total_fees": 40.00,
                "deposit_credit": 50.00,
                "advance_payment_credit": 0.00,
                "amount_due": 90.00
            }
        }
    )


class BatchStatusUpdateRequest(BaseModel):
    """Schema for batch status updates."""
    transaction_ids: List[UUID] = Field(..., min_length=1, description="Transaction IDs to update")
    new_status: RentalStatus = Field(..., description="New status for all transactions")
    notes: Optional[str] = Field(None, description="Batch update notes")


class BatchStatusUpdateResponse(BaseModel):
    """Schema for batch status update response."""
    updated_count: int
    failed_count: int
    failed_transactions: List[Dict[str, Any]]
    updated_transactions: List[UUID]