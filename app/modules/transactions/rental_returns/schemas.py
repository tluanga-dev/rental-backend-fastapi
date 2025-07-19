"""
Rental Returns Schemas

Schemas for rental return transactions, inspections, and damage assessments.
"""

from typing import Literal, Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


# Rental return specific line item
class RentalReturnLineItem(BaseModel):
    """Rental return specific line item properties."""
    
    original_line_id: UUID = Field(..., description="Original transaction line ID")
    return_quantity: Decimal = Field(..., gt=0, description="Quantity to return")
    return_reason: Optional[str] = Field(None, description="Item-specific return reason")
    condition_on_return: Literal["EXCELLENT", "GOOD", "FAIR", "POOR", "DAMAGED"] = Field(...)
    damage_description: Optional[str] = Field(None, description="Damage description")
    damage_photos: Optional[List[str]] = Field(default_factory=list, description="Damage photo URLs")
    cleaning_condition: Literal["CLEAN", "MINOR_CLEANING", "MAJOR_CLEANING"] = Field(...)
    functionality_check: Literal["WORKING", "PARTIAL", "NOT_WORKING"] = Field(...)
    missing_accessories: Optional[List[str]] = Field(default_factory=list)
    estimated_repair_cost: Optional[Decimal] = Field(None, ge=0)
    beyond_normal_wear: bool = Field(default=False)


# Rental return create schema
class RentalReturnCreate(BaseModel):
    """Rental return creation schema."""
    
    # Core return information
    original_transaction_id: UUID = Field(..., description="Original rental transaction to return against")
    return_date: datetime = Field(default_factory=datetime.utcnow)
    return_reason_code: str = Field(..., max_length=50, description="Standardized return reason code")
    return_reason_notes: Optional[str] = Field(None, max_length=1000, description="Additional return notes")
    processed_by: Optional[UUID] = Field(None, description="User processing the return")
    
    # Rental-specific properties
    scheduled_return_date: date = Field(..., description="When it was supposed to be returned")
    actual_return_date: date = Field(..., description="When it was actually returned")
    late_fee_applicable: bool = Field(default=False)
    late_fee_amount: Optional[Decimal] = Field(None, ge=0)
    damage_assessment_required: bool = Field(default=True)
    cleaning_required: bool = Field(default=False)
    cleaning_fee: Optional[Decimal] = Field(None, ge=0)
    deposit_amount: Decimal = Field(..., ge=0, description="Original deposit")
    deposit_deductions: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    deposit_refund_amount: Optional[Decimal] = Field(None, ge=0)
    inspection_checklist: Optional[Dict[str, Any]] = Field(None)
    photos_required: bool = Field(default=True)
    photo_urls: Optional[List[str]] = Field(default_factory=list)
    
    # Line items
    return_items: List[RentalReturnLineItem] = Field(..., min_length=1, description="Items to return")
    
    @field_validator('actual_return_date')
    @classmethod
    def validate_return_date(cls, v, info):
        """Validate actual return date is not in future."""
        if v > date.today():
            raise ValueError("Actual return date cannot be in the future")
        return v
    
    @model_validator(mode='after')
    def validate_late_fee(self):
        """Validate late fee consistency."""
        if self.actual_return_date > self.scheduled_return_date:
            self.late_fee_applicable = True
            if not self.late_fee_amount or self.late_fee_amount == 0:
                # Calculate default late fee if not provided
                days_late = (self.actual_return_date - self.scheduled_return_date).days
                self.late_fee_amount = Decimal(str(days_late * 10))  # $10 per day default
        return self
    
    @model_validator(mode='after')
    def validate_photos(self):
        """Validate photos are provided when required."""
        if self.photos_required and self.damage_assessment_required:
            has_damage = any(
                item.condition_on_return in ["POOR", "DAMAGED"] 
                for item in self.return_items
            )
            if has_damage and not self.photo_urls:
                raise ValueError("Photos required for damaged items")
        return self


# Simple rental return schema (for basic returns)
class RentalReturn(BaseModel):
    """Simple rental return schema for basic return operations."""
    
    actual_return_date: date = Field(..., description="Actual return date")
    late_fees: Optional[Decimal] = Field(None, ge=0, description="Late fees if applicable")
    damage_fees: Optional[Decimal] = Field(None, ge=0, description="Damage fees if applicable")
    notes: Optional[str] = Field(None, description="Return notes")


