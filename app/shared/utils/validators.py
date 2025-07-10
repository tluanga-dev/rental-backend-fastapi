import re
from typing import Optional, Union, List, Any
from uuid import UUID
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel


class ValidationError(ValueError):
    """Custom validation error with field information."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.field = field
        self.value = value
        super().__init__(message)


# Email validation
def validate_email_address(email: str) -> str:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address
        
    Raises:
        ValidationError: If email is invalid
    """
    try:
        # Validate and normalize email
        validation = validate_email(email, check_deliverability=False)
        return validation.email
    except EmailNotValidError as e:
        raise ValidationError(str(e), field="email", value=email)


# Phone number validation
def validate_phone_number(
    phone: str,
    country_code: str = "US"
) -> str:
    """
    Validate and format phone number.
    
    Args:
        phone: Phone number to validate
        country_code: ISO country code (default: US)
        
    Returns:
        Formatted phone number in E.164 format
        
    Raises:
        ValidationError: If phone number is invalid
    """
    try:
        # Parse phone number
        parsed = phonenumbers.parse(phone, country_code)
        
        # Validate phone number
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError(
                f"Invalid phone number for country {country_code}",
                field="phone",
                value=phone
            )
        
        # Format in E.164 format
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    
    except phonenumbers.NumberParseException as e:
        raise ValidationError(str(e), field="phone", value=phone)


# UUID validation
def validate_uuid(value: Union[str, UUID]) -> UUID:
    """
    Validate UUID format.
    
    Args:
        value: UUID string or UUID object
        
    Returns:
        UUID object
        
    Raises:
        ValidationError: If UUID is invalid
    """
    if isinstance(value, UUID):
        return value
    
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        raise ValidationError(f"Invalid UUID format", field="id", value=value)


# String validation
def validate_string_length(
    value: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "value"
) -> str:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)
        field_name: Field name for error message
        
    Returns:
        Validated string
        
    Raises:
        ValidationError: If string length is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string",
            field=field_name,
            value=value
        )
    
    length = len(value)
    
    if min_length is not None and length < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters",
            field=field_name,
            value=value
        )
    
    if max_length is not None and length > max_length:
        raise ValidationError(
            f"{field_name} must not exceed {max_length} characters",
            field=field_name,
            value=value
        )
    
    return value


def validate_non_empty_string(value: str, field_name: str = "value") -> str:
    """
    Validate that string is not empty or just whitespace.
    
    Args:
        value: String to validate
        field_name: Field name for error message
        
    Returns:
        Trimmed string
        
    Raises:
        ValidationError: If string is empty
    """
    if not value or not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            field=field_name,
            value=value
        )
    
    return value.strip()


# Numeric validation
def validate_positive_number(
    value: Union[int, float, Decimal],
    field_name: str = "value",
    allow_zero: bool = False
) -> Union[int, float, Decimal]:
    """
    Validate that number is positive.
    
    Args:
        value: Number to validate
        field_name: Field name for error message
        allow_zero: Whether to allow zero
        
    Returns:
        Validated number
        
    Raises:
        ValidationError: If number is not positive
    """
    try:
        num_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError(
            f"{field_name} must be a valid number",
            field=field_name,
            value=value
        )
    
    if allow_zero and num_value < 0:
        raise ValidationError(
            f"{field_name} cannot be negative",
            field=field_name,
            value=value
        )
    elif not allow_zero and num_value <= 0:
        raise ValidationError(
            f"{field_name} must be positive",
            field=field_name,
            value=value
        )
    
    # Return original type
    if isinstance(value, int):
        return int(num_value)
    elif isinstance(value, float):
        return float(num_value)
    else:
        return num_value


def validate_number_range(
    value: Union[int, float, Decimal],
    min_value: Optional[Union[int, float, Decimal]] = None,
    max_value: Optional[Union[int, float, Decimal]] = None,
    field_name: str = "value"
) -> Union[int, float, Decimal]:
    """
    Validate number is within range.
    
    Args:
        value: Number to validate
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        field_name: Field name for error message
        
    Returns:
        Validated number
        
    Raises:
        ValidationError: If number is out of range
    """
    try:
        num_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError(
            f"{field_name} must be a valid number",
            field=field_name,
            value=value
        )
    
    if min_value is not None and num_value < Decimal(str(min_value)):
        raise ValidationError(
            f"{field_name} must be at least {min_value}",
            field=field_name,
            value=value
        )
    
    if max_value is not None and num_value > Decimal(str(max_value)):
        raise ValidationError(
            f"{field_name} must not exceed {max_value}",
            field=field_name,
            value=value
        )
    
    # Return original type
    if isinstance(value, int):
        return int(num_value)
    elif isinstance(value, float):
        return float(num_value)
    else:
        return num_value


