from typing import Optional, Union, Any, Dict, List
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
import re
import json
from enum import Enum

from app.core.config import settings


# Number formatting
def format_currency(
    amount: Union[int, float, Decimal],
    currency: str = None,
    decimal_places: int = 2,
    include_symbol: bool = True
) -> str:
    """
    Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code (defaults to settings)
        decimal_places: Number of decimal places
        include_symbol: Whether to include currency symbol
        
    Returns:
        Formatted currency string
    """
    currency = currency or settings.DEFAULT_CURRENCY
    
    # Convert to Decimal for precision
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # Round to specified decimal places
    quantized = amount.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)
    
    # Format with thousand separators
    formatted = f"{quantized:,.{decimal_places}f}"
    
    # Add currency symbol
    if include_symbol:
        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "INR": "₹",
        }
        symbol = symbols.get(currency, currency + " ")
        
        # Place symbol before or after based on currency
        if currency in ["USD", "GBP"]:
            return f"{symbol}{formatted}"
        else:
            return f"{formatted} {symbol}"
    
    return formatted


def format_percentage(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
    include_symbol: bool = True
) -> str:
    """
    Format value as percentage.
    
    Args:
        value: Percentage value (0-100)
        decimal_places: Number of decimal places
        include_symbol: Whether to include % symbol
        
    Returns:
        Formatted percentage string
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    quantized = value.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)
    formatted = f"{quantized:.{decimal_places}f}"
    
    if include_symbol:
        return f"{formatted}%"
    
    return formatted


def format_decimal(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
    min_decimal_places: Optional[int] = None
) -> str:
    """
    Format decimal number.
    
    Args:
        value: Number to format
        decimal_places: Maximum decimal places
        min_decimal_places: Minimum decimal places
        
    Returns:
        Formatted number string
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Remove trailing zeros if min_decimal_places not specified
    if min_decimal_places is None:
        normalized = value.normalize()
        return str(normalized)
    
    # Format with specific decimal places
    quantized = value.quantize(Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP)
    return f"{quantized:.{min_decimal_places or decimal_places}f}"


def format_quantity(
    value: Union[int, float],
    unit: Optional[str] = None,
    decimal_places: int = 0
) -> str:
    """
    Format quantity with optional unit.
    
    Args:
        value: Quantity value
        unit: Unit of measurement
        decimal_places: Decimal places for non-integer quantities
        
    Returns:
        Formatted quantity string
    """
    if isinstance(value, int) or value.is_integer():
        formatted = str(int(value))
    else:
        formatted = format_decimal(value, decimal_places)
    
    if unit:
        return f"{formatted} {unit}"
    
    return formatted


# Date and time formatting
def format_date(
    date_value: Union[datetime, date, str],
    format_string: Optional[str] = None
) -> str:
    """
    Format date according to settings or custom format.
    
    Args:
        date_value: Date to format
        format_string: Custom format string
        
    Returns:
        Formatted date string
    """
    if isinstance(date_value, str):
        # Parse ISO format string
        date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
    
    if isinstance(date_value, datetime):
        date_value = date_value.date()
    
    format_str = format_string or settings.DATE_FORMAT
    return date_value.strftime(format_str)


def format_datetime(
    datetime_value: Union[datetime, str],
    format_string: Optional[str] = None,
    include_timezone: bool = False
) -> str:
    """
    Format datetime according to settings or custom format.
    
    Args:
        datetime_value: Datetime to format
        format_string: Custom format string
        include_timezone: Whether to include timezone
        
    Returns:
        Formatted datetime string
    """
    if isinstance(datetime_value, str):
        # Parse ISO format string
        datetime_value = datetime.fromisoformat(datetime_value.replace('Z', '+00:00'))
    
    format_str = format_string or settings.DATETIME_FORMAT
    
    if include_timezone:
        format_str += " %Z"
    
    return datetime_value.strftime(format_str)