# Rental inspection schemas
class RentalInspectionCreate(BaseModel):
    """Create a rental inspection record."""
    
    return_id: UUID = Field(..., description="Return transaction ID")
    inspector_id: UUID = Field(..., description="Inspector user ID")
    inspection_date: datetime = Field(default_factory=datetime.utcnow)
    overall_condition: Literal["EXCELLENT", "GOOD", "FAIR", "POOR", "DAMAGED"] = Field(...)
    cleanliness_rating: int = Field(..., ge=1, le=5, description="Cleanliness rating 1-5")
    functionality_rating: int = Field(..., ge=1, le=5, description="Functionality rating 1-5")
    
    # Detailed findings
    damage_findings: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    missing_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    repair_recommendations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    # Financial assessments
    estimated_repair_cost: Decimal = Field(default=Decimal("0"), ge=0)
    estimated_cleaning_cost: Decimal = Field(default=Decimal("0"), ge=0)
    recommended_deposit_deduction: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Documentation
    inspection_photos: Optional[List[str]] = Field(default_factory=list)
    inspection_notes: Optional[str] = Field(None, max_length=2000)
    customer_signature: Optional[str] = Field(None, description="Digital signature or acknowledgment")
    customer_disputed: bool = Field(default=False)
    dispute_notes: Optional[str] = Field(None)


class RentalInspectionResponse(BaseModel):
    """Rental inspection response."""
    
    id: UUID
    return_id: UUID
    inspector_id: UUID
    inspection_date: datetime
    overall_condition: str
    cleanliness_rating: int
    functionality_rating: int
    damage_findings: List[Dict[str, Any]]
    missing_items: List[Dict[str, Any]]
    repair_recommendations: List[Dict[str, Any]]
    estimated_repair_cost: Decimal
    estimated_cleaning_cost: Decimal
    recommended_deposit_deduction: Decimal
    inspection_photos: List[str]
    inspection_notes: Optional[str]
    customer_signature: Optional[str]
    customer_disputed: bool
    dispute_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Rental return response schemas
class RentalReturnDetails(BaseModel):
    """Rental return specific details for response."""
    
    scheduled_return_date: date
    actual_return_date: date
    days_late: int
    late_fee_applicable: bool
    late_fee_amount: Decimal
    damage_assessment_required: bool
    cleaning_required: bool
    cleaning_fee: Decimal
    deposit_amount: Decimal
    deposit_deductions: Decimal
    deposit_refund_amount: Decimal
    total_fees: Decimal
    inspection_completed: bool
    inspection_id: Optional[UUID]
    photos_urls: List[str]


class RentalReturnSummary(BaseModel):
    """Summary of rental return financial calculations."""
    
    original_rental_amount: Decimal
    deposit_amount: Decimal
    late_fees: Decimal
    damage_fees: Decimal
    cleaning_fees: Decimal
    other_fees: Decimal
    total_deductions: Decimal
    deposit_refund: Decimal
    amount_due: Decimal
    payment_status: str


class RentalDamageAssessment(BaseModel):
    """Damage assessment details."""
    
    item_id: UUID
    item_name: str
    damage_type: str
    severity: Literal["MINOR", "MODERATE", "SEVERE"]
    repair_cost: Decimal
    replacement_cost: Decimal
    recommended_action: Literal["REPAIR", "REPLACE", "WRITE_OFF"]
    photos: List[str]
    notes: Optional[str]


class RentalReturnFees(BaseModel):
    """Breakdown of all rental return fees."""
    
    late_fee: Decimal = Field(default=Decimal("0"))
    damage_fee: Decimal = Field(default=Decimal("0"))
    cleaning_fee: Decimal = Field(default=Decimal("0"))
    missing_item_fee: Decimal = Field(default=Decimal("0"))
    administrative_fee: Decimal = Field(default=Decimal("0"))
    total_fees: Decimal = Field(default=Decimal("0"))
    
    @model_validator(mode='after')
    def calculate_total(self):
        """Calculate total fees."""
        self.total_fees = (
            self.late_fee + 
            self.damage_fee + 
            self.cleaning_fee + 
            self.missing_item_fee + 
            self.administrative_fee
        )
        return self