# Date validation
def validate_date_range(
    start_date: Union[datetime, date],
    end_date: Union[datetime, date],
    field_name: str = "date range"
) -> tuple[Union[datetime, date], Union[datetime, date]]:
    """
    Validate that end date is after start date.
    
    Args:
        start_date: Start date
        end_date: End date
        field_name: Field name for error message
        
    Returns:
        Tuple of (start_date, end_date)
        
    Raises:
        ValidationError: If date range is invalid
    """
    # Convert to comparable types
    start = start_date.date() if isinstance(start_date, datetime) else start_date
    end = end_date.date() if isinstance(end_date, datetime) else end_date
    
    if end < start:
        raise ValidationError(
            f"End date must be after start date",
            field=field_name,
            value={"start_date": str(start_date), "end_date": str(end_date)}
        )
    
    return start_date, end_date


def validate_future_date(
    date_value: Union[datetime, date],
    field_name: str = "date",
    allow_today: bool = True
) -> Union[datetime, date]:
    """
    Validate that date is in the future.
    
    Args:
        date_value: Date to validate
        field_name: Field name for error message
        allow_today: Whether to allow today's date
        
    Returns:
        Validated date
        
    Raises:
        ValidationError: If date is not in future
    """
    today = datetime.now().date()
    check_date = date_value.date() if isinstance(date_value, datetime) else date_value
    
    if allow_today and check_date < today:
        raise ValidationError(
            f"{field_name} must be today or in the future",
            field=field_name,
            value=str(date_value)
        )
    elif not allow_today and check_date <= today:
        raise ValidationError(
            f"{field_name} must be in the future",
            field=field_name,
            value=str(date_value)
        )
    
    return date_value


# Pattern validation
def validate_pattern(
    value: str,
    pattern: str,
    field_name: str = "value",
    error_message: Optional[str] = None
) -> str:
    """
    Validate string against regex pattern.
    
    Args:
        value: String to validate
        pattern: Regex pattern
        field_name: Field name for error message
        error_message: Custom error message
        
    Returns:
        Validated string
        
    Raises:
        ValidationError: If string doesn't match pattern
    """
    if not re.match(pattern, value):
        message = error_message or f"{field_name} format is invalid"
        raise ValidationError(message, field=field_name, value=value)
    
    return value


# Business-specific validators
def validate_sku(sku: str) -> str:
    """
    Validate SKU format.
    
    Args:
        sku: SKU to validate
        
    Returns:
        Validated SKU
        
    Raises:
        ValidationError: If SKU format is invalid
    """
    # SKU must be alphanumeric with optional hyphens/underscores
    pattern = r"^[A-Za-z0-9\-_]+$"
    sku = validate_non_empty_string(sku, "SKU")
    return validate_pattern(sku, pattern, "SKU", "SKU must be alphanumeric")


def validate_barcode(barcode: str) -> str:
    """
    Validate barcode format (EAN-13, UPC-A, or custom).
    
    Args:
        barcode: Barcode to validate
        
    Returns:
        Validated barcode
        
    Raises:
        ValidationError: If barcode format is invalid
    """
    barcode = validate_non_empty_string(barcode, "barcode")
    
    # Check for common barcode formats
    if len(barcode) == 13 and barcode.isdigit():
        # EAN-13
        return barcode
    elif len(barcode) == 12 and barcode.isdigit():
        # UPC-A
        return barcode
    else:
        # Custom format - alphanumeric
        pattern = r"^[A-Za-z0-9]+$"
        return validate_pattern(barcode, pattern, "barcode", "Invalid barcode format")