def format_time_ago(
    datetime_value: datetime,
    reference_time: Optional[datetime] = None
) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago").
    
    Args:
        datetime_value: Datetime to format
        reference_time: Reference time (defaults to now)
        
    Returns:
        Relative time string
    """
    if reference_time is None:
        reference_time = datetime.now(datetime_value.tzinfo)
    
    delta = reference_time - datetime_value
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def format_duration(
    duration: Union[timedelta, int],
    unit: str = "seconds",
    verbose: bool = False
) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        duration: Duration as timedelta or integer
        unit: Unit of integer duration ("seconds", "minutes", "hours", "days")
        verbose: Whether to use verbose format
        
    Returns:
        Formatted duration string
    """
    if isinstance(duration, int):
        if unit == "minutes":
            duration = timedelta(minutes=duration)
        elif unit == "hours":
            duration = timedelta(hours=duration)
        elif unit == "days":
            duration = timedelta(days=duration)
        else:
            duration = timedelta(seconds=duration)
    
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
    
    parts = []
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and not days:  # Don't show seconds for long durations
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    if verbose:
        if len(parts) > 1:
            return ", ".join(parts[:-1]) + f" and {parts[-1]}"
        return parts[0] if parts else "0 seconds"
    else:
        # Return most significant unit
        return parts[0] if parts else "0 seconds"


# String formatting
def format_name(
    first_name: Optional[str],
    last_name: Optional[str],
    middle_name: Optional[str] = None,
    format_type: str = "full"
) -> str:
    """
    Format person name.
    
    Args:
        first_name: First name
        last_name: Last name
        middle_name: Middle name
        format_type: Format type ("full", "last_first", "initials")
        
    Returns:
        Formatted name
    """
    parts = []
    
    if format_type == "initials":
        if first_name:
            parts.append(first_name[0].upper() + ".")
        if middle_name:
            parts.append(middle_name[0].upper() + ".")
        if last_name:
            parts.append(last_name[0].upper() + ".")
        return " ".join(parts)
    
    elif format_type == "last_first":
        if last_name:
            parts.append(last_name)
        if first_name:
            if parts:
                parts.append(",")
            parts.append(first_name)
        if middle_name:
            parts.append(middle_name)
        return " ".join(parts)
    
    else:  # full
        if first_name:
            parts.append(first_name)
        if middle_name:
            parts.append(middle_name)
        if last_name:
            parts.append(last_name)
        return " ".join(parts)


def format_phone(
    phone: str,
    country_code: str = "US",
    international: bool = False
) -> str:
    """
    Format phone number.
    
    Args:
        phone: Phone number (E.164 format expected)
        country_code: Country code for formatting
        international: Whether to format as international
        
    Returns:
        Formatted phone number
    """
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    if country_code == "US" and len(digits) == 10:
        # Format as (XXX) XXX-XXXX
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif country_code == "US" and len(digits) == 11 and digits[0] == "1":
        # Format as +1 (XXX) XXX-XXXX
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        # Return as-is for other formats
        return phone


def format_address(
    street: str,
    city: str,
    state: str,
    postal_code: str,
    country: str = "US",
    multiline: bool = False
) -> str:
    """
    Format address.
    
    Args:
        street: Street address
        city: City
        state: State/Province
        postal_code: Postal/ZIP code
        country: Country code
        multiline: Whether to format as multiple lines
        
    Returns:
        Formatted address
    """
    if multiline:
        lines = [street]
        if country == "US":
            lines.append(f"{city}, {state} {postal_code}")
        else:
            lines.append(f"{city} {state} {postal_code}")
            lines.append(country)
        return "\n".join(lines)
    else:
        if country == "US":
            return f"{street}, {city}, {state} {postal_code}"
        else:
            return f"{street}, {city} {state} {postal_code}, {country}"


def format_code(code: str, prefix: Optional[str] = None) -> str:
    """
    Format code with optional prefix.
    
    Args:
        code: Code to format
        prefix: Optional prefix
        
    Returns:
        Formatted code
    """
    if prefix:
        return f"{prefix}-{code}"
    return code.upper()


