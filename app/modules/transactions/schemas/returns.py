"""
Return transaction schemas with polymorphic design for type-specific properties.
"""
from typing import Union, Literal, Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


# Base return line item schema
class ReturnLineItemBase(BaseModel):
    """Base schema for return line items."""
    
    original_line_id: UUID = Field(..., description="Original transaction line ID")
    return_quantity: Decimal = Field(..., gt=0, description="Quantity to return")
    return_reason: Optional[str] = Field(None, description="Item-specific return reason")


# Sale return specific line item
class SaleReturnLineItem(ReturnLineItemBase):
    """Sale return specific line item properties."""
    
    condition: Literal["NEW", "OPENED", "USED", "DAMAGED"] = Field(..., description="Item condition")
    return_to_stock: bool = Field(default=True, description="Whether to return to stock")
    original_packaging: bool = Field(default=True, description="Has original packaging")
    all_accessories_included: bool = Field(default=True, description="All accessories included")
    testing_required: bool = Field(default=False, description="Requires testing")
    testing_notes: Optional[str] = Field(None, description="Testing notes")


# Purchase return specific line item
class PurchaseReturnLineItem(ReturnLineItemBase):
    """Purchase return specific line item properties."""
    
    defect_code: Optional[str] = Field(None, description="Supplier defect code")
    batch_number: Optional[str] = Field(None, description="Batch number for tracking")
    expiry_date: Optional[date] = Field(None, description="For perishables")
    supplier_fault: bool = Field(default=False, description="Is supplier at fault")
    replacement_requested: bool = Field(default=False, description="Request replacement")


# Rental return specific line item
class RentalReturnLineItem(ReturnLineItemBase):
    """Rental return specific line item properties."""
    
    condition_on_return: Literal["EXCELLENT", "GOOD", "FAIR", "POOR", "DAMAGED"] = Field(...)
    damage_description: Optional[str] = Field(None, description="Damage description")
    damage_photos: Optional[List[str]] = Field(default_factory=list, description="Damage photo URLs")
    cleaning_condition: Literal["CLEAN", "MINOR_CLEANING", "MAJOR_CLEANING"] = Field(...)
    functionality_check: Literal["WORKING", "PARTIAL", "NOT_WORKING"] = Field(...)
    missing_accessories: Optional[List[str]] = Field(default_factory=list)
    estimated_repair_cost: Optional[Decimal] = Field(None, ge=0)
    beyond_normal_wear: bool = Field(default=False)




# Base return transaction schema
class ReturnTransactionBase(BaseModel):
    """Base schema for all return transactions."""
    
    # Shared properties
    original_transaction_id: UUID = Field(..., description="Original transaction to return against")
    return_date: datetime = Field(default_factory=datetime.utcnow)
    return_reason_code: str = Field(..., max_length=50, description="Standardized return reason code")
    return_reason_notes: Optional[str] = Field(None, max_length=1000, description="Additional return notes")
    processed_by: Optional[UUID] = Field(None, description="User processing the return")
    
    # Financial adjustments (shared but calculated differently)
    refund_amount: Optional[Decimal] = Field(None, ge=0, description="Amount to refund")
    restocking_fee: Optional[Decimal] = Field(default=Decimal("0"), ge=0)


# Sale return specific schema
class SaleReturnCreate(ReturnTransactionBase):
    """Sale return specific properties."""
    
    return_type: Literal["SALE_RETURN"] = Field(default="SALE_RETURN")
    
    # Sale-specific properties
    customer_return_method: Literal["IN_STORE", "SHIPPED", "PICKUP"] = Field(..., description="How customer is returning")
    refund_method: Literal["ORIGINAL_PAYMENT", "STORE_CREDIT", "EXCHANGE"] = Field(..., description="Refund method")
    exchange_transaction_id: Optional[UUID] = Field(None, description="New transaction if exchange")
    return_shipping_cost: Optional[Decimal] = Field(None, ge=0, description="Cost of return shipping")
    customer_pays_shipping: bool = Field(default=False)
    quality_check_required: bool = Field(default=True)
    restock_location_id: Optional[UUID] = Field(None, description="Where to restock items")
    
    # Line items
    return_items: List[SaleReturnLineItem] = Field(..., min_length=1, description="Items to return")
    
    @model_validator(mode='after')
    def validate_exchange_transaction(self):
        """Validate exchange transaction ID is provided when refund method is exchange."""
        if self.refund_method == "EXCHANGE" and not self.exchange_transaction_id:
            raise ValueError("Exchange transaction ID required when refund method is EXCHANGE")
        return self


# Purchase return specific schema
class PurchaseReturnCreate(ReturnTransactionBase):
    """Purchase return specific properties."""
    
    return_type: Literal["PURCHASE_RETURN"] = Field(default="PURCHASE_RETURN")
    
    # Purchase-specific properties
    supplier_rma_number: Optional[str] = Field(None, max_length=100, description="Supplier's RMA number")
    return_authorization_date: Optional[date] = Field(None)
    supplier_credit_expected: bool = Field(default=True)
    credit_memo_number: Optional[str] = Field(None, max_length=100)
    return_shipping_method: Optional[str] = Field(None, max_length=100)
    return_tracking_number: Optional[str] = Field(None, max_length=100)
    supplier_restocking_fee_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    quality_claim: bool = Field(default=False, description="Is this a quality issue claim?")
    expected_credit_date: Optional[date] = Field(None)
    
    # Line items
    return_items: List[PurchaseReturnLineItem] = Field(..., min_length=1, description="Items to return")
    
    @model_validator(mode='after')
    def validate_quality_claim(self):
        """Validate quality claim has supplier fault items."""
        if self.quality_claim:
            has_supplier_fault = any(item.supplier_fault for item in self.return_items)
            if not has_supplier_fault:
                raise ValueError("Quality claim requires at least one item marked as supplier fault")
        return self




