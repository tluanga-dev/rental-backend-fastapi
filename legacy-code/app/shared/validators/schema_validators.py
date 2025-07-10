"""
Pydantic Schema Validators and Custom Field Types.

This module provides enhanced validation for Pydantic schemas with custom
field types, validators, and business rule integration.
"""

from typing import Any, Optional, Union, List, Dict
from datetime import datetime, date
from decimal import Decimal
import re
from uuid import UUID

from pydantic import validator, Field, BaseModel
from pydantic.validators import str_validator

from .business_rules import (
    BusinessRuleValidator,
    CustomerValidator,
    InventoryValidator,
    RentalValidator,
    TransactionValidator
)


class EmailStr(str):
    """Custom email string type with validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate
    
    @classmethod
    def validate(cls, v: str) -> str:
        result = BusinessRuleValidator.validate_email(v)
        result.raise_if_errors()
        return v
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(
            format='email',
            example='user@example.com',
            description='Valid email address'
        )


class PhoneStr(str):
    """Custom phone string type with validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate
    
    @classmethod
    def validate(cls, v: str) -> str:
        result = BusinessRuleValidator.validate_phone_number(v)
        result.raise_if_errors()
        return v
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(
            format='phone',
            example='+1-555-123-4567',
            description='Valid phone number'
        )


class CurrencyDecimal(Decimal):
    """Custom currency decimal type with validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: Union[str, int, float, Decimal]) -> Decimal:
        if isinstance(v, (int, float)):
            v = str(v)
        elif isinstance(v, Decimal):
            v = str(v)
        
        try:
            decimal_value = Decimal(v)
        except Exception:
            raise ValueError('Invalid decimal value')
        
        result = BusinessRuleValidator.validate_currency_amount(decimal_value)
        result.raise_if_errors()
        
        return decimal_value
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(
            type='number',
            multipleOf=0.01,
            minimum=0,
            example=99.99,
            description='Currency amount with up to 2 decimal places'
        )


class SKUStr(str):
    """Custom SKU string type with validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate
    
    @classmethod
    def validate(cls, v: str) -> str:
        result = InventoryValidator.validate_sku(v)
        result.raise_if_errors()
        return v.upper()  # Normalize to uppercase
    
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(
            pattern='^[A-Za-z0-9\\-_]{3,50}$',
            example='LAPTOP-001',
            description='Product SKU (3-50 alphanumeric characters, hyphens, underscores)'
        )


# Common Field Definitions with Enhanced Validation
def email_field(**kwargs) -> EmailStr:
    """Email field with validation."""
    return Field(
        ...,
        title="Email Address",
        description="Valid email address",
        example="user@example.com",
        **kwargs
    )


def phone_field(**kwargs) -> PhoneStr:
    """Phone field with validation."""
    return Field(
        ...,
        title="Phone Number",
        description="Valid phone number",
        example="+1-555-123-4567",
        **kwargs
    )


def currency_field(min_value: float = 0, max_value: float = None, **kwargs) -> CurrencyDecimal:
    """Currency field with validation."""
    return Field(
        ...,
        title="Currency Amount",
        description="Currency amount with up to 2 decimal places",
        ge=min_value,
        le=max_value,
        example=99.99,
        **kwargs
    )


def sku_field(**kwargs) -> SKUStr:
    """SKU field with validation."""
    return Field(
        ...,
        title="Product SKU",
        description="Unique product identifier",
        example="LAPTOP-001",
        **kwargs
    )


def password_field(**kwargs) -> str:
    """Password field with validation."""
    return Field(
        ...,
        title="Password",
        description="Strong password (min 8 chars, mixed case, numbers, special chars)",
        min_length=8,
        max_length=128,
        example="SecurePass123!",
        **kwargs
    )


def date_field(**kwargs) -> date:
    """Date field with validation."""
    return Field(
        ...,
        title="Date",
        description="Date in YYYY-MM-DD format",
        example="2024-01-01",
        **kwargs
    )


def positive_int_field(max_value: int = None, **kwargs) -> int:
    """Positive integer field."""
    return Field(
        ...,
        title="Positive Integer",
        description="Positive integer value",
        ge=1,
        le=max_value,
        example=1,
        **kwargs
    )