# Data structure formatting
def format_list(
    items: List[Any],
    separator: str = ", ",
    last_separator: str = " and ",
    max_items: Optional[int] = None
) -> str:
    """
    Format list as string.
    
    Args:
        items: List of items
        separator: Separator between items
        last_separator: Separator before last item
        max_items: Maximum items to show
        
    Returns:
        Formatted list string
    """
    if not items:
        return ""
    
    str_items = [str(item) for item in items]
    
    if max_items and len(str_items) > max_items:
        shown = str_items[:max_items]
        remaining = len(str_items) - max_items
        shown.append(f"{remaining} more")
        str_items = shown
    
    if len(str_items) == 1:
        return str_items[0]
    elif len(str_items) == 2:
        return f"{str_items[0]}{last_separator}{str_items[1]}"
    else:
        return separator.join(str_items[:-1]) + last_separator + str_items[-1]


def format_key_value(
    data: Dict[str, Any],
    separator: str = ": ",
    line_separator: str = "\n",
    indent: int = 0
) -> str:
    """
    Format dictionary as key-value pairs.
    
    Args:
        data: Dictionary to format
        separator: Separator between key and value
        line_separator: Separator between pairs
        indent: Indentation level
        
    Returns:
        Formatted string
    """
    lines = []
    indent_str = " " * indent
    
    for key, value in data.items():
        # Convert key to title case
        formatted_key = key.replace("_", " ").title()
        
        # Format value based on type
        if isinstance(value, (int, float, Decimal)):
            formatted_value = str(value)
        elif isinstance(value, datetime):
            formatted_value = format_datetime(value)
        elif isinstance(value, date):
            formatted_value = format_date(value)
        elif isinstance(value, bool):
            formatted_value = "Yes" if value else "No"
        elif isinstance(value, Enum):
            formatted_value = value.value.replace("_", " ").title()
        elif value is None:
            formatted_value = "N/A"
        else:
            formatted_value = str(value)
        
        lines.append(f"{indent_str}{formatted_key}{separator}{formatted_value}")
    
    return line_separator.join(lines)


# Status and enum formatting
def format_status(
    status: Union[str, Enum],
    style: str = "title"
) -> str:
    """
    Format status value.
    
    Args:
        status: Status value
        style: Formatting style ("title", "upper", "lower")
        
    Returns:
        Formatted status
    """
    if isinstance(status, Enum):
        value = status.value
    else:
        value = str(status)
    
    # Replace underscores with spaces
    formatted = value.replace("_", " ")
    
    if style == "upper":
        return formatted.upper()
    elif style == "lower":
        return formatted.lower()
    else:
        return formatted.title()


# File size formatting
def format_file_size(
    size_bytes: int,
    decimal_places: int = 2
) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        decimal_places: Decimal places for larger units
        
    Returns:
        Formatted file size
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        # Bytes - no decimal places
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.{decimal_places}f} {units[unit_index]}"


# UUID formatting
def format_uuid(
    uuid_value: Union[str, UUID],
    short: bool = False
) -> str:
    """
    Format UUID.
    
    Args:
        uuid_value: UUID value
        short: Whether to return short version (first 8 chars)
        
    Returns:
        Formatted UUID
    """
    uuid_str = str(uuid_value)
    
    if short:
        return uuid_str[:8]
    
    return uuid_str


# JSON formatting
def format_json(
    data: Any,
    indent: int = 2,
    sort_keys: bool = True
) -> str:
    """
    Format data as pretty JSON.
    
    Args:
        data: Data to format
        indent: Indentation level
        sort_keys: Whether to sort keys
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        default=str,  # Convert non-serializable objects to string
        ensure_ascii=False
    )


__all__ = [
    "format_currency",
    "format_percentage",
    "format_decimal",
    "format_quantity",
    "format_date",
    "format_datetime",
    "format_time_ago",
    "format_duration",
    "format_name",
    "format_phone",
    "format_address",
    "format_code",
    "format_list",
    "format_key_value",
    "format_status",
    "format_file_size",
    "format_uuid",
    "format_json",
]