def validate_currency_code(code: str) -> str:
    """
    Validate ISO 4217 currency code.
    
    Args:
        code: Currency code to validate
        
    Returns:
        Validated currency code (uppercase)
        
    Raises:
        ValidationError: If currency code is invalid
    """
    # Common ISO 4217 currency codes
    valid_codes = {
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
        "CNY", "INR", "KRW", "SGD", "HKD", "NOK", "SEK", "DKK",
        "PLN", "CZK", "HUF", "RON", "BGN", "HRK", "RUB", "TRY",
        "BRL", "MXN", "ARS", "CLP", "COP", "PEN", "UYU", "ZAR"
    }
    
    code = code.upper().strip()
    if code not in valid_codes:
        raise ValidationError(
            f"Invalid currency code. Must be a valid ISO 4217 code",
            field="currency",
            value=code
        )
    
    return code


def validate_percentage(
    value: Union[int, float, Decimal],
    field_name: str = "percentage"
) -> Decimal:
    """
    Validate percentage value (0-100).
    
    Args:
        value: Percentage value
        field_name: Field name for error message
        
    Returns:
        Validated percentage as Decimal
        
    Raises:
        ValidationError: If percentage is invalid
    """
    return Decimal(str(validate_number_range(value, 0, 100, field_name)))


def validate_tax_id(tax_id: str, country_code: str = "US") -> str:
    """
    Validate tax ID format based on country.
    
    Args:
        tax_id: Tax ID to validate
        country_code: ISO country code
        
    Returns:
        Validated tax ID
        
    Raises:
        ValidationError: If tax ID format is invalid
    """
    tax_id = validate_non_empty_string(tax_id, "tax ID")
    
    # US TIN/EIN format: XX-XXXXXXX
    if country_code == "US":
        pattern = r"^\d{2}-\d{7}$"
        return validate_pattern(
            tax_id, pattern, "tax ID",
            "US tax ID must be in format XX-XXXXXXX"
        )
    
    # For other countries, just ensure it's not empty
    return tax_id


# List validators
def validate_list_not_empty(
    items: List[Any],
    field_name: str = "list"
) -> List[Any]:
    """
    Validate that list is not empty.
    
    Args:
        items: List to validate
        field_name: Field name for error message
        
    Returns:
        Validated list
        
    Raises:
        ValidationError: If list is empty
    """
    if not items:
        raise ValidationError(
            f"{field_name} cannot be empty",
            field=field_name,
            value=items
        )
    
    return items


def validate_unique_list(
    items: List[Any],
    field_name: str = "list"
) -> List[Any]:
    """
    Validate that list contains unique items.
    
    Args:
        items: List to validate
        field_name: Field name for error message
        
    Returns:
        Validated list
        
    Raises:
        ValidationError: If list contains duplicates
    """
    if len(items) != len(set(items)):
        raise ValidationError(
            f"{field_name} contains duplicate values",
            field=field_name,
            value=items
        )
    
    return items


# Composite validators
class AddressValidator(BaseModel):
    """Validate address components."""
    
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    
    def validate(self) -> dict:
        """Validate all address fields."""
        validated = {}
        
        # Validate required fields
        validated["street"] = validate_non_empty_string(self.street, "street")
        validated["city"] = validate_non_empty_string(self.city, "city")
        validated["state"] = validate_non_empty_string(self.state, "state")
        validated["country"] = validate_non_empty_string(self.country, "country")
        
        # Validate postal code based on country
        if self.country == "US":
            # US ZIP code: 5 digits or 5+4 format
            pattern = r"^\d{5}(-\d{4})?$"
            validated["postal_code"] = validate_pattern(
                self.postal_code, pattern, "postal code",
                "US postal code must be in format 12345 or 12345-6789"
            )
        else:
            validated["postal_code"] = validate_non_empty_string(
                self.postal_code, "postal code"
            )
        
        return validated


__all__ = [
    "ValidationError",
    "validate_email_address",
    "validate_phone_number",
    "validate_uuid",
    "validate_string_length",
    "validate_non_empty_string",
    "validate_positive_number",
    "validate_number_range",
    "validate_date_range",
    "validate_future_date",
    "validate_pattern",
    "validate_sku",
    "validate_barcode",
    "validate_currency_code",
    "validate_percentage",
    "validate_tax_id",
    "validate_list_not_empty",
    "validate_unique_list",
    "AddressValidator",
]