# Enhanced Base Schema with Common Validations
class EnhancedBaseModel(BaseModel):
    """Enhanced base model with common validations."""
    
    class Config:
        # Use enum values instead of names
        use_enum_values = True
        # Validate field defaults
        validate_all = True
        # Allow population by field name or alias
        allow_population_by_field_name = True
        # JSON schema customization
        schema_extra = {
            "examples": []
        }
    
    @validator('*', pre=True)
    def strip_strings(cls, v):
        """Strip whitespace from string fields."""
        if isinstance(v, str):
            return v.strip()
        return v
    
    @validator('*')
    def empty_strings_to_none(cls, v):
        """Convert empty strings to None."""
        if v == '':
            return None
        return v


# Domain-Specific Schema Mixins
class CustomerValidationMixin:
    """Mixin for customer validation."""
    
    @validator('email')
    def validate_email_format(cls, v):
        if v:
            result = BusinessRuleValidator.validate_email(v)
            result.raise_if_errors()
        return v
    
    @validator('phone_number')
    def validate_phone_format(cls, v):
        if v:
            result = BusinessRuleValidator.validate_phone_number(v)
            result.raise_if_errors()
        return v
    
    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v:
            result = CustomerValidator.validate_date_of_birth(v)
            result.raise_if_errors()
        return v
    
    @validator('credit_limit')
    def validate_credit_amount(cls, v):
        if v is not None:
            result = CustomerValidator.validate_credit_limit(v)
            result.raise_if_errors()
        return v


class InventoryValidationMixin:
    """Mixin for inventory validation."""
    
    @validator('sku')
    def validate_sku_format(cls, v):
        if v:
            result = InventoryValidator.validate_sku(v)
            result.raise_if_errors()
        return v.upper()
    
    @validator('rental_price_per_day', 'purchase_price')
    def validate_prices(cls, v):
        if v is not None:
            result = BusinessRuleValidator.validate_currency_amount(v)
            result.raise_if_errors()
        return v
    
    @validator('stock_quantity')
    def validate_stock(cls, v):
        if v is not None:
            result = InventoryValidator.validate_stock_quantity(v)
            result.raise_if_errors()
        return v


class RentalValidationMixin:
    """Mixin for rental validation."""
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v:
            result = BusinessRuleValidator.validate_date_range(start_date, v)
            result.raise_if_errors()
        return v
    
    @validator('quantity')
    def validate_rental_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Rental quantity must be positive')
        return v


class TransactionValidationMixin:
    """Mixin for transaction validation."""
    
    @validator('total_amount', 'tax_amount', 'discount_amount')
    def validate_amounts(cls, v):
        if v is not None:
            result = BusinessRuleValidator.validate_currency_amount(v)
            result.raise_if_errors()
        return v
    
    @validator('payment_method')
    def validate_payment(cls, v):
        if v:
            result = TransactionValidator.validate_payment_method(v)
            result.raise_if_errors()
        return v