# Rental return specific schema
class RentalReturnCreate(ReturnTransactionBase):
    """Rental return specific properties."""
    
    return_type: Literal["RENTAL_RETURN"] = Field(default="RENTAL_RETURN")
    
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


# Union type for all return creates
ReturnTransactionCreate = Union[
    SaleReturnCreate,
    PurchaseReturnCreate,
    RentalReturnCreate
]


# Response schemas for returns
class ReturnTransactionResponse(BaseModel):
    """Base response for return transactions."""
    
    id: UUID
    transaction_number: str
    return_type: str
    original_transaction_id: UUID
    reference_transaction_number: str
    return_date: datetime
    return_reason_code: str
    return_reason_notes: Optional[str]
    status: str
    financial_summary: Dict[str, Decimal]
    created_at: datetime
    updated_at: datetime


class SaleReturnDetails(BaseModel):
    """Sale return specific details for response."""
    
    customer_return_method: str
    refund_method: str
    exchange_transaction_id: Optional[UUID]
    return_shipping_cost: Optional[Decimal]
    customer_pays_shipping: bool
    quality_check_required: bool
    quality_check_status: Optional[str]
    restock_location_id: Optional[UUID]


class PurchaseReturnDetails(BaseModel):
    """Purchase return specific details for response."""
    
    supplier_rma_number: Optional[str]
    return_authorization_date: Optional[date]
    supplier_credit_expected: bool
    credit_memo_number: Optional[str]
    return_shipping_method: Optional[str]
    return_tracking_number: Optional[str]
    supplier_restocking_fee_percent: Optional[Decimal]
    quality_claim: bool
    expected_credit_date: Optional[date]
    credit_received: bool = False
    credit_received_date: Optional[date]


class RentalReturnDetails(BaseModel):
    """Rental return specific details for response."""
    
    scheduled_return_date: date
    actual_return_date: date
    days_late: int
    late_fee_applicable: bool
    late_fee_amount: Decimal
    damage_assessment_required: bool
    damage_assessment_status: Optional[str]
    cleaning_required: bool
    cleaning_fee: Decimal
    deposit_amount: Decimal
    deposit_deductions: Decimal
    deposit_refund_amount: Decimal
    inspection_checklist: Optional[Dict[str, Any]]
    photo_urls: List[str]


class ReturnDetailsResponse(BaseModel):
    """Comprehensive return details response."""
    
    # Common fields
    id: UUID
    transaction_number: str
    return_type: str
    original_transaction_id: UUID
    return_date: datetime
    status: str
    
    # Financial summary
    financial_summary: Dict[str, Decimal]
    
    # Type-specific details
    specific_details: Union[
        SaleReturnDetails,
        PurchaseReturnDetails,
        RentalReturnDetails
    ]
    
    # Line items
    return_lines: List[Dict[str, Any]]
    
    created_at: datetime
    updated_at: datetime


# Validation and status update schemas
class ReturnValidationRequest(BaseModel):
    """Request for return validation."""
    
    return_data: ReturnTransactionCreate


class ReturnValidationResponse(BaseModel):
    """Response from return validation."""
    
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    estimated_refund: Optional[Decimal]
    estimated_fees: Optional[Dict[str, Decimal]]


class ReturnStatusUpdate(BaseModel):
    """Update return status."""
    
    new_status: str
    notes: Optional[str]
    updated_by: UUID


class ReturnWorkflowState(str):
    """Return workflow states."""
    
    INITIATED = "INITIATED"
    VALIDATED = "VALIDATED"
    ITEMS_RECEIVED = "ITEMS_RECEIVED"
    INSPECTION_PENDING = "INSPECTION_PENDING"
    INSPECTION_COMPLETE = "INSPECTION_COMPLETE"
    REFUND_APPROVED = "REFUND_APPROVED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"




# Purchase return credit memo schemas
class PurchaseCreditMemoCreate(BaseModel):
    """Record supplier credit memo for purchase return."""
    
    return_id: UUID = Field(..., description="Purchase return ID")
    credit_memo_number: str = Field(..., max_length=100, description="Supplier's credit memo number")
    credit_date: date = Field(..., description="Date credit was issued")
    credit_amount: Decimal = Field(..., gt=0, description="Credit amount")
    
    # Credit details
    credit_type: Literal["FULL_REFUND", "PARTIAL_REFUND", "STORE_CREDIT", "REPLACEMENT"] = Field(...)
    currency: str = Field(default="USD", max_length=3)
    exchange_rate: Optional[Decimal] = Field(default=Decimal("1.0"), gt=0)
    
    # Line item credits (optional breakdown)
    line_credits: Optional[List[Dict[str, Any]]] = Field(None)
    
    # Additional information
    credit_terms: Optional[str] = Field(None, max_length=500)
    supplier_notes: Optional[str] = Field(None, max_length=1000)
    received_by: UUID = Field(..., description="User recording the credit")
    
    @model_validator(mode='after')
    def validate_credit_amount(self):
        """Validate credit amount is reasonable."""
        if self.credit_amount <= 0:
            raise ValueError("Credit amount must be positive")
        return self


class PurchaseCreditMemoResponse(BaseModel):
    """Purchase credit memo response."""
    
    id: UUID
    return_id: UUID
    credit_memo_number: str
    credit_date: date
    credit_amount: Decimal
    credit_type: str
    currency: str
    exchange_rate: Decimal
    line_credits: Optional[List[Dict[str, Any]]]
    credit_terms: Optional[str]
    supplier_notes: Optional[str]
    received_by: UUID
    created_at: datetime
    updated_at: datetime