# Example Enhanced Schemas with Field Examples
class EnhancedCustomerCreate(EnhancedBaseModel, CustomerValidationMixin):
    """Enhanced customer creation schema with validation."""
    
    customer_type: str = Field(
        ...,
        title="Customer Type",
        description="Type of customer",
        example="INDIVIDUAL",
        regex="^(INDIVIDUAL|BUSINESS)$"
    )
    
    first_name: Optional[str] = Field(
        None,
        title="First Name",
        description="Customer's first name (required for individual customers)",
        min_length=1,
        max_length=100,
        example="John"
    )
    
    last_name: Optional[str] = Field(
        None,
        title="Last Name", 
        description="Customer's last name (required for individual customers)",
        min_length=1,
        max_length=100,
        example="Doe"
    )
    
    business_name: Optional[str] = Field(
        None,
        title="Business Name",
        description="Company name (required for business customers)",
        min_length=1,
        max_length=255,
        example="Acme Corporation"
    )
    
    email: EmailStr = email_field()
    phone_number: Optional[PhoneStr] = phone_field(default=None)
    
    address: Optional[str] = Field(
        None,
        title="Address",
        description="Street address",
        max_length=255,
        example="123 Main Street"
    )
    
    city: Optional[str] = Field(
        None,
        title="City",
        description="City name",
        max_length=100,
        example="New York"
    )
    
    state: Optional[str] = Field(
        None,
        title="State/Province",
        description="State or province",
        max_length=100,
        example="NY"
    )
    
    postal_code: Optional[str] = Field(
        None,
        title="Postal Code",
        description="ZIP or postal code",
        max_length=20,
        example="10001"
    )
    
    country: Optional[str] = Field(
        None,
        title="Country",
        description="Country name",
        max_length=100,
        example="USA"
    )
    
    date_of_birth: Optional[date] = date_field(default=None)
    
    credit_limit: Optional[CurrencyDecimal] = currency_field(
        min_value=0,
        max_value=1000000,
        default=None
    )
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "customer_type": "INDIVIDUAL",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone_number": "+1-555-123-4567",
                    "address": "123 Main Street",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA",
                    "date_of_birth": "1985-06-15",
                    "credit_limit": 5000.00
                },
                {
                    "customer_type": "BUSINESS",
                    "business_name": "Acme Corporation",
                    "email": "contact@acme.com",
                    "phone_number": "+1-555-987-6543",
                    "address": "456 Business Ave",
                    "city": "Chicago",
                    "state": "IL",
                    "postal_code": "60601",
                    "country": "USA",
                    "credit_limit": 50000.00
                }
            ]
        }


class EnhancedInventoryItemCreate(EnhancedBaseModel, InventoryValidationMixin):
    """Enhanced inventory item creation schema."""
    
    name: str = Field(
        ...,
        title="Item Name",
        description="Name of the inventory item",
        min_length=1,
        max_length=255,
        example="MacBook Pro 16-inch"
    )
    
    description: Optional[str] = Field(
        None,
        title="Description",
        description="Detailed description of the item",
        max_length=1000,
        example="Apple MacBook Pro 16-inch with M1 chip, 16GB RAM, 512GB SSD"
    )
    
    sku: SKUStr = sku_field()
    
    category_id: Optional[UUID] = Field(
        None,
        title="Category ID",
        description="Category this item belongs to",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    
    brand_id: Optional[UUID] = Field(
        None,
        title="Brand ID",
        description="Brand of this item",
        example="123e4567-e89b-12d3-a456-426614174001"
    )
    
    rental_price_per_day: CurrencyDecimal = currency_field(
        min_value=0.01,
        max_value=10000
    )
    
    purchase_price: Optional[CurrencyDecimal] = currency_field(
        min_value=0,
        max_value=1000000,
        default=None
    )
    
    stock_quantity: Optional[int] = positive_int_field(
        max_value=10000,
        default=1
    )
    
    condition: Optional[str] = Field(
        "NEW",
        title="Condition",
        description="Current condition of the item",
        regex="^(NEW|EXCELLENT|GOOD|FAIR|POOR)$",
        example="NEW"
    )
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "name": "MacBook Pro 16-inch",
                    "description": "Apple MacBook Pro 16-inch with M1 chip",
                    "sku": "MBP16-M1-512",
                    "rental_price_per_day": 50.00,
                    "purchase_price": 2499.00,
                    "stock_quantity": 5,
                    "condition": "NEW"
                }
            ]
        }


def create_validation_examples():
    """Create validation examples for documentation."""
    return {
        "valid_customer": {
            "customer_type": "INDIVIDUAL",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "+1-555-123-4567",
            "date_of_birth": "1985-06-15"
        },
        "invalid_customer": {
            "customer_type": "INDIVIDUAL",
            "first_name": "",  # Empty string - invalid
            "email": "invalid-email",  # Invalid format
            "phone_number": "123",  # Too short
            "date_of_birth": "2030-01-01"  # Future date - invalid
        },
        "valid_inventory_item": {
            "name": "MacBook Pro",
            "sku": "MBP-001",
            "rental_price_per_day": 50.00,
            "purchase_price": 2500.00,
            "stock_quantity": 3
        },
        "invalid_inventory_item": {
            "name": "",  # Empty name - invalid
            "sku": "AB",  # Too short - invalid
            "rental_price_per_day": -10.00,  # Negative price - invalid
            "stock_quantity": -1  # Negative stock - invalid
        }
    }